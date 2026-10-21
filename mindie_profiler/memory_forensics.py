"""Memory inefficiency pattern scanner and step-monotonic leak forensics.

[Role]
  Distill Ascend ``msmemscope`` inefficiency/leak analyzers and MindIE memory
  forensics into deterministic, pure in-memory detectors for ``early_allocation``,
  ``late_deallocation``, ``temporary_buffer_spike`` (including temporary
  idleness), ``allocator_fragmentation``, and ``step_monotonic_leak`` versus
  warmup/graph-bucket reservation growth.

[Invariants]
  * All byte and timestamp metrics are derived strictly from caller-supplied
    block events or step snapshots; missing fields remain ``None``.
  * Initial warmup steps and ``reserved_bytes`` caching-allocator bucket step-ups
    where post-warmup ``allocated_bytes`` returns to baseline are never
    misclassified as ``step_monotonic_leak``.
  * ``allocator_fragmentation`` is computed from ``(reserved - allocated) / reserved``
    only when ``reserved_bytes > 0`` and ``allocated_bytes is not None``.

[Timeouts & Locks]
  Single-pass O(N log N) interval/sequence analysis in memory.  No I/O, no
  subprocesses, no network, and no locks.

[Side-Effect Policy]
  Pure functional transforms returning plain JSON-serializable dicts.
"""

from __future__ import annotations

import re
import statistics
from typing import Any, Mapping, Sequence

MEMORY_FORENSICS_SCHEMA = "mindie-memory-forensics/1"

_UNIT_MULTIPLIERS: dict[str, float] = {
    "B": 1.0, "BYTE": 1.0, "BYTES": 1.0,
    "KB": 1024.0, "KIB": 1024.0,
    "MB": 1024.0 ** 2, "MIB": 1024.0 ** 2,
    "GB": 1024.0 ** 3, "GIB": 1024.0 ** 3,
}


def _to_bytes_local(value: Any, default_unit: str = "B") -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) * _UNIT_MULTIPLIERS.get(default_unit.upper(), 1.0)
    if isinstance(value, str):
        m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$", value)
        if m:
            num = float(m.group(1))
            unit = (m.group(2) or default_unit).upper()
            return num * _UNIT_MULTIPLIERS.get(unit, 1.0)
    return None


def _opt_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _opt_bytes(value: Any, default_unit: str = "B") -> float | None:
    if value is None or isinstance(value, bool):
        return None
    val = _to_bytes_local(value, default_unit=default_unit)
    return float(val) if val is not None else None


