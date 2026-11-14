"""Collective readiness C7 SQLite joins, Golden Capture windows, and error honesty.

[Role]
  Verify ``read_collective_readiness`` and ``analyze_profile`` resolve real
  ``TASK.taskType`` and unambiguous ``globalTaskId`` joins on retained 2-rank
  Ascend950 Golden Captures, exclude gap collectives across disjoint windows,
  reject ambiguous repeated ``globalTaskId`` rows, resolve ``STRING_IDS`` IDs
  above 200,000 without truncation, and enforce shared ``timeout_s`` deadlines.

[Invariants]
  * ``TASK.taskId`` is a local ordinal and never decoded via ``STRING_IDS``.
  * Disjoint windows return only collectives overlapping the requested windows,
    never gap collectives inside ``[min(start), max(end)]``.
  * Repeated ``globalTaskId`` occurrences across ``TASK`` or child tables emit
    ``ambiguous_global_task_id`` and never attach collided child intervals.
  * Corrupt SQLite files and deadline expiries raise ``ProfilerError``.

[Timeouts & Locks]
  Retained 84 KB Ascend950 Golden Capture DBs and ``tmp_path`` SQLite fixtures;
  read-only queries under explicit deadlines; zero network or device access.

[Side-Effect Policy]
  Reads ``tests/fixtures/collective_readiness_a5_allreduce`` read-only; writes
  only inside pytest ``tmp_path``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path

import pytest

from mindie_profiler.analyze import analyze_profile
from mindie_profiler.collective_readiness import read_collective_readiness
from mindie_profiler.events import ProfilerError, ProfilerQueryError, Window

REAL_A5_FIXTURE = Path(__file__).parent / "fixtures" / "collective_readiness_a5_allreduce"
REAL_A5_PROVENANCE = REAL_A5_FIXTURE / "slice_provenance.json"


def _create_readiness_db(
    root: Path,
    rank: int,
    *,
    prior: bool = True,
    connection_base: int = 2,
    op_count: int = 1,
    string_id_offset: int = 100,
) -> Path:
    out = root / f"rank{rank}" / "profile" / "p" / "ASCEND_PROFILER_OUTPUT"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"ascend_pytorch_profiler_{rank}.db"
    db = sqlite3.connect(path)
    db.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(
            startNs INTEGER, endNs INTEGER, deviceId INTEGER,
            connectionId INTEGER, globalTaskId INTEGER, streamId INTEGER,
            taskId INTEGER, taskType INTEGER
        );
        CREATE TABLE COMMUNICATION_OP(
            opName INTEGER, startNs INTEGER, endNs INTEGER,
            connectionId INTEGER, groupName INTEGER, opId INTEGER PRIMARY KEY,
            dataType INTEGER, algType INTEGER, count NUMERIC, deviceId INTEGER,
            rankSize INTEGER, transportType INTEGER
        );
        CREATE TABLE COMPUTE_TASK_INFO(
            globalTaskId INTEGER, name INTEGER, opType INTEGER, taskType INTEGER
        );
        CREATE TABLE COMMUNICATION_TASK_INFO(
            timestampNs INTEGER, name INTEGER, globalTaskId INTEGER, taskType INTEGER
        );
        CREATE TABLE COMMUNICATION_SCHEDULE_TASK_INFO(
            globalTaskId INTEGER, name INTEGER, taskType INTEGER
        );
        CREATE TABLE ENUM_HCCL_DATA_TYPE(id INTEGER PRIMARY KEY, name TEXT);
        CREATE TABLE ENUM_HCCL_TRANSPORT_TYPE(id INTEGER PRIMARY KEY, name TEXT);
        """
    )
    string_rows = [
        (5, "EVENT RECORD"),
        (7, "NOTIFY WAIT"),
        (32, "group_name_0"),
        (36, "HcclLaunchAicpuKernel"),
        (37, "N/A"),
    ]
    for idx in range(op_count):
        string_rows.append((string_id_offset + idx, f"hcom_allGather_AicpuKernel_612_{idx}_1"))
    db.executemany("INSERT INTO STRING_IDS(id, value) VALUES(?, ?)", string_rows)
    db.executemany("INSERT INTO ENUM_HCCL_DATA_TYPE VALUES(?, ?)", [(11, "BFP16")])
    db.executemany("INSERT INTO ENUM_HCCL_TRANSPORT_TYPE VALUES(?, ?)", [(3, "UB")])

    for idx in range(op_count):
        base_ns = idx * 10_000
        conn_id = connection_base + idx
        gtid_prior = idx * 10 + 1
        gtid_comm = idx * 10 + 2
        if prior:
            db.execute(
                "INSERT INTO TASK VALUES(?, ?, ?, ?, ?, 26, 999, 5)",
                (base_ns + 100, base_ns + 900, rank, conn_id, gtid_prior),
            )
        db.execute(
            "INSERT INTO TASK VALUES(?, ?, ?, ?, ?, 26, ?, 7)",
            (base_ns + 1000, base_ns + 2000, rank, conn_id, gtid_comm, 1000 + idx),
        )
        db.execute(
            "INSERT INTO COMMUNICATION_OP VALUES(?, ?, ?, ?, 32, ?, 11, 32, 5120, ?, 2, 3)",
            (string_id_offset + idx, base_ns + 1000, base_ns + 2000, conn_id, idx, rank),
        )
        db.execute(
            "INSERT INTO COMMUNICATION_TASK_INFO VALUES(?, 37, ?, 7)",
            (base_ns + 1000, gtid_comm),
        )
        db.execute(
            "INSERT INTO COMMUNICATION_SCHEDULE_TASK_INFO VALUES(?, 36, 37)",
            (gtid_comm,),
        )
    db.commit()
    db.close()
    return path


