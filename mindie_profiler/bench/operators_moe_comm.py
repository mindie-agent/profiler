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
    BFLOAT16,
    FLOAT32,
    INT8,
    INT32,
    INT64,
    OP_CFG,
    cast_weight_nz,
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
    torch_dtype,
    upstream_input,
    wrap_ring_step,
    zeros,
)

def _is_w4a8(case: Mapping[str, Any]) -> bool:
    dtype_str = str(case.get("dtype") or "").lower()
    meta = case.get("metadata") if isinstance(case.get("metadata"), Mapping) else {}
    wfmt = str((meta or {}).get("weight_format") or case.get("weight_format") or "").lower()
    return dtype_str in {"w4a8", "w4a16", "int4", "mxfp4"} or wfmt in {"w4a8", "w4a16", "int4", "mxfp4"}

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
        packed = pack_op(item) if callable(pack_op) else item
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
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, (m * k + k * n + m * n) * eb)
    left_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    nk_layout = str(case.get("layout") or "") == "NK"
    raw_right = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(n, k) if nk_layout else (k, n),
        dtype=dtype, dtype_name=dtype_name, device=device,
    )
    explicit_nz = str(case.get("layout") or "") == "FRACTAL_NZ"
    use_nz = case.get("format_code") == int(OP_CFG["nz_format_code"]) or explicit_nz
    if use_nz:
        right_ring = [
            cast_weight_nz(
                torch, item, context, case=case, builder="matmul", required=explicit_nz
            )
            for item in raw_right
        ]
    elif nk_layout:
        right_ring = [getattr(item, "t")() for item in raw_right]
    else:
        right_ring = raw_right
    out_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, n), dtype=dtype,
        dtype_name=dtype_name, device=device,
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
    if _is_w4a8(case):
        return _weight_quant_matmul(torch, case, context)
    op = require_kernel(
        torch, case, context, ("npu_quant_matmul",),
        builder="quant_matmul", upstream_abi="aclnnQuantMatmulWeightNz",
    )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    int8_dt = getattr(torch, INT8, None)
    out_name = str(case.get("output_dtype", BFLOAT16))
    out_dt = torch_dtype(torch, out_name)
    slots = cold_ring_slot_count(case, context, m * k + k * n + m * n * element_bytes(out_name))
    left_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(m, k), dtype=int8_dt,
        dtype_name=INT8, device=device,
    )
    nk_layout = str(case.get("layout") or "") == "NK"
    raw_right = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(n, k) if nk_layout else (k, n),
        dtype=int8_dt, dtype_name=INT8, device=device,
    )
    if nk_layout:
        right_ring = [getattr(item, "t")() for item in raw_right]
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

