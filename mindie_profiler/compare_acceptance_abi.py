"""Simulation-vs-capture acceptance checks and native operator comparison (compare_acceptance_abi).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting simulation-vs-capture acceptance checks and native operator comparison.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from .compare_acceptance_helpers import _canon, _native_finite, _native_request_id, _native_sha

def _native_abi(record: Mapping[str, Any]) -> dict[str, Any]:
    """Consume shared ``native_tensor_abi`` qualification without re-promoting gaps.

    A record already marked incomplete/candidate/conflict is returned as such:
    re-projecting its retained slots cannot erase issues or a declared conflict.
    A complete record with slots is re-qualified only to verify its digest; a
    stale digest becomes a conflict receipt with ``digest=None``.
    """
    from .native_tensor_abi import native_abi_from_slots

    operator = record.get("native_operator")
    if not operator and isinstance(record.get("boundary"), Mapping):
        operator = record["boundary"].get("native_operator")
    abi = record.get("abi")
    if isinstance(abi, Mapping):
        status = abi.get("status")
        if status == "conflict":
            return {
                **dict(abi), "status": "conflict", "digest": None,
                "verified": False,
                "declared_digest": abi.get("declared_digest"),
                "computed_digest": abi.get("computed_digest"),
                "issues": list(abi.get("issues") or (
                    [{"slot": "abi.digest", "reason": "abi_digest_mismatch"}],)),
            }
        if status in {"incomplete", "candidate"}:
            return {
                **dict(abi), "status": status, "digest": None,
                "verified": False,
            }
        declared = abi.get("digest")
        has_slots = abi.get("inputs") is not None and abi.get("outputs") is not None
        if has_slots and status == "complete" and declared is None:
            return {
                **dict(abi), "status": "incomplete", "digest": None,
                "verified": False, "computed_digest": None,
                "issues": [*abi.get("issues", ()),
                           {"slot": "abi.digest",
                            "reason": "missing_declared_digest"}],
            }
        if has_slots:
            computed = native_abi_from_slots(
                abi.get("native_operator") or operator,
                abi.get("inputs") or (), abi.get("outputs") or ())
            if status == "complete" and computed.get("status") == "complete":
                if declared is not None and declared != computed.get("digest"):
                    return {
                        "schema": "mindie-native-tensor-abi/1",
                        "status": "conflict",
                        "native_operator": computed.get("native_operator"),
                        "inputs": computed.get("inputs"),
                        "outputs": computed.get("outputs"),
                        "slot_count": computed.get("slot_count"),
                        "digest": None, "declared_digest": declared,
                        "computed_digest": computed.get("digest"),
                        "verified": False,
                        "issues": [{"slot": "abi.digest",
                                    "reason": "abi_digest_mismatch"}],
                    }
                computed["declared_digest"] = declared
                computed["digest_source"] = "slots_recomputed"
                return computed
            if status == "complete":
                return {
                    **computed, "status": "incomplete",
                    "declared_digest": declared,
                    "computed_digest": None, "digest": None,
                    "verified": False,
                }
            return computed
        if isinstance(declared, str) and declared.startswith("sha256:"):
            return {
                "schema": "mindie-native-tensor-abi/1",
                "status": "complete" if status == "complete" else "incomplete",
                "native_operator": abi.get("native_operator") or operator,
                "inputs": None, "outputs": None,
                "slot_count": abi.get("slot_count"),
                "digest": declared if status == "complete" else None,
                "declared_digest": declared, "computed_digest": None,
                "verified": False, "digest_source": "declared_only",
                "issues": list(abi.get("issues") or (
                    [{"slot": "abi.slots", "reason": "abi_slots_not_declared"}],)),
            }
    digest = record.get("native_abi_sha256")
    if (isinstance(digest, str) and digest.startswith("sha256:")
            and isinstance(operator, str) and operator):
        return {
            "schema": "mindie-native-tensor-abi/1", "status": "complete",
            "native_operator": operator, "inputs": None, "outputs": None,
            "slot_count": None,
            "digest": digest, "declared_digest": digest,
            "computed_digest": None, "verified": False,
            "digest_source": "declared_only",
            "issues": [{"slot": "abi.slots", "reason": "abi_slots_not_declared"}],
        }
    return {
        "schema": "mindie-native-tensor-abi/1", "status": "incomplete",
        "native_operator": operator, "inputs": None, "outputs": None,
        "slot_count": None, "digest": None, "verified": False,
        "issues": [{"slot": "abi", "reason": "native_abi_missing"}],
    }

def _native_boundary(record: Mapping[str, Any]) -> tuple[dict[str, Any], set[str]]:
    raw = record.get("boundary")
    boundary = {
        "kind": None, "native_operator": None, "scope": None, "expansion": None,
        "fusion": {"status": None, "members": [], "member_count": 0,
                   "allocation": "none"},
    }
    provided: set[str] = set()
    fusion = None
    if isinstance(raw, Mapping):
        for field in ("kind", "native_operator", "scope", "expansion"):
            if raw.get(field) is not None:
                boundary[field] = raw[field]
                provided.add(field)
        if "fusion" in raw:
            fusion = raw.get("fusion")
    elif isinstance(raw, str):
        boundary["kind"] = raw
        provided.add("kind")
    if fusion is None and isinstance(record.get("fusion"), Mapping):
        fusion = record.get("fusion")
    if fusion is None and "fusion_members" in record:
        fusion = {"members": record.get("fusion_members")}
    if isinstance(fusion, Mapping) and fusion.get("members") is not None:
        members = sorted(str(item) for item in fusion.get("members") or ())
        boundary["fusion"] = {
            "status": fusion.get("status"), "members": members,
            "member_count": len(members),
            "allocation": fusion.get("allocation", "none"),
        }
        provided.add("fusion_members")
    if boundary["native_operator"] is None:
        operator = record.get("native_operator")
        if isinstance(operator, str) and operator:
            boundary["native_operator"] = operator
            provided.add("native_operator")
    return boundary, provided

def _native_conditions(record: Mapping[str, Any]) -> tuple[dict[str, Any], set[str]]:
    """Return the complete declared-condition mapping, including null values.

    The mapping is the canonical semantic projection used by request dedupe,
    group consistency, no-ID lookup, same-ID checks and final comparison.  A
    whitelist would drop new condition keys; provenance and gaps live in the
    sibling ``condition_sources``/``condition_gaps``/``condition_conflicts``
    fields so they do not rewrite the declared values.
    """
    raw = record.get("conditions")
    if not isinstance(raw, Mapping):
        return {}, set()
    return dict(raw), set(raw)

def _native_condition_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item)]
    return []

def _native_condition_gap_rows(value: Any) -> list[dict[str, Any]]:
    """Normalize declared condition gaps without deleting explicit nulls."""
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(value, Mapping):
        value = [{"field": key, "reason": reason} for key, reason in value.items()]
    if not isinstance(value, (list, tuple)):
        return []
    for item in value:
        if isinstance(item, str) and item:
            field, reason = item, "not_declared"
        elif isinstance(item, Mapping) and item.get("field"):
            field = str(item["field"])
            reason = str(item.get("reason") or "not_declared")
        else:
            continue
        rows[(field, reason)] = {"field": field, "reason": reason}
    return [rows[key] for key in sorted(rows)]

def _native_condition_conflict_rows(value: Any) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    if isinstance(value, Mapping):
        value = [{"field": key, "values": [val]} for key, val in value.items()]
    if not isinstance(value, (list, tuple)):
        return []
    for item in value:
        if isinstance(item, str) and item:
            field, values, sources = item, [], []
        elif isinstance(item, Mapping) and item.get("field"):
            field = str(item["field"])
            raw_values = item.get("values")
            values = (list(raw_values) if isinstance(raw_values, (list, tuple))
                      else [raw_values] if raw_values is not None else [])
            sources = _native_condition_strings(item.get("sources"))
        else:
            continue
        canonical = _canon(values)
        rows[(field, canonical)] = {
            "field": field, "values": values, "sources": sources,
        }
    return [rows[key] for key in sorted(rows)]

def _native_condition_meta(record: Mapping[str, Any]) -> tuple[
        dict[str, Any], dict[str, list[str]], list[dict[str, Any]],
        list[dict[str, Any]]]:
    conditions = _native_conditions(record)[0]
    raw_sources = record.get("condition_sources")
    sources: dict[str, list[str]] = {}
    if isinstance(raw_sources, Mapping):
        for key, value in raw_sources.items():
            labels = _native_condition_strings(value)
            if labels:
                sources[str(key)] = labels
    return (
        conditions, sources,
        _native_condition_gap_rows(record.get("condition_gaps")),
        _native_condition_conflict_rows(record.get("condition_conflicts")),
    )

def _native_flat_conditions(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Flatten declared conditions to named leaf paths for explicit reports."""
    flat: dict[str, Any] = {}

    def visit(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            if not item:
                flat[path or "conditions"] = {}
                return
            for key, child in item.items():
                visit(child, f"{path}.{key}" if path else str(key))
            return
        flat[path or "conditions"] = item

    visit(dict(value or {}), "")
    return flat

def _native_condition_differences(
    observed: Mapping[str, Any], predicted: Mapping[str, Any],
) -> list[str]:
    """Name every observed leaf that the prediction does not reproduce."""
    left = _native_flat_conditions(observed)
    right = _native_flat_conditions(predicted)
    return [
        path for path in sorted(left)
        if path not in right or _canon(left[path]) != _canon(right[path])
    ]

def _native_condition_difference_paths(
    left: Mapping[str, Any], right: Mapping[str, Any],
) -> list[str]:
    """Name condition leaves that differ in either direction (near-miss report)."""
    left_flat = _native_flat_conditions(left)
    right_flat = _native_flat_conditions(right)
    return [
        path for path in sorted(left_flat)
        if path not in right_flat
        or _canon(left_flat[path]) != _canon(right_flat[path])
    ]

def _native_scope_key(identity: Mapping[str, Any]) -> str:
    """Hash the non-condition call scope for no-ID near-miss diagnosis."""
    fields = (
        "boundary_kind", "native_operator", "scope", "expansion",
        "native_abi_sha256", "rank", "device_id", "stream_id",
        "clock_domain", "window_id", "fusion_members",
    )
    return _native_sha({field: identity.get(field) for field in fields})

def _native_item_condition_gaps(
    observed: Mapping[str, Any], prediction: Mapping[str, Any],
) -> list[str]:
    """Report missing actual facts while accepting explicit declaration scope.

    ``condition_scope`` is emitted by the native ``sim_bridge`` adapter.  A key marked
    ``declaration`` is a request/deployment declaration that the selected
    native spec does not preserve as an invocation condition; it is checked
    against the prediction's explicitly referenced request condition, never
    invented from an observation.  Keys marked ``actual`` (or without a scope)
    must be present in the actual receipt.
    """
    left = _native_flat_conditions(observed)
    right = _native_flat_conditions(prediction["conditions"])
    request_conditions = prediction.get("request_conditions")
    request_conditions = (request_conditions
                          if isinstance(request_conditions, Mapping) else {})
    scope = prediction.get("condition_scope")
    scope = scope if isinstance(scope, Mapping) else {}
    gaps = []
    for path in sorted(left):
        top = path.split(".", 1)[0]
        if path in right:
            if _canon(left[path]) != _canon(right[path]):
                gaps.append(path)
            continue
        if scope.get(top) == "declaration" and top in request_conditions:
            if _canon(observed.get(top)) == _canon(request_conditions.get(top)):
                continue
        gaps.append(path)
    return gaps

def _native_occurrence(record: Mapping[str, Any]) -> tuple[dict[str, Any], set[str]]:
    raw = record.get("occurrence")
    if not isinstance(raw, Mapping):
        return {}, set()
    return dict(raw), set(raw)

def _native_clock(record: Mapping[str, Any]) -> tuple[dict[str, Any], set[str]]:
    raw = record.get("clock")
    if not isinstance(raw, Mapping):
        return {}, set()
    return dict(raw), set(raw)

def _native_window_id(record: Mapping[str, Any]) -> str | None:
    top = record.get("window_id")
    if isinstance(top, str) and top:
        return top
    timing = record.get("timing")
    if isinstance(timing, Mapping):
        window_id = timing.get("window_id")
        if isinstance(window_id, str) and window_id:
            return window_id
        window = timing.get("window")
        if isinstance(window, Mapping) and isinstance(window.get("id"), str):
            return window["id"]
    occurrence = record.get("occurrence")
    if isinstance(occurrence, Mapping):
        window_id = occurrence.get("window_id")
        if isinstance(window_id, str) and window_id:
            return window_id
    return None

def _native_identity(boundary: Mapping[str, Any], abi: Mapping[str, Any],
                     conditions: Mapping[str, Any],
                     occurrence: Mapping[str, Any] | None = None,
                     clock: Mapping[str, Any] | None = None,
                     window_id: str | None = None,
                     *,
                     condition_gaps: Sequence[Mapping[str, Any]] | None = None,
                     condition_conflicts: Sequence[Mapping[str, Any]] | None = None,
                     ) -> dict[str, Any]:
    occurrence = occurrence if isinstance(occurrence, Mapping) else {}
    clock = clock if isinstance(clock, Mapping) else {}
    declared = dict(conditions or {})
    return {
        "boundary_kind": boundary.get("kind"),
        "native_operator": boundary.get("native_operator"),
        "scope": boundary.get("scope"),
        "expansion": boundary.get("expansion"),
        "native_abi_sha256": abi.get("digest"),
        "hardware": declared.get("hardware"),
        "rank": occurrence.get("rank"),
        "device_id": occurrence.get("device_id"),
        "stream_id": occurrence.get("stream_id"),
        "clock_domain": clock.get("domain"),
        "window_id": window_id,
        "phase": declared.get("phase"),
        "model": declared.get("model"),
        "quant": declared.get("quant"),
        "deployment_image_id": declared.get("deployment_image_id"),
        "implementation": declared.get("implementation"),
        "execution": declared.get("execution"),
        "attrs": declared.get("attrs"),
        "api": declared.get("api"),
        "version": declared.get("version"),
        "conditions": declared,
        "condition_gaps": _native_condition_gap_rows(condition_gaps),
        "condition_conflicts": _native_condition_conflict_rows(condition_conflicts),
        "fusion_members": list(boundary.get("fusion", {}).get("members", ())),
    }

def _native_group_key(identity: Mapping[str, Any]) -> str | None:
    if (not identity.get("boundary_kind") or not identity.get("native_operator")
            or not identity.get("native_abi_sha256")):
        return None
    return _native_sha(identity)

def _native_request_bases(records: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Deduplicate request facts while keeping every observation sample.

    Event/task/start/end are sample facts, not request facts.  Two samples with
    the same request_id and the same canonical request identity share one base;
    only genuinely different facts remain multiple entries and become ambiguity.
    """
    index: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        request_id = record.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            continue
        boundary, _ = _native_boundary(record)
        abi = _native_abi(record)
        conditions, sources, gaps, conflicts = _native_condition_meta(record)
        occurrence, _ = _native_occurrence(record)
        clock, _ = _native_clock(record)
        window_id = _native_window_id(record)
        identity = record.get("identity")
        if not isinstance(identity, Mapping):
            identity = _native_identity(
                boundary, abi, conditions, occurrence, clock, window_id,
                condition_gaps=gaps, condition_conflicts=conflicts)
        key = _canon(identity)
        index.setdefault(request_id, {}).setdefault(key, {
            "request_id": request_id,
            "boundary": boundary, "abi": abi, "conditions": conditions,
            "condition_sources": sources,
            "condition_gaps": gaps, "condition_conflicts": conflicts,
            "occurrence": occurrence, "clock": clock,
            "timing": {"window_id": window_id},
            "request_identity": record.get("request_identity"),
        })
    return {request_id: list(values.values())
            for request_id, values in index.items()}

def _native_group_differences(observations: Sequence[Mapping[str, Any]]) -> list[str]:
    """Name disagreements over all declared conditions, not a fixed whitelist."""
    fields = (
        "boundary_kind", "native_operator", "scope", "expansion",
        "native_abi_sha256", "rank", "device_id", "stream_id",
        "clock_domain", "window_id", "fusion_members",
    )
    differences: list[str] = []
    for field in fields:
        values = {_canon(item["identity"].get(field)) for item in observations}
        if len(values) > 1:
            differences.append(field)
    first = _native_flat_conditions(observations[0]["identity"].get("conditions"))
    for item in observations[1:]:
        other = _native_flat_conditions(item["identity"].get("conditions"))
        for path in sorted(set(first) | set(other)):
            if (path not in first or path not in other
                    or _canon(first[path]) != _canon(other[path])):
                if path not in differences:
                    differences.append(path)
    for field in ("condition_gaps", "condition_conflicts"):
        values = {_canon(item["identity"].get(field)) for item in observations}
        if len(values) > 1:
            differences.append(field)
    return differences

def _native_coverage(
    observation_report: Mapping[str, Any],
    observation_items: Sequence[Mapping[str, Any]],
    *,
    truncated: bool,
) -> dict[str, Any]:
    """Reconcile all declared windows and original counts with actual members.

    Top-level and nested window lists are unioned, not treated as alternatives.
    A filtered top-level list cannot shrink the denominator while the original
    ``counts.events`` or nested parent range still declares more.  An explicit
    tail ``scope`` selects its own denominator but retains the parent remainder.
    """
    window_declarations: list[Mapping[str, Any]] = []
    top_windows = observation_report.get("windows")
    if isinstance(top_windows, list):
        window_declarations.extend(item for item in top_windows
                                   if isinstance(item, Mapping))
    parent_window = observation_report.get("window")
    if isinstance(parent_window, Mapping):
        nested_windows = parent_window.get("windows")
        if isinstance(nested_windows, list):
            window_declarations.extend(item for item in nested_windows
                                       if isinstance(item, Mapping))
        if isinstance(parent_window.get("id"), str):
            window_declarations.append(parent_window)
    declared: dict[str, int] = {}
    declaration_conflicts: list[dict[str, Any]] = []
    for window in window_declarations:
        window_id = window.get("id")
        if not isinstance(window_id, str) or not window_id:
            continue
        try:
            count = int(window.get("event_count") or 0)
        except (TypeError, ValueError):
            count = 0
        if window_id in declared and declared[window_id] != count:
            declaration_conflicts.append({
                "window_id": window_id, "declared": declared[window_id],
                "conflicting": count,
            })
            declared[window_id] = max(declared[window_id], count)
        else:
            declared[window_id] = count
    counts = observation_report.get("counts")
    counts = counts if isinstance(counts, Mapping) else {}
    counts_events = None
    if counts.get("events") is not None:
        try:
            counts_events = int(counts["events"])
        except (TypeError, ValueError):
            counts_events = None
    window_sum = sum(declared.values())
    if counts_events is not None and declared and window_sum != counts_events:
        declaration_conflicts.append({
            "reason": "counts_events_vs_window_sum",
            "counts_events": counts_events, "window_sum": window_sum,
        })
    scope = observation_report.get("scope")
    scope = scope if isinstance(scope, Mapping) else None
    missing_declared_windows: list[str] = []
    scope_event_count = None
    parent_events = counts_events if counts_events is not None else window_sum
    if scope is not None:
        scope_windows = {str(item) for item in (scope.get("window_ids") or ())}
        if scope_windows:
            missing_declared_windows = sorted(scope_windows - set(declared))
            declared = {key: value for key, value in declared.items()
                        if key in scope_windows}
        if scope.get("event_count") is not None:
            try:
                scope_event_count = int(scope["event_count"])
            except (TypeError, ValueError):
                scope_event_count = None
    actual_counts = Counter(
        str(item["window_id"]) for item in observation_items)
    missing_window_ids = sorted(
        window_id for window_id, expected in declared.items()
        if actual_counts.get(window_id, 0) < expected)
    unexpected_window_ids = sorted(
        window_id for window_id in actual_counts
        if declared and window_id not in declared)
    if scope_event_count is not None:
        declared_events = scope_event_count
    elif declared:
        declared_events = sum(declared.values())
    elif counts_events is not None:
        declared_events = counts_events
    else:
        declared_events = None
    actual_events = len(observation_items)
    missing_events = (max(0, declared_events - actual_events)
                      if declared_events is not None else 0)
    unexpected_events = (max(0, actual_events - declared_events)
                         if declared_events is not None else 0)
    reconciled = (
        declared_events is not None
        and not declaration_conflicts
        and not missing_declared_windows
        and not missing_window_ids
        and not unexpected_window_ids
        and missing_events == 0
        and unexpected_events == 0
    )
    parent_remaining = (
        max(0, parent_events - declared_events)
        if scope is not None and parent_events is not None
        and declared_events is not None else 0
    )
    return {
        "reconciled": reconciled,
        "subset": scope is not None,
        "scope": dict(scope) if scope is not None else None,
        "parent_capture": (scope.get("parent_capture_id")
                           if scope is not None else None),
        "declared_window_counts": declared,
        "window_sum_declared": window_sum,
        "counts_events": counts_events,
        "declaration_conflicts": declaration_conflicts,
        "parent_events": parent_events,
        "parent_remaining_events": parent_remaining,
        "actual_window_counts": dict(actual_counts),
        "missing_declared_window_ids": missing_declared_windows,
        "missing_window_ids": missing_window_ids,
        "unexpected_window_ids": unexpected_window_ids,
        "declared_events": declared_events,
        "actual_events": actual_events,
        "missing_events": missing_events,
        "unexpected_events": unexpected_events,
        "truncated": truncated,
    }

def _native_observation_items(
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    raw = list(source.get("observations", ())) if isinstance(source, Mapping) else list(source)
    items = []
    for record in raw:
        if not isinstance(record, Mapping):
            raise ValueError("native observation must be a mapping")
        timing = record.get("timing")
        if not isinstance(timing, Mapping):
            raise ValueError("native observation needs timing.duration_ms")
        duration = _native_finite(
            timing.get("duration_ms"), name="observation duration_ms", positive=True)
        boundary, _ = _native_boundary(record)
        abi = _native_abi(record)
        conditions, condition_sources, condition_gaps, condition_conflicts = (
            _native_condition_meta(record))
        occurrence, _ = _native_occurrence(record)
        clock, _ = _native_clock(record)
        structure = record.get("structure")
        structure = dict(structure) if isinstance(structure, Mapping) else {}
        window_id = _native_window_id(record)
        identity = _native_identity(
            boundary, abi, conditions, occurrence, clock, window_id,
            condition_gaps=condition_gaps,
            condition_conflicts=condition_conflicts)
        items.append({
            "sample_id": record.get("observation_id") or _native_sha({
                "source": record.get("source"), "occurrence": occurrence,
                "abi": abi.get("digest"), "duration_ms": duration,
            }),
            "request_id": _native_request_id(record),
            "request_identity": record.get("request_identity"),
            "boundary": boundary, "abi": abi, "conditions": conditions,
            "condition_sources": condition_sources,
            "condition_gaps": condition_gaps,
            "condition_conflicts": condition_conflicts,
            "occurrence": occurrence, "clock": clock, "structure": structure,
            "duration_ms": duration, "window_id": window_id,
            "complete_in_window": bool(timing.get("complete_in_window", True)),
            "identity": identity,
            "evidence": record.get("evidence") or {},
            "source": record.get("source") or {},
        })
    deduped, seen = [], {}
    for item in items:
        signature = _canon({
            "request_id": item["request_id"], "identity": item["identity"],
            "duration_ms": item["duration_ms"],
        })
        if item["sample_id"] in seen:
            if seen[item["sample_id"]] != signature:
                raise ValueError(
                    f"conflicting native observation: {item['sample_id']}")
            continue
        seen[item["sample_id"]] = signature
        deduped.append(item)
    return deduped
