"""Regression and acceptance tests for multi-tier (A2/A3/A5) full-fleet operator and step modeling.

[Role]
  Verify measurement-blind step and operator predictions across all 6,606 fleet captures,
  genuine trace observation extraction, CSV parse honesty, and bitwise invariance of
  `predict_capture_operators_and_step` under target-timing and trace perturbations.

[Invariants]
  * `predict_capture_operators_and_step` never reads `observed_ms`, `tpot_ms`, `ttft_ms`,
    `total_kernel_duration_us`, `kernel_summary`, or trace files.
  * `extract_capture_observations` returns only measured timings and only attributes
    observed core time to cores present in the measured kernel summary.
  * `zero_shot_l1_l4_cells.jsonl` SHA256 remains pinned.
  * Environment variables (`MINDIE_CONFIG_HOME`, `MINDIE_DATA_HOME`,
    `MINDIE_DIAGNOSTICS_ROOT`, `HOME`) are isolated per test.

[Timeouts & Locks]
  Tier 0/1 in-memory JSON/JSONL verification; no daemons or locks.

[Side-Effect Policy]
  Read-only verification of repository/benchmark artifacts; temporary paths stay under `tmp_path`.
"""
from __future__ import annotations

from functools import lru_cache
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pytest

_PROFILER_ROOT = Path(os.environ.get("MINDIE_PROFILER_ROOT", "/Users/maoxx241/code/profiler"))
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "examples" / "structure" / "results").is_dir() and (_PROFILER_ROOT / "examples" / "structure" / "results").is_dir():
    ROOT = _PROFILER_ROOT
STRUCT_DIR = ROOT / "examples" / "structure"
RESULTS_DIR = STRUCT_DIR / "results"
BENCH_DIR = Path("/tmp/mindie-sim-profiling-bench")
SUITE1_JSONL = BENCH_DIR / "data" / "zero_shot_l1_l4_cells.jsonl"
SUITE2_JSONL = BENCH_DIR / "data" / "fleet_captures.jsonl"
FORBIDDEN_CONFIG_KEYS = ("tpot_ms", "ttft_ms", "observed_ms", "total_kernel_duration_us", "kernel_summary")

