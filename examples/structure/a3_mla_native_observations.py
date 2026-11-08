"""Install qualified static physical service profiles; never price a geometry.

[Role] Bind independently trained native responses by immutable physical
  identity so the simulator, not the caller's outer geometry, resolves the
  numerical domain.
[Invariants] ``B(raw)`` is deterministic, ``B(B(raw)) == B(raw)``, and the
  caller's declaration is never mutated. Installed parameters are independent
  of evaluation order, ``(tokens, context, sequences)``, layer count and any
  previously installed timing value. Qualification uses captured ABI and
  immutable implementation declarations only; M1/M19 calls may receive the
  output-A rule and fall back analytically outside its M2-M18 domain.
[Timeouts & Locks] Small local profile reads and finite rule lists; no waits,
  subprocesses, device contexts or locks.
[Side-Effect Policy] Read profile files, copy the input and return provenance.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
import math
from pathlib import Path

from mindie_sim.prediction.service_regimes import RegimePolicy, axis_equal
from mindie_sim.prediction.structure import parse_case

from capture_mla_structure import MARKER


PROFILE = Path(__file__).with_name("profiles") / "a3_sharedkv_output_a_20261107.json"
STATIC_PROFILE = Path(__file__).with_name("profiles") / "a3_static_service_20261107.json"

_EXPECTED_OUTPUT_A_ABI = {
    "kind": "TransposeBatchMatMul", "groups": 1, "n": 1024, "k": 4096,
    "input_dtype": "bf16", "weight_dtype": "bf16", "output_dtype": "bf16", "layout": "ND",
}
_COMPATIBLE_CALLER_CONTRACT = "BF16 TransposeBatchMatMul G1/N1024/K4096; only mla.o_a changed"
_NATIVE_QUEUE_FIELDS = (("rates", 1e9), ("resource_units", 1), ("work_units", "busy_ns"))
_INFINITY = math.inf


@lru_cache(maxsize=4)
def _profile_bytes(path_text):
    """Cache immutable bytes; parsed documents are copied before returning."""
    content = Path(path_text).read_bytes()
    return content, json.loads(content)


def _load_profile(path):
    """Return a private profile document and its content identity."""
    content, document = _profile_bytes(str(Path(path)))
    return deepcopy(document), {
        "id": document.get("id"),
        "path": str(Path(path)),
        "sha256": sha256(content).hexdigest(),
    }


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _rule_hash(rule):
    return sha256(_canonical(rule).encode("utf-8")).hexdigest()


def _has_qualified_output_a_abi(raw):
    runtime = raw.get("runtime") if isinstance(raw, dict) else None
    metadata = runtime.get("metadata") if isinstance(runtime, dict) else None
    metadata = metadata if isinstance(metadata, dict) else {}
    marker = metadata.get(MARKER)
    if isinstance(marker, dict) and marker.get("output_a") == _EXPECTED_OUTPUT_A_ABI:
        return True
    variant = metadata.get("compatible_caller_variant")
    return isinstance(variant, dict) and variant.get("quant_contract") == _COMPATIBLE_CALLER_CONTRACT


def _has_captured_mla_abi(raw):
    """The shared-KV capture declaration qualifies the A3 static profile."""
    runtime = raw.get("runtime") if isinstance(raw, dict) else None
    metadata = runtime.get("metadata") if isinstance(runtime, dict) else None
    metadata = metadata if isinstance(metadata, dict) else {}
    if isinstance(metadata.get(MARKER), dict):
        return True
    variant = metadata.get("compatible_caller_variant")
    return isinstance(variant, dict) and bool(variant.get("quant_contract"))


def _machine_hardware(raw):
    try:
        case = parse_case(raw)
    except (KeyError, TypeError, ValueError):
        return ""
    return str(case.machine.hardware_key or case.machine.sku or "")


def _native_queue_conflicts(raw):
    """A declared native queue is single-unit busy-ns at an explicit 1e9 rate."""
    try:
        case = parse_case(raw)
    except (KeyError, TypeError, ValueError):
        return True
    for die in case.machine.dies:
        for values, expected in (("rates", 1e9), ("resource_units", 1),
                                 ("work_units", "busy_ns")):
            declared = dict(getattr(die, values))
            if ("native_call_service" in declared
                    and declared["native_call_service"] != expected):
                return True
    return False


def _domain_box(rule):
    """Map each declared physical coordinate path to its closed interval."""
    coordinates = rule.get("coordinates")
    coordinates = coordinates if isinstance(coordinates, dict) else {}
    box = {}
    for name, bounds in (rule.get("domain") or {}).items():
        declaration = coordinates.get(name)
        if not isinstance(declaration, dict) or "path" not in declaration:
            return None
        if set(declaration) - {"path", "reduce", "scale"}:
            return None
        scale = declaration.get("scale", 1)
        if (isinstance(scale, bool) or not isinstance(scale, (int, float))
                or scale <= 0 or scale == _INFINITY or scale != scale):
            return None
        reducer = declaration.get("reduce", "sum")
        low = bounds.get("min", 0) / scale
        high = (bounds["max"] / scale) if "max" in bounds else _INFINITY
        path = (declaration["path"], reducer)
        if path in box:
            previous = box[path]
            low = max(low, previous[0])
            high = min(high, previous[1])
        box[path] = (low, high)
    return box


def _selectors_can_overlap(left, right):
    """Selectors overlap unless the same physical path names different values."""
    left_match = left.get("match") or {}
    right_match = right.get("match") or {}
    for path in set(left_match) & set(right_match):
        if not axis_equal(left_match[path], right_match[path]):
            return False
    return True


def _regime_rules_overlap(left, right):
    """Conservatively decide whether two installed responses can both apply.

    Domains are compared as closed boxes over physical coordinate paths. Two
    rules are disjoint only when a shared coordinate path has disjoint
    intervals; any uncomparable coordinate is treated as potential overlap and
    is rejected instead of being silently assumed harmless.
    """
    if not _selectors_can_overlap(left, right):
        return False
    left_box = _domain_box(left)
    right_box = _domain_box(right)
    if left_box is None or right_box is None:
        return True
    if not left_box or not right_box:
        return True
    disjoint = False
    shared = set(left_box) & set(right_box)
    for path in shared:
        left_low, left_high = left_box[path]
        right_low, right_high = right_box[path]
        if max(left_low, right_low) > min(left_high, right_high):
            disjoint = True
    if disjoint:
        return False
    if set(left_box) != set(right_box):
        return True
    return True


def _merge_candidates(existing, candidates, supersedes=None):
    """Return the merged declaration plus duplicate/conflict accounting.

    A same-ID payload may change only when the profile explicitly owns the old
    payload by hash. ID ownership alone is not a sufficient replacement
    contract because an edited foreign response can reuse our identifier.
    """
    merged = list(existing)
    by_id = {rule.get("id"): rule for rule in merged}
    added, duplicates, replaced, conflicts = [], [], [], []
    for candidate in candidates:
        rule_id = candidate.get("id")
        current = by_id.get(rule_id)
        if current is not None:
            if _canonical(current) == _canonical(candidate):
                duplicates.append(rule_id)
            elif _rule_hash(current) in (supersedes or {}).get(rule_id, ()):
                overlap = next((rule for rule in merged
                                if rule is not current
                                and _regime_rules_overlap(rule, candidate)), None)
                if overlap is not None:
                    conflicts.append({"id": rule_id, "reason": "foreign_overlapping_rule",
                                      "overlap_id": overlap.get("id")})
                    continue
                merged.remove(current)
                merged.append(candidate)
                by_id[rule_id] = candidate
                replaced.append({"id": rule_id, "superseded_sha256": _rule_hash(current)})
            else:
                conflicts.append({"id": rule_id, "reason": "same_id_different_payload"})
            continue
        overlap = next((rule for rule in merged
                        if _regime_rules_overlap(rule, candidate)), None)
        if overlap is not None:
            conflicts.append({"id": rule_id, "reason": "foreign_overlapping_rule",
                              "overlap_id": overlap.get("id")})
            continue
        merged.append(candidate)
        by_id[rule_id] = candidate
        added.append(rule_id)
    return merged, added, duplicates, replaced, conflicts


def _profile_rules(profile, *, hardware):
    """Validate and copy one flat rule list, or return no applicable rules."""
    rules = profile.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("static_service_profile_requires_nonempty_rule_list")
    RegimePolicy(rules)
    if hardware and profile.get("hardware") not in (None, hardware):
        return []
    return deepcopy(rules)


def _declared_rule_ids(raw):
    runtime = raw.get("runtime") if isinstance(raw, dict) else None
    kernels = runtime.get("kernels") if isinstance(runtime, dict) else None
    rules = kernels.get("service_regimes") if isinstance(kernels, dict) else None
    if not isinstance(rules, list):
        return set()
    return {rule.get("id") for rule in rules if isinstance(rule, dict)}


def _static_groups(raw):
    """Return declaration groups to install without consulting geometry.

    A group may require immutable ABI rule identifiers that the capture already
    declares. Those identifiers qualify the physical implementation; no query
    geometry, layer count or previously installed timing value is consulted.
    """
    hardware = _machine_hardware(raw)
    declared = _declared_rule_ids(raw)
    groups = []
    if _has_qualified_output_a_abi(raw):
        profile, identity = _load_profile(PROFILE)
        rules = _profile_rules(profile, hardware=hardware)
        if rules:
            groups.append({
                "name": "output_a", "profile": profile, "identity": identity,
                "rules": rules, "supersedes": profile.get("supersedes") or {},
                "replace_rule_ids": (),
            })
    if hardware == "Ascend910_9362" and _has_captured_mla_abi(raw):
        profile, identity = _load_profile(STATIC_PROFILE)
        if hardware and profile.get("hardware") not in (None, hardware):
            return groups
        declared_groups = profile.get("groups")
        if declared_groups is None:
            rules = _profile_rules(profile, hardware=hardware)
            declared_groups = [{"id": "static_physical", "rules": rules}]
        for declaration in declared_groups:
            required = set(declaration.get("requires_rule_ids") or ())
            if required and not required <= declared:
                continue
            rules = declaration.get("rules")
            if not isinstance(rules, list) or not rules:
                raise ValueError("static_service_group_requires_nonempty_rule_list")
            RegimePolicy(rules)
            groups.append({
                "name": "static:" + str(declaration.get("id") or "physical"),
                "profile": profile, "identity": identity,
                "rules": deepcopy(rules),
                "supersedes": declaration.get("supersedes") or {},
                "replace_rule_ids": tuple(declaration.get("replace_rule_ids") or ()),
            })
    return groups


def apply_a3_mla_native_observations(raw, *, profile_path=PROFILE,
                                    phase=None, tokens=None, context=None,
                                    sequences=None):
    """Install qualified static physical profiles; do not price a geometry.

    The keyword-only geometry arguments are accepted for backward source
    compatibility with archived replay callers. They are deliberately not read:
    the simulator resolves applicability from physical operator coordinates.
    ``profile_path`` remains a diagnostic override for the output-A profile.
    """
    result = deepcopy(raw)
    provenance = {
        "status": "not_applicable",
        "reason": "captured_mla_abi_not_declared",
        "body_total_fitting": False,
        "validation_timings_used": False,
        "geometry_independent": True,
        "profile": None,
        "installed_rule_ids": [],
        "deduplicated_rule_ids": [],
        "conflicts": [],
    }
    if not isinstance(raw, dict):
        return result, provenance
    groups = _static_groups(raw)
    if not groups:
        return result, provenance
    if _native_queue_conflicts(raw):
        provenance.update(status="conflict",
                          reason="native_service_queue_conflicts_with_declaration")
        return deepcopy(raw), provenance

    kernels = result.setdefault("runtime", {}).setdefault("kernels", {})
    existing = kernels.get("service_regimes")
    if existing is None:
        existing = []
    if not isinstance(existing, list):
        provenance.update(status="conflict", reason="existing_service_regimes_not_a_list")
        return deepcopy(raw), provenance

    merged = list(existing)
    installed, deduplicated, replaced, conflicts, identities = [], [], [], [], []
    for group in groups:
        name, profile, identity = group["name"], group["profile"], group["identity"]
        rules, supersedes = group["rules"], group["supersedes"]
        identities.append(identity)
        if name == "output_a" and profile_path != PROFILE:
            document, identity = _load_profile(Path(profile_path))
            rules = _profile_rules(document, hardware=_machine_hardware(raw))
            supersedes = document.get("supersedes") or {}
            identities[-1] = identity
        replace_ids = set(group.get("replace_rule_ids") or ())
        group_base, pre_replaced, replace_conflicts = [], [], []
        for rule in merged:
            rule_id = rule.get("id")
            if rule_id in replace_ids:
                rule_hash = _rule_hash(rule)
                if rule_hash in (supersedes or {}).get(rule_id, ()):
                    pre_replaced.append({"id": rule_id, "superseded_sha256": rule_hash})
                    continue
                replace_conflicts.append({"id": rule_id, "reason": "same_id_different_payload"})
            group_base.append(rule)
        (group_merged, group_added, group_duplicates,
         group_replaced, group_conflicts) = _merge_candidates(
            group_base, rules, supersedes)
        group_replaced = pre_replaced + group_replaced
        group_conflicts = replace_conflicts + group_conflicts
        if group_conflicts:
            if name == "output_a" or replace_conflicts:
                provenance.update(
                    status="conflict",
                    reason=("existing_output_a_service_preserved"
                            if name == "output_a"
                            else "existing_static_service_preserved"),
                    profile=identities[-1],
                    conflicts=group_conflicts,
                )
                return deepcopy(raw), provenance
            conflicts.extend({"group": name, **entry} for entry in group_conflicts)
            continue
        merged = group_merged
        installed.extend(group_added)
        deduplicated.extend(group_duplicates)
        replaced.extend(group_replaced)

    if not installed and not deduplicated and not replaced:
        provenance.update(status="not_applicable",
                          reason="no_qualified_static_profile_declaration",
                          conflicts=conflicts)
        return deepcopy(raw), provenance

    # Single atomic commit after every group has been validated.
    kernels["service_regimes"] = merged
    device = result.setdefault("machine", {}).setdefault("device", {})
    for field, value in _NATIVE_QUEUE_FIELDS:
        device.setdefault(field, {})["native_call_service"] = value
    provenance.update(
        status="applied",
        reason=("static_physical_profile_installed" if installed else
                "static_physical_profile_superseded" if replaced else
                "static_physical_profile_already_installed"),
        profile=identities[0] if len(identities) == 1 else identities,
        installed_rule_ids=installed,
        deduplicated_rule_ids=deduplicated,
        replaced_rule_payloads=replaced,
        conflicts=conflicts,
        imported_rule_count=len(installed),
    )
    return result, provenance
