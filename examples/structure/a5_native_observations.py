"""Explicitly bind retained A5 native observations to their active ABI domain.

[Role] Import complete local GDN/projection responses for a requested geometry.
[Invariants] Input dictionaries, captures and archives are never mutated. An
  unmatched calibration leaves ordinary prediction available. Unknown binary
  and caller-stride evidence is retained, never promoted to observed identity.
[Timeouts & Locks] One small local profile read and one target graph; no network,
  subprocesses, device contexts, locks or timing-dependent parameter assignment.
[Side-Effect Policy] Return a new input and provenance; write no files or state.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from mindie_sim import target_operators
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution
from mindie_sim.prediction.service_regimes import RegimePolicy, _axes, axis_equal, coordinates, lookup
from mindie_sim.prediction.structure import parse_case


PROFILE_PATH = Path(__file__).resolve().parent / "profiles" / "a5_gdn_decode_native_20261106.json"


def _read_profile(path: Path) -> tuple[dict, dict]:
    data = path.read_bytes()
    profile = json.loads(data)
    if profile["schema_version"] != "mindie-profiler-native-observation-profile/1":
        raise ValueError("unsupported_native_observation_profile")
    RegimePolicy(profile["rules"])
    return profile, {"id": profile["id"], "path": str(path.resolve()),
                     "sha256": sha256(data).hexdigest()}


def _physical_contract(case) -> dict:
    """Use normalized hardware declarations so omitted defaults are equivalent."""
    return json.loads(json.dumps({
        "runtime": {name: getattr(case.runtime, name)
                    for name in ("vllm_impl", "vllm_version", "kernel_format")},
        "devices": [{"compute_units": device.compute_units, **{
            name: dict(getattr(device, name)) for name in (
                "rates", "compute_peaks", "service_modes", "resource_units")}}
                    for device in case.machine.dies],
    }))


def _operator_axes(execution, op) -> dict:
    scope = dict(op.metadata).get("graph_replay_scope", "none")
    prepared, recipe = execution.prepare(op)
    context = execution._context(prepared, 0, scope, recipe=recipe)
    return _axes(context, physical_rates=True)


def _matches(axes: dict, rule: dict) -> bool:
    if any(not axis_equal(lookup(axes, key), value)
           for key, value in rule["match"].items()):
        return False
    # These measured domains contain exact active shapes, not interpolated rows
    # or cache-allocation capacities. The maintained file declares every axis.
    values = coordinates(axes, rule["coordinates"])
    for name, bounds in rule["domain"].items():
        value = values.get(name)
        if value is None or not bounds["min"] <= value <= bounds["max"]:
            return False
    return True


def apply_a5_native_observations(
    raw: dict, *, phase: str, tokens: int, context: int, sequences: int,
    profile_path: Path = PROFILE_PATH,
) -> tuple[dict, dict]:
    """Apply this explicitly selected profile, or report its physical-domain miss.

    The caller chooses the observed-native arm. This function does not select a
    native implementation, require a measurement before ordinary prediction, or
    access any of the retained capture paths. All five native boundaries must
    be covered for the requested sequence partition before old responses change.
    """
    profile, identity = _read_profile(Path(profile_path))
    result = deepcopy(raw)
    provenance = {
        "schema_version": "mindie-profiler-native-observation-import/1",
        "profile": identity, "status": "not_applicable",
        "geometry": {"phase": phase, "tokens": tokens, "context": context,
                     "sequences": sequences},
        "calibration": deepcopy(profile["calibration"]),
        "sources": deepcopy(profile["sources"]),
        "observations_modified": False, "matched_domains": [],
    }

    def miss(reason):
        provenance["reason"] = reason
        return result, provenance

    partition = profile["sequence_partition"]
    if phase != profile["phase"]:
        return miss("phase_outside_observed_domain")
    if (tokens != partition["tokens_per_sequence"] or
            sequences not in partition["sequences_per_replica"]):
        return miss("sequence_partition_outside_observed_domain")
    case = parse_case(raw)
    if (case.machine.hardware_key or case.machine.sku) != profile["hardware"]:
        return miss("hardware_outside_observed_domain")
    if any(getattr(case.runtime.parallel, key) != value
           for key, value in profile["parallel"].items()):
        return miss("parallelism_outside_observed_domain")
    if _physical_contract(case) != profile["source_contract"]:
        return miss("physical_rates_or_declared_runtime_outside_observed_domain")
    selected = raw.get("runtime", {}).get("kernels", {}).get("lowerings", {}).get("gdn_decode")
    caller = profile["caller_implementation"]
    if not isinstance(selected, dict) or selected.get("implementation") != caller["name"]:
        return miss("required_source_caller_not_explicitly_selected")
    if any(selected.get("options", {}).get(key) != value
           for key, value in caller["required_options"].items()):
        return miss("declared_caller_condition_outside_observed_domain")

    rules = profile["rules"]
    execution = Execution(case, CostModel(case), include_submission=False)
    recipes = {rule["match"]["recipe"] for rule in rules}
    hits = Counter()
    seen = set()
    for op in target_operators(raw, phase=phase, tokens=tokens, context=context, sequences=sequences):
        if op.recipe not in recipes:
            continue
        seen.add(op.recipe)
        axes = _operator_axes(execution, op)
        matches = [rule for rule in rules if _matches(axes, rule)]
        if len(matches) > 1:
            raise ValueError("overlapping_native_observation_domains:" + op.recipe)
        if not matches:
            provenance["unmatched_native_boundary"] = {
                "recipe": op.recipe, "active_shape": list(op.local_shape),
            }
            return miss("active_abi_or_declared_source_condition_outside_domain")
        hits[matches[0]["id"]] += 1
    if seen != recipes:
        return miss("required_native_boundaries_not_present")

    kernels = result["runtime"]["kernels"]
    previous = kernels.get("service_regimes", [])
    replaced = [rule for rule in previous if rule.get("match", {}).get("recipe") in recipes
                and rule.get("match", {}).get("phase") == phase]
    kernels["service_regimes"] = [rule for rule in previous if rule not in replaced]
    imported = [deepcopy(rule) for rule in rules if rule["id"] in hits]
    for rule in imported:
        rule["provenance"]["profile_sha256"] = identity["sha256"]
    kernels["service_regimes"].extend(imported)
    provenance.update(
        status="applied", reason="all_selected_native_boundaries_within_observed_domain",
        matched_domains=[{"id": key, "occurrences": count} for key, count in sorted(hits.items())],
        replaced_rule_ids=[rule["id"] for rule in replaced], imported_rule_count=len(imported),
    )
    return result, provenance
