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

from .profiles import profile_section
from .timing import HOST_FALLBACK

_CFG = profile_section("observations")

OBSERVATION_SCHEMA = "mindie-bench-observation/1"
OBSERVATION_RECORD = "observation"
CASE_COMPLETE_RECORD = "case_complete"
DEFAULT_ARM = "base"
SAMPLE_ID_PREFIX = "obs-"
SAMPLE_ID_CHARS = int(_CFG["sample_id_chars"])
_JOURNAL_MODE = int(_CFG["journal_mode"])
_TAIL_CHUNK = int(_CFG["tail_repair_chunk_bytes"])
IDENTITY_FIELDS = (
    "level", "boundary", "hardware", "implementation", "phase",
    "shape", "dtype", "layout", "execution",
)
PRIMITIVE_KEY_FIELDS = (
    "hardware", "implementation", "kernel", "dtype", "shape", "scope",
)
EXPERIMENT_SHAPE_KEYS = (
    "contention", "indices_per_cacheline", "path", "placement", "reuse",
    "transfer_protocol", "layout", "format_code", "split_k", "distribution",
    "zero_fraction", "active_experts", "residency", "owners", "direction",
    "pinned", "kernel_class",
)
_ENRICHED_SHAPE_KEYS = EXPERIMENT_SHAPE_KEYS
JSONL_NEWLINE = b"\n"


def _digest(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:SAMPLE_ID_CHARS]


def physical_case_key(sku: Any, evidence: Any) -> tuple[Any, str] | None:
    """Freeze the plan key and requested geometry as a JSON-compatible identity."""
    if not isinstance(evidence, Mapping):
        return None
    plan = evidence.get("plan_key")
    shape = evidence.get("requested_shape")
    if not isinstance(plan, Mapping) or not plan or not isinstance(shape, Mapping):
        return None
    return sku, json.dumps([dict(plan), dict(shape)], sort_keys=True, separators=(",", ":"))


def sample_id(
    *,
    plan_id: Any,
    case_id: Any,
    run_id: Any,
    arm: Any,
    timing_mode: Any,
    residency: Any,
    trial: Any,
    repeat_index: Any,
    rank: Any,
    case_geometry: str | None = None,
) -> str:
    """Deterministic pre-timing identity; ``duration_ms`` is never an input."""
    payload = [plan_id, case_id, run_id, arm, timing_mode, residency, trial, repeat_index, rank]
    if case_geometry is not None:
        payload.append(case_geometry)
    return SAMPLE_ID_PREFIX + _digest(payload)


def _resolved_impl(case: Mapping[str, Any]) -> str:
    """Distinguish builder families that share one kernel selector (mte2_aic/aiv)."""
    declared = str(case.get("implementation") or "").strip()
    if declared:
        return declared
    builder = str(case.get("builder") or "").strip()
    op = str(case.get("op") or "").strip()
    if builder and op and builder != op:
        return f"{builder}:{op}"
    return builder or op or "declared"


def _enriched_shape(case: Mapping[str, Any]) -> dict[str, Any]:
    """Copy ``case["shape"]`` and fold in declared experiment conditions.

    Conditions such as ``contention`` or ``reuse`` change the measured kernel
    even when the geometry is identical, so they must participate in both the
    primitive key and the observation identity without mutating the case.
    """
    raw = case.get("shape")
    shape = dict(raw) if isinstance(raw, Mapping) else {}
    for key in _ENRICHED_SHAPE_KEYS:
        if key not in shape and case.get(key) is not None:
            shape[key] = case.get(key)
    return shape


def primitive_key(
    case: Mapping[str, Any], *, boundary: str, scope: Any = None
) -> dict[str, Any] | None:
    """Complete 6-field primitive key when every field is declared."""
    shape = _enriched_shape(case)
    key = {
        "hardware": case.get("hardware") or shape.get("hardware"),
        "implementation": _resolved_impl(case),
        "kernel": case.get("kernel") or case.get("op"),
        "dtype": case.get("dtype"),
        "shape": case.get("primitive_shape") or dict(shape) or None,
        "scope": scope or case.get("scope") or boundary,
    }
    for field in PRIMITIVE_KEY_FIELDS:
        if key[field] in (None, ""):
            key[field] = "declared" if field != "shape" else {"declared": True}
    if not isinstance(key["shape"], (Mapping, str, list)):
        key["shape"] = str(key["shape"])
    return key


