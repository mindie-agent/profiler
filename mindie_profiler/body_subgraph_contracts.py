"""Native attention preprocessing and index-selection subgraph contracts.

[Role] Project source-defined fused boundaries onto independently declared DAGs.
[Invariants] A fused event covers its members inclusively, never their separate
  timings. Native types, parameter geometry and dtype remain distinct. Only
  documented MLA leading token axes may be combined; values and flags are unknown.
[Timeouts & Locks] Pure work over one bounded native tensor descriptor.
[Side-Effect Policy] No I/O, hardware, model catalogue or simulation imports.
"""
import math


SUBGRAPH_TYPES = {"MlaPrologV3", "LightningIndexer"}
_FLOAT = {"bf16", "fp16"}
_ACTIVATION = _FLOAT | {"int8", "fp8_e4m3"}
_EMPTY = ((), None, None)


def _tensor(slot, rank, dtypes, formats=("ND",)):
    shape, dtype, layout = slot
    return (len(shape) == rank and all(dim > 0 for dim in shape)
            and dtype in dtypes and layout in formats)


def _issue(kind, reason, detail, missing=()):
    return {
        "category": "capture_metadata_missing" if missing else "contract_support_gap",
        "reason": reason, "detail": detail, "operator_type": kind,
        **({"missing_fields": list(missing)} if missing else {}),
    }


def _lightning(inputs, outputs):
    kind = "LightningIndexer"
    required = (("input[0].shape", inputs[0]), ("input[1].shape", inputs[1]),
                ("input[2].shape", inputs[2]), ("output[0].shape", outputs[0]))
    missing = [name for name, slot in required if not slot[0]]
    if missing:
        return None, _issue(kind, "missing_active_tensor_shapes",
                            "Indexer Q, key, weights and index output shapes are required.", missing)
    query, cache, weights = inputs[:3]
    indices = outputs[0]
    if (not _tensor(query, 3, _FLOAT) or not _tensor(cache, 4, _FLOAT)
            or not _tensor(weights, 2, _FLOAT | {"fp32"})
            or not _tensor(inputs[5], 2, {"int32"})
            or not _tensor(indices, 3, {"int32"})
            or weights[0] != query[0][:2]
            or query[0][-1] != cache[0][-1] or query[1] != cache[1]
            or indices[0][:2] != (query[0][0], cache[0][2])):
        return None, _issue(
            kind, "unsupported_indexer_active_geometry",
            "The verified index-selection boundary requires TND Q, paged ND K, "
            "per-token/head weights, a block table and INT32 sparse-index output.")
    cache_head = (cache[0][2:], cache[1], cache[2])
    return ("lightning_indexer_active", kind, (query, weights), cache_head, indices), None