def test_real_a5_two_rank_golden_capture_and_disjoint_windows(tmp_path: Path) -> None:
    meta = json.loads(REAL_A5_PROVENANCE.read_text(encoding="utf-8"))
    assert meta["not_fabricated"] is True
    a5_root = tmp_path / "real_a5_capture"
    for rank_name, info in meta["ranks"].items():
        sql_file = REAL_A5_FIXTURE / info["sql_relpath"]
        sql_bytes = sql_file.read_bytes()
        assert hashlib.sha256(sql_bytes).hexdigest() == info["sql_sha256"]
        db_rel = info["sql_relpath"][:-4] + ".db"
        db_file = a5_root / db_rel
        db_file.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(db_file)
        con.executescript(sql_bytes.decode("utf-8"))
        for table, expected_rows in info["row_counts"].items():
            cur = con.execute(f'SELECT * FROM "{table}"')
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            assert len(rows) == expected_rows, (rank_name, table)
            digest = hashlib.sha256()
            digest.update(json.dumps(cols).encode("utf-8") + b"\n")
            for row in sorted(rows, key=lambda r: tuple((type(v).__name__, repr(v)) for v in r)):
                digest.update(
                    json.dumps(
                        [[type(v).__name__, v.hex() if isinstance(v, bytes) else v] for v in row],
                        ensure_ascii=False,
                    ).encode("utf-8")
                    + b"\n"
                )
            assert digest.hexdigest() == info["table_sha256"][table], (rank_name, table)
        con.close()

    full = read_collective_readiness(a5_root, source="db")
    assert full["status"] == "observed"
    assert full["rank_count"] == 2
    assert len(full["calls"]) == 20
    r0_calls = [c for c in full["calls"] if c["rank_id"] == "rank_0"]
    r1_calls = [c for c in full["calls"] if c["rank_id"] == "rank_1"]
    assert len(r0_calls) == len(r1_calls) == 10
    assert [c["call_ordinal"] for c in r0_calls] == list(range(10))
    assert all(c["operation"]["collective"] == "all_reduce" for c in full["calls"])
    # Each benchmark iteration pairs a 4-byte FP32 sync all_reduce with a 1 MiB BFP16 payload all_reduce.
    assert [c["operation"]["typed_bytes"] for c in r0_calls] == [4, 1_048_576] * 5
    assert [c["operation"]["typed_bytes"] for c in r1_calls] == [4, 1_048_576] * 5
    assert any(c["service_children"] for c in r0_calls)

    # Disjoint windows around rank_0's first and last collective MUST exclude middle calls 1..8!
    w_first = (r0_calls[0]["entry"]["start_ns"], r0_calls[0]["completion"]["end_ns"])
    w_last = (r0_calls[9]["entry"]["start_ns"], r0_calls[9]["completion"]["end_ns"])
    disjoint = read_collective_readiness(
        a5_root, ranks=["rank_0"], source="db", windows=[w_first, w_last]
    )
    assert [c["op_id"] for c in disjoint["calls"]] == [
        r0_calls[0]["op_id"],
        r0_calls[9]["op_id"],
    ]

    # Public analyze_profile with two disjoint Windows must ALSO exclude the gap!
    c7 = analyze_profile(
        a5_root,
        ranks=["rank_0"],
        source="db",
        windows=[
            Window(start_ns=w_first[0], end_ns=w_first[1], step=1, label="step_1"),
            Window(start_ns=w_last[0], end_ns=w_last[1], step=2, label="step_2"),
        ],
    )
    assert [c["op_id"] for c in c7["collective_readiness"]["calls"]] == [
        r0_calls[0]["op_id"],
        r0_calls[9]["op_id"],
    ]

    # Selecting only the first nanosecond of call 1 must still query its full envelope
    # so its child tasks and wait intervals are never silently dropped!
    op1 = r0_calls[1]
    op1_start = op1["entry"]["start_ns"]
    clipped = read_collective_readiness(
        a5_root,
        ranks=["rank_0"],
        source="db",
        windows=[(op1_start, op1_start + 1)],
    )
    assert len(clipped["calls"]) == 1
    assert clipped["calls"][0]["op_id"] == op1["op_id"]
    assert clipped["calls"][0]["waits"] == op1["waits"]
    assert clipped["calls"][0]["service_children"] == op1["service_children"]


