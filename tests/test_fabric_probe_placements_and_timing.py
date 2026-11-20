"""Fabric probe placements, AllToAllV splits, device timing and (h, f) fits.

[Role]
  Verify the declared ``a3_superpod`` 2x2/2x4 and A2 ``HCCS_8P_RING``
  placements, ``[0, d]`` rail-pair controls, unequal AllToAllV split matrices
  (uniform and skewed circulant, including non-power-of-two 6P/7P groups),
  ``LOCAL_RANK``-first binding, the stream-blocker/event timing helpers and the
  clean affine ``(h, f)`` route fit.

[Invariants]
  * No NPU or HCCL rank is created; the emitted script runs against fakes.
  * Split matrices conserve elements and satisfy ``recv_r[s] = send_s[r]``.

[Timeouts & Locks]
  Pure in-memory work and one bounded ``exec`` of the generated script.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` files.
"""

from __future__ import annotations

import json
import types

import pytest

from mindie_profiler import fabric_probe as probe
from mindie_profiler.events import ProfilerUsageError
from mindie_profiler.fabric_probe_fit import fit_calibrated_fabric_profile


def _script_namespace(plan):
    script = probe.emit_fabric_probe_script(plan)["script"]
    namespace: dict[str, object] = {"__name__": "fabric_probe_contract"}
    exec(compile(script, "<probe>", "exec"), namespace)
    return namespace


def test_placement_presets_cover_sio_hccs_sw_ring_and_superpod():
    expected = {
        "sio_pair": (2, 2, {"intra_package_sio"}),
        "hccs_sw_2rail": (4, 4, {"intra_node_hccs"}),
        "hccs_sw_4rail": (8, 8, {"intra_node_hccs_sw4"}),
        "a2_hccs_8p_mesh": (8, 8, {"a2_hccs_mesh_2p", "a2_hccs_mesh_4p",
                                   "a2_hccs_mesh_6p", "a2_hccs_mesh_7p",
                                   "a2_hccs_mesh_8p"}),
        "a2_hccs_8p_ring": (8, 8, {"intra_node_ring_2p", "intra_node_ring_4p",
                                   "intra_node_ring_6p", "intra_node_ring_7p"}),
        "a3_superpod_2x2": (4, 2, {"intra_package_sio.n0", "intra_package_sio.n1",
                                   "inter_node_superpod.rails"}),
        "a3_superpod_2x4": (8, 4, {"intra_package_sio.n0", "intra_package_sio.n1",
                                   "intra_package_sio.n2", "intra_package_sio.n3",
                                   "inter_node_superpod_2x4.rails"}),
    }
    assert set(probe.PLACEMENT_PRESETS) == set(expected)
    for name, (world, per_node, tiers) in expected.items():
        plan = probe.build_fabric_probe_plan(placement=name, sizes=[4096],
                                             ops=["all_reduce"], warmup=1,
                                             iterations=2)
        probe.validate_plan(plan)
        assert plan["world_size"] == world
        assert plan["ranks_per_node"] == per_node
        assert {tier["tier"] for tier in plan["tiers"]} == tiers
        assert plan["placement"] == name
        assert plan["placement_preset"]["declared"] is True
        assert plan["physical_verification"] is False
        if name in {"a2_hccs_8p_mesh", "a2_hccs_8p_ring"}:
            assert plan["dies_per_package"] == 1


def test_a2_hccs_8p_mesh_uses_zero_hop_per_pair_direct_mesh_and_ring_alias():
    plan = probe.build_fabric_probe_plan(
        placement="a2_hccs_8p_mesh",
        sizes=[4096],
        ops=["all_to_all_v"],
        warmup=1,
        iterations=2,
    )
    routes = {
        tier["tier"]: (tier["hops"], tier["rails"], tier.get("channel_semantics"), len(tier["ranks"]))
        for tier in plan["tiers"]
    }
    assert routes == {
        "a2_hccs_mesh_2p": (0, 1, "per_pair", 2),
        "a2_hccs_mesh_4p": (0, 3, "per_pair", 4),
        "a2_hccs_mesh_6p": (0, 5, "per_pair", 6),
        "a2_hccs_mesh_7p": (0, 6, "per_pair", 7),
        "a2_hccs_mesh_8p": (0, 7, "per_pair", 8),
    }
    assert probe.PLACEMENT_PRESETS["a2_hccs_8p_ring"]["legacy_alias_for"] == "a2_hccs_8p_mesh"


