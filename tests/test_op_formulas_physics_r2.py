"""Physics counterexample suite for attention, linear attention, MoE and fabric.

[Role]
  Encode every Round-1 mathematical counterexample at its root cause: exact
  per-sequence attention pairs and causal geometry (F03), matrix-state and
  compact-record physics for linear attention (F05), the LightningIndexer /
  SparseFlashMLA split (F06), certified-minimum GroupedMatmul routing (F07), and
  topology-qualified collectives/MC2 (F10).

[Invariants]
  * Batch totals are never cross-multiplied; causal decode sees the whole cache.
  * A certified floor uses guaranteed-minimum routing, never an expectation.
  * ``world_size == 1``/``ep == 1`` never charges inter-rank wire bytes.
  * A2/A3 and RoCE never report an ``a5_*_measured`` fit.

[Timeouts & Locks]
  Pure arithmetic; each test evaluates a handful of operators.

[Side-Effect Policy]
  No I/O and no writes.
"""

from __future__ import annotations

import pytest

from mindie_sim.op_formulas import FormulaValidationError, evaluate_operator


def test_dense_attention_sums_per_sequence_pairs_not_batch_products():
    evaluation = evaluate_operator(
        "flash_attention",
        dict(q_len=1024, kv_len=1024, hq=32, hkv=8, head_dim=128, batch=8,
             phase="prefill"))
    card = evaluation.formula_card
    assert card.bindings["attended_pairs"] == 8 * 1024 * 1024
    assert card.alg_flops == 137_438_953_472
    assert card.alg_flops_expr.count("attended_pairs") == 1
    assert evaluation.latency.cube_floor_us == pytest.approx(
        137_438_953_472 / 432.5376e12 * 1e6, rel=1e-9)


def test_causal_decode_sees_the_entire_cache():
    evaluation = evaluate_operator(
        "flash_attention",
        dict(q_len=1, kv_len=4096, hq=32, hkv=4, head_dim=128, causal=True))
    card = evaluation.formula_card
    assert card.bindings["attended_pairs"] == 4096
    assert card.alg_flops == 67_108_864
    assert card.bindings["causal_offset"] == 4095


def test_square_causal_prefill_uses_the_inclusive_triangle():
    evaluation = evaluate_operator(
        "flash_attention",
        dict(q_len=1024, kv_len=1024, hq=8, hkv=2, head_dim=64, causal=True,
             phase="prefill"))
    card = evaluation.formula_card
    assert card.bindings["attended_pairs"] == 1024 * 1025 // 2
    assert card.bindings["active_causal_tiles"] == 288
    assert card.bindings["tiled_pairs"] == 288 * 16 * 128
    assert card.cube_flops_tiled == 2 * 8 * 36 * 128 * 128 * (64 + 64)


def test_chunked_and_overlong_causal_geometry():
    chunked = evaluate_operator(
        "flash_attention",
        dict(q_len=128, kv_len=1024, hq=8, hkv=8, head_dim=64, causal=True))
    assert chunked.formula_card.bindings["attended_pairs"] == \
        128 * (1024 - 128) + 128 * 129 // 2
    overlong = evaluate_operator(
        "flash_attention",
        dict(q_len=2048, kv_len=1024, hq=8, hkv=8, head_dim=64, causal=True,
             causal_offset=0))
    assert overlong.formula_card.bindings["attended_pairs"] == \
        (1023 * 1024) // 2 + (2048 - 1023) * 1024


def test_independent_qk_and_v_head_dims():
    evaluation = evaluate_operator(
        "flash_attention",
        dict(q_len=16, kv_len=16, hq=8, hkv=8, head_dim=64, head_dim_v=32))
    card = evaluation.formula_card
    pairs = 16 * 16
    assert card.cube_macs == pairs * 8 * (64 + 32)
    assert card.alg_flops == 2 * pairs * 8 * (64 + 32)


def test_mask_bytes_are_charged_only_for_a_declared_mask():
    without = evaluate_operator(
        "flash_attention",
        dict(q_len=16, kv_len=16, hq=4, hkv=4, head_dim=64, causal=True))
    with_mask = evaluate_operator(
        "flash_attention",
        dict(q_len=16, kv_len=16, hq=4, hkv=4, head_dim=64, causal=True,
             has_attn_mask=True))
    assert without.formula_card.bindings["mask_bytes"] == 0
    assert with_mask.formula_card.bindings["mask_bytes"] == 16 * 16
    assert with_mask.formula_card.compulsory_read_bytes > \
        without.formula_card.compulsory_read_bytes


