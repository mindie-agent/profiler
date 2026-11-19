"""Attention, absorbed MLA, sparse indexer, KV-cache and RoPE bench builders.

[Role]
  Implement the 21 canonical attention, MLA prolog/compressor, sparse indexer,
  paged KV-cache and fused RoPE builders with cold-ring KV/query rotation and
  fail-fast ``BenchUnmodeledOperatorError`` enforcement.

[Invariants]
  * ``absorbed_mla`` allocates a single ``1152 B/tok`` (``512 + 64``) BF16
    ``c_kv`` backing tensor per slot—never a fake 2-matmul composite.
  * Every builder dispatches to its real CANN / ``torch_npu`` /
    ``torch.ops._C_ascend`` kernel or raises ``BenchUnmodeledOperatorError``.

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
    INT8,
    INT32,
    INT64,
    OP_CFG,
    cast_weight_nz,
    charge_alloc_bytes,
    cold_ring_slot_count,
    device_of,
    device_values,
    dim_int,
    dims_2d,
    element_bytes,
    ones,
    randn,
    require_kernel,
    resolve_case_dtype,
    resolve_op,
    shape_of,
    slice_ring_tensors,
    torch_dtype,
    wrap_ring_step,
    zeros,
)


def _attention_dims(shape: Mapping[str, Any]) -> tuple[int, int, int, int]:
    tokens = dim_int(shape, "tokens")
    heads = dim_int(shape, "heads")
    kv_heads = dim_int(shape, "kv_heads", heads)
    head_dim = dim_int(shape, "head_dim", int(OP_CFG["attention_head_dim"]))
    return tokens, heads, kv_heads, head_dim


def _resolved_op_name(
    torch: Any, op: Any, candidates: Sequence[str], context: Mapping[str, Any]
) -> str:
    """Resolve which candidate alias produced ``op`` (never ``inspect.signature``)."""
    declared = str(getattr(op, "__name__", "") or "")
    if declared.startswith("npu_") or declared in candidates:
        return declared
    for name in candidates:
        if resolve_op(torch, name, context=context, allow_torch_attr=False) is op:
            return name
    return declared


def _build_attention(
    torch: Any,
    case: Mapping[str, Any],
    context: Mapping[str, Any],
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
    )
    resolved = _resolved_op_name(torch, op, candidates, context)
    shape, device = shape_of(case), device_of(context)
    tokens, heads, kv_heads, head_dim = _attention_dims(shape)
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    block_size = max(
        1, dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"]))
    )
    num_blocks = max(1, -(-seq_len // block_size))
    if builder == "incre_flash_attention":
        slots = cold_ring_slot_count(
            case, context, (tokens * heads + 2 * tokens * seq_len * kv_heads) * head_dim * eb
        )
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, 1, heads * head_dim), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        k_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, seq_len, kv_heads * head_dim),
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        v_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, seq_len, kv_heads * head_dim),
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        scale = 1.0 / math.sqrt(head_dim)
        fia_fb = "fused_infer_attention" in resolved
        ifa_kw = (
            {"scale": scale, "actual_seq_lengths": [1] * tokens, "actual_seq_lengths_kv": [seq_len] * tokens}
            if fia_fb else {"scale_value": scale, "actual_seq_lengths": [seq_len] * tokens}
        )
        return wrap_ring_step(
            slots,
            lambda s: op(
                q_ring[s], k_ring[s], v_ring[s], num_heads=heads,
                num_key_value_heads=kv_heads, input_layout="BSH", **ifa_kw,
            ),
            retain_outputs=True,
        )
    paged = builder == "fused_infer_attention" and (
        bool(case.get("paged")) or bool(shape.get("block_table"))
    )
    if not paged and seq_len >= int(OP_CFG["long_context_threshold"]):
        slot_cap = int(OP_CFG["long_prefill_slot_cap_bytes"])
        if (tokens * heads + 2 * seq_len * kv_heads) * head_dim * eb > slot_cap:
            heads = max(kv_heads, min(heads, int(OP_CFG["long_prefill_max_heads"])))
            tokens = min(tokens, int(OP_CFG["long_prefill_query_cap"]))
    sequences = max(1, min(tokens, dim_int(shape, "sequences", 1))) if paged else 1
    total_blocks = sequences * num_blocks
    if paged:
        kv_dims = (total_blocks, kv_heads, block_size, head_dim)
        footprint = (
            tokens * heads + 2 * total_blocks * block_size * kv_heads
        ) * head_dim * eb
    else:
        kv_dims = (seq_len, kv_heads, head_dim)
        footprint = (tokens * heads + 2 * seq_len * kv_heads) * head_dim * eb
    slots = cold_ring_slot_count(case, context, footprint)
    q_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    k_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=kv_dims, dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    v_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=kv_dims, dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    if builder == "fusion_attention":
        fa_scale = 1.0 / math.sqrt(head_dim)
        return wrap_ring_step(
            slots,
            lambda s: op(
                q_ring[s], k_ring[s], v_ring[s], heads, input_layout="TND",
                scale=fa_scale, actual_seq_qlen=[tokens], actual_seq_kvlen=[seq_len],
            ),
            retain_outputs=True,
        )
    if builder == "fused_infer_attention" and paged:
        base_q, rem_q = divmod(tokens, sequences)
        q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(sequences)]
        actual_seq_q = [sum(q_lens[: idx + 1]) for idx in range(sequences)]
        block_table = device_values(
            torch,
            [list(range(idx * num_blocks, (idx + 1) * num_blocks)) for idx in range(sequences)],
            dtype=getattr(torch, INT32, None),
            device=device,
        )
        return wrap_ring_step(
            slots,
            lambda s: op(
                q_ring[s], k_ring[s], v_ring[s], num_heads=heads,
                num_key_value_heads=kv_heads, input_layout="TND",
                block_table=block_table, block_size=block_size,
                actual_seq_lengths=actual_seq_q,
                actual_seq_lengths_kv=[seq_len] * sequences,
            ),
            retain_outputs=True,
        )
    return wrap_ring_step(
        slots,
        lambda s: op(
            q_ring[s], k_ring[s], v_ring[s], num_heads=heads, num_key_value_heads=kv_heads,
            input_layout="TND", actual_seq_lengths=[tokens],
            actual_seq_lengths_kv=[seq_len],
        ),
        retain_outputs=True,
    )


def build_absorbed_mla(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context,
        ("npu_fused_infer_attention_score", "npu_mla_paged_attention", "absorbed_mla"),
        builder="absorbed_mla", upstream_abi="aclnnFusedInferAttentionScoreV4",
    )
    shape, device = shape_of(case), device_of(context)
    meta = (context or {}).get("_case_meta") or {}
    phase = str(case.get("phase") or meta.get("phase") or "").strip().lower()
    parent_batch = case.get("batch") if case.get("batch") is not None else meta.get("batch")
    tokens = dim_int(shape, "tokens")
    heads = dim_int(shape, "heads")
    seq_len = max(1, dim_int(shape, "seq_len", tokens))
    latent = dim_int(shape, "kv_lora_rank", int(OP_CFG["mla_latent_dim"]))
    rope = dim_int(shape, "qk_rope_head_dim", int(OP_CFG["mla_rope_dim"]))
    block_size = max(1, dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"])))
    default_seqs = (
        int(parent_batch) if isinstance(parent_batch, int) and not isinstance(parent_batch, bool) and parent_batch > 0
        else (1 if phase == "prefill" else tokens)
    )
    sequences = max(1, min(tokens, dim_int(shape, "sequences", default_seqs)))
    pages_per_seq = max(1, (seq_len + block_size - 1) // block_size)
    total_blocks = sequences * pages_per_seq
    dtype = torch_dtype(torch, BFLOAT16)
    eb = element_bytes(BFLOAT16)
    slots = cold_ring_slot_count(
        case, context, (tokens * heads + total_blocks * block_size) * (latent + rope) * eb
    )
    q_nope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, latent), dtype=dtype,
        dtype_name=BFLOAT16, device=device,
    )
    q_rope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, rope), dtype=dtype,
        dtype_name=BFLOAT16, device=device,
    )
    nope_elems = total_blocks * block_size * latent
    rope_elems = total_blocks * block_size * rope
    c_kv_flat = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(nope_elems + rope_elems,), dtype=dtype,
        dtype_name=BFLOAT16, device=device,
    )
    kv_nope = [
        buf.narrow(0, 0, nope_elems).view(total_blocks, block_size, latent)
        if callable(getattr(buf, "narrow", None)) and callable(getattr(buf, "view", None))
        else buf
        for buf in c_kv_flat
    ]
    k_rope = [
        buf.narrow(0, nope_elems, rope_elems).view(total_blocks, block_size, rope)
        if callable(getattr(buf, "narrow", None)) and callable(getattr(buf, "view", None))
        else buf
        for buf in c_kv_flat
    ]
    block_table = device_values(
        torch,
        [list(range(idx * pages_per_seq, (idx + 1) * pages_per_seq)) for idx in range(sequences)],
        dtype=getattr(torch, INT32, None),
        device=device,
    )
    base_q, rem_q = divmod(tokens, sequences)
    q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(sequences)]
    actual_seq_q = [sum(q_lens[: idx + 1]) for idx in range(sequences)]
    actual_seq_kv = [max(q_lens[idx], seq_len) for idx in range(sequences)]
    return wrap_ring_step(
        slots,
        lambda s: op(
            q_nope_ring[s], kv_nope[s], kv_nope[s],
            query_rope=q_rope_ring[s], key_rope=k_rope[s],
            num_heads=heads, num_key_value_heads=1, input_layout="TND",
            block_table=block_table, block_size=block_size,
            actual_seq_lengths=actual_seq_q, actual_seq_lengths_kv=actual_seq_kv,
        ),
        retain_outputs=True,
    )


def build_sparse_attention(
    *, builder: str, upstream_abi: str, candidates: Sequence[str]
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens, heads, kv_heads, head_dim = _attention_dims(shape)
        seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
        dtype = resolve_case_dtype(torch, case)
        kv_name = INT8 if builder == "block_sparse_attention_c8" else str(case.get("dtype", "bf16"))
        kv_dtype = getattr(torch, INT8, dtype) if kv_name == INT8 else dtype
        rope_dim = int(shape.get("qk_rope_head_dim") or (OP_CFG["mla_rope_dim"] if head_dim == int(OP_CFG["mla_latent_dim"]) else 0))
        slots = cold_ring_slot_count(
            case, context, (tokens * heads + seq_len * kv_heads) * (head_dim + rope_dim) * element_bytes(kv_name)
        )
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        kv_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(seq_len, kv_heads, head_dim), dtype=kv_dtype,
            dtype_name=kv_name, device=device,
        )
        topk = int(OP_CFG["topk_gating_default"])
        int32_dt = getattr(torch, INT32, None)
        scale = 1.0 / math.sqrt(head_dim + rope_dim)
        if builder == "sparse_flash_attention":
            indices = zeros(torch, tokens, kv_heads, topk, dtype=int32_dt, device=device)
            seq_q = device_values(torch, [tokens], dtype=int32_dt, device=device)
            seq_kv = device_values(torch, [seq_len], dtype=int32_dt, device=device)
            rope_kw = (
                {"query_rope": ones(torch, tokens, heads, rope_dim, dtype=dtype, device=device),
                 "key_rope": ones(torch, seq_len, kv_heads, rope_dim, dtype=dtype, device=device)}
                if rope_dim > 0 else {}
            )
            return wrap_ring_step(
                slots,
                lambda s: op(
                    q_ring[s], kv_ring[s], kv_ring[s], indices, scale,
                    layout_query="TND", layout_kv="TND",
                    actual_seq_lengths_query=seq_q, actual_seq_lengths_kv=seq_kv, **rope_kw,
                ),
                retain_outputs=True,
            )
        indices = zeros(torch, tokens, topk, dtype=int32_dt, device=device)
        return wrap_ring_step(
            slots,
            lambda s: op(q_ring[s], kv_ring[s], kv_ring[s], indices, scale_value=scale),
            retain_outputs=True,
        )

    return build


def _mla_prolog_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str]
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens = dim_int(shape, "tokens")
        width = dim_int(shape, "width", int(OP_CFG["mla_latent_dim"]))
        heads = dim_int(shape, "heads", 1)
        kv_heads = dim_int(shape, "kv_heads", 1)
        latent = int(OP_CFG["mla_latent_dim"])
        rope = int(OP_CFG["mla_rope_dim"])
        qk_nope = dim_int(shape, "qk_nope_head_dim", int(OP_CFG["attention_head_dim"]))
        head_dim = dim_int(shape, "head_dim", qk_nope + rope)
        q_lora = dim_int(shape, "q_lora_rank", latent)
        kv_lora = dim_int(shape, "kv_lora_rank", latent)
        block_size = max(
            1, dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"]))
        )
        num_blocks = max(1, -(-tokens // block_size))
        dtype = resolve_case_dtype(torch, case)
        weight_dtype = getattr(torch, INT8, dtype)
        eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
        token_x = randn(torch, tokens, width, dtype=dtype, device=device)
        weight_dq = cast_weight_nz(
            torch, randn(torch, width, q_lora, dtype=weight_dtype, device=device), context
        )
        weight_uq_qr = cast_weight_nz(
            torch, randn(torch, q_lora, heads * head_dim, dtype=weight_dtype, device=device),
            context,
        )
        weight_uk = cast_weight_nz(
            torch, randn(torch, heads, qk_nope, kv_lora, dtype=weight_dtype, device=device),
            context,
        )
        weight_dkv_kr = cast_weight_nz(
            torch, randn(torch, width, kv_lora + rope, dtype=weight_dtype, device=device),
            context,
        )
        rmsnorm_gamma_cq = ones(torch, q_lora, dtype=dtype, device=device)
        rmsnorm_gamma_ckv = ones(torch, kv_lora, dtype=dtype, device=device)
        rope_sin = ones(torch, tokens, rope, dtype=dtype, device=device)
        rope_cos = ones(torch, tokens, rope, dtype=dtype, device=device)
        kv_cache = zeros(
            torch, num_blocks, block_size, kv_heads, kv_lora, dtype=dtype, device=device
        )
        kr_cache = zeros(
            torch, num_blocks, block_size, kv_heads, rope, dtype=dtype, device=device
        )
        cache_index = zeros(torch, tokens, dtype=getattr(torch, INT64, None), device=device)
        return wrap_ring_step(
            1,
            lambda _s: op(
                token_x=token_x, weight_dq=weight_dq, weight_uq_qr=weight_uq_qr,
                weight_uk=weight_uk, weight_dkv_kr=weight_dkv_kr,
                rmsnorm_gamma_cq=rmsnorm_gamma_cq, rmsnorm_gamma_ckv=rmsnorm_gamma_ckv,
                rope_sin=rope_sin, rope_cos=rope_cos, cache_index=cache_index,
                kv_cache=kv_cache, kr_cache=kr_cache,
                rmsnorm_epsilon_cq=eps, rmsnorm_epsilon_ckv=eps, cache_mode="PA_BSND",
            ),
            retain_outputs=True,
        )

    return build


def _indexer_or_cache_builder(
    *, builder: str, upstream_abi: str, candidates: Sequence[str], with_indices: bool = False
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        op = require_kernel(
            torch, case, context, candidates, builder=builder, upstream_abi=upstream_abi
        )
        shape, device = shape_of(case), device_of(context)
        tokens, width = dims_2d(case)
        seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
        dtype = resolve_case_dtype(torch, case)
        eb = element_bytes(case.get("dtype", "bf16"))
        slots = cold_ring_slot_count(case, context, (tokens + seq_len) * width * eb)
        src_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        cache_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(seq_len, width), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        if with_indices:
            idx = zeros(torch, tokens, dtype=getattr(torch, INT32, None), device=device)
            return wrap_ring_step(slots, lambda s: op(src_ring[s], cache_ring[s], idx))
        return wrap_ring_step(
            slots, lambda s: op(src_ring[s], cache_ring[s]), retain_outputs=True
        )

    return build


def build_dcp_lse_attention_merge(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        (
            "npu_ring_attention_update",
            "npu_dcp_lse_attention_merge",
            "npu_lse_attention_merge",
            "dcp_lse_attention_merge",
        ),
        builder="dcp_lse_attention_merge",
        upstream_abi="aclnnRingAttentionUpdate",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, heads, kv_heads, _default_hd = _attention_dims(shape)
    head_dim = dim_int(shape, "head_dim", dim_int(shape, "width", _default_hd))
    if tokens >= int(OP_CFG["long_context_threshold"]):
        if tokens * heads * head_dim * element_bytes(case.get("dtype", "bf16")) * 2 > int(OP_CFG["long_prefill_slot_cap_bytes"]):
            heads = max(kv_heads, min(heads, int(OP_CFG["long_prefill_max_heads"])))
            tokens = min(tokens, int(OP_CFG["long_prefill_query_cap"]))
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * heads * head_dim * eb * 2)
    out_a = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    out_b = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    stat_width = int(OP_CFG["ring_attn_stat_width"])
    charge_alloc_bytes(
        context, tokens * heads * stat_width * int(OP_CFG["float32_element_bytes"]) * 2 * 2
    )
    max_a = ones(torch, tokens, heads, stat_width, dtype=fp32, device=device)
    sum_a = ones(torch, tokens, heads, stat_width, dtype=fp32, device=device)
    max_b = ones(torch, tokens, heads, stat_width, dtype=fp32, device=device)
    sum_b = ones(torch, tokens, heads, stat_width, dtype=fp32, device=device)
    if callable(getattr(max_b, "fill_", None)):
        max_b.fill_(2)
    if callable(getattr(sum_b, "fill_", None)):
        sum_b.fill_(2)
    actual_seq_qlen = device_values(
        torch, [0, tokens], dtype=getattr(torch, INT64, None), device=device
    )
    return wrap_ring_step(
        slots,
        lambda s: op(
            out_a[s], max_a, sum_a, out_b[s], max_b, sum_b,
            actual_seq_qlen=actual_seq_qlen,
            input_layout="TND",
            input_softmax_layout="TND",
        ),
        retain_outputs=True,
    )


def build_rotary_embedding(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_rotary_mul", "npu_apply_rotary_pos_emb", "rotary_embedding"),
        builder="rotary_embedding",
        upstream_abi="aclnnApplyRotaryPosEmbV2",
    )
    shape, device = shape_of(case), device_of(context)
    tokens = dim_int(shape, "tokens")
    heads = dim_int(shape, "heads", 1)
    head_dim = dim_int(shape, "head_dim", dim_int(shape, "width", int(OP_CFG["mla_rope_dim"])))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * heads * head_dim * eb * 2)
    q_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(1, tokens, heads, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    cos = ones(torch, 1, tokens, 1, head_dim, dtype=dtype, device=device)
    sin = zeros(torch, 1, tokens, 1, head_dim, dtype=dtype, device=device)
    return wrap_ring_step(slots, lambda s: op(q_ring[s], cos, sin), retain_outputs=True)


def build_split_qkv_rmsnorm_rope(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        (
            "split_qkv_rmsnorm_rope",
            "npu_split_qkv_rmsnorm_rope",
            "split_qkv_rmsnorm_mrope_kernel",
            "split_qkv_rmsnorm_rope_kernel",
        ),
        builder="split_qkv_rmsnorm_rope",
        upstream_abi="split_qkv_rmsnorm_mrope_kernel",
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    head_dim = int(OP_CFG["attention_head_dim"])
    dtype = resolve_case_dtype(torch, case)
    qkv = randn(torch, tokens, max(width, head_dim * 2), dtype=dtype, device=device)
    q_w = ones(torch, head_dim, dtype=dtype, device=device)
    k_w = ones(torch, head_dim, dtype=dtype, device=device)
    cos = ones(torch, tokens, head_dim, dtype=dtype, device=device)
    sin = zeros(torch, tokens, head_dim, dtype=dtype, device=device)
    return wrap_ring_step(1, lambda _s: op(qkv, q_w, k_w, cos, sin), retain_outputs=True)


def build_indexer_topk(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        ("npu_topk_v2", "indexer_topk", "topk"),
        builder="indexer_topk",
        upstream_abi="aclnnTopkV2",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    top_k = max(1, min(width, dim_int(shape, "top_k", int(OP_CFG["topk_gating_default"]))))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(case, context, tokens * width * eb)
    scores = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    return wrap_ring_step(slots, lambda s: op(scores[s], top_k), retain_outputs=True)


def build_lightning_indexer(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch,
        case,
        context,
        (
            "npu_lightning_indexer",
            "npu_quant_lightning_indexer_v3",
            "npu_quant_lightning_indexer",
            "lightning_indexer",
        ),
        builder="lightning_indexer",
        upstream_abi="aclnnQuantLightningIndexerV2",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    heads = max(1, dim_int(shape, "heads", 1))
    head_dim = max(1, dim_int(shape, "head_dim", width))
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    eb = element_bytes(case.get("dtype", "bf16"))
    slots = cold_ring_slot_count(
        case, context, (tokens * heads + seq_len) * head_dim * eb
    )
    src_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    cache_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(seq_len, 1, head_dim), dtype=dtype,
        dtype_name=str(case.get("dtype", "bf16")), device=device,
    )
    weights = ones(torch, tokens, heads, dtype=fp32, device=device)
    block_topk = max(1, min(seq_len, int(OP_CFG["topk_gating_default"])))
    candidates = (
        "npu_lightning_indexer",
        "npu_quant_lightning_indexer_v3",
        "npu_quant_lightning_indexer",
        "lightning_indexer",
    )
    if _resolved_op_name(torch, op, candidates, context).startswith("npu_"):
        int32_dt = getattr(torch, INT32, None)
        seq_q = device_values(torch, [tokens], dtype=int32_dt, device=device)
        seq_k = device_values(torch, [seq_len], dtype=int32_dt, device=device)
        return wrap_ring_step(
            slots,
            lambda s: op(
                src_ring[s], cache_ring[s], weights,
                actual_seq_lengths_query=seq_q, actual_seq_lengths_key=seq_k,
                layout_query="TND", layout_key="TND", sparse_count=block_topk,
            ),
            retain_outputs=True,
        )
    return wrap_ring_step(
        slots,
        lambda s: op(src_ring[s], cache_ring[s], weights, block_topk),
        retain_outputs=True,
    )


ATTENTION_MLA_BUILDERS: dict[str, Callable[..., Callable[[], Any]]] = {
    "fusion_attention": lambda torch, case, context: _build_attention(
        torch, case, context, builder="fusion_attention",
        upstream_abi="aclnnFlashAttentionVarLenScoreV2",
        candidates=("npu_fusion_attention", "npu_prompt_flash_attention"),
    ),
    "fused_infer_attention": lambda torch, case, context: _build_attention(
        torch, case, context, builder="fused_infer_attention",
        upstream_abi="aclnnFusedInferAttentionScoreV3",
        candidates=("npu_fused_infer_attention_score",),
    ),
    "incre_flash_attention": lambda torch, case, context: _build_attention(
        torch, case, context, builder="incre_flash_attention",
        upstream_abi="aclnnFusedInferAttentionScoreV3",
        candidates=("npu_incre_flash_attention", "npu_fused_infer_attention_score"),
    ),
    "absorbed_mla": build_absorbed_mla,
    "mla_prolog_v2": _mla_prolog_builder(
        builder="mla_prolog_v2", upstream_abi="aclnnMlaPrologV2WeightNz",
        candidates=("npu_mla_prolog_v2", "mla_prolog_v2"),
    ),
    "mla_prolog_v3": _mla_prolog_builder(
        builder="mla_prolog_v3", upstream_abi="aclnnMlaPrologV3WeightNz",
        candidates=("npu_mla_prolog_v3", "mla_prolog_v3"),
    ),
    "sparse_flash_attention": build_sparse_attention(
        builder="sparse_flash_attention", upstream_abi="aclnnSparseFlashAttention",
        candidates=("npu_sparse_flash_attention", "sparse_flash_attention"),
    ),
    "mixed_quant_sparse_mla": build_sparse_attention(
        builder="mixed_quant_sparse_mla", upstream_abi="aclnnMixedQuantSparseFlashMla",
        candidates=("npu_sparse_flash_mla", "npu_mixed_quant_sparse_flash_mla", "mixed_quant_sparse_mla"),
    ),
    "mla_kv_compressor": _indexer_or_cache_builder(
        builder="mla_kv_compressor", upstream_abi="aclnnCompressor",
        candidates=("compressor_from_projected", "npu_mla_kv_compressor", "npu_compressor", "mla_kv_compressor"),
    ),
    "lightning_indexer": build_lightning_indexer,
    "pool_key_indexer": _indexer_or_cache_builder(
        builder="pool_key_indexer", upstream_abi="aclnnPoolKeyIndexer",
        candidates=("npu_pool_key_indexer", "pool_key_indexer"),
    ),
    "key_pool": _indexer_or_cache_builder(
        builder="key_pool", upstream_abi="aclnnKeyPool",
        candidates=("npu_key_pool", "key_pool"),
    ),
    "indexer_quant_cache": _indexer_or_cache_builder(
        builder="indexer_quant_cache", upstream_abi="aclnnIndexerQuantCache",
        candidates=("npu_indexer_quant_cache", "indexer_quant_cache"), with_indices=True,
    ),
    "kv_compress_epilog": _indexer_or_cache_builder(
        builder="kv_compress_epilog", upstream_abi="aclnnKvCompressEpilog",
        candidates=("npu_kv_compress_epilog", "kv_compress_epilog"), with_indices=True,
    ),
    "block_sparse_attention_c8": build_sparse_attention(
        builder="block_sparse_attention_c8", upstream_abi="aclnnGenericBlockSparseAttention",
        candidates=("npu_generic_block_sparse_attention", "npu_block_sparse_attention", "block_sparse_attention_c8"),
    ),
    "dcp_lse_attention_merge": build_dcp_lse_attention_merge,
    "scatter_pa_kv_cache": _indexer_or_cache_builder(
        builder="scatter_pa_kv_cache", upstream_abi="aclnnScatterPaKvCache",
        candidates=("_npu_paged_attention", "npu_scatter_pa_kv_cache", "npu_reshape_and_cache", "scatter_pa_kv_cache"),
        with_indices=True,
    ),
    "scatter_index_cache": _indexer_or_cache_builder(
        builder="scatter_index_cache", upstream_abi="aclnnScatterNdUpdate",
        candidates=("npu_scatter_nd_update", "scatter_nd_update", "scatter_index_cache"),
        with_indices=True,
    ),
    "rotary_embedding": build_rotary_embedding,
    "split_qkv_rmsnorm_rope": build_split_qkv_rmsnorm_rope,
    "indexer_topk": build_indexer_topk,
}

__all__ = ["ATTENTION_MLA_BUILDERS"]
