"""Pre-indexed host/CANN/device correlation over explicit connection IDs.

[Role]
  Replace per-task linear rescans of ``CANN_API`` and ``PYTORCH_API`` with one
  connection-ID map, one bounded interval-containment index per thread, and one
  Fenwick-tree ancestry-uniqueness pass over the original host intervals.
[Invariants]
  * Candidate order is the original SQL ordinal (``startNs, rowid``); equal-start
    candidates are never reordered and no ``id`` tie-breaker is introduced.
  * ``_find_pytorch`` keeps its stable ``max(start_ns, -end_ns)`` selection rule.
  * ``unique_ancestry`` is computed over every original interval on the thread,
    not from the attached parent chain, so crossing outer intervals stay
    non-unique exactly as before.
  * A connection hit is tried before interval containment; multiple candidates
    remain explicitly non-unique.
[Timeouts & Locks]
  Pure in-memory index construction over already-read events; no SQL, locks or
  background threads.
[Side-Effect Policy]
  No I/O; candidate events are returned by reference and never mutated.
"""
from __future__ import annotations

from bisect import bisect_right
from itertools import groupby
from typing import Any, Iterable, Mapping, Sequence

DEFAULT_MAX_STACK_DEPTH = 64


def _connections_for(event: Mapping[str, Any], links: Mapping[int, set[int]]) -> set[int]:
    connection = event.get("connection_id")
    if connection is None:
        return set()
    if event["table"] == "CANN_API":
        return {connection}
    if event["table"] == "PYTORCH_API":
        return links.get(connection, set())
    return set()


def _is_step_marker(event: Mapping[str, Any]) -> bool:
    return str(event.get("name") or "").lower().startswith("profilerstep#")


def strict_stack(events: Sequence[Mapping[str, Any]]) -> bool:
    """Equal or crossing host intervals do not prove a unique ancestry."""
    ordered = sorted(events, key=lambda event: (event["start_ns"], -event["end_ns"]))
    return all(
        outer["start_ns"] <= inner["start_ns"]
        and outer["end_ns"] >= inner["end_ns"]
        and (outer["start_ns"], outer["end_ns"]) != (inner["start_ns"], inner["end_ns"])
        for outer, inner in zip(ordered, ordered[1:])
    )


def unique_ancestry(
    events: Sequence[Mapping[str, Any]], is_step_marker: Any,
) -> dict[int, bool]:
    """Fenwick-tree proof that each interval has a strictly unique ancestry."""
    result = {id(event): True for event in events}
    threads: dict[Any, list[Mapping[str, Any]]] = {}
    for event in events:
        tid = event.get("global_tid")
        if tid is not None and not is_step_marker(event):
            threads.setdefault(tid, []).append(event)
    for rows in threads.values():
        ordered = sorted(rows, key=lambda event: (event["start_ns"], -event["end_ns"]))
        ends = sorted({event["end_ns"] for event in rows})
        tree = [float("-inf")] * (len(ends) + 1)
        bad_threshold = float("-inf")
        for _, group in groupby(ordered, key=lambda event: event["start_ns"]):
            batch = list(group)
            seen_ends: set[int] = set()
            for event in batch:
                end = event["end_ns"]
                position = bisect_right(ends, end) - 1
                index = position
                while index > 0:
                    bad_threshold = max(bad_threshold, tree[index])
                    index -= index & -index
                if end in seen_ends:
                    bad_threshold = max(bad_threshold, end)
                seen_ends.add(end)
                index = position + 1
                while index < len(tree):
                    tree[index] = max(tree[index], end)
                    index += index & -index
            for event in batch:
                result[id(event)] = bad_threshold < event["end_ns"]
    return result


class _IntervalLookup:
    """Sorted-start/prefix-max-end containment lookup preserving input order."""

    def __init__(self, events: Iterable[Mapping[str, Any]]) -> None:
        self._events = list(events)
        self._order = sorted(
            range(len(self._events)),
            key=lambda index: (self._events[index]["start_ns"],
                               -self._events[index]["end_ns"]),
        )
        self._starts = [self._events[index]["start_ns"] for index in self._order]
        self._prefix_max_end: list[int] = []
        running = float("-inf")
        for index in self._order:
            running = max(running, self._events[index]["end_ns"])
            self._prefix_max_end.append(running)

    def containing(self, start_ns: int, end_ns: int) -> list[Mapping[str, Any]]:
        stop = bisect_right(self._starts, start_ns)
        found: list[tuple[int, Mapping[str, Any]]] = []
        index = stop - 1
        while index >= 0 and self._prefix_max_end[index] >= end_ns:
            event = self._events[self._order[index]]
            if event["end_ns"] >= end_ns:
                found.append((self._order[index], event))
            index -= 1
        found.sort(key=lambda item: item[0])
        return [event for _, event in found]


