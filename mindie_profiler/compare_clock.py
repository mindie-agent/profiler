"""Explicit-workload A/B C7 profile comparison and provenance verification (compare_clock).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting explicit-workload a/b c7 profile comparison and provenance verification.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

import hashlib
import json
from statistics import median
from typing import Any, Iterable, Mapping, Sequence
from .classify import EVENT_BLOCKS
from .compare_metric import metric as _metric, num as _num

SUMMARY_SCHEMA = "mindie-profile-summary/1"

COMPARISON_SCHEMA = "mindie-profile-comparison/1"

_ROW_METRICS = {
    "observed_event_span_ms_p50": "observed_event_span_ms",
    "device_busy_union_ms_p50": "device_busy_union_ms",
    "device_activity_sum_ms_p50": "device_activity_sum_ms",
    "exposed_comm_ms_p50": "exposed_comm_ms",
    "device_uncovered_ms_p50": "device_uncovered_ms",
    "total_cost_ms_p50": "total_cost_ms",
    # Deprecated aliases remain comparable for older C7 reports.
    "wall_ms_p50": "wall_ms",
    "busy_union_ms_p50": "busy_union_ms",
    "kernel_sum_ms_p50": "kernel_sum_ms",
    "host_gap_ms_p50": "host_gap_ms",
}

_RATIO_METRICS = ("underfeed_bubble_ratio", "aicpu_exposed_ratio")

_BLOCK_ORDER = ("Attention", "MoE", "Comm", "Norm", "Copy_Layout", "Unclassified", "Host_Gap")

_REQUIRED_SCENE = ("framework", "phase")

_OPTIONAL_SCENE = ("tp", "dp", "graph_mode")

_CLOCK_COVERAGE_FIELDS = (
    "mapped_event_count",
    "mapped_endpoint_count",
    "total_endpoint_count",
    "mapped_window_endpoint_count",
)

_P50_REL_TOL = 1e-6

def _int(value: Any) -> int | None:
    return int(value) if isinstance(value, int) and not isinstance(value, bool) else None

def _lim(code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"code": code, "message": message, **{k: v for k, v in extra.items() if v is not None}}

def _dedupe(items: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("code"), item.get("source"), item.get("field"), repr(item.get("details")))
        if key not in seen:
            seen.add(key)
            out.append(dict(item))
    return out

def _p50_provenance(declared: Any, values: list[float], *, basis: str) -> dict[str, Any]:
    """Retain both a declared p50 and the median of its own raw rows."""

    recomputed = round(float(median(values)), 6) if values else None
    declared_number = _num(declared)
    declared_invalid = declared is not None and declared_number is None
    consistent: bool | None = None
    if declared_number is not None and recomputed is not None:
        allowed = max(
            _P50_REL_TOL,
            _P50_REL_TOL * max(abs(declared_number), abs(recomputed)),
        )
        consistent = abs(declared_number - recomputed) <= allowed
    return {
        "comparison_basis": basis,
        "declared_p50": declared_number,
        "declared_value": declared,
        "declared_numeric": declared_number is not None,
        "declared_invalid": declared_invalid,
        "recomputed_from_window_accounting": recomputed,
        "aligned_observation_count": len(values),
        "declared_used": basis == "declared_p50",
        "declared_consistent": consistent,
    }

def _declared_mismatch(provenance: Mapping[str, Any]) -> bool:
    return provenance.get("declared_used") is True and provenance.get("declared_consistent") is False

def _declared_invalid(provenance: Mapping[str, Any]) -> bool:
    return provenance.get("declared_used") is True and provenance.get("declared_invalid") is True

def _clear_derived(entry: dict[str, Any]) -> None:
    for name in ("delta", "delta_ms", "relative_delta_pct", "direction", "delta_pp"):
        if name in entry:
            entry[name] = None

def _clock_evidence(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Read sourced clock domains already retained in ``step_accounting.by_rank``."""

    accounting = summary.get("step_accounting")
    rows = accounting.get("by_rank") if isinstance(accounting, Mapping) else None
    domains: set[str] = set()
    references: set[str] = set()
    per_rank: list[dict[str, Any]] = []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, Mapping):
                continue
            row_domains = sorted(
                str(item) for item in row.get("clock_domains", ())
                if isinstance(item, str) and item
            ) if isinstance(row.get("clock_domains"), list) else []
            row_references = sorted(
                str(item) for item in row.get("clock_reference_domains", ())
                if isinstance(item, str) and item
            ) if isinstance(row.get("clock_reference_domains"), list) else []
            domains.update(row_domains)
            references.update(row_references)
            per_rank.append({
                "rank_id": row.get("rank_id"),
                "domains": row_domains,
                "reference_domains": row_references,
            })
    return {
        "available": bool(domains),
        "domains": sorted(domains),
        "reference_domains": sorted(references),
        "ranks": per_rank,
        "source": "step_accounting.by_rank clock_domains/clock_reference_domains",
    }

