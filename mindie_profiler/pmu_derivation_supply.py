"""PMU pipe utilization, measured hardware supply derivation, and sparse MTE1 accounting (pmu_derivation_supply).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting pmu pipe utilization, measured hardware supply derivation, and sparse mte1 accounting.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import json
import math
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
    """Return issued math only for the source-certified CANN 9.2.1-r64 QBMM kernel.

    Shape, dtype, and K/N divisibility are necessary but insufficient: the
    capture must carry the pinned CANN r64 deployment image digest and true
    ``FRACTAL_NZ`` weight layout.  CANN r35 or unpinned images keep generic work.
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
