"""Prepare explicit GLM source-mechanism inputs without changing original cases.

[Role] Extend reviewed Flash source declarations with symbolic accepted-state KDA.
[Invariants] Full GLM models without KDA retain their own rope/cache declarations.
  Primary observed geometry selects index stride, not accepted-token values.
  Source selection remains conditional; no measured latency enters a recipe.
[Timeouts & Locks] Sequential small metadata reads, no workers or locks.
[Side-Effect Policy] Write a separate Sim case prefix and profiler input plan only.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from replay_body_operator_families import identity, read, write


def operator_inputs(plan, operator_manifest, output_dir):
    """Locate complete retained observations; never fill a missing population."""
    import ijson
    wanted = {row["case_id"]: row for row in plan["cases"] if row["kda_layer_ids"]}
    found = {}
    for name in read(operator_manifest)["operators"]:
        path = Path(name)
        path = path if path.is_absolute() else operator_manifest.parent / path
        with path.open("rb") as stream:
            for case in ijson.items(stream, "cases.item"):
                cid = case["source_case_id"]
                if cid in wanted:
                    found[cid] = {"actual_identity": case["actual_identity"],
                                  "mapping_identity": case["mapping_identity"],
                                  "prior_comparison_receipt": identity(path)}
    for path in (output_dir / "retained-four-actual").rglob("*.actual.json"):
        actual = read(path)
        found[actual["source_case_id"]] = {"actual_identity": identity(path),
            "mapping_identity": identity(Path(str(path).replace(".actual.json", ".mapping.json"))),
            "prior_comparison_receipt": None}
    records = []
    for cid, row in wanted.items():
        if cid not in found:
            records.append({"case_id": cid, "status": "complete_operator_observation_missing"})
            continue
        inputs = found[cid]
        actual = read(inputs["actual_identity"]["path"])
        if (actual["source_identity"] != row["source_identity"]
                or actual["geometry"] != row["geometry"]
                or actual["forward_count"] != row["selected_forwards"]):
            raise ValueError("operator_observation_not_primary_body_population:" + cid)
        records.append({"case_id": cid, "status": "ready_for_fresh_runtime_reprice",
            **inputs, "selected_case_identity": row["selected_case_identity"],
            "geometry": row["geometry"], "forward_count": actual["forward_count"],
            "conditional_operator_context_tokens": actual["conditional_context_tokens"],
            "conditional_body_context_tokens": row["conditional_context_tokens"],
            "context_policy": "Retain each campaign's declared context; no silent operator/body equivalence."})
    write(output_dir / "operator-reprice-inputs.json", {"schema_version": "mindie-glm-source-reprice-inputs/1",
        "status": "prepared_not_predicted", "operator_manifest_identity": identity(operator_manifest),
        "source_case_plan_identity": identity(output_dir / "source-case-plan.json"), "cases": records,
        "raw_capture_reads": 0, "prediction_executions": 0})


def build(sim_root, input_manifest, output_dir):
    from mindie_sim.prediction.structure import parse_case
    base = sim_root / "examples/cases/high-concurrency-20261030"
    destination = base / "glm-source-accepted-26"
    destination.mkdir(exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    source = read(input_manifest)
    planned, replay = [], []
    for entry in source["cases"]:
        case_id = entry["case_id"]
        relative = Path(entry["sim_case_path"]).as_posix().split("/examples/cases/", 1)[1]
        original_path = sim_root / "examples/cases" / relative
        original = read(original_path)
        parsed = parse_case(original)
        plans = parsed.model.layer_plans
        kda_layers = [plan.index for plan in plans if plan.attention == "kda" and not plan.mtp]
        observation = read(Path(entry["extraction_path"]))
        primary = max(observation["geometry_groups"], key=lambda g: g["body_forward_span_ms"]["count"])
        geometry = primary["geometry"]
        q, batch = geometry["tokens_per_sequence"], geometry["sequences_per_replica"]
        context = entry["geometry"]["context_tokens"]
        row = {"case_id": case_id, "source_identity": observation["source_identity"],
            "extraction_identity": identity(Path(entry["extraction_path"])),
            "original_case_identity": identity(original_path), "geometry": geometry,
            "conditional_context_tokens": context,
            "selected_forwards": primary["body_forward_span_ms"]["count"],
            "source_forwards": observation["body_forward_span_ms"]["count"], "kda_layer_ids": kda_layers}
        case_entry = deepcopy(entry)
        if not kda_layers:
            row.update(status="existing_full_glm_preserved", selected_case_identity=identity(original_path),
                reason="No KDA body layers; the Flash rope0/packed528 and accepted-state mechanisms do not apply.",
                mechanism_changes=[], original_rope_cache_declaration_preserved=True)
            case_entry["sim_case_path"] = str(original_path.resolve())
        else:
            sku = original["machine"]["sku"]
            if sku == "Ascend950DT_9582":
                suffix, prototype_name = "attention-plus-down", "glm53flash-a5-b32-q4.json"
            elif sku == "Ascend910_9362":
                suffix, prototype_name = "attention-only", "glm53flash-a3-b4-q6.json"
            else:
                raise ValueError("unreviewed_glm_source_architecture:" + sku)
            baseline_path = base / "glm-compatible-variants" / (case_id + "--" + suffix + ".json")
            prototype_path = base / "glm-kda-accepted-conditional" / prototype_name
            baseline, prototype = read(baseline_path), read(prototype_path)
            selected = deepcopy(baseline)
            lowering = deepcopy(prototype["runtime"]["kernels"]["lowerings"]["kda"])
            lowering["options"]["state_selection"]["index_row_stride"] = q
            selected["runtime"]["kernels"].setdefault("lowerings", {})["kda"] = lowering
            model_metadata = selected["model"].setdefault("metadata", {})
            for key, obsolete in (("unmodeled_features", "KDA_nonempty_accepted_token_state_ABI_not_source_bound"),
                                  ("degraded_submodules", "KDA_analytic_state_boundary")):
                model_metadata[key] = [value for value in model_metadata.get(key, []) if value != obsolete]
            metadata = selected["runtime"].setdefault("metadata", {})
            metadata["compatible_variant"]["KDA"] = "explicit symbolic accepted-state source reference; captured values and flags unobserved"
            metadata["accepted_state_scenario"] = {
                "id": case_id, "baseline": identity(baseline_path), "prototype": identity(prototype_path),
                "tokens_per_sequence": q, "sequences_per_replica": batch, "context_tokens": context,
                "scope": "body", "source_architecture": "arch35" if suffix.endswith("down") else "arch22",
                "value_identity": "not_established", "acceptance_changes_query_work": False,
                "sigmoid_placement": "explicit in-kernel scenario, not inferred from BF16 beta",
                "private_external_fp32_sigmoid_boundary": "not_matched_by_this_conditional_native_program",
                "observed_geometry_identity": identity(Path(entry["extraction_path"]))}
            selected["name"] = case_id + ":source-accepted-conditional"
            path = destination / (case_id + ".json")
            if path.exists() and read(path) != selected:
                raise ValueError("reviewed_source_variant_changed:" + str(path))
            if not path.exists():
                path.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + "\n")
            check = parse_case(selected)
            if check.runtime.parallel != parsed.runtime.parallel or check.machine != parsed.machine:
                raise ValueError("source_variant_changed_hardware_or_parallel")
            row.update(status="conditional_source_declaration_prepared",
                selected_case_identity=identity(path), baseline_identity=identity(baseline_path),
                prototype_identity=identity(prototype_path), mechanism_changes=[suffix, "symbolic_accepted_state_kda"],
                native_accepted_values_known=False, native_sigmoid_placement_known=False,
                strict_capture_binding_implied=False, full_native_abi_validation="required_per_retained_operator_bucket")
            case_entry["sim_case_path"] = str(path.resolve())
        case_entry["sim_case_identity"] = row["selected_case_identity"]
        case_entry["variant_id"] = "glm-source-accepted-conditional"
        planned.append(row)
        replay.append(case_entry)
    plan = {"schema_version": "mindie-glm-source-case-plan/1", "input_identity": identity(input_manifest),
        "status": "prepared_not_predicted", "raw_capture_reads": 0, "prediction_executions": 0,
        "cases": planned}
    write(output_dir / "source-case-plan.json", plan)
    write(output_dir / "decode-forward-glm-cases.json", {**source, "cases": replay,
        "variant_id": "glm-source-accepted-conditional", "case_plan_identity": identity(output_dir / "source-case-plan.json")})
    return plan


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sim-root", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--operator-manifest", type=Path,
                        help="Index complete retained family observations for fresh repricing")
    args = parser.parse_args()
    plan = build(args.sim_root, args.input_manifest, args.output_dir)
    if args.operator_manifest:
        operator_inputs(plan, args.operator_manifest, args.output_dir)
    print({"cases": len(plan["cases"]), "source_variants": sum(row["status"] == "conditional_source_declaration_prepared" for row in plan["cases"])})
