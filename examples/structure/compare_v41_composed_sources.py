"""Price explicit V4.1 MX32/HC source programs against retained native buckets.

[Role] Reuse complete MC2, HCPre, expert GEMM and output-matrix observations.
[Invariants] Source-case selection is explicit. Full DP traffic is constructed
  before representative serialization; costs keep the original complete case.
  No measured rows, peer waits or histogram splits are inferred from capacity.
[Timeouts & Locks] One sequential source child, 180 s and <=512 MiB; no locks.
[Side-Effect Policy] Read local retained JSON and write a new conditional arm.
"""
from __future__ import annotations

import argparse
import gc
import json
from pathlib import Path
import subprocess
import sys
import time

from body_source_role_references import predict_source_role_references
from compare_glm_native_partitions import peak_rss, render
from compare_body_operator_families import prediction_runtime_identity
from replay_body_operator_families import identity, read, write
from v41_mx32_hc_references import prepare_affected_references


def runtime_identity():
    value = prediction_runtime_identity()
    for name in ("compare_v41_composed_sources.py", "v41_mx32_hc_references.py",
                 "v41_native_references.py", "rebind_grouped_source_roles.py",
                 "kimi_native_references.py", "compare_glm_native_partitions.py"):
        path = Path(__file__).with_name(name).resolve()
        value[str(path)] = identity(path)["sha256"]
    return value


def validate_selection(case):
    """All new mechanisms must be selected in the actual execution input."""
    kernels = case.runtime.kernels
    protocol = kernels.get("native_moe_protocol", {})
    lowerings = kernels.get("lowerings", {})
    matrix = lowerings.get("mx_matrix", {})
    fusion = lowerings.get("native_fusion", {}).get("options", {}).get("traffic_profile", {})
    if protocol != {"kind": "arch35_fullmesh", "max_inflight_per_rank": 8, "dispatch_quant": "mx"}:
        raise ValueError("explicit_v41_mx32_fullmesh_window8_not_selected")
    if (matrix.get("implementation") != "ascend_prepared_mx32_matrix"
            or set(matrix.get("options", {}).get("projection_recipes", ())) != {"q_b", "grouped_output_a", "grouped_output_b"}
            or matrix.get("options", {}).get("scale_storage") != "replace_checkpoint_scales"):
        raise ValueError("explicit_prepared_mx32_projection_representation_not_selected")
    if fusion.get("hc_pre") != "hc_pre_arch35_mk_175ef4d4" or fusion.get("hc_post") != "hc_post_arch35_bf16_175ef4d4":
        raise ValueError("explicit_arch35_hc_source_pair_not_selected")
    if case.model.layers != 40 or case.runtime.parallel.dp != 8:
        raise ValueError("v41_complete_40_layer_dp8_case_required")


