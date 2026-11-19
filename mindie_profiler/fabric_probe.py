"""Topology-qualified HCCL probe planning and emitted-script control.

[Role]
  Build a deadline-bounded sweep over explicit physical tiers (intra-package
  die, intra-node HCCS mesh/switch, inter-node RoCE/SuperPod) with declared
  rank groups, estimate and admit only affordable samples, emit the standalone
  probe script and dispatch the fitting CLI.

[Invariants]
  * Tiers are explicit rank groups.  Derived tiers are scheduling assumptions
    labelled ``unverified_rank_group`` unless an explicit topology is supplied.
  * ``a2_hccs_8p_mesh`` models A2's ``K_8`` direct peer mesh (``hops=0``,
    ``channel_semantics="per_pair"``), while ``a2_hccs_8p_ring`` remains a
    backwards-compatible preset alias.
  * ``duration_s`` includes warmup, validation, synchronization and a bounded
    cleanup allowance; unaffordable work is marked ``unmeasured``.
  * The emitted script is syntax checked and contains no package imports.

[Timeouts & Locks]
  Planning is in-memory.  The emitted script owns a monotonic deadline plus a
  ``destroy_process_group`` watchdog.

[Side-Effect Policy]
  Writes only explicitly requested plan/script/profile paths.
"""

from __future__ import annotations

import argparse, json, math
from collections.abc import Mapping, Sequence
from functools import lru_cache
from pathlib import Path
from typing import Any

from .events import ProfilerUsageError
from .fabric_probe_fit import (
    PROFILE_SCHEMA, fit_calibrated_fabric_profile, parse_fabric_probe_samples,
)
from .fabric_probe_supervisor import render_fabric_probe_script, supervise_probe_processes
from .repro_values import bounded_count, bounded_mapping, bounded_sequence, load_cli_json

_PRESETS_PATH = Path(__file__).parent / "knowledge" / "fabric_probe_presets.json"


@lru_cache(maxsize=1)
def _load_presets() -> Mapping[str, Any]:
    return json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))


_PRESETS = _load_presets()
_DEFAULTS = _PRESETS["defaults"]

PLAN_SCHEMA = "mindie-fabric-probe-plan/3"
DEFAULT_SIZES = tuple(2 ** int(exp) for exp in _DEFAULTS["size_exponents"])
DEFAULT_OPS = ("all_reduce", "all_gather", "reduce_scatter", "all_to_all", "send_recv")
ALL_TO_ALL_V = "all_to_all_v"
SUPPORTED_OPS = DEFAULT_OPS + (ALL_TO_ALL_V,)
SMALL_COLLECTIVE_BYTES = int(_DEFAULTS["small_collective_bytes"])
DEVICE_TIMING_MODES = ("eager", "stream_saturated")
BLOCKER_TARGET_MS = float(_DEFAULTS["blocker_target_ms"])
ALL_TO_ALL_V_STYLES = ("uniform", "skew_circulant")
ALL_TO_ALL_V_ELEMENT_BYTES = int(_DEFAULTS["all_to_all_v_element_bytes"])
SKEW_FRACTION = float(_DEFAULTS["skew_fraction"])
MAX_TIERS = int(_DEFAULTS["max_tiers"])

ROUTE_CLASSES: dict[str, dict[str, Any]] = {
    str(name): dict(entry) for name, entry in _PRESETS["route_classes"].items()
}
PLACEMENT_PRESETS: dict[str, dict[str, Any]] = {
    str(name): dict(entry) for name, entry in _PRESETS["placement_presets"].items()
}

SYNC_OVERHEAD_US = float(_DEFAULTS["sync_overhead_us"])
INIT_OVERHEAD_US = float(_DEFAULTS["init_overhead_us"])
GROUP_CREATE_OVERHEAD_US = float(_DEFAULTS["group_create_overhead_us"])
VALIDATION_OVERHEAD_US = float(_DEFAULTS["validation_overhead_us"])

