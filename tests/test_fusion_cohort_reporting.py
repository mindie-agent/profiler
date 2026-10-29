"""Per-call accuracy accounting over retained full-capture cohort projections."""
import importlib
import json
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "examples/structure/acceptance-20261029"


@pytest.fixture
def reporting(monkeypatch):
    pytest.importorskip("mindie_sim.cohort_accuracy", reason="requires matching optional sim source")
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return importlib.import_module("fusion_cohort_reporting")


def _inputs(declaration, *kinds):
    """Retain the original family and cohort records, without another export."""
    prefix = ARTIFACTS / f"fusion-cohort-{declaration}"
    mapping = json.loads(prefix.with_suffix(".mapping.json").read_text())
    comparison = json.loads(prefix.with_suffix(".comparison.json").read_text())
    windows = [
        {"operators": [row for row in window["operators"] if row["operator_type"] in kinds]}
        for window in mapping["windows"]
    ]
    compared_windows = [
        {"cohorts": [row for row in window["cohorts"] if row["native_operator_type"] in kinds]}
        for window in comparison["windows"]
    ]
    return {"graph_id": mapping["graph_id"], "windows": windows}, {"windows": compared_windows}


def test_real_kimi_mixed_tiers_use_call_weights_without_hiding_failed_cohort(reporting):
    mapping, comparison = _inputs("a5_kimi_k3_decode-reference", "MatMulV3")
    table = reporting.family_table(mapping, comparison)
    family, = table["families"]
    assert family["scored_event_count"] == 8838
    assert family["observed_per_call_us"] == pytest.approx(14.033235913102512)
    assert family["predicted_per_call_us"] == pytest.approx(8.577709290444176)
    assert family["per_call_diff_us"] == pytest.approx(-5.455526622658336)
    assert family["abs_error_per_call_us"] == pytest.approx(5.455526622658336)
    # The weighted family difference is small, but the slow 67-call cohort
    # fails the relative tier; thousands of passing short calls cannot erase it.
    assert abs(family["per_call_diff_us"]) < 15
    assert family["accuracy_pass"] is False
    by_count = {row["observed"]["event_count"]: row for row in family["cohorts"]}
    assert set(by_count) == {67, 6973, 1798}
    assert by_count[67]["observed_per_call_us"] == pytest.approx(92.20841791044776)
    assert by_count[67]["predicted_per_call_us"] == pytest.approx(73.97828344242427)
    assert by_count[67]["accuracy_pass"] is False
    assert by_count[6973]["accuracy_pass"] is True
    assert by_count[1798]["accuracy_pass"] is True
    tiers = family["accuracy_by_tier"]
    assert len(tiers) == 2
    short = tiers[by_count[6973]["accuracy_tier"]]
    long = tiers[by_count[67]["accuracy_tier"]]
    assert short["scored_event_count"] == short["passed_event_count"] == 8771
    assert short["cohort_count"] == short["passed_cohort_count"] == 2
    assert short["failed_event_count"] == short["failed_cohort_count"] == 0
    assert short["accuracy_pass"] is True
    assert long["scored_event_count"] == long["failed_event_count"] == 67
    assert long["cohort_count"] == long["failed_cohort_count"] == 1
    assert long["passed_event_count"] == long["passed_cohort_count"] == 0
    assert long["accuracy_pass"] is False


def test_real_small_glm_kernels_pass_absolute_tier_despite_large_relative_error(reporting):
    mapping, comparison = _inputs("a3_glm53_decode-reference", "DynamicQuant")
    family, = reporting.family_table(mapping, comparison)["families"]
    assert family["scored_event_count"] == 17316
    assert family["observed_per_call_us"] == pytest.approx(2.9131344421344423)
    assert family["predicted_per_call_us"] == pytest.approx(0.011802307692307694)
    assert family["relative_activity_error"] < -0.99
    assert family["accuracy_pass"] is True
    assert all(row["accuracy_pass"] for row in family["cohorts"])
    assert all(row["accuracy_status"] == "within_launch_floor_tolerance"
               for row in family["cohorts"])
    tier, = (row for row in family["accuracy_by_tier"].values() if row["cohort_count"])
    assert tier["cohort_count"] == tier["passed_cohort_count"] == 3
    assert tier["scored_event_count"] == tier["passed_event_count"] == 17316
    assert tier["failed_cohort_count"] == tier["failed_event_count"] == 0


