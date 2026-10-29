"""Real model-body rows against independent sim frontend declarations.

These are offline contract replays. Explicit occurrence annotations in the
binding control are test inputs, not evidence of a newly collected module.
"""
from dataclasses import replace
import json
from pathlib import Path
import runpy

import pytest

from mindie_profiler.analyze import analyze_profile
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.normalized import kernel_rows, row_from_event
from mindie_profiler.structure_mapping import StructureMapper
from mindie_profiler.tensor_contracts import observed_contract


FIXTURES = Path(__file__).parent / "fixtures"


def declaration(name, tokens, **kwargs):
    structure = pytest.importorskip("mindie_sim.structure")
    case = Path(structure.__file__).resolve().parents[1] / "examples/cases" / f"{name}.json"
    if not case.exists():
        pytest.skip("the sim source checkout's declared cases are required")
    return structure.export_structure(
        json.loads(case.read_text()), phase="prefill", tokens=tokens, scope="model", **kwargs)


def mapped(group, capture, manifest, **kwargs):
    return analyze_profile(
        FIXTURES / group / capture, source="csv", full_range=True,
        structure=manifest, **kwargs,
    )["structure_mapping"]


@pytest.mark.parametrize("name,capture,tokens", [
    ("qwen35-a3-tp4", "a3_qwen35.csv", 8192),
    ("qwen36-a3-tp4", "a3_qwen36.csv", 8192),
    ("qwen38-a5", "a5_qwen38.csv", 16384),
])
def test_real_body_matches_keep_layers_ambiguous_until_occurrence_evidence(
    name, capture, tokens,
):
    manifest = declaration(name, tokens)
    attention = mapped("attention_cache_contracts", capture, manifest)
    fused = mapped("body_fused", capture, manifest)
    by_kind = {}
    for row in [*attention["event_mappings"], *fused["event_mappings"]]:
        by_kind.setdefault(row["operator_type"], row)
    expected_families = {
        "FusedInferAttentionScore": "attention",
        "ScatterPaKvCache": "cache_store",
        "_layer_norm_fwd_1pass_kernel_npu": "linear_attention",
    }
    nodes = {node["node_id"]: node for node in manifest["nodes"]}
    for kind, family in expected_families.items():
        row = by_kind[kind]
        assert row["status"] == "ambiguous"
        assert row["basis"] == "repeated_tensor_contract"
        assert row["node_ids"] == []
        assert row["candidate_count"] > 1
        selected = [nodes[key] for key in row["candidate_node_ids"]]
        if kind == "_layer_norm_fwd_1pass_kernel_npu":
            assert all(node["recipe"] == "linear_output_norm_gate" for node in selected)
        else:
            assert all(node["family"] == family for node in selected)
        assert len({node["layer"] for node in selected}) == len(selected)
        assert row["observed_contract_scope"]
        if kind in {"FusedInferAttentionScore", "ScatterPaKvCache"}:
            assert row["observed_native_tensor_abi"][:2] == ("native_tensor_abi", kind)
    incomplete = by_kind["split_qkv_rmsnorm_mrope_kernel"]
    assert incomplete["status"] == "unmapped"
    assert incomplete["diagnostic"]["category"] == "capture_metadata_missing"
    assert incomplete["diagnostic"]["reason"] == "incomplete_native_tensor_slots"
    assert not incomplete["candidate_node_ids"]
    assert attention["windows"][0]["bound_busy_union_ns"] == 0
    assert fused["windows"][0]["bound_busy_union_ns"] == 0
    per_operator = {row["operator_type"]: row for row in attention["windows"][0]["operators"]}
    assert per_operator["ScatterPaKvCache"]["contract_available_events"] > 0
    assert per_operator["ScatterPaKvCache"]["status_counts"]["ambiguous"] > 0


def test_shared_cache_does_not_claim_model_identity_and_wrong_attention_stays_unmapped():
    manifest = declaration("qwen35-a3-tp4", 8192)
    report = mapped("attention_cache_contracts", "a3_qwen36.csv", manifest)
    cache, attention = report["event_mappings"]
    assert cache["status"] == "ambiguous"
    assert attention["status"] == "unmapped"
    assert attention["candidate_node_ids"] == []
    assert attention["diagnostic"]["category"] == "declared_structure_mismatch"
    assert report["windows"][0]["nodes"] == []


