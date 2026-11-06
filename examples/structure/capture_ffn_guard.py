"""Retire legacy routed-FFN rules only when the generated physical matrix domain changes.

[Role] Match service-regime recipes against changed static expert matrix
  descriptors and remove only the affected routed-FFN rules.
[Invariants] Every changed banks/width/hidden axis must be explicitly guarded;
  unrelated rules and surviving values remain exact. No timing values change.
[Timeouts & Locks] Bounded linear list scan; no locks or waits.
[Side-Effect Policy] Mutates only the supplied copied service_regimes list.
"""
from __future__ import annotations


ROUTED_RECIPES = frozenset({"grouped_gate_up", "balanced_grouped_gate_up",
                            "grouped_down", "balanced_grouped_down"})


def _rule_role(rule):
    if not isinstance(rule, dict):
        return None
    match = rule.get("match")
    recipe = match.get("recipe") if isinstance(match, dict) else None
    if recipe not in ROUTED_RECIPES:
        return None
    return "gate_up" if recipe.endswith("grouped_gate_up") else "down"


def _rule_already_guards(rule, role, descriptor, changed_axes):
    """A complete guard must constrain every static axis that actually changed."""
    match = rule.get("match") if isinstance(rule, dict) else None
    if not isinstance(match, dict):
        return False
    guarded = set()
    if match.get("metadata.matrix_weight_bank_groups") == descriptor["banks"]:
        guarded.add("banks")
    if role == "gate_up":
        if match.get("local_shape.1") == 2 * descriptor["width"]:
            guarded.add("width")
        if match.get("local_shape.2") == descriptor["hidden"]:
            guarded.add("hidden")
    else:
        if match.get("local_shape.2") == descriptor["width"]:
            guarded.add("width")
        if match.get("local_shape.1") == descriptor["hidden"]:
            guarded.add("hidden")
    return bool(changed_axes) and set(changed_axes) <= guarded


def guard_legacy_ffn_rules(result, *, before_generated, after_generated,
                           evidence, command_sha256):
    """Retire only routed matrix rules whose generated physical domain changed."""
    if before_generated is None or after_generated is None:
        return {"status": "not_evaluated", "reason": "generated_descriptor_unavailable",
                "timing_values_modified": False}
    changed = {}
    for role in ("gate_up", "down"):
        old = before_generated["roles"].get(role)
        new = after_generated["roles"].get(role)
        if old is None or new is None:
            continue
        if (old["banks"], old["hidden"], old["width"]) != (
                new["banks"], new["hidden"], new["width"]):
            axes = set()
            if old["banks"] != new["banks"]:
                axes.add("banks")
            if old["width"] != new["width"]:
                axes.add("width")
            if old["hidden"] != new["hidden"]:
                axes.add("hidden")
            changed[role] = {"old": old, "new": new, "changed_axes": sorted(axes)}
    if not changed:
        return {"status": "unchanged", "reason": "matrix_physical_boundary_unchanged",
                "removed_ids": [], "removed_count": 0, "timing_values_modified": False}
    runtime = result.get("runtime")
    kernels = runtime.get("kernels") if isinstance(runtime, dict) else None
    regimes = kernels.get("service_regimes") if isinstance(kernels, dict) else None
    if not isinstance(regimes, list):
        return {"status": "not_evaluated", "reason": "service_regimes_not_present",
                "removed_ids": [], "removed_count": 0, "timing_values_modified": False}
    kept, removed = [], []
    already_guarded = False
    for index, rule in enumerate(regimes):
        role = _rule_role(rule)
        if role is None or role not in changed:
            kept.append(rule)
            continue
        new = changed[role]["new"]
        if _rule_already_guards(rule, role, new, changed[role]["changed_axes"]):
            already_guarded = True
            kept.append(rule)
            continue
        removed.append({
            "id": rule.get("id") if isinstance(rule, dict) else None,
            "index": index,
            "recipe": rule.get("match", {}).get("recipe"),
            "old": changed[role]["old"],
            "new": new,
            "changed_axes": changed[role]["changed_axes"],
        })
    if removed:
        kernels["service_regimes"] = kept
    source = evidence.get("source", {})
    return {
        "status": "applied" if removed else "unchanged",
        "reason": ("legacy_routed_ffn_matrix_boundary_changed" if removed
                   else "legacy_routed_ffn_rules_already_guarded" if already_guarded
                   else "no_matching_legacy_routed_ffn_rules"),
        "removed_ids": [item["id"] for item in removed],
        "removed_count": len(removed),
        "kept_count": len(kept),
        "removed": removed,
        "old_descriptors": {role: changed[role]["old"] for role in changed},
        "new_descriptors": {role: changed[role]["new"] for role in changed},
        "changed_axes": {role: changed[role]["changed_axes"] for role in changed},
        "source": {"capture_path": source.get("path"),
                   "capture_sha256": source.get("sha256"),
                   "command_sha256": command_sha256},
        "timing_values_modified": False,
    }
