"""Independently recompute saved Decode statistics without rereading raw captures.

[Role] Audit extraction identities, complete topology and timing/population math.
[Invariants] Historical cores are checked against their saved per-case identities,
  not silently relabelled as the currently installed core. Streams are nonadditive.
[Timeouts & Locks] Reports <=50 MiB, one at a time; no subprocesses or locks.
[Side-Effect Policy] Reads local reports and writes one independent review JSON.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics

from build_decode_forward_cases import _hash


def read(path):
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError(f"report exceeds bounded metadata size: {path}")
    return json.loads(path.read_text())


def review(receipt_path, output):
    receipt = read(receipt_path)
    checks, failures, reports = 0, [], []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def same_stats(actual, values, label):
        ordered = sorted(values)
        expected = {"count": len(ordered), "mean": statistics.mean(ordered) if ordered else None,
                    "p50": statistics.median(ordered) if ordered else None,
                    "p90": ordered[math.ceil(len(ordered)*.9)-1] if ordered else None,
                    "min": min(ordered, default=None), "max": max(ordered, default=None)}
        for key, value in expected.items():
            check(actual[key] == value if value is None else
                  math.isclose(actual[key], value, rel_tol=1e-12, abs_tol=1e-12), label+":"+key)

    forwards = events = 0
    for evidence in receipt["cases"]:
        path = Path(evidence["report_path"])
        check(_hash(path) == evidence["report_sha256"], evidence["case_id"]+":artifact_hash")
        data = read(path)
        label, rows = data["case_id"], data["forwards"]
        runtime = evidence.get("extraction_runtime", receipt.get("segmentation_runtime"))
        check(data["extraction_runtime"] == runtime, label+":original_core_identity")
        counts = data["scan_counts"]
        forwards += len(rows)
        events += counts["positive_events"]
        check(counts["positive_events"] == sum(counts.get(key, 0) for key in (
            "complete_body_segment_events", "auxiliary_candidate_segment_events",
            "rejected_segment_events", "trailing_segment_events")), label+":positive_partition")
        for metric in ("body_forward_span_ms", "body_activity_ms", "body_internal_gap_ms"):
            same_stats(data[metric], [row[metric] for row in rows], label+":"+metric)
        by_id, last = {row["forward_id"]: row for row in rows}, {}
        for row in rows:
            check(row["confidence"]["matched_layers"] == row["confidence"]["declared_layers"], label+":full_topology")
            check((row["end_ns"]-row["start_ns"])/1e6 == row["body_forward_span_ms"], label+":integer_span")
            if row["confidence"].get("closure_basis") == "mhc_final_norm":
                check(data["segmentation_options"].get("forward_closure") == "mhc_final_norm",
                      label+":source_declared_terminal_norm_closure")
                check(row["head_start_ns"] is None and row["head_end_ns"] is None,
                      label+":no_fabricated_head_boundary")
                if row["stages"]:
                    final_norm = [stage for stage in row["stages"] if stage["kind"] == "final_norm"]
                    check(len(final_norm) == 1 and row["end_ns"] <= final_norm[0]["start_ns"],
                          label+":terminal_norm_outside_body")
                    check(all(row["end_ns"] <= stage["start_ns"] for stage in row["stages"]
                              if stage["kind"] == "output_head_preparation"),
                          label+":head_preparation_outside_body")
            else:
                check(row["head_start_ns"] is not None and row["end_ns"] <= row["head_start_ns"],
                      label+":head_excluded")
            check(math.isclose(row["body_activity_ms"]+row["body_internal_gap_ms"], row["body_forward_span_ms"], abs_tol=1e-12), label+":activity_gap_partition")
            check(0 <= row["body_activity_ms"] <= row["body_forward_span_ms"] and row["body_internal_gap_ms"] >= 0, label+":nonnegative")
            key = row["rank_id"], row["device_id"]
            check(row["start_ns"] >= last.get(key, row["start_ns"]), label+":nonoverlap")
            last[key] = row["end_ns"]
            for stage in row["stages"]:
                check((stage["end_ns"]-stage["start_ns"])/1e6 == stage["span_ms"], label+":stage_span")
                check(math.isclose(stage["device_activity_union_ms"]+stage["internal_uncovered_gap_ms"], stage["span_ms"], abs_tol=1e-12), label+":stage_partition")
        grouped = []
        for group in data["geometry_groups"]:
            selected = [by_id[key] for key in group["forward_ids"]]
            grouped += group["forward_ids"]
            check(all(row["geometry"] == group["geometry"] for row in selected), label+":geometry_membership")
            for metric in ("body_forward_span_ms", "body_activity_ms", "body_internal_gap_ms"):
                same_stats(group[metric], [row[metric] for row in selected], label+":geometry_"+metric)
            for stream in group["per_stream_activity_ms"]:
                same_stats(stream["stats"], [entry["activity_union_ms"] for row in selected for entry in row["per_stream_activity_ms"] if entry["stream_id"] == stream["stream_id"]], label+":stream")
                check(stream["additive_across_streams"] is False, label+":streams_not_added")
            for layer in group["per_layer_ms"]:
                check(layer["stats"]["count"] == len(selected), label+":layer_geometry_population")
        check(sorted(grouped) == sorted(by_id), label+":geometry_partition")
        same_stats(data["auxiliary_forward_span_ms"], [row["span_ms"] for row in data["auxiliary_occurrences"]], label+":auxiliary")
        for layer in data["per_layer_ms"]:
            for key in ("stats", "activity_ms_stats", "internal_gap_ms_stats"):
                check(layer[key]["count"] == len(rows), label+":layer_full_population")
            check(len(layer["samples"]) <= 3, label+":bounded_samples")
            check(math.isclose(layer["activity_ms_stats"]["mean"]+layer["internal_gap_ms_stats"]["mean"], layer["stats"]["mean"], abs_tol=1e-12), label+":layer_mean_partition")
        reports.append({"case_id": label, "sha256": _hash(path), "forwards": len(rows), "positive_events": counts["positive_events"]})
    check(len(reports) == receipt["case_count"], "receipt:case_count")
    check(forwards == receipt["total_complete_forwards"], "receipt:forward_count")
    check(events == receipt["source_positive_events"], "receipt:event_count")
    result = {"schema_version": "mindie-decode-independent-review/1", "status": "passed" if not failures else "failed",
              "checks": checks, "failures": failures, "cases": len(reports), "forwards": forwards,
              "positive_events": events, "receipt_sha256": _hash(receipt_path), "reports": reports,
              "scope": "Independent saved arithmetic, complete population and per-geometry activity/stream statistics; no raw scan or prediction"}
    output.write_text(json.dumps(result, indent=2)+"\n")
    return {key: value for key, value in result.items() if key != "reports"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = review(args.receipt, args.output)
    print(json.dumps(result))
    if result["failures"]:
        raise SystemExit(1)
