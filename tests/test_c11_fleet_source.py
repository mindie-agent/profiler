"""Original fleet scalar and operator gate.

Fixtures carry their own source fields. Nothing here reads a scratch path,
reprices a fleet, or treats a client metric as the completion scalar.
"""
from __future__ import annotations

import json
import math
import statistics
import sys

import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_benchmark_gate as gate  # noqa: E402
import hf_fleet_source_gate as fleet_source  # noqa: E402
import hf_original_account as original  # noqa: E402


def _window_row(capture_id: str, spans: list[float], predicted: dict[str, float], *,
                basis: str, phase: str = "prefill") -> tuple[dict, dict, dict]:
    keys = [f"s{index}" for index in range(len(spans))]
    observed = math.fsum(spans) if "sum" in basis or "body_span" in basis else statistics.fmean(spans)
    row = {
        "capture_id": capture_id,
        "phase": phase,
        "hardware_tier": "A5",
        "suite": "fixture",
        "observed_ms": observed,
        "predicted_ms": observed + 100.0,
    }
    if "sum" in basis or "body_span" in basis:
        row["body_span_sum_ms"] = observed
    observation = {
        "observed_ms": observed + 3.0,
        "observed_basis": "client_reported_tpot_producer_basis",
        "capture": {"capture_id": capture_id, "phase": phase, "hardware_tier": "A5"},
        "source": {},
        "measurements": {
            "per_forward_window": {
                "status": "measured",
                "phase": phase,
                "samples_basis": basis,
                "samples_ms": list(spans),
                "sample_keys": keys,
                "mean_forward_span_ms": statistics.fmean(spans),
            },
        },
        "observed_by_family_ms": {"gemm": 4.0, "attention": 2.0},
        "observed_by_core_ms": {},
    }
    prediction = {
        "status": "modeled",
        "prediction_boundary": "per_forward_window",
        "boundary_basis": basis,
        "capture_id": capture_id,
        "phase": phase,
        "hardware_tier": "A5",
        "boundary_samples": {key: predicted[key] for key in keys},
        "predicted_step_ms": spans[0],
        "predicted_ms": observed + 50.0,
        "predicted_by_family_ms": {"gemm": 4.0, "attention": 2.0},
        "predicted_by_canonical_family_ms": {"gemm": 4.0, "attention": 2.0},
        "predicted_by_unified_family_ms": {"matmul_gemm": 4.0, "attention": 2.0},
        "predicted_by_core_ms": {"AI_CORE": None, "AI_VECTOR_CORE": None},
    }
    return row, observation, prediction


def test_row_scalar_survives_when_the_client_observation_is_removed_or_rotated() -> None:
    """27.774 stays the input. 15.225 is recorded and is not the completion value."""
    primary = 27.774
    client = 15.225
    row = {
        "capture_id": "a5_multinode_20261108:r06_2n_dsv4flash_0731_fp8_dp16_tp1_ep_400k:dualrank_decode_isl1024_c1",
        "phase": "decode",
        "hardware_tier": "A5",
        "observed_ms": primary,
        "predicted_ms": 99.0,
    }
    observation = {
        "observed_ms": client,
        "observed_basis": "client_reported_tpot_producer_basis",
        "measurements": {},
        "source": {},
        "capture": {"capture_id": row["capture_id"], "phase": "decode", "hardware_tier": "A5"},
    }
    scored = gate.score_fleet_row(row, observation, {})
    assert scored["source_observed_ms"] == row["observed_ms"]
    assert scored["source_observation_ms"] == observation["observed_ms"]
    assert scored["source_observation_basis"] == observation["observed_basis"]
    assert scored["source_scalar"]["status"] == "ambiguous"
    assert scored["source_scalar"]["signed_error"] is None
    rotated = dict(observation, observed_ms=1.0, observed_basis="rotated_client")
    rotated_score = gate.score_fleet_row(row, rotated, {})
    assert rotated_score["source_observed_ms"] == row["observed_ms"]
    assert rotated_score["source_observation_ms"] == rotated["observed_ms"]
    assert rotated_score["source_scalar"]["status"] == scored["source_scalar"]["status"]
    removed = dict(observation)
    removed["observed_ms"] = None
    removed["observed_basis"] = ""
    removed_score = gate.score_fleet_row(row, removed, {})
    assert removed_score["source_observed_ms"] == row["observed_ms"]
    assert removed_score["source_observation_ms"] is None
    poisoned = dict(scored)
    poisoned["source_observed_ms"] = client
    poisoned["source_scalar"] = dict(scored["source_scalar"], source_observed_ms=client,
                                     status="compared", predicted_aggregate_ms=client, passed_10pct=True)
    enrolled = original.enroll_population([poisoned], [row], [], [])
    assert enrolled[0]["source_observed_ms"] == row["observed_ms"]
    decision = original._fleet_row_gate(enrolled[0])
    assert decision["source_observed_ms"] == row["observed_ms"]
    assert decision["source_observation_ms"] == client
    assert decision["scalar_status"] == "ambiguous"
    assert decision["passed_10pct"] is False
    assert decision["signed_error"] is None


