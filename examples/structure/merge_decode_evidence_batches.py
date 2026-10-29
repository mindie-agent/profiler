"""Merge independently versioned Decode extraction batches without rereading CSV.

[Role] Assemble one source-indexed acceptance receipt across actual core generations.
[Invariants] Every manifest case occurs once; raw artifacts retain their original
  source, case, core and timing identities. Merging never relabels old extraction.
[Timeouts & Locks] Bounded saved reports only; no subprocesses or locks.
[Side-Effect Policy] Reads local JSON and writes the aggregate receipt and table.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_decode_forward_cases import _hash, _read


def merge(manifest_path, batch_paths, output):
    manifest = _read(manifest_path)
    expected = {row["case_id"]: row for row in manifest["cases"]}
    reports, batches = {}, []
    for path in batch_paths:
        batch = _read(path)
        batches.append({"path": str(path.resolve()), "sha256": _hash(path),
                        "status": batch["status"], "case_count": batch["case_count"],
                        "segmentation_runtime": batch["segmentation_runtime"],
                        "elapsed_seconds": batch.get("elapsed_seconds", batch.get("elapsed_seconds_completed_sources")),
                        "maximum_resident_set_size_raw": batch.get("maximum_resident_set_size_raw"),
                        "interruption": batch.get("interruption")})
        for row in batch["cases"]:
            name = row["case_id"]
            if name not in expected or name in reports:
                raise ValueError(f"unexpected/duplicate extraction case: {name}")
            report_path = Path(row["report_path"])
            if _hash(report_path) != row["report_sha256"]:
                raise ValueError(f"extraction artifact changed: {report_path}")
            observed = _read(report_path)
            case = expected[name]
            if (observed["source_identity"]["sha256"] != case["source"]["sha256"]
                    or observed["model_structure_identity"]["sha256"] != case["model_declaration"]["sha256"]
                    or observed["extraction_runtime"] != batch["segmentation_runtime"]):
                raise ValueError(f"source, model or original runtime identity disagrees: {name}")
            reports[name] = {**row, "extraction_runtime": observed["extraction_runtime"],
                             "batch_receipt": {"path": str(path.resolve()), "sha256": _hash(path)}}
    if set(reports) != set(expected):
        raise ValueError(f"unmeasured manifest cases: {sorted(set(expected)-set(reports))}")
    cases = [reports[row["case_id"]] for row in manifest["cases"]]
    result = {"schema_version": "mindie-decode-auto-acceptance/1", "status": "completed",
              "not_new_live_collection": True, "basis": "structure_guided_topology_alignment",
              "manifest": {"path": str(manifest_path.resolve()), "sha256": _hash(manifest_path)},
              "cases": cases, "case_count": len(cases), "batches": batches,
              "segmentation_runtimes": [batch["segmentation_runtime"] for batch in batches],
              "total_complete_forwards": sum(row["body_forward_span_ms"]["count"] for row in cases),
              "source_positive_events": sum(row["scan_counts"]["positive_events"] for row in cases),
              "geometry_group_count": sum(len(row["geometry_groups"]) for row in cases),
              "completed_source_scan_seconds": sum(row["elapsed_seconds"] for row in cases),
              "source_scans": len(cases), "raw_sources_rescanned_by_merge": False,
              "limitations": ["Historical and current extraction core generations remain distinct.",
                              "The first execution stopped before its tenth source when a Sim case changed; its nine completed sources were not rescanned.",
                              "First-execution final RSS was unavailable because that execution stopped before the final receipt; later per-source RSS is recorded.",
                              "Mixed geometry case means are descriptive only; comparisons must use geometry_groups."]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    lines = ["# 新增 26 源 Decode 主体提取", "",
             "每个完整主体均匹配 Sim 声明的完整层序列并由词表投影闭合；这是结构引导推断，不是 Host/module 标记。",
             "前 9 源保留旧核心版本，后 17 源使用补齐 mHC 与 MLA ABI 的新版本。各源仅完整扫描一次；首次执行在第 10 源前因模型配置变化停止，9 个已完成结果没有重扫。", "",
             "| Case | Body 次数 | 几何桶 | Mean ms | P50 ms | P90 ms | Activity mean ms | 内部未覆盖 mean ms |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in cases:
        s = row["body_forward_span_ms"]
        values = [s["mean"], s["p50"], s["p90"], row["body_activity_ms"]["mean"], row["body_internal_gap_ms"]["mean"]]
        cells = " | ".join("—" if value is None else f"{value:.6f}" for value in values)
        lines.append(f"| {row['case_id']} | {s['count']} | {len(row['geometry_groups'])} | {cells} |")
    lines += ["", f"合计 {result['case_count']} 源、{result['total_complete_forwards']} 个完整主体、{result['geometry_group_count']} 个执行几何桶、{result['source_positive_events']} 条正事件。",
              "表中的跨桶均值仅描述源数据，不用于混合工况评分。客户端并发与执行 B/q 分开；图 padding、排空阶段的小 batch 都保留。",
              "Activity 为非调度 wrapper 的设备事件区间并集，包含真实通信协议内等待，不等于 PMU 忙时。内部未覆盖时间不全部归因为 Host，也不从主体 span 扣除。",
              "新 GLM Flash 是 45 层 KDA/MLA；旧 78 层 GLM 是另一结构。Qwen397 使用官方独立 60 层条件声明，原 checkpoint 配置的完整同一性限制保留在 manifest。", ""]
    output.with_suffix(".md").write_text("\n".join(lines))
    return {key: result[key] for key in ("case_count", "total_complete_forwards", "source_positive_events", "geometry_group_count")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--batch", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(merge(args.manifest, args.batch, args.output)))