def _normalize_block(raw: Mapping[str, Any], idx: int) -> dict[str, Any]:
    unit = str(raw.get("unit") or "B")
    size_b = (
        _opt_bytes(raw.get("size_bytes"), "B")
        or _opt_bytes(raw.get("size"), unit)
        or _opt_bytes(raw.get("allocated_bytes"), "B")
        or 0.0
    )
    alloc_api = _opt_int(raw.get("malloc_api_id") or raw.get("alloc_api_id") or raw.get("alloc_seq") or raw.get("start_api_id"))
    free_api = _opt_int(raw.get("free_api_id") or raw.get("free_seq") or raw.get("end_api_id"))
    first_api = _opt_int(raw.get("first_access_api_id") or raw.get("first_use_api_id") or raw.get("first_use_seq"))
    last_api = _opt_int(raw.get("last_access_api_id") or raw.get("last_use_api_id") or raw.get("last_use_seq"))
    max_api_gap = _opt_int(raw.get("max_access_interval") or raw.get("max_access_api_gap"))

    alloc_ns = _opt_int(raw.get("alloc_ns") or raw.get("start_ns"))
    if alloc_ns is None and raw.get("alloc_ms") is not None:
        alloc_ns = int(round(float(raw["alloc_ms"]) * 1_000_000.0))
    free_ns = _opt_int(raw.get("free_ns") or raw.get("end_ns"))
    if free_ns is None and raw.get("free_ms") is not None:
        free_ns = int(round(float(raw["free_ms"]) * 1_000_000.0))
    first_ns = _opt_int(raw.get("first_use_ns") or raw.get("first_access_ns"))
    if first_ns is None and raw.get("first_use_ms") is not None:
        first_ns = int(round(float(raw["first_use_ms"]) * 1_000_000.0))
    last_ns = _opt_int(raw.get("last_use_ns") or raw.get("last_access_ns"))
    if last_ns is None and raw.get("last_use_ms") is not None:
        last_ns = int(round(float(raw["last_use_ms"]) * 1_000_000.0))
    max_idle_ns = _opt_int(raw.get("max_idle_gap_ns"))
    if max_idle_ns is None and raw.get("max_idle_gap_ms") is not None:
        max_idle_ns = int(round(float(raw["max_idle_gap_ms"]) * 1_000_000.0))

    return {
        "block_id": str(raw.get("block_id") or raw.get("addr") or raw.get("ptr") or f"block_{idx}"),
        "addr": str(raw.get("addr") or raw.get("ptr") or f"0x{idx:08x}"),
        "size_bytes": float(size_b),
        "op_name": str(raw.get("op_name") or raw.get("name") or raw.get("owner") or "unknown_op"),
        "tag": str(raw.get("tag") or raw.get("category") or "").lower(),
        "attr": str(raw.get("attr") or raw.get("allocator") or "PTA").upper(),
        "step": _opt_int(raw.get("step")),
        "stream_id": str(raw.get("stream_id")) if raw.get("stream_id") is not None else None,
        "free_stream_id": str(raw.get("free_stream_id")) if raw.get("free_stream_id") is not None else None,
        "malloc_api_id": alloc_api,
        "free_api_id": free_api,
        "first_access_api_id": first_api,
        "last_access_api_id": last_api,
        "max_access_interval": max_api_gap,
        "alloc_ns": alloc_ns,
        "free_ns": free_ns,
        "first_use_ns": first_ns,
        "last_use_ns": last_ns,
        "max_idle_gap_ns": max_idle_ns,
        "shadow": bool(raw.get("shadow", False)),
        "unfreed": bool(raw.get("unfreed", False)) or (free_api is None and free_ns is None and bool(raw.get("is_leaked", False))),
    }


