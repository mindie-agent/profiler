"""Measure device spans inside independently evidenced model boundaries.

[Role] Aggregate single target-body forwards and separately evidenced stages.
[Invariants] A profiler step is not a forward. Host callbacks need synchronized
  boundaries or exact correlated event occurrences. Names, tensor shapes and
  event periodicity never establish a layer. Body spans retain internal gaps
  and communication; embedding, final norm, LM/MTP heads have separate scopes.
  Only an explicitly evidenced trailing wait may shorten an event interval.
[Timeouts & Locks] One bounded event scan with interval indexes; no I/O or locks.
[Side-Effect Policy] Pure analysis; never initializes devices or modifies inputs.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import defaultdict
from itertools import accumulate
from math import ceil
from statistics import mean, median

from .classify import classify_event
from .events import ProfilerUsageError, SourceRef

BOUNDARY_SCHEMA = "mindie-forward-boundaries/1"
REPORT_SCHEMA = "mindie-forward-spans/1"
_KINDS = {"target_body", "embedding", "final_norm", "lm_head", "mtp",
          "dense_layer", "moe_layer", "module"}


def _statistics(values):
    ordered = sorted(values)
    return {"count": len(ordered), "mean": mean(ordered) if ordered else None,
            "p50": median(ordered) if ordered else None,
            "p90": ordered[ceil(len(ordered) * .9) - 1] if ordered else None,
            "min": ordered[0] if ordered else None,
            "max": ordered[-1] if ordered else None}


def _integer(value, label):
    if not isinstance(value, int) or isinstance(value, bool):
        raise ProfilerUsageError(f"{label} must be integer nanoseconds")
    return value


class _Scope:
    def __init__(self, row, forward, rank_id):
        self.row, self.forward = row, forward
        self.kind = row["kind"]
        if self.kind not in _KINDS:
            raise ProfilerUsageError(f"unknown forward scope kind {self.kind!r}")
        self.rank_id = row.get("rank_id", rank_id)
        self.device_id = str(row["device_id"]) if row.get("device_id") is not None else None
        self.start = _integer(row["start_ns"], "scope.start_ns")
        self.end = _integer(row["end_ns"], "scope.end_ns")
        if self.end <= self.start:
            raise ProfilerUsageError("forward scope end must follow start")
        self.reasons = set()
        evidence = row.get("evidence", {})
        basis = evidence.get("basis")
        self.ids = set(row.get("event_ids", ()))
        self.membership = basis == "correlated_host"
        if not evidence.get("reference"):
            self.reasons.add("boundary_evidence_missing")
        if basis not in {"device_range", "synchronized_module", "correlated_host"}:
            self.reasons.add("device_boundary_unproven")
        if basis == "synchronized_module" and evidence.get("npu_synchronize") is not True:
            self.reasons.add("unsynchronized_host_boundary")
        if self.membership and not self.ids:
            self.reasons.add("correlated_event_occurrences_missing")
        if row.get("complete") is not True:
            self.reasons.add("scope_completeness_unproven")
        if self.kind in {"dense_layer", "moe_layer"} and row.get("layer_id") is None:
            self.reasons.add("layer_identity_missing")
        self.tails = {item["event_id"]: item for item in row.get("tail_waits", ())}
        self.seen, self.tail_seen = set(), set()
        self.devices = set()
        self.first = self.last = self.raw_last = self.non_tail_last = None
        self.count = self.comm_count = self.aicpu_count = self.removed_ns = 0
        self.tail_starts = []

    def add(self, event):
        if event.event_id in self.seen:
            self.reasons.add("duplicate_event_occurrence")
            return
        self.seen.add(event.event_id)
        self.devices.add(str(event.device_id))
        start, end = event.start_ns, event.end_ns
        aicpu = any("aicpu" in value.lower().replace("_", "").replace(" ", "")
                    for value in (event.core, event.task_type))
        classification = classify_event(name=event.name, op_type=event.op_type,
                                        task_type=event.task_type, core=event.core,
                                        table=event.table)
        self.raw_last = max(self.raw_last or end, end)
        tail = self.tails.get(event.event_id)
        if tail is not None:
            self.tail_seen.add(event.event_id)
            evidence = tail.get("evidence", {})
            wait_start = _integer(tail["wait_start_ns"], "tail.wait_start_ns")
            # This is an occurrence assertion, never an allreduce-name filter.
            if (evidence.get("basis") != "trailing_wait" or not evidence.get("reference")
                    or not aicpu or not start <= wait_start <= end):
                self.reasons.add("tail_wait_evidence_invalid")
            else:
                self.removed_ns += end - wait_start
                end = wait_start
                self.tail_starts.append(wait_start)
        else:
            self.non_tail_last = max(self.non_tail_last or end, end)
        if not self.membership and not (self.start <= start and end <= self.end):
            self.reasons.add("event_crosses_scope_boundary")
        self.count += 1
        self.comm_count += int(classification.is_comm)
        self.aicpu_count += int(aicpu)
        if end > start:
            self.first = min(self.first if self.first is not None else start, start)
            self.last = max(self.last if self.last is not None else end, end)

    def finish(self):
        if len(self.devices) > 1:
            self.reasons.add("multiple_devices_require_explicit_scopes")
        if self.membership and self.ids != self.seen:
            self.reasons.add("correlated_event_occurrences_absent")
        if set(self.tails) != self.tail_seen:
            self.reasons.add("tail_wait_occurrence_absent")
        if self.non_tail_last is not None and any(
                start < self.non_tail_last for start in self.tail_starts):
            self.reasons.add("wait_is_not_a_tail_of_body_activity")
        if self.first is None:
            self.reasons.add("no_device_activity")
        measured = not self.reasons
        return {
            "scope_id": self.row["scope_id"], "kind": self.kind,
            "layer_id": self.row.get("layer_id"), "rank_id": self.rank_id,
            "device_id": self.device_id or (next(iter(self.devices)) if len(self.devices) == 1 else None),
            "observed_device_ids": sorted(self.devices),
            "replica": self.row.get("replica"), "stage": self.row.get("stage"),
            "status": "measured" if measured else "unresolved",
            "reasons": sorted(self.reasons),
            "start_ns": self.first if measured else None,
            "end_ns": self.last if measured else None,
            "span_ms": (self.last - self.first) / 1e6 if measured else None,
            "span_start_basis": "first_retained_device_event_start",
            "span_end_basis": "last_retained_device_event_end",
            "event_count": self.count, "communication_event_count": self.comm_count,
            "aicpu_event_count": self.aicpu_count,
            "excluded_tail_wait_activity_ms": self.removed_ns / 1e6,
            "boundary": {"start_ns": self.start, "end_ns": self.end},
            "evidence": self.row.get("evidence"),
        }


def measure_forward_spans(events, boundaries, *, source: SourceRef,
                          clock_domain="unix_wall_ns", max_events=5_000_000,
                          max_scopes=100_000, max_scope_events=500_000):
    """Consume existing normalized Events once and report evidenced spans.

    ``boundaries`` is ``mindie-forward-boundaries/1`` with a source SHA256,
    clock_domain, phase, optional geometry/comparison_scope, and ``forwards``.
    Each forward contains named ``scopes`` with kind, integer start/end_ns,
    complete, and evidence {basis, reference}. ``synchronized_module`` also
    requires npu_synchronize; ``correlated_host`` requires exact event_ids.
    A target_body scope must independently delimit only the target transformer
    body. Passing a whole step as target_body is not a supported inference.
    Per-scope tail_waits identify exact AICPU event_id + wait_start_ns and a
    trailing_wait evidence reference; unrelated AICPU intervals remain intact.
    """
    if boundaries.get("schema_version") != BOUNDARY_SCHEMA:
        raise ProfilerUsageError(f"expected {BOUNDARY_SCHEMA}")
    if not source.sha256 or boundaries.get("source_identity", {}).get("sha256") != source.sha256:
        raise ProfilerUsageError("forward evidence source SHA256 does not match event source")
    if boundaries.get("clock_domain") != clock_domain:
        raise ProfilerUsageError("forward evidence and device events use different clock domains")
    scopes, forward_rows = [], boundaries.get("forwards", [])
    seen_forwards = set()
    for forward in forward_rows:
        if forward["forward_id"] in seen_forwards:
            raise ProfilerUsageError("duplicate forward_id")
        seen_forwards.add(forward["forward_id"])
        seen_scopes = set()
        for row in forward.get("scopes", []):
            if row["scope_id"] in seen_scopes:
                raise ProfilerUsageError("duplicate scope_id in forward")
            seen_scopes.add(row["scope_id"])
            scopes.append(_Scope(row, forward["forward_id"], source.rank_id))
            if len(scopes) > max_scopes:
                raise ProfilerUsageError(f"forward boundaries exceed {max_scopes} scopes")
    by_id = defaultdict(list)
    interval_groups = defaultdict(list)
    for scope in scopes:
        if scope.membership:
            for event_id in scope.ids:
                by_id[event_id].append(scope)
        else:
            # Do not let an enclosing body interval turn every event lookup
            # into a scan of all preceding layer scopes in that forward.
            key = "layer" if scope.kind in {"dense_layer", "moe_layer"} else scope.kind
            interval_groups[key].append(scope)
    indices = []
    for intervals in interval_groups.values():
        intervals.sort(key=lambda item: item.start)
        indices.append((intervals, [item.start for item in intervals],
                        list(accumulate((item.end for item in intervals), max))))
    scanned = selected = scope_events = 0
    for event in events:
        scanned += 1
        if scanned > max_events:
            raise ProfilerUsageError(f"forward scan exceeds {max_events} events")
        if event.duration_ns <= 0:
            continue
        matches = []
        for intervals, starts, prefix_ends in indices:
            left = bisect_right(prefix_ends, event.start_ns)
            right = bisect_left(starts, event.end_ns)
            matches.extend(scope for scope in intervals[left:right]
                           if scope.end > event.start_ns and scope.rank_id == event.rank_id)
        matches.extend(scope for scope in by_id.get(event.event_id, ())
                       if scope.rank_id == event.rank_id)
        matches = [scope for scope in matches if scope.device_id is None
                   or scope.device_id == str(event.device_id)]
        bodies = [scope for scope in matches if scope.kind == "target_body"]
        if len(bodies) > 1:
            for scope in bodies:
                scope.reasons.add("overlapping_body_forward_evidence")
        excluded = {scope.forward for scope in matches
                    if scope.kind in {"embedding", "final_norm", "lm_head", "mtp"}}
        for scope in bodies:
            if scope.forward in excluded:
                scope.reasons.add("body_contains_explicitly_excluded_stage")
        if matches:
            selected += 1
        scope_events += len(matches)
        if scope_events > max_scope_events:
            raise ProfilerUsageError(f"forward scope memberships exceed {max_scope_events}; select fewer forwards")
        layer_matches = [scope for scope in matches if scope.kind in {"dense_layer", "moe_layer"}]
        if len(layer_matches) > 1:
            for scope in layer_matches:
                scope.reasons.add("overlapping_layer_evidence")
        for scope in matches:
            scope.add(event)
    finished = defaultdict(list)
    for scope in scopes:
        finished[scope.forward].append(scope.finish())
    forwards, values, layers, stages = [], [], defaultdict(list), defaultdict(list)
    for row in forward_rows:
        results = finished[row["forward_id"]]
        body = [item for item in results if item["kind"] == "target_body"]
        reasons = []
        if len(body) != 1:
            reasons.append("one_explicit_target_body_scope_required")
        elif body[0]["status"] != "measured":
            reasons.extend(body[0]["reasons"])
        phase = row.get("phase", boundaries.get("phase"))
        if phase != "decode":
            reasons.append("decode_phase_unproven")
        value = body[0]["span_ms"] if not reasons else None
        if value is not None:
            values.append(value)
        forwards.append({"forward_id": row["forward_id"], "phase": phase,
                         "status": "measured" if not reasons else "unresolved",
                         "reasons": reasons, "body_forward_span_ms": value,
                         "stages": results})
        for item in results:
            if item["kind"] == "target_body":
                continue
            sample = {"forward_id": row["forward_id"], "phase": phase, **item}
            if phase != "decode":
                sample.update(status="unresolved", span_ms=None,
                              reasons=[*item["reasons"], "decode_phase_unproven"])
            key = (item["kind"], item["layer_id"], item["rank_id"],
                   item["replica"], item["stage"], item["device_id"])
            (layers if item["kind"] in {"dense_layer", "moe_layer"} else stages)[key].append(sample)

    def groups(collection):
        return [{"kind": key[0], "layer_id": key[1], "rank_id": key[2],
                 "replica": key[3], "stage": key[4],
                 "device_id": key[5],
                 "stats": _statistics([item["span_ms"] for item in samples
                                       if item["status"] == "measured"]),
                 "unresolved_count": sum(item["status"] != "measured" for item in samples),
                 "samples": samples} for key, samples in collection.items()]

    return {
        "schema_version": REPORT_SCHEMA, "metric_boundary": "target_body_device_graph",
        "status": "measured" if values and len(values) == len(forwards)
        else "partial" if values else "unresolved",
        "phase": boundaries.get("phase"), "clock_domain": clock_domain,
        "span_start_basis": "first_retained_device_event_start",
        "span_end_basis": "last_retained_device_event_end",
        "source_identity": source.content_identity(), "geometry": boundaries.get("geometry"),
        "comparison_scope": boundaries.get("comparison_scope"),
        "body_forward_span_ms": _statistics(values), "forwards": forwards,
        "per_layer_ms": groups(layers), "stage_span_ms": groups(stages),
        "events_scanned": scanned, "events_selected": selected,
        "limitations": ["Spans include internal device gaps and real communication.",
                        "Per-layer spans may overlap and must not be summed.",
                        "Between-forward scheduling gaps are outside each measured span.",
                        "Boundary declarations require independent occurrence evidence."],
    }
