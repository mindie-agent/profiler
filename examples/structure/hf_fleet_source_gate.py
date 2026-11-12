"""Original fleet scalar and operator comparison.

The row ``observed_ms`` is the input scalar. A client TPOT or TTFT is recorded
beside it and is not a completion condition. The reducer and the window key
set come from the producer identity and the declared population. They are
fixed before any target number is read. A mismatch or a missing target does
not select a different reducer. Family, required core, and unified groups use
the maximum of total error, uncancelled error, and per-group error. Canonical
groups are diagnostic and do not decide coverage. A required group that the
forecast omits is failed. A map the original source never declared stays
inapplicable. When ``predicted_operator_ms`` is present it must match the
family prediction sum.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Mapping, Sequence

from hf_fleet_source_producer import producer_contract as _producer_contract
from hf_sample_scoring import sample_key

_CANONICAL_FAMILY = {
    "moe.combine": "moe", "moe.dispatch": "moe", "moe": "moe",
    "collective": "collective", "attention": "attention", "gemm": "gemm",
    "kv_cache": "kv_cache", "norm_activation": "norm_residual",
    "elementwise_quant": "elementwise_quant", "other": "other",
}
_UNIFIED_FAMILY = {
    "moe.combine": "moe_routing_grouped_gemm", "moe.dispatch": "moe_routing_grouped_gemm",
    "moe": "moe_routing_grouped_gemm", "collective": "collective_comm",
    "attention": "attention", "gemm": "matmul_gemm",
    "kv_cache": "kv_cache_position_rope",
    "norm_activation": "norm_activation_elementwise",
    "elementwise_quant": "norm_activation_elementwise", "other": "unclassified",
}
_CORE_CANON = {
    "AI_CORE": "AI_CORE", "AI_VECTOR_CORE": "AI_VECTOR_CORE", "AI_CPU": "AI_VECTOR_CORE",
    "MIX_AIC": "MIX_AIC", "COMMUNICATION": "COMMUNICATION", "MIX_AIV": "COMMUNICATION",
    "DSA_SQE": "COMMUNICATION",
}
_PASS = 0.10


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _finite(value: Any) -> float | None:
    number = _as_float(value)
    if number is None or not math.isfinite(number):
        return None
    return number


def _verbatim(value: Any) -> float | None:
    number = _finite(value)
    if number is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    return number


def _same_number(left: Any, right: Any) -> bool:
    a, b = _finite(left), _finite(right)
    if a is None or b is None:
        return False
    return abs(a - b) <= 1e-6 * max(1.0, abs(a), abs(b))


def _row_observed(row: Mapping[str, Any]) -> float | None:
    """Input scalar. ``observed_ms`` wins over a previously enrolled copy."""
    if "observed_ms" in row:
        return _verbatim(row.get("observed_ms"))
    if "source_observed_ms" in row:
        return _verbatim(row.get("source_observed_ms"))
    return None


def _client_observation(observation: Mapping[str, Any] | None) -> tuple[float | None, str]:
    if not isinstance(observation, Mapping):
        return None, ""
    basis = str(observation.get("observed_basis") or "")
    if not basis:
        client = (observation.get("measurements") or {}).get("native_client_request") or {}
        if isinstance(client, Mapping):
            basis = str(client.get("samples_basis") or "")
    return _verbatim(observation.get("observed_ms")), basis


def _predicted_step(prediction: Mapping[str, Any] | None) -> float | None:
    if not isinstance(prediction, Mapping):
        return None
    for key in ("predicted_step_ms", "predicted_step"):
        number = _finite(prediction.get(key))
        if number is not None:
            return number
    return None


def _window(observation: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(observation, Mapping):
        return {}
    window = (observation.get("measurements") or {}).get("per_forward_window")
    return window if isinstance(window, Mapping) else {}


def _series(observation: Mapping[str, Any] | None) -> tuple[list[float] | None, str]:
    window = _window(observation)
    if window and str(window.get("status") or "") not in {"", "measured"}:
        return None, str(window.get("samples_basis") or "")
    raw = None
    for name in ("samples_ms", "forward_spans_ms", "spans_ms"):
        candidate = window.get(name)
        if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes)) and candidate:
            raw = candidate
            break
    if raw is None:
        return None, str(window.get("samples_basis") or "")
    values: list[float] = []
    for item in raw:
        number = _finite(item)
        if number is None:
            return None, str(window.get("samples_basis") or "")
        values.append(number)
    return values, str(window.get("samples_basis") or "")


def _reduce(values: Sequence[float], reducer: str) -> float | None:
    if not values:
        return None
    if reducer == "single":
        return values[0] if len(values) == 1 else None
    if reducer == "mean":
        return statistics.fmean(values)
    if reducer == "median":
        return float(statistics.median(values))
    if reducer == "sum":
        return math.fsum(values)
    return None


def _enrollment_match(observed: float | None, produced: float | None) -> bool:
    """Source-number check used only after the reducer is already chosen."""
    if observed is None or produced is None:
        return False
    if _same_number(observed, produced):
        return True
    return round(float(produced), 4) == round(float(observed), 4)


def _vector_count(prediction: Mapping[str, Any] | None) -> int:
    if not isinstance(prediction, Mapping):
        return 0
    samples = prediction.get("boundary_samples")
    if isinstance(samples, Mapping):
        return len(samples)
    if isinstance(samples, Sequence) and not isinstance(samples, (str, bytes)):
        return len(samples)
    for name in ("boundary_samples_ms", "samples_ms", "per_forward_ms", "predicted_samples_ms"):
        raw = prediction.get(name)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and raw:
            return len(raw)
    return 0


def _sample_value(value: Any) -> float | None:
    """Forecast value only. An observed column is not a missing prediction."""
    if isinstance(value, Mapping):
        for name in ("boundary_ms", "predicted_ms", "predicted_boundary_ms",
                     "value_ms", "mean_ms"):
            number = _finite(value.get(name))
            if number is not None:
                return number
        return None
    return _finite(value)


def _blank_scalar(observed: float | None, client: float | None, basis: str, step: float | None,
                  status: str, reason: str, population: str, reducer: str = "") -> dict[str, Any]:
    return {
        "source_observed_ms": observed,
        "source_observation_ms": client,
        "source_observation_basis": basis,
        "predicted_step_ms": step,
        "predicted_aggregate_ms": None,
        "status": status,
        "reason": reason,
        "reducer": reducer,
        "population": population,
        "signed_error": None,
        "passed_10pct": False,
    }


def _same_proof(row: Mapping[str, Any], observation: Mapping[str, Any] | None,
                prediction: Mapping[str, Any] | None) -> bool:
    observation = observation or {}
    prediction = prediction or {}
    capture = observation.get("capture") if isinstance(observation.get("capture"), Mapping) else {}
    identities = [str(value) for value in (
        row.get("capture_id"), capture.get("capture_id"), prediction.get("capture_id"),
    ) if value not in (None, "")]
    if len(set(identities)) > 1:
        return False
    phases = [str(value).lower() for value in (
        row.get("phase"), capture.get("row_phase") or capture.get("phase"), prediction.get("phase"),
    ) if value not in (None, "")]
    if len(set(phases)) > 1:
        return False
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    digests = [str(value).lower() for value in (source.get("sha256"), prediction.get("source_sha256")) if value]
    return len(set(digests)) <= 1


_IDENTITY_HOLD = {
    "hardware_provenance_absent", "prediction_boundary_scope_mismatch",
    "hardware_mismatch", "model_mismatch", "capture_id_mismatch", "phase_mismatch",
    "source_sha256_mismatch",
}


def _identity_hold(boundary: Mapping[str, Any] | None) -> str:
    if not isinstance(boundary, Mapping):
        return ""
    reason = str(boundary.get("reason") or "")
    return reason if reason in _IDENTITY_HOLD else ""


def _cohort_prediction(prediction: Mapping[str, Any] | None, records: Sequence[Mapping[str, Any]]) -> list[float] | None:
    """Keyed forecast on the producer key set. Keys outside that set are ignored."""
    if not isinstance(prediction, Mapping):
        return None
    wanted = [str(row["key"]) for row in records]
    wanted_set = set(wanted)
    samples = prediction.get("boundary_samples")
    found: dict[str, float] = {}
    if isinstance(samples, Mapping):
        pairs = [(str(key), value) for key, value in samples.items()]
    elif isinstance(samples, Sequence) and not isinstance(samples, (str, bytes)):
        pairs = []
        for item in samples:
            if not isinstance(item, Mapping):
                return None
            pairs.append((str(sample_key(**item)), item))
    else:
        return None
    for key, value in pairs:
        if not key or key not in wanted_set:
            continue
        number = _sample_value(value)
        if number is None or key in found:
            return None
        found[key] = number
    if any(key not in found for key in wanted):
        return None
    return [found[key] for key in wanted]


def _closed_scalar(observed: float | None, client: float | None, basis: str, step: float | None,
                   status: str, reason: str, population: str, reducer: str, *,
                   aggregate: float | None = None, producer: str = "", label: str = "",
                   count: int = 0, window_filter: Mapping[str, Any] | None = None) -> dict[str, Any]:
    signed = None
    passed = False
    if status == "compared" and observed not in (None, 0) and aggregate is not None:
        signed = (float(aggregate) - float(observed)) / abs(float(observed))
        passed = abs(signed) <= _PASS
        if label == "conditional":
            passed = False
            reason = "conditional_population"
    return {
        "source_observed_ms": observed,
        "source_observation_ms": client,
        "source_observation_basis": basis,
        "predicted_step_ms": step,
        "predicted_aggregate_ms": aggregate,
        "status": status,
        "reason": reason,
        "reducer": reducer,
        "producer": producer,
        "population": population,
        "population_label": label,
        "population_count": count,
        "window_filter": dict(window_filter or {}),
        "signed_error": signed,
        "passed_10pct": passed,
    }


def score_source_scalar(row: Mapping[str, Any], observation: Mapping[str, Any] | None,
                        prediction: Mapping[str, Any] | None,
                        boundary: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compare the row scalar with the reducer the producer already named.

    The client observation is returned and is not read by the status. The
    target number is not used to choose mean, median, or sum.
    """
    observed = _row_observed(row)
    client, basis_client = _client_observation(observation)
    step = _predicted_step(prediction)
    values, basis = _series(observation)
    raw_observed = row.get("observed_ms") if "observed_ms" in row else row.get("source_observed_ms")
    raw_number = _as_float(raw_observed)
    nonfinite = raw_number is not None and not math.isfinite(raw_number)
    population = "multi" if values is not None and len(values) > 1 else "single" if values else "absent"
    if nonfinite:
        return _blank_scalar(None, client, basis_client, step, "ambiguous", "observed_nonfinite", population)
    if observed == 0:
        return _blank_scalar(observed, client, basis_client, step, "ambiguous", "observed_zero", population)
    if not _same_proof(row, observation, prediction):
        return _blank_scalar(observed, client, basis_client, step, "ambiguous", "capture_phase_source_mismatch", population)
    hold = _identity_hold(boundary)
    if hold:
        return _blank_scalar(observed, client, basis_client, step, "ambiguous", hold, population)
    if values:
        contract = _producer_contract(row, observation, values, basis)
        reducer = str(contract.get("reducer") or "")
        producer = str(contract.get("producer") or "")
        label = str(contract.get("label") or "")
        selected = list(contract.get("records") or [])
        window_filter = contract.get("window_filter") if isinstance(contract.get("window_filter"), Mapping) else {}
        if contract.get("status") != "ready":
            return _closed_scalar(observed, client, basis_client, step, str(contract.get("status") or "ambiguous"),
                                  str(contract.get("reason") or "producer_unsupported"), population, reducer,
                                  producer=producer, label=label, count=len(selected), window_filter=window_filter)
        aligned = _cohort_prediction(prediction, selected)
        aggregate = None if aligned is None else _reduce(aligned, reducer)
        if aligned is None or aggregate is None:
            status = "missing" if step is None and _vector_count(prediction) == 0 else "ambiguous"
            reason = "forecast_population_absent" if status == "missing" else "population_incomplete"
            return _closed_scalar(observed, client, basis_client, step, status, reason, population, reducer,
                                  producer=producer, label=label, count=len(selected), window_filter=window_filter)
        if observed is None:
            return _closed_scalar(observed, client, basis_client, step, "unavailable", "target_absent", population,
                                  reducer, aggregate=float(aggregate), producer=producer, label=label,
                                  count=len(selected), window_filter=window_filter)
        source_reduced = _reduce([float(item["value"]) for item in selected], reducer)
        if not _enrollment_match(observed, source_reduced):
            return _closed_scalar(observed, client, basis_client, step, "unavailable", "source_number_inconsistent",
                                  population, reducer, aggregate=float(aggregate), producer=producer, label=label,
                                  count=len(selected), window_filter=window_filter)
        return _closed_scalar(float(observed), client, basis_client, step, "compared", reducer, population, reducer,
                              aggregate=float(aggregate), producer=producer, label=label,
                              count=len(selected), window_filter=window_filter)
    declared_steps = _finite(row.get("forward_steps"))
    if declared_steps is not None and declared_steps > 1:
        return _closed_scalar(observed, client, basis_client, step, "ambiguous", "forecast_population_absent",
                              "absent", "", producer="declared_multi_window")
    if _vector_count(prediction) > 0:
        return _blank_scalar(observed, client, basis_client, step, "ambiguous", "partial_population", "single")
    if observed is None and step is None:
        return _blank_scalar(None, client, basis_client, None, "missing", "scalar_absent", "absent")
    if observed is None or step is None:
        return _blank_scalar(observed, client, basis_client, step, "ambiguous", "scalar_side_absent", "single")
    return _closed_scalar(float(observed), client, basis_client, step, "compared", "single", "single", "single",
                          aggregate=float(step), producer="single_host", label="single", count=1)


