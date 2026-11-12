"""Enrolled original identities for the profiling benchmark.

The normalized count is one fleet capture plus one zero-shot cell. Forward
windows, standalone calls, and client requests stay separate integers.
Independent holdout is used only when the source relation says so.
A missing relation stays unknown. Per-window and client-ordinal group
results are diagnostics. A zero-shot cell is passed intact to
``cell_from_dict`` / ``predict_cell`` / ``compare_cell``. Null TTFT/TPOT
is outside L4 only. Applicable L1–L3 stay compared. A pending prediction
is not a TTFT pass.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import hf_fleet_source_gate as _fleet_source

SCHEMA = "mindie-profiler-all-original/2"
CANONICAL_FLEET_IDS = 6606
CANONICAL_ZERO_CELLS = 731
_UNRESOLVED_KINDS = ("source_only", "no_forecast", "conditional", "failed")
_HOLDOUT_TOKENS = ("heldout", "hold-out", "hold_out", "not_used_for_fitting")
_FORWARD_SCOPES = {"forward_body"}
_CLIENT_SCOPES = {"request_l4"}
_STANDALONE_SCOPES = {"standalone"}
_GEOMETRY_FIELDS = ("prompt_tokens", "concurrency", "max_tokens", "tp", "dp")


def _coverage_text(relation: str, role: str) -> bool:
    text = f"{relation} {role}".lower()
    return "in_sample" in text or "not_blind" in text or "regime_table_replay" in text


def stratum_name(row: Mapping[str, Any]) -> str:
    """Coverage, independent holdout, or unknown.

    Holdout requires a source relation that says the row was held out or was
    not used for fitting. An empty or unspecified role is unknown.
    """
    relation = str(row.get("evaluation_relation") or "")
    role = str(row.get("calibration_role") or "")
    if row.get("coverage_only") or row.get("target_timing_used_to_fit") is True:
        return "coverage"
    if _coverage_text(relation, role):
        return "coverage"
    lineage = f"{relation} {role}".strip().lower()
    if any(token in lineage for token in _HOLDOUT_TOKENS):
        return "independent_holdout"
    if row.get("holdout_lineage") is True:
        return "independent_holdout"
    return "unknown"


def _identity_kind(row: Mapping[str, Any]) -> str:
    explicit = str(row.get("identity_type") or "")
    if explicit in {"fleet", "zero_cell"}:
        return explicit
    if str(row.get("suite") or "") == "zero_shot" or (row.get("cell_id") and not row.get("capture_id")):
        return "zero_cell"
    return "fleet"


def _identity_name(row: Mapping[str, Any], kind: str, index: int) -> str:
    if kind == "zero_cell":
        name = str(row.get("cell_id") or row.get("capture_id") or "")
    else:
        name = str(row.get("capture_id") or "")
    return name or f"#{index}"


def _unit_name(row: Mapping[str, Any]) -> str:
    scope = str(row.get("boundary_scope") or "")
    boundary = str(row.get("population_boundary") or "")
    if scope in _STANDALONE_SCOPES or boundary == "native_calls":
        return "standalone_calls"
    if scope in _CLIENT_SCOPES or boundary == "native_client_request":
        return "client_requests"
    if scope in _FORWARD_SCOPES or boundary in {"per_forward_window", "per_forward_window_elapsed", "per_forward_window_additive"}:
        return "forward_window_keys"
    if scope == "" and boundary == "" and _identity_kind(row) == "fleet":
        return "forward_window_keys"
    return "unspecified_keys"


def _account_int(row: Mapping[str, Any], key: str) -> int | None:
    value = row.get(key)
    return value if type(value) is int else None


def _account_over(row: Mapping[str, Any]) -> int | None:
    over = _account_int(row, "keys_over_10pct")
    if over is not None:
        return over
    matched = _account_int(row, "key_matched")
    return 0 if matched == 0 else None


def _account_within(row: Mapping[str, Any]) -> int | None:
    matched = _account_int(row, "key_matched")
    over = _account_over(row)
    if matched is None or over is None:
        return None
    return matched - over


def _sum_account(rows: Sequence[Mapping[str, Any]], pick) -> int | None:
    if not rows:
        return 0
    total = 0
    for row in rows:
        value = pick(row)
        if value is None:
            return None
        total += value
    return total


def _row_resolution(row: Mapping[str, Any]) -> str:
    """source-only, no forecast, conditional, and failed stay unresolved."""
    status = str(row.get("prediction_status") or "")
    if status == "source_only":
        return "source_only"
    if status.endswith("_failed") or status in {"insufficient_evidence"}:
        return "failed"
    comparison = str(row.get("comparison") or "")
    reason = str(row.get("comparison_reason") or "")
    if row.get("boundary_scope") == "standalone":
        comparison = str(row.get("standalone_comparison") or comparison)
        reason = str(row.get("standalone_reason") or reason)
    if status in {"", "missing"}:
        return "no_forecast"
    if comparison == "invalid":
        return "failed" if "fail" in reason else "conditional"
    if comparison in {"", "uncovered"} or status == "not_a_singleton":
        return "no_forecast"
    return ""


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _forward_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [row for row in rows if _unit_name(row) == "forward_window_keys"]


def _stratum_totals(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    forward = _forward_rows(rows)
    return {
        "ids": len(rows),
        "window_key_denominator": _sum_account(forward, lambda row: _account_int(row, "key_denominator")),
        "predictions": _sum_account(forward, lambda row: _account_int(row, "key_matched")),
        "missing": _sum_account(forward, lambda row: _account_int(row, "key_missing")),
        "over": _sum_account(forward, _account_over),
        "within": _sum_account(forward, _account_within),
    }


def _unit_count(rows: Sequence[Mapping[str, Any]], unit: str) -> int | None:
    chosen = [row for row in rows if _unit_name(row) == unit]
    return _sum_account(chosen, lambda row: _account_int(row, "key_denominator"))


def _trace_ready(row: Mapping[str, Any]) -> bool:
    trace = row.get("trace")
    if not isinstance(trace, Mapping):
        return False
    by_class = trace.get("by_class")
    if not isinstance(by_class, Mapping) or not by_class:
        return False
    for value in by_class.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
    return True


def _comparison_record(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        return dict(item)
    return {
        "level": getattr(item, "level", ""),
        "target": getattr(item, "target", ""),
        "measured_ms": getattr(item, "measured_ms", 0.0),
        "predicted_ms": getattr(item, "predicted_ms", 0.0),
        "guard": getattr(item, "guard", ""),
        "operator": getattr(item, "operator", ""),
        "uncancelled_ms": getattr(item, "uncancelled_ms", 0.0),
        "step_details": getattr(item, "step_details", ()) or (),
    }


def _geometry_ready(row: Mapping[str, Any]) -> bool:
    """A missing label or geometry is not a silent Q1/C1/TP1 model input."""
    if not str(row.get("model_label") or "").strip():
        return False
    return all(_finite(row.get(key)) is not None for key in _GEOMETRY_FIELDS)


def _spec_matches_source(row: Mapping[str, Any], cell: Any) -> bool:
    """Reject a spec that replaced a present source field with a default."""
    spec = cell.spec
    expected = {
        "prompt_tokens": spec.prompt_tokens,
        "concurrency": spec.concurrency,
        "max_tokens": spec.max_tokens,
        "tp": spec.tp,
        "dp": spec.dp,
        "ep": spec.ep,
        "pp": spec.pp,
        "graph_bucket": spec.graph_bucket,
    }
    for key, got in expected.items():
        if key not in row or row.get(key) is None:
            continue
        number = _finite(row.get(key))
        if number is None or int(number) != int(got):
            return False
    label = row.get("model_label")
    if label not in (None, "") and str(spec.model_label) != str(label):
        return False
    if row.get("decode_steps") is not None:
        steps = _finite(row.get("decode_steps"))
        if steps is None or int(steps) != int(cell.decode_steps):
            return False
    return True


def _run_compare_cell(row: Mapping[str, Any]) -> tuple[list[Any] | None, str]:
    """Original compare on the complete source row. A failure stays pending."""
    try:
        import zero_shot_piecewise_validation as zsv
        if not _trace_ready(row):
            return None, "prediction_pending"
        if not _geometry_ready(row):
            return None, "defaulted_source"
        cell = zsv.cell_from_dict(row)
        if not _spec_matches_source(row, cell):
            return None, "defaulted_source"
        if cell.trace is None or getattr(cell.trace, "incomplete", False) or not cell.success:
            return None, "trace_not_usable"
        prediction = zsv.predict_cell(cell.spec)
        if prediction.layers <= 0:
            return None, "prediction_pending"
        compared = list(zsv.compare_cell(cell, prediction))
        if not compared:
            return None, "no_comparisons"
        return compared, ""
    except Exception as exc:
        return None, type(exc).__name__


def collect_original_cell(row: Mapping[str, Any]) -> tuple[list[Any] | None, str]:
    """One original evaluation. An already stored comparison is not forecast again."""
    if "original_comparisons" in row:
        supplied = row.get("original_comparisons")
        if supplied is None:
            return None, str(row.get("original_pending_reason") or "prediction_pending")
        return list(supplied), ""
    return _run_compare_cell(row)


def _comparisons_of(row: Mapping[str, Any]) -> tuple[list[dict[str, Any]] | None, str]:
    if "original_comparisons" in row:
        supplied = row.get("original_comparisons")
        if supplied is None:
            return None, "prediction_pending"
        return [_comparison_record(item) for item in supplied], ""
    if _identity_kind(row) != "zero_cell" or not _trace_ready(row):
        return None, "prediction_pending"
    produced, reason = _run_compare_cell(row)
    if not produced:
        return None, reason or "prediction_pending"
    return [_comparison_record(item) for item in produced], ""


def _series_errors(comparison: Mapping[str, Any]) -> list[float]:
    details = comparison.get("step_details") or ()
    errors: list[float] = []
    for item in details:
        if not isinstance(item, (list, tuple)) or len(item) < 4:
            errors.append(math.inf)
            continue
        try:
            signed = float(item[3])
        except (TypeError, ValueError):
            errors.append(math.inf)
            continue
        errors.append(signed if math.isfinite(signed) else math.inf)
    return errors


def _comparison_passed(comparison: Mapping[str, Any]) -> dict[str, Any]:
    """One compare_cell row. Measured zero and an uncovered guard are not a pass."""
    measured = _finite(comparison.get("measured_ms"))
    predicted = _finite(comparison.get("predicted_ms"))
    guard = str(comparison.get("guard") or "").lower()
    operator = str(comparison.get("operator") or "").lower()
    uncovered = (
        measured is None or measured <= 0 or predicted is None
        or "uncovered" in guard or operator.startswith("missing")
    )
    series = _series_errors(comparison)
    if uncovered:
        return {"passed": False, "uncovered": True, "samples": len(series), "above": 0}
    errors = [abs(item) for item in series] if series else [abs((predicted - measured) / measured)]
    uncancelled = _finite(comparison.get("uncancelled_ms")) or 0.0
    ratio = uncancelled / measured if measured else math.inf
    above = sum(1 for item in errors if (not math.isfinite(item)) or item > 0.10)
    passed = bool(errors) and above == 0 and math.isfinite(ratio) and ratio <= 0.10
    return {"passed": passed, "uncovered": False, "samples": len(errors), "above": above}


def _formal_target(comparison: Mapping[str, Any]) -> bool:
    """Null observed L4 is not a formal target. A real series stays."""
    if str(comparison.get("level") or "") != "L4":
        return True
    measured = _finite(comparison.get("measured_ms"))
    operator = str(comparison.get("operator") or "")
    guard = str(comparison.get("guard") or "").lower()
    if (measured is None or measured <= 0) and (operator.startswith("missing") or "uncovered" in guard):
        return False
    return True


def _step_series_samples(comparison: Mapping[str, Any]) -> int:
    target = str(comparison.get("target") or "")
    if str(comparison.get("level") or "") != "L3" and not target.endswith("_step_trace"):
        return 0
    if not _series_errors(comparison):
        return 0
    return int(_comparison_passed(comparison)["samples"])


def _cell_original(row: Mapping[str, Any]) -> dict[str, Any]:
    phase = str(row.get("phase") or "")
    ttft = row.get("ttft_ms", None)
    tpot = row.get("tpot_ms", None)
    comparisons, pending_reason = _comparisons_of(row)
    service_null = (phase != "prefill" and tpot is None) or (phase == "prefill" and ttft is None)
    if comparisons is None:
        return {
            "status": "pending",
            "scope": "outside_scope" if ttft is None and tpot is None else "pending",
            "reason": pending_reason,
            "ttft_pass": False,
            "tpot_pass": False,
            "group_passed": False,
            "step_series": 0,
            "levels": 0,
            "l3_steps": 0,
            "l4_formal": 0,
            "l4_outside": bool(service_null),
            "step_trace_ms": row.get("step_trace_ms"),
        }
    formal = [item for item in comparisons if _formal_target(item)]
    if not formal:
        return {
            "status": "pending",
            "scope": "outside_scope" if service_null else "pending",
            "reason": pending_reason or "no_comparisons",
            "ttft_pass": False,
            "tpot_pass": False,
            "group_passed": False,
            "step_series": 0,
            "levels": 0,
            "l3_steps": 0,
            "l4_formal": 0,
            "l4_outside": bool(service_null),
            "step_trace_ms": row.get("step_trace_ms"),
        }
    judged = [_comparison_passed(item) for item in formal]
    ttft_rows = [item for item in formal if "ttft" in str(item.get("target") or "")]
    tpot_rows = [item for item in formal if "tpot" in str(item.get("target") or "")]
    ttft_pass = bool(ttft_rows) and all(_comparison_passed(item)["passed"] for item in ttft_rows) and ttft is not None and phase == "prefill"
    tpot_pass = bool(tpot_rows) and all(_comparison_passed(item)["passed"] for item in tpot_rows) and tpot is not None and phase == "decode"
    if phase != "prefill" or ttft is None:
        ttft_pass = False
    l3_steps = sum(_step_series_samples(item) for item in formal)
    l4_formal = sum(1 for item in formal if str(item.get("level") or "") == "L4")
    return {
        "status": "compared",
        "scope": "compared",
        "ttft_pass": ttft_pass,
        "tpot_pass": tpot_pass,
        "group_passed": bool(judged) and all(item["passed"] for item in judged),
        "step_series": l3_steps,
        "levels": len(formal),
        "l3_steps": l3_steps,
        "l4_formal": l4_formal,
        "l4_outside": l4_formal == 0 and bool(service_null),
        "step_trace_ms": row.get("step_trace_ms"),
        "reason": "",
    }


def _fleet_row_gate(row: Mapping[str, Any]) -> dict[str, Any]:
    """Original scalar reducer and family/core/unified max. Per-key lists are not a gate."""
    return _fleet_source.fleet_row_decision(row)


def _cell_ambiguous(row: Mapping[str, Any], original: Mapping[str, Any]) -> bool:
    """Null service is outside L4. It does not make a compared L1–L3 cell ambiguous."""
    if original.get("status") == "compared":
        return False
    if _unit_name(row) != "client_requests":
        return False
    return row.get("ttft_ms", None) is None and row.get("tpot_ms", None) is None


def _label_state(row: Mapping[str, Any]) -> str:
    relation = str(row.get("evaluation_relation") or "").strip()
    role = str(row.get("calibration_role") or "").strip().lower()
    if row.get("target_timing_used_to_fit") is True:
        return "fitted"
    if not relation or role in {"", "unspecified"}:
        return "missing"
    return "present"


def _dedupe(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    chosen: list[Mapping[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        kind = _identity_kind(row)
        key = (kind, _identity_name(row, kind, index))
        if key in seen:
            continue
        seen.add(key)
        chosen.append(row)
    return chosen


def _fleet_placeholder(row: Mapping[str, Any]) -> dict[str, Any]:
    relation = ""
    fit = None
    calibration = row.get("source_calibration")
    if isinstance(calibration, Mapping):
        relation = str(calibration.get("evaluation_relation") or "")
        stored = calibration.get("target_timing_used_to_fit")
        fit = stored if isinstance(stored, bool) else None
    role = str(row.get("calibration_role") or relation or "unspecified")
    return {
        "capture_id": str(row.get("capture_id") or ""),
        "identity_type": "fleet",
        "suite": str(row.get("suite") or ""),
        "phase": str(row.get("phase") or ""),
        "evaluation_relation": relation,
        "calibration_role": role,
        "coverage_only": _coverage_text(relation, role),
        "target_timing_used_to_fit": fit,
        "prediction_status": "missing",
        "comparison": "uncovered",
        "comparison_reason": "",
        "boundary_scope": "forward_body",
        "key_denominator": 0,
        "key_matched": 0,
        "key_missing": 0,
        "keys_over_10pct": 0,
        "group_passed_10pct": False,
    }


def _copy_source_scalar(record: dict[str, Any], row: Mapping[str, Any]) -> None:
    """The row scalar replaces a client value already written onto the record."""
    if "observed_ms" not in row:
        return
    record["source_observed_ms"] = row.get("observed_ms")
    scalar = record.get("source_scalar")
    if isinstance(scalar, Mapping) and scalar.get("source_observed_ms") != row.get("observed_ms"):
        record["source_scalar"] = _fleet_source.retarget_scalar(scalar, row.get("observed_ms"))


_SCORE_OVERLAY = (
    "comparison", "comparison_reason", "boundary_scope", "population_boundary",
    "population_status", "prediction_status", "key_denominator", "key_matched",
    "key_missing", "key_invalid", "keys_over_10pct", "group_passed_10pct",
    "passed_10pct", "hardware_tier", "l4_eligible", "calibration_role",
    "evaluation_relation", "coverage_only", "target_timing_used_to_fit",
)


def _cell_record(raw: Mapping[str, Any], scored: Mapping[str, Any] | None) -> dict[str, Any]:
    """Keep the complete source row. Only diagnostic score fields may fill gaps."""
    record = dict(raw)
    for key in _SCORE_OVERLAY:
        if key in record and record.get(key) not in (None, ""):
            continue
        if scored and key in scored and scored.get(key) not in (None, ""):
            record[key] = scored.get(key)
    if scored and "original_comparisons" in scored and "original_comparisons" not in record:
        record["original_comparisons"] = scored.get("original_comparisons")
    cell_id = str(raw.get("cell_id") or record.get("cell_id") or record.get("capture_id") or "")
    record["identity_type"] = "zero_cell"
    record["cell_id"] = cell_id
    record["capture_id"] = str(record.get("capture_id") or cell_id)
    record["suite"] = "zero_shot"
    record.setdefault("phase", str(raw.get("phase") or ""))
    record.setdefault("calibration_role", "unspecified")
    record.setdefault("evaluation_relation", "")
    record.setdefault("prediction_status", "missing")
    record.setdefault("comparison", "uncovered")
    record.setdefault("boundary_scope", "request_l4")
    record.setdefault("key_denominator", 0)
    record.setdefault("key_matched", 0)
    record.setdefault("key_missing", 0)
    return record


def enroll_population(
    scored: Sequence[Mapping[str, Any]],
    fleet_rows: Sequence[Mapping[str, Any]],
    l4_rows: Sequence[Mapping[str, Any]],
    zero_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Fleet ids and zero-shot cells. Unscored fleet ids stay no_forecast."""
    scored_by = {str(item.get("capture_id") or ""): item for item in scored}
    enrolled: list[dict[str, Any]] = []
    seen_fleet: set[str] = set()
    for raw in fleet_rows:
        capture_id = str(raw.get("capture_id") or "")
        seen_fleet.add(capture_id)
        base = dict(scored_by.get(capture_id) or _fleet_placeholder(raw))
        base["identity_type"] = "fleet"
        base["capture_id"] = capture_id or base.get("capture_id") or ""
        _copy_source_scalar(base, raw)
        enrolled.append(base)
    for capture_id, item in scored_by.items():
        if capture_id in seen_fleet:
            continue
        base = dict(item)
        base["identity_type"] = "fleet"
        enrolled.append(base)
    l4_by: dict[str, Mapping[str, Any]] = {}
    for item in l4_rows:
        key = str(item.get("cell_id") or item.get("capture_id") or "")
        l4_by[key] = item
    seen_cells: set[str] = set()
    for raw in zero_rows:
        cell_id = str(raw.get("cell_id") or "")
        seen_cells.add(cell_id)
        record = _cell_record(raw, l4_by.get(cell_id))
        if "original_comparisons" not in record:
            produced, reason = collect_original_cell(raw)
            record["original_comparisons"] = produced
            if reason:
                record["original_pending_reason"] = reason
        enrolled.append(record)
    for cell_id, item in l4_by.items():
        if cell_id in seen_cells:
            continue
        enrolled.append(_cell_record({"cell_id": cell_id}, item))
    return enrolled


