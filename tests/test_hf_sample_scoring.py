"""Focused tests for the exact keyed sample scorer.

The scorer is the single state machine used by the benchmark gate.  These tests
exercise the real observation parsers where they are cheap, and use compact
synthetic tables for the negative controls that real captures cannot supply
(duplicate keys, non-finite samples, missing hardware provenance).
"""
from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_sample_scoring as scoring  # noqa: E402
import fleet_capture_observations as observations  # noqa: E402


def _request_csv(path: Path, rows: list[dict[str, object]]) -> Path:
    fields = ["tag", "mode", "req_idx", "turn_idx", "concurrency", "isl", "osl_target",
              "ok", "status", "ttft_ms", "tpot_ms", "e2e_ms", "out_tokens",
              "itl_p50_ms", "itl_p90_ms", "itl_p99_ms", "prefix_cached", "error"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _request_observation(csv_path: Path, *, phase: str = "decode",
                          capture_id: str = "", hardware: str = "") -> dict:
    client = observations.parse_request_summary(csv_path)
    per_request = [row["tpot_ms"] if phase == "decode" else row["ttft_ms"]
                   for row in client["samples"] if row.get("ok")]
    capture: dict[str, object] = {"phase": phase}
    if capture_id:
        capture["capture_id"] = capture_id
    if hardware:
        capture["hardware_tier"] = hardware
    return {
        "capture": capture,
        "measurements": {
            "native_client_request": {
                "status": "measured",
                "boundary": "native_client_reported_request",
                "reported_tpot_ms": client["tpot_ms_median"],
                "reported_ttft_ms": client["ttft_ms_median"],
                "samples": client["samples"],
                "boundary_samples_ms": per_request,
            }
        },
    }


def _two_request_source(tmp_path: Path) -> Path:
    return _request_csv(tmp_path / "request_summary.csv", [
        {"tag": "cell", "mode": "decode", "req_idx": 0, "turn_idx": 1, "concurrency": 2,
         "isl": 1024, "osl_target": 2, "ok": 1, "status": 200, "ttft_ms": 10.0,
         "tpot_ms": 1.0, "e2e_ms": 12.0, "out_tokens": 2, "itl_p50_ms": 1.0,
         "itl_p90_ms": 1.0, "itl_p99_ms": 1.0},
        {"tag": "cell", "mode": "decode", "req_idx": 1, "turn_idx": 1, "concurrency": 2,
         "isl": 1024, "osl_target": 2, "ok": 1, "status": 200, "ttft_ms": 20.0,
         "tpot_ms": 99.0, "e2e_ms": 120.0, "out_tokens": 2, "itl_p50_ms": 99.0,
         "itl_p90_ms": 99.0, "itl_p99_ms": 99.0},
    ])


def _forward_observation(values: list[float], keys: list[str], *,
                          basis: str = "elapsed_window_span_ms") -> dict:
    return {
        "capture": {"phase": "decode"},
        "measurements": {
            "per_forward_window": {
                "status": "measured",
                "samples_ms": values,
                "sample_keys": keys,
                "samples_basis": basis,
            }
        },
    }


def _prediction(boundary: str, **kwargs: object) -> dict:
    return {"status": "predicted", "prediction_boundary": boundary, **kwargs}


# ---------------------------------------------------------------- request samples


def test_two_request_tpot_mean_is_not_a_per_request_pass(tmp_path: Path) -> None:
    source = _two_request_source(tmp_path)
    observation = _request_observation(source)
    assert observation["measurements"]["native_client_request"]["reported_tpot_ms"] == pytest.approx(50.0)

    scalar = scoring.score_boundary(
        _prediction("native_client_request", boundary_ms=50.0), observation)
    assert scalar["comparison"] == "invalid"
    assert scalar["reason"] == "aggregate_hides_per_sample_series"
    assert scalar["passed_10pct"] is False
    assert scalar["denominator"] == 2

    both_mid = scoring.score_boundary(
        _prediction("native_client_request", boundary_samples=[
            {"key": "req_idx=0", "boundary_ms": 50.0},
            {"key": "req_idx=1", "boundary_ms": 50.0}]), observation)
    assert both_mid["comparison"] == "compared"
    assert both_mid["passed_10pct"] is False
    assert both_mid["sample"] > 0.10

    exact = scoring.score_boundary(
        _prediction("native_client_request", boundary_samples=[
            {"key": "req_idx=0", "boundary_ms": 1.0},
            {"key": "req_idx=1", "boundary_ms": 99.0}]), observation)
    assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
    assert exact["n_samples"] == 2


def test_keyed_request_records_ignore_order(tmp_path: Path) -> None:
    observation = _request_observation(_two_request_source(tmp_path))
    forward = scoring.score_boundary(_prediction("native_client_request", boundary_samples=[
        {"key": "req_idx=0", "boundary_ms": 1.0},
        {"key": "req_idx=1", "boundary_ms": 99.0},
    ]), observation)
    reversed_records = scoring.score_boundary(_prediction("native_client_request", boundary_samples=[
        {"key": "req_idx=1", "boundary_ms": 99.0},
        {"key": "req_idx=0", "boundary_ms": 1.0},
    ]), observation)
    assert (forward["passed_10pct"], forward["sample"], forward["n_samples"]) == (
        reversed_records["passed_10pct"], reversed_records["sample"], reversed_records["n_samples"])
    assert reversed_records["worst_key"] == "req_idx=0"


def test_failed_request_stays_in_the_denominator(tmp_path: Path) -> None:
    source = _request_csv(tmp_path / "request_summary.csv", [
        {"tag": "cell", "mode": "decode", "req_idx": 0, "turn_idx": 1, "ok": 1,
         "status": 200, "ttft_ms": 10.0, "tpot_ms": 1.0, "e2e_ms": 12.0, "out_tokens": 2},
        {"tag": "cell", "mode": "decode", "req_idx": 1, "turn_idx": 1, "ok": 1,
         "status": 200, "ttft_ms": 20.0, "tpot_ms": 2.0, "e2e_ms": 22.0, "out_tokens": 2},
        {"tag": "cell", "mode": "decode", "req_idx": 2, "turn_idx": 1, "ok": 0,
         "status": 500, "error": "failed"},
    ])
    observation = _request_observation(source)
    result = scoring.score_boundary(_prediction(
        "native_client_request", boundary_samples=[{"key": "req_idx=0", "boundary_ms": 1.0},
                                                   {"key": "req_idx=1", "boundary_ms": 2.0}],
    ), observation)
    assert result["passed_10pct"] is False
    assert result["comparison"] == "invalid"
    assert result["reason"] in {"observation_sample_unmeasured", "sample_key_population_mismatch"}
    assert result["denominator"] == 3
    assert "req_idx=2" in result["missing_keys"]


# ------------------------------------------------------------- forward samples


def test_keyed_forward_records_ignore_order_and_preserve_score() -> None:
    keys = ["rank=0|forward_id=f0", "rank=0|forward_id=f1", "rank=0|forward_id=f2"]
    observation = _forward_observation([10.0, 20.0, 30.0], keys)
    predictions = [
        {"key": keys[0], "boundary_ms": 10.5},
        {"key": keys[1], "boundary_ms": 19.5},
        {"key": keys[2], "boundary_ms": 30.5},
    ]
    first = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=predictions), observation)
    second = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=list(reversed(predictions))), observation)
    assert first["comparison"] == second["comparison"] == "compared"
    assert first["passed_10pct"] == second["passed_10pct"] is True
    assert first["sample"] == second["sample"]
    assert first["n_samples"] == second["n_samples"] == 3
    # Reordering the measured records with their keys is also the same population.
    shuffled = _forward_observation([30.0, 10.0, 20.0], [keys[2], keys[0], keys[1]])
    third = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=predictions), shuffled)
    assert third["sample"] == first["sample"] and third["passed_10pct"] is True


