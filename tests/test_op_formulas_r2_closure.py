"""Round-2 regression matrix for R2-01..R2-14 (formulas, ABI, MCP envelope).

[Role]
  Independently exercise the repaired per-sequence attention geometry, strict
  catalog ABI interpretation, linear-attention recurrence/state ownership,
  sparse unique-key floors, MoE certified arrivals, quantization ownership,
  HCCL/MC2 algorithms and fit domains, public-boundary validation, mixed
  diagnostic envelopes, provable token budgets, vector buffer ownership, AST
  associativity and single-child composite diagnostics.

[Invariants]
  * Every rejection test asserts the exact stable error class, never "raises
    anything"; every acceptance test asserts an exact number or binding.
  * Compulsory floors are checked against legal counterexamples (empty expert
    rank, repeated sparse selections) rather than against the same formula.
  * Token-budget checks compare the conservative bound with the two real BPE
    encoders on the complete serialized envelope when tiktoken is available.
  * No assertion is a tautology; truthiness escapes are never used.

[Timeouts & Locks]
  Pure in-memory formula evaluation; tokenizer vocabularies are read from an
  offline cache and are never downloaded by this module.

[Side-Effect Policy]
  No file writes, network calls, device work or global mutation.
"""

from __future__ import annotations

import json
import random
import string
from pathlib import Path

import pytest

from mindie_profiler.op_abi_bridge import AbiError, infer_request
from mindie_profiler.op_formula_annotator import (
    annotate_profile_formulas, call_mcp_tool,
)
from mindie_profiler.token_budget import (
    fit_receipt_envelope, serialize, upper_bound_text, upper_bound_tokens,
)
from mindie_sim.op_formulas import (
    A5, FormulaValidationError, evaluate_operator,
)
from mindie_sim.op_formulas.expr_ast import (
    BinOp, Call, Const, Neg, evaluate_formula_expr,
)
from mindie_sim.op_formulas.primitives import attended_pairs

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "a5_op_goldens.json"


def card(operator: str, **params):
    return evaluate_operator(operator, params).formula_card


def raw(name: str, shapes, dtypes=None, layouts=None, outputs=None, **kw):
    return {
        "name": name, "type": name,
        "input_shapes": ";".join(
            ",".join(map(str, shape)) if isinstance(shape, (list, tuple))
            else str(shape) for shape in shapes),
        "input_data_types": ";".join(dtypes or ["DT_BF16"] * len(shapes)),
        "input_formats": ";".join(layouts or ["ND"] * len(shapes)),
        "output_shapes": ";".join(",".join(map(str, shape))
                                  for shape in (outputs or [])),
        "output_data_types": ";".join(["DT_BF16"] * len(outputs or [])),
        "output_formats": ";".join(["ND"] * len(outputs or [])),
        **kw,
    }


# --------------------------------------------------------------------------- #
# R2-01: per-sequence causal geometry, mask presence, cumulative decoding.
# --------------------------------------------------------------------------- #
def test_r2_01_batched_causal_geometry_is_permutation_invariant():
    params = dict(q_len=1, kv_len=4096, hq=8, hkv=2, head_dim=64, batch=2,
                  causal=True, actual_seq_lens_q=[1, 1],
                  actual_seq_lens_kv=[128, 4096])
    card_a = card("flash_attention", **params)
    assert card_a.bindings["attended_pairs"] == 4224
    assert card_a.bindings["active_causal_tiles"] == 33
    card_b = card("flash_attention", **dict(
        params, actual_seq_lens_kv=[4096, 128]))
    assert card_b.alg_flops == card_a.alg_flops
    assert card_b.cube_flops_tiled == card_a.cube_flops_tiled
    assert card_b.vector_ops == card_a.vector_ops
    assert card_b.compulsory_read_bytes == card_a.compulsory_read_bytes
    assert card_b.compulsory_write_bytes == card_a.compulsory_write_bytes


