"""Independently reconcile the priority scoreboard against its input receipts.

[Role] Verify reported populations, current selections and numerical accuracy.
[Invariants] Invalid input bindings retain observations but never earn a pass;
  conditional source references never enter strict operator accuracy counts.
[Timeouts & Locks] Sequential bounded receipt reads; local historical Git reads
  have a five-second timeout. No locks, prediction or capture subprocesses.
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
import subprocess
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
    wanted = {"schema_version", "runtime_source_identity", "runtime_sources_unchanged",
              "invalidated_body_receipts", "reason", "status", "runtime_provenance"}
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


def retained_observation_evidence(group):
    """Derive evidence from the original receipt, independently of the importer."""
    observed_abi = group.get("native_abi")
    observed_contract = group.get("observed_contract")
    if observed_abi is not None:
        raw_abi_digest = hashlib.sha256(canonical(observed_abi).encode()).hexdigest()
        domain, measured = "full_native_abi", observed_abi
        evidence = "complete_native_abi_conditional_program_reference"
    elif observed_contract is not None:
        raw_abi_digest = None
        domain, measured = "normalized_contract", observed_contract
        evidence = "complete_normalized_contract_conditional_program_reference"
    else:
        raw_abi_digest = None
        domain, measured = "source_symbol_retained_group", group["retained_group_id"]
        evidence = "source_symbol_conditional_program_reference"
    return {"native_abi_sha256": raw_abi_digest, "observation_identity_domain": domain,
            "observation_identity_sha256": hashlib.sha256(canonical({"domain": domain, "value": measured}).encode()).hexdigest(),
            "evidence_strength": evidence}


def review(path):
    started = time.monotonic()
    initial_sha = digest(path)
    # Cumulative scoreboard arrays can exceed the single-receipt JSON limit.
    # Decode their fields incrementally without also retaining the full text;
    # linked capture receipts are still consumed one case at a time below.
    with Path(path).open("rb") as stream:
        report = dict(ijson.kvitems(stream, "", use_float=True))
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
    selected_body_keys = {(row["receipt"]["path"], row["case_id"]) for row in report["current_body_comparisons"]
                          if row["comparison"]["status"] == "compared"}
    family = index(report["operator_families"],
                   ["case_id", "native_operator_type", "declared_role"])
    cohort = index(report["operator_cohorts"],
                   ["case_id", "native_operator_type", "declared_role", "cohort_id"])
    reference = Counter(canonical(row) for row in report["source_role_references"])
    seen_body, seen_family, seen_cohort = set(), set(), set()
    current_body, current_operator, populations, latest_attempts = {}, {}, {}, {}
    invalidations = {}
    body_order, operator_order, supplement_order = [], [], []
    supplement_cases, operator_actuals, controller_audits = [], {}, []
    corrected_quant_cases = 0
    historical_case_resolutions = []
    expected_references = Counter()

    def check_reference(receipt_path, case, group, expected_runtime, embedded, native=False):
        if native:
            expected_runtime = runtime(case)
            expected = {
                "reference_origin": "external_native_partition",
                "geometry": case["geometry"], "case_identity": case["case_identity"],
                "partition_identity": case["partition_identity"],
                "group_id": group["group_id"],
                "partition_indices": (group["partition_indices"] if "partition_indices" in group
                                      else [group["partition_index"]] if "partition_index" in group else None),
                "retained_group_id": group.get("retained_group_id"),
                "cohort_id": group.get("cohort_id"), "retained_cohort_id": group.get("retained_cohort_id"),
                "observed_contract": group.get("observed_contract"),
                **retained_observation_evidence(group),
                "forward_count": case["forward_count"], "calls_per_forward": group["calls_per_forward"],
                "native_operator_type": group["native_operator_type"],
                "attention_kind": group.get("attention_kind"), "block": group.get("block"),
                "declared_roles": [group["declared_role"]], "layer_ids": group["layer_ids"],
                "status": "reference_only",
                "observed_us": group["observed_us"], "predicted_us": None,
                "predicted_reference_us": group["predicted_reference_us"],
                "model_program_already_costed": True, "additional_budget_allowed": False,
                "boundary": group["reference_boundary"], "conditions": group.get("conditions"),
                "source_correspondence": group["source_correspondence"],
                "physical_program_signatures": group["physical_program_signatures"]}
            label = (case["case_id"], group["group_id"])
            calls = group["observed_us"]["count"]
            forwards = case["forward_count"]
            histogram = group["duration_ns_counter"]
            count = sum(n for _, n in histogram)
            activity = sum(ns * n for ns, n in histogram)
            check(count == calls, f"Native full histogram count: {label}")
            check(activity == group["observed_activity_sum_ns"], f"Native full histogram activity: {label}")
            check(near(group["calls_per_forward"], calls / forwards), f"Native calls per Forward: {label}")
            check(near(group["observed_us"]["mean"], activity / calls / 1000), f"Native full histogram mean: {label}")
            check(near(group["observed_activity_ms_per_forward"], activity / forwards / 1e6), f"Native activity per Forward: {label}")
            check(near(group["predicted_service_ms_per_forward"],
                       group["predicted_reference_us"] * calls / forwards / 1000), f"Native conditional service: {label}")
            check(group["prediction_status"] == "reference_only" and not group["strict_accuracy_implied"]
                  and not group["additional_budget_allowed"], f"Native reference is not strict or extra work: {label}")
        elif embedded:
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
        if source.get("schema_version") == "mindie-controller-operator-population-review/1":
            controller_audits.append((item,read(source_path)))
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
                layers = case.get("per_layer_comparison") or {}
                expanded_row = row
                if "per_layer_reference" in row:
                    expected_layer_reference = {
                        "receipt_sha256": item["sha256"], "case_id": case["case_id"],
                        "field": "per_layer_comparison",
                        "sha256": hashlib.sha256(json.dumps(layers, sort_keys=True).encode()).hexdigest()}
                    check(row["per_layer_reference"] == expected_layer_reference,
                          f"Historical layer detail reference: {key}")
                    expanded_row = {name: value for name, value in row.items()
                                    if name != "per_layer_reference"}
                    expanded_row["per_layer"] = layers
                else:
                    check(row["per_layer"] == layers, f"Layer comparison: {key}")
                for field in ["body_activity_ms", "body_internal_gap_ms"]:
                    check(row[field] == (case.get("observed") or {}).get(field), f"Body {field}: {key}")
                if shown["status"] == "failed":
                    check(row.get("error") == case.get("error"), f"Failed input error retained: {key}")
                    check(all(shown.get(field) is None for field in ("predicted_ms", "relative_error", "passed")),
                          f"Failed prediction is not zero: {key}")
                    if case.get("observed") is None:
                        check(shown["observed_ms"]["count"] == 0, f"Failed read has no measured population: {key}")
                        continue
                    check(row["prediction_failure"] == case["prediction_execution"],
                          f"Failed cost worker is preserved: {key}")
                pk = population(row)
                check(all(value is not None for value in pk), f"Complete population identity: {key}")
                if pk in populations:
                    check(populations[pk] == shown["observed_ms"], f"Shared population unchanged: {key}")
                populations[pk] = shown["observed_ms"]
                if shown["status"] in {"compared", "failed"}:
                    latest_attempts[pk] = row
                if shown["status"] == "failed":
                    continue
                if pk not in current_body or shown["status"] == "compared":
                    current_body[pk] = expanded_row
                if shown["status"] == "compared":
                    error = shown["predicted_ms"] / shown["observed_ms"]["mean"] - 1
                    check(near(shown["relative_error"], error), f"Body error: {key}")
                    check(near(shown["per_forward_diff_ms"], shown["predicted_ms"] - shown["observed_ms"]["mean"]), f"Body difference: {key}")
                    check(shown["passed"] == (abs(error) <= .15), f"Body pass: {key}")
                    if ("window8" in source_path and "kimi" in source_path) or (key in selected_body_keys and "kimi" in case["case_id"].lower()):
                        identity = case["prediction_execution"]["case_identity"]
                        case_path = Path(identity["path"])
                        if digest(case_path) == identity["sha256"]:
                            declaration = read(case_path)
                        else:
                            commit = source.get("runtime_provenance", {}).get("source_commit")
                            repo = next(parent for parent in case_path.parents if (parent / ".git").exists())
                            historical = subprocess.run(["git", "show", f"{commit}:{case_path.relative_to(repo)}"],
                                cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5).stdout
                            historical_sha = hashlib.sha256(historical).hexdigest()
                            check(historical_sha == identity["sha256"], f"Historical Kimi case SHA: {key}")
                            declaration = json.loads(historical)
                            historical_case_resolutions.append({"case_path": str(case_path),
                                "source_commit": commit, "recorded_sha256": identity["sha256"],
                                "historical_sha256": historical_sha,
                                "current_path_sha256": digest(case_path)})
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
                is_supplement = source.get("schema_version") == "mindie-operator-family-supplement/1"
                if is_supplement:
                    if source_path not in supplement_order: supplement_order.append(source_path)
                    supplement_cases.append((item, case))
                else:
                    if source_path not in operator_order: operator_order.append(source_path)
                    current_operator[population(case)] = (source_path, case["case_id"])
                    operator_actuals[population(case)] = case.get("actual_identity")
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
                native = source.get("schema_version") in {
                    "mindie-glm-native-reference-batch/1", "mindie-native-body-reference-batch/1"}
                for group in [*case["groups"], *case.get("source_role_gap_references", [])]:
                    check_reference(item, case, group, expected_runtime, False, native=native)
        del source
        gc.collect()

    check(seen_body == set(body), "All body receipt rows included exactly once")
    failed_rows = [row for row in body.values() if row["comparison"]["status"] == "failed"]
    check(Counter(canonical(row) for row in report.get("body_failed_attempts", [])) ==
          Counter(canonical(row) for row in failed_rows), "Failed attempts remain visible outside measured population")
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
    expected_applications = []
    def native_hist(value, native):
        h = Counter()
        for f in value["families"]:
            if f["native_operator_type"] == native:
                for ns,n in f["duration_ns_counter"]: h[int(ns)] += int(n)
        return sorted(h.items())
    for pin, case in supplement_cases:
        pk = population(case); kinds = set(case["native_operator_types"])
        check(pk in current_operator, "Supplement requires existing source/geometry")
        actual_pin = operator_actuals[pk]
        for identity in (actual_pin,case["actual_identity"]):
            check(digest(identity["path"])==identity["sha256"], "Supplement actual identity")
        baseline=read(actual_pin["path"]);retained=read(case["actual_identity"]["path"])
        for field in ("source_identity","geometry","forward_count","body_acceptance_identity"):
            check(case[field]==baseline[field]==retained[field], "Supplement exact population "+field)
        check(kinds=={f["native_operator_type"] for f in case["families"]}, "Supplement exact named-family scope")
        for native in kinds:
            hist=native_hist(baseline,native)
            check(bool(hist) and hist==native_hist(case,native)==native_hist(retained,native), "Supplement full native histogram")
            proof={"event_count":sum(n for _,n in hist),"duration_ns_histogram_sha256":
                hashlib.sha256(json.dumps(hist,separators=(",",":")).encode()).hexdigest()}
            check(proof==case["native_population_evidence"][native], "Supplement histogram content proof")
        before=[r for r in expected_current_families if population(r)==pk and r["native_operator_type"] in kinds]
        expected_current_families=[r for r in expected_current_families if not (population(r)==pk and r["native_operator_type"] in kinds)] + [
            r for r in family.values() if r["receipt"]["path"]==pin["path"] and r["case_id"]==case["case_id"]]
        expected_current_cohorts=[r for r in expected_current_cohorts if not (population(r)==pk and r["native_operator_type"] in kinds)] + [
            r for r in cohort.values() if r["receipt"]["path"]==pin["path"] and r["case_id"]==case["case_id"]]
        expected_applications.append({"receipt":pin,"case_id":case["case_id"],"source_identity":case["source_identity"],
            "geometry":case["geometry"],"forward_count":case["forward_count"],"native_operator_types":sorted(kinds),
            "native_population_evidence":case["native_population_evidence"],
            "replaced_rows":[{"receipt":r["receipt"],"case_id":r["case_id"],"native_operator_type":r["native_operator_type"],
                              "declared_role":r["declared_role"]} for r in before]})
        del baseline,retained
    check(report.get("operator_supplement_applications",[])==expected_applications,"Native supplements replace only the audited family")
    expected_overlays={}
    def controller_key(row):
        return row["receipt"]["sha256"],row["case_id"],row["native_operator_type"],row["declared_role"]
    for pin,audit in controller_audits:
        check(audit["status"]=="passed" and not audit["failures"], "Controller audit passed")
        for position,item in enumerate(audit["populations"]):
            check(item["strict_event_count"]==item["reference_event_count"]==0 and item["full_histogram_matches_typed_controller_evidence"], "Controller audited type/histogram boundary")
            for row in expected_current_families:
                if population(item)!=population(row) or item["native_operator_type"]!=row["native_operator_type"]:
                    continue
                exact=any(o["operator_receipt_identity"]["sha256"]==row["receipt"]["sha256"] and o["report_case_id"]==row["case_id"]
                          and o["family_key"]==[row["native_operator_type"],row["declared_role"]] for o in item["matched_operator_occurrences"])
                actual=operator_actuals.get(population(row)) or {}
                if not exact and actual.get("sha256")!=item["actual_identity"]["sha256"]:
                    continue
                check(row["status"]=="unresolved" and row["scored_event_count"]==0, "Controller remains unscored")
                check(row["forward_count"]==item["forward_count"] and row["observed_us"]["count"]==item["observed_event_count"], "Controller complete population preserved")
                check(near(row["observed_us"]["mean"]*1000*item["observed_event_count"],item["observed_activity_sum_ns"]), "Controller exact activity preserved")
                expected_overlays[controller_key(row)]={"audit_identity":pin,"population_index":position,
                    "basis":"exact_audited_operator_occurrence" if exact else "same_audited_actual_population_new_program_receipt",
                    "physical_service_comparable":False,"raw_population_and_strict_denominators_unchanged":True}
    controller_rows=[]
    for row in expected_current_families:
        expected=expected_overlays.get(controller_key(row))
        check(row.get("controller_overlay")==expected,"Controller audited current population overlay complete")
        if expected is not None:controller_rows.append(row)
    check(Counter(canonical(r) for r in report.get("current_controller_overlays",[]))==Counter(canonical(r) for r in controller_rows),"Controller display overlay preserves original rows")
    check(Counter(canonical(row) for row in report["current_operator_families"]) ==
          Counter(canonical(row) for row in expected_current_families), "Current operator families use latest receipt")
    check(Counter(canonical(row) for row in report["current_operator_cohorts"]) ==
          Counter(canonical(row) for row in expected_current_cohorts), "Current operator cohorts use latest receipt")
    if "current_source_role_references" in report:
        other_references, selected_references = [], {}
        for row in report["source_role_references"]:
            pk = population(row)
            if (row.get("reference_origin") != "external_native_partition"
                    and pk in current_operator and current_operator[pk] !=
                    (row["receipt"]["path"], row["case_id"])):
                continue
            if row.get("reference_origin") == "external_native_partition":
                evidence_key = row["native_abi_sha256"]
                if evidence_key is None:
                    evidence_key = (row["observation_identity_domain"], row["observation_identity_sha256"])
                key = (pk, row["native_operator_type"], tuple(sorted(row["declared_roles"])),
                       tuple(sorted(row["layer_ids"])), evidence_key)
                selected_references[key] = row
            else:
                other_references.append(row)
        expected_current_references = other_references + list(selected_references.values())
        check(Counter(canonical(row) for row in report["current_source_role_references"]) ==
              Counter(canonical(row) for row in expected_current_references),
              "Current references use their own population/role/layer/observation-domain generation; embedded references follow operator generation")
    runtime_sets = {}
    for row in expected_current_families:
        runtime_sets.setdefault(population(row),set()).add(row["runtime_identity"]["recorded_sim_file_map_sha256"] or "unknown")
    current_runtime_populations={key:next(iter(values)) if len(values)==1 else "mixed_native_family_runtimes"
                                 for key,values in runtime_sets.items()}
    summary = report["summary"]
    if "latest_body_attempts" in report:
        check(Counter(canonical(row) for row in report["latest_body_attempts"]) ==
              Counter(canonical(row) for row in latest_attempts.values()), "Latest attempts retain failed cost workers")
        check(summary["latest_body_attempt_count"] == len(latest_attempts), "Latest attempt denominator")
        check(summary["latest_body_attempt_completed"] == sum(row["comparison"]["status"] == "compared"
              for row in latest_attempts.values()), "Latest completed attempts")
        check(summary["latest_body_attempt_failed"] == sum(row["comparison"]["status"] == "failed"
              for row in latest_attempts.values()), "Latest failed attempts")
        check(summary["latest_body_attempt_passed"] == sum(row["comparison"].get("passed") is True
              for row in latest_attempts.values()), "Latest passed attempts")
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
        "current_operator_runtime_populations": dict(Counter(current_runtime_populations.values())),
        "current_operator_scored_events": sum(row["scored_event_count"] for row in expected_current_families),
        "current_operator_body_events": sum(row["observed_us"]["count"] for row in expected_current_families),
        "heavy_cohorts": sum(row["heavy_call"] for row in cohort.values())}
    if "operator_supplement_applications" in summary:
        expected_summary["operator_supplement_applications"]=len(expected_applications)
        expected_summary["current_mixed_operator_runtime_populations"]=sum(len(v)>1 for v in runtime_sets.values())
    if "current_controller_overlay_rows" in summary:
        expected_summary["current_controller_overlay_rows"]=len(controller_rows)
        expected_summary["current_controller_overlay_events"]=sum(r["observed_us"]["count"] for r in controller_rows)
    if "body_failed_attempts" in summary:
        expected_summary["body_failed_attempts"] = len(failed_rows)
    for key, value in expected_summary.items():
        check(summary[key] == value, f"Summary {key}")
    if "current_external_native_reference_groups" in summary:
        native_rows = [row for row in expected_current_references
                       if row.get("reference_origin") == "external_native_partition"]
        native_populations = {population(row): row["forward_count"] for row in native_rows}
        for key, value in {
            "groups": len(native_rows), "calls": sum(row["observed_us"]["count"] for row in native_rows),
            "populations": len(native_populations), "forwards": sum(native_populations.values())
        }.items():
            check(summary[f"current_external_native_reference_{key}"] == value,
                  f"Native reference independent denominator: {key}")
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
        check(supplement_order == declared.get("operator_supplements",[]), "Explicit supplement input order")
        check([pin["path"] for pin,_ in controller_audits] == declared.get("controller_overlays",[]), "Explicit controller audit inputs")
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
        "historical_case_resolutions": historical_case_resolutions,
        "execution": {"elapsed_seconds": time.monotonic() - started, "peak_rss_bytes": peak_bytes,
            "receipt_read_engine": "ijson top-level fields and sequential receipt cases"},
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
