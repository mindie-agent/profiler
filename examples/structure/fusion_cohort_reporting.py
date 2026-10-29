"""Report conditional cohort errors under the shared per-call accuracy policy.

[Role] Aggregate saved comparisons and separate large errors from small calls.
[Invariants] Cohorts determine acceptance before family aggregation. Family means
  are call-count weighted; reference costs never enter scored denominators.
  Tolerance does not modify predictions or prove a measured launch overhead.
[Timeouts & Locks] Finite saved comparison metadata; no subprocesses or locks.
[Side-Effect Policy] Writes requested family overview JSON and Markdown only.
"""
from __future__ import annotations

from collections import Counter
import json

from mindie_sim.cohort_accuracy import accuracy_fields, accuracy_policy

from fusion_replay_cases import _hash, _read
from forward_scoreboard import body_scoreboard


TIERS = ("relative_15pct", "absolute_15us")


def _aggregate(rows):
    scored = [row for row in rows if row["status"] == "compared"]
    passed = [row for row in scored if row["accuracy_pass"]]
    failed = [row for row in scored if row["accuracy_pass"] is False]
    count = sum(row["observed"]["event_count"] for row in scored)
    actual = sum(row["observed"]["activity_sum_ns"] / 1e6 for row in scored)
    predicted = sum(row["prediction"]["observed_call_count_total_ms"] for row in scored)
    tiers = {row["accuracy_tier"] for row in scored}
    return {
        "cohort_count": len(scored),
        "passed_cohort_count": len(passed), "failed_cohort_count": len(failed),
        "scored_event_count": count,
        "passed_event_count": sum(row["observed"]["event_count"] for row in passed),
        "failed_event_count": sum(row["observed"]["event_count"] for row in failed),
        "scored_activity_sum_ms": actual, "predicted_scored_activity_sum_ms": predicted,
        "signed_activity_residual_ms": predicted - actual if scored else None,
        "relative_activity_error": predicted / actual - 1 if actual > 0 else None,
        "observed_per_call_us": actual * 1000 / count if count else None,
        "predicted_per_call_us": predicted * 1000 / count if count else None,
        "per_call_diff_us": (predicted - actual) * 1000 / count if count else None,
        "abs_error_per_call_us": abs(predicted - actual) * 1000 / count if count else None,
        "accuracy_tier": next(iter(tiers)) if len(tiers) == 1 else "mixed" if tiers else "unscored",
        "accuracy_pass": not failed if scored else None,
        "accuracy_status": (
            "outside_tolerance" if failed else "unscored" if not scored else
            "within_launch_floor_tolerance" if tiers == {"absolute_15us"} else
            "within_relative_tolerance" if tiers == {"relative_15pct"} else "within_tolerance"),
        "accuracy_tolerance": scored[0]["accuracy_tolerance"] if len(tiers) == 1 else None,
        "accuracy_policy": accuracy_policy()["version"],
        "failed_observed_activity_sum_ms": sum(
            row["observed"]["activity_sum_ns"] / 1e6 for row in failed),
        "failed_absolute_activity_residual_ms": sum(
            abs(row["prediction"]["observed_call_count_total_ms"]
                - row["observed"]["activity_sum_ns"] / 1e6) for row in failed),
        "max_absolute_per_call_diff_us": max(
            (abs(row["per_call_diff_us"]) for row in scored), default=None),
    }


def _by_tier(rows):
    return {tier: _aggregate([row for row in rows if row["accuracy_tier"] == tier])
            for tier in TIERS}


def _priority(family):
    tiers = family["accuracy_by_tier"]
    large, micro = (tiers[tier] for tier in TIERS)
    if large["failed_cohort_count"]:
        return (0, -large["failed_observed_activity_sum_ms"], family["operator_type"])
    if micro["failed_cohort_count"]:
        return (1, -micro["max_absolute_per_call_diff_us"], family["operator_type"])
    if family["scored_event_count"]:
        return (2, -family["scored_activity_sum_ms"], family["operator_type"])
    return (3, -(family["activity_sum_ns"] or 0), family["operator_type"])


