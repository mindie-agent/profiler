"""C7 cross-run comparison for ``mindie-profile-summary/1`` reports.

[Role]
Pure read-only A/B comparison of C7 reports from ``analyze_profile``. Aligns
``window_accounting`` rows by ``(step, rank_id)`` across step, semantic-block,
and hierarchy metrics without reading DBs, contacting hosts, or re-running jobs.

[Invariants]
- Both inputs must declare ``schema_version == mindie-profile-summary/1``.
- Timing distributions (step/block/kernel p50) compare on homogeneous ranks even
  when ``clock_domain`` differs; ``clock_domain`` gates only cross-host timeline
  ordering, which requires sourced reference domains from ``by_rank``.
- Partial windows re-aggregate strictly from common ``window_accounting`` rows;
  declared p50s that disagree with aligned row medians mark ``not_comparable``.
- Unmatched rows inside/outside the common boundary stay in
  ``unpaired_observations`` / ``excluded_observations``; missing values stay
  ``None`` and confidence intervals use only aligned ``(step, rank_id)`` pairs.
- Layer alignment requires stable sequence shape plus ``layer_id + ordinal``
  identity (never display names, DB hashes, or query cache metadata alone).

[Timeouts & Locks]
None: CPU-only in-memory comparison with zero locks, I/O, or sleeps.

[Side-Effect Policy]
No filesystem, network, process, or global-state mutation; inputs stay read-only.
"""
from __future__ import annotations

import hashlib
import json
from statistics import median
from typing import Any, Iterable, Mapping, Sequence
from .compare_acceptance import (
    build_median_tables,
    classify_operator_sequence,
    compare_run_binding,
)
from .classify import EVENT_BLOCKS
from .compare_metric import metric as _metric, num as _num

from .compare_clock import (
    COMPARISON_SCHEMA, SUMMARY_SCHEMA, _BLOCK_ORDER, _CLOCK_COVERAGE_FIELDS,
    _COMPARISON_FIELD_ALIASES, _OPTIONAL_SCENE, _P50_REL_TOL, _RATIO_METRICS,
    _REQUIRED_SCENE, _ROW_METRICS, _block_declared, _block_row_evidence, _canon,
    _clear_derived, _clock_coverage_evidence, _clock_evidence, _column_values,
    _comparison_field, _cross_rank_projection, _declared_invalid, _declared_mismatch,
    _dedupe, _hash, _input_identity, _int, _layer_identity, _layer_ids, _lim,
    _p50_provenance, _rank_scope, _row_comparison_value, _row_map, _row_value, _scene,
    _schema_bad, _source_content, _steady_steps, _structural_reuse, _structure_parts,
    _window_rows,
)
from .compare_diff_tables import _assemble_comparable_diff
from .compare_evidence import (
    _block_share_evidence, _block_values, _excluded_observations, _hierarchy,
    _local_semantic_blocks, _local_step_accounting, _not_comparable, _observation_draft,
    _semantic_blocks_payload,
)

