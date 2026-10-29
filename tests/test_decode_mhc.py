"""Actual mHC body closure and new GLM paged MLA ABI regression evidence."""
import json
from pathlib import Path

import pytest

from mindie_profiler.decode_segmentation import _Row, _anchor, _query_geometry, auto_segment_decode_forwards
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_scope

FIXTURE = Path(__file__).parent / "fixtures/decode_forward"


def test_v41_hidden_output_forward_closes_at_real_final_norm_without_a_head():
    rows = list(kernel_rows(FIXTURE / "v41_dp8_first_body.csv"))
    config = json.loads((FIXTURE / "v41_dp8_model_config.json").read_text())
    result = auto_segment_decode_forwards(rows, config)
    forward = result["forwards"][0]
    assert result["body_forward_span_ms"]["count"] == 1
    assert forward["body_forward_span_ms"] == pytest.approx(13.848067)
    assert forward["geometry"]["sequences_per_replica"] == 1
    assert forward["geometry"]["tokens_per_sequence"] == 1
    assert forward["head_start_ns"] is None
    assert forward["confidence"]["closure_basis"] == "mhc_final_norm"
    assert not forward["confidence"]["vocabulary_head_contract_matches"]
    layers = [stage for stage in forward["stages"] if stage["layer_id"] is not None]
    assert len(layers) == 40
    assert layers[0]["evidence"]["first_locator"]["csv_line"] == 65
    assert layers[-1]["evidence"]["last_locator"]["csv_line"] == 1808
    assert all(layer["span_ms"] == pytest.approx(layer["device_activity_union_ms"]
                                               + layer["internal_uncovered_gap_ms"])
               for layer in layers)
    final = next(stage for stage in forward["stages"] if stage["kind"] == "final_norm")
    assert final["evidence"]["first_locator"]["csv_line"] == 1813
    # An unexported attention ABI remains unexported after structural alignment.
    anchors = [row for row in rows if row.event.op_type == "MqsmlaKernel___call__"]
    assert len(anchors) == 40
    assert all(row.input_shapes is None and observed_contract(row) is None for row in anchors)
    broken = auto_segment_decode_forwards([row for row in rows if row is not anchors[0]], config)
    assert broken["body_forward_span_ms"]["count"] == 0
    assert broken["anomaly_counts"]["auxiliary_or_partial_layer_sequence"] == 1
    no_source = {key: value for key, value in config.items() if key != "source_attention_anchors"}
    assert auto_segment_decode_forwards(rows, no_source)["body_forward_span_ms"]["count"] == 0


def test_complete_v4_mhc_body_excludes_output_head_collapse():
    rows = list(kernel_rows(FIXTURE / "v4f_a3_mhc_verify.csv"))
    config = json.loads((FIXTURE / "v4f_model_config.json").read_text())
    result = auto_segment_decode_forwards(rows, config)
    assert result["body_forward_span_ms"]["count"] == 1
    assert result["body_forward_span_ms"]["mean"] == pytest.approx(29.317754)
    assert result["geometry"]["tokens_per_sequence"] == 2
    assert result["geometry"]["sequences_per_replica"] == 1
    forward = result["forwards"][0]
    layers = [stage for stage in forward["stages"] if stage["layer_id"] is not None]
    assert len(layers) == 43
    by_line = {row.event.locator["csv_line"]: row.event for row in rows}
    for layer in layers:
        first = by_line[layer["evidence"]["first_locator"]["csv_line"]]
        assert first.op_type == "HcPre"
        assert layer["device_activity_union_ms"] + layer["internal_uncovered_gap_ms"] == pytest.approx(layer["span_ms"])
    assert by_line[layers[-1]["evidence"]["last_locator"]["csv_line"]].op_type == "HcPost"
    preparation = next(stage for stage in forward["stages"] if stage["kind"] == "output_head_preparation")
    assert preparation["span_ms"] == pytest.approx(0.474830)
    assert forward["end_ns"] < preparation["start_ns"] < forward["head_start_ns"]
    # Removal probes use this unchanged capture but are not hardware evidence.
    last_post = by_line[layers[-1]["evidence"]["last_locator"]["csv_line"]]
    broken = auto_segment_decode_forwards([row for row in rows if row.event is not last_post], config)
    assert broken["body_forward_span_ms"]["count"] == 0


def test_actual_glm_flash_mla_abis_supply_active_query_not_cache_capacity():
    rows = list(kernel_rows(FIXTURE / "glm_flash_mla_abi.csv"))
    config = {"layer_plans": [{"attention": "kda"}, {"attention": "mla"}]}
    geometry = []
    for item in rows:
        row = _Row(item.event, item.input_shapes, item.output_shapes)
        assert _anchor(row, config) == "mla"
        geometry.append(_query_geometry([row], item.input_shapes[0][0]))
        # Preserve the actual native interface until a source-declared active
        # projection is available; packed INT8 KV is not a BF16 latent cache.
        contract = observed_contract(item)
        assert contract[0] == "native_tensor_abi"
        assert len(contract[2]) == (18 if row.kind == "SparseFlashMla" else 9)
        assert contract[2][1][1] == ("bf16" if row.kind == "SparseFlashMla" else "int8")
        assert not observed_contract_scope(item)["occurrence_identity"]
    assert [item["sequences_per_replica"] for item in geometry] == [1, 1]
    assert [item["tokens_per_sequence"] for item in geometry] == [4, 256]
    assert all(item["context_tokens"] is None for item in geometry)


def test_glm78_quantized_kv_keeps_packed_cache_and_separates_long_and_short_query():
    rows = list(kernel_rows(FIXTURE / "glm78_kvquant_sparse_abi.csv"))
    geometry = []
    for item in rows:
        row = _Row(item.event, item.input_shapes, item.output_shapes)
        assert _anchor(row, {"layer_plans": [{"attention": "mla"}]}) == "mla"
        geometry.append(_query_geometry([row], item.input_shapes[0][0]))
        native = observed_contract(item)
        assert native[2][0][0][-1] == 576
        assert native[2][1][0][-1] == 656
        assert native[2][1][1] == "int8"
    assert [item["tokens_per_sequence"] for item in geometry] == [256, 6]
    assert all(item["sequences_per_replica"] == 1 for item in geometry)
