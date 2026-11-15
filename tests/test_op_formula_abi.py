"""ABI bridge contracts: layouts, sequence encodings, batching and rejection.

[Role]
  Prove F04: BSND/BNSD/TND layout-qualified shape inference, native sequence
  length spellings and cumulative offsets, fail-closed bounds, AddRmsNorm
  classification, BatchMatMul batch/broadcast handling, contraction validation,
  unknown-dtype rejection and the preserved padded-varlen negative fixture.
  R6/R7 cover packed arity, empty owners and native MC2 storage/ownership.

[Invariants]
  * Shapes are never guessed from anonymous positional tokens.
  * Invalid or ambiguous ABI metadata is reported as ``invalid_abi`` with a
    stable code, never clamped or silently re-modeled.
  * Full-padded operators keep their static storage; varlen layouts may skip
    padding only with valid evidence.
  * Kernel classification preserves residual traffic for AddRmsNorm.

[Timeouts & Locks]
  Pure in-memory parsing and evaluation.

[Side-Effect Policy]
  Read-only golden fixture access; other rows are literals. No writes.
"""

from __future__ import annotations

import pytest

from mindie_profiler.op_abi_bridge import AbiError, infer_request
from mindie_profiler.op_formula_annotator import annotate_row
from mindie_sim.op_formulas import FormulaValidationError, evaluate_operator


def raw_row(name: str, inputs: list[str], dtypes: list[str],
            formats: list[str], outputs: list[str],
            out_dtypes: list[str] | None = None,
            out_formats: list[str] | None = None, **extra) -> dict:
    return {
        "name": name,
        "type": extra.pop("type", name.split("_")[0]),
        "input_shapes": ";".join(inputs),
        "input_data_types": ";".join(dtypes),
        "input_formats": ";".join(formats),
        "output_shapes": ";".join(outputs),
        "output_data_types": ";".join(out_dtypes or ["DT_BF16"] * len(outputs)),
        "output_formats": ";".join(out_formats or ["ND"] * len(outputs)),
        **extra,
    }


def test_bsnd_layout_is_parsed_by_declared_axis():
    row = raw_row("FusedInferAttentionScore",
                  ["2,128,8,64", "2,256,2,64", "2,256,2,64"],
                  ["DT_BF16"] * 3, ["BSND"] * 3, ["2,128,8,64"])
    operator, params, _flags = infer_request(row)
    assert operator == "flash_attention"
    assert params["layout"] == "BSND"
    assert (params["batch"], params["q_len"], params["hq"], params["head_dim"]) \
        == (2, 128, 8, 64)
    assert (params["kv_len"], params["hkv"]) == (256, 2)
    evaluation = evaluate_operator(operator, params)
    card = evaluation.formula_card
    assert card.bindings["total_q"] == 256
    assert card.bindings["total_kv"] == 512
    assert card.compulsory_read_bytes == 524288


def test_bnsd_layout_is_not_mistaken_for_leading_sequence():
    row = raw_row("aclnnFusedInferAttentionScore_BNSD",
                  ["2,8,128,64", "2,2,256,64", "2,2,256,64"],
                  ["DT_BF16"] * 3, ["BNSD"] * 3, ["2,8,128,64"])
    operator, params, _flags = infer_request(row)
    assert params["layout"] == "BNSD"
    assert (params["batch"], params["q_len"], params["hq"]) == (2, 128, 8)
    assert (params["kv_len"], params["hkv"]) == (256, 2)


def test_tnd_cumulative_offsets_become_per_sequence_lengths():
    row = raw_row("aclnnFlashAttentionScore_TND",
                  ["5,8,64", "7,2,64", "7,2,64"],
                  ["DT_BF16"] * 3, ["TND"] * 3, ["5,8,64"],
                  actual_seq_lengths="2,5", actual_seq_lengths_kv="3,7")
    operator, params, _flags = infer_request(row)
    assert params["actual_seq_lens_q"] == [2, 3]
    assert params["actual_seq_lens_kv"] == [3, 4]
    evaluation = evaluate_operator(operator, params)
    assert evaluation.formula_card.bindings["attended_pairs"] == 2 * 3 + 3 * 4
    assert params["padding_skipped"] is False


def test_bsnd_valid_lengths_skip_padding_below_static_storage():
    row = raw_row("FusedInferAttentionScore",
                  ["2,8,8,64", "2,16,2,64", "2,16,2,64"],
                  ["DT_BF16"] * 3, ["BSND"] * 3, ["2,8,8,64"],
                  actual_seq_lengths="2,3", actual_seq_lengths_kv="4,5")
    operator, params, _flags = infer_request(row)
    assert params["actual_seq_lens_q"] == [2, 3]
    assert params["padding_skipped"] is True
    evaluation = evaluate_operator(operator, params)
    assert evaluation.formula_card.bindings["attended_pairs"] == 2 * 4 + 3 * 5
    assert any("padded rows skipped" in note
               for note in evaluation.assumptions)