def test_a3_superpod_2x4_has_d0_rail_pair_controls():
    plan = probe.build_fabric_probe_plan(placement="a3_superpod_2x4", sizes=[4096],
                                         ops=["send_recv"], warmup=1, iterations=2)
    rail = plan["rail_pairs"]["inter_node_superpod_2x4.rails"]
    assert rail == [[0, 4], [1, 5], [2, 6], [3, 7]]
    assert plan["pairwise"]["pairs_by_tier"]["inter_node_superpod_2x4.rails"] == rail
    tier = next(tier for tier in plan["tiers"]
                if tier["tier"] == "inter_node_superpod_2x4.rails")
    assert tier["route"] == "inter_node_superpod_2x4"
    assert (tier["hops"], tier["rails"]) == (1, 4)


def test_a3_superpod_2x2_pairs_each_local_die_with_its_remote_peer():
    plan = probe.build_fabric_probe_plan(placement="a3_superpod_2x2", sizes=[4096],
                                         ops=["send_recv"], warmup=1, iterations=2)
    assert plan["rail_pairs"]["inter_node_superpod.rails"] == [[0, 2], [1, 3]]


def test_ring_placements_use_hop_counts_and_non_power_of_two_subsets():
    plan = probe.build_fabric_probe_plan(placement="a2_hccs_8p_ring", sizes=[4096],
                                         ops=["all_to_all_v"], warmup=1,
                                         iterations=2)
    routes = {tier["tier"]: (tier["hops"], tier["rails"], tier["ranks"])
              for tier in plan["tiers"]}
    assert routes["intra_node_ring_2p"][:2] == (1, 2)
    assert routes["intra_node_ring_4p"][:2] == (3, 2)
    assert routes["intra_node_ring_6p"][0] == 5
    assert routes["intra_node_ring_6p"][2] == [0, 1, 2, 3, 5, 6]
    assert len(routes["intra_node_ring_6p"][2]) == 6  # 6P is not a power of two
    assert routes["intra_node_ring_7p"][:2] == (6, 2)
    assert routes["intra_node_ring_7p"][2] == [0, 1, 2, 3, 5, 6, 7]


def test_topology_route_metadata_is_validated_against_its_label():
    topology = {"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1],
                           "hops": 2, "rails": 4}]}
    plan = probe.build_fabric_probe_plan(world_size=2, topology=topology,
                                         sizes=[4096], ops=["all_reduce"],
                                         warmup=1, iterations=2)
    assert plan["routes"]["intra_node_hccs"]["route_label"] == "intra_node_hccs(h=2,f=4)"
    assert plan["physical_verification"] is True
    tampered = json.loads(json.dumps(plan))
    tampered["routes"]["intra_node_hccs"]["hops"] = 0
    with pytest.raises(ProfilerUsageError, match="routes disagree"):
        probe.validate_plan(tampered)


def test_unknown_placement_and_unknown_tier_are_refused():
    with pytest.raises(ProfilerUsageError, match="unknown placement preset"):
        probe.build_fabric_probe_plan(placement="a5_pod")
    with pytest.raises(ProfilerUsageError, match="unknown topology tier"):
        probe.build_fabric_probe_plan(world_size=2, topology={
            "tiers": [{"tier": "nonsense", "ranks": [0, 1]}]})


def test_all_to_all_v_is_admitted_with_both_split_styles():
    plan = probe.build_fabric_probe_plan(
        world_size=8, ranks_per_node=8, sizes=[4096, 1 << 20],
        ops=[probe.ALL_TO_ALL_V], warmup=1, iterations=2)
    probe.validate_plan(plan)
    assert plan["all_to_all_v"]["styles"] == ["uniform", "skew_circulant"]
    assert plan["all_to_all_v"]["recv_equals_send_transpose"] is True
    for item in plan["admitted"]:
        assert item["op"] == probe.ALL_TO_ALL_V
        assert item["split_styles"] == ["uniform", "skew_circulant"]
        assert item["timing_modes"] == (
            ["eager", "stream_saturated"] if item["bytes"] <= 4096 else ["eager"])


@pytest.mark.parametrize("group_size", [2, 4, 5, 6, 7, 8])
@pytest.mark.parametrize("style", ["uniform", "skew_circulant"])
def test_split_matrices_conserve_elements_and_transpose(group_size, style):
    namespace = _script_namespace(probe.build_fabric_probe_plan(
        world_size=8, ranks_per_node=8, sizes=[4096],
        ops=[probe.ALL_TO_ALL_V], warmup=1, iterations=2))
    counts = namespace["_all_to_all_v_counts"]
    total = 4096 // 4
    send_by_rank = {}
    for rank in range(group_size):
        send, recv = counts(rank, group_size, total, style)
        assert sum(send) == total == sum(recv)
        assert all(isinstance(value, int) and value >= 0 for value in send + recv)
        send_by_rank[rank] = send
    for rank in range(group_size):
        _send, recv = counts(rank, group_size, total, style)
        assert recv == [send_by_rank[source][rank] for source in range(group_size)]
    if style == "skew_circulant" and group_size >= 2:
        assert any(counts(rank, group_size, total, style)[0] !=
                   counts(rank, group_size, total, "uniform")[0]
                   for rank in range(group_size))