def _mla(inputs, outputs):
    kind = "MlaPrologV3"
    required = [(f"input[{i}].shape", inputs[i]) for i in (*range(7), 9, 10)]
    required += [(f"output[{i}].shape", outputs[i]) for i in range(4)]
    missing = [name for name, slot in required if not slot[0]]
    if missing:
        return None, _issue(kind, "missing_active_tensor_shapes",
                            "MLA token, parameters, cache and primary Q outputs are required.", missing)
    token = inputs[0]
    dq, uq, uk, dkv, gamma_q, gamma_kv = inputs[1:7]
    query, rope = outputs[:2]
    cache, rope_cache = inputs[9:11]
    if (len(token[0]) not in {2, 3}
            or not _tensor(token, len(token[0]), _ACTIVATION)
            or not all(_tensor(slot, 2, _ACTIVATION, ("FRACTAL_NZ",))
                       for slot in (dq, uq, dkv))
            or not _tensor(uk, 3, _FLOAT)
            or not all(_tensor(slot, 1, _FLOAT) for slot in (gamma_q, gamma_kv))
            or not all(_tensor(slot, 4, _FLOAT) for slot in (cache, rope_cache))
            or not _tensor(query, len(token[0]) + 1, _FLOAT)
            or not _tensor(rope, len(token[0]) + 1, _FLOAT)):
        return None, _issue(
            kind, "unsupported_mla_active_geometry",
            "The verified MLA projection requires logical NZ matrix descriptors, "
            "ND parameters, floating paged caches and complete token/Q axes.")
    leading = token[0][:-1]
    tokens, hidden = math.prod(leading), token[0][-1]
    heads, nope, latent = uk[0]
    rope_width = rope[0][-1]
    if (dq[0] != (hidden, gamma_q[0][0])
            or uq[0] != (gamma_q[0][0], heads * (nope + rope_width))
            or dkv[0] != (hidden, latent + rope_width)
            or gamma_kv[0] != (latent,)
            or query[0] != (*leading, heads, latent)
            or rope[0] != (*leading, heads, rope_width)
            or cache[0][2:] != (1, latent) or rope_cache[0][2:] != (1, rope_width)
            or outputs[2:4] != (cache, rope_cache)
            or len({slot[1] for slot in (uk, gamma_q, gamma_kv, query, rope,
                                         cache, rope_cache)}) != 1):
        return None, _issue(
            kind, "inconsistent_mla_active_parameters",
            "MLA projection, RMS, absorption, output and cache dimensions do not agree.")
    query_norm = outputs[5]
    if query_norm[0]:
        if (query_norm[0] not in {(tokens, gamma_q[0][0]), (*leading, gamma_q[0][0])}
                or not _tensor(query_norm, len(query_norm[0]), _ACTIVATION)):
            return None, _issue(kind, "unsupported_mla_query_norm",
                                "The recorded optional query-norm output must retain its row/rank axes.")
        query_norm = ((tokens, gamma_q[0][0]), query_norm[1], query_norm[2])
    else:
        # Both optional outputs are empty in the source's query_norm_flag=false
        # path. A scale with no corresponding data is incomplete capture evidence.
        if outputs[6][0]:
            return None, _issue(kind, "missing_active_tensor_shapes",
                                "Query-norm scale is present but its data shape is absent.",
                                ("output[5].shape",))
        query_norm = _EMPTY
    parameters = tuple((slot[0], slot[1]) for slot in inputs[1:7])
    cache_heads = tuple((slot[0][2:], slot[1], slot[2]) for slot in (cache, rope_cache))
    output_slots = (((tokens, heads, latent), query[1], query[2]),
                    ((tokens, heads, rope_width), rope[1], rope[2]), query_norm)
    return ("mla_prolog_active", kind, ((tokens, hidden), token[1], token[2]),
            parameters, cache_heads, output_slots), None


def subgraph_contract(native):
    """Return (active contract, issue) after native slot cardinality validation."""
    _, kind, inputs, outputs = native
    return _mla(inputs, outputs) if kind == "MlaPrologV3" else _lightning(inputs, outputs)


def subgraph_contract_scope(row):
    common = {
        "occurrence_identity": False,
        "unobserved": ["tensor_values", "scalar_dispatch_arguments", "selected_tiling",
                       "module_or_layer_identity"],
        "timing_scope": "inclusive_fused_subgraph; no_member_time_split",
    }
    if row.kind == "LightningIndexer":
        return {
            **common, "kind": "active_indexer_selection_descriptors",
            "compared": ["native_operator_type", "query_shape_dtype_format",
                         "weights_shape_dtype_format", "key_cache_head_shape_dtype_format",
                         "sparse_index_output_shape_dtype_format"],
            "not_compared": ["cache_capacity", "cache_block_size", "block_table_shape_and_values",
                             "sequence_length_tensors", "sparse_values_output", "sparse_mode",
                             "attention_window", "logical_input_layout", "phase"],
            "excluded_semantic_work": ["query_projection", "weight_projection", "index_cache_build"],
        }
    shapes = row.input_shapes or ()
    missing_auxiliary = [f"input[{i}].shape" for i in (7, 8)
                         if i >= len(shapes) or not shapes[i]]
    return {
        **common, "kind": "active_mla_prolog_descriptors",
        "compared": ["native_operator_type", "token_rows_hidden_dtype_format",
                     "projection_absorption_and_rms_parameter_shapes_dtypes",
                     "cache_head_shape_dtype_format", "query_and_query_rope_rows_heads_dims_dtypes",
                     "optional_query_norm_descriptor_presence_shape_dtype"],
        "not_compared": ["leading_token_axis_grouping", "parameter_physical_storage_layout",
                         "rope_input_tensors", "quantization_scale_tensors", "quantization_scalar_modes",
                         "epsilon", "query_key_scale", "cache_capacity", "cache_block_size",
                         "cache_index_tensor", "clip_and_smooth_values", "phase"],
        "excluded_capture_missing_fields": missing_auxiliary,
        "optional_query_norm_limit": "Empty recorded outputs are compared; the scalar flag is not observed.",
    }