def test_tnd_leading_zero_cumulative_and_lengths_encoding():
    leading = raw_row("FlashAttentionScore",
                      ["5,8,64", "7,2,64", "7,2,64"],
                      ["DT_BF16"] * 3, ["TND"] * 3, ["5,8,64"],
                      actual_seq_lengths="0,2,5",
                      actual_seq_lengths_kv="0,3,7")
    _, params, _ = infer_request(leading)
    assert params["actual_seq_lens_q"] == [2, 3]
    assert params["actual_seq_lens_kv"] == [3, 4]
    explicit = raw_row("FlashAttentionScore",
                       ["5,8,64", "7,2,64", "7,2,64"],
                       ["DT_BF16"] * 3, ["TND"] * 3, ["5,8,64"],
                       actual_seq_lengths="2,3",
                       actual_seq_lengths_kv="3,4",
                       offset_encoding="lengths")
    _, params2, _ = infer_request(explicit)
    assert params2["actual_seq_lens_q"] == [2, 3]
    assert params2["actual_seq_lens_kv"] == [3, 4]


@pytest.mark.parametrize("lengths", ["100", "-1", "2.5", "2,1", "a,b"])
def test_tnd_invalid_sequence_metadata_is_rejected(lengths):
    row = raw_row("FlashAttentionScore",
                  ["8,8,64", "8,2,64", "8,2,64"],
                  ["DT_BF16"] * 3, ["TND"] * 3, ["8,8,64"],
                  actual_seq_lengths=lengths,
                  actual_seq_lengths_kv=lengths)
    with pytest.raises(AbiError):
        infer_request(row)


def test_zero_active_tokens_is_rejected_not_coerced():
    row = raw_row("FlashAttentionScore",
                  ["8,8,64", "8,2,64", "8,2,64"],
                  ["DT_BF16"] * 3, ["TND"] * 3, ["8,8,64"],
                  actual_seq_lengths="0,0", actual_seq_lengths_kv="0,0")
    with pytest.raises(AbiError) as error:
        infer_request(row)
    assert error.value.code in {"zero_active_tokens",
                               "invalid_sequence_lengths"}


def test_storage_bounds_are_enforced_for_direct_and_raw_paths():
    with pytest.raises(FormulaValidationError):
        evaluate_operator("flash_attention",
                          dict(q_len=8, kv_len=16, hq=4, hkv=4, head_dim=64,
                               storage_kv=-4))
    negative = raw_row("FlashAttentionScore",
                       ["8,8,64", "-4,2,64", "-4,2,64"],
                       ["DT_BF16"] * 3, ["TND"] * 3, ["8,8,64"])
    with pytest.raises(AbiError):
        infer_request(negative)
    arity = raw_row("FlashAttentionScore",
                    ["8,8,64", "8,2,64", "8,2,64"],
                    ["DT_BF16"] * 3, ["TND"] * 3, ["8,8,64"],
                    actual_seq_lengths="2,3",
                    actual_seq_lengths_kv="2,3,4")
    with pytest.raises(AbiError):
        infer_request(arity)


def test_add_rms_norm_preserves_residual_traffic():
    row = raw_row("aclnnAddRmsNorm_AddRmsNorm",
                  ["2,8", "2,8", "8"], ["DT_BF16"] * 3, ["ND"] * 3,
                  ["2,8", "2", "2,8"],
                  out_dtypes=["DT_BF16", "DT_FLOAT", "DT_BF16"])
    operator, params, _ = infer_request(row)
    assert operator == "add_rms_norm"
    assert params["residual"] is True
    card = evaluate_operator(operator, params).formula_card
    plain = evaluate_operator("rms_norm", {"rows": 2, "hidden": 8}).formula_card
    assert card.compulsory_read_bytes > plain.compulsory_read_bytes
    assert card.compulsory_write_bytes > plain.compulsory_write_bytes


def test_batch_matmul_multiplies_batch_and_distinguishes_broadcast():
    batched = raw_row("aclnnBatchMatMul_BatchMatMul",
                      ["4,32,128", "4,128,256"], ["DT_BF16"] * 2,
                      ["ND"] * 2, ["4,32,256"])
    operator, params, _ = infer_request(batched)
    assert operator == "matmul"
    assert params["batch"] == 4
    assert params["weight_broadcast"] is False
    card = evaluate_operator(operator, params).formula_card
    assert card.cube_macs == 4 * 32 * 256 * 128
    broadcast = raw_row("aclnnBatchMatMul_BatchMatMul",
                        ["4,32,128", "1,128,256"], ["DT_BF16"] * 2,
                        ["ND"] * 2, ["4,32,256"])
    _, params2, _ = infer_request(broadcast)
    assert params2["batch"] == 4 and params2["weight_broadcast"] is True
    narrow = evaluate_operator("matmul", params2).formula_card
    assert narrow.compulsory_read_bytes < card.compulsory_read_bytes
    assert narrow.cube_macs == card.cube_macs


