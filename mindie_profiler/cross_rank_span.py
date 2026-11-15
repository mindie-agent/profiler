"""Cross-rank union timeline accounting, straggler attribution, and EP load balance (cross_rank_span).

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
from typing import Any, Iterable, Mapping, Sequence
from .classify import ALL_BLOCKS
from .events import ClockDomain, Event, Observation, Window

from .cross_rank_clock import (
    _block_ms, _block_share, _common_reference_domain, _metric,
    _observation_accounting, _preceding_projection, _reference_projections, p50,
)

def rank_summaries(observations: Sequence[Observation]) -> list[dict]:
    reference_data = _reference_projections(observations)
    projections = reference_data[1] if reference_data is not None else None
    comparison_domain = reference_data[0] if reference_data is not None else "local"

    def accounting_for(obs: Observation):
        return _observation_accounting(obs, projections)

    by_rank: dict[str, list[Observation]] = {}
    for obs in observations:
        by_rank.setdefault(obs.rank_id, []).append(obs)
    rows: list[dict] = []
    for rank_id in sorted(by_rank):
        group = by_rank[rank_id]
        usable = [obs for obs in group if obs.accounting.available]
        rank_index = next((obs.rank_index for obs in group if obs.rank_index is not None), None)
        comparison_complete = bool(projections is not None) and all(
            projections[id(obs)].get("complete", False) for obs in usable
        )
        comparison_unmapped = sum(
            projections[id(obs)].get("unmapped_event_count", 0)
            for obs in usable
        ) if projections is not None else 0
        row = {
            "rank": rank_index if rank_index is not None else rank_id,
            "rank_id": rank_id,
            "rank_index": rank_index,
            "observations": len(group),
            "observations_with_data": len(usable),
            "empty_windows": len(group) - len(usable),
            "steps": sorted({obs.window.step for obs in group if obs.window.step is not None}),
            "event_count": sum(obs.accounting.event_count for obs in group),
            "comm_event_count": sum(obs.accounting.comm_event_count for obs in group),
            "clipped_event_count": sum(obs.accounting.clipped_event_count for obs in group),
            "clock_domains": sorted({event.clock.domain for obs in group for event in obs.events}),
            "clock_reference_domains": sorted(
                {
                    event.clock.reference_domain
                    for obs in group
                    for event in obs.events
                    if event.clock.reference_domain is not None
                }
            ),
            "comparison_domain": comparison_domain,
            "comparison_complete": comparison_complete,
            "comparison_unmapped_event_count": comparison_unmapped,
            "request_wall_ms_p50": p50(_metric(obs.accounting, "request_wall") for obs in usable),
            "observed_event_span_ms_p50": p50(_metric(accounting_for(obs), "observed_event_span") for obs in usable),
            "device_busy_union_ms_p50": p50(_metric(accounting_for(obs), "busy_union") for obs in usable),
            "device_activity_sum_ms_p50": p50(_metric(accounting_for(obs), "device_activity_sum") for obs in usable),
            "exposed_comm_ms_p50": p50(_metric(accounting_for(obs), "exposed_comm") for obs in usable),
            "device_uncovered_ms_p50": p50(_metric(accounting_for(obs), "device_uncovered") for obs in usable),
            "total_cost_ms_p50": p50(_metric(accounting_for(obs), "total_cost") for obs in usable),
            "wall_ms_p50": p50(_metric(accounting_for(obs), "observed_event_span") for obs in usable),
            "busy_union_ms_p50": p50(_metric(accounting_for(obs), "busy_union") for obs in usable),
            "kernel_sum_ms_p50": p50(_metric(accounting_for(obs), "device_activity_sum") for obs in usable),
            "host_gap_ms_p50": p50(_metric(accounting_for(obs), "device_uncovered") for obs in usable),
            "underfeed_bubble_ratio_p50": p50(accounting_for(obs).underfeed_ratio for obs in usable),
            "aicpu_exposed_ratio_p50": p50(accounting_for(obs).aicpu_exposed_ratio for obs in usable),
            "coverage_ratio_p50": p50(accounting_for(obs).coverage_ratio for obs in usable),
            "local_wall_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
            "local_block_union_ms_p50": {
                block: p50(_block_ms(obs.accounting, block) for obs in usable) for block in ALL_BLOCKS
            },
            "block_union_ms_p50": {
                block: p50(_block_ms(accounting_for(obs), block) for obs in usable) for block in ALL_BLOCKS
            },
            "block_share_pct_p50": {
                block: p50(_block_share(accounting_for(obs), block) for obs in usable) for block in ALL_BLOCKS
            },
        }
        rows.append(row)
    return rows

def slowest_rank(summaries: Sequence[dict]) -> dict | None:
    candidates = [row for row in summaries if row.get("wall_ms_p50") is not None]
    if not candidates:
        return None
    slowest = max(candidates, key=lambda row: (row["wall_ms_p50"], row.get("busy_union_ms_p50") or 0.0, row["rank_id"]))
    others = [row for row in summaries if row["rank_id"] != slowest["rank_id"]]
    excesses: list[tuple[float, str]] = []
    for block in ALL_BLOCKS:
        mine = slowest["block_union_ms_p50"].get(block)
        peers = [row["block_union_ms_p50"].get(block) for row in others]
        peers = [value for value in peers if value is not None]
        if mine is None or not peers:
            continue
        baseline = float(statistics.median(peers))
        excesses.append((round(mine - baseline, 6), block))
    dominant = max(excesses, default=None)
    return {
        "rank": slowest["rank"],
        "rank_id": slowest["rank_id"],
        "rank_index": slowest["rank_index"],
        "wall_ms_p50": slowest["wall_ms_p50"],
        "busy_union_ms_p50": slowest["busy_union_ms_p50"],
        "dominant_excess_block": dominant[1] if dominant and dominant[0] > 0 else None,
        "dominant_excess_ms": dominant[0] if dominant and dominant[0] > 0 else None,
        "baseline_rank_count": len(others),
        "dominant_excess_reason": (
            None
            if dominant and dominant[0] > 0
            else ("no comparable rank/block median" if not excesses else "slowest rank has no positive block excess")
        ),
    }

def _normalize_collective_name(event_name: str, op_type: str) -> str:
    raw = (op_type or event_name or "collective").lower()
    for kind in ("allreduce", "allgather", "reducescatter", "alltoallv", "alltoall", "broadcast", "send", "recv"):
        if kind in raw.replace("_", ""):
            return f"hcom_{kind}"
    return op_type or event_name or "collective"

def _extract_collective_groups_from_observations(
    observations: Sequence[Observation],
) -> list[dict[str, Any]]:
    reference = _common_reference_domain(observations)
    projections = {
        id(obs): _preceding_projection(obs, reference) for obs in observations
    } if reference is not None else {}
    by_window_rank: dict[tuple[int | None, str], list[tuple[Observation, list[Event]]]] = {}
    for obs in observations:
        comm_events = sorted(
            [ev for ev in obs.events if ev.is_comm or ev.block == "Comm"],
            key=lambda e: (e.start_ns, e.end_ns, str(e.task_id or "")),
        )
        if not comm_events:
            continue
        win_key = (obs.window.step, obs.window.label or f"{obs.window.start_ns}_{obs.window.end_ns}")
        by_window_rank.setdefault(win_key, []).append((obs, comm_events))

    groups: list[dict[str, Any]] = []
    for (step, win_label), rank_entries in sorted(by_window_rank.items(), key=lambda x: (x[0][0] or -1, x[0][1])):
        if len(rank_entries) < 2:
            continue
        # Group per-rank communication events by normalized collective kind and ordinal index
        per_rank_by_kind: dict[str, dict[str, list[tuple[Observation, Event]]]] = {}
        for obs, comm_evs in rank_entries:
            for ev in comm_evs:
                kind = _normalize_collective_name(ev.name, ev.op_type)
                per_rank_by_kind.setdefault(kind, {}).setdefault(obs.rank_id, []).append((obs, ev))

        for kind, rank_map in sorted(per_rank_by_kind.items()):
            if len(rank_map) < 2:
                continue
            min_len = min(len(items) for items in rank_map.values())
            for ordinal in range(min_len):
                participants: list[dict[str, Any]] = []
                for rank_id in sorted(rank_map):
                    obs, ev = rank_map[rank_id][ordinal]
                    projection = projections.get(id(obs))
                    if projection is not None and projection["preceding_available"]:
                        mapped_by_id = projection["mapped_by_id"]
                        compare_ev = mapped_by_id.get(id(ev), ev)
                        compare_window = projection["window"]
                        compare_events = [
                            mapped_by_id.get(id(original), original)
                            for original in obs.events
                        ]
                        time_domain = "reference"
                    elif projection is not None:
                        compare_ev = ev
                        compare_window = obs.window
                        compare_events = obs.events
                        time_domain = "unavailable"
                    else:
                        compare_ev = ev
                        compare_window = obs.window
                        compare_events = obs.events
                        time_domain = "local"
                    pre_compute = [
                        k for k in compare_events
                        if not k.is_comm and k.start_ns < compare_ev.start_ns
                    ]
                    pre_compute_ns = sum(
                        max(0, min(k.end_ns, compare_ev.start_ns) - k.start_ns)
                        for k in pre_compute
                    )
                    win_elapsed_ns = max(0, compare_ev.start_ns - compare_window.start_ns)
                    pre_host_gap_ns = max(0, win_elapsed_ns - pre_compute_ns)
                    local_pre_compute = [
                        k for k in obs.events
                        if not k.is_comm and k.start_ns < ev.start_ns
                    ]
                    local_pre_compute_ns = sum(
                        max(0, min(k.end_ns, ev.start_ns) - k.start_ns)
                        for k in local_pre_compute
                    )
                    local_host_gap_ns = max(
                        0, ev.start_ns - obs.window.start_ns - local_pre_compute_ns
                    )
                    participants.append(
                        {
                            "rank_id": rank_id,
                            "rank_index": obs.rank_index,
                            "start_ns": int(ev.start_ns),
                            "end_ns": int(ev.end_ns),
                            "clock": ev.clock,
                            "wait_ns": int(ev.wait_ns) if ev.wait_ns is not None else None,
                            "preceding_compute_ns": pre_compute_ns,
                            "preceding_host_gap_ns": pre_host_gap_ns,
                            "local_preceding_compute_ns": local_pre_compute_ns,
                            "local_preceding_host_gap_ns": local_host_gap_ns,
                            "time_domain": time_domain,
                        }
                    )
                groups.append(
                    {
                        "step": step,
                        "window_label": win_label,
                        "collective_op": kind,
                        "ordinal": ordinal,
                        "ranks": participants,
                    }
                )
    return groups

def _empty_straggler_result() -> dict[str, Any]:
    return {
        "status": "not_applicable", "collective_count": 0, "primary_classification": None,
        "primary_straggler_rank_id": None, "primary_straggler_cause": None,
        "primary_victim_rank_ids": [], "primary_slow_link_ranks": [],
        "perpetrator_vote_counts": {}, "collectives": [], "findings": [],
        "clock_unverified_groups": 0,
        "link_attribution_unknown_groups": 0,
    }

def _to_ns(mapping: Mapping[str, Any], ns_key: str, us_key: str, ms_key: str) -> int | None:
    if mapping.get(ns_key) is not None:
        return int(mapping[ns_key])
    if mapping.get(us_key) is not None:
        return int(round(float(mapping[us_key]) * 1000.0))
    if mapping.get(ms_key) is not None:
        return int(round(float(mapping[ms_key]) * 1_000_000.0))
    return None