def build_grouped_matmul(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, ("npu_grouped_matmul",),
        builder="grouped_matmul", upstream_abi="aclnnGroupedMatmulV5",
    )
    shape, device = shape_of(case), device_of(context)
    m, n, k = dim_int(shape, "m"), dim_int(shape, "n"), dim_int(shape, "k")
    raw_gl = list(case.get("group_list") or ())
    experts = max(1, len(raw_gl) if raw_gl else dim_int(shape, "e", 1))
    counts, cumulative = _expert_counts(case, m, experts)
    experts = len(counts)
    w4 = _is_w4a8(case)
    quant = w4 or str(case.get("dtype", "")).lower() in {"int8", "fp8_e4m3", "mxfp8"}
    pack_op = resolve_op(torch, "npu_convert_weight_to_int4pack", context=context, allow_torch_attr=False) if w4 else None
    w_name = INT32 if w4 else (INT8 if quant else str(case.get("dtype", BFLOAT16)))
    w_dt = getattr(torch, w_name, None) if quant else resolve_case_dtype(torch, case)
    w_n = n if (not w4 or callable(pack_op)) else max(1, n // int(OP_CFG["int4_pack_int32_divisor"]))
    in_name = INT8 if quant else str(case.get("dtype", BFLOAT16))
    in_dt = getattr(torch, INT8, None) if quant else w_dt
    eb, out_eb = element_bytes(in_name), (2 if quant else element_bytes(in_name))
    w_bytes = experts * k * n // int(OP_CFG["int4_pack_divisor"]) if w4 else experts * k * n * eb
    slots = cold_ring_slot_count(case, context, m * k * eb + w_bytes + m * n * out_eb)
    group_list_type = int(case.get("group_list_type", 1))
    gl_vals = cumulative if group_list_type == 0 else counts
    group_list = torch.tensor(gl_vals, dtype=getattr(torch, INT64, None), device=device) if hasattr(torch, "tensor") else gl_vals
    x_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=(m, k), dtype=in_dt, dtype_name=in_name, device=device)
    w_dims = (1, k, w_n) if experts == 1 else (k, w_n)
    per_expert_rings = [slice_ring_tensors(torch, context, num_slots=slots, dims=w_dims, dtype=w_dt, dtype_name=w_name, device=device) for _ in range(experts)]
    w_slots = [
        [cast_weight_nz(torch, pack_op(per_expert_rings[e][s]) if callable(pack_op) else per_expert_rings[e][s], context) if quant else per_expert_rings[e][s]
         for e in range(experts)]
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
    return wrap_ring_step(slots, lambda s: op(
        [x_ring[s]], w_slots[s], bias=None, group_list=group_list,
        split_item=split_item, group_type=0, group_list_type=group_list_type, **quant_kw,
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
        experts = max(2, dim_int(shape, "e", int(OP_CFG["topk_gating_default"])))
        top_k = max(1, min(experts, dim_int(shape, "top_k", int(OP_CFG["topk_gating_default"]))))
        dtype = resolve_case_dtype(torch, case)
        slots = cold_ring_slot_count(
            case, context, tokens * experts * element_bytes(case.get("dtype", "bf16"))
        )
        logits = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, experts), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
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
    dtype = resolve_case_dtype(torch, case)
    x = randn(torch, tokens, width, dtype=dtype, device=device)
    expert_idx = zeros(torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device)
    return wrap_ring_step(
        1,
        lambda _s: op(
            x, expert_idx, active_num=tokens * top_k, expert_num=experts,
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
    dtype = resolve_case_dtype(torch, case)
    x = randn(torch, tokens, width, dtype=dtype, device=device)
    indices = zeros(torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device)
    return wrap_ring_step(1, lambda _s: op(x, indices), retain_outputs=True)

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
    dtype = resolve_case_dtype(torch, case)
    permuted = randn(torch, tokens * top_k, width, dtype=dtype, device=device)
    sorted_ids = zeros(torch, tokens * top_k, dtype=getattr(torch, INT32, None), device=device)
    probs = ones(torch, tokens, top_k, dtype=dtype, device=device)
    return wrap_ring_step(1, lambda _s: op(permuted, sorted_ids, probs=probs), retain_outputs=True)

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

def _declared_group_size(case: Mapping[str, Any], context: Mapping[str, Any]) -> int:
    shape = shape_of(case)
    declared = case.get("group_size") or shape.get("group_size") or context.get("group_size")
    try:
        return max(1, int(declared or 1))
    except (TypeError, ValueError):
        return 1


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
    fp_bytes = int(OP_CFG["float32_element_bytes"])
    nbytes = max(fp_bytes, int(case.get("nbytes") or shape.get("bytes")
                              or OP_CFG["collective_default_bytes"]))
    elements = max(1, nbytes // fp_bytes)
    world_fn = getattr(dist, "get_world_size", None)
    fallback_world = int(world_fn(group)) if callable(world_fn) and context.get("dist") is None else 1
    declared = case.get("group_size") or shape.get("group_size") or context.get("group_size")
    group_size = max(1, int(declared or fallback_world))
    fp32 = getattr(torch, FLOAT32, None)
    slots = cold_ring_slot_count(case, context, nbytes * 2)
    bufs = slice_ring_tensors(torch, context, num_slots=slots, dims=(elements,),
                              dtype=fp32, dtype_name=FLOAT32, device=device)
    if kind == "all_reduce":
        return wrap_ring_step(slots, lambda s: (dist.all_reduce(bufs[s], group=group), bufs[s])[1])
    if kind == "all_gather_into_tensor":
        outs = slice_ring_tensors(torch, context, num_slots=slots, dims=(elements * group_size,),
                                  dtype=fp32, dtype_name=FLOAT32, device=device)
        return wrap_ring_step(slots, lambda s: (
            dist.all_gather_into_tensor(outs[s], bufs[s], group=group), outs[s])[1])
    if kind == "reduce_scatter_tensor":
        outs = slice_ring_tensors(torch, context, num_slots=slots,
                                  dims=(max(1, elements // group_size),),
                                  dtype=fp32, dtype_name=FLOAT32, device=device)
        return wrap_ring_step(slots, lambda s: (
            dist.reduce_scatter_tensor(outs[s], bufs[s], group=group), outs[s])[1])
    if kind in {"all_to_all_single", "all_to_all_v"}:
        outs = slice_ring_tensors(torch, context, num_slots=slots, dims=(elements,),
                                  dtype=fp32, dtype_name=FLOAT32, device=device)
        if kind == "all_to_all_single":
            return wrap_ring_step(slots, lambda s: (
                dist.all_to_all_single(outs[s], bufs[s], group=group), outs[s])[1])
        send_c = [int(x) for x in (case.get("send_counts") or case.get("send_splits")
                                   or _default_splits(elements, group_size))]
        recv_c = [int(x) for x in (case.get("recv_counts") or case.get("recv_splits") or send_c)]
        return wrap_ring_step(slots, lambda s: (
            dist.all_to_all_single(outs[s], bufs[s], output_split_sizes=recv_c,
                                   input_split_sizes=send_c, group=group), outs[s])[1])
    peer = int(case.get("peer") or 0)
    if kind == "send":
        return wrap_ring_step(slots, lambda s: (dist.send(bufs[s], dst=peer, group=group), bufs[s])[1])
    return wrap_ring_step(slots, lambda s: (dist.recv(bufs[s], src=peer, group=group), bufs[s])[1])

def build_send_recv(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    direction = str(case.get("direction") or case.get("op") or "send")
    rank, pair = int(context.get("rank") or 0), case.get("pair")
    if direction not in {"send", "recv"}:
        direction = "send" if isinstance(pair, (list, tuple)) and rank == pair[0] else "recv"
    return _bind_collective(torch, case, context, direction)

def build_quantized_all_reduce(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = resolve_op(torch, "npu_quant_all_reduce", context=context, allow_torch_attr=False) or resolve_op(
        torch, "quantized_all_reduce", context=context, allow_torch_attr=False
    )
    if callable(op):
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype = resolve_case_dtype(torch, case)
        x = randn(torch, tokens, width, dtype=dtype, device=device)
        return wrap_ring_step(1, lambda _s: op(x), retain_outputs=True)
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_quant_all_reduce", "quant_all_reduce", "quantized_all_reduce"),
        builder="quantized_all_reduce",
        upstream_abi="hcclAllReduceInt8",
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    x = randn(torch, tokens, width, dtype=resolve_case_dtype(torch, case), device=device)
    return wrap_ring_step(1, lambda _s: op(x), retain_outputs=True)

def build_p2p_send_recv(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    op = resolve_op(torch, "npu_p2p_send_recv", context=context, allow_torch_attr=False) or resolve_op(
        torch, "p2p_send_recv", context=context, allow_torch_attr=False
    )
    if callable(op):
        device = device_of(context)
        tokens, width = dims_2d(case)
        buf = randn(torch, tokens, width, dtype=resolve_case_dtype(torch, case), device=device)
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
        int(case.get("nbytes") or shape_of(case).get("bytes") or OP_CFG["collective_default_bytes"]),
    )
    count = max(1, nbytes // int(OP_CFG["float32_element_bytes"]))
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

def _mc2_builder(*, builder: str, upstream_abi: str, candidates: Sequence[str]) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        experts = max(1, dim_int(shape, "e", int(OP_CFG["topk_gating_default"])))
        top_k = max(1, min(experts, dim_int(shape, "top_k", 1)))
        dtype = resolve_case_dtype(torch, case)
        fp32 = getattr(torch, FLOAT32, dtype)
        x = randn(torch, tokens, width, dtype=dtype, device=device)
        expert_ids = zeros(torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device)
        scales = ones(torch, tokens, top_k, dtype=fp32, device=device)
        hcomm = str(context.get("hcomm_info") or case.get("group") or "tp")
        ep_world = max(1, int(context.get("ep_world_size") or case.get("group_size") or context.get("group_size") or 1))
        ep_rank = int(context.get("ep_rank_id") or context.get("rank") or case.get("ep_rank_id") or 0)
        groups = context.get("groups")
        declared_size = _declared_group_size(case, context)
        sized = (groups.get(f"ep:{declared_size}") or groups.get(f"mc2:{declared_size}")
                 if isinstance(groups, Mapping) else None)
        group = sized or ((groups.get("ep") or groups.get("mc2"))
                          if isinstance(groups, Mapping) else None)
        dist = context.get("dist") or getattr(torch, "distributed", None)
        if group is not None and dist is not None:
            rank_fn = getattr(dist, "get_rank", None)
            world_fn = getattr(dist, "get_world_size", None)
            if callable(rank_fn):
                ep_rank = int(rank_fn(group))
            if callable(world_fn):
                ep_world = int(world_fn(group))
            backend_fn = getattr(group, "_get_backend", None)
            if callable(backend_fn):
                namer = getattr(backend_fn(), "get_hccl_comm_name", None)
                if callable(namer):
                    hcomm = str(namer(ep_rank))
        if "combine" in builder:
            assist_info = zeros(
                torch, tokens, top_k, dtype=getattr(torch, INT32, None), device=device
            )
            ep_counts = ones(torch, experts, dtype=getattr(torch, INT32, None), device=device)
            return wrap_ring_step(
                1,
                lambda _s: op(
                    expand_x=x, expert_ids=expert_ids,
                    assist_info_for_combine=assist_info, ep_send_counts=ep_counts,
                    expert_scales=scales, group_ep=hcomm, ep_world_size=ep_world,
                    ep_rank_id=ep_rank, moe_expert_num=experts,
                ),
                retain_outputs=True,
            )
        if "dispatch" in builder:
            return wrap_ring_step(
                1,
                lambda _s: op(
                    x=x, expert_ids=expert_ids, ep_world_size=ep_world,
                    ep_rank_id=ep_rank, moe_expert_num=experts,
                    group_ep=hcomm, expert_scales=scales,
                ),
                retain_outputs=True,
            )
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
        dtype = resolve_case_dtype(torch, case)
        x = randn(torch, m, k, dtype=dtype, device=device)
        w = randn(torch, k, n, dtype=dtype, device=device)
        hcomm = str(context.get("hcomm_info") or case.get("group") or "tp")
        world = max(1, int(context.get("group_size") or shape.get("group_size") or 1))
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
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
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
