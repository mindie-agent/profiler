"""Import shared-KV MLA tensor representation from a retained native capture.

[Role] Reconcile output projections and quantized indexer ABI before replay.
[Invariants] Structural tensor descriptors select fields, never names or timing.
  Representation presets may be refined; explicit conflicting precision and
  source callers are preserved. Native binary equivalence remains unknown.
[Timeouts & Locks] One bounded streaming CSV scan; no waits, processes or locks.
[Side-Effect Policy] Read capture descriptors; mutate only the supplied copy.
"""
from collections import Counter
from copy import deepcopy
import csv
import gzip
import time
from types import SimpleNamespace

from mindie_profiler.normalized import shapes
from mindie_profiler.sources_csv import _open_csv_text, _resolve
from mindie_profiler.sources_db import load_mapping
from mindie_sim.prediction.structure import parse_case

from capture_structure import capture_csv_path, _file_sha256


IMPLEMENTATION = "cann_quant_lightning_indexer_v2_complete"
MARKER = "captured_sharedkv_mla"
BF16 = {"weight_format": "bf16", "activation_format": "bf16"}
FP16_NAMES = {"FLOAT16", "DT_FLOAT16"}
TENSOR_COLUMNS = (
    "type", "input_shapes", "output_shapes", "input_dtypes",
    "output_dtypes", "input_formats", "output_formats",
)


def _descriptor_columns(path):
    """Resolve tensor columns once without retaining any descriptor row."""
    aliases = load_mapping()["csv"]["aliases"]
    with _open_csv_text(path) as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return None
        header_list = [str(name).strip() for name in header]
        columns = {name: _resolve(header_list, aliases[name]) for name in TENSOR_COLUMNS}
        if any(index is None for index in columns.values()):
            return None
        return columns


def _descriptor_rows(path):
    """Stream matching tensor descriptors; timing columns are never parsed.

    The caller consumes the iterator exactly once, so memory stays bounded by
    one row instead of one entry per matching kernel. A missing descriptor
    header is reported as ``None`` before the stream starts; scan-budget and
    timeout failures stay explicit iteration errors.
    """
    columns = _descriptor_columns(path)
    if columns is None:
        return None

    def rows():
        start = time.monotonic()
        with _open_csv_text(path) as handle:
            reader = csv.reader(handle)
            next(reader, None)  # the descriptor header was validated above
            for line, row in enumerate(reader, 2):
                if line > 1_000_001:
                    raise ValueError("captured_mla_row_budget_exceeded")
                if line % 1024 == 0 and time.monotonic() - start > 30:
                    raise TimeoutError("captured_mla_tensor_scan_timed_out")

                def cell(field):
                    idx = columns[field]
                    return str(row[idx]).strip() if idx < len(row) else ""
                kind = cell("type")
                if kind not in {"TransposeBatchMatMul", "MatMulV2", "MatMulV3",
                                "VllmAscendQuantLightningIndexerV2"}:
                    continue

                def tokens(field):
                    return tuple(value.strip() for value in cell(field).strip('"').split(";"))
                yield SimpleNamespace(
                    kind=kind, line=line,
                    input_shapes=shapes(cell("input_shapes")),
                    output_shapes=shapes(cell("output_shapes")),
                    input_dtypes=tokens("input_dtypes"),
                    output_dtypes=tokens("output_dtypes"),
                    input_formats=tokens("input_formats"),
                    output_formats=tokens("output_formats"))

    return rows()


def _matrix(row, *, hidden, rank, input_width):
    ins, outs = row.input_shapes, row.output_shapes
    if not ins or not outs:
        return None
    if row.kind == "TransposeBatchMatMul":
        if len(ins) != 2 or len(ins[0]) != 3 or ins[0][1:] != (1, input_width):
            return None
        role, expected_in, expected_out = "output_a", (1, input_width, rank), (ins[0][0], 1, rank)
    elif row.kind in {"MatMulV2", "MatMulV3"}:
        if len(ins) != 2 or len(ins[0]) != 2 or ins[0][1] != rank:
            return None
        role, expected_in, expected_out = "output_b", (hidden, rank), (ins[0][0], hidden)
    else:
        return None
    if ins[1] != expected_in:
        return None
    valid = (ins[0][0] > 0 and outs == (expected_out,)
             and row.input_dtypes == ("DT_BF16", "DT_BF16")
             and row.output_dtypes == ("DT_BF16",)
             and row.input_formats == ("ND", "ND") and row.output_formats == ("ND",))
    return role, valid, ins[0][0]