def _cross_rank_projection(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Pass through CLOCK's own union-span and attribution evidence."""

    accounting = summary.get("step_accounting")
    cross = accounting.get("cross_rank") if isinstance(accounting, Mapping) else None
    if not isinstance(cross, Mapping):
        return {"clock_union_span": None, "straggler_and_link_attribution": None}
    return {
        "clock_union_span": cross.get("clock_union_span"),
        "straggler_and_link_attribution": cross.get("straggler_and_link_attribution"),
    }

def _clock_coverage_evidence(
    rows: Mapping[tuple[int, str], Mapping[str, Any]],
    keys: Iterable[tuple[int, str]],
    label: str,
) -> dict[str, Any]:
    """Aggregate per-window CLOCK endpoint coverage over fixed comparison keys."""

    records: list[dict[str, Any]] = []
    for key in keys:
        coverage = rows[key].get("clock_coverage")
        if not isinstance(coverage, Mapping):
            records.append({
                "step": key[0], "rank_id": key[1],
                "status": "clock_coverage_evidence_absent",
                "reason": "clock_coverage_evidence_absent",
                "event_count": 0,
                "comparable_event_count": 0,
                "mapped_event_count": None,
                "mapped_endpoint_count": None,
                "total_endpoint_count": None,
                "mapped_window_endpoint_count": None,
                "domains": [],
                "reference_domains": [],
                "gaps": [{
                    "code": "clock_coverage_evidence_absent",
                    "scope": "window",
                    "detail": "window_accounting row carries no clock_coverage object",
                }],
            })
            continue
        rows_cov = coverage.get("rows")
        if isinstance(rows_cov, list) and rows_cov:
            # A report may aggregate several source rows under one window.
            sources = [item for item in rows_cov if isinstance(item, Mapping)]
        else:
            sources = [coverage]
        event_count = sum(_int(item.get("event_count")) or 0 for item in sources)
        comparable = sum(
            _int(item.get("comparable_event_count")) or 0 for item in sources
        )
        gaps: list[dict[str, Any]] = []
        domains: set[str] = set()
        refs: set[str] = set()
        known: dict[str, list[int | None]] = {
            field: [] for field in _CLOCK_COVERAGE_FIELDS
        }
        for index, item in enumerate(sources):
            for gap in (item.get("gaps") or ()):
                if isinstance(gap, Mapping):
                    gaps.append(dict(gap))
            raw_domains = item.get("domains")
            if isinstance(raw_domains, list):
                domains.update(str(domain) for domain in raw_domains if domain)
            raw_refs = item.get("reference_domains")
            if isinstance(raw_refs, list):
                refs.update(str(ref) for ref in raw_refs if ref)
            elif item.get("reference_domain"):
                refs.add(str(item["reference_domain"]))
            values = {
                field: _int(item.get(field)) for field in _CLOCK_COVERAGE_FIELDS
            }
            for field in _CLOCK_COVERAGE_FIELDS:
                known[field].append(values[field])
            missing = [
                field for field in _CLOCK_COVERAGE_FIELDS
                if values[field] is None
            ]
            if missing:
                # The declared relation/comparable count is retained above, but
                # it is not endpoint proof.  Ask for a named gap instead of
                # reconstructing a mapping from the old count.
                gaps.append({
                    "code": "clock_coverage_evidence_absent",
                    "scope": "row" if len(sources) > 1 else "window",
                    "row_index": index,
                    "missing_fields": missing,
                })
        complete = all(
            all(value is not None for value in known[field])
            for field in _CLOCK_COVERAGE_FIELDS
        )
        if complete:
            mapped_events = sum(known["mapped_event_count"])  # type: ignore[arg-type]
            mapped_endpoints = sum(known["mapped_endpoint_count"])  # type: ignore[arg-type]
            total_endpoints = sum(known["total_endpoint_count"])  # type: ignore[arg-type]
            mapped_window = sum(known["mapped_window_endpoint_count"])  # type: ignore[arg-type]
        else:
            mapped_events = None
            mapped_endpoints = None
            total_endpoints = None
            mapped_window = None
        status = str(coverage.get("status") or "")
        reason = coverage.get("reason")
        if not complete:
            status = "clock_coverage_evidence_absent"
            reason = "clock_coverage_evidence_absent"
        unique_gaps: list[dict[str, Any]] = []
        seen_gaps: set[str] = set()
        for gap in gaps:
            marker = json.dumps(gap, sort_keys=True, default=str)
            if marker not in seen_gaps:
                seen_gaps.add(marker)
                unique_gaps.append(gap)
        records.append({
            "step": key[0],
            "rank_id": key[1],
            "status": status,
            "reason": reason,
            "event_count": event_count,
            "comparable_event_count": comparable,
            "mapped_event_count": mapped_events,
            "mapped_endpoint_count": mapped_endpoints,
            "total_endpoint_count": total_endpoints,
            "mapped_window_endpoint_count": mapped_window,
            "domains": sorted(domains),
            "reference_domains": sorted(refs),
            "gaps": unique_gaps,
        })
    statuses = {item.get("status") for item in records}
    event_total = sum(item.get("event_count") or 0 for item in records)
    comparable_total = sum(item.get("comparable_event_count") or 0 for item in records)

    def _known_total(field: str) -> int | None:
        values = [item.get(field) for item in records]
        if any(value is None for value in values):
            return None
        return sum(int(value) for value in values)

    mapped_event_total = _known_total("mapped_event_count")
    mapped_endpoint_total = _known_total("mapped_endpoint_count")
    total_endpoint_total = _known_total("total_endpoint_count")
    mapped_window_total = _known_total("mapped_window_endpoint_count")
    all_refs = sorted({
        ref for item in records for ref in (item.get("reference_domains") or ())
    })
    all_domains = sorted({
        domain for item in records for domain in (item.get("domains") or ())
    })
    all_gaps = [gap for item in records for gap in (item.get("gaps") or ())]
    reason = ""
    if not records:
        reason = "no_aligned_window_rows"
    elif any(item.get("status") == "clock_coverage_evidence_absent" for item in records):
        reason = "clock_coverage_evidence_absent"
    elif event_total <= 0 or any((item.get("event_count") or 0) <= 0 for item in records):
        reason = "clock_coverage_no_events"
    elif (
        mapped_event_total is None
        or mapped_event_total != event_total
        or any(item.get("mapped_event_count") != (item.get("event_count") or 0)
               for item in records)
        or mapped_window_total != 2 * len(records)
        or (total_endpoint_total is not None
            and mapped_endpoint_total != total_endpoint_total)
    ):
        reason = "clock_coverage_incomplete"
    elif any(item.get("status") not in {"available"} for item in records):
        reason = "clock_coverage_incomplete"
    elif "unknown" in all_domains:
        reason = "clock_coverage_unknown_domain"
    elif len(all_refs) != 1:
        reason = "clock_reference_domain_missing_or_ambiguous"
    return {
        "label": label,
        "available": not reason,
        "reason": reason or None,
        "reference_domain": all_refs[0] if len(all_refs) == 1 and not reason else None,
        "event_count": event_total,
        "comparable_event_count": comparable_total,
        "mapped_event_count": mapped_event_total,
        "unmapped_event_count": (
            event_total - mapped_event_total if mapped_event_total is not None else None
        ),
        "mapped_endpoint_count": mapped_endpoint_total,
        "total_endpoint_count": total_endpoint_total,
        "mapped_window_endpoint_count": mapped_window_total,
        "domains": all_domains,
        "reference_domains": all_refs,
        "gaps": all_gaps,
        "rows": records,
    }

def _canon(value: Any) -> str | None:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError):
        return None

