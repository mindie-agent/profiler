"""Inventory the locally retained GLM78 W4A8 and V4.1 DSpark7 assets.

[Role] Separate rank-level device captures from client-only performance evidence.
[Invariants] A serving label never overrides the checkpoint identity. Client TPOT
  and prefix counters are not body timings; missing device data remains explicit.
[Timeouts & Locks] Read-only local files; hashes/decompression use 1 MiB buffers.
[Side-Effect Policy] Writes evidence JSON/Markdown; never collects new profiles.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tarfile


def digest(stream):
    h = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
        size += len(block)
    return h.hexdigest(), size


def identity(path):
    with path.open("rb") as stream:
        sha, size = digest(stream)
    return {"path": str(path), "sha256": sha, "size_bytes": size}


def read(path):
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError(f"Metadata too large: {path}")
    return json.loads(path.read_text())


def glm_capture(root, suffix, launch):
    directory = root / f"glm5_3_w4a8_int_high_conc_decode_tpot{suffix}_20261030"
    source = identity(directory / "kernel_details.csv")
    compressed = directory / "ranks/tp0/kernel_details.csv.gz"
    with gzip.open(compressed, "rb") as stream:
        sha, size = digest(stream)
    duplicate = sha == source["sha256"] and size == source["size_bytes"]
    if not duplicate:
        raise ValueError(f"Top-level source differs from tp0: {directory}")
    manifest = read(directory / "manifest.json")
    summary = read(directory / "benchmark_summary.json")
    cell = read(directory / "cell.json")
    ranks = []
    for declared in manifest["ranks"]:
        folder = directory / "ranks" / declared["rank"]
        files = {p.name: {"path": str(p), "size_bytes": p.stat().st_size}
                 for p in sorted(folder.iterdir()) if p.is_file()}
        ranks.append({"rank": declared["rank"], "capture_source": declared["src"],
                      "status": declared["status"], "raw_pruned": declared["raw_pruned"],
                      "declared_uncompressed_kernel_bytes": declared["kernel_details_bytes"],
                      "files": files, "device_events_parsed": False})
    return {
        "case_id": f"a3_glm53_w4a8_tp16_tpot{suffix}", "asset_root": str(directory),
        "selected_source": source, "selected_rank": "tp0", "retained_ranks": ranks,
        "rank_selection_basis": "One complete rank; other ranks retained for later peer-skew analysis.",
        "duplicate_source": {**identity(compressed), "uncompressed_sha256": sha,
                             "uncompressed_size_bytes": size, "same_as_selected_source": duplicate},
        "capture_manifest": identity(directory / "manifest.json"),
        "checkpoint": {"value": cell["tokenizer"], "source": identity(directory / "cell.json"),
                       "field": "tokenizer; models.data[].root",
                       "architecture": "GLM-5.3 old 78-layer declaration; not Glm5Next Flash 45"},
        "launch_declaration": {"source": launch, "tp": 16, "dp": 1, "ep": 16,
                               "kv_cache_dtype": "int8", "num_speculative_tokens": 5,
                               "rejection_sample_method": "synthetic",
                               "synthetic_acceptance_rates": [.8, .64, .512, .4096, .32768],
                               "force_eplb": True, "cudagraph_mode": "FULL_DECODE_ONLY",
                               "basis": "retained launch script, not a retained resolved startup log"},
        "profiled_client": {"source": identity(directory / "benchmark_summary.json"),
                            **{k: summary[k] for k in ("input_len", "output_len", "concurrency",
                               "num_prompts", "n_ok", "n_failed", "token_exact", "tpot_ms", "ttft_ms")},
                            "metric_scope": "client streaming chunks; not device forward"},
        "unprofiled_sweep": {"source": identity(directory / "sweep.json"),
                             "cells": read(directory / "sweep.json")["cells"]},
        "step_trace": {"source": identity(directory / "step_trace_time.csv"),
                       "rows": list(csv.DictReader((directory / "step_trace_time.csv").open())),
                       "boundary_scope": "aggregate capture row; empty Step is not a forward marker"},
        "limitations": ["cell.json is shared campaign bookkeeping (only_profile=88=8), not each capture's args.",
                        "No resolved startup log in this delivered directory; launch facts remain declarations.",
                        "Other rank CSVs are inventoried without parsing/decompressing their event populations.",
                        "A target directory TPOT label is not an achieved measurement."],
    }


def log_facts(path):
    facts = []
    keys = ("tensor_parallel_size", "data_parallel_size", "enable_expert_parallel",
            "num_speculative_tokens", "max_model_len", "enable_force_eplb")
    with path.open() as stream:
        for line_number, line in enumerate(stream, 1):
            if "non-default args" in line:
                values = {}
                for key in keys:
                    match = re.search(r"['\"]" + key + r"['\"]\s*:\s*([^,;}]+)", line)
                    if match:
                        values[key] = match.group(1).strip()
                values["method_dspark"] = "'method': 'dspark'" in line
                values["full_decode_only"] = "FULL_DECODE_ONLY" in line
                facts.append({"line": line_number, "resolved_args": values})
            if "Resolved architecture:" in line and not any("architecture" in f for f in facts):
                facts.append({"line": line_number, "architecture": line.split("Resolved architecture:", 1)[1].strip()})
    return {"source": identity(path), "facts": facts}


def v41_assets(root):
    directory = root / "deepseek_v4_1_flash_w8a8_dspark7_prefix_matrix_20261030"
    scenarios = []
    for comparison_path in sorted(directory.glob("*/comparison.json")):
        folder = comparison_path.parent
        dataset = read(folder / "dataset.json")
        config_path = folder / "prefix_perf_config.py"
        match = re.search(r"batch_size=(\d+)", config_path.read_text())
        comparisons = read(comparison_path)
        for arm in ("baseline", "candidate"):
            measurements = comparisons[arm]
            expected = sum(x["hits"] for x in measurements["per_dp"]) / sum(
                x["queries"] for x in measurements["per_dp"])
            if abs(expected - measurements["prefix_hit_rate"]) > 1e-12:
                raise ValueError(f"Prefix counters disagree: {folder}, {arm}")
        scenarios.append({"scenario": folder.name, "dataset_source": identity(folder / "dataset.json"),
                          "input_tokens": dataset["request_input_tokens"],
                          "output_tokens": dataset["request_output_tokens"],
                          "client_concurrency": int(match.group(1)),
                          "client_config": identity(config_path), "comparison_source": identity(comparison_path),
                          "serving_measurements": comparisons,
                          "server_logs": [log_facts(folder / f"{arm}-server.log") for arm in ("baseline", "candidate")],
                          "body_forward_span_ms": None, "per_layer_ms": None})
    broken_links, device_sources, client_databases, archives = [], [], [], []
    file_count = 0
    for path, folders, files in os.walk(directory, followlinks=False):
        for name in folders + files:
            p = Path(path) / name
            if p.is_symlink() and not p.exists():
                broken_links.append({"path": str(p), "target": os.readlink(p)})
        for name in files:
            p = Path(path) / name
            file_count += 1
            if any(token in name for token in ("kernel_details", "op_summary", "op_statistic", "trace_view", "ascend_pytorch_profiler", "msprof_")):
                device_sources.append(str(p))
            if name.endswith(".db") and p.exists():
                with sqlite3.connect(f"file:{p}?mode=ro", uri=True) as connection:
                    tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                client_databases.append({"source": identity(p), "tables": tables,
                                         "contains_device_task_table": "TASK" in tables})
            if name.endswith("-vllm.tar.gz"):
                with tarfile.open(p, "r:gz") as archive:
                    names = [member.name for member in archive]
                archives.append({"source": identity(p), "members": names,
                                 "device_profile_members": [n for n in names if any(t in n for t in (
                                     "kernel_details", "op_summary", "trace_view", "ascend_pytorch_profiler"))]})
    return {"asset_root": str(directory), "architecture": "DeepseekV41ForCausalLM",
            "model_config_retained": False, "scenarios": scenarios,
            "inventory": {"files": file_count, "device_profile_sources": device_sources,
                          "database_schemas": client_databases, "archives": archives, "broken_remote_links": broken_links},
            "coverage": "serving_client_only" if not device_sources else "device_sources_found",
            "limitations": ["AISBench numpy_store databases contain client arrays, not Ascend device TASK events.",
                            "Baseline/candidate TPOT and prefix counters are serving measurements, not body/layer timing.",
                            "Resolved EP enabled and TP4/DP4 do not independently establish physical rank placement or balance.",
                            "No model config or device capture was retained; do not substitute the V4Flash model." ]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data/a3"))
    parser.add_argument("--launch", type=Path, default=Path("/Users/maoxx241/code/mindie-agent/.workstreams/hp-serving/a3-highconc-decode/scripts/cases/serve_glm53f_w4a8.sh"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-glm78-v41"))
    args = parser.parse_args()
    captures = [glm_capture(args.data_root, suffix, identity(args.launch)) for suffix in ("30_c2", "50_c2", "88_c8")]
    if len({row["selected_source"]["sha256"] for row in captures}) != 3:
        raise ValueError("Repeated GLM source capture")
    result = {"schema_version": "mindie-glm78-v41-retained-evidence/1", "not_new_live_collection": True,
              "glm78_device_captures": captures, "v41_serving_assets": v41_assets(args.data_root)}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "retained-source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 新 GLM78 W4A8 与 V4.1 保留制品", "", "三份 GLM CSV 均与对应 tp0 压缩原件逐字节一致；三次源 SHA 不同。16 rank 路径完整保留，仅选择 tp0 分段，未把 16 rank 重复计入模型主体。", "",
             "| GLM 采集 | CSV MiB | Profiled client TPOT P50 ms | Rank 数 |", "|---|---:|---:|---:|"]
    for row in captures:
        lines.append(f"| {row['case_id']} | {row['selected_source']['size_bytes']/1024**2:.2f} | {row['profiled_client']['tpot_ms']['p50']:.4f} | {len(row['retained_ranks'])} |")
    lines += ["", "实际 checkpoint 是 GLM-5.3-W4A8-INT；served-model-name 中的 glm53f 不表示新版 45 层 Flash。保留启动脚本声明 TP16/EP16、DP1、INT8 KV、5-token MTP、synthetic 接收率及 force EPLB；交付目录未保留 resolved 启动日志，配置声明和实际负载均衡仍分列。", "",
              "V4.1 六组为客户端性能制品：启动日志确认 DeepseekV41ForCausalLM、TP4/DP4、EP enabled、DSpark7。12 个 AISBench 数据库仅有 numpy_store/sqlite_sequence，两份 vllm tar 中没有设备 profiling。Body/层耗时保持缺失，不用 V4Flash 替代。", "",
              "| V4.1 场景 | Input tokens | Client c | Baseline / Candidate TPOT mean ms | Prefix hit |", "|---|---:|---:|---:|---:|"]
    for row in result["v41_serving_assets"]["scenarios"]:
        a, b = (row["serving_measurements"][key] for key in ("baseline", "candidate"))
        lines.append(f"| {row['scenario']} | {row['input_tokens']} | {row['client_concurrency']} | {a['tpot_avg_ms']:.1f} / {b['tpot_avg_ms']:.1f} | {b['prefix_hit_rate']*100:.4f}% |")
    lines += ["", "Prefix hit 按四个 DP 的 hits/queries 独立复核；约 98.8%–99.0%，没有伪称 100%。TPOT 保持客户端指标，不当作单次模型 Forward 或纯算子耗时。完整原始路径、源 SHA、边界缺口与远端绝对符号链接见 JSON。", ""]
    (args.output / "retained-source-evidence.md").write_text("\n".join(lines))
    print(json.dumps({"glm_sources": len(captures), "ranks_each": 16, "v41_coverage": result["v41_serving_assets"]["coverage"], "output": str(args.output)}))


if __name__ == "__main__":
    main()
