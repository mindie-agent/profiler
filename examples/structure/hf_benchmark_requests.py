"""Request pairing for one zero-shot cell.

The benchmark entry calls this once per cell. Singleton eligibility stays in
the gate. A priced cell uses the existing ``predict_cell`` or ``forecast_cell``
hook and does not open a second scoring path.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any, Mapping, Sequence

import hf_benchmark_gate
from hf_request_ttft import _bind_request_forecast
try:
    from .hf_benchmark_cells import (
        cell_from_dict, forecast_cell, predict_cell, source_declarations,
        structure_fingerprint as _structure_fingerprint,
    )
except ImportError:
    from hf_benchmark_cells import (  # type: ignore[no-redef]
        cell_from_dict, forecast_cell, predict_cell, source_declarations,
        structure_fingerprint as _structure_fingerprint,
    )
try:
    from . import zero_shot_source_binding as zsb
except ImportError:
    import zero_shot_source_binding as zsb

def _l4_physical(
    spec: Any, *, source_file_sha256: str = "", origin_sha256: str = ""
) -> dict[str, Any]:
    """Bound host/worker weight source with declared, file and deployment identities.

    ``source_file_sha256`` is the actual bytes of the declared/bound config file;
    ``source_deploy_sha256``
    is the deployment-verified digest; ``source_config_sha256`` is the origin used
    for this prediction (deployment when available, otherwise the actual file).
    """
    origin = spec.source_config
    deploy_sha = str(getattr(spec, "source_deploy_sha256", "") or "").strip().lower()
    bound_sha = str(origin_sha256 or deploy_sha or spec.source_config_sha256 or "").strip().lower()
    return {
        "source_config": "" if origin is None else str(origin),
        "source_config_sha256": bound_sha,
        "source_file_sha256": str(source_file_sha256 or "").strip().lower(),
        "source_deploy_sha256": deploy_sha,
        "source_origin": "deployment" if deploy_sha else ("source_file" if source_file_sha256 else ""),
        "source_weight_dir": "" if spec.source_weight_dir is None else str(spec.source_weight_dir),
        "source_case_dir": "" if getattr(spec, "source_case_dir", None) is None else str(spec.source_case_dir),
        "require_source": bool(spec.require_source),
    }
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


def _declared_source_identity(row: Mapping[str, Any]) -> tuple[str, str]:
    """Return the caller's declared source path and digest.

    These fields are a declaration to verify, never the bound origin identity.
    """
    path = str(row.get("source_config") or row.get("model_config_path") or "")
    digest = str(row.get("source_config_sha256") or row.get("model_config_sha256") or "").strip().lower()
    return path, digest


def _source_file_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    """Read the declared file separately from any deployment binding.

    The returned identities are intentionally distinct: ``declared_sha256`` is
    what the caller claimed, ``source_file_sha256`` is the content actually at
    the declared path, and the deployment digest is resolved later by the case
    parser.  A directly decidable contradiction is returned here, before any
    pricer or unrelated parse failure can consume the cleared declaration.
    """
    declared_path, declared_sha = _declared_source_identity(row)
    identity: dict[str, Any] = {
        "declared_path": declared_path,
        "declared_sha256": declared_sha,
        "source_file_sha256": "",
        "path_error": "",
    }
    try:
        from .zero_shot_source_binding import resolve_declared_file
    except ImportError:
        from zero_shot_source_binding import resolve_declared_file
    resolution = resolve_declared_file(declared_path, declared_sha)
    identity["source_file_sha256"] = resolution.actual_sha256
    if resolution.error in {"source_override_path_invalid", "source_override_unreadable"}:
        identity["path_error"] = resolution.error
    return identity


def _prediction_parse_row(row: Mapping[str, Any], declared_path: str) -> dict[str, Any]:
    """Parse with an unverified digest cleared, preserving a pathless declaration.

    A declared config path names the bytes the caller wants checked, so the
    actual digest must come from those bytes.  A digest without any path is
    still kept so the existing path-validation branch can report that gap.
    """
    copied = dict(row)
    if declared_path:
        copied["source_config_sha256"] = ""
        copied["model_config_sha256"] = ""
    return copied


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
        measurement_sha256 = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except (OSError, ValueError):
        absent = {"eligible": False, "reason": "observation_absent", "streams": 0, "notes": notes, "source_raw": "missing"}
        if interface is not None:
            absent["interface"] = interface
        return absent
    decision = dict(hf_benchmark_gate.singleton_request_ttft(raw if isinstance(raw, Mapping) else {}, phase))
    decision["notes"] = notes
    decision["measurement_path"] = str(path)
    decision["measurement_sha256"] = measurement_sha256
    if interface is not None:
        decision["interface"] = interface
    if not price:
        return decision
    if not decision.get("eligible"):
        if capture is not None:
            _attach_request_forecast(decision, row, capture)
        return decision
    identity = _source_file_identity(row)
    declared_path, declared_sha = identity["declared_path"], identity["declared_sha256"]
    if declared_path or declared_sha:
        decision["declared_config"], decision["declared_config_sha256"] = declared_path, declared_sha
    decision["source_file_sha256"] = identity["source_file_sha256"]
    direct_mismatch = bool(
        declared_sha
        and identity["source_file_sha256"]
        and declared_sha != identity["source_file_sha256"]
    )
    if identity["path_error"]:
        # A declared path that is missing/unreadable is decidable without the
        # case parser; do not turn it into a pricer error or an absent case.
        decision["reason"], decision["source_raw"] = identity["path_error"], "missing"
        return decision
    try:
        # The declared digest is checked separately above.  It must not enter
        # case resolution as the origin identity, otherwise a present but
        # contradicting declaration raises and is then mislabelled absent.
        spec = cell_from_dict(_prediction_parse_row(row, declared_path)).spec
    except zsb.SourceConfigDigestMismatch as mismatch:
        # Defensive path: a digest field escaped the clear above.  Preserve the
        # actual file identity and report the digest gap, never "absent".
        decision["source_config_sha256"] = mismatch.actual_sha256
        decision["source_file_sha256"] = mismatch.actual_sha256
        try:
            spec = cell_from_dict(_prediction_parse_row(row, declared_path)).spec
        except (OSError, TypeError, ValueError, KeyError) as exc:
            decision["reason"], decision["source_raw"] = "source_config_sha256_mismatch", "uncertain"
            decision["diagnostics"] = [f"reparse_{type(exc).__name__}:{exc}"]
            return decision
    except (OSError, TypeError, ValueError, KeyError) as exc:
        if direct_mismatch:
            # A directly decidable file/digest contradiction takes precedence
            # over an unrelated parse failure and is never sent to a pricer.
            decision["reason"], decision["source_raw"] = "source_config_sha256_mismatch", "uncertain"
            decision["source_config_sha256"] = identity["source_file_sha256"]
            decision["diagnostics"] = [f"prediction_case_unparseable:{type(exc).__name__}:{exc}"]
            return decision
        # Genuinely missing/unparseable prediction input keeps its own reason;
        # the original exception is retained in diagnostics, not silently lost.
        decision["reason"], decision["source_raw"] = "prediction_case_absent", "missing"
        decision["diagnostics"] = [f"prediction_case_unparseable:{type(exc).__name__}:{exc}"]
        return decision
    deploy_sha = str(getattr(spec, "source_deploy_sha256", "") or "").strip().lower()
    bound_file_sha = identity["source_file_sha256"]
    if spec.source_config is not None:
        try:
            bound_file_sha = hashlib.sha256(Path(spec.source_config).read_bytes()).hexdigest()
        except OSError:
            bound_file_sha = identity["source_file_sha256"]
    physical = _l4_physical(
        spec,
        source_file_sha256=bound_file_sha,
        origin_sha256=bound_file_sha if not deploy_sha else "",
    )
    if spec.source_reject_reason and not direct_mismatch:
        decision["reason"] = spec.source_reject_reason
        decision["source_raw"] = "uncertain" if spec.source_reject_reason == "source_override_contradicts_deployment" else "missing"
        decision["source_deploy_sha256"] = physical["source_deploy_sha256"]
        return decision
    origin_sha = physical["source_config_sha256"]
    digest_mismatch = bool(
        direct_mismatch
        or (declared_sha and origin_sha and declared_sha != origin_sha)
    )
    deploy_expected = bool(
        deploy_sha
        or getattr(spec, "source_case_dir", None)
        or str(getattr(spec, "dataset", "")) == "out"
    )
    deploy_bad = bool(
        spec.require_source
        and deploy_expected
        and (
            not physical["source_config"]
            or not deploy_sha
            or deploy_sha != origin_sha
        )
    )
    source_missing = bool(spec.require_source and not origin_sha)
    if (not digest_mismatch) and (
        deploy_bad or source_missing or spec.model_case is None or not Path(spec.model_case).is_file()
    ):
        decision["reason"] = (
            "deploy_identity_missing_or_mismatch"
            if (deploy_bad or source_missing)
            else "prediction_case_absent"
        )
        decision["source_raw"] = "missing"
        return {**decision, **physical}
    priced_notes: tuple[str, ...] = ()
    try:
        if digest_mismatch:
            ttft = None
        else:
            # Hand the real predictor the same verified identity it just
            # checked: the actual file for bench, the deployment for out.
            priced_spec = replace(
                spec,
                source_config_sha256=origin_sha or spec.source_config_sha256,
                source_file_sha256=bound_file_sha,
                source_origin=physical["source_origin"],
                source_deploy_sha256=physical["source_deploy_sha256"],
            )
            priced = predict_cell(priced_spec)
            ttft = priced.get("ttft_ms") if isinstance(priced, Mapping) else getattr(priced, "ttft_ms", None)
            priced_notes = tuple(str(item) for item in (
                priced.get("notes") if isinstance(priced, Mapping) else getattr(priced, "notes", ()) or ()))
    except TimeoutError:
        raise
    except Exception as exc:
        decision["reason"], decision["source_raw"], decision["diagnostics"] = "predictor_failed", "uncertain", [f"{type(exc).__name__}:{exc}"]
        return {**decision, **physical}
    number = float(ttft) if isinstance(ttft, (int, float)) and math.isfinite(float(ttft)) and float(ttft) > 0 else None
    tier = str(row.get("hardware_tier") or "")
    config_source = {
        "independent": True,
        "kind": "config",
        "path": "" if spec.source_config is None else str(spec.source_config),
        "sha256": origin_sha,
        "file_sha256": bound_file_sha,
        "deploy_sha256": physical["source_deploy_sha256"],
        "origin": physical["source_origin"],
        "declared_sha256": declared_sha,
    }
    measurement_source = {
        "independent": True,
        "kind": "measurement",
        "path": str(path),
        "sha256": measurement_sha256,
    }
    observation = {"capture": {"capture_id": cell_id, "phase": spec.phase, "hardware_tier": tier}, "source": dict(config_source), "config_source": dict(config_source), "measurement_source": measurement_source, "measurements": {"native_client_request": {"status": "measured", "phase": spec.phase, "samples_basis": "singleton_request_ttft_ms", "samples": [{"key": decision.get("key") or "request:0", "observed_ms": decision["observed_ms"], "phase": spec.phase}]}}}
    prediction = {"status": "modeled", "prediction_boundary": "native_client_request", "boundary_basis": "singleton_request_ttft_ms", "capture_id": cell_id, "phase": spec.phase, "workload_id": cell_id, "hardware_tier": tier, "source_sha256": origin_sha, **physical}
    if digest_mismatch or number is None:
        if digest_mismatch:
            prediction["source_sha256"] = declared_sha
            decision["reason"], decision["source_raw"] = "source_config_sha256_mismatch", "uncertain"
        else:
            decision["reason"], decision["source_raw"] = "prediction_absent", "uncertain"
            if priced_notes:
                decision.update(_header_fields(priced_notes))
                decision["prediction_notes"] = priced_notes
            return {**decision, **physical, "structure_fingerprint": _structure_fingerprint(spec)}
        decision["notes"] = spec.notes
        return {**decision, **physical, "observation": observation, "prediction": prediction, "structure_fingerprint": _structure_fingerprint(spec)}
    prediction["boundary_ms"] = number
    decision["notes"], decision["source_raw"] = spec.notes, "bound"
    if priced_notes:
        decision.update(_header_fields(priced_notes))
        decision["prediction_notes"] = priced_notes
    return {**decision, **physical, "observation": observation, "prediction": prediction, "structure_fingerprint": _structure_fingerprint(spec)}
