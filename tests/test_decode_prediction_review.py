"""Rejected real Body costs retain diagnostics without entering accuracy totals."""
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "examples/structure/acceptance-20261030-runtime5ec8843a/decode-forward-remaining-replay.json"


@pytest.mark.parametrize("promote_rejected_cost", [False, True])
def test_real_memory_failure_keeps_measurements_but_cannot_be_scored(
        tmp_path, monkeypatch, capsys, promote_rejected_cost):
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    reviewer = importlib.import_module("review_decode_predictions")
    report = json.loads(REPORT.read_text())
    failed = next(row for row in report["cases"]
                  if row["comparison"]["status"] == "failed")
    assert failed["prediction_execution"]["reason"] == "body_prediction_memory_budget_exceeded"
    assert failed["prediction_execution"]["execution"]["peak_rss_bytes"] > 512 * 1024**2
    assert failed["prediction"] is not None
    if promote_rejected_cost:
        failed["comparison"]["passed"] = True
    source = tmp_path / "report.json"
    source.write_text(json.dumps(report))
    output = tmp_path / "review.json"
    assert reviewer.review(source, output) is promote_rejected_cost
    review = json.loads(output.read_text())
    assert review["compared"] == 14 and review["passed"] == 9
    assert review["failed_attempts"][0]["observed_calls_retained"] == 63
    assert review["failed_attempts"][0]["diagnostic_prediction_retained"]
    if promote_rejected_cost:
        assert any("failed_attempt_is_not_scored" in failure
                   for failure in review["failures"])
    else:
        assert not review["failures"]
    capsys.readouterr()


def test_runtime_delta_retains_the_new_resource_failure(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "examples/structure"))
    delta = importlib.import_module("compare_body_runtime_arms")
    prior = ROOT / "examples/structure/acceptance-20261030-source-complete/decode-forward-remaining-replay.json"
    result = delta.compare([prior], [REPORT])
    assert result["summary"]["attempted_after"] == 15
    assert result["summary"]["compared_after"] == 14
    assert result["summary"]["failed_after"] == 1
    assert result["summary"]["passed_before"] == 10
    assert result["summary"]["passed_after"] == 9
    assert result["summary"]["became_failed"] == ["a5_kimi_k3_p32768_c1:q1_b1_m1"]
    failed = next(row for row in result["cases"] if row["after"]["status"] == "failed")
    assert failed["prediction_delta_ms"] is None
    assert failed["after"]["observed_ms"] == failed["before"]["observed_ms"]
