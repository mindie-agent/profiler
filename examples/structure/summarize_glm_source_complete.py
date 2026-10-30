"""Report remaining GLM service residuals on exact retained populations.

[Role] Rank direct contract cohorts separately from complete native references.
[Invariants] P50 stays attached to its original group; activity is not Body wall
  time. Unknown native state/routing values never become strict accuracy claims.
[Timeouts & Locks] Sequential compact JSON reads; no locks or workers.
[Side-Effect Policy] Read existing results and write one local JSON/Markdown pair.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from replay_body_operator_families import identity, read, write
from reprice_body_operator_families import sim_sources


def summarize(directory):
    family_path = directory / "body-operator-family-scoreboard.json"
    native_path = directory / "glm-native-reference-scoreboard.json"
    families, native = read(family_path), read(native_path)
    if sim_sources(families["runtime_source_identity"]) != sim_sources(native["runtime_source_identity"]):
        raise ValueError("strict_and_native_runtime_differ")
    by_source = {c["case_id"]: c for c in native["cases"]}
    results = []
    for case in families["cases"]:
        observed = by_source[case["source_case_id"]]
        if (case["source_identity"] != observed["source_identity"]
                or case["forward_count"] != observed["forward_count"]
                or case["geometry"] != observed["geometry"]
                or case["case_identity"]["sha256"] != observed["case_identity"]["sha256"]
                or case["declaration_refresh"]["declared_execution"]["context"] != observed["conditional_context_tokens"]):
            raise ValueError("strict_and_native_population_or_declaration_differ")
        count = case["forward_count"]
        strict, refs, subgraph_refs = [], [], []
        for family in case["families"]:
            for cohort in family["cohorts"]:
                if cohort["status"] not in {"compared", "reference_only"}:
                    continue
                calls = cohort["observed"]["complete_event_count"]
                mean, pred = cohort["observed_per_call_us"], cohort["predicted_per_call_us"]
                row = {"native_operator_type": family["native_operator_type"],
                    "declared_role": family["declared_role"], "group_id": cohort["cohort_id"],
                    "evidence_level": "direct_tensor_contract_cohort", "calls": calls,
                    "calls_per_forward": calls/count, "observed_mean_us": mean,
                    "observed_p50_us": cohort["observed"]["duration_ns"]["p50"]/1000,
                    "predicted_us": pred, "observed_activity_ms_per_forward": mean*calls/count/1000,
                    "predicted_service_ms_per_forward": pred*calls/count/1000,
                    "activity_residual_ms_per_forward": (pred-mean)*calls/count/1000,
                    "accuracy_pass": cohort["accuracy_pass"], "accuracy_tier": cohort["accuracy_tier"],
                    "contract_scope": cohort["contract_scope"], "occurrence_binding_implied": False}
                if cohort["status"] == "compared":
                    strict.append(row)
                else:
                    row.update(evidence_level="conditional_declared_subgraph_reference",
                        boundary=cohort["prediction"]["boundary"], reason=cohort["reason"],
                        strict_accuracy_implied=False, additional_budget_allowed=False)
                    subgraph_refs.append(row)
        for group in observed["groups"]:
            refs.append({"native_operator_type": group["native_operator_type"],
                "declared_role": group["declared_role"], "group_id": group["group_id"],
                "layer_ids": group["layer_ids"], "evidence_level": "conditional_complete_native_reference",
                "calls": group["observed_us"]["count"], "calls_per_forward": group["calls_per_forward"],
                "observed_mean_us": group["observed_us"]["mean"], "observed_p50_us": group["observed_us"]["p50"],
                "predicted_us": group["predicted_reference_us"],
                "observed_activity_ms_per_forward": group["observed_activity_ms_per_forward"],
                "predicted_service_ms_per_forward": group["predicted_service_ms_per_forward"],
                "activity_residual_ms_per_forward": group["reference_activity_error_ms_per_forward"],
                "source_correspondence": group["source_correspondence"],
                "strict_accuracy_implied": False, "additional_budget_allowed": False})
        descending = lambda row: -abs(row["activity_residual_ms_per_forward"])
        native_keys = {(r["native_operator_type"], r["declared_role"]) for r in refs}
        if any((r["native_operator_type"], r["declared_role"]) in native_keys for r in subgraph_refs):
            raise ValueError("native_and_subgraph_references_overlap_require_explicit_partition_selection")
        results.append({"source_case_id": case["source_case_id"], "source_identity": case["source_identity"],
            "case_identity": case["case_identity"], "geometry": case["geometry"], "forward_count": count,
            "conditional_context_tokens": observed["conditional_context_tokens"],
            "strict_passed": sum(r["accuracy_pass"] for r in strict), "strict_compared": len(strict),
            "strict_calls": sum(r["calls"] for r in strict),
            "top3_failing_direct_cohorts": sorted((r for r in strict if not r["accuracy_pass"]), key=descending)[:3],
            "top3_conditional_native_residuals": sorted(refs, key=descending)[:3],
            "top3_conditional_residuals": sorted(refs + subgraph_refs, key=descending)[:3],
            "all_direct_cohorts": strict, "all_conditional_native_references": refs,
            "all_conditional_subgraph_references": subgraph_refs,
            "unresolved_native_partitions": observed["unresolved"]})
    result = {"schema_version": "mindie-glm-source-complete-residuals/1", "cases": results,
        "family_receipt_identity": identity(family_path), "native_receipt_identity": identity(native_path),
        "runtime_source_commit": families["runtime_source_commit"], "raw_capture_reads": 0,
        "new_predictions": 0, "ranking": "descending_absolute_activity_residual_within_each_evidence_class",
        "population": {"sources": len(results), "forwards": sum(r["forward_count"] for r in results),
            "strict_passed": sum(r["strict_passed"] for r in results),
            "strict_compared": sum(r["strict_compared"] for r in results)},
        "limitations": ["Activity sums include overlapping streams and communication wait; residuals are not additive Body wall-time attribution.",
            "Native references preserve full ABI partitions and unknown dynamic values; none contributes to strict accuracy denominators.",
            "P50 belongs to each original cohort/partition; different layer groups are not averaged into one P50.",
            "Newly retained nine sources cover RecurrentKda only; the original nine A5 sources also retain fused-up and sparse attention."]}
    write(directory / "glm-source-complete-residuals.json", result)
    lines = ["# GLM remaining service residuals", "", f"Runtime `{result['runtime_source_commit']}`; {len(results)} sources, "
        f"{result['population']['forwards']} retained Forward instances. Zero raw scans or new predictions in this summary.", ""]
    for case in results:
        lines += ["## " + case["source_case_id"], "", f"Strict {case['strict_passed']}/{case['strict_compared']}; "
            f"{case['forward_count']} Forward; B={case['geometry']['sequences_per_replica']}, "
            f"q={case['geometry']['tokens_per_sequence']}, conditional context={case['conditional_context_tokens']}.", "",
            "| Evidence / native / role | Calls/F | Real Mean / P50 us | Predicted us | Activity / service / residual ms/F |",
            "| --- | ---: | ---: | ---: | ---: |"]
        for key in ("top3_failing_direct_cohorts", "top3_conditional_residuals"):
            for row in case[key]:
                label = ("direct, outside tolerance" if key.startswith("top3_failing") else
                         "conditional subgraph" if row["evidence_level"] == "conditional_declared_subgraph_reference"
                         else "conditional native")
                lines.append(f"| {label} / {row['native_operator_type']} / {row['declared_role']} | {row['calls_per_forward']:.3f} | "
                    f"{row['observed_mean_us']:.6f} / {row['observed_p50_us']:.6f} | {row['predicted_us']:.6f} | "
                    f"{row['observed_activity_ms_per_forward']:.6f} / {row['predicted_service_ms_per_forward']:.6f} / {row['activity_residual_ms_per_forward']:+.6f} |")
        lines.append("")
    lines += ["## Interpretation", "", *["- " + x for x in result["limitations"]], ""]
    (directory / "glm-source-complete-residuals.md").write_text("\n".join(lines))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(summarize(args.directory)["population"])
