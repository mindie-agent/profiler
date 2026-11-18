"""Tier-1 closed-loop product acceptance for profiler <-> mindie-sim.

[Role] Exercise the shipped CLI/MCP product path end to end: 37-model catalog
  parity, 15-SKU hardware presets, A3 8-rank DB ``--auto-step`` analysis, DB-only
  ``export-sim-case``, A5 QSMLA/FP4/HiF8/mHC contracts, bidirectional structure
  ingress, advisor commands, and the big-trace speed guards.
[Invariants] No test initializes a device context or imports torch_npu; all
  timings are explicit and every negative control asserts a fail-closed error.
[Timeouts & Locks] Each fixture and command is bounded; no sleeps or live NPU.
[Side-Effect Policy] Writes only under pytest tmp_path.
"""
from __future__ import annotations

import json
import os
import sqlite3
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mindie_profiler import __version__  # noqa: E402
from mindie_profiler.events import ProfilerUsageError  # noqa: E402

pytestmark = pytest.mark.skipif(
    bool(os.environ.get("ASCEND_RT_VISIBLE_DEVICES")), reason="offline CPU acceptance only")


# --------------------------------------------------------------------------- #
# Synthetic torch_npu SQLite exports
# --------------------------------------------------------------------------- #
_TASK_COLUMNS = (
    "globalTaskId", "startNs", "endNs", "deviceId", "streamId", "taskId",
    "modelId", "contextId", "taskType", "connectionId",
)


