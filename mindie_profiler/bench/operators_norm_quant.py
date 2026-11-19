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

from typing import Any, Callable, Mapping, Sequence

from .operators_common import (
    FLOAT32,
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
    randn,
    require_kernel,
    require_npu_surface,
    resolve_case_dtype,
    resolve_op,
    shape_of,
    slice_ring_tensors,
    upstream_input,
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
        op = require_kernel(
            torch,
            case,
            context,
            candidates,
            builder=builder,
            upstream_abi=upstream_abi,
            extra_modules=extra_modules,
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        io_tensors = int(OP_CFG["binary_io_tensor_count"]) if (add or gated) else 2
        slots = cold_ring_slot_count(case, context, tokens * width * eb * io_tensors)
        seeded = upstream_input(case, context)
        if seeded is not None and slots == 1:
            x_ring = [seeded]
        else:
            x_ring = slice_ring_tensors(
                torch,
                context,
                num_slots=slots,
                dims=(tokens, width),
                dtype=dtype,
                dtype_name=str(case.get("dtype", "bf16")),
                device=device,
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
        if l2:
            return wrap_ring_step(slots, lambda s: op(x_ring[s], eps=eps), retain_outputs=True)
        if gated:
            return wrap_ring_step(
                slots,
                lambda s: op(x_ring[s], w_ring[s], z=aux_ring[s], eps=eps),
                retain_outputs=True,
            )
        if add and quant:
            return wrap_ring_step(
                slots,
                lambda s: op(x_ring[s], aux_ring[s], w_ring[s], epsilon=eps),
                retain_outputs=True,
            )
        if add:
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], aux_ring[s], w_ring[s], eps), retain_outputs=True
            )
        if quant:
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], w_ring[s], epsilon=eps), retain_outputs=True
            )
        return wrap_ring_step(slots, lambda s: op(x_ring[s], w_ring[s], eps), retain_outputs=True)

    return build


def build_layer_norm(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="layer_norm", upstream_abi="aclnnLayerNorm")
    npu_ln = resolve_op(torch, "npu_layer_norm_eval", context=context, allow_torch_attr=False)
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
    eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
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
        eb = element_bytes(case.get("dtype", "bf16"))
        slots = cold_ring_slot_count(
            case, context, tokens * width * eb * int(OP_CFG["binary_io_tensor_count"])
        )
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width * 2), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        return wrap_ring_step(slots, lambda s: op(x_ring[s]), retain_outputs=True)

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
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
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
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        cols = width * 2 if dual else width
        in_name = INT32 if dequant else str(case.get("dtype", "bf16"))
        in_dtype = getattr(torch, INT32, None) if dequant else resolve_case_dtype(torch, case)
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
    return launcher


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
    if direction == "h2d":
        return lambda: target.copy_(host, non_blocking=True)
    return lambda: host.copy_(target, non_blocking=True)


def build_noop_probe(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="noop_probe", upstream_abi="aclnnInplaceFillScalar")
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
    "empty_event_pair": lambda _t, _c, _ctx: (lambda: None),
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
        candidates=("npu_rms_norm_quant", "npu_rms_norm_dynamic_quant", "rms_norm_dynamic_quant"),
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
        gated=True, extra_modules=("fla.modules.layernorm_gated",),
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
        candidates=("npu_gelu", "fast_gelu"), allow_aten="gelu",
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
