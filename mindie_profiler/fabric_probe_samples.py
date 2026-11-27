"""Bounded JSON and JSONL fabric sample ingestion.

[Role]
  Preserve raw per-rank evidence while normalizing caller container carriers.
[Invariants]
  One bounded recursive snapshot precedes sample projection. Nested Mapping
  values and tuple arrays retain their metadata without caller mutation.
  Explicit terminal failure evidence dominates numeric measurement fields.
[Timeouts & Locks]
  Pure bounded container work; caller TimeoutError instances pass through.
[Side-Effect Policy]
  No I/O, subprocesses, hardware access or global limit changes.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .events import ProfilerUsageError
from .repro_values import (
    bounded_count, bounded_sequence, bounded_summary, decode_bounded_json,
    diagnostic_value,
)

_PRESETS_DOC = json.loads(
    (Path(__file__).resolve().parent / "knowledge" / "fabric_probe_presets.json").read_text(encoding="utf-8")
)
_SAMPLE_CFG = _PRESETS_DOC["sample_bounds"]
_US_PER_MS = float(_PRESETS_DOC["fit_bounds"]["ns_per_us"])
_MAX_REPEAT = int(_SAMPLE_CFG["max_repeat_index"])
_MAX_RANKS = int(_SAMPLE_CFG["max_ranks"])
_MAX_RANK_IDX = int(_SAMPLE_CFG["max_rank_index"])
_MAX_BYTES = 1 << int(_SAMPLE_CFG["max_bytes_shift"])

_RUN_FAILURE_STATUS = frozenset({"deadline_exceeded", "peer_aborted",
                                 "aborted", "abort", "cleanup_failed",
                                 "failed", "error", "partial"})
_CONTROL_KINDS = frozenset({"cleanup_failed", "abort", "deadline_exceeded",
                            "run_status", "error", "control", "failed"})

def _terminal_evidence(record: Mapping[str, Any]) -> bool:
    """Whole-run failure/control markers that override numeric fields.
    A terminal record may retain the previous measurement's ``bytes``,
    ``latency_us`` and even ``validated=True``.  The explicit failure/control
    evidence must be classified before any numeric sample projection.
    """
    kind = diagnostic_value(record.get("kind"))
    status = diagnostic_value(record.get("status"))
    return bool(
        (isinstance(kind, str) and kind in _CONTROL_KINDS)
        or record.get("cleanup_failed") is True
        or record.get("final_failure")
        or record.get("error")
        or record.get("aborted") is True
        or (isinstance(status, str) and status in _RUN_FAILURE_STATUS)
        or record.get("disqualified_reason"))

_CAMPAIGN_SCHEMA = "mindie-bench-campaign/1"
_OBS_V2_SCHEMA = "mindie-bench-observation/2"
_SKIP_OBS_RECORD_TYPES = frozenset({"case_complete", "case_outcome"})
_OK_OBS_STATUSES = frozenset({"ok", "completed", "passed", "success", "measured"})


def _project_campaign_case(entry: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project one ``mindie-bench-campaign/1`` case into fabric sample record(s)."""
    actual = entry.get("actual_executed_shape") if isinstance(entry.get("actual_executed_shape"), Mapping) else {}
    nbytes = entry.get("bytes")
    if nbytes is None:
        nbytes = entry.get("work_bytes") if entry.get("work_bytes") is not None else actual.get("bytes")
    p50_us = entry.get("p50_us")
    ranks = entry.get("group_ranks") or entry.get("participating_ranks")
    group_size = entry.get("group_size") or (len(ranks) if isinstance(ranks, (list, tuple)) and ranks else None)
    timing_mode = str(entry.get("timing_mode") or "eager")
    is_qualified = entry.get("qualified")
    device_us = (
        p50_us
        if is_qualified is not False
        and timing_mode != "host_fallback"
        and entry.get("timer_source") != "perf_counter_host_fallback"
        else None
    )
    base = {
        **dict(entry),
        "bytes": nbytes,
        "latency_us": p50_us,
        "device_completion_us": device_us,
        "tier": entry.get("tier") or entry.get("route") or "unidentified",
        "op": entry.get("op") or entry.get("bench_builder") or "unknown",
        "group_ranks": list(ranks) if isinstance(ranks, (list, tuple)) else None,
        "group_size": group_size,
        "run_id": entry.get("measured_in_run_id") or entry.get("run_id"),
        "repeat_index": 0,
        "timing_mode": "host_fallback" if device_us is None and p50_us is not None and is_qualified is not False else timing_mode,
        "saturated_qualified": bool(is_qualified) if timing_mode == "stream_saturated" else None,
        "qualified": is_qualified,
    }
    rank_map = entry.get("rank_latencies_us")
    if isinstance(rank_map, Mapping) and rank_map:
        expanded: list[dict[str, Any]] = []
        for rk_raw, lat_raw in sorted(rank_map.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else str(kv[0])):
            try:
                rk = int(rk_raw)
            except (TypeError, ValueError):
                continue
            lat = _num(lat_raw)
            expanded.append({
                **base,
                "rank": rk,
                "latency_us": lat if lat is not None else p50_us,
                "device_completion_us": (lat if lat is not None else device_us) if device_us is not None else None,
            })
        if expanded:
            return expanded
    return [base]