def _create_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE STRING_IDS(id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE TASK(globalTaskId INTEGER, startNs INTEGER, endNs INTEGER,
                          deviceId INTEGER, streamId INTEGER, taskId INTEGER,
                          modelId INTEGER, contextId INTEGER, taskType INTEGER,
                          connectionId INTEGER);
        CREATE TABLE COMPUTE_TASK_INFO(name INTEGER, globalTaskId INTEGER PRIMARY KEY,
                          blockDim INTEGER, mixBlockDim INTEGER, taskType INTEGER,
                          opType INTEGER, inputShapes INTEGER, inputDataTypes INTEGER,
                          inputFormats INTEGER, outputShapes INTEGER, outputDataTypes INTEGER,
                          outputFormats INTEGER, opState INTEGER, waitNs INTEGER);
        CREATE TABLE TASK_PMU_INFO(globalTaskId INTEGER, name INTEGER, value NUMERIC);
        CREATE TABLE STEP_TIME(id INTEGER, startNs INTEGER, endNs INTEGER);
        CREATE TABLE NPU_INFO(id INTEGER, name TEXT);
        CREATE TABLE RANK_DEVICE_MAP(rankId INTEGER, deviceId INTEGER);
        CREATE TABLE META_DATA(name TEXT, value TEXT);
        """
    )
    con.execute("INSERT INTO META_DATA VALUES ('SCHEMA_VERSION', '1.2.0')")


class _Ids:
    def __init__(self, con: sqlite3.Connection) -> None:
        self.con = con
        self.cache: dict[str, int] = {}

    def __call__(self, value: str | None) -> int | None:
        if value is None:
            return None
        if value not in self.cache:
            self.cache[value] = len(self.cache) + 1
            self.con.execute("INSERT INTO STRING_IDS VALUES (?,?)", (self.cache[value], value))
        return self.cache[value]


_KERNELS = (
    ("RecurrentGatedDeltaRule", "RecurrentGatedDeltaRule", "AI_CORE", "[2, 16, 128]",
     "DT_BF16", "ND", "[2, 16, 128]", "DT_BF16", "ND"),
    ("QuantGroupMatmul", "QuantGroupMatmul", "AI_CORE", "[128, 512];[512, 256]",
     "DT_INT8;DT_INT8", "ND;ND", "[128, 256]", "DT_BF16", "ND"),
    ("FusedInferAttentionScore", "FusedInferAttentionScore", "AI_CORE",
     "[2, 16, 8, 128]", "DT_BF16", "ND", "[2, 16, 8, 128]", "DT_BF16", "ND"),
    ("MoeInitRoutingV3", "MoeInitRoutingV3", "AI_VECTOR_CORE", "[256, 64]",
     "DT_BF16", "ND", "[256, 8]", "DT_INT32", "ND"),
    ("MoeDistributeDispatchV2", "MoeDistributeDispatchV2", "COMMUNICATION",
     "[256, 64]", "DT_BF16", "ND", "[256, 64]", "DT_BF16", "ND"),
    ("MoeDistributeCombineV2", "MoeDistributeCombineV2", "COMMUNICATION",
     "[256, 64]", "DT_BF16", "ND", "[256, 64]", "DT_BF16", "ND"),
    ("MatMulV2", "MatMulV2", "AI_CORE", "[128, 512];[512, 256]",
     "DT_BF16;DT_BF16", "ND;ND", "[128, 256]", "DT_BF16", "ND"),
)


def _build_rank_db(
    path: Path, *, rank: int, steady_ms: float = 12.5, warmup_ms: float = 45.0,
    steps: int = 5, npu: str = "Ascend910_9392",
    kernels: tuple = _KERNELS, pmu_per_task: int = 2,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    try:
        _create_schema(con)
        sid = _Ids(con)
        con.execute("INSERT INTO NPU_INFO VALUES (1, ?)", (npu,))
        con.execute("INSERT INTO RANK_DEVICE_MAP VALUES (?, ?)", (rank, rank))
        global_id = 1
        base = 1_000_000_000 + rank * 777_777
        for step in range(steps):
            span_ns = int((warmup_ms if step == 0 else steady_ms) * 1_000_000)
            start_ns = base + step * 60_000_000
            end_ns = start_ns + span_ns
            con.execute("INSERT INTO STEP_TIME VALUES (?,?,?)", (step, start_ns, end_ns))
            core_offset = 0
            for name, op_type, core, in_shapes, in_dtypes, in_formats, out_shapes, out_dtypes, out_formats in kernels:
                duration = 2_000_000 if name == "MatMulV2" else 900_000
                task_start = start_ns + 100_000 + core_offset
                core_offset += duration + 20_000
                if task_start + duration > end_ns:
                    task_start = start_ns + 100_000
                con.execute(
                    "INSERT INTO TASK VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (global_id, task_start, task_start + duration, rank,
                     step % 2, global_id, 0, 0, sid(core), None),
                )
                con.execute(
                    "INSERT INTO COMPUTE_TASK_INFO VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (sid(name), global_id, 20, 0, sid(core), sid(op_type),
                     sid(in_shapes), sid(in_dtypes), sid(in_formats),
                     sid(out_shapes), sid(out_dtypes), sid(out_formats),
                     sid("dynamic"), 0),
                )
                for metric in range(pmu_per_task):
                    con.execute(
                        "INSERT INTO TASK_PMU_INFO VALUES (?,?,?)",
                        (global_id, sid(f"aic_mac_time" if metric == 0 else "aic_mac_ratio"),
                         1000.0 + metric),
                    )
                global_id += 1
        con.commit()
    finally:
        con.close()
    return path


def _eight_rank_capture(tmp_path: Path) -> Path:
    root = tmp_path / "capture_a3"
    for rank in range(8):
        _build_rank_db(root / f"rank_{rank}" / "profiler" / "ascend_pytorch_profiler_0.db",
                       rank=rank)
    return root


def _cli(*argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(REPO_ROOT), env.get("PYTHONPATH", "")]).strip(os.pathsep)
    env["TORCH_DEVICE_BACKEND_AUTOLOAD"] = "0"
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["ASCEND_RT_VISIBLE_DEVICES"] = ""
    return subprocess.run(
        [sys.executable, "-m", "mindie_profiler", *argv],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=300,
    )


# --------------------------------------------------------------------------- #
# 1. Catalog / SKU parity
# --------------------------------------------------------------------------- #
def test_catalog_parity_37_models_and_skus_zero_silent_rewrite() -> None:
    from mindie_sim.backends.ascend import profiles
    from mindie_sim.model_catalog import CATALOG

    from mindie_profiler import sim_bridge_catalog as catalog

    assert len(CATALOG) >= 37
    # The bridge owns no model geometry mirror: every catalog key and alias is
    # resolved live, and a legacy preset key still resolves to itself.
    for model in CATALOG:
        assert catalog.resolve_sim_model_key(model) == model
    for model in ("kimi-k2", "kimi-k3.1", "qwen3.5-27b", "qwen3.6-35b-a3b",
                  "minimax-m3.1-flash", "deepseek-v4.1-flash",
                  "qwen3.8-flash-next", "step-5-preview"):
        assert catalog.resolve_sim_model_key(model) == model
    for legacy in ("bailing-v3", "hunyuan-video-dit", "longcat-flash-lite", "qwen3.5-moe"):
        assert catalog.resolve_sim_model_key(legacy) == legacy
    assert catalog.resolve_sim_model_key("deepseek-v4-flash") == "deepseek-v4-flash-0731"
    assert catalog.resolve_sim_model_key("qwen3-30b") == "qwen3-30b-a3b"
    assert catalog.resolve_sim_model_key("qwen3.8-2.4t") == "qwen3.8-2.4t-a95b"
    assert catalog.resolve_sim_model_key("qwen36") == "qwen3.6-27b"
    with pytest.raises(catalog.ProfilerUsageError, match="unsupported or unrecognized model"):
        catalog.resolve_sim_model_key("Qwen3-8B")

    supported = tuple(sorted(profiles()))
    assert len(supported) == 16
    assert "Ascend950PR_958b" in supported
    assert catalog.supported_hardware_skus() == supported
    for sku in supported:
        assert catalog._resolve_hw_token(sku) == sku
    for alias in ("a2", "a3", "a5", "950pr", "910_9599"):
        assert catalog._resolve_hw_token(alias)
    for quant in ("bf16", "w8a8", "w8a8_dynamic", "w8a8c8", "w8a16", "w4a16",
                  "w4a8", "w4a8_dynamic", "mxfp8", "w8a8_mxfp8", "hif8",
                  "hifloat8", "mxfp4", "fp4", "fp4_e2m1", "w4a4",
                  "w4a4_mxfp4", "w4a8_mxfp4", "w4a4c8"):
        assert catalog._normalize_quant(quant) is not None, quant


def test_hardware_presets_cover_exactly_the_public_profiles() -> None:
    from mindie_sim.backends.ascend import profiles

    from mindie_profiler.hardware_presets import (
        SUPPORTED_SKUS, resolve_chip_topology, resolve_hardware_preset,
    )

    live_profiles = profiles()
    assert tuple(sorted(SUPPORTED_SKUS)) == tuple(sorted(live_profiles))
    for sku, prof in live_profiles.items():
        topology = resolve_chip_topology(sku)
        assert topology.sku == sku and topology.aic_cores > 0 and topology.aiv_cores > 0
        declared = tuple((prof.get("device") or {}).get("compute_peaks") or ())
        assert set(topology.cube_tflops_by_dtype) == set(declared)
        for dtype in declared:
            spec = resolve_hardware_preset(sku, dtype=dtype)
            assert spec.peak_flops_per_s > 0 and spec.memory_bandwidth_bytes_per_s > 0
    with pytest.raises(ProfilerUsageError, match="hardware_compute_dtype_unsupported"):
        resolve_hardware_preset("Ascend910_9392", dtype="fp8_e4m3")
    with pytest.raises(ProfilerUsageError):
        resolve_hardware_preset("Ascend950PR_9581")


# --------------------------------------------------------------------------- #
# 2. A3 8-rank SQLite default CLI closed loop
# --------------------------------------------------------------------------- #
def test_a3_8rank_sqlite_default_cli_closed_loop(tmp_path: Path) -> None:
    root = _eight_rank_capture(tmp_path)

    inventory = _cli("inventory", "--root", str(root), "--jobs", "4")
    assert inventory.returncode == 0, inventory.stderr
    payload = json.loads(inventory.stdout)
    assert payload["rank_count"] == 8
    assert payload["detected_hardware_sku"] == "Ascend910_9392"
    for rank in payload["ranks"]:
        assert [item["step"] for item in rank["native_step_windows"]] == [0, 1, 2, 3, 4]

    missing = _cli("analyze", "--root", str(root))
    assert missing.returncode != 0
    assert "explicit" in missing.stderr
    assert "--auto-step" in missing.stderr and "--step-window" in missing.stderr

    summary_path = tmp_path / "summary.json"
    analyzed = _cli("analyze", "--root", str(root), "--auto-step", "--jobs", "4",
                    "--hardware", "a3", "--output", str(summary_path))
    assert analyzed.returncode == 0, analyzed.stderr
    report = json.loads(summary_path.read_text())
    assert report["step_accounting"]["steady_steps"] == [1, 2, 3, 4]
    assert report["window_provenance"]["selection_basis"] == "native_step_auto_steady"
    assert report["window_provenance"]["warmup_excluded_steps"] == [0]
    blocks = {row["block"]: row for row in report["semantic_block_breakdown"]}
    assert blocks["Attention"]["event_count"] > 0
    assert blocks["MoE"]["event_count"] > 0
    assert "modeling_not_run" not in {item["code"] for item in report["limitations"]}
    modeling = report["enrichment"]["modeling"]
    assert modeling["hotspots_modeled"] > 0
    assert modeling["model_inputs_supplied"] is True

    case_path = tmp_path / "case.json"
    exported = _cli(
        "export-sim-case", str(root), "--rank", "auto",
        "--model", "qwen3.5-35b-a3b", "--hardware", "a3", "--tp", "8",
        "--phase", "decode", "--concurrency", "32", "--prompt-tokens", "4096",
        "--output-tokens", "128", "--max-num-seqs", "32",
        "--max-num-batched-tokens", "32", "--max-model-len", "8192",
        "--kv-block-size", "128", "--enable-chunked-prefill",
        "--output", str(case_path))
    assert exported.returncode == 0, exported.stderr
    case = json.loads(case_path.read_text())
    observed = case["runtime"]["metadata"]["observed_profile"]
    assert observed["step_time_ms"] == pytest.approx(12.5)
    assert case["runtime"]["metadata"]["profiler_provenance"]["rank_selection"]["selected_rank"] == "rank_0"
    import mindie_sim.cli as sim_cli

    # Body-scope prediction prices the same production Case without replaying
    # the full 32x4096 serving horizon (kept inside the Tier-1 budget).
    assert sim_cli.main([
        "predict", str(case_path), "--scope", "body", "--phase", "decode",
        "--tokens", "1", "--sequences", "2", "--context", "4096"]) == 0
    assert sim_cli.main([
        "efficiency", str(case_path), "--phase", "decode", "--tokens", "1",
        "--sequences", "2", "--context", "4096"]) == 0


# --------------------------------------------------------------------------- #
# 3. A5 QSMLA / FP4 / HiF8 / mHC operator + structure loop
# --------------------------------------------------------------------------- #
def test_mqsmla_descriptor_projection_and_fp4_hif8_math() -> None:
    from types import SimpleNamespace

    from mindie_profiler.body_attention_contracts import observed_attention_contract
    from mindie_profiler.measured_supply import _nz_matches, derive_measured_supply
    from mindie_profiler.modeling_inputs import HardwareSpec, KernelInputs

    def row(kind, inputs, outputs):
        return SimpleNamespace(
            kind=kind,
            input_shapes=tuple(item[0] for item in inputs),
            input_dtypes=tuple(item[1] for item in inputs),
            input_formats=tuple(item[2] for item in inputs),
            output_shapes=tuple(item[0] for item in outputs),
            output_dtypes=tuple(item[1] for item in outputs),
            output_formats=tuple(item[2] for item in outputs),
        )

    query = ((2, 16, 512), "bf16", "ND")
    original = ((2, 16, 1, 544), "uint8", "ND")
    output = ((2, 16, 512), "bf16", "ND")
    indices = ((2, 16), "int32", "ND")
    filler = ((1,), "int32", "ND")
    compressed = ((2, 16, 1, 320), "uint8", "ND")
    expected = (
        "sparse_attention_active", "MqsmlaKernel___call__", (query,),
        (((1, 544), "uint8", "ND"), ((), None, None)), output)
    row_original = row(
        "MqsmlaKernel___call__",
        [query, ((2, 1, 1, 1), "bf16", "ND"), original, indices,
         filler, filler, filler], [output])
    assert observed_attention_contract(row_original) == expected
    row_compressed = row(
        "MqsmlaKernel",
        [query, ((2, 1, 1, 1), "bf16", "ND"), original, indices,
         filler, filler, filler, compressed, indices, filler], [output])
    assert observed_attention_contract(row_compressed) == (
        "sparse_attention_active", "MqsmlaKernel___call__", (query,),
        (((1, 544), "uint8", "ND"), ((1, 320), "uint8", "ND")), output)
    # Descriptor-free retained rows must stay unmatched, never fabricated.
    descriptor_free = row("MqsmlaKernel", [((), "N/A", "N/A")], [((), "N/A", "N/A")])
    assert observed_attention_contract(descriptor_free) is None

    hw = HardwareSpec("Ascend950DT_9582", 1.0e15, 4.0e12)
    assert KernelInputs(shape=(1, 1, 1), dtype="fp4_e2m1", layout="ND",
                        hardware=hw, op_kind="matmul").workload()[1] == 3.0
    assert KernelInputs(shape=(1,), dtype="fp4_e2m1", layout="ND",
                        hardware=hw, op_kind="copy").workload()[1] == 2.0

    assert _nz_matches((2, 5, 16, 32), 33, 65) is True
    assert _nz_matches((5, 2, 32, 16), 33, 65) is True
    assert _nz_matches((5, 2, 16, 32), 33, 65) is False
    assert _nz_matches((2, 5, 32, 16), 33, 65) is False
    # MXFP8 32-element block view retained by the real R64 QBMM fixture.
    assert _nz_matches((192, 1024, 16, 32), 16384, 6144) is True

    supply = derive_measured_supply(
        {"aic_mac_time": 2_000_000.0, "aic_mac_ratio": 0.98},
        input_shapes="64, 33;2, 5, 16, 32", input_dtypes="DT_FLOAT4_E2M1;DT_HIFLOAT8",
        output_shapes="64, 65", output_dtypes="DT_BF16",
        block_num=24, mix_block_num=0, complete_in_window=True,
        physical_owners=24, native_type="QuantBatchMatmulV4", duration_ns=2_100_000)
    assert "weight_dtype_not_parsed" not in supply["missing"]
    assert "weight_matrix_shape_mismatch" not in supply["missing"]
    assert supply["logical_flops"] == 2 * 64 * 65 * 33
    assert supply["weight_physical_elements"] == 5 * 2 * 32 * 16


def test_a5_dsv41_mqsmla_mxfp4_mhc_bidirectional_structure_loop(tmp_path: Path) -> None:
    from mindie_sim.compose import compose_case
    from mindie_sim.structure import main as structure_main

    case_doc = compose_case(
        "deepseek-v4.1-flash", hardware="Ascend950DT_9582", tp=8, ep=8,
        concurrency=2, prompt_tokens=256, output_tokens=4, quant="mxfp4",
        graph_capture_mode="none")
    case_path = tmp_path / "a5_case.json"
    case_path.write_text(json.dumps(case_doc), encoding="utf-8")

    root = tmp_path / "capture_a5"
    db_path = root / "rank_0" / "profiler" / "ascend_pytorch_profiler_0.db"
    _build_rank_db(
        db_path, rank=0, steady_ms=18.0, warmup_ms=50.0, steps=3,
        npu="Ascend950DT_9582",
        kernels=(
            ("MqsmlaKernel___call__", "MqsmlaKernel___call__", "AI_CORE",
             "[8, 512]", "DT_BF16", "ND", "[8, 512]", "DT_BF16", "ND"),
            ("HcPre", "HcPre", "AI_VECTOR_CORE", "[8, 512]", "DT_BF16", "ND",
             "[8, 512]", "DT_BF16", "ND"),
            ("HcPost", "HcPost", "AI_VECTOR_CORE", "[8, 512]", "DT_BF16", "ND",
             "[8, 512]", "DT_BF16", "ND"),
            ("QuantBatchMatmulV4", "QuantBatchMatmulV4", "AI_CORE",
             "[64, 33];[2, 5, 32, 16]", "DT_FLOAT4_E2M1;DT_HIFLOAT8",
             "ND;FRACTAL_NZ", "[64, 65]", "DT_BF16", "ND"),
            ("MatMulV2", "MatMulV2", "AI_CORE", "[128, 512];[512, 256]",
             "DT_BF16;DT_BF16", "ND;ND", "[128, 256]", "DT_BF16", "ND"),
        ))

    structure_path = tmp_path / "structure.json"
    assert structure_main([
        str(case_path), "--phase", "decode", "--tokens", "1", "--sequences", "2",
        "--context", "4096", "--scope", "body", "--output", str(structure_path),
    ]) == 0
    report_path = tmp_path / "closed_loop.json"
    analyzed = _cli(
        "analyze", "--root", str(root), "--auto-step",
        "--structure", str(structure_path), "--sim-case", str(case_path),
        "--phase", "decode", "--tokens", "1", "--sequences", "2",
        "--context", "4096", "--output", str(report_path))
    assert analyzed.returncode == 0, analyzed.stderr
    report = json.loads(report_path.read_text())
    assert report["structure_ingress"]["generated_structure"] is False
    assert report["structure_mapping"]["status"] in {
        "mapped", "partial", "unresolved", "unmatched"}
    assert report["sim_cohort_comparison"]["schema_version"] == "mindie-sim.cohort-comparison/1"
    assert isinstance(report["sim_cohort_comparison"]["windows"], list)

    # Reverse bridge 2: mindie-sim.graph/1 + explicit --sim-case/--context.
    graph_path = tmp_path / "graph.json"
    import mindie_sim.cli as sim_cli

    assert sim_cli.main([
        "graph", str(case_path), "--phase", "decode", "--tokens", "1",
        "--sequences", "2", "--scope", "body", "--output", str(graph_path),
    ]) == 0
    graph_report_path = tmp_path / "graph_loop.json"
    graph_analyzed = _cli(
        "analyze", "--root", str(root), "--auto-step",
        "--structure", str(graph_path), "--sim-case", str(case_path),
        "--phase", "decode", "--tokens", "1", "--sequences", "2",
        "--context", "4096", "--output", str(graph_report_path))
    assert graph_analyzed.returncode == 0, graph_analyzed.stderr
    graph_report = json.loads(graph_report_path.read_text())
    comparison = graph_report["sim_graph_summary_comparison"]
    assert comparison["status"] == "compared"
    assert comparison["graph_predicted_ms"] > 0
    assert "structure_mapping" in graph_report

    # Negative control: graph cost summary alone must name the exact command.
    missing_case = _cli(
        "analyze", "--root", str(root), "--auto-step",
        "--structure", str(graph_path), "--phase", "decode", "--tokens", "1",
        "--sequences", "2", "--context", "4096")
    assert missing_case.returncode != 0
    assert "mindie-sim structure" in missing_case.stderr


# --------------------------------------------------------------------------- #
# 4. version / doctor / remote-guide
# --------------------------------------------------------------------------- #
def test_doctor_version_and_remote_guide_contracts(tmp_path: Path) -> None:
    from mindie_profiler.cli_advisor import (
        doctor_main, remote_guide_main, version_main,
    )

    assert "torch_npu" not in sys.modules
    assert _cli("version").returncode == 0
    assert __version__ in _cli("version").stdout
    version_json = _cli("version", "--json")
    assert json.loads(version_json.stdout)["version"] == __version__

    doctor = _cli("doctor")
    assert doctor.returncode == 0, doctor.stderr
    payload = json.loads(doctor.stdout)
    assert payload["status"] in {"ok", "degraded"}
    assert payload["op_api_catalog"]["operator_count"] > 0
    assert payload["mindie_sim_bridge"]["catalog_models"] >= 37
    assert "torch_npu" not in sys.modules

    guide = _cli("remote-guide", "--root", "/remote/msprof",
                 "--stage-dir", str(tmp_path / "bundle"))
    assert guide.returncode == 0, guide.stderr
    guide_payload = json.loads(guide.stdout)
    assert guide_payload["bundle_staged"] is True
    export = guide_payload["remote_profiler_execution_guide"]["step_3_export_sim_case_in_place"]
    assert "--phase" in export["argv"] and "decode" in export["argv"]
    assert "--max-num-batched-tokens" in export["argv"]
    assert "max_num_batched-tokens" not in " ".join(export["argv"])
    assert (tmp_path / "bundle" / "mindie_profiler" / "op_api_catalog.json").is_file()
    for protected in (Path.home(), Path.cwd(), Path("/")):
        with pytest.raises(ProfilerUsageError):
            remote_guide_main(["--root", "/remote/msprof", "--stage-dir", str(protected)])
    # `main` maps the refusal to a non-zero exit without a traceback.
    refused = _cli("remote-guide", "--root", "/remote/msprof",
                   "--stage-dir", str(Path.cwd()))
    assert refused.returncode == 2 and "refusing" in refused.stderr

    missing = _cli("analyze", "--root", str(tmp_path / "absent_capture"))
    assert missing.returncode == 2
    assert "remote-guide" in missing.stderr
    assert "does NOT" in missing.stderr or "do NOT" in missing.stderr


# --------------------------------------------------------------------------- #
# 5. Big-trace speed guards
# --------------------------------------------------------------------------- #
def test_big_trace_perf_guards_pmu_csv_correlate_and_readonly_trace(tmp_path: Path) -> None:
    import csv
    import time

    from mindie_profiler.correlate_index import HostCorrelationIndex
    from mindie_profiler.events import Window
    from mindie_profiler.sources_csv import CsvSource, probe_csv
    from mindie_profiler.sources_db import DbSource, probe_db
    from mindie_profiler.sources_trace import build_trace_index

    # 5 windows / 50k unindexed PMU rows: one bounded scan, per-window budgets.
    db_path = tmp_path / "pmu.db"
    con = sqlite3.connect(db_path)
    try:
        _create_schema(con)
        sid = _Ids(con)
        windows = []
        gid = 1
        for step in range(5):
            start = step * 1_000_000
            con.execute("INSERT INTO STEP_TIME VALUES (?,?,?)", (step, start, start + 200_000))
            windows.append(Window(start, start + 200_000, step=step, label=f"step={step}"))
            for _ in range(1000):
                con.execute("INSERT INTO TASK VALUES (?,?,?,?,?,?,?,?,?,?)",
                            (gid, start + 1000, start + 2000, 0, 1, gid, 0, 0,
                             sid("AI_CORE"), None))
                con.execute("INSERT INTO COMPUTE_TASK_INFO VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (sid("MatMulV2"), gid, 20, 0, sid("AI_CORE"),
                             sid("MatMulV2"), sid("[8, 16];[16, 8]"),
                             sid("DT_BF16;DT_BF16"), sid("ND;ND"),
                             sid("[8, 8]"), sid("DT_BF16"), sid("ND"),
                             sid("dynamic"), 0))
                for metric in range(10):
                    con.execute("INSERT INTO TASK_PMU_INFO VALUES (?,?,?)",
                                (gid, sid(f"aic_mac_time_{metric}"), 1.0))
                gid += 1
        con.commit()
    finally:
        con.close()
    source = DbSource(probe_db(db_path))
    started = time.perf_counter()
    results = source.iter_windows(windows)
    elapsed = time.perf_counter() - started
    assert elapsed < 0.5, elapsed
    assert [stats.pmu_rows for _events, stats in results] == [10_000] * 5
    assert all(stats.rows_read > 0 for _events, stats in results)

    # CSV: 50k rows, 1% in window, identical rows_read/bad_rows to full iteration.
    csv_path = tmp_path / "kernel_details.csv"
    header = ["Name", "Type", "Accelerator Core", "Start Time(us)",
              "Duration(us)", "Wait Time(us)", "Input Shapes", "Input Data Types",
              "Input Formats", "Output Shapes", "Output Data Types", "Output Formats"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for index in range(50_000):
            start = 10.0 if index < 500 else 10_000.0 + index
            duration = "bad" if index in (700, 900) else "5.0"
            writer.writerow([
                "MatMulV2", "MatMulV2", "AI_CORE", str(start), duration, "0",
                "[8, 16];[16, 8]", "DT_BF16;DT_BF16", "ND;ND",
                "[8, 8]", "DT_BF16", "ND",
            ])
    schema = probe_csv(csv_path)
    csv_source = CsvSource(schema, rank_id="rank_0", rank_index=0)
    full_stats = None
    full_count = 0
    from mindie_profiler.events import QueryStats

    full_stats = QueryStats(rank_id="rank_0", window_label="full", budget=100_000)
    for _event in csv_source.iter_events(stats=full_stats):
        full_count += 1
    window = Window(0, 100_000, step=0, label="step=0")
    started = time.perf_counter()
    windowed = csv_source.read_windows([window])
    elapsed = time.perf_counter() - started
    assert elapsed < 0.5, elapsed
    events, stats = windowed[0]
    assert stats.rows_read == full_stats.rows_read == 50_000
    assert stats.bad_rows == full_stats.bad_rows == 2
    assert stats.rows_selected == len(events) == 500
    assert full_count == 49_998

    # Correlation index: 2000 x 2000 x 2000 under 0.5s, exact containment order.
    cann_events = [
        {"table": "CANN_API", "name": f"c{i}", "start_ns": i, "end_ns": i + 100,
         "global_tid": str(i % 4), "connection_id": i % 7}
        for i in range(2000)
    ]
    pytorch_events = [
        {"table": "PYTORCH_API", "name": f"p{i}", "start_ns": i, "end_ns": i + 120,
         "global_tid": str(i % 4), "connection_id": i % 7}
        for i in range(2000)
    ]
    links = {i: {i % 7} for i in range(1, 8)}
    started = time.perf_counter()
    index = HostCorrelationIndex(cann_events, pytorch_events, links)
    for task in cann_events[:2000]:
        index.find_cann(task)
        index.find_pytorch(task, task)
    elapsed = time.perf_counter() - started
    assert elapsed < 0.5, elapsed
    task = {"table": "TASK", "start_ns": 10, "end_ns": 50, "connection_id": None}
    cann, basis, unique, count = index.find_cann(task)
    assert cann["name"] == "c0" and basis == "cann_interval_contains_task"
    assert unique is False and count > 1

    # Read-only capture directory: sidecar falls back to the confined cache.
    read_only = tmp_path / "readonly"
    read_only.mkdir()
    trace = read_only / "trace_view.json"
    trace.write_text(json.dumps({"traceEvents": [
        {"name": "ProfilerStep#0", "ts": 1.0, "dur": 2.0, "pid": 1, "tid": 1},
        {"name": "op", "ts": 3.0, "dur": 1.0, "pid": 1, "tid": 1},
    ]}), encoding="utf-8")
    original_mode = read_only.stat().st_mode
    os.chmod(read_only, 0o555)
    try:
        facts = build_trace_index(trace)
    finally:
        os.chmod(read_only, original_mode)
    assert facts["rebuilt"] is True and facts["event_count"] == 2
    assert Path(facts["index_path"]).parent != read_only
