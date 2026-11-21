"""Cold-ring buffer, clock-lock warmup and admitted context helpers for bench.

[Role]
  Own ``ColdRing`` (cacheline-disjoint ``>= 3x L2`` device buffer with narrowed
  typed slice views), ``lock_clock``, ``make_blocker_unit_op``,
  ``admit_context`` and ``close_context``.

[Invariants]
  * ``ColdRing.slice_bytes`` always narrows ``(0, offset, size)`` first and
    calls ``sliced.view(dtype)`` on the narrowed slice—never ``self._buffer``.
  * ``admit_context`` enforces ``require_device_timing()`` so ``host_fallback``
    fails closed unless ``allow_cpu_smoke=True`` is explicitly passed.

[Timeouts & Locks]
  Single-shot setup outside timed windows; no locks or threads.

[Side-Effect Policy]
  Allocates and releases device buffers on the caller-supplied ``torch``.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import bind_device, measure_memory, vram_budget
from .operators_common import _account_alloc_bytes
from .profiles import profile_section

CONTEXT_SCHEMA = "mindie-bench-context/1"
RING_SCHEMA = "mindie-bench-cold-ring/1"
_UNITS = profile_section("units")
_CFG = profile_section("timing")

MIB = int(_UNITS["mib"])
HZ_PER_MHZ = int(_UNITS["hz_per_mhz"])
CACHELINE_BYTES = int(_CFG["cacheline_bytes"])
GEMM_LOCK_SIZE = int(_CFG["gemm_lock_size"])
GEMM_LOCK_REPEATS = int(_CFG["gemm_lock_repeats"])
BLOCKER_UNIT_SIZE = int(_CFG["blocker_unit_size"])
L2_RING_MULTIPLE = int(_CFG["l2_ring_multiple"])
DEFAULT_SLOT_BYTES = int(_CFG["default_slot_bytes"])
_ROUND_US = int(_CFG["round_us_digits"])
_MAX_CLOCK_HZ = float(_CFG["max_clock_hz"])
BF16_ELEMENT_BYTES = 2
HOT_CONTROL_OFFSET = 0


def _pos_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return int(value)


def resolve_l2_bytes(
    l2_bytes: Any = None,
    *,
    sku: str | None = None,
    torch_npu: Any = None,
    ordinal: int = 0,
) -> int | None:
    """Resolve one die's L2 size from the caller, the device or the SKU table."""
    explicit = _pos_int(l2_bytes)
    if explicit is not None:
        return explicit
    getter = getattr(torch_npu, "get_device_properties", None) if torch_npu is not None else None
    if callable(getter):
        try:
            props = getter(int(ordinal))
        except TimeoutError:
            raise
        except Exception:
            props = None
        for attr in ("L2_cache_size", "l2_cache_size"):
            observed = _pos_int(getattr(props, attr, None))
            if observed is not None:
                return observed
    table = _CFG.get("sku_l2_bytes") or {}
    return _pos_int(table.get(str(sku or "")))