def test_partial_window_population_is_not_a_comparable_scalar() -> None:
    """One forecast frame does not reduce a multi-window mean, and the id stays counted."""
    spans = [1.0 + (index % 7) * 0.05 for index in range(139)]
    mean = statistics.fmean(spans)
    keys = [f"w{index}" for index in range(139)]
    row = {
        "capture_id": "wave5:a5:partial",
        "phase": "decode",
        "hardware_tier": "A5",
        "observed_ms": mean,
        "predicted_ms": mean + 1.0,
    }
    observation = {
        "observed_ms": mean - 1.0,
        "observed_basis": "client_reported_tpot_producer_basis",
        "capture": {"capture_id": row["capture_id"], "phase": "decode", "hardware_tier": "A5"},
        "source": {},
        "measurements": {"per_forward_window": {
            "status": "measured", "phase": "decode", "samples_basis": "elapsed_window_span_ms",
            "samples_ms": spans, "sample_keys": keys, "mean_forward_span_ms": mean,
        }},
    }
    prediction = {
        "status": "modeled",
        "prediction_boundary": "per_forward_window",
        "boundary_basis": "elapsed_window_span_ms",
        "capture_id": row["capture_id"],
        "phase": "decode",
        "hardware_tier": "A5",
        "predicted_step_ms": spans[0],
        "predicted_ms": mean,
        "boundary_samples": {keys[0]: spans[0]},
    }
    scored = gate.score_fleet_row(row, observation, prediction)
    assert scored["key_denominator"] == 139
    assert scored["key_matched"] == 1
    assert scored["key_missing"] == 138
    assert scored["source_observed_ms"] == row["observed_ms"]
    assert scored["source_scalar"]["status"] == "ambiguous"
    assert scored["source_scalar"]["predicted_aggregate_ms"] is None
    assert scored["source_scalar"]["signed_error"] is None
    assert scored["source_predicted_step"] == prediction["predicted_step_ms"]
    assert scored["source_predicted_step"] != row["predicted_ms"]
    account = original.all_original_account(original.enroll_population([scored], [row], [], []))
    assert account["id_denominator"] == 1
    assert account["row_gate"]["changed_by_per_key"] is False


def test_complete_span_sum_and_operator_projection_pass_together() -> None:
    """A matched prefill span sum and the same frozen operator scorer can pass."""
    spans = {"s0": 1000.0, "s1": 200.0}
    predicted = {"s0": 1020.0, "s1": 190.0}
    row, observation, prediction = _window_row(
        "w8-span-sum", list(spans.values()), predicted, basis="body_span_sum_ms",
    )
    direct = fleet_source.compare_operator_projection(
        observation["observed_by_family_ms"], None, prediction, same_proof=True,
    )
    scored = gate.score_fleet_row(row, observation, prediction)
    assert scored["source_scalar"]["status"] == "compared"
    assert scored["source_scalar"]["reducer"] == "sum"
    assert scored["source_scalar"]["predicted_aggregate_ms"] == math.fsum(predicted.values())
    assert scored["source_scalar"]["predicted_aggregate_ms"] != prediction["predicted_step_ms"]
    assert scored["source_observed_ms"] == row["observed_ms"]
    assert scored["source_observation_ms"] != row["observed_ms"]
    assert scored["source_operator"]["operator_relative_error"] == direct["operator_relative_error"]
    assert scored["source_operator"]["status"] == direct["status"] == "compared"
    assert scored["source_operator"]["maps"]["core"]["status"] == "inapplicable"
    decision = original._fleet_row_gate(scored)
    assert decision["passed_10pct"] is True
    assert decision["scalar_passed_10pct"] is True
    assert decision["operator_passed_10pct"] is True
    assert decision["reducer"] == "sum"


