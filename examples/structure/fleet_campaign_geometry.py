"""Diagnostic-only source reconstruction for campaign/rack active-rank geometry.

Reads only existing producer archives: profiler_info epochs/rank, kernel_details
Input Shapes/Device_id, step_trace_time and client request_summary.  Durations,
byteshare and observed demand are never used.  Structural upper bounds from
``fleet_campaign_case`` stay upper bounds; this module reports whether a unique
active rank/host/pid/forward ordinal/query shape exists.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import fleet_campaign_case as campaign

_ATTENTION = ("FusedInferAttentionScore", "InferAttention", "FlashAttention", "attention", "mla")


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def export_dir(row: Mapping[str, Any], override: Path | None = None) -> Path | None:
    """Return the exact retained export directory for a row, never a neighbor."""
    if override is not None:
        return Path(override)
    scope = campaign._scope(row)
    if scope is None:
        return None
    if scope["kind"] == "campaign":
        path = campaign.CAMPAIGN_ROOT / "runs" / scope["case"] / scope["cell"]
        if scope.get("idle"):
            path = path / "idle_dp_rank"
        return path if path.is_dir() else None
    root = next((base / scope["workstream"] for base in campaign.WORKSTREAM_ROOTS
                 if (base / scope["workstream"]).is_dir()), None)
    if root is None:
        return None
    cell = root / "out" / scope["case"] / scope["cell"]
    matches = sorted(cell.glob(f"*/{scope['profile_dir']}"))
    return matches[0] if len(matches) == 1 else None


def _request_summary(directory: Path) -> dict[str, Any]:
    path = directory / "request_summary.csv"
    if not path.is_file():
        return {"present": False}
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, ValueError):
        return {"present": False}
    return {
        "present": True,
        "path": str(path),
        "sha256": campaign._sha256(path),
        "count": len(rows),
        "req_indices": [row.get("req_idx") for row in rows],
        "turn_indices": [row.get("turn_idx") for row in rows],
        "concurrency": sorted({campaign._int(row.get("concurrency")) for row in rows if campaign._int(row.get("concurrency"))}),
        "isl": sorted({campaign._int(row.get("isl")) for row in rows if campaign._int(row.get("isl"))}),
        "out_tokens_sum": sum(campaign._int(row.get("out_tokens")) or 0 for row in rows),
    }


def _step_trace(directory: Path) -> dict[str, Any]:
    path = directory / "step_trace_time.csv"
    if not path.is_file():
        return {"present": False}
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, ValueError):
        return {"present": False}
    return {
        "present": True,
        "path": str(path),
        "sha256": campaign._sha256(path),
        "rows": len(rows),
        "step_values": [row.get("Step") for row in rows],
        "device_ids": [row.get("Device_id") for row in rows],
        "forward_ordinal_observed": any(str(row.get("Step") or "").strip() for row in rows),
    }


def _rank_device(directory: Path) -> tuple[Any, Any]:
    profilers = sorted(directory.glob("profiler_info_*.json"))
    info = _read_json(profilers[0]) if profilers else None
    device = None
    kernel = directory / "kernel_details.csv.gz"
    if kernel.is_file():
        with gzip.open(kernel, "rt", newline="") as stream:
            record = next(csv.DictReader(stream), None)
            if record:
                device = campaign._int(record.get("Device_id"))
    return (info or {}).get("rank_id"), device


def _sibling_identity(directory: Path, scope: Mapping[str, Any] | None) -> dict[str, Any]:
    if not scope or scope.get("kind") != "campaign":
        return {"has_sibling": False, "same_rank": None, "same_device": None,
                "same_rank_different_device": False, "different_rank_same_device": False,
                "unique_retained_rank_device_pair": None}
    other = directory.parent if directory.name == "idle_dp_rank" else directory / "idle_dp_rank"
    if not other.is_dir():
        return {"has_sibling": False, "same_rank": None, "same_device": None,
                "same_rank_different_device": False, "different_rank_same_device": False,
                "unique_retained_rank_device_pair": None}
    rank_a, device_a = _rank_device(directory)
    rank_b, device_b = _rank_device(other)
    return {
        "has_sibling": True,
        "sibling_directory": str(other),
        "primary_or_idle_rank": [rank_a, rank_b],
        "primary_or_idle_device": [device_a, device_b],
        "same_rank": rank_a == rank_b,
        "same_device": device_a == device_b,
        "same_rank_different_device": rank_a == rank_b and device_a != device_b,
        "different_rank_same_device": rank_a != rank_b and device_a == device_b,
        "unique_retained_rank_device_pair": rank_a == rank_b and device_a == device_b,
    }


def _engine_schedule(directory: Path) -> dict[str, Any]:
    log = None
    for parent in (directory, *directory.parents):
        candidate = parent / "vllm_rank0.log"
        if candidate.is_file():
            log = candidate
            break
    if log is None:
        return {"present": False, "engine_schedule_observed": False}
    active: dict[int, int] = {}
    lines = 0
    with log.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            match = re.search(r"Engine (\d+):.*Running: (\d+) reqs, Waiting: (\d+) reqs", line)
            if match:
                lines += 1
                engine, running = int(match.group(1)), int(match.group(2))
                active[engine] = max(active.get(engine, 0), running)
    return {"present": True, "path": str(log), "sha256": campaign._sha256(log),
            "schedule_lines": lines, "engine_ids": sorted(active),
            "max_running_by_engine": {str(key): value for key, value in sorted(active.items())},
            "active_engines": sorted(key for key, value in active.items() if value > 0),
            "engine_schedule_observed": bool(lines)}


def _launch_processes(directory: Path) -> dict[str, Any]:
    path = directory / "kv_cache_startup.json"
    if not path.is_file():
        return {"present": False, "pid_observed": False}
    raw = path.read_text(errors="replace")
    processes = sorted({(role, int(pid)) for role, pid in
                        re.findall(r"\((Worker|EngineCore)_[A-Za-z0-9]+ pid=(\d+)\)", raw)})
    return {
        "present": True, "path": str(path), "sha256": campaign._sha256(path),
        "processes": [{"role": role, "pid": pid} for role, pid in processes],
        "pid_observed": bool(processes), "pid_scope": "cell_launch_all_workers",
        "export_rank_pid_bound": False,
    }


def probe_rank_binding(row: Mapping[str, Any], override: Path | None = None) -> dict[str, Any] | None:
    """Rank/epoch/request binding from the exact export; no measured durations."""
    directory = export_dir(row, override)
    if directory is None:
        return None
    profilers = sorted(directory.glob("profiler_info_*.json"))
    info = _read_json(profilers[0]) if profilers else None
    kernel = directory / "kernel_details.csv.gz"
    device_ids: set[int] = set()
    kernel_rows = 0
    if kernel.is_file():
        with gzip.open(kernel, "rt", newline="") as stream:
            for record in csv.DictReader(stream):
                kernel_rows += 1
                device = campaign._int(record.get("Device_id"))
                if device is not None:
                    device_ids.add(device)
    node = None
    scope = campaign._scope(row)
    worker = campaign._RANK_RE.match(directory.name)
    worker_rank = ({"dp": int(worker.group(1)), "pp": int(worker.group(2)),
                    "tp": int(worker.group(3)), "dcp": int(worker.group(4)),
                    "ep": int(worker.group(5)), "rank": int(worker.group(6))}
                   if worker else None)
    if scope and scope["kind"] == "rack":
        node = directory.parent.name
    return {
        "directory": str(directory),
        "stack": scope["kind"] if scope else None,
        "export_role": "idle_dp_rank" if scope and scope.get("idle") else "primary",
        "profiler_info": {
            "path": str(profilers[0]) if profilers else None,
            "sha256": campaign._sha256(profilers[0]) if profilers else None,
            "rank_id": campaign._int((info or {}).get("rank_id")),
            "start_cnt": (info or {}).get("start_info", {}).get("start_cnt"),
            "start_monotonic": (info or {}).get("start_info", {}).get("start_monotonic"),
            "collection_end": (info or {}).get("end_info", {}).get("collectionTimeEnd"),
        } if info else None,
        "kernel": {"path": str(kernel) if kernel.is_file() else None,
                   "rows": kernel_rows, "device_ids": sorted(device_ids),
                   "sha256": campaign._sha256(kernel) if kernel.is_file() else None},
        "host": {"node": node, "host_observed": node is not None, "pid": None,
                 "pid_observed": False},
        "worker_rank": worker_rank,
        "sibling_identity": _sibling_identity(directory, scope),
        "request_schedule": _request_summary(directory),
        "launch_processes": _launch_processes(directory),
        "engine_schedule": _engine_schedule(directory),
        "step_trace": _step_trace(directory),
        "binding": {
            "rank_observed": bool(device_ids or (info or {}).get("rank_id") is not None),
            "device_observed": bool(device_ids),
            "epoch_observed": bool((info or {}).get("start_info")),
            "host_observed": node is not None,
            "pid_observed": bool(_launch_processes(directory).get("pid_observed")),
            "pid_export_bound": False,
            "engine_schedule_observed": bool(_engine_schedule(directory).get("engine_schedule_observed")),
            "forward_ordinal_observed": False,
        },
    }


def _shape_int(text: str) -> int | None:
    first = str(text or "").split(";", 1)[0].split(",", 1)[0].strip().strip('"')
    return campaign._int(first)


def attention_query_candidates(row: Mapping[str, Any], *,
                               override: Path | None = None,
                               declared_mtp: int = 0,
                               max_num_seqs: int | None = None) -> dict[str, Any] | None:
    """Distinct attention bucket shapes from the exact export; no durations."""
    directory = export_dir(row, override)
    if directory is None:
        return None
    kernel = directory / "kernel_details.csv.gz"
    q: dict[int, int] = {}
    kv: dict[int, int] = {}
    signatures: dict[str, int] = {}
    rows = 0
    shaped_rows = 0
    if kernel.is_file():
        with gzip.open(kernel, "rt", newline="") as stream:
            for record in csv.DictReader(stream):
                name = str(record.get("Name") or "")
                if not any(token.lower() in name.lower() for token in _ATTENTION):
                    continue
                rows += 1
                fields = str(record.get("Input Shapes") or "").split(";")
                q_value = _shape_int(fields[0]) if fields else None
                kv_value = _shape_int(fields[1]) if len(fields) > 1 else None
                if q_value is not None:
                    shaped_rows += 1
                    q[q_value] = q.get(q_value, 0) + 1
                if kv_value is not None:
                    kv[kv_value] = kv.get(kv_value, 0) + 1
                signature = ";".join(fields[:3])
                signatures[signature] = signatures.get(signature, 0) + 1
    policy = 1 + int(declared_mtp or 0)
    candidates = sorted(q)
    decode_q = {key: count for key, count in q.items()
                if max_num_seqs is None or int(key) <= int(max_num_seqs)}
    narrow_candidate = len(decode_q) == 1 and shaped_rows > 0
    identified = shaped_rows > 0 and len(candidates) == 1
    if shaped_rows == 0:
        residual = ["attention_shapes_na_or_absent", "no_forward_ordinal_or_atb_launch_args"]
    elif identified:
        residual = []
    else:
        residual = ["multiple_attention_query_buckets", "no_forward_ordinal_or_atb_launch_args",
                    "padded_bucket_cannot_be_distinguished_from_valid_rows"]
    return {
        "directory": str(directory), "attention_rows": rows, "shape_rows": shaped_rows,
        "shape_available": shaped_rows > 0,
        "q_candidates": q, "kv_candidates": kv,
        "top_signatures": sorted(signatures.items(), key=lambda item: -item[1])[:5],
        "declared_policy_q": policy,
        "decode_q_candidates": decode_q,
        "single_decode_bucket_candidate": narrow_candidate,
        "actual_query_identified": False,
        "policy_present": policy in q,
        "bucket_q": max(q, key=q.get) if q else None,
        "unique_query_identified": identified, "residual": residual,
    }


_ORDINAL_MARKERS = {
    "combine": "_combine_sampled_and_draft_tokens_kernel",
    "slot": "_compute_slot_mappings_kernel",
}


def forward_ordinal_candidates(row: Mapping[str, Any], *,
                               override: Path | None = None,
                               max_num_seqs: int | None = None) -> dict[str, Any] | None:
    """Attention q distribution between observed kernel markers; no durations."""
    directory = export_dir(row, override)
    if directory is None:
        return None
    kernel = directory / "kernel_details.csv.gz"
    attention: list[tuple[float, int]] = []
    markers: dict[str, list[float]] = {name: [] for name in _ORDINAL_MARKERS}
    if kernel.is_file():
        with gzip.open(kernel, "rt", newline="") as stream:
            for record in csv.DictReader(stream):
                name = str(record.get("Name") or "")
                try:
                    start = float(str(record.get("Start Time(us)")).strip())
                except (TypeError, ValueError):
                    start = None
                if start is None:
                    continue
                for key, marker in _ORDINAL_MARKERS.items():
                    if marker in name:
                        markers[key].append(start)
                if any(token.lower() in name.lower() for token in _ATTENTION):
                    fields = str(record.get("Input Shapes") or "").split(";")
                    q_value = _shape_int(fields[0]) if fields else None
                    if q_value is not None:
                        attention.append((start, q_value))
    declared_steps = campaign._int(row.get("forward_steps"))
    result: dict[str, Any] = {"directory": str(directory), "attention_rows": len(attention),
                              "declared_forward_steps": declared_steps,
                              "marker_counts": {key: len(value) for key, value in markers.items()},
                              "ordinal_available": any(markers.values()), "by_marker": {}}
    for key, starts in markers.items():
        starts = sorted(starts)
        intervals = []
        if starts:
            bounds = starts + [float("inf")]
            for ordinal in range(len(starts)):
                counts: dict[int, int] = {}
                for start, q_value in attention:
                    if bounds[ordinal] <= start < bounds[ordinal + 1]:
                        counts[q_value] = counts.get(q_value, 0) + 1
                decode = {q: n for q, n in counts.items()
                          if max_num_seqs is None or q <= int(max_num_seqs)}
                intervals.append({"ordinal": ordinal, "q_counts": dict(sorted(counts.items())),
                                  "decode_q_counts": dict(sorted(decode.items()))})
        decode_values = sorted({q for item in intervals for q in item["decode_q_counts"]})
        prefill_ordinals = [item["ordinal"] for item in intervals
                            if item["q_counts"] and not item["decode_q_counts"]]
        mixed_ordinals = [item["ordinal"] for item in intervals if len(item["decode_q_counts"]) > 1]
        empty_ordinals = [item["ordinal"] for item in intervals if not item["q_counts"]]
        query_identified = (bool(intervals) and not empty_ordinals
                            and len(decode_values) == 1 and not mixed_ordinals)
        delta = (len(starts) - declared_steps) if declared_steps else None
        result["by_marker"][key] = {
            "marker_count": len(starts),
            "marker_step_delta": delta,
            "intervals_with_shapes": len(intervals) - len(empty_ordinals),
            "published_interval_count": len(intervals),
            "empty_ordinals": empty_ordinals,
            "q_by_ordinal": intervals,
            "decode_q_values": decode_values,
            "prefill_ordinals": prefill_ordinals,
            "mixed_decode_ordinals": mixed_ordinals,
            "single_q_per_interval": bool(intervals) and not empty_ordinals and all(len(item["q_counts"]) == 1 for item in intervals),
            "retained_rank_decode_query_identified": query_identified,
        }
    identified = any(item.get("retained_rank_decode_query_identified") for item in result["by_marker"].values())
    result["retained_rank_decode_query_identified"] = identified
    result["actual_batch_identified"] = identified
    result["active_rank_identified"] = False
    result["residual"] = ([] if identified else ["marker_sequence_not_declared_forward_ordinal",
                                                 "padded_graph_bucket_vs_valid_rows_unresolved",
                                                 "host_input_atb_launch_args_absent"]) + [
        "active_rank_selection_unproven"]
    return result


def canonical_digest(binding: Mapping[str, Any], geometry: Mapping[str, Any]) -> str:
    """Identity digest over source facts, excluding row IDs, targets and durations."""
    payload = {
        "directory": binding.get("directory"),
        "export_role": binding.get("export_role"),
        "profiler_rank": (binding.get("profiler_info") or {}).get("rank_id"),
        "worker_rank": binding.get("worker_rank"),
        "sibling_identity": binding.get("sibling_identity"),
        "profiler_sha256": (binding.get("profiler_info") or {}).get("sha256"),
        "kernel_sha256": (binding.get("kernel") or {}).get("sha256"),
        "device_ids": (binding.get("kernel") or {}).get("device_ids"),
        "host_node": (binding.get("host") or {}).get("node"),
        "request_count": (binding.get("request_schedule") or {}).get("count"),
        "request_sha256": (binding.get("request_schedule") or {}).get("sha256"),
        "launch_processes": (binding.get("launch_processes") or {}).get("processes"),
        "engine_schedule": {
            "engine_ids": (binding.get("engine_schedule") or {}).get("engine_ids"),
            "active_engines": (binding.get("engine_schedule") or {}).get("active_engines"),
        },
        "step_sha256": (binding.get("step_trace") or {}).get("sha256"),
        "request_concurrency": (binding.get("request_schedule") or {}).get("concurrency"),
        "request_isl": (binding.get("request_schedule") or {}).get("isl"),
        "q_candidates": geometry.get("q_candidates"),
        "kv_candidates": geometry.get("kv_candidates"),
        "declared_policy_q": geometry.get("declared_policy_q"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
