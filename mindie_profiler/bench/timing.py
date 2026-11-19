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
  * Device events are mandatory unless ``allow_cpu_smoke=True`` is explicitly
    requested for offline CPU smoke tests; ``host_fallback`` fails closed by
    default and is never marked qualified.
  * ``ColdRing.slice_bytes`` views the narrowed slice (``sliced.view(dtype)``),
    never the full backing buffer.
  * Missing L2/free-memory facts are explicit refusals.

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
from .abi import parse_allowed_phy_ids
from .profiles import profile_section
from .timing_ring import (
    CONTEXT_SCHEMA,
    ColdRing,
    HOT_CONTROL_OFFSET,
    RING_SCHEMA,
    build_admitted_context,
    close_context,
    cold_ring_plan,
    lock_clock,
    make_blocker_unit_op,
)

TIMING_SCHEMA = "mindie-bench-timing/1"

_UNITS = profile_section("units")
_CFG = profile_section("timing")

KIB = int(_UNITS["kib"])
MIB = int(_UNITS["mib"])
HZ_PER_MHZ = int(_UNITS["hz_per_mhz"])
CACHELINE_BYTES = int(_CFG["cacheline_bytes"])
GEMM_LOCK_SIZE = int(_CFG["gemm_lock_size"])
GEMM_LOCK_REPEATS = int(_CFG["gemm_lock_repeats"])
WARMUPS = int(_CFG["warmups"])
TRIALS = int(_CFG["trials"])
REPEATS = int(_CFG["repeats"])
BLOCKER_TARGET_MS = float(_CFG["blocker_target_ms"])
BLOCKER_MAX_REPEATS = int(_CFG["blocker_max_repeats"])
BLOCKER_UNIT_SIZE = int(_CFG["blocker_unit_size"])
_CAL_LOW_RATIO = float(_CFG["blocker_cal_low_ratio"])
_CAL_HIGH_RATIO = float(_CFG["blocker_cal_high_ratio"])
SMALL_OP_US = float(_CFG["small_op_us"])
SMALL_COLLECTIVE_BYTES = int(_CFG["small_collective_bytes"])
L2_RING_MULTIPLE = int(_CFG["l2_ring_multiple"])
DEFAULT_SLOT_BYTES = int(_CFG["default_slot_bytes"])
_ROUND_US = int(_CFG["round_us_digits"])
_ROUND_MS = int(_CFG["round_ms_digits"])
_P90 = float(_CFG["p90_quantile"])
_MAX_CLOCK_HZ = float(_CFG["max_clock_hz"])

STREAM_SATURATION_MODES = ("eager", "stream_saturated")
BF16_ELEMENT_BYTES = 2
GEMM_LOCK_BYTES = GEMM_LOCK_SIZE * GEMM_LOCK_SIZE * BF16_ELEMENT_BYTES
CLOCK_LOCK_BYTES = GEMM_LOCK_BYTES * 2
HOT_CONTROL_OFFSET = 0
ELEMENT_BYTES: dict[str, int] = {
    str(key): int(val) for key, val in _CFG["element_bytes"].items()
}

UNAVAILABLE = "unavailable"
MEASURED = "measured"
HOST_FALLBACK = "host_fallback"

_SHAPE_ELEMENT_KEYS = (
    "tokens", "m", "n", "k", "e", "rows", "width", "heads", "head_dim",
    "seq_len", "block_size", "sequences", "state_len", "latent", "rope", "length",
)
_SHAPE_BYTE_KEYS = ("bytes", "row_bytes", "expert_bytes", "l2_span_bytes")