_DEFAULT_WORLD = int(_DEFAULTS["default_world_size"])
_DEFAULT_PER_NODE = int(_DEFAULTS["default_ranks_per_node"])
_DEFAULT_DIES = int(_DEFAULTS["default_dies_per_package"])
_DEFAULT_DURATION_S = float(_DEFAULTS["default_duration_s"])
_DEFAULT_WARMUP = int(_DEFAULTS["default_warmup"])
_DEFAULT_ITERS = int(_DEFAULTS["default_iterations"])
_MAX_RANK = int(_DEFAULTS["max_rank_id"])
_MAX_WORLD = int(_DEFAULTS["max_world_size"])
_MAX_DURATION_S = float(_DEFAULTS["max_duration_s"])
_MIN_SIZE = int(_DEFAULTS["min_size_bytes"])
_MAX_SIZE = int(_DEFAULTS["max_size_bytes"])
_MAX_SIZES = int(_DEFAULTS["max_sizes"])
_MAX_GROUP_BUF = int(_DEFAULTS["max_group_buffer_bytes"])
_MAX_ADMITTED = int(_DEFAULTS["max_admitted"])
_MAX_PAIRS = int(_DEFAULTS["max_pairs"])
_MAX_ROUNDS = int(_DEFAULTS["max_pair_rounds"])
_MAX_LABEL = int(_DEFAULTS["max_tier_label_chars"])
_CLEANUP_MAX_S = float(_DEFAULTS["cleanup_max_s"])
_CLEANUP_MIN_S = float(_DEFAULTS["cleanup_min_s"])
_CLEANUP_FRAC = float(_DEFAULTS["cleanup_fraction"])
_MIN_SAMPLE_US = float(_DEFAULTS["min_sample_cost_us"])
_BUDGET_EPS_S = float(_DEFAULTS["budget_epsilon_s"])
_ROUND_S = int(_DEFAULTS["round_s_digits"])
_EXIT_ERR = int(_DEFAULTS["exit_error"])


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
    meta: dict[str, Any] = {
        "route": route,
        "hops": int(hops),
        "rails": max(1, int(rails)),
        "link": str(item.get("link") or priors["link"]),
        "protocol": str(item.get("protocol") or priors["protocol"]),
        "route_label": f"{route}(h={int(hops)},f={max(1, int(rails))})",
    }
    semantics = item.get("channel_semantics") or priors.get("channel_semantics")
    if semantics:
        meta["channel_semantics"] = str(semantics)
    return meta


def _default_topology(
    world_size: int, ranks_per_node: int, dies_per_package: int, nodes: int
) -> list[dict[str, Any]]:
    tiers, ranks = [], list(range(world_size))
    if dies_per_package >= 2 and world_size >= 2:
        tiers.append({"tier": "intra_package_die", "ranks": [0, 1], "available": True})
    if ranks_per_node >= 2:
        group = ranks[: min(ranks_per_node, world_size)]
        tiers.append(
            {"tier": "intra_node_hccs", "ranks": group, "available": len(group) >= 2}
        )
    if nodes >= 2 and ranks_per_node >= 1 and world_size > ranks_per_node:
        group = [
            idx * ranks_per_node
            for idx in range(nodes)
            if idx * ranks_per_node < world_size
        ]
        tiers.append(
            {"tier": "inter_node_roce", "ranks": group, "available": len(group) >= 2}
        )
    return [
        {
            **tier,
            **_route_metadata(tier["tier"], tier),
            "pairs": _pairs(tier["ranks"]),
            "rail_pairs": False,
        }
        for tier in tiers
    ]