def identity(
    *,
    case: Mapping[str, Any],
    boundary: str,
    execution: Any,
    level: str = "operator",
    phase: Any = None,
) -> dict[str, Any]:
    """Complete 9-field ``ObservationIdentity`` for one emitted row."""
    shape = _enriched_shape(case)
    return {
        "level": case.get("level") or level,
        "boundary": boundary,
        "hardware": case.get("hardware") or "declared",
        "implementation": _resolved_impl(case),
        "phase": phase or case.get("phase") or "benchmark",
        "shape": case.get("identity_shape") or dict(shape) or {"declared": True},
        "dtype": case.get("dtype") or "declared",
        "layout": case.get("layout") or shape.get("layout") or "declared",
        "execution": execution if execution is not None else {"mode": "declared"},
    }


def timing_rows(
    timing: Mapping[str, Any],
) -> Iterable[tuple[str, bool, int, int, float]]:
    """Yield ``(mode, mode_qualified, trial, repeat_index, repeat_us)``.

    ``mode_qualified`` is true only for device-timed, non-host-fallback modes
    whose per-mode summary is itself explicitly qualified; unqualified rows are
    still yielded so the packet builder can reject them explicitly.
    """
    if not isinstance(timing, Mapping):
        return
    host_fallback = timing.get("timer_source") == "perf_counter_host_fallback"
    modes = timing.get("modes") if isinstance(timing.get("modes"), Mapping) else {}
    for mode, summary in modes.items():
        if not isinstance(summary, Mapping):
            continue
        mode_name = str(mode)
        mode_qualified = bool(
            not host_fallback
            and mode_name != HOST_FALLBACK
            and summary.get("qualified") is True
        )
        for trial in summary.get("trials") or ():
            if not isinstance(trial, Mapping):
                continue
            for repeat_index, value in enumerate(trial.get("repeats_us") or ()):
                yield (
                    mode_name,
                    mode_qualified,
                    int(trial.get("trial") or 0),
                    repeat_index,
                    float(value),
                )