def estimate_working_set_bytes(case: Mapping[str, Any]) -> int:
    """Upper-bound the device working set a case builder may allocate.

    Exported subgraph cases declare their footprint as top-level ``hbm_bytes``
    and per-node shapes in ``nodes`` rather than a top-level ``shape``; both
    must count towards the S0 cap or a multi-hundred-MiB logits case would
    falsely report zero bytes.
    """
    explicit = _positive_int(case.get("estimated_bytes"))
    work = int(case.get("work_bytes") or 0)
    shape = case.get("shape") if isinstance(case.get("shape"), Mapping) else {}
    if not shape:
        shape = {
            key: case[key]
            for key in _SHAPE_ELEMENT_KEYS + _SHAPE_BYTE_KEYS
            if key in case
        }
    declared = next(
        (
            _positive_int(shape.get(key))
            for key in _SHAPE_BYTE_KEYS
            if _positive_int(shape.get(key)) is not None
        ),
        None,
    )
    elem_bytes = ELEMENT_BYTES.get(str(case.get("dtype") or ""), BF16_ELEMENT_BYTES)
    m, n, k = (_positive_int(shape.get(key)) for key in ("m", "n", "k"))
    tokens, width = _positive_int(shape.get("tokens")), _positive_int(shape.get("width"))
    heads, head_dim = _positive_int(shape.get("heads")), _positive_int(shape.get("head_dim"))
    seq_len = _positive_int(shape.get("seq_len")) or tokens
    kv_heads = _positive_int(shape.get("kv_heads")) or heads
    builder = str(case.get("builder") or "")
    if m is not None and k is not None:
        experts = max(1, _positive_int(shape.get("e")) or 1)
        shaped = m * k * elem_bytes
        if n is not None:
            shaped += (experts * k * n + m * n) * elem_bytes
    elif tokens is not None and heads is not None and head_dim is not None:
        shaped = (tokens * heads + 2 * int(seq_len or tokens) * int(kv_heads or heads)) * head_dim * elem_bytes
        if builder in {"fused_recurrent_kda", "recurrent_gated_delta_rule", "recurrent_gdn_recover_ssm"}:
            shaped += tokens * heads * head_dim * head_dim * ELEMENT_BYTES["fp32"] * 2
    elif tokens is not None and width is not None:
        shaped = tokens * width * elem_bytes
    else:
        elements = sum(
            val
            for val in (_positive_int(shape.get(key)) for key in _SHAPE_ELEMENT_KEYS)
            if val is not None
        )
        shaped = elements * elem_bytes
    nodes = case.get("nodes")
    nodes_total = 0
    if isinstance(nodes, Sequence) and not isinstance(nodes, (str, bytes, bytearray)):
        nodes_total = sum(
            estimate_working_set_bytes(node)
            for node in nodes
            if isinstance(node, Mapping)
        )
    physical_work = case.get("physical_work")
    pw_hbm = (
        _positive_int(physical_work.get("hbm_bytes"))
        if isinstance(physical_work, Mapping)
        else None
    )
    hbm_bytes = _positive_int(case.get("hbm_bytes")) or pw_hbm
    return max(
        int(work),
        max(
            shaped,
            int(declared or 0),
            int(hbm_bytes or 0),
            int(nodes_total),
            int(explicit or 0),
        ),
    )


def case_over_budget(case: Mapping[str, Any], budget: Mapping[str, Any] | None) -> bool:
    """True when the declared working set cannot fit the admitted S0 cap."""
    if not isinstance(budget, Mapping):
        return False
    cap = _positive_int(budget.get("cap_bytes"))
    return False if cap is None else estimate_working_set_bytes(case) > cap


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

    def __init__(self, torch: Any, *, allow_cpu_smoke: bool = False) -> None:
        self.torch = torch
        self.npu = getattr(torch, "npu", None)
        event_factory = getattr(self.npu, "Event", None)
        self.available = callable(event_factory)
        self.allow_cpu_smoke = bool(allow_cpu_smoke)
        self.source = (
            "torch.npu.Event(enable_timing=True)"
            if self.available
            else "perf_counter_host_fallback"
        )

    def require_device_timing(self) -> None:
        if not self.available and not self.allow_cpu_smoke:
            raise ProfilerUsageError(
                "bench_host_fallback_forbidden: torch.npu.Event is unavailable; "
                "pass --allow-cpu-smoke explicitly for offline CPU smoke runs"
            )

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
        current = self.current_stream()
        current_waiter = getattr(current, "wait_event", None)
        if callable(current_waiter):
            current_waiter(event)

    def synchronize_event(self, event: Any) -> None:
        synchronize = getattr(event, "synchronize", None)
        if callable(synchronize):
            synchronize()
            return
        self.synchronize()

    def elapsed_us(self, start: Any, end: Any) -> float:
        elapsed_ms = float(start.elapsed_time(end))
        return elapsed_ms * 1000.0

    def synchronize(self) -> None:
        sync = getattr(self.npu, "synchronize", None)
        if callable(sync):
            sync()


