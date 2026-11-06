"""Bind retained A3 prefill FlashAttention and TP AllReduce native responses.

[Role] Replace one observed prefill chunk's attention and TP collective
  boundaries with complete native kernel durations.
[Invariants] Every selectable axis is physical: hardware, parallelism, model
  geometry, quantization ABI, declared runtime and the graph's active rows.
  Native means are imported from per-call counts/sums; no Body duration, case
  name or capture path selects a response. Both boundaries change together or
  neither does. An unobserved or ambiguous state keeps the caller's input.
[Timeouts & Locks] One small local profile plus one bounded target graph.
  No device, capture, network, subprocess or timing-dependent selection.
[Side-Effect Policy] Read the packaged profile; return a copied input and
  provenance. Never write files or mutate the caller's mapping.
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
from mindie_sim.prediction.service_regimes import (
    RegimePolicy, _axes, axis_equal, coordinates, lookup)
from mindie_sim.prediction.structure import parse_case


PROFILE_PATH = Path(__file__).with_name("profiles") / "prefill_native_20261106.json"
SCHEMA = "mindie-profiler-prefill-native-observation-profile/1"


def _read_profile(path: Path):
    data = Path(path).read_bytes()
    profile = json.loads(data)
    if profile.get("schema") != SCHEMA or profile.get("phase") != "prefill":
        raise ValueError("unsupported_prefill_native_observation_profile")
    RegimePolicy(profile["service_regimes"])
    return profile, sha256(data).hexdigest()


@lru_cache(maxsize=1)
def _profile():
    return _read_profile(PROFILE_PATH)


def _physical_axes(execution, op):
    """Use the engine's normalized axes, including declared physical rates."""
    scope = dict(op.metadata).get("graph_replay_scope", "none")
    prepared, recipe = execution.prepare(op)
    context = execution._context(prepared, 0, scope, recipe=recipe)
    return _axes(context, physical_rates=True)


def _matches(axes, rule):
    if any(not axis_equal(lookup(axes, key), value)
           for key, value in rule.get("match", {}).items()):
        return False
    values = coordinates(axes, rule.get("coordinates", {}))
    if values is None:
        return False
    return all(bounds.get("min", 0) <= values[name] <= bounds.get("max", float("inf"))
               for name, bounds in rule.get("domain", {}).items())


def _layer_signature(plan, fields):
    return tuple(getattr(plan, name) for name in fields)


def _physical_contract(case):
    """Normalize device rates, links and rank placement for equality checks.

    Equal SKU and TP degree do not identify equal host service or topology.
    The complete derived machine declaration (device pipes, compute peaks,
    service modes, links and placements) stays a selectable physical axis.
    """
    return json.loads(json.dumps({
        "machine": case.machine.to_dict(),
        "parallel": case.runtime.parallel.to_dict(),
    }))


def _source_domain(case, contract):
    """Compare normalized declarations; omitted defaults are equivalent."""
    hardware = case.machine.hardware_key or case.machine.sku
    if hardware != contract["hardware"]:
        return "hardware_outside_observed_domain"
    parallel = case.runtime.parallel.to_dict()
    if any(parallel.get(name) != value for name, value in contract["parallel"].items()):
        return "parallelism_outside_observed_domain"
    if _physical_contract(case) != contract["physical"]:
        return "physical_rates_or_topology_outside_observed_domain"
    if any(getattr(case.model, name) != value for name, value in contract["model"].items()):
        return "model_geometry_outside_observed_domain"
    if not case.model.layer_plans:
        return "layer_geometry_outside_observed_domain"
    fields = contract["layer_fields"]
    declared = Counter(_layer_signature(plan, fields) for plan in case.model.layer_plans)
    expected = Counter({tuple(group["values"]): group["count"]
                        for group in contract["layer_groups"]})
    if declared != expected:
        return "layer_geometry_outside_observed_domain"
    quant = case.model.quant.to_dict()
    if any(key in quant and quant[key] != value
           for key, value in contract["quant"].items()):
        return "quantization_outside_observed_domain"
    for category, required in contract["quant_categories"].items():
        resolved = case.model.quant.for_category(category)
        if any(getattr(resolved, name) != value for name, value in required.items()):
            return "quantization_outside_observed_domain"
    runtime = case.runtime
    if any(getattr(runtime, name) != value for name, value in contract["runtime"].items()):
        return "runtime_outside_observed_domain"
    if any(name not in runtime.lowering_passes for name in contract["lowering_passes"]):
        return "required_source_lowering_not_selected"
    return None


