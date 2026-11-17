"""Round-1 review regressions: CSV step origins, PMU cache/budget, interval lookup.

[Role] Pin the five P1 review fixes that are observable without a live NPU:
  explicit ``step_trace_time.csv`` start timestamps, indexed PMU measurement
  survival through ``iter_windows``, unindexed PMU cache batch scoping, PMU
  budget accounting limited to selected IDs, and exact ``_IntervalLookup``
  containment equivalence at 32k nested host spans.
[Invariants] Every DB is synthetic and only exercises in-memory arithmetic plus
  read-only SQLite; no fixture, capture, or holdout path is modified.
[Timeouts & Locks] All scans are bounded (``max_rows``/``timeout_s``); no sleeps.
[Side-Effect Policy] Writes only under pytest ``tmp_path``.
"""

from __future__ import annotations

import csv
import random
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from mindie_profiler.analyze_windows import (
    _native_windows_for_source,
    resolve_auto_step_windows,
)
from mindie_profiler.correlate_index import _IntervalLookup
from mindie_profiler.events import ProfilerQueryError, ProfilerUsageError, Window
from mindie_profiler.sources_db import DbSource, probe_db


# --------------------------------------------------------------------------- #
# 1. CSV --auto-step requires a real start timestamp
# --------------------------------------------------------------------------- #
def _step_source(rank_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(kind="csv", rank_dir=str(rank_dir), rank_id="rank_0")


def _write_step_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def test_csv_auto_step_duration_only_rows_never_fabricate_origins(tmp_path: Path) -> None:
    rank_dir = tmp_path / "rank_0"
    path = rank_dir / "step_trace_time.csv"
    _write_step_csv(path, ["Step ID", "Stage(us)"], [["0", "12500"], ["1", "12500"]])
    source = _step_source(rank_dir)

    windows, table = _native_windows_for_source(source, timeout_s=1.0)
    assert windows == []
    assert table == "step_trace_time.csv"

    # Duration-only rows must hit the existing missing-marker path, not invent
    # step * 1_000_000 ns origins.
    with pytest.raises(ProfilerUsageError, match="no common native STEP_TIME"):
        resolve_auto_step_windows(tmp_path, [source])

    _write_step_csv(
        path,
        ["Step ID", "Step Start Time(us)", "Stage(us)"],
        [["0", "1763456164.89", "12500"], ["1", "1763456177.39", "12500"]],
    )
    windows, table = _native_windows_for_source(source, timeout_s=1.0)
    assert table == "step_trace_time.csv"
    assert windows[0]["start_ns"] == 1_763_456_164_890
    assert windows[0]["end_ns"] == 1_763_456_164_890 + 12_500_000
    assert windows[0]["duration_ms"] == 12.5
    assert windows[0]["start_ns"] != 0  # not fabricated from the step ID

    windows_by_rank, provenance = resolve_auto_step_windows(tmp_path, [source])
    selected = windows_by_rank["rank_0"]
    assert [window.step for window in selected] == [1]
    assert selected[0].start_ns == 1_763_456_177_390
    assert selected[0].end_ns == 1_763_456_177_390 + 12_500_000
    assert provenance["selection_basis"] == "native_step_auto_post_warmup"
    assert provenance["warmup_excluded_steps"] == [0]


# --------------------------------------------------------------------------- #
# 2. Synthetic profiler DBs for PMU regressions
# --------------------------------------------------------------------------- #
def _create_db(path: Path, *, indexed: bool) -> None:
    con = sqlite3.connect(path)
    try:
        con.executescript(
            """
            CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
            CREATE TABLE TASK(globalTaskId INTEGER, startNs INTEGER, endNs INTEGER,
                              deviceId INTEGER, streamId INTEGER, taskId INTEGER,
                              modelId INTEGER, contextId INTEGER, taskType INTEGER);
            CREATE TABLE COMPUTE_TASK_INFO(
                name INTEGER, globalTaskId INTEGER PRIMARY KEY, blockDim INTEGER,
                mixBlockDim INTEGER, taskType INTEGER, opType INTEGER,
                inputShapes INTEGER, inputDataTypes INTEGER, inputFormats INTEGER,
                outputShapes INTEGER, outputDataTypes INTEGER, outputFormats INTEGER,
                opState INTEGER, waitNs INTEGER);
            CREATE TABLE TASK_PMU_INFO(globalTaskId INTEGER, name INTEGER, value NUMERIC);
            CREATE TABLE META_DATA(name TEXT, value TEXT);
            """
        )
        con.execute("INSERT INTO META_DATA VALUES ('SCHEMA_VERSION', '1.2.0')")
        if indexed:
            con.execute(
                "CREATE INDEX idx_task_pmu_global ON TASK_PMU_INFO(globalTaskId)")
        con.commit()
    finally:
        con.close()


class _Ids:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.cache: dict[str, int] = {}

    def __call__(self, value: str) -> int:
        if value not in self.cache:
            self.cache[value] = len(self.cache) + 1
            self.con.execute(
                "INSERT INTO STRING_IDS VALUES (?,?)", (self.cache[value], value))
        return self.cache[value]


def _insert_task(con: sqlite3.Connection, ids: _Ids, gid: int, start: int,
                 end: int) -> None:
    con.execute(
        "INSERT INTO TASK VALUES (?,?,?,?,?,?,?,?,?)",
        (gid, start, end, 0, 1, gid, 0, 0, ids("AI_CORE")),
    )
    con.execute(
        "INSERT INTO COMPUTE_TASK_INFO VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (ids("MatMulV2"), gid, 20, 0, ids("AI_CORE"), ids("MatMulV2"),
         ids("[8, 16]"), ids("DT_BF16"), ids("ND"), ids("[8, 8]"),
         ids("DT_BF16"), ids("ND"), ids("dynamic"), 0),
    )


