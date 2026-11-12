"""Dataset card, release check, and in-memory evaluation.

Sample pairing stays in ``hf_sample_scoring``. The fleet scalar and operator
comparison stay in ``hf_fleet_source_gate``. This module assembles the summary
and does not rewrite the source jsonl.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from hf_request_ttft import score_client_request_interface

_BOUND = False
_GATE_NAMES = (
    "_ADVERTISED", "_PAIRS", "_REGISTERED_SUITES", "_REQUIRED_RELATIONS", "_UNRESOLVED_KINDS",
    "_apply_source_role", "_coverage_only", "_evidence_from_timetables", "_observation_signature",
    "_original_account", "_prediction_mutant", "_relation", "_role", "_sku_tier", "_source_slices",
    "_stored_fit", "_zs_gaps", "all_original_account", "apply_slice_disclosure", "disclose_source_slices",
    "enroll_population", "id_digest", "load_verified_table", "prediction_config", "score_fleet_row",
)


def _bind() -> None:
    """Copy gate helpers after both modules have finished importing."""
    global _BOUND
    if _BOUND:
        return
    import hf_benchmark_gate as gate
    for name in _GATE_NAMES:
        globals()[name] = getattr(gate, name)
    _BOUND = True


def _json_ready(value: Any) -> Any:
    _bind()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def _write_summary(summary_dir: Path, summary: Mapping[str, Any], readme: str) -> None:
    _bind()
    summary_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(_json_ready(summary), indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    (summary_dir / "manifest.json").write_text(text, encoding="utf-8")
    (summary_dir / "README.md").write_text(readme, encoding="utf-8")


def render_dataset_card(summary: Mapping[str, Any]) -> str:
    """Print pass, evaluated, and unverified as three different numbers."""
    _bind()
    totals = summary.get("totals") or {}
    op = totals.get("operator_modeling") or {}
    step = totals.get("step_modeling") or {}
    ident = summary.get("identity") or {}
    dist = summary.get("no_data") or {}
    lines = [
        "# MindIE profiling benchmark evaluation",
        "",
        f"- Inventory captures: `{totals.get('unique_captures', 0)}` "
        f"(zero-shot `{totals.get('zero_shot_l1_l4_cells', 0)}`, fleet `{totals.get('fleet_captures', 0)}`).",
        f"- Operator boundary: pass `{op.get('pass_10pct_captures', 0)}` / "
        f"evaluated `{op.get('evaluated_captures', 0)}` / "
        f"inventory `{totals.get('unique_captures', 0)}` / "
        f"unverified `{op.get('unverified_captures', 0)}`.",
        f"- Step boundary: pass `{step.get('pass_10pct_captures', 0)}` / "
        f"evaluated `{step.get('evaluated_captures', 0)}` / "
        f"inventory `{totals.get('unique_captures', 0)}` / "
        f"unverified `{step.get('unverified_captures', 0)}`.",
        f"- Strict global pass: `{summary.get('strict_global_pass', False)}` "
        f"(inventory `{summary.get('inventory')}`).",
        f"- Source calibration counted from the structure JSON: "
        f"retained `{ident.get('retained_source_relations', 0)}`, "
        f"in_sample `{ident.get('in_sample_group', 0)}`, "
        f"not_blind `{ident.get('not_blind_group', 0)}` "
        f"(decode in_sample `{ident.get('decode_in_sample', 0)}`, "
        f"prefill in_sample `{ident.get('prefill_in_sample', 0)}`, "
        f"retrospective not_blind `{ident.get('not_blind', 0)}`).",
        f"- Stored relation disagreements: `{ident.get('stored_calibration_disagreements', 0)}`. "
        f"Phase mismatches `{ident.get('phase_mismatches', 0)}`. "
        f"Hardware mismatches `{ident.get('hardware_mismatches', 0)}`.",
    ]
    slices = summary.get("physical_slices") or {}
    if slices:
        lines.append(
            f"- Measured forward IDs `{slices.get('measured_ids', 0)}` / "
            f"ID-windows `{slices.get('id_window_rows', 0)}`. "
            f"Unique physical series `{slices.get('unique_physical_series', 0)}` / "
            f"windows `{slices.get('unique_physical_windows', 0)}` "
            "stay a separate diagnostic and do not replace that scoring population."
        )
    original = summary.get("all_original") or {}
    if original:
        enrolled = original.get("enrolled") or {}
        unknown_ids = ((original.get("strata") or {}).get("unknown") or {}).get("ids", 0)
        lines.append(
            f"- All-original ids `{original.get('id_denominator', 0)}` "
            f"(fleet `{enrolled.get('fleet_ids', 0)}`, "
            f"zero-shot `{enrolled.get('zero_cells', 0)}`), "
            f"window keys `{original.get('window_key_denominator')}`, "
            f"predictions `{original.get('predictions')}`, "
            f"missing `{original.get('missing')}`, "
            f"over `{original.get('over')}`, "
            f"within `{original.get('within')}`. "
            f"Unknown role `{unknown_ids}`. "
            f"Unresolved `{original.get('unresolved_rows', 0)}`."
        )
    lines.extend([
        f"- No-data: per-forward unknown `{dist.get('per_forward_unknown', 0)}`, "
        f"operator ms empty `{dist.get('operator_ms_empty', 0)}`, "
        f"missing artifact `{dist.get('missing_artifact', 0)}`, "
        f"client measured but not a model-step sample `{dist.get('client_not_a_step_sample', 0)}`.",
        "",
        "Suite 1 validator output is diagnostic. It is not a strict pass.",
        "Evaluated means a finite same-boundary sample. It is not a pass count.",
        "",
    ])
    return "\n".join(lines)


def validate_release(dataset_dir: Path, *, manifest: Mapping[str, Any] | None = None, simulator_name: str = "") -> list[str]:
    """Check the six advertised files, matching digests, and the current identity. Never upload."""
    _bind()
    problems: list[str] = []
    present = {}
    for rel in _ADVERTISED:
        path = dataset_dir / rel
        if not path.is_file():
            problems.append(f"missing {rel}")
            continue
        present[rel] = path.read_bytes()
    for plain_rel, gz_rel, _id, _sha, _count in _PAIRS:
        if plain_rel not in present or gz_rel not in present:
            continue
        try:
            decoded = gzip.decompress(present[gz_rel])
        except (OSError, EOFError, gzip.BadGzipFile) as exc:
            problems.append(f"{gz_rel} is not gzip: {exc}")
            continue
        if decoded != present[plain_rel]:
            problems.append(f"{plain_rel} bytes differ from decompressed {gz_rel}")
    loaded = manifest
    manifest_path = dataset_dir / "manifest.json"
    if loaded is None and manifest_path.is_file():
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"manifest unreadable: {exc}")
            loaded = None
    if isinstance(loaded, Mapping):
        files = loaded.get("files") if isinstance(loaded.get("files"), Mapping) else {}
        for rel, raw in present.items():
            if rel in {"README.md", "manifest.json"}:
                continue
            meta = files.get(rel) if isinstance(files, Mapping) else None
            digest = hashlib.sha256(raw).hexdigest()
            if not isinstance(meta, Mapping) or meta.get("sha256") != digest or int(meta.get("size_bytes") or -1) != len(raw):
                problems.append(f"manifest digest/size does not match {rel}")
        if simulator_name and loaded.get("simulator_identity") != simulator_name:
            problems.append("manifest simulator_identity is not the current simulator")
    else:
        problems.append("manifest absent")
    return problems


def _identity_report(fleet_rows: Sequence[Mapping[str, Any]], identity_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _bind()
    by_id = {str(row.get("capture_id") or ""): row for row in identity_rows}
    phase_m = hw_m = cal_m = sha_m = digest_absent = 0
    overlap = 0
    decode_in = prefill_in = not_blind = 0
    retained = in_sample_group = not_blind_group = 0
    relations: Counter[str] = Counter()
    for row in identity_rows:
        relation = _relation(row)
        relations[relation or "unspecified"] += 1
        phase = str(row.get("phase") or "")
        suite = str(row.get("suite") or "")
        if suite in _REGISTERED_SUITES:
            retained += 1
            if "in_sample" in relation:
                in_sample_group += 1
            if "not_blind" in relation:
                not_blind_group += 1
        if suite == "registered_decode" and relation == "in_sample" and phase == "decode":
            decode_in += 1
        elif suite == "registered_prefill" and relation == "in_sample" and phase == "prefill":
            prefill_in += 1
        elif relation == "retrospective_context_transfer; not_blind":
            not_blind += 1
    for row in fleet_rows:
        src = by_id.get(str(row.get("capture_id") or ""))
        if src is None:
            continue
        overlap += 1
        if str(row.get("phase") or "") != str(src.get("phase") or ""):
            phase_m += 1
        if str(row.get("hardware_tier") or "") != str(src.get("hardware_tier") or ""):
            hw_m += 1
        if _relation(row) != _relation(src):
            cal_m += 1
        src_sha = str(src.get("source_sha256") or "")
        row_sha = str(row.get("source_sha256") or "")
        if not src_sha:
            digest_absent += 1
        elif src_sha != row_sha:
            sha_m += 1
    missing_roles = {
        name: int(need) - int(relations.get(name, 0))
        for name, need in _REQUIRED_RELATIONS.items()
        if int(relations.get(name, 0)) != int(need)
    }
    return {
        "structure_rows": len(identity_rows),
        "structure_overlap": overlap,
        "phase_mismatches": phase_m,
        "hardware_mismatches": hw_m,
        "stored_calibration_disagreements": cal_m,
        "stored_source_sha_disagreements": sha_m,
        "source_digest_absent": digest_absent,
        "decode_in_sample": decode_in,
        "prefill_in_sample": prefill_in,
        "not_blind": not_blind,
        "retained_source_relations": retained,
        "in_sample_group": in_sample_group,
        "not_blind_group": not_blind_group,
        "relation_counts": dict(relations),
        "relation_census_gaps": missing_roles,
        "by_id_role": {
            cid: {"relation": _relation(src), "role": _role(src), "phase": str(src.get("phase") or ""),
                  "hardware_tier": str(src.get("hardware_tier") or ""),
                  "source_sha256": str(src.get("source_sha256") or ""),
                  "target_timing_used_to_fit": _stored_fit(src)}
            for cid, src in by_id.items()
        },
    }


def _distribution(scored: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    _bind()
    evidence, prediction, comparison = Counter(), Counter(), Counter()
    paths: dict[str, list[str]] = {}
    per_forward_unknown = operator_empty = missing_artifact = client_not_sample = native_mass = 0
    for row in scored:
        evidence[str(row.get("evidence_status") or "missing")] += 1
        prediction[str(row.get("prediction_status") or "missing")] += 1
        comparison[str(row.get("comparison") or "uncovered")] += 1
        if row.get("per_forward_window") != "measured":
            per_forward_unknown += 1
        if row.get("observed_operator_ms") in (None, {}, []):
            operator_empty += 1
        if row.get("evidence_status") in {"missing_artifact", "missing_raw_kernel_rows"}:
            missing_artifact += 1
        if row.get("client_tpot_ms") is not None or row.get("client_ttft_ms") is not None:
            if row.get("comparison") != "compared":
                client_not_sample += 1
        if row.get("native_mass_us") is not None:
            native_mass += 1
        path = str(row.get("source_path") or "")
        if path:
            paths.setdefault(path, []).append(str(row.get("capture_id") or ""))
    alias_paths = {path: ids for path, ids in paths.items() if len(ids) > 1}
    return {
        "evidence_status": dict(evidence),
        "prediction_status": dict(prediction),
        "comparison": dict(comparison),
        "per_forward_unknown": per_forward_unknown,
        "operator_ms_empty": operator_empty,
        "missing_artifact": missing_artifact,
        "client_not_a_step_sample": client_not_sample,
        "native_mass_recorded_not_scored": native_mass,
        "rows": len(scored),
        "physical_source_paths": len(paths),
        "alias_paths": len(alias_paths),
        "alias_rows": sum(len(ids) for ids in alias_paths.values()),
    }


def _progress(summary_dir: Path | None, payload: Mapping[str, Any]) -> None:
    _bind()
    if summary_dir is None:
        return
    summary_dir.mkdir(parents=True, exist_ok=True)
    (summary_dir / "progress.json").write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _finite_sample(row: Mapping[str, Any], key: str) -> bool:
    _bind()
    value = row.get(key)
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _population_pack(rows: Sequence[Mapping[str, Any]], *, comparison: str, sample: str, passed: str) -> dict[str, Any]:
    """ID counts plus the key counts N actually returned.

    ``key_matched`` stays when the group fails. ``keys_over_10pct`` is N's
    ``count_over_10pct`` summed across compared rows. It stays null when any
    compared row did not carry that count. It is never guessed from the worst error.
    """
    _bind()
    compared = [row for row in rows if row.get(comparison) == "compared" and _finite_sample(row, sample)]
    invalid = [row for row in rows if row.get(comparison) == "invalid"]
    above = [row for row in compared if float(row[sample]) > 0.10]
    ok = [row for row in compared if row.get(passed) and float(row[sample]) <= 0.10]
    errors = [float(row[sample]) for row in compared]
    over_values = [row.get("keys_over_10pct") for row in compared]

    def _ints(key: str) -> int | None:
        if not rows:
            return 0
        values = [row.get(key) for row in rows]
        if any(type(value) is not int for value in values):
            return None
        return sum(values)

    return {
        "rows": len(rows),
        "compared": len(compared),
        "passed_10pct": len(ok),
        "above_10pct": len(above),
        "invalid": len(invalid),
        "unknown": len(rows) - len(compared) - len(invalid),
        "max_error": max(errors) if errors else None,
        "key_denominator": _ints("key_denominator"),
        "key_matched": _ints("key_matched"),
        "key_missing": _ints("key_missing"),
        "key_invalid": _ints("key_invalid"),
        "keys_over_10pct": sum(over_values) if over_values and all(isinstance(value, int) for value in over_values) else None,
    }


def _stratum_name(row: Mapping[str, Any]) -> str:
    """Same rule as the original-account helper. Unspecified stays unknown."""
    _bind()
    return _original_account.stratum_name(row)
def _hardware_still_missing(row: Mapping[str, Any], evidence: Mapping[str, Any] | None) -> bool:
    """A blank HF tier is resolved when the launch preflight mapped to A2/A3/A5."""
    _bind()
    if str(row.get("hardware_tier") or "") in {"A2", "A3", "A5"}:
        return False
    if not isinstance(evidence, Mapping) or not evidence.get("joined"):
        return True
    if evidence.get("hardware_tiers"):
        return False
    return str(evidence.get("hardware_tier") or "") not in {"A2", "A3", "A5"}


def _recovered_tier(row: Mapping[str, Any], evidence: Mapping[str, Any] | None) -> str:
    _bind()
    stored = str(row.get("hardware_tier") or "")
    if stored in {"A2", "A3", "A5"}:
        return stored
    if isinstance(evidence, Mapping):
        tier = str(evidence.get("hardware_tier") or "")
        if tier in {"A2", "A3", "A5"}:
            return tier
    return ""


def singleton_request_ttft(raw: Mapping[str, Any], phase: str) -> dict[str, Any]:
    """TTFT is one request only when the producer recorded exactly that request.

    A decode TPOT mean, an ITL, and a multi-request mean are not this pair.
    The observed value is the stream's own TTFT, and only when it equals the
    producer mean. No archived within-10% count is reused.
    """
    _bind()
    streams = [item for item in (raw.get("streams") or ()) if isinstance(item, Mapping)]
    failed = raw.get("failed")
    failed_streams = raw.get("failed_streams") or []
    no_failures = failed in (None, 0, False) and not failed_streams
    one_success = raw.get("success") in (1, True)
    if str(phase) != "prefill":
        return {"eligible": False, "reason": "tpot_not_a_per_step_boundary", "streams": len(streams), "observed_ms": None}
    if not (one_success and no_failures and len(streams) == 1 and streams[0].get("ok") is True):
        return {"eligible": False, "reason": "request_population_not_singleton", "streams": len(streams), "observed_ms": None}
    try:
        observed = float(streams[0].get("ttft_s")) * 1000.0
        mean = float(raw.get("ttft_mean_s")) * 1000.0
    except (TypeError, ValueError):
        return {"eligible": False, "reason": "singleton_ttft_absent", "streams": 1, "observed_ms": None}
    if not (math.isfinite(observed) and observed > 0 and math.isfinite(mean) and abs(observed - mean) <= 1e-3):
        return {"eligible": False, "reason": "ttft_mean_is_not_the_single_request", "streams": 1, "observed_ms": None}
    return {"eligible": True, "reason": "", "streams": 1, "observed_ms": observed, "key": "request:0"}


_L4_PUBLIC_FIELDS = (
    "source_raw", "source_config", "source_config_sha256", "source_deploy_sha256",
    "source_weight_dir", "source_case_dir", "require_source",
    "header_binding", "header_source_note",
    "producer_rack", "producer_sha256", "hardware_family", "hardware_basis",
    "request_ttft_boundaries", "request_ttft_absent", "request_ttft_unobserved",
    "request_ttft_orphans", "request_ttft_incompatible", "request_scalar_withheld",
    "tpot_domain", "l4_eligible", "per_key_errors", "producer_clock_status",
    "forecast_status", "forecast_reason", "forecast_assumptions",
    "request_forecasts", "forecast_unbound_keys",
)


def score_l4_bundle(
    row: Mapping[str, Any],
    bundle: Mapping[str, Any],
    *,
    tier: str = "",
) -> dict[str, Any]:
    """Score one zero-shot cell from the public pair bundle.

    A P6 interface is the observation. The singleton helper's ineligibility
    reason does not replace the request keys. Prefill concurrency 1 may carry
    the one scalar from ``predict_cell``. Any wider cell keeps those keys
    missing unless ``boundary_samples`` names them.
    """
    _bind()
    cell_id = str(row.get("cell_id") or row.get("capture_id") or "")
    phase = str(row.get("phase") or "")
    interface = bundle.get("interface") if isinstance(bundle.get("interface"), Mapping) else None
    families: list[str] = []
    bases: list[str] = []
    if interface is not None:
        cell = interface.get("cell") if isinstance(interface.get("cell"), Mapping) else {}
        families = [str(item) for item in cell.get("hardware_families") or () if str(item)]
        bases = [str(item) for item in cell.get("hardware_basis") or () if str(item)]
        if not tier:
            mapped: list[str] = []
            for family in families:
                got, _sku = _sku_tier({"sku": family})
                if got and got not in mapped:
                    mapped.append(got)
            if len(mapped) == 1:
                tier = mapped[0]
    if interface is not None:
        prediction = dict(bundle.get("prediction") or {})
        if tier and not str(prediction.get("hardware_tier") or ""):
            prediction["hardware_tier"] = tier
        scored = score_client_request_interface(interface, prediction, hardware_tier=tier)
        scored["l4_eligible"] = bool(bundle.get("eligible"))
        if families:
            scored["hardware_family"] = families
        if bases:
            scored["hardware_basis"] = bases
    elif (bundle.get("eligible")
          and isinstance(bundle.get("observation"), Mapping)
          and isinstance(bundle.get("prediction"), Mapping)):
        scored = score_fleet_row(
            {"capture_id": cell_id, "suite": "zero_shot", "phase": phase, "hardware_tier": tier},
            _stamp_hardware(bundle["observation"], tier),
            _stamp_hardware(bundle["prediction"], tier),
        )
        scored["l4_eligible"] = True
        scored["hardware_tier"] = tier or scored.get("hardware_tier") or ""
    else:
        scored = _l4_hold(
            cell_id, phase, tier, str(bundle.get("reason") or "observation_absent"),
            int(bundle.get("streams") or 0), eligible=bool(bundle.get("eligible")),
        )
    if tier:
        scored["hardware_tier"] = tier
    for name in _L4_PUBLIC_FIELDS:
        if name in bundle and name not in {"producer_rack", "producer_sha256", "tpot_domain", "l4_eligible"}:
            scored[name] = bundle.get(name)
    notes = bundle.get("notes") or ()
    note_text = " ".join(str(item) for item in notes) if isinstance(notes, (list, tuple)) else str(notes or "")
    if note_text:
        scored["coverage_only"] = _coverage_only(note_text, "")
    return scored


def _stamp_hardware(payload: Mapping[str, Any], tier: str) -> dict[str, Any]:
    _bind()
    out = dict(payload)
    if not tier:
        return out
    if "capture" in out or "measurements" in out:
        capture = dict(out.get("capture") or {})
        if not str(capture.get("hardware_tier") or ""):
            capture["hardware_tier"] = tier
        out["capture"] = capture
    if not str(out.get("hardware_tier") or ""):
        out["hardware_tier"] = tier
    return out


def _l4_hold(cell_id: str, phase: str, tier: str, reason: str, streams: int, *, eligible: bool) -> dict[str, Any]:
    _bind()
    return {
        "capture_id": cell_id, "suite": "zero_shot", "phase": phase, "enrolled_phase": phase,
        "native_phase": "", "hardware_tier": tier, "boundary_scope": "request_l4",
        "prediction_boundary": "native_client_request", "comparison": "uncovered",
        "comparison_reason": reason, "passed_10pct": False, "sample": None,
        "n_samples": streams, "matched": 0, "missing_keys": [], "max_error": None, "over_limit": None,
        "key_denominator": streams, "key_matched": 0, "key_missing": streams, "key_invalid": 0,
        "keys_over_10pct": None, "group_passed_10pct": False, "standalone_comparison": "",
        "standalone_reason": "", "standalone_passed_10pct": False, "standalone_max_error": None,
        "operator_comparison": "uncovered", "operator_reason": "not_an_operator_boundary",
        "operator_passed_10pct": False, "coverage_only": False, "l4_eligible": eligible,
        "prediction_status": "missing" if eligible else "not_a_singleton",
    }


def _semantic_hold(rows_n: int, reason: str) -> dict[str, Any]:
    """L1/L2/L3 validator quotients are not a sample population."""
    _bind()
    return {
        "status": "not_a_sample", "reason": reason, "rows": rows_n, "compared": 0,
        "passed_10pct": 0, "above_10pct": 0, "invalid": 0, "unknown": rows_n,
        "max_error": None, "key_denominator": 0, "key_matched": 0, "key_missing": 0,
        "key_invalid": 0, "keys_over_10pct": None,
    }


def evaluate(
    dataset_dir: Path,
    *,
    strict_10pct: bool,
    inventory: str,
    summary_dir: Path | None,
    identity_builder: Callable[[], Sequence[Mapping[str, Any]]] | None,
    simulator_name: str,
    predict: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    observe: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    run_validation: Callable[..., Mapping[str, Any]] | None,
    configure_roots: Callable[..., None] | None = None,
    data_roots: Sequence[Path] = (),
    file_meta: Callable[[Path], Mapping[str, Any]] | None = None,
    build_scoreboard: Callable[..., Mapping[str, Any]] | None = None,
    redact_hits: Callable[[str], set[str]] | None = None,
    deadline_s: float | None = None,
    zero_shot_timetables: Callable[[Mapping[str, Any]], Any] | None = None,
    zero_shot_requests: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Score the dataset in place in memory. Does not write the source jsonl.

    ``deadline_s`` is an explicit job budget checked between rows. It is not
    a per-row alarm. None scores every row. A budget that expires leaves the
    summary incomplete and cannot set a global pass.
    """
    _bind()
    mode = inventory if inventory in {"full", "targeted"} else "targeted"
    if strict_10pct and mode != "targeted":
        mode = "full"
    tables = {}
    content_sha = {}
    for plain_rel, gz_rel, id_key, expect_sha, expect_n in _PAIRS:
        rows, digest = load_verified_table(dataset_dir / plain_rel, dataset_dir / gz_rel)
        ids = [str(row.get(id_key) or "") for row in rows]
        tables[plain_rel] = rows
        content_sha[plain_rel] = digest
        unique = len(set(ids))
        digest_ok = id_digest(ids) == expect_sha and unique == len(ids) == expect_n and all(ids)
        content_sha[id_key] = {"sha256": id_digest(ids), "rows": len(ids), "unique": unique, "matches_original": digest_ok}
    zs_rows = tables["data/zero_shot_l1_l4_cells.jsonl"]
    fleet_rows = tables["data/fleet_captures.jsonl"]
    identity_ok = bool(content_sha["cell_id"]["matches_original"] and content_sha["capture_id"]["matches_original"])
    if mode == "full" and strict_10pct and not identity_ok:
        raise ValueError(
            "Strict <=10% gate failed: population identity "
            f"zs={content_sha['cell_id']} fleet={content_sha['capture_id']}"
        )
    zs_evidence: dict[str, dict[str, Any]] = {}
    if configure_roots is not None and mode == "full":
        configure_roots(data_roots=tuple(data_roots) or None)
    observe_s = predict_s = 0.0
    dependent = 0
    scored: list[dict[str, Any]] = []
    slice_records: list[dict[str, Any]] = []
    per_id = None
    if summary_dir is not None:
        summary_dir.mkdir(parents=True, exist_ok=True)
        per_id = (summary_dir / "per_id.jsonl").open("w", encoding="utf-8")
    _progress(summary_dir, {"fleet_scored": 0, "fleet_total": len(fleet_rows), "incomplete": True, "phase": "score"})
    job_started = time.monotonic()
    incomplete = False
    identity: dict[str, Any] = {
        "decode_in_sample": None, "prefill_in_sample": None, "not_blind": None,
        "in_sample_group": None, "not_blind_group": None, "retained_source_relations": None,
        "phase_mismatches": None, "hardware_mismatches": None, "stored_calibration_disagreements": None,
    }
    _PER_ID_KEYS = (
        "capture_id", "suite", "phase", "enrolled_phase", "native_phase", "hardware_tier",
        "calibration_role", "evaluation_relation", "coverage_only", "target_timing_used_to_fit",
        "model_target_timing_used_to_fit",
        "slice_role_inherited", "slice_role_source_id", "boundary_scope",
        "population_boundary", "population_status",
        "source_path", "evidence_status", "prediction_status", "prediction_boundary",
        "comparison", "comparison_reason", "passed_10pct",
        "n_samples", "matched", "missing_keys", "max_error", "over_limit",
        "key_denominator", "key_matched", "key_missing", "key_invalid", "keys_over_10pct", "group_passed_10pct",
        "standalone_comparison", "standalone_reason", "standalone_passed_10pct", "standalone_max_error",
        "operator_comparison", "operator_reason", "operator_passed_10pct", "sample",
    )
    for index, row in enumerate(fleet_rows, start=1):
        if deadline_s is not None and (time.monotonic() - job_started) >= float(deadline_s):
            incomplete = True
            break
        cfg = prediction_config(row)
        started = time.perf_counter()
        try:
            observation = observe(cfg)
        except TimeoutError:
            raise
        except Exception as exc:
            observation = {"evidence_status": "observer_failed", "measurements": {}, "source": {}, "diagnostics": [str(exc)]}
        observe_s += time.perf_counter() - started
        started = time.perf_counter()
        try:
            prediction = predict(cfg)
        except TimeoutError:
            raise
        except Exception as exc:
            prediction = {"status": "predictor_failed", "diagnostics": [str(exc)]}
        predict_s += time.perf_counter() - started
        viewed = observation if isinstance(observation, Mapping) else {}
        item = score_fleet_row(row, viewed, prediction if isinstance(prediction, Mapping) else {})
        slice_records.append(_source_slices.slice_record(row, viewed))
        graded = (item.get("comparison") == "compared" or item.get("operator_comparison") == "compared"
                  or item.get("standalone_comparison") == "compared")
        if graded:
            try:
                again = observe(_prediction_mutant(cfg))
            except Exception:
                again = None
            if again is None or _observation_signature(observation) != _observation_signature(again):
                dependent += 1
                if item.get("boundary_scope") == "standalone":
                    item["standalone_comparison"] = "invalid"
                    item["standalone_reason"] = "observation_depends_on_predictor"
                    item["standalone_passed_10pct"] = False
                    item["standalone_max_error"] = float("nan")
                    item["group_passed_10pct"] = False
                else:
                    item["comparison"] = "invalid"
                    item["comparison_reason"] = "observation_depends_on_predictor"
                    item["passed_10pct"] = False
                    item["sample"] = float("nan")
                    item["group_passed_10pct"] = False
                item["operator_comparison"] = "invalid"
                item["operator_reason"] = "observation_depends_on_predictor"
                item["operator_passed_10pct"] = False
                item["operator_sample"] = float("nan")
        scored.append(item)
        if per_id is not None:
            per_id.write(json.dumps(_json_ready({key: item.get(key) for key in _PER_ID_KEYS}), sort_keys=True) + "\n")
            if index == 1 or index % 25 == 0:
                per_id.flush()
        if summary_dir is not None and (index == 1 or index % 25 == 0):
            _progress(summary_dir, {"phase": "score", "fleet_scored": index, "fleet_total": len(fleet_rows),
                                    "incomplete": True, "observe_s": round(observe_s, 3),
                                    "predict_s": round(predict_s, 3)})
    if len(scored) != len(fleet_rows):
        incomplete = True
    if per_id is not None:
        per_id.close()
    identity_source_rows: list[Mapping[str, Any]] = []
    if identity_builder is not None:
        _progress(summary_dir, {"phase": "source_relation", "incomplete": True,
                                "fleet_scored": len(scored), "fleet_total": len(fleet_rows)})
        identity_source_rows = list(identity_builder())
        identity = _identity_report(fleet_rows, identity_source_rows)
        source_by_id = {str(key): value for key, value in (identity.get("by_id_role") or {}).items()}
        identity.pop("by_id_role", None)
        for item in scored:
            _apply_source_role(item, source_by_id.get(item["capture_id"]))
    slice_report = disclose_source_slices(slice_records, identity_source_rows)
    for item in scored:
        apply_slice_disclosure(item, slice_report["by_id"].get(item["capture_id"]))
    if summary_dir is not None:
        with (summary_dir / "per_id.jsonl").open("w", encoding="utf-8") as rewritten:
            for item in scored:
                rewritten.write(json.dumps(_json_ready({key: item.get(key) for key in _PER_ID_KEYS}),
                                           sort_keys=True) + "\n")
    dist = _distribution(scored)
    dist["observation_depends_on_predictor"] = dependent
    if mode == "full" and zero_shot_timetables is not None:
        for seen, row in enumerate(zs_rows, start=1):
            cell_id = str(row.get("cell_id") or "")
            zs_evidence[cell_id] = _evidence_from_timetables(zero_shot_timetables(row))
            if summary_dir is not None and seen % 25 == 0:
                _progress(summary_dir, {"phase": "zero_shot_windows", "cells": seen,
                                        "cells_total": len(zs_rows), "incomplete": True,
                                        "fleet_scored": len(scored), "fleet_total": len(fleet_rows)})
    l4_rows: list[dict[str, Any]] = []
    # Targeted and full both score the zero-shot rows that this dataset actually holds.
    # Forward-window timetables stay full-only. An empty fleet file is not the 6606 run.
    if zero_shot_requests is not None:
        l4_path = (summary_dir / "zs_l4_per_id.jsonl").open("w", encoding="utf-8") if summary_dir is not None else None
        for seen, row in enumerate(zs_rows, start=1):
            if deadline_s is not None and (time.monotonic() - job_started) >= float(deadline_s):
                incomplete = True
                break
            cell_id = str(row.get("cell_id") or "")
            phase = str(row.get("phase") or "")
            tier = _recovered_tier(row, zs_evidence.get(cell_id))
            try:
                bundle = zero_shot_requests(row) or {}
            except TimeoutError:
                raise
            except Exception as exc:
                bundle = {"eligible": False, "reason": f"l4_pair_failed:{type(exc).__name__}", "streams": 0}
            scored_l4 = score_l4_bundle(
                {"cell_id": cell_id, "phase": phase, "hardware_tier": tier},
                bundle,
                tier=tier,
            )
            l4_rows.append(scored_l4)
            if l4_path is not None:
                payload = {key: scored_l4.get(key) for key in _PER_ID_KEYS}
                for key in _L4_PUBLIC_FIELDS:
                    if key in scored_l4:
                        payload[key] = scored_l4.get(key)
                l4_path.write(json.dumps(_json_ready(payload), sort_keys=True) + "\n")
                if seen == 1 or seen % 25 == 0:
                    l4_path.flush()
            if summary_dir is not None and (seen == 1 or seen % 25 == 0):
                _progress(summary_dir, {"phase": "zero_shot_l4", "cells": seen, "cells_total": len(zs_rows),
                                        "incomplete": True, "fleet_scored": len(scored), "fleet_total": len(fleet_rows)})
        if l4_path is not None:
            l4_path.close()
        if len(l4_rows) != len(zs_rows):
            incomplete = True
    zs_hw_missing = sum(1 for row in zs_rows
                        if _hardware_still_missing(row, zs_evidence.get(str(row.get("cell_id") or ""))))
    zs_gaps = [(str(row.get("cell_id") or ""), _zs_gaps(row, zs_evidence.get(str(row.get("cell_id") or "")))) for row in zs_rows]
    zs_unverified = [cell_id for cell_id, gaps in zs_gaps if gaps]
    # Validator quotients change when layers or decode_steps change. They are not L4 samples.
    del run_validation
    zs_diagnostic = {"status": "not_a_sample", "zs_pass_n": 0,
                     "reason": "validator_errors_scale_with_prediction_layers_and_decode_steps",
                     "l4_request": "not_taken_from_validator"}
    forward_rows = [row for row in scored if row.get("boundary_scope") == "forward_body"]
    request_rows = [row for row in scored if row.get("boundary_scope") == "request_l4"] + l4_rows
    standalone_rows = [row for row in scored if row.get("boundary_scope") == "standalone"]
    unknown_rows = [row for row in scored if row.get("boundary_scope") == "unknown"]
    forward_pack = _population_pack(forward_rows, comparison="comparison", sample="sample", passed="passed_10pct")
    request_pack = _population_pack(request_rows, comparison="comparison", sample="sample", passed="passed_10pct")
    standalone_pack = _population_pack(standalone_rows, comparison="standalone_comparison",
                                       sample="standalone_max_error", passed="standalone_passed_10pct")
    unknown_pack = _population_pack(unknown_rows, comparison="comparison", sample="sample", passed="passed_10pct")
    blind_request = _population_pack(
        [row for row in request_rows if not row.get("coverage_only")],
        comparison="comparison", sample="sample", passed="passed_10pct")
    blind_standalone = _population_pack(
        [row for row in standalone_rows if not row.get("coverage_only")],
        comparison="standalone_comparison", sample="standalone_max_error", passed="standalone_passed_10pct")
    coverage_rows = [row for row in scored if row.get("coverage_only")]
    blind_forward = _population_pack(
        [row for row in forward_rows if not row.get("coverage_only")],
        comparison="comparison", sample="sample", passed="passed_10pct")
    coverage_forward = _population_pack(
        [row for row in forward_rows if row.get("coverage_only")],
        comparison="comparison", sample="sample", passed="passed_10pct")
    op_compared = [row for row in scored if row.get("operator_comparison") == "compared"
                   and _finite_sample(row, "operator_sample")]
    op_invalid = [row for row in scored if row.get("operator_comparison") == "invalid"]
    op_passed = [row for row in op_compared if row.get("operator_passed_10pct") and float(row["operator_sample"]) <= 0.10]
    performance = [row for row in scored if not row.get("coverage_only")]
    # Coverage rows stay out of blind accuracy. Their measured forward windows
    # still count here, so a no-prediction body is not an uncovered_step of 0.
    uncovered_step = [row for row in scored
                      if row.get("boundary_scope") == "forward_body"
                      and row.get("comparison") != "compared"]
    uncovered_operator = [row for row in performance
                          if row.get("boundary_scope") != "standalone"
                          and row.get("operator_comparison") not in {"compared", "unavailable"}]
    reasons: list[str] = []
    original_account = all_original_account(enroll_population(scored, fleet_rows, l4_rows, zs_rows))
    if mode == "full":
        if incomplete:
            reasons.append(f"incomplete={len(scored)}/{len(fleet_rows)}")
        if not identity_ok:
            reasons.append("population_identity")
        if identity.get("phase_mismatches"):
            reasons.append(f"phase_mismatches={identity['phase_mismatches']}")
        if identity.get("hardware_mismatches"):
            reasons.append(f"hardware_mismatches={identity['hardware_mismatches']}")
        if any(row.get("attribution_mismatch") for row in scored):
            reasons.append(f"row_attribution_mismatch={sum(bool(row.get('attribution_mismatch')) for row in scored)}")
        # Stored labels are reconciled to the source relation. The count stays in the summary.
        if identity.get("relation_census_gaps"):
            reasons.append(f"relation_census_gaps={identity['relation_census_gaps']}")
        if (identity.get("in_sample_group") != 72
                or identity.get("not_blind_group") != 91
                or identity.get("retained_source_relations") != 306):
            reasons.append(
                "calibration_source="
                f"{identity.get('in_sample_group')}/{identity.get('not_blind_group')}"
                f"/{identity.get('retained_source_relations')}"
            )
        if identity.get("stored_source_sha_disagreements"):
            reasons.append(f"source_digest_mismatch={identity.get('stored_source_sha_disagreements')}")
        if uncovered_step or len(scored) != len(fleet_rows):
            reasons.append(f"uncovered_step={len(uncovered_step)}")
        if uncovered_operator:
            reasons.append(f"uncovered_operator={len(uncovered_operator)}")
        step_bad = blind_forward["invalid"] + blind_forward["above_10pct"]
        blind_ops = [row for row in op_compared if not row.get("coverage_only") and row.get("boundary_scope") != "standalone"]
        blind_op_invalid = [row for row in op_invalid if not row.get("coverage_only") and row.get("boundary_scope") != "standalone"]
        op_bad = len(blind_op_invalid) + sum(float(row["operator_sample"]) > 0.10 for row in blind_ops)
        if step_bad or op_bad or dependent:
            reasons.append(f"above_10_or_non_finite step={step_bad} operator={op_bad} dependent={dependent}")
        if blind_request["above_10pct"] or blind_request["invalid"]:
            reasons.append(
                f"l4_above_10_or_non_finite above={blind_request['above_10pct']} invalid={blind_request['invalid']}"
            )
        if blind_standalone["above_10pct"] or blind_standalone["invalid"]:
            reasons.append(
                "standalone_above_10_or_non_finite "
                f"above={blind_standalone['above_10pct']} invalid={blind_standalone['invalid']}"
            )
        if blind_standalone["unknown"]:
            reasons.append(f"standalone_uncovered={blind_standalone['unknown']}")
        l4_eligible_gap = [row for row in l4_rows if row.get("l4_eligible") and row.get("comparison") != "compared" and not row.get("coverage_only")]
        if l4_eligible_gap:
            reasons.append(f"l4_singleton_uncovered={len(l4_eligible_gap)}")
        if zs_hw_missing:
            reasons.append(f"zs_hardware_unverified={zs_hw_missing}")
        gap_hist: Counter[str] = Counter()
        for _cell_id, gaps in zs_gaps:
            gap_hist.update(gaps)
        if gap_hist:
            reasons.append("zs_gaps=" + ",".join(f"{key}:{gap_hist[key]}" for key in sorted(gap_hist)))
        coverage_over = (original_account.get("strata") or {}).get("coverage", {}).get("over")
        if coverage_over:
            reasons.append(f"coverage_keys_over_10pct={coverage_over}")
        pending_original = int((original_account.get("original_cells") or {}).get("pending") or 0)
        if pending_original:
            reasons.append(f"original_pending={pending_original}")
        if original_account.get("target_ambiguous"):
            reasons.append(f"original_target_ambiguous={original_account.get('target_ambiguous')}")
        if original_account.get("global_unresolved"):
            unresolved = original_account.get("unresolved") or {}
            reasons.append(
                "unresolved=" + ",".join(f"{kind}:{unresolved.get(kind, 0)}" for kind in _UNRESOLVED_KINDS)
            )
    strict_global_pass = mode == "full" and strict_10pct and not reasons
    if mode == "targeted":
        strict_global_pass = False
    inventory_n = len(zs_rows) + len(fleet_rows)
    step_eval, step_pass = forward_pack["compared"], forward_pack["passed_10pct"]
    op_eval, op_pass = len(op_compared), len(op_passed)
    # Validator output is not a scoreboard sample. Placement tests call the scoreboard directly.
    board = build_scoreboard(zs_rows, {}, fleet_rows) if build_scoreboard else {}
    files = {}
    if file_meta is not None:
        for rel in _ADVERTISED:
            path = dataset_dir / rel
            if path.is_file() and rel not in {"README.md", "manifest.json"}:
                files[rel] = dict(file_meta(path))
    summary = {
        "schema": "mindie-sim-profiling-bench/1",
        "simulator_identity": simulator_name,
        "inventory": mode,
        "incomplete": bool(incomplete),
        "strict_10pct": bool(strict_10pct),
        "strict_global_pass": bool(strict_global_pass),
        "failure_reasons": reasons,
        "all_original": original_account,
        "identity": identity,
        "physical_slices": slice_report["cohort"],
        "id_census": {"cell_id": content_sha["cell_id"], "capture_id": content_sha["capture_id"]},
        "content_sha256": {key: value for key, value in content_sha.items() if key.startswith("data/")},
        "no_data": dist,
        "timings_s": {"observe": round(observe_s, 3), "predict": round(predict_s, 3)},
        "totals": {
            "unique_captures": inventory_n,
            "zero_shot_l1_l4_cells": len(zs_rows),
            "fleet_captures": len(fleet_rows),
            "operator_evaluated_captures": op_eval,
            "step_evaluated_captures": step_eval,
            "operator_modeling": {
                "evaluated_captures": op_eval,
                "pass_10pct_captures": op_pass,
                "unverified_captures": inventory_n - op_eval,
                "pass_rate_10pct": (op_pass / inventory_n) if inventory_n else 0.0,
            },
            "step_modeling": {
                "evaluated_captures": step_eval,
                "pass_10pct_captures": step_pass,
                "unverified_captures": inventory_n - step_eval,
                "pass_rate_10pct": (step_pass / inventory_n) if inventory_n else 0.0,
            },
            "structural_inference": {
                "evaluated_captures": 0, "all_4_pass": 0, "crashes": 0,
                "unverified_captures": inventory_n, "pass_rate": 0.0,
            },
            "zs_pass_n": 0,
            "zs_unverified": len(zs_unverified),
            "zs_hardware_unverified": zs_hw_missing,
        },
        "fleet_boundary": {
            "scored_rows": len(scored),
            "step_compared": step_eval,
            "step_passed_10pct": step_pass,
            "operator_compared": op_eval,
            "operator_passed_10pct": op_pass,
            "uncovered_step": len(uncovered_step),
            "uncovered_forward_keys": (
                sum(row["key_missing"] for row in uncovered_step)
                if all(type(row.get("key_missing")) is int for row in uncovered_step) else None
            ),
            "uncovered_operator": len(uncovered_operator),
            "step_invalid": forward_pack["invalid"],
            "operator_invalid": len(op_invalid),
            "coverage_only": len(coverage_rows),
        },
        "scopes": {
            "forward_body": forward_pack,
            "request_l4": request_pack,
            "standalone": standalone_pack,
            "unknown": unknown_pack,
        },
        "scheduler": {
            "forward": forward_pack,
            "step": {**unknown_pack,
                     "status": "not_a_sample" if not any(row.get("comparison") == "compared" for row in unknown_rows) else "scored",
                     "reason": "no_measured_source_boundary"},
            "unknown": unknown_pack,
            "L1": _semantic_hold(len(zs_rows), "validator_quotients_are_not_samples"),
            "L2": _semantic_hold(len(zs_rows), "validator_quotients_are_not_samples"),
            "L3": _semantic_hold(len(zs_rows), "validator_quotients_are_not_samples"),
            "L4": request_pack,
            "standalone": standalone_pack,
        },
        "blind_accuracy": {
            "forward_body": blind_forward,
            "request_l4": blind_request,
            "standalone": blind_standalone,
        },
        "coverage_stratum": {
            "rows": len(coverage_rows),
            "forward_body": coverage_forward,
        },
        "zero_shot_join": {
            "cells": len(zs_rows),
            "joined": sum(1 for item in zs_evidence.values() if item.get("joined")),
            "measured_traces": sum(int(item.get("measured_traces") or 0) for item in zs_evidence.values()),
            "missing_source": sum(int(item.get("missing_source") or 0) for item in zs_evidence.values()),
            "identified_windows": sum(int(item.get("identified_windows") or 0) for item in zs_evidence.values()),
            "forward_count": sum(int(item.get("forward_count") or 0) for item in zs_evidence.values()),
            "hardware_resolved": sum(1 for item in zs_evidence.values() if item.get("hardware_tiers")
                                     or item.get("hardware_tier") in {"A2", "A3", "A5"}),
            "rank_sha_count": sum(int(item.get("rank_sha_count") or 0) for item in zs_evidence.values()),
            "l4_request_on_timetable": sum(1 for item in zs_evidence.values() if item.get("l4_request_on_timetable")),
            "unknown_core_operators": sum(int(item.get("unknown_core_operators") or 0) for item in zs_evidence.values()),
            "named_core_operators": sum(int(item.get("named_core_operators") or 0) for item in zs_evidence.values()),
        },
        "zero_shot_diagnostic": {
            "zs_pass_n": 0,
            "reason": zs_diagnostic.get("reason") if isinstance(zs_diagnostic, Mapping) else "withheld",
            "status": zs_diagnostic.get("status") if isinstance(zs_diagnostic, Mapping) else "not_run",
            "coverage": zs_diagnostic.get("coverage") if isinstance(zs_diagnostic, Mapping) else {},
        },
        "unified_7337_scoreboard": board,
        "files": files,
    }
    readme = render_dataset_card(summary)
    blob = json.dumps(_json_ready(summary), ensure_ascii=False) + readme
    if redact_hits is not None and (hits := redact_hits(blob)):
        reasons.append(f"redaction={sorted(hits)}")
        strict_global_pass = False
        summary["failure_reasons"] = reasons
        summary["strict_global_pass"] = False
        readme = render_dataset_card(summary)
    if summary_dir is not None:
        _write_summary(summary_dir, summary, readme)
        _progress(summary_dir, {"done": not incomplete, "incomplete": incomplete,
                                "fleet_scored": len(scored), "fleet_total": len(fleet_rows),
                                "strict_global_pass": strict_global_pass, "reasons": reasons,
                                "observe_s": round(observe_s, 3), "predict_s": round(predict_s, 3)})
    if strict_10pct and mode == "full" and not strict_global_pass:
        raise ValueError("Strict <=10% gate failed: " + ", ".join(reasons))
    return summary