def test_median_of_a_span_sum_is_not_the_source_reducer() -> None:
    """Two priced spans whose median matches the sum still fail on the sum."""
    spans = {"s0": 1000.0, "s1": 200.0}
    predicted = {"s0": 1000.0, "s1": 1400.0}
    assert statistics.median(predicted.values()) == math.fsum(spans.values())
    row, observation, prediction = _window_row(
        "w8-not-median", list(spans.values()), predicted, basis="body_span_sum_ms",
    )
    scored = gate.score_fleet_row(row, observation, prediction)
    assert scored["source_scalar"]["status"] == "compared"
    assert scored["source_scalar"]["reducer"] == "sum"
    assert scored["source_scalar"]["predicted_aggregate_ms"] == math.fsum(predicted.values())
    assert scored["source_scalar"]["passed_10pct"] is False
    assert scored["source_operator"]["passed_10pct"] is True
    decision = original._fleet_row_gate(scored)
    assert decision["scalar_passed_10pct"] is False
    assert decision["operator_passed_10pct"] is True
    assert decision["passed_10pct"] is False
    assert decision["ambiguous"] is False


def test_operator_over_10pct_fails_while_the_scalar_passes() -> None:
    """A within-scalar row does not pass a family projection outside 10%."""
    row = {
        "capture_id": "operator-negative",
        "phase": "decode",
        "hardware_tier": "A3",
        "observed_ms": 10.0,
        "predicted_ms": 80.0,
    }
    observation = {
        "observed_ms": 4.0,
        "observed_basis": "client_reported_tpot_producer_basis",
        "measurements": {},
        "source": {},
        "capture": {"capture_id": row["capture_id"], "phase": "decode", "hardware_tier": "A3"},
        "observed_by_family_ms": {"gemm": 10.0, "attention": 5.0},
    }
    prediction = {
        "status": "modeled",
        "predicted_step_ms": 10.4,
        "predicted_ms": 1.0,
        "capture_id": row["capture_id"],
        "phase": "decode",
        "hardware_tier": "A3",
        "predicted_by_family_ms": {"gemm": 20.0, "attention": 5.0},
        "predicted_by_canonical_family_ms": {"gemm": 20.0, "attention": 5.0},
        "predicted_by_unified_family_ms": {"matmul_gemm": 20.0, "attention": 5.0},
        "predicted_by_core_ms": {"AI_CORE": None},
    }
    direct = fleet_source.compare_operator_projection(
        observation["observed_by_family_ms"], None, prediction,
    )
    scored = gate.score_fleet_row(row, observation, prediction)
    assert direct["status"] == "compared"
    assert direct["passed_10pct"] is False
    assert scored["source_operator"]["operator_relative_error"] == direct["operator_relative_error"]
    decision = original._fleet_row_gate(scored)
    assert decision["scalar_status"] == "compared"
    assert decision["scalar_passed_10pct"] is True
    assert decision["operator_status"] == "compared"
    assert decision["operator_passed_10pct"] is False
    assert decision["passed_10pct"] is False


def test_missing_operator_key_and_zero_observation_are_not_passes() -> None:
    """A dropped group cannot complete the map. A zero observation is not a relative error."""
    partial = fleet_source.compare_operator_projection(
        {"gemm": 4.0, "attention": 2.0}, None,
        {"predicted_by_family_ms": {"gemm": 4.0},
         "predicted_by_canonical_family_ms": {"gemm": 4.0},
         "predicted_by_unified_family_ms": {"matmul_gemm": 4.0}},
    )
    assert partial["status"] == "ambiguous"
    assert partial["passed_10pct"] is False
    zero = fleet_source.score_source_scalar(
        {"capture_id": "zero", "phase": "decode", "observed_ms": 0.0},
        {"capture": {"capture_id": "zero", "phase": "decode"}, "measurements": {}},
        {"predicted_step_ms": 0.0, "capture_id": "zero", "phase": "decode"},
        None,
    )
    assert zero["status"] == "ambiguous"
    assert zero["passed_10pct"] is False
    assert zero["signed_error"] is None
    assert zero["source_observed_ms"] == 0.0
    bad = fleet_source.score_source_scalar(
        {"capture_id": "nan", "phase": "decode", "observed_ms": float("nan")},
        {"measurements": {}},
        {"predicted_step_ms": 1.0, "capture_id": "nan", "phase": "decode"},
        None,
    )
    assert bad["status"] == "ambiguous"
    assert bad["passed_10pct"] is False


