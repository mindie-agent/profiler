"""Topology-qualified HCCL probe planning and emitted-script control.

[Role]
  Build a deadline-bounded sweep over explicit physical tiers (intra-package
  die, intra-node HCCS, inter-node RoCE) with declared rank groups, estimate and
  admit only affordable samples, emit the standalone probe script and dispatch
  the fitting CLI.

[Invariants]
  * Tiers are explicit rank groups.  Derived tiers are scheduling assumptions
    labelled ``unverified_rank_group`` unless an explicit topology is supplied.
  * ``duration_s`` is a measurement budget that includes warmup, validation and
    synchronization; a separate bounded cleanup allowance is reported.
  * Python-level checks admit work and validate samples before/after each step.
    A kernel-hung C++ HCCL call can only be stopped by the outer subprocess or
    the daemon cleanup watchdog after ``cleanup_allowance_s``.
  * At least one iteration is admitted or the sample is explicitly marked
    ``unmeasured``; the planner never forces three unaffordable iterations.
  * The estimate multiplies by the operation count and includes warmup, sync,
    initialization and cleanup.
  * The emitted script is syntax checked and contains no package imports.

[Timeouts & Locks]
  Planning is in-memory.  The emitted script owns a monotonic deadline plus a
  ``destroy_process_group`` watchdog (daemon timer and POSIX ``signal.alarm``);
  a kernel-hung C++ call still requires the outer subprocess watchdog.

[Side-Effect Policy]
  Writes only explicitly requested plan/script/profile paths.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import contextlib
import json
import inspect
import math
import os
from pathlib import Path
import pprint
import signal
import time
from typing import Any

from .events import ProfilerUsageError
from .fabric_probe_fit import (
    PROFILE_SCHEMA, fit_calibrated_fabric_profile, parse_fabric_probe_samples,
)
from .fabric_probe_samples import SPLIT_HELPERS
from . import repro_atomic_io as atomic_io
from .repro_atomic_io import path_exists
from .repro_values import bounded_count, bounded_mapping, bounded_sequence, load_cli_json

PLAN_SCHEMA = "mindie-fabric-probe-plan/3"
DEFAULT_SIZES = tuple(2 ** exponent for exponent in range(12, 29))
DEFAULT_OPS = ("all_reduce", "all_gather", "reduce_scatter", "all_to_all", "send_recv")
ALL_TO_ALL_V = "all_to_all_v"
SUPPORTED_OPS = DEFAULT_OPS + (ALL_TO_ALL_V,)
SMALL_COLLECTIVE_BYTES = 4096
DEVICE_TIMING_MODES = ("eager", "stream_saturated")
BLOCKER_TARGET_MS = 2.5
ALL_TO_ALL_V_STYLES = ("uniform", "skew_circulant")
ALL_TO_ALL_V_ELEMENT_BYTES = 4
SKEW_FRACTION = 0.5
MAX_TIERS = 8
# (h, f) route classes: h = switch stages crossed, f = parallel rails used.
# route: (alpha_us, beta_ns_per_byte, link, protocol, hops, rails)
_ROUTE_TABLE = {
    "intra_package_die": (2.0, 0.05, "hccs", "HCCS", 0, 1),
    "intra_package_sio": (2.0, 0.05, "hccs", "HCCS", 0, 1),
    "intra_node_hccs": (8.0, 0.10, "hccs", "HCCS", 0, 2),
    "intra_node_hccs_sw4": (8.0, 0.10, "hccs", "HCCS", 0, 4),
    "inter_node_roce": (30.0, 0.55, "roce", "RoCE", 1, 1),
    "inter_node_superpod": (4.0, 0.10, "hccs", "HCCS", 1, 2),
    "inter_node_superpod_2x4": (4.0, 0.10, "hccs", "HCCS", 1, 4),
    "intra_node_ring_2p": (3.0, 0.08, "hccs", "HCCS", 1, 2),
    "intra_node_ring_4p": (5.0, 0.08, "hccs", "HCCS", 3, 2),
    "intra_node_ring_6p": (7.0, 0.08, "hccs", "HCCS", 5, 2),
    "intra_node_ring_7p": (8.0, 0.08, "hccs", "HCCS", 6, 2),
    "a2_hccs_8p_ring": (7.0, 0.08, "hccs", "HCCS", 6, 2),
}
ROUTE_CLASSES = {
    name: {"alpha_us": alpha, "beta_ns_per_byte": beta, "link": link,
           "protocol": protocol, "hops": hops, "rails": rails}
    for name, (alpha, beta, link, protocol, hops, rails) in _ROUTE_TABLE.items()
}
_RAIL_RANKS = list(range(8))
# Declared sparse placements; a host map is still required for an override.
def _placement(world: int, per_node: int, nodes: int, tiers: Any,
               *, dies_per_package: int = 2) -> dict[str, Any]:
    return {"world_size": world, "ranks_per_node": per_node, "nodes": nodes,
            "dies_per_package": dies_per_package, "tiers": tiers}
PLACEMENT_PRESETS = {
    "sio_pair": _placement(2, 2, 1, ({"tier": "intra_package_sio", "ranks": [0, 1]},)),
    "hccs_sw_2rail": _placement(4, 4, 1, ({"tier": "intra_node_hccs",
                                           "ranks": [0, 1, 2, 3]},)),
    "hccs_sw_4rail": _placement(8, 8, 1, ({"tier": "intra_node_hccs_sw4",
                                           "ranks": _RAIL_RANKS},)),
    "a2_hccs_8p_ring": _placement(8, 8, 1, (
        {"tier": "intra_node_ring_2p", "ranks": [0, 1]},
        {"tier": "intra_node_ring_4p", "ranks": [0, 1, 2, 3]},
        {"tier": "intra_node_ring_6p", "ranks": [0, 1, 2, 3, 5, 6]},
        {"tier": "intra_node_ring_7p", "ranks": [0, 1, 2, 3, 5, 6, 7]}),
        dies_per_package=1),
    "a3_superpod_2x2": _placement(4, 2, 2, (
        {"tier": "intra_package_sio.n0", "ranks": [0, 1]},
        {"tier": "intra_package_sio.n1", "ranks": [2, 3]},
        {"tier": "inter_node_superpod.rails", "ranks": [0, 1, 2, 3],
         "pairs": [[0, 2], [1, 3]], "rail_pairs": True,
         "pair_rounds": [[[0, 2]], [[0, 3]], [[0, 2], [1, 3]]]})),
    "a3_superpod_2x4": _placement(8, 4, 2, (
        {"tier": "intra_package_sio.n0", "ranks": [0, 1]},
        {"tier": "intra_package_sio.n1", "ranks": [2, 3]},
        {"tier": "intra_package_sio.n2", "ranks": [4, 5]},
        {"tier": "intra_package_sio.n3", "ranks": [6, 7]},
        {"tier": "inter_node_superpod_2x4.rails", "ranks": _RAIL_RANKS,
         "pairs": [[0, 4], [1, 5], [2, 6], [3, 7]], "rail_pairs": True,
         "pair_rounds": [[[0, 4]], [[0, 5]], [[0, 6]], [[0, 7]],
                         [[0, 4], [1, 5], [2, 6], [3, 7]]]})),
}
SYNC_OVERHEAD_US = 5.0
INIT_OVERHEAD_US = 8000.0
GROUP_CREATE_OVERHEAD_US = 2000.0
VALIDATION_OVERHEAD_US = 500.0
def _route_metadata(name: str, item: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Resolve ``(h, f)`` route metadata; labels may carry an instance suffix."""
    item = item or {}
    route = str(item.get("route") or name.split(".", 1)[0])
    priors = ROUTE_CLASSES.get(route)
    if priors is None:
        raise ProfilerUsageError(f"unknown topology tier {name!r}")
    hops = item.get("hops", priors["hops"])
    rails = item.get("rails", priors["rails"])
    for label, value in (("hops", hops), ("rails", rails)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ProfilerUsageError(f"topology {label} must be a non-negative integer")
    return {"route": route, "hops": int(hops), "rails": max(1, int(rails)),
            "link": str(item.get("link") or priors["link"]),
            "protocol": str(item.get("protocol") or priors["protocol"]),
            "route_label": f"{route}(h={int(hops)},f={max(1, int(rails))})"}
def _default_topology(world_size: int, ranks_per_node: int,
                      dies_per_package: int, nodes: int) -> list[dict[str, Any]]:
    tiers, ranks = [], list(range(world_size))
    if dies_per_package >= 2 and world_size >= 2:
        tiers.append({"tier": "intra_package_die", "ranks": [0, 1], "available": True})
    if ranks_per_node >= 2:
        group = ranks[:min(ranks_per_node, world_size)]
        tiers.append({"tier": "intra_node_hccs", "ranks": group,
                      "available": len(group) >= 2})
    if nodes >= 2 and ranks_per_node >= 1 and world_size > ranks_per_node:
        group = [index * ranks_per_node for index in range(nodes)
                 if index * ranks_per_node < world_size]
        tiers.append({"tier": "inter_node_roce", "ranks": group,
                      "available": len(group) >= 2})
    return [{**tier, **_route_metadata(tier["tier"], tier),
             "pairs": _pairs(tier["ranks"]), "rail_pairs": False}
            for tier in tiers]
def _explicit_topology(topology: Any, world_size: int) -> list[dict[str, Any]]:
    if not isinstance(topology, dict) or not isinstance(topology.get("tiers"), list):
        raise ProfilerUsageError("topology must be {'tiers': [{'tier','ranks',...}]}")
    tiers = []
    for item in bounded_sequence(topology["tiers"], "tiers", MAX_TIERS):
        if not isinstance(item, dict):
            raise ProfilerUsageError("topology tier must be an object")
        name = str(item.get("tier") or "")
        if not name or len(name) > 64:
            raise ProfilerUsageError("topology tier label must be 1..64 characters")
        route = _route_metadata(name, item)
        ranks = [bounded_count(rank, "topology rank", 0, world_size - 1)
                 for rank in bounded_sequence(item.get("ranks", ()), "ranks", 4096)]
        if len(set(ranks)) != len(ranks) or any(tier["tier"] == name for tier in tiers):
            raise ProfilerUsageError("topology has duplicate ranks or tiers")
        ranks.sort()
        explicit_pairs = item.get("pairs")
        pairs = (_validated_pairs(explicit_pairs, world_size)
                 if explicit_pairs is not None else _pairs(ranks))
        rounds = (_validated_pair_rounds(item.get("pair_rounds"), world_size)
                  if item.get("pair_rounds") is not None else [])
        tiers.append({"tier": name, "ranks": ranks, **route, "pairs": pairs,
                      "pair_rounds": rounds,
                      "rail_pairs": bool(item.get("rail_pairs", False)),
                      "available": len(ranks) >= 2 and bool(item.get("available", True))})
    return tiers
def _validated_pairs(pairs: Any, world_size: int) -> list[list[int]]:
    """Rail-pair controls such as ``[0, d]`` for every cross-package peer."""
    result: list[list[int]] = []
    for pair in bounded_sequence(pairs, "pairs", 2048):
        values = bounded_sequence(pair, "pair", 2)
        if len(values) != 2:
            raise ProfilerUsageError("pair must contain two ranks")
        first, second = (bounded_count(value, "pair rank", 0, world_size - 1)
                         for value in values)
        if first == second:
            raise ProfilerUsageError("a rail pair needs two distinct ranks")
        result.append([first, second])
    return result
def _validated_pair_rounds(rounds: Any, world_size: int) -> list[list[list[int]]]:
    """Sequential pair rounds: every rank runs the same gate sequence."""
    result: list[list[list[int]]] = []
    for round_ in bounded_sequence(rounds, "pair_rounds", 32):
        result.append(_validated_pairs(round_, world_size))
    return result
def _pairs(ranks: list[int]) -> list[list[int]]:
    return [[ranks[i], ranks[i + 1]] for i in range(0, len(ranks) - 1, 2)]
def _finite(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProfilerUsageError("fabric probe requires non-boolean numeric parameters")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ProfilerUsageError("fabric probe requires finite numeric parameters") from exc
    if not math.isfinite(number):
        raise ProfilerUsageError("fabric probe requires finite numeric parameters")
    return number
def _resolve_placement(world_size: Any, ranks_per_node: Any,
                       dies_per_package: Any, nodes: Any,
                       placement: Any) -> tuple[int, int, int, int, Any]:
    preset = None
    if placement is not None:
        preset = PLACEMENT_PRESETS.get(str(placement))
        if preset is None:
            raise ProfilerUsageError(f"unknown placement preset {placement!r}")
    def pick(value: Any, key: str, default: int) -> int:
        return int(value) if value is not None else (
            int(preset[key]) if preset is not None else default)
    world, per_node, dies = (pick(world_size, "world_size", 16),
                             pick(ranks_per_node, "ranks_per_node", 8),
                             pick(dies_per_package, "dies_per_package", 2))
    node_count = (pick(nodes, "nodes", 1) if nodes is not None or preset is not None
                  else (world + per_node - 1) // per_node)
    return world, per_node, dies, node_count, preset
def _timing_modes(size: int, requested: Any) -> list[str]:
    """Eager plus stream-saturated for small calls and 4 KiB collectives."""
    if requested is None:
        return (list(DEVICE_TIMING_MODES) if int(size) <= SMALL_COLLECTIVE_BYTES
                else [DEVICE_TIMING_MODES[0]])
    modes = [str(mode) for mode in bounded_sequence(
        requested, "timing_modes", len(DEVICE_TIMING_MODES))]
    if not modes or any(mode not in DEVICE_TIMING_MODES for mode in modes):
        raise ProfilerUsageError(f"unknown timing modes: {modes}")
    return modes
def build_fabric_probe_plan(
    *,
    world_size: int | None = None,
    ranks_per_node: int | None = None,
    duration_s: float = 60.0,
    sizes: tuple[int, ...] | list[int] | None = None,
    ops: tuple[str, ...] | list[str] | None = None,
    warmup: int = 5,
    iterations: int = 20,
    topology: dict[str, Any] | None = None,
    dies_per_package: int | None = None,
    nodes: int | None = None,
    placement: str | None = None,
    timing_modes: tuple[str, ...] | list[str] | None = None,
    allowed_phy_ids: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Admit work: <=4096 ranks/nodes/dies, <=10**6 loop steps, <=64 sizes.
    Sizes are 4 KiB..256 MiB, operations <=6 and physical tiers <=8. A named
    ``placement`` supplies a declared sparse ``a3_superpod`` or ``a2`` layout;
    an explicit ``topology`` still wins and is the only form that carries a
    physical host map.  Resource limits are validated before materialization.
    """
    if topology is not None:
        topology = bounded_mapping(topology, "topology")
    phy_ids = None
    if allowed_phy_ids is not None:
        phy_ids = sorted({bounded_count(value, "allowed physical id", 0, 4095)
                          for value in bounded_sequence(allowed_phy_ids,
                                                        "allowed_phy_ids", 4096)})
    world_size, ranks_per_node, dies_per_package, nodes, preset = _resolve_placement(
        world_size, ranks_per_node, dies_per_package, nodes, placement)
    bounded_count(world_size, "world_size", 2, 4096)
    bounded_count(ranks_per_node, "ranks_per_node", 1, 4096)
    bounded_count(dies_per_package, "dies_per_package", 1, 4096)
    bounded_count(nodes, "nodes", 1, 4096)
    bounded_count(warmup, "warmup")
    bounded_count(iterations, "iterations", 1)
    duration_s = _finite(duration_s)
    if not 0 < duration_s <= 600:
        raise ProfilerUsageError("fabric probe duration_s must be in (0, 600]")
    size_list = sorted({bounded_count(size, "size bytes", 4096, 268_435_456)
        for size in bounded_sequence(DEFAULT_SIZES if sizes is None else sizes, "sizes", 64)})
    if not size_list:
        raise ProfilerUsageError("fabric probe needs at least one size >= 4 KiB")
    op_list = list(bounded_sequence(DEFAULT_OPS if ops is None else ops, "ops",
                                    len(SUPPORTED_OPS)))
    unknown = [op for op in op_list if op not in SUPPORTED_OPS]
    if unknown:
        raise ProfilerUsageError(f"unknown probe operations: {unknown}")
    if ALL_TO_ALL_V in op_list:
        misaligned = [size for size in size_list
                      if size % ALL_TO_ALL_V_ELEMENT_BYTES != 0]
        if misaligned:
            raise ProfilerUsageError(
                f"all_to_all_v sizes must be multiples of "
                f"{ALL_TO_ALL_V_ELEMENT_BYTES} bytes: {misaligned[:4]}")
    declared_topology = topology is not None
    if preset is not None and topology is None:
        topology = {"tiers": [dict(tier) for tier in preset["tiers"]]}
    tiers = (_explicit_topology(topology, world_size) if topology is not None
             else _default_topology(world_size, ranks_per_node,
                                    dies_per_package, nodes))
    for tier in tiers:  # Expanded collective buffers fit the 4 GiB cap.
        if any(op in {"all_gather", "reduce_scatter", "all_to_all", ALL_TO_ALL_V}
               for op in op_list):
            factor = 2 if ALL_TO_ALL_V in op_list else 1
            bounded_count(max(size_list) * len(tier["ranks"]) * factor,
                          "group buffer bytes", 0, 1 << 32)
    cleanup_s = min(2.0, max(0.05, duration_s * 0.1))
    measurement_s = max(0.0, duration_s - cleanup_s)
    init_s = INIT_OVERHEAD_US / 1e6
    group_create_s = GROUP_CREATE_OVERHEAD_US * max(1, len(tiers)) / 1e6
    budget_us = max(0.0, (duration_s - cleanup_s - init_s - group_create_s) * 1e6)
    estimated_us = 0.0
    warmup_us = 0.0
    measure_us = 0.0
    validation_count = 0
    admitted: list[dict[str, Any]] = []
    unmeasured: list[dict[str, Any]] = []
    per_tier: dict[str, Any] = {}
    for tier in tiers:
        prior = ROUTE_CLASSES[tier["route"]]
        tier_iters: dict[str, int] = {}
        admitted_count = 0
        if not tier.get("available"):
            unmeasured.append({"tier": tier["tier"], "reason": "tier_not_realizable"})
            per_tier[tier["tier"]] = {"iterations_per_size": {}, "admitted": 0,
                                      "status": "unavailable"}
            continue
        for op in op_list:
            pairs = tier.get("pairs") or _pairs(tier["ranks"])
            participants = (len(pairs) * 2 if op == "send_recv"
                            else len(tier["ranks"]))
            if participants < 2:
                unmeasured.append({"tier": tier["tier"], "op": op,
                                   "reason": "insufficient_participants"})
                continue
            for size in size_list:
                modes = _timing_modes(size, timing_modes)
                predicted = prior["alpha_us"] + prior["beta_ns_per_byte"] * size / 1000.0
                sample_cost = (predicted + SYNC_OVERHEAD_US) * len(modes)
                if "stream_saturated" in modes:
                    sample_cost += BLOCKER_TARGET_MS * 1000.0
                if op == ALL_TO_ALL_V:
                    sample_cost *= len(ALL_TO_ALL_V_STYLES)
                affordable = int(budget_us / max(sample_cost, 1e-6))
                count = min(int(iterations), max(0, affordable - int(warmup) - 1))
                if count < 1:
                    unmeasured.append({"tier": tier["tier"], "op": op, "bytes": size,
                                       "reason": "budget_exhausted"})
                    continue
                combo_us = (int(warmup) + count) * sample_cost
                if estimated_us + combo_us > budget_us + INIT_OVERHEAD_US:
                    unmeasured.append({"tier": tier["tier"], "op": op, "bytes": size,
                                       "reason": "budget_exhausted"})
                    continue
                estimated_us += combo_us
                warmup_us += int(warmup) * sample_cost
                measure_us += count * sample_cost
                validation_count += 1
                entry = {"tier": tier["tier"], "op": op, "bytes": size,
                         "iterations": count, "warmup": int(warmup),
                         "regime": "isolated", "timing_modes": modes,
                         "route": tier["route"], "hops": tier["hops"],
                         "rails": tier["rails"]}
                if tier.get("rail_pairs"):
                    entry["pairs"] = [list(pair) for pair in pairs]
                    if tier.get("pair_rounds"):
                        entry["pair_rounds"] = tier["pair_rounds"]
                if op == ALL_TO_ALL_V:
                    entry["split_styles"] = list(ALL_TO_ALL_V_STYLES)
                admitted.append(entry)
                tier_iters[str(size)] = max(tier_iters.get(str(size), 0), count)
                admitted_count += 1
        per_tier[tier["tier"]] = {
            "iterations_per_size": tier_iters, "admitted": admitted_count,
            "status": "admitted" if admitted_count else "unmeasured",
            "op_count": len(op_list),
        }
    validation_s = validation_count * VALIDATION_OVERHEAD_US / 1e6
    warmup_s = warmup_us / 1e6
    measured_s = measure_us / 1e6
    estimated_total_s = (init_s + group_create_s + warmup_s + measured_s
                         + validation_s + cleanup_s)
    within_budget = estimated_total_s <= float(duration_s) + 1e-12
    admitted_ok = bool(admitted) and within_budget
    if not within_budget and admitted:
        admitted = []
        for tier, block in per_tier.items():
            block["admitted"] = 0
            block["status"] = "unmeasured"
            block["iterations_per_size"] = {}
        unmeasured.append({"reason": "estimated_cost_exceeds_budget",
                           "estimated_s": round(estimated_total_s, 6),
                           "budget_s": float(duration_s)})
    status = ("admitted" if admitted_ok
              else "rejected" if not within_budget else "unmeasured")
    topology_label = ("explicit_topology" if declared_topology
                      else "declared_placement" if preset is not None
                      else "unverified_rank_group")
    breakdown = {"init_cost_s": round(init_s, 6),
                 "group_create_s": round(group_create_s, 6),
                 "warmup_s": round(warmup_s, 6),
                 "measure_s": round(measured_s, 6),
                 "validation_s": round(validation_s, 6),
                 "cleanup_s": round(cleanup_s, 6)}
    return {
        "schema": PLAN_SCHEMA, "status": status,
        "world_size": int(world_size), "ranks_per_node": int(ranks_per_node),
        "nodes": int(nodes), "dies_per_package": int(dies_per_package),
        "budget_s": float(duration_s),
        "topology_label": topology_label,
        "topology_source": ("explicit_host_map" if declared_topology
                            else "declared_placement" if preset is not None
                            else "rank_count_assumption"),
        "physical_verification": declared_topology,
        "deadline": {"mode": "time.monotonic", "duration_s": float(duration_s),
                     "measurement_budget_s": round(measurement_s, 6),
                     "cleanup_allowance_s": round(cleanup_s, 6),
                     "init_cost_s": round(init_s, 6),
                     "group_create_s": round(group_create_s, 6),
                     "validation_s": round(validation_s, 6),
                     "includes_warmup": True, "includes_validation": True,
                     "includes_synchronization": True,
                     "max_wall_s": float(duration_s)},
        "admission": {"admitted": admitted_ok,
                      "reason": None if admitted_ok else "estimated_cost_exceeds_budget",
                      "estimated_s": round(estimated_total_s, 6),
                      "budget_s": float(duration_s),
                      "breakdown_s": breakdown},
        "warmup": max(0, int(warmup)), "max_iterations": int(iterations),
        "sizes_bytes": size_list, "ops": op_list,
        "tiers": [{**tier, "group_size": len(tier["ranks"]),
                   "pairs": tier["pairs"],
                   "physical_verification": declared_topology,
                   "topology_label": topology_label} for tier in tiers],
        "topology": topology or {"mode": "derived",
                                 "ranks_per_node": int(ranks_per_node),
                                 "nodes": int(nodes),
                                 "dies_per_package": int(dies_per_package)},
        "iterations": per_tier,
        "admitted": admitted, "unmeasured": unmeasured,
        "estimated_measurement_s": round(measured_s, 6),
        "estimated_s": round(estimated_total_s, 6),
        "estimated_breakdown_s": breakdown,
        "cleanup_allowance_s": round(cleanup_s, 6),
        "pairwise": {"op": "send_recv",
                     "pairs_by_tier": {tier["tier"]: tier["pairs"] for tier in tiers},
                     "pair_rounds_by_tier": {tier["tier"]: tier["pair_rounds"]
                                             for tier in tiers
                                             if tier.get("pair_rounds")}},
        "multi_rank": {"ops": [op for op in op_list if op != "send_recv"],
                       "world_size": int(world_size)},
        "routes": {tier["tier"]: {"route": tier["route"], "hops": tier["hops"],
                                  "rails": tier["rails"], "protocol": tier["protocol"],
                                  "link": tier["link"],
                                  "route_label": tier["route_label"]}
                   for tier in tiers},
        "rail_pairs": {tier["tier"]: [list(pair) for pair in tier["pairs"]]
                       for tier in tiers if tier.get("rail_pairs")},
        "pair_rounds": {tier["tier"]: [[list(pair) for pair in round_]
                                       for round_ in tier["pair_rounds"]]
                        for tier in tiers if tier.get("pair_rounds")},
        "timing": {"device_event": True, "host_enqueue_qualified": True,
                   "max_across_ranks": True, "blocker_target_ms": BLOCKER_TARGET_MS,
                   "modes": list(DEVICE_TIMING_MODES),
                   "small_collective_bytes": SMALL_COLLECTIVE_BYTES,
                   "host_fallback": "declared when torch.npu.Event is unavailable"},
        "all_to_all_v": {"styles": list(ALL_TO_ALL_V_STYLES),
                         "element_bytes": ALL_TO_ALL_V_ELEMENT_BYTES,
                         "skew_fraction": SKEW_FRACTION,
                         "rule": "quotient_remainder_circulant_then_half_peer_transfer",
                         "recv_equals_send_transpose": True},
        "placement": placement, "allowed_phy_ids": phy_ids,
        "placement_preset": ({"name": placement, "declared": True,
                              "physical_verification": declared_topology}
                             if placement is not None else None),
    }
def validate_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    plan = bounded_mapping(plan, "plan")
    if not isinstance(plan, Mapping) or plan.get("schema") != PLAN_SCHEMA:
        raise ProfilerUsageError(f"expected plan schema {PLAN_SCHEMA}")
    for field in ("world_size", "sizes_bytes", "ops", "tiers", "admitted"):
        if field not in plan:
            raise ProfilerUsageError(f"plan missing {field}")
    world = bounded_count(plan["world_size"], "world_size", 2, 4096)
    for field in ("ranks_per_node", "dies_per_package", "nodes"):
        bounded_count(plan.get(field, 1), field, 1, 4096)
    bounded_count(plan.get("warmup", 0), "warmup")
    bounded_count(plan.get("max_iterations", 1), "max_iterations", 1)
    for size in bounded_sequence(plan["sizes_bytes"], "sizes", 64):
        bounded_count(size, "size bytes", 4096, 268_435_456)
    if any(str(op) not in SUPPORTED_OPS for op in
           bounded_sequence(plan["ops"], "ops", len(SUPPORTED_OPS))):
        raise ProfilerUsageError("plan contains an unsupported probe operation")
    tiers = _explicit_topology({"tiers": plan["tiers"]}, world)
    for tier, normalized in zip(plan["tiers"], tiers):
        group = bounded_count(tier.get("group_size", len(normalized["ranks"])), "group_size", 0, world)
        if group != len(normalized["ranks"]):
            raise ProfilerUsageError("group_size does not match topology ranks")
        if (tier.get("route"), tier.get("hops"), tier.get("rails")) != (
                normalized["route"], normalized["hops"], normalized["rails"]):
            raise ProfilerUsageError("tier route metadata does not match its label")
        entry = (plan.get("routes") or {}).get(tier["tier"])
        if entry is not None and (entry.get("route"), entry.get("hops"),
                                  entry.get("rails")) != (
                normalized["route"], normalized["hops"], normalized["rails"]):
            raise ProfilerUsageError("plan routes disagree with the tier entries")
        for pair in bounded_sequence(tier.get("pairs", ()), "pairs", 2048):
            if len(bounded_sequence(pair, "pair", 2)) != 2:
                raise ProfilerUsageError("pair must contain two ranks")
            for rank in pair:
                bounded_count(rank, "pair rank", 0, world - 1)
        for round_ in bounded_sequence(tier.get("pair_rounds", ()) or (),
                                       "pair_rounds", 32):
            for pair in bounded_sequence(round_, "pair round", 2048):
                if len(bounded_sequence(pair, "pair", 2)) != 2:
                    raise ProfilerUsageError("pair must contain two ranks")
                for rank in pair:
                    bounded_count(rank, "pair rank", 0, world - 1)
    for value in plan.get("allowed_phy_ids") or ():
        bounded_count(value, "allowed physical id", 0, 4095)
    for item in bounded_sequence(plan["admitted"], "admitted", 960):
        bounded_count(item.get("iterations", 0), "iterations")
        bounded_count(item.get("warmup", plan.get("warmup", 0)), "warmup")
        bounded_count(item.get("bytes"), "size bytes", 4096, 268_435_456)
        group = next((len(tier["ranks"]) for tier in tiers if tier["tier"] == item.get("tier")), 0)
        modes = bounded_sequence(item.get("timing_modes", DEVICE_TIMING_MODES),
                                 "timing_modes", len(DEVICE_TIMING_MODES))
        if any(str(mode) not in DEVICE_TIMING_MODES for mode in modes):
            raise ProfilerUsageError("admitted item has an unknown timing mode")
        if item.get("op") in {"all_gather", "reduce_scatter", "all_to_all", ALL_TO_ALL_V}:
            factor = 2 if item.get("op") == ALL_TO_ALL_V else 1
            bounded_count(item["bytes"] * group * factor, "group buffer bytes", 0, 1 << 32)
    if plan.get("deadline", {}).get("mode") != "time.monotonic":
        raise ProfilerUsageError("plan deadline must be a monotonic deadline")
    admission = plan.get("admission") or {}
    for section in (plan, plan.get("deadline") or {}, admission):
        for key, value in section.items():
            if key.endswith("_s") and value is not None and not isinstance(value, Mapping):
                _finite(value)
    if admission.get("admitted") and _finite(admission.get(
            "estimated_s", 0.0)) > _finite(admission.get("budget_s", 0.0)) + 1e-12:
        raise ProfilerUsageError(
            "plan admits work whose estimated cost exceeds its budget")
    return dict(plan)
from .fabric_probe_script_template import PROBE_TEMPLATE  # noqa: E402
def emit_fabric_probe_script(plan: dict[str, Any], *,
                             output_path: str | Path | None = None) -> dict[str, Any]:
    plan = validate_plan(plan)
    script = PROBE_TEMPLATE.replace("__PLAN__", pprint.pformat(
        plan, sort_dicts=True, width=100))
    script = script.replace("__IO_HELPERS__", "\n".join(inspect.getsource(getattr(atomic_io, name))
        for name in ("_cleanup_scope", "_retry_cleanup", "_recover_fd_inode", "_close_owned_fd",
                     "_stream_raw", "_borrow_stream_fd", "_close_stream")))
    script = script.replace("__SPLIT_HELPERS__", SPLIT_HELPERS)
    script = script.replace("__COUNT_HELPER__", inspect.getsource(bounded_count))
    try:
        compile(script, "<fabric_probe>", "exec")
    except SyntaxError as exc:
        raise ProfilerUsageError(f"fabric probe script failed syntax validation: {exc}") from exc
    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script, encoding="utf-8", newline="\n")
    return {"schema": "mindie-fabric-probe-script/2", "status": "ok",
            "syntax_ok": True,
            "line_count": len(script.splitlines()),
            "output_path": None if output_path is None else str(Path(output_path)),
            "script": script}
def _read_abort_record(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None
def _process_reaped(proc: Any) -> bool:
    if proc.returncode is None:
        return False
    handle = getattr(proc, "_handle", None) if os.name == "nt" else None
    if isinstance(handle, int) and not isinstance(handle, bool):
        import _winapi
        return _winapi.WaitForSingleObject(int(handle), 0) == 0
    return True
def _emergency_reap_children(children: Any, hard_end: float) -> None:
    """Round-robin kill/reap, sharing one deadline and preserving the primary."""
    # Even an expired deadline gets one short emergency slice, never one per PID.
    with contextlib.suppress(BaseException):
        end = max(hard_end, time.monotonic() + (0.25 if os.name == "nt" else 0.02))
        pending = list(children)
        while pending and time.monotonic() < end:
            survivors = []
            for proc in pending:
                with contextlib.suppress(BaseException):
                    proc.poll()
                if _process_reaped(proc):
                    continue
                if proc.returncode is None:
                    with contextlib.suppress(BaseException):
                        proc.kill()
                        proc.wait(timeout=0)
                    with contextlib.suppress(BaseException):
                        if proc.returncode is None and os.name == "nt":
                            import _winapi
                            _winapi.TerminateProcess(int(proc._handle), 1)
                        elif proc.returncode is None:
                            pid = getattr(proc, "pid", None)
                            if isinstance(pid, int) and pid > 0:
                                os.kill(pid, signal.SIGKILL)
                handle = getattr(proc, "_handle", None) if os.name == "nt" else None
                if isinstance(handle, int) and not isinstance(handle, bool):
                    import _winapi
                    if _winapi.WaitForSingleObject(int(handle), 2) == 0 and proc.returncode is None:
                        proc.returncode = _winapi.GetExitCodeProcess(int(handle))
                if not _process_reaped(proc):
                    survivors.append(proc)
            pending = survivors
            if pending:
                time.sleep(max(0, min(0.002, end - time.monotonic())))
def supervise_probe_processes(procs: Any, abort_file: str | Path | None = None,
                              wall_budget_s: float = 60.0,
                              poll_interval_s: float = 0.01) -> dict[str, Any]:
    """One failed peer stops every remaining rank process.
    ``ProcessGroup.abort()`` cannot interrupt every C++ HCCL kernel, so the
    emitted watcher is paired with this supervisor for real launches.
    """
    processes = list(bounded_sequence(() if procs is None else procs, "processes", 4096))
    if not processes:
        raise ProfilerUsageError("supervisor requires at least one process")
    budget = max(0.001, _finite(wall_budget_s))
    poll = max(0.001, min(_finite(poll_interval_s), 0.25))
    started = time.monotonic()
    deadline = started + budget
    # Cleanup shares the wall budget; only a small scheduling tolerance is added.
    cleanup_slice = min(0.04, 0.25 * budget)
    terminate_at = max(started, deadline - cleanup_slice)
    kill_at = max(terminate_at, deadline - 0.5 * cleanup_slice)
    hard_end = deadline + 0.03
    status, reason, codes = "completed", None, {}
    terminated: list[int] = []
    reaped = False
    def poll_once() -> None:
        nonlocal status, reason
        for index, proc in enumerate(processes):
            code = proc.poll()
            if code is not None:
                codes.setdefault(index, int(code))
                if code != 0 and status == "completed":
                    status, reason = "peer_aborted", f"rank_{index}_exit_{code}"
        if (status == "completed" and abort_file
                and path_exists(str(abort_file))):
            status, reason = "peer_aborted", "abort_record"
    def sleep_bounded(seconds: float, end: float) -> None:
        remaining = min(float(seconds), end - time.monotonic())
        if remaining > 0:
            time.sleep(remaining)
    try:
        while True:
            poll_once()
            if status != "completed":
                break
            if all(proc.poll() is not None for proc in processes):
                break
            now = time.monotonic()
            if now >= terminate_at:
                break
            sleep_bounded(poll, terminate_at)
        poll_once()
        if (status == "completed"
                and not all(proc.poll() is not None for proc in processes)):
            status, reason = "deadline_exceeded", "wall_budget_exceeded"
        # An abort-file writer is itself a child: give it a short bounded
        # chance to publish its exit status before terminating blocked peers.
        if status == "peer_aborted":
            settle_end = min(kill_at, time.monotonic() + 0.1)
            while time.monotonic() < settle_end:
                poll_once()
                if all(proc.poll() is not None for proc in processes):
                    break
                sleep_bounded(min(0.005, poll), settle_end)
        for index, proc in enumerate(processes):
            if proc.poll() is None:
                terminated.append(index)
                try:
                    proc.terminate()
                except TimeoutError:
                    raise
                except OSError:
                    pass
        grace_end = min(kill_at, time.monotonic() + 0.1)
        while time.monotonic() < grace_end:
            poll_once()
            if all(proc.poll() is not None for proc in processes):
                break
            sleep_bounded(min(0.005, poll), grace_end)
        for proc in processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                except TimeoutError:
                    raise
                except OSError:
                    pass
        for proc in processes:
            while proc.poll() is None and time.monotonic() < hard_end:
                try:
                    proc.wait(timeout=max(
                        0.001, min(0.01, hard_end - time.monotonic())))
                except TimeoutError:
                    raise
                except Exception:
                    pass
        reaped = all(
            proc.poll() is not None and _process_reaped(proc)
            for proc in processes
        )
        poll_once()
        for index, proc in enumerate(processes):
            if index not in codes and proc.returncode is not None:
                codes[index] = int(proc.returncode)
        payload = {"status": status,
                   "exit_code": 0 if status == "completed" else 2,
                   "exit_codes": dict(sorted(codes.items())),
                   "terminated_ranks": terminated,
                   "elapsed_s": round(time.monotonic() - started, 6)}
        record = _read_abort_record(abort_file)
        if record is not None:
            payload["abort_record"] = record
        return payload
    finally:
        if not reaped:
            _emergency_reap_children(processes, hard_end)
def build_fabric_probe_plan_from_args(args: argparse.Namespace) -> dict[str, Any]:
    topology = None
    if args.topology:
        topology = load_cli_json(args.topology)
    phy_ids = None
    from .bench.abi import resolve_allowed_phy_ids
    resolved = resolve_allowed_phy_ids(args.allowed_phy_ids)
    phy_ids = list(resolved) if resolved else None
    return build_fabric_probe_plan(
        world_size=args.world_size, ranks_per_node=args.ranks_per_node,
        duration_s=args.duration_s, topology=topology, placement=args.placement,
        dies_per_package=args.dies_per_package, nodes=args.nodes,
        ops=args.ops, timing_modes=args.timing_mode, allowed_phy_ids=phy_ids,
        warmup=args.warmup, iterations=args.iterations)
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler fabric-probe",
        description="Plan, emit, or fit bounded multi-tier HCCL fabric bandwidth and latency sweeps.",
        allow_abbrev=False,
    )
    parser.add_argument("--world-size", type=int, default=None, help="ranks across all nodes (default: 16 or the preset)")
    parser.add_argument("--ranks-per-node", type=int, default=None, help="ranks per host (default: 8 or the preset)")
    parser.add_argument("--dies-per-package", type=int, default=None, help="dies per package (default: 2)")
    parser.add_argument("--nodes", type=int, default=None, help="explicit node count override")
    parser.add_argument("--placement", default=None, choices=tuple(PLACEMENT_PRESETS), help="declared sparse placement preset")
    parser.add_argument("--ops", action="append", default=None, choices=SUPPORTED_OPS, help="operation subset (repeatable)")
    parser.add_argument("--timing-mode", action="append", default=None, choices=DEVICE_TIMING_MODES, help="device timing modes (repeatable)")
    parser.add_argument("--duration-s", type=float, default=60.0, help="total wall-clock budget (default: 60)")
    parser.add_argument("--warmup", type=int, default=5, help="untimed warmup iterations per size")
    parser.add_argument("--iterations", type=int, default=20, help="timed iterations per size")
    parser.add_argument("--topology", default=None, help="explicit topology JSON (host-verified rank map)")
    parser.add_argument("--allowed-phy-ids", default=None, help="physical die allowlist enforced after the bind")
    parser.add_argument("--samples", default=None, help="probe JSON/JSONL output to fit")
    parser.add_argument("--plan", default=None, help="write the sweep plan JSON here")
    parser.add_argument("--script", default=None, help="write the standalone script here")
    parser.add_argument("--output", "-o", default=None, help="write plan, script receipt, or fitted profile")
    args = parser.parse_args(list(argv or ()))
    plan = build_fabric_probe_plan_from_args(args)
    payload: dict[str, Any] = plan
    if args.script:
        payload = emit_fabric_probe_script(plan, output_path=args.script)
    if args.samples:
        records = parse_fabric_probe_samples(
            Path(args.samples).read_text(encoding="utf-8"))
        payload = fit_calibrated_fabric_profile(plan, records)
        if args.output is None:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
            return 0 if payload["status"] == "calibrated" else 2
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.plan:
        Path(args.plan).write_text(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0 if (payload.get("status") in {"admitted", "calibrated", "partial", "unmeasured", "ok"}
                 or payload.get("syntax_ok") is True) else 2
__all__ = [ "DEFAULT_OPS", "DEFAULT_SIZES", "PLAN_SCHEMA", "PROFILE_SCHEMA", "build_fabric_probe_plan", "build_fabric_probe_plan_from_args", "emit_fabric_probe_script", "fit_calibrated_fabric_profile", "main", "parse_fabric_probe_samples", "supervise_probe_processes", "validate_plan", ]
if __name__ == "__main__":
    raise SystemExit(main())
