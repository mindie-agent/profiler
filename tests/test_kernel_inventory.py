"""Reuse real A3/A5 export excerpts; never submit a hardware workload."""
import csv
import io
import json
from pathlib import Path
import shutil
import sqlite3
import tarfile

from mindie_profiler.kernel_inventory import build_inventory, csv_rows, _event

FIXTURES = Path(__file__).parent / "fixtures" / "kernel_inventory"


def _context():
    return {"hardware_key": "Ascend910_9362", "environment_key": "real-a3-excerpt",
            "capture_group": "real-a3-excerpt", "split": "unassigned"}


def test_real_export_columns_keep_multi_input_shapes_and_distinct_dtypes():
    with (FIXTURES / "a3_kernel_details.csv").open() as stream:
        row = next(r for r in csv_rows(stream) if r["type"] == "Index")
    first = _event(row, _context(), "capture")
    assert first[3]["input_shapes"] == "8;1;1;8192"
    assert first[3]["input_dtypes"] == "INT32;INT64;INT64;INT64"
    changed = _event({**row, "input_dtypes": "INT64;INT64;INT64;INT64"}, _context(), "capture")
    assert first[0] != changed[0]
    with (FIXTURES / "a5_op_summary.csv").open() as stream:
        a5 = next(csv_rows(stream))
    assert a5["duration_us"] == "3.186"
    assert a5["type"] == "Fill"
    assert a5["core"] == "AI_VECTOR_CORE"