def worker(partition_path, case_path, runtime_commit):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure

    started = time.perf_counter(); before = runtime_identity()
    partition_pin, case_pin = identity(partition_path), identity(case_path)
    partitions = read(partition_path)
    actual_pin = partitions["actual_identity"]
    if identity(actual_pin["path"]) != actual_pin:
        raise ValueError("retained_actual_identity_changed")
    actual = read(actual_pin["path"])
    if any(actual[key] != partitions[key] for key in ("source_identity", "geometry", "forward_count")):
        raise ValueError("native_partition_actual_population_differs")
    context, geometry = actual["conditional_context_tokens"], actual["geometry"]
    original_pin = partitions["case_identity"]
    if identity(original_pin["path"]) != original_pin:
        raise ValueError("retained_original_case_changed")
    case, original = parse_case(read(case_path)), parse_case(read(original_pin["path"]))
    model, old_model = case.model.to_dict(), original.model.to_dict()
    metadata, old_metadata = model.pop("metadata", None), old_model.pop("metadata", None)
    if model != old_model or case.machine != original.machine or case.runtime.parallel != original.runtime.parallel:
        raise ValueError("composed_source_arm_changes_model_hardware_or_parallel")
    validate_selection(case)
    changes = {"runtime.kernels": {"original": original.runtime.kernels, "selected": case.runtime.kernels}}
    if metadata != old_metadata:
        changes["model.metadata"] = {"original": old_metadata, "selected": metadata}
    del actual, partitions, original, model, old_model, metadata, old_metadata
    gc.collect()
    manifest = export_structure(case, phase="decode", tokens=geometry["tokens_per_sequence"],
        sequences=geometry["sequences_per_replica"], context=context, scope="body", replicas=(0,))
    actual, partitions = read(actual_pin["path"]), read(partition_path)
    refs, unresolved, compact = prepare_affected_references(actual, partitions, manifest)
    serialized_execution = manifest["execution"]
    observed_total = sum(g["observed_us"]["count"] for g in refs) + sum(g["event_count"] for g in unresolved)
    forward_count = actual["forward_count"]
    del manifest, actual
    gc.collect()
    unique = {g["program_set_key"]: g for g in refs}
    priced = predict_source_role_references(case, compact, {
        "source_role_references": list(unique.values()), "forward_count": forward_count})
    costs = {g["program_set_key"]: g for g in priced}
    results = []
    for group in refs:
        cost = costs[group["program_set_key"]]
        duration = cost["predicted_reference_us"]
        count = group["observed_us"]["count"]
        observed = group["observed_activity_sum_ns"] / 1e6 / forward_count
        predicted = duration * count / 1000 / forward_count
        results.append({**group, "prediction_status": "reference_only", "accuracy_status": "reference_only",
            "strict_accuracy_pass": None, "strict_accuracy_implied": False, "additional_budget_allowed": False,
            "predicted_reference_us": duration, "declared_programs": cost["declared_programs"],
            "reference_boundary": cost["boundary"], "calls_per_forward": count / forward_count,
            "observed_activity_ms_per_forward": observed, "predicted_service_ms_per_forward": predicted,
            "reference_activity_error_ms_per_forward": predicted - observed,
            "per_call_reference_diff_us": duration - group["observed_us"]["mean"],
            "conditions": ["Existing source-selected work; never an additional Body budget.",
                "The complete DP peer graph is rebuilt for costs; representative serialization does not reduce the case.",
                "Native elapsed may include peer waits; dynamic routing and binary/source equivalence remain conditional.",
                *group["source_correspondence"]["limitations"]]})
    if (runtime_identity() != before or identity(partition_path) != partition_pin
            or identity(case_path) != case_pin or identity(actual_pin["path"]) != actual_pin):
        raise ValueError("source_runtime_or_retained_input_changed")
    rss = peak_rss()
    if rss > 512 * 1024**2:
        raise MemoryError("composed_source_reference_exceeds_512_mib")
    return {"schema_version": "mindie-native-body-reference/1",
        "status": "partial" if unresolved else "completed", "case_id": partitions["source_case_id"],
        "partition_identity": partition_pin, "actual_identity": actual_pin,
        "case_identity": case_pin, "original_case_identity": original_pin,
        "declaration_variant": "explicit_composed_arch35_mx32_hc_source", "declaration_changes": changes,
        "source_identity": partitions["source_identity"], "geometry": geometry,
        "conditional_context_tokens": context, "forward_count": forward_count,
        "native_event_count": observed_total, "referenced_event_count": sum(g["observed_us"]["count"] for g in refs),
        "groups": results, "unresolved": unresolved, "strict_compared": 0,
        "serialized_structure_execution": serialized_execution,
        "runtime_source_commit": runtime_commit, "runtime_source_identity": before,
        "runtime_sources_unchanged": True,
        "coverage": {"included": ["MX32 dispatch", "float combine", "partial HCPre", "expert up/down", "prepared wo_a", "source-symbol MQSMLA"],
            "separate_normalized_cohorts": ["HCPost", "prepared q_b", "prepared wo_b"],
            "unchanged_not_repriced": ["rotary", "cache store"], "all_native_families_claimed": False},
        "execution": {"new_program_sets": len(unique), "raw_capture_reads": 0, "old_prediction_reused": False,
            "elapsed_seconds": time.perf_counter() - started, "maximum_resident_set_size_bytes": rss}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--partition", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-source-commit", required=True)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.worker:
        result = worker(args.partition, args.case, args.runtime_source_commit)
        write(args.output_dir / (result["case_id"] + "-references.json"), result)
        return
    before = runtime_identity(); started = time.perf_counter()
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--partition", str(args.partition.resolve()),
        "--case", str(args.case.resolve()), "--output-dir", str(args.output_dir.resolve()),
        "--runtime-source-commit", args.runtime_source_commit]
    case_id = read(args.partition)["source_case_id"]
    try:
        child = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
        if child.returncode:
            raise RuntimeError(child.stderr[-4000:])
        case = read(args.output_dir / (case_id + "-references.json"))
    except (subprocess.TimeoutExpired, RuntimeError) as error:
        case = {"case_id": case_id, "partition_path": str(args.partition), "status": "failed", "reason": str(error)}
    if runtime_identity() != before:
        raise ValueError("batch_source_runtime_changed")
    report = {"schema_version": "mindie-native-body-reference-batch/1", "status": case["status"],
        "runtime_source_commit": args.runtime_source_commit, "runtime_source_identity": before,
        "cases": [case], "elapsed_seconds": time.perf_counter() - started,
        "raw_capture_reads": 0, "strict_compared": 0}
    write(args.output_dir / "v41-composed-native-reference-scoreboard.json", report)
    (args.output_dir / "v41-composed-native-reference-scoreboard.md").write_text(render(report))
    print(json.dumps({"case": case_id, "status": case["status"]}), flush=True)
    if case["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
