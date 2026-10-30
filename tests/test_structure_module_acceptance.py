"""Real A2 module slice replay and controlled corruption of occurrence evidence."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from mindie_profiler.analyze import analyze_profile
from mindie_profiler.events import Observation, ProfilerUsageError, SourceRef, Window
from mindie_profiler.module_evidence import ModuleEvidence
from mindie_profiler.segment import load_steps_file
from mindie_profiler.sources_db import DbSource, probe_db
from mindie_profiler.structure_mapping import StructureMapper

FIXTURE = Path(__file__).parent / "fixtures/structure_module"


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
    source = Path(__file__).parent / "live_framework_capture_workload.py"
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


@pytest.fixture
def declaration():
    pytest.importorskip("mindie_sim.structure")

    manifest = mlp_structure()
    bindings = {
        "schema_version": "mindie-profile-bindings/1", "graph_id": manifest["graph_id"],
        "module_scopes": [
            {"module_id": module, "node_ids": [f"rank:0/{module}"]}
            for module in ("0", "1", "2")
        ],
    }
    return manifest, bindings


def run(declaration, *, trace=None, db=None, include_trace=True, max_events=100_000):
    manifest, bindings = declaration
    return analyze_profile(
        db or FIXTURE / "capture.db", source="db",
        windows=load_steps_file(FIXTURE / "steps.json", unit="ns"),
        structure=manifest, structure_bindings=bindings,
        structure_module_traces=[trace or FIXTURE / "module_trace.json"] if include_trace else [],
        max_mapping_events=max_events,
    )["structure_mapping"]


def altered_trace(tmp_path, transform):
    trace = json.loads((FIXTURE / "module_trace.json").read_text())
    transform(trace)
    target = tmp_path / "trace.json"
    target.write_text(json.dumps(trace))
    return target


def test_real_modules_resolve_candidates_and_keep_measured_time(declaration):
    original = sha256((FIXTURE / "capture.db").read_bytes()).hexdigest()
    without = run(declaration, include_trace=False)
    assert without["status_counts"] == {"candidate": 6}
    report = run(declaration)
    assert report["status_counts"] == {"bound": 6}
    assert report["reason_counts"] == {"synchronized_module_and_tensor": 6}
    window = report["windows"][0]
    assert window["bound_event_fraction"] == window["bound_busy_fraction"] == 1.0
    assert window["layers"] == []
    assert {row["node_id"]: row["event_count"] for row in window["nodes"]} == {
        "rank:0/0": 2, "rank:0/1": 2, "rank:0/2": 2,
    }
    assert window["bound_busy_union_ns"] == sum(
        row["end_ns"] - row["start_ns"] for row in report["event_mappings"])
    assert [row["evidence"][0]["module_id"] for row in report["event_mappings"]] == [
        "0", "1", "2", "0", "1", "2",
    ]
    assert report["module_evidence"][0]["db_sha256"] == original
    assert sha256((FIXTURE / "capture.db").read_bytes()).hexdigest() == original


@pytest.mark.parametrize("corruption,reason", [
    ("cross_step_overlap", "overlapping_module_invocations"),
    ("wrong_step", "module_step_mismatch"),
    ("crossing", "event_crosses_module_boundary"),
])
def test_conflicting_module_records_do_not_bind(declaration, tmp_path, corruption, reason):
    baseline = run(declaration)
    first_event = baseline["event_mappings"][0]

    def change(trace):
        first = trace["records"][0]
        if corruption == "cross_step_overlap":
            duplicate = deepcopy(first)
            duplicate["step_id"] = 2
            trace["records"].append(duplicate)
        elif corruption == "wrong_step":
            first["step_id"] = 2
        else:
            first["wall_end_ns"] = first_event["end_ns"] - 1

    report = run(declaration, trace=altered_trace(tmp_path, change))
    assert report["status_counts"] == {"ambiguous": 1, "bound": 5}
    assert report["event_mappings"][0]["basis"] == reason
    assert report["event_mappings"][0]["diagnostic"]["category"] == "occurrence_evidence_conflict"


def test_trace_hash_and_synchronization_are_required_evidence(declaration, tmp_path):
    wrong_hash = altered_trace(tmp_path, lambda trace: trace["source_identity"].update(
        db_sha256="0" * 64))
    with pytest.raises(ProfilerUsageError, match="DB hash matches no selected source"):
        run(declaration, trace=wrong_hash)
    unsynchronized = altered_trace(tmp_path, lambda trace: trace["instrumentation"].update(
        npu_synchronize=False))
    with pytest.raises(ProfilerUsageError, match="synchronized NPU boundaries"):
        run(declaration, trace=unsynchronized)


def test_old_aggregate_mapping_is_not_reused_and_record_budget_is_enforced(declaration, tmp_path):
    trace = altered_trace(tmp_path, lambda value: value.update(
        mapping={"events_total": 99999, "events_mapped": 0},
        invocations=[{"mapping_status": "unmapped"}] * 100,
    ))
    assert run(declaration, trace=trace)["status_counts"] == {"bound": 6}
    with pytest.raises(ProfilerUsageError, match="module records exceed"):
        run(declaration, trace=trace, max_events=5)


def test_module_record_budget_is_shared_across_traces(declaration):
    manifest, bindings = declaration
    with pytest.raises(ProfilerUsageError, match="module records exceed 4"):
        analyze_profile(
            FIXTURE / "capture.db", source="db",
            windows=load_steps_file(FIXTURE / "steps.json", unit="ns"),
            structure=manifest, structure_bindings=bindings,
            structure_module_traces=[FIXTURE / "module_trace.json"] * 2,
            max_mapping_events=10,
        )


def test_cli_replays_real_module_evidence(declaration, tmp_path, capsys):
    from mindie_profiler.__main__ import main

    manifest, bindings = declaration
    structure_path, bindings_path, output = (tmp_path / name for name in (
        "structure.json", "bindings.json", "report.json"))
    structure_path.write_text(json.dumps(manifest))
    bindings_path.write_text(json.dumps(bindings))
    assert main([
        "analyze", "--root", str(FIXTURE / "capture.db"), "--source", "db",
        "--steps-file", str(FIXTURE / "steps.json"), "--unit", "ns",
        "--structure", str(structure_path), "--bindings", str(bindings_path),
        "--module-trace", str(FIXTURE / "module_trace.json"),
        "--mapping-limit", "1", "--output", str(output),
    ]) == 0
    mapping = json.loads(output.read_text())["structure_mapping"]
    assert mapping["status_counts"] == {"bound": 6}
    assert mapping["retained_event_mappings"] == 1
    assert mapping["windows"][0]["bound_event_fraction"] == 1.0
    assert json.loads(capsys.readouterr().out)["structure_mapping"]["status"] == "mapped"


def test_streamed_module_mapping_requires_unclipped_event_evidence_bounds(declaration):
    path = (FIXTURE / "capture.db").resolve()
    schema = probe_db(path)
    window = load_steps_file(FIXTURE / "steps.json", unit="ns")[0]
    events, stats = DbSource(schema).iter_window(window)
    events = [replace(event, rank_id="rank_0", rank_index=0) for event in events]
    source = SourceRef(
        rank_id="rank_0", rank_index=0, kind="db", path=str(path), basename=path.name,
        sha256=sha256(path.read_bytes()).hexdigest(), size_bytes=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns, schema_version=schema.schema_version,
        schema_variant=schema.schema_variant,
    )
    manifest, bindings = declaration
    observation = Observation("rank_0", 0, window, None, [], source, stats)
    evidence = ModuleEvidence([FIXTURE / "module_trace.json"], [observation], max_records=10)
    mapper = StructureMapper(manifest, bindings=bindings, module_evidence=evidence)
    result = mapper.finish([mapper.map_window(observation, events=iter(events))])
    assert result["status_counts"] == {"bound": 6}
    assert result["windows"][0]["bound_busy_union_ns"] == sum(event.duration_ns for event in events)

    first = events[0]
    observation.window = Window(first.start_ns + 1, first.end_ns - 1, step=window.step)
    clipped_evidence = ModuleEvidence(
        [FIXTURE / "module_trace.json"], [observation], max_records=10)
    mapper = StructureMapper(manifest, bindings=bindings, module_evidence=clipped_evidence)
    with pytest.raises(ProfilerUsageError, match="full event bounds"):
        mapper.map_window(observation, events=iter([first]))
