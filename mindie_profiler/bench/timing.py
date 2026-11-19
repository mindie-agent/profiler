"""Event, stream-blocker and cold-ring timing protocol for the bench suite.

[Role]
  Own the S0 protocol: read ``LOCAL_RANK``, admit the VRAM envelope, lock the
  AIC clock with 30 BF16 ``4096x4096`` GEMMs inside the measured budget,
  calibrate a ``2.5 ms`` ``StreamBlocker`` on its own stream, preallocate
  events, run 5 warmups plus 3 trials x 20 repeats, time eager and
  stream-saturated ``< 50 us`` calls and ``4 KiB`` collectives, and allocate
  ``>= 3x L2`` cold rings paired with a hot control.

[Invariants]
  * A trial's latency is the median of its 20 event repeats; raw repeats stay.
  * ``startup_ms`` is ``0.0`` for the inclusive ``minimum_ms``: the timed
    window opens at the first launch, so no invented startup term is added.
  * Device events are only used when ``torch.npu.Event`` is callable; a host
    fallback is unqualified, never a device measurement.
  * Blocker work is enqueued on ``blocker_stream``; the measured stream waits on
    a ``blocker_done`` event before its ``start`` event is recorded.
  * ``slice_bytes`` rotates disjoint cold slots while the single-slot
    ``hot_control`` reuses address ``0`` on purpose.
  * Stream saturation is only *qualified* when a calibrated blocker exists and
    every measured host enqueue finished inside the blocked interval.
  * Missing L2/free-memory facts are explicit refusals; the clock-lock GEMMs
    are only allocated when the S0 envelope holds them.

[Timeouts & Locks]
  No wall-clock deadline of its own: the caller's container budget bounds the
  process.  Events, streams and the ring are preallocated once per context.

[Side-Effect Policy]
  Allocates device memory through the admitted ``torch`` handle and releases it
  through ``close()``; writes nothing.
"""

from __future__ import annotations

import contextlib
import math
import time
from typing import Any, Callable, Iterable, Mapping, Sequence

from ..events import ProfilerUsageError
from .abi import (
    bind_device, measure_memory, parse_allowed_phy_ids, vram_budget,
)

TIMING_SCHEMA = "mindie-bench-timing/1"
CONTEXT_SCHEMA = "mindie-bench-context/1"
RING_SCHEMA = "mindie-bench-cold-ring/1"

KIB = 1024
MIB = KIB * KIB
CACHELINE_BYTES = 128
GEMM_LOCK_SIZE = 4096
GEMM_LOCK_REPEATS = 30
WARMUPS = 5
TRIALS = 3
REPEATS = 20
BLOCKER_TARGET_MS = 2.5
BLOCKER_MAX_REPEATS = 4096
BLOCKER_UNIT_SIZE = 256
SMALL_OP_US = 50.0
SMALL_COLLECTIVE_BYTES = 4 * KIB
L2_RING_MULTIPLE = 3
DEFAULT_SLOT_BYTES = 8 * MIB
STREAM_SATURATION_MODES = ("eager", "stream_saturated")
HZ_PER_MHZ = 1_000_000
BF16_ELEMENT_BYTES = 2
GEMM_LOCK_BYTES = GEMM_LOCK_SIZE * GEMM_LOCK_SIZE * BF16_ELEMENT_BYTES
CLOCK_LOCK_BYTES = GEMM_LOCK_BYTES * 2
HOT_CONTROL_OFFSET = 0
ELEMENT_BYTES = {"bf16": 2, "fp16": 2, "float16": 2, "int8": 1, "w4a8": 1,
                 "float32": 4, "int32": 4, "int64": 8}

UNAVAILABLE = "unavailable"
MEASURED = "measured"
HOST_FALLBACK = "host_fallback"

