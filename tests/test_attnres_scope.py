"""Explicit scopes over retained native rows never become flag or layer evidence."""
import csv
from hashlib import sha256
import importlib
import json
from pathlib import Path

import pytest

from mindie_profiler.normalized import kernel_rows


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "tests/fixtures/kimi_grouped_attnres/a5_kimi_k3.csv"


@pytest.fixture
def scope(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return importlib.import_module("replay_attnres_scope")


@pytest.fixture
def captured():
    return [row for row in kernel_rows(CAPTURE) if row.kind == "AttnResFwd"]


def test_real_scope_counts_selected_rows_without_resolving_same_image_flags(scope, captured):
    first, second = captured[:2]
    report = scope.review_scope(
        CAPTURE, source_sha256=sha256(CAPTURE.read_bytes()).hexdigest(),
        start_ns=first.start_ns, end_ns=second.end_ns, expected_events=2)
    assert report["status"] == "completed"
    assert report["observed"]["event_count"] == report["observed"]["complete_event_count"] == 2
    assert report["observed"]["activity_sum_ns"] == first.duration_ns + second.duration_ns
    assert report["observed"]["clipped_event_count"] == 0
    assert report["expected_count_verified"] is True
    assert {item["representative_event"]["payload"]["locator"]["csv_line"]
            for item in report["descriptors"]} == {first.line, second.line}
    assert all(item["observed_contract"] is None for item in report["descriptors"])
    assert all(item["contract_diagnostic"]["reason"] == "active_view_or_stride_unobserved"
               for item in report["descriptors"])
    assert report["comparison"]["status"] == "reference_only"
    assert report["comparison"]["scored_event_count"] == report["comparison"]["bound_event_count"] == 0
    assert report["scope"]["phase"] is report["scope"]["step"] is report["scope"]["layer"] is None


def test_expected_120_does_not_truncate_pad_or_substitute_a_clipped_window(scope, captured, tmp_path):
    first, second = captured[:2]
    output = tmp_path / "scope.json"
    code = scope.main([
        str(CAPTURE), "--source-sha256", sha256(CAPTURE.read_bytes()).hexdigest(),
        "--start-ns", str(first.start_ns + 1000), "--end-ns", str(second.end_ns - 2000),
        "--expected-events", "120", "--output", str(output)])
    report = json.loads(output.read_text())
    assert code == 1 and report["status"] == "count_mismatch"
    assert report["expected_events"] == 120 and report["expected_count_verified"] is False
    assert report["observed"]["event_count"] == report["observed"]["clipped_event_count"] == 2
    assert report["observed"]["activity_sum_ns"] == first.duration_ns + second.duration_ns - 3000
    assert report["observed"]["complete_event_count"] == 0
    assert report["observed"]["complete_mean_us"] is None
    assert report["comparison"]["accuracy_pass"] is None


def test_duration_changes_do_not_choose_flags_for_explicit_real_row_locators(scope, captured, tmp_path):
    with CAPTURE.open(newline="") as stream:
        reader = csv.DictReader(stream)
        fields, rows = reader.fieldnames, list(reader)
    modified = tmp_path / "different-durations.csv"
    for row in rows:
        if row["OP Type"] == "AttnResFwd":
            row["Task Duration(us)"] = "1"
    with modified.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    results = [
        scope.review_scope(
            path, source_sha256=sha256(path.read_bytes()).hexdigest(),
            csv_lines=[row.line for row in captured], expected_events=4)
        for path in (CAPTURE, modified)]
    assert results[0]["observed"]["activity_sum_ns"] != results[1]["observed"]["activity_sum_ns"]
    assert results[1]["observed"]["activity_sum_ns"] == 4000
    assert [item["recorded_descriptor"] for item in results[0]["descriptors"]] == [
        item["recorded_descriptor"] for item in results[1]["descriptors"]]
    assert [item["observed_contract"] for item in results[0]["descriptors"]] == [None] * 4
    assert [item["observed_contract"] for item in results[1]["descriptors"]] == [None] * 4
    assert results[0]["comparison"] == results[1]["comparison"]
