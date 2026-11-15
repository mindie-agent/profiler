"""Simulation-vs-capture acceptance checks and native operator comparison (compare_acceptance_pairs).

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

from statistics import median
from typing import Any, Mapping, Sequence

from .compare_acceptance_abi import (
    _native_condition_difference_paths, _native_coverage, _native_group_key,
    _native_item_condition_gaps, _native_observation_items, _native_request_bases,
    _native_scope_key,
)
from .compare_acceptance_helpers import (
    FORMAL_NATIVE_TOLERANCE, NATIVE_COMPARISON_SCHEMA, _native_finite, _native_sha,
)
from .compare_acceptance_items import (
    _native_failure_matrix, _native_group_reason, _native_pair_reason,
    _native_prediction_items, _unpaired_observation, _unpaired_prediction,
)

def compare_native_predictions(
    observations: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    predictions: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    requests: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    diagnostic_tolerance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare independent native predictions on one exact tensor/ABI boundary.

    Formal A5 acceptance is fixed at every sample's
    ``abs(predicted - observed) / observed <= 0.10``.  A diagnostic tolerance
    is reported separately and never changes ``status``.  A prediction must
    declare its own complete ABI and boundary; a request ID only correlates the
    response and cannot supply or override identity facts.
    """
    formal_relative = FORMAL_NATIVE_TOLERANCE["relative"]
    formal_absolute = FORMAL_NATIVE_TOLERANCE["absolute_ms"]
    diagnostic = None
    if diagnostic_tolerance is not None:
        relative = _native_finite(
            diagnostic_tolerance.get("relative", formal_relative),
            name="diagnostic_tolerance.relative")
        absolute = _native_finite(
            diagnostic_tolerance.get("absolute_ms", 0.0),
            name="diagnostic_tolerance.absolute_ms")
        if relative < 0 or absolute < 0:
            raise ValueError("diagnostic native tolerance must be nonnegative")
        diagnostic = {"relative": relative, "absolute_ms": absolute,
                      "denominator": "observed_ms",
                      "application": "diagnostic_only_not_formal_acceptance"}
    observation_report = observations if isinstance(observations, Mapping) else {}
    observation_items = _native_observation_items(observations)
    request_raw = (
        list(requests.get("requests", ())) if isinstance(requests, Mapping)
        else list(requests) if requests is not None else []
    )
    request_index = _native_request_bases(request_raw)
    if not request_index:
        request_index = _native_request_bases(observation_items)
    prediction_items = _native_prediction_items(predictions, request_index)

    groups: dict[str, dict[str, Any]] = {}
    for item in observation_items:
        request_id = item["request_id"]
        if request_id is None:
            request_id = "request:" + _native_sha(item["identity"])[7:31]
            item["request_id"] = request_id
        groups.setdefault(request_id, {
            "request_id": request_id, "observations": [],
        })["observations"].append(item)
    for group in groups.values():
        first = group["observations"][0]
        group["boundary"] = first["boundary"]
        group["abi"] = first["abi"]
        group["conditions"] = first["conditions"]
        group["fusion"] = first["boundary"]["fusion"]
        group["duration_ms"] = median(item["duration_ms"] for item in group["observations"])
        group["durations_ms"] = [item["duration_ms"] for item in group["observations"]]
        group["reason"] = _native_group_reason(group)
        group["match_key"] = _native_group_key(first["identity"])
    groups_by_key: dict[str, list[dict[str, Any]]] = {}
    groups_by_scope: dict[str, list[dict[str, Any]]] = {}
    for group in groups.values():
        if group["match_key"]:
            groups_by_key.setdefault(group["match_key"], []).append(group)
        groups_by_scope.setdefault(
            _native_scope_key(group["observations"][0]["identity"]), []
        ).append(group)

    near_misses: dict[str, list[dict[str, Any]]] = {}
    for prediction in prediction_items:
        if prediction["request_id"] or not prediction["match_key"]:
            continue
        candidates = groups_by_key.get(prediction["match_key"], [])
        if len(candidates) == 1:
            prediction["request_id"] = candidates[0]["request_id"]
        elif len(candidates) > 1:
            prediction["conflicts"].append("ambiguous_observation_candidates")
            prediction["candidate_request_ids"] = [
                group["request_id"] for group in candidates]
        else:
            scope_candidates = groups_by_scope.get(
                _native_scope_key(prediction["identity"]), [])
            rows = []
            for group in scope_candidates:
                differences = _native_condition_difference_paths(
                    group["observations"][0]["conditions"],
                    prediction["conditions"])
                if not differences:
                    differences = ["conditions"]
                rows.append({
                    "request_id": group["request_id"],
                    "identity_differences": differences,
                })
            if rows:
                prediction["near_miss_candidates"] = rows
                near_misses[prediction["prediction_id"]] = rows

    by_request: dict[str, list[dict[str, Any]]] = {}
    for prediction in prediction_items:
        if prediction["request_id"]:
            by_request.setdefault(prediction["request_id"], []).append(prediction)
    ambiguous_predictions: dict[str, list[dict[str, Any]]] = {}
    for request_id, values in by_request.items():
        if len(values) > 1:
            ambiguous_predictions[request_id] = values

    items, unpaired_observations, unpaired_predictions, ambiguous = [], [], [], []
    used_predictions: set[str] = set()
    for request_id, group in groups.items():
        values = by_request.get(request_id, ())
        if request_id in ambiguous_predictions:
            ambiguous.append({
                "request_id": request_id, "reason": "ambiguous_predictions",
                "observations": [item["sample_id"] for item in group["observations"]],
                "predictions": [item["prediction_id"] for item in values],
                "candidates": values,
            })
            used_predictions.update(item["prediction_id"] for item in values)
            unpaired_observations.append(_unpaired_observation(group, "ambiguous_predictions"))
            continue
        prediction = values[0] if values else None
        if prediction is not None:
            used_predictions.add(prediction["prediction_id"])
        if group["reason"]:
            unpaired_observations.append(_unpaired_observation(group, group["reason"]))
            if prediction is not None:
                unpaired_predictions.append(_unpaired_prediction(
                    prediction, "observation_not_comparable:" + group["reason"]))
            continue
        if prediction is None:
            related = [
                (prediction_id, row)
                for prediction_id, rows in near_misses.items()
                for row in rows
                if row["request_id"] == request_id
            ]
            if related:
                fields = sorted({
                    field for _, row in related
                    for field in row["identity_differences"]
                })
                unpaired = _unpaired_observation(
                    group, "request_identity_conflict:" + ",".join(fields))
                unpaired["prediction_ids"] = sorted({
                    prediction_id for prediction_id, _ in related})
                unpaired["identity_differences"] = {
                    prediction_id: row["identity_differences"]
                    for prediction_id, row in related
                }
                unpaired_observations.append(unpaired)
            else:
                unpaired_observations.append(_unpaired_observation(
                    group, "no_exact_prediction_identity"))
            continue
        reason = _native_pair_reason(prediction, group)
        if reason is not None:
            unpaired_observations.append(_unpaired_observation(group, reason))
            unpaired_predictions.append(_unpaired_prediction(prediction, reason))
            continue
        if prediction.get("duration_ms") is None:
            observed = group["duration_ms"]
            item = {
                "item_id": "comparison:" + _native_sha({
                    "request_id": request_id,
                    "prediction_id": prediction["prediction_id"],
                    "observation_ids": [row["sample_id"] for row in group["observations"]],
                })[7:31],
                "request_id": request_id,
                "prediction_id": prediction["prediction_id"],
                "boundary": group["boundary"],
                "identity": group["observations"][0]["identity"],
                "observed_ms": observed,
                "predicted_ms": None,
                "observation_ids": [row["sample_id"] for row in group["observations"]],
                "observation_samples": len(group["observations"]),
                "observation_range_ms": [min(group["durations_ms"]),
                                          max(group["durations_ms"])],
                "observation_clock_domains": sorted({
                    str(row["clock"].get("domain")) for row in group["observations"]}),
                "observation_window_ids": sorted({
                    str(row["window_id"]) for row in group["observations"]}),
                "condition_gaps": _native_item_condition_gaps(
                    group["conditions"], prediction),
                "observation_evidence": {
                    "pipe_times_us": [
                        row["evidence"].get("pipe_times_us", {})
                        for row in group["observations"]
                    ],
                    "block_num": [row["evidence"].get("block_num")
                                  for row in group["observations"]],
                },
                "prediction_evidence": prediction["evidence"],
                "prediction_abi_digest": prediction["abi"].get("digest"),
                "observation_abi_digest": group["abi"].get("digest"),
                "comparison": {
                    "duration_available": False,
                    "formal_policy": "not_evaluated_no_predicted_duration",
                    "reason": "prediction_work_only",
                    "work": prediction.get("work"),
                    "observation_duration_ms": observed,
                    "sample_verdicts": [],
                },
                "status": "work_only",
            }
            items.append(item)
            continue
        observed = group["duration_ms"]
        predicted = prediction["duration_ms"]
        residual = predicted - observed
        sample_verdicts = []
        for row in group["observations"]:
            sample_observed = row["duration_ms"]
            sample_residual = predicted - sample_observed
            formal_allowed = formal_absolute + formal_relative * sample_observed
            formal_within = abs(sample_residual) <= formal_allowed
            verdict = {
                "observation_id": row["sample_id"],
                "observed_ms": sample_observed,
                "signed_residual_ms": sample_residual,
                "absolute_residual_ms": abs(sample_residual),
                "relative_error": sample_residual / sample_observed,
                "formal_allowed_error_ms": formal_allowed,
                "within_tolerance": formal_within,
                "clock_domain": row["clock"].get("domain"),
                "window_id": row["window_id"],
            }
            if diagnostic is not None:
                diagnostic_allowed = (diagnostic["absolute_ms"]
                                      + diagnostic["relative"] * sample_observed)
                verdict["diagnostic_allowed_error_ms"] = diagnostic_allowed
                verdict["diagnostic_within"] = abs(sample_residual) <= diagnostic_allowed
            sample_verdicts.append(verdict)
        outside_samples = [
            row["observation_id"] for row in sample_verdicts
            if not row["within_tolerance"]
        ]
        within = not outside_samples
        item = {
            "item_id": "comparison:" + _native_sha({
                "request_id": request_id,
                "prediction_id": prediction["prediction_id"],
                "observation_ids": [row["sample_id"] for row in group["observations"]],
            })[7:31],
            "request_id": request_id,
            "prediction_id": prediction["prediction_id"],
            "boundary": group["boundary"],
            "identity": group["observations"][0]["identity"],
            "observed_ms": observed,
            "predicted_ms": predicted,
            "statistic": "median_of_observation_durations",
            "observation_ids": [row["sample_id"] for row in group["observations"]],
            "observation_samples": len(group["observations"]),
            "observation_range_ms": [min(group["durations_ms"]), max(group["durations_ms"])],
            "observation_clock_domains": sorted({
                str(row["clock"].get("domain")) for row in group["observations"]}),
            "observation_window_ids": sorted({
                str(row["window_id"]) for row in group["observations"]}),
            "condition_gaps": _native_item_condition_gaps(
                group["conditions"], prediction),
            "observation_evidence": {
                "pipe_times_us": [
                    row["evidence"].get("pipe_times_us", {})
                    for row in group["observations"]
                ],
                "block_num": [row["evidence"].get("block_num")
                              for row in group["observations"]],
            },
            "prediction_evidence": prediction["evidence"],
            "prediction_abi_digest": prediction["abi"].get("digest"),
            "observation_abi_digest": group["abi"].get("digest"),
            "comparison": {
                "signed_residual_ms": residual,
                "absolute_residual_ms": abs(residual),
                "relative_error": residual / observed,
                "formal_allowed_error_ms": formal_absolute + formal_relative * observed,
                "denominator": "observed_ms",
                "within_tolerance": within,
                "formal_policy": "fixed_itemwise_10pct_no_absolute_allowance",
                "sample_verdicts": sample_verdicts,
                "outside_sample_ids": outside_samples,
                "worst_absolute_relative_error": max(
                    abs(row["relative_error"]) for row in sample_verdicts),
            },
            "status": "within_tolerance" if within else "outside_tolerance",
        }
        items.append(item)
    for prediction in prediction_items:
        if prediction["prediction_id"] in used_predictions:
            continue
        near = near_misses.get(prediction["prediction_id"])
        if prediction["conflicts"]:
            reason = prediction["conflicts"][0]
        elif near:
            fields = sorted({
                field for row in near for field in row["identity_differences"]})
            reason = "request_identity_conflict:" + ",".join(fields)
        elif (prediction["request_id"]
              and prediction["request_id"] not in groups):
            reason = "unknown_request_id"
        else:
            reason = "no_exact_observation_identity"
        item = _unpaired_prediction(prediction, reason)
        if near:
            item["candidate_request_ids"] = [
                row["request_id"] for row in near]
            item["identity_differences"] = {
                row["request_id"]: row["identity_differences"] for row in near}
        unpaired_predictions.append(item)

    reported_window = observation_report.get("window")
    reported_windows = observation_report.get("windows")
    truncated = bool(observation_report.get("truncated"))
    has_coverage_scope = (
        isinstance(observations, Mapping)
        and isinstance(observations.get("window"), Mapping))
    reconciled = _native_coverage(
        observation_report, observation_items, truncated=truncated)
    partial = ((not has_coverage_scope) or truncated or any(
        not item["complete_in_window"] for item in observation_items) or any(
        item["structure"].get("status") != "confirmed" for item in observation_items)
        or not reconciled["reconciled"])
    if isinstance(reported_window, Mapping):
        partial = partial or str(reported_window.get("kind", "")).startswith("truncated")
    coverage = {
        "observations": len(observation_items),
        "predictions": len(prediction_items),
        "request_groups": len(groups),
        "truncated": truncated,
        "partial_coverage": partial,
        "window": reported_window,
        "windows": reported_windows if isinstance(reported_windows, list) else None,
        "source_identity": observation_report.get("source_identity"),
        "observation_counts": observation_report.get("counts"),
        "reconciliation": reconciled,
    }
    failure_matrix = _native_failure_matrix(
        items, unpaired_observations, unpaired_predictions, ambiguous, coverage)
    counts = {
        "observations": len(observation_items),
        "predictions": len(prediction_items),
        "request_groups": len(groups),
        "paired": len(items),
        "within_tolerance": sum(item["status"] == "within_tolerance" for item in items),
        "outside_tolerance": sum(item["status"] == "outside_tolerance" for item in items),
        "work_only": sum(item["status"] == "work_only" for item in items),
        "observation_verdicts": sum(
            len(item["comparison"]["sample_verdicts"]) for item in items),
        "observations_within_tolerance": sum(
            sum(row["within_tolerance"] for row in item["comparison"]["sample_verdicts"])
            for item in items),
        "observations_outside_tolerance": sum(
            sum(not row["within_tolerance"]
                for row in item["comparison"]["sample_verdicts"])
            for item in items),
        "items_with_condition_gaps": sum(bool(item["condition_gaps"]) for item in items),
        "predictions_without_independent_abi": sum(
            not item["abi_declared"] for item in prediction_items),
        "predictions_with_abi_conflict": sum(
            any(conflict.startswith("abi.") for conflict in item["conflicts"])
            for item in prediction_items),
        "request_identity_conflicts": sum(
            any(conflict.startswith(("boundary.", "conditions.", "occurrence.",
                                     "clock.", "timing."))
                for conflict in item["conflicts"])
            for item in prediction_items),
        "observation_abi_unverified": sum(
            not item["abi"].get("verified") for item in observation_items),
        "truncated": truncated,
        "partial_coverage": partial,
        "unpaired_observations": len(unpaired_observations),
        "unpaired_predictions": len(unpaired_predictions),
        "ambiguous": len(ambiguous),
        "family_aggregates_used": 0,
        "name_only_matches": 0,
        "fused_members_allocated": 0,
    }
    if counts["outside_tolerance"]:
        status = "failed"
    elif counts["work_only"]:
        status = "inconclusive"
    elif (not items or counts["unpaired_observations"]
          or counts["unpaired_predictions"] or counts["ambiguous"]):
        status = "inconclusive"
    elif partial:
        status = "partial"
    else:
        status = "passed"
    return {
        "schema": NATIVE_COMPARISON_SCHEMA,
        "status": status,
        "tolerance": {
            "formal": dict(FORMAL_NATIVE_TOLERANCE),
            "diagnostic": diagnostic,
            "applies_to": "paired_comparable_items_only",
        },
        "boundary_policy": {
            "join": "native_operator+native_abi_sha256+boundary+rank/device/stream/clock/window+declared_conditions",
            "name_only_allowed": False,
            "family_average_allowed": False,
            "fusion_member_allocation_allowed": False,
            "prediction_identity_required": True,
            "request_id_is_correlation_only": True,
            "clock_policy": "local duration valid without cross-domain mapping; "
                            "per-domain windows and causal edges only",
        },
        "coverage": coverage,
        "counts": counts,
        "items": items,
        "unpaired_observations": unpaired_observations,
        "unpaired_predictions": unpaired_predictions,
        "ambiguous": ambiguous,
        "failure_matrix": failure_matrix,
        "non_claims": [
            "no_family_average_or_signed_cancellation_pass",
            "no_name_only_pairing",
            "no_all_unknown_structure_accuracy",
            "no_fused_member_allocation",
            "no_observed_duration_in_prediction_request",
            "no_request_identity_copy_as_independent_prediction",
            "no_M_only_proxy_claim_as_native_abi_binding",
            "no_standalone_native_runtime_pricing_claim_for_model_proxy",
        ],
        "interpretation": (
            "Only paired, fully ABI/boundary-bound items enter the fixed formal "
            "10% denominator. Per-sample formal verdicts are never replaced by a "
            "median. Diagnostic tolerance is reported separately. Truncated or "
            "partial observation windows retain item results but cannot pass."
        ),
    }
