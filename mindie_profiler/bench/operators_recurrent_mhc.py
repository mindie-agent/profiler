"""Recurrent GDN/KDA, mHC, PLE/Engram, sampling and elementwise bench builders.

[Role]
  Implement the 37 canonical GDN/KDA linear-attention, mHC / AttnRes,
  PLE / Engram host-offload, speculative/categorical sampling and elementwise
  builders with multi-slot cold-ring rotation and fail-fast kernel checks.

[Invariants]
  * ``ple_lookup`` and ``engram_uva_h2d`` never index a CPU tensor with an NPU
    index tensor; host slabs are indexed on CPU into pinned staging memory and
    copied asynchronously (``non_blocking=True``) to NPU buffers.
  * Every recurrent, mHC and sampling kernel is resolved explicitly without
    ``inspect.signature`` or unfused composite PyTorch fallbacks.

[Timeouts & Locks]
  Pure setup outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates tensors only on the caller-provided ``torch`` handle.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping, Sequence

from .operators_common import (
    BFLOAT16,
    FLOAT32,
    INT32,
    INT64,
    OP_CFG,
    UINT8,
    cold_ring_slot_count,
    device_of,
    device_values,
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
    wrap_ring_step,
    zeros,
)


def _conv1d_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str], update: bool
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch,
            case,
            context,
            candidates,
            builder=builder,
            upstream_abi=upstream_abi,
            extra_modules=("causal_conv1d", "fla.modules.convolution"),
        )
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        state_len = max(2, dim_int(shape, "state_len", int(OP_CFG["conv1d_state_len_default"])))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        slots = cold_ring_slot_count(case, context, tokens * width * state_len * eb)
        weight = randn(torch, width, state_len, dtype=dtype, device=device)
        if update:
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
                dtype_name=str(case.get("dtype", "bf16")), device=device,
            )
            st_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(tokens, width, state_len), dtype=dtype,
                dtype_name=str(case.get("dtype", "bf16")), device=device,
            )
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], st_ring[s], weight), retain_outputs=True
            )
        seq = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(1, width, tokens), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        return wrap_ring_step(slots, lambda s: op(seq[s], weight), retain_outputs=True)

    return build


def _recurrent_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    extra_modules: Sequence[str],
    tril: bool = False,
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates,
            builder=builder, upstream_abi=upstream_abi, extra_modules=extra_modules,
        )
        resolved = next((
            name for name in candidates
            if resolve_op(torch, name, context=context, extra_modules=extra_modules,
                          allow_torch_attr=False) is op
        ), str(getattr(op, "__name__", "") or ""))
        shape, device = shape_of(case), device_of(context)
        tokens = dim_int(shape, "tokens")
        heads = dim_int(shape, "heads", int(OP_CFG["topk_gating_default"]))
        head_dim = dim_int(shape, "head_dim", int(OP_CFG["attention_head_dim"]))
        dtype = resolve_case_dtype(torch, case)
        fp32 = getattr(torch, FLOAT32, dtype)
        eb = element_bytes(case.get("dtype", "bf16"))
        if tril:
            tile = int(OP_CFG["tril_tile_dim"])
            chunks = max(1, (tokens + tile - 1) // tile)
            slots = cold_ring_slot_count(case, context, chunks * heads * tile * tile * eb)
            mat = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(1, chunks, heads, tile, tile),
                dtype=fp32, dtype_name=FLOAT32, device=device,
            )
            return wrap_ring_step(slots, lambda s: op(mat[s]), retain_outputs=True)
        chunk_op = (
            resolved.startswith("npu_chunk_gated_delta_rule")
            or builder == "chunk_gated_delta_rule"
        ) and "fwd_prepare" not in resolved
        recurrent_op = resolved.startswith("npu_recurrent_gated_delta_rule") or builder in {
            "recurrent_gated_delta_rule", "recurrent_gdn_recover_ssm",
        }
        chunk_tnd = chunk_op and builder == "chunk_gated_delta_rule"
        tensor_dims = (tokens, heads, head_dim) if (chunk_tnd or recurrent_op) else (1, tokens, heads, head_dim)
        seq_lengths = device_values(
            torch, [tokens], dtype=getattr(torch, INT32, None), device=device
        )
        slots = cold_ring_slot_count(case, context, tokens * heads * head_dim * eb * int(OP_CFG["binary_io_tensor_count"]))
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=tensor_dims,
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        k_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=tensor_dims,
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        v_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=tensor_dims,
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        if builder == "fused_gdn_gating":
            a_log = zeros(torch, heads, dtype=fp32, device=device)
            dt_bias = zeros(torch, heads, dtype=fp32, device=device)
            beta = ones(torch, 1, tokens, heads, dtype=dtype, device=device)
            return wrap_ring_step(
                slots, lambda s: op(a_log, q_ring[s][:, :, :, 0], beta, dt_bias),
                retain_outputs=True,
            )
        if chunk_tnd:
            gated = zeros(torch, tokens, heads, dtype=fp32, device=device)
            beta = ones(torch, tokens, heads, dtype=dtype, device=device)
            state = zeros(torch, 1, heads, head_dim, head_dim, dtype=getattr(torch, BFLOAT16, dtype), device=device)
            scale = 1.0 / math.sqrt(head_dim)
            return wrap_ring_step(
                slots,
                lambda s: op(
                    q_ring[s], k_ring[s], v_ring[s], g=gated, beta=beta,
                    initial_state=state, actual_seq_lengths=seq_lengths, scale=scale,
                ),
                retain_outputs=True,
            )
        if recurrent_op:
            gated = zeros(torch, tokens, heads, dtype=fp32, device=device)
            beta = ones(torch, tokens, heads, dtype=dtype, device=device)
            state = zeros(torch, 1, heads, head_dim, head_dim, dtype=dtype, device=device)
            return wrap_ring_step(
                slots,
                lambda s: op(
                    q_ring[s], k_ring[s], v_ring[s], state,
                    beta=beta, g=gated, actual_seq_lengths=seq_lengths,
                ),
                retain_outputs=True,
            )
        kda_shape = builder in {"chunk_kda_fwd", "fused_recurrent_kda"}
        g_dims = (1, tokens, heads, head_dim) if kda_shape else (1, tokens, heads)
        gated = zeros(torch, *g_dims, dtype=fp32, device=device)
        beta = ones(torch, 1, tokens, heads, dtype=dtype, device=device)
        return wrap_ring_step(
            slots, lambda s: op(q_ring[s], k_ring[s], v_ring[s], gated, beta),
            retain_outputs=True,
        )

    return build


def _ssm_state_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str]
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype = resolve_case_dtype(torch, case)
        pool = randn(torch, max(tokens, 2), width, dtype=dtype, device=device)
        idx = zeros(torch, tokens, dtype=getattr(torch, INT32, None), device=device)
        state = randn(torch, tokens, width, dtype=dtype, device=device)
        return wrap_ring_step(
            1, lambda _s: op(pool, idx, state), retain_outputs=True
        )

    return build


def _mhc_builder(*, builder: str, upstream_abi: str, candidates: Sequence[str]) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        streams = max(1, dim_int(shape, "streams", int(OP_CFG["mhc_streams_default"])))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        fp32 = getattr(torch, FLOAT32, dtype)
        dtype_name = str(case.get("dtype", "bf16"))
        if builder == "hc_post":
            slots = cold_ring_slot_count(
                case, context, (tokens * width + tokens * streams * width) * eb
            )
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            res_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(tokens, streams, width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            post_t = ones(torch, tokens, streams, dtype=fp32, device=device)
            comb_t = ones(torch, tokens, streams, streams, dtype=fp32, device=device)
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], res_ring[s], post_t, comb_t),
                retain_outputs=True,
            )
        slots = cold_ring_slot_count(case, context, tokens * streams * width * eb)
        x_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, streams, width), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        mix = ones(torch, streams, streams, dtype=fp32, device=device)
        return wrap_ring_step(slots, lambda s: op(x_ring[s], mix), retain_outputs=True)

    return build


def build_ple_lookup(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="ple_lookup", upstream_abi="aclnnEmbedding")
    shape, device = shape_of(case), device_of(context)
    lookup = [int(item) for item in (case.get("lookup_ids") or ())]
    tokens = len(lookup) if lookup else dim_int(shape, "tokens")
    max_id = (max(lookup) + 1) if lookup else tokens
    rows = max(max_id, dim_int(shape, "rows", int(OP_CFG["engram_vocab_default"])))
    dtype_name = str(case.get("dtype", BFLOAT16)).lower()
    row_bytes = int(
        shape.get(
            "row_bytes",
            OP_CFG["ple_int8_row_bytes"] if dtype_name == "int8" else OP_CFG["ple_bf16_row_bytes"],
        )
    )
    path = str(case.get("path") or case.get("placement") or "hbm")
    reuse = str(case.get("reuse") or "repeated")
    base_ids = lookup if lookup else list(range(tokens))
    slot_map = case.get("slot_map")
    if isinstance(slot_map, Mapping):
        base_ids = [
            int(slot_map.get(str(item), slot_map.get(item, item))) for item in base_ids
        ]
    span = max(1, int(case.get("remap_span") or ((max(base_ids) + 1) if base_ids else rows)))
    span = min(span, rows)
    u8 = getattr(torch, UINT8, None)

    def ids_for(slot: int) -> list[int]:
        shift = slot if reuse == "rotating" else 0
        return [(int(item) + shift) % span for item in base_ids] or [0] * tokens

    def host_index(slot: int) -> Any:
        values = ids_for(slot)
        if hasattr(torch, "tensor"):
            return torch.tensor(values, dtype=getattr(torch, INT64, None), device="cpu")
        return zeros(torch, tokens, dtype=getattr(torch, INT64, None), device="cpu")

    if path in {"host_pinned", "uva", "host_dram", "uva_gather", "pinned_h2d"}:
        host_table = zeros(torch, rows, row_bytes, dtype=u8, device="cpu")
        slots = cold_ring_slot_count(case, context, tokens * row_bytes * 2)
        dst_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, row_bytes),
            dtype=u8, dtype_name=UINT8, device=device,
        )
        count = slots if reuse == "rotating" else 1
        if path in {"uva_gather", "uva"}:
            pin = getattr(host_table, "pin_memory", None)
            if callable(pin):
                host_table = pin()
            mapped = zeros(torch, rows, row_bytes, dtype=u8, device=device)
            copier = getattr(mapped, "copy_", None)
            if callable(copier):
                copier(host_table)
            int64_dt = getattr(torch, INT64, None)
            dev_idx = [device_values(torch, ids_for(slot), dtype=int64_dt, device=device)
                       for slot in range(count)]
            gather_op = resolve_op(torch, "npu_uva_gather", context=context, allow_torch_attr=False)

            def uva_step(slot: int) -> Any:
                index, target = dev_idx[slot % count], dst_ring[slot]
                if callable(gather_op):
                    return gather_op(host_table, index, out=target)
                try:
                    return torch.index_select(host_table, 0, index, out=target)
                except (TypeError, RuntimeError):
                    return torch.index_select(mapped, 0, index, out=target)

            return wrap_ring_step(slots, uva_step)
        cpu_idx_ring = [host_index(slot) for slot in range(count)]
        staged_ring = []
        for _ in range(count):
            staged = zeros(torch, tokens, row_bytes, dtype=u8, device="cpu")
            pin = getattr(staged, "pin_memory", None)
            staged_ring.append(pin() if callable(pin) else staged)

        def host_step(slot: int) -> Any:
            index = slot % count
            gathered = host_table.index_select(0, cpu_idx_ring[index])
            staged_ring[index].copy_(gathered)
            dst_ring[slot].copy_(staged_ring[index], non_blocking=True)
            return dst_ring[slot]

        return wrap_ring_step(slots, host_step)
    slots = cold_ring_slot_count(case, context, (rows + tokens) * row_bytes)
    table_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(rows, row_bytes),
        dtype=u8, dtype_name=UINT8, device=device,
    )
    count = slots if reuse == "rotating" else 1
    dev_idx_ring = [
        torch.tensor(
            ids_for(slot), dtype=getattr(torch, INT64, None), device=device
        ) if hasattr(torch, "tensor")
        else zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
        for slot in range(count)
    ]
    out_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, row_bytes),
        dtype=u8, dtype_name=UINT8, device=device,
    )

    def dev_step(slot: int) -> Any:
        index = dev_idx_ring[slot % count]
        try:
            return torch.index_select(table_ring[slot], 0, index, out=out_ring[slot])
        except TypeError:
            return table_ring[slot].index_select(0, index)

    return wrap_ring_step(slots, dev_step)


def build_engram_uva_h2d(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(
        torch, case, context, builder="engram_uva_h2d", upstream_abi="aclrtMemcpyAsync"
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    staged = zeros(torch, tokens, width, dtype=dtype, device="cpu")
    staged = staged.pin_memory() if callable(getattr(staged, "pin_memory", None)) else staged
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    dst_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: dst_ring[s].copy_(staged, non_blocking=True))


def build_engram_ngram_hash(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_engram_ngram_ids", "engram_ngram_ids_kernel", "engram_ngram_hash"),
        builder="engram_ngram_hash",
        upstream_abi="engram_ngram_ids_kernel",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    cols = dim_int(shape, "width", int(OP_CFG["engram_ngram_cols_default"]))
    ids = zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
    return wrap_ring_step(1, lambda _s: op(ids, cols), retain_outputs=True)


def build_vocab_embedding(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(
        torch, case, context, builder="vocab_embedding", upstream_abi="aclnnEmbedding"
    )
    fn_mod = getattr(getattr(torch, "nn", None), "functional", None)
    emb_fn = resolve_op(torch, "npu_embedding", context=context, allow_torch_attr=False) or (
        getattr(fn_mod, "embedding", None) if fn_mod is not None else None
    )
    if not callable(emb_fn):
        emb_fn = require_kernel(
            torch, case, context, ("npu_embedding", "embedding"),
            builder="vocab_embedding", upstream_abi="aclnnEmbedding",
        )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    vocab = max(2, dim_int(shape, "vocab_size", int(OP_CFG["vocab_size_default"])))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, (vocab + tokens) * width * eb)
    table = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(vocab, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    idx = zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
    return wrap_ring_step(slots, lambda s: emb_fn(idx, table[s]), retain_outputs=True)


def _sampler_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str]
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens = dim_int(shape, "tokens")
        vocab = max(2, dim_int(shape, "width", int(OP_CFG["vocab_size_default"])))
        fp32 = getattr(torch, FLOAT32, None)
        probs = ones(torch, tokens, vocab, dtype=fp32, device=device)
        if builder == "categorical_sampler":
            return wrap_ring_step(1, lambda _s: op(probs, 1), retain_outputs=True)
        draft_ids = zeros(torch, tokens, dtype=getattr(torch, INT32, None), device=device)
        return wrap_ring_step(1, lambda _s: op(probs, draft_ids), retain_outputs=True)

    return build


def _binary_ew_builder(
    *, builder: str, upstream_abi: str, op_name: str
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        require_npu_surface(torch, case, context, builder=builder, upstream_abi=upstream_abi)
        op = resolve_op(torch, op_name, context=context, allow_torch_attr=True)
        if not callable(op):
            raise_unmodeled(case, builder=builder, upstream_abi=upstream_abi, reason=f"{op_name}_missing")
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
        out_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )

        def step(slot: int) -> Any:
            try:
                return op(a_ring[slot], b_ring[slot], out=out_ring[slot])
            except TypeError:
                return op(a_ring[slot], b_ring[slot])

        return wrap_ring_step(slots, step)

    return build


def build_strided_gather(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(
        torch, case, context, builder="strided_gather", upstream_abi="aclnnIndexSelect"
    )
    device, shape = device_of(context), shape_of(case)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    if "length" in shape:
        tokens = dim_int(shape, "length")
        row_bytes = dim_int(shape, "row_bytes", int(OP_CFG["gather_row_bytes"]))
        stride_bytes = dim_int(shape, "stride_bytes", int(OP_CFG["cacheline_bytes"]))
        width = max(1, row_bytes // eb)
        step_stride = max(1, stride_bytes // max(1, row_bytes))
        rows = max(tokens, tokens * step_stride)
    else:
        tokens, width = dims_2d(case)
        step_stride = 1
        rows = max(tokens, dim_int(shape, "rows", tokens * 2))
    slots = cold_ring_slot_count(case, context, (rows + tokens) * width * eb)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(rows, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    out_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    idx = (
        torch.tensor(
            [i * step_stride for i in range(tokens)],
            dtype=getattr(torch, INT64, None),
            device=device,
        )
        if step_stride > 1 and hasattr(torch, "tensor")
        else zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
    )

    def step(slot: int) -> Any:
        try:
            return torch.index_select(src[slot], 0, idx, out=out_ring[slot])
        except TypeError:
            return src[slot].index_select(0, idx)

    return wrap_ring_step(slots, step)


def build_dtype_cast(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="dtype_cast", upstream_abi="aclnnCast")
    device = device_of(context)
    tokens, width = dims_2d(case)
    src_dt = resolve_case_dtype(torch, case)
    dst_name = str(case.get("output_dtype", FLOAT32))
    dst_dt = torch_dtype(torch, dst_name)
    slots = cold_ring_slot_count(
        case, context, tokens * width * (element_bytes(case.get("dtype", "bf16")) + element_bytes(dst_name))
    )
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=src_dt,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dst_dt,
        dtype_name=dst_name, device=device,
    )
    return wrap_ring_step(slots, lambda s: dst[s].copy_(src[s]))


def build_tensor_copy(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(
        torch, case, context, builder="tensor_copy", upstream_abi="aclnnInplaceCopy"
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: dst[s].copy_(src[s]))


def build_tensor_fill(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(
        torch, case, context, builder="tensor_fill", upstream_abi="aclnnInplaceZero"
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * width * eb)
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: dst[s].zero_())


def build_tensor_pad(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="tensor_pad", upstream_abi="aclnnPadV3")
    fn_mod = getattr(getattr(torch, "nn", None), "functional", None)
    pad_fn = resolve_op(torch, "tensor_pad", context=context, allow_torch_attr=False) or resolve_op(
        torch, "constant_pad_nd", context=context, allow_torch_attr=True
    ) or (getattr(fn_mod, "pad", None) if fn_mod is not None else None)
    if not callable(pad_fn):
        pad_fn = require_kernel(
            torch, case, context, ("tensor_pad", "constant_pad_nd"),
            builder="tensor_pad", upstream_abi="aclnnPadV3",
        )
    device = device_of(context)
    tokens, width = dims_2d(case)
    pad_w = int(OP_CFG["pad_width_default"])
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * (width + pad_w) * eb * 2)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: pad_fn(src[s], (0, pad_w)), retain_outputs=True)


def build_index_add(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="index_add", upstream_abi="aclnnIndexAdd")
    device, shape = device_of(context), shape_of(case)
    tokens, width = dims_2d(case)
    rows = max(1, dim_int(shape, "rows", tokens))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, (rows + tokens) * width * eb)
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(rows, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    contention = str(case.get("contention") or "")
    if contention == "shared_cacheline":
        idx = zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
    else:
        stride = max(1, -(-int(OP_CFG["cacheline_bytes"]) // max(1, width * eb)))
        values = (
            [(item * stride) % rows for item in range(tokens)]
            if contention == "disjoint_cacheline" else [0] * tokens
        )
        idx = device_values(torch, values, dtype=getattr(torch, INT64, None), device=device)
    return wrap_ring_step(slots, lambda s: dst[s].index_add_(0, idx, src[s]))


RECURRENT_MHC_BUILDERS: dict[str, Callable[..., Callable[[], Any]]] = {
    "causal_conv1d_fn": _conv1d_builder(
        builder="causal_conv1d_fn", upstream_abi="aclnnCausalConv1d",
        candidates=("npu_causal_conv1d", "causal_conv1d_fn"), update=False,
    ),
    "causal_conv1d_update": _conv1d_builder(
        builder="causal_conv1d_update", upstream_abi="aclnnCausalConv1dUpdate",
        candidates=("npu_causal_conv1d_update", "causal_conv1d_update"), update=True,
    ),
    "fused_gdn_gating": _recurrent_builder(
        builder="fused_gdn_gating", upstream_abi="fused_gdn_gating_kernel",
        candidates=("npu_fused_gdn_gating", "fused_gdn_gating"),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "chunk_gated_delta_rule": _recurrent_builder(
        builder="chunk_gated_delta_rule", upstream_abi="aclnnChunkGatedDeltaRuleFwd",
        candidates=("npu_chunk_gated_delta_rule", "chunk_gated_delta_rule"),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "chunk_gdn_fwd_prepare": _recurrent_builder(
        builder="chunk_gdn_fwd_prepare", upstream_abi="aclnnChunkGatedDeltaRuleFwdPrepare",
        candidates=("npu_chunk_gated_delta_rule_fwd_prepare", "chunk_gdn_fwd_prepare"),
        extra_modules=("fla.ops.gated_delta_rule.chunk",),
    ),
    "chunk_gdn_fwd_h": _recurrent_builder(
        builder="chunk_gdn_fwd_h", upstream_abi="aclnnChunkFwdH",
        candidates=("npu_chunk_fwd_h", "chunk_gated_delta_rule_fwd_h", "chunk_gdn_fwd_h"),
        extra_modules=("fla.ops.common.chunk_delta_h",),
    ),
    "chunk_gdn_fwd_o": _recurrent_builder(
        builder="chunk_gdn_fwd_o", upstream_abi="aclnnChunkFwdO",
        candidates=("npu_chunk_fwd_o", "chunk_fwd_o", "chunk_gdn_fwd_o"),
        extra_modules=("fla.ops.common.chunk_o",),
    ),
    "recurrent_gated_delta_rule": _recurrent_builder(
        builder="recurrent_gated_delta_rule", upstream_abi="aclnnRecurrentGatedDeltaRule",
        candidates=("npu_recurrent_gated_delta_rule", "fused_recurrent_gated_delta_rule"),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "recurrent_gdn_recover_ssm": _recurrent_builder(
        builder="recurrent_gdn_recover_ssm", upstream_abi="aclnnRecurrentGatedDeltaRule",
        candidates=(
            "npu_recurrent_gated_delta_rule",
            "recurrent_gdn_recover_ssm",
            "fused_recurrent_gated_delta_rule",
        ),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "chunk_kda_fwd": _recurrent_builder(
        builder="chunk_kda_fwd", upstream_abi="aclnnChunkKdaFwd",
        candidates=("npu_chunk_kda_fwd", "chunk_kda", "chunk_kda_fwd"),
        extra_modules=("fla.ops.kda",),
    ),
    "kda_chunk_products": _recurrent_builder(
        builder="kda_chunk_products", upstream_abi="aclnnChunkKdaFwdPrepare",
        candidates=("npu_chunk_kda_fwd_prepare", "chunk_kda_bwd_wy_intra", "kda_chunk_products"),
        extra_modules=("fla.ops.kda.chunk_intra",),
    ),
    "kda_chunk_output": _recurrent_builder(
        builder="kda_chunk_output", upstream_abi="aclnnChunkKdaFwdFinalize",
        candidates=("npu_chunk_kda_fwd_finalize", "kda_chunk_output", "chunk_fwd_o"),
        extra_modules=("fla.ops.kda", "fla.ops.common.chunk_o"),
    ),
    "kda_triangular_solve": _recurrent_builder(
        builder="kda_triangular_solve", upstream_abi="solve_tril_16x16_kernel",
        candidates=("npu_solve_tril", "solve_tril", "kda_triangular_solve"),
        extra_modules=("fla.ops.utils.solve_tril",), tril=True,
    ),
    "kda_wy_transform": _recurrent_builder(
        builder="kda_wy_transform", upstream_abi="recompute_w_u_fwd_kernel",
        candidates=("recompute_w_u_fwd", "kda_wy_transform"),
        extra_modules=("fla.ops.kda.wy_fast",),
    ),
    "fused_recurrent_kda": _recurrent_builder(
        builder="fused_recurrent_kda", upstream_abi="aclnnRecurrentKda",
        candidates=("npu_recurrent_kda", "fused_recurrent_kda"),
        extra_modules=("fla.ops.kda",),
    ),
    "ssm_state_gather": _ssm_state_builder(
        builder="ssm_state_gather", upstream_abi="_gather_ssm_states_kernel",
        candidates=("ssm_state_gather", "gather_ssm_states"),
    ),
    "ssm_state_scatter": _ssm_state_builder(
        builder="ssm_state_scatter", upstream_abi="_scatter_ssm_states_kernel",
        candidates=("ssm_state_scatter", "scatter_ssm_states"),
    ),
    "hc_pre": _mhc_builder(
        builder="hc_pre", upstream_abi="aclnnHcPre",
        candidates=("npu_hc_pre", "hc_pre"),
    ),
    "hc_post": _mhc_builder(
        builder="hc_post", upstream_abi="aclnnHcPost",
        candidates=("npu_hc_post", "hc_post"),
    ),
    "hc_combine_norm": _mhc_builder(
        builder="hc_combine_norm", upstream_abi="_hc_combine_norm_kernel",
        candidates=("hc_combine_norm", "_hc_combine_norm_kernel"),
    ),
    "mhc_stream_mix": _mhc_builder(
        builder="mhc_stream_mix", upstream_abi="mhc_hc_combine_kernel",
        candidates=("npu_mhc_stream_mix", "mhc_stream_mix"),
    ),
    "attn_res_prefix": _mhc_builder(
        builder="attn_res_prefix", upstream_abi="aclnnAttnResFwd",
        candidates=("npu_attn_res_fwd", "attn_res_fwd", "attn_res_prefix"),
    ),
    "vocab_embedding": build_vocab_embedding,
    "ple_lookup": build_ple_lookup,
    "engram_ngram_hash": build_engram_ngram_hash,
    "engram_uva_h2d": build_engram_uva_h2d,
    "gated_mul_add": _binary_ew_builder(
        builder="gated_mul_add", upstream_abi="aclnnMul", op_name="mul"
    ),
    "rejection_sampler": _sampler_builder(
        builder="rejection_sampler", upstream_abi="rejection_sample_kernel",
        candidates=("npu_rejection_sample", "rejection_sample", "rejection_sampler"),
    ),
    "categorical_sampler": _sampler_builder(
        builder="categorical_sampler", upstream_abi="_categorical_sample_kernel",
        candidates=("npu_categorical_sampler", "categorical_sampler", "multinomial"),
    ),
    "vector_add": _binary_ew_builder(builder="vector_add", upstream_abi="aclnnAdd", op_name="add"),
    "vector_mul_gate": _binary_ew_builder(
        builder="vector_mul_gate", upstream_abi="aclnnMul", op_name="mul"
    ),
    "vector_pack_indices": build_strided_gather,
    "dtype_cast": build_dtype_cast,
    "tensor_copy": build_tensor_copy,
    "tensor_fill": build_tensor_fill,
    "tensor_pad": build_tensor_pad,
    "strided_gather": build_strided_gather,
    "index_add": build_index_add,
}

__all__ = ["RECURRENT_MHC_BUILDERS"]
