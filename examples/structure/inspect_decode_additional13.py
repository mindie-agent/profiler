"""Pin the additional 13 captures without mutating the earlier 21-source receipt.

[Role] Connect delivered CSVs to retained benchmark/deployment metadata.
[Invariants] A3 token-sized ACLGraph capture buckets are a new source condition;
  a filename or launch intent does not become resolved runtime evidence.
[Timeouts & Locks] Stream hashes/gzip identity checks; no event parsing.
[Side-Effect Policy] Local read-only sources; write a separate JSON/Markdown receipt.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from inspect_decode_bundle_0406 import capture
from inspect_glm78_v41_assets import digest, identity, read


def build(data_root, workspace, sim_root, output):
    prior_path = Path(__file__).with_name("acceptance-20261030-bundle0406") / "retained-source-evidence.json"
    prior = read(prior_path)
    hp = workspace / ".workstreams/hp-serving"
    rows = []
    v41 = read(Path(prior["reused_v41_evidence"]["path"]))
    for concurrency in (4, 16, 32):
        directory = data_root / "a5" / f"deepseek_v4_1_flash_fp8_high_conc_decode_c{concurrency}_p2k_20261030"
        row = capture(directory, "a5_v41_dp8", {"launch_source": v41["launch"],
            "resolved_startup": v41["startup"], "actual_force_eplb": True,
            "current_capture_engine_config": read(directory / "benchmark_summary.json")["engine_config"]},
            sim_root / "examples/cases/v41-a5-dp4.json",
            "V4.1 40-layer body frontend candidate only; create TP1/DP8/EP8 APC-off input, do not inherit DP4 or A3 DSpark7.")
        row["selected_rank"] = "dp0_pp0_tp0_dcp0_ep0_rank0"
        row["trace_origin"] = (directory / "trace_dir.txt").read_text().strip()
        rows.append(row)
    deployment = next(row["deployment_evidence"] for row in prior["cases"] if row["group"] == "a5_kimi_tp8_ep8")
    template = next(row["declared_template_candidate"] for row in prior["cases"] if row["group"] == "a5_kimi_tp8_ep8")
    for concurrency in (1, 2, 4, 8, 16, 32):
        directory = data_root / "a5" / f"kimi_k3_tp8_high_conc_decode_c{concurrency}_p16k_20261030"
        rows.append(capture(directory, "a5_kimi_tp8_ep8", deployment, Path(template),
            "Same independent expert16-top8 TP8/DP1/EP8 source family as p4k; layer-plan template does not prove precision/cost. Actual prompt length comes from client usage."))
    launch = hp / "a3-highconc-decode/w10/cases/serve_glm53f_w8a8.sh"
    deployment = {"launch_source": identity(launch), "resolved_startup": None,
        "actual_force_eplb": None,
        "configured": {"checkpoint": "/mnt/weight/GLM-5.3-Flash-w8a8", "tp": 16, "dp": 1, "ep": 16,
                       "num_speculative_tokens": 5, "synthetic_acceptance_marginals": [.8, .64, .512, .4096, .32768],
                       "kv_cache_dtype": "int8", "force_eplb": True, "prefix_caching": True,
                       "graph_mode": "FULL_DECODE_ONLY",
                       "graph_capture_token_sizes": [6, 12, 24, 36, 48, 72, 96, 144, 192, 288, 384],
                       "graph_capture_size_axis": "tokens, not sequences", "quantization": "ascend / W8A8 checkpoint"},
        "evidence_strength": "retained source-specific launch and exact compressed rank alias; resolved startup log not retained"}
    for concurrency in (8, 16, 32, 64):
        name = f"glm5_3_flash_w8a8_high_conc_decode_aclgraph_c{concurrency}_20261030"
        directory = data_root / "a3" / name
        metadata = hp / "a3-highconc-decode/deliverables/a3" / name
        row = capture(directory, "a3_glmflash45_aclgraph", deployment,
            sim_root / "examples/cases/high-concurrency-20261030/new17/glm53flash-a3-tp16-c4.json",
            "Reuse GLMFlash45 KDA/MLA frontend; bind the new token-sized graph buckets, TP16/DP1/EP16, q6. Do not reuse old high-c eager source conditions.",
            metadata_directory=metadata)
        packed, original = directory / "kernel_details.csv.gz", metadata / "ranks/tp0/kernel_details.csv.gz"
        packed_id, original_id = identity(packed), identity(original)
        with gzip.open(packed, "rb") as stream:
            uncompressed_hash, uncompressed_size = digest(stream)
        if packed_id["sha256"] != original_id["sha256"] or uncompressed_hash != row["source"]["sha256"]:
            raise ValueError(f"A3 copied export identity does not match its metadata: {directory}")
        row["metadata_source_link"] = {"delivered_compressed": packed_id, "original_rank_compressed": original_id,
            "compressed_alias_identical": True, "uncompressed_sha256": uncompressed_hash,
            "uncompressed_bytes": uncompressed_size, "same_as_selected_csv": True}
        row["capture_cell"] = {"source": identity(metadata / "cell.json"), "args": read(metadata / "cell.json")["args"]}
        row["selected_rank"] = "tp0"
        rows.append(row)
    old_sources = {row["source"]["sha256"]: row["source"]["path"] for row in prior["cases"]}
    old_sources.update({row["source"]["sha256"]: row["source"]["path"] for row in prior["reused_v41_cases"]})
    aliases = [{"case_id": row["case_id"], "prior_source": old_sources[row["source"]["sha256"]]}
               for row in rows if row["source"]["sha256"] in old_sources]
    result = {"schema_version": "mindie-decode-bundle-additional-inputs/1", "not_new_live_collection": True,
              "prior_21_receipt": identity(prior_path), "prior_receipt_unchanged": True,
              "case_count": len(rows), "unique_new_source_hashes": len({row["source"]["sha256"] for row in rows}),
              "aliases_of_prior_21": aliases, "cases": rows, "full_csv_event_scans": 0,
              "cumulative_selected_paths": 21 + len(rows),
              "identity_policy": "Only 13 new sources hashed. Prior 21 raw sources were not read again."}
    output.mkdir(parents=True, exist_ok=True)
    (output / "retained-source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 后续 13 个 Decode 采集输入", "", "与上一批 21 源分开保留身份：新增 V4.1 c4/c16/c32 p2k 三源、Kimi p16k 六源、A3 GLMFlash ACLGraph 四源，共 13 个。没有重读上一批原始 CSV。", "",
        "A3 GLM 交付目录只保留导出的 CSV，benchmark 与 16-rank manifest 在 workstream 的同名 deliverables 下。已验证交付 gzip 与原 tp0 gzip 同 SHA，解压内容与当前 CSV 同 SHA，因此元数据关联有字节级证据。", "",
        "其启动脚本改为按 token 计的捕获桶 [6,12,24,36,48,72,96,144,192,288,384]，MTP5 的 q6 可覆盖到 c64。FULL_DECODE_ONLY、force EPLB 等保持脚本声明；未冒充缺失的 resolved 日志。", "",
        "| Case | 源 MiB | Client c | 实际 prompt tokens | Profiled token TPOT P50 ms |", "|---|---:|---:|---|---:|"]
    for row in rows:
        b = row["benchmark"]
        lines.append(f"| {row['case_id']} | {row['source']['size_bytes']/1024**2:.2f} | {b['client_concurrency']} | {b['observed_prompt_tokens']} | {b['profiled_token_tpot_p50_ms']:.4f} |")
    lines += ["", "以上均为客户端指标与源制品身份；Body、层耗时和实际每步 B/q/context 仍由后续结构引导提取产生。来源相同的不同运行时预测不增加实测分母。", ""]
    (output / "retained-source-evidence.md").write_text("\n".join(lines))
    print(json.dumps({"new_cases": len(rows), "cumulative_selected_paths": 21+len(rows), "prior_aliases": aliases, "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--workspace", type=Path, default=Path("/Users/maoxx241/code/mindie-agent"))
    parser.add_argument("--sim-root", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-additional13"))
    args = parser.parse_args()
    build(args.data_root, args.workspace, args.sim_root, args.output)
