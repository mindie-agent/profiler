"""Compare explicit device-body spans with the shared Sim graph scheduler.

[Role] Project Sim's public body-forward result onto profiler span boundaries.
[Invariants] Layer durations are first-kernel-ready/output-complete envelopes,
  never sums of kernel activity. Replica/stage envelopes are not additive.
  Unidentified geometry or a different measurement boundary stays unscored.
[Timeouts & Locks] One finite body graph; no history, subprocesses or locks.
[Side-Effect Policy] Local CPU simulation and optional explicit report write only.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
from statistics import median
import resource
import sys
import time


GEOMETRY_FIELDS = (
    "phase", "tokens_per_sequence", "context_tokens", "sequences_per_replica",
    "participating_replicas",
)
BOUNDARY = "target_body_device_graph"


def _stats(values):
    ordered = sorted(values)
    return {
        "count": len(values), "mean": sum(values) / len(values) if values else None,
        "p50": median(values) if values else None,
        "p90": ordered[math.ceil(len(values) * .9) - 1] if values else None,
        "min": min(values, default=None), "max": max(values, default=None),
    }


def _layer_activity_distribution(rows, field):
    """Aggregate available layer means without treating absent activity as zero."""
    values = [row[field]["mean"] for row in rows
              if row.get(field) and row[field].get("count") and row[field].get("mean") is not None]
    return _stats(values) if values else None


def _steady_layer_group(rows, *, attention_kind=None):
    """Summarize retained layer statistics without inventing pooled call quantiles."""
    means = _stats([row["observed_ms"]["mean"] for row in rows])
    call_medians = _stats([row["observed_ms"]["p50"] for row in rows
                          if row["observed_ms"].get("p50") is not None])
    predicted = _stats([row["predicted_ms"] for row in rows])
    observed_p50 = call_medians["p50"]
    error = ((predicted["p50"] - observed_p50) / observed_p50
             if observed_p50 and call_medians["count"] == len(rows) else None)
    return {
        "attention_kind": attention_kind, "layer_ids": [row["layer_id"] for row in rows],
        "layer_count": len(rows),
        "observed_call_count": sum(row["observed_ms"]["count"] for row in rows),
        "calls_per_layer_range": [min((row["observed_ms"]["count"] for row in rows), default=0),
                                  max((row["observed_ms"]["count"] for row in rows), default=0)],
        "observed_layer_mean_ms": means,
        "observed_layer_call_p50_ms": call_medians,
        "predicted_layer_ms": predicted,
        "comparison": {
            "observed_basis": "median_of_layer_call_p50",
            "predicted_basis": "median_of_declared_layer_predictions",
            "observed_ms": observed_p50, "predicted_ms": predicted["p50"],
            "relative_error": error, "passed": abs(error) <= .15 if error is not None else None,
        },
    }


def _steady_layers(comparisons):
    rows = [row for row in comparisons if row["layer_id"] != 0 and row["status"] == "compared"]
    kinds = defaultdict(list)
    for row in rows:
        kinds[row["attention_kind"]].append(row)
    return {
        "excluded_layer_ids": [0], "body_span_modified": False,
        "quantile_scope": "Each observed layer P50 uses all its Forward calls; the steady P50 is the median of those layer P50s, not a pooled quantile over all calls.",
        "population": _steady_layer_group(rows),
        "attention_groups": [_steady_layer_group(group, attention_kind=kind)
                             for kind, group in sorted(kinds.items())],
        "excluded_layers": [row for row in comparisons if row["layer_id"] == 0],
    }


def compare_pooled_layers(steady, pooled):
    """Compare exact observed invocation quantiles with repeated model layer spans."""
    compared = []
    expected = {group["attention_kind"]: group
                for group in [steady["population"], *steady["attention_groups"]]}
    for group in pooled["groups"]:
        predicted = expected[group["attention_kind"]]
        if group["layer_ids"] != predicted["layer_ids"]:
            raise ValueError("pooled_steady_layer_population_differs")
        count = pooled["forward_count"] * predicted["layer_count"]
        if (count != group["stats"]["count"] or count != predicted["observed_call_count"]
                or predicted["calls_per_layer_range"] != [pooled["forward_count"]] * 2):
            raise ValueError("pooled_steady_layer_multiplicity_differs")
        real = group["stats"]["p50"]
        modeled = predicted["predicted_layer_ms"]["p50"]
        error = (modeled - real) / real if real else None
        compared.append({
            "attention_kind": group["attention_kind"], "layer_ids": group["layer_ids"],
            "layer_count": predicted["layer_count"], "forward_count": pooled["forward_count"],
            "observed_call_count": count, "observed_ms": group["stats"],
            "predicted_ms": {**predicted["predicted_layer_ms"], "count": count},
            "predicted_population_basis": "Each declared layer prediction repeats once per matched Forward; equal multiplicity preserves its median.",
            "relative_error_vs_p50": error,
            "passed_vs_p50": abs(error) <= .15 if error is not None else None,
        })
    return {"observed_basis": "exact_pooled_layer_invocation_spans_excluding_layer_0",
            "body_span_modified": False, "groups": compared}


def summarize_prediction(case, result):
    """Preserve the graph completion span; project complete semantic timelines."""
    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(case)
    timeline = result["timeline"]
    complete = (
        result.get("schema") == "mindie-sim.body-forward/1"
        and result.get("metric_boundary") == BOUNDARY
        and sum(row["family"] != "barrier" for row in timeline)
        == result["operator_occurrences"]
    )
    grouped, replicas = defaultdict(list), defaultdict(list)
    kernel_rows = [row for row in timeline if row["family"] != "barrier"]
    first_kernel_ready = min((row["ready_ms"] for row in kernel_rows), default=None)
    for row in timeline:
        replicas[row["replica"]].append(row)
        if row["layer"] >= 0:
            grouped[row["replica"], row["stage"], row["layer"]].append(row)
    layers, kinds = [], defaultdict(list)
    for (replica, stage, layer), rows in sorted(grouped.items()):
        plan = parsed.model.layer_plans[layer]
        kernels = [row for row in rows if row["family"] != "barrier"]
        start = min(row["ready_ms"] for row in kernels)
        end = max(row["complete_ms"] for row in kernels)
        kind = "moe_layer" if plan.ffn == "moe" else "dense_layer"
        layers.append({
            "replica": replica, "stage": stage, "layer_id": layer, "kind": kind,
            "attention_kind": plan.attention, "ffn_kind": plan.ffn,
            "start_ms": start, "end_ms": end, "span_ms": end - start,
            "operator_count": sum(row["family"] != "barrier" for row in rows),
            "metric_boundary": "first_layer_kernel_invocation_ready_to_last_kernel_complete",
        })
        kinds[replica, stage, kind].append(end - start)
    return {
        "schema_version": "mindie-profile-body-prediction/1",
        "status": "modeled" if complete else "partial",
        "model_name": parsed.model.name, "metric_boundary": result["metric_boundary"],
        "span_start_basis": "input_hidden_and_kv_ready",
        "span_end_basis": "target_body_output_ready_on_all_cohort_participants",
        "geometry": result["geometry"],
        "body_forward_span_ms": result["body_forward_ms"],
        "first_kernel_ready_ms": first_kernel_ready,
        "first_kernel_to_body_complete_ms": (
            result["complete_ms"] - first_kernel_ready if first_kernel_ready is not None else None),
        "kernel_endpoint_basis": "first_kernel_invocation_ready_to_body_complete_including_startup",
        "per_layer_ms": layers,
        "layer_distributions_ms": [
            {"replica": replica, "stage": stage, "kind": kind,
             "statistic_scope": "across_declared_layers_in_one_forward",
             "stats": _stats(values)}
            for (replica, stage, kind), values in sorted(kinds.items())
        ],
        "replica_envelopes_ms": [
            {"replica": replica,
             "span_ms": max(row["complete_ms"] for row in rows)
             - min(row.get("local_ready_ms", row["ready_ms"]) for row in rows)}
            for replica, rows in sorted(replicas.items())
        ],
        "timeline_complete": complete,
        "timeline_count": len(timeline),
        "operator_occurrences": result["operator_occurrences"],
        "body_unassigned_operator_count": sum(
            row["layer"] < 0 and row["family"] != "barrier" for row in timeline),
        "boundary_details": result["boundary_details"],
        "interpretation": (
            "Body span is scheduler completion, not a sum of layer envelopes. "
            "Dense/MoE identifies the layer FFN; its attention remains attention. "
            "Embedding, final norm, LM head and MTP/draft are excluded, not zero-cost."
        ),
    }


def predict_body(case, *, tokens, context, sequences=1, phase="decode"):
    """Use the selected Sim API; its semantic timeline is independent of trace caps."""
    from mindie_sim import predict

    result = predict(case, scope="body", phase=phase, tokens=tokens,
                     context=context, sequences=sequences, event_limit=0)
    return summarize_prediction(case, result)


def compare_body_forward(predicted, observed):
    """Score only the shared target-body boundary and explicitly equal geometry.

    ``participating_replicas`` describes the measured boundary, not a guessed
    conversion of physical rank IDs. Automatic single-rank alignment is compared
    conditionally under exchange symmetry; full-cohort observation is not claimed.
    """
    reasons = []
    if predicted.get("status") != "modeled" or not predicted.get("timeline_complete"):
        reasons.append("prediction_timeline_incomplete")
    if observed.get("status") not in {"measured", "partial"}:
        reasons.append("measured_forward_boundary_unresolved")
    if observed.get("metric_boundary") != predicted.get("metric_boundary"):
        reasons.append("forward_metric_boundary_differs")
    automatic = observed.get("basis") == "structure_guided_topology_alignment"
    scope = observed.get("comparison_scope") or {}
    assumptions = list(observed.get("comparison_assumptions", []))
    if automatic:
        assumptions.append("Captured rank represents the declared balanced, exchange-symmetric cohort; this is conditional, not measured all-rank coverage.")
    if predicted.get("first_kernel_to_body_complete_ms") is None:
        reasons.append("prediction_first_kernel_endpoint_missing")
    for field in GEOMETRY_FIELDS:
        left, right = (observed.get("geometry") or {}).get(field), predicted["geometry"].get(field)
        if left is None:
            if automatic and field == "participating_replicas":
                continue
            reasons.append(f"observed_geometry_missing:{field}")
        elif left != right:
            if not (automatic and field == "participating_replicas"):
                reasons.append(f"geometry_differs:{field}")
    stats = observed.get("body_forward_span_ms", {})
    count, mean = stats.get("count", 0), stats.get("mean")
    if not count or not isinstance(mean, (int, float)) or not math.isfinite(mean) or mean <= 0:
        reasons.append("positive_complete_forward_samples_unavailable")
    result = {
        "status": "unresolved" if reasons else "compared",
        "metric_boundary": predicted.get("metric_boundary"),
        "reasons": reasons, "observed_forward_count": count,
        "observed_ms": stats, "predicted_ms": predicted["first_kernel_to_body_complete_ms"],
        "relative_error": None, "per_forward_diff_ms": None, "passed": None,
        "tolerance": {"kind": "relative", "limit": .15,
                      "scope": "whole_body_forward_not_single_kernel_launch"},
        "comparison_scope": scope,
        "comparison_basis": "conditional_single_rank_topology_alignment" if automatic else "explicit_body_boundary",
        "assumptions": assumptions,
        "endpoints": {
            "observed": "first_retained_device_event_start_to_last_retained_device_event_end",
            "predicted": predicted["kernel_endpoint_basis"],
            "input_ready_to_first_kernel_ms": predicted["first_kernel_ready_ms"],
            "kernel_startup_included": True,
        },
    }
    if not reasons:
        difference = predicted["first_kernel_to_body_complete_ms"] - mean
        result.update(relative_error=difference / mean, per_forward_diff_ms=difference,
                      passed=abs(difference / mean) <= .15)
    return result


def compare_layers(predicted, observed):
    """Collapse symmetric DP copies to one representative, without summing them."""
    replica = min((row["replica"] for row in predicted["per_layer_ms"]), default=None)
    indexed = {row["layer_id"]: row for row in predicted["per_layer_ms"] if row["replica"] == replica}
    comparisons, grouped, attention = [], defaultdict(list), defaultdict(list)
    for row in observed.get("per_layer_ms", []):
        layer = indexed.get(row["layer_id"])
        stats = row["stats"]
        value = stats.get("mean")
        result = {"layer_id": row["layer_id"], "kind": row["kind"], "rank_id": row.get("rank_id"),
                  "attention_kind": layer["attention_kind"] if layer else None,
                  "representative_replica": replica, "observed_ms": stats,
                  "observed_activity_ms": row.get("activity_ms_stats"),
                  "observed_internal_gap_ms": row.get("internal_gap_ms_stats"),
                  "predicted_ms": layer["span_ms"] if layer else None,
                  "relative_error": None, "passed": None, "status": "unresolved", "reasons": []}
        if layer is None:
            result["reasons"].append("declared_layer_missing")
        elif layer["kind"] != row["kind"]:
            result["reasons"].append("layer_ffn_kind_differs")
        elif not stats["count"] or value is None or value <= 0:
            result["reasons"].append("positive_layer_samples_missing")
        else:
            error = (layer["span_ms"] - value) / value
            result.update(status="compared", relative_error=error, passed=abs(error) <= .15)
            grouped[row["kind"]].append(result)
            attention[layer["attention_kind"]].append(result)
        comparisons.append(result)
    return {
        "basis": "conditional_topology_layer_alignment_single_representative_replica",
        "endpoint": "first_layer_kernel_invocation_to_last_layer_kernel_completion",
        "assumptions": ["Captured layer ordinal follows the declared full topology; this is not a Host occurrence binding.",
                        "One representative DP replica is compared under exchange symmetry; replicas are not summed."],
        "layers": comparisons,
        "summary": {"observed_layers": len(comparisons), "declared_layers": len(indexed),
                    "compared_layers": sum(row["status"] == "compared" for row in comparisons),
                    "passed_layers": sum(row["passed"] is True for row in comparisons)},
        "steady_layer_comparison": _steady_layers(comparisons),
        "ffn_kind_distributions": [
            {"kind": kind, "statistic_scope": "across_layer_means_in_this_geometry",
             "observed_ms": _stats([row["observed_ms"]["mean"] for row in rows]),
             "predicted_ms": _stats([row["predicted_ms"] for row in rows]),
             "observed_activity_ms": _layer_activity_distribution(rows, "observed_activity_ms"),
             "observed_internal_gap_ms": _layer_activity_distribution(rows, "observed_internal_gap_ms")}
            for kind, rows in sorted(grouped.items())],
        "attention_kind_distributions": [
            {"attention_kind": kind, "statistic_scope": "across_complete_layer_means_in_this_geometry",
             "observed_ms": _stats([row["observed_ms"]["mean"] for row in rows]),
             "predicted_ms": _stats([row["predicted_ms"] for row in rows]),
             "observed_activity_ms": _layer_activity_distribution(rows, "observed_activity_ms"),
             "observed_internal_gap_ms": _layer_activity_distribution(rows, "observed_internal_gap_ms"),
             "compared_layers": len(rows),
             "passed_layers": sum(row["passed"] is True for row in rows)}
            for kind, rows in sorted(attention.items())],
    }


def _load(path):
    if path.stat().st_size > 50 * 1024 ** 2:
        raise ValueError(f"body_report_too_large:{path}")
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, type=Path)
    parser.add_argument("--tokens", required=True, type=int)
    parser.add_argument("--context", required=True, type=int)
    parser.add_argument("--sequences", type=int, default=1)
    parser.add_argument("--phase", choices=("decode", "prefill"), default="decode")
    parser.add_argument("--observed", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    result = {"prediction": predict_body(
        _load(args.case), tokens=args.tokens, context=args.context,
        sequences=args.sequences, phase=args.phase)}
    if args.observed:
        result["comparison"] = compare_body_forward(result["prediction"], _load(args.observed))
    # Decode getrusage units only; this does not select an execution host.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    result["execution"] = {"elapsed_seconds": time.perf_counter() - started,
                           "peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024)}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["prediction"]["status"],
                      "body_forward_span_ms": result["prediction"]["body_forward_span_ms"],
                      "comparison": result.get("comparison", {}).get("status")}))


if __name__ == "__main__":
    main()