def _hash(value: Any) -> str | None:
    text = _canon(value)
    return hashlib.sha256(text.encode()).hexdigest() if text is not None else None

def _schema_bad(summary: Any, label: str) -> dict[str, Any] | None:
    if not isinstance(summary, Mapping):
        return _lim("summary_not_an_object", f"{label} summary is not an object", source=label)
    if summary.get("schema_version") != SUMMARY_SCHEMA:
        return _lim(
            "unsupported_schema_version",
            f"{label} schema_version is not {SUMMARY_SCHEMA}",
            source=label,
            field="schema_version",
            details={"expected": SUMMARY_SCHEMA, "actual": summary.get("schema_version")},
        )
    return None

def _scene(summary: Mapping[str, Any]) -> Mapping[str, Any]:
    value = summary.get("scene")
    return value if isinstance(value, Mapping) else {}

def _input_identity(summary: Mapping[str, Any]) -> Any:
    value = _scene(summary).get("input_signature")
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() and value.strip().lower() != "unknown" else None
    if isinstance(value, (Mapping, list, tuple, set)):
        return value if value else None
    return value

def _rank_scope(summary: Mapping[str, Any]) -> tuple[list[str] | None, dict[str, Any] | None]:
    accounting = summary.get("step_accounting")
    raw = accounting.get("rank_scope") if isinstance(accounting, Mapping) else None
    if not isinstance(raw, list) or not raw or any(
        not isinstance(item, str) or not item for item in raw
    ):
        return None, _lim("rank_scope_unavailable", "step_accounting.rank_scope must be a non-empty string list")
    return sorted(set(raw)), None

