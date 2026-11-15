"""Simulation-vs-capture acceptance checks and native operator comparison (compare_acceptance_items).

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

from typing import Any, Mapping, Sequence

from .compare_acceptance_abi import (
    _native_abi, _native_boundary, _native_clock, _native_condition_conflict_rows,
    _native_condition_difference_paths, _native_condition_gap_rows,
    _native_condition_strings, _native_conditions, _native_flat_conditions,
    _native_group_differences, _native_group_key, _native_identity, _native_occurrence,
    _native_window_id,
)
from .compare_acceptance_helpers import (
    _NATIVE_REQUIRED_CONDITIONS, _canon, _native_finite, _native_timing_key,
)

def _native_prediction_items(
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    requests: Mapping[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    raw = list(source.get("predictions", ())) if isinstance(source, Mapping) else list(source)
    items = []
    for index, record in enumerate(raw):
        if not isinstance(record, Mapping):
            raise ValueError("native prediction must be a mapping")
        for forbidden in ("observed_ms", "measured_ms", "target_ms", "actual_ms",
                          "duration_ns", "start_ns", "end_ns"):
            if forbidden in record:
                raise ValueError(
                    f"native prediction must not consume observed timing: {forbidden}")
        leak = _native_timing_key(record.get("conditions") or {}, "conditions")
        if leak:
            raise ValueError(f"native prediction must not consume observed timing: {leak}")
        request_id = record.get("request_id")
        bases = requests.get(request_id, []) if isinstance(request_id, str) else []
        conflicts: list[str] = []
        if len(bases) > 1:
            conflicts.append("ambiguous_request_identity")
        base = bases[0] if len(bases) == 1 else {}
        pred_boundary, pred_boundary_fields = _native_boundary(record)
        # A prediction may declare ``conditions`` (actual invocation receipt) or
        # ``actual_conditions``.  A separate ``condition_consumption`` receipt is
        # accepted only when it names the value actually consumed.  The request
        # declaration is retained for consistency checks but never used to fill a
        # missing actual condition.
        pred_conditions: dict[str, Any] = {}
        raw_actual = record.get("actual_conditions")
        raw_conditions = record.get("conditions")
        if isinstance(raw_actual, Mapping):
            pred_conditions.update(raw_actual)
            if isinstance(raw_conditions, Mapping):
                for key, value in raw_conditions.items():
                    if key in pred_conditions:
                        if _canon(pred_conditions[key]) != _canon(value):
                            conflicts.append(f"conditions.{key}")
                    else:
                        pred_conditions[key] = value
        elif isinstance(raw_conditions, Mapping):
            pred_conditions.update(raw_conditions)
        condition_sources: dict[str, list[str]] = {}
        raw_sources = record.get("condition_sources")
        if isinstance(raw_sources, Mapping):
            for key, value in raw_sources.items():
                condition_sources[str(key)] = _native_condition_strings(value)
        condition_gaps = _native_condition_gap_rows(record.get("condition_gaps"))
        condition_conflicts = _native_condition_conflict_rows(
            record.get("condition_conflicts"))
        consumption = record.get("condition_consumption")
        if isinstance(consumption, Mapping):
            for key, payload in consumption.items():
                key = str(key)
                if isinstance(payload, Mapping) and "value" in payload:
                    value = payload.get("value")
                    labels = _native_condition_strings(
                        payload.get("evidence") or payload.get("source"))
                else:
                    value, labels = payload, []
                if key in pred_conditions and _canon(pred_conditions[key]) != _canon(value):
                    condition_conflicts.append({
                        "field": key,
                        "values": [pred_conditions[key], value],
                        "sources": ["prediction.conditions",
                                    "prediction.condition_consumption"],
                    })
                else:
                    pred_conditions[key] = value
                condition_sources.setdefault(key, []).extend(
                    labels or ["prediction.condition_consumption"])
        request_conditions: dict[str, Any] = {}
        raw_request_conditions = record.get("request_conditions")
        if isinstance(raw_request_conditions, Mapping):
            request_conditions = dict(raw_request_conditions)
        request_condition_sources: dict[str, list[str]] = {}
        raw_request_sources = record.get("request_condition_sources")
        if isinstance(raw_request_sources, Mapping):
            for key, value in raw_request_sources.items():
                request_condition_sources[str(key)] = _native_condition_strings(value)
        pred_occurrence, pred_occurrence_fields = _native_occurrence(record)
        pred_clock, pred_clock_fields = _native_clock(record)
        pred_window_id = _native_window_id(record)
        if base:
            base_boundary, _ = _native_boundary(base)
            base_conditions, _ = _native_conditions(base)
            base_occurrence, _ = _native_occurrence(base)
            base_clock, _ = _native_clock(base)
            base_window_id = _native_window_id(base)
            for field in ("kind", "native_operator", "scope", "expansion"):
                if field in pred_boundary_fields and base_boundary.get(field) is not None:
                    if pred_boundary.get(field) != base_boundary.get(field):
                        conflicts.append(f"boundary.{field}")
                else:
                    pred_boundary[field] = base_boundary.get(field)
            if "fusion_members" in pred_boundary_fields:
                if (base_boundary["fusion"]["members"]
                        and pred_boundary["fusion"]["members"]
                        != base_boundary["fusion"]["members"]):
                    conflicts.append("boundary.fusion_members")
            else:
                pred_boundary["fusion"] = base_boundary["fusion"]
            # Same-ID consistency is checked, never repaired by copying the
            # observation/request declaration into the actual receipt.
            base_flat = _native_flat_conditions(base_conditions)
            request_flat = _native_flat_conditions(request_conditions)
            for path in sorted(request_flat):
                if (path in base_flat
                        and _canon(request_flat[path]) != _canon(base_flat[path])):
                    conflicts.append(f"request_conditions.{path}")
            for key in base_conditions:
                if key not in pred_conditions:
                    condition_gaps.append({
                        "field": key,
                        "reason": "no_actual_consumption_evidence",
                    })
            for path in _native_condition_difference_paths(
                    base_conditions, pred_conditions):
                if path.split(".", 1)[0] in pred_conditions:
                    conflict = f"conditions.{path}"
                    if conflict not in conflicts:
                        conflicts.append(conflict)
            for key in request_conditions:
                if key not in pred_conditions:
                    condition_gaps.append({
                        "field": key,
                        "reason": "request_condition_not_consumed",
                    })
            for field, value in base_occurrence.items():
                if field in pred_occurrence_fields:
                    if (value is not None and pred_occurrence.get(field) is not None
                            and pred_occurrence.get(field) != value):
                        conflicts.append(f"occurrence.{field}")
                else:
                    pred_occurrence[field] = value
            for field, value in base_clock.items():
                if field in pred_clock_fields:
                    if value is not None and pred_clock.get(field) != value:
                        conflicts.append(f"clock.{field}")
                else:
                    pred_clock[field] = value
            if pred_window_id is None:
                pred_window_id = base_window_id
            elif base_window_id is not None and pred_window_id != base_window_id:
                conflicts.append("timing.window_id")
        condition_gaps = _native_condition_gap_rows(condition_gaps)
        condition_conflicts = _native_condition_conflict_rows(condition_conflicts)
        conflicts.extend(
            f"conditions.{row['field']}" for row in condition_conflicts
            if f"conditions.{row['field']}" not in conflicts)
        abi_declared = ("abi" in record or "native_abi_sha256" in record)
        abi = _native_abi(record if abi_declared else {})
        base_abi = _native_abi(base) if base else {}
        if base and abi_declared:
            if abi.get("status") == "conflict":
                conflicts.append("abi.digest")
            elif base_abi.get("status") == "conflict":
                conflicts.append("abi.request_identity_conflict")
            elif abi.get("status") == "complete" and base_abi.get("status") == "complete":
                if abi.get("digest") != base_abi.get("digest"):
                    conflicts.append("abi.digest")
            elif base_abi.get("status") == "complete":
                conflicts.append("abi.incomplete")
        if (not abi_declared and base_abi.get("status") == "complete"
                and base_abi.get("verified")):
            abi = {
                **base_abi, "verified": False,
                "digest_source": "request_identity_only",
                "issues": [{"slot": "abi", "reason": "prediction_abi_not_declared"}],
            }
        status = str(record.get("status") or "modeled")
        reason = record.get("reason") or record.get("unmodeled_reason")
        raw_duration = record.get("duration_ms", record.get("predicted_ms"))
        if status in {"modeled", "predicted", "ok"}:
            duration = _native_finite(
                raw_duration, name="prediction duration_ms", positive=True)
        elif status == "modeled_work_only":
            duration = (None if raw_duration is None else _native_finite(
                raw_duration, name="prediction duration_ms", positive=False))
        else:
            try:
                duration = (None if raw_duration is None else _native_finite(
                    raw_duration, name="prediction duration_ms", positive=False))
            except ValueError:
                duration = None
        evidence = record.get("evidence")
        if isinstance(evidence, str):
            evidence = [evidence]
        identity = _native_identity(
            pred_boundary, abi, pred_conditions, pred_occurrence, pred_clock,
            pred_window_id, condition_gaps=condition_gaps,
            condition_conflicts=condition_conflicts)
        items.append({
            "prediction_id": record.get("prediction_id") or f"prediction:{index}",
            "request_id": request_id if isinstance(request_id, str) else None,
            "boundary": pred_boundary, "abi": abi,
            "conditions": pred_conditions,
            "condition_sources": condition_sources,
            "condition_gaps": condition_gaps,
            "condition_conflicts": condition_conflicts,
            "condition_scope": dict(record.get("condition_scope") or {}),
            "request_conditions": request_conditions,
            "request_condition_sources": request_condition_sources,
            "occurrence": pred_occurrence,
            "clock": pred_clock, "window_id": pred_window_id,
            "identity": identity,
            "duration_ms": duration, "duration_available": duration is not None,
            "work": record.get("work"), "status": status, "reason": reason,
            "evidence": list(evidence or ()),
            "fusion_members": list(pred_boundary.get("fusion", {}).get("members", ())),
            "match_key": _native_group_key(identity),
            "abi_declared": abi_declared,
            "abi_verified": bool(abi.get("verified")),
            "conflicts": conflicts,
        })
    return items

def _native_group_reason(group: Mapping[str, Any]) -> str | None:
    observations = group["observations"]
    first = observations[0]
    if not first["abi"].get("digest"):
        return "native_abi_incomplete"
    if not all(item["abi"].get("verified") for item in observations):
        return "observation_abi_not_verified"
    statuses = {item["structure"].get("status", "unidentified")
                for item in observations}
    if "unidentified" in statuses:
        return "unidentified_observation_structure"
    if "candidate" in statuses:
        return "candidate_observation_structure"
    differences = _native_group_differences(observations)
    if differences:
        return "conflicting_request_identity:" + ",".join(differences)
    conflict_fields = sorted({
        str(row["field"])
        for item in observations
        for row in (item.get("condition_conflicts") or ())
    })
    if conflict_fields:
        return "request_condition_conflict:" + ",".join(conflict_fields)
    if not all(item["complete_in_window"] for item in observations):
        return "observation_window_incomplete"
    missing = [
        field for field in _NATIVE_REQUIRED_CONDITIONS
        if not all(isinstance(item["conditions"].get(field), str)
                   and item["conditions"].get(field).strip()
                   for item in observations)
    ]
    if missing:
        return "condition_missing:" + ",".join(missing)
    return None

def _native_pair_reason(
    prediction: Mapping[str, Any], group: Mapping[str, Any],
) -> str | None:
    if prediction["status"] not in {"modeled", "predicted", "ok", "modeled_work_only"}:
        return f"prediction_{prediction['status']}" + (
            f":{prediction['reason']}" if prediction.get("reason") else "")
    if prediction.get("conflicts"):
        return "request_identity_conflict:" + ",".join(prediction["conflicts"])
    if not prediction.get("abi_declared"):
        return "prediction_abi_not_declared"
    if not prediction.get("abi_verified"):
        if prediction["abi"].get("status") == "conflict":
            return "prediction_abi_digest_mismatch"
        return "prediction_abi_not_verified"
    observed_abi = group["abi"]
    if not observed_abi.get("digest"):
        return "observation_abi_incomplete"
    if prediction["abi"].get("digest") != observed_abi.get("digest"):
        return "native_abi_mismatch"
    observed_boundary = group["boundary"]
    for field in ("kind", "native_operator", "scope", "expansion"):
        observed = observed_boundary.get(field)
        predicted = prediction["boundary"].get(field)
        if observed is not None and predicted is None:
            return f"boundary_missing:{field}"
        if observed is not None and predicted is not None and observed != predicted:
            return f"boundary_mismatch:{field}"
    observed_conditions = group["observations"][0]["conditions"]
    observed_flat = _native_flat_conditions(observed_conditions)
    predicted_flat = _native_flat_conditions(prediction["conditions"])
    observed_conflicts = sorted({
        str(row["field"])
        for item in group["observations"]
        for row in (item.get("condition_conflicts") or ())
    })
    if observed_conflicts:
        return "request_condition_conflict:" + ",".join(observed_conflicts)
    prediction_gaps = {
        str(row["field"]): str(row.get("reason") or "not_declared")
        for row in (prediction.get("condition_gaps") or ())
        if str(row["field"]) not in predicted_flat
        and not any(path.startswith(str(row["field"]) + ".")
                    for path in predicted_flat)
    }
    condition_scope = prediction.get("condition_scope")
    condition_scope = (condition_scope
                       if isinstance(condition_scope, Mapping) else {})
    request_conditions = prediction.get("request_conditions")
    request_conditions = (request_conditions
                          if isinstance(request_conditions, Mapping) else {})
    for path in sorted(observed_flat):
        top = path.split(".", 1)[0]
        if path in predicted_flat:
            if _canon(observed_flat[path]) != _canon(predicted_flat[path]):
                return f"condition_mismatch:{path}"
            continue
        if (condition_scope.get(top) == "declaration"
                and top in request_conditions):
            if _canon(observed_conditions.get(top)) != _canon(
                    request_conditions.get(top)):
                return f"request_conditions_mismatch:{top}"
            continue
        reason = next(
            (text for field, text in prediction_gaps.items()
             if path == field or path.startswith(field + ".")),
            "no_actual_consumption_evidence")
        return f"condition_missing:{path}:{reason}"
    request_flat = _native_flat_conditions(request_conditions)
    for path, value in sorted(request_flat.items()):
        if path in observed_flat and _canon(observed_flat[path]) != _canon(value):
            return f"request_conditions_mismatch:{path}"
    for field in ("rank", "device_id", "stream_id"):
        observed = group["observations"][0]["occurrence"].get(field)
        predicted = prediction["occurrence"].get(field)
        if observed is not None and predicted is None:
            return f"occurrence_missing:{field}"
        if observed is not None and predicted is not None and observed != predicted:
            return f"occurrence_mismatch:{field}"
    for field in ("clock_domain", "window_id"):
        observed = group["observations"][0]["identity"].get(field)
        predicted = prediction["identity"].get(field)
        if observed is not None and predicted is None:
            return f"scope_missing:{field}"
        if observed is not None and predicted is not None and observed != predicted:
            return f"scope_mismatch:{field}"
    observed_members = observed_boundary["fusion"]["members"]
    predicted_members = prediction["fusion_members"]
    if observed_members != predicted_members:
        if len(observed_members) > 1:
            return "fusion_boundary_mismatch"
        if len(predicted_members) > 1:
            return "prediction_fuses_atomic_observation"
    return None

def _native_root_cause(reason: str) -> str:
    if reason.startswith(("boundary_", "condition_", "occurrence_", "scope_",
                          "request_condition_", "request_conditions_",
                          "cross_clock")):
        return "input_boundary_or_unit"
    if reason.startswith("fusion_") or "fusion" in reason or "fuses" in reason:
        return "dependency_pipeline_or_fusion"
    if reason.startswith(("native_abi", "ambiguous_native_abi")):
        return "semantic_representation_or_geometry"
    if reason.startswith(("unidentified", "candidate", "ambiguous", "no_",
                          "unknown_", "truncated", "partial")):
        return "evidence_missing"
    if reason.startswith("prediction_"):
        return "prediction_gap"
    return "unclassified_residual"

def _native_discriminating_evidence(reason: str) -> list[str]:
    if reason == "relative_error_exceeds_tolerance":
        return [
            "same-ABI independent timing window",
            "separate AIC/AIV pipe intervals and stream overlap",
            "prediction stage breakdown against observed pipe counters",
        ]
    if reason.startswith(("boundary_", "condition_", "occurrence_", "scope_")):
        return ["declared prediction boundary", "same-call observation receipt"]
    if "fusion" in reason:
        return ["declared semantic members on both sides", "isolated member observations"]
    if reason.startswith("prediction_"):
        return ["independent provider status and unmodeled reason"]
    return ["additional captured ABI/occurrence evidence"]

def _unpaired_observation(group: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "request_id": group["request_id"],
        "observation_ids": [row["sample_id"] for row in group["observations"]],
        "boundary": group["boundary"],
        "abi": group["abi"],
        "conditions": group["conditions"],
        "condition_sources": group["observations"][0].get("condition_sources"),
        "condition_gaps": group["observations"][0].get("condition_gaps"),
        "condition_conflicts": group["observations"][0].get("condition_conflicts"),
        "occurrence": group["observations"][0]["occurrence"],
        "clock": group["observations"][0]["clock"],
        "identity": group["observations"][0]["identity"],
        "observed_ms": group["duration_ms"],
        "observation_samples": len(group["observations"]),
        "structure_status": group["observations"][0]["structure"].get("status"),
        "structure_statuses": sorted({
            str(row["structure"].get("status")) for row in group["observations"]}),
        "window_ids": sorted({
            str(row["window_id"]) for row in group["observations"]}),
        "reason": reason,
    }

def _unpaired_prediction(prediction: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "prediction_id": prediction["prediction_id"],
        "request_id": prediction["request_id"],
        "boundary": prediction["boundary"],
        "abi": prediction["abi"],
        "conditions": prediction["conditions"],
        "condition_sources": prediction.get("condition_sources"),
        "condition_gaps": prediction.get("condition_gaps"),
        "condition_conflicts": prediction.get("condition_conflicts"),
        "condition_scope": prediction.get("condition_scope"),
        "request_conditions": prediction.get("request_conditions"),
        "occurrence": prediction["occurrence"],
        "clock": prediction["clock"],
        "window_id": prediction["window_id"],
        "identity": prediction["identity"],
        "predicted_ms": prediction["duration_ms"],
        "status": prediction["status"],
        "abi_declared": prediction.get("abi_declared"),
        "abi_verified": prediction.get("abi_verified"),
        "conflicts": list(prediction.get("conflicts") or ()),
        "reason": reason,
    }

def _native_failure_matrix(
    items: Sequence[Mapping[str, Any]],
    unpaired_observations: Sequence[Mapping[str, Any]],
    unpaired_predictions: Sequence[Mapping[str, Any]],
    ambiguous: Sequence[Mapping[str, Any]],
    coverage: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    def add(reason: str, item_id: str, *, root: str | None = None,
            evidence: Mapping[str, Any] | None = None) -> None:
        root = root or _native_root_cause(reason)
        key = (root, reason)
        row = rows.setdefault(key, {
            "root_cause": root, "reason": reason, "count": 0,
            "item_ids": [], "evidence": evidence or {},
            "discriminating_evidence": _native_discriminating_evidence(reason),
            "claim": "candidate_dimension_not_proven_root_cause",
        })
        row["count"] += 1
        if len(row["item_ids"]) < 64:
            row["item_ids"].append(item_id)
    for item in items:
        if item["status"] == "work_only":
            add("prediction_work_only_no_duration", item["item_id"],
                root="prediction_gap",
                evidence={"observed_ms": item["observed_ms"],
                          "work": item["comparison"].get("work"),
                          "prediction_abi_digest": item["prediction_abi_digest"]})
            continue
        if item["status"] != "outside_tolerance":
            continue
        add("relative_error_exceeds_tolerance", item["item_id"],
            root="unclassified_residual",
            evidence={
                "observed_ms": item["observed_ms"],
                "predicted_ms": item["predicted_ms"],
                "relative_error": item["comparison"]["relative_error"],
                "sample_verdicts": item["comparison"]["sample_verdicts"],
                "observation_evidence": item["observation_evidence"],
                "prediction_evidence": item["prediction_evidence"],
            })
    for row in unpaired_observations:
        add(str(row["reason"]), row["observation_ids"][0]
            if row["observation_ids"] else row["request_id"])
    for row in unpaired_predictions:
        add(str(row["reason"]), row["prediction_id"],
            evidence={"conflicts": row.get("conflicts") or []})
    for row in ambiguous:
        add(str(row["reason"]), row["request_id"],
            evidence={"predictions": row["predictions"]})
    if coverage.get("partial_coverage"):
        add("partial_observation_window_coverage", "coverage",
            root="evidence_missing",
            evidence={
                "truncated": coverage.get("truncated"),
                "window": coverage.get("window"),
                "counts": coverage.get("observation_counts"),
            })
    return sorted(rows.values(), key=lambda row: (row["root_cause"], row["reason"]))
