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
from .operators_common import FA_CAUSAL_MASK_BYTES
from .operators_recurrent_state import chunk_kda_working_set_bytes, indexed_kda_working_set_bytes
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
CLOCK_OPERATOR_BUSY_UNION = "busy_union"
CLOCK_OPERATOR_ELAPSED_SPAN = "elapsed_span"
_HOST_SUBMISSION_SPAN = "host_submission_span"

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
_BLOCKER_CAL_WARMUPS = int(_CFG["blocker_cal_warmups"])
_BLOCKER_CAL_BURST = int(_CFG["blocker_cal_burst"])
_HOST_DISPATCH_SATURATION_RATIO = float(_CFG["host_dispatch_saturation_ratio"])
_CAL_LOW_RATIO = float(_CFG["blocker_cal_low_ratio"])
_CAL_HIGH_RATIO = float(_CFG["blocker_cal_high_ratio"])
SMALL_OP_US = float(_CFG["small_op_us"])
SMALL_COLLECTIVE_BYTES = int(_CFG["small_collective_bytes"])
L2_RING_MULTIPLE = int(_CFG["l2_ring_multiple"])
L2_EVICT_MULTIPLE = int(_CFG["l2_evict_multiple"])
DEFAULT_SLOT_BYTES = int(_CFG["default_slot_bytes"])
_ROUND_US = int(_CFG["round_us_digits"])
_ROUND_MS = int(_CFG["round_ms_digits"])
_P25 = float(_CFG["p25_quantile"])
_P75 = float(_CFG["p75_quantile"])
_P90 = float(_CFG["p90_quantile"])
_P99 = float(_CFG["p99_quantile"])
_PCT_SCALE = float(_CFG["pct_scale"])
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
    if builder == "chunk_kda_fwd":
        shaped = chunk_kda_working_set_bytes(case)
    elif m is not None and k is not None:
        experts = max(1, _positive_int(shape.get("e")) or 1)
        shaped = m * k * elem_bytes
        if n is not None:
            shaped += (experts * k * n + m * n) * elem_bytes
    elif tokens is not None and heads is not None and head_dim is not None:
        shaped = (tokens * heads + 2 * int(seq_len or tokens) * int(kv_heads or heads)) * head_dim * elem_bytes
        batch = _positive_int(shape.get("sequences"))
        state_len = _positive_int(shape.get("state_len"))
        if (
            (builder == "fusion_attention" and case.get("causal"))
            or (
                builder == "incre_flash_attention"
                and case.get("causal")
                and batch is not None
                and tokens > batch
            )
        ):
            shaped += FA_CAUSAL_MASK_BYTES
        elif builder == "fused_recurrent_kda" and "q_len" in shape and batch and state_len:
            shaped = indexed_kda_working_set_bytes(tokens, batch, heads, head_dim, state_len, str(case.get("dtype") or "bf16"))
        elif builder in {"fused_recurrent_kda", "recurrent_gated_delta_rule", "recurrent_gdn_recover_ssm"}:
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