def test_real_partial_program_reference_keeps_counts_out_of_accuracy_denominator(reporting):
    mapping, comparison = _inputs(
        "a3_glm53_decode-reference", "DynamicQuant", "GroupedMatmul")
    table = reporting.family_table(mapping, comparison)
    families = {row["operator_type"]: row for row in table["families"]}
    reference = families["GroupedMatmul"]
    assert reference["event_count"] == reference["reference_event_count"] == 5550
    assert reference["scored_event_count"] == 0
    assert reference["reference_activity_sum_ms"] > 0
    assert reference["predicted_reference_activity_sum_ms"] > 0
    assert reference["accuracy_pass"] is None
    assert all(row["cohort_count"] == row["scored_event_count"] == 0
               for row in reference["accuracy_by_tier"].values())
    row, = reference["cohorts"]
    assert row["status"] == "reference_only"
    assert row["reason"] == "quantized_epilogue_unmodeled"
    assert row["comparison"] is None
    assert row["accuracy_pass"] is None
    assert sum(tier["scored_event_count"] for family in families.values()
               for tier in family["accuracy_by_tier"].values()) == 17316
    assert sum(tier["scored_event_count"] for tier in table["accuracy_summary"].values()) == 17316


def test_real_small_passes_stay_out_of_error_sections_while_large_failures_lead(
    reporting, tmp_path,
):
    declaration = "a3_glm53_decode-reference"
    mapping, comparison = _inputs(declaration, "DynamicQuant", "SparseFlashAttention")
    table = reporting.family_table(mapping, comparison)
    assert [row["operator_type"] for row in table["families"]] == [
        "SparseFlashAttention", "DynamicQuant"]
    original_summary = ARTIFACTS / f"fusion-cohort-{declaration}.json"
    summary = json.loads(original_summary.read_text())
    (tmp_path / original_summary.name).write_text(json.dumps(summary))
    (tmp_path / original_summary.with_suffix(".families.json").name).write_text(json.dumps(table))
    reporting.write_family_overview(
        SimpleNamespace(output_dir=tmp_path, compare_existing=False),
        [{"capture_key": summary["capture_key"], "reports": [{"report": original_summary.name}]}],
    )
    text = (tmp_path / "fusion-cohort-replay-top-errors.md").read_text()
    large = text.split("### Large-call errors:", 1)[1].split("### Small-call errors:", 1)[0]
    small = text.split("### Small-call errors:", 1)[1].split("### Within tolerance:", 1)[0]
    passing = text.split("### Within tolerance:", 1)[1].split("### Unscored coverage:", 1)[0]
    assert "| SparseFlashAttention |" in large
    assert "| DynamicQuant |" not in large
    assert "| DynamicQuant |" not in small
    assert "| DynamicQuant |" in passing
    assert "| SparseFlashAttention |" not in passing


def test_same_real_family_tier_renders_disjoint_pass_and_fail_statistics(reporting):
    declaration = "a3_glm53_prefill-reference"
    mapping, comparison = _inputs(declaration, "QuantBatchMatmulV3")
    table = reporting.family_table(mapping, comparison)
    family, = table["families"]
    assert family["scored_event_count"] == 180
    tier = family["accuracy_by_tier"]["relative_15pct"]
    assert tier["passed_cohort_count"] == 4
    assert tier["failed_cohort_count"] == 1
    before = json.dumps(table, sort_keys=True)
    summary = json.loads((ARTIFACTS / f"fusion-cohort-{declaration}.json").read_text())
    text = "\n".join(reporting._variant_markdown(summary, table))
    assert json.dumps(table, sort_keys=True) == before
    errors = text.split("### Large-call errors:", 1)[1].split("### Small-call errors:", 1)[0]
    passing = text.split("### Within tolerance:", 1)[1].split("### Unscored coverage:", 1)[0]

    def rendered_row(section):
        header = next(line for line in section.splitlines() if line.startswith("| Native family |"))
        row, = (line for line in section.splitlines() if line.startswith("| QuantBatchMatmulV3 |"))
        return dict(zip(
            (field.strip() for field in header.strip("|").split("|")),
            (field.strip() for field in row.strip("|").split("|")),
        ))

    failed, passed = rendered_row(errors), rendered_row(passing)
    assert int(failed["Scored events"]) == 75
    assert int(passed["Scored events"]) == 105
    assert int(failed["Scored events"]) + int(passed["Scored events"]) == family["scored_event_count"]
    assert failed["Pass / fail cohorts"] == "0 / 1"
    assert passed["Pass / fail cohorts"] == "4 / 0"
    for row, observed, predicted, relative in (
        (failed, 242.87066666666666, 102.97840484848437, -0.5759948854185037),
        (passed, 267.03175238095235, 253.00695882251415, -0.052521070746785914),
    ):
        assert float(row["Observed us/call"]) == pytest.approx(observed, abs=0.00051)
        assert float(row["Predicted us/call"]) == pytest.approx(predicted, abs=0.00051)
        assert float(row["Per-call diff us"]) == pytest.approx(predicted - observed, abs=0.00051)
        assert float(row["Relative error"].removesuffix("%")) / 100 == pytest.approx(
            relative, abs=0.00051)