def test_gemm_contraction_mismatch_is_rejected():
    row = raw_row("aclnnMatmul_MatMulV3", ["32,128", "64,256"],
                  ["DT_BF16"] * 2, ["ND"] * 2, ["32,256"])
    with pytest.raises(AbiError) as error:
        infer_request(row)
    assert error.value.code == "gemm_k_mismatch"
    with pytest.raises(FormulaValidationError):
        evaluate_operator("matmul", {"M": 32, "N": 256, "K": 0})


def test_unknown_dtype_is_rejected_not_defaulted():
    row = raw_row("aclnnMatmul_MatMulV3", ["32,128", "128,256"],
                  ["DT_MYSTERY", "DT_BF16"], ["ND"] * 2, ["32,256"])
    with pytest.raises(AbiError) as error:
        infer_request(row)
    assert error.value.code == "unknown_dtype"
    annotation = annotate_row(row, measured_us=10.0)
    assert annotation["status"] == "invalid_abi"
    assert annotation["code"] == "unknown_dtype"


def test_full_padded_operators_keep_static_storage():
    row = raw_row("aclnnMatmul_MatMulV3", ["8,128", "128,256"],
                  ["DT_BF16"] * 2, ["ND"] * 2, ["8,256"],
                  actual_seq_lengths="4")
    operator, params, _ = infer_request(row)
    assert operator == "matmul"
    assert "actual_seq_lens_q" not in params
    evaluation = evaluate_operator(operator, params)
    assert "padded rows skipped" not in " ".join(evaluation.assumptions)
    assert evaluation.formula_card.bindings["M"] == 8


def test_rejected_padded_varlen_record_is_an_abi_negative_fixture():
    record = {
        "section": "D", "op": "padded_varlen_contract", "storage_m": 48,
        "logical_m": 33, "accepted": False,
        "error": "npu_fused_infer_attention_score_v2_symint: NPU function "
                 "error: call aclnnFusedInferAttentionScoreV5 failed, "
                 "error code is 561002",
    }
    annotation = annotate_row(record, measured_us=None)
    assert annotation["status"] == "invalid_abi"
    assert annotation["code"] == "rejected_capture_row"


def test_unsupported_attention_layout_is_rejected():
    row = raw_row("FlashAttentionScore", ["8,64", "8,64", "8,64"],
                  ["DT_BF16"] * 3, ["ND"] * 3, ["8,64"])
    with pytest.raises(AbiError) as error:
        infer_request(row)
    assert error.value.code == "unsupported_attention_layout"


# R5 native contracts: keep malformed supplied slots distinct from absence.
def _r5_row(name, inputs, outputs, dtypes=None, out_dtypes=None, **attrs):
    shape = lambda item: ','.join(map(str, item)) if isinstance(item, list) else item
    return raw_row(name, list(map(shape, inputs)), dtypes or ['DT_BF16']*len(inputs),
                   ['ND']*len(inputs), list(map(shape, outputs)), out_dtypes, **attrs)


def _r5_card(row):
    result = annotate_row(row, measured_us=1e12, include_card=True)
    assert result['status'] == 'clean', result
    return result['formula_card']


@pytest.mark.parametrize('shape,dtype,extra_bytes', [
    ('', '', 0), ('', 'DT_FLOAT', None), ([4, 16], 'DT_FLOAT', 256), ([16], 'DT_BF16', 32),
    ([1, 16], 'DT_FLOAT', 64), ([4, 1], 'DT_FLOAT', 16), ([1], 'DT_FLOAT', 4),
    ('bad', 'DT_FLOAT', None), ([9, 16], 'DT_FLOAT', None),
    ([4, 16], 'DT_INT32', None), ([4, 15], 'DT_FLOAT', None),
    ([4, 1, 16], 'DT_FLOAT', None),
])
def test_r5_03_pertoken_scale_presence_precision_and_batch(shape, dtype, extra_bytes):
    row = _r5_row('QuantBatchMatmulV3',
                  [[4, 16, 128], [4, 128, 32], [4, 32], '', shape], [[4, 16, 32]],
                  ['DT_INT8', 'DT_INT8', 'DT_FLOAT', 'DT_BF16', dtype])
    if not dtype:
        row['input_formats'] = 'ND;ND;ND;ND;'
    if extra_bytes is None:
        with pytest.raises(AbiError):
            infer_request(row)
    else:
        assert _r5_card(row)['compulsory_read_bytes'] == 25088 + extra_bytes