def test_copied_csv_archive_and_second_import_do_not_duplicate_measurements(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first = source / "kernel_details.csv"
    shutil.copyfile(FIXTURES / "a3_kernel_details.csv", first)
    shutil.copyfile(first, source / "copy_kernel_details.csv")
    with tarfile.open(source / "captured.tgz", "w:gz") as archive:
        archive.add(first, arcname="raw/kernel_details.csv")
    manifest = {"roots": [str(source)], "contexts": [{"prefix": str(source), "context": _context()}]}
    output = tmp_path / "inventory"
    result = build_inventory(manifest, output)
    assert result["calls"] == 32
    assert result["raw_rows"] == 96
    assert result["duplicate_rows"] == 64
    assert not result["failures"]
    again = build_inventory(manifest, output)
    assert again["calls"] == 32
    assert again["duplicate_rows"] == 64
    assert again["source_actions"] == {"completed": 0, "reused": 3}
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        assert connection.execute("SELECT SUM(calls) FROM costs").fetchone()[0] == 32


def test_missing_metadata_and_heldout_are_in_inventory_but_not_cost_candidates(tmp_path):
    source = tmp_path / "kernel_details.csv"
    shutil.copyfile(FIXTURES / "a3_kernel_details.csv", source)
    result = build_inventory({"roots": [str(source)]}, tmp_path / "unknown")
    assert result["cost_variants"] == 0
    assert result["gap_reasons"]["missing_hardware_key"] > 0
    result = build_inventory({"roots": [str(source)], "contexts": [
        {"prefix": str(tmp_path), "context": {**_context(), "split": "heldout"}}
    ]}, tmp_path / "heldout")
    assert result["cost_variants"] == 0
    assert result["gap_reasons"]["heldout_not_for_calibration"] > 0


def test_corrected_context_reclassifies_existing_observations_without_double_counting(tmp_path):
    source = tmp_path / "kernel_details.csv"
    shutil.copyfile(FIXTURES / "a3_kernel_details.csv", source)
    output = tmp_path / "inventory"
    unknown = build_inventory({"roots": [str(source)]}, output)
    corrected = build_inventory({"roots": [str(source)], "contexts": [
        {"prefix": str(tmp_path), "context": _context()}
    ]}, output)
    assert corrected["calls"] == unknown["calls"] == 32
    assert corrected["cost_variants"] > 0
    assert "missing_hardware_key" not in corrected["gap_reasons"]


def test_profile_cell_paths_keep_equal_helper_shapes_in_separate_capture_conditions(tmp_path):
    root = tmp_path / "raw"
    for cell in ("prof_p4096_c1", "prof_p16384_c1"):
        target = root / cell / "kernel_details.csv"
        target.parent.mkdir(parents=True)
        shutil.copyfile(FIXTURES / "a3_kernel_details.csv", target)
    result = build_inventory({"roots": [str(root)], "contexts": [
        {"prefix": str(root), "context": _context()}
    ]}, tmp_path / "inventory")
    assert result["calls"] == 64
    assert result["duplicate_rows"] == 0


def test_retained_pp4_task_time_export_keeps_observations_and_missing_signatures(tmp_path):
    source = tmp_path / "s0-task_time.csv"
    shutil.copyfile(FIXTURES / "a5_task_time.csv", source)
    with source.open() as stream:
        first = next(csv_rows(stream))
    assert first["duration_us"] == "5.248"
    assert first["core"] == "MEMCPY_ASYNC"
    result = build_inventory({"roots": [str(source)], "contexts": [
        {"prefix": str(tmp_path), "context": _context()}
    ]}, tmp_path / "inventory")
    assert result["calls"] == 32
    assert result["cost_variants"] == 0
    assert result["gap_reasons"]["memory_task_use_existing_transfer_model"] > 0


def _copied_capture(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    first = source / "a_kernel_details.csv"
    second = source / "b_kernel_details.csv"
    shutil.copyfile(FIXTURES / "a3_kernel_details.csv", first)
    shutil.copyfile(first, second)
    manifest = {"roots": [str(source)], "contexts": [
        {"prefix": str(source), "context": _context()}]}
    return first, second, manifest


def _change_first_duration(path, value):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    column = next(field for field in fields if "Duration" in field)
    rows[0][column] = value
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_replacing_one_copy_retains_occurrences_still_present_in_an_unchanged_copy(tmp_path):
    first, _, manifest = _copied_capture(tmp_path)
    output = tmp_path / "incremental"
    before = build_inventory(manifest, output)
    assert before["calls"] == 32
    _change_first_duration(first, "999.125")
    incremental = build_inventory(manifest, output)
    fresh = build_inventory(manifest, tmp_path / "fresh")
    # One updated occurrence and its original are both present across the two
    # current files; the remaining 31 observations are still duplicate copies.
    assert fresh["calls"] == 33
    assert incremental["calls"] == fresh["calls"]
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        assert connection.execute("SELECT SUM(calls) FROM costs").fetchone()[0] == 33


def test_failed_replacement_does_not_invalidate_a_successful_duplicate_source(tmp_path):
    first, _, manifest = _copied_capture(tmp_path)
    output = tmp_path / "incremental"
    assert build_inventory(manifest, output)["calls"] == 32
    _change_first_duration(first, "malformed")
    failed = build_inventory(manifest, output)
    assert len(failed["failures"]) == 1
    assert failed["source_status"]["failed"] == 1
    assert failed["calls"] == 32
    # Repairing the failed copy restores source completeness, not 32 extra
    # measurements. Raw events also retain a usable source for catalogue reads.
    shutil.copyfile(FIXTURES / "a3_kernel_details.csv", first)
    repaired = build_inventory(manifest, output)
    assert not repaired["failures"]
    assert repaired["calls"] == 32
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events e JOIN sources s ON s.id=e.source "
            "WHERE s.status!='completed'").fetchone()[0] == 0


def test_replaced_archive_drops_removed_members_without_retaining_old_costs(tmp_path):
    archive_path = tmp_path / "capture.tgz"
    fixture = FIXTURES / "a3_kernel_details.csv"
    members = ["prof_p4096_c1/kernel_details.csv", "prof_p16384_c1/kernel_details.csv"]
    with tarfile.open(archive_path, "w:gz") as archive:
        for member in members:
            archive.add(fixture, arcname=member)
    manifest = {"roots": [str(archive_path)], "contexts": [
        {"prefix": str(tmp_path), "context": _context()}]}
    output = tmp_path / "incremental"
    assert build_inventory(manifest, output)["calls"] == 64
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(fixture, arcname=members[0])
    incremental = build_inventory(manifest, output)
    fresh = build_inventory(manifest, tmp_path / "fresh")
    assert fresh["calls"] == 32
    assert incremental["calls"] == fresh["calls"]


def test_failed_new_source_removes_flushed_partial_occurrences(tmp_path):
    with (FIXTURES / "a3_kernel_details.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    duration = next(field for field in fields if "Duration" in field)
    source = tmp_path / "kernel_details.csv"
    with source.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        # Repeated captured records cross a committed import batch. An invalid
        # final record must not leave partial observations in catalogue reads.
        for _ in range(129):
            writer.writerows(rows)
        writer.writerow({**rows[0], duration: "malformed"})
    output = tmp_path / "inventory"
    result = build_inventory({"roots": [str(source)]}, output)
    assert len(result["failures"]) == 1
    assert result["calls"] == 0
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0


def test_legacy_catalogue_migration_rereads_unchanged_copy_outside_current_roots(tmp_path):
    first, second, manifest = _copied_capture(tmp_path)
    output = tmp_path / "inventory"
    assert build_inventory(manifest, output)["calls"] == 32
    # The original schema recorded only the first copy in events.source.
    # Removing copy memberships reproduces that retained on-disk schema.
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        connection.execute("DROP TABLE IF EXISTS event_sources")
    _change_first_duration(first, "999.125")
    narrowed = {**manifest, "roots": [str(first)]}
    migrated = build_inventory(narrowed, output)
    assert not migrated["failures"]
    assert migrated["calls"] == 33
    with sqlite3.connect(output / "kernels.sqlite") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM events e JOIN sources s ON s.id=e.source "
            "WHERE s.path=?", (str(second.resolve()),)).fetchone()[0] > 0
