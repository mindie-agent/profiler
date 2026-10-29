"""Bind source-pinned V4.1 captures to the existing Sim frontend and closure evidence.

[Role] Declare conditional attention anchors and the real terminal-norm boundary.
[Invariants] No observed tensor ABI is fabricated for MqsmlaKernel___call__.
  Model/layer plans come from each audited Sim case, never the test fixture.
[Timeouts & Locks] Bounded metadata only; source CSV hashes are reused here.
[Side-Effect Policy] Writes a replay manifest; no source model or capture mutation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mindie_sim.prediction.structure import parse_case

from inspect_glm78_v41_assets import identity, read


def source_segmentation_options(metadata):
    """Reuse the audited source boundary without inventing native tensor shapes."""
    native = metadata["native_attention"]
    for pin in (native["dsl"], metadata["startup"]):
        if identity(Path(pin["path"]))["sha256"] != pin["sha256"]:
            raise ValueError(f"Source evidence changed: {pin['path']}")
    return {
        "source_attention_anchors": [{"op_type": "MqsmlaKernel___call__",
            "name": "mixed_quant_sparse_flash_mla", "attention": "mla",
            "evidence": native["dsl"], "binary_identity": native["binary_identity"]}],
        "source_decode_query": {"tokens_per_sequence": 1,
            "basis": "source_declared_no_speculation_decode_capture",
            "evidence": metadata["startup"], "lines": metadata["startup_contract_lines"]},
        "forward_closure": "mhc_final_norm",
    }


def build(evidence_path, case_dir, output):
    evidence = read(evidence_path)
    rows = []
    for source in evidence["cases"]:
        model_path = case_dir / f"{source['case_id']}.json"
        raw = read(model_path)
        model = parse_case(raw)
        metadata = raw["runtime"]["metadata"]
        if (model.model.layers, model.model.hidden_size, model.runtime.parallel.tp,
                model.runtime.parallel.dp, model.runtime.parallel.ep) != (40, 5120, 1, 8, 8):
            raise ValueError(f"Expected the source-bound V4.1 TP1/DP8/EP8 body: {model_path}")
        if metadata["kernel_source"] != source["source"]:
            raise ValueError(f"Sim case and capture identities differ: {model_path}")
        native = metadata["native_attention"]
        options = source_segmentation_options(metadata)
        profiled = source["profiled_client"]
        rows.append({"case_id": source["case_id"], "source": source["source"],
            "sim_case_path": str(model_path), "model_declaration": identity(model_path),
            "segmentation": "auto_structure_guided", "segmentation_options": options,
            "boundaries_path": None, "geometry": None,
            "scenario_evidence": {"capture_directory": source["capture_directory"],
                "retained_inventory": identity(evidence_path),
                "client": {"concurrency": profiled["concurrency"], "input_len": profiled["prefix_len"],
                           "output_len": profiled["output_len"]},
                "benchmark_summary": source["profile_summary"],
                "tpot": {"profiled_run_client_ms": profiled["tpot_tok_ms"],
                         "unprofiled_sweep_ms": source["unprofiled_sweep"]["tpot_tok_ms"]["p50"],
                         "body_forward_is_separate_metric": True},
                "profile_window": profiled["profile_window"], "startup": metadata["startup"],
                "engine_config": metadata["engine_config"], "source_condition": native,
                "graph_native_mode": metadata["graph_native_mode"],
                "speculation": metadata["speculation"], "prefix_cache": metadata["prefix_cache"],
                "force_load_balance": metadata["force_eplb"], "selected_rank": metadata["selected_rank"],
                "request_geometry_is_not_per_forward_geometry": True,
                "forward_boundary": "40 complete declared layers, terminal mHC final-norm closure; any separately recorded LMHead remains outside the body",
                "other_dp_replicas_are_not_summed": True},
            "unresolved_reasons": metadata["unresolved_capture_contracts"],
        })
    result = {"schema_version": "mindie-decode-forward-replay/1", "cases": rows,
              "not_new_live_collection": True,
              "basis": "Sim-declared topology with source-conditional native attention and terminal-norm closure"}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "output": str(output), "sha256": identity(output)["sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).with_name("acceptance-20261030-v41-dp8")
    parser.add_argument("--evidence", type=Path, default=base / "retained-source-evidence.json")
    parser.add_argument("--case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/v41-dp8"))
    parser.add_argument("--output", type=Path, default=base / "decode-forward-auto-cases.json")
    args = parser.parse_args()
    build(args.evidence, args.case_dir, args.output)
