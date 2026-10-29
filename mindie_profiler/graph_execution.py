"""Read explicit device graph execution envelopes from msprof task exports.

[Role] Pair captured MODEL_EXECUTE / MODEL_WAIT_COMPLETE tasks and retain locators.
[Invariants] A graph envelope is not a model-body or layer boundary. Device graph
  IDs seen inside an envelope are temporal observations, not a semantic binding.
  Internal communications and waits remain in the elapsed span; gaps between
  executions are excluded. No sampler, tensor shape or expected-count heuristic.
[Timeouts & Locks] Streaming row/deadline budgets; bounded graph markers; no locks.
[Side-Effect Policy] Read-only local CSV/gzip; no device runtime or remote calls.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import csv
from pathlib import Path
import time

from .accounting import percentile
from .events import ProfilerQueryError, ProfilerSchemaError
from .forward_spans import _statistics
from .sources_csv import _number, _open_csv_text, _us_to_ns, probe_csv


def _identity(path):
    path = Path(path)
    stat = path.stat()
    return {"path": str(path.resolve()), "size_bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns}


def _ns(value, path, line):
    number = _number(value.strip())
    if number is None:
        raise ProfilerSchemaError(f"{path}: invalid time at CSV line {line}")
    return _us_to_ns(number)


def _budget(line, max_rows, deadline):
    if line - 1 > max_rows:
        raise ProfilerQueryError(f"graph execution row budget exceeded: {max_rows}")
    if line % 1024 == 0 and time.monotonic() > deadline:
        raise ProfilerQueryError("graph execution scan timed out")


def _distribution(windows):
    values = [(row["end_ns"] - row["start_ns"]) / 1e6 for row in windows]
    return {"count": len(values), "mean": sum(values) / len(values) if values else None,
            "p50": percentile(values, 0.5), "p90": percentile(values, 0.9)}


def graph_execution_envelopes(task_path, *, operator_path=None, max_rows=5_000_000,
                              max_markers=100_000, timeout_s=60.0):
    """Return measured graph envelopes, explicitly unresolved as model forwards.

    Supported task schema records consecutive execute/wait task IDs on the same
    device and stream. Unmatched/reordered markers stay visible and are never
    bridged across a subsequent execute. Source file rows need not be time sorted.
    """
    deadline = time.monotonic() + timeout_s
    identity = _identity(task_path)
    markers = defaultdict(list)
    marker_count = row_count = 0
    with _open_csv_text(Path(task_path)) as stream:
        reader = csv.DictReader(stream)
        required = {"Device_id", "kernel_type", "stream_id", "task_id",
                    "task_start(us)", "task_stop(us)"}
        if not required.issubset(reader.fieldnames or []):
            raise ProfilerSchemaError(f"{task_path}: unsupported task_time CSV header")
        for line, row in enumerate(reader, 2):
            _budget(line, max_rows, deadline)
            row_count += 1
            if row["kernel_type"] not in {"MODEL_EXECUTE", "MODEL_WAIT_COMPLETE"}:
                continue
            marker_count += 1
            if marker_count > max_markers:
                raise ProfilerQueryError(f"graph marker budget exceeded: {max_markers}")
            start = _ns(row["task_start(us)"], task_path, line)
            end = _ns(row["task_stop(us)"], task_path, line)
            if end < start:
                raise ProfilerSchemaError(f"{task_path}: negative task interval at line {line}")
            markers[(row["Device_id"], row["stream_id"])].append({
                "kind": row["kernel_type"], "task_id": row["task_id"],
                "start_ns": start, "end_ns": end, "csv_line": line,
            })
    windows, unmatched = [], []
    for (device, stream), rows in sorted(markers.items()):
        pending = None
        for row in sorted(rows, key=lambda item: (item["start_ns"], item["csv_line"])):
            if row["kind"] == "MODEL_EXECUTE":
                if pending is not None:
                    unmatched.append({**pending, "reason": "execute_without_completion"})
                pending = row
                continue
            adjacent = (pending is not None and pending["task_id"].isdigit()
                        and row["task_id"].isdigit()
                        and int(row["task_id"]) == int(pending["task_id"]) + 1)
            if not adjacent or row["end_ns"] < pending["end_ns"]:
                unmatched.append({**row, "reason": "completion_without_unique_execute"})
                continue
            windows.append({
                "kind": "graph_execution", "semantic_role": "unresolved",
                "device_id": device, "stream_id": stream,
                "start_ns": pending["start_ns"], "end_ns": row["end_ns"],
                "boundary_basis": "captured_consecutive_execute_completion_tasks",
                "execute": pending, "completion": row,
                "body_forward_span_ms": None, "per_layer_ms": None,
            })
            pending = None
        if pending is not None:
            unmatched.append({**pending, "reason": "execute_without_completion"})
    windows.sort(key=lambda row: (row["start_ns"], row["device_id"], row["stream_id"]))
    for ordinal, window in enumerate(windows):
        window["occurrence_id"] = f"graph-execution:{ordinal}"
    report = {
        "schema_version": "mindie-graph-execution-envelopes/1",
        "status": "completed", "source": identity,
        "row_count": row_count, "marker_count": marker_count,
        "windows": windows, "unmatched_markers": unmatched,
        "graph_execution_span_ms": _distribution(windows),
        "graph_execution_percentile_method": "sorted_values[round(p * (n - 1))]; Python round; no interpolation",
        "body_forward_span_ms": None, "per_layer_ms": None,
        "semantic_status": "graph_to_model_scope_evidence_missing",
        "tail_wait_removed": False,
    }
    if operator_path is not None:
        _observe_graph_ids(report, operator_path, max_rows, deadline)
    if identity != _identity(task_path):
        raise ProfilerQueryError("task source changed during graph scan")
    return report


def _observe_graph_ids(report, operator_path, max_rows, deadline):
    """Project existing CSV timing/header rules without duplicating kernel ABI parsing."""
    identity = _identity(operator_path)
    schema = probe_csv(operator_path)
    if "Model ID" not in schema.header or "device_id" not in schema.columns:
        raise ProfilerSchemaError(f"{operator_path}: Model ID and device columns required")
    model_column = schema.header.index("Model ID")
    indexed = defaultdict(list)
    for window in report["windows"]:
        window["observed_model_ids"] = {}
        window["dynamic_operator_count"] = 0
        indexed[window["device_id"]].append(window)
    indexes = {}
    for device, windows in indexed.items():
        starts = [window["start_ns"] for window in windows]
        prefix_ends, maximum = [], 0
        for window in windows:
            maximum = max(maximum, window["end_ns"])
            prefix_ends.append(maximum)
        indexes[device] = (windows, starts, prefix_ends)
    counts = Counter()
    with _open_csv_text(Path(operator_path)) as stream:
        reader = csv.reader(stream)
        next(reader)
        for line, row in enumerate(reader, 2):
            _budget(line, max_rows, deadline)
            counts["rows"] += 1
            start = _ns(row[schema.columns["start_us"]], operator_path, line)
            if "duration_us" in schema.columns:
                end = start + _ns(row[schema.columns["duration_us"]], operator_path, line)
            else:
                end = _ns(row[schema.columns["end_us"]], operator_path, line)
            if end < start:
                raise ProfilerSchemaError(f"{operator_path}: negative interval at line {line}")
            device = row[schema.columns["device_id"]]
            windows, starts, prefix_ends = indexes.get(device, ([], [], []))
            low, high = bisect_left(prefix_ends, start), bisect_right(starts, end)
            overlapping = [window for window in windows[low:high]
                           if window["start_ns"] < end and window["end_ns"] > start]
            contained = [window for window in overlapping
                         if window["start_ns"] <= start and end <= window["end_ns"]]
            if len(overlapping) != 1 or len(contained) != 1:
                counts["outside_or_crossing_or_overlapping_envelopes"] += 1
                continue
            window = contained[0]
            model = row[model_column]
            if model in {"4294967295", "N/A", "", "-1"}:
                window["dynamic_operator_count"] += 1
            else:
                observed = window["observed_model_ids"]
                observed[model] = observed.get(model, 0) + 1
            counts["uniquely_contained_rows"] += 1
    report["operator_source"] = identity
    report["operator_containment_counts"] = dict(counts)
    report["model_id_association_basis"] = "temporal_containment_only_not_semantic_binding"
    if identity != _identity(operator_path):
        raise ProfilerQueryError("operator source changed during graph scan")


def correlate_forward_envelopes(observed, graph_report):
    """Cross-check inferred complete bodies against independent device markers.

    Graph IDs acquire a conditional body/auxiliary association only after full
    model alignment. The association never feeds back into that alignment.
    """
    source = observed.get("source_identity") or {}
    operator_source = graph_report.get("operator_source") or {}
    if not source.get("sha256") or source["sha256"] != operator_source.get("sha256"):
        raise ProfilerSchemaError("forward and graph operator source hashes differ")
    groups = defaultdict(list)
    for window in graph_report["windows"]:
        groups[window["device_id"]].append(window)
    counts = Counter()
    bodies = defaultdict(list)
    auxiliary = Counter()
    missing = []
    differences = []

    def containing(device, start, end):
        return [window for window in groups.get(device, [])
                if window["start_ns"] <= start and end <= window["end_ns"]]

    for forward in observed.get("forwards", []):
        counts["complete_bodies"] += 1
        candidates = containing(forward["device_id"], forward["start_ns"], forward["end_ns"])
        if len(candidates) != 1:
            counts["body_without_unique_graph"] += 1
            if len(missing) < 16:
                missing.append({"forward_id": forward["forward_id"],
                                "reason": "body_without_unique_graph",
                                "candidate_count": len(candidates)})
            continue
        window = candidates[0]
        ids = tuple(sorted(window.get("observed_model_ids", {})))
        counts["body_unique_graph"] += 1
        difference = ((window["end_ns"] - window["start_ns"])
                      - (forward["end_ns"] - forward["start_ns"])) / 1e6
        differences.append(difference)
        bodies[ids].append(difference)
    for candidate in observed.get("auxiliary_occurrences", []):
        counts["auxiliary_heads"] += 1
        windows = containing(candidate["device_id"], candidate["head_start_ns"],
                             candidate["head_end_ns"])
        if len(windows) != 1:
            counts["auxiliary_head_without_unique_graph"] += 1
            continue
        counts["auxiliary_head_unique_graph"] += 1
        auxiliary[tuple(sorted(windows[0].get("observed_model_ids", {})))] += 1
    return {
        "schema_version": "mindie-forward-graph-crosscheck/1", "status": "completed",
        "operator_source_sha256": source["sha256"], "counts": dict(counts),
        "body_graph_groups": [{"observed_model_ids": list(ids), "body_count": len(values),
                               "graph_minus_body_span_ms": _statistics(values)}
                              for ids, values in sorted(bodies.items())],
        "auxiliary_head_graph_groups": [
            {"observed_model_ids": list(ids), "auxiliary_head_count": count}
            for ids, count in sorted(auxiliary.items())],
        "graph_minus_body_span_ms": _statistics(differences), "anomaly_examples": missing,
        "basis": "complete_structure_alignment_crosschecked_against_device_graph_markers",
        "semantic_graph_binding": "conditional_on_complete_structure_alignment",
        "graph_ids_did_not_select_model_layers": True,
    }
