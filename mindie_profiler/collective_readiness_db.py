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
MAX_SQLITE_LOCK_BUDGET_S = 5.0
SQLITE_CLEANUP_GRACE_S = 0.1
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


def reserve_sqlite_lock_budget(deadline: float, db_label: str, timeout_s: float) -> int:
    check_deadline(deadline, db_label, timeout_s)
    remaining_s = deadline - time.monotonic()
    usable_s = remaining_s - SQLITE_CLEANUP_GRACE_S
    if usable_s < MIN_SQLITE_LOCK_BUDGET_S:
        raise ProfilerQueryError(
            f"{db_label}: remaining deadline ({remaining_s:.3f}s) is below minimum "
            f"SQLite lock budget ({MIN_SQLITE_LOCK_BUDGET_S:.1f}s + "
            f"{SQLITE_CLEANUP_GRACE_S:.1f}s cleanup); readiness budget exceeded ({timeout_s:.1f}s)"
        )
    return min(
        int(MAX_SQLITE_LOCK_BUDGET_S * 1000),
        max(int(MIN_SQLITE_LOCK_BUDGET_S * 1000), int(usable_s * 1000)),
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
    busy_ms = reserve_sqlite_lock_budget(deadline, db_label, timeout_s)
    try:
        db.execute(f"PRAGMA busy_timeout = {busy_ms}")
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
    has_op_id = "opId" in cols
    if has_op_id:
        extra += ", opId"
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
            if has_op_id and row["opId"] is not None:
                record["_op_id"] = str(row["opId"])
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
    child_maps: list[dict[str, dict[str, Any]]] = []
    for table in (
        "COMPUTE_TASK_INFO",
        "COMMUNICATION_TASK_INFO",
        "COMMUNICATION_SCHEDULE_TASK_INFO",
    ):
        cols = column_names(db, db_label, tables, table, deadline=deadline, timeout_s=timeout_s)
        child_maps.append(
            _read_child_table(
                db,
                db_label,
                table,
                cols,
                unique_ids,
                ambiguous_globals,
                limitations,
                string_ids,
                deadline=deadline,
                timeout_s=timeout_s,
            )
        )
    compute, comm, schedule = child_maps
    for gid in list(ambiguous_globals):
        compute.pop(gid, None)
        comm.pop(gid, None)
        schedule.pop(gid, None)
    return compute, comm, schedule, string_ids


class TaskGroupIndex:
    """Segment max-tree index for guaranteed O((1 + K) log N) overlap lookup."""

    __slots__ = ("tasks", "starts", "tree_size", "tree")

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
        for idx, row in enumerate(rows):
            row_start, row_end = int(row["startNs"]), int(row["endNs"])
            tree[size + idx] = row_end if row_end > row_start else (row_end + 1)
        for node in range(size - 1, 0, -1):
            if not tree:
                break
            left, right_val = tree[node << 1], tree[(node << 1) | 1]
            tree[node] = left if left >= right_val else right_val
        self.tree = tree

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


class StreamOrderIndex:
    """Device-and-stream ordered TASK index independent of host connectionId."""

    __slots__ = ("by_stream",)

    def __init__(
        self,
        rows: Sequence[sqlite3.Row],
        *,
        deadline: float | None = None,
        db_label: str = "profile.db",
        timeout_s: float = 20.0,
    ) -> None:
        buckets: dict[tuple[str, str], list[sqlite3.Row]] = {}
        for idx, row in enumerate(rows):
            if deadline is not None and (idx & 255) == 0:
                check_deadline(deadline, db_label, timeout_s)
            if (
                row["deviceId"] is None
                or row["streamId"] is None
                or row["endNs"] is None
                or row["globalTaskId"] is None
            ):
                continue
            buckets.setdefault((str(row["deviceId"]), str(row["streamId"])), []).append(row)
        self.by_stream: dict[tuple[str, str], tuple[list[int], list[sqlite3.Row]]] = {}
        for key, bucket in buckets.items():
            if deadline is not None:
                check_deadline(deadline, db_label, timeout_s)
            bucket.sort(key=lambda r: (int(r["endNs"]), int(r["globalTaskId"] or 0)))
            self.by_stream[key] = ([int(r["endNs"]) for r in bucket], bucket)

    def prior(
        self, device_id: str, stream_id: str, op_start_ns: int, excluded_globals: set[str]
    ) -> sqlite3.Row | None:
        entry = self.by_stream.get((device_id, stream_id))
        if entry is None:
            return None
        ends, bucket = entry
        idx = bisect_right(ends, op_start_ns) - 1
        while idx >= 0:
            if str(bucket[idx]["globalTaskId"]) not in excluded_globals:
                return bucket[idx]
            idx -= 1
        return None


def resolve_stream_predecessor(
    db: sqlite3.Connection,
    db_label: str,
    bound: sqlite3.Row,
    op_start: int,
    owned_tasks: Sequence[sqlite3.Row],
    stream_index: StreamOrderIndex,
    task_intervals: Sequence[tuple[int, int]],
    ambiguous_globals: set[str],
    checked_globals: set[str],
    limitations: set[str],
    *,
    can_query_task: bool,
    deadline: float,
    timeout_s: float,
) -> sqlite3.Row | None:
    """Resolve latest unambiguous same-(deviceId, streamId) task with endNs <= op_start."""
    if bound["deviceId"] is None or bound["streamId"] is None:
        return None
    local_excl = {str(bound["globalTaskId"])} | {
        str(t["globalTaskId"]) for t in owned_tasks if t["globalTaskId"] is not None
    }
    pred = stream_index.prior(
        str(bound["deviceId"]), str(bound["streamId"]), op_start, local_excl | ambiguous_globals
    )
    cov_lo = next((lo for lo, hi in task_intervals if lo <= op_start <= hi), op_start)
    if pred is not None and int(pred["endNs"]) > cov_lo:
        return pred
    if not (can_query_task and cov_lo > 0 and op_start > 0):
        return pred
    excl_ints = sorted(int(g) for g in local_excl if int_id(g) is not None)
    not_in = (
        f" AND globalTaskId NOT IN ({','.join('?' for _ in excl_ints)})"
        if excl_ints and len(excl_ints) <= 64
        else ""
    )
    args: list[Any] = [bound["deviceId"], bound["streamId"], op_start]
    if not_in:
        args.extend(excl_ints)
    args.append(32)
    candidates = fetch_rows(
        db,
        db_label,
        "SELECT startNs,endNs,connectionId,deviceId,globalTaskId,streamId,taskId,taskType "
        "FROM TASK WHERE deviceId=? AND streamId=? AND endNs<=? "
        f"AND globalTaskId IS NOT NULL{not_in} ORDER BY endNs DESC, globalTaskId DESC LIMIT ?",
        args,
        32,
        deadline=deadline,
        timeout_s=timeout_s,
    )
    unchecked = [r["globalTaskId"] for r in candidates if str(r["globalTaskId"]) not in checked_globals]
    if unchecked:
        new_ambig = find_ambiguous_task_globals(
            db, db_label, unchecked, deadline=deadline, timeout_s=timeout_s
        )
        checked_globals.update(str(x) for x in unchecked)
        if new_ambig:
            ambiguous_globals.update(new_ambig)
            limitations.add("ambiguous_global_task_id")
    for cand in candidates:
        gid = str(cand["globalTaskId"])
        if gid not in local_excl and gid not in ambiguous_globals:
            return cand
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
            params = [bound for lo, hi in win_chunk for bound in (lo, hi)]
            probe = fetch_rows(
                db, db_label, f"SELECT 1 FROM COMMUNICATION_OP WHERE ({where}) LIMIT 1",
                params, 1, deadline=deadline, timeout_s=timeout_s,
            )
            if probe:
                limitations.add("call_row_budget_reached")
                break
        return []
    for win_chunk in chunks(intervals, _WINDOW_CHUNK):
        where = " OR ".join("(endNs>? AND startNs<?)" for _ in win_chunk)
        win_params = [bound for lo, hi in win_chunk for bound in (lo, hi)]
        cursor: tuple[int, int] | None = None
        while True:
            fetch_limit = max(1, (max_calls - len(calls)) + 1)
            after = "" if cursor is None else " AND (startNs>? OR (startNs=? AND rowid>?))"
            params = (
                [*win_params, fetch_limit]
                if cursor is None
                else [*win_params, cursor[0], cursor[0], cursor[1], fetch_limit]
            )
            sql = (
                f"SELECT {select_cols} FROM COMMUNICATION_OP WHERE ({where}){after} "
                "ORDER BY startNs ASC, rowid ASC LIMIT ?"
            )
            batch = fetch_rows(
                db, db_label, sql, params, fetch_limit, deadline=deadline, timeout_s=timeout_s
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
            base_params = [*dev_chunk, *(b for lo, hi in win_chunk for b in (lo, hi))]
            cursor: tuple[int, int] | None = None
            while True:
                fetch_limit = max(1, (MAX_TASKS - len(task_rows)) + 1)
                after = "" if cursor is None else " AND (startNs>? OR (startNs=? AND rowid>?))"
                params = (
                    [*base_params, fetch_limit]
                    if cursor is None
                    else [*base_params, cursor[0], cursor[0], cursor[1], fetch_limit]
                )
                sql = (
                    "SELECT rowid AS _rowid,startNs,endNs,connectionId,deviceId,globalTaskId,"
                    f"streamId,taskId,taskType FROM TASK WHERE deviceId IN ({dev_marks}) "
                    f"AND ({where_win}){after} ORDER BY startNs ASC, rowid ASC LIMIT ?"
                )
                batch = fetch_rows(
                    db, db_label, sql, params, fetch_limit, deadline=deadline, timeout_s=timeout_s
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


def index_call_ownership(
    calls: Sequence[sqlite3.Row],
    *,
    has_op_id_col: bool,
    task_by_global: dict[str, sqlite3.Row],
    compute_raw: dict[str, dict[str, Any]],
    comm_raw: dict[str, dict[str, Any]],
    sched_raw: dict[str, dict[str, Any]],
    ambiguous_globals: set[str],
    limitations: set[str],
    concurrency_calls: Sequence[sqlite3.Row] | None = None,
    deadline: float | None = None,
    timeout_s: float = 20.0,
    db_label: str = "profile.db",
) -> tuple[set[str], dict[tuple[str, str], list[sqlite3.Row]], set[str]]:
    """Resolve child opId ownership and detect concurrent same-connection calls in O(N log N)."""
    task_op_owner: dict[str, str] = {}
    conflicted_op_globals: set[str] = set()
    if has_op_id_col:
        for raw_map in (compute_raw, comm_raw, sched_raw):
            for idx, (gid, raw_child) in enumerate(list(raw_map.items())):
                if deadline is not None and (idx & 255) == 0:
                    check_deadline(deadline, db_label, timeout_s)
                if gid in ambiguous_globals or (child_op := raw_child.get("_op_id")) is None:
                    continue
                prev_op = task_op_owner.get(gid)
                if prev_op is not None and prev_op != child_op:
                    conflicted_op_globals.add(gid)
                    ambiguous_globals.add(gid)
                    limitations.add("ambiguous_global_task_id")
                    task_op_owner.pop(gid, None)
                    compute_raw.pop(gid, None)
                    comm_raw.pop(gid, None)
                    sched_raw.pop(gid, None)
                    task_by_global.pop(gid, None)
                else:
                    task_op_owner[gid] = child_op
    tasks_by_op_id: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for idx, (gid, owner_op) in enumerate(task_op_owner.items()):
        if deadline is not None and (idx & 255) == 0:
            check_deadline(deadline, db_label, timeout_s)
        if (owned := task_by_global.get(gid)) is not None and owned["deviceId"] is not None:
            tasks_by_op_id.setdefault((owner_op, str(owned["deviceId"])), []).append(owned)
    for owned_list in tasks_by_op_id.values():
        if deadline is not None:
            check_deadline(deadline, db_label, timeout_s)
        owned_list.sort(key=lambda r: (int(r["startNs"]), int(r["endNs"]), int(r["globalTaskId"])))
    calls_by_conn: dict[tuple[str, str], list[tuple[int, int, str]]] = {}
    source_calls = concurrency_calls if concurrency_calls is not None else calls
    for idx, item in enumerate(source_calls):
        if deadline is not None and (idx & 255) == 0:
            check_deadline(deadline, db_label, timeout_s)
        if (
            item["connectionId"] is None
            or item["startNs"] is None
            or item["endNs"] is None
            or int(item["endNs"]) <= int(item["startNs"])
        ):
            continue
        calls_by_conn.setdefault((str(item["connectionId"]), str(item["deviceId"])), []).append(
            (int(item["startNs"]), int(item["endNs"]), str(item["opId"]))
        )
    shared_conn_ops: set[str] = set()
    for spans in calls_by_conn.values():
        if len(spans) < 2:
            continue
        if deadline is not None:
            check_deadline(deadline, db_label, timeout_s)
        spans.sort()
        # Sorted by startNs: span i overlaps an earlier span iff s_ns < max_{r<i} e_r;
        # when s_ns >= max_end, e_ns > s_ns >= max_end updates max_oid for step i + 1.
        max_end = -1
        max_oid = ""
        for idx, (s_ns, e_ns, oid) in enumerate(spans):
            if deadline is not None and (idx & 255) == 0:
                check_deadline(deadline, db_label, timeout_s)
            if s_ns < max_end:
                shared_conn_ops.add(oid)
                shared_conn_ops.add(max_oid)
            if e_ns > max_end:
                max_end = e_ns
                max_oid = oid
    return set(task_op_owner) | conflicted_op_globals, tasks_by_op_id, shared_conn_ops
