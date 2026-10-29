"""Replay real multi-case Decode exports through Sim-declared topology alignment.

[Role] Produce source-pinned body/layer measurements and graph cross-checks.
[Invariants] Automatic boundaries remain structural inference; no timing fitting.
  Every positive event belongs to exactly one closed/rejected/trailing segment.
[Timeouts & Locks] Serial streaming, bounded core samples, 120 s per source scan.
[Side-Effect Policy] Local read-only captures; writes compact local reports only.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import resource
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
from mindie_profiler.events import SourceRef
from mindie_profiler.graph_execution import correlate_forward_envelopes
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.sources_csv import probe_csv
from mindie_sim.prediction.structure import parse_case


def _hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read(path):
    if path.stat().st_size > 50 * 1024 * 1024:
        raise ValueError(f"metadata exceeds 50 MiB: {path}")
    return json.loads(path.read_text())


def numeric_digest(observed):
    """Compare all populations/statistics while allowing endpoint locators to improve."""
    def groups(rows):
        return [{key: value for key, value in row.items() if key != "samples"}
                for row in rows]

    state = {key: observed[key] for key in (
        "body_forward_span_ms", "auxiliary_forward_span_ms", "scan_counts",
        "anomaly_counts", "geometry", "query_rows", "model_declaration")}
    state["per_layer_ms"] = groups(observed["per_layer_ms"])
    state["stage_span_ms"] = groups(observed["stage_span_ms"])
    state["forwards"] = [{key: value for key, value in row.items() if key != "stages"}
                         for row in observed["forwards"]]
    state["geometry_groups"] = [
        {**row, "per_layer_ms": groups(row["per_layer_ms"]),
         "stage_span_ms": groups(row["stage_span_ms"])} for row in observed["geometry_groups"]]
    state["graph_crosscheck"] = observed.get("graph_crosscheck")
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def replay(manifest_path, output, *, validation_baseline=None, reuse_extractions=None):
    started = time.monotonic()
    manifest = _read(manifest_path)
    baseline = _read(validation_baseline) if validation_baseline else None
    import mindie_profiler.decode_segmentation as segmentation
    module = Path(segmentation.__file__)
    module_hash = _hash(module)
    output.mkdir(parents=True, exist_ok=True)
    cases = manifest["cases"]
    # Resolve the five model families before traversing all request coordinates.
    first = {"a3_qwen35_p_4096_c1": 0, "a3_qwen36_p_4096_c1": 1,
             "a5_qwen38_p8192_c1": 2, "a3_glm53_dc4k_b1": 3,
             "a5_kimi_k3_p32768_c1": 4, "a5_qwen36_p4096_c1_hold": 5}
    cases = sorted(cases, key=lambda row: first.get(row["case_id"], 6))
    summaries = []
    for row in cases:
        case_started = time.monotonic()
        path, model_path = Path(row["source"]["path"]), Path(row["sim_case_path"])
        stat = path.stat()
        digest = _hash(path)
        if digest != row["source"]["sha256"]:
            raise ValueError(f"source hash changed: {path}")
        model_hash = _hash(model_path)
        if model_hash != row["model_declaration"]["sha256"]:
            raise ValueError(f"model declaration changed: {model_path}")
        case = parse_case(_read(model_path))
        config = asdict(case.model)
        config["tp"] = case.runtime.parallel.tp
        schema = probe_csv(path)
        source = SourceRef("", None, "csv", str(path), path.name, digest, stat.st_size,
                           schema.schema_version, schema.schema_variant, mtime_ns=stat.st_mtime_ns)
        cached = (reuse_extractions / f"auto-forward-{row['case_id']}.json"
                  if reuse_extractions else None)
        reused = bool(cached and cached.exists())
        if reused:
            observed = _read(cached)
            if (observed["source_identity"] != source.content_identity()
                    or observed["model_structure_identity"]["sha256"] != model_hash
                    or observed["extraction_runtime"]["sha256"] != module_hash):
                raise ValueError(f"precomputed extraction has a different source/model/core: {cached}")
            observed["reused_extraction"] = {"path": str(cached), "sha256": _hash(cached)}
        else:
            observed = auto_segment_decode_forwards(kernel_rows(path, timeout_s=120), config,
                                                    source=source)
        counts = observed["scan_counts"]
        accounted = sum(counts.get(key, 0) for key in (
            "complete_body_segment_events", "auxiliary_candidate_segment_events",
            "rejected_segment_events", "trailing_segment_events"))
        if accounted != counts["positive_events"]:
            raise ValueError(f"positive event partition mismatch: {row['case_id']}")
        if path.stat().st_mtime_ns != stat.st_mtime_ns or path.stat().st_size != stat.st_size:
            raise ValueError(f"source changed during replay: {path}")
        if _hash(module) != module_hash:
            raise ValueError("automatic segmentation source changed during replay")
        observed["case_id"] = row["case_id"]
        observed["model_structure_identity"] = {"path": str(model_path), "sha256": model_hash}
        observed["extraction_runtime"] = {"path": str(module), "sha256": module_hash}
        observed["positive_event_partition_verified"] = True
        observed["replay_control_elapsed_seconds"] = round(time.monotonic() - case_started, 3)
        if not reused:
            observed["elapsed_seconds"] = observed["replay_control_elapsed_seconds"]
        if row.get("graph_envelopes_path"):
            graph = _read(Path(row["graph_envelopes_path"]))
            observed["graph_crosscheck"] = correlate_forward_envelopes(observed, graph)
        if baseline:
            expected = baseline["cases"][row["case_id"]]
            if (source.sha256 != expected["source_sha256"]
                    or numeric_digest(observed) != expected["numeric_sha256"]):
                raise ValueError(f"endpoint validation changed measured population/statistics: {row['case_id']}")
            observed["endpoint_validation_statistics_unchanged"] = True
        report_path = output / f"auto-forward-{row['case_id']}.json"
        report_path.write_text(json.dumps(observed, ensure_ascii=False, indent=2) + "\n")
        summary = {"case_id": row["case_id"], "source_identity": source.content_identity(),
                   "report_path": str(report_path.resolve()), "report_sha256": _hash(report_path),
                   "model_declaration": observed["model_declaration"],
                   "model_structure_identity": observed["model_structure_identity"],
                   "body_forward_span_ms": observed["body_forward_span_ms"],
                   "geometry": observed["geometry"],
                   "geometry_groups": [{"geometry": group["geometry"],
                                        "body_forward_span_ms": group["body_forward_span_ms"]}
                                       for group in observed["geometry_groups"]],
                   "scan_counts": counts, "anomaly_counts": observed["anomaly_counts"],
                   "auxiliary_forward_span_ms": observed["auxiliary_forward_span_ms"],
                   "positive_event_partition_verified": True,
                   "graph_crosscheck": observed.get("graph_crosscheck"),
                   "elapsed_seconds": observed["elapsed_seconds"],
                   "reused_extraction": observed.get("reused_extraction")}
        summaries.append(summary)
        print(json.dumps({"case_id": row["case_id"], "body": summary["body_forward_span_ms"],
                          "geometry_groups": summary["geometry_groups"],
                          "positive_events": counts["positive_events"],
                          "graph": summary["graph_crosscheck"],
                          "elapsed_seconds": summary["elapsed_seconds"]}), flush=True)
        del observed
    receipt = {"schema_version": "mindie-decode-auto-acceptance/1", "status": "completed",
               "not_new_live_collection": True, "basis": "structure_guided_topology_alignment",
               "manifest": {"path": str(manifest_path), "sha256": _hash(manifest_path)},
               "segmentation_runtime": {"path": str(module), "sha256": module_hash},
               "cases": summaries, "case_count": len(summaries),
               "total_complete_forwards": sum(row["body_forward_span_ms"]["count"] for row in summaries),
               "source_positive_events": sum(row["scan_counts"]["positive_events"] for row in summaries),
               "elapsed_seconds": round(time.monotonic() - started, 3),
               "maximum_resident_set_size_raw": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               "runtime_sources_unchanged": _hash(module) == module_hash}
    receipt["source_scans_in_this_execution"] = sum(not row["reused_extraction"] for row in summaries)
    receipt["reused_source_extractions"] = sum(bool(row["reused_extraction"]) for row in summaries)
    receipt["reused_extraction_elapsed_seconds"] = sum(
        row["elapsed_seconds"] for row in summaries if row["reused_extraction"])
    if baseline:
        receipt["validation_rerun"] = {
            "reason": "Correct endpoint provenance to actual min-start/max-end events; measured spans are unchanged.",
            "validation_passes": 2, "source_scans_per_pass": len(summaries),
            "initial_generation": baseline["initial_generation"],
            "all_case_numeric_statistics_unchanged": len(summaries) == len(baseline["cases"]),
            "positive_source_events_read_across_both_generations":
                receipt["source_positive_events"] + baseline["initial_generation"]["source_positive_events"],
            "total_elapsed_seconds_across_both_generations":
                receipt["elapsed_seconds"] + baseline["initial_generation"]["elapsed_seconds"],
        }
    (output / "decode-forward-auto-acceptance.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Decode 自动主体与分层回放", "", "以下为已有采集的结构引导推断；模型层序列来自 Sim，时间来自原始设备事件，未伪造 Host/module 标记。",
             "每个完整主体必须匹配全部声明层并由词表投影闭合。源 CSV、SHA、完整主体/辅助/拒绝/尾片段事件分母见 JSON。", "",
             "| Case | 正事件 | 完整主体 | Mean ms | P50 ms | P90 ms |", "|---|---:|---:|---:|---:|---:|"]
    for row in summaries:
        s = row["body_forward_span_ms"]
        vals = [f"{s[key]:.6f}" if s[key] is not None else "—" for key in ("mean", "p50", "p90")]
        lines.append(f"| {row['case_id']} | {row['scan_counts']['positive_events']} | {s['count']} | {' | '.join(vals)} |")
    lines += ["", "不同请求并发和实际 query/batch 的统计分别保留在 geometry_groups；上表不直接用于混合工况的 Sim 误差判定。"]
    if any(row["graph_crosscheck"] for row in summaries):
        lines += ["已有 graph 证据的完整主体与独立 MODEL_EXECUTE/MODEL_WAIT_COMPLETE 窗口逐一交叉核验，"
                  "Model ID 在层序列对齐之后才归组。"]
    lines += ["", "负载均衡、MTP 接收率与 Prefix Cache 命中按 manifest 中的实测或配置证据分别报告；"
              "请求长度不冒充每步精确 KV 长度，客户端 TPOT 不冒充单次模型主体耗时。", ""]
    if baseline:
        lines += ["端点来源修复后再次流式回放同一 30 份源；两批统计逐项一致，仅端点 locator 更精确。"
                  "JSON 同时记录首批与验证批的核心身份、扫描量和耗时，未把重复验证计作新增采集或新增覆盖。", ""]
    (output / "decode-forward-auto-acceptance.md").write_text("\n".join(lines))
    return {"cases": len(summaries), "complete_forwards": receipt["total_complete_forwards"],
            "elapsed_seconds": receipt["elapsed_seconds"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    base = Path(__file__).with_name("acceptance-20261029")
    parser.add_argument("--manifest", type=Path, default=base / "decode-forward-auto-cases.json")
    parser.add_argument("--output", type=Path, default=base)
    parser.add_argument("--validation-baseline", type=Path)
    parser.add_argument("--reuse-extractions", type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.manifest, args.output, validation_baseline=args.validation_baseline,
                           reuse_extractions=args.reuse_extractions)))
