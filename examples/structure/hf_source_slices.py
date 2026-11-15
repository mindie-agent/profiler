"""Role of one physical forward slice.

A slice is the verified raw kernel and its per-forward key windows. The
receipt must verify those bytes; two receipt files for the same kernel and
the same windows are one slice. The same bytes at another phase or another
window set are a different slice. The relation is the earliest actual
calibration on that slice. ``zero_shot_piecewise_recomputed`` is a later
label, not that calibration. Alias rows keep their own capture ids. Unique
physical series are a diagnostic and are not a smaller scoring population.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

# A stored recompute label. It does not establish the calibration of a slice.
_RECOMPUTED_LABEL = "zero_shot_piecewise_recomputed"


def _sha_text(value: Any) -> str:
    text = str(value or "").lower()
    if len(text) == 64 and all(ch in "0123456789abcdef" for ch in text):
        return text
    return ""


def _resolved(path: Any) -> str:
    text = str(path or "")
    if not text:
        return ""
    try:
        return str(Path(text).resolve())
    except OSError:
        return text


def _actual_calibration(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """A source calibration record. The recomputed heldout label is not one."""
    if not isinstance(row, Mapping):
        return None
    cal = row.get("source_calibration")
    if not isinstance(cal, Mapping):
        return None
    relation = str(cal.get("evaluation_relation") or "")
    if not relation or relation == _RECOMPUTED_LABEL:
        return None
    fitted = cal.get("target_timing_used_to_fit")
    if not isinstance(fitted, bool):
        fitted = row.get("target_timing_used_to_fit")
    if not isinstance(fitted, bool):
        fitted = None
    role = str(row.get("calibration_role") or cal.get("calibration_role") or relation)
    return {
        "evaluation_relation": relation,
        "calibration_role": role,
        "target_timing_used_to_fit": fitted,
    }


def _observed_calibration(observation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """E4 verified source declaration for this exact raw/scope; no sibling needed."""
    window = (observation or {}).get("measurements", {}).get("per_forward_window") if isinstance(observation, Mapping) else None
    if not isinstance(window, Mapping):
        return None
    evaluation = window.get("evaluation") if isinstance(window.get("evaluation"), Mapping) else {}
    declaration = evaluation.get("source_declaration") if isinstance(evaluation.get("source_declaration"), Mapping) else {}
    if declaration.get("source_path_listed") is not True or declaration.get("target_timing_used_to_fit") is not True:
        return None
    relation = str(declaration.get("evaluation_relation") or "")
    if not relation or relation == _RECOMPUTED_LABEL:
        return None
    return {"evaluation_relation": relation, "calibration_role": relation,
            "target_timing_used_to_fit": True, "source_file_sha256": declaration.get("source_file_sha256")}


def _window_hashes(frames: Sequence[Mapping[str, Any]]) -> tuple[str, str] | None:
    """Exact key set and key windows. Phase, rank, device, and forward id are the key."""
    keys = []
    pairs = []
    phases: set[str] = set()
    for frame in frames:
        if not isinstance(frame, Mapping):
            return None
        rank = frame.get("rank_id")
        device = frame.get("device_id")
        phase = frame.get("phase")
        key = (
            phase,
            "" if rank is None else str(rank),
            "" if device is None else str(device),
            frame.get("forward_id"),
        )
        keys.append(key)
        pairs.append((key, frame.get("start_ns"), frame.get("end_ns")))
        phases.add("" if phase is None else str(phase))
    if len(phases) != 1 or "" in phases:
        return None
    try:
        ordered_keys = sorted(keys)
        ordered_pairs = sorted(pairs)
    except TypeError:
        return None
    key_hash = hashlib.sha256()
    window_hash = hashlib.sha256()
    for key in ordered_keys:
        key_hash.update(json.dumps(key, separators=(",", ":")).encode() + b"\n")
    for key, start, end in ordered_pairs:
        window_hash.update(
            json.dumps(key, separators=(",", ":")).encode()
            + b"\t" + str(start).encode() + b"\t" + str(end).encode() + b"\n"
        )
    return key_hash.hexdigest(), window_hash.hexdigest()


def slice_basis(observation: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Verified kernel + receipt + one per-forward scope. Missing any part does not join."""
    if not isinstance(observation, Mapping):
        return None
    window = (observation.get("measurements") or {}).get("per_forward_window")
    if not isinstance(window, Mapping) or window.get("status") != "measured":
        return None
    if window.get("raw_digest_verified") is not True:
        return None
    raw_sha = _sha_text(window.get("raw_sha256"))
    declared = _sha_text(window.get("source_sha256"))
    if not raw_sha or raw_sha != declared:
        return None
    raw_path = _resolved(window.get("raw_path") or (window.get("source_fingerprint") or {}).get("path"))
    receipt = _resolved(window.get("window_source"))
    if not raw_path or not receipt:
        return None
    frames = window.get("frame_identifiers") or []
    if not isinstance(frames, Sequence) or isinstance(frames, (str, bytes)) or not frames:
        return None
    if not all(isinstance(frame, Mapping) for frame in frames):
        return None
    hashed = _window_hashes(frames)
    if hashed is None:
        return None
    key_set, key_windows = hashed
    phase = str(frames[0].get("phase"))
    source_cal = _observed_calibration(observation)
    return {
        "source_calibration": source_cal,
        "source_declaration": ((window.get("evaluation") or {}).get("source_declaration")
                               if isinstance(window.get("evaluation"), Mapping) else None),
        "source_scope_id": window.get("source_scope_id"),
        "receipt_sha256": window.get("receipt_sha256"),
        "keyset": window.get("keyset"),
        "raw_sha256": raw_sha,
        "raw_path": raw_path,
        "receipt_path": receipt,
        "key_set_sha256": key_set,
        "key_windows_sha256": key_windows,
        "scope_phase": phase,
        "window_count": len(frames),
        "boundary": str(window.get("boundary") or ""),
    }


