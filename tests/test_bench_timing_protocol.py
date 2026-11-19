"""Bench timing protocol: blocker calibration, events, cold rings, VRAM gate.

[Role]
  Verify the S0 measurement protocol on a fake device: the ``2.5 ms``
  ``StreamBlocker`` calibration, the ``5 + 3 x 20`` event-repeat structure,
  eager versus stream-saturated qualification for sub-``50 us`` work and
  ``4 KiB`` collectives, ``>= 3x L2`` cacheline-disjoint cold rings with a
  single-slot hot control, the AIC clock lock, and the fail-closed VRAM
  envelope.

[Invariants]
  * No NPU is touched; the fake records the exact primitive call sequence.
  * ``startup_ms`` stays ``0.0`` and raw repeats are retained.

[Timeouts & Locks]
  Pure in-memory work; no sleeps or threads.

[Side-Effect Policy]
  No I/O.
"""

from __future__ import annotations

import pytest

from mindie_profiler.bench import timing
from mindie_profiler.events import ProfilerUsageError

MIB = 1024 * 1024
GIB = 1024 * MIB


class Clock:
    def __init__(self):
        self.ms = 0.0


class FakeEvent:
    def __init__(self, clock, enable_timing=False):
        self.clock = clock
        self.enable_timing = enable_timing
        self.stamp = None
        self.syncs = 0

    def record(self, stream=None):
        self.stamp = self.clock.ms

    def synchronize(self):
        self.syncs += 1

    def elapsed_time(self, other):
        return max(0.0, float(other.stamp) - float(self.stamp))


class FakeStream:
    def __init__(self):
        self.waits = 0

    def wait_event(self, _event):
        self.waits += 1


class FakeNpu:
    def __init__(self, clock, *, free=24 * GIB, total=64 * GIB, events=True):
        self.clock = clock
        self.calls = []
        self.free = free
        self.total = total
        self.events = events
        if not events:
            self.Event = None  # type: ignore[assignment] - absent primitive
        self._stream = FakeStream()

    def Event(self, enable_timing=False):
        if not self.events:
            raise AttributeError("Event")
        self.calls.append("Event")
        return FakeEvent(self.clock, enable_timing)

    def Stream(self):
        self.calls.append("Stream")
        return FakeStream()

    def current_stream(self):
        return self._stream

    def set_device(self, ordinal):
        self.calls.append(f"set_device:{ordinal}")

    def synchronize(self):
        self.calls.append("synchronize")

    def mem_get_info(self):
        return (self.free, self.total)


class FakeTensor:
    def __init__(self, size):
        self.size = size


class FakeTorch:
    def __init__(self, *, events=True, free=24 * GIB):
        self.clock = Clock()
        self.npu = FakeNpu(self.clock, events=events, free=free)
        self.uint8 = "uint8"
        self.bfloat16 = "bf16"
        self.float32 = "float32"
        self.mm_calls = 0
        self.allocations = []

    def empty(self, size, dtype=None, device=None):
        self.allocations.append((size, dtype, device))
        return FakeTensor(size)

    def randn(self, *shape, dtype=None, device=None):
        return FakeTensor(shape)

    def mm(self, left, right):
        self.mm_calls += 1
        return FakeTensor((1, 1))


def _context(**kwargs):
    torch = kwargs.pop("torch", None) or FakeTorch(**kwargs)
    return torch, timing.admit_context(
        torch=torch, torch_npu=torch.npu, environ={timing_env(): "0"},
        l2_bytes=96 * MIB, **kwargs)


def timing_env():
    from mindie_profiler.bench.abi import LOCAL_RANK_ENV

    return LOCAL_RANK_ENV


@pytest.mark.parametrize("l2_mib,slots,total_mib", [
    (96, 36, 288),
    (168, 63, 504),
    (192, 72, 576),
])
def test_cold_ring_is_three_times_l2_disjoint_slots(l2_mib, slots, total_mib):
    plan = timing.cold_ring_plan(l2_mib * MIB)
    assert plan["slots"] == slots
    assert plan["total_mib"] == total_mib
    assert plan["required_mib"] == 3 * l2_mib
    assert plan["total_bytes"] >= 3 * l2_mib
    assert plan["disjoint_cacheline"] is True
    assert plan["slot_stride_bytes"] % timing.CACHELINE_BYTES == 0
    assert plan["hot_control"]["slots"] == 1
    assert plan["hot_control"]["label"] == "hot_control"


