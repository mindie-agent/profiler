"""Dense/quantized/grouped GEMM, MoE routing, MC2 and HCCL collective builders.

[Role]
  Implement the 24 canonical GEMM, MoE gating/routing, MC2, matmul-collective
  and HCCL collective builders (plus S0/collective microbench aliases) with
  ``ACL_FORMAT_FRACTAL_NZ`` (29) weight casting, dedicated ``w4a8`` INT4
  routing and multi-slot cold-ring rotation across inputs, weights and outputs.

[Invariants]
  * ``w4a8`` / ``int4`` never falls through to INT8 ``npu_quant_matmul``; it
    dispatches to ``npu_weight_quant_batchmatmul`` or INT4-packed
    ``npu_grouped_matmul`` with ``ACL_FORMAT_FRACTAL_NZ`` (29).
  * Collectives require an active ``torch.distributed`` process group or fused
    MC2/HCCL kernel; missing kernels raise ``BenchUnmodeledOperatorError``.

[Timeouts & Locks]
  Pure setup outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates tensors and enqueues HCCL/NPU work only on the caller ``torch``.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from ..events import ProfilerUsageError
from .operators_common import (
    A5_ONLY_FP8_DTYPES,
    BFLOAT16,
    FLOAT32,
    INT8,
    INT32,
    INT64,
    OP_CFG,
    UINT8,
    cast_weight_nz,
    cold_ring_slot_count,
    device_of,
    device_values,
    dim_int,
    dims_2d,
    element_bytes,
    materialize_contiguous_zero_offset,
    ones,
    raise_unmodeled,
    randn,
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
    upstream_input,
    wrap_ring_step,
    zeros,
)

def _case_dtype_and_wfmt(case: Mapping[str, Any]) -> tuple[str, str]:
    dtype_str = str(case.get("dtype") or "").strip().lower()
    meta = case.get("metadata") if isinstance(case.get("metadata"), Mapping) else {}
    wfmt = str((meta or {}).get("weight_format") or case.get("weight_format") or "").strip().lower()
    return dtype_str, wfmt

def _is_mxfp4(case: Mapping[str, Any]) -> bool:
    dtype_str, wfmt = _case_dtype_and_wfmt(case)
    return dtype_str == "mxfp4" or wfmt == "mxfp4"

def _is_mxfp8(case: Mapping[str, Any]) -> bool:
    dtype_str, wfmt = _case_dtype_and_wfmt(case)
    return dtype_str == "mxfp8" or wfmt == "mxfp8"

def _is_w4a8(case: Mapping[str, Any]) -> bool:
    dtype_str, wfmt = _case_dtype_and_wfmt(case)
    return dtype_str in {"w4a8", "w4a16", "int4"} or wfmt in {"w4a8", "w4a16", "int4"}

def _transpose_dims(tensor: Any, d0: int, d1: int) -> Any:
    tr = getattr(tensor, "transpose", None)
    if callable(tr):
        return tr(d0, d1)
    if d0 == 0 and d1 == 1:
        t_fn = getattr(tensor, "t", None)
        if callable(t_fn):
            return t_fn()
    return tensor

def _mx_aligned_k(k: int) -> int:
    align = int(OP_CFG["mx_group_size"]) * int(OP_CFG["mx_scale_pair_size"])
    if k < align or k % align != 0:
        return max(align, ((k + align - 1) // align) * align)
    return k

def _mx_quant_matmul(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any], *, is_mxfp4: bool
) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, ("npu_quant_matmul",),
        builder="quant_matmul", upstream_abi="aclnnQuantMatmulV5",
    )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    k_eff = _mx_aligned_k(k)
    group_sz = int(OP_CFG["mx_group_size"])
    pair_sz = int(OP_CFG["mx_scale_pair_size"])
    k_groups = max(1, (k_eff + group_sz - 1) // group_sz)
    k_pairs = max(1, (k_groups + pair_sz - 1) // pair_sz)
    raw_out = str(case.get("output_dtype") or BFLOAT16).strip().lower()
    out_name = "fp16" if raw_out in {"fp16", "float16", "half"} else BFLOAT16
    out_dt = torch_dtype(torch, out_name)
    u8_dt = getattr(torch, UINT8, None)
    e8m0_dt = resolve_npu_dtype(torch, context, "float8_e8m0fnu", fallback_attr=UINT8)
    dtype_label = "mxfp4" if is_mxfp4 else "mxfp8"
    record_actual_shape(
        context, m=m, n=n, k=k, dtype=dtype_label,
        **({"k_eff": k_eff} if k_eff != k else {}),
    )
    if is_mxfp4:
        k_packed = max(1, k_eff // int(OP_CFG["mxfp4_pack_divisor"]))
        fp4_dt = resolve_npu_dtype(torch, context, "float4_e2m1fn_x2", fallback_attr=UINT8)
        slots = cold_ring_slot_count(
            case, context,
            (m * k_packed + n * k_packed) * element_bytes(UINT8) + m * n * element_bytes(out_name),
        )
        x1_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(m, k_packed), dtype=u8_dt,
            dtype_name=UINT8, device=device,
        )
        raw_x2 = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(n, k_packed), dtype=u8_dt,
            dtype_name=UINT8, device=device,
        )
        x2_ring = [_transpose_dims(item, 0, 1) for item in raw_x2]
        x2_scale = _transpose_dims(ones(torch, n, k_pairs, pair_sz, dtype=u8_dt, device=device), 0, 1)
        x1_scale = ones(torch, m, k_pairs, pair_sz, dtype=u8_dt, device=device)
        extra_kw: dict[str, Any] = {"x1_dtype": fp4_dt, "x2_dtype": fp4_dt}
    else:
        fp8_dt = torch_dtype(torch, "fp8_e4m3") or resolve_npu_dtype(torch, context, "float8_e4m3fn", fallback_attr=INT8)
        if fp8_dt is None:
            raise_unmodeled(
                case, builder="quant_matmul", upstream_abi="aclnnQuantMatmulV5",
                reason="missing_native_dtype:mxfp8", candidates=("npu_quant_matmul",),
                context=context,
            )
        slots = cold_ring_slot_count(
            case, context,
            (m * k_eff + k_eff * n) * element_bytes("fp8_e4m3") + m * n * element_bytes(out_name),
        )
        x1_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(m, k_eff), dtype=fp8_dt,
            dtype_name="fp8_e4m3", device=device,
        )
        raw_x2 = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(k_eff, n), dtype=fp8_dt,
            dtype_name="fp8_e4m3", device=device,
        )
        use_nz = str(case.get("layout") or "").upper() == "FRACTAL_NZ"
        x2_ring = (
            [cast_weight_nz(torch, item, context, case=case, builder="quant_matmul", customize_dtype=fp8_dt) for item in raw_x2]
            if use_nz else raw_x2
        )
        x2_scale = ones(torch, k_pairs, n, pair_sz, dtype=u8_dt, device=device)
        x1_scale = ones(torch, m, k_pairs, pair_sz, dtype=u8_dt, device=device)
        extra_kw = {}
    return wrap_ring_step(
        slots,
        lambda s: op(
            x1_ring[s], x2_ring[s], x2_scale,
            scale_dtype=e8m0_dt, pertoken_scale=x1_scale, pertoken_scale_dtype=e8m0_dt,
            output_dtype=out_dt, group_sizes=[1, 1, group_sz], **extra_kw,
        ),
        retain_outputs=True,
    )

def _weight_quant_matmul(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="quant_matmul", upstream_abi="aclnnWeightQuantBatchMatmulV2")
    wq_op = resolve_op(torch, "npu_weight_quant_batchmatmul", context=context, allow_torch_attr=False)
    q_op = resolve_op(torch, "npu_quant_matmul", context=context, allow_torch_attr=False)
    gmm_op = resolve_op(torch, "npu_grouped_matmul", context=context, allow_torch_attr=False)
    if not callable(wq_op) and not callable(q_op) and not callable(gmm_op):
        require_kernel(
            torch, case, context,
            ("npu_weight_quant_batchmatmul", "npu_quant_matmul", "npu_grouped_matmul"),
            builder="quant_matmul", upstream_abi="aclnnWeightQuantBatchMatmulV2",
        )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    nk = str(case.get("layout") or "") == "NK"
    quant_route = callable(q_op) and (
        not callable(wq_op) or str(case.get("op") or "") == "npu_quant_matmul"
    )
    act_name = INT8 if quant_route else BFLOAT16
    record_actual_shape(context, m=m, n=n, k=k)
    act_dtype = torch_dtype(torch, act_name)
    int32_dt = getattr(torch, INT32, None)
    packed_n = max(1, n // int(OP_CFG["int4_pack_int32_divisor"]))
    pack_op = resolve_op(torch, "npu_convert_weight_to_int4pack", context=context, allow_torch_attr=False)
    w_dims = ((n, k) if nk else (k, n)) if callable(pack_op) else (
        (packed_n, k) if nk else (k, packed_n)
    )
    slots = cold_ring_slot_count(
        case, context,
        m * k * element_bytes(act_name) + k * packed_n * element_bytes(INT32)
        + m * n * element_bytes(BFLOAT16),
    )
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=act_dtype,
        dtype_name=act_name, device=device,
    )
    raw_w = slice_ring_tensors(
        torch, context, num_slots=slots, dims=w_dims, dtype=int32_dt,
        dtype_name=INT32, device=device,
    )
    if nk:
        raw_w = [getattr(item, "t")() for item in raw_w]

    def to_nz(item: Any) -> Any:
        prepared = materialize_contiguous_zero_offset(item)
        packed = pack_op(prepared) if callable(pack_op) else prepared
        return cast_weight_nz(torch, packed, context, case=case, builder="quant_matmul", required=True)

    w_ring = [to_nz(item) for item in raw_w]
    if quant_route:
        q_scale = ones(torch, n, dtype=getattr(torch, FLOAT32, None), device=device)
        out_dt = torch_dtype(torch, BFLOAT16)
        return wrap_ring_step(
            slots,
            lambda s: q_op(x_ring[s], w_ring[s], q_scale, output_dtype=out_dt),
            retain_outputs=True,
        )
    scale = ones(torch, 1, n, dtype=act_dtype, device=device)
    offset = zeros(torch, 1, n, dtype=act_dtype, device=device)
    if callable(wq_op):
        return wrap_ring_step(
            slots,
            lambda s: wq_op(
                x_ring[s], w_ring[s], antiquant_scale=scale, antiquant_offset=offset
            ),
            retain_outputs=True,
        )
    group_list = zeros(torch, 1, dtype=getattr(torch, INT64, None), device=device)
    return wrap_ring_step(
        slots,
        lambda s: gmm_op(
            [x_ring[s]], [w_ring[s]], bias=None, scale=[scale], group_list=group_list,
            split_item=int(OP_CFG["megamoe_unpermute_mode"]) - 1, group_type=0, group_list_type=1,
        ),
        retain_outputs=True,
    )

def build_matmul(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    dtype_name = str(case.get("dtype", "bf16")).lower()
    if _is_mxfp4(case) or _is_mxfp8(case):
        return build_quant_matmul(torch, case, context)
    if _is_w4a8(case):
        return _weight_quant_matmul(torch, case, context)
    if dtype_name == "int8":
        return build_quant_matmul(torch, case, context)
    require_npu_surface(torch, case, context, builder="matmul", upstream_abi="aclnnMatmul")
    mm_op = resolve_op(torch, "matmul", context=context, allow_torch_attr=True)
    if not callable(mm_op):
        raise_unmodeled(
            case, builder="matmul", upstream_abi="aclnnMatmul", reason="torch_matmul_missing"
        )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    record_actual_shape(context, m=m, n=n, k=k, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, (m * k + k * n + m * n) * eb)
    left_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=dtype, dtype_name=dtype_name, device=device,
    )
    nk_layout = str(case.get("layout") or "") == "NK"
    raw_right = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(n, k) if nk_layout else (k, n),
        dtype=dtype, dtype_name=dtype_name, device=device,
    )
    explicit_nz = str(case.get("layout") or "") == "FRACTAL_NZ"
    use_nz = case.get("format_code") == int(OP_CFG["nz_format_code"]) or explicit_nz
    if use_nz:
        right_ring = [cast_weight_nz(torch, item, context, case=case, builder="matmul", required=explicit_nz) for item in raw_right]
    elif nk_layout:
        right_ring = [getattr(item, "t")() for item in raw_right]
    else:
        right_ring = raw_right
    out_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, n), dtype=dtype, dtype_name=dtype_name, device=device,
    )

    def step(slot: int) -> Any:
        dynamic = upstream_input(case, context, m * k)
        if dynamic is not None:
            viewer = getattr(dynamic, "view", None)
            left = viewer(m, k) if callable(viewer) else dynamic
        else:
            left = left_ring[slot]
        try:
            return mm_op(left, right_ring[slot], out=out_ring[slot])
        except TypeError:
            return mm_op(left, right_ring[slot])

    return wrap_ring_step(slots, step)

def build_quant_matmul(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    if _is_mxfp4(case):
        return _mx_quant_matmul(torch, case, context, is_mxfp4=True)
    if _is_mxfp8(case):
        return _mx_quant_matmul(torch, case, context, is_mxfp4=False)
    if _is_w4a8(case):
        return _weight_quant_matmul(torch, case, context)
    op = require_kernel(
        torch, case, context, ("npu_quant_matmul",),
        builder="quant_matmul", upstream_abi="aclnnQuantMatmulWeightNz",
    )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    raw_dt = str(case.get("dtype") or INT8).strip().lower() or INT8
    native_fp8 = raw_dt in A5_ONLY_FP8_DTYPES
    if native_fp8:
        in_dt = torch_dtype(torch, raw_dt)
        if in_dt is None:
            raise_unmodeled(
                case, builder="quant_matmul", upstream_abi="aclnnQuantMatmulWeightNz",
                reason=f"missing_native_dtype:{raw_dt}", candidates=("npu_quant_matmul",),
                context=context,
            )
        in_name = raw_dt
    else:
        in_name = INT8
        in_dt = getattr(torch, INT8, None)
    record_actual_shape(context, m=m, n=n, k=k, dtype=in_name)
    raw_out = str(case.get("output_dtype") or BFLOAT16).strip().lower()
    out_name = "fp16" if raw_out in {"fp16", "float16", "half"} else BFLOAT16
    out_dt = torch_dtype(torch, out_name)
    in_eb = element_bytes(in_name)
    slots = cold_ring_slot_count(case, context, (m * k + k * n) * in_eb + m * n * element_bytes(out_name))
    left_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=in_dt,
        dtype_name=in_name, device=device,
    )
    nk_layout = str(case.get("layout") or "") == "NK"
    nd_fp8 = native_fp8 and str(case.get("layout") or "").upper() == "ND"
    raw_right = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(n, k) if nk_layout else (k, n),
        dtype=in_dt, dtype_name=in_name, device=device,
    )
    if nk_layout:
        right_ring = [getattr(item, "t")() for item in raw_right]
    elif nd_fp8:
        right_ring = raw_right
    else:
        right_ring = [
            cast_weight_nz(
                torch, item, context, case=case, builder="quant_matmul",
                required=not bool((context or {}).get("allow_cpu_smoke")),
            )
            for item in raw_right
        ]
    scale = ones(torch, n, dtype=getattr(torch, FLOAT32, None), device=device)
    per_token = (
        ones(torch, m, dtype=getattr(torch, FLOAT32, None), device=device)
        if case.get("per_token_scale")
        else None
    )

    def step(slot: int) -> Any:
        kwargs: dict[str, Any] = {"output_dtype": out_dt}
        if per_token is not None:
            kwargs["pertoken_scale"] = per_token
        return op(left_ring[slot], right_ring[slot], scale, **kwargs)

    return wrap_ring_step(slots, step, retain_outputs=True)

def _expert_counts(case: Mapping[str, Any], m: int, experts: int) -> tuple[list[int], list[int]]:
    raw = [int(x) for x in (case.get("group_list") or ())]
    if raw:
        counts = (
            [raw[0], *(raw[i] - raw[i - 1] for i in range(1, len(raw)))]
            if int(case.get("group_list_type", 1)) == 0 else raw
        )
        if any(val < 0 for val in counts) or sum(counts) != m:
            raise ProfilerUsageError("bench_group_list_mismatch: declared group_list does not sum to M")
        if len(counts) < experts:
            counts = counts + [0] * (experts - len(counts))
    else:
        q, rem = divmod(m, experts)
        counts = [q + (1 if i < rem else 0) for i in range(experts)]
    return counts, [sum(counts[: i + 1]) for i in range(len(counts))]

def _build_a5_fp_grouped_matmul(
    torch: Any,
    case: Mapping[str, Any],
    context: Mapping[str, Any],
    op: Callable[..., Any],
    *,
    m: int,
    n: int,
    k: int,
    experts: int,
    group_list: Any,
    group_list_type: int,
    raw_dt: str,
    is_mxfp4: bool,
    is_mxfp8_nz: bool,
) -> Callable[[], Any]:
    device = device_of(context)
    split_item = int(OP_CFG["megamoe_unpermute_mode"]) - 1
    use_fp16 = str(case.get("output_dtype") or "").lower() in {"fp16", "float16", "half"}
    out_name = "fp16" if use_fp16 else BFLOAT16
    out_dt = torch_dtype(torch, out_name)
    out_eb = element_bytes(out_name)
    u8_dt = getattr(torch, UINT8, None)
    fp32_dt = getattr(torch, FLOAT32, out_dt)
    group_sz = int(OP_CFG["mx_group_size"])
    pair_sz = int(OP_CFG["mx_scale_pair_size"])
    if is_mxfp4:
        k_eff = _mx_aligned_k(k)
        k_packed = max(1, k_eff // int(OP_CFG["mxfp4_pack_divisor"]))
        k_pairs = max(1, ((k_eff + group_sz - 1) // group_sz + pair_sz - 1) // pair_sz)
        fp4_dt = resolve_npu_dtype(torch, context, "float4_e2m1fn_x2", fallback_attr=UINT8)
        e8m0_dt = resolve_npu_dtype(torch, context, "float8_e8m0fnu", fallback_attr=UINT8)
        slots = cold_ring_slot_count(
            case, context,
            (m * k_packed + experts * n * k_packed) * element_bytes(UINT8) + m * n * out_eb,
        )
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(m, k_packed), dtype=u8_dt,
            dtype_name=UINT8, device=device,
        )
        raw_w = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(experts, n, k_packed), dtype=u8_dt,
            dtype_name=UINT8, device=device,
        )
        w_ring = [_transpose_dims(item, 1, 2) for item in raw_w]
        w_scale = _transpose_dims(ones(torch, experts, n, k_pairs, pair_sz, dtype=u8_dt, device=device), 1, 2)
        x_scale = ones(torch, m, k_pairs, pair_sz, dtype=u8_dt, device=device)
        record_actual_shape(
            context, m=m, n=n, k=k, e=experts, matrix_groups=experts,
            dtype="mxfp4", weight_dtype="mxfp4", **({"k_eff": k_eff} if k_eff != k else {}),
        )
        return wrap_ring_step(
            slots,
            lambda s: op(
                [upstream_2d_input(context, x_ring[s], (m, k_packed), dtype=u8_dt, error="bench_grouped_matmul_input_mismatch")],
                [w_ring[s]], bias=None, scale=[w_scale], per_token_scale=[x_scale],
                group_list=group_list, split_item=split_item, group_type=0,
                group_list_type=group_list_type, output_dtype=out_dt,
                scale_dtype=e8m0_dt, per_token_scale_dtype=e8m0_dt,
                x_dtype=fp4_dt, weight_dtype=fp4_dt,
            ),
            retain_outputs=True,
        )
    fp8_key = "fp8_e5m2" if raw_dt in {"fp8_e5m2", "float8_e5m2"} else "fp8_e4m3"
    fp8_dt = torch_dtype(torch, fp8_key)
    if fp8_dt is None:
        raise_unmodeled(
            case, builder="grouped_matmul", upstream_abi="aclnnGroupedMatmulV5",
            reason=f"missing_native_dtype:{raw_dt}", candidates=("npu_grouped_matmul",),
            context=context,
        )
    if is_mxfp8_nz:
        k_eff = _mx_aligned_k(k)
        k_pairs = max(1, ((k_eff + group_sz - 1) // group_sz + pair_sz - 1) // pair_sz)
        e8m0_dt = resolve_npu_dtype(torch, context, "float8_e8m0fnu", fallback_attr=UINT8)
        slots = cold_ring_slot_count(
            case, context,
            (m * k_eff + experts * k_eff * n) * element_bytes(fp8_key) + m * n * out_eb,
        )
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(m, k_eff), dtype=fp8_dt,
            dtype_name=fp8_key, device=device,
        )
        raw_w = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(experts, k_eff, n), dtype=fp8_dt,
            dtype_name=fp8_key, device=device,
        )
        use_nz = str(case.get("layout") or "").upper() == "FRACTAL_NZ"
        w_ring = (
            [cast_weight_nz(torch, item, context, case=case, builder="grouped_matmul", customize_dtype=fp8_dt) for item in raw_w]
            if use_nz else raw_w
        )
        w_scale = ones(torch, experts, k_pairs, n, pair_sz, dtype=u8_dt, device=device)
        x_scale = ones(torch, m, k_pairs, pair_sz, dtype=u8_dt, device=device)
        record_actual_shape(
            context, m=m, n=n, k=k, e=experts, matrix_groups=experts,
            dtype=raw_dt, weight_dtype=raw_dt, **({"k_eff": k_eff} if k_eff != k else {}),
        )
        return wrap_ring_step(
            slots,
            lambda s: op(
                [upstream_2d_input(context, x_ring[s], (m, k_eff), dtype=fp8_dt, error="bench_grouped_matmul_input_mismatch")],
                [w_ring[s]], bias=None, scale=[w_scale], per_token_scale=[x_scale],
                group_list=group_list, split_item=split_item, group_type=0,
                group_list_type=group_list_type, output_dtype=out_dt,
                scale_dtype=e8m0_dt, per_token_scale_dtype=e8m0_dt,
            ),
            retain_outputs=True,
        )
    # ND FP8 dynamic MoE (W8A8FP8_DYNAMIC): ND weights + float32 per-channel scale.
    slots = cold_ring_slot_count(
        case, context, (m * k + experts * k * n) * element_bytes(fp8_key) + m * n * out_eb,
    )
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=fp8_dt, dtype_name=fp8_key, device=device,
    )
    w_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(experts, k, n), dtype=fp8_dt,
        dtype_name=fp8_key, device=device,
    )
    w_scale = ones(torch, experts, n, dtype=fp32_dt, device=device)
    x_scale = ones(torch, m, dtype=fp32_dt, device=device)
    record_actual_shape(
        context, m=m, n=n, k=k, e=experts, matrix_groups=experts,
        dtype=raw_dt, weight_dtype=raw_dt,
    )
    return wrap_ring_step(
        slots,
        lambda s: op(
            [upstream_2d_input(context, x_ring[s], (m, k), dtype=fp8_dt, error="bench_grouped_matmul_input_mismatch")],
            [w_ring[s]], bias=None, scale=[w_scale], per_token_scale=[x_scale],
            group_list=group_list, split_item=split_item, group_type=0,
            group_list_type=group_list_type, output_dtype=out_dt,
        ),
        retain_outputs=True,
    )


def build_grouped_matmul(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(torch, case, context, ("npu_grouped_matmul",),
                        builder="grouped_matmul", upstream_abi="aclnnGroupedMatmulV5")
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    raw_gl = list(case.get("group_list") or ())
    experts = max(1, len(raw_gl) if raw_gl else dim_int(shape, "e", 1))
    counts, cumulative = _expert_counts(case, m, experts)
    experts = len(counts)
    group_list_type = int(case.get("group_list_type", 1))
    gl_vals = cumulative if group_list_type == 0 else counts
    group_list = torch.tensor(gl_vals, dtype=getattr(torch, INT64, None), device=device) if hasattr(torch, "tensor") else gl_vals
    raw_dt = str(case.get("dtype", BFLOAT16)).strip().lower() or BFLOAT16
    is_mxfp4 = _is_mxfp4(case)
    is_mxfp8 = _is_mxfp8(case)
    is_fp8 = raw_dt in {"fp8", "fp8_e4m3", "float8_e4m3fn", "fp8_e5m2", "float8_e5m2"}
    if is_mxfp4 or is_mxfp8 or is_fp8:
        is_mxfp8_nz = is_mxfp8 or (is_fp8 and str(case.get("layout") or "").upper() == "FRACTAL_NZ")
        return _build_a5_fp_grouped_matmul(
            torch, case, context, op,
            m=m, n=n, k=k, experts=experts, group_list=group_list,
            group_list_type=group_list_type, raw_dt=raw_dt,
            is_mxfp4=is_mxfp4, is_mxfp8_nz=is_mxfp8_nz,
        )
    w4 = _is_w4a8(case)
    native_fp8 = (not w4) and (raw_dt in A5_ONLY_FP8_DTYPES)
    fp8_dt = None
    if native_fp8:
        fp8_dt = torch_dtype(torch, raw_dt)
        if fp8_dt is None:
            raise_unmodeled(
                case, builder="grouped_matmul", upstream_abi="aclnnGroupedMatmulV5",
                reason=f"missing_native_dtype:{raw_dt}", candidates=("npu_grouped_matmul",),
                context=context,
            )
    quant = w4 or raw_dt == INT8 or native_fp8
    pack_op = resolve_op(torch, "npu_convert_weight_to_int4pack", context=context, allow_torch_attr=False) if w4 else None
    w_name = INT32 if w4 else (raw_dt if native_fp8 else (INT8 if quant else raw_dt))
    w_dt = getattr(torch, INT32, None) if w4 else (
        fp8_dt if native_fp8 else (getattr(torch, w_name, None) if quant else resolve_case_dtype(torch, case))
    )
    w_n = n if (not w4 or callable(pack_op)) else max(1, n // int(OP_CFG["int4_pack_int32_divisor"]))
    in_name = INT8 if w4 else (raw_dt if native_fp8 else (INT8 if quant else raw_dt))
    in_dt = getattr(torch, INT8, None) if w4 else (
        fp8_dt if native_fp8 else (getattr(torch, INT8, None) if quant else w_dt)
    )
    eb, out_eb = element_bytes(in_name), (2 if quant else element_bytes(in_name))
    w_bytes = experts * k * n // int(OP_CFG["int4_pack_divisor"]) if w4 else experts * k * n * eb
    slots = cold_ring_slot_count(case, context, m * k * eb + w_bytes + m * n * out_eb)
    x_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(m, k), dtype=in_dt, dtype_name=in_name, device=device)
    w_dims = (1, k, w_n) if experts == 1 else (k, w_n)
    per_expert_rings = [slice_ring_tensors(torch, context, num_slots=slots, dims=w_dims, dtype=w_dt, dtype_name=w_name, device=device) for _ in range(experts)]

    def _prepare_weight(item: Any) -> Any:
        if not quant:
            return item
        prepared = materialize_contiguous_zero_offset(item)
        packed = pack_op(prepared) if callable(pack_op) else prepared
        return cast_weight_nz(torch, packed, context)

    w_slots = [
        [_prepare_weight(per_expert_rings[e][s]) for e in range(experts)]
        for s in range(len(per_expert_rings[0]))
    ]
    split_item = int(OP_CFG["megamoe_unpermute_mode"]) - 1
    quant_kw: dict[str, Any] = {}
    if quant:
        use_fp16 = str(case.get("output_dtype") or "").lower() in {"fp16", "float16", "half"}
        out_dt = torch_dtype(torch, "fp16" if use_fp16 else BFLOAT16)
        fp32_dt = getattr(torch, FLOAT32, out_dt)
        scale_dt = fp32_dt if use_fp16 else out_dt
        s_dims = (1, n) if experts == 1 else (n,)
        quant_kw = {
            "scale": [ones(torch, *s_dims, dtype=scale_dt, device=device) for _ in range(experts)],
            "per_token_scale": [ones(torch, m, dtype=fp32_dt, device=device)],
            "output_dtype": out_dt,
        }
    record_actual_shape(context, m=m, n=n, k=k, e=experts, matrix_groups=experts, dtype=in_name, weight_dtype=w_name)
    return wrap_ring_step(slots, lambda s: op(
        [upstream_2d_input(context, x_ring[s], (m, k), dtype=in_dt, error="bench_grouped_matmul_input_mismatch")],
        w_slots[s], bias=None, group_list=group_list, split_item=split_item,
        group_type=0, group_list_type=group_list_type, **quant_kw,
    ), retain_outputs=True)

def build_grouped_matmul_swiglu_quant(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    candidates = ("npu_grouped_matmul_swiglu_quant_v2", "grouped_matmul_swiglu_quant_weight_nz",
                  "npu_grouped_matmul_swiglu_quant", "grouped_matmul_swiglu_quant")
    op = require_kernel(
        torch, case, context, candidates,
        builder="grouped_matmul_swiglu_quant", upstream_abi="aclnnGroupedMatmulSwigluQuantWeightNZ",
    )
    resolved = next((c for c in candidates if resolve_op(torch, c, context=context, allow_torch_attr=False) is op), str(getattr(op, "__name__", "")))
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    raw_gl = list(case.get("group_list") or ())
    experts = max(1, len(raw_gl) if raw_gl else dim_int(shape, "e", 1))
    _counts, cumulative = _expert_counts(case, m, experts)
    experts = len(cumulative)
    record_actual_shape(context, m=m, n=n, k=k, e=experts, matrix_groups=experts, dtype=INT8)
    int8_dt, fp32_dt = getattr(torch, INT8, None), getattr(torch, FLOAT32, None)
    slots = cold_ring_slot_count(case, context, m * k + experts * k * n + m * n)
    x_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(m, k), dtype=int8_dt, dtype_name=INT8, device=device)
    group_list = torch.tensor(cumulative, dtype=getattr(torch, INT64, None), device=device) if hasattr(torch, "tensor") else cumulative
    x_scale = ones(torch, m, dtype=fp32_dt, device=device)
    if resolved in {"grouped_matmul_swiglu_quant_weight_nz", "npu_grouped_matmul_swiglu_quant"}:
        w_bank = [cast_weight_nz(torch, t, context) for t in slice_ring_tensors(torch, context, num_slots=slots, dims=(experts, k, n), dtype=int8_dt, dtype_name=INT8, device=device)]
        ws_bank = ones(torch, experts, n, dtype=fp32_dt, device=device)
        if resolved == "grouped_matmul_swiglu_quant_weight_nz":
            return wrap_ring_step(slots, lambda s: op(x=x_ring[s], weight=w_bank[s], weight_scale=ws_bank, x_scale=x_scale, group_list=group_list, bias=None, swiglu_limit=0.0), retain_outputs=True)
        return wrap_ring_step(slots, lambda s: op(x_ring[s], w_bank[s], ws_bank, x_scale, group_list), retain_outputs=True)
    per_expert = [slice_ring_tensors(torch, context, num_slots=slots, dims=(k, n), dtype=int8_dt, dtype_name=INT8, device=device) for _ in range(experts)]
    w_list = [[cast_weight_nz(torch, per_expert[e][s], context) for e in range(experts)] for s in range(len(per_expert[0]))]
    ws_list = [ones(torch, n, dtype=fp32_dt, device=device) for _ in range(experts)]
    return wrap_ring_step(slots, lambda s: op(x_ring[s], w_list[s], ws_list, x_scale, group_list=group_list), retain_outputs=True)

def _moe_gating_builder(*, builder: str, upstream_abi: str, candidates: Sequence[str]) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens = dim_int(shape, "tokens")
        has_e = "e" in shape
        experts = max(
            2, dim_int(shape, "e", dim_int(shape, "width", int(OP_CFG["topk_gating_default"])))
        )
        top_k = max(1, min(experts, dim_int(shape, "top_k", int(OP_CFG["topk_gating_default"]))))
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        gating_actual: dict[str, Any] = {
            "tokens": tokens, "e": experts, "top_k": top_k, "dtype": dtype_name,
        }
        if not has_e:
            gating_actual["width"] = experts
        record_actual_shape(context, **gating_actual)
        dtype = resolve_case_dtype(torch, case)
        slots = cold_ring_slot_count(
            case, context, tokens * experts * element_bytes(dtype_name)
        )
        logits = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, experts), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        return wrap_ring_step(slots, lambda s: op(logits[s], k=top_k), retain_outputs=True)

    return build

def build_moe_init_routing(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_moe_init_routing_v2", "npu_moe_init_routing_v3", "npu_moe_init_routing"),
        builder="moe_init_routing",
        upstream_abi="aclnnMoeInitRoutingV3",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    experts = max(1, dim_int(shape, "e", int(OP_CFG["topk_gating_default"])))
    top_k = max(1, min(experts, dim_int(shape, "top_k", 1)))
    width = dim_int(shape, "width", int(OP_CFG["attention_head_dim"]))
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, e=experts, top_k=top_k, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    expert_idx = zeros(torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device)
    return wrap_ring_step(
        slots,
        lambda s: op(
            x_ring[s], expert_idx, active_num=tokens * top_k, expert_num=experts,
            expert_tokens_num_type=1, expert_tokens_num_flag=True,
            active_expert_range=[0, experts], quant_mode=-1,
        ),
        retain_outputs=True,
    )

def build_moe_token_permute(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, ("npu_moe_token_permute", "moe_token_permute"),
        builder="moe_token_permute", upstream_abi="aclnnMoeTokenPermute",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    top_k = dim_int(shape, "top_k", 1)
    width = dim_int(shape, "width", int(OP_CFG["attention_head_dim"]))
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, top_k=top_k, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    indices = zeros(torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device)
    return wrap_ring_step(slots, lambda s: op(x_ring[s], indices), retain_outputs=True)

def build_moe_token_unpermute(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_moe_token_unpermute", "npu_moe_finalize_routing", "moe_token_unpermute"),
        builder="moe_token_unpermute",
        upstream_abi="aclnnMoeTokenUnpermute",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    top_k = dim_int(shape, "top_k", 1)
    width = dim_int(shape, "width", int(OP_CFG["attention_head_dim"]))
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, top_k=top_k, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    total_rows = tokens * top_k
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, total_rows * width * eb * 2)
    permuted_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(total_rows, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    sorted_ids = device_values(
        torch, list(range(total_rows)), dtype=getattr(torch, INT32, None), device=device,
    )
    probs = ones(torch, tokens, top_k, dtype=dtype, device=device)
    return wrap_ring_step(
        slots, lambda s: op(permuted_ring[s], sorted_ids, probs=probs), retain_outputs=True
    )

def build_histogram_v2(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_histogram_v2", "npu_histogram", "histogram_v2", "histc"),
        builder="histogram_v2",
        upstream_abi="aclnnHistogramV2",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    bins = max(1, dim_int(shape, "e", int(OP_CFG["histogram_bins_default"])))
    hist_actual: dict[str, Any] = {"tokens": tokens, "e": bins, "bins": bins}
    if "width" in shape:
        hist_actual["width"] = dim_int(shape, "width", 1)
    record_actual_shape(context, **hist_actual)
    idx = zeros(torch, tokens, dtype=getattr(torch, INT32, None), device=device)
    return wrap_ring_step(1, lambda _s: op(idx, bins), retain_outputs=True)


COLLECTIVE_OPS = (
    "all_reduce", "quantized_all_reduce", "all_gather", "all_gather_into_tensor",
    "reduce_scatter", "reduce_scatter_tensor", "all_to_all", "all_to_all_single",
    "all_to_all_v", "p2p_send_recv", "send", "recv", "send_recv",
    "npu_moe_distribute_dispatch_v2", "npu_moe_distribute_combine_v2",
)
COLLECTIVE_ALIASES: dict[str, str] = {
    "all_reduce": "all_reduce",
    "allreduce": "all_reduce",
    "all_gather": "all_gather_into_tensor",
    "allgather": "all_gather_into_tensor",
    "all_gather_into_tensor": "all_gather_into_tensor",
    "reduce_scatter": "reduce_scatter_tensor",
    "reducescatter": "reduce_scatter_tensor",
    "reduce_scatter_tensor": "reduce_scatter_tensor",
    "all_to_all": "all_to_all_single",
    "alltoall": "all_to_all_single",
    "all_to_all_single": "all_to_all_single",
    "all_to_all_v": "all_to_all_v",
    "alltoallv": "all_to_all_v",
    "send": "send",
    "recv": "recv",
}

def _declared_group_size(case: Mapping[str, Any], context: Mapping[str, Any], *, default: int = 1) -> int:
    shape = shape_of(case)
    declared = case.get("group_size") or shape.get("group_size") or context.get("group_size")
    try:
        return max(1, int(declared)) if declared is not None else default
    except (TypeError, ValueError):
        return default


def _group_for(case: Mapping[str, Any], context: Mapping[str, Any]) -> Any:
    name = str(case.get("group") or case.get("route") or "")
    groups = context.get("groups")
    if isinstance(groups, Mapping):
        raw_ranks = case.get("group_ranks") or case.get("participants")
        if isinstance(raw_ranks, (list, tuple, set, frozenset)):
            ranks = sorted({int(x) for x in raw_ranks if isinstance(x, int) and not isinstance(x, bool)})
            if len(ranks) > 1:
                explicit_key = f"{name or 'group'}@{','.join(str(r) for r in ranks)}"
                if explicit_key in groups:
                    return groups[explicit_key]
                raise ProfilerUsageError(
                    f"bench_collective_group_missing: explicit group_ranks {ranks!r} "
                    f"for {name or 'group'!r} was not created for this rank"
                )
        if not name:
            return groups.get("tp")
        group_size = _declared_group_size(case, context)
        if group_size > 1 and f"{name}:{group_size}" in groups:
            return groups[f"{name}:{group_size}"]
        if name not in groups:
            raise ProfilerUsageError(
                f"bench_collective_group_missing: named axis group {name!r} was not "
                "created for this rank; refusing to fall through to WORLD"
            )
        return groups[name]
    return context.get("group")

def _default_splits(elements: int, group_size: int) -> list[int]:
    quotient, remainder = divmod(int(elements), max(1, int(group_size)))
    return [quotient + (1 if idx < remainder else 0) for idx in range(group_size)]

def _circulant_splits(
    member_index: int, group_size: int, elements: int, style: str
) -> tuple[list[int], list[int]]:
    base = _default_splits(elements, group_size)

    def _send_for(idx: int) -> list[int]:
        send = [base[(peer - idx) % group_size] for peer in range(group_size)]
        if style == "skew_circulant" and group_size >= 2:
            moved = send[(idx + 1) % group_size] // 2
            if moved:
                send[(idx + 1) % group_size] -= moved
                send[(idx + 2) % group_size] += moved
        return send

    send_c = _send_for(member_index)
    recv_c = [_send_for(src)[member_index] for src in range(group_size)]
    return send_c, recv_c

def _resolve_dist(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any], kind: str) -> Any:
    injected = context.get("dist")
    if injected is not None:
        return injected
    dist = getattr(torch, "distributed", None)
    if dist is None or not getattr(dist, "is_initialized", lambda: False)():
        raise_unmodeled(
            case, builder=kind, upstream_abi=f"hccl_{kind}",
            reason="distributed_process_group_not_initialized",
        )
    return dist

def _bind_collective(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any], kind: str) -> Callable[[], Any]:
    """Bind one HCCL collective to its declared group and split matrices."""
    if kind not in {"all_reduce", "all_gather_into_tensor", "reduce_scatter_tensor",
                    "all_to_all_single", "all_to_all_v", "send", "recv"}:
        raise ProfilerUsageError(f"bench_collective_unsupported: {kind}")
    dist = _resolve_dist(torch, case, context, kind)
    group = _group_for(case, context)
    shape, device = shape_of(case), device_of(context)
    dtype_name = str(case.get("dtype") or shape.get("dtype") or FLOAT32)
    eb = element_bytes(dtype_name)
    nbytes = max(eb, int(case.get("nbytes") or shape.get("bytes") or OP_CFG["collective_default_bytes"]))
    elements = max(1, nbytes // eb)
    world_fn = getattr(dist, "get_world_size", None)
    default = 0 if kind in {"all_gather_into_tensor", "reduce_scatter_tensor"} else 1
    group_size = int(world_fn(group)) if callable(world_fn) else _declared_group_size(case, context, default=default)
    if group_size < 1:
        raise ProfilerUsageError("bench_collective_group_size_invalid")
    explicit_in = case.get("input_bytes") or shape.get("input_bytes")
    explicit_out = case.get("output_bytes") or shape.get("output_bytes")
    in_elements = max(1, int(explicit_in) // eb) if explicit_in is not None else elements
    if kind == "reduce_scatter_tensor":
        out_elements = (
            max(1, int(explicit_out) // eb)
            if explicit_out is not None
            else max(1, in_elements // group_size)
        )
        if explicit_in is None and explicit_out is not None:
            in_elements = out_elements * group_size
    elif kind == "all_gather_into_tensor":
        out_elements = (
            max(1, int(explicit_out) // eb)
            if explicit_out is not None
            else in_elements * group_size
        )
    elif kind in {"all_to_all_single", "all_to_all_v"}:
        out_elements = in_elements
    else:
        out_elements = 0
    record_actual_shape(
        context,
        dtype=dtype_name,
        nbytes=nbytes,
        bytes=nbytes,
        input_bytes=in_elements * eb,
        output_bytes=(out_elements or in_elements) * eb,
        elements=in_elements,
        output_elements=out_elements or in_elements,
        group_size=group_size,
    )
    buf_dt = resolve_case_dtype(torch, {"dtype": dtype_name})
    slots = cold_ring_slot_count(case, context, (in_elements + out_elements) * eb)
    bufs = slice_ring_tensors(torch, context, num_slots=slots, dims=(in_elements,),
                              dtype=buf_dt, dtype_name=dtype_name, device=device)
    if kind == "all_reduce":
        return wrap_ring_step(slots, lambda s: (dist.all_reduce(bufs[s], group=group), bufs[s])[1])
    if kind == "all_gather_into_tensor":
        outs = slice_ring_tensors(torch, context, num_slots=slots, dims=(out_elements,),
                                  dtype=buf_dt, dtype_name=dtype_name, device=device)
        return wrap_ring_step(slots, lambda s: (
            dist.all_gather_into_tensor(outs[s], bufs[s], group=group), outs[s])[1])
    if kind == "reduce_scatter_tensor":
        outs = slice_ring_tensors(torch, context, num_slots=slots,
                                  dims=(out_elements,),
                                  dtype=buf_dt, dtype_name=dtype_name, device=device)
        return wrap_ring_step(slots, lambda s: (
            dist.reduce_scatter_tensor(outs[s], bufs[s], group=group), outs[s])[1])
    if kind in {"all_to_all_single", "all_to_all_v"}:
        outs = slice_ring_tensors(torch, context, num_slots=slots, dims=(in_elements,),
                                  dtype=buf_dt, dtype_name=dtype_name, device=device)
        if kind == "all_to_all_single":
            return wrap_ring_step(slots, lambda s: (
                dist.all_to_all_single(outs[s], bufs[s], group=group), outs[s])[1])
        style = str(case.get("split_style") or "")
        if style in {"uniform", "skew_circulant"} and not (case.get("recv_counts") or case.get("recv_splits")):
            raw_ranks = case.get("group_ranks") or case.get("participants") or ()
            rank = int(context.get("rank") or 0)
            member_idx = raw_ranks.index(rank) if isinstance(raw_ranks, (list, tuple)) and rank in raw_ranks else (rank % group_size)
            send_c, recv_c = _circulant_splits(member_idx, group_size, in_elements, style)
        else:
            send_c = [int(x) for x in (case.get("send_counts") or case.get("send_splits")
                                       or _default_splits(in_elements, group_size))]
            recv_c = [int(x) for x in (case.get("recv_counts") or case.get("recv_splits") or send_c)]
        return wrap_ring_step(slots, lambda s: (
            dist.all_to_all_single(outs[s], bufs[s], output_split_sizes=recv_c,
                                   input_split_sizes=send_c, group=group), outs[s])[1])
    peer = int(case.get("peer") or 0)
    if kind == "send":
        return wrap_ring_step(slots, lambda s: (dist.send(bufs[s], dst=peer, group=group), bufs[s])[1])
    return wrap_ring_step(slots, lambda s: (dist.recv(bufs[s], src=peer, group=group), bufs[s])[1])


def _pair_for_rank(pairs: Sequence[Any], rank: int) -> tuple[int, int] | None:
    for item in pairs:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            first, second = int(item[0]), int(item[1])
            if rank in (first, second):
                return first, second
    return None


def _noop_send_recv(case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    shape = shape_of(case)
    dtype_name = str(case.get("dtype") or shape.get("dtype") or FLOAT32)
    eb = element_bytes(dtype_name)
    nbytes = max(eb, int(case.get("nbytes") or shape.get("bytes") or OP_CFG["collective_default_bytes"]))
    group_size = _declared_group_size(case, context, default=2)
    record_actual_shape(
        context, dtype=dtype_name, nbytes=nbytes, bytes=nbytes,
        elements=max(1, nbytes // eb), output_elements=max(1, nbytes // eb), group_size=group_size,
    )
    return lambda: None


def build_send_recv(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    rank = int(context.get("rank") or 0)
    pair_rounds = case.get("pair_rounds")
    if isinstance(pair_rounds, (list, tuple)) and pair_rounds:
        steps: list[Callable[[], Any]] = []
        for round_pairs in pair_rounds:
            active = _pair_for_rank(round_pairs, rank) if isinstance(round_pairs, (list, tuple)) else None
            if active is None:
                steps.append(_noop_send_recv(case, context))
                continue
            direction = "send" if rank == active[0] else "recv"
            peer = active[1] if rank == active[0] else active[0]
            steps.append(_bind_collective(torch, {**case, "direction": direction, "peer": peer}, context, direction))
        cursor = [0]

        def _round_step() -> Any:
            idx = cursor[0] % len(steps)
            cursor[0] += 1
            return steps[idx]()

        return _round_step
    pairs = case.get("pairs")
    if isinstance(pairs, (list, tuple)) and pairs:
        active = _pair_for_rank(pairs, rank)
        if active is None:
            return _noop_send_recv(case, context)
        direction = "send" if rank == active[0] else "recv"
        peer = active[1] if rank == active[0] else active[0]
        return _bind_collective(torch, {**case, "direction": direction, "peer": peer}, context, direction)
    direction = str(case.get("direction") or case.get("op") or "send")
    pair = case.get("pair")
    if isinstance(pair, (list, tuple)) and len(pair) == 2:
        first, second = int(pair[0]), int(pair[1])
        if rank not in (first, second):
            return _noop_send_recv(case, context)
        if direction not in {"send", "recv"}:
            direction = "send" if rank == first else "recv"
        if "peer" not in case:
            case = {**case, "peer": second if rank == first else first}
    elif direction not in {"send", "recv"}:
        direction = "send"
    return _bind_collective(torch, case, context, direction)

def build_quantized_all_reduce(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = resolve_op(torch, "npu_quant_all_reduce", context=context, allow_torch_attr=False) or resolve_op(
        torch, "quantized_all_reduce", context=context, allow_torch_attr=False
    )
    if not callable(op):
        op = require_kernel(
            torch,
            case,
            context,
            ("npu_quant_all_reduce", "quant_all_reduce", "quantized_all_reduce"),
            builder="quantized_all_reduce",
            upstream_abi="hcclAllReduceInt8",
        )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    actual_bytes = int(case.get("nbytes") or shape.get("bytes") or tokens * width * element_bytes(dtype_name))
    record_actual_shape(
        context, tokens=tokens, width=width, bytes=actual_bytes, nbytes=actual_bytes,
        group_size=_declared_group_size(case, context), dtype=dtype_name,
    )
    x = zeros(torch, tokens, width, dtype=resolve_case_dtype(torch, case), device=device)
    return wrap_ring_step(1, lambda _s: op(x), retain_outputs=True)

def build_p2p_send_recv(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = resolve_op(torch, "npu_p2p_send_recv", context=context, allow_torch_attr=False) or resolve_op(
        torch, "p2p_send_recv", context=context, allow_torch_attr=False
    )
    shape = shape_of(case)
    if callable(op):
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        actual_bytes = int(case.get("nbytes") or shape.get("bytes") or tokens * width * element_bytes(dtype_name))
        record_actual_shape(
            context, tokens=tokens, width=width, bytes=actual_bytes, nbytes=actual_bytes,
            group_size=_declared_group_size(case, context, default=2), dtype=dtype_name,
        )
        buf = zeros(torch, tokens, width, dtype=resolve_case_dtype(torch, case), device=device)
        return wrap_ring_step(1, lambda _s: op(buf), retain_outputs=True)
    dist = context.get("dist") or getattr(torch, "distributed", None)
    if dist is None or not getattr(dist, "is_initialized", lambda: False)():
        raise_unmodeled(
            case, builder="p2p_send_recv", upstream_abi="hcclSendRecv",
            reason="distributed_process_group_not_initialized",
        )
    group = context.get("group")
    world = max(2, int(context.get("group_size") or dist.get_world_size(group)))
    rank = int(getattr(dist, "get_rank", lambda _g=None: 0)(group))
    peer = (rank + 1) % world
    src = (rank - 1) % world
    nbytes = max(
        int(OP_CFG["float32_element_bytes"]),
        int(case.get("nbytes") or shape.get("bytes") or OP_CFG["collective_default_bytes"]),
    )
    count = max(1, nbytes // int(OP_CFG["float32_element_bytes"]))
    record_actual_shape(
        context, bytes=nbytes, nbytes=nbytes, elements=count, group_size=world, dtype=FLOAT32,
    )
    device = device_of(context)
    fp32 = getattr(torch, FLOAT32, None)
    send_buf = ones(torch, count, dtype=fp32, device=device)
    recv_buf = zeros(torch, count, dtype=fp32, device=device)

    def step(_slot: int) -> Any:
        ops = [
            dist.P2POp(dist.isend, send_buf, peer, group=group),
            dist.P2POp(dist.irecv, recv_buf, src, group=group),
        ]
        reqs = dist.batch_isend_irecv(ops)
        for req in reqs:
            req.wait()
        return recv_buf

    return wrap_ring_step(1, step)

def _mc2_dims(
    case: Mapping[str, Any], shape: Mapping[str, Any], elem_bytes: int,
    context: Mapping[str, Any] | None = None,
) -> tuple[int, int]:
    if "tokens" in shape or "width" in shape:
        return dims_2d(case)
    raw_bytes = case.get("nbytes") or shape.get("bytes")
    if not raw_bytes:
        return dims_2d(case)
    strides = case.get("strides")
    if not isinstance(strides, Mapping):
        ckey = case.get("canonical_key")
        strides = ckey.get("strides") if isinstance(ckey, Mapping) else None
    if not isinstance(strides, Mapping) and isinstance(context, Mapping):
        meta = context.get("_case_meta")
        strides = meta.get("strides") if isinstance(meta, Mapping) else None
    inp_stride = strides.get("input") if isinstance(strides, Mapping) else None
    width = int(OP_CFG["mc2_default_hidden_dim"])
    if isinstance(inp_stride, (list, tuple)) and len(inp_stride) >= 2:
        try:
            cand = int(inp_stride[0])
            if cand > 1:
                width = cand
        except (TypeError, ValueError):
            pass
    tokens = max(1, int(raw_bytes) // max(1, width * max(1, int(elem_bytes))))
    return tokens, width

def _resolve_hccl_comm_name(torch: Any, group: Any, ep_rank: int, fallback: str) -> str:
    backend_fn = getattr(group, "_get_backend", None)
    if not callable(backend_fn):
        return fallback
    backend_obj = None
    dev_ctor = getattr(torch, "device", None)
    if callable(dev_ctor):
        try:
            backend_obj = backend_fn(dev_ctor("npu"))
        except TypeError:
            backend_obj = backend_fn()
    else:
        backend_obj = backend_fn()
    namer = getattr(backend_obj, "get_hccl_comm_name", None)
    return str(namer(ep_rank)) if callable(namer) else fallback

def _resolve_mc2_group(case: Mapping[str, Any], context: Mapping[str, Any]) -> Any:
    groups = context.get("groups")
    if not isinstance(groups, Mapping):
        return None
    name = str(case.get("group") or case.get("route") or "")
    raw_ranks = case.get("group_ranks") or case.get("participants")
    if isinstance(raw_ranks, (list, tuple, set, frozenset)):
        ranks = sorted({int(x) for x in raw_ranks if isinstance(x, int) and not isinstance(x, bool)})
        if len(ranks) > 1:
            sig = ",".join(str(r) for r in ranks)
            for prefix in (name, "ep", "mc2", "group"):
                if prefix and f"{prefix}@{sig}" in groups:
                    return groups[f"{prefix}@{sig}"]
    declared_size = _declared_group_size(case, context)
    for prefix in (name, "ep", "mc2"):
        if prefix and f"{prefix}:{declared_size}" in groups:
            return groups[f"{prefix}:{declared_size}"]
    for prefix in (name, "ep", "mc2"):
        if prefix and prefix in groups:
            return groups[prefix]
    return None

def _mc2_expert_ids(
    torch: Any,
    tokens: int,
    top_k: int,
    moe_expert_num: int,
    device: str,
    *,
    ep_rank: int = 0,
    ep_world: int = 1,
) -> Any:
    int32 = getattr(torch, INT32, None)
    world = max(1, int(ep_world))
    rank = int(ep_rank) % world
    experts_per_rank = max(1, moe_expert_num // world)
    total = tokens * top_k
    if total > int(OP_CFG["mc2_expert_ids_python_limit"]):
        arange = getattr(torch, "arange", None)
        if callable(arange):
            try:
                flat = arange(total, dtype=int32, device=device)
                target_rank = (flat + rank) % world
                local_idx = (flat // world) % experts_per_rank
                eids = target_rank * experts_per_rank + local_idx
                view_fn = getattr(eids, "view", None)
                if callable(view_fn):
                    return view_fn(tokens, top_k)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                pass
    eid_rows = [
        [
            (((t * top_k + k_idx) + rank) % world) * experts_per_rank
            + (((t * top_k + k_idx) // world) % experts_per_rank)
            for k_idx in range(top_k)
        ]
        for t in range(tokens)
    ]
    return device_values(torch, eid_rows, dtype=int32, device=device)

def _mc2_builder(*, builder: str, upstream_abi: str, candidates: Sequence[str]) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        raw_dt = str(case.get("dtype") or BFLOAT16).strip().lower() or BFLOAT16
        eb = element_bytes(raw_dt)
        tokens, width = _mc2_dims(case, shape, eb, context)
        hcomm = str(context.get("hcomm_info") or case.get("group") or "tp")
        ep_world = max(1, int(context.get("ep_world_size") or case.get("group_size") or shape.get("group_size") or context.get("group_size") or 1))
        ep_rank = int(context.get("ep_rank_id") or context.get("rank") or case.get("ep_rank_id") or 0)
        group = _resolve_mc2_group(case, context)
        dist = context.get("dist") or getattr(torch, "distributed", None)
        if group is not None and dist is not None:
            rank_fn = getattr(dist, "get_rank", None)
            world_fn = getattr(dist, "get_world_size", None)
            if callable(rank_fn):
                ep_rank = int(rank_fn(group))
            if callable(world_fn):
                ep_world = int(world_fn(group))
            hcomm = _resolve_hccl_comm_name(torch, group, ep_rank, hcomm)
        raw_experts = dim_int(shape, "e", max(ep_world, int(OP_CFG["topk_gating_default"])))
        moe_expert_num = ((max(raw_experts, ep_world) + ep_world - 1) // ep_world) * ep_world
        top_k = max(1, min(moe_expert_num, dim_int(shape, "top_k", 1)))
        is_int8_comm = raw_dt == INT8
        is_fp8_comm = raw_dt in A5_ONLY_FP8_DTYPES
        if is_int8_comm or is_fp8_comm:
            x_dtype = torch_dtype(torch, BFLOAT16) or resolve_case_dtype(torch, case)
            quant_mode = int(OP_CFG["mc2_dispatch_quant_int8_mode"])
            y_dtype = torch_dtype(torch, raw_dt) if is_fp8_comm else None
        else:
            x_dtype = resolve_case_dtype(torch, case)
            quant_mode = 0
            y_dtype = None
        fp32 = getattr(torch, FLOAT32, x_dtype)
        actual_bytes = int(shape.get("bytes") or case.get("nbytes") or tokens * width * eb)
        record_actual_shape(
            context, tokens=tokens, width=width, e=raw_experts if "e" in shape else moe_expert_num,
            top_k=top_k, bytes=actual_bytes, nbytes=actual_bytes, group_size=ep_world, dtype=raw_dt,
        )
        x = zeros(torch, tokens, width, dtype=x_dtype, device=device)
        expert_ids = _mc2_expert_ids(
            torch, tokens, top_k, moe_expert_num, device, ep_rank=ep_rank, ep_world=ep_world,
        )
        scales = ones(torch, tokens, top_k, dtype=fp32, device=device)
        if "combine" in builder:
            dispatch_op = resolve_op(
                torch, "npu_moe_distribute_dispatch_v2", context=context, allow_torch_attr=False
            ) or resolve_op(
                torch, "npu_moe_distribute_dispatch", context=context, allow_torch_attr=False
            )
            expand_x = x
            assist_info = zeros(
                torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device
            )
            ep_counts = ones(torch, moe_expert_num, dtype=getattr(torch, INT32, None), device=device)
            combine_extra: dict[str, Any] = {}
            if callable(dispatch_op) and group is not None:
                disp_out = dispatch_op(
                    x=x, expert_ids=expert_ids, group_ep=hcomm,
                    ep_world_size=ep_world, ep_rank_id=ep_rank,
                    moe_expert_num=moe_expert_num,
                    expert_shard_type=0, shared_expert_rank_num=0,
                    quant_mode=0, global_bs=0,
                )
                min_out = int(OP_CFG["mc2_dispatch_min_outputs"])
                ep_idx = int(OP_CFG["mc2_dispatch_ep_counts_index"])
                sc_idx = int(OP_CFG["mc2_dispatch_scales_index"])
                if isinstance(disp_out, (tuple, list)) and len(disp_out) >= min_out:
                    expand_x = disp_out[0]
                    assist_info = disp_out[2]
                    ep_counts = disp_out[ep_idx]
                    if len(disp_out) > sc_idx and disp_out[sc_idx] is not None:
                        combine_extra["expand_scales"] = disp_out[sc_idx]
            return wrap_ring_step(
                1,
                lambda _s: op(
                    expand_x=expand_x, expert_ids=expert_ids,
                    assist_info_for_combine=assist_info, ep_send_counts=ep_counts,
                    expert_scales=scales, group_ep=hcomm, ep_world_size=ep_world,
                    ep_rank_id=ep_rank, moe_expert_num=moe_expert_num,
                    expert_shard_type=0, shared_expert_rank_num=0, global_bs=0,
                    **combine_extra,
                ),
                retain_outputs=True,
            )
        if "dispatch" in builder:
            dispatch_kw: dict[str, Any] = {
                "x": x, "expert_ids": expert_ids, "ep_world_size": ep_world,
                "ep_rank_id": ep_rank, "moe_expert_num": moe_expert_num,
                "group_ep": hcomm, "expert_scales": scales,
                "expert_shard_type": 0, "shared_expert_rank_num": 0,
                "quant_mode": quant_mode, "global_bs": 0,
            }
            if y_dtype is not None:
                dispatch_kw["y_dtype"] = y_dtype
            min_out = int(OP_CFG["mc2_dispatch_min_outputs"])
            nums_pos = int(OP_CFG["mc2_dispatch_expert_nums_index"])
            ep_pos = int(OP_CFG["mc2_dispatch_ep_counts_index"])

            def _run_dispatch(_s: int) -> Any:
                raw = op(**dispatch_kw)
                if isinstance(raw, (tuple, list)) and len(raw) >= min_out:
                    return (raw[nums_pos], raw[ep_pos])
                return raw

            return wrap_ring_step(1, _run_dispatch, retain_outputs=True)
        return wrap_ring_step(
            1, lambda _s: op(x, expert_ids, scales=scales), retain_outputs=True
        )

    return build

def _matmul_collective_builder(*, builder: str, upstream_abi: str, candidates: Sequence[str]) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        dtype = resolve_case_dtype(torch, case)
        x = zeros(torch, m, k, dtype=dtype, device=device)
        w = zeros(torch, k, n, dtype=dtype, device=device)
        hcomm = str(context.get("hcomm_info") or case.get("group") or "tp")
        world = max(1, int(context.get("group_size") or shape.get("group_size") or 1))
        record_actual_shape(context, m=m, n=n, k=k, group_size=world, dtype=dtype_name)
        return wrap_ring_step(1, lambda _s: op(x, w, hcomm, world), retain_outputs=True)

    return build

def build_muls_add(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("muls_add", "npu_muls_add", "muls_add_kernel", "addcmul"),
        builder="muls_add",
        upstream_abi="muls_add_kernel",
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(
        case, context, tokens * width * eb * int(OP_CFG["binary_io_tensor_count"])
    )
    a_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    b_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    c_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(
        slots, lambda s: op(a_ring[s], b_ring[s], c_ring[s]), retain_outputs=True
    )


def build_moe_ffn(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    """Bind fused MoE FFN with explicit expert gate/up/down weights and group_list."""
    candidates = ("npu_moe_ffn", "npu_fused_moe_ffn", "moe_ffn")
    op = None
    for cand in candidates:
        op = resolve_op(torch, cand, context=context, allow_torch_attr=False)
        if op is not None:
            break
    if op is None:
        return build_grouped_matmul(torch, case, context)
    shape, device = shape_of(case), device_of(context)
    m = dim_int(shape, "m", dim_int(shape, "tokens", 1))
    k = dim_int(shape, "k", dim_int(shape, "width", int(OP_CFG["attention_head_dim"])))
    n = dim_int(shape, "n", k)
    experts = max(1, dim_int(shape, "e", 2))
    counts, _cum = _expert_counts(case, m, experts)
    dtype_name = str(case.get("dtype") or BFLOAT16)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, (m * k + experts * k * n * 2 + m * k) * eb)
    x_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(m, k), dtype=dtype, dtype_name=dtype_name, device=device)
    w1_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(experts, k, n), dtype=dtype, dtype_name=dtype_name, device=device)
    w2_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(experts, n, k), dtype=dtype, dtype_name=dtype_name, device=device)
    gl = torch.tensor(counts, dtype=getattr(torch, INT64, None), device=device) if hasattr(torch, "tensor") else counts
    record_actual_shape(context, m=m, n=n, k=k, e=len(counts), dtype=dtype_name)
    return wrap_ring_step(slots, lambda s: op(x_ring[s], w1_ring[s], w2_ring[s], gl), retain_outputs=True)


MOE_COMM_BUILDERS: dict[str, Callable[..., Callable[[], Any]]] = {
    "matmul": build_matmul, "quant_matmul": build_quant_matmul,
    "grouped_matmul": build_grouped_matmul,
    "grouped_matmul_swiglu_quant": build_grouped_matmul_swiglu_quant,
    "moe_gating_topk": _moe_gating_builder(
        builder="moe_gating_topk", upstream_abi="aclnnMoeGatingTopKSoftmaxV2",
        candidates=("npu_moe_gating_top_k_softmax", "npu_moe_gating_top_k")),
    "moe_gating_topk_hash": _moe_gating_builder(
        builder="moe_gating_topk_hash", upstream_abi="aclnnMoeGatingTopKHash",
        candidates=("npu_moe_gating_top_k_hash", "moe_gating_top_k_hash", "moe_gating_topk_hash")),
    "moe_init_routing": build_moe_init_routing,
    "moe_token_permute": build_moe_token_permute,
    "moe_token_unpermute": build_moe_token_unpermute,
    "histogram_v2": build_histogram_v2,
    "mc2_dispatch": _mc2_builder(
        builder="mc2_dispatch", upstream_abi="aclnnMoeDistributeDispatchV2",
        candidates=("npu_moe_distribute_dispatch_v2", "npu_moe_distribute_dispatch", "mc2_dispatch")),
    "mc2_combine": _mc2_builder(
        builder="mc2_combine", upstream_abi="aclnnMoeDistributeCombineV2",
        candidates=("npu_moe_distribute_combine_v2", "npu_moe_distribute_combine", "mc2_combine")),
    "mc2_dispatch_v3": _mc2_builder(
        builder="mc2_dispatch_v3", upstream_abi="aclnnMoeDistributeDispatchV3",
        candidates=("npu_moe_distribute_dispatch_v3", "mc2_dispatch_v3")),
    "mc2_combine_v3": _mc2_builder(
        builder="mc2_combine_v3", upstream_abi="aclnnMoeDistributeCombineV3",
        candidates=("npu_moe_distribute_combine_v3", "mc2_combine_v3")),
    "megamoe_fused_mc2": _mc2_builder(
        builder="megamoe_fused_mc2", upstream_abi="aclnnMegaMoe",
        candidates=("npu_megamoe", "megamoe_fused_mc2")),
    "moe_ffn": build_moe_ffn,
    "matmul_reduce_scatter": _matmul_collective_builder(
        builder="matmul_reduce_scatter", upstream_abi="aclnnMatmulReduceScatter",
        candidates=("npu_mm_reduce_scatter_base", "matmul_reduce_scatter")),
    "all_gather_matmul": _matmul_collective_builder(
        builder="all_gather_matmul", upstream_abi="aclnnAllGatherMatmul",
        candidates=("npu_all_gather_base_mm", "all_gather_matmul")),
    "quantized_all_reduce": build_quantized_all_reduce,
    "p2p_send_recv": build_p2p_send_recv,
    "send_recv": build_send_recv,
    "muls_add": build_muls_add,
    **{
        alias: (lambda t, c, ctx, _k=kind: _bind_collective(t, c, ctx, _k))
        for alias, kind in COLLECTIVE_ALIASES.items()
    },
}

__all__ = ["COLLECTIVE_ALIASES", "COLLECTIVE_OPS", "MOE_COMM_BUILDERS", "_bind_collective"]
