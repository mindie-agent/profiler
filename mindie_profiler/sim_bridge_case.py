"""Simulator Case normalization and native operator observation/request bridge (sim_bridge_case).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting simulator case normalization and native operator observation/request bridge.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import argparse, csv, hashlib, json, math, os, re, sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from .events import PARSER_VERSION, ProfilerError, ProfilerUsageError
from .sim_bridge_cells import (
    CellSpec, cell_from_dict, forecast_cell, predict_cell, source_declarations,
    structure_fingerprint,
)

from .sim_bridge_observed import NATIVE_REQUEST_SCHEMA, _canonical_json, _native_timing_path

@dataclass(frozen=True)
class OperatorRow:
    """One published operator occurrence from a canonical public graph."""

    name: str
    kind: str
    mechanism: str
    subgraph: str
    duration_ms: float
    count: int
    regime: tuple[tuple[str, int], ...]
    dominant_pipe: str
    formula: str
    segment: int
    cost: Any = field(default=None, compare=False, repr=False)
    native_call: Any = field(default=None, compare=False, repr=False)
    native_occurrence: Any = field(default=None, compare=False, repr=False)
    phase: str = ""

    @property
    def total_ms(self) -> float:
        return self.duration_ms * self.count

    @property
    def guard_text(self) -> str:
        return (";" .join(f"{key}={value}" for key, value in self.regime)
                if self.regime else "no_discrete_guard")


def _native_capture_selection(value: str | Path, *, rank: str | None) -> tuple[Path, dict[str, Any]]:
    """Select one kernel_details CSV without hiding sibling-rank facts.

    Directory inputs consume CLOCK's inventory (the same bounded source/capture
    relation as T03), retain every rank candidate and read error, then require
    one unambiguous kernel_details source.  A sibling rank with only
    op_summary/task_time is a native-source gap, not silently omitted.
    """
    path = Path(value).expanduser().resolve()
    if path.is_file():
        if path.suffix.lower() not in {".csv", ".gz"}:
            raise ProfilerUsageError(
                "native observations require a kernel_details CSV; "
                f"got {path.name}")
        return path, {"kind": "explicit_file", "path": str(path),
                      "selected_path": str(path), "rank_count": 1,
                      "selected_rank": None, "ranks": []}
    if not path.is_dir():
        raise ProfilerUsageError(f"native observation input does not exist: {path}")
    from .inventory import inventory_profile
    try:
        inventory = inventory_profile(path)
    except ProfilerError as exc:
        raise ProfilerUsageError(
            f"native observations: inventory discovery failed for {path}: {exc}") from exc
    ranks = list(inventory.get("ranks") or ())
    facts = []
    for item in ranks:
        files = [file for file in item.get("files") or ()
                 if str(file.get("basename") or "").lower()
                 in {"kernel_details.csv", "kernel_details.csv.gz"}]
        facts.append({
            "rank_id": item.get("rank_id"), "rank_index": item.get("rank_index"),
            "rank_dir": item.get("rank_dir"),
            "kernel_details": [str(file.get("path")) for file in files],
            "csv_candidates": list(item.get("csv_candidates") or ()),
            "selected_csv": list(item.get("selected_csv") or ()),
            "db_candidates": list(item.get("db_candidates") or ()),
            "trace_candidates": list(item.get("trace_candidates") or ()),
            "limitations": list(item.get("limitations") or ()),
            "files": [
                dict(file) for file in (item.get("files") or ())
                if isinstance(file, Mapping)
            ],
        })
    discovery = {
        "kind": "clock_inventory", "root": str(path), "rank_count": len(ranks),
        "ranks": facts, "source_identity": inventory.get("capture_ids"),
        "selected_rank": rank, "selected_path": None,
        "sibling_rank_gaps": [
            {"rank_id": item.get("rank_id"), "reason": "no_kernel_details_csv",
             "rank_dir": item.get("rank_dir"),
             "csv_candidates": item.get("csv_candidates"),
             "limitations": item.get("limitations")}
            for item in facts if not item.get("kernel_details")
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
            "native observations: requested rank not found in inventory; "
            "available=" + ",".join(str(item.get("rank_id")) for item in facts))
    available = [item for item in chosen if item["kernel_details"]]
    missing = [item for item in chosen if not item["kernel_details"]]
    if not available:
        raise ProfilerUsageError(
            "native observations: no kernel_details.csv for requested rank scope; "
            "available=" + ",".join(str(item.get("rank_id")) for item in facts))
    if missing:
        raise ProfilerUsageError(
            "native observations: sibling rank has no kernel_details source; "
            "missing=" + ",".join(str(item.get("rank_id")) for item in missing)
            + "; candidates=" + json.dumps(discovery["ranks"], sort_keys=True))
    if len(available) > 1:
        raise ProfilerUsageError(
            "native observations: multiple ranks have kernel_details.csv; pass --rank; "
            + json.dumps(discovery["ranks"], sort_keys=True))
    candidates = available[0]["kernel_details"]
    if len(candidates) != 1:
        raise ProfilerUsageError(
            "native observations: rank has multiple kernel_details.csv candidates; "
            "pass the explicit file: " + ", ".join(candidates))
    discovery["selected_rank"] = available[0]["rank_id"]
    discovery["selected_path"] = candidates[0]
    return Path(candidates[0]), discovery

_NATIVE_EXECUTION_CORES = {
    "AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "MIX_AIV", "AI_CPU", "AICPU",
    "COMMUNICATION", "HCCL",
}

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
    conditions: Mapping[str, Any] | None, *,
    hardware: str | None, phase: str | None, model: str | None,
    quant: str | None, deployment_image_id: str | None,
    execution: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, list[str]], list[dict[str, Any]],
           list[dict[str, Any]]]:
    """Merge declared conditions and explicit arguments without losing sources.

    Every key (including any new key and an explicit ``null``) is retained.
    Conflicting values from the two declaration sources remain named in
    ``condition_conflicts`` instead of being silently overwritten; the explicit
    argument value remains the effective declaration for downstream consumers.
    """
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
        "hardware": hardware, "phase": phase, "model": model, "quant": quant,
        "deployment_image_id": deployment_image_id,
    }
    for key, value in explicit.items():
        if value is None or not str(value).strip():
            continue
        value = str(value).strip()
        if key in result and _canonical_json(result[key]) != _canonical_json(value):
            conflicts.append({
                "field": key, "values": [result[key], value],
                "sources": [*sources.get(key, ()), f"export.argument.{key}"],
            })
        result[key] = value
        sources[key] = [f"export.argument.{key}"]
    if execution is not None:
        if not isinstance(execution, Mapping):
            raise ProfilerUsageError("native execution conditions must be a mapping")
        execution = dict(execution)
        if ("execution" in result
                and _canonical_json(result["execution"]) != _canonical_json(execution)):
            conflicts.append({
                "field": "execution", "values": [result["execution"], execution],
                "sources": [*sources.get("execution", ()),
                            "export.argument.execution"],
            })
        result["execution"] = execution
        sources["execution"] = ["export.argument.execution"]
    found = _native_timing_path(result, "conditions")
    if found:
        raise ProfilerUsageError(
            f"native conditions must not contain target timing: {found}")
    try:
        _canonical_json(result)
    except (TypeError, ValueError) as exc:
        raise ProfilerUsageError(f"native conditions are not JSON-canonical: {exc}") from exc
    gaps = [
        {"field": field, "reason": "not_declared"}
        for field in ("hardware",)
        if field not in result or not isinstance(result.get(field), str)
        or not result[field].strip()
    ]
    return result, sources, gaps, conflicts

def _native_request_identity(boundary: Mapping[str, Any], abi: Mapping[str, Any],
                             conditions: Mapping[str, Any], occurrence: Mapping[str, Any],
                             clock: Mapping[str, Any], window_id: str | None,
                             *, condition_gaps: Sequence[Mapping[str, Any]] = (),
                             condition_conflicts: Sequence[Mapping[str, Any]] = (),
                             ) -> dict[str, Any]:
    fusion = boundary.get("fusion") if isinstance(boundary.get("fusion"), Mapping) else {}
    identity = {
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
    return identity

def native_prediction_requests(
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Project observations into timing-free requests for an independent native entry."""
    observations = (
        list(source.get("observations", ())) if isinstance(source, Mapping)
        else list(source)
    )
    requests, seen = [], {}
    # The captured launch grid is declared launch metadata, not timing.  It is
    # carried only when every observation of one request agrees on it, so the
    # request identity stays single-valued.
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
            "condition_conflicts": list(
                observation.get("condition_conflicts") or ()),
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
                f"native prediction request would leak target timing: {found}")
        payload = _canonical_json(request)
        if request_id not in seen:
            seen[request_id] = payload
            requests.append(request)
        elif seen[request_id] != payload:
            raise ProfilerUsageError(
                f"conflicting native request identity: {request_id}")
    report = {
        "schema": NATIVE_REQUEST_SCHEMA,
        "requests": requests,
        "counts": {"requests": len(requests), "observations": len(observations)},
        "excluded_fields": [
            "timing.duration_ms", "timing.duration_ns", "occurrence.start_ns",
            "occurrence.end_ns", "occurrence.event_id", "evidence.pipe_times_us",
        ],
        "interpretation": (
            "Only ABI and declared conditions are exposed. Observed durations stay "
            "in the profiler observation report and cannot flow into prediction."
        ),
    }
    if isinstance(source, Mapping) and source.get("source_identity"):
        report["source_identity"] = dict(source["source_identity"])
    return report

