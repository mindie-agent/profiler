"""Offline CAModel instruction-interval export for mindie-sim pipelines.

[Role]
  Stream a simulator Chrome trace and reduce caller-selected stage invocations
  to active-interval unions. Emit the existing ``durations_ns`` input format.
[Invariants]
  Each window is one complete invocation on an explicit core/pipe selection.
  Overlapping instructions count once; sync slices and idle gaps are excluded.
  Dependencies come from the caller's graph, never inferred from trace order.
  These are simulated interval costs, not board measurements or intrinsic ISA
  latencies. ``displayTimeUnit`` is a viewer hint, not the timestamp unit.
[Timeouts & Locks]
  Streaming scan has an explicit wall budget and selected-interval cap; memory
  is O(selected intervals + declared windows), not O(the full trace). No locks.
[Side-Effect Policy]
  Read supplied files only. The CLI writes only its requested output artifact;
  no simulator, device, network, or measurement database is invoked.
"""
from __future__ import annotations

import argparse
import json
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping

from .events import ProfilerQueryError, ProfilerSchemaError, ProfilerUsageError
from .sources_trace import iter_trace_events


def _number(value: Any, field: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ProfilerSchemaError(f"camodel: invalid {field}: {value!r}") from exc
    if not result.is_finite():
        raise ProfilerSchemaError(f"camodel: non-finite {field}")
    return result


def _time_scale(plan: Mapping[str, Any]) -> Decimal:
    unit = plan.get("timestamp_unit")
    if unit == "ns":
        return Decimal(1)
    if unit == "us":
        return Decimal(1000)
    if unit == "cycles":
        mhz = _number(plan.get("clock_mhz"), "clock_mhz")
        if mhz > 0:
            return Decimal(1000) / mhz
    raise ProfilerUsageError("camodel: declare timestamp_unit=ns|us|cycles (cycles needs clock_mhz > 0)")


def _selections(plan: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    stages = plan.get("stages")
    if not isinstance(stages, Mapping) or not stages:
        raise ProfilerUsageError("camodel: stages must map graph stage/node names to selections")
    result = {}
    for stage, selection in stages.items():
        if not isinstance(selection, Mapping) or "pid" not in selection or not selection.get("tids"):
            raise ProfilerUsageError(f"camodel: {stage} needs explicit pid and tids")
        tids = selection["tids"]
        if not isinstance(tids, list):
            raise ProfilerUsageError(f"camodel: {stage}.tids must be a list")
        names = selection.get("names")
        if names is not None and (not isinstance(names, list) or not names):
            raise ProfilerUsageError(f"camodel: {stage}.names must be a non-empty list when supplied")
        windows = selection.get("windows")
        if not isinstance(windows, list) or not windows:
            raise ProfilerUsageError(f"camodel: {stage} needs one window per complete invocation")
        parsed = []
        for bounds in windows:
            if not isinstance(bounds, list) or len(bounds) != 2:
                raise ProfilerUsageError(f"camodel: {stage} window must be [start, end]")
            start, end = (_number(value, f"{stage}.window") for value in bounds)
            if end <= start:
                raise ProfilerUsageError(f"camodel: {stage} window must have positive length")
            parsed.append((start, end))
        ordered = sorted(parsed)
        if any(right[0] < left[1] for left, right in zip(ordered, ordered[1:])):
            raise ProfilerUsageError(f"camodel: {stage} invocation windows overlap")
        result[str(stage)] = {
            "pid": selection["pid"], "tids": tids, "names": names,
            "windows": parsed, "intervals": [[] for _ in parsed], "sync_excluded": 0,
        }
    return result


def _union(intervals: list[tuple[Decimal, Decimal]]) -> Decimal:
    total = Decimal(0)
    left = right = None
    for start, end in sorted(intervals):
        if right is None or start > right:
            if right is not None:
                total += right - left
            left, right = start, end
        else:
            right = max(right, end)
    return total + (right - left if right is not None else Decimal(0))


def summarize_camodel(
    events: Iterable[Mapping[str, Any]], plan: Mapping[str, Any], *,
    source: str, max_intervals: int = 200_000, timeout_s: float = 30.0,
) -> dict[str, Any]:
    """Reduce explicit invocations; no phase, tile count, or core is guessed."""
    context = plan.get("context", {})
    if not isinstance(context, Mapping) or any(
        not context.get(key) for key in ("soc_version", "simulator_version", "kernel")
    ):
        raise ProfilerUsageError("camodel: context needs soc_version, simulator_version and kernel")
    scale = _time_scale(plan)
    stages = _selections(plan)
    if max_intervals <= 0 or not 0 < timeout_s < float("inf"):
        raise ProfilerUsageError("camodel: interval cap and timeout must be positive and finite")
    deadline = time.monotonic() + timeout_s
    selected = scanned = 0
    sync_names = {"SET_FLAG", "WAIT_FLAG", "BAR", "BARRIER", "PIPE_BARRIER"}
    for event in events:
        scanned += 1
        if time.monotonic() > deadline:
            raise ProfilerQueryError(f"camodel: trace scan exceeded {timeout_s:g}s")
        if event.get("ph") in {"M", "s", "f", "t"}:
            continue
        matched_stage = None
        for stage, selection in stages.items():
            if event.get("pid") != selection["pid"] or event.get("tid") not in selection["tids"]:
                continue
            name = str(event.get("name", ""))
            opcode = name.split("(", 1)[0].split(" ", 1)[0].upper()
            if opcode in sync_names:
                selection["sync_excluded"] += 1
                continue
            if selection["names"] is not None and name not in selection["names"]:
                continue
            if event.get("ph") != "X":
                raise ProfilerSchemaError(f"camodel: {stage} matched non-X instruction {name!r}")
            start = _number(event.get("ts"), "instruction.ts")
            duration = _number(event.get("dur"), "instruction.dur")
            if duration < 0:
                raise ProfilerSchemaError("camodel: negative instruction duration")
            end = start + duration
            for index, (left, right) in enumerate(selection["windows"]):
                if end <= left or start >= right:
                    continue
                if start < left or end > right:
                    raise ProfilerUsageError(f"camodel: {stage} window cuts instruction {name!r}")
                if matched_stage is not None:
                    raise ProfilerUsageError(f"camodel: instruction assigned to both {matched_stage} and {stage}")
                matched_stage = stage
                selected += 1
                if selected > max_intervals:
                    raise ProfilerQueryError(f"camodel: selected intervals exceed cap {max_intervals}")
                selection["intervals"][index].append((start, end))
    durations = {}
    reports = {}
    for stage, selection in stages.items():
        samples = []
        for index, intervals in enumerate(selection["intervals"]):
            if not intervals:
                raise ProfilerUsageError(f"camodel: {stage} invocation {index} has no instruction samples")
            busy = _union(intervals) * scale
            if busy <= 0:
                raise ProfilerUsageError(f"camodel: {stage} invocation {index} has no positive active time")
            samples.append({
                "active_ns": float(busy), "instruction_count": len(intervals),
                "summed_instruction_ns": float(sum((end - start for start, end in intervals), Decimal(0)) * scale),
                "span_ns": float((max(end for _, end in intervals) - min(start for start, _ in intervals)) * scale),
            })
        durations[stage] = median(sample["active_ns"] for sample in samples)
        reports[stage] = {
            "selection": dict(plan["stages"][stage]),
            "samples": samples, "sync_events_excluded": selection["sync_excluded"],
        }
    return {
        "unit": "ns", "durations_ns": durations, "provenance": f"CAModel:{source}",
        "evidence": {
            "source_class": "simulated", "backend": "camodel", "source": source,
            "timing_scope": "selected_instruction_interval_union",
            "aggregation": "median_of_explicit_invocations", "context": dict(context),
            "timestamp_unit": plan["timestamp_unit"], "clock_mhz": plan.get("clock_mhz"),
            "scanned_events": scanned, "selected_intervals": selected, "stages": reports,
        },
    }


def export_camodel(trace: str | Path, plan: Mapping[str, Any], **budgets: Any) -> dict[str, Any]:
    """Stream the existing profiler trace reader; never load a whole capture."""
    return summarize_camodel(iter_trace_events(trace), plan, source=str(Path(trace).resolve()), **budgets)


def main(argv: list[str] | None = None) -> int:
    from .__main__ import _emit

    parser = argparse.ArgumentParser(prog="mindie-profiler camodel", allow_abbrev=False)
    parser.add_argument("--trace", required=True, help="CAModel trace.json or exported Chrome trace")
    parser.add_argument("--plan", required=True, help="explicit context, timestamp unit and stage invocations JSON")
    parser.add_argument("--output", default=None, help="write stage durations for mindie-sim pipeline")
    parser.add_argument("--max-intervals", type=int, default=200_000)
    parser.add_argument("--timeout-s", type=float, default=30.0)
    args = parser.parse_args(argv)
    plan_path = Path(args.plan)
    if plan_path.stat().st_size > 1024 * 1024:
        raise ProfilerUsageError("camodel: plan exceeds 1 MiB; split into separate kernel/shape cases")
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfilerUsageError(f"camodel: invalid plan JSON: {exc}") from exc
    if not isinstance(plan, Mapping):
        raise ProfilerUsageError("camodel: plan must be an object")
    payload = export_camodel(args.trace, plan, max_intervals=args.max_intervals, timeout_s=args.timeout_s)
    return _emit(payload, args.output)
