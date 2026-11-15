"""Independent raw-observation boundary reconstruction for A5 fleet rows.

Reads the exact retained export only.  It tests whether kernel marker sequences
provide a consistent per-forward interval candidate; otherwise it names the
observable source unit actually present (per-rank kernel aggregate, request
schedule, operator aggregate, or missing raw).  It does not use E3 records,
op additive sums, idle gaps, layer counts, fitted times, or neighbor ranks.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import fleet_campaign_case as campaign
import fleet_campaign_geometry as geometry


def _rack_host_alignment(row: Mapping[str, Any], directory) -> dict[str, Any]:
    scope = campaign._scope(row)
    if scope is None or scope.get("kind") != "rack":
        return {"applicable": False, "ok": None}
    root = next((base / scope["workstream"] for base in campaign.WORKSTREAM_ROOTS
                 if (base / scope["workstream"]).is_dir()), None)
    spec = campaign._read_json(root / "cases" / f"{scope['case']}.json") if root else None
    nodes = [str(item) for item in (spec or {}).get("nodes") or ()]
    node = Path(directory).parent.name
    return {"applicable": True, "node": node, "declared_nodes": nodes,
            "ok": bool(nodes) and node in nodes}


def _marker_consistency(ordinal: Mapping[str, Any], declared_steps: int | None) -> dict[str, Any]:
    by = ordinal.get("by_marker") or {}
    candidates = {key: value for key, value in by.items() if value.get("intervals_with_shapes")}
    if not candidates:
        return {"consistent": False, "reason": "no_attention_marker_intervals"}
    counts = {key: value.get("marker_count") for key, value in candidates.items()}
    if len(set(counts.values())) > 1 and abs((counts.get("combine") or 0) - (counts.get("slot") or 0)) > 1:
        return {"consistent": False, "reason": "marker_types_disagree", "marker_counts": counts}
    key = "combine" if "combine" in candidates else next(iter(candidates))
    chosen = candidates[key]
    if not declared_steps:
        return {"consistent": False, "reason": "declared_forward_steps_absent"}
    if abs(int(chosen.get("marker_count") or 0) - int(declared_steps)) > 1:
        return {"consistent": False, "reason": "marker_count_not_declared_steps",
                "marker_count": chosen.get("marker_count"), "declared_steps": declared_steps}
    intervals = list(chosen.get("q_by_ordinal") or ())
    empty = [item["ordinal"] for item in intervals if not item.get("q_counts")]
    if empty:
        return {"consistent": False, "reason": "blank_marker_interval",
                "empty_ordinals": empty, "marker_count": chosen.get("marker_count"),
                "published_interval_count": len(intervals)}
    if not chosen.get("retained_rank_decode_query_identified"):
        return {"consistent": False, "reason": "decode_query_not_single",
                "decode_q_values": chosen.get("decode_q_values"),
                "mixed_decode_ordinals": chosen.get("mixed_decode_ordinals")}
    row_counts = [sum(item.get("q_counts", {}).values()) for item in intervals]
    if len(set(row_counts)) > 1:
        return {"consistent": False, "reason": "attention_rows_per_interval_disagree",
                "attention_rows_per_interval": sorted(set(row_counts))}
    marker_count = int(chosen.get("marker_count") or 0)
    return {"consistent": True, "marker_type": key, "marker_count": marker_count,
            "published_interval_count": len(intervals),
            "complete_span_count": marker_count - 1,
            "tail_span_count": 1,
            "layers_per_interval": row_counts[0] if row_counts else None,
            "layer_signature": {"layers_per_interval": row_counts[0] if row_counts else None,
                               "marker_count": marker_count,
                               "complete_span_count": marker_count - 1,
                               "tail_span_count": 1},
            "declared_steps": declared_steps,
            "delta": chosen.get("marker_step_delta"),
            "decode_q_values": chosen.get("decode_q_values"),
            "prefill_ordinals": chosen.get("prefill_ordinals")}


def reconstruct_observation_boundary(row: Mapping[str, Any], *,
                                     override=None,
                                     max_num_seqs: int | None = None) -> dict[str, Any]:
    """Return the real observable unit and, only when consistent, a marker candidate."""
    scope_id = campaign._scope(row)
    if scope_id is None:
        return {"capture_id": row.get("capture_id"), "status": "invalid_id",
                "source_unit": "missing_raw", "boundary": None,
                "id_status": "not_an_original_export_id"}
    binding = geometry.probe_rank_binding(row, override=override)
    if binding is None:
        return {"capture_id": row.get("capture_id"), "status": "no_source",
                "source_unit": "missing_raw", "boundary": None}
    host_alignment = _rack_host_alignment(row, binding["directory"])
    if host_alignment.get("ok") is False:
        return {"capture_id": row.get("capture_id"), "status": "host_mismatch",
                "source_unit": "missing_raw", "host_alignment": host_alignment,
                "source_hashes": {}, "boundary": None}
    ordinal = geometry.forward_ordinal_candidates(row, override=override, max_num_seqs=max_num_seqs)
    declared = (ordinal or {}).get("declared_forward_steps")
    consistency = _marker_consistency(ordinal or {}, declared)
    source_unit = "per_forward_marker_interval" if consistency.get("consistent") else None
    if source_unit is None:
        if (binding.get("request_schedule") or {}).get("present"):
            source_unit = "request_schedule"
        elif (binding.get("kernel") or {}).get("rows"):
            source_unit = "per_rank_kernel_aggregate"
        elif (Path(binding["directory"]) / "op_statistic.csv").is_file():
            source_unit = "operator_aggregate"
        else:
            source_unit = "missing_raw"
    scope = {
        "capture_id": row.get("capture_id"),
        "id_status": "original_export_id",
        "phase": row.get("phase"),
        "status": "marker_interval_candidate" if consistency.get("consistent") else "no_forward_boundary",
        "source_unit": source_unit,
        "rank": (binding.get("profiler_info") or {}).get("rank_id"),
        "worker_rank": binding.get("worker_rank"),
        "device_ids": (binding.get("kernel") or {}).get("device_ids"),
        "host": (binding.get("host") or {}).get("node"),
        "source_hashes": {
            "kernel": (binding.get("kernel") or {}).get("sha256"),
            "profiler": (binding.get("profiler_info") or {}).get("sha256"),
            "request": (binding.get("request_schedule") or {}).get("sha256"),
            "step": (binding.get("step_trace") or {}).get("sha256"),
        },
        "binding": binding.get("binding"),
        "host_alignment": host_alignment,
        "marker_consistency": consistency,
        "declared_forward_steps": declared,
        "coverage_tag": ("marker_interval_candidate" if consistency.get("consistent")
                         else "structural_upper_bound" if binding.get("kernel", {}).get("rows")
                         else "missing_raw"),
    }
    if consistency.get("consistent"):
        chosen = (ordinal.get("by_marker") or {}).get(consistency["marker_type"]) or {}
        scope["intervals"] = [{"ordinal": item["ordinal"], "q_counts": item["q_counts"],
                              "decode_q_counts": item["decode_q_counts"]}
                             for item in chosen.get("q_by_ordinal") or ()]
    return scope


def affected_population(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Exact row counts by stack/role and observable source unit."""
    from collections import Counter
    import fleet_campaign_case as campaign

    counts: Counter[str] = Counter()
    for row in rows:
        scope = campaign._scope(row)
        if scope is None:
            continue
        role = f"{scope['kind']}:{'idle' if scope.get('idle') else 'primary'}"
        counts[role] += 1
        counts["total"] += 1
    return dict(counts)
