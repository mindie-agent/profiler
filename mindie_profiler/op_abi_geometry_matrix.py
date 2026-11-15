"""Strict native dense/quantized/grouped matrix geometry.

[Role]
  Decode ``MatMul``/``BatchMatMul``/``QuantBatchMatmul`` and ``GroupedMatmul``
  descriptors into formula parameters.  Native quantization is never discarded:
  a ``QuantBatchMatmulV3`` row binds to the quantized family, requires its scale
  buffer and validates the declared activation/weight storage contract; a
  grouped row propagates its weight dtype so INT4 weights cannot be priced as
  BF16.

[Invariants]
  * Right-aligned broadcast prefixes are resolved axis by axis.
  * K, N and the exact output shape are checked before a card is certified.
  * Quantized native rows require a supported scale/quant contract and fail
    closed otherwise; no dense fallback is invented.
  * Grouped K/N and the weight dtype are preserved into the formula builder.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to the declared axes; no I/O.

[Side-Effect Policy]
  No mutation of the input row or slots; returns fresh params mappings.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_geometry_common import (
    _bool_attr, _capture_ints, _int_attr, _present, require_dtype, require_output,
    require_slot,
)
from mindie_profiler.op_abi_slots import AbiError, Slot

from mindie_sim.op_formulas.hardware import dtype_bytes

_QUANT_SCALE_DTYPES = {"fp16", "bf16", "fp32", "int64"}
_QUANT_WEIGHT_DTYPES = {
    "int4", "uint4", "int8", "uint8", "fp4", "mxfp4", "nvfp4", "fp8",
    "fp8_e4m3", "fp8_e5m2", "mxfp8", "hif8",
}


def _scale_elems(scale: Slot, n_dim: int, batch: int, what: str) -> int:
    """Validate a scale tensor broadcast against ``[batch, N]`` or ``[N]``."""
    dims = tuple(scale.dims)
    if not dims:
        raise AbiError(f"{what}_shape", "scalar rank-0 scale is not a tensor")
    if len(dims) > 2:
        raise AbiError(f"{what}_shape", f"rank {len(dims)} {dims}")
    if dims[-1] not in {n_dim, 1}:
        raise AbiError(f"{what}_shape", f"{dims} does not broadcast to N={n_dim}")
    if len(dims) == 2 and dims[0] not in {batch, 1}:
        raise AbiError(f"{what}_shape", f"{dims} does not broadcast to B={batch}")
    return int(math.prod(dims))


def _quant_weight(dtype: str | None) -> bool:
    return str(dtype or "").strip().lower() in _QUANT_WEIGHT_DTYPES


def _prefixes(lhs: Slot, rhs: Slot) -> tuple[tuple[int, ...], bool]:
    a = tuple(lhs.dims[:-2])
    b = tuple(rhs.dims[:-2])
    width = max(len(a), len(b))
    a = (1,) * (width - len(a)) + a
    b = (1,) * (width - len(b)) + b
    out = []
    for left, right in zip(a, b):
        if left == right:
            out.append(left)
        elif left == 1:
            out.append(right)
        elif right == 1:
            out.append(left)
        else:
            raise AbiError("gemm_batch_mismatch", f"{a} vs {b}")
    weight_broadcast = all(dim == 1 for dim in b)
    return tuple(out), weight_broadcast


def _quant_from_dtypes(act: str, weight: str) -> str:
    if weight in {"int4", "uint4"}:
        return "w4a8" if act in {"int8", "uint8"} else "w4a16"
    if weight in {"fp4", "mxfp4"}:
        return "mxfp4"
    if weight in {"fp8", "fp8_e4m3", "fp8_e5m2", "mxfp8"}:
        return "mxfp8"
    return "w8a8"


def _native_quant(act: str, weight: str) -> str:
    """Return the supported native quant contract or fail closed."""
    if weight in {"int8", "uint8"}:
        if act not in {"int8", "uint8"}:
            raise AbiError("unsupported_quant_contract",
                           f"INT8 weight with activation {act}")
        return "w8a8"
    if weight in {"int4", "uint4"}:
        if act in {"int8", "uint8"}:
            return "w4a8"
        if act in {"bf16", "fp16"}:
            return "w4a16"
        raise AbiError("unsupported_quant_contract",
                       f"INT4 weight with activation {act}")
    if weight in {"fp4", "mxfp4"}:
        return "mxfp4"
    if weight in {"fp8", "fp8_e4m3", "fp8_e5m2", "mxfp8"}:
        return "mxfp8"
    raise AbiError("unsupported_quant_contract",
                   f"activation {act} / weight {weight}")


def matmul_params(row: Mapping[str, Any], operator: str,
                  inputs: Sequence[Slot], outputs: Sequence[Slot]
                  ) -> tuple[dict[str, Any], dict[str, Any]]:
    lhs = require_slot(inputs, 0, "lhs")
    rhs = require_slot(inputs, 1, "rhs")
    if lhs.rank < 2 or rhs.rank < 2:
        raise AbiError("matmul_rank", f"{lhs.shape} @ {rhs.shape}")
    trans_a = _bool_attr(row, ("transpose_a", "trans_a", "transpose_x1"))
    trans_b = _bool_attr(row, ("transpose_b", "trans_b", "transpose_x2"))
    if trans_a:
        m_dim, k_lhs = lhs.shape[-1], lhs.shape[-2]
    else:
        m_dim, k_lhs = lhs.shape[-2], lhs.shape[-1]
    if trans_b:
        k_rhs, n_dim = rhs.shape[-1], rhs.shape[-2]
    else:
        k_rhs, n_dim = rhs.shape[-2], rhs.shape[-1]
    if k_lhs != k_rhs:
        raise AbiError("gemm_k_mismatch", f"K {k_lhs} != {k_rhs}")
    prefix, broadcast = _prefixes(lhs, rhs)
    if operator == "matmul" and prefix:
        raise AbiError("matmul_rank", f"leading axes {prefix} on MatMul")
    if operator == "batch_matmul" and not prefix:
        raise AbiError("batch_matmul_rank", "BatchMatMul requires batch axes")
    batch = math.prod(prefix) if prefix else 1
    act_batches = math.prod(lhs.dims[:-2]) if lhs.dims[:-2] else 1
    weight_batches = math.prod(rhs.dims[:-2]) if rhs.dims[:-2] else 1
    out = require_output(outputs, "gemm output")
    expected = prefix + (m_dim, n_dim)
    if tuple(out.dims) != expected:
        raise AbiError("gemm_output_shape",
                       f"out {out.shape} != {expected}")
    params = {
        "M": m_dim, "N": n_dim, "K": k_lhs, "batch": batch,
        "act_batch": act_batches, "weight_batch": weight_batches,
        "weight_broadcast": broadcast,
        "dtype": require_dtype(lhs, "lhs"),
        "weight_dtype": require_dtype(rhs, "rhs"),
        "out_dtype": require_dtype(out, "out"),
    }
    if operator == "quant_batch_matmul":
        scale = require_slot(inputs, 2, "quant scale")
        if scale.dtype not in _QUANT_SCALE_DTYPES:
            raise AbiError("unsupported_quant_scale",
                           f"scale dtype {scale.dtype}")
        params["quant"] = _native_quant(params["dtype"],
                                        params["weight_dtype"])
        params["scale_bytes"] = int(
            _scale_elems(scale, n_dim, batch, "quant_scale")
            * dtype_bytes(scale.dtype))
        # A per-token activation scale is charged only when the row actually
        # declares that optional buffer; it is never inferred.
        act_scale = 0
        for slot in inputs[3:]:
            if "scale" in slot.name.lower() and (
                    "token" in slot.name.lower()
                    or "activation" in slot.name.lower()):
                if not _present(slot):
                    continue
                if not slot.valid or slot.shape is None:
                    raise AbiError("invalid_tensor_slot", "pertoken_scale")
                if slot.dtype not in _QUANT_SCALE_DTYPES:
                    raise AbiError("unsupported_quant_scale", f"{slot.dtype}")
                act_scale = int(_scale_elems(slot, m_dim, batch,
                                             "activation_scale")
                                * dtype_bytes(slot.dtype))
                break
        params["act_scale_bytes"] = act_scale
        group_size = _int_attr(row, ("group_size",), None)
        if group_size is not None:
            params["group_size"] = group_size
    return params, {}


def _grouped_axes(x: Slot, w: Slot, out: Slot | None
                  ) -> tuple[int, int, int, int]:
    if x.rank != 2 or w.rank != 3:
        raise AbiError("grouped_shape", f"{x.shape} vs {w.shape}")
    rows, k_x = x.shape
    experts, dim1, dim2 = w.shape
    out_n = out.dims[-1] if out is not None else None
    if out_n is not None and out_n == dim2:
        k_dim, n_dim = dim1, dim2
    elif out_n is not None and out_n == dim1:
        k_dim, n_dim = dim2, dim1
    elif k_x == dim1:
        k_dim, n_dim = dim1, dim2
    elif k_x == dim2:
        k_dim, n_dim = dim2, dim1
    else:
        raise AbiError("gemm_k_mismatch", f"x K {k_x} vs W {w.shape}")
    if k_x != k_dim:
        raise AbiError("gemm_k_mismatch", f"x K {k_x} != W K {k_dim}")
    if out is not None and tuple(out.dims) != (rows, n_dim):
        raise AbiError("gemm_output_shape",
                       f"out {out.shape} != {(rows, n_dim)}")
    return rows, k_dim, n_dim, experts


def grouped_params(row: Mapping[str, Any], inputs: Sequence[Slot],
                   outputs: Sequence[Slot]
                   ) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    w = require_slot(inputs, 1, "weight")
    out = require_output(outputs, "grouped output")
    rows, k_dim, n_dim, experts = _grouped_axes(x, w, out)
    if n_dim == 2 * k_dim:
        mode, hidden, inter = "up_gate", k_dim, k_dim
    elif n_dim > k_dim:
        mode, hidden, inter = "down", n_dim, k_dim
    else:
        mode, hidden, inter = "generic", k_dim, k_dim
    weight_dtype = require_dtype(w, "weight")
    scale = None
    for slot in inputs[2:]:
        low = slot.name.lower()
        if slot.valid and "scale" in low and "activation" not in low \
                and "group" not in low:
            scale = slot
            break
    if scale is None and len(inputs) > 3 and inputs[3].valid:
        scale = inputs[3]
    if _quant_weight(weight_dtype):
        if scale is None:
            raise AbiError("missing_tensor_slot",
                           "quantized grouped weight requires its scale buffer")
        if scale.dtype not in _QUANT_SCALE_DTYPES:
            raise AbiError("unsupported_quant_scale",
                           f"grouped scale dtype {scale.dtype}")
        dims = tuple(scale.dims)
        if not dims or len(dims) > 3 or dims[-1] not in {n_dim, 1}:
            raise AbiError("grouped_scale_shape", f"{dims}")
        if len(dims) == 3 and dims[0] not in {experts, 1}:
            raise AbiError("grouped_scale_shape", f"{dims}")
    params = {
        "tokens": rows, "hidden": hidden, "inter": inter,
        "k_dim": k_dim, "n_dim": n_dim,
        "experts_total": experts, "experts_local": experts,
        "topk": 1, "ep": 1, "mode": mode,
        "dtype": require_dtype(x, "x"),
        "weight_dtype": weight_dtype,
        "out_dtype": require_dtype(out, "out"),
        "routed_rows": rows,
    }
    declared = row.get("quant", row.get("quant_mode"))
    if declared not in (None, ""):
        params["quant"] = str(declared)
    if scale is not None and _quant_weight(weight_dtype):
        params["scale_bytes"] = int(math.prod(scale.dims)
                                     * dtype_bytes(scale.dtype))
    group_list = row.get("group_list") or row.get("expert_token_nums")
    if group_list is None:
        for slot in inputs:
            low = slot.name.lower()
            if ("group" in low or "expert" in low) and slot.values is not None:
                group_list = slot.values
                break
    if group_list is not None:
        params["group_list"] = list(_capture_ints(group_list, "group_list"))
        params["group_list_type"] = _int_attr(
            row, ("group_list_type", "group_type"), 1) or 0
    return params, {"flags": {"unfiltered_padding_shape_bound": True}}


__all__ = ["grouped_params", "matmul_params"]
