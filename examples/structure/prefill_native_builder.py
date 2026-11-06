"""Build the retained A3 prefill native response profile from frozen captures.

[Role] Pool complete native FlashAttention and TP AllReduce kernel count/sum
  by physical call geometry, then emit the importable profile.
[Invariants] Only per-call durations and their counts enter a response. The
  training/validation split is declared in the spec before pooling; a
  validation capture never contributes a parameter. Every forward must expose
  the declared native boundary counts, a complete captured attention tensor
  ABI and the declared layer topology. Cached spans bind the exact source
  content, extractor and model configuration, or are re-extracted. Failed
  reads, changed sources and malformed counts raise instead of becoming a
  default.
[Timeouts & Locks] One CSV stream under row/time budgets, per-forward aggregates.
[Side-Effect Policy] Reads captures/templates; writes requested JSON and its cache.
"""
from __future__ import annotations

import argparse
import bisect
import csv
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

from mindie_sim import target_operators
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution
from mindie_sim.prediction.service_regimes import _axes
from mindie_sim.prediction.structure import parse_case
from mindie_profiler.native_tensor_abi import native_contract_issue, native_tensor_contract

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import prefill  # noqa: E402  (retained finite prefill topology extractor)
from prefill_native_observations import _physical_contract  # noqa: E402

SCHEMA = "mindie-profiler-prefill-native-observation-profile/1"
FLASH = "flash_attention"
ALLREDUCE = ("linear_reduce", "catalog_tp_allreduce", "ring_allreduce")
ALLREDUCE_CLASS = {"linear_reduce": "gdn_attention",
                   "catalog_tp_allreduce": "gqa_attention",
                   "ring_allreduce": "moe"}
LAYER_FIELDS = ("attention", "ffn", "num_heads", "num_kv_heads", "head_dim",
                "num_experts", "top_k", "moe_intermediate_size", "num_shared_experts",
                "conv_kernel", "linear_heads", "linear_head_dim", "indexer", "window",
                "compress_ratio", "router_dtype", "ffn_activation", "architecture")
CAPTURE_MODES = ("FusedInferAttentionScore", "hcom_allReduce_")


