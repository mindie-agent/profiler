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
     the unified scoreboard, per-cell `step_errors` extraction, L3 trace key matching
     (`L3:decode_step_trace` / `L3:prefill_step_trace`), honest structural inference
     counts, and direct local session metadata attachment without pre-computed demands.

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
import math
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
STRUCT_SCRIPT = ROOT / "examples" / "structure" / "hf_profiling_benchmark.py"
CLI_SCRIPT = ROOT / "scripts" / "hf_profiling_benchmark.py"

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
    assert b"\r\n" not in src_a


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
    assert sinf["exact_architecture_pass"] is True
    assert sinf["exact_tp_pass"] is False and sinf["exact_dp_pass"] is False and sinf["exact_ep_pass"] is False
    assert sinf["all_4_pass"] is False


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
    for r in rows:
        geom = r["geometry"]
        assert geom["prompt_tokens"] == 4096
        assert geom["concurrency"] == 2
        assert geom["tokens_per_sequence"] >= 1
        assert geom["sequences_per_replica"] >= 1
        assert geom["query_rows"] >= 1


def _base_fleet_row() -> dict[str, Any]:
    """Build a genuine measurement-blind row whose stored predictions match live recomputation."""
    raw: dict[str, Any] = {
        "suite": "test_suite",
        "capture_id": "test_suite:v41_decode_c4",
        "hardware_tier": "A5",
        "model_case": "cases/decode-a5_v41_fp8_tp1_dp8_ep8_c4_p2k.json",
        "phase": "decode",
        "forward_steps": 10,
        "target_timing_used_to_fit": False,
        "source_calibration": {
            "evaluation_relation": "zero_shot_piecewise_recomputed",
            "target_timing_used_to_fit": False,
        },
        "geometry": {
            "tp": 8, "dp": 1, "ep": 8, "pp": 1, "ep_dspark_wave_scale": 0.15,
            "context_tokens": 4096, "prompt_tokens": 4096, "concurrency": 4,
            "tokens_per_sequence": 1, "sequences_per_replica": 4, "query_rows": 4,
            "body_chunks": 1, "num_layers": 61, "num_experts": 256, "top_k": 8,
        },
    }
    predicted = hfb.predict_capture_operators_and_step(raw)
    step = predicted.get("predicted_step_ms")
    families = predicted.get("predicted_by_unified_family_ms") or {}
    if not isinstance(step, (int, float)) or not families:
        # The live predictor withheld a step. Stored numbers below are poison and must not pass.
        raw["observed_ms"] = 20.0
        raw["predicted_ms"] = None
        raw["relative_error"] = 0.0
        raw["passed_10pct"] = True
        raw["operator_modeling"] = _op_model(unified={
            "matmul_gemm": _entry(12.0, 12.36),
            "attention": _entry(8.0, 8.14),
        })
        raw["structural_inference"] = hfb._infer_from_top_ops([], raw["model_case"], raw["geometry"])
        return raw
    observed = round(float(step) * 1.02, 4)
    scale = 1000.0 * raw["forward_steps"] * 1.02
    unif = predicted["predicted_by_unified_family_ms"]
    w_gemm = float(unif["matmul_gemm"]) * scale * 1.004
    w_na = float(unif["norm_activation_elementwise"]) * scale * 0.996
    w_kv = float(unif["kv_cache_position_rope"]) * scale * 1.008
    w_attn = float(unif["attention"]) * scale * 0.994
    w_moe = float(unif["moe_routing_grouped_gemm"]) * scale * 1.002
    w_coll = float(unif["collective_comm"]) * scale * 0.998
    by_core = {
        "AI_CORE": round(w_gemm, 2),
        "AI_VECTOR_CORE": round(w_na + w_kv, 2),
        "MIX_AIC": round(w_attn + 0.55 * w_moe, 2),
        "COMMUNICATION": round(w_coll + 0.45 * w_moe, 2),
    }
    top_ops = [
        {"type": "Gemm", "core": "AI_CORE", "count": 10, "total_us": round(w_gemm, 2)},
        {"type": "IncreFlashAttention", "core": "MIX_AIC", "count": 10, "total_us": round(w_attn, 2)},
        {"type": "GroupedMatmul", "core": "MIX_AIC", "count": 10, "total_us": round(w_moe, 2)},
        {"type": "RmsNorm", "core": "AI_VECTOR_CORE", "count": 10, "total_us": round(w_na, 2)},
        {"type": "RotaryPositionEmbedding", "core": "AI_VECTOR_CORE", "count": 10, "total_us": round(w_kv, 2)},
    ]
    raw["observed_ms"] = observed
    raw["kernel_summary"] = {
        "total_kernel_rows": 50,
        "total_kernel_duration_us": round(sum(by_core.values()), 2),
        "by_accelerator_core": by_core,
        "top_op_types": top_ops,
    }
    raw["structural_inference"] = hfb._infer_from_top_ops(top_ops, raw["model_case"], raw["geometry"])
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
    zs_row = {
        "cell_id": "c1", "hardware_tier": "A5", "phase": "decode",
        "model_label": "DeepSeek-V4.1-Flash", "tp": 8, "dp": 1, "ep": 8,
        "trace": {"by_class": {"gemm": [100.0]}, "step_us": [1000.0]},
    }
    fleet_row = _base_fleet_row()
    if fleet_row_overrides:
        fleet_row.update(fleet_row_overrides)
    hfb._write_jsonl_gz(data_dir / "zero_shot_l1_l4_cells.jsonl.gz", [zs_row], also_plain=True)
    hfb._write_jsonl_gz(data_dir / "fleet_captures.jsonl.gz", [fleet_row], also_plain=True)

    default_levels = [
        {
            "level": lv,
            "target": tgt,
            "samples": 1,
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
    default_step_errors = [
        {"cell": "c1", "level": lv, "target": tgt, "step": 0, "signed_error": 0.03}
        for lv, tgt in hfb.zsv._REQUIRED_BENCH
    ]
    zs_res: dict[str, Any] = {
        "coverage": {"cells": 1, "evaluated": 1, "failed": 0, "step_samples": 10},
        "levels": default_levels,
        "step_errors": default_step_errors,
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
    """Verify `evaluate_dataset(..., strict_10pct=True)` rejects a subset that is not the original 7,337."""
    # A two-row table is not the original population, so strict mode fails closed.
    ok_dir = _setup_synthetic_dataset(tmp_path / "ok", monkeypatch)
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(ok_dir, strict_10pct=True)
    targeted = hfb.evaluate_dataset(ok_dir, strict_10pct=True, inventory="targeted")
    assert targeted["strict_global_pass"] is False
    assert targeted["totals"]["unique_captures"] == 2
    assert targeted["totals"]["operator_modeling"]["pass_10pct_captures"] == 0
    full = hfb.evaluate_dataset(ok_dir, inventory="full")
    assert full["inventory"] == "full"

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

    # 5b. A two-row table is not the original population. A withheld live step is not a pass either.
    valid_base = _base_fleet_row()
    live = hfb.predict_capture_operators_and_step({k: v for k, v in valid_base.items() if k != "predicted_ms"})
    live_step = live.get("predicted_step_ms")
    live_families = live.get("predicted_by_family_ms") or {}
    live_cores = live.get("predicted_by_core_ms") or {}
    if isinstance(live_step, (int, float)) and live_families and live_cores:
        step_ms = float(live_step)
        families = {k: {"observed_ms": v, "predicted_ms": v, "relative_error": 0.0} for k, v in live_families.items()}
        cores = {k: {"observed_ms": v, "predicted_ms": v, "relative_error": 0.0} for k, v in live_cores.items()}
        for group in (families, cores):
            keys = [k for k, entry in group.items() if entry["predicted_ms"] > 1e-6]
            group[keys[0]]["predicted_ms"] += 1e-5
            group[keys[1]]["predicted_ms"] -= 1e-5
            for key in keys[:2]:
                entry = group[key]
                entry["relative_error"] = abs(entry["predicted_ms"] - entry["observed_ms"]) / max(entry["observed_ms"], 1e-9)
        opp_overrides = {
            "observed_ms": step_ms, "predicted_ms": step_ms, "relative_error": 0.0,
            "operator_modeling": _op_model(
                families, cores,
                observed=sum(v["observed_ms"] for v in families.values()),
                predicted=sum(v["predicted_ms"] for v in families.values()),
            ),
        }
    else:
        step_ms = 20.0
        opp_overrides = None
    opp_tiny_dir = _setup_synthetic_dataset(tmp_path / "opp_tiny", monkeypatch, fleet_row_overrides=opp_overrides)
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(opp_tiny_dir, strict_10pct=True)
    assert hfb.evaluate_dataset(opp_tiny_dir, inventory="targeted")["strict_global_pass"] is False

    # 5c. Cancelling family or core errors (`12 -> 15 ms` [25%] and `8 -> 5.5 ms` [31.25%] cancelling to `20 -> 20.5 ms` [2.5%]) must fail.
    cancelled = {"cube_gemm": _entry(12.0, 15.0), "attention_mla": _entry(8.0, 5.5)}
    _strict_gate_rejects(tmp_path, monkeypatch, "cancel_fam", {"operator_modeling": _op_model(cancelled)})
    _strict_gate_rejects(tmp_path, monkeypatch, "cancel_core", {"operator_modeling": _op_model(cores=cancelled)})

    # 5d. A step error above 10% must fail even when the stored prediction matches live.
    _strict_gate_rejects(
        tmp_path, monkeypatch, "step_over",
        {"observed_ms": round(step_ms * 1.20, 4), "predicted_ms": step_ms, "relative_error": 0.20},
    )

    # 5e. Mutating architectural geometry changes the live operator/step split and must fail verification.
    tampered_geom = {**(valid_base.get("geometry") or {}), "tp": 1, "ep": 1, "concurrency": 32, "context_tokens": 131072}
    _strict_gate_rejects(tmp_path, monkeypatch, "geom_tamper", {"geometry": tampered_geom})

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
        "geometry": {"dp": 1, "ep": 1, "context_tokens": 4096, "concurrency": 4},
    }
    baseline = fom.predict_capture_operators_and_step(cfg)
    bogus = fom.predict_capture_operators_and_step({**cfg, "predicted_ms": 999999.0, "target_timing_used_to_fit": False})
    assert bogus["predicted_step_ms"] == baseline["predicted_step_ms"]
    assert baseline["predicted_step_ms"] != 999999.0
    trusted = fom._infer_geometry({"phase": "decode", "geometry": {"tp": 8, "dp": 1}})
    assert trusted.get("tp") == 8
    assert "tp" not in fom._infer_geometry({"capture_id": "model_mtp3_tp8_decode", "phase": "decode", "geometry": {}})
    step = baseline.get("predicted_step_ms")
    ks = {"total_kernel_duration_us": 8000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 8000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 8000.0}]}
    if isinstance(step, (int, float)) and math.isfinite(float(step)):
        row = {**cfg, "observed_ms": float(step), "kernel_summary": ks}
        assert fom.enrich_fleet_capture_with_operator_and_step_modeling({**row, "predicted_ms": 999999.0})["predicted_ms"] == step
    else:
        assert step is None
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
        fleet_row_overrides={"geometry": {"tp": 1, "dp": 1, "ep": 1, "context_tokens": 131072, "concurrency": 32}, "predicted_ms": 20.5, "observed_ms": 20.0, "relative_error": 0.025},
    )
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(tampered, strict_10pct=True)


