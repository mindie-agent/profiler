"""Explain failed large-call cohorts using verified, saved replay evidence.

[Role] Preserve descriptors and measurement/prediction boundaries for triage.
[Invariants] Only completed full replays are accepted. All referenced artifacts
  are hash-checked. Cohort/variant totals are not unique capture or model latency.
  Missing model coverage stays unknown; no occurrence or dispatch is inferred.
[Timeouts & Locks] Finite metadata files, each at most 32 MiB; no subprocesses.
[Side-Effect Policy] Writes two derived reports; no raw scans or sim execution.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path


def _hash(path):
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _identity(path):
    return {"file": path.name, "sha256": _hash(path),
            "size_bytes": path.stat().st_size}


def _read(path):
    if path.stat().st_size > 32 * 1024**2:
        raise ValueError(f"metadata_exceeds_32_mib:{path}")
    return json.loads(path.read_text())


def _coverage(comparison):
    if comparison.get("model_coverage") is not None:
        return {"status": "projected", "source": "saved_comparison.model_coverage",
                "value": comparison["model_coverage"]}
    return {
        "status": "not_projected", "source": "saved_comparison",
        "reason": "model_coverage_not_present_in_saved_comparison",
        "additional_sim_calls": 0, "completeness_implied": False,
    }


def _record(summary, window, row):
    observed, prediction = row["observed"], row["prediction"]
    mean = observed["duration_ns"]["mean"] / 1000
    predicted = prediction["per_call_ms"] * 1000
    difference = predicted - mean
    actual_total = observed["activity_sum_ns"] / 1e6
    predicted_total = prediction["observed_call_count_total_ms"]
    if (mean <= 50 or observed["clipped_event_count"]
            or observed["complete_event_count"] != observed["event_count"]):
        raise ValueError(f"invalid_large_call_scored_boundary:{row['cohort_id']}")
    for field, value in (("observed_per_call_us", mean),
                         ("predicted_per_call_us", predicted),
                         ("per_call_diff_us", difference),
                         ("abs_error_per_call_us", abs(difference))):
        if not math.isclose(row[field], value, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"cohort_accuracy_value_mismatch:{row['cohort_id']}:{field}")
    residual = row["comparison"]["activity_sum"]["signed_residual_ms"]
    if not math.isclose(residual, predicted_total - actual_total, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"cohort_activity_residual_mismatch:{row['cohort_id']}")
    return {
        "capture_key": summary["capture_key"], "declaration_key": summary["declaration_key"],
        "variant": summary["variant"], "graph_id": summary["graph_id"],
        "source_identity": summary["source_identity"],
        "cohort_id": row["cohort_id"], "native_operator_type": row["native_operator_type"],
        "contract": row["contract"], "contract_scope": row["contract_scope"],
        "physical_signature": row["physical_signature"],
        "physical_work_per_instance": prediction["physical_work_per_instance"],
        "structural_classification": row.get("structural_classification"),
        "observed": observed,
        "observed_duration_us": {
            key: None if observed["duration_ns"].get(key) is None
            else observed["duration_ns"][key] / 1000
            for key in ("mean", "p50", "min", "max")},
        "observed_per_call_us": mean, "predicted_per_call_us": predicted,
        "per_call_diff_us": difference, "abs_error_per_call_us": abs(difference),
        "relative_error": difference / mean,
        "observed_activity_ms": actual_total, "predicted_activity_ms": predicted_total,
        "signed_cumulative_gap_ms": predicted_total - actual_total,
        "absolute_cumulative_gap_ms": abs(predicted_total - actual_total),
        "accuracy_tier": row["accuracy_tier"], "accuracy_pass": row["accuracy_pass"],
        "accuracy_tolerance": row["accuracy_tolerance"], "accuracy_policy": row["accuracy_policy"],
        "captured_event_boundary": {
            "kind": "one_native_profiler_event_per_observed_call",
            "native_operator_type": row["native_operator_type"],
            "duration_basis": observed["duration_ns"].get("basis"),
            "descriptor_basis": "saved_matched_contract; raw_full_tensor_ABI_not_reloaded",
            "capture_dispatch_identity_verified": summary["declaration_source"].get(
                "capture_dispatch_identity_verified"),
        },
        "declared_prediction_boundary": prediction["boundary"],
        "single_device_program": prediction["single_device_program"],
        "prediction": prediction, "comparison": row["comparison"],
        "target_kind": row["target_kind"], "target_count": row.get("target_count"),
        "representative_target_id": prediction.get("representative_target_id"),
        "representative_operator_ids": prediction.get("representative_operator_ids"),
        "target_examples": row.get("target_examples"),
        "declared_instance_count": row["declared_instance_count"],
        "declared_candidate_instance_count": row.get("declared_candidate_instance_count"),
        "declared_layer_count": row["declared_layer_count"], "multiplicity": row["multiplicity"],
        "placement": row.get("placement"),
        "occurrence_binding_implied": row["occurrence_binding_implied"],
        "rank_id": row["rank_id"], "device_id": row.get("device_id"),
        "replica": row.get("replica"), "stage": row.get("stage"), "phase": row["phase"],
        "window": {key: window.get(key) for key in ("rank_id", "step", "window", "source_identity")},
    }


def _descriptor(contract):
    # Positional labels preserve the contract's actual axes without naming them.
    text = json.dumps(contract, separators=(",", ":"), ensure_ascii=True)
    return text if len(text) <= 320 else text[:290] + "... [full contract in JSON]"


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ").replace("`", "'")


def _markdown(report):
    totals = report["totals_across_variants"]
    lines = [
        "# Large-Call Failed Cohorts", "",
        f"Selection: status=compared, accuracy_tier=relative_15pct, accuracy_pass=false. "
        f"Observed complete-event mean > 50 us; absolute relative error > 15%.",
        f"Sort: `{report['sort_basis']}`. JSON retains all {len(report['cohorts'])} failed "
        "cohorts; this table shows the first 30.", "",
        f"Receipt SHA256: `{report['validation']['sha256']}`.",
        f"Script SHA256: `{report['script']['sha256']}`.", "",
        "Each observed call is one captured native profiler event. The prediction boundary is "
        "reported separately. Contract positions and stored tensor shapes/dtypes are shown verbatim; "
        "excluded fields remain subject to contract_scope in JSON.",
        "Variant totals reuse captures. Activity sums can overlap and are not full-model latency. "
        "A homogeneous cohort does not identify a layer, invocation, or DP replica.", "",
        "| Tier | Passed / compared cohorts | Failed |",
        "| --- | ---: | ---: |",
    ]
    for tier, counts in report["accuracy_summary_across_variants"].items():
        lines.append(
            f"| {tier} | {counts['passed_cohort_count']} / {counts['cohort_count']} | "
            f"{counts['failed_cohort_count']} |")
    total = Counter()
    for counts in report["accuracy_summary_across_variants"].values():
        total.update(counts)
    lines.extend([
        f"| All scored | {total['passed_cohort_count']} / {total['cohort_count']} | "
        f"{total['failed_cohort_count']} |", "",
        "| # | Declaration / variant | Native / cohort suffix | Calls | Observed mean / p50 us | "
        "Predicted us | Signed / abs diff us | Relative | Signed / abs total gap ms | "
        "Prediction boundary / single program | Saved tensor contract |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ])
    for index, row in enumerate(report["cohorts"][:30], 1):
        p50 = row["observed_duration_us"]["p50"]
        p50_text = "unknown" if p50 is None else f"{p50:.3f}"
        lines.append(
            f"| {index} | {_cell(row['declaration_key'])} / {_cell(row['variant'])} | "
            f"{_cell(row['native_operator_type'])} / {row['cohort_id'][-12:]} | "
            f"{row['observed']['event_count']} | {row['observed_per_call_us']:.3f} / {p50_text} | "
            f"{row['predicted_per_call_us']:.3f} | {row['per_call_diff_us']:+.3f} / "
            f"{row['abs_error_per_call_us']:.3f} | {row['relative_error']:+.2%} | "
            f"{row['signed_cumulative_gap_ms']:+.3f} / {row['absolute_cumulative_gap_ms']:.3f} | "
            f"{_cell(row['declared_prediction_boundary'])} / {row['single_device_program']} | "
            f"`{_cell(_descriptor(row['contract']))}` |")
    lines.extend([
        "", "## Reference Costs Excluded From Accuracy", "",
        f"{totals['reference_cohort_count']} reference cohorts / "
        f"{totals['reference_event_count']} observed calls. These are not passing comparisons.", "",
        "| Reason | Cohorts | Calls | Observed activity ms | Predicted reference ms |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for reason, counts in sorted(report["reference_by_reason"].items()):
        lines.append(
            f"| {_cell(reason)} | {counts['cohort_count']} | {counts['event_count']} | "
            f"{counts['observed_activity_ms']:.3f} | {counts['predicted_reference_activity_ms']:.3f} |")
    lines.extend([
        "", "## Case Evidence And Model Coverage", "",
        "Model coverage is copied only when present in the saved comparison. `not_projected` "
        "does not mean complete; this report makes no additional sim calls.", "",
        "| Declaration / variant | Capture | Recorded raw source SHA256 | Model coverage |",
        "| --- | --- | --- | --- |",
    ])
    for case in report["cases"]:
        lines.append(
            f"| {_cell(case['declaration_key'])} / {_cell(case['variant'])} | "
            f"{_cell(case['capture_key'])} | `{case['source_identity']['sha256']}` | "
            f"{case['model_coverage']['status']} |")
    return "\n".join(lines) + "\n"


def build_report(output_dir, sort_by):
    receipt_path = output_dir / "fusion-cohort-validation.json"
    receipt_identity, receipt = _identity(receipt_path), _read(receipt_path)
    if (receipt["status"] != "completed" or receipt.get("comparison_only")
            or not receipt["runtime_sources_unchanged"] or not receipt["memory_budget_passed"]
            or receipt["failures"] or receipt["comparison_failures"]):
        raise ValueError("large_call_report_requires_successful_full_replay")
    cases, rows, inputs, seen = [], [], [], set()
    statuses, references = Counter(), {}
    accuracy = {tier: Counter() for tier in ("relative_15pct", "absolute_15us")}
    for capture in receipt["captures"]:
        for entry in capture["reports"]:
            summary_path = output_dir / entry["report"]
            if summary_path.name in seen:
                raise ValueError(f"duplicate_replay_summary:{summary_path.name}")
            seen.add(summary_path.name)
            summary_identity, summary = _identity(summary_path), _read(summary_path)
            if summary_identity != entry.get("summary_identity"):
                raise ValueError(f"summary_generation_mismatch:{summary_path}")
            if (summary["capture_key"] != capture["capture_key"]
                    or summary["source_identity"] != capture["source_identity"]
                    or summary["comparison"]["status"] != "completed"):
                raise ValueError(f"summary_receipt_mismatch:{summary_path}")
            for artifact in summary["artifacts"].values():
                if _identity(output_dir / artifact["file"]) != artifact:
                    raise ValueError(f"artifact_identity_mismatch:{artifact['file']}")
            comparison = _read(output_dir / summary["artifacts"]["comparison"]["file"])
            if comparison["graph_id"] != summary["graph_id"]:
                raise ValueError(f"comparison_graph_mismatch:{summary_path}")
            cases.append({
                key: summary[key] for key in (
                    "capture_key", "declaration_key", "variant", "graph_id", "source_identity",
                    "declaration_source", "declared_execution")})
            cases[-1]["model_coverage"] = _coverage(comparison)
            inputs.append({"summary": summary_identity, "artifacts": summary["artifacts"]})
            for window in comparison["windows"]:
                for row in window["cohorts"]:
                    statuses[row["status"]] += 1
                    if row["status"] == "compared":
                        counts = accuracy[row["accuracy_tier"]]
                        counts["cohort_count"] += 1
                        counts["passed_cohort_count"] += int(row["accuracy_pass"])
                        counts["failed_cohort_count"] += int(not row["accuracy_pass"])
                    if row["status"] == "reference_only":
                        counts = references.setdefault(row["reason"], {
                            "cohort_count": 0, "event_count": 0,
                            "observed_activity_ms": 0, "predicted_reference_activity_ms": 0})
                        counts["cohort_count"] += 1
                        counts["event_count"] += row["observed"]["event_count"]
                        counts["observed_activity_ms"] += row["observed"]["activity_sum_ns"] / 1e6
                        counts["predicted_reference_activity_ms"] += row["prediction"][
                            "observed_call_count_total_ms"]
                    elif (row["status"] == "compared" and row["accuracy_tier"] == "relative_15pct"
                          and row["accuracy_pass"] is False):
                        rows.append(_record(summary, window, row))
    if len(cases) != receipt["declaration_variant_count"]:
        raise ValueError("replay_variant_count_mismatch")
    # Recheck metadata identities before writing so an in-progress replay cannot
    # produce a report assembled from different artifact generations.
    for record in inputs:
        if _identity(output_dir / record["summary"]["file"]) != record["summary"]:
            raise ValueError("summary_changed_during_report")
        for artifact in record["artifacts"].values():
            if _identity(output_dir / artifact["file"]) != artifact:
                raise ValueError("artifact_changed_during_report")
    if _identity(receipt_path) != receipt_identity:
        raise ValueError("validation_changed_during_report")
    sort_field = {"observed_activity": "observed_activity_ms",
                  "absolute_cumulative_gap": "absolute_cumulative_gap_ms"}[sort_by]
    rows.sort(key=lambda row: (-row[sort_field], row["declaration_key"],
                              row["variant"], row["cohort_id"]))
    return {
        "schema_version": "mindie-large-cohort-errors/1", "status": "completed",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selection": {"status": "compared", "accuracy_tier": "relative_15pct",
                      "accuracy_pass": False, "observed_mean_us_gt": 50},
        "sort_basis": sort_field + "_descending; declaration_variant_cohort_id_tiebreak",
        "validation": receipt_identity, "script": _identity(Path(__file__).resolve()),
        "runtime_source_identity": receipt["runtime_source_identity"], "inputs": inputs,
        "raw_capture_reads": 0, "prediction_executions": 0, "structure_exports": 0,
        "capture_identity_basis": "verified_replay_recorded_SHA256; raw_capture_not_reopened",
        "unique_capture_event_count": receipt["unique_capture_event_count"],
        "distinct_captured_sources": receipt["distinct_captured_sources"],
        "variant_totals_are_not_independent_captures": True,
        "accuracy_summary_across_variants": accuracy,
        "totals_across_variants": {
            "variant_count": len(cases), "cohort_status_counts": dict(statuses),
            "failed_large_cohort_count": len(rows),
            "failed_large_event_count": sum(row["observed"]["event_count"] for row in rows),
            "reference_cohort_count": sum(row["cohort_count"] for row in references.values()),
            "reference_event_count": sum(row["event_count"] for row in references.values())},
        "reference_by_reason": references, "cases": cases, "cohorts": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path,
                        default=Path(__file__).resolve().parent / "acceptance-20261029")
    parser.add_argument("--sort-by", choices=("observed_activity", "absolute_cumulative_gap"),
                        default="observed_activity")
    args = parser.parse_args()
    report = build_report(args.output_dir, args.sort_by)
    prefix = args.output_dir / "fusion-cohort-large-call-errors"
    prefix.with_suffix(".json").write_text(json.dumps(
        report, ensure_ascii=True, separators=(",", ":"), allow_nan=False) + "\n")
    prefix.with_suffix(".md").write_text(_markdown(report))
    print(json.dumps(report["totals_across_variants"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