def test_r2_01_sparse_and_indexer_work_is_additive_per_sequence():
    sparse_single = card(
        "sparse_flash_mla", tokens=16, heads=1, head_dim=128, kv_len=128,
        topk=8, q_lens=[16], kv_lens=[128])
    sparse_pair = card(
        "sparse_flash_mla", tokens=32, heads=1, head_dim=128, kv_len=128,
        topk=8, q_lens=[16, 16], kv_lens=[128, 128])
    assert sparse_pair.cube_flops_tiled == 2 * sparse_single.cube_flops_tiled
    indexer_single = card(
        "lightning_indexer", tokens=16, heads=1, index_dim=32, kv_len=128,
        topk=8, q_lens=[16], kv_lens=[128])
    indexer_pair = card(
        "lightning_indexer", tokens=32, heads=1, index_dim=32, kv_len=128,
        topk=8, q_lens=[16, 16], kv_lens=[128, 128])
    assert indexer_pair.cube_flops_tiled == 2 * indexer_single.cube_flops_tiled
    assert indexer_pair.cube_flops_tiled == 262_144


def test_r2_01_mask_shape_and_contradictory_presence():
    masked = card("flash_attention", q_len=16, kv_len=16, hq=4, hkv=4,
                  head_dim=64, attn_mask_shape=[16, 16])
    assert masked.bindings["mask_bytes"] == 256
    bf16_mask = card("flash_attention", q_len=16, kv_len=16, hq=4, hkv=4,
                     head_dim=64, attn_mask_shape=[16, 16],
                     mask_dtype="bf16")
    assert bf16_mask.bindings["mask_bytes"] == 512
    with pytest.raises(FormulaValidationError):
        evaluate_operator("flash_attention", dict(
            q_len=16, kv_len=16, hq=4, hkv=4, head_dim=64,
            attn_mask_shape=[16, 16], has_attn_mask=False))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("flash_attention", dict(
            q_len=16, kv_len=16, hq=4, hkv=4, head_dim=64,
            attn_mask_shape=[16, 0]))


def test_r2_01_cumulative_lengths_shared_by_direct_and_native_routes():
    direct = card(
        "flash_attention", q_len=5, kv_len=7, hq=8, hkv=2, head_dim=64,
        batch=2, actual_seq_lengths=[2, 5], actual_seq_lengths_kv=[3, 7],
        actual_seq_lengths_type="cumsum")
    alias = card(
        "flash_attention", q_len=5, kv_len=7, hq=8, hkv=2, head_dim=64,
        batch=2, actual_seq_lens=[2, 5], actual_seq_lens_kv=[3, 7],
        actual_seq_lengths_type="cumulative")
    assert direct.bindings["attended_pairs"] == 18
    assert alias.bindings["attended_pairs"] == 18
    native_row = raw(
        "FlashAttentionScore", [[5, 8, 64], [7, 2, 64], [7, 2, 64]],
        outputs=[[5, 8, 64]],
        layouts=["TND"] * 3, actual_seq_lengths=[2, 5],
        actual_seq_lengths_kv=[3, 7])
    operator, params, _flags = infer_request(native_row)
    native = card(operator, **params)
    assert native.alg_flops == direct.alg_flops
    for bad in ([2, 1], [2, -1], [2, 8]):
        with pytest.raises(FormulaValidationError):
            evaluate_operator("flash_attention", dict(
                q_len=5, kv_len=7, hq=8, hkv=2, head_dim=64, batch=2,
                actual_seq_lengths=bad, actual_seq_lengths_type="cumsum"))


