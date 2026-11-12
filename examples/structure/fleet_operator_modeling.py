"""Fleet step and operator costs from the declared device body graph.

The only cost source is ``mindie_sim.prediction.body.body_forward`` on the
case file named by ``model_case`` and the geometry that file, its extraction
receipt, and the row declare. Capture ids, suite names, measured times,
``structural_weights``, ``active_hbm_mb``, and ``active_cube_gflops`` do not
enter the cost. Standalone primitive workloads are delegated to
``fleet_primitive_workloads.predict_primitive_workload`` when that module
publishes ``is_primitive_workload``. Observations are delegated to
``fleet_capture_observations``.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import fleet_capture_observations as observations

_STRUCT_DIR = Path(__file__).resolve().parent
CASES_DIR = _STRUCT_DIR / "cases"
CASES_INDEX_PATH = _STRUCT_DIR / "cases.json"

DATA_ROOTS = observations.DATA_ROOTS
MULTINODE_RUNS_ROOT = observations.MULTINODE_RUNS_ROOT
RESULTS_DIR = observations.RESULTS_DIR
# Retained so tests can retarget the attributes. Prediction does not read them.
S5_PREFILL_ROOT = Path("/tmp/unused-s5-prefill-root")
_FLEET_TEMPLATE_PATH = Path("/tmp/unused-fleet-template.jsonl")

_ALLOWED_CFG_KEYS = (
    "capture_id", "suite", "hardware_tier", "model_case", "phase",
    "forward_steps", "geometry", "target_timing_used_to_fit",
    "source_calibration", "traits",
)
# Declared structure only. Demand fields and measured shares are not read.
_GEOMETRY_KEYS = (
    "tp", "dp", "ep", "pp", "cp", "pcp",
    "concurrency", "sequences_per_replica", "tokens_per_sequence", "query_rows",
    "context_tokens", "context_basis", "prompt_tokens", "prefix_tokens",
    "num_layers", "num_experts", "top_k",
    "max_num_batched_tokens", "enable_chunked_prefill", "batch_basis",
)
_CANONICAL_FAMILY = {
    "moe.combine": "moe", "moe.dispatch": "moe", "moe": "moe",
    "collective": "collective", "attention": "attention", "gemm": "gemm",
    "kv_cache": "kv_cache", "norm_activation": "norm_residual",
    "elementwise_quant": "elementwise_quant", "other": "other",
}
_BENCHMARK_FAMILY = {
    "moe.combine": "moe_comm_fusion", "moe.dispatch": "moe_comm_fusion",
    "moe": "moe_comm_fusion", "collective": "moe_comm_fusion",
    "attention": "attention_mla", "gemm": "cube_gemm",
    "kv_cache": "vector_elementwise", "norm_activation": "vector_elementwise",
    "elementwise_quant": "vector_elementwise", "other": "unclassified",
}
_UNIFIED_FAMILY = {
    "moe.combine": "moe_routing_grouped_gemm", "moe.dispatch": "moe_routing_grouped_gemm",
    "moe": "moe_routing_grouped_gemm", "collective": "collective_comm",
    "attention": "attention", "gemm": "matmul_gemm",
    "kv_cache": "kv_cache_position_rope",
    "norm_activation": "norm_activation_elementwise",
    "elementwise_quant": "norm_activation_elementwise", "other": "unclassified",
}
_CANONICAL_KEYS = (
    "gemm", "attention", "moe", "norm_residual", "collective", "kv_cache", "elementwise_quant", "other",
)
_BENCHMARK_KEYS = ("cube_gemm", "vector_elementwise", "attention_mla", "moe_comm_fusion", "unclassified")
_UNIFIED_KEYS = (
    "matmul_gemm", "attention", "moe_routing_grouped_gemm", "norm_activation_elementwise",
    "kv_cache_position_rope", "collective_comm", "unclassified",
)
# Accelerator Core labels stay unverified until a per-kernel source interval
# binds them. Resource busy time is a different measurement and is not copied here.
_CORE_KEYS = ("AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV", "COMMUNICATION", "AI_CPU")
# Per-id rename of a declared MSProf class string. This is not a duration split
# and not a resource-busy collapse. MIX_AIC stays a launch class. Only the exact
# class MIX_AIV is renamed; an AIV resource name is not that class.
_CORE_CANON = {
    "AI_CORE": "AI_CORE",
    "AI_VECTOR_CORE": "AI_VECTOR_CORE",
    "AI_CPU": "AI_VECTOR_CORE",
    "MIX_AIC": "MIX_AIC",
    "COMMUNICATION": "COMMUNICATION",
    "MIX_AIV": "COMMUNICATION",
    "DSA_SQE": "COMMUNICATION",
}
_ENGINE_FIELDS = ("accelerator_core", "core", "engine", "task_type")
_TIMING_PAYLOAD_KEYS = ("fixed_us", "fixed_ms", "fixed_ns", "knots")
_STRUCTURAL_KERNEL_KEYS = ("programs", "lowerings")

_CASE_INDEX: dict[str, dict[str, Any]] | None = None
_RECEIPT_GEOMETRY: dict[str, tuple[dict[str, Any], ...]] = {}
_GRAPH_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
_POPULATION_STEP_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}
_STEP_EQUIVALENCE: dict[tuple[Any, ...], dict[str, Any]] = {}
_ROOTS_SIG: tuple[Any, ...] | None = None


def clear_caches() -> None:
    """Drop graph aggregates and observation caches."""
    global _CASE_INDEX, _ROOTS_SIG, _ARCHIVE_CONFIGURED
    _ARCHIVE_CONFIGURED = False
    _CASE_INDEX = None
    _RECEIPT_GEOMETRY.clear()
    _GRAPH_CACHE.clear()
    _POPULATION_STEP_CACHE.clear()
    _STEP_EQUIVALENCE.clear()
    _ROOTS_SIG = None
    observations.clear_observation_caches()


def _sync_observation_roots() -> None:
    global _ROOTS_SIG
    sig = (tuple(str(p) for p in DATA_ROOTS), str(MULTINODE_RUNS_ROOT), str(RESULTS_DIR))
    if sig == _ROOTS_SIG:
        return
    observations.configure_observation_roots(
        data_roots=DATA_ROOTS, multinode_root=MULTINODE_RUNS_ROOT, results_dir=RESULTS_DIR,
    )
    _ROOTS_SIG = sig


def parse_kernel_details_summary(kd_path: Path | str) -> dict[str, Any]:
    """Delegate kernel-detail parsing to the observation module."""
    return observations.parse_kernel_details_summary(kd_path)


def _read_op_stat_summary(op_dir: Path) -> dict[str, Any]:
    """Delegate op-statistic parsing. Malformed cells raise ValueError."""
    return observations.parse_op_statistic_summary(op_dir)


def extract_capture_observations(row: Mapping[str, Any], include_timeline: bool = False) -> dict[str, Any]:
    """Delegate measurement extraction. Prediction does not call this."""
    _sync_observation_roots()
    return observations.extract_capture_observations(row, include_timeline=include_timeline)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and math.isfinite(value) and value == int(value):
        return int(value)
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value.strip())
    return None


def _declared_geometry(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key in _GEOMETRY_KEYS:
        if key in ("context_basis", "batch_basis"):
            value = raw.get(key)
            if isinstance(value, str) and value:
                out[key] = value
            continue
        if key == "enable_chunked_prefill":
            value = raw.get(key)
            if isinstance(value, bool):
                out[key] = value
            continue
        number = _as_int(raw.get(key))
        if number is not None:
            out[key] = number
    return out


def _model_case_text(model_case: Any) -> str:
    if isinstance(model_case, Mapping):
        for key in ("path", "sim_case_path", "catalog_key"):
            value = model_case.get(key)
            if isinstance(value, str) and value:
                return value
        return ""
    return str(model_case or "")


def _resolve_case_path(model_case: Any) -> Path | None:
    text = _model_case_text(model_case)
    if not text or not text.endswith(".json"):
        return None
    candidate = Path(text)
    options = [candidate] if candidate.is_absolute() else [CASES_DIR / candidate.name, _STRUCT_DIR / candidate, candidate]
    for path in options:
        if path.is_file():
            return path.resolve()
    return None


def _case_index() -> dict[str, dict[str, Any]]:
    global _CASE_INDEX
    if _CASE_INDEX is not None:
        return _CASE_INDEX
    index: dict[str, dict[str, Any]] = {}
    if CASES_INDEX_PATH.is_file():
        document = json.loads(CASES_INDEX_PATH.read_text(encoding="utf-8"))
        for entry in document.get("cases") or ():
            if not isinstance(entry, Mapping):
                continue
            paths = []
            model_case = entry.get("model_case") if isinstance(entry.get("model_case"), Mapping) else {}
            for value in (
                entry.get("sim_case_path"), model_case.get("path"),
                (entry.get("model_declaration") or {}).get("path") if isinstance(entry.get("model_declaration"), Mapping) else None,
            ):
                if isinstance(value, str) and value:
                    paths.append(value)
            record = {
                "case_id": entry.get("case_id"),
                "phase": entry.get("phase"),
                "paths": tuple(paths),
                "model_sha256": model_case.get("sha256") if isinstance(model_case, Mapping) else None,
                "extraction_path": entry.get("extraction_path"),
                "extraction_sha256": (entry.get("extraction_identity") or {}).get("sha256")
                if isinstance(entry.get("extraction_identity"), Mapping) else None,
                "index_geometry": _declared_geometry(entry.get("geometry")),
            }
            for path in paths:
                index[path] = record
                index[Path(path).name] = record
    _CASE_INDEX = index
    return index


def _load_case(path: Path, expected_sha: str | None) -> tuple[dict[str, Any] | None, str | None]:
    actual = _sha256(path)
    if expected_sha and actual != expected_sha:
        return None, f"case_sha256_mismatch:{actual}!={expected_sha}"
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        return None, "case_json_not_object"
    return document, None


def _unverified_cores() -> dict[str, None]:
    return {key: None for key in _CORE_KEYS}


def _core_time_basis(forecast: str) -> str:
    if forecast == "source_bound":
        return "source_bound_declared_accelerator_core"
    if forecast == "partial":
        return "partial_declared_accelerator_core"
    if forecast == "withheld_multi_rank":
        return "withheld_multi_rank_until_one_rank_is_selected"
    return "unresolved_no_declared_accelerator_core"


def _structural_sha(case: Mapping[str, Any]) -> str:
    payload = json.dumps(case, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def _document_source_sha(document: Mapping[str, Any]) -> str:
    """Physical source digest declared by a receipt. Span fields are not read."""
    holders = [document]
    observed = document.get("observed")
    if isinstance(observed, Mapping):
        holders.append(observed)
    for holder in holders:
        for key in ("source_identity", "source"):
            ident = holder.get(key)
            if isinstance(ident, Mapping):
                digest = ident.get("sha256")
                if isinstance(digest, str) and len(digest) == 64:
                    return digest
    return ""


def _receipt_populations(entry: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, list[str]]:
    """Geometry groups and structural forward order. Span times are not kept."""
    path_text = entry.get("extraction_path")
    notes: list[str] = []
    if not isinstance(path_text, str) or not path_text:
        return [], [], "", ["extraction_receipt_absent"]
    path = Path(path_text)
    if not path.is_file():
        return [], [], "", [f"extraction_receipt_missing:{path}"]
    cached = _RECEIPT_GEOMETRY.get(str(path))
    if cached is not None:
        populations, frames, source_sha = cached
        return [dict(item) for item in populations], [dict(item) for item in frames], source_sha, notes
    actual = _sha256(path)
    expected = entry.get("extraction_sha256")
    if expected and actual != expected:
        return [], [], "", [f"extraction_sha256_mismatch:{actual}!={expected}"]
    document = json.loads(path.read_text(encoding="utf-8"))
    source_sha = _document_source_sha(document)
    group_geometry: dict[Any, dict[str, Any]] = {}
    populations: list[dict[str, Any]] = []
    for group in document.get("geometry_groups") or ():
        if not isinstance(group, Mapping):
            continue
        geometry = _declared_geometry(group.get("geometry"))
        forward_ids = [item for item in (group.get("forward_ids") or ())]
        geometry["forward_count"] = len(forward_ids)
        populations.append(geometry)
        for forward_id in forward_ids:
            group_geometry[forward_id] = geometry
    frames: list[dict[str, Any]] = []
    for forward in document.get("forwards") or ():
        if not isinstance(forward, Mapping):
            continue
        own = forward.get("geometry") if isinstance(forward.get("geometry"), Mapping) else {}
        if not own:
            body = forward.get("body") if isinstance(forward.get("body"), Mapping) else {}
            own = body.get("geometry") if isinstance(body.get("geometry"), Mapping) else {}
        declared = _declared_geometry(own) or dict(group_geometry.get(forward.get("forward_id")) or {})
        frames.append({
            "forward_id": forward.get("forward_id"),
            "phase": forward.get("phase"),
            "rank_id": forward.get("rank_id"),
            "device_id": forward.get("device_id"),
            "sequences_per_replica": declared.get("sequences_per_replica"),
            "tokens_per_sequence": declared.get("tokens_per_sequence"),
            "query_rows": declared.get("query_rows"),
        })
    # Keep geometry and forward identity only. Span times stay in the receipt.
    _RECEIPT_GEOMETRY[str(path)] = (tuple(populations), tuple(frames), source_sha)
    del document
    if not populations:
        notes.append("extraction_receipt_has_no_geometry_groups")
    return populations, frames, source_sha, notes


def _sku_family(sku: str) -> str | None:
    if sku.startswith("Ascend910B"):
        return "A2"
    if sku.startswith("Ascend910_93"):
        return "A3"
    if sku.startswith("Ascend950") or sku.startswith("Ascend910_95"):
        return "A5"
    return None


def _scenario(case: Mapping[str, Any]) -> dict[str, Any]:
    runtime = case.get("runtime") if isinstance(case.get("runtime"), Mapping) else {}
    metadata = runtime.get("metadata") if isinstance(runtime.get("metadata"), Mapping) else {}
    scenario = metadata.get("accepted_state_scenario") if isinstance(metadata.get("accepted_state_scenario"), Mapping) else {}
    return _declared_geometry(scenario)


def _select_population(populations: Sequence[Mapping[str, Any]], sequences: int, tokens: int) -> dict[str, Any] | None:
    matches = [
        dict(item) for item in populations
        if item.get("sequences_per_replica") == sequences and item.get("tokens_per_sequence") == tokens
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return {"_ambiguous": matches}
    return None


def _resolve_probe(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve one body probe from the case file and declared geometry."""
    diagnostics: list[str] = []
    phase = str(cfg.get("phase") or "").lower()
    if phase not in {"decode", "prefill"}:
        return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["phase_not_declared"]}
    case_path = _resolve_case_path(cfg.get("model_case"))
    if case_path is None:
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": ["model_case_is_not_a_case_file"],
            "needed": ["model_case path of a checked-in case JSON"],
        }
    index = _case_index()
    entry = index.get(str(case_path.relative_to(_STRUCT_DIR)) if str(case_path).startswith(str(_STRUCT_DIR)) else case_path.name)
    if entry is None:
        entry = index.get(case_path.name)
    expected_sha = entry.get("model_sha256") if entry else None
    case, error = _load_case(case_path, expected_sha if isinstance(expected_sha, str) else None)
    if case is None:
        return {"ok": False, "status": "model_rejected", "diagnostics": [error or "case_unreadable"]}
    runtime = case.get("runtime") if isinstance(case.get("runtime"), Mapping) else {}
    row_geometry = _declared_geometry(cfg.get("geometry"))
    machine = case.get("machine") if isinstance(case.get("machine"), Mapping) else {}
    sku = str(machine.get("sku") or "")
    tier = str(cfg.get("hardware_tier") or "").upper()
    family = _sku_family(sku)
    if tier and family and tier != family:
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": [f"hardware_tier_{tier}_disagrees_with_case_sku_{sku}"],
        }
    parallel: dict[str, int] = {}
    for axis in ("tp", "dp", "ep", "pp"):
        row_value = row_geometry.get(axis)
        case_value = _as_int(runtime.get(axis))
        if row_value is not None and case_value is not None and row_value != case_value:
            return {
                "ok": False, "status": "insufficient_evidence",
                "diagnostics": [f"parallel_conflict:{axis}:row={row_value}:case={case_value}"],
            }
        chosen = row_value if row_value is not None else case_value
        if chosen is None or chosen < 1:
            return {"ok": False, "status": "insufficient_evidence", "diagnostics": [f"{axis}_not_declared"]}
        parallel[axis] = chosen
    if entry:
        populations, frames, source_sha, receipt_notes = _receipt_populations(entry)
    else:
        populations, frames, source_sha, receipt_notes = [], [], "", ["case_not_in_cases_index"]
    diagnostics.extend(receipt_notes)
    scenario = _scenario(case)
    sequences = row_geometry.get("sequences_per_replica")
    tokens = row_geometry.get("tokens_per_sequence")
    if sequences is None:
        sequences = scenario.get("sequences_per_replica")
    if tokens is None:
        tokens = scenario.get("tokens_per_sequence")
    if phase == "prefill" and tokens is None:
        tokens = row_geometry.get("prompt_tokens")
    if sequences is None or tokens is None or sequences < 1 or tokens < 1:
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": diagnostics + ["query_geometry_not_declared"],
            "needed": ["sequences_per_replica", "tokens_per_sequence"],
        }
    query_rows = row_geometry.get("query_rows")
    if query_rows is not None and query_rows != sequences * tokens:
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": diagnostics + [
                f"query_rows_{query_rows}_disagree_with_sequences_{sequences}_times_q_{tokens}",
            ],
        }
    population = _select_population(populations, sequences, tokens) if populations else None
    if population and population.get("_ambiguous"):
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": diagnostics + ["receipt_geometry_population_ambiguous"],
        }
    if populations and population is None:
        declared = [
            (item.get("sequences_per_replica"), item.get("tokens_per_sequence"), item.get("forward_count"))
            for item in populations
        ]
        return {
            "ok": False, "status": "insufficient_evidence",
            "diagnostics": diagnostics + [f"row_geometry_not_in_receipt_populations:{declared}"],
        }
    context = None
    context_source = None
    if population and population.get("context_tokens") is not None:
        context = population["context_tokens"]
        context_source = "extraction_receipt"
    elif phase == "prefill":
        context = 0
        context_source = "prefill_chunk_start"
    else:
        basis = (population or {}).get("context_basis") or row_geometry.get("context_basis")
        scenario_context = scenario.get("context_tokens")
        if scenario_context is not None:
            context = scenario_context
            context_source = "case_accepted_state_scenario"
            if basis:
                diagnostics.append(f"context_basis:{basis}")
        elif row_geometry.get("context_basis") != "not_observed_from_cache_capacity" and row_geometry.get("context_tokens") is not None:
            context = row_geometry["context_tokens"]
            context_source = "row_geometry"
        else:
            return {
                "ok": False, "status": "insufficient_evidence",
                "diagnostics": diagnostics + ([] if "context_tokens_not_observed" in diagnostics else ["context_tokens_not_observed"]),
                "needed": ["context_tokens observed or declared by the case scenario"],
            }
    blind, calibration = _strip_measured_overrides(case)
    if calibration["removed_service_regimes"] or calibration["removed_device_rates"]:
        diagnostics.append(
            "removed_measured_overrides:"
            f"service_regimes={len(calibration['removed_service_regimes'])}:"
            f"device_rates={len(calibration['removed_device_rates'])}"
        )
    if calibration["labels"].get("calibration_origin"):
        diagnostics.append(f"case_calibration_origin:{calibration['labels']['calibration_origin']}")
    if calibration["labels"].get("evaluation_relation"):
        diagnostics.append(f"case_evaluation_relation:{calibration['labels']['evaluation_relation']}")
    population_rows = [
        {
            "sequences_per_replica": item.get("sequences_per_replica"),
            "tokens_per_sequence": item.get("tokens_per_sequence"),
            "forward_count": item.get("forward_count"),
            "context_tokens": item.get("context_tokens"),
        }
        for item in populations
    ]
    graph_mode = runtime.get("graph_mode")
    if graph_mode is None:
        graph_mode = runtime.get("graph_capture_mode")
    return {
        "ok": True, "case": blind, "case_path": str(case_path), "phase": phase,
        "deployment_sha256": "",
        "structural_sha256": _structural_sha(blind),
        "parallel": parallel, "sequences": sequences, "tokens": tokens,
        "context": context, "context_source": context_source,
        "population": {k: population.get(k) for k in ("forward_count", "query_rows", "context_basis", "batch_basis")} if population else None,
        "populations": population_rows,
        "frames": frames,
        "calibration": calibration,
        "sku": sku, "diagnostics": diagnostics, "runtime": dict(runtime),
        "graph_mode": graph_mode,
        "mtp_proposal_tokens": 0,
        "source_role": "registered_case_file",
        "source_sha256": source_sha,
        "capture_id": cfg.get("capture_id"),
    }


