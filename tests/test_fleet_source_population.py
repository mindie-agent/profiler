"""Scope and denominator regression for the fleet gate.

The gate must keep the measured observation when a prediction is missing,
partial, wrong, or invalid. Counts come from ``hf_sample_scoring``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_benchmark_gate as gate  # noqa: E402
import hf_profiling_benchmark as benchmark  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def _forward_observation(keys: list[str]) -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "decode", "hardware_tier": "A5"},
        "source": {"sha256": "ab", "path": "/obs/kernel_details.csv"},
        "measurements": {"per_forward_window": {
            "status": "measured",
            "samples_basis": "elapsed",
            "samples": [
                {"key": key, "observed_ms": 10.0, "phase": "decode", "forward_id": key}
                for key in keys
            ],
        }},
    }


def _request_observation() -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "prefill", "hardware_tier": "A5"},
        "source": {"sha256": "ab", "path": "/obs/client.json"},
        "measurements": {"native_client_request": {
            "status": "measured",
            "phase": "prefill",
            "samples_basis": "elapsed",
            "samples": [{"key": "request:0", "observed_ms": 5.0, "phase": "prefill"}],
        }},
    }


def _calls_observation() -> dict:
    return {
        "capture": {"capture_id": "ex", "phase": "decode", "hardware_tier": "A5"},
        "source": {},
        "measurements": {"native_calls": {
            "status": "measured",
            "native_phase": "prefill",
            "source_sha256": "ab",
            "samples_basis": "elapsed_native_call_span_ms",
            "samples": [
                {"key": "call0", "observed_ms": 1.0, "phase": "prefill"},
                {"key": "call1", "observed_ms": 1.0, "phase": "prefill"},
            ],
        }},
    }


def _prediction(boundary: str, keys: list[str], *, status: str = "modeled", sha: str = "ab") -> dict:
    return {
        "status": status,
        "prediction_boundary": boundary,
        "boundary_basis": "elapsed",
        "capture_id": "ex",
        "phase": "decode",
        "hardware_tier": "A5",
        "source_sha256": sha,
        "boundary_samples": [
            {"key": key, "boundary_ms": 10.0, "phase": "decode", "forward_id": key}
            for key in keys
        ],
    }


def _row() -> dict:
    return {"capture_id": "ex", "suite": "unit", "phase": "decode", "hardware_tier": "A5"}


def test_missing_partial_wrong_and_unknown_scopes_stay_honest() -> None:
    """Independent counterexample. Prediction scope cannot rewrite the observation."""
    keys = ["f0", "f1", "f2"]
    observation = _forward_observation(keys)
    row = _row()

    missing = gate.score_fleet_row(row, observation, {})
    assert missing["boundary_scope"] == "forward_body"
    assert missing["population_boundary"] == "per_forward_window"
    assert missing["comparison"] == "uncovered"
    assert missing["key_denominator"] == 3
    assert missing["key_matched"] == 0
    assert missing["key_missing"] == 3
    assert missing["passed_10pct"] is False

    partial = gate.score_fleet_row(row, observation, _prediction("per_forward_window", ["f0"]))
    assert partial["boundary_scope"] == "forward_body"
    assert partial["comparison"] == "invalid"
    assert partial["comparison_reason"] == "sample_key_population_mismatch"
    assert partial["key_denominator"] == 3
    assert partial["key_matched"] == 1
    assert partial["key_missing"] == 2
    assert partial["group_passed_10pct"] is False

    wrong = gate.score_fleet_row(
        row, observation,
        {"status": "modeled", "prediction_boundary": "native_client_request",
         "boundary_basis": "elapsed", "capture_id": "ex", "phase": "decode", "hardware_tier": "A5",
         "boundary_samples": [{"key": "request:0", "boundary_ms": 10.0, "phase": "decode"}]},
    )
    assert wrong["boundary_scope"] == "forward_body"
    assert wrong["comparison_reason"] == "prediction_boundary_scope_mismatch"
    assert wrong["key_denominator"] == 3
    assert wrong["key_matched"] == 0
    assert wrong["key_missing"] == 3

    invented = gate.score_fleet_row(
        row, observation, _prediction("per_forward_totally_different_latencies", keys))
    assert invented["boundary_scope"] == "forward_body"
    assert invented["comparison"] != "compared"
    assert invented["key_denominator"] == 3
    assert invented["key_matched"] == 0
    assert invented["key_missing"] == 3
    assert invented["prediction_boundary"] == "per_forward_totally_different_latencies"

    invalid = gate.score_fleet_row(
        row, observation, _prediction("per_forward_window", keys, sha="cd"))
    assert invalid["boundary_scope"] == "forward_body"
    assert invalid["comparison"] == "invalid"
    assert invalid["key_denominator"] == 3
    assert invalid["key_matched"] == 0

    request = gate.score_fleet_row(
        row, _request_observation(), _prediction("per_forward_window", ["f0"]))
    assert request["boundary_scope"] == "request_l4"
    assert request["population_boundary"] == "native_client_request"
    assert request["key_denominator"] == 1
    assert request["key_missing"] == 1
    assert request["key_matched"] == 0

    calls = gate.score_fleet_row(
        {"capture_id": "ex", "suite": "operator_and_kernel_calibration_20261107",
         "phase": "decode", "hardware_tier": "A5"},
        _calls_observation(), {})
    assert calls["boundary_scope"] == "standalone"
    assert calls["comparison"] == "not_a_body_step"
    assert calls["key_denominator"] == 2
    assert calls["key_missing"] == 2
    assert calls["key_matched"] == 0

    unknown = gate.score_fleet_row(row, {"measurements": {}, "source": {}}, {})
    assert unknown["boundary_scope"] == "unknown"
    assert unknown["key_denominator"] is None
    assert unknown["key_missing"] is None
    assert unknown["boundary_scope"] != "forward_body"


def test_registered_source_relations_keep_in_sample_and_not_blind_groups() -> None:
    """72 in_sample and 91 not_blind stay inside the 306 registered source rows."""
    if not (benchmark.RESULTS_DIR / "decode.json").is_file():
        pytest.skip("structure results are not in this checkout")
    rows = benchmark._collect_structure_suites()[0]
    report = gate._identity_report([], rows)
    assert report["retained_source_relations"] == 306
    assert report["in_sample_group"] == 72
    assert report["not_blind_group"] == 91
    assert report["decode_in_sample"] == 68
    assert report["prefill_in_sample"] == 1
    assert report["not_blind"] == 77
    glm = report["by_id_role"]["registered_decode:glm53flash-a3-tp16-c4-livepre"]
    disclosed = {"evaluation_relation": "zero_shot", "calibration_role": "zero_shot", "coverage_only": False}
    gate._apply_source_role(disclosed, glm)
    assert disclosed["evaluation_relation"] == "in_sample"
    assert disclosed["coverage_only"] is True
    assert "zero_shot" not in str(disclosed["evaluation_relation"])


def _slice_observation(phase: str, raw_sha: str, frames: list[dict], receipt: str = "/receipts/same.json") -> dict:
    return {
        "measurements": {"per_forward_window": {
            "status": "measured",
            "raw_digest_verified": True,
            "raw_sha256": raw_sha,
            "source_sha256": raw_sha,
            "raw_path": "/kernels/same/kernel_details.csv",
            "window_source": receipt,
            "boundary": "per_forward_window_source_receipt",
            "frame_identifiers": frames,
        }},
    }


def _frame(phase: str, forward_id: str, start: int) -> dict:
    return {
        "phase": phase, "rank_id": "0", "device_id": "0", "forward_id": forward_id,
        "start_ns": start, "end_ns": start + 1000,
    }


def test_slice_role_follows_verified_windows_not_a_recomputed_label() -> None:
    """Same kernel, receipt, and key windows inherit the earliest calibration."""
    raw = "ab" * 32
    frames = [_frame("decode", "f0", 10), _frame("decode", "f1", 20)]
    other_phase = [_frame("prefill", "f0", 10), _frame("prefill", "f1", 20)]
    donor = {
        "capture_id": "wave5:donor", "suite": "wave5_20261031", "duration_ms": 1,
        "source_calibration": {
            "evaluation_relation": "regime_table_replay",
            "target_timing_used_to_fit": True,
            "calibration_role": "regime_table_replay",
        },
        "calibration_role": "regime_table_replay",
        "target_timing_used_to_fit": True,
    }
    extended = {
        "capture_id": "extended:alias", "suite": "extended_a3_a5_workstream_captures", "duration_ms": 999,
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
    }
    other = {
        "capture_id": "extended:other-phase", "suite": "extended_a3_a5_workstream_captures",
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
    }
    rows = [donor, extended, other]
    observations = [
        _slice_observation("decode", raw, frames),
        _slice_observation("decode", raw, frames, receipt="/receipts/other-file.json"),
        _slice_observation("prefill", raw, other_phase),
    ]
    report = gate.disclose_source_slices(
        [gate.slice_record(row, observation) for row, observation in zip(rows, observations)],
        rows,
    )
    cohort = report["cohort"]
    assert cohort["population_rows"] == 3
    assert cohort["measured_ids"] == 3
    assert cohort["id_window_rows"] == 6
    assert cohort["unique_physical_series"] == 2
    assert cohort["unique_physical_windows"] == 4
    assert cohort["alias_groups"] == 1
    assert report["alias_groups"][0]["conflict"] is False
    extended_info = report["by_id"]["extended:alias"]
    assert extended_info["inherited"] is True
    assert extended_info["donor_capture_id"] == "wave5:donor"
    assert extended_info["evaluation_relation"] == "regime_table_replay"
    assert extended_info["target_timing_used_to_fit"] is True
    labeled = {
        "capture_id": "extended:alias",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "calibration_role": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
        "target_timing_used_to_fit": False,
    }
    gate.apply_slice_disclosure(labeled, extended_info)
    assert labeled["capture_id"] == "extended:alias"
    assert labeled["evaluation_relation"] == "regime_table_replay"
    assert labeled["coverage_only"] is True
    assert labeled["target_timing_used_to_fit"] is True
    assert labeled["slice_role_inherited"] is True
    assert "zero_shot_piecewise_recomputed" not in labeled["evaluation_relation"]
    phase_info = report["by_id"]["extended:other-phase"]
    assert phase_info["inherited"] is False
    assert phase_info["evaluation_relation"] is None
    held = {
        "capture_id": "extended:other-phase",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
    }
    gate.apply_slice_disclosure(held, phase_info)
    assert held["evaluation_relation"] == "zero_shot_piecewise_recomputed"
    assert held["coverage_only"] is False
    conflict_donor = dict(donor)
    conflict_donor["capture_id"] = "wave5:donor"
    conflict_other = {
        "capture_id": "registered:other", "suite": "registered_decode",
        "source_calibration": {
            "evaluation_relation": "in_sample",
            "target_timing_used_to_fit": True,
            "calibration_role": "in_sample",
        },
        "calibration_role": "in_sample",
        "target_timing_used_to_fit": True,
    }
    conflict_alias = dict(extended)
    conflict_alias["capture_id"] = "extended:disputed"
    conflict_rows = [conflict_donor, conflict_other, conflict_alias]
    conflict_report = gate.disclose_source_slices(
        [gate.slice_record(row, _slice_observation("decode", raw, frames)) for row in conflict_rows],
        conflict_rows,
    )
    assert conflict_report["alias_groups"][0]["conflict"] is True
    conflicted = {
        "capture_id": "registered:other",
        "evaluation_relation": "in_sample",
        "calibration_role": "in_sample",
        "coverage_only": True,
        "target_timing_used_to_fit": True,
    }
    gate.apply_slice_disclosure(conflicted, conflict_report["by_id"]["registered:other"])
    assert conflicted["evaluation_relation"] == "in_sample"
    assert conflicted.get("slice_role_inherited") is not True
    disputed = {
        "capture_id": "extended:disputed",
        "evaluation_relation": "zero_shot_piecewise_recomputed",
        "coverage_only": False,
    }
    gate.apply_slice_disclosure(disputed, conflict_report["by_id"]["extended:disputed"])
    assert disputed["evaluation_relation"] == "zero_shot_piecewise_recomputed"
    assert disputed["coverage_only"] is False


def test_unobserved_ordinal_stays_distinct_from_a_missing_ttft() -> None:
    """A declared ordinal with no row is unobserved. A row without TTFT is missing."""
    interface = {
        "cell": {"cell_id": "cell-a", "phase": "prefill", "rack": "rack06", "missing_ordinals": [1]},
        "requests": [
            {"key": "cell-a|ordinal=0", "launch_ordinal": 0, "ttft_s": 0.2, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=2", "launch_ordinal": 2, "ttft_s": None, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
        ],
        "declarations": [
            {"key": "cell-a|ordinal=0", "ordinal": 0, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=1", "ordinal": 1, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
            {"key": "cell-a|ordinal=2", "ordinal": 2, "ttft_boundary": "client_send_to_first_sse_with_choices_may_empty"},
        ],
    }
    scored = gate.score_client_request_interface(interface, {})
    assert scored["capture_id"] == "cell-a"
    assert scored["key_denominator"] == 3
    assert scored["key_missing"] == 3
    assert set(scored["missing_keys"]) == {"cell-a|ordinal=0", "cell-a|ordinal=1", "cell-a|ordinal=2"}
    assert scored["request_ttft_absent"] == 1
    assert scored["request_ttft_unobserved"] == 1
    assert scored["request_ttft_orphans"] == 0
    assert scored["producer_rack"] == "rack06"
    assert scored["hardware_tier"] == ""
    assert scored["tpot_domain"] == "not_scored_on_request_ttft"
