"""Unit and anti-tampering tests for `hf_profiling_benchmark.py`.

[Role]
  Verify all `Codex Astra max` (`task-1240`) P0/P1/P2 guardrails on
  `examples/structure/hf_profiling_benchmark.py` and `scripts/hf_profiling_benchmark.py`:
  1. Unconditional structural rules in `_collect_structure_suites()` (no post-hoc
     `rel_err > 0.10` or path-substring `"mtp"` conditioning) and honest preservation
     of `source_calibration` provenance.
  2. `kernel_details.csv` fallback when `op_statistic.csv` is absent, `/pf_` phase
     detection, `Path(dp).parent` directory deduplication, and unique `capture_id`
     generation in `_collect_remaining_physical_captures()`.
  3. Hardened `evaluate_dataset(..., strict_10pct=True)` gate that recomputes
     `abs(predicted_ms - observed_ms) / observed_ms` and rejects uncompared suites,
     forged `relative_error=0.0`, `NaN` values, `target_timing_used_to_fit=True`,
     or non-blind Suite 1 validation results.
  4. Complete operator-family/unified-family maps, recomputed-error write-back into
     the unified scoreboard, and the in-tree non-timing geometry catalog fallback
     used when `/tmp` fleet captures are absent.

[Invariants]
  * Strict isolation of `MINDIE_CONFIG_HOME`, `MINDIE_DATA_HOME`,
    `MINDIE_DIAGNOSTICS_ROOT`, and `HOME` in all tests (Principle 16).
  * Tier 0/1 execution (< 5s), zero modification of repository or `/tmp` benchmark data.

[Timeouts & Locks]
  Pure in-memory and `tmp_path` execution; no locks or background processes.

[Side-Effect Policy]
  All file writes are confined to pytest `tmp_path`.
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
STRUCT_SCRIPT = ROOT / "examples" / "structure" / "hf_profiling_benchmark.py"
CLI_SCRIPT = ROOT / "scripts" / "hf_profiling_benchmark.py"

import sys
for _p in (str(ROOT), str(ROOT.parent / "sim"), str(ROOT / "examples" / "structure")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import hf_profiling_benchmark as hfb  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def test_scripts_and_examples_benchmark_are_byte_identical() -> None:
    """Ensure `examples/structure/hf_profiling_benchmark.py` and `scripts/hf_profiling_benchmark.py` match."""
    src_a = STRUCT_SCRIPT.read_bytes()
    src_b = CLI_SCRIPT.read_bytes()
    assert src_a == src_b
    assert len(src_a.splitlines()) < 800


def test_collect_structure_suites_is_unconditional_and_preserves_provenance() -> None:
    """Verify `_collect_structure_suites` has no magic thresholds/constants and preserves honest provenance."""
    src = inspect.getsource(hfb._collect_structure_suites)
    for forbidden in (
        "rel_err > 0.10",
        "rel_err > 0.1",
        '"mtp" in rel_path',
        "spec_tok >= 7",
        "ctx_tok >= 60000",
        "298.1765110924829",
        "40767.721063",
        "40324.170675",
    ):
        assert forbidden not in src, f"Forbidden literal in _collect_structure_suites: {forbidden}"

    rows, dsh_paths = hfb._collect_structure_suites()
    assert len(rows) == 280 + 26 + 575 + 1653
    assert all(not p.endswith((".csv", ".gz")) for p in dsh_paths)

    by_suite: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_suite.setdefault(r["suite"], []).append(r)
        assert "source_calibration" in r
        cal = r["source_calibration"]
        expected_fit = bool(
            cal.get("target_timing_used_to_fit", False)
            or "in_sample" in str(cal.get("evaluation_relation") or "").lower()
        )
        assert r.get("target_timing_used_to_fit") is expected_fit

    # Wave 5 raw rows must honestly report target_timing_used_to_fit=True prior to zero-shot recomputation
    assert all(r["target_timing_used_to_fit"] is True for r in by_suite["wave5_20261031"])

    # Multi-population cross-TP transfer cases in dsh_20261030_heldout must report pops[0] forward_steps (17)
    dspark_c32 = [r for r in by_suite["dsh_20261030_heldout"] if "tp8dp2_ep16_dspark7_decode_4k_c32" in r["capture_id"]]
    assert len(dspark_c32) == 1
    assert dspark_c32[0]["forward_steps"] == 17
    assert dspark_c32[0]["passed_10pct"] is True


def test_op_stat_summary_falls_back_to_kernel_details_csv(tmp_path: Path) -> None:
    """Verify `_op_stat_summary` parses `kernel_details.csv` when `op_statistic.csv` is missing."""
    cap_dir = tmp_path / "cap_no_op_stat"
    cap_dir.mkdir(parents=True)
    kd = cap_dir / "kernel_details.csv"
    kd.write_text(
        "Name,Type,Accelerator Core,Duration(us)\n"
        "MatMulV3,MatMulV3,AI_CORE,120.5\n"
        "IncreFlashAttention,IncreFlashAttention,MIX_AIC,85.0\n"
        "AllReduce,HcomAllReduce,COMMUNICATION,34.5\n",
        encoding="utf-8",
    )
    ksum, sinf = hfb._op_stat_summary(cap_dir, "deepseek-v4")
    assert ksum["total_kernel_rows"] == 3
    assert math.isclose(ksum["total_kernel_duration_us"], 240.0, rel_tol=1e-6)
    assert ksum["by_accelerator_core"]["AI_CORE"] == 120.5
    assert ksum["by_accelerator_core"]["MIX_AIC"] == 85.0
    assert ksum["by_accelerator_core"]["COMMUNICATION"] == 34.5
    assert len(ksum["top_op_types"]) == 3
    assert sinf["schema"].startswith("mindie-structural-inference/")


import math  # noqa: E402


@pytest.mark.parametrize("dsh_path", (
    "a3/heldout_case_1/kernel_details.csv",
    r"a3\heldout_case_1\kernel_details.csv",
))
def test_collect_remaining_physical_captures_dedup_and_pf_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, dsh_path: str
) -> None:
    """Verify `Path(dp).parent` deduplication, `/pf_` phase detection, and unique `capture_id`."""
    root1 = tmp_path / "root1"
    root2 = tmp_path / "root2"
    monkeypatch.setattr(hfb, "DATA_ROOTS", (root1, root2))
    monkeypatch.setattr(hfb, "_clean_text", lambda s: str(s).replace(str(root1) + "/", "").replace(str(root2) + "/", ""))

    # 1. Directory matching dsh_paths (passed with /kernel_details.csv suffix) -> must be skipped
    dsh_dup = root1 / "a3" / "heldout_case_1"
    dsh_dup.mkdir(parents=True)
    (dsh_dup / "kernel_details.csv").write_text("Name,Type,Accelerator Core,Duration(us)\nK,MatMul,AI_CORE,10.0\n", encoding="utf-8")

    # 2. Directory with `/pf_` in path -> must be detected as prefill
    pf_dir = root1 / "a5" / "model_x" / "pf_4k_c2"
    pf_dir.mkdir(parents=True)
    (pf_dir / "kernel_details.csv").write_text("Name,Type,Accelerator Core,Duration(us)\nK,MatMul,AI_CORE,20.0\n", encoding="utf-8")

    # 3. Same relative directory under root2 -> must receive distinct `#2` capture_id
    pf_dir2 = root2 / "a5" / "model_x" / "pf_4k_c2"
    pf_dir2.mkdir(parents=True)
    (pf_dir2 / "kernel_details.csv").write_text("Name,Type,Accelerator Core,Duration(us)\nK,MatMul,AI_CORE,25.0\n", encoding="utf-8")

    # A shared text prefix does not make a separate directory a duplicate.
    sibling = root1 / "a3" / "heldout_case_10" / "pf_4k_c2"
    sibling.mkdir(parents=True)
    (sibling / "kernel_details.csv").write_text("Name,Type,Accelerator Core,Duration(us)\nK,MatMul,AI_CORE,30.0\n", encoding="utf-8")

    rows = hfb._collect_remaining_physical_captures(
        set(),
        {dsh_path},
        {"A3": 10, "A5": 10},
    )
    assert len(rows) == 3
    assert all(r["phase"] == "prefill" for r in rows)
    cids = [r["capture_id"] for r in rows]
    assert len(set(cids)) == 3
    assert any("heldout_case_10/" in cid for cid in cids)
    assert any(cid.endswith("#2") for cid in cids)


def _base_fleet_row() -> dict[str, Any]:
    """Build a genuine measurement-blind row whose stored predictions match live recomputation."""
    raw: dict[str, Any] = {
        "suite": "test_suite",
        "capture_id": "test_suite:cap1",
        "hardware_tier": "A5",
        "phase": "decode",
        "forward_steps": 10,
        "target_timing_used_to_fit": False,
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
        "geometry": {
            "tp": 8, "dp": 1, "ep": 1, "context_tokens": 4096, "concurrency": 4,
            "active_hbm_mb": 12345.0,
        },
    }
    predicted = hfb.predict_capture_operators_and_step(raw)
    observed = round(float(predicted["predicted_step_ms"]) * 1.02, 4)
    total_us = observed * 1000.0 * raw["forward_steps"]
    raw["observed_ms"] = observed
    raw["kernel_summary"] = {
        "total_kernel_duration_us": total_us,
        "by_accelerator_core": {"AI_CORE": total_us * 0.60, "AI_VECTOR_CORE": total_us * 0.15, "MIX_AIC": total_us * 0.25},
        "top_op_types": [
            {"type": "MatMulV2", "core": "AI_CORE", "count": 1, "total_us": total_us * 0.60},
            {"type": "IncreFlashAttention", "core": "MIX_AIC", "count": 1, "total_us": total_us * 0.25},
            {"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": total_us * 0.15},
        ],
    }
    observed_block = hfb.fleet_modeling.extract_capture_observations(raw)
    weights = observed_block["structural_weights"]
    raw["geometry"]["structural_weights"] = [w * f for w, f in zip(weights, (1.005, 0.995, 1.01, 0.99, 1.0, 1.0))]
    return hfb.enrich_fleet_capture_with_operator_and_step_modeling(raw)


def _setup_synthetic_dataset(
    base_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    fleet_row_overrides: dict[str, Any] | None = None,
    zs_overrides: dict[str, Any] | None = None,
) -> Path:
    data_dir = base_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    zs_row = {"cell_id": "c1", "hardware_tier": "A5", "phase": "decode"}
    fleet_row = _base_fleet_row()
    if fleet_row_overrides:
        fleet_row.update(fleet_row_overrides)
    hfb._write_jsonl_gz(data_dir / "zero_shot_l1_l4_cells.jsonl.gz", [zs_row], also_plain=True)
    hfb._write_jsonl_gz(data_dir / "fleet_captures.jsonl.gz", [fleet_row], also_plain=True)

    default_levels = [
        {
            "level": lv,
            "target": tgt,
            "samples": 10,
            "cells": 1,
            "unmatched": 0,
            "step_err_p50": 0.03,
            "step_err_p90": 0.05,
            "step_err_max": 0.06,
            "uncancelled_p50": 0.03,
            "above_10pct": 0,
            "pass_rate_10pct": 1.0,
        }
        for lv, tgt in hfb.zsv._REQUIRED_BENCH
    ]
    zs_res: dict[str, Any] = {
        "coverage": {"cells": 1, "evaluated": 1, "failed": 0, "step_samples": 10},
        "levels": default_levels,
        "measurement_blind": True,
        "no_empirical_curve_fit": True,
        "forbidden_lookup_imported": False,
        "skipped": {},
    }
    if zs_overrides:
        zs_res.update(zs_overrides)
    monkeypatch.setattr(hfb.zsv, "run_validation", lambda **_kw: zs_res)
    return base_dir


def _entry(observed: float, predicted: float) -> dict[str, float]:
    """Build a self-consistent observed/predicted/relative-error group entry."""
    return {
        "observed_ms": observed,
        "predicted_ms": predicted,
        "relative_error": abs(predicted - observed) / max(observed, 1e-9),
    }


def _op_model(
    families: dict[str, dict[str, float]] | None = None,
    cores: dict[str, dict[str, float]] | None = None,
    *,
    observed: float = 20.0,
    predicted: float = 20.5,
    unified: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    """Build an operator model with default family/core groups and a consistent total error."""
    fams = {"cube_gemm": _entry(12.0, 12.36), "attention_mla": _entry(8.0, 8.14)} if families is None else families
    crs = {"AI_CORE": _entry(12.0, 12.36), "MIX_AIC": _entry(8.0, 8.14)} if cores is None else cores
    err = abs(predicted - observed) / max(observed, 1e-9)
    model: dict[str, Any] = {
        "status": "compared",
        "target_timing_used_to_fit": False,
        "observed_operator_ms": observed,
        "predicted_operator_ms": predicted,
        "operator_relative_error": err,
        "operator_passed_10pct": err <= 0.10,
        "families": fams,
        "by_accelerator_core": crs,
    }
    if unified is not None:
        model["unified_families"] = unified
    return model


def _strict_gate_rejects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tag: str,
    fleet_row_overrides: dict[str, Any] | None = None,
    zs_overrides: dict[str, Any] | None = None,
) -> None:
    """Assert that a synthetic dataset variant fails the strict <=10% gate."""
    dataset = _setup_synthetic_dataset(
        tmp_path / tag,
        monkeypatch,
        fleet_row_overrides=fleet_row_overrides,
        zs_overrides=zs_overrides,
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(dataset, strict_10pct=True)


def test_evaluate_dataset_strict_10pct_gate_hardening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify `evaluate_dataset(..., strict_10pct=True)` rejects forged, uncompared, NaN, and non-blind inputs."""
    # 0. Valid baseline passes
    ok_dir = _setup_synthetic_dataset(tmp_path / "ok", monkeypatch)
    res = hfb.evaluate_dataset(ok_dir, strict_10pct=True)
    assert res["totals"]["unique_captures"] == 2

    # 1. Inventory-only suite (`compared == 0`) must fail strict_10pct.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "uncomp",
        {"status": "measured_trace_bundle", "predicted_ms": None, "relative_error": None},
    )

    # 2. Forged `relative_error = 0.0` with `predicted_ms = 100.0, observed_ms = 20.0` must fail.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "forged",
        {"observed_ms": 20.0, "predicted_ms": 100.0, "relative_error": 0.0},
    )

    # 3a. Outer `target_timing_used_to_fit = True` must fail.
    _strict_gate_rejects(tmp_path, monkeypatch, "leaked", {"target_timing_used_to_fit": True})

    # 3b. Nested `source_calibration.target_timing_used_to_fit = True` alone must fail.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "nested_fit",
        {"target_timing_used_to_fit": False,
         "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed", "target_timing_used_to_fit": True}},
    )

    # 3c. Nested `source_calibration.evaluation_relation = "in_sample..."` alone must fail.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "nested_in_sample",
        {"target_timing_used_to_fit": False,
         "source_calibration": {"evaluation_relation": "in_sample_regime_calibration", "target_timing_used_to_fit": False}},
    )

    # 4a. Missing operator modeling (`operator_compared == 0`) must fail.
    _strict_gate_rejects(tmp_path, monkeypatch, "no_op", {"operator_modeling": None})

    # 4b. Empty `families` or `by_accelerator_core` breakdown must fail.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "empty_fam",
        {"operator_modeling": _op_model({}, {"AI_CORE": _entry(20.0, 20.5)})},
    )
    _strict_gate_rejects(
        tmp_path, monkeypatch, "empty_core",
        {"operator_modeling": _op_model(cores={})},
    )

    # 4c. Group total reconciliation mismatch (`1%` > `1e-4`) or NaN in group `predicted_ms` must fail.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "reconcile_mismatch",
        {"operator_modeling": _op_model({"cube_gemm": _entry(11.8, 12.36), "attention_mla": _entry(8.0, 8.14)})},
    )
    _strict_gate_rejects(
        tmp_path, monkeypatch, "nan_group",
        {"operator_modeling": _op_model({
            "cube_gemm": {"observed_ms": 12.0, "predicted_ms": float("nan"), "relative_error": 0.03},
            "attention_mla": _entry(8.0, 8.14),
        })},
    )

    # 5a. Synthetic equal-share operator splits (identical pred/obs ratio or equal shares) must fail.
    for tag, fams in (
        ("equal_share_nonzero", {"cube_gemm": _entry(12.0, 12.3), "attention_mla": _entry(8.0, 8.2)}),
        ("equal_share_zero_err", {"cube_gemm": _entry(10.0, 10.0), "attention_mla": _entry(10.0, 10.0)}),
    ):
        cores = {"AI_CORE": _entry(12.0, 12.36), "MIX_AIC": _entry(8.0, 8.14 if "nonzero" in tag else 7.64)}
        _strict_gate_rejects(
            tmp_path, monkeypatch, tag,
            {"operator_modeling": _op_model(fams, cores, predicted=sum(v["predicted_ms"] for v in fams.values()))},
        )

    # 5b. Genuine opposite-signed tiny deviations inside the live 1e-3 tolerance must be accepted.
    valid_base = _base_fleet_row()
    live = hfb.predict_capture_operators_and_step({k: v for k, v in valid_base.items() if k != "predicted_ms"})
    step_ms = float(live["predicted_step_ms"])
    families = {k: {"observed_ms": v, "predicted_ms": v, "relative_error": 0.0} for k, v in live["predicted_by_family_ms"].items()}
    cores = {k: {"observed_ms": v, "predicted_ms": v, "relative_error": 0.0} for k, v in live["predicted_by_core_ms"].items()}
    for group in (families, cores):
        keys = [k for k, entry in group.items() if entry["predicted_ms"] > 1e-6]
        group[keys[0]]["predicted_ms"] += 1e-5
        group[keys[1]]["predicted_ms"] -= 1e-5
        for key in keys[:2]:
            entry = group[key]
            entry["relative_error"] = abs(entry["predicted_ms"] - entry["observed_ms"]) / max(entry["observed_ms"], 1e-9)
    opp_tiny_dir = _setup_synthetic_dataset(
        tmp_path / "opp_tiny", monkeypatch,
        fleet_row_overrides={
            "observed_ms": step_ms, "predicted_ms": step_ms, "relative_error": 0.0,
            "operator_modeling": _op_model(
                families, cores,
                observed=sum(v["observed_ms"] for v in families.values()),
                predicted=sum(v["predicted_ms"] for v in families.values()),
            ),
        },
    )
    assert hfb.evaluate_dataset(opp_tiny_dir, strict_10pct=True)["totals"]["unique_captures"] == 2

    # 5c. Cancelling family or core errors (`12 -> 15 ms` [25%] and `8 -> 5.5 ms` [31.25%] cancelling to `20 -> 20.5 ms` [2.5%]) must fail.
    cancelled = {"cube_gemm": _entry(12.0, 15.0), "attention_mla": _entry(8.0, 5.5)}
    _strict_gate_rejects(tmp_path, monkeypatch, "cancel_fam", {"operator_modeling": _op_model(cancelled)})
    _strict_gate_rejects(tmp_path, monkeypatch, "cancel_core", {"operator_modeling": _op_model(cores=cancelled)})

    # 5d. A step error above 10% must fail even when the stored prediction matches live.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "step_over",
        {"observed_ms": round(step_ms * 1.20, 4), "predicted_ms": step_ms, "relative_error": 0.20},
    )

    # 5e. Mutating structural_weights changes the live operator split and must fail operator verification.
    tampered_geom = {**(valid_base.get("geometry") or {}), "structural_weights": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]}
    _strict_gate_rejects(tmp_path, monkeypatch, "weights", {"geometry": tampered_geom})

    # 5f. A suite outside every historical whitelist still gets unconditional live step/operator verification.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "unlisted",
        {"suite": "unlisted_suite_2027", "predicted_ms": 999999.0},
    )

    # 6. 21-row Suite 1 checks: decoupled L1 `step_err_max > 0.10`, `above_10pct > 0`, `samples == 0`, `unmatched > 0`, duplicate target, and unknown target
    for sub_name, row0_patch in (
        ("bad_l1_step_max", {"step_err_max": 0.25}),
        ("bad_l1_above_10pct", {"above_10pct": 1}),
        ("bad_l1_samples", {"samples": 0}),
        ("bad_l1_unmatched", {"unmatched": 1}),
        ("bad_l1_dup_target", {"level": hfb.zsv._REQUIRED_BENCH[1][0], "target": hfb.zsv._REQUIRED_BENCH[1][1]}),
        ("bad_l1_unknown_target", {"target": "unknown_target_xyz"}),
    ):
        lv_list = [
            {
                "level": lv, "target": tgt, "samples": 10, "cells": 1, "unmatched": 0,
                "step_err_p50": 0.03, "step_err_p90": 0.05, "step_err_max": 0.06,
                "uncancelled_p50": 0.03, "above_10pct": 0, "pass_rate_10pct": 1.0,
                **(row0_patch if idx == 0 else {}),
            }
            for idx, (lv, tgt) in enumerate(hfb.zsv._REQUIRED_BENCH)
        ]
        _strict_gate_rejects(tmp_path, monkeypatch, sub_name, zs_overrides={"levels": lv_list})

    # 7a/b. Suite 1 `measurement_blind = False` or `no_empirical_curve_fit = False` must fail.
    _strict_gate_rejects(tmp_path, monkeypatch, "nonblind", zs_overrides={"measurement_blind": False})
    _strict_gate_rejects(tmp_path, monkeypatch, "curvefit", zs_overrides={"no_empirical_curve_fit": False})


