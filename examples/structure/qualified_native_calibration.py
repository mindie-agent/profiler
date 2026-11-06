"""Explicitly opt in to frozen qualified A2/A5 native calibration profiles.

[Role] Bind the frozen A2 FIA/W8A8-dense and A5 prefill-attention/ChunkFwdH
  native service responses to ordinary Sim graphs, but only when the caller
  names the profile and supplies the actual retained native ABI.
[Invariants] Archived native profiles, default Sim, model names, case IDs and
  observed durations select nothing. The profile never assigns its own ABI
  labels to an incompatible caller declaration. A geometry/hardware/runtime
  outside the frozen domain keeps ordinary prediction and reports a reason; a
  malformed profile/ABI declaration is a visible typed error. One declared
  queue replaces the analytical schedule, whose reference work remains
  reported and is never charged twice.
[Timeouts & Locks] One bounded local JSON profile, one bounded target graph and
  one finite rule list. Files are hashed once per process; no locks, network,
  subprocesses or device work.
[Side-Effect Policy] Read packaged profiles and return a copied input plus
  provenance. No file, capture, archive or simulator state is written.
The two names below are fixed packaged files, not a registration API or a new
profile registry; adding a profile requires a reviewed source change here.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
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
from qualified_native_abi import (
    QualifiedAbiMismatch, QualifiedCalibrationError, check_caller_native_entity,
    validate_native_abi)


ROOT = Path(__file__).resolve().parent
PROFILE_DIR = ROOT / "profiles"
SCHEMA = "mindie-profiler-qualified-native-calibration/1"
IMPORT_SCHEMA = "mindie-profiler-qualified-native-calibration-import/1"
PROFILES = {
    "a2-fia-dense": PROFILE_DIR / "a2_fia_dense_qualified_20261107.json",
    "a5-attention": PROFILE_DIR / "a5_attention_qualified_20261107.json",
}
_RUNTIME_FIELDS = ("vllm_impl", "vllm_version", "kernel_format")


class QualifiedCalibrationIOError(QualifiedCalibrationError):
    """The profile file cannot be read or decoded."""


class QualifiedProfileError(QualifiedCalibrationError):
    """The profile content is internally inconsistent or unsupported."""


@dataclass(frozen=True)
class QualifiedProfile:
    data: Mapping
    path: Path
    sha256: str

    @property
    def id(self) -> str:
        return self.data["id"]


def profile_names() -> tuple[str, ...]:
    return tuple(PROFILES)


def _profile_path(name) -> Path:
    if isinstance(name, (str, Path)) and str(name) in PROFILES:
        return PROFILES[str(name)]
    path = Path(name)
    if not path.is_absolute():
        path = PROFILE_DIR / path
    return path


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


@lru_cache(maxsize=4)
def _read_profile(path: str) -> QualifiedProfile:
    target = Path(path)
    try:
        data = target.read_bytes()
    except TimeoutError:
        raise
    except OSError as error:
        raise QualifiedCalibrationIOError(f"profile_unreadable:{target}") from error
    try:
        profile = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise QualifiedCalibrationIOError(f"profile_not_json:{target}") from error
    if not isinstance(profile, dict) or profile.get("schema") != SCHEMA:
        raise QualifiedProfileError("unsupported_qualified_native_profile_schema")
    if profile.get("status") not in {"qualified_experimental", "train_only_experimental"}:
        raise QualifiedProfileError("unsupported_qualified_native_profile_status")
    if profile.get("activation") != "explicit_opt_in_named_profile_only":
        raise QualifiedProfileError("qualified_native_profile_must_be_explicit_opt_in")
    required = {"id", "hardware", "families", "projection", "rules", "abi",
                "provenance", "limitations"}
    missing = required - set(profile)
    if missing:
        raise QualifiedProfileError("qualified_native_profile_missing:" + ",".join(sorted(missing)))
    train_only = profile.get("train_only_families", ())
    families = tuple(profile["families"])
    if len(set(families)) != len(families) or not families:
        raise QualifiedProfileError("qualified_native_profile_families_not_unique")
    if not isinstance(profile["rules"], list) or not profile["rules"]:
        raise QualifiedProfileError("qualified_native_profile_rules_not_declared")
    if not isinstance(profile.get("train_only_rules", ()), list):
        raise QualifiedProfileError("qualified_native_profile_train_only_rules_not_list")
    if not isinstance(train_only, list):
        raise QualifiedProfileError("qualified_native_profile_train_only_families_not_list")
    declared = set(families) | set(train_only)
    projection = profile["projection"]
    if not isinstance(projection, dict) or not isinstance(projection.get("families"), dict):
        raise QualifiedProfileError("qualified_native_projection_missing")
    if "queue" not in projection:
        raise QualifiedProfileError("qualified_native_queue_missing")
    queue = projection["queue"]
    if (not isinstance(queue, dict) or not queue.get("resource")
            or float(queue.get("reference_rate", 0)) <= 0
            or queue.get("work_unit") != "busy_ns" or queue.get("units") != 1):
        raise QualifiedProfileError("qualified_native_queue_not_single_busy_ns_unit")
    for family in declared:
        if family not in projection["families"] or family not in profile["abi"]:
            raise QualifiedProfileError("qualified_native_family_contract_missing:" + family)
        spec = projection["families"][family]
        abi = profile["abi"][family]
        if not isinstance(spec, dict) or not isinstance(abi, dict):
            raise QualifiedProfileError("qualified_native_family_contract_not_mapping:" + family)
        if not isinstance(abi.get("fixed"), dict) or not isinstance(abi.get("geometry"), dict):
            raise QualifiedProfileError("qualified_native_abi_contract_missing:" + family)
        if "target_recipes" in spec and not isinstance(spec["target_recipes"], list):
            raise QualifiedProfileError("qualified_native_target_recipes_not_list:" + family)
    for rule in list(profile["rules"]) + list(profile.get("train_only_rules", ())):
        family = dict(rule.get("provenance", {})).get("profile_family")
        if family not in declared:
            raise QualifiedProfileError("qualified_native_rule_family_not_declared:" + str(rule.get("id")))
        if "execution" not in rule or rule["execution"].get("kind") != "joint_native":
            raise QualifiedProfileError("qualified_native_rule_requires_joint_native:" + str(rule.get("id")))
    try:
        RegimePolicy(list(profile["rules"]) + list(profile.get("train_only_rules", ())))
    except Exception as error:
        raise QualifiedProfileError("qualified_native_rule_contract_invalid:" + str(error)) from error
    return QualifiedProfile(data=profile, path=target.resolve(), sha256=sha256(data).hexdigest())


def load_qualified_profile(name="a2-fia-dense") -> QualifiedProfile:
    """Load one named packaged profile; never an implicit or remote default."""
    return _read_profile(str(_profile_path(name)))


def _remove_match(match, spec):
    exact = set(spec.get("remove_match", ())) | set(spec.get("remove_match_exact", ()))
    prefixes = tuple(spec.get("remove_match_prefixes", ()))
    kept, removed = {}, []
    for key, value in match.items():
        if key in exact or any(key.startswith(prefix) for prefix in prefixes):
            removed.append(key)
        else:
            kept[key] = deepcopy(value)
    return kept, sorted(removed)


def _project_rule(profile: QualifiedProfile, source: Mapping, spec: Mapping,
                  queue: Mapping, variant=None) -> dict:
    rule = deepcopy(source)
    match, removed = _remove_match(source["match"], spec)
    rule["match"] = match
    if variant is not None:
        match["family"] = variant
        match.pop("recipe", None)
        rule["id"] = str(source["id"]) + "." + str(variant)
    rule["coordinates"] = deepcopy(source.get("coordinates", {}))
    for name, declaration in dict(spec.get("coordinate_overrides", {})).items():
        rule["coordinates"][name] = deepcopy(declaration)
    execution = dict(source["execution"])
    rule["execution"] = {
        "kind": "joint_native", "resource": queue["resource"],
        "reference_rate": queue["reference_rate"],
        "native_kernel": execution["native_kernel"],
    }
    provenance = dict(rule.get("provenance", {}))
    provenance.update({
        "source_rule_id": source["id"],
        "source_rule_sha256": source["provenance"]["source_rule_sha256"],
        "projection": {
            "removed_match": removed,
            "coordinate_overrides": sorted(dict(spec.get("coordinate_overrides", {}))),
            "family_variant": variant,
            "source_queue": execution.get("resource"),
            "product_queue": queue["resource"],
            "reason": "removed selectors are verified against the declared actual native ABI",
        },
    })
    rule["provenance"] = provenance
    return rule


def _projected_rules(profile: QualifiedProfile, families, queue,
                     include_train_only=False) -> tuple[list[dict], dict]:
    specs = profile.data["projection"]["families"]
    active = list(profile.data["rules"])
    if include_train_only:
        active += list(profile.data.get("train_only_rules", ()))
    projected, removed, overrides, variants = [], set(), set(), {}
    for family in families:
        spec = specs[family]
        family_rules = [rule for rule in active
                        if dict(rule.get("provenance", {})).get("profile_family") == family]
        names = tuple(spec.get("family_variants") or (None,))
        for source in family_rules:
            for variant in names:
                rule = _project_rule(profile, source, spec, queue, variant)
                projected.append(rule)
                removed.update(rule["provenance"]["projection"]["removed_match"])
                overrides.update(rule["provenance"]["projection"]["coordinate_overrides"])
                if variant is not None:
                    variants.setdefault(family, []).append(variant)
    if not projected:
        raise QualifiedProfileError("qualified_native_profile_has_no_rules")
    try:
        RegimePolicy(projected)
    except Exception as error:
        raise QualifiedProfileError("qualified_native_projected_rules_invalid:" + str(error)) from error
    projection = {"removed_match": sorted(removed),
                  "coordinate_overrides": sorted(overrides),
                  "family_variants": {key: sorted(value) for key, value in sorted(variants.items())}}
    return projected, projection


def _raw_contract_reason(raw, profile):
    hardware = raw.get("machine", {}).get("hardware_key") or raw.get("machine", {}).get("sku")
    if not hardware:
        return "hardware_not_declared"
    if hardware != profile.data["hardware"]:
        return "hardware_outside_qualified_domain"
    runtime = raw.get("runtime", {}) or {}
    for key in _RUNTIME_FIELDS:
        if key not in runtime or runtime.get(key) in (None, ""):
            continue
        expected = dict(profile.data.get("runtime", {})).get(key)
        if expected is None or expected == "unknown":
            return "runtime_identity_outside_qualified_domain"
        if runtime.get(key) != expected:
            return "runtime_identity_outside_qualified_domain"
    for key, value in dict(profile.data.get("parallel", {})).items():
        if key in runtime and runtime[key] != value:
            return "parallelism_outside_qualified_domain"
    try:
        case = parse_case(raw)
    except Exception as error:
        raise QualifiedCalibrationError("raw_case_not_parseable") from error
    expected_quant = dict(profile.data.get("source_contract", {}).get("quant", {}))
    actual_quant = case.model.quant.to_dict()
    for key, value in expected_quant.items():
        if key in actual_quant and actual_quant[key] != value:
            return "quantization_outside_qualified_domain"
    return None


def _queue_conflict(raw, profile):
    queue = profile.data["projection"]["queue"]
    resource = queue["resource"]
    try:
        case = parse_case(raw)
    except Exception:
        return True
    for device in case.machine.dies:
        for values, expected in ((dict(device.rates), queue["reference_rate"]),
                                 (dict(device.resource_units), queue["units"]),
                                 (dict(device.work_units), queue["work_unit"])):
            if resource in values and values[resource] != expected:
                return True
    return False


def _matches(axes, rule):
    if any(not axis_equal(lookup(axes, key), value)
           for key, value in rule.get("match", {}).items()):
        return False
    values = coordinates(axes, rule.get("coordinates", {}))
    if values is None:
        return False
    return all(bounds.get("min", 0) <= values[name] <= bounds.get("max", float("inf"))
               for name, bounds in rule.get("domain", {}).items())


def _operator_axes(execution, op):
    scope = dict(op.metadata).get("graph_replay_scope", "none")
    prepared, recipe = execution.prepare(op)
    context = execution._context(prepared, 0, scope, recipe=recipe)
    return _axes(context, physical_rates=False)


def _heldout_label(profile, train_only=False):
    if train_only:
        return "train_only_not_heldout_validated"
    qualification = dict(profile.data.get("provenance", {})).get("qualification", {})
    if qualification.get("priority_families_pass"):
        return "priority_domain_heldout_pass_not_whole_profile"
    if qualification.get("fia_and_dense_heldout_accounted"):
        return "heldout_accounted_not_universal_10pct"
    return "train_only_not_heldout_validated"


def _heldout_status(profile, train_only):
    """Whole-profile validation is never inferred from an accounted heldout."""
    if train_only:
        return False
    qualification = dict(profile.data.get("provenance", {})).get("qualification", {})
    return bool(qualification.get("whole_profile_heldout_pass", False))


def _heldout_evaluated(profile):
    qualification = dict(profile.data.get("provenance", {})).get("qualification", {})
    return bool(qualification.get("priority_families_pass")
                or qualification.get("fia_and_dense_heldout_accounted"))


def _miss(profile, geometry, reason, **extra):
    provenance = {
        "schema_version": IMPORT_SCHEMA,
        "profile": {"id": profile.id, "sha256": profile.sha256,
                    "status": profile.data["status"],
                    "activation": profile.data["activation"]},
        "status": "not_applicable", "reason": reason,
        "geometry": dict(geometry), "observations_modified": False,
        "body_total_fitting": False,
        "provenance": deepcopy(profile.data["provenance"]),
        "limitations": deepcopy(profile.data["limitations"]),
        **extra,
    }
    return provenance


def apply_qualified_native_observations(
    raw: Mapping, *, profile="a2-fia-dense", phase: str, tokens: int,
    context: int, sequences: int = 1, native_abi: Mapping | None = None,
    include_train_only: bool = False, operators=None, recipes=None,
) -> tuple[dict, dict]:
    """Apply one named profile only when its frozen boundary agrees.

    ``native_abi`` is the caller's actual retained ABI, keyed by profile family.
    A missing or disagreeing actual ABI is a typed visible error. A physical
    geometry/hardware/runtime/quantization outside the frozen domain returns the
    caller's raw unchanged plus an ordinary-prediction reason. ``operators`` and
    ``recipes`` may be a declared public call graph (for example the GDN
    scan_prefill callback); otherwise ordinary target operators are generated.
    """
    loaded = (profile if isinstance(profile, QualifiedProfile)
              else load_qualified_profile(profile))
    geometry = {"phase": phase, "tokens": tokens, "context": context,
                "sequences": sequences}
    if (phase not in {"prefill", "decode"} or type(tokens) is not int
            or type(context) is not int or type(sequences) is not int):
        return deepcopy(raw), _miss(loaded, geometry, "geometry_not_declared")
    reason = _raw_contract_reason(raw, loaded)
    if reason:
        return deepcopy(raw), _miss(loaded, geometry, reason)
    if _queue_conflict(raw, loaded):
        return deepcopy(raw), _miss(loaded, geometry, "qualified_queue_declaration_conflict")
    families = list(dict.fromkeys(
        list(loaded.data["families"])
        + (list(loaded.data.get("train_only_families", ())) if include_train_only else [])))
    queue = loaded.data["projection"]["queue"]
    projected, projection = _projected_rules(loaded, families, queue, include_train_only)

    unpriced = deepcopy(raw)
    unpriced.setdefault("runtime", {}).setdefault("kernels", {})["service_regimes"] = []
    case = parse_case(unpriced)
    execution = Execution(case, CostModel(case), recipes=recipes, include_submission=False)
    if operators is None:
        operators = target_operators(raw, phase=phase, tokens=tokens,
                                     context=context, sequences=sequences)
        operator_source = "ordinary_target_operators"
    else:
        operator_source = "caller_declared_public_call"
    rules_by_family = {}
    for rule in projected:
        rules_by_family.setdefault(rule["provenance"]["profile_family"], []).append(rule)
    specs = loaded.data["projection"]["families"]
    matches, counts = [], Counter()
    observed, candidates = Counter(), Counter()
    unmatched = []
    for op in operators:
        candidate_rules = []
        for family in families:
            target = specs[family].get("target_recipes")
            if target is not None and op.recipe not in target:
                continue
            for rule in rules_by_family.get(family, ()):
                selector = rule["match"]
                if (selector.get("family") in (None, op.family)
                        and selector.get("recipe") in (None, op.recipe)
                        and selector.get("phase") in (None, op.phase)):
                    candidate_rules.append(rule)
        if not candidate_rules:
            continue
        candidates.update(rule["provenance"]["profile_family"]
                          for rule in candidate_rules)
        axes = _operator_axes(execution, op)
        hits = [rule for rule in candidate_rules if _matches(axes, rule)]
        if len(hits) > 1:
            raise QualifiedProfileError(
                "qualified_native_overlapping_rules:" + ",".join(rule["id"] for rule in hits))
        if not hits:
            unmatched.append({"recipe": op.recipe, "family": op.family,
                              "phase": op.phase, "local_shape": list(op.local_shape)})
            continue
        rule = hits[0]
        family = rule["provenance"]["profile_family"]
        matches.append((rule, op, axes))
        counts[rule["id"]] += 1
        observed[rule["provenance"]["profile_family"]] += 1
    if unmatched:
        return deepcopy(raw), _miss(
            loaded, geometry, "qualified_native_boundary_outside_domain",
            unmatched_boundaries=unmatched[:20],
            candidate_families=sorted(candidates))
    if not matches:
        return deepcopy(raw), _miss(
            loaded, geometry, "qualified_native_boundary_not_present",
            observed_boundaries=dict(observed))
    if not isinstance(native_abi, Mapping):
        raise QualifiedAbiMismatch("actual_native_abi_not_declared")
    abi_summaries = {}
    for family in sorted(observed):
        record = native_abi.get(family)
        if record is None:
            raise QualifiedAbiMismatch("actual_native_abi_not_declared", family=family)
        contract = loaded.data["abi"][family]
        family_matches = [(rule, match_op, axes) for rule, match_op, axes in matches
                          if rule["provenance"]["profile_family"] == family]
        rule, op, _ = family_matches[0]
        abi_summaries[family] = validate_native_abi(
            contract, family, record, op, rule, rule["provenance"]["source_rule_id"])
        for _, match_op, axes in family_matches:
            check_caller_native_entity(match_op, axes, family, contract)

    result = deepcopy(raw)
    kernels = result.setdefault("runtime", {}).setdefault("kernels", {})
    previous = kernels.get("service_regimes", []) or []
    owned = {_canonical(rule) for rule in projected}
    previous = [rule for rule in previous if _canonical(rule) not in owned]
    existing_ids = {rule.get("id") for rule in previous}
    if existing_ids & {rule["id"] for rule in projected}:
        return deepcopy(raw), _miss(loaded, geometry, "qualified_rule_id_collision")
    for rule, op, axes in matches:
        if any(_matches(axes, old) for old in previous):
            return deepcopy(raw), _miss(
                loaded, geometry, "existing_response_overlaps_qualified_boundary",
                conflicting_rule=rule["id"], recipe=op.recipe)
    kernels["service_regimes"] = previous + [deepcopy(rule) for rule in projected]
    device = result.setdefault("machine", {}).setdefault("device", {})
    if not isinstance(device, dict):
        return deepcopy(raw), _miss(loaded, geometry, "machine_device_not_declared")
    device.setdefault("rates", {})[queue["resource"]] = queue["reference_rate"]
    device.setdefault("resource_units", {})[queue["resource"]] = queue["units"]
    device.setdefault("work_units", {})[queue["resource"]] = queue["work_unit"]

    declared_train_only = set(loaded.data.get("train_only_families", ()))
    train_only = sorted({rule["provenance"]["profile_family"] for rule, _, _ in matches
                         if rule["provenance"]["profile_family"] in declared_train_only})
    provenance = _miss(loaded, geometry, "declared_boundary_applied")
    provenance.update({
        "status": "applied",
        "reason": "actual_native_abi_and_boundaries_within_qualified_domain",
        "queue": deepcopy(queue),
        "native_abi": abi_summaries,
        "projection": projection,
        "matched_boundaries": [{
            "rule_id": rule["id"], "source_rule_id": rule["provenance"]["source_rule_id"],
            "profile_family": rule["provenance"]["profile_family"],
            "recipe": op.recipe, "occurrences": counts[rule["id"]],
            "local_shape": list(op.local_shape),
        } for rule in {rule["id"]: rule for rule, _, _ in matches}.values()],
        "train_only_families_applied": train_only,
        "heldout_validated": _heldout_status(loaded, train_only),
        "heldout_evaluated": _heldout_evaluated(loaded),
        "heldout_status": _heldout_label(loaded, bool(train_only)),
        "operator_source": operator_source,
        "calibration_boundary": "observed_single_local_native_kernel",
    })
    return result, provenance


def qualified_prediction_provenance(provenance: Mapping) -> dict:
    """Return the compact cache-facing identity for one qualified application."""
    return {
        "schema_version": provenance.get("schema_version"),
        "profile": provenance.get("profile"),
        "status": provenance.get("status"),
        "reason": provenance.get("reason"),
        "native_abi": provenance.get("native_abi"),
        "queue": provenance.get("queue"),
        "matched_boundaries": provenance.get("matched_boundaries"),
        "train_only_families_applied": provenance.get("train_only_families_applied"),
    }


def _main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(
        description="Apply a frozen qualified native calibration profile explicitly.")
    parser.add_argument("--profile", default="a2-fia-dense", choices=profile_names())
    parser.add_argument("--case", required=True, help="raw Sim case JSON")
    parser.add_argument("--case-key", help="optional top-level key selecting one raw case")
    parser.add_argument("--abi", required=True, help="actual native ABI JSON, keyed by family")
    parser.add_argument("--abi-key", help="optional top-level key selecting one ABI record set")
    parser.add_argument("--phase", default="prefill")
    parser.add_argument("--tokens", type=int, required=True)
    parser.add_argument("--context", type=int, default=0)
    parser.add_argument("--sequences", type=int, default=1)
    parser.add_argument("--include-train-only", action="store_true")
    args = parser.parse_args(argv)
    raw = json.loads(Path(args.case).read_text(encoding="utf-8"))
    if args.case_key is not None:
        raw = raw[args.case_key]
    abi = json.loads(Path(args.abi).read_text(encoding="utf-8"))
    if args.abi_key is not None:
        abi = abi[args.abi_key]
    applied, provenance = apply_qualified_native_observations(
        raw, profile=args.profile, phase=args.phase, tokens=args.tokens,
        context=args.context, sequences=args.sequences, native_abi=abi,
        include_train_only=args.include_train_only)
    print(json.dumps({"applied_rules": len(applied.get("runtime", {}).get(
        "kernels", {}).get("service_regimes", [])), "provenance": provenance},
        indent=2, sort_keys=True))


if __name__ == "__main__":
    _main()
