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
  Pure in-memory arithmetic; zero I/O after one cached mapping load.

[Side-Effect Policy]
  Read-only after mapping load; no file writes, network, or source mutation.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from functools import lru_cache
from typing import Any, Mapping, Sequence
from .sources_db import load_mapping

from .pmu_derivation_summary import build_dual_load_service
from .pmu_derivation_supply import (
    DUAL_LOAD_SCHEMA, MEASURED_SUPPLY_SCHEMA, MEASURED_SUPPLY_SCOPE,
    PMU_ANALYSIS_SCHEMA, R35_IMAGE_SHA, R64_IMAGE_SHA, RULE_SOURCE, RULE_SOURCE_COMMIT,
    RULE_SOURCE_PATH, RULE_SOURCE_VERSION, SATURATION_THRESHOLD, _AIC_PIPES, _AIV_PIPES,
    _CUBE_REQUIRED, _DTYPE_ALIASES, _QBMM_ISSUE_RULE, _VECTOR_REQUIRED, _canonical,
    _cube_rule, _dtype_name, _finite, _frequency, _issue_rule, _issued_flops,
    _load_record, _mapping, _metric, _number, _pipe_evidence, _positive_int, _require,
    _rule_meta, _scope_evidence, _tensor_rows, _vector_rule, deployment_source_identity,
    derive_measured_supply, derive_pmu_evidence, image_digest, metric_units,
)

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