def _keyed_windows(capture_id: str, spans: list[float], *, phase: str, basis: str,
                   frames: list[dict] | None = None, groups: dict[str, int] | None = None,
                   boundary: str | None = None, source: dict | None = None) -> tuple[dict, dict]:
    keys = [f"s{index}" for index in range(len(spans))]
    window = {
        "status": "measured",
        "phase": phase,
        "samples_basis": basis,
        "samples_ms": list(spans),
        "sample_keys": keys,
    }
    if boundary is not None:
        window["boundary"] = boundary
    if frames is not None:
        window["frame_identifiers"] = frames
    if groups is not None:
        window["geometry_populations"] = groups
    observation = {
        "observed_ms": None,
        "observed_basis": "",
        "capture": {"capture_id": capture_id, "phase": phase, "hardware_tier": "A5"},
        "source": {} if source is None else source,
        "measurements": {"per_forward_window": window},
    }
    return keys, observation


def test_reducer_stays_when_the_target_number_changes() -> None:
    """Declared geometry mean stays. Sum, median, and a missing target do not retarget it."""
    spans = [1.0, 2.0, 3.0, 6.0]
    prices = [1.1, 2.2, 3.3, 6.6]
    frames = [{"ordinal": index, "phase": "decode", "query_rows": 1, "device_id": "0",
               "forward_id": f"auto:{index}"} for index in range(len(spans))]
    keys, observation = _keyed_windows(
        "decode-mean", spans, phase="decode", basis="elapsed_window_span_ms", frames=frames,
        groups={"q=1,seq=1,tok=1": len(spans)},
    )
    prediction = {
        "status": "modeled",
        "prediction_boundary": "per_forward_window",
        "capture_id": "decode-mean",
        "phase": "decode",
        "hardware_tier": "A5",
        "boundary_samples": {key: price for key, price in zip(keys, prices)},
        "predicted_step_ms": prices[0],
    }
    expected = statistics.fmean(prices)
    reducers = []
    aggregates = []
    counts = []
    for target in (statistics.fmean(spans), math.fsum(spans), statistics.median(spans), None):
        row = {"capture_id": "decode-mean", "phase": "decode", "hardware_tier": "A5", "predicted_ms": 0.0}
        if target is None:
            pass
        else:
            row["observed_ms"] = target
        scored = gate.score_fleet_row(row, observation, prediction)
        scalar = scored["source_scalar"]
        reducers.append(scalar["reducer"])
        aggregates.append(scalar["predicted_aggregate_ms"])
        counts.append(scalar["population_count"])
        assert scalar["producer"] == "largest_complete_forward_count"
        assert scored["source_predicted_step"] == prices[0]
    assert reducers == ["mean", "mean", "mean", "mean"]
    assert aggregates == [expected, expected, expected, expected]
    assert counts == [4, 4, 4, 4]
    matched = gate.score_fleet_row(
        {"capture_id": "decode-mean", "phase": "decode", "hardware_tier": "A5",
         "observed_ms": statistics.fmean(spans)},
        observation, prediction,
    )
    assert matched["source_scalar"]["status"] == "compared"
    assert matched["source_scalar"]["signed_error"] == (expected - statistics.fmean(spans)) / statistics.fmean(spans)
    withheld = gate.score_fleet_row(
        {"capture_id": "decode-mean", "phase": "decode", "hardware_tier": "A5"},
        observation, prediction,
    )
    assert withheld["source_scalar"]["status"] == "unavailable"
    assert withheld["source_scalar"]["reason"] == "target_absent"
    assert withheld["source_scalar"]["signed_error"] is None


