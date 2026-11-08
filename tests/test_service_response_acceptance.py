"""Acceptance must charge both residual signs; cancellation earns no credit.

[Role] Verify uncancelled L1 and signed relative error acceptance metrics.
[Invariants] Opposite-sign errors never cancel in uncancelled_L1.
[Timeouts & Locks] Tier 0 (<5s), no I/O or locks.
[Side-Effect Policy] Pure read-only in-memory unit tests.
"""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))

from service_response_acceptance import (  # noqa: E402
    AcceptanceError,
    acceptance_metrics,
    cancellation_mass,
    corpus_acceptance,
    evaluate_acceptance,
    native_call_acceptance,
    part_weight,
    require_acceptance,
    signed_relative_error,
    uncancelled_l1,
)


def parts(observed, predicted, counts=None):
    counts = counts or [1] * len(observed)
    return [
        {"id": f"part-{index}", "observed_ms": obs, "predicted_ms": pred,
         "count": count}
        for index, (obs, pred, count) in enumerate(zip(observed, predicted, counts))
    ]


def test_across_chunks_aggregate_zero_still_fails_uncancelled_acceptance():
    """Observations [100, 100], predictions [80, 120]: 0% aggregate, 20% L1."""
    ordered = parts([100.0, 100.0], [80.0, 120.0])
    metrics = acceptance_metrics(ordered)
    assert metrics["signed_relative_error"] == pytest.approx(0.0)
    assert metrics["uncancelled_L1"] == pytest.approx(0.20)
    assert metrics["cancellation_mass"] == pytest.approx(40.0)
    result = evaluate_acceptance(ordered, tolerance=0.10, label="chunk-trap")
    assert result["passed"] is False
    assert result["reason"] == "cancellation_dependent_aggregate"
    assert result["uncancelled_L1"] == pytest.approx(0.20)
    with pytest.raises(AcceptanceError, match="service_response_acceptance_failed"):
        require_acceptance(ordered, tolerance=0.10)


def test_across_operators_compensating_native_calls_fail_native_acceptance():
    """Native observations [4, 6], predictions [7, 3]: body total is right, L1 60%."""
    result = native_call_acceptance([4.0, 6.0], [7.0, 3.0], tolerance=0.10,
                                    label="operator-trap")
    assert result["signed_relative_error"] == pytest.approx(0.0)
    assert result["uncancelled_L1"] == pytest.approx(0.60)
    assert result["cancellation_mass"] == pytest.approx(6.0)
    assert result["passed"] is False
    assert result["reason"] == "cancellation_dependent_aggregate"

    corrected = native_call_acceptance([4.0, 6.0], [4.0, 6.0], tolerance=0.10)
    assert corrected["signed_relative_error"] == pytest.approx(0.0)
    assert corrected["uncancelled_L1"] == pytest.approx(0.0)
    assert corrected["cancellation_mass"] == pytest.approx(0.0)
    assert corrected["passed"] is True


def test_count_multiplicity_changes_population_and_worst_part_weighting():
    ordered = [
        {"id": "replayed", "observed_ms": 10.0, "predicted_ms": 20.0, "count": 9},
        {"id": "rare", "observed_ms": 90.0, "predicted_ms": 0.0, "count": 1},
    ]
    metrics = acceptance_metrics(ordered)
    # O = 90 + 90 = 180; P = 9 * 10 = 90; N = 1 * 90 = 90.
    assert metrics["observed_mass_ms"] == pytest.approx(180.0)
    assert metrics["positive_mass_ms"] == pytest.approx(90.0)
    assert metrics["negative_mass_ms"] == pytest.approx(90.0)
    assert metrics["signed_relative_error"] == pytest.approx(0.0)
    assert metrics["uncancelled_L1"] == pytest.approx(1.0)
    assert metrics["worst_part"]["index"] == 1
    assert metrics["total_count"] == 10

    reversed_counts = [
        {"id": "replayed", "observed_ms": 10.0, "predicted_ms": 20.0, "count": 1},
        {"id": "rare", "observed_ms": 90.0, "predicted_ms": 0.0, "count": 9},
    ]
    reweighted = acceptance_metrics(reversed_counts)
    # O = 10 + 810 = 820; P = 1 * 10 = 10; N = 9 * 90 = 810.
    assert reweighted["signed_relative_error"] == pytest.approx(-800.0 / 820.0)
    assert reweighted["uncancelled_L1"] == pytest.approx(1.0)


def test_part_weight_requires_declared_positive_integer_count():
    assert part_weight({"count": 3}) == 3
    for malformed in ({}, {"weight": 3}, {"count": 0}, {"count": -1},
                      {"count": 1.0}, {"count": True}, {"count": "2"}):
        with pytest.raises(AcceptanceError):
            part_weight(malformed)


def test_missing_prediction_is_incomplete_and_never_zero_error():
    missing = [{"id": "a", "observed_ms": 10.0, "count": 1},
               {"id": "b", "observed_ms": 10.0, "predicted_ms": 10.0, "count": 1}]
    result = evaluate_acceptance(missing, label="missing")
    assert result["status"] == "incomplete"
    assert result["passed"] is False
    assert "prediction" in result["reason"]
    with pytest.raises(AcceptanceError):
        acceptance_metrics(missing)


def test_missing_count_is_incomplete_and_never_defaulted():
    missing = [{"id": "a", "observed_ms": 10.0, "predicted_ms": 10.0}]
    result = evaluate_acceptance(missing, label="no-count")
    assert result["status"] == "incomplete"
    assert "count" in result["reason"]


