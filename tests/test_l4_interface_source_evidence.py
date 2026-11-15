"""Production L4 interface keeps recovered source identity and timing."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_benchmark_gate as gate  # noqa: E402
import hf_benchmark_report as report  # noqa: E402
import hf_request_ttft as request_ttft  # noqa: E402


@pytest.fixture(autouse=True)
def _restore_gate_identity_index():
    """Keep evaluate's global identity index from leaking into other tests."""
    previous = gate._IDENTITY_INDEX
    try:
        yield
    finally:
        gate._IDENTITY_INDEX = previous


BOUNDARY = "client_send_to_first_sse_with_choices_may_empty"


def _synthetic_interface(cell_id: str = "cell-a") -> dict:
    return {
        "cell": {"cell_id": cell_id, "phase": "prefill", "producer_sha256": "p" * 64},
        "requests": [{
            "key": "request:0",
            "launch_ordinal": 0,
            "ttft_s": 0.407916,
            "ttft_boundary": BOUNDARY,
        }],
        "declarations": [{"key": "request:0", "ordinal": 0, "ttft_boundary": BOUNDARY}],
    }


def _synthetic_prediction(cell_id: str = "cell-a") -> dict:
    return {
        "status": "modeled",
        "prediction_boundary": "native_client_request",
        "capture_id": cell_id,
        "phase": "prefill",
        "source_sha256": "f" * 64,
    }


def _synthetic_observation(cell_id: str = "cell-a") -> dict:
    return {
        "capture": {"capture_id": cell_id, "phase": "prefill"},
        "source": {"independent": True, "sha256": "a" * 64},
        "measurements": {"native_client_request": {
            "status": "measured",
            "samples": [{"key": "request:0", "observed_ms": 407.916}],
        }},
    }