def slice_record(row: Mapping[str, Any], observation: Mapping[str, Any] | None) -> dict[str, Any]:
    """One population row. The capture id is kept even when the row does not join."""
    return {
        "capture_id": str(row.get("capture_id") or ""),
        "suite": str(row.get("suite") or ""),
        "basis": slice_basis(observation),
        "row_calibration": _actual_calibration(row) or _observed_calibration(observation),
    }


def _overlay(calibration_rows: Sequence[Mapping[str, Any]] | None) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for row in calibration_rows or ():
        parsed = _actual_calibration(row)
        if parsed is None:
            continue
        found[str(row.get("capture_id") or "")] = parsed
    return found


def _resolved_calibration(record: Mapping[str, Any], overlay: Mapping[str, Mapping[str, Any]]) -> dict[str, Any] | None:
    """Structure/source calibration wins over a later recomputed label on the same id."""
    chosen = overlay.get(record["capture_id"])
    if chosen is not None:
        return dict(chosen)
    row_cal = record.get("row_calibration")
    return dict(row_cal) if isinstance(row_cal, Mapping) else None


def disclose_source_slices(
    records: Sequence[Mapping[str, Any]],
    calibration_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Group verified slices and name each group by its earliest actual calibration.

    Population order is the given record order. Filename, duration, and a
    blanket suite label are not the join. A later actual relation that
    disagrees is a conflict and is not overwritten.
    """
    overlay = _overlay(calibration_rows)
    groups: dict[tuple, list[dict[str, Any]]] = {}
    order: list[tuple] = []
    measured = windows = 0
    by_id: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        basis = record.get("basis")
        if not isinstance(basis, Mapping):
            continue
        measured += 1
        count = int(basis.get("window_count") or 0)
        windows += count
        # Receipt path is required evidence, not a second identity. A registered
        # extraction and a source receipt can both verify one kernel's windows.
        key = (
            basis.get("raw_sha256"),
            basis.get("raw_path"),
            basis.get("key_set_sha256"),
            basis.get("key_windows_sha256"),
            basis.get("scope_phase"),
        )
        if key not in groups:
            order.append(key)
            groups[key] = []
        groups[key].append({
            "index": index,
            "capture_id": record.get("capture_id") or "",
            "suite": record.get("suite") or "",
            "window_count": count,
            "calibration": _resolved_calibration(record, overlay),
            "basis": basis,
        })
    alias_groups = []
    unique_windows = 0
    repeated = 0
    for key in order:
        members = groups[key]
        count = int(members[0]["window_count"])
        same_count = all(int(member["window_count"]) == count for member in members)
        unique_windows += count if same_count else sum(int(member["window_count"]) for member in members)
        if len(members) > 1 and same_count:
            repeated += count * (len(members) - 1)
        donors = [member for member in members if member.get("calibration")]
        relations = {
            (item["calibration"]["evaluation_relation"], item["calibration"]["target_timing_used_to_fit"])
            for item in donors
        }
        conflict = len(relations) > 1 or not same_count
        donor = None if conflict or not donors else min(donors, key=lambda member: member["index"])
        if len(members) > 1:
            alias_groups.append({
                "capture_ids": [member["capture_id"] for member in members],
                "suites": [member["suite"] for member in members],
                "scope_phase": key[4],
                "window_count": count,
                "raw_sha256": key[0],
                "receipt_paths": sorted({str(member["basis"]["receipt_path"]) for member in members}),
                "key_windows_sha256": key[3],
                "donor_capture_id": None if donor is None else donor["capture_id"],
                "evaluation_relation": None if donor is None else donor["calibration"]["evaluation_relation"],
                "target_timing_used_to_fit": None if donor is None else donor["calibration"]["target_timing_used_to_fit"],
                "conflict": conflict,
            })
        for member in members:
            calibration = member.get("calibration")
            inherited = bool(donor is not None and calibration is None)
            chosen = donor["calibration"] if inherited else calibration
            by_id[str(member["capture_id"])] = {
                "capture_id": member["capture_id"],
                "inherited": inherited,
                "conflict": bool(conflict and calibration is not None and donor is None),
                "evaluation_relation": None if chosen is None else chosen["evaluation_relation"],
                "calibration_role": None if chosen is None else chosen["calibration_role"],
                "target_timing_used_to_fit": None if chosen is None else chosen["target_timing_used_to_fit"],
                "donor_capture_id": None if donor is None else donor["capture_id"],
                "scope_phase": key[4],
                "window_count": member["window_count"],
                "raw_sha256": key[0],
                "key_windows_sha256": key[3],
                "source_scope_id": member["basis"].get("source_scope_id"),
                "receipt_sha256": member["basis"].get("receipt_sha256"),
                "keyset": member["basis"].get("keyset"),
                "source_declaration": member["basis"].get("source_declaration"),
            }
    return {
        "by_id": by_id,
        "alias_groups": alias_groups,
        "cohort": {
            "population_rows": len(records),
            "measured_ids": measured,
            "id_window_rows": windows,
            "unique_physical_series": len(groups),
            "unique_physical_windows": unique_windows,
            "alias_groups": len(alias_groups),
            "repeated_id_window_rows": repeated,
            "scoring_population": "measured_ids",
        },
    }


def apply_slice_disclosure(
    item: dict[str, Any],
    info: Mapping[str, Any] | None,
    *,
    coverage_only: Callable[[str, str], bool],
) -> None:
    """Label a scored row from its slice. An actual relation already on the row stays."""
    if not isinstance(info, Mapping):
        return
    relation = str(info.get("evaluation_relation") or "")
    if not relation or relation == _RECOMPUTED_LABEL:
        return
    current = str(item.get("evaluation_relation") or "")
    current_actual = bool(current) and current != _RECOMPUTED_LABEL
    if info.get("inherited") and current_actual and current != relation:
        item["slice_relation_conflict"] = True
        return
    if info.get("inherited") or not current_actual or current == relation:
        if info.get("inherited") or not current_actual:
            role = str(info.get("calibration_role") or relation)
            item["evaluation_relation"] = relation
            item["calibration_role"] = role
            item["coverage_only"] = bool(coverage_only(relation, role))
        if "target_timing_used_to_fit" in info:
            item["target_timing_used_to_fit"] = info.get("target_timing_used_to_fit")
        if info.get("inherited"):
            item["slice_role_inherited"] = True
            item["slice_role_source_id"] = str(info.get("donor_capture_id") or "")
        elif info.get("source_scope_id"):
            item["slice_role_source_id"] = str(info.get("source_scope_id"))
        if info.get("source_scope_id"):
            item["slice_source_scope_id"] = info.get("source_scope_id")
