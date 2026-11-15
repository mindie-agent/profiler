"""Explicit-workload A/B C7 profile comparison and provenance verification (compare_diff_tables).

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

from statistics import median
from typing import Any, Iterable, Mapping, Sequence
from .compare_acceptance import (
    build_median_tables,
    classify_operator_sequence,
    compare_run_binding,
)
from .compare_metric import metric as _metric, num as _num

from .compare_clock import (
    COMPARISON_SCHEMA, _BLOCK_ORDER, _RATIO_METRICS, _ROW_METRICS, _block_declared,
    _clear_derived, _column_values, _declared_invalid, _declared_mismatch, _dedupe, _lim,
    _p50_provenance, _structural_reuse,
)
from .compare_evidence import (
    _block_share_evidence, _block_values, _hierarchy, _local_semantic_blocks,
    _not_comparable, _semantic_blocks_payload,
)

def _assemble_comparable_diff(*, aligned, applicability, b_rows, baseline, c_rows, candidate, clock_entry, exact, excluded_observations, hard, limits, matching, observation_rows, step_entry, unpaired_observations) -> dict[str, Any]:
    accounting_b = baseline["step_accounting"]
    accounting_c = candidate["step_accounting"]
    assert isinstance(accounting_b, Mapping) and isinstance(accounting_c, Mapping)
    metrics: dict[str, Any] = {}
    partial = not exact
    report_integrity = "consistent" if exact else "not_checked"

    def add_step_metric(key: str, field: str, unit: str) -> None:
        nonlocal partial, report_integrity
        b_values, b_missing = _column_values(b_rows, aligned, field)
        c_values, c_missing = _column_values(c_rows, aligned, field)
        if b_missing or c_missing:
            metrics[key] = _metric(unit, None, None, b_values, c_values)
            metrics[key]["reason"] = "incomplete_observation_coverage"
            metrics[key]["missing_observations"] = {
                "baseline": [{"step": step, "rank_id": rank} for step, rank in b_missing],
                "candidate": [{"step": step, "rank_id": rank} for step, rank in c_missing],
            }
            limits.append(_lim("metric_incomplete_observation_coverage",
                               f"{key} is null for at least one aligned observation",
                               field=f"step_accounting.{key}"))
            partial = True
            return
        b_declared, c_declared = accounting_b.get(key), accounting_c.get(key)
        b_value = b_declared if exact else median(b_values)
        c_value = c_declared if exact else median(c_values)
        entry = _metric(unit, b_value, c_value, b_values, c_values)
        provenance = {
            "baseline": _p50_provenance(b_declared, b_values, basis=step_entry["basis"]),
            "candidate": _p50_provenance(c_declared, c_values, basis=step_entry["basis"]),
        }
        entry["p50_provenance"] = provenance
        invalid_sides = [side for side, prov in provenance.items() if _declared_invalid(prov)]
        mismatch_sides = [side for side, prov in provenance.items() if _declared_mismatch(prov)]
        if exact and (invalid_sides or mismatch_sides):
            entry["status"] = "not_comparable"
            entry["reason"] = (
                "declared_p50_not_numeric" if invalid_sides
                else "declared_p50_inconsistent_with_window_accounting"
            )
            _clear_derived(entry)
            report_integrity = "failed"
            for side, prov in provenance.items():
                if _declared_invalid(prov):
                    limits.append(_lim(
                        "declared_p50_not_numeric",
                        f"{key} {side} declared p50 is not a finite number",
                        field=f"step_accounting.{key}",
                        details={"side": side, "declared_value": prov["declared_value"]},
                    ))
                elif _declared_mismatch(prov):
                    limits.append(_lim(
                        "declared_p50_inconsistent_with_window_accounting",
                        f"{key} {side} declared p50 disagrees with its own window_accounting rows",
                        field=f"step_accounting.{key}",
                        details={
                            "side": side,
                            "declared": prov["declared_p50"],
                            "recomputed": prov["recomputed_from_window_accounting"],
                        },
                    ))
            partial = True
        metrics[key] = entry
        if entry["status"] != "compared":
            partial = True
            if entry.get("reason") not in {
                "declared_p50_inconsistent_with_window_accounting",
                "declared_p50_not_numeric",
            }:
                limits.append(_lim("metric_value_missing", f"{key} is missing from a report p50",
                                   field=f"step_accounting.{key}"))

    for key, field in _ROW_METRICS.items():
        add_step_metric(key, field, "ms")
    for key in _RATIO_METRICS:
        add_step_metric(key, key, "ratio")

    b_blocks, b_block_limits = _block_declared(baseline)
    c_blocks, c_block_limits = _block_declared(candidate)
    limits.extend(b_block_limits)
    limits.extend(c_block_limits)
    block_names = sorted(set(b_blocks) | set(c_blocks) | set(_BLOCK_ORDER),
                         key=lambda name: (_BLOCK_ORDER.index(name) if name in _BLOCK_ORDER else len(_BLOCK_ORDER), name))
    block_results: list[dict[str, Any]] = []
    b_share_evidence = _block_share_evidence(b_rows, aligned)
    c_share_evidence = _block_share_evidence(c_rows, aligned)
    for name in block_names:
        b_block, c_block = b_blocks.get(name), c_blocks.get(name)
        b_values, b_missing = _block_values(b_rows, aligned, name, "block_union_ms")
        c_values, c_missing = _block_values(c_rows, aligned, name, "block_union_ms")
        entry = {
            "block": name, "status": "not_comparable",
            "baseline_busy_union_ms_p50": None, "candidate_busy_union_ms_p50": None,
            "delta_ms": None, "relative_delta_pct": None,
            "baseline_share_of_busy_pct": None, "candidate_share_of_busy_pct": None,
            "share_delta_pp": None, "confidence_interval": None,
            "confidence_interval_reason": "per_sample_observations_unavailable",
            "share_denominator": "sum_of_attributed_block_unions",
            "baseline_share_denominator_ms_p50": None,
            "candidate_share_denominator_ms_p50": None,
            "share_integrity": None,
        }
        if b_missing or c_missing:
            entry["reason"] = "incomplete_block_observation_coverage"
            entry["missing_observations"] = {
                "baseline": [{"step": step, "rank_id": rank} for step, rank in b_missing],
                "candidate": [{"step": step, "rank_id": rank} for step, rank in c_missing],
            }
            limits.append(_lim("block_incomplete_observation_coverage",
                               f"{name} block union is null for at least one aligned observation",
                               details={"block": name}))
            partial = True
            block_results.append(entry)
            continue
        b_raw_declared = b_block.get("busy_union_ms_p50") if b_block is not None else None
        c_raw_declared = c_block.get("busy_union_ms_p50") if c_block is not None else None
        b_declared = _num(b_raw_declared)
        c_declared = _num(c_raw_declared)
        b_value = b_declared if exact else median(b_values)
        c_value = c_declared if exact else median(c_values)
        p50_provenance = {
            "baseline": _p50_provenance(b_raw_declared, b_values, basis=step_entry["basis"]),
            "candidate": _p50_provenance(c_raw_declared, c_values, basis=step_entry["basis"]),
        }
        entry["p50_provenance"] = p50_provenance
        union_invalid = exact and any(_declared_invalid(prov) for prov in p50_provenance.values())
        union_mismatch = exact and any(_declared_mismatch(prov) for prov in p50_provenance.values())
        if exact and (union_invalid or union_mismatch):
            entry["status"] = "not_comparable"
            entry["reason"] = (
                "declared_block_p50_not_numeric" if union_invalid
                else "declared_block_p50_inconsistent_with_window_accounting"
            )
            entry["baseline_busy_union_ms_p50"] = b_declared
            entry["candidate_busy_union_ms_p50"] = c_declared
            entry["baseline_recomputed_busy_union_ms_p50"] = (
                round(float(median(b_values)), 6) if b_values else None
            )
            entry["candidate_recomputed_busy_union_ms_p50"] = (
                round(float(median(c_values)), 6) if c_values else None
            )
            _clear_derived(entry)
            entry["confidence_interval"] = None
            entry["confidence_interval_reason"] = "declared_p50_invalid"
            report_integrity = "failed"
            for side, prov in p50_provenance.items():
                if _declared_invalid(prov):
                    limits.append(_lim(
                        "declared_block_p50_not_numeric",
                        f"{name} {side} declared busy_union_ms_p50 is not a finite number",
                        details={"block": name, "side": side,
                                 "declared_value": prov["declared_value"]},
                    ))
                elif _declared_mismatch(prov):
                    limits.append(_lim(
                        "declared_block_p50_inconsistent_with_window_accounting",
                        f"{name} {side} declared busy_union_ms_p50 disagrees with its own rows",
                        details={
                            "block": name, "side": side,
                            "declared": prov["declared_p50"],
                            "recomputed": prov["recomputed_from_window_accounting"],
                        },
                    ))
            partial = True
        elif b_value is None or c_value is None:
            entry["reason"] = "semantic_block_value_missing"
            limits.append(_lim("semantic_block_value_missing", f"{name} has no declared busy_union_ms_p50",
                               details={"block": name}))
            partial = True
            block_results.append(entry)
            continue
        else:
            entry["baseline_busy_union_ms_p50"] = b_value
            entry["candidate_busy_union_ms_p50"] = c_value
            entry["delta_ms"] = c_value - b_value
            entry["status"] = "compared"
            if b_value != 0:
                entry["relative_delta_pct"] = (c_value - b_value) / abs(b_value) * 100.0
            metric_entry = _metric("ms", b_value, c_value, b_values, c_values)
            entry["confidence_interval"] = metric_entry["confidence_interval"]
            if metric_entry.get("confidence_interval_reason"):
                entry["confidence_interval_reason"] = metric_entry["confidence_interval_reason"]

        if name == "Host_Gap":
            # Host_Gap is device idle, not an attributed EVENT_BLOCK.  It has no
            # share and must not invalidate the six-block denominator evidence.
            entry["share_delta_pp"] = None
            entry["share_integrity"] = None
            entry["baseline_share_of_busy_pct"] = None
            entry["candidate_share_of_busy_pct"] = None
            block_results.append(entry)
            continue

        b_share_values = b_share_evidence["shares"].get(name, [])
        c_share_values = c_share_evidence["shares"].get(name, [])
        b_share_recomputed = round(float(median(b_share_values)), 6) if b_share_values else None
        c_share_recomputed = round(float(median(c_share_values)), 6) if c_share_values else None
        b_share_raw = b_block.get("share_of_busy_pct") if b_block is not None else None
        c_share_raw = c_block.get("share_of_busy_pct") if c_block is not None else None
        b_share_declared = _num(b_share_raw)
        c_share_declared = _num(c_share_raw)
        b_share = b_share_recomputed if b_share_recomputed is not None else b_share_declared
        c_share = c_share_recomputed if c_share_recomputed is not None else c_share_declared
        share_provenance = {
            "baseline": _p50_provenance(b_share_raw, b_share_values, basis=step_entry["basis"]),
            "candidate": _p50_provenance(c_share_raw, c_share_values, basis=step_entry["basis"]),
        }
        if exact and b_share_declared is None and b_share_values and not _declared_invalid(share_provenance["baseline"]):
            share_provenance["baseline"]["comparison_basis"] = "recomputed_missing_declaration"
        if exact and c_share_declared is None and c_share_values and not _declared_invalid(share_provenance["candidate"]):
            share_provenance["candidate"]["comparison_basis"] = "recomputed_missing_declaration"

        b_denominator_values = b_share_evidence["denominators"]
        c_denominator_values = c_share_evidence["denominators"]
        b_denominator_raw = b_block.get("share_denominator_ms_p50") if b_block is not None else None
        c_denominator_raw = c_block.get("share_denominator_ms_p50") if c_block is not None else None
        b_denominator_declared = _num(b_denominator_raw)
        c_denominator_declared = _num(c_denominator_raw)
        denominator_provenance = {
            "baseline": _p50_provenance(b_denominator_raw, b_denominator_values, basis=step_entry["basis"]),
            "candidate": _p50_provenance(c_denominator_raw, c_denominator_values, basis=step_entry["basis"]),
        }
        expected_denominator = "sum_of_attributed_block_unions"
        b_den_definition = str(b_block.get("share_denominator") or "") if b_block is not None else ""
        c_den_definition = str(c_block.get("share_denominator") or "") if c_block is not None else ""
        definition_ok = (
            (not b_den_definition or b_den_definition == expected_denominator)
            and (not c_den_definition or c_den_definition == expected_denominator)
            and (not b_den_definition or not c_den_definition or b_den_definition == c_den_definition)
        )

        b_zero = [
            row for row in b_share_evidence["records"]
            if row["complete"] and row["denominator"] in (None, 0)
        ]
        c_zero = [
            row for row in c_share_evidence["records"]
            if row["complete"] and row["denominator"] in (None, 0)
        ]
        b_complete = (
            b_share_evidence["complete"] and len(b_denominator_values) == len(aligned)
            and not b_zero and len(b_share_values) == len(aligned)
        )
        c_complete = (
            c_share_evidence["complete"] and len(c_denominator_values) == len(aligned)
            and not c_zero and len(c_share_values) == len(aligned)
        )
        evidence_complete = b_complete and c_complete
        b_missing = [
            *b_share_evidence["missing"], *b_share_evidence["invalid"],
        ]
        c_missing = [
            *c_share_evidence["missing"], *c_share_evidence["invalid"],
        ]
        entry["share_evidence"] = {
            "baseline": {
                "complete": b_complete,
                "missing": b_missing,
                "zero_denominator": b_zero,
            },
            "candidate": {
                "complete": c_complete,
                "missing": c_missing,
                "zero_denominator": c_zero,
            },
        }
        entry["share_p50_provenance"] = share_provenance
        entry["share_denominator_provenance"] = denominator_provenance
        entry["share_denominator"] = expected_denominator
        entry["baseline_declared_share_of_busy_pct"] = b_share_declared
        entry["candidate_declared_share_of_busy_pct"] = c_share_declared
        entry["baseline_share_of_busy_pct"] = b_share
        entry["candidate_share_of_busy_pct"] = c_share

        if not evidence_complete:
            entry["share_delta_pp"] = None
            entry["share_integrity"] = "not_verifiable"
            if report_integrity == "consistent":
                report_integrity = "incomplete"
            limits.append(_lim(
                "share_evidence_incomplete",
                f"{name} share denominator/share cannot be verified from complete EVENT_BLOCKS evidence",
                details={
                    "block": name,
                    "baseline_missing": b_missing,
                    "candidate_missing": c_missing,
                    "baseline_zero_denominator": b_zero,
                    "candidate_zero_denominator": c_zero,
                },
            ))
            entry["share_denominator_status"] = {
                "baseline": "not_verifiable_missing_blocks" if not b_complete else "consistent",
                "candidate": "not_verifiable_missing_blocks" if not c_complete else "consistent",
                "definition": "sum_of_attributed_block_unions" if definition_ok else "unknown_or_mismatched_definition",
            }
            entry["baseline_share_denominator_ms_p50"] = None
            entry["candidate_share_denominator_ms_p50"] = None
            partial = True
        else:
            b_den_value = b_denominator_declared if exact and b_denominator_declared is not None else round(float(median(b_denominator_values)), 6)
            c_den_value = c_denominator_declared if exact and c_denominator_declared is not None else round(float(median(c_denominator_values)), 6)
            if exact:
                if _declared_invalid(denominator_provenance["baseline"]):
                    b_den_status = "not_numeric"
                elif _declared_mismatch(denominator_provenance["baseline"]):
                    b_den_status = "inconsistent"
                    b_den_value = round(float(median(b_denominator_values)), 6)
                elif b_denominator_declared is None:
                    b_den_status = "recomputed_missing_declaration"
                else:
                    b_den_status = "consistent"
                if _declared_invalid(denominator_provenance["candidate"]):
                    c_den_status = "not_numeric"
                elif _declared_mismatch(denominator_provenance["candidate"]):
                    c_den_status = "inconsistent"
                    c_den_value = round(float(median(c_denominator_values)), 6)
                elif c_denominator_declared is None:
                    c_den_status = "recomputed_missing_declaration"
                else:
                    c_den_status = "consistent"
            else:
                b_den_status = c_den_status = "recomputed_from_common_rows"
                b_den_value = round(float(median(b_denominator_values)), 6)
                c_den_value = round(float(median(c_denominator_values)), 6)
            entry["baseline_share_denominator_ms_p50"] = b_den_value
            entry["candidate_share_denominator_ms_p50"] = c_den_value
            entry["share_denominator_status"] = {
                "baseline": b_den_status,
                "candidate": c_den_status,
                "definition": "sum_of_attributed_block_unions" if definition_ok else "unknown_or_mismatched_definition",
            }

            denominator_conflict = False
            if not definition_ok:
                denominator_conflict = True
            elif exact and (
                b_den_status in {"not_numeric", "inconsistent"}
                or c_den_status in {"not_numeric", "inconsistent"}
            ):
                denominator_conflict = True
            share_declared_conflict = exact and (
                _declared_invalid(share_provenance["baseline"])
                or _declared_invalid(share_provenance["candidate"])
                or _declared_mismatch(share_provenance["baseline"])
                or _declared_mismatch(share_provenance["candidate"])
            )
            row_conflict = bool(b_share_evidence["row_conflicts"] or c_share_evidence["row_conflicts"])
            if denominator_conflict or share_declared_conflict or row_conflict:
                entry["share_delta_pp"] = None
                entry["share_integrity"] = "failed"
                report_integrity = "failed"
                if denominator_conflict:
                    if "not_numeric" in {b_den_status, c_den_status}:
                        code = "declared_block_share_denominator_not_numeric"
                    elif "inconsistent" in {b_den_status, c_den_status}:
                        code = "declared_block_share_denominator_inconsistent_with_window_accounting"
                    elif not definition_ok:
                        code = "share_denominator_definition_mismatch"
                    else:
                        code = "share_denominator_unverified"
                    limits.append(_lim(
                        code,
                        f"{name} share denominator is not the declared/verified complete attributed block sum",
                        details={
                            "block": name,
                            "baseline": {"status": b_den_status,
                                         "declared_value": denominator_provenance["baseline"]["declared_value"]},
                            "candidate": {"status": c_den_status,
                                          "declared_value": denominator_provenance["candidate"]["declared_value"]},
                            "definition_ok": definition_ok,
                        },
                    ))
                if share_declared_conflict:
                    for side, prov in share_provenance.items():
                        if _declared_invalid(prov):
                            limits.append(_lim(
                                "declared_block_share_not_numeric",
                                f"{name} {side} declared share_of_busy_pct is not a finite number",
                                details={"block": name, "side": side,
                                         "declared_value": prov["declared_value"]},
                            ))
                        elif _declared_mismatch(prov):
                            limits.append(_lim(
                                "declared_block_share_inconsistent_with_window_accounting",
                                f"{name} {side} declared share_of_busy_pct disagrees with complete unions",
                                details={
                                    "block": name, "side": side,
                                    "declared": prov["declared_p50"],
                                    "recomputed": prov["recomputed_from_window_accounting"],
                                },
                            ))
                if row_conflict:
                    limits.append(_lim(
                        "block_share_column_conflicts_with_complete_unions",
                        f"{name} recorded block_share_pct disagrees with complete EVENT_BLOCKS unions",
                        details={
                            "block": name,
                            "conflicts": [
                                *b_share_evidence["row_conflicts"],
                                *c_share_evidence["row_conflicts"],
                            ],
                        },
                    ))
                partial = True
            elif b_share is not None and c_share is not None:
                entry["share_delta_pp"] = c_share - b_share
                entry["share_integrity"] = "consistent" if exact else "recomputed"
            elif name != "Host_Gap" or (b_share is not None) != (c_share is not None):
                limits.append(_lim("semantic_block_share_missing", f"{name} has no comparable share",
                                   details={"block": name}))
        block_results.append(entry)

    reuse = _structural_reuse(baseline, candidate)
    hierarchy = _hierarchy(baseline, candidate, reuse)
    limits.extend(hierarchy.get("limitations", []))
    operator_sequence = classify_operator_sequence(baseline, candidate)
    if operator_sequence.get("status") == "classified" and hierarchy.get("status") != "comparable":
        operator_sequence["reuse_recommendation"] = "unavailable_without_explicit_layers"
    limits.extend(operator_sequence.get("limitations", []))
    applicability["report_integrity"] = report_integrity
    applicability["declared_p50_consistency"] = (
        "checked_against_window_accounting" if exact
        else "not_applicable_recomputed_from_common_rows"
    )
    applicability["clock_timeline_alignment"] = clock_entry["timeline_alignment_available"]
    if not any(entry["status"] == "compared" for entry in metrics.values()):
        hard.append(_lim("no_comparable_step_metrics", "no step metric could be compared"))
        result = _not_comparable(matching, applicability, hard, limits, reuse)
        # Keep the per-metric receipts even when no metric is comparable, so an
        # integrity failure is inspectable instead of being collapsed to a
        # generic non-comparable receipt.
        result["step_accounting"] = {"status": "not_comparable", "metrics": metrics}
        result["observation_rows"] = observation_rows
        result["semantic_blocks"] = _semantic_blocks_payload(block_results)
        result["hierarchy"] = hierarchy
        result["operator_sequence"] = operator_sequence
        result["tables"] = build_median_tables(metrics, block_results, hierarchy)
        result["unpaired_observations"] = unpaired_observations
        result["excluded_observations"] = excluded_observations
        result["local_semantic_blocks"] = {
            "baseline": _local_semantic_blocks(baseline),
            "candidate": _local_semantic_blocks(candidate),
        }
        return result

    if any(entry["status"] != "compared" for entry in metrics.values()):
        partial = True
    if hierarchy.get("status") != "comparable":
        partial = True
    applicability["confidence_intervals"] = (
        "computed_from_aligned_window_observations"
        if any(entry.get("confidence_interval") for entry in metrics.values())
        else "unavailable_fewer_than_6_aligned_observations"
    )
    status = "comparable_with_limitations" if partial or limits else "comparable"
    tables = build_median_tables(metrics, block_results, hierarchy)
    return {
        "schema_version": COMPARISON_SCHEMA,
        "status": status,
        "comparable": True,
        "partial": partial,
        "reasons": [],
        "limitations": _dedupe(limits),
        "matching": matching,
        "applicability": applicability,
        "observation_rows": observation_rows,
        "unpaired_observations": unpaired_observations,
        "excluded_observations": excluded_observations,
        "structural_reuse": reuse,
        "step_accounting": {
            "status": "comparable" if all(
                entry["status"] == "compared" for entry in metrics.values()
            ) else "comparable_with_limitations",
            "metrics": metrics,
        },
        "semantic_blocks": {
            "status": "comparable" if block_results and all(
                entry["status"] == "compared" and entry.get("share_integrity") != "failed"
                for entry in block_results
            ) else "comparable_with_limitations" if block_results else "not_comparable",
            "blocks": block_results,
        },
        "hierarchy": hierarchy,
        "operator_sequence": operator_sequence,
        "tables": tables,
    }