class StreamBlocker:
    """Recalibrated each run to ~2.5 ms of queued work on a private stream."""

    def __init__(
        self,
        *,
        target_ms: float = BLOCKER_TARGET_MS,
        max_repeats: int = BLOCKER_MAX_REPEATS,
    ) -> None:
        self.target_ms = float(target_ms)
        self.max_repeats = int(max_repeats)
        self.unit_ms: float | None = None
        self.repeats = 0
        self.estimated_ms = 0.0
        self.calibrated = False

    def calibrate(self, unit_ms: Any) -> "StreamBlocker":
        if isinstance(unit_ms, bool) or not isinstance(unit_ms, (int, float)):
            raise ProfilerUsageError("bench_blocker_unit_invalid: unit op duration unknown")
        measured = float(unit_ms)
        if measured <= 0 or not math.isfinite(measured):
            raise ProfilerUsageError("bench_blocker_unit_invalid: unit op duration unknown")
        repeats = min(max(1, int(round(self.target_ms / measured))), self.max_repeats)
        self.unit_ms = measured
        self.repeats = repeats
        self.estimated_ms = measured * repeats
        self.calibrated = (
            self.target_ms * _CAL_LOW_RATIO
            <= self.estimated_ms
            <= self.target_ms * _CAL_HIGH_RATIO
        )
        return self

    @property
    def blocked_us(self) -> float:
        return float(self.estimated_ms) * 1000.0

    def receipt(self) -> dict[str, Any]:
        return {
            "target_ms": self.target_ms,
            "unit_ms": self.unit_ms,
            "repeats": self.repeats,
            "estimated_ms": round(self.estimated_ms, _ROUND_US),
            "blocked_us": round(self.blocked_us, _ROUND_US),
            "calibrated": self.calibrated,
            "basis": "measured single-unit device time on blocker_stream",
        }


def calibrate_blocker(
    runtime: TorchTimingRuntime,
    unit_op: Callable[[], Any],
    *,
    blocker: StreamBlocker | None = None,
    stream: Any = None,
) -> StreamBlocker:
    """Measure one unit op on the blocker stream, then size the blocker."""
    active = blocker or StreamBlocker()
    if not runtime.available:
        runtime.require_device_timing()
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
    elapsed_ms = runtime.elapsed_us(start, end) / 1000.0
    return active.calibrate(elapsed_ms)


class EventTimer:
    """Preallocated start/end events plus an optional blocker prefix."""

    def __init__(self, runtime: TorchTimingRuntime) -> None:
        self.runtime = runtime
        self.start = runtime.new_event() if runtime.available else None
        self.end = runtime.new_event() if runtime.available else None

    def measure(
        self,
        enqueue: Callable[[], Any],
        *,
        stream: Any = None,
        blocker: Callable[[], Any] | None = None,
        blocker_ms: float | None = None,
        blocker_stream: Any = None,
        blocker_done: Any = None,
    ) -> dict[str, Any]:
        if not self.runtime.available:
            self.runtime.require_device_timing()
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
        qualified = (
            None
            if blocker_ms is None
            else bool(enqueue_us <= float(blocker_ms) * 1000.0)
        )
        return {
            "duration_us": duration_us,
            "enqueue_us": enqueue_us,
            "stream_saturated_qualified": qualified,
            "mode": "stream_saturated" if blocker is not None else "eager",
        }

    def _host_measure(self, enqueue: Callable[[], Any]) -> dict[str, Any]:
        begin = time.perf_counter_ns()
        enqueue()
        self.runtime.synchronize()
        duration_us = (time.perf_counter_ns() - begin) / 1000.0
        return {
            "duration_us": duration_us,
            "enqueue_us": None,
            "stream_saturated_qualified": None,
            "mode": HOST_FALLBACK,
        }


def measurement_modes(
    kind: str, *, nbytes: int | None = None, observed_us: float | None = None
) -> tuple[str, ...]:
    """Return the qualified timing modes for one case."""
    small = bool(observed_us is not None and observed_us < SMALL_OP_US)
    if nbytes is not None and kind == "collective" and nbytes <= SMALL_COLLECTIVE_BYTES:
        small = True
    return STREAM_SATURATION_MODES if small else ("eager",)