_SHAPE_ELEMENT_KEYS = (
    "tokens", "m", "n", "k", "e", "rows", "width", "heads", "head_dim",
    "seq_len", "block_size", "sequences", "state_len", "latent", "rope", "length",
)
_SHAPE_BYTE_KEYS = ("bytes", "row_bytes", "expert_bytes", "l2_span_bytes")


def cold_ring_plan(l2_bytes: Any, *, slot_bytes: int = DEFAULT_SLOT_BYTES) -> dict[str, Any]:
    """Plan ``ceil(3 * L2 / slot)`` cacheline-disjoint slots plus a hot control."""
    size = _positive_int(l2_bytes)
    slot = _positive_int(slot_bytes)
    if size is None:
        raise ProfilerUsageError(
            "bench_l2_unknown: the cold ring needs an explicit L2-per-die size "
            "(--l2-mib or an exposed device property); it is never assumed")
    if slot is None:
        raise ProfilerUsageError("bench_cold_ring_slot_invalid: slot bytes must be positive")
    slots = -(-L2_RING_MULTIPLE * size // slot)
    stride = _align(slot, CACHELINE_BYTES)
    required = L2_RING_MULTIPLE * size
    total = slots * stride
    return {
        "schema": RING_SCHEMA,
        "l2_bytes": size,
        "l2_mib": round(size / MIB, 6),
        "slot_bytes": slot,
        "slot_stride_bytes": stride,
        "slots": slots,
        "total_bytes": total,
        "total_mib": round(total / MIB, 6),
        "required_bytes": required,
        "required_mib": round(required / MIB, 6),
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


def estimate_working_set_bytes(case: Mapping[str, Any]) -> int:
    """Upper-bound the device working set a case builder may allocate.

    An explicit ``estimated_bytes`` wins; otherwise the declared work bytes and
    the shape descriptors give a conservative envelope.  The value is only a
    budget gate, never a measurement.
    """
    explicit = _positive_int(case.get("estimated_bytes"))
    if explicit is not None:
        return explicit
    work = int(case.get("work_bytes") or 0)
    shape = case.get("shape") if isinstance(case.get("shape"), Mapping) else {}
    declared = next((_positive_int(shape.get(key)) for key in _SHAPE_BYTE_KEYS
                     if _positive_int(shape.get(key)) is not None), None)
    element_bytes = ELEMENT_BYTES.get(str(case.get("dtype") or ""), BF16_ELEMENT_BYTES)
    m, n, k = (_positive_int(shape.get(key)) for key in ("m", "n", "k"))
    tokens, width = _positive_int(shape.get("tokens")), _positive_int(shape.get("width"))
    if m is not None and k is not None:
        shaped = m * k * element_bytes
        if n is not None:
            shaped += (k * n + m * n) * element_bytes
    elif tokens is not None and width is not None:
        shaped = tokens * width * element_bytes
    else:
        elements = 0
        for key in _SHAPE_ELEMENT_KEYS:
            value = _positive_int(shape.get(key))
            if value is not None:
                elements += value
        shaped = elements * element_bytes
    shaped = max(shaped, int(declared or 0))
    return max(int(work), shaped)


def case_over_budget(case: Mapping[str, Any], budget: Mapping[str, Any] | None) -> bool:
    """True when the declared working set cannot fit the admitted S0 cap."""
    if not isinstance(budget, Mapping):
        return False
    cap = _positive_int(budget.get("cap_bytes"))
    if cap is None:
        return False
    return estimate_working_set_bytes(case) > cap


def _align(value: int, alignment: int) -> int:
    return -(-value // alignment) * alignment


def _positive_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value <= 0 or not math.isfinite(float(value)):
        return None
    return int(value)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        return 0.0
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(float(item) for item in values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * fraction
    low, high = int(math.floor(position)), int(math.ceil(position))
    if low == high:
        return ordered[low]
    return ordered[low] * (high - position) + ordered[high] * (position - low)


class TorchTimingRuntime:
    """Adapter over the torch NPU event/stream primitives."""

    def __init__(self, torch: Any) -> None:
        self.torch = torch
        self.npu = getattr(torch, "npu", None)
        event_factory = getattr(self.npu, "Event", None)
        self.available = callable(event_factory)
        self.source = ("torch.npu.Event(enable_timing=True)" if self.available
                       else "perf_counter_host_fallback")

    def new_event(self) -> Any:
        return self.npu.Event(enable_timing=True)

    def new_stream(self) -> Any:
        factory = getattr(self.npu, "Stream", None)
        if not callable(factory):
            return self.current_stream()
        try:
            return factory()
        except TimeoutError:
            raise
        except Exception:
            return self.current_stream()

    def current_stream(self) -> Any:
        factory = getattr(self.npu, "current_stream", None)
        return factory() if callable(factory) else None

    def stream_context(self, stream: Any) -> Any:
        """``torch.npu.stream(stream)`` when installed, else a null context."""
        factory = getattr(self.npu, "stream", None)
        if callable(factory) and stream is not None:
            try:
                return factory(stream)
            except TimeoutError:
                raise
            except Exception:
                return contextlib.nullcontext()
        return contextlib.nullcontext()

    def record(self, event: Any, stream: Any = None) -> None:
        if stream is None:
            event.record()
        else:
            event.record(stream)

    def wait_event(self, stream: Any, event: Any) -> None:
        waiter = getattr(stream, "wait_event", None)
        if callable(waiter):
            waiter(event)
            return
        sync = getattr(self.npu, "current_stream", None)
        current = sync() if callable(sync) else None
        current_waiter = getattr(current, "wait_event", None)
        if callable(current_waiter):
            current_waiter(event)

    def synchronize_event(self, event: Any) -> None:
        synchronize = getattr(event, "synchronize", None)
        if callable(synchronize):
            synchronize()
            return
        device_sync = getattr(self.npu, "synchronize", None)
        if callable(device_sync):
            device_sync()

    def elapsed_us(self, start: Any, end: Any) -> float:
        elapsed_ms = float(start.elapsed_time(end))
        return elapsed_ms * 1000.0

    def synchronize(self) -> None:
        sync = getattr(self.npu, "synchronize", None)
        if callable(sync):
            sync()


class StreamBlocker:
    """Recalibrated each run to ~2.5 ms of queued work on a private stream."""

    def __init__(self, *, target_ms: float = BLOCKER_TARGET_MS,
                 max_repeats: int = BLOCKER_MAX_REPEATS) -> None:
        self.target_ms = float(target_ms)
        self.max_repeats = int(max_repeats)
        self.unit_ms: float | None = None
        self.repeats = 0
        self.estimated_ms = 0.0
        self.calibrated = False

    def calibrate(self, unit_ms: Any) -> dict[str, Any]:
        if isinstance(unit_ms, bool) or not isinstance(unit_ms, (int, float)):
            raise ProfilerUsageError("bench_blocker_unit_invalid: unit op duration unknown")
        measured = float(unit_ms)
        if measured <= 0 or not math.isfinite(measured):
            raise ProfilerUsageError("bench_blocker_unit_invalid: unit op duration unknown")
        repeats = max(1, int(round(self.target_ms / measured)))
        repeats = min(repeats, self.max_repeats)
        self.unit_ms = measured
        self.repeats = repeats
        self.estimated_ms = measured * repeats
        self.calibrated = (self.target_ms * 0.95 <= self.estimated_ms
                           <= self.target_ms * 1.05)
        return self

    @property
    def blocked_us(self) -> float:
        return float(self.estimated_ms) * 1000.0

    def receipt(self) -> dict[str, Any]:
        return {
            "target_ms": self.target_ms,
            "unit_ms": self.unit_ms,
            "repeats": self.repeats,
            "estimated_ms": round(self.estimated_ms, 6),
            "blocked_us": round(self.blocked_us, 6),
            "calibrated": self.calibrated,
            "basis": "measured single-unit device time on blocker_stream",
        }


def calibrate_blocker(runtime: TorchTimingRuntime, unit_op: Callable[[], Any],
                      *, blocker: StreamBlocker | None = None,
                      stream: Any = None) -> StreamBlocker:
    """Measure one unit op on the blocker stream, then size the blocker."""
    active = blocker or StreamBlocker()
    if not runtime.available:
        active.unit_ms = None
        active.repeats = 0
        active.estimated_ms = 0.0
        active.calibrated = False
        return active
    unit_stream = stream if stream is not None else runtime.new_stream()
    start, end = runtime.new_event(), runtime.new_event()
    with runtime.stream_context(unit_stream):
        runtime.record(start, unit_stream)
        unit_op()
        runtime.record(end, unit_stream)
    runtime.synchronize_event(end)
    return active.calibrate(runtime.elapsed_us(start, end) / 1000.0)


class EventTimer:
    """Preallocated start/end events plus an optional blocker prefix."""

    def __init__(self, runtime: TorchTimingRuntime) -> None:
        self.runtime = runtime
        self.start = runtime.new_event() if runtime.available else None
        self.end = runtime.new_event() if runtime.available else None

    def measure(self, enqueue: Callable[[], Any], *, stream: Any = None,
                blocker: Callable[[], Any] | None = None,
                blocker_ms: float | None = None,
                blocker_stream: Any = None,
                blocker_done: Any = None) -> dict[str, Any]:
        if not self.runtime.available:
            return self._host_measure(enqueue)
        if blocker is not None:
            with self.runtime.stream_context(blocker_stream):
                blocker()
            if blocker_done is not None:
                self.runtime.record(blocker_done, blocker_stream)
                self.runtime.wait_event(stream, blocker_done)
        host_begin = time.perf_counter_ns()
        self.runtime.record(self.start, stream)
        enqueue()
        self.runtime.record(self.end, stream)
        enqueue_us = (time.perf_counter_ns() - host_begin) / 1000.0
        self.runtime.synchronize_event(self.end)
        duration_us = self.runtime.elapsed_us(self.start, self.end)
        qualified = (None if blocker_ms is None
                     else bool(enqueue_us <= float(blocker_ms) * 1000.0))
        return {"duration_us": duration_us, "enqueue_us": enqueue_us,
                "stream_saturated_qualified": qualified,
                "mode": "stream_saturated" if blocker is not None else "eager"}

    def _host_measure(self, enqueue: Callable[[], Any]) -> dict[str, Any]:
        begin = time.perf_counter_ns()
        enqueue()
        self.runtime.synchronize()
        duration_us = (time.perf_counter_ns() - begin) / 1000.0
        return {"duration_us": duration_us, "enqueue_us": None,
                "stream_saturated_qualified": None,
                "mode": HOST_FALLBACK}


def measurement_modes(kind: str, *, nbytes: int | None = None,
                      observed_us: float | None = None) -> tuple[str, ...]:
    """Return the qualified timing modes for one case.

    Both eager and stream-saturated timing are mandatory for sub-``50 us``
    calls and ``4 KiB`` collectives; larger work is timed eager only.
    """
    small = False
    if observed_us is not None and observed_us < SMALL_OP_US:
        small = True
    if nbytes is not None and kind == "collective" and nbytes <= SMALL_COLLECTIVE_BYTES:
        small = True
    return STREAM_SATURATION_MODES if small else ("eager",)


class MeasurementProtocol:
    """5 warmups + 3 trials x 20 device-event repeats per qualified mode."""

    def __init__(self, runtime: TorchTimingRuntime, *, warmups: int = WARMUPS,
                 trials: int = TRIALS, repeats: int = REPEATS) -> None:
        self.runtime = runtime
        self.timer = EventTimer(runtime)
        self.warmups = int(warmups)
        self.trials = int(trials)
        self.repeats = int(repeats)
        self.blocker_stream = runtime.new_stream() if runtime.available else None
        self.blocker_done = runtime.new_event() if runtime.available else None

    def run(self, enqueue: Callable[[], Any], *, case_id: str,
            kind: str = "operator", nbytes: int | None = None,
            blocker: Callable[[], Any] | None = None,
            blocker_receipt: Mapping[str, Any] | None = None,
            stream: Any = None,
            cold_ring: "ColdRing | None" = None,
            hot_enqueue: Callable[[], Any] | None = None) -> dict[str, Any]:
        if self.warmups < 0 or self.trials < 1 or self.repeats < 1:
            raise ProfilerUsageError("bench_timing_protocol_invalid")
        for _ in range(self.warmups):
            enqueue()
        self.runtime.synchronize()
        observed = self.timer.measure(enqueue, stream=stream)["duration_us"]
        modes = measurement_modes(kind, nbytes=nbytes, observed_us=observed)
        blocker_ready = (blocker is not None
                         and (blocker_receipt or {}).get("calibrated") is True)
        payload: dict[str, Any] = {
            "schema": TIMING_SCHEMA, "case_id": str(case_id),
            "protocol": "warmups + trials x repeats device events",
            "warmups": self.warmups, "trials": self.trials,
            "repeats": self.repeats, "kind": kind, "nbytes": nbytes,
            "startup_ms": 0.0, "inclusive_minimum": True,
            "timer_source": self.runtime.source,
            "blocker": dict(blocker_receipt) if blocker_receipt else None,
            "stream_saturated": "stream_saturated" in modes,
            "stream_saturated_available": bool(blocker_ready),
            "modes": {},
        }
        qualified = bool(self.runtime.available)
        if "stream_saturated" in modes and not blocker_ready:
            qualified = False
        for mode in modes:
            active_blocker = blocker if mode == "stream_saturated" else None
            blocker_ms = (blocker_receipt or {}).get("estimated_ms") \
                if mode == "stream_saturated" else None
            trials: list[dict[str, Any]] = []
            all_repeats: list[float] = []
            all_enqueue: list[float] = []
            for trial_index in range(self.trials):
                repeats: list[float] = []
                enqueue_samples: list[float] = []
                qualified_samples: list[bool] = []
                for _ in range(self.repeats):
                    sample = self.timer.measure(
                        enqueue, stream=stream, blocker=active_blocker,
                        blocker_ms=blocker_ms,
                        blocker_stream=self.blocker_stream,
                        blocker_done=self.blocker_done)
                    repeats.append(sample["duration_us"])
                    if sample["enqueue_us"] is not None:
                        enqueue_samples.append(sample["enqueue_us"])
                        all_enqueue.append(sample["enqueue_us"])
                    if sample["stream_saturated_qualified"] is not None:
                        qualified_samples.append(
                            bool(sample["stream_saturated_qualified"]))
                all_repeats.extend(repeats)
                trials.append({
                    "trial": trial_index,
                    "median_us": round(_median(repeats), 6),
                    "min_us": round(min(repeats), 6),
                    "max_us": round(max(repeats), 6),
                    "repeats_us": [round(value, 6) for value in repeats],
                    "enqueue_us": (round(_median(enqueue_samples), 6)
                                   if enqueue_samples else None),
                    "enqueue_us_samples": [round(value, 6)
                                           for value in enqueue_samples],
                    "stream_saturated_qualified": (
                        all(qualified_samples) if qualified_samples else None),
                })
                if qualified_samples and not all(qualified_samples):
                    qualified = False
            mode_summary = {
                "trials": trials,
                "trial_medians_us": [item["median_us"] for item in trials],
                "median_us": round(_median([item["median_us"] for item in trials]), 6),
                "minimum_us": round(min(all_repeats), 6),
                "p50_us": round(_percentile(all_repeats, 0.5), 6),
                "p90_us": round(_percentile(all_repeats, 0.9), 6),
                "repeat_count": len(all_repeats),
                "enqueue_us": round(_median(all_enqueue), 6) if all_enqueue else None,
                "enqueue_us_samples": [round(value, 6) for value in all_enqueue],
                "stream_saturated_qualified": (
                    all(item["stream_saturated_qualified"] for item in trials
                        if item["stream_saturated_qualified"] is not None)
                    if any(item["stream_saturated_qualified"] is not None
                           for item in trials) else None),
            }
            payload["modes"][mode] = mode_summary
        primary = payload["modes"].get("eager") or payload["modes"][modes[0]]
        payload["minimum_ms"] = round(primary["minimum_us"] / 1000.0, 9)
        payload["median_ms"] = round(primary["median_us"] / 1000.0, 9)
        payload["qualified"] = bool(qualified)
        if isinstance(cold_ring, ColdRing) and cold_ring.allocated:
            payload["cold_ring"] = cold_ring.receipt()
            payload["hot_control"] = self._hot_control(
                hot_enqueue or enqueue, stream=stream)
        return payload

    def _hot_control(self, enqueue: Callable[[], Any], *, stream: Any) -> dict[str, Any]:
        """Paired fixed-offset ``hot=True`` pass over the same ring buffer."""
        repeats: list[float] = []
        enqueue_samples: list[float] = []
        for _ in range(self.repeats):
            sample = self.timer.measure(enqueue, stream=stream)
            repeats.append(sample["duration_us"])
            if sample["enqueue_us"] is not None:
                enqueue_samples.append(sample["enqueue_us"])
        return {"kind": "hot_control", "offset_bytes": HOT_CONTROL_OFFSET,
                "repeats_us": [round(value, 6) for value in repeats],
                "median_us": round(_median(repeats), 6),
                "enqueue_us": (round(_median(enqueue_samples), 6)
                               if enqueue_samples else None),
                "mode": HOST_FALLBACK if not self.runtime.available else "eager"}


class ColdRing:
    """One device allocation rotated over cacheline-disjoint cold slots."""

    def __init__(self, torch: Any, plan: Mapping[str, Any], *, ordinal: int) -> None:
        self.torch = torch
        self.plan = dict(plan)
        self.ordinal = int(ordinal)
        self._buffer = None
        self._slot = 0
        self._rotations = 0
        self._precycled = 0
        self._hot_calls = 0

    def allocate(self) -> "ColdRing":
        total = int(self.plan["total_bytes"])
        self._buffer = self.torch.empty(total, dtype=self.torch.uint8,
                                        device=f"npu:{self.ordinal}")
        return self

    @property
    def allocated(self) -> bool:
        return self._buffer is not None

    @property
    def offset_bytes(self) -> int:
        return (self._slot % int(self.plan["slots"])) * int(
            self.plan["slot_stride_bytes"])

    def rotate(self) -> dict[str, Any]:
        """Advance to the next cold slot (whole cache lines, disjoint)."""
        slots = int(self.plan["slots"])
        stride = int(self.plan["slot_stride_bytes"])
        index = self._slot % slots
        self._slot = (self._slot + 1) % slots
        self._rotations += 1
        return {"slot_index": index, "offset_bytes": index * stride,
                "reuse_distance_slots": slots, "kind": "cold_ring"}

    def precycle(self, repeats: int) -> dict[str, Any]:
        """Advance past the rotation length when the ring has more slots."""
        slots = int(self.plan["slots"])
        count = max(0, int(repeats))
        if count and slots > count:
            advance = slots - count
            self._slot = (self._slot + advance) % slots
            self._precycled += advance
        return {"precycled_slots": self._precycled, "slots": slots,
                "repeats": count}

    def hot(self) -> dict[str, Any]:
        """Single-slot same-address reuse control."""
        return {"slot_index": 0, "offset_bytes": HOT_CONTROL_OFFSET,
                "reuse_distance_slots": 0, "kind": "hot_control"}

    def slice_bytes(self, nbytes: int, *, hot: bool = False,
                    dtype: Any = None) -> tuple[Any, dict]:
        """Return a ring slice at the next disjoint slot (or fixed offset 0).

        The buffer is a byte tensor; ``narrow``/``view`` produce a typed slice
        when the backend supports them.  Minimal fake tensors fall back to the
        whole backing buffer with an explicit ``view_fallback`` receipt.
        """
        if self._buffer is None:
            raise ProfilerUsageError("bench_cold_ring_not_allocated")
        size = _positive_int(nbytes)
        if size is None:
            raise ProfilerUsageError("bench_cold_ring_slice_invalid")
        stride = int(self.plan["slot_stride_bytes"])
        if size > stride:
            raise ProfilerUsageError(
                "bench_cold_ring_slice_too_large: slice exceeds the slot stride")
        receipt = self.hot() if hot else self.rotate()
        if hot:
            self._hot_calls += 1
        offset = int(receipt["offset_bytes"])
        narrow = getattr(self._buffer, "narrow", None)
        view = getattr(self._buffer, "view", None)
        if callable(narrow) and callable(view):
            sliced = narrow(0, offset, size)
            if dtype is not None:
                sliced = view(dtype)
            receipt = {**receipt, "slice_bytes": size, "view_fallback": False}
            return sliced, receipt
        receipt = {**receipt, "slice_bytes": size, "view_fallback": True}
        return self._buffer, receipt

    def close(self) -> None:
        self._buffer = None

    def receipt(self) -> dict[str, Any]:
        return {**self.plan, "allocated": self.allocated,
                "rotations": self._rotations, "precycled_slots": self._precycled,
                "hot_calls": self._hot_calls,
                "buffer_bytes": None if self._buffer is None
                else int(self.plan["total_bytes"])}


def make_blocker_unit_op(torch: Any, ordinal: int,
                         *, size: int = BLOCKER_UNIT_SIZE) -> Callable[[], Any]:
    """Preallocated BF16 GEMM used as one calibrated blocker unit."""
    dtype = getattr(torch, "bfloat16", None)
    device = f"npu:{int(ordinal)}"
    left = torch.randn(size, size, dtype=dtype, device=device)
    right = torch.randn(size, size, dtype=dtype, device=device)
    matmul = getattr(torch, "mm", None) or getattr(torch, "matmul", None)
    if not callable(matmul):
        raise ProfilerUsageError("bench_blocker_unit_unavailable: torch.mm is absent")

    def unit() -> Any:
        return matmul(left, right)

    return unit


def _observed_clock_mhz(torch_npu: Any) -> float | None:
    """Read the installed clock rate; an unreadable clock stays ``None``."""
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
            return value / HZ_PER_MHZ if value > 1e6 else value
    return None


def lock_clock(torch: Any, *, ordinal: int, size: int = GEMM_LOCK_SIZE,
               repeats: int = GEMM_LOCK_REPEATS,
               budget: Mapping[str, Any] | None = None,
               torch_npu: Any = None) -> dict[str, Any]:
    """Escape idle DVFS with 30 BF16 4096x4096 GEMMs inside the VRAM envelope."""
    dtype = getattr(torch, "bfloat16", None)
    device = f"npu:{int(ordinal)}"
    required = int(size) * int(size) * BF16_ELEMENT_BYTES * 2
    receipt: dict[str, Any] = {
        "repeats": int(repeats), "size": int(size), "dtype": "bf16",
        "clock_bytes": required,
        "clock_warmup_completed": False,
        "observed_clock_mhz": None,
        "idle_dvfs_escaped": False,
        "skipped": True,
        "basis": "30x4096_bf16_gemm_warmup",
    }
    torch_npu = torch_npu if torch_npu is not None else getattr(torch, "npu", None)
    cap = _positive_int((budget or {}).get("cap_bytes")) if isinstance(
        budget, Mapping) else None
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
        receipt.update({"clock_warmup_completed": True,
                        "idle_dvfs_escaped": True, "skipped": False})
        receipt["observed_clock_mhz"] = _observed_clock_mhz(torch_npu)
        return receipt
    finally:
        del left, right


def admit_context(*, torch: Any, torch_npu: Any | None = None,
                  allowed_phy_ids: Sequence[int] | Iterable[int] = (),
                  l2_bytes: Any = None, slot_bytes: int = DEFAULT_SLOT_BYTES,
                  environ: Mapping[str, str] | None = None,
                  resolver: Any = None, allocate: bool = True,
                  free_bytes: Any = None, lock: bool = True,
                  sparse_visible_devices: bool = False) -> dict[str, Any]:
    """Bind, admit the S0 envelope, lock clocks and size the cold ring."""
    torch_npu = torch_npu if torch_npu is not None else getattr(torch, "npu", None)
    binding = bind_device(torch=torch, torch_npu=torch_npu, environ=environ,
                          allowed_phy_ids=allowed_phy_ids, resolver=resolver,
                          sparse_visible_devices=sparse_visible_devices)
    memory = measure_memory(torch_npu, binding["ordinal"], torch=torch)
    if free_bytes is not None:
        memory = {"measured": True, "free_bytes": int(free_bytes),
                  "total_bytes": memory.get("total_bytes"), "missing": []}
    budget = vram_budget(memory.get("free_bytes"),
                        total_bytes=memory.get("total_bytes"))
    ring_plan = (cold_ring_plan(l2_bytes, slot_bytes=slot_bytes)
                 if l2_bytes is not None else None)
    if ring_plan is not None and ring_plan["total_bytes"] > budget["cap_bytes"]:
        raise ProfilerUsageError(
            "bench_vram_budget_exceeded: cold ring "
            f"{ring_plan['total_bytes']} bytes exceeds the S0 cap "
            f"{budget['cap_bytes']} bytes")
    clock = (lock_clock(torch, ordinal=binding["ordinal"], budget=budget,
                        torch_npu=torch_npu) if lock else {
        "repeats": 0, "idle_dvfs_escaped": False, "skipped": True,
        "clock_warmup_completed": False, "observed_clock_mhz": None,
        "basis": "disabled_by_caller"})
    runtime = TorchTimingRuntime(torch)
    ring = (ColdRing(torch, ring_plan, ordinal=binding["ordinal"])
            if ring_plan is not None else None)
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
        "protocol": MeasurementProtocol(runtime),
    }


def close_context(context: Mapping[str, Any]) -> None:
    ring = context.get("ring")
    if isinstance(ring, ColdRing):
        ring.close()


__all__ = [
    "BLOCKER_TARGET_MS", "CACHELINE_BYTES", "CLOCK_LOCK_BYTES", "CONTEXT_SCHEMA",
    "ColdRing", "DEFAULT_SLOT_BYTES", "EventTimer", "GEMM_LOCK_BYTES",
    "GEMM_LOCK_REPEATS", "GEMM_LOCK_SIZE", "L2_RING_MULTIPLE", "MEASURED",
    "MeasurementProtocol", "REPEATS", "RING_SCHEMA", "SMALL_COLLECTIVE_BYTES",
    "SMALL_OP_US", "STREAM_SATURATION_MODES", "StreamBlocker", "TIMING_SCHEMA",
    "TRIALS", "TorchTimingRuntime", "UNAVAILABLE", "WARMUPS", "admit_context",
    "calibrate_blocker", "case_over_budget", "close_context", "cold_ring_plan",
    "estimate_working_set_bytes", "lock_clock", "make_blocker_unit_op",
    "measurement_modes", "parse_allowed_phy_ids",
]
