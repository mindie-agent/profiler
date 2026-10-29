"""Inventory the five A3 DSpark7 captures and A5 DP8 c128 without model execution.

[Role] Preserve source identities and deployment differences for Sim inputs.
[Invariants] A3 disables Engram and uses fused MC2; A5 retains Engram and no MTP.
  Launch intent is not a resolved startup log or measured expert-balance proof.
[Timeouts & Locks] Streaming hashes and bounded metadata; no event parsing.
[Side-Effect Policy] Local read-only sources; writes an inventory receipt.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

from inspect_decode_bundle_0406 import capture
from inspect_glm78_v41_assets import digest, identity, read


def build(data_root, workspace, sim_root, output):
    here = Path(__file__).parent
    launch = workspace / ".workstreams/hp-serving/a3-highconc-decode/w10/cases/serve_dsv41_flash_w8a8_dspark7.sh"
    deployment = {"launch_source": identity(launch), "resolved_startup": None,
        "actual_force_eplb": None,
        "configured": {"checkpoint": "/mnt/weight/DeepSeek-V4.1-Flash-w8a8/",
            "tp": 4, "dp": 4, "ep": 16, "engram_layer_ids": [],
            "speculation": {"method": "dspark", "num_speculative_tokens": 7, "enforce_eager": True},
            "graph_mode": "FULL_DECODE_ONLY", "force_eplb": True, "prefix_caching": True,
            "enable_fused_mc2": True, "enable_flashcomm1": True, "enable_shared_expert_dp": True,
            "max_model_len": 65536, "max_num_seqs_per_dp": 32, "max_num_batched_tokens": 4096,
            "block_size": 128, "gpu_memory_utilization": .85,
            "software_lane": "standing nightly-main-a3 container, installed vLLM 0.31.0 pair; launch comments distinguish incompatible /work 0.32 source tree"},
        "evidence_strength": "source-specific retained launch; full resolved startup not located"}
    rows = []
    for concurrency in (4, 8, 16, 32, 64):
        directory = data_root / "a3" / f"deepseek_v4_1_flash_w8a8_dspark7_high_conc_decode_c{concurrency}_20261030"
        row = capture(directory, "a3_v41_dspark7_tp4_dp4_ep16", deployment, None,
            "V4.1 source-bound TP4/DP4/EP16, Engram disabled, DSpark7; fused DispatchFFNCombine must be represented explicitly, not as observed standalone GMM events.")
        packed = directory / "ranks/dp0_tp0/kernel_details.csv.gz"
        with gzip.open(packed, "rb") as stream:
            unpacked_hash, unpacked_bytes = digest(stream)
        if unpacked_hash != row["source"]["sha256"] or unpacked_bytes != row["source"]["size_bytes"]:
            raise ValueError(f"Top CSV is not the retained dp0_tp0 stream: {directory}")
        row["selected_rank"] = "dp0_tp0"
        row["selected_rank_alias"] = {"compressed_source": identity(packed),
            "uncompressed_sha256": unpacked_hash, "uncompressed_bytes": unpacked_bytes,
            "same_as_selected_csv": True}
        row["profile_cell"] = {"source": identity(directory / "profile_cell.json"),
                               "cell": read(directory / "profile_cell.json")["cell"]}
        row["unprofiled_cell"] = {"source": identity(directory / "cell.json"),
                                 "value": read(directory / "cell.json")}
        rows.append(row)
    prior = read(here / "acceptance-20261030-v41-dp8/retained-source-evidence.json")
    directory = data_root / "a5/deepseek_v4_1_flash_fp8_high_conc_decode_c128_p2k_20261030"
    row = capture(directory, "a5_v41_dp8", {"launch_source": prior["launch"],
        "resolved_startup": prior["startup"], "actual_force_eplb": True,
        "current_capture_engine_config": read(directory / "benchmark_summary.json")["engine_config"]},
        sim_root / "examples/cases/high-concurrency-20261030/matrix-extension/a5_v41_fp8_tp1_dp8_ep8_c32_p2k.json",
        "Reuse the A5 TP1/DP8/EP8 source frontend with client c128; resolve rank execution batch from the new capture, not the client count.")
    row["selected_rank"] = "dp0_pp0_tp0_dcp0_ep0_rank0"
    row["trace_origin"] = (directory / "trace_dir.txt").read_text().strip()
    rows.append(row)
    output.mkdir(parents=True, exist_ok=True)
    result = {"schema_version": "mindie-v41-final6-source-evidence/1", "not_new_live_collection": True,
        "case_count": 6, "unique_source_hashes": len({r["source"]["sha256"] for r in rows}),
        "full_csv_event_scans": 0, "cases": rows,
        "boundary": "Metadata inventory only; fused FFN and source-specific attention need bounded ABI checks before full replay."}
    (output / "retained-source-evidence.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# V4.1 后续 6 源", "", "A3 五源为 TP4/DP4/EP16、DSpark7、Engram 禁用、fused MC2 的独立部署；A5 c128 沿用 TP1/DP8/EP8、Engram 开启且无 MTP。不得共享同一执行配方。", "",
             "A3 每源 16 rank 保留；选择 dp0_tp0，解压 SHA 与顶层 CSV 完全相同。其他 rank 未做事件扫描。FULL_DECODE_ONLY、force EPLB 等 A3 条件目前是启动脚本声明，未冒充 resolved 日志。", "",
             "| Case | MiB | Profiled client c | Prompt tokens | Token TPOT P50 ms |", "|---|---:|---:|---|---:|"]
    for row in rows:
        b = row["benchmark"]
        lines.append(f"| {row['case_id']} | {row['source']['size_bytes']/1024**2:.2f} | {b['client_concurrency']} | {b['observed_prompt_tokens']} | {b['profiled_token_tpot_p50_ms']:.6f} |")
    lines += ["", "该表为客户端指标，不是主体 Forward 耗时；实测 q/B、结构完整性和 body/activity 由后续解析给出。", ""]
    (output / "retained-source-evidence.md").write_text("\n".join(lines))
    print(json.dumps({"cases": 6, "receipt": identity(output / "retained-source-evidence.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--workspace", type=Path, default=Path("/Users/maoxx241/code/mindie-agent"))
    parser.add_argument("--sim-root", type=Path, default=Path("/Users/maoxx241/code/sim-rewrite-20261027"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261030-v41-final6"))
    args = parser.parse_args()
    build(args.data_root, args.workspace, args.sim_root, args.output)