def retarget_scalar(scalar: Mapping[str, Any], observed: Any) -> dict[str, Any]:
    """Keep a stored decision on the row scalar when a client value was written over it."""
    out = dict(scalar)
    previous = out.get("source_observed_ms")
    verbatim = _verbatim(observed) if observed is not None else None
    if previous == verbatim or (previous is None and verbatim is None):
        out["source_observed_ms"] = observed if verbatim is None else verbatim
        return out
    predicted = _finite(out.get("predicted_aggregate_ms"))
    if predicted is not None and _same_number(predicted, previous):
        out.update({
            "source_observed_ms": verbatim,
            "status": "ambiguous",
            "reason": "observed_displaced",
            "signed_error": None,
            "passed_10pct": False,
            "predicted_aggregate_ms": None,
        })
        return out
    out["source_observed_ms"] = verbatim
    if out.get("status") == "compared":
        if verbatim is None or verbatim == 0 or predicted is None:
            out["status"] = "ambiguous"
            out["reason"] = "observed_retargeted"
            out["signed_error"] = None
            out["passed_10pct"] = False
        else:
            signed = (predicted - float(verbatim)) / abs(float(verbatim))
            out["signed_error"] = signed
            if out.get("population_label") == "conditional":
                out["passed_10pct"] = False
                out["reason"] = "conditional_population"
            else:
                out["passed_10pct"] = abs(signed) <= _PASS
    return out


