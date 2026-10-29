"""Shared CSV/DB tensor evidence from the retained GLM45 capture."""
import csv
from dataclasses import replace
import gzip
from pathlib import Path
import shutil
import sqlite3

import pytest

from mindie_profiler.events import ProfilerSchemaError, Window
from mindie_profiler.normalized import kernel_rows, row_from_event
from mindie_profiler.sources_csv import CsvSource, probe_csv
from mindie_profiler.sources_db import DbSource, probe_db
from mindie_profiler.segment import find_csv_candidates


CAPTURE = Path(__file__).parent / "fixtures/profiler_core/real_glm45"
CSV = CAPTURE / "kernel_details_slice.csv"
DB = CAPTURE / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db"


def test_real_csv_and_db_preserve_complete_tensor_contract_and_occurrence():
    csv_row = next(kernel_rows(CSV, rank_id="rank_0", rank_index=0))
    assert csv_row.start_ns == 1763456164890788360
    assert csv_row.duration_ns == 1920
    assert csv_row.input_shapes == ((2,), (1,))
    assert csv_row.output_shapes == ((3,),)
    assert csv_row.output_dtypes == ("INT32",)
    assert csv_row.output_formats == ("ND",)
    assert csv_row.blocks == 1 and csv_row.state == "dynamic"
    assert csv_row.line == 2
    assert csv_row.identity["payload"]["locator"]["source"] == str(CSV.resolve())
    assert csv_row.identity["payload"]["locator"]["csv_line"] == 2
    events, _ = DbSource(probe_db(DB)).iter_window(Window(csv_row.start_ns, csv_row.end_ns))
    db_row = row_from_event(next(event for event in events if event.name == csv_row.name))
    assert db_row.signature == csv_row.signature
    assert (db_row.start_ns, db_row.end_ns) == (csv_row.start_ns, csv_row.end_ns)
    assert db_row.event.locator["task_global_id"] == 1053
    assert db_row.source == str(DB.resolve())
    assert db_row.counters_us["aiv_mte2_time(us)"] == pytest.approx(
        csv_row.counters_us["aiv_mte2_time(us)"], abs=0.001)
    assert db_row.event_id != csv_row.event_id


def test_analysis_and_streaming_use_the_same_event_identity_and_decoder():
    row = next(kernel_rows(CSV, rank_id="rank_0", rank_index=0))
    source = CsvSource(probe_csv(CSV), rank_id="rank_0", rank_index=0)
    events, stats = source.read_windows([Window(row.start_ns, row.end_ns)])[0]
    assert stats.bad_rows == 0
    projected = row_from_event(next(event for event in events if event.name == row.name))
    assert projected == row
    assert projected.event_id == row.event_id
    unsupported = row_from_event(replace(projected.event, input_shapes="symbolic_N,5120"))
    assert unsupported.input_shapes is None
    assert unsupported.event.input_shapes == "symbolic_N,5120"
    assert unsupported.event.locator == row.event.locator


def test_optional_db_outputs_and_launch_fields_remain_unknown(tmp_path):
    target = tmp_path / "optional.db"
    shutil.copyfile(DB, target)
    with sqlite3.connect(target) as db:
        for column in ("outputShapes", "outputDataTypes", "outputFormats", "opState", "blockDim", "mixBlockDim"):
            db.execute(f"ALTER TABLE COMPUTE_TASK_INFO DROP COLUMN {column}")
    expected = next(kernel_rows(CSV))
    events, _ = DbSource(probe_db(target)).iter_window(Window(expected.start_ns, expected.end_ns))
    row = row_from_event(next(event for event in events if event.name == expected.name))
    assert row.input_shapes == expected.input_shapes
    assert row.output_shapes is None and row.output_dtypes == ()
    assert row.output_formats == () and row.state == "" and row.blocks is None
    assert row.duration_ns == expected.duration_ns


def test_malformed_timing_is_visible_in_analysis_and_strict_stream(tmp_path):
    with CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        raw = next(reader)
        header = reader.fieldnames
    raw["Start Time(us)"] = "NaN"
    target = tmp_path / "invalid.csv"
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        writer.writerow(raw)
    events, stats = CsvSource(probe_csv(target), rank_id="0", rank_index=0).read_windows(
        [Window(1, 2)])[0]
    assert not events and stats.bad_rows == 1 and stats.rows_read == 1
    with pytest.raises(ProfilerSchemaError, match="CSV line 2 has invalid timing"):
        list(kernel_rows(target))


def test_compressed_capture_uses_same_tensor_decoder_and_row_locations(tmp_path):
    target = tmp_path / "ASCEND_PROFILER_OUTPUT/kernel_details.csv.gz"
    target.parent.mkdir()
    with CSV.open("rb") as source, gzip.open(target, "wb") as output:
        shutil.copyfileobj(source, output)
    assert target in find_csv_candidates(tmp_path)
    original = list(kernel_rows(CSV))
    compressed = list(kernel_rows(target))
    assert len(original) == len(compressed)
    for first, second in zip(original, compressed):
        assert (first.signature, first.start_ns, first.duration_ns, first.line) == (
            second.signature, second.start_ns, second.duration_ns, second.line)
        assert second.source == str(target.resolve())
        assert second.event_id != first.event_id
    from mindie_profiler.inventory import inventory_profile
    from mindie_profiler.segment import discover_rank_sources

    named = target.with_name("pf4k_b1.csv.gz")
    target.rename(named)
    assert discover_rank_sources(named)[0].csv_path == str(named.resolve())
    inventory = inventory_profile(named)
    assert inventory["ranks"][0]["csv_candidates"] == [str(named.resolve())]
    assert inventory["ranks"][0]["files"][0]["kind"] == "csv"


def test_native_op_summary_distinguishes_operator_type_from_execution_core():
    capture = Path(__file__).parent / "fixtures/attention_cache_contracts/a5_fia_paged_probe.csv"
    row = next(kernel_rows(capture))
    assert row.kind == "FusedInferAttentionScore"
    assert row.core == "MIX_AIC"
    assert row.input_shapes is not None and len(row.input_shapes) == 31
    from mindie_profiler.tensor_contracts import observed_contract

    contract = observed_contract(row)
    assert contract[:2] == ("native_tensor_abi", "FusedInferAttentionScore")
