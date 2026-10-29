"""Bind retained Kimi captures to source-specific Sim declarations.

[Role] Prepare the A5 BF16 93-layer and A3 W4A8 four-layer extraction queue.
[Invariants] Match source identity, not a model-name alias or client concurrency.
  Per-forward batch comes from tensors; prompt length is only conditional context.
[Timeouts & Locks] Bounded metadata reads; existing streamed source hashes reused.
[Side-Effect Policy] Writes a local manifest; no model/capture mutation or cost run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mindie_sim.prediction.structure import parse_case

from inspect_glm78_v41_assets import identity, read


def build(inventories, case_dir, output):
    sources = {}
    for inventory in inventories:
        pin = identity(inventory)
        for row in read(inventory)["cases"]:
            if row["group"] in {"a5_kimi_tp8_ep8", "a3_kimi_4layer"}:
                key = row["capture_directory"]
                if key in sources:
                    raise ValueError(f"Repeated Kimi capture: {key}")
                sources[key] = row, pin
    rows = []
    for model_path in sorted(case_dir.glob("*.json")):
        raw = read(model_path)
        metadata = raw["runtime"]["metadata"]
        source, inventory_pin = sources.pop(metadata["capture_directory"])
        selected = metadata["selected_source"]
        if (any(selected[key] != source["source"][key] for key in ("path", "size_bytes"))
                or selected.get("sha256", source["source"]["sha256"]) != source["source"]["sha256"]):
            raise ValueError(f"Case source identity differs: {model_path}")
        case = parse_case(raw)
        declared = source["deployment_evidence"]["configured"]
        placement = case.runtime.parallel
        if (case.model.layers, placement.tp, placement.dp, placement.ep) != (
                declared["model_body_layers"], declared["tp"], declared["dp"], declared["ep"]):
            raise ValueError(f"Case model/placement differs from source declaration: {model_path}")
        benchmark = source["benchmark"]
        summary = benchmark["summary"]
        prompts = benchmark["observed_prompt_tokens"]
        completions = benchmark["observed_completion_tokens"]
        tpot = summary.get("tpot_ms", summary.get("tpot_tok_ms"))
        if tpot is None:
            tpot = {"p50": benchmark["profiled_token_tpot_p50_ms"]}
        rows.append({
            "case_id": model_path.stem, "source": source["source"],
            "sim_case_path": str(model_path), "model_declaration": identity(model_path),
            "segmentation": "auto_structure_guided", "boundaries_path": None,
            "geometry": None, "scenario_evidence": {
                "capture_directory": source["capture_directory"],
                "retained_inventory": inventory_pin,
                "case_source_identity_basis": "case path/size and inventory SHA; replay verifies full source SHA",
                "client": {"concurrency": benchmark["client_concurrency"],
                           "input_len": prompts[0] if len(prompts) == 1 else None,
                           "observed_prompt_tokens": prompts,
                           "output_len": completions[0] if len(completions) == 1 else None},
                "benchmark_summary": benchmark["source"],
                "tpot": {"profiled_run_client_ms": tpot,
                         "unprofiled_sweep_ms": None,
                         "body_forward_is_separate_metric": True},
                "retained_deployment": source["deployment_evidence"],
                "captured_execution_mode": metadata["captured_execution_mode"],
                "prefix_cache": metadata["prefix_cache"],
                "force_load_balance": {"configured": declared["force_eplb"],
                                       "observed": source["deployment_evidence"]["actual_force_eplb"]},
                "speculation": metadata["speculation"],
                "source_population": {"selected_rank": source["selected_rank"],
                                      "body_layers": case.model.layers},
                "request_geometry_is_not_per_forward_geometry": True,
                "context_basis": "initial prompt length; active per-forward KV growth is not observed",
                "layer_binding_basis": "Sim-declared topology and tensor anchors, not Host/module evidence",
            },
            "unresolved_reasons": metadata["unresolved_capture_contracts"],
        })
    if sources:
        raise ValueError(f"Source-bound Sim declarations are missing: {sorted(sources)}")
    result = {"schema_version": "mindie-decode-forward-replay/1", "cases": rows,
              "not_new_live_collection": True,
              "basis": "Independent source-bound Kimi variants; 93-layer A5 and four-layer A3 stay separate"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return {"cases": len(rows), "output": str(output), "sha256": identity(output)["sha256"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parent
    parser.add_argument("--inventory", type=Path, action="append")
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=base / "acceptance-20261030-kimi-variants" / "decode-forward-auto-cases.json")
    args = parser.parse_args()
    inventories = args.inventory or [base / name / "retained-source-evidence.json" for name in (
        "acceptance-20261030-bundle0406", "acceptance-20261030-additional13")]
    print(json.dumps(build(inventories, args.case_dir, args.output)))