def test_missing_duplicate_and_extra_keys_cannot_pass() -> None:
    keys = ["rank=0|forward_id=f0", "rank=0|forward_id=f1", "rank=0|forward_id=f2"]
    observation = _forward_observation([10.0, 20.0, 30.0], keys)
    missing = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": keys[0], "boundary_ms": 10.0}, {"key": keys[1], "boundary_ms": 20.0}]), observation)
    assert missing["passed_10pct"] is False and missing["reason"] == "sample_key_population_mismatch"
    assert missing["missing_keys"] == [keys[2]] and missing["denominator"] == 3

    duplicate = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": keys[0], "boundary_ms": 10.0}, {"key": keys[0], "boundary_ms": 10.0},
        {"key": keys[1], "boundary_ms": 20.0}]), observation)
    assert duplicate["passed_10pct"] is False
    assert duplicate["reason"] == "duplicate_prediction_sample_key"
    assert duplicate["duplicate_keys"] == [keys[0]]

    extra = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": keys[0], "boundary_ms": 10.0}, {"key": keys[1], "boundary_ms": 20.0},
        {"key": keys[2], "boundary_ms": 30.0}, {"key": "rank=0|forward_id=other", "boundary_ms": 1.0}]),
        observation)
    assert extra["passed_10pct"] is False
    assert extra["unmatched_keys"] == ["rank=0|forward_id=other"]

    duplicate_obs = _forward_observation([10.0, 20.0], [keys[0], keys[0]])
    dup_obs = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": keys[0], "boundary_ms": 10.0}]), duplicate_obs)
    assert dup_obs["reason"] == "duplicate_observation_sample_key"
    assert dup_obs["duplicate_keys"] == [keys[0]]


def test_invalid_value_and_length_controls() -> None:
    keys = ["a", "b"]
    observation = _forward_observation([10.0, 20.0], keys)
    non_finite = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": "a", "boundary_ms": float("nan")}, {"key": "b", "boundary_ms": 20.0}]), observation)
    assert non_finite["comparison"] == "invalid" and non_finite["reason"] == "non_finite"

    negative = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": "a", "boundary_ms": -1.0}, {"key": "b", "boundary_ms": 20.0}]), observation)
    assert negative["comparison"] == "invalid" and negative["reason"] == "negative_duration"

    zero = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": "a", "boundary_ms": 0.0}, {"key": "b", "boundary_ms": 20.0}]),
        _forward_observation([0.0, 20.0], keys))
    assert zero["comparison"] == "invalid" and zero["reason"] == "zero_observation"

    short = scoring.score_boundary(_prediction("per_forward_window", boundary_samples_ms=[10.0]),
                                   _forward_observation([10.0, 20.0], []))
    assert short["comparison"] == "invalid" and short["reason"] == "sample_population_length_mismatch"


def test_single_aggregate_is_not_a_per_forward_sample() -> None:
    result = scoring.score_boundary(
        _prediction("per_forward_window", boundary_ms=10.0),
        {"measurements": {"per_forward_window": {"status": "measured", "observed_ms": 10.0}}})
    assert result["passed_10pct"] is False
    assert result["reason"] == "per_forward_boundary_has_no_sample_series"
    assert result["denominator"] is None and result["missing_keys"] == []


def test_additive_class_mass_is_not_an_elapsed_forward() -> None:
    keys = ["a", "b"]
    additive = _forward_observation([10.0, 20.0], keys, basis="additive_class_sum_ms")
    elapsed_prediction = _prediction("per_forward_window", boundary_samples=[
        {"key": "a", "boundary_ms": 10.0}, {"key": "b", "boundary_ms": 20.0}])
    rejected = scoring.score_boundary(elapsed_prediction, additive)
    assert rejected["passed_10pct"] is False
    assert rejected["reason"] == "observation_basis_additive_class_mass_not_elapsed"

    additive_prediction = _prediction("per_forward_window_additive",
                                      boundary_basis="additive_class_sum_ms",
                                      boundary_samples=[
                                          {"key": "a", "boundary_ms": 10.0},
                                          {"key": "b", "boundary_ms": 20.0}])
    accepted = scoring.score_boundary(additive_prediction, additive)
    assert accepted["comparison"] == "compared" and accepted["passed_10pct"] is True

    elapsed = _forward_observation([10.0, 20.0], keys)
    wrong = scoring.score_boundary(_prediction("per_forward_window", boundary_basis="additive",
                                               boundary_samples=[
                                                   {"key": "a", "boundary_ms": 10.0},
                                                   {"key": "b", "boundary_ms": 20.0}]), elapsed)
    assert wrong["reason"] == "prediction_basis_additive_but_observation_is_elapsed"


