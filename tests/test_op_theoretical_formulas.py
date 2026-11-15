"""Core formula-engine contracts: card honesty, rates, floors and composition.

[Role]
  Prove the single-source-of-truth expression contract (F01), the raw Vector
  operation rate (F02), conservative pipe composition (F09), precision tiers and
  quantization scales (F08), and the Vector-family operation/transaction counts
  (F14).

[Invariants]
  * Every catalog card re-parses every rendered expression to its own number.
  * Vector-only operators have exactly zero Cube MACs and tiled Cube FLOPs.
  * ``0 < tau_hw <= t_floor <= t_ref`` for every operator and launch mode.
  * A one-component composite has the exact same floor as its child.

[Timeouts & Locks]
  Pure in-memory arithmetic; bounded to a few thousand evaluations.

[Side-Effect Policy]
  No writes outside pytest's ``tmp_path``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mindie_sim.op_formulas import (
    A2, A3, A5, FormulaError, FormulaValidationError, LAUNCH_MODES,
    canonical_name, dtype_bytes, evaluate_formula_expr, evaluate_operator,
    evaluate_with_diagnostics, formula_catalog, resolve_sku,
    supported_operators,
)

BASE_PARAMS = {
    "matmul": dict(M=64, N=1024, K=1024),
    "quant_batch_matmul": dict(M=32, N=1024, K=1024, quant="w4a8"),
    "grouped_matmul": dict(tokens=32, hidden=1024, inter=512, experts_total=64,
                           experts_local=8, topk=8, ep=8),
    "flash_attention": dict(q_len=1, kv_len=1024, hq=32, hkv=4, head_dim=128),
    "incre_flash_attention": dict(q_len=1, kv_len=1024, hq=32, hkv=4, head_dim=128),
    "paged_attention": dict(q_len=1, kv_len=1024, hq=32, hkv=4, head_dim=128,
                            block_size=128),
    "fused_infer_attention_score": dict(q_len=1, kv_len=1024, hq=32, hkv=4,
                                        head_dim=128),
    "mla_prolog": dict(tokens=32, hidden=1024, heads=16, head_dim=128,
                       q_lora_rank=512, kv_lora_rank=512),
    "sparse_flash_mla": dict(tokens=32, heads=16, head_dim=128, kv_len=4096,
                             topk=512),
    "lightning_indexer": dict(tokens=32, heads=16, index_dim=128, kv_len=4096,
                              topk=512),
    "chunk_kda": dict(tokens=512, heads=16, head_dim=128),
    "chunk_gated_delta_rule": dict(tokens=512, heads=16, head_dim=128),
    "recurrent_kda": dict(tokens=8, heads=16, head_dim=128),
    "fused_recurrent_gdn": dict(tokens=8, heads=16, head_dim=128),
    "kda_recover_ssm_verify": dict(tokens=8, heads=16, head_dim=128),
    "kda_recover_ssm_commit": dict(tokens=8, heads=16, head_dim=128),
    "causal_conv1d": dict(tokens=512, channels=1024),
    "rms_norm": dict(rows=32, hidden=1024),
    "add_rms_norm": dict(rows=32, hidden=1024),
    "qk_rms_norm": dict(rows=32, hidden=1024),
    "swiglu": dict(rows=32, hidden=512),
    "silu_and_mul": dict(rows=32, hidden=512),
    "geglu": dict(rows=32, hidden=512),
    "rotary_position_embedding": dict(tokens=32, heads=16, head_dim=128),
    "slice": dict(rows=32, in_hidden=6144, out_hidden=3072),
    "dynamic_quant": dict(rows=32, hidden=1024),
    "dequant_swiglu_quant": dict(rows=32, hidden=512),
    "moe_gating_topk_softmax": dict(tokens=32, experts=64, hidden=1024, topk=8),
    "moe_init_routing": dict(tokens=32, experts=64, hidden=1024, topk=8),
    "moe_finalize_routing": dict(tokens=32, experts=64, hidden=1024, topk=8),
    "moe_distribute_dispatch": dict(tokens=32, hidden=1024, experts_total=64,
                                    experts_local=8, topk=8, ep=8),
    "moe_distribute_combine": dict(tokens=32, hidden=1024, experts_total=64,
                                   experts_local=8, topk=8, ep=8),
    "hccl_all_reduce": dict(size_bytes=1048576, world_size=8),
    "hccl_reduce_scatter": dict(size_bytes=1048576, world_size=8),
    "hccl_all_gather": dict(size_bytes=1048576, world_size=8),
    "hccl_all_to_all": dict(size_bytes=1048576, world_size=8),
    "hccl_broadcast": dict(size_bytes=1048576, world_size=8),
    "embedding": dict(tokens=32, hidden=1024, vocab=32000),
    "vocab_parallel_embedding": dict(tokens=32, hidden=1024, vocab=32000),
    "lm_head": dict(tokens=32, hidden=1024, vocab=32000),
    "logits_matmul": dict(tokens=32, hidden=1024, vocab=32000),
    "argmax": dict(tokens=32, vocab=32000),
    "top_p_sample": dict(tokens=32, vocab=32000),
}

VECTOR_ONLY = {
    "rms_norm", "add_rms_norm", "qk_rms_norm", "swiglu", "silu_and_mul",
    "geglu", "rotary_position_embedding", "dynamic_quant",
    "dequant_swiglu_quant", "moe_gating_topk_softmax", "moe_init_routing",
    "moe_finalize_routing", "causal_conv1d", "embedding",
    "vocab_parallel_embedding", "argmax", "top_p_sample", "hccl_all_reduce",
    "hccl_all_gather", "hccl_reduce_scatter", "hccl_all_to_all",
    "hccl_broadcast", "slice",
}


def _leaf_operators():
    return [name for name in supported_operators() if name != "composite_chain"]


def test_catalog_covers_required_families_and_names():
    catalog = formula_catalog()
    families = {item["family"] for item in catalog}
    assert len(families) >= 18
    assert len(catalog) >= 41
    assert len({item["operator"] for item in catalog}) == len(catalog)
    for operator in _leaf_operators():
        assert operator in BASE_PARAMS, operator


def test_alias_resolution_is_deterministic():
    assert canonical_name("aclnnGroupedMatmulV5_GroupedMatmul_GroupedMatmul") == "grouped_matmul"
    assert canonical_name("FusedInferAttentionScore") == "fused_infer_attention_score"
    assert canonical_name("aclnnRmsNorm_RmsNorm") == "rms_norm"
    assert canonical_name("aclnnAddRmsNorm_AddRmsNorm") == "add_rms_norm"
    assert canonical_name("AddRmsNorm") == "add_rms_norm"
    assert canonical_name("MoeDistributeDispatchV3") == "moe_distribute_dispatch"
    assert canonical_name("HcclAllReduce") == "hccl_all_reduce"
    assert canonical_name("QuantBatchMatmul") == "quant_batch_matmul"
    assert canonical_name("aclnnArgMax_ArgMax") == "argmax"
    assert canonical_name("TopPSample") == "top_p_sample"
    assert canonical_name("not_a_real_operator") is None


def test_every_operator_has_finite_dual_bounds_in_all_launch_modes():
    for operator in _leaf_operators():
        for launch_mode in LAUNCH_MODES:
            evaluation = evaluate_operator(operator, BASE_PARAMS[operator],
                                           launch_mode=launch_mode)
            tau = evaluation.latency.tau_hw_floor_us
            assert 0 < tau <= evaluation.t_floor_us <= evaluation.t_ref_us
            minimum = {"superkernel_subtask": 0.45, "aclgraph": 1.0,
                       "eager": 3.5, "python_eager": 3.5}[launch_mode]
            assert evaluation.t_floor_us >= minimum
            derating = evaluation.derating
            assert derating.bw_geom_efficiency == pytest.approx(
                derating.eta_asymp_bw * derating.bw_wave_efficiency
                * derating.coalesce_efficiency)


def test_card_expressions_reevaluate_to_their_numbers_for_every_operator():
    for operator in _leaf_operators():
        evaluation = evaluate_operator(operator, BASE_PARAMS[operator])
        card = evaluation.formula_card
        card.verify()
        for name, text, number in card.expr_pairs():
            value = evaluate_formula_expr(text, card.bindings)
            assert abs(float(value) - float(number)) <= 1e-9 * max(
                1.0, abs(float(number))), (operator, name, text)
        if card.cube_macs:
            assert card.alg_flops == pytest.approx(2 * card.cube_macs)
        else:
            # Vector-executed (for example the FP32 GDN recurrence) and
            # communication-only cards must not fabricate Cube work.
            assert card.vector_ops >= card.alg_flops


def test_vector_only_operators_never_charge_cube_work():
    for operator in sorted(VECTOR_ONLY):
        card = evaluate_operator(operator, BASE_PARAMS[operator]).formula_card
        assert card.cube_macs == 0, operator
        assert card.cube_flops_tiled == 0, operator
        assert card.alg_flops == 0, operator


def test_heterogeneous_composite_qualifies_every_component_binding():
    components = [
        {"operator": "matmul", "params": {"M": 32, "N": 896, "K": 7168}},
        {"operator": "matmul", "params": {"M": 128, "N": 256, "K": 512}},
        {"operator": "rms_norm", "params": {"rows": 32, "hidden": 7168}},
    ]
    evaluation = evaluate_operator("composite_chain",
                                   {"components": components},
                                   launch_mode="python_eager",
                                   steady_l2_warm=True)
    card = evaluation.formula_card
    card.verify()
    assert card.bindings["components"] == 3
    assert card.bindings["c0_M"] == 32 and card.bindings["c1_M"] == 128
    assert "c0_M" in card.alg_flops_expr and "c1_M" in card.alg_flops_expr
    for name, text, number in card.expr_pairs():
        assert abs(float(evaluate_formula_expr(text, card.bindings))
                   - float(number)) <= 1e-9 * max(1.0, abs(float(number))), name


def test_evaluation_is_json_roundtrippable_and_immutable():
    evaluation = evaluate_operator("matmul", dict(M=32, N=896, K=7168),
                                   launch_mode="python_eager",
                                   steady_l2_warm=True, measured_us=31.645)
    payload = evaluation.as_dict()
    loaded = json.loads(json.dumps(payload, sort_keys=True, allow_nan=False))
    assert loaded == payload
    assert loaded["schema"] == "mindie-operator-formula/1"
    with pytest.raises(TypeError):
        evaluation.formula_card.bindings["M"] = 999


def test_vector_rate_is_operations_per_second_not_bytes():
    evaluation = evaluate_operator("rms_norm", dict(rows=4096, hidden=7168),
                                   steady_l2_warm=True)
    vector_ops = evaluation.formula_card.vector_ops
    assert vector_ops == 146_800_640
    assert evaluation.latency.vector_floor_us == pytest.approx(
        146_800_640 / 6.7584e12 * 1e6, rel=1e-12)
    assert evaluation.latency.vector_floor_us == pytest.approx(
        21.7212121212, rel=1e-9)
    assert evaluation.t_floor_us == pytest.approx(21.7212121212, rel=1e-9)
    assert A5.vector_ops_per_s == 6.7584e12


def test_tiny_operators_never_hallucinate_sub_microsecond_floors():
    cases = [("matmul", dict(M=1, N=1, K=1)),
             ("rms_norm", dict(rows=1, hidden=1)),
             ("swiglu", dict(rows=1, hidden=1)),
             ("hccl_all_reduce", dict(size_bytes=1, world_size=2))]
    for operator, params in cases:
        for launch_mode, expected in (("superkernel_subtask", 0.45),
                                      ("aclgraph", 1.0), ("eager", 3.5),
                                      ("python_eager", 3.5)):
            evaluation = evaluate_operator(operator, params,
                                           launch_mode=launch_mode)
            assert evaluation.t_floor_us >= expected
            assert evaluation.t_floor_us > 0.4


def test_concurrent_pipes_use_max_not_sum():
    evaluation = evaluate_operator("matmul", dict(M=4096, N=4096, K=4096))
    latency = evaluation.latency
    pipes = [latency.cube_floor_us, latency.vector_floor_us,
             latency.gm_floor_us, latency.comm_floor_us]
    assert latency.t_floor_us == pytest.approx(
        max([latency.tau_hw_floor_us] + pipes))
    assert latency.t_floor_us < sum(pipes) + latency.tau_hw_floor_us


def test_gm_floor_is_a_concurrent_hbm_l2_bound():
    cold = evaluate_operator("rms_norm", dict(rows=512, hidden=7168))
    warm = evaluate_operator("rms_norm", dict(rows=512, hidden=7168),
                             steady_l2_warm=True)
    compulsory = cold.formula_card.compulsory_gm_bytes
    assert cold.formula_card.l2_hot_eligible_bytes == 0
    assert cold.latency.gm_floor_us == pytest.approx(compulsory / 4.0e12 * 1e6)
    hot = warm.formula_card.l2_hot_eligible_bytes
    assert 0 < hot <= compulsory
    expected = max((compulsory - hot) / 4.0e12, hot / 8.0e12) * 1e6
    assert warm.latency.gm_floor_us == pytest.approx(expected)
    assert warm.latency.gm_floor_us <= cold.latency.gm_floor_us


def test_cold_causal_conv1d_receives_no_l2_credit():
    cold = evaluate_operator("causal_conv1d",
                             dict(tokens=1, channels=4194304, width=4,
                                  run_mode=1), steady_l2_warm=False)
    assert cold.formula_card.l2_hot_eligible_bytes == 0
    assert cold.formula_card.compulsory_gm_bytes == 100_663_296
    assert cold.t_floor_us == pytest.approx(25.165824, rel=1e-12)
    warm = evaluate_operator("causal_conv1d",
                             dict(tokens=1, channels=4194304, width=4,
                                  run_mode=1), steady_l2_warm=True)
    assert warm.formula_card.l2_hot_eligible_bytes > 0
    assert warm.t_floor_us < cold.t_floor_us


def test_one_component_composite_is_the_identity():
    params = dict(M=32, N=896, K=7168)
    single = evaluate_operator("matmul", params, launch_mode="python_eager",
                               steady_l2_warm=True)
    wrapped = evaluate_operator("composite_chain",
                                {"components": [{"operator": "matmul",
                                                 "params": params}]},
                                launch_mode="python_eager",
                                steady_l2_warm=True)
    assert wrapped.t_floor_us == single.t_floor_us
    assert wrapped.t_ref_us == single.t_ref_us
    assert wrapped.formula_card.as_dict() == single.formula_card.as_dict()


def test_multi_component_composite_sums_serial_device_floors():
    components = [
        {"operator": "matmul", "params": {"M": 32, "N": 896, "K": 7168}},
        {"operator": "rms_norm", "params": {"rows": 32, "hidden": 7168}},
    ]
    singles = [evaluate_operator(item["operator"], item["params"],
                                 launch_mode="python_eager", steady_l2_warm=True)
               for item in components]
    composite = evaluate_operator("composite_chain",
                                  {"components": components},
                                  launch_mode="python_eager",
                                  steady_l2_warm=True)
    assert composite.t_floor_us == pytest.approx(
        sum(item.t_floor_us for item in singles))
    assert composite.t_floor_us >= 2 * composite.latency.tau_hw_floor_us
    assert composite.t_ref_us == pytest.approx(
        sum(item.t_ref_us for item in singles))


def test_dense_gemm_charges_no_quantization_work():
    dense = evaluate_operator("matmul", dict(M=1, N=32, K=32))
    quant = evaluate_operator("quant_batch_matmul",
                              dict(M=1, N=32, K=32, quant="w8a8"))
    assert dense.formula_card.vector_ops == 0
    assert quant.formula_card.vector_ops > 0
    assert dense.formula_card.cube_macs == 1024
    assert dense.formula_card.cube_flops_tiled == 2 * 16 * 32 * 32


def test_attention_cube_tier_follows_declared_precision():
    bf16 = evaluate_operator("flash_attention",
                             dict(q_len=1024, kv_len=1024, hq=8, hkv=8,
                                  head_dim=64, dtype="bf16"))
    fp32 = evaluate_operator("flash_attention",
                             dict(q_len=1024, kv_len=1024, hq=8, hkv=8,
                                  head_dim=64, dtype="fp32"))
    assert bf16.formula_card.bindings["dtype"] == "bf16"
    assert fp32.formula_card.bindings["dtype"] == "fp32"
    assert fp32.latency.cube_floor_us == pytest.approx(
        16 * bf16.latency.cube_floor_us, rel=1e-9)


def test_routing_uses_exact_log2_ceil_not_bit_length():
    evaluation = evaluate_operator("moe_gating_topk_softmax",
                                   dict(tokens=2, experts=8, hidden=8, topk=2))
    card = evaluation.formula_card
    assert card.vector_ops == 5 * 2 * 8 + 2 * 8 * 3
    assert card.vector_ops == 128
    assert "log2_ceil(experts)" in card.vector_ops_expr


def test_fp32_gemm_uses_the_fp32_cube_peak():
    bf16 = evaluate_operator("matmul", dict(M=4096, N=4096, K=4096,
                                            dtype="bf16"), sku="a5")
    fp32 = evaluate_operator("matmul", dict(M=4096, N=4096, K=4096,
                                            dtype="fp32"), sku="a5")
    assert bf16.latency.cube_floor_us == pytest.approx(317.7503030303, rel=1e-9)
    assert fp32.latency.cube_floor_us == pytest.approx(5084.0048484848, rel=1e-9)
    assert fp32.latency.cube_floor_us == pytest.approx(
        16 * bf16.latency.cube_floor_us, rel=1e-9)
    assert fp32.formula_card.bindings["compute_tier"] == "fp32"


def test_dtype_bytes_are_exact_and_unknown_names_are_rejected():
    assert dtype_bytes("fp8_e4m3") == 1.0
    assert dtype_bytes("fp8_e5m2") == 1.0
    assert dtype_bytes("fp8") == 1.0
    assert dtype_bytes("float8_e4m3fn") == 1.0
    assert dtype_bytes("bf16") == 2.0 and dtype_bytes("bfloat16") == 2.0
    assert dtype_bytes("int4") == 0.5 and dtype_bytes("mxfp4") == 0.5
    assert dtype_bytes("int32") == 4.0 and dtype_bytes("int64") == 8.0
    for bad in ("dt_mystery", "float128", "", None):
        with pytest.raises(FormulaValidationError):
            dtype_bytes(bad)


def test_quantization_scale_tensors_and_group_size_validation():
    w8 = evaluate_operator("quant_batch_matmul",
                           dict(M=32, N=1024, K=1024, quant="w8a8"))
    mxfp8 = evaluate_operator("quant_batch_matmul",
                              dict(M=32, N=1024, K=1024, quant="mxfp8"))
    assert w8.formula_card.compulsory_read_bytes > 32 * 1024
    assert mxfp8.formula_card.bindings["group_size"] == 32
    assert mxfp8.formula_card.bindings["compute_tier"] == "fp8"
    with pytest.raises(FormulaValidationError):
        evaluate_operator("quant_batch_matmul",
                          dict(M=32, N=1024, K=1024, quant="mxfp8",
                               group_size=16))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("quant_batch_matmul",
                          dict(M=32, N=1000, K=1020, quant="w4a16",
                               group_size=128))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("quant_batch_matmul",
                          dict(M=32, N=1024, K=1024, quant="mystery_quant"))


def test_per_buffer_granule_alignment():
    assert evaluate_operator("rms_norm", dict(rows=1, hidden=1)
                             ).formula_card.granule_gm_bytes == 384
    assert evaluate_operator("add_rms_norm", dict(rows=1, hidden=1)
                             ).formula_card.granule_gm_bytes == 640
    card = evaluate_operator("add_rms_norm", dict(rows=1, hidden=1)).formula_card
    assert card.granule_read_bytes == 384 and card.granule_write_bytes == 256
    assert card.compulsory_gm_bytes == 10


def test_rope_rotation_work_scales_with_rotary_dim():
    narrow = evaluate_operator("rotary_position_embedding",
                               dict(tokens=32, heads=16, head_dim=128,
                                    rotary_dim=8))
    wide = evaluate_operator("rotary_position_embedding",
                             dict(tokens=32, heads=16, head_dim=128,
                                  rotary_dim=128))
    assert wide.formula_card.vector_ops == pytest.approx(
        16 * narrow.formula_card.vector_ops)
    assert wide.formula_card.vector_ops == pytest.approx(393216)
    for bad in (0, 130, 7):
        with pytest.raises(FormulaValidationError):
            evaluate_operator("rotary_position_embedding",
                              dict(tokens=4, heads=2, head_dim=128,
                                   rotary_dim=bad))


def test_gated_activation_operation_counts():
    swiglu = evaluate_operator("swiglu", dict(rows=32, hidden=512))
    geglu = evaluate_operator("geglu", dict(rows=32, hidden=512))
    gate = evaluate_operator("swiglu", dict(rows=32, hidden=512,
                                            mode="gate_mul"))
    assert swiglu.formula_card.vector_ops == 5 * 32 * 512
    assert geglu.formula_card.vector_ops == 8 * 32 * 512
    assert gate.formula_card.vector_ops == 32 * 512


def test_lm_head_sampler_separation_and_standalone_samplers():
    projection = evaluate_operator("lm_head", dict(tokens=32, hidden=1024,
                                                   vocab=32000))
    with_sampler = evaluate_operator("lm_head", dict(tokens=32, hidden=1024,
                                                     vocab=32000,
                                                     include_sampler=True))
    assert projection.formula_card.vector_ops == 0
    assert with_sampler.formula_card.vector_ops == 5 * 32 * 32000
    for name in ("argmax", "top_p_sample"):
        card = evaluate_operator(name, dict(tokens=32, vocab=32000)).formula_card
        assert card.cube_macs == 0 and card.cube_flops_tiled == 0
        assert card.compulsory_read_bytes == 32 * 32000 * 4
        assert card.compulsory_write_bytes == 32 * 4
    assert evaluate_operator("argmax", dict(tokens=32, vocab=32000)
                             ).formula_card.vector_ops == 32 * 32000


def test_invalid_inputs_raise_actionable_errors():
    with pytest.raises(FormulaError):
        evaluate_operator("matmul", dict(M=0, N=1, K=1))
    with pytest.raises(FormulaError):
        evaluate_operator("matmul", dict(N=1, K=1))
    with pytest.raises(FormulaError):
        evaluate_operator("not_an_operator", {})
    with pytest.raises(FormulaError):
        evaluate_operator("matmul", dict(M=1, N=1, K=1), launch_mode="teleport")
    with pytest.raises(FormulaError):
        evaluate_operator("moe_gating_topk_softmax",
                          dict(tokens=4, experts=8, hidden=8, topk=9))


def test_diagnose_reports_clean_and_violation_without_clamping():
    evaluation, clean = evaluate_with_diagnostics(
        "matmul", dict(M=32, N=896, K=7168), launch_mode="python_eager",
        steady_l2_warm=True, measured_us=31.645)
    assert clean["bound_violation_warning"] is False
    assert clean["sol_floor_pct"] <= 100.0
    assert clean["structural_gap_us"] == pytest.approx(
        evaluation.t_ref_us - evaluation.t_floor_us)
    _, violation = evaluate_with_diagnostics(
        "matmul", dict(M=32, N=896, K=7168), launch_mode="python_eager",
        steady_l2_warm=True, measured_us=evaluation.t_floor_us * 0.5)
    assert violation["bound_violation_warning"] is True
    assert violation["sol_floor_pct"] > 100.0
    assert violation["root_cause_candidates"]


def test_sku_ordering_and_resolution():
    params = dict(M=4096, N=4096, K=4096)
    floors = [evaluate_operator("matmul", params, launch_mode=mode).t_floor_us
              for mode in LAUNCH_MODES]
    assert floors == sorted(floors)
    assert A2.hbm_bps > A3.hbm_bps
    assert evaluate_operator("matmul", params, sku="a5").t_floor_us < \
        evaluate_operator("matmul", params, sku="a3").t_floor_us
    assert resolve_sku("Ascend950DT_9582").sku == "Ascend950DT_9582"
    assert resolve_sku("Ascend950PR_9579").hbm_bps < \
        resolve_sku("Ascend950DT_9581").hbm_bps


def test_cli_evaluates_and_rejects_bad_params(tmp_path):
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-m", "mindie_profiler", "op-formula",
               "--operator", "matmul", "--params",
               json.dumps({"M": 32, "N": 896, "K": 7168}),
               "--launch-mode", "python_eager", "--steady-l2-warm",
               "--measured-us", "31.645"]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True,
                            timeout=60)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["operator"] == "matmul"
    assert payload["diagnostic"]["bound_violation_warning"] is False
    bad = subprocess.run(
        [sys.executable, "-m", "mindie_profiler", "op-formula",
         "--operator", "matmul", "--params", "[]"],
        cwd=root, capture_output=True, text=True, timeout=60)
    assert bad.returncode == 2
    assert "Traceback" not in bad.stderr
