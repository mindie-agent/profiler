"""Native quantization and normalization-output contracts.

[Role] Keep dynamic INT8, MX quantization and RMS output variants distinct.
[Invariants] An optional affine input remains part of the contract when present.
  Auxiliary mask outputs do not identify dispatch or model-layer occurrence.
[Timeouts & Locks] Pure per-row checks; no locks or waits.
[Side-Effect Policy] No I/O, simulation import, hardware context or mutation.
"""
from __future__ import annotations


QUANT_FUSION_TYPES = {"DynamicQuant", "AddRmsNormDynamicQuant", "RmsNormCast"}
_FLOAT = {"bf16", "fp16"}
_EMPTY = ((), None, None)


def _issue(kind, reason, detail, missing=()):
    return {
        "category": "capture_metadata_missing" if missing else "contract_support_gap",
        "reason": reason, "detail": detail, "operator_type": kind,
        **({"missing_fields": list(missing)} if missing else {}),
    }


def quant_fusion_contract(native):
    _, kind, inputs, outputs = native
    arities = {"DynamicQuant": {(1, 2)}, "AddRmsNormDynamicQuant": {(3, 5), (4, 5)},
               "RmsNormCast": {(2, 2)}}
    if (len(inputs), len(outputs)) not in arities[kind]:
        return None, _issue(kind, "unsupported_native_tensor_slots",
                            "Captured slot counts do not match the retained native quantization ABI.")
    required_in = range(min(len(inputs), 3)) if kind == "AddRmsNormDynamicQuant" else range(len(inputs))
    required_out = (0, 2, 3) if kind == "AddRmsNormDynamicQuant" else (0, 1)
    missing = [f"input[{i}].shape" for i in required_in if not inputs[i][0]]
    missing += [f"output[{i}].shape" for i in required_out if not outputs[i][0]]
    if missing:
        return None, _issue(kind, "missing_active_tensor_shapes",
                            "Quantization input, result and scale shapes are required.", missing)
    x = inputs[0]
    if len(x[0]) != 2 or any(dim <= 0 for dim in x[0]) or x[1] not in _FLOAT or x[2] != "ND":
        return None, _issue(kind, "unsupported_quantization_geometry",
                            "The verified native projection requires a floating ND row/channel input.")
    rows, width = x[0]
    if kind == "RmsNormCast":
        if (inputs[1] != ((width,), x[1], "ND") or outputs[0] != x
                or outputs[1] != (x[0], "fp32", "ND")):
            return None, _issue(kind, "inconsistent_rmsnorm_cast_geometry",
                                "RmsNormCast must expose both the original-dtype and FP32 normalized outputs.")
        return native, None
    y, scale = (x[0], "int8", "ND"), ((rows,), "fp32", "ND")
    if kind == "DynamicQuant":
        if outputs != (y, scale):
            return None, _issue(kind, "inconsistent_dynamic_quant_geometry",
                                "The retained dynamic INT8 path requires one FP32 scale per input row.")
        return ("dynamic_quant_active", kind, x, y, scale), None
    optional = inputs[3] if len(inputs) == 4 else _EMPTY
    if (inputs[1] != x or inputs[2] != ((width,), x[1], "ND")
            or optional not in {_EMPTY, ((width,), x[1], "ND")}
            or (outputs[0], outputs[2], outputs[3]) != (y, x, scale)
            or outputs[1] != ((1,), "int8", "ND") or outputs[4] != ((1,), "fp32", "ND")):
        return None, _issue(
            kind, "inconsistent_add_rmsnorm_dynamic_quant_geometry",
            "The verified single-output-mask branch retains matching residual/weight "
            "geometry, optional affine input, INT8 result and per-row FP32 scales.")
    return ("add_rmsnorm_dynamic_quant_active", kind,
            (*inputs[:3], optional), (y, x, scale)), None


def quant_fusion_scope(kind):
    scope = {
        "occurrence_identity": False,
        "timing_scope": "inclusive_fused_subgraph; no_member_time_split",
        "unobserved": ["tensor_values", "scalar_dispatch_arguments", "module_or_layer_identity"],
        "not_compared": ["epsilon", "scale_values", "rounding_mode"],
    }
    if kind == "DynamicQuant":
        return {**scope, "kind": "dynamic_int8_tensor_descriptors",
                "compared": ["native_operator_type", "input_output_and_scale_slots"]}
    if kind == "RmsNormCast":
        return {**scope, "kind": "native_tensor_slots",
                "compared": ["native_operator_type", "all_input_and_output_slots"]}
    return {
        **scope, "kind": "add_rmsnorm_dynamic_int8_descriptors",
        "compared": ["native_operator_type", "input_residual_weight_optional_affine_slots",
                     "primary_quantized_residual_and_scale_slots"],
        "not_compared": [*scope["not_compared"], "auxiliary_mask_output_values"],
    }
