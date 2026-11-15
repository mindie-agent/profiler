"""Per-cell native-call forecast coverage for the zero-shot validator.

[Role] Project the public piecewise ``OperatorRow`` records (already bound by
  ``mindie_sim.prediction.piecewise.native_calls``) into an occurrence-exact
  coverage report and a per-model summary.
[Invariants] Only actual emitted rows count.  A row without a selected
  entry/source/typed ABI stays in the denominator.  A unique call is counted
  from its content-derived ``call_id``; no catalogue or target CSV is read.
[Timeouts & Locks] Bounded in-memory arithmetic; no I/O, device or locks.
[Side-Effect Policy] Pure projection; the caller keeps the prediction records.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable, Mapping


def route_binding(spec: Any, raw: dict[str, Any]) -> dict[str, Any]:
    """Use the selected transport route binder when present; keep raw otherwise."""
    try:
        from .pcom_route_binding import bind_moe_route_safe
    except ImportError:
        try:
            from pcom_route_binding import bind_moe_route_safe
        except ImportError:
            return raw
    return bind_moe_route_safe(spec, raw)


def forecast(prediction: Any) -> dict[str, Any]:
    """Occurrence coverage for one frozen prediction."""
    from mindie_sim.prediction.piecewise.native_calls import forecast_native_coverage
    return forecast_native_coverage(tuple(getattr(prediction, "rows", ()) or ()))


def aggregate(predictions: Iterable[Any]) -> dict[str, Any]:
    """Overall plus per-model coverage over every frozen prediction."""
    from mindie_sim.prediction.piecewise.native_calls import (
        forecast_native_coverage, model_native_coverage,
    )
    by_model: dict[str, list] = defaultdict(list)
    all_rows: list = []
    for prediction in predictions:
        rows = tuple(getattr(prediction, "rows", ()) or ())
        model = str(getattr(prediction, "model_label", "") or "unresolved")
        by_model[model].extend(rows)
        all_rows.extend(rows)
    return {
        "schema": "mindie-profiler/native-forecast/1",
        "overall": forecast_native_coverage(tuple(all_rows)),
        "by_model": model_native_coverage(by_model),
        "non_claims": ["frozen_prediction_only", "no_measured_latency_read"],
    }


def row_record(row: Any) -> dict[str, Any]:
    """Stable evidence record for one public row (call + occurrence)."""
    occurrence = getattr(row, "native_occurrence", None) or {}
    return {
        "name": getattr(row, "name", ""), "kind": getattr(row, "kind", ""),
        "mechanism": getattr(row, "mechanism", ""),
        "phase": getattr(row, "phase", "") or occurrence.get("phase", ""),
        "count": int(getattr(row, "count", 1) or 1),
        "duration_ms": float(getattr(row, "duration_ms", 0.0) or 0.0),
        "call_id": (getattr(row, "native_call", None) or {}).get("call_id"),
        "api": (getattr(row, "native_call", None) or {}).get("api"),
        "source": (getattr(row, "native_call", None) or {}).get("source"),
        "typed": (getattr(row, "native_call", None) or {}).get("typed"),
        "kernels": (getattr(row, "native_call", None) or {}).get("kernels", ()),
        "members": ((getattr(row, "native_call", None) or {}).get("members") or {}).get("op_ids", ()),
        "occurrence": occurrence,
    }