@pytest.mark.parametrize('residual_dtype,residual_bpe', [('DT_BF16', 2), ('DT_FLOAT', 4)])
@pytest.mark.parametrize('out_dtype,out_bpe', [('DT_BF16', 2), ('DT_FLOAT', 4)])
def test_r5_04_addnorm_residual_widths(residual_dtype, residual_bpe, out_dtype, out_bpe):
    row = _r5_row('AddRmsNorm', [[2, 8], [2, 8], [8]], [[2, 8], [2, 1], [2, 8]],
                  ['DT_BF16', residual_dtype, 'DT_BF16'], ['DT_BF16', 'DT_FLOAT', out_dtype])
    c = _r5_card(row)
    assert (c['compulsory_read_bytes'], c['compulsory_write_bytes']) == (
        48 + 16*residual_bpe, 40 + 16*out_bpe)
    p = dict(rows=2, hidden=8, rstd_elems=2,
             residual_dtype='fp32' if residual_bpe == 4 else 'bf16',
             x_out_dtype='fp32' if out_bpe == 4 else 'bf16')
    direct = evaluate_operator('add_rms_norm', p).formula_card
    assert (direct.compulsory_read_bytes, direct.compulsory_write_bytes) == (
        c['compulsory_read_bytes'], c['compulsory_write_bytes'])
    default = evaluate_operator('add_rms_norm', dict(rows=2, hidden=8, rstd_elems=2)).formula_card
    assert (default.compulsory_read_bytes, default.compulsory_write_bytes) == (80, 72)


@pytest.mark.parametrize('name,ops', [('SwiGlu', 5), ('SiluAndMul', 5), ('GeGlu', 8)])
def test_r5_05_packed_activation_complete_geometry(name, ops):
    for shape in ([9, 3], [2, 4], [6, 1]):
        with pytest.raises(AbiError):
            infer_request(_r5_row(name, [[2, 6]], [shape]))
    for x, out in (([2, 6], [2, 3]), ([2, 3, 6], [2, 3, 3]), ([12], [6])):
        c = _r5_card(_r5_row(name, [x], [out]))
        import math
        n = math.prod(out)
        assert (c['compulsory_read_bytes'], c['compulsory_write_bytes'], c['vector_ops']) == (
            4*n, 2*n, ops*n)


def _recurrent_row():
    return _r5_row('FusedRecurrentGdn',
                    [[2, 2, 16], [2, 2, 16], [2, 2, 8], [2, 2, 16], [2, 2], [2, 2, 16, 8]],
                    [[2, 2, 8]], ['DT_BF16']*5 + ['DT_FLOAT'])


@pytest.mark.parametrize('position', range(7))
@pytest.mark.parametrize('defect', ['missing', 'bad', 'dtype', 'axes'])
def test_r5_06_every_recurrent_operand_is_validated(position, defect):
    row = _recurrent_row()
    direction, idx = ('input', position) if position < 6 else ('output', 0)
    key = direction + ('_data_types' if defect == 'dtype' else '_shapes')
    values = row[key].split(';')
    values[idx] = {'missing': '', 'bad': 'bad', 'dtype': 'DT_INT32', 'axes': '2,7'}[defect]
    row[key] = ';'.join(values)
    with pytest.raises(AbiError):
        infer_request(row)


@pytest.mark.parametrize('scalar', [True, False])
@pytest.mark.parametrize('rate_dtype,bpe', [('DT_BF16', 2), ('DT_FLOAT', 4)])
def test_r5_06_recurrent_rates_and_primary_output(scalar, rate_dtype, bpe):
    row = _recurrent_row()
    shapes = row['input_shapes'].split(';')
    shapes[3] = '2,2' if scalar else '2,2,16'
    row.update(input_shapes=';'.join(shapes),
               input_data_types=';'.join(['DT_BF16']*3 + [rate_dtype]*2 + ['DT_FLOAT']),
               output_data_types='DT_FLOAT')
    c = _r5_card(row)
    assert c['compulsory_read_bytes'] == 2368 + bpe*(4 + (4 if scalar else 64))
    assert c['compulsory_write_bytes'] == 2048 + 128
    assert (c['vector_ops'], c['cube_macs']) == (4*(7*16*8 + 3*8 + 16), 0)
    # Rank-4 speculative buffers carry one gate/beta/output per slot.
    spec = _r5_row('FusedRecurrentGdn',
                    [[2, 3, 2, 16], [2, 3, 2, 16], [2, 3, 2, 8],
                     [2, 3, 2], [2, 3, 2], [2, 2, 16, 8]],
                    [[2, 3, 2, 8]], ['DT_BF16']*5 + ['DT_FLOAT'], spec_slots=3)
    assert _r5_card(spec)['compulsory_read_bytes'] == 2048 + 3*320 + 48
    with pytest.raises(AbiError):
        infer_request(dict(spec, spec_slots=2))