def test_skew_moves_half_of_one_peer_allotment():
    namespace = _script_namespace(probe.build_fabric_probe_plan(
        world_size=8, ranks_per_node=8, sizes=[4096], ops=[probe.ALL_TO_ALL_V],
        warmup=1, iterations=2))
    uniform = namespace["_all_to_all_v_send"](0, 4, 100, "uniform")
    skewed = namespace["_all_to_all_v_send"](0, 4, 100, "skew_circulant")
    assert uniform == [25, 25, 25, 25]
    assert skewed[1] == 13 and skewed[2] == 37
    assert sum(skewed) == 100


def test_script_never_probes_device_count_and_binds_local_rank_first(tmp_path):
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    namespace = _script_namespace(plan)
    assert "torch.npu.device_count" not in probe.emit_fabric_probe_script(plan)["script"]
    calls: list[str] = []

    class FakeNpu:
        Event = None

        def set_device(self, ordinal):
            calls.append(f"set_device:{ordinal}")

        def device_count(self):  # pragma: no cover - must never be called
            calls.append("device_count")
            return 2

        def synchronize(self):
            calls.append("synchronize")

    torch = types.ModuleType("torch")
    torch.npu = FakeNpu()
    torch_npu = types.ModuleType("torch_npu")

    def _stop(**_kwargs):
        calls.append("init_process_group")
        raise RuntimeError("stop after the bind")

    distributed = types.ModuleType("torch.distributed")
    distributed.init_process_group = _stop
    torch.distributed = distributed
    import sys

    saved = {name: sys.modules.get(name) for name in
             ("torch", "torch_npu", "torch.distributed")}
    sys.modules.update({"torch": torch, "torch_npu": torch_npu,
                        "torch.distributed": distributed})
    try:
        monkey = pytest.MonkeyPatch()
        monkey.setenv("LOCAL_RANK", "1")
        monkey.setenv("RANK", "1")
        monkey.setenv("WORLD_SIZE", "2")
        try:
            code = namespace["main"](["--output", str(tmp_path / "out.jsonl"),
                                      "--abort-file", str(tmp_path / "abort.json")])
        finally:
            monkey.undo()
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    assert code == 3  # the injected init failure is reported, not raised
    assert calls[0] == "set_device:1"
    assert "device_count" not in calls


def test_physical_die_allowlist_is_fail_closed_in_the_script():
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    plan["allowed_phy_ids"] = [12, 13]
    namespace = _script_namespace(plan)
    check = namespace["_check_physical_die"]
    with pytest.raises(Exception, match="allowed physical ids"):
        check(0, [12, 13])  # vllm_ascend is absent, so the die is unresolvable
    assert check(0, None) == {"physical_id": None, "allowed": None}


def test_host_timer_fallback_without_events():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    namespace = _script_namespace(plan)
    torch = types.SimpleNamespace(npu=types.SimpleNamespace())
    timer = namespace["_new_timer"](torch)
    assert timer["mode"] == "host_fallback"
    host_begin, timed = namespace["_begin"](timer, True)
    sample = namespace["_finish"](timer, host_begin, timed, True)
    assert timed is False
    assert sample["timing_mode"] == "host_fallback"
    assert sample["duration_us"] >= 0.0


class FakeEvent:
    def __init__(self, clock):
        self.clock = clock
        self.stamp = None

    def record(self, _stream=None):
        self.stamp = self.clock.now

    def synchronize(self):
        return None

    def elapsed_time(self, other):
        return other.stamp - self.stamp


def _device_timer_namespace():
    namespace = _script_namespace(probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2))
    return namespace


def test_device_timer_blocks_the_measured_stream_and_qualifies_enqueue():
    namespace = _device_timer_namespace()
    clock = types.SimpleNamespace(now=0.0)

    class Stream:
        def __init__(self):
            self.waits = 0

        def wait_event(self, _event):
            self.waits += 1

    class Npu:
        def __init__(self):
            self.current = Stream()
            self.blocker = Stream()

        def Event(self, enable_timing=False):
            return FakeEvent(clock)

        def Stream(self):
            return self.blocker

        def current_stream(self):
            return self.current

    torch = types.SimpleNamespace(npu=Npu())
    timer = namespace["_new_timer"](torch)
    assert timer["mode"] == "device_event"
    namespace["_calibrate_blocker"](torch, timer) if False else None
    timer.update({"unit": lambda: clock.__setattr__("now", clock.now + 0.05),
                  "unit_ms": 0.05, "repeats": 50, "calibrated": True})
    begin, timed = namespace["_begin"](timer, True)
    assert timed is True
    assert torch.npu.current.waits == 1  # start dependency on the blocker
    clock.now += 0.02  # the measured call itself
    sample = namespace["_finish"](timer, begin, timed, True,
                                  namespace["_blocker_receipt"](timer)["estimated_ms"])
    assert sample["timing_mode"] == "stream_saturated"
    assert sample["duration_us"] == pytest.approx(20.0)
    assert sample["qualified"] is True
    receipt = namespace["_blocker_receipt"](timer)
    assert receipt["estimated_ms"] == pytest.approx(2.5)
    assert receipt["target_ms"] == probe.BLOCKER_TARGET_MS


