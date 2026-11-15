"""C7 ``mindie-profile-summary/1`` report assembly.

[Role]
  Turn measured observations into the compact, data-traceable C7 JSON
  contract consumed by other MindIE packages.  The report separates wall,
  busy union, kernel sum, exposed communication, host/idle gap, seven semantic
  blocks, rank medians, and the slowest rank.

[Invariants]
  * Missing data is ``None``; the report never substitutes zero or a model
    prediction for a measurement.
  * Modeling fields stay ``unmodeled`` unless ``analyze_profile`` receives an
    explicit provider and complete user-supplied kernel inputs; the report
    itself never invents an ideal lower bound or predicted time.
  * Every hotspot carries source sha256/table/filter/task ids where available;
    bounded locator samples are marked separately from full measured totals.
  * Every share states its denominator explicitly: block shares use attributed
    block-union time and hotspot shares use device-activity-sum time.
  * ``steady_steps`` contains only caller-supplied steps; untagged windows stay
    untagged in ``window_accounting``.
  * Every window retains its clock-coverage receipt (clipped/comparable counts
    and sourced reference domains); rank names alone never imply shared clocks.

[Timeouts & Locks]
  O(n log n) medians and sorts over bounded events; optional atomic JSON write.

[Side-Effect Policy]
  Writes only the requested output JSON via a temporary file + ``os.replace``;
  no network and no mutation of source artifacts.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence
from .accounting import hotspot_aggregates, percentile
from .classify import ALL_BLOCKS, EVENT_BLOCKS, MAPPING_RULES
from .cross_rank import (
    _observation_accounting,
    _reference_projections,
    aggregate_observations,
    cross_rank_stats,
    p50,
)
from .events import Observation, PARSER_VERSION, REPORT_SCHEMA, SourceRef

from .report_sections import (
    _bound_family, _clock_coverage, _execution_engine, _filter_sql, _hotspot_key,
    _hotspots, _id_list, _metric_definitions, _ms, _schema_version, _source_kind,
    _source_sha_map,
)

def _comparison_projection(observations: Sequence[Observation]):
    """Return the common reference, its per-window projection and completeness.

    A projection exists only when CLOCK declared one common reference and every
    selected observation contributed at least one mapped event.  ``complete``
    is stricter: every usable window must have mapped all of its contribution.
    A partial mapping keeps its local duration as the comparison value.
    """
    reference_data = _reference_projections(observations)
    if reference_data is None:
        return "local", None, False
    domain, projections = reference_data
    usable = [obs for obs in observations if obs.accounting.available]
    complete = bool(usable) and all(
        projections.get(id(obs), {}).get("complete") for obs in usable
    )
    return domain, projections, complete

def _window_accounting(observations: Sequence[Observation]) -> list[dict]:
    # Duration-distribution summaries above this row are computed in the
    # common reference domain when CLOCK supplies a complete mapping.  Carry
    # the same projected accounting on the selected window row so a consumer
    # can check the declaration against the exact domain it was produced from.
    # Local durations remain on the existing fields; no value is overwritten.
    comparison_domain, projections, comparison_complete = _comparison_projection(
        observations
    )
    rows: list[dict] = []
    for observation in observations:
        accounting = observation.accounting
        projected = _observation_accounting(observation, projections)
        rows.append(
            {
                "rank_id": observation.rank_id,
                "rank_index": observation.rank_index,
                "step": observation.window.step,
                "label": observation.window.label,
                "window_origin_ns": observation.window.start_ns,
                "window_start_ns": observation.window.start_ns,
                "window_end_ns": observation.window.end_ns,
                "window_start_us": 0.0,
                "window_end_us": round(observation.window.span_ns / 1000.0, 3),
                "event_count": accounting.event_count,
                "complete_event_count": accounting.complete_event_count,
                "clipped_event_count": accounting.clipped_event_count,
                "comm_event_count": accounting.comm_event_count,
                "stream_count": accounting.stream_count,
                "request_wall_ms": _ms(accounting.request_wall_ns),
                "window_duration_ms": _ms(accounting.window_span_ns),
                "observed_event_span_ms": _ms(accounting.observed_event_span_ns),
                "device_busy_union_ms": _ms(accounting.busy_union_ns),
                "device_activity_sum_ms": _ms(accounting.device_activity_sum_ns),
                "exposed_comm_ms": _ms(accounting.exposed_comm_ns),
                "device_uncovered_ms": _ms(accounting.device_uncovered_ns),
                "host_dispatch_gap_ms": _ms(accounting.host_dispatch_gap_ns),
                "total_cost_ms": _ms(accounting.total_cost_ns),
                # Deprecated aliases: same measured values, explicit old names.
                "wall_ms": _ms(accounting.observed_event_span_ns),
                "busy_union_ms": _ms(accounting.busy_union_ns),
                "kernel_sum_ms": _ms(accounting.device_activity_sum_ns),
                "host_gap_ms": _ms(accounting.device_uncovered_ns),
                "exposed_aicpu_ms": _ms(accounting.exposed_aicpu_ns),
                "underfeed_bubble_ratio": accounting.underfeed_ratio,
                "aicpu_exposed_ratio": accounting.aicpu_exposed_ratio,
                "coverage_ratio": accounting.coverage_ratio,
                "largest_internal_bubble_ms": _ms(accounting.largest_internal_bubble_ns),
                "block_union_ms": {
                    block: (_ms(accounting.block_union_ns.get(block)) if accounting.available else None)
                    for block in ALL_BLOCKS
                },
                "block_share_pct": {
                    block: accounting.block_share_pct.get(block) for block in ALL_BLOCKS
                },
                "comparison_domain": comparison_domain,
                "comparison_complete": comparison_complete,
                "comparison_event_count": projected.event_count,
                "comparison_observed_event_span_ms": _ms(projected.observed_event_span_ns),
                "comparison_device_busy_union_ms": _ms(projected.busy_union_ns),
                "comparison_device_activity_sum_ms": _ms(projected.device_activity_sum_ns),
                "comparison_exposed_comm_ms": _ms(projected.exposed_comm_ns),
                "comparison_device_uncovered_ms": _ms(projected.device_uncovered_ns),
                "comparison_total_cost_ms": _ms(projected.total_cost_ns),
                "comparison_underfeed_bubble_ratio": projected.underfeed_ratio,
                "comparison_aicpu_exposed_ratio": projected.aicpu_exposed_ratio,
                "comparison_coverage_ratio": projected.coverage_ratio,
                "comparison_block_union_ms": {
                    block: (_ms(projected.block_union_ns.get(block)) if projected.available else None)
                    for block in ALL_BLOCKS
                },
                "comparison_block_share_pct": {
                    block: projected.block_share_pct.get(block) for block in ALL_BLOCKS
                },
                "clock_coverage": _clock_coverage(observation),
                "source": {
                    "kind": observation.source.kind,
                    "basename": observation.source.basename,
                    "sha256": observation.source.sha256,
                    "schema_version": observation.source.schema_version,
                },
                "query": {
                    "rows_read": observation.stats.rows_read,
                    "rows_selected": observation.stats.rows_selected,
                    "bad_rows": observation.stats.bad_rows,
                    "elapsed_ms": observation.stats.elapsed_ms,
                },
            }
        )
    return rows

def _block_breakdown(observations: Sequence[Observation]) -> list[dict]:
    # The step summary above uses CLOCK's reference projection when the mapping
    # is complete.  Keep the block table in that same domain so a consumer can
    # check one declared block p50 against one projected row; a partial mapping
    # falls back to the local window accounting that remains valid on its own.
    _domain, projections, complete = _comparison_projection(observations)

    def accounting_for(observation: Observation):
        if complete:
            return _observation_accounting(observation, projections)
        return observation.accounting

    usable = [obs for obs in observations if accounting_for(obs).available]
    denominators = [
        sum(
            accounting_for(obs).block_union_ns.get(block) or 0
            for block in EVENT_BLOCKS
        )
        for obs in usable
    ]
    denominator_ms_p50 = p50(_ms(value) for value in denominators)
    rows: list[dict] = []
    for block in ALL_BLOCKS:
        values = [
            _ms(accounting_for(obs).block_union_ns.get(block))
            for obs in usable
            if accounting_for(obs).block_union_ns.get(block) is not None
        ]
        shares = [
            accounting_for(obs).block_share_pct.get(block)
            for obs in usable
            if accounting_for(obs).block_share_pct.get(block) is not None
        ]
        rows.append(
            {
                "block": block,
                "busy_union_ms_p50": p50(values),
                "share_of_busy_pct": p50(shares),
                "mapping_rule": MAPPING_RULES[block],
                "event_count": sum(
                    accounting_for(obs).block_event_count.get(block, 0) for obs in usable
                ),
                "share_denominator": "sum_of_attributed_block_unions",
                "share_denominator_ms_p50": denominator_ms_p50,
                "basis": (
                    "device uncovered = observed event span - device busy union"
                    if block == "Host_Gap"
                    else "per-block union; shares normalised over attributed block unions"
                ),
            }
        )
    return rows

def _by_step(observations: Sequence[Observation]) -> list[dict]:
    grouped: dict[int, list[Observation]] = {}
    for observation in observations:
        if observation.window.step is not None:
            grouped.setdefault(observation.window.step, []).append(observation)
    rows: list[dict] = []
    for step in sorted(grouped):
        aggregate = aggregate_observations(grouped[step])
        rows.append({"step": step, **aggregate})
    return rows

def _limitations_findings(limitations: Sequence[dict]) -> list[dict]:
    return [
        {
            "finding_type": "measurement_limitation",
            "severity": item.get("severity", "medium"),
            "confidence": "high",
            "summary": item.get("detail", ""),
            "evidence_ref": item.get("code", "limitation"),
            "limitation_code": item.get("code"),
        }
        for item in limitations
    ]

def _source_event_facts(source: SourceRef, observations: Sequence[Observation]) -> dict:
    """Project CLOCK's selected source and Event facts without re-discovery."""

    event_rows = [
        (observation, event)
        for observation in observations
        if observation.rank_id == source.rank_id
        for event in observation.events
    ]
    layouts: set[str] = set()
    source_ids: set[str] = set()
    capture_ids: set[str] = set()
    table_kinds: set[str] = set()
    source_kinds: set[str] = set()
    clock_map: dict[str, dict] = {}
    field_presence: dict[str, bool] = {}
    raw_samples: list[dict] = []
    raw_count = 0
    for observation, event in event_rows:
        locator = event.locator if isinstance(event.locator, dict) else {}
        layout = str(locator.get("layout") or "")
        if layout:
            layouts.add(layout)
        if event.source_id:
            source_ids.add(str(event.source_id))
        if event.capture_id:
            capture_ids.add(str(event.capture_id))
        if event.table_kind:
            table_kinds.add(str(event.table_kind))
        if event.source_kind:
            source_kinds.add(str(event.source_kind))
        clock_entry = event.clock.as_dict()
        clock_map[repr(sorted(clock_entry.items()))] = clock_entry
        for name, present in (event.field_presence or {}).items():
            field_presence[str(name)] = bool(field_presence.get(str(name))) or bool(present)
        tick_start = event.clock_start_tick
        tick_duration = event.clock_duration_tick
        tick_end = event.clock_end_tick
        if tick_start is not None or tick_duration is not None or tick_end is not None:
            raw_count += 1
            if len(raw_samples) < 8:
                raw_samples.append({
                    "step": observation.window.step,
                    "source_id": event.source_id,
                    "clock_domain": event.clock.domain,
                    "start_tick": tick_start,
                    "duration_tick": tick_duration,
                    "end_tick": tick_end,
                })
    stats = [observation.stats for observation in observations if observation.rank_id == source.rank_id]
    read_errors = {
        "bad_rows": sum(item.bad_rows for item in stats),
        "unresolved_string_ids": sum(item.unresolved_string_ids for item in stats),
        "rows_read": sum(item.rows_read for item in stats),
        "rows_selected": sum(item.rows_selected for item in stats),
        "query_errors": list(source.notes),
        "optional_missing": list(source.optional_missing),
    }
    clock_domains = sorted(clock_map.values(), key=lambda item: item.get("domain", ""))
    layout_values = sorted(layouts)
    source_kind_values = sorted(source_kinds) or [source.kind]
    return {
        "layout": layout_values[0] if len(layout_values) == 1 else (layout_values or None),
        "source_kind": (
            source_kind_values[0] if len(source_kind_values) == 1
            else source_kind_values
        ),
        "source_ids": sorted(source_ids),
        "capture_ids": sorted(capture_ids),
        "table_kinds": sorted(table_kinds),
        "clock": clock_domains[0] if len(clock_domains) == 1 else None,
        "clock_domains": clock_domains,
        "raw_ticks": {
            "retained_count": raw_count,
            "sample_count": len(raw_samples),
            "samples": raw_samples,
            "fields": ["clock_start_tick", "clock_duration_tick", "clock_end_tick"],
        },
        "field_presence": field_presence,
        "read_errors": read_errors,
    }

