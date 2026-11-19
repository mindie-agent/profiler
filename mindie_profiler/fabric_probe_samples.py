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

_SAMPLE_CFG = json.loads(
    (Path(__file__).resolve().parent / "knowledge" / "fabric_probe_presets.json").read_text(encoding="utf-8")
)["sample_bounds"]
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

def _document_items(document: Any) -> list[Any]:
    """Flatten one JSON document while preserving outer control evidence."""
    if isinstance(document, Mapping):
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
    parsed_records: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
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
SPLIT_HELPERS = r"""def _sample_id(tier, op, size, rank, repeat_index, split_style, timing_mode):
    payload = json.dumps([PLAN.get("plan_id"), _RUN_ID, tier, op, int(size), int(rank),
                          int(repeat_index), split_style, timing_mode], sort_keys=True)
    return "fp-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
def _sample_identity(item, size, rank, timing_mode):
    return {"level": "collective", "boundary": "device_kernel",
            "hardware": PLAN.get("hardware") or "declared",
            "implementation": "hccl", "phase": "fabric_probe",
            "shape": {"bytes": int(size), "group_size": len(item.get("group_ranks") or ())},
            "dtype": "uint8", "layout": "linear",
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