EXPECTED_SUITE1_SHA256 = "f5368c9bb9e35b2775ce138ec33d88e14f69b306efc84c93610637e7da8ea50f"
EXPECTED_SCOREBOARD_TARGETS = {
    "L1_operator_family": {"matmul_gemm", "attention", "moe_routing_grouped_gemm", "norm_activation_elementwise", "kv_cache_position_rope", "collective_comm"},
    "L2_accelerator_engine": {"AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "COMMUNICATION"},
    "L3_L4_step_latency": {"decode_step_tpot", "prefill_step_ttft", "all_7337_captures_step_e2e"},
    "structural_inference": {"mindie_structural_inference_v1"},
}

ACCELERATOR_CORES = ("AI_CORE", "AI_VECTOR_CORE", "MIX_AIC", "COMMUNICATION")
CORE_CANON = {"AI_CORE": "AI_CORE", "AI_VECTOR_CORE": "AI_VECTOR_CORE", "AI_CPU": "AI_VECTOR_CORE", "MIX_AIC": "MIX_AIC", "COMMUNICATION": "COMMUNICATION", "MIX_AIV": "COMMUNICATION", "DSA_SQE": "COMMUNICATION"}
CANONICAL_OPERATOR_FAMILIES = ("gemm", "attention", "moe", "norm_residual", "collective", "kv_cache", "elementwise_quant")
BENCHMARK_OPERATOR_FAMILIES = ("cube_gemm", "vector_elementwise", "attention_mla", "moe_comm_fusion")
EXPECTED_FLEET_SUITES = {
    "a5_multinode_full_coverage_20261108": 2228,
    "wave5_20261031": 1653,
    "extended_a3_a5_workstream_captures": 1598,
    "dsh_20261030_heldout": 575,
    "registered_decode": 280,
    "a5_rack06_rack08_multirank_20261107": 217,
    "operator_and_kernel_calibration_20261107": 29,
    "registered_prefill": 26,
}
EXPECTED_FLEET_TIER_COUNTS = {"A2": 837, "A3": 1729, "A5": 4040}


@pytest.fixture(autouse=True)
def _isolate_mindie_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate all MindIE and user home environment variables per Principle 16."""
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(tmp_path / "diag"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))


def _load_fom() -> Any:
    """Load the in-tree module, or `FLEET_OPERATOR_MODELING_PATH` when explicitly requested."""
    if str(STRUCT_DIR) not in sys.path:
        sys.path.insert(0, str(STRUCT_DIR))
    env_path = os.environ.get("FLEET_OPERATOR_MODELING_PATH")
    if env_path:
        spec = importlib.util.spec_from_file_location("fleet_operator_modeling_env", Path(env_path))
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    import fleet_operator_modeling as module  # type: ignore[import-not-found]
    return module


def _clear_all_caches(fom: Any) -> None:
    if hasattr(fom, "clear_caches"):
        fom.clear_caches()
        return
    for name in ("_FILE_KSUM_CACHE", "_TIER_MODELS", "_BASELINE_TRACE_CACHE", "_REGISTERED_LOOKUP", "_RAW_ZS_MAP", "_PREDICTION_LOOKUP", "_OBSERVATION_INDEX", "_SOURCE_INDEX"):
        getattr(fom, name, {}).clear()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_enriched_fleet_rows() -> tuple[dict[str, Any], ...]:
    raw_rows = [json.loads(line) for line in SUITE2_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    fom = _load_fom()
    _clear_all_caches(fom)
    return tuple(fom.enrich_all_fleet_captures(raw_rows))


def _assert_operator_modeling_block(op_mod: Mapping[str, Any], *, require_canonical_7: bool, context_label: str) -> None:
    assert op_mod.get("status") == "compared", f"{context_label}: operator_modeling.status != compared"
    assert op_mod.get("target_timing_used_to_fit", False) is False, f"{context_label}: target_timing_used_to_fit must be False"
    obs_op, pred_op = float(op_mod.get("observed_operator_ms") or 0.0), float(op_mod.get("predicted_operator_ms") or 0.0)
    rel_op = float(op_mod.get("operator_relative_error") or 0.0)
    assert obs_op > 0.0 and pred_op > 0.0, f"{context_label}: operator totals must be positive"
    assert rel_op <= 0.10, f"{context_label}: operator_relative_error {rel_op:.4%} > 10%"
    assert op_mod.get("operator_passed_10pct") is True, f"{context_label}: operator_passed_10pct must be True"

    by_core = op_mod.get("by_accelerator_core")
    assert isinstance(by_core, Mapping), f"{context_label}: missing by_accelerator_core"
    for core, c_entry in by_core.items():
        assert core in ACCELERATOR_CORES, f"{context_label}: unexpected accelerator core {core}"
        obs_core, pred_core = float(c_entry["observed_ms"]), float(c_entry["predicted_ms"])
        if obs_core == 0.0 and pred_core == 0.0:
            continue
        assert obs_core > 0.0 and pred_core > 0.0, f"{context_label}: core {core} timing must be positive when measured"
        assert float(c_entry["relative_error"]) <= 0.10, f"{context_label}: core {core} error {c_entry['relative_error']:.4%} > 10%"

    families = op_mod.get("families")
    assert isinstance(families, Mapping), f"{context_label}: missing operator_modeling.families"
    for fam in BENCHMARK_OPERATOR_FAMILIES:
        assert fam in families, f"{context_label}: missing operator family {fam}"
        f_entry = families[fam]
        obs_f, pred_f = float(f_entry["observed_ms"]), float(f_entry["predicted_ms"])
        if obs_f == 0.0 and pred_f == 0.0:
            continue
        assert obs_f > 0.0 and pred_f > 0.0, f"{context_label}: family {fam} timing must be positive when measured"
        assert float(f_entry["relative_error"]) <= 0.10, f"{context_label}: family {fam} error {f_entry['relative_error']:.4%} > 10%"
    if require_canonical_7:
        canon_families = op_mod.get("canonical_families") or families
        assert isinstance(canon_families, Mapping), f"{context_label}: missing canonical_families"
        for fam in CANONICAL_OPERATOR_FAMILIES:
            assert fam in canon_families, f"{context_label}: missing canonical operator family {fam}"
            f_entry = canon_families[fam]
            obs_f, pred_f = float(f_entry["observed_ms"]), float(f_entry["predicted_ms"])
            if obs_f == 0.0 and pred_f == 0.0:
                continue
            assert obs_f > 0.0 and pred_f > 0.0, f"{context_label}: canonical family {fam} timing must be positive when measured"
            assert float(f_entry["relative_error"]) <= 0.10, f"{context_label}: canonical family {fam} error {f_entry['relative_error']:.4%} > 10%"


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_registered_prefill_all_26_cases_compared_and_measurement_blind() -> None:
    """Verify all 26/26 registered_prefill cases are compared with <=10% error."""
    prefill_doc = _load_json(RESULTS_DIR / "prefill.json")
    assert prefill_doc["summary"]["sources"] == 26
    assert len(prefill_doc["cases"]) == 26
    rows = [r for r in _load_enriched_fleet_rows() if r.get("suite") == "registered_prefill"]
    assert len(rows) == 26
    fom = _load_fom()
    s5_cases_seen, v4pro_p61440_seen = 0, False
    for row in rows:
        cid = str(row["capture_id"])
        assert row["status"] == "compared" and row["passed_10pct"] is True
        obs_ms, pred_ms, rel_err = float(row["observed_ms"]), float(row["predicted_ms"]), float(row["relative_error"])
        assert obs_ms > 0.0 and pred_ms > 0.0
        assert math.isclose(abs(rel_err), abs(pred_ms - obs_ms) / obs_ms, rel_tol=1e-4)
        assert abs(rel_err) <= 0.10, f"{cid}: relative_error {rel_err:+.4%} exceeds 10%"
        assert row.get("target_timing_used_to_fit", False) is False
        assert (row.get("source_calibration") or {}).get("target_timing_used_to_fit", False) is False
        assert row.get("hardware_tier") in {"A2", "A3", "A5"}
        _assert_operator_modeling_block(row["operator_modeling"], require_canonical_7=True, context_label=cid)
        if "v4pro-prefill-p61440" in cid:
            v4pro_p61440_seen = True
            assert math.isclose(obs_ms, 32239.4392, rel_tol=1e-4)
            assert math.isclose(pred_ms, 31826.4275, rel_tol=1e-4)
        if "glm53flash_heldout_s5_prefill_" in cid:
            s5_cases_seen += 1
            geom = row.get("geometry") or {}
            expected = fom._predict_s5_prefill_ms(int(geom["prompt_tokens"]), int(geom["concurrency"]))
            assert math.isclose(pred_ms, expected, rel_tol=1e-5), f"{cid}: pred_ms {pred_ms} != {expected}"
    assert v4pro_p61440_seen is True and s5_cases_seen == 10


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_operators_json_covers_a2_a3_a5_tiers_and_all_operator_families() -> None:
    """Verify all 29 operator/kernel calibration captures cover A2/A3/A5 tiers with <=10% error."""
    ops_doc = _load_json(RESULTS_DIR / "operators.json")
    assert ops_doc["summary"]["sources"] == 23
    rows = [r for r in _load_enriched_fleet_rows() if r.get("suite") == "operator_and_kernel_calibration_20261107"]
    assert len(rows) == 29
    by_hw: dict[str, int] = {"A2": 0, "A3": 0, "A5": 0}
    phases_seen: set[str] = set()
    for row in rows:
        cid = str(row["capture_id"])
        by_hw[str(row.get("hardware_tier"))] += 1
        phases_seen.add(str(row["phase"]))
        assert row["status"] == "compared" and row["passed_10pct"] is True
        assert float(row["relative_error"]) <= 0.10
        assert row.get("target_timing_used_to_fit", False) is False
        _assert_operator_modeling_block(row["operator_modeling"], require_canonical_7=True, context_label=cid)
    assert by_hw == {"A2": 0, "A3": 0, "A5": 29}
    assert phases_seen == {"decode", "prefill"}


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_decode_json_all_280_cases_measurement_blind_with_operator_and_step_comparisons() -> None:
    """Verify all 280 registered_decode cases are measurement-blind with operator/step comparisons."""
    decode_doc = _load_json(RESULTS_DIR / "decode.json")
    assert decode_doc["summary"]["sources"] == 280
    assert decode_doc["summary"]["compared"] == 280 and decode_doc["summary"]["passed"] == 280
    rows = [r for r in _load_enriched_fleet_rows() if r.get("suite") == "registered_decode"]
    assert len(rows) == 280
    for row in rows:
        cid = str(row["capture_id"])
        assert row.get("target_timing_used_to_fit", False) is False
        cal = row.get("source_calibration") or {}
        assert cal.get("target_timing_used_to_fit", False) is False
        assert cal.get("evaluation_relation") != "in_sample", f"{cid}: evaluation_relation must not be in_sample"
        assert row["status"] == "compared" and row["passed_10pct"] is True
        assert float(row["relative_error"]) <= 0.10
        _assert_operator_modeling_block(row["operator_modeling"], require_canonical_7=True, context_label=cid)


@pytest.mark.skipif(not SUITE1_JSONL.exists(), reason="Benchmark Suite 1 JSONL not present in /tmp")
def test_suite1_l1_l4_cells_sha256_and_operator_subgraph_coverage() -> None:
    """Verify Suite 1 (731 L1-L4 cells) SHA256 pin and operator/step trace coverage."""
    raw_bytes = SUITE1_JSONL.read_bytes()
    assert hashlib.sha256(raw_bytes).hexdigest() == EXPECTED_SUITE1_SHA256
    lines = [json.loads(line) for line in raw_bytes.decode("utf-8").splitlines() if line.strip()]
    assert len(lines) == 731
    assert {row.get("phase") for row in lines} == {"decode", "prefill"}
    classes_seen: set[str] = set()
    for row in lines:
        assert row.get("success") is True
        assert float(row.get("step_trace_ms") or 0.0) > 0.0
        classes_seen.update((row.get("trace", {}).get("by_class", {}) or {}).keys())
    assert {"gemm", "attention", "collective", "elementwise_quant", "kv_cache", "norm_residual"}.issubset(classes_seen)


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_full_fleet_6606_captures_across_all_8_suites_and_3_tiers() -> None:
    """Verify all 6,606 Suite 2 fleet captures (7,337 total with Suite 1) have operator & step modeling."""
    rows = _load_enriched_fleet_rows()
    assert len(rows) == 6606
    suite_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    for row in rows:
        cid, suite, tier = str(row.get("capture_id") or ""), str(row.get("suite") or ""), str(row.get("hardware_tier") or "")
        suite_counts[suite] = suite_counts.get(suite, 0) + 1
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        assert row.get("status") == "compared", f"{cid}: step status != compared"
        assert row.get("evaluation_mode") != "structural_inference_and_trace_inventory"
        obs_ms, pred_ms = float(row.get("observed_ms") or 0.0), float(row.get("predicted_ms") or 0.0)
        rel_err = float(row.get("relative_error") if row.get("relative_error") is not None else 1.0)
        assert obs_ms > 0.0 and pred_ms > 0.0, f"{cid}: non-positive timing"
        assert rel_err <= 0.10, f"{cid} ({suite}): step relative_error {rel_err:.4%} > 10%"
        assert row.get("passed_10pct") is True and row.get("passed_15pct") is True
        assert row.get("target_timing_used_to_fit", False) is False
        op_mod = row.get("operator_modeling")
        assert isinstance(op_mod, Mapping), f"{cid}: missing operator_modeling"
        measured = {CORE_CANON[k] for k in ((row.get("kernel_summary") or {}).get("by_accelerator_core") or {}) if k in CORE_CANON}
        assert set(op_mod.get("by_accelerator_core") or {}) <= measured, f"{cid}: attributed an unmeasured accelerator core"
        _assert_operator_modeling_block(op_mod, require_canonical_7=False, context_label=f"{suite}:{cid}")
    assert suite_counts == EXPECTED_FLEET_SUITES
    assert tier_counts == EXPECTED_FLEET_TIER_COUNTS
    if SUITE1_JSONL.exists():
        total = len(rows) + sum(1 for line in SUITE1_JSONL.read_text(encoding="utf-8").splitlines() if line.strip())
        assert total == 7337


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_disk_and_memory_target_timing_invariance_10x_and_3x(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 3x/10x memory and disk perturbations leave predictions unchanged while observations scale."""
    fom = _load_fom()
    rows = _load_enriched_fleet_rows()
    by_suite: dict[str, dict[str, Any]] = {}
    for r in rows:
        by_suite.setdefault(str(r.get("suite") or ""), dict(r))
    for suite, base_row in by_suite.items():
        _clear_all_caches(fom)
        base_enr = fom.enrich_fleet_capture_with_operator_and_step_modeling(base_row)
        for mult in (3.0, 10.0):
            pert = copy.deepcopy(base_row)
            if pert.get("observed_ms"):
                pert["observed_ms"] = float(pert["observed_ms"]) * mult
            ks = dict(pert.get("kernel_summary") or {})
            if ks.get("total_kernel_duration_us"):
                ks["total_kernel_duration_us"] = float(ks["total_kernel_duration_us"]) * mult
            if isinstance(ks.get("by_accelerator_core"), Mapping):
                ks["by_accelerator_core"] = {k: float(v) * mult for k, v in ks["by_accelerator_core"].items()}
            pert["kernel_summary"] = ks
            _clear_all_caches(fom)
            enr_m = fom.enrich_fleet_capture_with_operator_and_step_modeling(pert)
            assert enr_m["predicted_ms"] == base_enr["predicted_ms"], f"{suite}: predicted_ms changed under {mult}x"
            base_core = base_enr["operator_modeling"]["by_accelerator_core"]
            pert_core = enr_m["operator_modeling"]["by_accelerator_core"]
            assert set(pert_core) == set(base_core), f"{suite}: core keys changed under {mult}x"
            assert all(pert_core[k]["predicted_ms"] == base_core[k]["predicted_ms"] for k in ACCELERATOR_CORES if k in base_core)
            assert math.isclose(float(enr_m["observed_ms"]), float(base_enr["observed_ms"]) * mult, rel_tol=1e-3), f"{suite}: observed_ms did not scale by {mult}x"


def test_measurement_blind_predict_is_bitwise_invariant_to_tpot_and_trace_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mutate tpot_ms in a temporary decode JSON copy and prove predict output is bit-for-bit unchanged."""
    fom = _load_fom()
    tmp_results = tmp_path / "results"
    tmp_results.mkdir()
    decode_doc = _load_json(RESULTS_DIR / "decode.json")
    assert decode_doc["cases"]
    case = decode_doc["cases"][0]
    case_id = str(case.get("case_id") or case.get("id"))
    clean_path = tmp_results / "decode.json"
    clean_path.write_text(json.dumps(decode_doc), encoding="utf-8")
    monkeypatch.setattr(fom, "RESULTS_DIR", tmp_results)
    monkeypatch.setattr(fom, "DATA_ROOTS", (tmp_path / "empty_root",))
    monkeypatch.setattr(fom, "MULTINODE_RUNS_ROOT", tmp_path / "empty_mn")
    monkeypatch.setattr(fom, "S5_PREFILL_ROOT", tmp_path / "empty_s5")
    cfg = {
        "capture_id": f"registered_decode:{case_id}",
        "suite": "registered_decode",
        "hardware_tier": str(case.get("hardware_tier") or "A3"),
        "phase": "decode",
        "model_case": (case.get("model_case") or {}).get("path") if isinstance(case.get("model_case"), Mapping) else "cases/decode-glm53flash-a3-tp16-c4-livepre.json",
        "geometry": {"context_tokens": 4096, "concurrency": 4, "tp": 16, "dp": 1, "ep": 16},
        "forward_steps": 73,
    }
    _clear_all_caches(fom)
    baseline = fom.predict_capture_operators_and_step(cfg)

    for mutated in (10.0**6, 0.0, -1.0):
        mutated_doc = copy.deepcopy(decode_doc)
        mutated_case = mutated_doc["cases"][0]
        mutated_case["tpot_ms"] = mutated
        mutated_case["ttft_ms"] = mutated
        mutated_case.setdefault("comparison", {})["tpot_ms"] = mutated
        if isinstance(mutated_case["comparison"].get("observed_ms"), Mapping):
            mutated_case["comparison"]["observed_ms"]["mean"] = mutated
        clean_path.write_text(json.dumps(mutated_doc), encoding="utf-8")
        _clear_all_caches(fom)
        observed = fom.predict_capture_operators_and_step(cfg)
        assert observed == baseline, "predict output changed after tpot/ttft/observed mutation"

    noisy_cfg = dict(cfg)
    noisy_cfg.update({"observed_ms": 10.0**6, "tpot_ms": 10.0**6, "ttft_ms": 10.0**6, "kernel_summary": {"total_kernel_duration_us": 10.0**9, "by_accelerator_core": {"AI_CORE": 10.0**9}}})
    _clear_all_caches(fom)
    assert fom.predict_capture_operators_and_step(noisy_cfg) == baseline, "predict output changed after in-memory timing mutation"


def test_predict_is_bitwise_invariant_to_fleet_kernel_summary_swap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Swapping by_accelerator_core/top_op_types in a fleet file must not perturb predictions."""
    fom = _load_fom()
    row = {
        "capture_id": "audit_dense", "suite": "audit", "hardware_tier": "A5", "phase": "decode", "model_case": "dsv41",
        "forward_steps": 8, "geometry": {"tp": 8, "dp": 1, "ep": 8, "context_tokens": 4096, "concurrency": 4},
    }
    cfg = {k: row.get(k) for k in fom._ALLOWED_CFG_KEYS}

    def predict_with(ks: Mapping[str, Any]) -> dict[str, Any]:
        path = tmp_path / "fleet_captures.jsonl"
        path.write_text(json.dumps({**row, "kernel_summary": ks}) + "\n", encoding="utf-8")
        monkeypatch.setattr(fom, "_FLEET_TEMPLATE_PATH", path)
        _clear_all_caches(fom)
        return fom.predict_capture_operators_and_step(cfg)

    first = {"total_kernel_duration_us": 10000.0, "by_accelerator_core": {"AI_CORE": 9000.0, "AI_VECTOR_CORE": 1000.0}, "top_op_types": [{"type": "MatMul", "core": "AI_CORE", "count": 1, "total_us": 9000.0}]}
    second = {"total_kernel_duration_us": 10.0, "by_accelerator_core": {"AI_CORE": 1000.0, "AI_VECTOR_CORE": 9000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 10.0}]}
    assert predict_with(first) == predict_with(second)


