"""Source-defined attention and cache descriptor contracts.

[Role] Compare supported native ABIs and independently declared active tensors.
[Invariants] Active projections never identify phase, cache slot values, mask
  values or dispatch flags. Paged cache descriptors never become dense TND
  tensors by dividing dimensions or assuming a model's head configuration.
[Timeouts & Locks] Pure bounded tensor-slot inspection; no waits or locks.
[Side-Effect Policy] No I/O, model catalogue, hardware or simulation imports.
"""
from __future__ import annotations

from .native_tensor_abi import native_tensor_contract, native_tensor_diagnostic
from .body_subgraph_contracts import (
    SUBGRAPH_TYPES, subgraph_contract, subgraph_contract_scope,
)


# Arity variants come from retained original A3/A5 rows, including explicit
# undefined slots. Compact FIA captures retain the block-table as input 6.
_ARITIES = {
    "FusedInferAttentionScore": ({6, 7, 31}, {2}),
    "ReshapeAndCacheNdKernel": ({5}, {2}),
    "ScatterPaKvCache": ({5, 8}, {2}),
    "KvRmsNormRopeCache": ({12}, {4}),
    "PagedCacheLoadNdKernel": ({7}, {2}),
    "RINGMLAPrefillBF16Kernel": ({15}, {2}),
    "SparseAttnSharedkv": ({14}, {2}),
    "ScatterNdUpdateSk": ({3}, {1}),
    "LightningIndexer": ({6}, {2}),
    "SparseFlashAttention": ({9}, {3}),
    "MlaPrologV3": ({21}, {7}),
    "ChunkGatedDeltaRuleFwd": ({9, 10}, {4}),
    "RecurrentGatedDeltaRule": ({9, 10}, {2}),
}
ATTENTION_CACHE_TYPES = frozenset(_ARITIES)


def _native(row):
    contract = native_tensor_contract(row)
    if contract is None or row.kind not in _ARITIES:
        return None
    inputs, outputs = contract[2:]
    expected_inputs, expected_outputs = _ARITIES[row.kind]
    if len(inputs) not in expected_inputs or len(outputs) not in expected_outputs:
        return None
    return contract


def _dense_fia(inputs, outputs):
    # Full FIA input14 is the block table; the compact six-slot export has
    # Q/K/V, mask, q lengths and kv lengths. The seventh compact slot is paged.
    dense = len(inputs) == 6 or (
        len(inputs) == 31 and inputs[14] == ((), None, None))
    active = (*inputs[:3], outputs[0])
    if not dense or any(len(shape) != 3 or layout != "ND" for shape, _, layout in active):
        return None
    q, k, v, out = (slot[0] for slot in active)
    if (any(value <= 0 for shape in (q, k, v, out) for value in shape)
            or k[:2] != v[:2] or q[-1] != k[-1]
            or out != (q[0], q[1], v[-1])
            or len({slot[1] for slot in active}) != 1):
        return None
    return ("attention_active_qkv", "FusedInferAttentionScore", inputs[:3], outputs[:1])


def _paged_fia(inputs, outputs):
    # attention_v1._get_fia_params views (pages, block, KVheads, dim) as
    # (pages, block, packed_width). Preserve the packed width without dividing
    # it by the query width: GQA's KV-head count is a separate caller argument.
    if len(inputs) not in {7, 31}:
        return None
    query, key, value, output = *inputs[:3], outputs[0]
    table = inputs[6 if len(inputs) == 7 else 14]
    floating = {"bf16", "fp16"}
    if (not all(_nd_tensor(slot, 3, floating) for slot in (query, key, value, output))
            or not _nd_tensor(table, 2, {"int32"})
            or key[0][:2] != value[0][:2] or output != query
            or len({slot[1] for slot in (query, key, value, output)}) != 1):
        return None
    tails = tuple((slot[0][1:], slot[1], slot[2]) for slot in (key, value))
    return ("attention_paged_active_qkv", "FusedInferAttentionScore",
            query, tails, output, table[0][0])


def _reshape_cache(inputs, outputs):
    key, value, key_cache, value_cache, slots = inputs
    if (len(key[0]) != 3 or len(value[0]) != 3 or key[0] != value[0]
            or len(key_cache[0]) != 4 or len(value_cache[0]) != 4
            or key_cache[0][2:] != key[0][1:] or value_cache[0][2:] != value[0][1:]
            or slots[0] != (key[0][0],) or slots[1] not in {"int32", "int64"}
            or any(slot[2] != "ND" for slot in (*inputs, *outputs))
            or outputs != (key_cache, value_cache)
            or len({slot[1] for slot in (key, value, key_cache, value_cache)}) != 1):
        return None
    return ("kv_cache_store_active", "ReshapeAndCacheNdKernel", inputs[:2],
            slots, tuple(slot[1:] for slot in (key_cache, value_cache)))


