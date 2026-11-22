"""Shared error contracts, kernel resolution and cold-ring helpers for bench ops.

[Role]
  Provide ``BenchUnmodeledOperatorError`` (``UnmodeledCapabilityError``)
  carrying ``mindie-unmodeled-structure-hint/1``, ``inspect.signature``-free
  kernel resolution across ``torch_npu`` / ``torch.ops._C_ascend`` /
  ``cann_ops_transformer`` / ``fla``, and multi-slot cold-ring rotation.

[Invariants]
  * Zero ``inspect.signature`` calls (Iron Rule 4); kernel lookup uses explicit
    namespace attributes only.
  * Missing kernels or missing NPU runtime surfaces raise
    ``BenchUnmodeledOperatorError`` immediately—never ``None`` or composite
    PyTorch fallbacks.
  * Cold-ring builders never catch ``RuntimeError`` to degrade to L2-hot
    tensors; multi-slot rings rotate inputs, weights and outputs per repeat.

[Timeouts & Locks]
  Pure in-memory setup outside the timed window; no locks or threads.

[Side-Effect Policy]
  Allocates tensors only on the caller-provided ``torch`` handle.
"""

from __future__ import annotations

from collections import deque
import importlib
import json
import math
import sys
from typing import Any, Callable, Mapping, Sequence

from ..events import ProfilerUsageError
from .profiles import profile_section

UNMODELED_HINT_SCHEMA = "mindie-unmodeled-structure-hint/1"
OP_CFG = profile_section("operators")
TIMING_CFG = profile_section("timing")

DTYPE_NAMES: dict[str, str] = {
    "bf16": "bfloat16",
    "bfloat16": "bfloat16",
    "fp16": "float16",
    "float16": "float16",
    "fp32": "float32",
    "float32": "float32",
    "int8": "int8",
    "int32": "int32",
    "int64": "int64",
    "uint8": "uint8",
    "bool": "bool",
    "w4a8": "int8",
    "int4": "int8",
    "fp8_e4m3": "int8",
    "mxfp8": "int8",
    "mxfp4": "int8",
}
ELEMENT_BYTES: dict[str, int] = {
    str(key): int(val) for key, val in TIMING_CFG["element_bytes"].items()
}
FLOAT32 = "float32"
BFLOAT16 = "bfloat16"
INT8 = "int8"
INT32 = "int32"
INT64 = "int64"
UINT8 = "uint8"
_FA_COMPRESSED_MASK_DIM = int(OP_CFG["fa_compressed_mask_dim"])
FA_CAUSAL_MASK_SHAPE = (_FA_COMPRESSED_MASK_DIM, _FA_COMPRESSED_MASK_DIM)
FA_CAUSAL_MASK_BYTES = math.prod(FA_CAUSAL_MASK_SHAPE) * ELEMENT_BYTES[UINT8]
FA_CAUSAL_SPARSE_MODE = int(OP_CFG["fa_left_up_causal_sparse_mode"])
_ATTENTION_FLOPS_FACTOR = int(profile_section("sku_microbench")["attention_flops_factor"])
_OPS_NAMESPACES = ("npu", "cann_ops_transformer", "_C_ascend", "vllm", "mindie")


def causal_attention_pairs(query_len: int, kv_len: int) -> int:
    """Count pairs on and below the upper-left causal diagonal."""
    diagonal = min(query_len, kv_len)
    return diagonal * (diagonal + 1) // 2 + (query_len - diagonal) * kv_len


def attention_flops(query_key_pairs: int, heads: int, head_dim: int) -> int:
    return _ATTENTION_FLOPS_FACTOR * heads * query_key_pairs * head_dim


class BenchUnmodeledOperatorError(ProfilerUsageError, ValueError):
    """Hard fail-fast error for unknown builders or missing NPU/fla/Triton ops."""

    def __init__(
        self,
        payload: Mapping[str, Any],
        *,
        code: str = "bench_builder_unavailable",
    ) -> None:
        normalized = dict(payload)
        normalized.setdefault("schema", UNMODELED_HINT_SCHEMA)
        self.payload: dict[str, Any] = normalized
        self.hint: dict[str, Any] = normalized
        self.code = str(code)
        super().__init__(f"{self.code}: {json.dumps(self.payload, sort_keys=True)}")


UnmodeledCapabilityError = BenchUnmodeledOperatorError