def analyze_memory_inefficiencies(
    memory_blocks: Sequence[Mapping[str, Any]] | None = None,
    *,
    allocator_snapshots: Sequence[Mapping[str, Any]] | None = None,
    min_api_gap: int = 10,
    idle_api_gap_threshold: int = 3000,
    early_alloc_threshold_ms: float = 2.0,
    late_free_threshold_ms: float = 2.0,
    idle_gap_threshold_ms: float = 10.0,
    early_alloc_ratio_threshold: float = 0.30,
    late_free_ratio_threshold: float = 0.30,
    spike_ratio_threshold: float = 0.15,
    high_fragmentation_threshold: float = 0.15,
    moderate_fragmentation_threshold: float = 0.05,
) -> dict[str, Any]:
    """Detect early_allocation, late_deallocation, temporary_buffer_spike, and allocator_fragmentation."""
    blocks = [_normalize_block(b, i) for i, b in enumerate(memory_blocks or []) if isinstance(b, Mapping)]
    snapshots = [dict(s) for s in (allocator_snapshots or []) if isinstance(s, Mapping)]

    early_allocations: list[dict[str, Any]] = []
    late_deallocations: list[dict[str, Any]] = []
    temp_spikes: list[dict[str, Any]] = []
    fragmentation_records: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    early_ns_thresh = int(round(early_alloc_threshold_ms * 1_000_000.0))
    late_ns_thresh = int(round(late_free_threshold_ms * 1_000_000.0))
    idle_ns_thresh = int(round(idle_gap_threshold_ms * 1_000_000.0))

    free_apis = sorted(b["free_api_id"] for b in blocks if b["free_api_id"] is not None)
    malloc_apis = sorted(b["malloc_api_id"] for b in blocks if b["malloc_api_id"] is not None)
    free_times = sorted(b["free_ns"] for b in blocks if b["free_ns"] is not None)
    malloc_times = sorted(b["alloc_ns"] for b in blocks if b["alloc_ns"] is not None)

    for b in blocks:
        # 1. Early allocation check
        early_reasons: list[str] = []
        delay_ms: float | None = None
        delay_apis: int | None = None
        if b["malloc_api_id"] is not None and b["first_access_api_id"] is not None:
            gap_api = b["first_access_api_id"] - b["malloc_api_id"]
            intervening_free = any(b["malloc_api_id"] < f_id < b["first_access_api_id"] for f_id in free_apis)
            total_api_life = (
                (b["free_api_id"] - b["malloc_api_id"])
                if b["free_api_id"] is not None and b["free_api_id"] > b["malloc_api_id"]
                else gap_api
            )
            if gap_api >= min_api_gap and (intervening_free or (total_api_life > 0 and gap_api / total_api_life >= early_alloc_ratio_threshold)):
                delay_apis = gap_api
                early_reasons.append(
                    f"allocated {gap_api} API calls before first access"
                    + (" while preceding blocks were freed in between" if intervening_free else "")
                )
        if b["alloc_ns"] is not None and b["first_use_ns"] is not None:
            gap_ns = b["first_use_ns"] - b["alloc_ns"]
            life_ns = (
                (b["free_ns"] - b["alloc_ns"])
                if b["free_ns"] is not None and b["free_ns"] > b["alloc_ns"]
                else gap_ns
            )
            intervening_free_ns = any(b["alloc_ns"] < f_ns < b["first_use_ns"] for f_ns in free_times)
            if gap_ns >= early_ns_thresh and (intervening_free_ns or (life_ns > 0 and gap_ns / life_ns >= early_alloc_ratio_threshold)):
                delay_ms = round(gap_ns / 1_000_000.0, 6)
                early_reasons.append(f"held unused for {delay_ms:.3f} ms before first kernel access")

        if early_reasons:
            early_allocations.append(
                {
                    "pattern": "early_allocation",
                    "block_id": b["block_id"],
                    "addr": b["addr"],
                    "op_name": b["op_name"],
                    "size_bytes": b["size_bytes"],
                    "step": b["step"],
                    "delay_api_calls": delay_apis,
                    "pre_use_idle_ms": delay_ms,
                    "reasons": early_reasons,
                    "guidance": (
                        "Defer tensor allocation until immediately before its first consuming operator so "
                        "freed upstream buffers can be reused by the NPU caching allocator."
                    ),
                }
            )

        # 2. Late deallocation check
        late_reasons: list[str] = []
        retain_ms: float | None = None
        retain_apis: int | None = None
        cross_stream = bool(b["stream_id"] and b["free_stream_id"] and b["stream_id"] != b["free_stream_id"])
        if b["last_access_api_id"] is not None and b["free_api_id"] is not None:
            gap_api = b["free_api_id"] - b["last_access_api_id"]
            intervening_malloc = any(b["last_access_api_id"] < m_id < b["free_api_id"] for m_id in malloc_apis)
            total_api_life = (
                (b["free_api_id"] - b["malloc_api_id"])
                if b["malloc_api_id"] is not None and b["free_api_id"] > b["malloc_api_id"]
                else gap_api
            )
            if gap_api >= min_api_gap and (intervening_malloc or cross_stream or (total_api_life > 0 and gap_api / total_api_life >= late_free_ratio_threshold)):
                retain_apis = gap_api
                late_reasons.append(
                    f"retained {gap_api} API calls after last kernel access"
                    + (" while subsequent allocations competed for HBM" if intervening_malloc else "")
                )
        if b["last_use_ns"] is not None and b["free_ns"] is not None:
            gap_ns = b["free_ns"] - b["last_use_ns"]
            life_ns = (
                (b["free_ns"] - b["alloc_ns"])
                if b["alloc_ns"] is not None and b["free_ns"] > b["alloc_ns"]
                else gap_ns
            )
            intervening_malloc_ns = any(b["last_use_ns"] < m_ns < b["free_ns"] for m_ns in malloc_times)
            if gap_ns >= late_ns_thresh and (intervening_malloc_ns or cross_stream or (life_ns > 0 and gap_ns / life_ns >= late_free_ratio_threshold)):
                retain_ms = round(gap_ns / 1_000_000.0, 6)
                late_reasons.append(
                    f"retained unused for {retain_ms:.3f} ms after last access"
                    + (f" across streams ({b['stream_id']} -> {b['free_stream_id']})" if cross_stream else "")
                )

        if late_reasons:
            late_deallocations.append(
                {
                    "pattern": "late_deallocation",
                    "block_id": b["block_id"],
                    "addr": b["addr"],
                    "op_name": b["op_name"],
                    "size_bytes": b["size_bytes"],
                    "step": b["step"],
                    "cross_stream_retention": cross_stream,
                    "post_use_retain_api_calls": retain_apis,
                    "post_use_retain_ms": retain_ms,
                    "reasons": late_reasons,
                    "guidance": (
                        "Delete intermediate tensor references (del tensor) immediately after last operator use "
                        "and avoid extending tensor lifetimes across stream sync boundaries."
                    ),
                }
            )

        # 3. Temporary buffer spike & temporary idleness check on blocks
        spike_reasons: list[str] = []
        if b["max_access_interval"] is not None and b["max_access_interval"] >= idle_api_gap_threshold:
            spike_reasons.append(f"temporary idleness across {b['max_access_interval']} API calls between accesses")
        if b["max_idle_gap_ns"] is not None and b["max_idle_gap_ns"] >= idle_ns_thresh:
            spike_reasons.append(f"temporary idleness of {b['max_idle_gap_ns'] / 1e6:.3f} ms between accesses")
        if b["tag"] in {"workspace", "temp", "temporary", "comm_buffer", "transient"} and b["size_bytes"] > 0:
            spike_reasons.append(f"transient {b['tag']} buffer spike ({b['size_bytes'] / (1024 ** 2):.2f} MiB)")
        if spike_reasons:
            temp_spikes.append(
                {
                    "pattern": "temporary_buffer_spike",
                    "sub_type": "temporary_idleness" if "idleness" in spike_reasons[0] else "transient_workspace_spike",
                    "block_id": b["block_id"],
                    "addr": b["addr"],
                    "op_name": b["op_name"],
                    "size_bytes": b["size_bytes"],
                    "step": b["step"],
                    "reasons": spike_reasons,
                    "guidance": (
                        "Cap operator workspace pool size, reuse shared communication/workspace buffers, or "
                        "recompute/offload tensors with long intra-step idle gaps."
                    ),
                }
            )

    # Check allocator snapshots for transient spikes and external fragmentation
    for idx, snap in enumerate(snapshots):
        unit = str(snap.get("unit") or "B")
        alloc_b = (
            _opt_bytes(snap.get("allocated_bytes"), "B")
            if snap.get("allocated_bytes") is not None
            else _opt_bytes(snap.get("active_bytes") or snap.get("used_bytes") or snap.get("allocated"), unit)
        )
        res_b = (
            _opt_bytes(snap.get("reserved_bytes"), "B")
            if snap.get("reserved_bytes") is not None
            else _opt_bytes(snap.get("reserved") or snap.get(" cached_bytes"), unit)
        )
        peak_b = (
            _opt_bytes(snap.get("peak_allocated_bytes"), "B")
            if snap.get("peak_allocated_bytes") is not None
            else _opt_bytes(snap.get("max_allocated_bytes") or snap.get("peak_bytes"), unit)
        )
        step = _opt_int(snap.get("step"))

        if peak_b is not None and alloc_b is not None and alloc_b > 0 and peak_b > alloc_b:
            spike_delta = peak_b - alloc_b
            spike_ratio = spike_delta / alloc_b
            if spike_ratio >= spike_ratio_threshold:
                temp_spikes.append(
                    {
                        "pattern": "temporary_buffer_spike",
                        "sub_type": "step_peak_transient_surge",
                        "block_id": f"step_{step if step is not None else idx}_spike",
                        "addr": None,
                        "op_name": str(snap.get("peak_op") or snap.get("op_name") or "step_transient_workspace"),
                        "size_bytes": round(spike_delta, 2),
                        "steady_allocated_bytes": round(alloc_b, 2),
                        "peak_allocated_bytes": round(peak_b, 2),
                        "spike_ratio": round(spike_ratio, 6),
                        "step": step,
                        "reasons": [
                            f"Transient peak surge of {spike_delta / (1024 ** 2):.2f} MiB ({spike_ratio:.1%} above steady allocated)"
                        ],
                        "guidance": "Inspect peak operator workspace or logits materialization; chunk vocab/LM-head projection or cap HCCL/ACLNN workspace.",
                    }
                )

        if res_b is not None and res_b > 0 and alloc_b is not None and res_b >= alloc_b:
            unallocated_b = res_b - alloc_b
            frag_ratio = unallocated_b / res_b
            if frag_ratio >= high_fragmentation_threshold:
                severity = "high"
            elif frag_ratio >= moderate_fragmentation_threshold:
                severity = "moderate"
            else:
                severity = "low"
            if severity in {"high", "moderate"}:
                fragmentation_records.append(
                    {
                        "pattern": "allocator_fragmentation",
                        "step": step,
                        "allocated_bytes": round(alloc_b, 2),
                        "reserved_bytes": round(res_b, 2),
                        "unallocated_reserved_bytes": round(unallocated_b, 2),
                        "fragmentation_ratio": round(frag_ratio, 6),
                        "severity": severity,
                        "recommended_env": "PYTORCH_NPU_ALLOC_CONF=expandable_segments:True",
                        "guidance": (
                            f"NPU caching allocator holds {unallocated_b / (1024 ** 2):.2f} MiB "
                            f"({frag_ratio:.1%} of reserved HBM) in unallocated segments; set "
                            "PYTORCH_NPU_ALLOC_CONF=expandable_segments:True and pad dynamic shapes to fixed buckets."
                        ),
                    }
                )

    for label, collection, ref in (
        ("early_allocation", early_allocations, "early_allocation"),
        ("late_deallocation", late_deallocations, "late_deallocation"),
        ("temporary_buffer_spike", temp_spikes, "temporary_buffer_spike"),
        ("allocator_fragmentation", fragmentation_records, "allocator_fragmentation"),
    ):
        if not collection:
            continue
        first = collection[0]
        findings.append(
            {
                "finding_type": f"memory_{label}",
                "severity": "high" if label == "allocator_fragmentation" and first.get("severity") == "high" else "medium",
                "confidence": "high",
                "summary": (
                    f"Detected {len(collection)} {label} instance(s); "
                    + (
                        f"max fragmentation ratio {max(x['fragmentation_ratio'] for x in collection):.1%} "
                        f"(recommend {first['recommended_env']})."
                        if label == "allocator_fragmentation"
                        else f"top candidate {first['op_name']} ({first['size_bytes'] / (1024 ** 2):.2f} MiB)."
                    )
                ),
                "evidence_ref": ref,
                "evidence_scope": {"step": first.get("step"), "op_name": first.get("op_name")},
            }
        )

    max_frag = max((r["fragmentation_ratio"] for r in fragmentation_records), default=None)
    detected_any = bool(early_allocations or late_deallocations or temp_spikes or fragmentation_records)
    return {
        "status": "detected" if detected_any else ("clean" if (blocks or snapshots) else "not_applicable"),
        "early_allocation_count": len(early_allocations),
        "late_deallocation_count": len(late_deallocations),
        "temporary_buffer_spike_count": len(temp_spikes),
        "allocator_fragmentation_count": len(fragmentation_records),
        "max_fragmentation_ratio": max_frag,
        "expandable_segments_recommended": any(r["severity"] in {"high", "moderate"} for r in fragmentation_records),
        "early_allocations": early_allocations,
        "late_deallocations": late_deallocations,
        "temporary_buffer_spikes": temp_spikes,
        "allocator_fragmentation": fragmentation_records,
        "findings": findings,
    }