def test_cold_ring_refuses_unknown_l2_and_aligns_odd_slots():
    with pytest.raises(ProfilerUsageError, match="bench_l2_unknown"):
        timing.cold_ring_plan(None)
    plan = timing.cold_ring_plan(96 * MIB, slot_bytes=1000)
    assert plan["slot_stride_bytes"] == 1024
    assert plan["slot_bytes"] == 1000


def test_ring_rotation_advances_and_hot_control_reuses_one_slot():
    plan = timing.cold_ring_plan(96 * MIB)
    ring = timing.ColdRing(FakeTorch(), plan, ordinal=0).allocate()
    first = ring.rotate()
    second = ring.rotate()
    assert first["offset_bytes"] == 0
    assert second["offset_bytes"] == plan["slot_stride_bytes"]
    assert first["reuse_distance_slots"] == plan["slots"]
    assert ring.hot() == {"slot_index": 0, "offset_bytes": 0,
                          "reuse_distance_slots": 0, "kind": "hot_control"}
    assert ring.receipt()["rotations"] == 2
    ring.close()
    assert ring.allocated is False


@pytest.mark.parametrize("unit_ms,repeats,calibrated", [
    (0.05, 50, True),
    (0.025, 100, True),
    (3.0, 1, False),
])
def test_stream_blocker_calibration(unit_ms, repeats, calibrated):
    blocker = timing.StreamBlocker().calibrate(unit_ms)
    assert blocker.repeats == repeats
    assert blocker.calibrated is calibrated
    assert blocker.receipt()["estimated_ms"] == pytest.approx(unit_ms * repeats)
    with pytest.raises(ProfilerUsageError):
        timing.StreamBlocker().calibrate(0)


def test_calibrate_blocker_measures_one_unit_and_sizes_the_prefix():
    torch = FakeTorch()
    runtime = timing.TorchTimingRuntime(torch)
    unit_us = 50.0

    def unit():
        torch.clock.ms += unit_us / 1000.0

    blocker = timing.calibrate_blocker(runtime, unit)
    assert blocker.unit_ms == pytest.approx(unit_us / 1000.0)
    assert blocker.repeats == 50
    assert blocker.calibrated is True


def test_protocol_reports_5_plus_3x20_and_both_modes_for_small_ops():
    torch = FakeTorch()
    runtime = timing.TorchTimingRuntime(torch)
    protocol = timing.MeasurementProtocol(runtime)
    op_us = 20.0

    def enqueue():
        torch.clock.ms += op_us / 1000.0
        return True

    blocker = timing.StreamBlocker().calibrate(0.05)  # 50 x 50 us = 2.5 ms
    payload = protocol.run(enqueue, case_id="d1.vector", nbytes=6,
                           blocker=lambda: None, blocker_receipt=blocker.receipt())
    assert payload["warmups"] == 5
    assert payload["trials"] == 3
    assert payload["repeats"] == 20
    assert payload["startup_ms"] == 0.0
    assert payload["inclusive_minimum"] is True
    assert sorted(payload["modes"]) == ["eager", "stream_saturated"]
    for mode in payload["modes"].values():
        assert len(mode["trials"]) == 3
        assert all(len(trial["repeats_us"]) == 20 for trial in mode["trials"])
        assert mode["repeat_count"] == 60
    assert payload["minimum_ms"] == pytest.approx(op_us / 1000.0)
    assert payload["modes"]["stream_saturated"]["trials"][0][
        "stream_saturated_qualified"] is True
    assert payload["qualified"] is True


def test_protocol_uses_only_eager_for_large_work_and_4k_collectives_use_both():
    torch = FakeTorch()
    protocol = timing.MeasurementProtocol(timing.TorchTimingRuntime(torch))

    def big():
        torch.clock.ms += 0.5

    assert list(protocol.run(big, case_id="big")["modes"]) == ["eager"]

    def small_collective():
        torch.clock.ms += 0.02

    payload = protocol.run(small_collective, case_id="4k", kind="collective",
                           nbytes=timing.SMALL_COLLECTIVE_BYTES)
    assert sorted(payload["modes"]) == ["eager", "stream_saturated"]