# --------------------------------------------------------------- identities


def test_hardware_phase_and_rank_provenance() -> None:
    keys = ["a"]
    observed = _forward_observation([10.0], keys)
    observed["capture"].update({"capture_id": "registered_decode:cap", "hardware_tier": "A5"})
    missing_hw = dict(observed)
    missing_hw["capture"] = {"capture_id": "registered_decode:cap", "phase": "decode"}
    one = [{"key": "a", "boundary_ms": 10.0}]
    assert scoring.score_boundary(_prediction("per_forward_window", boundary_samples=one),
                                  missing_hw)["reason"] == "hardware_provenance_absent"
    assert scoring.score_boundary(_prediction("per_forward_window", boundary_samples=one),
                                  observed)["passed_10pct"] is True

    mismatch = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=one,
                                                  hardware_tier="A3"), observed)
    assert mismatch["comparison"] == "invalid" and mismatch["reason"] == "hardware_mismatch"
    phase = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=one,
                                               phase="prefill"), observed)
    assert phase["reason"] == "phase_mismatch"
    rank = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=one,
                                              rank_id=1),
                                  {**observed, "identity": {"rank_id": 2}})
    assert rank["reason"] == "rank_mismatch"
    rank_zero = scoring.score_boundary(
        _prediction("per_forward_window", boundary_samples=one, rank_id=9),
        {**observed, "identity": {"rank_id": 0}})
    assert rank_zero["comparison"] == "invalid" and rank_zero["reason"] == "rank_mismatch"


# ----------------------------------------------------------- operator groups


def _two_group_observation() -> dict:
    matrix, mix = scoring.operator_key("MatMulV3", "AI_CORE"), scoring.operator_key("QFFN", "MIX_AIC")
    return {"measurements": {"operator_groups": {
        matrix: {"status": "measured", "observed_ms": 10.0},
        mix: {"status": "measured", "observed_ms": 30.0},
    }}}


def test_two_observed_groups_require_both_and_reject_duplicates() -> None:
    observation = _two_group_observation()
    matrix, mix = scoring.operator_key("MatMulV3", "AI_CORE"), scoring.operator_key("QFFN", "MIX_AIC")
    both = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": mix, "boundary_ms": 30.0},
        {"key": matrix, "boundary_ms": 10.0},
    ]}, observation)
    assert both["comparison"] == "compared" and both["passed_10pct"] is True
    assert both["n_groups"] == 2 and both["denominator"] == 2

    omitted = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 10.0},
    ]}, observation)
    assert omitted["passed_10pct"] is False
    assert omitted["missing_keys"] == [mix]
    assert omitted["denominator"] == 2

    duplicated = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 10.0}, {"key": matrix, "boundary_ms": 10.0},
    ]}, observation)
    assert duplicated["passed_10pct"] is False
    assert duplicated["reason"] == "duplicate_or_blank_operator_group"

    extra = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 10.0}, {"key": mix, "boundary_ms": 30.0},
        {"key": scoring.operator_key("Unknown", "AI_CPU"), "boundary_ms": 1.0},
    ]}, observation)
    assert extra["passed_10pct"] is False
    assert extra["unmatched_keys"] == [scoring.operator_key("Unknown", "AI_CPU")]


def test_nested_duplicate_group_sample_keys_cannot_pass() -> None:
    observation = {"measurements": {"operator_groups": {
        "one": {"status": "measured", "samples_ms": [1.0], "sample_keys": ["one"]},
        "two": {"status": "measured", "samples_ms": [9.0], "sample_keys": ["two"]},
    }}}
    nested = {"status": "predicted", "operator_group_samples": [
        {"key": "one", "boundary_samples": [
            {"key": "one", "boundary_ms": 999.0}, {"key": "one", "boundary_ms": 1.0}]},
        {"key": "two", "boundary_samples": [{"key": "two", "boundary_ms": 9.0}]},
    ]}
    result = scoring.score_operator_groups(nested, observation)
    assert result["passed_10pct"] is False
    assert result["comparison"] == "invalid"
    assert result["reason"] == "duplicate_prediction_sample_key"


def test_operator_group_source_sha_mismatch_is_rejected() -> None:
    sha = "a" * 64
    observation = {"measurements": {"operator_groups": {
        "source_sha256": sha,
        "MatMulV3\x1fAI_CORE": {"status": "measured", "observed_ms": 1.0},
    }}}
    prediction = {"status": "predicted", "source_sha256": sha,
                  "operator_group_samples": [{"key": "MatMulV3\x1fAI_CORE",
                                              "boundary_ms": 1.0}]}
    assert scoring.score_operator_groups(prediction, observation)["passed_10pct"] is True
    mismatch = scoring.score_operator_groups(
        {**prediction, "source_sha256": "f" * 64}, observation)
    assert mismatch["comparison"] == "invalid"
    assert mismatch["reason"] == "source_sha256_mismatch"
    assert mismatch["n_pairs"] == 0


def test_positional_array_cannot_prove_a_keyed_observation() -> None:
    observation = _forward_observation([10.0, 20.0], ["rank=0|forward_id=f0", "rank=0|forward_id=f1"])
    result = scoring.score_boundary(
        _prediction("per_forward_window", boundary_samples_ms=[10.0, 20.0]), observation)
    assert result["passed_10pct"] is False
    assert result["reason"] == "prediction_samples_unkeyed_for_keyed_observation"
    assert result["denominator"] == 2