def test_body_occurrence_binding_preserves_contract_and_phase_guards():
    manifest = declaration("qwen38-a5", 16384)
    baseline = mapped("attention_cache_contracts", "a5_qwen38.csv", manifest)
    selected = next(row for row in baseline["event_mappings"]
                    if row["operator_type"] == "FusedInferAttentionScore")
    node_id = selected["candidate_node_ids"][0]
    bindings = {
        "schema_version": "mindie-profile-bindings/1", "graph_id": manifest["graph_id"],
        "events": [{
            "event_id": selected["event_id"], "node_ids": [node_id],
            "evidence": {"source": "controlled occurrence annotation; no collected module claim"},
        }],
    }
    report = mapped("attention_cache_contracts", "a5_qwen38.csv", manifest,
                    structure_bindings=bindings)
    assert report["status_counts"]["bound"] == 1
    bound = next(row for row in report["event_mappings"] if row["status"] == "bound")
    assert bound["node_ids"] == [node_id]
    assert bound["observed_contract_scope"] == selected["observed_contract_scope"]
    assert report["windows"][0]["nodes"][0]["event_count"] == 1

    cache = next(row for row in baseline["event_mappings"]
                 if row["operator_type"] == "ScatterPaKvCache")
    bindings["events"][0]["node_ids"] = [cache["candidate_node_ids"][0]]
    with pytest.raises(ProfilerUsageError, match="tensor contract mismatch"):
        mapped("attention_cache_contracts", "a5_qwen38.csv", manifest,
               structure_bindings=bindings)
    with pytest.raises(ProfilerUsageError, match="scene phase"):
        StructureMapper(manifest, phase="decode")


def test_native_layout_or_operator_identity_never_becomes_same_active_contract():
    row = next(row for row in kernel_rows(
        FIXTURES / "attention_cache_contracts/a5_qwen38.csv")
        if row.kind == "FusedInferAttentionScore")
    manifest = declaration("qwen38-a5", 16384)
    mapper = StructureMapper(manifest)
    expected = observed_contract(row)
    assert expected in mapper.contracts
    changed = row_from_event(replace(
        row.event, input_formats=row.event.input_formats.replace("ND", "NCL", 1)))
    assert observed_contract(changed) not in mapper.contracts
    different_kind = row_from_event(replace(row.event, op_type="SparseFlashAttention"))
    assert observed_contract(different_kind) not in mapper.contracts


@pytest.mark.parametrize("name,capture,kind", [
    ("glm53-a3-w4a8", "a3_glm53.csv", "SparseFlashAttention"),
    ("v4f-a3-w8a8-tp8", "a3_deepseek_v4f.csv", "SparseAttnSharedkv"),
    ("v4f-a3-w8a8-tp8", "a3_deepseek_v4f_compressed.csv", "SparseAttnSharedkv"),
])
def test_sparse_model_body_maps_only_its_native_role_and_cache_presence(name, capture, kind):
    manifest = declaration(name, 4096)
    result = mapped("attention_cache_contracts", capture, manifest)
    events = [row for row in result["event_mappings"] if row["operator_type"] == kind]
    assert events
    nodes = {node["node_id"]: node for node in manifest["nodes"]}
    for row in events:
        assert row["status"] == "ambiguous"
        assert row["candidate_count"] > 1
        assert row["observed_contract"][:2] == ("sparse_attention_active", kind)
        assert row["observed_native_tensor_abi"][:2] == ("native_tensor_abi", kind)
        assert all(nodes[key]["family"] == "attention" for key in row["candidate_node_ids"])
        assert row["node_ids"] == []
    assert result["windows"][0]["bound_busy_union_ns"] == 0


def test_kimi_norm_gate_keeps_primary_output_scope_and_original_missing_fields():
    manifest = declaration("kimi-k3-a5", 8192)
    result = mapped("body_fused", "kimi_a5_norm_gate.csv", manifest)
    complete, missing = result["event_mappings"]
    assert complete["status"] == "ambiguous"
    assert complete["observed_contract"][0] == "gated_norm_active_rows"
    assert complete["observed_native_tensor_abi"][1] == "layer_norm_gated_fwd_kernel"
    assert complete["observed_contract_scope"]["compared_output_slots"] == ["primary_output"]
    assert missing["status"] == "unmapped" and missing["observed_contract"] is None
    assert missing["diagnostic"]["category"] == "capture_metadata_missing"
    assert not missing["candidate_node_ids"]


def test_streaming_replay_retains_body_evidence_without_double_counting():
    structure = pytest.importorskip("mindie_sim.structure")
    case = Path(structure.__file__).resolve().parents[1] / "examples/cases/qwen38-a5.json"
    example = Path(__file__).resolve().parents[1] / "examples/structure/replay_body_capture.py"
    replay = runpy.run_path(str(example))["replay"]
    report = replay(
        FIXTURES / "body_fused/a5_qwen38.csv", case,
        phase="prefill", tokens=16384, mapping_limit=0)
    assert report["positive_event_count"] == 4
    assert sum(report["status_counts"].values()) == 4
    assert report["body_contracts"]["event_count"] == 4
    assert report["retained_examples"] == []
    examples = report["retained_body_examples"]
    assert len(examples) == 4
    assert {row["operator_type"] for row in examples} == {
        "_layer_norm_fwd_1pass_kernel_npu", "split_qkv_rmsnorm_mrope_kernel",
    }
    assert all(row["observed_contract_scope"] is not None for row in examples)
