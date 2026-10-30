"""[Role] Independently audit retained GLM native reference receipts.
[Invariants] Recompute full-histogram arithmetic and all-layer fresh work; never
  infer sparse/routing/state values or recreate unrecorded execution service.
[Timeouts & Locks] One metadata-only source at a time; <=512 MiB, no cost workers.
[Side-Effect Policy] Read saved JSON and Sim declarations; write one review.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gc
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import resource
import sys
import time


def load(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path)
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path.resolve()), "size_bytes": path.stat().st_size,
            "sha256": digest.hexdigest()}


def statistics(counter):
    rows = sorted((int(value), int(count)) for value, count in counter)
    total = sum(count for _, count in rows)
    def rank(k):
        seen = 0
        for value, count in rows:
            seen += count
            if seen >= k:
                return value / 1000
        raise AssertionError("histogram rank outside population")
    return {"count": total, "mean": sum(v*n for v,n in rows)/total/1000,
        "p50": (rank((total+1)//2)+rank((total+2)//2))/2,
        "p90": rank(math.ceil(total*.9)), "min": rows[0][0]/1000,
        "max": rows[-1][0]/1000}


def audit(path):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    started = time.perf_counter()
    report = load(path)
    failures, checked, totals, sources = [], 0, Counter(), []
    def check(condition, message):
        nonlocal checked
        checked += 1
        if not condition:
            failures.append(message)
    def close(left, right, message):
        check(math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-9), message)
    def same_pin(record):
        current = pin(record["path"])
        for key in ("sha256", "size_bytes"):
            check(current[key] == record[key], f"{record['path']}:{key}")
    check(report["status"] == "completed", "batch completed")
    check(report["raw_capture_reads"] == report["strict_compared"] == 0, "no raw or strict")
    runtime_seen = {}
    for case in report["cases"]:
        label = case["case_id"]
        for key in ("partition_identity", "actual_identity", "case_identity", "original_case_identity"):
            same_pin(case[key])
        partitions = load(case["partition_identity"]["path"])
        actual = load(case["actual_identity"]["path"])
        for key in ("source_identity", "geometry", "forward_count"):
            check(case[key] == partitions[key] == actual[key], label+":"+key)
        same_pin(partitions["body_acceptance_identity"])
        check(case["status"] == "completed" and not case["unresolved"], label+":completed")
        check(case["runtime_sources_unchanged"], label+":runtime stable")
        check(case["runtime_source_commit"] == report["runtime_source_commit"], label+":commit")
        for file, digest in case["runtime_source_identity"].items():
            if file not in runtime_seen:
                runtime_seen[file] = pin(file)["sha256"]
            check(runtime_seen[file] == digest, label+":runtime:"+file)
        check(case["execution"]["raw_capture_reads"] == 0, label+":no raw")
        check(not case["execution"]["old_prediction_reused"], label+":new costs")
        check(case["execution"]["maximum_resident_set_size_bytes"] <= 512*1024**2, label+":memory")
        geo = case["geometry"]
        declaration = parse_case(load(case["case_identity"]["path"]))
        manifest = export_structure(declaration, phase="decode", scope="body",
            tokens=geo["tokens_per_sequence"], sequences=geo["sequences_per_replica"],
            context=case["conditional_context_tokens"], replicas=(0,))
        nodes = {n["node_id"]: n for n in (*manifest["nodes"], *manifest.get("resource_operators", []))}
        count = 0
        selected_indices = set()
        for group in case["groups"]:
            gid = label+":"+group["group_id"]
            index = group["partition_index"]
            check(index not in selected_indices, gid+":partition once")
            selected_indices.add(index)
            original = partitions["partitions"][index]
            for key in ("native_operator_type", "native_abi", "duration_ns_counter", "observed_us"):
                check(group[key] == original[key], gid+":"+key)
            layers = sorted(int(x) for x in original["layer_counts"])
            check(group["layer_ids"] == layers, gid+":complete layers")
            check(sum(original["layer_counts"].values()) == sum(original["forward_counts"].values())
                  == group["observed_us"]["count"], gid+":layer/forward count")
            stats = statistics(group["duration_ns_counter"])
            for key, value in stats.items():
                close(value, group["observed_us"][key], gid+":stats:"+key)
            n = stats["count"]; count += n
            activity_ns = sum(ns*k for ns,k in group["duration_ns_counter"])
            check(activity_ns == group["observed_activity_sum_ns"], gid+":activity ns")
            calls = n/case["forward_count"]
            service = group["predicted_reference_us"] * calls / 1000
            observed = activity_ns / 1e6 / case["forward_count"]
            close(calls, group["calls_per_forward"], gid+":calls/F")
            close(observed, group["observed_activity_ms_per_forward"], gid+":activity/F")
            close(service, group["predicted_service_ms_per_forward"], gid+":service/F")
            close(service-observed, group["reference_activity_error_ms_per_forward"], gid+":residual/F")
            close(group["predicted_reference_us"]-stats["mean"], group["per_call_reference_diff_us"], gid+":diff/us")
            check(group["prediction_status"] == group["accuracy_status"] == "reference_only", gid+":reference")
            check(group["strict_accuracy_pass"] is None and not group["strict_accuracy_implied"]
                  and not group["additional_budget_allowed"] and not group["occurrence_binding_implied"], gid+":no strict")
            ids = group["representative_target_ids"]
            check(len(ids) == len(group["physical_program_signatures"]) == len(group["physical_work_per_program"]), gid+":program count")
            for layer in layers:
                for ordinal, identifier in enumerate(ids):
                    target = re.sub(r"\.l\d+\.", f".l{layer}.", identifier)
                    check(target in nodes, gid+":fresh node:"+target)
                    if target not in nodes:
                        continue
                    node = nodes[target]
                    check(node["physical_signature"] == group["physical_program_signatures"][ordinal], gid+":fresh signature")
                    check(node["physical_work"] == group["physical_work_per_program"][ordinal], gid+":fresh work")
            correspondence = group["source_correspondence"]
            native = group["native_operator_type"]
            if native == "RecurrentKda":
                check(len(group["native_abi"][2]) == 11 and len(group["native_abi"][3]) == 3, gid+":KDA ABI")
                check(correspondence["observed_accepted_token_values"] is None, gid+":accepted unknown")
                check(not correspondence["state_selection"]["acceptance_changes_query_work"], gid+":all q execute")
                check(correspondence["private_caller_sigmoid_placement"] == "not_established", gid+":sigmoid unknown")
            elif native == "KvQuantSparseFlashAttentionVllm":
                check(correspondence["observed_cache_row_bytes"] == 528, gid+":528")
                check(not correspondence["observed_cache_capacity_is_active_context"], gid+":not capacity")
                check(correspondence["observed_key_value_address_alias"] is None, gid+":alias unknown")
            elif native == "GroupedMatmulSwigluQuantV2":
                check(correspondence["native_fusion_resource_program_selected"], gid+":fused resource")
                check(correspondence["observed_valid_routed_rows"] is None, gid+":routing unknown")
            totals[native] += n; totals["groups"] += 1
        check(count == case["referenced_event_count"] == case["native_event_count"], label+":complete count")
        totals["events"] += count; totals["forwards"] += case["forward_count"]
        totals["new_program_sets"] += case["execution"]["new_program_sets"]
        sources.append({"case_id": label, "forward_count": case["forward_count"], "groups": len(case["groups"]), "events": count})
        del manifest, nodes, actual, partitions
        gc.collect()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin": rss *= 1024
    return {"schema_version": "mindie-glm-native-reference-independent-review/1",
        "status": "passed" if not failures else "failed", "checks": checked, "failures": failures,
        "report_identity": pin(path), "runtime_source_commit": report["runtime_source_commit"],
        "source_count": len(sources), "totals": dict(totals), "cases": sources,
        "raw_capture_reads": 0, "cost_executions": 0, "elapsed_seconds": time.perf_counter()-started,
        "reviewer_peak_rss_bytes": rss, "reviewer_identity": pin(__file__),
        "scope": ["Saved source/Body/case/runtime hashes, full native ABI and exact histogram equality.",
            "Independent quantiles and per-call/per-Forward arithmetic; every fresh layer physical signature/work.",
            "Service values are executed worker outputs; this review does not reconstruct unsaved per-program resource rates.",
            "No sparse/group-list/state values inferred; all groups remain reference-only."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.report)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({key: result[key] for key in ("status", "checks", "failures", "totals", "reviewer_peak_rss_bytes")}))
    if result["failures"]: raise SystemExit(1)


if __name__ == "__main__": main()
