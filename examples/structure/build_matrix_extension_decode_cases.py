"""Bind seven retained V4.1 / GLM Flash matrix-extension captures to Sim cases.

[Role] Metadata-only join of source-pinned captures and the Sim structural frontend.
[Invariants] Startup facts, launch intent and measured client metrics stay separate.
  Client concurrency does not establish execution batch or per-step cache context.
[Timeouts & Locks] Bounded metadata reads; no raw event scans or locks.
[Side-Effect Policy] Writes a local replay manifest, never edits cases or captures.
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
    sources = {row["capture_directory"]: row for row in inventory["cases"]
               if row["group"] in {"a5_v41_dp8", "a3_glmflash45_aclgraph"}}
    rows = []
    for model_path in sorted(case_dir.glob("*.json")):
        raw = read(model_path)
        metadata = raw["runtime"]["metadata"]
        source = sources[metadata["capture_directory"]]
        case = parse_case(raw)
        is_v41 = source["group"] == "a5_v41_dp8"
        expected = (40, 1, 8, 8) if is_v41 else (45, 16, 1, 16)
        if (case.model.layers, case.runtime.parallel.tp,
                case.runtime.parallel.dp, case.runtime.parallel.ep) != expected:
            raise ValueError(f"Unexpected declared topology: {model_path}")
        summary = metadata["summary_source" if is_v41 else "client_summary"]
        for pin in [summary, *([] if is_v41 else [metadata["launch_source"], metadata["profile_cell"]])]:
            if identity(Path(pin["path"]))["sha256"] != pin["sha256"]:
                raise ValueError(f"Changed metadata source: {pin['path']}")
        if summary["sha256"] != source["benchmark"]["source"]["sha256"]:
            raise ValueError(f"Inventory and declared client summary differ: {model_path}")
        row = {"case_id": model_path.stem, "source": source["source"],
            "sim_case_path": str(model_path), "model_declaration": identity(model_path),
            "segmentation": "auto_structure_guided", "boundaries_path": None, "geometry": None,
            "scenario_evidence": {
                "capture_directory": source["capture_directory"],
                "retained_inventory": identity(evidence_path),
                "client": metadata["profiled_client" if is_v41 else "client"],
                "benchmark_summary": summary,
                "retained_deployment": source["deployment_evidence"],
                "graph_native_mode": metadata["graph_native_mode"],
                "prefix_cache": metadata["prefix_cache"],
                "force_load_balance": metadata["force_eplb"],
                "speculation": metadata["speculation" if is_v41 else "speculative"],
                "selected_rank": metadata.get("selected_rank", source["selected_rank"]),
                "request_geometry_is_not_per_forward_geometry": True,
                "body_forward_is_separate_from_client_tpot": True,
                "metadata_source_link": source.get("metadata_source_link"),
            }, "unresolved_reasons": metadata["unresolved_capture_contracts"]}
        if is_v41:
            pin = metadata["kernel_source"]
            if pin["path"] != source["source"]["path"] or pin["bytes"] != source["source"]["size_bytes"]:
                raise ValueError(f"Declared source location differs: {model_path}")
            row["segmentation_options"] = source_segmentation_options(metadata)
            row["scenario_evidence"]["native_attention_source_condition"] = metadata["native_attention"]
        rows.append(row)
    if len(rows) != 7 or len(rows) != len(sources):
        raise ValueError(f"Expected seven matrix-extension captures, got {len(rows)}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"schema_version": "mindie-decode-forward-replay/1",
                                 "cases": rows, "not_new_live_collection": True},
                                ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"case_count": len(rows), "manifest": identity(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).parent
    parser.add_argument("--evidence", type=Path, default=here / "acceptance-20261030-additional13/retained-source-evidence.json")
    parser.add_argument("--case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030/matrix-extension"))
    parser.add_argument("--output", type=Path, default=here / "acceptance-20261030-matrix-extension/decode-forward-auto-cases.json")
    args = parser.parse_args()
    build(args.evidence, args.case_dir, args.output)