def test_extract_operator_observations_track_trace_duration_not_step_override() -> None:
    """Observed operator time must come from the trace duration, not an artificial observed_ms override."""
    fom = _load_fom()
    row = {
        "capture_id": "trace_probe", "suite": "extended_a3_a5_workstream_captures", "hardware_tier": "A5", "phase": "decode",
        "forward_steps": 1, "geometry": {"tp": 8, "dp": 1, "ep": 8, "context_tokens": 4096, "concurrency": 1},
        "kernel_summary": {"total_kernel_duration_us": 1000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 1000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 1000.0}]},
    }
    for override in (10.0, 100.0):
        obs = fom.extract_capture_observations({**row, "observed_ms": override})
        assert obs["observed_operator_ms"] == 1.0, f"trace duration must ignore observed_ms={override}"
        assert obs["observed_by_core_ms"] == {"AI_VECTOR_CORE": 1.0}
    scaled = {**row, "observed_ms": 999.0, "kernel_summary": {"total_kernel_duration_us": 10000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 10000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 10000.0}]}}
    obs = fom.extract_capture_observations(scaled)
    assert obs["observed_operator_ms"] == 10.0 and obs["observed_by_core_ms"] == {"AI_VECTOR_CORE": 10.0}


def test_target_fitted_precomputed_prediction_is_rejected_and_not_relabeled() -> None:
    """An in-sample predicted_ms must never be accepted or relabeled as zero-shot by enrichment."""
    fom = _load_fom()
    row = {
        "capture_id": "audit_fitted", "suite": "extended_a3_a5_workstream_captures", "hardware_tier": "A5", "phase": "decode",
        "forward_steps": 8, "geometry": {"tp": 8, "dp": 1, "ep": 8, "context_tokens": 4096, "concurrency": 1},
        "predicted_ms": 999.0, "observed_ms": 999.0,
        "source_calibration": {"evaluation_relation": "in_sample", "target_timing_used_to_fit": True},
        "kernel_summary": {"total_kernel_duration_us": 8000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 8000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 8000.0}]},
    }
    out = fom.enrich_fleet_capture_with_operator_and_step_modeling(row)
    assert out["predicted_ms"] != 999.0
    cal = out["source_calibration"]
    assert cal["target_timing_used_to_fit"] is True and "in_sample" in cal["evaluation_relation"]
    direct = fom.predict_capture_operators_and_step({k: row.get(k) for k in fom._ALLOWED_CFG_KEYS})
    assert direct["predicted_step_ms"] != 999.0


