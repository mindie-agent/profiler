"""Fused GDN and KDA recurrent-state benchmark builders.

[Role]
  Prepare the query, sequence offsets and state pools used by the fused
  GDN and KDA kernels and enqueue their declared shapes.

[Invariants]
  Budget enforcement preserves the planned token and head counts. Indexed
  recurrent cases keep one sequence-length entry per logical request.

[Timeouts & Locks]
  Allocates inputs before timing. Takes no locks.

[Side-Effect Policy]
  Allocates only on the caller's admitted device.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping, Sequence

from ..events import ProfilerUsageError
from .operators_common import (
    BFLOAT16, FLOAT32, INT32, INT64, OP_CFG, _lazy_module, charge_alloc_bytes,
    cold_ring_slot_count, device_of, device_values, dim_int, element_bytes, ones,
    raise_unmodeled, record_actual_shape, require_kernel, require_npu_surface,
    resolve_case_dtype, resolve_op, shape_of, slice_ring_tensors, wrap_ring_step, zeros,
)


def _filled(torch: Any, dims: Sequence[int], val: float, *, dtype: Any, device: str) -> Any:
    t = ones(torch, *dims, dtype=dtype, device=device)
    if callable(getattr(t, "fill_", None)):
        t.fill_(val)
    return t


_KDA_MODULES = ("vllm_ascend.ops.triton.kda", "vllm_ascend.ops.triton.kda.kda")


def _build_indexed_recurrent(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any], *,
    builder: str, upstream_abi: str,
) -> Callable[[], Any]:
    """Use the indexed state-pool ABI for the declared batch and q length."""
    shape, device = shape_of(case), device_of(context)
    batch, q_len = dim_int(shape, "sequences"), dim_int(shape, "q_len")
    tokens, state_len = dim_int(shape, "tokens"), dim_int(shape, "state_len")
    heads, head_dim = dim_int(shape, "heads"), dim_int(shape, "head_dim")
    if tokens != batch * q_len or state_len <= tokens:
        raise ProfilerUsageError("bench_recurrent_state_shape_invalid")
    kda = builder == "fused_recurrent_kda"
    if kda:
        require_npu_surface(torch, case, context, builder=builder, upstream_abi=upstream_abi)
        for module_name in _KDA_MODULES:
            module = _lazy_module(module_name, {**context, "torch": torch})
            op = getattr(module, builder, None)
            if callable(op):
                break
        else:
            raise_unmodeled(case, builder=builder, upstream_abi=upstream_abi,
                            reason="missing_kernel:vllm_ascend.fused_recurrent_kda",
                            candidates=(builder,), context=context)
    else:
        op = require_kernel(torch, case, context, ("npu_recurrent_gated_delta_rule",),
                            builder=builder, upstream_abi=upstream_abi)
    record_actual_shape(context, sequences=batch, q_len=q_len, tokens=tokens,
                        state_len=state_len, heads=heads, head_dim=head_dim)
    dtype = resolve_case_dtype(torch, case)
    fp32 = getattr(torch, FLOAT32, dtype)
    dtype_name = str(case["dtype"])
    state_dtype = FLOAT32 if kda else dtype_name
    state_bytes = state_len * heads * head_dim * head_dim * element_bytes(state_dtype)
    charge_alloc_bytes(context, state_bytes, reason="recurrent state pool")
    dims = (1, tokens, heads, head_dim) if kda else (tokens, heads, head_dim)
    slot_bytes = tokens * heads * head_dim * element_bytes(dtype_name) * int(OP_CFG["binary_io_tensor_count"])
    slots = cold_ring_slot_count(case, context, slot_bytes)
    q, k, v = (
        slice_ring_tensors(torch, context, num_slots=slots, dims=dims, dtype=dtype,
                           dtype_name=dtype_name, device=device)
        for _ in ("query", "key", "value")
    )
    state = zeros(torch, state_len, heads, head_dim, head_dim, dtype=fp32 if kda else dtype, device=device)
    gate = _filled(torch, dims if kda else dims[:-1], float(OP_CFG["recurrent_gate_init"]),
                   dtype=fp32, device=device)
    beta = _filled(torch, dims[:-1], float(OP_CFG["recurrent_beta_init"]), dtype=dtype, device=device)
    # Slot zero is reserved in the indexed KDA path. Spread the live rows
    # through the pool so the state-length sweep also changes their spacing.
    indices = [1 + idx * (state_len - 1) // tokens for idx in range(tokens)]
    int32 = getattr(torch, INT32, None)
    scale = 1.0 / math.sqrt(head_dim)
    if kda:
        offsets = device_values(torch, list(range(0, tokens + 1, q_len)), dtype=int32, device=device)
        index_grid = [indices[start:start + q_len] for start in range(0, tokens, q_len)]
        state_idx = device_values(torch, index_grid, dtype=getattr(torch, INT64, None), device=device)
        return wrap_ring_step(slots, lambda s: op(
            q[s], k[s], v[s], gate, beta, scale=scale, initial_state=state,
            cu_seqlens=offsets, ssm_state_indices=state_idx, inplace_final_state=True,
            use_qk_l2norm_in_kernel=False,
        ), retain_outputs=True)
    lengths = device_values(torch, [q_len] * batch, dtype=int32, device=device)
    state_idx = device_values(torch, indices, dtype=int32, device=device)
    spec = {}
    if q_len > 1:
        spec["num_accepted_tokens"] = device_values(torch, [1] * batch, dtype=int32, device=device)
    return wrap_ring_step(slots, lambda s: op(
        q[s], k[s], v[s], state, g=gate, beta=beta, scale=scale,
        actual_seq_lengths=lengths, ssm_state_indices=state_idx, **spec,
    ), retain_outputs=True)


def recurrent_builder(
    *,
    builder: str,
    upstream_abi: str,
    candidates: Sequence[str],
    extra_modules: Sequence[str],
    tril: bool = False,
) -> Callable[[Any, Mapping[str, Any], Mapping[str, Any]], Callable[[], Any]]:
    def build(torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]) -> Callable[[], Any]:
        if builder in {"recurrent_gated_delta_rule", "fused_recurrent_kda"} and "q_len" in shape_of(case):
            return _build_indexed_recurrent(torch, case, context, builder=builder, upstream_abi=upstream_abi)
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
        if tril:
            tile = int(OP_CFG["tril_tile_dim"])
            chunks = max(1, (tokens + tile - 1) // tile)
            slots = cold_ring_slot_count(case, context, chunks * heads * tile * tile * element_bytes(FLOAT32))
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
        kda_shape = builder in {"chunk_kda_fwd", "fused_recurrent_kda"}
        record_actual_shape(context, tokens=tokens, heads=heads, head_dim=head_dim)
        qkv_name = BFLOAT16 if (chunk_tnd or recurrent_op) else str(case.get("dtype", "bf16"))
        qkv_dt = getattr(torch, BFLOAT16, dtype) if (chunk_tnd or recurrent_op) else dtype
        tensor_dims = (tokens, heads, head_dim) if (chunk_tnd or recurrent_op) else (1, tokens, heads, head_dim)
        int32_dt = getattr(torch, INT32, None)
        vllm_kda = builder == "fused_recurrent_kda" and (
            str(getattr(op, "__module__", "")).startswith("vllm_ascend")
            or (resolve_op(torch, "fused_recurrent_kda", context=context, extra_modules=(), allow_torch_attr=False) is not op
                and resolve_op(torch, "fused_recurrent_kda", context=context,
                               extra_modules=("vllm_ascend.ops.triton.kda", "vllm_ascend.ops.triton.kda.kda"),
                               allow_torch_attr=False) is op)
        )
        fp32_eb = int(OP_CFG["float32_element_bytes"])
        extra_out = tokens * heads * head_dim * head_dim * fp32_eb if vllm_kda else 0
        slots = cold_ring_slot_count(
            case, context, tokens * heads * head_dim * element_bytes(qkv_name) * int(OP_CFG["binary_io_tensor_count"]) + extra_out,
        )
        q_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=tensor_dims, dtype=qkv_dt, dtype_name=qkv_name, device=device)
        k_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=tensor_dims, dtype=qkv_dt, dtype_name=qkv_name, device=device)
        v_ring = slice_ring_tensors(torch, context, num_slots=slots, dims=tensor_dims, dtype=qkv_dt, dtype_name=qkv_name, device=device)
        if builder == "fused_gdn_gating":
            a_log, dt_bias = zeros(torch, heads, dtype=fp32, device=device), zeros(torch, heads, dtype=fp32, device=device)
            beta = ones(torch, 1, tokens, heads, dtype=dtype, device=device)
            return wrap_ring_step(slots, lambda s: op(a_log, q_ring[s][:, :, :, 0], beta, dt_bias), retain_outputs=True)
        scale, g_val, b_val = 1.0 / math.sqrt(head_dim), float(OP_CFG["recurrent_gate_init"]), float(OP_CFG["recurrent_beta_init"])
        if chunk_tnd:
            charge_alloc_bytes(context, tokens * heads * (fp32_eb + element_bytes(qkv_name))
                               + heads * head_dim * head_dim * element_bytes(qkv_name))
            seq_lengths = device_values(torch, [tokens], dtype=int32_dt, device=device)
            gated, beta = _filled(torch, (tokens, heads), g_val, dtype=fp32, device=device), _filled(torch, (tokens, heads), b_val, dtype=qkv_dt, device=device)
            state = zeros(torch, 1, heads, head_dim, head_dim, dtype=qkv_dt, device=device)
            return wrap_ring_step(slots, lambda s: op(
                q_ring[s], k_ring[s], v_ring[s], g=gated, beta=beta,
                initial_state=state, actual_seq_lengths=seq_lengths, scale=scale,
            ), retain_outputs=True)
        if recurrent_op:
            rec_lens = device_values(torch, [1] * tokens, dtype=int32_dt, device=device)
            state_idx = device_values(torch, list(range(tokens)), dtype=int32_dt, device=device)
            use_fp32_state = (
                builder == "recurrent_gdn_recover_ssm"
                or str(shape.get("state_dtype") or "").lower() in {"fp32", "float32"}
                or "fp32" in f"{case.get('implementation', '')}:{case.get('op', '')}:{case.get('recipe', '')}".lower()
            )
            state_dt = fp32 if use_fp32_state else qkv_dt
            charge_alloc_bytes(context, tokens * heads * head_dim * head_dim * (fp32_eb if use_fp32_state else 2))
            gated, beta = _filled(torch, (tokens, heads), g_val, dtype=fp32, device=device), _filled(torch, (tokens, heads), b_val, dtype=qkv_dt, device=device)
            state = zeros(torch, tokens, heads, head_dim, head_dim, dtype=state_dt, device=device)
            return wrap_ring_step(slots, lambda s: op(
                q_ring[s], k_ring[s], v_ring[s], state, beta=beta, g=gated,
                actual_seq_lengths=rec_lens, ssm_state_indices=state_idx, scale=scale,
            ), retain_outputs=True)
        g_dims = (1, tokens, heads, head_dim) if kda_shape else (1, tokens, heads)
        charge_alloc_bytes(context, math.prod(g_dims) * fp32_eb + tokens * heads * element_bytes(qkv_name))
        gated, beta = _filled(torch, g_dims, g_val, dtype=fp32, device=device), _filled(torch, (1, tokens, heads), b_val, dtype=dtype, device=device)
        if vllm_kda:
            charge_alloc_bytes(context, heads * head_dim * head_dim * fp32_eb + extra_out * max(2, slots))
            init_h = zeros(torch, 1, heads, head_dim, head_dim, dtype=fp32, device=device)
            return wrap_ring_step(slots, lambda s: op(q_ring[s], k_ring[s], v_ring[s], gated, beta, initial_state=init_h, inplace_final_state=False), retain_outputs=True)
        vllm_chunk_kda = builder == "chunk_kda_fwd" and resolved == "chunk_kda"
        if vllm_chunk_kda:
            charge_alloc_bytes(context, heads * head_dim * head_dim * fp32_eb)
            init_c = zeros(torch, 1, heads, head_dim, head_dim, dtype=fp32, device=device)
            return wrap_ring_step(slots, lambda s: op(q_ring[s], k_ring[s], v_ring[s], gated, beta, initial_state=init_c), retain_outputs=True)
        return wrap_ring_step(slots, lambda s: op(q_ring[s], k_ring[s], v_ring[s], gated, beta), retain_outputs=True)

    return build