def test_attention_sequence_lengths_are_validated():
    with pytest.raises(FormulaValidationError):
        evaluate_operator("flash_attention",
                          dict(q_len=8, kv_len=16, hq=4, hkv=4, head_dim=64,
                               actual_seq_lens_q=[100]))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("flash_attention",
                          dict(q_len=8, kv_len=16, hq=4, hkv=4, head_dim=64,
                               actual_seq_lens_q=[-1]))
    quiet = evaluate_operator(
        "flash_attention",
        dict(q_len=8, kv_len=16, hq=4, hkv=4, head_dim=64, batch=2,
             actual_seq_lens_q=[4, 8], actual_seq_lens_kv=[16, 16]))
    assert quiet.formula_card.bindings["attended_pairs"] == 4 * 16 + 8 * 16


def test_direct_sequence_lists_reject_strings_and_bools():
    for bad in ("12", [True], [1.5], ["12"]):
        with pytest.raises(FormulaValidationError):
            evaluate_operator("flash_attention",
                              dict(q_len=8, kv_len=16, hq=4, hkv=4,
                                   head_dim=64, actual_seq_lens_q=bad))


def test_recover_ssm_matrix_state_and_compact_record():
    verify = evaluate_operator("kda_recover_ssm_verify",
                               dict(tokens=1, heads=16, head_dim=128))
    commit = evaluate_operator("kda_recover_ssm_commit",
                               dict(tokens=1, heads=16, head_dim=128))
    for evaluation in (verify, commit):
        card = evaluation.formula_card
        assert card.bindings["state_bytes_per_seq"] == 1_048_576
        assert card.bindings["compact_record_bytes"] == 24_576
    card = verify.formula_card
    assert card.compulsory_read_bytes == \
        card.bindings["state_bytes_per_seq"] + 16 * (2 * 128 + 128) * 2
    assert verify.formula_card.read_bytes_compulsory >= 1_048_576
    assert verify.formula_card.write_bytes_compulsory == 24_576 + 16 * 128 * 2
    assert commit.formula_card.write_bytes_compulsory == 1_048_576
    assert commit.formula_card.read_bytes_compulsory >= \
        1_048_576 + 24_576


def test_recurrent_attention_batch_state_and_spec_slots():
    decode = evaluate_operator("recurrent_kda", dict(tokens=8, heads=16,
                                                     head_dim=128))
    card = decode.formula_card
    assert card.bindings["batch"] == 8
    assert card.compulsory_read_bytes >= 8_388_608
    assert card.compulsory_write_bytes >= 8_388_608
    spec = evaluate_operator(
        "recurrent_kda", dict(tokens=8, heads=16, head_dim=128, spec_slots=4,
                              write_per_slot_states=True))
    assert spec.formula_card.compulsory_write_bytes >= 4 * 8_388_608
    no_slot = evaluate_operator(
        "recurrent_kda", dict(tokens=8, heads=16, head_dim=128, spec_slots=4))
    assert no_slot.formula_card.compulsory_write_bytes < \
        spec.formula_card.compulsory_write_bytes


def test_recurrent_independent_state_dims():
    square = evaluate_operator("recurrent_kda", dict(tokens=2, heads=4,
                                                     head_dim=64))
    rect = evaluate_operator("recurrent_kda", dict(tokens=2, heads=4,
                                                   head_dim_k=64,
                                                   head_dim_v=32))
    assert square.formula_card.alg_flops > rect.formula_card.alg_flops
    assert rect.formula_card.bindings["head_dim_v"] == 32


def test_chunk_attention_charges_sequence_states():
    evaluation = evaluate_operator("chunk_kda", dict(tokens=512, heads=16,
                                                     head_dim=128,
                                                     batch=4))
    assert evaluation.formula_card.read_bytes_compulsory >= 4 * 16 * 128 * 128 * 4
    assert evaluation.formula_card.write_bytes_compulsory >= 4 * 16 * 128 * 128 * 4