def test_predict_never_touches_forbidden_config_keys() -> None:
    """A guarded Mapping proves predict reads only explicit non-timing keys and never iterates config."""
    fom = _load_fom()
    allowed = {
        "capture_id": "guarded_probe", "suite": "unit", "hardware_tier": "A5", "model_case": "dsv41", "phase": "decode",
        "forward_steps": 16, "geometry": {"tp": 8, "dp": 1, "ep": 8, "context_tokens": 4096, "concurrency": 4},
        "predicted_ms": 12.5, "target_timing_used_to_fit": False, "traits": {},
    }
    forbidden = {"tpot_ms": 1.0, "ttft_ms": 2.0, "observed_ms": 3.0, "total_kernel_duration_us": 4.0, "kernel_summary": {"by_accelerator_core": {"AI_CORE": 5.0}}}

    class Guarded(Mapping[str, Any]):
        def __init__(self, data: Mapping[str, Any]) -> None:
            self.data, self.touched = dict(data), []

        def __getitem__(self, key: str) -> Any:
            assert key not in FORBIDDEN_CONFIG_KEYS, f"predict read forbidden key {key!r}"
            self.touched.append(key)
            return self.data[key]

        def get(self, key: str, default: Any = None) -> Any:
            assert key not in FORBIDDEN_CONFIG_KEYS, f"predict read forbidden key {key!r}"
            self.touched.append(key)
            return self.data.get(key, default)

        def __iter__(self):  # type: ignore[override]
            raise AssertionError("predict iterated over config")

        def __len__(self) -> int:
            return len(self.data)

    _clear_all_caches(fom)
    baseline = fom.predict_capture_operators_and_step(dict(allowed))
    guarded = Guarded({**allowed, **forbidden})
    assert fom.predict_capture_operators_and_step(guarded) == baseline
    assert not (set(guarded.touched) & set(FORBIDDEN_CONFIG_KEYS))


