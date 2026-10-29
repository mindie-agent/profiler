"""Separate GLM Flash45 device evidence, GLM78 evidence and serving-only history.

[Role] Assemble model/body, declared-layer and operator-source coverage for GLM.
[Invariants] GLM78 and Flash45 are different models. Serving TPOT never substitutes
  for body timing; whole-window operator summaries are not body-scoped cohorts.
[Timeouts & Locks] Bounded local metadata and sequential tar headers; no locks.
[Side-Effect Policy] Writes local evidence only; no raw kernel rescan or prediction.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import tarfile

from build_decode_forward_cases import _read
from summarize_decode_geometry import geometry_rows, identity


def summarize(profiler_examples, data_root, output):
    entries = []
    for label, folder in (("flash45_kda_mla", "acceptance-20261030-expanded"),
                          ("glm78_dsa", "acceptance-20261029")):
        base = profiler_examples / folder
        manifest_path = base / "decode-forward-auto-cases.json"
        manifest = _read(manifest_path)
        for case in manifest["cases"]:
            if "glm" not in case["case_id"]:
                continue
            path = base / f"auto-forward-{case['case_id']}.json"
            report = _read(path)
            rows = geometry_rows(case, report, path)
            source = Path(case["source"]["path"])
            op_summary = source.with_name("op_statistic.csv")
            inventory = None
            if op_summary.exists():
                with op_summary.open(newline="") as stream:
                    operators = list(csv.DictReader(stream))
                inventory = {"source": identity(op_summary), "rows": operators,
                             "scope": "whole_capture_including_prefill_auxiliary_and_partial_segments",
                             "body_scoped": False, "event_count_is_not_the_kernel_csv_positive_population": True}
            entries.append({"case_id": case["case_id"], "model_group": label,
                            "model_declaration": report["model_declaration"],
                            "manifest": identity(manifest_path), "extraction": identity(path),
                            "source_identity": report["source_identity"],
                            "extraction_runtime": report["extraction_runtime"],
                            "source_scenario": case["scenario_evidence"],
                            "body_forward_span_ms": report["body_forward_span_ms"],
                            "body_activity_ms": report.get("body_activity_ms"),
                            "body_internal_gap_ms": report.get("body_internal_gap_ms"),
                            "activity_status": "measured_interval_union" if "body_activity_ms" in report else "not_recorded_by_historical_extraction_generation",
                            "geometry_groups": rows,
                            "operator_level": {"body_scoped_comparison_status": "not_produced_by_this_summary",
                                               "window_inventory": inventory,
                                               "absence_is_not_a_sim_omission": True}})
    serving = []
    campaigns = [
        ("a5/2026-10-23/glm53-a5", "glm53-a5-report.md"),
        ("a5/2026-10-23/glm53-tp8", "tp8-report.md"),
        ("a5/2026-10-24/glm-c2c8", "supplement.md")]
    for relative, report_name in campaigns:
        root = data_root / relative
        source_report = root / report_name
        lines = [{"line": n, "text": text} for n, text in enumerate(source_report.read_text().splitlines(), 1)
                 if any(key in text for key in ("Glm5NextForConditionalGeneration", "45 layers", "config.json` sha256", "speculative_config=None"))]
        exported = [str(path.relative_to(root)) for path in root.rglob("*")
                    if path.is_file() and (path.suffix == ".db" or any(key in path.name for key in ("kernel_details", "op_summary", "trace_view", "pytorch_profiler", ".pt.trace")))]
        archives = []
        for archive in sorted(root.glob("*.tar.gz")):
            count, kernel_members = 0, []
            with tarfile.open(archive, "r|gz") as stream:
                for member in stream:
                    count += 1
                    if member.name.endswith(".db") or any(key in member.name for key in ("kernel_details", "op_summary", "trace_view", "pytorch_profiler", ".pt.trace")):
                        kernel_members.append(member.name)
            archives.append({**identity(archive), "member_count": count, "kernel_source_members": kernel_members})
        cells = []
        for cell_file in root.glob("raw/*/cells.csv"):
            with cell_file.open(newline="") as stream:
                cells.append({"source": identity(cell_file), "rows": list(csv.DictReader(stream)),
                              "scope": "client_benchmark_or_metrics; not device model body"})
        serving.append({"campaign": relative, "model_group": "flash45_bf16_serving_history",
                        "retained_report": identity(source_report), "model_evidence_lines": lines,
                        "exported_kernel_sources": exported, "archive_inventories": archives,
                        "serving_cells": cells,
                        "body_extraction_status": "unavailable_no_retained_kernel_or_trace_export" if not exported and not any(a["kernel_source_members"] for a in archives) else "kernel_source_discovered_requires_selection",
                        "body_forward_span_ms": None, "per_layer_ms": None})
    result = {"schema_version": "mindie-glm-three-level-evidence/1", "device_cases": entries,
              "device_case_count": len(entries), "device_forward_count": sum(row["body_forward_span_ms"]["count"] for row in entries),
              "serving_only_campaigns": serving, "raw_kernel_scans": 0, "predictions_executed": 0,
              "limitations": ["Flash45 KDA/MLA and GLM78 DSA remain separate model groups.",
                              "Historical GLM78 activity is unavailable until a justified operator pass collects it; historical spans remain unchanged.",
                              "Steady summaries exclude Layer0 but preserve full body spans; medians of layer P50s are explicitly not pooled-call P50.",
                              "Whole-capture operator inventory includes prefill/auxiliary work and cannot be added to body-scoped time."]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    lines = ["# GLM Decode：主体、分层与算子证据", "", "新 Flash 使用独立 45 层 KDA/MLA 结构；历史 GLM78 DSA 另组展示。以下统计全部复用已验收提取，无新增原始 kernel 扫描或 Sim 预测。", "",
             "| 模型组 / Case | 完整 Body | 几何桶 | Body P50 ms | Body activity mean ms |", "|---|---:|---:|---:|---:|"]
    for row in entries:
        activity = row["body_activity_ms"]
        value = f"{activity['mean']:.6f}" if activity else "历史版本未记录"
        lines.append(f"| {row['model_group']} / {row['case_id']} | {row['body_forward_span_ms']['count']} | {len(row['geometry_groups'])} | {row['body_forward_span_ms']['p50']:.6f} | {value} |")
    lines += ["", "每个几何桶的 Layer0、排除 Layer0 后的 attention×FFN 类型统计及源身份均见 JSON。跨桶的表格值仅描述数据，Sim 对账应逐桶进行。",
              "算子层已保留新七源的原始 op_statistic 入口和整窗统计，其口径包括 prefill/辅助段；尚未在本摘要中生成 Body 内角色对账，因此没有把未关联的算子说成 Sim 漏算。", "",
              "历史 A5 的 glm53-a5、glm53-tp8、glm-c2c8 三个目录都是 Flash45 BF16 服务压测。目录及四个原始 tar 均未发现 kernel_details/op_summary/trace/DB，只有客户端与服务指标；它们的 TPOT 保留为 serving 事实，Body 和 Layer 耗时保持空值。", ""]
    output.with_suffix(".md").write_text("\n".join(lines))
    return {key: result[key] for key in ("device_case_count", "device_forward_count", "raw_kernel_scans", "predictions_executed")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "acceptance-20261030-glm/glm-three-level-evidence.json")
    args = parser.parse_args()
    print(json.dumps(summarize(Path(__file__).parent, Path("/Volumes/data/mindie-sim-data"), args.output)))
