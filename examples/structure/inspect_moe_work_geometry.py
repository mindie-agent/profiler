"""Inspect one aligned layer's routed tensors against existing Sim declarations.

[Role] Expose physical grouped-MoE work mismatches before latency calibration.
[Invariants] Captured tensor rows and declared probability moments stay separate;
  neither output token counts nor timing prove a router distribution per expert.
[Timeouts & Locks] Bounded CSV scan to one accepted layer, no prediction or locks.
[Side-Effect Policy] Local reads and a compact evidence JSON; no device workload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from mindie_profiler.normalized import kernel_rows
from mindie_sim import target_graphs
from mindie_sim.prediction.structure import parse_case
from replay_decode_forwards import _sim_identity


def inspect(body_path, case_path):
    runtime = _sim_identity()
    if max(body_path.stat().st_size, case_path.stat().st_size) > 50 * 1024 ** 2:
        raise ValueError("body or case declaration exceeds bounded metadata read limit")
    body_raw = body_path.read_bytes()
    body = json.loads(body_raw)
    forward = next(row for row in body["forwards"] if row["stages"])
    layer = next(row for row in forward["stages"] if row["layer_id"] is not None)
    actual = []
    for row in kernel_rows(body["source_identity"]["path"]):
        if row.event.start_ns < layer["start_ns"]:
            continue
        if row.event.start_ns >= layer["end_ns"]:
            break
        if ("GroupedMatmul" in row.kind or row.kind.startswith(("Moe", "hcom_"))
                or row.kind in {"MatMulV3", "MatMulV2", "QuantBatchMatmulV3", "ForeachAddList"}
                or "RmsNorm" in row.kind):
            actual.append({"native_operator_type": row.kind, "locator": row.event.locator,
                           "input_shapes": row.input_shapes, "output_shapes": row.output_shapes,
                           "input_dtypes": row.input_dtypes, "output_dtypes": row.output_dtypes,
                           "duration_us": row.event.duration_ns / 1000})
    raw = case_path.read_bytes()
    case = parse_case(json.loads(raw))
    geometry = forward["geometry"]
    graphs = target_graphs(case, phase="decode", tokens=geometry["tokens_per_sequence"],
                          sequences=geometry["sequences_per_replica"], context=0, scope="body")
    declared = []
    for op in next(iter(graphs.values())):
        metadata = dict(op.metadata)
        if op.layer == layer["layer_id"] and (op.family == "grouped_gemm"
                or (op.family == "allreduce" and metadata.get("structure_block") == "ffn")):
            declared.append({"op_id": op.op_id, "family": op.family, "recipe": op.recipe,
                             "local_shape": op.local_shape, "metadata": metadata})
    return {"schema_version": "mindie-grouped-moe-work-evidence/1",
            "source_identity": body["source_identity"],
            "case_identity": {"path": str(case_path), "sha256": hashlib.sha256(raw).hexdigest()},
            "body_report_identity": {"path": str(body_path), "sha256": hashlib.sha256(body_raw).hexdigest()},
            "runtime_identity": {**runtime, "sources_unchanged": runtime == _sim_identity()},
            "geometry": geometry, "layer_id": layer["layer_id"], "actual": actual, "declared": declared,
            "limitations": ["One measured layer sample; timing is not an acceptance population.",
                            "Grouped input rows are a total routed extent, not rows for every expert.",
                            "Group-list values and per-expert padding are not exposed by shape alone.",
                            "No cost prediction is run; context=0 only exports context-independent MoE nodes."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body-report", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.body_report, args.case)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"actual_rows": len(result["actual"]), "declared_ffn_nodes": len(result["declared"])}))


if __name__ == "__main__":
    main()