def _cv_pct(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    nums = [float(item) for item in values]
    mean = sum(nums) / len(nums)
    if mean <= 0.0 or not math.isfinite(mean):
        return 0.0
    variance = sum((val - mean) ** 2 for val in nums) / len(nums)
    return math.sqrt(variance) / mean * _PCT_SCALE


def compute_busy_union_us(intervals: Sequence[tuple[float, float]]) -> float:
    """Compute exact union duration (us) of traced device kernel ``(start_us, end_us)`` intervals."""
    clean = sorted(
        (float(start), float(end))
        for start, end in intervals
        if math.isfinite(float(start)) and math.isfinite(float(end)) and float(end) > float(start)
    )
    if not clean:
        return 0.0
    total = 0.0
    cur_start, cur_end = clean[0]
    for start, end in clean[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start
            cur_start, cur_end = start, end
    return total + (cur_end - cur_start)


def _resolve_traced_repeat_samples(
    traced_intervals_us: Sequence[Any] | None,
    *,
    total_repeats: int,
) -> list[float] | None:
    """Resolve verified per-repeat busy-union durations; return None if trace evidence mismatches."""
    if not traced_intervals_us or total_repeats < 1:
        return None
    items = list(traced_intervals_us)
    first = items[0]
    is_flat_pair = (
        isinstance(first, (tuple, list))
        and len(first) == 2
        and isinstance(first[0], (int, float))
        and not isinstance(first[0], bool)
    )
    if is_flat_pair:
        if total_repeats != 1:
            return None
        val = compute_busy_union_us(items)
        return [val] if val > 0.0 else None
    if len(items) != total_repeats:
        return None
    resolved: list[float] = []
    for rep_intervals in items:
        if not isinstance(rep_intervals, (tuple, list)):
            return None
        val = compute_busy_union_us(rep_intervals)
        if val <= 0.0:
            return None
        resolved.append(val)
    return resolved


def reset_peak_memory_stats(
    torch_npu: Any, ordinal: int = 0, *, torch: Any = None
) -> bool:
    """Reset peak allocated NPU memory telemetry before one case execution."""
    surface = getattr(torch, "npu", None) if torch is not None else None
    for holder in (surface, torch_npu):
        reset_fn = getattr(holder, "reset_peak_memory_stats", None) if holder is not None else None
        if not callable(reset_fn):
            continue
        try:
            reset_fn(int(ordinal))
            return True
        except TypeError:
            try:
                reset_fn()
                return True
            except TimeoutError:
                raise
            except Exception:
                continue
        except TimeoutError:
            raise
        except Exception:
            continue
    return False


def measure_peak_allocated_bytes(
    torch_npu: Any, ordinal: int = 0, *, torch: Any = None
) -> int | None:
    """Read real peak allocated HBM bytes via ``torch.npu.max_memory_allocated``."""
    surface = getattr(torch, "npu", None) if torch is not None else None
    for holder in (surface, torch_npu):
        getter = getattr(holder, "max_memory_allocated", None) if holder is not None else None
        if not callable(getter):
            continue
        try:
            raw = getter(int(ordinal))
        except TypeError:
            try:
                raw = getter()
            except TimeoutError:
                raise
            except Exception:
                continue
        except TimeoutError:
            raise
        except Exception:
            continue
        if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw >= 0:
            return int(raw)
    return None


def make_l2_flush_op(
    torch: Any,
    l2_bytes: int | None,
    ordinal: int = 0,
    *,
    cap_bytes: int = 0,
) -> Callable[[], Any] | None:
    """Create an explicit ``> 2x L2`` streaming flush op between repeats (incl. ACLGraph)."""
    size = _positive_int(l2_bytes)
    if size is None or torch is None:
        return None
    flush_bytes = L2_EVICT_MULTIPLE * size + CACHELINE_BYTES
    if cap_bytes > 0 and flush_bytes > cap_bytes:
        return None
    empty = getattr(torch, "empty", None)
    uint8 = getattr(torch, "uint8", None)
    if not callable(empty) or uint8 is None:
        return None
    try:
        scratch = empty(flush_bytes, dtype=uint8, device=f"npu:{int(ordinal)}")
    except TimeoutError:
        raise
    except Exception:
        return None
    zero_ = getattr(scratch, "zero_", None)
    if callable(zero_):
        return lambda: zero_()
    fill_ = getattr(scratch, "fill_", None)
    if callable(fill_):
        return lambda: fill_(0)
    return None


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

    def wait_event(self, stream: Any, event: Any) -> bool:
        waiter = getattr(stream, "wait_event", None)
        if callable(waiter):
            waiter(event)
            return True
        current = self.current_stream()
        current_waiter = getattr(current, "wait_event", None)
        if callable(current_waiter):
            current_waiter(event)
            return True
        return False

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
        for _ in range(_BLOCKER_CAL_WARMUPS):
            unit_op()
    runtime.synchronize()
    with runtime.stream_context(unit_stream):
        runtime.record(start, unit_stream)
        for _ in range(_BLOCKER_CAL_BURST):
            unit_op()
        runtime.record(end, unit_stream)
    runtime.synchronize_event(end)
    elapsed_ms = runtime.elapsed_us(start, end) / (1000.0 * _BLOCKER_CAL_BURST)
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
        blocker_begin = time.perf_counter_ns() if blocker is not None else None
        blocked = False
        if blocker is not None:
            with self.runtime.stream_context(blocker_stream):
                blocker()
            if blocker_done is not None:
                self.runtime.record(blocker_done, blocker_stream)
                blocked = self.runtime.wait_event(stream, blocker_done)
        host_begin = time.perf_counter_ns()
        self.runtime.record(self.start, stream)
        with self.runtime.stream_context(stream):
            enqueue()
        self.runtime.record(self.end, stream)
        host_end = time.perf_counter_ns()
        enqueue_us = (host_end - host_begin) / 1000.0
        blocked_enqueue_us = (host_end - blocker_begin) / 1000.0 if blocker_begin is not None else None
        self.runtime.synchronize_event(self.end)
        duration_us = self.runtime.elapsed_us(self.start, self.end)
        qualified = (
            None
            if blocker_ms is None
            else bool(blocked and blocked_enqueue_us is not None
                      and blocked_enqueue_us <= float(blocker_ms) * 1000.0)
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
        multi_op: bool = False,
        captured: bool = False,
        pre_repeat: Callable[[], Any] | None = None,
        traced_intervals_us: Sequence[tuple[float, float]] | None = None,
        warmups: int | None = None,
        trials: int | None = None,
        repeats: int | None = None,
        timing_modes: Sequence[str] | None = None,
        deadline_monotonic: float | None = None,
    ) -> dict[str, Any]:
        """[Cohesive-Pipeline] Warmup, mode selection, repeat trials, and quantile summary."""
        eff_warmups = self.warmups if warmups is None else int(warmups)
        eff_trials = self.trials if trials is None else int(trials)
        eff_repeats = self.repeats if repeats is None else int(repeats)
        if eff_warmups < 0 or eff_trials < 1 or eff_repeats < 1:
            raise ProfilerUsageError("bench_timing_protocol_invalid")
        self.runtime.require_device_timing()
        deadline_hit = deadline_monotonic is not None and time.monotonic() >= float(deadline_monotonic)
        for _ in range(eff_warmups):
            if deadline_monotonic is not None and time.monotonic() >= float(deadline_monotonic):
                deadline_hit = True
                break
            enqueue()
        self.runtime.synchronize()
        blocker_ready = (
            blocker is not None and (blocker_receipt or {}).get("calibrated") is True
            and (blocker_receipt or {}).get("estimated_ms", 0) > 0
        )
        if timing_modes:
            modes = tuple(str(m) for m in timing_modes)
        else:
            probe_blocker = (
                blocker
                if (blocker_ready and not (captured and kind == "collective"))
                else None
            )
            probe_blocker_ms = (
                (blocker_receipt or {}).get("estimated_ms")
                if probe_blocker is not None
                else None
            )
            probe = self.timer.measure(
                enqueue,
                stream=stream,
                blocker=probe_blocker,
                blocker_ms=probe_blocker_ms,
                blocker_stream=self.blocker_stream,
                blocker_done=self.blocker_done,
            )
            observed = float(probe["duration_us"])
            if callable(probe_reduce):
                observed = float(probe_reduce(observed))
            modes = measurement_modes(kind, nbytes=nbytes, observed_us=observed)
            probe_enq = probe.get("enqueue_us")
            if (
                blocker_ready
                and "stream_saturated" not in modes
                and probe.get("stream_saturated_qualified") is True
                and probe_enq is not None
                and float(probe_enq) >= _HOST_DISPATCH_SATURATION_RATIO * max(observed, 1.0)
            ):
                modes = STREAM_SATURATION_MODES
        if not timing_modes:
            if multi_op and not captured:
                modes = ("stream_saturated",) if blocker_ready else ("eager",)
            elif captured and (kind == "collective" or not blocker_ready):
                modes = ("eager",)
            elif captured and multi_op and blocker_ready and "stream_saturated" not in modes:
                modes = STREAM_SATURATION_MODES
        traced_samples = _resolve_traced_repeat_samples(
            traced_intervals_us, total_repeats=eff_trials * eff_repeats
        )
        has_traced = traced_samples is not None
        clock_operator = CLOCK_OPERATOR_BUSY_UNION if has_traced else CLOCK_OPERATOR_ELAPSED_SPAN
        payload: dict[str, Any] = {
            "schema": TIMING_SCHEMA,
            "case_id": str(case_id),
            "protocol": "warmups + trials x repeats device events",
            "warmups": eff_warmups,
            "trials": eff_trials,
            "repeats": eff_repeats,
            "kind": kind,
            "nbytes": nbytes,
            "startup_ms": 0.0,
            "inclusive_minimum": True,
            "timer_source": self.runtime.source,
            "clock_operator": clock_operator,
            "traced_interval_verified": has_traced,
            "blocker": dict(blocker_receipt) if blocker_receipt else None,
            "stream_saturated": "stream_saturated" in modes,
            "stream_saturated_available": bool(blocker_ready),
            "explicit_l2_flush": callable(pre_repeat),
            "deadline_exceeded": bool(deadline_hit),
            "modes": {},
        }
        if has_traced and traced_samples is not None:
            payload["traced_busy_union_us"] = round(_median(traced_samples), _ROUND_US)
        qualified = bool(self.runtime.available and not deadline_hit)
        host_timed = (
            not self.runtime.available
            or self.runtime.source == "perf_counter_host_fallback"
        )
        if "stream_saturated" in modes and not blocker_ready:
            qualified = False
        for mode in modes:
            active_blocker = blocker if mode == "stream_saturated" and blocker_ready else None
            blocker_ms = (
                (blocker_receipt or {}).get("estimated_ms")
                if mode == "stream_saturated"
                else None
            )
            trials_out: list[dict[str, Any]] = []
            all_repeats: list[float] = []
            all_enqueue: list[float] = []
            sample_cursor = 0
            for trial_index in range(eff_trials):
                repeats_out: list[float] = []
                enqueue_samples: list[float] = []
                qualified_samples: list[bool] = []
                for _ in range(eff_repeats):
                    if deadline_monotonic is not None and time.monotonic() >= float(deadline_monotonic):
                        deadline_hit = True
                        qualified = False
                        break
                    if callable(pre_repeat):
                        pre_repeat()
                    sample = self.timer.measure(
                        enqueue,
                        stream=stream,
                        blocker=active_blocker,
                        blocker_ms=blocker_ms,
                        blocker_stream=self.blocker_stream,
                        blocker_done=self.blocker_done,
                    )
                    dur_us = (
                        traced_samples[sample_cursor]
                        if traced_samples is not None
                        else sample["duration_us"]
                    )
                    sample_cursor += 1
                    repeats_out.append(dur_us)
                    if sample["enqueue_us"] is not None:
                        enqueue_samples.append(sample["enqueue_us"])
                        all_enqueue.append(sample["enqueue_us"])
                    if sample["stream_saturated_qualified"] is not None:
                        qualified_samples.append(bool(sample["stream_saturated_qualified"]))
                if repeats_out:
                    all_repeats.extend(repeats_out)
                    trials_out.append(
                        {
                            "trial": trial_index,
                            "median_us": round(_median(repeats_out), _ROUND_US),
                            "min_us": round(min(repeats_out), _ROUND_US),
                            "max_us": round(max(repeats_out), _ROUND_US),
                            "repeats_us": [round(val, _ROUND_US) for val in repeats_out],
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
                if deadline_hit:
                    break
            if deadline_hit or host_timed or mode == HOST_FALLBACK or not all_repeats:
                mode_qualified = False
            elif mode == "stream_saturated":
                if not blocker_ready:
                    for trial in trials_out:
                        trial["stream_saturated_qualified"] = False
                    mode_qualified = False
                else:
                    mode_qualified = all(
                        trial.get("stream_saturated_qualified") is True
                        for trial in trials_out
                    )
            else:
                mode_qualified = not multi_op or captured
            payload["modes"][mode] = self._mode_summary(
                trials_out,
                all_repeats,
                all_enqueue,
                mode_qualified,
                clock_operator=clock_operator,
                warmups=eff_warmups,
                trials_count=eff_trials,
                repeats_count=eff_repeats,
            )
            if multi_op and not captured and not mode_qualified:
                payload["modes"][mode]["boundary"] = _HOST_SUBMISSION_SPAN
            if not mode_qualified:
                qualified = False
        payload["deadline_exceeded"] = bool(deadline_hit)
        sat = payload["modes"].get("stream_saturated")
        primary = (
            sat
            if (sat is not None and sat.get("qualified") is True)
            else (payload["modes"].get("eager") or payload["modes"][modes[0]])
        )
        minimum_ms = primary["minimum_us"] / 1000.0
        median_ms = primary["median_us"] / 1000.0
        payload["minimum_ms"] = round(minimum_ms, _ROUND_MS)
        payload["median_ms"] = round(median_ms, _ROUND_MS)
        payload["qualified"] = bool(qualified and not deadline_hit)
        if "boundary" in primary:
            payload["boundary"] = primary["boundary"]
        if isinstance(cold_ring, ColdRing) and cold_ring.allocated:
            payload["cold_ring"] = cold_ring.receipt()
            payload["hot_control"] = self._hot_control(
                hot_enqueue or enqueue, stream=stream
            )
            if multi_op and not captured:
                payload["hot_control"].update(qualified=False, boundary=_HOST_SUBMISSION_SPAN)
        return payload

    @staticmethod
    def _mode_summary(
        trials: Sequence[Mapping[str, Any]],
        all_repeats: Sequence[float],
        all_enqueue: Sequence[float],
        mode_qualified: bool,
        *,
        clock_operator: str = CLOCK_OPERATOR_ELAPSED_SPAN,
        warmups: int = WARMUPS,
        trials_count: int = TRIALS,
        repeats_count: int = REPEATS,
    ) -> dict[str, Any]:
        if not all_repeats:
            return {
                "trials": list(trials),
                "trial_medians_us": [],
                "median_us": 0.0,
                "minimum_us": 0.0,
                "min_us": 0.0,
                "p25_us": 0.0,
                "p50_us": 0.0,
                "p75_us": 0.0,
                "p90_us": 0.0,
                "p99_us": 0.0,
                "max_us": 0.0,
                "iqr_us": 0.0,
                "cv_pct": 0.0,
                "clock_operator": clock_operator,
                "stats_us": {
                    "min": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0,
                    "p90": 0.0, "p99": 0.0, "max": 0.0, "iqr": 0.0,
                    "cv_pct": 0.0, "enqueue_p50": None,
                    "warmups": int(warmups), "trials": int(trials_count),
                    "repeats": int(repeats_count), "repeat_count": 0,
                    "trial_medians": [],
                },
                "enqueue_us": None,
                "repeat_count": 0,
                "qualified": False,
            }
        p25 = round(_percentile(all_repeats, _P25), _ROUND_US)
        p50 = round(_percentile(all_repeats, 0.5), _ROUND_US)
        p75 = round(_percentile(all_repeats, _P75), _ROUND_US)
        p90 = round(_percentile(all_repeats, _P90), _ROUND_US)
        p99 = round(_percentile(all_repeats, _P99), _ROUND_US)
        min_v = round(min(all_repeats), _ROUND_US)
        max_v = round(max(all_repeats), _ROUND_US)
        iqr_v = round(max(0.0, p75 - p25), _ROUND_US)
        cv_v = round(_cv_pct(all_repeats), _ROUND_US)
        enq_p50 = round(_median(all_enqueue), _ROUND_US) if all_enqueue else None
        trial_medians = [item["median_us"] for item in trials]
        return {
            "trials": trials,
            "trial_medians_us": trial_medians,
            "median_us": round(_median(trial_medians), _ROUND_US),
            "minimum_us": min_v,
            "min_us": min_v,
            "p25_us": p25,
            "p50_us": p50,
            "p75_us": p75,
            "p90_us": p90,
            "p99_us": p99,
            "max_us": max_v,
            "iqr_us": iqr_v,
            "cv_pct": cv_v,
            "clock_operator": clock_operator,
            "stats_us": {
                "min": min_v,
                "p25": p25,
                "p50": p50,
                "p75": p75,
                "p90": p90,
                "p99": p99,
                "max": max_v,
                "iqr": iqr_v,
                "cv_pct": cv_v,
                "enqueue_p50": enq_p50,
                "warmups": int(warmups),
                "trials": int(trials_count),
                "repeats": int(repeats_count),
                "repeat_count": len(all_repeats),
                "trial_medians": trial_medians,
            },
            "repeat_count": len(all_repeats),
            "enqueue_us": enq_p50,
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
    "BLOCKER_TARGET_MS", "CACHELINE_BYTES", "CLOCK_LOCK_BYTES",
    "CLOCK_OPERATOR_BUSY_UNION", "CLOCK_OPERATOR_ELAPSED_SPAN", "CONTEXT_SCHEMA",
    "ColdRing", "DEFAULT_SLOT_BYTES", "EventTimer", "GEMM_LOCK_BYTES",
    "GEMM_LOCK_REPEATS", "GEMM_LOCK_SIZE", "HOST_FALLBACK", "L2_EVICT_MULTIPLE",
    "L2_RING_MULTIPLE", "MEASURED", "MeasurementProtocol", "REPEATS", "RING_SCHEMA",
    "SMALL_COLLECTIVE_BYTES", "SMALL_OP_US", "STREAM_SATURATION_MODES",
    "StreamBlocker", "TIMING_SCHEMA", "TRIALS", "TorchTimingRuntime",
    "UNAVAILABLE", "WARMUPS", "admit_context", "calibrate_blocker",
    "case_over_budget", "close_context", "cold_ring_plan", "compute_busy_union_us",
    "estimate_working_set_bytes", "lock_clock", "make_blocker_unit_op",
    "make_l2_flush_op", "measure_peak_allocated_bytes", "measurement_modes",
    "parse_allowed_phy_ids", "reset_peak_memory_stats",
]
