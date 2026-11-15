"""CANN 9.2.1 mindstudio_profiler_output CSV layouts through the generic importer."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from mindie_profiler.events import ProfilerError, ProfilerSchemaError, ProfilerUsageError, Window
from mindie_profiler.inventory import inventory_profile
from mindie_profiler.normalized import row_from_event
from mindie_profiler.sources_csv import (
    CsvSource,
    find_mindstudio_csv_candidates,
    probe_csv,
    select_mindstudio_csv,
)
from mindie_profiler.segment import discover_rank_sources, find_csv_candidates

FIXTURE = Path(__file__).parent / "fixtures/profiler_core/cann92_mindstudio"
OP_SUMMARY = FIXTURE / "op_summary_slice.csv"
TASK_TIME = FIXTURE / "task_time_slice.csv"


def test_real_op_summary_keeps_native_fields_duration_and_raw_tick():
    schema = probe_csv(OP_SUMMARY)
    assert schema.layout == "op_summary"
    assert schema.source_kind == "mindstudio_op_summary_csv"
    events = list(CsvSource(schema, rank_id="0", rank_index=0).iter_events())
    assert len(events) == 15

    event = events[0]
    assert event.name == "aclnnMatmul_MatMulV3Common_MatMulV3"
    assert event.op_type == "MatMulV3"
    assert event.device_id == "1"
    assert event.stream_id == "61"
    assert event.task_id == "6"
    assert event.start_ns == 1794498607945358570
    assert event.duration_ns == 5959
    assert event.input_shapes == '"64,64;64,64"'
    assert event.output_shapes == '"64,64"'
    assert event.input_dtypes == "DT_BF16;DT_BF16"
    assert event.wait_ns == 0 and event.wait_status == "bound"
    assert event.clock.domain == "mindstudio_op_summary_us"
    assert event.clock.unit == "us" and event.clock.scale_ns == 1000
    assert event.clock.reference_domain is None
    # Raw start/duration tokens are retained; the missing end column is None.
    assert event.clock_start_tick == "1794498607945358.570"
    assert event.clock_duration_tick == "5.959"
    assert event.clock_end_tick is None
    assert event.table == "op_summary.csv"
    assert event.locator["layout"] == "op_summary"
    assert event.source_id.startswith("SRC-")
    assert event.capture_id.startswith("CAP-")
    assert event.table_kind == "op_summary"
    assert event.field_presence == {"clock": True, "abi": True, "step": False, "state": True}

    row = row_from_event(event)
    assert row.duration_ns == 5959
    assert row.clock_duration_tick == "5.959"
    assert row.clock_start_tick == "1794498607945358.570"


def test_real_task_time_layout_uses_same_decoder_and_keeps_end_tick():
    schema = probe_csv(TASK_TIME)
    assert schema.layout == "task_time"
    assert schema.source_kind == "mindstudio_task_time_csv"
    events = list(CsvSource(schema, rank_id="0", rank_index=0).iter_events())
    assert len(events) == 15

    event = events[0]
    assert event.name.startswith("MatMulV3_ND_ND_ND_ND_BF16_BF16")
    assert event.core == "AI_CORE"
    assert event.device_id == "1"
    assert event.stream_id == "61"
    assert event.task_id == "6"
    assert event.start_ns == 1794498607945358570
    assert event.duration_ns == 5959
    assert event.clock.domain == "mindstudio_task_time_us"
    assert event.clock_start_tick == "1794498607945358.570"
    assert event.clock_duration_tick == "5.959"
    assert event.clock_end_tick == "1794498607945364.529"
    assert event.table == "task_time.csv"
    assert event.table_kind == "task_time"
    assert event.source_id.startswith("SRC-")
    assert event.capture_id.startswith("CAP-")
    assert event.field_presence == {"clock": True, "abi": False, "step": False, "state": False}


def test_task_time_invalid_timing_is_reported_not_coerced(tmp_path):
    target = tmp_path / "task_time_slice.csv"
    shutil.copyfile(TASK_TIME, target)
    with target.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    rows[0]["task_start(us)"] = "NaN"
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    schema = probe_csv(target)
    stats_events, stats = CsvSource(
        schema, rank_id="0", rank_index=0
    ).read_windows([Window(1, 2)])[0]
    assert stats.bad_rows == 1
    assert all(event.task_id != "6" for event in stats_events)
    with pytest.raises(ProfilerSchemaError, match="CSV line 2 has invalid timing"):
        list(CsvSource(schema, rank_id="0", rank_index=0).iter_events(strict=True))


def test_mindstudio_discovery_and_explicit_inventory_path():
    candidates = find_mindstudio_csv_candidates(FIXTURE)
    assert candidates["op_summary"] == [OP_SUMMARY.resolve()]
    assert candidates["task_time"] == [TASK_TIME.resolve()]
    selected, layout = select_mindstudio_csv(FIXTURE)
    assert selected == OP_SUMMARY.resolve()
    assert layout == "op_summary"

    inventory = inventory_profile(OP_SUMMARY)
    assert inventory["rank_count"] == 1
    assert inventory["ranks"][0]["csv_candidates"] == [str(OP_SUMMARY.resolve())]
    assert inventory["limitations"] == []


def test_directory_discovery_and_inventory_preserve_layout_clock_facts():
    sources = discover_rank_sources(FIXTURE, source="csv")
    assert len(sources) == 1
    assert sources[0].kind == "csv"
    assert sources[0].csv_path == str(OP_SUMMARY.resolve())

    inventory = inventory_profile(FIXTURE)
    assert inventory["rank_count"] == 1
    assert inventory["capture_count"] == 1
    assert inventory["limitations"] == []
    assert [Path(item).name for item in inventory["ranks"][0]["csv_candidates"]] == [
        "op_summary_slice.csv",
        "task_time_slice.csv",
    ]
    assert [Path(item).name for item in inventory["ranks"][0]["selected_csv"]] == [
        "op_summary_slice.csv"
    ]
    assert inventory["ranks"][0]["csv_selection_status"] == "selected"
    assert {fact["capture_id"] for fact in inventory["ranks"][0]["files"]} == {
        inventory["ranks"][0]["files"][0]["capture_id"]
    }
    file_fact = next(
        fact for fact in inventory["ranks"][0]["files"]
        if fact["layout"] == "op_summary"
    )
    assert file_fact["layout"] == "op_summary"
    assert file_fact["source_kind"] == "mindstudio_op_summary_csv"
    assert file_fact["schema_version"] == "op_summary_csv_48col"
    assert file_fact["source_id"].startswith("SRC-")
    assert file_fact["capture_id"].startswith("CAP-")
    assert file_fact["table_kind"] == "op_summary"
    assert file_fact["clock"]["domain"] == "mindstudio_op_summary_us"
    assert file_fact["clock"]["reference_domain"] is None


def test_multiple_mindstudio_candidates_require_explicit_path(tmp_path):
    first = tmp_path / "op_summary_a.csv"
    second = tmp_path / "op_summary_b.csv"
    shutil.copyfile(OP_SUMMARY, first)
    shutil.copyfile(OP_SUMMARY, second)
    assert [path.name for path in find_csv_candidates(tmp_path)] == [
        "op_summary_a.csv",
        "op_summary_b.csv",
    ]
    inventory = inventory_profile(tmp_path)
    assert inventory["limitations"][0]["code"] == "multiple_csv_candidates"
    assert inventory["ranks"][0]["csv_selection_status"] == "ambiguous"
    assert [Path(item).name for item in inventory["ranks"][0]["selected_csv"]] == [
        "op_summary_a.csv",
        "op_summary_b.csv",
    ]
    with pytest.raises(ProfilerUsageError, match="CSV candidates"):
        discover_rank_sources(tmp_path, source="csv")


def test_task_time_is_fallback_and_op_statistic_is_not_a_call_source(tmp_path):
    task_dir = tmp_path / "task_only"
    task_dir.mkdir()
    shutil.copyfile(TASK_TIME, task_dir / "task_time_slice.csv")
    assert [path.name for path in find_csv_candidates(task_dir)] == ["task_time_slice.csv"]
    task_inventory = inventory_profile(task_dir)
    assert task_inventory["ranks"][0]["files"][0]["layout"] == "task_time"
    assert task_inventory["ranks"][0]["csv_selection_status"] == "selected"

    statistic_dir = tmp_path / "stat_only"
    statistic_dir.mkdir()
    (statistic_dir / "op_statistic_1.csv").write_text(
        "Device_id,OP Type,Core Type,Count,Total Time(us)\n1,MatMulV3,AI_CORE,1,1.0\n",
        encoding="utf-8",
    )
    assert find_csv_candidates(statistic_dir) == []
    with pytest.raises(ProfilerError, match="no rank/source candidates"):
        inventory_profile(statistic_dir)


def test_inventory_preserves_csv_probe_read_error(tmp_path):
    bad = tmp_path / "op_summary_bad.csv"
    bad.write_text("unexpected,columns\n1,2\n", encoding="utf-8")
    inventory = inventory_profile(tmp_path)
    assert inventory["limitations"][0]["code"] == "csv_read_error"
    file_fact = inventory["ranks"][0]["files"][0]
    assert file_fact["read_error"]["stage"] == "header"
    assert file_fact["read_error"]["code"] == "csv_probe_failed"


def test_mixed_old_new_layouts_and_partial_ambiguity_do_not_drop_ranks(tmp_path):
    legacy = tmp_path / "rank_0"
    legacy.mkdir()
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/kernel_details_slice.csv",
        legacy / "kernel_details.csv",
    )
    modern = tmp_path / "rank_1" / "mindstudio_profiler_output"
    modern.mkdir(parents=True)
    shutil.copyfile(OP_SUMMARY, modern / "op_summary_a.csv")

    inventory = inventory_profile(tmp_path)
    assert inventory["rank_count"] == 2
    assert {
        Path(item).parent.name
        for rank in inventory["ranks"]
        for item in rank["csv_candidates"]
    } == {
        "rank_0",
        "mindstudio_profiler_output",
    }
    sources = discover_rank_sources(tmp_path, source="csv")
    assert len(sources) == 2
    assert {Path(source.csv_path).parent.name for source in sources} == {
        "rank_0",
        "mindstudio_profiler_output",
    }

    shutil.copyfile(OP_SUMMARY, modern / "op_summary_b.csv")
    ambiguous_inventory = inventory_profile(tmp_path)
    assert ambiguous_inventory["rank_count"] == 2
    rank_1 = next(rank for rank in ambiguous_inventory["ranks"] if rank["rank_id"] == "rank_1")
    assert rank_1["csv_selection_status"] == "ambiguous"
    assert [Path(item).name for item in rank_1["selected_csv"]] == [
        "op_summary_a.csv",
        "op_summary_b.csv",
    ]
    with pytest.raises(ProfilerUsageError, match="rank_1.*CSV candidates"):
        discover_rank_sources(tmp_path, source="csv")


def test_existing_db_priority_is_preserved_next_to_mindstudio(tmp_path):
    legacy = tmp_path / "rank_0" / "ASCEND_PROFILER_OUTPUT"
    legacy.mkdir(parents=True)
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        legacy / "ascend_pytorch_profiler_0.db",
    )
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/kernel_details_slice.csv",
        legacy / "kernel_details.csv",
    )
    modern = tmp_path / "rank_1" / "mindstudio_profiler_output"
    modern.mkdir(parents=True)
    shutil.copyfile(OP_SUMMARY, modern / "op_summary_a.csv")

    sources = discover_rank_sources(tmp_path, source="auto")
    by_rank = {source.rank_id: source for source in sources}
    assert by_rank["rank_0"].kind == "db"
    assert by_rank["rank_1"].kind == "csv"


def test_explicit_csv_ambiguity_is_not_suppressed_by_adjacent_db(tmp_path):
    rank_0 = tmp_path / "rank_0"
    rank_0.mkdir()
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/kernel_details_slice.csv",
        rank_0 / "kernel_details.csv",
    )
    rank_1 = tmp_path / "rank_1"
    modern = rank_1 / "mindstudio_profiler_output"
    modern.mkdir(parents=True)
    shutil.copyfile(OP_SUMMARY, modern / "op_summary_a.csv")
    shutil.copyfile(OP_SUMMARY, modern / "op_summary_b.csv")
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        rank_1 / "ascend_pytorch_profiler_1.db",
    )

    with pytest.raises(ProfilerUsageError, match="rank_1.*CSV candidates"):
        discover_rank_sources(tmp_path, source="csv")

    auto = discover_rank_sources(tmp_path, source="auto")
    by_rank = {source.rank_id: source for source in auto}
    assert set(by_rank) == {"rank_0", "rank_1"}
    assert by_rank["rank_0"].kind == "csv"
    assert by_rank["rank_1"].kind == "db"

    inventory = inventory_profile(tmp_path)
    assert inventory["rank_count"] == 2
    rank_1_fact = next(rank for rank in inventory["ranks"] if rank["rank_id"] == "rank_1")
    assert rank_1_fact["db_candidates"]
    assert rank_1_fact["csv_selection_status"] == "ambiguous"
    assert [Path(item).name for item in rank_1_fact["selected_csv"]] == [
        "op_summary_a.csv",
        "op_summary_b.csv",
    ]

    # Explicit DB ignores unrelated CSV ambiguity; explicit CSV with one
    # candidate also bypasses the DB.
    db_source = discover_rank_sources(rank_1 / "ascend_pytorch_profiler_1.db", source="db")[0]
    assert db_source.kind == "db"
    modern_b = tmp_path / "rank_2" / "mindstudio_profiler_output"
    modern_b.mkdir(parents=True)
    shutil.copyfile(OP_SUMMARY, modern_b / "op_summary_a.csv")
    rank_2 = tmp_path / "rank_2"
    shutil.copyfile(
        Path(__file__).parent / "fixtures/profiler_core/real_glm45/rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db",
        rank_2 / "ascend_pytorch_profiler_0.db",
    )
    csv_source = discover_rank_sources(rank_2, source="csv")[0]
    assert csv_source.kind == "csv"
    assert Path(csv_source.csv_path).name == "op_summary_a.csv"