def _sha256(path: Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: Path, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _plain(value):
    return json.loads(json.dumps(value))


def _extractor_identity() -> dict:
    """Name the exact topology extractor that produced a cached span file."""
    import mindie_profiler
    module = Path(prefill.__file__).resolve()
    normalized = Path(mindie_profiler.__file__).resolve().parent / "normalized.py"
    return {
        "profiler_version": getattr(mindie_profiler, "__version__", "unknown"),
        "prefill_path": str(module),
        "prefill_sha256": _sha256(module),
        "normalized_sha256": _sha256(normalized),
    }


def _resolve(spec: dict) -> tuple[dict, dict]:
    """Resolve the first training capture exactly as the replay harness does."""
    from capture_policy import import_capture_policy

    template = _read_json(Path(spec["template"]))
    source = spec["training"][0]["path"]
    resolved, provenance = import_capture_policy(deepcopy(template), capture_path=source)
    return resolved, {"template": str(Path(spec["template"]).resolve()),
                      "template_sha256": _sha256(Path(spec["template"])),
                      "capture_policy": provenance}


def _contract(raw: dict, hardware: str) -> dict:
    """Describe the selectable physical declaration in normalized form."""
    case = parse_case(raw)
    declared = {}
    for plan in case.model.layer_plans:
        key = tuple(getattr(plan, name) for name in LAYER_FIELDS)
        declared[key] = declared.get(key, 0) + 1
    quant = case.model.quant.to_dict()
    runtime = case.runtime
    return {
        "hardware": hardware,
        "parallel": case.runtime.parallel.to_dict(),
        "physical": _physical_contract(case),
        "model": {name: getattr(case.model, name) for name in (
            "layers", "hidden_size", "num_heads", "num_kv_heads", "head_dim",
            "num_experts", "top_k", "moe_intermediate_size", "activation_dtype",
            "kv_dtype", "weight_dtype", "quantization", "attention", "ffn")},
        "layer_fields": list(LAYER_FIELDS),
        "layer_groups": [{"count": c, "values": list(v)} for v, c in declared.items()],
        "quant": {name: quant[name] for name in (
            "weight_format", "activation_format", "expert_weight_format",
            "scale_format", "scale_bytes", "kv_dtype") if name in quant},
        "quant_categories": {"routed_expert": {
            "scale_format": "fp32", "scale_bytes": 4.0,
            "activation_scale_format": "fp32"}},
        "runtime": {"vllm_impl": runtime.vllm_impl,
                    "vllm_version": runtime.vllm_version,
                    "kernel_format": runtime.kernel_format,
                    "moe_recipe": runtime.moe_recipe,
                    "routing": deepcopy(dict(runtime.routing))},
        "lowering_passes": ["activation_quantization"],
    }


def _spans(capture: dict, model_cfg: dict, directory: Path, source_sha: str) -> dict:
    """Reuse a cache only when it binds source, extractor and model exactly."""
    path = directory / f"spans_{capture['id']}.json"
    extractor = _extractor_identity()
    config_sha = sha256(json.dumps(model_cfg, sort_keys=True).encode()).hexdigest()
    cached = None
    if path.exists():
        cached = _read_json(path)
        if not (cached.get("cache_version") == 2
                and cached.get("source", {}).get("sha256") == source_sha
                and cached.get("extractor") == extractor
                and cached.get("model_config_sha256") == config_sha
                and cached.get("forwards")): cached = None
    if cached is not None:
        return cached
    observed = prefill.extract_file(Path(capture["path"]), model_cfg,
                                    timeout_s=capture.get("extract_timeout_s", 180))
    stat = Path(capture["path"]).stat()
    spans = {"cache_version": 2, "capture": capture["id"],
             "source": {"path": str(Path(capture["path"]).resolve()),
                        "size_bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns,
                        "sha256": source_sha},
             "extractor": extractor, "model_config_sha256": config_sha, "forwards": [{
                 "q": item["query_rows"],
                 "first": item["body"]["evidence"]["first_locator"]["csv_line"],
                 "last": item["body"]["evidence"]["last_locator"]["csv_line"],
                 "layers": [[layer["layer_id"], layer["first_csv_line"],
                             layer["last_csv_line"], layer["attention"]]
                            for layer in item["layers"]],
                "attention_types": [group["native_type"]
                                    for group in item["attention_stage_groups"]]}
                for item in observed["forwards"]]}
    if not spans["forwards"]:
        raise ValueError(f"no_prefill_forward_spans:{capture['id']}")
    _write_json(path, spans)
    return spans


def _slots(text, *, numeric=False):
    text = (text or "").strip().strip('"')
    if not text or text in ("N/A", "NULL", "UNDEFINED"):
        return None
    parts = [part.strip() for part in text.split(";")]
    if not numeric:
        return parts
    shapes = []
    for part in parts:
        if not part:
            shapes.append(())
            continue
        try:
            shapes.append(tuple(int(value) for value in part.split(",")))
        except ValueError as error:
            raise ValueError(f"malformed_native_tensor_shape:{part}") from error
    return shapes


def _slot_shapes(text): return _slots(text, numeric=True)


def _slot_values(text): return _slots(text)


def _tensor_row(row) -> SimpleNamespace:
    return SimpleNamespace(
        kind=row["Type"], input_shapes=_slot_shapes(row["Input Shapes"]),
        input_dtypes=_slot_values(row["Input Data Types"]),
        input_formats=_slot_values(row["Input Formats"]),
        output_shapes=_slot_shapes(row["Output Shapes"]),
        output_dtypes=_slot_values(row["Output Data Types"]),
        output_formats=_slot_values(row["Output Formats"]))


_KV_BLOCK = 128
_KV_HEADS = 1
_HEAD_DIM = 256
_QUERY_HEADS = 2
_MASK, _LENGTH = ((2048, 2048), "int8", "ND"), ((1,), "int64", "ND")


def _attention_contract(entry, query_rows: int, *, paged: bool, context: int = 0) -> dict:
    """Validate every ordered FAI slot (shape, dtype, layout); scalar values
    are not exported by the source and stay explicitly unknown."""
    row = _tensor_row(entry)
    if native_contract_issue(row) is not None:
        raise ValueError("attention_tensor_abi_incomplete")
    _, kind, inputs, outputs = native_tensor_contract(row)
    query = (query_rows, _QUERY_HEADS, _HEAD_DIM)
    common = (len(inputs) >= 6 and inputs[0] == (query, "bf16", "ND")
              and inputs[3] == _MASK and inputs[4] == _LENGTH and inputs[5] == _LENGTH)
    key = inputs[1] if len(inputs) > 2 else ((), None, None)
    value = inputs[2] if len(inputs) > 2 else ((), None, None)
    if paged:
        blocks = key[0][0] if len(key[0]) == 3 else 0
        block_table = inputs[6] if len(inputs) > 6 else ((), None, None)
        valid = (len(inputs) == 7 and common
                 and key[0][1:] == (_KV_BLOCK, _HEAD_DIM) and key[1:] == ("bf16", "ND")
                 and value[0] == key[0] and value[1:] == ("bf16", "ND")
                 and blocks > 0 and blocks * _KV_BLOCK >= query_rows + context
                 and len(block_table[0]) == 2 and block_table[0][0] == 1
                 and block_table[0][1] >= -(-(query_rows + context) // _KV_BLOCK)
                 and block_table[1:] == ("int32", "ND"))
    else:
        dense = ((query_rows, _KV_HEADS, _HEAD_DIM), "bf16", "ND")
        valid = (len(inputs) == 6 and common and context == 0
                 and key == dense and value == dense)
    if not valid:
        raise ValueError("attention_input_tensor_abi_outside_source")
    if (len(outputs) != 2 or outputs[0] != (query, "bf16", "ND")
            or outputs[1] != ((), "fp32", "ND")):
        raise ValueError("attention_output_tensor_abi_outside_source")
    return {"kind": kind,
            "inputs": [[list(shape), dtype, layout] for shape, dtype, layout in inputs],
            "outputs": [[list(shape), dtype, layout] for shape, dtype, layout in outputs],
            "kv_layout": "paged" if paged else "dense"}


def _scan(capture: dict, spans: dict, *, max_rows: int, timeout_s: float) -> dict:
    """Stream one capture; retain per-forward native boundary aggregates only."""
    forwards = spans["forwards"]
    first = [item["first"] for item in forwards]
    state = [{"flash": [], "wait": [], "contracts": [], "layers": [[] for _ in f["layers"]]}
             for f in forwards]
    seen, active = set(), None
    deadline = time.monotonic() + timeout_s
    before = Path(capture["path"]).stat()
    rows = 0
    with Path(capture["path"]).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for line, row in enumerate(reader, 2):
            rows += 1
            if rows > max_rows: raise ValueError(f"source_row_budget_exceeded:{capture['id']}")
            if rows % 200_000 == 0 and time.monotonic() > deadline:
                raise TimeoutError(f"source_scan_timeout:{capture['id']}")
            index = bisect.bisect_right(first, line) - 1
            if index < 0 or line > forwards[index]["last"]:
                continue
            if index != active:
                seen.clear()
                active = index
            kind = row["Type"]
            if kind not in CAPTURE_MODES:
                continue
            key = (row.get("Device_id"), kind, row["Start Time(us)"], row["Duration(us)"])
            if kind.startswith("hcom_"):
                if key in seen:
                    continue
                seen.add(key)
            duration = float(row["Duration(us)"])
            if kind == "FusedInferAttentionScore":
                state[index]["flash"].append(duration)
                state[index]["contracts"].append(row)
                continue
            state[index]["wait"].append(float(row["Wait Time(us)"] or 0))
            for position, layer in enumerate(forwards[index]["layers"]):
                if layer[1] <= line <= layer[2]:
                    state[index]["layers"][position].append(duration)
                    break
            else:
                raise ValueError(f"collective_outside_layer_scope:{capture['id']}:{line}")

    after = Path(capture["path"]).stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError(f"source_changed_during_scan:{capture['id']}")
    digest = _sha256(Path(capture["path"]))
    if digest != spans["source"]["sha256"]:
        raise RuntimeError(f"source_content_differs_from_extracted_spans:{capture['id']}")

    records, context = [], 0
    for index, item in enumerate(forwards):
        current = state[index]
        types = item["attention_types"]
        if len(types) != 40 or types.count("FusedInferAttentionScore") != 10:
            raise ValueError(f"attention_topology_outside_source:{capture['id']}:{index}")
        if current["flash"] and len(current["flash"]) != 10:
            raise ValueError(f"unexpected_attention_call_count:{capture['id']}:{index}")
        if len(current["layers"]) != 40 or any(len(values) != 2 for values in current["layers"]):
            raise ValueError(f"unexpected_collective_layer_scope:{capture['id']}:{index}")
        contracts = [_attention_contract(entry, item["q"], paged=context > 0,
                                         context=context)
                     for entry in current["contracts"]]
        if len({json.dumps(value, sort_keys=True) for value in contracts}) > 1:
            raise ValueError(f"mixed_attention_tensor_abi:{capture['id']}:{index}")
        classes = {name: [] for name in ALLREDUCE}
        for position, values in enumerate(current["layers"]):
            native = types[position]
            recipe = ("catalog_tp_allreduce" if native == "FusedInferAttentionScore"
                      else "linear_reduce")
            classes[recipe].append(values[0])
            classes["ring_allreduce"].append(values[1])
        if not current["flash"] and any(classes.values()):
            raise ValueError(f"collective_without_attention_boundary:{capture['id']}:{index}")
        records.append({
            "forward": index, "query_rows": item["q"], "context": context,
            "attention": {"count": len(current["flash"]), "sum_us": sum(current["flash"])},
            "attention_tensor_abi": contracts[0] if contracts else None,
            "collectives": {name: {"count": len(values), "sum_us": sum(values)}
                            for name, values in classes.items()},
            "collective_calls": classes, "wait_us": sum(current["wait"]),
            "collective_tensor_abi": "not_provided_by_source",
        })
        context += item["q"]
    return {"capture": capture, "records": records, "total_query_rows": context,
            "sha256": digest, "source_rows": rows}


def _validate(capture: dict, scanned: dict, expected_counts: dict) -> None:
    if scanned["total_query_rows"] != capture["context_tokens"]:
        raise ValueError(f"prefill_chunk_tokens_do_not_match_declared_context:"
                         f"{capture['id']}:{scanned['total_query_rows']}")
    for record in scanned["records"]:
        if record["attention"]["count"] != expected_counts[FLASH]:
            raise ValueError(f"attention_boundary_missing:{capture['id']}:{record['forward']}")
        if any(record["collectives"][name]["count"] != expected_counts[name]
               for name in ALLREDUCE): raise ValueError(
                   f"collective_boundary_missing:{capture['id']}:{record['forward']}")


def _abi_invariant(record: dict) -> dict:
    """Enforce physical minimum capacity, then mask upper capacity dims.

    Larger declared capacities are legitimate; a table shorter than
    ceil((context+query_rows)/block) is not. Values are never read.
    """
    contract, required = record["attention_tensor_abi"], -(-(
        record["context"] + record["query_rows"]) // _KV_BLOCK)
    if contract["kv_layout"] == "dense":
        if record["context"] != 0: raise ValueError(
            "attention_dense_contract_outside_zero_context")
        return deepcopy(contract)
    if contract["inputs"][1][0][0] < required or contract["inputs"][6][0][1] < required:
        raise ValueError("attention_block_table_capacity_outside_source")
    masked = deepcopy(contract)
    masked["inputs"][1][0] = [0, _KV_BLOCK, _HEAD_DIM]
    masked["inputs"][2][0] = [0, _KV_BLOCK, _HEAD_DIM]
    masked["inputs"][6][0] = [1, 0]
    return masked


def _attention_abi_slots(training_records, validation_records) -> list:
    """Validate one complete training contract per layout and every heldout ABI."""
    slots, invariants = {}, {}
    for record in training_records:
        if record["query_rows"] != 8064:
            continue
        contract = record["attention_tensor_abi"]
        if contract is None: raise ValueError("attention_tensor_abi_missing")
        layout = contract["kv_layout"]
        slots.setdefault(layout, deepcopy(contract))
        invariant = json.dumps(_abi_invariant(record), sort_keys=True)
        if invariants.setdefault(layout, invariant) != invariant:
            raise ValueError("attention_tensor_abi_varies_within_training")
    if set(slots) != {"dense", "paged"}:
        raise ValueError("no_complete_attention_abi_in_training_captures")
    for record in validation_records:
        if record["query_rows"] != 8064:
            continue
        contract, layout = record["attention_tensor_abi"], None
        layout = contract["kv_layout"] if contract else None
        if (layout not in invariants or json.dumps(_abi_invariant(record), sort_keys=True)
                != invariants[layout]):
            raise ValueError("heldout_attention_tensor_abi_outside_training_domain")
    return [{"kv_layout": layout, **slots[layout]} for layout in ("dense", "paged")]


def _pool_training(scanned_training) -> dict:
    knots = {}
    for scanned in scanned_training:
        for record in scanned["records"]:
            if record["query_rows"] != 8064:
                continue
            kv_rows = record["context"] + record["query_rows"]
            knots.setdefault(kv_rows, []).append(record["attention"]["sum_us"] / 10)
    ordered = sorted(knots)
    shared = [r for s in scanned_training for r in s["records"] if r["query_rows"] == 8064]
    per_class = {name: [value for record in shared
                        for value in record["collective_calls"][name]]
                 for name in ALLREDUCE}
    totals = [sum(record["collectives"][name]["sum_us"] for name in ALLREDUCE) for record in shared]
    return {
        "knots": ordered,
        "flash_us": [statistics.fmean(knots[key]) for key in ordered],
        "capture_count": {key: len(knots[key]) for key in ordered},
        "full_chunk_count": len(shared),
        "training_ids": sorted(scanned["capture"]["id"] for scanned in scanned_training),
        "flash_call_count": 10 * len(shared),
        "allreduce_us": statistics.fmean(
            value for values in per_class.values() for value in values),
        "allreduce_class_values": per_class,
        "allreduce_forward_totals": totals,
        "flash_spread": {key: (max(knots[key]) - min(knots[key])) /
                         statistics.fmean(knots[key]) for key in ordered},
    }


def _spread_summary(values):
    ordered = sorted(values)
    return {"count": len(ordered), "mean_us": statistics.fmean(ordered),
            "median_us": statistics.median(ordered),
            "min_us": ordered[0], "max_us": ordered[-1],
            "p10_us": ordered[len(ordered) // 10],
            "p90_us": ordered[len(ordered) * 9 // 10]}


def _target_axes(raw: dict) -> dict:
    """Read the engine's own complete rule selectors from one full chunk."""
    geometry = {"phase": "prefill", "tokens": 8064, "context": 0, "sequences": 1}
    unpriced = deepcopy(raw)
    unpriced.setdefault("runtime", {}).setdefault("kernels", {})["service_regimes"] = []
    case = parse_case(unpriced)
    execution = Execution(case, CostModel(case), include_submission=False)
    selected = {}
    for op in target_operators(unpriced, **geometry):
        if op.recipe not in (FLASH, *ALLREDUCE) or op.recipe in selected:
            continue
        prepared, recipe = execution.prepare(op)
        context = execution._context(prepared, 0, "none", recipe=recipe)
        axes = _axes(context, physical_rates=True)
        selected[op.recipe] = _plain({
            "hardware": axes["hardware"], "dtype": axes["dtype"],
            "layout": axes["layout"], "replay_scope": axes["replay_scope"],
            "implementation": axes["implementation"], "runtime": axes["runtime"],
            "revision": axes["revision"], "format": axes["format"],
            "family": axes["family"], "phase": axes["phase"],
            "local_shape": axes["local_shape"], "padded_shape": axes["padded_shape"],
            "physical_rates": axes["physical_rates"], "transport": axes.get("transport"),
            "steps": dict(op.metadata).get("steps"),
            "group_axis": dict(op.metadata).get("group_axis"),
            "query_tile": dict(op.metadata).get("query_tile"),
            "kv_streams": dict(op.metadata).get("kv_streams"),
            "gqa": dict(op.metadata).get("gqa_prefill") or {}})
    missing = set((FLASH, *ALLREDUCE)) - set(selected)
    if missing: raise ValueError(f"native_boundary_missing_from_target_graph:{sorted(missing)}")
    return selected


def _identity_match(axes: dict) -> dict:
    return {"hardware": axes["hardware"], "dtype": axes["dtype"],
            "layout": axes["layout"], "replay_scope": axes["replay_scope"],
            "implementation": axes["implementation"], "runtime": axes["runtime"],
            "revision": axes["revision"], "format": axes["format"],
            "family": axes["family"], "physical_rates": axes["physical_rates"]}


def _rules(pool: dict, axes: dict, profile_id: str) -> list:
    flash = axes[FLASH]
    match = _identity_match(flash) | {
        "recipe": FLASH, "phase": "prefill",
        "metadata.gqa_prefill.query_heads": flash["gqa"]["query_heads"],
        "metadata.gqa_prefill.kv_heads": flash["gqa"]["kv_heads"],
        "metadata.gqa_prefill.head_dim": flash["gqa"]["head_dim"],
        "metadata.gqa_prefill.query_dtype": flash["gqa"]["query_dtype"],
        "metadata.gqa_prefill.kv_dtype": flash["gqa"]["kv_dtype"],
        "metadata.gqa_prefill.causal": flash["gqa"]["causal"],
        "metadata.gqa_prefill.window": flash["gqa"]["window"],
        "metadata.gqa_prefill.cp": flash["gqa"]["cp"],
        "metadata.query_tile": flash["query_tile"],
        "metadata.kv_streams": flash["kv_streams"]}
    rules = [{
        "id": "a3-qwen35-prefill-native-fai-q8064",
        "match": match,
        "coordinates": {"kv_rows": {"path": "local_shape.1"},
                        "query": {"path": "local_shape.0"}},
        "domain": {"query": {"min": 8064, "max": 8064},
                   "kv_rows": {"min": pool["knots"][0], "max": pool["knots"][-1]}},
        "response": {"kind": "piecewise_linear", "coordinate": "kv_rows",
                     "knots": [[key, round(value, 3)]
                               for key, value in zip(pool["knots"], pool["flash_us"])],
                     "outside": "analytic"},
        "provenance": {"profile_id": profile_id,
                       "native_boundary": "FusedInferAttentionScore",
                       "calls_per_forward": 10, "call_count": pool["flash_call_count"],
                       "response_unit": "us_per_complete_native_call",
                       "training_source_ids": pool["training_ids"]}}]
    for recipe in ALLREDUCE:
        collective = axes[recipe]
        match = _identity_match(collective) | {
            "recipe": recipe, "phase": "prefill",
            "local_shape": collective["local_shape"],
            "padded_shape": collective["padded_shape"],
            "transport": collective["transport"]}
        for name in ("group_axis", "steps"):
            if collective[name] is not None: match["metadata." + name] = collective[name]
        rules.append({
            "id": "a3-qwen35-prefill-native-ar-" + recipe.replace("_", "-"),
            "match": match,
            "coordinates": {"rows": {"path": "metadata.graph_active_query_rows"}},
            "domain": {"rows": {"min": 8064, "max": 8064}},
            "response": {"fixed_us": round(pool["allreduce_us"], 3)},
            "provenance": {
                "profile_id": profile_id, "native_boundary": "hcom_allReduce_",
                "calls_per_forward": len(pool["allreduce_class_values"][recipe]) //
                pool["full_chunk_count"],
                "call_count": len(pool["allreduce_class_values"][recipe]),
                "response_unit": "us_per_complete_native_call",
                "native_class": ALLREDUCE_CLASS[recipe],
                "native_class_mean_us": round(statistics.fmean(
                    pool["allreduce_class_values"][recipe]), 3),
                "response_basis": ("cohort pooled 80-call native mean; reproduces "
                                   "the cohort mean forward sum, not each measured sum"),
                "per_call_interval_us": [
                    round(min(pool["allreduce_class_values"][recipe]), 3),
                    round(max(pool["allreduce_class_values"][recipe]), 3)],
                "collective_tensor_abi": "not_provided_by_source",
                "training_source_ids": pool["training_ids"]}})
    return rules


def _audit(name: str, split: dict, pool: dict, scanned_list) -> dict:
    """Report train/held native residuals per class and per forward."""
    knots = dict(zip(pool["knots"], pool["flash_us"]))
    captures = []
    for scanned in scanned_list:
        capture = scanned["capture"]
        rows = []
        for record in scanned["records"]:
            kv_rows = record["context"] + record["query_rows"]
            bound = record["query_rows"] == 8064
            expected = 10 * knots.get(kv_rows) if bound else None
            native_total = sum(record["collectives"][item]["sum_us"] for item in ALLREDUCE)
            class_residuals = {}
            for recipe in ALLREDUCE:
                native = record["collectives"][recipe]["sum_us"]
                predicted = (record["collectives"][recipe]["count"] * pool["allreduce_us"]
                             if bound else None)
                class_residuals[recipe] = {
                    "native_us": native, "predicted_us": predicted,
                    "residual_us": None if predicted is None else native - predicted,
                    "relative": None if predicted is None else native / predicted - 1}
            rows.append({
                "forward": record["forward"], "query_rows": record["query_rows"],
                "context": record["context"], "kv_rows": kv_rows,
                "attention_native_us": record["attention"]["sum_us"],
                "attention_predicted_us": expected,
                "attention_residual": None if expected is None else (
                    record["attention"]["sum_us"] - expected),
                "collective_native_us": native_total,
                "collective_predicted_us": 80 * pool["allreduce_us"] if bound else None,
                "collective_residual": None if not bound else (
                    native_total - 80 * pool["allreduce_us"]),
                "collective_class_residuals": class_residuals,
                "collective_wait_us": record["wait_us"],
                "attention_tensor_abi": (record["attention_tensor_abi"]["kv_layout"]
                                         if record["attention_tensor_abi"] else None),
                "collective_tensor_abi": record["collective_tensor_abi"],
                "bound": bound})
        bound = [row for row in rows if row["bound"]]
        def mean(values):
            return statistics.fmean(values) if values else None
        captures.append({
            "id": capture["id"], "sha256": scanned["sha256"],
            "role": "training" if capture["id"] in split["training"] else "validation",
            "path": str(Path(capture["path"]).resolve()),
            "forwards": len(rows), "bound_forwards": len(bound),
            "attention_mean_abs_relative": mean([
                abs(row["attention_residual"] / row["attention_native_us"]) for row in bound]),
            "attention_max_abs_relative": (max(
                abs(row["attention_residual"] / row["attention_native_us"])
                for row in bound) if bound else None),
            "collective_total_mean_relative": mean([
                row["collective_residual"] / row["collective_native_us"] for row in bound]),
            "collective_total_max_abs_relative": (max(
                abs(row["collective_residual"] / row["collective_native_us"])
                for row in bound) if bound else None),
            "class_relative": {recipe: (None if not bound else {
                "mean": statistics.fmean(
                    row["collective_class_residuals"][recipe]["relative"] for row in bound),
                "max_abs": max(abs(row["collective_class_residuals"][recipe]["relative"])
                               for row in bound)}) for recipe in ALLREDUCE},
            "rows": rows})
    return {"profile": name, "split": split, "captures": captures}


def _historical_contracts(spec: dict) -> tuple[list, dict | None]:
    """Read the retained historical response payloads from the source catalog.

    Ownership must be decided by the complete physical rule, not by an id.
    Every catalog variant of the declared historical id is retained verbatim
    (match, coordinates, domain, response); source names and capture lengths do
    not participate. When no catalog is available the spec may declare the
    contracts explicitly.
    """
    regime_id = spec.get("historical_regime_id", "qwen35-a3-tp8-prefill-allreduce")
    catalog = Path(spec["template"]).parent / "_regime_catalog.json"
    if catalog.exists():
        variants = {}
        for entry in _read_json(catalog).values():
            for rule in entry.get("service_regimes", ()):
                if rule.get("id") == regime_id:
                    payload = {name: deepcopy(rule.get(name)) for name in
                               ("id", "match", "coordinates", "domain", "response")}
                    variants[json.dumps(payload, sort_keys=True)] = payload
        if not variants:
            raise ValueError(f"historical_regime_not_found:{regime_id}")
        return list(variants.values()), {"path": str(catalog.resolve()),
                                         "sha256": _sha256(catalog)}
    declared = spec.get("historical_contracts")
    if not declared:
        raise ValueError(f"historical_regime_source_missing:{regime_id}")
    return deepcopy(declared), None


def build(spec_path: Path, output: Path, audit_path: Path) -> dict:
    spec = _read_json(spec_path)
    if not spec.get("training") or not spec.get("validation"):
        raise ValueError("spec_requires_declared_training_and_validation_captures")
    training_ids = {item["id"] for item in spec["training"]}
    validation_ids = {item["id"] for item in spec["validation"]}
    if training_ids & validation_ids:
        raise ValueError("training_and_validation_captures_must_be_disjoint")
    ordered = [capture for role in ("training", "validation") for capture in spec[role]]
    seen_paths, seen_sources = {}, {}
    for capture in ordered:
        resolved = str(Path(capture["path"]).resolve())
        digest = _sha256(Path(capture["path"]))
        if resolved in seen_paths or digest in seen_sources:
            raise ValueError(f"duplicate_source_identity:{capture['id']}")
        seen_paths[resolved], seen_sources[digest] = capture["id"], capture["id"]
        capture["sha256"] = digest

    resolved, resolution = _resolve(spec)
    hardware = spec["hardware"]
    machine = parse_case(resolved).machine
    if (machine.hardware_key or machine.sku) != hardware:
        raise ValueError("resolved_case_hardware_does_not_match_spec")
    contract = _contract(resolved, hardware)
    model_cfg = dict(parse_case(resolved).model.to_dict())
    model_cfg["tp"] = spec["tp"]
    expected = {"flash_attention": 10, "linear_reduce": 30, "catalog_tp_allreduce": 10,
                "ring_allreduce": 40}
    spans_dir = Path(spec.get("spans_dir", Path(spec_path).parent / "spans"))
    max_rows, timeout_s = int(spec.get("max_rows", 5_000_000)), float(
        spec.get("scan_timeout_s", 900))

    scanned = {"training": [], "validation": []}
    for role in ("training", "validation"):
        for capture in (item for item in spec[role]):
            spans = _spans(capture, model_cfg, spans_dir, capture["sha256"])
            item = _scan(capture, spans, max_rows=max_rows, timeout_s=timeout_s)
            _validate(capture, item, expected)
            scanned[role].append(item)
    pool = _pool_training(scanned["training"])
    if len(pool["knots"]) < 2:
        raise ValueError("training_captures_do_not_cover_a_context_response")
    abi = _attention_abi_slots(
        [record for item in scanned["training"] for record in item["records"]],
        [record for item in scanned["validation"] for record in item["records"]])
    axes = _target_axes(resolved)
    rules = _rules(pool, axes, spec["id"])

    per_class = {recipe: _spread_summary(pool["allreduce_class_values"][recipe])
                 for recipe in ALLREDUCE}
    forward_totals = _spread_summary(pool["allreduce_forward_totals"])
    observations = {
        FLASH: {"recipe": FLASH, "native_type": "FusedInferAttentionScore",
                "calls_per_forward": 10, "call_count": pool["flash_call_count"],
                "response_unit": "us_per_complete_native_call", "tensor_abi": abi,
                "knots": [[key, round(value, 3)] for key, value in
                          zip(pool["knots"], pool["flash_us"])],
                "cross_capture_spread_max": max(pool["flash_spread"].values()),
                "calibration": "anchor_per_observed_full_chunk_state"},
        "allreduce": {
            "recipes": {recipe: len(pool["allreduce_class_values"][recipe]) //
                        pool["full_chunk_count"] for recipe in ALLREDUCE},
            "calls_per_forward": 80,
            "call_count": sum(len(values) for values in pool["allreduce_class_values"].values()),
            "response_unit": "us_per_complete_native_call",
            "us_per_call": round(pool["allreduce_us"], 3),
            "per_call_identification": ("cohort pooled 80-call native mean per forward; "
                                        "the three recipe classes are reported separately "
                                        "but their per-call intervals overlap"),
            "per_recipe_measurement": per_class, "per_forward_total": forward_totals,
            "collective_tensor_abi": "not_provided_by_source",
            "heterogeneity": ("Per-call durations and per-forward sums differ across "
                              "captures at identical physical states; the response "
                              "reproduces the cohort mean forward sum.")}}
    historical_contracts, historical_source = _historical_contracts(spec)
    historical_ids = sorted({rule["id"] for rule in historical_contracts})
    validation_lengths = {item["context_tokens"] for item in spec["validation"]}
    training_lengths = {item["context_tokens"] for item in spec["training"]}
    profile = {
        "schema": SCHEMA, "id": spec["id"], "phase": "prefill",
        "physical_domain": {
            "sequences": 1, "query_rows": 8064,
            "context_min": 0, "context_max": pool["knots"][-1] - 8064,
            "kv_rows": {"min": pool["knots"][0], "max": pool["knots"][-1]},
            "calls_per_forward": expected},
        "source_contract": contract, "native_observations": observations,
        "replaced_regime_ids": historical_ids,
        "replaced_regime_contracts": historical_contracts,
        "replaced_regime_contract_source": historical_source,
        "calibration": {
            "selection": ("declared_capture_coverage_before_pooling_after_"
                          "exploratory_native_review"),
            "exploratory_native_review_before_split": True,
            "split_declared_before_coefficients": True,
            "selection_rationale": spec.get("selection_rationale", (
                "training uses the production MTP3 capture at short and long "
                "declared lengths; the target body is identical to MTP0 and no "
                "Body outcome selects a parameter")),
            "training_capture_ids": sorted(training_ids),
            "validation_capture_ids": sorted(validation_ids),
            "training_declared_context_lengths": sorted(training_lengths),
            "validation_declared_context_lengths": sorted(validation_lengths),
            "validation_context_lengths_outside_training": sorted(
                validation_lengths - training_lengths),
            "heldout_relation": "repeat_geometry_cross_capture",
            "heldout_context_generalization": False,
            "heldout_note": ("validation captures repeat training chunk contexts; "
                             "they test separate runs, not unseen chunk geometry or "
                             "unseen context lengths"),
            "in_sample_history": ("The replaced A3 rule was fitted on these capture "
                                  "families during Wave5; the native response is rebuilt "
                                  "from complete kernel count/sum only."),
            "body_error_used_for_selection": False,
            "case_identity_used_in_predictor": False},
        "training_sources": [{"id": i["id"], "path": str(Path(i["path"]).resolve()),
                              "sha256": i["sha256"]} for i in spec["training"]],
        "validation_sources": [{"id": i["id"], "path": str(Path(i["path"]).resolve()),
                                "sha256": i["sha256"]} for i in spec["validation"]],
        "limitations": [
            "Only full 8064-row chunks are bound. Tail chunks keep the caller's "
            "prior response unchanged (including a legacy capture-selected floor "
            "if the caller has one); they are not converted to analytic.",
            "Per-call allreduce durations and per-forward sums are state dependent; "
            "the response reproduces the cohort mean forward sum, not each measured "
            "forward sum or an individual wait.",
            "The source does not export collective tensor slots; the allreduce "
            "response is identified by declared shape, transport and layer order, "
            "not by a captured payload descriptor.",
            "The first chunk's dense-KV attention anchor and the paged continuation "
            "are distinguished only by kv rows; a paged zero-context caller is "
            "outside the observed ABI.",
            "The retained captures do not identify the compiler binary, so source "
            "equivalence of the observed kernels is not claimed.",
            "Only A3 Q35 TP8 EP8 W8A8-DYNAMIC with the observed GDN/GQA topology, "
            "device service rates, links and placements is inside the guard."],
        "service_regimes": rules}
    _write_json(output, profile)
    audit = _audit(spec["id"], {"training": sorted(training_ids),
                                "validation": sorted(validation_ids)}, pool,
                   scanned["training"] + scanned["validation"])
    audit["resolution"] = resolution
    audit["extractor"] = _extractor_identity()
    _write_json(audit_path, audit)
    return {"profile": str(Path(output).resolve()),
            "profile_sha256": _sha256(Path(output)),
            "audit": str(Path(audit_path).resolve()), "knots": len(pool["knots"]),
            "allreduce_us": pool["allreduce_us"]}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    arguments = parser.parse_args(argv)
    print(json.dumps(build(arguments.spec, arguments.out, arguments.audit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
