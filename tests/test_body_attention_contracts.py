"""Original A3/A5 attention/cache rows and controlled evidence perturbations."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_attention_contracts import (
    attention_contract_diagnostic,
    attention_contract_scope,
    observed_attention_contract,
)
from mindie_profiler.native_tensor_abi import native_tensor_contract, native_tensor_diagnostic
from mindie_profiler.normalized import kernel_rows


FIXTURE = Path(__file__).parent / "fixtures/attention_cache_contracts"


def rows(name):
    return list(kernel_rows(FIXTURE / f"{name}.csv"))


@pytest.mark.parametrize("capture,qshape,kvshape", [
    ("a3_qwen35", (8192, 4, 256), (8192, 1, 256)),
    ("a3_qwen36", (8192, 6, 256), (8192, 1, 256)),
    ("a5_qwen38", (16384, 24, 256), (16384, 4, 256)),
])
def test_dense_fia_keeps_real_local_heads_and_native_tensor_axes(capture, qshape, kvshape):
    row = rows(capture)[1]
    contract = observed_attention_contract(row)
    assert contract == (
        "attention_active_qkv", "FusedInferAttentionScore",
        ((qshape, "bf16", "ND"), (kvshape, "bf16", "ND"), (kvshape, "bf16", "ND")),
        ((qshape, "bf16", "ND"),),
    )
    assert "logical_input_layout" in attention_contract_scope(row)["not_compared"]
    assert observed_attention_contract(replace(row, duration_ns=row.duration_ns * 1000)) == contract
    changed_heads = (qshape[0], qshape[1] + 1, qshape[2])
    changed = replace(row, input_shapes=(changed_heads, *row.input_shapes[1:]),
                      output_shapes=(changed_heads, *row.output_shapes[1:]))
    assert observed_attention_contract(changed) != contract
    changed_layout = replace(row, input_formats=("NCL", *row.input_formats[1:]))
    assert observed_attention_contract(changed_layout)[0] == "native_tensor_abi"


@pytest.mark.parametrize("capture,index,family", [
    ("a3_qwen35", 2, "attention_paged_active_qkv"),
    ("a5_qwen38", 3, "attention_paged_active_qkv"),
    ("a5_fia_paged_probe", 0, "native_tensor_abi"),
])
def test_paged_fia_retains_native_cache_and_block_table_descriptors(capture, index, family):
    row = rows(capture)[index]
    contract = observed_attention_contract(row)
    assert contract[0:2] == (family, "FusedInferAttentionScore")
    native = native_tensor_contract(row)
    assert native[2][1][0] == row.input_shapes[1]
    table_slot = 6 if len(row.input_shapes) == 7 else 14
    assert native[2][table_slot][0] == row.input_shapes[table_slot]
    assert native[2][table_slot][1] == "int32"
    if family == "attention_paged_active_qkv":
        assert contract[3][0][0] == row.input_shapes[1][1:]
        assert contract[-1] == row.input_shapes[table_slot][0]
        assert "block_table_column_count_and_values" in attention_contract_scope(row)["not_compared"]
    else:
        # The separate probe uses four-dimensional cache storage. Do not infer
        # a flattening or axis order from the serving capture's three-D view.
        assert contract == native
        assert len(native[2][1][0]) == 4


def test_explicit_empty_slots_do_not_become_scalar_or_disappear():
    row = rows("a5_qwen38")[1]
    contract = native_tensor_contract(row)
    assert len(contract[2]) == 31
    assert contract[2][3] == ((), None, None)
    assert contract[3][1] == ((), "fp32", "ND")
    assert contract[2][5] == ((1,), "int64", "ND")
    incomplete = replace(row, input_formats=row.input_formats[:-1])
    assert observed_attention_contract(incomplete) is None
    assert native_tensor_diagnostic(incomplete)["reason"] == "incomplete_native_tensor_slots"
    missing_dtype = replace(row, input_dtypes=("DT_UNDEFINED", *row.input_dtypes[1:]))
    assert observed_attention_contract(missing_dtype) is None
    assert native_tensor_diagnostic(missing_dtype)["missing_fields"] == ["input[0].dtype"]


@pytest.mark.parametrize("capture,elements,tokens", [
    ("a3_qwen35", 2097152, 8192), ("a3_qwen36", 2097152, 8192),
    ("a5_qwen38", 16777216, 16384),
])
def test_scatter_cache_compares_active_elements_without_inventing_head_factorization(
    capture, elements, tokens,
):
    row = rows(capture)[0]
    assert observed_attention_contract(row) == (
        "kv_cache_store_active_elements", "ScatterPaKvCache",
        ((elements, "bf16"), (elements, "bf16")), (tokens,),
    )
    scope = attention_contract_scope(row)
    assert {"cache_capacity", "head_shape_factorization", "slot_mapping_dtype",
            "slot_mapping_values", "native_storage_layout"} <= set(scope["not_compared"])
    changed_layout = replace(row, input_formats=("ND", *row.input_formats[1:]))
    assert observed_attention_contract(changed_layout)[0] == "native_tensor_abi"


def test_real_cache_capacity_variants_have_one_explicitly_limited_active_contract():
    first, _, other_capacity, _ = rows("a5_qwen38")
    assert first.input_shapes[1] != other_capacity.input_shapes[1]
    assert first.input_shapes[4] != other_capacity.input_shapes[4]
    assert native_tensor_contract(first) != native_tensor_contract(other_capacity)
    assert observed_attention_contract(first) == observed_attention_contract(other_capacity)


def test_reshape_cache_keeps_three_dimensional_geometry_and_slot_dtype():
    row = rows("qwen3_8b_s1")[0]
    assert observed_attention_contract(row) == (
        "kv_cache_store_active", "ReshapeAndCacheNdKernel",
        (((2048, 8, 128), "bf16", "ND"), ((2048, 8, 128), "bf16", "ND")),
        ((2048,), "int32", "ND"), (("bf16", "ND"), ("bf16", "ND")),
    )
    changed_slots = replace(row, input_shapes=(*row.input_shapes[:4], (2047,)))
    assert observed_attention_contract(changed_slots)[0] == "native_tensor_abi"


@pytest.mark.parametrize("capture,kinds", [
    ("dsv2lite_s1", ["KvRmsNormRopeCache", "RINGMLAPrefillBF16Kernel", "PagedCacheLoadNdKernel"]),
    ("a3_deepseek_v4f", ["ScatterNdUpdateSk", "SparseAttnSharedkv"]),
    ("a3_glm53", ["MlaPrologV3", "LightningIndexer", "SparseFlashAttention"]),
])
def test_mla_sparse_and_cache_helpers_preserve_full_recorded_abi(capture, kinds):
    observed = rows(capture)
    assert [row.kind for row in observed] == kinds
    for row in observed:
        contract = native_tensor_contract(row)
        assert contract[0] == "native_tensor_abi"
        assert tuple(slot[0] for slot in contract[2]) == row.input_shapes
        assert tuple(slot[0] for slot in contract[3]) == row.output_shapes
        if row.kind not in {"SparseAttnSharedkv", "SparseFlashAttention",
                            "MlaPrologV3", "LightningIndexer"}:
            assert observed_attention_contract(row) == contract
    if capture == "dsv2lite_s1":
        assert native_tensor_contract(observed[1])[3][1] == ((), None, None)


def test_glm_sparse_attention_compares_latent_rope_and_cache_head_geometry():
    row = rows("a3_glm53")[2]
    query = ((4096, 8, 512), "bf16", "ND")
    cache = ((1, 512), "bf16", "ND")
    contract = observed_attention_contract(row)
    assert contract == (
        "sparse_attention_active", "SparseFlashAttention",
        (query, ((4096, 8, 64), "bf16", "ND")),
        (cache, cache, ((1, 64), "bf16", "ND")), query,
    )
    changed_heads = replace(
        row, input_shapes=((4096, 4, 512), *row.input_shapes[1:7],
                           (4096, 4, 64), row.input_shapes[8]),
        output_shapes=((4096, 4, 512), *row.output_shapes[1:]),
    )
    assert observed_attention_contract(changed_heads) != contract
    broken_rope = replace(row, input_shapes=(*row.input_shapes[:7], (4096, 8, 32),
                                            row.input_shapes[8]))
    assert observed_attention_contract(broken_rope)[0] == "native_tensor_abi"
    broken_layout = replace(row, input_formats=("NCL", *row.input_formats[1:]))
    assert observed_attention_contract(broken_layout)[0] == "native_tensor_abi"


def test_shared_kv_preserves_compressed_presence_but_excludes_indices_and_capacity():
    original = rows("a3_deepseek_v4f")[1]
    compressed, other_compressed = rows("a3_deepseek_v4f_compressed")
    query, cache = ((4096, 8, 512), "bf16", "ND"), ((1, 512), "bf16", "ND")
    assert observed_attention_contract(original) == (
        "sparse_attention_active", "SparseAttnSharedkv",
        (query,), (cache, ((), None, None)), query,
    )
    contract = observed_attention_contract(compressed)
    assert contract == (
        "sparse_attention_active", "SparseAttnSharedkv", (query,), (cache, cache), query,
    )
    assert observed_attention_contract(other_compressed) == contract
    assert native_tensor_contract(other_compressed) != native_tensor_contract(compressed)
    changed_capacity = replace(
        compressed, input_shapes=(compressed.input_shapes[0], (2000, 64, 1, 512),
                                  (500, 64, 1, 512), *compressed.input_shapes[3:]),
    )
    assert observed_attention_contract(changed_capacity) == contract
    assert native_tensor_contract(changed_capacity) != native_tensor_contract(compressed)
    scope = attention_contract_scope(compressed)
    assert "compressed_cache_presence" in scope["compared"]
    assert {"cache_capacity", "cache_block_size", "sparse_index_tensors",
            "compression_ratio", "mask_modes"} <= set(scope["not_compared"])
    assert observed_attention_contract(replace(compressed, duration_ns=1)) == contract
    different_width = replace(
        compressed, input_shapes=(*compressed.input_shapes[:2], (4260, 128, 1, 256),
                                  *compressed.input_shapes[3:]),
    )
    assert observed_attention_contract(different_width)[0] == "native_tensor_abi"


def test_kimi_a5_preserves_unequal_key_value_widths_and_mixed_dtype_mla():
    path = FIXTURE.parent / "body_attention/kimi_a5_full_model.csv"
    by_kind = {row.kind: row for row in kernel_rows(path)}
    attention = observed_attention_contract(by_kind["FusedInferAttentionScore"])
    assert attention == (
        "attention_active_qkv", "FusedInferAttentionScore",
        (((8192, 12, 192), "bf16", "ND"), ((8192, 12, 192), "bf16", "ND"),
         ((8192, 12, 128), "bf16", "ND")),
        (((8192, 12, 128), "bf16", "ND"),),
    )
    assert observed_attention_contract(by_kind["ScatterPaKvCache"]) == (
        "kv_cache_store_active_elements", "ScatterPaKvCache",
        ((4194304, "bf16"), (524288, "bf16")), (8192,),
    )
    mla = native_tensor_contract(by_kind["MlaPrologV3"])
    assert mla[2][0][1] == "fp8_e4m3"
    assert mla[2][8] == ((), "bf16", "ND")
    assert observed_attention_contract(by_kind["MlaPrologV3"])[0] == "mla_prolog_active"


def test_unknown_operator_and_unobserved_arity_do_not_gain_a_body_contract():
    row = rows("a5_qwen38")[1]
    assert observed_attention_contract(replace(row, kind="FutureAttentionKernel")) is None
    fewer = replace(row, input_shapes=row.input_shapes[:-1],
                    input_dtypes=row.input_dtypes[:-1], input_formats=row.input_formats[:-1])
    assert native_tensor_contract(fewer) is not None
    assert observed_attention_contract(fewer) is None
    assert attention_contract_diagnostic(fewer)["reason"] == "unsupported_native_tensor_slots"