def compare_profiles(
    baseline: Any, candidate: Any, *, require_binding: bool = False,
    require_input_identity: bool = False,
) -> dict[str, Any]:
    """Compare C7 reports; CLI callers require identity, legacy API callers may inspect partial evidence."""
    hard: list[dict[str, Any]] = []
    limits: list[dict[str, Any]] = []
    matching: dict[str, Any] = {}
    applicability: dict[str, Any] = {}
    for label, summary in (("baseline", baseline), ("candidate", candidate)):
        problem = _schema_bad(summary, label)
        if problem:
            hard.append(problem)
    if hard:
        return _not_comparable(matching, applicability, hard, limits)
    assert isinstance(baseline, Mapping) and isinstance(candidate, Mapping)

    scene = _scene(baseline)
    other_scene = _scene(candidate)
    scene_source = scene.get("scene_source")
    if scene_source != "provided" or other_scene.get("scene_source") != "provided":
        hard.append(_lim("scene_not_provided", "scene facts were not provided; no scene match is assumed",
                         details={"baseline_scene_source": scene_source,
                                  "candidate_scene_source": other_scene.get("scene_source")}))
    matching["scene"] = {}
    for field in (*_REQUIRED_SCENE, *_OPTIONAL_SCENE):
        b_value, c_value = scene.get(field), other_scene.get(field)
        entry = {"baseline": b_value, "candidate": c_value, "status": "match"}
        if b_value is None or c_value is None:
            entry["status"] = "unavailable"
            limits.append(_lim("scene_field_unavailable", f"scene.{field} is missing from at least one report",
                               field=f"scene.{field}"))
            if field in _REQUIRED_SCENE:
                hard.append(_lim(f"scene_{field}_unavailable", f"scene.{field} is required for comparison"))
        elif b_value != c_value:
            entry["status"] = "mismatch"
            hard.append(_lim(f"scene_{field}_mismatch", f"scene.{field} differs",
                             field=f"scene.{field}", details={"baseline": b_value, "candidate": c_value}))
        matching["scene"][field] = entry

    b_clock, c_clock = scene.get("clock_domain"), other_scene.get("clock_domain")
    b_clock_names, c_clock_names = _clock_evidence(baseline), _clock_evidence(candidate)
    clock_entry = {
        "baseline": b_clock,
        "candidate": c_clock,
        "status": "match",
        "gates": ["cross_machine_timeline_alignment"],
        "duration_distribution_gate": False,
        "timeline_alignment_available": False,
        "timeline_alignment_basis": None,
        "timeline_alignment_reason": None,
        "legacy_rank_clock_names": {
            "baseline": b_clock_names,
            "candidate": c_clock_names,
        },
        "metric_policy": {
            "duration_distributions": "compared_by_metric_without_clock_domain",
            "absolute_timeline_alignment": "requires_equal_known_scene_clock_and_sourced_shared_reference",
            "event_ordering": "requires_equal_known_scene_clock_and_sourced_shared_reference",
            "source_clock_mapping": "scene.clock_domain alone is not a source mapping; "
                                    "window_accounting.clock_coverage must cover every aligned event "
                                    "with one shared sourced reference domain",
        },
        "basis": "local durations remain valid without cross-domain mapping; "
                 "absolute cross-machine timelines/ordering require sourced alignment",
        "cross_rank_evidence": {
            "baseline": _cross_rank_projection(baseline),
            "candidate": _cross_rank_projection(candidate),
        },
    }

    def known_clock(value: Any) -> bool:
        return value not in (None, "", "unknown")

    if not known_clock(b_clock) or not known_clock(c_clock):
        clock_entry["status"] = "unknown"
        clock_entry["timeline_alignment_reason"] = "scene_clock_domain_unknown"
        limits.append(
            _lim(
                "clock_domain_unknown",
                "clock_domain is unknown; duration distributions remain comparable, "
                "but cross-machine timeline alignment is unavailable",
                field="scene.clock_domain",
            )
        )
    elif b_clock != c_clock:
        clock_entry["status"] = "mismatch"
        clock_entry["timeline_alignment_reason"] = "scene_clock_domain_mismatch"
        limits.append(
            _lim(
                "clock_domain_mismatch",
                "clock_domain differs; duration distributions remain comparable, "
                "but cross-machine timeline alignment is unavailable",
                field="scene.clock_domain",
                details={"baseline": b_clock, "candidate": c_clock},
            )
        )
    else:
        # Scene labels match, but the fixed-scope source coverage is evaluated
        # only after the common step/rank rows are known.
        clock_entry["status"] = "match"
    matching["clock_domain"] = clock_entry

    b_input, c_input = _input_identity(baseline), _input_identity(candidate)
    input_entry = {
        "baseline_sha256": _hash(b_input) if b_input is not None else None,
        "candidate_sha256": _hash(c_input) if c_input is not None else None,
        "status": "unavailable",
    }
    # Strict callers need proof of workload equality; the default API keeps
    # partial-evidence comparisons available with explicit limitations.
    input_issues = hard if require_input_identity else limits
    if b_input is None and c_input is None:
        input_issues.append(_lim("input_identity_unavailable",
                           "C7 reports do not carry an input signature; workload equality is unverified"))
    elif b_input is None or c_input is None:
        input_issues.append(_lim("input_identity_incomplete",
                           "only one report declares scene.input_signature"))
    elif input_entry["baseline_sha256"] is None or input_entry["candidate_sha256"] is None:
        input_issues.append(_lim("input_identity_unhashable",
                           "scene.input_signature cannot be canonicalized for exact comparison"))
    elif input_entry["baseline_sha256"] != input_entry["candidate_sha256"]:
        input_entry["status"] = "mismatch"
        hard.append(_lim("input_identity_mismatch", "input signatures differ"))
    else:
        input_entry["status"] = "match"
    matching["input"] = input_entry

    binding_entry, binding_hard, binding_limits = compare_run_binding(
        baseline, candidate, required=require_binding
    )
    matching["run_binding"] = binding_entry
    hard.extend(binding_hard)
    limits.extend(binding_limits)

    b_ranks, b_rank_problem = _rank_scope(baseline)
    c_ranks, c_rank_problem = _rank_scope(candidate)
    rank_entry = {"baseline": b_ranks, "candidate": c_ranks, "common": None, "status": "unknown"}
    matching["rank_scope"] = rank_entry
    if b_rank_problem or c_rank_problem:
        hard.extend(item for item in (b_rank_problem, c_rank_problem) if item)
    else:
        assert b_ranks is not None and c_ranks is not None
        common_ranks = sorted(set(b_ranks) & set(c_ranks))
        rank_entry["common"] = common_ranks
        if not common_ranks:
            rank_entry["status"] = "disjoint"
            hard.append(_lim("rank_scope_disjoint", "the reports share no rank_id"))
        elif b_ranks == c_ranks:
            rank_entry["status"] = "match"
        else:
            rank_entry["status"] = "partial_overlap"
            limits.append(_lim("rank_scope_partial_overlap",
                               "rank scopes differ; only the common rank_id set is compared",
                               details={"baseline": b_ranks, "candidate": c_ranks}))

    # Invalid external containers are already reported by rank/step checks;
    # still preserve the remaining comparison receipt instead of dereferencing them.
    b_accounting, c_accounting = baseline.get("step_accounting"), candidate.get("step_accounting")
    b_slow = b_accounting.get("slowest_rank") if isinstance(b_accounting, Mapping) else None
    c_slow = c_accounting.get("slowest_rank") if isinstance(c_accounting, Mapping) else None
    slowest = {
        "baseline": b_slow.get("rank_id") if isinstance(b_slow, Mapping) else None,
        "candidate": c_slow.get("rank_id") if isinstance(c_slow, Mapping) else None,
        "status": "unavailable",
    }
    if slowest["baseline"] is not None and slowest["candidate"] is not None:
        slowest["status"] = "match" if slowest["baseline"] == slowest["candidate"] else "changed"
    matching["slowest_rank"] = slowest

    b_steps, b_step_problem = _steady_steps(baseline)
    c_steps, c_step_problem = _steady_steps(candidate)
    step_entry: dict[str, Any] = {
        "baseline": b_steps, "candidate": c_steps, "common": None, "missing": [],
        "alignment": None, "basis": None, "status": "unknown",
    }
    matching["steps"] = step_entry
    if b_step_problem or c_step_problem:
        hard.extend(item for item in (b_step_problem, c_step_problem) if item)

    common_steps = sorted(set(b_steps or []) & set(c_steps or []))
    common_ranks = sorted(set(b_ranks or []) & set(c_ranks or []))
    step_entry["common"] = common_steps
    if set(b_steps or []) == set(c_steps or []) and common_steps:
        step_entry["status"] = "same_steps"
    elif common_steps:
        step_entry["status"] = "partial_overlap"
        limits.append(_lim("partial_step_overlap",
                           "steady steps differ; only common steps are compared",
                           details={"baseline": b_steps, "candidate": c_steps}))
    else:
        step_entry["status"] = "disjoint"
        hard.append(_lim("steady_step_windows_disjoint", "the reports share no steady step"))
    if not common_steps or not common_ranks:
        step_entry["alignment"] = "not_comparable"
        step_entry["basis"] = "not_comparable"

    b_rows, b_row_limits = _window_rows(baseline)
    c_rows, c_row_limits = _window_rows(candidate)
    limits.extend(b_row_limits)
    limits.extend(c_row_limits)
    if b_rows is None or c_rows is None:
        hard.append(_lim("window_accounting_unavailable", "both reports need window_accounting rows"))
        hard_codes = [str(item.get("code")) for item in hard if item.get("code")]
        observation_rows = _observation_draft(
            b_rows, c_rows, common_steps, common_ranks, [], hard_codes
        )
        result = _not_comparable(matching, applicability, hard, limits)
        result["observation_rows"] = observation_rows
        result["local_step_accounting"] = {
            "baseline": _local_step_accounting(baseline),
            "candidate": _local_step_accounting(candidate),
        }
        result["local_semantic_blocks"] = {
            "baseline": _local_semantic_blocks(baseline),
            "candidate": _local_semantic_blocks(candidate),
        }
        return result

    expected_keys = [
        (step, rank) for step in common_steps for rank in common_ranks
    ]
    missing = [key for key in expected_keys if key not in b_rows or key not in c_rows]
    aligned = [key for key in expected_keys if key in b_rows and key in c_rows]
    step_entry["missing"] = [{"step": step, "rank_id": rank} for step, rank in missing]
    unpaired_observations: list[dict[str, Any]] = []
    for step, rank in missing:
        b_row, c_row = b_rows.get((step, rank)), c_rows.get((step, rank))
        present_rows = {
            side: dict(row)
            for side, row in (("baseline", b_row), ("candidate", c_row))
            if row is not None
        }
        unpaired_observations.append({
            "step": step,
            "rank_id": rank,
            "present_in": [side for side in ("baseline", "candidate") if side in present_rows],
            "absent_from": [side for side in ("baseline", "candidate") if side not in present_rows],
            "present_rows": present_rows,
        })
    excluded_observations = _excluded_observations(
        b_rows, c_rows, common_steps, common_ranks
    )
    hard_codes = [str(item.get("code")) for item in hard if item.get("code")]
    observation_rows = _observation_draft(
        b_rows, c_rows, common_steps, common_ranks, missing, hard_codes
    )
    if missing:
        limits.append(_lim("incomplete_common_observations",
                           "some common step/rank observations are absent; they are excluded, not imputed",
                           details={"missing": step_entry["missing"]}))
    applicability.update({
        "scope": "common steady steps and common rank_id set",
        "baseline_steps": b_steps,
        "candidate_steps": c_steps,
        "compared_steps": common_steps,
        "baseline_ranks": b_ranks,
        "candidate_ranks": c_ranks,
        "compared_ranks": common_ranks,
        "aligned_observation_count": len(aligned),
        "missing_observation_count": len(missing),
        "unpaired_observation_count": len(unpaired_observations),
        "excluded_observation_count": len(excluded_observations),
        "step_basis": step_entry.get("basis"),
        "input_identity": input_entry["status"],
        "notes": [],
    })
    if hard:
        result = _not_comparable(matching, applicability, hard, limits)
        result["observation_rows"] = observation_rows
        result["unpaired_observations"] = unpaired_observations
        result["excluded_observations"] = excluded_observations
        result["local_step_accounting"] = {
            "baseline": _local_step_accounting(baseline),
            "candidate": _local_step_accounting(candidate),
        }
        result["local_semantic_blocks"] = {
            "baseline": _local_semantic_blocks(baseline),
            "candidate": _local_semantic_blocks(candidate),
        }
        return result
    assert b_steps is not None and c_steps is not None
    assert b_ranks is not None and c_ranks is not None
    step_entry["alignment"] = "complete" if not missing else "incomplete"
    if not aligned:
        applicability["aligned_observation_count"] = 0
        hard.append(_lim("no_aligned_window_observations",
                         "no common step/rank observation exists in both reports"))
        result = _not_comparable(matching, applicability, hard, limits)
        result["observation_rows"] = observation_rows
        result["unpaired_observations"] = unpaired_observations
        result["excluded_observations"] = excluded_observations
        result["local_step_accounting"] = {
            "baseline": _local_step_accounting(baseline),
            "candidate": _local_step_accounting(candidate),
        }
        result["local_semantic_blocks"] = {
            "baseline": _local_semantic_blocks(baseline),
            "candidate": _local_semantic_blocks(candidate),
        }
        return result
    b_clock_coverage = _clock_coverage_evidence(b_rows, aligned, "baseline")
    c_clock_coverage = _clock_coverage_evidence(c_rows, aligned, "candidate")
    clock_entry["source_clock_evidence"] = {
        "basis": "window_accounting.clock_coverage",
        "scope": "all_aligned_window_rows",
        "baseline": b_clock_coverage,
        "candidate": c_clock_coverage,
        "union_span": {
            name: (evidence.get("clock_union_span")
                   if (evidence := clock_entry["cross_rank_evidence"].get(name)) else None)
            for name in ("baseline", "candidate")
        },
    }
    if clock_entry.get("status") == "match":
        coverage_reason = ""
        unavailable_reasons = [
            str(item.get("reason") or "clock_coverage_incomplete")
            for item in (b_clock_coverage, c_clock_coverage)
            if not item.get("available")
        ]
        if "clock_coverage_evidence_absent" in unavailable_reasons:
            # Missing endpoint proof is a named gap on either side; a partial
            # mapping on the other side must not hide it.
            coverage_reason = "clock_coverage_evidence_absent"
        elif unavailable_reasons:
            coverage_reason = unavailable_reasons[0]
        elif b_clock_coverage.get("reference_domain") != c_clock_coverage.get("reference_domain"):
            coverage_reason = "clock_reference_domain_mismatch"
        if coverage_reason:
            clock_entry["timeline_alignment_available"] = False
            clock_entry["timeline_alignment_reason"] = coverage_reason
        else:
            clock_entry["timeline_alignment_available"] = True
            clock_entry["timeline_alignment_basis"] = (
                "all_aligned_window_rows_shared_reference_domain:"
                + str(b_clock_coverage["reference_domain"])
            )
    exact = (set(b_steps) == set(c_steps) and set(b_ranks) == set(c_ranks) and not missing)
    step_entry["basis"] = "declared_p50" if exact else "recomputed_from_window_accounting"
    applicability.update({
        "scope": "common steady steps and common rank_id set",
        "baseline_steps": b_steps,
        "candidate_steps": c_steps,
        "compared_steps": common_steps,
        "baseline_ranks": b_ranks,
        "candidate_ranks": c_ranks,
        "compared_ranks": common_ranks,
        "aligned_observation_count": len(aligned),
        "missing_observation_count": len(missing),
        "unpaired_observation_count": len(unpaired_observations),
        "excluded_observation_count": len(excluded_observations),
        "step_basis": step_entry["basis"],
        "input_identity": input_entry["status"],
        "notes": [],
    })
    if not exact:
        applicability["notes"].append(
            "medians are re-aggregated from aligned window_accounting observations"
        )
    if input_entry["status"] != "match":
        applicability["notes"].append("workload identity is unverified")

    return _assemble_comparable_diff(aligned=aligned, applicability=applicability, b_rows=b_rows, baseline=baseline, c_rows=c_rows, candidate=candidate, clock_entry=clock_entry, exact=exact, excluded_observations=excluded_observations, hard=hard, limits=limits, matching=matching, observation_rows=observation_rows, step_entry=step_entry, unpaired_observations=unpaired_observations)

__all__ = ["COMPARISON_SCHEMA", "SUMMARY_SCHEMA", "compare_profiles"]
