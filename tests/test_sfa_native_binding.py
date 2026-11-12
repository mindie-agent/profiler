"""Focused R64 packed sparse-attention native binding test."""
from __future__ import annotations

import copy
import os
from dataclasses import replace
import sys
from pathlib import Path

import pytest

pytest.importorskip("mindie_sim")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
import zero_shot_piecewise_validation as z  # noqa: E402
from mindie_sim.prediction.piecewise import (  # noqa: E402
    ImplementationPolicy, OperatorPiecewiseCompiler, PipeSupply,
    RequestGeometry, WorkloadGeometry,
)
from mindie_sim.prediction.structure import parse_case  # noqa: E402
from mindie_sim.prediction.subgraphs.instantiate import (  # noqa: E402
    FeatureConfig, instantiate_model,
)

R64 = "sha256:8d422528ac20a8babcbbf93762cde3b47d4db6c5f7ab777f4f1f65b32b89ab3e"
UNKNOWN = "sha256:" + "f" * 64
R64_SOURCE = "2a2512595a08b1fd58f69772cf3cc830c0b62f702365f80160c7fa6df3981a5d"
CELL = "glm51_dp16tp1ep16_pf_1k_c1"
CELL_R35 = "glm53w8a8c8_dp32tp1ep32_on_prefill_1024_c1"


def _cell(cell_id: str = CELL):
    path = Path(os.environ.get(
        "MINDIE_ZERO_SHOT_JSONL",
        "/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl"))
    if not path.is_file():
        pytest.skip("original 731 jsonl unavailable")
    return next(c for c in z.load_benchmark_jsonl(path) if c.spec.cell_id == cell_id)


def _build(cell, *, image_id: str):
    raw = copy.deepcopy(z._raw_case(cell.spec))
    meta = dict(raw["runtime"]["metadata"])
    meta["image_id"] = image_id
    meta.pop("mx_quant_source_revision", None)
    raw["runtime"]["metadata"] = meta
    case = parse_case(raw)
    features = FeatureConfig.from_runtime(case.runtime, case.model).project(
        tp=cell.spec.tp, dp=cell.spec.dp, ep=cell.spec.ep, pp=cell.spec.pp,
        cores=64, graph_buckets=cell.spec.graph_buckets)
    instantiated = instantiate_model(case.model, features)
    instance = next(item for layer in instantiated.layers
                    for item in layer.subgraphs
                    if item.kind == "A1"
                    and any(op.name == "mla_attention" for op in item.operators))
    compiler = OperatorPiecewiseCompiler(
        PipeSupply.from_hardware(case.machine, dtype="bf16"),
        ImplementationPolicy(cores=64))
    return compiler.compile(instance, feature_metadata=features.metadata)


def _eval(compiled, m: int, requests: int = 1, *, phase: str = "prefill",
          context: int = 0):
    geometry = WorkloadGeometry(
        tuple(RequestGeometry(m, context if phase == "decode" else m, phase=phase)
              for _ in range(requests)),
        phase=phase, cohort_batch=requests, local_batch=requests)
    return {cost.name: cost for cost in compiled.evaluate(geometry).operators}["mla_attention"]