def test_live_operator_matches_requires_complete_families_and_recomputed_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P2: a partial family map, drifted family total, or stale relative_error must never verify."""
    base = _base_fleet_row()
    live = hfb.predict_capture_operators_and_step({k: v for k, v in base.items() if k != "predicted_ms"})
    live_ready = isinstance(live.get("predicted_step_ms"), (int, float)) and bool(live.get("predicted_by_family_ms"))
    if live_ready:
        assert hfb._live_operator_matches(live, base["operator_modeling"]) is True
        assert set(base["operator_modeling"]["families"]) == set(live["predicted_by_family_ms"])
    else:
        assert hfb._live_operator_matches(live, base["operator_modeling"]) is False

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
    live_ready = isinstance(live.get("predicted_step_ms"), (int, float)) and bool(live.get("predicted_by_unified_family_ms"))
    if live_ready:
        assert hfb._live_operator_matches(live, base["operator_modeling"]) is True
        assert set(base["operator_modeling"]["unified_families"]) == set(live["predicted_by_unified_family_ms"])
    else:
        assert hfb._live_operator_matches(live, base["operator_modeling"]) is False

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
    if live_ready:
        assert float(live["predicted_by_unified_family_ms"][key]) == pytest.approx(float(entry["predicted_ms"]), rel=1e-9)
        assert hfb._live_operator_matches(live, perturbed) is True
    else:
        assert hfb._live_operator_matches(live, perturbed) is False

    dataset = _setup_synthetic_dataset(
        tmp_path / "perturbed_unified_observed", monkeypatch, fleet_row_overrides={"operator_modeling": perturbed}
    )
    before = (dataset / "data" / "fleet_captures.jsonl").read_bytes()
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(dataset, strict_10pct=True)
    assert (dataset / "data" / "fleet_captures.jsonl").read_bytes() == before
    targeted = hfb.evaluate_dataset(dataset, inventory="targeted")
    assert targeted["strict_global_pass"] is False
    assert targeted["totals"]["operator_modeling"]["pass_10pct_captures"] == 0


def test_evaluate_dataset_does_not_turn_stored_errors_into_a_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stored observed/predicted fields stay on disk and cannot open a request-boundary pass."""
    base = _base_fleet_row()
    step = base.get("predicted_ms")
    step_ms = float(step) if isinstance(step, (int, float)) and math.isfinite(float(step)) else 20.0
    stale_op = copy.deepcopy(base["operator_modeling"])
    stale_op["operator_relative_error"] = 0.0
    stale_op["operator_passed_10pct"] = True
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
    before = (dataset / "data" / "fleet_captures.jsonl").read_bytes()
    result = hfb.evaluate_dataset(dataset, inventory="targeted")
    assert (dataset / "data" / "fleet_captures.jsonl").read_bytes() == before
    assert result["strict_global_pass"] is False
    assert result["totals"]["step_modeling"]["pass_10pct_captures"] == 0
    board = result["unified_7337_scoreboard"]
    step_row = next(r for r in board["rows"] if r["target"] == "decode_step_tpot")
    assert step_row["evaluated_captures"] == 0