def _steady_steps(summary: Mapping[str, Any]) -> tuple[list[int] | None, dict[str, Any] | None]:
    accounting = summary.get("step_accounting")
    raw = accounting.get("steady_steps") if isinstance(accounting, Mapping) else None
    if not isinstance(raw, list) or not raw or any(_int(item) is None for item in raw):
        return None, _lim("steady_steps_unavailable", "step_accounting.steady_steps must be a non-empty integer list")
    return sorted(set(_int(item) for item in raw)), None

def _window_rows(summary: Mapping[str, Any]) -> tuple[dict[tuple[int, str], Mapping[str, Any]] | None, list[dict[str, Any]]]:
    raw = summary.get("window_accounting")
    if not isinstance(raw, list):
        return None, [_lim("window_accounting_missing", "window_accounting must be a list")]
    rows: dict[tuple[int, str], Mapping[str, Any]] = {}
    limits: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            limits.append(_lim("window_row_invalid", "window_accounting contains a non-object row"))
            continue
        step = _int(item.get("step"))
        rank_id = item.get("rank_id")
        if step is None:
            continue
        if not isinstance(rank_id, str) or not rank_id:
            limits.append(_lim("window_row_rank_invalid", "window row has no rank_id"))
            continue
        key = (step, rank_id)
        if key in rows:
            limits.append(_lim("window_row_duplicate", f"duplicate window row {key!r}",
                               details={"step": step, "rank_id": rank_id}))
            continue
        rows[key] = item
    return rows, limits

