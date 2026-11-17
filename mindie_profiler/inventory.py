"""Fast, read-only inventory of an Ascend profiling directory.

[Role]
  Answer "what is here and can it answer the question?" without analyzing
  windows: enumerate ranks, every DB/CSV/JSON candidate (including ambiguous
  multiple-DB directories), sizes, available tables, native ``ProfilerStep#``
  and MSTX phase windows, and the captured time span.

[Invariants]
  * Multiple DBs in one rank directory are all listed; no newest-mtime source
    is chosen.  The caller must pass an explicit DB before ``analyze``.
  * Missing tables are reported as absent, never fabricated as empty results.
  * SQLite query failures propagate to ``db_query_failed``; they are never
    turned into empty STRING_IDS, empty windows, or a missing capture span.
  * Native step/MSTX windows come from real name rows joined through
    STRING_IDS; no window is inferred from kernel periodicity.
  * Every file size/mtime is read from stat; content SHA256 is not computed.

[Timeouts & Locks]
  SQLite connections use ``mode=ro`` + ``query_only=ON`` with a short bounded
  progress deadline.  Directory discovery is bounded by ``max_dirs``.

[Side-Effect Policy]
  Read-only filesystem/sqlite access.  No sidecar index, write, or network.
"""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

from .events import ProfilerError
from .segment import (
    _OUTPUT_DIR,
    _bundle_root_for_leaf,
    find_csv_candidates,
    find_csv_discovery_candidates,
    find_db_candidates,
    find_trace_candidates,
    infer_rank_id,
    infer_rank_index,
)
from .sources_csv import MINDSTUDIO_OUTPUT_DIR, find_mindstudio_csv_candidates, probe_csv
from .sources_db import probe_db
from .sql import open_readonly

INVENTORY_SCHEMA = "mindie-profiler-inventory/1"
_CORE_TABLES = (
    "STRING_IDS",
    "TASK",
    "COMPUTE_TASK_INFO",
    "PYTORCH_API",
    "CANN_API",
    "CONNECTION_IDS",
    "MSTX_EVENTS",
    "COMMUNICATION_OP",
    "COMMUNICATION_SCHEDULE_TASK_INFO",
    "TASK_PMU_INFO",
)
_STEP_RE = re.compile(r"ProfilerStep#(\d+)", re.IGNORECASE)
_PHASE_RE = re.compile(r"(warmup|prefill|decode|draft|verify|graph_capture)", re.IGNORECASE)
_TIME_TABLES = ("TASK", "PYTORCH_API", "MSTX_EVENTS", "CANN_API", "COMMUNICATION_OP")


def _table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in con.execute(f"PRAGMA table_info({table})")}


def _pick(columns: Iterable[str], aliases: Iterable[str]) -> str | None:
    available = set(columns)
    for alias in aliases:
        if alias in available:
            return alias
    return None