def test_stream_saturation_is_unqualified_when_enqueue_outlives_the_blocker():
    torch = FakeTorch()
    runtime = timing.TorchTimingRuntime(torch)
    protocol = timing.MeasurementProtocol(runtime)
    blocker = timing.StreamBlocker().calibrate(1.0)  # 2 x 1 ms = 2 ms blocker

    def slow_enqueue():
        runtime.synchronize()  # host work inside the measured window
        torch.clock.ms += 0.02
        import time

        time.sleep(0.003)  # 3 ms of host enqueue, beyond the 2 ms blocker

    payload = protocol.run(slow_enqueue, case_id="tiny", nbytes=4,
                           blocker=lambda: None,
                           blocker_receipt=blocker.receipt())
    saturated = payload["modes"]["stream_saturated"]
    assert saturated["trials"][0]["stream_saturated_qualified"] is False
    assert payload["qualified"] is False


def test_protocol_falls_back_to_host_timing_without_events():
    torch = FakeTorch(events=False)
    runtime = timing.TorchTimingRuntime(torch)
    assert runtime.available is False
    payload = timing.MeasurementProtocol(runtime).run(lambda: None, case_id="empty")

    def measured():
        import time

        time.sleep(0.0002)

    payload = timing.MeasurementProtocol(runtime).run(measured, case_id="host")
    assert payload["timer_source"] == "perf_counter_host_fallback"
    assert list(payload["modes"]) == ["eager"]
    assert payload["modes"]["eager"]["minimum_us"] > 0


def test_admit_context_binds_locks_and_allocates_the_ring():
    torch, context = _context()
    assert context["device"]["ordinal"] == 0
    assert torch.npu.calls[0] == "set_device:0"
    assert context["ring_plan"]["total_mib"] == 288
    assert context["ring"].allocated is True
    assert context["clock"]["repeats"] == timing.GEMM_LOCK_REPEATS
    assert context["clock"]["idle_dvfs_escaped"] is True
    assert torch.mm_calls == timing.GEMM_LOCK_REPEATS
    assert torch.allocations[0][0] == 288 * MIB
    timing.close_context(context)
    assert context["ring"].allocated is False


def test_admit_context_refuses_a_ring_above_the_s0_cap():
    torch = FakeTorch(free=6 * GIB)  # cap = min(8, 6-2) = 4 GiB
    context = timing.admit_context(torch=torch, torch_npu=torch.npu,
                                   environ={timing_env(): "0"},
                                   l2_bytes=1024 * MIB)  # 3 GiB ring fits the cap
    timing.close_context(context)
    torch = FakeTorch(free=6 * GIB)
    with pytest.raises(ProfilerUsageError, match="bench_vram_budget_exceeded"):
        timing.admit_context(torch=torch, torch_npu=torch.npu,
                             environ={timing_env(): "0"},
                             l2_bytes=2048 * MIB)  # 6 GiB ring > 4 GiB cap


def test_admit_context_can_skip_allocation_and_clock_lock():
    torch = FakeTorch()
    context = timing.admit_context(torch=torch, torch_npu=torch.npu,
                                   environ={timing_env(): "0"},
                                   l2_bytes=96 * MIB, allocate=False, lock=False)
    assert context["ring"].allocated is False
    assert context["clock"]["skipped"] is True
    assert torch.mm_calls == 0


def test_measurement_modes_thresholds():
    assert timing.measurement_modes("operator", observed_us=49.9) == (
        "eager", "stream_saturated")
    assert timing.measurement_modes("operator", observed_us=50.0) == ("eager",)
    assert timing.measurement_modes("collective", nbytes=4096) == (
        "eager", "stream_saturated")
    assert timing.measurement_modes("collective", nbytes=8192) == ("eager",)


def test_admit_context_without_l2_skips_the_cold_ring():
    torch = FakeTorch()
    context = timing.admit_context(torch=torch, torch_npu=torch.npu,
                                   environ={timing_env(): "0"}, l2_bytes=None)
    assert context["ring"] is None and context["ring_plan"] is None
    assert torch.allocations == []
    timing.close_context(context)


