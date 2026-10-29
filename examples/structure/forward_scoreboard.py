"""Render independently evidenced body forwards beside operator accuracy.

[Role] Link the Decode body replay into the unified cohort reports.
[Invariants] Kernel activity sums and graph envelopes never fill body timing.
  Missing evidence stays unscored. The two scoreboards keep separate denominators.
[Timeouts & Locks] Bounded report metadata; no prediction, subprocesses or locks.
[Side-Effect Policy] Reads an existing report and returns Markdown plus identity.
"""
from fusion_replay_cases import _hash, _read


def _number(value):
    return "—" if value is None else f"{value:.4f}"


def body_scoreboard(directory):
    path = directory / "decode-forward-replay.json"
    lines = ["", "## Decode Body Forward", "",
             "Body timing is the per-invocation device wall-clock span, including body "
             "communication and internal dependencies. Between-step gaps are excluded. "
             "Embedding, final norm/LM head and MTP remain separate boundaries. "
             "Kernel activity sums and unidentified graph envelopes are not body latency.", ""]
    if not path.exists():
        lines.append("Unresolved: no completed body-forward evidence report is available. "
                     "No Sim-vs-Real body accuracy is claimed.")
        return lines, {"status": "unresolved", "reason": "body_forward_report_missing"}
    report = _read(path)
    if report.get("schema_version") != "mindie-decode-forward-replay-report/1":
        raise ValueError("body_forward_report_schema_mismatch")
    identity = {"file": path.name, "sha256": _hash(path), "size_bytes": path.stat().st_size}
    lines.extend([
        f"Independent evidence: [Decode multi-case replay](decode-forward-replay.md), "
        f"JSON SHA256 `{identity['sha256']}`. Scenarios and unresolved reasons are retained there.", "",
        "| Case | Body forwards | Real mean ms | Real P50 ms | Real P90 ms | Sim ms | "
        "Relative error | Status |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    counts = {"compared": 0, "passed": 0, "unresolved": 0, "failed": 0}
    for case in report["cases"]:
        result = case["comparison"]
        status = result["status"]
        actual = result.get("observed_ms") or {}
        if status == "compared":
            if any(actual.get(key) is None for key in ("mean", "p50", "p90")):
                raise ValueError("compared_body_forward_missing_measured_distribution")
            counts["compared"] += 1
            counts["passed"] += result["passed"] is True
        else:
            counts["failed" if status == "failed" else "unresolved"] += 1
        error = result.get("relative_error")
        lines.append(
            f"| {case['case_id']} | {result.get('observed_forward_count') or '—'} | "
            f"{_number(actual.get('mean'))} | {_number(actual.get('p50'))} | "
            f"{_number(actual.get('p90'))} | {_number(result.get('predicted_ms'))} | "
            f"{'—' if error is None else f'{error:+.1%}'} | {status} |")
    lines.extend(["", f"Body accuracy: **{counts['passed']} / {counts['compared']}** "
                  f"comparable cases; {counts['unresolved']} unresolved, {counts['failed']} failed. "
                  "Unresolved cases do not count as passes or zero-duration forwards."])
    return lines, {"report_identity": identity, "counts": counts,
                   "separate_from_operator_cohort_denominator": True}
