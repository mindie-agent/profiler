"""Read-only Ascend profiler SQLite schema probing and bounded window streaming.

[Role]
  Stream bounded ``COMPUTE_TASK_INFO``, ``TASK_PMU_INFO``, ``COMMUNICATION_OP``,
  and ``COMMUNICATION_SCHEDULE_TASK_INFO`` rows for explicit caller windows.

[Invariants]
  * Connections open exclusively via ``?mode=ro`` + ``PRAGMA query_only = ON``.
  * Every SQL query enforces an explicit ``LIMIT`` and ``set_progress_handler``
    wall-clock deadline; budget overflows raise ``ProfilerQueryError``.
  * ``source_id``, ``capture_id``, ``table_kind``, ``clock``, and ``field_presence``
    are attached directly at ``Event`` construction without post-hoc mutation.

[Timeouts & Locks]
  Read-only SQLite connections with ``busy_timeout`` + progress-handler deadline.

[Side-Effect Policy]
  Read-only SQLite queries only; never creates or modifies database files.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Iterator, Mapping

from .events import Event, ProfilerQueryError, ProfilerSchemaError, QueryStats, Window
from .sources_db_comm import read_communication_events
from .sources_db_schema import (
    MAPPING_PATH,
    DbSchema,
    _IDENTIFIER,
    _PMU_BUDGET_FACTOR,
    _PMU_BUDGET_MAX,
    _PMU_BUDGET_MIN,
    _TASK_NS_CLOCK,
    _as_int,
    _as_optional_int,
    _as_text,
    _capture_id_for_file,
    _columns,
    _connect,
    _first_present,
    _missing_columns,
    _resolve_strings,
    _source_id_for_file,
    _table_names,
    _task_clock,
    _text,
    load_mapping,
    probe_db,
    sha256_file,
)


class _StringResolver(Mapping[int, str]):
    """Resolve only referenced ``STRING_IDS`` rows through the integer PK."""

    def __init__(self, con: sqlite3.Connection, table: str,
                 cache: dict[int, str]) -> None:
        self._con = con
        self._table = table
        self._cache = cache

    def __getitem__(self, key: int) -> str:
        key = int(key)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        row = self._con.execute(
            f"SELECT value FROM {self._table} WHERE id = ? LIMIT 1", (key,)
        ).fetchone()
        if row is None:
            raise KeyError(key)
        value = "" if row[0] is None else str(row[0])
        self._cache[key] = value
        return value

    def __iter__(self) -> Iterator[int]:
        return iter(())

    def __len__(self) -> int:
        return len(self._cache)


class DbSource:
    """A probed read-only DB.  One instance is reused across windows."""

    def __init__(self, schema: DbSchema, *, mapping: Mapping[str, Any] | None = None) -> None:
        self.schema = schema
        self.mapping = dict(mapping or load_mapping())
        self._source_id = _source_id_for_file(self.schema.path, self.schema.size_bytes)
        self._capture_id = _capture_id_for_file(self.schema.path)
        self._names = self.mapping["tables"]
        self._strings: dict[int, str] = {}
        self._task_occurrences: dict[int | str, int] | None = None
        self._occurrence_scan_ms = 0.0
        self._duplicate_counts_only = False
        self._integer_ids: bool | None = None
        self._pmu_indexed: bool | None = None
        self._pmu_cache: dict[int, list[tuple[Any, Any]]] | None = None

    def _connection(self, timeout_s: float) -> sqlite3.Connection:
        return _connect(Path(self.schema.path), timeout_s)

    def _load_strings(self, con: sqlite3.Connection) -> Mapping[int, str]:
        return _StringResolver(con, self._names["strings"], self._strings)

    def _detect_integer_ids(self, con: sqlite3.Connection) -> bool:
        if self._integer_ids is None:
            row = con.execute(
                f"SELECT 1 FROM {self._names['task']} "
                "WHERE globalTaskId IS NOT NULL "
                "AND typeof(globalTaskId) <> 'integer' LIMIT 1"
            ).fetchone()
            self._integer_ids = row is None
        return self._integer_ids

    def _has_index_on_global_task_id(self, con: sqlite3.Connection) -> bool:
        if self._pmu_indexed is None:
            table = self._names["pmu"]
            self._pmu_indexed = False
            if table in self.schema.tables:
                for index in con.execute(f"PRAGMA index_list({table})"):
                    for info in con.execute(f"PRAGMA index_info({index[1]})"):
                        if str(info[2]) == "globalTaskId":
                            self._pmu_indexed = True
                            break
                    if self._pmu_indexed:
                        break
        return self._pmu_indexed

    def _task_occurrence_counts(self, con: sqlite3.Connection) -> dict[int | str, int]:
        """Full-capture TASK occurrence count per globalTaskId (cached across windows)."""
        if self._task_occurrences is None:
            started = time.perf_counter()
            counts: dict[int | str, int] = {}
            integer_only = self._detect_integer_ids(con)
            sql = (
                f"SELECT globalTaskId, COUNT(*) FROM {self._names['task']} "
                "WHERE globalTaskId IS NOT NULL GROUP BY globalTaskId"
            )
            if integer_only:
                sql += " HAVING COUNT(*) > 1"
            for raw_gid, raw_cnt in con.execute(sql):
                key: int | str = (
                    igid if (igid := _as_optional_int(raw_gid)) is not None else str(raw_gid)
                )
                counts[key] = counts.get(key, 0) + int(raw_cnt)
            self._task_occurrences = counts
            self._duplicate_counts_only = integer_only
            self._occurrence_scan_ms = round((time.perf_counter() - started) * 1000.0, 6)
        return self._task_occurrences

    def _prime_pmu_cache(self, con: sqlite3.Connection, windows: list[Window],
                         *, max_rows: int) -> None:
        """One bounded TASK_PMU_INFO range scan for all windows (unindexed integer IDs)."""
        if self._pmu_cache is not None:
            return
        self._pmu_cache = {}
        table = self._names["pmu"]
        if table not in self.schema.tables or not windows:
            return
        if not self._detect_integer_ids(con) or self._has_index_on_global_task_id(con):
            return
        start_ns = min(window.start_ns for window in windows)
        end_ns = max(window.end_ns for window in windows)
        wanted = {
            int(row[0]) for row in con.execute(
                f"SELECT DISTINCT globalTaskId FROM {self._names['task']} "
                "WHERE endNs > ? AND startNs < ? AND globalTaskId IS NOT NULL",
                (start_ns, end_ns),
            )
            if _as_optional_int(row[0]) is not None
        }
        if not wanted:
            return
        budget = self._pmu_budget(max_rows) * max(1, len(windows))
        read_rows = 0
        for global_id, name_id, value in con.execute(
            f"SELECT globalTaskId, name, value FROM {table} "
            "WHERE globalTaskId >= ? AND globalTaskId <= ?",
            (min(wanted), max(wanted)),
        ):
            read_rows += 1
            if read_rows > budget:
                raise ProfilerQueryError(
                    f"{Path(self.schema.path).name}: multi-window PMU scan exceeded "
                    f"{budget} rows for {len(windows)} windows")
            gid = _as_optional_int(global_id)
            if gid in wanted:
                self._pmu_cache.setdefault(gid, []).append((name_id, value))

    def capture_range_ns(self, *, timeout_s: float = 20.0) -> tuple[int, int] | None:
        con = self._connection(timeout_s)
        try:
            lows: list[int] = []
            highs: list[int] = []
            for table in (self._names["task"], self._names["comm"]):
                if table not in self.schema.tables:
                    continue
                row = con.execute(f"SELECT MIN(startNs), MAX(endNs) FROM {table}").fetchone()
                if row and row[0] is not None and row[1] is not None:
                    lows.append(int(row[0]))
                    highs.append(int(row[1]))
            if not lows or not highs:
                return None
            return min(lows), max(highs)
        except sqlite3.Error as exc:
            raise ProfilerQueryError(f"cannot read capture range from {self.schema.path}: {exc}") from exc
        finally:
            con.close()

    def _pmu_budget(self, max_rows: int) -> int:
        return min(_PMU_BUDGET_MAX, max(_PMU_BUDGET_MIN, int(max_rows) * _PMU_BUDGET_FACTOR))

    def _load_pmu_rows(
        self,
        con: sqlite3.Connection,
        global_task_ids: list[int],
        strings: Mapping[int, str],
        unresolved: list[int],
        *,
        budget: int,
    ) -> tuple[dict[int, list[tuple[str, float | None]]], int, int]:
        table = self._names["pmu"]
        rows_by_id: dict[int, list[tuple[str, float | None]]] = {}
        read_rows = 0
        bad_values = 0
        if not global_task_ids or table not in self.schema.tables:
            return rows_by_id, read_rows, bad_values
        wanted = sorted({int(item) for item in global_task_ids})

        def consume(cursor: Iterator[tuple[Any, Any, Any]]) -> None:
            nonlocal read_rows, bad_values
            for global_id, name_id, value in cursor:
                read_rows += 1
                if read_rows > budget:
                    raise ProfilerQueryError(
                        f"{Path(self.schema.path).name}: PMU row budget {budget} exceeded for "
                        f"{len(wanted)} selected globalTaskIds"
                    )
                metric = _text(strings, name_id, unresolved)
                numeric: float | None = None
                if value is not None:
                    try:
                        numeric = float(value)
                    except (TypeError, ValueError):
                        bad_values += 1
                rows_by_id.setdefault(int(global_id), []).append((metric, numeric))

        if self._pmu_cache is not None:
            for global_id in wanted:
                for name_id, value in self._pmu_cache.get(global_id, ()):
                    consume(iter(((global_id, name_id, value),)))
            return rows_by_id, read_rows, bad_values
        unindexed = not self._has_index_on_global_task_id(con)
        if self._detect_integer_ids(con) and unindexed:
            low, high = wanted[0], wanted[-1]
            if len(wanted) <= 400:
                marks = ",".join("?" for _ in wanted)
                consume(con.execute(
                    f"SELECT globalTaskId, name, value FROM {table} "
                    f"WHERE globalTaskId BETWEEN ? AND ? AND globalTaskId IN ({marks})",
                    (low, high, *wanted)))
            else:
                consume(con.execute(
                    f"SELECT globalTaskId, name, value FROM {table} "
                    "WHERE globalTaskId >= ? AND globalTaskId <= ?", (low, high)))
            return rows_by_id, read_rows, bad_values
        for offset in range(0, len(wanted), 500):
            chunk = wanted[offset : offset + 500]
            placeholders = ",".join("?" for _ in chunk)
            sql = (
                f"SELECT globalTaskId, name, value FROM {table} "
                f"WHERE globalTaskId IN ({placeholders})"
            )
            consume(con.execute(sql, chunk))
        return rows_by_id, read_rows, bad_values

    @staticmethod
    def _wait_binding(
        raw_wait: Any,
        occurrences: int | None,
        wait_column: str | None,
    ) -> tuple[int | None, str]:
        if wait_column is None:
            return None, "not_available"
        if raw_wait is None:
            return None, "absent"
        try:
            wait_ns = int(raw_wait)
        except (TypeError, ValueError):
            return None, "invalid_value"
        if wait_ns < 0:
            return None, "invalid_value"
        if occurrences is None:
            return None, "cardinality_unknown"
        if occurrences > 1:
            return None, "ambiguous_task_occurrence"
        return wait_ns, "bound"

    @staticmethod
    def _pmu_group_summary(
        global_id: int,
        rows: list[tuple[str, float | None]],
        occurrences: int,
        status: str,
    ) -> dict[str, Any]:
        per_metric: dict[str, dict[str, Any]] = {}
        for metric, value in rows:
            entry = per_metric.setdefault(
                metric,
                {"rows": 0, "values": 0, "distinct_values": 0, "_values": []},
            )
            entry["rows"] += 1
            if value is not None:
                entry["values"] += 1
                entry["_values"].append(float(value))
        for entry in per_metric.values():
            values = entry.pop("_values")
            entry["distinct_values"] = len(set(values))
            entry["all_zero"] = bool(values) and all(value == 0.0 for value in values)
            entry["min"] = min(values) if values else None
            entry["max"] = max(values) if values else None
        return {
            "table": "TASK_PMU_INFO",
            "global_task_id": global_id,
            "task_occurrences_full_capture": occurrences,
            "status": status,
            "raw_rows": len(rows),
            "metric_count": len(per_metric),
            "per_metric": per_metric,
            "binding": "group_scoped_only",
        }

    def _bind_pmu(
        self,
        event: Event,
        rows: list[tuple[str, float | None]],
        occurrences: int | None,
        group_cache: dict[tuple[int, str], dict[str, Any]],
    ) -> None:
        global_id = event.locator.get("task_global_id")
        if not self.schema.pmu_table_present:
            event.pmu_status = "not_available"
            return
        if not isinstance(global_id, int):
            event.pmu_status = "cardinality_unknown"
            return
        if not rows:
            event.pmu_status = "absent"
            event.pmu_provenance = {
                "table": "TASK_PMU_INFO",
                "global_task_id": global_id,
                "task_occurrences_full_capture": occurrences,
                "status": "absent",
                "raw_rows": 0,
            }
            return
        per_metric: dict[str, int] = {}
        for metric, _value in rows:
            per_metric[metric] = per_metric.get(metric, 0) + 1
        if occurrences is None:
            status = "cardinality_unknown"
        elif occurrences > 1:
            status = "ambiguous_task_occurrence"
        elif any(count != 1 for count in per_metric.values()):
            status = "duplicate_metric_rows"
        elif any(value is None for _metric, value in rows):
            status = "incomplete_metric_value"
        else:
            status = "bound"
        event.pmu_status = status
        if status == "bound":
            meta = self.mapping["pmu_metrics"]
            canonical: dict[str, float] = {}
            for metric, value in rows:
                spec = meta.get(metric, {})
                key = str(spec.get("db_metric", metric))
                factor = float(spec.get("db_scale", 1.0))
                canonical[key] = float(value) * factor
            event.pmu = tuple(sorted(canonical.items()))
            event.pmu_provenance = {
                "table": "TASK_PMU_INFO",
                "global_task_id": global_id,
                "task_occurrences_full_capture": occurrences,
                "status": "bound",
                "raw_rows": len(rows),
                "metric_count": len(per_metric),
                "binding": "unique_task_occurrence",
            }
            return
        cache_key = (global_id, status)
        summary = group_cache.get(cache_key)
        if summary is None:
            summary = self._pmu_group_summary(global_id, rows, occurrences or 0, status)
            group_cache[cache_key] = summary
        event.pmu_provenance = summary

    def iter_windows(
        self,
        windows: list[Window] | tuple[Window, ...],
        *,
        max_rows: int = 1_000_000,
        timeout_s: float = 20.0,
    ) -> list[tuple[list[Event], QueryStats]]:
        """Read several windows with one shared TASK_PMU_INFO range scan."""
        selected = list(windows)
        if not selected:
            return []
        scaled = max(float(timeout_s), min(
            120.0, float(timeout_s) * max(1.0, len(selected) * 0.5)))
        con = self._connection(scaled)
        try:
            deadline = time.perf_counter() + scaled
            con.set_progress_handler(
                lambda: 1 if time.perf_counter() > deadline else 0, 20_000)
            self._task_occurrence_counts(con)
            self._prime_pmu_cache(con, selected, max_rows=max_rows)
        finally:
            con.set_progress_handler(None, 0)
            con.close()
        return [
            self.iter_window(window, max_rows=max_rows, timeout_s=scaled)
            for window in selected
        ]

    def iter_window(
        self,
        window: Window,
        *,
        max_rows: int = 1_000_000,
        timeout_s: float = 20.0,
    ) -> tuple[list[Event], QueryStats]:
        started = time.perf_counter()
        con = self._connection(timeout_s)
        deadline = started + max(0.1, timeout_s)
        con.set_progress_handler(lambda: 1 if time.perf_counter() > deadline else 0, 20_000)
        stats = QueryStats(rank_id="", window_label=window.label or str(window.step), budget=max_rows)
        events: list[Event] = []
        unresolved: list[int] = []
        try:
            strings = self._load_strings(con)
            occurrences = self._task_occurrence_counts(con)
            stats.measurement_scan_ms += self._occurrence_scan_ms
            names = self._names
            compute = names["compute"]
            block = f"c.{self.schema.block_column}" if self.schema.block_column else "NULL"
            mix = f"c.{self.schema.mix_block_column}" if self.schema.mix_block_column else "NULL"
            shape_exprs = []
            for column in ("inputShapes", "inputDataTypes", "inputFormats"):
                expression = f"c.{column}" if column in self.schema.shape_columns else "NULL"
                shape_exprs.append(f"{expression} AS {column}")
            output_exprs = [
                (f"c.{column}" if column in self.schema.shape_columns else "NULL") + f" AS {column}"
                for column in ("outputShapes", "outputDataTypes", "outputFormats", "opState")
            ]
            wait_expr = f"c.{self.schema.wait_column}" if self.schema.wait_column else "NULL"
            task_columns = _columns(con, names["task"])
            connection_expr = "t.connectionId" if "connectionId" in task_columns else "NULL"
            sql = (
                "SELECT t.globalTaskId, t.startNs, t.endNs, t.deviceId, t.streamId, t.taskId, "
                "t.modelId, t.contextId, c.name, c.opType, c.taskType, "
                + ", ".join(shape_exprs)
                + ", " + wait_expr + " AS wait_ns, " + block + " AS block_dim, " + mix + " AS mix_block_dim, "
                + ", ".join(output_exprs)
                + ", " + connection_expr + " AS connectionId "
                f"FROM {names['task']} t JOIN {compute} c ON c.globalTaskId = t.globalTaskId "
                "WHERE t.endNs > ? AND t.startNs < ? ORDER BY t.startNs, t.globalTaskId LIMIT ?"
            )
            rows = con.execute(sql, (window.start_ns, window.end_ns, max_rows + 1)).fetchall()
            stats.rows_read += len(rows)
            if len(rows) > max_rows:
                raise ProfilerQueryError(
                    f"{Path(self.schema.path).name}: window {window.label or window.step} "
                    f"exceeded row budget {max_rows}; narrow the window or raise --max-rows"
                )
            clock = _task_clock()
            compute_events: list[Event] = []
            pmu_ids: set[int] = set()
            for row in rows:
                if row[1] is None or row[2] is None or _as_int(row[2]) <= _as_int(row[1]):
                    stats.bad_rows += 1
                    continue
                global_id = _as_optional_int(row[0])
                occurrence_count = (
                    None if global_id is None
                    else occurrences.get(global_id, 1)
                    if self._duplicate_counts_only
                    else occurrences.get(global_id)
                )
                wait_ns, wait_status = self._wait_binding(row[14], occurrence_count, self.schema.wait_column)
                if wait_status == "bound":
                    stats.wait_bound_rows += 1
                elif wait_status == "ambiguous_task_occurrence":
                    stats.wait_ambiguous_rows += 1
                name = _text(strings, row[8], unresolved)
                op_type = _text(strings, row[9], unresolved)
                core = _text(strings, row[10], unresolved)
                event = Event(
                    rank_id="",
                    rank_index=None,
                    name=name,
                    op_type=op_type,
                    task_type=core,
                    core=core,
                    stream_id=_as_text(row[4]),
                    task_id=_as_text(row[5]),
                    device_id=_as_text(row[3]),
                    start_ns=_as_int(row[1]),
                    end_ns=_as_int(row[2]),
                    source_kind=self.schema.source_kind,
                    table=compute,
                    clock=clock,
                    clock_start_tick=_as_int(row[1]),
                    clock_end_tick=_as_int(row[2]),
                    source_id=self._source_id,
                    capture_id=self._capture_id,
                    table_kind=compute,
                    field_presence={
                        "clock": True,
                        "abi": bool(_text(strings, row[11], unresolved) or _text(strings, row[17], unresolved)),
                        "step": False,
                        "state": bool(_text(strings, row[20], unresolved)),
                    },
                    input_shapes=_text(strings, row[11], unresolved),
                    input_dtypes=_text(strings, row[12], unresolved),
                    input_formats=_text(strings, row[13], unresolved),
                    block_dim=_as_optional_int(row[15]),
                    mix_block_dim=_as_optional_int(row[16]),
                    output_shapes=_text(strings, row[17], unresolved),
                    output_dtypes=_text(strings, row[18], unresolved),
                    output_formats=_text(strings, row[19], unresolved),
                    op_state=_text(strings, row[20], unresolved),
                    wait_ns=wait_ns,
                    wait_status=wait_status,
                    wait_source=(f"COMPUTE_TASK_INFO.{self.schema.wait_column}" if self.schema.wait_column else None),
                    wait_provenance={
                        "table": compute,
                        "column": self.schema.wait_column,
                        "global_task_id": global_id,
                        "task_occurrences_full_capture": occurrence_count,
                        "raw_wait_ns": None if row[14] is None else _as_int(row[14]),
                        "status": wait_status,
                    },
                    pmu_kind="aicore",
                    pmu_source="TASK_PMU_INFO",
                    task_occurrences_full_capture=occurrence_count,
                    locator={
                        "source": self.schema.path,
                        "table": compute,
                        "task_global_id": global_id,
                        "task_id": _as_text(row[5]),
                        "stream_id": _as_text(row[4]),
                        "device_id": _as_text(row[3]),
                        "task_occurrences_full_capture": occurrence_count,
                        "connection_id": None if row[21] is None else _as_text(row[21]),
                    },
                )
                compute_events.append(event)
                events.append(event)
                if global_id is not None:
                    pmu_ids.add(global_id)
            stats.compute_rows = len(compute_events)
            stats.ambiguous_groups = len(
                {
                    event.locator.get("task_global_id")
                    for event in compute_events
                    if (event.task_occurrences_full_capture or 0) > 1
                }
            )
            if self.schema.pmu_table_present and pmu_ids:
                pmu_started = time.perf_counter()
                pmu_rows, pmu_read, bad_pmu = self._load_pmu_rows(
                    con,
                    sorted(pmu_ids),
                    strings,
                    unresolved,
                    budget=self._pmu_budget(max_rows),
                )
                stats.measurement_scan_ms += round((time.perf_counter() - pmu_started) * 1000.0, 6)
                stats.pmu_rows = pmu_read
                stats.pmu_bad_values = bad_pmu
                group_cache: dict[tuple[int, str], dict[str, Any]] = {}
                for event in compute_events:
                    global_id = event.locator.get("task_global_id")
                    rows_for_id = pmu_rows.get(global_id, []) if isinstance(global_id, int) else []
                    self._bind_pmu(
                        event,
                        rows_for_id,
                        event.task_occurrences_full_capture,
                        group_cache,
                    )
                    if event.pmu_status == "bound":
                        stats.pmu_bound_rows += 1
                    elif event.pmu_status in {
                        "ambiguous_task_occurrence",
                        "duplicate_metric_rows",
                        "incomplete_metric_value",
                        "cardinality_unknown",
                    }:
                        stats.pmu_ambiguous_rows += 1

            contested_comm_tasks: set[tuple[str, str]] = set()
            comm = names["comm"]
            if comm in self.schema.tables:
                events.extend(
                    read_communication_events(
                        con,
                        schema_path=self.schema.path,
                        source_kind=self.schema.source_kind,
                        tables=self.schema.tables,
                        comm_table=comm,
                        task_table=names["task"],
                        task_columns=task_columns,
                        columns_fn=_columns,
                        text_fn=_text,
                        strings=strings,
                        unresolved=unresolved,
                        window=window,
                        max_rows=max_rows,
                        stats=stats,
                        deadline=deadline,
                        timeout_s=timeout_s,
                        contested_tasks=contested_comm_tasks,
                        task_occurrences=occurrences,
                        clock=clock,
                        source_id=self._source_id,
                        capture_id=self._capture_id,
                    )
                )

            sched = names["comm_sched"]
            if sched in self.schema.tables:
                sched_sql = (
                    "SELECT s.globalTaskId, s.name, s.opType, s.taskType, t.startNs, t.endNs, "
                    "t.deviceId, t.streamId, t.taskId "
                    f"FROM {sched} s JOIN {names['task']} t ON t.globalTaskId = s.globalTaskId "
                    "WHERE t.endNs > ? AND t.startNs < ? ORDER BY t.startNs, s.globalTaskId LIMIT ?"
                )
                sched_rows = con.execute(sched_sql, (window.start_ns, window.end_ns, max_rows + 1)).fetchall()
                stats.rows_read += len(sched_rows)
                if len(sched_rows) > max_rows:
                    raise ProfilerQueryError(
                        f"{Path(self.schema.path).name}: comm-schedule window {window.label or window.step} "
                        f"exceeded row budget {max_rows}"
                    )
                for row in sched_rows:
                    if row[4] is None or row[5] is None or _as_int(row[5]) <= _as_int(row[4]):
                        stats.bad_rows += 1
                        continue
                    global_id = _as_optional_int(row[0])
                    events.append(
                        Event(
                            rank_id="",
                            rank_index=None,
                            name=_text(strings, row[1], unresolved),
                            op_type=_text(strings, row[2], unresolved),
                            task_type=_text(strings, row[3], unresolved),
                            core=_text(strings, row[3], unresolved),
                            stream_id=_as_text(row[7]),
                            task_id=_as_text(row[8]),
                            device_id=_as_text(row[6]),
                            start_ns=_as_int(row[4]),
                            end_ns=_as_int(row[5]),
                            source_kind=self.schema.source_kind,
                            table=sched,
                            clock=clock,
                            clock_start_tick=_as_int(row[4]),
                            clock_end_tick=_as_int(row[5]),
                            source_id=self._source_id,
                            capture_id=self._capture_id,
                            table_kind=sched,
                            field_presence={"clock": True, "abi": False, "step": False, "state": False},
                            wait_status="not_applicable",
                            pmu_status="not_applicable",
                            pmu_kind="not_applicable",
                            task_occurrences_full_capture=(occurrences.get(global_id) if global_id is not None else None),
                            locator={
                                "source": self.schema.path,
                                "table": sched,
                                "task_global_id": global_id,
                                "stream_id": _as_text(row[7]),
                            },
                        )
                    )
                stats.comm_sched_rows = len(sched_rows)
            if contested_comm_tasks:
                for ev in events:
                    gid = ev.locator.get("task_global_id")
                    if gid is not None and (ev.device_id, str(gid)) in contested_comm_tasks:
                        ev.locator["task_join_status"] = "unresolved_contested_comm_task"
        except sqlite3.OperationalError as exc:
            if "interrupted" in str(exc).lower():
                raise ProfilerQueryError(
                    f"{Path(self.schema.path).name}: query exceeded {timeout_s:.1f}s for "
                    f"window {window.label or window.step}"
                ) from exc
            raise ProfilerQueryError(f"{Path(self.schema.path).name}: query failed: {exc}") from exc
        except sqlite3.Error as exc:
            raise ProfilerQueryError(f"{Path(self.schema.path).name}: query failed: {exc}") from exc
        finally:
            con.set_progress_handler(None, 0)
            con.close()

        if len(events) > max_rows:
            raise ProfilerQueryError(
                f"{Path(self.schema.path).name}: window {window.label or window.step} combined "
                f"event budget {max_rows} exceeded"
            )
        events.sort(key=lambda item: (item.start_ns, item.end_ns, item.table, item.task_id))
        stats.rows_selected = len(events)
        stats.unresolved_string_ids = len(set(unresolved))
        stats.elapsed_ms = round((time.perf_counter() - started) * 1000.0, 6)
        return events, stats