class _DomainMiss(Exception):
    """A requested physical state is outside the retained native domain."""


def _physical_rule(rule):
    """Normalized physical content of an imported response, without provenance."""
    return json.loads(json.dumps({name: rule.get(name) for name in (
        "id", "match", "coordinates", "domain", "response")}))


def _previous_rules(raw, native_rules):
    """Drop only this profile's own earlier physical import.

    Imported rules carry no source identifier or hash. Equality is decided by
    the normalized physical payload, so a foreign rule that reuses one of the
    stable ids but changes a response or domain is retained and reported later.
    """
    owned = {json.dumps(_physical_rule(rule), sort_keys=True) for rule in native_rules}
    return [rule for rule in raw["runtime"]["kernels"].get("service_regimes", [])
            if json.dumps(_physical_rule(rule), sort_keys=True) not in owned]


def _known_historical_contracts(profile):
    """Complete physical payloads of the retained historical response variants.

    Ownership is decided by match/coordinates/domain/response, never by an id
    alone and never by provenance. A caller that edits the physical response
    therefore keeps it and receives a conflict.
    """
    contracts = profile.get("replaced_regime_contracts")
    if contracts is None:
        legacy = profile.get("replaced_regime_contract") or {}
        contracts = [{"id": legacy.get("id"),
                      "match": legacy.get("match"),
                      "coordinates": None, "domain": None,
                      "response": {"fixed_us": value}}
                     for value in (legacy.get("observed_response_by_declared_input_length_us")
                                   or {}).values()]
    known = set()
    for rule in contracts:
        if not rule.get("id"):
            continue
        known.add(json.dumps(_physical_rule(rule), sort_keys=True))
    return known


def _replaced_rules(previous, native_axes, other_axes, native_rules, known_contracts):
    """Return only exact retained historical physical rules for replacement.

    An explicit foreign response that matches a native boundary is a caller
    declaration, not this profile's earlier calibration. It is reported as a
    conflict and never silently overridden. A rule that also matches an
    unrelated native call is likewise preserved.
    """
    owned, spanning, foreign = [], [], []
    for rule in previous:
        on_native = any(_matches(axes, rule) for axes in native_axes)
        on_other = any(_matches(axes, rule) for axes in other_axes)
        if on_native and on_other:
            spanning.append(rule["id"])
        elif on_native:
            if json.dumps(_physical_rule(rule), sort_keys=True) in known_contracts:
                owned.append(rule)
            else:
                foreign.append(rule.get("id", ""))
    if spanning:
        raise _DomainMiss("existing_response_spans_native_and_other_boundaries")
    if foreign:
        raise _DomainMiss("foreign_response_matches_native_boundary:" +
                          ",".join(sorted(foreign)))
    retained = [rule for rule in previous if rule not in owned]
    for axes in native_axes:
        if any(_matches(axes, rule) for rule in retained):
            raise _DomainMiss("retained_response_overlaps_native_boundary")
    ids = {rule["id"] for rule in owned} | {rule["id"] for rule in native_rules}
    if len(ids) != len(owned) + len(native_rules):
        raise _DomainMiss("native_response_id_collides_with_existing_rule")
    return owned


def _boundary_counts(operators, expected):
    counts = Counter(op.recipe for op in operators if op.recipe in expected)
    return counts


