"""Canonical persistent receipt discovery for fleet observation sources.

[Role]
  Locate maintained native extraction receipts by canonical source identity
  (source path and/or SHA-256/size), independent of the working directory and
  of any task-local TSV.  One in-memory index is built per process from the
  declared archive roots; lookups are O(1).

[Roots]
  Default roots are the maintained acceptance archive extraction directories
  (DSH, Wave5 a2/a3/a5) plus an optional `MINDIE_RECEIPT_ROOTS` pathsep list.
  The temporary reviewer TSV is not required at runtime.

[Invariants] No measured timings are read for discovery; only source identity,
phase, parser/version, and usable-window counts.  Duplicate receipts are
selected deterministically by parser kind and receipt path, never by error.
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

ARCHIVE_DIR_NAME = "acceptance-archives-20261030"
_INDEX: dict[str, dict[str, Any]] | None = None
_ALL_INDEX: dict[str, list[dict[str, Any]]] | None = None
_ROOTS: tuple[Path, ...] | None = None


def configure_discovery_roots(*, data_roots: Sequence[Path] | None = None,
                              roots: Sequence[Path] | None = None) -> None:
    """Declare canonical archive roots; no machine-specific path is embedded."""
    global _ROOTS, _INDEX, _ALL_INDEX
    if roots is not None:
        _ROOTS = tuple(Path(p) for p in roots)
    elif data_roots is not None:
        declared = []
        for root in data_roots:
            archive = Path(root) / ARCHIVE_DIR_NAME
            declared.extend((archive / "dsh-full-generalization" / "extractions",
                             archive / "wave5-eval" / "a2" / "extractions",
                             archive / "wave5-eval" / "a3" / "extractions",
                             archive / "wave5-eval" / "a5" / "cache"))
        _ROOTS = tuple(declared)
    _INDEX = None


def clear_discovery_cache() -> None:
    """Drop the in-memory receipt index (tests/roots changes)."""
    global _INDEX, _ALL_INDEX
    _INDEX = None
    _ALL_INDEX = None
    _ALL_INDEX = None


def _roots() -> tuple[Path, ...]:
    raw = os.environ.get("MINDIE_RECEIPT_ROOTS")
    if raw:
        return tuple(Path(p) for p in raw.split(os.pathsep) if p)
    if _ROOTS is not None:
        return _ROOTS
    # Lazy declared-root fallback; do not embed a machine-specific data path.
    try:
        from fleet_capture_artifacts import DATA_ROOTS
        configure_discovery_roots(data_roots=DATA_ROOTS)
        return _ROOTS or ()
    except Exception:
        return ()


def _record(path: Path, document: Mapping[str, Any]) -> dict[str, Any] | None:
    observed = document.get("observed") if isinstance(document.get("observed"), Mapping) else document
    identity = observed.get("source_identity") or {}
    if not isinstance(identity, Mapping):
        return None
    source = str(identity.get("path") or "")
    sha = str(identity.get("sha256") or "").lower()
    if not source and not sha:
        return None
    forwards = [f for f in (observed.get("forwards") or ()) if isinstance(f, Mapping)]
    usable = 0
    for forward in forwards:
        body = forward.get("body") if isinstance(forward.get("body"), Mapping) else forward
        start, end = body.get("start_ns"), body.get("end_ns")
        if isinstance(start, int) and isinstance(end, int) and end > start:
            usable += 1
    parser = str(document.get("parser_identity") or "-")
    version = str(document.get("cache_version") or "-")
    phase = str(observed.get("phase") or "").lower()
    return {"receipt": str(path), "source_path": source, "source_sha256": sha,
            "source_size_bytes": identity.get("size_bytes"), "phase": phase,
            "status": str(observed.get("status") or ""), "parser": parser,
            "version": version, "forward_count": len(forwards),
            "usable_window_count": usable}


def canonical_receipts_by_source() -> dict[str, list[dict[str, Any]]]:
    """All measured receipts per canonical source path (conflicts preserved)."""
    global _ALL_INDEX, _INDEX
    if _ALL_INDEX is not None:
        return _ALL_INDEX
    all_index: dict[str, list[dict[str, Any]]] = {}
    for root in _roots():
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.json")):
            if not re.fullmatch(r"[a-f0-9]{64}", path.stem):
                continue
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            record = _record(path, document)
            if record is None or record["status"] != "measured" or not record["source_path"]:
                continue
            try:
                key = str(Path(record["source_path"]).resolve())
            except OSError:
                key = record["source_path"]
            all_index.setdefault(key, []).append(record)
    _ALL_INDEX = all_index
    _INDEX = {key: sorted(records, key=lambda r: (str(r.get("receipt") or "")))[0]
              for key, records in all_index.items()}
    for key, records in all_index.items():
        _INDEX[key] = min(records, key=lambda r: (not _better(r, records[0]), str(r.get("receipt") or "")))
    return all_index


def canonical_receipt_index() -> dict[str, dict[str, Any]]:
    """Deterministic selected receipt per source path (use lookup for conflict status)."""
    if _INDEX is not None:
        return _INDEX
    canonical_receipts_by_source()
    return _INDEX or {}


def _better(candidate: Mapping[str, Any], current: Mapping[str, Any]) -> bool:
    """Deterministic preference: nonlegacy parser, then usable windows, then path."""
    cand_legacy = "legacy" in str(candidate.get("parser") or "").lower()
    cur_legacy = "legacy" in str(current.get("parser") or "").lower()
    if cand_legacy != cur_legacy:
        return not cand_legacy
    if int(candidate.get("usable_window_count") or 0) != int(current.get("usable_window_count") or 0):
        return int(candidate.get("usable_window_count") or 0) > int(current.get("usable_window_count") or 0)
    return str(candidate.get("receipt") or "") < str(current.get("receipt") or "")


def lookup_source_receipt(*, source_path: str | Path | None = None,
                          source_sha256: str | None = None,
                          source_size_bytes: int | None = None,
                          phase: str | None = None) -> dict[str, Any]:
    """One public lookup: canonical path first, then exact SHA/size fallback.

    Returns ``status="resolved"`` with the selected receipt/source identity, or
    ``status="unknown"``/``"conflict"`` with the observed candidates.  No timing
    value is read or selected.
    """
    all_index = canonical_receipts_by_source()
    candidates: list[dict[str, Any]] = []
    if source_path:
        try:
            key = str(Path(source_path).resolve())
        except OSError:
            key = str(source_path)
        candidates = list(all_index.get(key) or ())
    wanted_sha = str(source_sha256 or "").lower()
    wanted_size = int(source_size_bytes) if source_size_bytes is not None else None
    if not candidates and (wanted_sha or wanted_size is not None):
        for records in all_index.values():
            for record in records:
                if wanted_sha and record["source_sha256"] != wanted_sha:
                    continue
                if wanted_size is not None and record.get("source_size_bytes") is not None and int(record["source_size_bytes"]) != wanted_size:
                    continue
                if phase and record.get("phase") and record["phase"] != phase:
                    continue
                candidates.append(record)
    if phase:
        phase_matched = [c for c in candidates if not c.get("phase") or c["phase"] == phase]
        if phase_matched:
            candidates = phase_matched
    if not candidates:
        return {"status": "unknown", "reason": "no maintained receipt for canonical source identity"}
    signatures = {(c["source_sha256"], c.get("source_size_bytes")) for c in candidates}
    if len(signatures) > 1:
        return {"status": "conflict", "reason": "multiple source digests/sizes for canonical source",
                "candidates": candidates[:8]}
    chosen = min(candidates, key=lambda c: (not _better(c, candidates[0]), str(c.get("receipt") or "")))
    return {"status": "resolved", "duplicate_receipts": len(candidates), "receipt": chosen["receipt"],
            "source_path": chosen["source_path"], "source_sha256": chosen["source_sha256"],
            "source_size_bytes": chosen.get("source_size_bytes"), "phase": chosen.get("phase"),
            "parser": chosen.get("parser"), "version": chosen.get("version"),
            "forward_count": chosen.get("forward_count"),
            "usable_window_count": chosen.get("usable_window_count")}
