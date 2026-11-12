"""Request pairing for one zero-shot cell.

The benchmark entry calls this once per cell. Singleton eligibility stays in
the gate. A priced cell uses the existing ``predict_cell`` or ``forecast_cell``
hook and does not open a second scoring path.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import hf_benchmark_gate
import zero_shot_piecewise_validation as zsv

def _l4_physical(spec: Any) -> dict[str, Any]:
    """Bound host/worker weight source. A caller path is not copied into this record."""
    origin = spec.source_config
    return {"source_config": "" if origin is None else str(origin), "source_config_sha256": str(spec.source_config_sha256 or "").strip().lower(), "source_deploy_sha256": str(spec.source_deploy_sha256 or ""), "source_weight_dir": "" if spec.source_weight_dir is None else str(spec.source_weight_dir), "source_case_dir": "" if getattr(spec, "source_case_dir", None) is None else str(spec.source_case_dir), "require_source": bool(spec.require_source)}
def _l4_interface(row: Mapping[str, Any]) -> tuple[dict[str, Any], Any]:
    """P8 cell plus declaration keys. Requests stay keys of this cell."""
    import zero_shot_client_requests as client
    capture = client.client_capture(row)
    interface = client.p6_interface(capture)
    boundary = str((capture.producer or {}).get("ttft_boundary") or "")
    interface["declarations"] = [
        {"key": item.key, "ordinal": item.ordinal, "ttft_boundary": boundary}
        for item in capture.declarations
    ]
    interface["cell"]["hardware_families"] = [str(item) for item in capture.hardware_families]
    interface["cell"]["hardware_basis"] = sorted({
        str(item.get("hardware_basis") or "")
        for item in capture.rank_sources
        if isinstance(item, Mapping) and item.get("hardware_basis")
    })
    return interface, capture


def _attach_request_forecast(decision: dict[str, Any], row: Mapping[str, Any], capture: Any) -> None:
    """Price one non-singleton cell with forecast_cell. The 94-scalar path does not call this."""
    from zero_shot_request_prediction import forecast_cell, source_declarations
    try:
        declarations = tuple(source_declarations(row))
    except (OSError, ValueError, KeyError, TypeError):
        declarations = ()
    if not declarations:
        decision["forecast_status"] = "unavailable"
        decision["forecast_reason"] = "declarations_absent"
        return
    try:
        forecast = forecast_cell(row, declarations=declarations)
    except TimeoutError:
        raise
    except Exception as exc:
        decision["forecast_status"] = "unavailable"
        decision["forecast_reason"] = f"forecast_failed:{type(exc).__name__}:{exc}"
        return
    interface = decision.get("interface") if isinstance(decision.get("interface"), Mapping) else {}
    observed = interface.get("requests") if isinstance(interface.get("requests"), Sequence) else ()
    producer_sha = str((getattr(capture, "producer", {}) or {}).get("producer_sha256") or "")
    bound = _bind_request_forecast(
        str(row.get("cell_id") or ""),
        str(row.get("phase") or ""),
        declarations,
        observed,
        producer_sha,
        forecast,
    )
    decision.update(bound)


def _header_fields(notes: tuple[str, ...] | list[str]) -> dict[str, str]:
    """Header status from predict_cell notes. It does not change model/config binding."""
    text = next((str(item).split(":", 1)[1] for item in notes if str(item).startswith("quant_source:")), "")
    if text.startswith("header_source_bound"):
        status = "bound"
    elif text.startswith("header_source_unreadable"):
        status = "unreadable"
    elif text.startswith("header_source_ineligible"):
        status = "ineligible"
    elif text.startswith("header_source_absent"):
        status = "absent"
    elif text.startswith("header_source_none"):
        status = "none"
    else:
        status = ""
    return {"header_binding": status, "header_source_note": text}


def _zero_shot_l4_pair(row: Mapping[str, Any], *, price: bool = True) -> dict[str, Any]:
    """TTFT from B's bound deployment. The caller path and digest are only a check.

    A missing file or another SKU is not priced. The producer singleton stays eligible.
    A real bound file declared with a different digest is invalid, not uncovered.
    ``price=False`` keeps the P8 request keys and does not call a pricer.
    A prefill concurrency-1 cell is priced once by ``predict_cell`` and is not
    sent through ``forecast_cell``. Every other priced cell uses ``forecast_cell``
    only. ``evaluate_cell`` actuals are not the model.
    """
    import zero_shot_actual_entry as zsa
    cell_id, phase = str(row.get("cell_id") or ""), str(row.get("phase") or "")
    capture = None
    try:
        interface, capture = _l4_interface(row)
    except (OSError, ValueError, KeyError, TypeError):
        interface = None
    paths = getattr(_zero_shot_l4_pair, "_paths", None)
    if paths is None:
        paths = zsa._index(zsa.DEFAULT_ROOTS)
        setattr(_zero_shot_l4_pair, "_paths", paths)
    path = paths.get(cell_id.split(":")[-1])
    notes = tuple(str(item) for item in (row.get("notes") or ()))
    if path is None:
        absent = {"eligible": False, "reason": "observation_absent", "streams": 0, "notes": notes, "source_raw": "missing"}
        if interface is not None:
            absent["interface"] = interface
        return absent
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        absent = {"eligible": False, "reason": "observation_absent", "streams": 0, "notes": notes, "source_raw": "missing"}
        if interface is not None:
            absent["interface"] = interface
        return absent
    decision = dict(hf_benchmark_gate.singleton_request_ttft(raw if isinstance(raw, Mapping) else {}, phase))
    decision["notes"] = notes
    if interface is not None:
        decision["interface"] = interface
    if not price:
        return decision
    if not decision.get("eligible"):
        if capture is not None:
            _attach_request_forecast(decision, row, capture)
        return decision
    declared_path = str(row.get("source_config") or row.get("model_config_path") or "")
    declared_sha = str(row.get("source_config_sha256") or row.get("model_config_sha256") or "").strip().lower()
    if declared_path or declared_sha:
        decision["declared_config"], decision["declared_config_sha256"] = declared_path, declared_sha
    try:
        spec = zsv.cell_from_dict(row).spec
    except (TypeError, ValueError, KeyError):
        decision["reason"], decision["source_raw"] = "prediction_case_absent", "missing"
        return decision
    physical = _l4_physical(spec)
    if spec.source_reject_reason:
        decision["reason"] = spec.source_reject_reason
        decision["source_raw"] = "uncertain" if spec.source_reject_reason == "source_override_contradicts_deployment" else "missing"
        return decision
    origin_sha = physical["source_config_sha256"]
    digest_mismatch = bool(declared_sha and declared_sha != origin_sha)
    deploy_bad = bool(spec.require_source and (not physical["source_config"] or not physical["source_deploy_sha256"] or physical["source_deploy_sha256"] != origin_sha))
    if (not digest_mismatch) and (deploy_bad or spec.model_case is None or not Path(spec.model_case).is_file()):
        decision["reason"] = "deploy_identity_missing_or_mismatch" if deploy_bad else "prediction_case_absent"
        decision["source_raw"] = "missing"
        return {**decision, **physical}
    priced_notes: tuple[str, ...] = ()
    try:
        if digest_mismatch:
            ttft = None
        else:
            priced = zsv.predict_cell(spec)
            ttft = priced.ttft_ms
            priced_notes = tuple(str(item) for item in priced.notes)
    except TimeoutError:
        raise
    except Exception as exc:
        decision["reason"], decision["source_raw"], decision["diagnostics"] = "predictor_failed", "uncertain", [f"{type(exc).__name__}:{exc}"]
        return {**decision, **physical}
    number = float(ttft) if isinstance(ttft, (int, float)) and math.isfinite(float(ttft)) and float(ttft) > 0 else None
    tier = str(row.get("hardware_tier") or "")
    observation = {"capture": {"capture_id": cell_id, "phase": spec.phase, "hardware_tier": tier}, "source": {"independent": True, "path": str(path)}, "measurements": {"native_client_request": {"status": "measured", "phase": spec.phase, "samples_basis": "singleton_request_ttft_ms", "samples": [{"key": decision.get("key") or "request:0", "observed_ms": decision["observed_ms"], "phase": spec.phase}]}}}
    prediction = {"status": "modeled", "prediction_boundary": "native_client_request", "boundary_basis": "singleton_request_ttft_ms", "capture_id": cell_id, "phase": spec.phase, "workload_id": cell_id, "hardware_tier": tier, **physical}
    if digest_mismatch or number is None:
        if digest_mismatch:
            observation["source"]["sha256"] = origin_sha
            prediction["source_sha256"] = declared_sha
            decision["reason"], decision["source_raw"] = "source_config_sha256_mismatch", "uncertain"
        else:
            decision["reason"], decision["source_raw"] = "prediction_absent", "uncertain"
            if priced_notes:
                decision.update(_header_fields(priced_notes))
                decision["prediction_notes"] = priced_notes
            return {**decision, **physical}
        decision["notes"] = spec.notes
        return {**decision, **physical, "observation": observation, "prediction": prediction}
    prediction["boundary_ms"] = number
    decision["notes"], decision["source_raw"] = spec.notes, "bound"
    if priced_notes:
        decision.update(_header_fields(priced_notes))
        decision["prediction_notes"] = priced_notes
    return {**decision, **physical, "observation": observation, "prediction": prediction}
