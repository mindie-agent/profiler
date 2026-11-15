"""Cross-rank union timeline accounting, straggler attribution, and EP load balance (cross_rank_clock).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting cross-rank union timeline accounting, straggler attribution, and ep load balance.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import statistics
from dataclasses import replace
from typing import Any, Iterable, Mapping, Sequence
from .accounting import account_window
from .events import ClockDomain, Event, Observation, Window

TRANSPORT_BANDWIDTH_FLOOR_GBPS: dict[str, float] = {
    "SDMA": 18.0,
    "RDMA": 21.0,
    "ROCE": 21.0,
    "HCCS": 25.0,
    "PCIE": 12.0,
}

MOE_OP_KEYWORDS = (
    "groupedmatmul",
    "grouped_matmul",
    "moedistributedispatch",
    "moedistributecombine",
    "moecomputeexperttokens",
    "moegatingtopksoftmax",
    "moetokenpermute",
    "moeinitrouting",
    "moe_token",
    "moe_gating",
    "moe_distribute",
)

def p50(values: Iterable[float | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return None
    return round(float(statistics.median(clean)), 6)

def _ms(value: int | float | None) -> float | None:
    return None if value is None else round(float(value) / 1_000_000.0, 6)

def _fmt_ms(value: float | None) -> str:
    return "unavailable" if value is None else f"{value:.3f} ms"

def _common_reference_domain(
    observations: Sequence[Observation],
) -> str | None:
    events = [event for obs in observations for event in obs.events]
    if not events:
        return None
    references = set()
    for event in events:
        clock = event.clock
        if not clock.comparable:
            return None
        references.add(str(clock.reference_domain))
    for obs in observations:
        window_clock = obs.window.clock
        if window_clock is not None:
            if not window_clock.comparable:
                return None
            references.add(str(window_clock.reference_domain))
    if len(references) != 1:
        return None
    return references.pop()

def _resolve_window_clock(
    obs: Observation,
) -> tuple[ClockDomain | None, str | None]:
    """Resolve the window's clock relation without using event order.

    An explicit Window.clock always wins.  Otherwise the relation is usable
    only when all contributing events declare one coordinate domain and the
    unique clock relation maps both window endpoints to one reference interval.
    Mixed domains or conflicting window mappings are ambiguous, not silently
    replaced by the first event's clock.
    """
    window = obs.window
    if window.clock is not None:
        if not window.clock.comparable:
            return None, "window_clock_not_comparable"
        start_ns = window.clock.to_reference_ns(window.start_ns)
        end_ns = window.clock.to_reference_ns(window.end_ns)
        if start_ns is None or end_ns is None or end_ns <= start_ns:
            return None, "window_clock_unmappable"
        return window.clock, None
    if not obs.events:
        return None, "no_events"
    domains = {event.clock.domain for event in obs.events}
    if len(domains) != 1:
        return None, "window_clock_ambiguous"
    candidates = sorted(
        {event.clock for event in obs.events},
        key=lambda clock: (
            clock.domain, clock.reference_domain or "",
            clock.reference_scale_num, clock.reference_scale_den,
            clock.offset_ns if clock.offset_ns is not None else 0,
            clock.valid_from_ns if clock.valid_from_ns is not None else -1,
            clock.valid_to_ns if clock.valid_to_ns is not None else -1,
        ),
    )
    mapped: dict[tuple[int, int], ClockDomain] = {}
    for clock in candidates:
        if not clock.comparable:
            continue
        start_ns = clock.to_reference_ns(window.start_ns)
        end_ns = clock.to_reference_ns(window.end_ns)
        if start_ns is None or end_ns is None or end_ns <= start_ns:
            continue
        mapped[(start_ns, end_ns)] = clock
    if not mapped:
        return None, "window_clock_unmappable"
    if len(mapped) > 1:
        return None, "window_clock_ambiguous"
    (_start, _end), clock = next(iter(mapped.items()))
    return clock, None

def _map_event_interval(
    obs: Observation,
    event: Event,
    window_clock: ClockDomain | None,
) -> tuple[int, int, str | None] | tuple[None, None, str]:
    """Map one event to the common reference after the correct clipping.

    Same-domain events are clipped in their local coordinates before mapping.
    Different-domain events are mapped first and clipped against the mapped
    window.  Without a provable window relation the full event interval is
    used only for metrics that do not need window endpoints; callers that do
    see the returned reason and withhold those facts.
    """
    clock = event.clock
    if not clock.comparable:
        return None, None, "no_reference_mapping"
    if window_clock is not None:
        if event.clock.domain == window_clock.domain:
            clipped = event.clipped(obs.window.start_ns, obs.window.end_ns)
            if clipped is None:
                return None, None, "outside_window"
            local_start, local_end = clipped
        else:
            mapped_start = clock.to_reference_ns(event.start_ns)
            mapped_end = clock.to_reference_ns(event.end_ns)
            window_start = window_clock.to_reference_ns(obs.window.start_ns)
            window_end = window_clock.to_reference_ns(obs.window.end_ns)
            if mapped_start is None or mapped_end is None:
                return None, None, "outside_validity"
            if window_start is None or window_end is None:
                return None, None, "window_clock_unmappable"
            local_start = max(mapped_start, window_start)
            local_end = min(mapped_end, window_end)
            if local_end <= local_start:
                return None, None, "outside_window"
            return int(local_start), int(local_end), None
    else:
        local_start, local_end = event.start_ns, event.end_ns
    mapped_start = clock.to_reference_ns(local_start)
    mapped_end = clock.to_reference_ns(local_end)
    if mapped_start is None or mapped_end is None:
        return None, None, "outside_validity"
    if mapped_end < mapped_start:
        return None, None, "mapping_unavailable"
    return int(mapped_start), int(mapped_end), None

def _preceding_projection(
    obs: Observation,
    reference: str | None,
) -> dict[str, Any] | None:
    """Map this observation's window and events for preceding-gap facts.

    A single missing non-comm interval marks only the preceding fact
    unavailable; it does not erase the mapped collective endpoints.
    """
    if reference is None or not obs.events:
        return None
    window_clock, window_reason = _resolve_window_clock(obs)
    if window_clock is None:
        return {
            "window": None,
            "mapped_by_id": {},
            "preceding_available": False,
            "reason": window_reason,
        }
    start_ns = window_clock.to_reference_ns(obs.window.start_ns)
    end_ns = window_clock.to_reference_ns(obs.window.end_ns)
    if start_ns is None or end_ns is None or end_ns <= start_ns:
        return {
            "window": None,
            "mapped_by_id": {},
            "preceding_available": False,
            "reason": "window_clock_unmappable",
        }
    mapped_by_id: dict[int, Event] = {}
    preceding_available = True
    for event in obs.events:
        mapped_start, mapped_end, _reason = _map_event_interval(
            obs, event, window_clock
        )
        if mapped_start is None or mapped_end is None:
            preceding_available = False
            continue
        mapped_by_id[id(event)] = replace(
            event, start_ns=mapped_start, end_ns=mapped_end
        )
    return {
        "window": Window(
            start_ns,
            end_ns,
            step=obs.window.step,
            label=obs.window.label,
            source=obs.window.source,
        ),
        "mapped_by_id": mapped_by_id,
        "preceding_available": preceding_available,
        "reason": None if preceding_available else "event_interval_unmappable",
    }

def _reference_projections(
    observations: Sequence[Observation],
) -> tuple[str, dict[int, dict[str, Any]]] | None:
    """Build mapped event/window/accounting copies for one common reference.

    Local Event/Window objects are never mutated.  Same-domain endpoints are
    clipped before mapping; cross-domain endpoints are mapped and clipped in
    the reference coordinate.  A contribution that cannot map is left out and
    marked incomplete; metrics that require complete coverage must check
    ``complete``.
    """
    reference = _common_reference_domain(observations)
    if reference is None:
        return None
    projections: dict[int, dict[str, Any]] = {}
    for obs in observations:
        if not obs.events:
            return None
        window_clock, window_reason = _resolve_window_clock(obs)
        mapped_events: list[Event] = []
        unmapped = 0
        for event in obs.events:
            mapped_start, mapped_end, _reason = _map_event_interval(
                obs, event, window_clock
            )
            if mapped_start is None or mapped_end is None:
                unmapped += 1
                continue
            mapped_events.append(
                replace(event, start_ns=mapped_start, end_ns=mapped_end)
            )
        if not mapped_events:
            return None
        if window_clock is not None:
            start_ns = window_clock.to_reference_ns(obs.window.start_ns)
            end_ns = window_clock.to_reference_ns(obs.window.end_ns)
        else:
            start_ns = min(event.start_ns for event in mapped_events)
            end_ns = max(event.end_ns for event in mapped_events)
        if start_ns is None or end_ns is None or end_ns <= start_ns:
            return None
        mapped_window = Window(
            start_ns,
            end_ns,
            step=obs.window.step,
            label=obs.window.label,
            source=obs.window.source,
        )
        projections[id(obs)] = {
            "reference_domain": reference,
            "events": mapped_events,
            "window": mapped_window,
            "accounting": account_window(mapped_events, mapped_window),
            "mapped_event_count": len(mapped_events),
            "unmapped_event_count": unmapped,
            "complete": unmapped == 0,
            "window_clock_reason": window_reason,
        }
    return reference, projections

def _observation_accounting(
    obs: Observation,
    projections: dict[int, dict[str, Any]] | None,
):
    if projections is None:
        return obs.accounting
    return projections[id(obs)]["accounting"]

def _local_moe_ms(obs: Observation) -> float | None:
    moe_ns = obs.accounting.block_union_ns.get("MoE") or 0
    if moe_ns > 0:
        return moe_ns / 1_000_000.0
    total = 0
    for event in obs.events:
        text = f"{event.op_type} {event.name}".lower()
        if event.block == "MoE" or any(kw in text for kw in MOE_OP_KEYWORDS):
            total += max(0, event.end_ns - event.start_ns)
    return total / 1_000_000.0 if total > 0 else None

def _metric(accounting, name: str) -> float | None:
    ns_name = f"{name}_ns"
    value = getattr(accounting, ns_name, None)
    return _ms(value)

def _block_ms(accounting, block: str) -> float | None:
    value = accounting.block_union_ns.get(block)
    return _ms(value)

def _block_share(accounting, block: str) -> float | None:
    return accounting.block_share_pct.get(block)

def _step_count(observations: Sequence[Observation]) -> int:
    return len({obs.window.step for obs in observations if obs.window.step is not None})

def cross_rank_union_span(
    observations: Sequence[Observation],
    *,
    reference_domain: str | None = None,
) -> dict[str, Any]:
    """Union span plus the coverage facts from one streaming clipped pass.

    The report/compare consumers need the selected window contribution count,
    how many contributions actually mapped their clipped endpoints, the
    declared/mapped reference domains, and why a span is unavailable.  This
    function computes those in the same pass; it never caches per-event
    intervals, maps an un-clipped endpoint, or turns a successful subset into a
    complete window.
    """
    rank_domains: dict[str, set[str]] = {}
    window_ranks: set[str] = set()
    mapped_ranks: set[str] = set()
    declared_references: set[str] = set()
    mapped_references: set[str] = set()
    window_keys: set[tuple[Any, Any, int, int]] = set()
    window_labels: set[str] = set()
    failure_reasons: dict[str, int] = {}

    def fail(reason: str) -> None:
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

    scanned_event_count = 0
    clipped_event_count = 0
    mapped_event_count = 0
    window_endpoint_count = 0
    mapped_window_endpoint_count = 0
    mapped_window_count = 0
    min_start_ns: int | None = None
    max_end_ns: int | None = None
    # One rolling pass: auxiliary memory is O(ranks + windows + reason codes),
    # never O(events or intervals).  Window endpoints participate in the same
    # common interval so an explicit window contributes its true extent (not
    # just the extent of surviving events).
    for obs in observations:
        window = obs.window
        window_keys.add(
            (window.step, window.label, int(window.start_ns), int(window.end_ns))
        )
        if window.label:
            window_labels.add(str(window.label))
        window_endpoint_count += 2
        window_clock, window_reason = _resolve_window_clock(obs)
        if window_clock is None:
            fail(window_reason or "window_clock_unavailable")
        else:
            mapped_window_start = window_clock.to_reference_ns(window.start_ns)
            mapped_window_end = window_clock.to_reference_ns(window.end_ns)
            if (
                mapped_window_start is None or mapped_window_end is None
                or mapped_window_end <= mapped_window_start
            ):
                fail("window_clock_unmappable")
            else:
                mapped_window_count += 1
                mapped_window_endpoint_count += 2
                declared_references.add(str(window_clock.reference_domain))
                mapped_references.add(str(window_clock.reference_domain))
                # An explicitly clocked window is itself part of the common
                # selected interval.  Implicit windows only contribute their
                # clipped events; otherwise caller padding would inflate span.
                if window.clock is not None:
                    min_start_ns = (
                        mapped_window_start if min_start_ns is None
                        else min(min_start_ns, mapped_window_start)
                    )
                    max_end_ns = (
                        mapped_window_end if max_end_ns is None
                        else max(max_end_ns, mapped_window_end)
                    )
        for event in obs.events:
            scanned_event_count += 1
            rank_domains.setdefault(obs.rank_id, set()).add(event.clock.domain)
            clipped = event.clipped(window.start_ns, window.end_ns)
            if clipped is None:
                continue
            clipped_event_count += 1
            window_ranks.add(obs.rank_id)
            clock = event.clock
            if not clock.comparable:
                fail("no_reference_mapping")
                continue
            declared_references.add(str(clock.reference_domain))
            start_ns, end_ns, reason = _map_event_interval(
                obs, event, window_clock
            )
            if start_ns is None or end_ns is None:
                fail(reason or "mapping_unavailable")
                continue
            mapped_event_count += 1
            mapped_ranks.add(obs.rank_id)
            mapped_references.add(str(clock.reference_domain))
            min_start_ns = start_ns if min_start_ns is None else min(min_start_ns, start_ns)
            max_end_ns = end_ns if max_end_ns is None else max(max_end_ns, end_ns)

    ordered_rank_domains = {
        rank: sorted(domains) for rank, domains in sorted(rank_domains.items())
    }
    unmapped_event_count = clipped_event_count - mapped_event_count
    mapped_rank_count = len(mapped_ranks)
    window_mapping_complete = mapped_window_count == len(observations)
    unmapped_rank_ids = sorted(window_ranks - mapped_ranks)
    declared_sorted = sorted(declared_references)
    mapped_sorted = sorted(mapped_references)
    actual_reference = (
        declared_sorted[0] if len(declared_sorted) == 1
        else mapped_sorted[0] if len(mapped_sorted) == 1
        else None
    )
    if len(declared_references) > 1:
        fail("reference_domain_mismatch")
    if reference_domain is not None and declared_references and (
        declared_sorted != [reference_domain]
    ):
        fail("requested_reference_domain_mismatch")
    if clipped_event_count == 0:
        fail("no_window_events")
    elif mapped_event_count == 0:
        fail("no_mapped_events")
    elif unmapped_event_count > 0:
        fail("partial_mapping")
    if not window_mapping_complete:
        fail("window_mapping_unavailable")

    if clipped_event_count == 0:
        reason = "no_window_events"
    elif len(declared_references) > 1:
        reason = "reference_domain_mismatch"
    elif reference_domain is not None and declared_references and (
        declared_sorted != [reference_domain]
    ):
        reason = "requested_reference_domain_mismatch"
    elif mapped_event_count == 0:
        reason = (
            "outside_validity" if failure_reasons.get("outside_validity")
            else "no_reference_mapping" if failure_reasons.get("no_reference_mapping")
            else "no_mapped_events"
        )
    elif unmapped_event_count > 0:
        reason = (
            "outside_validity" if failure_reasons.get("outside_validity")
            else "partial_mapping"
        )
    elif not window_mapping_complete:
        reason = "window_mapping_unavailable"
    elif len(declared_references) != 1:
        reason = "reference_domain_unavailable"
    else:
        reason = None

    common = {
        "clock_relation": "no_events" if clipped_event_count == 0 else (
            "sourced_reference" if reason is None else "unavailable_clock_relation"
        ),
        "requested_reference_domain": reference_domain,
        "actual_reference_domain": actual_reference,
        "declared_reference_domains": declared_sorted,
        "mapped_reference_domains": mapped_sorted,
        "reference_available": reason is None,
        "reason": reason,
        "failure_reason": reason,
        "failure_reasons": dict(sorted(failure_reasons.items())),
        "scanned_event_count": scanned_event_count,
        "event_count": clipped_event_count,
        "window_event_count": clipped_event_count,
        "mapped_event_count": mapped_event_count,
        "unmapped_event_count": unmapped_event_count,
        "endpoint_count": clipped_event_count * 2,
        "mapped_endpoint_count": mapped_event_count * 2,
        "window_endpoint_count": window_endpoint_count,
        "mapped_window_endpoint_count": mapped_window_endpoint_count,
        "mapped_window_count": mapped_window_count,
        "window_mapping_complete": window_mapping_complete,
        "mapped_rank_count": mapped_rank_count,
        "window_rank_count": len(window_ranks),
        "unmapped_rank_ids": unmapped_rank_ids,
        "window_count": len(window_keys),
        "window_labels": sorted(window_labels),
        "rank_count": len(rank_domains),
        "rank_domains": ordered_rank_domains,
    }
    if clipped_event_count == 0:
        return {
            **common,
            "status": "no_events",
            "reference_domain": None,
            "span_ns": None,
            "span_ms": None,
        }
    span_available = (
        reason is None
        and len(declared_references) == 1
        and min_start_ns is not None
        and max_end_ns is not None
        and mapped_event_count == clipped_event_count
        and window_mapping_complete
    )
    if not span_available:
        return {
            **common,
            "status": "unavailable_clock_relation",
            "reference_domain": None,
            "span_ns": None,
            "span_ms": None,
        }
    resolved_reference = next(iter(declared_references))
    span_ns = max_end_ns - min_start_ns
    return {
        **common,
        "status": "available",
        "reference_domain": resolved_reference,
        "span_ns": int(span_ns),
        "span_ms": _ms(span_ns),
    }

def aggregate_observations(observations: Sequence[Observation]) -> dict:
    reference_data = _reference_projections(observations)
    projections = reference_data[1] if reference_data is not None else None
    comparison_domain = reference_data[0] if reference_data is not None else "local"

    def accounting_for(obs: Observation):
        return _observation_accounting(obs, projections)

    usable = [obs for obs in observations if obs.accounting.available]
    steps = sorted({obs.window.step for obs in observations if obs.window.step is not None})
    comparison_complete = bool(projections is not None) and all(
        projections[id(obs)].get("complete", False) for obs in usable
    )
    comparison_unmapped = sum(
        projections[id(obs)].get("unmapped_event_count", 0)
        for obs in usable
    ) if projections is not None else 0
    return {
        "comparison_domain": comparison_domain,
        "comparison_complete": comparison_complete,
        "comparison_unmapped_event_count": comparison_unmapped,
        "observation_count": len(observations),
        "observations_with_data": len(usable),
        "step_count": len(steps),
        "rank_count": len({obs.rank_id for obs in observations}),
        "steady_steps": steps,
        "request_wall_ms_p50": p50(_metric(obs.accounting, "request_wall") for obs in usable),
        "observed_event_span_ms_p50": p50(_metric(accounting_for(obs), "observed_event_span") for obs in usable),
        "device_busy_union_ms_p50": p50(_metric(accounting_for(obs), "busy_union") for obs in usable),
        "device_activity_sum_ms_p50": p50(_metric(accounting_for(obs), "device_activity_sum") for obs in usable),
        "exposed_comm_ms_p50": p50(_metric(accounting_for(obs), "exposed_comm") for obs in usable),
        "device_uncovered_ms_p50": p50(_metric(accounting_for(obs), "device_uncovered") for obs in usable),
        "total_cost_ms_p50": p50(_metric(accounting_for(obs), "total_cost") for obs in usable),
        "clipped_event_count": sum(obs.accounting.clipped_event_count for obs in usable),
        "local_wall_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
        # Deprecated aliases.
        "wall_ms_p50": p50(_metric(accounting_for(obs), "observed_event_span") for obs in usable),
        "busy_union_ms_p50": p50(_metric(accounting_for(obs), "busy_union") for obs in usable),
        "kernel_sum_ms_p50": p50(_metric(accounting_for(obs), "device_activity_sum") for obs in usable),
        "host_gap_ms_p50": p50(_metric(accounting_for(obs), "device_uncovered") for obs in usable),
        "exposed_aicpu_ms_p50": p50(_metric(accounting_for(obs), "exposed_aicpu") for obs in usable),
        "underfeed_bubble_ratio_p50": p50(accounting_for(obs).underfeed_ratio for obs in usable),
        "aicpu_exposed_ratio_p50": p50(accounting_for(obs).aicpu_exposed_ratio for obs in usable),
        "coverage_ratio_p50": p50(accounting_for(obs).coverage_ratio for obs in usable),
    }
