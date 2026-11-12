"""Request TTFT source identity, domain check, and per-key scoring.

Source identity comes from the forecast declaration. A request
``producer_sha256`` is authoritative. The observer witness is used only
when neither the cell nor any request states a SHA. TTFT is not ITL or
TPOT. The 10% threshold stays in ``hf_sample_scoring`` and is reached
through ``score_fleet_row``.
"""
from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

def _forecast_view(item: Any) -> dict[str, Any]:
    """Declaration view. The canonical key stays even when ``as_dict`` omits it."""
    if isinstance(item, Mapping):
        view = dict(item)
    elif hasattr(item, "as_dict"):
        view = dict(item.as_dict())
    else:
        view = {}
    if not view.get("key"):
        key = getattr(item, "key", None)
        if key:
            view["key"] = key
    return view


def _same_field(left: Any, right: Any) -> bool:
    if left is None or right is None or left == "" or right == "":
        return True
    return str(left) == str(right)


def _declaration_matches(item: Mapping[str, Any], decl: Mapping[str, Any], cell_id: str) -> bool:
    """Structural bind: key, ordinal, prompt, phase, mix, rack, producer. Not list position."""
    key = str(item.get("key") or item.get("semantic_key") or "")
    if not key or key != str(decl.get("key") or ""):
        return False
    if not _same_field(item.get("cell_id") or cell_id, decl.get("cell_id") or cell_id):
        return False
    try:
        ordinal = int(decl["ordinal"])
        if int(item["launch_ordinal"]) != ordinal or int(item["prompt_tokens"]) != int(decl["prompt_tokens"]):
            return False
    except (KeyError, TypeError, ValueError):
        return False
    if f"|ordinal={ordinal}|" not in key:
        return False
    for name in ("phase", "mix_class", "rack", "producer", "max_tokens"):
        if not _same_field(item.get(name), decl.get(name)):
            return False
    if item.get("concurrency") is not None and decl.get("concurrency") is not None:
        try:
            if int(item["concurrency"]) != int(decl["concurrency"]):
                return False
        except (TypeError, ValueError):
            return False
    return True


def _forecast_identity(cell: Mapping[str, Any], rows: Sequence[Any]) -> tuple[str, str, bool, bool]:
    """Rack clock and producer SHA stated by the forecast. Not the observer.

    Each request ``producer_sha256`` is authoritative. One shared request SHA
    is the identity when the cell states none. Two different request SHAs are
    a contradiction and do not fall back to the observer. The legacy witness
    is allowed only when neither the cell nor any request states a SHA.
    ``producer_boundary`` and ``client_boundary`` are the forecast clocks.
    ``target_boundary`` is not a rack clock.
    """
    cell_sha = str(cell.get("producer_sha256") or "").strip()
    request_shas = {
        str(item.get("producer_sha256") or "").strip()
        for item in rows
        if isinstance(item, Mapping) and str(item.get("producer_sha256") or "").strip()
    }
    producer_clock = str(cell.get("producer_boundary") or "").strip()
    client_clock = str(cell.get("client_boundary") or "").strip()
    conflict = len(request_shas) > 1
    if cell_sha and request_shas and any(item != cell_sha for item in request_shas):
        conflict = True
    if producer_clock and client_clock and producer_clock != client_clock:
        conflict = True
        clock = client_clock
    else:
        clock = producer_clock or client_clock
    if len(request_shas) == 1:
        published = next(iter(request_shas))
        if cell_sha and cell_sha != published:
            published = cell_sha
    else:
        published = cell_sha
    allow_witness = not cell_sha and not request_shas
    return published, clock, conflict, allow_witness


