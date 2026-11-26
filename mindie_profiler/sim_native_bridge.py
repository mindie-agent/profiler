"""Cohesive native operator observation, request normalization, and T12 prediction bridge.

[Role]
  Consolidate ``kernel_details.csv`` source selection, timing-free native
  prediction request projection, ordered-slot / QBMM invocation lowering, and
  canonical ``mindie_sim.simulate_native_call`` execution into one cohesive
  module (replacing the legacy ``sim_bridge_{case,native_obs,predict}`` shards).
[Invariants]
  * Pure CPU at import time (``DEV-ZERO-CTX``); imports ``mindie_sim`` lazily
    only inside execution helpers.
  * Observed durations never enter timing-free prediction requests or
    invocations; any timing key leak fails closed.
  * Preserves deterministic schemas, explicit ``Missing`` / ``None`` semantics,
    source provenance, and condition conflict reporting with zero hidden state.
  * Every ``except OSError:`` / broad exception boundary propagates
    ``TimeoutError``.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms and bounded read-only source discovery; callers own
  any persisted files.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from .bench.profiles import profile_section
from .events import ProfilerError, ProfilerUsageError
from .native_abi_model import build_plan
from .sim_bridge_observed import NATIVE_REQUEST_SCHEMA, _canonical_json, _native_timing_path

_MEASURED_SUPPLY_CFG = profile_section("measured_supply")
_QBMM_INPUT_SLOTS = int(_MEASURED_SUPPLY_CFG["matrix_input_slots"])
_FRACTAL_NZ_RANK = _QBMM_INPUT_SLOTS
_MXFP8_GROUP_SIZE = int(_MEASURED_SUPPLY_CFG["nz_tile_mx"])

_NATIVE_EXECUTION_CORES = {
    "AI_CORE",
    "AI_VECTOR_CORE",
    "MIX_AIC",
    "MIX_AIV",
    "AI_CPU",
    "AICPU",
    "COMMUNICATION",
    "HCCL",
}

_T12_CONDITION_KEYS = {
    "variant",
    "owner",
    "members",
    "layer",
    "sequence_rows",
    "sequence_ranks",
    "phase",
}

_DTYPE_STORAGE_ALIASES = {"uint8": "fp8_e8m0"}


# ---------------------------------------------------------------------------
# Capture selection & timing-free request projection
# ---------------------------------------------------------------------------

def _native_capture_selection(
    value: str | Path, *, rank: str | None
) -> tuple[Path, dict[str, Any]]:
    """Select one ``kernel_details`` CSV without hiding sibling-rank facts.

    Directory inputs consume CLOCK's inventory (the same bounded source/capture
    relation as T03), retain every rank candidate and read error, then require
    one unambiguous ``kernel_details`` source.  A sibling rank with only
    ``op_summary``/``task_time`` is a native-source gap, not silently omitted.
    """
    path = Path(value).expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() not in {".csv", ".gz"}:
            raise ProfilerUsageError(
                f"native observations require a kernel_details CSV; got {path.name}"
            )
        return path, {
            "kind": "explicit_file",
            "path": str(path),
            "selected_path": str(path),
            "rank_count": 1,
            "selected_rank": None,
            "ranks": [],
        }
    if not path.is_dir():
        raise ProfilerUsageError(f"native observation input does not exist: {path}")
    from .inventory import inventory_profile

    try:
        inventory = inventory_profile(path)
    except ProfilerError as exc:
        raise ProfilerUsageError(
            f"native observations: inventory discovery failed for {path}: {exc}"
        ) from exc
    ranks = list(inventory.get("ranks") or ())
    facts = []
    for item in ranks:
        files = [
            file
            for file in item.get("files") or ()
            if str(file.get("basename") or "").lower()
            in {"kernel_details.csv", "kernel_details.csv.gz"}
        ]
        facts.append({
            "rank_id": item.get("rank_id"),
            "rank_index": item.get("rank_index"),
            "rank_dir": item.get("rank_dir"),
            "kernel_details": [str(file.get("path")) for file in files],
            "csv_candidates": list(item.get("csv_candidates") or ()),
            "selected_csv": list(item.get("selected_csv") or ()),
            "db_candidates": list(item.get("db_candidates") or ()),
            "trace_candidates": list(item.get("trace_candidates") or ()),
            "limitations": list(item.get("limitations") or ()),
            "files": [
                dict(file) for file in (item.get("files") or ()) if isinstance(file, Mapping)
            ],
        })
    discovery = {
        "kind": "clock_inventory",
        "root": str(path),
        "rank_count": len(ranks),
        "ranks": facts,
        "source_identity": inventory.get("capture_ids"),
        "selected_rank": rank,
        "selected_path": None,
        "sibling_rank_gaps": [
            {
                "rank_id": item.get("rank_id"),
                "reason": "no_kernel_details_csv",
                "rank_dir": item.get("rank_dir"),
                "csv_candidates": item.get("csv_candidates"),
                "limitations": item.get("limitations"),
            }
            for item in facts
            if not item.get("kernel_details")
        ],
    }
    wanted = str(rank) if rank is not None else None

    def matches(item: Mapping[str, Any]) -> bool:
        return (
            str(item.get("rank_id")) == wanted
            or str(item.get("rank_index")) == wanted
            or str(item.get("rank_id") or "").rsplit("_", 1)[-1] == wanted
            or Path(str(item.get("rank_dir") or "")).name == f"rank_{wanted}"
        )

    chosen = [item for item in facts if matches(item)] if wanted is not None else facts
    if wanted is not None and not chosen:
        raise ProfilerUsageError(
            "native observations: requested rank not found in inventory; available="
            + ",".join(str(item.get("rank_id")) for item in facts)
        )
    available = [item for item in chosen if item["kernel_details"]]
    missing = [item for item in chosen if not item["kernel_details"]]
    if not available:
        raise ProfilerUsageError(
            "native observations: no kernel_details.csv for requested rank scope; available="
            + ",".join(str(item.get("rank_id")) for item in facts)
        )
    if missing:
        raise ProfilerUsageError(
            "native observations: sibling rank has no kernel_details source; missing="
            + ",".join(str(item.get("rank_id")) for item in missing)
            + "; candidates="
            + json.dumps(discovery["ranks"], sort_keys=True)
        )
    if len(available) > 1:
        available_ids = [str(item["rank_id"]) for item in available]
        raise ProfilerUsageError(
            "native observations: multiple ranks have kernel_details.csv; "
            f"pass --rank {available_ids[0]}; available={','.join(available_ids)}"
        )
    candidates = available[0]["kernel_details"]
    if len(candidates) != 1:
        raise ProfilerUsageError(
            "native observations: rank has multiple kernel_details.csv candidates; "
            "pass the explicit file: " + ", ".join(candidates)
        )
    discovery["selected_rank"] = available[0]["rank_id"]
    discovery["selected_path"] = candidates[0]
    return Path(candidates[0]), discovery


def _native_operator_identity(row: Any, event: Any) -> tuple[str | None, str | None]:
    """Separate a captured Type from an execution-core fallback.

    The CSV adapter uses ``Type or Accelerator Core``.  Treating that fallback
    as a native operator would invent an ABI identity from the execution engine.
    """
    kind = str(getattr(row, "kind", "") or "").strip()
    core = str(getattr(row, "core", "") or getattr(event, "core", "") or "").strip()
    if not kind:
        return None, "native_type_missing"
    if kind.upper() in _NATIVE_EXECUTION_CORES:
        return None, "native_type_missing_used_execution_core"
    if core and kind.upper() == core.upper() and core.upper() in _NATIVE_EXECUTION_CORES:
        return None, "native_type_missing_used_execution_core"
    return kind, None


def _native_conditions(
    conditions: Mapping[str, Any] | None,
    *,
    hardware: str | None,
    phase: str | None,
    model: str | None,
    quant: str | None,
    deployment_image_id: str | None,
    execution: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, list[str]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Merge declared conditions and explicit arguments without losing sources."""
    result: dict[str, Any] = {}
    sources: dict[str, list[str]] = {}
    conflicts: list[dict[str, Any]] = []
    if conditions is not None:
        if not isinstance(conditions, Mapping):
            raise ProfilerUsageError("native conditions must be a mapping")
        for key, value in conditions.items():
            result[str(key)] = value
            sources[str(key)] = ["export.conditions"]
    explicit = {
        "hardware": hardware,
        "phase": phase,
        "model": model,
        "quant": quant,
        "deployment_image_id": deployment_image_id,
    }
    for key, value in explicit.items():
        if value is None or not str(value).strip():
            continue
        value = str(value).strip()
        if key in result and _canonical_json(result[key]) != _canonical_json(value):
            conflicts.append({
                "field": key,
                "values": [result[key], value],
                "sources": [*sources.get(key, ()), f"export.argument.{key}"],
            })
        result[key] = value
        sources[key] = [f"export.argument.{key}"]
    if execution is not None:
        if not isinstance(execution, Mapping):
            raise ProfilerUsageError("native execution conditions must be a mapping")
        execution = dict(execution)
        if "execution" in result and _canonical_json(result["execution"]) != _canonical_json(
            execution
        ):
            conflicts.append({
                "field": "execution",
                "values": [result["execution"], execution],
                "sources": [*sources.get("execution", ()), "export.argument.execution"],
            })
        result["execution"] = execution
        sources["execution"] = ["export.argument.execution"]
    found = _native_timing_path(result, "conditions")
    if found:
        raise ProfilerUsageError(f"native conditions must not contain target timing: {found}")
    try:
        _canonical_json(result)
    except (TypeError, ValueError) as exc:
        raise ProfilerUsageError(f"native conditions are not JSON-canonical: {exc}") from exc
    gaps = [
        {"field": field_name, "reason": "not_declared"}
        for field_name in ("hardware",)
        if field_name not in result
        or not isinstance(result.get(field_name), str)
        or not result[field_name].strip()
    ]
    return result, sources, gaps, conflicts