def apply_prefill_native_observations(
    raw: dict, *, phase: str, tokens: int, context: int, sequences: int = 1,
    profile_path: Path = PROFILE_PATH,
) -> tuple[dict, dict]:
    """Replace attention and TP collective responses for one observed chunk.

    The imported rules describe complete native kernels. They never absorb an
    internal Body gap, and they never select a caller from observed timing.
    """
    profile, digest = (_profile() if Path(profile_path) == PROFILE_PATH
                       else _read_profile(profile_path))
    domain = profile["physical_domain"]
    provenance = {
        "schema_version": "mindie-profiler-native-observation-import/1",
        "profile": {"id": profile["id"], "sha256": digest},
        "status": "not_applicable",
        "geometry": {"phase": phase, "tokens": tokens, "context": context,
                     "sequences": sequences},
        "calibration": deepcopy(profile["calibration"]),
        "observations_modified": False,
        "body_total_fitting": False,
        "capture_binary_identity": "unknown",
        "native_boundaries": deepcopy(profile["native_observations"]),
    }

    def miss(reason):
        return deepcopy(raw), {**provenance, "reason": reason}

    if phase != profile["phase"]:
        return miss("phase_outside_observed_domain")
    if sequences != domain["sequences"]:
        return miss("sequence_partition_outside_observed_domain")
    if type(tokens) is not int or type(context) is not int:
        return miss("geometry_outside_observed_domain")
    if tokens != domain["query_rows"]:
        return miss("prefill_chunk_rows_outside_observed_domain")
    if not domain["context_min"] <= context <= domain["context_max"]:
        return miss("prefill_context_outside_observed_domain")
    hardware = raw.get("machine", {}).get("hardware_key") or raw.get("machine", {}).get("sku")
    if hardware and hardware != profile["source_contract"]["hardware"]:
        return miss("hardware_outside_observed_domain")

    if raw.get("runtime", {}).get("kernels", {}).get("sequence_parallel"):
        return miss("sequence_parallel_outside_observed_domain")
    parsed = parse_case(raw)
    reason = _source_domain(parsed, profile["source_contract"])
    if reason:
        return miss(reason)

    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    operators = target_operators(raw, **geometry)
    expected = profile["physical_domain"]["calls_per_forward"]
    counts = _boundary_counts(operators, expected)
    if dict(counts) != expected:
        provenance["observed_boundary_counts"] = dict(counts)
        return miss("native_boundary_counts_outside_observed_domain")
    for op in operators:
        if op.recipe == "flash_attention":
            if op.local_shape[:2] != (tokens, context + tokens):
                provenance["unmatched_native_boundary"] = {
                    "recipe": op.recipe, "local_shape": list(op.local_shape)}
                return miss("attention_active_shape_outside_observed_domain")
        elif op.recipe in expected and dict(op.metadata).get("graph_active_query_rows") != tokens:
            provenance["unmatched_native_boundary"] = {
                "recipe": op.recipe, "active_rows": dict(op.metadata).get("graph_active_query_rows")}
            return miss("collective_active_rows_outside_observed_domain")

    rules = [deepcopy(rule) for rule in profile["service_regimes"]]
    # Rule selectors never depend on a response. Inspect axes on an unpriced
    # copy so a pre-existing overlapping declaration is reported by this
    # adapter instead of failing while its own old response is being evaluated.
    unpriced = deepcopy(raw)
    unpriced.setdefault("runtime", {}).setdefault("kernels", {})["service_regimes"] = []
    probe = parse_case(unpriced)
    execution = Execution(probe, CostModel(probe), include_submission=False)
    native_axes, other_axes = [], []
    hits = Counter()
    for op in operators:
        axes = _physical_axes(execution, op)
        if op.recipe not in expected:
            other_axes.append(axes)
            continue
        native_axes.append(axes)
        matching = [rule for rule in rules if _matches(axes, rule)]
        if len(matching) != 1:
            provenance["unmatched_native_boundary"] = {
                "recipe": op.recipe, "matching_native_rules": len(matching),
                "local_shape": list(op.local_shape)}
            return miss("native_physical_condition_outside_observed_domain")
        hits[matching[0]["id"]] += 1
    if any(hits[rule["id"]] != rule["provenance"]["calls_per_forward"] for rule in rules):
        return miss("native_boundary_counts_outside_observed_domain")

    try:
        previous = _previous_rules(raw, rules)
        replaced = _replaced_rules(previous, native_axes, other_axes, rules,
                                   _known_historical_contracts(profile))
    except _DomainMiss as error:
        return miss(str(error))

    result = deepcopy(raw)
    kernels = result["runtime"]["kernels"]
    kernels["service_regimes"] = [rule for rule in previous if rule not in replaced]
    imported = [{name: deepcopy(rule[name]) for name in (
        "id", "match", "coordinates", "domain", "response")} for rule in rules]
    kernels["service_regimes"].extend(imported)
    provenance.update(
        status="applied", reason="attention_and_collective_boundaries_within_observed_domain",
        matched_domains=[{"id": key, "occurrences": value}
                         for key, value in sorted(hits.items())],
        replaced_rule_ids=[rule["id"] for rule in replaced],
        imported_rule_count=len(rules),
        imported_rules=[{
            "id": rule["id"],
            "calls_per_forward": rule["provenance"]["calls_per_forward"],
            "call_count": rule["provenance"]["call_count"],
            "response_unit": rule["provenance"]["response_unit"],
            "native_boundary": rule["provenance"]["native_boundary"],
            "native_class": rule["provenance"].get("native_class"),
            "per_call_interval_us": rule["provenance"].get("per_call_interval_us"),
            "training_source_ids": list(rule["provenance"]["training_source_ids"]),
            "profile_sha256": digest,
        } for rule in rules],
    )
    return result, provenance
