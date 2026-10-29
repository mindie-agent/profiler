"""Replay the existing synchronized tiny-MLP capture through shared sim structure.

[Role] Reproducible acceptance example using the workload's independent declaration.
[Invariants] Linear/ReLU/Linear dimensions come from workload arguments, never
  captured timings or inferred kernel order. This is a module proof, not an LLM.
[Timeouts & Locks] Uses profiler's bounded DB, JSON and event-window budgets.
[Side-Effect Policy] Reads existing captures; writes only the requested report.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from mindie_profiler.analyze import analyze_profile
from mindie_profiler.segment import load_steps_file


def mlp_structure(*, hidden=256, batch=8):
    from mindie_sim.catalog.ops import gemm_op, vector_op
    from mindie_sim.catalog.types import QuantSpec
    from mindie_sim.structure import export_op_structure

    quant = QuantSpec("fp32", weight_format="fp32", activation_format="fp32")

    def linear(module, deps, inputs, outputs):
        return gemm_op(
            op_id=module, deps=deps, stage=0, layer=-1, requests=(),
            m=batch, n=outputs, k=inputs, quant=quant,
            category="dense_mlp", family="linear", phase="eager_mlp",
            metadata=(("module_id", module), ("module_type", "Linear"),
                      ("input_shape", (batch, inputs)), ("weight_shape", (outputs, inputs)),
                      ("output_shape", (batch, outputs)), ("bias", True),
                      ("bias_shape", (outputs,)), ("bias_dtype", "fp32")),
        )

    ops = (
        linear("0", ("input",), hidden, hidden * 2),
        vector_op(
            op_id="1", deps=("0",), stage=0, layer=-1, requests=(),
            elements=batch * hidden * 2, ops_per_element=1, dtype="fp32",
            family="relu", phase="eager_mlp", recipe="relu", shape=(batch, hidden * 2),
            metadata=(("module_id", "1"), ("module_type", "ReLU")),
        ),
        linear("2", ("1",), hidden * 2, hidden),
    )
    source = Path(__file__).resolve().parents[2] / "tests/live_framework_capture_workload.py"
    return export_op_structure(
        ops, model={"kind": "sequential", "name": "tiny-mlp-relu",
                    "input_shape": [batch, hidden], "dtype": "fp32"},
        execution={"phase": "eager_mlp", "scope": "model",
                   "replica_axis": "data_parallel", "shard_scope": "unsharded",
                   "stage_scope": "single_stage"},
        source={"path": str(source), "sha256": sha256(source.read_bytes()).hexdigest(),
                "declaration": "Linear(hidden,2*hidden), ReLU(), Linear(2*hidden,hidden)",
                "arguments": {"hidden": hidden, "batch": batch, "activation": "relu"}},
    )


def replay(db, trace, steps, *, output=None):
    manifest = mlp_structure()
    bindings = {
        "schema_version": "mindie-profile-bindings/1", "graph_id": manifest["graph_id"],
        "module_scopes": [
            {"module_id": module, "node_ids": [f"rank:0/{module}"]}
            for module in ("0", "1", "2")
        ],
    }
    report = analyze_profile(
        db, source="db", windows=load_steps_file(steps, unit="ns"),
        structure=manifest, structure_bindings=bindings,
        structure_module_traces=[trace], scene={"phase": "eager_mlp", "clock_domain": "unix_wall"},
        hash_sources=True, mapping_limit=12,
    )
    if output is not None:
        Path(output).write_text(json.dumps(evidence_projection(report), indent=2) + "\n")
    return report


def evidence_projection(report):
    """Retain measured attribution and provenance, omitting unrelated C7 enrichment."""
    return {
        "kind": "historical_capture_structure_replay",
        "report_schema_version": report["schema_version"],
        "not_new_live_collection": True,
        **{key: report[key] for key in (
            "source_identity", "scene", "window_accounting", "structure_mapping",
        )},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, type=Path)
    parser.add_argument("--module-trace", required=True, type=Path)
    parser.add_argument("--steps", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    mapping = replay(args.db, args.module_trace, args.steps, output=args.output)["structure_mapping"]
    print(json.dumps({
        "status_counts": mapping["status_counts"], "reason_counts": mapping["reason_counts"],
        "windows": [{
            "step": window["step"], "events": window["event_count"],
            "bound_event_fraction": window["bound_event_fraction"],
            "bound_busy_fraction": window["bound_busy_fraction"],
            "nodes": [{"node_id": node["node_id"], "events": node["event_count"]}
                      for node in window["nodes"]],
        } for window in mapping["windows"]],
    }, indent=2))


if __name__ == "__main__":
    main()