def _native_request_identity(
    boundary: Mapping[str, Any],
    abi: Mapping[str, Any],
    conditions: Mapping[str, Any],
    occurrence: Mapping[str, Any],
    clock: Mapping[str, Any],
    window_id: str | None,
    *,
    condition_gaps: Sequence[Mapping[str, Any]] = (),
    condition_conflicts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    del condition_gaps, condition_conflicts
    fusion = boundary.get("fusion") if isinstance(boundary.get("fusion"), Mapping) else {}
    return {
        "schema": "mindie-profiler-native-request-identity/1",
        "boundary": {
            "kind": boundary.get("kind"),
            "native_operator": boundary.get("native_operator"),
            "scope": boundary.get("scope"),
            "expansion": boundary.get("expansion"),
            "fusion_members": list(fusion.get("members", ())),
        },
        "native_abi_sha256": abi.get("digest"),
        "conditions": dict(conditions),
        "rank": occurrence.get("rank"),
        "stream": occurrence.get("stream_id"),
        "device": occurrence.get("device_id"),
        "clock_domain": clock.get("domain"),
        "window_id": window_id,
    }


def native_prediction_requests(
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Project observations into timing-free requests for an independent native entry."""
    observations = (
        list(source.get("observations", ())) if isinstance(source, Mapping) else list(source)
    )
    requests, seen = [], {}
    grids: dict[str, set[int]] = {}
    for observation in observations:
        if not isinstance(observation, Mapping):
            continue
        request_id = observation.get("request_id")
        block = (observation.get("evidence") or {}).get("block_num")
        try:
            block = int(block)
        except (TypeError, ValueError):
            continue
        if isinstance(request_id, str) and request_id and block > 0:
            grids.setdefault(request_id, set()).add(block)
    for observation in observations:
        if not isinstance(observation, Mapping):
            raise ProfilerUsageError("native observation must be a mapping")
        request_id = observation.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            raise ProfilerUsageError("native observation has no request_id")
        conditions = dict(observation.get("conditions") or {})
        condition_sources = dict(observation.get("condition_sources") or {})
        declared_grids = grids.get(request_id) or set()
        if len(declared_grids) == 1 and "block_num" not in conditions:
            conditions["block_num"] = next(iter(declared_grids))
            condition_sources["block_num"] = ["observation.evidence.block_num"]
        request = {
            "schema": "mindie-profiler-native-prediction-request/1",
            "request_id": request_id,
            "boundary": dict(observation.get("boundary") or {}),
            "abi": dict(observation.get("abi") or {}),
            "conditions": conditions,
            "condition_sources": condition_sources,
            "condition_gaps": list(observation.get("condition_gaps") or ()),
            "condition_conflicts": list(observation.get("condition_conflicts") or ()),
            "occurrence": {
                key: (observation.get("occurrence") or {}).get(key)
                for key in ("rank", "device_id", "stream_id")
            },
            "clock": dict(observation.get("clock") or {}),
            "window_id": (observation.get("timing") or {}).get("window_id"),
        }
        found = _native_timing_path(request, "request")
        if found:
            raise ProfilerUsageError(
                f"native prediction request would leak target timing: {found}"
            )
        payload = _canonical_json(request)
        if request_id not in seen:
            seen[request_id] = payload
            requests.append(request)
        elif seen[request_id] != payload:
            raise ProfilerUsageError(f"conflicting native request identity: {request_id}")
    report = {
        "schema": NATIVE_REQUEST_SCHEMA,
        "requests": requests,
        "counts": {"requests": len(requests), "observations": len(observations)},
        "excluded_fields": [
            "timing.duration_ms",
            "timing.duration_ns",
            "occurrence.start_ns",
            "occurrence.end_ns",
            "occurrence.event_id",
            "evidence.pipe_times_us",
        ],
        "interpretation": (
            "Only ABI and declared conditions are exposed. Observed durations stay "
            "in the profiler observation report and cannot flow into prediction."
        ),
    }
    if isinstance(source, Mapping) and source.get("source_identity"):
        report["source_identity"] = dict(source["source_identity"])
    return report


# ---------------------------------------------------------------------------
# Request condition merging, QBMM lowering, and ordered-slot ABI binding
# ---------------------------------------------------------------------------

def _native_request_condition_parts(
    request: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[str]], list[dict[str, Any]]]:
    """Split request-level and condition-level declarations without loss."""
    conditions = dict(request.get("conditions") or {})
    sources: dict[str, list[str]] = {}
    raw_sources = request.get("condition_sources")
    if isinstance(raw_sources, Mapping):
        for key, value in raw_sources.items():
            labels = value if isinstance(value, (list, tuple)) else [value]
            sources[str(key)] = [str(item) for item in labels if str(item)]
    for key in conditions:
        sources.setdefault(str(key), ["request.conditions"])
    parts: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    for name in ("api", "version", "attrs"):
        top = request.get(name)
        nested = conditions.pop(name, None)
        if isinstance(top, Mapping) and isinstance(nested, Mapping):
            merged = dict(nested)
            for key, value in top.items():
                if key in merged and _canonical_json(merged[key]) != _canonical_json(value):
                    conflicts.append({
                        "field": f"{name}.{key}",
                        "values": [merged[key], value],
                        "sources": [f"request.conditions.{name}", f"request.{name}"],
                    })
                merged[key] = value
            parts[name] = merged
            sources[name] = [f"request.conditions.{name}", f"request.{name}"]
        elif top is not None:
            if nested is not None and _canonical_json(top) != _canonical_json(nested):
                conflicts.append({
                    "field": name,
                    "values": [nested, top],
                    "sources": [f"request.conditions.{name}", f"request.{name}"],
                })
            parts[name] = dict(top) if isinstance(top, Mapping) else top
            sources[name] = [f"request.{name}"]
        elif nested is not None:
            parts[name] = dict(nested) if isinstance(nested, Mapping) else nested
            sources[name] = [f"request.conditions.{name}"]
        else:
            parts[name] = {}
    source_revision = request.get("source_revision")
    if source_revision and isinstance(parts.get("version"), Mapping):
        parts["version"].setdefault("source", source_revision)
        sources.setdefault("version.source", ["request.source_revision"])
    for key in ("software", "runtime", "runner_source", "producer"):
        if key in conditions:
            sources.setdefault(key, ["request.conditions"])
    return parts, conditions, sources, conflicts


def _native_api_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str) and value:
        return {
            "namespace": "torch" if value.startswith("torch") else "aclnn",
            "entry": value,
            "aclnn_symbol": value,
        }
    return {}


def _native_merge_explicit_invocation(
    explicit: Mapping[str, Any],
    parts: Mapping[str, Any],
    conditions: Mapping[str, Any],
    sources: Mapping[str, list[str]],
    conflicts: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge a complete explicit invocation with request declarations."""
    invocation = dict(explicit)
    meta_sources: dict[str, list[str]] = {}
    for name in ("api", "version", "attrs"):
        actual = invocation.get(name)
        declared = parts.get(name)
        if actual is None and declared:
            invocation[name] = declared
            meta_sources[name] = list(sources.get(name, [f"request.{name}"]))
        elif actual is not None and declared:
            if _canonical_json(actual) != _canonical_json(declared):
                conflicts.append({
                    "field": name,
                    "values": [declared, actual],
                    "sources": [*sources.get(name, ()), f"t12_invocation.{name}"],
                })
            meta_sources[name] = [f"t12_invocation.{name}"]
        elif actual is not None:
            meta_sources[name] = [f"t12_invocation.{name}"]
    raw_conditions = invocation.get("conditions")
    explicit_conditions = dict(raw_conditions) if isinstance(raw_conditions, Mapping) else {}
    merged_conditions = dict(conditions)
    for key, value in explicit_conditions.items():
        key = str(key)
        if key in merged_conditions and _canonical_json(
            merged_conditions[key]
        ) != _canonical_json(value):
            conflicts.append({
                "field": key,
                "values": [merged_conditions[key], value],
                "sources": [
                    *sources.get(key, ("request.conditions",)),
                    "t12_invocation.conditions",
                ],
            })
        merged_conditions[key] = value
        meta_sources.setdefault(key, []).append("t12_invocation.conditions")
    for key in ("api", "version", "attrs"):
        merged_conditions.pop(key, None)
    invocation["conditions"] = merged_conditions
    for key, labels in sources.items():
        if key not in {"api", "version", "attrs"}:
            meta_sources.setdefault(key, list(labels))
    return invocation, {
        "sources": meta_sources,
        "conflicts": conflicts,
        "t12_condition_keys": list((invocation.get("conditions") or {}).keys()),
    }


def _qbmm_w8a8_invocation(
    abi: Mapping[str, Any],
    *,
    version: Mapping[str, Any] | None = None,
    attrs: Mapping[str, Any] | None = None,
    conditions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a real 4-slot W8A8 QuantBatchMatmul ABI to a declared invocation."""
    inputs, outputs = list(abi.get("inputs") or ()), list(abi.get("outputs") or ())
    if len(inputs) != _QBMM_INPUT_SLOTS or len(outputs) != 1:
        raise ProfilerUsageError("native_qbmm_w8a8_slot_count")
    x, weight, weight_scale, pertoken = inputs
    output = outputs[0]

    def slot(row: Mapping[str, Any], name: str, role: str) -> dict[str, Any]:
        present = row.get("present", True) is not False
        return {
            "name": name,
            "shape": list(row.get("shape") or ()) if present else None,
            "dtype": row.get("dtype") if present else None,
            "layout": (row.get("layout") or "ND") if present else "ND",
            "role": role,
            "present": present,
            "dtype_present": bool(row.get("dtype")) if present else False,
            "layout_present": bool(row.get("layout")) if present else False,
        }

    weight_name = (
        "weight_nz" if str(weight.get("layout") or "").upper() == "FRACTAL_NZ" else "weight"
    )
    tensors = {
        "x": slot(x, "x", "input"),
        weight_name: slot(weight, weight_name, "weight"),
        "weight_scale": slot(weight_scale, "weight_scale", "scale"),
        "pertoken_scale": slot(pertoken, "pertoken_scale", "scale"),
        "output": slot(output, "output", "output"),
    }
    actual_attrs = dict(attrs or {})
    scale_dtype = str(weight_scale.get("dtype") or "").lower()
    if scale_dtype in {"bf16", "bfloat16"}:
        actual_attrs.setdefault("weight_scale_storage_format", "bf16")
    elif scale_dtype in {"fp32", "float32"}:
        actual_attrs.setdefault("weight_scale_storage_format", "fp32")
    return {
        "api": {
            "namespace": "aclnn",
            "entry": "aclnnQuantMatmulWeightNz",
            "aclnn_symbol": "aclnnQuantMatmulWeightNz",
        },
        "version": dict(version or {}),
        "tensors": tensors,
        "attrs": actual_attrs,
        "conditions": dict(conditions or {}),
    }


def _qbmm_t12_invocation(
    request: Mapping[str, Any],
    *,
    source_revision: str | None,
    parts: Mapping[str, Any],
    conditions: Mapping[str, Any],
    sources: Mapping[str, list[str]],
    conflicts: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    """Map the 4-slot QuantBatchMatmul ABI to its ``mindie-sim`` native leaf."""
    meta = {
        "sources": dict(sources),
        "conflicts": conflicts,
        "t12_condition_keys": list(conditions),
    }
    abi = request.get("abi")
    if not isinstance(abi, Mapping):
        return None, "t12_invocation_unavailable:qbmm_abi_missing", meta
    inputs, outputs = list(abi.get("inputs") or ()), list(abi.get("outputs") or ())
    if len(inputs) != _QBMM_INPUT_SLOTS or len(outputs) != 1:
        return None, "t12_invocation_unavailable:qbmm_slot_count", meta
    raw_version = parts.get("version")
    if isinstance(raw_version, Mapping):
        version = dict(raw_version)
    elif isinstance(raw_version, str) and raw_version:
        version = {"api": raw_version}
    else:
        version = {}
    actual_source = (
        source_revision
        or version.get("source")
        or version.get("source_revision")
        or version.get("revision")
        or request.get("source_revision")
    )
    attrs = dict(parts.get("attrs") or {}) if isinstance(parts.get("attrs"), Mapping) else {}
    declared_api = _native_api_mapping(parts.get("api"))
    weight_scale = inputs[2] if isinstance(inputs[2], Mapping) else {}
    is_w8a8 = (
        str(inputs[0].get("dtype") if isinstance(inputs[0], Mapping) else "").lower()
        in {"int8", "int8_t"}
        or str(weight_scale.get("dtype") or "").lower() in {"bf16", "bfloat16", "fp32"}
        or len(weight_scale.get("shape") or ()) == 1
    )
    if is_w8a8:
        try:
            invocation = _qbmm_w8a8_invocation(
                abi, version=version, attrs=attrs, conditions=conditions
            )
            if declared_api:
                invocation["api"] = declared_api
                meta["sources"]["api"] = list(sources.get("api", ["request.conditions.api"]))
            return invocation, None, meta
        except TimeoutError:
            raise
        except Exception as exc:
            return (
                None,
                f"t12_invocation_unavailable:qbmm_w8a8:{type(exc).__name__}:{exc}",
                meta,
            )
    try:
        x, legacy_weight, legacy_weight_scale, pertoken = inputs
        output = outputs[0]
        x_shape = [int(v) for v in x["shape"]]
        output_shape = [int(v) for v in output["shape"]]
        device_shape = [int(v) for v in legacy_weight["shape"]]
        scale_shape = [int(v) for v in legacy_weight_scale["shape"]]
        pertoken_shape = [int(v) for v in pertoken["shape"]]
    except (KeyError, TypeError, ValueError):
        return None, "t12_invocation_unavailable:qbmm_slot_descriptor", meta
    if len(x_shape) != 2 or len(output_shape) != 2:
        return None, "t12_invocation_unavailable:qbmm_rank", meta
    m, k = x_shape
    if len(device_shape) == _FRACTAL_NZ_RANK:
        n, k2 = device_shape[0] * device_shape[-1], device_shape[1] * device_shape[2]
    elif len(device_shape) == 2:
        if device_shape[1] == k and output_shape == [m, device_shape[1]]:
            k2, n = device_shape
        elif device_shape[0] == k and output_shape == [m, device_shape[0]]:
            n, k2 = device_shape
        elif device_shape[0] == k:
            k2, n = device_shape
        elif device_shape[1] == k:
            n, k2 = device_shape
        else:
            return None, "t12_invocation_unavailable:qbmm_weight_layout", meta
    else:
        return None, "t12_invocation_unavailable:qbmm_weight_layout", meta
    if k2 != k or output_shape != [m, n]:
        return None, "t12_invocation_unavailable:qbmm_geometry", meta
    pairs = ((k + _MXFP8_GROUP_SIZE - 1) // _MXFP8_GROUP_SIZE + 1) // 2
    if scale_shape != [n, pairs, 2] and scale_shape != [pairs, n, 2]:
        return None, "t12_invocation_unavailable:qbmm_scale_geometry", meta
    if pertoken_shape != [m, pairs, 2]:
        return None, "t12_invocation_unavailable:qbmm_scale_geometry", meta

    def tensor(shape: Sequence[int], dtype: Any, layout: str, role: str) -> dict[str, Any]:
        return {
            "shape": list(shape),
            "dtype": dtype,
            "layout": layout,
            "role": role,
            "present": True,
            "dtype_present": True,
            "layout_present": True,
        }

    tensors = {
        "x": tensor([m, k], x.get("dtype"), "ND", "input"),
        "weight": tensor([k, n], legacy_weight.get("dtype"), "ND", "weight"),
        "weight_scale": tensor([pairs, n, 2], "uint8", "ND", "scale"),
        "pertoken_scale": tensor(pertoken_shape, pertoken.get("dtype"), "ND", "scale"),
        "output": tensor([m, n], output.get("dtype"), "ND", "output"),
    }
    actual_version = dict(version)
    if actual_source:
        actual_version.setdefault("source", actual_source)
    physical_w_layout = (
        "FRACTAL_NZ"
        if len(device_shape) == _FRACTAL_NZ_RANK
        or str(legacy_weight.get("layout") or "").upper() == "FRACTAL_NZ"
        else "ND"
    )
    actual_attrs = {
        "group_size": _MXFP8_GROUP_SIZE,
        "output_dtype": "bf16",
        "scale_group": _MXFP8_GROUP_SIZE,
        "weight_scale_storage_format": "fp8_e8m0",
        "weight_scale_storage_bytes": 1,
        "weight_layout": physical_w_layout,
        **attrs,
    }
    api = declared_api or {"namespace": "torch", "entry": "torch_npu.npu_quant_matmul"}
    return {
        "api": api,
        "version": actual_version,
        "tensors": tensors,
        "attrs": actual_attrs,
        "conditions": dict(conditions),
    }, None, meta


def _t12_invocation_from_request(
    request: Mapping[str, Any], *, source_revision: str | None = None
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    """Build one timing-free native operator invocation from an exported request."""
    from .native_abi_model import catalog_spec

    parts, request_conditions, sources, conflicts = _native_request_condition_parts(request)
    declared_conditions = dict(request_conditions)
    meta = {
        "sources": sources,
        "conflicts": conflicts,
        "declared_conditions": declared_conditions,
    }
    explicit = None
    explicit_name = None
    for name in ("t12_invocation", "invocation"):
        candidate = request.get(name)
        if isinstance(candidate, Mapping):
            explicit, explicit_name = candidate, name
            break
    if explicit is not None:
        found = _native_timing_path(explicit, explicit_name or "invocation")
        if found:
            return None, f"t12_invocation_contains_timing:{found}", meta
        invocation, merged_meta = _native_merge_explicit_invocation(
            explicit, parts, request_conditions, sources, conflicts
        )
        meta = {
            **meta,
            "sources": merged_meta["sources"],
            "conflicts": merged_meta["conflicts"],
        }
        return invocation, None, meta
    boundary = request.get("boundary") if isinstance(request.get("boundary"), Mapping) else {}
    if boundary.get("native_operator") == "QuantBatchMatmulV3":
        return _qbmm_t12_invocation(
            request,
            source_revision=source_revision,
            parts=parts,
            conditions=request_conditions,
            sources=sources,
            conflicts=conflicts,
        )
    api = _native_api_mapping(parts.get("api"))
    entry = api.get("entry") or api.get("aclnn_symbol") or request.get("entry")
    native_operator = boundary.get("native_operator") or request.get("native_operator")
    if not entry:
        entry = native_operator
    if not entry:
        return None, "t12_invocation_unavailable:api_entry_not_declared", meta
    resolved = catalog_spec(entry, native_operator)
    if resolved is None:
        return None, "t12_invocation_unavailable:operator_not_in_catalogue", meta
    entry_record = resolved.get("entry") or {}
    slots = (
        entry_record.get("c_abi_slots")
        if isinstance(entry_record.get("c_abi_slots"), Mapping)
        else {}
    )
    slot_specs = (
        slots.get("slot_specs") if isinstance(slots.get("slot_specs"), Mapping) else {}
    )
    declared_inputs = [
        dict(item) for item in slot_specs.get("inputs") or () if isinstance(item, Mapping)
    ]
    declared_outputs = [
        dict(item) for item in slot_specs.get("outputs") or () if isinstance(item, Mapping)
    ]
    if not declared_inputs and not declared_outputs:
        return None, "t12_invocation_unavailable:descriptors_missing", meta
    if not api.get("entry"):
        api = {
            "namespace": "native",
            "entry": resolved.get("name") or entry,
            "aclnn_symbol": None,
        }
    abi = request.get("abi") if isinstance(request.get("abi"), Mapping) else {}
    input_slots = list(abi.get("inputs") or ())
    output_slots = list(abi.get("outputs") or ())
    if len(input_slots) > len(declared_inputs) or len(output_slots) > len(declared_outputs):
        return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    tensors: dict[str, Any] = {}

    def bind_slot(declared: Mapping[str, Any], slot: Any, *, output: bool = False) -> None:
        name = str(declared.get("name") or declared.get("c_name") or "tensor")
        role = "output" if output else str(declared.get("role") or "input")
        if slot is None:
            tensors[name] = {
                "shape": None,
                "dtype": None,
                "layout": declared.get("layout") or "ND",
                "role": role,
                "optional": True,
                "present": False,
            }
            return
        if isinstance(slot, Mapping):
            present = slot.get("present", True) is not False
            if str(slot.get("presence") or "").lower() in {"absent", "not_present"}:
                present = False
            if str(slot.get("quality") or "").strip() == "undefined":
                present = False
            if not slot.get("shape") and slot.get("dtype") is None and declared.get("optional"):
                present = False
            shape = slot.get("shape") if present else None
            dtype = slot.get("dtype") if present else None
            layout = slot.get("layout") if present else None
        else:
            present = True
            shape, dtype, layout = slot
        tensors[name] = {
            "shape": list(shape) if shape is not None else None,
            "dtype": dtype,
            "layout": layout or declared.get("layout") or "ND",
            "role": role,
            "optional": bool(declared.get("optional")),
            "present": present,
        }

    for index, declared in enumerate(declared_inputs):
        if index < len(input_slots):
            bind_slot(declared, input_slots[index])
        elif declared.get("optional"):
            bind_slot(declared, None)
        else:
            return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    for index, declared in enumerate(declared_outputs):
        if index < len(output_slots):
            bind_slot(declared, output_slots[index], output=True)
        elif declared.get("optional"):
            bind_slot(declared, None, output=True)
        else:
            return None, "t12_invocation_unavailable:tensor_slot_count_mismatch", meta
    raw_version = parts.get("version")
    version = (
        dict(raw_version)
        if isinstance(raw_version, Mapping)
        else ({"api": raw_version} if isinstance(raw_version, str) and raw_version else {})
    )
    attrs = dict(parts.get("attrs") or {}) if isinstance(parts.get("attrs"), Mapping) else {}
    if str(boundary.get("kind") or "") == "kernel" and str(
        api.get("aclnn_symbol") or api.get("entry") or ""
    ) in {"aclnnMatmul", "torch.matmul", "MatMulV3", "MatMulV2"}:
        x1_slot = tensors.get("x1") or {}
        x2_slot = tensors.get("x2") or {}
        out_slot = tensors.get("output") or {}
        x1_shape = x1_slot.get("shape") if x1_slot.get("present") else None
        x2_shape = x2_slot.get("shape") if x2_slot.get("present") else None
        out_shape = out_slot.get("shape") if out_slot.get("present") else None
        if (
            isinstance(x1_shape, list)
            and len(x1_shape) == 2
            and isinstance(x2_shape, list)
            and len(x2_shape) == 2
            and isinstance(out_shape, list)
            and len(out_shape) == 2
            and str(x1_slot.get("layout") or "ND").upper() == "ND"
            and str(x2_slot.get("layout") or "ND").upper() == "ND"
        ):
            out_m, out_n = out_shape[0], out_shape[1]
            if (
                "transpose_x1" not in attrs
                and x1_shape[0] == out_m
                and x1_shape[1] == out_m
                and out_m in (x2_shape[0], x2_shape[1])
            ):
                attrs["transpose_x1"] = False
                sources.setdefault("attrs.transpose_x1", []).append("kernel_nd_square_storage")
            inferred_k = (
                x1_shape[0]
                if attrs.get("transpose_x1") is True
                else x1_shape[1]
                if attrs.get("transpose_x1") is False
                else x1_shape[1]
                if x1_shape[0] == out_m and x1_shape[1] != out_m
                else x1_shape[0]
                if x1_shape[1] == out_m and x1_shape[0] != out_m
                else None
            )
            if (
                "transpose_x2" not in attrs
                and inferred_k == out_n
                and x2_shape[0] == out_n
                and x2_shape[1] == out_n
            ):
                attrs["transpose_x2"] = False
                sources.setdefault("attrs.transpose_x2", []).append("kernel_nd_square_storage")
    conditions = dict(request_conditions)
    for key in ("epsilon", "eps", "norm_eps"):
        if key in conditions:
            if key not in attrs:
                attrs[key] = conditions[key]
            conditions.pop(key)
            sources.setdefault(f"attrs.{key}", [])
            sources[f"attrs.{key}"].append(f"request.conditions.{key}")
    meta = {
        "sources": sources,
        "conflicts": conflicts,
        "declared_conditions": declared_conditions,
        "t12_condition_keys": list(conditions),
        "catalog_state": resolved.get("state") or "",
    }
    return {
        "api": api,
        "version": version,
        "tensors": tensors,
        "attrs": attrs,
        "conditions": conditions,
    }, None, meta


def _t12_duration_ms(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        if isinstance(value, str) and "/" in value:
            return float(Fraction(value))
        number = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return number


def _dtype_identity(dtype: Any) -> str:
    text = str(dtype or "").lower()
    return _DTYPE_STORAGE_ALIASES.get(text, text)


def _declared_slot_signature(abi: Mapping[str, Any]) -> list[str]:
    """Ordered present tensor signature ``(shape, dtype)`` of one declared ABI."""
    out: list[str] = []
    for direction in ("inputs", "outputs"):
        for slot in abi.get(direction) or ():
            if not isinstance(slot, Mapping) or not slot.get("present"):
                continue
            shape = slot.get("shape")
            if not isinstance(shape, (list, tuple)) or not shape:
                continue
            out.append(_canonical_json([list(shape), _dtype_identity(slot.get("dtype"))]))
    return out


def _invocation_slots(invocation: Mapping[str, Any]) -> list[str]:
    """Ordered present tensor signature ``(shape, dtype)`` of one invocation."""
    out: list[str] = []
    for tensor in (invocation.get("tensors") or {}).values():
        if not isinstance(tensor, Mapping) or tensor.get("present") is False:
            continue
        shape = tensor.get("shape")
        if not isinstance(shape, (list, tuple)) or not shape:
            continue
        out.append(_canonical_json([list(shape), _dtype_identity(tensor.get("dtype"))]))
    return out


def _slot_shape_equivalent(declared: Any, actual: Any) -> bool:
    """True when two declared slot shapes describe the same physical buffer."""
    left = list(declared or ())
    right = list(actual or ())
    if left == right:
        return True
    if len(left) != len(right):
        return False
    if len(left) == 2:
        return left == [right[1], right[0]]
    if len(left) > 2:
        return left[0] == right[1] and left[1] == right[0] and left[2:] == right[2:]
    return False


def _slots_equivalent(declared: list, actual: list) -> bool:
    """Ordered slot equivalence under the declared storage-transpose rule."""
    if len(declared) != len(actual):
        return False
    for left, right in zip(declared, actual):
        try:
            lshape, ldtype = json.loads(left)
            rshape, rdtype = json.loads(right)
        except (TypeError, ValueError):
            return False
        if ldtype != rdtype:
            return False
        if not _slot_shape_equivalent(lshape, rshape):
            return False
    return True


def _request_abi_lowered(result: Any, request_abi: Any) -> bool:
    """True when the selected program consumed exactly the declared request ABI."""
    if not isinstance(request_abi, Mapping):
        return False
    if str(request_abi.get("status") or "") != "complete":
        return False
    if not request_abi.get("digest") or not request_abi.get("verified"):
        return False
    invocation = getattr(result, "invocation", None)
    if not isinstance(invocation, Mapping):
        return False
    declared = _declared_slot_signature(request_abi)
    actual = _invocation_slots(invocation)
    return bool(declared) and _slots_equivalent(declared, actual)


def _t12_abi(result: Any) -> dict[str, Any] | None:
    """Project the actual declared invocation sequence, not a compressed dict."""
    invocation = getattr(result, "invocation", None)
    if not isinstance(invocation, Mapping):
        return None
    declared = invocation.get("tensors")
    if not isinstance(declared, Mapping) or not declared:
        return None
    program = getattr(result, "program", None)
    physical = program.get("physical") if isinstance(program, Mapping) else None
    physical_tensors = physical.get("tensors") if isinstance(physical, Mapping) else None
    physical_tensors = physical_tensors if isinstance(physical_tensors, Mapping) else {}
    binding = getattr(result, "binding", None)
    binding_dict = binding.to_dict() if hasattr(binding, "to_dict") else {}
    kernels = binding_dict.get("kernels") or []
    operator = kernels[0].get("name") if kernels and isinstance(kernels[0], Mapping) else None
    if not operator:
        spec = getattr(result, "spec", None) or {}
        kernels = spec.get("kernels") or ()
        operator = (
            kernels[0].get("name")
            if kernels and isinstance(kernels[0], Mapping)
            else spec.get("entry")
        )
    if not operator:
        return None
    inputs, outputs = [], []
    for name, tensor in declared.items():
        if not isinstance(tensor, Mapping):
            return None
        present = tensor.get("present", True) is not False
        if not present and tensor.get("optional") is True:
            continue
        selected = physical_tensors.get(name)
        if isinstance(selected, Mapping):
            views = selected.get("views") if isinstance(selected.get("views"), Mapping) else {}
            device = views.get("device") if isinstance(views.get("device"), Mapping) else {}
            logical = views.get("logical") if isinstance(views.get("logical"), Mapping) else {}
            storage = views.get("storage") if isinstance(views.get("storage"), Mapping) else {}
            interp = (
                views.get("interpretation")
                if isinstance(views.get("interpretation"), Mapping)
                else {}
            )
            shape = (
                device.get("shape")
                or selected.get("shape")
                or logical.get("shape")
                or storage.get("shape")
            )
            dtype = (
                interp.get("dtype")
                or device.get("dtype")
                or selected.get("dtype")
                or logical.get("dtype")
                or storage.get("dtype")
            )
            layout = (
                device.get("layout")
                or selected.get("layout")
                or logical.get("layout")
                or storage.get("layout")
                or "ND"
            )
        else:
            shape = tensor.get("shape") if present else None
            dtype = tensor.get("dtype") if present else None
            layout = tensor.get("layout") if present else None
        slot = {
            "shape": list(shape) if isinstance(shape, (list, tuple)) else None,
            "dtype": dtype,
            "layout": layout,
            "present": present,
            "dtype_present": present and bool(dtype),
            "layout_present": present and bool(layout),
        }
        (outputs if tensor.get("role") == "output" else inputs).append(slot)
    from .native_tensor_abi import native_abi_from_slots

    return native_abi_from_slots(operator, inputs, outputs)


def _native_prediction_request_fields(request: Mapping[str, Any]) -> dict[str, Any]:
    """Request-side facts retained on every prediction, modelled or not."""
    timing = request.get("timing")
    timing = timing if isinstance(timing, Mapping) else {}
    return {
        "boundary": dict(request.get("boundary") or {}),
        "occurrence": dict(request.get("occurrence") or {}),
        "clock": dict(request.get("clock") or {}),
        "window_id": request.get("window_id") or timing.get("window_id"),
        "request_conditions": dict(request.get("conditions") or {}),
        "request_condition_sources": dict(request.get("condition_sources") or {}),
        "condition_gaps": list(request.get("condition_gaps") or ()),
        "condition_conflicts": list(request.get("condition_conflicts") or ()),
        "conditions": {},
    }


def _native_json_safe(value: Any) -> Any:
    """Project a receipt onto JSON values without dropping its fields."""
    if isinstance(value, Mapping):
        return {str(key): _native_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_native_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


# ---------------------------------------------------------------------------
# Canonical ExecutionEnvironment construction & native prediction execution
# ---------------------------------------------------------------------------

def _canonical_environment(hardware: Any, execution: Any = None) -> tuple[Any, str | None]:
    """Build one canonical execution environment from supplied declarations."""
    from mindie_sim.public import ExecutionEnvironment

    if isinstance(hardware, ExecutionEnvironment):
        return hardware, None
    if hardware is None and execution is not None:
        borrowed = getattr(execution, "case", None)
        machine = getattr(borrowed, "machine", None)
        if machine is not None:
            try:
                return (
                    ExecutionEnvironment.from_hardware(
                        machine, runtime=getattr(borrowed, "runtime", None)
                    ),
                    None,
                )
            except TimeoutError:
                raise
            except Exception as exc:  # noqa: BLE001 - concrete environment gap
                return None, f"t12_environment_unavailable:{type(exc).__name__}:{exc}"
        return None, "t12_environment_unavailable:execution_has_no_hardware"
    from mindie_sim.schema.hardware import Hardware

    if isinstance(hardware, Hardware):
        return ExecutionEnvironment.from_hardware(hardware), None
    if isinstance(hardware, Mapping):
        raw = dict(hardware)
        if isinstance(raw.get("machine"), Mapping):
            raw = dict(raw["machine"])
        try:
            return ExecutionEnvironment.from_hardware(Hardware.from_mapping(raw)), None
        except TimeoutError:
            raise
        except Exception as exc:  # noqa: BLE001 - concrete environment gap
            return None, f"t12_environment_unavailable:{type(exc).__name__}:{exc}"
    if isinstance(hardware, str) and hardware.strip():
        from mindie_sim.backends import materialize

        requested = hardware.strip()
        try:
            from mindie_sim.compose import resolve_hardware_sku

            sku = resolve_hardware_sku(requested)
        except ImportError:
            sku = requested
        except (TypeError, ValueError) as exc:
            try:
                from mindie_sim.backends.ascend import profiles

                lookup = {str(item).lower(): item for item in profiles()}
                sku = lookup.get(requested.lower()) or lookup.get("ascend" + requested.lower())
            except ImportError:
                sku = None
            if sku is None:
                return None, f"t12_environment_unavailable:unknown_hardware_sku:{exc}"
        failures: list[str] = []
        for backend in ("ascend", "nvidia"):
            try:
                machine = Hardware.from_mapping(
                    materialize({"backend": backend, "sku": sku, "num_devices": 1})
                )
                return ExecutionEnvironment.from_hardware(machine), None
            except TimeoutError:
                raise
            except Exception as exc:  # noqa: BLE001 - try the next backend
                failures.append(f"{backend}:{type(exc).__name__}")
        return None, "t12_environment_unavailable:" + ",".join(failures)
    return None, "t12_environment_unavailable:hardware_not_declared"


def _binding_state(plan: Any) -> tuple[bool, str | None]:
    """Resolve the canonical source binding receipt, never a version label."""
    del plan
    return False, None


def _canonical_result(
    plan: Any,
    report: Mapping[str, Any] | None,
    *,
    duration: float | None,
    execute: bool,
    submitted: bool = False,
    execution_receipt: Mapping[str, Any] | None = None,
) -> Any:
    """Project one canonical call report onto the retained prediction receipt."""
    bound, gap = _binding_state(plan)
    payload = _canonical_json({
        "operator": plan.operator,
        "slots": [
            [
                tensor.get("shape"),
                tensor.get("dtype"),
                tensor.get("layout"),
                bool(tensor.get("present", True)),
            ]
            for tensor in plan.tensors.values()
        ],
        "api": plan.api,
        "attrs": plan.attrs,
    })
    call_id = "native:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    kernel = {"name": plan.operator}
    binding = {
        "call_id": call_id,
        "api": dict(plan.api),
        "typed": {
            "source": None,
            "kernels": [kernel],
            "variant": plan.conditions.get("variant"),
            "relation": "declared_native_call",
            "shapes": {
                str(name): list(tensor.get("shape"))
                for name, tensor in plan.tensors.items()
                if tensor.get("present") is not False
                and isinstance(tensor.get("shape"), (list, tuple))
            },
        },
        "unresolved": list(plan.unresolved)
        + (["attributable_source_reference_unresolved"] if not bound else []),
    }
    physical = {"tensors": plan.tensors}
    program = {
        "caller_plan": {"variant": plan.conditions.get("variant")},
        "physical": physical,
    }
    environment = {
        "basis": "canonical_declared_call",
        "arch": plan.family,
        "dtype": next((str(t.get("dtype")) for t in plan.tensors.values() if t.get("dtype")), ""),
        "policy": "simulate_native_call",
    }
    payload_dict = {
        "status": "predicted" if gap is None else "unmodeled",
        "reasons": [gap] if gap is not None else [],
        "binding_bound": bound,
        "invocation": {
            "api": dict(plan.api),
            "version": dict(plan.version),
            "tensors": plan.tensors,
            "attrs": dict(plan.attrs),
            "conditions": dict(plan.conditions),
        },
        "program": program,
        "binding": binding,
        "environment": environment,
        "spec": {"entry": plan.operator, "kernels": [kernel]},
        "prediction": {"duration_ms": duration, "work": plan.work},
        "execution_receipt": (
            dict(execution_receipt) if isinstance(execution_receipt, Mapping) else None
        ),
        "execution_handle_available": bool(submitted),
        "canonical": {
            "entry": "mindie_sim.simulate_native_call",
            "executed": bool(execute),
            "report": dict(report) if isinstance(report, Mapping) else None,
        },
    }
    return SimpleNamespace(
        status=payload_dict["status"],
        reasons=payload_dict["reasons"],
        binding_bound=bool(bound),
        invocation=payload_dict["invocation"],
        program=program,
        binding=SimpleNamespace(to_dict=lambda: dict(binding)),
        environment=environment,
        spec=payload_dict["spec"],
        prediction=payload_dict["prediction"],
        to_dict=lambda: dict(payload_dict),
    )


def _simulate_canonical(
    environment: Any,
    plan: Any,
    *,
    execute: bool,
    execution: Any = None,
    blocking: bool = True,
) -> tuple[Any, float | None]:
    """Run one declared call through the canonical simulator entry point."""
    if not execute:
        return _canonical_result(plan, None, duration=None, execute=False), None
    if execution is not None:
        if blocking:
            report = environment.graph_report(plan.ops, execution=execution)
            duration = _t12_duration_ms(report.get("duration_ms"))
            receipt = {
                "basis": "caller_supplied_execution",
                "blocking": True,
                "submitted": True,
                "duration_ms": duration,
                "operator_events": report.get("operator_events"),
                "complete_ms": report.get("complete_ms"),
            }
        else:
            step, _actual, _result, normalized = environment.submit_graph(
                plan.ops, execution=execution
            )
            completion = getattr(step, "completion", None)
            receipt = {
                "basis": "caller_supplied_execution",
                "blocking": False,
                "submitted": True,
                "duration_ms": None,
                "duration_basis": "deferred_until_caller_advances_engine",
                "operator_events": len(normalized),
                "replica": getattr(step, "replica", None),
                "iteration": getattr(step, "iteration", None),
                "start_ms": getattr(step, "start_ms", None),
                "completion_event": getattr(completion, "name", None),
                "completion_pending": completion is None or not completion.done,
            }
            duration = None
            report = {
                "schema": "mindie-sim.call-costs/1",
                "boundary": "standalone_declared_graph",
                "duration_ms": None,
                "duration_deferred": True,
                "operator_events": len(normalized),
                "step": {
                    key: receipt[key]
                    for key in (
                        "replica",
                        "iteration",
                        "start_ms",
                        "completion_event",
                        "completion_pending",
                    )
                },
            }
        return (
            _canonical_result(
                plan,
                report,
                duration=duration,
                execute=True,
                submitted=True,
                execution_receipt=receipt,
            ),
            duration,
        )
    from mindie_sim import simulate_native_call

    report = simulate_native_call(environment, plan.ops)
    duration = _t12_duration_ms(report.get("duration_ms"))
    return _canonical_result(plan, report, duration=duration, execute=True), duration


def predict_native_requests(
    requests: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    hardware: Any = None,
    supply: Any = None,
    policy: Any = None,
    phase: str | None = None,
    source_revision: str | None = None,
    execution: Any = None,
    execute: bool | None = None,
    blocking: bool = True,
) -> dict[str, Any]:
    """[Cohesive-Pipeline] Run timing-free requests through ``mindie-sim`` native execution."""
    del policy
    if execute is None:
        execute = bool(hardware is not None or supply is not None or execution is not None)
    rows = list(requests.get("requests", ())) if isinstance(requests, Mapping) else list(requests)
    environment, environment_gap = _canonical_environment(hardware, execution)
    predictions = []
    for request in rows:
        if not isinstance(request, Mapping):
            raise ProfilerUsageError("native prediction request must be a mapping")
        request_id = request.get("request_id")
        leak = _native_timing_path(request, "request")
        if leak:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id,
                "status": "unmodeled",
                "reason": "t12_request_contains_timing:" + leak,
                "duration_ms": None,
                "evidence": ["timing-free request rejected before T12 binding"],
                "t12": {"status": "not_invoked", "reason": "request_timing_present"},
                **_native_prediction_request_fields(request),
            })
            continue
        invocation, gap, invocation_meta = _t12_invocation_from_request(
            request, source_revision=source_revision
        )
        if invocation is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id,
                "status": "unmodeled",
                "reason": gap,
                "duration_ms": None,
                "evidence": [
                    "T12 invocation not constructible without explicit ABI/dispatch facts"
                ],
                "t12": {"status": "not_invoked", "reason": gap},
                **_native_prediction_request_fields(request),
            })
            continue
        boundary = request.get("boundary") if isinstance(request.get("boundary"), Mapping) else {}
        plan, plan_gap = build_plan(
            invocation,
            native_operator=boundary.get("native_operator") or request.get("native_operator"),
            phase=phase,
            cann_version=(invocation.get("version") or {}).get("api"),
        )
        if plan is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id,
                "status": "unmodeled",
                "reason": plan_gap,
                "duration_ms": None,
                "evidence": ["canonical ABI normalization preserved an explicit gap"],
                "t12": {"status": "not_invoked", "reason": plan_gap},
                **_native_prediction_request_fields(request),
            })
            continue
        if environment is None:
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id,
                "status": "unmodeled",
                "reason": environment_gap,
                "duration_ms": None,
                "evidence": ["canonical ExecutionEnvironment not constructible"],
                "t12": {"status": "environment_unavailable"},
                **_native_prediction_request_fields(request),
            })
            continue
        try:
            result, duration = _simulate_canonical(
                environment,
                plan,
                execute=bool(execute),
                execution=execution,
                blocking=blocking,
            )
        except TimeoutError:
            raise
        except Exception as exc:  # preserve a concrete provider gap
            predictions.append({
                "prediction_id": "t12:" + str(request_id or "unidentified"),
                "request_id": request_id,
                "status": "unmodeled",
                "reason": f"t12_exception:{type(exc).__name__}:{exc}",
                "duration_ms": None,
                "evidence": ["canonical simulate_native_call raised; no observation used"],
                "t12": {"status": "exception", "exception": type(exc).__name__},
                **_native_prediction_request_fields(request),
            })
            continue
        prediction_payload = result.prediction or {}
        if result.status == "predicted" and duration is not None:
            status = "modeled"
        elif result.status == "predicted":
            status = "modeled_work_only"
        else:
            status = "unmodeled"
        payload = result.to_dict()
        invocation = result.invocation or {}
        result_environment = result.environment or {}
        binding_payload = payload.get("binding") or {}
        typed = binding_payload.get("typed") or {}
        actual_conditions: dict[str, Any] = {}
        actual_condition_sources: dict[str, list[str]] = {}
        actual_condition_conflicts = list(invocation_meta.get("conflicts") or ())

        def add_actual(key: str, value: Any, source: str) -> None:
            key = str(key)
            if key in actual_conditions:
                if _canonical_json(actual_conditions[key]) != _canonical_json(value):
                    actual_condition_conflicts.append({
                        "field": key,
                        "values": [actual_conditions[key], value],
                        "sources": [*actual_condition_sources.get(key, ()), source],
                    })
                actual_condition_sources.setdefault(key, []).append(source)
                return
            actual_conditions[key] = value
            actual_condition_sources.setdefault(key, []).append(source)

        for key, value in dict(invocation.get("conditions") or {}).items():
            add_actual(key, value, "t12.invocation.conditions")
        for name in ("api", "version", "attrs"):
            value = invocation.get(name)
            if isinstance(value, Mapping):
                add_actual(name, dict(value), "t12.invocation." + name)
        image_id = (invocation.get("version") or {}).get("image_id")
        if image_id:
            add_actual("deployment_image_id", image_id, "t12.invocation.version.image_id")
        add_actual(
            "implementation",
            {
                "api": binding_payload.get("api"),
                "source": typed.get("source"),
                "kernels": typed.get("kernels"),
                "variant": typed.get("variant"),
                "relation": typed.get("relation"),
            },
            "t12.binding.implementation",
        )
        add_actual(
            "execution",
            {
                "basis": result_environment.get("basis"),
                "arch": result_environment.get("arch"),
                "dtype": result_environment.get("dtype"),
                "policy": result_environment.get("policy"),
            },
            "t12.environment.execution",
        )
        actual_hardware = result_environment.get("hardware") or hardware
        if actual_hardware:
            add_actual(
                "hardware",
                actual_hardware
                if isinstance(actual_hardware, str)
                else getattr(actual_hardware, "hardware_key", None)
                or getattr(getattr(actual_hardware, "machine", None), "sku", None),
                "t12.environment.hardware"
                if result_environment.get("hardware")
                else "predict.argument.hardware",
            )
        actual_phase = result_environment.get("phase") or phase
        if actual_phase:
            add_actual(
                "phase",
                actual_phase,
                "t12.environment.phase"
                if result_environment.get("phase")
                else "predict.argument.phase",
            )
        declared_conditions = dict(request.get("conditions") or {})
        actual_condition_gaps = [
            {"field": str(key), "reason": "not_consumed_by_t12_invocation"}
            for key in declared_conditions
            if key not in actual_conditions
        ]
        actual_condition_sources = {
            key: list(dict.fromkeys(labels))
            for key, labels in actual_condition_sources.items()
        }
        deduped_conflicts: dict[tuple[str, str], dict[str, Any]] = {}
        for row in actual_condition_conflicts:
            field_name = str(row.get("field"))
            deduped_conflicts[(field_name, _canonical_json(row.get("values")))] = {
                "field": field_name,
                "values": list(row.get("values") or ()),
                "sources": [str(item) for item in row.get("sources") or ()],
            }
        actual_condition_conflicts = [
            deduped_conflicts[key] for key in sorted(deduped_conflicts)
        ]
        declared_keys = set(request.get("conditions") or ())
        actual_keys = set(invocation_meta.get("t12_condition_keys") or ())
        actual_keys.update({"api", "version", "attrs", "hardware", "phase"})
        if (invocation.get("version") or {}).get("image_id"):
            actual_keys.add("deployment_image_id")
        condition_scope = {
            key: ("actual" if key in actual_keys else "declaration") for key in declared_keys
        }
        request_software = request.get("software")
        request_runtime = request.get("runtime")
        runner_source = request.get("runner_source", request.get("producer"))
        source_domains = {
            "request_version": dict(request.get("version") or {}),
            "request_software": dict(request_software)
            if isinstance(request_software, Mapping)
            else {},
            "request_runtime": dict(request_runtime)
            if isinstance(request_runtime, Mapping)
            else {},
            "runner_source": dict(runner_source) if isinstance(runner_source, Mapping) else {},
            "t12_invocation_version": dict(invocation.get("version") or {}),
            "t12_invocation_conditions": dict(invocation.get("conditions") or {}),
            "t12_environment": dict(result_environment),
            "t12_binding_source": typed.get("source"),
        }
        abi_for_eligibility = _t12_abi(result) if result.status == "predicted" else None
        request_abi = request.get("abi")
        same_abi = bool(
            isinstance(request_abi, Mapping)
            and request_abi.get("verified")
            and abi_for_eligibility
            and request_abi.get("digest") == abi_for_eligibility.get("digest")
        )
        if result.status == "predicted" and same_abi:
            abi_for_eligibility = dict(request_abi)
            abi_for_eligibility["digest_source"] = (
                "declared_request_slots_lowered_by_selected_program"
            )
        prediction = {
            "prediction_id": "t12:"
            + str(request_id or payload.get("spec", {}).get("entry", "native")),
            "request_id": request_id,
            "status": status,
            "duration_ms": duration,
            "duration_available": duration is not None,
            "work": prediction_payload.get("work"),
            "boundary": dict(request.get("boundary") or {}),
            "occurrence": dict(request.get("occurrence") or {}),
            "clock": dict(request.get("clock") or {}),
            "window_id": request.get("window_id")
            or (request.get("timing") or {}).get("window_id"),
            "conditions": actual_conditions,
            "condition_sources": actual_condition_sources,
            "condition_gaps": actual_condition_gaps,
            "condition_conflicts": actual_condition_conflicts,
            "condition_scope": condition_scope,
            "request_conditions": dict(request.get("conditions") or {}),
            "request_condition_sources": dict(request.get("condition_sources") or {}),
            "source_domains": source_domains,
            "eligibility": {
                "cpu_mechanism": result.status == "predicted",
                "selected_plan": bool(payload.get("program")),
                "timed_pairing": duration is not None,
                "capture_pairing": same_abi,
            },
            "abi": abi_for_eligibility,
            "evidence": [
                "mindie_sim.simulate_native_call",
                "binding_bound=" + str(bool(getattr(result, "binding_bound", False))),
                "request_contains_no_observed_duration",
                *(["actual_submission_receipt"] if payload.get("execution_receipt") else []),
            ],
            "submitted": bool(payload.get("execution_handle_available")),
            "actual_execution": _native_json_safe(payload.get("execution_receipt")),
            "t12": {
                "status": payload.get("status"),
                "binding_bound": bool(getattr(result, "binding_bound", False)),
                "reasons": list(payload.get("reasons") or ()),
                "binding": payload.get("binding"),
                "occurrence": payload.get("occurrence"),
                "program": payload.get("program"),
                "replay_minimal": payload.get("replay_minimal"),
                "environment": payload.get("environment"),
                "source_establishment": payload.get("source_establishment"),
                "invocation": payload.get("invocation"),
                "actual_conditions": actual_conditions,
            },
        }
        if status == "modeled_work_only":
            prediction["reason"] = "t12_timing_free_work_only_no_duration"
        elif status != "modeled":
            prediction["reason"] = "t12_" + str(result.status) + (
                ":" + ";".join(result.reasons) if result.reasons else ""
            )
        predictions.append(prediction)
    statuses: dict[str, int] = {}
    for prediction in predictions:
        statuses[prediction["status"]] = statuses.get(prediction["status"], 0) + 1
    submitted = sum(1 for item in predictions if item.get("submitted"))
    all_modeled = bool(predictions) and all(
        item.get("status") == "modeled" and item.get("duration_ms") is not None
        for item in predictions
    )
    return _native_json_safe({
        "schema": "mindie-profiler-t12-native-predictions/1",
        "predictions": predictions,
        "all_modeled": all_modeled,
        "execution": {
            "requested": bool(execute),
            "caller_execution": execution is not None,
            "blocking": bool(blocking),
            "submitted": submitted,
        },
        "counts": {
            "requests": len(rows),
            "predictions": len(predictions),
            "submitted": submitted,
            **{f"status_{key}": value for key, value in statuses.items()},
        },
        "non_claims": [
            "no_model_case_constructed",
            "no_default_model_or_quantization",
            "no_observation_identity_used_as_prediction",
            "t12_gap_preserved_when_native_binding_not_implemented",
            "cpu_prediction_only_not_device_execution",
        ],
    })


__all__ = [
    "_DTYPE_STORAGE_ALIASES",
    "_NATIVE_EXECUTION_CORES",
    "_T12_CONDITION_KEYS",
    "_binding_state",
    "_canonical_environment",
    "_canonical_result",
    "_declared_slot_signature",
    "_dtype_identity",
    "_invocation_slots",
    "_native_api_mapping",
    "_native_capture_selection",
    "_native_conditions",
    "_native_json_safe",
    "_native_merge_explicit_invocation",
    "_native_operator_identity",
    "_native_prediction_request_fields",
    "_native_request_condition_parts",
    "_native_request_identity",
    "_qbmm_t12_invocation",
    "_qbmm_w8a8_invocation",
    "_request_abi_lowered",
    "_simulate_canonical",
    "_slot_shape_equivalent",
    "_slots_equivalent",
    "_t12_abi",
    "_t12_duration_ms",
    "_t12_invocation_from_request",
    "native_prediction_requests",
    "predict_native_requests",
]
