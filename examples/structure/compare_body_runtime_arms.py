"""Compare runtime arms over identical measured Decode populations.

[Role] Show numerical gains and regressions when the declared program changes.
[Invariants] Match source, execution geometry and extraction bytes; never select
  the arm with the smaller error. Failed predecessors remain failed attempts.
[Timeouts & Locks] Bounded local JSON reads, no prediction workers or locks.
[Side-Effect Policy] Read existing receipts; write requested JSON and Markdown.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError(f"receipt exceeds 50 MiB: {path}")
    data = path.read_bytes()
    return json.loads(data), {"path": str(path.resolve()), "sha256": hashlib.sha256(data).hexdigest()}


def population(row):
    geometry = row["geometry"]
    return (row["source_identity"]["sha256"], *(geometry[key] for key in
            ("phase", "tokens_per_sequence", "sequences_per_replica", "context_tokens")))


def compare(before_paths, after_paths):
    previous, inputs, rows = {}, [], []
    for path in before_paths:
        report, identity = read(path)
        inputs.append({"arm": "before", **identity})
        for row in report["cases"]:
            previous[population(row)] = (row, identity)
    for path in after_paths:
        report, identity = read(path)
        inputs.append({"arm": "after", **identity})
        for row in report["cases"]:
            if row["comparison"]["status"] != "compared":
                continue
            prior, prior_identity = previous[population(row)]
            before, after = prior["comparison"], row["comparison"]
            if prior["extraction_identity"]["sha256"] != row["extraction_identity"]["sha256"]:
                raise ValueError(f"extraction changed: {row['case_id']}")
            if before["observed_ms"] != after["observed_ms"]:
                raise ValueError(f"observed population changed: {row['case_id']}")
            rows.append({"case_id": row["case_id"], "source_identity": row["source_identity"],
                         "geometry": row["geometry"], "extraction_identity": row["extraction_identity"],
                         "before_receipt": prior_identity, "after_receipt": identity,
                         "before_runtime": prior.get("runtime_identity"),
                         "after_runtime": row.get("runtime_identity"),
                         "observed_ms": after["observed_ms"], "before": before, "after": after,
                         "prediction_delta_ms": (after["predicted_ms"] - before["predicted_ms"]
                                                 if before["predicted_ms"] is not None else None)})
    return {"schema_version": "mindie-body-runtime-arm-comparison/1", "inputs": inputs,
            "raw_capture_reads": 0, "prediction_executions": 0, "cases": rows,
            "summary": {"compared_after": len(rows),
                        "passed_before": sum(row["before"]["passed"] is True for row in rows),
                        "passed_after": sum(row["after"]["passed"] is True for row in rows),
                        "failed_before": sum(row["before"]["status"] == "failed" for row in rows),
                        "lost_pass": [row["case_id"] for row in rows if row["before"]["passed"] is True
                                      and row["after"]["passed"] is False],
                        "gained_pass": [row["case_id"] for row in rows if row["before"]["passed"] is False
                                        and row["after"]["passed"] is True]},
            "limitations": ["A runtime arm may include multiple changes; the delta is not a single-commit causal attribution.",
                            "Body wall time is distinct from accumulated operator activity or isolated service time."]}


def render(report):
    lines = ["# Decode Body runtime comparison", "", "Identical retained source populations; no raw capture reads or new prediction in this join.", "",
             "| Case | Real mean ms | Before ms | After ms | Delta ms | Before error | After error |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    def number(value, scale=1, suffix=""):
        return "unavailable" if value is None else f"{value * scale:.4f}{suffix}"
    for row in report["cases"]:
        before, after = row["before"], row["after"]
        lines.append(f"| {row['case_id']} | {number(row['observed_ms']['mean'])} | "
                     f"{number(before['predicted_ms'])} | {number(after['predicted_ms'])} | "
                     f"{number(row['prediction_delta_ms'])} | {number(before['relative_error'], 100, '%')} | "
                     f"{number(after['relative_error'], 100, '%')} |")
    lines += ["", *report["limitations"], ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, action="append", required=True)
    parser.add_argument("--after", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.before, args.after)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(render(report))
    print(json.dumps(report["summary"]))


if __name__ == "__main__":
    main()
