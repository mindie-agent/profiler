"""Real GLM kernel rows with independent sim subgraphs and controlled evidence.

Host scopes and explicit annotations here are test controls, not collected
layer evidence. Raw tensor descriptors come unchanged from the retained capture.
"""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from mindie_profiler.events import Observation, ProfilerUsageError, QueryStats, SourceRef, Window
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.structure_mapping import map_structure


CAPTURE = Path(__file__).parent / "fixtures/attention_cache_contracts/a3_glm53.csv"


@pytest.fixture(scope="module")
def declared():
    structure = pytest.importorskip("mindie_sim.structure")
    case = Path(structure.__file__).resolve().parents[1] / "examples/cases/glm53-a3-w4a8.json"
    config = json.loads(case.read_text())
    config["runtime"].setdefault("kernels", {}).setdefault("lowerings", {}).update(
        mla_prolog="vllm_ascend_mla_prolog_v3")
    return structure.export_structure(config, phase="prefill", tokens=4096)


@pytest.fixture(scope="module")
def prolog():
    return next(row.event for row in kernel_rows(CAPTURE, rank_id="rank_0", rank_index=0)
                if row.kind == "MlaPrologV3")


def observation(events, window=None):
    stat = CAPTURE.stat()
    return Observation(
        "rank_0", 0, window or Window(min(event.start_ns for event in events),
                                    max(event.end_ns for event in events)),
        None, events, SourceRef(
            rank_id="rank_0", rank_index=0, kind="csv", path=str(CAPTURE.resolve()),
            basename=CAPTURE.name, sha256=None, size_bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns, schema_version="retained_capture",
            schema_variant="kernel_details",
        ), QueryStats("rank_0", "subgraph_control"),
    )


def bindings(declared, **kwargs):
    return {"schema_version": "mindie-profile-bindings/1",
            "graph_id": declared["graph_id"], **kwargs}


def selected(declared, event):
    report = map_structure([observation([event])], declared)
    row = report["event_mappings"][0]
    key = row["candidate_subgraph_ids"][0]
    return next(item for item in declared["subgraphs"] if item["subgraph_id"] == key)


def host_evidence(event, names):
    """Inject an exact connection in the real correlation schema as a control."""
    source = observation([event]).source
    return {
        "schema_version": "mindie-profiler-correlation/1", "rank_id": "rank_0",
        "source_identity": {"path": source.path, "size_bytes": source.size_bytes,
                            "mtime_ns": source.mtime_ns},
        "correlated_calls": [{
            "device_task": {
                "task_id": event.task_id, "stream_id": event.stream_id,
                "device_id": event.device_id, "start_ns": event.start_ns,
                "end_ns": event.end_ns, "global_task_id": event.locator.get("task_global_id"),
            },
            "global_task_id_unique": True,
            "association_basis": {"pytorch": "connection_ids"},
            "association_unique": {"pytorch": True},
            "host_stack": [{"name": name, "table": "PYTORCH_API"} for name in names],
        }],
    }


def test_real_fused_row_has_shared_structure_without_inventing_layer(declared, prolog):
    report = map_structure([observation([prolog])], declared)
    row = report["event_mappings"][0]
    assert row["status"] == "ambiguous"
    assert row["candidate_count"] > 1
    assert row["candidate_subgraph_ids"] and not row["candidate_node_ids"]
    assert not row["subgraph_ids"] and not row["covered_node_ids"]
    assert row["structural_classification"]["common"]["role"] == "mla_prolog"
    assert row["structural_classification"]["common"]["block"] == "attention"
    window = report["windows"][0]
    assert window["structural_groups"][0]["busy_union_ns"] == prolog.duration_ns
    assert window["bound_busy_union_ns"] == 0
    assert window["subgraphs"] == window["nodes"] == window["layers"] == []
    longer = replace(prolog, end_ns=prolog.end_ns + 100000)
    changed = map_structure([observation([longer])], declared)["event_mappings"][0]
    assert changed["candidate_subgraph_ids"] == row["candidate_subgraph_ids"]


