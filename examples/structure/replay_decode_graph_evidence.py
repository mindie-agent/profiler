"""Replay retained device graph boundaries without assigning model semantics.

[Role] Inventory local full-model exports and replay the Qwen3.6 graph markers.
[Invariants] Client concurrency/context are request facts, not Forward geometry.
  A missing graph-to-body/layer binding stays unresolved; no live collection.
[Timeouts & Locks] Bounded per-capture streaming; no locks or remote execution.
[Side-Effect Policy] Writes only compact local replay reports and a manifest.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import resource
import time

from mindie_profiler.accounting import percentile
from mindie_profiler.graph_execution import graph_execution_envelopes


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path):
    if path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError(f"metadata exceeds 5 MiB: {path}")
    return json.loads(path.read_text())


def _write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def replay(data_root, output):
    started = time.monotonic()
    capture = data_root / "a5/2026-10-23/qwen36-attn"
    server_log = capture / "logs/server-tp8-attn.log"
    log_identity = {"path": str(server_log), "sha256": _hash(server_log),
                    "line": 26}
    cases, summaries = [], []
    output.mkdir(parents=True, exist_ok=True)
    for task in sorted((capture / "traces").glob("*/task_time.csv.gz")):
        operators = task.with_name("op_summary.csv.gz")
        cell = task.parent.name
        client_path = capture / "raw" / f"{cell}.json"
        gate_path = capture / "raw" / f"{cell}.gate.json"
        client, gate = _read(client_path), _read(gate_path)
        graph = graph_execution_envelopes(task, operator_path=operators)
        graph["source"]["sha256"] = _hash(task)
        graph["operator_source"]["sha256"] = _hash(operators)
        path = output / f"decode-graph-a5_qwen36-{cell}.json"
        _write(path, graph)
        groups = defaultdict(list)
        for window in graph["windows"]:
            groups[",".join(sorted(window["observed_model_ids"])) or "none"].append(
                (window["end_ns"] - window["start_ns"]) / 1e6)
        summary = {
            "case_id": f"a5_qwen36_{cell}", "graph_envelopes_path": str(path.resolve()),
            "graph_occurrences": len(graph["windows"]),
            "unmatched_markers": len(graph["unmatched_markers"]),
            "request_input_len": client["input_len"],
            "request_concurrency": client["concurrency"],
            "graph_execution_groups": [
                {"observed_model_ids": ids, "count": len(values),
                 "mean_ms": sum(values) / len(values), "p50_ms": percentile(values, .5),
                 "p90_ms": percentile(values, .9)} for ids, values in sorted(groups.items())],
        }
        summaries.append(summary)
        cases.append({
            "case_id": summary["case_id"], "source": graph["operator_source"],
            "graph_envelopes_path": str(path.resolve()),
            "boundaries_path": None, "sim_case_path": None,
            "geometry": {"phase": "decode", "tokens_per_sequence": None,
                         "context_tokens": None, "sequences_per_replica": None,
                         "participating_replicas": None},
            "scenario_evidence": {
                "client": {"path": str(client_path), "sha256": _hash(client_path),
                           "input_len": client["input_len"], "concurrency": client["concurrency"],
                           "token_exact": client["token_exact"]},
                "gate": {"path": str(gate_path), "sha256": _hash(gate_path), **gate},
                "runtime": {"source": log_identity, "graph_mode": "FULL_DECODE_ONLY",
                            "prefix_caching_enabled": False, "speculative_tokens": 3,
                            "tensor_parallel_size": 8},
                "forced_load_balancing": "not_verified", "acceptance_0_8": "not_verified",
                "dspark": "not_verified", "prefix_hit_100_percent": False,
                "request_geometry_is_not_per_forward_geometry": True,
            },
            "unresolved_reasons": ["graph_to_body_scope_binding_missing",
                                   "layer_occurrence_boundaries_missing",
                                   "per_forward_geometry_missing",
                                   "terminal_allreduce_wait_identity_missing"],
        })
    inventory = defaultdict(lambda: {"csv_count": 0, "bytes": 0})
    microbenches = {"activation", "k3-gdn-shape", "mla-dsa", "k3-mla",
                   "k3-mla-matched", "op-sweep", "structure-blocks", "block-additivity"}
    for arch in ("a3", "a5"):
        for source in (data_root / arch).rglob("kernel_details.csv*"):
            relative = source.relative_to(data_root)
            if len(relative.parts) < 4 or relative.parts[2] in microbenches:
                continue
            key = "/".join(relative.parts[:3])
            inventory[key]["csv_count"] += 1
            inventory[key]["bytes"] += source.stat().st_size
    report = {
        "schema_version": "mindie-decode-forward-evidence/1", "status": "completed",
        "data_root": str(data_root), "latest_date_directories": {
            arch: max(path.name for path in (data_root / arch).iterdir() if path.is_dir())
            for arch in ("a3", "a5")},
        "cases": summaries, "candidate_csv_inventory": dict(sorted(inventory.items())),
        "inventory_scope": "discovery_candidates; campaign model scope requires separate verification",
        "body_forward_span_ms": None, "per_layer_ms": None,
        "graph_execution_percentile_method": "sorted_values[round(p * (n - 1))]; Python round; no interpolation",
        "limitations": [
            "Graph execution envelopes include internal waits/communication; only between-graph gaps are absent.",
            "Temporal Model ID containment does not identify body, embedding, layer, or MTP scope.",
            "Existing Q36 request scenarios have prefix caching disabled and do not verify forced balancing/0.8 acceptance/DSpark.",
            "Old sampler-marker/gdn-gap reductions are heuristics, not exact layer boundaries.",
            "Full-model Q35 and Q38 exports retain kernel CSVs but commonly omit Host DB/task exports.",
        ],
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "maximum_resident_set_size_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    _write(output / "decode-forward-evidence.json", report)
    _write(output / "decode-forward-cases.json", {
        "schema_version": "mindie-decode-forward-replay/1", "cases": cases})
    lines = ["# Decode Forward 边界证据回放", "",
             "复用本地历史 A5 Qwen3.6 TP8 的 8 份完整导出；本次没有真机补采。",
             "设备 MODEL_EXECUTE / MODEL_WAIT_COMPLETE 可给出 graph execution envelope，"
             "本文件仅记录这些设备标记直接支持的边界，body_forward_span_ms 和 per_layer_ms 不直接由图长短赋值。", "",
             "后续 [结构引导自动回放](decode-forward-auto-acceptance.md) 将完整模型层序列和 LMHead 契约闭合，"
             "再与这里的图窗口逐一交叉核验；自动推断的主体/层耗时在那里呈现。", "",
             "| Case | 请求长度 | 请求并发 | 图窗口 | 未配对 marker |", "|---|---:|---:|---:|---:|"]
    for row in summaries:
        lines.append(f"| {row['case_id']} | {row['request_input_len']} | {row['request_concurrency']} | {row['graph_occurrences']} | {row['unmatched_markers']} |")
    lines += ["", "图窗口覆盖执行发起到设备完成，保留图内通信与等待，仅自然剥离图间空泡。"
              "Model ID 的时间包含关系只作辅助证据，不把较长图认定为主体、较短图认定为 MTP。", "",
              "同批启动日志明确 prefix caching=false；强制负载均衡、0.8 接收率与 DSpark 未有制品证据。"
              "客户端 input_len/concurrency 只描述请求，不填作每次 Forward 的实际 KV 长度和活跃 batch。", "",
              "A3 Qwen3.5 的 `qwen35-gdn/PROVENANCE.md` 明确只保留导出 CSV；"
              "A5 `qwen38-c8/MANIFEST.md` 明确 DB/task_time 未取回。已有 sampler/gdn-gap 分段结果不作为精确层边界。", "",
              "复跑：`PYTHONPATH=. python examples/structure/replay_decode_graph_evidence.py`。", "",
              "辅助 graph 分位数沿用 accounting 的 `sorted_values[round(p*(n-1))]`（Python round、不插值）；"
              "主体报告使用 median P50 / 最近秩 P90，两者方法明确分开，未改写已完成主体回放的计时。", ""]
    (output / "decode-forward-evidence.md").write_text("\n".join(lines))
    return {"cases": len(cases), "graph_occurrences": sum(row["graph_occurrences"] for row in summaries),
            "unmatched_markers": sum(row["unmatched_markers"] for row in summaries),
            "elapsed_seconds": report["elapsed_seconds"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, default=Path("/Volumes/data/mindie-sim-data"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("acceptance-20261029"))
    args = parser.parse_args()
    print(json.dumps(replay(args.data_root, args.output)))