def _normalize_v2_observation_item(item: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Fill fabric fields from ``mindie-bench-observation/2`` columns and expand rank maps."""
    if item.get("schema") != _OBS_V2_SCHEMA:
        return [item]
    out = dict(item)
    actual = out.get("actual_executed_shape") if isinstance(out.get("actual_executed_shape"), Mapping) else {}
    ident = out.get("identity") if isinstance(out.get("identity"), Mapping) else {}
    ident_shape = ident.get("shape") if isinstance(ident.get("shape"), Mapping) else {}
    if out.get("bytes") is None:
        candidate = out.get("work_bytes")
        if candidate is None:
            candidate = actual.get("bytes") if actual.get("bytes") is not None else ident_shape.get("bytes")
        if candidate is not None:
            out["bytes"] = candidate
    if out.get("latency_us") is None and out.get("duration_ms") is not None:
        dur_ms = _num(out.get("duration_ms"))
        if dur_ms is not None and dur_ms > 0:
            out["latency_us"] = dur_ms * _US_PER_MS
            if (
                out.get("device_completion_us") is None
                and out.get("timing_mode") != "host_fallback"
                and out.get("qualified") is not False
            ):
                out["device_completion_us"] = out["latency_us"]
    if out.get("qualified") is False:
        out["device_completion_us"] = None
    if not out.get("tier") and out.get("route"):
        out["tier"] = out["route"]
    if not out.get("op"):
        out["op"] = out.get("bench_builder") or ident.get("implementation") or "unknown"
    rank_map = out.get("rank_latencies_us")
    if isinstance(rank_map, Mapping) and rank_map:
        expanded: list[Mapping[str, Any]] = []
        has_dev = out.get("device_completion_us") is not None and out.get("qualified") is not False
        for rk_raw, lat_raw in sorted(rank_map.items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else str(kv[0])):
            try:
                rk = int(rk_raw)
            except (TypeError, ValueError):
                continue
            lat = _num(lat_raw)
            row_out = dict(out)
            row_out.pop("rank_latencies_us", None)
            row_out["rank"] = rk
            if lat is not None:
                row_out["latency_us"] = lat
                if has_dev:
                    row_out["device_completion_us"] = lat
            expanded.append(row_out)
        if expanded:
            return expanded
    return [out]


def _document_items(document: Any) -> list[Any]:
    """Flatten one JSON document while preserving outer control evidence."""
    if isinstance(document, Mapping):
        if document.get("schema") == _CAMPAIGN_SCHEMA and isinstance(document.get("cases"), (list, tuple)):
            items: list[Any] = []
            for entry in document["cases"]:
                if isinstance(entry, Mapping):
                    items.extend(_project_campaign_case(entry))
            for fail_key in ("blocked_cases", "failed_cases", "worker_diagnostics"):
                for entry in document.get(fail_key) or ():
                    if isinstance(entry, Mapping):
                        status = str(entry.get("status") or "failed")
                        items.append({
                            **dict(entry),
                            "status": status,
                            "validated": False,
                            "disqualified_reason": str(entry.get("reason") or status),
                            "_control_record": True,
                        })
            return items
        if "samples" not in document:
            return [document]
        samples = document.get("samples")
        if isinstance(samples, (list, tuple)):
            items = list(bounded_sequence(samples, "samples", 100_000))
        elif isinstance(samples, Mapping):
            items = [samples]
        else:
            items = []
        outer = {key: value for key, value in document.items()
                 if key != "samples"}
        if outer and _terminal_evidence(outer):
            items.insert(0, {**outer, "_control_record": True,
                             "_wrapper_control": True})
        return items
    if isinstance(document, (list, tuple)):
        bounded_sequence(document, "sample document", 100_000)
        items: list[Any] = []
        for entry in document:
            items.extend(_document_items(entry))
            bounded_count(len(items), "sample document items", 0, 100_000)
        return items
    return []

def _num(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not -1e12 <= value <= 1e12:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None

def parse_fabric_probe_samples(
    payload: str | bytes | Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Parse JSON/JSONL records, preserving rank/tier/op/regime evidence."""
    payload = bounded_sequence([payload], "sample input")[0]
    if isinstance(payload, Mapping):
        raw = _document_items(payload)
    elif isinstance(payload, (list, tuple)):
        bounded_sequence(payload, "samples", 100_000)
        raw = []
        for item in payload:
            raw.extend(_document_items(item))
    else:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        text = text.strip()
        if not text:
            raise ProfilerUsageError("fabric probe output is empty")
        try:
            parsed = decode_bounded_json(text)
        except ValueError:
            raw = []
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    item = decode_bounded_json(line)
                except ValueError as exc:
                    raise ProfilerUsageError("invalid fabric probe line: " + bounded_summary(str(exc))) from exc
                raw.extend(_document_items(item))
        else:
            raw = _document_items(parsed)
    bounded_count(len(raw), "sample records", 0, 100_000)
    expanded_raw: list[Mapping[str, Any]] = []
    for raw_item in raw:
        if not isinstance(raw_item, Mapping):
            continue
        rec_type = raw_item.get("record_type")
        if rec_type in _SKIP_OBS_RECORD_TYPES:
            status_val = str(raw_item.get("status") or "").strip().lower()
            if _terminal_evidence(raw_item) or (rec_type == "case_outcome" and status_val not in _OK_OBS_STATUSES):
                expanded_raw.append({
                    **dict(raw_item),
                    "validated": False,
                    "disqualified_reason": str(raw_item.get("reason") or status_val or "case_outcome_failed"),
                    "_control_record": True,
                })
            continue
        expanded_raw.extend(_normalize_v2_observation_item(raw_item))
    parsed_records: list[dict[str, Any]] = []
    for item in expanded_raw:
        if item.get("_control_record") is True:
            parsed_records.append({key: diagnostic_value(value) for key, value in item.items()})
            continue
        if _terminal_evidence(item):
            parsed_records.append({**{key: diagnostic_value(value) for key, value in item.items()}, "_control_record": True})
            continue
        for key, low, maximum in (("repeat_index", 0, _MAX_REPEAT), ("hops", 0, _MAX_RANKS),
                                  ("rails", 1, _MAX_RANKS),
                                  ("rank", 0, _MAX_RANK_IDX), ("group_size", 1, _MAX_RANKS),
                                  ("bytes", 0, _MAX_BYTES), ("world_size", 1, _MAX_RANKS),
                                  ("local_rank", 0, _MAX_RANK_IDX), ("iterations", 1, _MAX_REPEAT),
                                  ("warmup", 0, _MAX_REPEAT)):
            if item.get(key) is not None:
                bounded_count(item[key], key, low, maximum)
        if item.get("group_ranks") is not None:
            for rank in bounded_sequence(item["group_ranks"], "group_ranks", _MAX_RANKS):
                bounded_count(rank, "group rank", 0, _MAX_RANK_IDX)
        nbytes, latency = item.get("bytes"), _num(item.get("latency_us"))
        if "latency_us" in item and (latency is None or latency < 1e-6):
            raise ProfilerUsageError("latency_us must be a non-boolean number in [1e-6, 1e12]")
        for field in ("clock_mhz", "monotonic_s", "enqueue_us", "device_completion_us"):
            if item.get(field) is not None and _num(item[field]) is None:
                raise ProfilerUsageError(f"{field} must be a finite non-boolean number in [-1e12, 1e12]")
        for field in ("send_counts", "recv_counts"):
            counts = item.get(field)
            if counts is None:
                continue
            if isinstance(counts, (str, bytes)) or not isinstance(counts, (list, tuple)):
                raise ProfilerUsageError(f"{field} must be a list of element counts")
            for count in bounded_sequence(counts, field, _MAX_RANKS):
                bounded_count(count, f"{field} entry", 0, _MAX_BYTES)
        if nbytes is None or latency is None or latency <= 0:
            if item.get("validated") is False:
                parsed_records.append({**dict(item), "_control_record": True})
            continue
        prior_rank = item.get("_rank_invalid")
        prior_size = item.get("_group_size_invalid")
        prior_group = item.get("_group_ranks_invalid")
        raw_rank = item.get("rank")
        rank_invalid = prior_rank is not None or (raw_rank is not None and (
            isinstance(raw_rank, bool) or not isinstance(raw_rank, int)
            or raw_rank < 0))
        raw_group = item.get("group_ranks")
        group_invalid = prior_group is not None or (raw_group is not None and (
            isinstance(raw_group, (str, bytes))
            or not isinstance(raw_group, (list, tuple))
            or any(isinstance(entry, bool) or not isinstance(entry, int)
                   or entry < 0 for entry in raw_group)
            or len(set(raw_group)) != len(raw_group)))
        raw_size = item.get("group_size")
        size_invalid = prior_size is not None or (raw_size is not None and (
            isinstance(raw_size, bool) or not isinstance(raw_size, int)
            or raw_size <= 0))
        if (not size_invalid and raw_size is not None
                and isinstance(raw_group, (list, tuple)) and not group_invalid
                and int(raw_size) != len(raw_group)):
            size_invalid = True
        if size_invalid:
            group_size = None
        elif raw_size is not None:
            group_size = int(raw_size)
        elif isinstance(item.get("group_size"), int) \
                and not isinstance(item.get("group_size"), bool):
            group_size = int(item["group_size"])
        elif isinstance(raw_group, (list, tuple)):
            group_size = len(raw_group)
        else:
            group_size = None
        parsed_records.append({
            **dict(item), "bytes": int(nbytes), "latency_us": latency,
            "tier": str(item.get("tier") or "unidentified"),
            "op": str(item.get("op") or "unknown"),
            "group_size": group_size,
            "protocol": str(item.get("protocol") or "unspecified"),
            "regime": str(item.get("regime") or "isolated"),
            "rank": None if rank_invalid else (
                int(raw_rank) if raw_rank is not None
                else item.get("rank") if isinstance(item.get("rank"), int)
                and not isinstance(item.get("rank"), bool) else None),
            "_rank_invalid": (prior_rank if prior_rank is not None
                              else bounded_summary(raw_rank) if rank_invalid else None),
            "_group_size_invalid": (prior_size if prior_size is not None
                                    else bounded_summary(raw_size) if size_invalid else None),
            "_group_ranks_invalid": (prior_group if prior_group is not None
                                     else bounded_summary(raw_group) if group_invalid else None),
            "group_ranks": None if group_invalid else (
                list(raw_group) if isinstance(raw_group, (list, tuple))
                else None),
            "_parsed_fabric_sample": True,
        })
    if not parsed_records:
        raise ProfilerUsageError("fabric probe produced no usable samples")
    return parsed_records

# Injected verbatim into the standalone probe script (it owns ``PLAN``).
SPLIT_HELPERS = r"""_FABRIC_ABI_MAP = {
    "all_reduce": "hcclAllReduce",
    "all_gather": "hcclAllGather",
    "reduce_scatter": "hcclReduceScatter",
    "all_to_all": "hcclAlltoAll",
    "all_to_all_v": "hcclAlltoAllV",
    "send_recv": "hcclSendRecv",
}
def _sample_id(tier, op, size, rank, repeat_index, split_style, timing_mode):
    payload = json.dumps([PLAN.get("plan_id"), _RUN_ID, tier, op, int(size), str(rank),
                          int(repeat_index), split_style, timing_mode], sort_keys=True)
    return "fp-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
def _sample_identity(item, size, rank, timing_mode):
    sku = PLAN.get("sku") or PLAN.get("hardware") or (BENCH_PLAN_V2.get("sku") if isinstance(BENCH_PLAN_V2, dict) else None) or "declared"
    op_name = str(item.get("op") or "")
    impl = str(item.get("upstream_abi") or _FABRIC_ABI_MAP.get(op_name) or "hccl")
    return {"level": "operator", "boundary": "device_kernel",
            "hardware": str(sku),
            "implementation": impl, "phase": "fabric",
            "shape": {"bytes": int(size), "group_size": len(item.get("group_ranks") or ())},
            "dtype": "fp32", "layout": "ND",
            "execution": {"mode": timing_mode, "protocol": item.get("protocol")}}
def _all_to_all_v_send(rank, group_size, total_elements, style):
    quotient, remainder = divmod(int(total_elements), int(group_size))
    base = [quotient + (1 if index < remainder else 0) for index in range(int(group_size))]
    send = [base[(peer - rank) % int(group_size)] for peer in range(int(group_size))]
    if style == "skew_circulant" and int(group_size) >= 2:
        moved = send[(rank + 1) % int(group_size)] // 2
        if moved:
            send[(rank + 1) % int(group_size)] -= moved
            send[(rank + 2) % int(group_size)] += moved
    return send
def _round_pair(rounds, cursor, rank):
    if not rounds:
        return None, None
    pairs = rounds[int(cursor) % len(rounds)]
    for pair in pairs:
        if rank in pair:
            return pair, 1000 + int(pair[0]) * 4096 + int(pair[1])
    return None, None
def _all_to_all_v_counts(rank, group_size, total_elements, style):
    send = _all_to_all_v_send(rank, group_size, total_elements, style)
    recv = [_all_to_all_v_send(source, group_size, total_elements, style)[rank]
            for source in range(int(group_size))]
    if sum(send) != int(total_elements) or sum(recv) != int(total_elements):
        raise ProfilerUsageError("all_to_all_v split sizes do not conserve elements")
    return send, recv
"""