class MeasurementProtocol:
    """5 warmups + 3 trials x 20 device-event repeats per qualified mode."""

    def __init__(
        self,
        runtime: TorchTimingRuntime,
        *,
        warmups: int = WARMUPS,
        trials: int = TRIALS,
        repeats: int = REPEATS,
    ) -> None:
        self.runtime = runtime
        self.timer = EventTimer(runtime)
        self.warmups = int(warmups)
        self.trials = int(trials)
        self.repeats = int(repeats)
        self.blocker_stream = runtime.new_stream() if runtime.available else None
        self.blocker_done = runtime.new_event() if runtime.available else None

    def run(
        self,
        enqueue: Callable[[], Any],
        *,
        case_id: str,
        kind: str = "operator",
        nbytes: int | None = None,
        blocker: Callable[[], Any] | None = None,
        blocker_receipt: Mapping[str, Any] | None = None,
        stream: Any = None,
        cold_ring: "ColdRing | None" = None,
        hot_enqueue: Callable[[], Any] | None = None,
        probe_reduce: Callable[[float], float] | None = None,
    ) -> dict[str, Any]:
        if self.warmups < 0 or self.trials < 1 or self.repeats < 1:
            raise ProfilerUsageError("bench_timing_protocol_invalid")
        self.runtime.require_device_timing()
        for _ in range(self.warmups):
            enqueue()
        self.runtime.synchronize()
        observed = self.timer.measure(enqueue, stream=stream)["duration_us"]
        if callable(probe_reduce):
            observed = float(probe_reduce(observed))
        modes = measurement_modes(kind, nbytes=nbytes, observed_us=observed)
        blocker_ready = (
            blocker is not None and (blocker_receipt or {}).get("calibrated") is True
        )
        payload: dict[str, Any] = {
            "schema": TIMING_SCHEMA,
            "case_id": str(case_id),
            "protocol": "warmups + trials x repeats device events",
            "warmups": self.warmups,
            "trials": self.trials,
            "repeats": self.repeats,
            "kind": kind,
            "nbytes": nbytes,
            "startup_ms": 0.0,
            "inclusive_minimum": True,
            "timer_source": self.runtime.source,
            "blocker": dict(blocker_receipt) if blocker_receipt else None,
            "stream_saturated": "stream_saturated" in modes,
            "stream_saturated_available": bool(blocker_ready),
            "modes": {},
        }
        qualified = bool(self.runtime.available)
        host_timed = (
            not self.runtime.available
            or self.runtime.source == "perf_counter_host_fallback"
        )
        if "stream_saturated" in modes and not blocker_ready:
            qualified = False
        for mode in modes:
            active_blocker = blocker if mode == "stream_saturated" else None
            blocker_ms = (
                (blocker_receipt or {}).get("estimated_ms")
                if mode == "stream_saturated"
                else None
            )
            trials: list[dict[str, Any]] = []
            all_repeats: list[float] = []
            all_enqueue: list[float] = []
            for trial_index in range(self.trials):
                repeats: list[float] = []
                enqueue_samples: list[float] = []
                qualified_samples: list[bool] = []
                for _ in range(self.repeats):
                    sample = self.timer.measure(
                        enqueue,
                        stream=stream,
                        blocker=active_blocker,
                        blocker_ms=blocker_ms,
                        blocker_stream=self.blocker_stream,
                        blocker_done=self.blocker_done,
                    )
                    repeats.append(sample["duration_us"])
                    if sample["enqueue_us"] is not None:
                        enqueue_samples.append(sample["enqueue_us"])
                        all_enqueue.append(sample["enqueue_us"])
                    if sample["stream_saturated_qualified"] is not None:
                        qualified_samples.append(bool(sample["stream_saturated_qualified"]))
                all_repeats.extend(repeats)
                trials.append(
                    {
                        "trial": trial_index,
                        "median_us": round(_median(repeats), _ROUND_US),
                        "min_us": round(min(repeats), _ROUND_US),
                        "max_us": round(max(repeats), _ROUND_US),
                        "repeats_us": [round(val, _ROUND_US) for val in repeats],
                        "enqueue_us": (
                            round(_median(enqueue_samples), _ROUND_US)
                            if enqueue_samples
                            else None
                        ),
                        "enqueue_us_samples": [
                            round(val, _ROUND_US) for val in enqueue_samples
                        ],
                        "stream_saturated_qualified": (
                            all(qualified_samples) if qualified_samples else None
                        ),
                    }
                )
                if qualified_samples and not all(qualified_samples):
                    qualified = False
            if host_timed or mode == HOST_FALLBACK:
                mode_qualified = False
            elif mode == "stream_saturated":
                if not blocker_ready:
                    for trial in trials:
                        trial["stream_saturated_qualified"] = False
                    mode_qualified = False
                else:
                    mode_qualified = all(
                        trial.get("stream_saturated_qualified") is True
                        for trial in trials
                    )
            else:
                mode_qualified = True
            payload["modes"][mode] = {
                "trials": trials,
                "trial_medians_us": [item["median_us"] for item in trials],
                "median_us": round(
                    _median([item["median_us"] for item in trials]), _ROUND_US
                ),
                "minimum_us": round(min(all_repeats), _ROUND_US),
                "p50_us": round(_percentile(all_repeats, 0.5), _ROUND_US),
                "p90_us": round(_percentile(all_repeats, _P90), _ROUND_US),
                "repeat_count": len(all_repeats),
                "enqueue_us": round(_median(all_enqueue), _ROUND_US) if all_enqueue else None,
                "enqueue_us_samples": [round(val, _ROUND_US) for val in all_enqueue],
                "stream_saturated_qualified": (
                    all(
                        item["stream_saturated_qualified"]
                        for item in trials
                        if item["stream_saturated_qualified"] is not None
                    )
                    if any(
                        item["stream_saturated_qualified"] is not None for item in trials
                    )
                    else None
                ),
                "qualified": bool(mode_qualified),
            }
            if not mode_qualified:
                qualified = False
        primary = payload["modes"].get("eager") or payload["modes"][modes[0]]
        minimum_ms = primary["minimum_us"] / 1000.0
        median_ms = primary["median_us"] / 1000.0
        payload["minimum_ms"] = round(minimum_ms, _ROUND_MS)
        payload["median_ms"] = round(median_ms, _ROUND_MS)
        payload["qualified"] = bool(qualified)
        if isinstance(cold_ring, ColdRing) and cold_ring.allocated:
            payload["cold_ring"] = cold_ring.receipt()
            payload["hot_control"] = self._hot_control(
                hot_enqueue or enqueue, stream=stream
            )
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
        return {
            "kind": "hot_control",
            "offset_bytes": HOT_CONTROL_OFFSET,
            "repeats_us": [round(val, _ROUND_US) for val in repeats],
            "median_us": round(_median(repeats), _ROUND_US),
            "enqueue_us": (
                round(_median(enqueue_samples), _ROUND_US) if enqueue_samples else None
            ),
            "mode": HOST_FALLBACK if not self.runtime.available else "eager",
        }