def _block_declared(summary: Mapping[str, Any]) -> tuple[dict[str, Mapping[str, Any]], list[dict[str, Any]]]:
    raw = summary.get("semantic_block_breakdown")
    if not isinstance(raw, list):
        return {}, [_lim("semantic_block_breakdown_missing", "semantic_block_breakdown is not a list")]
    result: dict[str, Mapping[str, Any]] = {}
    limits: list[dict[str, Any]] = []
    for item in raw:
        name = item.get("block") if isinstance(item, Mapping) else None
        if not isinstance(name, str) or not name:
            limits.append(_lim("semantic_block_name_missing", "semantic block has no name"))
        elif name in result:
            limits.append(_lim("semantic_block_duplicate", f"{name} appears twice"))
        else:
            result[name] = item
    return result, limits

def _source_content(summary: Mapping[str, Any]) -> dict[str, Any] | None:
    identity = summary.get("source_identity")
    if not isinstance(identity, Mapping):
        return None
    content: dict[str, Any] = {}
    for key in ("db_files_sha256", "csv_files_sha256"):
        value = identity.get(key)
        if isinstance(value, Mapping) and value:
            content[key] = dict(value)
    sources = identity.get("sources")
    if isinstance(sources, list):
        hashes = {
            item["rank_id"]: item["sha256"]
            for item in sources
            if isinstance(item, Mapping)
            and isinstance(item.get("rank_id"), str)
            and isinstance(item.get("sha256"), str)
        }
        if hashes:
            content["sources_sha256"] = hashes
    fingerprints = identity.get("source_fingerprints")
    if isinstance(fingerprints, Mapping) and fingerprints:
        content["source_fingerprints"] = dict(fingerprints)
    return content or None

def _structure_parts(summary: Mapping[str, Any]) -> tuple[Any, list[Mapping[str, Any]] | None]:
    container = summary.get("structure")
    if not isinstance(container, Mapping):
        return None, None
    shape = container.get("event_sequence_shape")
    raw_layers = container.get("layers")
    layers = [item for item in raw_layers if isinstance(item, Mapping)] if isinstance(raw_layers, list) else None
    return shape, layers

def _layer_identity(layer: Mapping[str, Any]) -> tuple[str | None, int | None, str | None]:
    layer_id = layer.get("layer_id")
    ordinal = _int(layer.get("ordinal"))
    name = layer.get("name") if isinstance(layer.get("name"), str) else None
    return (layer_id if isinstance(layer_id, str) and layer_id else None, ordinal, name)

def _layer_ids(layers: list[Mapping[str, Any]]) -> tuple[list[tuple[str, int]] | None, list[str]]:
    ids: list[tuple[str, int]] = []
    names: list[str] = []
    for layer in layers:
        layer_id, ordinal, name = _layer_identity(layer)
        if layer_id is None or ordinal is None:
            names.append(name or "<unnamed>")
            continue
        ids.append((layer_id, ordinal))
        names.append(name or layer_id)
    if len(ids) != len(layers):
        return None, names
    return ids, names

