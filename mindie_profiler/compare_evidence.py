"""Explicit-workload A/B C7 profile comparison and provenance verification (compare_evidence).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting explicit-workload a/b c7 profile comparison and provenance verification.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence
from .classify import EVENT_BLOCKS
from .compare_metric import metric as _metric, num as _num

from .compare_clock import (
    COMPARISON_SCHEMA, _P50_REL_TOL, _block_row_evidence, _dedupe, _layer_identity,
    _lim, _row_map, _structure_parts,
)

def _block_share_evidence(
    rows: Mapping[tuple[int, str], Mapping[str, Any]],
    keys: Iterable[tuple[int, str]],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    denominators: list[float] = []
    shares: dict[str, list[float]] = {block: [] for block in EVENT_BLOCKS}
    recorded: dict[str, list[float]] = {block: [] for block in EVENT_BLOCKS}
    missing: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for key in keys:
        evidence = _block_row_evidence(rows[key])
        record = {"step": key[0], "rank_id": key[1], **evidence}
        records.append(record)
        if not evidence["complete"]:
            if evidence["missing_blocks"]:
                missing.append({
                    "step": key[0], "rank_id": key[1],
                    "blocks": list(evidence["missing_blocks"]),
                })
            if evidence["invalid_blocks"]:
                invalid.append({
                    "step": key[0], "rank_id": key[1],
                    "blocks": list(evidence["invalid_blocks"]),
                })
            continue
        if evidence["denominator"] is not None:
            denominators.append(evidence["denominator"])
        for block in EVENT_BLOCKS:
            value = evidence["shares"].get(block)
            if value is not None:
                shares[block].append(value)
            observed = evidence["recorded_shares"].get(block)
            if observed is not None:
                recorded[block].append(observed)
                recomputed = evidence["shares"].get(block)
                if recomputed is not None:
                    allowed = max(_P50_REL_TOL, _P50_REL_TOL * max(abs(observed), abs(recomputed)))
                    if abs(observed - recomputed) > allowed:
                        conflicts.append({
                            "step": key[0], "rank_id": key[1], "block": block,
                            "recorded": observed, "recomputed": recomputed,
                        })
    return {
        "complete": not missing and not invalid,
        "records": records,
        "denominators": denominators,
        "shares": shares,
        "recorded_shares": recorded,
        "missing": missing,
        "invalid": invalid,
        "row_conflicts": conflicts,
    }

def _block_values(rows: Mapping[tuple[int, str], Mapping[str, Any]],
                  keys: Iterable[tuple[int, str]], block: str,
                  field: str) -> tuple[list[float], list[tuple[int, str]]]:
    values: list[float] = []
    missing: list[tuple[int, str]] = []
    for key in keys:
        mapping = _row_map(rows[key], field)
        value = _num(mapping.get(block)) if isinstance(mapping, Mapping) else None
        if value is None:
            missing.append(key)
        else:
            values.append(value)
    return values, missing

def _local_step_accounting(summary: Mapping[str, Any]) -> dict[str, Any] | None:
    accounting = summary.get("step_accounting")
    if not isinstance(accounting, Mapping):
        return None
    keys = (
        "steady_steps", "observed_steps", "rank_scope", "observed_event_span_ms_p50",
        "device_busy_union_ms_p50", "device_activity_sum_ms_p50", "exposed_comm_ms_p50",
        "device_uncovered_ms_p50", "total_cost_ms_p50", "underfeed_bubble_ratio",
        "aicpu_exposed_ratio", "coverage_ratio_p50",
    )
    return {"status": "local_only", **{key: accounting.get(key) for key in keys}}

def _local_semantic_blocks(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = summary.get("semantic_block_breakdown")
    if not isinstance(raw, list):
        return []
    keys = (
        "block", "busy_union_ms_p50", "share_of_busy_pct", "share_denominator",
        "share_denominator_ms_p50", "event_count", "mapping_rule", "basis",
    )
    return [
        {key: row.get(key) for key in keys}
        for row in raw if isinstance(row, Mapping)
    ]

def _observation_draft(
    b_rows: Mapping[tuple[int, str], Mapping[str, Any]] | None,
    c_rows: Mapping[tuple[int, str], Mapping[str, Any]] | None,
    common_steps: Iterable[int],
    common_ranks: Iterable[str],
    missing: Iterable[tuple[int, str]],
    hard_reasons: Sequence[str],
) -> list[dict[str, Any]]:
    """Mark every readable row before any comparison qualification return."""

    step_set, rank_set = set(common_steps), set(common_ranks)
    expected = {(step, rank) for step in step_set for rank in rank_set}
    missing_set = set(missing)
    records: list[dict[str, Any]] = []
    for side, rows, peer in (
        ("baseline", b_rows, c_rows),
        ("candidate", c_rows, b_rows),
    ):
        if not isinstance(rows, Mapping):
            continue
        for (step, rank), row in sorted(rows.items()):
            key = (step, rank)
            if step not in step_set:
                status, reason = "outside_scope", "step_outside_common_boundary"
            elif rank not in rank_set:
                status, reason = "outside_scope", "rank_outside_common_scope"
            elif key in expected:
                if not isinstance(peer, Mapping):
                    status, reason = "one_sided", "peer_window_accounting_unavailable"
                elif key not in peer:
                    status, reason = "one_sided", "missing_in_peer"
                elif hard_reasons:
                    status, reason = "excluded", hard_reasons[0]
                else:
                    status, reason = "paired", None
            else:
                status, reason = "outside_scope", "outside_common_step_rank_boundary"
            records.append({
                "side": side,
                "step": step,
                "rank_id": rank,
                "status": status,
                "reason": reason,
                "source": row.get("source"),
                "row": dict(row),
            })
    return records

def _excluded_observations(
    b_rows: Mapping[tuple[int, str], Mapping[str, Any]],
    c_rows: Mapping[tuple[int, str], Mapping[str, Any]],
    common_steps: Iterable[int],
    common_ranks: Iterable[str],
) -> list[dict[str, Any]]:
    step_set, rank_set = set(common_steps), set(common_ranks)
    records: list[dict[str, Any]] = []
    for side, rows in (("baseline", b_rows), ("candidate", c_rows)):
        for (step, rank), row in sorted(rows.items()):
            if step in step_set and rank in rank_set:
                continue
            if step not in step_set:
                reason = "step_outside_common_boundary"
            elif rank not in rank_set:
                reason = "rank_outside_common_scope"
            else:
                reason = "outside_common_step_rank_boundary"
            records.append({
                "side": side,
                "step": step,
                "rank_id": rank,
                "reason": reason,
                "source": row.get("source"),
                "row": dict(row),
            })
    return records

def _semantic_blocks_payload(block_results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "comparable" if block_results and all(
            entry["status"] == "compared" and entry.get("share_integrity") != "failed"
            for entry in block_results
        ) else "comparable_with_limitations" if block_results else "not_comparable",
        "blocks": block_results,
    }

def _not_comparable(matching: Mapping[str, Any], applicability: Mapping[str, Any],
                    reasons: list[dict[str, Any]], limitations: list[dict[str, Any]],
                    reuse: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": COMPARISON_SCHEMA,
        "status": "not_comparable",
        "comparable": False,
        "partial": False,
        "reasons": reasons,
        "limitations": _dedupe([*limitations, *reasons]),
        "matching": dict(matching),
        "applicability": dict(applicability),
        "structural_reuse": dict(reuse) if reuse is not None else None,
        "step_accounting": None,
        "semantic_blocks": None,
        "hierarchy": None,
        "unpaired_observations": [],
        "excluded_observations": [],
        "observation_rows": [],
        "local_step_accounting": None,
        "local_semantic_blocks": None,
    }

def _hierarchy(baseline: Mapping[str, Any], candidate: Mapping[str, Any],
               reuse: Mapping[str, Any]) -> dict[str, Any]:
    if not reuse.get("allowed"):
        status = "not_available" if reuse.get("status") == "not_available" else "not_comparable"
        return {
            "status": status,
            "layers": [],
            "baseline_source_content": reuse.get("baseline_source_content"),
            "candidate_source_content": reuse.get("candidate_source_content"),
            "limitations": [_lim(
                "structure_evidence_unavailable" if status == "not_available" else "structure_reuse_not_established",
                "no layer conclusion is possible without verified event-shape and layer identity evidence",
                details={"reason_codes": list(reuse.get("reason_codes", []))},
            )],
        }
    _, b_layers = _structure_parts(baseline)
    _, c_layers = _structure_parts(candidate)
    assert b_layers is not None and c_layers is not None
    b_map = {(layer_id, ordinal): layer for layer in b_layers
             for layer_id, ordinal, _ in [_layer_identity(layer)] if layer_id is not None and ordinal is not None}
    c_map = {(layer_id, ordinal): layer for layer in c_layers
             for layer_id, ordinal, _ in [_layer_identity(layer)] if layer_id is not None and ordinal is not None}
    results: list[dict[str, Any]] = []
    limits: list[dict[str, Any]] = []
    for key in sorted(b_map):
        b_layer, c_layer = b_map[key], c_map.get(key)
        name = _layer_identity(b_layer)[2] or key[0]
        if c_layer is None:
            limits.append(_lim("layer_missing_in_candidate", f"layer {key!r} has no counterpart",
                               details={"layer_id": key[0], "ordinal": key[1]}))
            results.append({"layer": name, "layer_id": key[0], "ordinal": key[1],
                            "status": "not_comparable", "reason": "layer_missing_in_candidate"})
            continue
        b_metrics = b_layer.get("metrics") if isinstance(b_layer.get("metrics"), Mapping) else b_layer
        c_metrics = c_layer.get("metrics") if isinstance(c_layer.get("metrics"), Mapping) else c_layer
        metric_results = {
            metric: _metric("ms", b_metrics.get(metric), c_metrics.get(metric))
            for metric in ("busy_union_ms_p50", "wall_ms_p50", "host_gap_ms_p50")
        }
        compared = all(item["status"] == "compared" for item in metric_results.values())
        results.append({
            "layer": name,
            "layer_id": key[0],
            "ordinal": key[1],
            "status": "compared" if compared else "not_comparable",
            "match_basis": "event_sequence_shape+layer_id+ordinal",
            "metrics": metric_results,
        })
        if not compared:
            limits.append(_lim("layer_metric_missing", f"layer {key!r} has a missing metric"))
    return {
        "status": "comparable" if results and all(item["status"] == "compared" for item in results)
        and not limits else "comparable_with_limitations" if any(
            item["status"] == "compared" for item in results
        ) else "not_comparable",
        "layers": results,
        "baseline_source_content": reuse.get("baseline_source_content"),
        "candidate_source_content": reuse.get("candidate_source_content"),
        "limitations": limits,
    }
