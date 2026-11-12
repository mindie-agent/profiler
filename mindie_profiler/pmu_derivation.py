"""Source-backed, full-event-only TASK_PMU derivation.

[Role]
  Map actual TASK_PMU_INFO/kernel_details metrics to canonical units and derive
  descriptive pipe-time fractions, ratio/time consistency, dominant measured
  pipes, official msprof-analyze cube/vector candidate rules, and one reusable
  full-grid/tail matrix-pipe service pair for the normal sim service interface.

[Invariants]
  * Raw ``*_ratio`` values are fractions of the corresponding AIC/AIV total
    time, never wall-clock utilization or causal proof.  Pipe fractions may
    overlap and can sum above 1; they are not normalised.
  * A measured service rate is issued work / measured active-pipe time, never
    issued work / elapsed kernel duration.  Full/tail selection requires the
    observed active-owner count and raw pipe ratio; an unknown owner, shape or
    counter stays unknown and is not substituted.
  * A rule candidate is emitted only when every required actual metric exists;
    it is a heuristic candidate from the pinned official rule table, not a
    confirmed root cause.
  * ``cube_utilization_pct`` is a separate CSV percent metric; it is never
    derived from ``aic_mac_ratio``.
  * PMU values are full-event counters.  Clipped events retain full counters
    but their derived evidence is explicitly not usable for clipped-window
    inference.
  * Missing metrics/units stay absent/unknown; no fabricated values.

[Timeouts & Locks]
  Pure in-memory mapping and arithmetic; no I/O after the one cached mapping
  read.

[Side-Effect Policy]
  No file writes, network, or source mutation.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from functools import lru_cache
from typing import Any, Mapping, Sequence

from .sources_db import load_mapping

PMU_ANALYSIS_SCHEMA = "mindie-pmu-derived/1"
MEASURED_SUPPLY_SCHEMA = "mindie-profiler-measured-supply/1"
DUAL_LOAD_SCHEMA = "mindie-profiler-dual-load/1"
MEASURED_SUPPLY_SCOPE = "matrix_pipe_service"
SATURATION_THRESHOLD = 0.90
RULE_SOURCE = "msprof-analyze/advisor/rules/en/aicore_performance.yaml"
RULE_SOURCE_PATH = "msprof_analyze/advisor/rules/en/aicore_performance.yaml"
RULE_SOURCE_VERSION = "26.1.0"
RULE_SOURCE_COMMIT = "639eb8702c1884813dfab59ddb371f7838caab6d"

_AIC_PIPES = ("mac", "scalar", "mte1", "mte2", "fixpipe")
_AIV_PIPES = ("vec", "scalar", "mte2", "mte3", "mac")
_CUBE_REQUIRED = ("aic_mac_ratio", "aic_mte2_ratio")
_VECTOR_REQUIRED = ("aiv_vec_ratio", "aiv_mte2_ratio", "aiv_mte3_ratio")


@lru_cache(maxsize=1)
def _mapping() -> dict[str, Any]:
    return dict(load_mapping())


def metric_units(metrics: Mapping[str, float]) -> dict[str, str]:
    specs = _mapping().get("pmu_metrics", {})
    return {
        name: (str(specs.get(name, {}).get("unit")) if specs.get(name, {}).get("unit") else "unknown")
        for name in sorted(metrics)
    }


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _number(metrics: Mapping[str, float], name: str) -> float | None:
    value = metrics.get(name)
    return float(value) if _finite(value) else None


def _scope_evidence(
    metrics: Mapping[str, float], prefix: str, pipes: tuple[str, ...],
    export_resolution: Mapping[str, float],
) -> dict[str, Any]:
    total_time = _number(metrics, f"{prefix}_total_time")
    total_cycles = _number(metrics, f"{prefix}_total_cycles")
    checks: list[dict[str, Any]] = []
    fractions: dict[str, float] = {}
    for pipe in pipes:
        ratio = _number(metrics, f"{prefix}_{pipe}_ratio")
        pipe_time = _number(metrics, f"{prefix}_{pipe}_time")
        if ratio is None or total_time is None:
            continue
        fractions[pipe] = ratio
        if pipe_time is None:
            checks.append({"pipe": pipe, "status": "time_missing"})
            continue
        expected = ratio * total_time
        residual = expected - pipe_time
        tolerance = max(1e-6, abs(pipe_time) * 1e-6)
        resolution_names = (f"{prefix}_{pipe}_ratio", f"{prefix}_total_time", f"{prefix}_{pipe}_time")
        resolution = [_number(export_resolution, name) for name in resolution_names]
        envelope = None
        if all(value is not None for value in resolution):
            ratio_unit, total_unit, pipe_unit = resolution
            # One displayed unit permits either rounding or truncation. This
            # bounds representation differences, not hardware measurement error.
            envelope = abs(total_time) * ratio_unit + abs(ratio) * total_unit + ratio_unit * total_unit + pipe_unit
        if abs(residual) <= tolerance:
            status = "consistent"
        elif envelope is not None and abs(residual) <= envelope:
            status = "compatible_with_export_precision"
        else:
            status = "inconsistent"
        checks.append(
            {
                "pipe": pipe,
                "ratio": ratio,
                "pipe_time_ns": pipe_time,
                "expected_time_ns": expected,
                "residual_ns": residual,
                "status": status,
                "export_precision_envelope_ns": envelope,
                "export_precision_policy": "one_display_unit_per_factor" if envelope is not None else None,
            }
        )
    dominant = None
    if fractions:
        name, value = max(fractions.items(), key=lambda item: (item[1], item[0]))
        dominant = {"pipe": name, "time_fraction": value}
    return {
        "total_time_ns": total_time,
        "total_cycles": total_cycles,
        "pipe_time_fractions": fractions,
        "sum_pipe_time_fractions": (sum(fractions.values()) if fractions else None),
        "fractions_overlap": (sum(fractions.values()) > 1.0 + 1e-9) if fractions else None,
        "ratio_time_consistency": checks,
        "ratio_time_all_consistent": (
            False if any(item["status"] == "inconsistent" for item in checks)
            else True if checks and all(item["status"] == "consistent" for item in checks)
            else None
        ),
        "dominant_pipe_by_time": dominant,
    }


def _frequency(total_time: float | None, total_cycles: float | None, block_num: int | None) -> dict[str, Any]:
    if total_time is None or total_cycles is None:
        return {"status": "not_available", "reason": "time_or_cycles_missing"}
    if total_time <= 0:
        return {"status": "not_available", "reason": "no_active_time"}
    if block_num is None or block_num <= 0:
        return {"status": "not_available", "reason": "block_num_missing"}
    return {
        "status": "inferred",
        "hz": total_cycles / (total_time * block_num) * 1e9,
        "basis": "total_cycles / (total_time_ns * block_num)",
        "scope_note": "inferred per-block relation; not generalized across A2/A3 core types",
    }


def _rule_meta(role: str, thresholds: Mapping[str, float]) -> dict[str, Any]:
    return {
        "role": role,
        "thresholds": dict(thresholds),
        "source": RULE_SOURCE,
        "source_path": RULE_SOURCE_PATH,
        "source_version": RULE_SOURCE_VERSION,
        "source_commit": RULE_SOURCE_COMMIT,
        "source_url": f"https://gitcode.com/Ascend/msprof-analyze/blob/{RULE_SOURCE_COMMIT}/{RULE_SOURCE_PATH}",
        "interpretation": "per_event_thresholds_from_rule_table",
        "upstream_implementation_reproduced": False,
        "confidence": "heuristic_candidate",
        "causal": False,
    }


def _cube_rule(metrics: Mapping[str, float], role: str | None) -> dict[str, Any]:
    if role not in {"aic", "mixed"}:
        return {
            "status": "not_applicable",
            "reason": "not_an_ai_core_event",
            "matched": False,
            "candidate_bound": None,
            "causal": False,
        }
    missing = [name for name in _CUBE_REQUIRED if _number(metrics, name) is None]
    if missing:
        return {
            "status": "metric_missing",
            "missing": missing,
            "required": list(_CUBE_REQUIRED),
            "matched": False,
            "candidate_bound": None,
            "causal": False,
        }
    mac = float(metrics["aic_mac_ratio"])
    mte2 = float(metrics["aic_mte2_ratio"])
    meta = _rule_meta("cube", {"aic_mac_ratio": 0.8, "aic_mte2_ratio": 0.95})
    matched = mac >= 0.8 or mte2 >= 0.95
    bound = None
    if mac >= 0.8 and mte2 >= 0.95:
        bound = "mac_and_mte2_bound"
    elif mac >= 0.8:
        bound = "mac_bound"
    elif mte2 >= 0.95:
        bound = "mte2_bound"
    return {**meta, "status": "available", "matched": matched, "candidate_bound": bound, "metrics": {"aic_mac_ratio": mac, "aic_mte2_ratio": mte2}}


def _vector_rule(metrics: Mapping[str, float], role: str | None) -> dict[str, Any]:
    if role not in {"aiv", "mixed"}:
        return {
            "status": "not_applicable",
            "reason": "not_an_ai_vector_event",
            "matched": False,
            "candidate_bound": None,
            "causal": False,
        }
    missing = [name for name in _VECTOR_REQUIRED if _number(metrics, name) is None]
    if missing:
        return {
            "status": "metric_missing",
            "missing": missing,
            "required": list(_VECTOR_REQUIRED),
            "matched": False,
            "candidate_bound": None,
            "causal": False,
        }
    vec = float(metrics["aiv_vec_ratio"])
    mte2 = float(metrics["aiv_mte2_ratio"])
    mte3 = float(metrics["aiv_mte3_ratio"])
    total = vec + mte2 + mte3
    meta = _rule_meta("vector", {"vec_plus_mte2_plus_mte3": 0.9, "individual": 0.7})
    matched = total >= 0.9 or max(vec, mte2, mte3) >= 0.7
    bound = None
    if total >= 0.9:
        bound = "vec_mte2_mte3_bound"
    elif vec >= 0.7:
        bound = "vec_bound"
    elif mte2 >= 0.7:
        bound = "mte2_bound"
    elif mte3 >= 0.7:
        bound = "mte3_bound"
    return {
        **meta,
        "status": "available",
        "matched": matched,
        "candidate_bound": bound,
        "metrics": {"aiv_vec_ratio": vec, "aiv_mte2_ratio": mte2, "aiv_mte3_ratio": mte3, "vec_plus_mte2_plus_mte3": total},
    }


def derive_pmu_evidence(
    metrics: Mapping[str, float],
    *,
    task_type: str | None = None,
    core: str | None = None,
    complete_in_window: bool,
    source: str | None = None,
    block_num: int | None = None,
    export_resolution: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """Return units, fractions, consistency, rules, and explicit scope."""
    folded = f"{task_type or ''} {core or ''}".upper()
    textual_role = None
    if "VECTOR" in folded or "AIV" in folded:
        textual_role = "aiv"
    elif "CORE" in folded or "AIC" in folded or "CUBE" in folded:
        textual_role = "aic"
    units = metric_units(metrics)
    aic = _scope_evidence(metrics, "aic", _AIC_PIPES, export_resolution or {})
    aiv = _scope_evidence(metrics, "aiv", _AIV_PIPES, export_resolution or {})
    aic_active = bool(aic.get("total_time_ns") and aic["total_time_ns"] > 0) or any(
        value > 0 for value in (aic.get("pipe_time_fractions") or {}).values()
    )
    aiv_active = bool(aiv.get("total_time_ns") and aiv["total_time_ns"] > 0) or any(
        value > 0 for value in (aiv.get("pipe_time_fractions") or {}).values()
    )
    if aic_active and aiv_active:
        role = "mixed"
    elif aiv_active:
        role = "aiv"
    elif aic_active:
        role = "aic"
    else:
        role = textual_role
    for scope, prefix in ((aic, "aic"), (aiv, "aiv")):
        scope["frequency"] = _frequency(
            scope.get("total_time_ns"),
            scope.get("total_cycles"),
            block_num,
        )
    cube = _cube_rule(metrics, role)
    vector = _vector_rule(metrics, role)
    cube_pct = _number(metrics, "cube_utilization_pct")
    return {
        "schema_version": PMU_ANALYSIS_SCHEMA,
        "attribution": "rule_candidate_not_root_cause",
        "causal": False,
        "task_role": role,
        "metric_units": units,
        "unmapped_metrics": sorted(name for name, unit in units.items() if unit == "unknown"),
        "scope": {
            "kind": "full_event",
            "source": source,
            "complete_in_window": bool(complete_in_window),
            "usable_for_clipped_window": bool(complete_in_window),
            "derived_for_clipped_window": bool(complete_in_window),
        },
        "aic": aic,
        "aiv": aiv,
        "cube_rule": cube,
        "vector_rule": vector,
        "cube_utilization_pct": {
            "value": cube_pct,
            "unit": "percent",
            "status": "present" if cube_pct is not None else "absent",
            "reason": None if cube_pct is not None else "not_exported_in_db",
            "not_equivalent_to": "aic_mac_ratio",
            "source": "kernel_details.csv:cube_utilization(%)" if cube_pct is not None else None,
        },
    }


_DTYPE_ALIASES = {
    "bfloat16": "bf16", "bf16": "bf16", "float16": "fp16", "fp16": "fp16",
    "float32": "fp32", "fp32": "fp32", "int8": "int8", "int32": "int32",
    "float8_e4m3fn": "fp8_e4m3", "fp8_e4m3": "fp8_e4m3",
    "float8_e5m2": "fp8_e5m2", "fp8_e5m2": "fp8_e5m2",
    "float8_e8m0": "fp8_e8m0", "fp8_e8m0": "fp8_e8m0",
    "uint8": "uint8", "int4": "int4",
}


R64_IMAGE_SHA = "8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
R35_IMAGE_SHA = "5461a1a8253c6dc07868956166ad94751f84c82d00ff7791c59a9c1ac497de06"


def image_digest(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text.startswith("sha256:"):
        text = text.split(":", 1)[1]
    return text


def deployment_source_identity(image_id: Any = None, *, basis: str = "absent") -> dict[str, Any]:
    """Classify only the declared deployment image, never a path or shape."""
    digest = image_digest(image_id)
    if not digest:
        return {"source_scope": "absent", "image_digest": None, "basis": basis}
    if digest.startswith(R64_IMAGE_SHA):
        scope = "r64"
    elif digest.startswith(R35_IMAGE_SHA):
        scope = "r35"
    else:
        scope = "unpinned"
    return {"source_scope": scope, "image_digest": digest, "basis": basis}


_QBMM_ISSUE_RULE = {
    "native_type": "QuantBatchMatmulV3",
    "dtype": "fp8_e4m3",
    "output_dtype": "bf16",
    "m_alignment": 16,
    "alignment_basis": "physical_tile_m16_not_logical_m",
    "source_path": "cann/op_kernel/quant_batch_matmul_v3/arch35/quant_batch_matmul_v3.cpp",
    "source_sha256": "13daf996890d70e7b1dc9275ab3a464043860e67d6df730e28742393c023ec88",
    "source_revision": "cann-9.2.1-r64",
    "weight_layout": "FRACTAL_NZ",
    "wrapper_source_path": "vllm_ascend/quantization/methods/w8a8/w8a8_mxfp8.py",
    "wrapper_source_sha256": "38de2275cf33ced653b8398e98a07f483489dc8e7353b2b3c238a5ff00782f79",
    "wrapper_source_revision": "r64/8d422528",
    "wrapper_symbol": "AscendW8A8MXFP8DynamicLinearMethod.apply",
    "scope": "matching_r64_qbmm_variant_only",
}


def _issue_rule(native_type: Any, dtype: Any, output_dtype: Any, n: Any, k: Any,
                *, input_formats: Any = None, output_formats: Any = None,
                source: Mapping[str, Any] | None = None) -> dict[str, Any] | None:
    """Return issued math only for the actual source-certified R64 QBMM.

    Shape, dtype and K/N divisibility are necessary but never sufficient: the
    capture must carry the R64 deployment image and the true WeightNz layout.
    R35, bare and foreign captures keep logical/generic work.
    """
    base = dict(_QBMM_ISSUE_RULE)
    if not source or source.get("source_scope") != "r64":
        return None
    if source.get("image_digest") != R64_IMAGE_SHA:
        return None
    formats = [part.strip().upper() for part in str(input_formats or "").strip('"').split(";")]
    if formats[:4] != ["ND", "FRACTAL_NZ", "ND", "ND"]:
        return None
    outputs = [part.strip().upper() for part in str(output_formats or "").strip('"').split(";")]
    if outputs and outputs[0] != "ND":
        return None
    if (native_type == base["native_type"] and dtype == base["dtype"]
            and output_dtype == base["output_dtype"]
            and isinstance(n, int) and isinstance(k, int) and n > 0 and k > 0
            and n % base["m_alignment"] == 0 and k % base["m_alignment"] == 0):
        return {**base, "deployment_image_id": source["image_digest"],
                "source_scope": source["source_scope"],
                "source_basis": source.get("basis")}
    return None


def _issued_flops(logical_flops: int | None, m: int | None, issue: Mapping[str, Any] | None) -> int | None:
    if logical_flops is None or m is None or issue is None:
        return None
    alignment = int(issue["m_alignment"])
    if alignment < 1 or m < 1:
        return None
    aligned_m = ((m + alignment - 1) // alignment) * alignment
    return int(logical_flops) // m * aligned_m


def _tensor_rows(value: Any, limit: int = 2) -> tuple[tuple[int, ...], ...]:
    """Parse a captured ``"m,k;..."`` shape string without inventing dims."""
    text = str(value or "").strip().strip('"')
    if not text:
        return ()
    rows: list[tuple[int, ...]] = []
    for raw in text.split(";"):
        cell = raw.strip().strip('"')
        if not cell:
            continue
        try:
            dims = tuple(int(part.strip()) for part in cell.split(","))
        except ValueError:
            return ()
        if not dims or any(dim < 0 for dim in dims):
            return ()
        rows.append(dims)
        if len(rows) >= limit:
            break
    return tuple(rows)


def _dtype_name(value: Any) -> str | None:
    first = str(value or "").split(";")[0].strip()
    if not first:
        return None
    key = first.removeprefix("DT_").lower()
    return _DTYPE_ALIASES.get(key, key or None)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _metric(metrics: Mapping[str, float], name: str) -> float | None:
    return _number(metrics, name)


def _pipe_evidence(metrics: Mapping[str, float]) -> tuple[dict[str, float], dict[str, float], str | None]:
    """Return the raw per-pipe times/ratios and the highest measured ratio."""
    times: dict[str, float] = {}
    ratios: dict[str, float] = {}
    for scope, pipes in (("aic", _AIC_PIPES), ("aiv", _AIV_PIPES)):
        for pipe in pipes:
            time = _metric(metrics, f"{scope}_{pipe}_time")
            ratio = _metric(metrics, f"{scope}_{pipe}_ratio")
            if time is not None:
                times[f"{scope}_{pipe}_time"] = time
            if ratio is not None:
                ratios[f"{scope}_{pipe}_ratio"] = ratio
    limiting = None
    if ratios:
        limiting = max(ratios.items(), key=lambda item: (item[1], item[0]))[0]
    return times, ratios, limiting


def derive_measured_supply(
    metrics: Mapping[str, float],
    *,
    input_shapes: Any,
    input_dtypes: Any,
    output_shapes: Any,
    output_dtypes: Any,
    block_num: int | None,
    mix_block_num: int | None = None,
    complete_in_window: bool,
    source: str | None = None,
    source_sha256: str | None = None,
    source_schema: str | None = None,
    event_id: str | None = None,
    row_index: int | None = None,
    observation_id: str | None = None,
    native_call: str | None = None,
    native_type: str | None = None,
    device_id: str | None = None,
    rank_id: str | None = None,
    rank_index: int | None = None,
    duration_ns: int | None = None,
    input_formats: Any = None,
    output_formats: Any = None,
    source_identity: Mapping[str, Any] | None = None,
    physical_owners: int | None = None,
    saturation_threshold: float = SATURATION_THRESHOLD,
) -> dict[str, Any]:
    """Derive one measured matrix-pipe service observation from raw counters.

    ``rate_flops_per_s`` is whole-pipe issued FLOPs / measured MAC active time;
    ``per_owner_rate_flops_per_s`` divides by active owners.  Elapsed kernel
    duration is retained as provenance and is never used as the rate numerator.
    """
    inputs = _tensor_rows(input_shapes, limit=1)
    outputs = _tensor_rows(output_shapes, limit=1)
    reasons: list[str] = []
    m = k = n = None
    if len(inputs) == 1 and len(inputs[0]) >= 2:
        m, k = int(inputs[0][0]), int(inputs[0][1])
    else:
        reasons.append("input_matrix_shape_not_parsed")
    if len(outputs) == 1 and len(outputs[0]) >= 2:
        out_m, n = int(outputs[0][0]), int(outputs[0][1])
        if m is not None and out_m != m:
            reasons.append("input_output_m_mismatch")
    else:
        reasons.append("output_matrix_shape_not_parsed")
    dtype = _dtype_name(input_dtypes)
    output_dtype = _dtype_name(output_dtypes)
    if dtype is None:
        reasons.append("input_dtype_not_parsed")
    active_owners = _positive_int(block_num)
    if active_owners is None:
        reasons.append("block_num_missing")
    physical_owners = _positive_int(physical_owners)
    if physical_owners is None:
        reasons.append("physical_owners_not_declared")
    logical_flops = (
        2 * m * n * k
        if all(isinstance(value, int) and value > 0 for value in (m, n, k))
        else None
    )
    issue = _issue_rule(native_type, dtype, output_dtype, n, k,
                        input_formats=input_formats, output_formats=output_formats,
                        source=source_identity)
    issued_flops = _issued_flops(logical_flops, m, issue)
    if logical_flops is None:
        reasons.append("logical_flops_not_available")
    if issue is not None and issued_flops is None:
        reasons.append("issued_flops_not_available")
    if issue is None:
        issued_flops = logical_flops
        work_basis = "logical_2_m_n_k_flops_no_issue_rule"
    else:
        work_basis = "issued_2_align_m_k_n_flops"
    if issued_flops is None:
        reasons.append("issued_flops_not_available")
    times, ratios, limiting = _pipe_evidence(metrics)
    mac_time_ns = times.get("aic_mac_time")
    mac_ratio = ratios.get("aic_mac_ratio")
    if mac_time_ns is None:
        reasons.append("aic_mac_time_missing")
    if mac_ratio is None:
        reasons.append("aic_mac_ratio_missing")
    rate = per_owner_rate = logical_rate = None
    if issued_flops is not None and active_owners and mac_time_ns and mac_time_ns > 0:
        rate = issued_flops / (mac_time_ns * 1e-9)
        per_owner_rate = rate / active_owners
        if logical_flops is not None:
            logical_rate = logical_flops / (mac_time_ns * 1e-9)
    if rate is None:
        reasons.append("measured_rate_not_available")
    saturated = None
    if physical_owners and active_owners and mac_ratio is not None:
        saturated = bool(active_owners == physical_owners and mac_ratio >= saturation_threshold)
    status = "measured" if rate is not None and active_owners else "unknown"
    cube_utilization = _metric(metrics, "cube_utilization_pct")
    return {
        "schema_version": MEASURED_SUPPLY_SCHEMA,
        "status": status,
        "scope": MEASURED_SUPPLY_SCOPE,
        "not_end_to_end_kernel_latency": True,
        "native_call": native_call,
        "native_type": native_type,
        "dtype": dtype,
        "output_dtype": output_dtype,
        "device_id": device_id,
        "rank_id": rank_id,
        "rank_index": rank_index,
        "m": m, "n": n, "k": k,
        "logical_flops": logical_flops,
        "issued_flops": issued_flops,
        "flops": issued_flops,
        "work_basis": work_basis,
        "issue": issue,
        "active_owners": active_owners,
        "block_num": active_owners,
        "mix_block_num": mix_block_num,
        "physical_owners": physical_owners,
        "limited_by": limiting,
        "pipe_times_ns": times,
        "pipe_ratios": ratios,
        "mac_ratio": mac_ratio,
        "cube_utilization_pct": cube_utilization,
        "saturation_threshold": saturation_threshold,
        "saturation_basis": "active_owners == physical_owners and aic_mac_ratio >= threshold",
        "limiting_pipe_basis": "highest measured AIC/AIV pipe ratio",
        "saturated": saturated,
        "rate_flops_per_s": rate,
        "per_owner_rate_flops_per_s": per_owner_rate,
        "logical_rate_flops_per_s": logical_rate,
        "rate_basis": "issued_flops / aic_mac_time_ns (whole matrix pipe); per_owner_rate divides by active_owners",
        "effective_rate_flops_per_s": (
            issued_flops / (duration_ns * 1e-9) if issued_flops and duration_ns else None),
        "duration_ns": duration_ns,
        "complete_in_window": bool(complete_in_window),
        "counter_status": "present" if not reasons else "unknown",
        "missing": reasons,
        "provenance": {
            "source": source,
            "source_sha256": source_sha256,
            "source_schema": source_schema,
            "event_id": event_id,
            "row_index": row_index,
            "observation_id": observation_id,
            "native_call": native_call,
            "native_type": native_type,
            "device_id": device_id,
            "rank_id": rank_id,
            "rank_index": rank_index,
            "input_shapes": str(input_shapes or ""),
            "input_dtypes": str(input_dtypes or ""),
            "input_formats": str(input_formats or ""),
            "output_shapes": str(output_shapes or ""),
            "output_dtypes": str(output_dtypes or ""),
            "output_formats": str(output_formats or ""),
            "source_identity": dict(source_identity) if source_identity else None,
            "logical_flops": logical_flops,
            "issued_flops": issued_flops,
            "issue_rule": issue,
            "metric_units": metric_units(metrics),
            "elapsed_duration_used_as_rate": False,
            "physical_owners_basis": (
                "declared_aic_count" if physical_owners else "not_declared"),
            "scope": "full_event_counters" if complete_in_window else "clipped_event_excluded",
        },
    }


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=str)


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _load_record(row: Mapping[str, Any], load_id: str) -> dict[str, Any]:
    return {
        "id": load_id,
        "active_owners": int(row["active_owners"]),
        "rate_flops_per_s": float(row["rate_flops_per_s"]),
        "measured_issued_flops": int(row["issued_flops"]),
        "measured_logical_flops": int(row["logical_flops"]),
        "event_count": int(row.get("event_count") or 1),
        "median_aic_mac_time_ns": row["pipe_times_ns"].get("aic_mac_time"),
        "median_aic_mac_ratio": row.get("mac_ratio"),
        "median_mte2_time_ns": row["pipe_times_ns"].get("aic_mte2_time"),
        "median_elapsed_ns": row.get("duration_ns"),
        "cube_utilization_pct": row.get("cube_utilization_pct"),
        "limiting_pipe": row.get("limited_by"),
        "provenance": row.get("provenance"),
    }


def build_dual_load_service(
    saturated: Mapping[str, Any],
    underfilled: Mapping[str, Any],
    *,
    physical_owners: int,
    recipe: str | None = None,
    kernel: str | None = None,
    hardware: str | None = None,
    saturation_threshold: float = SATURATION_THRESHOLD,
) -> dict[str, Any]:
    """Build the reusable dual-load record and normal MAC-service rule."""
    _require(saturated.get("status") == "measured", "measured_supply_saturated_unknown")
    _require(underfilled.get("status") == "measured", "measured_supply_underfilled_unknown")
    for field in ("native_type", "dtype", "output_dtype", "n", "k",
                  "device_id", "rank_id"):
        _require(saturated.get(field) == underfilled.get(field),
                 "measured_supply_identity_mismatch:" + field)
    _require(saturated.get("issue") is not None and underfilled.get("issue") is not None,
             "measured_supply_requires_certified_issue_rule")
    _require(saturated["issue"] == underfilled["issue"],
             "measured_supply_issue_rule_mismatch")
    _require(int(saturated["active_owners"]) == int(physical_owners),
             "measured_supply_saturated_not_full_grid")
    _require(int(underfilled["active_owners"]) < int(physical_owners),
             "measured_supply_underfilled_not_tail_grid")
    _require(int(saturated["active_owners"]) != int(underfilled["active_owners"]),
             "measured_supply_same_active_owners")
    full_mac, tail_mac = saturated.get("mac_ratio"), underfilled.get("mac_ratio")
    _require(isinstance(full_mac, (int, float)) and not isinstance(full_mac, bool),
             "measured_supply_saturated_mac_ratio_missing")
    _require(isinstance(tail_mac, (int, float)) and not isinstance(tail_mac, bool),
             "measured_supply_underfilled_mac_ratio_missing")
    _require(float(full_mac) >= saturation_threshold,
             "measured_supply_saturated_mac_ratio_below_threshold")
    _require(float(tail_mac) < saturation_threshold,
             "measured_supply_underfilled_mac_ratio_above_threshold")
    _require(float(saturated["rate_flops_per_s"]) > float(underfilled["rate_flops_per_s"]),
             "measured_supply_saturated_rate_not_greater")
    dtype = str(saturated["dtype"])
    issue = dict(saturated["issue"])
    n, k = int(saturated["n"]), int(saturated["k"])
    under_owners = int(underfilled["active_owners"])
    _require(n % under_owners == 0, "measured_supply_n_not_divisible_by_tail_owners")
    tile_n = n // under_owners
    n_tiles = n // tile_n
    full_owners = int(saturated["active_owners"])
    full_m = int(saturated["m"])
    tile_m = 128
    tile_k = 128
    identity = {
        "native_call": saturated.get("native_call"),
        "native_type": saturated.get("native_type"),
        "dtype": dtype,
        "output_dtype": saturated.get("output_dtype"),
        "n": n, "k": k,
        "device_id": saturated.get("device_id"),
        "rank_id": saturated.get("rank_id"),
        "physical_owners": int(physical_owners),
        "physical_owners_basis": saturated.get("provenance", {}).get(
            "physical_owners_basis", "declared_aic_count"),
        "issue_rule": issue,
    }
    loads = [
        _load_record(saturated, "saturated"),
        _load_record(underfilled, "underfilled"),
    ]
    match: dict[str, Any] = {"dtype": dtype}
    if recipe:
        match["recipe"] = recipe
    elif kernel:
        match["kernel"] = kernel
    else:
        match["kernel"] = saturated.get("native_type") or saturated.get("native_call")
    if hardware:
        match["hardware"] = hardware
    response = {
        "kind": "measured_dual_load",
        "fixed_us": 0.0,
        "resource": "cube",
        "dtype": dtype,
        "scope": MEASURED_SUPPLY_SCOPE,
        "issue": {
            **issue,
            "n": n, "k": k,
        },
        "owner_grid": {
            "tile_m": tile_m, "tile_n": tile_n, "cores": int(physical_owners),
        },
        "loads": loads,
    }
    rule = {
        "id": "measured-dual-load-" + hashlib.sha256(_canonical({
            "identity": identity,
            "loads": [{key: load[key] for key in (
                "id", "active_owners", "rate_flops_per_s",
                "measured_issued_flops")} for load in loads],
        }).encode()).hexdigest()[:16],
        "match": match,
        "coordinates": {
            "m": {"path": "local_shape.0"},
            "n": {"path": "local_shape.1"},
            "k": {"path": "local_shape.2"},
        },
        "domain": {
            "n": {"min": n, "max": n},
            "k": {"min": k, "max": k},
        },
        "execution": {
            "kind": "mac_service",
            "resource": "cube",
            "native_kernel": str(saturated.get("native_type") or ""),
            "tile_m": tile_m,
            "tile_n": tile_n,
            "tile_k": tile_k,
            "slots": 2,
        },
        "response": response,
        "provenance": {
            "schema_version": DUAL_LOAD_SCHEMA,
            "measured_supply_schema": MEASURED_SUPPLY_SCHEMA,
            "selected_by": "most_samples_per_condition_median",
            "issue_rule": issue,
            "tile_geometry": {
                "tile_m": tile_m, "tile_n": tile_n, "tile_k": tile_k,
                "basis": "N tile from observed tail owners; M tile 128 from family/source matrix geometry and L0c capacity; service cap does not depend on tile_m",
            },
            "physical_owners_basis": identity["physical_owners_basis"],
            "not_end_to_end_kernel_latency": True,
            "not_a_shape_work_envelope": True,
            "saturated_condition": saturated.get("provenance"),
            "underfilled_condition": underfilled.get("provenance"),
        },
    }
    return {
        "schema_version": DUAL_LOAD_SCHEMA,
        "identity": identity,
        "saturated": dict(saturated),
        "underfilled": dict(underfilled),
        "service_ratio": {
            "underfilled_over_saturated": float(underfilled["rate_flops_per_s"])
            / float(saturated["rate_flops_per_s"]),
        },
        "saturation_threshold": saturation_threshold,
        "service_regime": rule,
    }


def _median_value(rows: Sequence[Mapping[str, Any]], name: str) -> float | None:
    values = [float(row[name]) for row in rows
              if isinstance(row.get(name), (int, float))
              and not isinstance(row.get(name), bool)
              and math.isfinite(float(row[name]))]
    return statistics.median(values) if values else None


def _median_map(rows: Sequence[Mapping[str, Any]], name: str) -> dict[str, float]:
    keys = sorted({key for row in rows for key in (row.get(name) or {})})
    result = {}
    for key in keys:
        values = [float(row[name][key]) for row in rows
                  if isinstance(row.get(name), Mapping)
                  and isinstance(row[name].get(key), (int, float))
                  and math.isfinite(float(row[name][key]))]
        if values:
            result[key] = statistics.median(values)
    return result


def _condition_record(key: tuple[Any, ...], rows: Sequence[Mapping[str, Any]],
                      physical_owners: int, saturation_threshold: float) -> dict[str, Any]:
    first = dict(rows[0])
    times = _median_map(rows, "pipe_times_ns")
    ratios = _median_map(rows, "pipe_ratios")
    mac_time = times.get("aic_mac_time")
    mac_ratio = _median_value(rows, "mac_ratio")
    logical = _median_value(rows, "logical_flops")
    issued = _median_value(rows, "issued_flops")
    duration = _median_value(rows, "duration_ns")
    active_owners = int(first["active_owners"])
    rate = (issued / (mac_time * 1e-9)) if issued is not None and mac_time and mac_time > 0 else None
    per_owner = rate / active_owners if rate is not None else None
    limiting = max(ratios.items(), key=lambda item: (item[1], item[0]))[0] if ratios else None
    return {
        **first,
        "m": int(first["m"]), "n": int(first["n"]), "k": int(first["k"]),
        "active_owners": active_owners,
        "physical_owners": int(physical_owners),
        "event_count": len(rows),
        "logical_flops": int(logical) if logical is not None else None,
        "issued_flops": int(issued) if issued is not None else None,
        "flops": int(issued) if issued is not None else None,
        "duration_ns": duration,
        "mac_ratio": mac_ratio,
        "cube_utilization_pct": _median_value(rows, "cube_utilization_pct"),
        "pipe_times_ns": times,
        "pipe_ratios": ratios,
        "limited_by": limiting,
        "rate_flops_per_s": rate,
        "per_owner_rate_flops_per_s": per_owner,
        "effective_rate_flops_per_s": (
            issued / (duration * 1e-9) if issued and duration else None),
        "saturated": bool(active_owners == physical_owners and mac_ratio is not None
                          and mac_ratio >= saturation_threshold),
        "complete_in_window": all(bool(row.get("complete_in_window")) for row in rows),
        "provenance": {
            "source": first.get("provenance", {}).get("source"),
            "source_sha256": first.get("provenance", {}).get("source_sha256"),
            "source_schema": first.get("provenance", {}).get("source_schema"),
            "event_id": first.get("provenance", {}).get("event_id"),
            "row_index": first.get("provenance", {}).get("row_index"),
            "observation_id": first.get("provenance", {}).get("observation_id"),
            "native_call": first.get("native_call"),
            "native_type": first.get("native_type"),
            "device_id": first.get("device_id"),
            "rank_id": first.get("rank_id"),
            "rank_index": first.get("rank_index"),
            "condition": {
                "m": int(first["m"]), "n": int(first["n"]), "k": int(first["k"]),
                "active_owners": active_owners,
            },
            "event_count": len(rows),
            "median_basis": "per_condition_median_repeats",
            "source_paths": sorted({str(row.get("provenance", {}).get("source"))
                                    for row in rows
                                    if row.get("provenance", {}).get("source")})[:4],
            "event_ids": [row.get("provenance", {}).get("event_id")
                          for row in rows[:8]
                          if row.get("provenance", {}).get("event_id")],
            "row_indices": [row.get("provenance", {}).get("row_index")
                            for row in rows[:8]
                            if row.get("provenance", {}).get("row_index") is not None],
            "physical_owners_basis": "declared_aic_count",
            "issue_rule": first.get("issue"),
            "elapsed_duration_used_as_rate": False,
        },
    }


def summarize_measured_supply(
    candidates: Sequence[Mapping[str, Any]],
    *,
    physical_owners: int | None = None,
    source_identity: Mapping[str, Any] | None = None,
    resource_services: Sequence[Mapping[str, Any]] | None = None,
    saturation_threshold: float = SATURATION_THRESHOLD,
    max_groups: int = 16,
) -> dict[str, Any]:
    """Select one saturated/underfilled condition pair from per-condition medians."""
    limitations: list[dict[str, Any]] = []
    physical_owners = _positive_int(physical_owners)
    if physical_owners is None:
        limitations.append({
            "code": "measured_supply_physical_owners_not_declared",
            "detail": "declare the physical AIC count (for example --aic-count 32); "
                      "the maximum sampled Block Num is not capacity evidence",
            "severity": "high",
        })
        return {
            "schema_version": MEASURED_SUPPLY_SCHEMA,
            "status": "not_available",
            "selection": "most_samples_per_condition_median",
            "scope": MEASURED_SUPPLY_SCOPE,
            "not_end_to_end_kernel_latency": True,
            "pair": None,
            "source_identity": dict(source_identity) if source_identity else None,
            "resource_services": list(resource_services or ()),
            "candidates": [],
            "candidate_conditions": 0,
            "limitations": limitations,
        }
    conditions: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    clipped = 0
    for raw in candidates:
        candidate = dict(raw)
        if candidate.get("status") != "measured":
            continue
        if not candidate.get("complete_in_window"):
            clipped += 1
            continue
        key = (
            candidate.get("native_call"), candidate.get("native_type"),
            candidate.get("dtype"), candidate.get("output_dtype"),
            candidate.get("n"), candidate.get("k"),
            candidate.get("device_id"), candidate.get("rank_id"),
            int(candidate["m"]), int(candidate["active_owners"]),
            _canonical(candidate.get("issue")),
        )
        conditions.setdefault(key, []).append(candidate)
    summaries = [
        _condition_record(key, rows, physical_owners, saturation_threshold)
        for key, rows in conditions.items()
    ]
    identities: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in summaries:
        key = (
            row.get("native_call"), row.get("native_type"), row.get("dtype"),
            row.get("output_dtype"), row.get("n"), row.get("k"),
            row.get("device_id"), row.get("rank_id"),
            _canonical(row.get("issue")),
        )
        identities.setdefault(key, []).append(row)
    pairs: list[tuple[int, int, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    certified = 0
    for rows in identities.values():
        if rows[0].get("issue") is None:
            continue
        certified += 1
        fulls = [row for row in rows
                 if row["saturated"] and row["active_owners"] == physical_owners]
        tails = [row for row in rows
                 if not row["saturated"] and row["active_owners"] < physical_owners]
        best_full = max(fulls, key=lambda row: (row["event_count"], row["issued_flops"] or 0),
                        default=None)
        best_tail = max(tails, key=lambda row: (row["event_count"], -(row["issued_flops"] or 0)),
                        default=None)
        if best_full is None or best_tail is None:
            limitations.append({
                "code": ("measured_supply_no_saturated_condition" if best_full is None
                         else "measured_supply_no_underfilled_condition"),
                "detail": "identity has no complete full-grid saturated / lower-owner "
                          "underfilled condition pair",
                "severity": "medium",
            })
            continue
        try:
            pair = build_dual_load_service(
                best_full, best_tail, physical_owners=physical_owners,
                saturation_threshold=saturation_threshold)
        except ValueError as exc:
            limitations.append({
                "code": "measured_supply_pair_invalid",
                "detail": str(exc), "severity": "medium",
            })
            continue
        pairs.append((best_full["event_count"] + best_tail["event_count"],
                      int(best_full["issued_flops"] or 0), pair, best_full, best_tail))
    pair = None
    selected = ()
    if pairs:
        chosen = max(pairs, key=lambda item: (item[0], item[1]))
        pair, selected = chosen[2], (chosen[3], chosen[4])
    elif certified == 0:
        limitations.insert(0, {
            "code": "measured_supply_no_certified_issue_rule",
            "detail": "no condition carries the certified R64 QBMM issued-work rule",
            "severity": "medium",
        })
    if not summaries:
        limitations.insert(0, {
            "code": "measured_supply_no_matrix_pmu_events",
            "detail": "no complete matrix event with issued shape, owners and raw MAC counters",
            "severity": "medium",
        })
    if clipped:
        limitations.append({
            "code": "measured_supply_clipped_events_excluded",
            "detail": f"{clipped} matrix PMU events were clipped and not used",
            "severity": "medium",
        })
    selected_keys = {
        (row.get("native_call"), row.get("n"), row.get("k"), row.get("m"),
         row.get("active_owners"), row.get("device_id"), row.get("rank_id"))
        for row in selected
    }
    summaries.sort(key=lambda row: (
        0 if (row.get("native_call"), row.get("n"), row.get("k"), row.get("m"),
              row.get("active_owners"), row.get("device_id"), row.get("rank_id"))
        in selected_keys else 1,
        str(row.get("native_call")), row["n"], row["k"], row["m"], row["active_owners"]))
    return {
        "schema_version": MEASURED_SUPPLY_SCHEMA,
        "status": "measured_pair" if pair else "not_available",
        "selection": "most_samples_certified_identity_pair",
        "physical_owners": physical_owners,
        "physical_owners_basis": "declared_aic_count",
        "scope": MEASURED_SUPPLY_SCOPE,
        "not_end_to_end_kernel_latency": True,
        "certified_identities": certified,
        "pair": pair,
        "source_identity": dict(source_identity) if source_identity else None,
        "resource_services": list(resource_services or ()),
        "candidates": summaries[:max_groups],
        "candidate_conditions": len(summaries),
        "limitations": limitations,
    }


RESOURCE_SERVICE_SCHEMA = "mindie-profiler-resource-service/1"
SPARSE_NATIVE_TYPE = "KvQuantSparseFlashAttention"


def sparse_mte1_bytes(q_len: int, context: int, kv_len: int, *, causal: bool = True,
                      owners: int = 32, g: int = 64, dq: int = 576,
                      dv: int = 512, s2_tile: int = 128) -> dict[str, Any]:
    """Derive the actual per-owner QK/PV L1->L0A/B critical bytes.

    The sparse source walks contiguous S1 query prefixes across ``owners`` AIC
    owners; the critical owner is the maximum QK+PV L0A/L0B byte total, not the
    mean triangular work.  The geometry (q/context/kv/causal/owners) is an
    explicit input; a raw Qshape alone is not a geometry.
    """
    q_len, context, kv_len, owners = int(q_len), int(context), int(kv_len), int(owners)
    if q_len <= 0 or owners <= 0 or kv_len <= 0 or context < 0:
        raise ValueError("sparse_mte1_geometry_invalid")
    width = -(-q_len // owners)
    per_owner = []
    for start in range(0, q_len, width):
        qk = pv = ub = tiles = 0
        for index in range(start, min(start + width, q_len)):
            selected = min(kv_len, context + index + 1) if causal else min(
                kv_len, context + q_len)
            remaining = selected
            while remaining > 0:
                rows = min(int(s2_tile), remaining)
                aligned = ((rows + 15) // 16) * 16
                qk += 2 * g * dq + 2 * aligned * dq
                pv += 2 * g * aligned + 2 * dv * aligned
                ub += 2 * g * s2_tile
                tiles += 1
                remaining -= int(s2_tile)
        per_owner.append({"qk_pv_bytes": qk + pv, "qk_bytes": qk, "pv_bytes": pv,
                          "ub_bytes": ub, "tiles": tiles})
    critical_index = max(range(len(per_owner)),
                         key=lambda index: per_owner[index]["qk_pv_bytes"])
    critical = per_owner[critical_index]
    return {
        "q_len": q_len, "context": context, "kv_len": kv_len, "causal": bool(causal),
        "owners": owners, "g": int(g), "dq": int(dq), "dv": int(dv),
        "s2_tile": int(s2_tile), "per_owner_width": width,
        "critical_owner_index": critical_index,
        "critical_qk_pv_bytes": critical["qk_pv_bytes"],
        "critical_qk_bytes": critical["qk_bytes"],
        "critical_pv_bytes": critical["pv_bytes"],
        "critical_ub_bytes": critical["ub_bytes"],
        "critical_tiles": critical["tiles"],
        "total_qk_pv_bytes": sum(item["qk_pv_bytes"] for item in per_owner),
        "total_ub_bytes": sum(item["ub_bytes"] for item in per_owner),
        "total_tiles": sum(item["tiles"] for item in per_owner),
    }


def summarize_sparse_mte1(candidates: Sequence[Mapping[str, Any]], *,
                          source_identity: Mapping[str, Any] | None,
                          sparse_geometry: Mapping[str, Any] | None,
                          hardware: str | None = None) -> list[dict[str, Any]]:
    """One scoped saturated MTE1 resource service from actual SFA events."""
    if not source_identity or source_identity.get("source_scope") != "r64":
        return []
    if not isinstance(sparse_geometry, Mapping):
        return []
    if str(sparse_geometry.get("op_state", "dynamic")).lower() != "dynamic":
        return []
    if str(sparse_geometry.get("phase", "prefill")).lower() != "prefill":
        return []
    try:
        q_len = int(sparse_geometry["q_len"])
        context = int(sparse_geometry.get("context", 0))
        kv_len = int(sparse_geometry.get("kv_len", q_len))
        owners = int(sparse_geometry.get("owners", 32))
        mix = int(sparse_geometry.get("mix_block_num", 64))
        causal = bool(sparse_geometry.get("causal", True))
        state = str(sparse_geometry.get("op_state", "dynamic")).lower()
        phase = str(sparse_geometry.get("phase", "prefill"))
        geometry = sparse_mte1_bytes(
            q_len, context, kv_len, causal=causal, owners=owners,
            g=int(sparse_geometry.get("g", 64)),
            dq=int(sparse_geometry.get("dq", 576)),
            dv=int(sparse_geometry.get("dv", 512)),
            s2_tile=int(sparse_geometry.get("s2_tile", 128)),
        )
    except (KeyError, TypeError, ValueError):
        return []
    grouped: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for candidate in candidates:
        if str(candidate.get("native_type")) != SPARSE_NATIVE_TYPE:
            continue
        if str(candidate.get("dtype")) != "bf16":
            continue
        if int(candidate.get("q_tokens") or -1) != q_len:
            continue
        if int(candidate.get("block_num") or -1) != owners:
            continue
        if int(candidate.get("mix_block_num") or -1) != mix:
            continue
        if str(candidate.get("op_state") or "").lower() != state:
            continue
        if not candidate.get("mte1_us") or not candidate.get("elapsed_us"):
            continue
        grouped.setdefault((q_len, owners, mix, state), []).append(candidate)
    records = []
    for rows in grouped.values():
        mte1 = statistics.median(float(item["mte1_us"]) for item in rows)
        elapsed = statistics.median(float(item["elapsed_us"]) for item in rows)
        if mte1 <= 0:
            continue
        rate = geometry["critical_qk_pv_bytes"] / (mte1 * 1e-6)
        record = {
            "schema_version": RESOURCE_SERVICE_SCHEMA,
            "resource": "mte1",
            "native_type": SPARSE_NATIVE_TYPE,
            "kernel": SPARSE_NATIVE_TYPE,
            "source_identity": dict(source_identity),
            "hardware": str(hardware or sparse_geometry.get("hardware") or ""),
            "dtype": "bf16",
            "layout": str(sparse_geometry.get("layout")
                          or "QK/PV BF16 L1->L0A/L0B"),
            "input_formats": rows[0].get("input_formats"),
            "output_formats": rows[0].get("output_formats"),
            "phase": phase,
            "op_state": state,
            "scope": "critical_owner",
            "shape_class": str(sparse_geometry.get("shape_class")
                               or f"prefill_causal_q{q_len}_g{geometry['g']}_"
                                  f"dq{geometry['dq']}_dv{geometry['dv']}_"
                                  f"s2tile{geometry['s2_tile']}"),
            "geometry_binding": {**dict(sparse_geometry),
                                 "q_len": q_len, "context": context,
                                 "kv_len": kv_len, "owners": owners,
                                 "mix_block_num": mix, "causal": causal,
                                 "op_state": state, "phase": phase},
            "owners": owners,
            "block_num": owners,
            "mix_block_num": mix,
            "measured_q_tokens": q_len,
            "measured_context": context,
            "measured_kv_len": kv_len,
            "measured_critical_bytes": geometry["critical_qk_pv_bytes"],
            "measured_total_bytes": geometry["total_qk_pv_bytes"],
            "measured_critical_ub_bytes": geometry["critical_ub_bytes"],
            "measured_total_ub_bytes": geometry["total_ub_bytes"],
            "critical_owner_index": geometry["critical_owner_index"],
            "event_count": len(rows),
            "median_mte1_us": mte1,
            "median_elapsed_us": elapsed,
            "rate_bytes_per_s": rate,
            "pmu": "aic_mte1_time",
            "source": rows[0].get("source"),
            "source_sha256": rows[0].get("source_sha256"),
            "provenance": {
                "event_ids": [item.get("event_id") for item in rows[:8]],
                "row_indices": [item.get("row_index") for item in rows[:8]],
                "source_sha256": rows[0].get("source_sha256"),
                "geometry_basis": sparse_geometry.get("geometry_basis"),
                "not_elapsed_rate": True,
                "not_index_or_routing_target": True,
            },
        }
        records.append(record)
    return records


__all__ = [
    "DUAL_LOAD_SCHEMA",
    "RESOURCE_SERVICE_SCHEMA",
    "SPARSE_NATIVE_TYPE",
    "MEASURED_SUPPLY_SCHEMA",
    "MEASURED_SUPPLY_SCOPE",
    "PMU_ANALYSIS_SCHEMA",
    "SATURATION_THRESHOLD",
    "build_dual_load_service",
    "derive_measured_supply",
    "derive_pmu_evidence",
    "metric_units",
    "summarize_measured_supply",
]
