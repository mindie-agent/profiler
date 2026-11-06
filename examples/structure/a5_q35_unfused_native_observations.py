"""Bind retained unfused MC2 callers to complete local native responses.

[Role] Preserve source-valid expert rows separately from receive allocation.
[Invariants] Literal captured caller conditions select this conditional path;
  explicit conflicting declarations and unobserved domains retain the input.
  Eight native boundaries use operator means, never a Body residual. Group
  list values are source-derived, not claimed as captured tensor values.
[Timeouts & Locks] One bounded profile and target graph; no waits or locks.
[Side-Effect Policy] Return copied mappings; no capture, device or network I/O.
"""
from collections import Counter
from copy import deepcopy
from pathlib import Path

from mindie_sim import target_operators
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution
from mindie_sim.prediction.service_regimes import axis_equal, coordinates, lookup
from mindie_sim.prediction.structure import parse_case
from mindie_sim.schema.common import ModelingError

from a5_native_observations import _matches, _operator_axes, _physical_contract, _read_profile


PROFILE_PATH = Path(__file__).with_name("profiles") / "a5_q35_unfused_native_20261106.json"
CALLER = {"implementation": "vllm_ascend_mc2_unfused_w8a8", "options": {"global_bs": 0}}
MASK = {"kind": "vllm_ascend_mc2_tp", "global_bs": 0}
QUEUE = "native_call_service"
QUEUE_RATE = 1e9


def _queue_conflict(case):
    for device in case.machine.dies:
        for name, expected in (("rates", QUEUE_RATE), ("resource_units", 1), ("work_units", "busy_ns")):
            values = dict(getattr(device, name))
            if QUEUE in values and values[QUEUE] != expected:
                return True
        if QUEUE in dict(device.service_modes):
            return True
    return False


def _base_physical_contract(case):
    contract = _physical_contract(case)
    for device in contract["devices"]:
        for name in ("rates", "resource_units"):
            device[name].pop(QUEUE, None)
    return contract


def _add_native_queue(result):
    device = result["machine"].setdefault("device", {})
    for name, expected in (("rates", QUEUE_RATE), ("resource_units", 1), ("work_units", "busy_ns")):
        device.setdefault(name, {}).setdefault(QUEUE, expected)
    rebound = []
    # Exact dictionary selectors from prior native profiles must include the
    # newly declared independent queue. Every original rate/unit stays equal;
    # neither the old response nor its measured device service is changed.
    for rule in result["runtime"]["kernels"].get("service_regimes", []):
        match = rule.get("match", {})
        rates = match.get("physical_rates", {}).get("resources")
        maps = ((rates, QUEUE_RATE), (match.get("physical_rates.resources"), QUEUE_RATE),
                (match.get("resource_units"), 1))
        changed = False
        for values, value in maps:
            if isinstance(values, dict) and QUEUE not in values:
                values[QUEUE] = value
                changed = True
        if changed:
            rebound.append(rule["id"])
    return rebound


def _existing_matches(axes, rule):
    """Honor optional fields and missing coordinates of arbitrary old rules."""
    if any(not axis_equal(lookup(axes, key), value) for key, value in rule.get("match", {}).items()):
        return False
    values = coordinates(axes, rule.get("coordinates", {}))
    return values is not None and all(
        name in values and bounds.get("min", 0) <= values[name] <= bounds.get("max", float("inf"))
        for name, bounds in rule.get("domain", {}).items())


def _caller_input(raw, parsed):
    """Supply observed source conditions only when explicit choices agree."""
    runtime = raw["runtime"]
    additional = runtime.get("metadata", {}).get("captured_additional_config", {})
    if (additional.get("enable_force_eplb") is not True or
            additional.get("ascend_fusion_config", {}).get("fusion_ops_gmmswigluquant") is not False):
        return None, "literal_captured_caller_conditions_not_provided"
    kernels = runtime.get("kernels", {})
    if (parsed.runtime.routing != {"policy": "balanced"} or parsed.runtime.moe_recipe != "alltoall"
            or kernels.get("sequence_parallel")):
        return None, "routing_or_parallel_caller_outside_source_domain"
    if "activation_quantization" not in parsed.runtime.lowering_passes:
        return None, "required_activation_quantizer_not_selected"
    expert = parsed.model.quant.for_category("routed_expert")
    if expert.scale_format != "fp32" or expert.scale_bytes != 4:
        return None, "expert_weight_scale_outside_observed_native_abi"
    if any(plan.ffn_activation != "silu" for plan in parsed.model.layer_plans if plan.ffn == "moe"):
        return None, "expert_activation_outside_observed_native_abi"
    lowerings = kernels.get("lowerings", {})
    if ("grouped_int8_caller" in lowerings and lowerings["grouped_int8_caller"] != CALLER
            or "force_eplb_source" in kernels and kernels["force_eplb_source"] != MASK):
        return None, "explicit_native_caller_conflict"
    fusion = lowerings.get("native_fusion", {})
    if "grouped_gate_up_activation_quant" in fusion.get("options", {}).get("roles", ()):
        return None, "explicit_fused_native_caller_conflict"
    if (kernels.get("moe_token_partition", {}).get("kind") != "vllm_ascend_mc2_tp_slice"
            or kernels.get("native_moe_protocol", {}).get("kind") != "arch35_fullmesh"
            or kernels.get("native_moe_protocol", {}).get("dispatch_quant") != "per_token_int8"):
        return None, "required_mc2_source_partition_not_selected"
    model = raw["model"]
    explicit = [model, *model.get("layer_overrides", {}).values(), *model.get("layer_plans", [])]
    if any("router_dtype" in item and item["router_dtype"] != "fp32" for item in explicit):
        return None, "explicit_router_dtype_conflict"
    if any(plan.router_dtype not in ("", "fp32") for plan in parsed.model.layer_plans):
        return None, "router_dtype_outside_observed_domain"
    result = deepcopy(raw)
    result["runtime"]["kernels"].setdefault("lowerings", {})["grouped_int8_caller"] = deepcopy(CALLER)
    result["runtime"]["kernels"]["force_eplb_source"] = deepcopy(MASK)
    # Per-layer overrides retain every existing structural or quantized choice.
    overrides = result["model"].setdefault("layer_overrides", {})
    for plan in parsed.model.layer_plans:
        if plan.ffn == "moe":
            overrides.setdefault(str(plan.index), {})["router_dtype"] = "fp32"
    return result, None