def _indexer(row):
    if row.kind != "VllmAscendQuantLightningIndexerV2":
        return None
    ins, outs = row.input_shapes, row.output_shapes
    if not ins or not outs or len(ins) != 14 or len(outs) != 3:
        return False
    if len(ins[0]) != 3 or ins[0][1:] != (64, 128) or ins[0][0] <= 0:
        return False
    q = ins[0][0]
    if (len(ins[1]) != 4 or ins[1][1:] != (128, 1, 128) or ins[1][0] <= 0
            or ins[2:4] != ((q, 64), (q, 64)) or ins[4] != (ins[1][0], 128, 1)
            or outs[0] != (q, 1, 512) or outs[1:] != ((), ())):
        return False
    if (any(ins[i] != () for i in (6, 7, 11, 13))
            or any(len(ins[i]) != 1 or ins[i][0] <= 0 for i in (5, 8, 9, 12))
            or ins[8] != ins[9] or ins[5][0] != ins[8][0] + 1
            or len(ins[10]) != 2 or ins[10][0] != ins[8][0] or ins[10][1] <= 0
            or ins[12] != (1024,)):
        return False
    dt = row.input_dtypes
    return (len(dt) == 14 and dt[:2] == ("INT8", "INT8")
            and all(value in FP16_NAMES for value in dt[2:5])
            and dt[5:] == ("INT32", "DT_UNDEFINED", "DT_UNDEFINED", "INT32", "INT32",
                          "INT32", "DT_UNDEFINED", "INT32", "DT_UNDEFINED")
            and row.output_dtypes == ("INT32", "DT_BF16", "INT32")
            and len(row.input_formats) == 14
            and all(row.input_formats[i] == "ND" for i in (0, 1, 2, 3, 4, 5, 8, 9, 10, 12))
            and all(row.input_formats[i] == "NULL" for i in (6, 7, 11, 13))
            and row.output_formats == ("ND", "ND", "ND"))