def _unify(raw: Mapping[str, Any] | None, names: Mapping[str, str]) -> dict[str, float] | None:
    if not isinstance(raw, Mapping) or not raw:
        return None
    out: dict[str, float] = {}
    for key, value in raw.items():
        if value is None:
            continue
        number = _finite(value)
        if number is None:
            return None
        dest = names.get(str(key), str(key))
        out[dest] = out.get(dest, 0.0) + number
    return out or None


def _has_finite_prediction(raw: Mapping[str, Any] | None) -> bool:
    if not isinstance(raw, Mapping):
        return False
    return any(value is not None and _finite(value) is not None for value in raw.values())


def _finite_group(raw: Mapping[str, Any] | None) -> dict[str, float] | None:
    if not isinstance(raw, Mapping) or not raw:
        return None
    out: dict[str, float] = {}
    for key, value in raw.items():
        if value is None:
            continue
        number = _finite(value)
        if number is None:
            return None
        out[str(key)] = number
    return out or None


def _pair_exact(measured: Mapping[str, float] | None, predicted: Mapping[str, Any] | None, *,
                allow_extra: bool = False) -> tuple[str, str, dict[str, Any]]:
    """Pair one namespace. A required group the forecast omits is failed, not inapplicable.

    Core forecasts may carry extra keys, including a zero core the measurement
    did not declare. Family and unified keep exact key sets. Extra keys are
    not folded into the error.
    """
    measured_values = _finite_group(measured)
    prediction_map = predicted if isinstance(predicted, Mapping) else None
    positive = _has_finite_prediction(prediction_map)
    if measured_values is None:
        if not positive:
            return "inapplicable", "null_inapplicable", {}
        return "unknown", "measured_groups_absent", {}
    if not positive:
        return "failed", "required_group_missing", {}
    predicted_values: dict[str, float] = {}
    for key, value in prediction_map.items():
        if value is None:
            continue
        number = _finite(value)
        if number is None:
            if allow_extra and str(key) not in measured_values:
                continue
            return "ambiguous", "zero_or_nonfinite", {}
        predicted_values[str(key)] = number
    if allow_extra:
        if any(key not in predicted_values for key in measured_values):
            return "ambiguous", "operator_key_mismatch", {}
    elif set(measured_values) != set(predicted_values):
        return "ambiguous", "operator_key_mismatch", {}
    groups: dict[str, Any] = {}
    for key in sorted(measured_values):
        obs, pred = measured_values[key], predicted_values[key]
        if obs == 0.0:
            if pred != 0.0:
                return "ambiguous", "zero_or_nonfinite", {}
            relative = 0.0
        else:
            relative = abs(pred - obs) / abs(obs)
        groups[key] = {"observed_ms": obs, "predicted_ms": pred, "relative_error": relative}
    obs_total = math.fsum(item["observed_ms"] for item in groups.values())
    pred_total = math.fsum(item["predicted_ms"] for item in groups.values())
    uncancelled_abs = math.fsum(abs(item["predicted_ms"] - item["observed_ms"]) for item in groups.values())
    if obs_total == 0.0:
        if pred_total != 0.0 or uncancelled_abs != 0.0:
            return "ambiguous", "zero_or_nonfinite", {}
        total_rel = 0.0
        uncancelled = 0.0
    else:
        uncancelled = uncancelled_abs / abs(obs_total)
        total_rel = abs(pred_total - obs_total) / abs(obs_total)
    peak = max(item["relative_error"] for item in groups.values())
    return "compared", "", {
        "groups": groups,
        "relative_error": max(total_rel, uncancelled, peak),
        "uncancelled": uncancelled,
        "keys": sorted(groups),
    }