def test_lightning_indexer_is_not_sparse_flash_mla():
    indexer = evaluate_operator("lightning_indexer",
                                dict(tokens=32, heads=16, index_dim=128,
                                     kv_len=4096, topk=512))
    sparse = evaluate_operator("sparse_flash_mla",
                               dict(tokens=32, heads=16, head_dim=128,
                                    kv_len=4096, topk=512))
    assert indexer.family == "lightning_indexer"
    assert sparse.family == "sparse_flash_mla"
    assert indexer.formula_card.write_bytes_compulsory == 32 * 16 * 512 * 4
    assert sparse.formula_card.write_bytes_compulsory == 32 * 16 * 128 * 2
    assert indexer.formula_card.bindings["index_dim"] == 128
    assert sparse.formula_card.cube_macs != indexer.formula_card.cube_macs
    assert indexer.formula_card.compulsory_read_bytes != \
        sparse.formula_card.compulsory_read_bytes


def test_sparse_compulsory_kv_is_bounded_by_unique_visible_tokens():
    evaluation = evaluate_operator("sparse_flash_mla",
                                   dict(tokens=32, heads=16, head_dim=128,
                                        kv_len=4096, topk=512))
    card = evaluation.formula_card
    assert card.bindings["unique_kv_tokens"] == 32 * 512
    kv_bytes = card.bindings["unique_kv_tokens"] * 2 * 128 * 2
    assert card.compulsory_read_bytes >= kv_bytes
    assert card.compulsory_read_bytes <= (
        kv_bytes + 32 * 16 * 128 * 2 + 32 * 16 * 512 * 4)
    assert card.compulsory_read_bytes < 32 * 4096 * 2 * 128 * 2
    tight = evaluate_operator("sparse_flash_mla",
                              dict(tokens=1, heads=16, head_dim=128,
                                   kv_len=64, topk=512))
    assert tight.formula_card.bindings["unique_kv_tokens"] == 64


def test_indexer_pairs_respect_causal_offsets():
    dense = evaluate_operator("lightning_indexer",
                              dict(tokens=128, heads=8, index_dim=64,
                                   kv_len=1024, topk=64, q_lens=[128],
                                   kv_lens=[1024]))
    causal = evaluate_operator("lightning_indexer",
                               dict(tokens=128, heads=8, index_dim=64,
                                    kv_len=1024, topk=64, causal=True,
                                    q_lens=[128], kv_lens=[1024]))
    assert causal.formula_card.bindings["attended_pairs"] < \
        dense.formula_card.bindings["attended_pairs"]
    assert causal.formula_card.bindings["attended_pairs"] == \
        128 * (1024 - 128) + 128 * 129 // 2


def test_grouped_matmul_skew_floor_is_certified_minimum():
    params = dict(tokens=64, hidden=7168, inter=3072, experts_total=64,
                  experts_local=64, topk=1, ep=1, mode="up_gate")
    evaluation = evaluate_operator("grouped_matmul", params)
    card = evaluation.formula_card
    assert card.bindings["min_active_experts"] == 1
    assert card.compulsory_gm_bytes == 89_784_320
    assert evaluation.t_floor_us == pytest.approx(22.44608, rel=1e-9)
    skewed = evaluate_operator(
        "grouped_matmul", dict(**params, group_list=[64] + [0] * 63,
                               group_list_type=1))
    assert skewed.formula_card.bindings["E_active"] == 1
    assert skewed.t_floor_us == pytest.approx(22.44608, rel=1e-9)


def test_grouped_matmul_min_active_is_a_real_lower_bound():
    params = dict(tokens=64, hidden=1024, inter=512, experts_total=64,
                  experts_local=64, topk=4, ep=1, mode="up_gate")
    evaluation = evaluate_operator("grouped_matmul", params)
    assert evaluation.formula_card.bindings["min_active_experts"] == 4
    assert evaluation.formula_card.bindings["E_active_expected"] > 4