_T12_CONDITION_KEYS = {
    "variant", "owner", "members", "layer", "sequence_rows",
    "sequence_ranks", "phase",
}

def _native_request_condition_parts(
    request: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, list[str]],
           list[dict[str, Any]]]:
    """Split request-level and condition-level declarations without loss.

    ``api``/``version``/``attrs`` are accepted either as top-level fields or as
    keys inside the exported ``conditions`` mapping.  Both forms retain their
    source; a disagreement remains in ``condition_conflicts`` instead of being
    resolved by last-wins.
    """
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
                if (key in merged
                        and _canonical_json(merged[key]) != _canonical_json(value)):
                    conflicts.append({
                        "field": f"{name}.{key}",
                        "values": [merged[key], value],
                        "sources": [f"request.conditions.{name}",
                                    f"request.{name}"],
                    })
                merged[key] = value
            parts[name] = merged
            sources[name] = [f"request.conditions.{name}", f"request.{name}"]
        elif top is not None:
            if (nested is not None
                    and _canonical_json(top) != _canonical_json(nested)):
                conflicts.append({
                    "field": name, "values": [nested, top],
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
            "entry": value, "aclnn_symbol": value,
        }
    return {}

def _native_merge_explicit_invocation(
    explicit: Mapping[str, Any],
    parts: Mapping[str, Any],
    conditions: Mapping[str, Any],
    sources: Mapping[str, list[str]],
    conflicts: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Merge a complete explicit invocation with request declarations.

    The explicit invocation remains the actual declaration.  Missing
    API/version/attrs/conditions are filled from the request so the same facts
    reach ``mindie-sim`` native-call normalization; disagreements are retained.
    """
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
                    "field": name, "values": [declared, actual],
                    "sources": [*sources.get(name, ()),
                                f"t12_invocation.{name}"],
                })
            meta_sources[name] = [f"t12_invocation.{name}"]
        elif actual is not None:
            meta_sources[name] = [f"t12_invocation.{name}"]
    raw_conditions = invocation.get("conditions")
    explicit_conditions = dict(raw_conditions) if isinstance(raw_conditions, Mapping) else {}
    request_conditions = dict(conditions)
    merged_conditions = dict(request_conditions)
    for key, value in explicit_conditions.items():
        key = str(key)
        if (key in merged_conditions
                and _canonical_json(merged_conditions[key]) != _canonical_json(value)):
            conflicts.append({
                "field": key, "values": [merged_conditions[key], value],
                "sources": [*sources.get(key, ("request.conditions",)),
                            "t12_invocation.conditions"],
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
        "sources": meta_sources, "conflicts": conflicts,
        "t12_condition_keys": list(
            (invocation.get("conditions") or {}).keys()),
    }

def _qbmm_w8a8_invocation(
    abi: Mapping[str, Any], *,
    version: Mapping[str, Any] | None = None,
    attrs: Mapping[str, Any] | None = None,
    conditions: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a real 4-slot W8A8 QuantBatchMatmul ABI to a declared invocation.

    Slot order is x, weight (logical or FRACTAL_NZ storage), weight_scale and
    pertoken_scale, then output.  Storage shapes/dtypes/layouts are preserved;
    no MXFP8 block scale, bias, dtype or source revision is invented.
    """
    inputs, outputs = list(abi.get("inputs") or ()), list(abi.get("outputs") or ())
    if len(inputs) != 4 or len(outputs) != 1:
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
            "role": role, "present": present,
            "dtype_present": bool(row.get("dtype")) if present else False,
            "layout_present": bool(row.get("layout")) if present else False,
        }

    weight_name = ("weight_nz" if str(weight.get("layout") or "").upper()
                   == "FRACTAL_NZ" else "weight")
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
        "api": {"namespace": "aclnn",
                "entry": "aclnnQuantMatmulWeightNz",
                "aclnn_symbol": "aclnnQuantMatmulWeightNz"},
        "version": dict(version or {}),
        "tensors": tensors,
        "attrs": actual_attrs,
        "conditions": dict(conditions or {}),
    }


