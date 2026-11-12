"""Source geometry and null-L4 applicability for the original cell account.

These checks use a fixture. They do not read a scratch path or the 6606 fleet.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _path in (str(ROOT), str(ROOT / "examples" / "structure"), str(ROOT.parent / "sim")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import hf_benchmark_gate as gate  # noqa: E402
import hf_original_account as original  # noqa: E402
import zero_shot_piecewise_validation as zsv  # noqa: E402

STEP_TRACE_MS = 12.516435149606298


def _source_cell() -> dict:
    return {
        "cell_id": "smoke_qwen36_single_dc_4k_c8",
        "dataset": "bench",
        "phase": "decode",
        "model_case": str(Path(__file__).resolve()),
        "model_label": "Qwen3.6-27B",
        "prompt_tokens": 4096,
        "concurrency": 8,
        "max_tokens": 128,
        "tp": 2,
        "dp": 4,
        "ep": 1,
        "pp": 1,
        "graph_bucket": 8,
        "decode_steps": 127,
        "ttft_ms": None,
        "tpot_ms": None,
        "step_trace_ms": STEP_TRACE_MS,
        "success": True,
        "trace_quality": "ok",
        "trace": {
            "duration_us": STEP_TRACE_MS * 1000.0,
            "by_class": {"gemm": 1000.0, "attention": 500.0},
            "by_name": {},
            "counts": {},
            "step_us": [STEP_TRACE_MS * 1000.0] * 127,
            "incomplete": False,
        },
    }


def test_null_service_does_not_add_a_formal_l4() -> None:
    """A decode cell with null TPOT keeps L3 and does not invent decode_step_tpot."""
    cell = zsv.cell_from_dict(_source_cell())
    assert cell.spec.prompt_tokens == 4096
    assert cell.spec.concurrency == 8
    assert cell.spec.max_tokens == 128
    assert cell.spec.tp == 2 and cell.spec.dp == 4
    assert cell.spec.model_label == "Qwen3.6-27B"
    assert cell.decode_steps == 127
    prediction = zsv.Prediction(
        cell.spec.cell_id, cell.spec.model_label, 1,
        {"gemm": 0.2, "attention": 0.2}, {},
        6.3746, None, None, (), (), 6.3746, 0.0,
    )
    comparisons = zsv.compare_cell(cell, prediction)
    targets = {(item.level, item.target) for item in comparisons}
    assert ("L4", "decode_step_tpot") not in targets
    assert ("L4", "prefill_step_ttft") not in targets
    l3 = [item for item in comparisons if item.level == "L3"]
    assert len(l3) == 1
    assert l3[0].target == "decode_step_trace"
    assert len(l3[0].step_details) == 127
    assert l3[0].predicted_ms == 6.3746
    account = original.all_original_account([
        original._cell_record(_source_cell(), {"original_comparisons": comparisons}),
    ])
    assert account["id_denominator"] == 1
    assert account["original_cells"]["compared"] == 1
    assert account["original_cells"]["pending"] == 0
    assert account["original_cells"]["outside_scope"] == 0
    assert account["original_cells"]["l4_formal"] == 0
    assert account["original_cells"]["l4_outside"] == 1
    assert account["original_cells"]["l3_steps"] == 127
    assert account["original_cells"]["ttft_pass"] == 0
    assert account["nested"]["step_series"] == 127
    assert account["group_passed"] is False
    assert account["source_strict_pass"] is False


def test_enrollment_passes_the_complete_source_row(monkeypatch) -> None:
    """The call arm sees the source geometry. A normalized default is not accepted."""
    raw = _source_cell()
    seen: dict = {}

    def _predict(spec):
        seen["prompt_tokens"] = spec.prompt_tokens
        seen["concurrency"] = spec.concurrency
        seen["max_tokens"] = spec.max_tokens
        seen["tp"] = spec.tp
        seen["dp"] = spec.dp
        seen["model_label"] = spec.model_label
        return zsv.Prediction(
            spec.cell_id, spec.model_label, 1,
            {"gemm": 0.2}, {}, 6.3746, None, None, (), (), 6.3746, 0.0,
        )

    monkeypatch.setattr(zsv, "predict_cell", _predict)
    frozen = dict(raw)
    record = original._cell_record(raw, {"boundary_scope": "request_l4", "key_denominator": 8, "model_label": "unresolved", "prompt_tokens": 1, "tp": 1, "dp": 1})
    assert record["model_label"] == "Qwen3.6-27B"
    assert record["prompt_tokens"] == 4096
    assert record["tp"] == 2 and record["dp"] == 4
    produced, reason = original._run_compare_cell(record)
    assert reason == ""
    assert produced
    assert seen == {
        "prompt_tokens": 4096,
        "concurrency": 8,
        "max_tokens": 128,
        "tp": 2,
        "dp": 4,
        "model_label": "Qwen3.6-27B",
    }
    assert raw == frozen
    assert all(item.level != "L4" for item in produced)
    dropped = dict(record)
    for key in ("prompt_tokens", "concurrency", "max_tokens", "tp", "dp"):
        dropped.pop(key)
    missing, why = original._run_compare_cell(dropped)
    assert missing is None and why == "defaulted_source"


def test_forecast_step_is_not_replaced_by_a_historical_predicted_ms() -> None:
    """not_declared stays unknown. The returned predicted_step is the scalar."""
    row = {
        "capture_id": "registered_decode:glm53flash-a3-tp16-c4",
        "phase": "decode",
        "hardware_tier": "A3",
        "suite": "registered_decode",
        "observed_ms": 39.8413,
        "predicted_ms": 10.732872,
        "calibration_role": "not_declared",
        "source_calibration": {
            "origin": "not_declared",
            "evaluation_relation": "not_declared",
            "target_timing_used_to_fit": False,
            "rule_count": 0,
        },
    }
    prediction = {
        "status": "modeled",
        "prediction_boundary": "per_forward_window",
        "predicted_step_ms": 6.374629643722274,
        "predicted_ms": 99.0,
        "target_timing_used_to_fit": False,
    }
    observation = {
        "evidence_status": "missing",
        "measurements": {},
        "source": {},
        "capture": {"capture_id": row["capture_id"], "phase": "decode"},
        "observed_ms": None,
    }
    scored = gate.score_fleet_row(row, observation, prediction)
    assert scored["evaluation_relation"] == "not_declared"
    assert scored["source_predicted_step"] == 6.374629643722274
    assert scored["source_predicted_step"] != row["predicted_ms"]
    assert scored["source_observed_ms"] == 39.8413
    enrolled = gate.enroll_population([scored], [row], [], [])
    assert len(enrolled) == 1
    decision = original._fleet_row_gate(enrolled[0])
    assert decision["scalar_status"] == "compared"
    assert decision["ambiguous"] is False
    assert decision["scalar_passed_10pct"] is False
    assert decision["passed_10pct"] is False
    assert decision["operator_status"] == "unavailable"
    assert decision["source_observed_ms"] == row["observed_ms"]
    signed = (6.374629643722274 - 39.8413) / 39.8413
    assert decision["signed_error"] == signed
    account = gate.all_original_account(enrolled)
    assert account["id_denominator"] == 1
    assert account["strata"]["unknown"]["ids"] == 1
    assert account["strata"]["independent_holdout"]["ids"] == 0
    assert account["strata"]["coverage"]["ids"] == 0
    assert account["source_strict_pass"] is False
    assert account["row_gate"]["changed_by_per_key"] is False