def test_grouped_matmul_histogram_encodings_and_validation():
    base = dict(tokens=32, hidden=1024, inter=512, experts_total=8,
                experts_local=8, topk=2, ep=1, mode="up_gate")
    counts = [8] * 8
    as_counts = evaluate_operator("grouped_matmul",
                                  dict(base, group_list=counts,
                                       group_list_type=1))
    cumulative = evaluate_operator(
        "grouped_matmul",
        dict(base, group_list=[8, 16, 24, 32, 40, 48, 56, 64],
             group_list_type=0))
    assert as_counts.formula_card.bindings["rows"] == 64
    assert cumulative.formula_card.bindings["rows"] == 64
    assert as_counts.formula_card.compulsory_gm_bytes == \
        cumulative.formula_card.compulsory_gm_bytes
    for bad in ([8] * 7, [8, 0, 0, 0, 0, 0, 0, 8000],
                [10, 8, 6, 4, 2, 0, 0, 0]):
        with pytest.raises(FormulaValidationError):
            evaluate_operator("grouped_matmul",
                              dict(base, group_list=bad,
                                   group_list_type=1 if bad[0] == 8 else 0))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("grouped_matmul",
                          dict(base, group_list=[8] * 8, group_list_type=2))
    with pytest.raises(FormulaValidationError):
        evaluate_operator("grouped_matmul", dict(base, topk=9))


def test_grouped_matmul_ep_scope_matches_mc2():
    grouped = evaluate_operator("grouped_matmul",
                                dict(tokens=32, hidden=1024, inter=512,
                                     experts_total=64, experts_local=8,
                                     topk=8, ep=8, routed_rows=256,
                                     mode="up_gate"))
    mc2 = evaluate_operator("moe_distribute_dispatch",
                            dict(tokens=32, hidden=1024, experts_total=64,
                                 experts_local=8, topk=8, ep=8))
    assert grouped.formula_card.bindings["rows"] == 256
    assert mc2.formula_card.bindings["routed_rows"] == 256
    unknown = evaluate_operator("grouped_matmul",
                                dict(tokens=32, hidden=1024, inter=512,
                                     experts_total=64, experts_local=8,
                                     topk=8, ep=8, mode="up_gate"))
    assert unknown.formula_card.bindings["min_active_experts"] == 0


def test_collective_wire_factors_and_world_size_one():
    for size in (4096, 1024 * 1024, 16 * 1024 * 1024):
        reduce_all = evaluate_operator("hccl_all_reduce",
                                       dict(size_bytes=size, world_size=8))
        gather = evaluate_operator("hccl_all_gather",
                                   dict(size_bytes=size, world_size=8))
        scatter = evaluate_operator("hccl_reduce_scatter",
                                    dict(size_bytes=size, world_size=8))
        assert reduce_all.formula_card.comm_bytes == round(2 * 7 / 8 * size)
        assert gather.formula_card.comm_bytes == round(7 / 8 * size)
        assert scatter.formula_card.comm_bytes == round(7 / 8 * size)
    for name in ("hccl_all_reduce", "hccl_all_gather",
                 "hccl_reduce_scatter", "hccl_all_to_all", "hccl_broadcast"):
        single = evaluate_operator(name, dict(size_bytes=1048576,
                                              world_size=1))
        assert single.formula_card.comm_bytes == 0
        assert single.formula_card.comm_ref_bytes == 0
        assert single.latency.comm_floor_us == 0.0


def test_all_to_all_v_split_vectors_and_hd_algorithm():
    split = evaluate_operator(
        "hccl_all_to_all", dict(size_bytes=4096, world_size=4,
                                send_counts=[1024, 1024, 1024, 1024],
                                recv_counts=[1024, 1024, 1024, 1024],
                                self_rank=1))
    assert split.formula_card.comm_bytes == 3 * 1024 * 2
    with pytest.raises(FormulaValidationError):
        evaluate_operator("hccl_all_to_all",
                          dict(size_bytes=4096, world_size=4,
                               send_counts=[1024] * 3,
                               recv_counts=[1024] * 4))
    hd = evaluate_operator("hccl_all_reduce",
                           dict(size_bytes=4096, world_size=8, algorithm="hd"))
    ring = evaluate_operator("hccl_all_reduce",
                             dict(size_bytes=4096, world_size=8))
    assert hd.formula_card.bindings["alpha_steps"] < \
        ring.formula_card.bindings["alpha_steps"]
    with pytest.raises(FormulaValidationError):
        evaluate_operator("hccl_all_reduce",
                          dict(size_bytes=4096, world_size=6, algorithm="hd"))


