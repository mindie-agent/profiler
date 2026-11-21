"""Trial journal, observation emission and CLI execution for ``bench sku``.

[Role]
  Own ``JsonlSink`` (append-only fsynced resume journal with torn-tail repair),
  ``_emit_observations``, ``run_cases`` and ``_run_one`` for the five-domain
  SKU microbench, keeping ``bench_sku_microbench`` strictly under 800 lines.

[Invariants]
  * ``host_fallback`` fails closed unless ``allow_cpu_smoke=True`` is explicitly
    requested; missing kernels attach ``mindie-unmodeled-structure-hint/1``.
  * Published receipts are scrubbed via ``scrub_portable`` / ``portable_receipt``.
  * The original plan and requested shape survive a budget rejection.
    Only successful full-shape runs emit timing observations.

[Timeouts & Locks]
  Single-process bounded execution; fsyncs each completed trial row.

[Side-Effect Policy]
  Writes only explicit ``resume``, ``observations`` and ``output`` paths.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence
import uuid

from ..events import ProfilerUsageError
from .abi import capture_uri, scrub_portable
from .observations import (
    ObservationJournal, case_complete_row, completion_key, observation_row, timing_rows,
)
from .operators import (
    BenchUnmodeledOperatorError,
    build_operator_enqueue,
    supports_cold_ring,
)
from .operators_common import shape_of
from .profiles import profile_section
from .timing import HOST_FALLBACK, calibrate_blocker, case_over_budget

MICROBENCH_SCHEMA = "mindie-bench-sku-microbench/1"
RECEIPT_SCHEMA = "mindie-bench-receipt/1"
_CFG = profile_section("sku_microbench")
_JOURNAL_MODE = int(_CFG["journal_mode"])
_REASON_LIMIT = int(_CFG["max_reason_chars"])
_PRECYCLE_FACTOR = int(_CFG["precycle_trial_factor"])
_RUN_SUFFIX_CHARS = 2 * 2 * 2
BYTE_RATE_OPS = frozenset({"gather", "mte2_aic", "mte2_aiv", "pinned_copy", "ple_lookup"})
_RECEIPT_EVIDENCE = (
    "plan_key", "requested_shape", "actual_shape", "participating_ranks",
    "cold_ring_bytes", "timing_events",
)


class JsonlSink:
    """Append-only, fsynced JSONL trial log with torn-tail repair."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.repair()

    def repair(self) -> int:
        return ObservationJournal(self.path).repair()

    def _records(self):
        self.repair()
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, Mapping):
                    yield dict(record)

    def completed_case_keys(self) -> set[tuple[Any, str]]:
        keys: set[tuple[Any, str]] = set()
        for record in self._records():
            if record.get("status") != "ok":
                continue
            case_id = record.get("case_id")
            if isinstance(case_id, str) and case_id:
                keys.add((record.get("sku"), case_id))
        return keys

    def completed_case_ids(self) -> set[str]:
        return {case_id for _sku, case_id in self.completed_case_keys()}

    def append(self, record: Mapping[str, Any]) -> None:
        if self.path.exists() and self.path.stat().st_size:
            with self.path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    self.repair()
        line = json.dumps(dict(record), ensure_ascii=False, sort_keys=True) + "\n"
        descriptor = os.open(
            self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, _JOURNAL_MODE
        )
        try:
            payload = line.encode("utf-8")
            if os.write(descriptor, payload) != len(payload):
                raise ProfilerUsageError("bench_resume_short_write")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _emit_observations(
    journal: Any, case: Mapping[str, Any], record: Mapping[str, Any], sku: Any, run_id: str
) -> None:
    if journal is None or record.get("status") != "ok":
        return
    timing = record.get("timing")
    if not isinstance(timing, Mapping):
        return
    flops = int(case.get("work_flops") or 0)
    byte_rate = case.get("work_bytes") if case.get("op") in BYTE_RATE_OPS else None
    knee = (
        {"work": flops, "resource": "cube", "work_unit": "flops", "active_units": 1}
        if flops > 0 and str(case.get("case_id") or "").startswith("d2.mknee.")
        else {}
    )
    case_obs = {**case, "hardware": sku or case.get("hardware")}
    validated = bool(record.get("validated", True))
    for mode, mode_qualified, trial, repeat_index, repeat_us in timing_rows(timing):
        journal.append(
            observation_row(
                plan_id=sku,
                case=case_obs,
                run_id=f"{run_id}.{mode}.t{trial}",
                split=str(case.get("split") or "train"),
                boundary=str(case.get("boundary") or "device_kernel"),
                timing_mode=mode,
                residency=str(case.get("residency") or "device"),
                trial=trial,
                repeat_index=repeat_index,
                rank=None,
                duration_ms=float(repeat_us) / 1000.0,
                source=f"capture://bench-sku/{case.get('case_id')}/{mode}.{trial}.{repeat_index}",
                validated=validated,
                qualified=validated and mode_qualified,
                sku=sku,
                level="operator",
                phase=case.get("phase"),
                execution={"mode": mode, "protocol": timing.get("protocol")},
                work_bytes=byte_rate,
                **knee,
            )
        )
    journal.append(
        case_complete_row(
            plan_id=sku,
            case_id=case.get("case_id"),
            run_id=run_id,
            sku=sku,
            status="ok",
            split=str(case.get("split") or "train"),
            summary={"domain": case.get("domain"), "op": case.get("op"),
                     **{key: record[key] for key in _RECEIPT_EVIDENCE if key in record}},
        )
    )


