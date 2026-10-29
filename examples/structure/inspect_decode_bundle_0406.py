"""Inventory the 04:06 local Decode bundle without repeating event parsing.

[Role] Give model-input owners a source-pinned, per-campaign configuration queue.
[Invariants] Resolved logs, launch intent and measured counters are distinct.
  A 4-layer checkpoint is not a complete 93-layer model; unknown rates are null.
[Timeouts & Locks] Stream source hashes; bounded JSON metadata, no raw event scan.
[Side-Effect Policy] Reads local retained captures and writes metadata reports.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re

from inspect_glm78_v41_assets import identity, read


def log_metadata(path):
    facts = []
    for number, line in enumerate(path.open(), 1):
        if "Resolved architecture:" in line:
            facts.append({"line": number, "architecture": line.split("Resolved architecture:", 1)[1].strip()})
        if "non-default args" not in line and "Initializing" not in line:
            continue
        found = {}
        for key in ("model", "tensor_parallel_size", "data_parallel_size", "enable_expert_parallel",
                    "enable_force_eplb", "enable_prefix_caching", "num_speculative_tokens", "quantization"):
            match = re.search(r"['\"]?" + key + r"['\"]?\s*[:=]\s*([^,;}]{1,180})", line)
            if match:
                found[key] = match.group(1).strip()
        for key in ("synthetic_acceptance_rates",):
            match = re.search(r"['\"]?" + key + r"['\"]?\s*[:=]\s*(\[[^\]]*\])", line)
            if match:
                found[key] = match.group(1)
        match = re.search(r"CUDAGraphMode\.([A-Z_]+)", line)
        if match:
            found["cudagraph_mode"] = match.group(1)
        if found:
            facts.append({"line": number, "resolved_values": found})
    return {"source": identity(path), "facts": facts}


def benchmark(path):
    raw = read(path)
    if "summary" in raw:
        summary = raw["summary"]
        requests = raw["requests"]
        prompts = sorted({row["prompt_tokens"] for row in requests if row.get("prompt_tokens") is not None})
        outputs = sorted({row["completion_tokens"] for row in requests if row.get("completion_tokens") is not None})
        return {"source": identity(path), "schema": "summary_delta_requests", "summary": summary,
                "observed_prompt_tokens": prompts, "observed_completion_tokens": outputs,
                "metric_delta": raw["delta"], "client_concurrency": summary["concurrency"],
                "profiled_token_tpot_p50_ms": summary.get("tpot_true_p50_ms"),
                "request_count": len(requests)}
    if "tpot_tok_ms" in raw:
        requests = raw["per_request"]
        return {"source": identity(path), "schema": "token_tpot_profile_window",
                "summary": {key: value for key, value in raw.items() if key != "per_request"},
                "observed_prompt_tokens": sorted({row["prompt_tokens"] for row in requests}),
                "observed_completion_tokens": sorted({row["completion_tokens"] for row in requests}),
                "client_concurrency": raw["concurrency"],
                "profiled_token_tpot_p50_ms": raw["tpot_tok_ms"]["p50"], "request_count": len(requests)}
    return {"source": identity(path), "schema": "flat_per_request", "summary": {
        key: value for key, value in raw.items() if key not in ("per_request", "itl_ms_all_tokens")},
            "observed_prompt_tokens": raw["observed_prompt_tokens"],
            "observed_completion_tokens": raw["observed_completion_tokens"],
            "client_concurrency": raw["concurrency"], "profiled_token_tpot_p50_ms": raw["tpot_ms"]["p50"],
            "request_count": len(raw["per_request"])}


def capture(directory, group, deployment, template, parent_config_scope, *, metadata_directory=None):
    metadata_directory = metadata_directory or directory
    source = directory / "kernel_details.csv"
    if not source.exists():
        source = directory / "ranks/tp0/kernel_details.csv.gz"
    if not source.exists():
        raise FileNotFoundError(source)
    raw_manifest = metadata_directory / "manifest.json"
    ranks = []
    if raw_manifest.exists():
        manifest = read(raw_manifest)
        for row in manifest["ranks"]:
            p = metadata_directory / "ranks" / row["rank"] / "kernel_details.csv.gz"
            ranks.append({"rank": row["rank"], "raw_origin": row["src"], "status": row["status"],
                          "path": str(p), "size_bytes": p.stat().st_size})
    result = {"case_id": directory.name.removesuffix("_20261030"), "group": group,
              "source": identity(source), "capture_directory": str(directory),
              "benchmark": benchmark(metadata_directory / "benchmark_summary.json"),
              "deployment_evidence": deployment, "declared_template_candidate": str(template) if template else None,
              "required_model_input_scope": parent_config_scope,
              "source_bound_sim_case": None, "geometry": None,
              "retained_rank_sources": ranks, "selected_rank": "tp0" if ranks else "top_level_export_rank_unconfirmed",
              "full_event_scans": 0, "body_forward_span_ms": None,
              "step_trace": {"source": identity(directory / "step_trace_time.csv"),
                             "rows": list(csv.DictReader((directory / "step_trace_time.csv").open()))},
              "operator_summary": {"source": identity(directory / "op_statistic.csv"),
                                   "rows": list(csv.DictReader((directory / "op_statistic.csv").open())),
                                   "scope": "whole capture, not body-only"},
              "limitations": ["Client concurrency and prompt length do not establish per-rank execution geometry.",
                              "This manifest does not run a model or predict/fit cost.",
                              "Declared force EPLB is not a measured per-expert balance histogram."]}
    if raw_manifest.exists():
        result["capture_manifest"] = identity(raw_manifest)
    return result


def build(data_root, workspace, sim_root, output):
    hp = workspace / ".workstreams/hp-serving"
    a5_kimi_launch = hp / "glm53-hc/scripts/ws9/serve_kimi_k3_tp8.sh"
    a3_kimi_launch = hp / "a3-highconc-decode/w10/cases/serve_kimi_k3_w4a8_4layer.sh"
    glm_log = hp / "glm53-hc/raw/ws9/logs/serve-mtp.log"
    deployments = {
        "a5_kimi_tp8_ep8": {"launch_source": identity(a5_kimi_launch), "resolved_startup": None,
            "configured": {"checkpoint": "/mnt/weight/Kimi-K3-expert16-top8-100B-CountBenchQA",
                           "tp": 8, "dp": 1, "ep": 8, "model_body_layers": 93,
                           "force_eplb": True, "prefix_caching": False, "num_speculative_tokens": 0,
                           "graph_mode": "FULL_DECODE_ONLY", "quantization": "checkpoint_auto; not an explicit CLI flag"},
            "evidence_strength": "retained_launch_intent; resolved startup not located",
            "actual_force_eplb": None},
        "a3_kimi_4layer": {"launch_source": identity(a3_kimi_launch), "resolved_startup": None,
            "configured": {"checkpoint": "/mnt/weight/Kimi-K3-w4a8-4layer", "tp": 8, "dp": 1, "ep": 8,
                           "model_body_layers": 4, "force_eplb": True, "prefix_caching": True,
                           "num_speculative_tokens": 0, "graph_mode": "FULL_DECODE_ONLY", "quantization": "ascend / W4A8 checkpoint"},
            "evidence_strength": "retained_launch_intent; resolved startup and checkpoint config not located",
            "actual_force_eplb": None},
        "a5_glm_flash45": {"launch_source": identity(hp / "glm53-hc/scripts/serve_glm53_mtp.sh"),
            "resolved_startup": log_metadata(glm_log), "actual_force_eplb": True,
            "configured": {"checkpoint": "/mnt/weight/GLM-5.3-Flash-w8a8-mxfp8", "tp": 8, "dp": 1,
                           "ep": 1, "ep_basis": "no enable-expert-parallel in the retained launch; do not borrow EP8 from Kimi",
                           "model_body_layers": 45, "force_eplb": True, "prefix_caching": True,
                           "num_speculative_tokens": 3, "synthetic_acceptance_marginals": [.8, .64, .512],
                           "graph_mode": "FULL_AND_PIECEWISE", "quantization": "ascend / W8A8-MXFP8 checkpoint"},
            "evidence_strength": "resolved startup log plus exact benchmark alias in same raw/ws9 campaign"},
    }
    rows = []
    kimi_plan = Path(__file__).resolve().with_name("acceptance-20261029") / "fusion-cohort-a5_kimi_k3_decode_checkpoint-reference.case.json"
    for concurrency in (1, 2, 4, 8, 16, 32):
        directory = data_root / "a5" / f"kimi_k3_tp8_high_conc_decode_c{concurrency}_p4k_20261030"
        rows.append(capture(directory, "a5_kimi_tp8_ep8", deployments["a5_kimi_tp8_ep8"],
            kimi_plan,
            "Existing template is layer-plan only, not a cost/precision case. Create independent TP8/DP1/EP8 source input: observed BF16 FIA differs from the old FP8 arm; do not inherit DP4."))
    for concurrency in (1, 4, 16, 32, 64):
        directory = data_root / "a3" / f"kimi_k3_w4a8_4layer_tp8_high_conc_decode_c{concurrency}_20261030"
        rows.append(capture(directory, "a3_kimi_4layer", deployments["a3_kimi_4layer"], None,
            "Needs exact 4-layer checkpoint configuration/layer plan; never treat this as a full 93-layer Kimi forward."))
    for length, concurrencies in ((4, (8, 16, 32, 64)), (8, (4, 16, 32))):
        for concurrency in concurrencies:
            directory = data_root / "a5" / f"glm5_3_flash_w8a8_mxfp8_high_conc_decode_c{concurrency}_p{length}k_20261030"
            row = capture(directory, "a5_glm_flash45", deployments["a5_glm_flash45"],
                sim_root / "examples/cases/high-concurrency-20261030/new17/glm53flash-a5-tp8-c1.json",
                "Reuse 45-layer Glm5Next KDA/MLA model frontend; keep TP8/DP1/EP1 and source roles. Never use old GLM78.")
            original = hp / f"glm53-hc/raw/ws9/profile/c{concurrency}_p{length}k.json"
            row["benchmark_original"] = identity(original)
            row["benchmark_alias_verified"] = row["benchmark_original"]["sha256"] == row["benchmark"]["source"]["sha256"]
            if not row["benchmark_alias_verified"]:
                raise ValueError(f"Delivered benchmark does not match source campaign: {directory}")
            rows.append(row)
    probe_path = Path(__file__).with_name("acceptance-20261030-kimi-tp8") / "geometry-probe.json"
    if probe_path.exists():
        probe = read(probe_path)
        probe_sources = {row["source"]["path"]: row["source"] for row in probe["cases"]}
        for row in rows:
            if row["group"] == "a5_kimi_tp8_ep8":
                observed = probe_sources[row["source"]["path"]]
                if observed.get("sha256") != row["source"]["sha256"]:
                    raise ValueError("Candidate probe and inventory source hashes differ")
                row["bounded_candidate_probe"] = identity(probe_path)
    v41_path = Path(__file__).with_name("acceptance-20261030-v41-dp8") / "retained-source-evidence.json"
    v41 = read(v41_path)
    extras = sorted(str(p) for p in (data_root / "a5").glob("kimi_k3_tp8_high_conc_decode_c*_p16k_20261030"))
    result = {"schema_version": "mindie-decode-bundle-input-inventory/1", "not_new_live_collection": True,
              "cases": rows, "newly_hashed_source_count": len(rows), "reused_v41_source_count": len(v41["cases"]),
              "reused_v41_evidence": identity(v41_path), "reused_v41_cases": v41["cases"],
              "actual_selected_case_count": len(rows) + len(v41["cases"]),
              "requested_count_label": 19, "selected_paths_count": 21,
              "count_policy": "Count the listed existing paths; never coerce 21 into the request's 19 label.",
              "additional_existing_paths_not_in_selected_bundle": extras,
              "full_csv_event_scans": 0,
              "probe_ownership": {"a5_kimi_tp8_ep8": "sim_forward bounded candidate probe; no duplicate event reads here",
                                  "a3_kimi_4layer": "forward_extractor c1/c64 bounded probe; no duplicate event reads here"}}
    output.mkdir(parents=True, exist_ok=True)
    (output / "retained-source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 04:06 Decode 制品与模型输入清单", "", "实际选择 21 个目录：已固定的 A5 V4.1 3 个、本次 A5 Kimi 6 个、A3 Kimi 四层 5 个、A5 GLMFlash 7 个。V4.1 身份直接复用；其余 18 份源仅流式哈希，不重复全事件解析。", "",
             "| 组 | 数量 | 声明结构/放置 | Force EPLB 证据 | Prefix / MTP |", "|---|---:|---|---|---|",
             "| A5 Kimi | 6 | 93层 expert16-top8，TP8/DP1/EP8 | launch 意图；resolved log 未找到 | APC off / 未配置 MTP |",
             "| A3 Kimi | 5 | 独立4层 checkpoint，TP8/DP1/EP8 | launch 意图；resolved log 未找到 | APC on / 无 MTP 声明 |",
             "| A5 GLMFlash | 7 | 45层 KDA/MLA，TP8/DP1/EP1 | resolved log 明确 true | APC on / 3 drafts，synthetic [.8,.64,.512] |",
             "| A5 V4.1 | 3 | 40层主体前端候选，TP1/DP8/EP8 | resolved log 明确 true | APC off / 未配置 MTP |", "",
             "GLM 的 measured spec_accept_ratio 独立保留；约 0.65 的整组 accepted/draft 比率不等于首位置 0.8 接收率。prefix queries 为零时 hit ratio 保持未知，不伪称零命中或 100% 命中。", "",
             "| Case | 源 MiB | Client c | 实际 prompt tokens | Profiled token TPOT P50 ms |", "|---|---:|---:|---|---:|"]
    for row in rows:
        b = row["benchmark"]
        lines.append(f"| {row['case_id']} | {row['source']['size_bytes']/1024**2:.2f} | {b['client_concurrency']} | {b['observed_prompt_tokens']} | {b['profiled_token_tpot_p50_ms']:.4f} |")
    lines += ["", "A3 源大小为压缩 CSV 大小，选 tp0；其余 rank 路径保留。客户端 c 不当作 per-rank B，prompt token 不当作每步精确 KV context。额外已落盘的 A5 Kimi p16k 四目录另列，不混入本 21 源覆盖数。", ""]
    (output / "retained-source-evidence.md").write_text("\n".join(lines))
    print(json.dumps({"selected_cases": result["actual_selected_case_count"], "new_hashes": len(rows), "reused_v41": 3, "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--workspace", type=Path, default=Path("/Users/maoxx241/code/mindie-agent"))
    parser.add_argument("--sim-root", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-bundle0406"))
    args = parser.parse_args()
    build(args.data_root, args.workspace, args.sim_root, args.output)