@pytest.mark.parametrize('name', ['KdaRecoverSsmVerify', 'KdaRecoverSsmCommit'])
@pytest.mark.parametrize('named', [True, False])
@pytest.mark.parametrize('which', ['initial', 'final'])
@pytest.mark.parametrize('bad', ['bad', [1, 2, 16]])
def test_r5_06_recover_validates_both_state_slots(name, named, which, bad):
    initial = bad if which == 'initial' else [1, 2, 16, 8]
    final = bad if which == 'final' else [1, 2, 16, 8]
    row = _r5_row(name, [[1, 2, 16], initial], [final],
                  ['DT_BF16', 'DT_FLOAT'], ['DT_FLOAT'])
    if named:
        row['input_shapes'] = [dict(name='compact', shape=[1, 2, 16], dtype='DT_BF16'),
                               dict(name='initial_state', shape=initial, dtype='DT_FLOAT')]
        row['output_shapes'] = [dict(name='final_state', shape=final, dtype='DT_FLOAT')]
    with pytest.raises(AbiError):
        infer_request(row)


def test_r5_06_chunk_output_precision_is_preserved():
    for dtype, expected in [('DT_BF16', 1184), ('DT_FLOAT', 1344)]:
        row = _r5_row('ChunkGatedDeltaRule',
                       [[5, 2, 16], [5, 2, 16], [5, 2, 8], [5, 2], [5, 2, 16], [1, 2, 16, 8]],
                       [[5, 2, 8], [1, 2, 16, 8]], ['DT_BF16']*5 + ['DT_FLOAT'],
                       [dtype, 'DT_FLOAT'], actual_seq_lengths=[5])
        c = _r5_card(row)
        assert (c['compulsory_read_bytes'], c['compulsory_write_bytes']) == (2164, expected)


@pytest.mark.parametrize('name,ins,outs', [
    ('HcclAllGather', [3], [12]), ('HcclReduceScatter', [12], [3]),
    ('HcclAllReduce', [12], [12]), ('HcclAllToAll', [12], [12]),
    ('HcclAllToAllV', [12], [15]),
])
def test_r5_08_native_collectives_require_matching_output_dtype(name, ins, outs):
    attrs = dict(world_size=4)
    if name.endswith('V'):
        attrs.update(send_counts=[3]*4, recv_counts=[3, 4, 4, 4], rank=0)
    row = _r5_row(name, [ins], [outs], **attrs)
    c = _r5_card(row)
    assert (c['compulsory_read_bytes'], c['compulsory_write_bytes']) == (2*ins[0], 2*outs[0])
    for output in ('', 'bad'):
        with pytest.raises(AbiError):
            infer_request(dict(row, output_shapes=output))
    for dtype in ('', 'DT_FLOAT'):
        with pytest.raises(AbiError):
            infer_request(dict(row, output_data_types=dtype))
    # A malformed input cannot fall back to an unrelated size-only contract.
    with pytest.raises(AbiError):
        infer_request(dict(row, input_shapes='bad', size_bytes=24))


@pytest.mark.parametrize('name', ['SwiGlu', 'SiluAndMul', 'GeGlu'])
@pytest.mark.parametrize('x,out', [
    ([2, 6], [2, 6]), ([6], [6]), ([2, 6], [9, 3]),
    ([2, 3, 6], [6, 3]), ([2, 3, 6], [3, 2, 3]),
    ([2, 5], [2, 2]), ([2, 0], [2, 0]), ('[]', '[]'), ([6], '[]'),
])
def test_r6_01_packed_contract_precedes_shape_fallback(name, x, out):
    row = _r5_row(name, [x], [out])
    with pytest.raises(AbiError) as error:
        infer_request(row)
    assert error.value.code == 'activation_output_shape'
    assert annotate_row(row)['status'] == 'invalid_abi'


@pytest.mark.parametrize('name,ops', [('SwiGlu', 15), ('SiluAndMul', 15), ('GeGlu', 24)])
def test_r6_01_rank_one_two_input_and_unary_contracts(name, ops):
    c = _r5_card(_r5_row(name, [[3], [3]], [[3]]))
    assert (c['vector_ops'], c['compulsory_read_bytes'], c['compulsory_write_bytes']) == (ops, 12, 6)
    for unary in ('Silu', 'Swish'):
        c = _r5_card(_r5_row(unary, [[6]], [[2, 3]]))
        assert (c['vector_ops'], c['compulsory_read_bytes'], c['compulsory_write_bytes']) == (30, 12, 12)


def _r6_lengths_row(name, q_raw, kv_raw, mode='cumulative', tokens=5, **attrs):
    dense = name == 'FlashAttentionScore'
    return _r5_row(name, [[tokens, 1, 16], [1030, 1, 16],
                          [1030, 1, 16] if dense else [tokens, 1, 2]], [[tokens, 1, 16]],
                   ['DT_BF16', 'DT_BF16', 'DT_BF16' if dense else 'DT_INT32'],
                   actual_seq_lengths=q_raw, actual_seq_lengths_kv=kv_raw,
                   actual_seq_lengths_type=mode, topk=2, causal=True, causal_offset=0, **attrs)