def test_accuracy_refresh_preserves_real_metrics_and_updates_verified_artifact_hashes(
    reporting, tmp_path, monkeypatch,
):
    from mindie_profiler.sources_csv import CsvSource
    from mindie_sim import cohort_comparison, structure
    from mindie_sim.cohort_accuracy import accuracy_fields

    refresh = importlib.import_module("fusion_cohort_refresh")

    def unexpected_execution(*args, **kwargs):
        raise AssertionError("accuracy refresh scanned raw data or executed prediction")

    monkeypatch.setattr(CsvSource, "iter_events", unexpected_execution)
    monkeypatch.setattr(cohort_comparison, "compare_cohorts", unexpected_execution)
    monkeypatch.setattr(structure, "export_structure", unexpected_execution)
    name = "fusion-cohort-a3_glm53_decode-reference.json"
    summary = json.loads((ARTIFACTS / name).read_text())
    historical = json.loads((ARTIFACTS / "fusion-cohort-validation.json").read_text())
    capture = next(row for row in historical["captures"] if row["capture_key"] == summary["capture_key"])
    reference = next(row for row in capture["reports"] if row["report"] == name)
    summary.pop("accuracy_evaluation", None)
    summary["artifacts"] = {
        key: value for key, value in summary["artifacts"].items()
        if key in {"mapping", "case", "comparison", "families"}
    }
    for record in summary["artifacts"].values():
        (tmp_path / record["file"]).write_bytes((ARTIFACTS / record["file"]).read_bytes())
    comparison_path = tmp_path / summary["artifacts"]["comparison"]["file"]
    comparison = json.loads(comparison_path.read_text())
    comparison.pop("accuracy_policy", None)
    comparison.pop("accuracy_evaluation", None)
    for window in comparison["windows"]:
        for row in window["cohorts"]:
            for field in accuracy_fields(row):
                row.pop(field, None)
    comparison_path.write_text(json.dumps(comparison, separators=(",", ":")) + "\n")

    def identity(path):
        return {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size}

    def metrics(value):
        return json.dumps([
            {key: row[key] for key in ("observed", "prediction", "comparison")}
            for window in value["windows"] for row in window["cohorts"]
        ], sort_keys=True, separators=(",", ":"))

    original_metrics = metrics(comparison)
    summary["artifacts"]["comparison"] = identity(comparison_path)
    original_artifacts = dict(summary["artifacts"])
    (tmp_path / name).write_text(json.dumps(summary))
    receipt_path = tmp_path / "fusion-cohort-validation.json"
    receipt_path.write_text(json.dumps({
        "status": historical["status"],
        "captures": [{"capture_key": capture["capture_key"], "reports": [reference]}],
    }))
    original_receipt = receipt_path.read_bytes()
    refresh.refresh_accuracy(
        SimpleNamespace(output_dir=tmp_path, compare_existing=False),
        runtime_identity=lambda: {}, rss=lambda: 0,
    )
    updated = json.loads(comparison_path.read_text())
    assert metrics(updated) == original_metrics
    assert receipt_path.read_bytes() == original_receipt
    updated_summary = json.loads((tmp_path / name).read_text())
    assert updated_summary["artifacts"]["comparison"] == identity(comparison_path)
    assert updated_summary["artifacts"]["comparison"] != original_artifacts["comparison"]
    for key in ("mapping", "case"):
        assert identity(tmp_path / original_artifacts[key]["file"]) == original_artifacts[key]
    assert updated_summary["artifacts"]["families"] == identity(
        tmp_path / original_artifacts["families"]["file"])
    rows = [row for window in updated["windows"] for row in window["cohorts"]]
    references = [row for row in rows if row["status"] == "reference_only"]
    assert references
    assert all(row["comparison"] is None and row["accuracy_pass"] is None for row in references)
    assert all(row["accuracy_pass"] is not None for row in rows if row["status"] == "compared")
    validation = json.loads((tmp_path / "fusion-cohort-accuracy-validation.json").read_text())
    assert validation["status"] == "completed"
    assert validation["variant_count"] == 1
    assert validation["original_metrics_unchanged"] is True
    assert validation["raw_capture_reads"] == validation["prediction_executions"] == 0