def test_device_timer_disqualifies_when_host_enqueue_exceeds_the_blocker():
    namespace = _device_timer_namespace()
    clock = types.SimpleNamespace(now=0.0)

    class Npu:
        def Event(self, enable_timing=False):
            return FakeEvent(clock)

        def Stream(self):
            return types.SimpleNamespace(wait_event=lambda _event: None)

        def current_stream(self):
            return types.SimpleNamespace(wait_event=lambda _event: None)

    timer = namespace["_new_timer"](types.SimpleNamespace(npu=Npu()))
    timer.update({"unit": lambda: None, "unit_ms": 1.0, "repeats": 1,
                  "calibrated": True})
    begin, timed = namespace["_begin"](timer, True)
    import time

    time.sleep(0.003)  # 3 ms of host enqueue beyond the 1 ms blocker
    clock.now += 0.02
    sample = namespace["_finish"](timer, begin, timed, True, 1.0)
    assert sample["qualified"] is False
    assert sample["timing_mode"] == "stream_saturated"


def test_plan_rejects_admitted_items_with_unknown_timing_modes():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    tampered = json.loads(json.dumps(plan))
    tampered["admitted"][0]["timing_modes"] = ["turbo"]
    with pytest.raises(ProfilerUsageError, match="unknown timing mode"):
        probe.validate_plan(tampered)


def test_plan_rejects_more_ops_than_supported():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    tampered = json.loads(json.dumps(plan))
    tampered["ops"] = ["all_reduce"] * 7
    with pytest.raises(ProfilerUsageError):
        probe.validate_plan(tampered)


def _route_samples(tiers, *, alpha=5.0, beta=0.2, sizes=(4096, 65536, 4194304),
                   rank_offset=0.0):
    samples = []
    for tier in tiers:
        hops, rails = tier["hops"], tier["rails"]
        for size in sizes:
            for rank in tier["ranks"]:
                latency = alpha * (1 + hops) + beta * size / 1000.0 / rails
                samples.append({
                    "tier": tier["tier"], "op": "all_reduce", "bytes": size,
                    "latency_us": latency + rank_offset * rank,
                    "group_size": len(tier["ranks"]),
                    "group_ranks": list(tier["ranks"]), "rank": rank,
                    "validated": True, "protocol": tier["protocol"],
                    "repeat_index": 0, "timing_mode": "eager"})
    return samples


def test_route_model_recovers_alpha_and_per_rail_bandwidth():
    plan = probe.build_fabric_probe_plan(
        placement="a3_superpod_2x4", sizes=[4096, 65536, 4194304],
        ops=["all_reduce"], warmup=1, iterations=2)
    tiers = [tier for tier in plan["tiers"]
             if tier["route"] in {"intra_package_sio", "inter_node_superpod_2x4"}]
    profile = fit_calibrated_fabric_profile(plan, _route_samples(tiers))
    model = profile["route_models"]["all_reduce"]
    assert model["fit_quality"] == "affine_hops_rails"
    assert model["alpha_us"] == pytest.approx(5.0, rel=1e-6)
    assert model["beta_ns_per_byte"] == pytest.approx(0.2, rel=1e-6)
    assert model["bandwidth_gbps"] == pytest.approx(5.0, rel=1e-6)
    assert model["identifiable"] is True
    sio = profile["tiers"]["intra_package_sio.n0"]["operations"]["all_reduce"]
    assert sio["route"] == {"route": "intra_package_sio", "hops": 0, "rails": 1,
                            "route_label": "intra_package_sio(h=0,f=1)"}
    assert sio["route_model"]["alpha_us"] == pytest.approx(5.0, rel=1e-6)
    rails = profile["tiers"]["inter_node_superpod_2x4.rails"]["operations"][
        "all_reduce"]
    assert rails["route"]["hops"] == 1 and rails["route"]["rails"] == 4


def test_cross_rank_max_is_taken_per_repeat_and_timing_mode_is_kept_apart():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096, 65536], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    ranks = [0, 1]
    samples = []
    for size in (4096, 65536):
        for repeat in (0, 1):
            for rank in ranks:
                samples.append({
                    "tier": "intra_node_hccs", "op": "all_reduce", "bytes": size,
                    "latency_us": 10.0 + repeat + rank,
                    "group_size": 2, "group_ranks": ranks, "rank": rank,
                    "validated": True, "protocol": "HCCS", "repeat_index": repeat,
                    "timing_mode": "eager"})
    profile = fit_calibrated_fabric_profile(plan, samples)
    condition = profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"][
        "conditions"][0]
    assert condition["timing_mode"] == "eager"
    assert condition["cross_rank_max_of"] == 8
    assert condition["raw"]["4096"]["min_us"] == pytest.approx(11.0)
    assert condition["raw"]["4096"]["max_us"] == pytest.approx(12.0)