def test_readiness_uses_task_type_and_high_string_ids(tmp_path: Path) -> None:
    # STRING_IDS key 500_000 (> 200,000) must resolve cleanly without truncation!
    _create_readiness_db(tmp_path, 0, string_id_offset=500_000)
    report = read_collective_readiness(tmp_path, source="auto")
    assert report["schema"] == "mindie-profiler/collective-readiness/1"
    assert len(report["calls"]) == 1
    assert "unresolved_string_ids" not in report["limitations"]
    call = report["calls"][0]
    assert call["rank_id"] == "rank_0"
    assert call["operation"]["op_name"] == "hcom_allGather_AicpuKernel_612_0_1"
    assert call["operation"]["dtype"] == "BFP16"
    assert call["operation"]["typed_bytes"] == 10240
    assert call["observed_context"]["bound_task_global_id"] == "2"
    assert [(c["source_table"], c["name"]) for c in call["service_children"]] == [
        ("COMMUNICATION_TASK_INFO", "N/A"),
        ("COMMUNICATION_SCHEDULE_TASK_INFO", "HcclLaunchAicpuKernel"),
    ]
    assert call["waits"][0]["task_type_name"] == "NOTIFY WAIT"
    assert call["dependencies"][0]["task_type_name"] == "EVENT RECORD"
    assert call["dependencies"][0]["causal_status"] == "event_order_candidate"
    assert "ready_after_dependency_ns" not in call
    assert call["clock"]["cross_rank_aligned"] is False
    assert "cross_rank_clock_not_established" in call["unknowns"]
    assert all(item["causal_join"] is False for item in call["observed_overlaps"])


def test_repeated_global_task_id_marked_ambiguous_never_overwritten(tmp_path: Path) -> None:
    db_path = _create_readiness_db(tmp_path, 0)
    con = sqlite3.connect(db_path)
    con.execute("INSERT INTO STRING_IDS VALUES(99, 'MatMulBogus')")
    # Insert a second full-capture TASK occurrence reusing globalTaskId=2 at [30000, 40000]!
    con.execute("INSERT INTO TASK VALUES(30000, 40000, 0, 77, 2, 26, 2000, 5)")
    con.execute("INSERT INTO COMPUTE_TASK_INFO VALUES(2, 99, 99, 5)")
    con.commit()
    con.close()

    report = read_collective_readiness(tmp_path, start_ns=0, end_ns=5000)
    assert "ambiguous_global_task_id" in report["limitations"]
    call = report["calls"][0]
    assert call["service_children"] == []
    assert "native_child_global_task_ambiguous" in call["unknowns"]