def unmodeled_payload(
    case: Mapping[str, Any],
    *,
    builder: str,
    upstream_abi: str,
    reason: str,
    candidates: Sequence[str] = (),
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a schema-conformant ``mindie-unmodeled-structure-hint/1`` dict."""
    shape = shape_of(case)
    ctx_meta = (context or {}).get("_case_meta")
    sources: list[Mapping[str, Any]] = [case]
    for key in ("metadata", "meta"):
        candidate = case.get(key)
        if isinstance(candidate, Mapping):
            sources.append(candidate)
    if isinstance(ctx_meta, Mapping):
        sources.append(ctx_meta)

    def field(key: str, default: Any) -> Any:
        for source in sources:
            value = source.get(key)
            if value is not None and value != "":
                return value
        return default

    raw_dtypes = field("dtypes", ())
    dtypes = (
        [str(item) for item in raw_dtypes]
        if isinstance(raw_dtypes, (list, tuple))
        else [str(field("dtype", ""))]
    )
    raw_ls = field("local_shape", None)
    local_shape = (
        list(raw_ls)
        if isinstance(raw_ls, (list, tuple)) and raw_ls
        else dict(shape)
    )
    try:
        layer_idx = int(field("layer_idx", -1))
    except (TypeError, ValueError):
        layer_idx = -1
    meta = next((item for item in sources if item is not case), {})
    return {
        "schema": UNMODELED_HINT_SCHEMA,
        "builder": str(builder),
        "upstream_abi": str(upstream_abi),
        "reason": str(reason),
        "candidates_checked": [str(item) for item in candidates],
        "model_id": str(field("model_id", "")),
        "layer_idx": layer_idx,
        "family": str(field("family", "")),
        "recipe": str(field("recipe", "")),
        "implementation": str(field("implementation", field("op", ""))),
        "local_shape": local_shape,
        "dtypes": dtypes,
        "metadata": dict(meta) if isinstance(meta, Mapping) else {},
        "agent_action": (
            "inspect upstream kernel ABI in vllm-ascend/cann/fla and register "
            "explicit PhysicalRecipe + bench operator builder"
        ),
    }


def raise_unmodeled(
    case: Mapping[str, Any],
    *,
    builder: str,
    upstream_abi: str,
    reason: str,
    candidates: Sequence[str] = (),
    code: str = "bench_builder_unavailable",
    context: Mapping[str, Any] | None = None,
) -> None:
    """Raise ``BenchUnmodeledOperatorError`` with full structural provenance."""
    raise BenchUnmodeledOperatorError(
        unmodeled_payload(
            case, builder=builder, upstream_abi=upstream_abi,
            reason=reason, candidates=candidates, context=context,
        ),
        code=code,
    )


def has_npu_surface(torch: Any, context: Mapping[str, Any] | None = None) -> bool:
    """Return True when an NPU surface, override table or smoke flag is active."""
    ctx = context or {}
    if ctx.get("allow_cpu_smoke") or ctx.get("op_overrides") or ctx.get("extra_ops"):
        return True
    if ctx.get("torch_npu") is not None or getattr(torch, "npu", None) is not None:
        return True
    ops = getattr(torch, "ops", None)
    return any(getattr(ops, ns, None) is not None for ns in _OPS_NAMESPACES)


def require_npu_surface(
    torch: Any,
    case: Mapping[str, Any],
    context: Mapping[str, Any] | None,
    *,
    builder: str,
    upstream_abi: str,
) -> None:
    """Refuse silent host-CPU execution when no NPU surface is bound."""
    if not has_npu_surface(torch, context):
        raise_unmodeled(
            case, builder=builder, upstream_abi=upstream_abi,
            reason="npu_runtime_surface_unavailable", context=context,
        )


def _lazy_module(name: str, context: Mapping[str, Any] | None) -> Any:
    ctx = context or {}
    modules = ctx.get("extra_modules")
    if isinstance(modules, Mapping) and name in modules:
        return modules[name]
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    if not has_npu_surface(ctx.get("torch"), ctx):
        return None
    try:
        return importlib.import_module(name)
    except TimeoutError:
        raise
    except Exception:
        return None


def resolve_op(
    torch: Any,
    name: str,
    *,
    context: Mapping[str, Any] | None = None,
    extra_modules: Sequence[str] = (),
    allow_torch_attr: bool = True,
) -> Any:
    """Resolve one operator packet without ``inspect.signature``."""
    ctx = context or {}
    for table_key in ("op_overrides", "extra_ops"):
        overrides = ctx.get(table_key)
        if isinstance(overrides, Mapping) and callable(overrides.get(name)):
            return overrides[name]
    for holder in (ctx.get("torch_npu"), sys.modules.get("torch_npu"), getattr(torch, "npu", None)):
        candidate = getattr(holder, name, None) if holder is not None else None
        if callable(candidate):
            return candidate
    ops = getattr(torch, "ops", None)
    for ns in _OPS_NAMESPACES:
        container = getattr(ops, ns, None) if ops is not None else None
        candidate = getattr(container, name, None) if container is not None else None
        if callable(candidate):
            return candidate
    for mod_name in ("cann_ops_transformer", *extra_modules):
        mod = _lazy_module(mod_name, {**ctx, "torch": torch})
        candidate = getattr(mod, name, None) if mod is not None else None
        if callable(candidate):
            return candidate
    if allow_torch_attr:
        direct = getattr(torch, name, None)
        if callable(direct):
            return direct
    return None


def resolved_kernel_name(
    torch: Any, op: Any, candidates: Sequence[str], context: Mapping[str, Any]
) -> str:
    """Resolve the candidate alias that produced the kernel."""
    declared = str(getattr(op, "__name__", "") or "")
    if declared.startswith("npu_") or declared in candidates:
        return declared
    for name in candidates:
        if resolve_op(torch, name, context=context, allow_torch_attr=False) is op:
            return name
    return declared


def require_kernel(
    torch: Any,
    case: Mapping[str, Any],
    context: Mapping[str, Any] | None,
    candidates: Sequence[str],
    *,
    builder: str,
    upstream_abi: str,
    extra_modules: Sequence[str] = (),
) -> Callable[..., Any]:
    """Resolve the first installed fused kernel or raise fail-fast."""
    require_npu_surface(torch, case, context, builder=builder, upstream_abi=upstream_abi)
    ctx = context or {}
    for table_key in ("op_overrides", "extra_ops"):
        overrides = ctx.get(table_key)
        if isinstance(overrides, Mapping) and callable(overrides.get(builder)):
            return overrides[builder]
    for name in candidates:
        op = resolve_op(
            torch, name, context=context, extra_modules=extra_modules, allow_torch_attr=False
        )
        if callable(op):
            return op
    raise_unmodeled(
        case,
        builder=builder,
        upstream_abi=upstream_abi,
        reason=f"missing_kernel:{candidates[0] if candidates else upstream_abi}",
        candidates=candidates,
        context=context,
    )
    raise AssertionError("unreachable")


def torch_dtype(torch: Any, name: Any) -> Any:
    mapped = DTYPE_NAMES.get(str(name or "").strip().lower())
    return getattr(torch, mapped, None) if mapped is not None else None


def element_bytes(dtype: Any) -> int:
    return ELEMENT_BYTES.get(str(dtype or "").strip().lower(), 2)


def device_of(context: Mapping[str, Any]) -> str:
    ordinal = ((context or {}).get("device") or {}).get("ordinal", 0)
    return f"npu:{int(ordinal)}"


def shape_of(case: Mapping[str, Any]) -> Mapping[str, Any]:
    raw = case.get("shape")
    return raw if isinstance(raw, Mapping) else {}


def record_actual_shape(context: Mapping[str, Any], **dims: Any) -> None:
    """Report resolved operand dimensions to a caller collecting shape evidence."""
    actual = context.get("_actual_shape")
    if isinstance(actual, dict):
        actual.update(dims)
        node_id = context.get("_active_node_id")
        if node_id:
            node_shapes = actual.setdefault("node_shapes", {})
            if isinstance(node_shapes, dict):
                node_shapes.setdefault(str(node_id), {}).update(dims)


_DISPATCH_DIMENSIONS = frozenset({
    "m", "n", "k", "e", "tokens", "width", "heads", "kv_heads", "head_dim",
    "top_k", "topk", "sparse_count", "group_size", "bytes", "nbytes",
})


def shape_evidence_problem(requested: Mapping[str, Any], actual: Mapping[str, Any]) -> str | None:
    """Reject conflicting geometry and missing declared dispatch dimensions."""
    shared = requested.keys() & actual.keys()
    if any(requested[key] != actual[key] for key in shared):
        return "mismatch"
    if requested and (not shared or _DISPATCH_DIMENSIONS.intersection(requested.keys() - shared)):
        return "missing"
    return None


def dim_int(shape: Mapping[str, Any], key: str, default: int = 1) -> int:
    try:
        value = shape.get(key, default)
        return max(1, int(default if value is None else value))
    except (TypeError, ValueError):
        return max(1, int(default))


def dims_2d(
    case: Mapping[str, Any],
    shape: Mapping[str, Any] | None = None,
    *,
    default_width: int | None = None,
) -> tuple[int, int]:
    """Extract ``(tokens, width)`` while reshaping 1D flattened shapes safely."""
    shp = shape if shape is not None else shape_of(case)
    fallback_w = int(default_width or OP_CFG["attention_head_dim"])
    local = case.get("local_shape")
    if isinstance(local, (list, tuple)) and len(local) == 1:
        total = max(1, int(local[0]))
        width = min(total, fallback_w)
        return max(1, total // width), width
    tokens = dim_int(shp, "tokens", 1)
    width = dim_int(shp, "width", fallback_w)
    threshold = int(OP_CFG["dims_1d_split_threshold"])
    if tokens == width and tokens > threshold and "m" not in shp:
        capped = min(tokens, fallback_w)
        return max(1, tokens // capped), capped
    return tokens, width


def resolve_case_dtype(torch: Any, case: Mapping[str, Any], default: str = "bf16") -> Any:
    raw = str(case.get("dtype") or default).strip() or default
    resolved = torch_dtype(torch, raw)
    if resolved is None:
        raise ProfilerUsageError(f"bench_dtype_unavailable: {raw!r} is not installed")
    return resolved


def zeros(torch: Any, *dims: int, dtype: Any = None, device: str) -> Any:
    return torch.zeros(*dims, dtype=dtype, device=device)


def ones(torch: Any, *dims: int, dtype: Any = None, device: str) -> Any:
    factory = getattr(torch, "ones", None)
    return factory(*dims, dtype=dtype, device=device) if callable(factory) else zeros(
        torch, *dims, dtype=dtype, device=device
    )


def randn(torch: Any, *dims: int, dtype: Any = None, device: str) -> Any:
    factory = getattr(torch, "randn", None) or getattr(torch, "ones", None)
    return factory(*dims, dtype=dtype, device=device) if callable(factory) else zeros(
        torch, *dims, dtype=dtype, device=device
    )


def upstream_inputs(context: Mapping[str, Any]) -> Sequence[Any]:
    """Return the current producer outputs in data-edge order."""
    ctx = context or {}
    live = ctx.get("_live_inputs")
    inputs = live.get("tensors") if isinstance(live, Mapping) else None
    return inputs or ctx.get("_node_inputs") or ()


def upstream_input(
    case: Mapping[str, Any], context: Mapping[str, Any], expected_elements: int | None = None
) -> Any:
    inputs = upstream_inputs(context)
    if not inputs:
        return None
    candidate = inputs[0]
    if expected_elements is None:
        return candidate
    numel = getattr(candidate, "numel", None)
    return candidate if (callable(numel) and int(numel()) == expected_elements) else None


def view_upstream_operand(
    output: Any,
    target: tuple[int, ...],
    *,
    compatible: Callable[[tuple[int, ...]], bool],
    error: str,
) -> Any:
    """Validate a producer's primary tensor and adapt its shape without copying."""
    tensor = output[0] if isinstance(output, (tuple, list)) and output else output
    try:
        shape = tuple(tensor.shape)
        if shape == target:
            return tensor
        if compatible(shape):
            return tensor.view(*target)
    except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
        raise ProfilerUsageError(error) from exc
    raise ProfilerUsageError(error)


def rotary_query_input(
    context: Mapping[str, Any], fallback: Any, shape: tuple[int, int, int, int]
) -> Any:
    inputs = upstream_inputs(context)
    if not inputs:
        return fallback
    if len(inputs) != 1:
        raise ProfilerUsageError("bench_rotary_query_count_mismatch")
    _, tokens, heads, head_dim = shape
    return view_upstream_operand(
        inputs[0], shape,
        compatible=lambda dims: len(dims[1:]) in (1, 2)
        and dims[0] == tokens and math.prod(dims[1:]) == heads * head_dim,
        error="bench_rotary_query_shape_mismatch",
    )


def device_values(torch: Any, values: Sequence[int], *, dtype: Any, device: str) -> Any:
    """Build a device tensor of ``values``, or a zeros fallback on fake handles."""
    items = list(values)
    factory = getattr(torch, "tensor", None)
    if callable(factory):
        return factory(items, dtype=dtype, device=device)
    dims = (len(items), len(items[0])) if items and isinstance(
        items[0], (list, tuple)) else (len(items),)
    return zeros(torch, *dims, dtype=dtype, device=device)


def _arena_get(arena: Any, key: str, default: Any = None) -> Any:
    return arena.get(key, default) if isinstance(arena, dict) else default


def _aligned_bytes(nbytes: int) -> int:
    cacheline = int(OP_CFG["cacheline_bytes"])
    return -(-max(1, int(nbytes)) // cacheline) * cacheline


def _invocation_stride(arena: Any, ring: Any, per_call_bytes: int) -> int:
    cacheline = int(OP_CFG["cacheline_bytes"])
    pad = int(OP_CFG["sub_offset_pad_cachelines"]) * cacheline
    recorded = int(_arena_get(arena, "inv_stride", 0) or 0)
    if recorded > 0:
        return recorded
    ring_stride = int(ring.plan["slot_stride_bytes"]) if ring is not None else 0
    return _aligned_bytes(max(ring_stride, int(per_call_bytes) + pad))


def _ring_allocated_bytes(ring: Any) -> int:
    if ring is None or not bool(getattr(ring, "allocated", False)):
        return 0
    recorded = getattr(ring, "allocated_bytes", None)
    if isinstance(recorded, int) and not isinstance(recorded, bool):
        return int(recorded)
    return int((getattr(ring, "plan", None) or {}).get("total_bytes") or 0)


def _byte_ledger(context: Mapping[str, Any]) -> dict[str, Any] | None:
    """Return the per-case allocation ledger, seeding it with live ring bytes."""
    if not isinstance(context, dict):
        return None
    ledger = context.get("_byte_ledger")
    if not isinstance(ledger, dict):
        allocated = _ring_allocated_bytes(context.get("ring"))
        ledger = {"persistent_bytes": allocated, "peak_bytes": allocated}
        context["_byte_ledger"] = ledger
    return ledger


def _account_alloc_bytes(
    ledger: dict[str, Any] | None, nbytes: int, *, cap: int, over_budget_reason: str,
    workspace_bytes: int = 0, charge: bool = False,
) -> int:
    current = ledger or {}
    previous_peak = int(current.get("peak_bytes") or 0)
    # A ledger seeded with only a peak starts with persistent ring bytes.
    persistent_bytes = int(current.get("persistent_bytes", previous_peak)) + max(0, int(nbytes))
    # Cold and hot inputs coexist while their provider calls execute in sequence.
    max_workspace_bytes = max(int(current.get("max_workspace_bytes") or 0), workspace_bytes)
    peak_bytes = persistent_bytes + max_workspace_bytes
    if cap > 0 and peak_bytes > cap:
        raise ProfilerUsageError(f"bench_vram_budget_exceeded: {over_budget_reason}")
    if charge and ledger is not None:
        ledger.update(
            persistent_bytes=persistent_bytes,
            max_workspace_bytes=max_workspace_bytes,
            peak_bytes=max(previous_peak, peak_bytes),
        )
    return peak_bytes


def check_alloc_bytes(
    context: Mapping[str, Any], nbytes: int, *, reason: str = "operand buffers", workspace_bytes: int = 0,
) -> int:
    """Check prospective peak bytes against the S0 cap without charging them."""
    cap = int((context.get("budget") or {}).get("cap_bytes") or 0)
    return _account_alloc_bytes(
        _byte_ledger(context), nbytes, cap=cap, workspace_bytes=workspace_bytes,
        over_budget_reason=f"{reason} exceed S0 cap",
    )


def charge_alloc_bytes(
    context: Mapping[str, Any], nbytes: int, *, reason: str = "operand buffers", workspace_bytes: int = 0,
) -> None:
    """Charge persistent bytes and reserve the maximum sequential workspace."""
    cap = int((context.get("budget") or {}).get("cap_bytes") or 0)
    _account_alloc_bytes(
        _byte_ledger(context), nbytes, cap=cap, workspace_bytes=workspace_bytes, charge=True,
        over_budget_reason=f"{reason} exceed S0 cap",
    )


def cold_ring_slot_count(
    case: Mapping[str, Any], context: Mapping[str, Any], per_call_bytes: int
) -> int:
    """Compute multi-slot ring length ``>= 3 x L2`` (or ``1`` when ``hot``)."""
    ctx = context or {}
    arena = ctx.get("_ring_arena")
    if isinstance(arena, dict):
        arena["invocation_bytes"] = max(
            int(arena.get("invocation_bytes") or 0), int(per_call_bytes)
        )
    if ctx.get("hot"):
        return 1
    ring = ctx.get("ring")
    active = bool(case.get("cold_ring")) or (
        ring is not None and bool(getattr(ring, "allocated", False))
    )
    if not active:
        return 1
    ring_plan = ctx.get("ring_plan") or (getattr(ring, "plan", None) if ring is not None else None)
    required = int(
        (ring_plan or {}).get("required_bytes")
        or case.get("cold_ring_bytes")
        or OP_CFG["default_cold_ring_bytes"]
    )
    touched = max(int(OP_CFG["cacheline_bytes"]), int(per_call_bytes))
    slots_wanted = max(2, -(-required // touched))
    slots = min(int(OP_CFG["max_ring_slots"]), slots_wanted)
    cap = int((ctx.get("budget") or {}).get("cap_bytes") or 0)
    ring_total = int(
        (getattr(ring, "plan", None) or {}).get("total_bytes")
        or (ring_plan or {}).get("total_bytes")
        or 0
    )
    ring_reserved = (
        ring_total if ring is not None and bool(getattr(ring, "allocated", False)) else 0
    )
    if cap > 0 and touched * 2 + ring_reserved > cap:
        raise ProfilerUsageError(
            "bench_vram_budget_exceeded: multi-slot cold ring exceeds S0 cap"
        )
    if cap > 0:
        slots = min(slots, max(2, (cap - ring_reserved) // touched))
    if ring is not None and bool(getattr(ring, "allocated", False)):
        inv_stride = _invocation_stride(arena, ring, int(per_call_bytes))
        max_fit = ring_total // inv_stride
        if isinstance(arena, dict):
            arena["inv_stride"] = inv_stride
            arena["max_ring_fit"] = max_fit
        if max_fit >= 2:
            slots = min(int(OP_CFG["max_ring_slots"]), max_fit, slots_wanted)
            if cap > 0:
                slots = min(slots, max(2, (cap - ring_reserved) // inv_stride))
    if isinstance(ctx, dict):
        ctx["_cold_coverage"] = {
            "touched_bytes": slots * touched,
            "required_bytes": required,
            "qualified": bool(slots * touched >= required),
        }
    return slots


def slice_ring_tensors(
    torch: Any,
    context: Mapping[str, Any],
    *,
    num_slots: int,
    dims: Sequence[int],
    dtype: Any,
    dtype_name: str,
    device: str,
    fill_ones: bool = False,
) -> list[Any]:
    """Slice typed, non-aliasing slot views from ``ColdRing`` or allocate buffers."""
    ctx = context or {}
    hot = bool(ctx.get("hot"))
    count = 1 if hot else max(1, int(num_slots))
    elements = max(1, math.prod(max(1, int(d)) for d in dims))
    nbytes = elements * element_bytes(dtype_name)
    ring = ctx.get("ring")
    arena = ctx.get("_ring_arena")
    maker = ones if fill_ones else randn
    cap = int((ctx.get("budget") or {}).get("cap_bytes") or 0)

    def fallback_alloc() -> list[Any]:
        tensors: list[Any] = []
        for _ in range(count):
            charge_alloc_bytes(ctx, nbytes, reason="disjoint operand buffers")
            tensors.append(maker(torch, *dims, dtype=dtype, device=device))
        return tensors

    if not (ring is not None and bool(getattr(ring, "allocated", False))):
        return fallback_alloc()

    def shape_slice(sliced: Any, fallback: bool) -> Any:
        if fallback:
            raise ProfilerUsageError(
                "bench_cold_ring_view_unavailable: ColdRing backing lacks narrow/view"
            )
        viewer = getattr(sliced, "view", None)
        shaped = viewer(*dims) if callable(viewer) else sliced
        if fill_ones and callable(getattr(shaped, "fill_", None)):
            shaped.fill_(1)
        return shaped

    aligned = _aligned_bytes(nbytes)
    sub_offset = int(_arena_get(arena, "sub_offset", 0) or 0)
    if hot:
        invocation = int(_arena_get(arena, "invocation_bytes", nbytes) or nbytes)
        reserve = _invocation_stride(arena, ring, invocation)
        sliced, receipt = ring.slice_hot(
            nbytes, offset_bytes=sub_offset, dtype=dtype, reserve_bytes=reserve,
            ledger=_byte_ledger(ctx), cap_bytes=cap,
        )
        if isinstance(arena, dict):
            arena["sub_offset"] = sub_offset + aligned
        return [shape_slice(sliced, bool(receipt.get("view_fallback")))]

    inv_stride = _invocation_stride(arena, ring, nbytes)
    max_fit = int(_arena_get(arena, "max_ring_fit", 0) or 0)
    if max_fit <= 0:
        max_fit = int(ring.plan["total_bytes"]) // inv_stride
    if max_fit >= count and sub_offset + aligned <= inv_stride and isinstance(arena, dict):
        if arena.get("base_slot") is None:
            arena["base_slot"] = int(ring.rotate()["slot_index"]) % max_fit
        base_slot = int(arena["base_slot"])
        tensors: list[Any] = []
        for slot in range(count):
            block = (base_slot + slot) % max_fit
            offset = block * inv_stride + sub_offset
            sliced, receipt = ring.slice_at(
                offset, nbytes, dtype=dtype, slot_index=block
            )
            tensors.append(shape_slice(sliced, bool(receipt.get("view_fallback"))))
        arena["sub_offset"] = sub_offset + aligned
        return tensors
    return fallback_alloc()


def cast_weight_nz(
    torch: Any,
    weight: Any,
    context: Mapping[str, Any] | None,
    *,
    case: Mapping[str, Any] | None = None,
    builder: str = "matmul",
    required: bool = False,
) -> Any:
    """Cast weights to ``ACL_FORMAT_FRACTAL_NZ`` (29) on NPU when available."""
    cast_op = resolve_op(torch, "npu_format_cast", context=context, allow_torch_attr=False)
    code = int((case or {}).get("format_code") or OP_CFG["nz_format_code"])
    allow_cpu_smoke = bool((context or {}).get("allow_cpu_smoke"))
    if callable(cast_op):
        return cast_op(weight, code)
    if required and not allow_cpu_smoke:
        raise_unmodeled(
            case or {},
            builder=builder,
            upstream_abi="npu_format_cast",
            reason="missing_kernel:npu_format_cast",
            candidates=("npu_format_cast",),
            context=context,
        )
    return weight


def wrap_ring_step(
    num_slots: int,
    step_fn: Callable[[int], Any],
    *,
    retain_outputs: bool = False,
) -> Callable[[], Any]:
    """Rotate ``slot = idx % num_slots`` per repeat and pin ``num_slots - 1`` outputs."""
    fifo: deque[Any] | None = (
        deque(maxlen=num_slots - 1) if retain_outputs and num_slots > 1 else None
    )
    cursor = [0]

    def invoke() -> Any:
        slot = cursor[0] % max(1, num_slots)
        cursor[0] += 1
        out = step_fn(slot)
        if fifo is not None:
            fifo.append(out)
        return out

    return invoke


__all__ = [
    "BFLOAT16", "BenchUnmodeledOperatorError", "DTYPE_NAMES", "ELEMENT_BYTES",
    "FLOAT32", "INT8", "INT32", "INT64", "OP_CFG", "UINT8",
    "UNMODELED_HINT_SCHEMA", "UnmodeledCapabilityError", "cast_weight_nz",
    "charge_alloc_bytes", "cold_ring_slot_count", "device_of", "device_values",
    "dim_int", "dims_2d", "element_bytes",
    "has_npu_surface", "ones", "raise_unmodeled", "randn", "require_kernel",
    "require_npu_surface", "resolve_case_dtype", "resolve_op", "resolved_kernel_name",
    "rotary_query_input", "shape_of",
    "slice_ring_tensors", "torch_dtype", "unmodeled_payload", "upstream_input",
    "upstream_inputs", "view_upstream_operand", "wrap_ring_step", "zeros",
]
