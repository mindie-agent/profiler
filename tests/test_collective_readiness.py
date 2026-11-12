"""C7 readiness uses real taskType/globalTask joins, never taskId strings."""
import sqlite3
from pathlib import Path

from mindie_profiler.collective_readiness import read_collective_readiness


def _db(root: Path, rank: int, *, prior=True):
    out = root / f"rank{rank}" / "profile" / "p" / "ASCEND_PROFILER_OUTPUT"
    out.mkdir(parents=True)
    path = out / f"ascend_pytorch_profiler_{rank}.db"
    db = sqlite3.connect(path)
    db.executescript("""
      CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
      CREATE TABLE TASK(startNs INTEGER,endNs INTEGER,deviceId INTEGER,
        connectionId INTEGER,globalTaskId INTEGER,streamId INTEGER,
        taskId INTEGER,taskType INTEGER);
      CREATE TABLE COMMUNICATION_OP(opName INTEGER,startNs INTEGER,endNs INTEGER,
        connectionId INTEGER,groupName INTEGER,opId INTEGER PRIMARY KEY,
        dataType INTEGER,algType INTEGER,count NUMERIC,deviceId INTEGER,
        rankSize INTEGER,transportType INTEGER);
      CREATE TABLE COMMUNICATION_TASK_INFO(timestampNs INTEGER,name INTEGER,
        globalTaskId INTEGER,taskType INTEGER);
      CREATE TABLE COMMUNICATION_SCHEDULE_TASK_INFO(globalTaskId INTEGER,
        name INTEGER,taskType INTEGER);
      CREATE TABLE ENUM_HCCL_DATA_TYPE(id INTEGER PRIMARY KEY,name TEXT);
      CREATE TABLE ENUM_HCCL_TRANSPORT_TYPE(id INTEGER PRIMARY KEY,name TEXT);
    """)
    db.executemany("INSERT INTO STRING_IDS(id,value) VALUES(?,?)", [
        (5, "EVENT RECORD"), (7, "NOTIFY WAIT"),
        (31, "hcom_allGather_AicpuKernel_612_0_1"), (32, "group_name_0"),
        (37, "N/A"), (36, "HcclLaunchAicpuKernel"),
    ])
    db.executemany("INSERT INTO ENUM_HCCL_DATA_TYPE VALUES(?,?)", [(11, "BFP16")])
    db.executemany("INSERT INTO ENUM_HCCL_TRANSPORT_TYPE VALUES(?,?)", [(3, "UB")])
    if prior:
        # taskId is deliberately a local ordinal, not a STRING_IDS key.
        db.execute("INSERT INTO TASK VALUES(100,900,0,2,1,26,999,5)")
    db.execute("INSERT INTO TASK VALUES(1000,2000,0,2,2,26,1000,7)")
    db.execute("INSERT INTO COMMUNICATION_OP VALUES(31,1000,2000,2,32,0,11,32,5120,0,2,3)")
    db.execute("INSERT INTO COMMUNICATION_TASK_INFO VALUES(1000,37,2,7)")
    db.execute("INSERT INTO COMMUNICATION_SCHEDULE_TASK_INFO VALUES(2,36,37)")
    db.commit(); db.close()
    return path


def test_readiness_uses_task_type_and_global_join(tmp_path):
    _db(tmp_path, 0)
    report = read_collective_readiness(tmp_path, source="auto")
    assert report["schema"] == "mindie-profiler/collective-readiness/1"
    call = report["calls"][0]
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
    # An overlapping ordinal with no join is context, not a service child.
    assert all(item["causal_join"] is False for item in call["observed_overlaps"])


def test_missing_causal_predecessor_remains_unknown(tmp_path):
    _db(tmp_path, 0, prior=False)
    call = read_collective_readiness(tmp_path)["calls"][0]
    assert call["dependencies"] == []
    assert "causal_predecessor_not_joined" in call["unknowns"]