def test_operator_groups_permutation_is_score_invariant() -> None:
    observation = _two_group_observation()
    matrix, mix = scoring.operator_key("MatMulV3", "AI_CORE"), scoring.operator_key("QFFN", "MIX_AIC")
    forward = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 10.0}, {"key": mix, "boundary_ms": 30.0}]}, observation)
    reverse = scoring.score_operator_groups({"status": "predicted", "operator_group_samples": [
        {"key": mix, "boundary_ms": 30.0}, {"key": matrix, "boundary_ms": 10.0}]}, observation)
    assert forward["sample"] == reverse["sample"]
    assert forward["passed_10pct"] == reverse["passed_10pct"] is True
    assert forward["n_groups"] == reverse["n_groups"] == 2


def test_family_aggregate_is_not_promoted_to_operator_groups() -> None:
    observation = {"measurements": {"capture_op_statistic_aggregate": {
        "status": "measured", "families_us": {"gemm": {"duration_us": 1000.0}},
        "by_op_us": {"MatMulV3": 1000.0},
    }}}
    result = scoring.score_operator_groups({"status": "predicted",
                                            "predicted_by_core_ms": {"AI_CORE": 1.0}}, observation)
    assert result["comparison"] == "uncovered"
    assert result["reason"] == "operator_groups_absent"
    assert result["passed_10pct"] is False