@pytest.mark.parametrize('name', ['LightningIndexer', 'SparseFlashMla', 'FlashAttentionScore'])
@pytest.mark.parametrize('batch_source', ['row', 'attrs', 'paired'])
@pytest.mark.parametrize('q_raw,kv_raw,mode,qs,ks', [
    ([0, 2, 5], [10, 1010, 1030], 'cumulative', [0, 2, 3], [10, 1000, 20]),
    ([0, 0, 5], [10, 1010, 1030], 'cumulative', [0, 0, 5], [10, 1000, 20]),
    ([0, 0, 2, 5], [0, 10, 1010, 1030], 'cumulative', [0, 2, 3], [10, 1000, 20]),
    ([0, 0, 2, 5], [10, 1010, 1030], 'cumulative', [0, 2, 3], [10, 1000, 20]),
    ([0, 2, 5], [0, 10, 1010, 1030], 'cumulative', [0, 2, 3], [10, 1000, 20]),
    ([0, 2, 3], [10, 1000, 20], 'per_seq', [0, 2, 3], [10, 1000, 20]),
    ([3, 0], [7, 1000], 'per_seq', [3, 0], [7, 1000]),
    ([2, 0, 3], [10, 1000, 20], 'per_seq', [2, 0, 3], [10, 1000, 20]),
    ([2, 2, 5], [10, 1010, 1030], 'cumulative', [2, 0, 3], [10, 1000, 20]),
])
def test_r6_02_native_owner_decoding_matches_direct(name, batch_source, q_raw, kv_raw, mode, qs, ks):
    attrs = {'batch': len(qs)} if batch_source == 'row' else (
        {'attrs': {'batch': len(qs)}} if batch_source == 'attrs' else {})
    row = _r6_lengths_row(name, q_raw, kv_raw, mode, sum(qs), **attrs)
    op, params, _ = infer_request(row)
    assert (params['actual_seq_lens_q'], params['actual_seq_lens_kv'], params['batch']) == (qs, ks, len(qs))
    p = dict(batch=len(qs), actual_seq_lens_q=qs, actual_seq_lens_kv=ks,
             kv_len=1030, causal=True, causal_offset=0)
    if name == 'FlashAttentionScore':
        p.update(q_len=sum(qs), hq=1, hkv=1, head_dim=16, layout='TND',
                 storage_q=sum(qs), storage_kv=1030)
    else:
        p.update(tokens=sum(qs), heads=1, head_dim=16, index_heads=1, index_dim=16, topk=2)
    native, direct = _r5_card(row), evaluate_operator(op, p).formula_card
    for key in ('alg_flops', 'vector_ops', 'compulsory_read_bytes', 'compulsory_write_bytes',
                'granule_gm_bytes', 'cube_flops_tiled'):
        assert native[key] == getattr(direct, key)
    if qs == [0, 2, 3] and name != 'FlashAttentionScore':
        pairs = 'attended_pairs' if name == 'LightningIndexer' else 'sparse_pairs'
        assert (native['bindings'][pairs], native['compulsory_gm_bytes']) == (
            (9, 360) if name == 'LightningIndexer' else (8, 616))


@pytest.mark.parametrize('name', ['LightningIndexer', 'SparseFlashMla', 'FlashAttentionScore'])
@pytest.mark.parametrize('batch', [True, False, 0, -1, 3.0, 1.5, '3'])
def test_r6_02_invalid_explicit_batch(name, batch):
    for attrs in ({'batch': batch}, {'attrs': {'batch': batch}}):
        row = _r6_lengths_row(name, [0, 2, 5], [10, 1010, 1030], **attrs)
        with pytest.raises(AbiError):
            infer_request(row)


@pytest.mark.parametrize('name', ['LightningIndexer', 'SparseFlashMla', 'FlashAttentionScore'])
@pytest.mark.parametrize('q,kv', [([2, 5], [10, 1010, 1030]),
                                 ([1, 1, 2, 5], [10, 1010, 1030]),
                                 ([0, 2, 5], [1, 10, 1010, 1030])])
def test_r6_02_explicit_batch_rejects_bad_vector_arity(name, q, kv):
    with pytest.raises(AbiError):
        infer_request(_r6_lengths_row(name, q, kv, batch=3))


