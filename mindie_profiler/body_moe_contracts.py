"""Tensor contracts for grouped FFN implementations and quantized epilogues.

[Role] Retain native fusion identity while comparing independent channel geometry.
[Invariants] Actual routed token counts are not an expected routing distribution.
  Packed weights remain native evidence; descriptor projection does not prove
  dispatch flags, scale values, expert selection or a model occurrence.
[Timeouts & Locks] Pure bounded per-row work; no locks or waits.
[Side-Effect Policy] No I/O, hardware contexts, simulation imports or mutations.
"""
from __future__ import annotations

import math


MOE_FUSION_TYPES = {
    "GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2",
    "GroupedMatmulSituQuant", "DequantSwigluQuant", "RmsNormDynamicMxQuant",
}
_EMPTY = ((), None, None)


def _issue(kind, reason, detail):
    return {"category": "contract_support_gap", "reason": reason, "detail": detail,
            "operator_type": kind}


def _tensor(slot, rank, dtypes, layout="ND"):
    return (len(slot[0]) == rank and all(dim > 0 for dim in slot[0])
            and slot[1] in dtypes and slot[2] == layout)


def _missing(kind, inputs, outputs, ins, outs):
    fields = [f"input[{i}].shape" for i in ins if not inputs[i][0]]
    fields += [f"output[{i}].shape" for i in outs if not outputs[i][0]]
    return ({
        "category": "capture_metadata_missing", "reason": "missing_active_tensor_shapes",
        "operator_type": kind, "missing_fields": fields,
        "detail": "The compared grouped-FFN/epilogue tensor shapes are absent.",
    } if fields else None)


def _grouped(kind, inputs, outputs):
    expected = 5 if kind == "GroupedMatmulSwigluQuant" else 6
    if len(inputs) != expected or len(outputs) != 2:
        return None, _issue(kind, "unsupported_native_tensor_slots",
                            "Only the retained single stacked expert-weight ABI is supported.")
    missing = _missing(kind, inputs, outputs, range(expected), range(2))
    if missing:
        return None, missing
    x, result, out_scale = inputs[0], outputs[0], outputs[1]
    if kind == "GroupedMatmulSwigluQuant":
        weight, weight_scale, x_scale, groups = inputs[1:]
    else:
        x_scale, groups, weight, weight_scale, assist = inputs[1:]
        if assist[0] != weight_scale[0] or assist[1:] != ("fp32", "ND"):
            return None, _issue(kind, "unsupported_grouped_assistance_geometry",
                                "The retained W4A8 implementation requires per-expert/channel assistance.")
    if (not _tensor(x, 2, {"int8"}) or not _tensor(result, 2, {"int8"})
            or x[0][0] != result[0][0] or not _tensor(groups, 1, {"int64"})
            or x_scale != ((x[0][0],), "fp32", "ND") or out_scale != x_scale
            or not _tensor(weight, 5, {"int8", "DT_INT4"}, "FRACTAL_NZ")
            or weight[0][0] != groups[0][0]
            or not _tensor(weight_scale, 2, {"fp32", "bf16", "fp16", "UINT64", "DT_UINT64"})
            or weight_scale[0] != (groups[0][0], 2 * result[0][1])
            or math.prod(weight[0][1:]) != x[0][1] * 2 * result[0][1]):
        return None, _issue(
            kind, "unsupported_grouped_mlp_parameter_geometry",
            "Input/output channels, expert bank, packed weight element count and "
            "per-token/per-channel scales must describe the verified grouped SwiGLU ABI.")
    weight_dtype = "int4" if weight[1] == "DT_INT4" else weight[1]
    return ("grouped_mlp_parameters_active", kind,
            (groups[0][0], x[0][1], result[0][1]),
            (x[1], weight_dtype, result[1])), None


