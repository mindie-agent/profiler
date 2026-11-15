"""Read-only Ascend profiler SQLite schema probing and bounded window streaming (sources_db_reader).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting read-only ascend profiler sqlite schema probing and bounded window streaming.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Mapping
from .events import (
    ClockDomain,
    Event,
    ProfilerQueryError,
    ProfilerSchemaError,
    QueryStats,
    Window,
)

from .sources_db_schema import (
    DbSchema, _PMU_BUDGET_FACTOR, _PMU_BUDGET_MAX, _PMU_BUDGET_MIN, _as_int,
    _as_optional_int, _as_text, _capture_id_for_file, _columns, _connect,
    _resolve_strings, _source_id_for_file, _task_clock, _text, load_mapping,
)

class DbSource:
    """A probed read-only DB.  One instance is reused across windows."""

    def __init__(self, schema: DbSchema, *, mapping: Mapping[str, Any] | None = None) -> None:
        self.schema = schema
        self.mapping = dict(mapping or load_mapping())
        self._source_id = _source_id_for_file(self.schema.path, self.schema.size_bytes)
        self._capture_id = _capture_id_for_file(self.schema.path)
        self._names = self.mapping["tables"]
        self._strings: dict[int, str] | None = None
        self._task_occurrences: dict[int, int] | None = None
        self._occurrence_scan_ms = 0.0

    def _connection(self, timeout_s: float) -> sqlite3.Connection:
        return _connect(Path(self.schema.path), timeout_s)

    def _load_strings(self, con: sqlite3.Connection) -> dict[int, str]:
        if self._strings is None:
            self._strings = _resolve_strings(con, self._names["strings"])
        return self._strings

    def _task_occurrence_counts(self, con: sqlite3.Connection) -> dict[int, int]:
        """Full-capture TASK occurrence count per globalTaskId.

        This is deliberately a full-capture query, not a window query: a
        globalTaskId repeated outside the selected window still makes the
        CTI waitNs/PMU group ambiguous for the selected occurrence.
        """

        if self._task_occurrences is None:
            started = time.perf_counter()
            self._task_occurrences = {
                int(row[0]): int(row[1])
                for row in con.execute(
                    f"SELECT globalTaskId, COUNT(*) FROM {self._names['task']} GROUP BY globalTaskId"
                )
            }
            self._occurrence_scan_ms = round((time.perf_counter() - started) * 1000.0, 6)
        return self._task_occurrences

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
        for offset in range(0, len(global_task_ids), 500):
            chunk = global_task_ids[offset : offset + 500]
            placeholders = ",".join("?" for _ in chunk)
            sql = (
                f"SELECT globalTaskId, name, value FROM {table} "
                f"WHERE globalTaskId IN ({placeholders})"
            )
            for global_id, name_id, value in con.execute(sql, chunk):
                read_rows += 1
                if read_rows > budget:
                    raise ProfilerQueryError(
                        f"{Path(self.schema.path).name}: PMU row budget {budget} exceeded for "
                        f"{len(global_task_ids)} selected globalTaskIds"
                    )
                metric = _text(strings, name_id, unresolved)
                numeric: float | None = None
                if value is not None:
                    try:
                        numeric = float(value)
                    except (TypeError, ValueError):
                        bad_values += 1
                rows_by_id.setdefault(int(global_id), []).append((metric, numeric))
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
            connection_expr = ("t.connectionId" if "connectionId" in task_columns
                               else "NULL")
            sql = (
                "SELECT t.globalTaskId, t.startNs, t.endNs, t.deviceId, t.streamId, t.taskId, "
                "t.modelId, t.contextId, c.name, c.opType, c.taskType, "
                + ", ".join(shape_exprs)
                + ", " + wait_expr + " AS wait_ns, " + block + " AS block_dim, " + mix + " AS mix_block_dim, "
                + ", ".join(output_exprs)
                + ", t.connectionId "
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
            compute_events: list[Event] = []
            pmu_ids: set[int] = set()
            for row in rows:
                if row[1] is None or row[2] is None or _as_int(row[2]) <= _as_int(row[1]):
                    stats.bad_rows += 1
                    continue
                start_ns = _as_int(row[1])
                end_ns = _as_int(row[2])
                clock = _task_clock()
                global_id = _as_optional_int(row[0])
                occurrence_count = occurrences.get(global_id) if global_id is not None else None
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
                    start_ns=start_ns,
                    end_ns=end_ns,
                    source_kind=self.schema.source_kind,
                    table=compute,
                    clock=clock,
                    clock_start_tick=start_ns,
                    clock_end_tick=end_ns,
                    source_id=self._source_id,
                    capture_id=self._capture_id,
                    table_kind=compute,
                    field_presence={
                        "clock": True,
                        "abi": bool(
                            _text(strings, row[11], unresolved)
                            or _text(strings, row[17], unresolved)
                        ),
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
                        "connection_id": _as_text(row[21]),
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

            comm = names["comm"]
            if comm in self.schema.tables:
                comm_columns = _columns(con, comm)
                optional = {name: (name if name in comm_columns else "NULL")
                            for name in ("connectionId", "algType", "dataType",
                                         "count", "groupName", "rankSize")}
                comm_sql = (
                    "SELECT rowid, opName, opType, startNs, endNs, deviceId, "
                    f"{optional['connectionId']}, {optional['algType']}, "
                    f"{optional['dataType']}, {optional['count']}, "
                    f"{optional['groupName']}, {optional['rankSize']} "
                    f"FROM {comm} WHERE endNs > ? AND startNs < ? ORDER BY startNs, rowid LIMIT ?"
                )
                comm_rows = con.execute(comm_sql, (window.start_ns, window.end_ns, max_rows + 1)).fetchall()
                stats.rows_read += len(comm_rows)
                if len(comm_rows) > max_rows:
                    raise ProfilerQueryError(
                        f"{Path(self.schema.path).name}: comm window {window.label or window.step} "
                        f"exceeded row budget {max_rows}"
                    )
                # COMMUNICATION_OP carries connectionId but not globalTaskId/
                # stream/task.  TASK carries both.  Join the real relational
                # key and require exactly one interval-matching TASK row.
                task_rows = con.execute(
                    f"SELECT connectionId, deviceId, globalTaskId, streamId, taskId, startNs, endNs "
                    f"FROM {names['task']} WHERE endNs > ? AND startNs < ?",
                    (window.start_ns, window.end_ns),
                ).fetchall()
                tasks_by_connection: dict[tuple[str, str], list[tuple]] = {}
                for task in task_rows:
                    key = (_as_text(task[0]), _as_text(task[1]))
                    tasks_by_connection.setdefault(key, []).append(task)
                for row in comm_rows:
                    if row[3] is None or row[4] is None or _as_int(row[4]) <= _as_int(row[3]):
                        stats.bad_rows += 1
                        continue
                    start_ns = _as_int(row[3])
                    end_ns = _as_int(row[4])
                    clock = _task_clock()
                    connection_id = _as_text(row[6])
                    device_id = _as_text(row[5])
                    candidates = tasks_by_connection.get((connection_id, device_id), ())
                    containing = [
                        task for task in candidates
                        if _as_int(task[5]) <= _as_int(row[3])
                        and _as_int(task[6]) >= _as_int(row[4])
                    ]
                    exact = [
                        task for task in containing
                        if _as_int(task[5]) == _as_int(row[3])
                        and _as_int(task[6]) == _as_int(row[4])
                    ]
                    bound_task = (exact or containing)[0] if len(exact or containing) == 1 else None
                    global_task_id = _as_text(bound_task[2]) if bound_task else None
                    stream_id = _as_text(bound_task[3]) if bound_task else ""
                    task_id = _as_text(bound_task[4]) if bound_task else ""
                    locator = {
                        "source": self.schema.path,
                        "table": comm,
                        "rowid": _as_optional_int(row[0]),
                        "device_id": device_id,
                        "connection_id": connection_id,
                        "global_task_id": global_task_id,
                        "stream_id": stream_id,
                        "task_id": task_id,
                        "algorithm": _text(strings, row[7], []),
                        "data_type": _as_optional_int(row[8]),
                        "count": _as_optional_int(row[9]),
                        "group_name": _text(strings, row[10], []),
                        "rank_size": _as_optional_int(row[11]),
                    }
                    if bound_task is None:
                        locator["task_join_status"] = "unresolved_no_unique_connection_task"
                    else:
                        locator["task_join_status"] = "connection_and_interval"
                    events.append(
                        Event(
                            rank_id="",
                            rank_index=None,
                            name=_text(strings, row[1], unresolved),
                            op_type=_text(strings, row[2], unresolved),
                            task_type="COMMUNICATION",
                            core="COMMUNICATION",
                            stream_id=stream_id,
                            task_id=task_id,
                            device_id=device_id,
                            start_ns=start_ns,
                            end_ns=end_ns,
                            source_kind=self.schema.source_kind,
                            table=comm,
                            clock=clock,
                            clock_start_tick=start_ns,
                            clock_end_tick=end_ns,
                            source_id=self._source_id,
                            capture_id=self._capture_id,
                            table_kind=comm,
                            field_presence={
                                "clock": True, "abi": False,
                                "step": False, "state": False,
                            },
                            wait_status="not_applicable",
                            pmu_status="not_applicable",
                            pmu_kind="not_applicable",
                            locator=locator,
                        )
                    )
                stats.comm_rows = len(comm_rows)

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
                    start_ns = _as_int(row[4])
                    end_ns = _as_int(row[5])
                    clock = _task_clock()
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
                            start_ns=start_ns,
                            end_ns=end_ns,
                            source_kind=self.schema.source_kind,
                            table=sched,
                            clock=clock,
                            clock_start_tick=start_ns,
                            clock_end_tick=end_ns,
                            source_id=self._source_id,
                            capture_id=self._capture_id,
                            table_kind=comm,
                            field_presence={
                                "clock": True, "abi": False,
                                "step": False, "state": False,
                            },
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