def _explicit_topology(topology: Any, world_size: int) -> list[dict[str, Any]]:
    if not isinstance(topology, dict) or not isinstance(topology.get("tiers"), list):
        raise ProfilerUsageError("topology must be {'tiers': [{'tier','ranks',...}]}")
    tiers = []
    for item in bounded_sequence(topology["tiers"], "tiers", MAX_TIERS):
        if not isinstance(item, dict):
            raise ProfilerUsageError("topology tier must be an object")
        name = str(item.get("tier") or "")
        if not name or len(name) > _MAX_LABEL:
            raise ProfilerUsageError("topology tier label must be 1..64 characters")
        route = _route_metadata(name, item)
        ranks = [
            bounded_count(rank, "topology rank", 0, world_size - 1)
            for rank in bounded_sequence(item.get("ranks", ()), "ranks", _MAX_WORLD)
        ]
        if len(set(ranks)) != len(ranks) or any(tier["tier"] == name for tier in tiers):
            raise ProfilerUsageError("topology has duplicate ranks or tiers")
        ranks.sort()
        explicit_pairs = item.get("pairs")
        pairs = (
            _validated_pairs(explicit_pairs, world_size)
            if explicit_pairs is not None
            else _pairs(ranks)
        )
        rounds = (
            _validated_pair_rounds(item.get("pair_rounds"), world_size)
            if item.get("pair_rounds") is not None
            else []
        )
        tiers.append(
            {
                "tier": name,
                "ranks": ranks,
                **route,
                "pairs": pairs,
                "pair_rounds": rounds,
                "rail_pairs": bool(item.get("rail_pairs", False)),
                "available": len(ranks) >= 2 and bool(item.get("available", True)),
            }
        )
    return tiers


def _validated_pairs(pairs: Any, world_size: int) -> list[list[int]]:
    result: list[list[int]] = []
    for pair in bounded_sequence(pairs, "pairs", _MAX_PAIRS):
        values = bounded_sequence(pair, "pair", 2)
        if len(values) != 2:
            raise ProfilerUsageError("pair must contain two ranks")
        first, second = (
            bounded_count(val, "pair rank", 0, world_size - 1) for val in values
        )
        if first == second:
            raise ProfilerUsageError("a rail pair needs two distinct ranks")
        result.append([first, second])
    return result


def _validated_pair_rounds(rounds: Any, world_size: int) -> list[list[list[int]]]:
    return [
        _validated_pairs(round_, world_size)
        for round_ in bounded_sequence(rounds, "pair_rounds", _MAX_ROUNDS)
    ]


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


def _resolve_placement(
    world_size: Any,
    ranks_per_node: Any,
    dies_per_package: Any,
    nodes: Any,
    placement: Any,
) -> tuple[int, int, int, int, Any]:
    preset = None
    if placement is not None:
        preset = PLACEMENT_PRESETS.get(str(placement))
        if preset is None:
            raise ProfilerUsageError(f"unknown placement preset {placement!r}")

    def pick(value: Any, key: str, default: int) -> int:
        return (
            int(value)
            if value is not None
            else (int(preset[key]) if preset is not None else default)
        )

    world = pick(world_size, "world_size", _DEFAULT_WORLD)
    per_node = pick(ranks_per_node, "ranks_per_node", _DEFAULT_PER_NODE)
    dies = pick(dies_per_package, "dies_per_package", _DEFAULT_DIES)
    node_count = (
        pick(nodes, "nodes", 1)
        if nodes is not None or preset is not None
        else (world + per_node - 1) // per_node
    )
    return world, per_node, dies, node_count, preset


def _timing_modes(size: int, requested: Any) -> list[str]:
    if requested is None:
        return (
            list(DEVICE_TIMING_MODES)
            if int(size) <= SMALL_COLLECTIVE_BYTES
            else [DEVICE_TIMING_MODES[0]]
        )
    modes = [
        str(mode)
        for mode in bounded_sequence(requested, "timing_modes", len(DEVICE_TIMING_MODES))
    ]
    if not modes or any(mode not in DEVICE_TIMING_MODES for mode in modes):
        raise ProfilerUsageError(f"unknown timing modes: {modes}")
    return modes