def build_report(
    *,
    sources: Sequence[SourceRef],
    observations: Sequence[Observation],
    requested_steps: Sequence[int],
    scene: dict[str, Any],
    scene_provided: bool,
    limitations: Sequence[dict],
    query_timings: Sequence[dict],
    elapsed_ms: float,
    schema_rows: Sequence[dict],
    output_path: str | None,
    top_n: int,
    group_by: str = "variant",
) -> dict:
    steps = sorted({int(step) for step in requested_steps})
    step_observations = [
        observation for observation in observations if observation.window.step is not None
    ]
    step_aggregate = aggregate_observations(step_observations) if steps else aggregate_observations([])
    step_cross = cross_rank_stats(step_observations) if steps else cross_rank_stats([])
    analysis_observations = step_observations if steps else list(observations)
    cross = cross_rank_stats(analysis_observations)
    source_by_rank = {source.rank_id: source for source in sources}
    source_facts = {
        source.rank_id: _source_event_facts(source, observations) for source in sources
    }
    step_accounting = {
        "steady_steps": steps,
        "observed_steps": step_aggregate["steady_steps"],
        "step_status": "explicit" if steps else "not_provided",
        "rank_scope": sorted({observation.rank_id for observation in observations}),
        "aggregation": "p50_over_step_rank_observations",
        "request_wall_ms_p50": step_aggregate["request_wall_ms_p50"],
        "observed_event_span_ms_p50": step_aggregate["wall_ms_p50"],
        "device_busy_union_ms_p50": step_aggregate["busy_union_ms_p50"],
        "device_activity_sum_ms_p50": step_aggregate["kernel_sum_ms_p50"],
        "exposed_comm_ms_p50": step_aggregate["exposed_comm_ms_p50"],
        "device_uncovered_ms_p50": step_aggregate["host_gap_ms_p50"],
        "total_cost_ms_p50": step_aggregate["total_cost_ms_p50"],
        "clipped_event_count": step_aggregate["clipped_event_count"],
        # Deprecated aliases.
        "wall_ms_p50": step_aggregate["wall_ms_p50"],
        "busy_union_ms_p50": step_aggregate["busy_union_ms_p50"],
        "kernel_sum_ms_p50": step_aggregate["kernel_sum_ms_p50"],
        "host_gap_ms_p50": step_aggregate["host_gap_ms_p50"],
        "underfeed_bubble_ratio": step_aggregate["underfeed_bubble_ratio_p50"],
        "aicpu_exposed_ratio": step_aggregate["aicpu_exposed_ratio_p50"],
        "coverage_ratio_p50": step_aggregate["coverage_ratio_p50"],
        "slowest_rank": step_cross["slowest_rank"],
        "by_step": _by_step(observations),
        "by_rank": step_cross["rank_summaries"] if steps else cross["rank_summaries"],
        "cross_rank": {
            "rank_count_with_data": step_cross["rank_count_with_data"] if steps else cross["rank_count_with_data"],
            "wall_skew_ms": step_cross["wall_skew_ms"] if steps else cross["wall_skew_ms"],
            "wall_ratio": step_cross["wall_ratio"] if steps else cross["wall_ratio"],
            "clock_union_span": (
                step_cross["cross_rank_union_span"] if steps
                else cross["cross_rank_union_span"]
            ),
            "straggler_and_link_attribution": (
                step_cross["straggler_and_link_attribution"] if steps
                else cross["straggler_and_link_attribution"]
            ),
        },
    }
    report = {
        "schema_version": REPORT_SCHEMA,
        "source_identity": {
            "source_kind": _source_kind(sources),
            "db_files_sha256": _source_sha_map(sources, "db"),
            "csv_files_sha256": _source_sha_map(sources, "csv"),
            "exporter_schema_version": _schema_version(sources),
            "parser_version": PARSER_VERSION,
            "query_elapsed_ms": round(float(elapsed_ms), 6),
            "timing_scope": "schema probe + bounded explicit-window reads (plus sha256 only with --hash); capture, export, and first cold full-table scan are excluded",
            "cache_state": "path_size_mtime",
            "cache_scope": "content sha256 is opt-in (--hash); the default identity is path+size_bytes+mtime_ns+schema_version",
            "query_timings": list(query_timings),
            "sources": [
                {
                    "rank_id": source.rank_id,
                    "kind": source.kind,
                    "basename": source.basename,
                    "path": source.path,
                    "sha256": source.sha256,
                    "size_bytes": source.size_bytes,
                    "mtime_ns": source.mtime_ns,
                    "schema_version": source.schema_version,
                    "schema_variant": source.schema_variant,
                    "header_sha256": source.header_sha256,
                    "optional_missing": list(source.optional_missing),
                    "notes": list(source.notes),
                    "content_identity": source.content_identity(),
                    **source_facts[source.rank_id],
                    "csv_candidates": getattr(source, "csv_candidates", None),
                    "selected_csv": getattr(source, "selected_csv", None),
                    "csv_selection_status": getattr(source, "csv_selection_status", None),
                    "candidate_evidence": (
                        "available" if getattr(source, "csv_candidates", None) is not None
                        else "unavailable_from_analyze_source_ref"
                    ),
                }
                for source in sources
            ],
            "source_fingerprints": {
                source.rank_id: source.content_identity() for source in sources
            },
            "source_inventory": {
                "rank_count": len(sources),
                "capture_count": len({
                    capture
                    for facts in source_facts.values()
                    for capture in facts.get("capture_ids", [])
                }),
                "capture_ids": sorted({
                    capture
                    for facts in source_facts.values()
                    for capture in facts.get("capture_ids", [])
                }),
                "rank_sources": [
                    {
                        "rank_id": source.rank_id,
                        "kind": source.kind,
                        "selected_path": source.path,
                        "layout": source_facts[source.rank_id].get("layout"),
                        "source_ids": source_facts[source.rank_id].get("source_ids", []),
                        "capture_ids": source_facts[source.rank_id].get("capture_ids", []),
                        "table_kinds": source_facts[source.rank_id].get("table_kinds", []),
                        "clock_domains": source_facts[source.rank_id].get("clock_domains", []),
                        "read_errors": source_facts[source.rank_id].get("read_errors", {}),
                        "csv_candidates": getattr(source, "csv_candidates", None),
                        "selected_csv": getattr(source, "selected_csv", None),
                        "csv_selection_status": getattr(source, "csv_selection_status", None),
                        "candidate_evidence": (
                            "available" if getattr(source, "csv_candidates", None) is not None
                            else "unavailable_from_analyze_source_ref"
                        ),
                    }
                    for source in sources
                ],
                "candidate_projection_blocker": (
                    "analyze_profile currently passes selected SourceRef facts only; "
                    "full RankSource csv_candidates/selected_csv/csv_selection_status "
                    "must be carried by a narrow analyze/CLOCK sidecar"
                ),
            },
            "schema": list(schema_rows),
        },
        "scene": {
            "framework": None,
            "phase": None,
            "tp": None,
            "dp": None,
            "graph_mode": None,
            **(scene or {}),
            "clock_domain": (scene or {}).get("clock_domain") or "unknown",
            "scene_source": "provided" if scene_provided else "not_provided",
        },
        "step_accounting": step_accounting,
        "semantic_block_breakdown": _block_breakdown(analysis_observations),
        "top_hotspot_kernels": _hotspots(
            analysis_observations, source_by_rank, top_n, group_by=group_by
        ),
        "hotspot_grouping": group_by,
        "window_accounting": _window_accounting(observations),
        "findings": _limitations_findings(limitations),
        "limitations": list(limitations),
        "metric_definitions": _metric_definitions(),
        "time_origin_policy": (
            "window_accounting.window_start_us/window_end_us are relative to window_origin_ns; "
            "exact integer nanosecond bounds are window_start_ns/window_end_ns"
        ),
        "artifacts": {
            "report_json": output_path,
            "report_md": None,
            "report_html_v2": None,
            "remote_output_dir": str(Path(output_path).resolve().parent) if output_path else None,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return report

def write_report(report: dict, output_path: str | Path) -> Path:
    """Atomically write the C7 JSON; no partial file is left on failure."""

    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, destination)
    except TimeoutError:
        raise
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return destination
