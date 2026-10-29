"""Price existing Sim programs for complete retained GLM native ABI buckets.

[Role] Execute conditional full-batch or fused-semantic-subgraph references.
[Invariants] Fresh declarations supply all cost work; exact retained populations
  supply observations only. No partial sample is extrapolated or scored strict.
[Timeouts & Locks] Sequential source subprocesses, 180 s each, <=512 MiB RSS.
[Side-Effect Policy] Local retained JSON/case reads and separate result files only.
"""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from body_source_role_references import predict_source_role_references
from compare_body_operator_families import prediction_runtime_identity
from glm_native_references import prepare_references
from replay_body_operator_families import identity, read, write


def runtime_identity():
    value = prediction_runtime_identity()
    for name in ("glm_native_references.py", "compare_glm_native_partitions.py"):
        path = Path(__file__).with_name(name).resolve()
        value[str(path)] = identity(path)["sha256"]
    return value


def peak_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def worker(path, runtime_commit):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure

    started = time.perf_counter(); before = runtime_identity(); pin = identity(path)
    partitions = read(path)
    actual_pin, case_pin = partitions["actual_identity"], partitions["case_identity"]
    if identity(actual_pin["path"])["sha256"] != actual_pin["sha256"]:
        raise ValueError("retained_actual_changed")
    if identity(case_pin["path"])["sha256"] != case_pin["sha256"]:
        raise ValueError("source_bound_case_changed")
    actual = read(actual_pin["path"])
    if (actual["source_identity"] != partitions["source_identity"]
            or actual["forward_count"] != partitions["forward_count"]
            or actual["geometry"] != partitions["geometry"]):
        raise ValueError("partition_actual_population_changed")
    case = parse_case(read(case_pin["path"])); geo = partitions["geometry"]
    manifest = export_structure(case, phase="decode", tokens=geo["tokens_per_sequence"],
        sequences=geo["sequences_per_replica"], context=actual["conditional_context_tokens"], scope="body")
    refs, unresolved, compact = prepare_references(partitions, manifest)
    unique = {}
    for group in refs:
        unique.setdefault(group["program_set_key"], group)
    # The source helper expands the shared frontend itself; release the first
    # complete manifest so only its selected representative targets remain live.
    del manifest, actual
    gc.collect()
    priced = predict_source_role_references(case, compact, {
        "source_role_references": list(unique.values()), "forward_count": partitions["forward_count"]})
    costs = {row["program_set_key"]: row for row in priced}
    results = []
    for group in refs:
        cost = costs[group["program_set_key"]]
        duration = cost["predicted_reference_us"]
        count = group["observed_us"]["count"]; forwards = partitions["forward_count"]
        observed = group["observed_activity_sum_ns"] / 1e6 / forwards
        predicted = duration * count / 1000 / forwards
        results.append({**group, "prediction_status": "reference_only",
            "predicted_reference_us": duration, "declared_programs": cost["declared_programs"],
            "reference_boundary": cost["boundary"], "calls_per_forward": count / forwards,
            "observed_activity_ms_per_forward": observed,
            "predicted_service_ms_per_forward": predicted,
            "reference_activity_error_ms_per_forward": predicted - observed,
            "per_call_reference_diff_us": duration - group["observed_us"]["mean"],
            "accuracy_status": "reference_only", "strict_accuracy_pass": None,
            "conditions": ["Existing case-declared work is not an additional Body budget.",
                "Complete native descriptors are retained; scalar values, routing or sparse lengths remain conditional.",
                "One native full-batch invocation is compared with the complete selected declared batch program set.",
                *group["source_correspondence"]["limitations"]]})
    if (runtime_identity() != before or identity(path) != pin
            or identity(case_pin["path"])["sha256"] != case_pin["sha256"]):
        raise ValueError("reference_runtime_or_input_changed")
    rss = peak_rss()
    if rss > 512 * 1024**2:
        raise MemoryError("native_reference_exceeds_512_mib")
    return {"schema_version": "mindie-glm-native-reference/1", "status": "partial" if unresolved else "completed",
        "case_id": partitions["source_case_id"], "partition_identity": pin,
        "actual_identity": actual_pin, "case_identity": case_pin,
        "source_identity": partitions["source_identity"], "geometry": geo,
        "conditional_context_tokens": compact["execution"]["context"],
        "forward_count": partitions["forward_count"], "native_event_count": partitions["native_event_count"],
        "referenced_event_count": sum(g["observed_us"]["count"] for g in results),
        "groups": results, "unresolved": unresolved, "strict_compared": 0,
        "runtime_source_commit": runtime_commit, "runtime_source_identity": before,
        "runtime_sources_unchanged": True, "execution": {"new_program_sets": len(unique),
            "raw_capture_reads": 0, "old_prediction_reused": False,
            "elapsed_seconds": time.perf_counter()-started, "maximum_resident_set_size_bytes": rss}}