def test_missing_causal_predecessor_and_multi_rank_ordinals(tmp_path: Path) -> None:
    single_root = tmp_path / "single"
    _create_readiness_db(single_root, 0, prior=False)
    call = read_collective_readiness(single_root)["calls"][0]
    assert call["dependencies"] == []
    assert "causal_predecessor_not_joined" in call["unknowns"]

    multi_root = tmp_path / "multi"
    _create_readiness_db(multi_root, 0, connection_base=10, op_count=3)
    _create_readiness_db(multi_root, 1, connection_base=90, op_count=3)
    report = read_collective_readiness(multi_root)
    assert len(report["calls"]) == 6
    for rank in ("rank_0", "rank_1"):
        calls = [item for item in report["calls"] if item["rank_id"] == rank]
        assert [item["call_ordinal"] for item in calls] == [0, 1, 2]

    # Windowed predecessor across boundary + disjoint second window predecessor in gap!
    win_report = read_collective_readiness(
        multi_root, ranks=["rank_0"], windows=[(950, 2500), (20950, 22500)]
    )
    assert [c["entry"]["start_ns"] for c in win_report["calls"]] == [1000, 21000]
    assert [c["dependencies"][0]["end_ns"] for c in win_report["calls"]] == [900, 20900]


def test_bounded_overlap_caps_and_deadline_enforcement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = _create_readiness_db(tmp_path, 0, op_count=1)
    con = sqlite3.connect(db_path)
    # 100 overlapping tasks on same (connectionId=2, deviceId=0) -> capped at MAX_OVERLAPS_PER_CALL=32!
    con.executemany(
        "INSERT INTO TASK VALUES(1000, 2000, 0, 2, ?, 26, ?, 5)",
        [(5000 + i, 5000 + i) for i in range(100)],
    )
    con.commit()
    con.close()

    capped = read_collective_readiness(tmp_path)
    assert len(capped["calls"][0]["observed_overlaps"]) == 32
    assert "overlap_detail_capped" in capped["limitations"]

    # Force expired monotonic clock after initial start -> raises ProfilerQueryError immediately!
    real_monotonic = time.monotonic
    calls_made = 0

    def fake_monotonic() -> float:
        nonlocal calls_made
        calls_made += 1
        return real_monotonic() + (1.0 if calls_made > 2 else 0.0)

    monkeypatch.setattr("mindie_profiler.collective_readiness.time.monotonic", fake_monotonic)
    monkeypatch.setattr("mindie_profiler.collective_readiness_db.time.monotonic", fake_monotonic)
    with pytest.raises(ProfilerQueryError, match="exceeded"):
        read_collective_readiness(tmp_path, timeout_s=0.1)


def test_csv_only_limitation_and_corrupt_db_raises(tmp_path: Path) -> None:
    csv_root = tmp_path / "csv_only" / "rank_0"
    csv_root.mkdir(parents=True)
    (csv_root / "kernel_details.csv").write_text(
        "Name,Type,Start Time(us),Duration(us)\nAdd,Add,1.0,2.0\n",
        encoding="utf-8",
    )
    csv_report = read_collective_readiness(tmp_path / "csv_only", source="csv")
    assert csv_report["calls"] == []
    assert "no_db_source" in csv_report["limitations"]

    bad_dir = tmp_path / "corrupt" / "rank_0" / "ASCEND_PROFILER_OUTPUT"
    bad_dir.mkdir(parents=True)
    bad_db = bad_dir / "ascend_pytorch_profiler_0.db"
    bad_db.write_bytes(b"not a valid sqlite3 header at all")
    with pytest.raises(ProfilerError):
        read_collective_readiness(bad_db, source="db")


def test_half_open_task_interval_index_and_busy_timeout_ceiling(tmp_path: Path) -> None:
    from mindie_profiler.collective_readiness_db import TaskGroupIndex
    from mindie_profiler.sql import open_readonly

    db_path = tmp_path / "intervals.db"
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE TASK(startNs INT, endNs INT, globalTaskId INT, streamId INT)"
    )
    con.executemany(
        "INSERT INTO TASK VALUES(?, ?, ?, 1)",
        [(0, 10, 1), (10, 20, 2), (20, 30, 3)],
    )
    con.commit()
    rows = con.execute("SELECT * FROM TASK").fetchall()
    con.close()

    index = TaskGroupIndex(rows)
    matched, capped = index.overlapping(10, 20)
    assert not capped
    assert [int(r["globalTaskId"]) for r in matched] == [2]

    from mindie_profiler.segment import infer_rank_id, infer_rank_index

    ro_floor = open_readonly(db_path, timeout_s=0.1, allow_pragma=True)
    try:
        assert ro_floor.execute("PRAGMA busy_timeout").fetchone()[0] == 3000
    finally:
        ro_floor.close()
    ro_ceil = open_readonly(db_path, timeout_s=30.0, allow_pragma=True)
    try:
        assert ro_ceil.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
    finally:
        ro_ceil.close()

    test_prefixed = tmp_path / "test_rank7" / "sub"
    test_prefixed.mkdir(parents=True)
    assert infer_rank_id(test_prefixed, stop_at=tmp_path / "test_rank7") == "rank_7"
    assert infer_rank_index(test_prefixed, stop_at=tmp_path / "test_rank7") == 7


