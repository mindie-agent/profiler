"""Typed, independent measured evidence for the fleet capture inventory.

[Role]
  Public observation API assembled from `fleet_capture_artifacts`.  Exposes
  distinct boundaries (raw kernel mass, op aggregate, client request, recorded
  forward span) without dividing by unverified forward counts.

[Invariants]
  * `observed_ms` is only a typed client metric; no cross-boundary fallback.
  * Row `kernel_summary`/`observed_ms` never score.
  * Per-forward windows stay unknown without independent marker/rank proof.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from fleet_capture_calls import native_call_targets, native_phase_for_path, parse_native_calls, window_keyset
from fleet_source_discovery import lookup_source_receipt
from fleet_capture_artifacts import (
    DATA_ROOTS, MULTINODE_RUNS_ROOT, RESULTS_DIR, SCHEMA_VERSION, _CLIENT_FILE,
    _artifact_in_dir, _base_capture_id, _cell_meta_path, _declared_steps,
    _forward_scope, _identity, _measured_json_path, _reported_entry,
    _registered_extraction_index, _REGISTERED_FORWARD_CACHE, _receipt_index,
    _STEP_MARKERS, _as_float, _open_text,
    _reported_scope, _row_summary_is_derived, _source_index,
    clear_observation_caches, configure_observation_roots,
    parse_kernel_details_summary, parse_op_statistic_summary,
    resolve_capture_directory,
    _client_from_cell_meta, _client_from_measurement_json, _parse_float_cell,
    _read_json, _cache_put, _stat_key, _sha256_file, _recovered_source,
    _CLIENT_CACHE, _median, _normalise_ops, _FILE_CACHE,
)

__all__ = ["extract_capture_observations", "select_measurement",
           "summarize_observation_inventory", "configure_observation_roots",
           "clear_observation_caches", "clear_caches", "native_call_targets",
           "parse_native_calls", "lookup_source_receipt"]

clear_caches = clear_observation_caches
_WAVE5_DECLARATION: dict[str, Any] | None = None
def _source_declaration(source_path: str | None) -> dict[str, Any] | None:
    """Existing Wave5 source declaration, attached only when its source path is listed."""
    global _WAVE5_DECLARATION
    if not source_path:
        return None
    if _WAVE5_DECLARATION is None:
        path = RESULTS_DIR / "wave5_full_generalization.json"
        try:
            raw = path.read_bytes(); doc = json.loads(raw)
            _WAVE5_DECLARATION = {"sha256": __import__("hashlib").sha256(raw).hexdigest(),
                                  "provenance": doc.get("calibration_provenance") or {},
                                  "sources": {str(c.get("path")) for c in doc.get("cases") or () if c.get("path")}}
        except (OSError, ValueError):
            _WAVE5_DECLARATION = {"sha256": None, "provenance": {}, "sources": set()}
    if source_path not in _WAVE5_DECLARATION["sources"]:
        return None
    return {"source_file_sha256": _WAVE5_DECLARATION["sha256"],
            "evaluation_relation": (_WAVE5_DECLARATION["provenance"] or {}).get("evaluation_relation"),
            "target_timing_used_to_fit": (_WAVE5_DECLARATION["provenance"] or {}).get("target_timing_used_to_fit"),
            "source_path_listed": True}

_SCOPE_RULES: tuple[tuple[str, tuple[str, ...], bool], ...] = (
    ("moe.combine", ("moe", "combine"), True),
    ("moe.dispatch", ("moe", "dispatch"), True),
    ("moe", ("groupedmatmul", "moe", "gating", "hcpre", "hcpost", "swigluquant"), False),
    ("collective", ("hcom", "hccl", "allreduce", "allgather", "alltoall", "reduce_scatter", "reducescatter", "broadcast"), False),
    ("attention", ("attention", "fia", "mla", "indexer", "sparseattn", "sparseflash", "sharedkv", "chunkkda"), False),
    ("gemm", ("matmul", "gemm", "conv"), False),
    ("kv_cache", ("rope", "rotary", "kv", "cache", "scatterpakv", "prolog"), False),
    ("norm_activation", ("norm", "silu", "swiglu", "gelu", "add", "mul", "sigmoid"), False),
    ("elementwise_quant", ("quant", "cast", "zero", "fill", "slice", "pad", "transpose", "copy", "div", "sub"), False),
)
def scope_for_op(op_type: str) -> str:
    """One exact scope per op; no share allocation."""
    low = str(op_type or "").lower()
    if "combine" in low and any(k in low for k in ("moe", "distribute", "dispatchffn")):
        return "moe.combine"
    if "dispatch" in low and any(k in low for k in ("moe", "distribute", "dispatchffn")):
        return "moe.dispatch"
    for scope, tokens, require_all in _SCOPE_RULES:
        if (all(t in low for t in tokens) if require_all else any(t in low for t in tokens)):
            return scope
    return "other"

def family_durations_us(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Sum complete measured op durations by exact scope, keeping op names/counts."""
    scopes: dict[str, dict[str, Any]] = {}
    engine_rows = summary.get("by_op_engine")
    if not isinstance(engine_rows, Mapping) or not engine_rows:
        engine_rows = {f"{op}\x1f{(entry or {}).get('core', 'UNKNOWN') if isinstance(entry, Mapping) else 'UNKNOWN'}":
                       {"op_type": op, "core": (entry or {}).get("core", "UNKNOWN") if isinstance(entry, Mapping) else "UNKNOWN",
                        "count": (entry or {}).get("count", 0) if isinstance(entry, Mapping) else 0,
                        "total_us": entry if not isinstance(entry, Mapping) else entry.get("total_us", 0.0)}
                       for op, entry in (summary.get("ops") or {}).items()}
    for _key, entry in engine_rows.items():
        op_type = str((entry or {}).get("op_type") or "UNKNOWN")
        core = str((entry or {}).get("core") or "UNKNOWN")
        scope = scope_for_op(op_type)
        total = float((entry or {}).get("total_us") or 0.0)
        count = int((entry or {}).get("count") or 0)
        bucket = scopes.setdefault(scope, {"duration_us": 0.0, "count": 0, "op_types": {}, "cores": Counter()})
        bucket["duration_us"] += total
        bucket["count"] += count
        op_bucket = bucket["op_types"].setdefault(op_type, {"count": 0, "total_us": 0.0, "core": core, "by_engine_us": {}})
        op_bucket["count"] += count
        op_bucket["total_us"] = round(op_bucket["total_us"] + total, 6)
        if op_bucket["core"] != core:
            op_bucket["core"] = "MIXED"
        op_bucket["by_engine_us"][core] = round(op_bucket["by_engine_us"].get(core, 0.0) + total, 6)
        bucket["cores"][core] += total
    return {scope: {"duration_us": round(b["duration_us"], 6), "count": b["count"],
                    "op_types": b["op_types"], "by_core_us": {k: round(v, 6) for k, v in sorted(b["cores"].items())}}
            for scope, b in sorted(scopes.items())}