def _namespace(measured_scopes: Mapping[str, float] | None, kind: str) -> dict[str, float] | None:
    if measured_scopes is None:
        return None
    if kind == "family":
        return dict(measured_scopes)
    if kind == "canonical":
        return _unify(measured_scopes, _CANONICAL_FAMILY)
    if kind == "unified":
        return _unify(measured_scopes, _UNIFIED_FAMILY)
    return None


_DECLARED_GROUPS = (
    ("family", "families"),
    ("canonical", "canonical_families"),
    ("unified", "unified_families"),
    ("core", "by_accelerator_core"),
)


def _flatten_observed(raw: Any) -> dict[str, float] | None:
    """Observed side of a nested operator group. Stored predicted_ms is not a forecast."""
    if not isinstance(raw, Mapping) or not raw:
        return None
    out: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, Mapping):
            if "observed_ms" not in value:
                return None
            number = _finite(value.get("observed_ms"))
        else:
            number = _finite(value)
        if number is None:
            return None
        out[str(key)] = number
    return out or None


def declared_operator_maps(row: Mapping[str, Any] | None) -> dict[str, dict[str, float] | None] | None:
    """Original kernel-group sums. This is not the scalar window cohort."""
    block = row.get("operator_modeling") if isinstance(row, Mapping) else None
    if not isinstance(block, Mapping):
        return None
    maps: dict[str, dict[str, float] | None] = {}
    present = False
    for kind, key in _DECLARED_GROUPS:
        flat = _flatten_observed(block.get(key)) if key in block else None
        maps[kind] = flat
        present = present or bool(flat)
    return maps if present else None