def all_original_account(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Normalized identity count, with nested sample units kept beside it.

    ``id_denominator`` is unique fleet ids plus unique zero-shot cells.
    It is not a window count, a client count, or a holdout-only count.
    """
    chosen = _dedupe(rows)
    by_stratum = {"coverage": [], "independent_holdout": [], "unknown": []}
    unresolved = {kind: 0 for kind in _UNRESOLVED_KINDS}
    labels = {"missing": 0, "fitted": 0, "present": 0}
    fleet_ids = 0
    zero_cells = 0
    ambiguous = 0
    cell_pending = 0
    cell_outside = 0
    cell_compared = 0
    cell_groups = 0
    l3_steps = 0
    l4_formal = 0
    l4_outside = 0
    ttft_pass = 0
    cell_group_passed = 0
    pending_reasons: dict[str, int] = {}
    step_series = 0
    fleet_group_passed = 0
    protocol_open = False
    for row in chosen:
        kind = _identity_kind(row)
        if kind == "zero_cell":
            zero_cells += 1
            original = _cell_original(row)
            step_series += int(original["step_series"])
            l3_steps += int(original["l3_steps"])
            cell_groups += int(original["levels"])
            l4_formal += int(original["l4_formal"])
            if original["l4_outside"]:
                l4_outside += 1
            if original["status"] == "pending":
                cell_pending += 1
                protocol_open = True
                reason = str(original.get("reason") or "prediction_pending")
                pending_reasons[reason] = pending_reasons.get(reason, 0) + 1
            elif original["status"] == "compared":
                cell_compared += 1
            if original["scope"] == "outside_scope":
                cell_outside += 1
            if original["ttft_pass"]:
                ttft_pass += 1
            if original["group_passed"]:
                cell_group_passed += 1
            else:
                protocol_open = True
            if _cell_ambiguous(row, original):
                ambiguous += 1
        else:
            fleet_ids += 1
            gate = _fleet_row_gate(row)
            if gate["passed_10pct"]:
                fleet_group_passed += 1
            else:
                protocol_open = True
            if gate["ambiguous"]:
                ambiguous += 1
        stratum = stratum_name(row)
        by_stratum[stratum].append(row)
        resolution = _row_resolution(row)
        if resolution:
            unresolved[resolution] += 1
        labels[_label_state(row)] += 1
    unresolved_rows = sum(unresolved.values())
    forward = _forward_rows(chosen)
    canonical_complete = fleet_ids == CANONICAL_FLEET_IDS and zero_cells == CANONICAL_ZERO_CELLS
    group_passed = bool(chosen) and not protocol_open
    source_strict_pass = bool(group_passed and canonical_complete and not unresolved_rows and ambiguous == 0)
    return {
        "schema": SCHEMA,
        "id_denominator": len(chosen),
        "enrolled": {"fleet_ids": fleet_ids, "zero_cells": zero_cells},
        "canonical_population": {
            "fleet_ids": CANONICAL_FLEET_IDS,
            "zero_cells": CANONICAL_ZERO_CELLS,
            "complete": canonical_complete,
        },
        "window_key_denominator": _sum_account(forward, lambda row: _account_int(row, "key_denominator")),
        "predictions": _sum_account(forward, lambda row: _account_int(row, "key_matched")),
        "missing": _sum_account(forward, lambda row: _account_int(row, "key_missing")),
        "over": _sum_account(forward, _account_over),
        "within": _sum_account(forward, _account_within),
        "strata": {name: _stratum_totals(items) for name, items in by_stratum.items()},
        "holdout_only": _stratum_totals(by_stratum["independent_holdout"]),
        "nested": {
            "forward_window_keys": _unit_count(chosen, "forward_window_keys"),
            "standalone_calls": _unit_count(chosen, "standalone_calls"),
            "client_requests": _unit_count(chosen, "client_requests"),
            "step_series": step_series,
        },
        "labels": labels,
        "target_ambiguous": ambiguous,
        "original_cells": {
            "pending": cell_pending,
            "compared": cell_compared,
            "outside_scope": cell_outside,
            "groups": cell_groups,
            "l3_steps": l3_steps,
            "l4_formal": l4_formal,
            "l4_outside": l4_outside,
            "ttft_pass": ttft_pass,
            "group_passed": cell_group_passed,
            "pending_reasons": pending_reasons,
        },
        "row_gate": {
            "fleet_target": "observed_ms/source_aggregate",
            "operator_aggregate": "family_maximum/core_maximum/unified_maximum/uncancelled",
            "group_passed": fleet_group_passed,
            "changed_by_per_key": False,
        },
        "group_passed": group_passed,
        "source_strict_pass": source_strict_pass,
        "unresolved": unresolved,
        "unresolved_rows": unresolved_rows,
        "global_unresolved": bool(unresolved_rows) or cell_pending > 0,
    }
