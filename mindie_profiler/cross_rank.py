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
    earliest-entering ranks (longest collective wait) as victims.  Entry/exit
    skew is computed only through a declared common clock reference; raw
    per-rank starts are never shifted by subtracting each rank's minimum.
  * A missing clock relation leaves local durations, duration skew, transport
    evidence and the union unavailable only for spans/order that need it.
  * A slow-link rank needs its own paired payload/explicit transit result or
    retransmission.  A group-level payload is not divided by another rank's
    transit, and the longest local duration is never a rank-attribution
    fallback; missing pairs stay unknown.
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
from dataclasses import replace
from typing import Any, Iterable, Mapping, Sequence
from .accounting import account_window
from .classify import ALL_BLOCKS
from .events import ClockDomain, Event, Observation, Window

from .cross_rank_clock import (
    MOE_OP_KEYWORDS, TRANSPORT_BANDWIDTH_FLOOR_GBPS, _block_ms, _block_share,
    _common_reference_domain, _fmt_ms, _local_moe_ms, _map_event_interval, _metric, _ms,
    _observation_accounting, _preceding_projection, _reference_projections,
    _resolve_window_clock, _step_count, aggregate_observations, cross_rank_union_span,
    p50,
)
from .cross_rank_span import (
    _empty_straggler_result, _extract_collective_groups_from_observations,
    _normalize_collective_name, _to_ns, rank_summaries, slowest_rank,
)
from .cross_rank_stragglers import attribute_cluster_stragglers_and_links

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

    reference_data = _reference_projections(observations) if observations else None
    projections = reference_data[1] if reference_data is not None else None
    duration_domain = reference_data[0] if reference_data is not None else "local"
    duration_available = bool(projections is not None) and all(
        projections[id(obs)].get("complete", False) for obs in observations
    )
    duration_unmapped = sum(
        projections[id(obs)].get("unmapped_event_count", 0)
        for obs in observations
    ) if projections is not None else 0
    local_by_rank_moe_ms: dict[str, list[float]] = {}
    if observations:
        for obs in observations:
            if not obs.accounting.available:
                continue
            comparison_accounting = _observation_accounting(obs, projections)
            rk = str(obs.rank_id)
            moe_union_ns = comparison_accounting.block_union_ns.get("MoE") or 0
            comm_union_ns = comparison_accounting.block_union_ns.get("Comm") or 0
            exposed_comm_ns = comparison_accounting.exposed_comm_ns or 0
            if comm_union_ns > 0:
                masked_ns = max(0, comm_union_ns - exposed_comm_ns)
                mask_ratio = masked_ns / float(comm_union_ns)
                by_rank_masking.setdefault(rk, []).append(mask_ratio)
                if masked_ns > 0 and comparison_accounting.stream_count >= 2:
                    dual_stream_overlap = True
            local_moe_ms = _local_moe_ms(obs)
            if local_moe_ms is not None:
                local_by_rank_moe_ms.setdefault(rk, []).append(local_moe_ms)

            step_tokens = 0
            has_tokens = False
            moe_keyword_intervals: list[tuple[int, int]] = []
            comparison_events = (
                projections[id(obs)]["events"] if projections is not None
                else obs.events
            )
            for ev in comparison_events:
                text = f"{ev.op_type} {ev.name}".lower()
                is_moe = ev.block == "MoE" or any(kw in text for kw in MOE_OP_KEYWORDS)
                if not is_moe:
                    continue
                moe_keyword_intervals.append((ev.start_ns, ev.end_ns))
                if "groupedmatmul" in text or "grouped_matmul" in text or "moe" in text:
                    parsed_tok = _parse_routed_tokens_from_shapes(ev.input_shapes)
                    if parsed_tok is not None:
                        step_tokens += parsed_tok
                        has_tokens = True
            keyword_union_ns = 0
            if moe_keyword_intervals:
                clipped = sorted(moe_keyword_intervals)
                left, right = clipped[0]
                for next_left, next_right in clipped[1:]:
                    if next_left <= right:
                        right = max(right, next_right)
                    else:
                        keyword_union_ns += max(0, right - left)
                        left, right = next_left, next_right
                keyword_union_ns += max(0, right - left)
            effective_moe_ns = moe_union_ns if moe_union_ns > 0 else keyword_union_ns
            if effective_moe_ns > 0:
                by_rank_moe_ms.setdefault(rk, []).append(effective_moe_ns / 1_000_000.0)
            if has_tokens:
                by_rank_tokens.setdefault(rk, []).append(float(step_tokens))

    all_ranks = sorted(set(by_rank_tokens) | set(by_rank_moe_ms) | set(by_rank_masking))
    rank_token_p50 = {rk: p50(by_rank_tokens[rk]) for rk in sorted(by_rank_tokens) if by_rank_tokens[rk]}
    rank_moe_ms_p50 = {rk: p50(by_rank_moe_ms[rk]) for rk in sorted(by_rank_moe_ms) if by_rank_moe_ms[rk]}
    local_rank_moe_ms_p50 = {
        rk: p50(local_by_rank_moe_ms[rk])
        for rk in sorted(local_by_rank_moe_ms) if local_by_rank_moe_ms[rk]
    }
    rank_masking_p50 = {rk: p50(by_rank_masking[rk]) for rk in sorted(by_rank_masking) if by_rank_masking[rk]}
    comm_masking_p50 = p50(rank_masking_p50.values())

    token_vals = [v for v in rank_token_p50.values() if v is not None]
    dur_vals = [v for v in rank_moe_ms_p50.values() if v is not None]
    local_dur_vals = [v for v in local_rank_moe_ms_p50.values() if v is not None]

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
    local_dur_cv, _local_dur_straggler, _local_dur_max_to_mean = _stats(local_dur_vals)

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
        "duration_domain": duration_domain,
        "duration_available": duration_available,
        "duration_unmapped_event_count": duration_unmapped,
        "local_duration_cv": local_dur_cv,
        "local_rank_moe_compute_ms_p50": local_rank_moe_ms_p50,
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
    local_walls = [
        row["local_wall_ms_p50"]
        for row in summaries
        if row.get("local_wall_ms_p50") is not None
    ]
    slowest = slowest_rank(summaries)
    skew = round(max(walls) - min(walls), 6) if len(walls) >= 2 else None
    ratio = round(max(walls) / min(walls), 6) if len(walls) >= 2 and min(walls) > 0 else None
    local_skew = (
        round(max(local_walls) - min(local_walls), 6)
        if len(local_walls) >= 2 else None
    )
    local_ratio = (
        round(max(local_walls) / min(local_walls), 6)
        if len(local_walls) >= 2 and min(local_walls) > 0 else None
    )
    straggler_vs_link = attribute_cluster_stragglers_and_links(observations)
    ep_balance = evaluate_ep_load_balance(observations)
    return {
        "rank_summaries": summaries,
        "slowest_rank": slowest,
        "rank_count_with_data": len(walls),
        "comparison_domain": summaries[0].get("comparison_domain", "local") if summaries else "local",
        "comparison_complete": bool(summaries) and all(
            row.get("comparison_complete", False) for row in summaries
        ),
        "wall_skew_ms": skew,
        "wall_ratio": ratio,
        "local_wall_skew_ms": local_skew,
        "local_wall_ratio": local_ratio,
        "cross_rank_union_span": cross_rank_union_span(observations),
        "straggler_and_link_attribution": straggler_vs_link,
        "ep_load_balance": ep_balance,
    }

__all__ = [
    "aggregate_observations",
    "attribute_cluster_stragglers_and_links",
    "cross_rank_stats",
    "cross_rank_union_span",
    "evaluate_ep_load_balance",
    "p50",
    "rank_summaries",
    "slowest_rank",
]
