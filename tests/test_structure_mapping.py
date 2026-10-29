"""Behavioral tests of occurrence identity and nonadditive structure attribution."""
from dataclasses import replace
from hashlib import sha256
import json

import pytest

from mindie_profiler.accounting import account_window
from mindie_profiler.events import Event, Observation, ProfilerUsageError, QueryStats, SourceRef, Window
from mindie_profiler.structure_diagnostics import mismatch_diagnostic
from mindie_profiler.structure_mapping import StructureMapper, map_structure


def norm(start=0, end=100, *, task="1", rank="rank_0"):
    return Event(
        rank_id=rank, rank_index=0, name="RmsNorm", op_type="RmsNorm",
        task_type="AI_VECTOR_CORE", core="AI_VECTOR_CORE", stream_id="1",
        task_id=task, device_id="0", start_ns=start, end_ns=end,
        source_kind="db", table="COMPUTE_TASK_INFO", input_shapes="2,8;8",
        input_dtypes="DT_BF16;DT_BF16", input_formats="ND;ND",
        output_shapes="2,8;2,1", output_dtypes="DT_BF16;DT_FLOAT",
        output_formats="ND;ND", locator={"source": "/capture/profile.db", "task_rowid": int(task)},
    )


def observation(events, window=None):
    window = window or Window(0, max(event.end_ns for event in events), step=3)
    source = SourceRef(
        rank_id="rank_0", rank_index=0, kind="db", path="/capture/profile.db",
        basename="profile.db", sha256=None, size_bytes=4096, schema_version="1.2.0",
        schema_variant="test", mtime_ns=123,
    )
    return Observation(
        "rank_0", 0, window, account_window(events, window), events,
        source, QueryStats("rank_0", "3"),
    )


def structure(count=2):
    return seal({
        "schema_version": "mindie-model-structure/1",
        "source": {"kind": "unit_structure"},
        "nodes": [
            {"node_id": f"rank:0/s0.l{i}.norm1", "op_id": f"s0.l{i}.norm1",
             "replica": 0, "layer": i, "stage": 0, "block": "attention", "family": "rmsnorm",
             "contract": ["rmsnorm", [2, 8], "bf16", True]}
            for i in range(count)
        ],
    })


def seal(manifest):
    payload = {key: value for key, value in manifest.items() if key not in {"graph_id", "source"}}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    manifest["graph_id"] = "sha256:" + sha256(canonical.encode()).hexdigest()
    return manifest


def bindings(manifest=None, **kwargs):
    manifest = structure() if manifest is None else seal(manifest)
    return {"schema_version": "mindie-profile-bindings/1",
            "graph_id": manifest["graph_id"], **kwargs}


def event_binding(event, nodes, relation="direct"):
    return {"event_id": event.event_id, "node_ids": nodes, "relation": relation,
            "evidence": {"source": "test occurrence annotation", "kind": "declared"}}


def correlation(event, *, ambiguous=False, host="model.layers.0.attention"):
    return {
        "schema_version": "mindie-profiler-correlation/1", "rank_id": "rank_0",
        "source_identity": {"path": "/capture/profile.db", "size_bytes": 4096, "mtime_ns": 123},
        "correlated_calls": [{
            "device_task": {"task_id": event.task_id, "stream_id": event.stream_id,
                            "device_id": event.device_id, "start_ns": event.start_ns, "end_ns": event.end_ns,
                            "global_task_id": event.locator.get("task_global_id")},
            "ambiguous_global_task_id": ambiguous,
            "global_task_id_unique": not ambiguous,
            "association_basis": {"cann": "connection_ids", "pytorch": "same_global_tid_containment"},
            "association_unique": {"cann": True, "pytorch": True},
            "host_stack": [{"name": host, "table": "PYTORCH_API", "start_ns": 0, "end_ns": 50}],
        }],
    }