def _bind_request_forecast(
    cell_id: str,
    phase: str,
    declarations: Sequence[Any],
    observed: Sequence[Any],
    producer_sha256: str,
    forecast: Mapping[str, Any],
) -> dict[str, Any]:
    """Turn forecast_cell rows into keyed TTFT milliseconds.

    ``actual_ms``, ``signed_error`` and ``unsigned_error`` are not read.
    One cell mean is not copied onto every key. Equal predicted values stay
    when each row has its own ordinal and causal state. A second row with the
    same key and a different time is not a sample. A request producer SHA is
    the identity when the cell states none. Disagreeing request SHAs are not
    paired and are not replaced by the witness. ``producer_sha256`` is the
    legacy witness only when the forecast states no SHA at all. A row with
    ``grade_eligible`` false is not paired to the source.
    """
    declared = {str(view.get("key") or ""): view for item in declarations if (view := _forecast_view(item)).get("key")}
    rows = forecast.get("requests") if isinstance(forecast.get("requests"), Sequence) else ()
    cell = forecast.get("cell") if isinstance(forecast.get("cell"), Mapping) else {}
    stated_sha, clock, identity_conflict, allow_witness = _forecast_identity(cell, rows)
    samples: dict[str, float] = {}
    state: list[dict[str, Any]] = []
    unbound: list[str] = []
    conflicts: set[str] = set()
    for raw in rows:
        if not isinstance(raw, Mapping):
            continue
        item = {key: value for key, value in raw.items() if key not in {"actual_ms", "signed_error", "unsigned_error"}}
        key = str(item.get("semantic_key") or item.get("key") or "")
        status = item.get("semantic_key_status")
        decl = declared.get(key)
        if (status is not None and str(status) != "verified") or decl is None or not _declaration_matches(item, decl, cell_id):
            unbound.append(key or "?")
            continue
        if item.get("grade_eligible") is False or cell.get("grade_eligible") is False:
            unbound.append(key or "?")
            continue
        try:
            value = float(item.get("predicted_ms"))
        except (TypeError, ValueError):
            unbound.append(key)
            continue
        if key in samples:
            if samples[key] != value:
                conflicts.add(key)
            unbound.append(key)
            continue
        if not math.isfinite(value) or value <= 0.0:
            unbound.append(key)
            continue
        samples[key] = value
        state.append({
            "key": key,
            "launch_ordinal": item.get("launch_ordinal"),
            "predicted_ms": value,
            "own_body_ms": item.get("own_body_ms"),
            "queue_wait_ms": item.get("queue_wait_ms"),
            "rank_assignment": item.get("rank_assignment"),
            "rank_queue_index": item.get("rank_queue_index"),
            "prompt_tokens": item.get("prompt_tokens"),
            "mix_class": item.get("mix_class"),
        })
    for key in conflicts:
        samples.pop(key, None)
        state = [item for item in state if item.get("key") != key]
    if identity_conflict:
        for key in list(samples):
            unbound.append(key)
        samples.clear()
        state.clear()
    host_status = cell.get("host_overhead_status")
    host_ms = cell.get("host_overhead_ms")
    if str(host_status or "") == "absent_assumed_zero":
        host_ms = None
    prediction: dict[str, Any] = {
        "status": "modeled" if samples else "not_measured",
        "prediction_boundary": "native_client_request",
        "boundary_basis": "per_request_client_ttft",
        "capture_id": cell_id,
        "phase": str(cell.get("phase") or phase),
        "workload_id": cell_id,
        "producer_sha256": stated_sha if stated_sha or not allow_witness else str(producer_sha256 or ""),
    }
    if clock:
        prediction["ttft_boundary"] = clock
    if samples:
        prediction["boundary_samples"] = samples
    return {
        "prediction": prediction,
        "request_forecasts": state,
        "forecast_unbound_keys": unbound,
        "forecast_status": forecast.get("status"),
        "forecast_reason": forecast.get("reason"),
        "forecast_assumptions": {
            "schema": forecast.get("schema"),
            "host_overhead_status": host_status,
            "host_overhead_ms": host_ms,
            "scheduler_condition": cell.get("scheduler_condition"),
            "actual_scheduler_observed": cell.get("actual_scheduler_observed"),
            "chunk_budget": cell.get("chunk_budget"),
            "chunk_budget_source": cell.get("chunk_budget_source"),
            "mean_forecast_ms": cell.get("mean_forecast_ms"),
            "priced_by": "forecast_cell",
        },
        "source_config_sha256": str(cell.get("source_config_sha256") or ""),
        "source_deploy_sha256": str(cell.get("source_deploy_sha256") or ""),
        "source_raw": "bound" if forecast.get("status") == "forecast" and cell.get("model_case") else "uncertain",
    }


_SCALAR_PREDICTION_FIELDS = (
    "boundary_ms", "predicted_boundary_ms", "boundary_samples_ms", "samples_ms",
    "per_forward_ms", "predicted_samples_ms",
)
# Producer clocks that are client TTFT. TPOT and ITL are not members.
_TTFT_CLOCKS = {
    "client_send_to_first_sse_with_choices_may_empty",
    "client_send_to_first_nonempty_text_or_terminal_fallback",
}


def _basis_rejects_request_ttft(basis: str) -> bool:
    """One check for a basis or field name that is TPOT or ITL, not request TTFT.

    ``itl`` is not a substring of ``inter_token``. Both are the wrong domain.
    """
    text = str(basis or "").lower().replace("-", "_")
    return "itl" in text or "inter_token" in text or "tpot" in text


