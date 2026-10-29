"""Original A3 four-layer Kimi MLA ABI; never reinterpret it as GQA TND."""
from dataclasses import replace
from pathlib import Path

from mindie_profiler.body_attention_contracts import fia_block_table_slot
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_scope

FIXTURE = Path(__file__).parent / 'fixtures/attention_cache_contracts'


def change(row, field, index, value):
    values = list(getattr(row, field))
    values[index] = value
    return replace(row, **{field: tuple(values)})


def test_original_kimi_b1_b64_mla_preserves_rotary_and_nbsd_output_axes():
    for row, batch in zip(kernel_rows(FIXTURE / 'a3_kimi_four_layer_mla.csv'), (1, 64)):
        q = ((batch, 16, 1, 512), 'bf16', 'ND')
        qr = ((batch, 16, 1, 64), 'bf16', 'ND')
        kv = ((1, 128, 512), 'bf16', 'ND')
        kr = ((1, 128, 64), 'bf16', 'ND')
        output = ((16, batch, 1, 512), 'bf16', 'ND')
        expected = ('attention_paged_mla_qk_rope', row.kind, (q, qr),
                    (kv, kv, kr), output, batch)
        assert observed_contract(row) == expected
        assert observed_contract(replace(row, duration_ns=1)) == expected
        assert fia_block_table_slot(row) == 4
        assert native_tensor_contract(row)[2][6][0] == (285642, 1, 128, 64)
        assert {'context_length', 'sequence_length_values', 'cache_capacity'} <= set(
            observed_contract_scope(row)['not_compared'])


def test_kimi_mla_excludes_capacity_but_rejects_axis_rotary_and_batch_mismatches():
    row = list(kernel_rows(FIXTURE / 'a3_kimi_four_layer_mla.csv'))[1]
    expected = observed_contract(row)
    resized = row
    for index in (1, 2, 6):
        resized = change(resized, 'input_shapes', index, (1000, *row.input_shapes[index][1:]))
    resized = change(resized, 'input_shapes', 4, (64, 1029))
    assert observed_contract(resized) == expected
    assert native_tensor_contract(resized) != native_tensor_contract(row)
    for field, index, value in [
        ('input_shapes', 3, (63,)), ('input_shapes', 4, (1, 258)),
        ('input_shapes', 5, (64, 16, 1, 32)),
        ('input_shapes', 6, (285642, 128, 1, 64)),
        ('output_shapes', 0, (64, 16, 1, 512)),
        ('input_dtypes', 5, 'FLOAT16'), ('input_formats', 0, 'NCHW'),
    ]:
        changed = change(row, field, index, value)
        assert observed_contract(changed)[0] == 'native_tensor_abi'
        assert fia_block_table_slot(changed) is None
    incomplete = change(row, 'input_dtypes', 6, 'DT_UNDEFINED')
    assert observed_contract(incomplete) is None
    assert fia_block_table_slot(incomplete) is None


def test_real_gqa_compact_seven_slot_contract_still_uses_slot_six():
    row = list(kernel_rows(FIXTURE / 'a3_qwen35.csv'))[2]
    assert len(row.input_shapes) == 7
    assert fia_block_table_slot(row) == 6
    assert observed_contract(row)[0] == 'attention_paged_active_qkv'
    dense = list(kernel_rows(FIXTURE / 'a3_qwen35.csv'))[1]
    assert fia_block_table_slot(dense) is None


def test_real_a5_full31_mla_uses_table14_and_recovers_b1_b32_geometry():
    from mindie_profiler.decode_segmentation import _Row, _query_geometry
    from mindie_profiler.normalized import shapes
    rows = list(kernel_rows(FIXTURE / 'a5_kimi_mla31.csv'))
    compact = list(kernel_rows(FIXTURE / 'a3_kimi_four_layer_mla.csv'))[0]
    for row, batch in zip(rows, (1, 1, 32)):
        assert len(row.input_shapes) == 31
        assert fia_block_table_slot(row) == 14
        assert observed_contract(row)[0] == 'attention_paged_mla_qk_rope'
        geometry = _query_geometry([_Row(row.event, shapes(row.event.input_shapes),
                                        shapes(row.event.output_shapes))], batch)
        assert (geometry['tokens_per_sequence'], geometry['sequences_per_replica']) == (1, batch)
    assert observed_contract(rows[0]) == observed_contract(compact)
    assert observed_contract(rows[0]) == observed_contract(rows[1])
    assert observed_contract(rows[2]) != observed_contract(rows[0])


def test_full31_geometry_does_not_require_unrelated_optional_tensor_contracts():
    row = list(kernel_rows(FIXTURE / 'a5_kimi_mla31.csv'))[-1]
    unknown_auxiliary = change(row, 'input_formats', 3, 'N/A')
    assert observed_contract(unknown_auxiliary) is None
    assert fia_block_table_slot(unknown_auxiliary) == 14
    for field, index, value in [
        ('input_shapes', 14, (1, 516)),
        ('input_shapes', 24, (32, 16, 1, 32)),
        ('input_shapes', 25, (12828, 128, 1, 64)),
        ('input_dtypes', 14, 'DT_UNDEFINED'),
        ('output_shapes', 0, (32, 16, 1, 512)),
    ]:
        assert fia_block_table_slot(change(row, field, index, value)) is None