def apply_a5_q35_unfused_native_observations(
    raw: dict, *, phase: str, tokens: int, context: int, sequences: int,
    profile_path: Path = PROFILE_PATH,
) -> tuple[dict, dict]:
    """Import all eight exact native domains atomically, or retain the input."""
    profile, identity = _read_profile(Path(profile_path))
    provenance = {"schema_version": "mindie-profiler-native-observation-import/1",
                  "profile": identity, "status": "not_applicable", "matched_domains": [],
                  "geometry": {"phase": phase, "tokens": tokens, "context": context,
                               "sequences": sequences},
                  "calibration": deepcopy(profile["calibration"]),
                  "observations_modified": False}

    def miss(reason):
        return deepcopy(raw), {**provenance, "reason": reason}

    if phase != "decode" or tokens != 4 or sequences * tokens > 32:
        return miss("sequence_partition_outside_mc2_observed_domain")
    parsed = parse_case(raw)
    contract = profile["source_contract"]
    if ((parsed.machine.hardware_key or parsed.machine.sku) != profile["hardware"] or
            any(getattr(parsed.runtime.parallel, key) != value for key, value in contract["parallel"].items())):
        return miss("hardware_or_parallelism_outside_observed_domain")
    if _queue_conflict(parsed):
        return miss("native_queue_declaration_conflict")
    if _base_physical_contract(parsed) != contract["physical"]:
        return miss("physical_rates_or_declared_runtime_outside_observed_domain")
    if (any(getattr(parsed.model, key) != value for key, value in contract["model"].items()) or
            not parsed.model.layer_plans or any(
                any(getattr(plan, key) != value for key, value in contract["layer"].items())
                for plan in parsed.model.layer_plans)):
        return miss("model_geometry_outside_observed_domain")
    result, reason = _caller_input(raw, parsed)
    if reason:
        return miss(reason)
    rebound = _add_native_queue(result)
    # Domain inspection uses the physical graph without executing any old
    # response. Otherwise an unrelated broad rule can overlap before we decide
    # that replacing it would alter an unobserved native boundary.
    unpriced = deepcopy(result)
    unpriced["runtime"]["kernels"]["service_regimes"] = []
    case = parse_case(unpriced)
    execution = Execution(case, CostModel(case), include_submission=False)
    recipes = {rule["match"]["recipe"] for rule in profile["rules"]}
    hits, seen, native_axes, other_axes = Counter(), set(), [], []
    try:
        operators = target_operators(result, phase=phase, tokens=tokens, context=context, sequences=sequences)
    except ModelingError as error:
        # The selected native caller owns its exact structural domain. A
        # domain miss preserves ordinary prediction, including its own errors.
        if not str(error).startswith("mc2_unfused_"):
            raise
        provenance["native_caller_domain_error"] = str(error)
        return miss("native_caller_contract_outside_observed_domain")
    for op in operators:
        axes = _operator_axes(execution, op)
        if (op.recipe not in recipes or
                op.recipe == "dynamic_quantize" and "mc2_unfused_storage" not in dict(op.metadata)):
            other_axes.append(axes)
            continue
        seen.add(op.recipe)
        native_axes.append(axes)
        matches = [rule for rule in profile["rules"] if _matches(axes, rule)]
        if len(matches) > 1:
            raise ValueError("overlapping_native_observation_domains:" + op.recipe)
        if not matches:
            provenance["unmatched_native_boundary"] = {
                "recipe": op.recipe, "local_shape": list(op.local_shape),
                "padded_shape": list(op.padded_shape)}
            return miss("native_physical_or_source_condition_outside_observed_domain")
        hits[matches[0]["id"]] += 1
    if seen != recipes:
        return miss("required_native_boundaries_not_present")
    kernels = result["runtime"]["kernels"]
    replaced = [rule for rule in kernels.get("service_regimes", [])
                if any(_existing_matches(axes, rule) for axes in native_axes)]
    if any(_existing_matches(axes, rule) for axes in other_axes for rule in replaced):
        return miss("existing_response_spans_observed_and_other_native_boundaries")
    kernels["service_regimes"] = [rule for rule in kernels.get("service_regimes", []) if rule not in replaced]
    imported = [deepcopy(rule) for rule in profile["rules"] if rule["id"] in hits]
    for rule in imported:
        rule["provenance"]["profile_sha256"] = identity["sha256"]
    kernels["service_regimes"].extend(imported)
    provenance.update(status="applied", reason="all_eight_native_boundaries_within_observed_domain",
                      matched_domains=[{"id": key, "occurrences": count} for key, count in sorted(hits.items())],
                      replaced_rule_ids=[rule["id"] for rule in replaced], imported_rule_count=len(imported),
                      added_queue_guard_rule_ids=rebound,
                      group_list_values="source_derived_force_eplb_with_active_prefix_mask_not_captured")
    return result, provenance