def test_real_op_statistic_engine_table_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "op_statistic.csv"
    path.write_text(
        "OP Type,Core Type,Count,Total Time(us)\n"
        "MatMulV3,AI_CORE,2,100000.0\n"
        "MatMulV3,MIX_AIC,1,40000.0\n",
        encoding="utf-8",
    )
    summary = observations.parse_op_statistic_summary(path)
    observation = {"measurements": {"capture_op_statistic_aggregate": {
        "status": "measured", "by_op_engine": summary["by_op_engine"],
    }}}
    matrix, mix = scoring.operator_key("MatMulV3", "AI_CORE"), scoring.operator_key("MatMulV3", "MIX_AIC")
    predicted = {"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 100.0}, {"key": mix, "boundary_ms": 40.0}]}
    result = scoring.score_operator_groups(predicted, observation)
    assert result["comparison"] == "compared" and result["passed_10pct"] is True
    assert result["basis"] == "additive_op_engine_total_us"

    swapped = {"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 40.0}, {"key": mix, "boundary_ms": 100.0}]}
    failed = scoring.score_operator_groups(swapped, observation)
    assert failed["comparison"] == "compared" and failed["passed_10pct"] is False

    wrong_engine = {"status": "predicted", "operator_group_samples": [
        {"key": scoring.operator_key("MatMulV3", "AI_CPU"), "boundary_ms": 100.0},
        {"key": mix, "boundary_ms": 40.0}]}
    unmatched = scoring.score_operator_groups(wrong_engine, observation)
    assert unmatched["passed_10pct"] is False
    assert unmatched["missing_keys"] == [matrix]
    assert unmatched["unmatched_keys"] == [scoring.operator_key("MatMulV3", "AI_CPU")]


def test_elapsed_prediction_cannot_compare_to_additive_engine_mass() -> None:
    matrix = scoring.operator_key("MatMulV3", "AI_CORE")
    observation = {"measurements": {"capture_op_statistic_aggregate": {
        "status": "measured",
        "by_op_engine": {matrix: {"op_type": "MatMulV3", "core": "AI_CORE",
                                  "count": 2, "total_us": 100000.0}},
    }}}
    predicted = {"status": "predicted", "operator_group_samples": [
        {"key": matrix, "boundary_ms": 100.0, "basis": "elapsed_window_span_ms"}]}
    result = scoring.score_operator_groups(predicted, observation)
    assert result["passed_10pct"] is False
    assert result["reason"] == "prediction_basis_is_elapsed_but_operator_group_is_additive"


# ---------------------------------------------------------- positive control


def test_positive_control_independent_matching(tmp_path: Path) -> None:
    """A correct independent prediction on the same keys passes; corruption does not."""
    source = _request_csv(tmp_path / "request_summary.csv", [
        {"tag": "cell", "mode": "decode", "req_idx": 0, "turn_idx": 1, "ok": 1,
         "status": 200, "ttft_ms": 10.0, "tpot_ms": 10.0, "e2e_ms": 20.0, "out_tokens": 2},
        {"tag": "cell", "mode": "decode", "req_idx": 1, "turn_idx": 1, "ok": 1,
         "status": 200, "ttft_ms": 12.0, "tpot_ms": 20.0, "e2e_ms": 32.0, "out_tokens": 2},
        {"tag": "cell", "mode": "decode", "req_idx": 2, "turn_idx": 2, "ok": 1,
         "status": 200, "ttft_ms": 14.0, "tpot_ms": 30.0, "e2e_ms": 44.0, "out_tokens": 2},
    ])
    observation = _request_observation(source)
    # Independent reader: the predictor never reads the observation object.
    with source.open("r", encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    prediction_records = []
    for row in raw:
        if row["ok"] != "1":
            continue
        key = scoring.sample_key(req_idx=row["req_idx"])
        prediction_records.append({"key": key, "boundary_ms": float(row["tpot_ms"]) * 1.04})
    correct = scoring.score_boundary(
        _prediction("native_client_request", boundary_samples=list(reversed(prediction_records))),
        observation)
    assert correct["comparison"] == "compared" and correct["passed_10pct"] is True
    assert correct["denominator"] == 3 and correct["matched"] == 3

    corrupt = [dict(record) for record in prediction_records]
    corrupt[1]["boundary_ms"] = float(corrupt[1]["boundary_ms"]) * 2.0
    bad = scoring.score_boundary(_prediction("native_client_request", boundary_samples=corrupt), observation)
    assert bad["comparison"] == "compared" and bad["passed_10pct"] is False


# ------------------------------------------------------------- real source


_REAL_REQUEST = Path(
    "/Volumes/data/mindie-sim-data/a5/multinode-full-coverage-20261108/runs/"
    "r08_2n2427_qwen35_397b_w8a8_mxfp8_dp2_tp8_ep_131k/"
    "mixed_pd_multiturn_nocache_isl65536_c8/request_summary.csv"
)


@pytest.mark.skipif(not _REAL_REQUEST.is_file(), reason="real multinode source absent")
def test_real_request_source_requires_per_request_pairs(tmp_path: Path) -> None:
    with _REAL_REQUEST.open("r", encoding="utf-8", newline="") as handle:
        raw = list(csv.DictReader(handle))
    # The producer reuses req_idx across turns.  Keep the real first-turn rows;
    # a per-request key must retain turn identity when the producer emits it.
    turn_one = [row for row in raw if row["turn_idx"] == "1"]
    subset = _request_csv(tmp_path / "request_summary_turn1.csv", turn_one)
    observation = _request_observation(subset, phase="decode")
    samples = observation["measurements"]["native_client_request"]["samples"]
    assert len(samples) == 8
    aggregate = observation["measurements"]["native_client_request"]["reported_tpot_ms"]
    scalar = scoring.score_boundary(
        _prediction("native_client_request", boundary_ms=aggregate), observation)
    assert scalar["passed_10pct"] is False
    assert scalar["denominator"] == len(samples)

    # Independent raw CSV reader; keys and values never come from the observation object.
    records = [{"key": scoring.sample_key(req_idx=row["req_idx"]),
                "boundary_ms": float(row["tpot_ms"])} for row in turn_one]
    exact = scoring.score_boundary(
        _prediction("native_client_request", boundary_samples=list(reversed(records))), observation)
    assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
    assert exact["denominator"] == len(samples)


def test_nan_sample_is_never_a_zero_error() -> None:
    result = scoring.score_boundary(
        _prediction("per_forward_window", boundary_samples=[{"key": "a", "boundary_ms": float("nan")}]),
        _forward_observation([float("nan")], ["a"]))
    assert result["comparison"] == "invalid"
    assert result["passed_10pct"] is False
    assert math.isnan(result["sample"])


_REAL_FLEET = Path("/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl")
_CALIBRATION = Path("/Volumes/data/mindie-sim-data/calibration-20261107/a5")


@pytest.mark.skipif(not (_REAL_FLEET.is_file() and _CALIBRATION.is_dir()),
                    reason="real fleet/calibration source absent")
def test_real_per_forward_windows_are_keyed_and_scalar_mean_is_rejected() -> None:
    import json

    for line in _REAL_FLEET.open("r", encoding="utf-8"):
        row = json.loads(line)
        observation = observations.extract_capture_observations(row)
        window = observation["measurements"]["per_forward_window"]
        if (window.get("status") != "measured" or not window.get("window_source")
                or not 1 < int(window.get("window_count") or 0) <= 64):
            continue
        raw = json.loads(Path(window["window_source"]).read_text(encoding="utf-8"))
        data = raw.get("observed") if isinstance(raw.get("observed"), dict) else raw
        records = []
        for forward in data.get("forwards") or ():
            if not isinstance(forward, dict):
                continue
            body = forward.get("body") if isinstance(forward.get("body"), dict) else {}
            value = forward.get("body_forward_span_ms") or body.get("span_ms")
            if value is None:
                continue
            records.append({
                "key": scoring.sample_key(phase=forward.get("phase"),
                                          device_id=forward.get("device_id"),
                                          forward_id=forward.get("forward_id")),
                "boundary_ms": float(value),
            })
        assert records
        exact = scoring.score_boundary(_prediction(
            "per_forward_window",
            capture_id=observation["capture"]["capture_id"],
            phase=observation["capture"]["phase"],
            source_sha256=window.get("source_sha256") or window.get("raw_sha256"),
            boundary_samples=list(reversed(records))), observation)
        assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
        assert exact["denominator"] == int(window["window_count"])
        scalar = scoring.score_boundary(_prediction(
            "per_forward_window",
            capture_id=observation["capture"]["capture_id"],
            phase=observation["capture"]["phase"],
            source_sha256=window.get("source_sha256") or window.get("raw_sha256"),
            boundary_ms=sum(window["samples_ms"]) / len(window["samples_ms"])), observation)
        assert scalar["passed_10pct"] is False
        assert scalar["reason"] == "aggregate_hides_per_sample_series"
        return
    pytest.skip("no real per-forward capture with <=64 keyed windows")


@pytest.mark.skipif(not (_REAL_FLEET.is_file() and _CALIBRATION.is_dir()),
                    reason="real fleet/calibration source absent")
def test_real_fia_native_calls_identity_and_sha_mutation() -> None:
    """Actual E4 native_calls source; actual I3 per-call values; mutate only SHA."""
    import json

    row = None
    for line in _REAL_FLEET.open("r", encoding="utf-8"):
        candidate = json.loads(line)
        if str(candidate.get("capture_id") or "").endswith(
                "/fia_prefill_q8192_35b_tp4"):
            row = candidate
            break
    assert row is not None
    observation = observations.extract_capture_observations(row)
    calls = observation["measurements"]["native_calls"]
    assert calls["status"] == "measured" and calls["call_count"] == 3
    assert calls["samples_basis"] == "elapsed_native_call_span_ms"
    assert all(sample["engine"] == "UNKNOWN" and sample["engine_known"] is False
               for sample in calls["samples"])
    actual_source = calls["source_sha256"]
    assert actual_source == "47e8ad42742063ff6440e0deb602b3041737a3a2a820d1a23d969a613c111fe4"
    prediction = {
        "status": "predicted",
        "prediction_boundary": "native_calls",
        "boundary_basis": "elapsed_native_call_span_ms",
        "capture_id": observation["capture"]["capture_id"],
        "phase": calls["native_phase"],
        "source_sha256": actual_source,
        "boundary_samples": [
            {"key": key, "boundary_ms": 0.549453824} for key in calls["sample_keys"]
        ],
    }
    exact = scoring.score_boundary(prediction, observation)
    assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
    assert exact["n_pairs"] == 3 and exact["n_within_10pct"] == 3
    assert exact["count_over_10pct"] == 0
    assert exact["sample"] <= 0.005
    assert exact["source_identity_status"] == "matched"
    assert set(exact["per_key_errors"]) == set(calls["sample_keys"])
    assert exact["identity"]["rank"]["status"] in {"absent", "prediction_absent"}
    assert exact["identity"]["device"]["status"] in {"absent", "prediction_absent"}

    mutated = dict(prediction, source_sha256="f" * 64)
    mismatch = scoring.score_boundary(mutated, observation)
    assert mismatch["comparison"] == "invalid"
    assert mismatch["reason"] == "source_sha256_mismatch"
    assert mismatch["passed_10pct"] is False
    assert mismatch["n_pairs"] == 0

    dropped = {key: value for key, value in prediction.items() if key != "source_sha256"}
    absent = scoring.score_boundary(dropped, observation)
    assert absent["comparison"] == "uncovered"
    assert absent["reason"] == "native_calls_source_sha256_absent"
    assert absent["passed_10pct"] is False

    duplicated = dict(prediction, boundary_samples=[
        {"key": calls["sample_keys"][0], "boundary_ms": 0.549453824},
        {"key": calls["sample_keys"][0], "boundary_ms": 0.549453824},
    ])
    dup = scoring.score_boundary(duplicated, observation)
    assert dup["comparison"] == "invalid"
    assert dup["reason"] == "duplicate_prediction_sample_key"
    assert dup["passed_10pct"] is False


def test_counts_and_signed_per_key_errors_on_failed_group() -> None:
    keys = ["f0", "f1", "f2"]
    observation = _forward_observation([10.0, 20.0, 30.0], keys)
    prediction = _prediction("per_forward_window", boundary_samples=[
        {"key": "f0", "boundary_ms": 10.5},
        {"key": "f1", "boundary_ms": 17.0},
        {"key": "f2", "boundary_ms": 30.1},
    ])
    result = scoring.score_boundary(prediction, observation)
    assert result["comparison"] == "compared" and result["passed_10pct"] is False
    assert result["n_pairs"] == 3 and result["n_groups"] == 1
    assert result["count_over_10pct"] == 1
    assert result["n_within_10pct"] == 2
    assert result["per_key_errors"]["f0"] == pytest.approx(0.05)
    assert result["per_key_errors"]["f1"] == pytest.approx(-0.15)
    assert result["per_key_errors"]["f2"] == pytest.approx(0.1 / 30.0)
    assert result["max_signed_error"] == pytest.approx(-0.15)
    assert result["over_10pct_keys"] == ["f1"]


def test_identity_witness_conflicts_are_rejected_before_numeric() -> None:
    obs = {
        "capture": {"capture_id": "cap", "phase": "decode", "hardware_tier": "A5"},
        "source": {"sha256": "a" * 64},
        "measurements": {"per_forward_window": {
            "status": "measured", "source_sha256": "a" * 64,
            "samples_ms": [1.0], "sample_keys": ["k"],
            "samples_basis": "elapsed_window_span_ms",
        }},
    }
    pred = _prediction("per_forward_window", capture_id="cap", phase="decode",
                       source_sha256="a" * 64,
                       boundary_samples=[{"key": "k", "boundary_ms": 1.0}])
    assert scoring.score_boundary(pred, obs)["comparison"] == "compared"
    conflicted = dict(obs, source={"sha256": "b" * 64})
    result = scoring.score_boundary(pred, conflicted)
    assert result["comparison"] == "invalid"
    assert result["reason"] == "observation_source_sha256_witness_conflict"
    assert result["n_pairs"] == 0
    nested_conflict = dict(pred, boundary_samples=[
        {"key": "k", "boundary_ms": 1.0, "source_sha256": "b" * 64}])
    nested = scoring.score_boundary(nested_conflict, obs)
    assert nested["comparison"] == "invalid"
    assert nested["reason"] == "prediction_source_sha256_witness_conflict"


def test_operator_group_counts_are_whole_groups_and_pairs_separately() -> None:
    observation = {"measurements": {"operator_groups": {
        "a": {"status": "measured", "observed_ms": 1.0},
        "b": {"status": "measured", "observed_ms": 2.0},
    }}}
    prediction = {"status": "predicted", "operator_group_samples": [
        {"key": "a", "boundary_ms": 1.0},
        {"key": "b", "boundary_ms": 2.4},
    ]}
    result = scoring.score_operator_groups(prediction, observation)
    assert result["comparison"] == "compared" and result["passed_10pct"] is False
    assert result["n_groups"] == 2 and result["n_pairs"] == 2
    assert result["groups_matched"] == 2
    assert result["count_over_10pct"] == 1 and result["n_within_10pct"] == 1
    assert result["per_key_errors"]["a"] == pytest.approx(0.0)
    assert result["per_key_errors"]["b"] == pytest.approx(0.2)


@pytest.mark.skipif(not (_REAL_FLEET.is_file() and _CALIBRATION.is_dir()),
                    reason="real fleet/calibration source absent")
def test_real_calibration_native_calls_are_keyed_48_intervals_unknown_engine() -> None:
    import json

    measured = []
    calls = 0
    known = 0
    for line in _REAL_FLEET.open("r", encoding="utf-8"):
        row = json.loads(line)
        if not str(row.get("suite") or "").startswith("operator_and_kernel_calibration"):
            continue
        native = observations.extract_capture_observations(row)["measurements"].get("native_calls") or {}
        if native.get("status") != "measured":
            continue
        measured.append(native)
        calls += int(native.get("call_count") or 0)
        known += int(native.get("engines_known_count") or 0)
        assert native.get("source_sha256")
        assert native.get("samples_basis") == "elapsed_native_call_span_ms"
        assert len(native.get("sample_keys") or []) == int(native["call_count"])
    assert len(measured) == 16
    assert calls == 48
    assert known == 0


def test_native_calls_boundary_sha_is_used_when_top_level_is_absent() -> None:
    sha = "47e8ad42742063ff6440e0deb602b3041737a3a2a820d1a23d969a613c111fe4"
    observation = {
        "capture": {"capture_id": "cal:fia", "phase": "decode", "hardware_tier": "A5"},
        "source": {"sha256": None},
        "measurements": {"native_calls": {
            "status": "measured", "capture_id": "cal:fia", "native_phase": "prefill",
            "source_sha256": sha, "samples_basis": "elapsed_native_call_span_ms",
            "samples": [
                {"key": "call0", "observed_ms": 1.0, "phase": "prefill"},
                {"key": "call1", "observed_ms": 2.0, "phase": "prefill"},
            ],
        }},
    }
    prediction = {
        "status": "predicted", "prediction_boundary": "native_calls",
        "boundary_basis": "elapsed_native_call_span_ms",
        "capture_id": "cal:fia", "phase": "prefill", "source_sha256": sha,
        "boundary_samples": [{"key": "call0", "boundary_ms": 1.0},
                             {"key": "call1", "boundary_ms": 2.0}],
    }
    exact = scoring.score_boundary(prediction, observation)
    assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
    assert exact["identity"]["source_sha256"]["observation_basis"] == "boundary"
    mutated = scoring.score_boundary({**prediction, "source_sha256": "f" * 64}, observation)
    assert mutated["comparison"] == "invalid"
    assert mutated["reason"] == "source_sha256_mismatch"
    assert mutated["n_pairs"] == 0


@pytest.fixture(autouse=True)
def _isolate_scorer_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("HOME", "MINDIE_CONFIG_HOME", "MINDIE_DATA_HOME", "MINDIE_DIAGNOSTICS_ROOT"):
        monkeypatch.setenv(name, str(tmp_path / name.lower()))


def test_zero_prediction_keeps_original_forward_population() -> None:
    observation = _forward_observation([1.0, 2.0, 3.0], ["a", "b", "c"])
    result = scoring.score_boundary({}, observation)
    assert result["comparison"] == "uncovered"
    assert result["reason"] == "prediction_status_not_measured"
    assert result["denominator"] == 3
    assert result["population_boundary"] == "per_forward_window"
    assert result["population_status"] == "measured"
    assert result["matched"] == 0 and result["n_pairs"] == 0
    assert result["missing_keys"] == ["a", "b", "c"]


def test_subset_prediction_keeps_full_denominator_and_matched_counts() -> None:
    observation = _forward_observation([10.0, 20.0, 30.0], ["a", "b", "c"])
    result = scoring.score_boundary(_prediction("per_forward_window", boundary_samples=[
        {"key": "a", "boundary_ms": 10.5},
    ]), observation)
    assert result["comparison"] == "invalid"
    assert result["reason"] == "sample_key_population_mismatch"
    assert result["denominator"] == 3
    assert result["matched"] == 1 and result["n_pairs"] == 1
    assert result["missing_keys"] == ["b", "c"]
    assert result["count_over_10pct"] == 0 and result["n_within_10pct"] == 1
    assert result["passed_10pct"] is False


def test_wrong_scope_uses_observed_primary_population() -> None:
    observation = _forward_observation([1.0, 2.0], ["a", "b"])
    result = scoring.score_boundary(
        _prediction("native_client_request", boundary_ms=1.0), observation)
    assert result["comparison"] == "uncovered"
    assert result["reason"] == "prediction_boundary_scope_mismatch"
    assert result["denominator"] == 2
    assert result["population_boundary"] == "per_forward_window"
    assert result["missing_keys"] == ["a", "b"]
    assert result["matched"] == 0


def test_zero_prediction_keeps_native_call_population() -> None:
    sha = "a" * 64
    observation = {
        "capture": {"capture_id": "cal:fia", "phase": "prefill", "hardware_tier": "A5"},
        "measurements": {"native_calls": {
            "status": "measured", "capture_id": "cal:fia", "native_phase": "prefill",
            "source_sha256": sha, "samples_basis": "elapsed_native_call_span_ms",
            "samples": [
                {"key": "call0", "observed_ms": 1.0, "phase": "prefill"},
                {"key": "call1", "observed_ms": 2.0, "phase": "prefill"},
                {"key": "call2", "observed_ms": 3.0, "phase": "prefill"},
            ],
        }},
    }
    result = scoring.score_boundary({}, observation)
    assert result["denominator"] == 3
    assert result["population_boundary"] == "native_calls"
    assert result["missing_keys"] == ["call0", "call1", "call2"]
    assert result["matched"] == 0


def test_invalid_source_keeps_denominator_and_is_ungraded() -> None:
    sha = "a" * 64
    observation = {
        "capture": {"capture_id": "cap", "phase": "decode", "hardware_tier": "A5"},
        "source": {"sha256": sha},
        "measurements": {"per_forward_window": {
            "status": "measured", "capture_id": "cap", "source_sha256": sha,
            "samples_ms": [1.0, 2.0, 3.0], "sample_keys": ["a", "b", "c"],
            "samples_basis": "elapsed_window_span_ms",
        }},
    }
    result = scoring.score_boundary(_prediction(
        "per_forward_window", capture_id="cap", phase="decode", source_sha256="f" * 64,
        boundary_samples=[{"key": "a", "boundary_ms": 1.0}]), observation)
    assert result["comparison"] == "invalid"
    assert result["reason"] == "source_sha256_mismatch"
    assert result["denominator"] == 3
    assert result["matched"] == 0 and result["n_pairs"] == 0
    assert result["missing_keys"] == []
    assert result["passed_10pct"] is False


def test_missing_hardware_tracks_population_but_withholds_pass() -> None:
    observation = {
        "capture": {"capture_id": "cap", "phase": "prefill"},
        "measurements": {"native_client_request": {
            "status": "measured", "phase": "prefill",
            "samples": [{"key": "request:0", "ttft_ms": 10.0, "ok": True}],
        }},
    }
    result = scoring.score_boundary(_prediction(
        "native_client_request", capture_id="cap", phase="prefill",
        boundary_samples=[{"key": "request:0", "boundary_ms": 10.0}]), observation)
    assert result["comparison"] == "uncovered"
    assert result["reason"] == "hardware_provenance_absent"
    assert result["denominator"] == 1
    assert result["matched"] == 1 and result["missing_keys"] == []
    assert result["population_provenance"]["hardware_status"] == "absent"
    assert result["passed_10pct"] is False


_REAL_FLEET = Path("/tmp/mindie-sim-profiling-bench/data/fleet_captures.jsonl")
_POPULATION_CASES = {
    "dsh_heldout:a3/heldout_engine_20261030/dsv41_wave23_ablation_20261030/prof/tp2dp8_ep16_dspark0_decode_128k_c16/kernel_details.csv":
        (101, "09da8f3a770226dd568a9f5e7956092503bfa90a099ca29f6b953bba862a7fb8"),
    "wave5:a2:a2/a2_real_dsv2lite_E64_K6_tp4ep4_decode:a2_real_dsv2lite_E64_K6_tp4ep4_decode_128k_c1":
        (83, "8f14c6f56a4efa84bbe619de749dadf6c0b96382fdedd6ca099481a2b0d2b5ac"),
    "wave5:a5:a5/a5_qwen30ba3b_tp4_ep4_decode:a5_qwen30ba3b_tp4_ep4_decode_4k_c1":
        (139, "75582719a2e4290752b27eb69625e21c5ee1ce6d914909ce21bb0083e0acd095"),
    "wave5:a2:a2/a2_synth_dsv2lite_L8_E16_K4_tp4ep4_decode:a2_synth_dsv2lite_L8_E16_K4_tp4ep4_decode_4k_c32":
        (140, "1f575ea150729221ad46d8f00075be597210e016781a1aaf32ca70934cf31304"),
}


@pytest.mark.skipif(not _REAL_FLEET.is_file(), reason="real fleet source absent")
def test_real_dsh_wave5_and_a2_population_keys_are_not_lost() -> None:
    import hashlib
    import json

    wanted = set(_POPULATION_CASES)
    rows = {}
    for line in _REAL_FLEET.open("r", encoding="utf-8"):
        row = json.loads(line)
        if row.get("capture_id") in wanted:
            rows[row["capture_id"]] = row
    assert set(rows) == wanted
    for capture_id, (expected_count, expected_sha) in _POPULATION_CASES.items():
        observation = observations.extract_capture_observations(rows[capture_id])
        zero = scoring.score_boundary({}, observation)
        assert zero["denominator"] == expected_count
        assert zero["population_boundary"] == "per_forward_window"
        assert len(zero["missing_keys"]) == expected_count
        assert zero["matched"] == 0
        frames = observation["measurements"]["per_forward_window"]["frame_identifiers"]
        keys = []
        for frame in frames:
            data = frame.get("body") if isinstance(frame.get("body"), dict) else frame
            keys.append((frame.get("phase"),
                         str(data.get("rank_id") if data.get("rank_id") is not None else ""),
                         str(data.get("device_id") if data.get("device_id") is not None else ""),
                         frame.get("forward_id")))
        digest = hashlib.sha256()
        for key in sorted(keys):
            digest.update(json.dumps(key, separators=(",", ":")).encode() + b"\n")
        assert digest.hexdigest() == expected_sha


def test_exact_elapsed_alias_is_accepted_but_wait_only_namespace_is_not() -> None:
    keys = ["a", "b", "c"]
    observation = _forward_observation([1.0, 2.0, 3.0], keys)
    elapsed = _prediction("per_forward_window_elapsed", boundary_samples=[
        {"key": "a", "boundary_ms": 1.0}, {"key": "b", "boundary_ms": 2.0},
        {"key": "c", "boundary_ms": 3.0}])
    result = scoring.score_boundary(elapsed, observation)
    assert result["comparison"] == "compared" and result["passed_10pct"] is True
    assert result["boundary_class"] == "inclusive_forward_elapsed"
    for invented in ("per_forward_totally_different_latencies",
                     "per_forward_window_time_inside_allocator_wait"):
        wrong = scoring.score_boundary({**elapsed, "prediction_boundary": invented}, observation)
        assert wrong["comparison"] == "uncovered"
        assert wrong["reason"] == "unsupported_prediction_boundary_scope"
        assert wrong["denominator"] == 3
        assert wrong["matched"] == 0 and wrong["n_pairs"] == 0
        assert wrong["missing_keys"] == keys
        assert wrong["boundary_class"] == "unknown_prediction_scope"
        assert wrong["passed_10pct"] is False


_REAL_KIMI = ("dsh_heldout:a3/heldout_engine_20261030/"
              "kimi_k3_w4a8_4layer_tp16_ep16_heldout_20261030/prof/prefill_c1_p16k/"
              "kernel_details.csv")


@pytest.mark.skipif(not _REAL_FLEET.is_file(), reason="real fleet source absent")
def test_real_kimi_three_keys_keep_scope_authority() -> None:
    import json

    row = None
    for line in _REAL_FLEET.open("r", encoding="utf-8"):
        candidate = json.loads(line)
        if candidate.get("capture_id") == _REAL_KIMI:
            row = candidate
            break
    assert row is not None
    observation = observations.extract_capture_observations(row)
    population = scoring.observed_boundary_population(observation, "per_forward_window")
    assert population["denominator"] == 3
    provenance = population["provenance"]
    prediction = {
        "status": "predicted", "prediction_boundary": "per_forward_window",
        "boundary_basis": "elapsed_window_span_ms",
        "capture_id": provenance["capture_id"], "phase": provenance["phase"],
        "source_sha256": provenance["source_sha256"],
        "boundary_samples": [{"key": key, "boundary_ms": value}
                             for key, value in zip(population["keys"], population["values"])],
    }
    exact = scoring.score_boundary(prediction, observation)
    assert exact["comparison"] == "compared" and exact["passed_10pct"] is True
    assert exact["denominator"] == exact["matched"] == exact["n_pairs"] == 3
    assert exact["boundary_class"] == "inclusive_forward_elapsed"
    for invented in ("per_forward_totally_different_latencies",
                     "per_forward_window_time_inside_allocator_wait"):
        wrong = scoring.score_boundary({**prediction, "prediction_boundary": invented}, observation)
        assert wrong["comparison"] == "uncovered"
        assert wrong["reason"] == "unsupported_prediction_boundary_scope"
        assert wrong["denominator"] == 3 and wrong["matched"] == 0
        assert wrong["n_pairs"] == 0 and len(wrong["missing_keys"]) == 3
        assert wrong["passed_10pct"] is False
