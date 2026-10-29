"""Reprice retained body observations against an independently rebuilt declaration.

[Role] Reuse captured aggregates without scanning CSV or copying capture snapshots.
[Invariants] New work comes only from a fresh Sim manifest. Aggregate rebinding
  cannot split measured populations or infer ABI from two retained examples.
[Timeouts & Locks] One bounded subprocess per physical program; 512 MiB acceptance
  limit. No locks; outputs are a new, explicit comparison arm.
[Side-Effect Policy] Read saved evidence and Sim metadata; write new reports only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import _freeze
from mindie_sim.cohort_comparison import _check_cohort, compare_cohorts
from mindie_sim.structure import export_structure
from compare_body_operator_families import (
    family_rows, prediction_runtime_identity, program_references, render,
)
from replay_body_operator_families import RoleMapper, declared_role, identity, read, write
from replay_fusion_cohorts import _compact_comparison, _failed_cohort, _program_key, _rss


MAX_RSS = 512 * 1024**2


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def runtime_identity():
    result = prediction_runtime_identity()
    for path in (Path(__file__).resolve(), Path(__file__).with_name("rebind_body_source_roles.py").resolve(),
                 Path(__file__).with_name("rebind_grouped_source_roles.py").resolve()):
        source = identity(path)
        result[source["path"]] = source["sha256"]
    return result


def compact_case(value):
    """The global index references per-source histograms rather than duplicating them."""
    if isinstance(value, dict):
        return {key: compact_case(item) for key, item in value.items()
                if key not in {"duration_ns_counter", "examples", "candidate_target_ids"}}
    if isinstance(value, list):
        return [compact_case(item) for item in value]
    return value


def fresh_structure(case_path, mapping):
    execution = mapping["declared_execution"]
    geometry = {key: execution[key] for key in ("phase", "tokens", "context", "sequences", "scope")}
    for key in ("apply_body_defaults", "expand_calls"):
        if key in execution:
            geometry[key] = execution[key]
    return export_structure(read(case_path), **geometry)


def validate_observation_join(actual, mapping):
    """The observed cohort population must belong to this retained source and geometry."""
    source = actual["source_identity"]
    for window in mapping["windows"]:
        if any(window["source_identity"].get(key) != source.get(key)
               for key in ("path", "sha256", "size_bytes")):
            raise ValueError("mapping_and_actual_source_identity_differ")
    execution, geometry = mapping["declared_execution"], actual["geometry"]
    if (execution["phase"] != "decode" or execution["scope"] != "body"
            or execution["tokens"] != geometry["tokens_per_sequence"]
            or execution["sequences"] != geometry["sequences_per_replica"]
            or execution["context"] != actual["conditional_context_tokens"]):
        raise ValueError("mapping_and_actual_execution_geometry_differ")
    observed = {(row["native_operator_type"], row["declared_role"]): row for row in actual["families"]}
    counts, activity = Counter(), Counter()
    for window in mapping["windows"]:
        for row in window["cohorts"]:
            key = row["native_operator_type"], "|".join(mapping["conditional_role_by_cohort_id"][row["cohort_id"]])
            counts[key] += row["event_count"]
            activity[key] += row["complete_activity_sum_ns"]
    for key, count in counts.items():
        family = observed.get(key)
        if (family is None or count > family["observed_us"]["count"]
                or activity[key] > sum(ns * n for ns, n in family["duration_ns_counter"])):
            raise ValueError("mapping_cohort_population_exceeds_actual_family")


def _observation(window, source):
    rank = window["rank_id"]
    ref = SourceRef(rank, 0, "csv", source["path"], Path(source["path"]).name,
                    source["sha256"], source["size_bytes"], source.get("schema_version", "retained"),
                    "retained_verified_body_aggregate", mtime_ns=source.get("mtime_ns"))
    bounds = window["window"]
    return Observation(rank, 0, Window(bounds["start_ns"], bounds["end_ns"]), None, [], ref,
                       QueryStats(rank, "retained_cohort_rebind"))


def rebind_mapping(mapping, manifest, source):
    """Retain observations only when the complete semantic candidate set survives.

    This deliberately does not rematch changed native contracts. Saved family
    histograms may mix several contracts, and their two examples do not establish
    which calls belong to a new physical subset.
    """
    mapper = RoleMapper(manifest, mapping_limit=0, phase=manifest["execution"]["phase"])
    targets = mapper.target_index.all
    if mapping["graph_id"] == manifest["graph_id"]:
        for window in mapping["windows"]:
            for cohort in window["cohorts"]:
                _check_cohort(cohort, window, manifest, targets)
        return mapping, {"mode": "identical_declaration_new_cost", "rebound": [], "excluded": []}
    windows, roles, changes, excluded = [], {}, [], []
    for window in mapping["windows"]:
        observation = _observation(window, source)
        accumulator = CohortAccumulator(manifest["graph_id"], mapper.target_index, observation,
                                        execution=manifest["execution"])
        cohorts, counts = [], Counter(window.get("cohort_excluded_event_counts", {}))
        for old in window["cohorts"]:
            old_roles = mapping["conditional_role_by_cohort_id"][old["cohort_id"]]
            available = mapper._rank_candidates(
                mapper.contracts.get(_freeze(old["contract"]), ()), observation.rank_id)
            candidates = sorted(key for key in available if declared_role(targets[key]) in old_roles)
            reason = None
            if candidates != sorted(old["target_ids"]):
                reason = "observed_contract_or_semantic_candidate_set_changed"
            declaration = None
            if reason is None:
                declaration, reason = accumulator._cohort(candidates)
            if reason is None:
                for field in ("target_kind", "placement", "replica", "stage", "phase",
                              "resource_boundary", "contract_scope", "structural_classification"):
                    if canonical(old.get(field)) != canonical(declaration.get(field)):
                        reason = "aggregate_" + field + "_changed"
                        break
            if reason:
                counts["rebind:" + reason] += old["event_count"]
                excluded.append({"old_cohort_id": old["cohort_id"], "native_operator_type": old["native_operator_type"],
                    "declared_roles": old_roles, "event_count": old["event_count"], "reason": reason,
                    "observed_contract": old["contract"], "requires": "richer_observed_partition_or_targeted_evidence"})
                continue
            key = (old["native_operator_type"], old["device_id"], tuple(candidates))
            cohort_id = "sha256:" + sha256(canonical((manifest["graph_id"], observation.rank_id, key)).encode()).hexdigest()
            row = {**old, **declaration, "cohort_id": cohort_id}
            # _cohort supplies all fresh declaration fields; observed timing is
            # unchanged and is never used to select the candidate set.
            _check_cohort(row, window, manifest, targets)
            cohorts.append(row)
            roles[cohort_id] = old_roles
            changes.append({"old_cohort_id": old["cohort_id"], "cohort_id": cohort_id,
                            "event_count": old["event_count"], "observation_partition": "identical"})
        windows.append({**window, "cohorts": cohorts, "cohort_excluded_event_counts": dict(counts)})
    result = {**mapping, "graph_id": manifest["graph_id"], "declared_execution": manifest["execution"],
              "structure_source": manifest.get("source"), "windows": windows,
              "conditional_role_by_cohort_id": roles,
              "cohort_event_window_count": sum(c["event_count"] for w in windows for c in w["cohorts"]),
              "cohort_status": "partial" if excluded else "aggregated"}
    return result, {"mode": "one_to_one_aggregate_rebind", "rebound": changes, "excluded": excluded}


def safe_reference_actual(actual, manifest):
    """Do not carry old reference work through a changed declared program."""
    targets = {node["node_id"]: node for node in manifest["nodes"]}
    retained, excluded = [], []
    for group in actual.get("source_role_references", ()):
        selected = [targets[key] for key in group["representative_target_ids"] if key in targets]
        same = (len(selected) == len(group["representative_target_ids"])
                and [node["physical_signature"] for node in selected] == group["physical_program_signatures"]
                and [node["physical_work"] for node in selected] == group["physical_work_per_program"])
        if same:
            retained.append(group)
        else:
            excluded.append({"group_id": group["group_id"], "native_operator_type": group["native_operator_type"],
                "declared_role": group["declared_role"], "event_count": group["observed_us"]["count"],
                "reason": "source_reference_requires_fresh_abi_or_source_correspondence_rebind",
                "full_native_abi_retained": group["source_correspondence"].get("observed_native_tensor_contract") is not None})
    return {**actual, "source_role_references": retained}, excluded


def reference_coverage(total, strict, groups, excluded):
    covered = sum(group["observed_us"]["count"] for group in groups)
    dropped = sum(group.get("event_count", 0) for group in excluded)
    if strict + covered + dropped > total:
        raise ValueError("source_reference_partitions_overlap_or_exceed_family")
    return {"measured_event_count": total, "strict_scored_event_count": strict,
            "reference_event_count": covered, "excluded_reference_event_count": dropped,
            "unclassified_event_count": total - strict - covered - dropped,
            "reference_events_enter_strict_denominator": False}


def repriced_family_rows(actual, mapping, comparison, references, excluded):
    """Preserve partial reference groups without implying coverage of the whole family."""
    groups = references.get("_source_role_groups", ())
    rows = family_rows(actual, mapping, comparison,
                       {key: value for key, value in references.items() if key != "_source_role_groups"})
    for row in rows:
        selected = [group for group in groups if group["native_operator_type"] == row["native_operator_type"]
                    and group["declared_role"] == row["declared_role"]]
        dropped = [group for group in excluded if group.get("native_operator_type") == row["native_operator_type"]
                   and group.get("declared_role") == row["declared_role"]]
        if selected or dropped:
            row["source_reference_coverage"] = reference_coverage(
                row["observed_us"]["count"], row["scored_event_count"], selected, dropped)
            row["conditional_source_role_references"] = selected
            if selected:
                row["evidence_strength"] = "partial_source_reference" if dropped else "source_reference"
                row["status"] = "compared" if row["scored_event_count"] else "reference_only"
    return rows


def render_repriced(report):
    lines = [render(report), "", "## Retained source-reference coverage", "",
             "Reference coverage stays outside strict accuracy; excluded calls retain their measured durations.", "",
             "| Case / native role | All calls | Strict | Reference | Excluded reference | Other unclassified |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for case in report["cases"]:
        for family in case["families"]:
            counts = family.get("source_reference_coverage")
            if counts:
                role = family["declared_role"].replace("|", " + ")
                lines.append(f"| {case['case_id']} / {family['native_operator_type']} / {role} | "
                    + " | ".join(str(counts[key]) for key in ("measured_event_count", "strict_scored_event_count",
                      "reference_event_count", "excluded_reference_event_count", "unclassified_event_count")) + " |")
    return "\n".join(lines) + "\n"


def worker(args):
    mapping = read(args.mapping)
    started = time.perf_counter()
    if args.worker == "program":
        key = json.loads(args.program_key)
        mapping = {**mapping, "windows": [{**window, "cohorts": [
            row for row in window["cohorts"] if list(_program_key(row)) == key]}
            for window in mapping["windows"]]}
        result = _compact_comparison(compare_cohorts(args.case, mapping))
    else:
        actual = read(args.actual)
        manifest = fresh_structure(args.case, mapping)
        rebindings = []
        if args.frozen_native_rebind:
            from rebind_body_source_roles import rebind_frozen_native_groups
            from rebind_grouped_source_roles import rebind_frozen_grouped_groups
            actual, rebindings = rebind_frozen_native_groups(actual, manifest)
            actual, grouped_rebindings = rebind_frozen_grouped_groups(actual, manifest)
            rebindings += grouped_rebindings
        retained, excluded = safe_reference_actual(actual, manifest)
        del manifest
        result = {"references": program_references(args.case, mapping, retained), "excluded": excluded,
                  "frozen_native_rebindings": rebindings}
    result.update(maximum_resident_set_size_bytes=_rss(), elapsed_seconds=time.perf_counter() - started)
    if result["maximum_resident_set_size_bytes"] > MAX_RSS:
        raise RuntimeError("comparison_worker_exceeds_512_mib")
    write(args.worker_output, result)


def run_worker(args, *, kind, actual_path, mapping_path, case_path, output, key=None):
    timeout = args.compare_timeout if kind == "program" else args.reference_timeout
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", kind,
               "--actual", str(actual_path), "--mapping", str(mapping_path), "--case", str(case_path),
               "--worker-output", str(output)]
    if key is not None:
        command += ["--program-key", json.dumps(key)]
    if kind == "references" and args.frozen_native_rebind:
        command.append("--frozen-native-rebind")
    started = time.perf_counter()
    try:
        child = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        failure = {"reason": "physical_program_timeout", "timeout_seconds": timeout}
    else:
        failure = None if child.returncode == 0 else {"reason": "comparison_process_failed",
                   "returncode": child.returncode, "stderr": child.stderr[-6000:]}
    receipt = {"kind": kind, "physical_program_key": key, "timeout_seconds": timeout,
               "elapsed_seconds": time.perf_counter() - started, "status": "failed" if failure else "completed"}
    if failure:
        receipt.update(failure)
        return None, receipt
    result = read(output)
    output.unlink()
    receipt["maximum_resident_set_size_bytes"] = result["maximum_resident_set_size_bytes"]
    return result, receipt


def compare_programs(args, prefix, actual_path, mapping_path, case_path, mapping):
    keys = list(dict.fromkeys(_program_key(row) for window in mapping["windows"] for row in window["cohorts"]))
    by_cohort, receipts, base = {}, [], None
    for index, key in enumerate(keys):
        partial = prefix.with_suffix(f".program-{index}.json")
        result, receipt = run_worker(args, kind="program", actual_path=actual_path, mapping_path=mapping_path,
                                     case_path=case_path, output=partial, key=list(key))
        receipts.append(receipt)
        if result is None:
            for wi, window in enumerate(mapping["windows"]):
                for row in window["cohorts"]:
                    if _program_key(row) == key:
                        by_cohort[wi, row["cohort_id"]] = _failed_cohort(row, receipt)
        else:
            base = base or {k: v for k, v in result.items() if k not in {"windows", "status_counts"}}
            for wi, window in enumerate(result["windows"]):
                by_cohort.update(((wi, row["cohort_id"]), row) for row in window["cohorts"])
        print(json.dumps({"case": prefix.name, "program": index + 1, "programs": len(keys),
                          "status": receipt["status"]}), flush=True)
    windows = [{**{k: v for k, v in window.items() if k != "cohorts"},
                "cohorts": [by_cohort[wi, row["cohort_id"]] for row in window["cohorts"]]}
               for wi, window in enumerate(mapping["windows"])]
    return {**(base or {"graph_id": mapping["graph_id"], "report_schema_version": "mindie-sim.cohort-comparison/1"}),
            "windows": windows, "status_counts": dict(Counter(row["status"] for w in windows for row in w["cohorts"])),
            "program_receipts": receipts, "attempted_physical_programs": len(keys),
            "maximum_resident_set_size_bytes": max((r.get("maximum_resident_set_size_bytes", 0) for r in receipts), default=0),
            "raw_capture_reads": 0, "old_prediction_reused": False}


def reprice(args):
    before, started, cases, plans, seen = runtime_identity(), time.perf_counter(), [], [], set()
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / "body-operator-family-scoreboard.json").exists():
        raise ValueError("choose_a_new_output_arm_existing_report_not_overwritten")
    for actual_path in args.actual:
        actual_path = actual_path.resolve()
        actual = read(actual_path)
        if actual["case_id"] in seen:
            raise ValueError("one_observation_arm_per_case_id_required")
        seen.add(actual["case_id"])
        old_prefix = actual_path.with_name(actual_path.name.removesuffix(".actual.json"))
        old_mapping_path = (args.mapping or old_prefix.with_suffix(".mapping.json")).resolve()
        selected_source = (Path(actual["case_identity"]["path"]) if args.use_source_case_path
                           else old_prefix.with_suffix(".case.json"))
        case_path = (args.case or (args.case_dir / Path(actual["case_identity"]["path"]).name
                     if args.case_dir else selected_source)).resolve()
        input_pins = {"actual_identity": identity(actual_path), "old_mapping_identity": identity(old_mapping_path),
                      "case_identity": identity(case_path)}
        old_mapping = read(old_mapping_path)
        validate_observation_join(actual, old_mapping)
        manifest = fresh_structure(case_path, old_mapping)
        mapping, plan = rebind_mapping(old_mapping, manifest, actual["source_identity"])
        prefix = args.output_dir / ("body-operator-" + actual["case_id"] + "-" + args.variant)
        mapping_path = old_mapping_path
        if mapping is not old_mapping:
            mapping_path = prefix.with_suffix(".mapping.json")
            write(mapping_path, mapping)
        if args.role:
            mapping = {**mapping, "windows": [{**w, "cohorts": [c for c in w["cohorts"]
                if set(mapping["conditional_role_by_cohort_id"][c["cohort_id"]]) & set(args.role)]}
                for w in mapping["windows"]]}
            mapping_path = prefix.with_suffix(".selected-mapping.json")
            write(mapping_path, mapping)
        plan = {**plan, **input_pins, "case_id": actual["case_id"], "fresh_graph_id": manifest["graph_id"],
                "mapping_identity": identity(mapping_path), "selected_roles": args.role,
                "model_representation": {key: manifest["model"].get(key) for key in (
                    "quantization", "quant", "activation_dtype", "weight_dtype", "kv_dtype", "compute_dtype")},
                "observed_geometry": actual["geometry"], "declared_execution": manifest["execution"],
                "raw_capture_reads": 0, "old_prediction_reused": False}
        plans.append(plan)
        if args.validate_only:
            continue
        comparison = compare_programs(args, prefix, actual_path, mapping_path, case_path, mapping)
        comparison_path = prefix.with_suffix(".comparison.json")
        write(comparison_path, comparison)
        if args.skip_references:
            references, reference_exclusions, reference_receipt = {}, [], {"status": "not_requested"}
        else:
            reference_result, reference_receipt = run_worker(args, kind="references", actual_path=actual_path,
                mapping_path=mapping_path, case_path=case_path, output=prefix.with_suffix(".references-worker.json"))
            if reference_result is None:
                references, reference_exclusions = {}, [{"reason": "reference_prediction_failed", **reference_receipt}]
            else:
                references, reference_exclusions = reference_result["references"], reference_result["excluded"]
        families = repriced_family_rows(actual, mapping, comparison, references, reference_exclusions)
        for family in families:
            family["retained_observation_classification"] = "original_mapping_generation"
            family["current_rebind_exclusions"] = [r for r in plan["excluded"]
                if r["native_operator_type"] == family["native_operator_type"]
                and "|".join(r["declared_roles"]) == family["declared_role"]]
            family["current_source_reference_exclusions"] = [r for r in reference_exclusions
                if r.get("native_operator_type") in {None, family["native_operator_type"]}
                and r.get("declared_role") in {None, family["declared_role"]}]
        row = {"case_id": actual["case_id"] + " / " + args.variant,
            "source_case_id": actual.get("source_case_id", actual["case_id"]), "variant": args.variant,
            **input_pins, "mapping_identity": identity(mapping_path), "comparison_identity": identity(comparison_path),
            "source_identity": actual["source_identity"], "forward_count": actual["forward_count"],
            "source_forward_count": actual["source_forward_count"], "geometry": actual["geometry"],
            "families": families, "passed_cohorts": sum(f["passed_cohort_count"] for f in families),
            "comparison_status_counts": comparison["status_counts"], "strict_prediction_reused_from": None,
            "reference_receipt": reference_receipt, "reference_exclusions": reference_exclusions,
            "frozen_native_rebindings": (reference_result.get("frozen_native_rebindings", [])
                if not args.skip_references and reference_result else []),
            "declaration_refresh": plan}
        detail_path = prefix.with_suffix(".family-scoreboard.json")
        detail = {"schema_version": "mindie-body-operator-comparison/1", "cases": [row],
                  "runtime_source_identity": before, "raw_capture_reads": 0,
                  "old_prediction_reused": False}
        write(detail_path, detail)
        prefix.with_suffix(".family-scoreboard.md").write_text(render_repriced(detail))
        cases.append({**compact_case(row), "case_detail_identity": identity(detail_path),
                      "projection": "statistics_and_costs; exact_histograms_in_case_detail"})
        for record in input_pins.values():
            if identity(record["path"]) != record:
                raise ValueError("retained_input_changed_during_reprice")
        del actual, old_mapping, manifest, mapping, comparison, families, row, detail, references
        if not args.skip_references:
            del reference_result
    if runtime_identity() != before:
        raise ValueError("runtime_changed_during_reprice")
    write(args.output_dir / "reprice-plan.json", {"schema_version": "mindie-body-reprice-plan/1", "cases": plans,
          "runtime_source_identity": before, "runtime_sources_unchanged": True, "raw_capture_reads": 0})
    if args.validate_only:
        print(json.dumps({"validated_cases": len(plans), "modes": dict(Counter(p["mode"] for p in plans))}))
        return
    failed = any(c["comparison_status_counts"].get("prediction_failed") or c["reference_receipt"]["status"] == "failed" for c in cases)
    result = {"schema_version": "mindie-body-operator-comparison/1", "status": "partial" if failed else "completed",
              "cases": cases, "runtime_source_identity": before, "runtime_sources_unchanged": True,
              "runtime_source_commit": args.runtime_source_commit,
              "runtime_validation_status": args.runtime_validation_status, "raw_capture_reads": 0,
              "coverage_status": "partial" if any(f["unscored_event_count"] for c in cases for f in c["families"]) else "complete",
              "elapsed_seconds": time.perf_counter() - started, "old_prediction_reused": False}
    write(args.output_dir / "body-operator-family-scoreboard.json", result)
    (args.output_dir / "body-operator-family-scoreboard.md").write_text(render_repriced(result))
    if failed:
        raise SystemExit("reprice_contains_visible_prediction_failures")


def sim_sources(runtime):
    return {path: digest for path, digest in runtime.items() if "mindie_sim" in Path(path).parts}


def validate_reference_retry(row, original_runtime, current_runtime):
    """Reuse successful costs only under the identical Sim, case and mapping."""
    original_sim = sim_sources(original_runtime)
    if not original_sim or original_sim != sim_sources(current_runtime):
        raise ValueError("reference_retry_sim_runtime_changed")
    for key in ("actual_identity", "mapping_identity", "case_identity", "comparison_identity"):
        if identity(row[key]["path"]) != row[key]:
            raise ValueError("reference_retry_input_identity_changed:" + key)
    actual = read(row["actual_identity"]["path"])
    mapping = read(row["mapping_identity"]["path"])
    comparison = read(row["comparison_identity"]["path"])
    validate_observation_join(actual, mapping)
    if comparison["graph_id"] != mapping["graph_id"]:
        raise ValueError("reference_retry_comparison_graph_differs")
    if comparison["status_counts"].get("prediction_failed"):
        raise ValueError("reference_retry_requires_successful_strict_predictions")
    return actual, mapping, comparison


def retry_references(args):
    """Retry failed references in a new arm; preserve successful strict receipts."""
    before, started = runtime_identity(), time.perf_counter()
    source_report = args.retry_references_from.resolve()
    report_identity, original = identity(source_report), read(source_report)
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if (args.output_dir / "body-operator-family-scoreboard.json").exists():
        raise ValueError("choose_a_new_output_arm_existing_report_not_overwritten")
    cases, attempts = [], 0
    for previous in original["cases"]:
        detail_identity = previous["case_detail_identity"]
        if identity(detail_identity["path"]) != detail_identity:
            raise ValueError("reference_retry_detail_identity_changed")
        saved = read(detail_identity["path"])["cases"][0]
        actual, mapping, comparison = validate_reference_retry(
            saved, original["runtime_source_identity"], before)
        prefix = args.output_dir / ("body-operator-" + actual["case_id"] + "-" + args.variant)
        row = {**saved, "case_id": actual["case_id"] + " / " + args.variant, "variant": args.variant,
               "strict_prediction_reused_from": saved["comparison_identity"],
               "reference_retry_source_report": report_identity,
               "previous_reference_receipt": saved["reference_receipt"]}
        eligible_rebind = args.frozen_native_rebind and any(
            group["native_operator_type"] == "DispatchFFNCombine"
            for group in actual.get("source_role_references", ()))
        retried = saved["reference_receipt"]["status"] == "failed" or eligible_rebind
        history = list(saved.get("reference_attempt_history", []))
        if not history:
            if saved.get("previous_reference_receipt"):
                history.append(saved["previous_reference_receipt"])
            history.append(saved["reference_receipt"])
        if retried:
            attempts += 1
            result, receipt = run_worker(args, kind="references", actual_path=Path(saved["actual_identity"]["path"]),
                mapping_path=Path(saved["mapping_identity"]["path"]), case_path=Path(saved["case_identity"]["path"]),
                output=prefix.with_suffix(".references-worker.json"))
            references = result["references"] if result else {}
            excluded = result["excluded"] if result else [{"reason": "reference_prediction_failed", **receipt}]
            families = repriced_family_rows(actual, mapping, comparison, references, excluded)
            for family in families:
                family["retained_observation_classification"] = "original_mapping_generation"
                family["current_rebind_exclusions"] = [item for item in saved["declaration_refresh"]["excluded"]
                    if item["native_operator_type"] == family["native_operator_type"]
                    and "|".join(item["declared_roles"]) == family["declared_role"]]
                family["current_source_reference_exclusions"] = [item for item in excluded
                    if item.get("native_operator_type") in {None, family["native_operator_type"]}
                    and item.get("declared_role") in {None, family["declared_role"]}]
            row.update(families=families, reference_receipt=receipt, reference_exclusions=excluded,
                       frozen_native_rebindings=result.get("frozen_native_rebindings", []) if result else [])
            history.append(receipt)
            del result, references, excluded, families
        row["reference_attempt_history"] = history
        row["reference_retry"] = {"attempted": retried, "strict_programs_executed": 0,
                                  "raw_capture_reads": 0, "sim_sources_identical": True}
        detail_path = prefix.with_suffix(".family-scoreboard.json")
        detail = {"schema_version": "mindie-body-operator-comparison/1", "cases": [row],
                  "runtime_source_identity": before, "strict_prediction_source_report": report_identity,
                  "raw_capture_reads": 0, "successful_strict_predictions_reused": True}
        write(detail_path, detail)
        prefix.with_suffix(".family-scoreboard.md").write_text(render_repriced(detail))
        cases.append({**compact_case(row), "case_detail_identity": identity(detail_path),
                      "projection": "statistics_and_costs; exact_histograms_in_case_detail"})
        print(json.dumps({"case": actual["case_id"], "reference_retry": retried,
                          "status": row["reference_receipt"]["status"]}), flush=True)
        for key in ("actual_identity", "mapping_identity", "case_identity", "comparison_identity"):
            if identity(saved[key]["path"]) != saved[key]:
                raise ValueError("reference_retry_input_changed_during_execution")
        del actual, mapping, comparison, saved, row, detail
    if runtime_identity() != before or identity(source_report) != report_identity:
        raise ValueError("reference_retry_runtime_or_original_report_changed")
    failed = any(case["reference_receipt"]["status"] == "failed" for case in cases)
    report = {"schema_version": "mindie-body-operator-comparison/1", "status": "partial" if failed else "completed",
              "cases": cases, "runtime_source_identity": before, "runtime_sources_unchanged": True,
              "runtime_source_commit": original.get("runtime_source_commit"),
              "runtime_validation_status": original.get("runtime_validation_status"),
              "strict_prediction_source_report": report_identity, "reference_retry_count": attempts,
              "frozen_native_rebind_requested": args.frozen_native_rebind,
              "new_strict_program_count": 0, "successful_strict_predictions_reused": True,
              "coverage_status": original["coverage_status"], "raw_capture_reads": 0,
              "elapsed_seconds": time.perf_counter() - started}
    write(args.output_dir / "body-operator-family-scoreboard.json", report)
    (args.output_dir / "body-operator-family-scoreboard.md").write_text(render_repriced(report))
    if failed:
        raise SystemExit("reference_retry_contains_visible_failures")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", type=Path, action="append", default=[])
    parser.add_argument("--retry-references-from", type=Path,
                        help="Retry only failed references; preserve same-runtime successful strict comparisons")
    parser.add_argument("--frozen-native-rebind", action="store_true",
                        help="Revalidate complete retained MC2 and GroupedMatmul ABI partitions as conditional references")
    parser.add_argument("--mapping", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--case-dir", type=Path)
    parser.add_argument("--use-source-case-path", action="store_true",
                        help="Use each actual.case_identity.path as the new declaration; pin its current bytes")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--variant", default="repriced")
    parser.add_argument("--runtime-source-commit")
    parser.add_argument("--runtime-validation-status", choices=("candidate", "maintained"), default="candidate")
    parser.add_argument("--role", action="append")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--skip-references", action="store_true")
    parser.add_argument("--compare-timeout", type=float, default=120)
    parser.add_argument("--reference-timeout", type=float, default=180)
    parser.add_argument("--worker", choices=("program", "references"))
    parser.add_argument("--program-key")
    parser.add_argument("--worker-output", type=Path)
    args = parser.parse_args()
    if args.worker:
        args.actual = args.actual[0]
        worker(args)
    elif args.retry_references_from:
        if args.output_dir is None or args.actual or args.case or args.mapping or args.validate_only:
            parser.error("reference retry requires output-dir and the prior report only")
        retry_references(args)
    else:
        if not args.actual or args.output_dir is None or len(args.actual) > 1 and (args.case or args.mapping):
            parser.error("output-dir is required; explicit case/mapping accepts one actual input")
        reprice(args)


if __name__ == "__main__":
    main()
