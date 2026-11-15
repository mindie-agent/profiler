"""Per-physical-invocation observations for standalone calibration captures.

[Role]
  Turn a raw calibration `kernel_details.csv` into genuine native calls: ordered
  invocation windows with integer-nanosecond start/end, per-call elapsed/additive
  values, exact raw `Name`, actual reported `Accelerator Core` (UNKNOWN when
  absent, never inferred), device/stream ids, and source SHA-256.

[Boundaries]
  * explicit 10000-10002 / 30000-30002 marker windows: only rows strictly
    between the markers (producer `collect_native_point.py` semantics);
  * one single-kernel row per call for FIA/GDN/conv1d probes;
  * markerless multi-kernel sequences stay UNKNOWN rather than being grouped by
    name period or duration thresholds.

[Invariants] Aggregate totals are never substituted for calls; elapsed span is
not additive kernel mass; absent engine stays UNKNOWN; no predictor import.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

from fleet_capture_artifacts import _open_text, _sha256_file


def _rows(path: Path) -> list[dict[str, Any]]:
    """Decode rows through the maintained integer-nanosecond CSV parser."""
    from mindie_profiler.events import QueryStats
    from mindie_profiler.sources_csv import decode_csv_row, probe_csv

    schema = probe_csv(path)
    stats = QueryStats(rank_id="", window_label="native_calls")
    rows: list[dict[str, Any]] = []
    with _open_text(path) as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for index, raw in enumerate(reader):
            event = decode_csv_row(raw, index, schema, rank_id="", rank_index=None, stats=stats)
            if event is None:
                continue
            core = str(event.core or "").strip()
            if not core or core in {"N/A", "NA"}:
                core = "UNKNOWN"
            rows.append({"row_index": index, "name": str(event.name or event.op_type or "UNKNOWN"),
                         "raw_type": str(event.op_type or "N/A"), "core": core,
                         "start_ns": int(event.start_ns), "end_ns": int(event.end_ns),
                         "duration_ns": int(event.end_ns - event.start_ns),
                         "device_id": str(event.device_id or ""),
                         "stream_id": str(event.stream_id or ""),
                         "task_id": str(event.task_id or ""),
                         "input_shapes": str(event.input_shapes or "")})
    rows.sort(key=lambda item: (item["start_ns"], item["row_index"]))
    return rows


def _shape_text(row: dict[str, Any]) -> str:
    return str(row.get("input_shapes") or "").strip().strip('"').strip()


def _zero_marker(row: dict[str, Any]) -> bool:
    return "zero" in str(row.get("name") or "").lower()


def _marker_groups(rows: list[dict[str, Any]], reps: int = 3) -> tuple[list[dict[str, Any]], list[str], list[int]]:
    """Producer-compatible marker validation; returns (calls, errors, missing reps).

    Requires exact ZerosLike markers with normalized 1-D rep shapes
    10000+i / 30000+i, exactly one of each, in start-time order
    10000,30000,10001,30001,... .  Missing reps are retained as explicit
    missing identities, never renumbered.
    """
    starts: dict[int, dict[str, Any]] = {}
    ends: dict[int, dict[str, Any]] = {}
    errors: list[str] = []
    for row in rows:
        shape = _shape_text(row)
        if not _zero_marker(row):
            if re.search(r"\b(?:1000[0-2]|3000[0-2])\b", shape):
                errors.append(f"marker_operation_not_zero:{shape}:{row.get('name')}")
            continue
        if not re.fullmatch(r"\d+", shape):
            if re.search(r"\b(?:1000[0-2]|3000[0-2])\b", shape):
                errors.append(f"marker_shape_not_single_integer:{shape}")
            continue
        value = int(shape)
        if 10000 <= value < 10000 + reps:
            rep = value - 10000
            if rep in starts:
                errors.append(f"duplicate_start_rep_id:{rep}")
            else:
                starts[rep] = row
        elif 30000 <= value < 30000 + reps:
            rep = value - 30000
            if rep in ends:
                errors.append(f"duplicate_end_rep_id:{rep}")
            else:
                ends[rep] = row
    missing = sorted(set(range(reps)) - set(starts) | set(range(reps)) - set(ends))
    if errors:
        return [], errors, missing
    # Order only complete reps; incomplete reps stay explicit missing identities.
    complete = sorted(set(starts) & set(ends))
    ordered = sorted([(r["start_ns"], "start", rep) for rep, r in starts.items() if rep in complete]
                     + [(r["start_ns"], "end", rep) for rep, r in ends.items() if rep in complete])
    expected = [(rep, kind) for rep in complete for kind in ("start", "end")]
    actual = [(rep, kind) for _ts, kind, rep in ordered]
    if actual != expected:
        errors.append(f"marker_order:{actual}!={expected}")
        return [], errors, missing
    calls: list[dict[str, Any]] = []
    for rep in complete:
        srow, erow = starts[rep], ends[rep]
        interior = [r for r in rows if srow["start_ns"] < r["start_ns"] < erow["start_ns"]]
        if not interior:
            errors.append(f"empty_rep:{rep}")
            if rep not in missing:
                missing.append(rep)
                missing.sort()
            continue
        calls.append({"interior": interior, "rep_id": rep,
                      "marker_start_ns": srow["start_ns"], "marker_end_ns": erow["end_ns"]})
    return calls, errors, missing


def _call_record(index: int, group: dict[str, Any], capture_id: str) -> dict[str, Any]:
    interior = group["interior"]
    rep_id = int(group.get("rep_id", index))
    begin = min(row["start_ns"] for row in interior)
    end = max(row["end_ns"] for row in interior)
    additive_ns = sum(row["duration_ns"] for row in interior)
    engines = sorted({row["core"] for row in interior})
    known = [engine for engine in engines if engine not in {"", "UNKNOWN", "N/A"}]
    names = Counter(row["name"] for row in interior)
    ordered = sorted(interior, key=lambda row: (row["start_ns"], row["row_index"]))
    gaps = [max(0, ordered[i + 1]["start_ns"] - ordered[i]["end_ns"])
            for i in range(len(ordered) - 1)]
    largest = max(gaps) if gaps else 0
    largest_after = ordered[gaps.index(largest)]["name"] if gaps else None
    marker_start = group.get("marker_start_ns")
    marker_end = group.get("marker_end_ns")
    return {"call_index": index, "rep_id": rep_id,
            "call_id": f"{capture_id or 'capture'}:call{rep_id}",
            "start_ns": int(begin), "end_ns": int(end),
            "start_us": round(begin / 1000.0, 6), "end_us": round(end / 1000.0, 6),
            "span_us": round((end - begin) / 1000.0, 6),
            "additive_us": round(additive_ns / 1000.0, 6),
            "marker_start_ns": group.get("marker_start_ns"),
            "marker_end_ns": group.get("marker_end_ns"),
            "marker_rows_excluded": group.get("marker_start_ns") is not None,
            "gap_total_us": round(sum(gaps) / 1000.0, 6),
            "largest_gap_us": round(largest / 1000.0, 6),
            "largest_gap_after_name": largest_after,
            "marker_to_first_kernel_us": (round((ordered[0]["start_ns"] - marker_start) / 1000.0, 6)
                                          if marker_start is not None else None),
            "last_kernel_to_marker_us": (round((marker_end - ordered[-1]["end_ns"]) / 1000.0, 6)
                                         if marker_end is not None else None),
            "event_count": len(interior), "primary_name": names.most_common(1)[0][0],
            "names": list(names), "engines": engines, "engine_known": bool(known),
            "engine": known[0] if len(known) == 1 else ("MIXED" if len(known) > 1 else "UNKNOWN"),
            "device_ids": sorted({row["device_id"] for row in interior}),
            "stream_ids": sorted({row["stream_id"] for row in interior}),
            "task_ids": sorted({row["task_id"] for row in interior if row["task_id"]}),
            "positive_span": (end - begin) > 0 and additive_ns > 0,
            "kernels": [{"name": row["name"], "raw_core": row["core"],
                         "start_ns": row["start_ns"], "end_ns": row["end_ns"],
                         "duration_ns": row["duration_ns"], "device_id": row["device_id"],
                         "stream_id": row["stream_id"], "task_id": row["task_id"]}
                        for row in interior]}


def window_keyset(forwards: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Canonical key + integer-ns/10ns window digests; never uses durations."""
    import hashlib
    import json
    keys: list[tuple[Any, ...]] = []
    pairs: list[tuple[Any, ...]] = []
    ten: list[tuple[Any, ...]] = []
    exact_10 = 0
    for f in forwards:
        body = f.get("body") if isinstance(f.get("body"), Mapping) else {}
        key = (f.get("phase"), str(f.get("rank_id") if f.get("rank_id") is not None else body.get("rank_id", "")),
               str(f.get("device_id") if f.get("device_id") is not None else body.get("device_id", "")),
               f.get("forward_id"))
        start = f.get("start_ns") if f.get("start_ns") is not None else body.get("start_ns")
        end = f.get("end_ns") if f.get("end_ns") is not None else body.get("end_ns")
        keys.append(key)
        if start is None or end is None:
            continue
        pairs.append((key, int(start), int(end)))
        if int(start) % 10 == 0 and int(end) % 10 == 0:
            exact_10 += 1
        ten.append((key, int(start) // 10, int(end) // 10))
    def digest(rows):
        h = hashlib.sha256()
        for row in sorted(rows): h.update(json.dumps(row, separators=(",", ":"), default=str).encode() + b"\n")
        return h.hexdigest()
    return {"key_count": len(keys), "keyset_sha256": digest(keys),
            "windows_integer_ns_sha256": digest(pairs),
            "windows_integer_10ns_sha256": digest(ten),
            "integer_ns_complete": len(pairs) == len(keys),
            "integer_10ns_exact": exact_10 == len(keys), "integer_10ns_exact_count": exact_10}


def native_phase_for_path(path: Path | str) -> tuple[str | None, str]:
    """Raw-operation phase vocabulary from the actual source path, not comparison."""
    low = str(path or "").lower()
    if "fia_chunked" in low or "conv1d" in low or "gdn_" in low or "fia_prefill" in low:
        return "prefill", "source_path_native_operation_vocabulary"
    if "fia_decode" in low:
        return "decode", "source_path_native_operation_vocabulary"
    return None, "source_path_did_not_establish_phase"


def _int_ns(text: Any) -> int | None:
    try:
        value = Decimal(str(text).strip().replace("\t", ""))
    except (InvalidOperation, ValueError):
        return None
    return int((value * Decimal(1000)).to_integral_value()) if value.is_finite() else None


def _task_time_index(path: Path) -> tuple[dict[tuple[Any, ...], dict[str, Any]], list[str]]:
    """Index exact (Device_id,start_ns,end_ns) task owners; no duration inference."""
    index: dict[tuple[Any, ...], dict[str, Any]] = {}
    errors: list[str] = []
    with path.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            device = str(row.get("Device_id") or "").strip()
            begin = _int_ns(row.get("task_start(us)"))
            end = _int_ns(row.get("task_stop(us)"))
            owner = str(row.get("kernel_type") or "").strip()
            if not device or begin is None or end is None or not owner:
                errors.append("malformed_task_row")
                continue
            key = (device, begin, end)
            record = {"device_id": device, "start_ns": begin, "end_ns": end,
                      "native_owner": owner, "stream_id": str(row.get("stream_id") or ""),
                      "task_id": str(row.get("task_id") or ""),
                      "task_duration_ns": _int_ns(row.get("task_time(us)"))}
            if key in index:
                current = index[key]
                index[key] = (current + [record]) if isinstance(current, list) else [current, record]
            else:
                index[key] = record
    return index, errors


def _attach_native_owners(calls: list[dict[str, Any]], task_path: Path) -> dict[str, Any]:
    index, errors = _task_time_index(task_path)
    counts: Counter[str] = Counter()
    joined = unknown = conflicts = 0
    for call in calls:
        call_counts: Counter[str] = Counter()
        for kernel in call["kernels"]:
            base = (kernel["device_id"], kernel["start_ns"], kernel["end_ns"])
            record = index.get(base)
            if isinstance(record, list):
                # Only stream+task can disambiguate a duplicated exact triple.
                matches = [r for r in record
                           if r.get("stream_id") == kernel["stream_id"] and r.get("task_id") == kernel["task_id"]]
                record = matches[0] if len(matches) == 1 else None
                if record is None:
                    conflicts += 1
            if record is None or not isinstance(record, Mapping):
                kernel.update({"native_owner": None, "native_owner_status": "unknown",
                               "owner_source": None, "owner_reason": "missing_or_conflicting_task_time"})
                unknown += 1
                continue
            owner = str(record["native_owner"])
            delta = (kernel["end_ns"] - kernel["start_ns"]) - int(record.get("task_duration_ns") or 0)
            kernel.update({"native_owner": owner, "native_owner_status": "joined",
                           "owner_source": str(task_path), "owner_task_id": record.get("task_id"),
                           "owner_stream_id": record.get("stream_id"),
                           "task_duration_delta_ns": delta})
            call_counts[owner] += 1
            counts[owner] += 1
            joined += 1
        call["native_owners"] = dict(sorted(call_counts.items()))
        call["native_owner_known_count"] = sum(call_counts.values())
        call["native_owner_unknown_count"] = len(call["kernels"]) - sum(call_counts.values())
        call["native_owner_complete"] = call["native_owner_unknown_count"] == 0
    return {"status": "joined" if joined else "unknown", "owner_counts": dict(sorted(counts.items())),
            "joined_kernels": joined, "unknown_kernels": unknown, "conflict_kernels": conflicts,
            "task_time_sha256": _sha256_file(task_path), "task_time_path": str(task_path),
            "errors": errors,
            "note": "per-kernel native owner joined on exact Device_id+integer start/end ns; MIX labels kept raw"}


def parse_native_calls(kd_path: Path | str, *, capture_id: str = "") -> dict[str, Any]:
    """Return genuine physical calls from one calibration kernel timeline."""
    path = Path(kd_path)
    if not path.is_file():
        return {"status": "unknown", "reason": "kernel_details absent", "source_path": str(path)}
    rows = _rows(path)
    if not rows:
        return {"status": "unknown", "reason": "no positive kernel rows", "source_path": str(path)}
    groups, marker_errors, missing_reps = _marker_groups(rows)
    if groups:
        basis = "explicit_10000_30000_markers_interior_rows_only"
    elif marker_errors:
        return {"status": "invalid",
                "reason": "source marker identity/order/shape is not one valid start+end per rep",
                "errors": marker_errors, "missing_rep_ids": missing_reps,
                "source_path": str(path), "row_count": len(rows),
                "source_sha256": _sha256_file(path), "source_size_bytes": path.stat().st_size}
    elif len(rows) <= 3 and len({row["name"] for row in rows}) == 1:
        groups = [{"interior": [row], "rep_id": index} for index, row in enumerate(rows)]
        basis = "one_single_kernel_row_per_native_call"
        missing_reps = []
    else:
        return {"status": "unknown",
                "reason": "markerless_multikernel_sequence_requires_recorded_call_boundary",
                "source_path": str(path), "row_count": len(rows),
                "residual_uncertainty": "no explicit start/end markers; period/name grouping removed",
                "source_sha256": _sha256_file(path), "source_size_bytes": path.stat().st_size}
    calls = [_call_record(index, group, capture_id or path.stem) for index, group in enumerate(groups)]
    owner_scope = {"status": "unknown", "reason": "no adjacent task_time.csv"}
    task_path = path.parent / "task_time.csv"
    if task_path.is_file():
        owner_scope = _attach_native_owners(calls, task_path)
    else:
        for call in calls:
            for kernel in call["kernels"]:
                kernel.update({"native_owner": None, "native_owner_status": "unknown",
                               "owner_source": None, "owner_reason": "task_time_absent"})
            call["native_owners"] = {}
            call["native_owner_known_count"] = 0
            call["native_owner_unknown_count"] = len(call["kernels"])
            call["native_owner_complete"] = False
    kernel_owners: list[dict[str, Any]] = []
    for call in calls:
        for kernel_index, kernel in enumerate(call["kernels"]):
            kernel_owners.append({"call_id": call["call_id"], "rep_id": call["rep_id"],
                                  "kernel_index": kernel_index, "name": kernel["name"],
                                  "raw_core": kernel["raw_core"],
                                  "native_owner": kernel.get("native_owner"),
                                  "native_owner_status": kernel.get("native_owner_status"),
                                  "owner_source": kernel.get("owner_source"),
                                  "device_id": kernel["device_id"],
                                  "stream_id": kernel["stream_id"], "task_id": kernel["task_id"],
                                  "start_ns": kernel["start_ns"], "end_ns": kernel["end_ns"],
                                  "task_duration_delta_ns": kernel.get("task_duration_delta_ns")})
    status = ("measured" if calls and not missing_reps and all(c["positive_span"] for c in calls)
              else ("partial" if calls else "unknown"))
    return {"status": status, "missing_rep_ids": missing_reps, "marker_errors": marker_errors,
            "source_path": str(path), "source_sha256": _sha256_file(path),
            "source_size_bytes": path.stat().st_size, "row_count": len(rows),
            "grouping_basis": basis, "call_count": len(calls),
            "engines_known_count": sum(1 for c in calls if c["engine_known"]),
            "native_owners": owner_scope, "kernel_owners": kernel_owners,
            "unit": "ms", "samples_basis": "elapsed_native_call_span_ms",
            "samples": [{"key": c["call_id"], "observed_ms": round(c["span_us"] / 1000.0, 9),
                         "engine": c["engine"], "engine_known": c["engine_known"],
                         "native_owners": c.get("native_owners"),
                         "native_owner_complete": c.get("native_owner_complete"),
                         "primary_name": c["primary_name"]} for c in calls],
            "sample_keys": [c["call_id"] for c in calls], "calls": calls,
            "note": "individual physical invocations; span is elapsed between interior rows, additive_us is per-call sum"}


def native_call_targets(observations: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Project per-call observed targets for I/N/C scoring (one row per call)."""
    scope = (observations.get("measurements") or {}).get("native_calls") or {}
    if scope.get("status") != "measured":
        return []
    capture_id = ((observations.get("capture") or {}).get("capture_id")
                  or scope.get("capture_id"))
    return [{"capture_id": capture_id, "call_id": c["call_id"],
             "observed_ms": round(c["span_us"] / 1000.0, 9),
             "additive_ms": round(c["additive_us"] / 1000.0, 9),
             "elapsed_ms": c["span_us"] / 1000.0,
             "gap_total_ms": round(c["gap_total_us"] / 1000.0, 9),
             "engine": c["engine"], "engine_known": c["engine_known"],
             "primary_name": c["primary_name"], "device_ids": c["device_ids"],
             "start_ns": c["start_ns"], "end_ns": c["end_ns"],
             "marker_rows_excluded": c["marker_rows_excluded"], "phase": c.get("phase"),
             "source_path": scope.get("source_path"), "source_sha256": scope.get("source_sha256"),
             "source_size_bytes": scope.get("source_size_bytes"),
             "native_owners": c.get("native_owners"),
             "native_owner_complete": c.get("native_owner_complete"),
             "source_fingerprint": {"sha256": scope.get("source_sha256"),
                                    "size_bytes": scope.get("source_size_bytes"),
                                    "task_time_sha256": (scope.get("native_owners") or {}).get("task_time_sha256")}}
            for c in scope["calls"]]