def _chunk_plan(probe: Mapping[str, Any]) -> list[tuple[int, int, int]] | dict[str, Any]:
    explicit = probe.get("chunk_steps")
    if isinstance(explicit, list) and explicit:
        steps: list[tuple[int, int, int]] = []
        for item in explicit:
            if not isinstance(item, tuple) or len(item) != 3 or not all(isinstance(value, int) for value in item):
                return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["chunk_steps_malformed"]}
            step_tokens, step_context, step_sequences = item
            if step_tokens < 1 or step_sequences < 1 or step_context < 0:
                return {"ok": False, "status": "insufficient_evidence", "diagnostics": ["chunk_steps_not_positive"]}
            steps.append((step_tokens, step_context, step_sequences))
        return steps
    tokens, context, sequences = int(probe["tokens"]), int(probe["context"]), int(probe["sequences"])
    if probe["phase"] != "prefill":
        return [(tokens, context, sequences)]
    runtime = probe["runtime"]
    chunked = runtime.get("enable_chunked_prefill")
    budget = _as_int(runtime.get("max_num_batched_tokens"))
    if chunked is not True or budget is None or budget < 1:
        return [(tokens, context, sequences)]
    per = max(1, budget // max(1, sequences))
    steps: list[tuple[int, int, int]] = []
    done = 0
    remain = tokens
    while remain > 0:
        step = min(per, remain)
        steps.append((step, context + done, sequences))
        done += step
        remain -= step
        if len(steps) > 100000:
            return {"ok": False, "status": "model_rejected", "diagnostics": ["prefill_chunk_plan_did_not_terminate"]}
    return steps


def _op_name(event: Mapping[str, Any]) -> str:
    kind = event.get("native_kind")
    if not kind:
        implementation = event.get("native_implementation")
        if isinstance(implementation, Mapping):
            kind = implementation.get("native_kind")
    if not kind:
        kind = event.get("family")
    return str(kind or "")


def _blank_maps() -> dict[str, dict[str, float]]:
    return {
        "scope": {},
        "canonical": {key: 0.0 for key in _CANONICAL_KEYS},
        "benchmark": {key: 0.0 for key in _BENCHMARK_KEYS},
        "unified": {key: 0.0 for key in _UNIFIED_KEYS},
        "core": {key: 0.0 for key in _CORE_KEYS},
    }


def _add_scope(bucket: dict[str, dict[str, float]], scope: str, elapsed: float) -> None:
    """Add elapsed already resolved to one scope. Does not assign a core."""
    bucket["scope"][scope] = bucket["scope"].get(scope, 0.0) + elapsed
    canonical = _CANONICAL_FAMILY.get(scope, "other")
    benchmark = _BENCHMARK_FAMILY.get(scope, "unclassified")
    unified = _UNIFIED_FAMILY.get(scope, "unclassified")
    bucket["canonical"][canonical] = bucket["canonical"].get(canonical, 0.0) + elapsed
    bucket["benchmark"][benchmark] = bucket["benchmark"].get(benchmark, 0.0) + elapsed
    bucket["unified"][unified] = bucket["unified"].get(unified, 0.0) + elapsed


def _add_elapsed(bucket: dict[str, dict[str, float]], name: str, elapsed: float) -> None:
    """Add family elapsed from the event's declared native name.

    Core time is not assigned here. The engine resource ledger is the only
    core source, and an unnamed resource stays unlabeled.
    """
    _add_scope(bucket, observations.scope_for_op(name), elapsed)


def _string_list(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            found.append(text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            for text in _string_list(item):
                if text not in found:
                    found.append(text)
    return found


def _declared_native_kinds(record: Mapping[str, Any]) -> list[str]:
    """Native function names carried on the compact event. A family label is not one."""
    kinds = _string_list(record.get("native_kind"))
    implementation = record.get("native_implementation")
    if isinstance(implementation, str):
        for text in _string_list(implementation):
            if text not in kinds:
                kinds.append(text)
    elif isinstance(implementation, Mapping):
        for key in ("native_kind", "native_kinds", "op_type"):
            for text in _string_list(implementation.get(key)):
                if text not in kinds:
                    kinds.append(text)
    return kinds


def _declared_engine_text(record: Mapping[str, Any]) -> str:
    """Declared class string, or the first supplied text when it is not a class.

    A resource name is preserved and is not promoted into an accelerator class.
    """
    sources: list[Mapping[str, Any]] = [record]
    implementation = record.get("native_implementation")
    if isinstance(implementation, Mapping):
        sources.append(implementation)
    texts: list[str] = []
    for source in sources:
        for name in _ENGINE_FIELDS:
            value = source.get(name)
            if isinstance(value, str) and value.strip():
                text = value.strip()
                if text not in texts:
                    texts.append(text)
    for text in texts:
        if text in _CORE_CANON:
            return text
    return texts[0] if texts else ""


def _record_identity(record: Mapping[str, Any]) -> dict[str, Any]:
    """One compact event's native names and, when declared, its accelerator class.

    Disagreeing native kinds stay partial. The elapsed is not split across them
    and a family or program name is not read as a physical core.
    """
    kinds = _declared_native_kinds(record)
    raw_engine = _declared_engine_text(record)
    engine = _CORE_CANON.get(raw_engine)
    if len(kinds) == 1:
        scope = observations.scope_for_op(kinds[0])
        return {
            "native_kinds": kinds,
            "native_op": kinds[0],
            "native_selection": "declared",
            "family_scope": scope,
            "family_identity": "declared_kind" if scope != "other" else "declared_kind_unscoped",
            "engine": engine,
            "declared_engine": raw_engine or None,
        }
    if len(kinds) > 1:
        scopes = {observations.scope_for_op(kind) for kind in kinds}
        agreed = next(iter(scopes)) if len(scopes) == 1 else None
        return {
            "native_kinds": kinds,
            "native_op": None,
            "native_selection": "unselected_variants",
            "family_scope": agreed,
            "family_identity": "partial_kinds" if agreed is None else (
                "declared_kind" if agreed != "other" else "declared_kind_unscoped"
            ),
            "engine": engine,
            "declared_engine": raw_engine or None,
        }
    family = record.get("family")
    family_name = family.strip() if isinstance(family, str) else ""
    return {
        "native_kinds": [],
        "native_op": None,
        "native_selection": "absent",
        "family_scope": observations.scope_for_op(family_name) if family_name else "other",
        "family_identity": "family_label" if family_name else "absent",
        "engine": engine,
        "declared_engine": raw_engine or None,
    }


def _regime_id(regime: Any) -> str:
    if isinstance(regime, Mapping):
        return str(regime.get("id") or "unnamed_service_regime")
    return "unnamed_service_regime"


def _strip_measured_overrides(case: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Remove validation-corpus service timing before compile.

    Every ``service_regimes`` list is dropped, including unlabeled fixed or
    knotted rules and copies nested under metadata. Kernel programs and
    lowerings stay. Hardware catalog rates stay. Observed busy-time rates,
    which are not catalog peaks, are removed with the rules that named them.
    """
    blind = copy.deepcopy(dict(case))
    runtime = blind.get("runtime") if isinstance(blind.get("runtime"), dict) else {}
    metadata = runtime.get("metadata") if isinstance(runtime.get("metadata"), dict) else {}
    evidence = metadata.get("calibration_evidence") if isinstance(metadata.get("calibration_evidence"), dict) else {}
    labels = {
        "calibration_origin": metadata.get("calibration_origin") or evidence.get("calibration_origin"),
        "evaluation_relation": evidence.get("evaluation_relation") or metadata.get("evaluation_relation"),
        "json_pointer": evidence.get("json_pointer"),
    }
    removed_regimes: list[str] = []
    removed_nested: list[str] = []

    def _drop_regimes(holder: dict[str, Any]) -> None:
        regimes = holder.get("service_regimes")
        if regimes is None:
            return
        if isinstance(regimes, list):
            removed_regimes.extend(_regime_id(item) for item in regimes)
        else:
            removed_regimes.append(_regime_id(regimes))
        holder.pop("service_regimes", None)

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if "service_regimes" in node:
                _drop_regimes(node)
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(blind)
    kernels = runtime.get("kernels") if isinstance(runtime.get("kernels"), dict) else None
    if isinstance(kernels, dict):
        for key in list(kernels):
            if key in _STRUCTURAL_KERNEL_KEYS:
                continue
            value = kernels.get(key)
            if isinstance(value, dict) and any(name in value for name in _TIMING_PAYLOAD_KEYS):
                removed_nested.append(f"runtime.kernels.{key}")
                kernels.pop(key, None)
    if isinstance(metadata, dict):
        for key in list(metadata):
            if key in {"calibration_origin", "evaluation_relation"}:
                continue
            value = metadata.get(key)
            if key == "calibration_evidence" and isinstance(value, dict):
                for child in list(value):
                    if child in {"evaluation_relation", "calibration_origin", "json_pointer"}:
                        continue
                    payload = value.get(child)
                    timed = child in _TIMING_PAYLOAD_KEYS or (
                        isinstance(payload, dict) and any(name in payload for name in _TIMING_PAYLOAD_KEYS)
                    )
                    if timed or child in {"service_regimes", "response", "execution"}:
                        removed_nested.append(f"runtime.metadata.calibration_evidence.{child}")
                        value.pop(child, None)
                continue
            if isinstance(value, dict) and any(name in value for name in _TIMING_PAYLOAD_KEYS):
                removed_nested.append(f"runtime.metadata.{key}")
                metadata.pop(key, None)
    removed_rates: list[str] = []
    machine = blind.get("machine") if isinstance(blind.get("machine"), dict) else None
    device = machine.get("device") if isinstance(machine, dict) and isinstance(machine.get("device"), dict) else None
    if isinstance(device, dict):
        work_units = device.get("work_units") if isinstance(device.get("work_units"), dict) else {}
        drop = {
            str(key) for key, unit in work_units.items()
            if str(key).startswith("observed_") or str(unit).lower() in {"busy_ns", "busy_us", "busy_ms"}
        }
        for bucket in ("rates", "work_units", "resource_units"):
            mapping = device.get(bucket)
            if not isinstance(mapping, dict):
                continue
            for key in list(mapping):
                if str(key).startswith("observed_") or str(key) in drop:
                    if bucket == "rates":
                        removed_rates.append(str(key))
                    mapping.pop(key, None)
    relation = str(labels.get("evaluation_relation") or "").lower()
    origin = str(labels.get("calibration_origin") or "").lower()
    return blind, {
        "labels": labels,
        "removed_service_regimes": removed_regimes,
        "removed_nested_timing": removed_nested,
        "removed_device_rates": removed_rates,
        "prediction_consumed_measured_overrides": False,
        "source_case_declares_in_sample": "in_sample" in relation or origin == "observed",
    }


def _round_map(values: Mapping[str, float]) -> dict[str, float]:
    return {key: round(float(value), 9) for key, value in sorted(values.items())}


def _reassign_declared_kind_families(profile: Mapping[str, Any], bucket: dict[str, dict[str, float]]) -> None:
    """Move a by_family lump when every replica declares kinds that agree on one scope.

    The lump is the original family elapsed, so the move does not resplit duration.
    A family with any unlabeled or disagreeing replica stays where the family name put it.
    """
    families = profile.get("by_family") if isinstance(profile.get("by_family"), Mapping) else {}
    operators = profile.get("by_operator") if isinstance(profile.get("by_operator"), Mapping) else {}
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for stats in operators.values():
        if not isinstance(stats, Mapping):
            continue
        replicas = stats.get("replicas") if isinstance(stats.get("replicas"), Mapping) else {}
        for record in replicas.values():
            if not isinstance(record, Mapping) or record.get("family") == "barrier":
                continue
            family = record.get("family")
            if isinstance(family, str) and family:
                grouped.setdefault(family, []).append(record)
    for family, records in grouped.items():
        identities = [_record_identity(record) for record in records]
        if any(not item["native_kinds"] or item["family_identity"] == "partial_kinds" for item in identities):
            continue
        scopes = {item["family_scope"] for item in identities}
        if len(scopes) != 1:
            continue
        scope = next(iter(scopes))
        current = observations.scope_for_op(family)
        if not isinstance(scope, str) or scope == current:
            continue
        stats = families.get(family)
        elapsed = stats.get("elapsed_ms") if isinstance(stats, Mapping) else None
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        _add_scope(bucket, current, -float(elapsed))
        _add_scope(bucket, scope, float(elapsed))


def _classify_compact_profile(profile: Mapping[str, Any]) -> tuple[dict[str, dict[str, float]], float, int]:
    """Family elapsed from compact operator identity, or from by_family when names are absent.

    Compact operator rows on the current engine omit native_kind and family at the
    top level. Replica native_kind and native_kinds are the declared function.
    Names the existing scope map does not recognize stay in ``other``.
    """
    bucket = _blank_maps()
    elapsed_sum = 0.0
    counted = 0
    operators = profile.get("by_operator") if isinstance(profile.get("by_operator"), Mapping) else {}
    named: list[tuple[str, float, int]] = []
    unnamed_elapsed = 0.0
    for stats in operators.values():
        if not isinstance(stats, Mapping) or stats.get("family") == "barrier":
            continue
        elapsed = stats.get("elapsed_ms")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        events = stats.get("operator_events")
        event_count = int(events) if isinstance(events, int) and events > 0 else 1
        counted += event_count
        name = _op_name(stats)
        if name:
            named.append((name, float(elapsed), event_count))
        else:
            unnamed_elapsed += float(elapsed)
    if named:
        for name, elapsed, _event_count in named:
            elapsed_sum += elapsed
            _add_elapsed(bucket, name, elapsed)
        elapsed_sum += unnamed_elapsed
        if unnamed_elapsed:
            _add_elapsed(bucket, "", unnamed_elapsed)
        return bucket, elapsed_sum, counted
    families = profile.get("by_family") if isinstance(profile.get("by_family"), Mapping) else {}
    if not families:
        return bucket, unnamed_elapsed, counted
    elapsed_sum = 0.0
    for name, stats in families.items():
        if str(name) == "barrier":
            continue
        elapsed = stats.get("elapsed_ms") if isinstance(stats, Mapping) else stats
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        elapsed_sum += float(elapsed)
        _add_elapsed(bucket, str(name), float(elapsed))
    _reassign_declared_kind_families(profile, bucket)
    return bucket, elapsed_sum, counted


def _native_op_name(record: Mapping[str, Any]) -> str:
    """Declared native operator name. A family label is not an op type.

    Several unselected variants do not collapse to the first name.
    """
    kinds = _declared_native_kinds(record)
    if len(kinds) == 1:
        return kinds[0]
    return ""


def _bound_engine(record: Mapping[str, Any]) -> str:
    """Canonical accelerator class only when the record declares one.

    Resource names are not cores. An absent or unknown binding stays unbound.
    """
    raw = _declared_engine_text(record)
    mapped = _CORE_CANON.get(raw)
    return mapped or ""


def _program_ledger(profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Additive rank/phase rows from the compact program. Not a step and not a core guess."""
    rows: list[dict[str, Any]] = []
    operators = profile.get("by_operator") if isinstance(profile.get("by_operator"), Mapping) else {}
    for frame_id, stats in operators.items():
        if not isinstance(stats, Mapping):
            continue
        op_id = str(stats.get("op_id") or "")
        replicas = stats.get("replicas") if isinstance(stats.get("replicas"), Mapping) else {}
        for rank, record in replicas.items():
            if not isinstance(record, Mapping) or record.get("family") == "barrier":
                continue
            elapsed = record.get("elapsed_ms")
            events = record.get("operator_events")
            identity = _record_identity(record)
            unit = record.get("unit")
            rows.append({
                "rank_id": rank,
                "phase": record.get("phase"),
                "frame_id": str(frame_id),
                "op_id": op_id,
                "family": record.get("family"),
                "recipe": record.get("recipe"),
                "program": record.get("program"),
                "fusion_role": record.get("fusion_role"),
                "native_op": identity["native_op"],
                "native_kinds": list(identity["native_kinds"]),
                "native_selection": identity["native_selection"],
                "family_scope": identity["family_scope"],
                "family_identity": identity["family_identity"],
                "engine": identity["engine"],
                "declared_engine": identity["declared_engine"],
                "count": int(events) if isinstance(events, int) and events > 0 else None,
                "elapsed_ms": round(float(elapsed), 9) if isinstance(elapsed, (int, float)) and math.isfinite(float(elapsed)) else None,
                "unit": unit if isinstance(unit, str) and unit else "ms",
                "basis": "additive",
            })
    return rows


def _core_publication(rows: Sequence[Mapping[str, Any]], elapsed_total: float) -> dict[str, Any]:
    """Publish accelerator-core elapsed from declared classes only.

    Each row is one kernel duration. The sum is not divided by a forward-window
    count and is not a share of the step scalar. Unknown mass stays off every
    core. None is unbound, not zero. A partial map is not a complete forecast.
    """
    bound_mass = {key: 0.0 for key in _CORE_KEYS}
    bound_sum = 0.0
    unresolved = 0.0
    bound_ranks: set[Any] = set()
    saw_bound = False
    for row in rows:
        elapsed = row.get("elapsed_ms")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        value = float(elapsed)
        unit = row.get("unit")
        engine = row.get("engine")
        if unit not in (None, "", "ms") or not isinstance(engine, str) or engine not in _CORE_KEYS:
            unresolved += value
            continue
        bound_mass[engine] += value
        bound_sum += value
        saw_bound = True
        rank = row.get("rank_id")
        if rank not in (None, ""):
            bound_ranks.add(rank)
    multi = len(bound_ranks) > 1
    if not saw_bound or multi:
        published = _unverified_cores()
        status = "withheld_multi_rank" if multi else "unresolved"
        unresolved_out = round(float(elapsed_total), 9)
        bound_out = 0.0
    else:
        published = {
            key: (round(bound_mass[key], 9) if bound_mass[key] > 0.0 else None)
            for key in _CORE_KEYS
        }
        status = "partial" if unresolved > 0.0 else "source_bound"
        unresolved_out = round(unresolved, 9)
        bound_out = round(bound_sum, 9)
    return {
        "predicted_by_core_ms": published,
        "cores_unnamed_by_engine": [key for key, value in published.items() if value is None],
        "core_forecast": status,
        "core_map_is_complete_forecast": status == "source_bound",
        "bound_core_elapsed_ms": bound_out,
        "unresolved_core_elapsed_ms": unresolved_out,
    }


def _identity_totals(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Per native-op elapsed counted once. Disagreeing kinds are not split."""
    recovered: dict[str, float] = {}
    unresolved: dict[str, float] = {}
    partial_ms = 0.0
    for row in rows:
        elapsed = row.get("elapsed_ms")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        value = float(elapsed)
        status = str(row.get("family_identity") or "absent")
        kinds = [str(item) for item in (row.get("native_kinds") or ())]
        label = str(row.get("native_op") or "") or ("+".join(kinds) if kinds else "")
        scope = row.get("family_scope")
        if status == "partial_kinds":
            partial_ms += value
            key = label or str(row.get("family") or "partial")
            unresolved[key] = unresolved.get(key, 0.0) + value
            continue
        if status == "declared_kind" and scope not in (None, "", "other"):
            key = label or str(row.get("family") or "declared")
            recovered[key] = recovered.get(key, 0.0) + value
            continue
        if scope in (None, "", "other"):
            key = label or str(row.get("family") or "unscoped")
            unresolved[key] = unresolved.get(key, 0.0) + value
    return {
        "recovered_native_kind_ms": _round_map(recovered),
        "unresolved_family_identity_ms": _round_map(unresolved),
        "partial_kind_elapsed_ms": round(partial_ms, 9),
    }


def _operator_groups_from_ledger(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Exact op x engine groups only. Family rows and unbound engines stay out of this population."""
    bound = [row for row in rows if row.get("native_op") and row.get("engine")]
    if not bound:
        return [], "absent_no_native_op_engine_binding"
    ranks = {row.get("rank_id") for row in bound}
    if len(ranks) > 1:
        return [], "withheld_multi_rank_until_observation_keys_match"
    bucket: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in bound:
        key = (row.get("native_op"), row.get("engine"), row.get("rank_id"), row.get("phase"))
        acc = bucket.setdefault(key, {"count": 0, "elapsed_ms": 0.0})
        if isinstance(row.get("count"), int):
            acc["count"] += int(row["count"])
        if isinstance(row.get("elapsed_ms"), (int, float)):
            acc["elapsed_ms"] += float(row["elapsed_ms"])
    groups = []
    for (op_type, engine, rank, phase), acc in bucket.items():
        item = {
            "op_type": op_type,
            "engine": engine,
            "count": acc["count"],
            "boundary_ms": round(acc["elapsed_ms"], 9),
            "basis": "additive",
            "unit": "ms",
        }
        if rank not in (None, ""):
            item["rank_id"] = rank
        if phase not in (None, ""):
            item["phase"] = phase
        groups.append(item)
    return groups, "source_bound_op_engine"


def _graph_once(case: Mapping[str, Any], phase: str, tokens: int, context: int,
                sequences: int | Sequence[int]) -> dict[str, Any]:
    from mindie_sim.prediction.body import body_forward
    from mindie_sim.schema.common import ModelingError

    # Same sku, phase, and token geometry is one body. A different context is not grouped.
    sequence_key = tuple(sequences) if isinstance(sequences, (list, tuple)) else sequences
    equivalence = (_structural_sha(case), phase, tokens, context, sequence_key)
    cached = _STEP_EQUIVALENCE.get(equivalence)
    if cached is not None:
        return dict(cached)
    try:
        # compact drops the per-event timeline. Costs and the dependency
        # schedule are the same graph; the profile keeps every non-barrier
        # operator elapsed under its declared identity.
        result = body_forward(
            case, phase=phase, tokens=tokens, context=context, sequences=sequences,
            event_limit=0, compact=True,
        )
    except ModelingError as exc:
        return {"ok": False, "status": "model_rejected", "diagnostics": [str(exc)]}
    profile = result.get("profile") if isinstance(result.get("profile"), Mapping) else None
    if not isinstance(profile, Mapping):
        return {"ok": False, "status": "model_rejected", "diagnostics": ["compact_profile_absent"]}
    bucket, elapsed_sum, counted = _classify_compact_profile(profile)
    ledger = _program_ledger(profile)
    core_pub = _core_publication(ledger, elapsed_sum)
    resources = []
    for row in result.get("resources") or ():
        if not isinstance(row, Mapping):
            continue
        busy = row.get("busy_ms")
        busy_ms = float(busy) if isinstance(busy, (int, float)) and math.isfinite(float(busy)) else None
        resources.append({
            "resource": row.get("resource"),
            "busy_ms": busy_ms,
            "capacity_bound_ms": row.get("capacity_bound_ms"),
            "unit": row.get("unit"),
        })
    engine_geometry = result.get("geometry") if isinstance(result.get("geometry"), Mapping) else {}
    priced = {
        "ok": True,
        "body_forward_ms": float(result["body_forward_ms"]),
        "family_elapsed_ms": elapsed_sum,
        "operator_events": counted,
        "by_scope_ms": bucket["scope"],
        "by_canonical_ms": bucket["canonical"],
        "by_benchmark_ms": bucket["benchmark"],
        "by_unified_ms": bucket["unified"],
        "by_core_ms": core_pub["predicted_by_core_ms"],
        "core_forecast": core_pub["core_forecast"],
        "core_map_is_complete_forecast": core_pub["core_map_is_complete_forecast"],
        "unresolved_core_elapsed_ms": core_pub["unresolved_core_elapsed_ms"],
        "resources": resources,
        "additive_rows": ledger,
        "engine_query": {
            "valid_query_tokens": engine_geometry.get("valid_query_tokens"),
            "graph_query_tokens": engine_geometry.get("graph_query_tokens"),
            "padded_query_tokens": engine_geometry.get("padded_query_tokens"),
            "sequences_by_replica": engine_geometry.get("sequences_by_replica"),
            "valid_query_tokens_by_replica": engine_geometry.get("valid_query_tokens_by_replica"),
            "graph_query_tokens_by_replica": engine_geometry.get("graph_query_tokens_by_replica"),
            "padded_query_tokens_by_replica": engine_geometry.get("padded_query_tokens_by_replica"),
            "physical_global_ranks_by_replica": engine_geometry.get("physical_global_ranks_by_replica"),
            "physical_global_rank_basis": engine_geometry.get("physical_global_rank_basis"),
        },
    }
    _STEP_EQUIVALENCE[equivalence] = priced
    return dict(priced)


def _cache_key(probe: Mapping[str, Any], steps: Sequence[tuple[int, int, int]]) -> tuple[Any, ...]:
    """One deployment, phase, and query. A shared weights path is not a deployment."""
    return (
        str(probe.get("deployment_sha256") or ""),
        str(probe.get("structural_sha256") or ""),
        str(probe.get("case_path") or ""),
        probe.get("phase"),
        probe.get("sku"),
        tuple(sorted((probe.get("parallel") or {}).items())),
        tuple(steps),
        (tuple(probe["body_sequences"]) if isinstance(probe.get("body_sequences"), (list, tuple))
         else None),
        probe.get("graph_mode"),
        int(probe.get("mtp_proposal_tokens") or 0),
    )


def _structural_workload(phase: str, sequences: int, tokens: int, context: int) -> dict[str, Any]:
    """Workload required to parse a case. The body query is the explicit arguments."""
    if phase == "prefill":
        prompt, output, prefix = tokens, 1, 0
    else:
        prompt, output, prefix = context, tokens, 0
    return {
        "num_requests": sequences,
        "prompt_tokens": prompt,
        "output_tokens": output,
        "prefix_tokens": prefix,
        "synthetic": True,
    }


def _failure_probe(status: str, diagnostics: Sequence[str], needed: Sequence[str] | None, role: str) -> dict[str, Any]:
    return {
        "ok": False,
        "status": status or "insufficient_evidence",
        "diagnostics": list(diagnostics),
        "needed": list(needed or []),
        "source_role": role,
    }


def _labeled_hardware_candidates(diagnostics: Sequence[str]) -> list[dict[str, Any]]:
    """Keep every declared SKU. Nothing here chooses the easier body."""
    found: list[str] = []
    for item in diagnostics:
        text = str(item)
        if not text.startswith("candidate:"):
            continue
        sku = text.split(":", 1)[1]
        if sku and sku not in found:
            found.append(sku)
    if len(found) < 2:
        return []
    return [{"sku": sku, "priced": False, "label": sku, "selected": False} for sku in found]


def _declared_catalog_skus(rows: Any) -> list[str]:
    """Catalogue identities in source order. Elapsed time does not sort them."""
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return []
    found: list[str] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        sku = row.get("catalog_sku")
        if isinstance(sku, str) and sku and sku not in found:
            found.append(sku)
    return found


def _campaign_probe(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Consume J's declaration. Do not rewrite graph mode, batch, or quant."""
    role = "campaign_declaration"
    if not resolved.get("ok"):
        diagnostics = [str(item) for item in (resolved.get("diagnostics") or [])]
        failure = _failure_probe(
            str(resolved.get("status") or "insufficient_evidence"),
            diagnostics,
            resolved.get("needed") or [],
            role,
        )
        candidates = _labeled_hardware_candidates(diagnostics)
        if candidates:
            failure["hardware_candidates"] = candidates
            failure["hardware_selection"] = "not_selected"
        return failure
    diagnostics = [str(item) for item in (resolved.get("diagnostics") or [])]
    source = resolved.get("source") if isinstance(resolved.get("source"), Mapping) else {}
    model = source.get("model") if isinstance(source.get("model"), Mapping) else {}
    if model.get("heterogeneous_weight_classes") or any(
        "quant_policy_reduced_to_dominant_weight_class" in item for item in diagnostics
    ):
        diagnostics.append("missing_work:per_tensor_weight_class_contract")
        return _failure_probe("insufficient_evidence", diagnostics, ["per-tensor weight class contract"], role)
    if any("mixed_window" in item for item in diagnostics):
        return _failure_probe("insufficient_evidence", diagnostics, ["single-phase declared population"], role)
    mtp = int(resolved.get("mtp_proposal_tokens") or 0)
    tokens = resolved.get("tokens")
    sequences = resolved.get("sequences")
    context = resolved.get("context")
    if not isinstance(tokens, int) or not isinstance(sequences, int) or not isinstance(context, int):
        return _failure_probe("insufficient_evidence", diagnostics + ["campaign_query_not_declared"], ["tokens", "sequences", "context"], role)
    measurement_role = str(resolved.get("measurement_role") or "active")
    normal_body_eligible = resolved.get("normal_body_eligible") is not False
    body_sequences = resolved.get("body_sequences")
    if body_sequences is not None:
        dp = int((resolved.get("parallel") or {}).get("dp") or 0)
        if (not isinstance(body_sequences, Sequence) or isinstance(body_sequences, (str, bytes))
                or len(body_sequences) != dp or any(type(value) is not int or value < 0 for value in body_sequences)
                or not any(body_sequences)):
            diagnostics.append("campaign_body_sequences_not_complete_per_dp")
            return _failure_probe("insufficient_evidence", diagnostics, ["complete nonnegative per-DP sequence vector"], role)
    if mtp > 0 and tokens < 1 + mtp:
        diagnostics.append(f"missing_work:speculative_proposal_tokens_{mtp}_not_in_declared_query_{tokens}")
        return _failure_probe("insufficient_evidence", diagnostics, ["declared target and draft query rows"], role)
    case = resolved.get("case")
    if not isinstance(case, Mapping):
        return _failure_probe("insufficient_evidence", diagnostics + ["campaign_case_absent"], ["composed case"], role)
    blind, calibration = _strip_measured_overrides(case)
    if calibration["removed_service_regimes"] or calibration["removed_device_rates"] or calibration["removed_nested_timing"]:
        diagnostics.append(
            "removed_measured_overrides:"
            f"service_regimes={len(calibration['removed_service_regimes'])}:"
            f"device_rates={len(calibration['removed_device_rates'])}:"
            f"nested={len(calibration['removed_nested_timing'])}"
        )
    geometry = resolved.get("geometry") if isinstance(resolved.get("geometry"), Mapping) else {}
    if geometry.get("rank_batch_observed") is False:
        diagnostics.append("rank_batch_is_declared_concurrency_over_dp_upper_bound")
    if geometry.get("sequences_observed") is False:
        diagnostics.append("sequences_are_declared_upper_bound")
    if geometry.get("actual_q_observed") is False:
        diagnostics.append("query_is_declared_policy_not_observed")
    runtime = blind.get("runtime") if isinstance(blind.get("runtime"), Mapping) else {}
    export = source.get("export_rank") if isinstance(source.get("export_rank"), Mapping) else {}
    export_rank = None
    if export.get("rank_observed") is True and export.get("rank_id") is not None:
        export_rank = {
            "rank_id": export.get("rank_id"),
            "rank_observed": True,
            "batch_observed": bool(export.get("batch_observed")),
            "profiler_info_sha256": str(export.get("sha256") or ""),
        }
    deployment = str(resolved.get("deployment_sha256") or "")
    population = resolved.get("population") if isinstance(resolved.get("population"), Mapping) else None
    return {
        "ok": True,
        "case": blind,
        "case_path": str(resolved.get("case_path") or ""),
        "deployment_sha256": deployment,
        "structural_sha256": _structural_sha(blind),
        "phase": str(resolved.get("phase") or ""),
        "parallel": dict(resolved.get("parallel") or {}),
        "sequences": sequences,
        "tokens": tokens,
        "context": context,
        "context_source": str(resolved.get("context_source") or "declared_launch_isv"),
        "population": population,
        "populations": [],
        "frames": [],
        "calibration": calibration,
        "sku": str(resolved.get("sku") or ""),
        "source_image": str(resolved.get("source_image") or ""),
        "diagnostics": diagnostics,
        "runtime": dict(runtime),
        "graph_mode": resolved.get("graph_mode"),
        "mtp_proposal_tokens": mtp,
        "speculative_method": resolved.get("speculative_method"),
        "source_role": role,
        "source_sha256": deployment,
        "source_sha_basis": "deployment_identity" if deployment else "",
        "sequences_observed": geometry.get("sequences_observed"),
        "sequences_upper_bound": geometry.get("sequences_upper_bound"),
        "tokens_basis": geometry.get("tokens_basis"),
        "actual_q_observed": geometry.get("actual_q_observed"),
        "rank_batch_observed": geometry.get("rank_batch_observed"),
        "export_rank": export_rank,
        "body_sequences": body_sequences,
        "measurement_role": measurement_role,
        "normal_body_eligible": normal_body_eligible,
        "physical_rank": (dict(resolved["physical_rank"])
                          if isinstance(resolved.get("physical_rank"), Mapping) else None),
        "active_physical_rank": (dict(resolved["active_physical_rank"])
                                 if isinstance(resolved.get("active_physical_rank"), Mapping) else None),
        "idle_physical_rank": (dict(resolved["idle_physical_rank"])
                               if isinstance(resolved.get("idle_physical_rank"), Mapping) else None),
    }


_ARCHIVE_CONFIGURED = False


def _canonical_receipt_index() -> Path:
    """Prefer an index that lives with the archives.

    The task-local file is used only when it is the sole index and its rows
    name canonical archive paths. Callers record that distinction.
    """
    shipped = (
        Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030/observation_receipt_index.tsv"),
        Path("/Volumes/data/mindie-sim-data/observation_receipt_index.tsv"),
        _STRUCT_DIR / "observation_receipt_index.tsv",
    )
    for candidate in shipped:
        if candidate.is_file():
            return candidate
    task_local = Path("/tmp/mindie-3h-20261111/observation_receipt_index.tsv")
    if task_local.is_file():
        return task_local
    return shipped[0]


def _ensure_archive():
    global _ARCHIVE_CONFIGURED
    import fleet_archive_case as archive

    if not _ARCHIVE_CONFIGURED:
        archive.configure_archive_roots(
            data_roots=(
                Path("/Volumes/data/mindie-sim-data"),
                Path("/Users/maoxx241/code/mindie-agent/.workstreams"),
            ),
            results_dir=_STRUCT_DIR / "results",
            cases_dir=CASES_DIR,
            archive_root=Path("/Volumes/data/mindie-sim-data/acceptance-archives-20261030"),
            receipt_index=_canonical_receipt_index(),
            cases_index=CASES_INDEX_PATH,
        )
        _ARCHIVE_CONFIGURED = True
    return archive


def _env_integers(path: Path) -> dict[str, int]:
    """Explicit KEY=integer assignments. Timing keys are not read."""
    wanted = {
        "PREFIX_LEN": "prefix_len",
        "INPUT_LEN": "input_len",
        "OUTPUT_LEN": "output_len",
        "CONCURRENCY": "concurrency",
        "SPEC_K": "spec_k",
    }
    found: dict[str, int] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        name = wanted.get(key.strip())
        if name is None:
            continue
        number = _as_int(value.strip().strip("'\""))
        if number is not None:
            found[name] = number
    if found:
        found_basis = "meta.env"
        return {"basis": found_basis, **{key: value for key, value in found.items()}}
    return {}


def _run_meta_workload(path: Path) -> dict[str, Any]:
    """Declared workload only. The metrics object is not read."""
    document = json.loads(path.read_text(encoding="utf-8"))
    workload = document.get("workload") if isinstance(document, dict) else None
    if not isinstance(workload, dict):
        return {}
    found: dict[str, Any] = {"basis": "run_meta.workload"}
    for key in ("prefix_len", "input_len", "output_len", "concurrency"):
        number = _as_int(workload.get(key))
        if number is not None:
            found[key] = number
    return found


def _campaign_spec(script_text: str, tag: str) -> dict[str, Any]:
    """Positional run_prof arguments for this cell tag. No duration fields."""
    marker = f'{tag}"'
    index = -1
    bits: list[str] = []
    cursor = 0
    while cursor < len(script_text):
        found = script_text.find(marker, cursor)
        if found < 0:
            break
        quote_start = script_text.rfind('"', 0, found)
        spec = script_text[quote_start + 1:found] if quote_start >= 0 else ""
        candidate = spec.split()
        if len(candidate) >= 2 and candidate[0].isdigit() and candidate[1].isdigit():
            index = found
            bits = candidate
            break
        cursor = found + len(marker)
    if index < 0 or len(bits) < 2:
        return {}
    call = None
    for line in script_text[index:].splitlines():
        stripped = line.strip()
        if stripped.startswith("run_prof "):
            call = stripped.split()
            break
    if call is None or len(call) < 5 or not call[4].isdigit():
        return {}
    return {
        "basis": "campaign_script_run_prof",
        "concurrency": int(bits[0]),
        "input_len": int(bits[1]),
        "prefix_len": int(call[4]),
    }


def _prefix_declaration_note(source: Path) -> str:
    """Name the disagreeing designed integers. Observed cache counters are not read."""
    directory = source.parent if source.is_file() else source
    folders = [directory, *list(directory.parents)[:4]]
    parts: list[str] = []
    for folder in folders:
        env = folder / "meta.env"
        if not env.is_file():
            continue
        parsed = _env_integers(env)
        if "prefix_len" in parsed:
            parts.append(f"meta.env.PREFIX_LEN={parsed['prefix_len']}")
            break
    for folder in folders:
        meta = folder / "run_meta.json"
        if not meta.is_file():
            continue
        parsed = _run_meta_workload(meta)
        if "prefix_len" in parsed:
            parts.append(f"run_meta.workload.prefix_len={parsed['prefix_len']}")
            break
    for folder in folders:
        found = False
        for path in sorted(folder.glob("*.json")):
            if path.name == "run_meta.json" or path.stat().st_size > 2_000_000:
                continue
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            summary = document.get("summary") if isinstance(document, dict) else None
            design = summary.get("design") if isinstance(summary, dict) else None
            if not isinstance(design, dict):
                continue
            shared = _as_int(design.get("shared_tokens"))
            fresh = _as_int(design.get("fresh_tokens"))
            prompt = _as_int(design.get("prompt_tokens"))
            if shared is None and fresh is None:
                continue
            parts.append(
                f"{path.name}.design.shared_tokens={shared}:fresh_tokens={fresh}:prompt_tokens={prompt}"
            )
            found = True
            break
        if found:
            break
    return "declared_prefix_values:" + ",".join(parts) if parts else ""


def _declared_launch(source: Path) -> dict[str, Any]:
    """Prefix, input, and concurrency written beside the verified kernel source.

    A missing prefix stays missing. It is not filled from a prompt length or
    from a measured cache hit.
    """
    directory = source.parent if source.is_file() else source
    folders = [directory, *list(directory.parents)[:4]]
    declarations: list[dict[str, Any]] = []
    for folder in folders:
        env = folder / "meta.env"
        if env.is_file():
            parsed = _env_integers(env)
            if parsed:
                declarations.append(parsed)
                break
    for folder in folders:
        meta = folder / "run_meta.json"
        if meta.is_file():
            parsed = _run_meta_workload(meta)
            if parsed.get("prefix_len") is not None or parsed.get("input_len") is not None:
                declarations.append(parsed)
                break
    if not any("prefix_len" in item for item in declarations):
        for folder in folders:
            for script in sorted(folder.glob("run_*.sh")):
                parsed = _campaign_spec(script.read_text(encoding="utf-8", errors="replace"), directory.name)
                if parsed:
                    declarations.append(parsed)
                    break
            if any(item.get("basis") == "campaign_script_run_prof" for item in declarations):
                break
    merged: dict[str, Any] = {}
    bases: list[str] = []
    for item in declarations:
        bases.append(str(item.get("basis") or ""))
        for key in ("prefix_len", "input_len", "output_len", "concurrency", "spec_k"):
            if key not in item:
                continue
            if key in merged and merged[key] != item[key]:
                return {"conflict": f"launch_{key}_disagrees:{merged[key]}!={item[key]}", "basis": "+".join(bases)}
            merged[key] = item[key]
    merged["basis"] = "+".join(base for base in bases if base)
    return merged


def _receipt_forward_frames(paths: Sequence[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Forward identity and query rows. Span times are not kept."""
    notes: list[str] = []
    chosen: list[dict[str, Any]] | None = None
    for text in paths:
        if not isinstance(text, str) or not text:
            continue
        path = Path(text)
        if not path.is_file():
            notes.append(f"receipt_forward_file_missing:{path.name}")
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        observed = document.get("observed") if isinstance(document, dict) and isinstance(document.get("observed"), dict) else document
        frames: list[dict[str, Any]] = []
        if isinstance(observed, dict):
            for forward in observed.get("forwards") or ():
                if not isinstance(forward, dict):
                    continue
                body = forward.get("body") if isinstance(forward.get("body"), dict) else {}
                forward_rank = forward.get("rank_id")
                forward_device = forward.get("device_id")
                body_device = body.get("device_id")
                frames.append({
                    "forward_id": forward.get("forward_id"),
                    "phase": forward.get("phase"),
                    "rank_id": forward_rank if forward_rank not in (None, "") else None,
                    "device_id": forward_device if forward_device not in (None, "") else None,
                    "body_device_id": body_device if body_device not in (None, "") else None,
                    "query_rows": _as_int(forward.get("query_rows")),
                })
        del document
        if not frames:
            notes.append(f"receipt_has_no_forwards:{path.name}")
            continue
        signature = tuple(item.get("query_rows") for item in frames)
        if chosen is None:
            chosen = frames
            continue
        if tuple(item.get("query_rows") for item in chosen) != signature:
            return [], notes + ["receipt_forward_query_rows_disagree"]
    return chosen or [], notes


def _schedule_from_launch(frames: Sequence[Mapping[str, Any]], launch: Mapping[str, Any]) -> tuple[list[tuple[int, int, int]] | None, list[str]]:
    """One body step per receipt forward. Context is the declared prefix plus prior query rows."""
    if launch.get("conflict"):
        return None, [str(launch["conflict"])]
    prefix = launch.get("prefix_len")
    if not isinstance(prefix, int) or prefix < 0:
        return None, ["missing_work:declared_prefix_not_in_launch_record"]
    queries: list[int] = []
    for frame in frames:
        query = frame.get("query_rows")
        if not isinstance(query, int) or query < 1:
            return None, ["receipt_query_rows_absent"]
        queries.append(query)
    if not queries:
        return None, ["receipt_query_rows_absent"]
    input_len = launch.get("input_len")
    if isinstance(input_len, int) and sum(queries) != input_len:
        return None, [f"receipt_query_sum_{sum(queries)}_disagrees_with_declared_input_{input_len}"]
    concurrency = launch.get("concurrency")
    if concurrency is None:
        return None, ["missing_work:declared_concurrency_absent"]
    if not isinstance(concurrency, int) or concurrency < 1:
        return None, ["declared_concurrency_not_positive"]
    notes = [
        "context_zero_is_declared_initial_cache" if prefix == 0 else "context_is_declared_prefix",
        f"launch_basis:{launch.get('basis') or 'undeclared'}",
        "prefill_chunks_follow_receipt_forward_order",
    ]
    if concurrency != 1:
        if len(queries) == 1 and isinstance(input_len, int) and queries[0] == input_len * concurrency:
            return [(input_len, prefix, concurrency)], notes
        return None, notes + ["missing_work:concurrency_above_1_chunk_geometry_not_declared"]
    steps: list[tuple[int, int, int]] = []
    done = 0
    for query in queries:
        steps.append((query, prefix + done, 1))
        done += query
    return steps, notes


def _cache_prefix_apart_from_synthetic_design(resolved: Mapping[str, Any], source_path: str, diagnostics: Sequence[str]) -> int | None:
    """A counted cache that matches the launch prefix. Design shared_tokens is not that cache.

    Zero is a real count. This does not read a duration, and it does not pick a
    hardware SKU.
    """
    if any(str(item).startswith("prefix_cache_disagrees") for item in diagnostics):
        return None
    geometry = resolved.get("geometry") if isinstance(resolved.get("geometry"), Mapping) else {}
    prefix = geometry.get("prefix") if isinstance(geometry.get("prefix"), Mapping) else {}
    observed = prefix.get("observed_cached_tokens")
    if isinstance(observed, bool) or not isinstance(observed, int) or observed < 0:
        return None
    launch = _declared_launch(Path(source_path)) if source_path else {}
    if launch.get("conflict") or launch.get("prefix_len") != observed:
        return None
    note = _prefix_declaration_note(Path(source_path)) if source_path else ""
    if f"meta.env.PREFIX_LEN={observed}" not in note or f"run_meta.workload.prefix_len={observed}" not in note:
        return None
    return observed


def _archive_probe(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Join producer frames. Receipt replay is not the archive schedule."""
    from fleet_operator_archive import archive_probe
    return archive_probe(resolved)


def _resolve_any(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Primitive rows are handled earlier. Campaign, then archive, then a checked-in case file."""
    try:
        import fleet_campaign_case as campaign
    except ImportError:
        campaign = None
    if campaign is not None:
        resolved = campaign.resolve_campaign_case(cfg)
        if resolved is not None:
            return _campaign_probe(resolved)
    try:
        import fleet_archive_case as archive
    except ImportError:
        archive = None
    if archive is not None and archive.archive_case_domain(cfg):
        archive = _ensure_archive()
        resolved = archive.resolve_archive_case(cfg)
        if resolved is None:
            return _failure_probe("insufficient_evidence", ["archive_resolver_returned_none"], [], "archive_case")
        return _archive_probe(resolved)
    return _resolve_probe(cfg)


def _boundary_sample(frame: Mapping[str, Any], value: Any, capture_id: Any) -> dict[str, Any]:
    """One elapsed sample. The key uses the same fields E puts on a forward frame.

    ``capture_id`` is carried on the record and is not part of the key. E copies
    ``body.device_id`` when the forward object omits ``device_id``, including 0.
    The key is built after that copy. A global rank is not invented.
    """
    from hf_sample_scoring import sample_key

    ident: dict[str, Any] = {}
    for name in ("phase", "rank_id", "device_id", "forward_id"):
        raw = frame.get(name)
        if raw is None or raw == "":
            continue
        ident[name] = raw
    if "device_id" not in ident:
        body_device = frame.get("body_device_id")
        if body_device not in (None, ""):
            ident["device_id"] = body_device
    record = dict(ident)
    record["key"] = sample_key(**ident)
    if capture_id not in (None, ""):
        record["capture_id"] = capture_id
    record["value_ms"] = value
    record["boundary_ms"] = value
    record["boundary"] = "body_graph_span"
    record["boundary_basis"] = "elapsed"
    for name in ("sequences_per_replica", "tokens_per_sequence", "context_tokens"):
        if frame.get(name) is not None:
            record[name] = frame.get(name)
    return record


def _elapsed_boundary(probe: Mapping[str, Any], cached: Mapping[str, Any], forecasts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Elapsed body samples keyed by structural forward identity.

    A scalar body span is not a client request. Family elapsed is additive and
    is not a sample. Per-forward values are emitted only in receipt order.
    """
    by_population: dict[tuple[Any, Any], Any] = {}
    population_rows: list[dict[str, Any]] = []
    for item in forecasts:
        row = {
            "sequences_per_replica": item.get("sequences_per_replica"),
            "tokens_per_sequence": item.get("tokens_per_sequence"),
            "context_tokens": item.get("context_tokens"),
            "forward_count": item.get("forward_count"),
            "boundary_ms": item.get("predicted_step_ms") if item.get("status") == "modeled" else None,
            "boundary": "body_graph_span",
            "boundary_basis": "elapsed",
            "status": item.get("status"),
        }
        population_rows.append(row)
        if row["boundary_ms"] is not None:
            by_population[(row["sequences_per_replica"], row["tokens_per_sequence"])] = row["boundary_ms"]
    chunk_rows = [dict(item) for item in (cached.get("chunk_rows") or ())]
    if not population_rows:
        single = len(chunk_rows) <= 1
        by_population[(probe.get("sequences"), probe.get("tokens"))] = cached.get("predicted_step_ms") if single else None
        population_rows.append({
            "sequences_per_replica": probe.get("sequences"),
            "tokens_per_sequence": probe.get("tokens"),
            "context_tokens": probe.get("context"),
            "boundary_ms": cached.get("predicted_step_ms") if single else None,
            "boundary": "body_graph_span",
            "boundary_basis": "elapsed",
            "status": "modeled",
            "not_a_sample": not single,
        })
    frames = list(probe.get("frames") or [])
    capture_id = probe.get("capture_id")
    samples: list[dict[str, Any]] = []
    complete = False
    if frames and len(chunk_rows) == 1:
        for frame in frames:
            seq = frame.get("sequences_per_replica")
            tok = frame.get("tokens_per_sequence")
            value = by_population.get((seq, tok))
            if frame.get("phase") in (None, ""):
                frame = {**frame, "phase": probe.get("phase")}
            samples.append(_boundary_sample(frame, value, capture_id))
        complete = bool(samples) and all(item.get("boundary_ms") is not None for item in samples)
    elif frames and len(frames) == len(chunk_rows) and len(chunk_rows) > 1:
        aligned = True
        built: list[dict[str, Any]] = []
        for frame, chunk in zip(frames, chunk_rows):
            if frame.get("tokens_per_sequence") not in (None, chunk.get("tokens_per_sequence")):
                aligned = False
                break
            if frame.get("context_tokens") not in (None, chunk.get("context_tokens")):
                aligned = False
                break
            if frame.get("phase") in (None, ""):
                frame = {**frame, "phase": probe.get("phase")}
            built.append(_boundary_sample(frame, chunk.get("boundary_ms"), capture_id))
        if aligned:
            samples = built
            complete = bool(samples) and all(item.get("boundary_ms") is not None for item in samples)
    boundaries = {
        "body_graph_span": {
            "basis": "elapsed",
            "boundary_ms": cached.get("predicted_step_ms") if len(chunk_rows) == 1 else None,
            "chunks": chunk_rows,
            "populations": population_rows,
        },
        "family_elapsed_sum": {
            "basis": "additive",
            "ms": cached.get("predicted_operator_ms"),
            "not_a_sample": True,
        },
    }
    payload: dict[str, Any] = {"boundaries": boundaries}
    # One elapsed value per structural forward, in receipt order. A multi-chunk
    # series stays a list of samples. It is not collapsed to one scalar.
    if complete:
        payload.update({
            "prediction_boundary": "per_forward_window",
            "boundary_basis": "elapsed",
            "boundary_samples": samples,
            "boundary_samples_ms": [item["boundary_ms"] for item in samples],
        })
    elif frames:
        payload["boundary_sample_gap"] = "receipt_frames_not_aligned_to_chunk_spans"
    return payload


def _probe_with_sku(probe: Mapping[str, Any], sku: str) -> dict[str, Any]:
    """Same declared program with one catalogue SKU. The other candidate is not dropped."""
    one = dict(probe)
    case = copy.deepcopy(dict(probe["case"]))
    machine = dict(case.get("machine") or {})
    machine["sku"] = sku
    case["machine"] = machine
    one["case"] = case
    one["sku"] = sku
    one["hardware_alternatives"] = []
    one["structural_sha256"] = _structural_sha(case)
    return one


def _publish_hardware_alternatives(probe: Mapping[str, Any], cfg: Mapping[str, Any], alternatives: Sequence[str]) -> dict[str, Any]:
    """Price each declared SKU. The public step stays unset so a scorer cannot pick the easier one."""
    priced = []
    for sku in alternatives:
        one = _price_probe(_probe_with_sku(probe, sku), cfg)
        one["hardware_candidate"] = sku
        one["selected"] = False
        priced.append(one)
    return {
        "engine": "mindie_sim.prediction.body.body_forward",
        "measurement_features_read": False,
        "status": "conditional_hardware",
        "capture_id": probe.get("capture_id") or cfg.get("capture_id"),
        "phase": probe.get("phase") or cfg.get("phase"),
        "hardware_tier": cfg.get("hardware_tier"),
        "source_role": probe.get("source_role"),
        "source_sha256": probe.get("source_sha256") or "",
        "source_sha_basis": probe.get("source_sha_basis") or "",
        "predicted_step_ms": None,
        "predicted_operator_ms": None,
        "prediction_boundary": None,
        "hardware_candidates": priced,
        "hardware_selection": "not_selected",
        "diagnostics": list(probe.get("diagnostics") or []) + [
            "hardware_candidates_retained_without_outcome_selection",
        ],
        "coverage": {
            "modeled": False,
            "hardware_candidates_priced": len(priced),
            "hardware_selection": "not_selected",
            "absent_scopes_remain_in_denominator": True,
            "cores_unverified": list(_CORE_KEYS),
        },
    }


def _predict_body(cfg: Mapping[str, Any]) -> dict[str, Any]:
    probe = _resolve_any(cfg)
    if probe.get("source_role") == "archive_case":
        from fleet_operator_archive import publish_archive_prediction
        published = publish_archive_prediction(probe, cfg)
        if published is not None:
            return published
    alternatives = [str(item) for item in (probe.get("hardware_alternatives") or []) if item]
    if probe.get("ok") and len(alternatives) >= 2:
        return _publish_hardware_alternatives(probe, cfg, alternatives)
    return _price_probe(probe, cfg)


def _price_probe(probe: Mapping[str, Any], cfg: Mapping[str, Any]) -> dict[str, Any]:
    base = {
        "engine": "mindie_sim.prediction.body.body_forward",
        "measurement_features_read": False,
        "capture_id": probe.get("capture_id") or cfg.get("capture_id"),
        "phase": probe.get("phase") or cfg.get("phase"),
        "hardware_tier": cfg.get("hardware_tier"),
        "source_role": probe.get("source_role"),
        "source_sha256": probe.get("source_sha256") or "",
        "source_sha_basis": probe.get("source_sha_basis") or "",
        "source_image": probe.get("source_image") or "",
        "target_scope": probe.get("target_scope") or probe.get("predictable_scope"),
        "captured_frame_scope": probe.get("captured_frame_scope"),
        "service_scope": probe.get("service_scope"),
    }
    if not probe.get("ok"):
        failure = {
            **base, "status": probe.get("status") or "insufficient_evidence",
            "predicted_step_ms": None, "predicted_operator_ms": None,
            "predicted_by_scope_ms": {},
            "predicted_by_canonical_family_ms": {key: 0.0 for key in _CANONICAL_KEYS},
            "predicted_by_family_ms": {key: 0.0 for key in _BENCHMARK_KEYS},
            "predicted_by_unified_family_ms": {key: 0.0 for key in _UNIFIED_KEYS},
            "predicted_by_core_ms": _unverified_cores(),
            "geometry": {}, "diagnostics": list(probe.get("diagnostics") or []),
            "needed": probe.get("needed") or [],
            "coverage": {
                "modeled": False,
                "absent_scopes_remain_in_denominator": True,
                "cores_unverified": list(_CORE_KEYS),
            },
        }
        if probe.get("hardware_candidates"):
            failure["hardware_candidates"] = list(probe["hardware_candidates"])
            failure["hardware_selection"] = "not_selected"
        return failure
    steps = _chunk_plan(probe)
    if isinstance(steps, dict):
        return {**base, "status": steps["status"], "predicted_step_ms": None, "diagnostics": steps["diagnostics"]}
    key = _cache_key(probe, steps)
    cached = _GRAPH_CACHE.get(key)
    body_sequences = probe.get("body_sequences")
    if cached is None:
        span = 0.0
        elapsed = 0.0
        events = 0
        maps = _blank_maps()
        resources: list[dict[str, Any]] = []
        graph_geometry = None
        chunk_rows: list[dict[str, Any]] = []
        # Distinct windows stay separate rows. Chunk index keeps a later window
        # from being added into an earlier rank's count.
        additive_rows: list[dict[str, Any]] = []
        body_sequences = probe.get("body_sequences")
        for index, (tokens, context, sequences) in enumerate(steps):
            query_sequences = body_sequences if body_sequences is not None else sequences
            once = _graph_once(probe["case"], probe["phase"], tokens, context, query_sequences)
            if not once.get("ok"):
                return {
                    **base, "status": once.get("status") or "model_rejected",
                    "predicted_step_ms": None, "predicted_operator_ms": None,
                    "diagnostics": list(probe["diagnostics"]) + list(once.get("diagnostics") or []),
                    "geometry": {
                        "phase": probe["phase"], "tokens_per_sequence": probe["tokens"],
                        "sequences_per_replica": probe["sequences"], "context_tokens": probe["context"],
                        "sequences_by_replica": body_sequences,
                        "physical_rank": probe.get("physical_rank"),
                        "idle_physical_rank": probe.get("idle_physical_rank"),
                        "measurement_role": probe.get("measurement_role"),
                        "context_source": probe["context_source"], **probe["parallel"],
                    },
                    "coverage": {"modeled": False, "chunks_attempted": len(steps)},
                }
            span += float(once["body_forward_ms"])
            elapsed += float(once["family_elapsed_ms"])
            events += int(once["operator_events"])
            for kind in ("scope", "canonical", "benchmark", "unified"):
                source = once[{"scope": "by_scope_ms", "canonical": "by_canonical_ms", "benchmark": "by_benchmark_ms", "unified": "by_unified_ms"}[kind]]
                for name, value in source.items():
                    maps[kind][name] = maps[kind].get(name, 0.0) + float(value)
            resources.extend(once["resources"])
            for row in once.get("additive_rows") or ():
                if isinstance(row, Mapping):
                    copied = dict(row)
                    copied["chunk_index"] = index
                    additive_rows.append(copied)
            graph_geometry = once.get("engine_query")
            chunk_rows.append({
                "chunk_index": index,
                "phase": probe["phase"],
                "tokens_per_sequence": tokens,
                "context_tokens": context,
                "sequences_per_replica": sequences,
                "boundary_ms": round(float(once["body_forward_ms"]), 9),
                "family_elapsed_ms": round(float(once["family_elapsed_ms"]), 9),
                "boundary": "body_graph_span",
                "boundary_basis": "elapsed",
                "cohort": (once.get("engine_query") or {}).get("sequences_by_replica"),
            })
        absent = [name for name, value in maps["canonical"].items() if value == 0.0]
        cached = {
            "predicted_step_ms": round(span, 9),
            "predicted_operator_ms": round(elapsed, 9),
            "predicted_by_scope_ms": _round_map(maps["scope"]),
            "predicted_by_canonical_family_ms": _round_map(maps["canonical"]),
            "predicted_by_family_ms": _round_map(maps["benchmark"]),
            "predicted_by_unified_family_ms": _round_map(maps["unified"]),
            "resources": resources,
            "graph_geometry": graph_geometry,
            "operator_events": events,
            "absent_canonical_families": absent,
            "chunks": len(steps),
            "chunk_rows": chunk_rows,
            "engine_query": graph_geometry,
            "additive_rows": additive_rows,
        }
        core_pub = _core_publication(additive_rows, elapsed)
        identity = _identity_totals(additive_rows)
        cached["predicted_by_core_ms"] = core_pub["predicted_by_core_ms"]
        cached["cores_unnamed_by_engine"] = list(core_pub["cores_unnamed_by_engine"])
        cached["core_publication"] = core_pub
        cached["identity_totals"] = identity
        _GRAPH_CACHE[key] = cached
    absent = list(cached["absent_canonical_families"])
    forecasts = _population_forecasts(probe, cached)
    boundary = _elapsed_boundary(probe, cached, forecasts)
    diagnostics = list(probe["diagnostics"])
    graph_mode = str(probe.get("graph_mode") or "none")
    if graph_mode in {"", "none"}:
        diagnostics.append("missing_work:first_forward_cold_start_not_in_steady_body_graph")
        diagnostics.append("missing_work:no_independently_declared_launch_startup_term")
    single_chunk = cached["chunks"] == 1
    if not single_chunk:
        diagnostics.append("predicted_step_ms_withheld_because_chunks_are_separate_samples")
    additive_rows = [dict(row) for row in (cached.get("additive_rows") or ())]
    groups, group_status = _operator_groups_from_ledger(additive_rows)
    engines_bound = group_status == "source_bound_op_engine"
    core_view = cached.get("core_publication") if isinstance(cached.get("core_publication"), Mapping) else {}
    identity_view = cached.get("identity_totals") if isinstance(cached.get("identity_totals"), Mapping) else {}
    export_rank = probe.get("export_rank") if isinstance(probe.get("export_rank"), Mapping) else None
    engine = cached.get("engine_query") if isinstance(cached.get("engine_query"), Mapping) else {}
    selected = probe.get("physical_rank") if isinstance(probe.get("physical_rank"), Mapping) else None
    rank_scope = None
    if selected is not None and body_sequences is not None:
        selected_dp = int(selected.get("dp_index", -1))
        if 0 <= selected_dp < len(body_sequences):
            graph_by_replica = engine.get("graph_query_tokens_by_replica") or {}
            padded_by_replica = engine.get("padded_query_tokens_by_replica") or {}
            valid_by_replica = engine.get("valid_query_tokens_by_replica") or {}
            global_by_replica = engine.get("physical_global_ranks_by_replica") or {}
            at = lambda mapping: mapping.get(selected_dp, mapping.get(str(selected_dp)))
            rank_scope = {
                "rank_id": selected.get("rank_id"), "dp_index": selected_dp,
                "tp_index": selected.get("tp_index"), "role": probe.get("measurement_role"),
                "logical_sequences": body_sequences[selected_dp],
                "valid_query_tokens": at(valid_by_replica),
                "graph_query_tokens": at(graph_by_replica),
                "padded_query_tokens": at(padded_by_replica),
                "physical_global_scope": at(global_by_replica),
                "scope_basis": engine.get("physical_global_rank_basis"),
                "parent_step_ms": cached["predicted_step_ms"] if single_chunk else None,
                "parent_basis": ("full declared DP/TP cohort body graph; selected rank scope, "
                                 "not a duplicate per-TP aggregate"),
                "local_aggregate_basis": ("selected DP lane additive ledger; per-DP proxy for "
                                          "the selected rank, exact per-TP split not modeled"),
                "per_tp_resolution": ("not fabricated; symmetric TP assumption is not asserted "
                                      "when source transport detail is absent"),
            }
    all_additive_rows = additive_rows
    selected_rows = []
    local_scope = False
    local_elapsed = cached["predicted_operator_ms"]
    local_events = cached["operator_events"]
    local_absent = list(cached["absent_canonical_families"])
    local_scope_map = dict(cached["predicted_by_scope_ms"])
    local_canonical = dict(cached["predicted_by_canonical_family_ms"])
    local_benchmark = dict(cached["predicted_by_family_ms"])
    local_unified = dict(cached["predicted_by_unified_family_ms"])
    if rank_scope is not None:
        selected_dp = int(rank_scope["dp_index"])
        selected_rows = [row for row in all_additive_rows
                         if int(row.get("rank_id") or 0) == selected_dp]
        if selected_rows:
            local_scope = True
            additive_rows = selected_rows
            local_bucket = _blank_maps()
            local_elapsed = 0.0
            for row in selected_rows:
                elapsed = row.get("elapsed_ms")
                if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
                    continue
                value = float(elapsed)
                local_elapsed += value
                _add_scope(local_bucket, str(row.get("family_scope") or "other"), value)
            local_elapsed = round(local_elapsed, 9)
            local_events = len(selected_rows)
            local_absent = [name for name, value in local_bucket["canonical"].items() if value == 0.0]
            local_scope_map = _round_map(local_bucket["scope"])
            local_canonical = _round_map(local_bucket["canonical"])
            local_benchmark = _round_map(local_bucket["benchmark"])
            local_unified = _round_map(local_bucket["unified"])
            groups, group_status = _operator_groups_from_ledger(selected_rows)
            engines_bound = group_status == "source_bound_op_engine"
            core_view = _core_publication(selected_rows, local_elapsed)
            identity_view = _identity_totals(selected_rows)
    if rank_scope is not None:
        tp_width = int((probe.get("parallel") or {}).get("tp") or 1)
        selected_rank = rank_scope.get("rank_id")
        for row in additive_rows:
            dp_index = int(row.get("rank_id") or 0)
            row["logical_dp_replica"] = dp_index
            row["physical_global_scope"] = list(range(dp_index * tp_width, (dp_index + 1) * tp_width))
            row["physical_global_rank_basis"] = "dp_replica * tp + tp_rank"
            row["contains_selected_physical_rank"] = dp_index == rank_scope.get("dp_index")
            row["selected_physical_global_rank"] = selected_rank if row["contains_selected_physical_rank"] else None
            row["rank_attribution"] = ("per-DP-shard aggregate; selected measured rank is resolved "
                                       "in rank_scope, not duplicated per TP lane")
    if not list(probe.get("frames") or []):
        diagnostics.append("body_graph_span_is_not_an_op_statistic_aggregate")
    return {
        **base, "status": "modeled",
        "predicted_step_ms": cached["predicted_step_ms"] if single_chunk else None,
        "predicted_operator_ms": local_elapsed if local_scope else cached["predicted_operator_ms"],
        "predicted_by_scope_ms": (local_scope_map if local_scope else dict(cached["predicted_by_scope_ms"])),
        "predicted_by_canonical_family_ms": (local_canonical if local_scope else dict(cached["predicted_by_canonical_family_ms"])),
        "predicted_by_family_ms": (local_benchmark if local_scope else dict(cached["predicted_by_family_ms"])),
        "predicted_by_unified_family_ms": (local_unified if local_scope else dict(cached["predicted_by_unified_family_ms"])),
        "predicted_by_core_ms": dict(core_view.get("predicted_by_core_ms") or cached["predicted_by_core_ms"]),
        "resources": list(cached["resources"]),
        "resources_scope": ("whole_declared_DP_cohort_capacity_not_selected_rank"
                            if local_scope else "whole_cohort"),
        **({"whole_cohort": {
            "basis": "whole_declared_DP_cohort_parent",
            "additive_rows": len(all_additive_rows),
            "operator_events": cached["operator_events"],
            "predicted_step_ms": cached["predicted_step_ms"] if single_chunk else None,
            "predicted_operator_ms": cached["predicted_operator_ms"],
            "predicted_by_scope_ms": dict(cached["predicted_by_scope_ms"]),
            "predicted_by_canonical_family_ms": dict(cached["predicted_by_canonical_family_ms"]),
            "predicted_by_family_ms": dict(cached["predicted_by_family_ms"]),
            "predicted_by_unified_family_ms": dict(cached["predicted_by_unified_family_ms"]),
            "predicted_by_core_ms": dict(cached["predicted_by_core_ms"]),
            "core_forecast": cached["core_publication"].get("core_forecast") if isinstance(cached.get("core_publication"), Mapping) else None,
            "identity_totals": dict(cached.get("identity_totals") or {}),
            "absent_canonical_families": list(cached["absent_canonical_families"]),
        }} if local_scope else {}),
        "calibration": dict(probe.get("calibration") or {}),
        "deployment_sha256": probe.get("deployment_sha256") or "",
        "structural_sha256": probe.get("structural_sha256") or "",
        "geometry": {
            "phase": probe["phase"],
            "tokens_per_sequence": probe["tokens"],
            "sequences_per_replica": probe["sequences"],
            **({"sequences_by_replica": probe["body_sequences"],
                "physical_rank": probe.get("physical_rank"),
                "active_physical_rank": probe.get("active_physical_rank"),
                "idle_physical_rank": probe.get("idle_physical_rank"),
                "measurement_role": probe.get("measurement_role"),
                "rank_scope": rank_scope,
                "local_operator_scope": ("selected_dp_lane_additive_ledger"
                                         if local_scope else "whole_cohort"),
                "local_operator_ms": local_elapsed if local_scope else cached["predicted_operator_ms"],
                "whole_cohort_step_ms": cached["predicted_step_ms"] if single_chunk else None}
               if probe.get("body_sequences") is not None else {}),
            "query_rows": probe["sequences"] * probe["tokens"],
            "context_tokens": probe["context"],
            "context_source": probe["context_source"],
            "case_path": probe["case_path"],
            "sku": probe["sku"],
            "receipt_population": probe["population"],
            "engine_query": cached.get("engine_query"),
            "cohort_sequences_by_replica": (cached.get("engine_query") or {}).get("sequences_by_replica"),
            "batch_basis": (probe.get("population") or {}).get("batch_basis") if isinstance(probe.get("population"), Mapping) else None,
            "graph_mode": probe.get("graph_mode"),
            "mtp_proposal_tokens": probe.get("mtp_proposal_tokens") or 0,
            "sequences_observed": probe.get("sequences_observed"),
            "sequences_upper_bound": probe.get("sequences_upper_bound"),
            "tokens_basis": probe.get("tokens_basis"),
            "actual_q_observed": probe.get("actual_q_observed"),
            "rank_batch_observed": probe.get("rank_batch_observed"),
            **probe["parallel"],
        },
        "export_rank": export_rank,
        "physical_rank": probe.get("physical_rank"),
        "active_physical_rank": probe.get("active_physical_rank"),
        "idle_physical_rank": probe.get("idle_physical_rank"),
        "measurement_role": probe.get("measurement_role"),
        "body_sequences": probe.get("body_sequences"),
        "rank_scope": rank_scope,
        "additive_rank_phase": {
            "basis": ("selected_dp_lane_additive" if local_scope else "additive"),
            "not_a_step": True,
            "not_an_op_statistic_substitute": True,
            "op_identity": "sim_operator_id",
            "engine_binding": "source_bound" if engines_bound else "unverified",
            "rank_scope": rank_scope,
            "logical_to_physical": "dp_replica * tp + tp_rank",
            "selected_physical_global_rank": (rank_scope or {}).get("rank_id"),
            "rows": additive_rows,
            "selected_dp_rows": len(additive_rows) if local_scope else None,
            "whole_cohort_rows": len(all_additive_rows),
            "per_tp_resolution": ("per-DP proxy; exact per-TP split not modeled"
                                  if local_scope else "not_applicable_legacy_scope"),
        },
        **({"predicted_operator_groups": groups} if groups else {}),
        "diagnostics": diagnostics,
        **boundary,
        "coverage": {
            "modeled": True,
            "chunks": cached["chunks"],
            "operator_events": local_events if local_scope else cached["operator_events"],
            "graph_span_ms": cached["predicted_step_ms"] if single_chunk else None,
            "chunk_span_sum_ms": cached["predicted_step_ms"],
            "chunk_span_sum_is_not_a_sample": not single_chunk,
            "family_elapsed_sum_ms": local_elapsed if local_scope else cached["predicted_operator_ms"],
            "span_equals_family_sum": (cached["predicted_step_ms"] == local_elapsed
                                       if local_scope else
                                       cached["predicted_step_ms"] == cached["predicted_operator_ms"]),
            "family_elapsed_sum_delta_vs_parent_ms": (
                round(local_elapsed - cached["predicted_step_ms"], 9) if local_scope else None),
            "span_equals_family_sum_within_1e-6": (
                abs(local_elapsed - cached["predicted_step_ms"]) <= 1e-6
                if local_scope else
                abs(cached["predicted_step_ms"] - cached["predicted_operator_ms"]) <= 1e-6),
            "local_operator_scope": ("selected_dp_lane_additive_ledger"
                                     if local_scope else "whole_cohort"),
            "selected_dp_rows": len(additive_rows) if local_scope else None,
            "whole_cohort_rows": len(all_additive_rows),
            "whole_cohort_operator_events": cached["operator_events"],
            "whole_cohort_family_elapsed_sum_ms": cached["predicted_operator_ms"],
            "absent_canonical_families": local_absent if local_scope else absent,
            "absent_scopes_remain_in_denominator": True,
            "context_observed_in_receipt": probe["context_source"] == "extraction_receipt",
            "core_time_basis": _core_time_basis(str(core_view.get("core_forecast") or "unresolved")),
            "core_time_is_not_a_partition_of_the_span": core_view.get("core_forecast") != "source_bound",
            "core_forecast": core_view.get("core_forecast"),
            "core_map_is_complete_forecast": bool(core_view.get("core_map_is_complete_forecast")),
            "bound_core_elapsed_ms": core_view.get("bound_core_elapsed_ms"),
            "unresolved_core_elapsed_ms": core_view.get("unresolved_core_elapsed_ms"),
            "recovered_native_kind_ms": dict(identity_view.get("recovered_native_kind_ms") or {}),
            "unresolved_family_identity_ms": dict(identity_view.get("unresolved_family_identity_ms") or {}),
            "partial_kind_elapsed_ms": identity_view.get("partial_kind_elapsed_ms"),
            "cores_unnamed_by_engine": list(core_view.get("cores_unnamed_by_engine") or _CORE_KEYS),
            "cores_unverified": list(core_view.get("cores_unnamed_by_engine") or _CORE_KEYS),
            "resource_busy_is_not_accelerator_core_elapsed": True,
            "receipt_populations": forecasts,
            "unpriced_scopes": ["first_forward_cold_start"] if graph_mode in {"", "none"} else [],
            "startup_term": None,
            "startup_term_source": "not_declared",
            "operator_groups": group_status,
            "additive_rank_phase_rows": len(additive_rows),
            "body_span_is_not_op_statistic": not bool(probe.get("frames")),
        },
    }


def _population_forecasts(probe: Mapping[str, Any], primary: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Predict every decode receipt population. The row geometry stays the public step."""
    populations = list(probe.get("populations") or [])
    if probe.get("phase") != "decode" or len(populations) <= 1:
        return []
    if len(populations) > 8:
        return [{
            "status": "not_expanded",
            "predicted_step_ms": None,
            "diagnostics": [f"receipt_population_count_{len(populations)}_exceeds_8"],
        }]
    rows: list[dict[str, Any]] = []
    for item in populations:
        sequences = item.get("sequences_per_replica")
        tokens = item.get("tokens_per_sequence")
        record: dict[str, Any] = {
            "sequences_per_replica": sequences,
            "tokens_per_sequence": tokens,
            "forward_count": item.get("forward_count"),
            "context_tokens": probe["context"],
            "context_source": probe["context_source"],
            "selected_row_geometry": sequences == probe["sequences"] and tokens == probe["tokens"],
        }
        if record["selected_row_geometry"]:
            record["status"] = "modeled"
            record["predicted_step_ms"] = primary["predicted_step_ms"]
            record["boundary_ms"] = primary["predicted_step_ms"]
            record["boundary"] = "body_graph_span"
            record["boundary_basis"] = "elapsed"
            record["engine_query"] = primary.get("engine_query")
            rows.append(record)
            continue
        if not isinstance(sequences, int) or not isinstance(tokens, int) or sequences < 1 or tokens < 1:
            record["status"] = "insufficient_evidence"
            record["predicted_step_ms"] = None
            record["diagnostics"] = ["population_geometry_incomplete"]
            rows.append(record)
            continue
        sub = dict(probe)
        sub["sequences"] = sequences
        sub["tokens"] = tokens
        steps = _chunk_plan(sub)
        if isinstance(steps, dict):
            record["status"] = steps["status"]
            record["predicted_step_ms"] = None
            record["diagnostics"] = list(steps.get("diagnostics") or [])
            rows.append(record)
            continue
        key = _cache_key(sub, steps)
        cached = _GRAPH_CACHE.get(key) or _POPULATION_STEP_CACHE.get(key)
        if cached is None:
            span = 0.0
            query = None
            failed = None
            for step_tokens, step_context, step_sequences in steps:
                once = _graph_once(probe["case"], probe["phase"], step_tokens, step_context, step_sequences)
                if not once.get("ok"):
                    failed = once
                    break
                span += float(once["body_forward_ms"])
                query = once.get("engine_query")
            if failed is not None:
                record["status"] = failed.get("status") or "model_rejected"
                record["predicted_step_ms"] = None
                record["diagnostics"] = list(failed.get("diagnostics") or [])
                rows.append(record)
                continue
            cached = {"predicted_step_ms": round(span, 9), "engine_query": query}
            _POPULATION_STEP_CACHE[key] = cached
        record["status"] = "modeled"
        record["predicted_step_ms"] = cached["predicted_step_ms"]
        record["boundary_ms"] = cached["predicted_step_ms"]
        record["boundary"] = "body_graph_span"
        record["boundary_basis"] = "elapsed"
        record["engine_query"] = cached.get("engine_query")
        rows.append(record)
    return rows


def _scope_maps_from_kernels(kernels: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, float]]:
    """Route I's priced kernel durations through the published scope names."""
    maps = _blank_maps()
    for kernel in kernels:
        if not isinstance(kernel, Mapping):
            continue
        elapsed = kernel.get("duration_ms")
        if not isinstance(elapsed, (int, float)) or not math.isfinite(float(elapsed)):
            continue
        name = str(kernel.get("name") or kernel.get("native_kind") or kernel.get("role") or "")
        _add_elapsed(maps, name, float(elapsed))
    return maps


def _adopt_primitive_result(result: Mapping[str, Any]) -> dict[str, Any]:
    """Publish I's primitive result, including comparison scopes. Do not replace it with a catalog body."""
    status = str(result.get("status") or "")
    program = result.get("program") if isinstance(result.get("program"), Mapping) else {}
    kernels = [item for item in (program.get("kernels") or ()) if isinstance(item, Mapping)]
    unsupported = result.get("unsupported") if isinstance(result.get("unsupported"), Mapping) else {}
    scopes = result.get("comparison_scopes") if isinstance(result.get("comparison_scopes"), Mapping) else None
    priced = status in {"predicted", "modeled"} and isinstance(result.get("predicted_ms"), (int, float))
    if not priced:
        missing = list(unsupported.get("missing_facts") or [])
        boundary_name = str(result.get("prediction_boundary") or "native_calls")
        return {
            "engine": "fleet_primitive_workloads.predict_primitive_workload",
            "status": status or "insufficient_evidence",
            "predicted_step_ms": None,
            "predicted_operator_ms": None,
            "predicted_by_scope_ms": {},
            "predicted_by_canonical_family_ms": {key: 0.0 for key in _CANONICAL_KEYS},
            "predicted_by_family_ms": {key: 0.0 for key in _BENCHMARK_KEYS},
            "predicted_by_unified_family_ms": {key: 0.0 for key in _UNIFIED_KEYS},
            "predicted_by_core_ms": _unverified_cores(),
            "comparison_scopes": scopes,
            "prediction_boundary": boundary_name,
            "boundary_samples": [dict(item) for item in (result.get("boundary_samples") or ()) if isinstance(item, Mapping)],
            "diagnostics": [str(unsupported.get("reason") or status or "primitive_unsupported")],
            "needed": missing,
            "measurement_features_read": False,
            "source_sha256": result.get("source_sha256") or "",
            "capture_id": result.get("capture_id"),
            "coverage": {
                "modeled": False,
                "boundary": boundary_name,
                "absent_scopes_remain_in_denominator": True,
                "cores_unverified": list(_CORE_KEYS),
            },
        }
    maps = _scope_maps_from_kernels(kernels)
    operator_ms = round(sum(maps["scope"].values()), 9) if maps["scope"] else result.get("predicted_ms")
    step_ms = round(float(result["predicted_ms"]), 9)
    resources = []
    for row in result.get("resources") or ():
        if not isinstance(row, Mapping):
            continue
        busy = row.get("busy_ms")
        busy_ms = float(busy) if isinstance(busy, (int, float)) and math.isfinite(float(busy)) else None
        resources.append({
            "resource": row.get("resource"),
            "busy_ms": busy_ms,
            "unit": row.get("unit"),
        })
    published: list[dict[str, Any]] = []
    for item in result.get("boundary_samples") or ():
        if not isinstance(item, Mapping) or not item.get("key"):
            continue
        row = dict(item)
        if row.get("value_ms") is None and isinstance(row.get("boundary_ms"), (int, float)):
            row["value_ms"] = row["boundary_ms"]
        row.setdefault("boundary", "native_call_span")
        row.setdefault("boundary_basis", str(result.get("boundary_basis") or "elapsed_native_call_span_ms"))
        published.append(row)
    boundary_name = str(result.get("prediction_boundary") or "native_calls")
    per_call_ms = published[0].get("boundary_ms") if published else step_ms
    return {
        "engine": "fleet_primitive_workloads.predict_primitive_workload",
        "status": status,
        "predicted_step_ms": step_ms,
        "predicted_operator_ms": None if operator_ms is None else round(float(operator_ms), 9),
        "predicted_total_ms": result.get("predicted_total_ms"),
        "predicted_by_scope_ms": _round_map(maps["scope"]),
        "predicted_by_canonical_family_ms": _round_map(maps["canonical"]),
        "predicted_by_family_ms": _round_map(maps["benchmark"]),
        "predicted_by_unified_family_ms": _round_map(maps["unified"]),
        "predicted_by_core_ms": _unverified_cores(),
        "resources": resources,
        "comparison_scopes": scopes,
        "prediction_boundary": boundary_name,
        "boundary_basis": str(result.get("boundary_basis") or "elapsed_native_call_span_ms"),
        "boundary_ms": None if per_call_ms is None else round(float(per_call_ms), 9),
        "boundary_samples": published,
        "diagnostics": [result.get("diagnostics")] if result.get("diagnostics") is not None else [],
        "measurement_features_read": False,
        "kind": result.get("kind"),
        "program": program,
        "source_sha256": result.get("source_sha256") or "",
        "capture_id": result.get("capture_id"),
        "phase": result.get("phase"),
        "source_role": "standalone_native_primitive",
        "coverage": {
            "modeled": True,
            "boundary": boundary_name,
            "absent_scopes_remain_in_denominator": True,
            "absent_canonical_families": [name for name, value in maps["canonical"].items() if value == 0.0],
            "cores_unnamed_by_engine": list(_CORE_KEYS),
            "cores_unverified": list(_CORE_KEYS),
            "core_time_basis": "unverified_until_per_kernel_source_bound_interval",
            "resource_busy_is_not_accelerator_core_elapsed": True,
            "repeats": result.get("repeats"),
        },
    }


def _primitive_prediction(cfg: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        import fleet_primitive_workloads as primitive
    except ImportError:
        return None
    predict = getattr(primitive, "predict_primitive_workload", None)
    if not callable(predict):
        return None
    predicate = getattr(primitive, "is_primitive_workload", None)
    if callable(predicate):
        if not predicate(cfg):
            return None
    elif not callable(getattr(primitive, "primitive_workload_descriptor", None)):
        return None
    result = predict(cfg)
    if result is None:
        return None
    if not isinstance(result, dict):
        return None
    if result.get("status") in {"not_primitive", "not_a_primitive"}:
        return None
    return _adopt_primitive_result(result)


def predict_capture_operators_and_step(config: Mapping[str, Any]) -> dict[str, Any]:
    """Predict step span and family elapsed for one capture.

    Reads only ``_ALLOWED_CFG_KEYS``. Does not iterate ``config``.
    """
    cfg = {key: config.get(key) for key in _ALLOWED_CFG_KEYS} if isinstance(config, Mapping) else {}
    routed = _primitive_prediction(cfg)
    if routed is not None:
        return routed
    return _predict_body(cfg)


def _rel(predicted: float | None, observed: float | None) -> float | None:
    if predicted is None or observed is None:
        return None
    if observed == 0.0:
        return 0.0 if predicted == 0.0 else None
    return abs(predicted - observed) / abs(observed)


def _family_block(predicted: Mapping[str, Any], observed: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Every predicted key stays in the block. Missing observations and unverified cores stay missing."""
    block: dict[str, dict[str, Any]] = {}
    for key, pred in predicted.items():
        obs = observed.get(key) if isinstance(observed, Mapping) else None
        obs_value = float(obs) if isinstance(obs, (int, float)) and math.isfinite(float(obs)) else None
        pred_value = float(pred) if isinstance(pred, (int, float)) and math.isfinite(float(pred)) else None
        if pred_value is None:
            block[key] = {
                "predicted_ms": None,
                "observed_ms": None if obs_value is None else round(obs_value, 9),
                "relative_error": None,
                "status": "unverified",
            }
            continue
        error = _rel(pred_value, obs_value)
        block[key] = {
            "predicted_ms": round(pred_value, 9),
            "observed_ms": None if obs_value is None else round(obs_value, 9),
            "relative_error": None if error is None else round(error, 8),
            "status": "compared" if obs_value is not None else "missing_observation",
        }
    return block


def enrich_fleet_capture_with_operator_and_step_modeling(row: Mapping[str, Any]) -> dict[str, Any]:
    """Attach a body-graph prediction and the delegated observation."""
    out = dict(row)
    prediction = predict_capture_operators_and_step(row)
    coverage = prediction.get("coverage") if isinstance(prediction.get("coverage"), Mapping) else {}
    if coverage.get("boundary") == "per_standalone_native_call":
        # A primitive call is not a serving step. Do not score it against the row's
        # fabricated forward population.
        out.update({
            "status": prediction.get("status"),
            "observed_ms": None,
            "predicted_ms": prediction.get("predicted_step_ms"),
            "relative_error": None,
            "passed_10pct": False,
            "passed_15pct": False,
            "target_timing_used_to_fit": False,
            "prediction": prediction,
            "operator_modeling": {
                "status": "primitive_call_not_serving_step",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": None,
                "predicted_operator_ms": prediction.get("predicted_operator_ms"),
                "operator_relative_error": None,
                "operator_passed_10pct": False,
                "canonical_families": _family_block(
                    prediction.get("predicted_by_canonical_family_ms") or {}, {},
                ),
            },
        })
        return out
    obs = extract_capture_observations(row)
    source = dict(out.get("source_calibration") or {})
    fitted = bool(source.get("target_timing_used_to_fit")) or "in_sample" in str(source.get("evaluation_relation") or "").lower()
    if fitted:
        source["target_timing_used_to_fit"] = True
        source["evaluation_relation"] = source.get("evaluation_relation") or "in_sample"
    else:
        source["target_timing_used_to_fit"] = False
        source.setdefault("evaluation_relation", "body_graph")
    observed = obs.get("observed_ms")
    observed_value = float(observed) if isinstance(observed, (int, float)) and math.isfinite(float(observed)) else None
    predicted = prediction.get("predicted_step_ms")
    predicted_value = float(predicted) if isinstance(predicted, (int, float)) else None
    step_error = _rel(predicted_value, observed_value)
    families = _family_block(
        prediction.get("predicted_by_canonical_family_ms") or {},
        obs.get("observed_by_canonical_family_ms") or {},
    )
    benchmark = _family_block(prediction.get("predicted_by_family_ms") or {}, obs.get("observed_by_family_ms") or {})
    cores = _family_block(prediction.get("predicted_by_core_ms") or {}, obs.get("observed_by_core_ms") or {})
    family_compared = [item for item in families.values() if item["status"] == "compared" and (item["observed_ms"] or 0.0) > 0.0]
    family_missing = [key for key, item in families.items() if item["status"] != "compared"]
    family_ok = bool(family_compared) and all((item["relative_error"] or 1.0) <= 0.10 for item in family_compared) and not family_missing
    step_ok = step_error is not None and step_error <= 0.10 and prediction.get("status") == "modeled"
    # A pass requires the step and every canonical family. Absent observations
    # stay in the denominator and cannot be skipped into a pass.
    passed = bool(step_ok and family_ok and obs.get("status") == "compared")
    operator_status = "compared" if family_compared and not family_missing else (
        "missing_artifact" if obs.get("status") == "missing_artifact" else "scope_unverified"
    )
    out.update({
        "status": "compared" if observed_value is not None and predicted_value is not None else (
            prediction.get("status") if predicted_value is None else obs.get("status") or "missing_artifact"
        ),
        "observed_ms": observed_value,
        "predicted_ms": predicted_value,
        "relative_error": None if step_error is None else round(step_error, 8),
        "passed_10pct": passed,
        "passed_15pct": bool(step_ok and family_ok and step_error is not None and step_error <= 0.15),
        "target_timing_used_to_fit": fitted,
        "source_calibration": source,
        "geometry": prediction.get("geometry") or out.get("geometry"),
        "prediction": prediction,
        "operator_modeling": {
            "status": operator_status,
            "target_timing_used_to_fit": False,
            "observed_operator_ms": obs.get("observed_operator_ms"),
            "predicted_operator_ms": prediction.get("predicted_operator_ms"),
            "operator_relative_error": None,
            "operator_passed_10pct": family_ok,
            "by_accelerator_core": cores,
            "families": benchmark,
            "canonical_families": families,
            "unified_families": _family_block(
                prediction.get("predicted_by_unified_family_ms") or {},
                obs.get("observed_by_unified_family_ms") or {},
            ),
            "absent_canonical_families": (prediction.get("coverage") or {}).get("absent_canonical_families"),
        },
    })
    return out


def enrich_all_fleet_captures(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Enrich each fleet row. Duplicate capture ids receive a ``#n`` suffix."""
    from collections import Counter

    seen: Counter[str] = Counter()
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        capture_id = str(item.get("capture_id") or "")
        seen[capture_id] += 1
        if seen[capture_id] > 1:
            item["capture_id"] = f"{capture_id}#{seen[capture_id]}"
        enriched.append(enrich_fleet_capture_with_operator_and_step_modeling(item))
    return enriched


def _infer_geometry(row: Mapping[str, Any]) -> dict[str, Any]:
    """Return declared geometry fields. Capture-id text is not a geometry source."""
    return _declared_geometry(row.get("geometry") if isinstance(row, Mapping) else None)
