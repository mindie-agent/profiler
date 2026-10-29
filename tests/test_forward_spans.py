"""Boundary arithmetic on retained hardware events; no inferred LLM forwards.

The module fixture supplies real synchronized leaf scopes. Tests that relabel
a scope as target_body are explicit controlled annotations testing accounting,
not acceptance evidence that the tiny MLP was a Decode Transformer capture.
"""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from mindie_profiler.events import ProfilerUsageError, SourceRef
from mindie_profiler.forward_spans import measure_forward_spans
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.segment import load_steps_file
from mindie_profiler.sources_db import DbSource, probe_db

FIXTURE = Path(__file__).parent / "fixtures/structure_module"


@pytest.fixture
def captured():
    path = FIXTURE / "capture.db"
    schema = probe_db(path)
    events, _ = DbSource(schema).iter_window(load_steps_file(FIXTURE / "steps.json", unit="ns")[0])
    events = [replace(event, rank_id="rank_0") for event in events]
    source = SourceRef("rank_0", 0, "db", str(path), path.name,
                       sha256(path.read_bytes()).hexdigest(), path.stat().st_size,
                       schema.schema_version, schema.schema_variant)
    trace = json.loads((FIXTURE / "module_trace.json").read_text())
    bounds = {
        "schema_version": "mindie-forward-boundaries/1",
        "source_identity": {"sha256": source.sha256}, "clock_domain": "unix_wall_ns",
        "phase": "decode", "forwards": [{"forward_id": "fixture-slice", "scopes": []}],
    }
    for record in trace["records"]:
        bounds["forwards"][0]["scopes"].append({
            "scope_id": str(record["invocation"]), "kind": "module", "complete": True,
            "start_ns": record["wall_start_ns"], "end_ns": record["wall_end_ns"],
            "evidence": {"basis": "synchronized_module", "npu_synchronize": True,
                         "reference": {"path": str(FIXTURE / "module_trace.json"),
                                       "invocation": record["invocation"]}},
        })
    return events, source, bounds


def test_real_synchronized_leaf_records_do_not_invent_body_or_layers(captured):
    events, source, bounds = captured
    report = measure_forward_spans(iter(events), bounds, source=source)
    assert report["status"] == "unresolved"
    assert report["body_forward_span_ms"]["count"] == 0
    assert report["per_layer_ms"] == []
    stages = report["forwards"][0]["stages"]
    assert [row["span_ms"] for row in stages] == [event.duration_ns / 1e6 for event in events]
    assert all(row["status"] == "measured" for row in stages)


def test_explicit_occurrence_groups_preserve_internal_gaps_not_between_groups(captured):
    events, source, bounds = captured
    # Controlled membership annotation: source event times are unchanged.
    bounds["forwards"] = []
    for index, group in enumerate((events[:3], events[3:])):
        bounds["forwards"].append({"forward_id": str(index), "scopes": [{
            "scope_id": "body", "kind": "target_body", "complete": True,
            "start_ns": group[0].start_ns - 500_000, "end_ns": group[-1].end_ns + 500_000,
            "evidence": {"basis": "correlated_host", "reference": "controlled_fixture_membership"},
            "event_ids": [event.event_id for event in group],
        }]})
    report = measure_forward_spans(iter(events), bounds, source=source)
    expected = [(group[-1].end_ns - group[0].start_ns) / 1e6
                for group in (events[:3], events[3:])]
    assert report["status"] == "measured"
    assert [row["body_forward_span_ms"] for row in report["forwards"]] == expected
    assert report["body_forward_span_ms"]["mean"] == pytest.approx(sum(expected) / 2)
    assert report["body_forward_span_ms"]["p90"] == max(expected)
    assert sum(expected) > sum(event.duration_ns for event in events) / 1e6
    assert sum(expected) < (events[-1].end_ns - events[0].start_ns) / 1e6


def test_unsynchronized_callback_and_clipped_event_are_not_exact_spans(captured):
    events, source, bounds = captured
    first, second = bounds["forwards"][0]["scopes"][:2]
    first["evidence"]["npu_synchronize"] = False
    second["end_ns"] = events[1].end_ns - 1
    report = measure_forward_spans(events, bounds, source=source)
    stages = report["forwards"][0]["stages"]
    assert stages[0]["reasons"] == ["unsynchronized_host_boundary"]
    assert stages[1]["reasons"] == ["event_crosses_scope_boundary"]
    assert stages[0]["span_ms"] is stages[1]["span_ms"] is None


def test_correlated_membership_must_be_complete_and_source_clock_must_match(captured):
    events, source, bounds = captured
    scope = bounds["forwards"][0]["scopes"][0]
    scope.update(kind="target_body", event_ids=[events[0].event_id, events[1].event_id])
    scope["evidence"]["basis"] = "correlated_host"
    bounds["forwards"][0]["scopes"] = [scope]
    report = measure_forward_spans(events[:1], bounds, source=source)
    assert report["forwards"][0]["reasons"] == ["correlated_event_occurrences_absent"]
    changed = deepcopy(bounds)
    changed["source_identity"]["sha256"] = "0" * 64
    with pytest.raises(ProfilerUsageError, match="SHA256"):
        measure_forward_spans(events, changed, source=source)
    with pytest.raises(ProfilerUsageError, match="clock"):
        measure_forward_spans(events, bounds, source=source, clock_domain="device_ns")