def _blocker_prefix(unit_op: Callable[[], Any], repeats: int) -> Callable[[], Any]:
    def arm() -> None:
        for _ in range(int(repeats)):
            unit_op()

    return arm


def _timing_events(timing: Mapping[str, Any]) -> dict[str, Any]:
    modes = {}
    for mode, summary in (timing.get("modes") or {}).items():
        sample_count = summary.get("repeat_count")
        if sample_count is None:
            sample_count = sum(len(trial.get("repeats_us", ())) for trial in summary.get("trials", ()))
        modes[mode] = sample_count
    if timing.get("hot_control") is not None:
        modes["hot_control"] = len(timing["hot_control"].get("repeats_us", ()))
    return {"source": timing.get("timer_source"), "samples_by_mode": modes}


def _run_one(
    case: Mapping[str, Any],
    *,
    context: Mapping[str, Any],
    protocol: Any,
    home: str | None,
    sku: str | None = None,
) -> dict[str, Any]:
    requested_shape = dict(shape_of(case))
    record: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "sku": sku,
        "case_id": str(case["case_id"]),
        "domain": case["domain"],
        "op": case["op"],
        "dtype": case["dtype"],
        "split": case["split"],
        "plan_key": case.get("plan_key"),
        "requested_shape": requested_shape,
        "status": "ok",
        "source_uri": capture_uri("bench-sku", str(case["case_id"])),
    }
    if case.get("parallel_axis") in {"pcp", "dcp"} and case.get("world_size", 1) > 1:
        record.update(status="plan_only", reason="context-parallel plan requires a distributed runner")
        return scrub_portable(record, home=home)
    if case_over_budget(case, context.get("budget")):
        record.update({"status": "over_budget", "reason": "case working set exceeds the S0 cap"})
        return scrub_portable(record, home=home)
    ring = context.get("ring")
    ring_allocated = bool(getattr(ring, "allocated", False))
    allocated = getattr(ring, "allocated_bytes", 0) if ring_allocated else 0
    actual_shape = dict(requested_shape)
    context = dict(context, _byte_ledger={"peak_bytes": int(allocated or 0)},
                   _hot_arena={"sub_offset": 0}, _actual_shape=actual_shape)
    try:
        torch = context["torch"]
        cold = ring_allocated and supports_cold_ring(case)
        run_kwargs: dict[str, Any] = {}
        if cold:
            effective = dict(case, cold_ring=True)
            enqueue = build_operator_enqueue(torch, effective, context)
            hot_enqueue = build_operator_enqueue(torch, effective, context, hot=True)
            precycle = getattr(ring, "precycle", None)
            if callable(precycle):
                precycle(int(getattr(protocol, "repeats", 0)) * _PRECYCLE_FACTOR)
            run_kwargs.update({"cold_ring": ring, "hot_enqueue": hot_enqueue})
        else:
            enqueue = build_operator_enqueue(torch, case, context)
        if any(actual_shape.get(key) != value for key, value in requested_shape.items()):
            raise ProfilerUsageError("bench_requested_shape_mismatch")
        blocker, blocker_receipt = None, None
        unit_op = context.get("blocker_unit_op")
        if callable(unit_op):
            calibrated = calibrate_blocker(context["runtime"], unit_op)
            blocker_receipt = calibrated.receipt()
            if calibrated.repeats:
                blocker = _blocker_prefix(unit_op, calibrated.repeats)
        timing = protocol.run(
            enqueue,
            case_id=str(case["case_id"]),
            kind="collective" if case["op"] in {"all_reduce", "all_gather"} else "operator",
            nbytes=int(case.get("work_bytes") or 0),
            blocker=blocker,
            blocker_receipt=blocker_receipt,
            **run_kwargs,
        )
        if not context.get("allow_cpu_smoke") and (
            timing.get("timer_source") == "perf_counter_host_fallback"
            or HOST_FALLBACK in (timing.get("modes") or {})
        ):
            raise ProfilerUsageError("bench_host_fallback_forbidden")
        device = context.get("device") or {}
        ring_plan = getattr(ring, "plan", None) or {}
        record.update(
            {
                "timing": timing,
                "actual_shape": actual_shape,
                "participating_ranks": [int(device.get("local_rank", device.get("ordinal", 0)))],
                "cold_ring_bytes": int(ring_plan.get("total_bytes", allocated)) if cold else 0,
                "timing_events": _timing_events(timing),
                "minimum_ms": timing["minimum_ms"],
                "startup_ms": 0.0,
                "validated": True,
                "qualified": bool(timing.get("qualified", True)),
                "work_bytes": int(case.get("work_bytes") or 0),
                "work_flops": int(case.get("work_flops") or 0),
                "group_list": case.get("group_list"),
                "group_list_type": case.get("group_list_type"),
            }
        )
    except TimeoutError:
        raise
    except Exception as exc:
        status = "unsupported_binding" if isinstance(exc, ProfilerUsageError) else "failed"
        if isinstance(exc, ProfilerUsageError) and str(exc).startswith("bench_vram_budget_exceeded:"):
            status = "over_budget"
        record.update({"status": status, "reason": str(exc)[:_REASON_LIMIT]})
        if isinstance(exc, BenchUnmodeledOperatorError):
            record["unmodeled_hint"] = dict(exc.payload)
    return scrub_portable(record, home=home)