def test_unqualified_stream_saturation_is_rejected_not_pooled():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    samples = []
    for size in (4096, 65536):
        for rank in (0, 1):
            samples.append({
                "tier": "intra_node_hccs", "op": "all_reduce", "bytes": size,
                "latency_us": 12.0, "group_size": 2, "group_ranks": [0, 1],
                "rank": rank, "validated": True, "protocol": "HCCS",
                "timing_mode": "stream_saturated", "saturated_qualified": False})
    profile = fit_calibrated_fabric_profile(plan, samples)
    reasons = {item["reason"] for item in profile["rejected_samples"]}
    assert "stream_saturation_unqualified" in reasons
    assert profile["status"] == "partial"


def test_route_model_is_empty_when_a_condition_has_no_points():
    plan = probe.build_fabric_probe_plan(world_size=2, ranks_per_node=2,
                                         sizes=[4096], ops=["all_reduce"],
                                         topology={"tiers": [
                                             {"tier": "intra_node_hccs",
                                              "ranks": [0, 1]}]},
                                         warmup=1, iterations=2)
    profile = fit_calibrated_fabric_profile(plan, [{
        "tier": "intra_node_hccs", "op": "all_reduce", "bytes": 4096,
        "latency_us": 12.0, "group_size": 2, "group_ranks": [0, 1], "rank": 0,
        "validated": True, "protocol": "HCCS"}])
    assert profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"][
        "route_model"]["fit_quality"] == "affine_hops_rails"


