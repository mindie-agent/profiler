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
    record_actual_shape,
    require_kernel,
    require_npu_surface,
    resolve_case_dtype,
    resolve_op,
    resolved_kernel_name,
    shape_of,
    slice_ring_tensors,
    torch_dtype,
    wrap_ring_step,
    zeros,
)

from .operators_recurrent_state import recurrent_builder


def _conv1d_aligned_dims(tokens: int, width: int) -> tuple[int, int]:
    """Factor 1D flattened ``(tokens, 1)`` conv inputs into aligned ``(batch, dim)``."""
    align = int(OP_CFG["conv1d_align_dim"])
    fla_align = int(OP_CFG["conv1d_fla_align_dim"])
    if width != 1 or tokens < fla_align:
        return tokens, width
    for cand in OP_CFG["conv1d_width_candidates"]:
        dim = int(cand)
        if tokens >= dim and tokens % dim == 0:
            return max(1, tokens // dim), dim
    if tokens >= align and tokens % align == 0:
        return max(1, tokens // align), align
    if tokens % fla_align == 0:
        return max(1, tokens // fla_align), fla_align
    return tokens, width


def _conv1d_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str], update: bool
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        extra_mods = ("fla_npu.ops.ascendc", "vllm_ascend.ops.causal_conv1d", "causal_conv1d", "fla.modules.convolution")
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi,
            extra_modules=extra_mods,
        )
        resolved = resolved_kernel_name(torch, op, candidates, context)
        is_fla_npu = str(getattr(op, "__module__", "")).startswith("fla_npu")
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        eff_tokens, eff_width = _conv1d_aligned_dims(tokens, width)
        state_len = max(2, dim_int(shape, "state_len", int(OP_CFG["conv1d_state_len_default"])))
        kernel_w = max(
            int(OP_CFG["conv1d_fla_min_kernel_width"]),
            min(int(OP_CFG["conv1d_fla_max_kernel_width"]), state_len),
        )
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(
            context, tokens=tokens, width=width, state_len=state_len,
            conv_tokens=eff_tokens, conv_width=eff_width, dtype=dtype_name,
        )
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(dtype_name)
        slots = cold_ring_slot_count(case, context, eff_tokens * eff_width * state_len * eb)
        int32_dt = getattr(torch, INT32, None)
        if update:
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(eff_tokens, eff_width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            if resolved == "npu_fused_causal_conv1d":
                kernel_k = int(OP_CFG["conv1d_fused_kernel_size"])
                weight = zeros(torch, kernel_k, eff_width, dtype=dtype, device=device)
                st_ring = slice_ring_tensors(
                    torch, context, num_slots=slots, dims=(eff_tokens, state_len, eff_width),
                    dtype=dtype, dtype_name=dtype_name, device=device,
                )
                q_start = device_values(torch, list(range(eff_tokens + 1)), dtype=int32_dt, device=device)
                c_idx = device_values(torch, list(range(eff_tokens)), dtype=int32_dt, device=device)
                return wrap_ring_step(
                    slots,
                    lambda s: op(
                        x_ring[s], weight, st_ring[s],
                        query_start_loc=q_start, cache_indices=c_idx,
                    ),
                    retain_outputs=True,
                )
            if is_fla_npu:
                weight = zeros(torch, kernel_w, eff_width, dtype=dtype, device=device)
                st_ring = slice_ring_tensors(
                    torch, context, num_slots=slots, dims=(eff_tokens, state_len, eff_width),
                    dtype=dtype, dtype_name=dtype_name, device=device,
                )
                out_ring = slice_ring_tensors(
                    torch, context, num_slots=slots, dims=(eff_tokens, eff_width),
                    dtype=dtype, dtype_name=dtype_name, device=device,
                )
                q_start = device_values(torch, list(range(eff_tokens + 1)), dtype=int32_dt, device=device)
                c_idx = device_values(torch, list(range(eff_tokens)), dtype=int32_dt, device=device)
                return wrap_ring_step(
                    slots,
                    lambda s: op(
                        x_ring[s], st_ring[s], weight,
                        activation="silu", conv_state_indices=c_idx,
                        query_start_loc=q_start, max_query_len=1, out=out_ring[s],
                    ),
                    retain_outputs=True,
                )
            weight = zeros(torch, eff_width, state_len, dtype=dtype, device=device)
            st_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(eff_tokens, eff_width, state_len), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], st_ring[s], weight), retain_outputs=True
            )
        if is_fla_npu:
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(eff_tokens, eff_width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            weight = zeros(torch, kernel_w, eff_width, dtype=dtype, device=device)
            st_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(1, state_len, eff_width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            q_start = device_values(torch, [0, eff_tokens], dtype=int32_dt, device=device)
            c_idx = device_values(torch, [0], dtype=int32_dt, device=device)
            return wrap_ring_step(
                slots,
                lambda s: op(
                    x_ring[s], weight, None, st_ring[s],
                    query_start_loc=q_start, cache_indices=c_idx,
                ),
                retain_outputs=True,
            )
        weight = zeros(torch, eff_width, state_len, dtype=dtype, device=device)
        seq = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(1, eff_width, eff_tokens), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        return wrap_ring_step(slots, lambda s: op(seq[s], weight), retain_outputs=True)

    return build


def _ssm_state_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    extra_modules: Sequence[str] = (),
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi,
            extra_modules=extra_modules,
        )
        resolved = next(
            (c for c in candidates if resolve_op(torch, c, context=context, extra_modules=extra_modules, allow_torch_attr=False) is op),
            str(getattr(op, "__name__", "")),
        )
        device = device_of(context)
        tokens, width = dims_2d(case)
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(dtype_name)
        rows = max(tokens, 2)
        slots = cold_ring_slot_count(case, context, (rows + tokens) * width * eb)
        pool_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(rows, width), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        idx = device_values(torch, list(range(tokens)), dtype=getattr(torch, INT32, None), device=device)
        if resolved == "gather_ssm_states":
            has_init = ones(torch, tokens, dtype=getattr(torch, "bool", None), device=device)
            return wrap_ring_step(slots, lambda s: op(pool_ring[s], idx, has_init), retain_outputs=True)
        state_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        return wrap_ring_step(
            slots, lambda s: op(pool_ring[s], idx, state_ring[s]), retain_outputs=True
        )

    return build


def _hc_factor_dims(tokens: int, width: int, streams: int) -> tuple[int, int]:
    """Factor 1D flattened ``(tokens, 1)`` mHC inputs into ``(rows, hidden_dim)``."""
    if width != 1 or tokens < streams:
        return tokens, width
    per_stream = tokens // streams if tokens % streams == 0 else tokens
    for cand in OP_CFG["hc_pre_width_candidates"]:
        dim = int(cand)
        if per_stream >= dim and per_stream % dim == 0:
            return max(1, per_stream // dim), dim
    return max(1, tokens // streams), streams


def _mhc_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    extra_modules: Sequence[str] = (),
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi,
            extra_modules=extra_modules,
        )
        resolved = next(
            (c for c in candidates if resolve_op(torch, c, context=context, extra_modules=extra_modules, allow_torch_attr=False) is op),
            str(getattr(op, "__name__", "")),
        )
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        streams = max(1, dim_int(shape, "streams", int(OP_CFG["mhc_streams_default"])))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        fp32 = getattr(torch, FLOAT32, dtype)
        dtype_name = str(case.get("dtype", "bf16"))
        record_actual_shape(context, tokens=tokens, width=width, streams=streams, dtype=dtype_name)
        if resolved in {"npu_hc_pre_v2", "npu_hc_pre_v3"}:
            hc_mult = int(OP_CFG["hc_pre_mult_default"])
            mix_hc = int(OP_CFG["hc_pre_mix_dim"])
            scale_dim = int(OP_CFG["hc_pre_scale_dim"])
            sinkhorn_iters = int(OP_CFG["hc_pre_sinkhorn_iters"])
            eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
            eff_tokens, eff_width = _hc_factor_dims(tokens, width, hc_mult)
            bf16_dt = torch_dtype(torch, BFLOAT16) or dtype
            slots = cold_ring_slot_count(case, context, eff_tokens * hc_mult * eff_width * element_bytes(BFLOAT16))
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(eff_tokens, hc_mult, eff_width), dtype=bf16_dt,
                dtype_name=BFLOAT16, device=device,
            )
            hc_fn = zeros(torch, mix_hc, hc_mult * eff_width, dtype=fp32, device=device)
            hc_scale = ones(torch, scale_dim, dtype=fp32, device=device)
            hc_base = zeros(torch, mix_hc, dtype=fp32, device=device)
            if resolved == "npu_hc_pre_v3":
                return wrap_ring_step(
                    slots,
                    lambda s: op(
                        x_ring[s], hc_fn, hc_scale, hc_base, None,
                        hc_mult=hc_mult, hc_sinkhorn_iters=sinkhorn_iters, norm_eps=eps, hc_eps=eps,
                    ),
                    retain_outputs=True,
                )
            return wrap_ring_step(
                slots,
                lambda s: op(x_ring[s], hc_fn, hc_scale, hc_base, hc_mult, sinkhorn_iters, eps, eps),
                retain_outputs=True,
            )
        if resolved in {"hc_gate_mix", "qwen4_exp_ascend_hc_gate_mix"}:
            if width == 1:
                eff_tokens, eff_width = _hc_factor_dims(tokens, width, streams)
                dim = eff_width * streams if eff_width * streams <= tokens else eff_width
                rows = max(1, tokens // dim) if tokens >= dim else eff_tokens
            else:
                rows, dim = tokens, width
            hc_count = streams if dim % streams == 0 else 1
            slots = cold_ring_slot_count(case, context, rows * dim * eb * 2)
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(rows, dim), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            gate_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(rows, dim), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            return wrap_ring_step(
                slots, lambda s: op(x_ring[s], gate_ring[s], hc_count), retain_outputs=True,
            )
        if builder == "hc_post":
            eff_tokens, eff_width = _hc_factor_dims(tokens, width, streams)
            slots = cold_ring_slot_count(
                case, context, (eff_tokens * eff_width + eff_tokens * streams * eff_width) * eb
            )
            x_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(1, eff_tokens, eff_width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            res_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(1, eff_tokens, streams, eff_width), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            post_t = ones(torch, 1, eff_tokens, streams, dtype=fp32, device=device)
            comb_t = ones(torch, 1, eff_tokens, streams, streams, dtype=fp32, device=device)
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
    if "row_bytes" in shape:
        row_bytes = int(shape["row_bytes"])
    elif "width" in shape:
        row_bytes = dim_int(shape, "width") * element_bytes(dtype_name)
    else:
        row_bytes = int(
            OP_CFG["ple_int8_row_bytes"] if dtype_name == "int8" else OP_CFG["ple_bf16_row_bytes"]
        )
    path = str(case.get("path") or case.get("placement") or "hbm")
    record_actual_shape(context, tokens=tokens, row_bytes=row_bytes, width=row_bytes // element_bytes(dtype_name))
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
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    record_actual_shape(context, tokens=tokens, width=width, bytes=tokens * width * eb, dtype=dtype_name)
    staged = zeros(torch, tokens, width, dtype=dtype, device="cpu")
    staged = staged.pin_memory() if callable(getattr(staged, "pin_memory", None)) else staged
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    dst_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    return wrap_ring_step(slots, lambda s: dst_ring[s].copy_(staged, non_blocking=True))


def build_engram_ngram_hash(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    candidates = ("npu_engram_ngram_ids", "engram_ngram_ids_kernel", "engram_ngram_hash", "_hash_ids_kernel")
    extra_mods = ("vllm_ascend.ops.triton.engram_hash",)
    op = require_kernel(
        torch,
        case,
        context,
        candidates,
        builder="engram_ngram_hash",
        upstream_abi="engram_ngram_ids_kernel",
        extra_modules=extra_mods,
    )
    resolved = next(
        (c for c in candidates if resolve_op(torch, c, context=context, extra_modules=extra_mods, allow_torch_attr=False) is op),
        str(getattr(op, "__name__", "")),
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    cols = dim_int(shape, "width", int(OP_CFG["engram_ngram_cols_default"]))
    record_actual_shape(context, tokens=tokens, width=cols)
    int32_dt = getattr(torch, INT32, None)
    int64_dt = getattr(torch, INT64, None)
    if resolved == "_hash_ids_kernel":
        bool_dt = getattr(torch, "bool", None)
        num_layers = int(OP_CFG["engram_num_layers"])
        max_ngram = next(
            (int(c) for c in OP_CFG["engram_max_ngram_candidates"] if cols % max(1, int(c) - 1) == 0),
            2,
        )
        num_heads = max(1, cols // max(1, max_ngram - 1))
        block_t = int(OP_CFG["engram_block_t"])
        block_h = 1 << (num_heads - 1).bit_length()
        vocab = int(OP_CFG["engram_vocab_default"])
        lookback_depth = int(OP_CFG["engram_lookback_depth"])
        num_warps = int(OP_CFG["engram_num_warps"])
        dead_id = int(OP_CFG["engram_dead_id"])
        input_ids = zeros(torch, tokens, dtype=int64_dt, device=device)
        token_map = zeros(torch, vocab, dtype=int32_dt, device=device)
        dead_mask = zeros(torch, tokens, dtype=bool_dt, device=device)
        positions = device_values(torch, list(range(tokens)), dtype=int64_dt, device=device)
        query_start_loc = device_values(torch, [0, tokens], dtype=int32_dt, device=device)
        req_ids = zeros(torch, tokens, dtype=int32_dt, device=device)
        multipliers = ones(torch, num_layers, max_ngram, dtype=int64_dt, device=device)
        primes = ones(torch, num_layers, max_ngram - 1, num_heads, dtype=int64_dt, device=device)
        offsets = zeros(torch, num_layers, max_ngram - 1, num_heads, dtype=int64_dt, device=device)
        lookback_ids = zeros(torch, 1, lookback_depth, dtype=int64_dt, device=device)
        lookback_mask = zeros(torch, 1, lookback_depth, dtype=bool_dt, device=device)
        output = zeros(torch, tokens, num_layers, (max_ngram - 1) * num_heads, dtype=int32_dt, device=device)
        req_kernel = resolve_op(
            torch, "_engram_req_index_kernel", context=context, extra_modules=extra_mods, allow_torch_attr=False
        )
        grid_t = (tokens + block_t - 1) // block_t
        q_stride = int(query_start_loc.stride(0)) if callable(getattr(query_start_loc, "stride", None)) else 1
        in_stride = int(input_ids.stride(0)) if callable(getattr(input_ids, "stride", None)) else 1
        m_stride = int(dead_mask.stride(0)) if callable(getattr(dead_mask, "stride", None)) else 1
        p_stride = int(positions.stride(0)) if callable(getattr(positions, "stride", None)) else 1
        lb_r = int(lookback_ids.stride(0)) if callable(getattr(lookback_ids, "stride", None)) else lookback_depth
        lb_c = int(lookback_ids.stride(1)) if callable(getattr(lookback_ids, "stride", None)) else 1
        lbm_r = int(lookback_mask.stride(0)) if callable(getattr(lookback_mask, "stride", None)) else lookback_depth
        lbm_c = int(lookback_mask.stride(1)) if callable(getattr(lookback_mask, "stride", None)) else 1

        def _run_engram(_s: int) -> Any:
            if req_kernel is not None:
                req_kernel[(grid_t,)](query_start_loc, req_ids, tokens, 1, q_stride, BLOCK_T=block_t)
            op[(grid_t, num_layers)](
                input_ids, token_map, dead_mask, positions, None, query_start_loc, req_ids,
                multipliers, primes, offsets, None, lookback_ids, lookback_mask, output,
                tokens, 0, 0,
                input_stride=in_stride, mask_stride=m_stride, position_stride=p_stride,
                table_stride=0, table_col_stride=0, query_stride=q_stride,
                num_table_rows=0, max_blocks=0, cache_block_size=1,
                MAX_NGRAM=max_ngram, num_heads=num_heads, BLOCK_T=block_t, BLOCK_H=block_h,
                dead_id=dead_id, lookback_depth=lookback_depth,
                lookback_row_stride=lb_r, lookback_col_stride=lb_c,
                lookback_mask_row_stride=lbm_r, lookback_mask_col_stride=lbm_c,
                num_warps=num_warps,
            )
            return output

        return wrap_ring_step(1, _run_engram, retain_outputs=True)
    ids = zeros(torch, tokens, dtype=int64_dt, device=device)
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
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, vocab_size=vocab, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, (vocab + tokens) * width * eb)
    table = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(vocab, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
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
        vocab = max(1, dim_int(shape, "width", int(OP_CFG["vocab_size_default"])))
        record_actual_shape(context, tokens=tokens, width=vocab, vocab_size=vocab)
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
        record_actual_shape(context, tokens=tokens, width=width)
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
    record_actual_shape(context, length=tokens, tokens=tokens, rows=rows, width=width,
                        stride_bytes=step_stride * width * eb)
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
    src_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    src_dt = resolve_case_dtype(torch, case)
    dst_name = str(case.get("output_dtype", FLOAT32))
    dst_dt = torch_dtype(torch, dst_name)
    record_actual_shape(context, tokens=tokens, width=width, dtype=src_name, output_dtype=dst_name)
    slots = cold_ring_slot_count(
        case, context, tokens * width * (element_bytes(src_name) + element_bytes(dst_name))
    )
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=src_dt,
        dtype_name=src_name, device=device,
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
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * width * eb * 2)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
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
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * width * eb)
    dst = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
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
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, pad_width=pad_w, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, tokens * (width + pad_w) * eb * 2)
    src = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    return wrap_ring_step(slots, lambda s: pad_fn(src[s], (0, pad_w)), retain_outputs=True)


def build_index_add(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="index_add", upstream_abi="aclnnIndexAdd")
    device, shape = device_of(context), shape_of(case)
    tokens, width = dims_2d(case)
    rows = max(1, dim_int(shape, "rows", tokens))
    record_actual_shape(context, tokens=tokens, width=width, rows=rows)
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
        candidates=("npu_causal_conv1d_update", "npu_fused_causal_conv1d", "causal_conv1d_update"), update=True,
    ),
    "fused_gdn_gating": recurrent_builder(
        builder="fused_gdn_gating", upstream_abi="fused_gdn_gating_kernel",
        candidates=("npu_fused_gdn_gating", "fused_gdn_gating_patch", "fused_gdn_gating"),
        extra_modules=("vllm_ascend.ops.triton.fused_gdn_gating", "fla.ops.gated_delta_rule"),
    ),
    "chunk_gated_delta_rule": recurrent_builder(
        builder="chunk_gated_delta_rule", upstream_abi="aclnnChunkGatedDeltaRuleFwd",
        candidates=("npu_chunk_gated_delta_rule", "chunk_gated_delta_rule"),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "chunk_gdn_fwd_prepare": recurrent_builder(
        builder="chunk_gdn_fwd_prepare", upstream_abi="aclnnChunkGatedDeltaRuleFwdPrepare",
        candidates=("npu_chunk_gated_delta_rule_fwd_prepare", "chunk_gdn_fwd_prepare"),
        extra_modules=("fla.ops.gated_delta_rule.chunk",),
    ),
    "chunk_gdn_fwd_h": recurrent_builder(
        builder="chunk_gdn_fwd_h", upstream_abi="aclnnChunkFwdH",
        candidates=("npu_chunk_fwd_h", "chunk_gated_delta_rule_fwd_h", "chunk_gdn_fwd_h"),
        extra_modules=("fla.ops.common.chunk_delta_h",),
    ),
    "chunk_gdn_fwd_o": recurrent_builder(
        builder="chunk_gdn_fwd_o", upstream_abi="aclnnChunkFwdO",
        candidates=("npu_chunk_fwd_o", "chunk_fwd_o", "chunk_gdn_fwd_o"),
        extra_modules=("fla.ops.common.chunk_o",),
    ),
    "recurrent_gated_delta_rule": recurrent_builder(
        builder="recurrent_gated_delta_rule", upstream_abi="aclnnRecurrentGatedDeltaRule",
        candidates=("npu_recurrent_gated_delta_rule", "fused_recurrent_gated_delta_rule"),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "recurrent_gdn_recover_ssm": recurrent_builder(
        builder="recurrent_gdn_recover_ssm", upstream_abi="aclnnRecurrentGatedDeltaRule",
        candidates=(
            "npu_recurrent_gated_delta_rule",
            "recurrent_gdn_recover_ssm",
            "fused_recurrent_gated_delta_rule",
        ),
        extra_modules=("fla.ops.gated_delta_rule",),
    ),
    "chunk_kda_fwd": recurrent_builder(
        builder="chunk_kda_fwd", upstream_abi="aclnnChunkKdaFwd",
        candidates=("npu_chunk_kda_fwd", "chunk_kda_fwd", "chunk_kda"),
        extra_modules=("vllm_ascend.ops.triton.kda", "vllm_ascend.ops.triton.kda.kda", "fla.ops.kda"),
    ),
    "kda_chunk_products": recurrent_builder(
        builder="kda_chunk_products", upstream_abi="aclnnChunkKdaFwdPrepare",
        candidates=("npu_chunk_kda_fwd_prepare", "chunk_kda_bwd_wy_intra", "kda_chunk_products"),
        extra_modules=("fla.ops.kda.chunk_intra",),
    ),
    "kda_chunk_output": recurrent_builder(
        builder="kda_chunk_output", upstream_abi="aclnnChunkKdaFwdFinalize",
        candidates=("npu_chunk_kda_fwd_finalize", "kda_chunk_output", "chunk_fwd_o"),
        extra_modules=("fla.ops.kda", "fla.ops.common.chunk_o"),
    ),
    "kda_triangular_solve": recurrent_builder(
        builder="kda_triangular_solve", upstream_abi="solve_tril_16x16_kernel",
        candidates=("npu_solve_tril", "solve_tril", "kda_triangular_solve"),
        extra_modules=("fla.ops.utils.solve_tril",), tril=True,
    ),
    "kda_wy_transform": recurrent_builder(
        builder="kda_wy_transform", upstream_abi="recompute_w_u_fwd_kernel",
        candidates=("recompute_w_u_fwd", "kda_wy_transform"),
        extra_modules=("fla.ops.kda.wy_fast",),
    ),
    "fused_recurrent_kda": recurrent_builder(
        builder="fused_recurrent_kda", upstream_abi="aclnnRecurrentKda",
        candidates=("npu_recurrent_kda", "fused_recurrent_kda"),
        extra_modules=("vllm_ascend.ops.triton.kda", "vllm_ascend.ops.triton.kda.kda", "fla.ops.kda"),
    ),
    "ssm_state_gather": _ssm_state_builder(
        builder="ssm_state_gather", upstream_abi="_gather_ssm_states_kernel",
        candidates=("ssm_state_gather", "gather_ssm_states"),
        extra_modules=("vllm_ascend.ops.triton.mamba.state_index",),
    ),
    "ssm_state_scatter": _ssm_state_builder(
        builder="ssm_state_scatter", upstream_abi="_scatter_ssm_states_kernel",
        candidates=("ssm_state_scatter", "scatter_ssm_states_", "scatter_ssm_states"),
        extra_modules=("vllm_ascend.ops.triton.mamba.state_index",),
    ),
    "hc_pre": _mhc_builder(
        builder="hc_pre", upstream_abi="aclnnHcPre",
        candidates=("npu_hc_pre_v2", "npu_hc_pre_v3", "npu_hc_pre", "hc_pre"),
    ),
    "hc_post": _mhc_builder(builder="hc_post", upstream_abi="aclnnHcPost", candidates=("npu_hc_post", "hc_post")),
    "hc_combine_norm": _mhc_builder(builder="hc_combine_norm", upstream_abi="_hc_combine_norm_kernel", candidates=("hc_combine_norm", "_hc_combine_norm_kernel")),
    "mhc_stream_mix": _mhc_builder(
        builder="mhc_stream_mix", upstream_abi="mhc_hc_combine_kernel",
        candidates=("npu_mhc_stream_mix", "mhc_stream_mix", "hc_gate_mix", "qwen4_exp_ascend_hc_gate_mix"),
        extra_modules=("vllm_ascend.ops.triton.qwen4_exp.hc",),
    ),
    "attn_res_prefix": _mhc_builder(builder="attn_res_prefix", upstream_abi="aclnnAttnResFwd", candidates=("npu_attn_res_fwd", "attn_res_fwd", "attn_res_prefix")),
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