def test_primary_geometry_mean_is_not_the_closer_all_window_aggregate() -> None:
    """Largest retained geometry is the cohort. A closer all-window number is not selected."""
    primary = [10.0, 10.0, 10.0, 14.0]
    other = [1.0, 1.0]
    spans = other + primary
    frames = []
    for index, query in enumerate([6, 6, 24, 24, 24, 24]):
        frames.append({"ordinal": index, "phase": "decode", "rank_id": "", "device_id": "0",
                       "forward_id": f"auto:{index}", "query_rows": query})
    keys, observation = _keyed_windows(
        "primary-geometry", spans, phase="decode", basis="elapsed_window_span_ms", frames=frames,
        groups={"q=6,seq=1,tok=6": 2, "q=24,seq=4,tok=6": 4},
    )
    prices = {key: (100.0 if index < 2 else 11.0) for index, key in enumerate(keys)}
    prediction = {
        "status": "modeled", "prediction_boundary": "per_forward_window",
        "capture_id": "primary-geometry", "phase": "decode", "hardware_tier": "A5",
        "boundary_samples": prices, "predicted_step_ms": statistics.fmean(spans),
    }
    row = {"capture_id": "primary-geometry", "phase": "decode", "hardware_tier": "A5",
           "observed_ms": statistics.fmean(primary), "forward_steps": len(spans)}
    scored = gate.score_fleet_row(row, observation, prediction)
    scalar = scored["source_scalar"]
    assert scalar["reducer"] == "mean"
    assert scalar["producer"] == "largest_complete_forward_count"
    assert scalar["population_count"] == 4
    assert scalar["window_filter"]["query_rows"] == 24
    assert scalar["predicted_aggregate_ms"] == 11.0
    assert scalar["predicted_aggregate_ms"] != statistics.fmean(list(prices.values()))
    assert scalar["status"] == "compared"
    moved = dict(row, observed_ms=statistics.fmean(spans))
    shifted = gate.score_fleet_row(moved, observation, prediction)
    assert shifted["source_scalar"]["reducer"] == "mean"
    assert shifted["source_scalar"]["population_count"] == 4
    assert shifted["source_scalar"]["predicted_aggregate_ms"] == 11.0
    assert shifted["source_scalar"]["status"] == "unavailable"
    assert shifted["source_scalar"]["reason"] == "source_number_inconsistent"


def test_prefill_sum_is_not_selected_by_matching_the_target() -> None:
    """Two prefill spans sum. Setting the target to their mean does not switch reducers."""
    spans = [1000.0, 200.0]
    prices = [1010.0, 190.0]
    frames = [
        {"ordinal": 0, "phase": "prefill", "device_id": "4", "forward_id": "prefill:0", "query_rows": 3840},
        {"ordinal": 1, "phase": "prefill", "device_id": "4", "forward_id": "prefill:1", "query_rows": 256},
    ]
    keys, observation = _keyed_windows(
        "prefill-sum", spans, phase="prefill", basis="elapsed_window_span_ms", frames=frames,
        groups={"q=None,seq=None,tok=None": 2},
        boundary="per_forward_window_source_receipt_prefill_chunk",
    )
    prediction = {
        "status": "modeled", "prediction_boundary": "per_forward_window",
        "capture_id": "prefill-sum", "phase": "prefill", "hardware_tier": "A5",
        "boundary_samples": {key: price for key, price in zip(keys, prices)},
        "predicted_step_ms": prices[0],
        "sequences_per_replica": 1,
    }
    aggregate = math.fsum(prices)
    mean_target = gate.score_fleet_row(
        {"capture_id": "prefill-sum", "phase": "prefill", "hardware_tier": "A5",
         "observed_ms": statistics.fmean(spans)},
        observation, prediction,
    )
    assert mean_target["source_scalar"]["reducer"] == "sum"
    assert mean_target["source_scalar"]["producer"] == "dsh_scoped_prefill.score_prefill_capture"
    assert mean_target["source_scalar"]["predicted_aggregate_ms"] == aggregate
    assert mean_target["source_scalar"]["status"] == "unavailable"
    summed = gate.score_fleet_row(
        {"capture_id": "prefill-sum", "phase": "prefill", "hardware_tier": "A5",
         "observed_ms": math.fsum(spans)},
        observation, prediction,
    )
    assert summed["source_scalar"]["reducer"] == "sum"
    assert summed["source_scalar"]["predicted_aggregate_ms"] == aggregate
    assert summed["source_scalar"]["population_label"] == "conditional"
    assert summed["source_scalar"]["status"] == "compared"
    assert summed["source_scalar"]["passed_10pct"] is False
    decision = original._fleet_row_gate(summed)
    assert decision["passed_10pct"] is False
    assert decision["ambiguous"] is False
    assert decision["reducer"] == "sum"


