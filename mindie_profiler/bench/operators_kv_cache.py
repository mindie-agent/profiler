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
    shape_of,
    slice_ring_tensors,
    upstream_2d_input,
    upstream_inputs,
    view_upstream_operand,
    wrap_ring_step,
)

_KV_INPUT_MISMATCH = "bench_kv_input_mismatch"
_CACHE_ROW_ALIGNMENT = AdvisorConfig().ub_burst_bytes


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


def build_kv_compress_epilog(
    torch: Any, case: Mapping[str, Any], context: Mapping[str, Any]
) -> Callable[[], Any]:
    op = require_kernel(
        torch, case, context, ("npu_kv_compress_epilog", "kv_compress_epilog"),
        builder="kv_compress_epilog", upstream_abi="aclnnKvCompressEpilog",
    )
    shape, device = shape_of(case), device_of(context)
    tokens, width = dims_2d(case)
    seq_len = max(tokens, dim_int(shape, "seq_len", tokens))
    block_size = _kv_compress_block_size(case, shape)
    block_num = (seq_len + block_size - 1) // block_size

    # CANN uses 64 rotary channels and groups of 64 NoPE channels.
    # Size for the BF16 rotary tail and the larger, two-byte group scale.
    rope_width = int(OP_CFG["mla_rope_dim"])
    nope = max(width, rope_width) - rope_width
    groups = (nope + rope_width - 1) // rope_width
    bf16_bytes = element_bytes("bf16")
    concat_col = nope + (rope_width + groups) * bf16_bytes
    align = _CACHE_ROW_ALIGNMENT
    cache_col = max(width, ((concat_col + align - 1) // align) * align)

    dtype = resolve_case_dtype(torch, case)
    dtype_name = str(case.get("dtype") or "bf16").strip() or "bf16"
    cache_dtype = getattr(torch, UINT8, dtype)
    cache_dtype_name = dtype_name if cache_dtype is dtype else UINT8
    record_actual_shape(context, tokens=tokens, width=width, seq_len=seq_len, dtype=dtype_name)
    cache_shape = (block_num, block_size, 1, cache_col)
    per_slot_bytes = (tokens * width * element_bytes(dtype_name)
                      + math.prod(cache_shape) * element_bytes(cache_dtype_name))
    slots = cold_ring_slot_count(case, context, per_slot_bytes)
    x_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=(tokens, width), dtype=dtype,
        dtype_name=dtype_name, device=device,
    )
    cache_ring = slice_ring_tensors(
        torch, context, num_slots=slots, dims=cache_shape, dtype=cache_dtype,
        dtype_name=cache_dtype_name, device=device, fill_ones=True,
    )
    slot_mapping = device_values(torch, range(tokens), dtype=getattr(torch, INT32, None), device=device)

    def source(slot: int) -> Any:
        return upstream_2d_input(
            context, x_ring[slot], (tokens, width), dtype=dtype, error=_KV_INPUT_MISMATCH,
        )

    return wrap_ring_step(slots, lambda s: op(cache_ring[s], source(s), slot_mapping))


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
    op = require_kernel(
        torch, case, context,
        ("npu_scatter_pa_kv_cache", "npu_reshape_and_cache", "scatter_pa_kv_cache"),
        builder="scatter_pa_kv_cache", upstream_abi="aclnnScatterPaKvCache",
    )
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
    per_slot_bytes = 2 * (math.prod(input_shape) + math.prod(cache_shape)) * element_bytes(dtype_name)
    slots = cold_ring_slot_count(case, context, per_slot_bytes)
    key_ring, value_ring, key_cache_ring, value_cache_ring = (
        slice_ring_tensors(
            torch, context, num_slots=slots, dims=dims, dtype=dtype,
            dtype_name=dtype_name, device=device, fill_ones=True,
        )
        for dims in (input_shape, input_shape, cache_shape, cache_shape)
    )
    slot_mapping = device_values(torch, range(tokens), dtype=getattr(torch, INT32, None), device=device)

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
        key = source(inputs[0]) if inputs else key_ring[slot]
        value = source(inputs[1]) if len(inputs) == 2 else value_ring[slot]
        return op(key, value, key_cache_ring[slot], value_cache_ring[slot], slot_mapping)

    return wrap_ring_step(slots, step)