class HostCorrelationIndex:
    """One connection/containment/ancestry index reused for every task."""

    def __init__(
        self,
        cann_events: Sequence[Mapping[str, Any]],
        pytorch_events: Sequence[Mapping[str, Any]],
        links: Mapping[int, set[int]],
    ) -> None:
        self.links = dict(links)
        self.cann_events = list(cann_events)
        self.pytorch_events = list(pytorch_events)
        self._ordinal = {
            id(event): index
            for index, event in enumerate((*self.cann_events, *self.pytorch_events))
        }
        self.cann_by_conn: dict[int, list[Mapping[str, Any]]] = {}
        self.pytorch_by_conn: dict[int, list[Mapping[str, Any]]] = {}
        for event in self.cann_events:
            for connection in _connections_for(event, self.links):
                self.cann_by_conn.setdefault(connection, []).append(event)
        for event in self.pytorch_events:
            if _is_step_marker(event):
                continue
            for connection in _connections_for(event, self.links):
                self.pytorch_by_conn.setdefault(connection, []).append(event)
        self.cann_lookup = _IntervalLookup(self.cann_events)
        by_tid: dict[Any, list[Mapping[str, Any]]] = {}
        for event in self.pytorch_events:
            if event.get("global_tid") is not None and not _is_step_marker(event):
                by_tid.setdefault(str(event["global_tid"]), []).append(event)
        self.pytorch_tid_lookup = {
            tid: _IntervalLookup(rows) for tid, rows in by_tid.items()
        }
        self._unique = unique_ancestry(self.pytorch_events, _is_step_marker)

    def host_stack_unique(self, event: Mapping[str, Any]) -> bool:
        return self._unique.get(id(event), True)

    def _ordered(self, events: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        unique: dict[int, Mapping[str, Any]] = {id(event): event for event in events}
        return sorted(unique.values(), key=lambda event: self._ordinal.get(id(event), 0))

    def find_cann(self, task: Mapping[str, Any]) -> tuple[Any, str | None, bool, int]:
        connection = task.get("connection_id")
        if connection is not None:
            candidates = self.cann_by_conn.get(int(connection), ())
            if candidates:
                return candidates[0], "connection_ids", len(candidates) == 1, len(candidates)
        candidates = self.cann_lookup.containing(task["start_ns"], task["end_ns"])
        if candidates:
            return candidates[0], "cann_interval_contains_task", len(candidates) == 1, len(candidates)
        return None, None, False, 0

    def find_pytorch(
        self, cann: Mapping[str, Any] | None, task: Mapping[str, Any],
    ) -> tuple[Any, str | None, bool, int]:
        if cann is not None:
            connections = _connections_for(cann, self.links)
            if task.get("connection_id") in connections:
                connections = {task["connection_id"]}
            candidates = self._ordered(
                event for connection in connections
                for event in self.pytorch_by_conn.get(int(connection), ()))
            if candidates:
                unique = len(candidates) == 1 and self.host_stack_unique(candidates[0])
                return candidates[0], "connection_ids", unique, len(candidates)
            tid = cann.get("global_tid")
            if tid is not None:
                lookup = self.pytorch_tid_lookup.get(str(tid))
                if lookup is not None:
                    contained = lookup.containing(cann["start_ns"], cann["end_ns"])
                    if contained:
                        selected = max(
                            contained,
                            key=lambda event: (event["start_ns"], -event["end_ns"]))
                        return (selected, "same_global_tid_containment",
                                strict_stack(contained), len(contained))
        connection = task.get("connection_id")
        if connection is not None:
            candidates = self.pytorch_by_conn.get(int(connection), ())
            if candidates:
                unique = len(candidates) == 1 and self.host_stack_unique(candidates[0])
                return candidates[0], "connection_ids", unique, len(candidates)
        return None, None, False, 0


__all__ = ["HostCorrelationIndex", "strict_stack", "unique_ancestry"]
