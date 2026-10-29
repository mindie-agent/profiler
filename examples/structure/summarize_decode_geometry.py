"""Rank complete Decode geometry populations and summarize declared layer types.

[Role] Give prediction consumers every measured bucket with explicit population.
[Invariants] Layer statistics keep their original invocation quantiles; medians of
  per-layer P50 values are not pooled-call P50. Unassociated is not a Sim omission.
[Timeouts & Locks] One bounded saved report at a time; metadata-only Sim parsing.
[Side-Effect Policy] No raw profiling scan, device initialization or prediction.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from build_decode_forward_cases import _hash, _read
from mindie_sim.prediction.structure import parse_case


def identity(path):
    return {"path": str(path.resolve()), "sha256": _hash(path)}


def layer_groups(layers, plans):
    buckets = defaultdict(list)
    for layer in layers:
        if layer["layer_id"] == 0:
            continue
        plan = plans[layer["layer_id"]]
        buckets[(plan.attention, layer["kind"])].append(layer)
    result = []
    for (attention, kind), selected in sorted(buckets.items()):
        count = sum(row["stats"]["count"] for row in selected)
        result.append({"attention_kind": attention, "ffn_layer_kind": kind,
                       "layer_ids": [row["layer_id"] for row in selected],
                       "declared_layer_count": len(selected), "observed_layer_call_count": count,
                       "observed_call_weighted_mean_ms": sum(row["stats"]["mean"]*row["stats"]["count"] for row in selected)/count,
                       "median_of_layer_call_p50_ms": statistics.median(row["stats"]["p50"] for row in selected),
                       "pooled_layer_call_p50_ms": None,
                       "activity_call_weighted_mean_ms": sum(row["activity_ms_stats"]["mean"]*row["stats"]["count"] for row in selected)/count if all("activity_ms_stats" in row for row in selected) else None,
                       "internal_gap_call_weighted_mean_ms": sum(row["internal_gap_ms_stats"]["mean"]*row["stats"]["count"] for row in selected)/count if all("internal_gap_ms_stats" in row for row in selected) else None,
                       "quantile_basis": "median_of_complete_per_layer_invocation_P50; not pooled invocation P50"})
    return result


def geometry_rows(case, report, report_path):
    declaration = parse_case(_read(Path(case["sim_case_path"]))).model
    plans = [plan for plan in declaration.layer_plans if not plan.mtp]
    if len(plans) != report["model_declaration"]["layers"] or declaration.hidden_size != report["model_declaration"]["hidden_size"]:
        raise ValueError(f"current declared topology differs from saved extraction: {case['case_id']}")
    total = report["body_forward_span_ms"]["count"]
    groups = report["geometry_groups"]
    order = sorted(range(len(groups)), key=lambda index: (-groups[index]["body_forward_span_ms"]["count"], index))
    rank = {index: number+1 for number, index in enumerate(order)}
    rows = []
    for index, group in enumerate(groups):
        layers = group["per_layer_ms"]
        zero = next((row for row in layers if row["layer_id"] == 0), None)
        count = group["body_forward_span_ms"]["count"]
        rows.append({"case_id": case["case_id"], "geometry_index": index, "geometry": group["geometry"],
                     "rank_within_case_by_forward_count": rank[index], "primary_population": rank[index] == 1,
                     "forward_count": count, "case_forward_count": total, "case_population_fraction": count/total,
                     "model_declaration": report["model_declaration"], "source_identity": report["source_identity"],
                     "extraction_identity": identity(report_path), "model_structure_identity": report["model_structure_identity"],
                     "extraction_runtime": report["extraction_runtime"],
                     "client": case["scenario_evidence"].get("client"),
                     "body_forward_span_ms": group["body_forward_span_ms"],
                     "body_activity_ms": group.get("body_activity_ms"), "body_internal_gap_ms": group.get("body_internal_gap_ms"),
                     "layer0": {key: zero.get(key) for key in ("kind", "stats", "activity_ms_stats", "internal_gap_ms_stats")} if zero else None,
                     "steady_layer_groups": layer_groups(layers, plans),
                     "source_role_basis": "complete declared topology plus tensor contracts; conditional device occurrence alignment, not Host binding",
                     "prediction_status": "not_executed_by_this_index", "sim_omission_claim": False})
    return rows


def summarize(manifest_path, receipt_path, output):
    manifest, receipt = _read(manifest_path), _read(receipt_path)
    cases = {row["case_id"]: row for row in manifest["cases"]}
    all_rows = []
    for evidence in receipt["cases"]:
        path = Path(evidence["report_path"])
        if _hash(path) != evidence["report_sha256"]:
            raise ValueError(f"saved extraction changed: {path}")
        report = _read(path)
        all_rows.extend(geometry_rows(cases[evidence["case_id"]], report, path))
    primary = [row for row in all_rows if row["primary_population"]]
    result = {"schema_version": "mindie-decode-geometry-priority/1", "manifest": identity(manifest_path),
              "extraction_receipt": identity(receipt_path), "case_count": len(cases),
              "geometry_group_count": len(all_rows), "total_forward_count": sum(row["forward_count"] for row in all_rows),
              "primary_geometry_forward_count": sum(row["forward_count"] for row in primary),
              "ranking_basis": "largest observed complete-forward population within each source; all secondary buckets remain retained",
              "rows": sorted(all_rows, key=lambda row: (row["case_id"], row["rank_within_case_by_forward_count"])),
              "limitations": ["This index does not run Sim or call missing cost predictions model omissions.",
                              "Per-case primary buckets prioritize coverage without discarding smaller execution geometries.",
                              "Layer0 is retained separately; body spans are unchanged.",
                              "Steady group means are exact weighted means; pooled call P50 needs complete per-invocation samples and stays null here."]}
    if result["total_forward_count"] != receipt["total_complete_forwards"]:
        raise ValueError("geometry population does not equal the receipt population")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    lines = ["# Decode 执行几何与优先对账索引", "", "每源优先桶按完整 Forward 数量选取，全部其他桶继续保留；下表只显示优先桶。", "",
             "| Case | M / B / q | 优先桶 / 全源 Body | 覆盖 | Body P50 ms | Layer0 P50 ms |", "|---|---|---:|---:|---:|---:|"]
    for row in sorted(primary, key=lambda row: row["case_id"]):
        g = row["geometry"]
        label = "/".join(str(g[key]) for key in ("query_rows", "sequences_per_replica", "tokens_per_sequence"))
        lines.append(f"| {row['case_id']} | {label} | {row['forward_count']} / {row['case_forward_count']} | {row['case_population_fraction']:.1%} | {row['body_forward_span_ms']['p50']:.6f} | {row['layer0']['stats']['p50']:.6f} |")
    lines += ["", f"完整分母：{result['case_count']} 源、{result['geometry_group_count']} 桶、{result['total_forward_count']} 个主体。各源优先桶合计覆盖 {result['primary_geometry_forward_count']} 个主体。",
              "M/B/q 是实测执行几何，可能包含 padding；客户端 c 单独保留。稳态组排除 Layer0，按 Sim attention 结构及 FFN 类型交叉分组；同组单层 P50 的中位数不冒充所有调用的 pooled P50。", ""]
    output.with_suffix(".md").write_text("\n".join(lines))
    return {key: result[key] for key in ("case_count", "geometry_group_count", "total_forward_count", "primary_geometry_forward_count")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(summarize(args.manifest, args.receipt, args.output)))