def test_tail_wait_needs_occurrence_evidence_and_does_not_remove_internal_aicpu():
    path = Path(__file__).parent / "fixtures/kernel_inventory/a3_kernel_details.csv"
    rows = list(kernel_rows(path, rank_id="rank_0"))
    events = [row.event for row in rows]
    tail = next(event for event in events if event.name == "allreduceAicpuKernel")
    source = SourceRef("rank_0", 0, "csv", str(path), path.name,
                       sha256(path.read_bytes()).hexdigest(), path.stat().st_size, "fixture", "fixture")
    last_compute = max(event.end_ns for event in events if event is not tail)
    # The retained real A3 interval has a trailing AICPU suffix. Only the
    # controlled annotation below authorizes stripping it in this test.
    assert tail.start_ns < last_compute < tail.end_ns
    scope = {"scope_id": "body", "kind": "target_body", "complete": True,
             "start_ns": min(event.start_ns for event in events),
             "end_ns": max(event.end_ns for event in events),
             "evidence": {"basis": "device_range", "reference": "controlled_test_boundary"}}
    bounds = {"schema_version": "mindie-forward-boundaries/1", "clock_domain": "unix_wall_ns",
              "source_identity": {"sha256": source.sha256}, "phase": "decode",
              "forwards": [{"forward_id": "controlled", "scopes": [scope]}]}
    raw = measure_forward_spans(events, bounds, source=source)
    assert raw["forwards"][0]["stages"][0]["end_ns"] == tail.end_ns
    scope["tail_waits"] = [{"event_id": tail.event_id, "wait_start_ns": last_compute,
                            "evidence": {"basis": "trailing_wait", "reference": "controlled_tail"}}]
    result = measure_forward_spans(events, bounds, source=source)
    stage = result["forwards"][0]["stages"][0]
    assert stage["end_ns"] == last_compute
    assert stage["aicpu_event_count"] == 1
    assert stage["excluded_tail_wait_activity_ms"] == (tail.end_ns - last_compute) / 1e6
    scope["tail_waits"][0]["wait_start_ns"] = tail.start_ns
    rejected = measure_forward_spans(events, bounds, source=source)
    assert rejected["forwards"][0]["reasons"] == ["wait_is_not_a_tail_of_body_activity"]


def test_layer_and_body_conflicts_do_not_assign_one_event_twice(captured):
    events, source, bounds = captured
    one = bounds["forwards"][0]["scopes"][0]
    one.update(kind="target_body")
    layer = {**deepcopy(one), "scope_id": "layer", "kind": "moe_layer", "layer_id": 2}
    bounds["forwards"][0]["scopes"] = [one, layer]
    second = deepcopy(bounds["forwards"][0])
    second["forward_id"] = "conflict"
    bounds["forwards"].append(second)
    report = measure_forward_spans(events, bounds, source=source)
    assert report["body_forward_span_ms"]["count"] == 0
    assert report["per_layer_ms"][0]["stats"]["count"] == 0
    assert report["per_layer_ms"][0]["samples"][0]["reasons"] == ["overlapping_layer_evidence"]


def test_body_separates_embedding_and_mtp_and_retains_dense_moe_layer_spans(captured):
    events, source, bounds = captured
    scopes = []
    for kind, indices, layer in (("embedding", [0], None), ("target_body", [1, 2, 3, 4], None),
                                 ("dense_layer", [1, 2], 0), ("moe_layer", [3, 4], 1),
                                 ("mtp", [5], None)):
        group = [events[index] for index in indices]
        scopes.append({"scope_id": kind, "kind": kind, "layer_id": layer, "complete": True,
                       "start_ns": group[0].start_ns, "end_ns": group[-1].end_ns,
                       "event_ids": [event.event_id for event in group],
                       "evidence": {"basis": "correlated_host", "reference": "controlled_membership"}})
    bounds["forwards"][0]["scopes"] = scopes
    report = measure_forward_spans(events, bounds, source=source)
    assert report["body_forward_span_ms"]["mean"] == (events[4].end_ns - events[1].start_ns) / 1e6
    assert [row["stats"]["mean"] for row in report["per_layer_ms"]] == [
        (events[2].end_ns - events[1].start_ns) / 1e6,
        (events[4].end_ns - events[3].start_ns) / 1e6]
    assert [row["kind"] for row in report["stage_span_ms"]] == ["embedding", "mtp"]
    assert report["span_start_basis"] == "first_retained_device_event_start"
    scopes[0]["event_ids"].append(events[1].event_id)
    conflict = measure_forward_spans(events, bounds, source=source)
    assert conflict["forwards"][0]["reasons"] == ["body_contains_explicitly_excluded_stage"]


def test_same_rank_multi_die_events_require_explicit_device_scope(captured):
    events, source, bounds = captured
    one = bounds["forwards"][0]["scopes"][0]
    one.update(kind="target_body")
    bounds["forwards"][0]["scopes"] = [one]
    other_die = replace(events[0], device_id="1")
    mixed = measure_forward_spans([events[0], other_die], bounds, source=source)
    assert mixed["forwards"][0]["reasons"] == ["multiple_devices_require_explicit_scopes"]
    one["device_id"] = events[0].device_id
    selected = measure_forward_spans([events[0], other_die], bounds, source=source)
    assert selected["body_forward_span_ms"]["mean"] == events[0].duration_ns / 1e6
    assert selected["events_selected"] == 1
