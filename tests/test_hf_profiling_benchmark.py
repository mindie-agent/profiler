"""Unit and anti-tampering tests for `hf_profiling_benchmark.py`.

[Role]
  Verify all `Codex Astra max` (`task-1240`) P0/P1 guardrails on
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


def test_collect_remaining_physical_captures_dedup_and_pf_phase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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

    rows = hfb._collect_remaining_physical_captures(
        set(),
        {"a3/heldout_case_1/kernel_details.csv"},
        {"A3": 10, "A5": 10},
    )
    assert len(rows) == 2
    assert all(r["phase"] == "prefill" for r in rows)
    cids = [r["capture_id"] for r in rows]
    assert len(set(cids)) == 2
    assert any(cid.endswith("#2") for cid in cids)


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
    fleet_row: dict[str, Any] = {
        "suite": "test_suite",
        "capture_id": "test_suite:cap1",
        "hardware_tier": "A5",
        "phase": "decode",
        "status": "compared",
        "evaluation_mode": "physical_operator_and_step_modeling",
        "forward_steps": 10,
        "observed_ms": 20.0,
        "predicted_ms": 20.5,
        "relative_error": 0.025,
        "passed_10pct": True,
        "passed_15pct": True,
        "target_timing_used_to_fit": False,
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
        "operator_modeling": {
            "status": "compared",
            "target_timing_used_to_fit": False,
            "observed_operator_ms": 20.0,
            "predicted_operator_ms": 20.5,
            "operator_relative_error": 0.025,
            "operator_passed_10pct": True,
            "families": {
                "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
            },
            "by_accelerator_core": {
                "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
            },
        },
    }
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


def test_evaluate_dataset_strict_10pct_gate_hardening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify `evaluate_dataset(..., strict_10pct=True)` rejects forged, uncompared, NaN, and non-blind inputs."""
    # 0. Valid baseline passes
    ok_dir = _setup_synthetic_dataset(tmp_path / "ok", monkeypatch)
    res = hfb.evaluate_dataset(ok_dir, strict_10pct=True)
    assert res["totals"]["unique_captures"] == 2

    # 1. Inventory-only suite (`compared == 0`) must fail strict_10pct
    uncomp_dir = _setup_synthetic_dataset(
        tmp_path / "uncomp",
        monkeypatch,
        fleet_row_overrides={"status": "measured_trace_bundle", "predicted_ms": None, "relative_error": None},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(uncomp_dir, strict_10pct=True)

    # 2. Forged `relative_error = 0.0` with `predicted_ms = 100.0, observed_ms = 20.0` must fail
    forged_dir = _setup_synthetic_dataset(
        tmp_path / "forged",
        monkeypatch,
        fleet_row_overrides={"observed_ms": 20.0, "predicted_ms": 100.0, "relative_error": 0.0},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(forged_dir, strict_10pct=True)

    # 3a. Outer `target_timing_used_to_fit = True` must fail
    leaked_dir = _setup_synthetic_dataset(
        tmp_path / "leaked",
        monkeypatch,
        fleet_row_overrides={"target_timing_used_to_fit": True},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(leaked_dir, strict_10pct=True)

    # 3b. Nested `source_calibration.target_timing_used_to_fit = True` alone must fail
    nested_fit_dir = _setup_synthetic_dataset(
        tmp_path / "nested_fit",
        monkeypatch,
        fleet_row_overrides={
            "target_timing_used_to_fit": False,
            "source_calibration": {"evaluation_relation": "zero_shot_piecewise_recomputed", "target_timing_used_to_fit": True},
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(nested_fit_dir, strict_10pct=True)

    # 3c. Nested `source_calibration.evaluation_relation = "in_sample..."` alone must fail
    nested_in_sample_dir = _setup_synthetic_dataset(
        tmp_path / "nested_in_sample",
        monkeypatch,
        fleet_row_overrides={
            "target_timing_used_to_fit": False,
            "source_calibration": {"evaluation_relation": "in_sample_regime_calibration", "target_timing_used_to_fit": False},
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(nested_in_sample_dir, strict_10pct=True)

    # 4a. Missing operator modeling (`operator_compared == 0`) must fail
    no_op_dir = _setup_synthetic_dataset(
        tmp_path / "no_op",
        monkeypatch,
        fleet_row_overrides={"operator_modeling": None},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(no_op_dir, strict_10pct=True)

    # 4b. Empty `families` or `by_accelerator_core` breakdown must fail
    empty_fam_dir = _setup_synthetic_dataset(
        tmp_path / "empty_fam",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {},
                "by_accelerator_core": {"AI_CORE": {"observed_ms": 20.0, "predicted_ms": 20.5, "relative_error": 0.025}},
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(empty_fam_dir, strict_10pct=True)

    empty_core_dir = _setup_synthetic_dataset(
        tmp_path / "empty_core",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {
                    "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
                "by_accelerator_core": {},
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(empty_core_dir, strict_10pct=True)

    # 4c. Group total reconciliation mismatch (`1%` > `1e-4`) or NaN in group `predicted_ms` must fail
    reconcile_mismatch_dir = _setup_synthetic_dataset(
        tmp_path / "reconcile_mismatch",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {
                    "cube_gemm": {"observed_ms": 11.8, "predicted_ms": 12.36, "relative_error": 12.36 / 11.8 - 1.0},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
                "by_accelerator_core": {
                    "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                    "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(reconcile_mismatch_dir, strict_10pct=True)

    nan_group_dir = _setup_synthetic_dataset(
        tmp_path / "nan_group",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {
                    "cube_gemm": {"observed_ms": 12.0, "predicted_ms": float("nan"), "relative_error": 0.03},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
                "by_accelerator_core": {
                    "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                    "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(nan_group_dir, strict_10pct=True)

    # 5a. Synthetic equal-share operator splits (identical pred/obs ratio or equal shares) must fail
    for tag, fams in (
        (
            "equal_share_nonzero",
            {
                "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 12.3, "relative_error": 0.025},
                "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.2, "relative_error": 0.025},
            },
        ),
        (
            "equal_share_zero_err",
            {
                "cube_gemm": {"observed_ms": 10.0, "predicted_ms": 10.0, "relative_error": 0.0},
                "attention_mla": {"observed_ms": 10.0, "predicted_ms": 10.0, "relative_error": 0.0},
            },
        ),
    ):
        eq_dir = _setup_synthetic_dataset(
            tmp_path / tag,
            monkeypatch,
            fleet_row_overrides={
                "operator_modeling": {
                    "status": "compared",
                    "target_timing_used_to_fit": False,
                    "observed_operator_ms": 20.0,
                    "predicted_operator_ms": sum(v["predicted_ms"] for v in fams.values()),
                    "operator_relative_error": abs(sum(v["predicted_ms"] for v in fams.values()) - 20.0) / 20.0,
                    "families": fams,
                    "by_accelerator_core": {
                        "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                        "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 8.14 if "nonzero" in tag else 7.64, "relative_error": 0.0175 if "nonzero" in tag else 0.045},
                    },
                }
            },
        )
        with pytest.raises(ValueError, match="Strict <=10% gate failed"):
            hfb.evaluate_dataset(eq_dir, strict_10pct=True)

    # 5b. Genuine opposite-signed tiny deviations (`12 -> 12.00001` and `8 -> 7.99999`) must be accepted
    opp_tiny_dir = _setup_synthetic_dataset(
        tmp_path / "opp_tiny",
        monkeypatch,
        fleet_row_overrides={
            "observed_ms": 20.0,
            "predicted_ms": 20.0,
            "relative_error": 0.0,
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.0,
                "operator_relative_error": 0.0,
                "families": {
                    "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 12.00001, "relative_error": 1e-5 / 12.0},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 7.99999, "relative_error": 1e-5 / 8.0},
                },
                "by_accelerator_core": {
                    "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.00001, "relative_error": 1e-5 / 12.0},
                    "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 7.99999, "relative_error": 1e-5 / 8.0},
                },
            },
        },
    )
    assert hfb.evaluate_dataset(opp_tiny_dir, strict_10pct=True)["totals"]["unique_captures"] == 2

    # 5c. Cancelling family or core errors (`12 -> 15 ms` [25%] and `8 -> 5.5 ms` [31.25%] cancelling to `20 -> 20.5 ms` [2.5%]) must fail
    cancel_fam_dir = _setup_synthetic_dataset(
        tmp_path / "cancel_fam",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {
                    "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 15.0, "relative_error": 0.25},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 5.5, "relative_error": 0.3125},
                },
                "by_accelerator_core": {
                    "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                    "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(cancel_fam_dir, strict_10pct=True)

    cancel_core_dir = _setup_synthetic_dataset(
        tmp_path / "cancel_core",
        monkeypatch,
        fleet_row_overrides={
            "operator_modeling": {
                "status": "compared",
                "target_timing_used_to_fit": False,
                "observed_operator_ms": 20.0,
                "predicted_operator_ms": 20.5,
                "operator_relative_error": 0.025,
                "families": {
                    "cube_gemm": {"observed_ms": 12.0, "predicted_ms": 12.36, "relative_error": 0.03},
                    "attention_mla": {"observed_ms": 8.0, "predicted_ms": 8.14, "relative_error": 0.0175},
                },
                "by_accelerator_core": {
                    "AI_CORE": {"observed_ms": 12.0, "predicted_ms": 15.0, "relative_error": 0.25},
                    "MIX_AIC": {"observed_ms": 8.0, "predicted_ms": 5.5, "relative_error": 0.3125},
                },
            }
        },
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(cancel_core_dir, strict_10pct=True)

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
                **(row0_patch if idx == 0 else {}),
            }
            for idx, (lv, tgt) in enumerate(hfb.zsv._REQUIRED_BENCH)
        ]
        bad_zs_dir = _setup_synthetic_dataset(
            tmp_path / sub_name,
            monkeypatch,
            zs_overrides={"levels": lv_list},
        )
        with pytest.raises(ValueError, match="Strict <=10% gate failed"):
            hfb.evaluate_dataset(bad_zs_dir, strict_10pct=True)

    # 7a. Suite 1 `measurement_blind = False` must fail
    nonblind_dir = _setup_synthetic_dataset(
        tmp_path / "nonblind",
        monkeypatch,
        zs_overrides={"measurement_blind": False},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(nonblind_dir, strict_10pct=True)

    # 7b. Suite 1 `no_empirical_curve_fit = False` must fail
    curvefit_dir = _setup_synthetic_dataset(
        tmp_path / "curvefit",
        monkeypatch,
        zs_overrides={"no_empirical_curve_fit": False},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(curvefit_dir, strict_10pct=True)


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