def _qbmm_t12_invocation(
    request: Mapping[str, Any], *,
    source_revision: str | None,
    parts: Mapping[str, Any],
    conditions: Mapping[str, Any],
    sources: Mapping[str, list[str]],
    conflicts: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None, dict[str, Any]]:
    """Map the 4-slot QuantBatchMatmul ABI to its ``mindie-sim`` native leaf.

    W8A8 delegates to ``mindie-sim``'s public QBMM helper and restores the declared API, so an
    explicit ``torch_npu.npu_quant_matmul`` request keeps the torch namespace
    and the ND tensor name ``weight``, while an ACLNN WeightNZ declaration keeps
    its actual entry and ``weight_nz`` representation.  The MXFP8 branch keeps
    the existing logical-weight mapping.  Version/API facts are passed through
    only when declared; no directory image or vLLM source revision is invented.
    """
    meta = {"sources": dict(sources), "conflicts": conflicts,
            "t12_condition_keys": list(conditions)}
    abi = request.get("abi")
    if not isinstance(abi, Mapping):
        return None, "t12_invocation_unavailable:qbmm_abi_missing", meta
    inputs, outputs = list(abi.get("inputs") or ()), list(abi.get("outputs") or ())
    if len(inputs) != 4 or len(outputs) != 1:
        return None, "t12_invocation_unavailable:qbmm_slot_count", meta
    raw_version = parts.get("version")
    if isinstance(raw_version, Mapping):
        version = dict(raw_version)
    elif isinstance(raw_version, str) and raw_version:
        version = {"api": raw_version}
    else:
        version = {}
    actual_source = (
        source_revision or version.get("source")
        or version.get("source_revision") or version.get("revision")
        or request.get("source_revision")
    )
    attrs = dict(parts.get("attrs") or {}) if isinstance(
        parts.get("attrs"), Mapping) else {}
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
                abi, version=version, attrs=attrs, conditions=conditions)
            if declared_api:
                invocation["api"] = declared_api
                meta["sources"]["api"] = list(
                    sources.get("api", ["request.conditions.api"]))
            return invocation, None, meta
        except TimeoutError:
            raise
        except Exception as exc:
            return None, ("t12_invocation_unavailable:qbmm_w8a8:"
                          + type(exc).__name__ + ":" + str(exc)), meta
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
    weight_transposed = False
    if len(device_shape) == 4:
        n, k2 = device_shape[0] * device_shape[3], device_shape[1] * device_shape[2]
    elif len(device_shape) == 2:
        # ND weight storage may be [k, n] or the transposed [n, k]; the
        # declared output closes exactly one of the two orientations.
        if device_shape[1] == k and output_shape == [m, device_shape[1]]:
            k2, n = device_shape
        elif device_shape[0] == k and output_shape == [m, device_shape[0]]:
            n, k2 = device_shape
            weight_transposed = True
        elif device_shape[0] == k:
            k2, n = device_shape
        elif device_shape[1] == k:
            n, k2 = device_shape
            weight_transposed = True
        else:
            return None, "t12_invocation_unavailable:qbmm_weight_layout", meta
    else:
        return None, "t12_invocation_unavailable:qbmm_weight_layout", meta
    if k2 != k or output_shape != [m, n]:
        return None, "t12_invocation_unavailable:qbmm_geometry", meta
    pairs = ((k + 31) // 32 + 1) // 2
    scale_layout = "pairs_first"
    if scale_shape == [n, pairs, 2]:
        scale_layout = "n_first"
    elif scale_shape != [pairs, n, 2]:
        return None, "t12_invocation_unavailable:qbmm_scale_geometry", meta
    if pertoken_shape != [m, pairs, 2]:
        return None, "t12_invocation_unavailable:qbmm_scale_geometry", meta
    # The container image / source revision is optional identity, not a
    # physical input: a standalone timing-free CSV ABI without a declared
    # source still has complete geometry, scale and output slots.

    def tensor(slot, shape, dtype, layout, role):
        return {"shape": list(shape), "dtype": dtype, "layout": layout,
                "role": role, "present": True,
                "dtype_present": True, "layout_present": True}

    tensors = {
        "x": tensor(x, [m, k], x.get("dtype"), "ND", "input"),
        "weight": tensor(legacy_weight, [k, n], legacy_weight.get("dtype"),
                         "ND", "weight"),
        "weight_scale": tensor(legacy_weight_scale, [pairs, n, 2],
                               "uint8", "ND", "scale"),
        "pertoken_scale": tensor(pertoken, pertoken_shape,
                                 pertoken.get("dtype"), "ND", "scale"),
        "output": tensor(output, [m, n], output.get("dtype"), "ND", "output"),
    }
    actual_version = dict(version)
    if actual_source:
        actual_version.setdefault("source", actual_source)
    physical_w_layout = (
        "FRACTAL_NZ"
        if len(device_shape) == 4
        or str(legacy_weight.get("layout") or "").upper() == "FRACTAL_NZ"
        else "ND"
    )
    actual_attrs = {
        "group_size": 32, "output_dtype": "bf16", "scale_group": 32,
        "weight_scale_storage_format": "fp8_e8m0",
        "weight_scale_storage_bytes": 1, "weight_layout": physical_w_layout,
        **attrs,
    }
    api = declared_api or {
        "namespace": "torch", "entry": "torch_npu.npu_quant_matmul"}
    return {
        "api": api,
        "version": actual_version,
        "tensors": tensors,
        "attrs": actual_attrs,
        "conditions": dict(conditions),
    }, None, meta