def test_zero_shot_incomplete_trace_is_rejected(tmp_path: Path) -> None:
    """Verify `attach_trace` and `compare_cell` reject corrupt traces even when valid rows or sibling ranks exist."""
    valid_csv = tmp_path / "rank0_kernel_details.csv"
    valid_csv.write_text("Name,Type,Duration(us)\nMatMulV3,MatMulV3,120.0\n", encoding="utf-8")
    corrupt_csv = tmp_path / "rank1_kernel_details.csv"
    corrupt_csv.write_text(
        "Name,Type,Duration(us)\nMatMulV3,MatMulV3,120.0\nBadKernel,MatMulV3,not_a_float\n",
        encoding="utf-8",
    )
    spec = hfb.zsv.CellSpec(
        "corrupt_cell", "unit", "decode", None, "deepseek-v4.1-flash", 1024, 1, 1, 1, 1, 1, 1
    )
    # 1. Single corrupt trace with non-empty by_class/step_us and incomplete=True
    cell1 = hfb.zsv.MeasuredCell(spec, (corrupt_csv,), None, None, None, None, 1, True)
    att1 = hfb.zsv.attach_trace(cell1)
    assert att1.trace is not None and att1.trace.incomplete is True and bool(att1.trace.by_class)
    assert att1.success is False
    assert att1.trace_quality == "corrupt_incomplete_trace"
    pred = hfb.zsv.Prediction("corrupt_cell", "deepseek-v4.1-flash", 40, {"gemm": 0.12}, {"attention": 0.12}, 4.8, None, None, (), ())
    assert hfb.zsv.compare_cell(att1, pred) == []

    # 2. Multi-rank cell where rank 0 is valid and rank 1 is corrupt -> must reject rather than silently dropping rank 1
    cell2 = hfb.zsv.MeasuredCell(spec, (valid_csv, corrupt_csv), None, None, None, None, 1, True)
    att2 = hfb.zsv.attach_trace(cell2)
    assert att2.success is False
    assert att2.trace_quality == "corrupt_incomplete_trace"

    # 3. Already-attached incomplete trace passed to attach_trace -> must reject
    pre_attached = hfb.zsv.MeasuredCell(spec, (valid_csv,), att1.trace, None, 10.0, 10.0, 1, True)
    att3 = hfb.zsv.attach_trace(pre_attached)
    assert att3.success is False
    assert att3.trace_quality == "corrupt_incomplete_trace"
    assert hfb.zsv.compare_cell(pre_attached, pred) == []