# --------------------------------------------------------------------------- #
# R2-02: fail-closed ABI, positional slots, GEMM/GMM/collective ownership.
# --------------------------------------------------------------------------- #
def test_r2_02_attention_abi_ownership_and_layouts():
    attn = raw(
        "FusedInferAttentionScore",
        [[2, 128, 8, 64], [2, 256, 2, 64], [2, 256, 2, 32]],
        layouts=["BSND"] * 3, outputs=[[2, 128, 8, 32]], causal=True)
    operator, params, _flags = infer_request(attn)
    attention_card = card(operator, **params)
    assert attention_card.bindings["head_dim_qk"] == 64
    assert attention_card.bindings["head_dim_v"] == 32
    assert attention_card.bindings["causal"] is True
    with pytest.raises(AbiError):
        infer_request(raw("FusedInferAttentionScore",
                          [[2, 128, 8, 64], [3, 256, 2, 64],
                           [2, 256, 2, 64]], layouts=["BSND"] * 3))
    with pytest.raises(AbiError):
        infer_request(raw("FlashAttentionScore",
                          [[8, 8, 64], [16, 2, 64]], layouts=["TND"] * 2))
    with pytest.raises(AbiError):
        infer_request(raw("FlashAttentionScore",
                          [[8, 8, 64], [16, 2, 64], [16, 2, 64]],
                          layouts=["BOGUS"] * 3))
    bnsd = raw("aclnnFusedInferAttentionScore_BNSD",
               [[2, 8, 128, 64], [2, 2, 256, 64], [2, 2, 256, 64]],
               layouts=["BNSD"] * 3, outputs=[[2, 8, 128, 64]])
    operator, params, _flags = infer_request(bnsd)
    assert params["layout"] == "BNSD"
    assert params["q_len"] == 128 and params["batch"] == 2


def test_r2_02_matmul_grouped_and_collective_abi():
    with pytest.raises(AbiError):
        infer_request(raw("BatchMatMul",
                          [[2, 3, 4, 8], [3, 2, 8, 16]],
                          outputs=[[2, 3, 4, 16]]))
    with pytest.raises(AbiError):
        infer_request(raw("MatMul", ["bad", [32, 128], [128, 64]],
                          outputs=[[32, 64]]))
    grouped = raw("GroupedMatmul", [[32, 128], [2, 128, 512]],
                  outputs=[[32, 512]], group_list=[16, 16])
    operator, params, _flags = infer_request(grouped)
    grouped_card = card(operator, **params)
    assert grouped_card.bindings["K"] == 128
    assert grouped_card.bindings["N"] == 512
    operator, params, _flags = infer_request(
        raw("HcclAllReduce", [[1024]], outputs=[[1024]], dtypes=["DT_BF16"], world_size=4))
    assert params["size_bytes"] == 2048
    assert operator == "hccl_all_reduce"
    with pytest.raises(AbiError) as error:
        infer_request(raw("MatMul", [[32, 128], [128, 256]],
                          dtypes=["DT_MYSTERY", "DT_BF16"],
                          outputs=[[32, 256]]))
    assert error.value.code == "unknown_dtype"


# --------------------------------------------------------------------------- #
# R2-03: recurrence physics, chunk state ownership, decode conv state.
# --------------------------------------------------------------------------- #
def test_r2_03_recurrent_gdn_is_vector_executed_full_recurrence():
    recurrent = card("fused_recurrent_gdn", tokens=1, heads=1, head_dim=128)
    mandatory = 7 * 128 * 128 + 3 * 128 + 128
    assert mandatory == 115_200
    assert recurrent.alg_flops >= mandatory
    assert recurrent.vector_ops == recurrent.alg_flops
    assert recurrent.cube_macs == 0
    assert recurrent.cube_flops_tiled == 0
    assert recurrent.bindings["state_bytes_per_seq"] == 128 * 128 * 4
    with pytest.raises(FormulaValidationError):
        evaluate_operator("fused_recurrent_gdn",
                          dict(tokens=1, heads=1, head_dim=128,
                               state_dtype="int32"))


