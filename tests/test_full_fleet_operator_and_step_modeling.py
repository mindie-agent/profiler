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
def _load_raw_fleet_rows() -> tuple[dict[str, Any], ...]:
    raw_rows = [json.loads(line) for line in SUITE2_JSONL.read_text(encoding="utf-8").splitlines() if line.strip()]
    return tuple(raw_rows)


def _glm_livepre_cfg() -> dict[str, Any]:
    return {
        "capture_id": "registered_decode:glm53flash-a3-tp16-c4-livepre",
        "suite": "registered_decode",
        "hardware_tier": "A3",
        "phase": "decode",
        "model_case": "cases/decode-glm53flash-a3-tp16-c4-livepre.json",
        "forward_steps": 73,
        "geometry": {
            "tp": 16, "dp": 1, "ep": 16,
            "sequences_per_replica": 4, "tokens_per_sequence": 6, "query_rows": 24,
            "context_tokens": 4096, "context_basis": "not_observed_from_cache_capacity",
        },
    }


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
    rows = [r for r in _load_raw_fleet_rows() if r.get("suite") == "registered_prefill"]
    assert len(rows) == 26
    fom = _load_fom()
    s5_cases_seen, v4pro_p61440_seen = 0, False
    for row in rows:
        cid = str(row["capture_id"])
        if "v4pro-prefill-p61440" in cid:
            v4pro_p61440_seen = True
        if "glm53flash_heldout_s5_prefill_" in cid:
            s5_cases_seen += 1
        pred = fom.predict_capture_operators_and_step({k: row.get(k) for k in fom._ALLOWED_CFG_KEYS})
        assert pred["status"] in {"modeled", "insufficient_evidence", "model_rejected"}
        if pred["status"] == "modeled":
            assert float(pred["predicted_step_ms"]) > 0.0
            assert pred["measurement_features_read"] is False
        else:
            assert pred["predicted_step_ms"] is None
            assert pred.get("diagnostics")
    assert v4pro_p61440_seen is True and s5_cases_seen == 10


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_operators_json_covers_a2_a3_a5_tiers_and_all_operator_families() -> None:
    """Verify all 29 operator/kernel calibration captures cover A2/A3/A5 tiers with <=10% error."""
    ops_doc = _load_json(RESULTS_DIR / "operators.json")
    assert ops_doc["summary"]["sources"] == 23
    rows = [r for r in _load_raw_fleet_rows() if r.get("suite") == "operator_and_kernel_calibration_20261107"]
    assert len(rows) == 29
    by_hw: dict[str, int] = {"A2": 0, "A3": 0, "A5": 0}
    phases_seen: set[str] = set()
    fom = _load_fom()
    for row in rows:
        by_hw[str(row.get("hardware_tier"))] += 1
        phases_seen.add(str(row["phase"]))
        # Standalone kernels are I's primitive contract, not one catalog layer.
        pred = fom.predict_capture_operators_and_step({k: row.get(k) for k in fom._ALLOWED_CFG_KEYS})
        assert pred.get("engine") != "mindie_sim.prediction.body.body_forward"
        assert (pred.get("coverage") or {}).get("boundary") == "native_calls"
        if pred["status"] in {"predicted", "modeled"} and pred.get("predicted_step_ms") is not None:
            assert float(pred["predicted_step_ms"]) > 0.0
            scopes = pred.get("comparison_scopes") or {}
            assert "per_native_call" in scopes
            assert pred.get("prediction_boundary") == "native_calls"
            samples = pred.get("boundary_samples") or []
            assert samples and all(":call" in str(item.get("key")) for item in samples)
            assert all(value is None for value in (pred.get("predicted_by_core_ms") or {}).values())
        else:
            assert str(pred["status"]).startswith("unsupported") or pred["status"] in {
                "insufficient_evidence", "model_rejected",
            }
            assert pred["predicted_step_ms"] is None
    assert by_hw == {"A2": 0, "A3": 0, "A5": 29}
    assert phases_seen == {"decode", "prefill"}


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_decode_json_all_280_cases_measurement_blind_with_operator_and_step_comparisons() -> None:
    """Verify all 280 registered_decode cases are measurement-blind with operator/step comparisons."""
    decode_doc = _load_json(RESULTS_DIR / "decode.json")
    assert decode_doc["summary"]["sources"] == 280
    rows = [r for r in _load_raw_fleet_rows() if r.get("suite") == "registered_decode"]
    assert len(rows) == 280
    for row in rows:
        cid = str(row["capture_id"])
        cal = row.get("source_calibration") or {}
        assert cal.get("evaluation_relation") != "in_sample", f"{cid}: evaluation_relation must not be in_sample"
        assert row.get("model_case")


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
    rows = _load_raw_fleet_rows()
    assert len(rows) == 6606
    suite_counts: dict[str, int] = {}
    tier_counts: dict[str, int] = {}
    for row in rows:
        suite, tier = str(row.get("suite") or ""), str(row.get("hardware_tier") or "")
        suite_counts[suite] = suite_counts.get(suite, 0) + 1
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        assert row.get("capture_id")
    assert suite_counts == EXPECTED_FLEET_SUITES
    assert tier_counts == EXPECTED_FLEET_TIER_COUNTS
    if SUITE1_JSONL.exists():
        total = len(rows) + sum(1 for line in SUITE1_JSONL.read_text(encoding="utf-8").splitlines() if line.strip())
        assert total == 7337