def test_nonfinite_boolean_and_negative_observed_inputs_fail_explicitly():
    for malformed in (
        [{"observed_ms": float("nan"), "predicted_ms": 1.0, "count": 1}],
        [{"observed_ms": 1.0, "predicted_ms": float("inf"), "count": 1}],
        [{"observed_ms": True, "predicted_ms": 1.0, "count": 1}],
        [{"observed_ms": -1.0, "predicted_ms": 1.0, "count": 1}],
        [{"observed_ms": 0.0, "predicted_ms": 1.0, "count": 1}],
    ):
        result = evaluate_acceptance(malformed)
        assert result["status"] == "incomplete" and result["passed"] is False


def test_duplicate_display_ids_remain_distinct_ordered_parts():
    duplicate = [
        {"id": "same", "observed_ms": 100.0, "predicted_ms": 80.0, "count": 1},
        {"id": "same", "observed_ms": 100.0, "predicted_ms": 120.0, "count": 1},
    ]
    metrics = acceptance_metrics(duplicate)
    assert metrics["part_count"] == 2
    assert [row["index"] for row in metrics["parts"]] == [0, 1]
    assert metrics["uncancelled_L1"] == pytest.approx(0.20)


def test_audit_relative_error_parts_use_count_and_keep_cancellation_visible():
    # Mirrors the replay corpus: observed duration plus a declared residual.
    corpus_parts = [
        {"observed_ms": 100.0, "relative_error": -0.20, "count": 1},
        {"observed_ms": 100.0, "relative_error": 0.20, "count": 1},
    ]
    metrics = acceptance_metrics(corpus_parts)
    assert metrics["observed_mass_ms"] == pytest.approx(200.0)
    assert metrics["signed_relative_error"] == pytest.approx(0.0)
    assert metrics["uncancelled_L1"] == pytest.approx(0.20)
    assert signed_relative_error(corpus_parts) == pytest.approx(0.0)
    assert uncancelled_l1(corpus_parts) == pytest.approx(0.20)
    assert cancellation_mass(corpus_parts) == pytest.approx(40.0)


def test_same_sign_residuals_have_zero_cancellation_mass():
    ordered = parts([10.0, 20.0], [11.0, 22.0])
    metrics = acceptance_metrics(ordered)
    assert metrics["cancellation_mass"] == pytest.approx(0.0)
    assert metrics["signed_relative_error"] == pytest.approx(
        metrics["uncancelled_L1"])


def test_corpus_acceptance_fails_on_one_incomplete_or_failing_capture():
    good = evaluate_acceptance(parts([10.0], [10.0]), label="good")
    bad = evaluate_acceptance(parts([100.0, 100.0], [80.0, 120.0]),
                              label="bad")
    incomplete = evaluate_acceptance(
        [{"observed_ms": 1.0, "count": 1}], label="incomplete")
    summary = corpus_acceptance([good, bad, incomplete])
    assert summary["passed"] is False
    assert summary["failed_count"] == 1
    assert summary["incomplete_count"] == 1
    assert summary["failed_labels"] == ["bad"]
    assert summary["incomplete_labels"] == ["incomplete"]
    assert corpus_acceptance([good])["passed"] is True


def test_tolerance_boundary_is_inclusive_and_negative_tolerance_is_rejected():
    at_limit = parts([100.0], [110.0])
    assert evaluate_acceptance(at_limit, tolerance=0.10)["passed"] is True
    over_limit = parts([100.0], [110.0001])
    assert evaluate_acceptance(over_limit, tolerance=0.10)["passed"] is False
    with pytest.raises(AcceptanceError):
        evaluate_acceptance(at_limit, tolerance=-0.1)


def test_negative_individual_observation_unresolved_population_and_prefill_normalization():
    mixed_negative = [
        {"observed_ms": -1.0, "predicted_ms": 0.0, "count": 1},
        {"observed_ms": 100.0, "predicted_ms": 100.0, "count": 1},
    ]
    res = evaluate_acceptance(mixed_negative)
    assert res["status"] == "incomplete"
    assert res["passed"] is False

    unresolved = [
        {"observed_ms": 0.0307, "predicted_ms": 0.0307, "status": "unresolved", "count": 1},
    ]
    res_unres = evaluate_acceptance(unresolved)
    assert res_unres["status"] == "incomplete"
    assert res_unres["passed"] is False

    from wave5_generalization_eval import _normalize_case
    prefill_raw = {
        "traits": {"cell": "prefill-cell", "family": "deepseek", "phase": "prefill", "tp": 8},
        "status": "compared",
        "forward_count": 2,
        "observed_ms": 200.0,
        "predicted_ms": 200.0,
        "relative_error": 0.0,
        "passed_15pct": True,
        "passed_10pct": True,
        "ordered_parts": [
            {"observed_ms": 100.0, "predicted_ms": 80.0, "count": 1, "id": "prefill:0"},
            {"observed_ms": 100.0, "predicted_ms": 120.0, "count": 1, "id": "prefill:1"},
        ],
        "uncancelled_acceptance": evaluate_acceptance(
            [
                {"observed_ms": 100.0, "predicted_ms": 80.0, "count": 1, "id": "prefill:0"},
                {"observed_ms": 100.0, "predicted_ms": 120.0, "count": 1, "id": "prefill:1"},
            ],
            tolerance=0.10,
            label="prefill-cell",
        ),
    }
    norm = _normalize_case("a3", prefill_raw)
    assert norm["uncancelled_acceptance"]["passed"] is False
    assert norm["uncancelled_acceptance"]["uncancelled_L1"] == pytest.approx(0.20)