def family_table(mapping, comparison):
    grouped, all_rows = {}, []
    for window_index, window in enumerate(comparison["windows"]):
        for original in window["cohorts"]:
            row = {**original, **accuracy_fields(original)}
            grouped.setdefault((window_index, row["native_operator_type"]), []).append(row)
            all_rows.append(row)
    families = []
    for window_index, window in enumerate(mapping["windows"]):
        for operator in window["operators"]:
            kind = operator["operator_type"]
            cohorts = grouped.get((window_index, kind), [])
            scored = [row for row in cohorts if row["status"] == "compared"]
            references = [row for row in cohorts if row["status"] == "reference_only"]
            unscored = Counter(operator.get("cohort_excluded_event_counts", {}))
            for row in cohorts:
                if row["status"] != "compared":
                    unscored[row["reason"]] += row["observed"]["event_count"]
            missing = operator["event_count"] - sum(
                row["observed"]["event_count"] for row in scored) - sum(unscored.values())
            if "cohort_excluded_event_counts" in operator and missing:
                raise ValueError("native_family_unscored_denominator_inconsistent")
            families.append({
                **operator, **_aggregate(cohorts), "cohort_count": len(cohorts),
                "activity_sum_ns": operator.get("activity_sum_ns"),
                "complete_activity_sum_ns": operator.get("complete_activity_sum_ns"),
                "cohort_status_counts": dict(Counter(row["status"] for row in cohorts)),
                "cohort_event_count": sum(row["observed"]["event_count"] for row in cohorts),
                "reference_event_count": sum(row["observed"]["event_count"] for row in references),
                "reference_activity_sum_ms": sum(
                    row["observed"]["activity_sum_ns"] / 1e6 for row in references),
                "predicted_reference_activity_sum_ms": sum(
                    row["prediction"]["observed_call_count_total_ms"] for row in references),
                "accuracy_by_tier": _by_tier(cohorts),
                "unscored_event_reason_counts": dict(unscored),
                "unscored_events_without_reason_metadata": missing,
                "cohorts": [{
                    key: row.get(key) for key in (
                        "cohort_id", "target_kind", "physical_signature", "contract_scope",
                        "structural_classification", "status", "reason", "observed",
                        "declared_instance_count", "declared_layer_count", "multiplicity",
                        "prediction", "comparison", "observed_per_call_us", "predicted_per_call_us",
                        "per_call_diff_us", "abs_error_per_call_us", "accuracy_tier",
                        "accuracy_pass", "accuracy_status", "accuracy_tolerance", "accuracy_policy")}
                    for row in cohorts],
            })
    return {
        "kind": "complete_capture_native_family_conditional_errors",
        "graph_id": mapping["graph_id"],
        "event_denominator": "all_valid_positive_duration_events_in_complete_capture_window",
        "activity_denominator": "sum_of_event_intersections_with_window; overlapping_events_count_separately",
        "sort_basis": "large_failed_cohort_activity_then_micro_absolute_per_call_error",
        "accuracy_policy": accuracy_policy(),
        "accuracy_summary": _by_tier(all_rows),
        "families": sorted(families, key=_priority),
        "limitations": [
            "Every native type remains included, including types with no valid cohort.",
            "Per-call family means use scored calls only and are weighted by event count.",
            "Pass/fail is computed per cohort; signed family averages cannot cancel failed cohorts.",
            "Passed/failed event counts weight cohort-mean decisions; they are not per-event error tests.",
            "The absolute tolerance is an acceptance allowance, not measured launch-overhead attribution.",
            "Residuals and pass rates exclude reference, clipped, failed and unmatched events.",
            "Activity sums may overlap and are not full model latency or throughput.",
        ],
    }


def _value(value, digits=3):
    return "-" if value is None else f"{value:.{digits}f}"


def _percentage(value):
    return "-" if value is None else f"{value * 100:+.1f}%"