def test_shape_match_never_invents_layer_or_step_from_duration():
    events = [norm(), norm(200, 800, task="2")]
    report = map_structure([observation(events)], structure())
    assert report["status_counts"] == {"ambiguous": 2}
    assert report["windows"][0]["nodes"] == []
    longer = [replace(event, end_ns=event.end_ns + 20_000) for event in events]
    changed = map_structure([observation(longer)], structure())
    assert [row["candidate_node_ids"] for row in changed["event_mappings"]] == [
        row["candidate_node_ids"] for row in report["event_mappings"]
    ]
    assert all(row["node_ids"] == [] for row in changed["event_mappings"])
    unique = map_structure([observation(events)], structure(1))
    assert unique["status_counts"] == {"candidate": 2}
    assert unique["windows"][0]["bound_busy_union_ns"] == 0


def test_explicit_binding_addresses_replay_occurrence_not_reused_task_id():
    first = norm()
    replay = replace(first, start_ns=200, end_ns=300)
    manifest = structure()
    selected = manifest["nodes"][0]["node_id"]
    report = map_structure(
        [observation([first, replay])], manifest,
        bindings=bindings(manifest, events=[event_binding(first, [selected])]),
    )
    assert [row["status"] for row in report["event_mappings"]] == ["bound", "ambiguous"]
    assert report["windows"][0]["nodes"][0]["event_count"] == 1
    assert report["windows"][0]["bound_busy_union_ns"] == 100


def test_fusion_counts_once_in_layer_and_window_and_retains_inclusive_nodes():
    first, overlap = norm(0, 100), norm(50, 150, task="2")
    manifest = structure()
    manifest["nodes"][1]["layer"] = 0
    ids = [node["node_id"] for node in manifest["nodes"]]
    report = map_structure(
        [observation([first, overlap], Window(25, 125, step=3))], manifest,
        bindings=bindings(manifest, events=[event_binding(first, ids, "fusion"),
                                            event_binding(overlap, [ids[0]])]),
    )
    window = report["windows"][0]
    assert window["bound_busy_union_ns"] == 100
    assert window["layers"][0]["event_count"] == 2
    assert window["layers"][0]["busy_union_ns"] == 100
    assert window["layers"][0]["activity_sum_ns"] == 150
    assert window["blocks"][0]["busy_union_ns"] == 100
    assert [row["busy_union_ns"] for row in window["nodes"]] == [100, 75]
    assert window["nodes"][1]["shared_event_count"] == 1
    assert all(row["attribution"] == "inclusive_nonadditive" for row in window["nodes"])


def test_cross_block_fusion_preserves_original_scopes_and_nonadditive_window_time():
    # Controlled occurrence accounting: a fused boundary can contain the
    # preceding FFN residual and the next block's attention normalization.
    event = norm(0, 100)
    manifest = structure(1)
    node = manifest["nodes"][0]
    node["layer"] = 1
    node["node_id"], node["op_id"] = "rank:0/s0.l1.norm1", "s0.l1.norm1"
    node["operator"] = {"metadata": {"fused_origin_scopes": [
        {"op_id": "s0.l0.ffn.residual", "stage": 0, "layer": 0,
         "block": "ffn", "role": "residual"},
        {"op_id": "s0.l1.norm1", "stage": 0, "layer": 1,
         "block": "attention", "role": "body"},
    ]}}
    report = map_structure(
        [observation([event])], seal(manifest),
        bindings=bindings(manifest, events=[event_binding(event, [node["node_id"]])]),
    )
    window = report["windows"][0]
    assert window["bound_busy_union_ns"] == 100
    assert {(row["layer"], row["busy_union_ns"]) for row in window["layers"]} == {
        (0, 100), (1, 100)}
    assert {(row["layer"], row["block"], row["event_count"])
            for row in window["blocks"]} == {(0, "ffn", 1), (1, "attention", 1)}
    assert all(row["attribution"] == "inclusive_nonadditive" for row in window["layers"])


def test_streamed_mapping_preserves_occurrences_clipping_and_accounting():
    events = [norm(0, 100), norm(50, 150, task="2"), norm(400, 500, task="3")]
    captured = observation(events, Window(25, 125, step=3))
    manifest = structure()
    evidence = bindings(manifest, events=[
        event_binding(events[0], [manifest["nodes"][0]["node_id"]]),
    ])
    expected = map_structure([captured], manifest, bindings=evidence)
    mapper = StructureMapper(manifest, bindings=evidence)
    metadata_only = replace(captured, events=[])
    result = mapper.finish([mapper.map_window(metadata_only, events=iter(events))])
    assert result == expected