def test_r64_packed_sfa_typed_nine_inputs_and_wrong_source_control():
    cell = _cell()
    first = {row.name: row for row in z.predict_cell(cell.spec).rows}["mla_attention"]
    second = {row.name: row for row in z.predict_cell(
        replace(cell.spec, prompt_tokens=2048)).rows}["mla_attention"]
    dc = {row.name: row for row in z.predict_cell(
        _cell("glm51_dp16tp1ep16_dc_1k_c32").spec).rows}["mla_attention"]
    call, occurrence = first.native_call, first.native_occurrence
    assert call["api"]["entry"] == "torch_npu.npu_kv_quant_sparse_flash_attention"
    assert call["api"]["version"] == "r64/8d422528"
    assert call["source"]["sha256"] == R64_SOURCE
    assert call["source"]["path"] == "vllm_ascend/device/device_op.py"
    assert call["source"]["symbol"] == "A5DeviceAdaptor._execute_kv_quant_sparse_flash_attention_vllm"
    assert call["kernels"][0]["caller_sha256"].startswith("22593148")
    assert occurrence["status"] == "bound"
    assert call["typed"]["shapes"] == {
        "query": [64, 576], "key": [128, 1, 656], "value": [128, 1, 656],
        "sparse_indices": [1, 2048], "block_table": [1088],
        "output": [64, 512],
    }
    assert call["typed"]["attrs"]["layout_kv"] == "PA_BSND"
    assert call["typed"]["attrs"]["quant_mode"] == 2
    assert call["typed"]["attrs"]["sparse_mode"] == 3
    assert call["typed"]["attrs"]["attention_mode"] == 2
    assert call["typed"]["attrs"]["quant_scale_repo_mode"] == 1
    assert call["typed"]["attrs"]["rope_head_dim"] == 64
    assert call["typed"]["attrs"]["optional_null_inputs"] == [
        "key_quant_scale", "value_quant_scale"]
    prepared = occurrence["prepare"]
    assert prepared["complete"] is False
    assert prepared["source_lines"] == [1122, 1181]
    assert prepared["shapes"]["query"] == [1024, 64, 576]
    assert prepared["shapes"]["key"] == [None, 128, 1, 656]
    assert prepared["shapes"]["value"] == [None, 128, 1, 656]
    assert prepared["shapes"]["sparse_indices"] == [1024, 1, 2048]
    assert prepared["shapes"]["block_table"] == [1, 1088]
    assert prepared["shapes"]["output"] == [1024, 64, 512]
    assert prepared["shapes"]["key_quant_scale"] is None
    assert prepared["shapes"]["value_quant_scale"] is None
    assert prepared["aliases"]["key"] == "value"
    assert prepared["match"]["key_value_alias"] is True
    assert "sfa_prepare_partial" in occurrence["unresolved"]
    assert second.native_call["call_id"] == call["call_id"]
    assert second.native_occurrence["prepare"]["shapes"]["query"] == [2048, 64, 576]
    assert second.native_occurrence["prepare"]["shapes"]["output"] == [2048, 64, 512]
    assert dc.native_occurrence["prepare"]["shapes"]["query"] == [2, 64, 576]
    assert dc.native_occurrence["prepare"]["shapes"]["block_table"] == [2, 1088]
    assert dc.native_occurrence["prepare"]["shapes"]["actual_seq_lengths_query"] == [2]
    assert dc.native_occurrence["prepare"]["shapes"]["actual_seq_lengths_kv"] == [2]
    assert dc.native_occurrence["prepare"]["shapes"]["output"] == [2, 64, 512]
    assert "sfa_prepare_partial" in dc.native_occurrence["unresolved"]

    r35 = {row.name: row for row in z.predict_cell(
        _cell(CELL_R35).spec).rows}["mla_attention"]
    assert r35.native_call["api"]["entry"] == "torch_npu.npu_kv_quant_sparse_flash_attention"
    assert r35.native_call["api"]["version"] == "r35/5461a1a8"
    assert r35.native_call["source"]["sha256"] == "f4392f346816c85f138d7e033a924c6b628ae684cd4fcd7a6d8818518351b5c9"
    assert r35.native_occurrence["prepare"]["shapes"]["block_table"] == [1, 1026]
    assert r35.native_occurrence["prepare"]["complete"] is False
    unknown = _eval(_build(cell, image_id=UNKNOWN), 1024)
    assert unknown.native_call is None


def test_r64_i1_c8_selector_and_actual_ordinary_packet():
    from mindie_sim.prediction.piecewise.native_calls import _indexer_spec

    positive = {
        "source_family": "A5DeviceAdaptor.indexer_select_post_process",
        "image_id": R64, "q_dtype": "fp8_e4m3", "k_dtype": "fp8_e4m3",
        "query_scale_present": True, "query_scale_dtype": "fp32",
        "layout_query": "TND", "layout_key": "PA_BSND",
        "query_quant_mode": 0, "key_quant_mode": 0,
    }

    class FakeTheta:
        extras = {"candidate_blocks": 2048}

        def find(self, key, default=None):
            return positive if key == "indexer_source" else self.extras.get(key, default)

    metadata = (("image_id", R64), ("max_model_len", 139264))
    spec = _indexer_spec(FakeTheta(), {"candidate_blocks": "2048"},
                         kind="I1", name="index_score",
                         feature_metadata=metadata)
    assert spec is not None
    assert spec.typed["attrs"]["qscale_present"] is True
    assert spec.typed["attrs"]["query_dtype"] == "fp8_e4m3"
    for change in ({"q_dtype": "fp4_e2m1", "query_scale_dtype": "fp8_e8m0"},
                   {"query_scale_present": False},
                   {"q_dtype": "bf16", "k_dtype": "bf16"},
                   {"image_id": "sha256:" + "f" * 64}):
        bad = {**positive, **change}

        class BadTheta:
            def find(self, key, default=None, _d=bad):
                return _d if key == "indexer_source" else default

        assert _indexer_spec(BadTheta(), {"candidate_blocks": "2048"},
                             kind="I1", name="index_score",
                             feature_metadata=metadata) is None
    cell = _cell()
    rows = {row.name: row for row in z.predict_cell(cell.spec).rows}
    assert rows["index_score"].native_call["api"]["entry"] == (
        "torch_npu.npu_quant_lightning_indexer")
    assert rows["topk"].native_call["call_id"] == rows["index_score"].native_call["call_id"]
    packet = Path("/tmp/mindie-7337-20261111-1457/obs-r4/indexer-ordinary-first.json")
    if packet.is_file():
        import json
        evidence = json.loads(packet.read_text())
        returned = evidence["cases"]["glm51_dp16tp1ep16_dc_1k_c32"]["returned"][0]
        assert returned["call"]["source"]["sha256"] == R64_SOURCE
        assert returned["call"]["source"]["symbol"] == "A5DeviceAdaptor.indexer_select_post_process"
        assert returned["call"]["api"]["entry"] == "torch_npu.npu_quant_lightning_indexer"
        assert returned["call"]["typed"]["shapes"]["query"] == [32, 128]


