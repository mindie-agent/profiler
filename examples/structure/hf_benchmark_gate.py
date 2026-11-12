"""Honest strict gate for the 7,337-capture profiling benchmark.

The public entry stays in ``hf_profiling_benchmark``. This module owns the
checks that must not turn a stored error, a gzip-only read, or a trimmed
table into a pass.

A sample exists only when ``hf_sample_scoring`` pairs a declared boundary
with a finite observation on that same key. Kernel mass, client TPOT/TTFT,
and historical ``observed_ms`` are recorded and are not substituted for
one another. One row is never cut off by a fixed alarm; an explicit
job-level deadline stops only between rows and leaves the run incomplete.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import hf_fleet_source_gate as _fleet_source
import hf_original_account as _original_account
import hf_source_slices as _source_slices
from hf_sample_scoring import score_boundary, score_operator_groups
from hf_request_ttft import _basis_rejects_request_ttft

# Sorted unique IDs, UTF-8, one id per line, trailing LF. Census checksums,
# not per-record costs.
ZS_ID_SHA256 = "cb9b995b24cda52cd084bc8132dec66486ae25a6fc8fdf1d9c6fb97b49af7a74"
FLEET_ID_SHA256 = "ae2dea16bf44358e8cdc42f7e9ff059015d73fe65ecff2cf3e0d70041d2fe38f"
ZS_ID_COUNT = 731
FLEET_ID_COUNT = 6606

_POISON_KEYS = {
    "observed_ms", "predicted_ms", "relative_error", "passed_10pct", "passed_15pct",
    "operator_modeling", "kernel_summary", "structural_inference",
    "structural_weights", "active_hbm_mb", "active_cube_gflops",
}
_DEMAND_KEYS = ("structural_weights", "active_hbm_mb", "active_cube_gflops")
_ADVERTISED = (
    "README.md",
    "manifest.json",
    "data/zero_shot_l1_l4_cells.jsonl",
    "data/fleet_captures.jsonl",
    "data/zero_shot_l1_l4_cells.jsonl.gz",
    "data/fleet_captures.jsonl.gz",
)
_PAIRS = (
    ("data/zero_shot_l1_l4_cells.jsonl", "data/zero_shot_l1_l4_cells.jsonl.gz", "cell_id", ZS_ID_SHA256, ZS_ID_COUNT),
    ("data/fleet_captures.jsonl", "data/fleet_captures.jsonl.gz", "capture_id", FLEET_ID_SHA256, FLEET_ID_COUNT),
)
_UNDECLARED_BOUNDARY = "model_step_ms_undeclared"
# Source relations copied from decode.json / prefill.json. Variants stay separate.
_REQUIRED_RELATIONS = {
    "in_sample": 69,
    "in_sample_native_physical_domains": 1,
    "mixed_native_transfer_and_in_sample_hccl_gating": 2,
    "retrospective_context_transfer; not_blind": 77,
    "new_target_not_used_for_fitting; previously_inspected_not_blind": 12,
    "new_q4_128K_target_not_used_for_fitting; previously_inspected_not_blind": 2,
}


def id_digest(ids: Sequence[str]) -> str:
    """SHA-256 of sorted UTF-8 lines with a trailing newline."""
    payload = "".join(f"{item}\n" for item in sorted(ids)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def prediction_config(row: Mapping[str, Any]) -> dict[str, Any]:
    """Drop stored timings, demand backfill, and kernel projections before predict."""
    cfg = {key: value for key, value in row.items() if key not in _POISON_KEYS}
    geom = {key: value for key, value in dict(cfg.get("geometry") or {}).items() if key not in _DEMAND_KEYS}
    traits = {key: value for key, value in dict(cfg.get("traits") or {}).items() if key not in _DEMAND_KEYS}
    cfg["geometry"] = geom
    if traits:
        cfg["traits"] = traits
    else:
        cfg.pop("traits", None)
    return cfg


def load_verified_table(plain: Path, gz: Path) -> tuple[list[dict[str, Any]], str]:
    """Read one table only when the plain bytes equal the decompressed gzip."""
    if not plain.is_file() or not gz.is_file():
        raise ValueError(
            "Strict <=10% gate failed: plain/gzip pair missing "
            f"plain={plain.name}:{plain.is_file()} gz={gz.name}:{gz.is_file()}"
        )
    plain_bytes = plain.read_bytes()
    with gzip.open(gz, "rb") as handle:
        gz_bytes = handle.read()
    if plain_bytes != gz_bytes:
        plain_sha = hashlib.sha256(plain_bytes).hexdigest()
        gz_sha = hashlib.sha256(gz_bytes).hexdigest()
        raise ValueError(
            "Strict <=10% gate failed: plain jsonl and gzip disagree "
            f"{plain.name}={plain_sha} decompressed={gz_sha}"
        )
    rows = [json.loads(line) for line in plain_bytes.decode("utf-8").splitlines() if line.strip()]
    return rows, hashlib.sha256(plain_bytes).hexdigest()


def _relation(row: Mapping[str, Any]) -> str:
    cal = row.get("source_calibration")
    if isinstance(cal, Mapping):
        return str(cal.get("evaluation_relation") or "")
    return ""


def _stored_fit(row: Mapping[str, Any]) -> bool | None:
    cal = row.get("source_calibration")
    if isinstance(cal, Mapping) and isinstance(cal.get("target_timing_used_to_fit"), bool):
        return cal["target_timing_used_to_fit"]
    if isinstance(row.get("target_timing_used_to_fit"), bool):
        return row["target_timing_used_to_fit"]
    return None


def _role(row: Mapping[str, Any]) -> str:
    role = str(row.get("calibration_role") or "")
    if role:
        return role
    relation = _relation(row)
    if relation == "in_sample":
        return "in_sample"
    if relation == "retrospective_context_transfer; not_blind":
        return "not_blind"
    return relation or "unspecified"


def _prediction_mutant(row: Mapping[str, Any]) -> dict[str, Any]:
    """Double layer and step counters. An independent observation does not move."""
    out = dict(row)
    try:
        out["layers"] = int(out.get("layers") or 40) * 2
    except (TypeError, ValueError):
        out["layers"] = 80
    try:
        base = int(out.get("decode_steps") or out.get("forward_steps") or 63)
    except (TypeError, ValueError):
        base = 63
    out["decode_steps"] = base * 2
    return out


def _observation_signature(observation: Mapping[str, Any] | None) -> str:
    obs = observation or {}
    payload = {
        "measurements": obs.get("measurements"),
        "observed_ms": obs.get("observed_ms"),
        "observed_operator_ms": obs.get("observed_operator_ms"),
        "observed_by_core_ms": obs.get("observed_by_core_ms"),
        "observed_by_family_ms": obs.get("observed_by_family_ms"),
        "native_mass_us": obs.get("native_mass_us"),
    }
    return json.dumps(_json_ready(payload), sort_keys=True, default=str)


# Same SKU prefixes the fleet model and the archive case reader already use.
# A product string such as Ascend950DT is a tier, not a disagreement with "A5".
_SKU_TIER_PREFIXES = (
    ("Ascend910B", "A2"),
    ("Ascend910_93", "A3"),
    ("Ascend950", "A5"),
    ("Ascend910_95", "A5"),
)


def _sku_tier(hardware: Mapping[str, Any] | None) -> tuple[str, str]:
    """Map one launch/preflight record to A2/A3/A5. Unknown SKUs stay blank."""
    if not isinstance(hardware, Mapping):
        return "", ""
    raw = str(hardware.get("hardware_key") or hardware.get("sku") or "")
    if raw in {"A2", "A3", "A5"}:
        return raw, raw
    for prefix, tier in _SKU_TIER_PREFIXES:
        if raw.startswith(prefix):
            return tier, raw
    return "", raw


def _evidence_from_timetables(timetables: Any) -> dict[str, Any]:
    """Compact join of one cell. Timetable objects are not retained.

    Two positive raw SHAs are two physical ranks, not a digest conflict.
    L4 client TTFT/TPOT is not on this timetable and is not invented from the raw span.
    """
    phases: set[str] = set()
    ranks: list[dict[str, Any]] = []
    identified = forwards = traces = missing = unknown_ops = named_ops = 0
    l4_present = False
    for timetable in timetables:
        status = str(getattr(timetable, "status", "") or "")
        if status == "missing_source":
            missing += 1
            continue
        traces += 1
        phase = str(getattr(timetable, "phase", "") or "")
        if phase in {"decode", "prefill"}:
            phases.add(phase)
        hardware = getattr(timetable, "hardware", None) or {}
        tier, sku = _sku_tier(hardware if isinstance(hardware, Mapping) else {})
        digest = str(getattr(timetable, "source_sha256", "") or "")
        boundaries = getattr(timetable, "boundaries", None) or {}
        if isinstance(boundaries, Mapping) and any(boundaries.get(name) for name in ("ttft", "tpot", "request")):
            l4_present = True
        rank_conflict = str(getattr(timetable, "rank_conflict", "") or "")
        ranks.append({
            "rank": getattr(timetable, "rank", None),
            "device_id": getattr(timetable, "device_id", None),
            "source_sha256": digest,
            "hardware_tier": tier,
            "hardware_key": sku,
            "rank_conflict": rank_conflict,
        })
        forwards += len(tuple(getattr(timetable, "forwards", ()) or ()))
        for layer in getattr(timetable, "layer_windows", ()) or ():
            if (getattr(layer, "layer_id", None) is not None and getattr(layer, "forward_id", None)
                    and getattr(layer, "start_ns", None) is not None and getattr(layer, "end_ns", None) is not None):
                identified += 1
        for op in getattr(timetable, "operators", ()) or ():
            core = str(getattr(op, "core", "") or "").strip().upper()
            if core in {"", "UNKNOWN", "N/A", "NA"}:
                unknown_ops += 1
            else:
                named_ops += 1
    tiers = sorted({item["hardware_tier"] for item in ranks if item["hardware_tier"]})
    digests = sorted({item["source_sha256"] for item in ranks if item["source_sha256"]})
    return {
        "joined": True,
        "phase": next(iter(phases)) if len(phases) == 1 else "",
        "hardware_tier": tiers[0] if len(tiers) == 1 else "",
        "hardware_tiers": tiers,
        "source_sha256": digests[0] if len(digests) == 1 else "",
        "source_sha256_by_rank": ranks,
        "rank_sha_count": len(digests),
        "identified_windows": identified,
        "forward_count": forwards,
        "measured_traces": traces,
        "missing_source": missing,
        "unknown_core_operators": unknown_ops,
        "named_core_operators": named_ops,
        "l4_request_on_timetable": l4_present,
    }


def _zs_gaps(row: Mapping[str, Any], evidence: Mapping[str, Any] | None = None) -> list[str]:
    """Gaps come from a joined timetable. A stored column that was never joined is not a check."""
    del row
    if not evidence or not evidence.get("joined"):
        return ["not_joined"]
    gaps: list[str] = []
    if str(evidence.get("phase") or "") not in {"decode", "prefill"}:
        gaps.append("phase")
    recovered = evidence.get("hardware_tiers") or []
    if not recovered and str(evidence.get("hardware_tier") or "") not in {"A2", "A3", "A5"}:
        gaps.append("hardware")
    if int(evidence.get("rank_sha_count") or 0) <= 0 and not str(evidence.get("source_sha256") or ""):
        gaps.append("source_digest")
    if int(evidence.get("identified_windows") or 0) <= 0 and int(evidence.get("forward_count") or 0) <= 0:
        gaps.append("native_windows")
    return gaps


def _named_engine_keys(observation: Mapping[str, Any]) -> tuple[int, int]:
    """Count op groups whose engine is a named core. UNKNOWN and N/A are not engines."""
    raw = (observation.get("measurements") or {}).get("operator_groups")
    if isinstance(raw, Mapping) and isinstance(raw.get("groups"), (Mapping, list, tuple)):
        raw = raw.get("groups")
    named = unknown = 0
    items = raw.items() if isinstance(raw, Mapping) else ()
    for key, entry in items:
        if str(key) in {"status", "basis", "groups", "source", "unit", "note", "samples_basis"}:
            continue
        core = ""
        if isinstance(entry, Mapping):
            core = str(entry.get("engine") or entry.get("core") or "")
        if not core and "\x1f" in str(key):
            core = str(key).split("\x1f", 1)[1].split("\x1f", 1)[0]
        token = core.strip().upper()
        if token in {"", "UNKNOWN", "N/A", "NA"}:
            unknown += 1
        else:
            named += 1
    return named, unknown


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _client_field(observation: Mapping[str, Any], key: str) -> float | None:
    client = (observation.get("measurements") or {}).get("native_client_request") or {}
    if client.get("status") != "measured":
        return None
    return _finite(client.get(key))


def _coverage_only(relation: str, role: str) -> bool:
    """Calibration rows stay in the inventory and are not blind performance samples."""
    text = f"{relation} {role}".lower()
    return "in_sample" in text or "not_blind" in text or "regime_table_replay" in text


def _identity_index() -> Mapping[str, Mapping[str, Any]]:
    """Structure-suite rows. The same provider the dataset entry already uses."""
    global _IDENTITY_INDEX
    if _IDENTITY_INDEX is None:
        import hf_profiling_benchmark as benchmark
        _IDENTITY_INDEX = {
            str(row.get("capture_id") or ""): row
            for row in benchmark._collect_structure_suites()[0]
        }
    return _IDENTITY_INDEX


def _bind_inherited_role(item: dict[str, Any], row: Mapping[str, Any], observation: Mapping[str, Any]) -> None:
    """Copy source fit and slice identity. Does not read the model fit flag."""
    identity = _identity_index().get(str(item.get("capture_id") or ""))
    if identity is not None:
        _apply_source_role(item, {
            "relation": _relation(identity),
            "role": _role(identity),
            "phase": str(identity.get("phase") or ""),
            "hardware_tier": str(identity.get("hardware_tier") or ""),
            "target_timing_used_to_fit": _stored_fit(identity),
        })
    disclosed = _source_slices.disclose_source_slices(
        [_source_slices.slice_record(row, observation)],
        [identity] if identity is not None else None,
    )
    apply_slice_disclosure(item, disclosed["by_id"].get(str(item.get("capture_id") or "")))


def _emitted_model_fit(prediction: Mapping[str, Any]) -> bool | None:
    """The publisher's own fit flag. Absent means the model did not emit one."""
    emitted = prediction.get("target_timing_used_to_fit")
    return emitted if isinstance(emitted, bool) else None


