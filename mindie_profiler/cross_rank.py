"""Cross-rank p50 statistics, slow-rank vs slow-link attribution, and MoE EP balance.

[Role]
  Aggregate per-window observations into per-rank and per-step medians, find
  the slowest rank by wall p50, separate collective ``slow_rank`` (compute or
  host-dispatch straggler causing peer wait) from ``slow_link`` (communication
  transport bottleneck), and evaluate MoE Expert Parallelism (EP) load balance
  and dual-stream communication-compute masking.

[Invariants]
  * Every statistic is computed from measured window observations or explicit
    records; missing values stay ``None`` and are never fabricated as 0.
  * ``slow_rank`` identifies the latest-entering rank (shortest collective
    duration, largest preceding compute/host lag) as the perpetrator and
    earliest-entering ranks (longest collective wait) as victims.
  * No thermal/power conclusion is drawn from timing alone.

[Timeouts & Locks]
  O(N log N) medians and linear collective/MoE scans over bounded observations;
  no I/O, subprocesses, or locks.

[Side-Effect Policy]
  Pure computation over immutable observations and mappings.
"""

from __future__ import annotations

import re
import statistics
from typing import Any, Iterable, Mapping, Sequence

from .classify import ALL_BLOCKS
from .events import Event, Observation

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


def aggregate_observations(observations: Sequence[Observation]) -> dict:
    usable = [obs for obs in observations if obs.accounting.available]
    steps = sorted({obs.window.step for obs in observations if obs.window.step is not None})
    return {
        "observation_count": len(observations),
        "observations_with_data": len(usable),
        "step_count": len(steps),
        "rank_count": len({obs.rank_id for obs in observations}),
        "steady_steps": steps,
        "request_wall_ms_p50": p50(_metric(obs.accounting, "request_wall") for obs in usable),
        "observed_event_span_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
        "device_busy_union_ms_p50": p50(_metric(obs.accounting, "busy_union") for obs in usable),
        "device_activity_sum_ms_p50": p50(_metric(obs.accounting, "device_activity_sum") for obs in usable),
        "exposed_comm_ms_p50": p50(_metric(obs.accounting, "exposed_comm") for obs in usable),
        "device_uncovered_ms_p50": p50(_metric(obs.accounting, "device_uncovered") for obs in usable),
        "total_cost_ms_p50": p50(_metric(obs.accounting, "total_cost") for obs in usable),
        "clipped_event_count": sum(obs.accounting.clipped_event_count for obs in usable),
        # Deprecated aliases.
        "wall_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
        "busy_union_ms_p50": p50(_metric(obs.accounting, "busy_union") for obs in usable),
        "kernel_sum_ms_p50": p50(_metric(obs.accounting, "device_activity_sum") for obs in usable),
        "host_gap_ms_p50": p50(_metric(obs.accounting, "device_uncovered") for obs in usable),
        "exposed_aicpu_ms_p50": p50(_metric(obs.accounting, "exposed_aicpu") for obs in usable),
        "underfeed_bubble_ratio_p50": p50(obs.accounting.underfeed_ratio for obs in usable),
        "aicpu_exposed_ratio_p50": p50(obs.accounting.aicpu_exposed_ratio for obs in usable),
        "coverage_ratio_p50": p50(obs.accounting.coverage_ratio for obs in usable),
    }