def _r6_mc2_row(stage, capacity, **attrs):
    dispatch = stage == 'dispatch'
    return _r5_row('MoeDistribute' + stage.title() + 'V3',
                   [[1], [4 if dispatch else capacity, 16], [4, 1], [4]],
                   [[capacity if dispatch else 4, 16]],
                   ['DT_INT32', 'DT_BF16', 'DT_INT32', 'DT_INT32'], **attrs)


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('ep_key', ['ep', 'ep_world_size', 'world_size', 'expert_counts'])
@pytest.mark.parametrize('routed', [0, 4, 8, 9, 16])
def test_r6_03_arrivals_preserve_ep_and_match_direct(stage, ep_key, routed):
    p = dict(experts_total=4, experts_local=2, topk=1, routed_rows=routed)
    row = _r6_mc2_row(stage, max(1, routed), **p, **({ep_key: 2} if ep_key != 'expert_counts' else {}))
    if routed > 8:
        with pytest.raises(AbiError):
            infer_request(row)
        assert annotate_row(row)['status'] == 'invalid_abi'
        with pytest.raises(FormulaValidationError):
            evaluate_operator('moe_distribute_' + stage, dict(p, tokens=4, hidden=16, ep=2))
    else:
        op, params, _ = infer_request(row)
        assert (params['ep'], params['routed_rows']) == (2, routed)
        c = _r5_card(row)
        direct = evaluate_operator(op, dict(p, tokens=4, hidden=16, ep=2, use_measured_fit=False)).formula_card
        assert c['bindings']['routed_rows'] == routed
        for key in ('compulsory_read_bytes', 'compulsory_write_bytes', 'comm_bytes'):
            assert c[key] == getattr(direct, key)


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('names', [('local', 'remote', 'sent', 'received'),
                                  ('local_rows', 'remote_rows', 'sent_rows', 'received_rows'),
                                  ('local_routed_rows', 'remote_routed_rows', 'sent_routed_rows', 'received_routed_rows')])
def test_r6_03_exact_locality_and_explicit_zeros(stage, names):
    p = dict(ep=2, experts_total=4, experts_local=2, topk=1, routed_rows=8)
    counts = (4, 4, 0, 4) if stage == 'dispatch' else (4, 4, 4, 0)
    row = _r6_mc2_row(stage, 8, **p, attrs=dict(zip(names, counts)))
    c = _r5_card(row)
    assert (c['bindings']['local_rows'], c['bindings']['remote_routed_rows'], c['comm_bytes']) == (4, 4, 128)
    assert annotate_row(dict(row, attrs=dict.fromkeys(names, 0)))['status'] == 'invalid_abi'
    remote_only = _r6_mc2_row(stage, 4, **dict(p, routed_rows=4),
                               attrs=dict(zip(names, (0, 4, 4, 4))))
    c = _r5_card(remote_only)
    assert (c['bindings']['local_rows'], c['comm_bytes']) == (0, 128)
    empty = _r6_mc2_row(stage, 1, **dict(p, experts_local=0, routed_rows=0))
    assert _r5_card(empty)['bindings']['routed_rows'] == 0


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('field', [
    'routed_rows', 'local', 'local_rows', 'local_routed_rows', 'remote', 'remote_rows',
    'remote_routed_rows', 'sent', 'sent_rows', 'sent_routed_rows', 'received', 'received_rows',
    'received_routed_rows', 'experts_total', 'E', 'experts_local', 'E_local', 'topk', 'K',
    'ep', 'world_size', 'ep_world_size', 'tokens', 'T', 'hidden', 'H',
])
def test_r6_03_native_integer_declarations_are_strict(stage, field):
    for bad in (True, False, -1, 1.0, 1.5, '1', ''):
        for attrs in ({field: bad}, {'attrs': {field: bad}}):
            with pytest.raises(AbiError):
                infer_request(_r6_mc2_row(stage, 8, **attrs))


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
def test_r6_03_capacity_conflicts_and_authentic_mutations(stage):
    p = dict(ep=2, experts_total=4, experts_local=2, topk=1, routed_rows=8)
    for extra in ({'world_size': 3}, {'attrs': {'ep': 3}}, {'local': 0, 'local_rows': 1},
                  {'topk': 2}, {'tokens': 5}, {'hidden': 17}, {'ep': 0}, {'experts_total': 0}):
        with pytest.raises(AbiError):
            infer_request(_r6_mc2_row(stage, 8, **dict(p, **extra)))
    with pytest.raises(AbiError) as error:
        infer_request(_r6_mc2_row(stage, 7, **p))
    assert error.value.code == 'mc2_buffer_capacity'
    row = _r6_mc2_row(stage, 8, **p)
    for output in ('', '4,15', '1,4,16'):
        with pytest.raises(AbiError):
            infer_request(dict(row, output_shapes=output))
    with pytest.raises(AbiError) as error:
        infer_request(_r6_mc2_row(stage, 8, routed_rows=8))
    assert error.value.code == 'mc2_ep_ambiguous'
    from pathlib import Path
    import json
    fixture = json.loads((Path(__file__).parent / 'fixtures/a5_op_goldens.json').read_text())
    raw = next(point['raw_row'] for point in fixture['points']
               if point['group'] == 'kernel' and point['operator'] == 'moe_distribute_' + stage)
    _r5_card(raw)
    for dtype, code in [('DT_FLOAT', 'mc2_dtype_mismatch'), ('DT_INT32', 'mc2_dtype')]:
        dtypes = raw['output_data_types'].split(';')
        a = annotate_row(dict(raw, output_data_types=';'.join([dtype, *dtypes[1:]])))
        assert (a['status'], a['code']) == ('invalid_abi', code)
    op, baseline, _ = infer_request(raw)
    c = _r5_card(dict(raw, routed_rows=1024))
    direct = evaluate_operator(op, dict(baseline, routed_rows=1024)).formula_card
    assert (c['bindings']['ep'], c['bindings']['routed_rows']) == (baseline['ep'], 1024)
    assert c['compulsory_gm_bytes'] == direct.compulsory_gm_bytes
    for extra in ({'routed_rows': 2049 if stage == 'dispatch' else 4097}, {'routed_rows': -1},
                  dict(routed_rows=512, local=0, remote=0, sent=0, received=0)):
        assert annotate_row(dict(raw, **extra))['status'] == 'invalid_abi'


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('extra', [{}, {'routed_rows': None}, {'routed_rows': 4},
                                  dict(local=4, remote=0, sent=0, received=0)])