def test_null_connection_id_child_dup_past_truncation_and_segment_tree_speed(
    tmp_path: Path,
) -> None:
    from mindie_profiler.collective_readiness_db import MAX_CHILDREN, TaskGroupIndex

    # 1. COMMUNICATION_OP with NULL connectionId is preserved honestly, never dropped.
    # 2. Duplicate child globalTaskId at row MAX_CHILDREN+1 (past truncation) is caught as ambiguous!
    db_path = _create_readiness_db(tmp_path, 0, op_count=1)
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO COMMUNICATION_OP VALUES(100, 3000, 4000, NULL, 32, 99, 11, 32, 5120, 0, 2, 3)"
    )
    con.executemany(
        "INSERT INTO COMMUNICATION_TASK_INFO VALUES(1000, 37, ?, 7)",
        [(10_000 + i,) for i in range(MAX_CHILDREN + 5)],
    )
    # Duplicate globalTaskId=2 placed past MAX_CHILDREN truncation boundary!
    con.execute("INSERT INTO COMMUNICATION_TASK_INFO VALUES(1005, 37, 2, 7)")
    con.commit()
    con.close()

    report = read_collective_readiness(tmp_path)
    assert len(report["calls"]) == 2
    assert "null_connection_id" in report["limitations"]
    assert "ambiguous_global_task_id" in report["limitations"]

    first_call, null_conn_call = report["calls"]
    assert "native_child_global_task_ambiguous" in first_call["unknowns"]
    assert first_call["service_children"] == []
    assert null_conn_call["connection_id"] is None
    assert "call_bound_task_unresolved" in null_conn_call["unknowns"]

    # 3. Segment max-tree keeps worst-case spanning query sub-50ms over 20,000 intervals.
    span_db = tmp_path / "span_20k.db"
    scon = sqlite3.connect(span_db)
    scon.row_factory = sqlite3.Row
    scon.execute("CREATE TABLE TASK(startNs INT, endNs INT, globalTaskId INT, streamId INT)")
    scon.executemany(
        "INSERT INTO TASK VALUES(?, ?, ?, 1)",
        [(i * 10, i * 10 + 5, i) for i in range(20_000)],
    )
    scon.commit()
    rows = scon.execute("SELECT * FROM TASK").fetchall()
    scon.close()

    index = TaskGroupIndex(rows)
    t0 = time.perf_counter()
    matched, capped = index.overlapping(0, 10**9, scan_limit=32)
    elapsed_s = time.perf_counter() - t0
    assert capped is True
    assert len(matched) == 32
    assert elapsed_s < 0.05