def _structural_reuse(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    b_shape, b_layers = _structure_parts(baseline)
    c_shape, c_layers = _structure_parts(candidate)
    result: dict[str, Any] = {
        "status": "not_available",
        "allowed": False,
        "reason_codes": [],
        "baseline_source_content": _source_content(baseline),
        "candidate_source_content": _source_content(candidate),
        "event_sequence_shape": {"baseline_sha256": _hash(b_shape) if b_shape is not None else None,
                                 "candidate_sha256": _hash(c_shape) if c_shape is not None else None},
    }
    b_ids = _layer_ids(b_layers)[0] if b_layers is not None else None
    c_ids = _layer_ids(c_layers)[0] if c_layers is not None else None
    if b_shape is None and c_shape is None and b_ids is None and c_ids is None:
        result["reason_codes"] = ["structure_evidence_unavailable"]
        return result
    reasons: list[str] = []
    if b_shape is None or c_shape is None:
        reasons.append("event_sequence_shape_unavailable")
    elif _hash(b_shape) != _hash(c_shape):
        reasons.append("event_sequence_shape_mismatch")
    if b_ids is None or c_ids is None or not b_ids or not c_ids:
        reasons.append("layer_identity_unavailable")
    elif sorted(b_ids) != sorted(c_ids):
        reasons.append("layer_identity_mismatch")
    result["reason_codes"] = reasons
    result["status"] = "rejected" if reasons else "verified"
    result["allowed"] = not reasons
    return result

_COMPARISON_FIELD_ALIASES = {
    "wall_ms": "comparison_observed_event_span_ms",
    "busy_union_ms": "comparison_device_busy_union_ms",
    "kernel_sum_ms": "comparison_device_activity_sum_ms",
    "host_gap_ms": "comparison_device_uncovered_ms",
}

def _comparison_field(field: str) -> str:
    return _COMPARISON_FIELD_ALIASES.get(field, f"comparison_{field}")

def _row_comparison_value(row: Mapping[str, Any], field: str) -> float | None:
    projected = _comparison_field(field)
    if row.get("comparison_complete") is True and projected in row:
        return _num(row.get(projected))
    return None

def _row_value(row: Mapping[str, Any], field: str) -> float | None:
    projected = _row_comparison_value(row, field)
    return projected if projected is not None else _num(row.get(field))

def _row_map(row: Mapping[str, Any], field: str) -> Mapping[str, Any] | None:
    projected = _comparison_field(field)
    if row.get("comparison_complete") is True and isinstance(row.get(projected), Mapping):
        return row.get(projected)
    value = row.get(field)
    return value if isinstance(value, Mapping) else None

def _column_values(rows: Mapping[tuple[int, str], Mapping[str, Any]],
                   keys: Iterable[tuple[int, str]], field: str) -> tuple[list[float], list[tuple[int, str]]]:
    values: list[float] = []
    missing: list[tuple[int, str]] = []
    for key in keys:
        value = _row_value(rows[key], field)
        if value is None:
            missing.append(key)
        else:
            values.append(value)
    return values, missing

def _block_row_evidence(row: Mapping[str, Any]) -> dict[str, Any]:
    """One row's complete attributed-block union and share evidence.

    Every EVENT_BLOCK must be present and numeric.  An explicit zero is a
    value; a missing or non-numeric component is a named gap and never becomes
    zero.  The denominator is the sum of all six attributed block unions.
    """

    block_map = _row_map(row, "block_union_ms")
    values: dict[str, float] = {}
    missing: list[str] = []
    invalid: list[str] = []
    for block in EVENT_BLOCKS:
        if not isinstance(block_map, Mapping) or block not in block_map:
            missing.append(block)
            continue
        value = _num(block_map.get(block))
        if value is None:
            invalid.append(block)
        else:
            values[block] = value
    complete = not missing and not invalid
    denominator = sum(values.values()) if complete else None
    shares = {
        block: (value / denominator * 100.0 if denominator not in (None, 0) else None)
        for block, value in values.items()
    } if complete else {}
    recorded_map = _row_map(row, "block_share_pct")
    recorded: dict[str, float | None] = {}
    if isinstance(recorded_map, Mapping):
        for block in EVENT_BLOCKS:
            recorded[block] = _num(recorded_map.get(block))
    return {
        "complete": complete,
        "missing_blocks": missing,
        "invalid_blocks": invalid,
        "denominator": denominator,
        "shares": shares,
        "recorded_shares": recorded,
        "values": values,
    }