def test_r2_03_chunk_state_ownership_and_commit_classification():
    implicit = card("chunk_kda", tokens=512, heads=16, head_dim=128)
    explicit = card("chunk_kda", tokens=512, batch=1, heads=16, head_dim=128)
    assert implicit.bindings["sequences"] == 1
    assert implicit.compulsory_gm_bytes == explicit.compulsory_gm_bytes
    state_row = raw("ChunkGatedDeltaRule",
                    [[512, 16, 128], [512, 16, 128], [512, 16, 128],
                     [512, 16], [512, 16, 128], [1, 16, 128, 128]],
                    outputs=[[512, 16, 128], [1, 16, 128, 128]],
                    actual_seq_lengths="512")
    operator, params, _flags = infer_request(state_row)
    assert operator == "chunk_kda"
    assert params["batch"] == 1
    bad_state = raw("ChunkGatedDeltaRule",
                    [[512, 16, 128], [512, 16, 128], [512, 16, 128],
                     [512, 16], [512, 16, 128], [2, 16, 128, 128]],
                    outputs=[[512, 16, 128], [2, 16, 128, 128]],
                    actual_seq_lengths="512")
    with pytest.raises(AbiError):
        infer_request(bad_state)
    commit = raw("KdaRecoverSsmCommit", [[1, 16, 128]],
                 outputs=[[1, 16, 128, 128]])
    operator, _params, _flags = infer_request(commit)
    assert operator == "kda_recover_ssm_commit"
    verify = raw("KdaRecoverSsmVerify", [[1, 16, 128]],
                 outputs=[[1, 16, 128, 128]])
    assert infer_request(verify)[0] == "kda_recover_ssm_verify"


def test_r2_03_decode_conv_ring_state_is_per_sequence():
    single = card("causal_conv1d", tokens=1, channels=16, width=4, run_mode=1)
    batch = card("causal_conv1d", tokens=8, channels=16, width=4, run_mode=1)
    assert single.compulsory_read_bytes == 256
    assert single.compulsory_write_bytes == 128
    assert batch.compulsory_read_bytes == 1152
    assert batch.compulsory_write_bytes == 1024
    with pytest.raises(FormulaValidationError):
        evaluate_operator("chunk_kda", dict(tokens=8, heads=2, head_dim=64,
                                            batch=1, state_dtype="int32"))


# --------------------------------------------------------------------------- #
# R2-04: sparse unique-key lower bound and per-sequence indexer tiling.
# --------------------------------------------------------------------------- #
def test_r2_04_sparse_unique_keys_are_a_compulsory_floor():
    sparse = card("sparse_flash_mla", tokens=32, heads=1, head_dim=128,
                  kv_len=4096, topk=512, q_lens=[32], kv_lens=[4096])
    assert sparse.bindings["unique_kv_tokens"] == 512
    assert sparse.granule_gm_bytes >= sparse.compulsory_gm_bytes
    explicit = card("sparse_flash_mla", tokens=32, heads=1, head_dim=128,
                    kv_len=4096, topk=512, q_lens=[32], kv_lens=[4096],
                    unique_selected_kv=512)
    assert explicit.bindings["unique_kv_tokens"] == 512
    with pytest.raises(FormulaValidationError):
        evaluate_operator("sparse_flash_mla", dict(
            tokens=32, heads=1, head_dim=128, kv_len=4096, topk=512,
            q_lens=[32], kv_lens=[4096], unique_selected_kv=999_999))


# --------------------------------------------------------------------------- #
# R2-05: certified MoE arrivals versus statistical expectation.
# --------------------------------------------------------------------------- #
def test_r2_05_empty_rank_counterexample_and_feasibility():
    base = dict(tokens=4096, hidden=7168, inter=3072, experts_total=64,
                experts_local=8, topk=8, ep=8)
    unknown = evaluate_operator("grouped_matmul", base)
    empty = evaluate_operator("grouped_matmul", dict(base, group_list=[0] * 8))
    assert unknown.t_floor_us <= empty.t_floor_us
    assert unknown.formula_card.bindings["floor_routed_rows"] == 0
    assert unknown.formula_card.bindings["min_active_experts"] == 0
    assert unknown.formula_card.bindings["expected_routed_rows"] == 4096 * 8
    with pytest.raises(FormulaValidationError):
        evaluate_operator("grouped_matmul", dict(
            tokens=16, hidden=128, inter=64, experts_total=8, experts_local=8,
            topk=4, ep=1, group_list=[64] + [0] * 7))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("grouped_matmul", dict(
            tokens=16, hidden=128, inter=64, experts_total=8, experts_local=8,
            topk=4, ep=1, routed_rows=1))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("grouped_matmul", dict(
            tokens=16, hidden=128, inter=64, experts_total=8, experts_local=8,
            topk=4, ep=1, group_list=[1] * 8))