def _base_run_id(record: Mapping[str, Any]) -> str | None:
    """Recover the base execution run id from a receipt or observation row."""
    value = record.get("run_id")
    if not value:
        return None
    text = str(value)
    if record.get("record_type") == "case_complete":
        return text
    mode, trial = record.get("timing_mode"), record.get("trial")
    if mode is not None and trial is not None:
        suffix = f".{mode}.t{int(trial)}"
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def _recorded_run_id(*sources: Any) -> str | None:
    """Recover the first recorded run id so a resumed execution stays stable."""
    for source in sources:
        if source is None:
            continue
        iterator = getattr(source, "records", None) or getattr(source, "_records", None)
        if not callable(iterator):
            continue
        records = iterator()
        if records is None:
            continue
        for record in records:
            value = _base_run_id(record)
            if value:
                return value
    return None


def run_cases(
    cases: Sequence[Mapping[str, Any]],
    *,
    context: Mapping[str, Any],
    resume: str | Path | None = None,
    observations: str | Path | None = None,
    sku: str | None = None,
    home: str | None = None,
) -> dict[str, Any]:
    """Execute admitted cases and append one portable receipt per case."""
    sink = JsonlSink(resume) if resume else None
    journal = ObservationJournal(observations) if observations else None
    run_id = (
        _recorded_run_id(sink, journal)
        or str(context.get("run_id") or "")
        or f"{sku or 'bench-sku'}-{uuid.uuid4().hex[:_RUN_SUFFIX_CHARS]}"
    )
    journal_done: dict[tuple[Any, Any], Any] = {}
    if journal is not None:
        journal.purge_incomplete_cases()
        journal_done = {
            key: row.get("summary") for row in journal.records()
            if (key := completion_key(row)) is not None
        }
    sink_done = sink.completed_case_keys() if sink is not None else set()
    completed = sink_done | journal_done.keys()
    protocol = context["protocol"]
    records: list[dict[str, Any]] = []
    skipped: list[str] = []
    recovered = 0
    for case in cases:
        case_id = str(case["case_id"])
        key = (sku, case_id)
        if key in completed:
            if sink is not None and key in journal_done and key not in sink_done:
                summary = journal_done[key]
                evidence = ({field: summary[field] for field in _RECEIPT_EVIDENCE if field in summary}
                            if isinstance(summary, Mapping) else {})
                sink.append({
                    "schema": RECEIPT_SCHEMA, "sku": sku, "case_id": case_id,
                    "domain": case.get("domain"), "op": case.get("op"),
                    "dtype": case.get("dtype"), "split": case.get("split"),
                    "status": "ok", "run_id": run_id, "recovered": True,
                    "source_uri": capture_uri("bench-sku", case_id),
                    **evidence,
                })
            skipped.append(case_id)
            recovered += 1
            continue
        record = _run_one(case, context=context, protocol=protocol, home=home, sku=sku)
        record.setdefault("run_id", run_id)
        records.append(record)
        _emit_observations(journal, case, record, sku, run_id)
        if sink is not None:
            sink.append(record)
    plan_only_count = sum(item["status"] == "plan_only" for item in records)
    return {
        "schema": MICROBENCH_SCHEMA,
        "status": "ok" if all(item["status"] in {"ok", "plan_only"} for item in records) else "partial",
        "run_id": run_id,
        "case_count": len(cases),
        "executed_case_count": len(records) - plan_only_count,
        "plan_only_case_count": plan_only_count,
        "skipped_case_count": len(skipped),
        "skipped_case_ids": skipped,
        "recovered_records": recovered,
        "recovered_case_ids": list(skipped),
        "records": records,
    }


def emit_sku_output(payload: Mapping[str, Any], output: str | None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        target = Path(output)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(target.name + ".tmp")
        temporary.write_text(text, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        print(json.dumps({"output": str(target), "status": payload.get("status")}, sort_keys=True))
        return
    sys.stdout.write(text)


__all__ = [
    "BYTE_RATE_OPS", "JsonlSink", "MICROBENCH_SCHEMA", "RECEIPT_SCHEMA",
    "_emit_observations", "_run_one", "emit_sku_output", "run_cases",
]