def build_fabric_probe_plan(
    *,
    world_size: int | None = None,
    ranks_per_node: int | None = None,
    duration_s: float = _DEFAULT_DURATION_S,
    sizes: tuple[int, ...] | list[int] | None = None,
    ops: tuple[str, ...] | list[str] | None = None,
    warmup: int = _DEFAULT_WARMUP,
    iterations: int = _DEFAULT_ITERS,
    topology: dict[str, Any] | None = None,
    dies_per_package: int | None = None,
    nodes: int | None = None,
    placement: str | None = None,
    timing_modes: tuple[str, ...] | list[str] | None = None,
    allowed_phy_ids: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Admit affordable HCCL probe work across declared or derived fabric tiers."""
    if topology is not None:
        topology = bounded_mapping(topology, "topology")
    phy_ids = None
    if allowed_phy_ids is not None:
        phy_ids = sorted(
            {
                bounded_count(val, "allowed physical id", 0, _MAX_RANK)
                for val in bounded_sequence(allowed_phy_ids, "allowed_phy_ids", _MAX_WORLD)
            }
        )
    world_size, ranks_per_node, dies_per_package, nodes, preset = _resolve_placement(
        world_size, ranks_per_node, dies_per_package, nodes, placement
    )
    bounded_count(world_size, "world_size", 2, _MAX_WORLD)
    bounded_count(ranks_per_node, "ranks_per_node", 1, _MAX_WORLD)
    bounded_count(dies_per_package, "dies_per_package", 1, _MAX_WORLD)
    bounded_count(nodes, "nodes", 1, _MAX_WORLD)
    bounded_count(warmup, "warmup")
    bounded_count(iterations, "iterations", 1)
    duration_s = _finite(duration_s)
    if not 0 < duration_s <= _MAX_DURATION_S:
        raise ProfilerUsageError("fabric probe duration_s must be in (0, 600]")
    size_list = sorted(
        {
            bounded_count(size, "size bytes", _MIN_SIZE, _MAX_SIZE)
            for size in bounded_sequence(
                DEFAULT_SIZES if sizes is None else sizes, "sizes", _MAX_SIZES
            )
        }
    )
    if not size_list:
        raise ProfilerUsageError("fabric probe needs at least one size >= 4 KiB")
    op_list = list(
        bounded_sequence(DEFAULT_OPS if ops is None else ops, "ops", len(SUPPORTED_OPS))
    )
    unknown = [op for op in op_list if op not in SUPPORTED_OPS]
    if unknown:
        raise ProfilerUsageError(f"unknown probe operations: {unknown}")
    if ALL_TO_ALL_V in op_list:
        misaligned = [s for s in size_list if s % ALL_TO_ALL_V_ELEMENT_BYTES != 0]
        if misaligned:
            raise ProfilerUsageError(
                f"all_to_all_v sizes must be multiples of "
                f"{ALL_TO_ALL_V_ELEMENT_BYTES} bytes: {misaligned[:2]}"
            )
    declared_topology = topology is not None
    if preset is not None and topology is None:
        topology = {"tiers": [dict(tier) for tier in preset["tiers"]]}
    tiers = (
        _explicit_topology(topology, world_size)
        if topology is not None
        else _default_topology(world_size, ranks_per_node, dies_per_package, nodes)
    )
    for tier in tiers:
        if any(
            op in {"all_gather", "reduce_scatter", "all_to_all", ALL_TO_ALL_V}
            for op in op_list
        ):
            factor = 2 if ALL_TO_ALL_V in op_list else 1
            bounded_count(
                max(size_list) * len(tier["ranks"]) * factor,
                "group buffer bytes",
                0,
                _MAX_GROUP_BUF,
            )
    cleanup_s = min(_CLEANUP_MAX_S, max(_CLEANUP_MIN_S, duration_s * _CLEANUP_FRAC))
    measurement_s = max(0.0, duration_s - cleanup_s)
    init_s = INIT_OVERHEAD_US / 1_000_000.0
    group_create_s = GROUP_CREATE_OVERHEAD_US * max(1, len(tiers)) / 1_000_000.0
    remaining_seconds = max(0.0, duration_s - cleanup_s - init_s - group_create_s)
    budget_us = remaining_seconds * 1_000_000.0
    estimated_us = warmup_us = measure_us = 0.0
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
            per_tier[tier["tier"]] = {
                "iterations_per_size": {},
                "admitted": 0,
                "status": "unavailable",
            }
            continue
        for op in op_list:
            pairs = tier.get("pairs") or _pairs(tier["ranks"])
            participants = len(pairs) * 2 if op == "send_recv" else len(tier["ranks"])
            if participants < 2:
                unmeasured.append(
                    {"tier": tier["tier"], "op": op, "reason": "insufficient_participants"}
                )
                continue
            for size in size_list:
                modes = _timing_modes(size, timing_modes)
                predicted_us = prior["alpha_us"] + prior["beta_ns_per_byte"] * size / 1000.0
                sample_cost_us = (predicted_us + SYNC_OVERHEAD_US) * len(modes)
                if "stream_saturated" in modes:
                    sample_cost_us += BLOCKER_TARGET_MS * 1000.0
                if op == ALL_TO_ALL_V:
                    sample_cost_us *= len(ALL_TO_ALL_V_STYLES)
                affordable = int(budget_us / max(sample_cost_us, _MIN_SAMPLE_US))
                count = min(int(iterations), max(0, affordable - int(warmup) - 1))
                if count < 1:
                    unmeasured.append(
                        {"tier": tier["tier"], "op": op, "bytes": size, "reason": "budget_exhausted"}
                    )
                    continue
                combo_us = (int(warmup) + count) * sample_cost_us
                if estimated_us + combo_us > budget_us + INIT_OVERHEAD_US:
                    unmeasured.append(
                        {"tier": tier["tier"], "op": op, "bytes": size, "reason": "budget_exhausted"}
                    )
                    continue
                estimated_us += combo_us
                warmup_us += int(warmup) * sample_cost_us
                measure_us += count * sample_cost_us
                validation_count += 1
                entry: dict[str, Any] = {
                    "tier": tier["tier"],
                    "op": op,
                    "bytes": size,
                    "iterations": count,
                    "warmup": int(warmup),
                    "regime": "isolated",
                    "timing_modes": modes,
                    "route": tier["route"],
                    "hops": tier["hops"],
                    "rails": tier["rails"],
                }
                if tier.get("channel_semantics"):
                    entry["channel_semantics"] = tier["channel_semantics"]
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
            "iterations_per_size": tier_iters,
            "admitted": admitted_count,
            "status": "admitted" if admitted_count else "unmeasured",
            "op_count": len(op_list),
        }
    validation_s = validation_count * VALIDATION_OVERHEAD_US / 1_000_000.0
    warmup_s = warmup_us / 1_000_000.0
    measured_s = measure_us / 1_000_000.0
    estimated_total_s = (
        init_s + group_create_s + warmup_s + measured_s + validation_s + cleanup_s
    )
    within_budget = estimated_total_s <= float(duration_s) + _BUDGET_EPS_S
    admitted_ok = bool(admitted) and within_budget
    if not within_budget and admitted:
        admitted = []
        for block in per_tier.values():
            block["admitted"] = 0
            block["status"] = "unmeasured"
            block["iterations_per_size"] = {}
        unmeasured.append(
            {
                "reason": "estimated_cost_exceeds_budget",
                "estimated_s": round(estimated_total_s, _ROUND_S),
                "budget_s": float(duration_s),
            }
        )
    status = "admitted" if admitted_ok else "rejected" if not within_budget else "unmeasured"
    topology_label = (
        "explicit_topology"
        if declared_topology
        else "declared_placement"
        if preset is not None
        else "unverified_rank_group"
    )
    breakdown = {
        "init_cost_s": round(init_s, _ROUND_S),
        "group_create_s": round(group_create_s, _ROUND_S),
        "warmup_s": round(warmup_s, _ROUND_S),
        "measure_s": round(measured_s, _ROUND_S),
        "validation_s": round(validation_s, _ROUND_S),
        "cleanup_s": round(cleanup_s, _ROUND_S),
    }
    routes_map: dict[str, dict[str, Any]] = {}
    for tier in tiers:
        route_entry = {
            "route": tier["route"],
            "hops": tier["hops"],
            "rails": tier["rails"],
            "protocol": tier["protocol"],
            "link": tier["link"],
            "route_label": tier["route_label"],
        }
        if tier.get("channel_semantics"):
            route_entry["channel_semantics"] = tier["channel_semantics"]
        routes_map[tier["tier"]] = route_entry
    preset_meta = None
    if placement is not None:
        preset_meta = {
            "name": placement,
            "declared": True,
            "physical_verification": declared_topology,
        }
        if preset and preset.get("channel_semantics"):
            preset_meta["channel_semantics"] = preset["channel_semantics"]
        if preset and preset.get("legacy_alias_for"):
            preset_meta["legacy_alias_for"] = preset["legacy_alias_for"]
    return {
        "schema": PLAN_SCHEMA,
        "status": status,
        "world_size": int(world_size),
        "ranks_per_node": int(ranks_per_node),
        "nodes": int(nodes),
        "dies_per_package": int(dies_per_package),
        "budget_s": float(duration_s),
        "topology_label": topology_label,
        "topology_source": (
            "explicit_host_map"
            if declared_topology
            else "declared_placement"
            if preset is not None
            else "rank_count_assumption"
        ),
        "physical_verification": declared_topology,
        "deadline": {
            "mode": "time.monotonic",
            "duration_s": float(duration_s),
            "measurement_budget_s": round(measurement_s, _ROUND_S),
            "cleanup_allowance_s": round(cleanup_s, _ROUND_S),
            "init_cost_s": round(init_s, _ROUND_S),
            "group_create_s": round(group_create_s, _ROUND_S),
            "validation_s": round(validation_s, _ROUND_S),
            "includes_warmup": True,
            "includes_validation": True,
            "includes_synchronization": True,
            "max_wall_s": float(duration_s),
        },
        "admission": {
            "admitted": admitted_ok,
            "reason": None if admitted_ok else "estimated_cost_exceeds_budget",
            "estimated_s": round(estimated_total_s, _ROUND_S),
            "budget_s": float(duration_s),
            "breakdown_s": breakdown,
        },
        "warmup": max(0, int(warmup)),
        "max_iterations": int(iterations),
        "sizes_bytes": size_list,
        "ops": op_list,
        "tiers": [
            {
                **tier,
                "group_size": len(tier["ranks"]),
                "pairs": tier["pairs"],
                "physical_verification": declared_topology,
                "topology_label": topology_label,
            }
            for tier in tiers
        ],
        "topology": topology
        or {
            "mode": "derived",
            "ranks_per_node": int(ranks_per_node),
            "nodes": int(nodes),
            "dies_per_package": int(dies_per_package),
        },
        "iterations": per_tier,
        "admitted": admitted,
        "unmeasured": unmeasured,
        "estimated_measurement_s": round(measured_s, _ROUND_S),
        "estimated_s": round(estimated_total_s, _ROUND_S),
        "estimated_breakdown_s": breakdown,
        "cleanup_allowance_s": round(cleanup_s, _ROUND_S),
        "pairwise": {
            "op": "send_recv",
            "pairs_by_tier": {tier["tier"]: tier["pairs"] for tier in tiers},
            "pair_rounds_by_tier": {
                tier["tier"]: tier["pair_rounds"]
                for tier in tiers
                if tier.get("pair_rounds")
            },
        },
        "multi_rank": {
            "ops": [op for op in op_list if op != "send_recv"],
            "world_size": int(world_size),
        },
        "routes": routes_map,
        "rail_pairs": {
            tier["tier"]: [list(pair) for pair in tier["pairs"]]
            for tier in tiers
            if tier.get("rail_pairs")
        },
        "pair_rounds": {
            tier["tier"]: [[list(pair) for pair in round_] for round_ in tier["pair_rounds"]]
            for tier in tiers
            if tier.get("pair_rounds")
        },
        "timing": {
            "device_event": True,
            "host_enqueue_qualified": True,
            "max_across_ranks": True,
            "blocker_target_ms": BLOCKER_TARGET_MS,
            "modes": list(DEVICE_TIMING_MODES),
            "small_collective_bytes": SMALL_COLLECTIVE_BYTES,
            "host_fallback": "declared when torch.npu.Event is unavailable",
        },
        "all_to_all_v": {
            "styles": list(ALL_TO_ALL_V_STYLES),
            "element_bytes": ALL_TO_ALL_V_ELEMENT_BYTES,
            "skew_fraction": SKEW_FRACTION,
            "rule": "quotient_remainder_circulant_then_half_peer_transfer",
            "recv_equals_send_transpose": True,
        },
        "placement": placement,
        "allowed_phy_ids": phy_ids,
        "placement_preset": preset_meta,
    }


def validate_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    plan = bounded_mapping(plan, "plan")
    if not isinstance(plan, Mapping) or plan.get("schema") != PLAN_SCHEMA:
        raise ProfilerUsageError(f"expected plan schema {PLAN_SCHEMA}")
    for field in ("world_size", "sizes_bytes", "ops", "tiers", "admitted"):
        if field not in plan:
            raise ProfilerUsageError(f"plan missing {field}")
    world = bounded_count(plan["world_size"], "world_size", 2, _MAX_WORLD)
    for field in ("ranks_per_node", "dies_per_package", "nodes"):
        bounded_count(plan.get(field, 1), field, 1, _MAX_WORLD)
    bounded_count(plan.get("warmup", 0), "warmup")
    bounded_count(plan.get("max_iterations", 1), "max_iterations", 1)
    for size in bounded_sequence(plan["sizes_bytes"], "sizes", _MAX_SIZES):
        bounded_count(size, "size bytes", _MIN_SIZE, _MAX_SIZE)
    if any(
        str(op) not in SUPPORTED_OPS
        for op in bounded_sequence(plan["ops"], "ops", len(SUPPORTED_OPS))
    ):
        raise ProfilerUsageError("plan contains an unsupported probe operation")
    tiers = _explicit_topology({"tiers": plan["tiers"]}, world)
    for tier, normalized in zip(plan["tiers"], tiers):
        group = bounded_count(
            tier.get("group_size", len(normalized["ranks"])), "group_size", 0, world
        )
        if group != len(normalized["ranks"]):
            raise ProfilerUsageError("group_size does not match topology ranks")
        if (tier.get("route"), tier.get("hops"), tier.get("rails")) != (
            normalized["route"],
            normalized["hops"],
            normalized["rails"],
        ):
            raise ProfilerUsageError("tier route metadata does not match its label")
        entry = (plan.get("routes") or {}).get(tier["tier"])
        if entry is not None and (
            entry.get("route"),
            entry.get("hops"),
            entry.get("rails"),
        ) != (normalized["route"], normalized["hops"], normalized["rails"]):
            raise ProfilerUsageError("plan routes disagree with the tier entries")
        for pair in bounded_sequence(tier.get("pairs", ()), "pairs", _MAX_PAIRS):
            if len(bounded_sequence(pair, "pair", 2)) != 2:
                raise ProfilerUsageError("pair must contain two ranks")
            for rank in pair:
                bounded_count(rank, "pair rank", 0, world - 1)
        for round_ in bounded_sequence(
            tier.get("pair_rounds", ()) or (), "pair_rounds", _MAX_ROUNDS
        ):
            for pair in bounded_sequence(round_, "pair round", _MAX_PAIRS):
                if len(bounded_sequence(pair, "pair", 2)) != 2:
                    raise ProfilerUsageError("pair must contain two ranks")
                for rank in pair:
                    bounded_count(rank, "pair rank", 0, world - 1)
    for value in plan.get("allowed_phy_ids") or ():
        bounded_count(value, "allowed physical id", 0, _MAX_RANK)
    for item in bounded_sequence(plan["admitted"], "admitted", _MAX_ADMITTED):
        bounded_count(item.get("iterations", 0), "iterations")
        bounded_count(item.get("warmup", plan.get("warmup", 0)), "warmup")
        bounded_count(item.get("bytes"), "size bytes", _MIN_SIZE, _MAX_SIZE)
        group = next(
            (len(tier["ranks"]) for tier in tiers if tier["tier"] == item.get("tier")),
            0,
        )
        modes = bounded_sequence(
            item.get("timing_modes", DEVICE_TIMING_MODES),
            "timing_modes",
            len(DEVICE_TIMING_MODES),
        )
        if any(str(mode) not in DEVICE_TIMING_MODES for mode in modes):
            raise ProfilerUsageError("admitted item has an unknown timing mode")
        if item.get("op") in {"all_gather", "reduce_scatter", "all_to_all", ALL_TO_ALL_V}:
            factor = 2 if item.get("op") == ALL_TO_ALL_V else 1
            bounded_count(
                item["bytes"] * group * factor, "group buffer bytes", 0, _MAX_GROUP_BUF
            )
    if plan.get("deadline", {}).get("mode") != "time.monotonic":
        raise ProfilerUsageError("plan deadline must be a monotonic deadline")
    admission = plan.get("admission") or {}
    for section in (plan, plan.get("deadline") or {}, admission):
        for key, value in section.items():
            if key.endswith("_s") and value is not None and not isinstance(value, Mapping):
                _finite(value)
    if admission.get("admitted") and _finite(
        admission.get("estimated_s", 0.0)
    ) > _finite(admission.get("budget_s", 0.0)) + _BUDGET_EPS_S:
        raise ProfilerUsageError("plan admits work whose estimated cost exceeds its budget")
    return dict(plan)


def emit_fabric_probe_script(
    plan: dict[str, Any], *, output_path: str | Path | None = None
) -> dict[str, Any]:
    return render_fabric_probe_script(plan, validator=validate_plan, output_path=output_path)


def build_fabric_probe_plan_from_args(args: argparse.Namespace) -> dict[str, Any]:
    topology = load_cli_json(args.topology) if args.topology else None
    from .bench.abi import resolve_allowed_phy_ids

    resolved = resolve_allowed_phy_ids(args.allowed_phy_ids)
    phy_ids = list(resolved) if resolved else None
    return build_fabric_probe_plan(
        world_size=args.world_size,
        ranks_per_node=args.ranks_per_node,
        duration_s=args.duration_s,
        topology=topology,
        placement=args.placement,
        dies_per_package=args.dies_per_package,
        nodes=args.nodes,
        ops=args.ops,
        timing_modes=args.timing_mode,
        allowed_phy_ids=phy_ids,
        warmup=args.warmup,
        iterations=args.iterations,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler fabric-probe", allow_abbrev=False,
        description="Plan, emit, or fit bounded multi-tier HCCL fabric sweeps.",
    )
    for flag in ("--world-size", "--ranks-per-node", "--dies-per-package", "--nodes"):
        parser.add_argument(flag, type=int, default=None)
    parser.add_argument("--placement", default=None, choices=tuple(PLACEMENT_PRESETS))
    parser.add_argument("--ops", action="append", default=None, choices=SUPPORTED_OPS)
    parser.add_argument("--timing-mode", action="append", default=None, choices=DEVICE_TIMING_MODES)
    parser.add_argument("--duration-s", type=float, default=_DEFAULT_DURATION_S)
    parser.add_argument("--warmup", type=int, default=_DEFAULT_WARMUP)
    parser.add_argument("--iterations", type=int, default=_DEFAULT_ITERS)
    for flag in ("--topology", "--allowed-phy-ids", "--samples", "--plan", "--script"):
        parser.add_argument(flag, default=None)
    parser.add_argument("--output", "-o", default=None)
    args = parser.parse_args(list(argv or ()))
    plan = build_fabric_probe_plan_from_args(args)
    payload: dict[str, Any] = plan
    if args.script:
        payload = emit_fabric_probe_script(plan, output_path=args.script)
    if args.samples:
        records = parse_fabric_probe_samples(Path(args.samples).read_text(encoding="utf-8"))
        payload = fit_calibrated_fabric_profile(plan, records)
        if args.output is None:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))
            return 0 if payload["status"] == "calibrated" else _EXIT_ERR
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.plan:
        Path(args.plan).write_text(
            json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    ok = (
        payload.get("status") in {"admitted", "calibrated", "partial", "unmeasured", "ok"}
        or payload.get("syntax_ok") is True
    )
    return 0 if ok else _EXIT_ERR


__all__ = [
    "ALL_TO_ALL_V", "ALL_TO_ALL_V_ELEMENT_BYTES", "BLOCKER_TARGET_MS",
    "DEFAULT_OPS", "DEFAULT_SIZES", "PLACEMENT_PRESETS", "PLAN_SCHEMA",
    "PROFILE_SCHEMA", "ROUTE_CLASSES", "SKEW_FRACTION", "SMALL_COLLECTIVE_BYTES",
    "build_fabric_probe_plan", "build_fabric_probe_plan_from_args",
    "emit_fabric_probe_script", "fit_calibrated_fabric_profile", "main",
    "parse_fabric_probe_samples", "supervise_probe_processes", "validate_plan",
]

if __name__ == "__main__":
    raise SystemExit(main())