def test_bound_composite_keeps_one_measured_boundary_and_occurrence_identity(declared, prolog):
    subgraph = selected(declared, prolog)
    replay = replace(prolog, start_ns=prolog.end_ns + 100, end_ns=prolog.end_ns * 2 - prolog.start_ns + 100)
    evidence = bindings(declared, events=[{
        "event_id": prolog.event_id, "subgraph_ids": [subgraph["subgraph_id"]],
        "evidence": {"source": "controlled explicit occurrence; no collected module claim"},
    }])
    result = map_structure([observation([prolog, replay])], declared, bindings=evidence)
    assert result["status_counts"] == {"bound": 1, "ambiguous": 1}
    row = result["event_mappings"][0]
    assert row["node_ids"] == []
    assert set(row["covered_node_ids"]) == set(subgraph["node_ids"])
    window = result["windows"][0]
    assert window["nodes"] == []
    assert window["subgraphs"][0]["member_timing"] == "not_separately_measured"
    for record in (window["subgraphs"][0], window["layers"][0], window["blocks"][0]):
        assert record["event_count"] == 1
        assert record["busy_union_ns"] == prolog.duration_ns
    assert window["bound_busy_union_ns"] == prolog.duration_ns
    assert set(window["covered_node_ids"]) == set(subgraph["node_ids"])
    assert set(window["unobserved_node_ids"]).isdisjoint(subgraph["node_ids"])


def test_nested_host_scope_requires_entire_subgraph_and_keeps_ancestor_constraints(declared, prolog):
    subgraph = selected(declared, prolog)
    members = subgraph["node_ids"]
    all_nodes = [node["node_id"] for node in declared["nodes"]]
    scopes = [
        {"name": "controlled.model", "node_ids": all_nodes},
        {"name": "controlled.layer.prolog", "node_ids": members},
    ]
    connected = host_evidence(prolog, [scope["name"] for scope in scopes])

    def run():
        return map_structure([observation([prolog])], declared,
                             bindings=bindings(declared, host_scopes=scopes),
                             correlations=[connected])

    result = run()
    assert result["event_mappings"][0]["subgraph_ids"] == [subgraph["subgraph_id"]]
    assert result["event_mappings"][0]["basis"] == "host_connection_and_tensor"
    scopes[1]["node_ids"] = members[:1]
    partial = run()
    assert partial["status_counts"] != {"bound": 1}
    assert partial["windows"][0]["bound_busy_union_ns"] == 0
    scopes[1] = {"name": "controlled.layer.prolog", "subgraph_ids": [subgraph["subgraph_id"]]}
    scopes[0]["node_ids"] = [node for node in all_nodes if node not in members]
    conflict = run()
    assert conflict["event_mappings"][0]["basis"] == "conflicting_host_scopes"
    assert conflict["windows"][0]["subgraphs"] == []


def test_explicit_subgraph_evidence_cannot_override_wrong_tensor_contract(declared, prolog):
    subgraph = selected(declared, prolog)
    changed = replace(prolog, output_dtypes=prolog.output_dtypes.replace("DT_BF16", "FLOAT", 1))
    evidence = bindings(declared, events=[{
        "event_id": changed.event_id, "subgraph_ids": [subgraph["subgraph_id"]],
        "evidence": {"source": "controlled mismatch"},
    }])
    with pytest.raises(ProfilerUsageError, match="subgraph binding tensor contract mismatch"):
        map_structure([observation([changed])], declared, bindings=evidence)


def test_native_implementation_correspondence_survives_missing_capture_fields_without_matching(
    declared, prolog,
):
    missing = replace(prolog, input_shapes="N/A", input_dtypes="N/A", input_formats="N/A",
                      output_shapes="N/A", output_dtypes="N/A", output_formats="N/A")
    result = map_structure([observation([missing])], declared)
    row = result["event_mappings"][0]
    correspondence = row["implementation_correspondence"]
    expected = [group for group in declared["subgraphs"] if group["role"] == "mla_prolog"]
    assert correspondence["declared_target_count"] == len(expected)
    assert correspondence["targets_with_contract"] == len(expected)
    assert correspondence["common"]["role"] == "mla_prolog"
    assert correspondence["tensor_match_implied"] is False
    assert correspondence["occurrence_binding_implied"] is False
    assert row["status"] == "unmapped" and row["candidate_count"] == 0
    assert row["diagnostic"]["category"] == "capture_metadata_missing"
    assert row["structural_classification"]["common"] == {}
    window = result["windows"][0]
    assert window["bound_busy_union_ns"] == 0
    assert window["structural_groups"] == window["subgraphs"] == []
    assert window["operators"][0]["implementation_correspondence"] == correspondence


def test_native_implementation_correspondence_does_not_hide_precision_mismatch(declared, prolog):
    changed = replace(prolog, input_dtypes="DT_BF16;" + prolog.input_dtypes.split(";", 1)[1])
    result = map_structure([observation([changed])], declared)
    row = result["event_mappings"][0]
    assert row["observed_contract"] is not None
    assert row["implementation_correspondence"]["common"]["role"] == "mla_prolog"
    assert row["candidate_count"] == 0
    assert row["status"] == "unmapped"
    assert row["diagnostic"]["category"] == "declared_structure_mismatch"
    assert result["windows"][0]["bound_busy_union_ns"] == 0
