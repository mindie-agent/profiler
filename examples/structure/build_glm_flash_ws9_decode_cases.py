"""Bind the seven retained GLM Flash captures to source-declared Sim cases.

[Role] Construct replay inputs without reconstructing the model in profiler.
[Invariants] The 45-layer KDA/MLA body is distinct from GLM78. Client TPOT,
  configured MTP acceptance and measured per-forward execution geometry differ.
[Timeouts & Locks] Bounded metadata reads; source hashes come from the inventory.
[Side-Effect Policy] Writes one local manifest; no capture or model mutation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mindie_sim.prediction.structure import parse_case

from inspect_glm78_v41_assets import identity, read


def build(evidence_path, case_dir, output):
    inventory = read(evidence_path)
    sources = {row["capture_directory"]: row for row in inventory["cases"]
               if row["group"] == "a5_glm_flash45"}
    rows = []
    for model_path in sorted(case_dir.glob("a5_glm53flash_tp8_c*_p*k.json")):
        raw = read(model_path)
        case = parse_case(raw)
        metadata = raw["runtime"]["metadata"]
        source = sources[metadata["capture_directory"]]
        if (case.model.layers, case.runtime.parallel.tp, case.runtime.parallel.dp,
                case.runtime.parallel.ep) != (45, 8, 1, 1):
            raise ValueError(f"Unexpected GLM Flash topology: {model_path}")
        for key in ("startup",):
            pin = metadata[key]
            if identity(Path(pin["path"]))["sha256"] != pin["sha256"]:
                raise ValueError(f"Changed source metadata: {pin['path']}")
        if metadata["client_summary"]["sha256"] != source["benchmark"]["source"]["sha256"]:
            raise ValueError(f"Capture and case benchmark differ: {model_path}")
        # The producer retained the exact raw profile under its explicit evidence
        # filename while replacing benchmark_summary with a clean/profile report.
        profile_path = Path(source["capture_directory"]) / "profile_evidence.json"
        profile_pin = identity(profile_path)
        if profile_pin["sha256"] != metadata["client_summary"]["sha256"]:
            raise ValueError(f"Relocated raw profile differs from case pin: {profile_path}")
        summary_path = Path(source["capture_directory"]) / "benchmark_summary.json"
        summary = read(summary_path)
        profile_tpot = source["benchmark"]["profiled_token_tpot_p50_ms"]
        if summary["tpot_samples"]["profiled_client_p50_ms"] != profile_tpot:
            raise ValueError(f"Profile TPOT differs from retained raw evidence: {summary_path}")
        rows.append({
            "case_id": model_path.stem, "source": source["source"],
            "sim_case_path": str(model_path), "model_declaration": identity(model_path),
            "segmentation": "auto_structure_guided", "boundaries_path": None, "geometry": None,
            "scenario_evidence": {
                "capture_directory": source["capture_directory"],
                "retained_inventory": identity(evidence_path),
                "benchmark_summary": identity(summary_path),
                "profile_evidence": profile_pin,
                "original_case_profile_pin": metadata["client_summary"],
                "profile_relocation_basis": "byte-identical SHA256; producer renamed the original raw profile and added a clean/profile summary",
                "client": metadata["client"],
                "tpot": {"profiled_run_client_p50_ms": profile_tpot,
                         "unprofiled_clean_sweep_p50_ms": summary["headline_tpot_ms"]["value"],
                         "body_forward_is_separate_metric": True},
                "startup": metadata["startup"],
                "resolved_configuration_lines": metadata["resolved_configuration_lines"],
                "checkpoint": metadata["checkpoint"],
                "force_load_balance": metadata["force_eplb"],
                "expert_parallel": metadata["expert_parallel"],
                "graph_native_mode": metadata["graph_native_mode"],
                "prefix_cache": metadata["prefix_cache"],
                "unprofiled_clean_sweep_prefix": summary["clean_sweep_cell"]["prefix"],
                "prefix_cache_protocol": summary["prefix_cache_protocol"],
                "speculation": metadata["speculative"],
                "observed_accept_ratio": metadata["observed_accept_ratio"],
                "selected_rank": source["selected_rank"],
                "request_geometry_is_not_per_forward_geometry": True,
            },
            "unresolved_reasons": metadata["unresolved_capture_contracts"],
        })
    if len(rows) != len(sources) or len(rows) != 7:
        raise ValueError(f"Expected seven distinct source-bound cases, got {len(rows)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": "mindie-decode-forward-replay/1",
                                 "not_new_live_collection": True, "cases": rows},
                                ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "output": str(output), "sha256": identity(output)["sha256"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).parent
    parser.add_argument("--evidence", type=Path, default=here / "acceptance-20261030-bundle0406/retained-source-evidence.json")
    parser.add_argument("--case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/glm-flash-ws9"))
    parser.add_argument("--output", type=Path, default=here / "acceptance-20261030-glm-flash-ws9/decode-forward-auto-cases.json")
    args = parser.parse_args()
    build(args.evidence, args.case_dir, args.output)