def rank_summaries(observations: Sequence[Observation]) -> list[dict]:
    by_rank: dict[str, list[Observation]] = {}
    for obs in observations:
        by_rank.setdefault(obs.rank_id, []).append(obs)
    rows: list[dict] = []
    for rank_id in sorted(by_rank):
        group = by_rank[rank_id]
        usable = [obs for obs in group if obs.accounting.available]
        rank_index = next((obs.rank_index for obs in group if obs.rank_index is not None), None)
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
            "request_wall_ms_p50": p50(_metric(obs.accounting, "request_wall") for obs in usable),
            "observed_event_span_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
            "device_busy_union_ms_p50": p50(_metric(obs.accounting, "busy_union") for obs in usable),
            "device_activity_sum_ms_p50": p50(_metric(obs.accounting, "device_activity_sum") for obs in usable),
            "exposed_comm_ms_p50": p50(_metric(obs.accounting, "exposed_comm") for obs in usable),
            "device_uncovered_ms_p50": p50(_metric(obs.accounting, "device_uncovered") for obs in usable),
            "total_cost_ms_p50": p50(_metric(obs.accounting, "total_cost") for obs in usable),
            "wall_ms_p50": p50(_metric(obs.accounting, "observed_event_span") for obs in usable),
            "busy_union_ms_p50": p50(_metric(obs.accounting, "busy_union") for obs in usable),
            "kernel_sum_ms_p50": p50(_metric(obs.accounting, "device_activity_sum") for obs in usable),
            "host_gap_ms_p50": p50(_metric(obs.accounting, "device_uncovered") for obs in usable),
            "underfeed_bubble_ratio_p50": p50(obs.accounting.underfeed_ratio for obs in usable),
            "aicpu_exposed_ratio_p50": p50(obs.accounting.aicpu_exposed_ratio for obs in usable),
            "coverage_ratio_p50": p50(obs.accounting.coverage_ratio for obs in usable),
            "block_union_ms_p50": {
                block: p50(_block_ms(obs.accounting, block) for obs in usable) for block in ALL_BLOCKS
            },
            "block_share_pct_p50": {
                block: p50(_block_share(obs.accounting, block) for obs in usable) for block in ALL_BLOCKS
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
                    # Compute preceding non-comm busy duration and uncovered gap before ev.start_ns
                    pre_compute = [
                        k for k in obs.events
                        if not k.is_comm and k.start_ns < ev.start_ns
                    ]
                    pre_compute_ns = sum(max(0, min(k.end_ns, ev.start_ns) - k.start_ns) for k in pre_compute)
                    win_elapsed_ns = max(0, ev.start_ns - obs.window.start_ns)
                    pre_host_gap_ns = max(0, win_elapsed_ns - pre_compute_ns)
                    participants.append(
                        {
                            "rank_id": rank_id,
                            "rank_index": obs.rank_index,
                            "start_ns": int(ev.start_ns),
                            "end_ns": int(ev.end_ns),
                            "wait_ns": int(ev.wait_ns) if ev.wait_ns is not None else None,
                            "preceding_compute_ns": pre_compute_ns,
                            "preceding_host_gap_ns": pre_host_gap_ns,
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
    }


def _to_ns(mapping: Mapping[str, Any], ns_key: str, us_key: str, ms_key: str) -> int | None:
    if mapping.get(ns_key) is not None:
        return int(mapping[ns_key])
    if mapping.get(us_key) is not None:
        return int(round(float(mapping[us_key]) * 1000.0))
    if mapping.get(ms_key) is not None:
        return int(round(float(mapping[ms_key]) * 1_000_000.0))
    return None


def attribute_cluster_stragglers_and_links(
    observations: Sequence[Observation] | None = None,
    *,
    collective_groups: Sequence[Mapping[str, Any]] | None = None,
    min_skew_ms: float = 0.005,
    entry_skew_share_threshold: float = 0.30,
    tight_exit_ratio_threshold: float = 0.35,
) -> dict[str, Any]:
    """Orthogonally separate Slow Rank (compute/host straggler) from Slow Link (transport bottleneck)."""
    raw_groups: list[Mapping[str, Any]] = []
    if collective_groups is not None:
        raw_groups.extend(collective_groups)
    elif observations is not None:
        raw_groups.extend(_extract_collective_groups_from_observations(observations))
    if not raw_groups:
        return _empty_straggler_result()

    evaluated: list[dict[str, Any]] = []
    vote_counts: dict[str, int] = {}
    cause_votes: dict[str, dict[str, int]] = {}
    victim_set: set[str] = set()
    slow_link_ranks: set[str] = set()
    classification_counts: dict[str, int] = {"slow_rank": 0, "slow_link": 0, "mixed_straggler_and_link": 0, "balanced": 0}

    for idx, group in enumerate(raw_groups):
        ranks_raw = group.get("ranks") or []
        if len(ranks_raw) < 2:
            continue
        rows: list[dict[str, Any]] = []
        for r in ranks_raw:
            s_ns = _to_ns(r, "start_ns", "start_us", "start_ms") or 0
            e_ns = _to_ns(r, "end_ns", "end_us", "end_ms")
            if e_ns is None:
                e_ns = s_ns + (_to_ns(r, "duration_ns", "duration_us", "duration_ms") or 0)
            dur_ns = max(0, e_ns - s_ns)
            rows.append(
                {
                    "rank_id": str(r.get("rank_id") if r.get("rank_id") is not None else f"rank_{r.get('rank', 0)}"),
                    "rank_index": r.get("rank_index", r.get("rank")),
                    "start_ns": s_ns,
                    "end_ns": e_ns,
                    "duration_ns": dur_ns,
                    "explicit_wait_ns": _to_ns(r, "wait_ns", "wait_us", "wait_ms"),
                    "explicit_transit_ns": _to_ns(r, "transit_ns", "transit_us", "transit_ms"),
                    "preceding_compute_ns": _to_ns(r, "preceding_compute_ns", "preceding_compute_us", "preceding_compute_ms"),
                    "preceding_host_gap_ns": _to_ns(r, "preceding_host_gap_ns", "preceding_host_gap_us", "preceding_host_gap_ms"),
                    "retry": int(r.get("retry") or 0),
                    "relay": int(r.get("relay") or 0),
                    "transport": str(r.get("transport") or group.get("transport") or "").upper() or None,
                    "size_bytes": int(r.get("size_bytes") or group.get("size_bytes") or 0) or None,
                }
            )

        min_start = min(r["start_ns"] for r in rows)
        max_start = max(r["start_ns"] for r in rows)
        min_end = min(r["end_ns"] for r in rows)
        max_end = max(r["end_ns"] for r in rows)
        min_dur = min(r["duration_ns"] for r in rows)
        max_dur = max(r["duration_ns"] for r in rows)

        launch_skew_ns = max_start - min_start
        end_skew_ns = max_end - min_end
        dur_skew_ns = max_dur - min_dur

        explicit_transits = [r["explicit_transit_ns"] for r in rows if r["explicit_transit_ns"] is not None]
        transit_ns = int(statistics.median(explicit_transits)) if explicit_transits else min_dur
        launch_skew_ms = _ms(launch_skew_ns) or 0.0
        end_skew_ms = _ms(end_skew_ns) or 0.0
        dur_skew_ms = _ms(dur_skew_ns) or 0.0
        transit_ms = _ms(transit_ns) or 0.0
        max_dur_ms = _ms(max_dur) or 0.0

        # Check transport bandwidth and hardware retry indicators
        size_bytes = next((r["size_bytes"] for r in rows if r["size_bytes"] is not None), None)
        transport = next((r["transport"] for r in rows if r["transport"] is not None), None)
        bw_gbps: float | None = None
        bw_degraded = False
        if size_bytes is not None and transit_ns > 0:
            bw_gbps = round(float(size_bytes) / float(transit_ns), 4)  # bytes/ns == GB/s
            floor = TRANSPORT_BANDWIDTH_FLOOR_GBPS.get(transport or "SDMA", 18.0)
            if bw_gbps < floor:
                bw_degraded = True
        has_retry = any(r["retry"] > 0 for r in rows)

        earliest_rank = min(rows, key=lambda r: (r["start_ns"], -r["duration_ns"], r["rank_id"]))
        latest_rank = max(rows, key=lambda r: (r["start_ns"], -r["duration_ns"], r["rank_id"]))
        slowest_completing_rank = max(rows, key=lambda r: (r["end_ns"] - max_start, r["duration_ns"], r["rank_id"]))

        entry_skew_dominant = (
            launch_skew_ms >= min_skew_ms
            and max_dur_ms > 0
            and (launch_skew_ms / max_dur_ms) >= entry_skew_share_threshold
            and earliest_rank["rank_id"] != latest_rank["rank_id"]
        )
        tight_exit = end_skew_ms <= max(0.002, tight_exit_ratio_threshold * launch_skew_ms)
        exit_or_link_skew = (
            end_skew_ms >= min_skew_ms
            or dur_skew_ms >= min_skew_ms
            or bw_degraded
            or has_retry
        )

        perpetrator_id: str | None = None
        straggler_cause: str | None = None
        victims: list[str] = []
        link_bottleneck_ranks: list[str] = []
        transport_anomaly: str | None = None

        if entry_skew_dominant and tight_exit and not has_retry and not bw_degraded:
            classification = "slow_rank"
            perpetrator_id = latest_rank["rank_id"]
            victims = [
                r["rank_id"]
                for r in rows
                if r["rank_id"] != perpetrator_id
                and (max_start - r["start_ns"]) >= int(0.25 * launch_skew_ns)
            ]
            # Sub-attribute compute_straggler vs host_dispatch_straggler
            peers = [r for r in rows if r["rank_id"] != perpetrator_id]
            peer_comp = [r["preceding_compute_ns"] for r in peers if r["preceding_compute_ns"] is not None]
            peer_gap = [r["preceding_host_gap_ns"] for r in peers if r["preceding_host_gap_ns"] is not None]
            perp_comp = latest_rank["preceding_compute_ns"]
            perp_gap = latest_rank["preceding_host_gap_ns"]
            comp_excess = (perp_comp - statistics.median(peer_comp)) if (perp_comp is not None and peer_comp) else 0.0
            gap_excess = (perp_gap - statistics.median(peer_gap)) if (perp_gap is not None and peer_gap) else 0.0
            if gap_excess > comp_excess and gap_excess > 0:
                straggler_cause = "host_dispatch_straggler"
            else:
                straggler_cause = "compute_straggler"
            vote_counts[perpetrator_id] = vote_counts.get(perpetrator_id, 0) + 1
            cause_votes.setdefault(perpetrator_id, {})[straggler_cause] = (
                cause_votes.get(perpetrator_id, {}).get(straggler_cause, 0) + 1
            )
            victim_set.update(victims)
        elif not entry_skew_dominant and exit_or_link_skew:
            classification = "slow_link"
            if has_retry:
                transport_anomaly = "rdma_retransmission"
            elif bw_degraded:
                transport_anomaly = "low_link_bandwidth"
            else:
                transport_anomaly = "asymmetric_link_completion"
            # Identify rank(s) with abnormally long transit or retry
            retry_ranks = [r["rank_id"] for r in rows if r["retry"] > 0]
            if retry_ranks:
                link_bottleneck_ranks = sorted(set(retry_ranks))
            elif dur_skew_ns > 0:
                threshold_dur = min_dur + 0.5 * dur_skew_ns
                link_bottleneck_ranks = sorted(
                    r["rank_id"] for r in rows if r["duration_ns"] >= threshold_dur and r["duration_ns"] > min_dur
                )
            if not link_bottleneck_ranks:
                link_bottleneck_ranks = [slowest_completing_rank["rank_id"]]
            slow_link_ranks.update(link_bottleneck_ranks)
        elif entry_skew_dominant and exit_or_link_skew:
            classification = "mixed_straggler_and_link"
            perpetrator_id = latest_rank["rank_id"]
            straggler_cause = "compute_straggler"
            victims = [r["rank_id"] for r in rows if r["rank_id"] != perpetrator_id]
            link_bottleneck_ranks = [slowest_completing_rank["rank_id"]]
            vote_counts[perpetrator_id] = vote_counts.get(perpetrator_id, 0) + 1
            victim_set.update(victims)
            slow_link_ranks.update(link_bottleneck_ranks)
        else:
            classification = "balanced"

        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        evaluated.append(
            {
                "collective_index": idx,
                "step": group.get("step"),
                "collective_op": str(group.get("collective_op") or group.get("op_name") or "collective"),
                "classification": classification,
                "launch_skew_ms": launch_skew_ms,
                "end_skew_ms": end_skew_ms,
                "duration_skew_ms": dur_skew_ms,
                "transit_duration_ms": transit_ms,
                "max_duration_ms": max_dur_ms,
                "effective_bandwidth_gbps": bw_gbps,
                "transport": transport,
                "perpetrator_rank_id": perpetrator_id,
                "straggler_cause": straggler_cause,
                "victim_rank_ids": victims,
                "link_bottleneck_rank_ids": link_bottleneck_ranks,
                "transport_anomaly": transport_anomaly,
            }
        )

    if not evaluated:
        return _empty_straggler_result()

    primary_straggler: str | None = None
    primary_cause: str | None = None
    if vote_counts:
        primary_straggler = max(sorted(vote_counts), key=lambda r: vote_counts[r])
        causes = cause_votes.get(primary_straggler, {})
        if causes:
            primary_cause = max(sorted(causes), key=lambda c: causes[c])

    if classification_counts["slow_rank"] > 0 and classification_counts["slow_rank"] >= classification_counts["slow_link"]:
        primary_class = "slow_rank"
    elif classification_counts["slow_link"] > 0:
        primary_class = "slow_link"
    elif classification_counts["mixed_straggler_and_link"] > 0:
        primary_class = "mixed_straggler_and_link"
    else:
        primary_class = "balanced"

    findings: list[dict[str, Any]] = []
    if primary_class == "slow_rank" and primary_straggler is not None:
        sample = next(c for c in evaluated if c["perpetrator_rank_id"] == primary_straggler)
        findings.append(
            {
                "finding_type": "cluster_slow_rank_straggler",
                "severity": "high",
                "confidence": "high",
                "summary": (
                    f"Collective wait is caused by Slow Rank {primary_straggler} ({primary_cause}, "
                    f"entry skew {sample['launch_skew_ms']:.3f} ms vs exit skew {sample['end_skew_ms']:.3f} ms); "
                    f"early-arriving victim ranks {sorted(victim_set)} are waiting, not link-bottlenecked."
                ),
                "evidence_ref": primary_cause or "slow_rank",
                "evidence_scope": {
                    "perpetrator_rank_id": primary_straggler,
                    "victim_rank_ids": sorted(victim_set),
                    "step": sample["step"],
                    "collective_op": sample["collective_op"],
                },
            }
        )
    elif primary_class == "slow_link":
        sample = next(c for c in evaluated if c["classification"] == "slow_link")
        findings.append(
            {
                "finding_type": "cluster_slow_communication_link",
                "severity": "high",
                "confidence": "high",
                "summary": (
                    f"Collective bottleneck is a Slow Link ({sample['transport_anomaly']}, "
                    f"entry skew {sample['launch_skew_ms']:.3f} ms, transit {sample['transit_duration_ms']:.3f} ms, "
                    f"exit skew {sample['end_skew_ms']:.3f} ms) on ranks {sorted(slow_link_ranks)}."
                ),
                "evidence_ref": sample["transport_anomaly"] or "slow_link",
                "evidence_scope": {
                    "bottleneck_rank_ids": sorted(slow_link_ranks),
                    "step": sample["step"],
                    "collective_op": sample["collective_op"],
                },
            }
        )

    return {
        "status": "detected" if primary_class in {"slow_rank", "slow_link", "mixed_straggler_and_link"} else "balanced",
        "collective_count": len(evaluated),
        "classification_counts": classification_counts,
        "primary_classification": primary_class,
        "primary_straggler_rank_id": primary_straggler,
        "primary_straggler_cause": primary_cause,
        "primary_victim_rank_ids": sorted(victim_set),
        "primary_slow_link_ranks": sorted(slow_link_ranks),
        "perpetrator_vote_counts": vote_counts,
        "collectives": evaluated,
        "findings": findings,
    }


def _parse_routed_tokens_from_shapes(input_shapes: str | None) -> int | None:
    """Extract total routed expert tokens from GroupedMatmul/MoE input_shapes."""
    if not input_shapes:
        return None
    cleaned = input_shapes.strip().strip('"').strip("'")
    if not cleaned:
        return None
    parts = [p.strip().strip("[]()") for p in cleaned.split(";") if p.strip()]
    if not parts:
        return None
    first_dims: list[int] = []
    for part in parts:
        dims = [tok.strip() for tok in part.split(",") if tok.strip()]
        if len(dims) == 2 and dims[0].isdigit():
            val = int(dims[0])
            if val > 0:
                first_dims.append(val)
    if not first_dims:
        return None
    # For single MatMul [M, K];[K, N], first tensor dim[0] is M tokens.
    # For multi-tensor GroupedMatmul list of expert activations, sum dynamic M dims if > 2 tensors.
    return first_dims[0] if len(first_dims) <= 2 else sum(first_dims)


def evaluate_ep_load_balance(
    observations: Sequence[Observation] | None = None,
    *,
    expert_loads: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    cv_threshold: float = 0.15,
    straggler_ratio_threshold: float = 1.20,
) -> dict[str, Any]:
    """Evaluate MoE Expert Parallelism (EP) cross-rank token/duration balance and comm masking ratio."""
    by_rank_tokens: dict[str, list[float]] = {}
    by_rank_moe_ms: dict[str, list[float]] = {}
    by_rank_masking: dict[str, list[float]] = {}
    dual_stream_overlap = False

    if isinstance(expert_loads, Mapping):
        for rank_key, val in expert_loads.items():
            rk = str(rank_key)
            if isinstance(val, (int, float)):
                by_rank_tokens.setdefault(rk, []).append(float(val))
            elif isinstance(val, Mapping):
                if val.get("tokens") is not None or val.get("routed_tokens") is not None:
                    by_rank_tokens.setdefault(rk, []).append(float(val.get("tokens") or val.get("routed_tokens")))
                if val.get("moe_compute_ms") is not None:
                    by_rank_moe_ms.setdefault(rk, []).append(float(val["moe_compute_ms"]))
                if val.get("comm_masking_ratio") is not None:
                    by_rank_masking.setdefault(rk, []).append(float(val["comm_masking_ratio"]))
                elif val.get("comm_union_ms") is not None and val.get("exposed_comm_ms") is not None:
                    cu = float(val["comm_union_ms"])
                    ec = float(val["exposed_comm_ms"])
                    if cu > 0:
                        ratio = max(0.0, min(1.0, (cu - ec) / cu))
                        by_rank_masking.setdefault(rk, []).append(ratio)
                        if ratio > 0.05:
                            dual_stream_overlap = True
    elif isinstance(expert_loads, Sequence):
        for row in expert_loads:
            if not isinstance(row, Mapping):
                continue
            rk = str(row.get("rank_id") or (f"rank_{row['rank']}" if row.get("rank") is not None else "rank_0"))
            tok = row.get("tokens") if row.get("tokens") is not None else row.get("routed_tokens")
            if tok is not None:
                by_rank_tokens.setdefault(rk, []).append(float(tok))
            if row.get("moe_compute_ms") is not None:
                by_rank_moe_ms.setdefault(rk, []).append(float(row["moe_compute_ms"]))
            if row.get("comm_masking_ratio") is not None:
                r_val = float(row["comm_masking_ratio"])
                by_rank_masking.setdefault(rk, []).append(r_val)
                if r_val > 0.05:
                    dual_stream_overlap = True
            elif row.get("comm_union_ms") is not None and row.get("exposed_comm_ms") is not None:
                cu = float(row["comm_union_ms"])
                ec = float(row["exposed_comm_ms"])
                if cu > 0:
                    r_val = max(0.0, min(1.0, (cu - ec) / cu))
                    by_rank_masking.setdefault(rk, []).append(r_val)
                    if r_val > 0.05:
                        dual_stream_overlap = True

    if observations:
        for obs in observations:
            if not obs.accounting.available:
                continue
            rk = str(obs.rank_id)
            moe_union_ns = obs.accounting.block_union_ns.get("MoE") or 0
            comm_union_ns = obs.accounting.block_union_ns.get("Comm") or 0
            exposed_comm_ns = obs.accounting.exposed_comm_ns or 0
            if comm_union_ns > 0:
                masked_ns = max(0, comm_union_ns - exposed_comm_ns)
                mask_ratio = masked_ns / float(comm_union_ns)
                by_rank_masking.setdefault(rk, []).append(mask_ratio)
                if masked_ns > 0 and obs.accounting.stream_count >= 2:
                    dual_stream_overlap = True

            step_tokens = 0
            has_tokens = False
            moe_kernel_ns = 0
            for ev in obs.events:
                text = f"{ev.op_type} {ev.name}".lower()
                is_moe = ev.block == "MoE" or any(kw in text for kw in MOE_OP_KEYWORDS)
                if not is_moe:
                    continue
                moe_kernel_ns += max(0, ev.end_ns - ev.start_ns)
                if "groupedmatmul" in text or "grouped_matmul" in text or "moe" in text:
                    parsed_tok = _parse_routed_tokens_from_shapes(ev.input_shapes)
                    if parsed_tok is not None:
                        step_tokens += parsed_tok
                        has_tokens = True
            effective_moe_ns = moe_union_ns if moe_union_ns > 0 else moe_kernel_ns
            if effective_moe_ns > 0:
                by_rank_moe_ms.setdefault(rk, []).append(effective_moe_ns / 1_000_000.0)
            if has_tokens:
                by_rank_tokens.setdefault(rk, []).append(float(step_tokens))

    all_ranks = sorted(set(by_rank_tokens) | set(by_rank_moe_ms) | set(by_rank_masking))
    rank_token_p50 = {rk: p50(by_rank_tokens[rk]) for rk in sorted(by_rank_tokens) if by_rank_tokens[rk]}
    rank_moe_ms_p50 = {rk: p50(by_rank_moe_ms[rk]) for rk in sorted(by_rank_moe_ms) if by_rank_moe_ms[rk]}
    rank_masking_p50 = {rk: p50(by_rank_masking[rk]) for rk in sorted(by_rank_masking) if by_rank_masking[rk]}
    comm_masking_p50 = p50(rank_masking_p50.values())

    token_vals = [v for v in rank_token_p50.values() if v is not None]
    dur_vals = [v for v in rank_moe_ms_p50.values() if v is not None]

    def _stats(vals: list[float]) -> tuple[float | None, float | None, float | None]:
        if len(vals) < 2:
            return None, None, None
        mean_v = statistics.mean(vals)
        med_v = statistics.median(vals)
        max_v = max(vals)
        cv = round(statistics.pstdev(vals) / mean_v, 6) if mean_v > 0 else 0.0
        s_to_med = round(max_v / med_v, 6) if med_v > 0 else None
        max_to_mean = round(max_v / mean_v, 6) if mean_v > 0 else None
        return cv, s_to_med, max_to_mean

    token_cv, token_straggler_ratio, token_max_to_mean = _stats(token_vals)
    dur_cv, dur_straggler_ratio, dur_max_to_mean = _stats(dur_vals)

    ep_cv = token_cv if token_cv is not None else dur_cv
    straggler_ratio = token_straggler_ratio if token_straggler_ratio is not None else dur_straggler_ratio
    max_to_mean = token_max_to_mean if token_max_to_mean is not None else dur_max_to_mean

    primary_map = rank_token_p50 if len(token_vals) >= 2 else rank_moe_ms_p50
    hot_rank = max(primary_map, key=lambda r: (primary_map[r] or 0.0, r)) if len(primary_map) >= 2 else None
    cold_rank = min(primary_map, key=lambda r: (primary_map[r] or 0.0, r)) if len(primary_map) >= 2 else None

    tokens_max = round(max(token_vals), 2) if token_vals else None
    tokens_min = round(min(token_vals), 2) if token_vals else None
    tokens_median = round(statistics.median(token_vals), 2) if token_vals else None
    tokens_mean = round(statistics.mean(token_vals), 2) if token_vals else None
    tokens_diff = round(tokens_max - tokens_min, 2) if (tokens_max is not None and tokens_min is not None) else None

    eplb_recommended = bool(
        (ep_cv is not None and ep_cv >= cv_threshold)
        or (straggler_ratio is not None and straggler_ratio >= straggler_ratio_threshold)
    )

    findings: list[dict[str, Any]] = []
    if eplb_recommended:
        findings.append(
            {
                "finding_type": "cluster_moe_ep_load_imbalance",
                "severity": "high" if (ep_cv or 0.0) >= 0.25 or (straggler_ratio or 1.0) >= 1.35 else "medium",
                "confidence": "high",
                "summary": (
                    f"MoE Expert Parallelism load imbalance detected across ranks (CV={ep_cv:.3f}, "
                    f"straggler/median={straggler_ratio:.2f}x, hot rank={hot_rank}, cold rank={cold_rank}); "
                    "enable dynamic EPLB (enable_eplb=True) with redundant expert placement."
                ),
                "evidence_ref": "ep_load_imbalance",
                "evidence_scope": {
                    "hot_expert_rank_id": hot_rank,
                    "cold_expert_rank_id": cold_rank,
                    "ep_imbalance_cv": ep_cv,
                    "straggler_to_median_ratio": straggler_ratio,
                },
            }
        )

    status = "not_applicable"
    if len(primary_map) >= 2:
        status = "imbalanced" if eplb_recommended else "balanced"
    elif rank_masking_p50:
        status = "masking_only"

    return {
        "status": status, "rank_count_evaluated": len(all_ranks),
        "ep_imbalance_cv": ep_cv, "token_cv": token_cv, "duration_cv": dur_cv,
        "straggler_to_median_ratio": straggler_ratio,
        "token_straggler_to_median_ratio": token_straggler_ratio,
        "duration_straggler_to_median_ratio": dur_straggler_ratio,
        "max_to_mean_ratio": max_to_mean,
        "tokens_max": tokens_max, "tokens_min": tokens_min,
        "tokens_median": tokens_median, "tokens_mean": tokens_mean, "tokens_diff": tokens_diff,
        "hot_expert_rank_id": hot_rank, "cold_expert_rank_id": cold_rank,
        "eplb_recommended": eplb_recommended,
        "comm_masking_ratio_p50": comm_masking_p50,
        "dual_stream_overlap_active": dual_stream_overlap,
        "per_rank_routed_tokens_p50": rank_token_p50,
        "per_rank_moe_compute_ms_p50": rank_moe_ms_p50,
        "per_rank_comm_masking_ratio_p50": rank_masking_p50,
        "guidance": (
            "Enable dynamic Expert Parallelism Load Balancing (enable_eplb=True, num_redundant_experts>=1) "
            "and dual-stream AllToAll/GroupedMatmul overlap (comm_masking_ratio target >= 0.60)."
            if eplb_recommended else None
        ),
        "findings": findings,
    }


def cross_rank_stats(observations: Sequence[Observation]) -> dict:
    summaries = rank_summaries(observations)
    walls = [row["wall_ms_p50"] for row in summaries if row["wall_ms_p50"] is not None]
    slowest = slowest_rank(summaries)
    skew = round(max(walls) - min(walls), 6) if len(walls) >= 2 else None
    ratio = round(max(walls) / min(walls), 6) if len(walls) >= 2 and min(walls) > 0 else None
    straggler_vs_link = attribute_cluster_stragglers_and_links(observations)
    ep_balance = evaluate_ep_load_balance(observations)
    return {
        "rank_summaries": summaries,
        "slowest_rank": slowest,
        "rank_count_with_data": len(walls),
        "wall_skew_ms": skew,
        "wall_ratio": ratio,
        "straggler_and_link_attribution": straggler_vs_link,
        "ep_load_balance": ep_balance,
    }


__all__ = [
    "aggregate_observations",
    "attribute_cluster_stragglers_and_links",
    "cross_rank_stats",
    "evaluate_ep_load_balance",
    "p50",
    "rank_summaries",
    "slowest_rank",
]