def test_missing_required_core_is_failed_and_not_forced_to_the_scalar_cohort() -> None:
    """Original cores are kernel sums. A null core forecast is failed, not inapplicable."""
    spans = [5.0, 5.0, 5.0, 5.0]
    keys, observation = _keyed_windows("core-pop", spans, phase="decode", basis="elapsed_window_span_ms")
    row = {
        "capture_id": "core-pop",
        "phase": "decode",
        "hardware_tier": "A5",
        "observed_ms": statistics.fmean(spans),
        "forward_steps": 7,
        "operator_modeling": {
            "families": {"cube_gemm": {"observed_ms": 4.0, "predicted_ms": 99.0}},
            "canonical_families": {"gemm": {"observed_ms": 4.0, "predicted_ms": 99.0}},
            "unified_families": {
                "matmul_gemm": {"observed_ms": 4.0, "predicted_ms": 99.0},
                "collective_comm": {"observed_ms": 0.0, "predicted_ms": 99.0},
            },
            "by_accelerator_core": {
                "AI_CORE": {"observed_ms": 4.0, "predicted_ms": 99.0},
                "COMMUNICATION": {"observed_ms": 1.0, "predicted_ms": 99.0},
            },
        },
    }
    prediction = {
        "status": "modeled",
        "prediction_boundary": "per_forward_window",
        "capture_id": "core-pop",
        "phase": "decode",
        "hardware_tier": "A5",
        "boundary_samples": {key: 5.1 for key in keys},
        "predicted_step_ms": 5.1,
        "predicted_by_family_ms": {"cube_gemm": 4.0, "unclassified": 11.5},
        "predicted_by_canonical_family_ms": {"gemm": 4.0},
        "predicted_by_unified_family_ms": {"matmul_gemm": 4.0, "collective_comm": 0.0},
        "predicted_by_core_ms": {"AI_CORE": None, "AI_VECTOR_CORE": None, "COMMUNICATION": None, "MIX_AIC": None},
    }
    scored = gate.score_fleet_row(row, observation, prediction)
    operator = scored["source_operator"]
    assert operator["maps"]["core"]["status"] == "failed"
    assert operator["maps"]["core"]["status"] != "inapplicable"
    assert operator["maps"]["core"]["reason"] == "required_group_missing"
    assert operator["operator_population"] == "kernel_group_sums"
    assert operator["population_forward_steps"] == 7
    assert operator["population_forward_steps"] != scored["source_scalar"]["population_count"]
    assert scored["source_scalar"]["population_count"] == 4
    decision = original._fleet_row_gate(scored)
    assert decision["passed_10pct"] is False
    assert decision["operator_status"] == "failed"
    account = original.all_original_account(original.enroll_population([scored], [row], [], []))
    assert account["id_denominator"] == 1
    absent = fleet_source.compare_operator_projection(None, None, {}, same_proof=True)
    assert absent["status"] == "unavailable"
    assert absent["reason"] == "operator_maps_absent"


def test_phase_alone_does_not_name_sum_or_mean() -> None:
    """Elapsed windows with only a phase string stay unpriced."""
    spans = [4.0, 6.0]
    prices = [4.0, 6.0]
    for phase, target in (("prefill", math.fsum(spans)), ("decode", statistics.fmean(spans))):
        keys, observation = _keyed_windows(f"phase-only-{phase}", spans, phase=phase, basis="elapsed_window_span_ms")
        prediction = {
            "status": "modeled", "prediction_boundary": "per_forward_window",
            "capture_id": f"phase-only-{phase}", "phase": phase, "hardware_tier": "A5",
            "boundary_samples": {key: price for key, price in zip(keys, prices)},
            "predicted_step_ms": prices[0], "sequences_per_replica": 1,
        }
        scored = gate.score_fleet_row(
            {"capture_id": f"phase-only-{phase}", "phase": phase, "hardware_tier": "A5", "observed_ms": target},
            observation, prediction,
        )
        scalar = scored["source_scalar"]
        assert scalar["reducer"] == ""
        assert scalar["producer"] == "unsupported"
        assert scalar["predicted_aggregate_ms"] is None
        assert scalar["status"] == "ambiguous"
        assert scalar["reason"] == "producer_unsupported"


def _operator_case(prediction: dict) -> dict:
    row = {
        "capture_id": "op-contract",
        "phase": "decode",
        "hardware_tier": "A5",
        "observed_ms": 10.0,
        "operator_modeling": {
            "families": {"gemm": {"observed_ms": 4.0, "predicted_ms": 4.0}},
            "by_accelerator_core": {"AI_CORE": {"observed_ms": 4.0, "predicted_ms": 4.0}},
            "unified_families": {"matmul_gemm": {"observed_ms": 4.0, "predicted_ms": 4.0}},
            "canonical_families": {"gemm": {"observed_ms": 4.0, "predicted_ms": 9.0}},
        },
    }
    observation = {
        "observed_ms": None,
        "capture": {"capture_id": "op-contract", "phase": "decode", "hardware_tier": "A5"},
        "source": {},
        "measurements": {},
    }
    return gate.score_fleet_row(row, observation, prediction)