def test_report_wide_budget_chunk_pagination_capped_overlap_and_lock_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mindie_profiler.collective_readiness_db import (
        query_windowed_calls,
        query_windowed_tasks,
    )

    # 1. Report-wide MAX_TOTAL_CALLS bounds total retained calls across multiple ranks.
    multi = tmp_path / "multi_budget"
    _create_readiness_db(multi, 0, op_count=2)
    _create_readiness_db(multi, 1, op_count=2)
    monkeypatch.setattr("mindie_profiler.collective_readiness.MAX_TOTAL_CALLS", 3)
    capped_report = read_collective_readiness(multi)
    assert len(capped_report["calls"]) == 3
    assert "call_row_budget_reached" in capped_report["limitations"]
    monkeypatch.undo()

    # 2. 65 disjoint windows with spanning rows across chunk boundary return ALL unique rows.
    chunk_db = tmp_path / "chunk65.db"
    con = sqlite3.connect(chunk_db)
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE COMMUNICATION_OP(opId INT, startNs INT, endNs INT, connectionId INT, deviceId INT)"
    )
    con.execute(
        "CREATE TABLE TASK(startNs INT, endNs INT, connectionId INT, deviceId INT, "
        "globalTaskId INT, streamId INT, taskId INT, taskType INT)"
    )
    # Ops 1..3 span across window 0..64 so chunk 2 sees 3 duplicate spanning rows before op 5!
    ops_data = [
        (1, 5, 70_000, 1, 0),
        (2, 6, 70_000, 2, 0),
        (3, 7, 70_000, 3, 0),
        (4, 150, 250, 4, 0),
        (5, 64_100, 64_200, 5, 0),
    ]
    con.executemany("INSERT INTO COMMUNICATION_OP VALUES(?, ?, ?, ?, ?)", ops_data)
    con.executemany(
        "INSERT INTO TASK VALUES(?, ?, ?, 0, ?, 1, ?, 10)",
        [(s, e, cid, cid, cid) for cid, s, e, _, _ in ops_data],
    )
    con.commit()
    windows_65 = [(i * 1_000, i * 1_000 + 500) for i in range(65)]
    lims: set[str] = set()
    monkeypatch.setattr("mindie_profiler.collective_readiness_db.MAX_TASKS", 5)
    got_calls = query_windowed_calls(
        con,
        "chunk65.db",
        ["startNs", "endNs", "connectionId", "deviceId", "opId"],
        "opId",
        windows_65,
        lims,
        deadline=time.monotonic() + 10.0,
        timeout_s=10.0,
        max_calls=5,
    )
    got_tasks = query_windowed_tasks(
        con,
        "chunk65.db",
        ["0"],
        windows_65,
        lims,
        deadline=time.monotonic() + 10.0,
        timeout_s=10.0,
    )
    con.close()
    monkeypatch.undo()
    assert [int(r["opId"]) for r in got_calls] == [1, 2, 3, 4, 5]
    assert len(got_tasks) == 5
    assert lims == set()

    # 3. Capped overlap scan (>256 overlaps) leaves bound_task_global_id unresolved, never fabricated!
    cap_root = tmp_path / "cap_overlap"
    cap_db = _create_readiness_db(cap_root, 0, op_count=1)
    ccon = sqlite3.connect(cap_db)
    # First call in _create_readiness_db has startNs=1000, endNs=2000, deviceId=0, connectionId=2.
    # Add 260 non-enclosing overlapping tasks plus a second enclosing task at the end!
    ccon.executemany(
        "INSERT INTO TASK VALUES(1500, 1600, 0, 2, ?, 26, ?, 7)",
        [(5_000 + i, 5_000 + i) for i in range(260)],
    )
    ccon.execute("INSERT INTO TASK VALUES(900, 2100, 0, 2, 9999, 26, 9999, 7)")
    ccon.commit()
    ccon.close()
    cap_res = read_collective_readiness(cap_root)
    assert "overlap_scan_budget_reached" in cap_res["limitations"]
    assert cap_res["calls"][0]["observed_context"]["bound_task_global_id"] is None
    assert "call_bound_task_unresolved" in cap_res["calls"][0]["unknowns"]

    # 4. Sub-3s readiness timeout_s is rejected upfront rather than waiting 3,000ms on SQLite lock!
    with pytest.raises(ProfilerQueryError, match="minimum SQLite lock budget"):
        read_collective_readiness(cap_root, timeout_s=1.0)


