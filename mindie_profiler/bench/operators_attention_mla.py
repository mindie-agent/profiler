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
    FA_CAUSAL_MASK_BYTES,
    FA_CAUSAL_MASK_SHAPE,
    FA_CAUSAL_SPARSE_MODE,
    FA_RIGHT_DOWN_CAUSAL_SPARSE_MODE,
    FLOAT32,
    INT8,
    INT32,
    INT64,
    OP_CFG,
    UINT8,
    cast_weight_nz,
    causal_attention_pairs,
    charge_alloc_bytes,
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
    right_aligned_causal_pairs,
    rotary_query_input,
    shape_of,
    slice_ring_tensors,
    torch_dtype,
    upstream_2d_input,
    wrap_ring_step,
    zeros,
)
from .operators_kv_cache import build_kv_compress_epilog, build_scatter_pa_kv_cache


def _attention_dims(shape: Mapping[str, Any]) -> tuple[int, int, int, int]:
    tokens = dim_int(shape, "tokens")
    heads = dim_int(shape, "heads")
    kv_heads = dim_int(shape, "kv_heads", heads)
    head_dim = dim_int(shape, "head_dim", int(OP_CFG["attention_head_dim"]))
    return tokens, heads, kv_heads, head_dim


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
    resolved = resolved_kernel_name(torch, op, candidates, context)
    shape, device = shape_of(case), device_of(context)
    tokens, heads, kv_heads, head_dim = _attention_dims(shape)
    seq_len = max(tokens, dim_int(shape, "seq_len", dim_int(shape, "kv_len", tokens)))
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(case.get("dtype", "bf16"))
    block_size = max(
        1, dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"]))
    )
    num_blocks = max(1, -(-seq_len // block_size))
    extra_actual: dict[str, Any] = {}
    if shape.get("kv_len") is not None:
        extra_actual["kv_len"] = seq_len
    if shape.get("is_prefill") is not None:
        extra_actual["is_prefill"] = int(shape["is_prefill"])
    record_actual_shape(
        context, tokens=tokens, heads=heads, kv_heads=kv_heads,
        head_dim=head_dim, seq_len=seq_len,
        layout="BSH" if builder == "incre_flash_attention" else "TND",
        **extra_actual,
    )
    if builder == "incre_flash_attention":
        has_seq = shape.get("sequences") is not None
        batch = max(1, min(tokens, dim_int(shape, "sequences", tokens))) if has_seq else tokens
        base_q, rem_q = divmod(tokens, batch) if has_seq else (1, 0)
        q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(batch)]
        max_q = max(q_lens)
        if has_seq and shape.get("kv_len") is not None:
            base_kv, rem_kv = divmod(seq_len, batch)
            kv_lens = [
                max(q_lens[idx], base_kv + (1 if idx < rem_kv else 0)) for idx in range(batch)
            ]
        else:
            kv_lens = [max(q_lens[idx], seq_len) for idx in range(batch)]
        max_kv = max(kv_lens)
        scale = 1.0 / math.sqrt(head_dim)
        if max_q > 1 and "fused_infer_attention" not in resolved:
            fia_op = resolve_op(
                torch, "npu_fused_infer_attention_score", context=context, allow_torch_attr=False
            )
            if callable(fia_op):
                op, resolved = fia_op, "npu_fused_infer_attention_score"
            else:
                raise_unmodeled(
                    case, builder=builder, upstream_abi=upstream_abi,
                    reason="incre_flash_attention_requires_fia_for_multi_query",
                    candidates=("npu_fused_infer_attention_score",), context=context,
                )
        record_actual_shape(
            context, sequences=batch, q_len=max_q,
            actual_seq_lengths=q_lens, actual_seq_lengths_kv=kv_lens,
        )
        fia_fb = "fused_infer_attention" in resolved
        ifa_causal = bool(case.get("causal")) and fia_fb and max_q > 1
        if ifa_causal:
            charge_alloc_bytes(context, FA_CAUSAL_MASK_BYTES, reason="compressed causal mask")
        slots = cold_ring_slot_count(
            case, context, (batch * max_q * heads + 2 * batch * max_kv * kv_heads) * head_dim * eb
        )
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(batch, max_q, heads * head_dim), dtype=dtype,
            dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        k_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(batch, max_kv, kv_heads * head_dim),
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        v_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(batch, max_kv, kv_heads * head_dim),
            dtype=dtype, dtype_name=str(case.get("dtype", "bf16")), device=device,
        )
        ifa_kw: dict[str, Any] = (
            {
                "scale": scale,
                "actual_seq_lengths": q_lens,
                "actual_seq_lengths_kv": kv_lens,
            }
            if fia_fb else {"scale_value": scale, "actual_seq_lengths": kv_lens}
        )
        if ifa_causal:
            # In CANN right-aligned causal attention (sparse_mode=3), nonzero entries mask future keys.
            mask = ones(torch, *FA_CAUSAL_MASK_SHAPE, dtype=torch_dtype(torch, UINT8), device="cpu")
            mask = mask.triu_(diagonal=1).to(device)
            ifa_kw.update(atten_mask=mask, sparse_mode=FA_RIGHT_DOWN_CAUSAL_SPARSE_MODE)
            record_actual_shape(
                context,
                atten_mask_shape=list(mask.shape),
                atten_mask_dtype=UINT8,
                atten_mask_bytes=FA_CAUSAL_MASK_BYTES,
                sparse_mode=FA_RIGHT_DOWN_CAUSAL_SPARSE_MODE,
                query_key_pairs=sum(
                    right_aligned_causal_pairs(ql, kvl) for ql, kvl in zip(q_lens, kv_lens)
                ),
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
    sequences = max(1, min(tokens, dim_int(shape, "sequences", 1)))
    base_q, rem_q = divmod(tokens, sequences)
    q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(sequences)]
    actual_seq_q = [sum(q_lens[: idx + 1]) for idx in range(sequences)]
    base_kv, rem_kv = divmod(seq_len, sequences)
    kv_lens = [base_kv + (1 if idx < rem_kv else 0) for idx in range(sequences)]
    actual_seq_kv = [sum(kv_lens[: idx + 1]) for idx in range(sequences)]
    seq_actual: dict[str, Any] = {}
    if shape.get("sequences") is None or int(shape["sequences"]) == sequences:
        seq_actual["sequences"] = sequences
    if shape.get("q_len") is None or int(shape["q_len"]) == max(q_lens):
        seq_actual["q_len"] = max(q_lens)
    record_actual_shape(context, actual_sequences=sequences, actual_q_len=max(q_lens), **seq_actual)
    total_blocks = sequences * num_blocks
    if paged:
        record_actual_shape(context, block_size=block_size, block_table=[sequences, num_blocks])
        kv_dims = (total_blocks, kv_heads, block_size, head_dim)
        footprint = (
            tokens * heads + 2 * total_blocks * block_size * kv_heads
        ) * head_dim * eb
    else:
        kv_dims = (seq_len, kv_heads, head_dim)
        footprint = (tokens * heads + 2 * seq_len * kv_heads) * head_dim * eb
    causal = builder == "fusion_attention" and bool(case.get("causal"))
    if causal:
        charge_alloc_bytes(context, FA_CAUSAL_MASK_BYTES, reason="compressed causal mask")
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
        causal_kwargs: dict[str, Any] = {}
        if causal:
            # In CANN's lower-triangular attention, nonzero entries mask future keys.
            mask = ones(torch, *FA_CAUSAL_MASK_SHAPE, dtype=torch_dtype(torch, UINT8), device="cpu")
            mask = mask.triu_(diagonal=1).to(device)
            causal_kwargs.update(atten_mask=mask, sparse_mode=FA_CAUSAL_SPARSE_MODE)
            record_actual_shape(
                context, atten_mask_shape=list(mask.shape), atten_mask_dtype=UINT8,
                atten_mask_bytes=FA_CAUSAL_MASK_BYTES, sparse_mode=FA_CAUSAL_SPARSE_MODE,
                query_key_pairs=sum(
                    causal_attention_pairs(ql, kvl) for ql, kvl in zip(q_lens, kv_lens)
                ),
            )

        def _fa_step(s: int) -> Any:
            res = op(
                q_ring[s], k_ring[s], v_ring[s], heads, input_layout="TND",
                scale=fa_scale, keep_prob=1.0, gen_mask_parallel=False,
                actual_seq_qlen=actual_seq_q, actual_seq_kvlen=actual_seq_kv, **causal_kwargs,
            )
            return res[0] if isinstance(res, (tuple, list)) and res else res

        return wrap_ring_step(slots, _fa_step, retain_outputs=True)
    if builder == "fused_infer_attention" and paged:
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
            input_layout="TND", actual_seq_lengths=actual_seq_q,
            actual_seq_lengths_kv=actual_seq_kv,
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
    layout = shape.get("input_layout") or shape.get("query_layout") or case.get("layout") or "TND"
    meta = (context or {}).get("_case_meta") or {}
    phase = str(case.get("phase") or meta.get("phase") or "").strip().lower()
    parent_batch = case.get("batch") if case.get("batch") is not None else meta.get("batch")
    tokens = dim_int(shape, "tokens")
    heads = dim_int(shape, "heads")
    seq_len = max(1, dim_int(shape, "seq_len", tokens))
    latent = dim_int(shape, "kv_lora_rank", dim_int(shape, "latent", int(OP_CFG["mla_latent_dim"])))
    rope = dim_int(shape, "qk_rope_head_dim", dim_int(shape, "rope", int(OP_CFG["mla_rope_dim"])))
    block_size = max(1, dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"])))
    default_seqs = (
        int(parent_batch) if isinstance(parent_batch, int) and not isinstance(parent_batch, bool) and parent_batch > 0
        else (1 if phase == "prefill" else tokens)
    )
    sequences = max(1, min(tokens, dim_int(shape, "sequences", default_seqs)))
    base_q, rem_q = divmod(tokens, sequences)
    q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(sequences)]
    max_q = max(q_lens)
    q_dims = (sequences, heads, max_q) if layout == "BNSD" else (tokens, heads)
    query_elements = sequences * max_q if layout == "BNSD" else tokens
    pages_per_seq = max(1, (seq_len + block_size - 1) // block_size)
    total_blocks = sequences * pages_per_seq
    dtype = torch_dtype(torch, BFLOAT16)
    eb = element_bytes(BFLOAT16)
    slots = cold_ring_slot_count(
        case, context, (query_elements * heads + total_blocks * block_size) * (latent + rope) * eb
    )
    q_nope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(*q_dims, latent), dtype=dtype,
        dtype_name=BFLOAT16, device=device,
    )
    q_rope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(*q_dims, rope), dtype=dtype,
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
    actual_seq_q = q_lens if layout == "BNSD" else [sum(q_lens[: idx + 1]) for idx in range(sequences)]
    actual_seq_kv = [max(q_lens[idx], seq_len) for idx in range(sequences)]
    record_actual_shape(
        context, tokens=tokens, sequences=sequences, q_len=max_q,
        seq_len=max(actual_seq_kv), heads=heads, kv_heads=1, head_dim=latent,
        block_size=block_size, block_table=[sequences, pages_per_seq], latent=latent, rope=rope,
        kv_bytes_per_token=(latent + rope) * eb, layout=layout, input_layout=layout, query_layout=layout, single_backing=True,
    )
    return wrap_ring_step(
        slots,
        lambda s: op(
            q_nope_ring[s], kv_nope[s], kv_nope[s],
            query_rope=q_rope_ring[s], key_rope=k_rope[s],
            num_heads=heads, num_key_value_heads=1, input_layout=layout,
            block_table=block_table, block_size=block_size,
            actual_seq_lengths=actual_seq_q, actual_seq_lengths_kv=actual_seq_kv,
        ),
        retain_outputs=True,
    )


