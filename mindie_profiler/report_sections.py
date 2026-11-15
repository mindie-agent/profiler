"""Deterministic C7 mindie-profile-summary/1 report assembly and atomic JSON output (report_sections).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting deterministic c7 mindie-profile-summary/1 report assembly and atomic json output.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from typing import Any, Sequence
from .accounting import hotspot_aggregates, percentile
from .cross_rank import (
    _observation_accounting,
    _reference_projections,
    aggregate_observations,
    cross_rank_stats,
    p50,
)
from .events import Observation, PARSER_VERSION, REPORT_SCHEMA, SourceRef

def _ms(value: int | float | None) -> float | None:
    return None if value is None else round(float(value) / 1_000_000.0, 6)

def _source_kind(sources: Sequence[SourceRef]) -> str:
    kinds = {source.kind for source in sources}
    if kinds == {"db"}:
        return "ascend_pytorch_profiler_db"
    if kinds == {"csv"}:
        return "kernel_details_csv"
    return "mixed"

def _source_sha_map(sources: Sequence[SourceRef], kind: str) -> dict[str, str | None]:
    return {
        source.rank_id: source.sha256
        for source in sources
        if source.kind == kind
    }

def _schema_version(sources: Sequence[SourceRef]) -> str | dict[str, str]:
    values = sorted({source.schema_version for source in sources})
    if len(values) == 1:
        return values[0]
    return {source.rank_id: source.schema_version for source in sources}

def _metric_definitions() -> dict[str, str]:
    return {
        "request_wall_ms": "external client/server request duration; None unless explicitly supplied",
        "window_duration_ms": "query window length (window.end_ns - window.start_ns), not a request duration",
        "observed_event_span_ms": "max clipped event end - min clipped event start inside the explicit window",
        "device_busy_union_ms": "length of the union of clipped device event intervals; overlapping events counted once",
        "device_activity_sum_ms": "sum of clipped device event durations; overlapping events counted per event",
        "exposed_comm_ms": "communication union minus non-communication union; fused MoE communication is not exposed",
        "device_uncovered_ms": "observed_event_span minus device_busy_union; device idle, not a host-dispatch measurement",
        "host_dispatch_gap_ms": "measured Host/Runtime to device launch gap; None without correlate evidence",
        "total_cost_ms": "device_activity_sum + device_uncovered; not an end-to-end wall and not additive with exposed_comm",
        "clipped_event_count": "events crossed by a window boundary; kept in activity sums but excluded from per-call P50/P90/Max",
        "underfeed_bubble_ratio": "device_uncovered / observed_event_span",
        "block_union_ms": "per-block union of clipped events; shares are normalised over the sum of block unions",
        "wall_ms": "deprecated alias for observed_event_span_ms",
        "busy_union_ms": "deprecated alias for device_busy_union_ms",
        "kernel_sum_ms": "deprecated alias for device_activity_sum_ms",
        "host_gap_ms": "deprecated alias for device_uncovered_ms",
        "steady_steps": "only explicitly supplied steps; kernel details have no step-id column",
        "window_start_us/window_end_us": "offsets from window_origin_ns; exact bounds remain integer window_start_ns/window_end_ns",
    }

def _id_list(values: Sequence[int]) -> str:
    return ",".join(str(int(value)) for value in values)

def _filter_sql(locator: dict[str, Any], task_ids: Sequence[int], row_indices: Sequence[int], rowids: Sequence[int]) -> str:
    table = locator.get("table") or "kernel_details.csv"
    if table == "COMMUNICATION_OP":
        return f"COMMUNICATION_OP WHERE rowid IN ({_id_list(rowids)})"
    if table in {"COMPUTE_TASK_INFO", "COMMUNICATION_SCHEDULE_TASK_INFO"}:
        return f"{table} WHERE globalTaskId IN ({_id_list(task_ids)})"
    return f"kernel_details.csv WHERE row_index IN ({_id_list(row_indices)})"

def _hotspot_key(row: dict, group_by: str) -> tuple:
    if group_by == "kernel":
        return (row["rank_id"], row["semantic_block"], row["kernel_name"])
    return (
        row["rank_id"],
        row["semantic_block"],
        row["kernel_name"],
        row.get("input_shapes", ""),
        row.get("input_dtypes", ""),
        row.get("input_formats", ""),
    )

def _execution_engine(row: dict) -> str | None:
    engines = sorted(str(item) for item in row.get("execution_engines", ()) if item)
    if not engines:
        return None
    return engines[0] if len(engines) == 1 else "mixed"

def _bound_family(row: dict) -> str:
    families = sorted(str(item) for item in row.get("bound_families", ()) if item and item != "unknown")
    return families[0] if len(families) == 1 else "unknown"

def _hotspots(
    observations: Sequence[Observation],
    sources: dict[str, SourceRef],
    top_n: int,
    *,
    group_by: str = "variant",
) -> list[dict]:
    if group_by not in {"variant", "kernel"}:
        raise ValueError(f"group_by must be variant or kernel, got {group_by!r}")
    grouped: dict[tuple, dict] = {}
    total_duration = 0
    for observation in observations:
        if not observation.accounting.available:
            continue
        total_duration += observation.accounting.device_activity_sum_ns or 0
        identity_by_locator = {id(event.locator): event.identity() for event in observation.events}
        for row in hotspot_aggregates(observation.events, observation.window):
            enriched_locators = []
            for locator in row["locators"]:
                identity = identity_by_locator.get(id(locator)) or {}
                enriched_locators.append({**locator, "event_id": identity.get("event_id")})
            row["locators"] = enriched_locators
            key = _hotspot_key(row, group_by)
            current = grouped.get(key)
            if current is None:
                current = {
                    **row,
                    "durations": list(row["durations"]),
                    "locators": list(row["locators"]),
                    "execution_engines": set(row.get("execution_engines", ())),
                    "bound_families": set(row.get("bound_families", ())),
                    "last_observation": observation,
                    "window_labels": [observation.window.label or str(observation.window.step)],
                    "window_bounds_ns": [[observation.window.start_ns, observation.window.end_ns]],
                    "variant_inputs": {
                        (row.get("input_shapes", ""), row.get("input_dtypes", ""), row.get("input_formats", ""))
                    },
                }
                grouped[key] = current
            else:
                current["duration_ns"] += row["duration_ns"]
                current["count"] += row["count"]
                current["clipped_event_count"] += row["clipped_event_count"]
                current["durations"].extend(row["durations"])
                current["execution_engines"].update(row.get("execution_engines", ()))
                current["bound_families"].update(row.get("bound_families", ()))
                current["variant_inputs"].add(
                    (row.get("input_shapes", ""), row.get("input_dtypes", ""), row.get("input_formats", ""))
                )
                if len(current["locators"]) < 16:
                    current["locators"].extend(row["locators"][: 16 - len(current["locators"])])
                label = observation.window.label or str(observation.window.step)
                current["window_labels"].append(label)
                current["window_bounds_ns"].append([observation.window.start_ns, observation.window.end_ns])
    rows: list[dict] = []
    for row in grouped.values():
        observation = row["last_observation"]
        source = sources.get(row["rank_id"])
        locator = row["locators"][0] if row["locators"] else {}
        task_ids = sorted(
            {
                int(item["task_global_id"])
                for item in row["locators"]
                if item.get("task_global_id") is not None
            }
        )
        row_indices = sorted(
            {
                int(item["row_index"])
                for item in row["locators"]
                if item.get("row_index") is not None
            }
        )
        rowids = sorted(
            {
                int(item["rowid"])
                for item in row["locators"]
                if item.get("rowid") is not None
            }
        )
        event_ids = sorted(
            {
                str(item["event_id"])
                for item in row["locators"]
                if item.get("event_id")
            }
        )
        evidence = {
            "db_file": source.basename if source and source.kind == "db" else None,
            "csv_file": source.basename if source and source.kind == "csv" else None,
            "table": locator.get("table"),
            "filter_sql": _filter_sql(locator, task_ids, row_indices, rowids),
            "task_global_ids": task_ids,
            "row_indices": row_indices,
            "rowids": rowids,
            "ids_truncated": row["count"] > len(row["locators"]),
            "total_contributing_events": row["count"],
            "retained_event_locators": len(row["locators"]),
            "event_ids": event_ids,
            "event_id_count": len(event_ids),
            "event_ids_truncated": row["count"] > len(event_ids),
            "filter_scope": "locator_sample",
            "measurement_basis": "all clipped event occurrences in the requested windows; filter_sql selects the retained locator sample",
            "window_labels": row["window_labels"],
            "window_bounds_ns": row["window_bounds_ns"],
            "rank_id": row["rank_id"],
            "source_sha256": source.sha256 if source else None,
        }
        variant_inputs = sorted(row.get("variant_inputs", ()))
        variant_count = len(variant_inputs) if group_by == "kernel" else 1
        if group_by == "kernel" and variant_count > 1:
            input_shapes = None
            input_dtypes = None
            input_formats = None
        else:
            input_shapes = row.get("input_shapes") or None
            input_dtypes = row.get("input_dtypes") or None
            input_formats = row.get("input_formats") or None
        has_shape = bool(input_shapes)
        reason = (
            "model provider/inputs not configured; no ideal lower bound or prediction was requested"
            if has_shape
            else "missing input shape/dtype/layout and no model provider configured"
        )
        durations = row["durations"]
        rows.append(
            {
                "rank": observation.rank_index if observation.rank_index is not None else row["rank_id"],
                "rank_id": row["rank_id"],
                "rank_index": observation.rank_index,
                "semantic_block": row["semantic_block"],
                "kernel_name": row["kernel_name"],
                "input_shapes": input_shapes,
                "input_dtypes": input_dtypes,
                "input_formats": input_formats,
                "variant_count": variant_count,
                "variant_inputs": [
                    {"input_shapes": shapes, "input_dtypes": dtypes, "input_formats": formats}
                    for shapes, dtypes, formats in variant_inputs
                ] if group_by == "kernel" else [],
                "group_by": group_by,
                "execution_engine": _execution_engine(row),
                "bound_family": _bound_family(row),
                "measured_device_ms_p50": p50(_ms(value) for value in durations),
                "measured_device_ms_p90": _ms(percentile(durations, 0.9)),
                "measured_device_ms_max": _ms(max(durations) if durations else None),
                "measured_device_ms_total": _ms(row["duration_ns"]),
                "share_of_busy_pct": (
                    round(100.0 * row["duration_ns"] / total_duration, 6) if total_duration > 0 else None
                ),
                "share_basis": "sum of clipped event durations / device_activity_sum",
                "share_denominator": "device_activity_sum_ms",
                "share_denominator_ms": _ms(total_duration),
                "representative_window": observation.window.label or str(observation.window.step),
                "call_count": row["count"],
                "complete_call_count": len(durations),
                "clipped_event_count": row["clipped_event_count"],
                "distribution_basis": "complete_in_window_events_only",
                "modeling_alignment": {
                    "status": "unmodeled",
                    "ideal_hardware_lower_bound_ms": None,
                    "model_predicted_ms": None,
                    "model_provider": None,
                    "model_assumptions": None,
                    "unmodeled_reason": reason,
                },
                "wait_anchor_false_hotspot": None,
                "wait_anchor_assessment": "not_evaluated",
                "wait_anchor_reason": "exact event/window Wait-Anchor attachment was not evaluated for this hotspot",
                "wait_anchor_evidence": [],
                "wait_anchor_scope": None,
                "evidence_locator": evidence,
            }
        )
    rows.sort(key=lambda item: (item["measured_device_ms_total"] or 0.0, item["kernel_name"]), reverse=True)
    return rows[:top_n]

def _clock_coverage(observation: Observation) -> dict:
    """Coverage of the exact clipped endpoints used by this window.

    The clock relation itself belongs to CLOCK's ``ClockDomain``.  This
    consumer asks that same relation to convert the clipped event endpoints
    and both window endpoints; it never reconstructs scale/offset/validity in
    the report.  A partially overlapping event is clipped first and then
    mapped, so the original window clipping is reused.
    """

    window = observation.window
    event_count = 0
    mapped_events = 0
    relation_events = 0
    endpoint_total = 0
    endpoint_mapped = 0
    local_ns = 0
    mapped_ns = 0
    domains: set[str] = set()
    references: set[str] = set()
    event_clocks: set[str] = set()
    gaps: list[dict] = []
    mapped_by_clock = 0
    clipped_clocks: list = []
    for index, event in enumerate(observation.events):
        clipped = event.clipped(window.start_ns, window.end_ns)
        if clipped is None:
            continue
        left, right = clipped
        event_count += 1
        endpoint_total += 2
        local_ns += max(0, right - left)
        domains.add(event.clock.domain)
        event_clocks.add(event.clock.domain)
        clipped_clocks.append(event.clock)
        if event.clock.comparable:
            relation_events += 1
            if event.clock.reference_domain is not None:
                references.add(str(event.clock.reference_domain))
        mapped_start = event.clock.to_reference_ns(left)
        mapped_end = event.clock.to_reference_ns(right)
        if mapped_start is not None and mapped_end is not None:
            mapped_events += 1
            endpoint_mapped += 2
            mapped_ns += max(0, mapped_end - mapped_start)
            mapped_by_clock += 1
        else:
            gaps.append({
                "code": (
                    "event_endpoint_outside_clock_validity"
                    if event.clock.comparable
                    else "clock_relation_unavailable"
                ),
                "scope": "event",
                "index": index,
                "event_id": event.event_id,
                "domain": event.clock.domain,
                "start_mapped": mapped_start is not None,
                "end_mapped": mapped_end is not None,
            })

    window_clock = window.clock
    if window_clock is None and len(event_clocks) == 1 and clipped_clocks:
        # Same single domain as the contributing events; this is the CLOCK
        # relation already carried by those events, not a new relation.
        window_clock = clipped_clocks[0]
    window_start_mapped = None
    window_end_mapped = None
    endpoint_total += 2
    if window_clock is None:
        gaps.append({
            "code": "window_clock_ambiguous" if event_clocks else "window_clock_unavailable",
            "scope": "window",
        })
    else:
        window_start_mapped = window_clock.to_reference_ns(window.start_ns)
        window_end_mapped = window_clock.to_reference_ns(window.end_ns)
        if window_start_mapped is not None and window_end_mapped is not None:
            endpoint_mapped += 2
        else:
            gaps.append({
                "code": (
                    "window_endpoint_outside_clock_validity"
                    if window_clock.comparable
                    else "window_clock_relation_unavailable"
                ),
                "scope": "window",
                "start_mapped": window_start_mapped is not None,
                "end_mapped": window_end_mapped is not None,
            })
        if window_clock.comparable and window_clock.reference_domain is not None:
            references.add(str(window_clock.reference_domain))

    if event_count == 0:
        status = "no_events"
        reason = "clock_coverage_no_events"
    elif (
        mapped_events == event_count
        and window_start_mapped is not None
        and window_end_mapped is not None
        and len(references) == 1
        and "unknown" not in domains
    ):
        status = "available"
        reason = ""
    else:
        status = "unavailable_clock_relation"
        reason = "clock_coverage_incomplete"
    return {
        "status": status,
        "reason": reason or None,
        "event_count": event_count,
        "total_event_count": event_count,
        "mapped_event_count": mapped_events,
        "unmapped_event_count": event_count - mapped_events,
        "relation_event_count": relation_events,
        # Kept for older C7 consumers; this is now the mapped endpoint count.
        "comparable_event_count": mapped_events,
        "total_endpoint_count": endpoint_total,
        "mapped_endpoint_count": endpoint_mapped,
        "unmapped_endpoint_count": endpoint_total - endpoint_mapped,
        "window_endpoint_count": 2,
        "mapped_window_endpoint_count": (
            int(window_start_mapped is not None) + int(window_end_mapped is not None)
        ),
        "window_start_mapped_ns": window_start_mapped,
        "window_end_mapped_ns": window_end_mapped,
        "local_duration_ms": round(local_ns / 1_000_000.0, 6) if event_count else None,
        "mapped_duration_ms": round(mapped_ns / 1_000_000.0, 6) if event_count else None,
        "domains": sorted(domains),
        "reference_domains": sorted(references),
        "reference_domain": next(iter(references)) if len(references) == 1 else None,
        "window_clock_domain": window_clock.domain if window_clock is not None else None,
        "gaps": gaps,
        "gap_codes": sorted({str(gap.get("code")) for gap in gaps if gap.get("code")}),
        "mapped_by_clock_count": mapped_by_clock,
        "source": "clipped_event_and_window_endpoints_via_clock_domain",
    }
