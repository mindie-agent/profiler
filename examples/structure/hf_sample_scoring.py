"""Exact keyed scoring for the 7,337-capture profiling benchmark.

This is the single sample scorer.  A sample is a finite measured value on
the *same* physical boundary and identity as a predicted value.  Keys are
opaque lineage identifiers (capture/case, rank, phase, step, layer,
occurrence, request/forward, op type, native accelerator engine).  Pairs are
formed by key, never by list position, so reordering records does not change
a score.

Deliberately not samples: additive kernel mass, resource busy seconds,
family/scope aggregates, producer-recorded model-step fields, and any
observation whose basis is a different physical quantity.  Missing and
duplicate keys stay in the denominator and are reported by key.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Mapping, Sequence

__all__ = [
    "score_boundary",
    "score_operator_groups",
    "observed_sample_table",
    "observed_boundary_population",
    "observed_operator_table",
    "sample_key",
    "operator_key",
]

_PREDICTION_OK = {"predicted", "modeled"}
_MEASURED = {"measured", "reported"}
# These are recorded aggregates/projections, not an elapsed per-sample boundary.
_NOT_A_SAMPLE = {
    "whole_capture_native_kernel_rows_all_streams_additive",
    "capture_op_statistic_aggregate",
    "native_call_set",
    "raw_native_call_set_not_model_forward",
    "producer_reported_device_forward_span",
    "model_step_ms_undeclared",
}
_BOUNDARY_ALIASES = {
    "per_forward_window_elapsed": ("per_forward_window", "elapsed"),
    "per_forward_window_additive": ("per_forward_window", "additive"),
}
# Exact documented prediction scopes only.  Prefix/fuzzy acceptance is forbidden:
# an invented label must not borrow another boundary's samples.
_SUPPORTED_BOUNDARIES = {
    "native_calls", "per_forward_window", "per_forward_window_elapsed",
    "per_forward_window_additive", "native_client_request",
}
_KEY_FIELDS = (
    "capture_id", "case_id", "group_id", "phase", "rank_id", "rank",
    "device_id", "step_index", "layer_index", "occurrence", "turn_idx",
    "request_id", "request_index", "req_idx", "forward_id", "op_type",
    "op", "engine", "core",
)
_SERIES_FIELDS = (
    "boundary_samples_ms", "samples_ms", "forward_spans_ms", "spans_ms",
    "per_forward_ms", "values",
)
_META_GROUP_KEYS = {
    "status", "boundary", "basis", "samples_basis", "source", "unit",
    "note", "groups", "capture_id", "phase", "rank_id", "hardware_tier",
    "source_sha256", "raw_sha256", "recorded_source_sha256",
    "reported_source_sha256", "source_path", "source_size_bytes", "capture",
    "rank", "device", "device_id", "workload", "workload_id", "native_phase",
    "row_phase", "phase_basis", "phase_conflict", "call_count", "sample_keys",
    "samples", "calls", "frame_identifiers", "samples_ms",
}


def sample_key(**identity: Any) -> str:
    """Canonical opaque key for one measured/predicted sample."""
    explicit = identity.get("key") or identity.get("sample_key")
    if explicit not in (None, ""):
        return str(explicit)
    parts = [f"{name}={identity[name]}" for name in _KEY_FIELDS
             if identity.get(name) not in (None, "")]
    return "|".join(parts) or "sample"


def operator_key(op_type: str, engine: str, **identity: Any) -> str:
    """Canonical op x native-engine key.  ``engine`` is the raw Accelerator Core."""
    parts = [str(op_type), str(engine)]
    parts += [f"{name}={identity[name]}" for name in _KEY_FIELDS
              if identity.get(name) not in (None, "")]
    return "\x1f".join(parts)


def _blank(reason: str, boundary: str, comparison: str = "uncovered",
           sample: float | None = None, **extra: Any) -> dict[str, Any]:
    out = {"comparison": comparison, "reason": reason, "boundary": boundary,
           "passed_10pct": False, "sample": sample}
    nested = extra.pop("extra", None)
    if isinstance(nested, Mapping):
        extra.update(nested)
    out.update(extra)
    return out


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cell(value: Any) -> float:
    """A present cell that is not numeric is invalid, not absent."""
    number = _number(value)
    return float("nan") if number is None else number


def _pair_error(predicted: Any, observed: Any) -> tuple[str, float]:
    """One pair.  Negative/non-finite/zero observations never become zero error."""
    left, right = _number(predicted), _number(observed)
    if left is None or right is None or not math.isfinite(left) or not math.isfinite(right):
        return "non_finite", float("nan")
    if left < 0.0 or right < 0.0:
        return "negative_duration", float("nan")
    if right == 0.0:
        return "zero_observation", float("nan")
    return "", abs(left - right) / abs(right)


def _record_key(record: Mapping[str, Any], index: int, prefix: str = "sample") -> str:
    for name in ("key", "sample_key", "record_key"):
        if record.get(name) not in (None, ""):
            return str(record[name])
    parts = [f"{name}={record[name]}" for name in _KEY_FIELDS
             if record.get(name) not in (None, "")]
    return "|".join(parts) if parts else f"{prefix}:{index}"


def _record_value(record: Mapping[str, Any], phase: str, boundary: str) -> float | None:
    if record.get("ok") is False:
        return None
    if str(record.get("status") or "").lower() in {"failed", "unknown", "insufficient_evidence",
                                                    "model_rejected", "not_measured"}:
        return None
    fields: tuple[str, ...] = ()
    if boundary == "native_client_request":
        fields = (("tpot_ms", "reported_tpot_ms") if phase == "decode"
                  else ("ttft_ms", "reported_ttft_ms") if phase == "prefill" else ())
    fields += ("value_ms", "boundary_ms", "observed_ms", "duration_ms",
               "span_ms", "forward_span_ms", "total_ms")
    for name in fields:
        if name in record and record.get(name) not in (None, ""):
            return _cell(record[name])
    return None


def _forecast_record_value(record: Mapping[str, Any], phase: str, boundary: str) -> float | None:
    """Explicit forecast cell only. An observed column is not a forecast."""
    if record.get("ok") is False:
        return None
    if str(record.get("status") or "").lower() in {"failed", "unknown", "insufficient_evidence",
                                                    "model_rejected", "not_measured"}:
        return None
    fields: tuple[str, ...] = ()
    if boundary == "native_client_request":
        fields = (("tpot_ms", "reported_tpot_ms") if phase == "decode"
                  else ("ttft_ms", "reported_ttft_ms") if phase == "prefill" else ())
    fields += ("predicted_ms", "predicted_boundary_ms", "boundary_ms", "value_ms", "mean_ms")
    for name in fields:
        if name in record and record.get(name) not in (None, ""):
            return _cell(record[name])
    return None


def _phase_of(observation: Mapping[str, Any], entry: Mapping[str, Any]) -> str:
    for source in (entry, observation.get("capture") or {}, observation):
        value = str((source or {}).get("phase") or "").lower()
        if value:
            return value
    return ""


def _unit_scale(entry: Mapping[str, Any]) -> float:
    unit = str(entry.get("unit") or entry.get("units") or "ms").lower()
    return 0.001 if unit in {"us", "microsecond", "microseconds"} else 1.0


def _basis(entry: Mapping[str, Any]) -> str:
    for name in ("samples_basis", "basis", "observed_basis", "metric_basis"):
        value = str(entry.get(name) or "").lower()
        if value:
            return value
    if any("additive" in str(entry.get(name) or "").lower()
           for name in ("mean_additive_us_per_window", "mean_additive_us_per_call")):
        return "additive"
    return ""


def _is_additive(basis: str) -> bool:
    return "additive" in basis or "busy" in basis or "class_sum" in basis


def _entry_table(entry: Mapping[str, Any], *, phase: str, boundary: str,
                 prefix: str = "sample") -> dict[str, Any] | None:
    """Build a keyed table from one measurement entry.  No list filtering."""
    scale = _unit_scale(entry)
    records = entry.get("samples")
    if isinstance(records, Sequence) and not isinstance(records, (str, bytes)) and records:
        if isinstance(records[0], Mapping):
            keys = [_record_key(row, index, prefix) if isinstance(row, Mapping)
                    else f"{prefix}:{index}" for index, row in enumerate(records)]
            values = [(_record_value(row, phase, boundary) if isinstance(row, Mapping)
                       else _cell(row)) for row in records]
            if scale != 1.0:
                values = [None if value is None else value * scale for value in values]
            return {"keys": keys, "values": values, "basis": _basis(entry),
                    "keyed": True, "scale": scale, "source": "records"}
    for name in _SERIES_FIELDS:
        raw = entry.get(name)
        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)) or not raw:
            continue
        keys = entry.get("sample_keys") or entry.get("keys") or entry.get("labels")
        if not isinstance(keys, Sequence) or len(keys) != len(raw):
            frames = entry.get("frame_identifiers")
            if isinstance(frames, Sequence) and len(frames) == len(raw) and all(isinstance(f, Mapping) for f in frames):
                keys = [_record_key(frame, index, prefix) for index, frame in enumerate(frames)]
            else:
                keys = [f"pos:{index}" for index in range(len(raw))]
        values = [None if value is None else _cell(value) * scale for value in raw]
        return {"keys": [str(key) for key in keys], "values": values,
                "basis": _basis(entry), "keyed": any(not str(k).startswith("pos:") for k in keys),
                "scale": scale, "source": name}
    value = None
    if boundary == "native_client_request" and phase == "decode":
        value = entry.get("reported_tpot_ms")
    elif boundary == "native_client_request" and phase == "prefill":
        value = entry.get("reported_ttft_ms")
    if value is None:
        for name in ("observed_ms", "boundary_ms", "value_ms", "mean_ms"):
            if entry.get(name) is not None:
                value = entry.get(name)
                break
    if value is None:
        return None
    return {"keys": ["aggregate"], "values": [_cell(value) * scale],
            "basis": _basis(entry), "keyed": False, "scale": scale, "source": "scalar"}


def observed_sample_table(observation: Mapping[str, Any] | None,
                          boundary: str) -> dict[str, Any]:
    """Resolve one typed observation boundary to a keyed table.

    Returns ``{"status": "absent"|"measured", ...}``.  Additive class mass and
    family aggregates are never promoted to an elapsed sample.
    """
    observation = observation or {}
    requested = str(boundary or "")
    if requested not in _SUPPORTED_BOUNDARIES:
        return {"status": "absent", "boundary": requested,
                "reason": "unsupported_prediction_boundary_scope"}
    expected_basis = ""
    if requested in _BOUNDARY_ALIASES:
        requested, expected_basis = _BOUNDARY_ALIASES[requested]
    entry = (observation.get("measurements") or {}).get(requested)
    if not isinstance(entry, Mapping) or entry.get("status") not in _MEASURED:
        return {"status": "absent", "boundary": requested,
                "reason": "observation boundary absent or unmeasured"}
    phase = _phase_of(observation, entry)
    table = _entry_table(entry, phase=phase, boundary=requested)
    if table is None:
        return {"status": "absent", "boundary": requested,
                "reason": "observation boundary has no sample values"}
    table.update({"status": "measured", "boundary": requested,
                  "phase": phase, "expected_basis": expected_basis,
                  "truncated": bool(entry.get("truncated") or entry.get("samples_truncated"))})
    count = entry.get("window_count")
    if count is not None and _number(count) is not None and int(_number(count)) != len(table["keys"]):
        table["truncated"] = True
    return table


_POPULATION_PRIORITY = ("native_calls", "per_forward_window", "native_client_request")


def _boundary_class(boundary: str, table: Mapping[str, Any] | None = None) -> str:
    if boundary == "native_calls":
        return "standalone_native_call_elapsed"
    if boundary == "native_client_request":
        return "request_l4"
    if boundary == "per_forward_window":
        table = table or {}
        if (_is_additive(str(table.get("basis") or ""))
                or table.get("expected_basis") == "additive"):
            return "additive_independent_op_span"
        return "inclusive_forward_elapsed"
    return "unknown_prediction_scope"


def _population_from_table(table: Mapping[str, Any]) -> dict[str, Any]:
    keys = list(table.get("keys") or ())
    return {
        "status": "measured",
        "boundary": str(table.get("boundary") or ""),
        "keys": keys,
        "values": list(table.get("values") or ()),
        "denominator": len(keys),
        "basis": str(table.get("basis") or ""),
        "source": str(table.get("source") or ""),
        "phase": str(table.get("phase") or ""),
        "keyed": bool(table.get("keyed")),
        "boundary_class": _boundary_class(str(table.get("boundary") or ""), table),
        "table": dict(table),
    }


def _population_provenance(observation: Mapping[str, Any],
                           entry: Mapping[str, Any] | None,
                           boundary: str) -> dict[str, Any]:
    """Observation-side witnesses only; never infers a missing source/rank."""
    bag: dict[str, dict[str, list[str]]] = {}
    _identity_walk(bag, observation, "observation", observation=True)
    if isinstance(entry, Mapping):
        _identity_walk(bag, entry, "observation.boundary", observation=True, entry_level=True)
    provenance: dict[str, Any] = {"boundary": boundary, "witness_conflicts": []}
    for field in ("source_sha256", "capture_id", "rank", "device", "hardware", "model"):
        values = _witness_values(bag, field)
        if len(values) > 1:
            provenance["witness_conflicts"].append(field)
        provenance[field] = values[0] if values else ""
        provenance[f"{field}_status"] = ("conflict" if len(values) > 1 else
                                         "present" if values else "absent")
    native_phase = _witness_values(bag, "phase_native")
    enrolled_phase = _witness_values(bag, "phase_enrolled")
    if len(native_phase) > 1 or len(enrolled_phase) > 1:
        provenance["witness_conflicts"].append("phase")
    provenance["phase_native"] = native_phase[0] if native_phase else ""
    provenance["phase_enrolled"] = enrolled_phase[0] if enrolled_phase else ""
    provenance["phase"] = provenance["phase_native"] or provenance["phase_enrolled"]
    provenance["phase_status"] = ("conflict"
                                  if "phase" in provenance["witness_conflicts"]
                                  else "present" if provenance["phase"] else "absent")
    provenance["phase_conflict"] = bool(provenance["phase_native"]
                                        and provenance["phase_enrolled"]
                                        and provenance["phase_native"].lower()
                                        != provenance["phase_enrolled"].lower())
    return provenance


def _usable_population_table(name: str, table: Mapping[str, Any]) -> bool:
    if table.get("status") != "measured":
        return False
    base = _BOUNDARY_ALIASES.get(name, (name, ""))[0]
    if base == "per_forward_window" and table.get("source") == "scalar":
        return False
    if base == "native_calls" and table.get("source") != "records":
        return False
    return True


def observed_boundary_population(observation: Mapping[str, Any] | None,
                                 boundary: str | None = None) -> dict[str, Any]:
    """Resolve the original observation population before prediction checks.

    Priority is exact native calls, then measured forward windows, then a
    measured producer request boundary.  Family/scope aggregates and recorded
    forward aggregates are never promoted to window populations.
    """
    observation = observation or {}
    requested = str(boundary) if isinstance(boundary, str) and boundary else ""
    requested_table = observed_sample_table(observation, requested) if requested else {"status": "absent"}
    primary = None
    for name in _POPULATION_PRIORITY:
        table = observed_sample_table(observation, name)
        if _usable_population_table(name, table):
            primary = _population_from_table(table)
            break
    if requested and _usable_population_table(requested, requested_table):
        population = _population_from_table(requested_table)
        population["requested_boundary"] = requested
        population["scope_mismatch"] = False
    elif primary is not None:
        population = primary
        population["requested_boundary"] = requested
        population["scope_mismatch"] = bool(requested)
    else:
        reason = "no measured original observation population"
        if requested and requested_table.get("status") == "measured":
            reason = ("per_forward_boundary_has_no_sample_series"
                      if requested.startswith("per_forward")
                      else f"{requested}_boundary_has_no_sample_series")
        return {"status": "absent", "boundary": None, "keys": [], "values": [],
                "denominator": None, "basis": "", "source": "", "phase": "",
                "keyed": False, "table": {}, "requested_boundary": requested,
                "scope_mismatch": False, "reason": reason}
    entry = (observation.get("measurements") or {}).get(population["boundary"])
    population["entry"] = entry
    population["provenance"] = _population_provenance(
        observation, entry if isinstance(entry, Mapping) else None, population["boundary"])
    return population


def _population_extra(population: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "population_boundary": population.get("boundary"),
        "population_status": population.get("status"),
        "population_denominator": population.get("denominator"),
        "population_basis": population.get("basis"),
        "population_source": population.get("source"),
        "population_provenance": population.get("provenance"),
        "requested_boundary": population.get("requested_boundary"),
        "boundary_class": population.get("boundary_class") or "unknown_prediction_scope",
        "requested_boundary_class": (
            _boundary_class(str(population.get("boundary") or ""), population.get("table"))
            if str(population.get("requested_boundary") or "") in _SUPPORTED_BOUNDARIES
            else "unknown_prediction_scope"),
    }


def _prediction_table(prediction: Mapping[str, Any], *, phase: str = "",
                      boundary: str = "") -> dict[str, Any] | None:
    """Prediction sample table; order is irrelevant for keyed records."""
    keyed = prediction.get("boundary_samples")
    if isinstance(keyed, Mapping):
        pairs = []
        for key, value in keyed.items():
            if isinstance(value, Mapping):
                pairs.append((str(key), _forecast_record_value(value, phase, boundary)))
            else:
                pairs.append((str(key), value))
        return {"kind": "keyed", "pairs": pairs}
    if (isinstance(keyed, Sequence) and not isinstance(keyed, (str, bytes)) and keyed
            and not isinstance(keyed[0], Mapping)):
        return {"kind": "positional", "values": [_cell(value) for value in keyed]}
    if isinstance(keyed, Sequence) and not isinstance(keyed, (str, bytes)) and keyed:
        if isinstance(keyed[0], Mapping):
            pairs = [(_record_key(row, index, "prediction") if isinstance(row, Mapping)
                      else f"prediction:{index}",
                      _forecast_record_value(row, phase, boundary) if isinstance(row, Mapping)
                      else _cell(row))
                     for index, row in enumerate(keyed)]
            return {"kind": "keyed", "pairs": pairs}
    for name in ("boundary_samples_ms", "samples_ms", "per_forward_ms", "predicted_samples_ms"):
        raw = prediction.get(name)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and raw:
            return {"kind": "positional", "values": [_cell(value) for value in raw]}
    for name in ("boundary_ms", "predicted_boundary_ms"):
        if prediction.get(name) is not None:
            return {"kind": "scalar", "value": _cell(prediction[name])}
    return None


def _text(*values: Any) -> str:
    """First present identifier as text; rank/device 0 is a real identity."""
    for value in values:
        if value is not None and str(value) != "":
            return str(value)
    return ""


_SOURCE_SHA_FIELDS = ("source_sha256", "raw_sha256", "recorded_source_sha256",
                      "reported_source_sha256")
_IDENTITY_WITNESS_FIELDS = ("source_sha256", "capture_id", "phase_native", "phase_enrolled",
                            "rank", "device", "workload", "hardware", "model")


def _witness(bag: dict[str, dict[str, list[str]]], field: str, value: Any,
             where: str) -> None:
    text = _text(value)
    if not text:
        return
    key = text.lower() if field == "source_sha256" else text
    bag.setdefault(field, {}).setdefault(key, []).append(where)


def _identity_walk(bag: dict[str, dict[str, list[str]]], obj: Any, tag: str, *,
                   observation: bool, entry_level: bool = False, depth: int = 0) -> None:
    """Collect identity witnesses, keeping native phase separate from enrolled phase."""
    if not isinstance(obj, Mapping) or depth > 2:
        return
    for name in _SOURCE_SHA_FIELDS:
        _witness(bag, "source_sha256", obj.get(name), f"{tag}.{name}")
    for nested_name in ("source", "source_fingerprint"):
        nested = obj.get(nested_name)
        if isinstance(nested, Mapping):
            _witness(bag, "source_sha256", nested.get("sha256"),
                     f"{tag}.{nested_name}.sha256")
    _witness(bag, "capture_id", obj.get("capture_id"), f"{tag}.capture_id")
    capture = obj.get("capture")
    if isinstance(capture, Mapping):
        _witness(bag, "capture_id", capture.get("capture_id"), f"{tag}.capture.capture_id")
        _witness(bag, "phase_enrolled", capture.get("phase"), f"{tag}.capture.phase")
        _witness(bag, "phase_enrolled", capture.get("observed_phase"),
                 f"{tag}.capture.observed_phase")
        _witness(bag, "hardware", capture.get("hardware_tier"),
                 f"{tag}.capture.hardware_tier")
        _witness(bag, "model", capture.get("model_case"), f"{tag}.capture.model_case")
    identity = obj.get("identity")
    if isinstance(identity, Mapping):
        _witness(bag, "rank", identity.get("rank_id"), f"{tag}.identity.rank_id")
        _witness(bag, "rank", identity.get("rank"), f"{tag}.identity.rank")
        _witness(bag, "device", identity.get("device_id"), f"{tag}.identity.device_id")
        _witness(bag, "hardware", identity.get("hardware_tier"),
                 f"{tag}.identity.hardware_tier")
    if observation and not entry_level:
        _witness(bag, "phase_enrolled", obj.get("phase"), f"{tag}.phase")
        _witness(bag, "phase_enrolled", obj.get("observed_phase"), f"{tag}.observed_phase")
    else:
        for name in ("native_phase", "phase", "prediction_phase"):
            _witness(bag, "phase_native", obj.get(name), f"{tag}.{name}")
    _witness(bag, "phase_enrolled", obj.get("row_phase"), f"{tag}.row_phase")
    _witness(bag, "rank", obj.get("rank_id"), f"{tag}.rank_id")
    _witness(bag, "rank", obj.get("rank"), f"{tag}.rank")
    for name in ("device_id", "profiler_device_id"):
        _witness(bag, "device", obj.get(name), f"{tag}.{name}")
    for name in ("device_ids", "profiler_device_ids"):
        raw = obj.get(name)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            for item in raw:
                _witness(bag, "device", item, f"{tag}.{name}[]")
    _witness(bag, "workload", obj.get("workload_id"), f"{tag}.workload_id")
    if isinstance(obj.get("workload"), str):
        _witness(bag, "workload", obj.get("workload"), f"{tag}.workload")
    _witness(bag, "hardware", obj.get("hardware_tier"), f"{tag}.hardware_tier")
    _witness(bag, "model", obj.get("model_case"), f"{tag}.model_case")
    for name in ("samples", "calls", "frame_identifiers", "boundary_samples",
                 "operator_group_samples", "predicted_operator_groups"):
        raw = obj.get(name)
        if isinstance(raw, Mapping):
            raw = list(raw.values())
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            for index, child in enumerate(raw):
                if isinstance(child, Mapping):
                    _identity_walk(bag, child, f"{tag}.{name}[{index}]",
                                   observation=observation, entry_level=True, depth=depth + 1)


def _witness_values(bag: Mapping[str, Mapping[str, Any]], field: str) -> list[str]:
    return sorted(bag.get(field) or {})


def _witness_basis(bag: Mapping[str, Mapping[str, Any]], field: str) -> str:
    where = [item for values in (bag.get(field) or {}).values() for item in values]
    boundary = any(".boundary" in item for item in where)
    top = any(".boundary" not in item for item in where)
    return ("boundary+top" if boundary and top else "boundary" if boundary
            else "top_level" if top else "absent")


def _identity_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "identity": dict(report),
        "identity_status": report.get("status") or "absent",
        "identity_verified": bool(report.get("verified")),
        "source_identity_status": str((report.get("source_sha256") or {}).get("status") or "absent"),
        "capture_identity_status": str((report.get("capture_id") or {}).get("status") or "absent"),
        "phase_identity_status": str((report.get("phase") or {}).get("status") or "absent"),
        "rank_identity_status": str((report.get("rank") or {}).get("status") or "absent"),
        "device_identity_status": str((report.get("device") or {}).get("status") or "absent"),
        "workload_identity_status": str((report.get("workload") or {}).get("status") or "absent"),
    }


def _identity_check(observation: Mapping[str, Any], prediction: Mapping[str, Any],
                    entry: Mapping[str, Any] | None = None,
                    boundary: str = "") -> tuple[str, str, dict[str, Any]]:
    """Enforce same-boundary identity witnesses before any numeric comparison.

    Source/workload/capture/rank/phase witnesses are collected from the exact
    measurement entry, its nested native calls/samples, and the top-level
    observation/prediction.  Nested-vs-flat contradictions are rejected.  A
    known source digest requires the prediction to witness the same digest;
    a missing digest is disclosed, never treated as proof.
    """
    obs: dict[str, dict[str, list[str]]] = {}
    pred: dict[str, dict[str, list[str]]] = {}
    _identity_walk(obs, observation, "observation", observation=True)
    if isinstance(entry, Mapping):
        _identity_walk(obs, entry, "observation.boundary", observation=True, entry_level=True)
    _identity_walk(pred, prediction, "prediction", observation=False)
    report: dict[str, Any] = {
        "status": "absent", "verified": False,
        "witness_conflicts": [], "phase_conflict": False,
    }
    for role, bag in (("observation", obs), ("prediction", pred)):
        for field in ("source_sha256", "capture_id", "phase_native", "rank", "device",
                      "workload", "hardware", "model"):
            values = _witness_values(bag, field)
            if len(values) > 1:
                report["witness_conflicts"].append(f"{role}.{field}")
                report[field.replace("_native", "")] = {
                    "status": "witness_conflict", "values": values,
                    "witnesses": dict(bag.get(field) or {}),
                }
                return "invalid", f"{role}_{field}_witness_conflict", report

    def one(bag: Mapping[str, Mapping[str, Any]], field: str) -> str:
        values = _witness_values(bag, field)
        return values[0] if values else ""

    obs_source, pred_source = one(obs, "source_sha256"), one(pred, "source_sha256")
    obs_capture, pred_capture = one(obs, "capture_id"), one(pred, "capture_id")
    obs_native_phase = one(obs, "phase_native")
    obs_enrolled_phase = one(obs, "phase_enrolled")
    obs_phase = obs_native_phase or obs_enrolled_phase
    pred_phase = one(pred, "phase_native")
    report["phase_conflict"] = bool(obs_native_phase and obs_enrolled_phase
                                    and obs_native_phase.lower() != obs_enrolled_phase.lower())
    report["phase_enrolled"] = obs_enrolled_phase
    source_verified = False
    if obs_source and pred_source:
        if obs_source != pred_source:
            report["source_sha256"] = {"status": "mismatch", "observation": obs_source,
                                       "prediction": pred_source}
            return "invalid", "source_sha256_mismatch", report
        source_verified = True
        report["source_sha256"] = {"status": "matched", "observation": obs_source,
                                   "prediction": pred_source}
    elif obs_source and not pred_source:
        report["source_sha256"] = {"status": "prediction_absent",
                                   "observation": obs_source, "prediction": ""}
        reason = ("native_calls_source_sha256_absent" if boundary == "native_calls"
                  else "prediction_source_identity_absent")
        return "uncovered", reason, report
    elif pred_source and not obs_source:
        report["source_sha256"] = {"status": "observation_absent",
                                   "observation": "", "prediction": pred_source}
        return "uncovered", "observation_source_identity_absent", report
    else:
        report["source_sha256"] = {"status": "absent", "observation": "", "prediction": ""}

    # Capture and phase are required when the boundary carries a source digest.
    for name, obs_value, pred_value in (("capture_id", obs_capture, pred_capture),
                                        ("phase", obs_phase, pred_phase)):
        if obs_value and pred_value:
            if obs_value.lower() != pred_value.lower():
                report[name] = {"status": "mismatch", "observation": obs_value,
                                "prediction": pred_value}
                return "invalid", f"{name}_mismatch", report
            report[name] = {"status": "matched", "observation": obs_value,
                            "prediction": pred_value}
        elif source_verified and obs_value and not pred_value:
            report[name] = {"status": "prediction_absent", "observation": obs_value,
                            "prediction": ""}
            return "uncovered", f"prediction_{name}_identity_absent", report
        elif source_verified and pred_value and not obs_value:
            report[name] = {"status": "observation_absent", "observation": "",
                            "prediction": pred_value}
            return "uncovered", f"observation_{name}_identity_absent", report
        else:
            report[name] = {"status": "absent", "observation": obs_value or "",
                            "prediction": pred_value or ""}
    if report.get("phase_conflict"):
        report["phase"]["native"] = obs_native_phase
        report["phase"]["enrolled"] = obs_enrolled_phase

    for name in ("rank", "device", "workload"):
        obs_value, pred_value = one(obs, name), one(pred, name)
        if obs_value and pred_value:
            if obs_value != pred_value:
                report[name] = {"status": "mismatch", "observation": obs_value,
                                "prediction": pred_value}
                return "invalid", f"{name}_mismatch", report
            report[name] = {"status": "matched", "observation": obs_value,
                            "prediction": pred_value}
        elif obs_value:
            report[name] = {"status": "prediction_absent", "observation": obs_value,
                            "prediction": ""}
        elif pred_value:
            report[name] = {"status": "observation_absent", "observation": "",
                            "prediction": pred_value}
        else:
            report[name] = {"status": "absent", "observation": "", "prediction": ""}

    obs_hardware, pred_hardware = one(obs, "hardware"), one(pred, "hardware")
    if obs_hardware and pred_hardware and obs_hardware.upper() != pred_hardware.upper():
        report["hardware"] = {"status": "mismatch", "observation": obs_hardware,
                              "prediction": pred_hardware}
        return "invalid", "hardware_mismatch", report
    report["hardware"] = {"status": "matched" if obs_hardware and pred_hardware else
                          ("observation_only" if obs_hardware else "absent"),
                          "observation": obs_hardware, "prediction": pred_hardware}
    if obs_capture and not obs_hardware:
        return "uncovered", "hardware_provenance_absent", report
    obs_model, pred_model = one(obs, "model"), one(pred, "model")
    if obs_model and pred_model and obs_model != pred_model:
        report["model"] = {"status": "mismatch", "observation": obs_model,
                           "prediction": pred_model}
        return "invalid", "model_mismatch", report
    report["model"] = {"status": "matched" if obs_model and pred_model else "absent",
                       "observation": obs_model, "prediction": pred_model}
    for name, field in (("source_sha256", "source_sha256"),
                        ("capture_id", "capture_id"), ("phase", "phase_native")):
        if name in report:
            report[name]["observation_basis"] = _witness_basis(obs, field)
    if "phase" in report and report["phase"].get("observation_basis") == "absent":
        report["phase"]["observation_basis"] = _witness_basis(obs, "phase_enrolled")
    report["verified"] = bool(source_verified
                              and report["capture_id"]["status"] == "matched"
                              and report["phase"]["status"] == "matched")
    report["status"] = ("verified" if report["verified"] else
                        "partial" if source_verified or obs_capture or obs_phase else "absent")
    return "", "", report


def _error_counts(signed_errors: Mapping[str, float]) -> dict[str, Any]:
    over = sorted(key for key, value in signed_errors.items() if abs(value) > 0.10)
    return {"n_pairs": len(signed_errors),
            "count_over_10pct": len(over),
            "n_within_10pct": len(signed_errors) - len(over),
            "per_key_errors": dict(signed_errors),
            "over_10pct_keys": over}


def score_boundary(prediction: Mapping[str, Any] | None,
                   observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Compare one declared boundary, sample by sample and key by key.

    A scalar prediction is valid only for a one-sample aggregate observation.
    When the observation carries a per-request/per-forward series, the
    prediction must carry the same keyed population; a producer mean/median
    can never hide an individual sample.  Source/capture/phase identity is
    read from this exact boundary entry (and its nested samples), never from
    an unrelated top-level field.
    """
    prediction = prediction or {}
    observation = observation or {}
    declared = prediction.get("prediction_boundary")
    declared_boundary = declared if isinstance(declared, str) else ""
    population = observed_boundary_population(observation, declared_boundary or None)
    pop_extra = _population_extra(population)
    status = str(prediction.get("status") or "")
    population_keys = list(population.get("keys") or ())
    population_label = (str(population.get("boundary") or "")
                        or declared_boundary or "model_step_ms_undeclared")
    if status not in _PREDICTION_OK or prediction.get("ok") is False:
        return _blank("prediction_status_not_measured", population_label,
                      extra={"denominator": population.get("denominator"),
                             "matched": 0, "n_pairs": 0, "n_groups": 1,
                             "n_samples": 0, "missing_keys": population_keys,
                             **_error_counts({}), **pop_extra})
    if (not isinstance(declared, str) or not declared.strip()
            or declared in _NOT_A_SAMPLE):
        return _blank("prediction_boundary_undeclared" if not declared
                      else "boundary_is_not_a_comparable_sample",
                      population_label,
                      extra={"denominator": population.get("denominator"),
                             "matched": 0, "n_pairs": 0, "n_groups": 1,
                             "n_samples": 0, "missing_keys": population_keys,
                             **_error_counts({}), **pop_extra})
    if population.get("status") != "measured":
        reason = str(population.get("reason") or "observation_boundary_absent")
        if reason == "no measured original observation population":
            reason = "observation_boundary_absent"
        return _blank(reason, declared_boundary,
                      extra={"denominator": None, "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "n_samples": 0, "missing_keys": [],
                             **_error_counts({}), **pop_extra})
    if declared_boundary not in _SUPPORTED_BOUNDARIES:
        return _blank("unsupported_prediction_boundary_scope", population_label,
                      extra={"denominator": population.get("denominator"),
                             "matched": 0, "n_pairs": 0, "n_groups": 1,
                             "n_samples": 0, "missing_keys": population_keys,
                             **_error_counts({}), **pop_extra,
                             "boundary_class": "unknown_prediction_scope",
                             "requested_boundary_class": "unknown_prediction_scope"})
    if population.get("scope_mismatch"):
        return _blank("prediction_boundary_scope_mismatch", population_label,
                      extra={"denominator": population.get("denominator"),
                             "matched": 0, "n_pairs": 0, "n_groups": 1,
                             "n_samples": 0, "missing_keys": population_keys,
                             **_error_counts({}), **pop_extra})
    boundary = declared_boundary
    table = population["table"]
    entry = (observation.get("measurements") or {}).get(table.get("boundary") or boundary)
    reason, identity_reason, identity = _identity_check(
        observation, prediction, entry, str(table.get("boundary") or boundary))
    ident = _identity_summary(identity)
    identity_hold: str = ""
    if reason == "invalid":
        return _blank(identity_reason, boundary, reason,
                      extra={"denominator": len(table["keys"]), "matched": 0,
                             "n_pairs": 0, "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    if reason == "uncovered":
        # Absence is disclosed and cannot pass, but still pair all keys so C gets
        # the true numerator/counts. Contradictions above already returned early.
        identity_hold = identity_reason
    if table.get("truncated"):
        return _blank("observation_samples_truncated", boundary, "invalid",
                      extra={"denominator": len(table["keys"]), "matched": 0,
                             "n_pairs": 0, "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    if boundary.startswith("per_forward") and table.get("source") == "scalar":
        return _blank("per_forward_boundary_has_no_sample_series", boundary,
                      extra={"denominator": 1, "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    obs_keys, obs_values = list(table["keys"]), list(table["values"])
    duplicates = sorted(key for key, count in Counter(obs_keys).items() if count > 1)
    if duplicates:
        return _blank("duplicate_observation_sample_key", boundary, "invalid",
                      extra={"denominator": len(obs_keys), "duplicate_keys": duplicates,
                             "matched": 0, "n_pairs": 0, "n_groups": 1,
                             "missing_keys": [], **_error_counts({}), **ident, **pop_extra})
    additive_obs = _is_additive(str(table.get("basis") or ""))
    expected_basis = table.get("expected_basis") or ""
    pred_basis = str(prediction.get("boundary_basis") or prediction.get("prediction_basis") or "").lower()
    if expected_basis == "additive" and not additive_obs:
        return _blank("declared_additive_boundary_is_not_additive", boundary,
                      extra={"denominator": len(obs_keys), "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    if expected_basis == "elapsed" and additive_obs:
        return _blank("declared_elapsed_boundary_is_additive", boundary,
                      extra={"denominator": len(obs_keys), "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    if additive_obs and "additive" not in pred_basis:
        return _blank("observation_basis_additive_class_mass_not_elapsed", boundary,
                      extra={"denominator": len(obs_keys), "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    if not additive_obs and _is_additive(pred_basis):
        return _blank("prediction_basis_additive_but_observation_is_elapsed", boundary,
                      extra={"denominator": len(obs_keys), "matched": 0, "n_pairs": 0,
                             "n_groups": 1, "missing_keys": [],
                             **_error_counts({}), **ident, **pop_extra})
    pred_table = _prediction_table(prediction, phase=str(table.get("phase") or ""),
                                   boundary=boundary)
    if pred_table is None:
        reason = ("prediction_value_not_on_boundary" if prediction.get("predicted_step_ms") is not None
                  else "prediction_samples_absent")
        return _blank(reason, boundary, extra={"denominator": len(obs_keys),
                                               "matched": 0, "n_pairs": 0, "n_groups": 1,
                                               "missing_keys": obs_keys,
                                               **_error_counts({}), **ident, **pop_extra})
    signed_errors: dict[str, float] = {}
    worst_key, worst = "", float("nan")
    missing_keys: list[str] = []
    unmatched_keys: list[str] = []
    if pred_table["kind"] == "scalar":
        if len(obs_keys) != 1:
            return _blank("aggregate_hides_per_sample_series", boundary, "invalid",
                          extra={"denominator": len(obs_keys), "n_samples": len(obs_keys),
                                 "matched": 0, "n_pairs": 0, "n_groups": 1,
                                 "missing_keys": [], **_error_counts({}), **ident, **pop_extra})
        pairs = [(obs_keys[0], pred_table["value"], obs_values[0])]
    elif pred_table["kind"] == "positional":
        # Positional values are only comparable when the observation itself is
        # positional.  A keyed observation requires shared keyed records; order
        # alone is not independent identity proof.
        if table.get("keyed"):
            return _blank("prediction_samples_unkeyed_for_keyed_observation", boundary,
                          "invalid", extra={"denominator": len(obs_keys),
                                            "matched": 0, "n_pairs": 0, "n_groups": 1,
                                            "missing_keys": obs_keys,
                                            **_error_counts({}), **ident, **pop_extra})
        if len(pred_table["values"]) != len(obs_keys):
            return _blank("sample_population_length_mismatch", boundary, "invalid",
                          extra={"denominator": len(obs_keys),
                                 "prediction_samples": len(pred_table["values"]),
                                 "matched": 0, "n_pairs": 0, "n_groups": 1,
                                 "missing_keys": [], **_error_counts({}), **ident, **pop_extra})
        pairs = [(key, value, observed) for key, value, observed
                 in zip(obs_keys, pred_table["values"], obs_values)]
    else:
        pred_pairs = pred_table["pairs"]
        pred_keys = [str(key) for key, _ in pred_pairs]
        pred_dupes = sorted(key for key, count in Counter(pred_keys).items() if count > 1)
        if pred_dupes:
            return _blank("duplicate_prediction_sample_key", boundary, "invalid",
                          extra={"denominator": len(obs_keys), "duplicate_keys": pred_dupes,
                                 "matched": 0, "n_pairs": 0, "n_groups": 1,
                                 "missing_keys": [], **_error_counts({}), **ident, **pop_extra})
        pred_map = {str(key): value for key, value in pred_pairs}
        missing_keys = [key for key in obs_keys if key not in pred_map]
        unmatched_keys = [key for key in pred_keys if key not in set(obs_keys)]
        pairs = [(key, pred_map[key], observed) for key, observed in zip(obs_keys, obs_values)
                 if key in pred_map]
    unmeasured = []
    for key, predicted, observed in pairs:
        if observed is None:
            unmeasured.append(key)
            continue
        reason, error = _pair_error(predicted, observed)
        if reason:
            counts = _error_counts(signed_errors)
            return _blank(reason, boundary, "invalid", error,
                          extra={"denominator": len(obs_keys), "invalid_keys": [key],
                                 **counts, **ident, **pop_extra})
        errors_value = (float(predicted) - float(observed)) / abs(float(observed))
        signed_errors[key] = errors_value
        if len(signed_errors) == 1 or error > worst:
            worst, worst_key = error, key
    counts = _error_counts(signed_errors)
    if unmeasured:
        return _blank("observation_sample_unmeasured", boundary, "invalid",
                      extra={"denominator": len(obs_keys), "missing_keys": unmeasured,
                             **counts, **ident, **pop_extra})
    if missing_keys or unmatched_keys:
        return _blank("sample_key_population_mismatch", boundary, "invalid", worst,
                      extra={"denominator": len(obs_keys), "matched": counts["n_pairs"],
                             "n_samples": counts["n_pairs"], "n_groups": 1,
                             "missing_keys": missing_keys, "unmatched_keys": unmatched_keys,
                             "max_signed_error": signed_errors.get(worst_key),
                             **counts, **ident, **pop_extra})
    if identity_hold:
        return _blank(identity_hold, boundary, "uncovered", worst,
                      extra={"denominator": len(obs_keys), "matched": counts["n_pairs"],
                             "n_samples": counts["n_pairs"], "n_groups": 1,
                             "missing_keys": [], "unmatched_keys": [],
                             "max_signed_error": signed_errors.get(worst_key),
                             **counts, **ident, **pop_extra})
    return {"comparison": "compared", "reason": "exact_keyed_samples",
            "boundary": boundary,
            "passed_10pct": (counts["n_pairs"] == len(obs_keys)
                             and counts["n_pairs"] > 0
                             and counts["count_over_10pct"] == 0),
            "sample": worst, "n_samples": counts["n_pairs"],
            "denominator": len(obs_keys), "matched": counts["n_pairs"],
            "worst_key": worst_key, "missing_keys": [], "unmatched_keys": [],
            "duplicate_keys": [], "invalid_keys": [], "basis": table.get("basis") or "",
            "alignment": ("keyed" if pred_table["kind"] == "keyed" else
                          "positional" if pred_table["kind"] == "positional" else "aggregate"),
            "n_groups": 1,
            "max_signed_error": signed_errors.get(worst_key),
            **counts, **ident, **pop_extra}


def _group_records(raw: Any, *, from_prediction: bool) -> list[tuple[str, Mapping[str, Any]]]:
    records: list[tuple[str, Mapping[str, Any]]] = []
    if isinstance(raw, Mapping):
        if "key" in raw and ("boundary_ms" in raw or "value_ms" in raw or "samples_ms" in raw):
            return [(str(raw.get("key") or ""), raw)]
        for key, value in raw.items():
            if str(key) in _META_GROUP_KEYS:
                continue
            if isinstance(value, Mapping):
                records.append((str(key), value))
            elif from_prediction:
                records.append((str(key), {"boundary_ms": value}))
            else:
                records.append((str(key), {"observed_ms": value}))
        return records
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
        for index, value in enumerate(raw):
            if not isinstance(value, Mapping):
                continue
            key = str(value.get("key") or "")
            if not key and from_prediction:
                key = operator_key(str(value.get("op_type") or value.get("op") or ""),
                                   str(value.get("engine") or value.get("core") or ""))
            records.append((key, value))
    return records


def observed_operator_table(observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Observed op x native-engine population.

    Only exact op x engine evidence is promoted.  A family/scope aggregate
    alone is an absent population, never one group.
    """
    observation = observation or {}
    measurements = observation.get("measurements") or {}
    raw = measurements.get("operator_groups")
    if isinstance(raw, Mapping):
        status = str(raw.get("status") or "measured")
        if status not in _MEASURED:
            return {"status": "absent", "reason": "operator_groups_not_measured"}
        groups = raw.get("groups") if isinstance(raw.get("groups"), (Mapping, list, tuple)) else raw
        records = _group_records(groups, from_prediction=False)
        basis = str(raw.get("basis") or raw.get("samples_basis") or "").lower()
        if records:
            return {"status": "measured", "records": records, "basis": basis,
                    "entry": raw, "source": "measurements.operator_groups"}
    for scope in ("capture_op_statistic_aggregate", "whole_capture_native_kernel_rows"):
        entry = measurements.get(scope)
        if not isinstance(entry, Mapping) or entry.get("status") not in _MEASURED:
            continue
        by_engine = entry.get("by_op_engine")
        if not isinstance(by_engine, Mapping) or not by_engine:
            by_engine = observation.get("by_op_engine")
        if not isinstance(by_engine, Mapping) or not by_engine:
            by_engine = (observation.get("kernel_summary") or {}).get("by_op_engine")
        if not isinstance(by_engine, Mapping) or not by_engine:
            continue
        records = []
        for raw_key, row in by_engine.items():
            if not isinstance(row, Mapping):
                continue
            if any(isinstance(value, Mapping) for value in row.values()):
                for engine, leaf in row.items():
                    if not isinstance(leaf, Mapping):
                        continue
                    total_us = _number(leaf.get("total_us"))
                    records.append((operator_key(str(raw_key), str(engine)),
                                    {"status": "measured", "observed_ms":
                                     None if total_us is None else total_us / 1000.0,
                                     "op_type": str(raw_key), "engine": str(engine),
                                     "basis": "additive_op_engine_total_us"}))
                continue
            op = str(row.get("op_type") or str(raw_key).split("\x1f", 1)[0])
            engine = str(row.get("core") or (str(raw_key).split("\x1f", 1)[1]
                                             if "\x1f" in str(raw_key) else "UNKNOWN"))
            key = str(raw_key) if "\x1f" in str(raw_key) else operator_key(op, engine)
            total_us = _number(row.get("total_us"))
            records.append((key, {"status": "measured", "observed_ms":
                                  None if total_us is None else total_us / 1000.0,
                                  "op_type": op, "engine": engine,
                                  "basis": "additive_op_engine_total_us"}))
        if records:
            return {"status": "measured", "records": records,
                    "basis": "additive_op_engine_total_us", "entry": entry, "source": scope}
    return {"status": "absent", "reason": "no exact op x engine observation"}


def _prediction_operator_table(prediction: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    raw = prediction.get("operator_group_samples")
    if raw is None:
        raw = prediction.get("predicted_operator_groups")
    if raw is not None:
        return _group_records(raw, from_prediction=True)
    nested = prediction.get("predicted_by_op_engine_ms")
    if isinstance(nested, Mapping):
        records = []
        for op, engines in nested.items():
            if isinstance(engines, Mapping):
                for engine, value in engines.items():
                    records.append((operator_key(str(op), str(engine)),
                                    {"boundary_ms": value}))
            else:
                records.append((operator_key(str(op), "UNKNOWN"), {"boundary_ms": engines}))
        return records
    return []


def _group_pair(observed: Mapping[str, Any], predicted: Mapping[str, Any]) -> tuple[str, list[tuple[Any, Any, Any]]]:
    """Pair one group's scalar or sample series by exact key."""
    obs_series = _entry_table(observed, phase="", boundary="operator_group")
    pred_series = _prediction_table(predicted)
    if obs_series is not None and obs_series.get("source") != "scalar":
        if pred_series is None or pred_series.get("kind") == "scalar":
            return "aggregate_hides_per_forward_samples", []
        obs_keys = list(obs_series["keys"])
        obs_dupes = sorted(key for key, count in Counter(obs_keys).items() if count > 1)
        if obs_dupes:
            return "duplicate_observation_sample_key", []
        if pred_series["kind"] == "positional":
            if len(pred_series["values"]) != len(obs_keys):
                return "sample_population_length_mismatch", []
            return "", [(key, value, observed_value) for key, value, observed_value
                        in zip(obs_keys, pred_series["values"], obs_series["values"])]
        pred_pairs = pred_series["pairs"]
        pred_keys = [str(key) for key, _ in pred_pairs]
        if len(set(pred_keys)) != len(pred_keys):
            return "duplicate_prediction_sample_key", []
        pred_map = {str(key): value for key, value in pred_pairs}
        if set(pred_map) != set(obs_keys):
            return "sample_key_population_mismatch", []
        return "", [(key, pred_map[key], observed_value)
                    for key, observed_value in zip(obs_keys, obs_series["values"])]
    if pred_series is not None and pred_series.get("kind") in {"keyed", "positional"}:
        return "prediction_has_samples_but_observation_is_one_value", []
    observed_value = None
    for name in ("observed_ms", "total_ms", "duration_ms", "value_ms"):
        if observed.get(name) is not None:
            observed_value = observed.get(name)
            if name == "total_ms" and _number(observed.get("total_us")) is not None:
                observed_value = _number(observed.get("total_us"))
        if observed_value is not None:
            break
    predicted_value = None
    for name in ("boundary_ms", "value_ms", "predicted_ms", "total_ms"):
        if predicted.get(name) is not None:
            predicted_value = predicted.get(name)
            break
    if observed_value is None or predicted_value is None:
        return "operator_group_value_absent", []
    return "", [(None, predicted_value, observed_value)]


def score_operator_groups(prediction: Mapping[str, Any] | None,
                          observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """Score the exact observed op x native-engine population.

    The observation defines the required keys.  Missing, duplicate, extra, or
    unmeasured keys cannot pass; family aggregates are not a group.  Reordering
    keyed records yields the same score.  Identity witnesses are read from the
    operator_groups/by_op_engine object and its nested samples, not from an
    unrelated flat field.
    """
    prediction = prediction or {}
    observation = observation or {}
    status = str(prediction.get("status") or "")
    if status not in _PREDICTION_OK or prediction.get("ok") is False:
        return _blank("prediction_status_not_measured", "operator_groups",
                      extra=_error_counts({}))
    observed = observed_operator_table(observation)
    if observed.get("status") != "measured":
        return _blank("operator_groups_absent", "operator_groups",
                      extra={"denominator": 0, **_error_counts({})})
    records = observed["records"]
    keys = [key for key, _ in records]
    duplicates = sorted(key for key, count in Counter(keys).items() if count > 1)
    if duplicates:
        return _blank("duplicate_observation_group_key", "operator_groups", "invalid",
                      extra={"denominator": len(keys), "duplicate_keys": duplicates,
                             **_error_counts({})})
    reason, identity_reason, identity = _identity_check(
        observation, prediction, observed.get("entry"), "operator_groups")
    ident = _identity_summary(identity)
    identity_hold: str = ""
    if reason == "invalid":
        return _blank(identity_reason, "operator_groups", reason,
                      extra={"denominator": len(keys), **_error_counts({}), **ident})
    if reason == "uncovered":
        identity_hold = identity_reason
    predicted = _prediction_operator_table(prediction)
    if not predicted:
        return _blank("prediction_operator_groups_absent", "operator_groups",
                      extra={"denominator": len(keys), "missing_keys": keys,
                             **_error_counts({})})
    pred_keys = [key for key, _ in predicted]
    pred_dupes = sorted(key for key, count in Counter(pred_keys).items() if count > 1)
    if pred_dupes or any(not key for key in pred_keys):
        return _blank("duplicate_or_blank_operator_group", "operator_groups", "invalid",
                      extra={"denominator": len(keys), "duplicate_keys": pred_dupes,
                             **_error_counts({})})
    pred_map = dict(predicted)
    missing = [key for key in keys if key not in pred_map]
    unmatched = [key for key in pred_keys if key not in set(keys)]
    if missing or unmatched:
        return _blank("operator_group_population_mismatch", "operator_groups", "invalid",
                      extra={"denominator": len(keys), "missing_keys": missing,
                             "unmatched_keys": unmatched, **_error_counts({}), **ident})
    obs_basis = str(observed.get("basis") or "").lower()
    signed_errors: dict[str, float] = {}
    groups_paired: set[str] = set()
    worst_key, worst = "", float("nan")
    for key, observed_entry in records:
        if observed_entry.get("status") not in (None, *_MEASURED):
            return _blank("observation_group_unmeasured", "operator_groups", "invalid",
                          extra={"denominator": len(keys), "invalid_keys": [key],
                                 **_error_counts(signed_errors), **ident})
        predicted_entry = pred_map[key]
        group_status = str(predicted_entry.get("status") or "").lower()
        if group_status and group_status not in _PREDICTION_OK | _MEASURED:
            return _blank("prediction_operator_group_not_measured", "operator_groups", "invalid",
                          extra={"denominator": len(keys), "invalid_keys": [key],
                                 **_error_counts(signed_errors), **ident})
        unit_scale = _unit_scale(observed_entry)
        reason, pairs = _group_pair(observed_entry, predicted_entry)
        if reason:
            return _blank(reason, "operator_groups", "invalid", float("nan"),
                          extra={"denominator": len(keys), "invalid_keys": [key],
                                 **_error_counts(signed_errors), **ident})
        for pair_key, predicted_value, observed_value in pairs:
            if observed_value is not None:
                observed_number = _number(observed_value)
                observed_value = None if observed_number is None else observed_number * unit_scale
            pred_basis = str(predicted_entry.get("basis") or "").lower()
            if any(token in pred_basis for token in ("elapsed", "wall", "step_wall")):
                return _blank("prediction_basis_is_elapsed_but_operator_group_is_additive",
                              "operator_groups", "invalid", float("nan"),
                              extra={"denominator": len(keys), "invalid_keys": [key],
                                     **_error_counts(signed_errors), **ident})
            if _is_additive(obs_basis) and pred_basis and not _is_additive(pred_basis):
                return _blank("prediction_basis_is_elapsed_but_observation_is_additive",
                              "operator_groups", "invalid", float("nan"),
                              extra={"denominator": len(keys), "invalid_keys": [key],
                                     **_error_counts(signed_errors), **ident})
            reason, error = _pair_error(predicted_value, observed_value)
            if reason:
                return _blank(reason, "operator_groups", "invalid", error,
                              extra={"denominator": len(keys), "invalid_keys": [key],
                                     **_error_counts(signed_errors), **ident})
            error_key = (f"{key}:{pair_key}" if pair_key is not None else key)
            if error_key in signed_errors:
                error_key = f"{error_key}#{len(signed_errors)}"
            signed_errors[error_key] = ((float(predicted_value) - float(observed_value))
                                        / abs(float(observed_value)))
            groups_paired.add(key)
            if len(signed_errors) == 1 or error > worst:
                worst = error
                worst_key = error_key
    counts = _error_counts(signed_errors)
    if identity_hold:
        return _blank(identity_hold, "operator_groups", "uncovered", worst,
                      extra={"denominator": len(keys), "matched": counts["n_pairs"],
                             "n_groups": len(keys), "n_pairs": counts["n_pairs"],
                             "groups_matched": len(groups_paired),
                             "max_signed_error": signed_errors.get(worst_key),
                             **counts, **ident})
    return {"comparison": "compared", "reason": "exact_keyed_operator_groups",
            "boundary": "operator_groups",
            "passed_10pct": (counts["n_pairs"] >= len(keys)
                             and len(groups_paired) == len(keys)
                             and counts["n_pairs"] > 0
                             and counts["count_over_10pct"] == 0),
            "sample": worst, "n_groups": len(keys), "n_pairs": counts["n_pairs"],
            "denominator": len(keys), "matched": counts["n_pairs"],
            "groups_matched": len(groups_paired),
            "worst_key": worst_key, "missing_keys": [], "unmatched_keys": [],
            "duplicate_keys": [], "invalid_keys": [], "basis": obs_basis,
            "max_signed_error": signed_errors.get(worst_key),
            **counts, **ident}
