"""Original identity count, unknown roles, and split diagnostic units.

A short fixture must not claim the reserved 6606+731 population. Archive
captures stay opt-in. These checks do not read a scratch path.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_benchmark_gate as gate  # noqa: E402
import hf_original_account as original  # noqa: E402
import hf_profiling_benchmark as hf  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402

STEP_TRACE_MS = 12.516435149606298


def _fleet(capture_id: str, **extra) -> dict:
    row = {
        "capture_id": capture_id,
        "identity_type": "fleet",
        "evaluation_relation": "in_sample_regime_calibration",
        "calibration_role": "in_sample_regime_calibration",
        "coverage_only": True,
        "target_timing_used_to_fit": True,
        "prediction_status": "modeled",
        "comparison": "invalid",
        "comparison_reason": "sample_key_population_mismatch",
        "boundary_scope": "forward_body",
        "population_boundary": "per_forward_window",
        "key_denominator": 4,
        "key_matched": 1,
        "key_missing": 3,
        "keys_over_10pct": 1,
        "group_passed_10pct": False,
    }
    row.update(extra)
    return row


def _cell(**extra) -> dict:
    row = {
        "cell_id": "cell-1",
        "capture_id": "cell-1",
        "identity_type": "zero_cell",
        "suite": "zero_shot",
        "phase": "decode",
        "calibration_role": "unspecified",
        "evaluation_relation": "",
        "coverage_only": False,
        "target_timing_used_to_fit": None,
        "ttft_ms": None,
        "tpot_ms": None,
        "step_trace_ms": STEP_TRACE_MS,
        "prediction_status": "modeled",
        "comparison": "compared",
        "comparison_reason": "exact_keyed_samples",
        "boundary_scope": "request_l4",
        "population_boundary": "native_client_request",
        "key_denominator": 8,
        "key_matched": 8,
        "key_missing": 0,
        "keys_over_10pct": 8,
        "group_passed_10pct": False,
        "original_comparisons": None,
    }
    row.update(extra)
    return row


def test_mixed_input_keeps_the_zero_cell_and_an_unknown_role() -> None:
    """One fleet id plus one zero cell is two identities. The cell is not holdout."""
    fleet = _fleet("fleet-1")
    cell = _cell()
    account = gate.all_original_account([fleet, cell])
    assert account["schema"] == original.SCHEMA
    assert account["id_denominator"] == 2
    assert account["enrolled"] == {"fleet_ids": 1, "zero_cells": 1}
    assert account["canonical_population"]["complete"] is False
    assert account["canonical_population"]["fleet_ids"] == 6606
    assert account["canonical_population"]["zero_cells"] == 731
    assert account["id_denominator"] != 6606
    assert account["strata"]["coverage"]["ids"] == 1
    assert account["strata"]["unknown"]["ids"] == 1
    assert account["strata"]["independent_holdout"]["ids"] == 0
    assert account["holdout_only"]["ids"] == 0
    assert account["nested"]["forward_window_keys"] == 4
    assert account["nested"]["client_requests"] == 8
    assert account["nested"]["standalone_calls"] == 0
    assert account["window_key_denominator"] == 4
    assert account["id_denominator"] != account["nested"]["client_requests"]
    assert account["labels"]["fitted"] == 1
    assert account["labels"]["missing"] == 1
    assert account["over"] == 1
    assert account["unresolved"]["conditional"] == 1
    assert account["original_cells"]["ttft_pass"] == 0
    assert account["original_cells"]["pending"] == 1
    assert account["original_cells"]["outside_scope"] == 1
    assert account["group_passed"] is False
    assert account["source_strict_pass"] is False
    assert account["global_unresolved"] is True
    dropped = gate.all_original_account([fleet])
    assert dropped["id_denominator"] == 1


def test_unspecified_role_is_unknown_until_lineage_is_present() -> None:
    """Mutating the source relation is what changes the stratum."""
    cell = _cell()
    assert gate._stratum_name(cell) == "unknown"
    mutated = dict(cell)
    mutated["evaluation_relation"] = "template_matched_heldout_replay"
    mutated["calibration_role"] = "template_matched_heldout_replay"
    assert gate._stratum_name(mutated) == "independent_holdout"
    cleared = dict(mutated)
    cleared["evaluation_relation"] = ""
    cleared["calibration_role"] = "unspecified"
    assert gate._stratum_name(cleared) == "unknown"
    account = gate.all_original_account([cleared])
    assert account["strata"]["unknown"]["ids"] == 1
    assert account["strata"]["independent_holdout"]["ids"] == 0
    assert account["id_denominator"] == 1


def test_client_and_window_counts_do_not_become_gate_ids() -> None:
    """6820-sized client keys and a large window count stay nested."""
    fleet = _fleet("fleet-1", key_denominator=302422, key_matched=1, key_missing=302421, keys_over_10pct=1)
    standalone = _fleet(
        "fleet-2",
        boundary_scope="standalone",
        population_boundary="native_calls",
        key_denominator=5,
        key_matched=5,
        key_missing=0,
        keys_over_10pct=0,
        comparison="not_a_body_step",
        standalone_comparison="compared",
        standalone_reason="",
        prediction_status="modeled",
    )
    cell = _cell(key_denominator=6820, key_matched=6820, keys_over_10pct=6820, group_passed_10pct=True)
    account = gate.all_original_account([fleet, standalone, cell])
    assert account["id_denominator"] == 3
    assert account["enrolled"]["fleet_ids"] == 2
    assert account["enrolled"]["zero_cells"] == 1
    assert account["nested"]["forward_window_keys"] == 302422
    assert account["nested"]["standalone_calls"] == 5
    assert account["nested"]["client_requests"] == 6820
    assert account["nested"]["step_series"] == 0
    assert account["group_passed"] is False
    assert account["source_strict_pass"] is False
    assert account["original_cells"]["ttft_pass"] == 0
    assert "pass_rate" not in account


def test_compare_cell_step_series_does_not_pass_a_null_ttft() -> None:
    """The original protocol keeps step details and does not pass a null TTFT."""
    cell_row = {
        "cell_id": "tiny-decode",
        "phase": "decode",
        "dataset": "bench",
        "model_case": str(Path(__file__).resolve()),
        "model_label": "synthetic",
        "ttft_ms": None,
        "tpot_ms": None,
        "step_trace_ms": STEP_TRACE_MS,
        "decode_steps": 2,
        "success": True,
        "trace_quality": "ok",
        "trace": {
            "duration_us": 2000.0,
            "by_class": {"gemm": 1000.0, "attention": 1000.0},
            "by_name": {},
            "counts": {},
            "step_us": [STEP_TRACE_MS * 1000.0, STEP_TRACE_MS * 1000.0],
            "incomplete": False,
        },
    }
    measured = zsv.cell_from_dict(cell_row)
    prediction = zsv.Prediction(
        "tiny-decode", "synthetic", 1,
        {"gemm": 0.2, "attention": 0.2}, {},
        20.0, None, None, (), (), 20.0, 0.0,
    )
    comparisons = zsv.compare_cell(measured, prediction)
    assert comparisons
    enrolled = _cell(
        cell_id="tiny-decode",
        capture_id="tiny-decode",
        original_comparisons=comparisons,
        step_trace_ms=STEP_TRACE_MS,
    )
    account = original.all_original_account([enrolled])
    assert account["id_denominator"] == 1
    assert account["original_cells"]["ttft_pass"] == 0
    assert account["original_cells"]["pending"] == 0
    assert account["nested"]["step_series"] >= 1
    assert account["nested"]["step_series"] != account["id_denominator"]
    assert account["group_passed"] is False
    assert account["source_strict_pass"] is False
    levels = {item.level for item in comparisons}
    assert "L3" in levels or "L1" in levels


def test_low_count_can_pass_its_own_protocol_without_a_source_strict_pass() -> None:
    """A passing pair is not the reserved 6606+731 population."""
    fleet = _fleet(
        "fleet-ok",
        comparison="compared",
        comparison_reason="",
        key_denominator=1,
        key_matched=1,
        key_missing=0,
        keys_over_10pct=0,
        group_passed_10pct=True,
        target_timing_used_to_fit=False,
        coverage_only=False,
        evaluation_relation="template_matched_heldout_replay",
        calibration_role="template_matched_heldout_replay",
        source_observed_ms=10.0,
        source_predicted_step=10.5,
        operator_family_abs_errors=[0.02],
        operator_core_abs_errors=[0.04],
        operator_uncancelled_ratio=0.01,
    )
    within = {
        "level": "L3",
        "target": "decode_step_trace",
        "measured_ms": 12.516435149606298,
        "predicted_ms": 13.0,
        "guard": "declared",
        "operator": "body",
        "uncancelled_ms": 0.1,
        "step_details": ((0, 12.516435149606298, 13.0, (13.0 - 12.516435149606298) / 12.516435149606298),),
    }
    cell = _cell(
        key_denominator=0,
        key_matched=0,
        key_missing=0,
        keys_over_10pct=0,
        boundary_scope="forward_body",
        population_boundary="",
        comparison="uncovered",
        prediction_status="modeled",
        original_comparisons=[within],
        phase="decode",
    )
    # A client boundary with a null service target would be ambiguous. This cell
    # carries only the compare_cell series, so the protocol can pass on its own.
    cell["boundary_scope"] = ""
    account = original.all_original_account([fleet, cell])
    assert account["group_passed"] is True
    assert account["source_strict_pass"] is False
    assert account["canonical_population"]["complete"] is False
    assert account["id_denominator"] == 2
    assert account["original_cells"]["ttft_pass"] == 0
    assert account["nested"]["step_series"] == 1
    assert account["strata"]["independent_holdout"]["ids"] == 1
    assert account["strata"]["unknown"]["ids"] == 1


def _dataset(root: Path, fleet: dict, cell: dict) -> Path:
    data = root / "data"
    data.mkdir(parents=True)
    fleet_blob = (json.dumps(fleet, sort_keys=True) + "\n").encode()
    cell_blob = (json.dumps({k: v for k, v in cell.items() if k != "original_comparisons"}, sort_keys=True) + "\n").encode()
    for name, blob in (("fleet_captures.jsonl", fleet_blob), ("zero_shot_l1_l4_cells.jsonl", cell_blob)):
        (data / name).write_bytes(blob)
        (data / f"{name}.gz").write_bytes(gzip.compress(blob, mtime=0))
    return root


@pytest.fixture
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")


def test_direct_score_and_dataset_entry_share_the_mixed_aggregate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolate: None) -> None:
    """score_fleet_row and evaluate_dataset enroll the same two identities."""
    monkeypatch.setattr(hf, "_collect_structure_suites", lambda: ([], set()))
    fleet_row = {
        "capture_id": "fleet-1",
        "phase": "decode",
        "hardware_tier": "A5",
        "suite": "synthetic",
        "source_calibration": {
            "evaluation_relation": "in_sample_regime_calibration",
            "target_timing_used_to_fit": True,
        },
    }
    cell_row = {
        "cell_id": "cell-1",
        "phase": "decode",
        "ttft_ms": None,
        "tpot_ms": None,
        "step_trace_ms": STEP_TRACE_MS,
        "success": True,
    }
    observation = {"evidence_status": "missing", "measurements": {}, "source": {}, "capture": {"capture_id": "fleet-1", "phase": "decode"}}

    def _predict(cfg: dict) -> dict:
        return {"status": "missing", "capture_id": cfg.get("capture_id")}

    def _requests(row: dict) -> dict:
        return {"eligible": False, "reason": "stub", "streams": 0}

    monkeypatch.setattr(hf, "predict_capture_operators_and_step", _predict)
    monkeypatch.setattr(hf, "_zero_shot_l4_pair", _requests)
    import fleet_capture_observations as observations
    monkeypatch.setattr(observations, "extract_capture_observations", lambda cfg: observation)
    previous_index = gate._IDENTITY_INDEX
    gate._IDENTITY_INDEX = None
    try:
        summary = hf.evaluate_dataset(_dataset(tmp_path / "ds", fleet_row, cell_row), inventory="targeted", summary_dir=tmp_path / "out")
        direct = gate.score_fleet_row(fleet_row, observation, _predict(fleet_row))
    finally:
        gate._IDENTITY_INDEX = previous_index
    l4 = json.loads((tmp_path / "out" / "zs_l4_per_id.jsonl").read_text(encoding="utf-8").splitlines()[0])
    enrolled = gate.enroll_population([direct], [fleet_row], [l4], [cell_row])
    account = gate.all_original_account(enrolled)
    published = summary["all_original"]
    assert published["id_denominator"] == account["id_denominator"] == 2
    assert published["enrolled"] == account["enrolled"] == {"fleet_ids": 1, "zero_cells": 1}
    assert published["strata"]["coverage"]["ids"] == 1
    assert published["strata"]["unknown"]["ids"] == 1
    assert published["strata"]["independent_holdout"]["ids"] == 0
    assert published["original_cells"]["ttft_pass"] == 0
    assert published["original_cells"]["pending"] == 1
    assert published["group_passed"] is False
    assert published["source_strict_pass"] is False
    assert summary["strict_global_pass"] is False
    assert direct["target_timing_used_to_fit"] is True
    assert direct["coverage_only"] is True
    assert direct["group_passed_10pct"] is False