def test_r2_05_reference_tiling_uses_expected_active_experts():
    grouped = card("grouped_matmul", tokens=16, hidden=128, inter=64,
                   experts_total=8, experts_local=8, topk=2, ep=1,
                   group_list=[4] * 8)
    # 32 expected rows over 8 active experts -> 4 rows each, padded to 16.
    # ``up_gate`` produces 2 * inter = 128 output columns.
    expected_tiled = 2 * 8 * 16 * 128 * 128
    assert grouped.bindings["expected_routed_rows"] == 32
    assert grouped.bindings["expected_active_experts"] == 8
    assert grouped.bindings["uniform_rows_per_expert"] == 4
    assert grouped.cube_flops_tiled == expected_tiled


# --------------------------------------------------------------------------- #
# R2-06: typed quantization contract and sub-byte buffer rounding.
# --------------------------------------------------------------------------- #
def test_r2_06_quant_batch_and_one_expert_equivalence():
    q1 = card("quant_batch_matmul", M=16, N=32, K=128, quant="w8a8")
    q4 = card("quant_batch_matmul", M=16, N=32, K=128, quant="w8a8",
              batch=4, weight_broadcast=False)
    assert q4.compulsory_read_bytes == 4 * q1.compulsory_read_bytes
    assert q4.compulsory_read_bytes == 25_344
    assert q4.vector_ops == 4 * q1.vector_ops
    dense = card("quant_batch_matmul", M=32, N=128, K=128, quant="w4a16")
    grouped = card("grouped_matmul", tokens=32, hidden=128, inter=64,
                   experts_total=1, experts_local=1, topk=1, ep=1,
                   group_list=[32], quant="w4a16")
    assert grouped.vector_ops == dense.vector_ops
    with pytest.raises(FormulaValidationError):
        evaluate_operator("quant_batch_matmul", dict(
            M=16, N=32, K=128, quant="w8a8", dtype="nonsense"))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("moe_distribute_dispatch", dict(
            tokens=8, hidden=128, experts_total=8, topk=2, ep=2,
            quant="nonsense"))


def test_r2_06_sub_byte_buffers_round_per_buffer():
    for dtype in ("int4", "mxfp4", "uint4", "fp4"):
        evaluation = evaluate_operator("matmul", dict(
            M=1, N=1, K=1, dtype=dtype))
        evaluation.formula_card.verify()
        assert evaluation.formula_card.compulsory_read_bytes >= 2
        assert evaluation.formula_card.compulsory_write_bytes >= 1
    grouped = evaluate_operator("grouped_matmul", dict(
        tokens=1, hidden=1, inter=1, experts_total=1, experts_local=1,
        topk=1, ep=1, group_list=[1], dtype="int4"))
    grouped.formula_card.verify()
    assert grouped.formula_card.compulsory_read_bytes == 2
    assert grouped.formula_card.compulsory_write_bytes == 1


# --------------------------------------------------------------------------- #
# R2-07: HCCL split buffers, algorithm schedule, MC2 reference and domain.
# --------------------------------------------------------------------------- #
def test_r2_07_split_buffers_and_algorithm_schedule():
    split = card("hccl_all_to_all", size_bytes=4096, world_size=4,
                 send_counts=[1024] * 4, recv_counts=[1024] * 4)
    assert split.compulsory_read_bytes == 8192
    assert split.compulsory_write_bytes == 8192
    with pytest.raises(FormulaValidationError):
        evaluate_operator("hccl_all_to_all", dict(
            size_bytes=4096, world_size=4, send_counts=[0, -1, 2, 3],
            recv_counts=[0, 1, 2, 3]))
    refs = {}
    for algorithm in ("ring", "hd", "mesh"):
        refs[algorithm] = evaluate_operator(
            "hccl_all_reduce", dict(size_bytes=4096, world_size=8,
                                    algorithm=algorithm,
                                    transport="roce")).t_ref_us
    assert refs["ring"] > refs["hd"] > refs["mesh"]
    assert refs["mesh"] > 0