def _coerce_ttft_samples(samples: Any, basis: str) -> tuple[Any, bool]:
    """Publish explicit ``ttft_ms`` on every phase. Do not read ``tpot_ms`` as TTFT.

    A plain millisecond stays a plain millisecond. N remains the numeric scorer.
    A mapping without ``ttft_ms`` that carries a TPOT or ITL field is rejected
    rather than passed through the decode TPOT preference.
    """
    if _basis_rejects_request_ttft(basis):
        return {}, True
    if not isinstance(samples, Mapping):
        return samples, False
    coerced: dict[str, Any] = {}
    for key, value in samples.items():
        if not isinstance(value, Mapping):
            coerced[str(key)] = value
            continue
        typed = value.get("ttft_ms")
        if typed not in (None, ""):
            coerced[str(key)] = typed
            continue
        names = " ".join(str(name) for name in value)
        if _basis_rejects_request_ttft(names):
            return {}, True
        coerced[str(key)] = value
    return coerced, False


def _clock_incompatible(boundary: str, metric: str) -> bool:
    """A named TPOT/ITL value is not a TTFT sample. An empty clock is not a claim."""
    if _basis_rejects_request_ttft(f"{boundary} {metric}"):
        return True
    return bool(boundary) and boundary not in _TTFT_CLOCKS


