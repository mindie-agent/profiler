"""L1-L4 comparison, markdown and end-to-end projection tests.

[Role] Exercise the report projection extracted from the validator at its own
  boundaries: per-step distributions, cancellation, diagnosis selection and the
  baseline JSON/markdown.
[Invariants] Predictions stay measurement-blind; measured fields are read only
  after the prediction is frozen.
[Timeouts & Locks] Bounded local fixtures; no external dataset is required.
[Side-Effect Policy] Writes only under pytest ``tmp_path``.
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import zero_shot_piecewise_validation as z  # noqa: E402
from test_zero_shot_piecewise_validation import (  # noqa: E402
    MODEL_CASE, fake_cell, fake_prediction, fake_row, make_corpus,
    write_kernel_csv, write_measured,
)


@pytest.fixture(scope="module")
def compact_qwen38(tmp_path_factory):
    doc = json.loads(MODEL_CASE.read_text(encoding="utf-8"))
    doc["model"]["layers"] = 4
    if "layer_plans" in doc["model"]:
        doc["model"]["layer_plans"] = list(doc["model"]["layer_plans"])[:4]
    dst = tmp_path_factory.mktemp("zspc_case") / "compact_qwen38.json"
    dst.write_text(json.dumps(doc), encoding="utf-8")
    return dst


def test_compare_cell_builds_l1_to_l4_and_survives_absent_measured_class(tmp_path, compact_qwen38):
    root = make_corpus(tmp_path, model_case=compact_qwen38)
    cell = z.attach_trace(z.discover_workstream(root)[0])
    prediction = z.predict_cell(replace(cell.spec, prompt_tokens=128, max_tokens=1))
    comparisons = z.compare_cell(cell, prediction)
    levels = {item.level for item in comparisons}
    targets = {item.target for item in comparisons}
    assert {"L1", "L2", "L3", "L4"}.issubset(levels)
    assert {"gemm", "attention", "decode_step_trace", "decode_step_tpot"}.issubset(targets)
    assert "prefill_step_ttft" not in targets
    assert not {"forward_body", "tpot", "ttft"} & targets
    for item in comparisons:
        assert item.operator and item.guard is not None
        assert math.isfinite(item.unsigned_error) or item.measured_ms <= 0
    for item in comparisons:
        if item.target == "decode_step_trace":
            assert item.measured_ms == pytest.approx(cell.step_trace_ms)
            assert item.step_details and all(detail[1] > 0 for detail in item.step_details)

def test_per_step_latency_error_reports_distribution_and_cancellation():
    spec = z.CellSpec("steps", "test", "decode", None, "fake", 1, 1, 1, 1, 1, 1, 1)
    trace = z.KernelTrace(4.2, {}, {"GemmV3": 4.0, "HcPre": 0.2},
                          step_us=(900.0, 1100.0, 1000.0, 1200.0))
    cell = z.MeasuredCell(spec, (), trace, None, 1.0, 1.05, 4, True)
    prediction = z.Prediction("steps", "fake", 1, {"gemm": 1.0}, {}, 1.0, 1.3,
                              None, (), (), 1.0, 1.2)
    comparisons = z.compare_cell(cell, prediction)
    trace_cmp = next(item for item in comparisons if item.target == "decode_step_trace")
    assert len(trace_cmp.step_details) == 4
    assert trace_cmp.measured_ms == pytest.approx(1.05)
    assert [detail[3] for detail in trace_cmp.step_details] == pytest.approx(
        [(1.0 - 0.9) / 0.9, (1.0 - 1.1) / 1.1, 0.0, (1.0 - 1.2) / 1.2])
    row = next(item for item in z.aggregate(comparisons)
               if item["target"] == "decode_step_trace")
    assert row["samples"] == 4 and row["cells"] == 1
    assert row["step_err_p50"] == pytest.approx((0.1 / 1.1 + 0.1 / 0.9) / 2, abs=1e-6)
    assert row["step_err_p90"] == pytest.approx(0.2 / 1.2, abs=1e-6)
    assert row["step_err_max"] == pytest.approx(0.2 / 1.2)
    assert row["signed_p50"] < 0 and row["signed_p50"] > -0.2 / 1.2
    assert "pass_rate_10pct" in row and 0.0 <= row["pass_rate_10pct"] <= 1.0
    assert row["uncancelled_p50"] >= 0.0

def test_markdown_uses_bilingual_terms_and_per_step_columns(tmp_path, compact_qwen38):
    root = make_corpus(tmp_path, model_case=compact_qwen38)
    write_measured(root / "case" / "measured" / "case_dc_1k_c1.json", model_case=str(compact_qwen38), prompt_tokens=128, max_tokens=1)
    result = z.run_validation(roots=(root,), include_historical=False)
    summary = z.render_markdown(result)
    for marker in ("Per-Step Latency Error", "单步耗时误差", "step_err_p50",
                   "step_err_p90", "step_err_max", "signed_p50",
                   "uncancelled_p50", "<=10% pass",
                   "Decode 单步耗时",
                   "Unmodeled Operation / Boundary Mismatch (未建模算子或边界偏差)",
                   "Fusion Boundary Mismatch (算子融合边界偏差)",
                   "Collective Communication Skew / Latency (集合通信慢卡倾斜或握手延迟)",
                   "Tile / Core Wave Quantization (分块与核波次量化效应)",
                   "Memory Alignment Amplification (访存粒度对齐放大)"):
        assert marker in summary, marker
    assert "Prefill 单步耗时" in z._STEP_LABELS["prefill_step_ttft"]

# ---------------------------------------------------------------------------
# Diagnosis taxonomy

def test_threshold_is_strictly_ten_percent():
    cell = fake_cell()
    row = fake_row()
    comparison = z.Comparison("L1", "gemm", "gemm", 1.05, 1.0, "op", "g", "cube", "f", 1)
    assert z.diagnose(comparison, cell, fake_prediction(row)) is None
    above = replace(comparison, predicted_ms=1.11)
    assert z.diagnose(above, cell, fake_prediction(row)) is not None

def test_tiling_wave_step_is_selected_from_discrete_guard():
    cell = fake_cell()
    row = fake_row(regime=(("M_TILES", 2), ("SPLITS", 8)))
    comparison = z.Comparison("L1", "gemm", "gemm", 2.0, 1.0, "gate_up", "M_TILES=2", "hbm",
                              "stage0 cube", 3)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "tiling_wave_step"
    assert "TAIL" not in diagnosis.required_fix
    assert "ceil(tiles/cores)" in diagnosis.required_fix

def test_mte2_granule_amplification_is_selected_from_dominant_pipe():
    cell = fake_cell()
    row = fake_row(pipe="mte2")
    comparison = z.Comparison("L1", "gemm", "gemm", 2.0, 1.0, "gate_up", "g", "mte2",
                              "stage0 mte2", 3)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "mte2_granule_amplification"
    assert "granule" in diagnosis.required_fix

def test_fusion_boundary_is_selected_from_dominant_fused_kernel():
    cell = fake_cell(names=("FusedInferAttentionScore",))
    row = fake_row(pipe="cube", mechanism="attention", target="attention")
    comparison = z.Comparison("L1", "attention", "attention", 2.0, 1.0, "attention", "g",
                              "cube", "stage0", 1)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "fusion_boundary"
    assert "fusion" in diagnosis.required_fix

def test_collective_skew_is_selected_for_communication_family():
    cell = fake_cell()
    row = fake_row(pipe="link", mechanism="collective", target="collective")
    comparison = z.Comparison("L1", "collective", "collective", 2.0, 1.0, "dispatch", "g",
                              "link", "stage0", 1)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(row))
    assert diagnosis and diagnosis.physical_mechanism == "collective_skew"
    assert "slowest-rank skew" in diagnosis.required_fix

def test_structural_gap_is_selected_for_missing_or_service_boundary():
    cell = fake_cell()
    missing = z.Comparison("L1", "indexer", "indexer", 0.0, 1.0, "missing:indexer", "g",
                           "", "", -1)
    assert z.diagnose(missing, cell, fake_prediction(None)).physical_mechanism == \
        "confirmed_structural_gap"
    service = z.Comparison("L4", "tpot", "service", 2.0, 1.0, "service_framework", "g",
                           "host", "body", -1)
    assert z.diagnose(service, cell, fake_prediction(None)).physical_mechanism == \
        "confirmed_structural_gap"

def test_uncancelled_l1_component_error_is_a_fusion_boundary():
    cell = fake_cell()
    comparison = z.Comparison("L2", "moe", "moe", 1.0, 1.0, "expert_gate_up", "g", "cube",
                              "stage0", 1, uncancelled_ms=0.5)
    diagnosis = z.diagnose(comparison, cell, fake_prediction(None))
    assert diagnosis and diagnosis.physical_mechanism == "fusion_boundary"
    assert "cancel" in diagnosis.required_fix

def test_aggregate_counts_unmatched_prediction_without_infinite_means():
    valid = z.Comparison("L1", "gemm", "gemm", 1.2, 1.0, "op", "g", "cube", "f", 1)
    unmatched = z.Comparison("L1", "indexer", "indexer", 0.1, 0.0, "missing", "g", "", "", -1)
    rows = z.aggregate((valid, unmatched))
    row, absent = next(item for item in rows if item["target"] == "gemm"), next(item for item in rows if item["target"] == "indexer")
    assert row["samples"] == 1 and row["unmatched"] == 0 and row["pass_rate_10pct"] == 0.0
    assert row["step_err_p50"] == pytest.approx(0.2) and row["step_err_max"] == pytest.approx(0.2) and row["signed_p50"] == pytest.approx(0.2)
    assert absent["samples"] == 0 and absent["unmatched"] == 1 and math.isfinite(absent["signed_error_mean"]) and math.isfinite(absent["step_err_p90"])

def test_end_to_end_baseline_runs_over_synthetic_fleet_cell(tmp_path, compact_qwen38):
    root = make_corpus(tmp_path, model_case=compact_qwen38)
    write_measured(root / "case" / "measured" / "case_dc_1k_c1.json", model_case=str(compact_qwen38), prompt_tokens=128, max_tokens=1)
    result = z.run_validation(roots=(root,), include_historical=False)
    assert result["coverage"]["cells"] == 1 and result["coverage"]["evaluated"] == 1 and result["coverage"]["failed"] == 0
    assert result["measurement_blind"] is True and result["levels"] and result["diagnoses"] and result["coverage"]["step_samples"] >= 1 and result["step_errors"]
    assert {"cell", "level", "target", "step", "measured_ms", "predicted_ms", "signed_error"} == set(result["step_errors"][0])
    assert set(result["diagnosis_counts"]) <= {"confirmed_structural_gap", "mte2_granule_amplification", "tiling_wave_step", "fusion_boundary", "collective_skew"}
    summary = z.render_markdown(result)
    assert all(s in summary for s in ("Zero-shot piecewise validation baseline", "Coverage by level", "Physical diagnoses", "forbidden lookup imported: False"))