def test_local_session_metadata_and_honest_scoreboard_without_template_catalog() -> None:
    """Verify removed template catalog symbols, local session geometry, L3 trace keys, and structural inference stats."""
    src_text = STRUCT_SCRIPT.read_text(encoding="utf-8")
    for removed in (
        "_GEOM_TEMPLATE_KEYS",
        "_DEFAULT_FLEET_TEMPLATE_PATH",
        "_FLEET_TEMPLATE_PATH",
        "_active_fleet_template_path",
        "_load_fleet_geometry_catalog",
        "_merge_fleet_template_geometry",
        "L3:decode_body",
        "L3:prefill_body",
    ):
        assert not hasattr(hfb, removed)
        assert removed not in src_text

    assert not (hfb.RESULTS_DIR / "fleet_geometry_demands.json.gz").exists()
    assert not (hfb.RESULTS_DIR / "zero_shot_trace_cache.json.gz").exists()

    rows, _ = hfb._collect_structure_suites()
    evidenced_keys = {
        "tokens_per_sequence", "query_rows", "context_tokens", "prompt_tokens",
        "body_chunks", "tp", "dp", "ep", "num_layers",
    }
    for row in rows:
        geom = row["geometry"]
        assert evidenced_keys.issubset(geom.keys()), row["capture_id"]
        assert "predicted_ms" not in row
        sinf = row["structural_inference"]
        assert isinstance(sinf, dict)
        parallel_ok = all(hfb._positive_int(geom.get(key)) is not None for key in ("tp", "dp", "ep"))
        # These four suites pass no operator events, so architecture stays unverified.
        assert sinf.get("exact_architecture_pass") is False
        assert sinf.get("all_4_pass") is (bool(sinf.get("exact_architecture_pass")) and parallel_ok)
        provenance = geom["demand_provenance"]
        for key in ("structural_weights", "active_hbm_mb", "active_cube_gflops"):
            assert provenance[key] == "absent"
            assert key not in geom
    dense = next(r for r in rows if r["capture_id"] == "registered_decode:qwen36-a5-tp2-c12")
    assert "num_experts" not in dense["geometry"] and "top_k" not in dense["geometry"]
    assert any(r["suite"] == "wave5_20261031" and "pp" not in r["geometry"] for r in rows)

    # Scoreboard must extract actual per-cell step_errors, use L3:*_step_trace, and report 0 when structural_inference is empty
    zs_rows = [{"cell_id": "dc1", "phase": "decode"}, {"cell_id": "pf1", "phase": "prefill"}]
    zs_result = {
        "coverage": {"cells": 2, "evaluated": 2, "failed": 0, "step_samples": 4},
        "levels": [],
        "step_errors": [
            {"cell": "dc1", "level": "L1", "target": "gemm", "step": 0, "signed_error": -0.015},
            {"cell": "dc1", "level": "L1", "target": "gemm", "step": 1, "signed_error": 0.042},
            {"cell": "pf1", "level": "L1", "target": "gemm", "step": 0, "signed_error": 0.081},
            {"cell": "dc1", "level": "L3", "target": "decode_step_trace", "step": 0, "signed_error": 0.037},
            {"cell": "pf1", "level": "L3", "target": "prefill_step_trace", "step": 0, "signed_error": -0.064},
        ],
    }
    board_empty_sinf = hfb._build_unified_7337_scoreboard(
        zs_rows, zs_result, [{"suite": "s", "capture_id": "c", "phase": "decode"}],
        {}, 10, {"A5": 3}, {"decode": 2, "prefill": 1},
    )
    gemm_row = next(r for r in board_empty_sinf["rows"] if r["target"] == "matmul_gemm")
    assert gemm_row["evaluated_captures"] == 2
    assert gemm_row["err_max"] == pytest.approx(0.081)
    assert gemm_row["err_p50"] == pytest.approx(0.0615)

    dec_trace = next(r for r in board_empty_sinf["rows"] if r["target"] == "decode_step_trace")
    pf_trace = next(r for r in board_empty_sinf["rows"] if r["target"] == "prefill_step_trace")
    dec_row = next(r for r in board_empty_sinf["rows"] if r["target"] == "decode_step_tpot")
    pf_row = next(r for r in board_empty_sinf["rows"] if r["target"] == "prefill_step_ttft")
    e2e = next(r for r in board_empty_sinf["rows"] if r["target"] == "all_7337_captures_step_e2e")
    ai_core = next(r for r in board_empty_sinf["rows"] if r["target"] == "AI_CORE")
    assert dec_trace["evaluated_captures"] == 1 and dec_trace["err_max"] == pytest.approx(0.037)
    assert pf_trace["evaluated_captures"] == 1 and pf_trace["err_max"] == pytest.approx(0.064)
    assert dec_row["evaluated_captures"] == 0 and pf_row["evaluated_captures"] == 0
    assert e2e["evaluated_captures"] == 0 and ai_core["evaluated_captures"] == 0
    assert board_empty_sinf["l3_step_trace_err_p50"] == pytest.approx(0.0505)

    sinf_empty = board_empty_sinf["structural_inference"]
    for key in ("evaluated_captures", "exact_architecture_pass", "exact_tp_pass", "exact_dp_pass", "exact_ep_pass", "all_4_pass"):
        assert sinf_empty[key] == 0
    assert sinf_empty["pass_rate_10pct"] == 0.0


def test_nan_second_sample_is_fatal() -> None:
    errs = hfb._zs_cell_errors(
        {"step_errors": [
            {"cell": "c", "level": "L1", "target": "gemm", "signed_error": 0.001},
            {"cell": "c", "level": "L1", "target": "gemm", "signed_error": float("nan")},
        ]},
        {},
    )
    assert math.isnan(errs["L1:gemm"][0])


