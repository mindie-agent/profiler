"""Fused normalization, activation and dynamic-quantization bench builders.

[Role]
  Implement the 20 canonical norm, activation and activation-quantization
  builders with per-repeat multi-slot cold-ring rotation across inputs,
  weights and outputs.

[Invariants]
  * Zero unfused PyTorch composite fallbacks (no ``pow/mean/rsqrt`` or
    ``F.silu(a) * b`` emulation); missing kernels raise
    ``BenchUnmodeledOperatorError`` carrying ``mindie-unmodeled-structure-hint/1``.
  * Cold-ring execution rotates ``slot = repeat_idx % num_slots`` inside the
    timed callable and retains ``num_slots - 1`` live outputs so
    ``NPUCachingAllocator`` cannot recycle L2-hot output buffers.

[Timeouts & Locks]
  Pure setup outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates tensors only on the caller-provided ``torch`` handle.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping, Sequence

from ..events import ProfilerUsageError
from .operators_common import (
    BFLOAT16,
    FLOAT32,
    INT8,
    INT32,
    OP_CFG,
    UINT8,
    cold_ring_slot_count,
    device_of,
    dim_int,
    dims_2d,
    element_bytes,
    ones,
    raise_unmodeled,
    record_actual_shape,
    require_kernel,
    require_npu_surface,
    resolve_case_dtype,
    resolve_npu_dtype,
    resolve_op,
    shape_of,
    slice_ring_tensors,
    torch_dtype,
    upstream_2d_input,
    upstream_inputs,
    view_upstream_operand,
    wrap_ring_step,
    zeros,
)


def _norm_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    add: bool = False,
    quant: bool = False,
    gated: bool = False,
    l2: bool = False,
    extra_modules: Sequence[str] = (),
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        dynamic_add = None
        if builder == "add_rms_norm_quant":
            for candidate in candidates:
                found = resolve_op(
                    torch, candidate, context=context, allow_torch_attr=False
                )
                if callable(found):
                    if "dynamic" in candidate:
                        dynamic_add = found
                    break
        effective_candidates = candidates
        soc_arch = str((context or {}).get("soc_arch") or (context or {}).get("arch") or "").strip().upper()
        if builder == "rms_norm_quant" and soc_arch == "A5" and "npu_rms_norm_quant" in candidates:
            effective_candidates = ("npu_rms_norm_quant", *(c for c in candidates if c != "npu_rms_norm_quant"))
        op = dynamic_add if callable(dynamic_add) else require_kernel(
            torch,
            case,
            context,
            effective_candidates,
            builder=builder,
            upstream_abi=upstream_abi,
            extra_modules=extra_modules,
        )
        resolved = next((
            name for name in effective_candidates
            if resolve_op(
                torch, name, context=context, extra_modules=extra_modules, allow_torch_attr=False
            ) is op
        ), str(getattr(op, "__name__", "") or ""))
        dynamic = "dynamic" in resolved or "dynamic" in str(getattr(op, "__name__", "") or "")
        vllm_gated = gated and resolved == "rms_norm_gated" and (
            str(getattr(op, "__module__", "")).startswith("vllm_ascend")
            or (
                resolve_op(torch, "rms_norm_gated", context=context, extra_modules=(), allow_torch_attr=False) is not op
                and resolve_op(
                    torch, "rms_norm_gated", context=context,
                    extra_modules=("vllm_ascend.ops.triton.kda.kda", "vllm_ascend.ops.triton.kda"),
                    allow_torch_attr=False,
                ) is op
            )
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        record_actual_shape(context, tokens=tokens, width=width)
        eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        io_tensors = int(OP_CFG["binary_io_tensor_count"]) if (add or gated) else 2
        slots = cold_ring_slot_count(case, context, tokens * width * eb * io_tensors)
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        w_ring = slice_ring_tensors(
            torch,
            context,
            num_slots=slots,
            dims=(width,),
            dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")),
            device=device,
            fill_ones=True,
        )
        aux_ring = (
            slice_ring_tensors(
                torch,
                context,
                num_slots=slots,
                dims=(tokens, width),
                dtype=dtype,
                dtype_name=str(case.get("dtype", "bf16")),
                device=device,
            )
            if (add or gated)
            else []
        )

        def compatible(shape: tuple[int, ...]) -> bool:
            return shape == (tokens * width,) or (
                len(shape) > 1 and shape[-1] == width and math.prod(shape[:-1]) == tokens
            )

        def norm_operand(output: Any) -> Any:
            return view_upstream_operand(
                output, (tokens, width), compatible=compatible, error="bench_norm_input_shape_mismatch"
            )

        def norm_input(slot: int) -> Any:
            inputs = upstream_inputs(context)
            if len(inputs) > 1:
                raise ProfilerUsageError("bench_norm_input_count_mismatch")
            return norm_operand(inputs[0]) if inputs else x_ring[slot]

        def norm_inputs(slot: int) -> tuple[Any, Any]:
            inputs = upstream_inputs(context)
            if len(inputs) > 2:
                raise ProfilerUsageError("bench_norm_input_count_mismatch")
            return (
                norm_operand(inputs[0]) if inputs else x_ring[slot],
                norm_operand(inputs[1]) if len(inputs) == 2 else aux_ring[slot],
            )

        def gated_step(slot: int) -> Any:
            x, z = norm_inputs(slot)
            if vllm_gated:
                viewer_x = getattr(x, "view", None)
                viewer_z = getattr(z, "view", None)
                x3 = viewer_x(tokens, 1, width) if callable(viewer_x) else x
                z3 = viewer_z(tokens, 1, width) if callable(viewer_z) else z
                return op(x3, z3, w_ring[slot], None, activation="swish", eps=eps)
            return op(x, w_ring[slot], z=z, eps=eps)

        if l2:
            return wrap_ring_step(slots, lambda s: op(norm_input(s), eps=eps), retain_outputs=True)
        if gated:
            return wrap_ring_step(slots, gated_step, retain_outputs=True)
        if add and quant:
            if callable(dynamic_add):
                return wrap_ring_step(
                    slots,
                    lambda s: op(*norm_inputs(s), w_ring[s], epsilon=eps),
                    retain_outputs=True,
                )
            scales1 = ones(torch, 1, dtype=getattr(torch, FLOAT32, dtype), device=device)
            zero_points1 = zeros(torch, 1, dtype=getattr(torch, INT32, dtype), device=device)
            return wrap_ring_step(
                slots,
                lambda s: op(*norm_inputs(s), w_ring[s], scales1, zero_points1, epsilon=eps),
                retain_outputs=True,
            )
        if add:
            return wrap_ring_step(
                slots, lambda s: op(*norm_inputs(s), w_ring[s], eps), retain_outputs=True
            )
        if quant:
            if dynamic:
                return wrap_ring_step(
                    slots,
                    lambda s: op(norm_input(s), w_ring[s], epsilon=eps),
                    retain_outputs=True,
                )
            beta = zeros(torch, width, dtype=dtype, device=device)
            scale = ones(torch, 1, dtype=getattr(torch, FLOAT32, dtype), device=device)
            offset = zeros(torch, 1, dtype=getattr(torch, INT8, dtype), device=device)
            return wrap_ring_step(
                slots,
                lambda s: op(norm_input(s), w_ring[s], beta, scale, offset, epsilon=eps),
                retain_outputs=True,
            )
        return wrap_ring_step(slots, lambda s: op(norm_input(s), w_ring[s], eps), retain_outputs=True)

    return build


def build_layer_norm(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="layer_norm", upstream_abi="aclnnLayerNorm")
    soc_arch = str((context or {}).get("soc_arch") or (context or {}).get("arch") or "").strip().upper()
    npu_ln = (
        None if soc_arch == "A5"
        else resolve_op(torch, "npu_layer_norm_eval", context=context, allow_torch_attr=False)
    )
    fn_mod = getattr(getattr(torch, "nn", None), "functional", None)
    fn_ln = getattr(fn_mod, "layer_norm", None) if fn_mod is not None else None
    op = npu_ln or resolve_op(
        torch, "layer_norm", context=context, allow_torch_attr=True
    ) or fn_ln
    if not callable(op):
        require_kernel(
            torch,
            case,
            context,
            ("npu_layer_norm_eval", "layer_norm"),
            builder="layer_norm",
            upstream_abi="aclnnLayerNorm",
        )
    device = device_of(context)
    tokens, width = dims_2d(case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
    eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    w_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(width,), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device, fill_ones=True,
    )
    return wrap_ring_step(
        slots, lambda s: op(x_ring[s], (width,), w_ring[s], None, eps), retain_outputs=True
    )


def _gated_act_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str]
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype = resolve_case_dtype(torch, case)
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
        eb = element_bytes(dtype_name)
        slots = cold_ring_slot_count(
            case, context, tokens * width * eb * int(OP_CFG["binary_io_tensor_count"])
        )
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width * 2), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        return wrap_ring_step(slots, lambda s: op(upstream_2d_input(
            context, x_ring[s], (tokens, width * 2), dtype=dtype, error="bench_swiglu_input_mismatch",
        )), retain_outputs=True)

    return build


def _unary_act_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    allow_aten: str | None = None,
    pass_dim: bool = False,
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        require_npu_surface(torch, case, context, builder=builder, upstream_abi=upstream_abi)
        op = None
        for cand in candidates:
            op = resolve_op(torch, cand, context=context, allow_torch_attr=False)
            if callable(op):
                break
        if op is None and allow_aten is not None:
            fn_mod = getattr(getattr(torch, "nn", None), "functional", None)
            op = resolve_op(torch, allow_aten, context=context, allow_torch_attr=True) or (
                getattr(fn_mod, allow_aten, None) if fn_mod is not None else None
            )
        if not callable(op):
            op = require_kernel(
                torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
            )
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(dtype_name)
        slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        if pass_dim:
            return wrap_ring_step(slots, lambda s: op(x_ring[s], -1), retain_outputs=True)
        return wrap_ring_step(slots, lambda s: op(x_ring[s]), retain_outputs=True)

    return build


def _quant_act_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str], dequant: bool, dual: bool
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        raw_dt = str(case.get("dtype") or "bf16").strip().lower() or "bf16"
        is_dyn_quant = (not dequant) and (not dual) and builder == "dynamic_quant"
        is_mxfp4 = is_dyn_quant and raw_dt == "mxfp4"
        is_mxfp8 = is_dyn_quant and raw_dt == "mxfp8"
        is_fp8 = is_dyn_quant and raw_dt in {"fp8", "fp8_e4m3", "float8_e4m3fn", "fp8_e5m2", "float8_e5m2"}
        is_hif8 = is_dyn_quant and raw_dt in {"hif8", "hifloat8"}
        is_quant_target = is_dyn_quant and (is_mxfp4 or is_mxfp8 or is_fp8 or is_hif8 or raw_dt == INT8)
        mx_op = (
            resolve_op(torch, "npu_dynamic_mx_quant", context=context, allow_torch_attr=False)
            if (is_mxfp4 or is_mxfp8) else None
        )
        if (is_mxfp4 or is_mxfp8) and not callable(mx_op):
            raise_unmodeled(
                case, builder=builder, upstream_abi="aclnnDynamicMxQuant",
                reason="missing_kernel:npu_dynamic_mx_quant",
                candidates=("npu_dynamic_mx_quant",), context=context,
            )
        op = mx_op if callable(mx_op) else require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        dst_dt: Any = None
        if callable(mx_op):
            mx_attr = "float4_e2m1fn_x2" if is_mxfp4 else "float8_e4m3fn"
            dst_dt = resolve_npu_dtype(torch, context, mx_attr)
            if dst_dt is None:
                raise_unmodeled(
                    case, builder=builder, upstream_abi="aclnnDynamicMxQuant",
                    reason=f"missing_native_dtype:{mx_attr}",
                    candidates=("npu_dynamic_mx_quant",), context=context,
                )
        elif is_fp8:
            fp8_attr = "float8_e5m2" if raw_dt in {"fp8_e5m2", "float8_e5m2"} else "float8_e4m3fn"
            dst_dt = resolve_npu_dtype(torch, context, fp8_attr, fallback_attr=fp8_attr)
            if dst_dt is None:
                raise_unmodeled(
                    case, builder=builder, upstream_abi=upstream_abi,
                    reason=f"missing_native_dtype:{fp8_attr}",
                    candidates=candidates, context=context,
                )
        elif is_hif8:
            dst_dt = resolve_npu_dtype(torch, context, "hifloat8")
            if dst_dt is None:
                raise_unmodeled(
                    case, builder=builder, upstream_abi=upstream_abi,
                    reason="missing_native_dtype:hifloat8",
                    candidates=candidates, context=context,
                )
        device = device_of(context)
        tokens, width = dims_2d(case)
        cols = width * 2 if dual else width
        in_name = INT32 if dequant else (BFLOAT16 if is_quant_target else str(case.get("dtype", "bf16")))
        record_actual_shape(context, tokens=tokens, width=width, dtype=str(case.get("dtype", "bf16")))
        in_dtype = (
            getattr(torch, INT32, None) if dequant
            else (torch_dtype(torch, BFLOAT16) if is_quant_target else resolve_case_dtype(torch, case))
        )
        slots = cold_ring_slot_count(case, context, tokens * cols * element_bytes(in_name) * 2)
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, cols), dtype=in_dtype,
            dtype_name=in_name, device=device,
        )
        if dequant:
            w_scale = ones(torch, cols, dtype=getattr(torch, FLOAT32, None), device=device)
            a_scale = ones(torch, tokens, dtype=getattr(torch, FLOAT32, None), device=device)
            return wrap_ring_step(
                slots,
                lambda s: op(
                    x_ring[s], weight_scale=w_scale, activation_scale=a_scale, activate_left=True
                ),
                retain_outputs=True,
            )
        if callable(mx_op):
            if is_mxfp4:
                return wrap_ring_step(
                    slots,
                    lambda s: mx_op(x_ring[s], dst_type=dst_dt, round_mode="round"),
                    retain_outputs=True,
                )
            return wrap_ring_step(
                slots,
                lambda s: mx_op(x_ring[s], dst_type=dst_dt),
                retain_outputs=True,
            )
        if is_fp8 or is_hif8:
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], dst_type=dst_dt), retain_outputs=True,
            )
        return wrap_ring_step(slots, lambda s: op(x_ring[s]), retain_outputs=True)

    return build


def build_silu_mul(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="silu_mul", upstream_abi="aclnnSilu")
    fused = resolve_op(
        torch, "npu_swiglu", context=context, allow_torch_attr=False
    ) or resolve_op(torch, "npu_silu", context=context, allow_torch_attr=False)
    fn_mod = getattr(getattr(torch, "nn", None), "functional", None)
    silu_fn = fused or (getattr(fn_mod, "silu", None) if fn_mod is not None else None)
    if not callable(silu_fn):
        silu_fn = require_kernel(
            torch, case, context, ("npu_silu", "silu"), builder="silu_mul", upstream_abi="aclnnSilu"
        )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    slots = cold_ring_slot_count(
        case, context, tokens * width * element_bytes(case.get("dtype", "bf16")) * 2
    )
    cols = width * 2 if (fused is not None and shape.get("gated")) else width
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, cols), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: silu_fn(x_ring[s]), retain_outputs=True)


def build_empty_launch(
    _torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    kernel = str(shape_of(case).get("kernel") or case.get("op") or "")
    launcher = (context.get("empty_launchers") or {}).get(kernel)
    if not callable(launcher):
        raise_unmodeled(
            case, builder="empty_launch", upstream_abi=kernel or "empty_launch",
            reason="empty_launch_unavailable", code=f"bench_empty_launch_unavailable: {kernel}",
        )
    record_actual_shape(context, kernel=kernel)
    return launcher


def build_empty_event_pair(_torch: Any, _case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], None]:
    record_actual_shape(context, events=2)
    return lambda: None


def build_mte2_transfer(
    _torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    direction = str(case.get("op") or "mte2_aic")
    probe = (context.get("native_probes") or {}).get(direction)
    if not callable(probe):
        raise_unmodeled(
            case, builder="mte2_transfer", upstream_abi=direction,
            reason="native_probe_absent",
            code=(
                f"bench_native_probe_absent: {direction} needs an ABI-matched native probe"
            ),
        )
    nbytes = int(shape_of(case).get("bytes") or 0)
    residency = str(case.get("residency") or "dram")
    owners = str(case.get("owners") or "one_owner")
    record_actual_shape(context, bytes=nbytes, residency=residency, owners=owners)
    return lambda: probe(nbytes, residency=residency, owners=owners)


def build_pinned_copy(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="pinned_copy", upstream_abi="aclrtMemcpyAsync")
    shape, device = shape_of(case), device_of(context)
    size = dim_int(shape, "bytes", int(OP_CFG["collective_default_bytes"]))
    u8 = getattr(torch, UINT8, None)
    empty_fn = getattr(torch, "empty", None)
    if callable(empty_fn):
        try:
            host = empty_fn(size, dtype=u8, pin_memory=True)
        except TypeError:
            host = zeros(torch, size, dtype=u8, device="cpu")
        target = empty_fn(size, dtype=u8, device=device)
    else:
        host = zeros(torch, size, dtype=u8, device="cpu")
        target = zeros(torch, size, dtype=u8, device=device)
    direction = str(case.get("direction") or shape.get("direction") or "h2d")
    record_actual_shape(context, bytes=size, direction=direction)
    if direction == "h2d":
        return lambda: target.copy_(host, non_blocking=True)
    return lambda: host.copy_(target, non_blocking=True)


def build_noop_probe(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="noop_probe", upstream_abi="aclnnInplaceFillScalar")
    record_actual_shape(context, elements=1, bytes=int(OP_CFG["float32_element_bytes"]))
    buf = zeros(torch, 1, dtype=getattr(torch, FLOAT32, None), device=device_of(context))
    if callable(getattr(buf, "fill_", None)):
        return lambda: buf.fill_(0.0)
    return lambda: torch.add(buf, buf, out=buf)


def build_stream_read_probe(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="stream_read_probe", upstream_abi="aclnnInplaceCopy")
    shape, device = shape_of(case), device_of(context)
    nbytes = max(
        int(OP_CFG["cacheline_bytes"]),
        dim_int(shape, "bytes", int(OP_CFG["collective_default_bytes"])),
    )
    record_actual_shape(context, bytes=nbytes, nbytes=nbytes)
    u8 = getattr(torch, UINT8, None)
    slots = cold_ring_slot_count(case, context, nbytes * 2)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(nbytes,), dtype=u8, dtype_name=UINT8, device=device
    )
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(nbytes,), dtype=u8, dtype_name=UINT8, device=device
    )
    return wrap_ring_step(slots, lambda s: dst[s].copy_(src[s]))


NORM_QUANT_BUILDERS: dict[str, Callable[..., Callable[[], Any]]] = {
    "empty_event_pair": build_empty_event_pair,
    "empty_launch": build_empty_launch,
    "mte2_transfer": build_mte2_transfer,
    "pinned_copy": build_pinned_copy,
    "noop_probe": build_noop_probe,
    "stream_read_probe": build_stream_read_probe,
    "rms_norm": _norm_builder(
        builder="rms_norm", upstream_abi="aclnnRmsNorm", candidates=("npu_rms_norm",)
    ),
    "add_rms_norm": _norm_builder(
        builder="add_rms_norm", upstream_abi="aclnnAddRmsNorm",
        candidates=("npu_add_rms_norm",), add=True,
    ),
    "gemma_rms_norm": _norm_builder(
        builder="gemma_rms_norm", upstream_abi="aclnnGemmaRmsNorm",
        candidates=("npu_gemma_rms_norm", "gemma_rms_norm"),
    ),
    "layer_norm": build_layer_norm,
    "rms_norm_quant": _norm_builder(
        builder="rms_norm_quant", upstream_abi="aclnnRmsNormDynamicQuant",
        candidates=("npu_rms_norm_dynamic_quant", "npu_rms_norm_quant", "rms_norm_dynamic_quant"),
        quant=True,
    ),
    "add_rms_norm_quant": _norm_builder(
        builder="add_rms_norm_quant", upstream_abi="aclnnAddRmsNormDynamicQuantV2",
        candidates=(
            "npu_add_rms_norm_quant",
            "npu_add_rms_norm_dynamic_quant",
            "add_rms_norm_dynamic_quant",
        ),
        add=True, quant=True,
    ),
    "rms_norm_gated": _norm_builder(
        builder="rms_norm_gated", upstream_abi="_layer_norm_fwd_1pass_kernel_npu",
        candidates=("npu_rms_norm_gated", "rmsnorm_fn", "rms_norm_gated"),
        gated=True,
        extra_modules=("vllm_ascend.ops.triton.kda.kda", "vllm_ascend.ops.triton.kda", "fla.modules.layernorm_gated"),
    ),
    "l2_norm": _norm_builder(
        builder="l2_norm", upstream_abi="l2norm_fwd_kernel2",
        candidates=("npu_l2_norm", "l2norm_fwd", "l2_norm"),
        l2=True, extra_modules=("fla.modules.l2norm",),
    ),
    "dynamic_quant": _quant_act_builder(
        builder="dynamic_quant", upstream_abi="aclnnDynamicQuantV2",
        candidates=("npu_dynamic_quant", "dynamic_quant"), dequant=False, dual=False,
    ),
    "swiglu": _gated_act_builder(
        builder="swiglu", upstream_abi="aclnnSwiGlu", candidates=("npu_swiglu",)
    ),
    "swiglu_oai": _gated_act_builder(
        builder="swiglu_oai", upstream_abi="aclnnSwiGluOai",
        candidates=("npu_clipped_swiglu", "npu_swiglu_oai", "swiglu_oai"),
    ),
    "swiglu_dynamic_quant": _quant_act_builder(
        builder="swiglu_dynamic_quant", upstream_abi="aclnnSwigluQuant",
        candidates=("npu_swiglu_quant", "swiglu_dynamic_quant"), dequant=False, dual=True,
    ),
    "dequant_swiglu_quant": _quant_act_builder(
        builder="dequant_swiglu_quant", upstream_abi="aclnnDequantSwigluQuant",
        candidates=("npu_dequant_swiglu_quant", "dequant_swiglu_quant"), dequant=True, dual=True,
    ),
    "dequant_situ_quant": _quant_act_builder(
        builder="dequant_situ_quant", upstream_abi="aclnnDequantSituQuant",
        candidates=("npu_dequant_situ_quant", "dequant_situ_quant"), dequant=True, dual=True,
    ),
    "situ_activation": _gated_act_builder(
        builder="situ_activation", upstream_abi="aclnnSitu", candidates=("npu_situ", "situ")
    ),
    "geglu": _gated_act_builder(
        builder="geglu", upstream_abi="aclnnGeGluV2", candidates=("npu_geglu",)
    ),
    "gelu": _unary_act_builder(
        builder="gelu", upstream_abi="aclnnGelu",
        candidates=("npu_gelu", "npu_fast_gelu", "fast_gelu"), allow_aten="gelu",
    ),
    "silu_mul": build_silu_mul,
    "sigmoid": _unary_act_builder(
        builder="sigmoid", upstream_abi="aclnnSigmoid",
        candidates=("npu_sigmoid",), allow_aten="sigmoid",
    ),
    "softmax": _unary_act_builder(
        builder="softmax", upstream_abi="aclnnSoftmaxV2",
        candidates=("npu_softmax", "softmax"), allow_aten="softmax", pass_dim=True,
    ),
}

__all__ = ["NORM_QUANT_BUILDERS"]
