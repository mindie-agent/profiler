"""PMU pipe utilization, measured hardware supply derivation, and sparse MTE1 accounting (pmu_derivation_summary).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting pmu pipe utilization, measured hardware supply derivation, and sparse mte1 accounting.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

from .pmu_derivation_supply import (
    DUAL_LOAD_SCHEMA, MEASURED_SUPPLY_SCHEMA, MEASURED_SUPPLY_SCOPE,
    SATURATION_THRESHOLD, _canonical, _load_record, _require,
)

def build_dual_load_service(
    saturated: Mapping[str, Any],
    underfilled: Mapping[str, Any],
    *,
    physical_owners: int,
    recipe: str | None = None,
    kernel: str | None = None,
    hardware: str | None = None,
    saturation_threshold: float = SATURATION_THRESHOLD,
) -> dict[str, Any]:
    """Build the reusable dual-load record and normal MAC-service rule."""
    _require(saturated.get("status") == "measured", "measured_supply_saturated_unknown")
    _require(underfilled.get("status") == "measured", "measured_supply_underfilled_unknown")
    for field in ("native_type", "dtype", "output_dtype", "n", "k",
                  "device_id", "rank_id"):
        _require(saturated.get(field) == underfilled.get(field),
                 "measured_supply_identity_mismatch:" + field)
    _require(saturated.get("issue") is not None and underfilled.get("issue") is not None,
             "measured_supply_requires_certified_issue_rule")
    _require(saturated["issue"] == underfilled["issue"],
             "measured_supply_issue_rule_mismatch")
    _require(int(saturated["active_owners"]) == int(physical_owners),
             "measured_supply_saturated_not_full_grid")
    _require(int(underfilled["active_owners"]) < int(physical_owners),
             "measured_supply_underfilled_not_tail_grid")
    _require(int(saturated["active_owners"]) != int(underfilled["active_owners"]),
             "measured_supply_same_active_owners")
    full_mac, tail_mac = saturated.get("mac_ratio"), underfilled.get("mac_ratio")
    _require(isinstance(full_mac, (int, float)) and not isinstance(full_mac, bool),
             "measured_supply_saturated_mac_ratio_missing")
    _require(isinstance(tail_mac, (int, float)) and not isinstance(tail_mac, bool),
             "measured_supply_underfilled_mac_ratio_missing")
    _require(float(full_mac) >= saturation_threshold,
             "measured_supply_saturated_mac_ratio_below_threshold")
    _require(float(tail_mac) < saturation_threshold,
             "measured_supply_underfilled_mac_ratio_above_threshold")
    _require(float(saturated["rate_flops_per_s"]) > float(underfilled["rate_flops_per_s"]),
             "measured_supply_saturated_rate_not_greater")
    dtype = str(saturated["dtype"])
    issue = dict(saturated["issue"])
    n, k = int(saturated["n"]), int(saturated["k"])
    under_owners = int(underfilled["active_owners"])
    _require(n % under_owners == 0, "measured_supply_n_not_divisible_by_tail_owners")
    tile_n = n // under_owners
    n_tiles = n // tile_n
    full_owners = int(saturated["active_owners"])
    full_m = int(saturated["m"])
    tile_m = 128
    tile_k = 128
    identity = {
        "native_call": saturated.get("native_call"),
        "native_type": saturated.get("native_type"),
        "dtype": dtype,
        "output_dtype": saturated.get("output_dtype"),
        "n": n, "k": k,
        "device_id": saturated.get("device_id"),
        "rank_id": saturated.get("rank_id"),
        "physical_owners": int(physical_owners),
        "physical_owners_basis": saturated.get("provenance", {}).get(
            "physical_owners_basis", "declared_aic_count"),
        "issue_rule": issue,
    }
    loads = [
        _load_record(saturated, "saturated"),
        _load_record(underfilled, "underfilled"),
    ]
    match: dict[str, Any] = {"dtype": dtype}
    if recipe:
        match["recipe"] = recipe
    elif kernel:
        match["kernel"] = kernel
    else:
        match["kernel"] = saturated.get("native_type") or saturated.get("native_call")
    if hardware:
        match["hardware"] = hardware
    response = {
        "kind": "measured_dual_load",
        "fixed_us": 0.0,
        "resource": "cube",
        "dtype": dtype,
        "scope": MEASURED_SUPPLY_SCOPE,
        "issue": {
            **issue,
            "n": n, "k": k,
        },
        "owner_grid": {
            "tile_m": tile_m, "tile_n": tile_n, "cores": int(physical_owners),
        },
        "loads": loads,
    }
    rule = {
        "id": "measured-dual-load-" + hashlib.sha256(_canonical({
            "identity": identity,
            "loads": [{key: load[key] for key in (
                "id", "active_owners", "rate_flops_per_s",
                "measured_issued_flops")} for load in loads],
        }).encode()).hexdigest()[:16],
        "match": match,
        "coordinates": {
            "m": {"path": "local_shape.0"},
            "n": {"path": "local_shape.1"},
            "k": {"path": "local_shape.2"},
        },
        "domain": {
            "n": {"min": n, "max": n},
            "k": {"min": k, "max": k},
        },
        "execution": {
            "kind": "mac_service",
            "resource": "cube",
            "native_kernel": str(saturated.get("native_type") or ""),
            "tile_m": tile_m,
            "tile_n": tile_n,
            "tile_k": tile_k,
            "slots": 2,
        },
        "response": response,
        "provenance": {
            "schema_version": DUAL_LOAD_SCHEMA,
            "measured_supply_schema": MEASURED_SUPPLY_SCHEMA,
            "selected_by": "most_samples_per_condition_median",
            "issue_rule": issue,
            "tile_geometry": {
                "tile_m": tile_m, "tile_n": tile_n, "tile_k": tile_k,
                "basis": "N tile from observed tail owners; M tile 128 from family/source matrix geometry and L0c capacity; service cap does not depend on tile_m",
            },
            "physical_owners_basis": identity["physical_owners_basis"],
            "not_end_to_end_kernel_latency": True,
            "not_a_shape_work_envelope": True,
            "saturated_condition": saturated.get("provenance"),
            "underfilled_condition": underfilled.get("provenance"),
        },
    }
    return {
        "schema_version": DUAL_LOAD_SCHEMA,
        "identity": identity,
        "saturated": dict(saturated),
        "underfilled": dict(underfilled),
        "service_ratio": {
            "underfilled_over_saturated": float(underfilled["rate_flops_per_s"])
            / float(saturated["rate_flops_per_s"]),
        },
        "saturation_threshold": saturation_threshold,
        "service_regime": rule,
    }
