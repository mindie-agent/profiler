"""Tier 0/1 unit and CLI tests for the profiler -> mindie-sim bridge.

[Role] Verify deterministic Wave 5/profiler/C7 normalization, CLI overrides and
  atomic output, strict observed-profile isolation, and schema-valid Cases.
[Invariants] Observed timings never leave runtime.metadata; missing values stay
  None; every exported Case must parse and predict with the installed simulator.
[Timeouts & Locks] Pure in-memory/tmp_path work; one bounded isolated import.
[Side-Effect Policy] Reads repository fixtures; writes only tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from mindie_profiler import sim_bridge

ROOT = Path(__file__).resolve().parents[1]
OBSERVED_KEYS = {
    "step_time_ms", "tpot_p50_ms", "ttft_p50_ms", "device_busy_union_ms",
    "device_activity_sum_ms", "exposed_comm_ms", "device_uncovered_ms",
    "cube_share", "vector_share", "hccl_share", "comm_share", "aicpu_share",
    "host_share", "attention_share", "moe_share", "kv_peak_ratio",
    "dominant_bottleneck", "top_operators",
}
PROVENANCE_KEYS = {
    "schema_version", "parser_version", "source_path", "source_kind", "cell_tag",
    "extracted_hardware", "extracted_model", "execution_mode",
    "hccl_op_expansion_mode", "overrides_applied", "no_forward_latency_leakage",
}


@pytest.fixture(autouse=True)
def isolated_bridge_environment(tmp_path, monkeypatch):
    for key in ("MINDIE_CONFIG_HOME", "MINDIE_DATA_HOME", "MINDIE_DIAGNOSTICS_ROOT",
                "HOME", "USERPROFILE", "XDG_CONFIG_HOME", "XDG_STATE_HOME"):
        monkeypatch.setenv(key, str(tmp_path / ("env-" + key.lower())))
    yield


def _write_wave5(root: Path, *, npu_type: str = "A3", graph: str = "piecewise") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "run_meta.json").write_text(json.dumps({
        "npu_type": npu_type,
        "model_name": "Qwen3.6-27B-W8A8",
        "parallelism": {"tp": 4, "dp": 2, "ep": 8},
        "workload": {"batch_size": 8, "seq_len": 4096, "decode_steps": 128},
        "env": {"NUM_LAYERS": "64", "NUM_EXPERTS": "256", "TOP_K": "8", "SPEC_K": "3",
                "HCCL_OP_EXPANSION_MODE": "AICPU"},
    }), encoding="utf-8")
    (root / "benchmark_summary.json").write_text(json.dumps({
        "label": "a3_qwen36_tp4dp2ep8_c8", "concurrency": 8, "prefix_len": 4096,
        "decode_len": 128, "tensor_parallel_size": 4, "step_time_ms": 22.0,
        "tpot_client_ms": {"median": 7.5}, "ttft_ms": {"median": 220.0},
        "kernel_stats": {
            "total_device_time_us": 2_000_000.0,
            "by_accelerator_core": {
                "MIX_AIC": {"total_us": 800_000.0, "pct_of_device_time": 40.0},
                "AI_VECTOR_CORE": {"total_us": 400_000.0, "pct_of_device_time": 20.0},
                "COMMUNICATION": {"total_us": 700_000.0, "pct_of_device_time": 35.0},
                "AI_CPU": {"total_us": 100_000.0, "pct_of_device_time": 5.0},
            },
            "top_operators_by_device_time": [
                {"op_type": "hcom_allReduce_", "count": 100, "total_us": 700_000.0,
                 "pct_of_device_time": 35.0},
                {"op_type": "FusedInferAttentionScore", "count": 50,
                 "total_us": 300_000.0, "pct_of_device_time": 15.0},
            ],
        },
        "extra": {"graph_mode": graph, "quantization": "W8A8"},
    }), encoding="utf-8")
    (root / "client_cell.json").write_text(json.dumps({
        "label": "a3_qwen36_tp4dp2ep8_c8", "concurrency": 8,
        "prefix_len": 4096, "decode_len": 128,
    }), encoding="utf-8")
    (root / "meta.env").write_text(
        "NPU_TYPE=A3\nTP=4\nDP=2\nEP=8\nINPUT_LEN=4096\nPREFIX_LEN=0\n"
        "OUTPUT_LEN=128\nCONCURRENCY=8\nHCCL_OP_EXPANSION_MODE=AICPU\n",
        encoding="utf-8",
    )
    (root / "cmd.sh").write_text(
        "python serve.py --tensor-parallel-size 4 --data-parallel-size 2 "
        "--enable-expert-parallel --enforce-eager\n", encoding="utf-8",
    )
    (root / "op_statistic.csv").write_text(
        "Device_id,OP Type,Core Type,Count,Total Time(us),Avg Time(us),Ratio(%)\n"
        "0,hcom_allReduce_,AI_CPU,100,700000,7,35\n"
        "0,QuantBatchMatmulV3,MIX_AIC,200,800000,4,40\n"
        "0,FusedInferAttentionScore,AI_CORE,50,300000,6,15\n"
        "0,Slice,AI_VECTOR_CORE,50,200000,4,10\n", encoding="utf-8",
    )
    (root / "step_trace_time.csv").write_text(
        "Device_id,Step,Computing,Communication(Not Overlapped),Overlapped,"
        "Communication,Free,Stage,Bubble,Communication(Not Overlapped and Exclude Receive),Preparing\n"
        "0,,1200000,700000,0,700000,100000,2000000,0,700000,0\n", encoding="utf-8",
    )
    return root


def _assert_schema_valid(case: dict) -> None:
    sim = pytest.importorskip("mindie_sim")
    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(case)
    result = sim.predict(parsed, scope="body", phase="decode", tokens=1, context=4096)
    assert result["complete_ms"] > 0


def test_wave5_capture_extracts_metadata_and_observed_profile(tmp_path):
    case = sim_bridge.export_sim_case(_write_wave5(tmp_path / "wave5"))

    assert set(case) == {"machine", "model", "workload", "runtime", "slo"}
    metadata = case["runtime"]["metadata"]
    assert set(metadata["observed_profile"]) == OBSERVED_KEYS
    assert set(metadata["profiler_provenance"]) == PROVENANCE_KEYS
    assert metadata["profiler_provenance"]["schema_version"] == "mindie-profiler-sim-bridge/1"
    assert metadata["profiler_provenance"]["no_forward_latency_leakage"] is True
    assert case["machine"]["sku"] == "Ascend910_9392"
    assert case["runtime"]["parallel"] == {"tp": 4, "dp": 2, "ep": 8, "pp": 1}
    assert metadata["execution_mode"] == "piecewise"
    assert case["runtime"]["graph_capture_mode"] == "piecewise"
    assert metadata["hccl_op_expansion_mode"] == "aicpu"
    assert metadata["bridge_summary"]["system"]["quantization"] == "w8a8"
    assert metadata["bridge_summary"]["system"]["spec_tokens"] == 3
    assert metadata["bridge_summary"]["workload"]["batch_size"] == 8

    observed = metadata["observed_profile"]
    assert observed["step_time_ms"] == 22.0
    assert observed["tpot_p50_ms"] == 7.5
    assert observed["ttft_p50_ms"] == 220.0
    assert observed["device_busy_union_ms"] == pytest.approx(1900.0)
    assert observed["device_activity_sum_ms"] == pytest.approx(2000.0)
    assert observed["exposed_comm_ms"] == pytest.approx(700.0)
    assert observed["device_uncovered_ms"] == pytest.approx(100.0)
    assert observed["hccl_share"] == pytest.approx(0.35)
    assert observed["aicpu_share"] == pytest.approx(0.05)
    assert observed["dominant_bottleneck"] in {
        "comm_bound", "launch_host_bound", "memory_kv_bound", "compute_bound",
    }
    assert 0 < len(observed["top_operators"]) <= 10
    assert observed["top_operators"][0]["op_type"] == "hcom_allReduce_"
    assert metadata["profiler_provenance"]["extracted_model"] == "qwen3.6-27b"
    _assert_schema_valid(case)


def test_profiler_capture_fixture_exports_without_observed_leakage():
    fixture = ROOT / "tests" / "fixtures" / "profiler_capture_a2"
    case = sim_bridge.export_sim_case(fixture)

    metadata = case["runtime"]["metadata"]
    provenance = metadata["profiler_provenance"]
    assert provenance["source_kind"] == "profiler_capture"
    assert provenance["extracted_hardware"] == "Ascend910B4"
    assert metadata["observed_profile"]["step_time_ms"] == pytest.approx(44.24024666666667)
    assert metadata["observed_profile"]["top_operators"] == []
    assert "observed_profile" not in case
    assert "profiler_provenance" not in case["runtime"]
    _assert_schema_valid(case)


def test_c7_summary_json_exports_observed_blocks_and_hotspots(tmp_path):
    report = {
        "schema_version": "mindie-profile-summary/1",
        "scene": {"phase": "decode", "tp": 4, "dp": 2, "graph_mode": "aclgraph"},
        "step_accounting": {
            "step_time_ms": 20.0, "wall_ms_p50": 20.0, "device_busy_union_ms_p50": 18.0,
            "device_activity_sum_ms_p50": 30.0, "exposed_comm_ms_p50": 9.0,
            "host_gap_ms_p50": 2.0, "aicpu_exposed_ratio_p50": 0.1,
        },
        "semantic_block_breakdown": [
            {"block": "Comm", "share_of_busy_pct": 50.0},
            {"block": "Attention", "share_of_busy_pct": 25.0},
            {"block": "MoE", "share_of_busy_pct": 15.0},
        ],
        "top_hotspot_kernels": [
            {"kernel_name": "hcom_allReduce_", "call_count": 10,
             "measured_device_ms_total": 9.0, "share_of_busy_pct": 50.0,
             "execution_engine": "hccl"},
            {"kernel_name": "FusedInferAttentionScore", "call_count": 5,
             "measured_device_ms_total": 4.5, "share_of_busy_pct": 25.0,
             "execution_engine": "aic"},
        ],
    }
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    case = sim_bridge.export_sim_case(path, chip="A3", model="qwen3-30b-a3b",
                                      tp=4, dp=2, ep=8)

    observed = case["runtime"]["metadata"]["observed_profile"]
    assert case["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "c7_report"
    assert observed["step_time_ms"] == 20.0
    assert observed["hccl_share"] == 0.5
    assert observed["comm_share"] == 0.5
    assert observed["attention_share"] == 0.25
    assert observed["moe_share"] == 0.15
    assert observed["top_operators"][0]["name"] == "hcom_allReduce_"
    assert observed["dominant_bottleneck"] == "comm_bound"
    _assert_schema_valid(case)


def test_cli_overrides_write_atomic_case(tmp_path):
    capture = _write_wave5(tmp_path / "wave5")
    output = tmp_path / "case.json"
    assert sim_bridge.main([
        "export-sim-case", "--capture-dir", str(capture), "--chip", "A3",
        "--model", "qwen3-30b-a3b", "--tp", "4", "--dp", "2", "--ep", "8",
        "--batch-size", "8", "--seq-len", "2048", "--decode-steps", "64",
        "--phase", "decode", "--quant", "w8a8", "--graph-mode", "eager",
        "--hccl-expansion-mode", "aiv", "--output", str(output),
    ]) == 0
    case = json.loads(output.read_text(encoding="utf-8"))
    metadata = case["runtime"]["metadata"]
    assert case["runtime"]["parallel"] == {"tp": 4, "dp": 2, "ep": 8, "pp": 1}
    assert metadata["profiler_provenance"]["overrides_applied"] == [
        "batch_size", "chip", "decode_steps", "dp", "ep", "graph_mode",
        "hccl_expansion_mode", "model", "phase", "quant", "seq_len", "tp",
    ]
    assert metadata["execution_mode"] == "eager"
    assert case["runtime"]["graph_capture_mode"] == "none"
    assert metadata["hccl_op_expansion_mode"] == "aiv"
    assert metadata["bridge_summary"]["workload"] == {
        "batch_size": 8, "seq_len": 2048, "decode_steps": 64,
        "prefix_len": 0, "phase": "decode",
    }
    assert not list(tmp_path.glob("*.tmp"))
    _assert_schema_valid(case)


@pytest.mark.parametrize("flag", ["--input", "--root", "positional"])
def test_cli_input_aliases(tmp_path, flag):
    capture = _write_wave5(tmp_path / ("wave5-" + flag.strip("-")))
    argv = ["export-sim-case"]
    if flag == "positional":
        argv.append(str(capture))
    else:
        argv.extend([flag, str(capture)])
    assert sim_bridge.main(argv) == 0


def test_no_leakage_and_roundtrip_prediction(tmp_path):
    case = sim_bridge.export_sim_case(_write_wave5(tmp_path / "wave5"))
    metadata = case["runtime"]["metadata"]
    assert "observed_profile" in metadata and "profiler_provenance" in metadata
    for key in ("observed_profile", "profiler_provenance", "bridge_summary"):
        assert key not in case
        assert key not in case["runtime"]
    for section in ("model", "machine", "workload"):
        text = json.dumps(case[section], sort_keys=True)
        for token in ("step_time_ms", "tpot_p50_ms", "ttft_p50_ms", "top_operators"):
            assert token not in text
    assert "observed_profile" not in json.dumps(case["runtime"].get("kernels", {}))
    _assert_schema_valid(case)

    code = (
        "import sys; "
        f"sys.path.insert(0, {str(ROOT)!r}); "
        "import mindie_profiler; from mindie_profiler.cli import main; "
        "assert 'mindie_sim' not in sys.modules; print('NO_SIM_AT_IMPORT')"
    )
    proc = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True,
                          text=True, timeout=10, check=False)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "NO_SIM_AT_IMPORT"


def test_raw_run_meta_and_benchmark_json_inputs(tmp_path):
    run_meta = tmp_path / "run_meta.json"
    run_meta.write_text(json.dumps({
        "npu_type": "A3", "model_name": "Qwen3-30B-A3B-W8A8",
        "parallelism": {"tp": 4, "dp": 2, "ep": 8},
        "workload": {"batch_size": 8, "seq_len": 2048, "decode_steps": 64},
    }), encoding="utf-8")
    case = sim_bridge.export_sim_case(run_meta)
    assert case["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "run_meta"
    assert case["runtime"]["parallel"] == {"tp": 4, "dp": 2, "ep": 8, "pp": 1}
    assert case["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "qwen3-30b-a3b"

    benchmark = tmp_path / "benchmark_summary.json"
    benchmark.write_text(json.dumps({
        "label": "a3_qwen30_tp4_c8", "tensor_parallel_size": 4, "concurrency": 8,
        "kernel_stats": {"total_device_time_us": 1000,
                         "by_accelerator_core": {"COMMUNICATION": {"total_us": 400},
                                                  "AI_CORE": {"total_us": 600}}},
        "top_operators": [{"op_type": "hcom_allReduce_", "total_us": 400,
                           "pct_of_device_time": 40.0}],
    }), encoding="utf-8")
    case = sim_bridge.export_sim_case(benchmark, chip="A3", model="qwen3-30b-a3b")
    assert case["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "benchmark_summary"
    assert case["runtime"]["parallel"]["tp"] == 4
    assert case["runtime"]["metadata"]["observed_profile"]["hccl_share"] == pytest.approx(0.4)


def test_attribution_named_report_and_explicit_output(tmp_path):
    report = {
        "schema_version": "mindie-profile-summary/1",
        "step_accounting": {"wall_ms_p50": 12.0, "device_busy_union_ms_p50": 10.0,
                            "exposed_comm_ms_p50": 4.0},
        "semantic_block_breakdown": [{"block": "Comm", "share_of_busy_pct": 40.0}],
        "top_hotspot_kernels": [{"kernel_name": "hcom_allReduce_", "call_count": 3,
                                 "measured_device_ms_total": 4.0,
                                 "share_of_busy_pct": 40.0, "execution_engine": "hccl"}],
    }
    source = tmp_path / "attribution.json"
    source.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "nested" / "case.json"
    returned = sim_bridge.export_sim_case(
        source, chip="a3", model="qwen3-30b-a3b", tp=4, ep=4, output=output,
    )
    written = json.loads(output.read_text(encoding="utf-8"))
    assert returned == written
    assert written["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "c7_report"
    assert not list(output.parent.glob("*.tmp"))


def test_catalog_models_preserve_geometry_with_structural_metadata():
    qwen = sim_bridge.export_sim_case({
        "npu_type": "A3", "model_name": "Qwen3.6-27B",
        "env": {"NUM_LAYERS": "64", "SPEC_K": "3"},
    })
    assert qwen["model"]["hidden_size"] == 5120
    assert qwen["model"]["num_heads"] == 24
    assert qwen["model"]["attention"] == "gdn"
    assert qwen["model"]["ffn"] == "dense"
    assert qwen["model"]["layers"] == 64
    _assert_schema_valid(qwen)

    dsv4 = sim_bridge.export_sim_case({
        "npu_type": "A3", "model_name": "deepseek-v4-flash",
        "env": {"SPEC_K": "3"},
    })
    assert dsv4["model"]["hidden_size"] == 4096
    assert dsv4["model"]["num_heads"] == 64
    assert dsv4["model"]["attention"] == "mla"
    assert dsv4["model"]["ffn"] == "moe"
    assert dsv4["model"]["layers"] == 43
    _assert_schema_valid(dsv4)


def test_invalid_parallel_topology_rejected_by_api_and_cli(tmp_path):
    capture = _write_wave5(tmp_path / "wave5")
    output = tmp_path / "invalid.json"
    with pytest.raises(sim_bridge.ProfilerUsageError, match=r"ep_not_divisor_of_dp_tp_domain|invalid_ep_partition"):
        sim_bridge.export_sim_case(capture, tp=4, dp=1, ep=3)
    rc = sim_bridge.main([
        "export-sim-case", "--input", str(capture),
        "--tp", "4", "--dp", "1", "--ep", "3", "--output", str(output),
    ])
    assert rc == 2
    assert not output.exists()


def test_nested_traits_and_wrapped_benchmark_summary():
    case_traits = sim_bridge.export_sim_case({
        "traits": {
            "hw": "a2", "family": "dsv2lite", "phase": "decode",
            "tp": 4, "ep": 4, "concurrency": 16, "context_tokens": 8192,
        },
        "observed_ms": 14.2,
    })
    assert case_traits["machine"]["sku"] == "Ascend910B4"
    assert case_traits["runtime"]["parallel"] == {"tp": 4, "dp": 1, "ep": 4, "pp": 1}
    assert case_traits["runtime"]["metadata"]["bridge_summary"]["workload"]["batch_size"] == 16
    assert case_traits["runtime"]["metadata"]["bridge_summary"]["workload"]["seq_len"] == 8192
    assert case_traits["runtime"]["metadata"]["observed_profile"]["step_time_ms"] == pytest.approx(14.2)

    wrapped = sim_bridge.export_sim_case({
        "benchmark_summary": {
            "concurrency": 8, "tensor_parallel_size": 4,
            "step_time_ms": 12.5, "tpot_client_ms": {"median": 6.2},
        },
    }, model="qwen3-30b-a3b")
    assert wrapped["runtime"]["parallel"]["tp"] == 4
    assert wrapped["runtime"]["metadata"]["bridge_summary"]["workload"]["batch_size"] == 8
    assert wrapped["runtime"]["metadata"]["observed_profile"]["step_time_ms"] == pytest.approx(12.5)
    assert wrapped["runtime"]["metadata"]["observed_profile"]["tpot_p50_ms"] == pytest.approx(6.2)


def test_small_pct_non_renormalized_hotspots_and_step_trace_overlap(tmp_path):
    c7 = sim_bridge.export_sim_case({
        "schema_version": "mindie-profile-summary/1",
        "step_accounting": {
            "wall_ms_p50": 10.0,
            "aicpu_exposed_ratio": 0.12,
            "underfeed_bubble_ratio": 0.08,
        },
        "semantic_block_breakdown": [{"block": "Comm", "share_of_busy_pct": 0.5}],
    })
    obs_c7 = c7["runtime"]["metadata"]["observed_profile"]
    assert obs_c7["comm_share"] == pytest.approx(0.005)
    assert obs_c7["aicpu_share"] == pytest.approx(0.12)
    assert obs_c7["host_share"] == pytest.approx(0.08)

    bench = sim_bridge.export_sim_case({
        "kernel_stats": {
            "top_operators_by_device_time": [
                {"op_type": "FusedInferAttentionScore", "pct_of_device_time": 20.0},
                {"op_type": "MatMulV3", "pct_of_device_time": 20.0},
            ],
        },
    })
    assert bench["runtime"]["metadata"]["observed_profile"]["attention_share"] == pytest.approx(0.2)

    trace_dir = tmp_path / "trace_only"
    trace_dir.mkdir()
    (trace_dir / "step_trace_time.csv").write_text(
        "Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n"
        "1000,200,300,500,100,1300\n",
        encoding="utf-8",
    )
    trace_case = sim_bridge.export_sim_case(trace_dir)
    obs_trace = trace_case["runtime"]["metadata"]["observed_profile"]
    assert obs_trace["device_busy_union_ms"] == pytest.approx(1.2)
    assert obs_trace["device_activity_sum_ms"] == pytest.approx(1.5)
    system_summary = trace_case["runtime"]["metadata"]["bridge_summary"]["system"]
    for key in ("source_kind", "source_path", "cell_tag"):
        assert key not in system_summary


def test_glm53_qwen35_mxfp8_and_registered_skus():
    glm = sim_bridge.export_sim_case({}, model="glm-5.3", chip="Ascend910_9362")
    assert glm["machine"]["sku"] == "Ascend910_9362"
    assert glm["model"]["layers"] == 78
    assert glm["model"]["num_experts"] == 256
    assert glm["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "glm-5.3"
    _assert_schema_valid(glm)

    glm_flash = sim_bridge.export_sim_case({}, model="glm-5.3-flash", chip="Ascend910B1")
    assert glm_flash["machine"]["sku"] == "Ascend910B1"
    assert glm_flash["model"]["layers"] == 45
    assert glm_flash["model"]["num_experts"] == 288
    _assert_schema_valid(glm_flash)

    q35 = sim_bridge.export_sim_case({}, model="qwen3.5-35b-a3b", chip="a3")
    assert q35["model"]["layers"] == 40
    assert q35["model"]["attention"] == "gdn"
    assert q35["model"]["num_experts"] == 256
    _assert_schema_valid(q35)

    mxfp8 = sim_bridge.export_sim_case({
        "npu_type": "A5", "model_name": "Qwen3.8-27B-W8A8-MXFP8",
    })
    assert mxfp8["runtime"]["metadata"]["bridge_summary"]["system"]["quantization"] == "w8a8_mxfp8"
    _assert_schema_valid(mxfp8)


def test_explicit_config_precedence_deepseek_mla_and_a3_tp16():
    cfg_case = sim_bridge.export_sim_case({
        "model_name": "Qwen3.6-27B",
        "model_config": {
            "hidden_size": 1024, "num_attention_heads": 8,
            "num_hidden_layers": 2, "intermediate_size": 3072, "vocab_size": 1024,
        },
    })
    assert cfg_case["model"]["hidden_size"] == 1024
    assert cfg_case["model"]["num_heads"] == 8
    assert cfg_case["model"]["layers"] == 2
    _assert_schema_valid(cfg_case)

    dsv2_cfg = sim_bridge.export_sim_case({
        "model_config": {
            "model_type": "deepseek_v2", "hidden_size": 2048, "num_attention_heads": 16,
            "num_hidden_layers": 27, "intermediate_size": 10944, "vocab_size": 102400,
            "kv_lora_rank": 512, "q_lora_rank": None, "qk_nope_head_dim": 128,
            "qk_rope_head_dim": 64, "v_head_dim": 128, "n_routed_experts": 64,
            "num_experts_per_tok": 6, "moe_intermediate_size": 1408,
        },
    }, chip="a3", tp=16, ep=16)
    assert dsv2_cfg["model"]["attention"] == "mla"
    assert dsv2_cfg["machine"]["ranks_per_node"] == 16
    _assert_schema_valid(dsv2_cfg)


def test_standalone_kernel_csv_wrapped_env_sim_case_roundtrip_and_walk_timeout(tmp_path, monkeypatch):
    kdir = tmp_path / "kernel_only"
    kdir.mkdir()
    (kdir / "kernel_details.csv").write_text(
        "Name,Accelerator Core,Duration(us)\n"
        "hcom_allReduce_,AI_CPU,300\n"
        "QuantBatchMatmulV3,MIX_AIC,700\n",
        encoding="utf-8",
    )
    kcase = sim_bridge.export_sim_case(kdir)
    kobs = kcase["runtime"]["metadata"]["observed_profile"]
    assert kobs["device_activity_sum_ms"] == pytest.approx(1.0)
    assert len(kobs["top_operators"]) == 2
    assert kcase["runtime"]["metadata"]["hccl_op_expansion_mode"] == "aicpu"

    wrapped_env = sim_bridge.export_sim_case({"run_meta": {"env": {"TP": "4"}}})
    assert wrapped_env["runtime"]["parallel"]["tp"] == 4

    base_case = sim_bridge.export_sim_case(
        {}, chip="a3", model="deepseek-v2-lite", tp=4, ep=4,
        batch_size=8, seq_len=2048, decode_steps=64,
    )
    roundtrip = sim_bridge.export_sim_case(base_case)
    assert roundtrip["runtime"]["parallel"] == {"tp": 4, "dp": 1, "ep": 4, "pp": 1}
    assert len(roundtrip["workload"]["requests"]) == 8
    assert roundtrip["workload"]["requests"][0]["prompt_tokens"] == 2048
    assert roundtrip["workload"]["requests"][0]["output_tokens"] == 64

    def fake_walk(root, onerror=None):
        if onerror is not None:
            onerror(TimeoutError("scan timeout"))
        return iter(())

    monkeypatch.setattr(sim_bridge.os, "walk", fake_walk)
    with pytest.raises(TimeoutError, match="scan timeout"):
        sim_bridge.export_sim_case(kdir)


def test_full_catalog_override_precedence_and_strict_bounds(tmp_path):
    for model_id in (
        "deepseek-v3.2-prune-3l", "deepseek-v4-10t", "deepseek-v4-flash",
        "deepseek-v4-flash-0731", "deepseek-v4-pro-0813", "deepseek-v4.1-flash",
        "hunyuan-video-dit", "kimi-k3-dspark", "qwen3-30b-a3b",
        "qwen3.5-27b", "qwen3.5-moe", "qwen3.8-2.4t-a95b", "qwen3.8-27b",
    ):
        case = sim_bridge.export_sim_case({}, model=model_id, chip="a3")
        assert case["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == model_id
        _assert_schema_valid(case)

    override_case = sim_bridge.export_sim_case(
        {"model_name": "DeepSeek-V3-671B"}, model="Qwen3.6-27B", chip="a3",
    )
    assert override_case["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "qwen3.6-27b"
    assert override_case["model"]["layers"] == 64

    with pytest.raises(sim_bridge.ProfilerUsageError, match=r"(?i)unsupported.*model"):
        sim_bridge.export_sim_case({}, model="unknown-custom-model")

    for bad_batch in (0, 4097):
        with pytest.raises(sim_bridge.ProfilerUsageError, match="batch_size_out_of_bounds"):
            sim_bridge.export_sim_case({}, batch_size=bad_batch)

    partial_acct = sim_bridge.export_sim_case({
        "accounting": {
            "step_accounting": {"step_time_ms": 12.0},
            "window_accounting": {
                "device_busy_union_ms": 9.5,
                "exposed_comm_ms": 1.5,
                "aicpu_share": 0.1,
            },
        },
    })
    obs_partial = partial_acct["runtime"]["metadata"]["observed_profile"]
    assert obs_partial["step_time_ms"] == pytest.approx(12.0)
    assert obs_partial["device_busy_union_ms"] == pytest.approx(9.5)
    assert obs_partial["exposed_comm_ms"] == pytest.approx(1.5)
    assert obs_partial["aicpu_share"] == pytest.approx(0.1)

    window_only = sim_bridge.export_sim_case({
        "accounting": {
            "window_accounting": {"device_busy_union_ms_p50": 8.0},
        },
    })
    obs_win = window_only["runtime"]["metadata"]["observed_profile"]
    assert obs_win["step_time_ms"] is None
    assert obs_win["device_busy_union_ms"] == pytest.approx(8.0)

    multi_step_dir = tmp_path / "multi_step"
    multi_step_dir.mkdir()
    (multi_step_dir / "step_trace_time.csv").write_text(
        "Device_id,Step,Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n"
        "0,1,1000,200,300,500,100,1300\n"
        "0,2,2000,400,600,1000,200,2600\n"
        "1,1,9000,9000,9000,9000,9000,9000\n",
        encoding="utf-8",
    )
    multi_case = sim_bridge.export_sim_case(multi_step_dir)
    obs_multi = multi_case["runtime"]["metadata"]["observed_profile"]
    assert obs_multi["step_time_ms"] == pytest.approx(1.95)
    assert obs_multi["device_busy_union_ms"] == pytest.approx(1.8)

    corrupt_dir = tmp_path / "corrupt_meta"
    corrupt_dir.mkdir()
    (corrupt_dir / "step_trace_time.csv").write_text(
        "Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n"
        "1000,200,300,500,100,1300\n",
        encoding="utf-8",
    )
    (corrupt_dir / "run_meta.json").write_text("{corrupt", encoding="utf-8")
    with pytest.raises(sim_bridge.ProfilerUsageError, match="invalid JSON"):
        sim_bridge.export_sim_case(corrupt_dir)

    huge_csv = tmp_path / "huge.csv"
    huge_csv.write_text("Name,Duration(us)\n" + "op,1\n" * 5, encoding="utf-8")
    with pytest.raises(sim_bridge.ProfilerUsageError, match="CSV row count exceeds"):
        list(sim_bridge._iter_csv(huge_csv, max_rows=3))


def test_fourth_review_p2_regressions(tmp_path):
    a5_pr = sim_bridge.export_sim_case({"npu_type": "Ascend950PR_A5"})
    assert a5_pr["machine"]["sku"] == "Ascend950PR_9579"
    _assert_schema_valid(a5_pr)
    qwen_synth = sim_bridge.export_sim_case({"family": "synth-qwen3-30b-l8-e16-k2", "hw": "a3", "phase": "decode"})
    assert qwen_synth["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "qwen3-30b-a3b"
    _assert_schema_valid(qwen_synth)
    explicit_dsv = sim_bridge.export_sim_case({"model_config": {"model_type": "deepseek_v2", "hidden_size": 2048, "num_attention_heads": 16, "num_hidden_layers": 4, "first_k_dense_replace": 1, "intermediate_size": 10944, "vocab_size": 102400, "kv_lora_rank": 512, "q_lora_rank": 0, "qk_nope_head_dim": 128, "qk_rope_head_dim": 64, "v_head_dim": 128, "n_routed_experts": 64, "num_experts_per_tok": 6, "n_shared_experts": 2, "moe_intermediate_size": 1408}}, chip="a3")
    if "layer_plans" in explicit_dsv["model"]:
        assert explicit_dsv["model"]["layer_plans"][0]["ffn"] == "dense" and explicit_dsv["model"]["layer_plans"][1]["ffn"] == "moe" and explicit_dsv["model"]["layer_plans"][1]["num_shared_experts"] == 2
    with pytest.raises(sim_bridge.ProfilerUsageError, match="max_position_embeddings"):
        sim_bridge.export_sim_case({}, model="deepseek-v2-lite", seq_len=999999)
    dense_rt = sim_bridge.export_sim_case(sim_bridge.export_sim_case({}, model="qwen3.6-27b", chip="a3"))
    assert dense_rt["model"]["ffn"] == "dense"
    _assert_schema_valid(dense_rt)

    # 6. SPEC_K=3 configures draft_mode/draft_proposal_tokens/auxiliary.mtp without fabricating acceptance length
    spec_case = sim_bridge.export_sim_case({"env": {"SPEC_K": "3"}}, model="qwen3-30b-a3b", chip="a3")
    assert spec_case["runtime"]["metadata"]["draft_mode"] == "mtp"
    assert spec_case["runtime"]["metadata"]["draft_proposal_tokens"] == 3
    assert spec_case["runtime"].get("mtp_acceptance_length", 1.0) == 1.0
    assert spec_case["model"]["auxiliary"]["mtp"] is not None
    _assert_schema_valid(spec_case)
    spec_explicit = sim_bridge.export_sim_case(
        {"env": {"SPEC_K": "3", "MTP_ACCEPTANCE_LENGTH": "2.4"}}, model="qwen3-30b-a3b", chip="a3"
    )
    assert spec_explicit["runtime"]["mtp_acceptance_length"] == pytest.approx(2.4)

    # 7 & 8. mode="prefill_chunked" -> phase="prefill", traits.is_eager=False -> aclgraph_full
    prefill_rec = sim_bridge.export_sim_case({
        "traits": {"hw": "a3", "family": "qwen3-30b-a3b", "phase": "prefill_chunked", "is_eager": False},
    })
    assert prefill_rec["runtime"]["metadata"]["bridge_summary"]["workload"]["phase"] == "prefill"
    assert prefill_rec["runtime"]["metadata"]["execution_mode"] == "aclgraph_full"

    # 9 & 10. Untagged step_trace_time.csv keeps step_time_ms=None; tagged rows compute per-step median
    untagged_dir = tmp_path / "untagged_trace"
    untagged_dir.mkdir()
    (untagged_dir / "step_trace_time.csv").write_text(
        "Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n"
        "1000,900,100,1000,100,2000\n"
        "1200,100,900,1000,100,1400\n"
        "2000,200,800,1000,100,2300\n",
        encoding="utf-8",
    )
    untagged_case = sim_bridge.export_sim_case(untagged_dir)
    assert untagged_case["runtime"]["metadata"]["observed_profile"]["step_time_ms"] is None

    tagged_dir = tmp_path / "tagged_trace"
    tagged_dir.mkdir()
    (tagged_dir / "step_trace_time.csv").write_text(
        "Step,Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n"
        "1,1000,900,100,1000,100,2000\n"
        "2,1200,100,900,1000,100,1400\n"
        "3,2000,200,800,1000,100,2300\n",
        encoding="utf-8",
    )
    tagged_case = sim_bridge.export_sim_case(tagged_dir)
    obs_tagged = tagged_case["runtime"]["metadata"]["observed_profile"]
    assert obs_tagged["step_time_ms"] == pytest.approx(2.0)
    # Per-step busy is [1.9, 1.3, 2.2] -> median is 1.9 (not median(comp)=1.2 + median(exp)=0.2 = 1.4)
    assert obs_tagged["device_busy_union_ms"] == pytest.approx(1.9)

    # 11. api_statistic.csv Time(us) header support
    api_dir = tmp_path / "api_time_us"
    api_dir.mkdir()
    (api_dir / "run_meta.json").write_text(json.dumps({"observed_profile": {"step_time_ms": 10.0}}), encoding="utf-8")
    (api_dir / "api_statistic.csv").write_text("Name,Time(us)\naclnnLaunch,2500\n", encoding="utf-8")
    api_case = sim_bridge.export_sim_case(api_dir)
    assert api_case["runtime"]["metadata"]["observed_profile"]["host_share"] == pytest.approx(0.25)

    # 12. Uncataloged model names reject instead of silently selecting another model
    for bad_name in ("Qwen3-8B", "Qwen3-235B-A22B", "DeepSeek-V3-671B"):
        with pytest.raises(sim_bridge.ProfilerUsageError, match="unsupported or unrecognized model"):
            sim_bridge.export_sim_case({"model_name": bad_name}, chip="a3")

    # 13. architecture_override.num_routed_experts is respected
    routed_case = sim_bridge.export_sim_case({
        "model_name": "dsv2lite",
        "architecture_override": {"num_hidden_layers": 27, "num_routed_experts": 16, "num_experts_per_tok": 6},
    }, chip="a2")
    assert routed_case["model"]["num_experts"] == 16

    # 14. Standalone benchmark_summary design.max_tokens and design.shared_tokens are extracted
    bench_design = tmp_path / "benchmark_summary.json"
    bench_design.write_text(json.dumps({
        "summary": {
            "concurrency": 1, "cell": "a2_real_dsv2lite_E64_K6_tp4ep4_decode_128k_c1",
            "mode": "profile",
            "design": {"prompt_tokens": 131072, "shared_tokens": 130944, "max_tokens": 160},
        },
    }), encoding="utf-8")
    b_case = sim_bridge.export_sim_case(bench_design, model="deepseek-v2-lite", chip="a2")
    assert b_case["workload"]["requests"][0]["prompt_tokens"] == 131072
    assert b_case["workload"]["requests"][0]["prefix_tokens"] == 130944
    assert b_case["workload"]["requests"][0]["output_tokens"] == 160
    assert b_case["runtime"]["metadata"]["bridge_summary"]["workload"]["phase"] == "decode"

    # 15. Multi-step api_statistic.csv does not divide capture-wide API sum by single-step time
    multi_api_dir = tmp_path / "multi_api"
    multi_api_dir.mkdir()
    (multi_api_dir / "run_meta.json").write_text(json.dumps({
        "metrics": {"summary": {"step_from_metrics_ms": 35.0, "profile": {"window_s": 2.0}}},
    }), encoding="utf-8")
    (multi_api_dir / "api_statistic.csv").write_text(
        "Device_id,Level,API Name,Time(us),Count\n"
        "host,acl,aclrtSynchronizeEvent,800000,80\n"
        "host,acl,aclrtLaunchKernelWithHostArgs,200000,80\n",
        encoding="utf-8",
    )
    multi_api_case = sim_bridge.export_sim_case(multi_api_dir)
    assert multi_api_case["runtime"]["metadata"]["observed_profile"]["host_share"] == pytest.approx(0.1)


def test_fifth_review_p2_regressions(tmp_path):
    # 1. qwen35 shorthand & benchmark_summary mapping parity with file
    q35_case = sim_bridge.export_sim_case({"summary": {"concurrency": 4, "cell": "a3_real_qwen35_E256_K8_tp4ep4_prefill_4k_c4", "mode": "profile", "design": {"prompt_tokens": 4096, "max_tokens": 32}}, "tpot_client_ms": {"median": 12.0}})
    assert q35_case["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "qwen3.5-35b-a3b" and q35_case["runtime"]["parallel"] == {"tp": 4, "dp": 1, "ep": 4, "pp": 1} and q35_case["runtime"]["metadata"]["bridge_summary"]["workload"]["phase"] == "prefill"

    # 2. Nested text_config in multimodal config.json; static num_nextn_predict_layers does not enable speculation
    nested_case = sim_bridge.export_sim_case({"model_type": "qwen3_5_moe", "text_config": {"hidden_size": 2048, "num_attention_heads": 16, "num_key_value_heads": 2, "head_dim": 256, "num_hidden_layers": 2, "intermediate_size": 512, "vocab_size": 248320, "num_experts": 16, "num_experts_per_tok": 4, "moe_intermediate_size": 512, "num_nextn_predict_layers": 1}}, chip="a3")
    assert nested_case["model"]["layers"] == 2 and nested_case["model"]["num_experts"] == 16 and nested_case["runtime"]["metadata"].get("spec_tokens") is None and "draft_mode" not in nested_case["runtime"]["metadata"]

    # 3. SPEC_K=0 overrides architecture_override.num_nextn_predict_layers
    spec_off = sim_bridge.export_sim_case({"model_name": "qwen3-30b-a3b", "architecture_override": {"num_nextn_predict_layers": 1}, "env": {"SPEC_K": "0"}}, chip="a3")
    assert spec_off["runtime"]["metadata"]["spec_tokens"] == 0 and "draft_mode" not in spec_off["runtime"]["metadata"]

    # 4. --speculative-config enforce_eager does not poison main model graph_mode; --enable-expert-parallel ignores PP
    cmd_dir = tmp_path / "spec_cmd"
    cmd_dir.mkdir()
    (cmd_dir / "cmd.sh").write_text("vllm serve dsv2lite --tensor-parallel-size 4 --pipeline-parallel-size 2 --enable-expert-parallel --compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\"}' --speculative-config '{\"enforce_eager\":true}'\n", encoding="utf-8")
    cmd_case = sim_bridge.export_sim_case(cmd_dir, chip="a3")
    assert cmd_case["runtime"]["metadata"]["execution_mode"] == "aclgraph_full" and cmd_case["runtime"]["parallel"] == {"tp": 4, "dp": 1, "ep": 4, "pp": 2}

    # 5. Model override ignores source config max_position_embeddings
    assert sim_bridge.export_sim_case({"model_config": {"hidden_size": 2048, "num_attention_heads": 16, "max_position_embeddings": 2048}}, model="qwen3.5-35b-a3b", chip="a3", seq_len=8192)["workload"]["requests"][0]["prompt_tokens"] == 8192

    # 6. Case round-trip preserves layer_plans and applies quant override; kimi-k3-dspark uses catalog auxiliary.dspark
    q36_rt = sim_bridge.export_sim_case(sim_bridge.export_sim_case({}, model="qwen3.6-27b", chip="a3"), quant="w8a8")
    assert q36_rt["model"]["weight_dtype"] == "int8" and any(lp.get("attention") == "gdn" for lp in q36_rt["model"].get("layer_plans", ()))
    dspark_case = sim_bridge.export_sim_case({}, model="kimi-k3-dspark", chip="a3")
    if "auxiliary" in dspark_case["model"]: assert dspark_case["model"]["auxiliary"].get("dspark") is not None

    # 7. Exposed comm share is not masked; 10 tagged 100-ms steps + 1000 API calls gives host_share=0.2; W4A8 order-independent
    comm_dir = tmp_path / "comm_exp"
    comm_dir.mkdir()
    (comm_dir / "step_trace_time.csv").write_text("Step,Computing,Communication(Not Overlapped),Overlapped,Communication,Free,Stage\n" + "".join(f"{i},50000,50000,0,50000,0,100000\n" for i in range(1, 11)), encoding="utf-8")
    (comm_dir / "op_statistic.csv").write_text("OP Type,Core Type,Count,Total Time(us)\nDynamicQuant,AI_VECTOR_CORE,10,399000\nW4A8MatMul,AI_CORE,10,1000\nHcomAllReduce,AI_CPU,10,1000\n", encoding="utf-8")
    (comm_dir / "api_statistic.csv").write_text("API Name,Time(us),Count\naclrtLaunchKernel,200000,1000\n", encoding="utf-8")
    comm_case = sim_bridge.export_sim_case(comm_dir)
    assert comm_case["runtime"]["metadata"]["observed_profile"]["comm_share"] == pytest.approx(0.5) and comm_case["runtime"]["metadata"]["observed_profile"]["host_share"] == pytest.approx(0.2) and comm_case["runtime"]["metadata"]["bridge_summary"]["system"]["quantization"] == "w4a8"

    # 8. Unknown hardware tokens and non-positive dimensions raise ProfilerUsageError
    for bad_hw in ("Ascend910B7", "a4"):
        with pytest.raises(sim_bridge.ProfilerUsageError, match="unsupported or unrecognized hardware"):
            sim_bridge.export_sim_case({}, chip=bad_hw)
    for bad_kw in ({"tp": 0}, {"dp": -1}, {"seq_len": 0}, {"decode_steps": 0}):
        with pytest.raises(sim_bridge.ProfilerUsageError, match="invalid simulation case"):
            sim_bridge.export_sim_case({}, **bad_kw)

    # 9. Real qwen35-benchmark, qwen36-benchmark, qwen36-client-cell, and glm_a5_mtp3_c12_profile fixtures
    q35_bench = sim_bridge.export_sim_case(ROOT / "tests" / "fixtures" / "pipeline" / "local_a5_metadata" / "qwen35-benchmark.json", chip="a5")
    assert q35_bench["workload"]["requests"][0]["prompt_tokens"] == 4096 and q35_bench["workload"]["requests"][0]["prefix_tokens"] == 0 and q35_bench["workload"]["requests"][0]["output_tokens"] == 256
    assert q35_bench["runtime"]["metadata"]["observed_profile"]["step_time_ms"] == pytest.approx(21.073193821429133) and q35_bench["runtime"]["metadata"]["observed_profile"]["tpot_p50_ms"] == pytest.approx(7.133439254902013)
    q36_bench = sim_bridge.export_sim_case(ROOT / "tests" / "fixtures" / "pipeline" / "local_a5_metadata" / "qwen36-benchmark.json", chip="a5")
    assert q36_bench["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "benchmark_summary" and q36_bench["runtime"]["metadata"]["draft_proposal_tokens"] == 3 and q36_bench["runtime"]["metadata"]["observed_profile"]["tpot_p50_ms"] == pytest.approx(8.043379514866745)
    q36_cell = sim_bridge.export_sim_case(ROOT / "tests" / "fixtures" / "pipeline" / "local_a5_metadata" / "qwen36-client-cell.json", chip="a5")
    assert q36_cell["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "client_cell" and q36_cell["workload"]["requests"][0]["prompt_tokens"] == 4104 and q36_cell["runtime"]["metadata"]["observed_profile"]["step_time_ms"] == pytest.approx(23.685343364054606)
    glm_prof = sim_bridge.export_sim_case(ROOT / "tests" / "fixtures" / "engine_boundaries" / "glm_a5_mtp3_c12_profile.json", model="glm-5.3", chip="a5")
    assert len(glm_prof["workload"]["requests"]) == 12 and glm_prof["workload"]["requests"][0]["output_tokens"] == 256 and glm_prof["runtime"]["metadata"]["draft_proposal_tokens"] == 3

    # 10. fp16 preserves catalog architecture; Case round-trip preserves mxfp4_routed_only & no-layer_plans explicit model; standalone draft rejects SPEC_K; C7 wall_ms_p50 is not step_time_ms
    fp16_q36 = sim_bridge.export_sim_case({}, model="qwen3.6-27b", chip="a3", quant="fp16")
    assert fp16_q36["model"]["attention"] == "gdn" and fp16_q36["model"]["weight_dtype"] == "fp16"
    dsv4_rt = sim_bridge.export_sim_case(sim_bridge.export_sim_case({}, model="deepseek-v4-flash", chip="a5"))
    assert dsv4_rt["model"]["quant"]["name"] == "fp8_dynamic+mxfp4_experts"
    no_lp = {"machine": fp16_q36["machine"], "model": {"name": "inline-test", "layers": 2, "hidden_size": 1024, "num_heads": 8, "num_kv_heads": 8, "head_dim": 128, "intermediate_size": 2048, "vocab_size": 32000, "attention": "gqa", "ffn": "moe", "num_experts": 8, "top_k": 2, "moe_intermediate_size": 512, "weight_dtype": "fp16"}, "workload": fp16_q36["workload"], "runtime": {"parallel": {"tp": 1, "dp": 1, "ep": 1, "pp": 1}}, "slo": fp16_q36["slo"]}
    assert sim_bridge.export_sim_case(no_lp)["model"]["hidden_size"] == 1024 and sim_bridge.export_sim_case(no_lp, quant="w4a8")["model"]["quant"]["expert_weight_format"] == "int4"
    assert sim_bridge.export_sim_case({"provenance": {"source": "host on Ascend950DT_9581 node"}})["machine"]["sku"] == "Ascend950DT_9581"
    assert sim_bridge.export_sim_case({"provenance": {"source": "host on Ascend910B4-1 node"}})["machine"]["sku"] == "Ascend910B4-1"
    assert sim_bridge.export_sim_case({"model_name": "Qwen3-30B-A3B-W8A8"}, chip="a3", quant="none")["model"]["weight_dtype"] == "bf16"
    assert 512 in sim_bridge.export_sim_case({"env": {"SPEC_K": "3"}}, model="qwen3-30b-a3b", chip="a3", batch_size=128, graph_mode="aclgraph")["runtime"]["graph_capture_keys"]
    assert sim_bridge.export_sim_case({"schema_version": "mindie-profile-summary/1", "step_accounting": {"wall_ms_p50": 15.0}})["runtime"]["metadata"]["observed_profile"]["step_time_ms"] is None
    with pytest.raises(sim_bridge.ProfilerUsageError, match="standalone_draft_requires_target_model"): sim_bridge.export_sim_case({"env": {"SPEC_K": "3"}}, model="kimi-k3-dspark", chip="a3")
    with pytest.raises(sim_bridge.ProfilerUsageError, match="unsupported or unrecognized quantization"): sim_bridge.export_sim_case({}, model="qwen3.6-27b", chip="a3", quant="int3_unknown")
    with pytest.raises(sim_bridge.ProfilerUsageError, match="cannot scan directory"): sim_bridge._walk_err(PermissionError("permission denied"))
    bm_with_model = sim_bridge.export_sim_case({"model_name": "Qwen3-30B-A3B", "npu_type": "A3", "tensor_parallel_size": 4, "concurrency": 8, "step_time_ms": 12.5, "tpot_client_ms": {"median": 6.2}})
    assert bm_with_model["runtime"]["metadata"]["profiler_provenance"]["source_kind"] == "benchmark_summary" and bm_with_model["runtime"]["parallel"]["tp"] == 4 and bm_with_model["runtime"]["metadata"]["observed_profile"]["step_time_ms"] == pytest.approx(12.5)
    assert sim_bridge.export_sim_case({"schema_version": "mindie-profile-summary/1", "top_hotspot_kernels": [{"kernel_name": "hcom", "share_of_busy_pct": 25.0, "execution_engine": "hccl"}]})["runtime"]["metadata"]["observed_profile"]["cube_share"] is None
    int8_case = sim_bridge.export_sim_case({}, model="qwen3.6-27b", chip="a3", quant="w8a8")
    sim_bridge.export_sim_case(int8_case, quant="fp16")
    assert int8_case["model"]["quant"]["weight_format"] == "int8"
    kimi_cmd = tmp_path / "kimi_cmd.sh"
    kimi_cmd.write_text("vllm serve /weights/kimi-k3 --tensor-parallel-size 8 --enable-expert-parallel --speculative-config '{\"model\":\"/weights/kimi-k3-dspark\",\"num_speculative_tokens\":3}'\n", encoding="utf-8")
    assert sim_bridge.export_sim_case(kimi_cmd, chip="a3")["runtime"]["metadata"]["profiler_provenance"]["extracted_model"] == "kimi-k3"
    aiv_dir = tmp_path / "aiv_comm"
    aiv_dir.mkdir()
    (aiv_dir / "op_statistic.csv").write_text("OP Type,Core Type,Count,Total Time(us)\nHcomAllReduce,AI_VECTOR_CORE,10,500\nReshape,AI_CPU,10,100\n", encoding="utf-8")
    assert sim_bridge.export_sim_case(aiv_dir)["runtime"]["metadata"]["hccl_op_expansion_mode"] == "aiv"
    no_sim_proc = subprocess.run([sys.executable, "-I", "-S", "-c", f"import sys,json; sys.path.insert(0,{str(ROOT)!r}); from mindie_profiler.sim_bridge import export_sim_case; print(json.dumps(export_sim_case({{}},model='qwen3.6-27b')))"], capture_output=True, text=True, timeout=10, check=True)
    _assert_schema_valid(json.loads(no_sim_proc.stdout))


