"""Index the additional 17 + 9 retained high-concurrency captures.

[Role] Join one rank per capture to externally declared Sim cases and source facts.
[Invariants] Launch intent, observed startup settings, client metrics and tensor
  execution geometry remain separate. Missing checkpoint identity stays explicit.
[Timeouts & Locks] Metadata <=5 MiB; source hashes stream in 1 MiB blocks; no locks.
[Side-Effect Policy] Reads local captures/configuration and writes local evidence.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re

from build_decode_forward_cases import _hash, _read


def identity(path):
    return {"path": str(path.resolve()), "sha256": _hash(path),
            "size_bytes": path.stat().st_size}


def startup(path):
    lines = []
    if not path.exists():
        return None
    for number, line in enumerate(path.open(), 1):
        if any(text in line for text in ("non-default args:", "Initializing a V1",
                                        "Resolved architecture:", "ACL graph replay is active",
                                        "Prefix cache hit rate:")):
            lines.append({"line": number, "text": line.rstrip()})
    args = next((row for row in lines if "non-default args:" in row["text"]), None)
    engine = next((row for row in lines if "Initializing a V1" in row["text"]), None)
    text = args["text"] if args else ""
    def value(key):
        match = re.search(r"'" + re.escape(key) + r"': (True|False|\d+|'[^']*')", text)
        if not match:
            return None
        raw = match.group(1)
        return {"True": True, "False": False}.get(raw, int(raw) if raw.isdigit() else raw.strip("'"))
    return {"source": identity(path), "evidence_lines": lines,
            "runtime_fields": {key: value(key) for key in (
                "model", "tensor_parallel_size", "enable_expert_parallel", "enable_force_eplb",
                "num_speculative_tokens", "enforce_eager", "enable_prefix_caching",
                "max_num_seqs", "max_num_batched_tokens", "fusion_ops_gmmswigluquant")},
            "engine_config_observed": engine is not None,
            "missing_argument_is_not_false": True}


def campaign_evidence(root, workstream):
    name = root.name
    launch = []
    log = None
    if root.parent.name == "a3" and name.startswith("Qwen"):
        stem = ("qwen397-16" if "397B" in name else "qwen35moe-4" if "35B" in name
                else "qwen36-4" if "3.6" in name else "qwen38-4")
        log = workstream / "hp-serving/a3-highconc-decode/evidence/logs" / f"serve-{stem}.log"
        launch = [workstream / "hp-serving/a3-highconc-decode/cfg/serve.sh"]
    elif root.parent.name == "a5" and name.startswith("glm5"):
        log = workstream / "hp-serving/glm53-hc/logs/glm53-serve.log"
        launch = [workstream / "hp-serving/glm53-hc/scripts/serve_glm53_mtp.sh"]
    elif root.parent.name == "a3" and "livepre" not in name:
        script = ("serve_dsv4f_w8a8_mtp.sh" if name.startswith("deepseek")
                  else "serve_glm53f_w8a8.sh")
        launch = [workstream / "hp-serving/a3-highconc-decode/scripts/cases" / script]
    elif "qwen3_5_35b" in name:
        concurrency = int(re.search(r"_c(\d+)_", name).group(1))
        graph = concurrency in {4, 64, 128}
        launch = [workstream / "w3-a5-hc-decode/cfg" / ("serve_qwen35_graph.sh" if graph else "serve_qwen35.sh")]
        if graph:
            log = workstream / "w3-a5-hc-decode/evidence/qwen35_graph_startup_and_prefix_hit.txt"
    elif "qwen3_6_27b_w8a8_tp2" in name:
        launch = [root / "cfg/serve_t6c_qwen36_tp2.sh"]
        candidates = list((root / "logs").glob("*.log")) if (root / "logs").exists() else []
        log = candidates[0] if len(candidates) == 1 else None
    return {"startup": startup(log) if log else None,
            "launch_sources": [identity(path) for path in launch if path.exists()],
            "launch_source_is_execution_intent": True}


def selected_source(root):
    top = root / "kernel_details.csv"
    if top.exists():
        return top, root / "step_trace_time.csv", "top_level_export", []
    source = root / "ranks/tp0/kernel_details.csv.gz"
    if not source.exists():
        raise FileNotFoundError(f"retained rank-zero source missing: {root}")
    ranks = sorted(path.name for path in (root / "ranks").iterdir() if path.is_dir())
    return source, root / "ranks/tp0/step_trace_time.csv", "tp0", ranks


def benchmark_metrics(root, summary, concurrency):
    """Preserve metric populations; a client TPOT is never a device body span."""
    tpot = {"profiled_run_client_ms": None, "unprofiled_sweep_ms": None,
            "body_forward_is_separate_metric": True}
    prefix = {"profiled_metrics": None, "unprofiled_metrics": None,
              "unknown_metrics_are_not_zero": True}
    if "tpot_client_ms" in summary:
        tpot.update(profiled_run_client_ms=summary["tpot_client_ms"],
                    profiled_engine_window_estimate_ms=summary["tpot_engine_ms"],
                    unprofiled_sweep_ms=summary["unprofiled_sweep"]["tpot_sweep_unprofiled_ms"])
        prefix["profiled_metrics"] = {"hit_rate": summary["prefix_cache_hit_rate"],
                                      "basis": "benchmark_summary.cell_metrics"}
    elif "profile_cell" in summary:
        tpot["profiled_run_client_ms"] = {"median": summary["profile_cell"]["tpot_true_p50_ms"]}
        tpot["unprofiled_sweep_ms"] = summary["sweep_cell"]["tpot_true_p50_ms"]
        prefix["profiled_metrics"] = summary["profile_cell"]["prefix"]
        prefix["unprofiled_metrics"] = summary["sweep_cell"]["prefix"]
    elif "tpot_tok_ms" in summary:
        tpot["profiled_run_client_ms"] = summary["tpot_tok_ms"]
        sweep = root / f"sweep_c{concurrency}.json"
        if sweep.exists():
            original = _read(sweep)
            if original.get("profile", {}).get("requested") is not False:
                raise ValueError(f"sweep is not explicitly unprofiled: {sweep}")
            tpot["unprofiled_sweep_ms"] = original["tpot_tok_ms"]["median"]
            tpot["unprofiled_sweep_source"] = identity(sweep)
    elif "tpot_ms" in summary:
        tpot["profiled_run_client_ms"] = summary["tpot_ms"]
        sweep = root / "sweep.json"
        if sweep.exists():
            matching = [row for row in _read(sweep)["cells"] if row["concurrency"] == concurrency]
            if len(matching) == 1:
                row = matching[0]
                tpot["unprofiled_sweep_ms"] = row["tpot_median"]
                tpot["unprofiled_sweep_population"] = row["tpot_source"]
                tpot["unprofiled_sweep_source"] = identity(sweep)
                prefix["unprofiled_metrics"] = row.get("prefix_cache_metrics")
    else:
        tpot["profiled_run_client_ms"] = {"median": summary.get("median_tpot_ms"),
                                          "mean": summary.get("mean_tpot_ms")}
        tpot["profiled_trimmed_itl_ms"] = summary.get("tpot_trimmed_ms")
    return tpot, prefix


def build(data_root, sim_root, workstream, output):
    rows = []
    for name in ("new17", "new9"):
        audit_path = sim_root / "data/verification" / f"high-concurrency-{name}-inputs-20261030.json"
        audit = _read(audit_path)
        rows.extend({"root": Path(row["capture_directory"]), "audit": row,
                     "audit_identity": identity(audit_path)} for row in audit["cases"])
    if len(rows) != 26 or len({str(row["root"]) for row in rows}) != 26:
        raise ValueError("expected exactly 17 + 9 distinct retained captures")
    cases = []
    for item in rows:
        root, audit_row = item["root"], item["audit"]
        source, step, rank, ranks = selected_source(root)
        summary_path = root / "benchmark_summary.json"
        summary = _read(summary_path)
        concurrency = summary.get("max_concurrency", summary.get("concurrency", summary.get("tier", {}).get("concurrency")))
        prompt_tokens = summary.get("input_len", summary.get("prefix_cache_protocol", {}).get(
            "requests_prompt_tokens", summary.get("prefix_len", 4096) + summary.get("suffix_len", 0)))
        tpot, prefix = benchmark_metrics(root, summary, concurrency)
        compact = {key: value for key, value in summary.items()
                   if key not in {"per_request", "op_statistic", "top_operators"}}
        with step.open(newline="") as stream:
            step_rows = list(csv.DictReader(stream))
        evidence = campaign_evidence(root, workstream)
        case_path = Path(audit_row["case"]["path"]) if audit_row and audit_row.get("case") else None
        case_id = audit_row["case_id"] if audit_row else root.name
        source_ref = identity(source)
        unresolved = []
        if not case_path:
            unresolved.append("source_bound_sim_model_declaration_pending")
        if not evidence["startup"]:
            unresolved.append("startup_log_not_located; launch_intent_is_not_runtime_confirmation")
        facts = {
            "capture_directory": str(root), "benchmark_summary": identity(summary_path),
            "benchmark_summary_fields": compact, "retained_deployment": evidence,
            "client": {"concurrency": concurrency, "input_len": prompt_tokens,
                       "token_exact": summary.get("token_exact")},
            "tpot": tpot, "prefix_cache": prefix,
            "source_population": {"selected_rank": rank, "available_rank_directories": ranks,
                                  "all_ranks_are_not_summed": True,
                                  "gzip_is_streamed_without_materialization": source.suffix == ".gz"},
            "step_trace": {"source": identity(step), "rows": step_rows,
                           "explicit_nonempty_step_values": sum(bool(row.get("Step", "").strip()) for row in step_rows)},
            "request_geometry_is_not_per_forward_geometry": True,
            "force_load_balance": {"value": (evidence["startup"] or {}).get("runtime_fields", {}).get("enable_force_eplb"),
                                   "basis": "retained_non_default_startup_args_if_present"},
            "prefix_and_acceptance": {"configured_values_are_not_measured_rates": True,
                                      "unknown_metrics_are_not_zero": True},
            "tpot_body_scope": "client/profiled/sweep metrics retained separately in source fields; never body_forward_span_ms",
        }
        if audit_row:
            facts["sim_input_audit"] = {"source": item["audit_identity"], "case_id": case_id,
                                        "model_contract": audit_row.get("model_contract"),
                                        "case_status": audit_row.get("case_status"),
                                        "unresolved": audit_row.get("unresolved", [])}
        if "qwen3_5_35b" in root.name:
            facts["prefix_and_acceptance"]["prefix_cache_reuse_ratio_client_field_is_not_cache_metric"] = True
            facts["retained_deployment"]["script_local_patches"] = [
                "DequantSwigluQuantV2 clamp_limit=1e9", "disable Triton swiglu_quant branch"]
        cases.append({"case_id": case_id, "source": source_ref,
                      "sim_case_path": str(case_path) if case_path else None,
                      "model_declaration": {**identity(case_path), "basis": "source_bound_sim_case_with_audited_model_identity_limits"} if case_path else None,
                      "segmentation": "auto_structure_guided", "boundaries_path": None,
                      "geometry": None, "scenario_evidence": facts,
                      "unresolved_reasons": unresolved})
    result = {"schema_version": "mindie-decode-forward-replay/1", "cases": cases,
              "not_new_live_collection": True, "segmentation": "auto_structure_guided",
              "notes": ["26 newly retained sources; earlier 6 and 30-source generations remain unchanged.",
                        "Model shapes and complete topology come from Sim, never inferred by fitting event durations.",
                        "Source-bound Sim declarations may remain pending; such sources are inventoried explicitly."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 新增 17 + 9 份 Decode 采集源证据", "",
             "每份仅选一个原始 rank；gzip 流式读取。启动日志、脚本意图与实测客户端指标分别保留，模型声明缺失时不套用其他模型。", "",
             "| Case | CSV MiB | 单 rank | Sim 声明 | 运行 force_eplb |", "|---|---:|---|---|---|"]
    for row in cases:
        s = row["scenario_evidence"]
        lines.append(f"| {row['case_id']} | {row['source']['size_bytes']/1024**2:.2f} | {s['source_population']['selected_rank']} | {'已配对' if row['sim_case_path'] else '待补'} | {s['force_load_balance']['value']} |")
    lines += ["", "CSV 大小对 gzip 指压缩文件字节；此表不代表完整解压后的事件内存。None 表示尚无该字段的直接启动证据，不等于 False。",
              "Q35 A5 客户端 prefix_cache_reuse_ratio 不是服务端缓存指标；0.0 不解释为零命中。来源配对与原始 checkpoint config 完全同一性分别记录，存在 Sim 声明不表示采集目录保存了原始配置。", ""]
    output.with_suffix(".md").write_text("\n".join(lines))
    return {"cases": len(cases), "with_model_declaration": sum(bool(row["sim_case_path"]) for row in cases),
            "manifest": identity(output)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--sim-root", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027"))
    parser.add_argument("--workstream", type=Path, default=Path("/Users/maoxx241/code/mindie-agent/.workstreams"))
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "acceptance-20261030-expanded/decode-forward-auto-cases.json")
    args = parser.parse_args()
    print(json.dumps(build(args.data_root, args.sim_root, args.workstream, args.output)))