def _family_total_matches(prediction: Mapping[str, Any], detail: Mapping[str, Any],
                          *, declared_total: bool = False) -> bool | None:
    """Original family-sum check.

    A forecast that omits a total is not failed when the original row never
    declared one. If the original row did declare ``predicted_operator_ms``,
    deleting it from the forecast does not erase that requirement.
    """
    if "predicted_operator_ms" not in prediction:
        return False if declared_total else None
    total = _finite(prediction.get("predicted_operator_ms"))
    groups = detail.get("groups") if isinstance(detail.get("groups"), Mapping) else None
    if total is None or not groups:
        return False
    predicted = math.fsum(float(item["predicted_ms"]) for item in groups.values())
    return math.isclose(predicted, total, rel_tol=1e-3, abs_tol=1e-3)


def compare_operator_projection(measured_scopes_ms: Mapping[str, float] | None,
                                measured_cores_ms: Mapping[str, float] | None,
                                prediction: Mapping[str, Any] | None, *,
                                same_proof: bool = True, source_declared: bool = False,
                                measured_canonical: Mapping[str, float] | None = None,
                                measured_unified: Mapping[str, float] | None = None,
                                declared_total: bool = False) -> dict[str, Any]:
    """Original max and noncancellation. Core groups are not the scalar window set."""
    prediction = prediction or {}
    if source_declared:
        plan = (
            ("family", _finite_group(measured_scopes_ms), prediction.get("predicted_by_family_ms")),
            ("canonical", _finite_group(measured_canonical), prediction.get("predicted_by_canonical_family_ms")),
            ("unified", _finite_group(measured_unified), prediction.get("predicted_by_unified_family_ms")),
            ("core", _finite_group(measured_cores_ms), prediction.get("predicted_by_core_ms")),
        )
    else:
        scopes = None if not measured_scopes_ms else {str(key): value for key, value in measured_scopes_ms.items()}
        cores = _unify(measured_cores_ms, _CORE_CANON) if measured_cores_ms else None
        plan = (
            ("family", _namespace(scopes, "family"), prediction.get("predicted_by_family_ms")),
            ("canonical", _namespace(scopes, "canonical"), prediction.get("predicted_by_canonical_family_ms")),
            ("unified", _namespace(scopes, "unified"), prediction.get("predicted_by_unified_family_ms")),
            ("core", cores, prediction.get("predicted_by_core_ms")),
        )
    declared = any(_has_finite_prediction(pred if isinstance(pred, Mapping) else None) for _name, _meas, pred in plan)
    measured = any(item is not None for _name, item, _pred in plan)
    if not declared and not measured:
        return {"status": "unavailable", "reason": "operator_maps_absent", "passed_10pct": False,
                "operator_relative_error": None, "operator_population": "kernel_group_sums", "maps": {}}
    if not same_proof:
        return {"status": "ambiguous", "reason": "capture_phase_source_mismatch", "passed_10pct": False,
                "operator_relative_error": None, "operator_population": "kernel_group_sums", "maps": {}}
    maps: dict[str, Any] = {}
    errors: list[float] = []
    headline: tuple[str, str] | None = None
    family_detail: Mapping[str, Any] | None = None
    rank = {"failed": 3, "unknown": 2, "ambiguous": 2}
    for name, measured_map, predicted_map in plan:
        status, reason, detail = _pair_exact(
            measured_map, predicted_map if isinstance(predicted_map, Mapping) else None,
            allow_extra=(name == "core"),
        )
        maps[name] = {"status": status, "reason": reason, "keys": list(detail.get("keys") or [])}
        if status == "compared":
            maps[name]["relative_error"] = detail["relative_error"]
        if name == "canonical":
            continue
        if status == "compared":
            errors.append(float(detail["relative_error"]))
            if name == "family":
                family_detail = detail
        elif rank.get(status, 0) > rank.get(headline[0], 0) if headline else rank.get(status, 0) > 0:
            headline = (status, reason)
    if headline is None and family_detail is not None:
        matched = _family_total_matches(prediction, family_detail, declared_total=declared_total)
        if matched is False:
            headline = ("failed", "predicted_operator_total")
    if headline is not None:
        return {"status": headline[0], "reason": headline[1], "passed_10pct": False,
                "operator_relative_error": None, "operator_population": "kernel_group_sums", "maps": maps}
    if not errors:
        return {"status": "unavailable", "reason": "operator_maps_absent", "passed_10pct": False,
                "operator_relative_error": None, "operator_population": "kernel_group_sums", "maps": maps}
    peak = max(errors)
    return {"status": "compared", "reason": "", "passed_10pct": peak <= _PASS,
            "operator_relative_error": peak, "operator_population": "kernel_group_sums", "maps": maps}


