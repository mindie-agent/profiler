"""Two-rank HCCL relational DB join, alias union deduplication, and CSV honesty.

[Role]
  Verify ``discover_rank_sources`` and ``analyze_profile`` resolve nested
  ``rank0/profile/...`` directories, join ``COMPUTE_TASK_INFO`` and
  ``COMMUNICATION_OP`` presentations through ``TASK.connectionId`` /
  ``globalTaskId``, deduplicate ``native_calls`` via true interval union even
  under ``mapping_limit`` truncation, and leave CSV-only or ``connectionId``-less
  schemas explicitly unresolved.

[Invariants]
  * Raw events remain visible in ``event_mappings`` while ``native_calls``
    charges each physical call once per rank using interval union.
  * ``mapping_limit`` bounds retained ``event_mappings`` samples only; full
    window ``native_calls`` and ``native_call_identity_counts`` are never truncated.
  * CSV-only inputs and minimal DBs lacking ``TASK.connectionId`` report honest
    unresolved counters without SQL errors or fabricated empty keys.

[Timeouts & Locks]
  Reads the retained ``tests/fixtures/profiler_core/real_glm45`` Golden Capture
  plus targeted schema/deadline probes in ``tmp_path``; zero devices or network.

[Side-Effect Policy]
  Reads ``tests/fixtures/profiler_core/real_glm45`` read-only; writes only inside
  pytest ``tmp_path``.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler import segment
from mindie_profiler.analyze import analyze_profile
from mindie_profiler.accounting import account_window
from mindie_profiler.events import (
    Event,
    Observation,
    ProfilerQueryError,
    QueryStats,
    SourceRef,
    Window,
)
from mindie_profiler.sources_db import DbSource, probe_db
from mindie_profiler.structure_mapping import StructureMapper

REAL_GLM45_ROOT = Path(__file__).parent / "fixtures" / "profiler_core" / "real_glm45"

_RANK_SPANS = {
    0: (1_000_000, 57_348_811),
    1: (2_000_000, 2_013_445),
}


def _write_two_rank_packet(root: Path, *, with_connection_id: bool = True) -> Path:
    """Deliberate schema/discovery probe for colliding enum IDs and missing connectionId."""
    csv_header = (
        "Device_id,Model ID,Task ID,Stream ID,Name,Type,OP State,Accelerator Core,"
        "Start Time(us),Duration(us),Wait Time(us),Block Num,Mix Block Num,"
        "Input Shapes,Input Data Types,Input Formats,Output Shapes,Output Data Types,Output Formats\n"
    )
    for rank, (start_ns, end_ns) in _RANK_SPANS.items():
        out = root / f"rank{rank}" / "profile" / f"run_{rank}" / "ASCEND_PROFILER_OUTPUT"
        out.mkdir(parents=True, exist_ok=True)
        dur_us = (end_ns - start_ns) / 1000.0
        start_us = start_ns / 1000.0
        (out / "kernel_details.csv").write_text(
            csv_header
            + f"{rank},1,17,26,AivKernel,AivKernel,dynamic,MIX_AIC,{start_us:.3f},{dur_us:.3f},0.0,8,8,5120,DT_BF16,ND,5120,DT_BF16,ND\n"
            + f"{rank},1,17,26,hcom_allGather__612_0_1,hcom_allGather__612_0_1,dynamic,HCCL,{start_us:.3f},{dur_us:.3f},0.0,0,0,5120,DT_BF16,ND,10240,DT_BF16,ND\n",
            encoding="utf-8",
        )
        db = sqlite3.connect(out / f"ascend_pytorch_profiler_{rank}.db")
        conn_col_task = ", connectionId INTEGER" if with_connection_id else ""
        conn_col_comm = ", connectionId INTEGER" if with_connection_id else ""
        db.executescript(
            f"""
            CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
            CREATE TABLE TASK(
                globalTaskId INTEGER, startNs INTEGER, endNs INTEGER,
                deviceId INTEGER, streamId INTEGER, taskId INTEGER,
                modelId INTEGER, contextId INTEGER, taskType INTEGER{conn_col_task}
            );
            CREATE TABLE COMPUTE_TASK_INFO(
                name INTEGER, globalTaskId INTEGER, opType INTEGER, taskType INTEGER,
                blockDim INTEGER, mixBlockDim INTEGER, waitNs INTEGER,
                inputShapes INTEGER, inputDataTypes INTEGER, inputFormats INTEGER,
                outputShapes INTEGER, outputDataTypes INTEGER, outputFormats INTEGER
            );
            CREATE TABLE COMMUNICATION_OP(
                opName INTEGER, opType INTEGER, startNs INTEGER, endNs INTEGER,
                deviceId INTEGER, groupName INTEGER, dataType INTEGER,
                algType INTEGER, count NUMERIC, rankSize INTEGER{conn_col_comm}
            );
            CREATE TABLE ENUM_HCCL_DATA_TYPE(id INTEGER PRIMARY KEY, name TEXT);
            CREATE TABLE ENUM_HCCL_ALGO_TYPE(id INTEGER PRIMARY KEY, name TEXT);
            """
        )
        db.executemany(
            "INSERT INTO STRING_IDS(id, value) VALUES(?, ?)",
            [
                (1, "AivKernel"),
                (2, "MIX_AIC"),
                (3, "hcom_allGather__612_0_1"),
                (4, "group_tp_0"),
                (5, "5120"),
                (6, "10240"),
                (7, "DT_BF16"),
                (8, "ND"),
                (32, "CollidingStringId32MustNotOverrideAlgoEnum"),
            ],
        )
        db.execute("INSERT INTO ENUM_HCCL_DATA_TYPE VALUES(11, 'BFP16')")
        db.execute("INSERT INTO ENUM_HCCL_ALGO_TYPE VALUES(32, 'AlgType::NHR')")
        if with_connection_id:
            db.execute(
                "INSERT INTO TASK VALUES(5, ?, ?, ?, 26, 17, 1, 4294967295, 2, 2)",
                (start_ns, end_ns, rank),
            )
            db.execute(
                "INSERT INTO COMMUNICATION_OP VALUES(3, 3, ?, ?, ?, 4, 11, 32, 5120, 2, 2)",
                (start_ns, end_ns, rank),
            )
        else:
            db.execute(
                "INSERT INTO TASK VALUES(5, ?, ?, ?, 26, 17, 1, 4294967295, 2)",
                (start_ns, end_ns, rank),
            )
            db.execute(
                "INSERT INTO COMMUNICATION_OP VALUES(3, 3, ?, ?, ?, 4, 11, 32, 5120, 2)",
                (start_ns, end_ns, rank),
            )
        db.execute(
            "INSERT INTO COMPUTE_TASK_INFO VALUES(1, 5, 1, 2, 8, 8, 0, 5, 7, 8, 5, 7, 8)"
        )
        db.commit()
        db.close()
    return root


def _hccl_structure() -> dict:
    from mindie_sim.prediction import hccl_graph, native_binding
    from mindie_sim.schema import operators as schema
    from mindie_sim import structure as structure_module

    aliases = [
        {
            "rank_id": f"rank_{rank}",
            "logical_rank": rank,
            "global_task_id": "5",
            "stream_id": "26",
            "task_id": "17",
            "connection_id": "2",
            "device_id": str(rank),
            "start_ns": str(start_ns),
            "end_ns": str(end_ns),
            "compute_name": "AivKernel",
            "comm_name": "hcom_allGather__612_0_1",
        }
        for rank, (start_ns, end_ns) in _RANK_SPANS.items()
    ]
    op = schema.OpSpec(
        "s0.l0.tp_all_gather",
        "allgather",
        "decode",
        0,
        0,
        (),
        (5120,),
        (5120,),
        (5120,),
        (5120,),
        link_bytes=10240,
        dtype="bf16",
        metadata=(("group_axis", "tp"), ("collective", "allgather")),
    )
    lowered = list(hccl_graph.lower((op,), SimpleNamespace(kernels={}), "bf16"))
    lowered[0] = native_binding.declare_native_call(
        lowered[0],
        api={"namespace": "hccl", "entry": "HcclAllGather"},
        source={"path": "hccl/all_gather.cc", "sha256": "a" * 64},
        kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
        observed_aliases=aliases,
    )
    replicas = {0: tuple(lowered), 1: tuple(lowered)}
    return structure_module.export_op_structure(
        replicas, model={}, execution={"phase": "decode"}, native_evidence=True
    )


def _bindings(structure: dict) -> dict:
    return {
        "schema_version": "mindie-profile-bindings/1",
        "graph_id": structure["graph_id"],
        "rank_replicas": {"rank_0": "0", "rank_1": "1"},
    }


def test_whole_directory_discovery_normalizes_nested_rank_names(tmp_path: Path) -> None:
    packet = _write_two_rank_packet(tmp_path / "out")
    sources = segment.discover_rank_sources(packet, source="auto")
    assert [(item.rank_id, item.rank_index) for item in sources] == [
        ("rank_0", 0),
        ("rank_1", 1),
    ]
    assert {item.kind for item in sources} == {"db"}

    # Passing --root .../rank7 with nested anonymous subdir preserves rank_7, while
    # external ancestor /rank99 above an anonymous direct file/dir never contaminates!
    external = tmp_path / "rank99"
    anon = external / "anon_bundle"
    anon.mkdir(parents=True)
    csv_file = anon / "kernel_details.csv"
    csv_file.write_text("Name,Type,Start Time(us),Duration(us)\nAdd,Add,1.0,2.0\n", encoding="utf-8")
    assert segment.discover_rank_sources(anon, source="csv")[0].rank_id == "anon_bundle"
    assert segment.discover_rank_sources(csv_file, source="csv")[0].rank_id == "anon_bundle"

    rank7_root = external / "rank7"
    leaf = rank7_root / "sub"
    leaf.mkdir(parents=True)
    (leaf / "kernel_details.csv").write_text(
        "Name,Type,Start Time(us),Duration(us)\nAdd,Add,1.0,2.0\n", encoding="utf-8"
    )
    discovered_r7 = segment.discover_rank_sources(rank7_root, source="csv")[0]
    assert (discovered_r7.rank_id, discovered_r7.rank_index) == ("rank_7", 7)


def test_public_analyze_profile_links_two_ranks_and_survives_mapping_limit(
    tmp_path: Path,
) -> None:
    packet = _write_two_rank_packet(tmp_path / "out")
    structure = _hccl_structure()
    report = analyze_profile(
        packet,
        source="auto",
        structure=structure,
        structure_bindings=_bindings(structure),
        full_range=True,
        hash_sources=False,
        mapping_limit=50,
    )
    mapping = report["structure_mapping"]
    assert mapping["native_call_count"] == 2
    assert mapping["native_call_identity_counts"] == {"observed_raw_identity": 4}
    assert {call["presentation_count"] for call in mapping["native_calls"]} == {2}
    assert {call["charge"] for call in mapping["native_calls"]} == {"call"}
    activities = {call["rank_id"]: call["activity_ns"] for call in mapping["native_calls"]}
    assert activities == {"rank_0": 56_348_811, "rank_1": 13_445}

    by_rank: dict[str, dict[str, dict]] = {}
    for row in mapping["event_mappings"]:
        assert row["native_call_identity"] == "observed_raw_identity"
        assert row["native_call_occurrence"]["charge"] == "call"
        by_rank.setdefault(row["rank_id"], {})[row["kernel_name"]] = row["locator"]
    for rank in ("rank_0", "rank_1"):
        compute = by_rank[rank]["AivKernel"]
        comm = by_rank[rank]["hcom_allGather__612_0_1"]
        assert compute["connection_id"] == comm["connection_id"] == "2"
        assert str(compute["task_global_id"]) == str(comm["global_task_id"]) == "5"
        assert compute["stream_id"] == comm["stream_id"] == "26"
        assert compute["task_id"] == comm["task_id"] == "17"
        assert comm["algorithm"] == "AlgType::NHR"
        assert comm["count"] == 5120

    # mapping_limit=1 caps retained event_mappings per window, never native_calls!
    capped = analyze_profile(
        packet,
        source="auto",
        structure=structure,
        structure_bindings=_bindings(structure),
        full_range=True,
        hash_sources=False,
        mapping_limit=1,
    )["structure_mapping"]
    assert len(capped["event_mappings"]) == 1  # mapper-wide sample cap = 1 row total
    assert capped["native_call_count"] == 2
    assert capped["native_call_identity_counts"] == {"observed_raw_identity": 4}


def test_csv_only_and_connectionless_db_stay_honestly_unresolved(tmp_path: Path) -> None:
    packet = _write_two_rank_packet(tmp_path / "full")
    structure = _hccl_structure()
    csv_mapping = analyze_profile(
        packet,
        source="csv",
        structure=structure,
        structure_bindings=_bindings(structure),
        full_range=True,
        hash_sources=False,
        mapping_limit=50,
    )["structure_mapping"]
    assert csv_mapping["native_call_count"] == 0
    assert csv_mapping["native_call_identity_counts"] == {
        "unresolved_alias_without_relational_keys": 4
    }

    no_conn = _write_two_rank_packet(tmp_path / "no_conn", with_connection_id=False)
    db_report = analyze_profile(
        no_conn,
        source="db",
        structure=structure,
        structure_bindings=_bindings(structure),
        full_range=True,
        hash_sources=False,
        mapping_limit=50,
    )
    assert db_report["structure_mapping"]["native_call_count"] == 0
    assert db_report["structure_mapping"]["native_call_identity_counts"] == {
        "unresolved_alias_without_relational_keys": 4
    }


def test_alias_presentations_use_interval_union_not_bounding_span() -> None:
    from mindie_profiler.structure_native_calls import (
        NativeCallGlobalTracker,
        NativeCallWindowTracker,
    )

    start_ns, end_ns = _RANK_SPANS[0]
    locator = {"global_task_id": "5", "connection_id": "2", "source": "/prepare-only"}
    first = Event(
        rank_id="rank_0",
        rank_index=0,
        name="AivKernel",
        op_type="AivKernel",
        task_type="MIX_AIC",
        core="MIX_AIC",
        stream_id="26",
        task_id="17",
        device_id="0",
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind="db",
        table="COMPUTE_TASK_INFO",
        locator=locator,
    )
    second = Event(
        rank_id="rank_0",
        rank_index=0,
        name="hcom_allGather__612_0_1",
        op_type="hcom_allGather__612_0_1",
        task_type="COMMUNICATION",
        core="COMMUNICATION",
        stream_id="26",
        task_id="17",
        device_id="0",
        start_ns=start_ns,
        end_ns=end_ns,
        source_kind="db",
        table="COMMUNICATION_OP",
        locator=locator,
    )
    correspondence = {
        "basis": "observed_hccl_alias_same_call",
        "raw_identity": {"rank_id": "rank_0", "global_task_id": "5"},
        "native_call": {
            "call_id": "c" * 64,
            "timing_owner": {"op_id": "s0.l0.tp_all_gather"},
        },
    }
    tracker = NativeCallWindowTracker(
        NativeCallGlobalTracker(), {"AivKernel", "hcom_allGather__612_0_1"}
    )
    # Disjoint sub-intervals (100..200) and (300..500): union is 300 ns, NOT span 400 ns.
    tracker.observe(first, (100, 200), correspondence)
    tracker.observe(second, (300, 500), correspondence)
    calls = tracker.finish()
    assert len(calls) == 1
    assert calls[0]["activity_ns"] == 300
    assert calls[0]["presentation_count"] == 2


def test_real_glm45_golden_capture_hccl_alias_deduplicates_interval_union() -> None:
    """Acceptance happy path on retained real GLM-4.5 hardware capture SQLite DB."""
    from mindie_sim.prediction import hccl_graph, native_binding
    from mindie_sim.schema import operators as schema
    from mindie_sim import structure as structure_module

    real_start = 1763456164890902342
    real_end = 1763456164890910282
    op = schema.OpSpec(
        "s0.l0.tp_all_reduce",
        "allreduce",
        "decode",
        0,
        0,
        (),
        (3,),
        (3,),
        (3,),
        (3,),
        (3,),
        link_bytes=12,
        dtype="fp32",
        metadata=(("group_axis", "tp"), ("collective", "allreduce")),
    )
    lowered = list(hccl_graph.lower((op,), SimpleNamespace(kernels={}), "fp32"))
    lowered[0] = native_binding.declare_native_call(
        lowered[0],
        api={"namespace": "hccl", "entry": "HcclAllReduce"},
        source={"path": "hccl/all_reduce.cc", "sha256": "b" * 64},
        kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
        observed_aliases=[
            {
                "rank_id": "rank_0",
                "logical_rank": 0,
                "global_task_id": "528",
                "stream_id": "5",
                "task_id": "62134",
                "connection_id": "20633",
                "device_id": "0",
                "start_ns": str(real_start),
                "end_ns": str(real_end),
                "compute_name": "AivKernel",
                "comm_name": "hcom_allReduce__042_0_1",
            }
        ],
    )
    structure = structure_module.export_op_structure(
        {0: tuple(lowered)}, model={}, execution={"phase": "decode"}, native_evidence=True
    )
    bindings = {
        "schema_version": "mindie-profile-bindings/1",
        "graph_id": structure["graph_id"],
        "rank_replicas": {"rank_0": "0"},
    }

    report = analyze_profile(
        REAL_GLM45_ROOT,
        ranks=["rank_0"],
        source="db",
        structure=structure,
        structure_bindings=bindings,
        windows=[Window(start_ns=real_start - 1_000, end_ns=real_end + 1_000, step=1)],
        hash_sources=False,
        mapping_limit=1,
    )
    mapping = report["structure_mapping"]
    assert len(mapping["event_mappings"]) == 1
    assert mapping["native_call_count"] == 1
    assert mapping["native_call_identity_counts"] == {"observed_raw_identity": 2}
    call = mapping["native_calls"][0]
    assert call["presentation_count"] == 2
    assert call["activity_ns"] == real_end - real_start == 7_940


def test_reused_connection_id_join_is_sublinear_and_enforces_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Deliberate scalability/deadline probe: 4,000 calls sharing one connectionId."""
    db_path = tmp_path / "reused_conn.db"
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(
            globalTaskId INTEGER, startNs INTEGER, endNs INTEGER,
            deviceId INTEGER, streamId INTEGER, taskId INTEGER,
            modelId INTEGER, contextId INTEGER, taskType INTEGER, connectionId INTEGER
        );
        CREATE TABLE COMPUTE_TASK_INFO(
            name INTEGER, globalTaskId INTEGER, opType INTEGER, taskType INTEGER
        );
        CREATE TABLE COMMUNICATION_OP(
            opName INTEGER, opType INTEGER, startNs INTEGER, endNs INTEGER,
            deviceId INTEGER, connectionId INTEGER
        );
        INSERT INTO STRING_IDS VALUES(1, 'hcom_allReduce_'), (2, 'COMMUNICATION');
        """
    )
    n_rows = 4_000
    con.executemany(
        "INSERT INTO TASK VALUES(?, ?, ?, 0, 5, ?, 1, 1, 2, 77)",
        [(i + 1, i * 1_000 + 100, i * 1_000 + 900, i + 1) for i in range(n_rows)],
    )
    con.executemany(
        "INSERT INTO COMMUNICATION_OP VALUES(1, 1, ?, ?, 0, 77)",
        [(i * 1_000 + 100, i * 1_000 + 900) for i in range(n_rows)],
    )
    con.commit()
    con.close()

    source = DbSource(probe_db(db_path))
    win = Window(start_ns=0, end_ns=n_rows * 1_000 + 1_000, step=1)
    t0 = time.perf_counter()
    events, _ = source.iter_window(win, max_rows=20_000, timeout_s=5.0)
    elapsed_s = time.perf_counter() - t0
    assert len(events) == n_rows
    assert all(ev.locator["task_join_status"] == "connection_and_interval" for ev in events)
    assert elapsed_s < 0.5

    real_perf = time.perf_counter
    tick = 0

    def expired_perf() -> float:
        nonlocal tick
        tick += 1
        return real_perf() + (1.0 if tick > 4 else 0.0)

    monkeypatch.setattr("mindie_profiler.sources_db_comm.time.perf_counter", expired_perf)
    with pytest.raises(ProfilerQueryError, match="exceeded"):
        source.iter_window(win, max_rows=20_000, timeout_s=0.1)


def test_competing_comm_ops_on_same_task_never_collapse_into_one_native_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import copy
    import shutil
    from mindie_sim import structure as structure_module
    from mindie_sim.prediction import hccl_graph, native_binding
    from mindie_sim.schema import operators as schema
    from mindie_profiler.collective_readiness import read_collective_readiness

    real_db = REAL_GLM45_ROOT / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db"
    db_copy = tmp_path / "glm_dup" / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db"
    db_copy.parent.mkdir(parents=True)
    shutil.copy2(real_db, db_copy)

    con = sqlite3.connect(db_copy)
    row78 = con.execute(
        "SELECT opName, startNs, endNs, connectionId, groupName, opId, relay, retry, "
        "dataType, algType, count, opType, deviceId, waitNs, opConnectionId "
        "FROM COMMUNICATION_OP WHERE opId = 78"
    ).fetchone()
    assert row78 is not None and len(row78) == 15
    real_start, real_end = int(row78[1]), int(row78[2])
    con.close()

    op = schema.OpSpec(
        "s0.l0.tp_all_reduce", "allreduce", "decode", 0, 0, (),
        (3,), (3,), (3,), (3,), (3,), link_bytes=12, dtype="fp32",
        metadata=(("group_axis", "tp"), ("collective", "allreduce")),
    )
    lowered = list(hccl_graph.lower((op,), SimpleNamespace(kernels={}), "fp32"))
    lowered[0] = native_binding.declare_native_call(
        lowered[0],
        api={"namespace": "hccl", "entry": "HcclAllReduce"},
        source={"path": "hccl/all_reduce.cc", "sha256": "b" * 64},
        kernels=[{"name": "AivKernel", "role": "aiv", "evidence": "source_declared"}],
        observed_aliases=[
            {
                "rank_id": "rank_0", "logical_rank": 0, "global_task_id": "528",
                "stream_id": "5", "task_id": "62134", "connection_id": "20633",
                "device_id": "0", "start_ns": str(real_start), "end_ns": str(real_end),
                "compute_name": "AivKernel", "comm_name": "hcom_allReduce__042_0_1",
            }
        ],
    )
    structure = structure_module.export_op_structure(
        {0: tuple(lowered)}, model={}, execution={"phase": "decode"}, native_evidence=True
    )
    bindings = {
        "schema_version": "mindie-profile-bindings/1",
        "graph_id": structure["graph_id"],
        "rank_replicas": {"rank_0": "0"},
    }
    win = Window(start_ns=real_start - 1_000, end_ns=real_end + 1_000, step=1)

    # 1. Positive control BEFORE inserting competing opId=79: binds 1 native call (2 presentations).
    pos = analyze_profile(
        tmp_path / "glm_dup", ranks=["rank_0"], source="db",
        structure=structure, structure_bindings=bindings, windows=[win], hash_sources=False,
    )["structure_mapping"]
    assert pos["native_call_count"] == 1
    assert pos["native_calls"][0]["presentation_count"] == 2
    assert pos["native_calls"][0]["activity_ns"] == real_end - real_start == 7_940

    # 2. Insert competing opId=79 on connectionId=20633: invalidates BOTH comm AND AivKernel!
    con = sqlite3.connect(db_copy)
    row79 = list(row78)
    row79[5] = 79
    row79[10] = 6
    con.execute(
        f"INSERT INTO COMMUNICATION_OP VALUES ({','.join('?' for _ in row79)})", row79
    )
    con.commit()
    con.close()

    events, _ = DbSource(probe_db(db_copy)).iter_window(win)
    comm_events = [ev for ev in events if ev.table == "COMMUNICATION_OP"]
    aiv_events = [ev for ev in events if ev.name == "AivKernel"]
    assert len(comm_events) == 2 and len(aiv_events) == 1
    assert all(ev.locator["global_task_id"] is None for ev in comm_events)
    assert aiv_events[0].locator.get("task_join_status") == "unresolved_contested_comm_task"

    neg = analyze_profile(
        tmp_path / "glm_dup", ranks=["rank_0"], source="db",
        structure=structure, structure_bindings=bindings, windows=[win], hash_sources=False,
    )["structure_mapping"]
    assert neg["native_call_count"] == 0
    assert neg["native_calls"] == []
    assert neg["native_call_identity_counts"] == {"conflicted_comm_op_claim": 3}
    for row in neg["event_mappings"]:
        corr = row.get("implementation_correspondence") or {}
        assert corr.get("observed_proof") is not True
        assert corr.get("occurrence_binding_implied") is not True

    # 3. Pre-built Event parity between list (streamed=False) and iterator (streamed=True).
    aiv_pre = Event(
        rank_id="rank_0", rank_index=0, name="AivKernel", op_type="AivKernel",
        task_type="MIX_AIC", core="MIX_AIC", stream_id="5", task_id="62134", device_id="0",
        start_ns=real_start, end_ns=real_end, source_kind="db", table="COMPUTE_TASK_INFO",
        locator={"task_global_id": "528", "connection_id": "20633"},
    )
    comm_pre = [
        Event(
            rank_id="rank_0", rank_index=0, name="hcom_allReduce__042_0_1",
            op_type="hcom_allReduce_", task_type="COMMUNICATION", core="COMMUNICATION",
            stream_id="5", task_id="62134", device_id="0", start_ns=real_start, end_ns=real_end,
            source_kind="db", table="COMMUNICATION_OP",
            locator={"op_id": oid, "global_task_id": "528", "connection_id": "20633", "count": cnt},
        )
        for oid, cnt in (("78", 3), ("79", 6))
    ]
    for batch, expected_claims in ((comm_pre, 2), ([aiv_pre, *comm_pre], 3)):
        obs = Observation(
            "rank_0", 0, win, account_window(batch, win), batch,
            SourceRef("rank_0", 0, "db", "/mem", "mem", None, 1, "v1", "db", 1),
            QueryStats("rank_0", "1"),
        )
        results = []
        for streamed in (False, True):
            mapper = StructureMapper(copy.deepcopy(structure), bindings=bindings)
            wres = mapper.map_window(obs, events=iter(batch)) if streamed else mapper.map_window(obs)
            assert wres["native_calls"] == []
            assert dict(mapper.native_tracker.identity_counts) == {
                "conflicted_comm_op_claim": expected_claims
            }
            for srow in mapper.sample:
                scorr = srow.get("implementation_correspondence") or {}
                assert scorr.get("observed_proof") is not True
                assert scorr.get("occurrence_binding_implied") is not True
                assert srow["native_call_occurrence"] is None
            for op_row in wres["operators"]:
                ocorr = op_row.get("implementation_correspondence") or {}
                assert ocorr.get("observed_proof") is not True
                assert ocorr.get("occurrence_binding_implied") is not True
            results.append((dict(mapper.native_tracker.identity_counts), [r["implementation_correspondence"] for r in mapper.sample]))
        assert results[0] == results[1]

    # 4. Child ownership query enforces max_rows budget without reading unbounded rows.
    child_db = tmp_path / "child_budget.db"
    ccon = sqlite3.connect(child_db)
    ccon.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(
            globalTaskId INT, startNs INT, endNs INT, deviceId INT,
            streamId INT, taskId INT, modelId INT, contextId INT, taskType INT, connectionId INT
        );
        CREATE TABLE COMPUTE_TASK_INFO(name INT, globalTaskId INT, opType INT, taskType INT);
        CREATE TABLE COMMUNICATION_OP(
            opName INT, opType INT, startNs INT, endNs INT, deviceId INT, connectionId INT, opId INT
        );
        CREATE TABLE COMMUNICATION_TASK_INFO(globalTaskId INT, opId INT);
        INSERT INTO STRING_IDS VALUES(1, 'hcom_allReduce_');
        INSERT INTO TASK VALUES(5, 100, 200, 0, 1, 1, 1, 1, 1, 9);
        INSERT INTO COMMUNICATION_OP VALUES(1, 1, 100, 200, 0, 9, 1);
        """
    )
    ccon.executemany("INSERT INTO COMMUNICATION_TASK_INFO VALUES(5, 1)", [() for _ in range(500)])
    ccon.commit()
    ccon.close()
    with pytest.raises(ProfilerQueryError, match="comm child join.*exceeded row budget 4"):
        DbSource(probe_db(child_db)).iter_window(Window(0, 500, step=1), max_rows=4)

    # 5. Readiness sequential non-overlapping collectives never share one unowned TASK,
    #    and fetch_rows issues zero per-query PRAGMA busy_timeout statements (Iron Rule 1).
    seq_db = tmp_path / "seq" / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db"
    seq_db.parent.mkdir(parents=True)
    scon = sqlite3.connect(seq_db)
    scon.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(
            globalTaskId INT, startNs INT, endNs INT, deviceId INT,
            streamId INT, taskId INT, taskType INT, connectionId INT
        );
        CREATE TABLE COMPUTE_TASK_INFO(globalTaskId INT, name INT, opType INT, taskType INT);
        CREATE TABLE COMMUNICATION_OP(
            opName INT, startNs INT, endNs INT, connectionId INT, deviceId INT, opId INT
        );
        INSERT INTO STRING_IDS VALUES(1, 'AivKernel'), (2, 'MIX_AIC'), (3, 'hcom_allReduce_');
        INSERT INTO TASK VALUES(1, 0, 100, 0, 5, 17, 2, 77);
        INSERT INTO COMPUTE_TASK_INFO VALUES(1, 1, 1, 2);
        INSERT INTO COMMUNICATION_OP VALUES(3, 10, 20, 77, 0, 10), (3, 50, 60, 77, 0, 11);
        """
    )
    scon.commit()
    scon.close()

    from mindie_profiler import sql as sql_mod

    real_open = sql_mod.open_readonly
    post_open_sql: list[str] = []

    def traced_open(*args, **kwargs):
        conn = real_open(*args, **kwargs)
        conn.set_trace_callback(post_open_sql.append)
        return conn

    monkeypatch.setattr("mindie_profiler.collective_readiness.open_readonly", traced_open)
    for r_windows in (None, [(10, 20)]):
        post_open_sql.clear()
        res = read_collective_readiness(tmp_path / "seq", source="db", windows=r_windows)
        assert not any("busy_timeout" in stmt.lower() for stmt in post_open_sql)
        assert "shared_connection_without_op_id" in res["limitations"]
        for rcall in res["calls"]:
            assert rcall["observed_context"]["bound_task_global_id"] is None
            assert rcall["service_children"] == []
    monkeypatch.undo()

    # 6. DbSource reuses TASK occurrence cache across chunks/windows; readiness distinguishes all_to_allv.
    cache_db = tmp_path / "cache" / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db"
    cache_db.parent.mkdir(parents=True)
    kcon = sqlite3.connect(cache_db)
    kcon.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(
            globalTaskId INT, startNs INT, endNs INT, deviceId INT,
            streamId INT, taskId INT, taskType INT, connectionId INT, modelId INT, contextId INT
        );
        CREATE INDEX TaskIndex ON TASK(startNs, globalTaskId);
        CREATE TABLE COMPUTE_TASK_INFO(globalTaskId INT PRIMARY KEY, name INT, opType INT, taskType INT);
        CREATE TABLE COMMUNICATION_OP(
            opName INT, opType INT, startNs INT, endNs INT, deviceId INT,
            connectionId INT, groupName INT, opId INT PRIMARY KEY
        );
        INSERT INTO STRING_IDS VALUES
            (1, 'hcom_allToAllV_AicpuKernel_0'), (2, 'hcom_allToAll__0'),
            (3, 'hcom_allToAll_vllm_0'), (4, 'ep_group'), (5, 'AI_VECTOR_CORE');
        """
    )
    # 1,050 comm rows (>2 chunks of 500) + 1 duplicate globalTaskId outside window 1.
    kcon.executemany(
        "INSERT INTO TASK VALUES(?, ?, ?, 0, 7, ?, 5, ?, 1, 0)",
        [(i, i * 10, i * 10 + 5, i, 10_000 + i) for i in range(1, 1051)]
        + [(1050, 999_000, 999_005, 9999, 99_999)],
    )
    kcon.executemany(
        "INSERT INTO COMMUNICATION_OP VALUES(?, 1, ?, ?, 0, ?, 4, ?)",
        [
            (1 if i % 3 == 1 else (2 if i % 3 == 2 else 3), i * 10, i * 10 + 5, 10_000 + i, i)
            for i in range(1, 1051)
        ],
    )
    kcon.commit()
    kcon.close()

    from mindie_profiler import sources_db as sdb_mod

    orig_connect = sdb_mod._connect
    src_sql: list[str] = []
    monkeypatch.setattr(
        sdb_mod,
        "_connect",
        lambda p, t: (c := orig_connect(p, t), c.set_trace_callback(src_sql.append))[0],
    )
    cached_src = DbSource(probe_db(cache_db))
    ev_w0, _ = cached_src.iter_window(Window(0, 6_000, step=0))
    group_scans_w0 = [s for s in src_sql if "GROUP BY globalTaskId" in s]
    assert len(group_scans_w0) == 1
    src_sql.clear()
    ev_w1, _ = cached_src.iter_window(Window(6_000, 11_000, step=1))
    assert [s for s in src_sql if "GROUP BY globalTaskId" in s] == []
    by_op = {e.locator["op_id"]: e for e in (*ev_w0, *ev_w1)}
    assert by_op["1"].locator["task_join_status"] == "connection_and_interval"
    assert by_op["1050"].locator["task_join_status"] == "unresolved_ambiguous_global_task_id"
    monkeypatch.undo()

    monkeypatch.setattr("mindie_profiler.collective_readiness.open_readonly", traced_open)
    post_open_sql.clear()
    a2a_res = read_collective_readiness(tmp_path / "cache", source="db", windows=[(8, 48)])
    assert len([s for s in post_open_sql if "FROM TASK" in s and "GROUP BY globalTaskId" in s]) == 1
    calls_4 = a2a_res["calls"]
    assert [c["operation"]["collective"] for c in calls_4] == [
        "all_to_allv", "all_to_all", "all_to_all", "all_to_allv"
    ]
    assert [(c["operation"]["collective"], c["call_ordinal"]) for c in calls_4] == [
        ("all_to_allv", 0), ("all_to_all", 0), ("all_to_all", 1), ("all_to_allv", 1)
    ]
