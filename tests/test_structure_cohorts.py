"""Real native descriptors, independent sim declarations and controlled timings."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json

from mindie_profiler.events import Window
from mindie_profiler.structure_mapping import map_structure
from test_structure_subgraphs import declared, prolog, observation, bindings, host_evidence


def seal(value):
    payload = {k: v for k, v in value.items() if k not in {"source", "graph_id"}}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    value["graph_id"] = "sha256:" + sha256(encoded.encode()).hexdigest()
    return value


def test_repeated_real_contract_has_nonzero_group_statistics_without_layer_binding(declared, prolog):
    events = [
        replace(prolog, start_ns=100, end_ns=200, task_id="1"),
        replace(prolog, start_ns=150, end_ns=450, task_id="2"),
        replace(prolog, start_ns=500, end_ns=700, task_id="3"),
    ]
    report = map_structure([observation(events)], declared, mapping_limit=0)
    window = report["windows"][0]
    assert report["status_counts"] == {"ambiguous": 3}
    assert window["nodes"] == window["layers"] == window["subgraphs"] == []
    assert len(window["cohorts"]) == 1
    group = window["cohorts"][0]
    assert group["declared_instance_count"] == group["declared_layer_count"] == 21
    assert group["event_count"] == group["complete_event_count"] == 3
    assert group["activity_sum_ns"] == 600
    assert group["busy_union_ns"] == 550
    assert group["duration_ns"] == {
        "mean": 200, "p50": 200, "min": 100, "max": 300, "basis": "complete_events_only"}
    assert group["multiplicity"]["calls_per_declared_instance"] == 3 / 21
    assert group["multiplicity"]["steps_in_window"] is None
    assert not group["occurrence_binding_implied"]
    assert report["cohort_event_window_count"] == 3
    assert report["event_mappings"] == []
    assert window["operators"][0]["activity_sum_ns"] == 600
    assert window["operators"][0]["complete_event_count"] == 3
    assert window["operators"][0]["cohort_event_count"] == 3
    assert window["operators"][0]["cohort_excluded_event_counts"] == {}


def test_clipped_events_do_not_bias_single_call_distribution_or_become_steps(declared, prolog):
    events = [replace(prolog, start_ns=0, end_ns=100),
              replace(prolog, start_ns=100, end_ns=400, task_id="2")]
    window = Window(50, 400, step=17)
    report_window = map_structure([observation(events, window)], declared)["windows"][0]
    group = report_window["cohorts"][0]
    assert group["clipped_event_count"] == group["complete_event_count"] == 1
    assert group["activity_sum_ns"] == 350
    assert group["complete_activity_sum_ns"] == 300
    assert group["duration_ns"]["mean"] == group["duration_ns"]["p50"] == 300
    assert group["multiplicity"]["steps_in_window"] is None
    operator = report_window["operators"][0]
    assert operator["activity_sum_ns"] == 350
    assert operator["complete_activity_sum_ns"] == 300
    assert operator["complete_event_count"] == operator["clipped_event_count"] == 1


def test_equal_contract_with_different_declared_work_cannot_choose_group_by_timing(declared, prolog):
    changed = deepcopy(declared)
    baseline = map_structure([observation([prolog])], changed)
    target = baseline["windows"][0]["cohorts"][0]["target_ids"][0]
    group = next(row for row in changed["subgraphs"] if row["subgraph_id"] == target)
    group["physical_work"]["mte2_bytes"] += 256
    group["physical_signature"] = "sha256:controlled-different-traffic"
    report = map_structure([observation([prolog])], seal(changed))
    assert report["windows"][0]["cohorts"] == []
    assert report["windows"][0]["cohort_excluded_event_counts"] == {
        "candidate_physical_work_differs": 1}
    assert report["event_mappings"][0]["candidate_count"] == 21
    assert report["windows"][0]["operators"][0]["cohort_event_count"] == 0
    assert report["windows"][0]["operators"][0]["cohort_excluded_event_counts"] == {
        "candidate_physical_work_differs": 1}


def test_conflicting_host_evidence_cannot_be_hidden_in_a_cohort(declared, prolog):
    groups = [row for row in declared["subgraphs"] if row["role"] == "mla_prolog"
              and row["contract"] is not None]
    first = groups[0]
    scope = bindings(declared, host_scopes=[
        {"name": "controlled.a", "subgraph_ids": [first["subgraph_id"]]},
        {"name": "controlled.b", "node_ids": [
            row["node_id"] for row in declared["nodes"]
            if row["node_id"] not in first["node_ids"]]},
    ])
    report = map_structure([observation([prolog])], declared, bindings=scope,
                           correlations=[host_evidence(prolog, ["controlled.a", "controlled.b"])])
    assert report["event_mappings"][0]["basis"] == "conflicting_host_scopes"
    assert report["windows"][0]["cohorts"] == []
    assert report["windows"][0]["cohort_excluded_event_counts"] == {
        "conflicting_or_incomplete_occurrence_evidence": 1}


def _dp_structure(declared):
    """Retain two complete real-source subgraphs on four declared DP replicas."""
    value = deepcopy(declared)
    groups = [row for row in value["subgraphs"]
              if row["role"] == "mla_prolog" and row["contract"] is not None][:2]
    members = {key for group in groups for key in group["node_ids"]}
    nodes = [row for row in value["nodes"] if row["node_id"] in members]

    def clone(row, replica):
        item = json.loads(json.dumps(row).replace("rank:0/", f"rank:{replica}/"))
        item["replica"] = replica
        return item

    value["nodes"] = [clone(row, replica) for replica in range(4) for row in nodes]
    value["subgraphs"] = [clone(row, replica) for replica in range(4) for row in groups]
    value["execution"].update(replicas=[0, 1, 2, 3], replica_axis="data_parallel")
    return seal(value)


def test_dp_alternatives_preserve_single_device_counts_and_explicit_rank_binding(declared, prolog):
    value = _dp_structure(declared)
    result = map_structure([observation([prolog])], value)
    group = result["windows"][0]["cohorts"][0]
    assert result["status_counts"] == {"ambiguous": 1}
    assert group["declared_instance_count"] == group["declared_layer_count"] == 2
    assert group["declared_candidate_instance_count"] == len(group["target_ids"]) == 8
    assert group["replica"] is None
    assert group["multiplicity"]["calls_per_declared_instance"] == .5
    assert not group["placement"]["replica_binding_implied"]
    assert result["windows"][0]["subgraphs"] == result["windows"][0]["layers"] == []
    explicit = map_structure(
        [observation([prolog])], value,
        bindings=bindings(value, rank_replicas={"rank_0": 2}))
    chosen = explicit["windows"][0]["cohorts"][0]
    assert chosen["replica"] == 2
    assert chosen["declared_candidate_instance_count"] == chosen["declared_instance_count"] == 2
    assert explicit["status_counts"] == {"ambiguous": 1}
    target = next(row["subgraph_id"] for row in value["subgraphs"] if row["replica"] == 2)
    bound = map_structure(
        [observation([prolog])], value,
        bindings=bindings(value, events=[{
            "event_id": prolog.event_id, "subgraph_ids": [target],
            "evidence": {"source": "controlled independent occurrence annotation"},
        }]))
    known = bound["windows"][0]["cohorts"][0]
    assert bound["status_counts"] == {"bound": 1}
    assert known["replica"] == 2 and known["target_ids"] == [target]
    assert known["declared_instance_count"] == 1


def test_dp_cohort_requires_complete_symmetry_and_one_known_capture_device(declared, prolog):
    value = _dp_structure(declared)
    for change in ("missing_instance", "unknown_axis", "pipeline_stage"):
        changed = deepcopy(value)
        if change == "missing_instance":
            changed["subgraphs"].pop()
        elif change == "unknown_axis":
            changed["execution"].pop("replica_axis")
        else:
            for row in changed["nodes"] + changed["subgraphs"]:
                if row["replica"] == 3:
                    row["stage"] = 1
        result = map_structure([observation([prolog])], seal(changed))
        assert result["windows"][0]["cohorts"] == []
        assert result["windows"][0]["cohort_excluded_event_counts"] == {
            "candidate_placement_differs": 1}
    unknown_device = replace(prolog, device_id="")
    result = map_structure([observation([unknown_device])], value)
    assert result["windows"][0]["cohorts"] == []
    assert result["windows"][0]["cohort_excluded_event_counts"] == {
        "capture_device_scope_not_single": 1}
