"""Explicitly bind retained A5 native observations to their active ABI domain.

[Role] Import complete local GDN/projection responses for a requested geometry.
[Invariants] Input dictionaries, captures and archives are never mutated. An
  unmatched calibration leaves ordinary prediction available. Unknown binary
  and caller-stride evidence is retained, never promoted to observed identity.
  This is an explicit historical-observation replay/diagnostic arm, not the
  general production price authority: a fixed whole-kernel response may replay
  its measured domain, but must be decomposed into resource/phase services
  before it can enter general prediction. Additive hardware declarations that
  did not exist at capture do not widen the observed domain; every declared
  rate/mode/unit/runtime value remains an exact guard, and a changed or removed
  one falls back to ordinary prediction.
[Timeouts & Locks] One small local profile read and one target graph; no network,
  subprocesses, device contexts, locks or timing-dependent parameter assignment.
[Side-Effect Policy] Return a new input and provenance; write no files or state.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path

from mindie_sim import target_operators
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution
from mindie_sim.prediction.service_regimes import RegimePolicy, _axes, axis_equal, coordinates, lookup
from mindie_sim.prediction.structure import parse_case


PROFILE_PATH = Path(__file__).resolve().parent / "profiles" / "a5_gdn_decode_native_20261106.json"


def _flatten_selector(path: str, value):
    if isinstance(value, dict):
        for name, inner in value.items():
            yield from _flatten_selector(f"{path}.{name}", inner)
    else:
        yield path, value


def _flatten_match(match: dict) -> dict:
    """Express physical guards as exact declared leaves.

    Aggregate equality would reject a retained rule when a newer hardware
    declaration adds an unrelated rate, mode or unit. Flattening keeps every
    measured value an exact guard while leaving additive declarations outside
    the observed domain.
    """
    flat = {}
    for key, value in match.items():
        if key in ("physical_rates", "resource_units", "metadata.mc2_unfused_storage") and isinstance(value, dict):
            for path, leaf in _flatten_selector(key, value):
                flat[path] = leaf
        else:
            flat[key] = value
    return flat


@lru_cache(maxsize=8)
def _read_profile_cached(resolved: str, mtime_ns: int, size: int, flatten_rules: bool) -> tuple[dict, dict]:
    data = Path(resolved).read_bytes()
    profile = json.loads(data)
    if profile["schema_version"] != "mindie-profiler-native-observation-profile/1":
        raise ValueError("unsupported_native_observation_profile")
    if flatten_rules:
        profile["rules"] = [
            {**rule, "match": _flatten_match(rule["match"])}
            for rule in profile["rules"]]
    RegimePolicy(profile["rules"])
    return profile, {"id": profile["id"], "path": resolved,
                     "sha256": sha256(data).hexdigest()}


def _read_profile(path: Path, *, flatten_rules: bool = False) -> tuple[dict, dict]:
    resolved = path.resolve()
    stat = resolved.stat()
    profile, identity = _read_profile_cached(
        str(resolved), stat.st_mtime_ns, stat.st_size, flatten_rules)
    return deepcopy(profile), dict(identity)


_BOUNDARY_CACHE: dict[tuple, tuple[set[str], Counter, dict | None, set[str]]] = {}


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


CONTRACT_FIELDS = ("rates", "compute_peaks", "service_modes", "resource_units")


def _replay_case(raw: dict, physical: dict) -> dict:
    """Prepare a retained case for the current simulator schema.

    Retained cases predate two clean-core changes: they omit rates that used to
    equal SKU defaults, and they may name the removed aggregate ``envelope``
    recipe. The captured profile declares the rates, so pin only omitted keys
    (an explicit caller override still wins). Recipes rejected by the current
    schema are dropped from the replay copy, never from the caller's input.
    """
    result = deepcopy(raw)
    devices = physical.get("devices") or []
    if devices:
        current = parse_case(raw)
        current_rates = ({key for key, _ in current.machine.dies[0].rates}
                         if current.machine.dies else set())
        device = result.setdefault("machine", {}).setdefault("device", {})
        rates = device.setdefault("rates", {})
        for key, value in (devices[0].get("rates") or {}).items():
            # Only resurrect rates the current SKU still declares; a retired
            # supply must remain a declared-domain mismatch.
            if key in current_rates:
                rates.setdefault(key, value)
    recipes = result.get("runtime", {}).get("kernels", {}).get("recipes")
    if isinstance(recipes, dict):
        for name in [name for name, spec in recipes.items()
                     if isinstance(spec, dict) and spec.get("kind") == "envelope"]:
            recipes.pop(name, None)
    return result


def _declared_environment_gaps(declared: dict, current: dict) -> tuple[list[str], list[str]]:
    """Return declared-domain mismatches and current-only physical declarations.

    The retained profile records the hardware/runtime environment under which
    its responses were pooled. Later hardware profiles may add newly declared
    instruction services, modes or resource units; those additions did not
    exist in the observed environment, so they neither widen nor invalidate it.
    Every value that *was* declared must still be present and identical. A
    changed or removed declared value is a real service-supply change and must
    fall back to ordinary prediction rather than reuse the response.
    """
    mismatches: list[str] = []
    additions: list[str] = []
    if declared.get("runtime") != current.get("runtime"):
        mismatches.append("runtime")
    old_devices = declared.get("devices") or []
    new_devices = current.get("devices") or []
    if len(old_devices) != len(new_devices):
        return mismatches + ["devices"], additions
    for index, (old, new) in enumerate(zip(old_devices, new_devices)):
        prefix = f"devices.{index}"
        if old.get("compute_units") != new.get("compute_units"):
            mismatches.append(f"{prefix}.compute_units")
        for field in CONTRACT_FIELDS:
            old_values = old.get(field) or {}
            new_values = new.get(field) or {}
            for key, value in old_values.items():
                if key not in new_values or new_values[key] != value:
                    mismatches.append(f"{prefix}.{field}.{key}")
            additions.extend(f"{prefix}.{field}.{key}"
                             for key in sorted(set(new_values) - set(old_values)))
    return mismatches, additions


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
    profile, identity = _read_profile(Path(profile_path), flatten_rules=True)
    result = _replay_case(raw, profile.get("source_contract") or {})
    provenance = {
        "schema_version": "mindie-profiler-native-observation-import/1",
        "profile": identity, "status": "not_applicable",
        "geometry": {"phase": phase, "tokens": tokens, "context": context,
                     "sequences": sequences},
        "calibration": deepcopy(profile["calibration"]),
        "sources": deepcopy(profile["sources"]),
        "consumption": "explicit_observation_replay",
        "general_production_pricing": False,
        "migration": "decompose_whole_kernel_responses_into_resource_phase_services_before_general_prediction",
        "physical_contract_mismatches": [],
        "undeclared_physical_contract_additions": [],
        "observations_modified": False, "matched_domains": [],
    }

    def miss(reason):
        provenance["reason"] = reason
        return deepcopy(raw), provenance

    partition = profile["sequence_partition"]
    if phase != profile["phase"]:
        return miss("phase_outside_observed_domain")
    if (tokens != partition["tokens_per_sequence"] or
            sequences not in partition["sequences_per_replica"]):
        return miss("sequence_partition_outside_observed_domain")
    case = parse_case(result)
    if (case.machine.hardware_key or case.machine.sku) != profile["hardware"]:
        return miss("hardware_outside_observed_domain")
    if any(getattr(case.runtime.parallel, key) != value
           for key, value in profile["parallel"].items()):
        return miss("parallelism_outside_observed_domain")
    mismatches, additions = _declared_environment_gaps(
        profile["source_contract"], _physical_contract(case))
    provenance["undeclared_physical_contract_additions"] = additions
    if mismatches:
        provenance["physical_contract_mismatches"] = mismatches
        return miss("physical_rates_or_declared_runtime_outside_observed_domain")
    selected = raw.get("runtime", {}).get("kernels", {}).get("lowerings", {}).get("gdn_decode")
    caller = profile["caller_implementation"]
    if not isinstance(selected, dict) or selected.get("implementation") != caller["name"]:
        return miss("required_source_caller_not_explicitly_selected")
    if any(selected.get("options", {}).get(key) != value
           for key, value in caller["required_options"].items()):
        return miss("declared_caller_condition_outside_observed_domain")

    rules = profile["rules"]
    recipes = {rule["match"]["recipe"] for rule in rules}
    b_key = (
        sha256(json.dumps(raw, sort_keys=True, default=repr).encode("utf-8")).hexdigest(),
        identity["sha256"], phase, tokens, context, sequences,
    )
    cached_boundary = _BOUNDARY_CACHE.get(b_key)
    if cached_boundary is None:
        execution = Execution(case, CostModel(case), include_submission=False)
        hits = Counter()
        seen = set()
        unmatched = None
        for op in target_operators(case, phase=phase, tokens=tokens, context=context, sequences=sequences):
            if op.recipe not in recipes:
                continue
            seen.add(op.recipe)
            axes = _operator_axes(execution, op)
            matches = [rule for rule in rules if _matches(axes, rule)]
            if len(matches) > 1:
                raise ValueError("overlapping_native_observation_domains:" + op.recipe)
            if not matches:
                unmatched = {"recipe": op.recipe, "active_shape": list(op.local_shape)}
                break
            hits[matches[0]["id"]] += 1
        if len(_BOUNDARY_CACHE) >= 64:
            _BOUNDARY_CACHE.clear()
        _BOUNDARY_CACHE[b_key] = (recipes, hits, unmatched, seen)
    else:
        recipes, hits, unmatched, seen = cached_boundary
    if unmatched is not None:
        provenance["unmatched_native_boundary"] = deepcopy(unmatched)
        return miss("active_abi_or_declared_source_condition_outside_domain")
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
        rule["provenance"]["consumption"] = "explicit_observation_replay"
        rule["provenance"]["general_production_pricing"] = False
        rule["provenance"]["physical_guard_basis"] = "profile_declared_leaves"
    kernels["service_regimes"].extend(imported)
    provenance.update(
        status="applied", reason="all_selected_native_boundaries_within_observed_domain",
        matched_domains=[{"id": key, "occurrences": count} for key, count in sorted(hits.items())],
        replaced_rule_ids=[rule["id"] for rule in replaced], imported_rule_count=len(imported),
    )
    return result, provenance
