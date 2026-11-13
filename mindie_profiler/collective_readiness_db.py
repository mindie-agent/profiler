"""Deadline-guarded SQLite queries and interval index for collective readiness.

[Role]
  Execute read-only SQLite queries for ``COMMUNICATION_OP``, ``TASK``,
  ``STRING_IDS``, and native child tables across disjoint time windows, detect
  full-capture ``globalTaskId`` ambiguity, and index ``TASK`` intervals for
  ``O(log N + K)`` overlap and stream-predecessor lookups.

[Invariants]
  * Referenced integer string IDs are resolved via chunked ``WHERE id IN (...)``
    queries with no ``LIMIT 200000`` truncation; missing IDs record
    ``unresolved_string_ids``.
  * Repeated ``globalTaskId`` values across full-capture ``TASK`` or within any
    child info table are added to ``ambiguous_globals`` and excluded from child
    joins.
  * Every SQLite query and Python index step checks the shared wall-clock
    ``deadline`` and raises ``ProfilerQueryError`` on expiry.

[Timeouts & Locks]
  Enforces caller-supplied monotonic ``deadline``; holds zero locks.

[Side-Effect Policy]
  Read-only queries over caller-supplied ``sqlite3.Connection``; mutates only
  caller-passed ``limitations`` / ``ambiguous_globals`` sets.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
import sqlite3
import time
from typing import Any, Iterable, Sequence

from .accounting import merge_intervals
from .events import ProfilerQueryError, ProfilerUsageError

MAX_CALLS = 20_000
MAX_TOTAL_CALLS = 20_000
MAX_TASKS = 20_000
MAX_CHILDREN = 2_000
MAX_OVERLAP_SCAN_PER_CALL = 256
MIN_SQLITE_LOCK_BUDGET_S = 3.0
_CHUNK_SIZE = 400
_WINDOW_CHUNK = 64
MAX_NS = 9_223_372_036_854_775_807


def chunks(items: Iterable[Any], size: int = _CHUNK_SIZE):
    seq = list(items)
    for start in range(0, len(seq), size):
        yield seq[start : start + size]


def check_deadline(deadline: float, db_label: str, timeout_s: float) -> None:
    if time.monotonic() > deadline:
        raise ProfilerQueryError(
            f"{db_label}: collective readiness query exceeded {timeout_s:.1f}s"
        )


def fetch_rows(
    db: sqlite3.Connection,
    db_label: str,
    sql: str,
    args: Sequence[Any] = (),
    limit: int = MAX_TASKS,
    *,
    deadline: float,
    timeout_s: float,
) -> list[sqlite3.Row]:
    check_deadline(deadline, db_label, timeout_s)
    try:
        out = list(db.execute(sql, tuple(args)).fetchmany(limit))
    except TimeoutError:
        raise
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower() or time.monotonic() > deadline:
            raise ProfilerQueryError(
                f"{db_label}: collective readiness query exceeded {timeout_s:.1f}s"
            ) from exc
        raise ProfilerQueryError(
            f"{db_label}: collective readiness query failed: {exc}"
        ) from exc
    except sqlite3.Error as exc:
        raise ProfilerQueryError(
            f"{db_label}: collective readiness query failed: {exc}"
        ) from exc
    check_deadline(deadline, db_label, timeout_s)
    return out


def table_names(
    db: sqlite3.Connection, db_label: str, *, deadline: float, timeout_s: float
) -> set[str]:
    rows = fetch_rows(
        db,
        db_label,
        "SELECT name FROM sqlite_master WHERE type='table'",
        limit=10_000,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    return {str(row["name"]) for row in rows}


def column_names(
    db: sqlite3.Connection,
    db_label: str,
    tables: set[str],
    table: str,
    *,
    deadline: float,
    timeout_s: float,
) -> set[str]:
    if table not in tables:
        return set()
    rows = fetch_rows(
        db,
        db_label,
        f"PRAGMA table_info({table})",
        limit=1_000,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    return {str(row["name"]) for row in rows}


def int_id(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_strings(
    db: sqlite3.Connection,
    db_label: str,
    tables: set[str],
    referenced_ids: set[int],
    limitations: set[str],
    *,
    deadline: float,
    timeout_s: float,
) -> dict[str, str]:
    if not referenced_ids:
        return {}
    cols = column_names(
        db, db_label, tables, "STRING_IDS", deadline=deadline, timeout_s=timeout_s
    )
    if not {"id", "value"} <= cols:
        limitations.add("unresolved_string_ids")
        return {}
    resolved: dict[str, str] = {}
    for chunk in chunks(sorted(referenced_ids)):
        marks = ",".join("?" for _ in chunk)
        rows = fetch_rows(
            db,
            db_label,
            f"SELECT id, value FROM STRING_IDS WHERE id IN ({marks})",
            chunk,
            len(chunk) + 1,
            deadline=deadline,
            timeout_s=timeout_s,
        )
        for row in rows:
            if row["value"] is not None:
                resolved[str(row["id"])] = str(row["value"])
    if any(str(item) not in resolved for item in referenced_ids):
        limitations.add("unresolved_string_ids")
    return resolved


def enum_map(
    db: sqlite3.Connection,
    db_label: str,
    tables: set[str],
    table: str,
    *,
    deadline: float,
    timeout_s: float,
) -> dict[str, str]:
    cols = column_names(db, db_label, tables, table, deadline=deadline, timeout_s=timeout_s)
    if not {"id", "name"} <= cols:
        return {}
    rows = fetch_rows(
        db,
        db_label,
        f"SELECT id, name FROM {table} LIMIT 10000",
        limit=10_000,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    return {str(row["id"]): str(row["name"]) for row in rows if row["name"] is not None}


def find_ambiguous_task_globals(
    db: sqlite3.Connection,
    db_label: str,
    global_ids: Iterable[Any],
    *,
    deadline: float,
    timeout_s: float,
) -> set[str]:
    unique_ids = sorted({int(item) for item in global_ids if int_id(item) is not None})
    ambiguous: set[str] = set()
    for chunk in chunks(unique_ids):
        marks = ",".join("?" for _ in chunk)
        rows = fetch_rows(
            db,
            db_label,
            f"SELECT globalTaskId, COUNT(*) AS cnt FROM TASK "
            f"WHERE globalTaskId IN ({marks}) GROUP BY globalTaskId HAVING cnt > 1",
            chunk,
            len(chunk) + 1,
            deadline=deadline,
            timeout_s=timeout_s,
        )
        for row in rows:
            ambiguous.add(str(row["globalTaskId"]))
    return ambiguous


def _read_child_table(
    db: sqlite3.Connection,
    db_label: str,
    table: str,
    cols: set[str],
    unique_ids: Sequence[int],
    ambiguous_globals: set[str],
    limitations: set[str],
    string_ids: set[int],
    *,
    deadline: float,
    timeout_s: float,
) -> dict[str, dict[str, Any]]:
    if not {"globalTaskId", "name", "taskType"} <= cols:
        return {}
    extra = ""
    if table == "COMPUTE_TASK_INFO":
        extra = ", opType" if "opType" in cols else ", NULL AS opType"
    elif table == "COMMUNICATION_TASK_INFO":
        extra = ", timestampNs" if "timestampNs" in cols else ", NULL AS timestampNs"
    seen: set[str] = set()
    out: dict[str, dict[str, Any]] = {}
    for chunk in chunks(unique_ids):
        marks = ",".join("?" for _ in chunk)
        dup_rows = fetch_rows(
            db,
            db_label,
            f"SELECT globalTaskId FROM {table} "
            f"WHERE globalTaskId IN ({marks}) "
            f"GROUP BY globalTaskId HAVING COUNT(*) > 1 LIMIT ?",
            (*chunk, len(chunk) + 1),
            len(chunk) + 1,
            deadline=deadline,
            timeout_s=timeout_s,
        )
        chunk_dups = {
            str(item["globalTaskId"])
            for item in dup_rows
            if item["globalTaskId"] is not None
        }
        if chunk_dups:
            ambiguous_globals.update(chunk_dups)
            limitations.add("ambiguous_global_task_id")
            for gid in chunk_dups:
                out.pop(gid, None)
        non_dup_chunk = [gid for gid in chunk if str(gid) not in ambiguous_globals]
        if not non_dup_chunk:
            continue
        nd_marks = ",".join("?" for _ in non_dup_chunk)
        rows = fetch_rows(
            db,
            db_label,
            f"SELECT globalTaskId, name, taskType{extra} FROM {table} "
            f"WHERE globalTaskId IN ({nd_marks}) ORDER BY globalTaskId LIMIT ?",
            (*non_dup_chunk, MAX_CHILDREN + 1),
            MAX_CHILDREN + 1,
            deadline=deadline,
            timeout_s=timeout_s,
        )
        if len(rows) > MAX_CHILDREN:
            limitations.add("child_row_budget_reached")
            rows = rows[:MAX_CHILDREN]
        for row in rows:
            gid = str(row["globalTaskId"])
            if gid in seen:
                out.pop(gid, None)
                ambiguous_globals.add(gid)
                limitations.add("ambiguous_global_task_id")
                continue
            seen.add(gid)
            if (sid := int_id(row["name"])) is not None:
                string_ids.add(sid)
            record: dict[str, Any] = {
                "source_table": table,
                "global_task_id": gid,
                "_name_id": row["name"],
                "task_type": str(row["taskType"]),
            }
            if table == "COMPUTE_TASK_INFO":
                if (sid := int_id(row["opType"])) is not None:
                    string_ids.add(sid)
                record["_op_type_id"] = row["opType"]
            elif table == "COMMUNICATION_TASK_INFO":
                record["timestamp_ns"] = (
                    int(row["timestampNs"]) if row["timestampNs"] is not None else None
                )
            out[gid] = record
    return out


def load_raw_children(
    db: sqlite3.Connection,
    db_label: str,
    tables: set[str],
    global_ids: Iterable[Any],
    ambiguous_globals: set[str],
    limitations: set[str],
    *,
    deadline: float,
    timeout_s: float,
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    set[int],
]:
    unique_ids = sorted(
        {
            int(item)
            for item in global_ids
            if int_id(item) is not None and str(item) not in ambiguous_globals
        }
    )
    string_ids: set[int] = set()
    if not unique_ids:
        return {}, {}, {}, string_ids
    compute = _read_child_table(
        db,
        db_label,
        "COMPUTE_TASK_INFO",
        column_names(
            db, db_label, tables, "COMPUTE_TASK_INFO", deadline=deadline, timeout_s=timeout_s
        ),
        unique_ids,
        ambiguous_globals,
        limitations,
        string_ids,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    comm = _read_child_table(
        db,
        db_label,
        "COMMUNICATION_TASK_INFO",
        column_names(
            db, db_label, tables, "COMMUNICATION_TASK_INFO", deadline=deadline, timeout_s=timeout_s
        ),
        unique_ids,
        ambiguous_globals,
        limitations,
        string_ids,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    schedule = _read_child_table(
        db,
        db_label,
        "COMMUNICATION_SCHEDULE_TASK_INFO",
        column_names(
            db,
            db_label,
            tables,
            "COMMUNICATION_SCHEDULE_TASK_INFO",
            deadline=deadline,
            timeout_s=timeout_s,
        ),
        unique_ids,
        ambiguous_globals,
        limitations,
        string_ids,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    for gid in list(ambiguous_globals):
        compute.pop(gid, None)
        comm.pop(gid, None)
        schedule.pop(gid, None)
    return compute, comm, schedule, string_ids


class TaskGroupIndex:
    """Segment max-tree index for guaranteed O((1 + K) log N) overlap lookup."""

    __slots__ = ("tasks", "starts", "tree_size", "tree", "by_stream")

    def __init__(self, rows: list[sqlite3.Row]) -> None:
        rows.sort(key=lambda r: (int(r["startNs"]), int(r["endNs"]), int(r["globalTaskId"] or 0)))
        self.tasks = rows
        self.starts = [int(r["startNs"]) for r in rows]
        n = len(rows)
        size = 1
        while size < max(1, n):
            size <<= 1
        self.tree_size = size if n > 0 else 0
        tree = [-1] * (2 * size) if n > 0 else []
        stream_buckets: dict[str, list[sqlite3.Row]] = {}
        for idx, row in enumerate(rows):
            row_start = int(row["startNs"])
            row_end = int(row["endNs"])
            tree[size + idx] = row_end if row_end > row_start else (row_end + 1)
            stream_buckets.setdefault(str(row["streamId"]), []).append(row)
        for node in range(size - 1, 0, -1):
            if not tree:
                break
            left = tree[node << 1]
            right_val = tree[(node << 1) | 1]
            tree[node] = left if left >= right_val else right_val
        self.tree = tree
        self.by_stream: dict[str, tuple[list[int], list[sqlite3.Row]]] = {}
        for stream_id, bucket in stream_buckets.items():
            bucket.sort(key=lambda r: (int(r["endNs"]), int(r["globalTaskId"] or 0)))
            self.by_stream[stream_id] = ([int(r["endNs"]) for r in bucket], bucket)

    def overlapping(
        self, start_ns: int, end_ns: int, *, scan_limit: int = MAX_OVERLAP_SCAN_PER_CALL
    ) -> tuple[list[sqlite3.Row], bool]:
        """Return tasks overlapping half-open [start_ns, end_ns) in O((1 + K) log N)."""
        right = (
            bisect_left(self.starts, end_ns)
            if end_ns > start_ns
            else bisect_right(self.starts, end_ns)
        )
        min_eff = (start_ns + 1) if end_ns > start_ns else start_ns
        if right <= 0 or self.tree_size == 0 or self.tree[1] < min_eff:
            return [], False
        matched: list[sqlite3.Row] = []
        capped = False
        stack: list[tuple[int, int, int]] = [(1, 0, self.tree_size)]
        while stack:
            node, seg_l, seg_r = stack.pop()
            if seg_l >= right or self.tree[node] < min_eff:
                continue
            if seg_r - seg_l == 1:
                row = self.tasks[seg_l]
                if end_ns <= start_ns and int(row["endNs"]) < start_ns:
                    continue
                if len(matched) >= scan_limit:
                    capped = True
                    break
                matched.append(row)
                continue
            mid = (seg_l + seg_r) >> 1
            if mid < right and self.tree[(node << 1) | 1] >= min_eff:
                stack.append(((node << 1) | 1, mid, seg_r))
            if self.tree[node << 1] >= min_eff:
                stack.append((node << 1, seg_l, mid))
        return matched, capped

    def prior_on_stream(
        self, stream_id: str, op_start_ns: int, exclude_global_id: str
    ) -> sqlite3.Row | None:
        entry = self.by_stream.get(stream_id)
        if entry is None:
            return None
        ends, bucket = entry
        idx = bisect_right(ends, op_start_ns) - 1
        while idx >= 0:
            cand = bucket[idx]
            if str(cand["globalTaskId"]) != exclude_global_id:
                return cand
            idx -= 1
        return None


def normalize_intervals(
    start_ns: int | None,
    end_ns: int | None,
    windows: Sequence[tuple[int, int]] | None,
) -> list[tuple[int, int]]:
    if windows is not None:
        parsed: list[tuple[int, int]] = []
        for lo, hi in windows:
            lo_i, hi_i = int(lo), int(hi)
            if hi_i <= lo_i:
                raise ProfilerUsageError(f"invalid readiness window ({lo_i}, {hi_i})")
            parsed.append((lo_i, hi_i))
        return merge_intervals(parsed)
    lo = int(start_ns) if start_ns is not None else 0
    hi = int(end_ns) if end_ns is not None else MAX_NS
    if hi <= lo:
        raise ProfilerUsageError(f"invalid readiness bounds ({lo}, {hi})")
    return [(lo, hi)]


def _sort_calls(calls: list[sqlite3.Row]) -> list[sqlite3.Row]:
    calls.sort(
        key=lambda r: (int(r["startNs"]), int(r["opId"]) if int_id(r["opId"]) is not None else 0)
    )
    return calls


def query_windowed_calls(
    db: sqlite3.Connection,
    db_label: str,
    selected: Sequence[str],
    order_col: str,
    intervals: Sequence[tuple[int, int]],
    limitations: set[str],
    *,
    deadline: float,
    timeout_s: float,
    max_calls: int = MAX_CALLS,
) -> list[sqlite3.Row]:
    del order_col
    seen_ops: set[str] = set()
    calls: list[sqlite3.Row] = []
    select_cols = ",".join(["rowid AS _rowid", *selected])
    if max_calls <= 0:
        for win_chunk in chunks(intervals, _WINDOW_CHUNK):
            where = " OR ".join("(endNs>? AND startNs<?)" for _ in win_chunk)
            params: list[Any] = []
            for lo, hi in win_chunk:
                params.extend((lo, hi))
            probe = fetch_rows(
                db,
                db_label,
                f"SELECT 1 FROM COMMUNICATION_OP WHERE ({where}) LIMIT 1",
                params,
                1,
                deadline=deadline,
                timeout_s=timeout_s,
            )
            if probe:
                limitations.add("call_row_budget_reached")
                break
        return []
    for win_chunk in chunks(intervals, _WINDOW_CHUNK):
        where = " OR ".join("(endNs>? AND startNs<?)" for _ in win_chunk)
        win_params: list[Any] = []
        for lo, hi in win_chunk:
            win_params.extend((lo, hi))
        cursor: tuple[int, int] | None = None
        while True:
            fetch_limit = max(1, (max_calls - len(calls)) + 1)
            if cursor is None:
                sql = (
                    f"SELECT {select_cols} FROM COMMUNICATION_OP "
                    f"WHERE ({where}) ORDER BY startNs ASC, rowid ASC LIMIT ?"
                )
                params = [*win_params, fetch_limit]
            else:
                sql = (
                    f"SELECT {select_cols} FROM COMMUNICATION_OP "
                    f"WHERE ({where}) AND (startNs>? OR (startNs=? AND rowid>?)) "
                    "ORDER BY startNs ASC, rowid ASC LIMIT ?"
                )
                params = [*win_params, cursor[0], cursor[0], cursor[1], fetch_limit]
            batch = fetch_rows(
                db,
                db_label,
                sql,
                params,
                fetch_limit,
                deadline=deadline,
                timeout_s=timeout_s,
            )
            for row in batch:
                op_key = str(row["opId"])
                if op_key in seen_ops:
                    continue
                if len(calls) >= max_calls:
                    limitations.add("call_row_budget_reached")
                    return _sort_calls(calls)
                seen_ops.add(op_key)
                calls.append(row)
            if len(batch) < fetch_limit:
                break
            cursor = (int(batch[-1]["startNs"]), int(batch[-1]["_rowid"]))
    return _sort_calls(calls)


def query_windowed_tasks(
    db: sqlite3.Connection,
    db_label: str,
    devices: Sequence[str],
    intervals: Sequence[tuple[int, int]],
    limitations: set[str],
    *,
    deadline: float,
    timeout_s: float,
) -> list[sqlite3.Row]:
    task_rows: list[sqlite3.Row] = []
    seen_rowids: set[int] = set()
    for dev_chunk in chunks(devices):
        dev_marks = ",".join("?" for _ in dev_chunk)
        for win_chunk in chunks(intervals, _WINDOW_CHUNK):
            where_win = " OR ".join("(endNs>? AND startNs<?)" for _ in win_chunk)
            base_params: list[Any] = list(dev_chunk)
            for lo, hi in win_chunk:
                base_params.extend((lo, hi))
            cursor: tuple[int, int] | None = None
            while True:
                fetch_limit = max(1, (MAX_TASKS - len(task_rows)) + 1)
                if cursor is None:
                    sql = (
                        "SELECT rowid AS _rowid,startNs,endNs,connectionId,deviceId,globalTaskId,"
                        f"streamId,taskId,taskType FROM TASK WHERE deviceId IN ({dev_marks}) "
                        f"AND ({where_win}) ORDER BY startNs ASC, rowid ASC LIMIT ?"
                    )
                    params = [*base_params, fetch_limit]
                else:
                    sql = (
                        "SELECT rowid AS _rowid,startNs,endNs,connectionId,deviceId,globalTaskId,"
                        f"streamId,taskId,taskType FROM TASK WHERE deviceId IN ({dev_marks}) "
                        f"AND ({where_win}) AND (startNs>? OR (startNs=? AND rowid>?)) "
                        "ORDER BY startNs ASC, rowid ASC LIMIT ?"
                    )
                    params = [*base_params, cursor[0], cursor[0], cursor[1], fetch_limit]
                batch = fetch_rows(
                    db,
                    db_label,
                    sql,
                    params,
                    fetch_limit,
                    deadline=deadline,
                    timeout_s=timeout_s,
                )
                for row in batch:
                    rid = int(row["_rowid"])
                    if rid in seen_rowids:
                        continue
                    if len(task_rows) >= MAX_TASKS:
                        limitations.add("task_row_budget_reached")
                        return task_rows
                    seen_rowids.add(rid)
                    task_rows.append(row)
                if len(batch) < fetch_limit:
                    break
                cursor = (int(batch[-1]["startNs"]), int(batch[-1]["_rowid"]))
    return task_rows
