"""Read synchronized module occurrences for declared-structure attribution.

[Role] Join existing leaf-module traces to the exact captured DB and window.
[Invariants] Only raw records count as evidence, never an older mapping summary.
  A source content hash, NPU synchronization and unique full containment are
  required. Module IDs name actual caller modules, not inferred model layers.
[Timeouts & Locks] Streaming JSON with a 30s scan budget; retained records are
  capped by the structural mapping budget. No database locks or subprocesses.
[Side-Effect Policy] Reads selected traces and hashes selected DBs; no writes.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from itertools import accumulate
from pathlib import Path
import time

from .events import ProfilerUsageError, Window
from .sources_db import sha256_file
from .sources_trace import _JsonStream


def _skip_value(stream, check_budget):
    """Discard enriched summaries without materializing their nested arrays."""
    check_budget()
    char = stream.peek()
    if char == "[":
        stream.expect("[")
        while stream.peek() != "]":
            _skip_value(stream, check_budget)
            if stream.peek() != ",":
                break
            stream.expect(",")
        stream.expect("]")
    elif char == "{":
        stream.expect("{")
        while stream.peek() != "}":
            stream.value()
            stream.expect(":")
            _skip_value(stream, check_budget)
            if stream.peek() != ",":
                break
            stream.expect(",")
        stream.expect("}")
    else:
        stream.value()


def _read_trace(path, windows, max_records, timeout_s):
    started = time.monotonic()
    metadata, records = {}, []
    scanned = 0

    def check_budget():
        if time.monotonic() - started > timeout_s:
            raise ProfilerUsageError(f"{path}: module trace scan exceeded {timeout_s}s")

    with _JsonStream(path) as stream:
        stream.expect("{")
        seen = set()
        while stream.peek() != "}":
            key = stream.value()
            if key in seen:
                raise ProfilerUsageError(f"{path}: duplicated module trace field {key}")
            seen.add(key)
            stream.expect(":")
            if key == "records":
                for record in stream.iter_array():
                    check_budget()
                    scanned += 1
                    start, end = record["wall_start_ns"], record["wall_end_ns"]
                    if not isinstance(start, int) or not isinstance(end, int) or end <= start:
                        raise ProfilerUsageError(f"{path}: invalid module wall-clock interval")
                    if any(start < window.end_ns and end > window.start_ns for window in windows):
                        records.append(record)
                        if len(records) > max_records:
                            raise ProfilerUsageError(
                                f"{path}: module records exceed {max_records}; select a smaller window")
            elif key in {"schema_version", "instrumentation", "source_identity"}:
                metadata[key] = stream.value()
            else:
                _skip_value(stream, check_budget)
            if stream.peek() != ",":
                break
            stream.expect(",")
        stream.expect("}")
        if stream.peek():
            raise ProfilerUsageError(f"{path}: extra data after module trace")
    if metadata.get("schema_version") != "mindie-module-trace/1":
        raise ProfilerUsageError(f"{path}: expected mindie-module-trace/1")
    if metadata.get("instrumentation", {}).get("npu_synchronize") is not True:
        raise ProfilerUsageError(f"{path}: module containment requires synchronized NPU boundaries")
    if not metadata.get("source_identity", {}).get("db_sha256"):
        raise ProfilerUsageError(f"{path}: module evidence requires source_identity.db_sha256")
    return metadata, records, scanned


class ModuleEvidence:
    """Window-bounded interval indexes over independently recorded modules."""

    def __init__(self, paths, observations, *, max_records, timeout_s=30.0):
        self.indices = {}
        self.summaries = []
        sources = {str(Path(obs.source.path).resolve()): obs.source for obs in observations}
        hashes = {}
        retained = 0
        # Attribution tests full event intervals, including portions clipped out
        # of the selected window. Keep any conflicting invocation in that span.
        evidence_windows = [
            Window(min([obs.window.start_ns, *(event.start_ns for event in obs.events)]),
                   max([obs.window.end_ns, *(event.end_ns for event in obs.events)]))
            for obs in observations
        ]
        for value in paths:
            path = Path(value).resolve()
            metadata, records, scanned = _read_trace(
                path, evidence_windows, max_records - retained, timeout_s)
            retained += len(records)
            identity = metadata["source_identity"]
            matching = []
            for source_path, source in sources.items():
                if source.kind != "db":
                    continue
                if source_path not in hashes:
                    before = Path(source_path).stat()
                    if (before.st_size != source.size_bytes
                            or before.st_mtime_ns != source.mtime_ns):
                        raise ProfilerUsageError("module evidence DB changed after event parsing")
                    hashes[source_path] = source.sha256 or sha256_file(Path(source_path))
                    after = Path(source_path).stat()
                    if (after.st_size, after.st_mtime_ns) != (before.st_size, before.st_mtime_ns):
                        raise ProfilerUsageError("module evidence DB changed while hashing")
                if hashes[source_path] == identity["db_sha256"]:
                    matching.append(source_path)
            if not matching:
                raise ProfilerUsageError(f"{path}: module evidence DB hash matches no selected source")
            records.sort(key=lambda row: row["wall_start_ns"])
            for source_path in matching:
                if source_path in self.indices:
                    raise ProfilerUsageError("supply only one module trace for each captured DB")
                self.indices[source_path] = (
                    records, [row["wall_start_ns"] for row in records],
                    list(accumulate((row["wall_end_ns"] for row in records), max)),
                    str(path),
                )
            self.summaries.append({
                "path": str(path), "db_sha256": identity["db_sha256"],
                "matched_sources": matching, "records_scanned": scanned,
                "records_retained": len(records),
                "instrumentation": metadata["instrumentation"],
                "not_application_throughput": True,
            })

    def lookup(self, event, observation):
        indexed = self.indices.get(str(Path(observation.source.path).resolve()))
        overlapping = []
        if indexed is not None:
            rows, starts, prefix_ends, path = indexed
            left = bisect_right(prefix_ends, event.start_ns)
            right = bisect_left(starts, event.end_ns)
            for row in rows[left:right]:
                if row["wall_end_ns"] > event.start_ns:
                    overlapping.append((row, path))
        if not overlapping:
            return None, None
        if len(overlapping) != 1:
            return "overlapping_module_invocations", [
                {"module_id": row["module_id"], "invocation": row.get("invocation"),
                 "path": path} for row, path in overlapping[:16]]
        row, path = overlapping[0]
        evidence = {key: row.get(key) for key in (
            "module_id", "module_type", "invocation", "step_id", "wall_start_ns",
            "wall_end_ns", "input_tensors", "output_tensors",
        )}
        evidence.update(path=path, basis="synchronized_unique_containment")
        if observation.window.step is not None and row.get("step_id") != observation.window.step:
            return "module_step_mismatch", evidence
        if row["wall_start_ns"] <= event.start_ns and event.end_ns <= row["wall_end_ns"]:
            return "contained", evidence
        return "event_crosses_module_boundary", evidence
