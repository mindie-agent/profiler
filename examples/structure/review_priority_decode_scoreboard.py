"""Independently reconcile the priority scoreboard against its input receipts.

[Role] Verify reported populations, current selections and numerical accuracy.
[Invariants] Invalid input bindings retain observations but never earn a pass;
  conditional source references never enter strict operator accuracy counts.
[Timeouts & Locks] Sequential bounded receipt reads; no locks or subprocesses.
[Side-Effect Policy] Writes only one review JSON; never predicts or parses captures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gc
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time

import ijson


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(part)
    return value.hexdigest()


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024 ** 2:
        raise ValueError(f"Receipt exceeds bounded JSON read limit: {path}")
    with path.open() as stream:
        return json.load(stream)



def receipt_metadata(path):
    """Read only needed top-level fields; never materialize the cases array."""
    wanted = {"runtime_source_identity", "runtime_sources_unchanged",
              "invalidated_body_receipts", "reason", "status"}
    result, active, builder = {}, None, None
    with Path(path).open("rb") as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if active is not None:
                builder.event(event, value)
                if prefix == active and event in {"end_map", "end_array"}:
                    result[active], active, builder = builder.value, None, None
            elif prefix in wanted:
                if event in {"start_map", "start_array"}:
                    active, builder = prefix, ijson.ObjectBuilder()
                    builder.event(event, value)
                elif event in {"string", "number", "boolean", "null"}:
                    result[prefix] = value
    return result


def receipt_cases(path):
    with Path(path).open("rb") as stream:
        yield from ijson.items(stream, "cases.item", use_float=True)


def population(row):
    source, geometry = row.get("source_identity") or {}, row.get("geometry") or {}
    return (source.get("sha256"), geometry.get("query_rows"),
            geometry.get("tokens_per_sequence"), geometry.get("sequences_per_replica"))


def runtime(receipt):
    files = {p.split("/mindie_sim/", 1)[1]: sha
             for p, sha in receipt.get("runtime_source_identity", {}).items()
             if "/mindie_sim/" in p}
    return {"recorded_sim_file_map_sha256": hashlib.sha256(
                json.dumps(files, sort_keys=True).encode()).hexdigest() if files else None,
            "recorded_sim_file_count": len(files),
            "sources_unchanged": receipt.get("runtime_sources_unchanged"),
            "basis": "recorded_relative_sim_file_hash_map; full_receipt_retains_source_paths"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def review(path):
    started = time.monotonic()
    initial_sha = digest(path)
    report = read(path)
    checks, failures = 0, []

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)

    def near(a, b):
        return math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-10)

    def index(rows, fields):
        result = {}
        for row in rows:
            key = (row["receipt"]["path"], *(row.get(field) for field in fields))
            check(key not in result, f"Duplicate scoreboard row: {key}")
            result[key] = row
        return result

    body = index(report["body_comparisons"], ["case_id"])
    family = index(report["operator_families"],
                   ["case_id", "native_operator_type", "declared_role"])
    cohort = index(report["operator_cohorts"],
                   ["case_id", "native_operator_type", "declared_role", "cohort_id"])
    reference = Counter(canonical(row) for row in report["source_role_references"])
    seen_body, seen_family, seen_cohort = set(), set(), set()
    current_body, current_operator, populations = {}, {}, {}
    invalidations = {}
    body_order, operator_order = [], []
    corrected_quant_cases = 0
    expected_references = Counter()

    def check_reference(receipt_path, case, group, expected_runtime, embedded):
        if embedded:
            expected = {"native_operator_type": group["native_operator_type"],
                "attention_kind": group["attention_kind"], "block": group.get("block"),
                "declared_roles": [group["declared_role"]], "layer_ids": group["layer_ids"],
                "status": group["prediction_status"], "evidence_strength": group["evidence_strength"],
                "observed_us": group["observed_us"], "predicted_us": None,
                "predicted_reference_us": group.get("predicted_reference_us"),
                "model_program_already_costed": True, "additional_budget_allowed": False,
                "boundary": group.get("boundary"), "conditions": group.get("conditions"),
                "source_correspondence": group.get("source_correspondence"),
                "physical_program_signatures": group["physical_program_signatures"],
                "geometry": case["geometry"]}
        else:
            expected = {key: group.get(key) for key in (
                "native_operator_type", "attention_kind", "block", "declared_roles", "status",
                "observed_us", "predicted_us", "predicted_reference_us", "evidence_strength",
                "model_program_already_costed", "additional_budget_allowed", "reason")}
        observed, predicted = group.get("observed_activity_ms_per_forward"), group.get("predicted_service_ms_per_forward")
        expected.update({"case_id": case["case_id"], "receipt": receipt_path,
            "runtime_identity": expected_runtime, "source_identity": case["source_identity"],
            "observed_activity_ms_per_forward": observed,
            "predicted_service_ms_per_forward": predicted,
            "reference_residual_ms_per_forward": predicted - observed if predicted is not None else None,
            "scored": False})
        expected_references[canonical(expected)] += 1

    for item in report["inputs"]:
        source_path = item["path"]
        check(digest(source_path) == item["sha256"], f"Input SHA: {source_path}")
        source = receipt_metadata(source_path)
        for invalid in source.get("invalidated_body_receipts", []):
            check(digest(invalid["path"]) == invalid["sha256"], "Invalidated original receipt remains intact")
            invalidations[invalid["sha256"]] = {"receipt": item,
                "reason": source["reason"], "status": source["status"]}
        expected_runtime = runtime(source)
        for case in receipt_cases(source_path):
            key = source_path, case["case_id"]
            if "comparison" in case:
                if source_path not in body_order:
                    body_order.append(source_path)
                row = body[key]
                seen_body.add(key)
                original, shown = case["comparison"], row["comparison"]
                invalidation = invalidations.get(item["sha256"])
                if invalidation:
                    check(row.get("prediction_invalidation") == invalidation, f"Invalidation identity: {key}")
                    check(row.get("original_comparison") == original, f"Historical prediction retained: {key}")
                    expected = {**original, "status": invalidation["status"], "passed": None,
                                "predicted_ms": None, "per_forward_diff_ms": None, "relative_error": None}
                    check(shown == expected, f"Invalidated predictions excluded: {key}")
                else:
                    check(shown == original, f"Unmodified body comparison: {key}")
                    check("prediction_invalidation" not in row, f"Only declared receipts invalidated: {key}")
                for field in ["runtime_identity", "source_identity", "geometry", "declared_runtime"]:
                    check(row[field] == case.get(field), f"Body {field}: {key}")
                check(row["per_layer"] == (case.get("per_layer_comparison") or {}), f"Layer comparison: {key}")
                for field in ["body_activity_ms", "body_internal_gap_ms"]:
                    check(row[field] == case.get("observed", {}).get(field), f"Body {field}: {key}")
                pk = population(row)
                check(all(value is not None for value in pk), f"Complete population identity: {key}")
                if pk in populations:
                    check(populations[pk] == shown["observed_ms"], f"Shared population unchanged: {key}")
                populations[pk] = shown["observed_ms"]
                if pk not in current_body or shown["status"] == "compared":
                    current_body[pk] = row
                if shown["status"] == "compared":
                    error = shown["predicted_ms"] / shown["observed_ms"]["mean"] - 1
                    check(near(shown["relative_error"], error), f"Body error: {key}")
                    check(near(shown["per_forward_diff_ms"], shown["predicted_ms"] - shown["observed_ms"]["mean"]), f"Body difference: {key}")
                    check(shown["passed"] == (abs(error) <= .15), f"Body pass: {key}")
                    if "window8" in source_path and "kimi" in source_path:
                        identity = case["prediction_execution"]["case_identity"]
                        check(digest(identity["path"]) == identity["sha256"], f"Current Kimi case SHA: {key}")
                        declaration = read(identity["path"])
                        actual = case["prediction"]["model_representation"]["quant"]
                        from mindie_sim.prediction.structure import parse_case
                        effective = parse_case(declaration).model.quant.to_dict()
                        check(actual == effective, f"Effective parsed Kimi quant: {key}")
                        for field, value in declaration.get("quant", declaration["model"].get("quant", {})).items():
                            if field == "exclusions":
                                check(set(value).issubset(actual[field]), f"Explicit Kimi exclusions retained: {key}")
                            else:
                                check(actual.get(field) == value, f"Effective Kimi quant {field}: {key}")
                        expected_expert = "int4" if case["case_id"].startswith("a3_") else "bf16"
                        check(actual["expert_weight_format"] == expected_expert, f"Effective Kimi expert dtype: {key}")
                        corrected_quant_cases += 1
                else:
                    check(all(shown.get(field) is None for field in ("predicted_ms", "relative_error", "passed")), f"Unscored body is not zero: {key}")
            elif "families" in case:
                if source_path not in operator_order:
                    operator_order.append(source_path)
                current_operator[population(case)] = (source_path, case["case_id"])
                count = case["forward_count"]
                check(count > 0, f"Positive operator denominator: {key}")
                for original in case["families"]:
                    fk = (*key, original["native_operator_type"], original["declared_role"])
                    row = family[fk]
                    seen_family.add(fk)
                    observed = original["observed_us"]
                    activity = observed["count"] * observed["mean"]
                    scored = sum(c["observed"]["complete_activity_sum_ns"] / 1000
                                 for c in original.get("cohorts", []) if c["status"] == "compared")
                    check(scored <= activity + 1e-6, f"Scored activity subset: {fk}")
                    check(near(row["measured_activity_ms_per_forward"], activity / count / 1000), f"Family activity: {fk}")
                    check(near(row["unscored_activity_ms_per_forward"], max(0, activity - scored) / count / 1000), f"Exact unscored activity: {fk}")
                    check(row["forward_count"] == count and row["source_identity"] == case["source_identity"], f"Family population: {fk}")
                    check(row["runtime_identity"] == expected_runtime, f"Family runtime: {fk}")
                    check(row["missing_match_is_missing_cost"] is False, f"Missing match not missing cost: {fk}")
                    for field in ["scored_event_count", "unscored_event_count", "compared_cohort_count", "passed_cohort_count"]:
                        check(row[field] == original.get(field), f"Family coverage {field}: {fk}")
                    for value in original.get("cohorts", []):
                        mean, predicted = value.get("observed_per_call_us"), value.get("predicted_per_call_us")
                        if mean is None or predicted is None:
                            continue
                        ck = (*fk, value["cohort_id"])
                        output = cohort[ck]
                        seen_cohort.add(ck)
                        calls = value["observed"]["complete_event_count"]
                        difference = predicted - mean
                        residual = difference * calls / count / 1000
                        for field, expected in {"observed_calls": calls, "observed_us": mean,
                            "predicted_us": predicted, "physical_signature": value["physical_signature"],
                            "status": value["status"], "heavy_call": mean > 50}.items():
                            check(output[field] == expected, f"Cohort {field}: {ck}")
                        for field, expected in {"per_call_diff_us": difference,
                            "signed_activity_residual_ms_per_forward": residual,
                            "absolute_activity_residual_ms_per_forward": abs(residual),
                            "measured_activity_ms_per_forward": mean * calls / count / 1000,
                            "predicted_activity_ms_per_forward": predicted * calls / count / 1000}.items():
                            check(near(output[field], expected), f"Cohort {field}: {ck}")
                        check(output["interpretation"] == "nonadditive_activity_priority_not_causal_body_error_contribution", f"Activity not causal wall clock: {ck}")
                        if value["status"] == "compared":
                            passed = abs(difference / mean) <= .15 if mean > 50 else abs(difference) <= 15
                            check(output["accuracy_pass"] == passed, f"Tiered operator pass: {ck}")
                    for group in original.get("conditional_source_role_references", []):
                        check_reference(item, case, group, expected_runtime, True)
            elif "groups" in case:
                for group in [*case["groups"], *case["source_role_gap_references"]]:
                    check_reference(item, case, group, expected_runtime, False)
        del source
        gc.collect()

    check(seen_body == set(body), "All body receipt rows included exactly once")
    check(seen_family == set(family), "All operator families included exactly once")
    check(seen_cohort == set(cohort), "All numeric cohorts included exactly once")
    check(reference == expected_references, "All conditional references retain evidence and remain unscored")
    observed_current = {population(row): row for row in report["current_body_comparisons"]}
    check(len(observed_current) == len(report["current_body_comparisons"]), "Current body populations unique")
    check(observed_current == current_body, "Current bodies selected in input order, not by error")
    expected_current_families = [row for row in family.values()
        if current_operator[population(row)] == (row["receipt"]["path"], row["case_id"])]
    expected_current_cohorts = [row for row in cohort.values()
        if current_operator[population(row)] == (row["receipt"]["path"], row["case_id"])]
    check(Counter(canonical(row) for row in report["current_operator_families"]) ==
          Counter(canonical(row) for row in expected_current_families), "Current operator families use latest receipt")
    check(Counter(canonical(row) for row in report["current_operator_cohorts"]) ==
          Counter(canonical(row) for row in expected_current_cohorts), "Current operator cohorts use latest receipt")
    summary = report["summary"]
    expected_summary = {"body_compared": sum(row["comparison"]["status"] == "compared" for row in body.values()),
        "body_passed": sum(row["comparison"].get("passed") is True for row in body.values()),
        "current_body_compared": sum(row["comparison"]["status"] == "compared" for row in current_body.values()),
        "current_body_passed": sum(row["comparison"].get("passed") is True for row in current_body.values()),
        "invalidated_body_prediction_arms": sum("prediction_invalidation" in row for row in body.values()),
        "unique_source_count": len({key[0] for key in populations}),
        "unique_source_geometry_populations": len(populations),
        "unique_observed_forward_count": sum(stats["count"] for stats in populations.values()),
        "operator_status_counts": dict(Counter(row["status"] for row in cohort.values())),
        "current_operator_source_populations": len(current_operator),
        "current_operator_scored_events": sum(row["scored_event_count"] for row in expected_current_families),
        "current_operator_body_events": sum(row["observed_us"]["count"] for row in expected_current_families),
        "heavy_cohorts": sum(row["heavy_call"] for row in cohort.values())}
    for key, value in expected_summary.items():
        check(summary[key] == value, f"Summary {key}")
    tiers = {}
    for heavy, label in [(True, "heavy_relative_15pct"), (False, "micro_absolute_15us")]:
        values = [row for row in expected_current_cohorts if row["status"] == "compared" and row["heavy_call"] == heavy]
        tiers[label] = {"compared": len(values), "passed": sum(row["accuracy_pass"] is True for row in values)}
    check(summary["operator_accuracy_by_tier"] == tiers, "Strict current-only tier denominator excludes references")
    manifest = Path(path).with_name("priority-scoreboard-inputs.json")
    if manifest.exists():
        declared = read(manifest)
        check(body_order == declared["body"], "Explicit body input order")
        check(operator_order == declared["operators"], "Explicit operator input order")
    for item in report["additional_evidence"]:
        check(digest(item["path"]) == item["sha256"], f"Additional evidence SHA: {item['path']}")
    check(digest(path) == initial_sha, "Scoreboard unchanged during independent review")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    check(peak_bytes <= 512 * 1024 ** 2, "Bounded reviewer peak RSS")
    return {"schema_version": "mindie-priority-scoreboard-independent-review/2",
        "status": "passed" if not failures else "failed", "checks": checks,
        "failures": failures, "report_sha256": digest(path), "summary": summary,
        "body_rows": len(body), "family_rows": len(family), "cohort_rows": len(cohort),
        "reference_rows": sum(reference.values()), "corrected_kimi_quant_cases_checked": corrected_quant_cases,
        "execution": {"elapsed_seconds": time.monotonic() - started, "peak_rss_bytes": peak_bytes,
                      "receipt_read_engine": "ijson top-level metadata and sequential cases; scoreboard bounded JSON"},
        "scope": "Independent sequential receipt reconciliation; no raw capture parsing or prediction. "
                 "Invalidation, effective current Kimi precision, source/geometry deduplication, explicit input order, "
                 "strict tier arithmetic and unscored source references are checked separately."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = review(args.report)
    output = args.output or args.report.with_name("priority-three-level-scoreboard-independent-review.json")
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0 if result["status"] == "passed" else 1)