def test_concurrent_same_connection_op_id_ownership_and_unkeyed_honesty(
    tmp_path: Path,
) -> None:
    meta = json.loads(REAL_A5_PROVENANCE.read_text(encoding="utf-8"))
    sql_bytes = (REAL_A5_FIXTURE / meta["ranks"]["rank_0"]["sql_relpath"]).read_bytes()
    overlap_db = (
        tmp_path
        / "a5_overlap"
        / "rank_0"
        / "ASCEND_PROFILER_OUTPUT"
        / "ascend_pytorch_profiler_0.db"
    )
    overlap_db.parent.mkdir(parents=True)
    con = sqlite3.connect(overlap_db)
    con.executescript(sql_bytes.decode("utf-8"))
    op0 = con.execute(
        "SELECT startNs, endNs, connectionId FROM COMMUNICATION_OP WHERE opId=0"
    ).fetchone()
    op1 = con.execute("SELECT startNs, endNs FROM COMMUNICATION_OP WHERE opId=1").fetchone()
    assert op0 is not None and op1 is not None
    shift_ns = (int(op0[0]) + 1_000) - int(op1[0])
    con.execute(
        "UPDATE COMMUNICATION_OP SET startNs = startNs + ?, endNs = endNs + ?, connectionId = ? "
        "WHERE opId = 1",
        (shift_ns, shift_ns, int(op0[2])),
    )
    con.execute(
        "UPDATE TASK SET startNs = startNs + ?, endNs = endNs + ?, connectionId = ? "
        "WHERE globalTaskId IN (29, 31)",
        (shift_ns, shift_ns, int(op0[2])),
    )
    con.commit()
    con.close()

    res = read_collective_readiness(tmp_path / "a5_overlap", source="db")
    calls_by_op = {c["op_id"]: c for c in res["calls"]}
    c0, c1 = calls_by_op["0"], calls_by_op["1"]
    assert [ch["global_task_id"] for ch in c0["service_children"]] == ["4", "6"]
    assert [w["global_task_id"] for w in c0["waits"]] == ["6"]
    assert [ch["global_task_id"] for ch in c1["service_children"]] == ["29", "31"]
    assert [w["global_task_id"] for w in c1["waits"]] == ["31"]
    assert {"4", "6", "29", "31"} <= {ov["global_task_id"] for ov in c0["observed_overlaps"]}
    assert all(ov["causal_join"] is False for ov in c0["observed_overlaps"])

    # Unkeyed shared connection (even when call 1 overlaps call 0 outside narrow user window)
    # must report shared_connection_without_op_id rather than falsely attributing children/waits.
    unkeyed_root = tmp_path / "unkeyed_shared"
    unkeyed_db = _create_readiness_db(unkeyed_root, 0, op_count=2)
    ucon = sqlite3.connect(unkeyed_db)
    ucon.execute(
        "UPDATE COMMUNICATION_OP SET startNs = 1500, endNs = 2500, connectionId = 2 WHERE opId = 1"
    )
    ucon.execute(
        "UPDATE TASK SET startNs = 1500, endNs = 2500, connectionId = 2 WHERE globalTaskId = 12"
    )
    ucon.commit()
    ucon.close()

    narrow = read_collective_readiness(unkeyed_root, windows=[(1000, 1100)])
    assert len(narrow["calls"]) == 1
    assert "shared_connection_without_op_id" in narrow["limitations"]
    assert narrow["calls"][0]["observed_context"]["bound_task_global_id"] is None
    assert narrow["calls"][0]["service_children"] == []
    assert narrow["calls"][0]["waits"] == []


