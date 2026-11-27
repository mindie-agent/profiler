"""CANN paged KV-cache benchmark builders.

[Role]
  Build the tensor operands for KV compression and paged key/value scatter.

[Invariants]
  * Slot indices are unique and fit within the allocated cache pages.
  * Producer operands are bound in data-edge order using zero-copy views.

[Timeouts & Locks]
  Tensor setup runs outside the timed window. No locks or threads.

[Side-Effect Policy]
  Allocates tensors on the caller-provided device. Kernels update cache tensors
  in place.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from ..events import ProfilerUsageError
from ..profiler_configs import AdvisorConfig
from .operators_common import (
    INT32,
    OP_CFG,
    UINT8,
    cold_ring_slot_count,
    device_of,
    device_values,
    dim_int,
    dims_2d,
    element_bytes,
    record_actual_shape,
    require_kernel,
    resolve_case_dtype,
    resolved_kernel_name,
    shape_of,
    slice_ring_tensors,
    upstream_2d_input,
    upstream_inputs,
    verify_cold_eviction,
    view_upstream_operand,
    wrap_ring_step,
)

_KV_INPUT_MISMATCH = "bench_kv_input_mismatch"
_CACHE_ROW_ALIGNMENT = AdvisorConfig().ub_burst_bytes
_CACHELINE_BYTES = int(OP_CFG["cacheline_bytes"])


def _kv_l2_bytes(context: Mapping[str, Any]) -> int:
    ring = context.get("ring")
    ring_plan = context.get("ring_plan") or (getattr(ring, "plan", None) if ring is not None else None)
    if isinstance(ring_plan, Mapping) and ring_plan.get("l2_bytes"):
        return int(ring_plan["l2_bytes"])
    return int(context.get("l2_bytes") or 0)


def _rotating_slot_mappings(
    torch: Any,
    *,
    num_rotations: int,
    tokens: int,
    total_slots: int,
    row_bytes: int,
    device: str,
) -> list[Any]:
    """Build per-repeat slot_mapping tensors rotating across disjoint cache lines."""
    int32_dt = getattr(torch, INT32, None)
    rows_per_line = max(1, -(-_CACHELINE_BYTES // max(1, int(row_bytes))))
    step = max(int(tokens), rows_per_line)
    mappings: list[Any] = []
    for rot in range(max(1, int(num_rotations))):
        base = (rot * step) % max(1, int(total_slots))
        vals = [(base + idx) % max(1, int(total_slots)) for idx in range(int(tokens))]
        mappings.append(device_values(torch, vals, dtype=int32_dt, device=device))
    return mappings


def _kv_compress_block_size(case: Mapping[str, Any], shape: Mapping[str, Any]) -> int:
    """Resolve KV page size from plan/case ``page_geometry`` without importing ``mindie_sim``."""
    page_geo = case.get("page_geometry")
    if not isinstance(page_geo, Mapping):
        page_geo = shape.get("page_geometry")
    if isinstance(page_geo, Mapping):
        for key in ("page_tokens", "block_size", "kv_kernel_block_size", "kv_allocator_block_size"):
            if page_geo.get(key) is not None:
                return dim_int(page_geo, key, int(OP_CFG["kv_compress_page_tokens_default"]))
    if shape.get("block_size") is not None:
        return dim_int(shape, "block_size", int(OP_CFG["kv_compress_page_tokens_default"]))
    for key in ("kv_kernel_block_size", "kv_allocator_block_size"):
        if case.get(key) is not None:
            return dim_int(case, key, int(OP_CFG["kv_compress_page_tokens_default"]))
    return int(OP_CFG["kv_compress_page_tokens_default"])


def _kv_compress_aligned_dims(tokens: int, width: int) -> tuple[int, int]:
    """Factor 1D flattened ``(tokens, 1)`` KV compress inputs into 64-aligned ``(t, d)``."""
    align = int(OP_CFG["kv_compress_min_align_dim"])
    if width != 1 or tokens < align or tokens % align != 0:
        return tokens, width
    for cand in OP_CFG["kv_compress_width_candidates"]:
        dim = int(cand)
        if tokens >= dim and tokens % dim == 0:
            return max(1, tokens // dim), dim
    return max(1, tokens // align), align


def build_kv_compress_epilog(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, ("npu_kv_compress_epilog", "kv_compress_epilog"),
        builder="kv_compress_epilog", upstream_abi="aclnnKvCompressEpilog",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    eff_tokens, eff_width = _kv_compress_aligned_dims(tokens, width)
    seq_len = max(eff_tokens, dim_int(shape, "seq_len", eff_tokens))
    block_size = _kv_compress_block_size(case, shape)
    block_num = (seq_len + block_size - 1) // block_size

    # CANN uses 64 rotary channels and groups of 64 NoPE channels.
    # Size for the BF16 rotary tail and the larger, two-byte group scale.
    rope_width = int(OP_CFG["mla_rope_dim"])
    nope = max(eff_width, rope_width) - rope_width
    groups = (nope + rope_width - 1) // rope_width
    bf16_bytes = element_bytes("bf16")
    concat_col = nope + (rope_width + groups) * bf16_bytes
    align = _CACHE_ROW_ALIGNMENT
    cache_col = max(eff_width, ((concat_col + align - 1) // align) * align)

    dtype = resolve_case_dtype(torch, case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    cache_dtype = getattr(torch, UINT8, dtype)
    cache_dtype_name = dtype_name if cache_dtype is dtype else UINT8
    record_actual_shape(
        context, tokens=tokens, width=width, seq_len=seq_len, dtype=dtype_name,
        **({"eff_tokens": eff_tokens, "eff_width": eff_width} if eff_width != width else {}),
    )
    cache_shape = (block_num, block_size, 1, cache_col)
    touched_per_repeat = (
        eff_tokens * eff_width * element_bytes(dtype_name)
        + eff_tokens * cache_col * element_bytes(cache_dtype_name)
    )
    alloc_per_slot = (
        eff_tokens * eff_width * element_bytes(dtype_name)
        + math.prod(cache_shape) * element_bytes(cache_dtype_name)
    )
    slots = cold_ring_slot_count(case, context, alloc_per_slot)
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(eff_tokens, eff_width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    cache_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=cache_shape, dtype=cache_dtype,
        dtype_name=cache_dtype_name, device=device, fill_ones=True,
    )
    total_cache_slots = block_num * block_size
    row_bytes = cache_col * element_bytes(cache_dtype_name)
    l2_bytes = _kv_l2_bytes(context)
    is_cold = not bool(context.get("hot")) and (
        bool(case.get("cold_ring")) or bool(getattr(context.get("ring"), "allocated", False))
    )
    rotations = slots
    if is_cold and l2_bytes > 0 and slots == 1:
        max_rot = max(1, total_cache_slots // max(eff_tokens, -(-_CACHELINE_BYTES // max(1, row_bytes))))
        rotations = min(int(OP_CFG["max_ring_slots"]), max_rot)
    slot_mappings = _rotating_slot_mappings(
        torch,
        num_rotations=rotations,
        tokens=eff_tokens,
        total_slots=total_cache_slots,
        row_bytes=row_bytes,
        device=device,
    )
    if isinstance(context, dict) and is_cold:
        has_upstream = bool(upstream_inputs(context))
        cache_write_bytes = eff_tokens * cache_col * element_bytes(cache_dtype_name)
        input_read_bytes = eff_tokens * eff_width * element_bytes(dtype_name)
        distinct_bytes = (
            len(slot_mappings) * cache_write_bytes
            + (1 if has_upstream else slots) * input_read_bytes
        )
        context["_cold_coverage"] = verify_cold_eviction(
            distinct_bytes,
            1,
            l2_bytes,
            explicit_l2_flush=bool(context.get("explicit_l2_flush")),
        )

    def source(slot: int) -> Any:
        return upstream_2d_input(
            context, x_ring[slot % len(x_ring)], (eff_tokens, eff_width), dtype=dtype, error=_KV_INPUT_MISMATCH,
        )

    return wrap_ring_step(
        len(slot_mappings),
        lambda s: op(cache_ring[s % len(cache_ring)], source(s), slot_mappings[s]),
    )


def _scatter_head_dims(shape: Mapping[str, Any], width: int) -> tuple[int, int]:
    try:
        head_dim = int(shape.get("head_dim", width))
    except (TypeError, ValueError, OverflowError):
        return 1, width
    if head_dim <= 0 or width % head_dim:
        return 1, width
    inferred_heads = width // head_dim
    kv_heads = dim_int(shape, "kv_heads", inferred_heads)
    return (kv_heads if kv_heads * head_dim == width else inferred_heads), head_dim


def build_scatter_pa_kv_cache(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    candidates = ("npu_scatter_pa_kv_cache", "npu_reshape_and_cache", "scatter_pa_kv_cache")
    op = require_kernel(
        torch, case, context, candidates,
        builder="scatter_pa_kv_cache", upstream_abi="aclnnScatterPaKvCache",
    )
    resolved = resolved_kernel_name(torch, op, candidates, context)
    use_norm_mode = resolved == "npu_scatter_pa_kv_cache"
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    kv_heads, head_dim = _scatter_head_dims(shape, width)
    block_size = dim_int(shape, "block_size", int(OP_CFG["paged_block_size_default"]))
    num_blocks = (seq_len + block_size - 1) // block_size
    dtype = resolve_case_dtype(torch, case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    record_actual_shape(context, tokens=tokens, width=width, seq_len=seq_len, dtype=dtype_name)

    flat_shape = (tokens, width)
    input_shape = (tokens, kv_heads, head_dim)
    cache_shape = (num_blocks, block_size, kv_heads, head_dim)
    elem_b = element_bytes(dtype_name)
    touched_per_repeat = 2 * (math.prod(input_shape) * 2) * elem_b
    alloc_per_slot = 2 * (math.prod(input_shape) + math.prod(cache_shape)) * elem_b
    slots = cold_ring_slot_count(case, context, alloc_per_slot)
    key_ring, value_ring, key_cache_ring, value_cache_ring = (
        slice_ring_tensors(
            torch, context, num_slots=slots, dims=dims, dtype=dtype,
            dtype_name=dtype_name, device=device, fill_ones=True,
        )
        for dims in (input_shape, input_shape, cache_shape, cache_shape)
    )
    total_cache_slots = num_blocks * block_size
    row_bytes = kv_heads * head_dim * elem_b
    l2_bytes = _kv_l2_bytes(context)
    is_cold = not bool(context.get("hot")) and (
        bool(case.get("cold_ring")) or bool(getattr(context.get("ring"), "allocated", False))
    )
    rotations = slots
    if is_cold and l2_bytes > 0 and slots == 1:
        max_rot = max(1, total_cache_slots // max(tokens, -(-_CACHELINE_BYTES // max(1, row_bytes))))
        rotations = min(int(OP_CFG["max_ring_slots"]), max_rot)
    slot_mappings = _rotating_slot_mappings(
        torch,
        num_rotations=rotations,
        tokens=tokens,
        total_slots=total_cache_slots,
        row_bytes=row_bytes,
        device=device,
    )
    if isinstance(context, dict) and is_cold:
        up = upstream_inputs(context)
        cache_write_bytes = 2 * math.prod(input_shape) * elem_b
        key_read = math.prod(input_shape) * elem_b * (1 if len(up) >= 1 else slots)
        val_read = math.prod(input_shape) * elem_b * (1 if len(up) >= 2 else slots)
        distinct_bytes = len(slot_mappings) * cache_write_bytes + key_read + val_read
        context["_cold_coverage"] = verify_cold_eviction(
            distinct_bytes,
            1,
            l2_bytes,
            explicit_l2_flush=bool(context.get("explicit_l2_flush")),
        )

    def source(output: Any) -> Any:
        flat = view_upstream_operand(
            output, flat_shape, dtype=dtype, error=_KV_INPUT_MISMATCH,
            compatible=lambda dims: dims == (tokens * width,) or (
                len(dims) > 1 and dims[-1] == width and math.prod(dims[:-1]) == tokens
            ),
        )
        return view_upstream_operand(
            flat, input_shape, compatible=lambda dims: dims == flat_shape, error=_KV_INPUT_MISMATCH,
        )

    def step(slot: int) -> Any:
        inputs = upstream_inputs(context)
        if len(inputs) > 2:
            raise ProfilerUsageError(_KV_INPUT_MISMATCH)
        ring_idx = slot % len(key_ring)
        key = source(inputs[0]) if inputs else key_ring[ring_idx]
        value = source(inputs[1]) if len(inputs) == 2 else value_ring[ring_idx]
        if use_norm_mode:
            return op(
                key, value, key_cache_ring[ring_idx], value_cache_ring[ring_idx],
                slot_mappings[slot], cache_mode="Norm",
            )
        return op(key, value, key_cache_ring[ring_idx], value_cache_ring[ring_idx], slot_mappings[slot])

    return wrap_ring_step(len(slot_mappings), step)
