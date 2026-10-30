"""Automatic whole-to-layer alignment on one unchanged complete A3 forward.

Corruption and timestamp-shift tests below are deliberate algorithm probes;
only the retained original CSV is hardware acceptance evidence.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from mindie_profiler.decode_segmentation import (
    _Row, _communication_bounds, _norm, _scope, auto_segment_decode_forwards,
)
from mindie_profiler.normalized import kernel_rows, shapes

FIXTURE = Path(__file__).parent / "fixtures/decode_forward"


@pytest.fixture
def cross_head_suffix():
    events = [row.event for row in kernel_rows(FIXTURE / "qwen36_a3_cross_head_summary.csv")]
    config = json.loads((FIXTURE / "model_config.json").read_text())
    # The retained records are the complete real layers 60--63 of auto:98.
    # Exercise that ordered suffix without manufacturing the preceding layers.
    config["layer_plans"] = config["layer_plans"][60:64]
    config["layers"] = config["body_layers"] = 4
    rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)) for event in events]
    norms = [i for i, row in enumerate(rows) if _norm(row, config["hidden_size"])]
    return events, config, rows, norms


def test_real_cross_head_summaries_use_hidden_consumer_bound_without_changing_events(cross_head_suffix):
    events, config, rows, norms = cross_head_suffix
    original = deepcopy(events)
    bounds = _communication_bounds(rows, config["hidden_size"], norms, rows[-1])
    assert len(bounds) == 4
    assert [value["raw_duration_ns"] for value in bounds.values()] == [
        51_248_269, 51_242_709, 51_241_329, 51_242_129]
    assert [value["effective_end_ns"] - value["raw_start_ns"] for value in bounds.values()] == [
        14_901, 14_661, 17_781, 17_181]
    by_line = {event.locator["csv_line"]: event for event in events}
    for proof in bounds.values():
        consumer = by_line[proof["consumer_locator"]["csv_line"]]
        assert consumer.op_type == "AddRmsNormBias"
        gamma = by_line[consumer.locator["csv_line"] - 1]
        assert gamma.op_type == "Add" and shapes(gamma.input_shapes)[0] == (5120,)
        assert proof["effective_end_ns"] > gamma.end_ns
        assert not proof["physical_transport_completion_observed"]
    seen = []
    report = auto_segment_decode_forwards(events, config,
        on_forward=lambda result, raw: seen.append((result, raw)))
    body = report["forwards"][0]
    assert body["body_forward_span_ms"] == pytest.approx(1.676807)
    layers = {stage["layer_id"]: stage for stage in body["stages"] if stage["layer_id"] is not None}
    assert [layers[i]["span_ms"] for i in (60, 61, 62, 63)] == pytest.approx([
        .340373, .333074, .329234, .677647])
    assert layers[61]["span_end_basis"] == layers[62]["span_end_basis"] == "structural_consumer_start_upper_bound"
    assert layers[60]["span_end_basis"] == layers[63]["span_end_basis"] == "last_retained_device_event_end"
    assert body["end_ns"] < body["head_start_ns"]
    assert body["communication_envelope_bounds"] == list(bounds.values())
    for stage in body["stages"]:
        assert stage["device_activity_union_ms"] + stage["internal_uncovered_gap_ms"] == pytest.approx(stage["span_ms"])
        for proof in stage.get("communication_envelope_bounds", []):
            assert proof in body["communication_envelope_bounds"]
    assert report["scan_counts"]["structurally_bounded_communication_envelopes"] == 4
    accounting = report["communication_envelope_accounting"]
    assert accounting["affected_events"] == 4 and accounting["affected_forwards"] == 1
    assert accounting["raw_envelope_total_ns"] == sum(value["raw_duration_ns"] for value in bounds.values())
    assert accounting["unassigned_summary_suffix_total_ns"] == sum(
        value["unassigned_summary_suffix_ns"] for value in bounds.values())
    assert not accounting["additive_body_time_cause"]
    assert events == original and list(seen[0][1]) == original
    # The old raw envelope remains reproducible when no complete head proof
    # was supplied; no schema/name-only event filter has been introduced.
    unbounded = _scope(rows, "target_body", "raw_without_head_proof")
    assert unbounded["end_ns"] == max(event.end_ns for event in events)


def test_cross_head_evidence_survives_bounded_stage_detail_retention(cross_head_suffix):
    events, config, _, _ = cross_head_suffix
    report = auto_segment_decode_forwards(events, config, max_detailed_forwards=0, max_samples_per_layer=0)
    forward = report["forwards"][0]
    assert forward["stages"] == []
    assert len(forward["communication_envelope_bounds"]) == 4
    assert report["body_activity_ms"]["mean"] + report["body_internal_gap_ms"]["mean"] == pytest.approx(1.676807)


def test_real_summary_between_final_norm_and_head_is_not_reinterpreted(cross_head_suffix):
    _, config, rows, norms = cross_head_suffix
    head = rows[-1]
    changed = [_Row(replace(row.event, end_ns=head.event.start_ns - 1), row.inputs, row.outputs)
               if row.event.core == "COMMUNICATION" and row.event.end_ns > head.event.start_ns else row
               for row in rows]
    assert rows[norms[-1]].event.start_ns < head.event.start_ns - 1
    assert _communication_bounds(changed, config["hidden_size"], norms, head) == {}
    assert _communication_bounds(rows, config["hidden_size"], norms, None) == {}


@pytest.mark.parametrize("evidence", ["device_task", "stream", "pmu", "tensor_descriptor", "block_grid",
                                      "different_consumer_stream", "wrong_hidden_shape"])
def test_unbound_summary_correction_requires_the_real_structural_chain(cross_head_suffix, evidence):
    _, config, rows, norms = cross_head_suffix
    baseline = _communication_bounds(rows, config["hidden_size"], norms, rows[-1])
    first = next(row for row in rows if id(row.event) in baseline)
    proof = baseline[id(first.event)]
    consumer = next(row for row in rows if row.event.locator == proof["consumer_locator"])
    producer = next(row for row in rows if row.event.locator == proof["producer_locator"])
    if evidence == "device_task":
        replacement = _Row(replace(first.event, core="AI_VECTOR_CORE", task_id=producer.event.task_id,
                                  stream_id=producer.event.stream_id), first.inputs, first.outputs)
        target = first
    elif evidence == "stream":
        target = first
        replacement = _Row(replace(first.event, stream_id=producer.event.stream_id), first.inputs, first.outputs)
    elif evidence == "pmu":
        target = first
        replacement = _Row(replace(first.event, pmu=producer.event.pmu), first.inputs, first.outputs)
        assert replacement.event.pmu
    elif evidence in {"tensor_descriptor", "block_grid"}:
        target = first
        change = {"input_dtypes": "DT_BF16"} if evidence == "tensor_descriptor" else {"block_dim": 20}
        replacement = _Row(replace(first.event, **change), first.inputs, first.outputs)
    elif evidence == "different_consumer_stream":
        target = consumer
        replacement = _Row(replace(consumer.event, stream_id=rows[-1].event.stream_id), consumer.inputs, consumer.outputs)
        assert replacement.event.stream_id != producer.event.stream_id
    else:
        target = producer
        replacement = _Row(producer.event, producer.inputs, ((16, 4352),))
    changed = [replacement if row is target else row for row in rows]
    bounded = _communication_bounds(changed, config["hidden_size"], norms, rows[-1])
    assert len(bounded) == 3
    assert all(value["envelope_locator"] != first.event.locator for value in bounded.values())


@pytest.fixture
def kimi_cross_head():
    events = [row.event for row in kernel_rows(FIXTURE / "kimi4_tp16_cross_head_summary.csv")]
    config = json.loads((FIXTURE / "kimi4_tp8_model_config.json").read_text())
    # The independent source model pin in the fixture provenance declares
    # this same four-layer architecture at TP16, not the earlier TP8 capture.
    config.update(name="kimi-k3-4layer-w4a8-tp16-source", tp=16)
    rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)) for event in events]
    norms = [i for i, row in enumerate(rows) if _norm(row, config["hidden_size"])]
    return events, config, rows, norms


def test_real_padded_tp16_reduce_scatter_bounds_only_its_summary(kimi_cross_head):
    events, config, rows, norms = kimi_cross_head
    original = deepcopy(events)
    bounds = _communication_bounds(rows, config["hidden_size"], norms, rows[-1], tp=16)
    assert len(bounds) == 1
    proof = next(iter(bounds.values()))
    assert proof["raw_duration_ns"] == 9_749_614
    assert proof["effective_end_ns"] - proof["raw_start_ns"] == 38_780
    assert proof["tensor_chain_evidence"]["declared_tp"] == 16
    assert proof["tensor_chain_evidence"]["projection_output_shape"] == [24, 7168]
    assert proof["tensor_chain_evidence"]["padded_hidden_shape"] == [32, 7168]
    assert proof["tensor_chain_evidence"]["consumer_flat_hidden_shape"] == [14336]
    assert proof["tensor_chain_evidence"]["local_hidden_rows"] == 2
    controllers = [event for event in events if event.op_type == "reduce_scatterAicpuKernel"]
    assert len(controllers) == 8
    assert all(event.end_ns < rows[-1].event.start_ns and id(event) not in bounds for event in controllers)
    report = auto_segment_decode_forwards(events, config)
    forward = report["forwards"][0]
    assert forward["body_forward_span_ms"] == pytest.approx(5.271545)
    assert forward["body_activity_ms"] == pytest.approx(5.131242)
    assert forward["body_internal_gap_ms"] == pytest.approx(.140303)
    assert forward["end_ns"] < forward["head_start_ns"]
    layers = [stage for stage in forward["stages"] if stage["layer_id"] is not None]
    assert [stage["span_ms"] for stage in layers] == pytest.approx([1.071841, 1.700794, 1.090382, 1.407568])
    assert len(layers[-1]["communication_envelope_bounds"]) == 1
    assert all(not stage.get("communication_envelope_bounds") for stage in layers[:-1])
    assert report["communication_envelope_accounting"]["unassigned_summary_suffix_total_ns"] == 9_710_834
    assert events == original
    assert _scope(rows[:-1], "target_body", "original_raw_envelopes")["span_ms"] == pytest.approx(14.090541)


@pytest.mark.parametrize("missing_link", ["declared_tp", "padding_input", "consumer_dtype", "following_local_rows"])
def test_padded_consumer_requires_complete_tp_tensor_chain(kimi_cross_head, missing_link):
    _, config, rows, norms = kimi_cross_head
    proof = next(iter(_communication_bounds(rows, config["hidden_size"], norms, rows[-1], tp=16).values()))
    changed, tp = list(rows), 16
    if missing_link == "declared_tp":
        tp = 8
    else:
        key = {"padding_input": "padding_locator", "following_local_rows": "following_hidden_matrix_locator"}
        locator = (proof["consumer_locator"] if missing_link == "consumer_dtype"
                   else proof["tensor_chain_evidence"][key[missing_link]])
        index = next(i for i, row in enumerate(rows) if row.event.locator == locator)
        row = rows[index]
        if missing_link == "consumer_dtype":
            changed[index] = _Row(replace(row.event, input_dtypes="DT_FLOAT16;" * 5 + "DT_FLOAT16"),
                                  row.inputs, row.outputs)
        elif missing_link == "padding_input":
            changed[index] = _Row(row.event, ((23, 7168), *row.inputs[1:]), row.outputs)
        else:
            changed[index] = _Row(row.event, ((3, 7168), *row.inputs[1:]), row.outputs)
    assert _communication_bounds(changed, config["hidden_size"], norms, rows[-1], tp=tp) == {}


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
    group = report["geometry_groups"][0]
    assert group["body_activity_ms"]["count"] == group["body_internal_gap_ms"]["count"] == 2
    assert group["body_activity_ms"]["mean"] + group["body_internal_gap_ms"]["mean"] == pytest.approx(
        group["body_forward_span_ms"]["mean"])
    for layer in group["per_layer_ms"]:
        assert layer["activity_ms_stats"]["count"] == layer["internal_gap_ms_stats"]["count"] == 2
        assert layer["activity_ms_stats"]["mean"] + layer["internal_gap_ms_stats"]["mean"] == pytest.approx(
            layer["stats"]["mean"])


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


def test_actual_a5_hccl_launch_suffix_crosses_norm_but_real_hcom_is_retained():
    identity = json.loads((FIXTURE / "qwen38_a5_hccl_launch_layer.provenance.json").read_text())
    rows = list(kernel_rows(FIXTURE / "qwen38_a5_hccl_launch_layer.csv", rank_id="rank_0"))
    source = [_Row(row.event, row.input_shapes, row.output_shapes) for row in rows
              if row.line < identity["next_layer_start_fixture_line"]]
    successor_raw = next(row for row in rows if row.line == identity["successor_norm_fixture_line"])
    successor = _Row(successor_raw.event, successor_raw.input_shapes, successor_raw.output_shapes)
    tail = next(row for row in source if row.kind == "HcclLaunchAicpuKernel"
                and row.event.end_ns > successor.event.start_ns)
    scope = _scope(source, "dense_layer", "actual_layer", successor=successor)
    hcom = [row for row in source if row.kind.startswith("hcom_")]
    assert hcom
    assert scope["end_ns"] >= max(row.event.end_ns for row in hcom)
    assert scope["end_ns"] < successor.event.start_ns < tail.event.end_ns
    assert scope["excluded_tail_wait_activity_ms"] > 0
    # With no successor dependency evidence this same captured AICPU duration
    # is retained; its name alone never authorizes truncating a measurement.
    unbounded = _scope(source, "dense_layer", "no_successor")
    assert unbounded["end_ns"] == max(row.event.end_ns for row in source)
    assert unbounded["excluded_tail_wait_activity_ms"] == 0


def test_device_activity_union_deduplicates_hcom_and_preserves_internal_gap(capture):
    events, _ = capture
    hcom = next(event for event in events if event.op_type == "hcom_allReduce_")
    compute = next(event for event in events if event.op_type == "QuantBatchMatmulV3")
    scheduler = next(event for event in events if event.op_type == "allreduceAicpuKernel")
    # Controlled intervals on actual exported event schemas. The communication
    # summary duplicates a device task; overlapping streams never add latency.
    selected = [replace(hcom, start_ns=100, end_ns=200, stream_id="comm"),
                replace(hcom, start_ns=100, end_ns=200, stream_id="N/A"),
                replace(compute, start_ns=150, end_ns=250, stream_id="compute"),
                replace(compute, start_ns=300, end_ns=400, stream_id="compute"),
                replace(scheduler, start_ns=100, end_ns=400, stream_id="scheduler")]
    rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)) for event in selected]
    scope = _scope(rows, "dense_layer", "overlap_and_gap")
    assert scope["span_ms"] == 300 / 1e6
    assert scope["device_activity_union_ms"] == 250 / 1e6
    assert scope["internal_uncovered_gap_ms"] == 50 / 1e6
    assert scope["activity_excluded_scheduler_event_count"] == 1
    streams = {row["stream_id"]: row["activity_union_ms"] for row in scope["per_stream_activity_ms"]}
    assert streams == {"comm": 100 / 1e6, "N/A": 100 / 1e6, "compute": 200 / 1e6}
    assert sum(streams.values()) > scope["device_activity_union_ms"]


def test_forward_consumer_receives_complete_layers_before_detail_limit(capture):
    events, config = capture
    seen = []
    def consume(result, segment):
        layers = [row for row in result["stages"] if row["layer_id"] is not None]
        seen.append((len(layers), len(segment), sum(row["span_ms"] for row in layers[1:])))
        assert segment[-1].start_ns == result["head_start_ns"]
        assert segment[-1].start_ns > result["end_ns"]
    report = auto_segment_decode_forwards(events, config, max_detailed_forwards=0,
                                         max_samples_per_layer=0, on_forward=consume)
    assert seen[0][:2] == (64, 1944)
    assert seen[0][2] > 0
    assert report["forwards"][0]["stages"] == []
    assert report["body_forward_span_ms"]["mean"] == pytest.approx(17.202996)


@pytest.mark.parametrize("output_rows", [6, 12])
def test_real_kimi_graph_padding_keeps_body_and_logits_geometry_separate(output_rows):
    stem = f"kimi4_tp8_head_unpad_c{output_rows}"
    events = [row.event for row in kernel_rows(FIXTURE / f"{stem}.csv")]
    config = json.loads((FIXTURE / "kimi4_tp8_model_config.json").read_text())
    evidence = json.loads((FIXTURE / f"{stem}.provenance.json").read_text())
    report = auto_segment_decode_forwards(events, config)
    forward = report["forwards"][0]
    assert report["body_forward_span_ms"]["count"] == 1
    assert report["anomaly_counts"] == {}
    assert report["geometry"]["query_rows"] == evidence["expected_body_query_rows"]
    assert report["geometry"]["sequences_per_replica"] == evidence["expected_body_query_rows"]
    assert report["geometry"]["tokens_per_sequence"] == 1
    assert report["geometry"]["output_query_rows"] == output_rows
    assert forward["confidence"]["matched_layers"] == 4
    assert forward["start_ns"] == evidence["expected_body_start_ns"]
    assert forward["end_ns"] == evidence["expected_body_end_ns"]
    assert forward["head_start_ns"] == evidence["expected_head_start_ns"]
    assert forward["body_forward_span_ms"] == evidence["expected_body_span_ms"]
    body = next(stage for stage in forward["stages"] if stage["kind"] == "target_body")
    for endpoint in ("first_locator", "last_locator"):
        assert {k: v for k, v in body["evidence"][endpoint].items() if k != "source"} == {
            k: v for k, v in evidence[f"expected_{endpoint}"].items() if k != "source"}
    assert report["scan_counts"]["complete_body_segment_events"] == len(events)


def test_kimi_padding_does_not_accept_inconsistent_body_attention():
    events = [row.event for row in kernel_rows(FIXTURE / "kimi4_tp8_head_unpad_c6.csv")]
    config = json.loads((FIXTURE / "kimi4_tp8_model_config.json").read_text())
    kda = next(event for event in events if event.op_type == "RecurrentKda")
    # Controlled corruption of a real body query slot, not another capture.
    changed = replace(kda, input_shapes=kda.input_shapes.replace("1,8,12,128", "1,6,12,128"))
    report = auto_segment_decode_forwards([changed if event is kda else event for event in events], config)
    assert report["body_forward_span_ms"]["count"] == 0
    assert report["anomaly_counts"] == {"layer_query_geometry_changes": 1}


def test_same_padded_body_different_output_rows_are_distinct_populations():
    events = [row.event for row in kernel_rows(FIXTURE / "kimi4_tp8_head_unpad_c6.csv")]
    config = json.loads((FIXTURE / "kimi4_tp8_model_config.json").read_text())
    # Controlled second logits-selection boundary on the same captured body.
    shifted = [replace(event, start_ns=event.start_ns + 1_000_000_000,
                       end_ns=event.end_ns + 1_000_000_000) for event in events]
    shifted[-1] = replace(shifted[-1], input_shapes='"8,7168;20480,7168"',
                          output_shapes='"8,20480"')
    report = auto_segment_decode_forwards([*events, *shifted], config)
    assert report["body_forward_span_ms"]["count"] == 2
    assert {group["geometry"]["output_query_rows"] for group in report["geometry_groups"]} == {6, 8}
    assert all(group["body_forward_span_ms"]["count"] == 1 for group in report["geometry_groups"])