def _dsa_sparse_indices(
    torch: Any,
    *,
    tokens: int,
    kv_heads: int,
    seq_len: int,
    dsa_topk: int,
    int32_dt: Any,
    device: str,
) -> Any:
    """Build deterministic strided `[0..seq_len-1]` DSA indices padded with `-1`."""
    valid_k = min(seq_len, dsa_topk)
    step = max(1, seq_len // max(1, valid_k))
    row = [(idx * step) % seq_len for idx in range(valid_k)] + [-1] * (dsa_topk - valid_k)
    raw = device_values(torch, row * (tokens * kv_heads), dtype=int32_dt, device=device)
    viewer = getattr(raw, "view", None)
    return viewer(tokens, kv_heads, dsa_topk) if callable(viewer) else raw


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
        dtype_name = str(case.get("dtype", "bf16"))
        kv_name = INT8 if builder == "block_sparse_attention_c8" else dtype_name
        kv_dtype = getattr(torch, INT8, dtype) if kv_name == INT8 else dtype
        rope_dim = int(shape.get("qk_rope_head_dim") or (OP_CFG["mla_rope_dim"] if head_dim == int(OP_CFG["mla_latent_dim"]) else 0))
        slots = cold_ring_slot_count(
            case, context, (tokens * heads + seq_len * kv_heads) * (head_dim + rope_dim) * element_bytes(kv_name)
        )
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        kv_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(seq_len, kv_heads, head_dim), dtype=kv_dtype,
            dtype_name=kv_name, device=device,
        )
        int32_dt = getattr(torch, INT32, None)
        scale = 1.0 / math.sqrt(head_dim + rope_dim)
        if builder == "sparse_flash_attention":
            dsa_topk = dim_int(shape, "top_k", int(OP_CFG["dsa_index_topk"]))
            record_actual_shape(context, tokens=tokens, sequences=1, q_len=tokens, seq_len=seq_len,
                                heads=heads, kv_heads=kv_heads, head_dim=head_dim, top_k=dsa_topk)
            charge_alloc_bytes(
                context, tokens * kv_heads * dsa_topk * int(OP_CFG["float32_element_bytes"])
            )
            indices = _dsa_sparse_indices(
                torch, tokens=tokens, kv_heads=kv_heads, seq_len=seq_len,
                dsa_topk=dsa_topk, int32_dt=int32_dt, device=device,
            )
            seq_q = device_values(torch, [tokens], dtype=int32_dt, device=device)
            seq_kv = device_values(torch, [seq_len], dtype=int32_dt, device=device)
            q_rope_ring = (
                slice_ring_tensors(torch, context, num_slots=slots, dims=(tokens, heads, rope_dim), dtype=dtype, dtype_name=dtype_name, device=device)
                if rope_dim > 0 else ()
            )
            k_rope_ring = (
                slice_ring_tensors(torch, context, num_slots=slots, dims=(seq_len, kv_heads, rope_dim), dtype=dtype, dtype_name=dtype_name, device=device)
                if rope_dim > 0 else ()
            )
            return wrap_ring_step(
                slots,
                lambda s: op(
                    q_ring[s], kv_ring[s], kv_ring[s], indices, scale,
                    layout_query="TND", layout_kv="TND", attention_mode=2,
                    actual_seq_lengths_query=seq_q, actual_seq_lengths_kv=seq_kv,
                    **({"query_rope": q_rope_ring[s], "key_rope": k_rope_ring[s]} if rope_dim > 0 else {}),
                ),
                retain_outputs=True,
            )
        topk = int(OP_CFG["topk_gating_default"])
        record_actual_shape(
            context, tokens=tokens, sequences=1, q_len=tokens, seq_len=seq_len,
            heads=heads, kv_heads=kv_heads, head_dim=head_dim, top_k=topk, dtype=dtype_name,
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
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(
            context, tokens=tokens, width=width, heads=heads, kv_heads=kv_heads,
            head_dim=head_dim, q_lora_rank=q_lora, kv_lora_rank=kv_lora,
            block_size=block_size, dtype=dtype_name,
        )
        weight_dtype = getattr(torch, INT8, dtype)
        eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
        token_x = zeros(torch, tokens, width, dtype=dtype, device=device)
        weight_dq = cast_weight_nz(
            torch, zeros(torch, width, q_lora, dtype=weight_dtype, device=device), context
        )
        weight_uq_qr = cast_weight_nz(
            torch, zeros(torch, q_lora, heads * head_dim, dtype=weight_dtype, device=device),
            context,
        )
        weight_uk = cast_weight_nz(
            torch, zeros(torch, heads, qk_nope, kv_lora, dtype=weight_dtype, device=device),
            context,
        )
        weight_dkv_kr = cast_weight_nz(
            torch, zeros(torch, width, kv_lora + rope, dtype=weight_dtype, device=device),
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
        dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
        record_actual_shape(context, tokens=tokens, width=width, seq_len=seq_len, dtype=dtype_name)
        eb = element_bytes(dtype_name)
        slots = cold_ring_slot_count(case, context, (tokens + seq_len) * width * eb)
        src_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        cache_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(seq_len, width), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )

        def source(slot: int) -> Any:
            return upstream_2d_input(
                context, src_ring[slot], (tokens, width), dtype=dtype, error="bench_kv_input_mismatch",
            )

        if with_indices:
            idx = zeros(torch, tokens, dtype=getattr(torch, INT32, None), device=device)
            return wrap_ring_step(slots, lambda s: op(source(s), cache_ring[s], idx))
        return wrap_ring_step(
            slots, lambda s: op(source(s), cache_ring[s]), retain_outputs=True
        )

    return build


def build_pool_key_indexer(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    """Bind CANN 9.3.0 ``pool_key_indexer`` with query, pool_key, weights, and pool_tail_k."""
    candidates = ("npu_pool_key_indexer", "pool_key_indexer")
    op = require_kernel(
        torch, case, context, candidates,
        builder="pool_key_indexer", upstream_abi="aclnnPoolKeyIndexer",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    heads = max(1, dim_int(shape, "heads", 1))
    head_dim = max(1, dim_int(shape, "head_dim", width))
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    pool_size = int(OP_CFG["pool_key_size_default"])
    pool_tokens = max(1, (seq_len + pool_size - 1) // pool_size)
    dtype_name = str(case.get("dtype") or BFLOAT16).strip().lower() or BFLOAT16
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    fp16 = getattr(torch, "float16", fp32)
    bf16 = getattr(torch, BFLOAT16, dtype)
    int32_dt = getattr(torch, INT32, None)
    int64_dt = getattr(torch, INT64, None)
    is_fp8 = dtype_name in {"fp8", "fp8_e4m3", "fp8_e5m2", "float8_e4m3fn", "float8_e5m2"}
    is_int8 = dtype_name == INT8
    topk_key = next((k for k in ("top_k", "topk", "sparse_count") if shape.get(k) is not None), None)
    if topk_key is not None:
        topk = dim_int(shape, topk_key, min(seq_len, int(OP_CFG["dsa_index_topk"])))
    else:
        raw_topk = min(seq_len, int(OP_CFG["dsa_index_topk"]))
        topk = max(pool_size, ((raw_topk + pool_size - 1) // pool_size) * pool_size)
        if seq_len < topk:
            seq_len = topk
            pool_tokens = max(1, (seq_len + pool_size - 1) // pool_size)
    eb = element_bytes(dtype_name)
    record_actual_shape(
        context, tokens=tokens, width=width, seq_len=seq_len,
        heads=heads, head_dim=head_dim, top_k=topk, dtype=dtype_name,
        **({topk_key: topk} if topk_key and topk_key != "top_k" else {}),
    )
    slots = cold_ring_slot_count(case, context, (tokens * heads + pool_tokens) * head_dim * eb)
    q_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    k_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(pool_tokens, 1, head_dim), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    weights = ones(torch, tokens, heads, dtype=fp16 if is_int8 else bf16, device=device)
    pool_tail_k = device_values(torch, [seq_len % pool_size], dtype=int64_dt, device=device)
    actual_seq_q = device_values(torch, [tokens], dtype=int32_dt, device=device)
    actual_seq_k = device_values(torch, [pool_tokens], dtype=int32_dt, device=device)
    extra_kw: dict[str, Any] = {
        "actual_seq_q": actual_seq_q,
        "actual_seq_k": actual_seq_k,
        "layout_q": "TND",
        "layout_k": "TND",
        "topk": topk,
        "pool_size": pool_size,
        "mask_mode": int(OP_CFG["pool_key_mask_mode_causal"]),
    }
    if is_fp8:
        extra_kw.update(
            q_descale=ones(torch, tokens, heads, dtype=fp32, device=device),
            k_descale=ones(torch, pool_tokens, 1, dtype=fp32, device=device),
            quant_mode=0,
        )
    elif is_int8:
        extra_kw.update(
            q_descale=ones(torch, tokens, heads, dtype=fp16, device=device),
            k_descale=ones(torch, pool_tokens, 1, dtype=fp16, device=device),
            quant_mode=2,
        )
    return wrap_ring_step(
        slots, lambda s: op(q_ring[s], k_ring[s], weights, pool_tail_k, **extra_kw),
        retain_outputs=True,
    )


def build_scatter_index_cache(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    """Bind CANN ``npu_scatter_nd_update(input, indices[T, 1], updates[T, D])``."""
    op = require_kernel(
        torch, case, context,
        ("npu_scatter_nd_update", "scatter_nd_update", "scatter_index_cache"),
        builder="scatter_index_cache", upstream_abi="aclnnScatterNdUpdate",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    dtype_name = str(case.get("dtype") or "bf16").strip().lower() or "bf16"
    dtype = resolve_case_dtype(torch, case)
    # CANN npu_scatter_nd_update supports fp32/fp16/bf16/int8/int64/bool; use 1-byte int8
    # carrier for 1-byte FP8/MXFP4 cache rows so byte footprint and scatter width match.
    if dtype_name in {"fp8", "fp8_e4m3", "fp8_e5m2", "float8_e4m3fn", "float8_e5m2", "mxfp8", "mxfp4", "hif8"}:
        store_dtype = getattr(torch, INT8, dtype)
        store_name = INT8
    else:
        store_dtype = dtype
        store_name = dtype_name
    record_actual_shape(context, tokens=tokens, width=width, seq_len=seq_len, dtype=dtype_name)
    eb = element_bytes(store_name)
    slots = cold_ring_slot_count(case, context, (tokens + seq_len) * width * eb)
    updates_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=store_dtype,
        dtype_name=store_name, device=device,
    )
    cache_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(seq_len, width), dtype=store_dtype,
        dtype_name=store_name, device=device,
    )
    indices = device_values(
        torch, [[idx % seq_len] for idx in range(tokens)],
        dtype=getattr(torch, INT32, None), device=device,
    )

    def updates(slot: int) -> Any:
        return upstream_2d_input(
            context, updates_ring[slot], (tokens, width), dtype=store_dtype, error="bench_kv_input_mismatch",
        )

    return wrap_ring_step(slots, lambda s: op(cache_ring[s], indices, updates(s)), retain_outputs=True)


def _mqsmla_packed_geometry(
    shape: Mapping[str, Any], head_dim: int, rope_dim: int, *, kv_eb: int, q_eb: int
) -> tuple[int, int, int]:
    """Derive ``(q_dim, nope_dim, packed_kv_bytes)`` for ``cann_ops_transformer.mixed_quant_sparse_flash_mla``."""
    mla_total_dim = int(OP_CFG["mla_latent_dim"])
    if head_dim == mla_total_dim and "latent" not in shape and "kv_lora_rank" not in shape:
        q_dim = head_dim
        nope_dim = max(0, head_dim - rope_dim)
    else:
        nope_dim = head_dim
        q_dim = head_dim + rope_dim
    quant_group = int(OP_CFG["mla_rope_dim"])
    scale_groups = max(1, (nope_dim + quant_group - 1) // quant_group)
    raw_row_bytes = nope_dim * kv_eb + (rope_dim + scale_groups) * q_eb
    row_align = int(OP_CFG["mqsmla_record_align_bytes"])
    packed_kv_bytes = ((raw_row_bytes + row_align - 1) // row_align) * row_align
    return q_dim, nope_dim, packed_kv_bytes


def build_mixed_quant_sparse_mla(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    """Mixed-quant sparse MLA (c8/INT8 or A5 FP8/BF16 KV + rope + paged PA_BBND)."""
    shape, device = shape_of(case), device_of(context)
    q_dtype_name = str(case.get("dtype") or BFLOAT16).strip().lower() or BFLOAT16
    raw_kv_dtype = str(shape.get("kv_dtype") or case.get("kv_dtype") or "").strip().lower()
    bf16_aliases = frozenset({"bf16", BFLOAT16})
    explicit_mixed = (
        str(case.get("recipe") or "").strip().lower() == "aclnn_mixed_quant_sparse_flash_mla"
        or str(case.get("implementation") or "").strip() == "aclnnMixedQuantSparseFlashMla"
    )
    quant_requested = (
        (bool(raw_kv_dtype) and raw_kv_dtype not in bf16_aliases)
        or (not raw_kv_dtype and q_dtype_name not in bf16_aliases)
        or (explicit_mixed and raw_kv_dtype not in bf16_aliases)
    )
    extra_mods = ("cann_ops_transformer", "vllm_ascend.ops", "vllm_ascend.ops.attention")
    mixed_candidates = ("mixed_quant_sparse_flash_mla", "npu_mixed_quant_sparse_flash_mla")
    candidates = (
        (*mixed_candidates, "npu_sparse_flash_mla", "mixed_quant_sparse_mla")
        if quant_requested
        else ("npu_sparse_flash_mla", *mixed_candidates, "mixed_quant_sparse_mla")
    )
    op = require_kernel(
        torch,
        case,
        context,
        candidates,
        builder="mixed_quant_sparse_mla",
        upstream_abi="aclnnMixedQuantSparseFlashMla",
        extra_modules=extra_mods,
    )
    resolved_name = next(
        (
            c
            for c in candidates
            if resolve_op(torch, c, context=context, extra_modules=extra_mods, allow_torch_attr=False) is op
        ),
        str(getattr(op, "__name__", "")),
    )
    tokens, heads, kv_heads, _default_hd = _attention_dims(shape)
    head_dim = dim_int(
        shape, "head_dim",
        dim_int(shape, "kv_lora_rank", dim_int(shape, "latent", int(OP_CFG["mla_latent_dim"]))),
    )
    rope_dim = dim_int(
        shape, "qk_rope_head_dim", dim_int(shape, "rope", int(OP_CFG["mla_rope_dim"]))
    )
    sequences = max(1, min(tokens, dim_int(shape, "sequences", 1)))
    q_len = dim_int(shape, "q_len", max(1, tokens // sequences))
    raw_kv = shape.get("kv_len")
    seq_len = max(tokens, dim_int(shape, "seq_len", dim_int(shape, "kv_len", tokens)))
    sparse_count = dim_int(
        shape,
        "sparse_count",
        dim_int(shape, "top_k", int(OP_CFG["dsa_index_topk"])),
    )
    q_dtype = torch_dtype(torch, BFLOAT16) or resolve_case_dtype(torch, case)
    scale_dt = getattr(torch, FLOAT32, q_dtype)
    int32_dt = getattr(torch, INT32, None)
    q_eb = element_bytes(BFLOAT16)
    extra_actual: dict[str, Any] = {
        "sequences": sequences,
        "q_len": q_len,
    }
    if "width" in shape:
        extra_actual["width"] = dim_int(shape, "width")
    if "latent" in shape:
        extra_actual["latent"] = head_dim
    if "kv_lora_rank" in shape:
        extra_actual["kv_lora_rank"] = head_dim
    if "rope" in shape:
        extra_actual["rope"] = rope_dim
    if raw_kv is not None:
        extra_actual["kv_len"] = int(raw_kv)
    if "is_prefill" in shape:
        extra_actual["is_prefill"] = int(shape["is_prefill"])
    block_size = dim_int(shape, "block_size", int(OP_CFG["smla_block_size"]))
    kv_per_seq = max(1, (seq_len + sequences - 1) // sequences)
    pages_per_seq = max(1, (kv_per_seq + block_size - 1) // block_size)
    total_blocks = sequences * pages_per_seq
    base_q, rem_q = divmod(tokens, sequences)
    q_lens = [base_q + (1 if idx < rem_q else 0) for idx in range(sequences)]
    cu_q_vals = [0]
    for ql in q_lens:
        cu_q_vals.append(cu_q_vals[-1] + ql)
    if resolved_name == "npu_sparse_flash_mla":
        if quant_requested:
            req_kv = raw_kv_dtype or (q_dtype_name if q_dtype_name not in bf16_aliases else INT8)
            raise_unmodeled(
                case,
                builder="mixed_quant_sparse_mla",
                upstream_abi="aclnnMixedQuantSparseFlashMla",
                reason=f"npu_sparse_flash_mla_bf16_only:quantized_kv_unsupported:{req_kv}",
                candidates=mixed_candidates,
                context=context,
            )
        total_dim = head_dim + rope_dim
        scale = 1.0 / math.sqrt(total_dim)
        record_actual_shape(
            context,
            tokens=tokens,
            heads=heads,
            kv_heads=kv_heads,
            head_dim=head_dim,
            qk_rope_head_dim=rope_dim,
            seq_len=seq_len,
            top_k=sparse_count,
            sparse_count=sparse_count,
            kv_dtype="bf16",
            kv_bytes_per_token=total_dim * q_eb,
            **extra_actual,
        )
        per_slot = (tokens * heads + total_blocks * block_size * kv_heads) * total_dim * q_eb
        slots = cold_ring_slot_count(case, context, per_slot)
        q_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, heads, total_dim),
            dtype=q_dtype, dtype_name=BFLOAT16, device=device,
        )
        ori_kv_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(total_blocks, block_size, kv_heads, total_dim),
            dtype=q_dtype, dtype_name=BFLOAT16, device=device,
        )
        cu_q = device_values(torch, cu_q_vals, dtype=int32_dt, device=device)
        seq_ori = device_values(torch, [kv_per_seq] * sequences, dtype=int32_dt, device=device)
        block_table = device_values(
            torch,
            [list(range(idx * pages_per_seq, (idx + 1) * pages_per_seq)) for idx in range(sequences)],
            dtype=int32_dt, device=device,
        )
        eff_topk = min(kv_per_seq, sparse_count)
        indices = _dsa_sparse_indices(
            torch, tokens=tokens, kv_heads=kv_heads, seq_len=kv_per_seq,
            dsa_topk=sparse_count, int32_dt=int32_dt, device=device,
        )
        ori_topk_len = device_values(torch, [eff_topk] * tokens, dtype=int32_dt, device=device)
        meta_op = resolve_op(
            torch, "npu_sparse_flash_mla_metadata", context=context, allow_torch_attr=False
        )
        smla_meta = (
            meta_op(
                heads, kv_heads, total_dim,
                cu_seqlens_q=cu_q, seqused_ori_kv=seq_ori,
                batch_size=sequences, max_seqlen_q=max(q_lens),
                max_seqlen_ori_kv=kv_per_seq, ori_topk=sparse_count,
                ori_topk_length=ori_topk_len, cmp_topk=0, cmp_ratio=0,
                ori_mask_mode=0, cmp_mask_mode=0,
                layout_q="TND", layout_kv="PA_BBND",
                has_ori_kv=True, has_cmp_kv=False,
            )
            if callable(meta_op) else None
        )
        return wrap_ring_step(
            slots,
            lambda s: op(
                q_ring[s],
                ori_kv=ori_kv_ring[s],
                ori_sparse_indices=indices,
                ori_topk_length=ori_topk_len,
                ori_block_table=block_table,
                cu_seqlens_q=cu_q,
                seqused_ori_kv=seq_ori,
                metadata=smla_meta,
                softmax_scale=scale,
                cmp_ratio=0,
                ori_mask_mode=0,
                cmp_mask_mode=0,
                layout_q="TND",
                layout_kv="PA_BBND",
                topk_value_mode=1,
                return_softmax_lse=False,
            ),
            retain_outputs=True,
        )
    kv_name = raw_kv_dtype or (
        q_dtype_name if q_dtype_name in {"fp8_e4m3", "fp8", "float8_e4m3fn", "mxfp8", INT8} else INT8
    )
    kv_dtype = torch_dtype(torch, kv_name)
    if kv_dtype is None:
        raise_unmodeled(
            case,
            builder="mixed_quant_sparse_mla",
            upstream_abi="aclnnMixedQuantSparseFlashMla",
            reason=f"missing_native_dtype:{kv_name}",
            candidates=candidates,
            context=context,
        )
    kv_eb = element_bytes(kv_dtype)
    q_dim, _nope_dim, packed_kv_bytes = _mqsmla_packed_geometry(
        shape, head_dim, rope_dim, kv_eb=kv_eb, q_eb=q_eb
    )
    packed_kv_elems = max(1, packed_kv_bytes // kv_eb)
    quant_mode = int(OP_CFG["mqsmla_packed_quant_mode"])
    scale = 1.0 / math.sqrt(q_dim)
    record_actual_shape(
        context,
        tokens=tokens,
        heads=heads,
        kv_heads=kv_heads,
        head_dim=head_dim,
        qk_rope_head_dim=rope_dim,
        seq_len=seq_len,
        top_k=sparse_count,
        sparse_count=sparse_count,
        kv_dtype=kv_name,
        scale_dtype="bf16",
        quant_mode=quant_mode,
        kv_bytes_per_token=packed_kv_bytes,
        ori_kv_record_bytes=packed_kv_bytes,
        layout_q="TND",
        layout_kv="PA_BBND",
        **extra_actual,
    )
    per_slot = (
        tokens * heads * q_dim * q_eb
        + total_blocks * block_size * kv_heads * packed_kv_bytes
    )
    slots = cold_ring_slot_count(case, context, per_slot)
    q_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, q_dim),
        dtype=q_dtype, dtype_name=BFLOAT16, device=device,
    )
    ori_kv_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(total_blocks, block_size, kv_heads, packed_kv_elems),
        dtype=kv_dtype, dtype_name=kv_name, device=device,
    )
    cu_q = device_values(torch, cu_q_vals, dtype=int32_dt, device=device)
    seq_ori = device_values(torch, [kv_per_seq] * sequences, dtype=int32_dt, device=device)
    block_table = device_values(
        torch,
        [list(range(idx * pages_per_seq, (idx + 1) * pages_per_seq)) for idx in range(sequences)],
        dtype=int32_dt, device=device,
    )
    eff_topk = min(kv_per_seq, sparse_count)
    indices = _dsa_sparse_indices(
        torch, tokens=tokens, kv_heads=kv_heads, seq_len=kv_per_seq,
        dsa_topk=sparse_count, int32_dt=int32_dt, device=device,
    )
    ori_topk_len = device_values(torch, [eff_topk] * tokens, dtype=int32_dt, device=device)
    sinks = zeros(torch, heads, dtype=scale_dt, device=device)
    mq_meta_op = (
        resolve_op(
            torch, "mixed_quant_sparse_flash_mla_metadata",
            context=context, extra_modules=extra_mods, allow_torch_attr=False,
        )
        or resolve_op(
            torch, "npu_mixed_quant_sparse_flash_mla_metadata",
            context=context, extra_modules=extra_mods, allow_torch_attr=False,
        )
    )
    mq_meta = (
        mq_meta_op(
            num_heads_q=heads,
            num_heads_kv=kv_heads,
            head_dim=q_dim,
            cu_seqlens_q=cu_q,
            seqused_ori_kv=seq_ori,
            batch_size=sequences,
            max_seqlen_q=max(q_lens),
            max_seqlen_ori_kv=kv_per_seq,
            ori_topk=sparse_count,
            ori_topk_length=ori_topk_len,
            cmp_topk=0,
            cmp_ratio=1,
            quant_mode=quant_mode,
            rope_head_dim=rope_dim,
            ori_mask_mode=0,
            cmp_mask_mode=0,
            layout_q="TND",
            layout_kv="PA_BBND",
            has_ori_kv=True,
            has_cmp_kv=False,
        )
        if callable(mq_meta_op) else None
    )
    return wrap_ring_step(
        slots,
        lambda s: op(
            q_ring[s],
            ori_kv=ori_kv_ring[s],
            ori_sparse_indices=indices,
            ori_topk_length=ori_topk_len,
            ori_block_table=block_table,
            cu_seqlens_q=cu_q,
            seqused_ori_kv=seq_ori,
            sinks=sinks,
            metadata=mq_meta,
            quant_mode=quant_mode,
            rope_head_dim=rope_dim,
            softmax_scale=scale,
            cmp_ratio=1,
            ori_mask_mode=0,
            cmp_mask_mode=0,
            layout_q="TND",
            layout_kv="PA_BBND",
            topk_value_mode=1,
            return_softmax_lse=False,
        ),
        retain_outputs=True,
    )


def build_dcp_query_pack(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    candidates = ("npu_dcp_query_pack", "dcp_query_pack", "pack_dcp_query")
    op = require_kernel(
        torch, case, context, candidates,
        builder="dcp_query_pack", upstream_abi="aclnnDcpQueryPack",
        extra_modules=("vllm_ascend.ops", "vllm_ascend.ops.context_parallel"),
    )
    shape, device = shape_of(case), device_of(context)
    tokens, heads, _kv_heads, _default_hd = _attention_dims(shape)
    head_dim = dim_int(shape, "head_dim", dim_int(shape, "width", _default_hd))
    rope_dim = dim_int(shape, "qk_rope_head_dim", int(OP_CFG["mla_rope_dim"]))
    dcp = max(1, dim_int(shape, "dcp", dim_int(shape, "partial_count", 2)))
    dtype = resolve_case_dtype(torch, case)
    dtype_name = str(case.get("dtype") or BFLOAT16)
    eb = element_bytes(dtype_name)
    record_actual_shape(
        context, tokens=tokens, heads=heads, head_dim=head_dim, width=heads * head_dim,
        qk_rope_head_dim=rope_dim, dcp=dcp, dtype=dtype_name,
    )
    slots = cold_ring_slot_count(case, context, tokens * heads * (head_dim + rope_dim) * eb * 2)
    q_nope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim),
        dtype=dtype, dtype_name=dtype_name, device=device,
    )
    q_rope_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, rope_dim),
        dtype=dtype, dtype_name=dtype_name, device=device,
    )
    return wrap_ring_step(slots, lambda s: op(q_nope_ring[s], q_rope_ring[s], dcp), retain_outputs=True)


def build_dcp_output_pack(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    candidates = ("npu_dcp_output_pack", "dcp_output_pack", "pack_dcp_output_lse", "pack_dcp_output")
    extra_mods = ("vllm_ascend.ops.triton.dcp.dcp_a2a", "vllm_ascend.ops", "vllm_ascend.ops.context_parallel")
    op = require_kernel(
        torch, case, context, candidates,
        builder="dcp_output_pack", upstream_abi="aclnnDcpOutputPack",
        extra_modules=extra_mods,
    )
    shape, device = shape_of(case), device_of(context)
    tokens, heads, _kv_heads, _default_hd = _attention_dims(shape)
    head_dim = dim_int(shape, "head_dim", dim_int(shape, "width", _default_hd))
    dcp = max(1, dim_int(shape, "dcp", dim_int(shape, "partial_count", 2)))
    scatter_dim = int(shape.get("scatter_dim", 1))
    if scatter_dim == 1 and heads % dcp != 0:
        if tokens % dcp == 0:
            scatter_dim = 0
        else:
            dcp = 1
    elif scatter_dim == 0 and tokens % dcp != 0:
        dcp = 1
    dtype = resolve_case_dtype(torch, case)
    dtype_name = str(case.get("dtype") or BFLOAT16)
    fp32 = getattr(torch, FLOAT32, dtype)
    eb = element_bytes(dtype_name)
    record_actual_shape(
        context, tokens=tokens, heads=heads, head_dim=head_dim,
        width=dim_int(shape, "width", heads * head_dim),
        dcp=dcp, scatter_dim=scatter_dim, dtype=dtype_name,
    )
    slots = cold_ring_slot_count(case, context, tokens * heads * head_dim * eb * 2)
    out_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim),
        dtype=dtype, dtype_name=dtype_name, device=device,
    )
    lse_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, 1),
        dtype=fp32, dtype_name=FLOAT32, device=device,
    )
    return wrap_ring_step(
        slots, lambda s: op(out_ring[s], lse_ring[s], dcp, scatter_dim), retain_outputs=True
    )


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
    partial_count = max(2, dim_int(shape, "partial_count", 2))
    case_dtype = str(case.get("dtype", "bf16"))
    record_actual_shape(context, tokens=tokens, heads=heads, kv_heads=kv_heads, head_dim=head_dim,
                        width=heads * head_dim, sequences=1, q_len=tokens, partial_count=partial_count, dtype=case_dtype)
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    eb = element_bytes(case_dtype)
    slots = cold_ring_slot_count(case, context, tokens * heads * head_dim * eb * partial_count)
    outs = [
        slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
            dtype_name=case_dtype, device=device,
        )
        for _ in range(partial_count)
    ]
    stat_width = int(OP_CFG["ring_attn_stat_width"])
    charge_alloc_bytes(
        context, tokens * heads * stat_width * int(OP_CFG["float32_element_bytes"]) * 2 * partial_count
    )
    maxes = [ones(torch, tokens, heads, stat_width, dtype=fp32, device=device) for _ in range(partial_count)]
    sums = [ones(torch, tokens, heads, stat_width, dtype=fp32, device=device) for _ in range(partial_count)]
    for idx in range(1, partial_count):
        if callable(getattr(maxes[idx], "fill_", None)):
            maxes[idx].fill_(idx + 1)
        if callable(getattr(sums[idx], "fill_", None)):
            sums[idx].fill_(idx + 1)
    actual_seq_qlen = device_values(
        torch, [0, tokens], dtype=getattr(torch, INT64, None), device=device
    )

    def _merge(s: int) -> Any:
        acc_o, acc_m, acc_s = outs[0][s], maxes[0], sums[0]
        out: Any = None
        for idx in range(1, partial_count):
            out = op(
                acc_o, acc_m, acc_s, outs[idx][s], maxes[idx], sums[idx],
                actual_seq_qlen=actual_seq_qlen,
                input_layout="TND",
                input_softmax_layout="TND",
            )
            if isinstance(out, (tuple, list)) and len(out) > 2:
                acc_o, acc_m, acc_s = out[0], out[1], out[2]
            elif out is not None:
                acc_o = out
        return out

    return wrap_ring_step(slots, _merge, retain_outputs=True)


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
    eff_tokens, eff_head_dim = tokens, head_dim
    rope_align = int(OP_CFG["mla_rope_dim"])
    if eff_head_dim == 1 and eff_tokens >= rope_align and eff_tokens % rope_align == 0:
        eff_tokens, eff_head_dim = eff_tokens // rope_align, rope_align
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(
        context, tokens=tokens, heads=heads, head_dim=head_dim,
        width=dim_int(shape, "width", heads * head_dim), dtype=dtype_name,
    )
    dtype = resolve_case_dtype(torch, case)
    eb = element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, eff_tokens * heads * eff_head_dim * eb * 2)
    query_shape = (1, eff_tokens, heads, eff_head_dim)
    q_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=query_shape, dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    cos = ones(torch, 1, eff_tokens, 1, eff_head_dim, dtype=dtype, device=device)
    sin = zeros(torch, 1, eff_tokens, 1, eff_head_dim, dtype=dtype, device=device)
    return wrap_ring_step(
        slots, lambda s: op(rotary_query_input(context, q_ring[s], query_shape, dtype=dtype), cos, sin),
        retain_outputs=True,
    )


def build_split_qkv_rmsnorm_rope(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    candidates = (
        "split_qkv_rmsnorm_rope",
        "npu_split_qkv_rmsnorm_rope",
        "split_qkv_rmsnorm_rope_impl",
        "qkv_rmsnorm_rope",
        "split_qkv_rmsnorm_mrope_kernel",
        "split_qkv_rmsnorm_rope_kernel",
    )
    extra_mods = ("vllm_ascend.ops.triton.linearnorm.split_qkv_rmsnorm_rope",)
    op = require_kernel(
        torch,
        case,
        context,
        candidates,
        builder="split_qkv_rmsnorm_rope",
        upstream_abi="split_qkv_rmsnorm_mrope_kernel",
        extra_modules=extra_mods,
    )
    resolved = next(
        (c for c in candidates if resolve_op(torch, c, context=context, extra_modules=extra_mods, allow_torch_attr=False) is op),
        str(getattr(op, "__name__", "")),
    )
    device = device_of(context)
    tokens, width = dims_2d(case)
    head_dim = int(OP_CFG["attention_head_dim"])
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, head_dim=head_dim, dtype=dtype_name)
    dtype = resolve_case_dtype(torch, case)
    if resolved in {"split_qkv_rmsnorm_rope_impl", "qkv_rmsnorm_rope"}:
        min_sum = int(OP_CFG["split_qkv_min_heads_sum"])
        if width < head_dim * min_sum:
            head_dim = max(int(OP_CFG["split_qkv_min_head_dim"]), width // int(OP_CFG["split_qkv_kv_divisor"]))
        total = max(width, head_dim * min_sum)
        kv_heads = max(1, (total // head_dim) // int(OP_CFG["split_qkv_kv_divisor"]))
        kv_hidden = kv_heads * head_dim
        q_hidden = total - 2 * kv_hidden
        max_pos = max(tokens, int(OP_CFG["split_qkv_max_pos"]))
        eb = element_bytes(dtype_name)
        slots = cold_ring_slot_count(case, context, tokens * total * eb * 2)
        qkv_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, total), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        cos_sin = ones(torch, max_pos, head_dim, dtype=dtype, device=device)
        positions = device_values(
            torch, [idx % max_pos for idx in range(tokens)],
            dtype=getattr(torch, INT64, None), device=device,
        )
        q_w = ones(torch, head_dim, dtype=dtype, device=device)
        k_w = ones(torch, head_dim, dtype=dtype, device=device)
        eps = float(case.get("epsilon", OP_CFG["rms_norm_epsilon"]))
        return wrap_ring_step(
            slots,
            lambda s: op(qkv_ring[s], cos_sin, positions, q_w, k_w, q_hidden, kv_hidden, head_dim, eps),
            retain_outputs=True,
        )
    qkv = zeros(torch, tokens, max(width, head_dim * 2), dtype=dtype, device=device)
    q_w = ones(torch, head_dim, dtype=dtype, device=device)
    k_w = ones(torch, head_dim, dtype=dtype, device=device)
    cos = ones(torch, tokens, head_dim, dtype=dtype, device=device)
    sin = zeros(torch, tokens, head_dim, dtype=dtype, device=device)
    return wrap_ring_step(1, lambda _s: op(qkv, q_w, k_w, cos, sin), retain_outputs=True)


def build_indexer_topk(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    require_npu_surface(torch, case, context, builder="indexer_topk", upstream_abi="aclnnTopkV2")
    op = (
        resolve_op(torch, "npu_topk_v2", context=context, allow_torch_attr=False)
        or resolve_op(torch, "indexer_topk", context=context, allow_torch_attr=False)
        or resolve_op(torch, "topk", context=context, allow_torch_attr=True)
    )
    if not callable(op):
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
    record_actual_shape(context, tokens=tokens, width=width, top_k=top_k)
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
    dtype_name = str(case.get("dtype", "bf16")).strip().lower() or "bf16"
    quant = dtype_name in {"fp8_e4m3", "float8_e4m3fn", "fp8", "int8", "hif8", "mxfp8", "mxfp4"}
    candidates = (
        ("npu_quant_lightning_indexer_v2", "npu_quant_lightning_indexer_v3",
         "npu_quant_lightning_indexer", "npu_lightning_indexer", "lightning_indexer")
        if quant else
        ("npu_lightning_indexer", "npu_quant_lightning_indexer_v3",
         "npu_quant_lightning_indexer", "lightning_indexer")
    )
    op = require_kernel(
        torch, case, context, candidates, builder="lightning_indexer",
        upstream_abi="aclnnQuantLightningIndexerV2" if quant else "aclnnLightningIndexer",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    heads, head_dim = max(1, dim_int(shape, "heads", 1)), max(1, dim_int(shape, "head_dim", width))
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    scale_name = "fp16" if dtype_name == "int8" else "fp32"
    scale_dt = getattr(torch, "float16", fp32) if scale_name == "fp16" else fp32
    eb = element_bytes(dtype_name)
    topk_limit = int(OP_CFG["dsa_index_topk"])
    explicit_topk_key = next(
        (key for key in ("sparse_count", "top_k", "topk") if shape.get(key) is not None), None,
    )
    block_topk = dim_int(shape, explicit_topk_key, topk_limit) if explicit_topk_key else min(seq_len, topk_limit)
    actual_extra: dict[str, Any] = {explicit_topk_key: block_topk} if explicit_topk_key in {"sparse_count", "topk"} else {}
    if quant:
        actual_extra.update(query_dequant_scale_dtype=scale_name, key_dequant_scale_dtype=scale_name)
    record_actual_shape(
        context, tokens=tokens, sequences=1, q_len=tokens, seq_len=seq_len,
        heads=heads, kv_heads=1, head_dim=head_dim, width=dim_int(shape, "width", heads * head_dim),
        top_k=block_topk, query_dtype=dtype_name, cache_dtype=dtype_name, **actual_extra,
    )
    kname = resolved_kernel_name(torch, op, candidates, context)
    int32_dt = getattr(torch, INT32, None)
    if kname in {"npu_quant_lightning_indexer_v2", "npu_quant_lightning_indexer_v3"}:
        q_mode = int(OP_CFG["qli_v2_int8_quant_mode"] if dtype_name == "int8" else OP_CFG["qli_v2_fp8_quant_mode"])
        mask_mode = int(OP_CFG["qli_v2_mask_mode_causal"])
        cu_q = device_values(torch, [0, tokens], dtype=int32_dt, device=device)
        seq_k = device_values(torch, [seq_len], dtype=int32_dt, device=device)
        meta_op = resolve_op(
            torch, "npu_quant_lightning_indexer_v2_metadata", context=context, allow_torch_attr=False
        )
        weights = ones(torch, tokens, heads, dtype=scale_dt, device=device)
        q_scale = ones(torch, tokens, heads, dtype=scale_dt, device=device)
        if callable(meta_op):
            block_size = dim_int(shape, "block_size", int(OP_CFG["qli_v2_block_size"]))
            num_blocks = max(1, (seq_len + block_size - 1) // block_size)
            slots = cold_ring_slot_count(
                case, context, (tokens * heads + num_blocks * block_size) * head_dim * eb
            )
            src_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            k_ring = slice_ring_tensors(
                torch, context, num_slots=slots, dims=(num_blocks, block_size, 1, head_dim), dtype=dtype,
                dtype_name=dtype_name, device=device,
            )
            k_scale = ones(torch, num_blocks, block_size, 1, dtype=scale_dt, device=device)
            block_table = device_values(torch, [list(range(num_blocks))], dtype=int32_dt, device=device)
            qli_meta = meta_op(
                heads, 1, head_dim, block_topk, q_mode,
                cu_seqlens_q=cu_q, seqused_k=seq_k, batch_size=1,
                max_seqlen_q=tokens, max_seqlen_k=seq_len,
                layout_q="TND", layout_k="PA_BBND", mask_mode=mask_mode, cmp_ratio=1,
            )
            return wrap_ring_step(
                slots,
                lambda s: op(
                    src_ring[s], k_ring[s], weights,
                    query_dequant_scale=q_scale, key_dequant_scale=k_scale,
                    topk=block_topk, quant_mode=q_mode,
                    cu_seqlens_q=cu_q, seqused_k=seq_k, block_table=block_table,
                    metadata=qli_meta, layout_q="TND", layout_k="PA_BBND",
                    mask_mode=mask_mode, cmp_ratio=1, return_value=0,
                ),
                retain_outputs=True,
            )
        slots = cold_ring_slot_count(case, context, (tokens * heads + seq_len) * head_dim * eb)
        src_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        cache_ring = slice_ring_tensors(
            torch, context, num_slots=slots, dims=(seq_len, 1, head_dim), dtype=dtype,
            dtype_name=dtype_name, device=device,
        )
        k_scale = ones(torch, seq_len, 1, dtype=scale_dt, device=device)
        return wrap_ring_step(
            slots,
            lambda s: op(
                src_ring[s], cache_ring[s], weights,
                query_dequant_scale=q_scale, key_dequant_scale=k_scale,
                topk=block_topk, quant_mode=q_mode,
                cu_seqlens_q=cu_q, seqused_k=seq_k,
                layout_q="TND", layout_k="TND", mask_mode=mask_mode, cmp_ratio=1,
            ),
            retain_outputs=True,
        )
    slots = cold_ring_slot_count(case, context, (tokens * heads + seq_len) * head_dim * eb)
    src_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, heads, head_dim), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    cache_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(seq_len, 1, head_dim), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    # CANN aclnnLightningIndexer requires weights dtype to match query/key (bf16/fp16).
    weights = ones(torch, tokens, heads, dtype=scale_dt if quant else dtype, device=device)
    if kname.startswith("npu_"):
        seq_q = device_values(torch, [tokens], dtype=int32_dt, device=device)
        seq_k = device_values(torch, [seq_len], dtype=int32_dt, device=device)
        extra_kw: dict[str, Any] = {}
        if quant or kname.startswith("npu_quant_lightning_indexer"):
            extra_kw["query_dequant_scale"] = ones(torch, tokens, heads, dtype=scale_dt, device=device)
            extra_kw["key_dequant_scale"] = ones(torch, seq_len, 1, dtype=scale_dt, device=device)
            if kname == "npu_quant_lightning_indexer":
                extra_kw["query_quant_mode"] = 0
                extra_kw["key_quant_mode"] = 0
        return wrap_ring_step(
            slots,
            lambda s: op(
                src_ring[s], cache_ring[s], weights,
                actual_seq_lengths_query=seq_q, actual_seq_lengths_key=seq_k,
                layout_query="TND", layout_key="TND", sparse_count=block_topk, **extra_kw,
            ),
            retain_outputs=True,
        )
    return wrap_ring_step(slots, lambda s: op(src_ring[s], cache_ring[s], weights, block_topk), retain_outputs=True)


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
        candidates=(
            ("npu_fused_infer_attention_score",)
            if str((context or {}).get("soc_arch") or (context or {}).get("arch") or "").strip().upper() == "A5"
            else ("npu_incre_flash_attention", "npu_fused_infer_attention_score")
        ),
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
    "mixed_quant_sparse_mla": build_mixed_quant_sparse_mla,
    "dcp_query_pack": build_dcp_query_pack,
    "dcp_output_pack": build_dcp_output_pack,
    "mla_kv_compressor": _indexer_or_cache_builder(
        builder="mla_kv_compressor", upstream_abi="aclnnCompressor",
        candidates=("compressor_from_projected", "npu_mla_kv_compressor", "npu_compressor", "mla_kv_compressor"),
    ),
    "lightning_indexer": build_lightning_indexer,
    "pool_key_indexer": build_pool_key_indexer,
    "key_pool": _indexer_or_cache_builder(
        builder="key_pool", upstream_abi="aclnnKeyPool",
        candidates=("npu_key_pool", "key_pool"),
    ),
    "indexer_quant_cache": _indexer_or_cache_builder(
        builder="indexer_quant_cache", upstream_abi="aclnnIndexerQuantCache",
        candidates=("npu_indexer_quant_cache", "indexer_quant_cache"), with_indices=True,
    ),
    "kv_compress_epilog": build_kv_compress_epilog,
    "block_sparse_attention_c8": build_sparse_attention(
        builder="block_sparse_attention_c8", upstream_abi="aclnnGenericBlockSparseAttention",
        candidates=("npu_generic_block_sparse_attention", "npu_block_sparse_attention", "block_sparse_attention_c8"),
    ),
    "dcp_lse_attention_merge": build_dcp_lse_attention_merge,
    "scatter_pa_kv_cache": build_scatter_pa_kv_cache,
    "scatter_index_cache": build_scatter_index_cache,
    "rotary_embedding": build_rotary_embedding,
    "split_qkv_rmsnorm_rope": build_split_qkv_rmsnorm_rope,
    "indexer_topk": build_indexer_topk,
}

__all__ = ["ATTENTION_MLA_BUILDERS"]
