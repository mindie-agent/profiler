"""Replay the retained Flash families and native buckets with reviewed source cases.

[Role] Sequence the existing fresh repricer and native reference driver.
[Invariants] Retain original observed histograms/context; source cases only change
  declarations. Native references stay separate from strict cohort populations.
[Timeouts & Locks] One source worker at a time; outer budget covers all programs.
[Side-Effect Policy] Local saved evidence reads and new result files; zero raw scans.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

from compare_glm_native_partitions import render as render_native
from replay_body_operator_families import identity, read, write
from reprice_body_operator_families import render_repriced


def merge(paths, output, *, native):
    first, cases, elapsed = None, [], 0.0
    for path in paths:
        report = read(path)
        if first is None:
            first = {k: v for k, v in report.items() if k not in {"cases", "elapsed_seconds"}}
        if report["runtime_source_identity"] != first["runtime_source_identity"]:
            raise ValueError("source_replay_runtime_changed")
        cases.extend(report["cases"])
        elapsed += report["elapsed_seconds"]
    report = {**first, "cases": cases, "elapsed_seconds": elapsed,
              "status": "completed" if all(read(p)["status"] == "completed" for p in paths) else "partial",
              "input_receipts": [identity(p) for p in paths], "aggregation_only_no_new_predictions": True}
    write(output, report)
    output.with_suffix(".md").write_text((render_native if native else render_repriced)(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--body-manifest", type=Path, required=True)
    parser.add_argument("--native-dir", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-source-commit", required=True)
    parser.add_argument("--phase", choices=("families", "native"), required=True)
    args = parser.parse_args()
    inputs = read(args.inputs)
    declarations = {c["case_id"]: c for c in read(args.body_manifest)["cases"]}
    scripts = Path(__file__).resolve().parent
    paths, attempts = [], []
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for item in inputs["cases"]:
        source = item["case_id"]
        declared = declarations[source]
        case_path = Path(declared["sim_case_path"])
        if identity(case_path)["sha256"] != declared["model_declaration"]["sha256"]:
            raise ValueError("source_complete_case_changed:" + source)
        for field in ("actual_identity", "mapping_identity"):
            if identity(item[field]["path"])["sha256"] != item[field]["sha256"]:
                raise ValueError("retained_operator_input_changed:" + source)
        directory = args.output_dir / args.phase / source
        directory.mkdir(parents=True, exist_ok=True)
        if args.phase == "families":
            command = [sys.executable, str(scripts / "reprice_body_operator_families.py"),
                "--actual", item["actual_identity"]["path"], "--mapping", item["mapping_identity"]["path"],
                "--case", str(case_path), "--output-dir", str(directory),
                "--variant", "source-complete-" + args.runtime_source_commit[:8],
                "--runtime-source-commit", args.runtime_source_commit, "--skip-references"]
            mapping = read(item["mapping_identity"]["path"])
            timeout = sum(len(w["cohorts"]) for w in mapping["windows"]) * 120 + 180
            filename = "body-operator-family-scoreboard.json"
        else:
            partitions = [p / (source + "-native-partitions.json") for p in args.native_dir
                          if (p / (source + "-native-partitions.json")).exists()]
            if len(partitions) != 1:
                raise ValueError("native_source_partition_not_unique:" + source)
            command = [sys.executable, str(scripts / "compare_glm_native_partitions.py"),
                "--partition", str(partitions[0]), "--case", str(case_path),
                "--output-dir", str(directory), "--runtime-source-commit", args.runtime_source_commit,
                "--accepted-kda", "--source-mechanisms"]
            timeout, filename = 190, "glm-native-reference-scoreboard.json"
        started = time.perf_counter()
        with (directory / "run.log").open("w") as log:
            child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        attempts.append({"case_id": source, "returncode": child.returncode,
            "elapsed_seconds": time.perf_counter()-started, "command": command,
            "timeout_seconds": timeout, "log_path": str(directory / "run.log")})
        write(args.output_dir / (args.phase + "-execution.json"), {"attempts": attempts,
            "inputs_identity": identity(args.inputs), "body_manifest_identity": identity(args.body_manifest),
            "raw_capture_reads": 0, "generator_identity": identity(Path(__file__))})
        print(json.dumps({"case_id": source, "phase": args.phase, "returncode": child.returncode,
                          "completed": len(attempts), "total": len(inputs["cases"])}), flush=True)
        if child.returncode:
            raise SystemExit("source replay failed; see retained run.log")
        paths.append(directory / filename)
    merge(paths, args.output_dir / filename, native=args.phase == "native")


if __name__ == "__main__":
    main()