def test_host_scope_resolves_repeated_shapes_only_with_connected_occurrence():
    event = norm()
    manifest = structure()
    node = manifest["nodes"][0]["node_id"]
    evidence = bindings(manifest, host_scopes=[{"name": "model.layers.0.attention", "node_ids": [node]}])
    report = map_structure([observation([event])], manifest, bindings=evidence,
                           correlations=[correlation(event)])
    assert report["event_mappings"][0]["node_ids"] == [node]
    assert report["event_mappings"][0]["basis"] == "host_connection_and_tensor"
    ambiguous = map_structure([observation([event])], manifest, bindings=evidence,
                             correlations=[correlation(event, ambiguous=True)])
    assert ambiguous["status_counts"] == {"ambiguous": 1}
    interval_only = correlation(event)
    interval_only["correlated_calls"][0]["association_basis"]["cann"] = "cann_interval_contains_task"
    unmapped = map_structure([observation([event])], manifest, bindings=evidence,
                            correlations=[interval_only])
    assert unmapped["status_counts"] == {"ambiguous": 1}
    interval_only["correlated_calls"][0]["association_basis"]["pytorch"] = "connection_ids"
    disconnected = map_structure([observation([event])], manifest, bindings=evidence,
                                 correlations=[interval_only])
    assert disconnected["status_counts"] == {"ambiguous": 1}
    duplicate = correlation(event)
    duplicate["correlated_calls"][0]["association_unique"]["cann"] = False
    conflict = map_structure([observation([event])], manifest, bindings=evidence,
                             correlations=[duplicate])
    assert conflict["status_counts"] == {"ambiguous": 1}
    other_task = correlation(event)
    other_task["correlated_calls"][0]["device_task"]["global_task_id"] = 99
    wrong_occurrence = map_structure([observation([event])], manifest, bindings=evidence,
                                    correlations=[other_task])
    assert wrong_occurrence["status_counts"] == {"ambiguous": 1}


def test_stale_source_and_wrong_graph_cannot_bind_measurements():
    event = norm()
    stale = correlation(event)
    stale["source_identity"]["mtime_ns"] += 1
    with pytest.raises(ProfilerUsageError, match="source changed"):
        map_structure([observation([event])], structure(), correlations=[stale])
    wrong = bindings()
    wrong["graph_id"] = "another-graph"
    with pytest.raises(ProfilerUsageError, match="graph_id"):
        map_structure([observation([event])], structure(), bindings=wrong)
    stale_graph = structure()
    stale_graph["nodes"][0]["layer"] = 99
    with pytest.raises(ProfilerUsageError, match="graph_id.*contents"):
        map_structure([observation([event])], stale_graph)


def test_conflicting_host_evidence_and_declared_phase_do_not_bind():
    event = norm()
    manifest = structure()
    manifest["execution"] = {"phase": "prefill"}
    manifest["nodes"][1]["contract"][1] = [2, 16]
    declared = bindings(manifest, host_scopes=[
        {"name": "scope.one", "node_ids": [manifest["nodes"][0]["node_id"]]},
        {"name": "scope.two", "node_ids": [manifest["nodes"][1]["node_id"]]},
    ])
    report = map_structure(
        [observation([event])], manifest, bindings=declared,
        correlations=[correlation(event, host="scope.one"), correlation(event, host="scope.two")],
    )
    assert report["status_counts"] == {"ambiguous": 1}
    assert report["event_mappings"][0]["basis"] == "conflicting_host_scopes"
    with pytest.raises(ProfilerUsageError, match="scene phase"):
        map_structure([observation([event])], manifest, phase="decode")