def test_ordinary_r64_i1_binds_one_fused_owner_pf_and_dc(monkeypatch):
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
                       "/private/tmp/mindie-7337-20261111-1457/header-provenance")
    for cell_id, q_rows, batch, table in (
            (CELL, 1024, 1, [1, 1088]),
            ("glm51_dp16tp1ep16_dc_1k_c32", 2, 2, [2, 1088])):
        pred = z.predict_cell(_cell(cell_id).spec)
        rows = {row.name: row for row in pred.rows}
        fused = rows["fused:quant_lightning_indexer"]
        score = rows["index_score"]
        topk = rows["topk"]
        assert fused.native_call["api"]["entry"] == "torch_npu.npu_quant_lightning_indexer"
        assert fused.native_call["source"]["sha256"] == R64_SOURCE
        assert score.native_call["call_id"] == fused.native_call["call_id"]
        assert topk.native_call["call_id"] == fused.native_call["call_id"]
        assert fused.native_occurrence["charge"] == "call"
        assert fused.native_occurrence["typed"]["shapes"]["query"] == [q_rows, 32, 128]
        assert fused.native_occurrence["typed"]["attrs"]["batch"] == batch
        assert fused.native_occurrence["prepare"]["match"]["m"] == q_rows
        assert fused.native_occurrence["prepare"]["complete"] is False
        assert score.native_occurrence["charge"] == "none"
        assert topk.native_occurrence["charge"] == "none"
        prepared = score.native_occurrence["prepare"]
        assert prepared["complete"] is False
        assert prepared["shapes"]["query"] == [q_rows, 32, 128]
        assert prepared["shapes"]["key"] == [None, 128, 1, 128]
        assert prepared["shapes"]["weights"] == [q_rows, 32]
        assert prepared["shapes"]["query_dequant_scale"] == [q_rows, 32]
        assert prepared["shapes"]["block_table"] == table
        assert prepared["shapes"]["actual_seq_lengths_query"] == [batch]
        assert prepared["shapes"]["output"] == [q_rows, 1, 2048]
        assert prepared["match"]["query_dtype"] == "fp8_e4m3"
        assert prepared["match"]["key_dtype"] == "fp8_e4m3"
        assert prepared["match"]["query_scale_dtype"] == "fp32"
        coverage = z._native_forecast((pred,))["overall"]
        owner = next(item for item in coverage["fused_owners"]
                     if item["owner"] == "fused:quant_lightning_indexer")
        assert owner["count"] == 78


def test_i1_absent_scale_does_not_emit_c8_fusion_or_native_work():
    cell = _cell()
    raw = copy.deepcopy(z._raw_case(cell.spec))
    raw["runtime"]["metadata"] = dict(raw["runtime"]["metadata"])
    raw["runtime"]["metadata"]["indexer_query_scale_present"] = False
    case = parse_case(raw)
    features = FeatureConfig.from_runtime(case.runtime, case.model).project(
        tp=cell.spec.tp, dp=cell.spec.dp, ep=cell.spec.ep, pp=cell.spec.pp,
        cores=64, graph_buckets=cell.spec.graph_buckets)
    instantiated = instantiate_model(case.model, features)
    i1 = next(item for layer in instantiated.layers
              for item in layer.subgraphs if item.kind == "I1")
    assert not any(fusion.name == "quant_lightning_indexer"
                   for fusion in i1.template.fusions)
    for operator in i1.operators:
        assert operator.theta.find("indexer_source", None) is None