def test_geometry_echo_and_model_label_are_not_all_four_pass() -> None:
    sinf = hfb._infer_from_top_ops(
        [{"type": "NotARealOp", "core": "AI_CORE", "count": 1, "total_us": 1.0}],
        "label-only",
        {"tp": 128, "dp": 17, "ep": 91},
    )
    assert sinf["exact_architecture_pass"] is True
    assert sinf["exact_tp_pass"] is False and sinf["exact_dp_pass"] is False and sinf["exact_ep_pass"] is False
    assert sinf["all_4_pass"] is False
    assert sinf["inferred_tp"] is None
    stats = hfb._structural_inference_stats(
        [{
            "model_label": "only", "tp": 128, "dp": 17, "ep": 91,
            "trace": {"by_class": {"gemm": [1.0]}, "step_us": [1.0]},
            "structural_inference": {"all_4_pass": True, "exact_architecture_pass": True, "exact_tp_pass": True, "exact_dp_pass": True, "exact_ep_pass": True},
        }],
        [], 1, 1, {"A5": 1},
    )
    assert stats["evaluated_captures"] == 0
    assert stats["all_4_pass"] == 0


def test_op_statistic_preserves_op_by_engine(tmp_path: Path) -> None:
    cap = tmp_path / "cap"
    cap.mkdir()
    (cap / "op_statistic.csv").write_text(
        "OP Type,Core Type,Count,Total Time(us)\nMatMulV3,AI_CORE,2,100.0\nMatMulV3,MIX_AIC,1,40.0\n",
        encoding="utf-8",
    )
    ksum, sinf = hfb._op_stat_summary(cap, "deepseek")
    assert ksum["by_op_engine"]["MatMulV3"]["AI_CORE"]["total_us"] == pytest.approx(100.0)
    assert ksum["by_op_engine"]["MatMulV3"]["MIX_AIC"]["total_us"] == pytest.approx(40.0)
    assert ksum["by_accelerator_core"]["AI_CORE"] == pytest.approx(100.0)
    assert ksum["by_accelerator_core"]["MIX_AIC"] == pytest.approx(40.0)
    assert ksum["total_kernel_duration_us"] == pytest.approx(140.0)
    assert sinf["all_4_pass"] is False


def test_calibration_counts_and_source_sha_come_from_the_case_record() -> None:
    assert hfb._calibration_role("observed_service_regimes", "not_blind") == "observed_service_regimes"
    assert hfb._calibration_role("retrospective_context_transfer; not_blind", "compared") == "not_blind"
    assert hfb._calibration_role("in_sample", "heldout") == "in_sample"
    rows, _paths = hfb._collect_structure_suites()
    decode = [row for row in rows if row["suite"] == "registered_decode"]
    prefill = [row for row in rows if row["suite"] == "registered_prefill"]
    assert sum(row["source_calibration"]["evaluation_relation"] == "in_sample" for row in decode) == 68
    assert sum(row["source_calibration"]["evaluation_relation"] == "retrospective_context_transfer; not_blind" for row in decode) == 77
    assert sum(row["source_calibration"]["evaluation_relation"] == "in_sample" for row in prefill) == 1
    assert all(row["calibration_role"] == "regime_table_replay" for row in rows if row["suite"] == "wave5_20261031")
    cases = json.loads((hfb.RESULTS_DIR / "decode.json").read_text(encoding="utf-8"))["cases"]
    by_id = {str(case.get("case_id") or case.get("id")): case for case in cases}
    differ = [
        cid for cid, case in by_id.items()
        if str((case.get("source") or {}).get("sha256") or "")
        and str((case.get("source") or {}).get("sha256")) != str(case.get("input_sha256") or "")
    ]
    assert differ
    row = next(item for item in decode if item["capture_id"] == f"registered_decode:{differ[0]}")
    assert row["source_sha256"] == str(by_id[differ[0]]["source"]["sha256"])
    assert row["generator_input_sha256"] == str(by_id[differ[0]].get("input_sha256") or "")


