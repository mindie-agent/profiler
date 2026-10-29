"""Audit an explicitly located AttnRes population without assigning source flags.

[Role] Recount retained CSV events in a caller-supplied window or row selection.
[Invariants] Expected counts never select events. Backing tensor extents and
  durations never establish active views, flags, layers or source occurrences.
[Timeouts & Locks] One deadline covers streaming hashing and a bounded CSV scan;
  at most max_descriptors aggregates and one example per descriptor are retained.
[Side-Effect Policy] Reads one capture; writes only the requested JSON report.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import time

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_diagnostic


def _hash(path, deadline):
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            if time.monotonic() >= deadline:
                raise TimeoutError("AttnRes source hashing exceeded the scope deadline")
            digest.update(chunk)
    return digest.hexdigest()


def _descriptor(row):
    return {
        "native_operator_type": row.kind,
        "input_shapes": row.input_shapes,
        "input_dtypes": row.input_dtypes,
        "input_formats": row.input_formats,
        "output_shapes": row.output_shapes,
        "output_dtypes": row.output_dtypes,
        "output_formats": row.output_formats,
    }


def review_scope(capture, *, source_sha256, start_ns=None, end_ns=None,
                 csv_lines=(), complete_capture=False, device_id=None,
                 stream_id=None, expected_events=None, max_rows=1_000_000,
                 max_descriptors=128, timeout_s=30):
    """Count positive events intersecting an explicit scope; retain clipped counts."""
    started = time.monotonic()
    deadline = started + timeout_s
    capture = Path(capture).resolve()
    csv_lines = frozenset(int(line) for line in csv_lines)
    window_supplied = start_ns is not None or end_ns is not None
    if sum((bool(csv_lines), window_supplied, complete_capture)) != 1:
        raise ValueError("select exactly one explicit window, CSV row set, or complete capture")
    if window_supplied and (start_ns is None or end_ns is None or end_ns <= start_ns):
        raise ValueError("the explicit window requires start_ns < end_ns")
    before = capture.stat()
    actual_hash = _hash(capture, deadline)
    if actual_hash != source_sha256:
        raise ValueError(f"capture SHA256 mismatch: expected {source_sha256}, found {actual_hash}")

    descriptors = {}
    positive_rows_visited = 0
    selected_count = complete_count = clipped_count = activity_ns = complete_activity_ns = 0
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("AttnRes source hashing exhausted the scope deadline")
    for row in kernel_rows(capture, max_rows=max_rows, timeout_s=remaining):
        positive_rows_visited += 1
        if row.kind != "AttnResFwd":
            continue
        if device_id is not None and row.event.device_id != str(device_id):
            continue
        if stream_id is not None and row.stream != str(stream_id):
            continue
        if csv_lines and row.line not in csv_lines:
            continue
        overlap_start, overlap_end = row.start_ns, row.end_ns
        if window_supplied:
            overlap_start = max(overlap_start, start_ns)
            overlap_end = min(overlap_end, end_ns)
            if overlap_end <= overlap_start:
                continue
        complete = (overlap_start, overlap_end) == (row.start_ns, row.end_ns)
        intersection_ns = overlap_end - overlap_start
        descriptor = _descriptor(row)
        key = sha256(json.dumps(descriptor, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if key not in descriptors:
            if len(descriptors) >= max_descriptors:
                raise ValueError("AttnRes descriptor budget exceeded; no partial report emitted")
            descriptors[key] = {
                "descriptor_sha256": key,
                "recorded_descriptor": descriptor,
                "event_count": 0, "complete_event_count": 0, "clipped_event_count": 0,
                "activity_sum_ns": 0, "complete_activity_sum_ns": 0,
                "observed_contract": observed_contract(row),
                "contract_diagnostic": observed_contract_diagnostic(row),
                "representative_event": row.identity,
            }
        item = descriptors[key]
        item["event_count"] += 1
        item["complete_event_count"] += int(complete)
        item["clipped_event_count"] += int(not complete)
        item["activity_sum_ns"] += intersection_ns
        item["complete_activity_sum_ns"] += row.duration_ns if complete else 0
        selected_count += 1
        complete_count += int(complete)
        clipped_count += int(not complete)
        activity_ns += intersection_ns
        complete_activity_ns += row.duration_ns if complete else 0

    after = capture.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("capture changed during the scope review")
    count_verified = None if expected_events is None else selected_count == expected_events
    return {
        "schema_version": "mindie-attnres-scope-review/1",
        "status": "count_mismatch" if count_verified is False else "completed",
        "source": {"path": str(capture), "sha256": actual_hash, "size_bytes": after.st_size},
        "scope": {
            "basis": "explicit_window" if window_supplied else (
                "explicit_csv_lines" if csv_lines else "explicit_complete_capture"),
            "window_ns": [start_ns, end_ns] if window_supplied else None,
            "csv_lines": sorted(csv_lines), "device_id": device_id, "stream_id": stream_id,
            "phase": None, "step": None, "layer": None,
            "event_count_basis": "positive_duration_AttnResFwd_events_intersecting_scope",
        },
        "expected_events": expected_events,
        "expected_count_verified": count_verified,
        "observed": {
            "event_count": selected_count, "complete_event_count": complete_count,
            "clipped_event_count": clipped_count, "activity_sum_ns": activity_ns,
            "complete_activity_sum_ns": complete_activity_ns,
            "complete_mean_us": complete_activity_ns / complete_count / 1000 if complete_count else None,
        },
        "descriptors": list(descriptors.values()),
        "comparison": {
            "status": "reference_only", "scored_event_count": 0, "bound_event_count": 0,
            "prediction_runs": 0, "accuracy_pass": None,
            "reason": "source_flags_and_active_views_not_observed",
            "count_agreement_implies_source_occurrence": False,
        },
        "execution": {
            "positive_rows_visited": positive_rows_visited, "max_rows": max_rows,
            "max_descriptors": max_descriptors, "timeout_s": timeout_s,
            "elapsed_seconds": time.monotonic() - started,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--start-ns", type=int)
    parser.add_argument("--end-ns", type=int)
    parser.add_argument("--csv-line", type=int, action="append", default=[])
    parser.add_argument("--complete-capture", action="store_true")
    parser.add_argument("--device-id")
    parser.add_argument("--stream-id")
    parser.add_argument("--expected-events", type=int)
    parser.add_argument("--max-rows", type=int, default=1_000_000)
    parser.add_argument("--max-descriptors", type=int, default=128)
    parser.add_argument("--timeout-s", type=float, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = review_scope(
        args.capture, source_sha256=args.source_sha256,
        start_ns=args.start_ns, end_ns=args.end_ns, csv_lines=args.csv_line,
        complete_capture=args.complete_capture, device_id=args.device_id,
        stream_id=args.stream_id, expected_events=args.expected_events,
        max_rows=args.max_rows, max_descriptors=args.max_descriptors, timeout_s=args.timeout_s)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 1 if report["status"] == "count_mismatch" else 0


if __name__ == "__main__":
    raise SystemExit(main())