def test_plan_and_cli_carry_the_physical_die_allowlist(capsys):
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2, allowed_phy_ids=(13, 12, 13))
    assert plan["allowed_phy_ids"] == [12, 13]
    probe.validate_plan(plan)
    tampered = json.loads(json.dumps(plan))
    tampered["allowed_phy_ids"] = [4096]
    with pytest.raises(ProfilerUsageError):
        probe.validate_plan(tampered)
    assert probe.main(["--world-size", "2", "--ranks-per-node", "2",
                       "--allowed-phy-ids", "12..15", "--duration-s", "30"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["allowed_phy_ids"] == [12, 13, 14, 15]


class _FakeBuffer:
    def __init__(self, elements):
        self._elements = elements

    def numel(self):
        return self._elements


class _FakeWork:
    def __init__(self):
        self.waited = 0

    def wait(self):
        self.waited += 1


class _FakeDist:
    def __init__(self):
        self.calls = []

    def all_to_all_single(self, out, buffer, **kwargs):
        work = _FakeWork()
        self.calls.append((out, buffer, kwargs, work))
        return work


def test_call_once_all_to_all_v_sends_unequal_splits_and_waits():
    namespace = _script_namespace(probe.build_fabric_probe_plan(
        world_size=8, ranks_per_node=8, sizes=[4096], ops=[probe.ALL_TO_ALL_V],
        warmup=1, iterations=2))
    dist = _FakeDist()
    torch = types.SimpleNamespace()
    output = _FakeBuffer(1024)
    payload = _FakeBuffer(1024)
    finished = namespace["_call_once"](
        torch, dist, probe.ALL_TO_ALL_V, payload, output, "group", None, 0, 0,
        [0, 1, 2, 3, 4, 5], "skew_circulant")
    assert finished is True
    out, buf, kwargs, work = dist.calls[0]
    assert out is output and buf is payload
    assert sum(kwargs["input_split_sizes"]) == 1024
    assert sum(kwargs["output_split_sizes"]) == 1024
    assert kwargs["input_split_sizes"] == [
        namespace["_all_to_all_v_send"](0, 6, 1024, "skew_circulant")[peer]
        for peer in range(6)]
    assert work.waited == 1


def test_rail_pair_rounds_are_explicit_and_sequential():
    plan = probe.build_fabric_probe_plan(
        placement="a3_superpod_2x2", sizes=[4096], ops=["send_recv"],
        warmup=1, iterations=2)
    tier = "inter_node_superpod.rails"
    assert plan["pair_rounds"][tier] == [[[0, 2]], [[0, 3]], [[0, 2], [1, 3]]]
    plan4 = probe.build_fabric_probe_plan(
        placement="a3_superpod_2x4", sizes=[4096], ops=["send_recv"],
        warmup=1, iterations=2)
    tier4 = "inter_node_superpod_2x4.rails"
    assert plan4["pair_rounds"][tier4] == [
        [[0, 4]], [[0, 5]], [[0, 6]], [[0, 7]], [[0, 4], [1, 5], [2, 6], [3, 7]]]
    rail_items = [item for item in plan4["admitted"] if item["tier"] == tier4]
    assert rail_items and all(item.get("pair_rounds") for item in rail_items)


def test_all_to_all_v_requires_element_aligned_sizes():
    with pytest.raises(ProfilerUsageError, match="multiples of"):
        probe.build_fabric_probe_plan(world_size=4, ranks_per_node=4,
                                      sizes=[4098], ops=[probe.ALL_TO_ALL_V],
                                      warmup=1, iterations=2)


def test_stream_saturated_blocker_and_split_styles_are_costed():
    eager_only = probe.build_fabric_probe_plan(
        world_size=4, ranks_per_node=4, sizes=[4096], ops=["all_reduce"],
        warmup=1, iterations=1000, timing_modes=["eager"], duration_s=60.0)
    saturated = probe.build_fabric_probe_plan(
        world_size=4, ranks_per_node=4, sizes=[4096], ops=["all_reduce"],
        warmup=1, iterations=1000, duration_s=60.0)
    assert saturated["admitted"][0]["timing_modes"] == [
        "eager", "stream_saturated"]
    assert (saturated["admission"]["estimated_s"]
            > eager_only["admission"]["estimated_s"])
    a2av = probe.build_fabric_probe_plan(
        world_size=4, ranks_per_node=4, sizes=[4096],
        ops=[probe.ALL_TO_ALL_V], warmup=1, iterations=1000,
        duration_s=60.0)
    assert a2av["admitted"][0]["split_styles"] == ["uniform", "skew_circulant"]


def test_host_fallback_samples_are_diagnostic_only_and_never_override():
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096, 65536],
        ops=["all_reduce"], topology={"tiers": [
            {"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    samples = []
    for size in (4096, 65536):
        for rank in (0, 1):
            samples.append({
                "schema": "mindie-fabric-probe-sample/3",
                "tier": "intra_node_hccs", "op": "all_reduce", "bytes": size,
                "latency_us": 12.0, "group_size": 2, "group_ranks": [0, 1],
                "rank": rank, "validated": True, "protocol": "HCCS",
                "repeat_index": 0, "timing_mode": "host_fallback",
                "device_completion_us": None, "saturated_qualified": None})
    profile = fit_calibrated_fabric_profile(plan, samples)
    assert profile["status"] == "partial"
    assert profile["usable_for_link_override"] is False
    reasons = {item["reason"] for item in profile["rejected_samples"]}
    assert "host_fallback" in reasons
    condition = profile["tiers"]["intra_node_hccs"]["operations"][
        "all_reduce"]["conditions"][0]
    assert condition["qualified"] is False
    assert condition["diagnostic_only"] is True


def test_incomplete_rank_sets_block_calibration_per_repeat():
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    samples = [
        {"schema": "mindie-fabric-probe-sample/3",
         "tier": "intra_node_hccs", "op": "all_reduce", "bytes": 4096,
         "latency_us": 12.0, "group_size": 2, "group_ranks": [0, 1],
         "rank": 0, "validated": True, "protocol": "HCCS",
         "repeat_index": 0, "timing_mode": "eager",
         "device_completion_us": 12.0, "saturated_qualified": None}]
    profile = fit_calibrated_fabric_profile(plan, samples)
    assert profile["status"] == "partial"
    assert profile["run_evidence_blocked"] is True
    reasons = {item["reason"] for item in profile["rejected_samples"]}
    assert "incomplete_rank_set" in reasons
    assert profile["usable_for_link_override"] is False


def test_per_timing_mode_fits_are_preserved_separately():
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096, 65536],
        ops=["all_reduce"], topology={"tiers": [
            {"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    samples = []
    for mode, base in (("eager", 10.0), ("stream_saturated", 20.0)):
        for size in (4096, 65536):
            for rank in (0, 1):
                samples.append({
                    "schema": "mindie-fabric-probe-sample/3",
                    "tier": "intra_node_hccs", "op": "all_reduce",
                    "bytes": size, "latency_us": base + size / 1000.0,
                    "group_size": 2, "group_ranks": [0, 1], "rank": rank,
                    "validated": True, "protocol": "HCCS", "repeat_index": 0,
                    "timing_mode": mode, "device_completion_us": base,
                    "saturated_qualified": True})
    profile = fit_calibrated_fabric_profile(plan, samples)
    operation = profile["tiers"]["intra_node_hccs"]["operations"]["all_reduce"]
    assert sorted(operation["timing_modes"]) == ["eager", "stream_saturated"]
    assert operation["timing_modes"]["eager"]["alpha_us"] == pytest.approx(
        10.0, rel=1e-6)
    assert operation["timing_modes"]["stream_saturated"][
        "alpha_us"] == pytest.approx(20.0, rel=1e-6)
    assert operation["primary_timing_mode"] == "eager"


def test_send_recv_repeats_pair_both_ranks_of_the_same_pair():
    plan = probe.build_fabric_probe_plan(
        placement="a3_superpod_2x2", sizes=[4096, 65536], ops=["send_recv"],
        warmup=1, iterations=2)
    pair = plan["rail_pairs"]["inter_node_superpod.rails"][0]
    samples = []
    for size in (4096, 65536):
        for rank, direction in ((pair[0], "send"), (pair[1], "recv")):
            samples.append({
                "schema": "mindie-fabric-probe-sample/3",
                "tier": "inter_node_superpod.rails", "op": "send_recv",
                "bytes": size, "latency_us": 15.0 + rank, "rank": rank,
                "group_size": 4, "group_ranks": [0, 1, 2, 3],
                "protocol": "HCCS", "repeat_index": 0, "direction": direction,
                "timing_mode": "eager", "device_completion_us": 15.0,
                "validated": True})
    profile = fit_calibrated_fabric_profile(plan, samples)
    reasons = {item["reason"] for item in profile["rejected_samples"]}
    assert "incomplete_rank_set" not in reasons
    conditions = profile["tiers"]["inter_node_superpod.rails"]["operations"][
        "send_recv"]["conditions"]
    assert conditions and conditions[0]["size_count"] == 2


def test_device_timer_runs_the_blocker_on_its_private_stream():
    namespace = _device_timer_namespace()
    clock = types.SimpleNamespace(now=0.0)
    units: list[str] = []

    class Stream:
        def __init__(self, name):
            self.name = name
            self.waits = 0

        def wait_event(self, _event):
            self.waits += 1

    class Context:
        def __init__(self, npu, stream):
            self.npu, self.stream = npu, stream

        def __enter__(self):
            self.npu.active = self.stream

        def __exit__(self, *_exc):
            self.npu.active = None

    class Npu:
        def __init__(self):
            self.current = Stream("measurement")
            self.blocker = Stream("blocker")
            self.active = None

        def Event(self, enable_timing=False):
            return FakeEvent(clock)

        def Stream(self):
            return self.blocker

        def current_stream(self):
            return self.current

        def stream(self, target):
            return Context(self, target)

    npu = Npu()
    torch = types.SimpleNamespace(npu=npu)
    timer = namespace["_new_timer"](torch)
    assert timer["torch"] is torch
    timer.update({"unit": lambda: units.append(npu.active.name),
                  "unit_ms": 0.05, "repeats": 5, "calibrated": True})
    _begin, timed = namespace["_begin"](timer, True)
    assert timed is True
    assert units == ["blocker"] * 5  # never the measurement stream
    assert npu.current.waits == 1
    assert npu.blocker.waits == 0


def test_default_a2_mesh_ten_second_budget_retains_affordable_combinations():
    plan = probe.build_fabric_probe_plan(placement="a2_hccs_8p_mesh", duration_s=10.0)
    probe.validate_plan(plan)
    assert plan["budget"]["within_budget"] is True
    assert plan["admission"]["admitted"] is True
    assert plan["admission"]["estimated_s"] <= plan["budget_s"]
    assert plan["admitted"]
    assert plan["run_id"]


def test_equal_all_to_all_requires_a_divisible_group_payload():
    plan = probe.build_fabric_probe_plan(
        placement="a2_hccs_8p_mesh", sizes=[4096], ops=["all_to_all"],
        warmup=1, iterations=2)
    indivisible = {(item["tier"], item["bytes"]) for item in plan["unmeasured"]
                   if item.get("reason") == "indivisible_group_payload"}
    assert indivisible == {("a2_hccs_mesh_6p", 4096),
                           ("a2_hccs_mesh_7p", 4096)}
    assert {item["tier"] for item in plan["admitted"]} == {
        "a2_hccs_mesh_2p", "a2_hccs_mesh_4p", "a2_hccs_mesh_8p"}
    namespace = _script_namespace(plan)

    class FakeBuffer:
        def fill_(self, _value):
            return self

    torch = types.SimpleNamespace(
        zeros=lambda _count, **_kwargs: FakeBuffer(), float32="float32")
    with pytest.raises(namespace["ProfilerUsageError"],
                       match="must divide group_size"):
        namespace["_buffers"](torch, 4096, 6, "all_to_all", 0)


def test_run_identity_and_held_out_split_are_required_for_calibration():
    plan = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096, 65536],
        ops=["all_reduce"], topology={"tiers": [
            {"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    base = {
        "schema": "mindie-fabric-probe-sample/3", "tier": "intra_node_hccs",
        "op": "all_reduce", "group_size": 2, "group_ranks": [0, 1],
        "protocol": "HCCS", "repeat_index": 0, "timing_mode": "eager",
        "device_completion_us": 12.0, "validated": True,
        "saturated_qualified": None}
    split_run, heldout = [], []
    for size in (4096, 65536):
        split_run.extend([
            {**base, "bytes": size, "latency_us": 12.0, "rank": 0,
             "run_id": "run-a"},
            {**base, "bytes": size, "latency_us": 13.0, "rank": 1,
             "run_id": "run-b"}])
        for rank in (0, 1):
            heldout.append({**base, "bytes": size, "latency_us": 12.0 + rank,
                            "rank": rank, "run_id": "run-c",
                            "split": "heldout"})
    split_profile = fit_calibrated_fabric_profile(plan, split_run)
    assert split_profile["status"] == "partial"
    assert split_profile["run_evidence_blocked"] is True
    assert split_profile["usable_for_link_override"] is False
    assert "incomplete_rank_set" in {
        item["reason"] for item in split_profile["rejected_samples"]}
    heldout_profile = fit_calibrated_fabric_profile(plan, heldout)
    condition = heldout_profile["tiers"]["intra_node_hccs"]["operations"][
        "all_reduce"]["conditions"][0]
    assert heldout_profile["status"] == "partial"
    assert heldout_profile["usable_for_link_override"] is False
    assert condition["qualified"] is False
    assert condition["size_count"] == 0


def test_send_recv_direct_pair_uses_one_rail_not_the_mesh_fanout():
    plan = probe.build_fabric_probe_plan(
        placement="a2_hccs_8p_mesh", sizes=[4096, 65536, 1048576],
        ops=["send_recv"], warmup=1, iterations=2)
    tier = next(item for item in plan["tiers"]
                if item["tier"] == "a2_hccs_mesh_8p")
    assert tier["rails"] == 7
    samples = []
    for size in (4096, 65536, 1048576):
        for rank in (0, 1):
            samples.append({
                "schema": "mindie-fabric-probe-sample/3", "tier": tier["tier"],
                "op": "send_recv", "bytes": size,
                "latency_us": 3.0 + size / 50000.0, "rank": rank,
                "group_size": 8, "group_ranks": list(tier["ranks"]),
                "pair": [0, 1], "repeat_index": 0, "protocol": "HCCS",
                "timing_mode": "eager", "device_completion_us": 3.0,
                "validated": True, "split": "train"})
    profile = fit_calibrated_fabric_profile(plan, samples)
    model = profile["route_models"]["send_recv"]
    assert model["alpha_us"] == pytest.approx(3.0, rel=1e-6)
    assert model["bandwidth_gbps"] == pytest.approx(50.0, rel=1e-6)
    block = profile["tiers"]["a2_hccs_mesh_8p"]["operations"]["send_recv"]
    assert block["route_model"]["bandwidth_gbps"] == pytest.approx(
        50.0, rel=1e-6)


def test_distinct_default_launch_run_ids_and_uncalibrated_blocker_disqualification():
    plan_a = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096, 65536], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    plan_b = probe.build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096, 65536], ops=["all_reduce"],
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1]}]},
        warmup=1, iterations=2)
    assert plan_a == plan_b
    ns_a = _script_namespace(plan_a)
    ns_b = _script_namespace(plan_b)
    # Two launches without --run-id assign distinct execution _RUN_IDs and sample_ids
    ns_a["_RUN_ID"] = f"{plan_a['plan_id']}-launcha"
    ns_b["_RUN_ID"] = f"{plan_b['plan_id']}-launchb"
    sid_a = ns_a["_sample_id"]("intra_node_hccs", "all_reduce", 4096, 0, 0, None, "eager")
    sid_b = ns_b["_sample_id"]("intra_node_hccs", "all_reduce", 4096, 0, 0, None, "eager")
    assert sid_a != sid_b

    namespace = _device_timer_namespace()
    clock = types.SimpleNamespace(now=0.0)

    class Npu:
        def Event(self, enable_timing=False):
            return FakeEvent(clock)

        def Stream(self):
            return types.SimpleNamespace(wait_event=lambda _event: None)

        def current_stream(self):
            return types.SimpleNamespace(wait_event=lambda _event: None)

    timer = namespace["_new_timer"](types.SimpleNamespace(npu=Npu()))
    # Measured 1.1ms * 2 = 2.2ms < 95% of 2.5ms -> calibrated=False, 0 blocker calls
    timer.update({"unit": lambda: None, "unit_ms": 1.1, "repeats": 2, "calibrated": False})
    begin, timed = namespace["_begin"](timer, True)
    clock.now += 0.01
    sample = namespace["_finish"](timer, begin, timed, True, 2.2)
    assert sample["timing_mode"] == "stream_saturated"
    assert sample["qualified"] is False