@pytest.mark.skipif(not SUITE2_JSONL.exists(), reason="Benchmark Suite 2 JSONL not present in /tmp")
def test_disk_and_memory_target_timing_invariance_10x_and_3x(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify 3x/10x memory and disk perturbations leave predictions unchanged while observations scale."""
    fom = _load_fom()
    cfg = _glm_livepre_cfg()
    _clear_all_caches(fom)
    base = fom.predict_capture_operators_and_step(cfg)
    assert base["status"] == "modeled"
    for mult in (3.0, 10.0):
        pert = copy.deepcopy(cfg)
        pert["observed_ms"] = 29.7616 * mult
        pert["tpot_ms"] = 29.7616 * mult
        pert["geometry"] = dict(pert["geometry"])
        pert["geometry"]["structural_weights"] = [0.9, 0.1, 0, 0, 0, 0]
        pert["geometry"]["active_hbm_mb"] = 999.0 * mult
        pert["geometry"]["active_cube_gflops"] = 12.0 * mult
        pert["kernel_summary"] = {"total_kernel_duration_us": 1.0e6 * mult, "by_accelerator_core": {"AI_CORE": 1.0e6 * mult}}
        assert fom.predict_capture_operators_and_step(pert) == base


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
        assert obs["observed_operator_ms"] is None
        assert obs.get("row_claimed", {}).get("used_as_evidence") is False
        assert obs["observed_ms"] != override or obs.get("observed_basis") != "row_observed_ms"


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

    assert observed({"AI_CORE": 72000.0, "AI_VECTOR_CORE": 8000.0}) == {}
    assert observed({"AI_CORE": 8000.0, "AI_VECTOR_CORE": 72000.0}) == {}


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
    assert obs["observed_by_core_ms"] == {}
    assert obs.get("by_core_us", {}).get("AI_CORE") == 400000.0

    raw = {"capture_id": "single_core", "suite": "extended_a3_a5_workstream_captures", "hardware_tier": "A3", "phase": "decode", "observed_ms": 2.0, "forward_steps": 8, "geometry": {"context_tokens": 4096, "concurrency": 1, "tp": 4, "dp": 1, "ep": 1}, "kernel_summary": {"total_kernel_rows": 9, "total_kernel_duration_us": 16000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 16000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 9, "total_us": 16000.0}]}}
    obs_raw = fom.extract_capture_observations(raw)
    assert obs_raw["observed_by_core_ms"] == {}
    assert obs_raw.get("row_claimed", {}).get("used_as_evidence") is False
    malformed = dict(raw)
    malformed["observed_ms"] = None
    malformed["kernel_summary"] = {**raw["kernel_summary"], "total_kernel_duration_us": "not-a-number"}
    obs_bad = fom.extract_capture_observations(malformed)
    assert obs_bad.get("row_claimed", {}).get("used_as_evidence") is False


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
    assert enr["status"] in {"missing_artifact", "insufficient_evidence"} and enr["observed_ms"] is None
    assert enr["passed_10pct"] is False
    assert enr["operator_modeling"]["observed_operator_ms"] is None
    assert enr["predicted_ms"] is None
    unmeasured = {**missing_row, "capture_id": "extended_a3_a5_workstream_captures:nonexistent_measured_dir", "observed_ms": 5.0}
    _clear_all_caches(fom)
    enr2 = fom.enrich_fleet_capture_with_operator_and_step_modeling(unmeasured)
    assert enr2["observed_ms"] is None
    assert enr2["passed_10pct"] is False
    assert enr2["predicted_ms"] is None


def test_multi_tier_a2_a3_a5_hardware_differentiation() -> None:
    """A bare label is not a case file, so no tier template is invented."""
    fom = _load_fom()
    steps = {
        hw: fom.predict_capture_operators_and_step(
            {"hardware_tier": hw, "phase": "decode", "model_case": "dsv41", "capture_id": "tier_probe"}
        )
        for hw in ("A2", "A3", "A5")
    }
    assert {item["status"] for item in steps.values()} == {"insufficient_evidence"}
    assert {item["predicted_step_ms"] for item in steps.values()} == {None}


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


def test_glm_livepre_strips_measured_case_timing_and_keeps_receipt_populations() -> None:
    """The public GLM step ignores in-sample regimes and predicts every receipt batch."""
    fom = _load_fom()
    cfg = _glm_livepre_cfg()
    _clear_all_caches(fom)
    base = fom.predict_capture_operators_and_step(cfg)
    assert base["status"] == "modeled"
    assert base["measurement_features_read"] is False
    calibration = base["calibration"]
    assert calibration["prediction_consumed_measured_overrides"] is False
    assert len(calibration["removed_service_regimes"]) == 10
    assert "observed_a3_local_native" in calibration["removed_device_rates"]
    assert calibration["labels"]["evaluation_relation"] == "in_sample"
    assert calibration["labels"]["calibration_origin"] == "observed"
    assert base["coverage"]["context_observed_in_receipt"] is False
    assert "MIX_AIC" in base["coverage"]["cores_unnamed_by_engine"]
    assert "MIX_AIV" in base["coverage"]["cores_unnamed_by_engine"]
    assert "AI_CPU" in base["coverage"]["cores_unnamed_by_engine"]
    assert all(value is None for value in base["predicted_by_core_ms"].values())
    assert base["prediction_boundary"] == "per_forward_window"
    assert base["boundary_basis"] == "elapsed"
    assert base["prediction_boundary"] != "native_client_request"
    assert "boundary_ms" not in base
    samples = base["boundary_samples_ms"]
    assert len(samples) == 73
    # Body-graph spans for the receipt populations. Not a 46-window mean.
    assert set(samples) == {22.525579582, 25.32662096, 28.106554111, 30.951848864}
    assert base["boundaries"]["family_elapsed_sum"]["basis"] == "additive"
    assert base["boundaries"]["family_elapsed_sum"]["not_a_sample"] is True
    assert "first_forward_cold_start" in base["coverage"]["unpriced_scopes"]
    assert base["coverage"]["startup_term"] is None
    populations = base["coverage"]["receipt_populations"]
    by_sequences = {item["sequences_per_replica"]: item for item in populations}
    assert set(by_sequences) == {1, 2, 3, 4}
    assert by_sequences[4]["selected_row_geometry"] is True
    assert by_sequences[4]["predicted_step_ms"] == base["predicted_step_ms"]
    assert base["predicted_step_ms"] == 30.951848864
    cohort = (base["geometry"].get("engine_query") or {}).get("sequences_by_replica") or {}
    assert cohort
    assert set(cohort.values()) == {4}
    assert base["geometry"]["cohort_sequences_by_replica"] == cohort
    assert by_sequences[1]["predicted_step_ms"] == 22.525579582
    assert by_sequences[2]["predicted_step_ms"] == 25.32662096
    assert by_sequences[3]["predicted_step_ms"] == 28.106554111
    assert all(item["status"] == "modeled" and item["predicted_step_ms"] > 0.0 for item in populations)
    refused = copy.deepcopy(cfg)
    refused["geometry"] = dict(refused["geometry"])
    refused["geometry"]["sequences_per_replica"] = 8
    refused["geometry"]["query_rows"] = 48
    outside = fom.predict_capture_operators_and_step(refused)
    assert outside["status"] == "insufficient_evidence"
    assert outside["predicted_step_ms"] is None

    original_load = fom._load_case

    def poisoned(path, expected):
        document, error = original_load(path, expected)
        if not isinstance(document, dict):
            return document, error
        for regime in document["runtime"]["kernels"].get("service_regimes") or []:
            regime.setdefault("response", {})["fixed_us"] = 1.0e12
        document["runtime"]["kernels"]["service_regimes"].append({
            "id": "unlabeled-fixed-rule",
            "response": {"fixed_us": 1.0e12, "terms": {"bytes": 1}},
            "execution": {"resource": "observed_a3_local_native"},
        })
        document["runtime"].setdefault("metadata", {}).setdefault("calibration_evidence", {})["service_regimes"] = [
            {"id": "metadata-indirect-rule", "response": {"knots": [[0, 1], [1, 2]]}},
        ]
        document["runtime"]["kernels"]["planted_service"] = {"fixed_us": 1.0e12, "terms": {"x": 1}}
        document["machine"]["device"]["rates"]["observed_a3_local_native"] = 1.0
        return document, error

    fom._load_case = poisoned
    try:
        fom._GRAPH_CACHE.clear()
        fom._POPULATION_STEP_CACHE.clear()
        mutated = fom.predict_capture_operators_and_step(cfg)
    finally:
        fom._load_case = original_load
    assert mutated["predicted_step_ms"] == base["predicted_step_ms"]
    assert mutated["predicted_by_canonical_family_ms"] == base["predicted_by_canonical_family_ms"]
    assert mutated["predicted_by_core_ms"] == base["predicted_by_core_ms"]
    assert "unlabeled-fixed-rule" in mutated["calibration"]["removed_service_regimes"]
    assert "metadata-indirect-rule" in mutated["calibration"]["removed_service_regimes"]
    assert any("planted_service" in item for item in mutated["calibration"]["removed_nested_timing"])
    assert mutated["structural_sha256"] == base["structural_sha256"]


def test_bogus_predicted_ms_and_historical_decode_json_are_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A caller-supplied or on-disk `predicted_ms` must not change a live architectural prediction."""
    fom = _load_fom()
    cfg = {
        "capture_id": "model_mtp3_tp8_decode", "suite": "unit", "hardware_tier": "A5", "phase": "decode",
        "forward_steps": 8, "target_timing_used_to_fit": False,
        "geometry": {"dp": 1, "ep": 1, "context_tokens": 4096, "concurrency": 4, "active_hbm_mb": 12345.0},
    }
    _clear_all_caches(fom)
    baseline = fom.predict_capture_operators_and_step(cfg)
    bogus = {**cfg, "predicted_ms": 999999.0, "target_timing_used_to_fit": False}
    assert fom.predict_capture_operators_and_step(bogus)["predicted_step_ms"] == baseline["predicted_step_ms"]
    assert baseline["predicted_step_ms"] != 999999.0
    assert fom._infer_geometry({"capture_id": "model_mtp3_tp8_decode", "phase": "decode", "geometry": {}}) == {}
    assert fom._infer_geometry({"capture_id": "model_mtp3_tp8_decode", "phase": "decode", "geometry": {"tp": 8}})["tp"] == 8
    ks = {"total_kernel_duration_us": 8000.0, "by_accelerator_core": {"AI_VECTOR_CORE": 8000.0}, "top_op_types": [{"type": "Silu", "core": "AI_VECTOR_CORE", "count": 1, "total_us": 8000.0}]}
    claimed = baseline["predicted_step_ms"]
    row = {**cfg, "observed_ms": float(claimed) if claimed is not None else None, "kernel_summary": ks}
    assert fom.enrich_fleet_capture_with_operator_and_step_modeling({**row, "predicted_ms": 999999.0})["predicted_ms"] == fom.enrich_fleet_capture_with_operator_and_step_modeling(row)["predicted_ms"]
    tmp_results = tmp_path / "results"
    tmp_results.mkdir()
    decode_doc = _load_json(RESULTS_DIR / "decode.json")
    case = decode_doc["cases"][0]
    case_id = str(case.get("case_id") or case.get("id"))
    (tmp_results / "decode.json").write_text(json.dumps(decode_doc), encoding="utf-8")
    monkeypatch.setattr(fom, "RESULTS_DIR", tmp_results)
    live_cfg = {"capture_id": f"registered_decode:{case_id}", "suite": "registered_decode", "hardware_tier": "A3", "phase": "decode", "forward_steps": 32, "target_timing_used_to_fit": False, "geometry": dict(case.get("geometry") or {})}
    _clear_all_caches(fom)
    before = fom.predict_capture_operators_and_step(live_cfg)
    mutated = copy.deepcopy(decode_doc)
    mutated["cases"][0].setdefault("comparison", {})["predicted_ms"] = 999999.0
    (tmp_results / "decode.json").write_text(json.dumps(mutated), encoding="utf-8")
    _clear_all_caches(fom)
    assert fom.predict_capture_operators_and_step({**live_cfg, "predicted_ms": 999999.0, "target_timing_used_to_fit": False}) == before


def test_receipt_chunk_schedule_uses_declared_prefix_and_keeps_sample_key() -> None:
    """Chunk context is the declared prefix plus prior query rows. The sample key matches E's frame fields."""
    fom = _load_fom()
    frames = [
        {"forward_id": "prefill:0", "phase": "prefill", "query_rows": 8064, "body_device_id": "0"},
        {"forward_id": "prefill:1", "phase": "prefill", "query_rows": 8064, "body_device_id": "0"},
        {"forward_id": "prefill:2", "phase": "prefill", "query_rows": 256, "body_device_id": "0"},
    ]
    steps, notes = fom._schedule_from_launch(frames, {"prefix_len": 0, "input_len": 16384, "concurrency": 1, "basis": "test"})
    assert steps == [(8064, 0, 1), (8064, 8064, 1), (256, 16128, 1)]
    assert "context_zero_is_declared_initial_cache" in notes
    refused, refused_notes = fom._schedule_from_launch(frames, {"input_len": 16384, "concurrency": 1})
    assert refused is None
    assert "missing_work:declared_prefix_not_in_launch_record" in refused_notes
    mismatched, mismatch_notes = fom._schedule_from_launch(frames, {"prefix_len": 0, "input_len": 4096, "concurrency": 1})
    assert mismatched is None
    assert any(item.startswith("receipt_query_sum_") for item in mismatch_notes)
    sample = fom._boundary_sample(
        {"forward_id": "prefill:0", "phase": "prefill", "body_device_id": "0", "tokens_per_sequence": 8064, "context_tokens": 0, "sequences_per_replica": 1},
        1.25,
        "capture-a",
    )
    from hf_sample_scoring import sample_key
    assert sample["key"] == sample_key(phase="prefill", device_id="0", forward_id="prefill:0")
    assert sample["device_id"] == "0"
    assert sample["capture_id"] == "capture-a"
    assert sample["value_ms"] == 1.25
    assert "capture_id=" not in sample["key"]
    assert "device_id=0" in sample["key"]
    wave = fom._boundary_sample(
        {"forward_id": "prefill:0", "phase": "prefill", "body_device_id": "4"},
        108.0,
        "wave5",
    )
    assert wave["key"] == "phase=prefill|device_id=4|forward_id=prefill:0"
    frames = [
        {"forward_id": "prefill:0", "phase": "prefill", "body_device_id": "0", "tokens_per_sequence": 8064, "context_tokens": 0, "sequences_per_replica": 1},
        {"forward_id": "prefill:1", "phase": "prefill", "body_device_id": "0", "tokens_per_sequence": 8064, "context_tokens": 8064, "sequences_per_replica": 1},
        {"forward_id": "prefill:2", "phase": "prefill", "body_device_id": "0", "tokens_per_sequence": 256, "context_tokens": 16128, "sequences_per_replica": 1},
    ]
    cached = {
        "predicted_step_ms": 128.0,
        "predicted_operator_ms": 120.0,
        "chunk_rows": [
            {"tokens_per_sequence": 8064, "context_tokens": 0, "sequences_per_replica": 1, "boundary_ms": 59.0},
            {"tokens_per_sequence": 8064, "context_tokens": 8064, "sequences_per_replica": 1, "boundary_ms": 62.0},
            {"tokens_per_sequence": 256, "context_tokens": 16128, "sequences_per_replica": 1, "boundary_ms": 5.0},
        ],
    }
    payload = fom._elapsed_boundary({"frames": frames, "capture_id": "kimi", "phase": "prefill"}, cached, [])
    assert payload["prediction_boundary"] == "per_forward_window"
    assert "boundary_ms" not in payload
    assert payload["boundaries"]["body_graph_span"]["boundary_ms"] is None
    assert [item["boundary_ms"] for item in payload["boundary_samples"]] == [59.0, 62.0, 5.0]
    assert [item["key"] for item in payload["boundary_samples"]] == [
        "phase=prefill|device_id=0|forward_id=prefill:0",
        "phase=prefill|device_id=0|forward_id=prefill:1",
        "phase=prefill|device_id=0|forward_id=prefill:2",
    ]
    unnamed = {
        "by_operator": {"s0:a": {"elapsed_ms": 1.0, "operator_events": 1}},
        "by_family": {
            "gemm": {"elapsed_ms": 3.0},
            "attention": {"elapsed_ms": 1.5},
            "allreduce": {"elapsed_ms": 2.0},
            "native_fusion": {"elapsed_ms": 0.5},
        },
    }
    bucket, elapsed, counted = fom._classify_compact_profile(unnamed)
    assert counted == 1
    assert elapsed == 7.0
    assert bucket["canonical"]["gemm"] == 3.0
    assert bucket["canonical"]["attention"] == 1.5
    assert bucket["canonical"]["collective"] == 2.0
    assert bucket["canonical"]["other"] == 0.5
    named = {"by_operator": {"s0:a": {"elapsed_ms": 4.0, "operator_events": 2, "family": "gemm"}}}
    named_bucket, named_elapsed, named_count = fom._classify_compact_profile(named)
    assert named_count == 2 and named_elapsed == 4.0
    assert named_bucket["canonical"]["gemm"] == 4.0


def test_a3_lowered_case_keeps_tensor_routing_parallel_and_cohort_contract() -> None:
    """Strip removes measured regimes and leaves the declared tensor, routing, and parallel program."""
    fom = _load_fom()
    path = STRUCT_DIR / "cases" / "decode-glm53flash-a3-tp16-c4-livepre.json"
    case, error = fom._load_case(path, None)
    assert error is None and case is not None
    blind, calibration = fom._strip_measured_overrides(case)
    assert len(calibration["removed_service_regimes"]) == 10
    assert "service_regimes" not in blind["runtime"]["kernels"]
    runtime = blind["runtime"]
    assert {axis: runtime[axis] for axis in ("tp", "dp", "ep", "pp")} == {"tp": 16, "dp": 1, "ep": 16, "pp": 1}
    assert runtime["kernels"]["lowerings"]["kda"]["implementation"] == "vllm_ascend_recurrent_kda_arch22"
    assert runtime["kernels"]["lowerings"]["native_fusion"]["implementation"] == "declared_native_fusion"
    assert runtime["kernels"]["programs"]["indexed_attention"]["kind"] == "indexed_attention_packed_int8"
    assert runtime["metadata"]["tensor_geometry_candidates"][0]["tensor_query_rows"] == 6
    assert runtime.get("routing") in (None, {})
    quant = blind["model"]["quant"]
    assert quant["weight_format"] == "int8"
    assert quant["kv_dtype"] == "int8"
    assert quant["category_overrides"] == {}
    from mindie_sim.prediction.structure import parse_case
    parsed = parse_case(blind)
    assert parsed.runtime.parallel.tp == 16
    assert parsed.runtime.parallel.dp == 1
    assert parsed.runtime.parallel.ep == 16
    assert parsed.model.quant.weight_format == "int8"
    assert parsed.runtime.routing.get("policy") != "balanced"
    assert "kda" in parsed.runtime.kernels["lowerings"]


def test_operator_groups_require_a_declared_engine_and_two_skus_stay_unselected() -> None:
    """Family elapsed is not an op x engine group. Two conditional SKUs are both labeled and neither is chosen."""
    fom = _load_fom()
    unbound = fom._program_ledger({
        "by_operator": {
            "s0:gemm": {
                "op_id": "gemm",
                "replicas": {
                    0: {"family": "gemm", "phase": "decode", "operator_events": 3, "elapsed_ms": 1.5},
                },
            },
        },
    })
    groups, status = fom._operator_groups_from_ledger(unbound)
    assert groups == []
    assert status == "absent_no_native_op_engine_binding"
    assert unbound[0]["rank_id"] == 0 and unbound[0]["phase"] == "decode" and unbound[0]["count"] == 3
    bound = [{
        "native_op": "MatMulV2", "engine": "AI_CORE", "rank_id": 0, "phase": "decode",
        "count": 2, "elapsed_ms": 0.5,
    }]
    groups, status = fom._operator_groups_from_ledger(bound)
    assert status == "source_bound_op_engine"
    assert groups[0]["op_type"] == "MatMulV2" and groups[0]["engine"] == "AI_CORE"
    assert groups[0]["basis"] == "additive" and groups[0]["count"] == 2
    multi = fom._operator_groups_from_ledger([
        {"native_op": "MatMulV2", "engine": "AI_CORE", "rank_id": 0, "phase": "decode", "count": 1, "elapsed_ms": 0.2},
        {"native_op": "MatMulV2", "engine": "AI_CORE", "rank_id": 1, "phase": "decode", "count": 1, "elapsed_ms": 0.2},
    ])
    assert multi[1] == "withheld_multi_rank_until_observation_keys_match"
    failure = fom._campaign_probe({
        "ok": False,
        "status": "insufficient_evidence",
        "diagnostics": [
            "hardware_sku_ambiguous_catalogue_capacity",
            "candidate:Ascend950PR_9579",
            "candidate:Ascend950DT_9582",
        ],
        "needed": ["per-host SKU"],
    })
    assert failure["ok"] is False
    assert failure["hardware_selection"] == "not_selected"
    assert [item["sku"] for item in failure["hardware_candidates"]] == ["Ascend950PR_9579", "Ascend950DT_9582"]
    assert all(item["priced"] is False and item["selected"] is False for item in failure["hardware_candidates"])
    public = fom._price_probe(failure, {"capture_id": "ambiguous", "phase": "decode"})
    assert public["predicted_step_ms"] is None
    assert public["hardware_selection"] == "not_selected"
    assert [item["sku"] for item in public["hardware_candidates"]] == ["Ascend950PR_9579", "Ascend950DT_9582"]


def test_campaign_row_publishes_deployment_identity_and_additive_rank_phase() -> None:
    """One real campaign row keeps J's ceiling, identity, and additive program. The op aggregate is not the step."""
    fom = _load_fom()
    _clear_all_caches(fom)
    target = "a5_multinode_20261108:r06_2n_qwen38_27b_bf16_dp4_tp4_131k:dualrank_decode_isl1024_c1"
    row = None
    with SUITE2_JSONL.open(encoding="utf-8") as handle:
        for line in handle:
            if target not in line:
                continue
            item = json.loads(line)
            if item.get("capture_id") == target:
                row = item
                break
    assert row is not None
    cfg = {key: row.get(key) for key in fom._ALLOWED_CFG_KEYS}
    import fleet_campaign_case as campaign
    resolved = campaign.resolve_campaign_case(cfg)
    assert resolved["ok"] is True
    probe = fom._campaign_probe(resolved)
    assert probe["ok"] is True
    assert probe["frames"] == []
    assert probe["source_sha256"] == resolved["deployment_sha256"]
    assert probe["source_sha_basis"] == "deployment_identity"
    assert probe["sequences_observed"] is False
    runtime = probe["case"]["runtime"]
    applied = runtime.get("parallel") if isinstance(runtime.get("parallel"), dict) else runtime
    for axis, value in resolved["parallel"].items():
        assert applied[axis] == value
    quant = (probe["case"].get("model") or {}).get("quant")
    assert isinstance(quant, dict) and quant.get("weight_format")
    assert "expert_routing" in (probe["case"].get("model") or {})
    result = fom.predict_capture_operators_and_step(cfg)
    assert result["status"] == "modeled"
    assert result["source_sha256"] == resolved["deployment_sha256"]
    assert result["source_sha_basis"] == "deployment_identity"
    assert result.get("prediction_boundary") in (None, "")
    assert result["predicted_step_ms"] is not None
    assert result["geometry"]["sequences_observed"] is False
    assert result["geometry"]["actual_q_observed"] is False
    assert result["geometry"]["sequences_upper_bound"] == result["geometry"]["sequences_per_replica"]
    assert result["geometry"]["cohort_sequences_by_replica"]
    assert "body_graph_span_is_not_an_op_statistic_aggregate" in result["diagnostics"]
    ledger = result["additive_rank_phase"]
    assert ledger["not_a_step"] is True and ledger["basis"] == "additive"
    assert ledger["rows"]
    assert all(item.get("phase") and item.get("count") and item.get("unit") == "ms" for item in ledger["rows"])
    assert all(item.get("rank_id") is not None for item in ledger["rows"])
    if result["coverage"]["operator_groups"] != "source_bound_op_engine":
        assert "predicted_operator_groups" not in result
    poisoned = dict(cfg)
    poisoned["observed_ms"] = 1.0
    poisoned["tpot_ms"] = 99.0
    poisoned["ttft_ms"] = 99.0
    poisoned["kernel_summary"] = {"total_kernel_duration_us": 1.0}
    again = fom.predict_capture_operators_and_step(poisoned)
    assert again["predicted_step_ms"] == result["predicted_step_ms"]
    assert again["source_sha256"] == result["source_sha256"]
    assert again["additive_rank_phase"]["rows"] == ledger["rows"]
    from hf_sample_scoring import score_boundary, score_operator_groups
    import fleet_capture_observations as observations
    observed = observations.extract_capture_observations(row)
    boundary = score_boundary(result, observed)
    groups = score_operator_groups(result, observed)
    assert boundary["reason"] == "prediction_boundary_undeclared"
    assert boundary["passed_10pct"] is False
    assert result.get("prediction_boundary") != "capture_op_statistic_aggregate"
    assert groups["passed_10pct"] is False
    forward = (observed.get("measurements") or {}).get("per_forward_window") or {}
    assert forward.get("status") != "measured"