def _evaluate_bundle(tmp_path: Path, monkeypatch, bundle: dict, row: dict, name: str):
    """Drive the visible evaluate writer and return its JSONL row + summary."""
    report._bind()
    monkeypatch.setattr(
        report, "load_verified_table",
        lambda path, gz_path: ([row], "x") if "zero_shot" in str(path) else ([], "x"),
    )
    summary_dir = tmp_path / name
    summary = report.evaluate(
        tmp_path / "bench_root",
        strict_10pct=False,
        inventory="targeted",
        summary_dir=summary_dir,
        identity_builder=None,
        simulator_name="test",
        predict=lambda cfg: {},
        observe=lambda cfg: {},
        run_validation=None,
        zero_shot_requests=lambda source_row: bundle,
    )
    item = json.loads(
        (summary_dir / "zs_l4_per_id.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    return item, summary


def test_interface_scorer_merges_actual_source_and_reports_mismatch() -> None:
    scored = request_ttft.score_client_request_interface(
        _synthetic_interface(),
        _synthetic_prediction(),
        hardware_tier="A5",
        source_observation=_synthetic_observation(),
    )
    assert scored["comparison"] == "invalid"
    assert scored["comparison_reason"] == "source_sha256_mismatch"
    assert scored["source_sha256"] == "a" * 64
    assert scored["observed_ms"] == pytest.approx(407.916)
    assert scored["prediction_scalar_present"] is False
    assert scored["evidence_status"] == "measured"
    assert scored["sample"] is None
    assert scored["key_denominator"] == 1
    assert scored["key_matched"] == 0


def test_score_l4_bundle_preserves_declaration_actual_and_eligibility() -> None:
    bundle = {
        "eligible": True,
        "reason": "source_config_sha256_mismatch",
        "source_raw": "uncertain",
        "observed_ms": 407.916,
        "declared_config_sha256": "f" * 64,
        "source_config_sha256": "a" * 64,
        "source_file_sha256": "a" * 64,
        "source_origin": "source_file",
        "measurement_path": "/measured/request.json",
        "measurement_sha256": "b" * 64,
        "interface": _synthetic_interface(),
        "observation": _synthetic_observation(),
        "prediction": _synthetic_prediction(),
    }
    scored = report.score_l4_bundle(
        {"cell_id": "cell-a", "phase": "prefill", "hardware_tier": "A5"},
        bundle,
        tier="A5",
    )
    assert scored["comparison"] == "invalid"
    assert scored["comparison_reason"] == "source_sha256_mismatch"
    assert scored["l4_eligible"] is True
    assert scored["observed_ms"] == pytest.approx(407.916)
    assert scored["declared_config_sha256"] == "f" * 64
    assert scored["source_config_sha256"] == "a" * 64
    assert scored["source_file_sha256"] == "a" * 64
    assert scored["source_origin"] == "source_file"
    assert scored["source_sha256"] == "b" * 64
    assert scored["measurement_sha256"] == "b" * 64
    assert scored["measurement_path"] == "/measured/request.json"
    assert scored["source_evidence"]["measurement"]["sha256"] == "b" * 64
    assert scored["source_evidence"]["config"]["file_sha256"] == "a" * 64
    assert scored["source_evidence"]["identity"]["status"] == "conflict"
    assert scored["source_raw"] == "uncertain"
    assert scored["l4_reason"] == "source_config_sha256_mismatch"
    assert scored["prediction_scalar_present"] is False
    assert scored["sample"] is None
    assert scored["passed_10pct"] is False


def test_legal_bench_file_without_deployment_is_not_a_conflict() -> None:
    interface = _synthetic_interface("bench-cell")
    prediction = {
        "status": "modeled",
        "prediction_boundary": "native_client_request",
        "boundary_basis": "singleton_request_ttft_ms",
        "boundary_ms": 412.0,
        "capture_id": "bench-cell",
        "phase": "prefill",
        "source_sha256": "a" * 64,
    }
    bundle = {
        "eligible": True,
        "interface": interface,
        "observation": _synthetic_observation("bench-cell"),
        "prediction": prediction,
        "declared_config_sha256": "a" * 64,
        "source_file_sha256": "a" * 64,
        "source_config_sha256": "a" * 64,
        "source_deploy_sha256": "",
        "source_origin": "source_file",
        "measurement_path": "/measured/bench.json",
        "measurement_sha256": "b" * 64,
    }
    scored = report.score_l4_bundle(
        {"cell_id": "bench-cell", "phase": "prefill", "hardware_tier": "A5"},
        bundle, tier="A5",
    )
    assert scored["comparison"] == "compared"
    assert scored["comparison_reason"] == "exact_keyed_samples"
    assert scored["source_identity"]["status"] == "clear"
    assert scored["sample"] == pytest.approx((412.0 - 407.916) / 407.916)
    assert scored["prediction_scalar_present"] is True


def test_non_p6_correct_source_singleton_is_assembled_and_compared(
    tmp_path: Path, monkeypatch
) -> None:
    sha = "a" * 64
    bundle = {
        "eligible": True,
        "streams": 1,
        "key": "request:0",
        "observed_ms": 407.916,
        "measurement_path": "/measured/request.json",
        "measurement_sha256": "b" * 64,
        "source_config": str(tmp_path / "config.json"),
        "source_config_sha256": sha,
        "source_file_sha256": sha,
        "source_deploy_sha256": "",
        "prediction": {
            "status": "modeled",
            "prediction_boundary": "native_client_request",
            "boundary_basis": "singleton_request_ttft_ms",
            "boundary_ms": 407.916,
            "capture_id": "cell-single",
            "phase": "prefill",
            "source_sha256": sha,
            "hardware_tier": "A5",
        },
    }
    row = {"cell_id": "cell-single", "phase": "prefill", "hardware_tier": "A5"}
    scored = report.score_l4_bundle(row, bundle, tier="A5")
    assert scored["comparison"] == "compared"
    assert scored["comparison_reason"] == "exact_keyed_samples"
    assert scored["observed_ms"] == pytest.approx(407.916)
    assert scored["streams"] == 1
    assert scored["n_samples"] == 1
    assert scored["key_denominator"] == 1
    assert scored["key_matched"] == 1
    assert scored["key_missing"] == 0
    assert scored["unpaired_count"] == 0
    assert scored["prediction_scalar_present"] is True
    assert scored["sample"] == pytest.approx(0.0)
    assert scored["evidence_status"] == "measured"
    assert scored["source_identity"]["status"] == "clear"

    item, summary = _evaluate_bundle(tmp_path, monkeypatch, bundle, row, "singleton-non-p6")
    assert item["comparison"] == "compared"
    assert item["comparison_reason"] == "exact_keyed_samples"
    assert item["n_samples"] == 1
    assert item["key_denominator"] == 1
    assert item["key_matched"] == 1
    assert item["key_missing"] == 0
    assert item["unpaired_count"] == 0
    assert item["prediction_scalar_present"] is True
    assert item["sample"] == pytest.approx(0.0)
    assert summary["l4_scoring"] == {
        "rows": 1, "invalid": 0, "unknown": 0,
        "reasons": {"exact_keyed_samples": 1},
        "n_samples": 1, "key_denominator": 1, "key_matched": 1,
        "key_missing": 0, "unpaired_count": 0, "unpaired_prediction_count": 0,
    }


def test_non_p6_absent_population_is_held_without_inventing_a_sample(
    tmp_path: Path, monkeypatch
) -> None:
    bundle = {
        "eligible": False,
        "reason": "observation_absent",
        "streams": 0,
        "key": "request:0",
        "observed_ms": None,
    }
    row = {"cell_id": "cell-absent", "phase": "prefill", "hardware_tier": "A5"}
    scored = report.score_l4_bundle(row, bundle, tier="A5")
    assert scored["comparison"] == "uncovered"
    assert scored["comparison_reason"] == "observation_absent"
    assert scored["l4_eligible"] is False
    assert scored["n_samples"] == 0
    assert scored["key_denominator"] == 0
    assert scored["key_matched"] == 0
    assert scored["key_missing"] == 0
    assert scored["unpaired_count"] == 0
    assert scored["prediction_scalar_present"] is False
    assert scored["sample"] is None
    assert scored["prediction_status"] == "not_a_singleton"

    item, summary = _evaluate_bundle(tmp_path, monkeypatch, bundle, row, "absent-non-p6")
    assert item["comparison"] == "uncovered"
    assert item["comparison_reason"] == "observation_absent"
    assert item["n_samples"] == 0
    assert item["key_denominator"] == 0
    assert item["key_missing"] == 0
    assert item["sample"] is None
    assert summary["l4_scoring"] == {
        "rows": 1, "invalid": 0, "unknown": 1,
        "reasons": {"observation_absent": 1},
        "n_samples": 0, "key_denominator": 0, "key_matched": 0,
        "key_missing": 0, "unpaired_count": 0, "unpaired_prediction_count": 0,
    }
    assert summary["scopes"]["request_l4"]["unknown"] == 1
