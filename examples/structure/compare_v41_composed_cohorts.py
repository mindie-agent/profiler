"""Retain complete normalized V4.1 cohorts as explicit source references.

[Role] Price prepared q_b/wo_b and arch35 HCPost without a full-DP JSON copy.
[Invariants] The original complete cohort and whole-family histogram must cover
  exactly the same calls. All forty fresh layer contracts/work agree. Serializing
  replica 0 is a conditional DP symmetry projection, never a new strict binding.
[Timeouts & Locks] One source worker; 180 s child / 190 s outer; <=512 MiB.
[Side-Effect Policy] Saved local metadata only, separate reports, no raw/NPU work.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import gc
from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import time

from body_source_role_references import canonical, predict_source_role_references
from compare_glm_native_partitions import peak_rss, render
from compare_v41_composed_sources import runtime_identity as base_runtime_identity, validate_selection
from kimi_native_references import program_signature
from rebind_body_source_roles import freeze
from reprice_body_operator_families import validate_observation_join
from replay_body_operator_families import duration_stats, identity, read, write

ROLES = {"q_b", "grouped_output_b", "attention.hc_post_group", "ffn.hc_post_group"}


def runtime_identity():
    result = base_runtime_identity()
    source = identity(Path(__file__).resolve())
    result[source["path"]] = source["sha256"]
    return result


def prepare_references(actual, mapping, manifest):
    validate_observation_join(actual, mapping)
    replica = min(manifest["execution"]["replicas"])
    expected_replicas = manifest["execution"]["cohort_replicas"]
    targets = {n["node_id"]: n for n in manifest["nodes"]}
    targets.update((n["subgraph_id"], n) for n in manifest["subgraphs"])
    resources = {n["node_id"]: n for n in manifest["resource_operators"]}
    by_role = defaultdict(list)
    for window in mapping["windows"]:
        for cohort in window["cohorts"]:
            roles = mapping["conditional_role_by_cohort_id"][cohort["cohort_id"]]
            if len(roles) == 1 and roles[0] in ROLES:
                by_role[roles[0]].append(cohort)
    refs, unresolved, selected = [], [], {}
    for role in sorted(ROLES):
        family = [f for f in actual["families"] if f["declared_role"] == role]
        count = sum(f["observed_us"]["count"] for f in family)
        try:
            if len(family) != 1 or len(by_role[role]) != 1:
                raise ValueError("one_complete_observed_cohort_required_no_histogram_split")
            family, old = family[0], by_role[role][0]
            hist = dict(family["duration_ns_counter"])
            if (count != old["event_count"] or count != old["complete_event_count"]
                    or old["clipped_event_count"] != 0 or sum(hist.values()) != count
                    or sum(ns*n for ns,n in hist.items()) != old["complete_activity_sum_ns"]):
                raise ValueError("whole_family_histogram_is_not_exact_complete_cohort")
            old_ids = defaultdict(set)
            for key in old["target_ids"]:
                prefix, local = key.split("/", 1)
                old_ids[int(prefix.removeprefix("rank:"))].add(local)
            if sorted(old_ids) != expected_replicas or any(ids != old_ids[replica] for ids in old_ids.values()):
                raise ValueError("retained_full_candidate_set_is_not_symmetric_dp")
            members = [targets[f"rank:{replica}/{local}"] for local in sorted(old_ids[replica])]
            if {n["layer"] for n in members} != set(range(40)) or len(members) != 40:
                raise ValueError("complete_forty_layer_candidate_set_required")
            first, signature = None, None
            for target in members:
                if freeze(target["contract"]) != freeze(old["contract"]):
                    raise ValueError("fresh_active_contract_differs_from_complete_observed_cohort")
                if role.endswith("hc_post_group"):
                    boundary = target.get("resource_boundary", {})
                    if boundary.get("traffic_profile") != "hc_post_arch35_bf16_175ef4d4" or len(boundary.get("operator_ids", ())) != 1:
                        raise ValueError("arch35_hcpost_resource_not_selected")
                    program = resources[boundary["operator_ids"][0]]
                else:
                    program = target
                    if program["recipe"] != "prepared_mx32_aic_matrix":
                        raise ValueError("prepared_mx32_matrix_not_selected")
                key = canonical((program_signature(program), program["physical_work"]))
                if signature is not None and key != signature:
                    raise ValueError("fresh_layer_work_heterogeneous_cannot_split_histogram")
                if first is None:
                    first, signature = program, key
        except (ValueError, KeyError) as error:
            unresolved.append({"declared_role": role, "native_operator_type": "HcPost" if "hc_post" in role else "QuantBatchMatmulV3",
                "event_count": count, "status": "unresolved", "reason": str(error)})
            continue
        selected[first["node_id"]] = first
        refs.append({"group_id": "sha256:" + sha256(canonical((old["cohort_id"], signature)).encode()).hexdigest(),
            "retained_cohort_id": old["cohort_id"], "native_operator_type": old["native_operator_type"],
            "declared_role": role, "layer_ids": list(range(40)), "representative_replica": replica,
            "representative_target_ids": [first["node_id"]], "program_set_key": sha256(signature.encode()).hexdigest(),
            "physical_program_signatures": [first["physical_signature"]], "physical_work_per_program": [first["physical_work"]],
            "observed_contract": old["contract"], "native_abi": None,
            "observed_us": duration_stats(hist, 1000), "duration_ns_counter": family["duration_ns_counter"],
            "observed_activity_sum_ns": old["complete_activity_sum_ns"],
            "strict_accuracy_implied": False, "additional_budget_allowed": False, "occurrence_binding_implied": False,
            "original_partition_histogram_unchanged": True,
            "source_correspondence": {"boundary_relation": "complete_normalized_cohort_to_explicit_source_program_reference",
                "observed_active_contract": old["contract"], "complete_native_abi_available": False,
                "retained_contract_scope": old["contract_scope"], "retained_candidate_placement": old["placement"],
                "declared_cohort_replicas": expected_replicas, "fresh_layer_contracts_validated": 40,
                "selected_program_metadata": first["operator"]["metadata"],
                "limitations": ["The saved normalized contract is complete for its original comparison scope, but is not a new full native ABI capture.",
                    "The unique old cohort and family histogram have equal complete count/activity; neither is split or extrapolated.",
                    "Eight DP replicas are a declared symmetry condition; no captured occurrence is bound to replica 0.",
                    "Fresh source resource boundaries may differ from the old strict cohort, so this arm remains reference-only."]}})
    return refs, unresolved, {"execution": manifest["execution"], "graph_id": manifest["graph_id"], "nodes": list(selected.values())}


def worker(reference_path, commit):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    start = time.perf_counter(); before = runtime_identity(); reference_pin = identity(reference_path)
    prior = read(reference_path)
    actual_pin, case_pin = prior["actual_identity"], prior["case_identity"]
    for pin in (actual_pin, case_pin):
        if identity(pin["path"]) != pin: raise ValueError("retained_input_changed")
    actual = read(actual_pin["path"])
    mapping_path = Path(actual_pin["path"]).with_name(Path(actual_pin["path"]).name.replace(".actual.json", ".mapping.json"))
    mapping_pin = identity(mapping_path); mapping = read(mapping_path)
    case = parse_case(read(case_pin["path"])); validate_selection(case)
    geo = actual["geometry"]
    manifest = export_structure(case, phase="decode", tokens=geo["tokens_per_sequence"],
        sequences=geo["sequences_per_replica"], context=actual["conditional_context_tokens"], scope="body", replicas=(0,))
    refs, failures, compact = prepare_references(actual, mapping, manifest)
    del manifest, mapping
    gc.collect()
    unique = {g["program_set_key"]: g for g in refs}
    costs = {g["program_set_key"]: g for g in predict_source_role_references(case, compact,
        {"source_role_references": list(unique.values()), "forward_count": actual["forward_count"]})}
    groups = []
    for group in refs:
        cost = costs[group["program_set_key"]]
        observed = group["observed_activity_sum_ns"] / 1e6 / actual["forward_count"]
        calls = group["observed_us"]["count"] / actual["forward_count"]
        predicted = cost["predicted_reference_us"] * calls / 1000
        groups.append({**group, "prediction_status": "reference_only", "accuracy_status": "reference_only",
            "strict_accuracy_pass": None, "predicted_reference_us": cost["predicted_reference_us"],
            "reference_boundary": cost["boundary"], "declared_programs": cost["declared_programs"],
            "calls_per_forward": calls, "observed_activity_ms_per_forward": observed,
            "predicted_service_ms_per_forward": predicted, "reference_activity_error_ms_per_forward": predicted-observed,
            "per_call_reference_diff_us": cost["predicted_reference_us"] - group["observed_us"]["mean"]})
    for pin in (reference_pin, actual_pin, case_pin, mapping_pin):
        if identity(pin["path"]) != pin: raise ValueError("retained_input_changed_during_reference")
    if runtime_identity() != before: raise ValueError("reference_runtime_changed")
    rss = peak_rss()
    if rss > 512 * 1024**2: raise MemoryError("normalized_reference_exceeds_512_mib")
    return {"schema_version": "mindie-native-body-reference/1", "status": "partial" if failures else "completed",
        "case_id": prior["case_id"], "source_identity": actual["source_identity"], "geometry": geo,
        "forward_count": actual["forward_count"], "conditional_context_tokens": actual["conditional_context_tokens"],
        "actual_identity": actual_pin, "case_identity": case_pin, "mapping_identity": mapping_pin,
        "native_reference_identity": reference_pin, "runtime_source_commit": commit, "runtime_source_identity": before,
        "native_event_count": sum(g["observed_us"]["count"] for g in groups)+sum(g["event_count"] for g in failures),
        "referenced_event_count": sum(g["observed_us"]["count"] for g in groups), "groups": groups,
        "unresolved": failures, "strict_compared": 0, "runtime_sources_unchanged": True,
        "execution": {"new_program_sets": len(unique), "raw_capture_reads": 0, "old_prediction_reused": False,
            "elapsed_seconds": time.perf_counter()-start, "maximum_resident_set_size_bytes": rss}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-report", type=Path, required=True); p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--runtime-source-commit", required=True); p.add_argument("--worker", action="store_true")
    a = p.parse_args(); a.output_dir.mkdir(parents=True, exist_ok=True)
    if a.worker:
        result = worker(a.native_report, a.runtime_source_commit)
        write(a.output_dir / (result["case_id"]+"-references.json"), result); return
    before = runtime_identity(); prior = read(a.native_report); cases=[]; started=time.perf_counter()
    for case in prior["cases"]:
        source = a.native_report.parent / case["case_id"] / (case["case_id"]+"-references.json")
        command=[sys.executable,str(Path(__file__).resolve()),"--worker","--native-report",str(source.resolve()),
            "--output-dir",str(a.output_dir.resolve()),"--runtime-source-commit",a.runtime_source_commit]
        child=subprocess.run(command,capture_output=True,text=True,timeout=190)
        if child.returncode: raise RuntimeError(child.stderr[-4000:])
        cases.append(read(a.output_dir/(case["case_id"]+"-references.json")))
        print({"case_id":case["case_id"],"status":cases[-1]["status"]},flush=True)
    if runtime_identity()!=before: raise ValueError("batch_runtime_changed")
    result={"schema_version":"mindie-native-body-reference-batch/1",
        "status":"completed" if all(c["status"]=="completed" for c in cases) else "partial",
        "runtime_source_commit":a.runtime_source_commit,"runtime_source_identity":before,"cases":cases,
        "raw_capture_reads":0,"strict_compared":0,"elapsed_seconds":time.perf_counter()-started,
        "native_batch_identity":identity(a.native_report)}
    target=a.output_dir/"v41-normalized-reference-scoreboard.json";write(target,result);target.with_suffix(".md").write_text(render(result))


if __name__ == "__main__": main()