def _operator_prediction(**overrides: object) -> dict:
    prediction = {
        "status": "modeled",
        "capture_id": "op-contract",
        "phase": "decode",
        "hardware_tier": "A5",
        "predicted_step_ms": 10.2,
        "predicted_operator_ms": 4.0,
        "predicted_by_family_ms": {"gemm": 4.0},
        "predicted_by_core_ms": {"AI_CORE": 4.0},
        "predicted_by_unified_family_ms": {"matmul_gemm": 4.0},
        "predicted_by_canonical_family_ms": {"gemm": 4.0},
    }
    prediction.update(overrides)
    return prediction


def test_canonical_is_diagnostic_and_declared_total_is_required() -> None:
    """Canonical absence or a wrong canonical keeps the required-map score."""
    control = _operator_case(_operator_prediction())
    no_canonical = dict(_operator_prediction())
    del no_canonical["predicted_by_canonical_family_ms"]
    dropped = _operator_case(no_canonical)
    wrong = _operator_case(_operator_prediction(predicted_by_canonical_family_ms={"gemm": 80.0, "extra": 1.0}))
    extra_core = _operator_case(_operator_prediction(predicted_by_core_ms={"AI_CORE": 4.0, "AI_CPU": 0.0}))
    no_total = dict(_operator_prediction())
    del no_total["predicted_operator_ms"]
    undeclared_total = _operator_case(no_total)
    changed_total = _operator_case(_operator_prediction(predicted_operator_ms=9.0))
    missing_family = dict(_operator_prediction())
    del missing_family["predicted_by_family_ms"]
    missing_core = dict(_operator_prediction())
    del missing_core["predicted_by_core_ms"]
    missing_unified = dict(_operator_prediction())
    del missing_unified["predicted_by_unified_family_ms"]

    def signature(scored: dict) -> tuple:
        operator = scored["source_operator"]
        return (operator["status"], operator["passed_10pct"], operator["operator_relative_error"],
                scored["source_scalar"]["reducer"], scored["source_scalar"]["predicted_aggregate_ms"])

    assert signature(control) == signature(dropped) == signature(wrong) == signature(extra_core)
    assert control["source_operator"]["passed_10pct"] is True
    assert signature(undeclared_total) == signature(control)
    assert changed_total["source_operator"]["status"] == "failed"
    assert changed_total["source_operator"]["reason"] == "predicted_operator_total"
    assert changed_total["source_operator"]["passed_10pct"] is False
    for broken in (missing_family, missing_core, missing_unified):
        scored = _operator_case(broken)
        assert scored["source_operator"]["passed_10pct"] is False
        assert scored["source_operator"]["status"] in {"failed", "ambiguous"}


def test_prefill_b1_binds_from_the_capture_root_not_the_frame(tmp_path: Path) -> None:
    """Exact B1 on the capture root certifies. A forecast sequence and an unknown max_running do not."""
    spans = [1000.0, 200.0]
    frames = [
        {"ordinal": 0, "phase": "prefill", "device_id": "4", "forward_id": "prefill:0"},
        {"ordinal": 1, "phase": "prefill", "device_id": "4", "forward_id": "prefill:1"},
    ]

    def usage(max_running: float) -> None:
        (tmp_path / "benchmark_summary.json").write_text(json.dumps({
            "summary": {"concurrency": 1, "max_running": max_running, "n_ok": 1},
            "requests": [{"idx": 0, "ok": True, "prompt_tokens": 4096, "completion_tokens": 1, "chunk_epochs": [1.0]}],
        }))

    def score(source: dict | None, max_running: float | None = None) -> dict:
        if max_running is not None:
            usage(max_running)
        keys, observation = _keyed_windows(
            "b1-prefill", spans, phase="prefill", basis="elapsed_window_span_ms", frames=frames,
            boundary="per_forward_window_source_receipt_prefill_chunk", source=source,
        )
        prediction = {
            "status": "modeled", "prediction_boundary": "per_forward_window",
            "capture_id": "b1-prefill", "phase": "prefill", "hardware_tier": "A5",
            "boundary_samples": {key: value for key, value in zip(keys, spans)},
            "predicted_step_ms": spans[0], "sequences_per_replica": 1,
        }
        return gate.score_fleet_row(
            {"capture_id": "b1-prefill", "phase": "prefill", "hardware_tier": "A5", "observed_ms": math.fsum(spans)},
            observation, prediction,
        )

    bound = score({"directory": str(tmp_path)}, 1.0)
    unknown = score({"directory": str(tmp_path)}, 0.0)
    blind = score({})
    assert bound["source_scalar"]["population_label"] == "certified"
    assert bound["source_scalar"]["reducer"] == "sum"
    assert bound["source_scalar"]["producer"] == "dsh_scoped_prefill.score_prefill_capture"
    assert unknown["source_scalar"]["population_label"] == "conditional"
    assert blind["source_scalar"]["population_label"] == "conditional"
    assert unknown["comparison"] == "compared"
    assert unknown["passed_10pct"] is False
    assert unknown["source_scalar"]["predicted_aggregate_ms"] == bound["source_scalar"]["predicted_aggregate_ms"]
    assert blind["source_scalar"]["reducer"] == bound["source_scalar"]["reducer"]
    assert bound["source_scalar"]["passed_10pct"] is True
    assert unknown["source_scalar"]["passed_10pct"] is False
    decision = original._fleet_row_gate(unknown)
    assert decision["passed_10pct"] is False
    assert decision["ambiguous"] is False