def render(report):
    lines = ["# GLM complete-native-bucket conditional references", "",
        f"Runtime `{report['runtime_source_commit']}`. The full retained native buckets are compared to existing declared program sets; all rows remain reference-only.",
        "No raw capture scan or old cost reuse. Native launch count, fusion elimination, state-slot behavior and sparse valid lengths are not silently replaced by a contract claim.", "",
        "| Case / native / aligned region | Calls/F | Real Mean / P50 us | Sim reference us | Activity / predicted service / residual ms/F | Boundary |",
        "| --- | ---: | ---: | ---: | ---: | --- |"]
    for case in report["cases"]:
        if case.get("status") == "failed":
            lines.append(f"| {case['partition_path']} | — | — | — | {case['reason']} | failed |")
            continue
        for group in case["groups"]:
            layers = ",".join(map(str, group["layer_ids"]))
            lines.append(f"| {case['case_id']} / {group['native_operator_type']} / layers {layers} | {group['calls_per_forward']:.3f} | "
                f"{group['observed_us']['mean']:.6f} / {group['observed_us']['p50']:.6f} | {group['predicted_reference_us']:.6f} | "
                f"{group['observed_activity_ms_per_forward']:.6f} / {group['predicted_service_ms_per_forward']:.6f} / {group['reference_activity_error_ms_per_forward']:+.6f} | {group['source_correspondence']['boundary_relation']} |")
        for row in case["unresolved"]:
            lines.append(f"| {case['case_id']} / {row['native_operator_type']} | — | — | — | {row['reason']} | unresolved |")
    lines += ["", "Activity residuals overlap in time and cannot be added to explain Body wall time. Exact histograms, all validated layer IDs, source/case/runtime hashes and conditional details are in the JSON.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partition", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-source-commit", required=True)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.worker:
        result = worker(args.partition[0], args.runtime_source_commit)
        write(args.output_dir / (result["case_id"] + "-references.json"), result)
        return
    before = runtime_identity(); started = time.perf_counter(); cases = []
    for path in args.partition:
        case_id = read(path)["source_case_id"]
        command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--partition", str(path.resolve()),
            "--output-dir", str(args.output_dir.resolve()), "--runtime-source-commit", args.runtime_source_commit]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            if result.returncode:
                raise RuntimeError(result.stderr[-4000:])
            case = read(args.output_dir / (case_id + "-references.json"))
        except (subprocess.TimeoutExpired, RuntimeError) as error:
            case = {"case_id": case_id, "partition_path": str(path), "status": "failed", "reason": str(error)}
        cases.append(case)
        print(json.dumps({"case": case_id, "status": case["status"]}), flush=True)
    if before != runtime_identity():
        raise ValueError("batch_reference_runtime_changed")
    report = {"schema_version": "mindie-glm-native-reference-batch/1",
        "status": "completed" if all(c["status"] == "completed" for c in cases) else "partial",
        "runtime_source_commit": args.runtime_source_commit, "runtime_source_identity": before,
        "cases": cases, "elapsed_seconds": time.perf_counter()-started,
        "raw_capture_reads": 0, "strict_compared": 0}
    write(args.output_dir / "glm-native-reference-scoreboard.json", report)
    (args.output_dir / "glm-native-reference-scoreboard.md").write_text(render(report))
    if any(c["status"] == "failed" for c in cases):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
