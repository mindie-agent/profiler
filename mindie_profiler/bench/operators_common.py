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
_OPS_NAMESPACES = ("npu", "cann_ops_transformer", "_C_ascend", "vllm", "mindie")


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
) -> dict[str, Any]:
    """Build a schema-conformant ``mindie-unmodeled-structure-hint/1`` dict."""
    shape = shape_of(case)
    raw_dtypes = case.get("dtypes")
    dtypes = (
        [str(item) for item in raw_dtypes]
        if isinstance(raw_dtypes, (list, tuple))
        else [str(case.get("dtype") or "")]
    )
    meta = case.get("metadata")
    return {
        "schema": UNMODELED_HINT_SCHEMA,
        "builder": str(builder),
        "upstream_abi": str(upstream_abi),
        "reason": str(reason),
        "candidates_checked": [str(item) for item in candidates],
        "model_id": str(case.get("model_id") or ""),
        "layer_idx": int(case.get("layer_idx", -1)),
        "family": str(case.get("family") or ""),
        "recipe": str(case.get("recipe") or ""),
        "implementation": str(case.get("implementation") or case.get("op") or ""),
        "local_shape": list(case.get("local_shape") or ()) or dict(shape),
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
) -> None:
    """Raise ``BenchUnmodeledOperatorError`` with full structural provenance."""
    raise BenchUnmodeledOperatorError(
        unmodeled_payload(
            case, builder=builder, upstream_abi=upstream_abi,
            reason=reason, candidates=candidates,
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
            reason="npu_runtime_surface_unavailable",
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


def upstream_input(
    case: Mapping[str, Any], context: Mapping[str, Any], expected_elements: int | None = None
) -> Any:
    inputs = (context or {}).get("_node_inputs") or ()
    if not inputs:
        return None
    candidate = inputs[0]
    if expected_elements is None:
        return candidate
    numel = getattr(candidate, "numel", None)
    return candidate if (callable(numel) and int(numel()) == expected_elements) else None


def cold_ring_slot_count(
    case: Mapping[str, Any], context: Mapping[str, Any], per_call_bytes: int
) -> int:
    """Compute multi-slot ring length ``>= 3 x L2`` (or ``1`` when ``hot``)."""
    ctx = context or {}
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
    footprint = max(int(OP_CFG["cacheline_bytes"]), int(per_call_bytes))
    needed = -(-required // footprint)
    slots = max(2, min(int(OP_CFG["max_ring_slots"]), needed))
    cap = int((ctx.get("budget") or {}).get("cap_bytes") or 0)
    ring_reserved = (
        int((ring_plan or {}).get("total_bytes") or 0)
        if ring is not None and bool(getattr(ring, "allocated", False))
        else 0
    )
    if cap > 0 and footprint * 2 + ring_reserved > cap:
        raise ProfilerUsageError(
            "bench_vram_budget_exceeded: multi-slot cold ring exceeds S0 cap"
        )
    if cap > 0:
        slots = min(slots, max(2, (cap - ring_reserved) // footprint))
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
    """Slice typed slot views from ``ColdRing`` or allocate distinct slot buffers."""
    ctx = context or {}
    hot = bool(ctx.get("hot"))
    count = 1 if hot else max(1, int(num_slots))
    elements = max(1, math.prod(max(1, int(d)) for d in dims))
    nbytes = elements * element_bytes(dtype_name)
    ring = ctx.get("ring")
    if ring is not None and bool(getattr(ring, "allocated", False)):
        stride = int(ring.plan["slot_stride_bytes"])
        if 0 < nbytes <= stride:
            tensors: list[Any] = []
            for _ in range(count):
                sliced, receipt = ring.slice_bytes(nbytes, hot=hot, dtype=dtype)
                if receipt.get("view_fallback"):
                    raise ProfilerUsageError(
                        "bench_cold_ring_view_unavailable: ColdRing backing lacks narrow/view"
                    )
                viewer = getattr(sliced, "view", None)
                shaped = viewer(*dims) if callable(viewer) else sliced
                if fill_ones and callable(getattr(shaped, "fill_", None)):
                    shaped.fill_(1)
                tensors.append(shaped)
            return tensors
    maker = ones if fill_ones else randn
    return [maker(torch, *dims, dtype=dtype, device=device) for _ in range(count)]


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
    if callable(cast_op):
        return cast_op(weight, code)
    if required:
        raise_unmodeled(
            case or {},
            builder=builder,
            upstream_abi="npu_format_cast",
            reason="missing_kernel:npu_format_cast",
            candidates=("npu_format_cast",),
        )
    return weight


def wrap_ring_step(
    num_slots: int,
    step_fn: Callable[[int], Any],
    *,
    retain_outputs: bool = False,
) -> Callable[[], Any]:
    """Rotate ``slot = idx % num_slots`` per repeat and pin ``num_slots - 1`` outputs."""
    fifo: deque[Any] | None = None
    if retain_outputs and num_slots > 1:
        fifo = deque(maxlen=num_slots - 1)
        for warm_idx in range(num_slots - 1):
            fifo.append(step_fn(warm_idx))
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
    "cold_ring_slot_count", "device_of", "dim_int", "dims_2d", "element_bytes",
    "has_npu_surface", "ones", "raise_unmodeled", "randn", "require_kernel",
    "require_npu_surface", "resolve_case_dtype", "resolve_op", "shape_of",
    "slice_ring_tensors", "torch_dtype", "unmodeled_payload", "upstream_input",
    "wrap_ring_step", "zeros",
]
