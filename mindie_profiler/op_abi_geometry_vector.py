"""Native normalization and activation operand contracts.

[Role]
  Bind ``RmsNorm``/``AddRmsNorm``/``QkRmsNorm`` gamma/output/rstd slots and the
  one- or two-buffer nonlinear activation arithmetic without flattening a
  gated SiLU/GeGLU into a plain multiply.

[Invariants]
  * A mandatory norm slot is validated even when it is malformed or rank-wrong.
  * Gamma matches the normalized trailing axes; dtypes and byte widths are the
    declared ones.
  * A declared statistics output is charged with its own dtype and element count.
  * Activation buffer arity is independent of the nonlinear mode.

[Timeouts & Locks]
  Pure in-memory arithmetic proportional to declared slots; no I/O.

[Side-Effect Policy]
  No mutation of the input row; returns fresh params mappings.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, Sequence

from mindie_profiler.op_abi_geometry_common import (
    _present, require_dtype, require_float_dtype, require_output, require_slot,
)
from mindie_profiler.op_abi_slots import AbiError, Slot


def _gamma_slot(operator: str, inputs: Sequence[Slot]) -> Slot | None:
    for slot in inputs:
        if "gamma" in slot.name.lower():
            return slot
    index = 2 if operator == "add_rms_norm" else 1
    if index < len(inputs):
        return inputs[index]
    return None


def _validate_gamma(gamma: Slot | None, x: Slot, operator: str) -> Slot:
    if not _present(gamma):
        raise AbiError("missing_tensor_slot", f"{operator} mandatory gamma input")
    if not gamma.valid or gamma.shape is None:
        raise AbiError("invalid_tensor_slot", f"{operator} gamma")
    require_float_dtype(gamma, f"{operator} gamma")
    dims = tuple(gamma.dims)
    if not dims or len(dims) > x.rank or dims != tuple(x.dims[-len(dims):]):
        raise AbiError("norm_gamma_shape",
                       f"gamma {gamma.shape} != normalized trailing axis of "
                       f"x {x.shape}")
    return gamma


def _validate_norm_output(out: Slot, x: Slot, operator: str) -> str:
    if not out.valid or out.shape is None:
        raise AbiError("invalid_tensor_slot", f"{operator} output")
    dtype = require_float_dtype(out, f"{operator} output")
    if tuple(out.dims) != tuple(x.dims):
        raise AbiError("norm_output_shape",
                       f"output {out.shape} != x {x.shape}")
    return dtype


def rms_params(operator: str, inputs: Sequence[Slot],
               outputs: Sequence[Slot]) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    if x.rank < 1:
        raise AbiError("norm_rank", f"{x.shape}")
    dtype = require_float_dtype(x, "x")
    residual_slot = None
    residual_dtype = x_out_dtype = dtype
    if operator == "add_rms_norm":
        residual_slot = inputs[1] if len(inputs) > 1 else None
        if not _present(residual_slot) or not residual_slot.valid \
                or residual_slot.shape is None:
            raise AbiError("missing_tensor_slot",
                           "add_rms_norm mandatory residual input")
        residual_dtype = require_float_dtype(residual_slot, "add_rms_norm residual")
        if tuple(residual_slot.dims) != tuple(x.dims):
            raise AbiError("norm_residual_shape",
                           f"residual {residual_slot.shape} != x {x.shape}")
    gamma = _validate_gamma(_gamma_slot(operator, inputs), x, operator)
    out = require_output(outputs, f"{operator} output")
    out_dtype = _validate_norm_output(out, x, operator)
    rows = 1
    for dim in x.dims[:-1]:
        rows *= dim
    rows = max(1, rows)
    rstd_elems = 0
    rstd_dtype = "fp32"
    if len(outputs) > 1 and _present(outputs[1]):
        rstd = outputs[1]
        if not rstd.valid or rstd.shape is None:
            raise AbiError("invalid_tensor_slot", f"{operator} rstd")
        rstd_dtype = require_float_dtype(rstd, f"{operator} rstd")
        count = math.prod(rstd.dims) if rstd.dims else 1
        if count != rows:
            raise AbiError("norm_rstd_shape",
                           f"rstd {rstd.shape} does not hold one value per row "
                           f"({rows})")
        rstd_elems = int(count)
    if operator == "add_rms_norm" and len(outputs) > 2 and _present(outputs[2]):
        residual_out = outputs[2]
        if not residual_out.valid or residual_out.shape is None:
            raise AbiError("invalid_tensor_slot", "add_rms_norm x_out")
        x_out_dtype = require_float_dtype(residual_out, "add_rms_norm x_out")
        if tuple(residual_out.dims) != tuple(x.dims):
            raise AbiError("norm_residual_out_shape",
                           f"x_out {residual_out.shape} != x {x.shape}")
    return ({"rows": rows, "hidden": x.dims[-1], "dtype": dtype,
             "residual": operator == "add_rms_norm",
             "gamma_dtype": require_dtype(gamma, "gamma"),
             "gamma_elems": int(math.prod(gamma.dims)),
             "out_dtype": out_dtype, "rstd_elems": rstd_elems,
             "rstd_dtype": rstd_dtype,
             **({"residual_dtype": residual_dtype, "x_out_dtype": x_out_dtype}
                if operator == "add_rms_norm" else {})}, {})


def swiglu_params(operator: str, inputs: Sequence[Slot],
                  outputs: Sequence[Slot],
                  row: Mapping[str, Any] | None = None
                  ) -> tuple[dict[str, Any], dict[str, Any]]:
    x = require_slot(inputs, 0, "x")
    dtype = require_dtype(x, "x")
    out = require_output(outputs, "activation output")
    out_dtype = require_float_dtype(out, "activation output")
    native = re.sub(r"[^a-z]", "", " ".join(str((row or {}).get(key) or "")
                                          for key in ("name", "type")).lower())
    elementwise = str((row or {}).get("type") or "").strip().lower() in {
        "mul", "add", "multiply"}
    gated = any(name in native for name in ("swiglu", "siluandmul", "geglu"))
    elementwise = elementwise and not gated
    unary = not gated and any(name in native for name in ("silu", "swish"))
    packed = not elementwise and not unary
    mode = "geglu" if operator == "geglu" else "gate_mul" if elementwise else "silu"
    elements = int(math.prod(x.dims)) if x.dims else 1
    out_elems = int(math.prod(out.dims)) if out.dims else 1
    second = None
    if len(inputs) > 1 and inputs[1].state not in {
            "omitted", "absent", "undefined", "null"}:
        second = inputs[1]
        if not second.valid or second.shape is None:
            raise AbiError("activation_second_operand", f"{operator} second input")
        if require_dtype(second, "second") != dtype:
            raise AbiError("activation_second_dtype",
                           f"{second.dtype} != {dtype}")
    if second is None and packed:
        if (x.rank < 1 or out.rank != x.rank or out.dims[:-1] != x.dims[:-1]
                or out.dims[-1] < 1 or out.dims[-1] * 2 != x.dims[-1]
                or out_elems * 2 != elements):
            raise AbiError("activation_output_shape", f"out {out.shape} vs {x.shape}")
        return ({"rows": math.prod(out.dims[:-1]), "hidden": out.dims[-1],
                 "mode": "geglu" if operator == "geglu" else "swiglu",
                 "dtype": dtype, "out_dtype": out_dtype}, {})
    if x.rank < 2:
        # Captured Mul/Add/unary kernels publish flattened buffers; the output
        # owns the logical shape. Single-input gated kernels cannot reach here.
        if out_elems != elements:
            raise AbiError("activation_output_shape",
                           f"out {out.shape} != x elements {elements}")
        rows = math.prod(out.dims[:-1]) if out.rank > 1 else 1
        hidden = out.dims[-1] if out.dims else elements
        if second is not None:
            second_elems = int(math.prod(second.dims))
            if second_elems < out_elems:
                raise AbiError("activation_second_shape",
                               f"{second.shape} does not cover {out.shape}")
        else:
            second_elems = 0
        return ({"rows": max(1, rows), "hidden": max(1, hidden), "mode": mode,
                 "dtype": dtype, "two_input": second is not None,
                 "out_dtype": out_dtype, "first_elems": elements,
                 "second_elems": second_elems}, {})
    two_input = second is not None
    if two_input and tuple(second.dims) != tuple(x.dims):
        raise AbiError("activation_second_shape",
                       f"{second.shape} != {x.shape}")
    rows = math.prod(x.dims[:-1])
    if tuple(out.dims) != tuple(x.dims):
        raise AbiError("activation_output_shape", f"out {out.shape} != {x.shape}")
    out_last = out.dims[-1]
    return ({"rows": max(1, rows), "hidden": max(1, out_last), "mode": mode,
             "dtype": dtype, "two_input": two_input,
             "out_dtype": out_dtype, "first_elems": elements,
             "second_elems": elements if two_input else 0}, {})
