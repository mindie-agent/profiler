"""Retained mixed-step A3/A5 tensors; durations never select a workload or layer."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import (
    observed_contract, observed_contract_diagnostic, observed_contract_scope,
)


FIXTURE = Path(__file__).parent / "fixtures/mixed_step_body"


def captured(name, kind, tokens=None):
    return next(
        row for row in kernel_rows(FIXTURE / (name + ".csv"))
        if row.kind == kind and (tokens is None or row.input_shapes[0][0] == tokens)
    )


def change_slot(row, field, slot, value):
    values = list(getattr(row, field))
    values[slot] = value
    return replace(row, **{field: tuple(values)})


@pytest.mark.parametrize("name,tokens,heads,width", [
    ("a3_qwen35", 2, 4, 256),
    ("a3_qwen36", 1, 6, 256),
    ("a3_qwen36", 4, 6, 256),
    ("a5_qwen38", 1, 24, 1024),
    ("a5_qwen38", 4, 24, 1024),
])
def test_real_paged_fia_preserves_query_and_cache_geometry(name, tokens, heads, width):
    row = captured(name, "FusedInferAttentionScore", tokens)
    query = ((tokens, heads, 256), "bf16", "ND")
    tail = ((128, width), "bf16", "ND")
    expected = ("attention_paged_active_qkv", row.kind, query, (tail, tail), query, 1)
    assert observed_contract(row) == expected
    assert observed_contract(replace(row, duration_ns=1)) == expected
    assert not observed_contract_scope(row)["occurrence_identity"]
    assert {"context_length", "phase", "verify_or_draft_role"} <= set(
        observed_contract_scope(row)["not_compared"])


def test_paged_capacity_is_excluded_but_batch_block_width_kind_and_dtype_are_not():
    row = captured("a3_qwen36", "FusedInferAttentionScore", 4)
    expected = observed_contract(row)
    table = 6
    changed = change_slot(row, "input_shapes", 1, (900, 128, 256))
    changed = change_slot(changed, "input_shapes", 2, (900, 128, 256))
    changed = change_slot(changed, "input_shapes", table, (1, 2000))
    assert observed_contract(changed) == expected
    assert native_tensor_contract(changed) != native_tensor_contract(row)
    for field, index, value in [
        ("input_shapes", table, (2, 1029)),
        ("input_shapes", 1, (21567, 64, 256)),
        ("input_shapes", 1, (21567, 128, 512)),
        ("input_shapes", 0, (4, 3, 256)),
        ("input_formats", 0, "NCL"),
        ("input_dtypes", 0, "FLOAT16"),
        ("output_dtypes", 0, "FLOAT16"),
        ("output_shapes", 0, (4, 6, 128)),
    ]:
        assert observed_contract(change_slot(row, field, index, value)) != expected
    assert observed_contract(replace(row, kind="OtherAttention")) is None
    assert observed_contract(change_slot(row, "input_dtypes", 1, "DT_UNDEFINED")) is None


@pytest.mark.parametrize("name,tokens", [
    ("a3_qwen35", 8192), ("a3_qwen36", 8192),
])
def test_equal_prefill_query_shapes_do_not_erase_dense_and_paged_boundaries(name, tokens):
    rows = [row for row in kernel_rows(FIXTURE / (name + ".csv"))
            if row.kind == "FusedInferAttentionScore" and row.input_shapes[0][0] == tokens]
    assert {observed_contract(row)[0] for row in rows} == {
        "attention_active_qkv", "attention_paged_active_qkv"}
    assert rows[0].input_shapes[0] == rows[1].input_shapes[0]
    assert observed_contract(rows[0]) != observed_contract(rows[1])


@pytest.mark.parametrize("name,tokens,key_heads,value_heads", [
    ("a3_qwen35", 2, 4, 8), ("a3_qwen36", 4, 4, 12), ("a5_qwen38", 4, 16, 48),
])
def test_recurrent_gdn_accepts_real_scalar_decay_and_validates_all_active_operands(
    name, tokens, key_heads, value_heads,
):
    row = captured(name, "RecurrentGatedDeltaRule")
    expected = ("recurrent_vector", (tokens, key_heads, value_heads, 128, 128), 1, "fp32")
    assert observed_contract(row) == expected
    assert observed_contract(replace(row, duration_ns=999999999)) == expected
    for field, index, value in [
        ("input_shapes", 1, (tokens, key_heads + 1, 128)),
        ("output_shapes", 0, (tokens, value_heads, 64)),
        ("input_dtypes", 2, "FLOAT16"),
        ("input_dtypes", 3, "FLOAT"),
        ("input_formats", 1, "NCL"),
        ("input_shapes", 6, (tokens + 1,)),
        ("input_shapes", 7, (tokens, key_heads)),
        ("output_shapes", 1, (1, value_heads, 128, 128)),
    ]:
        assert observed_contract(change_slot(row, field, index, value)) is None
    missing = replace(row, input_shapes=None, event=replace(row.event, input_shapes="N/A"))
    assert observed_contract(missing) is None
    assert observed_contract_diagnostic(missing)["category"] == "capture_metadata_missing"
    assert "state_capacity" in observed_contract_scope(row)["not_compared"]


@pytest.mark.parametrize("name,heads", [("a3_qwen35", 8), ("a3_qwen36", 12)])
def test_legacy_chunk_gdn_retains_complete_native_boundary_without_generic_alias(name, heads):
    row = captured(name, "ChunkGatedDeltaRuleFwd")
    native = native_tensor_contract(row)
    assert observed_contract(row) == native
    assert native[0:2] == ("native_tensor_abi", "ChunkGatedDeltaRuleFwd")
    assert native[2][6] == ((1, heads, 128, 128), "fp32", "NCHW")
    assert native[3][1][0] == (heads * 128 * 128,)
    assert observed_contract_diagnostic(row)["category"] == "tensor_contract_available"
    scope = observed_contract_scope(row)
    assert scope["kind"] == "native_chunk_gdn_tensor_abi"
    for field, index, value in [
        ("input_shapes", 1, (1, 5, 8192, 128)),
        ("input_shapes", 4, (1, heads, 8192, 32)),
        ("input_dtypes", 6, "INT32"),
        ("input_dtypes", 7, "INT32"),
        ("output_shapes", 3, (1,)),
    ]:
        assert observed_contract(change_slot(row, field, index, value)) is None
