"""Measured matrix-pipe dual-load supply and deployment source identity.

[Role]
  Derive per-event matrix-pipe service observations from raw AIC/AIV PMU
  counters, certify issued work through the implementation/tiling issue laws
  in ``measured_supply_rules``, and construct a pure saturated/underfilled
  dual-load measurement document without inventing simulator execution
  policies or tile schedules.

[Invariants]
  * A measured service rate is ``issued_flops / aic_mac_time``, never
    ``issued_flops / duration_ns``.  Elapsed kernel duration stays provenance.
  * Physical AIC capacity (``physical_owners``) must be declared explicitly
    (e.g. ``--aic-count 32``) and is never inferred from sampled ``Block Num``.
  * Only 2D ``[M, K] -> [M, N]`` matrix shapes with compatible weight elements
    are certified; higher-rank batched tensors remain ``unknown``.
  * Issued math requires a certified issue law (pinned kernel and wrapper
    source identity, or a legacy corroborating image digest) plus
    ``ND;FRACTAL_NZ;ND;ND -> ND`` formats; R35, bare, conflicting, and foreign
    captures retain logical FLOPs.

[Timeouts & Locks]
  Pure in-memory finite arithmetic; no I/O or locks.

[Side-Effect Policy]
  Returns fresh dicts/lists only; mutates neither events nor global state.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from .events import Event, Observation
from .measured_supply_rules import (
    ISSUE_LAWS,
    R35_IMAGE_SHA,
    R64_IMAGE_SHA,
    _DTYPE_ALIASES,
    _QBMM_ISSUE_RULE,
    _dtype_name,
    _dtype_slots,
    _issue_rule,
    _issued_flops,
    _nz_matches,
    _parse_2d_matrix_shapes,
    _tensor_rows,
    certify_issue_law,
    deployment_source_identity,
    image_digest,
    verified_implementation,
)
from .pmu_derivation import _AIC_PIPES, _AIV_PIPES, _number, metric_units

MEASURED_SUPPLY_SCHEMA = "mindie-profiler-measured-supply/1"
DUAL_LOAD_SCHEMA = "mindie-profiler-dual-load/1"
MEASURED_SUPPLY_SCOPE = "matrix_pipe_service"
SATURATION_THRESHOLD = 0.90
MAX_SUPPLY_CONDITIONS = 256
MAX_SAMPLES_PER_CONDITION = 512

SELECTION_LIMITATION_CODES = frozenset(
    {
        "measured_supply_no_matrix_pmu_events",
        "measured_supply_pair_invalid",
        "measured_supply_clipped_events_excluded",
        "measured_supply_physical_owners_not_declared",
        "measured_supply_no_certified_issue_rule",
        "measured_supply_condition_cap_reached",
        "measured_supply_condition_samples_capped",
        "sparse_mte1_source_not_r64",
        "sparse_mte1_not_prefill_dynamic",
        "sparse_mte1_no_matching_events",
        "sparse_mte1_tensor_geometry_mismatch",
        "sparse_mte1_groups_capped",
        "sparse_mte1_samples_capped",
    }
)


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def _pipe_evidence(
    metrics: Mapping[str, float],
) -> tuple[dict[str, float], dict[str, float], str | None]:
    times: dict[str, float] = {}
    ratios: dict[str, float] = {}
    for scope, pipes in (("aic", _AIC_PIPES), ("aiv", _AIV_PIPES)):
        for pipe in pipes:
            time_val = _number(metrics, f"{scope}_{pipe}_time")
            ratio_val = _number(metrics, f"{scope}_{pipe}_ratio")
            if time_val is not None:
                times[f"{scope}_{pipe}_time"] = time_val
            if ratio_val is not None:
                ratios[f"{scope}_{pipe}_ratio"] = ratio_val
    limiting = max(ratios.items(), key=lambda item: (item[1], item[0]))[0] if ratios else None
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
    """Derive one measured matrix-pipe service observation from raw counters."""
    in_dtypes_slots = _dtype_slots(input_dtypes, limit=6)
    out_dtypes_slots = _dtype_slots(output_dtypes, limit=2)
    dtype = in_dtypes_slots[0] if in_dtypes_slots else None
    weight_dtype = in_dtypes_slots[1] if len(in_dtypes_slots) >= 2 else None
    output_dtype = out_dtypes_slots[0] if out_dtypes_slots else None
    active_owners = _positive_int(block_num)
    resolved_owners = _positive_int(physical_owners)
    times, ratios, limiting = _pipe_evidence(metrics)
    folded_kind = f"{native_type or ''} {native_call or ''}".lower()
    is_named_non_matrix = (
        (native_type is not None or native_call is not None)
        and "matmul" not in folded_kind
        and "gemm" not in folded_kind
    )
    if is_named_non_matrix:
        return {
            "schema_version": MEASURED_SUPPLY_SCHEMA,
            "status": "not_applicable",
            "scope": MEASURED_SUPPLY_SCOPE,
            "not_end_to_end_kernel_latency": True,
            "native_call": native_call,
            "native_type": native_type,
            "dtype": dtype,
            "output_dtype": output_dtype,
            "device_id": device_id,
            "rank_id": rank_id,
            "rank_index": rank_index,
            "m": None,
            "n": None,
            "k": None,
            "logical_flops": None,
            "issued_flops": None,
            "flops": None,
            "work_basis": "not_matrix_operator",
            "issue": None,
            "active_owners": active_owners,
            "block_num": active_owners,
            "mix_block_num": _positive_int(mix_block_num),
            "physical_owners": resolved_owners,
            "duration_ns": duration_ns,
            "mac_ratio": ratios.get("aic_mac_ratio"),
            "cube_utilization_pct": _number(metrics, "cube_utilization"),
            "pipe_times_ns": times,
            "pipe_ratios": ratios,
            "limited_by": limiting,
            "rate_flops_per_s": None,
            "per_owner_rate_flops_per_s": None,
            "logical_rate_flops_per_s": None,
            "effective_rate_flops_per_s": None,
            "saturated": None,
            "complete_in_window": bool(complete_in_window),
            "counter_status": "not_applicable",
            "missing": ["not_matrix_operator"],
            "provenance": {
                "source": source,
                "source_sha256": source_sha256,
                "source_schema": source_schema,
                "event_id": event_id,
                "row_index": row_index,
                "observation_id": observation_id,
                "input_formats": input_formats,
                "output_formats": output_formats,
                "scope": "not_matrix_operator",
                "elapsed_duration_used_as_rate": False,
            },
        }
    m, k, n, reasons, in_shapes_slots = _parse_2d_matrix_shapes(input_shapes, output_shapes)
    shape_valid = not reasons and all(isinstance(v, int) and v > 0 for v in (m, n, k))
    if dtype is None:
        reasons.append("input_dtype_not_parsed")
    if weight_dtype is None:
        reasons.append("weight_dtype_not_parsed")
    if output_dtype is None:
        reasons.append("output_dtype_not_parsed")
    dtype_valid = dtype is not None and weight_dtype is not None and output_dtype is not None
    if active_owners is None:
        reasons.append("block_num_missing")
    if resolved_owners is None:
        reasons.append("physical_owners_not_declared")
    logical_flops = (
        2 * int(m) * int(n) * int(k) if (shape_valid and dtype_valid) else None
    )
    weight = in_shapes_slots[1] if len(in_shapes_slots) > 1 else None
    # FLOPs stay logical 2*M*K*N; padded NZ extent is transfer-volume evidence only.
    weight_physical_elements = math.prod(weight) if isinstance(weight, tuple) and len(weight) == 4 else None
    issue = (
        _issue_rule(
            native_type,
            dtype,
            output_dtype,
            n,
            k,
            input_shapes_slots=in_shapes_slots,
            input_dtypes_slots=in_dtypes_slots,
            input_formats=input_formats,
            output_formats=output_formats,
            source=source_identity,
        )
        if (shape_valid and dtype_valid)
        else None
    )
    issued_flops = _issued_flops(logical_flops, m, issue)
    if logical_flops is None:
        reasons.append("logical_flops_not_available")
    if issue is None:
        issued_flops = logical_flops
        work_basis = "logical_2_m_n_k_flops_no_issue_rule"
    else:
        work_basis = "issued_2_align_m_k_n_flops"
    if issued_flops is None:
        reasons.append("issued_flops_not_available")
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
    saturated = (
        bool(active_owners == resolved_owners and mac_ratio >= saturation_threshold)
        if resolved_owners and active_owners and mac_ratio is not None
        else None
    )
    status = "measured" if rate is not None and active_owners else "unknown"
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
        "m": m if shape_valid else None,
        "n": n if shape_valid else None,
        "k": k if shape_valid else None,
        "logical_flops": logical_flops,
        "weight_physical_elements": weight_physical_elements,
        "issued_flops": issued_flops,
        "flops": issued_flops,
        "work_basis": work_basis,
        "issue": issue,
        "active_owners": active_owners,
        "block_num": active_owners,
        "mix_block_num": mix_block_num,
        "physical_owners": resolved_owners,
        "limited_by": limiting,
        "pipe_times_ns": times,
        "pipe_ratios": ratios,
        "mac_ratio": mac_ratio,
        "cube_utilization_pct": _number(metrics, "cube_utilization_pct"),
        "saturation_threshold": saturation_threshold,
        "saturation_basis": "active_owners == physical_owners and aic_mac_ratio >= threshold",
        "limiting_pipe_basis": "highest measured AIC/AIV pipe ratio",
        "saturated": saturated,
        "rate_flops_per_s": rate,
        "per_owner_rate_flops_per_s": per_owner_rate,
        "logical_rate_flops_per_s": logical_rate,
        "rate_basis": (
            "issued_flops / aic_mac_time_ns (whole matrix pipe); "
            "per_owner_rate divides by active_owners"
        ),
        "effective_rate_flops_per_s": (
            issued_flops / (duration_ns * 1e-9) if issued_flops and duration_ns else None
        ),
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
            "weight_physical_elements": weight_physical_elements,
            "issued_flops": issued_flops,
            "issue_rule": issue,
            "metric_units": metric_units(metrics),
            "elapsed_duration_used_as_rate": False,
            "physical_owners_basis": "declared_aic_count" if resolved_owners else "not_declared",
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
        "per_owner_rate_flops_per_s": float(row["per_owner_rate_flops_per_s"]),
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


def _canonical_issue(issue: Mapping[str, Any]) -> dict[str, Any]:
    """Law identity excludes per-capture evidence, so cross-image runs pair."""
    excluded = {
        "deployment_image_id",
        "source_basis",
        "source_scope",
        "implementation_verified",
        "kernel_source_sha256",
        "kernel_revision",
        "wrapper_source_sha256",
        "wrapper_revision",
    }
    return {key: value for key, value in issue.items() if key not in excluded}


def build_dual_load_service(
    saturated: Mapping[str, Any],
    underfilled: Mapping[str, Any],
    *,
    physical_owners: int,
    saturation_threshold: float = SATURATION_THRESHOLD,
) -> dict[str, Any]:
    """Build a pure measured dual-load supply observation pair.

    Profiler emits measurement evidence only; simulation execution modes, queue
    bindings, and tile interpolation policies belong in ``mindie-sim``.
    """
    _require(saturated.get("status") == "measured", "measured_supply_saturated_unknown")
    _require(underfilled.get("status") == "measured", "measured_supply_underfilled_unknown")
    _require(
        saturated.get("complete_in_window") is True,
        "measured_supply_saturated_incomplete_in_window",
    )
    _require(
        underfilled.get("complete_in_window") is True,
        "measured_supply_underfilled_incomplete_in_window",
    )
    for field in ("native_type", "dtype", "output_dtype", "n", "k", "device_id", "rank_id"):
        _require(
            saturated.get(field) == underfilled.get(field),
            f"measured_supply_identity_mismatch:{field}",
        )
    _require(
        saturated.get("issue") is not None and underfilled.get("issue") is not None,
        "measured_supply_requires_certified_issue_rule",
    )
    _require(_canonical_issue(saturated["issue"]) == _canonical_issue(underfilled["issue"]),
             "measured_supply_issue_rule_mismatch")
    _require(
        int(saturated["active_owners"]) == int(physical_owners),
        "measured_supply_saturated_not_full_grid",
    )
    _require(
        0 < int(underfilled["active_owners"]) < int(physical_owners),
        "measured_supply_underfilled_not_tail_grid",
    )
    full_mac, tail_mac = saturated.get("mac_ratio"), underfilled.get("mac_ratio")
    _require(
        isinstance(full_mac, (int, float)) and not isinstance(full_mac, bool),
        "measured_supply_saturated_mac_ratio_missing",
    )
    _require(
        isinstance(tail_mac, (int, float)) and not isinstance(tail_mac, bool),
        "measured_supply_underfilled_mac_ratio_missing",
    )
    _require(
        float(full_mac) >= saturation_threshold,
        "measured_supply_saturated_mac_ratio_below_threshold",
    )
    _require(
        float(tail_mac) < saturation_threshold,
        "measured_supply_underfilled_mac_ratio_above_threshold",
    )
    _require(
        float(saturated["rate_flops_per_s"]) > float(underfilled["rate_flops_per_s"]),
        "measured_supply_saturated_rate_not_greater",
    )
    dtype = str(saturated["dtype"])
    issue = dict(saturated["issue"])
    n, k = int(saturated["n"]), int(saturated["k"])
    identity = {
        "native_call": saturated.get("native_call"),
        "native_type": saturated.get("native_type"),
        "dtype": dtype,
        "output_dtype": saturated.get("output_dtype"),
        "n": n,
        "k": k,
        "device_id": saturated.get("device_id"),
        "rank_id": saturated.get("rank_id"),
        "physical_owners": int(physical_owners),
        "physical_owners_basis": saturated.get("provenance", {}).get(
            "physical_owners_basis", "declared_aic_count"
        ),
        "issue_rule": issue,
    }
    loads = [_load_record(saturated, "saturated"), _load_record(underfilled, "underfilled")]
    pair_digest = hashlib.sha256(
        _canonical(
            {
                "identity": identity,
                "loads": [
                    {
                        key: load[key]
                        for key in (
                            "id",
                            "active_owners",
                            "rate_flops_per_s",
                            "measured_issued_flops",
                        )
                    }
                    for load in loads
                ],
            }
        ).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "schema_version": DUAL_LOAD_SCHEMA,
        "pair_id": f"measured-dual-load-{pair_digest}",
        "identity": identity,
        "loads": loads,
        "saturated": dict(saturated),
        "underfilled": dict(underfilled),
        "service_ratio": {
            "underfilled_over_saturated": float(underfilled["rate_flops_per_s"])
            / float(saturated["rate_flops_per_s"]),
        },
        "saturation_threshold": saturation_threshold,
        "provenance": {
            "schema_version": DUAL_LOAD_SCHEMA,
            "measured_supply_schema": MEASURED_SUPPLY_SCHEMA,
            "selected_by": "most_samples_per_condition_median",
            "issue_rule": issue,
            "physical_owners_basis": identity["physical_owners_basis"],
            "not_end_to_end_kernel_latency": True,
            "not_a_shape_work_envelope": True,
            "execution_policy_emitted": False,
            "saturated_condition": saturated.get("provenance"),
            "underfilled_condition": underfilled.get("provenance"),
        },
    }


def measured_supply_event_record(
    observation: Observation,
    event: Event,
    source_identity: Mapping[str, Any] | None = None,
    *,
    physical_owners: int | None = None,
) -> dict[str, Any]:
    """Build one matrix-pipe observation; missing fields remain explicit."""
    return derive_measured_supply(
        event.pmu_map(),
        input_shapes=event.input_shapes,
        input_dtypes=event.input_dtypes,
        input_formats=event.input_formats,
        output_shapes=event.output_shapes,
        output_dtypes=event.output_dtypes,
        output_formats=event.output_formats,
        source_identity=source_identity,
        block_num=event.block_dim,
        mix_block_num=event.mix_block_dim,
        complete_in_window=event.complete_in(observation.window.start_ns, observation.window.end_ns),
        source=observation.source.path,
        source_sha256=observation.source.sha256,
        source_schema=observation.source.schema_version,
        event_id=event.event_id,
        row_index=event.locator.get("row_index"),
        observation_id=observation.identity()["observation_id"],
        native_call=event.name,
        native_type=event.op_type,
        device_id=event.device_id,
        rank_id=observation.rank_id,
        rank_index=observation.rank_index,
        duration_ns=event.duration_ns,
        physical_owners=physical_owners,
        saturation_threshold=SATURATION_THRESHOLD,
    )


def is_matrix_supply_event(event: Event) -> bool:
    folded = f"{event.op_type} {event.name}".lower()
    return ("matmul" in folded or "gemm" in folded) and "aic_mac_time" in event.pmu_map()


from .measured_supply_summary import MatrixSupplyAccumulator, summarize_measured_supply  # noqa: E402

__all__ = [
    "DUAL_LOAD_SCHEMA",
    "ISSUE_LAWS",
    "MAX_SAMPLES_PER_CONDITION",
    "MAX_SUPPLY_CONDITIONS",
    "MEASURED_SUPPLY_SCHEMA",
    "MEASURED_SUPPLY_SCOPE",
    "MatrixSupplyAccumulator",
    "R35_IMAGE_SHA",
    "R64_IMAGE_SHA",
    "SATURATION_THRESHOLD",
    "SELECTION_LIMITATION_CODES",
    "_DTYPE_ALIASES",
    "_QBMM_ISSUE_RULE",
    "_canonical",
    "_dtype_name",
    "_dtype_slots",
    "_issue_rule",
    "_issued_flops",
    "_nz_matches",
    "_parse_2d_matrix_shapes",
    "_positive_int",
    "_tensor_rows",
    "build_dual_load_service",
    "certify_issue_law",
    "deployment_source_identity",
    "derive_measured_supply",
    "image_digest",
    "is_matrix_supply_event",
    "measured_supply_event_record",
    "summarize_measured_supply",
    "verified_implementation",
]
