"""[Role] Run reviewed V4.1 composed cases against the seven retained populations.
[Invariants] Input identities, all forty layers and DP peer work stay explicit;
  a successful same-generation source is reused only with identical tool/input pins.
[Timeouts & Locks] One reference worker at a time; 190 s outer / 180 s child.
[Side-Effect Policy] Local saved metadata and new reports; no raw capture reads.
"""
import argparse
from pathlib import Path
import subprocess
import sys
import time

from compare_glm_native_partitions import render
from compare_v41_composed_sources import runtime_identity
from replay_body_operator_families import identity, read, write


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--case-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runtime-source-commit", required=True)
    args = parser.parse_args()
    started = time.perf_counter(); before = runtime_identity()
    inputs_pin = identity(args.inputs); inputs = read(args.inputs)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases, attempts, declarations = [], [], []
    script = Path(__file__).with_name("compare_v41_composed_sources.py").resolve()
    for row in inputs["cases"]:
        case_id = row["case_id"]
        partition_pin = row["partition_identity"]
        if identity(partition_pin["path"]) != partition_pin:
            raise ValueError("retained_partition_changed:" + case_id)
        case_path = args.case_dir / (case_id + "-composed-arch35-source.json")
        case_pin = identity(case_path)
        declarations.append({"case_id": case_id, "case_identity": case_pin,
                             "partition_identity": partition_pin})
        directory = args.output_dir / case_id
        directory.mkdir(parents=True, exist_ok=True)
        report_path = directory / "v41-composed-native-reference-scoreboard.json"
        reused = False
        if report_path.exists():
            saved = read(report_path)
            candidate = saved["cases"][0]
            reused = (saved["status"] == "completed" and saved["runtime_source_identity"] == before
                and candidate["case_identity"] == case_pin and candidate["partition_identity"] == partition_pin)
        if not reused:
            command = [sys.executable, str(script), "--partition", partition_pin["path"],
                "--case", str(case_path.resolve()), "--output-dir", str(directory.resolve()),
                "--runtime-source-commit", args.runtime_source_commit]
            tick = time.perf_counter()
            with (directory / "run.log").open("w") as log:
                child = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=190)
            attempts.append({"case_id": case_id, "command": command, "returncode": child.returncode,
                "elapsed_seconds": time.perf_counter() - tick, "log_identity": identity(directory / "run.log")})
            write(args.output_dir / "execution.json", {"attempts": attempts, "raw_capture_reads": 0,
                "generator_identity": identity(Path(__file__))})
            if child.returncode:
                raise SystemExit("composed source reference failed; retained run.log has the error")
        report = read(report_path)
        if report["runtime_source_identity"] != before:
            raise ValueError("composed_reference_runtime_differs")
        cases.extend(report["cases"])
        print({"case_id": case_id, "status": report["status"], "same_generation_reused": reused}, flush=True)
    if runtime_identity() != before or identity(args.inputs) != inputs_pin:
        raise ValueError("composed_batch_runtime_or_input_changed")
    write(args.output_dir / "input-manifest.json", {"schema_version": "mindie-composed-native-inputs/1",
        "runtime_source_commit": args.runtime_source_commit, "retained_inputs_identity": inputs_pin,
        "cases": declarations})
    result = {"schema_version": "mindie-native-body-reference-batch/1",
        "status": "completed" if all(c["status"] == "completed" for c in cases) else "partial",
        "runtime_source_commit": args.runtime_source_commit, "runtime_source_identity": before,
        "cases": cases, "raw_capture_reads": 0, "strict_compared": 0,
        "elapsed_seconds": sum(c["execution"]["elapsed_seconds"] for c in cases),
        "batch_elapsed_seconds": time.perf_counter() - started,
        "input_receipts": [identity(args.output_dir / c["case_id"] / "v41-composed-native-reference-scoreboard.json") for c in cases],
        "generator_identity": identity(Path(__file__))}
    target = args.output_dir / "v41-composed-native-reference-scoreboard.json"
    write(target, result)
    target.with_suffix(".md").write_text(render(result))


if __name__ == "__main__":
    main()
