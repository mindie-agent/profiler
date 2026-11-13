"""Bounded read-only COMMUNICATION_OP query and relational TASK join.

[Role]
  Read Ascend profiler ``COMMUNICATION_OP`` rows within an explicit window and
  join each call to a unique containing ``TASK`` row via real ``connectionId``
  and ``deviceId`` keys when present in the schema.

[Invariants]
  * ``connectionId`` is optional in minimal ``TASK``/``COMMUNICATION_OP``
    schemas; absent columns never trigger invalid SQL or fabricate empty string
    keys (``None`` stays ``None``).
  * Every ``COMMUNICATION_OP`` and ``TASK`` query enforces ``max_rows + 1``
    with deterministic ``ORDER BY``; row-budget overflow raises
    ``ProfilerQueryError`` and is never silently truncated.
  * A ``TASK`` row binds to ``COMMUNICATION_OP`` only when ``(connectionId,
    deviceId)`` matches and the interval contains (preferring exact match) a
    unique ``TASK`` occurrence; ambiguous or missing matches remain unresolved.

[Timeouts & Locks]
  Executes on the caller-owned read-only SQLite connection under its active
  progress-handler deadline; holds no independent locks.

[Side-Effect Policy]
  Read-only SQLite queries and ``QueryStats`` counter updates only; no writes.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
import sqlite3
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from .events import Event, ProfilerQueryError, QueryStats, Window

_CHUNK_SIZE = 500


def _check_deadline(
    deadline: float | None,
    schema_path: str,
    window: Window,
    timeout_s: float,
) -> None:
    if deadline is not None and time.perf_counter() > deadline:
        raise ProfilerQueryError(
            f"{Path(schema_path).name}: query exceeded {timeout_s:.1f}s for "
            f"window {window.label or window.step}"
        )


class _ContainingTaskIndex:
    """O(log N) exact-preferring interval containment index per (connectionId, deviceId)."""

    __slots__ = ("rows", "starts", "ends", "top1_end", "top1_idx", "top2_end")

    def __init__(self, raw_rows: list[tuple[Any, ...]]) -> None:
        raw_rows.sort(key=lambda r: (_as_int(r[5]), _as_int(r[6]), _as_int(r[2])))
        self.rows = raw_rows
        self.starts = [_as_int(r[5]) for r in raw_rows]
        self.ends = [_as_int(r[6]) for r in raw_rows]
        top1_end: list[int] = []
        top1_idx: list[int] = []
        top2_end: list[int] = []
        best_end = -1
        best_idx = -1
        second_end = -1
        for idx, end_val in enumerate(self.ends):
            if end_val >= best_end:
                second_end = best_end
                best_end = end_val
                best_idx = idx
            elif end_val > second_end:
                second_end = end_val
            top1_end.append(best_end)
            top1_idx.append(best_idx)
            top2_end.append(second_end)
        self.top1_end = top1_end
        self.top1_idx = top1_idx
        self.top2_end = top2_end

    def unique_bound(self, start_ns: int, end_ns: int) -> tuple[Any, ...] | None:
        lo_eq = bisect_left(self.starts, start_ns)
        hi_eq = bisect_right(self.starts, start_ns)
        eq_lo = bisect_left(self.ends, end_ns, lo_eq, hi_eq)
        eq_hi = bisect_right(self.ends, end_ns, lo_eq, hi_eq)
        exact_count = eq_hi - eq_lo
        if exact_count == 1:
            return self.rows[eq_lo]
        if exact_count > 1:
            return None
        same_start_containing = hi_eq - eq_hi
        if lo_eq == 0 or self.top1_end[lo_eq - 1] < end_ns:
            prior_containing = 0
            prior_task = None
        elif self.top2_end[lo_eq - 1] >= end_ns:
            return None
        else:
            prior_containing = 1
            prior_task = self.rows[self.top1_idx[lo_eq - 1]]
        if same_start_containing + prior_containing != 1:
            return None
        return self.rows[eq_hi] if same_start_containing == 1 else prior_task


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text != "" else None


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _enum_lookup(
    con: sqlite3.Connection,
    tables: tuple[str, ...],
    table: str,
    columns_fn: Callable[[sqlite3.Connection, str], set[str]],
) -> dict[int, str]:
    if table not in tables:
        return {}
    cols = columns_fn(con, table)
    if not {"id", "name"} <= cols:
        return {}
    rows = con.execute(f"SELECT id, name FROM {table} ORDER BY id LIMIT 10000").fetchall()
    result: dict[int, str] = {}
    for row in rows:
        key = _as_optional_int(row[0])
        if key is not None and row[1] is not None:
            result[key] = str(row[1])
    return result


def _optional_string(
    strings: Mapping[int, str],
    value: Any,
) -> str | None:
    if value is None:
        return None
    key = _as_optional_int(value)
    if key is None:
        text = str(value)
        return text if text else None
    if key in strings:
        return strings[key]
    return f"<unresolved:{key}>"


def _optional_enum(
    enums: Mapping[int, str],
    strings: Mapping[int, str],
    value: Any,
) -> str | None:
    """Resolve enum-typed columns (e.g. algType) from the enum table before STRING_IDS."""
    if value is None:
        return None
    key = _as_optional_int(value)
    if key is None:
        text = str(value)
        return text if text else None
    if key in enums:
        return enums[key]
    if not enums and key in strings:
        return strings[key]
    return f"<unresolved:{key}>"


def read_communication_events(
    con: sqlite3.Connection,
    *,
    schema_path: str,
    source_kind: str,
    tables: tuple[str, ...],
    comm_table: str,
    task_table: str,
    task_columns: set[str],
    columns_fn: Callable[[sqlite3.Connection, str], set[str]],
    text_fn: Callable[[Mapping[int, str], Any, list[int]], str],
    strings: Mapping[int, str],
    unresolved: list[int],
    window: Window,
    max_rows: int,
    stats: QueryStats,
    deadline: float | None = None,
    timeout_s: float = 20.0,
) -> list[Event]:
    """Read windowed ``COMMUNICATION_OP`` events with optional relational TASK join."""
    _check_deadline(deadline, schema_path, window, timeout_s)
    comm_columns = columns_fn(con, comm_table)
    optional = {
        name: (name if name in comm_columns else "NULL")
        for name in ("connectionId", "algType", "dataType", "count", "groupName", "rankSize")
    }
    comm_sql = (
        "SELECT rowid, opName, opType, startNs, endNs, deviceId, "
        f"{optional['connectionId']}, {optional['algType']}, "
        f"{optional['dataType']}, {optional['count']}, "
        f"{optional['groupName']}, {optional['rankSize']} "
        f"FROM {comm_table} WHERE endNs > ? AND startNs < ? ORDER BY startNs, rowid LIMIT ?"
    )
    comm_rows = con.execute(
        comm_sql, (window.start_ns, window.end_ns, max_rows + 1)
    ).fetchall()
    stats.rows_read += len(comm_rows)
    if len(comm_rows) > max_rows:
        raise ProfilerQueryError(
            f"{Path(schema_path).name}: comm window {window.label or window.step} "
            f"exceeded row budget {max_rows}"
        )
    stats.comm_rows = len(comm_rows)
    if not comm_rows:
        return []

    can_join_task = "connectionId" in comm_columns and "connectionId" in task_columns
    task_indexes: dict[tuple[str, str], _ContainingTaskIndex] = {}
    if can_join_task:
        conn_values = sorted(
            {row[6] for row in comm_rows if _optional_text(row[6]) is not None},
            key=str,
        )
        valid_spans = [
            (_as_int(row[3]), _as_int(row[4]))
            for row in comm_rows
            if row[3] is not None and row[4] is not None and _as_int(row[4]) > _as_int(row[3])
        ]
        query_lo = min([window.start_ns, *(s for s, _ in valid_spans)])
        query_hi = max([window.end_ns, *(e for _, e in valid_spans)])
        tasks_by_connection: dict[tuple[str, str], list[tuple[Any, ...]]] = {}
        task_read = 0
        for offset in range(0, len(conn_values), _CHUNK_SIZE):
            _check_deadline(deadline, schema_path, window, timeout_s)
            chunk = conn_values[offset : offset + _CHUNK_SIZE]
            marks = ", ".join("?" for _ in chunk)
            remaining = (max_rows - task_read) + 1
            task_sql = (
                "SELECT connectionId, deviceId, globalTaskId, streamId, taskId, startNs, endNs "
                f"FROM {task_table} WHERE connectionId IN ({marks}) "
                "AND endNs > ? AND startNs < ? ORDER BY startNs, globalTaskId LIMIT ?"
            )
            batch = con.execute(
                task_sql, (*chunk, query_lo, query_hi, remaining)
            ).fetchall()
            task_read += len(batch)
            stats.rows_read += len(batch)
            if task_read > max_rows:
                raise ProfilerQueryError(
                    f"{Path(schema_path).name}: comm TASK join window {window.label or window.step} "
                    f"exceeded row budget {max_rows}"
                )
            for task in batch:
                conn_text = _optional_text(task[0])
                if conn_text is None or task[5] is None or task[6] is None:
                    continue
                if _as_int(task[6]) <= _as_int(task[5]):
                    continue
                dev_text = "" if task[1] is None else str(task[1])
                tasks_by_connection.setdefault((conn_text, dev_text), []).append(task)
        for key, raw_list in tasks_by_connection.items():
            _check_deadline(deadline, schema_path, window, timeout_s)
            task_indexes[key] = _ContainingTaskIndex(raw_list)

    algo_enums = _enum_lookup(con, tables, "ENUM_HCCL_ALGO_TYPE", columns_fn)
    events: list[Event] = []
    for idx, row in enumerate(comm_rows):
        if (idx & 255) == 0:
            _check_deadline(deadline, schema_path, window, timeout_s)
        if row[3] is None or row[4] is None or _as_int(row[4]) <= _as_int(row[3]):
            stats.bad_rows += 1
            continue
        start_ns = _as_int(row[3])
        end_ns = _as_int(row[4])
        device_id = "" if row[5] is None else str(row[5])
        connection_id = _optional_text(row[6]) if "connectionId" in comm_columns else None
        bound_task = None
        if can_join_task and connection_id is not None:
            index = task_indexes.get((connection_id, device_id))
            if index is not None:
                bound_task = index.unique_bound(start_ns, end_ns)

        global_task_id = _optional_text(bound_task[2]) if bound_task is not None else None
        stream_id = ("" if bound_task[3] is None else str(bound_task[3])) if bound_task is not None else ""
        task_id = ("" if bound_task[4] is None else str(bound_task[4])) if bound_task is not None else ""
        if bound_task is not None:
            join_status = "connection_and_interval"
        elif not can_join_task or connection_id is None:
            join_status = "unresolved_connection_id_absent"
        else:
            join_status = "unresolved_no_unique_connection_task"

        locator: dict[str, Any] = {
            "source": schema_path,
            "table": comm_table,
            "rowid": _as_optional_int(row[0]),
            "device_id": device_id,
            "connection_id": connection_id,
            "global_task_id": global_task_id,
            "stream_id": stream_id,
            "task_id": task_id,
            "algorithm": _optional_enum(algo_enums, strings, row[7]),
            "data_type": _as_optional_int(row[8]),
            "count": _as_optional_int(row[9]),
            "group_name": _optional_string(strings, row[10]),
            "rank_size": _as_optional_int(row[11]),
            "task_join_status": join_status,
        }
        events.append(
            Event(
                rank_id="",
                rank_index=None,
                name=text_fn(strings, row[1], unresolved),
                op_type=text_fn(strings, row[2], unresolved),
                task_type="COMMUNICATION",
                core="COMMUNICATION",
                stream_id=stream_id,
                task_id=task_id,
                device_id=device_id,
                start_ns=start_ns,
                end_ns=end_ns,
                source_kind=source_kind,
                table=comm_table,
                wait_status="not_applicable",
                pmu_status="not_applicable",
                pmu_kind="not_applicable",
                locator=locator,
            )
        )
    return events


__all__ = ["read_communication_events"]