def apply_captured_mla_structure(raw, *, capture_path):
    """Refine a declared shared-KV caller only when every observed ABI agrees."""
    provenance = {"schema_version": "mindie-profiler-captured-mla/1",
        "status": "not_applicable", "reason": "sharedkv_grouped_output_domain_not_present",
        "timing_values_used": False, "capture_binary_identity": "unknown",
        "changed_fields": [], "evidence": {}}
    model = raw.get("model")
    if not isinstance(model, dict) or model.get("attention") not in {None, "mla"}:
        return provenance
    case = parse_case(raw)
    if case.model.attention != "mla":
        return provenance
    plans = [p for p in case.model.layer_plans if p.scope == "body"]
    if ((case.machine.hardware_key or case.machine.sku) != "Ascend910_9362"
            or not plans or case.model.activation_dtype != "bf16"
            or any(p.mla_variant != "latent_mqa" or p.cache_kind != "window_compressed"
                   or p.o_groups != case.runtime.parallel.tp or p.o_lora_rank != 1024
                   or p.num_heads // case.runtime.parallel.tp * p.head_dim != 4096
                   for p in plans)):
        return provenance
    path = capture_csv_path(capture_path)
    if not path.is_file():
        provenance.update(status="not_provided", reason="capture_csv_not_present")
        return provenance
    descriptor_rows = _descriptor_rows(path)
    if descriptor_rows is None:
        provenance.update(status="unsupported", reason="captured_mla_requires_complete_tensor_columns")
        return provenance
    counts, bad, first, rows_a, rows_b = Counter(), Counter(), {}, Counter(), Counter()
    for row in descriptor_rows:
        projection = _matrix(row, hidden=case.model.hidden_size, rank=1024, input_width=4096)
        if projection:
            role, valid, rows = projection
            counts[role] += 1
            bad[role] += not valid
            first.setdefault(role, row.line)
            (rows_a if role == "output_a" else rows_b)[rows] += 1
        indexer = _indexer(row)
        if indexer is not None:
            counts["indexer"] += 1
            bad["indexer"] += not indexer
            first.setdefault("indexer", row.line)
    provenance["evidence"] = {"source": {"path": str(path), "sha256": _file_sha256(path)},
        "counts": dict(counts), "invalid_abi_counts": dict(bad), "first_csv_lines": first,
        "output_a_row_histogram": dict(rows_a), "output_b_row_histogram": dict(rows_b)}
    if not counts["output_a"] or not counts["output_b"] or rows_a != rows_b or any(bad.values()):
        provenance.update(status="unsupported", reason="missing_mixed_or_inconsistent_native_mla_abi")
        return provenance
    quant = case.model.quant.to_dict()
    source = quant.get("source", {})
    preset = source.get("kind") == "representation_preset"
    explicit = quant.get("category_overrides", {})
    global_explicit = (
        {k: quant[k] for k in ("weight_format", "activation_format") if k in quant}
        if not preset else {}
    )
    for category in ("mla.o_a", "mla.o_b"):
        values = {**global_explicit, **dict(explicit.get("mla", {})), **dict(explicit.get(category, {}))}
        if any(key in values and values[key] != value for key, value in BF16.items()):
            provenance.update(status="conflict", reason="explicit_projection_precision_conflicts_with_capture")
            return provenance
    index_plans = [p for p in plans if p.indexer or p.owns_topk or p.index_query_per_layer]
    has_indexer = bool(counts["indexer"])
    if has_indexer and (not index_plans or any(
            (p.index_heads, p.index_dim, p.index_topk, p.compress_ratio, p.index_kpool)
            != (64, 128, 512, 4, 1) or p.candidate_filter for p in index_plans)
            or case.runtime.parallel.cp != 1 or case.runtime.parallel.pcp != 1):
        provenance.update(status="unsupported", reason="native_indexer_and_structural_geometry_disagree")
        return provenance
    if has_indexer and not preset and (quant["index_dtype"], quant["index_scale_dtype"]) != ("int8", "fp16"):
        provenance.update(status="conflict", reason="explicit_indexer_precision_conflicts_with_capture")
        return provenance
    runtime = raw.get("runtime")
    if runtime is not None and not isinstance(runtime, dict):
        provenance.update(status="unsupported", reason="runtime_declaration_is_not_a_mapping")
        return provenance
    pending_runtime = deepcopy(runtime) if isinstance(runtime, dict) else {}
    kernels = pending_runtime.get("kernels")
    kernels = kernels if isinstance(kernels, dict) else {}
    lowerings = kernels.get("lowerings")
    lowerings = lowerings if isinstance(lowerings, dict) else {}
    previous = lowerings.get("quant_lightning_indexer")
    selected = {"implementation": IMPLEMENTATION}
    equivalent_previous = (
        previous == IMPLEMENTATION
        or (isinstance(previous, dict)
            and not (set(previous) - {"implementation", "options", "recipes"})
            and previous.get("implementation") == IMPLEMENTATION
            and previous.get("options") in (None, {})
            and previous.get("recipes") in (None, (), []))
    )
    fusion = lowerings.get("native_fusion")
    if (has_indexer and isinstance(fusion, dict)
            and {"lightning_indexer", "quant_lightning_indexer"}.intersection(
                fusion.get("options", {}).get("roles", ()))):
        provenance.update(status="conflict", reason="explicit_indexer_fusion_boundary_preserved")
        return provenance
    if has_indexer and previous is not None and not equivalent_previous:
        provenance.update(status="conflict", reason="explicit_indexer_source_caller_conflicts_with_capture")
        return provenance
    before = deepcopy(quant)
    quant.setdefault("category_overrides", {}).update({"mla.o_a": dict(BF16), "mla.o_b": dict(BF16)})
    if has_indexer:
        quant.update(index_dtype="int8", index_scale_dtype="fp16")
    declaration = {
        "output_a": {"kind": "TransposeBatchMatMul", "groups": 1, "n": 1024, "k": 4096,
                     "input_dtype": "bf16", "weight_dtype": "bf16", "output_dtype": "bf16", "layout": "ND"},
        "output_b": {"input_dtype": "bf16", "weight_dtype": "bf16", "output_dtype": "bf16"},
        "quant_indexer": has_indexer,
    }
    # Atomic commit: every structural validation above has completed. The
    # pending runtime is a private copy, so a malformed nested declaration is
    # rejected before either top-level field is replaced.
    if not isinstance(pending_runtime.get("kernels", {}), dict):
        provenance.update(status="unsupported", reason="runtime_kernels_declaration_is_not_a_mapping")
        return provenance
    if not isinstance(pending_runtime.get("metadata", {}), dict):
        provenance.update(status="unsupported", reason="runtime_metadata_declaration_is_not_a_mapping")
        return provenance
    if has_indexer and previous is None:
        pending_runtime.setdefault("kernels", {}).setdefault("lowerings", {})[
            "quant_lightning_indexer"] = selected
    pending_runtime.setdefault("metadata", {})[MARKER] = declaration
    raw["model"]["quant"] = quant
    raw["runtime"] = pending_runtime
    if has_indexer and previous is None:
        provenance["changed_fields"].append("runtime.kernels.lowerings.quant_lightning_indexer")
    if quant != before:
        provenance["changed_fields"].append("model.quant")
    provenance["changed_fields"].append("runtime.metadata." + MARKER)
    provenance.update(status="applied", reason="native_tensor_abi_refines_declared_sharedkv_representation")
    return provenance