slice_record = _source_slices.slice_record


def disclose_source_slices(
    records: Sequence[Mapping[str, Any]],
    calibration_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Group verified kernel/receipt/window slices. Does not drop a population row."""
    return _source_slices.disclose_source_slices(records, calibration_rows)


def apply_slice_disclosure(item: dict[str, Any], info: Mapping[str, Any] | None) -> None:
    """Copy the slice's earliest calibration onto a row that has no actual relation."""
    _source_slices.apply_slice_disclosure(item, info, coverage_only=_coverage_only)


def _apply_source_role(item: dict[str, Any], src: Mapping[str, Any] | None) -> None:
    """Disclose the case-record relation. A stored zero_shot label is not that relation."""
    if not isinstance(src, Mapping):
        return
    relation, role = str(src.get("relation") or ""), str(src.get("role") or "")
    if relation:
        item["evaluation_relation"] = relation
        item["calibration_role"] = role or relation
        item["coverage_only"] = _coverage_only(relation, role)
        if "target_timing_used_to_fit" in src:
            item["target_timing_used_to_fit"] = src.get("target_timing_used_to_fit")
    if (str(item.get("phase") or "") != str(src.get("phase") or "")
            or str(item.get("hardware_tier") or "") != str(src.get("hardware_tier") or "")):
        item["attribution_mismatch"] = True


# Exact source boundaries. An invented per_forward* label is not a member.
_FORWARD_BOUNDARIES = {
    "per_forward_window",
    "per_forward_window_elapsed",
    "per_forward_window_additive",
}
_REQUEST_BOUNDARIES = {"native_client_request"}
_STANDALONE_BOUNDARIES = {"native_calls"}
_DECLARED_SCOPE = {
    "per_forward_window": "forward_body",
    "per_forward_window_elapsed": "forward_body",
    "per_forward_window_additive": "forward_body",
    "native_client_request": "request_l4",
    "native_calls": "standalone",
}
_POPULATION_SCOPE = {
    "per_forward_window": "forward_body",
    "native_client_request": "request_l4",
    "native_calls": "standalone",
}
_REGISTERED_SUITES = {"registered_decode", "registered_prefill"}
_IDENTITY_INDEX: dict[str, Mapping[str, Any]] | None = None
_UNRESOLVED_KINDS = ("source_only", "no_forecast", "conditional", "failed")


def _key_account(result: Mapping[str, Any]) -> dict[str, Any]:
    """Copy N's key population. A failing group does not erase matched or missing keys.

    N returns the worst relative error, not how many keys exceed 10%. That
    count stays absent. Paired keys stay in ``matched``.
    """
    missing = list(result.get("missing_keys") or [])
    invalid = list(result.get("invalid_keys") or [])
    compared = result.get("comparison") == "compared"
    sample = result.get("sample")
    over = result.get("count_over_10pct")
    denominator = result.get("denominator", result.get("n_samples"))
    # No measured population is not a zero-key coverage claim.
    missing_count = None if denominator is None else len(missing)
    return {
        "denominator": denominator,
        "matched": result.get("matched"),
        "missing": missing_count,
        "invalid": len(invalid),
        "missing_keys": missing,
        "group_passed_10pct": bool(compared and result.get("passed_10pct")),
        "max_error": sample if result.get("comparison") in {"compared", "invalid"} else None,
        "comparison": str(result.get("comparison") or "uncovered"),
        "reason": str(result.get("reason") or ""),
        "keys_over_10pct": over if isinstance(over, int) else None,
    }


def _observation_for_native_calls(observation: Mapping[str, Any]) -> dict[str, Any]:
    """Return the observation unchanged.

    N reads the enrolled phase, the producer native phase, the top-level source
    digest, and ``measurements.native_calls.source_sha256`` as separate witnesses.
    Copying the call digest onto ``source.sha256`` hides a real disagreement.
    """
    return observation


def _apply_native_digest_rule(prediction: Mapping[str, Any], observation: Mapping[str, Any],
                               scored: Mapping[str, Any]) -> dict[str, Any]:
    """A native-call pass needs the call file's own sha. A mismatch is invalid.

    N compares the top-level source sha. Calibration rows leave that field empty
    and put the file digest on ``measurements.native_calls``. Either side missing
    is uncovered. An already invalid comparison is left as N returned it.
    """
    if scored.get("comparison") == "invalid":
        return dict(scored)
    native = (observation.get("measurements") or {}).get("native_calls") or {}
    boundary_sha = str(native.get("source_sha256") or "").strip().lower() if isinstance(native, Mapping) else ""
    pred_sha = str(prediction.get("source_sha256") or "").strip().lower()
    if boundary_sha and pred_sha and boundary_sha != pred_sha:
        out = dict(scored)
        out["comparison"] = "invalid"
        out["reason"] = "native_calls_source_sha256_mismatch"
        out["passed_10pct"] = False
        return out
    if scored.get("comparison") == "compared" and (not boundary_sha or not pred_sha):
        out = dict(scored)
        out["comparison"] = "uncovered"
        out["reason"] = "native_calls_source_sha256_absent"
        out["passed_10pct"] = False
        return out
    return dict(scored)


def _request_basis_allows(observation: Mapping[str, Any], scored: Mapping[str, Any]) -> bool:
    """TPOT requires a per-request boundary. A prefill singleton may use its one TTFT.

    An absent basis is not rewritten. A harness aggregate is not per-step TPOT.
    A prefill aggregate is a TTFT pair only when the population is exactly one request.
    """
    entry = (observation.get("measurements") or {}).get("native_client_request") or {}
    if not isinstance(entry, Mapping):
        return True
    basis = str(entry.get("samples_basis") or "")
    if not basis:
        return True
    if _basis_rejects_request_ttft(basis):
        return False
    phase = str((observation.get("capture") or {}).get("phase") or "").lower()
    if "harness_aggregate" in basis:
        if phase == "decode":
            return False
        return int(scored.get("denominator") or 0) == 1
    return True


def _population_scope(result: Mapping[str, Any]) -> str:
    """Scope of the measured observation. A missing population stays unknown."""
    if str(result.get("population_status") or "") != "measured":
        return "unknown"
    return _POPULATION_SCOPE.get(str(result.get("population_boundary") or ""), "unknown")


def _published_scope(declared: str, result: Mapping[str, Any]) -> str:
    """Keep a declared scope only when it is the observation's own boundary.

    Missing, wrong, invalid, and unsupported predictions keep the measured
    population. Nothing measured stays unknown and is not called a forward.
    """
    population = _population_scope(result)
    declared_scope = _DECLARED_SCOPE.get(declared)
    if (declared_scope is not None
            and declared_scope == population
            and result.get("reason") != "prediction_boundary_scope_mismatch"):
        return declared_scope
    return population


def score_fleet_row(row: Mapping[str, Any], observation: Mapping[str, Any], prediction: Mapping[str, Any]) -> dict[str, Any]:
    """One capture. Stored observed/predicted fields are not read.

    ``native_calls`` is a standalone scope. It does not become a body step or a
    service TPOT/TTFT. Request boundaries stay on ``request_l4``. Forward windows
    stay on ``forward_body``. When the prediction is missing, wrong, or invalid,
    the published scope is the measured observation, not ``undeclared``.
    """
    declared = str(prediction.get("prediction_boundary") or "")
    native = (observation.get("measurements") or {}).get("native_calls") or {}
    native_phase = str(native.get("native_phase") or "") if isinstance(native, Mapping) else ""
    viewed = _observation_for_native_calls(observation) if declared == "native_calls" else observation
    boundary_result = score_boundary(prediction, viewed)
    population_boundary = str(boundary_result.get("population_boundary") or "")
    if (declared in _STANDALONE_BOUNDARIES
            and population_boundary == "native_calls"
            and boundary_result.get("reason") != "prediction_boundary_scope_mismatch"):
        boundary_result = _apply_native_digest_rule(prediction, observation, boundary_result)
    if (declared in _REQUEST_BOUNDARIES
            and population_boundary == "native_client_request"
            and boundary_result.get("reason") != "prediction_boundary_scope_mismatch"
            and not _request_basis_allows(observation, boundary_result)):
        boundary_result = dict(boundary_result)
        boundary_result["comparison"] = "uncovered"
        boundary_result["reason"] = "request_boundary_not_per_request"
        boundary_result["passed_10pct"] = False
    scope = _published_scope(declared, boundary_result)
    account = _key_account(boundary_result)
    operator = score_operator_groups(prediction, observation)
    named_engines, unknown_engines = _named_engine_keys(observation)
    if scope == "standalone" and unknown_engines and not named_engines:
        operator = dict(operator)
        operator["passed_10pct"] = False
        operator["comparison"] = "unavailable"
        operator["reason"] = "engine_unavailable"
    elif operator.get("passed_10pct") and unknown_engines:
        operator = dict(operator)
        operator["passed_10pct"] = False
        operator["reason"] = "unknown_core_not_a_pass"
    measurements = observation.get("measurements") or {}
    kernel = measurements.get("whole_capture_native_kernel_rows") or {}
    window = measurements.get("per_forward_window") or {}
    source = observation.get("source") if isinstance(observation.get("source"), Mapping) else {}
    op_sample = operator.get("sample")
    relation, role = _relation(row), _role(row)
    body_score = scope != "standalone"
    body_sample = account["max_error"] if body_score else None
    scalar = _fleet_source.score_source_scalar(row, observation, prediction, boundary_result)
    families, cores = _fleet_source.measured_scopes(observation)
    declared_maps = None if families or cores else _fleet_source.declared_operator_maps(row)
    if declared_maps is not None:
        operator_source = _fleet_source.compare_operator_projection(
            declared_maps.get("family"), declared_maps.get("core"), prediction,
            same_proof=_fleet_source._same_proof(row, observation, prediction),
            source_declared=True,
            measured_canonical=declared_maps.get("canonical"),
            measured_unified=declared_maps.get("unified"),
            declared_total=("predicted_operator_ms" in (row.get("operator_modeling") or {})),
        )
        operator_source = dict(operator_source)
        operator_source["population_forward_steps"] = row.get("forward_steps")
    else:
        operator_source = _fleet_source.compare_operator_projection(
            families, cores, prediction, same_proof=_fleet_source._same_proof(row, observation, prediction),
        )
    conditional_population = str(scalar.get("population_label") or "") == "conditional"
    item = {
        "capture_id": str(row.get("capture_id") or ""),
        "suite": str(row.get("suite") or ""),
        "phase": str(row.get("phase") or ""),
        "enrolled_phase": str(row.get("phase") or ""),
        "native_phase": native_phase,
        "hardware_tier": str(row.get("hardware_tier") or ""),
        "calibration_role": role,
        "evaluation_relation": relation,
        "coverage_only": _coverage_only(relation, role),
        "boundary_scope": scope,
        "population_boundary": population_boundary or None,
        "population_status": str(boundary_result.get("population_status") or ""),
        "evidence_status": str(observation.get("evidence_status") or "missing"),
        "native_status": str(kernel.get("status") or "unknown"),
        "per_forward_window": str(window.get("status") or "unknown"),
        "prediction_status": str(prediction.get("status") or "missing"),
        "prediction_boundary": declared or population_boundary or str(boundary_result.get("boundary") or _UNDECLARED_BOUNDARY),
        "comparison": account["comparison"] if body_score else "not_a_body_step",
        "comparison_reason": (account["reason"] if body_score
                              else "standalone_native_call_is_not_a_body_or_service_step"),
        "sample": body_sample,
        "n_samples": account["denominator"],
        "matched": account["matched"],
        "missing_keys": account["missing_keys"],
        "max_error": account["max_error"],
        "over_limit": account["keys_over_10pct"],
        "passed_10pct": bool(body_score and account["group_passed_10pct"] and not conditional_population),
        "key_denominator": account["denominator"],
        "key_matched": account["matched"],
        "key_missing": account["missing"],
        "key_invalid": account["invalid"],
        "keys_over_10pct": account["keys_over_10pct"],
        "group_passed_10pct": account["group_passed_10pct"],
        "standalone_comparison": account["comparison"] if scope == "standalone" else "",
        "standalone_reason": account["reason"] if scope == "standalone" else "",
        "standalone_passed_10pct": bool(scope == "standalone" and account["group_passed_10pct"]),
        "standalone_max_error": account["max_error"] if scope == "standalone" else None,
        "operator_comparison": str(operator.get("comparison") or "uncovered"),
        "operator_reason": str(operator.get("reason") or ""),
        "operator_sample": op_sample if operator.get("comparison") in {"compared", "invalid"} else None,
        "operator_passed_10pct": bool(operator.get("comparison") == "compared" and operator.get("passed_10pct")),
        "per_key_errors": dict(boundary_result.get("per_key_errors") or {}),
        "source_path": str(source.get("path") or source.get("directory") or ""),
        "source_sha256": str(source.get("sha256") or source.get("recorded_source_sha256") or ""),
        "source_independent": bool(source.get("independent")),
        "target_timing_used_to_fit": _stored_fit(row),
        "model_target_timing_used_to_fit": _emitted_model_fit(prediction),
        "slice_role_inherited": False,
        "slice_role_source_id": "",
        "client_tpot_ms": _client_field(observation, "reported_tpot_ms"),
        "client_ttft_ms": _client_field(observation, "reported_ttft_ms"),
        "native_mass_us": _finite(observation.get("native_mass_us")),
        "observed_operator_ms": observation.get("observed_operator_ms"),
        "source_observed_ms": scalar["source_observed_ms"],
        "source_observation_ms": scalar["source_observation_ms"],
        "source_observation_basis": scalar["source_observation_basis"],
        "source_predicted_step": scalar["predicted_step_ms"],
        "source_scalar": scalar,
        "source_operator": operator_source,
    }
    _bind_inherited_role(item, row, observation)
    return item




def enroll_population(
    scored: Sequence[Mapping[str, Any]],
    fleet_rows: Sequence[Mapping[str, Any]],
    l4_rows: Sequence[Mapping[str, Any]],
    zero_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """One record per fleet id and per zero-shot cell actually in this input."""
    return _original_account.enroll_population(scored, fleet_rows, l4_rows, zero_rows)


def all_original_account(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Normalized fleet-plus-cell count. Nested keys stay in their own fields.

    Alias ids stay separate. A window, a standalone call, and a client request
    are not extra gate ids. Independent holdout requires source lineage.
    """
    return _original_account.all_original_account(rows)



from hf_benchmark_report import (  # noqa: E402
    _hardware_still_missing,
    _identity_report,
    _json_ready,
    _stamp_hardware,
    _stratum_name,
    evaluate,
    render_dataset_card,
    score_l4_bundle,
    singleton_request_ttft,
    validate_release,
)