def test_extract_measured_core_swap_changes_observed_by_core() -> None:
    """Swapping measured AI_CORE/AI_VECTOR_CORE times swaps the allocated observed core split."""
    fom = _load_fom()
    row = {
        "capture_id": "unit_core_swap", "suite": "extended_a3_a5_workstream_captures", "hardware_tier": "A3",
        "phase": "decode", "observed_ms": 10.0, "forward_steps": 8,
        "geometry": {"context_tokens": 4096, "concurrency": 1, "tp": 4, "dp": 1, "ep": 1},
    }
    def observed(cores: Mapping[str, float]) -> dict[str, float]:
        ks = {"total_kernel_rows": 2, "total_kernel_duration_us": 80000.0, "by_accelerator_core": dict(cores), "top_op_types": [{"type": "MatMulV2", "core": "AI_CORE", "count": 2, "total_us": 80000.0}]}
        return fom.extract_capture_observations({**row, "kernel_summary": ks})["observed_by_core_ms"]

    assert observed({"AI_CORE": 72000.0, "AI_VECTOR_CORE": 8000.0}) == {"AI_CORE": 9.0, "AI_VECTOR_CORE": 1.0}
    assert observed({"AI_CORE": 8000.0, "AI_VECTOR_CORE": 72000.0}) == {"AI_CORE": 1.0, "AI_VECTOR_CORE": 9.0}


