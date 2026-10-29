"""Rebind complete retained MatMul partitions into a full family scoreboard.

[Role] Add newly declared matrix roles without scanning captures or losing other families.
[Invariants] Complete ABI, verified layer region and homogeneous work select cohorts;
  timing never selects targets. Equal-work role alternatives remain a single cohort.
  Previously priced work is reused only under the identical runtime and physical key.
[Timeouts & Locks] One bounded new-cost subprocess at a time; 512 MiB budget; no locks.
[Side-Effect Policy] Read frozen evidence and declarations; write a distinct canonical arm.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import time

from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import _freeze
from mindie_sim.cohort_comparison import _check_cohort, _comparison, _program_ids, accuracy_fields
from compare_body_operator_families import family_rows
from reprice_body_operator_families import (canonical, compact_case, compare_programs, fresh_structure,
    identity, read, write, runtime_identity, sim_sources, _observation, _program_key, render_repriced, _rss)
from replay_body_operator_families import RoleMapper, declared_role, role_block, duration_stats


def verify_retained_inputs(compact, row, actual, partitions):
    """Join retained populations by recorded identity before using their histograms."""
    for pin in (compact["case_detail_identity"], *(row[key] for key in (
            "actual_identity", "mapping_identity", "comparison_identity", "case_identity"))):
        if identity(pin["path"]) != pin:
            raise ValueError("retained_matrix_input_identity_changed")
    for key in ("source_identity", "body_acceptance_identity", "geometry", "forward_count"):
        if partitions[key] != actual[key]:
            raise ValueError("matrix_partition_population_join_differs:" + key)
    retained_actual = partitions["actual_identity"]
    retained_path = Path(retained_actual["path"])
    if not retained_path.is_absolute():
        retained_path = Path(__file__).resolve().parents[2] / retained_path
    if ({**retained_actual, "path": str(retained_path.resolve())} != row["actual_identity"]
            or identity(retained_path) != row["actual_identity"]):
        raise ValueError("matrix_partition_actual_identity_differs")
    if partitions["source_case_id"] != actual["source_case_id"]:
        raise ValueError("matrix_partition_source_case_differs")


def matrix_mapping(partitions, previous, manifest):
    """Preserve exact histograms while rebuilding every matrix candidate set."""
    mapper = RoleMapper(manifest, mapping_limit=0, phase="decode")
    window = previous["windows"][0]
    observation = _observation(window, partitions["source_identity"])
    acc = CohortAccumulator(manifest["graph_id"], mapper.target_index, observation,
                            execution=manifest["execution"])
    groups, family = {}, {}
    decisions = []
    for index, part in enumerate(partitions["partitions"]):
        contract = part["contract"]
        available = mapper._rank_candidates(mapper.contracts.get(_freeze(contract), ()), "rank_0") if contract else []
        layers = {int(layer) for layer in part["layer_counts"]}
        block = "ffn" if part["topology_region"] == "ffn" else "attention"
        candidates = sorted(key for key in available if mapper.targets[key].get("layer") in layers
            and role_block(mapper.targets[key]) in {None, block})
        per_layer = {layer: sorted({declared_role(mapper.targets[key]) for key in candidates
            if mapper.targets[key].get("layer") == layer}) for layer in layers}
        roles = sorted({role for values in per_layer.values() for role in values})
        complete = all(per_layer.values()) and len({tuple(values) for values in per_layer.values()}) == 1
        declaration, reason = acc._cohort(candidates) if complete else (None, "missing_or_heterogeneous_layer_candidates")
        role = "|".join(roles) if roles else "unresolved"
        hist = Counter(dict(part["duration_ns_counter"]))
        f = family.setdefault(role, {"hist": Counter(), "reasons": Counter(), "targets": set(),
                                     "regions": defaultdict(Counter), "partitions": []})
        f["hist"].update(hist); f["reasons"][reason or "cohort_eligible"] += sum(hist.values())
        f["targets"].update(candidates); f["regions"][part["attention_kind"], block].update(hist)
        f["partitions"].append(index)
        if declaration is not None:
            key = (canonical(contract), tuple(roles), declaration["physical_signature"])
            value = groups.setdefault(key, {"targets": set(), "hist": Counter(), "partitions": []})
            value["targets"].update(candidates); value["hist"].update(hist); value["partitions"].append(index)
        decisions.append({"partition_index": index, "old_roles": part["declared_roles"], "fresh_roles": roles,
            "event_count": sum(hist.values()), "eligible": declaration is not None, "reason": reason,
            "full_native_abi_sha256": sha256(canonical(part["native_abi"]).encode()).hexdigest()})
    cohorts, roles_by_id = [], {}
    for (_, roles, _), value in groups.items():
        declaration, reason = acc._cohort(sorted(value["targets"]))
        if reason:
            raise ValueError("merged_native_partitions_are_not_homogeneous:" + reason)
        hist = value["hist"]; n = sum(hist.values()); activity = sum(ns * count for ns, count in hist.items())
        stats = duration_stats(hist, 1)
        cid = "sha256:" + sha256(canonical((manifest["graph_id"], "rank_0", "MatMulV3", declaration["target_ids"])).encode()).hexdigest()
        row = {"schema_version": "mindie-profile-cohort/1", "cohort_id": cid, **declaration,
            "native_operator_type": "MatMulV3", "rank_id": "rank_0", "device_id": window["cohorts"][0]["device_id"],
            "event_count": n, "complete_event_count": n, "clipped_event_count": 0,
            "activity_sum_ns": activity, "complete_activity_sum_ns": activity, "busy_union_ns": None,
            "duration_ns": {key: stats[key] for key in ("mean", "p50", "min", "max")},
            "status_counts": {"candidate_set": n}, "occurrence_binding_implied": False,
            "multiplicity": {"observed_calls": n, "declared_instances": declaration["declared_instance_count"],
                "calls_per_declared_instance": n / declaration["declared_instance_count"], "steps_in_window": None,
                "basis": "complete_histogram_and_verified_layer_region; equal_work_role_alternatives_not_occurrence_binding"},
            "native_partition_indices": value["partitions"], "interval_union_available": False}
        _check_cohort(row, window, manifest, mapper.targets)
        cohorts.append(row); roles_by_id[cid] = list(roles)
    families = [{"native_operator_type": "MatMulV3", "declared_role": role,
        "duration_ns_counter": sorted(v["hist"].items()), "observed_us": duration_stats(v["hist"], 1000),
        "cohort_reasons": dict(v["reasons"]), "candidate_target_ids": sorted(v["targets"]),
        "role_basis": "complete_native_abi_and_verified_layer_region; candidate_set_not_occurrence_binding",
        "examples": [], "native_partition_indices": v["partitions"],
        "structure_groups": [{"attention_kind": k[0], "block": k[1], "duration_ns_counter": sorted(h.items()),
                               "observed_us": duration_stats(h, 1000)} for k, h in v["regions"].items()]}
        for role, v in sorted(family.items())]
    return cohorts, roles_by_id, families, decisions


def reuse_comparison(cohort, prior, manifest, window, receipt):
    """Reuse service for a validated identical physical program, not measured averages."""
    targets = {row["node_id"]: row for row in manifest["nodes"]}
    targets.update((row["subgraph_id"], row) for row in manifest.get("subgraphs", []))
    selected = _check_cohort(cohort, window, manifest, targets)
    if _program_key(cohort) != _program_key(prior) or prior["status"] != "compared":
        raise ValueError("matrix_cost_reuse_requires_identical_completed_program")
    prediction = deepcopy(prior["prediction"])
    if canonical(prediction["physical_work_per_instance"]) != canonical(cohort["physical_work_per_instance"]):
        raise ValueError("matrix_cost_reuse_work_changed")
    ids, boundary = _program_ids(selected[0], cohort["target_kind"])
    prediction.update(representative_target_id=cohort["target_ids"][0], representative_operator_ids=ids,
        resource_boundary=boundary, observed_call_count_total_ms=prediction["per_call_ms"] * cohort["event_count"],
        per_declared_step_ms=prediction["per_call_ms"] * cohort["declared_instance_count"])
    row = {key: deepcopy(value) for key, value in prior.items()}
    for key in ("cohort_id", "target_ids", "target_kind", "native_operator_type", "physical_signature", "replica",
                "stage", "phase", "rank_id", "device_id", "contract", "contract_scope", "resource_boundary",
                "structural_classification", "declared_instance_count", "declared_candidate_instance_count",
                "declared_layer_count", "placement", "multiplicity"):
        row[key] = deepcopy(cohort.get(key))
    row["observed"] = {key: cohort.get(key) for key in ("event_count", "complete_event_count", "clipped_event_count",
        "duration_ns", "activity_sum_ns", "complete_activity_sum_ns", "busy_union_ns", "status_counts")}
    row["prediction"] = prediction
    row["status"], row["reason"], row["comparison"] = _comparison(cohort, prediction)
    row.update(accuracy_fields(row), same_runtime_physical_cost_reused_from=receipt,
               reused_cost_cohort_id=prior["cohort_id"])
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--partition-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--compare-timeout", type=float, default=120)
    args = parser.parse_args(); args.reference_timeout = 180; args.frozen_native_rebind = False
    started = time.perf_counter(); before = runtime_identity(); own_source = identity(Path(__file__))
    parent = read(args.previous)
    if sim_sources(before) != sim_sources(parent["runtime_source_identity"]):
        raise ValueError("prior_cost_runtime_differs")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []; total_new = total_reused = 0
    for compact in parent["cases"]:
        old = read(compact["case_detail_identity"]["path"])["cases"][0]
        source_id = old["source_case_id"]; prefix = args.output_dir / ("body-operator-" + source_id + "-logical96-full-matrix")
        actual = read(old["actual_identity"]["path"]); previous = read(old["mapping_identity"]["path"])
        comparison = read(old["comparison_identity"]["path"]); case = Path(old["case_identity"]["path"])
        if identity(case) != old["case_identity"]: raise ValueError("case_changed")
        part_path = args.partition_dir / (source_id + "-matrix-partitions.json"); partitions = read(part_path)
        verify_retained_inputs(compact, old, actual, partitions)
        manifest = fresh_structure(case, previous)
        cohorts, role_ids, matrices, decisions = matrix_mapping(partitions, previous, manifest)
        native_hist = Counter()
        for f in actual["families"]:
            if f["native_operator_type"] == "MatMulV3": native_hist.update(dict(f["duration_ns_counter"]))
        new_hist = Counter()
        for f in matrices: new_hist.update(dict(f["duration_ns_counter"]))
        if native_hist != new_hist: raise ValueError("matrix_histogram_population_changed")
        updated_actual = {**actual, "families": [f for f in actual["families"] if f["native_operator_type"] != "MatMulV3"] + matrices,
            "original_actual_identity": old["actual_identity"], "matrix_partition_identity": identity(part_path),
            "declaration_role_refresh": "complete_retained_matrix_ABI_and_whole_layer_topology"}
        actual_path = prefix.with_suffix(".actual.json"); write(actual_path, updated_actual)
        retained = [c for c in previous["windows"][0]["cohorts"] if c["native_operator_type"] != "MatMulV3"]
        role_ids.update({c["cohort_id"]: previous["conditional_role_by_cohort_id"][c["cohort_id"]] for c in retained})
        excluded = Counter()
        for family in updated_actual["families"]:
            excluded.update({key: value for key, value in family["cohort_reasons"].items()
                             if key != "cohort_eligible"})
        mapping = {**previous, "windows": [{**previous["windows"][0], "cohorts": retained + cohorts,
                    "cohort_excluded_event_counts": dict(excluded)}],
            "conditional_role_by_cohort_id": role_ids, "matrix_partition_identity": identity(part_path),
            "cohort_status": "partial" if excluded else "aggregated",
            "cohort_event_window_count": sum(c["event_count"] for c in retained + cohorts)}
        mapping_path = prefix.with_suffix(".mapping.json"); write(mapping_path, mapping)
        prior_rows = comparison["windows"][0]["cohorts"]
        cache = {_program_key(c): c for c in prior_rows if c["status"] == "compared"}
        fresh = [c for c in cohorts if _program_key(c) not in cache]
        new_mapping = {**mapping, "windows": [{**mapping["windows"][0], "cohorts": fresh}]}
        fresh_path = prefix.with_suffix(".new-program-mapping.json"); write(fresh_path, new_mapping)
        added = compare_programs(args, prefix, actual_path, fresh_path, case, new_mapping)
        new_rows = {c["cohort_id"]: c for c in added["windows"][0]["cohorts"]}
        combined = [c for c in prior_rows if c["native_operator_type"] != "MatMulV3"]
        for c in cohorts:
            combined.append(new_rows[c["cohort_id"]] if c["cohort_id"] in new_rows else
                reuse_comparison(c, cache[_program_key(c)], manifest, mapping["windows"][0], old["comparison_identity"]))
        merged = {**comparison, "windows": [{**mapping["windows"][0], "cohorts": combined}],
            "status_counts": dict(Counter(c["status"] for c in combined)),
            "prior_program_cost_receipt": old["comparison_identity"],
            "additional_program_receipts": added["program_receipts"],
            "new_physical_programs": added["attempted_physical_programs"],
            "same_runtime_reused_matrix_cohorts": len(cohorts) - len(fresh), "raw_capture_reads": 0}
        comparison_path = prefix.with_suffix(".comparison.json"); write(comparison_path, merged)
        matrix_rows = family_rows({**updated_actual, "families": matrices}, mapping, merged, {})
        all_families = [f for f in old["families"] if f["native_operator_type"] != "MatMulV3"] + matrix_rows
        if sum(f["observed_us"]["count"] for f in all_families) != sum(f["observed_us"]["count"] for f in old["families"]):
            raise ValueError("full_body_event_population_changed")
        row = {**old, "case_id": source_id + " / logical96-full-matrix", "variant": "logical96-full-matrix",
            "actual_identity": identity(actual_path), "mapping_identity": identity(mapping_path),
            "comparison_identity": identity(comparison_path), "families": all_families,
            "passed_cohorts": sum(f["passed_cohort_count"] for f in all_families),
            "comparison_status_counts": merged["status_counts"],
            "matrix_role_refresh": {"previous_case_detail_identity": compact["case_detail_identity"],
                "partition_identity": identity(part_path), "decisions": decisions,
                "histogram_exactly_conserved": True, "prior_strict_events": sum(f["scored_event_count"] for f in old["families"]),
                "current_strict_events": sum(f["scored_event_count"] for f in all_families),
                "new_physical_programs": added["attempted_physical_programs"],
                "same_runtime_reused_matrix_cohorts": len(cohorts) - len(fresh)}}
        detail = {"schema_version": parent["schema_version"], "cases": [row], "runtime_source_identity": before,
                  "raw_capture_reads": 0, "observed_partition_source": identity(part_path)}
        detail_path = prefix.with_suffix(".family-scoreboard.json"); write(detail_path, detail)
        rows.append({**compact_case(row), "case_detail_identity": identity(detail_path)})
        total_new += added["attempted_physical_programs"]; total_reused += len(cohorts) - len(fresh)
        print(source_id, row["matrix_role_refresh"]["prior_strict_events"], row["matrix_role_refresh"]["current_strict_events"], flush=True)
    if runtime_identity() != before or identity(Path(__file__)) != own_source:
        raise ValueError("runtime_or_generator_changed")
    failed = any(row["comparison_status_counts"].get("prediction_failed") for row in rows)
    result = {**{key: value for key, value in parent.items() if key != "cases"}, "cases": rows,
        "status": "partial" if failed else "completed", "generator_identity": own_source,
        "prior_full_family_receipt": identity(args.previous), "runtime_source_identity": before,
        "elapsed_seconds": time.perf_counter() - started, "new_physical_programs": total_new,
        "same_runtime_reused_matrix_cohorts": total_reused, "raw_capture_reads": 0,
        "maximum_resident_set_size_bytes": _rss(), "coverage_status": "partial",
        "successful_same_runtime_predictions_reused": True, "previous_runtime_predictions_reused": False}
    if result["maximum_resident_set_size_bytes"] > 512 * 1024**2:
        raise MemoryError("matrix_rebind_exceeds_512MiB")
    write(args.output_dir / "body-operator-family-scoreboard.json", result)
    (args.output_dir / "body-operator-family-scoreboard.md").write_text(render_repriced(result))
    if failed:
        raise SystemExit("matrix_rebind_contains_visible_prediction_failures")


if __name__ == "__main__":
    main()
