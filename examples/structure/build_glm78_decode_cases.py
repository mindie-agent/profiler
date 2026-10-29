"""Bind the three retained GLM78 TP16 captures to audited Sim cases.

[Role] Build the shared automatic Decode manifest without defining a model.
[Invariants] Sim owns the model/placement; measured client metrics and configured
  synthetic acceptance/force balance remain separate from device geometry.
[Timeouts & Locks] Bounded local JSON metadata only; no device event parsing.
[Side-Effect Policy] Writes a replay manifest; does not mutate source Sim cases.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mindie_sim.prediction.structure import parse_case
import mindie_sim.prediction.structure as sim_structure

from inspect_glm78_v41_assets import identity, read


def build(evidence_path, model_paths, output):
    evidence = read(evidence_path)
    captures = evidence["glm78_device_captures"]
    if len(model_paths) != len(captures):
        raise ValueError("Provide one audited Sim case for tpot30_c2, tpot50_c2 and tpot88_c8.")
    rows = []
    for capture, model_path in zip(captures, model_paths):
        case = parse_case(read(model_path))
        parallel = case.runtime.parallel
        if (case.model.layers, case.model.hidden_size, case.model.vocab_size,
                parallel.tp, parallel.dp, parallel.ep) != (78, 6144, 154880, 16, 1, 16):
            raise ValueError(f"This source requires the GLM78 TP16/DP1/EP16 declaration: {model_path}")
        profiled = capture["profiled_client"]
        sweep = next(row for row in capture["unprofiled_sweep"]["cells"]
                     if row["concurrency"] == profiled["concurrency"])
        rows.append({
            "case_id": capture["case_id"], "source": capture["selected_source"],
            "sim_case_path": str(model_path),
            "model_declaration": {**identity(model_path), "basis": "source_bound_sim_declaration"},
            "segmentation": "auto_structure_guided", "boundaries_path": None, "geometry": None,
            "scenario_evidence": {
                "retained_evidence": identity(evidence_path), "capture_directory": capture["asset_root"],
                "client": {key: profiled[key] for key in ("concurrency", "input_len", "output_len", "token_exact")},
                "benchmark_summary": profiled["source"],
                "tpot": {"profiled_run_client_ms": profiled["tpot_ms"],
                         "unprofiled_sweep_ms": sweep["tpot_median"],
                         "unprofiled_sweep_population": sweep["tpot_source"],
                         "unprofiled_sweep_source": capture["unprofiled_sweep"]["source"],
                         "body_forward_is_separate_metric": True},
                "retained_deployment": capture["launch_declaration"],
                "source_population": {"selected_rank": "tp0", "available_rank_directories": [
                    rank["rank"] for rank in capture["retained_ranks"]],
                    "all_ranks_are_not_summed": True,
                    "top_csv_verified_identical_to_rank0_gzip": True},
                "step_trace": capture["step_trace"],
                "force_load_balance": {"value": None, "configured": True,
                                       "basis": "launch_script; actual_expert_distribution_not_measured"},
                "acceptance": {"configured_method": "synthetic",
                               "configured_marginals": capture["launch_declaration"]["synthetic_acceptance_rates"],
                               "measured_rate": None},
                "prefix_cache": {"profiled_metrics": None,
                                 "unprofiled_metrics": sweep["prefix_cache_metrics"],
                                 "unknown_metrics_are_not_zero": True},
                "request_geometry_is_not_per_forward_geometry": True,
                "prefix_and_acceptance": {"configured_values_are_not_measured_rates": True},
            },
            "unresolved_reasons": ["exact_per_forward_context_unencoded", "resolved_startup_log_not_retained",
                                   "profiled_prefix_hit_and_actual_expert_balance_not_measured"],
        })
    manifest = {"schema_version": "mindie-decode-forward-replay/1", "cases": rows,
                "source_evidence": identity(evidence_path), "not_new_live_collection": True,
                "structural_frontend": {**identity(Path(sim_structure.__file__)),
                                        "use": "model metadata only; no cost prediction"}}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "output": str(output), "sha256": identity(output)["sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).with_name("acceptance-20261030-glm78-v41")
    parser.add_argument("--evidence", type=Path, default=base / "retained-source-evidence.json")
    parser.add_argument("--sim-case", type=Path, action="append", required=True,
                        help="In order: tpot30_c2, tpot50_c2, tpot88_c8.")
    parser.add_argument("--output", type=Path, default=base / "decode-forward-auto-cases.json")
    args = parser.parse_args()
    build(args.evidence, args.sim_case, args.output)