def cold_ring_plan(l2_bytes: Any, *, slot_bytes: int = DEFAULT_SLOT_BYTES) -> dict[str, Any]:
    """Plan ``ceil(3 * L2 / slot)`` cacheline-disjoint slots plus a hot control."""
    size = _pos_int(l2_bytes)
    slot = _pos_int(slot_bytes)
    if size is None:
        raise ProfilerUsageError(
            "bench_l2_unknown: the cold ring needs an explicit L2-per-die size "
            "(--l2-mib or an exposed device property); it is never assumed"
        )
    if slot is None:
        raise ProfilerUsageError("bench_cold_ring_slot_invalid: slot bytes must be positive")
    slots = -(-L2_RING_MULTIPLE * size // slot)
    stride = -(-slot // CACHELINE_BYTES) * CACHELINE_BYTES
    required = L2_RING_MULTIPLE * size
    total = slots * stride
    return {
        "schema": RING_SCHEMA,
        "l2_bytes": size,
        "l2_mib": round(size / MIB, _ROUND_US),
        "slot_bytes": slot,
        "slot_stride_bytes": stride,
        "slots": slots,
        "total_bytes": total,
        "total_mib": round(total / MIB, _ROUND_US),
        "required_bytes": required,
        "required_mib": round(required / MIB, _ROUND_US),
        "cacheline_bytes": CACHELINE_BYTES,
        "disjoint_cacheline": stride >= CACHELINE_BYTES and stride % CACHELINE_BYTES == 0,
        "rule": "slots = ceil(3 * L2_per_die / slot_bytes)",
        "hot_control": {
            "slots": 1,
            "offset_bytes": HOT_CONTROL_OFFSET,
            "reuses_same_address": True,
            "label": "hot_control",
            "purpose": "same-address reuse control for the cold ring",
        },
    }


class ColdRing:
    """One device allocation rotated over cacheline-disjoint cold slots."""

    def __init__(self, torch: Any, plan: Mapping[str, Any], *, ordinal: int) -> None:
        self.torch = torch
        self.plan = dict(plan)
        self.ordinal = int(ordinal)
        self._buffer = None
        self._hot_buffer = None
        self._hot_capacity = 0
        self._slot = 0
        self._rotations = 0
        self._precycled = 0
        self._hot_calls = 0

    def allocate(self) -> "ColdRing":
        total = int(self.plan["total_bytes"])
        self._buffer = self.torch.empty(
            total, dtype=self.torch.uint8, device=f"npu:{self.ordinal}"
        )
        zero_ = getattr(self._buffer, "zero_", None)
        if callable(zero_):
            zero_()
        return self

    @property
    def allocated(self) -> bool:
        return self._buffer is not None

    @property
    def allocated_bytes(self) -> int:
        """Total live device bytes owned by this ring, including the hot control."""
        total = int(self.plan["total_bytes"]) if self._buffer is not None else 0
        return total + (int(self._hot_capacity) if self._hot_buffer is not None else 0)

    @property
    def offset_bytes(self) -> int:
        return (self._slot % int(self.plan["slots"])) * int(self.plan["slot_stride_bytes"])

    def rotate(self) -> dict[str, Any]:
        slots = int(self.plan["slots"])
        stride = int(self.plan["slot_stride_bytes"])
        index = self._slot % slots
        self._slot = (self._slot + 1) % slots
        self._rotations += 1
        return {
            "slot_index": index,
            "offset_bytes": index * stride,
            "reuse_distance_slots": slots,
            "kind": "cold_ring",
        }

    def precycle(self, repeats: int) -> dict[str, Any]:
        slots = int(self.plan["slots"])
        count = max(0, int(repeats))
        if count and slots > count:
            advance = slots - count
            self._slot = (self._slot + advance) % slots
            self._precycled += advance
        return {"precycled_slots": self._precycled, "slots": slots, "repeats": count}

    def hot(self) -> dict[str, Any]:
        return {
            "slot_index": 0,
            "offset_bytes": HOT_CONTROL_OFFSET,
            "reuse_distance_slots": 0,
            "kind": "hot_control",
        }

    def _view(
        self, backing: Any, offset: int, size: int, dtype: Any
    ) -> tuple[Any, bool]:
        narrow = getattr(backing, "narrow", None)
        if not callable(narrow):
            if dtype is not None:
                raise ProfilerUsageError("bench_cold_ring_view_unavailable")
            return backing, True
        sliced = narrow(0, int(offset), int(size))
        if dtype is not None:
            sliced_view = getattr(sliced, "view", None)
            if not callable(sliced_view):
                raise ProfilerUsageError("bench_cold_ring_view_unavailable")
            sliced = sliced_view(dtype)
        return sliced, False

    def slice_at(
        self,
        offset_bytes: int,
        nbytes: int,
        *,
        dtype: Any = None,
        slot_index: int | None = None,
    ) -> tuple[Any, dict[str, Any]]:
        """Return one exact byte range inside the cold ring without rotating."""
        if self._buffer is None:
            raise ProfilerUsageError("bench_cold_ring_not_allocated")
        size = _pos_int(nbytes)
        offset = int(offset_bytes)
        if size is None or offset < 0 or offset + size > int(self.plan["total_bytes"]):
            raise ProfilerUsageError("bench_cold_ring_slice_invalid")
        sliced, fallback = self._view(self._buffer, offset, size, dtype)
        return sliced, {
            "slot_index": (
                int(slot_index) if slot_index is not None
                else offset // max(1, int(self.plan["slot_stride_bytes"]))
            ),
            "offset_bytes": offset,
            "reuse_distance_slots": int(self.plan["slots"]),
            "kind": "cold_ring",
            "slice_bytes": size,
            "view_fallback": fallback,
        }

    def slice_hot(
        self,
        nbytes: int,
        *,
        offset_bytes: int = HOT_CONTROL_OFFSET,
        dtype: Any = None,
        reserve_bytes: int = 0,
        ledger: dict[str, Any] | None = None,
        cap_bytes: int = 0,
    ) -> tuple[Any, dict[str, Any]]:
        """Slice the dedicated hot-control buffer at a per-operand byte offset."""
        size = _pos_int(nbytes)
        offset = int(offset_bytes)
        if size is None or offset < 0:
            raise ProfilerUsageError("bench_cold_ring_slice_invalid")
        need = offset + size
        reserve = int(reserve_bytes)
        if self._hot_buffer is None or self._hot_capacity < max(need, reserve):
            capacity = max(int(self.plan["slot_stride_bytes"]), need, reserve)
            growth = capacity - (int(self._hot_capacity) if self._hot_buffer is not None else 0)
            if isinstance(ledger, dict) and growth > 0:
                _account_alloc_bytes(
                    ledger, growth, cap=int(cap_bytes), charge=True,
                    over_budget_reason="hot control buffer exceeds S0 cap",
                )
            hot_buffer = self.torch.empty(
                capacity, dtype=self.torch.uint8, device=f"npu:{self.ordinal}"
            )
            zero_ = getattr(hot_buffer, "zero_", None)
            if callable(zero_):
                zero_()
            self._hot_buffer = hot_buffer
            self._hot_capacity = capacity
        sliced, fallback = self._view(self._hot_buffer, offset, size, dtype)
        self._hot_calls += 1
        return sliced, {
            **self.hot(),
            "offset_bytes": offset,
            "slice_bytes": size,
            "view_fallback": fallback,
        }

    def slice_bytes(
        self, nbytes: int, *, hot: bool = False, dtype: Any = None
    ) -> tuple[Any, dict[str, Any]]:
        """Return a narrowed ring slice at the next disjoint slot (or hot offset 0)."""
        if self._buffer is None:
            raise ProfilerUsageError("bench_cold_ring_not_allocated")
        size = _pos_int(nbytes)
        if size is None:
            raise ProfilerUsageError("bench_cold_ring_slice_invalid")
        stride = int(self.plan["slot_stride_bytes"])
        if size > stride:
            raise ProfilerUsageError(
                "bench_cold_ring_slice_too_large: slice exceeds the slot stride"
            )
        if hot:
            return self.slice_hot(size, dtype=dtype)
        receipt = self.rotate()
        sliced, fallback = self._view(
            self._buffer, int(receipt["offset_bytes"]), size, dtype
        )
        return sliced, {**receipt, "slice_bytes": size, "view_fallback": fallback}

    def close(self) -> None:
        self._buffer = None
        self._hot_buffer = None
        self._hot_capacity = 0

    def receipt(self) -> dict[str, Any]:
        return {
            **self.plan,
            "allocated": self.allocated,
            "rotations": self._rotations,
            "precycled_slots": self._precycled,
            "hot_calls": self._hot_calls,
            "buffer_bytes": None if self._buffer is None else int(self.plan["total_bytes"]),
        }


def make_blocker_unit_op(
    torch: Any, ordinal: int, *, size: int = BLOCKER_UNIT_SIZE
) -> Callable[[], Any]:
    dtype = getattr(torch, "bfloat16", None)
    device = f"npu:{int(ordinal)}"
    left = torch.randn(size, size, dtype=dtype, device=device)
    right = torch.randn(size, size, dtype=dtype, device=device)
    matmul = getattr(torch, "mm", None) or getattr(torch, "matmul", None)
    if not callable(matmul):
        raise ProfilerUsageError("bench_blocker_unit_unavailable: torch.mm is absent")
    return lambda: matmul(left, right)


def _observed_clock_mhz(torch_npu: Any) -> float | None:
    for name in ("npu_get_clock_rate", "get_clock_rate"):
        getter = getattr(torch_npu, name, None) if torch_npu is not None else None
        if not callable(getter):
            continue
        try:
            value = float(getter())
        except TimeoutError:
            raise
        except Exception:
            continue
        if math.isfinite(value) and value > 0:
            return value / HZ_PER_MHZ if value > _MAX_CLOCK_HZ else value
    return None


def lock_clock(
    torch: Any,
    *,
    ordinal: int,
    size: int = GEMM_LOCK_SIZE,
    repeats: int = GEMM_LOCK_REPEATS,
    budget: Mapping[str, Any] | None = None,
    torch_npu: Any = None,
) -> dict[str, Any]:
    """Escape idle DVFS with 30 BF16 4096x4096 GEMMs inside the VRAM envelope."""
    dtype = getattr(torch, "bfloat16", None)
    device = f"npu:{int(ordinal)}"
    required = int(size) * int(size) * BF16_ELEMENT_BYTES * 2
    receipt: dict[str, Any] = {
        "repeats": int(repeats),
        "size": int(size),
        "dtype": "bf16",
        "clock_bytes": required,
        "clock_warmup_completed": False,
        "observed_clock_mhz": None,
        "idle_dvfs_escaped": False,
        "skipped": True,
        "basis": "30x4096_bf16_gemm_warmup",
    }
    torch_npu = torch_npu if torch_npu is not None else getattr(torch, "npu", None)
    cap = _pos_int((budget or {}).get("cap_bytes")) if isinstance(budget, Mapping) else None
    if cap is not None and cap < required:
        receipt["reason"] = "bench_clock_lock_over_budget"
        return receipt
    left = right = None
    try:
        left = torch.randn(size, size, dtype=dtype, device=device)
        right = torch.randn(size, size, dtype=dtype, device=device)
        matmul = getattr(torch, "mm", None) or getattr(torch, "matmul", None)
        if not callable(matmul):
            raise ProfilerUsageError("bench_clock_lock_unsupported: torch.mm is absent")
        for _ in range(int(repeats)):
            matmul(left, right)
        synchronize = getattr(getattr(torch, "npu", None), "synchronize", None)
        if callable(synchronize):
            synchronize()
        receipt.update(
            {"clock_warmup_completed": True, "idle_dvfs_escaped": True, "skipped": False}
        )
        receipt["observed_clock_mhz"] = _observed_clock_mhz(torch_npu)
        return receipt
    finally:
        del left, right


def build_admitted_context(
    runtime_cls: Any,
    protocol_cls: Any,
    *,
    torch: Any,
    torch_npu: Any | None = None,
    allowed_phy_ids: Sequence[int] | Iterable[int] = (),
    l2_bytes: Any = None,
    slot_bytes: int = DEFAULT_SLOT_BYTES,
    environ: Mapping[str, str] | None = None,
    resolver: Any = None,
    allocate: bool = True,
    free_bytes: Any = None,
    lock: bool = True,
    sparse_visible_devices: bool = False,
    allow_cpu_smoke: bool = False,
) -> dict[str, Any]:
    """Bind, admit the S0 envelope, lock clocks and size the cold ring."""
    torch_npu = torch_npu if torch_npu is not None else getattr(torch, "npu", None)
    binding = bind_device(
        torch=torch,
        torch_npu=torch_npu,
        environ=environ,
        allowed_phy_ids=allowed_phy_ids,
        resolver=resolver,
        sparse_visible_devices=sparse_visible_devices,
    )
    memory = measure_memory(torch_npu, binding["ordinal"], torch=torch)
    if free_bytes is not None:
        memory = {
            "measured": True,
            "free_bytes": int(free_bytes),
            "total_bytes": memory.get("total_bytes"),
            "missing": [],
        }
    budget = vram_budget(memory.get("free_bytes"), total_bytes=memory.get("total_bytes"))
    ring_plan = (
        cold_ring_plan(l2_bytes, slot_bytes=slot_bytes) if l2_bytes is not None else None
    )
    if ring_plan is not None and ring_plan["total_bytes"] > budget["cap_bytes"]:
        raise ProfilerUsageError(
            "bench_vram_budget_exceeded: cold ring "
            f"{ring_plan['total_bytes']} bytes exceeds the S0 cap {budget['cap_bytes']} bytes"
        )
    clock = (
        lock_clock(torch, ordinal=binding["ordinal"], budget=budget, torch_npu=torch_npu)
        if lock
        else {
            "repeats": 0,
            "idle_dvfs_escaped": False,
            "skipped": True,
            "clock_warmup_completed": False,
            "observed_clock_mhz": None,
            "basis": "disabled_by_caller",
        }
    )
    runtime = runtime_cls(torch, allow_cpu_smoke=allow_cpu_smoke)
    runtime.require_device_timing()
    ring = (
        ColdRing(torch, ring_plan, ordinal=binding["ordinal"])
        if ring_plan is not None
        else None
    )
    if ring is not None and allocate:
        ring.allocate()
    return {
        "schema": CONTEXT_SCHEMA,
        "torch": torch,
        "torch_npu": torch_npu,
        "device": binding,
        "memory": memory,
        "budget": budget,
        "clock": clock,
        "ring": ring,
        "ring_plan": ring_plan,
        "runtime": runtime,
        "timer_source": runtime.source,
        "allow_cpu_smoke": bool(allow_cpu_smoke),
        "protocol": protocol_cls(runtime),
    }


def close_context(context: Mapping[str, Any]) -> None:
    ring = context.get("ring")
    if isinstance(ring, ColdRing):
        ring.close()


__all__ = [
    "CONTEXT_SCHEMA", "ColdRing", "HOT_CONTROL_OFFSET", "RING_SCHEMA",
    "build_admitted_context", "close_context", "cold_ring_plan",
    "lock_clock", "make_blocker_unit_op", "resolve_l2_bytes",
]
