"""Join explicit GLM mechanism arms without rerunning cost or observations.

[Role] Present focused expert-down cohorts beside full native-bucket references.
[Invariants] Partial expert-down reports cannot replace a full operator scoreboard.
  References remain conditional and unscored; activity residual is not Body error.
[Timeouts & Locks] Bounded sequential receipt reads, no locks or subprocesses.
[Side-Effect Policy] Read retained results and write a distinct summary and reference batch.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from compare_glm_native_partitions import render
from replay_body_operator_families import identity, read, write
from reprice_body_operator_families import sim_sources, render_repriced


def full_family(directory):
    """Join all-family source receipts, preserving unscored populations as well."""
    result, rows, inputs, elapsed = None, [], [], 0.0
    for label in ("a5-c64", "a5-c32", "a5-c1", "a3-c32", "a3-c64"):
        path = directory / ("full-family-" + label) / "body-operator-family-scoreboard.json"
        report = read(path)
        if report["status"] != "completed" or not report["runtime_sources_unchanged"]:
            raise ValueError("full_family_source_receipt_incomplete")
        if result is not None and report["runtime_source_identity"] != result["runtime_source_identity"]:
            raise ValueError("full_family_source_runtime_changed")
        if result is None:
            result = {key: value for key, value in report.items() if key != "cases"}
        rows.extend(report["cases"])
        inputs.append(identity(path))
        elapsed += report["elapsed_seconds"]
    result.update(cases=rows, elapsed_seconds=elapsed, input_receipts=inputs,
                  aggregation_only_no_new_predictions=True,
                  generator_identity=identity(Path(__file__)))
    write(directory / "body-operator-family-scoreboard.json", result)
    (directory / "body-operator-family-scoreboard.md").write_text(render_repriced(result))
    return result


def summarize(directory):
    manifest = read(directory / "source-mechanism-inputs.json")
    source_by_id = {case["source_case_id"]: case for case in manifest["cases"]}
    refs, focused, inputs, runtime = [], [], [], None
    for label in ("a5-c64", "a5-c32", "a5-c1", "a3-c32", "a3-c64"):
        reference_path = directory / (label + ("-packed" if label.startswith("a3") else "-native")) / "glm-native-reference-scoreboard.json"
        batch = read(reference_path)
        if batch["status"] != "completed":
            raise ValueError("source_reference_batch_incomplete")
        current = sim_sources(batch["runtime_source_identity"])
        if runtime is not None and current != runtime:
            raise ValueError("source_mechanism_runtime_mismatch")
        runtime = current
        inputs.append(identity(reference_path))
        for case in batch["cases"]:
            source = source_by_id[case["case_id"]]
            if (case["source_identity"] != source["source_identity"]
                    or case["geometry"] != source["geometry"]
                    or case["forward_count"] != source["forward_count"]
                    or case["case_identity"] != source["source_case_identity"]
                    or case["conditional_context_tokens"] != source["conditional_context_tokens"]):
                raise ValueError("source_reference_population_or_case_changed")
            refs.append(case)
        if label.startswith("a3"):
            continue
        path = directory / (label + "-down") / "body-operator-family-scoreboard.json"
        report = read(path)
        if sim_sources(report["runtime_source_identity"]) != runtime:
            raise ValueError("strict_and_reference_runtime_mismatch")
        inputs.append(identity(path))
        for case in report["cases"]:
            source = source_by_id[case["source_case_id"]]
            if case["source_identity"] != source["source_identity"] or case["geometry"] != source["geometry"]:
                raise ValueError("expert_down_population_changed")
            family = next(f for f in case["families"] if f["declared_role"] == "expert_down")
            for cohort in family["cohorts"]:
                if cohort["status"] != "compared":
                    raise ValueError("expert_down_cohort_incomplete")
                calls = cohort["observed"]["complete_event_count"]
                real, pred = cohort["observed_per_call_us"], cohort["predicted_per_call_us"]
                focused.append({"source_case_id": case["source_case_id"],
                    "source_identity": case["source_identity"], "geometry": case["geometry"],
                    "case_identity": case["case_identity"], "receipt_identity": identity(path),
                    "cohort_id": cohort["cohort_id"], "native_operator_type": family["native_operator_type"],
                    "declared_role": "expert_down", "forward_count": case["forward_count"],
                    "observed_calls": calls, "observed_mean_us": real,
                    "observed_p50_us": cohort["observed"]["duration_ns"]["p50"] / 1000,
                    "predicted_us": pred, "per_call_difference_us": pred-real,
                    "relative_error": pred/real-1, "accuracy_pass": cohort["accuracy_pass"],
                    "accuracy_tier": cohort["accuracy_tier"],
                    "calls_per_forward": calls/case["forward_count"],
                    "activity_residual_ms_per_forward": (pred-real)*calls/case["forward_count"]/1000,
                    "contract_scope": cohort["contract_scope"],
                    "whole_family_scoreboard_replacement_allowed": False})
    populations = {case["source_identity"]["sha256"]: case["forward_count"] for case in refs}
    summary = {"sources": len(populations), "complete_forwards": sum(populations.values()),
        "focused_expert_down_cohorts": len(focused),
        "focused_expert_down_passed": sum(row["accuracy_pass"] for row in focused),
        "focused_expert_down_calls": sum(row["observed_calls"] for row in focused),
        "reference_groups": sum(len(case["groups"]) for case in refs),
        "reference_calls": sum(case["referenced_event_count"] for case in refs),
        "reference_program_sets_executed": sum(case["execution"]["new_program_sets"] for case in refs),
        "reference_strict_compared": 0}
    reference_batch = {"schema_version": "mindie-native-body-reference-batch/1", "status": "completed",
        "runtime_source_commit": manifest["declared_runtime_source_commit"],
        "runtime_source_identity": batch["runtime_source_identity"],
        "runtime_sources_unchanged": all(case["runtime_sources_unchanged"] for case in refs),
        "cases": refs, "raw_capture_reads": 0, "strict_compared": 0,
        "input_receipts": inputs, "new_predictions_during_aggregation": 0}
    write(directory / "glm-source-native-reference-scoreboard.json", reference_batch)
    text = render(reference_batch)
    (directory / "glm-source-native-reference-scoreboard.md").write_text(text)
    result = {"schema_version": "mindie-glm-source-mechanism-summary/1",
        "status": "completed", "input_manifest_identity": identity(directory / "source-mechanism-inputs.json"),
        "runtime_source_commit": manifest["declared_runtime_source_commit"], "inputs": inputs,
        "summary": summary, "focused_expert_down": focused,
        "reference_batch_identity": identity(directory / "glm-source-native-reference-scoreboard.json"),
        "limitations": ["Focused expert_down results must not replace any full-family operator receipt.",
            "Reference activity residuals overlap and cannot be added as Body wall-clock error.",
            "Per-expert row counts, active sparse lengths and private source dispatch remain conditional."]}
    write(directory / "source-mechanism-scoreboard.json", result)
    lines = ["# GLM explicit source mechanisms", "", f"Runtime `{result['runtime_source_commit']}`. "
        f"{summary['sources']} retained sources / {summary['complete_forwards']} complete Forwards; no new capture.", "",
        "## Focused expert_down cohorts", "", "| Source | Calls/F | Real Mean / P50 us | Source us | Relative error | Activity residual ms/F | Tier / pass |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
    for row in focused:
        lines.append(f"| {row['source_case_id']} | {row['calls_per_forward']:.0f} | {row['observed_mean_us']:.6f} / {row['observed_p50_us']:.6f} | "
            f"{row['predicted_us']:.6f} | {row['relative_error']:.2%} | {row['activity_residual_ms_per_forward']:+.6f} | {row['accuracy_tier']} / {row['accuracy_pass']} |")
    lines += ["", "The active tensor contract is checked; group-list values and the actual native dispatch are not established. "
        "The c1 micro-call uses the 15 us absolute-error tolerance; larger calls use 15% relative error. "
        "These focused receipts do not replace the full-family scoreboard.", "", "## Complete native-bucket conditional references", "",
        f"{summary['reference_groups']} complete groups / {summary['reference_calls']} calls; all reference-only. "
        "Original group Mean/P50 and layer sets are retained. See [per-group table](glm-source-native-reference-scoreboard.md).", "",
        *["- " + line for line in result["limitations"]], ""]
    (directory / "source-mechanism-scoreboard.md").write_text("\n".join(lines))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--full-family", action="store_true",
                        help="Also join all five complete family receipts for canonical operator selection")
    args = parser.parse_args()
    print(summarize(args.directory)["summary"])
    if args.full_family:
        full_family(args.directory)
