"""Run source-pinned operator replay in one bounded process per source and phase.

[Role] Orchestrate the existing extraction/costing tools without another mapper.
[Invariants] Context is explicit request evidence, q/B is measured; all sources
  retain their unselected populations. Event activity is not additive body time.
[Timeouts & Locks] 240s extraction; comparison sums per-program budgets plus 180s.
[Side-Effect Policy] Reads retained local captures; writes local replay artifacts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from replay_body_operator_families import identity, read, runtime_identity, write
from replay_fusion_cohorts import _program_key


def queue_runtime():
    from compare_body_operator_families import prediction_runtime_identity

    result = {**runtime_identity(), **prediction_runtime_identity()}
    for path in (Path(__file__).resolve(), Path(__file__).with_name("replay_fusion_cohorts.py")):
        pin = identity(path)
        result[pin["path"]] = pin["sha256"]
    return result


def run(command, log_path, timeout):
    started = time.perf_counter()
    with log_path.open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f"operator replay exited {result.returncode}: {log_path}")
    return {"command": command, "elapsed_seconds": time.perf_counter() - started,
            "timeout_seconds": timeout, "log": identity(log_path), "returncode": result.returncode}


def summarize(case_reports, output, runtime, manifest, receipt):
    from compare_body_operator_families import render

    cases, pools, executions = [], [], []
    for case_id, directory, execution in case_reports:
        report = read(directory / "body-operator-family-scoreboard.json")
        for row in report["cases"]:
            actual = read(row["actual_identity"]["path"])
            cases.append({**row, **{key: actual[key] for key in (
                "source_forward_count", "unselected_source_forward_count", "geometry_selection",
                "conditional_context_tokens")}})
        pools.extend(read(directory / "steady-layer-pooled.json")["cases"])
        executions.append({"case_id": case_id, **execution})
    result = {"schema_version": "mindie-body-operator-comparison/1", "cases": cases,
              "status": "partial" if any(case["comparison_status_counts"].get("prediction_failed") for case in cases) else "completed",
              "runtime_source_identity": read(case_reports[0][1] / "body-operator-family-scoreboard.json")["runtime_source_identity"],
              "runtime_sources_unchanged": queue_runtime() == runtime,
              "manifest_identity": identity(manifest), "receipt_identity": identity(receipt),
              "source_process_executions": executions, "raw_capture_scans": len(case_reports),
              "coverage_status": "partial" if any(row["unscored_event_count"] for case in cases for row in case["families"]) else "complete"}
    write(output / "body-operator-family-scoreboard.json", result)
    (output / "body-operator-family-scoreboard.md").write_text(render(result))
    write(output / "steady-layer-pooled.json", {"schema_version": "mindie-steady-layer-pooled/1",
          "cases": pools, "source_receipt_identity": identity(receipt),
          "population_basis": "pooled_layer_calls_excluding_layer0"})
    lines = ["# Kimi 主体算子活动量：按结构区域排列", "",
             "完整主体主几何内的原生事件按结构区域分组，每组按实测活动毫秒/Forward降序排列。",
             "活动量是事件时长之和，包含真实通信等待且可能跨 stream 重叠，不能相加当作主体跨度。未匹配不等于 Sim 漏算；完整成本/契约覆盖见全族表。", ""]
    for case in cases:
        lines += ["## " + case["case_id"], ""]
        grouped = {"KDA attention": [], "MLA attention": [], "FFN": []}
        for family in case["families"]:
            for group in family.get("structure_groups", ()):
                bucket = "FFN" if group["block"] == "ffn" else group["attention_kind"].upper() + " attention"
                if bucket not in grouped:
                    continue
                stats = group["observed_us"]
                grouped[bucket].append((stats["mean"] * stats["count"] / 1000 / case["forward_count"], family, stats))
        for name, rows in grouped.items():
            lines += ["### " + name, "", "| Native family / role | Calls | Mean us | Activity ms/F | Strict scored / family calls |",
                      "|---|---:|---:|---:|---:|"]
            for activity, family, stats in sorted(rows, key=lambda row: -row[0]):
                role = family["declared_role"].replace("|", " + ")
                lines.append(f"| {family['native_operator_type']} / {role} | {stats['count']} | {stats['mean']:.3f} | {activity:.6f} | {family['scored_event_count']} / {family['observed_us']['count']} |")
            lines.append("")
    (output / "body-operator-structure-contributions.md").write_text("\n".join(lines))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--case-dir", type=Path, help="Use byte-identical case declarations from a selected runtime checkout")
    parser.add_argument("--compare-timeout", type=float, default=120)
    args = parser.parse_args()
    manifest, receipt = read(args.manifest), read(args.receipt)
    source_entries = {row["case_id"]: row for row in receipt["cases"]}
    runtime = queue_runtime()
    results = []
    scripts = Path(__file__).resolve().parent
    for case in manifest["cases"]:
        case_id = case["case_id"]
        entry = source_entries[case_id]
        if case["source"]["sha256"] != entry["source_identity"]["sha256"]:
            raise ValueError(f"manifest and receipt source differ: {case_id}")
        context = case["scenario_evidence"]["client"]["input_len"]
        if not isinstance(context, int):
            raise ValueError(f"explicit representative context is unavailable: {case_id}")
        directory = (args.output_dir / case_id).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        selected_case = (args.case_dir / Path(case["sim_case_path"]).name
                         if args.case_dir else Path(case["sim_case_path"]))
        if identity(selected_case)["sha256"] != case["model_declaration"]["sha256"]:
            raise ValueError(f"selected case differs from retained body declaration: {case_id}")
        extract = [sys.executable, str(scripts / "replay_body_operator_families.py"),
                   "--receipt", str(args.receipt.resolve()), "--case-id", case_id,
                   "--output-dir", str(directory), "--context-tokens", str(context), "--geometry-limit", "1"]
        if args.case_dir:
            extract.extend(["--case-dir", str(args.case_dir.resolve())])
        extraction = run(extract, directory / "extract.log", 240)
        mappings = list(directory.glob("*.mapping.json"))
        programs = {_program_key(row) for mapping in mappings for window in read(mapping)["windows"] for row in window["cohorts"]}
        compare = [sys.executable, str(scripts / "compare_body_operator_families.py"),
                   "--output-dir", str(directory), "--compare-timeout", str(args.compare_timeout)]
        comparison = run(compare, directory / "compare.log", max(1, len(programs)) * args.compare_timeout + 180)
        if queue_runtime() != runtime:
            raise ValueError("operator queue runtime changed")
        results.append((case_id, directory, {"extraction": extraction, "comparison": comparison}))
        print(json.dumps({"case_id": case_id, "completed": len(results), "total": len(manifest["cases"]), "programs": len(programs)}), flush=True)
    report = summarize(results, args.output_dir, runtime, args.manifest, args.receipt)
    if report["status"] != "completed":
        raise SystemExit("operator comparison contains visible prediction failures")


if __name__ == "__main__":
    main()
