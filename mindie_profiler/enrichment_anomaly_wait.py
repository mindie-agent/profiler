"""Wait-interval anchor attribution, AI_CPU stall summaries, and PMU anomaly enrichment (enrichment_anomaly_wait).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting wait-interval anchor attribution, ai_cpu stall summaries, and pmu anomaly enrichment.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import re
from typing import Any, Mapping, Sequence
from .anomaly_discovery import (
    KernelEvent,
    assess_aicpu_exposure,
    assess_wait_anchor,
)
from .events import Event, Observation

WAIT_ANCHOR_REASON = (
    "no complete unambiguous waitNs/Wait Time event with a fully observed wait "
    "interval was available for Wait-Anchor verification"
)

PMU_REASON = (
    "no AICPU-specific PMU counters were attached to the selected AICPU events; "
    "AI-core PMU is not used as AICPU counter evidence"
)

UNDERFEED_THRESHOLD = 0.30

PMU_SCHEMA = "mindie-pmu-observation/1"

def _duration_ms(value_ns: int | None) -> float | None:
    return None if value_ns is None else round(float(value_ns) / 1_000_000.0, 6)

def _relative_us(value_ns: int, origin_ns: int) -> float:
    return (int(value_ns) - int(origin_ns)) / 1000.0

def add_limitation(
    limitations: list[dict[str, Any]],
    code: str,
    scope: str,
    detail: str,
    severity: str = "medium",
) -> None:
    for item in limitations:
        if item.get("code") == code and item.get("scope") == scope:
            return
    limitations.append({"code": code, "scope": scope, "detail": detail, "severity": severity})

def _finding(
    finding_type: str,
    severity: str,
    confidence: str,
    summary: str,
    evidence_ref: str,
    *,
    scope: Mapping[str, Any] | None = None,
    limitation_code: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "finding_type": finding_type,
        "severity": severity,
        "confidence": confidence,
        "summary": summary,
        "evidence_ref": evidence_ref,
        "evidence_scope": dict(scope or {}),
    }
    if limitation_code is not None:
        payload["limitation_code"] = limitation_code
    return payload

def _explicit_task_type(event: Event) -> str | None:
    engine = str(getattr(event, "execution_engine", "") or "")
    if event.is_aicpu or engine == "aicpu":
        return "AI_CPU"
    if event.is_comm or engine == "hccl":
        return "COMMUNICATION"
    if engine in {"aic", "aiv", "mix"}:
        return "AI_CORE"
    return event.task_type or event.core or None

def _stream_id(event: Event) -> int | None:
    match = re.search(r"\d+", str(event.stream_id or ""))
    return int(match.group(0)) if match else None

def _wait_interval(
    event: Event,
    window,
) -> tuple[float | None, float | None, str | None]:
    """Return (wait_us, wait_start_us, exclusion_reason) for assessment.

    The returned interval is relative to the observation window origin.  Only
    a complete event with a fully observed wait interval is usable.
    """

    wait_ns = event.wait_ns
    if event.wait_status != "bound" or wait_ns is None:
        return None, None, f"wait_status_{event.wait_status}"
    if not event.complete_in(window.start_ns, window.end_ns):
        return None, None, "event_clipped_by_window"
    wait_us = float(wait_ns) / 1000.0
    wait_end_us = _relative_us(event.start_ns, window.start_ns)
    wait_start_us = wait_end_us - wait_us
    if wait_start_us < 0:
        return None, None, "wait_interval_outside_observed_window"
    return wait_us, wait_start_us, None

def _mapped_events(observation: Observation) -> tuple[list[KernelEvent], int, list[Event]]:
    origin_ns = int(observation.window.start_ns)
    observation_id = str(observation.identity()["observation_id"])
    mapped: list[KernelEvent] = []
    core_events: list[Event] = []
    for event in observation.events:
        clipped = event.clipped(observation.window.start_ns, observation.window.end_ns)
        if clipped is None:
            continue
        left, right = clipped
        wait_us, wait_start_us, _reason = _wait_interval(event, observation.window)
        counters: tuple[tuple[str, float], ...] = ()
        if (
            event.complete_in(observation.window.start_ns, observation.window.end_ns)
            and event.pmu_status == "bound"
            and event.pmu
            and event.pmu_kind == "aicore"
            and not event.is_aicpu
            and not event.is_comm
        ):
            counters = event.pmu
        identity = event.identity()
        mapped.append(
            KernelEvent(
                name=event.name or "<missing>",
                step=observation.window.step,
                start_us=_relative_us(left, origin_ns),
                duration_us=_relative_us(right, left),
                wait_us=wait_us,
                task_type=_explicit_task_type(event),
                accelerator_core=event.core or None,
                stream_id=_stream_id(event),
                rank=event.rank_index if event.rank_index is not None else event.rank_id,
                event_id=str(identity["event_id"]),
                wait_start_us=wait_start_us,
                wait_end_us=(None if wait_start_us is None else wait_start_us + (wait_us or 0.0)),
                counters=counters,
                observation_id=observation_id,
                window_start_ns=observation.window.start_ns,
                window_end_ns=observation.window.end_ns,
                window_label=observation.window.label or str(observation.window.step),
                source_kind=observation.source.kind,
                source_sha256=observation.source.sha256,
                source_table=event.table,
                device_id=event.device_id,
                global_task_id=event.locator.get("task_global_id"),
                task_id=event.task_id,
                semantic_block=event.block,
                event_start_ns=event.start_ns,
                event_end_ns=event.end_ns,
                wait_ns=(None if wait_us is None else event.wait_ns),
                wait_start_ns=(
                    None if wait_us is None or event.wait_ns is None else event.start_ns - int(event.wait_ns)
                ),
                wait_end_ns=(None if wait_us is None else event.start_ns),
                event_identity=identity,
            )
        )
        core_events.append(event)
    return mapped, origin_ns, core_events

def _measurement_counts(observations: Sequence[Observation]) -> dict[str, int]:
    counts = {
        "event_count": 0,
        "wait_bound_event_count": 0,
        "wait_usable_event_count": 0,
        "wait_clipped_event_count": 0,
        "wait_outside_window_event_count": 0,
        "wait_ambiguous_event_count": 0,
        "wait_absent_event_count": 0,
        "wait_not_available_event_count": 0,
        "wait_not_applicable_event_count": 0,
        "pmu_bound_event_count": 0,
        "pmu_ambiguous_event_count": 0,
        "pmu_clipped_bound_event_count": 0,
        "aicpu_event_count": 0,
    }
    for observation in observations:
        for event in observation.events:
            counts["event_count"] += 1
            status = event.wait_status
            if status == "bound":
                counts["wait_bound_event_count"] += 1
                wait_us, _start, reason = _wait_interval(event, observation.window)
                if wait_us is not None:
                    counts["wait_usable_event_count"] += 1
                elif reason == "event_clipped_by_window":
                    counts["wait_clipped_event_count"] += 1
                elif reason == "wait_interval_outside_observed_window":
                    counts["wait_outside_window_event_count"] += 1
            elif status == "ambiguous_task_occurrence":
                counts["wait_ambiguous_event_count"] += 1
            elif status in {"absent", "invalid_value"}:
                counts["wait_absent_event_count"] += 1
            elif status == "not_available":
                counts["wait_not_available_event_count"] += 1
            elif status == "not_applicable":
                counts["wait_not_applicable_event_count"] += 1
            if event.pmu_status == "bound":
                counts["pmu_bound_event_count"] += 1
                if not event.complete_in(observation.window.start_ns, observation.window.end_ns):
                    counts["pmu_clipped_bound_event_count"] += 1
            elif event.pmu_status in {
                "ambiguous_task_occurrence",
                "duplicate_metric_rows",
                "incomplete_metric_value",
                "cardinality_unknown",
            }:
                counts["pmu_ambiguous_event_count"] += 1
            if event.is_aicpu:
                counts["aicpu_event_count"] += 1
    return counts

def _evidence_scope(observation: Observation, core_events: Sequence[Event] | None = None) -> dict[str, Any]:
    events = list(core_events if core_events is not None else observation.events)
    streams = sorted({str(event.stream_id) for event in events if event.stream_id})
    task_types = sorted(
        {str(_explicit_task_type(event)) for event in events if _explicit_task_type(event) is not None}
    )
    task_ids = sorted({str(event.task_id) for event in events if event.task_id})
    tables = sorted({str(event.table) for event in events if event.table})
    names = sorted({str(event.name) for event in events if event.name})
    devices = sorted({str(event.device_id) for event in events if event.device_id})
    bound_families = sorted({str(event.bound_family) for event in events if event.bound_family})
    execution_engines = sorted(
        {str(getattr(event, "execution_engine", "unknown") or "unknown") for event in events}
    )
    return {
        "observation_id": observation.identity()["observation_id"],
        "rank_id": observation.rank_id,
        "rank_index": observation.rank_index,
        "step": observation.window.step,
        "window_label": observation.window.label or str(observation.window.step),
        "time_origin_ns": observation.window.start_ns,
        "window_start_ns": observation.window.start_ns,
        "source_kind": observation.source.kind,
        "source_sha256": observation.source.sha256,
        "window_end_ns": observation.window.end_ns,
        "stream_ids": streams,
        "task_types": task_types,
        "reported_task_types": sorted({str(event.task_type) for event in events if event.task_type}),
        "reported_cores": sorted({str(event.core) for event in events if event.core}),
        "task_ids": task_ids[:32],
        "event_tables": tables,
        "kernel_names": names[:16],
        "device_ids": devices[:16],
        "bound_families": bound_families,
        "execution_engines": execution_engines,
        "event_count": len(events),
        "aicpu_event_count": sum(1 for event in events if event.is_aicpu),
        "comm_event_count": sum(1 for event in events if event.is_comm),
        "wait_bound_event_count": sum(1 for event in events if event.wait_status == "bound"),
        "wait_ambiguous_event_count": sum(
            1 for event in events if event.wait_status == "ambiguous_task_occurrence"
        ),
        "hardware_scope": {
            "status": "not_available",
            "reason": "no hardware identity envelope was attached to the observation",
        },
        "pmu_bound_event_count": sum(1 for event in events if event.pmu_status == "bound"),
        "pmu_ambiguous_event_count": sum(
            1
            for event in events
            if event.pmu_status
            in {
                "ambiguous_task_occurrence",
                "duplicate_metric_rows",
                "incomplete_metric_value",
                "cardinality_unknown",
            }
        ),
    }

def wait_anchor_summary(observations: Sequence[Observation]) -> dict[str, Any]:
    scopes = [_evidence_scope(observation) for observation in observations if observation.events]
    counts = _measurement_counts(observations)
    limitations: list[dict[str, Any]] = []
    if counts["wait_ambiguous_event_count"]:
        add_limitation(
            limitations,
            "wait_time_ambiguous_task_occurrence",
            "global",
            "One or more selected events share a globalTaskId with other full-capture TASK "
            "occurrences; their CTI waitNs is group-scoped and was not assigned.",
            "high",
        )
    if counts["wait_clipped_event_count"]:
        add_limitation(
            limitations,
            "wait_time_clipped_event_not_used_for_wait_anchor",
            "global",
            "One or more events carrying waitNs were clipped by the observation window; "
            "their full wait was not used for Wait-Anchor.",
            "high",
        )
    if counts["wait_outside_window_event_count"]:
        add_limitation(
            limitations,
            "wait_interval_outside_observed_window",
            "global",
            "One or more complete events have a wait interval starting before the observation "
            "window; only fully observed wait intervals are used.",
            "medium",
        )
    if not counts["wait_usable_event_count"]:
        add_limitation(limitations, "wait_anchor_unverified", "global", WAIT_ANCHOR_REASON, "medium")
        if counts["wait_absent_event_count"] or counts["wait_not_available_event_count"]:
            add_limitation(
                limitations,
                "wait_time_absent_or_unavailable",
                "global",
                "No explicit waitNs/Wait Time value was present for the selected events.",
                "medium",
            )
        return {
            "status": "unverified",
            "wait_anchor_false_hotspot": None,
            "reason": WAIT_ANCHOR_REASON,
            "assessment": "not_run",
            "findings": [],
            "limitations": limitations,
            "measurement_scope": counts,
            "evidence_scope": scopes,
            "hardware_scope": {
                "status": "not_available",
                "reason": "no hardware identity envelope was attached to the observations",
            },
        }
    mapped: list[KernelEvent] = []
    for observation in observations:
        events, _, _ = _mapped_events(observation)
        mapped.extend(events)
    report = assess_wait_anchor(mapped)
    overlap_missing = 0
    no_individual = 0
    for item in report.limitations:
        text = str(item)
        if text.startswith("missing_wait_time"):
            continue
        if text.startswith("wait_anchor_overlap_missing:"):
            overlap_missing += 1
            continue
        if text.startswith("wait_anchor_no_individual_candidate:"):
            no_individual += 1
            continue
        add_limitation(limitations, text, "global", "Wait-Anchor limitation", "medium")
    if overlap_missing:
        add_limitation(
            limitations,
            "wait_anchor_overlap_missing",
            "global",
            f"{overlap_missing} Wait-Anchor candidate group(s) lacked a same-scope overlapping event; no false-hotspot flag was emitted for them.",
            "medium",
        )
    if no_individual:
        add_limitation(
            limitations,
            "wait_anchor_no_individual_candidate",
            "global",
            f"{no_individual} Wait-Anchor group candidate(s) had no individual event meeting the strict wait-ratio and tiny-duration thresholds; no group result was attached to an individual hotspot.",
            "high",
        )
    raw_findings = report.as_c7_list()
    findings: list[dict[str, Any]] = []
    for item in raw_findings:
        confirmed = bool(item.get("is_false_hotspot_risk"))
        candidate_ids = list(item.get("candidate_event_ids") or [])
        event_ref = candidate_ids[0] if candidate_ids else f"wait_anchor:{item.get('location')}:{item.get('op_name')}"
        findings.append(
            {
                **item,
                "finding_type": "wait_anchor_masked" if confirmed else "wait_anchor_insufficient",
                "severity": "high" if confirmed else "medium",
                "confidence": "high" if confirmed else "low",
                "summary": (
                    f"Wait-Anchor candidate {item.get('op_name')} has wait ratio "
                    f"{item.get('wait_ratio')} and insufficient correlated overlap."
                    if not confirmed
                    else f"Wait-Anchor candidate {item.get('op_name')} overlaps another "
                    "same-scope event while carrying high wait time."
                ),
                "evidence_ref": f"wait_anchor:{event_ref}",
            }
        )
    confirmed = any(item.get("is_false_hotspot_risk") for item in raw_findings)
    return {
        "status": report.status,
        "wait_anchor_false_hotspot": True if confirmed else None,
        "reason": None,
        "assessment": report.status,
        "findings": findings,
        "limitations": limitations,
        "measurement_scope": counts,
        "evidence_scope": scopes,
        "hardware_scope": {
            "status": "not_available",
            "reason": "no hardware identity envelope was attached to the observations",
        },
    }
