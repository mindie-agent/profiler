"""Cross-check prioritization against recorded cohort activity arithmetic."""
import importlib
import json
from pathlib import Path

import pytest


def test_real_cohort_priority_uses_complete_forward_and_per_call_tier(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    source = root / "examples/structure/acceptance-20261030-high-concurrency/body-operator-family-scoreboard.json"
    if not source.exists():
        pytest.skip("recorded acceptance campaign is available in the source checkout")
    receipt = json.loads(source.read_text())
    families, rows = module.operator_rows(receipt, {"path": str(source)})
    original = {(case["case_id"], cohort["cohort_id"]): (case["forward_count"], cohort)
                for case in receipt["cases"] for family in case["families"]
                for cohort in family["cohorts"] if cohort["status"] == "compared"}
    assert len(rows) == len(original) == 168
    for row in rows:
        forwards, cohort = original[row["case_id"], row["cohort_id"]]
        activity = cohort["comparison"]["activity_sum"]["signed_residual_ms"]
        assert row["signed_activity_residual_ms_per_forward"] == pytest.approx(activity / forwards)
        assert row["heavy_call"] == (cohort["observed"]["duration_ns"]["mean"] > 50_000)
    unscored = [row for row in families if row["unscored_event_count"]]
    assert unscored and all(not row["missing_match_is_missing_cost"] for row in unscored)
    # Large cumulative micro-kernel activity must not be promoted into >50us.
    assert any(row["measured_activity_ms_per_forward"] > 1 and not row["heavy_call"] for row in rows)


def test_runtime_controls_replace_current_prediction_without_duplicating_real_forwards(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "examples/structure"))
    module = importlib.import_module("priority_decode_scoreboard")
    base = root / "examples/structure/acceptance-20261030-priority"
    old = base / "decode-forward-second-wave-replay.json"
    update = base / "decode-forward-glm-runtime-controls-replay.json"
    before = module.build([old], [])
    after = module.build([old, update], [])
    cases = {row["case_id"]: row for row in after["current_body_comparisons"]}
    b8 = next(row for key, row in cases.items() if key.startswith("a3_glm53_dc4k_b8")
              and row["comparison"]["status"] == "compared")
    assert b8["comparison"]["passed"]
    assert b8["comparison"]["predicted_ms"] == pytest.approx(44.050191, abs=1e-6)
    # Runtime controls include three genuinely different GLM45 sources as well
    # as two repeated GLM78 populations. Only the three new sources add samples.
    originals = {row["source_identity"]["sha256"] for row in before["body_comparisons"]}
    new = module.build([update], [])
    new_populations = [row for row in new["current_body_comparisons"]
                       if row["source_identity"]["sha256"] not in originals]
    assert after["summary"]["unique_observed_forward_count"] == (
        before["summary"]["unique_observed_forward_count"]
        + sum(row["comparison"]["observed_ms"]["count"] for row in new_populations))