def _scatter_cache(inputs, outputs):
    # CANN's operator graph orders key, keyCacheRef, slotMapping, value,
    # valueCacheRef, unlike the public PyTorch wrapper's argument order.
    key, key_cache, slots, value, value_cache = inputs[:5]
    if (len(key[0]) != 1 or len(value[0]) != 1 or len(slots[0]) != 1
            or not slots[0][0] or key[0][0] <= 0 or value[0][0] <= 0
            or key[0][0] % slots[0][0] or value[0][0] % slots[0][0]
            or tuple(slot[2] for slot in inputs[:5]) != ("NCL", "NCHW", "ND", "NCL", "NCHW")
            or outputs != (key_cache, value_cache)
            or key[1] != key_cache[1] or value[1] != value_cache[1]
            or slots[1] not in {"int32", "int64"}):
        return None
    return ("kv_cache_store_active_elements", "ScatterPaKvCache",
            ((key[0][0], key[1]), (value[0][0], value[1])), slots[0])


def _nd_tensor(slot, rank, dtypes):
    shape, dtype, layout = slot
    return (len(shape) == rank and all(value > 0 for value in shape)
            and dtype in dtypes and layout == "ND")


def _sparse_attention(kind, inputs, outputs):
    floating = {"bf16", "fp16"}
    query, output = inputs[0], outputs[0]
    if (not _nd_tensor(query, 3, floating) or output != query):
        return None
    if kind == "SparseFlashAttention":
        key, value, rope, key_rope = inputs[1], inputs[2], inputs[7], inputs[8]
        # PA_BSND is (block_count, block_size, heads, dim); TND query keeps
        # its native axes. A recorded block table establishes the paged ABI.
        if (not all(_nd_tensor(slot, 4, floating) for slot in (key, value, key_rope))
                or not _nd_tensor(rope, 3, floating)
                or not _nd_tensor(inputs[4], 2, {"int32"})
                or key != value or key[0][-1] != query[0][-1]
                or key_rope[0][:3] != key[0][:3]
                or rope[0][:2] != query[0][:2]
                or rope[0][-1] != key_rope[0][-1]
                or rope[1] != query[1] or key_rope[1] != key[1]):
            return None
        caches = tuple((slot[0][2:], slot[1], slot[2]) for slot in (key, value, key_rope))
        return ("sparse_attention_active", kind, (query, rope), caches, output)
    original, compressed = inputs[1:3]
    empty = ((), None, None)
    # SharedKV uses PA_ND with the same final (heads, dim) axes. Presence of
    # the compressed tensor remains part of the contract, independent of size.
    if (not _nd_tensor(original, 4, floating)
            or original[0][-1] != query[0][-1]
            or not _nd_tensor(inputs[5], 2, {"int32"})):
        return None
    original_head = (original[0][2:], original[1], original[2])
    if compressed == empty:
        if inputs[6] != empty:
            return None
        compressed_head = empty
    else:
        if (not _nd_tensor(compressed, 4, floating)
                or not _nd_tensor(inputs[6], 2, {"int32"})
                or (compressed[0][2:], compressed[1:]) != (original[0][2:], original[1:])):
            return None
        compressed_head = (compressed[0][2:], compressed[1], compressed[2])
    return ("sparse_attention_active", kind, (query,), (original_head, compressed_head), output)


def observed_attention_contract(row):
    native = _native(row)
    if native is None:
        return None
    if row.kind in SUBGRAPH_TYPES:
        return subgraph_contract(native)[0]
    inputs, outputs = native[2:]
    if row.kind == "FusedInferAttentionScore":
        return _dense_fia(inputs, outputs) or _paged_fia(inputs, outputs) or native
    if row.kind == "ReshapeAndCacheNdKernel":
        return _reshape_cache(inputs, outputs) or native
    if row.kind == "ScatterPaKvCache":
        return _scatter_cache(inputs, outputs) or native
    if row.kind in {"SparseFlashAttention", "SparseAttnSharedkv"}:
        return _sparse_attention(row.kind, inputs, outputs) or native
    return native


