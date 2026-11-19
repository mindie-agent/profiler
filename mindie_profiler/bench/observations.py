"""Deterministic bench observation JSONL rows and a torn-tail-safe journal.

[Role]
  Build the ``mindie-bench-observation/1`` rows emitted by ``bench sku`` and
  ``bench subgraph`` so ``sim/tools/bench_packets.py`` ingests them directly,
  and own the append-only resume journal that repairs an unterminated tail.

[Invariants]
  * ``sample_id`` uses pre-timing facts only and never ``duration_ms``.
  * Every observation carries a complete 9-field identity; ``work_bytes`` is
    omitted when zero and ``key`` is always a complete 6-field primitive key.
  * A resume journal is truncated to its last valid newline before a new line
    is appended, so a torn tail can never corrupt a later record.

[Timeouts & Locks]
  Pure line-oriented file I/O; no locks, timers or background threads.

[Side-Effect Policy]
  Writes only the requested journal path; a repair truncates a partial line.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

OBSERVATION_SCHEMA = "mindie-bench-observation/1"
OBSERVATION_RECORD = "observation"
CASE_COMPLETE_RECORD = "case_complete"
DEFAULT_ARM = "base"
SAMPLE_ID_PREFIX = "obs-"
SAMPLE_ID_CHARS = 20
IDENTITY_FIELDS = ("level", "boundary", "hardware", "implementation", "phase",
                   "shape", "dtype", "layout", "execution")
PRIMITIVE_KEY_FIELDS = ("hardware", "implementation", "kernel", "dtype", "shape",
                        "scope")
JSONL_NEWLINE = b"\n"
def _digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:SAMPLE_ID_CHARS]
def sample_id(*, plan_id: Any, case_id: Any, run_id: Any, arm: Any,
              timing_mode: Any, residency: Any, trial: Any, repeat_index: Any,
              rank: Any) -> str:
    """Deterministic pre-timing identity; ``duration_ms`` is never an input."""
    return SAMPLE_ID_PREFIX + _digest([
        plan_id, case_id, run_id, arm, timing_mode, residency, trial,
        repeat_index, rank])
def primitive_key(case: Mapping[str, Any], *, boundary: str,
                  scope: Any = None) -> dict[str, Any] | None:
    """Complete 6-field primitive key when every field is declared."""
    shape = case.get("shape") if isinstance(case.get("shape"), Mapping) else {}
    key = {"hardware": case.get("hardware") or shape.get("hardware"),
           "implementation": case.get("implementation") or case.get("builder"),
           "kernel": case.get("kernel") or case.get("op"),
           "dtype": case.get("dtype"),
           "shape": case.get("primitive_shape") or dict(shape) or None,
           "scope": scope or case.get("scope") or boundary}
    for field in PRIMITIVE_KEY_FIELDS:
        if key[field] in (None, ""):
            key[field] = ("declared" if field != "shape"
                          else {"declared": True})
    if not isinstance(key["shape"], (Mapping, str, list)):
        key["shape"] = str(key["shape"])
    return key
def identity(*, case: Mapping[str, Any], boundary: str, execution: Any,
             level: str = "operator", phase: Any = None) -> dict[str, Any]:
    """Complete 9-field ``ObservationIdentity`` for one emitted row."""
    shape = case.get("shape") if isinstance(case.get("shape"), Mapping) else {}
    return {"level": case.get("level") or level, "boundary": boundary,
            "hardware": case.get("hardware") or "declared",
            "implementation": case.get("implementation") or case.get("builder")
            or case.get("op") or "declared",
            "phase": phase or case.get("phase") or "benchmark",
            "shape": case.get("identity_shape") or dict(shape) or {"declared": True},
            "dtype": case.get("dtype") or "declared",
            "layout": case.get("layout") or shape.get("layout") or "declared",
            "execution": execution if execution is not None else {"mode": "declared"}}
def observation_row(*, plan_id: Any, case: Mapping[str, Any], run_id: Any,
                    split: str, boundary: str, timing_mode: str,
                    residency: str, trial: int, repeat_index: int, rank: Any,
                    duration_ms: float, source: str, arm: Any = DEFAULT_ARM,
                    status: str = "ok", validated: bool = True,
                    qualified: bool = True, level: str = "operator",
                    phase: Any = None, execution: Any = None, work_bytes: Any = None,
                    work: Any = None, resource: Any = None, work_unit: Any = None,
                    active_units: Any = None, key: Any = None,
                    identity_override: Mapping[str, Any] | None = None,
                    service_identity: Mapping[str, Any] | None = None
                    ) -> dict[str, Any]:
    """Build one schema-conformant observation row (facets only when present)."""
    case_id = str(case.get("case_id") or case.get("node_id") or "case")
    record: dict[str, Any] = {
        "schema": OBSERVATION_SCHEMA,
        "record_type": OBSERVATION_RECORD,
        "sample_id": sample_id(
            plan_id=plan_id, case_id=case_id, run_id=run_id, arm=arm,
            timing_mode=timing_mode, residency=residency, trial=trial,
            repeat_index=repeat_index, rank=rank),
        "case_id": case_id,
        "run_id": str(run_id),
        "trial": int(trial),
        "repeat_index": int(repeat_index),
        "split": "heldout" if split == "heldout" else "train",
        "status": status,
        "validated": bool(validated),
        "qualified": bool(qualified),
        "timing_mode": str(timing_mode),
        "residency": str(residency),
        "boundary": str(boundary),
        "duration_ms": float(duration_ms),
        "source": str(source),
        "identity": identity(case=case, boundary=boundary, execution=execution,
                             level=level, phase=phase),
    }
    if isinstance(identity_override, Mapping) and all(
            field in identity_override for field in IDENTITY_FIELDS):
        overridden = dict(identity_override)
        execution_mode = overridden.get("execution")
        execution_mode = (dict(execution_mode)
                          if isinstance(execution_mode, Mapping) else {})
        execution_mode["mode"] = str(timing_mode)
        overridden["execution"] = execution_mode
        record["identity"] = overridden
    if isinstance(service_identity, Mapping):
        record["service_identity"] = dict(service_identity)
    declared_bytes = int(work_bytes or 0)
    if declared_bytes > 0:
        record["work_bytes"] = declared_bytes
    if work is not None or resource is not None or work_unit is not None:
        record["work"] = work
        record["resource"] = resource
        record["work_unit"] = work_unit
        record["active_units"] = int(active_units or 1)
    primitive = key if isinstance(key, Mapping) else primitive_key(
        case, boundary=boundary)
    if primitive is not None:
        record["key"] = dict(primitive)
    return record
def case_complete_row(*, plan_id: Any, case_id: Any, run_id: Any, sku: Any = None,
                      status: str = "ok", split: str = "train",
                      summary: Any = None) -> dict[str, Any]:
    record = {"schema": OBSERVATION_SCHEMA, "record_type": CASE_COMPLETE_RECORD,
              "plan_id": plan_id, "case_id": str(case_id), "run_id": str(run_id),
              "sku": sku, "split": "heldout" if split == "heldout" else "train",
              "status": str(status)}
    if summary is not None:
        record["summary"] = summary
    return record
def completion_key(record: Mapping[str, Any]) -> tuple[Any, Any] | None:
    """Resume identity: ``(sku, case_id)``; markers also need ``status == ok``."""
    if record.get("record_type") not in {OBSERVATION_RECORD, CASE_COMPLETE_RECORD}:
        return None
    if record.get("status") != "ok":
        return None
    case_id = record.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        return None
    return record.get("sku"), case_id
def _valid_prefix(data: bytes) -> int:
    """Return the byte offset after the last complete, valid JSONL line."""
    if not data:
        return 0
    parts = data.split(JSONL_NEWLINE)
    complete = parts[:-1]  # a trailing unterminated fragment is never valid
    offset = 0
    for part in complete:
        if part.strip():
            try:
                json.loads(part)
            except ValueError:
                break
        offset += len(part) + len(JSONL_NEWLINE)
    return offset

class ObservationJournal:
    """Append-only observation journal with torn-tail repair and resume scan."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def repair(self) -> int:
        """Truncate a partial/invalid tail; return the number of dropped bytes."""
        if not self.path.exists():
            return 0
        data = self.path.read_bytes()
        if not data:
            return 0
        valid = _valid_prefix(data)
        if valid == len(data):
            return 0
        os.truncate(self.path, valid)
        return len(data) - valid

    def records(self) -> Iterable[dict[str, Any]]:
        self.repair()
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, Mapping):
                    yield dict(record)
    def completed_keys(self) -> set[tuple[Any, Any]]:
        return {key for key in (completion_key(record) for record in self.records())
                if key is not None}
    def append(self, record: Mapping[str, Any]) -> None:
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                             _JOURNAL_MODE)
        try:
            payload = line.encode("utf-8")
            if os.write(descriptor, payload) != len(payload):
                raise OSError("short observation journal write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


_JOURNAL_MODE = 0o644
__all__ = [
    "CASE_COMPLETE_RECORD", "DEFAULT_ARM", "IDENTITY_FIELDS",
    "OBSERVATION_RECORD", "OBSERVATION_SCHEMA", "ObservationJournal",
    "PRIMITIVE_KEY_FIELDS", "case_complete_row", "completion_key", "identity",
    "observation_row", "primitive_key", "sample_id",
]
