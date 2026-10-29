"""Actual A5 task markers bound graphs, not inferred body/layer occurrences."""
import csv
import json
from pathlib import Path

import pytest

from mindie_profiler.graph_execution import correlate_forward_envelopes, graph_execution_envelopes


FIXTURE = Path(__file__).parent / "fixtures/graph_execution"


def test_real_markers_preserve_internal_wait_and_exclude_between_graph_gap():
    report = graph_execution_envelopes(FIXTURE / "task_time.csv",
                                       operator_path=FIXTURE / "op_summary.csv")
    first, second, *_ = report["windows"]
    assert len(report["windows"]) == 4
    assert report["unmatched_markers"] == []
    assert first["start_ns"] == 1792729149280519372
    assert first["end_ns"] == 1792729149290851792
    assert (first["end_ns"] - first["start_ns"]) / 1e6 == pytest.approx(10.332420)
    assert second["start_ns"] - first["end_ns"] == 470338
    assert first["observed_model_ids"] == {"31": 3}
    assert second["observed_model_ids"] == {"30": 3}
    assert report["operator_containment_counts"]["uniquely_contained_rows"] == 6
    assert report["operator_containment_counts"]["outside_or_crossing_or_overlapping_envelopes"] == 3
    assert report["graph_execution_span_ms"]["mean"] == pytest.approx(5.913863)
    assert report["body_forward_span_ms"] is None
    assert report["per_layer_ms"] is None
    assert all(row["semantic_role"] == "unresolved" for row in report["windows"])
    assert not report["tail_wait_removed"]


def test_incomplete_real_capture_does_not_bridge_to_next_graph(tmp_path):
    with (FIXTURE / "task_time.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    path = tmp_path / "partial.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        # Remove the first completion as at an incomplete export boundary.
        writer.writerows(rows[:1] + rows[2:])
    report = graph_execution_envelopes(path)
    assert len(report["windows"]) == 3
    assert report["windows"][0]["execute"]["task_id"] == "361525"
    assert [(row["task_id"], row["reason"]) for row in report["unmatched_markers"]] == [
        ("361348", "execute_without_completion")]


def test_task_export_row_order_does_not_change_measured_envelopes(tmp_path):
    with (FIXTURE / "task_time.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    path = tmp_path / "reverse.csv"
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(reversed(rows))
    expected = graph_execution_envelopes(FIXTURE / "task_time.csv")
    actual = graph_execution_envelopes(path)
    assert actual["graph_execution_span_ms"] == expected["graph_execution_span_ms"]
    assert [(row["start_ns"], row["end_ns"]) for row in actual["windows"]] == [
        (row["start_ns"], row["end_ns"]) for row in expected["windows"]]


def test_complete_topology_and_auxiliary_heads_crosscheck_independent_graph_markers():
    # The two full 64-layer alignments and six auxiliary head intervals come
    # from the complete Q36 A5 capture; no graph ID selected their layer roles.
    fixture = json.loads((FIXTURE / "forward_crosscheck.json").read_text())
    result = correlate_forward_envelopes(fixture["observed"], fixture["graph_report"])
    assert result["counts"] == {"complete_bodies": 2, "body_unique_graph": 2,
                                "auxiliary_heads": 6, "auxiliary_head_unique_graph": 6}
    assert result["body_graph_groups"][0]["observed_model_ids"] == ["31"]
    assert result["auxiliary_head_graph_groups"] == [
        {"observed_model_ids": ["30"], "auxiliary_head_count": 6}]
    graph = fixture["graph_report"]["windows"][0]
    body = fixture["observed"]["forwards"][0]
    expected = ((graph["end_ns"] - graph["start_ns"])
                - (body["end_ns"] - body["start_ns"])) / 1e6
    assert result["graph_minus_body_span_ms"]["min"] <= expected
    assert result["graph_minus_body_span_ms"]["max"] >= expected
    assert result["anomaly_examples"] == []