def detect_step_monotonic_leaks(
    step_snapshots: Sequence[Mapping[str, Any]] | None = None,
    *,
    memory_blocks: Sequence[Mapping[str, Any]] | None = None,
    warmup_steps: int = 1,
    min_post_warmup_steps: int = 3,
    min_leak_bytes: float = 1_048_576.0,
) -> dict[str, Any]:
    """Separate warmup/graph-bucket reservation growth from true post-warmup step_monotonic_leak."""
    raw_steps = [dict(s) for s in (step_snapshots or []) if isinstance(s, Mapping)]
    blocks = [_normalize_block(b, i) for i, b in enumerate(memory_blocks or []) if isinstance(b, Mapping)]

    normalized_steps: list[dict[str, Any]] = []
    for idx, row in enumerate(raw_steps):
        unit = str(row.get("unit") or "B")
        step_id = _opt_int(row.get("step"))
        if step_id is None:
            step_id = idx
        alloc_b = (
            _opt_bytes(row.get("allocated_bytes"), "B")
            if row.get("allocated_bytes") is not None
            else _opt_bytes(row.get("used_bytes") or row.get("active_bytes") or row.get("allocated"), unit)
        )
        res_b = (
            _opt_bytes(row.get("reserved_bytes"), "B")
            if row.get("reserved_bytes") is not None
            else _opt_bytes(row.get("reserved"), unit)
        )
        phase = str(row.get("phase") or "").lower()
        is_warmup = bool(row.get("is_warmup", False)) or phase == "warmup"
        if alloc_b is None and res_b is None:
            continue
        normalized_steps.append(
            {
                "step": step_id,
                "allocated_bytes": alloc_b,
                "reserved_bytes": res_b,
                "is_warmup": is_warmup,
                "phase": phase or None,
            }
        )

    normalized_steps.sort(key=lambda r: r["step"])
    # Identify HAL / PTA unfreed or shadow-exit-freed candidate blocks
    leaked_candidates = [
        {
            "block_id": b["block_id"],
            "addr": b["addr"],
            "op_name": b["op_name"],
            "size_bytes": b["size_bytes"],
            "attr": b["attr"],
            "step": b["step"],
            "shadow_exit_free": b["shadow"],
            "leak_layer": "HAL" if b["attr"] == "HAL" else "PTA",
        }
        for b in blocks
        if b["unfreed"] or b["shadow"]
    ]

    if len(normalized_steps) < warmup_steps + min_post_warmup_steps:
        return {
            "status": "insufficient_steps",
            "classification": "insufficient_steps",
            "leak_detected": False,
            "step_count": len(normalized_steps),
            "post_warmup_step_count": max(0, len(normalized_steps) - warmup_steps),
            "warmup_growth_bytes": None,
            "total_post_warmup_growth_bytes": None,
            "leak_rate_bytes_per_step": None,
            "reserved_bucket_growth_bytes": None,
            "leaked_block_candidates": leaked_candidates,
            "findings": [],
        }

    explicit_warmup = [s for s in normalized_steps if s["is_warmup"]]
    if explicit_warmup:
        post_warmup = [s for s in normalized_steps if not s["is_warmup"]]
        warmup_slice = explicit_warmup
    else:
        warmup_slice = normalized_steps[: max(0, warmup_steps)]
        post_warmup = normalized_steps[max(0, warmup_steps) :]

    if len(post_warmup) < min_post_warmup_steps:
        return {
            "status": "insufficient_steps",
            "classification": "insufficient_steps",
            "leak_detected": False,
            "step_count": len(normalized_steps),
            "post_warmup_step_count": len(post_warmup),
            "warmup_growth_bytes": None,
            "total_post_warmup_growth_bytes": None,
            "leak_rate_bytes_per_step": None,
            "reserved_bucket_growth_bytes": None,
            "leaked_block_candidates": leaked_candidates,
            "findings": [],
        }

    alloc_series = [
        s["allocated_bytes"] if s["allocated_bytes"] is not None else s["reserved_bytes"]
        for s in post_warmup
    ]
    res_series = [
        s["reserved_bytes"] if s["reserved_bytes"] is not None else s["allocated_bytes"]
        for s in post_warmup
    ]

    first_warm_alloc = (
        warmup_slice[0]["allocated_bytes"]
        if warmup_slice and warmup_slice[0]["allocated_bytes"] is not None
        else alloc_series[0]
    )
    warmup_growth = round(float(alloc_series[0] - first_warm_alloc), 2) if (first_warm_alloc is not None and alloc_series[0] is not None) else 0.0

    deltas = [alloc_series[i + 1] - alloc_series[i] for i in range(len(alloc_series) - 1)]
    res_deltas = [res_series[i + 1] - res_series[i] for i in range(len(res_series) - 1)]
    total_post_growth = round(float(alloc_series[-1] - alloc_series[0]), 2)
    reserved_post_growth = round(float(res_series[-1] - res_series[0]), 2)

    non_decreasing = all(d >= 0 for d in deltas)
    positive_steps = sum(1 for d in deltas if d > 0)
    positive_ratio = positive_steps / float(len(deltas)) if deltas else 0.0
    never_returned_to_baseline = all(val > alloc_series[0] for val in alloc_series[1:])

    is_monotonic_leak = (
        non_decreasing
        and positive_ratio >= 0.80
        and never_returned_to_baseline
        and total_post_growth >= min_leak_bytes
    )

    findings: list[dict[str, Any]] = []
    if is_monotonic_leak:
        classification = "step_monotonic_leak"
        leak_rate = round(total_post_growth / float(len(deltas)), 2)
        findings.append(
            {
                "finding_type": "memory_step_monotonic_leak",
                "severity": "high",
                "confidence": "high",
                "summary": (
                    f"Post-warmup step_monotonic_leak detected across steps "
                    f"{[s['step'] for s in post_warmup]}: allocated memory grew monotonically by "
                    f"{total_post_growth / (1024 ** 2):.2f} MiB ({leak_rate / (1024 ** 2):.3f} MiB/step)."
                ),
                "evidence_ref": "step_monotonic_leak",
                "evidence_scope": {
                    "post_warmup_steps": [s["step"] for s in post_warmup],
                    "leak_rate_bytes_per_step": leak_rate,
                    "total_post_warmup_growth_bytes": total_post_growth,
                },
            }
        )
    elif warmup_growth > 0 or reserved_post_growth > 0 or any(d > 0 for d in res_deltas):
        classification = "warmup_or_bucket_reservation_growth"
        leak_rate = 0.0
    else:
        classification = "stable"
        leak_rate = 0.0

    return {
        "status": "detected" if is_monotonic_leak else "clean",
        "classification": classification,
        "leak_detected": is_monotonic_leak,
        "step_count": len(normalized_steps),
        "warmup_steps": [s["step"] for s in warmup_slice],
        "post_warmup_steps": [s["step"] for s in post_warmup],
        "post_warmup_allocated_bytes": [round(float(x), 2) for x in alloc_series],
        "post_warmup_reserved_bytes": [round(float(x), 2) for x in res_series],
        "warmup_growth_bytes": warmup_growth,
        "total_post_warmup_growth_bytes": total_post_growth,
        "reserved_bucket_growth_bytes": reserved_post_growth,
        "leak_rate_bytes_per_step": leak_rate,
        "positive_step_transition_ratio": round(positive_ratio, 4),
        "leaked_block_candidates": leaked_candidates,
        "guidance": (
            "Inspect Python history lists, KV/request metadata tables, or unfreed C++/PTA tensors "
            "accumulating per decode step; use msmemscope MSTX mark A/B/C diffing to isolate leaked blocks."
            if is_monotonic_leak
            else (
                "Observed memory increase is bounded warmup or caching-allocator bucket reservation growth, "
                "not a per-step monotonic leak."
                if classification == "warmup_or_bucket_reservation_growth"
                else None
            )
        ),
        "findings": findings,
    }