def test_lock_clock_checks_the_budget_before_allocating_gemms():
    torch = FakeTorch()
    receipt = timing.lock_clock(torch, ordinal=0, budget={"cap_bytes": 1024})
    assert receipt["skipped"] is True
    assert receipt["clock_warmup_completed"] is False
    assert receipt["idle_dvfs_escaped"] is False
    assert receipt["observed_clock_mhz"] is None
    assert receipt["basis"] == "30x4096_bf16_gemm_warmup"
    assert receipt["reason"] == "bench_clock_lock_over_budget"
    assert torch.mm_calls == 0


def test_lock_clock_reports_an_unreadable_clock_as_none():
    torch = FakeTorch()
    receipt = timing.lock_clock(torch, ordinal=0,
                                budget={"cap_bytes": 8 * 1024 * MIB})
    assert receipt["clock_warmup_completed"] is True
    assert receipt["idle_dvfs_escaped"] is True
    assert receipt["observed_clock_mhz"] is None
    assert torch.mm_calls == timing.GEMM_LOCK_REPEATS


def test_cold_ring_slice_bytes_rotates_and_hot_uses_offset_zero():
    plan = timing.cold_ring_plan(96 * MIB)
    ring = timing.ColdRing(FakeTorch(), plan, ordinal=0).allocate()
    first, first_receipt = ring.slice_bytes(128)
    second, second_receipt = ring.slice_bytes(128)
    assert first_receipt["offset_bytes"] == 0
    assert second_receipt["offset_bytes"] == plan["slot_stride_bytes"]
    assert first_receipt["view_fallback"] is True
    hot, hot_receipt = ring.slice_bytes(128, hot=True)
    assert hot_receipt["offset_bytes"] == 0
    assert hot_receipt["kind"] == "hot_control"
    with pytest.raises(ProfilerUsageError, match="bench_cold_ring_slice_too_large"):
        ring.slice_bytes(plan["slot_stride_bytes"] + 1)
    ring.close()
    with pytest.raises(ProfilerUsageError, match="bench_cold_ring_not_allocated"):
        ring.slice_bytes(128)


def test_stream_saturation_is_unqualified_without_a_calibrated_blocker():
    torch = FakeTorch()
    protocol = timing.MeasurementProtocol(timing.TorchTimingRuntime(torch))
    payload = protocol.run(lambda: torch.clock.__setattr__("ms", 0.02),
                           case_id="tiny", nbytes=4, blocker=lambda: None,
                           blocker_receipt={"estimated_ms": 2.0,
                                            "calibrated": False})
    assert "stream_saturated" in payload["modes"]
    assert payload["stream_saturated_available"] is False
    assert payload["qualified"] is False


def test_protocol_retains_enqueue_samples_and_runs_a_hot_control():
    torch = FakeTorch()
    protocol = timing.MeasurementProtocol(timing.TorchTimingRuntime(torch))
    ring = timing.ColdRing(torch, timing.cold_ring_plan(96 * MIB), ordinal=0).allocate()
    payload = protocol.run(
        lambda: torch.clock.__setattr__("ms", torch.clock.ms + 0.02),
        case_id="ring", nbytes=4, blocker=lambda: None,
        blocker_receipt={"estimated_ms": 2.5, "calibrated": True},
        cold_ring=ring,
        hot_enqueue=lambda: torch.clock.__setattr__("ms", torch.clock.ms + 0.01))
    eager = payload["modes"]["eager"]
    assert len(eager["enqueue_us_samples"]) == protocol.repeats * protocol.trials
    assert eager["enqueue_us"] is not None
    assert all(len(trial["enqueue_us_samples"]) == protocol.repeats
               for trial in eager["trials"])
    assert payload["cold_ring"]["allocated"] is True
    assert payload["hot_control"]["kind"] == "hot_control"
    assert payload["hot_control"]["offset_bytes"] == 0
    assert len(payload["hot_control"]["repeats_us"]) == protocol.repeats


def test_case_working_set_is_checked_against_the_budget():
    case = {"dtype": "bf16", "work_bytes": 4096,
            "shape": {"m": 1024, "k": 1024}}
    assert timing.estimate_working_set_bytes(case) >= 1024 * 1024
    assert timing.case_over_budget(case, {"cap_bytes": 1024}) is True
    assert timing.case_over_budget(case, {"cap_bytes": 64 * 1024 * 1024}) is False
    assert timing.case_over_budget({"estimated_bytes": 99}, {"cap_bytes": 1}) is True