def admit_context(**kwargs: Any) -> dict[str, Any]:
    """Bind, admit the S0 envelope, lock clocks and size the cold ring."""
    return build_admitted_context(TorchTimingRuntime, MeasurementProtocol, **kwargs)


__all__ = [
    "BLOCKER_TARGET_MS", "CACHELINE_BYTES", "CLOCK_LOCK_BYTES", "CONTEXT_SCHEMA",
    "ColdRing", "DEFAULT_SLOT_BYTES", "EventTimer", "GEMM_LOCK_BYTES",
    "GEMM_LOCK_REPEATS", "GEMM_LOCK_SIZE", "HOST_FALLBACK", "L2_RING_MULTIPLE",
    "MEASURED", "MeasurementProtocol", "REPEATS", "RING_SCHEMA",
    "SMALL_COLLECTIVE_BYTES", "SMALL_OP_US", "STREAM_SATURATION_MODES",
    "StreamBlocker", "TIMING_SCHEMA", "TRIALS", "TorchTimingRuntime",
    "UNAVAILABLE", "WARMUPS", "admit_context", "calibrate_blocker",
    "case_over_budget", "close_context", "cold_ring_plan",
    "estimate_working_set_bytes", "lock_clock", "make_blocker_unit_op",
    "measurement_modes", "parse_allowed_phy_ids",
]
