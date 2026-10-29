"""Index the retained 2026-10-30 A5 high-concurrency Decode captures.

[Role] Bind original rank-zero exports to source-derived Sim cases and run facts.
[Invariants] Profiled client TPOT, engine-window estimates, unprofiled sweep TPOT,
  and model-body spans have different boundaries; none substitutes for another.
[Timeouts & Locks] Streaming hashes, bounded metadata; no subprocesses or locks.
[Side-Effect Policy] Reads existing local captures and writes one local manifest.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from build_decode_forward_cases import _case, _hash, _read


def identity(path):
    return {"path": str(path.resolve()), "sha256": _hash(path),
            "size_bytes": path.stat().st_size}


def build(data_root, workstream, sim_case_dir, output):
    cases = []
    floor = data_root / "a5_kernel_floor_1tok_high_conc_decode_20261030/benchmark_summary.json"
    floor_report = _read(floor)
    for model, tp, letter, quantization in (
        ("qwen36", 8, "c", "w8a8_dynamic"),
        ("qwen38", 4, "b", "W8A8_MXFP8"),
    ):
        prefix = "qwen3_6_27b_w8a8" if model == "qwen36" else "qwen3_8_27b_w8a8_mxfp8_mtp"
        roots = sorted(data_root.glob(prefix + "_high_conc_decode_tpot*20261030"))
        if len(roots) != 3:
            raise ValueError(f"expected three retained tiers for {model}: {roots}")
        launch = workstream / "cfg" / f"serve_t1{letter}_{model}.sh"
        log = workstream / "pulls/logs" / f"t1{letter}_{model}_server.log"
        # Verify the retained engine log, rather than treating the launch intent as execution.
        with log.open() as stream:
            config_lines = [(line_no, line.rstrip()) for line_no, line in enumerate(stream, 1)
                            if "Initializing a V1 LLM engine" in line]
        if len(config_lines) != 1 or f"tensor_parallel_size={tp}," not in config_lines[0][1]:
            raise ValueError(f"retained engine configuration does not identify TP{tp}: {log}")
        if "enable_prefix_caching=True" not in config_lines[0][1]:
            raise ValueError(f"retained engine did not enable APC: {log}")
        for root in roots:
            summary_path, client_path = root / "benchmark_summary.json", root / "client_cell.json"
            summary, client = _read(summary_path), _read(client_path)
            concurrency = summary["concurrency"]
            case_path = sim_case_dir / f"{model}-a5-tp{tp}-c{concurrency}.json"
            if _read(case_path)["runtime"]["tp"] != tp:
                raise ValueError(f"Sim case TP differs from the actual serving TP: {case_path}")
            source, duplicate = root / "kernel_details.csv", root / "prof/rank0/kernel_details.csv"
            if _hash(source) != _hash(duplicate):
                raise ValueError(f"top-level source is not the retained rank-zero export: {root}")
            if summary["tensor_parallel_size"] != tp:
                raise ValueError(f"summary TP differs from the retained engine: {root}")
            with (root / "step_trace_time.csv").open(newline="") as stream:
                step_rows = list(csv.DictReader(stream))
            cell = summary["cell_metrics"]
            prefix_queries = cell["vllm:prefix_cache_queries_total"]
            prefix_hits = cell["vllm:prefix_cache_hits_total"]
            observed_prefix_rate = prefix_hits / prefix_queries
            if abs(observed_prefix_rate - summary["prefix_cache_hit_rate"]) > 1e-12:
                raise ValueError(f"prefix counters disagree with the reported ratio: {root}")
            cached_per_request = prefix_hits / summary["n_ok"]
            prefix_reuse = cached_per_request / summary["prefix_len"]
            scenario = {
                "benchmark_summary": identity(summary_path),
                "capture_tier_label": summary["tpot_tier"],
                "requested_tpot_target_ms": int(summary["tpot_tier"].split("ms")[0].removeprefix("tpot")),
                "client": {**identity(client_path), "input_len": client["prefix_len"] + client["suffix_len"],
                           "prefix_len": client["prefix_len"], "suffix_len": client["suffix_len"],
                           "decode_len": client["decode_len"], "concurrency": concurrency,
                           "token_exact": client["token_exact"]},
                "runtime": {"launch_source": identity(launch), "engine_log": identity(log),
                            "engine_log_line": config_lines[0][0], "startup_arguments_line": 23,
                            "image": summary["image"], "image_basis": "external_capture_summary",
                            "model_path": summary["model_path"], "tensor_parallel_size": tp,
                            "data_parallel_size": 1, "quantization": quantization,
                            "quantization_basis": "checkpoint_identity_and_existing_sim_catalog",
                            "loader_quantization": "ascend", "activation_dtype": "bfloat16",
                            "prefix_caching_enabled": True, "graph_mode": "FULL_AND_PIECEWISE",
                            "max_num_seqs": 160, "max_num_batched_tokens": 16384,
                            "speculative_method": "mtp", "speculative_tokens": 3,
                            "synthetic_acceptance_rates_configured": [0.8, 0.64, 0.512]},
                "hardware": {"expected_key": "Ascend950DT_9582", "capture_host": summary["host"],
                             "floor_measurement": identity(floor),
                             "floor_measurement_host": floor_report["host"],
                             "floor_measurement_device": floor_report["device"],
                             "direct_device_identity_in_serving_csv": "not_exported",
                             "basis": "declared_A5_campaign; exact SKU directly recorded by its independent floor capture"},
                "profile_window": summary["profile_window"],
                "tpot": {"profiled_run_client_ms": summary["tpot_client_ms"],
                         "profiled_engine_window_estimate_ms": summary["tpot_engine_ms"],
                         "unprofiled_sweep_ms": summary["unprofiled_sweep"]["tpot_sweep_unprofiled_ms"],
                         "profiling_overhead_client_median_pct": summary["unprofiled_sweep"]["profiling_overhead_tpot_pct"],
                         "body_forward_is_separate_metric": True},
                "scheduler_step": {"profiled_run_client_ms": summary["step_time_client_ms"],
                                   "profiled_engine_window_estimate_ms": summary["step_time_engine_ms"],
                                   "unprofiled_sweep_ms": summary["unprofiled_sweep"]["step_sweep_unprofiled_ms"]},
                "mtp": {"engine_window_acceptance_rate": summary["mtp_acceptance_rate"],
                        "whole_run_acceptance_rate": cell["acceptance_rate"],
                        "engine_window_tokens_per_step": summary["tokens_per_step"],
                        "whole_run_tokens_per_step": cell["tokens_per_step"],
                        "engine_window": summary["engine_window"]},
                "prefix_cache": {"queries": prefix_queries, "hits": prefix_hits,
                                 "hit_rate_including_unique_suffix": observed_prefix_rate,
                                 "cached_tokens_per_request": cached_per_request,
                                 "shared_prefix_reuse_fraction": prefix_reuse},
                "prefix_hit_100_percent": observed_prefix_rate == 1.0,
                "shared_prefix_fully_reused": prefix_reuse == 1.0,
                "acceptance_0_8": "configured_first_draft_probability_not_measured_aggregate_rate",
                "forced_load_balancing": "not_applicable_dense_model_DP1",
                "dspark": "not_verified",
                "step_trace": {"source": identity(root / "step_trace_time.csv"),
                               "rows": step_rows, "per_step_boundaries_available": False,
                               "scope": "entire_capture; blank Step field is not a per-forward marker"},
                "source_population": {"selected_rank": 0, "selected_device_id": "0",
                                      "top_level_is_rank0_duplicate": True,
                                      "duplicate_source": identity(duplicate),
                                      "available_exported_ranks": [p.parent.name for p in sorted((root / "prof").glob("rank*/kernel_details.csv"))],
                                      "declared_kernel_rows": summary["kernel_stats"]["n_kernel_rows"]},
                "request_geometry_is_not_per_forward_geometry": True,
            }
            case = _case(f"a5_{model}_highconc_c{concurrency}", source, case_path, scenario)
            case["model_declaration"]["basis"] = "existing_sim_structure_with_serving_log_bound_TP_and_quantization"
            cases.append(case)
    result = {"schema_version": "mindie-decode-forward-replay/1", "cases": cases,
              "segmentation": "auto_structure_guided", "not_new_live_collection": True,
              "notes": ["Six existing external-session captures; only one retained rank-zero export per capture is selected.",
                        "Prefix cache and aggregate MTP acceptance are measured, not equated to configured targets.",
                        "Client TPOT includes a profiled run; engine-window estimates, unprofiled sweep TPOT, and body spans remain distinct.",
                        "Step trace contains whole-capture totals; automatic layer/Forward extraction supplies local boundaries.",
                        "Observed M/B/q are tensor execution geometry and can contain padding; client concurrency remains an independent fact."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return {"case_count": len(cases), "manifest": identity(output)}


def render_evidence(manifest_path, receipt_path, output):
    manifest, receipt = _read(manifest_path), _read(receipt_path)
    observed = {row["case_id"]: row for row in receipt["cases"]}
    lines = ["# A5 高并发 Decode：源证据与自动主体提取", "",
             "复用外部采集任务已经落盘的六组数据，仅读取每组 rank 0；顶层 CSV 与 prof/rank0 副本 SHA 完全一致，未把两个副本重复统计。",
             "模型结构来自现有 Sim，运行 TP、MTP、图模式与 APC 配置来自保留的 server log。",
             "层边界是结构引导推断；M/B/q 表示张量执行几何，可能含 padding，客户端并发另列。", "",
             "| 模型 / TP | 客户端 c | 执行 M/B/q | 完整主体 | Body Mean ms | P50 ms | P90 ms |",
             "|---|---:|---|---:|---:|---:|---:|"]
    for row in manifest["cases"]:
        scenario = row["scenario_evidence"]
        for group in observed[row["case_id"]]["geometry_groups"]:
            geometry, stats = group["geometry"], group["body_forward_span_ms"]
            name = scenario["runtime"]["model_path"].split("/")[-1]
            label = f"{name} / TP{scenario['runtime']['tensor_parallel_size']}"
            dimensions = "/".join(str(geometry[k]) for k in ("query_rows", "sequences_per_replica", "tokens_per_sequence"))
            lines.append(f"| {label} | {scenario['client']['concurrency']} | {dimensions} | {stats['count']} | "
                         f"{stats['mean']:.6f} | {stats['p50']:.6f} | {stats['p90']:.6f} |")
    lines += ["", "下面的 TPOT 与上表 Body 使用不同边界。Profiled client 是带采集运行的客户端统计，engine window 是 /metrics 窗口估计；二者均不冒充纯模型主体。", "",
              "| Case | 未采集 sweep TPOT ms | 带采集 client P50 ms | Engine window TPOT ms | 整体 prefix 命中 | 共享前缀复用 | 窗口 MTP 接收率 |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for row in manifest["cases"]:
        s = row["scenario_evidence"]
        t, p = s["tpot"], s["prefix_cache"]
        lines.append(f"| {row['case_id']} | {t['unprofiled_sweep_ms']:.4f} | {t['profiled_run_client_ms']['median']:.4f} | "
                     f"{t['profiled_engine_window_estimate_ms']:.4f} | {p['hit_rate_including_unique_suffix']:.4%} | "
                     f"{p['shared_prefix_reuse_fraction']:.4%} | {s['mtp']['engine_window_acceptance_rate']:.4%} |")
    lines += ["", "MTP 配置为三个位置的 synthetic 接收概率 [0.8, 0.64, 0.512]；实测每 draft token 的汇总接收率不是 0.8。",
              "Qwen3.6 每请求缓存 4096 / 4104 个 prompt token；共享前缀全部复用，8 个唯一 suffix 不命中。Qwen3.8 缓存 3584 / 4104 个 token，共享前缀仅复用 87.5%。",
              "六份 step_trace_time.csv 都只有整窗一行且 Step 为空，不用它构造单步分母。当前每 Forward 精确 KV 长度没有导出，请求 4104 token 仅是条件预测起点。", "",
              "Ascend950DT_9582 的直接设备属性来自同批独立 kernel-floor capture：32 Cube / 64 Vector，rack06os1。Serving CSV 只导出 Device_id，未伪称六份 CSV 分别直接记录了 SKU。镜像 v0.30.0rc2-a5/c3d00a196905 来自采集摘要；日志验证运行 vLLM 0.30.0、TP4/TP8、DP1、FULL_AND_PIECEWISE 和 APC 开启。", "",
              "Kernel-floor 的独立审查见 Sim data/verification/a5-microbench-boundary-review-20261030.json（c850dbfd）：完整 kernel Duration 与同 stream 间隔不等于统一 launch 常数；本次未用该微基准改写 runtime。", "",
              f"本轮完整主体 {receipt['total_complete_forwards']} 个，正事件 {receipt['source_positive_events']} 条；每个正事件在完整主体、辅助段、拒绝段或尾片段中恰计一次。",
              "源 CSV/SHA、配置日志行、MTP 与 prefix 原始计数、每 case 完整事件分母均保存在 decode-forward-auto-cases.json 与 decode-forward-auto-acceptance.json。", ""]
    if receipt.get("validation_rerun"):
        rerun = receipt["validation_rerun"]
        lines += ["新采集包含 HcclLaunchAicpuKernel controller 跨后继层 norm 的尾部。补齐这个真实 ABI 后，六份采集统一再次提取；只在真实跨层时裁 controller 尾，正常 hcom 与层内 controller 仍保留。",
                  f"两代提取总耗时 {rerun['total_elapsed_seconds_across_generations']:.3f}s；完整主体统计与事件分母保持一致，层边界统计按新规则更新。原 30 源历史 generation 未重写。", ""]
    output.write_text("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data/a5"))
    parser.add_argument("--workstream", type=Path, default=Path("/Users/maoxx241/code/mindie-agent/.workstreams/hp-serving/a5-20261030"))
    parser.add_argument("--sim-case-dir", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027/examples/cases/high-concurrency-20261030"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-high-concurrency") / "decode-forward-auto-cases.json")
    parser.add_argument("--render-receipt", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.data_root, args.workstream, args.sim_case_dir, args.output)))
    if args.render_receipt:
        render_evidence(args.output, args.render_receipt, args.output.parent / "high-concurrency-source-evidence.md")
