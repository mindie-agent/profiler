"""Independently catch stale prediction and evidence-label drift in real focus rows."""
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def retained(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    reviewer = importlib.import_module("review_priority_decode_scoreboard")
    folder = root / "tests/fixtures/source_callers"
    data = json.loads((folder / "high-concurrency-focus.json").read_text())
    projection = json.loads((folder / "high-concurrency-focus-review.json").read_text())
    focus = projection["priority_focus"]
    spec = tmp_path / "focus.json"
    spec.write_text(json.dumps(data["focus_spec"]))
    focus["specification_identity"] = {"path": str(spec), "sha256": hashlib.sha256(spec.read_bytes()).hexdigest()}
    report = {"current_body_comparisons": projection["current"],
              "latest_body_attempts": deepcopy(projection["current"]), "priority_focus": focus}

    def review(value):
        failures = []
        reviewer.review_priority_focus(value, lambda ok, label: failures.append(label) if not ok else None)
        return failures

    return report, data, review


def test_real_thirteen_source_projection_rejects_inventory_prediction_and_hidden_timeout(retained):
    report, data, review = retained
    assert not review(report)
    stale = deepcopy(report)
    shown = next(row for row in stale["priority_focus"]["sources"]
                 if row["source_case_id"] == "qwen36-a5-tp2-c96")
    shown["predicted_body_ms"] = data["qwen96_previous"]["comparison"]["predicted_ms"]
    assert any("predicted_body_ms" in message for message in review(stale))
    hidden = deepcopy(report)
    hidden["latest_body_attempts"] = [data["qwen96_timeout"] if row["case_id"] == data["qwen96_timeout"]["case_id"]
                                      else row for row in hidden["latest_body_attempts"]]
    assert any("latest_execution_status" in message for message in review(hidden))
    assert report["priority_focus"]["summary"]["observed_forward_count"] == 877


def test_observed_in_sample_metadata_preserves_pass_but_cannot_be_invented(retained):
    report, _, review = retained
    current = next(row for row in report["current_body_comparisons"]
                   if row["case_id"].startswith("v4flash-a3-tp8-c4:"))
    shown = next(row for row in report["priority_focus"]["sources"]
                 if row["source_case_id"] == "v4flash-a3-tp8-c4")
    # Explicit metadata-only test projection; the retained historical timing
    # is unchanged and is not claimed to have used this calibration.
    current["calibration_origin"] = "observed"
    current["calibration_evidence"] = {"evaluation_relation": "in_sample",
        "fit_source_identity": current["source_identity"], "evaluation_source_identity": current["source_identity"]}
    shown["calibration"].update(origin="observed", evaluation_relation="in_sample",
                                evidence=current["calibration_evidence"])
    assert not review(report)
    assert shown["body_accuracy_status"] == "PASS"
    shown["calibration"]["evaluation_relation"] = "held_out"
    assert any("calibration evaluation_relation" in message for message in review(report))