def test_plain_and_gzip_disagreement_fails(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    (data / "zero_shot_l1_l4_cells.jsonl").write_text('{"cell_id":"a"}\n', encoding="utf-8")
    (data / "fleet_captures.jsonl").write_text('{"capture_id":"f"}\n', encoding="utf-8")
    (data / "fleet_captures.jsonl.gz").write_bytes(hfb.gzip.compress(b'{"capture_id":"f"}\n'))
    (data / "zero_shot_l1_l4_cells.jsonl.gz").write_bytes(hfb.gzip.compress(b'{"cell_id":"OTHER"}\n'))
    with pytest.raises(ValueError, match="disagree"):
        hfb.evaluate_dataset(tmp_path, inventory="targeted")


def test_full_population_false_is_not_a_strict_opt_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = _setup_synthetic_dataset(tmp_path / "tiny", monkeypatch)
    with pytest.raises(ValueError, match="Strict <=10% gate failed"):
        hfb.evaluate_dataset(dataset, strict_10pct=True, full_population=False)


def test_multinode_keeps_zero_export_and_phase_aligned_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    case = tmp_path / "runs" / "caseA"
    (case / "cellA").mkdir(parents=True)
    (case / "cellB").mkdir()
    (case / "cellA" / "export_summary.json").write_text(
        json.dumps({"total_kernel_duration_us": 0, "total_kernel_rows": 0, "top_op_types": []}), encoding="utf-8"
    )
    (case / "cellB" / "export_summary.json").write_text(
        json.dumps({"total_kernel_duration_us": 50000, "total_kernel_rows": 3, "top_op_types": []}), encoding="utf-8"
    )
    (case / "cellA.json").write_text(json.dumps({"mode": "decode", "tpot_ms": {"median": 12.5}}), encoding="utf-8")
    monkeypatch.setattr(hfb, "MULTINODE_20261108_ROOT", tmp_path)
    rows = hfb._collect_multinode_20261108()
    zero = next(row for row in rows if row["capture_id"].endswith("caseA:cellA"))
    assert zero["observed_ms"] == pytest.approx(12.5)
    assert zero["kernel_summary"]["total_kernel_duration_us"] == 0.0


def test_score_boundary_does_not_reuse_model_step_as_client_tpot() -> None:
    import hf_benchmark_gate as gate

    stolen = gate.score_boundary(
        {"status": "predicted", "prediction_boundary": "native_client_request", "predicted_step_ms": 10.0},
        {"capture": {"phase": "decode"}, "measurements": {"native_client_request": {"status": "measured", "reported_tpot_ms": 10.0}}},
    )
    assert stolen["comparison"] == "uncovered"
    matched = gate.score_boundary(
        {"status": "predicted", "prediction_boundary": "native_client_request", "boundary_ms": 10.0},
        {"capture": {"phase": "decode"}, "measurements": {"native_client_request": {"status": "measured", "reported_tpot_ms": 11.0}}},
    )
    assert matched["comparison"] == "compared" and matched["passed_10pct"] is True
    fatal = gate.score_boundary(
        {"status": "predicted", "prediction_boundary": "native_client_request", "boundary_ms": float("nan")},
        {"capture": {"phase": "decode"}, "measurements": {"native_client_request": {"status": "measured", "reported_tpot_ms": 11.0}}},
    )
    assert fatal["comparison"] == "invalid" and fatal["passed_10pct"] is False
    failed = gate.score_boundary(
        {"status": "failed", "prediction_boundary": "per_forward_window", "boundary_ms": -4.0},
        {"measurements": {"per_forward_window": {"status": "measured", "observed_ms": -4.0, "forward_spans_ms": [-4.0]}}},
    )
    assert failed["passed_10pct"] is False
    withheld = gate.score_boundary(
        {"status": "insufficient_evidence", "prediction_boundary": "per_forward_window", "boundary_ms": 5.0},
        {"measurements": {"per_forward_window": {"status": "measured", "observed_ms": 5.0, "forward_spans_ms": [5.0]}}},
    )
    assert withheld["passed_10pct"] is False
    hidden = gate.score_boundary(
        {"status": "predicted", "prediction_boundary": "per_forward_window", "boundary_ms": 5.0},
        {"measurements": {"per_forward_window": {"status": "measured", "observed_ms": 5.0, "forward_spans_ms": [5.0, 99999.0]}}},
    )
    assert hidden["passed_10pct"] is False and hidden["comparison"] == "invalid"
    negative = gate.score_boundary(
        {"status": "predicted", "prediction_boundary": "per_forward_window", "boundary_samples_ms": [-4.0]},
        {"measurements": {"per_forward_window": {"status": "measured", "forward_spans_ms": [-4.0]}}},
    )
    assert negative["passed_10pct"] is False and negative["comparison"] == "invalid"
    groups = {"measurements": {"operator_groups": {
        "MatMulV3 / AI_CORE": {"status": "measured", "observed_ms": 1.0},
        "QFFN / MIX_AIC": {"status": "measured", "observed_ms": 3.0},
    }}}
    both = gate.score_operator_groups(
        {"status": "predicted", "operator_group_samples": [
            {"key": "MatMulV3 / AI_CORE", "boundary_ms": 1.0},
            {"key": "QFFN / MIX_AIC", "boundary_ms": 3.0},
        ]},
        groups,
    )
    assert both["passed_10pct"] is True and both["n_groups"] == 2
    omitted = gate.score_operator_groups(
        {"status": "predicted", "operator_group_samples": [{"key": "MatMulV3 / AI_CORE", "boundary_ms": 1.0}]},
        groups,
    )
    assert omitted["passed_10pct"] is False
    duplicated = gate.score_operator_groups(
        {"status": "predicted", "operator_group_samples": [{"key": "MatMulV3 / AI_CORE", "boundary_ms": 1.0}] * 2},
        groups,
    )
    assert duplicated["passed_10pct"] is False


def _analytical_request_and_groups() -> tuple[dict[str, Any], dict[str, Any]]:
    """Two request keys and two op×engine keys. Values are declared, not fitted."""
    observation = {
        "capture": {"capture_id": "unit:analytical", "phase": "decode", "hardware_tier": "A5"},
        "measurements": {
            "native_client_request": {
                "status": "measured",
                "samples": [
                    {"request_id": "r1", "tpot_ms": 1.0},
                    {"request_id": "r2", "tpot_ms": 99.0},
                ],
            },
            "operator_groups": {
                "MatMulV3\x1fAI_CORE": {"status": "measured", "observed_ms": 10.0},
                "GroupedMatmul\x1fMIX_AIC": {"status": "measured", "observed_ms": 4.0},
            },
        },
    }
    prediction = {
        "status": "predicted",
        "prediction_boundary": "native_client_request",
        "capture_id": "unit:analytical",
        "phase": "decode",
        "hardware_tier": "A5",
        "boundary_samples": {"request_id=r1": 1.0, "request_id=r2": 99.0},
        "operator_group_samples": [
            {"key": "MatMulV3\x1fAI_CORE", "boundary_ms": 10.0},
            {"key": "GroupedMatmul\x1fMIX_AIC", "boundary_ms": 4.0},
        ],
    }
    return observation, prediction


def _analytical_operator_model() -> tuple[dict[str, Any], dict[str, Any]]:
    live = {
        "predicted_by_family_ms": {"cube_gemm": 12.0, "attention_mla": 8.0},
        "predicted_by_core_ms": {"AI_CORE": 12.0, "MIX_AIC": 8.0},
        "predicted_operator_ms": 20.0,
        "predicted_by_unified_family_ms": {"matmul_gemm": 12.0, "attention": 8.0},
    }
    model = _op_model(
        {"cube_gemm": _entry(12.0, 12.0), "attention_mla": _entry(8.0, 8.0)},
        {"AI_CORE": _entry(12.0, 12.0), "MIX_AIC": _entry(8.0, 8.0)},
        observed=20.0,
        predicted=20.0,
        unified={"matmul_gemm": _entry(12.0, 12.0), "attention": _entry(8.0, 8.0)},
    )
    return live, model


def test_analytical_pair_passes_then_one_poison_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A declared pair passes. One poisoned field fails that target only.

    A two-row table is rejected by the full-population gate. That rejection
    is not evidence that a stored error, a missing family, or a median was checked.
    """
    import hf_benchmark_gate as gate

    observation, prediction = _analytical_request_and_groups()
    step = gate.score_boundary(prediction, observation)
    groups = gate.score_operator_groups(prediction, observation)
    assert step["comparison"] == "compared" and step["passed_10pct"] is True and step["n_samples"] == 2
    assert groups["passed_10pct"] is True and groups["n_groups"] == 2
    swapped = {**prediction, "boundary_samples": {"request_id=r2": 99.0, "request_id=r1": 1.0}}
    assert gate.score_boundary(swapped, observation)["passed_10pct"] is True
    stolen = gate.score_boundary({**prediction, "predicted_ms": 999999.0}, observation)
    assert stolen["passed_10pct"] is True and stolen["sample"] == step["sample"]

    median = {key: value for key, value in prediction.items() if key != "boundary_samples"}
    median["boundary_ms"] = 50.0
    hidden = gate.score_boundary(median, observation)
    assert hidden["passed_10pct"] is False and hidden["comparison"] == "invalid"
    assert gate.score_operator_groups(median, observation)["passed_10pct"] is True

    one_request = {**prediction, "boundary_samples": {"request_id=r1": 1.0, "request_id=r2": 50.0}}
    drifted = gate.score_boundary(one_request, observation)
    assert drifted["passed_10pct"] is False
    assert gate.score_operator_groups(one_request, observation)["passed_10pct"] is True

    dropped = {**prediction, "operator_group_samples": prediction["operator_group_samples"][:1]}
    assert gate.score_operator_groups(dropped, observation)["passed_10pct"] is False
    assert gate.score_boundary(dropped, observation)["passed_10pct"] is True

    row = {
        "capture_id": "unit:analytical", "suite": "unit", "phase": "decode", "hardware_tier": "A5",
        "observed_ms": 1.0, "predicted_ms": 1.0, "relative_error": 0.0, "passed_10pct": True,
    }
    fresh = gate.score_fleet_row(row, observation, prediction)
    assert fresh["passed_10pct"] is True and fresh["operator_passed_10pct"] is True
    stale = gate.score_fleet_row(row, observation, one_request)
    assert stale["passed_10pct"] is False

    live, model = _analytical_operator_model()
    assert hfb._live_operator_matches(live, model) is True
    partial = copy.deepcopy(model)
    partial["families"].pop("cube_gemm")
    assert hfb._live_operator_matches(live, partial) is False
    tampered = copy.deepcopy(model)
    tampered["unified_families"]["matmul_gemm"] = _entry(12.0, 18.0)
    assert hfb._live_operator_matches(live, tampered) is False
    stale_error = copy.deepcopy(model)
    stale_error["families"]["cube_gemm"]["relative_error"] = 0.5
    assert hfb._live_operator_matches(live, stale_error) is False

    unknown = {
        "measurements": {"operator_groups": {
            "MatMulV3\x1fUNKNOWN": {"status": "measured", "observed_ms": 1.0, "engine": "UNKNOWN"},
        }},
    }
    unknown_pred = {
        "status": "predicted", "prediction_boundary": "native_client_request", "boundary_ms": 1.0,
        "operator_group_samples": [{"key": "MatMulV3\x1fUNKNOWN", "boundary_ms": 1.0}],
    }
    withheld_core = gate.score_fleet_row(
        {"capture_id": "unit:unknown-core", "phase": "decode", "hardware_tier": "A5"},
        unknown, unknown_pred,
    )
    assert withheld_core["operator_passed_10pct"] is False
    assert withheld_core["operator_reason"] == "unknown_core_not_a_pass"

    class _Layer:
        layer_id, forward_id, start_ns, end_ns = 0, "f0", 10, 20

    class _Trace:
        status, phase = "measured", "decode"
        hardware = {"hardware_key": "A5"}
        source_sha256 = "abc"
        layer_windows = (_Layer(),)
        operators = ()

    joined = gate._evidence_from_timetables([_Trace()])
    assert gate._zs_gaps({"hardware_tier": "A5", "native_windows": []}, joined) == []
    assert gate._zs_gaps({"hardware_tier": "A5"}) == ["not_joined"]

    dataset = _setup_synthetic_dataset(tmp_path / "label", monkeypatch)
    observation, prediction = _analytical_request_and_groups()

    def _builder():
        return [{
            "capture_id": "test_suite:v41_decode_c4",
            "suite": "registered_decode",
            "phase": "decode",
            "hardware_tier": "A5",
            "source_sha256": "abc",
            "source_calibration": {"evaluation_relation": "in_sample", "target_timing_used_to_fit": False},
        }]

    labeled = gate.evaluate(
        dataset, strict_10pct=False, inventory="targeted", summary_dir=tmp_path / "sum",
        identity_builder=_builder, simulator_name="unit",
        predict=lambda _cfg: prediction, observe=lambda _cfg: observation, run_validation=lambda **_kw: {},
    )
    disclosed = json.loads((tmp_path / "sum" / "per_id.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert disclosed["evaluation_relation"] == "in_sample"
    assert disclosed["coverage_only"] is True
    assert disclosed["passed_10pct"] is True
    assert labeled["strict_global_pass"] is False

    dataset = _setup_synthetic_dataset(tmp_path / "not_7337", monkeypatch)
    with pytest.raises(ValueError, match="population identity"):
        hfb.evaluate_dataset(dataset, strict_10pct=True, full_population=False)
    targeted = hfb.evaluate_dataset(dataset, inventory="targeted")
    assert targeted["strict_global_pass"] is False
    assert targeted["totals"]["unique_captures"] == 2


def test_dataset_card_prints_pass_evaluated_and_unverified() -> None:
    text = hfb._render_dataset_card({
        "totals": {
            "unique_captures": 10,
            "zero_shot_l1_l4_cells": 1,
            "fleet_captures": 9,
            "operator_modeling": {"pass_10pct_captures": 0, "evaluated_captures": 4, "unverified_captures": 6},
            "step_modeling": {"pass_10pct_captures": 0, "evaluated_captures": 4, "unverified_captures": 6},
        },
        "strict_global_pass": False,
        "inventory": "targeted",
        "identity": {},
        "no_data": {},
    })
    assert "pass `0`" in text
    assert "evaluated `4`" in text
    assert "unverified `6`" in text


def test_upload_does_not_post(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="upload refused"):
        hfb.upload_dataset(tmp_path, allow_network=True)


def test_standalone_calls_stay_out_of_the_body_step(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A native call is not a body step. A failing group keeps its paired-key count.

    An in_sample forward miss stays in the coverage stratum. It is not a blind miss.
    Two rank SHAs and an Ascend950DT preflight are not a digest or hardware conflict.
    """
    import hf_benchmark_gate as gate

    observation = {
        "capture": {"capture_id": "cal:fia", "phase": "decode", "hardware_tier": "A5"},
        "source": {},
        "measurements": {
            "native_calls": {
                "status": "measured",
                "native_phase": "prefill",
                "source_sha256": "ab",
                "samples_basis": "elapsed_native_call_span_ms",
                "samples": [
                    {"key": "fia:call0", "observed_ms": 1.0, "phase": "prefill"},
                    {"key": "fia:call1", "observed_ms": 1.0, "phase": "prefill"},
                ],
            },
            "operator_groups": {
                "FIA\x1fUNKNOWN": {"status": "measured", "observed_ms": 1.0, "engine": "UNKNOWN"},
            },
        },
    }
    prediction = {
        "status": "predicted",
        "prediction_boundary": "native_calls",
        "boundary_basis": "elapsed_native_call_span_ms",
        "capture_id": "cal:fia",
        "phase": "prefill",
        "hardware_tier": "A5",
        "source_sha256": "ab",
        "source_role": "standalone_native_primitive",
        "boundary_samples": [
            {"key": "fia:call0", "boundary_ms": 1.0, "phase": "prefill"},
            {"key": "fia:call1", "boundary_ms": 1.2, "phase": "prefill"},
        ],
        "operator_group_samples": [{"key": "FIA\x1fUNKNOWN", "boundary_ms": 1.0}],
    }
    row = {"capture_id": "cal:fia", "suite": "operator_and_kernel_calibration_20261107",
           "phase": "decode", "hardware_tier": "A5"}
    scored = gate.score_fleet_row(row, observation, prediction)
    assert scored["comparison"] == "not_a_body_step"
    assert scored["passed_10pct"] is False
    assert scored["boundary_scope"] == "standalone"
    assert scored["standalone_comparison"] == "compared"
    assert scored["group_passed_10pct"] is False
    assert scored["key_denominator"] == 2
    assert scored["key_matched"] == 2
    assert scored["standalone_max_error"] == pytest.approx(0.2)
    assert scored["operator_comparison"] == "unavailable"
    assert scored["native_phase"] == "prefill"
    assert scored["enrolled_phase"] == "decode"

    mismatched = dict(prediction)
    mismatched["source_sha256"] = "cd"
    rejected = gate.score_fleet_row(row, observation, mismatched)
    assert rejected["standalone_comparison"] == "invalid"
    assert rejected["passed_10pct"] is False

    missing_digest = dict(prediction)
    missing_digest["source_sha256"] = ""
    missing_digest["boundary_samples"] = [
        {"key": "fia:call0", "boundary_ms": 1.0, "phase": "prefill"},
        {"key": "fia:call1", "boundary_ms": 1.0, "phase": "prefill"},
    ]
    withheld = gate.score_fleet_row(row, observation, missing_digest)
    assert withheld["standalone_comparison"] == "uncovered"
    assert withheld["standalone_reason"] == "native_calls_source_sha256_absent"
    assert withheld["standalone_passed_10pct"] is False
    assert withheld["key_matched"] == 2

    contradicted = {
        **observation,
        "source": {"sha256": "ee" * 32, "path": "/same/kernel.csv", "sha256_scope": "parsed_artifact"},
    }
    conflicted = gate.score_fleet_row(row, contradicted, prediction)
    direct = gate.score_boundary(prediction, contradicted)
    assert conflicted["standalone_comparison"] == "invalid"
    assert conflicted["standalone_passed_10pct"] is False
    assert conflicted["passed_10pct"] is False
    assert conflicted["standalone_reason"] == direct["reason"] == "observation_source_sha256_witness_conflict"

    class _Rank:
        def __init__(self, sha: str, rank: int) -> None:
            self.status = "measured"
            self.phase = "decode"
            self.hardware = {"hardware_key": "Ascend950DT"}
            self.source_sha256 = sha
            self.rank = rank
            self.device_id = rank
            self.rank_conflict = None
            self.forwards = ()
            self.layer_windows = ()
            self.operators = ()
            self.boundaries = {}

    evidence = gate._evidence_from_timetables([_Rank("a" * 64, 0), _Rank("b" * 64, 13)])
    assert evidence["rank_sha_count"] == 2
    assert evidence["hardware_tier"] == "A5"
    assert "hardware" not in gate._zs_gaps({}, evidence)
    assert "source_digest" not in gate._zs_gaps({}, evidence)
    assert gate._hardware_still_missing({"hardware_tier": ""}, evidence) is False

    dataset = _setup_synthetic_dataset(tmp_path / "coverage", monkeypatch)

    def _observe(_cfg: dict) -> dict:
        return {
            "capture": {"capture_id": "test_suite:v41_decode_c4", "phase": "decode", "hardware_tier": "A5"},
            "measurements": {"per_forward_window": {
                "status": "measured", "samples_basis": "elapsed",
                "samples": [{"key": "f0", "observed_ms": 10.0, "phase": "decode", "forward_id": "f0"}],
            }},
        }

    def _predict(_cfg: dict) -> dict:
        return {
            "status": "modeled", "prediction_boundary": "per_forward_window", "boundary_basis": "elapsed",
            "capture_id": "test_suite:v41_decode_c4", "phase": "decode", "hardware_tier": "A5",
            "boundary_samples": [{"key": "f0", "boundary_ms": 12.0, "phase": "decode", "forward_id": "f0"}],
        }

    def _builder() -> list[dict]:
        return [{
            "capture_id": "test_suite:v41_decode_c4", "suite": "registered_decode",
            "phase": "decode", "hardware_tier": "A5",
            "source_calibration": {"evaluation_relation": "in_sample", "target_timing_used_to_fit": False},
        }]

    labeled = gate.evaluate(
        dataset, strict_10pct=False, inventory="targeted", summary_dir=tmp_path / "sum",
        identity_builder=_builder, simulator_name="unit",
        predict=_predict, observe=_observe, run_validation=lambda **_kw: {},
    )
    disclosed = json.loads((tmp_path / "sum" / "per_id.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert disclosed["evaluation_relation"] == "in_sample"
    assert disclosed["coverage_only"] is True
    assert disclosed["boundary_scope"] == "forward_body"
    assert disclosed["passed_10pct"] is False
    assert disclosed["key_matched"] == 1
    assert disclosed["max_error"] == pytest.approx(0.2)
    assert labeled["strict_global_pass"] is False
    assert labeled["blind_accuracy"]["forward_body"]["above_10pct"] == 0
    assert labeled["blind_accuracy"]["forward_body"]["rows"] == 0
    assert labeled["coverage_stratum"]["forward_body"]["above_10pct"] == 1
    assert labeled["coverage_stratum"]["forward_body"]["max_error"] == pytest.approx(0.2)
    assert labeled["totals"]["unique_captures"] == 2
    assert labeled["scheduler"]["forward"]["rows"] == 1
    assert labeled["scheduler"]["forward"]["key_matched"] == 1
    assert labeled["scheduler"]["forward"]["above_10pct"] == 1
    assert labeled["scheduler"]["standalone"]["rows"] == 0
    assert labeled["scheduler"]["L1"]["status"] == "not_a_sample"
    assert labeled["scheduler"]["L2"]["status"] == "not_a_sample"
    assert labeled["scheduler"]["L3"]["status"] == "not_a_sample"
    assert labeled["scheduler"]["L4"]["rows"] == 0
    assert labeled["scheduler"]["L1"]["keys_over_10pct"] is None
    one = gate.singleton_request_ttft(
        {"success": 1, "failed": 0, "streams": [{"ok": True, "ttft_s": 1.5}], "ttft_mean_s": 1.5}, "prefill")
    assert one["eligible"] is True
    assert one["observed_ms"] == pytest.approx(1500.0)
    many = gate.singleton_request_ttft(
        {"success": 2, "failed": 0, "streams": [{"ok": True, "ttft_s": 1.0}, {"ok": True, "ttft_s": 3.0}], "ttft_mean_s": 2.0},
        "prefill")
    assert many["eligible"] is False
    assert many["reason"] == "request_population_not_singleton"
    decode = gate.singleton_request_ttft(
        {"success": 1, "failed": 0, "streams": [{"ok": True, "ttft_s": 1.0}], "ttft_mean_s": 1.0, "tpot_mean_s": 0.2},
        "decode")
    assert decode["eligible"] is False
    assert decode["reason"] == "tpot_not_a_per_step_boundary"


def test_l4_pair_binds_origin_deployment_and_keeps_singleton_eligibility() -> None:
    """Ordinary GLM5.1 authorization matches an explicit correct file. Bad checks do not price."""
    import hashlib
    import json

    import hf_benchmark_gate as gate

    cells = Path("/tmp/mindie-sim-profiling-bench/data/zero_shot_l1_l4_cells.jsonl")
    assert cells.is_file()
    rows = {}
    for line in cells.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("cell_id") in {"glm51_dp16tp1ep16_pf_1k_c1", "glm53_dp16tp1ep16_pf_1k_c1"}:
            rows[row["cell_id"]] = row
    assert set(rows) == {"glm51_dp16tp1ep16_pf_1k_c1", "glm53_dp16tp1ep16_pf_1k_c1"}
    base = rows["glm51_dp16tp1ep16_pf_1k_c1"]
    origin51 = hfb._zero_shot_l4_pair(base)
    origin53 = hfb._zero_shot_l4_pair(rows["glm53_dp16tp1ep16_pf_1k_c1"])
    price51 = origin51["prediction"]["boundary_ms"]
    price53 = origin53["prediction"]["boundary_ms"]
    assert origin51["eligible"] is True and origin53["eligible"] is True
    assert origin51["source_raw"] == "bound" and origin53["source_raw"] == "bound"
    assert origin51["observed_ms"] == pytest.approx(407.916)
    assert price51 != pytest.approx(price53)
    assert price51 != pytest.approx(94.80180157034263)
    assert price53 != pytest.approx(94.80180157034263)
    assert "GLM-5.1" in origin51["source_config"] and "GLM-5.3" in origin53["source_config"]
    file51 = Path(origin51["source_config"])
    file53 = Path(origin53["source_config"])
    sha51 = hashlib.sha256(file51.read_bytes()).hexdigest()
    sha53 = hashlib.sha256(file53.read_bytes()).hexdigest()
    assert sha51.startswith("726e45") and sha53.startswith("ca8f")
    assert origin51["source_config_sha256"] == sha51 and origin53["source_config_sha256"] == sha53
    assert sha51 != sha53
    physical = ("source_config", "source_config_sha256", "source_deploy_sha256", "source_weight_dir", "source_case_dir", "require_source")
    for key in physical:
        assert origin51["prediction"][key] == origin51[key]
        assert origin53["prediction"][key] == origin53[key]
    assert origin51["require_source"] is True and origin51["source_deploy_sha256"] == sha51
    assert Path(origin51["source_weight_dir"]).name in file51.parent.name

    def _grade(bundle: dict[str, Any]) -> dict[str, Any]:
        if bundle.get("eligible") and isinstance(bundle.get("observation"), dict) and isinstance(bundle.get("prediction"), dict):
            tier = str(bundle["prediction"].get("hardware_tier") or "A5")
            return gate.score_fleet_row(
                {"capture_id": bundle["observation"]["capture"]["capture_id"], "suite": "zero_shot", "phase": "prefill", "hardware_tier": tier},
                gate._stamp_hardware(bundle["observation"], tier),
                gate._stamp_hardware(bundle["prediction"], tier),
            )
        return {"comparison": "uncovered", "comparison_reason": bundle.get("reason"), "l4_eligible": bool(bundle.get("eligible"))}

    declared = dict(base)
    declared["source_config"] = str(file51)
    declared["source_config_sha256"] = sha51
    same = hfb._zero_shot_l4_pair(declared)
    assert json.dumps(same["prediction"], sort_keys=True) == json.dumps(origin51["prediction"], sort_keys=True)
    assert same["observed_ms"] == origin51["observed_ms"] and same["eligible"] is True
    for key in physical:
        assert same[key] == origin51[key]
    assert same["declared_config"] == str(file51)
    assert same["prediction"]["source_config"] == origin51["source_config"]
    assert _grade(origin51)["comparison"] == "compared"
    assert _grade(same)["comparison"] == "compared"

    def _check(path, sha) -> dict[str, Any]:
        test = dict(base)
        if path is not None:
            test["source_config"] = str(path)
        if sha is not None:
            test["source_config_sha256"] = sha
        bundle = hfb._zero_shot_l4_pair(test)
        assert bundle["eligible"] is True
        assert bundle["observed_ms"] == pytest.approx(407.916)
        assert bundle.get("key") == origin51.get("key")
        assert "boundary_ms" not in bundle
        return bundle

    missing = _check(Path("/never-existed-Astra/config.json"), sha51)
    assert missing["reason"] == "source_override_path_invalid" and missing["source_raw"] == "missing"
    assert "prediction" not in missing and "source_config" not in missing
    assert _grade(missing)["comparison"] == "uncovered"
    assert missing["declared_config"].endswith("/never-existed-Astra/config.json")
    foreign = _check(file53, sha53)
    assert foreign["reason"] == "source_override_contradicts_deployment" and foreign["source_raw"] == "uncertain"
    assert "prediction" not in foreign and "source_config" not in foreign
    assert foreign["declared_config_sha256"] == sha53
    assert _grade(foreign)["comparison"] == "uncovered"
    no_path = _check(None, sha51)
    assert no_path["reason"] == "source_override_path_invalid" and "prediction" not in no_path
    false_sha = _check(file51, "f" * 64)
    assert false_sha["reason"] == "source_config_sha256_mismatch" and false_sha["source_raw"] == "uncertain"
    assert false_sha["source_config"] == origin51["source_config"]
    assert false_sha["source_config_sha256"] == sha51 and false_sha["source_deploy_sha256"] == origin51["source_deploy_sha256"]
    assert false_sha["source_weight_dir"] == origin51["source_weight_dir"]
    assert false_sha["source_case_dir"] == origin51["source_case_dir"] and origin51["source_case_dir"]
    assert "boundary_ms" not in false_sha["prediction"]
    assert false_sha["prediction"]["source_sha256"] == "f" * 64
    assert false_sha["prediction"]["source_config_sha256"] == sha51
    assert false_sha["observation"]["source"]["sha256"] == sha51
    assert false_sha["observation"]["measurements"]["native_client_request"]["samples"][0]["observed_ms"] == pytest.approx(407.916)
    graded = _grade(false_sha)
    assert graded["comparison"] == "invalid" and graded["comparison_reason"] == "source_sha256_mismatch"
    assert graded["passed_10pct"] is False and graded["sample"] is None