def _file_row(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
    except TimeoutError:
        raise
    except OSError:
        return {"path": str(path), "basename": path.name, "size_bytes": None, "mtime_ns": None}
    return {
        "path": str(path.resolve()),
        "basename": path.name,
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _discover_rank_dirs(root: Path, *, max_dirs: int) -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()
    walked = 0
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        walked += 1
        if walked > max_dirs:
            raise ProfilerError(f"inventory discovery exceeded {max_dirs} directories under {root}")
        current_path = Path(current)
        has_db = any(name.startswith("ascend_pytorch_profiler") and name.endswith(".db") for name in filenames)
        has_csv = any(name in filenames for name in ("kernel_details.csv", "kernel_details.csv.gz"))
        has_trace = any(name.startswith("trace_view") and name.endswith(".json") for name in filenames)
        has_mindstudio = MINDSTUDIO_OUTPUT_DIR in dirnames or any(
            name.startswith("op_summary_") and name.endswith(".csv")
            or name.startswith("task_time_") and name.endswith(".csv")
            for name in filenames
        )
        has_output = _OUTPUT_DIR in dirnames
        if has_mindstudio:
            candidates = find_mindstudio_csv_candidates(current_path)
            if candidates["op_summary"] or candidates["task_time"]:
                if current_path not in seen:
                    discovered.append(current_path)
                    seen.add(current_path)
                dirnames[:] = []
                continue
        if has_db or has_csv or has_trace:
            if current_path not in seen:
                discovered.append(current_path)
                seen.add(current_path)
            dirnames[:] = []
            continue
        if has_output:
            output = current_path / _OUTPUT_DIR
            try:
                names = {entry.name for entry in output.iterdir()}
            except TimeoutError:
                raise
            except OSError:
                names = set()
            if (
                any(name.startswith("ascend_pytorch_profiler") and name.endswith(".db") for name in names)
                or any(name in names for name in ("kernel_details.csv", "kernel_details.csv.gz"))
                or any(name.startswith("trace_view") and name.endswith(".json") for name in names)
            ):
                if current_path not in seen:
                    discovered.append(current_path)
                    seen.add(current_path)
                dirnames[:] = []
    return discovered


_STEP_STRING_PATTERNS = (
    "%ProfilerStep#%", "%prefill%", "%Prefill%", "%decode%", "%Decode%",
)


def _string_ids(con: sqlite3.Connection, ids: Iterable[int]) -> dict[int, str]:
    wanted = sorted({int(item) for item in ids})
    if not wanted:
        return {}
    resolved: dict[int, str] = {}
    for start in range(0, len(wanted), 500):
        chunk = wanted[start:start + 500]
        marks = ",".join("?" for _ in chunk)
        for row in con.execute(
            f"SELECT id, value FROM STRING_IDS WHERE id IN ({marks})", chunk
        ):
            resolved[int(row[0])] = str(row[1]) if row[1] is not None else ""
    return resolved


def _native_step_time_windows(
    con: sqlite3.Connection, tables: set[str], *, limit: int,
) -> list[dict[str, Any]]:
    if "STEP_TIME" not in tables:
        return []
    columns = _table_columns(con, "STEP_TIME")
    if not {"id", "startNs", "endNs"} <= columns:
        return []
    rows = con.execute(
        "SELECT id, startNs, endNs FROM STEP_TIME "
        "WHERE startNs IS NOT NULL AND endNs IS NOT NULL AND endNs > startNs "
        "ORDER BY startNs, id LIMIT ?",
        (max(1, int(limit)),),
    ).fetchall()
    return [
        {
            "source_table": "STEP_TIME", "name": f"Step#{int(row[0])}",
            "step": int(row[0]), "start_ns": int(row[1]), "end_ns": int(row[2]),
            "duration_ms": round((int(row[2]) - int(row[1])) / 1_000_000.0, 6),
            "global_tid": None,
        }
        for row in rows
    ]


def _pytorch_step_windows(
    con: sqlite3.Connection, tables: set[str], *, limit: int,
) -> list[dict[str, Any]]:
    if "PYTORCH_API" not in tables:
        return []
    columns = _table_columns(con, "PYTORCH_API")
    name_col = _pick(columns, ("name", "eventName", "message"))
    start_col = _pick(columns, ("startNs", "start_ns", "timestamp"))
    end_col = _pick(columns, ("endNs", "end_ns"))
    tid_col = _pick(columns, ("globalTid", "tid", "threadId"))
    if name_col is None or start_col is None or end_col is None:
        return []
    tid_expr = f", {tid_col}" if tid_col else ", NULL"
    if "STRING_IDS" in tables:
        where = " OR ".join("value LIKE ?" for _ in _STEP_STRING_PATTERNS)
        source = (
            f"SELECT {name_col}, {start_col}, {end_col}{tid_expr} FROM PYTORCH_API "
            f"WHERE {name_col} IN (SELECT id FROM STRING_IDS WHERE {where}) "
            f"AND {end_col} > {start_col} ORDER BY {start_col} LIMIT ?"
        )
        rows = con.execute(source, (*_STEP_STRING_PATTERNS, max(1, int(limit)))).fetchall()
        ids = {int(row[0]) for row in rows if isinstance(row[0], int)}
        strings = _string_ids(con, ids)
    else:
        where = " OR ".join("name LIKE ?" for _ in _STEP_STRING_PATTERNS)
        rows = con.execute(
            f"SELECT {name_col}, {start_col}, {end_col}{tid_expr} FROM PYTORCH_API "
            f"WHERE ({where}) AND {end_col} > {start_col} ORDER BY {start_col} LIMIT ?",
            (*_STEP_STRING_PATTERNS, max(1, int(limit))),
        ).fetchall()
        strings = {}
    steps: list[dict[str, Any]] = []
    for row in rows:
        raw_name = row[0]
        name = strings.get(raw_name, str(raw_name or "")) if isinstance(raw_name, int) else str(raw_name or "")
        match = _STEP_RE.search(name)
        if not match:
            continue
        start_ns, end_ns = int(row[1]), int(row[2])
        steps.append({
            "source_table": "PYTORCH_API", "name": name, "step": int(match.group(1)),
            "start_ns": start_ns, "end_ns": end_ns,
            "duration_ms": round((end_ns - start_ns) / 1_000_000.0, 6),
            "global_tid": None if row[3] is None else str(row[3]),
        })
    return steps


def _db_device_facts(con: sqlite3.Connection, tables: set[str]) -> dict[str, Any]:
    facts: dict[str, Any] = {"detected_npu_names": [], "rank_device_map": []}
    if "NPU_INFO" in tables:
        columns = _table_columns(con, "NPU_INFO")
        name_col = _pick(columns, ("name", "npu_name", "chip_name"))
        if name_col is not None:
            raw = [row[0] for row in con.execute(
                f"SELECT {name_col} FROM NPU_INFO LIMIT 64")]
            ids = {int(value) for value in raw if isinstance(value, int)}
            strings = _string_ids(con, ids) if ("STRING_IDS" in tables and ids) else {}
            facts["detected_npu_names"] = sorted({
                strings.get(value, str(value)) if isinstance(value, int) else str(value)
                for value in raw if value is not None and str(value).strip()
            })
    if "RANK_DEVICE_MAP" in tables:
        columns = _table_columns(con, "RANK_DEVICE_MAP")
        rank_col = _pick(columns, ("rankId", "rank_id", "rank"))
        device_col = _pick(columns, ("deviceId", "device_id", "device"))
        if rank_col is not None and device_col is not None:
            facts["rank_device_map"] = [
                {"rank_id": str(row[0]), "device_id": str(row[1])}
                for row in con.execute(
                    f"SELECT {rank_col}, {device_col} FROM RANK_DEVICE_MAP LIMIT 256")
            ]
    return facts


def _native_windows(
    con: sqlite3.Connection,
    tables: set[str],
    *,
    limit: int = 200,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    steps = _native_step_time_windows(con, tables, limit=limit)
    steps.extend(_pytorch_step_windows(con, tables, limit=limit))
    steps.sort(key=lambda item: (item["start_ns"], item.get("step", 0)))
    mstx: list[dict[str, Any]] = []
    for table in ("MSTX_EVENTS",):
        if table not in tables:
            continue
        columns = _table_columns(con, table)
        name_col = _pick(columns, ("name", "eventName", "message"))
        start_col = _pick(columns, ("startNs", "start_ns", "timestamp"))
        end_col = _pick(columns, ("endNs", "end_ns"))
        tid_col = _pick(columns, ("globalTid", "tid", "threadId"))
        if name_col is None or start_col is None or end_col is None:
            continue
        tid_expr = f", {tid_col}" if tid_col else ", NULL"
        sql = (
            f"SELECT {name_col}, {start_col}, {end_col}{tid_expr} FROM {table} "
            f"WHERE {end_col} > {start_col} ORDER BY {start_col} LIMIT ?"
        )
        rows = con.execute(sql, (max(1, int(limit)) * 50,)).fetchall()
        strings = _string_ids(con, {
            int(row[0]) for row in rows if isinstance(row[0], int)
        })
        for row in rows:
            raw_name = row[0]
            if isinstance(raw_name, int):
                name = strings.get(raw_name, f"<unresolved:{raw_name}>")
            else:
                name = str(raw_name or "")
            start_ns, end_ns = int(row[1]), int(row[2])
            entry = {
                "source_table": table,
                "name": name,
                "start_ns": start_ns,
                "end_ns": end_ns,
                "duration_ms": round((end_ns - start_ns) / 1_000_000.0, 6),
                "global_tid": None if row[3] is None else str(row[3]),
            }
            step_match = _STEP_RE.search(name)
            if step_match:
                entry["step"] = int(step_match.group(1))
                steps.append(entry)
                continue
            phase_match = _PHASE_RE.search(name)
            if phase_match:
                entry["phase"] = phase_match.group(1).lower()
                mstx.append(entry)
    mstx.sort(key=lambda item: item["start_ns"])
    # A native STEP_TIME row outranks an API marker for the same step id.
    by_step: dict[int, dict[str, Any]] = {}
    for item in steps:
        step = item.get("step")
        if step is None:
            continue
        current = by_step.get(step)
        if current is None or (current["source_table"] != "STEP_TIME" and item["source_table"] == "STEP_TIME"):
            by_step[step] = item
    return sorted(by_step.values(), key=lambda item: (item["start_ns"], item["step"]))[:limit], mstx[:limit]


def _capture_span(con: sqlite3.Connection, tables: set[str]) -> dict[str, Any] | None:
    lows: list[int] = []
    highs: list[int] = []
    for table in _TIME_TABLES:
        if table not in tables:
            continue
        columns = _table_columns(con, table)
        start_col = _pick(columns, ("startNs", "start_ns", "timestamp"))
        end_col = _pick(columns, ("endNs", "end_ns"))
        if start_col is None or end_col is None:
            continue
        row = con.execute(f"SELECT MIN({start_col}), MAX({end_col}) FROM {table}").fetchone()
        if row and row[0] is not None and row[1] is not None:
            lows.append(int(row[0]))
            highs.append(int(row[1]))
    if not lows or not highs:
        return None
    start_ns, end_ns = min(lows), max(highs)
    return {
        "start_ns": start_ns,
        "end_ns": end_ns,
        "duration_ms": round((end_ns - start_ns) / 1_000_000.0, 6),
        "basis": "min(startNs)..max(endNs) over available time tables",
    }


def _db_facts(path: Path, *, timeout_s: float) -> dict[str, Any]:
    row = _file_row(path)
    capture_root = path.parent.parent if path.parent.name == _OUTPUT_DIR else path.parent
    facts: dict[str, Any] = {
        **row,
        "kind": "db",
        "source_id": "SRC-" + hashlib.sha256(
            f"{path.resolve()}\x1f{row['size_bytes']}".encode("utf-8")
        ).hexdigest()[:16].upper(),
        "capture_id": "CAP-" + hashlib.sha256(
            str(capture_root.resolve()).encode("utf-8")
        ).hexdigest()[:16].upper(),
        "table_kind": "db",
        "schema_version": None,
        "schema_variant": None,
        "tables": [],
        "core_tables": {name: False for name in _CORE_TABLES},
        "native_step_windows": [],
        "mstx_windows": [],
        "capture_span": None,
        "limitations": [],
    }
    try:
        schema = probe_db(path, timeout_s=timeout_s)
        facts["schema_version"] = schema.schema_version
        facts["schema_variant"] = schema.schema_variant
        facts["tables"] = list(schema.tables)
    except ProfilerError as exc:
        facts["limitations"].append({"code": "db_schema_probe_failed", "detail": str(exc)})
    try:
        con = open_readonly(path, timeout_s=timeout_s, allow_pragma=True)
    except (ProfilerError, sqlite3.Error) as exc:
        facts["limitations"].append({"code": "db_open_failed", "detail": str(exc)})
        return facts
    try:
        deadline = time.perf_counter() + max(0.1, timeout_s)
        con.set_progress_handler(lambda: 1 if time.perf_counter() > deadline else 0, 20_000)
        table_rows = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        tables = {str(item[0]) for item in table_rows}
        facts["tables"] = sorted(tables)
        facts["core_tables"] = {name: name in tables for name in _CORE_TABLES}
        steps, mstx = _native_windows(con, tables)
        facts["native_step_windows"] = steps
        facts["mstx_windows"] = mstx
        facts["capture_span"] = _capture_span(con, tables)
        facts.update(_db_device_facts(con, tables))
        if not steps and not mstx:
            facts["limitations"].append(
                {"code": "native_windows_unavailable", "detail": "no STEP_TIME, ProfilerStep# or MSTX phase rows were found"}
            )
    except sqlite3.Error as exc:
        facts["limitations"].append({"code": "db_query_failed", "detail": str(exc)})
    finally:
        con.close()
    return facts


def _csv_file_fact(path: Path) -> tuple[dict[str, Any], dict[str, Any] | None]:
    row = {**_file_row(path), "kind": "csv"}
    try:
        schema = probe_csv(path)
    except TimeoutError:
        raise
    except (ProfilerError, OSError, ValueError) as exc:
        error = {
            "code": "csv_probe_failed",
            "stage": "header",
            "message": str(exc),
            "path": str(path.resolve()),
        }
        row["read_error"] = error
        return row, error
    row.update(
        {
            "layout": schema.layout,
            "source_kind": schema.source_kind,
            "schema_version": schema.schema_version,
            "schema_variant": schema.schema_variant,
            "source_id": schema.source_id,
            "capture_id": schema.capture_id,
            "table_kind": schema.table_kind,
            "clock": schema.clock.as_dict(),
        }
    )
    return row, None


def _rank_facts(rank_dir: Path, *, ordinal: int, timeout_s: float,
                explicit_file: Path | None = None,
                stop_at: Path | None = None) -> dict[str, Any]:
    boundary = stop_at if stop_at is not None else _bundle_root_for_leaf(rank_dir)
    rank_id = infer_rank_id(rank_dir, ordinal, stop_at=boundary)
    db_candidates = find_db_candidates(rank_dir)
    csv_candidates = find_csv_discovery_candidates(rank_dir)
    selected_csv = find_csv_candidates(rank_dir)
    trace_candidates = find_trace_candidates(rank_dir)
    if explicit_file is not None:
        if explicit_file.suffix == ".db":
            db_candidates, csv_candidates, selected_csv, trace_candidates = [explicit_file], [], [], []
        elif explicit_file.name.endswith((".csv", ".csv.gz")):
            db_candidates, csv_candidates, selected_csv, trace_candidates = [], [explicit_file], [explicit_file], []
        elif explicit_file.name.endswith((".json", ".json.gz")):
            db_candidates, csv_candidates, selected_csv, trace_candidates = [], [], [], [explicit_file]
        else:
            raise ProfilerError(f"unsupported profiling source file: {explicit_file}")
    dbs = [_db_facts(path, timeout_s=timeout_s) for path in db_candidates]
    csv_files: list[dict[str, Any]] = []
    limitations: list[dict[str, Any]] = []
    for path in csv_candidates:
        csv_row, csv_error = _csv_file_fact(path)
        csv_files.append(csv_row)
        if csv_error is not None:
            limitations.append(
                {
                    "code": "csv_read_error",
                    "detail": csv_error["message"],
                    "path": csv_error["path"],
                    "stage": csv_error["stage"],
                }
            )
    files = (
        [*dbs]
        + csv_files
        + [{**_file_row(path), "kind": "json_trace"} for path in trace_candidates]
    )
    if len(db_candidates) > 1:
        limitations.append(
            {
                "code": "multiple_db_candidates",
                "detail": f"{len(db_candidates)} DB candidates; pass one explicit .db path",
                "candidates": [str(item.resolve()) for item in db_candidates],
            }
        )
    if len(selected_csv) > 1:
        limitations.append(
            {
                "code": "multiple_csv_candidates",
                "detail": f"{len(selected_csv)} selectable CSV candidates; pass one explicit .csv path",
                "candidates": [str(item.resolve()) for item in selected_csv],
            }
        )
    if not db_candidates and not csv_candidates and not trace_candidates:
        limitations.append({"code": "no_source_files", "detail": "rank directory has no DB/CSV/trace source"})
    detected_npu_names = sorted({
        str(name) for db in dbs for name in db.get("detected_npu_names", ())
        if str(name).strip()
    })
    rank_device_map = next(
        (db.get("rank_device_map") for db in dbs if db.get("rank_device_map")), []
    )
    native_windows = sorted(
        {
            (item.get("step"), item["start_ns"], item["end_ns"]): item
            for db in dbs for item in db.get("native_step_windows", ())
        }.values(),
        key=lambda item: (item["start_ns"], item.get("step") or 0),
    )
    return {
        "rank_id": rank_id,
        "detected_npu_names": detected_npu_names,
        "rank_device_map": rank_device_map,
        "native_step_windows": native_windows,
        "capture_span": next(
            (db.get("capture_span") for db in dbs if db.get("capture_span")), None),
        "rank_index": infer_rank_index(rank_dir, stop_at=boundary),
        "rank_dir": str(rank_dir.resolve()),
        "db_candidates": [str(item.resolve()) for item in db_candidates],
        "csv_candidates": [str(item.resolve()) for item in csv_candidates],
        "selected_csv": [str(item.resolve()) for item in selected_csv],
        "csv_selection_status": (
            "ambiguous" if len(selected_csv) > 1
            else "selected" if len(selected_csv) == 1
            else "none"
        ),
        "trace_candidates": [str(item.resolve()) for item in trace_candidates],
        "files": files,
        "limitations": limitations,
    }


def _resolve_jobs(jobs: int | None, count: int) -> int:
    if jobs is None:
        return 1 if count <= 1 else max(1, min(count, os.cpu_count() or 4, 8))
    if isinstance(jobs, bool) or not isinstance(jobs, int) or jobs < 1:
        raise ProfilerError("jobs must be a positive integer")
    return jobs


def inventory_profile(
    root: str | Path,
    *,
    max_dirs: int = 4096,
    timeout_s: float = 5.0,
    jobs: int | None = None,
) -> dict[str, Any]:
    """Return a bounded inventory object for a directory or a single source file."""

    path = Path(root).expanduser()
    if not path.exists():
        raise ProfilerError(f"profiling root not found: {path}")
    work: list[tuple[int, Path, Path | None]] = []
    if path.is_file():
        rank_dir = path.parent.parent if path.parent.name in {_OUTPUT_DIR, MINDSTUDIO_OUTPUT_DIR} else path.parent
        work.append((0, rank_dir, path))
    else:
        resolved = path.resolve()
        if resolved.name in {_OUTPUT_DIR, MINDSTUDIO_OUTPUT_DIR}:
            resolved = resolved.parent
        own = find_db_candidates(resolved) + find_csv_candidates(resolved) + find_trace_candidates(resolved)
        if own:
            work.append((0, resolved, None))
        else:
            work = [
                (ordinal, rank_dir, None)
                for ordinal, rank_dir in enumerate(
                    sorted(_discover_rank_dirs(resolved, max_dirs=max_dirs), key=str))
            ]
    resolved_jobs = _resolve_jobs(jobs, len(work))
    if resolved_jobs <= 1 or len(work) <= 1:
        ranks = [
            _rank_facts(rank_dir, ordinal=ordinal, timeout_s=timeout_s,
                        explicit_file=explicit, stop_at=None if path.is_file() else path.resolve())
            for ordinal, rank_dir, explicit in work
        ]
    else:
        from concurrent.futures import ThreadPoolExecutor
        boundary = path.resolve()

        def probe(item: tuple[int, Path, Path | None]) -> dict[str, Any]:
            ordinal, rank_dir, explicit = item
            return _rank_facts(rank_dir, ordinal=ordinal, timeout_s=timeout_s,
                               explicit_file=explicit, stop_at=boundary)

        with ThreadPoolExecutor(max_workers=resolved_jobs) as pool:
            ranks = list(pool.map(probe, work))
    ranks.sort(key=lambda rank: (
        rank.get("rank_index") is None,
        rank.get("rank_index") if rank.get("rank_index") is not None else 0,
        str(rank.get("rank_id")),
    ))
    if not ranks:
        raise ProfilerError(f"no rank/source candidates found under {path}")
    limitations: list[dict[str, Any]] = []
    for rank in ranks:
        limitations.extend(
            {"rank_id": rank["rank_id"], **item} for item in rank.get("limitations", [])
        )
    capture_ids = sorted(
        {
            file_fact["capture_id"]
            for rank in ranks
            for file_fact in rank.get("files", [])
            if file_fact.get("capture_id")
        }
    )
    detected_skus = sorted({
        name for rank in ranks for name in rank.get("detected_npu_names", ())
    })
    return {
        "schema_version": INVENTORY_SCHEMA,
        "root": str(path.resolve()),
        "rank_count": len(ranks),
        "jobs": resolved_jobs,
        "detected_hardware_sku": detected_skus[0] if len(detected_skus) == 1 else None,
        "capture_count": len(capture_ids),
        "capture_ids": capture_ids,
        "ranks": ranks,
        "source_priority": "DB > CSV > JSON Trace; only one authority per metric",
        "identity_policy": "path+size_bytes+mtime_ns+schema_version; no SHA256 by default",
        "limitations": limitations,
    }


__all__ = ["INVENTORY_SCHEMA", "inventory_profile"]