def _dequant_swiglu(kind, inputs, outputs):
    if len(inputs) != 7 or len(outputs) != 2:
        return None, _issue(kind, "unsupported_native_tensor_slots",
                            "The verified dequantize/SwiGLU/quantize ABI has seven inputs and two outputs.")
    missing = _missing(kind, inputs, outputs, range(3), range(2))
    if missing:
        return None, missing
    x, w_scale, x_scale = inputs[:3]
    result, scale = outputs
    if any(slot != _EMPTY for slot in inputs[3:]):
        return None, _issue(
            kind, "dequant_swiglu_optional_boundary_unsupported",
            "Bias, explicit quantization scales/offsets or grouped indices select "
            "a different epilogue boundary from the retained dynamic-quantization path.")
    if (not _tensor(x, 2, {"int32"}) or not _tensor(result, 2, {"int8"})
            or x[0] != (result[0][0], result[0][1] * 2)
            or w_scale != ((x[0][1],), "fp32", "ND")
            or x_scale != ((x[0][0],), "fp32", "ND") or scale != x_scale):
        return None, _issue(kind, "unsupported_dequant_swiglu_geometry",
                            "The verified epilogue halves the channel width and retains per-row scales.")
    return ("dequant_swiglu_quant_active", kind, x, w_scale, x_scale, result, scale), None


def _rmsnorm_mxquant(kind, inputs, outputs):
    if len(inputs) != 2 or len(outputs) != 3:
        return None, _issue(kind, "unsupported_native_tensor_slots",
                            "The retained RMS/MX quantization ABI has two inputs and three outputs.")
    missing = _missing(kind, inputs, outputs, range(2), range(2))
    if missing:
        return None, missing
    x, gamma = inputs
    result, scale, auxiliary = outputs
    if (not _tensor(x, 2, {"bf16", "fp16"})
            or gamma != ((x[0][-1],), x[1], "ND")
            or result != (x[0], "fp8_e4m3", "ND")
            or x[0][-1] % 64 or scale != ((x[0][0], x[0][1] // 64, 2), "fp8_e8m0", "NCL")
            or auxiliary[0]):
        return None, _issue(
            kind, "unsupported_rmsnorm_mxquant_geometry",
            "The retained path exposes one FP8 output and E8M0 paired scales, "
            "with matching RMS weight and no materialized auxiliary output.")
    return ("rmsnorm_mxquant_active", kind, x, gamma, result, scale), None


def moe_fusion_contract(native):
    _, kind, inputs, outputs = native
    if kind in {"GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"}:
        return _grouped(kind, inputs, outputs)
    if kind == "DequantSwigluQuant":
        return _dequant_swiglu(kind, inputs, outputs)
    if kind == "RmsNormDynamicMxQuant":
        return _rmsnorm_mxquant(kind, inputs, outputs)
    return None, _issue(
        kind, "native_implementation_abi_unverified",
        "The retained native GroupedMatmulSituQuant name has no verified local "
        "implementation schema. It is not aliased to grouped SwiGLU quantization.")


def moe_fusion_scope(kind):
    common = {
        "occurrence_identity": False,
        "timing_scope": "inclusive_fused_subgraph; no_member_time_split",
        "unobserved": ["tensor_values", "scalar_dispatch_arguments", "module_or_layer_identity"],
    }
    if kind in {"GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"}:
        return {
            **common, "kind": "grouped_mlp_channel_and_precision_descriptors",
            "compared": ["native_operator_type", "expert_bank_size", "input_output_channels",
                         "input_weight_output_dtypes"],
            "not_compared": ["routed_token_count", "expert_group_sizes_and_indices",
                             "weight_packing", "quantization_scale_representation",
                             "quantization_scale_values", "activation_variant_and_limit",
                             "transpose_and_dequantization_flags"],
            "excluded_semantic_work": ["routing", "expert_down_projection", "combine"],
        }
    if kind == "DequantSwigluQuant":
        return {
            **common, "kind": "dequant_swiglu_quant_tensor_descriptors",
            "compared": ["native_operator_type", "input_output_slots", "weight_and_token_scale_slots"],
            "not_compared": ["activation_side", "activation_variant_and_limit", "rounding_mode",
                             "quantization_scale_values"],
            "excluded_semantic_work": ["input_matrix_multiplication"],
        }
    if kind == "RmsNormDynamicMxQuant":
        return {
            **common, "kind": "rmsnorm_mxquant_tensor_descriptors",
            "compared": ["native_operator_type", "input_weight_output_and_scale_slots"],
            "not_compared": ["epsilon", "rounding_mode", "scale_values", "auxiliary_output"],
        }
    return {
        **common, "kind": "native_implementation_boundary_only", "compared": [],
        "not_compared": ["native_implementation_abi", "active_tensor_geometry"],
    }
