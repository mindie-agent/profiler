"""C7 rank-local collective readiness and observed context.

[Role]
  Read real Ascend profiler DB rows for HCCL COMMUNICATION_OP calls and expose
  per-rank entry/completion, actual typed operation bytes, causally joined
  native children, observed waits and recorded same-stream order.
[Invariants]
  * ``TASK.taskId`` is a task ordinal, never a STRING_IDS key.  Native names
    come from COMPUTE_TASK_INFO/COMMUNICATION_TASK_INFO/
    COMMUNICATION_SCHEDULE_TASK_INFO via globalTaskId/connectionId; task type
    names come from TASK.taskType.
  * Only causally joined native rows become service children.  Merely
    overlapping TASK rows stay in ``observed_overlaps`` as context.
  * Rank-local chronology never becomes a ready threshold or a cross-rank
    clock.  Missing causal predecessor/clock evidence remains unknown.
  * One bounded scan per selected rank/window; no per-call TASK rescans.
[Timeouts & Locks]
  Read-only sqlite connections, bounded row/index working sets; no locks held.
[Side-Effect Policy]
  Reads selected source DBs and returns plain records; writes nothing.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from urllib.parse import quote

from .events import ProfilerUsageError
from .segment import discover_rank_sources, resolve_ranks

SCHEMA = "mindie-profiler/collective-readiness/1"
MAX_CALLS = 20_000
MAX_TASKS = 20_000
MAX_CHILDREN = 2_000


def _connect(path: str) -> sqlite3.Connection:
    try:
        return sqlite3.connect(f"file:{quote(str(path))}?mode=ro", uri=True,
                               timeout=5.0)
    except sqlite3.Error as exc:
        raise ProfilerUsageError(f"cannot open profiler DB {path}: {exc}") from exc


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    return {str(row[1]) for row in db.execute(f"PRAGMA table_info({table})")}


def _tables(db: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _rows(db: sqlite3.Connection, sql: str, args=(), limit: int = MAX_TASKS):
    db.row_factory = sqlite3.Row
    try:
        return list(db.execute(sql, args).fetchmany(limit))
    except sqlite3.Error:
        return []


def _strings(db: sqlite3.Connection) -> dict[str, str]:
    if "STRING_IDS" not in _tables(db):
        return {}
    return {str(row["id"]): str(row["value"]) for row in _rows(
        db, "SELECT id,value FROM STRING_IDS", limit=100_000)}


def _text(strings: dict[str, str], value) -> str | None:
    return None if value is None else strings.get(str(value))


def _task_type_name(strings, value) -> str | None:
    return _text(strings, value)


def _enum_map(db, table, strings):
    if "id" not in _columns(db, table) or "name" not in _columns(db, table):
        return {}
    return {str(row["id"]): str(row["name"]) for row in _rows(
        db, f"SELECT id,name FROM {table}", limit=10_000)}


def _chunks(items, size=500):
    items = list(items)
    for start in range(0, len(items), size):
        yield items[start:start + size]


def _load_children(db, strings, global_ids):
    """Load actual native children once for the selected global task ids."""
    global_ids = sorted({int(item) for item in global_ids if item is not None})
    compute, comm, schedule = {}, {}, {}
    tables = _tables(db)
    for chunk in _chunks(global_ids):
        marks = ",".join("?" for _ in chunk)
        if "COMPUTE_TASK_INFO" in tables:
            for row in _rows(
                    db,
                    f"SELECT globalTaskId,name,opType,taskType FROM COMPUTE_TASK_INFO "
                    f"WHERE globalTaskId IN ({marks})", tuple(chunk), MAX_CHILDREN):
                compute[str(row["globalTaskId"])] = {
                    "source_table": "COMPUTE_TASK_INFO",
                    "global_task_id": str(row["globalTaskId"]),
                    "name": _text(strings, row["name"]),
                    "op_type": _text(strings, row["opType"]),
                    "task_type": str(row["taskType"]),
                }
        if "COMMUNICATION_TASK_INFO" in tables:
            for row in _rows(
                    db,
                    f"SELECT globalTaskId,name,taskType,timestampNs "
                    f"FROM COMMUNICATION_TASK_INFO WHERE globalTaskId IN ({marks})",
                    tuple(chunk), MAX_CHILDREN):
                comm[str(row["globalTaskId"])] = {
                    "source_table": "COMMUNICATION_TASK_INFO",
                    "global_task_id": str(row["globalTaskId"]),
                    "name": _text(strings, row["name"]),
                    "task_type": str(row["taskType"]),
                    "timestamp_ns": int(row["timestampNs"]),
                }
        if "COMMUNICATION_SCHEDULE_TASK_INFO" in tables:
            for row in _rows(
                    db,
                    f"SELECT globalTaskId,name,taskType FROM "
                    f"COMMUNICATION_SCHEDULE_TASK_INFO WHERE globalTaskId IN ({marks})",
                    tuple(chunk), MAX_CHILDREN):
                schedule[str(row["globalTaskId"])] = {
                    "source_table": "COMMUNICATION_SCHEDULE_TASK_INFO",
                    "global_task_id": str(row["globalTaskId"]),
                    "name": _text(strings, row["name"]),
                    "task_type": str(row["taskType"]),
                }
    return compute, comm, schedule


def _bound_task(op, tasks_by_key):
    """Find one containing TASK by real connectionId/device/interval."""
    candidates = tasks_by_key.get((str(op["connectionId"]), str(op["deviceId"])), ())
    containing = [task for task in candidates
                  if int(task["startNs"]) <= int(op["startNs"])
                  and int(task["endNs"]) >= int(op["endNs"])]
    exact = [task for task in containing
             if int(task["startNs"]) == int(op["startNs"])
             and int(task["endNs"]) == int(op["endNs"])]
    chosen = exact or containing
    return chosen[0] if len(chosen) == 1 else None


def _call_rows(source, *, start_ns=None, end_ns=None):
    db = _connect(source.db_path)
    try:
        strings = _strings(db)
        data_types = _enum_map(db, "ENUM_HCCL_DATA_TYPE", strings)
        transports = _enum_map(db, "ENUM_HCCL_TRANSPORT_TYPE", strings)
        cols = _columns(db, "COMMUNICATION_OP")
        if not {"startNs", "endNs", "connectionId", "deviceId"} <= cols:
            return []
        selected = ["startNs", "endNs", "connectionId", "deviceId", "opId"]
        for optional in ("opName", "groupName", "dataType", "algType",
                         "count", "rankSize", "transportType"):
            if optional in cols:
                selected.append(optional)
        low = int(start_ns or 0)
        high = int(end_ns or 9_223_372_036_854_775_807)
        calls = _rows(
            db, "SELECT " + ",".join(selected) + " FROM COMMUNICATION_OP "
            "WHERE endNs>? AND startNs<? ORDER BY startNs,opId LIMIT ?",
            (low, high, MAX_CALLS + 1), MAX_CALLS + 1)
        if not calls:
            return []
        devices = sorted({str(item["deviceId"]) for item in calls})
        task_rows = []
        for chunk in _chunks(devices):
            marks = ",".join("?" for _ in chunk)
            task_rows.extend(_rows(
                db, "SELECT startNs,endNs,connectionId,deviceId,globalTaskId,"
                "streamId,taskId,taskType FROM TASK WHERE deviceId IN (" + marks +
                ") AND endNs>? AND startNs<? ORDER BY startNs,globalTaskId LIMIT ?",
                (*chunk, low, high, MAX_TASKS), MAX_TASKS))
        tasks_by_key = {}
        task_by_global = {}
        for task in task_rows:
            tasks_by_key.setdefault((str(task["connectionId"]),
                                     str(task["deviceId"])), []).append(task)
            task_by_global[str(task["globalTaskId"])] = task
        # Only children referenced by actual containing/participant tasks.
        global_ids = {str(task["globalTaskId"]) for task in task_rows}
        compute, comm_info, schedule = _load_children(db, strings, global_ids)
        result = []
        for call in calls[:MAX_CALLS]:
            op_start, op_end = int(call["startNs"]), int(call["endNs"])
            device = str(call["deviceId"])
            bound = _bound_task(call, tasks_by_key)
            participants = []
            if bound is not None:
                participants = [bound]
            else:
                for task in tasks_by_key.get((str(call["connectionId"]), device), ()):
                    if (int(task["startNs"]) == op_start
                            or int(task["endNs"]) == op_end):
                        participants.append(task)
            participant_globals = {str(task["globalTaskId"]) for task in participants}
            related = [task for task in tasks_by_key.get(
                (str(call["connectionId"]), device), ())
                if int(task["startNs"]) <= op_end and int(task["endNs"]) >= op_start]
            service, waits, deps = [], [], []
            seen_children = set()
            for task in related:
                global_id = str(task["globalTaskId"])
                task_type = _task_type_name(strings, task["taskType"])
                for child in (compute.get(global_id), comm_info.get(global_id),
                              schedule.get(global_id)):
                    if not child:
                        continue
                    key = (child["source_table"], global_id)
                    if key not in seen_children:
                        seen_children.add(key)
                        service.append({**child, "task_type_name": task_type})
                name = task_type or ""
                if "WAIT" in name.upper() or "SYNC" in name.upper():
                    waits.append({
                        "source_table": "TASK",
                        "global_task_id": global_id,
                        "stream_id": str(task["streamId"]),
                        "task_id": str(task["taskId"]),
                        "task_type": str(task["taskType"]),
                        "task_type_name": task_type,
                        "start_ns": int(task["startNs"]),
                        "end_ns": int(task["endNs"]),
                        "duration_ns": max(0, int(task["endNs"]) - int(task["startNs"])),
                    })
            if bound is not None:
                stream = str(bound["streamId"])
                key = (str(bound["connectionId"]), device)
                prior = [task for task in tasks_by_key.get(key, ())
                         if str(task["streamId"]) == stream
                         and int(task["endNs"]) <= op_start
                         and str(task["globalTaskId"]) != str(bound["globalTaskId"])]
                pred = max(prior, key=lambda item: int(item["endNs"]), default=None)
                if pred is not None:
                    pred_type = _task_type_name(strings, pred["taskType"])
                    if pred_type and "WAIT" in pred_type.upper():
                        causal = "wait_prior_not_data"
                    elif pred_type and ("RECORD" in pred_type.upper()
                                        or "EVENT" in pred_type.upper()):
                        causal = "event_order_candidate"
                    else:
                        causal = "same_stream_order_only"
                    deps.append({
                        "kind": "same_stream_prior_task",
                        "relation": "recorded_same_stream_order",
                        "causal_status": causal,
                        "global_task_id": str(pred["globalTaskId"]),
                        "stream_id": str(pred["streamId"]),
                        "task_id": str(pred["taskId"]),
                        "task_type": str(pred["taskType"]),
                        "task_type_name": pred_type,
                        "end_ns": int(pred["endNs"]),
                        "source_table": "TASK",
                    })
            op_name = (_text(strings, call["opName"])
                       if "opName" in cols else None)
            lower_name = (op_name or "").lower()
            collective = ("all_gather" if "allgather" in lower_name
                          else "reduce_scatter" if "reducescatter" in lower_name
                          else "all_to_all" if "alltoall" in lower_name
                          else "all_reduce" if "allreduce" in lower_name
                          else None)
            dtype = (data_types.get(str(call["dataType"]))
                     if "dataType" in cols else None)
            elements = call["count"] if "count" in cols else None
            width = {"BFP16": 2, "FP16": 2, "FP32": 4, "INT8": 1,
                     "FP8E4M3": 1, "FP8E5M2": 1, "FP8E8M0": 1}.get(dtype)
            overlaps = [{
                "source_table": "TASK",
                "global_task_id": str(task["globalTaskId"]),
                "stream_id": str(task["streamId"]),
                "task_id": str(task["taskId"]),
                "task_type": str(task["taskType"]),
                "task_type_name": _task_type_name(strings, task["taskType"]),
                "start_ns": int(task["startNs"]),
                "end_ns": int(task["endNs"]),
                "causal_join": False,
            } for task in tasks_by_key.get((str(call["connectionId"]), device), ())
                if int(task["startNs"]) <= op_end and int(task["endNs"]) >= op_start]
            service_ns = []
            for child in service:
                task = task_by_global.get(str(child.get("global_task_id")))
                if task is not None:
                    child["start_ns"] = int(task["startNs"])
                    child["end_ns"] = int(task["endNs"])
                    child["duration_ns"] = max(
                        0, int(task["endNs"]) - int(task["startNs"]))
                    child["interval_kind"] = "task_interval"
                    service_ns.append(child["duration_ns"])
            communicator = (_text(strings, call["groupName"])
                            if "groupName" in cols else None)
            result.append({
                "rank_id": source.rank_id,
                "rank_index": source.rank_index,
                "device_id": device,
                "connection_id": str(call["connectionId"]),
                "op_id": str(call["opId"]),
                "operation": {
                    "op_name": op_name,
                    "collective": collective,
                    "group_name": communicator,
                    "communicator": communicator,
                    "count": elements,
                    "data_type": call["dataType"] if "dataType" in cols else None,
                    "dtype": dtype,
                    "typed_bytes": (int(elements) * width
                                    if elements is not None and width else None),
                    "alg_type": call["algType"] if "algType" in cols else None,
                    "rank_size": call["rankSize"] if "rankSize" in cols else None,
                    "transport": (transports.get(str(call["transportType"]))
                                  if "transportType" in cols else None),
                },
                "entry": {"start_ns": op_start, "source_table": "COMMUNICATION_OP",
                          "op_id": str(call["opId"])},
                "completion": {"end_ns": op_end, "source_table": "COMMUNICATION_OP",
                               "op_id": str(call["opId"])},
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
                "observed_overlaps": overlaps[:MAX_CHILDREN],
                "observed_context": {
                    "entry_ns": op_start, "completion_ns": op_end,
                    "entry_domain": "rank_local", "cross_rank_aligned": False,
                    "bound_task_global_id": (str(bound["globalTaskId"])
                                             if bound is not None else None),
                    "participant_global_ids": sorted(participant_globals),
                },
                "clock": {
                    "domain": "rank_local", "cross_rank_aligned": False,
                    "basis": "native TASK/COMMUNICATION_OP timestamps on one rank; no runtime clock correlation supplied",
                },
                "unknowns": ([] if bound is not None
                             else ["call_bound_task_unresolved"])
                + ([] if deps else ["causal_predecessor_not_joined"])
                + ([] if service else ["native_child_not_joined"])
                + ["cross_rank_clock_not_established"],
                "provenance": {
                    "source": source.db_path,
                    "rank_id": source.rank_id,
                    "device_id": device,
                    "query_tables": ["COMMUNICATION_OP", "TASK", "STRING_IDS",
                                     "COMPUTE_TASK_INFO", "COMMUNICATION_TASK_INFO",
                                     "COMMUNICATION_SCHEDULE_TASK_INFO"],
                    "accounting_basis": "one_rank_local_semantic_call; children joined by globalTaskId/connection, not summed",
                },
            })
        counts = {}
        for item in result:
            operation = item["operation"]
            key = (item["rank_id"],
                   operation.get("communicator") or operation.get("group_name")
                   or operation.get("op_name"),
                   operation.get("collective"))
            item["call_ordinal"] = counts.get(key, 0)
            counts[key] = item["call_ordinal"] + 1
        return result
    finally:
        db.close()


def read_collective_readiness(root: str | Path, *, source: str = "auto",
                             ranks=None, start_ns: int | None = None,
                             end_ns: int | None = None) -> dict:
    """Return the public C7 readiness report for a captured bundle."""
    sources = resolve_ranks(discover_rank_sources(root, source=source), ranks)
    calls = []
    for item in sources:
        if item.db_path:
            calls.extend(_call_rows(item, start_ns=start_ns, end_ns=end_ns))
    return {
        "schema": SCHEMA,
        "status": "observed" if calls else "unavailable",
        "calls": calls,
        "rank_count": len(sources),
        "clock": {"cross_rank_aligned": False,
                  "basis": "rank-local DB timestamps; no runtime clock correlation"},
        "limitations": ([] if calls else ["no_communication_op_rows"])
        + (["call_row_budget_reached"] if len(calls) >= MAX_CALLS else []),
    }


def attach_to_report(report, root, *, source="auto", ranks=None) -> dict:
    """Attach a readiness document beside an existing C7 report."""
    report["collective_readiness"] = read_collective_readiness(
        root, source=source, ranks=ranks)
    return report
