"""Bind V4.1 final-six captures to source-declared target-body closure rules.

[Role] Reuse Sim cases and pinned launch/source evidence for profiling extraction.
[Invariants] A3 attention supplies measured query geometry; local hidden rows,
  routed buffers and DSpark-selected logits never substitute for query tokens.
[Timeouts & Locks] Bounded metadata only; no event parsing or device work.
[Side-Effect Policy] Writes one local replay manifest; source cases remain intact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mindie_sim.prediction.structure import parse_case

from build_v41_decode_cases import source_segmentation_options
from inspect_glm78_v41_assets import identity, read


def build(evidence_path, case_dir, output):
    inventory = read(evidence_path)
    sources = {row["capture_directory"]: row for row in inventory["cases"]}
    rows = []
    for path in sorted(case_dir.glob("*.json")):
        raw = read(path)
        metadata = raw["runtime"]["metadata"]
        source = sources[metadata["capture_directory"]]
        case = parse_case(raw)
        a3 = source["group"] == "a3_v41_dspark7_tp4_dp4_ep16"
        expected = (40, 4, 4, 16) if a3 else (40, 1, 8, 8)
        if (case.model.layers, case.runtime.parallel.tp, case.runtime.parallel.dp,
                case.runtime.parallel.ep) != expected:
            raise ValueError(f"Source-specific V4.1 topology differs: {path}")
        if metadata["kernel_source"] != source["source"]:
            raise ValueError(f"Source identity differs from inventory: {path}")
        pin = metadata["launch"]
        if identity(Path(pin["path"]))["sha256"] != pin["sha256"]:
            raise ValueError(f"Retained launch changed: {pin['path']}")
        if a3:
            reference = metadata["bounded_physical_rows_reference"]
            if identity(Path(reference["path"]))["sha256"] != reference["sha256"]:
                raise ValueError(f"Physical-row evidence identity differs: {reference['path']}")
            options = {"forward_closure": "mhc_final_norm", "sequence_parallel": {
                "factor": 4, "source": pin,
                "basis": "source declares TP4 and FlashComm1; each occurrence must independently match hidden-shard rows times four to captured SparseFlashMla query rows",
                "bounded_source_validation": reference}}
        else:
            options = source_segmentation_options(metadata)
        summary = source["benchmark"]
        rows.append({"case_id": path.stem, "source": source["source"],
            "sim_case_path": str(path), "model_declaration": identity(path),
            "segmentation": "auto_structure_guided", "segmentation_options": options,
            "boundaries_path": None, "geometry": None,
            "scenario_evidence": {"capture_directory": source["capture_directory"],
                "retained_inventory": identity(evidence_path), "client": metadata["client"],
                "benchmark_summary": summary["source"],
                "tpot": {"profiled_run_client_ms": {"median": summary["profiled_token_tpot_p50_ms"]},
                         "body_forward_is_separate_metric": True},
                "deployment_evidence": metadata["deployment_evidence"],
                "prefix_cache": metadata["prefix_cache"],
                "speculation": metadata["speculation"],
                "graph_native_mode": metadata["graph_native_mode"],
                "selected_rank": metadata["selected_rank"],
                "selected_rank_alias": source.get("selected_rank_alias"),
                "request_geometry_is_not_per_forward_geometry": True,
                "hidden_shard_rows_and_routed_capacity_are_not_query_rows": True},
            "unresolved_reasons": metadata["unresolved_capture_contracts"]})
    if len(rows) != 6:
        raise ValueError(f"Expected six source-bound cases, got {len(rows)}")
    output.write_text(json.dumps({"schema_version": "mindie-decode-forward-replay/1",
                                 "cases": rows, "not_new_live_collection": True},
                                ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"cases": len(rows), "manifest": identity(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).with_name("acceptance-20261030-v41-final6")
    parser.add_argument("--evidence", type=Path, default=base / "retained-source-evidence.json")
    parser.add_argument("--case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/v41-new6"))
    parser.add_argument("--output", type=Path, default=base / "decode-forward-auto-cases.json")
    args = parser.parse_args()
    build(args.evidence, args.case_dir, args.output)