def test_prediction_table_never_reads_observed_column_as_forecast() -> None:
    """A paired observed/predicted record keeps its predicted price; observed-only is absent."""
    import hf_sample_scoring as scoring
    import hf_fleet_source_producer as producer

    paired = {"predicted_ms": 3.25, "observed_ms": 9.5, "rel": 0.1}
    table = scoring._prediction_table({"boundary_samples": {"k": paired}})
    assert table == {"kind": "keyed", "pairs": [("k", 3.25)]}
    assert fleet_source._sample_value(paired) == 3.25
    assert fleet_source._sample_value({"observed_ms": 9.5}) is None
    absent = scoring._prediction_table({"boundary_samples": {"k": {"observed_ms": 9.5}}})
    assert absent["kind"] == "keyed" and absent["pairs"][0][0] == "k"
    assert absent["pairs"][0][1] is None
    observed = {"measurements": {"per_forward_window": {
        "status": "measured",
        "samples": [{"key": "k", "observed_ms": 6.974505727},
                    {"key": "k2", "observed_ms": 7.0}],
    }}}
    observed_table = scoring.observed_sample_table(observed, "per_forward_window")
    assert observed_table["status"] == "measured"
    assert observed_table["keys"] == ["k", "k2"]
    assert observed_table["values"][0] == 6.974505727


def test_source_declared_logical_populations_are_complete_and_unrounded(tmp_path: Path) -> None:
    """A source receipt may retain q=3 where the physical shape is padded q=4."""
    import hf_fleet_source_producer as producer

    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps({"observed": {"geometry_groups": [
        {"geometry": {"output_query_rows": 4},
         "forward_ids": ["f0", "f1"],
         "body_forward_span_ms": {"mean": 7.6453}},
        {"geometry": {"output_query_rows": 3},
         "forward_ids": ["f2"],
         "body_forward_span_ms": {"mean": 7.3836}},
    ]}}), encoding="utf-8")
    observation = {
        "source": {"sha256": "ab", "path": "/obs/kernel_details.csv"},
        "measurements": {"per_forward_window": {
            "status": "measured", "samples_basis": "elapsed_window_span_ms",
            "samples_ms": [7.0, 7.1, 7.2], "sample_keys": ["f0", "f1", "f2"],
            "frame_identifiers": [
                {"forward_id": "f0", "device_id": "0"},
                {"forward_id": "f1", "device_id": "0"},
                {"forward_id": "f2", "device_id": "0"},
            ],
            "geometry_populations": {"q=4,seq=4,tok=1": 3},
            "window_source": str(receipt),
        }},
    }
    contract = producer.producer_contract(
        {"capture_id": "ex", "phase": "decode"}, observation, [7.0, 7.1, 7.2],
        "elapsed_window_span_ms")
    assert contract["status"] == "ready"
    assert contract["producer"] == "source_declared_populations"
    assert contract["label"] == "source_population"
    assert len(contract["records"]) == 3
    weighted = (2 * 7.6453 + 7.3836) / 3
    assert statistics.fmean(item["value"] for item in contract["records"]) == pytest.approx(weighted)


def test_declared_total_missing_only_fails_when_original_declared_it() -> None:
    detail = {"groups": {"AI_CORE": {"predicted_ms": 1.0}}}
    assert fleet_source._family_total_matches({}, detail) is None
    assert fleet_source._family_total_matches({}, detail, declared_total=True) is False
    assert fleet_source._family_total_matches(
        {"predicted_operator_ms": None}, detail, declared_total=True) is False
