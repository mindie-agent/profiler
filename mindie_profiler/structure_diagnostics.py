"""Explain unmatched contracts without promoting similarities into mappings.

[Role] Separate absent capture evidence, unsupported contracts and declarations.
[Invariants] Near contracts are explanations only, never occurrence candidates.
  Geometry cannot establish phase, layer, draft ownership or actual dispatch.
[Timeouts & Locks] Pure bounded comparisons over distinct declared contracts.
[Side-Effect Policy] No I/O, model imports or mutations.
"""
from __future__ import annotations

FIELDS = {
    "matrix": ("family", "geometry", "input_dtype", "weight_dtype", "output_dtype",
               "scale_shape", "scale_dtype"),
    "matrix_bias": ("family", "geometry", "input_dtype", "weight_dtype", "output_dtype",
                    "bias_shape", "bias_dtype"),
    "grouped_matrix": ("family", "geometry", "input_dtype", "weight_dtype", "output_dtype",
                       "scale_shape", "scale_dtype"),
    "slice_copy": ("family", "input_shape", "output_shape", "input_dtype", "output_dtype"),
    "rmsnorm": ("family", "shape", "dtype", "has_weight"),
    "add_rmsnorm": ("family", "shape", "dtype", "has_weight"),
    "DynamicMxQuant": ("family", "shape", "input_dtype", "output_dtype", "scale_shape", "scale_dtype"),
    "AddRmsNormDynamicMxQuant": (
        "family", "shape", "input_dtype", "output_dtype", "scale_shape", "scale_dtype"),
    "native_tensor_abi": ("family", "native_operator", "input_slots", "output_slots"),
    "attention_active_qkv": ("family", "native_operator", "qkv_slots", "main_output_slots"),
    "kv_cache_store_active": ("family", "native_operator", "kv_slots", "slot_mapping",
                              "cache_dtypes_layouts"),
    "kv_cache_store_active_elements": ("family", "native_operator", "kv_elements_dtype",
                                      "slot_mapping_shape"),
    "sparse_attention_active": ("family", "native_operator", "query_slots",
                                "cache_head_slots", "output_slot"),
    "gated_norm_active_rows": ("family", "native_operator", "rows_slot", "weight_slot"),
    "lightning_indexer_active": ("family", "native_operator", "query_and_weight_slots",
                                "key_cache_head_slot", "sparse_index_output_slot"),
    "mla_prolog_active": ("family", "native_operator", "token_rows_slot",
                         "parameter_shape_dtype_slots", "cache_head_slots", "output_slots"),
    "quant_lightning_indexer_active": (
        "family", "native_operator", "query_weight_scale_slots",
        "key_cache_and_scale_head_slots", "sparse_index_output_slot"),
    "hyper_connection_active": (
        "family", "native_operator", "canonical_input_slots", "primary_output_slots"),
    "compressor_active": (
        "family", "native_operator", "token_slot", "parameter_slots",
        "state_channel_slot", "rope_width_slots", "output_width_slot"),
    "recurrent_kda_parameters_active": (
        "family", "native_operator", "gate_beta_parameter_slots",
        "qkv_dtype_format", "state_dtype_format", "output_dtype_format"),
    "grouped_mlp_parameters_active": (
        "family", "native_operator", "expert_and_channel_geometry", "input_weight_output_dtypes"),
    "dequant_swiglu_quant_active": (
        "family", "native_operator", "input_slot", "weight_scale_slot", "token_scale_slot",
        "output_slot", "output_scale_slot"),
    "rmsnorm_mxquant_active": (
        "family", "native_operator", "input_slot", "weight_slot", "output_slot", "scale_slot"),
    "dynamic_quant_active": (
        "family", "native_operator", "input_slot", "output_slot", "scale_slot"),
    "add_rmsnorm_dynamic_quant_active": (
        "family", "native_operator", "input_residual_weight_affine_slots", "primary_output_slots"),
    "layernorm_active": (
        "family", "native_operator", "input_slot", "weight_slot", "bias_slot", "output_slot"),
    "transpose_batchmatmul_active": (
        "family", "native_operator", "batch_geometry", "input_dtype", "weight_dtype", "output_dtype"),
    "router_selection_active": (
        "family", "native_operator", "selection_mode", "logits_slot", "weights_slot", "indices_slot"),
}
NATIVE_FAMILIES = {
    "native_tensor_abi", "attention_active_qkv", "kv_cache_store_active",
    "kv_cache_store_active_elements",
    "sparse_attention_active", "gated_norm_active_rows",
    "lightning_indexer_active", "mla_prolog_active",
    "quant_lightning_indexer_active", "hyper_connection_active", "compressor_active",
    "recurrent_kda_parameters_active",
    "grouped_mlp_parameters_active", "dequant_swiglu_quant_active", "rmsnorm_mxquant_active",
    "dynamic_quant_active", "add_rmsnorm_dynamic_quant_active",
    "layernorm_active", "transpose_batchmatmul_active",
    "router_selection_active",
}


def mismatch_diagnostic(contract, declared):
    family = contract[0]
    same_family = [
        other for other in declared if other[0] == family
        and (family not in NATIVE_FAMILIES or other[1] == contract[1])
    ]
    if not same_family:
        return {
            "category": "declared_structure_mismatch",
            "reason": "declared_operator_family_absent",
            "detail": "No declared contract in the selected rank/scope has this operator family.",
        }
    # Exact equality is handled by the mapper. These comparisons only explain
    # which declaration needs inspection; no nearest node is ever selected.
    names = FIELDS.get(family, ("family", "shape"))
    differences = []
    for other in same_family:
        fields = [names[index] if index < len(names) else f"field_{index}"
                  for index in range(max(len(contract), len(other)))
                  if index >= len(contract) or index >= len(other) or contract[index] != other[index]]
        differences.append((fields, other))
    differences.sort(key=lambda pair: len(pair[0]))
    best = differences[0][0]
    same_geometry = [fields for fields, other in differences if other[1] == contract[1]]
    precision_fields = {
        "input_dtype", "weight_dtype", "output_dtype", "bias_dtype", "scale_shape", "scale_dtype",
    }
    if family in {"matrix", "matrix_bias", "grouped_matrix"} and any(
        fields and set(fields) <= precision_fields for fields in same_geometry
    ):
        reason = "declared_dtype_or_quantization_mismatch"
    elif any(field in best for field in ("geometry", "shape", "input_shape", "output_shape")):
        reason = "declared_geometry_or_scope_mismatch"
    else:
        reason = "declared_tensor_descriptor_mismatch"
    return {
        "category": "declared_structure_mismatch", "reason": reason,
        "detail": ("Compare the selected execution geometry, precision and scope with the capture; "
                   "tensor descriptors alone do not establish prefill/decode or draft ownership."),
        "near_contracts": [
            {"contract": other, "differing_fields": fields}
            for fields, other in differences[:3]
        ],
    }