def test_r7_01_effective_capacity_and_empty_arrivals(stage, extra):
    p = dict(ep=2, experts_total=4, experts_local=2, topk=1)
    for source in ('row', 'attrs', 'attributes'):
        attrs = extra if source == 'row' else {source: extra}
        for capacity in (0, 1, 4):
            row = _r6_mc2_row(stage, capacity, **p, **attrs)
            if capacity < 4:
                a = annotate_row(row)
                assert (a['status'], a['code']) == ('invalid_abi', 'mc2_buffer_capacity')
            else:
                assert _r5_card(row)['bindings']['routed_rows'] == 4
    for capacity in (0, 1):
        for el in (0, 2):
            row = _r6_mc2_row(stage, capacity, **dict(p, experts_local=el, routed_rows=0))
            assert _r5_card(row)['bindings']['tokens'] == 4
        assert _r5_card(_r6_mc2_row(stage, capacity, **dict(p, experts_local=0)))['bindings']['routed_rows'] == 0


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('dtype', ['DT_BF16', 'DT_FLOAT16', 'DT_FLOAT', 'DT_INT32', 'DT_INT64', 'DT_UINT8', 'BOOL'])
def test_r7_02_primary_storage_width_contract(stage, dtype):
    floating = {'DT_BF16': 2, 'DT_FLOAT16': 2, 'DT_FLOAT': 4}
    for other in floating:
        row = _r6_mc2_row(stage, 8, ep=2, experts_total=4, experts_local=2, routed_rows=8)
        for in_dtype, out_dtype in ((dtype, other), (other, dtype)):
            row.update(input_data_types=f'DT_INT32;{in_dtype};DT_INT32;DT_INT32', output_data_types=out_dtype)
            if dtype not in floating or in_dtype != out_dtype:
                a = annotate_row(row)
                code = 'mc2_dtype' if dtype not in floating else 'mc2_dtype_mismatch'
                assert (a['status'], a['code']) == ('invalid_abi', code)
            else:
                c = _r5_card(row)
                assert c['compulsory_write_bytes'] == (128*floating[dtype]+16 if stage == 'dispatch' else 64*floating[dtype])
                op, params, _ = infer_request(row)
                assert c['granule_gm_bytes'] == evaluate_operator(op, params).formula_card.granule_gm_bytes


@pytest.mark.parametrize('stage', ['dispatch', 'combine'])
@pytest.mark.parametrize('defect', ['tokens', 'hidden', 'expert_ids', 'scales', 'topk'])
def test_r7_03_descriptor_axes_are_not_clamped(stage, defect):
    t, h, k = (0 if defect == 'tokens' else 4), (0 if defect == 'hidden' else 16), (0 if defect == 'topk' else 1)
    row = _r5_row('MoeDistribute' + stage.title() + 'V3',
                   [[1], [t if stage == 'dispatch' else 1, h],
                    [3 if defect == 'expert_ids' else t, k], [4], [3 if defect == 'scales' else t, k]],
                   [[1 if stage == 'dispatch' else t, h]],
                   ['DT_INT32', 'DT_BF16', 'DT_INT32', 'DT_INT32', 'DT_FLOAT'],
                   ep=2, experts_total=4, experts_local=2, routed_rows=0)
    a = annotate_row(row)
    assert (a['status'], a['code']) == ('invalid_abi', 'mc2_buffer_shape')
