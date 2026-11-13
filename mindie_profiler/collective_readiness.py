"""C7 rank-local collective readiness and observed context.

[Role]
  Read real Ascend profiler DB rows for HCCL ``COMMUNICATION_OP`` calls inside
  explicit time windows and expose per-rank entry/completion, actual typed
  operation bytes, causally joined unambiguous native children, observed waits,
  and recorded same-stream order.

[Invariants]
  * ``TASK.taskId`` is a task ordinal, never a ``STRING_IDS`` key.  Native
    names come from ``COMPUTE_TASK_INFO`` / ``COMMUNICATION_TASK_INFO`` /
    ``COMMUNICATION_SCHEDULE_TASK_INFO`` via unambiguous ``globalTaskId``;
    repeated ``globalTaskId`` occurrences across ``TASK`` or child tables stay
    unjoined and emit ``ambiguous_global_task_id``.
  * Disjoint windows are queried as disjoint intervals, never collapsed into a
    single ``[min(start), max(end)]`` span.
  * SQLite failures and shared wall-clock deadline expiries across SQLite and
    Python loops raise ``ProfilerQueryError`` rather than returning ``[]``.

[Timeouts & Locks]
  Read-only SQLite via ``sql.open_readonly`` plus shared monotonic deadline and
  ``O(log N + K)`` interval indexing with bounded detail caps; zero held locks.

[Side-Effect Policy]
  Reads selected source DBs and returns plain records; writes nothing.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from .accounting import merge_intervals
from .collective_readiness_db import (
    MAX_CALLS,
    MAX_CHILDREN,
    MAX_NS,
    MAX_TASKS,
    MAX_TOTAL_CALLS,
    MIN_SQLITE_LOCK_BUDGET_S,
    TaskGroupIndex,
    check_deadline,
    column_names,
    enum_map,
    fetch_rows,
    find_ambiguous_task_globals,
    index_call_ownership,
    int_id,
    load_raw_children,
    normalize_intervals,
    query_windowed_calls,
    query_windowed_tasks,
    resolve_strings,
    table_names,
)
from .events import ProfilerQueryError
from .segment import RankSource, discover_rank_sources, resolve_ranks
from .sql import open_readonly

SCHEMA = "mindie-profiler/collective-readiness/1"
MAX_OVERLAPS_PER_CALL = 32
MAX_TOTAL_OVERLAPS = 2_000
MAX_TOTAL_CHILDREN = 2_000
MAX_TOTAL_WAITS = 2_000
_DTYPE_WIDTHS = {
    "BFP16": 2,
    "BF16": 2,
    "FP16": 2,
    "FP32": 4,
    "FP64": 8,
    "INT8": 1,
    "UINT8": 1,
    "HIF8": 1,
    "INT16": 2,
    "UINT16": 2,
    "INT32": 4,
    "UINT32": 4,
    "INT64": 8,
    "UINT64": 8,
    "INT128": 16,
    "FP8E4M3": 1,
    "FP8E5M2": 1,
    "FP8E8M0": 1,
}


def _text(strings: dict[str, str], value: Any) -> str | None:
    return None if value is None else strings.get(str(value))


def _bound_task(related: Sequence[sqlite3.Row], op_start: int, op_end: int) -> sqlite3.Row | None:
    containing = [
        task
        for task in related
        if int(task["startNs"]) <= op_start and int(task["endNs"]) >= op_end
    ]
    exact = [
        task
        for task in containing
        if int(task["startNs"]) == op_start and int(task["endNs"]) == op_end
    ]
    chosen = exact or containing
    return chosen[0] if len(chosen) == 1 else None


def _collective_kind(op_name: str | None) -> str | None:
    lower = (op_name or "").lower()
    if "allgather" in lower:
        return "all_gather"
    if "reducescatter" in lower:
        return "reduce_scatter"
    if "alltoall" in lower:
        return "all_to_all"
    if "allreduce" in lower:
        return "all_reduce"
    return None


def _prior_task_causal_status(pred_type: str | None) -> str:
    upper = (pred_type or "").upper()
    if "WAIT" in upper:
        return "wait_prior_not_data"
    if "RECORD" in upper or "EVENT" in upper:
        return "event_order_candidate"
    return "same_stream_order_only"


def _call_rows(
    source: RankSource,
    *,
    intervals: Sequence[tuple[int, int]],
    deadline: float,
    timeout_s: float,
    limitations: set[str],
    budgets: dict[str, int],
) -> list[dict[str, Any]]:
    if not intervals:
        return []
    assert source.db_path is not None
    db_label = Path(source.db_path).name
    effective_timeout = max(0.1, float(timeout_s))
    check_deadline(deadline, db_label, effective_timeout)
    remaining_s = deadline - time.monotonic()
    if remaining_s < MIN_SQLITE_LOCK_BUDGET_S:
        raise ProfilerQueryError(
            f"{db_label}: remaining deadline ({remaining_s:.3f}s) is below minimum "
            f"SQLite lock budget ({MIN_SQLITE_LOCK_BUDGET_S:.1f}s); readiness budget exceeded"
        )
    db = open_readonly(
        source.db_path, timeout_s=min(effective_timeout, remaining_s), allow_pragma=True
    )
    db.row_factory = sqlite3.Row
    db.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 5_000)
    try:
        tables = table_names(db, db_label, deadline=deadline, timeout_s=effective_timeout)
        if "COMMUNICATION_OP" not in tables:
            limitations.add("missing_communication_op_table")
            return []
        cols = column_names(
            db, db_label, tables, "COMMUNICATION_OP", deadline=deadline, timeout_s=effective_timeout
        )
        if not {"startNs", "endNs", "connectionId", "deviceId"} <= cols:
            limitations.add("incomplete_communication_op_schema")
            return []

        data_types = enum_map(
            db, db_label, tables, "ENUM_HCCL_DATA_TYPE", deadline=deadline, timeout_s=effective_timeout
        )
        transports = enum_map(
            db,
            db_label,
            tables,
            "ENUM_HCCL_TRANSPORT_TYPE",
            deadline=deadline,
            timeout_s=effective_timeout,
        )

        has_op_id_col = "opId" in cols
        op_id_expr = "opId" if has_op_id_col else "rowid AS opId"
        order_col = "opId" if has_op_id_col else "rowid"
        selected = ["startNs", "endNs", "connectionId", "deviceId", op_id_expr]
        for optional in (
            "opName",
            "groupName",
            "dataType",
            "algType",
            "count",
            "rankSize",
            "transportType",
        ):
            if optional in cols:
                selected.append(optional)
        call_budget = max(0, MAX_TOTAL_CALLS - int(budgets.setdefault("calls", 0)))
        calls = query_windowed_calls(
            db,
            db_label,
            selected,
            order_col,
            intervals,
            limitations,
            deadline=deadline,
            timeout_s=effective_timeout,
            max_calls=min(MAX_CALLS, call_budget),
        )
        if not calls:
            return []

        task_cols = column_names(
            db, db_label, tables, "TASK", deadline=deadline, timeout_s=effective_timeout
        )
        can_query_task = {
            "startNs",
            "endNs",
            "connectionId",
            "deviceId",
            "globalTaskId",
            "streamId",
            "taskId",
            "taskType",
        } <= task_cols
        windowed = list(intervals) != [(0, MAX_NS)]
        call_envelopes = [
            (int(item["startNs"]), int(item["endNs"]))
            for item in calls
            if item["startNs"] is not None
            and item["endNs"] is not None
            and int(item["endNs"]) > int(item["startNs"])
        ]
        envelope_lims: set[str] = set()
        envelope_calls = (
            query_windowed_calls(
                db,
                db_label,
                ["startNs", "endNs", "connectionId", "deviceId", op_id_expr],
                order_col,
                merge_intervals(call_envelopes),
                envelope_lims,
                deadline=deadline,
                timeout_s=effective_timeout,
                max_calls=MAX_TOTAL_CALLS * 2,
            )
            if windowed and call_envelopes
            else calls
        )
        task_rows: list[sqlite3.Row] = []
        if can_query_task:
            devices = sorted(
                {str(item["deviceId"]) for item in calls if item["deviceId"] is not None}
            )
            task_intervals = merge_intervals([*intervals, *call_envelopes])
            task_rows = query_windowed_tasks(
                db,
                db_label,
                devices,
                task_intervals,
                limitations,
                deadline=deadline,
                timeout_s=effective_timeout,
            )

        grouped_rows: dict[tuple[str, str], list[sqlite3.Row]] = {}
        global_ids: set[Any] = set()
        referenced_string_ids: set[int] = set()
        for call in calls:
            for col in ("opName", "groupName"):
                if col in cols and (sid := int_id(call[col])) is not None:
                    referenced_string_ids.add(sid)
        for task in task_rows:
            if (sid := int_id(task["taskType"])) is not None:
                referenced_string_ids.add(sid)
            if task["globalTaskId"] is not None:
                global_ids.add(task["globalTaskId"])
            if task["connectionId"] is None or task["deviceId"] is None:
                continue
            grouped_rows.setdefault((str(task["connectionId"]), str(task["deviceId"])), []).append(
                task
            )

        ambiguous_globals = (
            find_ambiguous_task_globals(
                db, db_label, global_ids, deadline=deadline, timeout_s=effective_timeout
            )
            if can_query_task and global_ids
            else set()
        )
        if ambiguous_globals:
            limitations.add("ambiguous_global_task_id")

        task_index: dict[tuple[str, str], TaskGroupIndex] = {}
        for key, rows in grouped_rows.items():
            check_deadline(deadline, db_label, effective_timeout)
            task_index[key] = TaskGroupIndex(rows)

        task_by_global: dict[str, sqlite3.Row] = {}
        for task in task_rows:
            if task["globalTaskId"] is None:
                continue
            gid = str(task["globalTaskId"])
            if gid not in ambiguous_globals:
                task_by_global[gid] = task

        compute_raw, comm_raw, sched_raw, child_string_ids = load_raw_children(
            db,
            db_label,
            tables,
            global_ids,
            ambiguous_globals,
            limitations,
            deadline=deadline,
            timeout_s=effective_timeout,
        )
        referenced_string_ids.update(child_string_ids)
        claimed_globals, tasks_by_op_id, shared_conn_ops = index_call_ownership(
            calls,
            has_op_id_col=has_op_id_col,
            task_by_global=task_by_global,
            compute_raw=compute_raw,
            comm_raw=comm_raw,
            sched_raw=sched_raw,
            ambiguous_globals=ambiguous_globals,
            limitations=limitations,
            concurrency_calls=envelope_calls,
        )
        if "call_row_budget_reached" in envelope_lims:
            limitations.add("call_row_budget_reached")
            shared_conn_ops.update(str(item["opId"]) for item in calls)

        prepared_calls: list[
            tuple[
                sqlite3.Row,
                list[sqlite3.Row],
                list[sqlite3.Row],
                bool,
                sqlite3.Row | None,
                sqlite3.Row | None,
            ]
        ] = []
        for call in calls:
            check_deadline(deadline, db_label, effective_timeout)
            if call["startNs"] is None or call["endNs"] is None:
                limitations.add("invalid_communication_op_span")
                continue
            op_start, op_end = int(call["startNs"]), int(call["endNs"])
            if op_end <= op_start:
                limitations.add("invalid_communication_op_span")
                continue
            call_op_id = str(call["opId"])
            dev_str = str(call["deviceId"]) if call["deviceId"] is not None else ""
            explicit_owned = list(tasks_by_op_id.get((call_op_id, dev_str), ()))
            if call["connectionId"] is None:
                limitations.add("null_connection_id")
                bound_null = _bound_task(explicit_owned, op_start, op_end)
                prepared_calls.append((call, [], explicit_owned, False, bound_null, None))
                continue
            conn_key = (str(call["connectionId"]), dev_str)
            group = task_index.get(conn_key)
            scan_capped = False
            if group is not None:
                related, scan_capped = group.overlapping(op_start, op_end)
                if scan_capped:
                    limitations.add("overlap_scan_budget_reached")
            else:
                related = []
            seen_owned = {str(t["globalTaskId"]) for t in explicit_owned}
            owned_tasks = list(explicit_owned)
            unkeyed_related = [
                t for t in related if str(t["globalTaskId"]) not in claimed_globals
            ]
            if call_op_id in shared_conn_ops:
                if unkeyed_related:
                    limitations.add("shared_connection_without_op_id")
                bound = _bound_task(owned_tasks, op_start, op_end)
            else:
                candidates = list(explicit_owned)
                for t in unkeyed_related:
                    if str(t["globalTaskId"]) not in seen_owned:
                        candidates.append(t)
                bound = None if scan_capped else _bound_task(candidates, op_start, op_end)
                bound_gid = str(bound["globalTaskId"]) if bound is not None else None
                if not scan_capped:
                    for t in unkeyed_related:
                        gid = str(t["globalTaskId"])
                        if gid in seen_owned:
                            continue
                        if gid == bound_gid or (
                            op_start <= int(t["startNs"]) and int(t["endNs"]) <= op_end
                        ):
                            seen_owned.add(gid)
                            owned_tasks.append(t)
            owned_tasks.sort(
                key=lambda r: (int(r["startNs"]), int(r["endNs"]), str(r["globalTaskId"]))
            )
            pred: sqlite3.Row | None = None
            if bound is not None:
                stream = str(bound["streamId"])
                bound_global = str(bound["globalTaskId"])
                if group is not None:
                    pred = group.prior_on_stream(stream, op_start, bound_global)
                if pred is None and windowed and can_query_task and op_start > 0:
                    fallback = fetch_rows(
                        db,
                        db_label,
                        "SELECT startNs,endNs,connectionId,deviceId,globalTaskId,"
                        "streamId,taskId,taskType FROM TASK "
                        "WHERE connectionId=? AND deviceId=? AND streamId=? "
                        "AND endNs<=? AND globalTaskId!=? "
                        "ORDER BY endNs DESC, globalTaskId DESC LIMIT 1",
                        (
                            bound["connectionId"],
                            bound["deviceId"],
                            bound["streamId"],
                            op_start,
                            bound["globalTaskId"],
                        ),
                        1,
                        deadline=deadline,
                        timeout_s=effective_timeout,
                    )
                    if fallback:
                        pred = fallback[0]
                        if (sid := int_id(pred["taskType"])) is not None:
                            referenced_string_ids.add(sid)
            prepared_calls.append((call, related, owned_tasks, scan_capped, bound, pred))

        strings = resolve_strings(
            db,
            db_label,
            tables,
            referenced_string_ids,
            limitations,
            deadline=deadline,
            timeout_s=effective_timeout,
        )

        result: list[dict[str, Any]] = []
        for call, related, owned_tasks, scan_capped, bound, pred in prepared_calls:
            check_deadline(deadline, db_label, effective_timeout)
            op_start, op_end = int(call["startNs"]), int(call["endNs"])
            call_op_id = str(call["opId"])
            device = str(call["deviceId"]) if call["deviceId"] is not None else None
            conn_str = str(call["connectionId"]) if call["connectionId"] is not None else None
            if bound is not None:
                participants = [bound]
            elif owned_tasks:
                participants = [
                    task
                    for task in owned_tasks
                    if int(task["startNs"]) == op_start or int(task["endNs"]) == op_end
                ] or list(owned_tasks)
            else:
                participants = []
            participant_globals = {str(task["globalTaskId"]) for task in participants}
            service: list[dict[str, Any]] = []
            waits: list[dict[str, Any]] = []
            deps: list[dict[str, Any]] = []
            seen_children: set[tuple[str, str]] = set()
            had_ambiguous_child = any(
                str(t["globalTaskId"]) in ambiguous_globals for t in (*owned_tasks, *related)
            )

            for task in owned_tasks:
                global_id = str(task["globalTaskId"])
                task_type = _text(strings, task["taskType"])
                if global_id in ambiguous_globals:
                    had_ambiguous_child = True
                else:
                    for raw_child in (
                        compute_raw.get(global_id),
                        comm_raw.get(global_id),
                        sched_raw.get(global_id),
                    ):
                        if not raw_child:
                            continue
                        if (
                            has_op_id_col
                            and raw_child.get("_op_id") is not None
                            and raw_child["_op_id"] != call_op_id
                        ):
                            continue
                        key = (raw_child["source_table"], global_id)
                        if key in seen_children:
                            continue
                        seen_children.add(key)
                        if budgets["children"] >= MAX_TOTAL_CHILDREN:
                            limitations.add("child_detail_capped")
                            continue
                        budgets["children"] += 1
                        child_entry: dict[str, Any] = {
                            "source_table": raw_child["source_table"],
                            "global_task_id": global_id,
                            "name": _text(strings, raw_child.get("_name_id")),
                            "task_type": raw_child["task_type"],
                            "task_type_name": task_type,
                        }
                        if "_op_type_id" in raw_child:
                            child_entry["op_type"] = _text(strings, raw_child["_op_type_id"])
                        if "timestamp_ns" in raw_child:
                            child_entry["timestamp_ns"] = raw_child["timestamp_ns"]
                        service.append(child_entry)
                upper_name = (task_type or "").upper()
                if "WAIT" in upper_name or "SYNC" in upper_name:
                    if budgets["waits"] >= MAX_TOTAL_WAITS:
                        limitations.add("wait_detail_capped")
                    else:
                        budgets["waits"] += 1
                        waits.append(
                            {
                                "source_table": "TASK",
                                "global_task_id": global_id,
                                "stream_id": str(task["streamId"]),
                                "task_id": str(task["taskId"]),
                                "task_type": str(task["taskType"]),
                                "task_type_name": task_type,
                                "start_ns": int(task["startNs"]),
                                "end_ns": int(task["endNs"]),
                                "duration_ns": max(0, int(task["endNs"]) - int(task["startNs"])),
                            }
                        )

            if pred is not None:
                pred_type = _text(strings, pred["taskType"])
                deps.append(
                    {
                        "kind": "same_stream_prior_task",
                        "relation": "recorded_same_stream_order",
                        "causal_status": _prior_task_causal_status(pred_type),
                        "global_task_id": str(pred["globalTaskId"]),
                        "stream_id": str(pred["streamId"]),
                        "task_id": str(pred["taskId"]),
                        "task_type": str(pred["taskType"]),
                        "task_type_name": pred_type,
                        "end_ns": int(pred["endNs"]),
                        "source_table": "TASK",
                    }
                )

            overlaps: list[dict[str, Any]] = []
            if len(related) > MAX_OVERLAPS_PER_CALL:
                limitations.add("overlap_detail_capped")
            for task in related[:MAX_OVERLAPS_PER_CALL]:
                if budgets["overlaps"] >= MAX_TOTAL_OVERLAPS:
                    limitations.add("overlap_detail_capped")
                    break
                budgets["overlaps"] += 1
                overlaps.append(
                    {
                        "source_table": "TASK",
                        "global_task_id": str(task["globalTaskId"]),
                        "stream_id": str(task["streamId"]),
                        "task_id": str(task["taskId"]),
                        "task_type": str(task["taskType"]),
                        "task_type_name": _text(strings, task["taskType"]),
                        "start_ns": int(task["startNs"]),
                        "end_ns": int(task["endNs"]),
                        "causal_join": False,
                    }
                )

            service_ns: list[int] = []
            for child in service:
                task = task_by_global.get(str(child.get("global_task_id")))
                if task is not None:
                    child["start_ns"] = int(task["startNs"])
                    child["end_ns"] = int(task["endNs"])
                    child["duration_ns"] = max(0, int(task["endNs"]) - int(task["startNs"]))
                    child["interval_kind"] = "task_interval"
                    service_ns.append(child["duration_ns"])

            op_name = _text(strings, call["opName"]) if "opName" in cols else None
            collective = _collective_kind(op_name)
            dtype = data_types.get(str(call["dataType"])) if "dataType" in cols else None
            elements = call["count"] if "count" in cols else None
            width = _DTYPE_WIDTHS.get(dtype or "")
            communicator = _text(strings, call["groupName"]) if "groupName" in cols else None
            unknowns = (
                ([] if bound is not None else ["call_bound_task_unresolved"])
                + ([] if deps else ["causal_predecessor_not_joined"])
                + ([] if service else ["native_child_not_joined"])
                + (["native_child_global_task_ambiguous"] if had_ambiguous_child else [])
                + ["cross_rank_clock_not_established"]
            )
            result.append(
                {
                    "rank_id": source.rank_id,
                    "rank_index": source.rank_index,
                    "device_id": device,
                    "connection_id": conn_str,
                    "op_id": str(call["opId"]),
                    "operation": {
                        "op_name": op_name,
                        "collective": collective,
                        "group_name": communicator,
                        "communicator": communicator,
                        "count": elements,
                        "data_type": call["dataType"] if "dataType" in cols else None,
                        "dtype": dtype,
                        "typed_bytes": (
                            int(elements) * width
                            if elements is not None and width is not None
                            else None
                        ),
                        "alg_type": call["algType"] if "algType" in cols else None,
                        "rank_size": call["rankSize"] if "rankSize" in cols else None,
                        "transport": (
                            transports.get(str(call["transportType"]))
                            if "transportType" in cols
                            else None
                        ),
                    },
                    "entry": {
                        "start_ns": op_start,
                        "source_table": "COMMUNICATION_OP",
                        "op_id": str(call["opId"]),
                    },
                    "completion": {
                        "end_ns": op_end,
                        "source_table": "COMMUNICATION_OP",
                        "op_id": str(call["opId"]),
                    },
                    "service_children": service,
                    "service": {
                        "envelope_ns": max(0, op_end - op_start),
                        "child_durations_ns": service_ns,
                        "wait_durations_ns": [w["duration_ns"] for w in waits],
                        "active_service_ns": None,
                        "accounting_basis": "parent_envelope_not_sum_of_children_or_waits",
                    },
                    "waits": waits,
                    "dependencies": deps,
                    "observed_overlaps": overlaps,
                    "observed_context": {
                        "entry_ns": op_start,
                        "completion_ns": op_end,
                        "entry_domain": "rank_local",
                        "cross_rank_aligned": False,
                        "bound_task_global_id": (
                            str(bound["globalTaskId"]) if bound is not None else None
                        ),
                        "participant_global_ids": sorted(participant_globals),
                    },
                    "clock": {
                        "domain": "rank_local",
                        "cross_rank_aligned": False,
                        "basis": (
                            "native TASK/COMMUNICATION_OP timestamps on one rank; "
                            "no runtime clock correlation supplied"
                        ),
                    },
                    "unknowns": unknowns,
                    "provenance": {
                        "source": source.db_path,
                        "rank_id": source.rank_id,
                        "device_id": device,
                        "query_tables": [
                            "COMMUNICATION_OP",
                            "TASK",
                            "STRING_IDS",
                            "COMPUTE_TASK_INFO",
                            "COMMUNICATION_TASK_INFO",
                            "COMMUNICATION_SCHEDULE_TASK_INFO",
                        ],
                        "accounting_basis": (
                            "one_rank_local_semantic_call; children joined by "
                            "unambiguous globalTaskId/connection, not summed"
                        ),
                    },
                }
            )
        counts: dict[tuple[Any, ...], int] = {}
        for item in result:
            operation = item["operation"]
            key = (
                item["rank_id"],
                operation.get("communicator")
                or operation.get("group_name")
                or operation.get("op_name"),
                operation.get("collective"),
            )
            item["call_ordinal"] = counts.get(key, 0)
            counts[key] = item["call_ordinal"] + 1
        budgets["calls"] = int(budgets.get("calls", 0)) + len(result)
        return result
    finally:
        db.set_progress_handler(None, 0)
        db.close()


def read_collective_readiness(
    root: str | Path,
    *,
    source: str = "auto",
    ranks: Iterable[str] | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    windows: Sequence[tuple[int, int]] | None = None,
    timeout_s: float = 20.0,
    resolved_sources: Sequence[RankSource] | None = None,
) -> dict[str, Any]:
    """Return the public C7 readiness report for a captured bundle."""
    effective_timeout = max(0.1, float(timeout_s))
    deadline = time.monotonic() + effective_timeout
    intervals = normalize_intervals(start_ns, end_ns, windows)
    sources = (
        list(resolved_sources)
        if resolved_sources is not None
        else resolve_ranks(discover_rank_sources(root, source=source), ranks)
    )
    calls: list[dict[str, Any]] = []
    limitations: set[str] = set()
    budgets = {"calls": 0, "overlaps": 0, "children": 0, "waits": 0}
    db_sources = 0
    for item in sources:
        if item.db_path and source != "csv":
            db_sources += 1
            calls.extend(
                _call_rows(
                    item,
                    intervals=intervals,
                    deadline=deadline,
                    timeout_s=effective_timeout,
                    limitations=limitations,
                    budgets=budgets,
                )
            )
    ordered_limitations: list[str] = []
    if db_sources == 0:
        ordered_limitations.append("no_db_source")
    if not calls:
        ordered_limitations.append("no_communication_op_rows")
    for code in sorted(limitations):
        if code not in ordered_limitations:
            ordered_limitations.append(code)
    return {
        "schema": SCHEMA,
        "status": "observed" if calls else "unavailable",
        "calls": calls,
        "rank_count": len(sources),
        "clock": {
            "cross_rank_aligned": False,
            "basis": "rank-local DB timestamps; no runtime clock correlation",
        },
        "limitations": ordered_limitations,
    }


def attach_to_report(
    report: dict[str, Any],
    root: str | Path,
    *,
    source: str = "auto",
    ranks: Iterable[str] | None = None,
    start_ns: int | None = None,
    end_ns: int | None = None,
    windows: Sequence[tuple[int, int]] | None = None,
    timeout_s: float = 20.0,
) -> dict[str, Any]:
    """Attach a readiness document beside an existing C7 report."""
    report["collective_readiness"] = read_collective_readiness(
        root,
        source=source,
        ranks=ranks,
        start_ns=start_ns,
        end_ns=end_ns,
        windows=windows,
        timeout_s=timeout_s,
    )
    return report


__all__ = [
    "MAX_CALLS",
    "MAX_CHILDREN",
    "MAX_OVERLAPS_PER_CALL",
    "MAX_TASKS",
    "MAX_TOTAL_CALLS",
    "MAX_TOTAL_CHILDREN",
    "MAX_TOTAL_OVERLAPS",
    "MAX_TOTAL_WAITS",
    "MIN_SQLITE_LOCK_BUDGET_S",
    "SCHEMA",
    "attach_to_report",
    "read_collective_readiness",
]
