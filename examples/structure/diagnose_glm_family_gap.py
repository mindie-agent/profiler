"""Explain saved GLM operator residuals without treating activity as body time.

[Role] Join retained observed histograms with completed physical-program receipts.
[Invariants] Strict and conditional reference residuals remain separate. Missing
  predictions remain null; family P50 never stands in for a partial cohort P50.
  Native names do not identify layers. No observed duration chooses a program.
[Timeouts & Locks] One bounded source receipt at a time; no workers or locks.
  Optional controls execute only finite generic declared matrix programs.
[Side-Effect Policy] Read retained JSON; write the requested diagnostic arm.
  Explicit matrix controls price declared work without reading raw captures.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys


LIMIT = 32 * 1024**2


def read(path):
    path = Path(path)
    if path.stat().st_size > LIMIT:
        raise ValueError("use_per_source_receipt_over_32_mib")
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}


def activity(histogram):
    return sum(ns * count for ns, count in histogram)


def saved_baseline(case, selected=None):
    actual = Path(case["actual_identity"]["path"])
    prefix = actual.with_name(actual.name.removesuffix(".actual.json"))
    if selected and selected["actual_identity"]["sha256"] != case["actual_identity"]["sha256"]:
        raise ValueError("baseline_actual_observation_partition_differs")
    comparison_path = Path(selected["comparison_identity"]["path"]) if selected else prefix.with_suffix(".comparison.json")
    mapping_path = Path(selected["mapping_identity"]["path"]) if selected else prefix.with_suffix(".mapping.json")
    comparison, mapping = read(comparison_path), read(mapping_path)
    source = case["source_identity"]
    for window in mapping["windows"]:
        if any(window["source_identity"].get(key) != source.get(key)
               for key in ("path", "sha256", "size_bytes")):
            raise ValueError("baseline_source_identity_differs")
    if comparison["graph_id"] != mapping["graph_id"]:
        raise ValueError("baseline_comparison_mapping_graph_differs")
    families = defaultdict(list)
    for window in comparison["windows"]:
        declared = {row["cohort_id"]: row for original in mapping["windows"] for row in original["cohorts"]}
        for cohort in window["cohorts"]:
            role = "|".join(mapping["conditional_role_by_cohort_id"][cohort["cohort_id"]])
            families[cohort["native_operator_type"], role].append(
                {**cohort, "retained_target_ids": declared[cohort["cohort_id"]]["target_ids"]})
    return families, {"comparison": identity(comparison_path), "mapping": identity(mapping_path)}


def compared_totals(cohorts):
    compared = [row for row in cohorts if row["status"] == "compared"]
    count = sum(row["observed"]["event_count"] for row in compared)
    observed_ns = sum(row["observed"]["complete_activity_sum_ns"] for row in compared)
    service_ms = sum(row["prediction"]["per_call_ms"] * row["observed"]["event_count"] for row in compared)
    return count, observed_ns, service_ms


def observation_key(cohorts):
    return sorted(json.dumps({"native": row["native_operator_type"], "contract": row["contract"],
        "targets": sorted(row["retained_target_ids"]), "observed": row["observed"]}, sort_keys=True)
        for row in cohorts if row["status"] == "compared")


def diagnose_case(case, baseline_case=None):
    actual_path = case["actual_identity"]["path"]
    if identity(actual_path)["sha256"] != case["actual_identity"]["sha256"]:
        raise ValueError("actual_receipt_changed")
    actual = read(actual_path)
    source_families = {(row["native_operator_type"], row["declared_role"]): row for row in actual["families"]}
    baseline, baseline_identity = saved_baseline(case, baseline_case)
    if identity(case["mapping_identity"]["path"])["sha256"] != case["mapping_identity"]["sha256"]:
        raise ValueError("current_mapping_receipt_changed")
    current_mapping = read(case["mapping_identity"]["path"])
    current_targets = {row["cohort_id"]: row["target_ids"] for window in current_mapping["windows"] for row in window["cohorts"]}
    forwards = case["forward_count"]
    rows, references = [], []
    for family in case["families"]:
        key = family["native_operator_type"], family["declared_role"]
        measured = source_families[key]
        ns = activity(measured["duration_ns_counter"])
        count = measured["observed_us"]["count"]
        strict_count, strict_ns, service_ms = compared_totals(family["cohorts"])
        if strict_count > count or strict_ns > ns:
            raise ValueError("strict_population_exceeds_saved_family")
        old_count, old_ns, old_service_ms = compared_totals(baseline.get(key, []))
        current = [{**row, "retained_target_ids": current_targets[row["cohort_id"]]} for row in family["cohorts"]]
        equivalent = (strict_count > 0 and old_count == strict_count and old_ns == strict_ns
                      and observation_key(baseline.get(key, [])) == observation_key(current))
        strict_cohorts = [row for row in family["cohorts"] if row["status"] == "compared"]
        strict_p50 = (measured["observed_us"]["p50"] if strict_count == count else
                      strict_cohorts[0]["observed"]["duration_ns"]["p50"] / 1000
                      if len(strict_cohorts) == 1 else None)
        rows.append({"native_operator_type": key[0], "declared_role": key[1],
            "evidence_level": "strict_tensor_cohort" if strict_count else "no_strict_prediction",
            "all_calls": count, "calls_per_forward": count / forwards,
            "actual_mean_us": ns / count / 1000, "actual_p50_us": measured["observed_us"]["p50"],
            "actual_p50_population": "all_saved_native_family_calls",
            "measured_activity_ms_per_forward": ns / 1e6 / forwards,
            "strict_calls": strict_count, "strict_calls_per_forward": strict_count / forwards,
            "strict_observed_mean_us": strict_ns / strict_count / 1000 if strict_count else None,
            "strict_observed_p50_us": strict_p50,
            "strict_p50_population": ("all_saved_native_family_calls" if strict_count == count else
                "one_exact_retained_cohort" if len(strict_cohorts) == 1 else "pooled_strict_partition_not_retained"),
            "predicted_strict_mean_us": service_ms * 1000 / strict_count if strict_count else None,
            "predicted_strict_service_ms_per_forward": service_ms / forwards if strict_count else None,
            "strict_activity_error_ms_per_forward": (service_ms - strict_ns / 1e6) / forwards if strict_count else None,
            "strict_passed": family["passed_cohort_count"], "strict_compared": family["compared_cohort_count"],
            "unscored_calls": count - strict_count,
            "unscored_calls_per_forward": (count - strict_count) / forwards,
            "unscored_mean_us": (ns - strict_ns) / (count - strict_count) / 1000 if count > strict_count else None,
            "unscored_p50_us": measured["observed_us"]["p50"] if not strict_count else None,
            "unscored_activity_ms_per_forward": (ns - strict_ns) / 1e6 / forwards,
            "baseline_observation_partition_identical": equivalent,
            "baseline_strict_mean_us": old_service_ms * 1000 / old_count if equivalent else None,
            "cost_change_ms_per_forward": (service_ms - old_service_ms) / forwards if equivalent else None,
            "semantic_regions": sorted({(group.get("attention_kind"), group.get("block"))
                                         for group in measured.get("structure_groups", [])}, key=str),
            "saved_contract_sample_kinds": sorted({str(example["contract"][0]) if example.get("contract") else "contract_unresolved"
                for example in measured.get("examples", [])}),
            "retained_native_abi_group_calls": sum(group["observed_us"]["count"]
                for group in actual.get("source_role_references", [])
                if (group["native_operator_type"], group["declared_role"]) == key
                and group.get("source_correspondence", {}).get("observed_native_tensor_contract")),
            "cohort_reasons": family.get("cohort_reasons", {}),
            "rebind_exclusions": family.get("current_rebind_exclusions", []),
            "source_reference_exclusions": family.get("current_source_reference_exclusions", []),
            "body_critical_path_attribution": False})
        groups = family.get("conditional_source_role_references", [])
        for cohort in family["cohorts"]:
            if cohort["status"] != "reference_only" or not cohort.get("prediction"):
                continue
            observed = cohort["observed"]
            group_count = observed["complete_event_count"]
            group_ns = observed["complete_activity_sum_ns"]
            prediction = cohort["prediction"]["per_call_ms"] * 1000
            references.append({"native_operator_type": key[0], "declared_role": key[1],
                "evidence_level": "conditional_cohort_program_reference", "cohort_id": cohort["cohort_id"],
                "all_calls": group_count, "calls_per_forward": group_count / forwards,
                "actual_mean_us": group_ns / group_count / 1000,
                "actual_p50_us": observed["duration_ns"]["p50"] / 1000,
                "actual_p50_population": "complete_calls_in_exact_saved_reference_cohort",
                "measured_activity_ms_per_forward": group_ns / 1e6 / forwards,
                "predicted_reference_mean_us": prediction,
                "predicted_reference_service_ms_per_forward": prediction * group_count / 1000 / forwards,
                "reference_activity_error_ms_per_forward": (prediction * group_count / 1000 - group_ns / 1e6) / forwards,
                "conditions": [cohort.get("reason"), cohort["contract_scope"]],
                "reference_boundary": cohort["prediction"].get("boundary"),
                "strict_accuracy_implied": False, "body_critical_path_attribution": False})
        for group in groups:
            group_count = group["observed_us"]["count"]
            group_ns = group["observed_activity_sum_ns"]
            prediction = group.get("predicted_reference_us")
            references.append({"native_operator_type": key[0], "declared_role": key[1],
                "evidence_level": "conditional_source_program_reference", "group_id": group["group_id"],
                "all_calls": group_count, "calls_per_forward": group_count / forwards,
                "actual_mean_us": group["observed_us"]["mean"], "actual_p50_us": group["observed_us"]["p50"],
                "actual_p50_population": "exact_saved_source_reference_partition",
                "measured_activity_ms_per_forward": group_ns / 1e6 / forwards,
                "predicted_reference_mean_us": prediction,
                "predicted_reference_service_ms_per_forward": prediction * group_count / 1000 / forwards if prediction is not None else None,
                "reference_activity_error_ms_per_forward": (prediction * group_count / 1000 - group_ns / 1e6) / forwards if prediction is not None else None,
                "conditions": group.get("conditions", []), "source_correspondence": group.get("source_correspondence"),
                "strict_accuracy_implied": False, "body_critical_path_attribution": False})
        direct = family.get("conditional_program_reference", {})
        if not groups and direct.get("per_call_ms") is not None:
            prediction = direct["per_call_ms"] * 1000
            references.append({"native_operator_type": key[0], "declared_role": key[1],
                "evidence_level": "conditional_program_reference", "all_calls": count,
                "calls_per_forward": count / forwards, "actual_mean_us": ns / count / 1000,
                "actual_p50_us": measured["observed_us"]["p50"],
                "actual_p50_population": "all_saved_native_family_calls",
                "measured_activity_ms_per_forward": ns / 1e6 / forwards,
                "predicted_reference_mean_us": prediction,
                "predicted_reference_service_ms_per_forward": direct["per_call_ms"] * count / forwards,
                "reference_activity_error_ms_per_forward": (direct["per_call_ms"] * count - ns / 1e6) / forwards,
                "conditions": [direct.get("reason")], "strict_accuracy_implied": False,
                "body_critical_path_attribution": False})
    return {"case_id": case["case_id"], "source_case_id": case["source_case_id"],
        "actual_identity": case["actual_identity"], "source_identity": case["source_identity"],
        "case_identity": case["case_identity"], "comparison_identity": case["comparison_identity"],
        "baseline_identity": baseline_identity, "geometry": case["geometry"],
        "declared_execution": {key: current_mapping["declared_execution"][key]
            for key in ("phase", "tokens", "context", "sequences", "scope")},
        "forward_count": forwards, "source_forward_count": case["source_forward_count"],
        "families": rows, "conditional_references": references}


def top(rows, key, count=3):
    return sorted((row for row in rows if row.get(key) is not None),
                  key=lambda row: abs(row[key]), reverse=True)[:count]


def matrix_candidate_controls(case_path, geometry):
    """Price identical declared generic matrices with only underfilled changed."""
    from dataclasses import asdict, replace
    import mindie_sim
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.body_defaults import effective_body_declaration
    from mindie_sim.prediction.operator_analysis import target_graphs, physical_signature
    from mindie_sim.prediction.graph_analysis import graph_costs
    from mindie_sim.prediction.program import RecipeBook
    from mindie_sim.prediction.matrix_steady import SteadyMatmul
    from mindie_sim.prediction.matrix_mapping import UNDERFILLED_CANDIDATES

    sim_root = Path(mindie_sim.__file__).resolve().parent
    paths = sorted(sim_root.rglob("*.py")) + sorted((sim_root / "backends/profiles").glob("*.json"))
    runtime = {str(path): identity(path)["sha256"] for path in paths}
    case_pin = identity(case_path)
    case, _ = effective_body_declaration(parse_case(read(case_path)), "decode",
        tokens=geometry["tokens"], scope="body")
    book = RecipeBook.from_mapping(case.runtime.kernels)
    graphs = target_graphs(case, **geometry)
    rows, seen, excluded = [], set(), []
    for op in book.expand(graphs[min(graphs)]):
        if dict(op.metadata).get("program_kind") != "matmul":
            continue
        signature = json.dumps(physical_signature(op), sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        recipe = book.select(op)
        if not isinstance(recipe, SteadyMatmul):
            excluded.append({"recipe": op.recipe, "program": type(recipe).__name__,
                             "reason": "source_or_adapted_program_not_generic_steady_matmul"})
            continue
        arms = {}
        for label, selected in (("runtime_default", recipe),
                ("underfilled_disabled", replace(recipe, underfilled_candidates=())),
                ("underfilled_explicit", replace(recipe, underfilled_candidates=UNDERFILLED_CANDIDATES))):
            arm = RecipeBook(recipes={**book.recipes, op.recipe: selected}, families=book.families,
                             programs=book.programs, default=book.default)
            result = graph_costs(case, (op,), recipes=arm,
                external_inputs={dep: 0 for dep in op.deps}, include_submission=False, isolated=False)
            mapping = result["parameters"]["matrix_mappings"]
            if len(mapping) != 1:
                raise ValueError("generic_matrix_control_must_have_one_mapping")
            arms[label] = {"predicted_us": result["duration_ms"] * 1000,
                "selected_mapping": mapping[0]["selected"],
                "underfilled_grid_candidates": mapping[0]["underfilled_grid_candidates"],
                "serviced": result["execution"]["serviced"]}
        rows.append({"representative_operator_id": op.op_id, "recipe": op.recipe,
            "shape": list(op.local_shape), "compute_format": dict(op.metadata).get("compute_format", op.dtype),
            "operator": op.to_dict(), "original_recipe": asdict(recipe), "arms": arms,
            "only_changed_field": "underfilled_candidates", "narrow_candidates_unchanged": True,
            "observed_duration_used_for_selection": False,
            "native_occurrence_binding_implied": False})
    if identity(case_path) != case_pin or runtime != {str(path): identity(path)["sha256"] for path in paths}:
        raise ValueError("matrix_control_runtime_or_case_changed")
    return {"case_identity": case_pin, "geometry": geometry, "runtime_source_identity": runtime,
            "rows": rows, "excluded_programs": excluded,
            "scope": "same_runtime_same_declared_operator_only_underfilled_candidate_domain_changes",
            "body_accuracy_implied": False}


def render(report):
    lines = ["# GLM family / role activity residuals", "",
        "These are completed-program comparisons against unchanged saved observations. Activity residuals are not additive body wall-time attribution.",
        "Strict, conditional reference and missing-prediction populations remain separate. P50 is identified by its exact population; a whole-family P50 does not describe a scored subset.",
        f"Saved comparison runtime arm: `{report['runtime_source_commit']}`. Raw capture reads: 0; separate declared-program control executions: {report['prediction_executions']}.", ""]
    for case in report["cases"]:
        lines += ["## " + case["source_case_id"], "", f"Selected Forward: {case['forward_count']} / {case['source_forward_count']}; observed geometry: `{json.dumps(case['geometry'], sort_keys=True)}`.",
            f"Declared conditional execution: `{json.dumps(case.get('declared_execution'), sort_keys=True)}`. Declared context is not observed active KV length.", ""]
        for title, rows, key, pred in (
            ("Strict residual Top 3", case["families"], "strict_activity_error_ms_per_forward", "predicted_strict_mean_us"),
            ("Conditional reference residual Top 3", case["conditional_references"], "reference_activity_error_ms_per_forward", "predicted_reference_mean_us"),
            ("Unscored activity Top 3 — exposure, not prediction error", case["families"], "unscored_activity_ms_per_forward", None)):
            chosen = top(rows, key)
            lines += ["### " + title, "", "| Native / declared role | Calls/F | Real mean / P50 us | Sim/ref us | Activity / error ms/F | Evidence |",
                      "| --- | ---: | ---: | ---: | ---: | --- |"]
            for row in chosen:
                predicted = row.get(pred) if pred else None
                predicted_text = f"{predicted:.6f}" if predicted is not None else "—"
                if key.startswith("strict_"):
                    calls, mean, p50 = row["strict_calls_per_forward"], row["strict_observed_mean_us"], row["strict_observed_p50_us"]
                elif pred is None:
                    calls, mean, p50 = row["unscored_calls_per_forward"], row["unscored_mean_us"], row["unscored_p50_us"]
                else:
                    calls, mean, p50 = row["calls_per_forward"], row["actual_mean_us"], row["actual_p50_us"]
                observed_text = " / ".join(f"{value:.6f}" if value is not None else "—" for value in (mean, p50))
                lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {calls:.3f} | {observed_text} | {predicted_text} | {row[key]:+.6f} | {row['evidence_level']} |")
            lines.append("")
    lines += ["## Saved owner-candidate controls", "", "The following same-runtime, same-operator controls isolate the historical 83f720ae owner-candidate change. A later whole-runtime delta must not be attributed solely to this change.", "",
        "| Source / shape | Original us | Owner candidates us | Original tile | Selected tile |", "| --- | ---: | ---: | --- | --- |"]
    for row in report.get("owner_controls", []):
        lines.append(f"| {Path(row['case']['path']).name} / {row['shape']} | {row['original_us']:.6f} | {row['owner_candidates_us']:.6f} | {row['original_tile']} | {row['selected_tile']} |")
    if report.get("matrix_candidate_controls"):
        lines += ["", "## Same-runtime underfilled-only controls", "",
            f"Control runtime: `{report['matrix_candidate_controls'].get('runtime_source_commit', 'see exact source hashes')}`; kept separate from the saved comparison arm above.", "",
            "All three arms share each exact declared operator and runtime. Only `underfilled_candidates` changes; narrow candidates and dtype stay fixed. These controls do not bind a native invocation or predict a body critical path.", "",
            "| Declared recipe / shape / compute | Default us | Disabled us | Explicit underfilled us |",
            "| --- | ---: | ---: | ---: |"]
        displayed = set()
        for row in report["matrix_candidate_controls"]["rows"]:
            arms = row["arms"]
            key = json.dumps((row["recipe"], row["shape"], row["compute_format"], arms), sort_keys=True)
            if key in displayed:
                continue
            displayed.add(key)
            lines.append(f"| {row['recipe']} / {row['shape']} / {row['compute_format']} | {arms['runtime_default']['predicted_us']:.6f} | {arms['underfilled_disabled']['predicted_us']:.6f} | {arms['underfilled_explicit']['predicted_us']:.6f} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--baseline-report", type=Path)
    parser.add_argument("--owner-controls", type=Path)
    parser.add_argument("--matrix-control-case", type=Path)
    parser.add_argument("--matrix-control-source")
    parser.add_argument("--matrix-control-runtime")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source, pin = read(args.report), identity(args.report)
    baseline = read(args.baseline_report) if args.baseline_report else None
    baseline_cases = {case["source_case_id"]: case for case in baseline["cases"]} if baseline else {}
    report = {"schema_version": "mindie-glm-family-gap/1", "source_report": pin,
        "runtime_source_commit": source.get("runtime_source_commit"),
        "runtime_source_identity": source.get("runtime_source_identity"),
        "cases": [diagnose_case(case, baseline_cases[case["source_case_id"]] if baseline else None) for case in source["cases"]], "raw_capture_reads": 0,
        "prediction_executions": 0, "body_critical_path_attribution": False,
        "residual_metric": "predicted_program_service_minus_measured_kernel_activity_per_selected_forward"}
    if baseline:
        report["baseline_report_identity"] = identity(args.baseline_report)
        report["baseline_runtime_source_commit"] = baseline.get("runtime_source_commit")
    if args.owner_controls:
        controls = read(args.owner_controls)
        report["owner_control_identity"] = identity(args.owner_controls)
        report["owner_controls"] = [{"case": row["case"], "shape": row["contract"][1],
            "original_us": row["arms"]["original"]["predicted_per_call_us"],
            "owner_candidates_us": row["arms"]["owner_candidates"]["predicted_per_call_us"],
            "original_tile": row["arms"]["original"]["mapping"]["selected"],
            "selected_tile": row["arms"]["owner_candidates"]["mapping"]["selected"]} for row in controls["rows"]]
    if args.matrix_control_case:
        selected = next(case for case in source["cases"] if case["source_case_id"] == args.matrix_control_source)
        mapping = read(selected["mapping_identity"]["path"])
        geometry = {key: mapping["declared_execution"][key] for key in ("phase", "tokens", "context", "sequences", "scope")}
        report["matrix_candidate_controls"] = matrix_candidate_controls(args.matrix_control_case, geometry)
        report["matrix_candidate_controls"]["runtime_source_commit"] = args.matrix_control_runtime
        report["prediction_executions"] = 3 * len(report["matrix_candidate_controls"]["rows"])
    if identity(args.report) != pin:
        raise ValueError("source_report_changed_during_diagnostic")
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["maximum_resident_set_size_bytes"] = rss if sys.platform == "darwin" else rss * 1024
    if report["maximum_resident_set_size_bytes"] > 512 * 1024**2:
        raise RuntimeError("diagnostic_exceeds_512_mib")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix(".json").write_text(json.dumps(report, separators=(",", ":"), allow_nan=False) + "\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps({"cases": len(report["cases"]), "output": str(args.output), "rss_bytes": report["maximum_resident_set_size_bytes"]}))


if __name__ == "__main__":
    main()
