"""Reproduction probes for Codex Astra max audit findings on zero-shot validation.

[Role]
  Verify all 12 P0/P1/P2 audit invariants (Probes 1-12) and source-level
  denylist constraints on ``examples/structure/zero_shot_piecewise_validation.py``.

[Invariants]
  * Pure Tier-0 in-memory/tmp_path execution (< 5s); zero host pollution.
  * Predictions depend strictly on ``CellSpec`` and declared model/hardware
    specifications, never on ``MeasuredCell`` durations or kernel counts.

[Timeouts & Locks]
  Deterministic in-process unit tests; no subprocesses, locks, or timers.

[Side-Effect Policy]
  Writes only to pytest ``tmp_path`` fixtures; default trace loading writes no
  cache files.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from examples.structure import zero_shot_piecewise_validation as z

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "examples" / "structure" / "zero_shot_piecewise_validation.py"
MODEL_CASE = ROOT / "examples" / "structure" / "cases" / "decode-a5_qwen38_highconc_c4.json"


def _write_csv(path: Path, rows: tuple[tuple[str, str, float, float], ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["Step Id,Model ID,Task ID,Stream ID,Name,Type,Accelerator Core,Start Time(us),Duration(us),Wait Time(us)"]
    for idx, (name, typ, start_us, dur_us) in enumerate(rows):
        core = "HCCL" if name.startswith("hcom_") or "alltoall" in name.lower() else "AI_CORE"
        lines.append(f"1,1,{idx},1,{name},{typ},{core},{start_us},{dur_us},0")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_source_denies_fitted_corrections() -> None:
    text = VALIDATOR.read_text(encoding="utf-8")
    banned = (
        "_EP_S",
        "_qwen_l1_scale",
        "_k3_l1",
        "_ep1_l1_scale",
        "_UG",
        "_VG",
        "_clean_ep1_cell",
        "_pf_op_geometry",
        "gettempdir",
    )
    for name in banned:
        assert name not in text, f"Forbidden fitted symbol {name} present in validator"
    assert "measurement_blind" in text
    assert z._source_is_blind() is True
    for file_path in (
        VALIDATOR,
        ROOT / "tests" / "test_zero_shot_piecewise_validation.py",
        Path(__file__).resolve(),
    ):
        lines = file_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 800, f"{file_path.name} has {len(lines)} lines (>= 800)"
        header = "\n".join(lines[:30])
        for section in ("[Role]", "[Invariants]", "[Timeouts & Locks]", "[Side-Effect Policy]"):
            assert section in header, f"{file_path.name} missing {section} in first 30 lines"


def test_probe_1_measured_duration_never_moves_prediction() -> None:
    spec = z.CellSpec("probe1", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 4, 1, 1, 1)
    pred = z.Prediction(
        cell_id="probe1",
        model_label="Qwen3.8-27B",
        layers=1,
        per_layer={"gemm": 10.0, "attention": 5.0},
        subgraphs={"attention": 5.0},
        body_ms=15.0,
        ttft_ms=50.0,
        dual_moe_ms=None,
        rows=(),
        notes=(),
        decode_body_ms=15.0,
        prefill_body_ms=50.0,
    )
    tr_a = z.KernelTrace(
        duration_us=7000.0,
        by_class={"gemm": 2000.0, "attention": 5000.0},
        by_name={"aclnnTransposeBatchMatMulWeightNz": 2000.0, "FusedInferAttentionScore": 5000.0},
        counts={"aclnnTransposeBatchMatMulWeightNz": 1, "FusedInferAttentionScore": 1},
        step_us=(7000.0,),
    )
    tr_b = z.KernelTrace(
        duration_us=13000.0,
        by_class={"gemm": 8000.0, "attention": 5000.0},
        by_name={"aclnnTransposeBatchMatMulWeightNz": 8000.0, "FusedInferAttentionScore": 5000.0},
        counts={"aclnnTransposeBatchMatMulWeightNz": 64, "FusedInferAttentionScore": 64},
        step_us=(13000.0,),
    )
    comp_a = {c.target: c.predicted_ms for c in z.compare_cell(z.MeasuredCell(spec, (), tr_a, 50.0, 15.0, 7.0, 1, True), pred) if c.level == "L1"}
    comp_b = {c.target: c.predicted_ms for c in z.compare_cell(z.MeasuredCell(spec, (), tr_b, 50.0, 15.0, 13.0, 1, True), pred) if c.level == "L1"}
    assert comp_a == {"gemm": 10.0, "attention": 5.0}
    assert comp_b == {"gemm": 10.0, "attention": 5.0}


def test_probe_2_collective_microseconds_never_clamped_in_norm_cell() -> None:
    spec = z.CellSpec("probe2", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 4, 1, 1, 1)
    tr = z.KernelTrace(
        duration_us=11000.0,
        by_class={"attention": 1000.0, "collective": 10000.0},
        by_name={"FusedInferAttentionScore": 1000.0, "hcom_allReduce_": 10000.0},
        counts={"FusedInferAttentionScore": 1, "hcom_allReduce_": 1},
        step_us=(11000.0,),
    )
    normed = z._norm_cell(z.MeasuredCell(spec, (), tr, None, None, 11.0, 1, True))
    assert normed.trace is not None
    assert normed.trace.by_class["collective"] == pytest.approx(10000.0)
    assert normed.trace.by_name["hcom_allReduce_"] == pytest.approx(10000.0)


def test_probe_3_slow_decode_step_retained_without_prefill_marker(tmp_path: Path) -> None:
    rows = (
        ("MlaPrologV3", "MlaPrologV3", 0.0, 60000.0),
        ("_categorical_sample_kernel", "_categorical_sample_kernel", 60000.0, 10.0),
        ("MlaPrologV3", "MlaPrologV3", 60010.0, 20000.0),
        ("_categorical_sample_kernel", "_categorical_sample_kernel", 80010.0, 10.0),
        ("MlaPrologV3", "MlaPrologV3", 80020.0, 20000.0),
        ("_categorical_sample_kernel", "_categorical_sample_kernel", 100020.0, 10.0),
        ("MlaPrologV3", "MlaPrologV3", 100030.0, 20000.0),
        ("_categorical_sample_kernel", "_categorical_sample_kernel", 120030.0, 10.0),
    )
    csv_path = tmp_path / "kernel_details.csv"
    _write_csv(csv_path, rows)
    spec = z.CellSpec("probe3", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, (csv_path,), None, None, None, None, 4, True))
    assert cell.trace_quality == "ok"
    assert cell.decode_steps == 4
    series = z._step_series(cell)
    assert len(series) == 4 and max(series) == pytest.approx(60.01)


def test_probe_4_multi_rank_retains_all_ranks_and_takes_slowest_step(tmp_path: Path) -> None:
    case_root = tmp_path / "case_r5"
    paths = []
    for r in range(5):
        dur = 30000.0 if r == 4 else 20000.0
        p = case_root / "dc_1k_c4" / f"rank_{r}" / "kernel_details.csv"
        _write_csv(
            p,
            (
                ("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, dur),
                ("_categorical_sample_kernel", "_categorical_sample_kernel", dur, 10.0),
                ("FusedInferAttentionScore", "FusedInferAttentionScore", dur + 10.0, dur),
                ("_categorical_sample_kernel", "_categorical_sample_kernel", 2 * dur + 10.0, 10.0),
            ),
        )
        paths.append(p)
    paired = z._pair_kernels(case_root, "dc_1k_c4", paths)
    assert len(paired) == 5
    spec = z.CellSpec("probe4", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 4, 2, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, paired, None, None, None, None, 2, True))
    assert cell.trace_quality == "ok"
    assert cell.step_trace_ms == pytest.approx(30.01)

    short_p = case_root / "dc_1k_c4" / "rank_4" / "kernel_details.csv"
    _write_csv(
        short_p,
        (
            ("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, 30000.0),
            ("_categorical_sample_kernel", "_categorical_sample_kernel", 30000.0, 10.0),
        ),
    )
    mismatch_cell = z.attach_trace(z.MeasuredCell(spec, paired, None, None, None, None, 2, True))
    assert mismatch_cell.trace_quality == "rank_step_alignment_unresolved"


def test_probe_5_ttft_perturbation_never_suppresses_l4_ttft(tmp_path: Path) -> None:
    csv_path = tmp_path / "pf.csv"
    _write_csv(csv_path, (("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, 80000.0),))
    spec = z.CellSpec("probe5", "unit", "prefill", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    pred = z.predict_cell(spec)
    for ttft_ms in (100.0, 106.0, 500.0):
        cell = z.attach_trace(z.MeasuredCell(spec, (csv_path,), None, ttft_ms, None, None, 1, True))
        assert cell.trace_quality == "ok"
        targets = {c.target for c in z.compare_cell(cell, pred)}
        assert "prefill_step_ttft" in targets


def test_probe_6_step_cancellation_is_exposed_in_aggregate_and_diagnose() -> None:
    spec = z.CellSpec("probe6", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 2, 4, 1, 1, 1)
    tr = z.KernelTrace(2000.0, {"gemm": 2000.0}, {"MatMulV3": 2000.0}, {"MatMulV3": 2}, (500.0, 1500.0))
    cell = z.MeasuredCell(spec, (), tr, None, 1.0, 1.0, 2, True)
    pred = z.Prediction("probe6", "Qwen3.8-27B", 1, {"gemm": 1.01}, {}, 1.01, None, None, (), (), 1.01, 1.01)
    comp = z._latency_comparison("L3", "decode_step_trace", 1.01, 1.0, cell, "MatMulV3", "g", "cube", "f", 0, 0.0, (0.5, 1.5))
    agg = z.aggregate([comp])[0]
    assert agg["above_10pct"] == 2
    assert agg["pass_rate_10pct"] == pytest.approx(0.0)
    assert agg["step_err_max"] == pytest.approx(1.02)
    diag = z.diagnose(comp, cell, pred)
    assert diag is not None and diag.unsigned_error == pytest.approx(1.02)


def test_probe_7_uncancelled_ms_uses_consistent_units_across_l1_l2_l3_l4() -> None:
    spec = z.CellSpec("probe7", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    tr = z.KernelTrace(
        duration_us=100000.0,
        by_class={"gemm": 25000.0, "attention": 75000.0},
        by_name={"MatMulV3": 25000.0, "FusedInferAttentionScore": 75000.0},
        counts={"MatMulV3": 100, "FusedInferAttentionScore": 100},
        step_us=(100000.0,),
    )
    cell = z.MeasuredCell(spec, (), tr, None, 100.0, 100.0, 1, True)
    pred = z.Prediction(
        cell_id="probe7",
        model_label="Qwen3.8-27B",
        layers=100,
        per_layer={"gemm": 0.75, "attention": 0.25},
        subgraphs={"attention": 0.25},
        body_ms=100.0,
        ttft_ms=None,
        dual_moe_ms=None,
        rows=(),
        notes=(),
        decode_body_ms=100.0,
        prefill_body_ms=100.0,
    )
    by_level = {(c.level, c.target): c for c in z.compare_cell(cell, pred)}
    l3 = by_level[("L3", "decode_step_trace")]
    assert l3.uncancelled_ms == pytest.approx(100.0)
    assert l3.uncancelled_ms / l3.measured_ms == pytest.approx(1.0)


def test_probe_8_union_duration_is_unbounded_and_distinct_from_forward_span(tmp_path: Path) -> None:
    csv_5k = tmp_path / "five_thousand.csv"
    rows_5k = tuple(("MatMulV3", "MatMulV3", float(2 * i), 1.0) for i in range(5000))
    _write_csv(csv_5k, rows_5k)
    tr_5k = z.load_kernel_trace(csv_5k)
    assert tr_5k.duration_us == pytest.approx(5000.0)
    assert tr_5k.union_duration_us == pytest.approx(5000.0)
    assert tr_5k.forward_span_us == pytest.approx(9999.0)
    assert tr_5k.incomplete is False

    csv_ov = tmp_path / "overlap.csv"
    _write_csv(csv_ov, (("MatMulV3", "MatMulV3", 0.0, 50.0), ("MatMulV3", "MatMulV3", 20.0, 50.0)))
    tr_ov = z.load_kernel_trace(csv_ov)
    assert tr_ov.duration_us == pytest.approx(100.0)
    assert tr_ov.union_duration_us == pytest.approx(70.0)
    assert tr_ov.forward_span_us == pytest.approx(70.0)


def test_probe_9_cache_key_isolates_structure_and_never_poisons_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    k3_case = ROOT / "examples" / "structure" / "cases" / "decode-a5_kimi_k3_p32768_c1.json"
    s_base = z.CellSpec("k3_base_c1", "a5", "decode", k3_case, "Kimi-K3", 1024, 1, 8, 8, 1, 8, 1)
    s_dspk = z.CellSpec("k3_dspark_c1", "a5", "decode", k3_case, "Kimi-K3", 1024, 1, 8, 8, 1, 8, 1)
    assert z._structure_fingerprint(s_base) != z._structure_fingerprint(s_dspk)
    assert s_base.prediction_key() != s_dspk.prediction_key()

    import mindie_sim.prediction.structure as sim_struct

    z._COMPILED_MODELS.clear()
    monkeypatch.setattr(sim_struct, "parse_case", lambda _raw: (_ for _ in ()).throw(ValueError("bad_case")))
    err_pred = z.predict_cell(s_dspk)
    assert err_pred.layers == 0 and any("case_parse_error" in n for n in err_pred.notes)
    assert not z._COMPILED_MODELS


def test_probe_10_synthetic_moe_mutates_layer_plans_schema() -> None:
    from mindie_sim.prediction.structure import parse_case

    spec = z.CellSpec("syn_l8_e16_k2_c1", "unit", "decode", MODEL_CASE, "Synthetic-MoE-L8-E16-K2", 128, 1, 4, 4, 1, 4, 1)
    case = parse_case(z._raw_case(spec))
    model, notes = z._model_for_instantiation(case.model, spec)
    assert "synthetic_layer_plans" in notes
    assert len(model.layer_plans) == 8
    assert [lp.index for lp in model.layer_plans] == list(range(8))
    assert all(lp.ffn == "moe" and lp.num_experts == 16 and lp.top_k == 2 for lp in model.layer_plans)
    assert not hasattr(model, "moe")


def test_probe_11_default_load_kernel_trace_is_read_only_unless_cache_dir_passed(tmp_path: Path) -> None:
    csv_path = tmp_path / "trace.csv"
    _write_csv(csv_path, (("MatMulV3", "MatMulV3", 0.0, 42.0),))
    tr1 = z.load_kernel_trace(csv_path)
    assert list(tmp_path.rglob("*.pkl")) == []
    cache_dir = tmp_path / "explicit_cache"
    tr2 = z.load_kernel_trace(csv_path, cache_dir=cache_dir)
    pkls = list(cache_dir.glob("*.pkl"))
    assert len(pkls) == 1
    tr3 = z.load_kernel_trace(csv_path, cache_dir=cache_dir)
    assert tr1.duration_us == tr2.duration_us == tr3.duration_us == pytest.approx(42.0)


def test_probe_12_acceptance_and_cli_exit_code_enforce_thresholds_and_coverage(tmp_path: Path) -> None:
    good_rows = [
        {
            "level": lvl,
            "target": tgt,
            "samples": 4,
            "unmatched": 0,
            "step_err_p50": 0.02,
            "step_err_max": 0.05,
            "uncancelled_p50": 0.03,
            "above_10pct": 0,
        }
        for lvl, tgt in z._REQUIRED_BENCH
    ]
    base = {"coverage": {"failed": 0}, "skipped": {}, "measurement_blind": True, "no_empirical_curve_fit": True, "levels": good_rows}
    assert z.acceptance(base, require_all_21=True)["pass"] is True
    assert z.acceptance({**base, "skipped": {"no_kernel_trace": 1}}, require_all_21=True)["pass"] is False
    assert z.acceptance({**base, "measurement_blind": False}, require_all_21=True)["pass"] is False
    assert z.acceptance({**base, "levels": good_rows[:-1]}, require_all_21=True)["pass"] is False

    bad_row = {**good_rows[0], "step_err_max": 0.11, "above_10pct": 1}
    assert z.acceptance({**base, "levels": [bad_row, *good_rows[1:]]}, require_all_21=True)["pass"] is False

    csv_path = tmp_path / "bad.csv"
    _write_csv(csv_path, (("MatMulV3", "MatMulV3", 0.0, 90000.0),))
    spec = z.CellSpec("bad_cli", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, (csv_path,), None, 100.0, 90.0, 90.0, 1, True))
    jsonl = tmp_path / "bad_bench.jsonl"
    jsonl.write_text(json.dumps(z.cell_to_dict(cell)) + "\n", encoding="utf-8")
    assert z.main(["--benchmark-jsonl", str(jsonl), "--no-historical", "--json"]) == 1


def test_probe_13_compute_dtype_propagates_unexpected_runtime_error() -> None:
    from unittest.mock import patch
    from mindie_sim.prediction.structure import parse_case

    spec = z.CellSpec("dt", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    case = parse_case(z._raw_case(spec))
    with patch.object(type(case.machine.dies[0]), "peak", side_effect=RuntimeError("broken hardware supply")):
        with pytest.raises(RuntimeError, match="broken hardware supply"):
            z._compute_dtype(case.model, case.machine)


def test_probe_14_hccl_launch_requires_interval_overlap_evidence(tmp_path: Path) -> None:
    seq_csv = tmp_path / "seq_hccl.csv"
    _write_csv(
        seq_csv,
        (
            ("HcclLaunchAicpuKernel", "HcclLaunchAicpuKernel", 0.0, 1000.0),
            ("hcom_allReduce", "hcom_allReduce", 1000.0, 100.0),
            ("MatMulV3", "MatMulV3", 1100.0, 200.0),
        ),
    )
    spec = z.CellSpec("seq_hccl", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, (seq_csv,), None, None, None, None, 1, True))
    assert cell.trace is not None
    assert cell.trace.duration_us == pytest.approx(1300.0)
    assert cell.trace.by_class["collective"] == pytest.approx(1100.0)
    assert "HcclLaunchAicpuKernel" in cell.trace.by_name


def test_probe_15_slow_decode_step_and_multi_rank_and_skew_prefill_not_excluded(tmp_path: Path) -> None:
    slow_csv = tmp_path / "slow_1100ms.csv"
    _write_csv(
        slow_csv,
        (
            ("MlaPrologV3", "MlaPrologV3", 0.0, 1100000.0),
            ("_categorical_sample_kernel", "_categorical_sample_kernel", 1100000.0, 10.0),
        ),
    )
    spec_dc = z.CellSpec("slow_dc", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    pred_dc = z.predict_cell(spec_dc)
    c_slow = z.attach_trace(z.MeasuredCell(spec_dc, (slow_csv,), None, None, 1100.01, None, 1, True))
    assert c_slow.trace_quality == "ok"
    assert c_slow.step_trace_ms == pytest.approx(1100.01)
    assert len(z.compare_cell(c_slow, pred_dc)) > 0

    r0 = tmp_path / "rank0" / "kernel_details.csv"
    r1 = tmp_path / "rank1" / "kernel_details.csv"
    _write_csv(r0, (("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, 20000.0), ("_categorical_sample_kernel", "x", 20000.0, 10.0)))
    _write_csv(
        r1,
        (
            ("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, 5000.0),
            ("hcom_allReduce", "hcom_allReduce", 5000.0, 100000.0),
            ("_categorical_sample_kernel", "x", 105000.0, 10.0),
        ),
    )
    c_mr = z.attach_trace(z.MeasuredCell(spec_dc, (r0, r1), None, None, None, None, 1, True))
    assert c_mr.step_trace_ms == pytest.approx(105.01)

    skew_csv = tmp_path / "skew_prefill.csv"
    _write_csv(
        skew_csv,
        (
            ("FusedInferAttentionScore", "FusedInferAttentionScore", 0.0, 80000.0),
            ("hcom_allGather", "hcom_allGather", 80000.0, 5000.0),
            ("hcom_allToAll", "hcom_allToAll", 85000.0, 1000.0),
        ),
    )
    spec_pf = z.CellSpec("skew_pf", "unit", "prefill", MODEL_CASE, "Qwen3.8-27B", 32768, 2, 1, 4, 1, 1, 1)
    pred_pf = z.predict_cell(spec_pf)
    c_skew = z.attach_trace(z.MeasuredCell(spec_pf, (skew_csv,), None, 500.0, None, None, 1, True))
    assert c_skew.trace_quality == "ok"
    assert "prefill_step_ttft" in {c.target for c in z.compare_cell(c_skew, pred_pf)}


def test_probe_16_l1_l2_per_step_details_expose_segment_cancellation() -> None:
    spec = z.CellSpec("seg_l12", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 2, 4, 1, 1, 1)
    tr = z.KernelTrace(
        duration_us=4000.0,
        by_class={"gemm": 2000.0, "attention": 2000.0},
        by_name={"MatMulV3": 2000.0, "FusedInferAttentionScore": 2000.0},
        counts={"MatMulV3": 2, "FusedInferAttentionScore": 2},
        step_us=(2000.0, 2000.0),
        segments=(
            (2000.0, {"gemm": 500.0, "attention": 1500.0}, {"MatMulV3": 500.0, "FusedInferAttentionScore": 1500.0}, {"MatMulV3": 1, "FusedInferAttentionScore": 1}),
            (2000.0, {"gemm": 1500.0, "attention": 500.0}, {"MatMulV3": 1500.0, "FusedInferAttentionScore": 500.0}, {"MatMulV3": 1, "FusedInferAttentionScore": 1}),
        ),
    )
    cell = z.MeasuredCell(spec, (), tr, None, 2.0, 2.0, 2, True)
    pred = z.Prediction("seg_l12", "Qwen3.8-27B", 1, {"gemm": 1.0, "attention": 1.0}, {"attention": 1.0}, 2.0, None, None, (), (), 2.0, 2.0)
    rows = {(r["level"], r["target"]): r for r in z.aggregate(z.compare_cell(cell, pred))}
    for key in (("L1", "gemm"), ("L1", "attention"), ("L2", "attention")):
        assert rows[key]["samples"] == 2
        assert rows[key]["step_err_max"] == pytest.approx(1.0)
        assert rows[key]["above_10pct"] == 2


def test_probe_17_excluded_cell_fails_coverage_and_cli(tmp_path: Path) -> None:
    spec = z.CellSpec("good", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    pred = z.predict_cell(spec)
    good_tr = z.KernelTrace(pred.body_ms * 1000.0, {k: v * 1000.0 * pred.layers for k, v in pred.per_layer.items()}, {"MatMulV3": 1000.0}, {"MatMulV3": pred.layers}, (pred.body_ms * 1000.0,))
    good_cell = z.MeasuredCell(spec, (), good_tr, pred.ttft_ms, pred.body_ms, pred.body_ms, 1, True, "", "ok")
    skew_cell = replace(good_cell, spec=replace(spec, cell_id="skew"), trace_quality="dp_barrier_skew")
    jsonl = tmp_path / "two_cells.jsonl"
    jsonl.write_text("\n".join(json.dumps(z.cell_to_dict(c)) for c in (good_cell, skew_cell)) + "\n", encoding="utf-8")
    res = z.run_validation(benchmark_jsonl=jsonl, include_historical=False)
    assert res["coverage"]["failed"] == 1
    assert res["skipped"] == {"dp_barrier_skew": 1}
    assert z.acceptance(res)["pass"] is False
    assert z.main(["--benchmark-jsonl", str(jsonl), "--no-historical", "--json"]) == 1


def test_probe_18_l3_uses_union_duration_and_roundtrips_span_fields(tmp_path: Path) -> None:
    ov_csv = tmp_path / "ov70.csv"
    _write_csv(ov_csv, (("MatMulV3", "MatMulV3", 0.0, 50000.0), ("MatMulV3", "MatMulV3", 20000.0, 50000.0)))
    spec = z.CellSpec("ov70", "unit", "decode", MODEL_CASE, "Qwen3.8-27B", 1024, 1, 1, 4, 1, 1, 1)
    cell = z.attach_trace(z.MeasuredCell(spec, (ov_csv,), None, None, None, None, 1, True))
    assert cell.trace is not None
    assert cell.trace.duration_us / 1000.0 == pytest.approx(100.0)
    assert cell.trace.union_duration_us / 1000.0 == pytest.approx(70.0)
    assert cell.trace.forward_span_us / 1000.0 == pytest.approx(70.0)
    l3 = next(c for c in z.compare_cell(cell, z.predict_cell(spec)) if c.level == "L3")
    assert l3.measured_ms == pytest.approx(70.0)
    rt = z.cell_from_dict(z.cell_to_dict(cell))
    assert rt.trace is not None and rt.trace.forward_span_us == pytest.approx(70000.0)


def test_probe_19_no_empirical_curve_fit_and_conservation_of_time(monkeypatch: pytest.MonkeyPatch) -> None:
    import inspect, math, mindie_sim.prediction.piecewise.service_span as _sp
    for fn in (z._raw_case, z._structure_fingerprint, z._model_for_instantiation, z._ep_ranks, z._service_ttft_overhead_ms, z._predict_pd, z._component_errors):
        assert "model_label" not in inspect.getsource(fn)
    assert inspect.getsource(z.predict_cell).count("model_label") <= 2
    orig_lower = _sp.lower_layer_predictions
    for phase in ("decode", "prefill"):
        spec = z.CellSpec(f"cons_{phase}", "unit", phase, MODEL_CASE, "Qwen3.8-27B", 1024, 2, 4, 2, 4, 1, 1)
        pred = z.predict_cell(spec)
        pred_relabel = z.predict_cell(replace(spec, model_label="Gemma-4-31B"))
        assert (pred.layers, pred.body_ms, pred.per_layer, pred.subgraphs) == (pred_relabel.layers, pred_relabel.body_ms, pred_relabel.per_layer, pred_relabel.subgraphs)
        monkeypatch.delattr(_sp, "lower_layer_predictions", raising=False)
        unlowered = z.predict_cell(replace(spec, cell_id=f"unlow_{phase}"))
        monkeypatch.setattr(_sp, "lower_layer_predictions", orig_lower, raising=False)
        assert abs(pred.body_ms - unlowered.body_ms) <= 1e-6
        assert abs(sum(pred.per_layer.values()) * pred.layers - sum(r.total_ms for r in pred.rows)) <= 1e-5
        assert z._no_empirical_curve_fit((pred,)) is True
        assert z._no_empirical_curve_fit((replace(pred, per_layer={k: v * 1.1 for k, v in pred.per_layer.items()}),)) is False
        assert z._no_empirical_curve_fit((replace(pred, body_ms=pred.body_ms * 1.1),)) is False
        assert z._no_empirical_curve_fit((replace(pred, layers=0),)) is False
        assert z._no_empirical_curve_fit((replace(pred, body_ms=math.nan),)) is False
    verdict = z.acceptance({"coverage": {"failed": 0}, "skipped": {}, "measurement_blind": True, "levels": [{"level": "L1", "target": "gemm", "samples": 1, "unmatched": 0, "step_err_p50": 0.01, "step_err_max": 0.01, "uncancelled_p50": 0.01, "above_10pct": 0}]})
    assert verdict["pass"] is False and "empirical_curve_fit_detected" in verdict["failures"]