def score_client_request_interface(
    interface: Mapping[str, Any],
    prediction: Mapping[str, Any] | None = None,
    *,
    hardware_tier: str = "",
) -> dict[str, Any]:
    """Score one P6 cell's per-request TTFT keys.

    The enrolled id is the cell. Each launch ordinal is a key on that cell, not
    another enrolled id. A declared ordinal with no TTFT row is unobserved. A
    row whose TTFT is not finite is missing. A scalar prediction is not copied
    onto more than one key. Producer TPOT is not derived from these samples.
    ``hardware_tier`` is the enrolled A2/A3/A5 tier. The rack name stays on
    ``producer_rack`` and is not used as that tier.
    """
    # The gate imports this module. Import the row scorer only when scoring.
    from hf_benchmark_gate import score_fleet_row

    cell = interface.get("cell") if isinstance(interface.get("cell"), Mapping) else {}
    requests = interface.get("requests") if isinstance(interface.get("requests"), Sequence) else ()
    declared = interface.get("declarations") if isinstance(interface.get("declarations"), Sequence) else ()
    phase = str(cell.get("phase") or "")
    cell_id = str(cell.get("cell_id") or "")
    samples: list[dict[str, Any]] = []
    boundaries: list[str] = []
    absent = 0
    incompatible = 0
    seen: set[int] = set()
    declared_ordinals: set[int] = set()
    orphans = 0

    def _boundary(value: Any) -> None:
        text = str(value or "")
        if text and text not in boundaries:
            boundaries.append(text)

    for request in requests:
        if not isinstance(request, Mapping):
            continue
        boundary = str(request.get("ttft_boundary") or "")
        metric = str(request.get("metric") or request.get("value_basis") or "")
        _boundary(boundary)
        ordinal = request.get("launch_ordinal")
        try:
            seen.add(int(ordinal))
        except (TypeError, ValueError):
            ordinal = None
        wrong_domain = _clock_incompatible(boundary, metric)
        ttft = request.get("ttft_s")
        try:
            observed = float(ttft) * 1000.0
        except (TypeError, ValueError):
            observed = None
        if wrong_domain:
            incompatible += 1
            observed = None
            state = "incompatible"
        elif observed is None or not math.isfinite(observed):
            absent += 1
            observed = None
            state = "missing"
        else:
            state = "measured"
        samples.append({
            "key": str(request.get("key") or ""),
            "observed_ms": observed,
            "phase": phase,
            "launch_ordinal": ordinal,
            "status": "measured" if observed is not None else "not_measured",
            "measurement_state": state,
        })
    for item in declared:
        if not isinstance(item, Mapping):
            continue
        try:
            ordinal = int(item.get("ordinal"))
        except (TypeError, ValueError):
            continue
        declared_ordinals.add(ordinal)
        _boundary(item.get("ttft_boundary"))
        if ordinal in seen:
            continue
        seen.add(ordinal)
        samples.append({
            "key": str(item.get("key") or f"{cell_id}|ordinal={ordinal}"),
            "observed_ms": None,
            "phase": phase,
            "launch_ordinal": ordinal,
            "status": "not_measured",
            "measurement_state": "unobserved",
        })
    if declared_ordinals:
        orphans = sum(
            1 for request in requests
            if isinstance(request, Mapping)
            and isinstance(request.get("launch_ordinal"), int)
            and int(request["launch_ordinal"]) not in declared_ordinals
        )
    elif isinstance(cell.get("missing_ordinals"), Sequence):
        for ordinal in cell.get("missing_ordinals") or ():
            try:
                number = int(ordinal)
            except (TypeError, ValueError):
                continue
            if number in seen:
                continue
            seen.add(number)
            samples.append({
                "key": f"{cell_id}|ordinal={number}",
                "observed_ms": None,
                "phase": phase,
                "launch_ordinal": number,
                "status": "not_measured",
                "measurement_state": "unobserved",
            })
    unobserved = sum(1 for sample in samples if sample.get("measurement_state") == "unobserved")
    tier = str(hardware_tier or "")
    observation = {
        "capture": {
            "capture_id": cell_id,
            "phase": phase,
            "hardware_tier": tier,
        },
        "source": {"independent": True},
        "measurements": {"native_client_request": {
            "status": "measured" if samples else "unknown",
            "phase": phase,
            "samples_basis": "per_request_client_ttft",
            "samples": samples,
        }},
    }
    incoming = dict(prediction or {})
    basis = str(incoming.get("boundary_basis") or incoming.get("prediction_basis") or "")
    coerced, rejected_basis = _coerce_ttft_samples(incoming.get("boundary_samples"), basis)
    if rejected_basis:
        incoming.pop("boundary_samples", None)
        for name in _SCALAR_PREDICTION_FIELDS:
            incoming.pop(name, None)
        incoming["status"] = "not_measured"
    elif isinstance(coerced, Mapping):
        incoming["boundary_samples"] = coerced
    cell_sha = str(cell.get("producer_sha256") or "").strip().lower()
    pred_sha = str(incoming.get("producer_sha256") or "").strip().lower()
    producer_mismatch = bool(cell_sha and pred_sha and cell_sha != pred_sha)
    if producer_mismatch:
        incoming.pop("boundary_samples", None)
        for name in _SCALAR_PREDICTION_FIELDS:
            incoming.pop(name, None)
        incoming["status"] = "not_measured"
    else:
        keyed_now = incoming.get("boundary_samples")
        declared_clock = str(incoming.get("ttft_boundary") or "")
        if isinstance(keyed_now, Mapping) and declared_clock:
            request_clock = {
                str(item.get("key") or ""): str(item.get("ttft_boundary") or "")
                for item in requests if isinstance(item, Mapping)
            }
            incoming["boundary_samples"] = {
                str(key): value for key, value in keyed_now.items()
                if not request_clock.get(str(key)) or request_clock.get(str(key)) == declared_clock
            }
    keyed = incoming.get("boundary_samples")
    withheld_scalar = (
        not rejected_basis
        and len(samples) > 1
        and not (isinstance(keyed, Mapping) and len(keyed) > 0)
    )
    if withheld_scalar:
        for name in _SCALAR_PREDICTION_FIELDS:
            incoming.pop(name, None)
    scored = score_fleet_row(
        {"capture_id": cell_id, "suite": "zero_shot", "phase": phase, "hardware_tier": tier},
        observation,
        incoming,
    )
    scored["hardware_tier"] = tier or scored.get("hardware_tier") or ""
    scored["producer_rack"] = str(cell.get("rack") or "")
    scored["producer_sha256"] = str(cell.get("producer_sha256") or "")
    scored["request_ttft_boundaries"] = boundaries
    scored["request_ttft_absent"] = absent
    scored["request_ttft_unobserved"] = unobserved
    scored["request_ttft_orphans"] = orphans
    scored["request_ttft_incompatible"] = incompatible
    scored["request_scalar_withheld"] = withheld_scalar
    scored["tpot_domain"] = "not_scored_on_request_ttft"
    if producer_mismatch:
        scored["comparison"] = "invalid"
        scored["comparison_reason"] = "producer_sha256_mismatch"
        scored["passed_10pct"] = False
        scored["group_passed_10pct"] = False
        scored["producer_clock_status"] = "mismatch"
    elif rejected_basis:
        scored["comparison"] = "uncovered"
        scored["comparison_reason"] = "request_boundary_not_per_request"
        scored["passed_10pct"] = False
        scored["group_passed_10pct"] = False
        scored["per_key_errors"] = {}
        scored["key_matched"] = 0
        scored["matched"] = 0
        scored["keys_over_10pct"] = 0
        scored["over_limit"] = 0
    elif pred_sha:
        scored["producer_clock_status"] = "matched"
    else:
        scored["producer_clock_status"] = "unwitnessed"
    return scored