def measured_scopes(observation: Mapping[str, Any] | None) -> tuple[dict[str, float] | None, dict[str, float] | None]:
    """Raw millisecond group identities already on the observation. No share allocation."""
    if not isinstance(observation, Mapping):
        return None, None
    families = observation.get("observed_by_family_ms")
    cores = observation.get("observed_by_core_ms")
    family_map = None
    core_map = None
    if isinstance(families, Mapping) and families:
        unified = _unify(families, {})
        family_map = unified
    if isinstance(cores, Mapping) and cores:
        core_map = {str(key): value for key, value in cores.items()}
    return family_map, core_map


def apply_original_gate(scalar: Mapping[str, Any], operator: Mapping[str, Any]) -> dict[str, Any]:
    """A missing required group blocks. An originally absent map does not.

    A conditional prefill population is not a completion pass. Operator
    kernel sums are not resized to the scalar window cohort.
    """
    scalar_status = str(scalar.get("status") or "missing")
    conditional = str(scalar.get("population_label") or "") == "conditional"
    scalar_pass = bool(scalar.get("passed_10pct")) and scalar_status == "compared" and not conditional
    operator_status = str(operator.get("status") or "unavailable")
    operator_reason = str(operator.get("reason") or "")
    operator_pass = bool(operator.get("passed_10pct")) and operator_status == "compared"
    blocked = operator_status in {"ambiguous", "failed", "unknown"} or (
        operator_status == "compared" and not operator_pass
    ) or operator_reason == "required_group_missing"
    return {
        "target": "observed_ms/source_aggregate",
        "operator_aggregate": "family_maximum/core_maximum/unified_maximum/uncancelled",
        "scalar_status": scalar_status,
        "scalar_passed_10pct": scalar_pass,
        "operator_status": operator_status,
        "operator_passed_10pct": operator_pass,
        "passed_10pct": bool(scalar_pass and not blocked),
        "ambiguous": scalar_status == "ambiguous" or operator_status == "ambiguous",
        "signed_error": scalar.get("signed_error") if scalar_status == "compared" else None,
        "reducer": str(scalar.get("reducer") or ""),
        "source_observed_ms": scalar.get("source_observed_ms"),
        "source_observation_ms": scalar.get("source_observation_ms"),
        "source_observation_basis": str(scalar.get("source_observation_basis") or ""),
    }