def test_r2_07_mc2_reference_traffic_and_exact_locality():
    reference = evaluate_operator("moe_distribute_dispatch", dict(
        tokens=32, hidden=1024, experts_total=64, experts_local=8, topk=8,
        ep=8, use_measured_fit=False))
    assert reference.formula_card.comm_bytes == 0
    assert reference.formula_card.comm_ref_bytes > 0
    assert reference.latency.comm_ref_us > 0
    local = card("moe_distribute_dispatch", tokens=32, hidden=1024,
                 experts_total=64, experts_local=8, topk=8, ep=8,
                 remote_routed_rows=0)
    assert local.comm_bytes == 0
    assert local.comm_ref_bytes == 0


def test_r2_07_mc2_fit_domain_requires_exact_captured_geometry():
    base = dict(tokens=32, experts_local=8, ep=8, use_measured_fit=True)
    in_domain = card("moe_distribute_dispatch", **base, hidden=7168,
                     experts_total=64, topk=8)
    assert in_domain.bindings["fit_domain_status"] == "in_calibrated_ref_domain"
    assert in_domain.bindings["fit_source"] == "a5_mc2_measured"
    for mismatch in (dict(hidden=1024, experts_total=64, topk=8),
                     dict(hidden=7168, experts_total=256, topk=8),
                     dict(hidden=7168, experts_total=64, topk=4),
                     dict(hidden=7168, experts_total=64, topk=8, quant="w8a8"),
                     dict(hidden=7168, experts_total=64, topk=8, dtype="fp16")):
        outside = card("moe_distribute_dispatch", **base, **mismatch)
        assert outside.bindings["fit_domain_status"] == \
            "outside_captured_workload_geometry"
        assert "fit_source" not in outside.bindings


def test_r2_07_all_golden_mc2_points_are_clean_and_domain_consistent():
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    points = [point for point in golden["points"] if point["group"] == "mc2"]
    assert len(points) == 36
    for point in points:
        evaluation = evaluate_operator(point["operator"], point["params"])
        status = evaluation.formula_card.bindings["fit_domain_status"]
        assert status == point["fit_domain_status"], point["id"]
        assert point["params"]["hidden"] == 7168
        assert point["params"]["experts_total"] == 64
        assert point["params"]["topk"] == 8


# --------------------------------------------------------------------------- #
# R2-08 / R2-09: public validation and mixed diagnostic envelopes.
# --------------------------------------------------------------------------- #
def test_r2_08_public_boundaries_are_strict_and_never_crash():
    with pytest.raises(FormulaValidationError):
        evaluate_operator("matmul", dict(M=16, N=128, K=128),
                          steady_l2_warm="false")
    with pytest.raises(FormulaValidationError):
        evaluate_operator("composite_chain", dict(
            components=[dict(operator="flash_attention", params=[])]))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("matmul", dict(M=16, N=128, K=128),
                          measured_us=10 ** 400)
    assert call_mcp_tool("evaluate_op_formula", dict(
        operator="flash_attention", params=[]))["status"] == "invalid_request"
    for bad_tol in (float("nan"), float("inf"), -0.5, 1.0):
        receipt = call_mcp_tool("evaluate_op_formula", dict(
            operator="matmul", params=dict(M=2, N=2, K=2), tol=bad_tol))
        assert receipt["status"] == "invalid_request"
    with pytest.raises(FormulaValidationError):
        annotate_profile_formulas(
            [dict(operator="matmul", params=dict(M=2, N=2, K=2))],
            tol=float("nan"))