def test_nested_host_scopes_retain_ancestor_constraints_when_narrowing():
    event = norm()
    manifest = structure()
    first, second = [node["node_id"] for node in manifest["nodes"]]
    connected = correlation(event, host="scope.outer")
    connected["correlated_calls"][0]["host_stack"].append({
        "name": "scope.inner", "table": "PYTORCH_API", "start_ns": 1, "end_ns": 40,
    })
    scopes = [
        {"name": "scope.outer", "node_ids": [first]},
        {"name": "scope.inner", "node_ids": [second]},
    ]
    conflicting = map_structure(
        [observation([event])], manifest,
        bindings=bindings(manifest, host_scopes=scopes), correlations=[connected],
    )
    row = conflicting["event_mappings"][0]
    assert row["status"] == "ambiguous"
    assert row["node_ids"] == []
    assert row["basis"] == "conflicting_host_scopes"
    assert row["diagnostic"]["category"] == "occurrence_evidence_conflict"
    assert conflicting["windows"][0]["bound_busy_union_ns"] == 0
    assert conflicting["windows"][0]["nodes"] == []

    scopes[0]["node_ids"] = [first, second]
    narrowed = map_structure(
        [observation([event])], manifest,
        bindings=bindings(manifest, host_scopes=scopes), correlations=[connected],
    )
    row = narrowed["event_mappings"][0]
    assert row["status"] == "bound" and row["node_ids"] == [second]
    assert row["basis"] == "host_connection_and_tensor"
    assert [item["frame"]["name"] for item in row["evidence"]] == [
        "scope.outer", "scope.inner",
    ]
    assert narrowed["windows"][0]["bound_busy_union_ns"] == 100


@pytest.mark.parametrize("index,value,field,reason", [
    (5, (1, 512), "bias_shape", "declared_tensor_descriptor_mismatch"),
    (6, "fp16", "bias_dtype", "declared_dtype_or_quantization_mismatch"),
    (1, (16, 512, 256), "geometry", "declared_geometry_or_scope_mismatch"),
])
def test_biased_matrix_diagnostics_separate_geometry_descriptors_and_precision(
    index, value, field, reason,
):
    observed = ("matrix_bias", (8, 512, 256), "fp32", "fp32", "fp32", (512,), "fp32")
    declared = list(observed)
    declared[index] = value
    diagnostic = mismatch_diagnostic(observed, [tuple(declared)])
    assert diagnostic["reason"] == reason
    assert diagnostic["near_contracts"] == [
        {"contract": tuple(declared), "differing_fields": [field]},
    ]


def test_explicit_binding_does_not_override_tensor_mismatch():
    event = norm()
    manifest = structure(1)
    manifest["nodes"][0]["contract"][1] = [2, 16]
    with pytest.raises(ProfilerUsageError, match="tensor contract mismatch"):
        map_structure([observation([event])], manifest,
                      bindings=bindings(manifest, events=[event_binding(event, [manifest["nodes"][0]["node_id"]])]))


def test_mapping_sample_limit_does_not_truncate_measurement_totals():
    events = [norm(i * 100, i * 100 + 50, task=str(i + 1)) for i in range(5)]
    manifest = structure(1)
    declared = bindings(manifest, events=[
        event_binding(event, [manifest["nodes"][0]["node_id"]]) for event in events
    ])
    report = map_structure([observation(events)], manifest, bindings=declared, mapping_limit=1)
    assert report["event_mappings_truncated"] is True
    assert len(report["event_mappings"]) == 1
    assert report["status_counts"] == {"bound": 5}
    assert report["windows"][0]["bound_busy_union_ns"] == 250
    with pytest.raises(ProfilerUsageError, match="event-window"):
        map_structure([observation(events)], manifest, max_events=4)


def test_rank_assignment_is_explicit_when_capture_and_structure_ranks_differ():
    event = norm()
    manifest = structure()
    manifest["nodes"][1]["replica"] = 2
    manifest["nodes"][1]["stage"] = 1
    seal(manifest)
    report = map_structure([observation([event])], manifest)
    assert report["status_counts"] == {"ambiguous": 1}
    assert report["windows"][0]["rank_scope"]["basis"] == "unspecified"
    mapped = map_structure([observation([event])], manifest,
                           bindings=bindings(manifest, rank_replicas={"rank_0": 2},
                                             rank_stages={"rank_0": 1}))
    assert mapped["status_counts"] == {"candidate": 1}
    assert mapped["event_mappings"][0]["candidate_node_ids"] == [manifest["nodes"][1]["node_id"]]
    with pytest.raises(ProfilerUsageError, match="replicas or pipeline stages"):
        map_structure([observation([event])], manifest, bindings=bindings(
            manifest, events=[event_binding(event, [node["node_id"] for node in manifest["nodes"]], "fusion")],
        ))