def _family_rows(lines, groups, *, accepted):
    if not groups:
        lines.extend(["None.", ""])
        return
    lines.extend([
        "| Native family | Tier | All events | Scored events | Reference events | Scored observed ms | Predicted ms | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Pass / fail cohorts |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for family, tier in groups:
        row = _aggregate([
            cohort for cohort in family["cohorts"]
            if cohort["accuracy_tier"] == tier and cohort["accuracy_pass"] is accepted])
        lines.append(
            f"| {family['operator_type']} | {tier} | {family['event_count']} | "
            f"{row['scored_event_count']} | {family['reference_event_count']} | "
            f"{row['scored_activity_sum_ms']:.3f} | {row['predicted_scored_activity_sum_ms']:.3f} | "
            f"{_value(row['observed_per_call_us'])} | {_value(row['predicted_per_call_us'])} | "
            f"{_value(row['per_call_diff_us'])} | {_percentage(row['relative_activity_error'])} | "
            f"{row['passed_cohort_count']} / {row['failed_cohort_count']} |")
    lines.append("")


def _variant_markdown(summary, table):
    lines = [
        f"## {summary['declaration_key']} / {summary['variant']}", "",
        f"Graph: `{summary['graph_id']}`.", "",
        "| Tier | Compared cohorts | Passed | Failed | Passed events | Failed events |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for tier, counts in table["accuracy_summary"].items():
        lines.append(
            f"| {tier} | {counts['cohort_count']} | {counts['passed_cohort_count']} | "
            f"{counts['failed_cohort_count']} | {counts['passed_event_count']} | "
            f"{counts['failed_event_count']} |")
    lines.extend(["", "### Large-call errors: observed mean > 50 us", ""])
    large = [(family, TIERS[0]) for family in table["families"]
             if family["accuracy_by_tier"][TIERS[0]]["failed_cohort_count"]]
    _family_rows(lines, sorted(large, key=lambda pair: (
        -pair[0]["accuracy_by_tier"][pair[1]]["failed_observed_activity_sum_ms"],
        pair[0]["operator_type"])), accepted=False)
    lines.extend(["### Small-call errors: absolute per-call difference > 15 us", ""])
    micro = [(family, TIERS[1]) for family in table["families"]
             if family["accuracy_by_tier"][TIERS[1]]["failed_cohort_count"]]
    _family_rows(lines, sorted(micro, key=lambda pair: (
        -pair[0]["accuracy_by_tier"][pair[1]]["max_absolute_per_call_diff_us"],
        pair[0]["operator_type"])), accepted=False)
    lines.extend(["### Within tolerance: separate from Top Errors", ""])
    passing = [(family, tier) for family in table["families"] for tier in TIERS
               if family["accuracy_by_tier"][tier]["passed_cohort_count"]]
    _family_rows(lines, sorted(passing, key=lambda pair: (
        pair[1], -pair[0]["accuracy_by_tier"][pair[1]]["scored_activity_sum_ms"])), accepted=True)
    unresolved = [row for row in table["families"] if row["unscored_event_reason_counts"]]
    lines.extend([
        "### Unscored coverage: highest activity families", "",
        "| Native family | All events | All activity ms | Reference events | Unscored reasons |",
        "| --- | ---: | ---: | ---: | --- |",
    ])
    for row in sorted(unresolved, key=lambda item: -(item["activity_sum_ns"] or 0))[:10]:
        reasons = ", ".join(f"{key} ({count})" for key, count in sorted(
            row["unscored_event_reason_counts"].items(), key=lambda item: -item[1])[:2])
        activity = row["activity_sum_ns"]
        lines.append(
            f"| {row['operator_type']} | {row['event_count']} | "
            f"{_value(None if activity is None else activity / 1e6)} | "
            f"{row['reference_event_count']} | {reasons.replace('|', '/')} |")
    if not unresolved:
        lines.append("| - | 0 | - | 0 | None |")
    lines.extend([
        "", "### Subgraph cohorts", "",
        "| Subgraph native family | Cohort | Events | Status | Observed us/call | Predicted us/call | Per-call diff us | Relative error | Tier | Pass |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ])
    subgraphs = [(family["operator_type"], row) for family in table["families"]
                 for row in family["cohorts"] if row["target_kind"] == "subgraph"]
    for kind, row in subgraphs:
        error = (row["comparison"] or {}).get("per_call_mean", {}).get("relative_error")
        passed = "-" if row["accuracy_pass"] is None else str(row["accuracy_pass"]).lower()
        lines.append(
            f"| {kind} | {row['cohort_id'][-12:]} | {row['observed']['event_count']} | "
            f"{row['status']} | {_value(row['observed_per_call_us'])} | "
            f"{_value(row['predicted_per_call_us'])} | {_value(row['per_call_diff_us'])} | "
            f"{_percentage(error)} | {row['accuracy_tier']} | {passed} |")
    if not subgraphs:
        lines.append("| - | - | 0 | No valid subgraph cohort | - | - | - | - | - | - |")
    return [*lines, ""]


def _family_index(summary, table, identity):
    return {
        "capture_key": summary["capture_key"], "variant": summary["variant"],
        "declaration_key": summary["declaration_key"], "graph_id": summary["graph_id"],
        "source_identity": summary["source_identity"],
        "file": identity["file"], "sha256": identity["sha256"],
        "family_count": len(table["families"]),
        "event_count": sum(row["event_count"] for row in table["families"]),
        "accuracy_summary": table["accuracy_summary"],
    }


def write_family_overview(args, captures):
    variants, sections, summaries = [], [], {tier: Counter() for tier in TIERS}
    statuses = Counter()
    for capture in captures:
        for report in capture["reports"]:
            summary_path = args.output_dir / report["report"]
            summary = _read(summary_path)
            family_path = summary_path.with_suffix(".families.json")
            table = _read(family_path)
            for family in table["families"]:
                statuses.update(family["cohort_status_counts"])
            variants.append(_family_index(summary, table, {
                "file": family_path.name, "sha256": _hash(family_path)}))
            for tier, counts in table["accuracy_summary"].items():
                summaries[tier].update({key: counts[key] for key in (
                    "cohort_count", "passed_cohort_count", "failed_cohort_count",
                    "scored_event_count", "passed_event_count", "failed_event_count")})
            sections.extend(_variant_markdown(summary, table))
    lines = [
        "# Complete-Capture Operator Families And Tiered Conditional Errors", "",
        "Historical captures; report refresh can reuse saved comparisons without raw scans or new predictions.", "",
        "Policy: observed complete-event mean > 50 us uses absolute relative error <= 15%; "
        "mean <= 50 us uses absolute per-call difference <= 15 us, including exactly 50 us. "
        "Per-call diff is predicted minus observed. No launch floor is added to predictions. "
        "This is an acceptance allowance, not evidence that a residual was caused by launch overhead.", "",
        "Acceptance is decided per cohort before aggregation. Family/tier means are call-count weighted; "
        "pass/fail counts preserve failed cohorts even if signed averages cancel. "
        "The scored columns cover the indicated tier and pass/fail subset only: failed cohorts appear "
        "in error tables and passed cohorts appear within tolerance, including when a family has both. "
        "All/reference event counts describe the whole native family and repeat across these subsets. "
        "Every native type and full-family aggregate remains in JSON.", "",
        "Large failed cohorts lead Top Errors, sorted by their observed activity; small failures are "
        "separate and sorted by absolute per-call difference. Within-tolerance groups and unscored "
        "coverage have separate tables. Reference, clipped, prediction-failed and unmatched events "
        "are not scored; accuracy-failed cohorts remain in the scored denominator.", "",
        "Activity sums count overlapping events separately and are not wall-clock latency. "
        "Variant totals reuse captures and must not be counted as independent evidence.", "",
        "| Tier | Compared cohorts across variants | Passed | Failed |",
        "| --- | ---: | ---: | ---: |",
    ]
    for tier, counts in summaries.items():
        lines.append(f"| {tier} | {counts['cohort_count']} | "
                     f"{counts['passed_cohort_count']} | {counts['failed_cohort_count']} |")
    total = Counter()
    for counts in summaries.values():
        total.update(counts)
    lines.append(f"| All scored | {total['cohort_count']} | "
                 f"{total['passed_cohort_count']} | {total['failed_cohort_count']} |")
    if statuses.get("prediction_failed"):
        lines.extend(["", f"**Partial prediction coverage: {statuses['prediction_failed']} "
                      "cohort predictions failed and remain outside accuracy denominators.** "
                      "The full replay receipt retains their failure and retry records."])
    body_lines, body_identity = body_scoreboard(args.output_dir)
    lines.extend([*body_lines, "", *sections])
    suffix = "comparison" if args.compare_existing else "replay"
    unique_events = {row["source_identity"]["sha256"]: row["event_count"] for row in variants}
    overview = {
        "kind": "complete_capture_native_family_tables", "variants": variants,
        "accuracy_policy": accuracy_policy(), "accuracy_summary_across_variants": summaries,
        "distinct_capture_count": len(unique_events),
        "unique_capture_event_count": sum(unique_events.values()),
        "variant_totals_are_not_independent_captures": True,
        "not_new_live_collection": True, "occurrence_binding_implied": False,
        "body_forward_scoreboard": body_identity,
        "status": "partial" if statuses.get("prediction_failed") else "completed",
        "comparison_cohort_status_counts": dict(statuses),
    }
    (args.output_dir / f"fusion-cohort-{suffix}-families.json").write_text(
        json.dumps(overview, separators=(",", ":"), allow_nan=False) + "\n")
    (args.output_dir / f"fusion-cohort-{suffix}-top-errors.md").write_text(
        "\n".join(lines).rstrip() + "\n")


def write_full_replay_summary(output_dir, receipt):
    """Build the global scoreboard from one verified saved replay generation."""
    expected_variants = []
    expected_tiers = {tier: Counter() for tier in TIERS}
    for capture in receipt["captures"]:
        for entry in capture["reports"]:
            path = output_dir / entry["report"]
            if entry.get("summary_identity") != {
                "file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size,
            }:
                raise ValueError(f"summary_generation_mismatch:{path}")
            summary = _read(path)
            identity = summary["artifacts"]["families"]
            family_path = output_dir / identity["file"]
            if identity != {
                "file": family_path.name, "sha256": _hash(family_path),
                "size_bytes": family_path.stat().st_size,
            }:
                raise ValueError(f"artifact_identity_mismatch:{family_path}")
            table = _read(family_path)
            if table["graph_id"] != summary["graph_id"]:
                raise ValueError(f"artifact_graph_mismatch:{family_path}")
            expected_variants.append(_family_index(summary, table, identity))
            for tier, counts in table["accuracy_summary"].items():
                expected_tiers[tier].update({key: counts[key] for key in (
                    "cohort_count", "passed_cohort_count", "failed_cohort_count",
                    "scored_event_count", "passed_event_count", "failed_event_count")})
    overview = _read(output_dir / "fusion-cohort-replay-families.json")
    # Equal cohort counts can describe different captures and pass populations.
    # Verify the complete generation before replacing the previous scoreboard.
    if (overview["variants"] != expected_variants
            or overview["accuracy_summary_across_variants"] != expected_tiers):
        raise ValueError("overview_generation_mismatch")
    tiers = overview["accuracy_summary_across_variants"]
    total = Counter()
    for counts in tiers.values():
        total.update(counts)
    statuses = receipt["comparison_cohort_status_counts"]
    if total["cohort_count"] != statuses.get("compared", 0):
        raise ValueError("full_replay_summary_compared_denominator_mismatch")
    lines = [
        "# Complete Family And Physical-Cohort Replay", "",
        f"This {'completed' if receipt['status'] == 'completed' else 'partial'} historical replay uses **{receipt['distinct_captured_sources']} "
        f"complete A3/A5 captures and {receipt['unique_capture_event_count']:,} "
        f"positive-duration events**, with {receipt['declaration_variant_count']} variants "
        f"and {receipt['raw_parsed_capture_scans']} serial capture scans. "
        "No new NPU workload was launched.", "",
        "Every valid tensor/physical-work cohort enters comparison. There is no operator-type "
        "allowlist. Different declarations reuse the same captures; their counts below are "
        "conditional comparisons, not independent hardware trials.", "",
        f"Prediction status: **{receipt['status']}**; "
        f"{statuses.get('compared', 0)} compared, {statuses.get('reference_only', 0)} reference, "
        f"{statuses.get('prediction_failed', 0)} prediction-failed cohorts. "
        "Prediction failures remain outside the accuracy denominator; recorded timeout attempts "
        "remain in the full replay receipt.", "",
        "## Global Accuracy", "",
        "| Observed complete-event mean | Criterion | Passed / compared cohorts | Failed |",
        "| --- | --- | ---: | ---: |",
    ]
    for tier, label, criterion in (
        ("absolute_15us", "<= 50 us", "Absolute per-call difference <= 15 us"),
        ("relative_15pct", "> 50 us", "Absolute relative error <= 15%"),
    ):
        counts = tiers[tier]
        lines.append(
            f"| {label} | {criterion} | {counts['passed_cohort_count']} / "
            f"{counts['cohort_count']} | {counts['failed_cohort_count']} |")
    lines.extend([
        f"| All scored | Each cohort's own tier | {total['passed_cohort_count']} / "
        f"{total['cohort_count']} | {total['failed_cohort_count']} |", "",
        f"**{statuses.get('reference_only', 0)} reference cohorts remain unscored.** "
        "The absolute tolerance does not change predictions or establish that launch overhead "
        "caused a residual. Family means are call-count weighted; cancellation of signed "
        "errors cannot turn a failed cohort into a pass.", "",
        "## Complete Variant Results", "",
        "| Declaration / variant | Cohort events | Scored events | Reference events | "
        "Passed / compared | Reference cohorts |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ])
    for variant in overview["variants"]:
        table = _read(output_dir / variant["file"])
        counts = Counter()
        for tier in table["accuracy_summary"].values():
            counts.update({key: tier[key] for key in (
                "passed_cohort_count", "cohort_count", "scored_event_count")})
        families = table["families"]
        lines.append(
            f"| {variant['declaration_key']} / {variant['variant']} | "
            f"{sum(row['cohort_event_count'] for row in families):,} | "
            f"{counts['scored_event_count']:,} | "
            f"{sum(row['reference_event_count'] for row in families):,} | "
            f"{counts['passed_cohort_count']} / {counts['cohort_count']} | "
            f"{sum(row['cohort_status_counts'].get('reference_only', 0) for row in families)} |")
    combined = [variant for variant in overview["variants"]
                if variant["variant"] == "source_combined_prefill_conditional"]
    if combined:
        lines.extend([
            "", "## Combined Prefill Recipe Coverage", "",
            "These rows use the same declarations and cohorts as the complete table. "
            "Steady matmul applies to standalone projections; staged prefill owns its internal "
            "QK/PV work. Other body recipes remain selected as declared. "
            "Paged and contiguous tensor interfaces stay separate, including zero-match arms.", "",
            "| Declaration | Native family | All capture events | Scored events | "
            "Passed / compared | Observed us/call | Predicted us/call | Per-call diff us |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ])
        for variant in combined:
            table = _read(output_dir / variant["file"])
            for family in table["families"]:
                if family["operator_type"] not in {
                        "FusedInferAttentionScore", "QuantBatchMatmulV3", "MatMulV3"}:
                    continue
                lines.append(
                    f"| {variant['declaration_key']} | {family['operator_type']} | "
                    f"{family['event_count']} | {family['scored_event_count']} | "
                    f"{family['passed_cohort_count']} / "
                    f"{family['cohort_status_counts'].get('compared', 0)} | "
                    f"{_value(family['observed_per_call_us'])} | "
                    f"{_value(family['predicted_per_call_us'])} | "
                    f"{_value(family['per_call_diff_us'])} |")
    body_lines, _ = body_scoreboard(output_dir)
    lines.extend(body_lines)
    lines.extend([
        "", "## Coverage And Interpretation", "",
        "Paged attention uses independently declared query and cache-block geometry. "
        "Cache capacity does not establish active context, and query width does not identify "
        "verify or draft execution. Recurrent GDN retains exact state dtype. Sparse-attention "
        "buckets use observed index descriptors and independently declared layer structure; "
        "no event is duplicated between heterogeneous buckets within one declaration. "
        "Across declarations the same captured events can be reused; summed scored-event counts "
        "are not a unique-event coverage rate.", "",
        "Source-selected shared INT32 quantization separates the accumulator producer from "
        "its dequantization/activation consumer. Compressor normalization references retain "
        "their missing native state-write/reuse boundary and stay outside accuracy counts. "
        "Kimi single-bank wrappers require their explicit source caller and execution domain. "
        "Missing routing/scalar/dispatch evidence remains visible in the unscored reasons.", "",
        "Exported physical-work signatures describe semantic operator contracts. "
        "Predictions execute the selected recipe, whose staged transfer traffic can differ "
        "from that semantic work. Source selection is conditional and does not prove which "
        "binary dispatched the captured kernel.", "",
        "All occurrence-level layer/replica/step identities remain unbound. "
        "Activity sums count overlapping events separately and are not model latency. "
        "Per-operator passes do not establish complete model coverage or end-to-end accuracy.", "",
        "## Reproducibility", "",
        f"Full replay: {receipt['elapsed_seconds']:.3f} seconds. Peak mapping "
        f"{receipt['peak_worker_rss_bytes'] / 1024**2:.2f} MiB; peak comparison "
        f"{receipt['peak_comparison_rss_bytes'] / 1024**2:.2f} MiB. "
        f"Runtime sources unchanged: {receipt['runtime_sources_unchanged']}. "
        f"Capture failures: {len(receipt['failures'])}; comparison failures: "
        f"{len(receipt['comparison_failures'])}.", "",
        "The [full replay receipt](fusion-cohort-validation.json) records capture SHA256, "
        "runtime source hashes, case declarations and program budgets. "
        "The [Top Errors](fusion-cohort-replay-top-errors.md), "
        "[large-call report](fusion-cohort-large-call-errors.md), and "
        "[complete family JSON index](fusion-cohort-replay-families.json) share this replay. "
        "See [maintained-suite verification](cohort-verification.json) and "
        "[independent review](fusion-cohort-independent-review.json) for their recorded runs.", "",
    ])
    (output_dir / "cohort-full-family-replay.md").write_text("\n".join(lines))