def parse_request_summary(path: Path | str) -> dict[str, Any]:
    """Read every per-request row; keep producer semantics and failures."""
    req_path = Path(path)
    key = _stat_key(req_path)
    if key is not None and key in _CLIENT_CACHE:
        return _CLIENT_CACHE[key]
    if not req_path.exists() or not req_path.is_file():
        raise FileNotFoundError(str(req_path))
    samples: list[dict[str, Any]] = []
    modes: Counter[str] = Counter()
    with req_path.open("rt", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            ok_field = row.get("ok")
            ok = (str(ok_field).strip().lower() in {"1", "true", "yes"} if ok_field is not None and str(ok_field).strip() != ""
                  else str(row.get("status") or "").strip() == "200")
            mode = str(row.get("mode") or "").strip()
            if mode:
                modes[mode] += 1
            out_tokens = _parse_float_cell(row.get("out_tokens"))
            ttft, tpot = _parse_float_cell(row.get("ttft_ms")), _parse_float_cell(row.get("tpot_ms"))
            e2e = _parse_float_cell(row.get("e2e_ms"))
            derived = ((e2e - ttft) / (out_tokens - 1.0)
                       if e2e is not None and ttft is not None and out_tokens is not None and out_tokens > 1.0 else None)
            samples.append({"ok": ok, "mode": mode, "req_idx": row.get("req_idx"),
                            "concurrency": _parse_float_cell(row.get("concurrency")),
                            "isl": _parse_float_cell(row.get("isl")), "out_tokens": out_tokens,
                            "out_tokens_known": "out_tokens" in row and str(row.get("out_tokens") or "").strip() != "",
                            "ttft_ms": ttft, "tpot_ms": tpot, "derived_tpot_ms": derived, "e2e_ms": e2e,
                            "itl_p50_ms": _parse_float_cell(row.get("itl_p50_ms")),
                            "itl_p90_ms": _parse_float_cell(row.get("itl_p90_ms")),
                            "itl_p99_ms": _parse_float_cell(row.get("itl_p99_ms"))})
    ok_samples = [s for s in samples if s["ok"]]
    known = [s for s in ok_samples if s["out_tokens_known"]]
    missing = len(ok_samples) - len(known)
    decode_tokens = sum(max(0.0, (s["out_tokens"] or 0.0) - 1.0) for s in known)
    reported_tpot = _median(s["tpot_ms"] for s in ok_samples)
    derived_tpot = _median(s["derived_tpot_ms"] for s in ok_samples)
    prefill_only = bool(ok_samples) and all("prefill" in (s.get("mode") or "").lower() for s in ok_samples)
    evidence = ("no_successful_requests" if not ok_samples else
                ("unknown_completion_tokens" if missing > 0 else
                 ("client_decode_tokens" if decode_tokens > 0.0 else
                  ("no_decode_tokens" if prefill_only else "unknown_completion_tokens"))))
    result = {
        "source_path": str(req_path), "requests": len(samples), "ok_requests": len(ok_samples),
        "failed_requests": len(samples) - len(ok_samples), "modes": dict(sorted(modes.items())),
        "concurrency_max": max((s["concurrency"] or 0.0) for s in ok_samples) if ok_samples else None,
        "ttft_ms_median": _median(s["ttft_ms"] for s in ok_samples), "tpot_ms_median": reported_tpot,
        "tpot_ms_derived_median": derived_tpot,
        "tpot_derived_consistent": (abs(reported_tpot - derived_tpot) <= 0.05 * max(reported_tpot, derived_tpot)
                                    if reported_tpot and derived_tpot else None),
        "itl_p50_ms_median": _median(s["itl_p50_ms"] for s in ok_samples),
        "itl_p90_ms_median": _median(s["itl_p90_ms"] for s in ok_samples),
        "itl_p99_ms_median": _median(s["itl_p99_ms"] for s in ok_samples),
        "e2e_ms_median": _median(s["e2e_ms"] for s in ok_samples),
        "decode_token_count": int(round(decode_tokens)) if ok_samples and missing == 0 else None,
        "successful_requests_with_known_completion_tokens": len(known),
        "successful_requests_missing_completion_tokens": missing,
        "metric_semantics": ("producer_reported_tpot_column; may be SSE-event interval per producer count, "
                             "not independently tokenized; completion counts are the producer out_tokens field"),
        "completion_tokens_field_present": any(s["out_tokens_known"] for s in samples),
        "decode_evidence": evidence, "samples": samples,
    }
    if key is not None:
        _cache_put(_CLIENT_CACHE, key, result)
    return result

def parse_export_summary(path: Path | str) -> dict[str, Any]:
    """Parse measured `export_summary.json`; never rescale a total."""
    ex_path = Path(path)
    key = _stat_key(ex_path)
    if key is not None and key in _FILE_CACHE:
        return _FILE_CACHE[key]
    data = json.loads(ex_path.read_text(encoding="utf-8"))
    by_core, core_counts = {}, Counter()
    for core, entry in (data.get("by_accelerator_core") or {}).items():
        if isinstance(entry, Mapping):
            by_core[str(core)] = float(entry.get("total_us") or entry.get("duration_us") or 0.0)
            core_counts[str(core)] = int(entry.get("count") or 0)
        else:
            by_core[str(core)] = float(entry or 0.0)
    ops = _normalise_ops({str(i.get("type")): i for i in (data.get("top_op_types") or ())
                          if isinstance(i, Mapping) and i.get("type")})
    result = {
        "source_kind": "export_summary", "source_path": str(ex_path),
        "total_kernel_rows": int(data.get("total_kernel_rows") or 0),
        "total_kernel_duration_us": round(float(data.get("total_kernel_duration_us") or sum(by_core.values()) or 0.0), 6),
        "by_accelerator_core": {k: round(v, 6) for k, v in sorted(by_core.items())},
        "by_accelerator_core_counts": dict(sorted(core_counts.items())),
        "ops": ops, "ops_complete": False,
        "top_op_types": [{"type": k, "core": v["core"], "count": v["count"], "total_us": round(v["total_us"], 2)}
                         for k, v in sorted(ops.items(), key=lambda item: -item[1]["total_us"])[:5]],
        "first_start_us": None, "last_end_us": None, "span_us": None,
    }
    if key is not None:
        _cache_put(_FILE_CACHE, key, result)
    return result

def _kernel_timeline(kd_path: Path) -> dict[str, Any]:
    """Bounded timeline evidence: one pass, no event retention/sort."""
    path = Path(kd_path)
    count = 0
    min_start = max_end = last_start = None
    ordered = True
    busy = gap = max_gap = 0.0
    gap_count = seg_count = markers = 0
    cur_start = cur_end = None
    first_marker = last_marker = None
    with _open_text(path) as handle:
        for row in csv.DictReader(handle):
            raw_dur = row.get("Duration(us)")
            if raw_dur is None:
                raw_dur = row.get("Task Duration(us)")
            if raw_dur is None:
                raw_dur = row.get("Duration(ns)")
                divisor = 1000.0
            else:
                divisor = 1.0
            if raw_dur is None or str(raw_dur).strip() == "":
                raise ValueError(f"malformed duration cell in {path}: {raw_dur!r}")
            dur = _as_float(raw_dur, "duration cell", path) / divisor
            raw_start = row.get("Start Time(us)") or row.get("Task Start Time(us)")
            if raw_start in (None, "", "N/A"):
                continue
            try:
                begin = float(str(raw_start).strip())
            except (TypeError, ValueError):
                continue
            if not math.isfinite(begin):
                continue
            count += 1
            finish = begin + dur
            min_start = begin if min_start is None else min(min_start, begin)
            max_end = finish if max_end is None else max(max_end, finish)
            if last_start is not None and begin < last_start:
                ordered = False
            last_start = begin
            if ordered:
                if cur_start is None:
                    cur_start, cur_end, seg_count = begin, finish, 1
                elif begin <= cur_end + 1.0:
                    cur_end = max(cur_end, finish)
                else:
                    busy += max(0.0, cur_end - cur_start)
                    delta = begin - cur_end
                    gap += delta
                    gap_count += 1
                    max_gap = max(max_gap, delta)
                    cur_start, cur_end, seg_count = begin, finish, seg_count + 1
            if str(row.get("Name") or row.get("Type") or "") in _STEP_MARKERS:
                markers += 1
                first_marker = begin if first_marker is None else min(first_marker, begin)
                last_marker = finish if last_marker is None else max(last_marker, finish)
    if count == 0:
        return {"status": "no_timeline_rows", "source_path": str(path), "timeline_rows": 0}
    if ordered and cur_start is not None and cur_end is not None:
        busy += max(0.0, cur_end - cur_start)
    return {"status": "measured_timeline", "source_path": str(path), "timeline_rows": count,
            "start_order": "nondecreasing" if ordered else "out_of_order",
            "wall_span_us": round(max_end - min_start, 6) if (max_end is not None and min_start is not None) else None,
            "busy_union_us": round(busy, 6) if ordered else None,
            "idle_gap_us": round(gap, 6) if ordered else None,
            "idle_gap_count": gap_count if ordered else None,
            "max_gap_us": round(max_gap, 6) if ordered else None,
            "segment_count": seg_count if ordered else None,
            "step_marker_count": markers, "step_marker_first_us": first_marker,
            "step_marker_last_us": last_marker,
            "step_marker_meaning": "invocation count only; no proven one-marker-per-forward mapping"}

def _extraction_scope(path: Path, expected_sha: str | None, label: str,
                      raw_source: Path | None = None) -> dict[str, Any]:
    """Per-forward spans from one exact extraction/receipt file.

    The receipt is only promoted when the actual raw source file at
    ``source_identity.path`` has matching size and streamed SHA-256, and the
    caller-provided expected SHA agrees (when present).  Cache entries are
    invalidated by receipt mtime/size, expected SHA, and raw mtime/size.
    """
    stat = _stat_key(path)
    expected = str(expected_sha or "").lower()
    cached = _REGISTERED_FORWARD_CACHE.get(stat) if stat is not None else None
    if isinstance(cached, Mapping):
        raw_path = Path(str(cached.get("raw_path") or ""))
        try:
            raw_stat = raw_path.stat() if raw_path.is_file() else None
        except OSError:
            raw_stat = None
        if (cached.get("expected") == expected and raw_stat is not None
                and (raw_stat.st_size, raw_stat.st_mtime_ns) == (cached.get("raw_size"), cached.get("raw_mtime"))):
            return cached["result"]
    raw = _read_json(path) or {}
    data = raw.get("observed") if isinstance(raw.get("observed"), Mapping) else raw
    source = data.get("source_identity") or {}
    source_sha = str(source.get("sha256") or "").lower()
    if expected and not source_sha:
        return {"status": "unknown", "reason": "expected source sha exists but receipt/source identity has none"}
    if expected and source_sha and expected != source_sha:
        return {"status": "unknown", "reason": "extraction source sha does not match expected source sha"}
    if data.get("status") != "measured":
        return {"status": "unknown", "reason": "extraction is not measured"}
    boundary = data.get("metric_boundary")
    prefill_schema = str(data.get("schema_version") or "").startswith("mindie-prefill-body-observation")
    if boundary != "target_body_device_graph" and not prefill_schema:
        return {"status": "unknown", "reason": f"unsupported extraction boundary {boundary!r}"}
    raw_path = Path(str(source["path"])) if source.get("path") else (raw_source or Path())
    if not raw_path.is_file():
        recovered = _recovered_source(raw_path)
        if recovered is not None:
            raw_path = recovered
    raw_digest = None
    raw_verified = False
    if raw_path.is_file():
        try:
            raw_size = raw_path.stat().st_size
        except OSError:
            raw_size = -1
        if source.get("size_bytes") is None or int(source["size_bytes"]) == raw_size:
            raw_digest = _sha256_file(raw_path)
            raw_verified = bool(raw_digest and source_sha and raw_digest == source_sha)
    if not raw_verified:
        return {"status": "unknown",
                "reason": "actual raw source bytes do not match the receipt source identity",
                "receipt_source_sha256": source_sha, "raw_path": str(raw_path),
                "raw_sha256": raw_digest, "raw_available": raw_path.is_file()}
    forwards = [f for f in (data.get("forwards") or ()) if isinstance(f, Mapping)]
    spans = [float(f["body_forward_span_ms"]) for f in forwards
             if isinstance(f.get("body_forward_span_ms"), (int, float)) and math.isfinite(float(f["body_forward_span_ms"]))]
    if prefill_schema:
        spans = [float(f["body"]["span_ms"]) for f in forwards
                 if isinstance(f.get("body"), Mapping) and isinstance(f["body"].get("span_ms"), (int, float))
                 and math.isfinite(float(f["body"]["span_ms"]))]
    if not spans:
        return {"status": "unknown", "reason": "extraction has no measured forward spans"}
    activities = [float(f["body_activity_ms"]) for f in forwards
                  if isinstance(f.get("body_activity_ms"), (int, float))]
    if prefill_schema:
        activities = [float(f["body"]["device_activity_union_ms"]) for f in forwards
                      if isinstance(f.get("body"), Mapping) and isinstance(f["body"].get("device_activity_union_ms"), (int, float))]
    geometries = Counter()
    for forward in forwards:
        geom = forward.get("geometry") or {}
        geometries[f"q={geom.get('query_rows')},seq={geom.get('sequences_per_replica')},tok={geom.get('tokens_per_sequence')}"] += 1
    result = {"status": "measured",
              "boundary": (f"per_forward_window_{label}_prefill_chunk" if prefill_schema else f"per_forward_window_{label}"),
              "window_source": str(path), "receipt_sha256": _sha256_file(path),
              "receipt_source_identity": dict(source), "keyset": window_keyset(forwards),
              "extraction_sha256": expected or source_sha,
              "source_sha256": source_sha, "raw_path": str(raw_path), "raw_sha256": raw_digest,
              "raw_digest_verified": True, "same_artifact": True,
              "source_fingerprint": {"sha256": source_sha, "path": str(raw_path), "size_bytes": raw_path.stat().st_size},
              "window_count": len(spans), "offset": None,
              "portable_match": f"{label}_extraction_identity",
              "mean_forward_span_ms": round(sum(spans) / len(spans), 6),
              "median_forward_span_ms": round(sorted(spans)[len(spans) // 2], 6),
              "min_forward_span_ms": round(min(spans), 6), "max_forward_span_ms": round(max(spans), 6),
              "mean_body_activity_ms": round(sum(activities) / len(activities), 6) if activities else None,
              "forward_spans_ms": [round(v, 6) for v in spans],
              "samples_ms": [round(v, 6) for v in spans],
              "samples_basis": "elapsed_window_span_ms",
              "geometry_populations": dict(geometries),
              "frame_identifiers": [
                  {"ordinal": index, "forward_id": f.get("forward_id"), "phase": f.get("phase"),
                   "rank_id": (f.get("rank_id") if f.get("rank_id") is not None
                               else (f.get("body") or {}).get("rank_id") if isinstance(f.get("body"), Mapping) else None),
                   "device_id": (f.get("device_id") if f.get("device_id") is not None
                                 else (f.get("body") or {}).get("device_id") if isinstance(f.get("body"), Mapping) else None),
                   "query_rows": (f.get("geometry") or {}).get("query_rows", f.get("query_rows")),
                   "start_ns": (f.get("start_ns") or (f.get("body") or {}).get("start_ns")
                                if isinstance(f.get("body"), Mapping) else f.get("start_ns")),
                   "end_ns": (f.get("end_ns") or (f.get("body") or {}).get("end_ns")
                              if isinstance(f.get("body"), Mapping) else f.get("end_ns"))}
                  for index, f in enumerate(forwards)],
              "mean_additive_us_per_window": None,
              "note": "device forward spans from the extraction; not client TPOT/TTFT"}
    if stat is not None:
        raw_stat = raw_path.stat()
        _cache_put(_REGISTERED_FORWARD_CACHE, stat,
                   {"result": result, "expected": expected, "raw_path": str(raw_path),
                    "raw_size": raw_stat.st_size, "raw_mtime": raw_stat.st_mtime_ns})
    return result

def _registered_forward_scope(base_cid: str, phase: str, entry: Mapping[str, Any] | None) -> dict[str, Any]:
    """Per-forward spans from an exact registered extraction identity."""
    if not base_cid.startswith("registered_"):
        return {"status": "unknown", "reason": "not a registered capture"}
    case_id = base_cid.split(":", 1)[1] if ":" in base_cid else ""
    path = _registered_extraction_index().get((phase, case_id))
    if path is None:
        return {"status": "unknown", "reason": "no registered extraction with this phase/case id"}
    raw_source = Path(str(entry["path"])) if entry and entry.get("path") else None
    return _extraction_scope(path, (entry or {}).get("sha256"), "registered", raw_source)

def _receipt_forward_scope(entry: Mapping[str, Any] | None, directory: Path | None) -> dict[str, Any]:
    """Per-forward spans from a source-indexed measured receipt (DSH/Wave5/aliases)."""
    index = _receipt_index()
    candidates: list[str] = []
    if entry and entry.get("path"):
        candidates.append(str(entry["path"]))
    if directory is not None:
        for name in ("kernel_details.csv", "kernel_details.csv.gz"):
            candidates.append(str(directory / name))
        candidates += [str(p) for p in sorted(directory.glob("*.kernel_details.csv.gz"))]
        candidates += [str(p) for p in sorted(directory.glob("*.kernel_details.csv"))]
    record = None
    used = ""
    for source in candidates:
        record = index.get(source)
        if record is None:
            try:
                record = index.get(str(Path(source).resolve()))
            except OSError:
                record = None
        if record is not None:
            used = source
            break
    if record is None:
        return {"status": "unknown", "reason": "no measured receipt for this exact source path"}
    expected = str(record.get("sha256") or (entry or {}).get("sha256") or "")
    return _extraction_scope(record["receipt"], expected, "source_receipt", Path(used)) | {"source_path": used}

def extract_capture_observations(row: Mapping[str, Any], *, include_timeline: bool = False) -> dict[str, Any]:
    """Return typed measured/unknown scopes for one fleet capture row."""
    cid = str(row.get("capture_id") or "")
    base = _base_capture_id(cid)
    suite = str(row.get("suite") or (base.split(":", 1)[0] if ":" in base else ""))
    phase = str(row.get("phase") or "").lower()
    declared = _declared_steps(row)
    directory, preferred, notes = resolve_capture_directory(row)
    entry = _reported_entry(_source_index().get(base))
    diagnostics = [{"kind": "source_resolution", "detail": n} for n in notes]
    kernel_scope = {"status": "unknown", "boundary": "whole_capture_native_kernel_rows_all_streams_additive"}
    op_scope = {"status": "unknown", "boundary": "capture_op_statistic_aggregate"}
    client, timeline, export_data, raw_path = None, None, None, None
    kernel_summary: dict[str, Any] = {}
    native_calls_scope: dict[str, Any] = {"status": "unknown", "reason": "not a standalone calibration capture"}
    if suite == "operator_and_kernel_calibration_20261107" and directory is not None:
        preferred_kernel = preferred if (preferred is not None and preferred.suffix in {".csv", ".gz"}) else None
        calibration_kd = _artifact_in_dir(directory, ("kernel_details.csv.gz", "kernel_details.csv"), preferred_kernel)
        if calibration_kd is not None:
            native_calls_scope = {**parse_native_calls(calibration_kd, capture_id=cid), "capture_id": cid}
            native_phase, phase_basis = native_phase_for_path(calibration_kd)
            native_calls_scope.update({"phase": native_phase, "native_phase": native_phase, "row_phase": phase,
                                       "phase_basis": phase_basis,
                                       "phase_conflict": bool(native_phase and phase and native_phase != phase)})
            for call in native_calls_scope.get("calls") or ():
                call["phase"] = native_phase
            for sample in native_calls_scope.get("samples") or ():
                sample["phase"] = native_phase
    if directory is not None:
        op_path = _artifact_in_dir(directory, ("op_statistic.csv",))
        export_path = _artifact_in_dir(directory, ("export_summary.json",))
        preferred_kernel = preferred if (preferred is not None and preferred.suffix in {".csv", ".gz"}
                                         and "export" not in preferred.name) else None
        kd_path = _artifact_in_dir(directory, ("kernel_details.csv.gz", "kernel_details.csv"), preferred_kernel)
        raw_path = op_path or kd_path or export_path
        if export_path is not None:
            export_data = _read_json(export_path)
            try:
                ex = parse_export_summary(export_path)
                rows, total = int(ex.get("total_kernel_rows") or 0), float(ex.get("total_kernel_duration_us") or 0.0)
                kernel_scope = {"status": "measured" if rows > 0 and total > 0.0 else "zero_raw_kernel_rows",
                                "boundary": "whole_capture_native_kernel_rows_all_streams_additive",
                                "source_kind": "export_summary", "source_path": str(export_path),
                                "total_kernel_rows": rows, "total_kernel_duration_us": round(total, 6),
                                "by_core_us": {str(k): round(float(v), 6) for k, v in (ex.get("by_accelerator_core") or {}).items()},
                                "worker_dir": (export_data or {}).get("worker_dir"),
                                "rank_label": (export_data or {}).get("rank_label"),
                                "note": "rank export; header-only/zero is missing evidence, not measured zero"}
            except (OSError, ValueError) as exc:
                diagnostics.append({"kind": "raw_summary_error", "path": str(export_path), "error": str(exc)})
        if op_path is not None:
            try:
                op = parse_op_statistic_summary(op_path)
                rows, total = int(op.get("total_kernel_rows") or 0), float(op.get("total_kernel_duration_us") or 0.0)
                if rows > 0 and total > 0.0:
                    op_scope = {"status": "measured", "boundary": "capture_op_statistic_aggregate",
                                "source_kind": "op_statistic", "source_path": str(op_path),
                                "native_call_count": rows, "total_kernel_duration_us": round(total, 6),
                                "by_core_us": {str(k): round(float(v), 6) for k, v in (op.get("by_accelerator_core") or {}).items()},
                                "by_op_us": {str(k): round(float(v.get("total_us") or 0.0), 6) for k, v in (op.get("ops") or {}).items()},
                                "families_us": family_durations_us(op), "ops_complete": True,
                                "note": "same-rank op aggregate; no kernel start times/windows"}
                    kernel_summary = op
            except (OSError, ValueError) as exc:
                diagnostics.append({"kind": "raw_summary_error", "path": str(op_path), "error": str(exc)})
        if kd_path is not None and ((not kernel_summary and kernel_scope["status"] != "zero_raw_kernel_rows") or include_timeline):
            try:
                kd = parse_kernel_details_summary(kd_path)
                rows, total = int(kd.get("total_kernel_rows") or 0), float(kd.get("total_kernel_duration_us") or 0.0)
                if rows > 0 and total > 0.0:
                    kernel_scope = {"status": "measured", "boundary": "whole_capture_native_kernel_rows_all_streams_additive",
                                    "source_kind": "kernel_details", "source_path": str(kd_path),
                                    "total_kernel_rows": rows, "total_kernel_duration_us": round(total, 6),
                                    "by_core_us": {str(k): round(float(v), 6) for k, v in (kd.get("by_accelerator_core") or {}).items()},
                                    "first_start_us": kd.get("first_start_us"), "max_end_us": kd.get("last_end_us"),
                                    "span_us": kd.get("span_us"),
                                    "note": "row-level kernels; additive over streams; may exceed wall span; not a forward"}
                    op_scope = {"status": "measured", "boundary": "whole_capture_native_kernel_rows_all_streams_additive",
                                "source_kind": "kernel_details", "source_path": str(kd_path),
                                "native_call_count": rows, "total_kernel_duration_us": round(total, 6),
                                "by_core_us": kernel_scope["by_core_us"],
                                "by_op_us": {str(k): round(float(v.get("total_us") or 0.0), 6) for k, v in (kd.get("ops") or {}).items()},
                                "families_us": family_durations_us(kd), "ops_complete": True,
                                "note": "row-level kernels summed by exact op classification"}
                    kernel_summary = kd
                else:
                    kernel_scope = {"status": "zero_raw_kernel_rows", "boundary": "whole_capture_native_kernel_rows_all_streams_additive",
                                    "source_kind": "kernel_details", "source_path": str(kd_path),
                                    "total_kernel_rows": rows, "total_kernel_duration_us": round(total, 6),
                                    "note": "header-only CSV is missing evidence, not measured zero"}
                    diagnostics.append({"kind": "header_only_or_zero_rows", "path": str(kd_path),
                                        "detail": "raw kernel CSV has no data rows"})
            except (OSError, ValueError) as exc:
                diagnostics.append({"kind": "raw_summary_error", "path": str(kd_path), "error": str(exc)})
        if kernel_scope["status"] == "zero_raw_kernel_rows" and op_scope["status"] == "measured":
            diagnostics.append({"kind": "op_aggregate_without_kernel_rows",
                                "detail": "positive op aggregate without kernel rows/start times is not a kernel measurement"})
        request_path = _artifact_in_dir(directory, (_CLIENT_FILE,))
        if request_path is not None:
            try:
                client = parse_request_summary(request_path)
            except (OSError, ValueError) as exc:
                diagnostics.append({"kind": "client_summary_error", "path": str(request_path), "error": str(exc)})
        else:
            meta = _cell_meta_path(directory)
            if meta is not None:
                client = _client_from_cell_meta(meta)
                if client:
                    diagnostics.append({"kind": "client_source", "source": "cell_metadata", "path": str(meta)})
            elif preferred is not None and preferred.suffix == ".json" and "export_summary" not in preferred.name:
                client = _client_from_measurement_json(preferred)
                if client:
                    diagnostics.append({"kind": "client_source", "source": "measurement_json", "path": str(preferred)})
            elif (measured := _measured_json_path(directory)) is not None:
                client = _client_from_measurement_json(measured)
                if client:
                    diagnostics.append({"kind": "client_source", "source": "same_cell_measured_json", "path": str(measured)})
        if include_timeline and kd_path is not None:
            try:
                timeline = _kernel_timeline(kd_path)
            except (OSError, ValueError) as exc:
                diagnostics.append({"kind": "timeline_error", "path": str(kd_path), "error": str(exc)})
        elif include_timeline:
            diagnostics.append({"kind": "timeline_unavailable", "reason": "no kernel_details.csv[.gz]"})

    client_scope = {"status": "unknown", "boundary": "native_client_reported_request"}
    if client:
        raw_samples = [s for s in (client.get("samples") or ()) if isinstance(s, Mapping)]
        per_request = []
        for sample in raw_samples:
            if not sample.get("ok", True):
                continue
            value = None
            if phase == "decode":
                value = sample.get("tpot_ms")
            else:
                value = sample.get("ttft_ms")
                if value is None and sample.get("ttft_s") is not None:
                    value = float(sample["ttft_s"]) * 1000.0
            if value is not None and math.isfinite(float(value)):
                per_request.append(round(float(value), 6))
        client_scope = {"status": "measured", "boundary": "native_client_reported_request",
                        "source_path": client.get("source_path"),
                        "reported_tpot_ms": client.get("tpot_ms_median"),
                        "reported_ttft_ms": client.get("ttft_ms_median"),
                        "reported_e2e_ms": client.get("e2e_ms_median"),
                        "reported_itl_p50_ms": client.get("itl_p50_ms_median"),
                        "reported_itl_p90_ms": client.get("itl_p90_ms_median"),
                        "reported_itl_p99_ms": client.get("itl_p99_ms_median"),
                        "completion_tokens": client.get("decode_token_count"),
                        "decode_evidence": client.get("decode_evidence"),
                        "metric_semantics": client.get("metric_semantics"),
                        "samples": raw_samples,
                        "boundary_samples_ms": per_request,
                        "samples_basis": ("producer_per_request_tpot_or_ttft" if client.get("source_path", "").endswith(".csv")
                                          else "harness_aggregate_only_no_itl_promotion")}
    observed = basis = None
    if client_scope["status"] == "measured":
        if phase == "decode" and client_scope.get("reported_tpot_ms") is not None:
            observed, basis = float(client_scope["reported_tpot_ms"]), "client_reported_tpot_producer_basis"
        elif phase == "prefill" and client_scope.get("reported_ttft_ms") is not None:
            observed, basis = float(client_scope["reported_ttft_ms"]), "client_reported_ttft_producer_basis"
    reported_scope = _reported_scope(entry, raw_path, directory, phase)
    row_ks = dict(row.get("kernel_summary") or {})
    row_observed = _parse_float_cell(row.get("observed_ms"))
    row_claimed = {"used_as_evidence": False, "observed_ms": row_observed,
                   "kernel_summary_total_us": (round(_parse_float_cell(row_ks.get("total_kernel_duration_us")), 6)
                                               if row_ks and _parse_float_cell(row_ks.get("total_kernel_duration_us")) is not None else None),
                   "matches_observed_times_declared_steps": _row_summary_is_derived(row_ks, row_observed, declared or 0),
                   "note": "stored fleet projection; never a measurement"}
    kernel_ok, op_ok = kernel_scope["status"] == "measured", op_scope["status"] == "measured"
    primary = op_scope if op_ok else kernel_scope
    if kernel_ok and op_ok:
        evidence_status = "measured"
    elif op_ok:
        evidence_status = "measured_op_aggregate_only"
    elif kernel_ok:
        evidence_status = "measured_kernel_export"
    elif kernel_scope["status"] == "zero_raw_kernel_rows" or client_scope["status"] == "measured":
        evidence_status = "missing_raw_kernel_rows"
    else:
        evidence_status = "missing_artifact"
    forward_scope = _forward_scope(directory)
    if forward_scope.get("status") == "measured":
        forward_scope = {**forward_scope, "capture_id": cid}
    if forward_scope.get("status") != "measured":
        registered_scope = _registered_forward_scope(base, phase, entry)
        if registered_scope.get("status") == "measured":
            forward_scope = {**registered_scope, "capture_id": cid}
        else:
            receipt_scope = _receipt_forward_scope(entry, directory)
            if receipt_scope.get("status") == "measured":
                forward_scope = {**receipt_scope, "capture_id": cid}
    calibration = row.get("source_calibration") if isinstance(row.get("source_calibration"), Mapping) else {}
    source_role = _source_declaration((forward_scope.get("source_fingerprint") or {}).get("path"))
    evaluation = {"evaluation_mode": row.get("evaluation_mode"), "calibration_role": row.get("calibration_role"),
                  "evaluation_relation": row.get("evaluation_relation") or calibration.get("evaluation_relation"),
                  "target_timing_used_to_fit": row.get("target_timing_used_to_fit", calibration.get("target_timing_used_to_fit")),
                  "source_role": row.get("source_role"), "declared_status": row.get("status"),
                  "source_declaration": source_role,
                  "role_provenance_status": ("source_declared" if source_role else
                                             "recorded_envelope" if (row.get("evaluation_mode") or row.get("source_calibration") or row.get("calibration_role")) else "not_declared"),
                  "blind_claim_status": ("not_blind_source_target_fit" if source_role and source_role.get("target_timing_used_to_fit")
                                         else "no_declared_blind_role")}
    if forward_scope.get("status") == "measured":
        forward_scope["evaluation"] = dict(evaluation)
        forward_scope["source_scope_id"] = f"{forward_scope.get('source_sha256')}:{(forward_scope.get('keyset') or {}).get('windows_integer_ns_sha256')}"
    count = int(primary.get("native_call_count") or primary.get("total_kernel_rows") or 0)
    mass = primary.get("total_kernel_duration_us") if (kernel_ok or op_ok) else None
    call_set = {"status": "measured" if mass is not None else "unknown",
                "boundary": "raw_native_call_set_not_model_forward",
                "call_count": count or None,
                "additive_total_us": round(float(mass), 6) if mass is not None else None,
                "mean_additive_us_per_call": round(float(mass) / count, 6) if mass is not None and count > 0 else None,
                "source_kind": primary.get("source_kind"),
                "note": "kernel rows/op counts including repetitions; not a model forward"}
    return {
        "schema_version": SCHEMA_VERSION,
        "status": ("compared" if observed is not None and (kernel_ok or op_ok)
                   else "client_only" if observed is not None
                   else "reported_only" if (reported_scope.get("status") == "reported"
                                            or forward_scope.get("status") == "measured")
                   else "native_only" if (kernel_ok or op_ok)
                   else "missing_artifact"),
        "evidence_status": evidence_status,
        "capture": {"capture_id": cid, "base_capture_id": base, "suite": suite,
                    "hardware_tier": str(row.get("hardware_tier") or "").upper(),
                    "phase": native_calls_scope.get("native_phase") or phase,
                    "row_phase": phase,
                    "observed_phase": native_calls_scope.get("native_phase"), "evaluation": evaluation,
                    "declared_forward_steps": declared, "declared_forward_steps_used_for_measurement": False},
        "identity": {**_identity(directory, export_data),
                     **({"reported_rank": m.group(1)} if entry and (m := re.search(r"/ranks/([^/]+)/", str(entry.get("path") or ""))) else {})},
        "source": {"kind": primary.get("source_kind") or "none",
                   "path": primary.get("source_path") or (str(directory) if directory else ""),
                   "directory": str(directory) if directory else "",
                   "sha256": ((entry or {}).get("sha256") if reported_scope.get("source_relation")
                              else native_calls_scope.get("source_sha256") if native_calls_scope.get("status") == "measured" else None),
                   "sha256_scope": ("parsed_artifact" if reported_scope.get("same_artifact")
                                    else "recorded_source_file" if reported_scope.get("source_relation")
                                    else "native_calls_raw" if native_calls_scope.get("status") == "measured" else None),
                   "sha256_source_path": (reported_scope.get("source_path") if reported_scope.get("source_relation")
                                          else native_calls_scope.get("source_path")
                                          if native_calls_scope.get("status") == "measured" else None),
                   "recorded_source_sha256": (entry or {}).get("sha256") if reported_scope.get("source_relation") else None,
                   "reported_source_sha256": (entry or {}).get("sha256"),
                   "reported_source_relation": reported_scope.get("source_relation"),
                   "independent": kernel_ok or op_ok, "timeline_included": timeline is not None},
        "measurements": {"whole_capture_native_kernel_rows": kernel_scope,
                         "capture_op_statistic_aggregate": op_scope,
                         "native_calls": native_calls_scope,
                         "native_call_set": call_set,
                         "native_client_request": client_scope,
                         "producer_reported_device_forward_span": reported_scope,
                         "per_forward_window": forward_scope},
        "observed_ms": observed, "observed_basis": basis,
        "step_targets": {
            "client_native_request_ms": observed,
            "producer_reported_device_forward_span_ms": (reported_scope.get("observed_ms")
                                                         if reported_scope.get("status") == "reported"
                                                         and reported_scope.get("target_proven") else None),
            "per_forward_window_ms": (forward_scope.get("mean_forward_span_ms")
                                      if forward_scope.get("status") == "measured" else None),
            "per_forward_window_elapsed_ms": (forward_scope.get("mean_forward_span_ms")
                                              if forward_scope.get("status") == "measured" else None),
            "per_forward_window_additive_ms": (round(float(forward_scope["mean_additive_us_per_window"]) / 1000.0, 9)
                                               if forward_scope.get("status") == "measured"
                                               and forward_scope.get("mean_additive_us_per_window") is not None else None),
            "native_mass_ms": (round(float(mass) / 1000.0, 9) if mass is not None else None),
            "native_call_mean_ms": (round(float(mass) / count / 1000.0, 9) if mass is not None and count > 0 else None),
            "native_call_samples_ms": [t["observed_ms"] for t in native_call_targets({"measurements": {"native_calls": native_calls_scope}})],
            "native_call_ids": [t["call_id"] for t in native_call_targets({"measurements": {"native_calls": native_calls_scope}})],
            "native_call_engines": [t["engine"] for t in native_call_targets({"measurements": {"native_calls": native_calls_scope}})],
            "native_call_engine_known": [t["engine_known"] for t in native_call_targets({"measurements": {"native_calls": native_calls_scope}})],
            "native_call_phase": native_calls_scope.get("native_phase"),
            "native_call_phase_conflict": native_calls_scope.get("phase_conflict"),
            "per_forward_window_samples_ms": list(forward_scope.get("samples_ms") or ())
                                               if forward_scope.get("status") == "measured" else [],
            "per_forward_window_samples_basis": forward_scope.get("samples_basis"),
        },
        "observed_operator_ms": None, "observed_by_core_ms": {}, "observed_by_family_ms": {},
        "observed_forward_by_family_ms": ({k: round(v / 1000.0, 9) for k, v in
                                           (forward_scope.get("family_mean_us_per_window") or {}).items()}
                                          if forward_scope.get("status") == "measured" else {}),
        "observed_by_canonical_family_ms": {}, "observed_by_unified_family_ms": {},
        "by_core_us": primary.get("by_core_us") or {}, "by_op_us": primary.get("by_op_us") or {},
        "by_scope": primary.get("families_us") or {}, "native_call_count": count or None,
        "native_call_mean_us": round(float(mass) / count, 6) if mass is not None and count > 0 else None,
        "native_calls": native_calls_scope,
        "native_call_targets": native_call_targets({"measurements": {"native_calls": native_calls_scope}}),
        "native_mass_us": mass, "native_mass_boundary": primary.get("boundary") if mass is not None else None,
        "native_kernel_mass_us": kernel_scope.get("total_kernel_duration_us") if kernel_ok else None,
        "native_op_mass_us": op_scope.get("total_kernel_duration_us") if op_ok else None,
        "kernel_summary": kernel_summary if (kernel_ok or op_ok) else {},
        "client": client, "timeline": timeline, "reported": reported_scope,
        "row_claimed": row_claimed, "diagnostics": diagnostics,
    }

def select_measurement(observations: Mapping[str, Any], boundary: str) -> float | None:
    """Read only the explicitly requested typed boundary (no substitution)."""
    lookup = "per_forward_window" if boundary == "per_forward_window_additive" else boundary
    entry = (observations.get("measurements") or {}).get(lookup) or {}
    if entry.get("status") not in {"measured", "reported"}:
        return None
    if boundary == "producer_reported_device_forward_span" and not entry.get("target_proven"):
        return None
    if boundary == "native_client_request":
        phase = (observations.get("capture") or {}).get("phase")
        value = entry.get("reported_tpot_ms") if phase == "decode" else entry.get("reported_ttft_ms")
        return float(value) if value is not None else None
    if entry.get("observed_ms") is not None:
        return float(entry["observed_ms"])
    if boundary == "per_forward_window":
        value = entry.get("mean_forward_span_ms")
        return float(value) if value is not None else None
    if boundary == "per_forward_window_additive":
        value = entry.get("mean_additive_us_per_window")
        return round(float(value) / 1000.0, 9) if value is not None else None
    if boundary == "native_calls":
        return None
    if boundary == "native_call_set":
        value = entry.get("mean_additive_us_per_call")
        return round(float(value) / 1000.0, 9) if value is not None else None
    if entry.get("total_kernel_duration_us") is not None:
        return round(float(entry["total_kernel_duration_us"]) / 1000.0, 9)
    return None

def summarize_observation_inventory(rows: Sequence[Mapping[str, Any]], *, include_timeline: bool = False) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    basis_counts: Counter[str] = Counter()
    decode_counts: Counter[str] = Counter()
    forward_counts: Counter[str] = Counter()
    missing: list[str] = []
    observed_none = 0
    native_call_captures = 0
    native_call_count = 0
    native_engine_known_calls = 0
    for row in rows:
        obs = extract_capture_observations(row, include_timeline=include_timeline)
        status_counts[obs["evidence_status"]] += 1
        source_counts[obs["source"]["kind"]] += 1
        basis_counts[obs["observed_basis"] or "none"] += 1
        decode_counts[(obs.get("client") or {}).get("decode_evidence") or "no_client_data"] += 1
        forward_counts[(obs["measurements"].get("per_forward_window") or {}).get("status") or "unknown"] += 1
        if obs["observed_ms"] is None:
            observed_none += 1
        nc = obs["measurements"].get("native_calls") or {}
        if nc.get("status") == "measured":
            native_call_captures += 1
            native_call_count += int(nc.get("call_count") or 0)
            native_engine_known_calls += int(nc.get("engines_known_count") or 0)
        if obs["evidence_status"] in {"missing_artifact", "missing_raw_kernel_rows"}:
            missing.append(str(row.get("capture_id") or ""))
    return {"schema_version": SCHEMA_VERSION, "captures": len(rows),
            "status": dict(sorted(status_counts.items())), "source_kinds": dict(sorted(source_counts.items())),
            "observed_bases": dict(sorted(basis_counts.items())), "decode_evidence": dict(sorted(decode_counts.items())),
            "per_forward_window": dict(sorted(forward_counts.items())), "observed_ms_none": observed_none,
            "native_call_captures": native_call_captures, "native_call_count": native_call_count,
            "native_engine_known_calls": native_engine_known_calls,
            "missing_artifact_captures": missing[:50], "missing_artifact_count": len(missing)}