def attention_contract_scope(row):
    if row.kind in SUBGRAPH_TYPES:
        return subgraph_contract_scope(row)
    contract = observed_attention_contract(row)
    if contract is None:
        return None
    common = {
        "occurrence_identity": False,
        "unobserved": ["tensor_values", "scalar_dispatch_arguments", "selected_tiling",
                       "module_or_layer_identity"],
    }
    if contract[0] == "attention_active_qkv":
        return {
            **common, "kind": "active_attention_tensor_descriptors",
            "compared": ["query_shape_dtype_format", "key_shape_dtype_format",
                         "value_shape_dtype_format", "main_output_shape_dtype_format"],
            "not_compared": ["mask_descriptor_and_values", "sequence_length_arrays",
                             "optional_auxiliary_tensors", "scale", "sparse_mode",
                             "causal_flag", "logical_input_layout", "phase"],
            "storage_boundary": "nonpaged_qkv_descriptors",
        }
    if contract[0] == "attention_paged_active_qkv":
        return {
            **common, "kind": "active_paged_attention_tensor_descriptors",
            "compared": ["native_operator_type", "query_shape_dtype_format",
                         "cache_block_size_packed_row_width_dtype_format",
                         "main_output_shape_dtype_format", "block_table_batch_count"],
            "not_compared": ["cache_capacity", "block_table_column_count_and_values",
                             "sequence_length_array_values", "kv_head_factorization",
                             "mask_descriptor_and_values", "optional_auxiliary_tensors",
                             "scale", "sparse_mode", "causal_flag", "logical_input_layout",
                             "phase", "context_length", "verify_or_draft_role"],
            "storage_boundary": "paged_BSH_cache_and_TND_query_descriptors",
            "conditions": "Execution geometry and context require an independent declaration; "
                          "query token count does not identify a verify or draft invocation.",
        }
    if contract[0] == "kv_cache_store_active":
        return {
            **common, "kind": "active_cache_store_tensor_descriptors",
            "compared": ["key_shape_dtype_format", "value_shape_dtype_format",
                         "slot_mapping_shape_dtype_format", "cache_dtype_format"],
            "not_compared": ["cache_capacity", "slot_mapping_values", "cache_block_size",
                             "cache_mode", "compression_scalar_arguments"],
        }
    if contract[0] == "kv_cache_store_active_elements":
        return {
            **common, "kind": "active_cache_store_elements",
            "compared": ["key_element_count_dtype", "value_element_count_dtype",
                         "slot_mapping_shape"],
            "validated_capture_abi": "flattened_NCL_key_value_NCHW_cache_ND_slots",
            "not_compared": ["native_storage_layout", "head_shape_factorization",
                             "cache_capacity", "cache_block_size", "slot_mapping_dtype",
                             "slot_mapping_values", "cache_mode", "compression_scalar_arguments"],
        }
    if contract[0] == "sparse_attention_active":
        return {
            **common, "kind": "active_sparse_attention_tensor_descriptors",
            "compared": ["native_operator_type", "query_shape_dtype_format",
                         "query_rope_shape_dtype_format_when_present",
                         "cache_head_shape_dtype_format", "compressed_cache_presence",
                         "main_output_shape_dtype_format"],
            "validated_capture_abi": "ND_query_rank3_and_paged_cache_rank4_with_block_table",
            "not_compared": ["cache_capacity", "cache_block_size", "block_table_shape_and_values",
                             "sequence_length_tensors", "sparse_index_tensors", "sink_tensor",
                             "metadata_tensor", "compression_ratio", "kv_strides",
                             "mask_modes", "attention_window", "logical_input_layout",
                             "scale", "auxiliary_outputs", "phase"],
        }
    return {
        **common, "kind": "native_tensor_abi",
        "compared": ["all_ordered_tensor_shapes", "all_tensor_dtypes", "all_tensor_formats"],
        "not_compared": ["block_table_values", "slot_mapping_values", "sequence_length_values",
                         "cache_mode", "scale", "sparse_mode", "logical_input_layout"],
    }


def attention_contract_diagnostic(row):
    if native_tensor_contract(row) is None:
        return native_tensor_diagnostic(row)
    if _native(row) is None:
        return {
            "category": "contract_support_gap", "reason": "unsupported_native_tensor_slots",
            "detail": "This attention/cache ABI arity has no source-backed contract.",
            "operator_type": row.kind,
        }
    if row.kind in SUBGRAPH_TYPES:
        _, issue = subgraph_contract(_native(row))
        if issue is not None:
            return issue
    return {
        "category": "tensor_contract_available", "reason": "observed_tensor_contract_available",
        "detail": "The compared descriptor scope is explicit; occurrence evidence remains independent.",
        "operator_type": row.kind,
    }