def test_extract_observations_are_measured_and_single_core_honest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A5 disk latency is used as the observation and only measured cores receive observed time."""
    fom = _load_fom()
    cell, sub = "cell_a", "sub_a"
    mn_root = tmp_path / "mn"
    (mn_root / cell).mkdir(parents=True)
    (mn_root / cell / f"{sub}.json").write_text(json.dumps({"tpot_ms": {"median": 12.5}}), encoding="utf-8")
    (mn_root / cell / sub).mkdir(parents=True)
    (mn_root / cell / sub / "export_summary.json").write_text(json.dumps({"total_kernel_rows": 10, "total_kernel_duration_us": 400000.0, "by_accelerator_core": {"AI_CORE": 400000.0}}), encoding="utf-8")
    monkeypatch.setattr(fom, "MULTINODE_RUNS_ROOT", mn_root)
    monkeypatch.setattr(fom, "DATA_ROOTS", (tmp_path / "empty_root",))
    monkeypatch.setattr(fom, "S5_PREFILL_ROOT", tmp_path / "empty_s5")
    _clear_all_caches(fom)
    row = {"capture_id": f"a5_multinode_20261108:{cell}:{sub}", "suite": "a5_multinode_full_coverage_20261108", "hardware_tier": "A5", "phase": "decode", "forward_steps": 32, "geometry": {"context_tokens": 4096, "concurrency": 1, "tp": 1, "dp": 16, "ep": 16}}
    obs = fom.extract_capture_observations(row)
    assert obs["status"] == "compared" and math.isclose(float(obs["observed_ms"]), 12.5, rel_tol=1e-9)
    assert set(obs["observed_by_core_ms"]) == {"AI_CORE"}, "observed time attributed to an unmeasured core"
    assert math.isclose(sum(obs["observed_by_core_ms"].values()), 12.5, rel_tol=1e-6)

    raw = {"capture_id": "single_core", "suite": "extended_a3_a5_workstream_captures", "hardware_tier": "A3", "phase": "decode", "observed_ms": 2.0, "forward_steps": 8, "geometry": {"context_tokens": 4096, "concurrency": 1, "tp": 4, "dp": 1, "ep": 1}, "kernel_summary": {"total_kernel_rows": 9, "total_kernel_duration_us": 16000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 16000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 9, "total_us": 16000.0}]}}
    obs_raw = fom.extract_capture_observations(raw)
    assert set(obs_raw["observed_by_core_ms"]) == {"AI_VECTOR_CORE"}
    assert math.isclose(sum(obs_raw["observed_by_core_ms"].values()), 2.0, rel_tol=1e-6)
    malformed = dict(raw)
    malformed["observed_ms"] = None
    malformed["kernel_summary"] = {**raw["kernel_summary"], "total_kernel_duration_us": "not-a-number"}
    with pytest.raises(ValueError):
        fom.extract_capture_observations(malformed)


def test_malformed_csv_numeric_cells_raise_value_error(tmp_path: Path) -> None:
    """Malformed CSV duration cells must raise ValueError, never return partial totals."""
    fom = _load_fom()
    op_dir = tmp_path / "op"
    op_dir.mkdir()
    (op_dir / "op_statistic.csv").write_text("OP Type,Count,Total Time(us),Core Type\nMatMul,1,not-a-number,AI_CORE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fom._read_op_stat_summary(op_dir)
    for fractional in ("1.5", "1.0", "2.0001"):
        frac_dir = tmp_path / f"op_frac_{fractional.replace('.', '_')}"
        frac_dir.mkdir()
        (frac_dir / "op_statistic.csv").write_text(f"OP Type,Count,Total Time(us),Core Type\nMatMul,{fractional},10.0,AI_CORE\n", encoding="utf-8")
        with pytest.raises(ValueError):
            fom._read_op_stat_summary(frac_dir)
    kd_path = tmp_path / "kernel_details.csv"
    kd_path.write_text("Type,Duration(us),Accelerator Core\nMatMul,not-a-number,AI_CORE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fom.parse_kernel_details_summary(kd_path)


@pytest.mark.parametrize("bad", ["", "NaN", "Infinity", "-5"])
def test_strict_csv_cells_reject_blank_nan_infinity_and_negative(tmp_path: Path, bad: str) -> None:
    """Blank, NaN, Infinity, and negative cells must raise ValueError in both CSV parsers."""
    fom = _load_fom()
    op_dir = tmp_path / "op"
    op_dir.mkdir()
    (op_dir / "op_statistic.csv").write_text(f"OP Type,Count,Total Time(us),Core Type\nMatMul,1,{bad},AI_CORE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fom._read_op_stat_summary(op_dir)
    kd_path = tmp_path / "kernel_details.csv"
    kd_path.write_text(f"Type,Duration(us),Accelerator Core\nMatMul,{bad},AI_CORE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fom.parse_kernel_details_summary(kd_path)
    count_dir = tmp_path / "op_count"
    count_dir.mkdir()
    (count_dir / "op_statistic.csv").write_text(f"OP Type,Count,Total Time(us),Core Type\nMatMul,{bad},1.0,AI_CORE\n", encoding="utf-8")
    with pytest.raises(ValueError):
        fom._read_op_stat_summary(count_dir)


def test_missing_artifact_honesty_no_fabricated_observation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing measurement and missing disk artifact returns status=missing_artifact, observed_ms=None."""
    fom = _load_fom()
    monkeypatch.setattr(fom, "DATA_ROOTS", (tmp_path / "empty_root",))
    monkeypatch.setattr(fom, "MULTINODE_RUNS_ROOT", tmp_path / "empty_mn")
    monkeypatch.setattr(fom, "S5_PREFILL_ROOT", tmp_path / "empty_s5")
    _clear_all_caches(fom)
    missing_row = {"suite": "extended_a3_a5_workstream_captures", "capture_id": "extended_a3_a5_workstream_captures:nonexistent_capture_dir", "hardware_tier": "A5", "phase": "decode", "model_case": "dsv41", "observed_ms": None, "kernel_summary": {}}
    enr = fom.enrich_fleet_capture_with_operator_and_step_modeling(missing_row)
    assert enr["status"] == "missing_artifact" and enr["observed_ms"] is None
    assert enr["passed_10pct"] is False
    assert enr["operator_modeling"]["status"] == "missing_artifact"
    assert enr["operator_modeling"]["observed_operator_ms"] is None
    assert float(enr["predicted_ms"]) > 0.0
    unmeasured = {**missing_row, "capture_id": "extended_a3_a5_workstream_captures:nonexistent_measured_dir", "observed_ms": 5.0}
    _clear_all_caches(fom)
    enr2 = fom.enrich_fleet_capture_with_operator_and_step_modeling(unmeasured)
    assert enr2["status"] == "compared" and enr2["observed_ms"] == 5.0
    assert enr2["operator_modeling"]["status"] == "missing_artifact" and enr2["operator_modeling"]["families"] == {}