def _insert_pmu(con: sqlite3.Connection, gid: int, metric: int, value: float) -> None:
    con.execute("INSERT INTO TASK_PMU_INFO VALUES (?,?,?)", (gid, metric, value))


def _pmu_status(events, gid: int) -> tuple[str, dict[str, float]]:
    event = next(event for event in events
                 if event.locator.get("task_global_id") == gid)
    return event.pmu_status, dict(event.pmu or ())


# --------------------------------------------------------------------------- #
# 3. Indexed PMU measurements must survive iter_windows and later batches
# --------------------------------------------------------------------------- #
def test_indexed_pmu_measurements_survive_iter_windows(tmp_path: Path) -> None:
    db_path = tmp_path / "indexed_pmu.db"
    _create_db(db_path, indexed=True)
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        _insert_task(con, ids, 1, 1_000, 2_000)
        _insert_pmu(con, 1, ids("aic_mac_ratio"), 0.75)
        con.commit()
    finally:
        con.close()

    window = Window(0, 3_000, step=0, label="step=0")
    source = DbSource(probe_db(db_path))

    events, _stats = source.iter_window(window)
    assert _pmu_status(events, 1) == ("bound", {"aic_mac_ratio": 0.75})

    # The pre-fix cache published {} for indexed tables and dropped the metric.
    batched_events, batched_stats = source.iter_windows([window])[0]
    assert _pmu_status(batched_events, 1) == ("bound", {"aic_mac_ratio": 0.75})
    assert batched_stats.pmu_rows == 1
    assert batched_stats.pmu_bound_rows == 1

    # Cache lifetime is the batch: a later direct read must still query SQL.
    assert source._pmu_cache is None
    later_events, _later_stats = source.iter_window(window)
    assert _pmu_status(later_events, 1) == ("bound", {"aic_mac_ratio": 0.75})


def test_unindexed_pmu_cache_does_not_leak_into_next_batch(tmp_path: Path) -> None:
    db_path = tmp_path / "unindexed_cache.db"
    _create_db(db_path, indexed=False)
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        _insert_task(con, ids, 1, 1_000, 2_000)
        _insert_task(con, ids, 2, 101_000, 102_000)
        _insert_pmu(con, 1, ids("aic_mac_ratio"), 0.25)
        _insert_pmu(con, 2, ids("aic_mac_ratio"), 0.50)
        con.commit()
    finally:
        con.close()

    source = DbSource(probe_db(db_path))
    first = Window(0, 3_000, step=0, label="step=0")
    second = Window(100_000, 103_000, step=1, label="step=1")

    events, _stats = source.iter_windows([first])[0]
    assert _pmu_status(events, 1) == ("bound", {"aic_mac_ratio": 0.25})
    assert source._pmu_cache is None

    events, _stats = source.iter_window(second)
    assert _pmu_status(events, 2) == ("bound", {"aic_mac_ratio": 0.50})


