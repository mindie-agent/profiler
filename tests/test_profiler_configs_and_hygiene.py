"""Contract tests for typed profiler configuration schemas and module hygiene."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys

import pytest

from mindie_profiler import (
    ACLGraphLaunchConfig,
    AdvisorConfig,
    CorrelationConfig,
    FusionRuleConfig,
    MemoryForensicsConfig,
    SimBridgeBottleneckPolicy,
    StructuralInferenceConfig,
    effective_launch_floor_us,
    evaluate_advisor_rules,
    infer_trace_structure,
    run_memory_forensics,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PKG_ROOT = REPO_ROOT / "mindie_profiler"


def test_typed_configs_enforce_immutability_and_type_bounds() -> None:
    cfg = CorrelationConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.max_rows = 10  # type: ignore[misc]

    with pytest.raises(ValueError, match="must be int"):
        CorrelationConfig(max_rows=True)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="must be finite"):
        AdvisorConfig(cast_storm_share_ratio=float("nan"))

    with pytest.raises(ValueError, match="gc_high_severity_us"):
        AdvisorConfig(gc_gap_us=25_000, gc_high_severity_us=20_000)

    with pytest.raises(ValueError, match="max_savings_ratio"):
        FusionRuleConfig(min_savings_ratio=0.7, max_savings_ratio=0.4)

    with pytest.raises(ValueError, match="high_fragmentation_ratio"):
        MemoryForensicsConfig(high_fragmentation_ratio=0.04, moderate_fragmentation_ratio=0.10)

    assert StructuralInferenceConfig().candidate_step_upper_bound == 255
    assert SimBridgeBottleneckPolicy().comm_share_ratio == pytest.approx(0.35)


def test_typed_configs_thread_into_diagnostic_entrypoints() -> None:
    acl_cfg = ACLGraphLaunchConfig(
        superkernel_us=0.40,
        full_graph_us=1.50,
        piecewise_graph_us=1.90,
        eager_us=6.25,
    )
    assert effective_launch_floor_us("full", config=acl_cfg) == pytest.approx(1.50)
    assert effective_launch_floor_us("piecewise", config=acl_cfg) == pytest.approx(1.90)
    assert effective_launch_floor_us("none", config=acl_cfg) == pytest.approx(6.25)
    assert effective_launch_floor_us("full", superkernel=True, config=acl_cfg) == pytest.approx(0.40)

    adv_res = evaluate_advisor_rules(events=[], config=AdvisorConfig())
    assert adv_res["schema_version"] == "mindie-profile-advisor/1"

    mem_res = run_memory_forensics(config=MemoryForensicsConfig())
    assert mem_res["schema_version"] == "mindie-memory-forensics/1"

    inf_res = infer_trace_structure([], config=StructuralInferenceConfig())
    assert inf_res.schema_version == "mindie-structural-inference/1"


def test_production_modules_cohesion_headers_lf_and_magic_gate_clean() -> None:
    py_files = sorted(PKG_ROOT.rglob("*.py"))
    assert len(py_files) >= 140
    required_tags = ("[Role]", "[Invariants]", "[Timeouts & Locks]", "[Side-Effect Policy]")
    for path in py_files:
        raw = path.read_bytes()
        assert b"\r" not in raw, f"CR byte in {path.name}"
        lines = raw.decode("utf-8").splitlines()
        if len(lines) >= 800:
            header = "\n".join(lines[:30])
            missing = [tag for tag in required_tags if tag not in header]
            assert not missing, f"{path.name} ({len(lines)} lines) missing top-30-line contract header tags: {missing}"

    proc = subprocess.run(
        [
            sys.executable,
            "-B",
            str(REPO_ROOT / "scripts" / "check_no_magic_numbers.py"),
            "--root",
            f"profiler={PKG_ROOT}",
            "--baseline",
            str(REPO_ROOT / "scripts" / "magic_number_baseline.json"),
            "--exceptions",
            str(REPO_ROOT / "scripts" / "magic_number_exceptions.json"),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