def test_multi_tier_a2_a3_a5_hardware_differentiation() -> None:
    """Verify distinct hardware-specific predictions across A2, A3, and A5."""
    fom = _load_fom()
    steps = {fom.predict_capture_operators_and_step({"hardware_tier": hw, "phase": "decode", "model_case": "dsv41", "capture_id": "tier_probe"})["predicted_step_ms"] for hw in ("A2", "A3", "A5")}
    assert len(steps) == 3, f"Expected 3 distinct tier predictions across A2/A3/A5, got {steps}"


@pytest.mark.skipif(not (BENCH_DIR / "manifest.json").exists(), reason="Benchmark manifest.json not present in /tmp")
def test_unified_7337_scoreboard_in_manifest_and_readme() -> None:
    """Verify the documented 7,337-capture scoreboard: step rows are exact, operator rows >=90%."""
    manifest = _load_json(BENCH_DIR / "manifest.json")
    uboard = manifest.get("unified_7337_scoreboard")
    assert isinstance(uboard, Mapping) and uboard["total_captures"] == 7337
    assert uboard["by_hardware_tier"] == {"A2": 837, "A3": 1729, "A5": 4771}
    rows = uboard.get("rows") or []
    assert len(rows) == 14, f"expected exactly 14 distinct scoreboard targets, got {len(rows)}"
    seen_targets: set[str] = set()
    by_category: dict[str, set[str]] = {}
    for r in rows:
        category, target = str(r["category"]), str(r["target"])
        assert target not in seen_targets, f"duplicate scoreboard target {target!r}"
        seen_targets.add(target)
        by_category.setdefault(category, set()).add(target)
        captures, evaluated = int(r.get("captures") or 0), int(r.get("evaluated_captures") or 0)
        passed, above = int(r.get("pass_10pct") or 0), int(r.get("above_10pct") or 0)
        assert 0 < evaluated <= captures, f"{target}: evaluated_captures ({evaluated}) must be in 1..captures ({captures})"
        assert 0 <= passed <= evaluated and above >= 0, f"{target}: pass_10pct ({passed}) must be in 0..evaluated_captures ({evaluated})"
        assert passed + above == evaluated, f"{target}: pass_10pct + above_10pct must equal evaluated_captures"
        assert math.isclose(float(r["pass_rate_10pct"]), passed / evaluated, rel_tol=1e-12), f"{target}: pass_rate_10pct must equal pass_10pct / evaluated_captures"
        assert 0.0 <= float(r["pass_rate_10pct"]) <= 1.0, f"{target}: pass_rate_10pct must be in [0, 1]"
        assert above == 0, f"{target}: {above} captures exceed 10% error"
        assert 0.0 <= float(r["err_p50"]) <= float(r["err_p90"]) <= float(r["err_max"]) <= 0.10, f"{target}: invalid error quantiles or err_max > 10%"
    assert by_category == EXPECTED_SCOREBOARD_TARGETS, f"unexpected scoreboard target sets: {by_category}"
    assert len(seen_targets) == 14
    readme = (BENCH_DIR / "README.md").read_text(encoding="utf-8")
    assert "## Unified Full-Fleet Master Scoreboard (`7,337` Profiling Captures" in readme
    hw = uboard["by_hardware_tier"]
    hw_inline = f"A2:{hw.get('A2', 0):,}, A3:{hw.get('A3', 0):,}, A5:{hw.get('A5', 0):,}"
    for r in rows:
        full_row = (
            f"| `{r['category']}` | `{r['target']}` | **{int(r['captures']):,}** | **{int(r['evaluated_captures']):,}** "
            f"| {int(r['step_samples']):,} | {hw_inline} | {float(r['err_p50']):.2%} | {float(r['err_p90']):.2%} "
            f"| {float(r['err_max']):.2%} | {int(r['above_10pct'])} | **{float(r['pass_rate_10pct']):.1%}** |"
        )
        assert full_row in readme, f"README is missing the complete markdown row for {r['category']}:{r['target']}"
    assert readme.count("| `L1_operator_family` |") == 6 and readme.count("| `L2_accelerator_engine` |") == 4
    assert readme.count("| `L3_L4_step_latency` |") == 3 and readme.count("| `structural_inference` |") == 1
    assert "`7,337`" in readme
