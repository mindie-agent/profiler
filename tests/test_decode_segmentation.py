"""Automatic whole-to-layer alignment on one unchanged complete A3 forward.

Corruption and timestamp-shift tests below are deliberate algorithm probes;
only the retained original CSV is hardware acceptance evidence.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from mindie_profiler.decode_segmentation import _Row, _scope, auto_segment_decode_forwards
from mindie_profiler.normalized import kernel_rows, shapes

FIXTURE = Path(__file__).parent / "fixtures/decode_forward"


@pytest.fixture
def capture():
    return ([row.event for row in kernel_rows(FIXTURE / "qwen36_a3_verify.csv", rank_id="rank_0")],
            json.loads((FIXTURE / "model_config.json").read_text()))


def test_complete_real_64_layer_forward_matches_topology_and_closes_on_vocab(capture):
    events, config = capture
    report = auto_segment_decode_forwards(iter(events), config)
    assert report["body_forward_span_ms"]["count"] == 1
    assert report["body_forward_span_ms"]["mean"] == pytest.approx(17.202996)
    assert report["geometry"]["tokens_per_sequence"] == 4
    assert report["geometry"]["sequences_per_replica"] == 1
    assert report["geometry"]["context_tokens"] is None
    assert len(report["per_layer_ms"]) == 64
    body = report["forwards"][0]
    assert body["confidence"]["matched_layers"] == 64
    assert not body["confidence"]["server_phase_marker_observed"]
    assert body["end_ns"] < body["head_start_ns"]
    stages = body["stages"]
    assert {row["kind"] for row in stages} >= {"embedding", "final_norm", "lm_head", "target_body"}
    assert [row["attention"] for row in stages if row["kind"] == "dense_layer"] == [
        plan["attention"] for plan in config["layer_plans"]]
    assert all(layer["stats"]["count"] == 1 for layer in report["per_layer_ms"])
    assert report["scan_counts"]["positive_events"] == report["scan_counts"]["complete_body_segment_events"] == 1944


def test_missing_attention_or_wrong_declared_order_does_not_number_layers(capture):
    events, config = capture
    missing = next(event for event in events if event.op_type == "RecurrentGatedDeltaRule")
    result = auto_segment_decode_forwards((event for event in events if event is not missing), config)
    assert result["body_forward_span_ms"]["count"] == 0
    assert result["per_layer_ms"] == []
    swapped = deepcopy(config)
    swapped["layer_plans"][0]["attention"] = "gqa"
    swapped["layer_plans"][3]["attention"] = "gdn"
    wrong = auto_segment_decode_forwards(events, swapped)
    assert wrong["anomaly_counts"] == {"ordered_layer_topology_mismatch": 1}


def test_activation_without_hidden_down_projection_is_not_complete_ffn(capture):
    events, config = capture
    down = [event for event in events if event.op_type == "QuantBatchMatmulV3"
            and shapes(event.output_shapes) == ((4, 5120),)][-1]
    report = auto_segment_decode_forwards((event for event in events if event is not down), config)
    assert report["body_forward_span_ms"]["count"] == 0
    assert report["anomaly_counts"] == {"ffn_output_hidden_contract_missing": 1}
    assert report["anomalies"][0]["layer"] == 63


def test_missing_head_stays_visible_as_unclosed_fragment(capture):
    events, config = capture
    report = auto_segment_decode_forwards(events[:-1], config)
    assert report["status"] == "unresolved"
    assert report["anomaly_counts"] == {"trailing_segment_without_vocabulary_head": 1}
    assert report["scan_counts"]["trailing_segment_events"] == 1943


def test_bounded_details_preserve_all_geometry_and_layer_statistics(capture):
    events, config = capture
    shifted = [replace(event, start_ns=event.start_ns + 1_000_000_000,
                       end_ns=event.end_ns + 1_000_000_000) for event in events]
    report = auto_segment_decode_forwards(iter([*events, *shifted]), config,
                                         max_detailed_forwards=1, max_samples_per_layer=1)
    assert report["body_forward_span_ms"]["count"] == 2
    assert report["body_forward_span_ms"]["mean"] == pytest.approx(17.202996)
    assert report["forwards"][1]["stages"] == []
    assert all(row["stats"]["count"] == 2 and row["sample_count"] == 1
               for row in report["per_layer_ms"])
    assert report["geometry_groups"][0]["body_forward_span_ms"]["count"] == 2
    assert all(row["stats"]["count"] == 2 for row in report["geometry_groups"][0]["per_layer_ms"])


def test_gemma_parameter_preparation_belongs_to_following_norm_layer(capture):
    events, config = capture
    report = auto_segment_decode_forwards(events, config)
    second = report["per_layer_ms"][1]["samples"][0]
    event = next(event for event in events if event.start_ns == second["start_ns"])
    assert event.op_type == "Add"
    assert shapes(event.input_shapes)[0] == (config["hidden_size"],)
    first = report["per_layer_ms"][0]["samples"][0]
    assert first["end_ns"] < second["start_ns"]


def test_only_scheduler_tail_crossing_successor_boundary_is_shortened(capture):
    events, _ = capture
    rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)) for event in events]
    # Original first layer has a long AICPU scheduling tail crossing the next
    # layer's input norm. Real HCCL completion remains in the retained span.
    # Choose the next layer start directly from the measured scope locator.
    report = auto_segment_decode_forwards(events, json.loads((FIXTURE / "model_config.json").read_text()))
    first = report["per_layer_ms"][0]["samples"][0]
    successor_ns = first["evidence"]["successor_boundary_start_ns"]
    successor = next(row for row in rows if row.event.start_ns == successor_ns)
    selected = [row for row in rows if first["start_ns"] <= row.event.start_ns < successor_ns]
    measured = _scope(selected, "dense_layer", "controlled", successor=successor)
    assert measured["excluded_tail_wait_activity_ms"] > 0
    tail = next(row for row in selected if row.kind == "allreduceAicpuKernel"
                and row.event.end_ns > successor_ns)
    changed = _Row(replace(tail.event, end_ns=successor_ns - 1), tail.inputs, tail.outputs)
    retained = _scope([changed if row is tail else row for row in selected],
                      "dense_layer", "controlled", successor=successor)
    assert retained["end_ns"] == successor_ns - 1
    assert retained["excluded_tail_wait_activity_ms"] == 0


def test_endpoint_locator_tracks_completion_not_last_started_operator(capture):
    events, _ = capture
    communication = next(event for event in events if event.op_type == "hcom_allReduce_")
    following = next(event for event in events if event.start_ns > communication.start_ns)
    # Controlled overlap perturbation of actual exported events: an earlier
    # communication can complete after the following device operator starts.
    communication = replace(communication, end_ns=following.end_ns + 5_000)
    rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes))
            for event in (communication, following)]
    scope = _scope(rows, "dense_layer", "overlap")
    assert scope["start_ns"] == communication.start_ns
    assert scope["end_ns"] == communication.end_ns
    assert scope["evidence"]["first_locator"] == communication.locator
    assert scope["evidence"]["last_locator"] == communication.locator
    assert scope["evidence"]["last_started_locator"] == following.locator