def test_bogus_predicted_ms_is_ignored_and_tampered_rows_fail(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Live step prediction ignores bogus `predicted_ms`, and `evaluate_dataset` rejects a tampered row."""
    import fleet_operator_modeling as fom

    cfg = {
        "capture_id": "model_mtp3_tp8_decode", "suite": "unit", "hardware_tier": "A5", "phase": "decode",
        "forward_steps": 8, "target_timing_used_to_fit": False,
        "geometry": {"dp": 1, "ep": 1, "context_tokens": 4096, "concurrency": 4, "active_hbm_mb": 12345.0},
    }
    baseline = fom.predict_capture_operators_and_step(cfg)
    bogus = fom.predict_capture_operators_and_step({**cfg, "predicted_ms": 999999.0, "target_timing_used_to_fit": False})
    assert bogus["predicted_step_ms"] == baseline["predicted_step_ms"] != 999999.0
    assert fom._infer_geometry({"capture_id": "model_mtp3_tp8_decode", "phase": "decode", "geometry": {}})["tp"] == 8
    ks = {"total_kernel_duration_us": 8000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 8000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 8000.0}]}
    row = {**cfg, "observed_ms": float(baseline["predicted_step_ms"]), "kernel_summary": ks}
    assert fom.enrich_fleet_capture_with_operator_and_step_modeling({**row, "predicted_ms": 999999.0})["predicted_ms"] == baseline["predicted_step_ms"]
    decode_doc = json.loads((ROOT / "examples" / "structure" / "results" / "decode.json").read_text(encoding="utf-8"))
    case = decode_doc["cases"][0]
    case_id = str(case.get("case_id") or case.get("id"))
    tmp_results = tmp_path / "results"
    tmp_results.mkdir()
    (tmp_results / "decode.json").write_text(json.dumps(decode_doc), encoding="utf-8")
    monkeypatch.setattr(fom, "RESULTS_DIR", tmp_results)
    live_cfg = {"capture_id": f"registered_decode:{case_id}", "suite": "registered_decode", "hardware_tier": "A3", "phase": "decode", "forward_steps": 32, "target_timing_used_to_fit": False, "geometry": dict(case.get("geometry") or {})}
    before = fom.predict_capture_operators_and_step(live_cfg)
    mutated = json.loads(json.dumps(decode_doc))
    mutated["cases"][0].setdefault("comparison", {})["predicted_ms"] = 999999.0
    (tmp_results / "decode.json").write_text(json.dumps(mutated), encoding="utf-8")
    fom.clear_caches()
    assert fom.predict_capture_operators_and_step({**live_cfg, "predicted_ms": 999999.0, "target_timing_used_to_fit": False}) == before
    tampered = _setup_synthetic_dataset(
        tmp_path / "tampered", monkeypatch,
        fleet_row_overrides={"geometry": {"active_hbm_mb": 1.0, "tp": 8, "dp": 1, "ep": 1, "context_tokens": 4096, "concurrency": 1}, "predicted_ms": 20.5, "observed_ms": 20.0, "relative_error": 0.025},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(tampered, strict_10pct=True)


def test_live_operator_matches_requires_complete_families_and_recomputed_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2: a partial family map, drifted family total, or stale relative_error must never verify."""
    base = _base_fleet_row()
    live = hfb.predict_capture_operators_and_step({k: v for k, v in base.items() if k != "predicted_ms"})
    assert hfb._live_operator_matches(live, base["operator_modeling"]) is True
    assert set(base["operator_modeling"]["families"]) == set(live["predicted_by_family_ms"])

    # 1. Dropping even one benchmark family must fail even though every remaining entry still matches.
    partial = copy.deepcopy(base["operator_modeling"])
    dropped = next(k for k, v in partial["families"].items() if float(v["predicted_ms"]) > 1e-6)
    partial["families"].pop(dropped)
    assert hfb._live_operator_matches(live, partial) is False
    partial_dir = _setup_synthetic_dataset(
        tmp_path / "partial_families", monkeypatch, fleet_row_overrides={"operator_modeling": partial}
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(partial_dir, strict_10pct=True)

    # 2. Every entry within per-entry tolerance but a family sum drifted past abs_tol must fail.
    drifted = copy.deepcopy(base["operator_modeling"])
    for entry in drifted["families"].values():
        pred = float(entry["predicted_ms"])
        entry["predicted_ms"] = round(pred + 0.9 * max(1e-3 * abs(pred), 1e-3), 12)
        entry["relative_error"] = abs(entry["predicted_ms"] - entry["observed_ms"]) / max(entry["observed_ms"], 1e-9)
    assert hfb._live_operator_matches(live, drifted) is False

    # 3. Stale stored relative_error=0.0 in a family or core entry must fail.
    stale_family = copy.deepcopy(base["operator_modeling"])
    fam_key = next(k for k, v in stale_family["families"].items() if float(v["predicted_ms"]) > 1e-6)
    stale_family["families"][fam_key]["relative_error"] = 0.0
    assert hfb._live_operator_matches(live, stale_family) is False
    stale_core = copy.deepcopy(base["operator_modeling"])
    stale_core["by_accelerator_core"][next(iter(stale_core["by_accelerator_core"]))]["relative_error"] = 0.0
    assert hfb._live_operator_matches(live, stale_core) is False


def test_unified_families_live_validation_and_strict_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2: unified-family predictions, keys, errors, and observed magnitudes are validated."""
    base = _base_fleet_row()
    live = hfb.predict_capture_operators_and_step({k: v for k, v in base.items() if k != "predicted_ms"})
    assert hfb._live_operator_matches(live, base["operator_modeling"]) is True
    assert set(base["operator_modeling"]["unified_families"]) == set(live["predicted_by_unified_family_ms"])

    # 1. A tampered unified `predicted_ms` (with a self-consistent relative_error) must fail.
    tampered = copy.deepcopy(base["operator_modeling"])
    key = next(k for k, v in tampered["unified_families"].items() if float(v["predicted_ms"]) > 1e-6)
    entry = tampered["unified_families"][key]
    entry["predicted_ms"] = round(float(entry["predicted_ms"]) * 1.5, 12)
    entry["relative_error"] = abs(entry["predicted_ms"] - entry["observed_ms"]) / max(entry["observed_ms"], 1e-9)
    assert hfb._live_operator_matches(live, tampered) is False
    tampered_dir = _setup_synthetic_dataset(
        tmp_path / "tampered_unified", monkeypatch, fleet_row_overrides={"operator_modeling": tampered}
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(tampered_dir, strict_10pct=True)

    # 2. A missing unified family or a stale unified `relative_error=0.0` must fail.
    incomplete = copy.deepcopy(base["operator_modeling"])
    incomplete["unified_families"].pop(key)
    assert hfb._live_operator_matches(live, incomplete) is False
    stale = copy.deepcopy(base["operator_modeling"])
    stale["unified_families"][key]["relative_error"] = 0.0
    assert hfb._live_operator_matches(live, stale) is False

    # 3. A valid live prediction with one >10% perturbed unified `observed_ms` must fail strict gating
    #    and flip `operator_passed_10pct`, even though every unified `predicted_ms` still matches live.
    perturbed = copy.deepcopy(base["operator_modeling"])
    entry = perturbed["unified_families"][key]
    entry["observed_ms"] = round(float(entry["predicted_ms"]) / 1.5, 12)
    entry["relative_error"] = abs(float(entry["predicted_ms"]) - entry["observed_ms"]) / max(entry["observed_ms"], 1e-9)
    assert entry["relative_error"] == pytest.approx(0.5)
    assert float(live["predicted_by_unified_family_ms"][key]) == pytest.approx(float(entry["predicted_ms"]), rel=1e-9)
    assert hfb._live_operator_matches(live, perturbed) is True

    captured: dict[str, Any] = {}
    real_read = hfb._read_jsonl_any

    def _read_spy(path: Path) -> list[dict[str, Any]]:
        rows = real_read(path)
        if Path(path).name == "fleet_captures.jsonl.gz":
            captured["fleet"] = rows
        return rows

    monkeypatch.setattr(hfb, "_read_jsonl_any", _read_spy)
    dataset = _setup_synthetic_dataset(
        tmp_path / "perturbed_unified_observed", monkeypatch, fleet_row_overrides={"operator_modeling": perturbed}
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(dataset, strict_10pct=True)
    op_mod = captured["fleet"][0]["operator_modeling"]
    assert op_mod["operator_passed_10pct"] is False
    assert op_mod["operator_relative_error"] > 0.10


def test_evaluate_dataset_writeback_overrides_stale_zero_errors_in_scoreboard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2: recomputed step/operator errors must be written back so the scoreboard cannot stay green."""
    base = _base_fleet_row()
    step_ms = float(base["predicted_ms"])
    stale_op = copy.deepcopy(base["operator_modeling"])
    stale_op["operator_relative_error"] = 0.0
    stale_op["operator_passed_10pct"] = True
    captured: dict[str, Any] = {}
    real_build = hfb._build_unified_7337_scoreboard

    def _spy(zs_rows: Any, zs_result: Any, fleet_rows: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
        captured["rows"] = list(fleet_rows)
        return real_build(zs_rows, zs_result, fleet_rows, *args, **kwargs)

    monkeypatch.setattr(hfb, "_build_unified_7337_scoreboard", _spy)
    dataset = _setup_synthetic_dataset(
        tmp_path / "stale_errors",
        monkeypatch,
        fleet_row_overrides={
            "observed_ms": round(step_ms * 2.0, 4),
            "predicted_ms": step_ms,
            "relative_error": 0.0,
            "passed_10pct": True,
            "passed_15pct": True,
            "operator_modeling": stale_op,
        },
    )
    result = hfb.evaluate_dataset(dataset)

    row = captured["rows"][0]
    assert row["relative_error"] == pytest.approx(0.5, abs=1e-6)
    assert row["passed_10pct"] is False and row["passed_15pct"] is False
    op = row["operator_modeling"]
    assert op["operator_relative_error"] > 0.0
    assert op["operator_passed_10pct"] is (op["operator_relative_error"] <= 0.10)
    board = result["unified_7337_scoreboard"]
    step_row = next(r for r in board["rows"] if r["target"] == "decode_step_tpot")
    assert step_row["above_10pct"] >= 1
    assert step_row["err_max"] == pytest.approx(0.5, abs=1e-6)


def test_collect_structure_suites_and_predict_fall_back_to_geometry_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2: rebuilding and prediction must use the in-tree non-timing geometry catalog when /tmp is absent."""
    fom = hfb.fleet_modeling
    absent = tmp_path / "absent_fleet_captures.jsonl"
    monkeypatch.setattr(hfb, "_FLEET_TEMPLATE_PATH", absent)
    rows, dsh_paths = hfb._collect_structure_suites()
    assert len(rows) == 280 + 26 + 575 + 1653
    assert all(not p.endswith((".csv", ".gz")) for p in dsh_paths)

    catalog = fom._load_geometry_catalog()
    assert len(catalog) == 6606
    assert all(set(entry) <= set(hfb._GEOM_TEMPLATE_KEYS) for entry in catalog.values())
    for row in rows:
        entry = catalog[row["capture_id"]]
        assert row["geometry"].get("structural_weights") is not None
        demand = "active_cube_gflops" if row["phase"] == "prefill" else "active_hbm_mb"
        assert row["geometry"].get(demand) is not None
        assert all(row["geometry"].get(key) == value for key, value in entry.items())

    # Prediction must also fall back to the catalog when the results dir contains no catalog copy.
    monkeypatch.setattr(fom, "_FLEET_TEMPLATE_PATH", absent)
    monkeypatch.setattr(fom, "RESULTS_DIR", tmp_path / "empty_results")
    probe = next(r for r in rows if r["phase"] == "decode")
    full = fom.predict_capture_operators_and_step({**probe, "geometry": dict(probe["geometry"])})
    stripped_geometry = {k: v for k, v in probe["geometry"].items() if k not in hfb._GEOM_TEMPLATE_KEYS}
    fallback = fom.predict_capture_operators_and_step({**probe, "geometry": stripped_geometry})
    assert fallback["geometry"]["active_hbm_mb"] == catalog[probe["capture_id"]]["active_hbm_mb"]
    assert fallback["predicted_step_ms"] == full["predicted_step_ms"]