def test_analyze_profile_readiness_timeout_budget_and_failure_degradation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    glm45_db = (
        Path(__file__).parent
        / "fixtures"
        / "profiler_core"
        / "real_glm45"
        / "rank_0"
        / "ASCEND_PROFILER_OUTPUT"
        / "ascend_pytorch_profiler_0.db"
    )
    ok_report = analyze_profile(glm45_db, full_range=True, query_timeout_s=3.0)
    assert ok_report["collective_readiness"]["schema"] == "mindie-profiler/collective-readiness/1"
    assert ok_report["collective_readiness"]["status"] != "error"

    def fail_readiness(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise ProfilerQueryError("simulated readiness lock timeout")

    monkeypatch.setattr(
        "mindie_profiler.collective_readiness.read_collective_readiness", fail_readiness
    )
    out_json = tmp_path / "degraded_report.json"
    degraded = analyze_profile(
        glm45_db, full_range=True, query_timeout_s=3.0, output=out_json
    )
    assert out_json.is_file()
    assert degraded["window_accounting"] and degraded["top_hotspot_kernels"]
    assert degraded["collective_readiness"]["status"] == "error"
    assert "simulated readiness lock timeout" in degraded["collective_readiness"]["error"]
    lim_codes = {item["code"] for item in degraded["limitations"]}
    assert "collective_readiness_failed" in lim_codes
    saved = json.loads(out_json.read_text(encoding="utf-8"))
    assert saved["collective_readiness"]["status"] == "error"


def test_truncated_tasks_suppress_false_binding_cross_conn_predecessor_and_fast_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from mindie_profiler.collective_readiness_db import index_call_ownership

    # 1. Task truncation (task_row_budget_reached) never turns ambiguity into a false unique binding.
    trunc_root = tmp_path / "trunc_ambig"
    trunc_db = _create_readiness_db(trunc_root, 0, prior=False, op_count=1)
    con = sqlite3.connect(trunc_db)
    con.execute("DELETE FROM TASK")
    con.executemany(
        "INSERT INTO TASK VALUES(0, 1, 0, 9, ?, 1, ?, 5)",
        [(100 + i, 100 + i) for i in range(4)],
    )
    con.executemany(
        "INSERT INTO TASK VALUES(1000, 2000, 0, 2, ?, ?, ?, 7)",
        [(20_000, 26, 100), (20_001, 27, 101)],
    )
    con.commit()
    con.close()

    monkeypatch.setattr("mindie_profiler.collective_readiness_db.MAX_TASKS", 5)
    win_res = read_collective_readiness(trunc_root, windows=[(1000, 2000)])
    full_res = read_collective_readiness(trunc_root)
    monkeypatch.undo()
    assert win_res["calls"][0]["observed_context"]["bound_task_global_id"] is None
    assert full_res["calls"][0]["observed_context"]["bound_task_global_id"] is None
    assert full_res["calls"][0]["service_children"] == []
    assert full_res["calls"][0]["waits"] == []
    assert "task_row_budget_reached" in full_res["limitations"]
    assert "task_row_budget_reached" in full_res["calls"][0]["unknowns"]

    # 2. Real GLM-4.5 Golden Capture resolves cross-connection same-stream predecessor (1055 -> 528),
    # and disjoint windows resolve closer gap predecessor across differing connectionIds.
    glm45_db = (
        Path(__file__).parent
        / "fixtures"
        / "profiler_core"
        / "real_glm45"
        / "rank_0"
        / "ASCEND_PROFILER_OUTPUT"
        / "ascend_pytorch_profiler_0.db"
    )
    glm_report = read_collective_readiness(glm45_db, source="db")
    call_528 = next(
        c
        for c in glm_report["calls"]
        if c["observed_context"]["bound_task_global_id"] == "528"
    )
    assert call_528["dependencies"][0]["global_task_id"] == "1055"
    assert call_528["dependencies"][0]["stream_id"] == "5"
    assert call_528["dependencies"][0]["end_ns"] == 1763456164890797580

    gap_root = tmp_path / "gap_pred"
    gap_db = _create_readiness_db(gap_root, 0, prior=False, op_count=1)
    gcon = sqlite3.connect(gap_db)
    gcon.execute("DELETE FROM TASK")
    gcon.execute("DELETE FROM COMMUNICATION_OP")
    gcon.execute("INSERT INTO TASK VALUES(120, 180, 0, 50, 1, 26, 1, 5)")
    gcon.execute("INSERT INTO TASK VALUES(500, 600, 0, 51, 2, 26, 2, 5)")
    gcon.execute("INSERT INTO TASK VALUES(1100, 1500, 0, 52, 3, 26, 3, 7)")
    gcon.execute(
        "INSERT INTO COMMUNICATION_OP VALUES(100, 1100, 1500, 52, 32, 1, 11, 32, 5120, 0, 2, 3)"
    )
    gcon.commit()
    gcon.close()
    gap_res = read_collective_readiness(gap_root, windows=[(100, 200), (1000, 2000)])
    assert gap_res["calls"][0]["dependencies"][0]["global_task_id"] == "2"
    assert gap_res["calls"][0]["dependencies"][0]["end_ns"] == 600

    # 3. 20,000 overlapping calls sweep in O(N log N) well within 3.2s and honor expired deadline.
    sweep_db = tmp_path / "sweep" / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db"
    sweep_db.parent.mkdir(parents=True)
    scon = sqlite3.connect(sweep_db)
    scon.row_factory = sqlite3.Row
    scon.execute(
        "CREATE TABLE COMMUNICATION_OP(startNs INT, endNs INT, connectionId INT, deviceId INT, opId INT)"
    )
    scon.executemany(
        "INSERT INTO COMMUNICATION_OP VALUES(?, 30000, 2, 0, ?)",
        [(i + 1, i + 1) for i in range(20_000)],
    )
    scon.commit()
    raw_calls = scon.execute("SELECT * FROM COMMUNICATION_OP").fetchall()
    scon.close()

    t0 = time.perf_counter()
    sweep_res = read_collective_readiness(tmp_path / "sweep", source="db", timeout_s=3.2)
    assert time.perf_counter() - t0 < 1.5
    assert len(sweep_res["calls"]) == 20_000

    with pytest.raises(ProfilerQueryError, match="exceeded"):
        index_call_ownership(
            raw_calls,
            has_op_id_col=True,
            task_by_global={},
            compute_raw={},
            comm_raw={},
            sched_raw={},
            ambiguous_globals=set(),
            limitations=set(),
            deadline=time.monotonic() - 0.01,
            timeout_s=3.2,
            db_label="sweep.db",
        )
