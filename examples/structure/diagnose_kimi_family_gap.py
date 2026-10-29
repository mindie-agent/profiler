"""Compare retained Kimi family populations without attributing activity to wall time.

[Role] Rank remaining measured family/role gaps across explicit cost generations.
[Invariants] Exact histograms and source/geometry must survive each join. Strict
  cohorts, conditional source references, and unpriced activity stay separate.
  A cross-runtime difference is descriptive; it never isolates a tile change.
[Timeouts & Locks] One source detail at a time, no locks and no raw capture scan.
[Side-Effect Policy] Read retained receipts; write only the requested diagnostic.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

import ijson


PREFIX = "a5_kimi_tp8_e16_bf16_"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identity(path):
    path = Path(path).resolve()
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}


def metadata(path, field):
    with Path(path).open("rb") as stream:
        return next(ijson.items(stream, field, use_float=True), None)


def rows(path):
    with Path(path).open("rb") as stream:
        yield from ijson.items(stream, "cases.item", use_float=True)


def detail(row):
    pin = row.get("case_detail_identity")
    if not pin:
        return row
    actual = identity(pin["path"])
    if any(actual[key] != pin[key] for key in ("path", "sha256", "size_bytes")):
        raise ValueError("case_detail_identity_changed")
    selected = list(rows(pin["path"]))
    if len(selected) != 1 or selected[0]["source_case_id"] != row["source_case_id"]:
        raise ValueError("case_detail_population_changed")
    return selected[0]


def family_key(row):
    return row["native_operator_type"], row["declared_role"]


def family_summary(family, forwards):
    histogram = sorted((int(ns), int(count)) for ns, count in family["duration_ns_counter"])
    count = sum(count for _, count in histogram)
    activity_ns = sum(ns * count for ns, count in histogram)
    if count != family["observed_us"]["count"]:
        raise ValueError("histogram_count_differs")
    compared = [c for c in family.get("cohorts", ()) if c["status"] == "compared"]
    scored = sum(c["observed"]["event_count"] for c in compared)
    scored_ns = sum(c["observed"]["complete_activity_sum_ns"] for c in compared)
    predicted_ms = sum(c["prediction"]["per_call_ms"] * c["observed"]["event_count"] for c in compared)
    if scored != family["scored_event_count"] or scored > count or scored_ns > activity_ns:
        raise ValueError("strict_population_differs")
    strict = None
    if scored:
        strict = {"event_count": scored, "cohort_count": len(compared),
            "observed_us_per_call": scored_ns / scored / 1000,
            "predicted_us_per_call": predicted_ms * 1000 / scored,
            "observed_activity_ms_per_forward": scored_ns / 1e6 / forwards,
            "predicted_activity_ms_per_forward": predicted_ms / forwards,
            "underprediction_activity_ms_per_forward": (scored_ns / 1e6 - predicted_ms) / forwards,
            "whole_family_covered": scored == count,
            "cohorts": [{"cohort_id": c["cohort_id"], "physical_signature": c["physical_signature"],
                "contract": c["contract"], "representative_target_id": c["prediction"]["representative_target_id"],
                "event_count": c["observed"]["event_count"],
                "observed_activity_sum_ns": c["observed"]["complete_activity_sum_ns"],
                "predicted_per_call_us": c["prediction"]["per_call_ms"] * 1000}
                for c in compared]}
    references = []
    for group in family.get("conditional_source_role_references", ()):
        references.append({key: group.get(key) for key in (
            "group_id", "observed_us", "predicted_reference_us", "observed_activity_ms_per_forward",
            "predicted_service_ms_per_forward", "boundary", "evidence_strength", "status",
            "declared_role", "native_operator_type", "target_count")})
    reference_count = sum(g["observed_us"]["count"] for g in references)
    if reference_count + scored > count:
        raise ValueError("reference_population_overlaps_strict_or_exceeds_family")
    return {"native_operator_type": family["native_operator_type"], "declared_role": family["declared_role"],
        "event_count": count, "histogram_sha256": sha256(canonical(histogram).encode()).hexdigest(),
        "observed_us": family["observed_us"], "observed_activity_ms_per_forward": activity_ns / 1e6 / forwards,
        "strict": strict, "unscored_event_count": count - scored,
        "unscored_activity_ms_per_forward": (activity_ns - scored_ns) / 1e6 / forwards,
        "conditional_source_references": references,
        "conditional_reference_event_count": reference_count,
        "conditional_reference_underprediction_activity_ms_per_forward": sum(
            g["observed_activity_ms_per_forward"] - g["predicted_service_ms_per_forward"]
            for g in references if g["predicted_service_ms_per_forward"] is not None),
        "reference_exclusions": family.get("current_source_reference_exclusions", []),
        "classification_basis": family.get("role_basis"),
        "whole_family_error_available": scored == count}


def summarize_case(row):
    return {key: row.get(key) for key in ("source_case_id", "source_identity", "case_identity",
        "actual_identity", "mapping_identity", "comparison_identity", "geometry", "forward_count",
        "source_forward_count")} | {"families": [family_summary(f, row["forward_count"]) for f in row["families"]]}


def load_arm(path):
    selected = {}
    for row in rows(path):
        if not row["source_case_id"].startswith(PREFIX):
            continue
        row = detail(row)
        if row["source_case_id"] in selected:
            raise ValueError("duplicate_source_case")
        selected[row["source_case_id"]] = summarize_case(row)
    runtime = metadata(path, "runtime_source_identity")
    return {"input_identity": identity(path), "runtime_source_commit": metadata(path, "runtime_source_commit"),
        "runtime_file_map_sha256": sha256(canonical(runtime).encode()).hexdigest(), "cases": selected}


def load_bodies(path):
    result = {}
    if path is None:
        return result
    for row in rows(path):
        case_id = row.get("source_case_id", row.get("case_id", "").split(":")[0])
        if not case_id.startswith(PREFIX) or row.get("status") != "compared":
            continue
        key = case_id, row["geometry"]["sequences_per_replica"], row["geometry"]["tokens_per_sequence"]
        if key in result:
            raise ValueError("duplicate_body_geometry")
        result[key] = {"case_id": row["case_id"], "source_identity": row["source_identity"],
            "geometry": row["geometry"], "runtime_identity": row["runtime_identity"],
            "comparison": row["comparison"], "model_structure_identity": row.get("model_structure_identity")}
    return result


def ranked(families, value, limit=3):
    return sorted(families, key=value, reverse=True)[:limit]


def diagnose(args):
    start = time.perf_counter()
    prior, current = load_arm(args.previous), load_arm(args.current)
    if set(prior["cases"]) != set(current["cases"]):
        raise ValueError("cost_arms_source_sets_differ")
    old_bodies, new_bodies = load_bodies(args.body_previous), load_bodies(args.body_current)
    results, pooled = [], defaultdict(lambda: {"event_count": 0, "scored_event_count": 0,
        "observed_activity_ms": 0., "strict_observed_activity_ms": 0., "strict_predicted_activity_ms": 0.,
        "unscored_activity_ms": 0., "case_count": 0, "reference_event_count": 0,
        "reference_underprediction_activity_ms": 0.})
    total_forwards = sum(c["forward_count"] for c in current["cases"].values())
    for case_id, new in current["cases"].items():
        old = prior["cases"][case_id]
        for key in ("source_identity", "geometry", "forward_count", "actual_identity"):
            if canonical(old[key]) != canonical(new[key]):
                raise ValueError("observation_join_differs:" + key)
        old_families = {family_key(f): f for f in old["families"]}
        for family in new["families"]:
            previous = old_families[family_key(family)]
            if family["histogram_sha256"] != previous["histogram_sha256"]:
                raise ValueError("observed_histogram_changed")
            same_partition = family["strict"] is not None and previous["strict"] is not None
            if same_partition:
                def partitions(f):
                    return sorted((canonical(c["contract"]), c["representative_target_id"],
                                   c["event_count"], c["observed_activity_sum_ns"]) for c in f["strict"]["cohorts"])
                same_partition = partitions(family) == partitions(previous)
            family["previous_strict_same_observation_partition"] = same_partition
            family["strict_cost_change_ms_per_forward"] = (
                family["strict"]["predicted_activity_ms_per_forward"] - previous["strict"]["predicted_activity_ms_per_forward"]
                if same_partition else None)
            item = pooled[family_key(family)]; n = new["forward_count"]
            item["event_count"] += family["event_count"]; item["case_count"] += 1
            item["observed_activity_ms"] += family["observed_activity_ms_per_forward"] * n
            item["unscored_activity_ms"] += family["unscored_activity_ms_per_forward"] * n
            item["reference_event_count"] += family["conditional_reference_event_count"]
            item["reference_underprediction_activity_ms"] += family["conditional_reference_underprediction_activity_ms_per_forward"] * n
            if family["strict"]:
                item["scored_event_count"] += family["strict"]["event_count"]
                item["strict_observed_activity_ms"] += family["strict"]["observed_activity_ms_per_forward"] * n
                item["strict_predicted_activity_ms"] += family["strict"]["predicted_activity_ms_per_forward"] * n
        strict = [f for f in new["families"] if f["strict"]]
        new["strict_top3_remaining_underprediction"] = [family_key(f) for f in ranked(strict,
            lambda f: f["strict"]["underprediction_activity_ms_per_forward"])]
        new["unscored_top3_activity"] = [family_key(f) for f in ranked(new["families"],
            lambda f: f["unscored_activity_ms_per_forward"])]
        new["conditional_reference_top3_underprediction"] = [family_key(f) for f in ranked(
            [f for f in new["families"] if f["conditional_reference_event_count"]],
            lambda f: f["conditional_reference_underprediction_activity_ms_per_forward"])]
        key = case_id, new["geometry"]["sequences_per_replica"], new["geometry"]["tokens_per_sequence"]
        if key in old_bodies and key in new_bodies:
            before, after = old_bodies[key], new_bodies[key]
            if (before["source_identity"]["sha256"] != new["source_identity"]["sha256"]
                or after["source_identity"]["sha256"] != new["source_identity"]["sha256"]
                or before["comparison"]["observed_ms"] != after["comparison"]["observed_ms"]):
                raise ValueError("body_observation_join_differs")
            new["body_cost_change"] = {"previous": before, "current": after,
                "predicted_ms_change": after["comparison"]["predicted_ms"] - before["comparison"]["predicted_ms"],
                "causality": "cross_runtime_and_case_change; not_a_matrix_only_ablation"}
        results.append(new)
    pool = []
    for (native, role), values in pooled.items():
        pool.append({"native_operator_type": native, "declared_role": role, **values,
            "strict_underprediction_activity_ms_per_forward": (
                values["strict_observed_activity_ms"] - values["strict_predicted_activity_ms"]) / total_forwards,
            "reference_underprediction_activity_ms_per_forward": values["reference_underprediction_activity_ms"] / total_forwards,
            "unscored_activity_ms_per_forward": values["unscored_activity_ms"] / total_forwards})
    costed = []
    for family in pool:
        for basis, count_key, residual_key in (
            ("strict_tensor_cohort_conditional_topology", "scored_event_count", "strict_underprediction_activity_ms_per_forward"),
            ("conditional_source_reference_not_strict", "reference_event_count", "reference_underprediction_activity_ms_per_forward")):
            if family[count_key]:
                costed.append({"native_operator_type": family["native_operator_type"],
                    "declared_role": family["declared_role"], "evidence_basis": basis,
                    "costed_event_count": family[count_key], "underprediction_activity_ms_per_forward": family[residual_key]})
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin": rss *= 1024
    if rss > 512 * 1024**2: raise MemoryError("analysis_exceeds_512MiB")
    return {"schema_version": "mindie-kimi-family-gap/1", "previous_arm": {k:v for k,v in prior.items() if k != "cases"},
        "current_arm": {k:v for k,v in current.items() if k != "cases"},
        "body_input_identities": [identity(p) for p in (args.body_previous,args.body_current) if p],
        "cases": results, "summary": {"sources": len(results), "selected_forwards": total_forwards,
            "pooled_basis": "sum_activity_divided_by_sum_selected_forwards; capture_population_weighted_not_universal_batch",
            "strict_top3_remaining_underprediction": ranked([f for f in pool if f["scored_event_count"]],
                lambda f: f["strict_underprediction_activity_ms_per_forward"]),
            "conditional_reference_top3_remaining_underprediction": ranked([f for f in pool if f["reference_event_count"]],
                lambda f: f["reference_underprediction_activity_ms_per_forward"]),
            "costed_activity_top3_with_explicit_evidence_tiers": ranked(costed,
                lambda f: f["underprediction_activity_ms_per_forward"]),
            "unscored_top3_activity": ranked(pool, lambda f: f["unscored_activity_ms_per_forward"])},
        "interpretation": ["Strict rows compare only their exact scored event subset; unscored is not zero cost.",
            "Source-reference groups remain conditional and are excluded from strict Top3.",
            "Activity differences overlap in time and cannot be added to explain Body wall-clock error.",
            "Cross-runtime changes do not isolate underfilled candidates; a same-runtime ablation is required."],
        "execution": {"raw_capture_reads": 0, "read_strategy": "ijson_cases_then_one_source_detail",
            "elapsed_seconds": time.perf_counter()-start, "maximum_resident_set_size_bytes": rss}}


def render(report):
    lines = ["# Kimi Family / Role Residuals", "", f"{report['summary']['sources']} sources; "
        f"{report['summary']['selected_forwards']} selected complete forwards. Exact saved duration histograms are unchanged.", "",
        "Activity residuals below are diagnostic device-service differences, not a decomposition of Body wall time.", "",
        "Largest costed activity gaps, keeping evidence tiers explicit (not an accuracy pass/fail ranking):", "",
        "| Family / role | Evidence tier | Activity deficit ms/forward |", "|---|---|---:|"]
    for row in report["summary"]["costed_activity_top3_with_explicit_evidence_tiers"]:
        lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['evidence_basis']} | {row['underprediction_activity_ms_per_forward']:.6f} |")
    lines += ["",
        "| Strict family / role | Scored calls | Unmodelled activity excluded | Residual ms/forward |",
        "|---|---:|---:|---:|"]
    for row in report["summary"]["strict_top3_remaining_underprediction"]:
        lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['scored_event_count']} | "
            f"{row['event_count']-row['scored_event_count']} calls | {row['strict_underprediction_activity_ms_per_forward']:.6f} |")
    lines += ["", "Conditional references (separate from strict accuracy; routed valid rows remain declared):", "",
              "| Family / role | Reference calls | Residual ms/forward |", "|---|---:|---:|"]
    for row in report["summary"]["conditional_reference_top3_remaining_underprediction"]:
        lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['reference_event_count']} | {row['reference_underprediction_activity_ms_per_forward']:.6f} |")
    lines += ["", "Outside strict coverage (may include the conditional references above; not a second additive budget):", "",
              "| Family / role | Unscored activity ms/forward |", "|---|---:|"]
    for row in report["summary"]["unscored_top3_activity"]:
        lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['unscored_activity_ms_per_forward']:.6f} |")
    lines += ["", "Per-source strict Top3 (underprediction activity ms/forward):", "",
              "| Case | First | Second | Third |", "|---|---|---|---|"]
    for case in report["cases"]:
        index = {family_key(f): f for f in case["families"]}
        cells = [f"{n}/{r}: {index[n,r]['strict']['underprediction_activity_ms_per_forward']:.4f}"
                 for n,r in case["strict_top3_remaining_underprediction"]]
        lines.append("| " + " | ".join([case["source_case_id"], *cells]) + " |")
    return "\n".join(lines + ["", *report["interpretation"], ""])


def ablate(args):
    """Explicit candidate domains isolate selection without changing work/precision."""
    from copy import deepcopy
    from mindie_sim import graph_costs, target_graphs
    from mindie_sim.prediction.matrix_mapping import NARROW_CANDIDATES, UNDERFILLED_CANDIDATES
    from mindie_sim.prediction.program import RecipeBook
    from compare_body_operator_families import prediction_runtime_identity

    before = prediction_runtime_identity()
    case_pin = identity(args.ablation_case)
    case = json.loads(args.ablation_case.read_text())
    geometry = dict(phase="decode", tokens=1, sequences=args.sequences, context=args.context, scope="body")
    graphs = target_graphs(case, **geometry)
    selected = {op.op_id: op for op in graphs[0] if op.op_id in args.ablation_op}
    if set(selected) != set(args.ablation_op):
        raise ValueError("ablation_operator_not_in_declared_graph")
    output = []
    for op_id, op in selected.items():
        arms = {}
        for name, overrides in (("current_default", {}),
                ("explicit_underfilled_only", {"underfilled_candidates": UNDERFILLED_CANDIDATES}),
                ("explicit_previous_full_subtiles", {"underfilled_candidates": UNDERFILLED_CANDIDATES,
                                                     "narrow_candidates": NARROW_CANDIDATES})):
            arm = deepcopy(case)
            arm["runtime"]["kernels"]["programs"]["matmul"].update(overrides)
            recipe = RecipeBook.from_mapping(arm["runtime"]["kernels"]).select(op)
            cost = graph_costs(arm, (op,), external_inputs={dep: 0 for dep in op.deps}, isolated=False)
            arms[name] = {"predicted_us": cost["duration_ms"] * 1000,
                "selected_recipe_class": type(recipe).__name__, "configuration_delta": overrides,
                "matrix_mappings": cost["parameters"].get("matrix_mappings", []),
                "physical_service": cost["execution"]["serviced"],
                "operator_identity_sha256": sha256(repr(op).encode()).hexdigest()}
        output.append({"op_id": op_id, "recipe": op.recipe, "family": op.family,
            "local_shape": list(op.local_shape), "metadata": dict(op.metadata), "arms": arms,
            "underfilled_only_effect_us": arms["explicit_underfilled_only"]["predicted_us"] - arms["current_default"]["predicted_us"],
            "additional_narrow_effect_us": arms["explicit_previous_full_subtiles"]["predicted_us"] - arms["explicit_underfilled_only"]["predicted_us"]})
    if prediction_runtime_identity() != before or identity(args.ablation_case) != case_pin:
        raise ValueError("ablation_inputs_changed")
    return {"schema_version": "mindie-kimi-matrix-domain-ablation/1", "case_identity": case_pin,
        "runtime_source_identity": before, "runtime_sources_unchanged": True, "geometry": geometry,
        "operators": output, "raw_capture_reads": 0,
        "interpretation": "Same runtime, identical declared operator and precision; only explicit candidate domains differ. Isolated service changes cannot be added as Body wall-clock changes."}


def reprice_context_matrices(args):
    """Change declared context explicitly while retaining only context-free matrices."""
    from copy import deepcopy
    from types import SimpleNamespace
    from compare_body_operator_families import family_rows, prediction_runtime_identity
    from reprice_body_operator_families import compare_programs, rebind_mapping, compact_case
    from reprice_body_operator_families import validate_observation_join, render_repriced
    from mindie_sim.structure import export_structure

    started = time.perf_counter(); before = prediction_runtime_identity()
    actual_path = args.context_rebind_actual.resolve(); actual = json.loads(actual_path.read_text())
    mapping_path = actual_path.with_name(actual_path.name.replace(".actual.", ".mapping."))
    original = json.loads(mapping_path.read_text()); validate_observation_join(actual, original)
    case_path = args.ablation_case.resolve(); case = json.loads(case_path.read_text())
    execution = original["declared_execution"]
    geometry = {k: execution[k] for k in ("phase", "tokens", "sequences", "scope")}
    geometry.update(context=args.context)
    for k in ("apply_body_defaults", "expand_calls"):
        if k in execution: geometry[k] = execution[k]
    manifest = export_structure(case, **geometry)
    selected = deepcopy(original); explicit_exclusions = []
    for window in selected["windows"]:
        retained = []
        for cohort in window["cohorts"]:
            if cohort["contract"][0] in {"matrix", "grouped_matrix"}:
                retained.append(cohort)
            else:
                explicit_exclusions.append({"old_cohort_id": cohort["cohort_id"],
                    "native_operator_type": cohort["native_operator_type"],
                    "declared_roles": original["conditional_role_by_cohort_id"][cohort["cohort_id"]],
                    "event_count": cohort["event_count"], "reason": "new_context_requires_independent_nonmatrix_evidence"})
        window["cohorts"] = retained
    rebound, plan = rebind_mapping(selected, manifest, actual["source_identity"])
    plan["excluded"].extend(explicit_exclusions)
    directory = args.output.parent; directory.mkdir(parents=True, exist_ok=True)
    prefix = directory / ("body-operator-" + actual["source_case_id"] + "-context32768-matrix-only")
    new_mapping = prefix.with_suffix(".mapping.json")
    new_mapping.write_text(json.dumps(rebound, separators=(",", ":")) + "\n")
    worker_args = SimpleNamespace(compare_timeout=180, reference_timeout=180, frozen_native_rebind=False)
    comparison = compare_programs(worker_args, prefix, actual_path, new_mapping, case_path, rebound)
    comparison_path = prefix.with_suffix(".comparison.json")
    comparison_path.write_text(json.dumps(comparison, separators=(",", ":")) + "\n")
    families = family_rows(actual, rebound, comparison, {})
    pins = {"actual_identity":identity(actual_path), "old_mapping_identity":identity(mapping_path),
        "case_identity":identity(case_path), "mapping_identity":identity(new_mapping),
        "comparison_identity":identity(comparison_path)}
    plan.update(**pins, case_id=actual["case_id"], fresh_graph_id=manifest["graph_id"],
        model_representation={k:manifest["model"].get(k) for k in ("quantization","quant","activation_dtype","weight_dtype","kv_dtype","compute_dtype")},
        observed_geometry=actual["geometry"], declared_execution=manifest["execution"],
        declared_context_change={"previous":execution["context"], "current":args.context,
            "basis":"explicit_representative_profiled_prompt; not_cache_capacity", "raw_observation_unchanged":True},
        raw_capture_reads=0, old_prediction_reused=False)
    row = {"case_id":actual["source_case_id"]+" / runtime86-context32768-matrix-only",
        "source_case_id":actual["source_case_id"], "variant":"runtime86-context32768-matrix-only", **pins,
        "source_identity":actual["source_identity"], "forward_count":actual["forward_count"],
        "source_forward_count":actual["source_forward_count"], "geometry":actual["geometry"],
        "conditional_context_tokens":args.context, "retained_actual_declared_context_tokens":actual["conditional_context_tokens"],
        "families":families, "passed_cohorts":sum(f["passed_cohort_count"] for f in families),
        "comparison_status_counts":comparison["status_counts"], "strict_prediction_reused_from":None,
        "reference_receipt":{"status":"not_requested","reason":"new_context_matrix_only_arm"},
        "reference_exclusions":[], "declaration_refresh":plan}
    if prediction_runtime_identity() != before: raise ValueError("context_reprice_runtime_changed")
    detail_path = prefix.with_suffix(".family-scoreboard.json")
    detail_path.write_text(json.dumps({"schema_version":"mindie-body-operator-comparison/1", "cases":[row],
        "runtime_source_identity":before, "raw_capture_reads":0, "old_prediction_reused":False},separators=(",", ":"))+"\n")
    result = {"schema_version":"mindie-body-operator-comparison/1", "status":"completed",
        "coverage_status":"partial", "cases":[{**compact_case(row),"case_detail_identity":identity(detail_path)}],
        "runtime_source_identity":before,"runtime_sources_unchanged":True,
        "runtime_source_commit":args.runtime_source_commit, "runtime_validation_status":"maintained",
        "raw_capture_reads":0, "old_prediction_reused":False, "elapsed_seconds":time.perf_counter()-started}
    if comparison["status_counts"].get("prediction_failed"): result["status"]="partial"
    args.output.write_text(json.dumps(result,indent=2)+"\n")
    args.output.with_suffix(".md").write_text(render_repriced(result))
    print(json.dumps({"status":result["status"],"comparison_status_counts":comparison["status_counts"],
        "passed_cohorts":row["passed_cohorts"],"excluded":len(plan["excluded"])}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--body-previous", type=Path)
    parser.add_argument("--body-current", type=Path)
    parser.add_argument("--ablation-case", type=Path)
    parser.add_argument("--context-rebind-actual", type=Path)
    parser.add_argument("--runtime-source-commit")
    parser.add_argument("--ablation-op", action="append", default=[])
    parser.add_argument("--sequences", type=int, default=32)
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.context_rebind_actual:
        if not args.ablation_case: parser.error("context rebind requires an explicit case")
        if not args.runtime_source_commit: parser.error("context rebind requires its committed runtime identity")
        reprice_context_matrices(args)
        return
    if not args.ablation_case and (not args.previous or not args.current):
        parser.error("provide previous/current receipts or an explicit ablation-case")
    report = ablate(args) if args.ablation_case else diagnose(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    if not args.ablation_case:
        args.output.with_suffix(".md").write_text(render(report))
        print(json.dumps(report["summary"], ensure_ascii=False))
    else:
        print(json.dumps([{k: row[k] for k in ("op_id", "underfilled_only_effect_us", "additional_narrow_effect_us")}
                          for row in report["operators"]]))


if __name__ == "__main__":
    main()
