"""Inspect newly delivered A5 V4.1 TP1/DP8/EP8 captures without segmenting them.

[Role] Pin device sources, measured client windows and resolved deployment facts.
[Invariants] These are APC-off A5 captures, not the A3 DSpark7 prefix campaign.
  N/A attention tensors remain missing; native names do not prove a layer ABI.
[Timeouts & Locks] Stream SHA256; inspect at most 160 CSV records per capture.
[Side-Effect Policy] Local reads and evidence JSON/Markdown writes only.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
from pathlib import Path
import re

from inspect_glm78_v41_assets import identity, read


def build(data_root, output):
    campaign = data_root / "dsv41_dp8ep8_sweep_20261030"
    log = campaign / "serve.log"
    resolved = []
    for line_number, line in enumerate(log.open(), 1):
        if "non-default args" in line or "Initializing" in line:
            values = {}
            for key in ("model", "tensor_parallel_size", "data_parallel_size", "enable_expert_parallel",
                        "max_model_len", "enable_prefix_caching", "enable_force_eplb", "quantization"):
                match = re.search(r"['\"]?" + key + r"['\"]?\s*[:=]\s*([^,;}]{1,150})", line)
                if match:
                    values[key] = match.group(1).strip()
            if values:
                resolved.append({"line": line_number, "values": values})
        if "Resolved architecture:" in line:
            resolved.append({"line": line_number, "architecture": line.split("Resolved architecture:", 1)[1].strip()})
    sources = []
    for tag in ("5ms_c1", "10ms_c8", "30ms_c64"):
        directory = data_root / f"deepseek_v4_1_flash_fp8_high_conc_decode_tpot{tag}_20261030"
        source = identity(directory / "kernel_details.csv")
        summary_path = directory / "benchmark_summary.json"
        summary = read(summary_path)
        original_summary = campaign / f"profile_tpot{tag}.json"
        duplicate_summary = identity(original_summary)["sha256"] == identity(summary_path)["sha256"]
        if not duplicate_summary:
            raise ValueError(f"Profile summary alias differs: {tag}")
        with (directory / "kernel_details.csv").open() as stream:
            reader = csv.DictReader(stream)
            sample = list(itertools.islice(reader, 160))
        landmarks = []
        seen = set()
        for line_number, row in enumerate(sample, 2):
            kind = row["Type"]
            if kind in seen or kind not in ("HcPre", "HcPost", "RmsNorm", "MqsmlaKernel___call__",
                                           "TransposeQuantBatchMatMul", "KvCompressEpilogV2"):
                continue
            seen.add(kind)
            landmarks.append({"csv_line": line_number, **{key: row.get(key) for key in (
                "Type", "Name", "Model ID", "Device_id", "Stream ID", "Input Shapes", "Output Shapes",
                "Input Data Types", "Output Data Types")}})
        sweep_path = directory / f"sweep_c{summary['concurrency']}.json"
        sweep = read(sweep_path)
        sources.append({
            "case_id": f"a5_v41_fp8_tp1_dp8_ep8_tpot{tag}", "capture_directory": str(directory),
            "source": source, "trace_origin": (directory / "trace_dir.txt").read_text().strip(),
            "selected_physical_rank": "dp0_pp0_tp0_dcp0_ep0_rank0",
            "other_rank_profiles_delivered": False, "model_case_path": None,
            "profile_summary": identity(summary_path), "original_summary": identity(original_summary),
            "summary_alias_verified": duplicate_summary,
            "profiled_client": {key: summary.get(key) for key in (
                "mode", "model", "prefix_len", "output_len", "concurrency", "n_ok", "n_failed",
                "tpot_tok_ms", "step_ms", "tokens_per_chunk", "profile_window", "engine_config",
                "steady_state", "steady_state_confirmed", "profile_start_resp", "profile_stop_resp")},
            "unprofiled_sweep": {"source": identity(sweep_path), "tpot_tok_ms": sweep.get("tpot_tok_ms"),
                                 "step_ms": sweep.get("step_ms"), "concurrency": sweep.get("concurrency")},
            "step_trace": {"source": identity(directory / "step_trace_time.csv"),
                           "rows": list(csv.DictReader((directory / "step_trace_time.csv").open()))},
            "operator_inventory": {"source": identity(directory / "op_statistic.csv"),
                                   "scope": "full selected capture; not a body-only population",
                                   "rows": list(csv.DictReader((directory / "op_statistic.csv").open()))},
            "bounded_tensor_landmarks": landmarks, "sampled_csv_rows": len(sample),
            "body_forward_span_ms": None, "per_layer_ms": None,
            "unresolved": ["Exact source-bound V4.1 model declaration is pending; do not substitute V4Flash.",
                           "MqsmlaKernel___call__ exports N/A tensors; do not invent an attention ABI.",
                           "Client c and DP8 do not prove how many requests are active on this rank.",
                           "Delivered source is rank0; peer readiness and expert balance are not measured by this inventory."]})
    result = {"schema_version": "mindie-v41-dp8-source-evidence/1", "not_new_live_collection": True,
              "campaign": str(campaign), "startup": {"source": identity(log), "facts": resolved},
              "launch": identity(campaign / "cfg/hc_serve_dp8.sh"),
              "launch_environment": identity(campaign / "launch.env"),
              "cases": sources, "unique_sources": len({row['source']['sha256'] for row in sources}),
              "full_csv_event_scans": 0, "source_identity_hashing_is_not_event_parsing": True,
              "campaign_boundary": "A5 FP8 TP1/DP8/EP8, APC disabled, no speculative-config in launch; distinct from A3 DSpark7 prefix matrix."}
    output.mkdir(parents=True, exist_ok=True)
    (output / "retained-source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# A5 V4.1 TP1/DP8/EP8 本地新采集", "", "三份完整 kernel CSV 已落盘，源 SHA 与 DP0/rank0 采集目录已固定。启动日志/engine config 确认 FP8、TP1/DP8/EP8、force EPLB、APC 关闭；没有把 A3 DSpark7 与 Prefix 99% 的条件套用到本批。", "",
             "| 采集 | CSV MiB | Client c | Profiled token TPOT P50 ms | Unprofiled token TPOT P50 ms |", "|---|---:|---:|---:|---:|"]
    for row in sources:
        profiled, sweep = row["profiled_client"], row["unprofiled_sweep"]
        lines.append(f"| {row['case_id']} | {row['source']['size_bytes']/1024**2:.2f} | {profiled['concurrency']} | {profiled['tpot_tok_ms']['p50']:.4f} | {sweep['tpot_tok_ms']['p50']:.4f} |")
    lines += ["", "5 ms / 10 ms 是目标标签，实际并未达到。Profile 仅在队列空且所有客户端发出首 token 后打开约 2 秒；客户端 TPOT 仍与设备主体耗时不同。", "",
              "每源只读取前 160 个事件寻找 ABI 线索，尚未做完整事件分段。HcPre/HcPost 有真实张量描述；MqsmlaKernel___call__ 的输入/输出 shape/dtype 在原 CSV 均为 N/A。缺失不能用 V4 的 ABI 或形状填补。后续应使用独立 V4.1 模型声明及整体结构边界验证，未获得这些证据前 Body/层耗时保持空值。", ""]
    (output / "retained-source-evidence.md").write_text("\n".join(lines))
    print(json.dumps({"sources": len(sources), "unique_sources": result["unique_sources"], "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data/a5"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-v41-dp8"))
    args = parser.parse_args()
    build(args.data_root, args.output)
