"""Tier-1 inventory and Host/Device correlation tests on a real sqlite shape."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from mindie_profiler.correlate import correlate_profile
from mindie_profiler.analyze import analyze_profile
from mindie_profiler.events import ProfilerQueryError, ProfilerUsageError, Window
from mindie_profiler.inventory import inventory_profile
from mindie_profiler.__main__ import main


def _sid(con: sqlite3.Connection, cache: dict[str, int], value: str) -> int:
    if value not in cache:
        cache[value] = len(cache) + 1
        con.execute("INSERT INTO STRING_IDS VALUES (?, ?)", (cache[value], value))
    return cache[value]


def build_correlate_db(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    cache: dict[str, int] = {}
    try:
        con.executescript(
            """
            CREATE TABLE META_DATA(name TEXT, value TEXT);
            CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
            CREATE TABLE TASK(startNs INTEGER, endNs INTEGER, deviceId INTEGER, connectionId INTEGER,
                              globalTaskId INTEGER, globalPid INTEGER, taskType INTEGER, contextId INTEGER,
                              streamId INTEGER, taskId INTEGER, modelId INTEGER, depth INTEGER);
            CREATE TABLE COMPUTE_TASK_INFO(name INTEGER, globalTaskId INTEGER PRIMARY KEY,
                              blockDim INTEGER, mixBlockDim INTEGER, taskType INTEGER, opType INTEGER,
                              inputFormats INTEGER, inputDataTypes INTEGER, inputShapes INTEGER,
                              outputFormats INTEGER, outputDataTypes INTEGER, outputShapes INTEGER,
                              attrInfo INTEGER, opState INTEGER, hf32Eligible INTEGER, waitNs INTEGER);
            CREATE TABLE PYTORCH_API(id INTEGER, name INTEGER, globalTid INTEGER,
                              startNs INTEGER, endNs INTEGER, connectionId INTEGER);
            CREATE TABLE CANN_API(id INTEGER, name INTEGER, globalTid INTEGER,
                              startNs INTEGER, endNs INTEGER, connectionId INTEGER);
            CREATE TABLE CONNECTION_IDS(id INTEGER, connectionId INTEGER);
            CREATE TABLE MSTX_EVENTS(id INTEGER, name INTEGER, globalTid INTEGER,
                              startNs INTEGER, endNs INTEGER);
            """
        )
        con.execute("INSERT INTO META_DATA VALUES ('SCHEMA_VERSION', '1.2.0')")

        def host(table, rowid, name, start, end, connection=None):
            placeholders = "?" if table == "MSTX_EVENTS" else "?,?"
            values = (rowid, _sid(con, cache, name), 100, start, end)
            if table != "MSTX_EVENTS":
                values = values + (connection,)
            con.execute(
                f"INSERT INTO {table} VALUES (?,?,?,?,{placeholders})",
                values,
            )

        host("PYTORCH_API", 1, "model.forward", 0, 90_000)
        host("PYTORCH_API", 2, "layer.mla", 1_000, 80_000)
        host("PYTORCH_API", 3, "ProfilerStep#1", 0, 90_000)
        host("CANN_API", 10, "aclrtLaunchKernel", 2_000, 2_500, 500)
        host("MSTX_EVENTS", 20, "prefill", 0, 50_000)
        host("MSTX_EVENTS", 21, "decode", 50_000, 90_000)

        tasks = [
            (1, 3_000, 6_000, 500, 1, 1),
            (2, 7_000, 8_000, 501, 2, 2),
            (1, 20_000, 22_000, 500, 1, 1),
            (3, 30_000, 35_000, 502, 3, 3),
        ]
        for global_id, start, end, connection, task_id, stream in tasks:
            con.execute(
                "INSERT INTO TASK VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (start, end, 0, connection, global_id, 100, 3, 4294967295, stream, task_id, 4294967295, 0),
            )
        for global_id, task_id, name, op_type in (
            (1, 1, "aclnnFlashAttention", "FlashAttention"),
            (2, 2, "aclnnRmsNorm", "RmsNorm"),
            (3, 3, "aclnnTransData", "TransData"),
        ):
            con.execute(
                "INSERT INTO COMPUTE_TASK_INFO VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    _sid(con, cache, name), global_id, 20, 0, 3, _sid(con, cache, op_type),
                    0, 0, _sid(con, cache, '"8,16"'), 0, 0, None, 0, _sid(con, cache, "dynamic"),
                    _sid(con, cache, "NO"), 0,
                ),
            )
        con.commit()
    finally:
        con.close()
    return path


def test_inventory_lists_tables_native_windows_and_capture_span(tmp_path):
    db_path = build_correlate_db(tmp_path / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db")
    result = inventory_profile(db_path.parent.parent)
    db = result["ranks"][0]["files"][0]
    assert db["core_tables"]["PYTORCH_API"] is True
    assert db["core_tables"]["CANN_API"] is True
    assert db["core_tables"]["CONNECTION_IDS"] is True
    assert db["core_tables"]["MSTX_EVENTS"] is True
    assert [row["step"] for row in db["native_step_windows"]] == [1]
    assert {row["phase"] for row in db["mstx_windows"]} == {"prefill", "decode"}
    assert db["capture_span"]["start_ns"] == 0
    assert db["capture_span"]["end_ns"] == 90_000


def test_correlate_builds_host_stack_dispatch_gap_and_unmatched_ratio(tmp_path):
    db_path = build_correlate_db(tmp_path / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db")
    result = correlate_profile(
        db_path.parent.parent,
        window=Window(0, 60_000),
        kernel_name="FlashAttention",
        min_gap_ms=0.01,
    )
    assert result["host"]["matched_task_count"] == 2
    assert result["host"]["unmatched_task_count"] == 0
    call = result["correlated_calls"][0]
    assert [item["name"] for item in call["host_stack"]] == ["model.forward", "layer.mla"]
    assert call["cann_api"]["name"] == "aclrtLaunchKernel"
    assert call["dispatch"]["host_dispatch_gap_ms"] == 0.0005
    assert call["association_basis"]["cann"] == "connection_ids"
    assert call["association_basis"]["pytorch"] == "same_global_tid_containment"
    assert call["association_unique"] == {"cann": True, "pytorch": True}
    assert result["aclgraph"]["ambiguous_global_task_ids"] == [1]
    assert all(call["ambiguous_global_task_id"] for call in result["correlated_calls"])
    assert len(result["device_gaps"]) == 2

    all_tasks = correlate_profile(db_path.parent.parent, window=Window(0, 60_000))
    assert all_tasks["host"]["matched_task_count"] == 2
    assert all_tasks["host"]["unmatched_task_count"] == 2
    assert all_tasks["host"]["unmatched_ratio"] == 0.5
    assert any(gap["device_uncovered_ms"] == 0.012 for gap in all_tasks["device_gaps"])


def test_inventory_correlate_and_sql_cli_subcommands(tmp_path, capsys):
    db_path = build_correlate_db(tmp_path / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db")
    root = db_path.parent.parent
    assert main(["inventory", "--root", str(root)]) == 0
    assert '"schema_version": "mindie-profiler-inventory/1"' in capsys.readouterr().out

    assert main(["correlate", "--root", str(root), "--window", "0:60"]) == 0
    assert '"schema_version": "mindie-profiler-correlation/1"' in capsys.readouterr().out

    assert main(["sql", "--db", str(db_path), "--query", "SELECT id, value FROM STRING_IDS LIMIT 2"]) == 0
    assert '"row_count": 2' in capsys.readouterr().out


def test_correlate_requires_explicit_window(tmp_path):
    db_path = build_correlate_db(tmp_path / "rank_0" / "ASCEND_PROFILER_OUTPUT" / "ascend_pytorch_profiler_0.db")
    with pytest.raises(ProfilerUsageError, match="explicit"):
        correlate_profile(db_path.parent.parent)


def _norm_connection_db(path, *, connection_mode="connected"):
    db_path = build_correlate_db(path)
    with sqlite3.connect(db_path) as con:
        cache = {value: sid for sid, value in con.execute("SELECT id, value FROM STRING_IDS")}
        descriptors = [
            "ND;ND", "DT_BF16;DT_BF16", "2,8;8",
            "ND;ND", "DT_BF16;DT_FLOAT", "2,8;2,1",
        ]
        con.execute(
            "UPDATE COMPUTE_TASK_INFO SET inputFormats=?, inputDataTypes=?, inputShapes=?, "
            "outputFormats=?, outputDataTypes=?, outputShapes=? WHERE globalTaskId=2",
            tuple(_sid(con, cache, value) for value in descriptors),
        )
        con.execute(
            "INSERT INTO CANN_API VALUES (11, ?, 200, 6500, 6800, 501)",
            (_sid(con, cache, "aclnnRmsNorm"),),
        )
        con.execute(
            "INSERT INTO PYTORCH_API VALUES (4, ?, 200, 6000, 6900, 4)",
            (_sid(con, cache, "model.layers.0.norm"),),
        )
        con.execute("INSERT INTO CONNECTION_IDS VALUES (4, 501)")
        if connection_mode == "containment":
            con.execute("DELETE FROM CONNECTION_IDS WHERE id=4")
        elif connection_mode == "direct":
            con.execute("DELETE FROM CANN_API WHERE id=11")
        elif connection_mode == "multiple_connections":
            con.execute("INSERT INTO CONNECTION_IDS VALUES (4, 503)")
        elif connection_mode == "cann_conflict":
            con.execute(
                "INSERT INTO CANN_API VALUES (12, ?, 300, 6600, 6800, 501)",
                (_sid(con, cache, "otherRmsNormLaunch"),),
            )
        elif connection_mode == "host_conflict":
            con.execute(
                "INSERT INTO PYTORCH_API VALUES (5, ?, 201, 6000, 6900, 5)",
                (_sid(con, cache, "model.layers.1.norm"),),
            )
            con.execute("INSERT INTO CONNECTION_IDS VALUES (5, 501)")
        elif connection_mode == "crossing_scopes":
            con.execute("DELETE FROM CONNECTION_IDS WHERE id=4")
            con.execute(
                "INSERT INTO PYTORCH_API VALUES (5, ?, 200, 6200, 7000, NULL)",
                (_sid(con, cache, "model.layers.1.norm"),),
            )
        elif connection_mode == "interval_only":
            con.execute("UPDATE CONNECTION_IDS SET connectionId=502 WHERE id=4")
            con.execute("UPDATE CANN_API SET connectionId=502, endNs=8500 WHERE id=11")
    return db_path


def _analyze_correlated_norm(db_path, *, max_rows=5000):
    from test_structure_mapping import bindings, structure

    manifest = structure()
    scopes = [
        {"name": f"model.layers.{index}.norm", "node_ids": [node["node_id"]]}
        for index, node in enumerate(manifest["nodes"])
    ]
    window = Window(0, 10_000, step=1)
    correlation = correlate_profile(db_path, window=window, max_rows=max_rows)
    report = analyze_profile(
        db_path, source="db", windows=[window], structure=manifest,
        structure_bindings=bindings(manifest, host_scopes=scopes),
        structure_correlations=[correlation],
    )["structure_mapping"]
    call = next(row for row in correlation["correlated_calls"]
                if row["device_task"]["global_task_id"] == 2)
    event = next(row for row in report["event_mappings"] if row["kernel_name"] == "aclnnRmsNorm")
    return call, event, report


@pytest.mark.parametrize("mode", ["connected", "containment", "direct", "multiple_connections"])
def test_sqlite_connections_bind_only_proven_host_occurrence(tmp_path, mode):
    db_path = _norm_connection_db(
        tmp_path / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        connection_mode=mode,
    )
    call, event, report = _analyze_correlated_norm(db_path)
    assert call["global_task_id_unique"] is True
    assert call["association_unique"]["pytorch"] is True
    assert event["observed_contract"] == ("rmsnorm", (2, 8), "bf16", True)
    assert event["basis"] == "host_connection_and_tensor"
    assert event["node_ids"] == ["rank:0/s0.l0.norm1"]
    assert report["windows"][0]["bound_busy_union_ns"] == 1_000
    assert report["windows"][0]["layers"][0]["busy_union_ns"] == 1_000


@pytest.mark.parametrize("mode, edge", [
    ("cann_conflict", "cann"), ("host_conflict", "pytorch"),
    ("crossing_scopes", "pytorch"), ("interval_only", None),
])
def test_conflicting_or_interval_only_host_chains_never_select_a_layer(tmp_path, mode, edge):
    db_path = _norm_connection_db(
        tmp_path / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        connection_mode=mode,
    )
    call, event, report = _analyze_correlated_norm(db_path)
    if edge:
        assert call["association_unique"][edge] is False
        assert call["association_candidate_counts"][edge] == 2
    else:
        assert call["association_basis"] == {
            "cann": "cann_interval_contains_task", "pytorch": "connection_ids"}
    assert event["status"] == "ambiguous"
    assert event["node_ids"] == []
    assert event["candidate_count"] == 2
    assert report["windows"][0]["bound_busy_union_ns"] == 0


def test_host_query_budget_cannot_hide_a_second_connection_candidate(tmp_path):
    db_path = _norm_connection_db(
        tmp_path / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        connection_mode="host_conflict",
    )
    with pytest.raises(ProfilerQueryError, match="PYTORCH_API exceeds"):
        correlate_profile(db_path, window=Window(0, 10_000), max_rows=4)


def test_small_window_does_not_load_unreferenced_capture_connections(tmp_path):
    db_path = _norm_connection_db(
        tmp_path / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
    )
    with sqlite3.connect(db_path) as con:
        con.executemany(
            "INSERT INTO CONNECTION_IDS VALUES (?, ?)",
            ((index, index + 100_000) for index in range(10_000, 15_001)),
        )
    call, event, report = _analyze_correlated_norm(db_path, max_rows=4)
    assert call["association_unique"] == {"cann": True, "pytorch": True}
    assert event["node_ids"] == ["rank:0/s0.l0.norm1"]
    assert report["windows"][0]["bound_busy_union_ns"] == 1_000
    with sqlite3.connect(db_path) as con:
        con.executemany(
            "INSERT INTO CONNECTION_IDS VALUES (?, ?)",
            [(4, 601), (4, 602), (4, 603), (4, 604)],
        )
    with pytest.raises(ProfilerQueryError, match="referenced CONNECTION_IDS exceeds"):
        correlate_profile(db_path, window=Window(0, 10_000), max_rows=4)


def _real_qwen_connection_db(tmp_path):
    fixture_path = (
        Path(__file__).parent / "fixtures/profiler_core/real_qwen3_host/correlation_slice.json"
    )
    fixture = json.loads(fixture_path.read_text())
    path = tmp_path / "ascend_pytorch_profiler_0.db"
    with sqlite3.connect(path) as con:
        for table, data in fixture["tables"].items():
            con.execute(data["schema"])
            placeholders = ",".join("?" for _ in data["rows"][0])
            columns = ["rowid"] + [
                row[1] for row in con.execute(f"PRAGMA table_info({table})")
            ]
            con.executemany(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                data["rows"],
            )
    return path, Window(*fixture["provenance"]["window_ns"])


def test_real_qwen_cann_direct_value_and_pytorch_index_are_distinct_namespaces(tmp_path):
    path, window = _real_qwen_connection_db(tmp_path)
    with sqlite3.connect(path) as con:
        # The hardware schema has no generic id column in either API table.
        assert "id" not in {row[1] for row in con.execute("PRAGMA table_info(CANN_API)")}
        assert "id" not in {row[1] for row in con.execute("PRAGMA table_info(PYTORCH_API)")}
        assert con.execute(
            "SELECT connectionId FROM CONNECTION_IDS WHERE id=1523"
        ).fetchone() == (1342188552,)

    result = correlate_profile(path, window=window)
    call, = result["correlated_calls"]
    assert call["device_task"]["connection_id"] == 1523
    assert call["global_task_id_unique"] is True
    assert call["cann_api"]["name"] == "launch"
    assert call["host_stack"][-1]["name"] == "aclnnInplaceFillScalar"
    assert call["association_basis"] == {"cann": "connection_ids", "pytorch": "connection_ids"}
    assert call["association_unique"] == {"cann": True, "pytorch": True}


@pytest.mark.parametrize("missing", ["row", "table"])
def test_real_qwen_missing_pytorch_dictionary_never_becomes_a_literal_connection(tmp_path, missing):
    path, window = _real_qwen_connection_db(tmp_path)
    with sqlite3.connect(path) as con:
        # Model a partial export by deleting evidence, without inventing row values.
        # The retained Enqueue row uses index1523, numerically equal to TASK's
        # connection1523 but actually mapped to the unrelated flow1342188552.
        con.execute("DELETE FROM PYTORCH_API WHERE rowid=2959")
        con.execute("DELETE FROM CANN_API")
        if missing == "row":
            con.execute("DELETE FROM CONNECTION_IDS WHERE id=1523")
        else:
            con.execute("DROP TABLE CONNECTION_IDS")
    result = correlate_profile(path, window=window)
    call, = result["correlated_calls"]
    assert call["host_stack"] == []
    assert call["association_basis"] == {"cann": None, "pytorch": None}
    assert result["host"]["unmatched_task_count"] == 1
