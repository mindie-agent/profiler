"""Round-4 closure matrix for R4-01..R4-13.

[Role]
  Independently pin the reachable-KV attention contract, exact causal sparse
  unions, physical broadcast ownership, native quantized scale descriptors,
  norm statistics/residual slots, two-input nonlinear arithmetic, linear-state
  validation and beta/gate precision, the four-projection MlaProlog ledger,
  global grouped-MoE arrivals, strict collective ownership, native attention
  layout/head precedence, lossless bounded diagnostics and timeout propagation.

[Invariants]
  * Every rejection asserts a stable class/code; every acceptance asserts an
    exact byte, operation or binding value.
  * Inaccessible cache capacity never enters a certified floor or scan count.
  * Declared buffers, not inferred placeholders, determine compulsory traffic.
  * Golden expectations are read from the authentic regenerated fixture.

[Timeouts & Locks]
  Pure in-memory evaluation; the timeout tests patch Path methods only.

[Side-Effect Policy]
  No fixture writes, network, device work or global mutation.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from mindie_profiler.op_abi_bridge import AbiError, infer_request
from mindie_profiler.op_formula_annotator import (
    annotate_profile_formulas, annotate_row, call_mcp_tool, load_rows, main,
)
from mindie_sim.op_formulas import FormulaValidationError, evaluate_operator

ROOT = Path(__file__).parents[1]
A5 = "Ascend950DT_9581"


def raw(name, shapes, outputs=None, dtypes=None, out_dtypes=None, **extra):
    def shape(item):
        return ",".join(map(str, item)) if isinstance(item, (list, tuple)) else item
    return {
        "name": name, "type": name,
        "input_shapes": ";".join(shape(item) for item in shapes),
        "input_data_types": ";".join(dtypes or ["DT_BF16"] * len(shapes)),
        "input_formats": ";".join(["ND"] * len(shapes)),
        "output_shapes": ";".join(shape(item) for item in (outputs or [])),
        "output_data_types": ";".join(
            out_dtypes or ["DT_BF16"] * len(outputs or [])),
        "output_formats": ";".join(["ND"] * len(outputs or [])),
        **extra,
    }


def card(operator, **params):
    return evaluate_operator(operator, params, sku=A5).formula_card


def annotated(row):
    return annotate_row(row, sku=A5, measured_us=1e12, include_card=True)


# --------------------------------------------------------------------- R4-01
def test_r4_01_dense_attention_only_charges_reachable_kv():
    for q_len, offset in ((1, 0), (8, 7), (32, 0)):
        big = evaluate_operator(
            "flash_attention",
            dict(q_len=q_len, kv_len=1048576, hq=1, hkv=1, head_dim=128,
                 head_dim_v=64, causal=True, causal_offset=offset))
        small = evaluate_operator(
            "flash_attention",
            dict(q_len=q_len, kv_len=q_len + offset, hq=1, hkv=1,
                 head_dim=128, head_dim_v=64, causal=True,
                 causal_offset=offset))
        expected = 2 * (q_len * 192 + (q_len + offset) * 192)
        assert big.formula_card.compulsory_gm_bytes == expected
        assert big.t_floor_us == small.t_floor_us
        assert big.formula_card.bindings["visible_kv_rows"] == q_len + offset


def test_r4_01_empty_query_sequence_reads_no_cache():
    card_i = card("flash_attention", q_len=1, kv_len=1048576, batch=2, hq=1,
                  hkv=1, head_dim=16,
                  actual_seq_lens_q=[1, 0],
                  actual_seq_lens_kv=[1, 1048576])
    assert card_i.compulsory_gm_bytes == 128
    assert card_i.bindings["visible_kv_rows"] == 1


def test_r4_01_indexer_scans_only_visible_positions():
    card_i = card("lightning_indexer", tokens=32, index_heads=1, index_dim=16,
                  kv_len=1048576, topk=8, q_lens=[32],
                  kv_lens=[1048576], causal=True, causal_offset=0)
    assert card_i.compulsory_read_bytes == 2048
    assert card_i.bindings["selection_ops"] == 528
    assert card_i.bindings["visible_kv_rows"] == 32


# --------------------------------------------------------------------- R4-02
def test_r4_02_sparse_union_is_exactly_the_reachable_union():
    for q_len in range(1, 5):
        for kv_len in range(1, 7):
            for topk in range(1, 4):
                for offset in (0, 2):
                    choices = [list(itertools.combinations(
                        range(min(kv_len, offset + pos + 1)),
                        min(topk, kv_len, offset + pos + 1)))
                        for pos in range(q_len)]
                    unions = {len(set().union(*map(set, picks)))
                              for picks in itertools.product(*choices)}
                    params = dict(tokens=q_len, heads=1, head_dim=8,
                                  kv_len=kv_len, topk=topk, q_lens=[q_len],
                                  kv_lens=[kv_len], causal=True,
                                  causal_offset=offset)
                    floor = card("sparse_flash_mla", **params).bindings[
                        "unique_kv_tokens"]
                    assert floor == min(unions)
                    for value in range(kv_len + 1):
                        try:
                            card("sparse_flash_mla", **params,
                                 unique_selected_kv=value)
                            accepted = True
                        except FormulaValidationError:
                            accepted = False
                        assert accepted == (value in unions)


def test_r4_02_native_sparse_keeps_causality_and_rejects_bad_topk():
    row = raw("SparseFlashMla",
              [[32, 1, 128], [4096, 1, 128], [32, 1, 8]],
              [[32, 1, 128]],
              dtypes=["DT_BF16", "DT_BF16", "DT_INT32"],
              topk=8, causal=True, causal_offset=0, actual_seq_lengths=[32])
    result = annotated(row)
    assert result["status"] == "clean"
    assert result["formula_card"]["bindings"]["sparse_pairs"] == 228
    for bad in (0, -1):
        assert annotated(dict(row, topk=bad))["status"] == "invalid_abi"


# --------------------------------------------------------------------- R4-03
@pytest.mark.parametrize("shapes,out,read,write", [
    ([[1, 16, 128], [4, 128, 32]], [[4, 16, 32]], 36864, 4096),
    ([[2, 1, 4, 8], [1, 3, 8, 16]], [[2, 3, 4, 16]], 896, 768),
    ([[4, 16, 128], [128, 32]], [[4, 16, 32]], 24576, 4096),
])
def test_r4_03_broadcast_inputs_keep_physical_batch_bytes(
        shapes, out, read, write):
    result = annotated(raw("BatchMatMul", shapes, out))
    assert result["status"] == "clean"
    assert (result["formula_card"]["compulsory_read_bytes"],
            result["formula_card"]["compulsory_write_bytes"]) == (read, write)


# --------------------------------------------------------------------- R4-04
def test_r4_04_native_quant_scale_shape_dtype_and_actual_bytes():
    base = [[4, 16, 128], [4, 128, 32], [4, 32]]
    for shape in ([4, 31], [4, 32, 2]):
        row = raw("QuantBatchMatmulV3", base[:2] + [shape], [[4, 16, 32]],
                  dtypes=["DT_INT8", "DT_INT8", "DT_FLOAT"])
        assert annotated(row)["status"] == "invalid_abi"
    for dtype, scale_bytes in (("DT_FLOAT", 512), ("DT_BF16", 256)):
        row = raw("QuantBatchMatmulV3", base, [[4, 16, 32]],
                  dtypes=["DT_INT8", "DT_INT8", dtype])
        result = annotated(row)
        assert result["status"] == "clean"
        assert result["formula_card"]["compulsory_read_bytes"] == \
            4 * 16 * 128 + 4 * 128 * 32 + scale_bytes
    scalar = annotated(raw("QuantBatchMatmulV3",
                           base[:2] + [[1]], [[4, 16, 32]],
                           dtypes=["DT_INT8", "DT_INT8", "DT_FLOAT"]))
    assert scalar["formula_card"]["compulsory_read_bytes"] == 24580
    missing = raw("QuantBatchMatmulV3", base[:2], [[4, 16, 32]],
                  dtypes=["DT_INT8", "DT_INT8"])
    assert annotated(missing)["status"] == "invalid_abi"


def test_r4_04_grouped_scale_presence_precision_and_storage():
    missing = raw("GroupedMatmul", [[32, 128], [1, 128, 128]],
                  [[32, 128]], dtypes=["DT_BF16", "DT_INT4"], group_list=[32])
    assert annotated(missing)["status"] == "invalid_abi"
    fp32 = annotated(raw("GroupedMatmul", [[32, 128], [1, 128, 128]],
                         [[32, 128]], dtypes=["DT_BF16", "DT_FLOAT"],
                         group_list=[32]))
    assert fp32["formula_card"]["compulsory_read_bytes"] == \
        32 * 128 * 2 + 128 * 128 * 4
    for dtypes in (["DT_INT32", "DT_INT4"],):
        row = raw("GroupedMatmul", [[32, 128], [1, 128, 128]],
                  [[32, 128]], dtypes=dtypes, group_list=[32])
        assert annotated(row)["status"] == "invalid_abi"
    direct = dict(tokens=32, hidden=128, inter=64, experts_total=1,
                  experts_local=1, topk=1, group_list=[32],
                  dtype="bf16", weight_dtype="bf16", quant="w8a8")
    with pytest.raises(FormulaValidationError):
        card("grouped_matmul", **direct)


# --------------------------------------------------------------------- R4-05
def test_r4_05_norm_gamma_output_and_residual_contract():
    for shape in ([7], [2, 7], ["bad"]):
        assert annotated(raw("RmsNorm", [[2, 8], shape],
                             [[2, 8]]))["status"] == "invalid_abi"
    assert annotated(raw("RmsNorm", [[2, 8], [8]],
                         [[2, 9]]))["status"] == "invalid_abi"
    assert annotated(raw("RmsNorm", [[2, 8], [8]], [[2, 8]],
                         dtypes=["DT_BF16", "DT_INT32"]))["status"] == \
        "invalid_abi"
    fp32_gamma = annotated(raw("RmsNorm", [[2, 8], [8]], [[2, 8]],
                               dtypes=["DT_BF16", "DT_FLOAT"]))
    assert fp32_gamma["formula_card"]["compulsory_read_bytes"] == 64
    fp32_out = annotated(raw("RmsNorm", [[2, 8], [8]], [[2, 8]],
                             out_dtypes=["DT_FLOAT"]))
    assert fp32_out["formula_card"]["compulsory_write_bytes"] == 64
    assert annotated(raw("AddRmsNorm", [[2, 8], "", [8]],
                         [[2, 8]]))["status"] == "invalid_abi"
    assert annotated(raw("AddRmsNorm", [[2, 8], [3, 8], [8]],
                         [[2, 8]]))["status"] == "invalid_abi"


def test_r4_05_captured_rmsnorm_rows_include_rstd_writes():
    fixture = json.loads((ROOT / "tests/fixtures/a5_op_goldens.json").read_text())
    rms = [point for point in fixture["points"]
           if point["operator"] == "rms_norm"
           and point["id"].startswith("kernel_")]
    assert len(rms) == 14
    for point in rms:
        assert point["params"]["rstd_elems"] == point["params"]["rows"]
        assert point["params"]["rstd_dtype"] == "fp32"
    target = next(point for point in rms
                  if point["id"] == "kernel_r102_rms_norm")
    assert card("rms_norm", **target["params"]).compulsory_write_bytes == 458880


# --------------------------------------------------------------------- R4-06
@pytest.mark.parametrize("operator,ops", [
    ("Mul", 3), ("SiluAndMul", 15), ("SwiGlu", 15), ("GeGlu", 24),
])
def test_r4_06_two_input_activation_keeps_nonlinear_math(operator, ops):
    result = annotated(raw(operator, [[1, 3], [1, 3]], [[1, 3]]))
    assert result["status"] == "clean"
    assert result["formula_card"]["vector_ops"] == ops
    assert (result["formula_card"]["compulsory_read_bytes"],
            result["formula_card"]["granule_read_bytes"]) == (12, 256)
    assert annotated(raw(operator, [[2, 3], [2, 3]],
                         [[2, 4]]))["status"] == "invalid_abi"
    assert annotated(raw(operator, [[1, 3], "bad"],
                         [[1, 3]]))["status"] == "invalid_abi"


# --------------------------------------------------------------------- R4-07
def test_r4_07_chunk_state_and_rate_descriptor_contract():
    base_in = [[5, 2, 16], [5, 2, 16], [5, 2, 8], [5, 2], [5, 2, 16],
               [1, 2, 16, 8]]
    base_out = [[5, 2, 8], [1, 2, 16, 8]]
    dtypes = ["DT_BF16"] * 5 + ["DT_FLOAT"]
    out_dtypes = ["DT_BF16", "DT_FLOAT"]
    def chunk(inputs=base_in, outputs=base_out, ds=dtypes, os=out_dtypes):
        return annotated(raw("ChunkGatedDeltaRule", inputs, outputs,
                             dtypes=ds, out_dtypes=os,
                             actual_seq_lengths=[5]))
    exact = chunk()
    assert (exact["formula_card"]["compulsory_read_bytes"],
            exact["formula_card"]["compulsory_write_bytes"]) == (2164, 1184)
    scalar = chunk(inputs=[*base_in[:4], [5, 2], base_in[5]])
    assert scalar["formula_card"]["compulsory_read_bytes"] == 1864
    for index, shape in ((5, [1, 2, 16]), (3, [5, 3]),
                         (4, [5, 2, 17]), (5, "bad")):
        broken = [*base_in]
        broken[index] = shape
        assert chunk(inputs=broken)["status"] == "invalid_abi"
    for index in (1, 2):
        broken = list(dtypes)
        broken[index] = "DT_INT32"
        assert chunk(ds=broken)["status"] == "invalid_abi"
    assert chunk(outputs=["", base_out[1]])["status"] == "invalid_abi"


# --------------------------------------------------------------------- R4-08
def test_r4_08_mla_prolog_complete_four_projection_contract():
    params = dict(tokens=8, hidden=7168, heads=32, head_dim=128,
                  q_lora_rank=1536, kv_lora_rank=512, rope_dim=64,
                  dtype="bf16")
    fused = evaluate_operator("mla_prolog", params)
    c = fused.formula_card
    assert c.alg_flops == 426770432
    assert c.compulsory_read_bytes == 53467200
    assert c.compulsory_write_bytes == 304128
    unfused = evaluate_operator("mla_prolog", dict(params, fused=False))
    assert (unfused.formula_card.compulsory_gm_bytes
            - c.compulsory_gm_bytes) == 2 * 8 * 1536 * 2


# --------------------------------------------------------------------- R4-09
def test_r4_09_grouped_routing_uses_global_source_population():
    params = dict(tokens=4, hidden=16, inter=8, experts_total=4,
                  experts_local=2, topk=1, ep=2)
    assert card("grouped_matmul", **params,
                group_list=[4, 4]).bindings["floor_routed_rows"] == 8
    assert card("grouped_matmul", **params,
                routed_rows=8).bindings["floor_routed_rows"] == 8
    for bad in (dict(group_list=[8, 8]), dict(routed_rows=17)):
        with pytest.raises(FormulaValidationError):
            card("grouped_matmul", **params, **bad)


# --------------------------------------------------------------------- R4-10
def test_r4_10_collective_local_buffer_ownership():
    for operator in ("HcclAllGather", "HcclReduceScatter"):
        result = annotated(raw(operator, [[1024]], [[1024]], world_size=4))
        assert result["status"] == "invalid_abi"
    gather = annotated(raw("HcclAllGather", [[1024]], [[4096]],
                           world_size=4))
    assert (gather["formula_card"]["compulsory_read_bytes"],
            gather["formula_card"]["compulsory_write_bytes"]) == (2048, 8192)
    scatter = annotated(raw("HcclReduceScatter", [[4096]], [[1024]],
                            world_size=4))
    assert (scatter["formula_card"]["compulsory_read_bytes"],
            scatter["formula_card"]["compulsory_write_bytes"]) == (8192, 2048)
    asym = annotated(raw("HcclAlltoAllV", [[12]], [[15]], world_size=4,
                         send_counts=[3] * 4, recv_counts=[3, 4, 4, 4]))
    assert (asym["formula_card"]["compulsory_read_bytes"],
            asym["formula_card"]["compulsory_write_bytes"]) == (24, 30)
    broken = raw("HcclAlltoAllV", [[12]], [[15]], world_size=4,
                 send_counts=[3, 3, 3, 2], recv_counts=[3, 4, 4, 4])
    assert annotated(broken)["status"] == "invalid_abi"


# --------------------------------------------------------------------- R4-11
def test_r4_11_semantic_layout_precedes_physical_nd():
    row = raw("FusedInferAttentionScore",
              [[2, 8, 128, 64], [2, 2, 256, 64], [2, 2, 256, 32]],
              [[2, 8, 128, 32]], input_layout="BNSD")
    assert annotated(row)["status"] == "clean"
    gqa = raw("FusedInferAttentionScore",
              [[2, 128, 512], [2, 256, 128], [2, 256, 64]],
              [[2, 128, 256]], head_num=8, num_key_value_heads=2)
    gqa["input_formats"] = "BSH;BSH;BSH"
    gqa["output_formats"] = "BSH"
    assert annotated(gqa)["status"] == "clean"
    contradiction = raw("FusedInferAttentionScore",
                        [[2, 8, 128, 64], [2, 2, 256, 64], [2, 2, 256, 32]],
                        [[2, 8, 128, 32]], input_layout="BSND")
    contradiction["input_formats"] = "BNSD;BNSD;BNSD"
    assert annotated(contradiction)["status"] == "invalid_abi"


# --------------------------------------------------------------------- R4-12
def test_r4_12_modest_diagnostic_batch_is_lossless_and_receipted():
    base = dict(M=2, N=2, K=2)
    rows = [
        dict(operator="matmul", params=base, measured_us=.01,
             flags={"wrong_sku_spec": True,
                    "unfiltered_padding_shape_bound": True,
                    "async_overlap_shadowed": True}),
        dict(operator="matmul", params=dict(base, M=-1)),
        raw("MatMul", [[2, 3], [4, 5]], [[2, 5]]),
        raw("UnknownKernel", [[1]], [[1]]),
        raw("FusedInferAttentionScore",
            [[2, 128, 8, 64], [2, 256, 2, 64], [2, 256, 3, 32]],
            [[2, 128, 8, 32]]),
        raw("FusedInferAttentionScore",
            [[2, 128, 8, 64], [2, 256, 2, 64], [2, 256, 2, 32]], []),
    ]
    full = annotate_profile_formulas(rows, sku=A5)
    assert len(full["error_codes"]) == 8
    body = call_mcp_tool("annotate_profile_formulas", {"rows": rows})
    assert body["error_codes"] == full["error_codes"]
    assert not body.get("codes_truncated")
    assert body["receipt"]["within_budget"] is True
    unknown = call_mcp_tool("unknown", {})
    assert unknown["receipt"]["within_budget"] is True
    assert unknown["receipt"]["token_estimate"] <= 250


# --------------------------------------------------------------------- R4-13
def test_r4_13_timeouts_are_never_converted_to_usage_errors(tmp_path):
    path = tmp_path / "rows.json"
    path.write_text("[]\n")
    with patch.object(Path, "read_text", side_effect=TimeoutError("injected")):
        with pytest.raises(TimeoutError):
            load_rows(path)
    with patch.object(Path, "read_text", side_effect=TimeoutError("injected")):
        with pytest.raises(TimeoutError):
            main(["--operator", "matmul", "--params-file", str(path)])
    with pytest.raises(AbiError):
        infer_request(raw("MatMul", [[2, 3], [3, 4]], [[2, 5]]))


# --------------------------------------------------------------------- hygiene
SCOPED = [
    "mindie_sim/op_formulas/__init__.py", "mindie_sim/op_formulas/errors.py",
    "mindie_sim/op_formulas/expr_ast.py", "mindie_sim/op_formulas/primitives.py",
    "mindie_sim/op_formulas/hardware.py", "mindie_sim/op_formulas/work.py",
    "mindie_sim/op_formulas/model.py", "mindie_sim/op_formulas/engine.py",
    "mindie_sim/op_formulas/ops_matmul.py",
    "mindie_sim/op_formulas/ops_attention.py",
    "mindie_sim/op_formulas/ops_linear_attn.py",
    "mindie_sim/op_formulas/ops_vector.py", "mindie_sim/op_formulas/ops_comm.py",
    "mindie_sim/op_formulas/registry.py",
    "mindie_sim/op_formulas/registry_names.py",
    "mindie_sim/op_formulas/ops_quant.py",
    "mindie_profiler/op_abi_slots.py", "mindie_profiler/op_abi_descriptors.py",
    "mindie_profiler/op_abi_geometry.py",
    "mindie_profiler/op_abi_geometry_common.py",
    "mindie_profiler/op_abi_geometry_matrix.py",
    "mindie_profiler/op_abi_geometry_vector.py",
    "mindie_profiler/op_abi_attention.py", "mindie_profiler/op_abi_numeric.py",
    "mindie_profiler/op_abi_padding.py",
    "mindie_profiler/op_abi_padding_rules.py",
    "mindie_profiler/op_abi_bridge.py",
    "mindie_profiler/op_formula_annotator.py",
    "mindie_profiler/op_formula_mcp.py",
    "mindie_profiler/op_mcp_tool_specs.py", "mindie_profiler/token_budget.py",
    "tests/test_op_theoretical_formulas.py",
    "tests/test_op_formulas_physics_r2.py", "tests/test_op_formula_abi.py",
    "tests/test_op_formula_strict_contracts.py",
    "tests/test_op_formula_mc2_r8.py",
    "tests/test_op_theoretical_formulas_a5_goldens.py",
    "tests/test_op_formulas_r2_closure.py",
    "tests/test_op_formulas_r4_closure.py",
    "tests/fixtures/build_a5_op_goldens.py",
]
MARKERS = ("[Role]", "[Invariants]", "[Timeouts & Locks]", "[Side-Effect Policy]")


def _resolve_scoped(name: str) -> Path:
    candidate = ROOT / name
    if candidate.exists():
        return candidate
    import mindie_sim
    return Path(mindie_sim.__file__).resolve().parents[1] / name


def test_r4_scoped_files_stay_below_the_physical_line_cap():
    for name in SCOPED:
        data = _resolve_scoped(name).read_bytes()
        lines = data.splitlines()
        head = b"\n".join(lines[:30]).decode("utf-8")
        assert len(lines) < 650, (name, len(lines))
        assert b"\r" not in data, name
        assert all(marker in head for marker in MARKERS), name


@pytest.mark.parametrize('q,dk,dv,expected', [(32, 128, 64, 24576), (4, 16, 8, 384)])
def test_r5_01_native_offset_zero_is_capacity_invariant(q, dk, dv, expected):
    results = []
    for capacity in (q, 1048576):
        row = raw('FusedInferAttentionScore', [[q, 1, dk], [capacity, 1, dk], [capacity, 1, dv]],
                  [[q, 1, dv]], input_layout='TND', actual_seq_lengths=[q],
                  causal=True, causal_offset=0)
        result = annotate_row(row, include_card=True, launch_mode='eager', steady_l2_warm=False)
        c = result['formula_card']
        assert (c['bindings']['visible_kv_rows'], c['compulsory_gm_bytes']) == (q, expected)
        results.append(result['t_floor_us'])
        for bad in (-1, True, 1.5, 'bad'):
            with pytest.raises(AbiError):
                infer_request(dict(row, causal_offset=bad))
    assert results == [4.0, 4.0]


@pytest.mark.parametrize('op', ['lightning_indexer', 'sparse_flash_mla'])
@pytest.mark.parametrize('causal', [True, False])
def test_r5_02_inactive_sequences_have_zero_work_and_traffic(op, causal):
    p = dict(tokens=3, kv_len=10000, topk=2, causal=causal, causal_offset=0,
             index_heads=1, index_dim=16, heads=1, head_dim=16)
    active = card(op, **p, q_lens=[3], kv_lens=[9])
    mixed = card(op, **p, q_lens=[3, 0], kv_lens=[9, 10000])
    for field in ('alg_flops', 'cube_flops_tiled', 'vector_ops',
                  'compulsory_read_bytes', 'compulsory_write_bytes', 'granule_gm_bytes'):
        assert getattr(active, field) == getattr(mixed, field), field
    if op == 'sparse_flash_mla':
        for union in (0, 1):
            if union:
                with pytest.raises(FormulaValidationError):
                    card(op, **p, q_lens=[3, 0], kv_lens=[9, 10000], unique_selected_kv=[2, union])
            else:
                assert card(op, **p, q_lens=[3, 0], kv_lens=[9, 10000],
                            unique_selected_kv=[2, union]).bindings['unique_kv_tokens'] == 2
    with pytest.raises(FormulaValidationError):
        card(op, **p, q_lens=[0, 0], kv_lens=[9, 10000])


@pytest.mark.parametrize('native,binding,expected', [
    ('LightningIndexer', 'visible_pairs', 9), ('SparseFlashMla', 'sparse_pairs', 8)])
@pytest.mark.parametrize('encoding,ql,kl', [
    ('per_seq', [2, 0, 3], [10, 1000, 20]), ('cumulative', [2, 2, 5], [10, 1010, 1030])])
def test_r5_02_native_equal_adjacent_query_offsets(native, binding, expected, encoding, ql, kl):
    row = raw(native, [[5, 1, 16], [1030, 1, 16], [5, 1, 2]], [[5, 1, 16]],
              dtypes=['DT_BF16', 'DT_BF16', 'DT_INT32'], topk=2, causal=True, causal_offset=0,
              actual_seq_lengths=ql, actual_seq_lengths_kv=kl, actual_seq_lengths_type=encoding)
    assert annotated(row)['formula_card']['bindings'][binding] == expected


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
def test_r5_07_mc2_global_conservation_and_ownership(stage):
    op = 'moe_distribute_' + stage
    p = dict(tokens=4, ep=2, hidden=16, experts_total=4, experts_local=2, use_measured_fit=False)
    for k, low, high in ((1, 0, 8), (3, 8, 16), (4, 16, 16)):
        for rows in range(18):
            if low <= rows <= high:
                c = card(op, **p, topk=k, routed_rows=rows)
                assert c.bindings['routed_rows'] == rows
            else:
                with pytest.raises(FormulaValidationError):
                    card(op, **p, topk=k, routed_rows=rows)
    # R=6 local arrivals, L=3 self routes: dispatch sends 1 and receives 3.
    sent, received = (1, 3) if stage == 'dispatch' else (3, 1)
    owned = dict(topk=1, routed_rows=6, local=3, remote=3, sent=sent, received=received)
    c = card(op, **p, **owned)
    assert (c.bindings['local_rows'], c.comm_bytes) == (3, 96)
    # Empty expert arrivals still require this rank's source routes to travel.
    empty = dict(topk=1, routed_rows=0, local=0, remote=0,
                 sent=4 if stage == 'dispatch' else 0,
                 received=0 if stage == 'dispatch' else 4)
    assert card(op, **p, **empty).comm_bytes == 128
    for field in ('local', 'remote', 'sent', 'received'):
        with pytest.raises(FormulaValidationError):
            card(op, **p, **dict(owned, **{field: owned[field] + 1}))
    for local_experts, rows in ((0, 0), (4, 8)):
        c = card(op, **dict(p, experts_local=local_experts), topk=1, routed_rows=rows)
        assert c.bindings['routed_rows'] == rows


@pytest.mark.parametrize('hkv', [2, 4])
def test_r5_09_sbh_matches_other_attention_layouts(hkv):
    ledgers = []
    for layout, shapes, out in (
        ('SBH', [[3, 2, 32], [7, 2, hkv*8], [7, 2, hkv*4]], [3, 2, 16]),
        ('BSH', [[2, 3, 32], [2, 7, hkv*8], [2, 7, hkv*4]], [2, 3, 16]),
        ('BNSD', [[2, 4, 3, 8], [2, hkv, 7, 8], [2, hkv, 7, 4]], [2, 4, 3, 4]),
        ('BSND', [[2, 3, 4, 8], [2, 7, hkv, 8], [2, 7, hkv, 4]], [2, 3, 4, 4]),
    ):
        row = raw('FusedInferAttentionScore', shapes, [out], input_layout=layout,
                  head_num=4, num_key_value_heads=hkv)
        _, p, _ = infer_request(row)
        assert (p['batch'], p['q_len'], p['kv_len'], p['head_dim'], p['head_dim_v']) == (2, 3, 7, 8, 4)
        c = annotated(row)['formula_card']
        ledgers.append(tuple(c[k] for k in ('alg_flops', 'cube_flops_tiled', 'compulsory_gm_bytes', 'granule_gm_bytes')))
    assert len(set(ledgers)) == 1


def test_r5_10_all_scoped_handlers_rethrow_timeouts_and_keep_module_markers():
    import ast
    assert len(SCOPED) == len(set(SCOPED)) == 40
    for name in SCOPED:
        tree = ast.parse(_resolve_scoped(name).read_text())
        assert all(marker in (ast.get_docstring(tree) or '') for marker in MARKERS), name
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Try, ast.TryStar)):
                continue
            guarded = False
            for handler in node.handlers:
                names = {n.id for n in ast.walk(handler.type) if isinstance(n, ast.Name)} if handler.type else {'bare'}
                if names & {'OSError', 'Exception', 'BaseException', 'bare'}:
                    assert guarded, (name, handler.lineno)
                if isinstance(handler.type, ast.Name) and handler.type.id == 'TimeoutError':
                    guarded = (len(handler.body) == 1 and isinstance(handler.body[0], ast.Raise)
                               and handler.body[0].exc is None)
