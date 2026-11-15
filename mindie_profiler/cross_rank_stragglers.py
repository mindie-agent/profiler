"""Cross-rank union timeline accounting, straggler attribution, and EP load balance (cross_rank_stragglers).

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
from .events import ClockDomain, Event, Observation, Window

from .cross_rank_clock import TRANSPORT_BANDWIDTH_FLOOR_GBPS, _ms
from .cross_rank_span import (
    _empty_straggler_result, _extract_collective_groups_from_observations, _to_ns,
)

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
    classification_counts: dict[str, int] = {
        "slow_rank": 0,
        "slow_link": 0,
        "mixed_straggler_and_link": 0,
        "balanced": 0,
        "clock_unverified": 0,
        "link_attribution_unknown": 0,
    }

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
            transport_value = r.get("transport")
            transport_source = (
                "rank" if transport_value is not None
                else ("group" if group.get("transport") is not None else None)
            )
            if transport_value is None:
                transport_value = group.get("transport")
            size_value = r.get("size_bytes")
            size_source = (
                "rank" if size_value is not None
                else ("group" if group.get("size_bytes") is not None else None)
            )
            if size_value is None:
                size_value = group.get("size_bytes")
            rows.append(
                {
                    "rank_id": str(r.get("rank_id") if r.get("rank_id") is not None else f"rank_{r.get('rank', 0)}"),
                    "rank_index": r.get("rank_index", r.get("rank")),
                    "start_ns": s_ns,
                    "end_ns": e_ns,
                    "duration_ns": dur_ns,
                    "clock": r.get("clock"),
                    "explicit_wait_ns": _to_ns(r, "wait_ns", "wait_us", "wait_ms"),
                    "explicit_transit_ns": _to_ns(r, "transit_ns", "transit_us", "transit_ms"),
                    "preceding_compute_ns": _to_ns(r, "preceding_compute_ns", "preceding_compute_us", "preceding_compute_ms"),
                    "preceding_host_gap_ns": _to_ns(r, "preceding_host_gap_ns", "preceding_host_gap_us", "preceding_host_gap_ms"),
                    "local_preceding_compute_ns": _to_ns(
                        r, "local_preceding_compute_ns",
                        "local_preceding_compute_us", "local_preceding_compute_ms"
                    ),
                    "local_preceding_host_gap_ns": _to_ns(
                        r, "local_preceding_host_gap_ns",
                        "local_preceding_host_gap_us", "local_preceding_host_gap_ms"
                    ),
                    "preceding_time_domain": r.get("time_domain", "caller_declared"),
                    "retry": int(r.get("retry") or 0),
                    "relay": int(r.get("relay") or 0),
                    "transport": str(transport_value or "").upper() or None,
                    "transport_source": transport_source,
                    "size_bytes": int(size_value) if size_value not in (None, 0) else None,
                    "size_source": size_source,
                }
            )

        local_durations = [r["duration_ns"] for r in rows]
        local_min_dur = min(local_durations)
        local_max_dur = max(local_durations)

        # Rank-local starts are comparable only when every participant declares
        # the same sourced reference.  Explicit caller-supplied groups retain
        # their declaration; observation-derived groups carry Event.clock.
        has_clock_metadata = any(isinstance(r.get("clock"), ClockDomain) for r in rows)
        aligned_starts: list[int] = []
        aligned_ends: list[int] = []
        if has_clock_metadata:
            clocks = [r.get("clock") for r in rows]
            references = {
                clock.reference_domain
                for clock in clocks
                if isinstance(clock, ClockDomain)
                and clock.comparable
                and clock.offset_ns is not None
            }
            if (
                len(references) == 1
                and all(
                    isinstance(clock, ClockDomain) and clock.comparable
                    for clock in clocks
                )
            ):
                reference = next(iter(references))
                mapped = [
                    (clock.to_reference_ns(r["start_ns"]), clock.to_reference_ns(r["end_ns"]))
                    for clock, r in zip(clocks, rows)
                ]
                if all(start is not None and end is not None for start, end in mapped):
                    aligned_starts = [int(start) for start, _end in mapped]
                    aligned_ends = [int(end) for _start, end in mapped]
                    clock_relation = "sourced_reference"
                    clock_reference = reference
                else:
                    clock_relation = "unavailable_clock_relation"
                    clock_reference = None
            else:
                clock_relation = "unavailable_clock_relation"
                clock_reference = None
        else:
            # The explicit collective_groups API supplies one already-aligned
            # interval set; it is a caller declaration, not an inferred clock.
            aligned_starts = [r["start_ns"] for r in rows]
            aligned_ends = [r["end_ns"] for r in rows]
            clock_relation = "caller_declared"
            clock_reference = None

        if clock_relation == "unavailable_clock_relation":
            launch_skew_ns: int | None = None
            end_skew_ns: int | None = None
            duration_domain = "local"
            comparison_durations = local_durations
        else:
            launch_skew_ns = max(aligned_starts) - min(aligned_starts)
            end_skew_ns = max(aligned_ends) - min(aligned_ends)
            duration_domain = (
                "reference" if clock_relation == "sourced_reference"
                else "caller_declared"
            )
            comparison_durations = [
                end_ns - start_ns
                for start_ns, end_ns in zip(aligned_starts, aligned_ends)
            ]
        min_dur = min(comparison_durations)
        max_dur = max(comparison_durations)
        dur_skew_ns = max_dur - min_dur
        comparison_duration_by_rank = {
            r["rank_id"]: int(duration)
            for r, duration in zip(rows, comparison_durations)
        }

        explicit_transits = [r["explicit_transit_ns"] for r in rows if r["explicit_transit_ns"] is not None]
        transit_ns = int(statistics.median(explicit_transits)) if explicit_transits else local_min_dur
        if not explicit_transits:
            transit_source = "min_duration_estimate"
        elif len(explicit_transits) == len(rows):
            transit_source = "explicit"
        else:
            transit_source = "mixed"
        launch_skew_ms = None if launch_skew_ns is None else (_ms(launch_skew_ns) or 0.0)
        end_skew_ms = None if end_skew_ns is None else (_ms(end_skew_ns) or 0.0)
        dur_skew_ms = _ms(dur_skew_ns) or 0.0
        transit_ms = _ms(transit_ns) or 0.0
        max_dur_ms = _ms(max_dur) or 0.0

        # Pair payload, explicit transit and transport on the same rank.  A
        # group-level size/transport is an explicit shared declaration; it is
        # never combined with another rank's transit.  The min-duration
        # estimate stays a descriptive marker and cannot prove link transit.
        rank_facts: dict[str, dict[str, Any]] = {}
        for r in rows:
            size_bytes = r["size_bytes"]
            rank_transit_ns = r["explicit_transit_ns"]
            transport_value = r["transport"]
            floor = (
                TRANSPORT_BANDWIDTH_FLOOR_GBPS.get(transport_value)
                if transport_value is not None
                else None
            )
            missing_reasons: list[str] = []
            if size_bytes is None:
                missing_reasons.append("size_missing")
            if rank_transit_ns is None:
                missing_reasons.append("transit_missing")
            elif rank_transit_ns <= 0:
                missing_reasons.append("transit_not_positive")
            if transport_value is None:
                missing_reasons.append("transport_missing")
            elif floor is None:
                missing_reasons.append(f"transport_unrecognized:{transport_value}")
            bandwidth = None
            if (
                size_bytes is not None
                and rank_transit_ns is not None
                and rank_transit_ns > 0
            ):
                bandwidth = round(float(size_bytes) / float(rank_transit_ns), 4)
            low_bandwidth = bool(
                bandwidth is not None
                and floor is not None
                and bandwidth < floor
            )
            retried = r["retry"] > 0
            if retried and low_bandwidth:
                evidence = "retransmission_and_low_bandwidth"
            elif retried:
                evidence = "retransmission"
            elif low_bandwidth:
                evidence = "low_bandwidth"
            else:
                evidence = None
            rank_facts[r["rank_id"]] = {
                "collective_index": idx,
                "rank_id": r["rank_id"],
                "size_bytes": size_bytes,
                "size_source": r["size_source"],
                "transit_ms": _ms(rank_transit_ns),
                "transit_source": (
                    "explicit" if rank_transit_ns is not None else "missing"
                ),
                "transport": transport_value,
                "transport_source": r["transport_source"],
                "applicable_floor_gbps": floor,
                "bandwidth_gbps": bandwidth,
                "retry": r["retry"],
                "local_duration_ms": _ms(r["duration_ns"]),
                "comparison_duration_ms": _ms(
                    comparison_duration_by_rank[r["rank_id"]]
                ),
                "duration_domain": duration_domain,
                "missing_reasons": missing_reasons,
                "link_evidence": evidence,
            }
        rank_transits_ms = {
            rank: fact["transit_ms"] for rank, fact in rank_facts.items()
        }
        rank_sizes_bytes = {
            rank: fact["size_bytes"] for rank, fact in rank_facts.items()
        }
        rank_size_sources = {
            rank: fact["size_source"] for rank, fact in rank_facts.items()
        }
        rank_transports = {
            rank: fact["transport"] for rank, fact in rank_facts.items()
        }
        rank_transport_sources = {
            rank: fact["transport_source"] for rank, fact in rank_facts.items()
        }
        rank_bandwidths: dict[str, float | None] = {
            rank: fact["bandwidth_gbps"] for rank, fact in rank_facts.items()
        }
        rank_low_bandwidth = {
            rank for rank, fact in rank_facts.items()
            if fact["link_evidence"] in {
                "low_bandwidth",
                "retransmission_and_low_bandwidth",
            }
        }
        paired_bandwidths = [value for value in rank_bandwidths.values() if value is not None]
        if not paired_bandwidths:
            bandwidth_status = "unavailable"
        elif len(paired_bandwidths) < len(rows):
            bandwidth_status = "incomplete"
        elif len(set(paired_bandwidths)) == 1:
            bandwidth_status = "uniform"
        else:
            bandwidth_status = "per_rank"
        effective_bandwidth_gbps = (
            paired_bandwidths[0] if bandwidth_status == "uniform" else None
        )
        bandwidth_source = (
            "explicit_transit"
            if bandwidth_status in {"uniform", "per_rank"}
            else None
        )
        retry_ranks = [
            rank for rank, fact in rank_facts.items() if fact["retry"] > 0
        ]
        has_retry = bool(retry_ranks)
        bw_degraded = bool(rank_low_bandwidth)
        link_bottleneck_ranks = sorted(
            rank for rank, fact in rank_facts.items()
            if fact["link_evidence"] is not None
        )
        rank_link_evidence = {
            rank: fact["link_evidence"] for rank, fact in rank_facts.items()
        }
        transports = {
            fact["transport"] for fact in rank_facts.values()
            if fact["transport"] is not None
        }
        transport = next(iter(transports)) if len(transports) == 1 else None

        earliest_rank = None
        latest_rank = None
        if clock_relation != "unavailable_clock_relation":
            earliest_rank = min(
                zip(aligned_starts, rows),
                key=lambda item: (
                    item[0],
                    -comparison_duration_by_rank[item[1]["rank_id"]],
                    item[1]["rank_id"],
                ),
            )[1]
            latest_rank = max(
                zip(aligned_starts, rows),
                key=lambda item: (
                    item[0],
                    -comparison_duration_by_rank[item[1]["rank_id"]],
                    item[1]["rank_id"],
                ),
            )[1]
        entry_skew_dominant = bool(
            launch_skew_ms is not None
            and latest_rank is not None
            and earliest_rank is not None
            and launch_skew_ms >= min_skew_ms
            and max_dur_ms > 0
            and (launch_skew_ms / max_dur_ms) >= entry_skew_share_threshold
            and earliest_rank["rank_id"] != latest_rank["rank_id"]
        )
        tight_exit = bool(
            end_skew_ms is not None
            and launch_skew_ms is not None
            and end_skew_ms <= max(0.002, tight_exit_ratio_threshold * launch_skew_ms)
        )
        exit_or_link_skew = bool(
            (end_skew_ms is not None and end_skew_ms >= min_skew_ms)
            or dur_skew_ms >= min_skew_ms
            or bw_degraded
            or has_retry
        )

        perpetrator_id: str | None = None
        straggler_cause: str | None = None
        victims: list[str] = []
        transport_anomaly: str | None = None
        preceding_unavailable = any(
            r.get("preceding_time_domain") == "unavailable" for r in rows
        )

        if entry_skew_dominant and tight_exit and not has_retry and not bw_degraded:
            classification = "slow_rank"
            perpetrator_id = latest_rank["rank_id"]
            max_aligned_start = max(aligned_starts)
            lead_ns = int(launch_skew_ns or 0)
            victims = [
                r["rank_id"]
                for r, aligned_start in zip(rows, aligned_starts)
                if r["rank_id"] != perpetrator_id
                and (max_aligned_start - aligned_start) >= int(0.25 * lead_ns)
            ]
            # Sub-attribute compute_straggler vs host_dispatch_straggler
            peers = [r for r in rows if r["rank_id"] != perpetrator_id]
            peer_comp = [r["preceding_compute_ns"] for r in peers if r["preceding_compute_ns"] is not None]
            peer_gap = [r["preceding_host_gap_ns"] for r in peers if r["preceding_host_gap_ns"] is not None]
            perp_comp = latest_rank["preceding_compute_ns"]
            perp_gap = latest_rank["preceding_host_gap_ns"]
            comp_excess = (perp_comp - statistics.median(peer_comp)) if (perp_comp is not None and peer_comp) else 0.0
            gap_excess = (perp_gap - statistics.median(peer_gap)) if (perp_gap is not None and peer_gap) else 0.0
            if preceding_unavailable:
                straggler_cause = None
            elif gap_excess > comp_excess and gap_excess > 0:
                straggler_cause = "host_dispatch_straggler"
            else:
                straggler_cause = "compute_straggler"
            if straggler_cause is not None:
                vote_counts[perpetrator_id] = vote_counts.get(perpetrator_id, 0) + 1
                cause_votes.setdefault(perpetrator_id, {})[straggler_cause] = (
                    cause_votes.get(perpetrator_id, {}).get(straggler_cause, 0) + 1
                )
            victim_set.update(victims)
        elif not entry_skew_dominant and exit_or_link_skew:
            if has_retry or bw_degraded:
                classification = "slow_link"
                if has_retry:
                    transport_anomaly = "rdma_retransmission"
                elif bw_degraded:
                    transport_anomaly = "low_link_bandwidth"
                # Rank attribution is exactly the per-rank evidenced set; it
                # never falls back to the longest local duration.
                slow_link_ranks.update(link_bottleneck_ranks)
            elif clock_relation == "unavailable_clock_relation":
                classification = "clock_unverified"
            else:
                classification = "link_attribution_unknown"
        elif entry_skew_dominant and exit_or_link_skew:
            if has_retry or bw_degraded:
                classification = "mixed_straggler_and_link"
                perpetrator_id = latest_rank["rank_id"]
                straggler_cause = "compute_straggler"
                victims = [r["rank_id"] for r in rows if r["rank_id"] != perpetrator_id]
                if has_retry:
                    transport_anomaly = "rdma_retransmission"
                elif bw_degraded:
                    transport_anomaly = "low_link_bandwidth"
                vote_counts[perpetrator_id] = vote_counts.get(perpetrator_id, 0) + 1
                victim_set.update(victims)
                slow_link_ranks.update(link_bottleneck_ranks)
            elif clock_relation == "unavailable_clock_relation":
                classification = "clock_unverified"
            else:
                classification = "link_attribution_unknown"
        elif clock_relation == "unavailable_clock_relation":
            classification = "clock_unverified"
        else:
            classification = "balanced"

        classification_counts[classification] = classification_counts.get(classification, 0) + 1
        evaluated.append(
            {
                "collective_index": idx,
                "step": group.get("step"),
                "collective_op": str(group.get("collective_op") or group.get("op_name") or "collective"),
                "classification": classification,
                "clock_relation": clock_relation,
                "clock_reference_domain": clock_reference,
                "launch_skew_ms": launch_skew_ms,
                "end_skew_ms": end_skew_ms,
                "duration_skew_ms": dur_skew_ms,
                "transit_duration_ms": transit_ms,
                "transit_source": transit_source,
                "rank_transits_ms": rank_transits_ms,
                "rank_sizes_bytes": rank_sizes_bytes,
                "rank_size_sources": rank_size_sources,
                "rank_transports": rank_transports,
                "rank_transport_sources": rank_transport_sources,
                "max_duration_ms": max_dur_ms,
                "local_max_duration_ms": _ms(local_max_dur),
                "min_duration_ms": _ms(min_dur),
                "duration_domain": duration_domain,
                "rank_bandwidths_gbps": rank_bandwidths,
                "bandwidth_status": bandwidth_status,
                "effective_bandwidth_gbps": effective_bandwidth_gbps,
                "bandwidth_source": bandwidth_source,
                "rank_link_evidence": rank_link_evidence,
                "rank_link_facts": rank_facts,
                "preceding_compute_ns_by_rank": {
                    r["rank_id"]: r["preceding_compute_ns"] for r in rows
                },
                "preceding_host_gap_ns_by_rank": {
                    r["rank_id"]: r["preceding_host_gap_ns"] for r in rows
                },
                "local_preceding_compute_ns_by_rank": {
                    r["rank_id"]: r["local_preceding_compute_ns"] for r in rows
                },
                "local_preceding_host_gap_ns_by_rank": {
                    r["rank_id"]: r["local_preceding_host_gap_ns"] for r in rows
                },
                "preceding_time_domain": (
                    sorted({r["preceding_time_domain"] for r in rows})
                    if rows else []
                ),
                "transport": transport,
                "transports": sorted(transports),
                "perpetrator_rank_id": perpetrator_id,
                "straggler_cause": straggler_cause,
                "cause_unavailable_reason": (
                    "preceding_time_domain_unavailable"
                    if preceding_unavailable and straggler_cause is None
                    else None
                ),
                "victim_rank_ids": victims,
                "link_bottleneck_rank_ids": link_bottleneck_ranks,
                "transport_anomaly": transport_anomaly,
            }
        )

    if not evaluated:
        return _empty_straggler_result()

    # One reduction from evaluated facts into two independent views.  The
    # primary classification only orders the summary; it never filters which
    # known anomalies are emitted.
    slow_link_view: list[dict[str, Any]] = []
    slow_rank_view: list[dict[str, Any]] = []
    for c in evaluated:
        link_ranks = {
            rank: evidence
            for rank, evidence in c["rank_link_evidence"].items()
            if evidence is not None
        }
        if link_ranks:
            anomaly = c["transport_anomaly"]
            if anomaly is None:
                has_retry = any(
                    str(evidence).startswith("retransmission")
                    for evidence in link_ranks.values()
                )
                anomaly = "rdma_retransmission" if has_retry else "low_link_bandwidth"
            slow_link_view.append(
                {
                    "collective_index": c["collective_index"],
                    "step": c["step"],
                    "collective_op": c["collective_op"],
                    "transport_anomaly": anomaly,
                    "bottleneck_rank_ids": sorted(link_ranks),
                    "rank_link_evidence": c["rank_link_evidence"],
                    "rank_bandwidths_gbps": c["rank_bandwidths_gbps"],
                    "transit_source": c["transit_source"],
                }
            )
        if c["perpetrator_rank_id"] is not None:
            slow_rank_view.append(
                {
                    "collective_index": c["collective_index"],
                    "step": c["step"],
                    "collective_op": c["collective_op"],
                    "classification": c["classification"],
                    "perpetrator_rank_id": c["perpetrator_rank_id"],
                    "straggler_cause": c["straggler_cause"],
                    "cause_unavailable_reason": c.get("cause_unavailable_reason"),
                    "victim_rank_ids": c["victim_rank_ids"],
                    "launch_skew_ms": c["launch_skew_ms"],
                    "end_skew_ms": c["end_skew_ms"],
                }
            )

    slow_link_rank_union = sorted(
        {
            rank
            for item in slow_link_view
            for rank in item["bottleneck_rank_ids"]
        }
    )
    slow_link_ranks = set(slow_link_rank_union)
    vote_counts = {}
    cause_votes = {}
    for item in slow_rank_view:
        perpetrator = item["perpetrator_rank_id"]
        vote_counts[perpetrator] = vote_counts.get(perpetrator, 0) + 1
        cause = item["straggler_cause"]
        if cause is not None:
            cause_votes.setdefault(perpetrator, {})[cause] = (
                cause_votes.get(perpetrator, {}).get(cause, 0) + 1
            )
    primary_straggler: str | None = None
    primary_cause: str | None = None
    victim_set: set[str] = set()
    if vote_counts:
        primary_straggler = max(sorted(vote_counts), key=lambda r: vote_counts[r])
        causes = cause_votes.get(primary_straggler, {})
        if causes:
            primary_cause = max(sorted(causes), key=lambda c: causes[c])
        victim_set.update(
            victim
            for item in slow_rank_view
            if item["perpetrator_rank_id"] == primary_straggler
            for victim in item["victim_rank_ids"]
        )

    if classification_counts["slow_rank"] > 0 and classification_counts["slow_rank"] >= classification_counts["slow_link"]:
        primary_class = "slow_rank"
    elif classification_counts["slow_link"] > 0:
        primary_class = "slow_link"
    elif classification_counts["mixed_straggler_and_link"] > 0:
        primary_class = "mixed_straggler_and_link"
    elif classification_counts.get("clock_unverified", 0) > 0:
        primary_class = "clock_unverified"
    elif classification_counts.get("link_attribution_unknown", 0) > 0:
        primary_class = "link_attribution_unknown"
    else:
        primary_class = "balanced"

    findings: list[dict[str, Any]] = []
    if slow_rank_view:
        summary_parts = [
            f"step {item['step']} {item['collective_op']}: "
            f"{item['perpetrator_rank_id']} ({item['straggler_cause'] or 'cause_unavailable'}); "
            f"victims {sorted(item['victim_rank_ids'])}"
            for item in slow_rank_view
        ]
        findings.append(
            {
                "finding_type": "cluster_slow_rank_straggler",
                "severity": "high",
                "confidence": "high",
                "summary": (
                    f"Slow-rank evidence in {len(slow_rank_view)} collective(s): "
                    + "; ".join(summary_parts)
                ),
                "evidence_ref": primary_cause or "slow_rank",
                "evidence_scope": {
                    "perpetrator_rank_id": primary_straggler,
                    "slow_rank_evidence": slow_rank_view,
                },
            }
        )
    if slow_link_view:
        summary_parts = [
            f"step {item['step']} {item['collective_op']}: "
            f"ranks {item['bottleneck_rank_ids']} ({item['transport_anomaly']})"
            for item in slow_link_view
        ]
        findings.append(
            {
                "finding_type": "cluster_slow_communication_link",
                "severity": "high",
                "confidence": "high",
                "summary": (
                    f"Slow-link evidence in {len(slow_link_view)} collective(s): "
                    + "; ".join(summary_parts)
                ),
                "evidence_ref": "slow_link_evidence",
                "evidence_scope": {
                    "slow_link_evidence": slow_link_view,
                    "slow_link_rank_union": slow_link_rank_union,
                },
            }
        )
    if not slow_rank_view and not slow_link_view and primary_class == "clock_unverified":
        sample = next(c for c in evaluated if c["classification"] == "clock_unverified")
        findings.append(
            {
                "finding_type": "cross_rank_clock_relation_unavailable",
                "severity": "medium",
                "confidence": "high",
                "summary": (
                    "Collective entry/exit order cannot be compared because participant ranks "
                    "do not share a sourced clock reference. Local durations, transport evidence "
                    "and inventory remain usable; no per-rank-minimum offset was invented."
                ),
                "evidence_ref": "clock_relation_unavailable",
                "evidence_scope": {
                    "step": sample["step"],
                    "collective_op": sample["collective_op"],
                    "clock_unverified_groups": classification_counts["clock_unverified"],
                },
            }
        )
    if (
        not slow_rank_view
        and not slow_link_view
        and primary_class == "link_attribution_unknown"
    ):
        sample = next(
            c for c in evaluated if c["classification"] == "link_attribution_unknown"
        )
        findings.append(
            {
                "finding_type": "cross_rank_link_evidence_missing",
                "severity": "medium",
                "confidence": "high",
                "summary": (
                    "Timing or completion asymmetry is present, but no rank has a paired "
                    "payload/explicit-transit low-bandwidth result or retransmission. "
                    "Rank-level link attribution is left unknown."
                ),
                "evidence_ref": "link_evidence_missing",
                "evidence_scope": {
                    "step": sample["step"],
                    "collective_op": sample["collective_op"],
                    "bandwidth_status": sample["bandwidth_status"],
                    "rank_bandwidths_gbps": sample["rank_bandwidths_gbps"],
                    "rank_link_evidence": sample["rank_link_evidence"],
                },
            }
        )

    if slow_rank_view or slow_link_view:
        status = "detected"
    elif primary_class == "clock_unverified":
        status = "clock_relation_unavailable"
    elif primary_class == "link_attribution_unknown":
        status = "link_attribution_unknown"
    else:
        status = "balanced"
    return {
        "status": status,
        "collective_count": len(evaluated),
        "classification_counts": classification_counts,
        "clock_unverified_groups": classification_counts["clock_unverified"],
        "link_attribution_unknown_groups": classification_counts[
            "link_attribution_unknown"
        ],
        "primary_classification": primary_class,
        "primary_straggler_rank_id": primary_straggler,
        "primary_straggler_cause": primary_cause,
        "primary_victim_rank_ids": sorted(victim_set),
        "primary_slow_link_ranks": slow_link_rank_union,
        "slow_link_rank_union": slow_link_rank_union,
        "slow_link_evidence": slow_link_view,
        "slow_rank_evidence": slow_rank_view,
        "perpetrator_vote_counts": vote_counts,
        "collectives": evaluated,
        "findings": findings,
    }
