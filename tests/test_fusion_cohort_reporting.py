"""Historical reporting math plus invariance when refreshing current artifacts."""
from collections import Counter
import importlib
import json
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "examples/structure/acceptance-20261029"
HISTORICAL = ROOT / "tests/fixtures/fusion_reporting/historical-cohorts.json"


@pytest.fixture
def reporting(monkeypatch):
    pytest.importorskip("mindie_sim.cohort_accuracy", reason="requires matching optional sim source")
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    return importlib.import_module("fusion_cohort_reporting")


def _historical(declaration):
    """Fixed reporting counterexamples must survive improvements to prediction."""
    return json.loads(HISTORICAL.read_text())["declarations"][declaration]


def _inputs(declaration, *kinds):
    original = _historical(declaration)
    mapping, comparison = original["mapping"], original["comparison"]
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
    summary_path = tmp_path / f"fusion-cohort-{declaration}.json"
    summary = _historical(declaration)["summary"]
    summary_path.write_text(json.dumps(summary))
    summary_path.with_suffix(".families.json").write_text(json.dumps(table))
    reporting.write_family_overview(
        SimpleNamespace(output_dir=tmp_path, compare_existing=False),
        [{"capture_key": summary["capture_key"], "reports": [{"report": summary_path.name}]}],
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
    summary = _historical(declaration)["summary"]
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


def test_fixed_replay_totals_exclude_references_and_reject_mixed_summary_generation(
    reporting, tmp_path,
):
    large = importlib.import_module("report_large_cohort_errors")
    fixture = json.loads(HISTORICAL.read_text())
    captures, all_rows = [], []
    events_by_source = {}

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")
        return {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size}

    for name, original in fixture["declarations"].items():
        mapping, comparison = original["mapping"], original["comparison"]
        table = reporting.family_table(mapping, comparison)
        prefix = "fusion-cohort-" + name
        summary = original["summary"]
        summary["artifacts"] = {
            key: write(prefix + "." + key + ".json", value)
            for key, value in (
                ("case", original["case"]), ("mapping", mapping),
                ("comparison", comparison), ("families", table))
        }
        identity = write(prefix + ".json", summary)
        captures.append({
            "capture_key": summary["capture_key"],
            "source_identity": summary["source_identity"],
            "reports": [{"report": identity["file"], "summary_identity": identity}],
        })
        events_by_source[summary["source_identity"]["sha256"]] = summary["positive_event_count"]
        all_rows.extend(row for window in comparison["windows"] for row in window["cohorts"])

    # The population is a projection of fixed real replay artifacts. Its
    # measured/predicted values stay unchanged; only counts and file receipts
    # are recomputed for the selected declarations and native families.
    receipt = {
        **fixture["report_receipt"], "captures": captures,
        "declaration_variant_count": len(captures),
        "distinct_captured_sources": len(events_by_source),
        "unique_capture_event_count": sum(events_by_source.values()),
        "comparison_cohort_status_counts": dict(Counter(row["status"] for row in all_rows)),
    }
    write("fusion-cohort-validation.json", receipt)
    reporting.write_family_overview(
        SimpleNamespace(output_dir=tmp_path, compare_existing=False), captures)
    reporting.write_full_replay_summary(tmp_path, receipt)
    report = large.build_report(tmp_path, "observed_activity")
    top_text = (tmp_path / "fusion-cohort-replay-top-errors.md").read_text()
    full_text = (tmp_path / "cohort-full-family-replay.md").read_text()
    large_text = large._markdown(report)

    assert "| All scored | 12 | 9 | 3 |" in top_text
    assert "| All scored | Each cohort's own tier | 9 / 12 | 3 |" in full_text
    assert "| All scored | 9 / 12 | 3 |" in large_text
    assert report["accuracy_summary_across_variants"] == {
        "relative_15pct": {"cohort_count": 7, "passed_cohort_count": 4, "failed_cohort_count": 3},
        "absolute_15us": {"cohort_count": 5, "passed_cohort_count": 5, "failed_cohort_count": 0},
    }
    assert report["totals_across_variants"]["reference_cohort_count"] == 1
    assert report["totals_across_variants"]["reference_event_count"] == 5550
    assert report["reference_by_reason"]["quantized_epilogue_unmodeled"]["event_count"] == 5550
    expected = {row["cohort_id"] for row in all_rows
                if row["status"] == "compared" and row["accuracy_pass"] is False
                and row["accuracy_tier"] == "relative_15pct"}
    assert {row["cohort_id"] for row in report["cohorts"]} == expected
    assert all(row["observed_per_call_us"] > 50 for row in report["cohorts"])

    # A newer summary can have valid artifact hashes yet belong to a different
    # generation. Both consumers must reject it before trusting its contents.
    changed = fixture["declarations"]["a3_glm53_decode-reference"]["summary"]
    changed["graph_id"] = fixture["declarations"]["a3_glm53_prefill-reference"]["summary"]["graph_id"]
    write("fusion-cohort-a3_glm53_decode-reference.json", changed)
    with pytest.raises(ValueError, match="summary_generation_mismatch"):
        large.build_report(tmp_path, "observed_activity")
    with pytest.raises(ValueError, match="summary_generation_mismatch"):
        reporting.write_full_replay_summary(tmp_path, receipt)
    assert (tmp_path / "cohort-full-family-replay.md").read_text() == full_text


@pytest.mark.parametrize("stale_artifact", ["overview", "families"])
def test_same_count_historical_generations_cannot_replace_current_scoreboard(
    reporting, tmp_path, stale_artifact,
):
    fixture = json.loads(HISTORICAL.read_text())

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value, separators=(",", ":"), allow_nan=False) + "\n")
        return {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size}

    def generation(declaration, kind):
        original = fixture["declarations"][declaration]
        mapping = {
            **original["mapping"],
            "windows": [{
                **window,
                "operators": [row for row in window["operators"]
                              if row["operator_type"] == kind],
                "cohorts": [row for row in window.get("cohorts", [])
                            if row["native_operator_type"] == kind],
            } for window in original["mapping"]["windows"]],
        }
        comparison = {
            **original["comparison"],
            "windows": [{
                **window,
                "cohorts": [row for row in window["cohorts"]
                            if row["native_operator_type"] == kind],
            } for window in original["comparison"]["windows"]],
        }
        rows = [row for window in comparison["windows"] for row in window["cohorts"]]
        table = reporting.family_table(mapping, comparison)
        prefix = "fusion-cohort-" + declaration
        summary = {
            **original["summary"],
            "comparison": {
                **original["summary"]["comparison"],
                "status_counts": dict(Counter(row["status"] for row in rows)),
            },
            "artifacts": {
                key: write(prefix + "." + key + ".json", value)
                for key, value in (
                    ("case", original["case"]), ("mapping", mapping),
                    ("comparison", comparison), ("families", table))
            },
        }
        identity = write(prefix + ".json", summary)
        capture = {
            "capture_key": summary["capture_key"],
            "source_identity": summary["source_identity"],
            "reports": [{"report": identity["file"], "summary_identity": identity}],
        }
        receipt = {
            **fixture["report_receipt"], "captures": [capture],
            "declaration_variant_count": 1, "distinct_captured_sources": 1,
            "unique_capture_event_count": summary["positive_event_count"],
            "comparison_cohort_status_counts": dict(Counter(row["status"] for row in rows)),
        }
        reporting.write_family_overview(
            SimpleNamespace(output_dir=tmp_path, compare_existing=False), [capture])
        reporting.write_full_replay_summary(tmp_path, receipt)
        return receipt, summary, table

    # Both projections retain unedited real cohort rows and have three compared
    # cohorts. The old Kimi generation has one failed large call; the current
    # GLM DynamicQuant generation passes all three short-call cohorts.
    old_receipt, old_summary, old_table = generation(
        "a5_kimi_k3_decode-reference", "MatMulV3")
    overview_path = tmp_path / "fusion-cohort-replay-families.json"
    old_overview = overview_path.read_bytes()
    old_family = (tmp_path / old_summary["artifacts"]["families"]["file"]).read_bytes()
    current_receipt, current_summary, current_table = generation(
        "a3_glm53_decode-reference", "DynamicQuant")
    assert old_receipt["comparison_cohort_status_counts"] == (
        current_receipt["comparison_cohort_status_counts"]) == {"compared": 3}
    assert sum(tier["passed_cohort_count"] for tier in old_table["accuracy_summary"].values()) == 2
    assert sum(tier["passed_cohort_count"] for tier in current_table["accuracy_summary"].values()) == 3
    output = tmp_path / "cohort-full-family-replay.md"
    correct_output = output.read_bytes()

    if stale_artifact == "overview":
        overview_path.write_bytes(old_overview)
        error = "overview_generation_mismatch"
    else:
        (tmp_path / current_summary["artifacts"]["families"]["file"]).write_bytes(old_family)
        error = "artifact_identity_mismatch"
    with pytest.raises(ValueError, match=error):
        reporting.write_full_replay_summary(tmp_path, current_receipt)
    assert output.read_bytes() == correct_output


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
    # This successfully predicted declaration remains usable when a different
    # declaration in the live replay has timed out. Project its actual result;
    # never promote the status of the enclosing failed replay.
    assert summary["comparison"]["status"] == "completed"
    assert all(row["status"] in {"compared", "reference_only"}
               for window in comparison["windows"] for row in window["cohorts"])
    reference = {**reference, "summary_identity": identity(tmp_path / name)}
    receipt_path.write_text(json.dumps({
        "status": summary["comparison"]["status"],
        "captures": [{**capture, "reports": [reference]}],
        "declaration_variant_count": 1,
        "comparison_cohort_status_counts": dict(Counter(
            row["status"] for window in comparison["windows"] for row in window["cohorts"])),
        "projection_basis": "completed_declaration_subset_of_retained_replay",
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


def test_real_fia_timeout_is_visible_in_partial_reports_and_never_scored(reporting, tmp_path):
    large = importlib.import_module("report_large_cohort_errors")
    fixture = json.loads((HISTORICAL.parent / "prediction-timeout-cohorts.json").read_text())
    mapping, comparison, summary = (fixture[key] for key in ("mapping", "comparison", "summary"))
    table = reporting.family_table(mapping, comparison)
    failed = next(row for window in comparison["windows"] for row in window["cohorts"]
                  if row["status"] == "prediction_failed")
    assert [row["timeout_seconds"] for row in failed["prediction_failure"]["attempts"]] == [120, 300]

    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value, separators=(",", ":")) + "\n")
        return {"file": path.name, "sha256": sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size}

    prefix = "fusion-cohort-timeout-projection"
    summary["artifacts"] = {kind: write(prefix + "." + kind + ".json", value)
                            for kind, value in (("mapping", mapping), ("comparison", comparison),
                                                ("families", table))}
    identity = write(prefix + ".json", summary)
    captures = [{"capture_key": summary["capture_key"], "source_identity": summary["source_identity"],
                 "reports": [{"report": identity["file"], "summary_identity": identity}]}]
    receipt = {**fixture["report_receipt"], "captures": captures}
    write("fusion-cohort-validation.json", receipt)
    reporting.write_family_overview(SimpleNamespace(output_dir=tmp_path, compare_existing=False), captures)
    reporting.write_full_replay_summary(tmp_path, receipt)
    result = large.build_report(tmp_path, "observed_activity")
    assert result["status"] == "partial"
    assert result["totals_across_variants"]["cohort_status_counts"] == {"compared": 1, "prediction_failed": 1}
    assert sum(row["cohort_count"] for row in result["accuracy_summary_across_variants"].values()) == 1
    assert failed["cohort_id"] not in {row["cohort_id"] for row in result["cohorts"]}
    failure, = result["prediction_failures"]
    assert failure["observed_event_count"] == 17 and failure["accuracy_pass"] is None
    assert len(failure["failure"]["attempts"]) == 2
    assert "partial historical replay" in (tmp_path / "cohort-full-family-replay.md").read_text()
    assert "Partial prediction coverage" in (tmp_path / "fusion-cohort-replay-top-errors.md").read_text()
    assert "Report status: **partial**" in large._markdown(result)
    assert json.loads((tmp_path / "fusion-cohort-validation.json").read_text())["status"] == "failed"