def observation_row(
    *,
    plan_id: Any,
    case: Mapping[str, Any],
    run_id: Any,
    split: str,
    boundary: str,
    timing_mode: str,
    residency: str,
    trial: int,
    repeat_index: int,
    rank: Any,
    duration_ms: float,
    source: str,
    arm: Any = DEFAULT_ARM,
    status: str = "ok",
    validated: bool = True,
    qualified: bool = True,
    sku: Any = None,
    level: str = "operator",
    phase: Any = None,
    execution: Any = None,
    work_bytes: Any = None,
    work: Any = None,
    resource: Any = None,
    work_unit: Any = None,
    active_units: Any = None,
    mixed_domains: Any = None,
    route: Any = None,
    key: Any = None,
    identity_override: Mapping[str, Any] | None = None,
    service_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one schema-conformant observation row (facets only when present)."""
    case_id = str(case.get("case_id") or case.get("node_id") or "case")
    evidence = {"plan_key": case.get("plan_key"), "requested_shape": case.get("shape")}
    physical_key = physical_case_key(sku, evidence)
    record: dict[str, Any] = {
        "schema": OBSERVATION_SCHEMA,
        "record_type": OBSERVATION_RECORD,
        "sample_id": sample_id(
            plan_id=plan_id,
            case_id=case_id,
            run_id=run_id,
            arm=arm,
            timing_mode=timing_mode,
            residency=residency,
            trial=trial,
            repeat_index=repeat_index,
            rank=rank,
            case_geometry=physical_key[1] if physical_key is not None else None,
        ),
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
        "identity": identity(
            case=case, boundary=boundary, execution=execution, level=level, phase=phase
        ),
    }
    if physical_key is not None:
        record.update(evidence)
    if isinstance(identity_override, Mapping) and all(
        field in identity_override for field in IDENTITY_FIELDS
    ):
        overridden = dict(identity_override)
        exec_mode = overridden.get("execution")
        exec_mode = dict(exec_mode) if isinstance(exec_mode, Mapping) else {}
        if isinstance(execution, Mapping):
            exec_mode.update(execution)
        exec_mode["mode"] = str(timing_mode)
        overridden["execution"] = exec_mode
        record["identity"] = overridden
    if isinstance(service_identity, Mapping):
        record["service_identity"] = dict(service_identity)
    if sku is not None:
        record["sku"] = str(sku)
    if rank is not None:
        record["rank"] = rank
    declared_bytes = int(work_bytes or 0)
    if declared_bytes > 0:
        record["work_bytes"] = declared_bytes
    if mixed_domains is not None:
        record["mixed_domains"] = bool(mixed_domains)
    if isinstance(route, str) and route:
        record["route"] = route
    if work is not None or resource is not None or work_unit is not None:
        record["work"] = work
        record["resource"] = resource
        record["work_unit"] = work_unit
        record["active_units"] = int(active_units or 1)
    primitive = key if isinstance(key, Mapping) else primitive_key(case, boundary=boundary)
    if primitive is not None:
        record["key"] = dict(primitive)
    return record


def case_complete_row(
    *,
    plan_id: Any,
    case_id: Any,
    run_id: Any,
    sku: Any = None,
    status: str = "ok",
    split: str = "train",
    summary: Any = None,
) -> dict[str, Any]:
    record = {
        "schema": OBSERVATION_SCHEMA,
        "record_type": CASE_COMPLETE_RECORD,
        "plan_id": plan_id,
        "case_id": str(case_id),
        "run_id": str(run_id),
        "sku": sku,
        "split": "heldout" if split == "heldout" else "train",
        "status": str(status),
    }
    if summary is not None:
        record["summary"] = summary
    return record


DEFAULT_OBSERVATION_BOUNDARY = "device_kernel"


def _case_boundary(case: Mapping[str, Any], identities: Mapping[str, Any]) -> str:
    accuracy = identities.get("accuracy_identity")
    declared = accuracy.get("boundary") if isinstance(accuracy, Mapping) else None
    timing = case.get("timing")
    timed = timing.get("boundary") if isinstance(timing, Mapping) else None
    return str(declared or timed or case.get("boundary") or DEFAULT_OBSERVATION_BOUNDARY)

def _row_qualified(record: Mapping[str, Any], graph: str | None, mode_qualified: bool) -> bool:
    if record.get("shape_qualified") is False:
        return False
    if graph == "aclgraph":
        return bool(record.get("qualified") and record.get("outputs_agree") and mode_qualified)
    if graph == "eager":
        return bool(mode_qualified)
    return bool(record.get("validated", True)) and bool(mode_qualified)

def _emit_case_observations(
    journal: Any, plan: Mapping[str, Any], case: Mapping[str, Any],
    record: Mapping[str, Any], run_id: str, stage: str, *, rank: Any = None,
) -> None:
    if journal is None or record.get("status") not in {"ok", "unqualified"}:
        return
    split = str(case.get("split") or "train")
    identities = case.get("identities") if isinstance(case.get("identities"), Mapping) else {}
    boundary = _case_boundary(case, identities)
    node_shapes = record.get("node_shapes")
    row_rank = case.get("rank") if case.get("rank") is not None else rank
    plan_hw = plan.get("hardware")
    hw = (case.get("hardware") or case.get("sku") or plan.get("sku")
          or (plan_hw.get("sku") if isinstance(plan_hw, Mapping) else plan_hw) or plan.get("plan_id") or "subgraph")
    nodes = [n for n in (case.get("nodes") or ()) if isinstance(n, Mapping)]
    n0 = nodes[0] if nodes else {}
    obs_case = {**case, "hardware": hw,
                "implementation": case.get("implementation") or n0.get("implementation") or n0.get("builder") or n0.get("op") or case.get("archetype") or "subgraph",
                "dtype": case.get("dtype") or n0.get("dtype") or "bf16"}
    service = identities.get("service")
    mixed = service.get("mixed_domains") if isinstance(service, Mapping) and "mixed_domains" in service else case.get("mixed_domains")
    wb = case.get("work_bytes") if case.get("work_bytes") is not None else case.get("fabric_bytes")
    facets, base_timing = ("work", "resource", "work_unit", "active_units"), (None if record.get("eager_ran") is False else record.get("timing"))
    arms = [(a, t, g) for a, t, g in (("base", base_timing, None), ("base", record.get("eager"), "eager"), ("aclgraph", record.get("aclgraph"), "aclgraph")) if isinstance(t, Mapping)]
    for arm, arm_timing, graph in arms:
        capabilities = ({key: service.get(key) for key in facets} if isinstance(service, Mapping)
                        else ({"work": arm_timing.get("minimum_ms"), "resource": case.get("resource"),
                               "work_unit": case.get("work_unit"), "active_units": case.get("active_units")}
                              if case.get("work_unit") else {}))
        for mode, mode_qualified, trial, repeat_index, repeat_us in timing_rows(arm_timing):
            execution: dict[str, Any] = {"mode": mode, "stage": stage, **({"graph": graph} if graph is not None else {})}
            row_boundary = arm_timing["modes"][mode].get("boundary", boundary)
            row = observation_row(
                plan_id=plan.get("plan_id"), case=obs_case, run_id=f"{run_id}.{arm}.{mode}.t{trial}",
                split=split, boundary=row_boundary, timing_mode=mode, residency=str(case.get("residency") or "device"),
                trial=trial, repeat_index=repeat_index, rank=row_rank, duration_ms=float(repeat_us) / 1000.0,
                source=f"capture://bench-subgraph/{case.get('case_id')}/{arm}.{mode}.{trial}.{repeat_index}",
                arm=arm, validated=bool(record.get("validated", True)), qualified=_row_qualified(record, graph, mode_qualified),
                level=str(case.get("level") or "subgraph"), phase=case.get("phase"), execution=execution,
                work_bytes=wb, mixed_domains=mixed, route=case.get("route"), key=identities.get("primitive_key"),
                identity_override=identities.get("accuracy_identity"),
                service_identity=(service.get("identity") if isinstance(service, Mapping) else None), **capabilities,
            )
            row["identity"]["boundary"] = row_boundary
            if node_shapes is not None:
                row["node_shapes"] = node_shapes
            journal.append(row)
    summary: dict[str, Any] = {"stage": stage, "timed_nodes": record.get("timed_nodes"), "outputs_agree": record.get("outputs_agree"),
                               **({"mixed_domains": bool(mixed)} if mixed is not None else {}),
                               **({"work_bytes": int(wb)} if int(wb or 0) > 0 else {})}
    if node_shapes is not None:
        summary["node_shapes"] = node_shapes
    journal.append(case_complete_row(plan_id=plan.get("plan_id"), case_id=case.get("case_id"), run_id=run_id, status=str(record.get("status")), split=split, summary=summary))


def completion_key(record: Mapping[str, Any], *, allow_legacy: bool = True) -> tuple[Any, str] | None:
    """Read a completed marker's physical identity or its legacy case ID."""
    if record.get("record_type") != CASE_COMPLETE_RECORD:
        return None
    if record.get("status") != "ok":
        return None
    case_id = record.get("case_id")
    if not isinstance(case_id, str) or not case_id:
        return None
    sku = record.get("sku")
    key = physical_case_key(sku, record.get("summary"))
    return (sku, case_id) if key is None and allow_legacy else key


def _parse_jsonl_line(raw: bytes) -> bool:
    """True when ``raw`` is a blank or valid UTF-8 JSON line."""
    if not raw.strip():
        return True
    try:
        json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return False
    return True


def _trailing_line(handle: Any, size: int) -> bytes:
    """Read the final newline-terminated line via bounded backwards chunks."""
    position = size
    buffer = b""
    while True:
        read_size = min(_TAIL_CHUNK, position)
        position -= read_size
        handle.seek(position)
        buffer = handle.read(read_size) + buffer
        body = buffer[:-1] if buffer.endswith(JSONL_NEWLINE) else buffer
        index = body.rfind(JSONL_NEWLINE)
        if index >= 0:
            return body[index + len(JSONL_NEWLINE):]
        if position == 0:
            return body


def _last_valid_offset(path: Path) -> int:
    """Return the offset after the last complete valid JSONL line."""
    size = path.stat().st_size
    position = size
    buffer = b""
    with path.open("rb") as handle:
        while position > 0:
            read_size = min(_TAIL_CHUNK, position)
            position -= read_size
            handle.seek(position)
            buffer = handle.read(read_size) + buffer
            parts = buffer.split(JSONL_NEWLINE)
            complete = parts[:-1]
            start = position
            candidates: list[tuple[int, bytes]] = []
            for part in complete:
                candidates.append((start, part))
                start += len(part) + len(JSONL_NEWLINE)
            for start, part in reversed(candidates):
                if start == position and position > 0:
                    handle.seek(start - 1)
                    if handle.read(1) != JSONL_NEWLINE:
                        continue
                if _parse_jsonl_line(part):
                    return start + len(part) + len(JSONL_NEWLINE)
    return 0


class ObservationJournal:
    """Append-only observation journal with torn-tail repair and resume scan."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def repair(self) -> int:
        """Truncate a partial/invalid tail; return the number of dropped bytes.

        A newline-terminated file whose final line is valid JSON costs one
        bounded backwards read, never a whole-file scan.
        """
        if not self.path.exists():
            return 0
        size = self.path.stat().st_size
        if size == 0:
            return 0
        with self.path.open("rb") as handle:
            handle.seek(size - 1)
            if handle.read(1) == JSONL_NEWLINE and _parse_jsonl_line(
                _trailing_line(handle, size)
            ):
                return 0
        valid = _last_valid_offset(self.path)
        if valid >= size:
            return 0
        os.truncate(self.path, valid)
        return size - valid


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
        return {
            key
            for key in (completion_key(record) for record in self.records())
            if key is not None
        }

    def purge_incomplete_cases(self) -> int:
        """Drop rows from an in-flight case that never reached ``case_complete``."""
        self.repair()
        if not self.path.exists():
            return 0
        records = list(self.records())
        complete = {key for record in records if (key := completion_key(record, allow_legacy=False)) is not None}
        legacy_complete = {(record.get("sku"), record.get("case_id")) for record in records
                           if record.get("record_type") == CASE_COMPLETE_RECORD and record.get("status") == "ok"}

        def completed(record: Mapping[str, Any]) -> bool:
            sku = record.get("sku")
            key = physical_case_key(sku, record)
            return key in complete if key is not None else (sku, record.get("case_id")) in legacy_complete

        kept = [
            record for record in records
            if record.get("record_type") != OBSERVATION_RECORD
            or completed(record)
        ]
        removed = len(records) - len(kept)
        if removed <= 0:
            return 0
        text = "".join(
            json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in kept
        )
        temporary = self.path.with_name(self.path.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, self.path)
        return removed

    def append(self, record: Mapping[str, Any]) -> None:
        self.repair()
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, _JOURNAL_MODE
        )
        try:
            payload = line.encode("utf-8")
            if os.write(descriptor, payload) != len(payload):
                raise OSError("short observation journal write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


__all__ = [
    "CASE_COMPLETE_RECORD", "DEFAULT_ARM", "EXPERIMENT_SHAPE_KEYS",
    "IDENTITY_FIELDS", "OBSERVATION_RECORD", "OBSERVATION_SCHEMA",
    "ObservationJournal", "PRIMITIVE_KEY_FIELDS", "case_complete_row",
    "completion_key", "identity", "observation_row", "physical_case_key", "primitive_key",
    "sample_id", "timing_rows",
]
