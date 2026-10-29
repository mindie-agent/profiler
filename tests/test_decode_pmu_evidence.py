"""Full descriptor filters preserve real CSV units, zeros and source populations."""
import csv
import importlib.util
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def evidence():
    path = ROOT / "examples/structure/replay_decode_pmu_evidence.py"
    spec = importlib.util.spec_from_file_location("decode_pmu_evidence_test", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("capture,fixture,lines,populations", [
    ("a3_qwen35", "mixed_step_body/a3_qwen35.csv", [8], [(1, 0), (2, 1)]),
    ("a3_qwen36", "mixed_step_body/a3_qwen36.csv", [9, 16], [(1, 1), (4, 1)]),
    ("a3_v4pro", "fusion_contracts/a3_v4pro.csv", [38, 55], [(None, 1), (None, 1)]),
])
def test_original_capture_rows_keep_units_and_nonselected_population(
        evidence, capture, fixture, lines, populations):
    path = ROOT / "tests/fixtures" / fixture
    with path.open(newline="") as stream:
        originals = {line: row for line, row in enumerate(csv.DictReader(stream), 2)}
    result = evidence.analyze_capture(path, evidence.REQUESTS[capture])
    assert result["source_row_count"] == len(originals)
    assert result["positive_event_count"] == len(originals)
    assert result["invalid_timing_rows"] == 0
    assert [(row["query_rows"], row["event_count"])
            for row in result["requested_populations"]] == populations
    groups = {group["source_rows"]["first"]: group for group in result["groups"]}
    assert set(groups) == set(lines)
    assert sum(result["operator_counts"].values()) == len(originals)
    for line, group in groups.items():
        raw = originals[line]
        assert group["event_count"] == 1
        assert group["source_rows"]["sample"] == [line]
        assert group["duration"]["mean"] == pytest.approx(float(raw["Duration(us)"]) * 1000)
        block, = group["block_configurations"]
        assert block["block_num"] == int(raw["Block Num"])
        assert block["mix_block_num"] == int(raw["Mix Block Num"])
        assert block["event_count"] == 1
        for metric in group["pmu"].values():
            original_value = float(raw[metric["source_column"]])
            assert metric["mean"] == pytest.approx(
                original_value * metric["source_to_normalized_scale"])
            assert metric["present_count"] == 1 and metric["missing_count"] == 0
            assert metric["zero_count"] == int(original_value == 0)
            assert sum(bucket["count"] for bucket in metric["histogram"]) == 1
        assert group["pmu"]["aic_mac_time"]["normalized_unit"] == "ns"
        assert group["pmu"]["aic_total_cycles"]["normalized_unit"] == "cycles"
        assert group["pmu"]["aic_mac_ratio"]["normalized_unit"] == "ratio"
        assert group["pmu"]["cube_utilization_pct"]["normalized_unit"] == "percent"
    if capture == "a3_v4pro":
        post = next(group for group in groups.values()
                    if group["descriptor"]["native_operator_type"] == "HcPost")
        assert post["pmu"]["aic_mac_time"]["mean"] == 0
        assert post["pmu"]["aic_mac_time"]["missing_count"] == 0
        assert post["pmu"]["aiv_vec_time"]["mean"] > 0


def test_log_histogram_tracks_real_pmu_variation_without_retaining_event_values(evidence):
    path = ROOT / "tests/fixtures/mixed_step_body/a3_qwen36.csv"
    with path.open(newline="") as stream:
        rows = [row for row in csv.DictReader(stream)
                if row["Type"] == "FusedInferAttentionScore"]
    values = [float(row["aic_mac_time(us)"]) * 1000 for row in rows]
    distribution = evidence.Distribution()
    for value in values:
        distribution.add(value)
    result = distribution.result(len(values))
    assert result["mean"] == pytest.approx(sum(values) / len(values))
    assert result["min"] == min(values) and result["max"] == max(values)
    assert sum(bucket["count"] for bucket in result["histogram"]) == len(values)
    expected_variance = sum((value - result["mean"]) ** 2 for value in values) / len(values)
    assert result["population_stddev"] ** 2 == pytest.approx(expected_variance)
    for value in values:
        containing = [bucket for bucket in result["histogram"]
                      if "lower_inclusive" in bucket
                      and bucket["lower_inclusive"] <= value
                      and (bucket["upper_exclusive"] is None or value < bucket["upper_exclusive"])]
        assert len(containing) == 1
