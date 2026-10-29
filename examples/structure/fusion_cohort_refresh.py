"""Refresh accuracy annotations on verified saved fusion-cohort comparisons.

[Role] Reuse the completed replay without scanning captures or running prediction.
[Invariants] Artifact hashes are checked first; observed/predicted values, graph
  IDs, counts and original residuals remain byte-equivalent under canonical JSON.
  Original full-replay receipts remain historical evidence with their own hashes.
[Timeouts & Locks] Bounded metadata inputs and a finite report set; no locks.
[Side-Effect Policy] Updates comparison annotations, family reports and summaries.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import time

from mindie_sim.cohort_accuracy import accuracy_fields, accuracy_policy

from fusion_cohort_reporting import family_table, write_family_overview
from fusion_replay_cases import _hash, _read


def _write(path, value):
    Path(path).write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")


def _identity(path):
    return {"file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size}


def _metrics_identity(comparison):
    original = {key: value for key, value in comparison.items()
                if key not in {"accuracy_policy", "accuracy_evaluation", "windows"}}
    original["windows"] = [
        {**window, "cohorts": [
            {key: value for key, value in row.items() if key not in accuracy_fields(row)}
            for row in window["cohorts"]]}
        for window in comparison["windows"]]
    return sha256(json.dumps(original, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def refresh_accuracy(args, *, runtime_identity, rss):
    started = time.perf_counter()
    receipt_path = args.output_dir / "fusion-cohort-validation.json"
    historical = _read(receipt_path)
    if historical["status"] != "completed":
        raise ValueError("accuracy_refresh_requires_completed_replay")
    inputs, seen = [], set()
    # Check the entire input set before replacing any derived report.
    for capture in historical["captures"]:
        for entry in capture["reports"]:
            path = args.output_dir / entry["report"]
            if path.name in seen:
                raise ValueError(f"duplicate_replay_report:{path.name}")
            seen.add(path.name)
            summary = _read(path)
            for record in summary["artifacts"].values():
                artifact = args.output_dir / record["file"]
                if _identity(artifact) != record:
                    raise ValueError(f"replay_artifact_identity_mismatch:{artifact}")
            inputs.append({
                "summary": _identity(path),
                "artifacts": summary["artifacts"],
            })
    before = runtime_identity()
    records, statuses = [], Counter()
    tier_counts = {tier: Counter() for tier in ("relative_15pct", "absolute_15us")}
    for record in inputs:
        path = args.output_dir / record["summary"]["file"]
        summary = _read(path)
        comparison_path = args.output_dir / summary["artifacts"]["comparison"]["file"]
        comparison = _read(comparison_path)
        unchanged = _metrics_identity(comparison)
        comparison["accuracy_policy"] = accuracy_policy()
        comparison["accuracy_evaluation"] = {
            "method": "saved_comparison_projection",
            "raw_capture_reads": 0, "prediction_executions": 0,
            "prediction_adjustment": "none",
        }
        for window in comparison["windows"]:
            for row in window["cohorts"]:
                row.update(accuracy_fields(row))
                statuses[row["status"]] += 1
        if _metrics_identity(comparison) != unchanged:
            raise ValueError(f"accuracy_refresh_changed_original_metrics:{path}")
        mapping = _read(args.output_dir / summary["artifacts"]["mapping"]["file"])
        table = family_table(mapping, comparison)
        family_path = args.output_dir / summary["artifacts"]["families"]["file"]
        for tier, counts in table["accuracy_summary"].items():
            tier_counts[tier].update({key: counts[key] for key in (
                "cohort_count", "passed_cohort_count", "failed_cohort_count",
                "scored_event_count", "passed_event_count", "failed_event_count")})
        _write(comparison_path, comparison)
        _write(family_path, table)
        summary["accuracy_evaluation"] = {
            **comparison["accuracy_evaluation"], "accuracy_policy": accuracy_policy(),
            "accuracy_summary": table["accuracy_summary"],
            "original_comparison_metrics_sha256": unchanged,
        }
        summary["artifacts"].update(
            comparison=_identity(comparison_path), families=_identity(family_path))
        _write(path, summary)
        records.append({
            "input": record, "output_summary": _identity(path),
            "output_artifacts": summary["artifacts"],
            "original_comparison_metrics_sha256": unchanged,
            "original_metrics_unchanged": True,
        })
    write_family_overview(args, historical["captures"])
    after, peak = runtime_identity(), rss()
    result = {
        "kind": "saved_fusion_cohort_accuracy_refresh",
        "status": "completed" if before == after and peak <= 512 * 1024**2 else "failed",
        "historical_full_replay": _identity(receipt_path),
        "not_new_live_collection": True, "raw_capture_reads": 0, "prediction_executions": 0,
        "variant_count": len(records), "accuracy_policy": accuracy_policy(),
        "comparison_cohort_status_counts": statuses,
        "accuracy_summary_across_variants": tier_counts,
        "original_metrics_unchanged": True, "reports": records,
        "runtime_source_identity": before, "runtime_sources_unchanged_during_refresh": before == after,
        "maximum_resident_set_size_bytes": peak, "memory_budget_passed": peak <= 512 * 1024**2,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "overview": _identity(args.output_dir / "fusion-cohort-replay-families.json"),
        "top_errors": _identity(args.output_dir / "fusion-cohort-replay-top-errors.md"),
    }
    _write(args.output_dir / "fusion-cohort-accuracy-validation.json", result)
    print(json.dumps({key: result[key] for key in (
        "status", "variant_count", "accuracy_summary_across_variants",
        "original_metrics_unchanged", "maximum_resident_set_size_bytes", "elapsed_seconds")}),
        flush=True)
    if result["status"] != "completed":
        raise SystemExit(1)
