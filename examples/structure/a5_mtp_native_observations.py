"""Bind retained q4 attention and recurrence responses to physical domains.

[Role] Import complete native operators with explicit active and graph shapes.
[Invariants] Logical requests never include graph padding. q1 and q4 responses
  are separate; context interpolation uses native durations, never Body totals.
  Unknown binary identity remains provenance. Domain misses keep the input.
[Timeouts & Locks] One local profile and active target graph; no waits or locks.
[Side-Effect Policy] Copies input mappings; reads no capture or device state.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path

from mindie_sim import target_operators
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution
from mindie_sim.prediction.structure import parse_case

from a5_native_observations import _matches, _operator_axes, _physical_contract, _read_profile


PROFILE_PATH = Path(__file__).with_name("profiles") / "a5_mtp_native_20261106.json"


def apply_a5_mtp_native_observations(
    raw: dict, *, phase: str, tokens: int, context: int, sequences: int,
    profile_path: Path = PROFILE_PATH,
) -> tuple[dict, dict]:
    """Apply both complete native boundaries only within their declared domain."""
    profile, identity = _read_profile(Path(profile_path))
    result = deepcopy(raw)
    provenance = {
        "schema_version": "mindie-profiler-native-observation-import/1",
        "profile": identity, "status": "not_applicable", "matched_domains": [],
        "geometry": {"phase": phase, "tokens": tokens, "context": context,
                     "sequences": sequences},
        "calibration": deepcopy(profile["calibration"]),
        "observations_modified": False,
    }

    def miss(reason):
        provenance["reason"] = reason
        return result, provenance

    if phase != "decode" or tokens != 4:
        return miss("sequence_partition_outside_observed_domain")
    case = parse_case(raw)
    if (case.machine.hardware_key or case.machine.sku) != profile["hardware"]:
        return miss("hardware_outside_observed_domain")
    contract = profile["source_contracts"].get(str(case.runtime.parallel.tp))
    if contract is None or any(getattr(case.runtime.parallel, name) != value
                               for name, value in contract["parallel"].items()):
        return miss("parallelism_outside_observed_domain")
    if _physical_contract(case) != contract["physical"]:
        return miss("physical_rates_or_declared_runtime_outside_observed_domain")
    caller = raw.get("runtime", {}).get("kernels", {}).get("lowerings", {}).get("gdn_decode")
    if not isinstance(caller, dict) or caller.get("implementation") != "vllm_ascend_gdn_decode":
        return miss("required_source_caller_not_explicitly_selected")
    options = caller.get("options", {})
    if options.get("recurrent_implementation") != "arch35_fp32" or options.get("cache_index_row_stride") != 4:
        return miss("declared_caller_condition_outside_observed_domain")
    recipes = {"flash_attention_decode", "ascend_recurrent_gdn_fp32_state"}
    execution = Execution(case, CostModel(case), include_submission=False)
    hits, seen = Counter(), set()
    for op in target_operators(raw, phase=phase, tokens=tokens, context=context, sequences=sequences):
        if op.recipe not in recipes:
            continue
        seen.add(op.recipe)
        axes = _operator_axes(execution, op)
        matches = [rule for rule in profile["rules"] if _matches(axes, rule)]
        if len(matches) > 1:
            raise ValueError("overlapping_native_observation_domains:" + op.recipe)
        if not matches:
            provenance["unmatched_native_boundary"] = {
                "recipe": op.recipe, "active_shape": list(op.local_shape),
                "padded_shape": list(op.padded_shape),
                "physical_query_rows": dict(op.metadata).get("graph_physical_query_rows"),
            }
            return miss("active_physical_partition_or_context_outside_observed_domain")
        hits[matches[0]["id"]] += 1
    if seen != recipes:
        return miss("required_native_boundaries_not_present")

    kernels = result["runtime"]["kernels"]
    previous = kernels.get("service_regimes", [])
    replaced = [rule for rule in previous if rule.get("match", {}).get("recipe") in recipes
                and rule.get("match", {}).get("phase") == phase]
    kernels["service_regimes"] = [rule for rule in previous if rule not in replaced]
    imported = [deepcopy(rule) for rule in profile["rules"] if rule["id"] in hits]
    for rule in imported:
        rule["provenance"]["profile_sha256"] = identity["sha256"]
    kernels["service_regimes"].extend(imported)
    provenance.update(
        status="applied", reason="both_complete_native_boundaries_within_observed_domain",
        matched_domains=[{"id": key, "occurrences": count} for key, count in sorted(hits.items())],
        replaced_rule_ids=[rule["id"] for rule in replaced], imported_rule_count=len(imported),
    )
    return result, provenance