def test_r2_09_mixed_status_error_codes_and_canonical_identity():
    mixed = [
        dict(operator="matmul", params=dict(M=1024, N=1024, K=1024),
             measured_us=0.01),
        dict(operator="matmul", params=dict(M=-1, N=2, K=2), measured_us=10),
    ]
    aggregate = call_mcp_tool("annotate_profile_formulas", dict(rows=mixed))
    assert aggregate["status"] == "violations_detected"
    assert aggregate["violation_count"] == 1
    assert aggregate["invalid_rows"] == 1
    assert "validation_error" in json.dumps(aggregate)
    batch = call_mcp_tool("annotate_profile_formulas", dict(
        rows=[dict(operator="matmul", params=dict(M=32, N=896, K=7168),
                   measured_us=31.645)] * 8
        + [dict(operator="matmul", params=dict(M=1024, N=1024, K=1024),
                measured_us=0.01)] * 112,
        launch_mode="python_eager"))
    assert (batch["total_rows"], batch["violation_count"]) == (120, 112)
    alias = call_mcp_tool("annotate_profile_formulas", dict(
        rows=[dict(operator="matmul_" + "Z" * 20000,
                   params=dict(M=32, N=128, K=128), measured_us=0.01)]))
    assert alias["sample_rows_returned"] >= 1
    assert alias["sample_rows"][0]["canonical_op"] == "matmul"
    assert len(alias["sample_rows"][0]["canonical_op"]) <= 24
    unmodeled = call_mcp_tool("evaluate_op_formula", dict(
        operator="not_a_real_operator", params=dict(M=2, N=2, K=2)))
    assert unmodeled["status"] == "unmodeled"


# --------------------------------------------------------------------------- #
# R2-10: provable token bound and zero path leakage.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def bpe_encoders():
    tiktoken = pytest.importorskip("tiktoken")
    return [tiktoken.get_encoding(name) for name in
            ("o200k_base", "cl100k_base")]


def test_r2_10_real_bpe_bound_and_path_sanitization(bpe_encoders):
    adversarial = [
        "\U00010428" * 200,
        "\U0001f600" * 200,
        "qz" * 128,
        "0a" * 64,
        "qzxj" * 50,
        "/Users/alice/secret.csv",
        "e\u0301" * 160,
    ]
    for bad in adversarial:
        receipt = call_mcp_tool("evaluate_op_formula", dict(
            operator="matmul", params=dict(M=2, N=2, K=2, dtype=bad)))
        text = serialize(receipt)
        counts = [len(encoder.encode(text)) for encoder in bpe_encoders]
        assert max(counts) <= 250
        assert upper_bound_tokens(receipt) >= max(counts)
        assert receipt["receipt"]["within_budget"] is True
        assert receipt["receipt"]["token_limit"] == 250
        assert "/Users/alice/" not in text
        assert "secret.csv" not in text
    path = call_mcp_tool("evaluate_op_formula", dict(
        operator="/Users/alice/secret.csv"))
    assert "/Users/alice/" not in serialize(path)


def test_r2_10_tiny_envelope_always_fits_an_oversized_core(bpe_encoders):
    core = {
        "schema": "mindie-op-formula-mcp/1",
        "status": "invalid_abi",
        "error_code": "validation_error",
        "operator": "/Users/alice/secret.csv",
        "reason": "x" * 20_000,
    }
    envelope = fit_receipt_envelope(core, (), limit=250)
    text = serialize(envelope)
    counts = [len(encoder.encode(text)) for encoder in bpe_encoders]
    assert max(counts) <= 250
    assert upper_bound_tokens(envelope) >= max(counts)
    assert envelope["receipt"]["within_budget"] is True


def test_r2_10_upper_bound_fuzz_matches_real_encoders(bpe_encoders):
    rng = random.Random(19)
    alphabet = ("abcXYZ0123 _-/\\.:" + "\U00010428\U0001f600\u0301\u00e9"
                + string.printable)
    for _ in range(400):
        text = "".join(rng.choice(alphabet)
                       for _ in range(rng.randint(0, 120)))
        bound = upper_bound_text(text)
        assert bound >= len(text.encode("utf-8"))
        for encoder in bpe_encoders:
            assert bound >= len(encoder.encode(text))