def run_memory_forensics(
    manifest: Mapping[str, Any] | None = None,
    *,
    memory_blocks: Sequence[Mapping[str, Any]] | None = None,
    allocator_snapshots: Sequence[Mapping[str, Any]] | None = None,
    step_snapshots: Sequence[Mapping[str, Any]] | None = None,
    warmup_steps: int = 1,
    min_post_warmup_steps: int = 3,
    min_leak_bytes: float = 1_048_576.0,
) -> dict[str, Any]:
    """Run both memory inefficiency pattern scanning and step-monotonic leak detection."""
    if isinstance(manifest, Mapping):
        if memory_blocks is None:
            memory_blocks = manifest.get("memory_blocks") or manifest.get("block_events")
        if allocator_snapshots is None:
            allocator_snapshots = manifest.get("allocator_snapshots") or manifest.get("step_snapshots")
        if step_snapshots is None:
            step_snapshots = manifest.get("step_snapshots") or manifest.get("allocator_snapshots")

    inefficiencies = analyze_memory_inefficiencies(
        memory_blocks,
        allocator_snapshots=allocator_snapshots,
    )
    leaks = detect_step_monotonic_leaks(
        step_snapshots,
        memory_blocks=memory_blocks,
        warmup_steps=warmup_steps,
        min_post_warmup_steps=min_post_warmup_steps,
        min_leak_bytes=min_leak_bytes,
    )
    return {
        "schema_version": MEMORY_FORENSICS_SCHEMA,
        "inefficiencies": inefficiencies,
        "step_leak_analysis": leaks,
        "findings": [*inefficiencies["findings"], *leaks["findings"]],
    }


__all__ = [
    "MEMORY_FORENSICS_SCHEMA",
    "analyze_memory_inefficiencies",
    "detect_step_monotonic_leaks",
    "run_memory_forensics",
]