def fleet_row_decision(row: Mapping[str, Any]) -> dict[str, Any]:
    """Use the stored frozen result. Recompute only when this row has none."""
    scalar = row.get("source_scalar") if isinstance(row.get("source_scalar"), Mapping) else None
    operator = row.get("source_operator") if isinstance(row.get("source_operator"), Mapping) else None
    verbatim = row.get("observed_ms") if "observed_ms" in row else row.get("source_observed_ms")
    if scalar is None:
        view: dict[str, Any] = {}
        if row.get("source_predicted_step") is not None:
            view["predicted_step_ms"] = row.get("source_predicted_step")
        scalar = score_source_scalar(row, {"measurements": row.get("measurements") or {}}, view, None)
    elif scalar.get("source_observed_ms") != _verbatim(verbatim) and "observed_ms" in row:
        scalar = retarget_scalar(scalar, verbatim)
    if operator is None:
        families = _unify(row.get("observed_by_family_ms"), {}) if isinstance(row.get("observed_by_family_ms"), Mapping) else None
        cores = row.get("observed_by_core_ms") if isinstance(row.get("observed_by_core_ms"), Mapping) else None
        declared = None if families or cores else declared_operator_maps(row)
        view = {key: row.get(key) for key in (
            "predicted_by_family_ms", "predicted_by_core_ms",
            "predicted_by_canonical_family_ms", "predicted_by_unified_family_ms",
            "predicted_operator_ms",
        )}
        if declared is not None:
            operator = compare_operator_projection(
                declared.get("family"), declared.get("core"), view, same_proof=True, source_declared=True,
                measured_canonical=declared.get("canonical"), measured_unified=declared.get("unified"),
                declared_total=("predicted_operator_ms" in (row.get("operator_modeling") or {})),
            )
        else:
            operator = compare_operator_projection(families, cores, view, same_proof=True)
    return apply_original_gate(scalar, operator)