# --------------------------------------------------------------------------- #
# 4. PMU budget counts only selected IDs, not unrelated range rows
# --------------------------------------------------------------------------- #
def test_pmu_budget_ignores_unrelated_rows_in_range_scan(tmp_path: Path) -> None:
    db_path = tmp_path / "pmu_budget.db"
    _create_db(db_path, indexed=False)
    selected = [*range(1, 401), 100_002]
    con = sqlite3.connect(db_path)
    try:
        ids = _Ids(con)
        for gid in selected:
            _insert_task(con, ids, gid, 1_000, 2_000)
        metric = ids("aic_mac_ratio")
        con.executemany(
            "INSERT INTO TASK_PMU_INFO VALUES (?,?,?)",
            ((gid, metric, 1.0) for gid in range(1, 100_003)),
        )
        con.commit()
    finally:
        con.close()

    window = Window(0, 3_000, step=0, label="step=0")
    source = DbSource(probe_db(db_path))

    # Direct read > 400 IDs uses the unindexed range scan and its consume()
    # budget: only the 401 selected rows may be charged.
    events, stats = source.iter_window(window, max_rows=500)
    assert len(events) == len(selected)
    assert stats.pmu_rows == len(selected)
    assert all(event.pmu_status == "bound" for event in events)

    # iter_windows primes the cache through the other range scan; the same
    # selected-only accounting applies there.
    batch, batch_stats = source.iter_windows([window], max_rows=500)[0]
    assert len(batch) == len(selected)
    assert batch_stats.pmu_rows == len(selected)
    assert all(event.pmu_status == "bound" for event in batch)

    # Control: a genuinely oversized selected-row set still fails closed.
    source._pmu_budget = lambda max_rows: 3  # type: ignore[method-assign]
    with pytest.raises(ProfilerQueryError, match="PMU row budget"):
        source.iter_window(window, max_rows=500)
    with pytest.raises(ProfilerQueryError, match="PMU scan exceeded"):
        source.iter_windows([window], max_rows=500)


# --------------------------------------------------------------------------- #
# 5. _IntervalLookup exact input-order equivalence and non-quadratic nesting
# --------------------------------------------------------------------------- #
def _bruteforce(events, start_ns: int, end_ns: int):
    return [
        event for event in events
        if event["start_ns"] <= start_ns and event["end_ns"] >= end_ns
    ]


def test_interval_lookup_matches_bruteforce_with_nesting_and_ties() -> None:
    rng = random.Random(20261014)
    events = []
    for index in range(300):
        start = rng.randrange(0, 100_000)
        event = {
            "name": f"e{index}",
            "start_ns": start,
            "end_ns": start + rng.choice([0, 1, 10, 1_000, 20_000, 200_000]),
        }
        events.append(event)
    # Force equal starts and strict nesting so the tie-break/order rules run.
    events.extend([
        {"name": "outer", "start_ns": 50_000, "end_ns": 150_000},
        {"name": "inner", "start_ns": 50_000, "end_ns": 60_000},
        {"name": "same-start-short", "start_ns": 50_000, "end_ns": 55_000},
    ])
    rng.shuffle(events)

    lookup = _IntervalLookup(events)
    assert _IntervalLookup([]).containing(0, 0) == []
    for _ in range(500):
        start = rng.randrange(0, 120_000)
        end = start + rng.randrange(0, 60_000)
        assert lookup.containing(start, end) == _bruteforce(events, start, end)


def test_interval_lookup_nested_forward_is_not_quadratic() -> None:
    outer = {"name": "model.forward", "start_ns": 0, "end_ns": 32_001 * 100}
    atens = [
        {"name": f"aten::{index}", "start_ns": index * 100,
         "end_ns": index * 100 + 50}
        for index in range(1, 32_001)
    ]
    events = [outer, *atens]
    lookup = _IntervalLookup(events)

    # Every nested aten query is contained by exactly the outer span and itself.
    for index, aten in enumerate(atens):
        found = lookup.containing(aten["start_ns"], aten["end_ns"])
        assert found == [outer, aten], (index, [event["name"] for event in found])

    # Cross-span and unmatchable queries agree with the brute-force definition.
    for start, end in ((100, 3_200_000), (100, 3_200_001), (3_200_050, 3_200_060)):
        assert lookup.containing(start, end) == _bruteforce(events, start, end)

    started = time.perf_counter()
    for aten in atens:
        lookup.containing(aten["start_ns"], aten["end_ns"])
    elapsed = time.perf_counter() - started
    # The reviewed backward scan took 19.7s here; the tree takes ~0.2s.
    assert elapsed < 5.0, elapsed