def test_mc2_locality_and_ep_one_zero_wire():
    local = evaluate_operator("moe_distribute_dispatch",
                              dict(tokens=8, hidden=1024, experts_total=64,
                                   experts_local=8, topk=4, ep=2))
    assert local.formula_card.comm_bytes == 0
    assert local.formula_card.comm_ref_bytes > 0
    single = evaluate_operator("moe_distribute_dispatch",
                               dict(tokens=32, hidden=1024, experts_total=64,
                                    experts_local=64, topk=8, ep=1))
    assert single.formula_card.comm_bytes == 0
    assert single.formula_card.comm_ref_bytes == 0
    exact = evaluate_operator("moe_distribute_combine",
                              dict(tokens=32, hidden=1024, experts_total=64,
                                   experts_local=8, topk=8, ep=8,
                                   remote_routed_rows=128))
    assert exact.formula_card.comm_bytes == 128 * 1024 * 2
    with pytest.raises(FormulaValidationError):
        evaluate_operator("moe_distribute_combine",
                          dict(tokens=32, hidden=1024, experts_total=64,
                               experts_local=8, topk=8, ep=8,
                               remote_routed_rows=9999))


def test_mc2_fit_domain_is_qualified_and_sku_gated():
    in_domain = evaluate_operator("moe_distribute_dispatch",
                                  dict(tokens=32, hidden=7168,
                                       experts_total=64, experts_local=8,
                                       topk=8, ep=8, skew=1.0))
    assert in_domain.formula_card.bindings["fit_source"] == "a5_mc2_measured"
    assert in_domain.formula_card.bindings["fit_domain_status"] == \
        "in_calibrated_ref_domain"
    narrow = evaluate_operator("moe_distribute_dispatch",
                               dict(tokens=32, hidden=1024, experts_total=64,
                                    experts_local=8, topk=8, ep=8))
    assert "fit_source" not in narrow.formula_card.bindings
    assert narrow.formula_card.bindings["fit_domain_status"] == \
        "outside_captured_workload_geometry"
    wide_experts = evaluate_operator(
        "moe_distribute_dispatch",
        dict(tokens=32, hidden=7168, experts_total=256, experts_local=8,
             topk=8, ep=8))
    assert "fit_source" not in wide_experts.formula_card.bindings
    assert wide_experts.formula_card.bindings["fit_domain_status"] == \
        "outside_captured_workload_geometry"
    skewed = evaluate_operator("moe_distribute_dispatch",
                               dict(tokens=32, hidden=7168, experts_total=64,
                                    experts_local=8, topk=8, ep=8, skew=2.5))
    assert "fit_source" not in skewed.formula_card.bindings
    assert skewed.formula_card.bindings["fit_domain_status"] == \
        "outside_balanced_decode_fit"
    large = evaluate_operator("moe_distribute_dispatch",
                              dict(tokens=512, hidden=7168,
                                   experts_total=64, experts_local=8, topk=8,
                                   ep=8))
    assert "fit_source" not in large.formula_card.bindings
    a2 = evaluate_operator("moe_distribute_dispatch",
                           dict(tokens=32, hidden=7168, experts_total=64,
                                experts_local=8, topk=8, ep=8), sku="a2")
    assert "fit_source" not in a2.formula_card.bindings
    assert a2.formula_card.bindings["fit_domain_status"] != \
        "in_calibrated_ref_domain"


def test_fabric_fit_is_a5_ub_only():
    a5 = evaluate_operator("hccl_all_reduce",
                           dict(size_bytes=4096, world_size=8), sku="a5")
    assert a5.formula_card.bindings["fit_source"] == "a5_fabric_measured"
    assert a5.formula_card.bindings["transport"] == "a5_ub_urma_intra_node"
    for sku in ("a2", "a3"):
        other = evaluate_operator("hccl_all_reduce",
                                  dict(size_bytes=4096, world_size=8), sku=sku)
        assert "fit_source" not in other.formula_card.bindings
        assert other.formula_card.bindings["fit_domain_status"] == \
            "analytical_alpha_beta"
    roce = evaluate_operator("hccl_all_reduce",
                             dict(size_bytes=4096, world_size=8,
                                  transport="roce"), sku="a5")
    assert "fit_source" not in roce.formula_card.bindings
    assert roce.formula_card.bindings["transport"] == "roce_inter_node"
    assert roce.formula_card.bindings["link_bps"] == 50.0e9
    superpod = evaluate_operator("hccl_all_reduce",
                                 dict(size_bytes=268435456, world_size=16))
    assert superpod.formula_card.bindings["transport"] == "a5_ub_urma_superpod"
    assert superpod.formula_card.bindings["link_bps"] == 512.0e9
