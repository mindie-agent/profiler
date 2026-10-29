"""Independently check source populations and numerical Decode predictions.

[Role] Reconcile saved Body/layer comparisons against original extraction rows.
[Invariants] Recompute arithmetic without importing the production comparator;
  deferred populations stay measured and do not count as scored predictions.
[Timeouts & Locks] One <=50 MiB JSON at a time; no subprocess, device or locks.
[Side-Effect Policy] Reads retained local receipts; writes a numerical review.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import mean, median


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError(f"metadata exceeds 50 MiB: {path}")
    raw = path.read_bytes()
    return json.loads(raw), sha256(raw).hexdigest()


def review(path, output):
    report, report_hash = read(path)
    checks, failures = 0, []
    extraction_path, extraction = None, None

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    def equal(left, right, label):
        check(math.isclose(left, right, rel_tol=1e-11, abs_tol=1e-11), label)

    passed = compared = 0
    failed_attempts = []
    populations = {}
    for case in report["cases"]:
        label = case["case_id"]
        if case["comparison"]["status"] == "failed":
            check(case.get("observed") is None and case.get("prediction") is None,
                  label + ":failed_read_not_measured_or_predicted")
            check(case["comparison"]["observed_ms"]["count"] == 0, label + ":failed_read_no_calls")
            check(bool(case.get("error")) and bool(case["comparison"]["reasons"]), label + ":failure_visible")
            failed_attempts.append({"case_id": label, "error": case["error"]})
            continue
        identity = case["extraction_identity"]
        if extraction_path != identity["path"]:
            extraction, digest = read(identity["path"])
            extraction_path = identity["path"]
        check(digest == identity["sha256"], label + ":extraction_identity")
        geometry = case["geometry"]
        key = tuple(geometry[field] for field in ("tokens_per_sequence", "sequences_per_replica", "query_rows"))
        group = next(group for group in extraction["geometry_groups"] if tuple(
            group["geometry"][field] for field in ("tokens_per_sequence", "sequences_per_replica", "query_rows")) == key)
        values = [row["body_forward_span_ms"] for row in extraction["forwards"] if row["forward_id"] in group["forward_ids"]]
        comp = case["comparison"]
        check(comp["observed_ms"] == group["body_forward_span_ms"], label + ":population_stats")
        equal(comp["observed_ms"]["mean"], mean(values), label + ":body_mean")
        equal(comp["observed_ms"]["p50"], median(values), label + ":body_p50")
        populations[(case["source_identity"]["sha256"], key)] = len(values)
        if comp["status"] != "compared":
            check(comp["predicted_ms"] is None, label + ":deferred_is_not_prediction")
            continue
        compared += 1
        predicted = case["prediction"]["body_forward_span_ms"]
        equal(predicted, comp["predicted_ms"], label + ":prediction")
        difference = predicted - mean(values)
        equal(difference, comp["per_forward_diff_ms"], label + ":body_difference")
        equal(difference / mean(values), comp["relative_error"], label + ":relative_error")
        good = abs(difference / mean(values)) <= .15
        check(comp["passed"] is good, label + ":body_pass")
        passed += good
        measured_layers = {row["layer_id"]: row for row in group["per_layer_ms"]}
        for layer in case["per_layer_comparison"]["layers"]:
            check(layer["observed_ms"] == measured_layers[layer["layer_id"]]["stats"], label + ":layer_population")
            declared = next(row for row in case["prediction"]["per_layer_ms"] if row["layer_id"] == layer["layer_id"]
                            and row["replica"] == layer["representative_replica"])
            equal(declared["end_ms"] - declared["start_ms"], layer["predicted_ms"], label + ":layer_endpoint")
            error = layer["predicted_ms"] / layer["observed_ms"]["mean"] - 1
            equal(error, layer["relative_error"], label + ":layer_error")
            check(layer["passed"] is (abs(error) <= .15), label + ":layer_pass")
    check(compared == report["summary"]["compared_cases"], "compared_total")
    check(passed == report["summary"]["passed_cases"], "passed_total")
    check(len(failed_attempts) == report["summary"]["failed_cases"], "failed_attempt_total")
    check(report["runtime_generation"]["unchanged"], "runtime_generation")
    result = {"schema_version": "mindie-decode-prediction-review/1", "status": "failed" if failures else "passed",
              "report_sha256": report_hash, "checks": checks, "failures": failures,
              "compared": compared, "passed": passed, "unique_source_geometry_populations": len(populations),
              "input_execution_status": report["status"], "failed_attempts": failed_attempts,
              "unique_forwards": sum(populations.values()),
              "scope": "Independent saved-source population, endpoint, error and unrounded 15% arithmetic; no raw scan or prediction."}
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return bool(failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(review(args.report, args.output))
