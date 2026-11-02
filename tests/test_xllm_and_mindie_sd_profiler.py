"""Unit tests for xLLM and MindIE-SD profiler window detection and memory log parsing."""
from __future__ import annotations

from mindie_profiler.collect import check_profile_window, profile_window_from_serve_args
from mindie_profiler.memory_logs import parse_mindie_sd_logs, parse_xllm_logs, resolve_kv_log_measurement
from mindie_profiler.memory_profile import attribute_memory


def test_mindie_sd_command_detection_and_default_profiler_env_injection():
    env: dict[str, str] = {}
    inj = profile_window_from_serve_args(
        ["python3", "mindie_bench.py", "--model", "Wan2.2-T2V-14B"],
        endpoint="http://127.0.0.1:9999",
        execution_id="exec-sd",
        environ=env,
    )
    assert inj.enabled is True
    assert inj.framework == "mindie-sd"
    assert env["MINDIE_SD_PROFILER_ENABLE"] == "1"
    assert env["MINDIE_SD_PROFILER_WARMUP_STEPS"] == "2"
    assert check_profile_window(inj)["ok"] is True

    # Explicit --framework mindie-sd and xpu-perf-plugin are also recognized
    inj_plugin = profile_window_from_serve_args(
        ["xpu-perf-plugin", "--framework", "mindie-sd", "--profile_dir", "/tmp/sd_prof"],
        endpoint="http://127.0.0.1:9999",
        execution_id="exec-sd-plugin",
        environ={},
    )
    assert inj_plugin.framework == "mindie-sd"
    assert inj_plugin.profile_dir == "/tmp/sd_prof"

    # Regression [P0-1]: xllm with --profile_dir must NOT be misclassified as mindie-sd
    inj_xllm = profile_window_from_serve_args(
        ["xllm", "--model", "/models/qwen3", "--profile_dir", "/tmp/xllm_prof"],
        endpoint="http://127.0.0.1:9999",
        execution_id="exec-xllm-prof",
        environ={},
    )
    assert inj_xllm.framework == "xllm"
    assert inj_xllm.profile_dir == "/tmp/xllm_prof"


def test_parse_mindie_sd_logs_and_memory_attribution():
    log_text = (
        "Loading model weights took 14.0 GB\n"
        "DiTCache: total_steps=50, computed_steps=20, cached_steps=30, hit_rate=0.60\n"
        "VAE Peak Memory: 12.5 GB\n"
        "vae_peak_mb=12500, vae_tiles=16\n"
        "MindIE-SD NPU Memory: allocated=34.0 GB, reserved=38.5 GB\n"
    )
    parsed = parse_mindie_sd_logs(log_text)
    assert parsed["source"] == "mindie_sd_log"
    assert parsed["framework"] == "mindie-sd"
    assert parsed["total_steps"] == 50
    assert parsed["computed_steps"] == 20
    assert parsed["cached_steps"] == 30
    assert parsed["cache_hit_ratio"] == 0.60
    assert parsed["vae_tiles"] == 16
    assert parsed["vae_peak_bytes"] == 12_500_000_000.0
    assert parsed["allocated_bytes"] == 34_000_000_000.0
    assert parsed["reserved_bytes"] == 38_500_000_000.0

    resolved = resolve_kv_log_measurement(parsed)
    assert resolved is not None
    byte_val, unit, _raw, kind, _ref = resolved
    assert kind == "mindie_sd_log"
    assert unit == "B"
    assert byte_val == 12_500_000_000.0

    manifest = {
        "tp": 1,
        "dp": 1,
        "baseline_hbm": {"0": {"used_bytes": 1_000_000_000, "source_kind": "npu_smi", "is_peak": False}},
        "after_ready_hbm": {"0": {"used_bytes": 28_000_000_000, "source_kind": "npu_smi", "is_peak": False}},
        "after_infer_hbm": {"0": {"used_bytes": 28_100_000_000, "source_kind": "npu_smi",
                                  "measurement_kind": "measured_peak", "is_peak": True}},
        "msprof_components": {"HCCL": {"bytes": 100_000_000}, "RUNTIME": {"bytes": 50_000_000}},
        "mindie_sd_log": log_text,
    }
    attr = attribute_memory(manifest)
    comps = {item["key"]: item for item in attr["devices"][0]["components"]}
    assert comps["kv_cache"]["source"]["kind"] == "mindie_sd_log"
    assert comps["kv_cache"]["bytes"] == 12_500_000_000.0

    # Regression [P2-2]: generic log_text with TaylorSeer / vae_peak_mb= also attributes MindIE-SD memory
    attr_generic = attribute_memory({
        **{k: v for k, v in manifest.items() if k != "mindie_sd_log"},
        "log_text": "Loading model weights took 14.0 GB\nTaylorSeer: total_steps=50, computed_steps=20\nvae_peak_mb=10000\n",
    })
    comps_generic = {item["key"]: item for item in attr_generic["devices"][0]["components"]}
    assert comps_generic["kv_cache"]["source"]["kind"] == "mindie_sd_log"
    assert comps_generic["kv_cache"]["bytes"] == 10_000_000_000.0


def test_parse_xllm_logs_roundtrip():
    xllm_parsed = parse_xllm_logs(
        "shared_vmm_allocator: allocated_pages=100, high_watermark_pages=128, total_pages=256, page_size=2097152\n"
    )
    assert xllm_parsed["xtensor_high_watermark_bytes"] == 128 * 2097152
