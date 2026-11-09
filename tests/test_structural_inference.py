"""Behavioral tests for bottom-up structural module, speculative, and envelope inference.

[Role]
  Verify that ``infer_trace_structure`` discovers repeating target-body layers
  (including hybrid Attention+KDA/GDN and Dense+MoE splits), fused composite
  subgraphs (both known like ``MegaMoe`` and unseen vendor-fused kernels),
  speculative decoding draft/verify stacks (DSpark/MTP/DFlash), and O(1)
  framework envelope operators without arbitrary single-family forced mapping.

[Invariants]
  * Pure Tier-0 in-memory execution (< 2s); zero host filesystem pollution.
  * Unseen fused operators bind to enclosing L2 subgraphs via multiplicity and
    missing-subgraph complementarity and emit explicit ``AgentDecisionItem`` records.

[Timeouts & Locks]
  In-memory unit tests; no external processes or locks.

[Side-Effect Policy]
  Read-only assertions on returned ``StructuralInferenceReport`` dataclasses.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mindie_profiler import (
    STRUCTURAL_INFERENCE_SCHEMA,
    classify_canonical_l1_family,
    infer_trace_structure,
)
from mindie_profiler.normalized import kernel_rows
def _repeat_op(
    name: str,
    op_type: str,
    core: str,
    count: int,
    dur_us: float,
) -> list[dict[str, object]]:
    return [
        {"name": name, "op_type": op_type, "core": core, "dur_us": dur_us}
        for _ in range(count)
    ]
def test_kimi_k3_dspark5_separates_93_target_layers_from_5_draft_layers() -> None:
    """Verify Kimi-K3 + DSpark5 trace infers 93 hybrid body layers (24 MLA + 69 KDA,
    1 Dense + 92 MoE) and separates the 5-layer DSpark speculative module instead
    of mis-mapping the whole trace to a standalone 5-layer draft model.
    """
    steps = 10
    events: list[dict[str, object]] = []
    # 24 full MLA layers + 69 linear KDA layers = 93 body layers per step
    events.extend(_repeat_op("FlashMla", "FlashMla", "AI_CORE", 24 * steps, 42.0))
    events.extend(_repeat_op("RecurrentKda", "RecurrentKda", "AI_VECTOR_CORE", 69 * steps, 28.0))
    # 92 MoE layers + 1 dense layer = 93 body layers per step
    events.extend(_repeat_op("MoeGatingTopK", "MoeGatingTopK", "AI_VECTOR_CORE", 92 * steps, 6.0))
    events.extend(_repeat_op("GroupedMatmul", "GroupedMatmul", "AI_CORE", 184 * steps, 35.0))
    events.extend(_repeat_op("DequantSwigluQuant", "DequantSwigluQuant", "AI_VECTOR_CORE", 92 * steps, 11.0))
    events.extend(_repeat_op("QuantBatchMatmulV3", "QuantBatchMatmulV3", "AI_CORE", 93 * 2 * steps, 18.0))
    events.extend(_repeat_op("AddRmsNormDynamicQuant", "AddRmsNormDynamicQuant", "AI_VECTOR_CORE", 93 * 2 * steps, 7.0))
    # 5-layer DSpark speculative draft stack + tree verification
    events.extend(_repeat_op("DSparkDraftAttention", "FusedInferAttentionScore", "AI_CORE", 5 * steps, 15.0))
    events.extend(_repeat_op("DSparkDraftMlpGemm", "QuantBatchMatmulV3", "AI_CORE", 5 * steps, 12.0))
    events.extend(_repeat_op("DSparkTreeVerifyTokens", "TreeVerify", "AI_VECTOR_CORE", 1 * steps, 22.0))
    # Framework step-envelope ops (1 per step)
    events.extend(_repeat_op("GatherV2_Embedding", "GatherV2", "AI_VECTOR_CORE", 1 * steps, 14.0))
    events.extend(_repeat_op("ArgMax_Sampler", "ArgMax", "AI_VECTOR_CORE", 1 * steps, 9.0))
    events.extend(_repeat_op("allreduceAicpuKernel", "allreduceAicpuKernel", "AI_CPU", 1 * steps, 19.0))
    report = infer_trace_structure(events, model_hint="r08_4n_kimi_k3_dspark5")
    assert report.schema_version == STRUCTURAL_INFERENCE_SCHEMA
    topo = report.body_topology
    assert topo.inferred_steps == steps
    assert topo.total_body_layers == 93
    assert topo.full_attention_layers == 24
    assert topo.linear_attention_layers == 69
    assert topo.moe_ffn_layers == 92
    assert topo.dense_ffn_layers == 1
    assert topo.is_hybrid_attention is True
    assert topo.is_hybrid_ffn is True
    spec = report.speculative_module
    assert spec.has_speculative_decoding is True
    assert spec.speculative_kind == "dspark"
    assert spec.inferred_draft_layers == 5
    assert abs(spec.draft_us_per_step - (5 * 15.0 + 5 * 12.0 + 22.0)) < 1e-6
    env = report.framework_envelope
    # D1: the once-per-step allreduce is collective traffic, not AICPU envelope.
    assert abs(env.envelope_us_per_step - (14.0 + 9.0)) < 1e-6
    assert env.aicpu_controller_us_per_step == 0
    assert "allreduceAicpuKernel" not in env.step_boundary_operators
    assert report.l1_family_us_per_step["collective"] == pytest.approx(19.0)
    assert report.l2_subgraph_us_per_step["comm_subgraph"] == pytest.approx(19.0)
def test_minimax_m3_fused_megamoe_and_qknorm_rope_cache_composites() -> None:
    """Verify MiniMax-M3 / M3.1-Flash fused kernels (MegaMoe across 57 MoE layers
    and _minimax_qknorm_rope_cache_kernel across 60 attention layers) bind to
    L2 composite subgraphs with explicit Agent decision metadata.
    """
    steps = 8
    events: list[dict[str, object]] = []
    # 60 Sparse-GQA attention layers per step
    events.extend(_repeat_op("SparseAttentionScore", "SparseAttentionScore", "AI_CORE", 60 * steps, 48.0))
    events.extend(
        _repeat_op(
            "_minimax_qknorm_rope_cache_kernel",
            "CustomTriton",
            "AI_VECTOR_CORE",
            60 * steps,
            14.0,
        )
    )
    events.extend(
        _repeat_op(
            "_decode_qk_score_kernel",
            "CustomTriton",
            "AI_CORE",
            60 * steps,
            16.0,
        )
    )
    events.extend(_repeat_op("QuantBatchMatmulV3", "QuantBatchMatmulV3", "AI_CORE", 120 * steps, 20.0))
    # 57 fused MegaMoe layers + 3 dense layers = 60 layers
    events.extend(_repeat_op("MegaMoe", "MegaMoe", "MIX_AIC_AIV", 57 * steps, 195.0))
    events.extend(_repeat_op("AddRmsNorm", "AddRmsNorm", "AI_VECTOR_CORE", 120 * steps, 6.5))
    report = infer_trace_structure(events, explicit_steps=steps)
    topo = report.body_topology
    assert topo.total_body_layers == 60
    assert topo.full_attention_layers == 60
    assert topo.sparse_indexer_layers == 60
    assert topo.moe_ffn_layers == 57
    assert topo.dense_ffn_layers == 3
    comp_by_name = {c.operator_name: c for c in report.fused_composites}
    assert "MegaMoe" in comp_by_name
    assert comp_by_name["MegaMoe"].enclosing_subgraph == "moe_subgraph"
    assert set(comp_by_name["MegaMoe"].constituent_families) == {
        "moe_router",
        "moe_grouped",
        "activation",
        "collective",
    }
    assert comp_by_name["MegaMoe"].replaces_unfused_families is True
    assert "_minimax_qknorm_rope_cache_kernel" in comp_by_name
    assert comp_by_name["_minimax_qknorm_rope_cache_kernel"].enclosing_subgraph == "attn_subgraph"
    assert set(comp_by_name["_minimax_qknorm_rope_cache_kernel"].constituent_families) == {
        "norm_residual",
        "rope",
        "kv_cache",
    }
    # Verify MegaMoe was NOT arbitrarily dumped into a single L1 family
    fam, subg, is_comp, fams = classify_canonical_l1_family("MegaMoe", "MegaMoe", "MIX")
    assert fam is None
    assert subg == "moe_subgraph"
    assert is_comp is True
    assert "moe_grouped" in fams
def test_unseen_vendor_fused_moe_kernel_inferred_by_structural_complementarity() -> None:
    """Verify that a completely unknown operator whose per-step call count matches
    L_moe (58) when standard GroupedMatmul is absent is structurally inferred as an
    L2 fused MoE composite and surfaced in agent_decision_items.
    """
    steps = 4
    events: list[dict[str, object]] = []
    # 61 attention layers + 58 MoE routers, but GroupedMatmul is replaced by an unseen kernel
    events.extend(_repeat_op("SparseFlashMla", "SparseFlashMla", "AI_CORE", 61 * steps, 50.0))
    events.extend(_repeat_op("MoeGatingTopK", "MoeGatingTopK", "AI_VECTOR_CORE", 58 * steps, 5.0))
    events.extend(
        _repeat_op(
            "FutureNextGenSuperFusedExpertBlockV9",
            "FutureNextGenSuperFusedExpertBlockV9",
            "MIX_AIC",
            58 * steps,
            210.0,
        )
    )
    events.extend(_repeat_op("RmsNorm", "RmsNorm", "AI_VECTOR_CORE", 122 * steps, 6.0))
    report = infer_trace_structure(events, explicit_steps=steps)
    assert report.body_topology.total_body_layers == 61
    assert report.body_topology.moe_ffn_layers == 58
    assert report.body_topology.dense_ffn_layers == 3
    decisions = {d.operator_name: d for d in report.agent_decision_items}
    assert "FutureNextGenSuperFusedExpertBlockV9" in decisions
    item = decisions["FutureNextGenSuperFusedExpertBlockV9"]
    assert item.inferred_role == "inferred_fused_moe_composite"
    assert item.inferred_subgraph == "moe_subgraph"
    assert "moe_grouped" in item.candidate_families
    assert item.multiplicity_match == "matches_L_moe(58)"
    assert report.l2_subgraph_us_per_step["moe_subgraph"] >= 58 * 210.0
def test_boundary_anchor_and_launch_suffix_infer_10_steps_of_32() -> None:
    """10 steps x 32 layers must not collapse to the first 20-120 factorization."""
    events = [
        {"name": f"FlashAttention_{i}", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": 1.0}
        for i in range(320)
    ]
    events += [
        {"name": f"ArgMax_{i}", "op_type": "ArgMax", "core": "AI_VECTOR_CORE", "dur_us": 1.0}
        for i in range(10)
    ]
    report = infer_trace_structure(events)
    topo = report.body_topology
    assert topo.inferred_steps == 10
    assert topo.total_body_layers == 32
    assert topo.full_attention_layers == 32
    assert topo.confidence == "high"
    attention = [op for op in report.operators if op.canonical_family == "attention"]
    assert [(op.name, op.call_count) for op in attention] == [("FlashAttention", 320)]
    assert "ArgMax" in report.framework_envelope.step_boundary_operators
def test_two_grouped_matmul_launches_do_not_inflate_moe_layers() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 64, 1.0)
    events += _repeat_op("GroupedMatmul", "GroupedMatmul", "AI_CORE", 116, 1.0)
    topo = infer_trace_structure(events, explicit_steps=1).body_topology
    assert topo.total_body_layers == 64
    assert topo.moe_ffn_layers == 58
    assert topo.dense_ffn_layers == 6
    assert topo.is_hybrid_ffn is True
def test_named_draft_kda_does_not_replace_the_target_linear_cohort() -> None:
    events = _repeat_op("FlashMla", "FlashMla", "AI_CORE", 24, 1.0)
    events += _repeat_op("RecurrentKda", "RecurrentKda", "AI_VECTOR_CORE", 69, 1.0)
    events += _repeat_op("MTP_RecurrentKda", "RecurrentKda", "AI_VECTOR_CORE", 5, 1.0)
    events += _repeat_op("MoeGatingTopK", "MoeGatingTopK", "AI_VECTOR_CORE", 92, 1.0)
    report = infer_trace_structure(events, explicit_steps=1)
    topo, spec = report.body_topology, report.speculative_module
    assert topo.total_body_layers == 93
    assert topo.full_attention_layers == 24
    assert topo.linear_attention_layers == 69
    assert topo.moe_ffn_layers == 92
    assert spec.has_speculative_decoding is True
    assert spec.inferred_draft_layers == 5
    assert "MTP_RecurrentKda" in spec.draft_operators
def test_ordinary_small_hybrid_cohort_is_not_speculative() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 4, 1.0)
    events += _repeat_op("RecurrentKda", "RecurrentKda", "AI_VECTOR_CORE", 28, 1.0)
    report = infer_trace_structure(events, explicit_steps=1)
    topo = report.body_topology
    assert topo.total_body_layers == 32
    assert topo.full_attention_layers == 4
    assert topo.linear_attention_layers == 28
    assert topo.is_hybrid_attention is True
    assert report.speculative_module.has_speculative_decoding is False
    assert report.speculative_module.inferred_draft_layers == 0
def test_second_unknown_is_not_moe_when_megamoe_already_covers_it() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0)
    events += _repeat_op("MegaMoe", "MegaMoe", "MIX_AIC", 32, 10.0)
    events += _repeat_op("OpaqueKernel", "OpaqueKernel", "AI_CORE", 32, 3.0)
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.body_topology.total_body_layers == 32
    assert report.body_topology.moe_ffn_layers == 32
    roles = {item.operator_name: item.inferred_role for item in report.agent_decision_items}
    assert roles["OpaqueKernel"] != "inferred_fused_moe_composite"
    assert "MegaMoe" in {comp.operator_name for comp in report.fused_composites}
def test_per_layer_aicpu_collective_stays_in_the_body() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0)
    events += _repeat_op("allreduceAicpuKernel", "allreduceAicpuKernel", "AI_CPU", 32, 1.0)
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.body_topology.total_body_layers == 32
    assert "allreduceAicpuKernel" not in report.framework_envelope.step_boundary_operators
    assert report.framework_envelope.envelope_us_per_step == 0
    assert report.l1_family_us_per_step["collective"] == pytest.approx(32)

def test_known_multifamily_composites_do_not_fill_a_single_l1_bucket() -> None:
    for name in (
        "AddRmsNormDynamicQuant", "GroupedMatmulSwigluQuant", "MlaProlog",
        "KvRmsNormRopeCache", "DequantSwigluQuant",
    ):
        family, _subgraph, composite, families = classify_canonical_l1_family(name, name, "AI_VECTOR_CORE")
        assert family is None and composite is True and len(families) >= 2
    family, subgraph, composite, families = classify_canonical_l1_family("MlaPrologV3", "MlaPrologV3", "AI_CORE")
    assert family is None and composite is True
    assert {"gemm", "norm_residual", "rope", "kv_cache"} <= set(families)
    events = _repeat_op("AddRmsNormDynamicQuant", "AddRmsNormDynamicQuant", "AI_VECTOR_CORE", 64, 10.0)
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.l1_family_us_per_step["norm_residual"] == 0
    assert report.l1_family_us_per_step["elementwise_quant"] == 0
    assert report.l2_subgraph_us_per_step["norm_quant_subgraph"] == pytest.approx(640)
    assert report.fused_composites[0].operator_name == "AddRmsNormDynamicQuant"


def test_unseen_quant_matmul_allreduce_norm_is_not_only_collective() -> None:
    family, subgraph, composite, families = classify_canonical_l1_family(
        "aclnnQuantMatmulAllReduceAddRmsNorm", "aclnnQuantMatmulAllReduceAddRmsNorm", "AI_CORE",
    )
    assert family is None and composite is True and subgraph == "multi_family_composite"
    assert {"gemm", "collective", "norm_residual"} <= set(families)
    events = _repeat_op(
        "aclnnQuantMatmulAllReduceAddRmsNorm", "aclnnQuantMatmulAllReduceAddRmsNorm", "AI_CORE", 32, 1.0,
    )
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.l1_family_us_per_step["collective"] == 0
    assert report.l1_family_us_per_step["gemm"] == 0
    assert report.l2_subgraph_us_per_step["multi_family_composite"] == pytest.approx(32)
    assert {"gemm", "collective", "norm_residual"} <= set(report.fused_composites[0].constituent_families)


def test_native_dspark_fixture_keeps_40_target_layers() -> None:
    rows = list(kernel_rows(Path(__file__).parent / "fixtures/decode_forward/a3_v41_dspark7_two_forwards.csv"))
    report = infer_trace_structure(rows, explicit_steps=2, model_hint="dspark7")
    topo = report.body_topology
    assert topo.inferred_steps == 2
    assert topo.total_body_layers == 40
    assert topo.full_attention_layers == 40
    assert topo.moe_ffn_layers == 40
    assert topo.confidence == "high"
    spec = report.speculative_module
    assert spec.has_speculative_decoding is True
    assert spec.speculative_kind == "dspark"
    assert spec.inferred_draft_layers == 3
    envelope = report.framework_envelope.step_boundary_operators
    assert "allgatherAicpuKernel" not in envelope
    assert "reduce_scatterAicpuKernel" not in envelope


def test_hcom_launch_suffixes_stay_one_collective_cohort() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0)
    events += [
        {"name": f"hcom_allReduce__{i}_0_1", "op_type": "hcom_allReduce_", "core": "COMMUNICATION", "dur_us": 2.0}
        for i in range(32)
    ]
    report = infer_trace_structure(events, explicit_steps=1)
    collectives = [op for op in report.operators if op.canonical_family == "collective"]
    assert [(op.name, op.call_count, op.structural_scope) for op in collectives] == [
        ("hcom_allReduce", 32, "target_body"),
    ]


def test_same_name_different_types_do_not_collapse_to_the_first_family() -> None:
    events = _repeat_op("same", "FlashAttention", "AI_CORE", 32, 1.0)
    events += _repeat_op("same", "RecurrentKda", "AI_VECTOR_CORE", 32, 1.0)
    topo = infer_trace_structure(events, explicit_steps=1).body_topology
    assert topo.full_attention_layers == 32
    assert topo.linear_attention_layers == 32
    assert topo.total_body_layers == 64


def test_blocked_attention_implementations_add_when_they_do_not_interleave() -> None:
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 16, 1.0)
    events += _repeat_op("PagedAttention", "PagedAttention", "AI_CORE", 16, 1.0)
    assert infer_trace_structure(events, explicit_steps=1).body_topology.full_attention_layers == 32


def test_ambiguous_step_factorization_is_not_high_confidence() -> None:
    topo = infer_trace_structure(_repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 480, 1.0)).body_topology
    assert topo.confidence == "low"
    assert topo.inferred_steps == 0
    assert topo.total_body_layers == 0


def test_empty_hint_and_invalid_steps_do_not_invent_topology() -> None:
    empty = infer_trace_structure([], hint_layers=64).body_topology
    assert empty.confidence == "low" and empty.total_body_layers == 0 and empty.inferred_steps == 0
    invalid = infer_trace_structure(
        _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0), explicit_steps=0,
    ).body_topology
    assert invalid.confidence == "low" and invalid.inferred_steps == 0 and invalid.total_body_layers == 0


def test_timestamp_duration_is_translation_invariant() -> None:
    base = 1793479803855734000
    shifted = [{"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "start_ns": base, "end_ns": base + 1000}]
    origin = [{"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "start_ns": 0, "end_ns": 1000}]
    assert infer_trace_structure(shifted, explicit_steps=1).total_duration_us == pytest.approx(1.0)
    assert infer_trace_structure(origin, explicit_steps=1).total_duration_us == pytest.approx(1.0)


def test_invalid_and_missing_durations_stay_unmeasured() -> None:
    invalid = infer_trace_structure([
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": float("nan")},
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": -5},
    ], explicit_steps=1)
    assert invalid.total_duration_us == 0
    assert "invalid_duration" in invalid.duration_basis
    missing = infer_trace_structure(
        [{"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE"}], explicit_steps=1,
    )
    assert missing.total_duration_us == 0
    assert "no_finite_duration" in missing.duration_basis
    assert "missing_duration" in missing.duration_basis


def test_family_maps_reject_mutation() -> None:
    report = infer_trace_structure(_repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 8, 1.0), explicit_steps=1)
    with pytest.raises(TypeError):
        report.l1_family_us_per_step["attention"] = -1
    with pytest.raises(TypeError):
        report.l2_subgraph_us_per_step["attn_subgraph"] = -1


def test_overlapping_kernels_expose_span_separately_from_activity_sum() -> None:
    events = [
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": 100, "start_ns": 0, "end_ns": 100_000},
        {"name": "MatMulV2", "op_type": "MatMulV2", "core": "AI_CORE", "dur_us": 100, "start_ns": 0, "end_ns": 100_000},
    ]
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.step_duration_us == pytest.approx(200)
    assert report.activity_sum_us_per_step == pytest.approx(200)
    assert report.observed_span_us_per_step == pytest.approx(100)
    assert report.busy_union_us_per_step == pytest.approx(100)
    assert "activity_sum" in report.duration_basis


def test_aicpu_collectives_stay_out_of_the_framework_envelope() -> None:
    """D1: communication kernels are collective even at one call per step on AICPU."""
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0)
    names = (
        "allgatherAicpuKernel", "reduce_scatterAicpuKernel", "allreduceAicpuKernel",
        "HcclLaunchAicpuKernel", "hcom_allReduce", "alltoall",
    )
    for name in names:
        events.extend(_repeat_op(name, name, "AI_CPU", 1, 4.0))
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.framework_envelope.envelope_us_per_step == 0
    assert report.framework_envelope.aicpu_controller_us_per_step == 0
    collectives = {op.name for op in report.operators if op.canonical_family == "collective"}
    assert set(names) <= collectives
    assert all(op.structural_scope == "target_body" for op in report.operators if op.name in names)
    comm = [op for op in report.operators if op.name in names and op.name != "alltoall"]
    assert {op.enclosing_subgraph for op in comm} == {"comm_subgraph"}


def test_auto_mode_keeps_27_layers_across_98_steps() -> None:
    """D2: 2646 = 27 x 98 must not invert into 27 steps of 98 layers."""
    topo = infer_trace_structure(
        _repeat_op("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE", 2646, 1.0),
    ).body_topology
    assert topo.inferred_steps == 98
    assert topo.total_body_layers == 27
    assert topo.full_attention_layers == 27
    poisoned = _repeat_op("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE", 2646, 1.0)
    poisoned += _repeat_op("_compute_local_logits_stats_kernel", "Logits", "AI_VECTOR_CORE", 1, 1.0)
    kept = infer_trace_structure(poisoned).body_topology
    assert kept.inferred_steps == 98 and kept.total_body_layers == 27
    coprime = _repeat_op("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE", 2646, 1.0)
    coprime += _repeat_op("ArgMax", "ArgMax", "AI_VECTOR_CORE", 2, 1.0)
    coprime += _repeat_op("GatherV2", "GatherV2", "AI_VECTOR_CORE", 3, 1.0)
    assert infer_trace_structure(coprime).body_topology.inferred_steps == 98
    events = []
    for step in range(4):
        base = step * 1_000_000
        for layer in range(32):
            start = base + layer * 1_000
            events.append({
                "name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE",
                "dur_us": 1.0, "start_ns": start, "end_ns": start + 500,
            })
    gapped = infer_trace_structure(events).body_topology
    assert gapped.inferred_steps == 4
    assert gapped.total_body_layers == 32


def test_kimi_hybrid_anchors_ignore_prolog_metadata_and_state_copy() -> None:
    """D3: primary anchors, not MlaProlog / metadata / state-copy, yield 24+69 and 92+1."""
    steps = 17

    def shaped(name: str, op_type: str, core: str, count: int, shape: list[list[int]]) -> list[dict[str, object]]:
        return [
            {"name": name, "op_type": op_type, "core": core, "dur_us": 1.0, "input_shapes": shape}
            for _ in range(count)
        ]

    events: list[dict[str, object]] = []
    events.extend(shaped("FlashMla", "FlashMla", "AI_CORE", 384, [[8, 12, 576], [1]]))
    events.extend(shaped("FlashMla", "FlashMla", "AI_CORE", 85, [[7, 8, 576], [1]]))
    events.extend(shaped("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE", 24, [[1277, 12, 192], [1]]))
    events.extend(_repeat_op("MlaPrologV3", "MlaPrologV3", "AI_CORE", 479, 1.0))
    events.extend(_repeat_op("FlashMlaMetadata", "FlashMlaMetadata", "AI_CPU", 66, 1.0))
    events.extend(_repeat_op("CausalConv1d", "CausalConv1d", "AI_VECTOR_CORE", 1173, 1.0))
    events.extend(_repeat_op("RecurrentKda", "RecurrentKda", "AI_VECTOR_CORE", 1104, 1.0))
    events.extend(_repeat_op("_kda_state_copy_kernel", "_kda_state_copy_kernel", "AI_VECTOR_CORE", 138, 1.0))
    events.extend(_repeat_op("MoeGatingTopK", "MoeGatingTopK", "AI_VECTOR_CORE", 1564, 1.0))
    events.extend(_repeat_op("MoeInitRoutingV2", "MoeInitRoutingV2", "AI_VECTOR_CORE", 92, 1.0))
    events.extend(_repeat_op("MoeInitRoutingV3", "MoeInitRoutingV3", "AI_VECTOR_CORE", 92, 1.0))
    topo = infer_trace_structure(events, explicit_steps=steps, model_hint="kimik3_dspark_block5").body_topology
    assert topo.full_attention_layers == 24
    assert topo.linear_attention_layers == 69
    assert topo.moe_ffn_layers == 92
    assert topo.dense_ffn_layers == 1
    assert topo.total_body_layers == 93


def test_minimax_and_target_kernels_are_not_speculative_by_multiplicity() -> None:
    """D4: draft-glue names and ordinary target kernels do not invent a draft stack."""
    minimax = _repeat_op("SparseAttentionScore", "SparseAttentionScore", "AI_CORE", 60, 1.0)
    minimax += _repeat_op(
        "_combine_sampled_and_draft_tokens_kernel", "_combine_sampled_and_draft_tokens_kernel", "AI_VECTOR_CORE", 64, 0.1,
    )
    minimax += _repeat_op("MoeInitRoutingV2", "MoeInitRoutingV2", "AI_VECTOR_CORE", 57, 1.0)
    plain = infer_trace_structure(minimax, explicit_steps=1, model_hint="minimax_m3")
    assert plain.speculative_module.has_speculative_decoding is False
    hinted = _repeat_op("FlashMla", "FlashMla", "AI_CORE", 24 * 17, 1.0)
    hinted += _repeat_op("MoeInitRoutingV2", "MoeInitRoutingV2", "AI_VECTOR_CORE", 92, 1.0)
    hinted += _repeat_op("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE", 24, 1.0)
    hinted += _repeat_op("FlashMlaMetadata", "FlashMlaMetadata", "AI_CPU", 66, 1.0)
    spec = infer_trace_structure(hinted, explicit_steps=17, model_hint="kimik3_dspark_block5").speculative_module
    assert spec.has_speculative_decoding is False
    assert spec.speculative_kind is None
    assert spec.draft_operators == ()
    for name in ("MoeInitRoutingV2", "FusedInferAttentionScore", "FlashMlaMetadata"):
        assert name not in spec.draft_operators


def test_hcpre_and_hcpost_count_toward_hyperconnection_layers() -> None:
    """D5: HcPre/HcPost are hyperconnection, including two launches per layer."""
    family, subgraph, composite, families = classify_canonical_l1_family("HcPre", "HcPre", "AI_VECTOR_CORE")
    assert family == "hyperconnection" and subgraph == "norm_quant_subgraph" and composite is False
    assert classify_canonical_l1_family("HcPost", "HcPost", "")[0] == "hyperconnection"
    steps = 2
    events = _repeat_op("SparseFlashMla", "SparseFlashMla", "AI_CORE", 4 * steps, 5.0)
    events += _repeat_op("HcPre", "HcPre", "AI_VECTOR_CORE", 2 * 4 * steps, 3.0)
    events += _repeat_op("HcPost", "HcPost", "AI_VECTOR_CORE", 2 * 4 * steps, 1.0)
    topo = infer_trace_structure(events, explicit_steps=steps).body_topology
    assert topo.full_attention_layers == 4
    assert topo.hyperconnection_layers == 4
    assert topo.topology_signature.endswith("hc=4)")
    # 40 target + 3 draft attention. Draft-scoped HcPre/HcPost do not raise target hc above L_body.
    span_steps = 2
    span = [
        {"name": "SparseFlashMla", "op_type": "SparseFlashMla", "core": "AI_CORE", "dur_us": 1.0, "input_shapes": [[8, 12, 576]]}
        for _ in range(40 * span_steps)
    ]
    span += [
        {"name": "SparseFlashMla", "op_type": "SparseFlashMla", "core": "AI_CORE", "dur_us": 1.0, "input_shapes": [[7, 8, 576]]}
        for _ in range(3 * span_steps)
    ]
    span += _repeat_op("HcPre", "HcPre", "AI_VECTOR_CORE", 2 * 43 * span_steps, 1.0)
    span += _repeat_op("HcPost", "HcPost", "AI_VECTOR_CORE", 2 * 43 * span_steps, 1.0)
    drafted = infer_trace_structure(span, explicit_steps=span_steps, model_hint="dsv41flash_dspark5").body_topology
    assert drafted.full_attention_layers == 40
    assert drafted.total_body_layers == 40
    assert drafted.hyperconnection_layers == 40
    assert drafted.hyperconnection_layers <= drafted.total_body_layers


def test_adds_add_is_elementwise_not_an_indexer() -> None:
    """D6: folding Adds_Add must not fire the ``dsa`` indexer token."""
    family, subgraph, composite, _families = classify_canonical_l1_family(
        "aclnnAdds_AddAiCore_Add", "Add", "AI_VECTOR_CORE",
    )
    assert family == "elementwise_quant"
    assert subgraph == "norm_quant_subgraph"
    assert composite is False
    assert classify_canonical_l1_family("aclnnDsaBlockSparse", "DSA", "AI_CORE")[0] == "indexer"
    events = _repeat_op("aclnnAdds_AddAiCore_Add", "Add", "AI_VECTOR_CORE", 32, 1.0)
    events += _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 1.0)
    topo = infer_trace_structure(events, explicit_steps=1).body_topology
    assert topo.sparse_indexer_layers == 0
    assert topo.full_attention_layers == 32


def test_glue_ops_are_not_inferred_fused_composites() -> None:
    """D7: indexing, glue, and activation ops are not fabricated fused modules."""
    events = _repeat_op("FlashAttention", "FlashAttention", "AI_CORE", 32, 2.0)
    events += _repeat_op("MoeGatingTopK", "MoeGatingTopK", "AI_VECTOR_CORE", 32, 1.0)
    glue = (
        ("aclnnArgMax_ArgMaxV2", "ArgMax"),
        ("aclnnEmbedding_GatherV2", "GatherV2"),
        ("aclnnIndex", "Index"),
        ("aclnnScatterNdUpdateSk", "ScatterNdUpdate"),
        ("aclnnTanh", "Tanh"),
        ("aclnnDivs_RealDiv", "RealDiv"),
        ("aclnnCat_ConcatD", "ConcatD"),
        ("aclnnLtTensor_Less", "Less"),
        ("aclnnSlice", "Slice"),
        ("aclnnCast", "Cast"),
    )
    for name, op_type in glue:
        events.extend(_repeat_op(name, op_type, "AI_VECTOR_CORE", 32, 1.0))
    report = infer_trace_structure(events, explicit_steps=1)
    banned = {"inferred_fused_attention_prep_composite", "inferred_fused_moe_composite"}
    roles = {item.operator_name: item.inferred_role for item in report.agent_decision_items}
    for name, _op_type in glue:
        assert roles.get(name) not in banned
    assert all(comp.detection_basis != "structural_multiplicity_and_missing_moe_complement" for comp in report.fused_composites)


def _calls(name: str, count: int, duration: float = 1.0, core: str = "AI_CORE") -> list[dict[str, object]]:
    return [{"name": name, "op_type": name, "core": core, "dur_us": duration} for _ in range(count)]


def test_as_dict_json_roundtrip_on_empty_and_nonempty_reports() -> None:
    empty = infer_trace_structure([]).as_dict()
    json.dumps(empty)
    assert isinstance(empty["l1_family_us_per_step"], dict)
    report = infer_trace_structure(_calls("FlashAttention", 32), explicit_steps=1)
    payload = json.loads(json.dumps(report.as_dict()))
    assert payload["body_topology"]["total_body_layers"] == 32
    assert payload["l1_family_us_per_step"]["attention"] == pytest.approx(32)
    with pytest.raises(TypeError):
        report.l1_family_us_per_step["attention"] = -1


def test_hint_layers_use_combined_attention_not_router_divisibility() -> None:
    minimax = _calls("SparseAttentionScore", 5700) + _calls("MoeGatingTopK", 5415) + _calls("MegaMoe", 5415)
    hinted = infer_trace_structure(minimax, hint_layers=60)
    assert hinted.body_topology.inferred_steps == 95
    assert hinted.body_topology.total_body_layers == 60
    assert hinted.body_topology.moe_ffn_layers == 57
    assert hinted.body_topology.dense_ffn_layers == 3
    explicit = infer_trace_structure(minimax, explicit_steps=95).body_topology
    assert explicit.topology_signature.startswith("L60(attn=60,lin=0,idx=0;dense=3,moe=57")
    hybrid = infer_trace_structure(_calls("FlashMla", 2280) + _calls("RecurrentKda", 6555, core="AI_VECTOR_CORE"), hint_layers=93)
    assert hybrid.body_topology.inferred_steps == 95
    assert hybrid.body_topology.total_body_layers == 93
    assert hybrid.body_topology.full_attention_layers == 24
    assert hybrid.body_topology.linear_attention_layers == 69
    small = infer_trace_structure(_calls("FlashMla", 60) + _calls("RecurrentKda", 120, core="AI_VECTOR_CORE"), hint_layers=30)
    assert small.body_topology.inferred_steps == 6
    assert small.body_topology.total_body_layers == 30
    assert small.body_topology.full_attention_layers == 10
    assert small.body_topology.linear_attention_layers == 20


def test_field_separator_does_not_invent_ssm_and_prep_stays_attention() -> None:
    family, subgraph, composite, families = classify_canonical_l1_family("MlaPreprocess", "MlaPreprocess", "AI_CORE")
    assert (family, subgraph, composite, families) == ("attention", "attn_subgraph", False, ("attention",))
    assert classify_canonical_l1_family("Compressor", "Compressor", "AI_VECTOR_CORE")[0] == "attention"
    _fam, sub, comp, fams = classify_canonical_l1_family("VendorFlashAttentionRopeCache", "VendorFlashAttentionRopeCache", "AI_CORE")
    assert comp is True and sub == "attn_subgraph" and "attention" in fams
    events = _calls("SparseFlashAttention", 399) + _calls("MlaPreprocess", 399)
    topo = infer_trace_structure(events, explicit_steps=133).body_topology
    assert topo.full_attention_layers == 3
    assert topo.linear_attention_layers == 0
    assert topo.total_body_layers == 3


def test_unresolved_steps_keep_per_step_fields_at_zero() -> None:
    events = _calls("FlashAttention", 480) + _calls("OpaqueKernel", 1, duration=100.0)
    report = infer_trace_structure(events)
    assert report.total_duration_us == pytest.approx(580)
    assert report.step_duration_us == 0
    assert report.activity_sum_us_per_step == 0
    assert report.target_body_us_per_step == 0
    assert report.speculative_module.draft_us_per_step == 0
    assert report.framework_envelope.envelope_us_per_step == 0
    assert sum(report.l1_family_us_per_step.values()) == 0
    assert sum(report.l2_subgraph_us_per_step.values()) == 0
    assert report.l2_subgraph_us_per_step["unresolved_body"] == 0
    assert sum(report.l2_subgraph_us_per_step.values()) == report.step_duration_us
    assert all(op.calls_per_step == 0 and op.us_per_step == 0 for op in report.operators)
    assert sum(op.total_us for op in report.operators) == pytest.approx(580)
    assert sum(op.call_count for op in report.operators) == 481


def test_disjoint_attention_sums_and_qkv_is_not_dense_ffn() -> None:
    paired = _calls("FlashAttention", 16) + _calls("PagedAttention", 16)
    assert infer_trace_structure(paired, explicit_steps=1).body_topology.full_attention_layers == 32
    uneven = _calls("FlashAttention", 8) + _calls("PagedAttention", 24)
    assert infer_trace_structure(uneven, explicit_steps=1).body_topology.full_attention_layers == 32
    score = _calls("FlashAttentionScore", 16) + _calls("PagedAttention", 16)
    assert infer_trace_structure(score, explicit_steps=1).body_topology.full_attention_layers == 32
    repeated: list[dict[str, object]] = []
    for _step in range(10):
        repeated.extend(_calls("FlashAttention", 16))
        repeated.extend(_calls("PagedAttention", 16))
    assert infer_trace_structure(repeated, explicit_steps=10).body_topology.full_attention_layers == 32
    qkv = _calls("FlashAttention", 32) + _calls("QkvProjectionMatMul", 32)
    topo = infer_trace_structure(qkv, explicit_steps=1).body_topology
    assert topo.full_attention_layers == 32
    assert topo.dense_ffn_layers == 0
    gemm = next(op for op in infer_trace_structure(qkv, explicit_steps=1).operators if op.name == "QkvProjectionMatMul")
    assert gemm.canonical_family == "gemm"
    assert gemm.enclosing_subgraph != "dense_ffn_subgraph"


def test_verify_stays_on_target_and_hint_alone_is_not_execution() -> None:
    events = _calls("FlashAttention", 32)
    events += _calls("METHOD_VerifyMegaMoe", 32, duration=10.0)
    events += _calls("METHOD_DraftFlashAttention", 5)
    report = infer_trace_structure(events, explicit_steps=1, model_hint="dspark")
    assert report.body_topology.total_body_layers == 32
    assert report.body_topology.moe_ffn_layers == 32
    assert report.speculative_module.inferred_draft_layers == 5
    assert "METHOD_VerifyMegaMoe" not in report.speculative_module.draft_operators
    assert "METHOD_DraftFlashAttention" in report.speculative_module.draft_operators
    hinted = infer_trace_structure(_calls("FlashAttention", 32), model_hint="dspark", explicit_steps=1)
    assert hinted.speculative_module.has_speculative_decoding is False
    assert hinted.speculative_module.draft_operators == ()


def test_competing_unknowns_and_vector_glue_are_not_moe_composites() -> None:
    events = _calls("FlashAttention", 32, duration=100.0)
    events += _calls("MoeGatingTopK", 32, duration=10.0, core="AI_VECTOR_CORE")
    events += _calls("OpaqueA", 32, duration=10.0)
    events += _calls("OpaqueB", 32, duration=5.0)
    report = infer_trace_structure(events, explicit_steps=1)
    roles = {item.operator_name: item for item in report.agent_decision_items}
    assert roles["OpaqueA"].inferred_role == "layer_body_unknown_op"
    assert roles["OpaqueB"].inferred_role == "layer_body_unknown_op"
    assert roles["OpaqueA"].multiplicity_match == "competing_unknown_candidates"
    assert roles["OpaqueB"].multiplicity_match == "competing_unknown_candidates"
    assert "OpaqueA" not in {comp.operator_name for comp in report.fused_composites}
    swapped = _calls("FlashAttention", 32, duration=100.0) + _calls("MoeGatingTopK", 32, duration=10.0, core="AI_VECTOR_CORE")
    swapped += _calls("OpaqueA", 32, duration=5.0) + _calls("OpaqueB", 32, duration=10.0)
    swapped_roles = {item.operator_name: item.inferred_role for item in infer_trace_structure(swapped, explicit_steps=1).agent_decision_items}
    assert swapped_roles["OpaqueA"] == swapped_roles["OpaqueB"] == "layer_body_unknown_op"
    logical = _calls("FlashAttention", 32, duration=100.0) + _calls("MoeGatingTopK", 32, duration=10.0, core="AI_VECTOR_CORE")
    logical += _calls("LogicalNot", 32, duration=1.0, core="AI_VECTOR_CORE")
    logical_report = infer_trace_structure(logical, explicit_steps=1)
    assert all(item.inferred_role != "inferred_fused_moe_composite" for item in logical_report.agent_decision_items)
    assert all(comp.operator_name != "LogicalNot" for comp in logical_report.fused_composites)


def test_lmhead_is_gemm_and_unknown_aicpu_stays_unresolved() -> None:
    events = _calls("FlashAttention", 32)
    events += _calls("LmHeadMatMul", 1, duration=100.0)
    events += _calls("LogitsMatMul", 1, duration=40.0)
    events += [{"name": "OpaqueCompute", "op_type": "OpaqueCompute", "core": "AI_CPU", "dur_us": 100.0}]
    report = infer_trace_structure(events, explicit_steps=1)
    by_name = {op.name: op for op in report.operators}
    assert by_name["LmHeadMatMul"].canonical_family == "gemm"
    assert by_name["LmHeadMatMul"].enclosing_subgraph == "dense_ffn_subgraph"
    assert by_name["LogitsMatMul"].canonical_family == "gemm"
    assert by_name["LogitsMatMul"].enclosing_subgraph == "dense_ffn_subgraph"
    assert by_name["LmHeadMatMul"].structural_scope != "framework_envelope"
    assert by_name["OpaqueCompute"].structural_scope != "framework_envelope"
    assert report.l1_family_us_per_step["gemm"] == pytest.approx(140)
    assert "OpaqueCompute" not in report.framework_envelope.step_boundary_operators
    assert report.framework_envelope.aicpu_controller_us_per_step == 0


def test_rank_device_scope_and_timestamp_order_are_stable() -> None:
    def native(rank: str, device: str, count: int, start: int = 0) -> list[object]:
        rows = []
        for index in range(count):
            stamp = start + index * 1000
            rows.append(type("E", (), {
                "name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": 1.0,
                "rank_id": rank, "device_id": device, "start_ns": stamp, "end_ns": stamp + 500,
            })())
        return rows
    dual = native("0", "0", 32) + native("1", "1", 32)
    assert infer_trace_structure(dual, explicit_steps=1).body_topology.full_attention_layers == 32
    flash = [
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": 1.0, "start_ns": i * 1000, "end_ns": i * 1000 + 100}
        for i in range(16)
    ]
    paged = [
        {"name": "PagedAttention", "op_type": "PagedAttention", "core": "AI_CORE", "dur_us": 1.0, "start_ns": 100_000 + i * 1000, "end_ns": 100_000 + i * 1000 + 100}
        for i in range(16)
    ]
    interleaved: list[dict[str, object]] = []
    for left, right in zip(flash, paged):
        interleaved.extend((left, right))
    grouped = flash + paged
    left_layers = infer_trace_structure(interleaved, explicit_steps=1).body_topology.full_attention_layers
    right_layers = infer_trace_structure(grouped, explicit_steps=1).body_topology.full_attention_layers
    assert left_layers == right_layers == 32


def test_invalid_intervals_do_not_make_span_or_union_negative() -> None:
    events = [
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "dur_us": 1.0, "start_ns": 0, "end_ns": 1000},
        {"name": "FlashAttention", "op_type": "FlashAttention", "core": "AI_CORE", "start_ns": 10000, "end_ns": 0},
    ]
    report = infer_trace_structure(events, explicit_steps=1)
    assert report.observed_span_us_per_step is not None and report.observed_span_us_per_step >= 0
    assert report.busy_union_us_per_step is not None and report.busy_union_us_per_step >= 0
    assert report.observed_span_us_per_step == pytest.approx(1.0)
    assert "invalid_duration" in report.duration_basis


def test_round3_linear_layers_hints_and_unknown_roles() -> None:
    one = infer_trace_structure(
        _calls("FlashMla", 1) + _calls("CausalConv1d", 3, core="AI_VECTOR_CORE") + _calls("RecurrentKda", 3, core="AI_VECTOR_CORE"),
        explicit_steps=1,
    ).body_topology
    assert (one.full_attention_layers, one.linear_attention_layers, one.total_body_layers) == (1, 3, 4)
    wide = _calls("FusedInferAttentionScore", 242) + _calls("CausalConv1d", 726, core="AI_VECTOR_CORE")
    wide += _calls("RecurrentKda", 726, core="AI_VECTOR_CORE") + _calls("MoeGatingTopK", 726, core="AI_VECTOR_CORE")
    wide += _calls("ArgMax", 242, core="AI_VECTOR_CORE")
    hinted = infer_trace_structure(wide, hint_layers=4).body_topology
    assert (hinted.inferred_steps, hinted.full_attention_layers, hinted.linear_attention_layers, hinted.total_body_layers) == (242, 1, 3, 4)
    indexed = _calls("SparseAttentionScore", 5700) + _calls("MoeGatingTopK", 5415, core="AI_VECTOR_CORE")
    indexed += _calls("MegaMoe", 5415) + _calls("_decode_qk_score_kernel", 5640)
    mini = infer_trace_structure(indexed, hint_layers=60).body_topology
    assert (mini.inferred_steps, mini.total_body_layers, mini.moe_ffn_layers, mini.dense_ffn_layers) == (95, 60, 57, 3)
    odd = infer_trace_structure(_calls("FlashMla", 65) + _calls("RecurrentKda", 115, core="AI_VECTOR_CORE"), hint_layers=30).body_topology
    assert (odd.inferred_steps, odd.total_body_layers, odd.full_attention_layers, odd.linear_attention_layers) == (6, 30, 11, 19)
    assert infer_trace_structure(_calls("MlaPreprocess", 32)).body_topology.total_body_layers == 0
    assert infer_trace_structure(_calls("Compressor", 32), explicit_steps=1).body_topology.full_attention_layers == 0
    assert "gdn_kda" in classify_canonical_l1_family("VendorRecurrentKdaRopeCache", "VendorRecurrentKdaRopeCache", "AI_CORE")[3]
    assert "attention" in classify_canonical_l1_family("VendorFlashMlaRopeCache", "VendorFlashMlaRopeCache", "AI_CORE")[3]
    opaque = _calls("FlashAttention", 32, duration=100) + _calls("MoeGatingTopK", 32, duration=10, core="AI_VECTOR_CORE")
    opaque += _calls("OpaqueCompute", 32, duration=10)
    opaque_roles = {item.operator_name: item.inferred_role for item in infer_trace_structure(opaque, explicit_steps=1).agent_decision_items}
    assert opaque_roles["OpaqueCompute"] == "layer_body_unknown_op"
    logical = _calls("FlashAttention", 32, duration=100) + _calls("MoeGatingTopK", 32, duration=10, core="AI_VECTOR_CORE")
    logical += _calls("LogicalNot", 32, duration=10)
    logical_roles = {item.operator_name: item.inferred_role for item in infer_trace_structure(logical, explicit_steps=1).agent_decision_items}
    assert logical_roles["LogicalNot"] == "layer_body_unknown_op"
    cpu = _calls("FlashAttention", 32) + _calls("OpaqueCacheCompute", 1, duration=100, core="AI_CPU")
    cpu += _calls("OpaqueEventCompute", 1, duration=100, core="AI_CPU")
    cpu_report = infer_trace_structure(cpu, explicit_steps=1)
    assert cpu_report.framework_envelope.envelope_us_per_step == 0
    cpu_roles = {item.operator_name: item.inferred_role for item in cpu_report.agent_decision_items}
    assert cpu_roles["OpaqueCacheCompute"] == cpu_roles["OpaqueEventCompute"] == "layer_body_unknown_op"
    a5 = [{"name": "FlashMla", "op_type": "FlashMla", "core": "AI_CORE", "dur_us": 1.0, "input_shapes": [[8, 12, 576]]} for _ in range(384)]
    a5 += [{"name": "FlashMla", "op_type": "FlashMla", "core": "AI_CORE", "dur_us": 1.0, "input_shapes": [[7, 8, 576]]} for _ in range(85)]
    a5 += [{"name": "FusedInferAttentionScore", "op_type": "FusedInferAttentionScore", "core": "AI_CORE", "dur_us": 1.0, "input_shapes": [[1277, 12, 192]]} for _ in range(24)]
    a5 += _calls("CausalConv1d", 1173, core="AI_VECTOR_CORE") + _calls("RecurrentKda", 1104, core="AI_VECTOR_CORE")
    a5 += _calls("MoeGatingTopK", 1564, core="AI_VECTOR_CORE")
    a5_topo = infer_trace_structure(a5, hint_layers=93).body_topology
    assert (a5_topo.inferred_steps, a5_topo.total_body_layers, a5_topo.full_attention_layers, a5_topo.linear_attention_layers) == (17, 93, 24, 69)
    assert a5_topo.moe_ffn_layers == 92 and a5_topo.dense_ffn_layers == 1