# --------------------------------------------------------------------------- #
# R2-11 / R2-12 / R2-13: vector buffers, AST associativity, composite identity.
# --------------------------------------------------------------------------- #
def test_r2_11_vector_buffers_are_independently_aligned():
    gate = card("swiglu", rows=1, hidden=1, mode="gate_mul")
    packed = card("swiglu", rows=1, hidden=1, mode="packed")
    assert gate.granule_read_bytes == 256
    assert packed.granule_read_bytes == 128
    plain = card("dynamic_quant", rows=2, hidden=128)
    smooth = card("dynamic_quant", rows=2, hidden=128,
                  has_smooth_scales=True)
    assert plain.compulsory_read_bytes == 512
    assert smooth.compulsory_read_bytes == 520


def _random_expr(depth: int, rng: random.Random):
    if depth <= 0:
        return Const(rng.randint(1, 9))
    choice = rng.randrange(6)
    if choice == 0:
        return Neg(_random_expr(depth - 1, rng))
    if choice == 1:
        return Call("min", (_random_expr(depth - 1, rng),
                            _random_expr(depth - 1, rng)))
    if choice == 2:
        return Call("align_up", (_random_expr(depth - 1, rng),
                                 Const(rng.choice([1, 2, 4, 8]))))
    if choice == 3:
        return BinOp("//", _random_expr(depth - 1, rng),
                     Const(rng.randint(1, 5)))
    if choice == 4:
        return Call("max", (_random_expr(depth - 1, rng),
                            _random_expr(depth - 1, rng)))
    return BinOp(rng.choice(["+", "-", "*"]),
                 _random_expr(depth - 1, rng),
                 _random_expr(depth - 1, rng))


def test_r2_12_ast_rendering_is_semantics_preserving():
    expression = Const(2) * (Const(3) // Const(2))
    assert expression.render() == "2 * (3 // 2)"
    assert evaluate_formula_expr(expression.render(), {}) == expression.value({})
    quotient = Const(7) / Const(2)
    assert evaluate_formula_expr(quotient.render(), {}) == quotient.value({})
    assert quotient.value({}) == 3.5
    rng = random.Random(23)
    for _ in range(250):
        tree = _random_expr(4, rng)
        rendered = tree.render()
        assert evaluate_formula_expr(rendered, {}) == tree.value({}), rendered


def test_r2_12_frozen_bindings_reject_post_construction_mutation():
    frozen = card("grouped_matmul", tokens=2, hidden=16, inter=8,
                  experts_total=2, experts_local=2, topk=1,
                  group_list=[1, 1])
    with pytest.raises(TypeError):
        frozen.bindings["group_counts"][0] = 99
    assert isinstance(frozen.as_dict()["bindings"]["group_counts"], list)


def test_r2_13_single_child_composite_preserves_measured_diagnostics():
    leaf = evaluate_operator("matmul", dict(M=32, N=128, K=128),
                             measured_us=10)
    wrapped = evaluate_operator("composite_chain", dict(
        components=[dict(operator="matmul",
                         params=dict(M=32, N=128, K=128))]), measured_us=10)
    assert wrapped.t_floor_us == leaf.t_floor_us
    assert wrapped.sol_floor_pct == leaf.sol_floor_pct
    assert wrapped.ref_ratio == leaf.ref_ratio
    assert wrapped.structural_gap_us == leaf.structural_gap_us
    assert wrapped.impl_headroom_us == leaf.impl_headroom_us
    assert wrapped.sol_floor_pct == 40.0


def test_r2_14_fixture_has_all_428_operator_points_and_five_blocks():
    golden = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert golden["point_count"] == 428
    assert len(golden["points"]) == 428
    assert len(golden["block_points"]) == 5
    assert golden["counts"]["kernel"] == 112
    assert golden["kernel_rows"]["unmodeled"] == 28
    assert A5.vector_ops_per_s == 6.7584e12