def test_ordinary_r64_f1_gating_and_f2_weighted_return_pf_dc(monkeypatch):
    monkeypatch.setenv("MINDIE_WEIGHT_HEADER_PROVENANCE_ROOT",
                       "/private/tmp/mindie-7337-20261111-1457/header-provenance")
    for cell_id, phase in ((CELL, "pf"), ("glm51_dp16tp1ep16_dc_1k_c32", "dc")):
        pred = z.predict_cell(_cell(cell_id).spec)
        rows = {row.name: row for row in pred.rows}
        gate = rows["router_topk"]
        assert gate.native_call["api"]["entry"] == "torch_npu.npu_moe_gating_top_k"
        assert gate.native_call["source"]["sha256"] == R64_SOURCE
        assert gate.native_occurrence["charge"] == "call"
        assert gate.native_occurrence["prepare"]["shapes"]["x"] == (
            [1024, 256] if phase == "pf" else [2, 256])
        assert gate.native_occurrence["prepare"]["shapes"]["topk_ids"] == (
            [1024, 8] if phase == "pf" else [2, 8])
        assert rows["router_gemm"].native_call is None
        gate_up = rows["expert_gate_up"]
        assert gate_up.native_call["api"]["entry"] == (
            "torch_npu.npu_grouped_matmul_swiglu_quant_v2")
        assert gate_up.native_occurrence["charge"] == "call"
        for rope_name, key_width in (("index_rope", 32), ("index_k_rope", 1)):
            rope = rows[rope_name]
            assert rope.native_call["api"]["entry"] == "rope_forward_triton_siso"
            assert rope.native_occurrence["charge"] == "call"
            expected_m = 1024 if phase == "pf" else 2
            assert rope.native_occurrence["prepare"]["shapes"]["qk"] == [
                expected_m, key_width, 128]
        k_norm = rows["index_k_norm"]
        assert k_norm.native_call["api"]["entry"] == "torch.nn.functional.layer_norm"
        assert k_norm.native_occurrence["charge"] == "call"
        assert k_norm.native_occurrence["prepare"]["shapes"]["input"][-1] == 128
        histogram = rows["router_histogram"]
        if phase == "pf":
            assert histogram.native_call["api"]["entry"] == "torch.histc"
            assert histogram.native_occurrence["charge"] == "call"
            assert histogram.native_occurrence["prepare"]["shapes"]["histogram"] == [256]
            assert histogram.native_occurrence["prepare"]["arguments"]["bins"] == 256
        else:
            assert histogram.native_call is None
        permute = rows["router_permute"]
        if phase == "pf":
            assert permute.native_call["api"]["entry"] == (
                "torch_npu.npu_moe_token_permute")
            assert permute.native_occurrence["charge"] == "call"
            prepared = permute.native_occurrence["prepare"]
            assert prepared["shapes"]["tokens"] == [1024, 6144]
            assert prepared["shapes"]["permuted_tokens"] == [8192, 6144]
            assert prepared["arguments"]["num_out_tokens"] == 8192
        else:
            assert permute.native_call is None
        unweighted = rows.get("router_unweighted_reorder")
        if phase == "pf":
            assert unweighted.native_call["api"]["entry"] == (
                "torch_npu.npu_moe_token_unpermute")
            assert unweighted.native_occurrence["charge"] == "call"
        else:
            assert unweighted is not None
            assert unweighted.native_call is None
        finalize = rows.get("router_finalize")
        if phase == "pf":
            assert finalize.native_call["api"]["entry"] == (
                "torch_npu.npu_moe_token_unpermute")
            assert finalize.native_occurrence["charge"] == "call"
            prepared = finalize.native_occurrence["prepare"]
            assert prepared["shapes"]["permuted_tokens"] == [8192, 6144]
            assert prepared["shapes"]["sorted_indices"] == [8192]
            assert prepared["shapes"]["probs"] == [1024, 8]
            assert prepared["shapes"]["output"] == [1024, 6144]
            assert prepared["match"]["weighted"] is True
            assert prepared["arguments"]["permuted_tokens"] == "permuted_tokens"
        else:
            # DC remains the signed MC2 V3 path; no PF finalize is fabricated.
            assert finalize is not None
            assert finalize.native_call is None


def test_f3_unweighted_finalize_is_distinct_from_weighted_return():
    pred = z.predict_cell(_cell().spec)
    row = next(row for row in pred.rows
               if row.name == "router_unweighted_reorder")
    assert row.native_call["api"]["entry"] == "torch_npu.npu_moe_token_unpermute"
    assert row.native_call["source"]["sha256"] == R64_SOURCE
    occurrence = row.native_occurrence
    assert occurrence["charge"] == "call"
    assert occurrence["typed"]["attrs"]["weighted"] is False
    assert occurrence["typed"]["attrs"]["router_symbolic_input"] is True
    assert occurrence["typed"]["shapes"]["permuted_tokens"] == [None, 6144]
    assert occurrence["typed"]["shapes"]["output"] == [None, 6144]
    prepared = occurrence["prepare"]
    assert prepared["complete"] is False
    assert prepared["partial"] is True
    assert prepared["partial_reasons"] == ["router_received_rows_unresolved"]
    assert prepared["arguments"]["probs"] is None
    assert "probs" in prepared["argument_order"]
    assert prepared["optional_slots"]["probs"] == "present_none"
    finalize = next(row for row in pred.rows if row.name == "router_finalize")
    assert finalize.native_call["call_id"] != row.native_call["call_id"]
