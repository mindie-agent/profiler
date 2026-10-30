"""[Role] Reprice every retained V4.1 cohort with the formal composed cases.
[Invariants] Full-family observed populations remain intact; source references
  keep their separate receipts. A successful same-runtime case is not repeated.
[Timeouts & Locks] One worker at a time; outer sum of program budgets +120 s.
[Side-Effect Policy] Read saved metadata, write a new arm; no CSV or NPU work.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys
import time

from reprice_body_operator_families import render_repriced, runtime_identity
from replay_body_operator_families import identity, read, write
from replay_fusion_cohorts import _program_key


def resolved_pin(record):
    """Retained reports use both repository-relative and resolved file paths."""
    return {**record, "path": str(Path(record["path"]).resolve())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-source-commit", required=True)
    parser.add_argument("--compare-timeout", type=float, default=120)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    inputs = read(args.native_report); input_pin = identity(args.native_report)
    before = runtime_identity(); cases, attempts, receipts, durations = [], [], [], []
    script = Path(__file__).with_name("reprice_body_operator_families.py").resolve()
    for source in inputs["cases"]:
        case_id = source["case_id"]
        actual_pin, case_pin = (resolved_pin(source[key]) for key in ("actual_identity", "case_identity"))
        for pin in (actual_pin, case_pin):
            if identity(pin["path"]) != pin:
                raise ValueError("retained_composed_input_changed:" + case_id)
        directory = args.output_dir / case_id
        directory.mkdir(exist_ok=True)
        target = directory / "body-operator-family-scoreboard.json"
        reused = False
        if target.exists():
            previous = read(target)
            row = previous["cases"][0]
            reused = (previous["status"] == "completed" and previous["runtime_source_identity"] == before
                and row["actual_identity"] == actual_pin and row["case_identity"] == case_pin)
            if not reused:
                raise ValueError("existing_case_is_not_a_completed_same_runtime_receipt:" + case_id)
        if not reused:
            old_mapping = Path(actual_pin["path"]).with_name(
                Path(actual_pin["path"]).name.replace(".actual.json", ".mapping.json"))
            mapping = read(old_mapping)
            programs = {_program_key(c) for w in mapping["windows"] for c in w["cohorts"]}
            timeout = len(programs) * args.compare_timeout + 120
            command = [sys.executable, str(script), "--actual", actual_pin["path"],
                "--case", case_pin["path"], "--output-dir", str(directory.resolve()),
                "--variant", "composed-arch35-" + args.runtime_source_commit[:8],
                "--runtime-source-commit", args.runtime_source_commit,
                "--runtime-validation-status", "maintained", "--skip-references",
                "--compare-timeout", str(args.compare_timeout)]
            started = time.perf_counter()
            with (directory / "run.log").open("w") as log:
                child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
            attempts.append({"case_id": case_id, "command": command, "returncode": child.returncode,
                "timeout_seconds": timeout, "elapsed_seconds": time.perf_counter()-started,
                "log_identity": identity(directory / "run.log")})
            write(args.output_dir / "execution.json", {"attempts": attempts,
                "raw_capture_reads": 0, "generator_identity": identity(Path(__file__))})
            if child.returncode:
                raise SystemExit("composed_cohort_failed:see_immediate_failure_in_run_log")
        report = read(target)
        if report["runtime_source_identity"] != before:
            raise ValueError("composed_cohort_runtime_changed")
        cases.extend(report["cases"]); durations.append(report["elapsed_seconds"])
        receipts.append({"identity": identity(target), "same_generation_reused": reused})
        print({"case_id": case_id, "status": report["status"], "same_generation_reused": reused}, flush=True)
    if runtime_identity() != before or identity(args.native_report) != input_pin:
        raise ValueError("composed_campaign_runtime_or_inputs_changed")
    result = {"schema_version": "mindie-body-operator-comparison/1", "status": "completed",
        "cases": cases, "runtime_source_identity": before, "runtime_sources_unchanged": True,
        "runtime_source_commit": args.runtime_source_commit, "runtime_validation_status": "maintained",
        "raw_capture_reads": 0, "old_prediction_reused": False,
        "coverage_status": "partial" if any(f["unscored_event_count"] for c in cases for f in c["families"]) else "complete",
        "elapsed_seconds": sum(durations), "input_native_receipt_identity": input_pin,
        "input_receipts": receipts, "source_reference_policy": "separate_original_runtime_receipts"}
    target = args.output_dir / "body-operator-family-scoreboard.json"
    write(target, result)
    target.with_suffix(".md").write_text(render_repriced(result))


if __name__ == "__main__": main()
