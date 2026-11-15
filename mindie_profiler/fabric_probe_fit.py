"""Nonnegative piecewise fits for topology-qualified HCCL fabric samples.

[Role]
  Parse JSON/JSONL probe output, keep per-rank raw evidence, fit one
  ``(alpha_us, beta_ns_per_byte)`` model per ``(tier, op, group_size, protocol,
  regime)`` condition, and publish a calibrated profile with explicit
  uncertainty, holdout error, missing/unidentified tiers and a congestion
  factor computed from separate isolated and loaded fits.

[Invariants]
  * Distinct collectives are never pooled; the fit key includes the operation,
    group size and protocol.
  * Alpha and beta are nonnegative.  A decreasing measured curve is reported as
    a monotonicity violation, never clamped into a fake negative bandwidth.
  * A single message size cannot yield a slope: beta is ``None`` and the fit is
    ``single_size``/``insufficient``.  Such a profile is not usable as a link
    override.
  * A congestion factor requires separate isolated and loaded regimes at a
    common size.  It is never derived from the same already-loaded samples.
  * Samples whose tier/operation cannot be identified are listed as
    ``unidentified``; no tier is fabricated.
  * Qualification requires ``validated is True``, an explicit in-group rank and
    compatible ``group_ranks``.  Unverified topology can never be an override.
  * Explicit terminal failure/control markers dominate numeric measurement
    fields and wrapper metadata, even with ``validated=True``.

[Timeouts & Locks]
  Pure in-memory arithmetic; at most O(sizes^2) piecewise candidates.

[Side-Effect Policy]
  No I/O, subprocesses or hardware access.
"""

from __future__ import annotations

import json, math
from typing import Any, Mapping, Sequence

from .events import ProfilerUsageError
from .fabric_probe_samples import (
    _CONTROL_KINDS, _RUN_FAILURE_STATUS, _document_items, _num,
    _terminal_evidence, parse_fabric_probe_samples,
)
from .repro_values import bounded_count, bounded_sequence, bounded_summary, diagnostic_value, validate_container_depth, decode_bounded_json

PROFILE_SCHEMA = "mindie-calibrated-fabric-profile/2"
REGIMES = ("isolated", "loaded")
OPS = ("all_reduce", "all_gather", "reduce_scatter", "all_to_all", "send_recv")
_EVIDENCE_REASONS = frozenset({"validated_absent", "rank_absent",
                               "group_ranks_absent"})
def _finite_result(value):
    """No derived coefficient, reciprocal, prediction or profile may be NaN/Inf."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ProfilerUsageError("fabric fit produced a non-finite numeric result")
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, (list, tuple)):
            pending.extend(item)
    return value

def _published_profile(profile):
    """Check the actual strict-JSON values, including positive rates/ratios."""
    published = json.loads(json.dumps(_finite_result(profile), allow_nan=False))
    pending = [published]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            beta, bandwidth = item.get("beta_ns_per_byte"), item.get("bandwidth_gbps")
            if "beta_ns_per_byte" in item:
                if item["alpha_us"] < 0 or (beta is not None and beta < 0):
                    raise ProfilerUsageError("published fabric coefficients must be nonnegative")
            if "bandwidth_gbps" in item:
                if (beta and (bandwidth is None or bandwidth <= 0 or
                              not math.isclose(beta * bandwidth, 1., rel_tol=1e-12))) or (
                        not beta and bandwidth is not None):
                    raise ProfilerUsageError("published fabric bandwidth must match its positive reciprocal")
            evidence = item.get("congestion_evidence")
            if evidence:
                predictions = [evidence[key]["alpha_us"] + evidence[key]["beta_ns_per_byte"] *
                               evidence["bytes"] / 1000. for key in ("isolated", "loaded")]
                factor = item["congestion_factor"]
                if (not all(math.isfinite(v) and v > 0 for v in predictions) or
                        factor is None or factor <= 0 or not math.isclose(
                            factor, predictions[1] / predictions[0], rel_tol=1e-12)):
                    raise ProfilerUsageError("published fabric congestion must match its positive predictions")
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return published

def _weighted_fit(points: Sequence[tuple[float, float]],
                  weights: Sequence[float]) -> dict[str, Any]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    sw = sum(weights)
    mean_x = sum(w * x for w, x in zip(weights, xs)) / sw
    mean_y = sum(w * y for w, y in zip(weights, ys)) / sw
    sxx = sum(w * (x - mean_x) ** 2 for w, x in zip(weights, xs))
    sxy = sum(w * (x - mean_x) * (y - mean_y) for w, x, y in zip(weights, xs, ys))
    syy = sum(w * (y - mean_y) ** 2 for w, y in zip(weights, ys))
    candidates = []
    if sxx > 0:
        slope = sxy / sxx
        alpha = mean_y - slope * mean_x
        candidates.append((alpha, slope))
    sxx_raw = sum(w * x * x for w, x in zip(weights, xs))
    sxy_raw = sum(w * x * y for w, x, y in zip(weights, xs, ys))
    # Both nonnegative boundaries are projected and compared by SSE: the
    # origin-constrained slope is sum(wxy)/sum(wx^2), NOT the unconstrained
    # slope sxy/sxx.  For (1,1),(2,4) this is (0, 1.8), SSE 0.8.
    candidates.append((0.0, max(0.0, sxy_raw / sxx_raw) if sxx_raw > 0 else 0.0))
    candidates.append((max(0.0, mean_y), 0.0))
    candidates.append((0.0, 0.0))
    best = None
    for alpha, slope in candidates:
        if alpha < 0 or slope < 0:
            continue
        sse = sum(w * (y - (alpha + slope * x)) ** 2
                  for w, x, y in zip(weights, xs, ys))
        if best is None or sse < best[0]:
            best = (sse, alpha, slope)
    sse, alpha, slope = best or (syy, 0.0, 0.0)
    r2 = 1.0 - sse / syy if syy > 0 else 1.0
    sigma2 = sse / max(1, len(points) - 2)
    se_alpha = math.sqrt(max(0.0, sigma2 * (1.0 / sw + mean_x ** 2 / sxx))) if sxx else None
    se_beta = math.sqrt(max(0.0, sigma2 / sxx)) if sxx else None
    return _finite_result({"alpha_us": max(0.0, alpha), "beta_ns_per_byte": max(0.0, slope * 1000.0),
            "sse": sse, "syy": syy, "r2_weighted": r2,
            "se_alpha_us": se_alpha,
            "se_beta_ns_per_byte": None if se_beta is None else se_beta * 1000.0})

def _fit_points(points: Sequence[tuple[int, float]]) -> dict[str, Any]:
    if not points:
        return {"fit_quality": "empty", "alpha_us": 0.0, "beta_ns_per_byte": None,
                "r2_weighted": 0.0, "sample_count": 0, "size_count": 0}
    grouped: dict[int, list[float]] = {}
    for nbytes, latency in points:
        grouped.setdefault(int(nbytes), []).append(latency)
    sizes = sorted(grouped)
    means = {size: sum(values) / len(values) for size, values in grouped.items()}
    weights = {size: 1.0 / max(1e-9, _variance(values)) for size, values in grouped.items()}
    xy = [(float(size), means[size]) for size in sizes]
    weighted = [_weighted_fit(xy, [weights[size] for size in sizes])]
    quality = "affine"
    segments: list[dict[str, Any]] = []
    breakpoint_size = None
    if len(sizes) >= 6:
        best = None
        for index in range(2, len(sizes) - 2):
            left = [point for point in xy if point[0] <= sizes[index]]
            right = [point for point in xy if point[0] > sizes[index]]
            if len({point[0] for point in left}) < 2 or len({point[0] for point in right}) < 2:
                continue
            left_fit = _weighted_fit(left, [weights[size] for size in sizes if size <= sizes[index]])
            right_fit = _weighted_fit(right, [weights[size] for size in sizes if size > sizes[index]])
            total = left_fit["sse"] + right_fit["sse"]
            if best is None or total < best[0]:
                best = (total, index, left_fit, right_fit)
        if best is not None and best[0] < 0.85 * weighted[0]["sse"]:
            total, index, left_fit, right_fit = best
            if left_fit["beta_ns_per_byte"] >= 0 and right_fit["beta_ns_per_byte"] >= 0:
                quality = "piecewise"
                breakpoint_size = sizes[index]
                segments = [
                    {"from_bytes": sizes[0], "to_bytes": sizes[index],
                     **{key: left_fit[key] for key in ("alpha_us", "beta_ns_per_byte",
                                                       "r2_weighted", "se_alpha_us",
                                                       "se_beta_ns_per_byte")},
                     "size_count": index + 1},
                    {"from_bytes": sizes[index + 1], "to_bytes": sizes[-1],
                     **{key: right_fit[key] for key in ("alpha_us", "beta_ns_per_byte",
                                                        "r2_weighted", "se_alpha_us",
                                                        "se_beta_ns_per_byte")},
                     "size_count": len(sizes) - index - 1},
                ]
                weighted[0] = {"alpha_us": left_fit["alpha_us"],
                               "beta_ns_per_byte": left_fit["beta_ns_per_byte"],
                               "sse": total, "syy": weighted[0]["syy"],
                               "r2_weighted": 1.0 - total / weighted[0]["syy"]
                               if weighted[0]["syy"] > 0 else 1.0,
                               "se_alpha_us": left_fit["se_alpha_us"],
                               "se_beta_ns_per_byte": left_fit["se_beta_ns_per_byte"]}
    fit = weighted[0]
    monotone = all(means[right] >= means[left] - 1e-9
                   for left, right in zip(sizes, sizes[1:]))
    holdout = _holdout_mape(xy)
    fit_quality = quality
    if len(sizes) < 2:
        fit_quality = "single_size"
        fit = {**fit, "beta_ns_per_byte": None, "alpha_us": means[sizes[0]],
               "r2_weighted": None}
    sample_count = len(points)
    return _finite_result({
        **{key: fit[key] for key in ("alpha_us", "beta_ns_per_byte", "r2_weighted")},
        "fit_quality": fit_quality, "segments": segments, "breakpoint_bytes": breakpoint_size,
        "sample_count": sample_count, "size_count": len(sizes),
        "se_alpha_us": fit.get("se_alpha_us"), "se_beta_ns_per_byte": fit.get("se_beta_ns_per_byte"),
        "holdout_mape_pct": holdout,
        "monotonicity_violation": not monotone,
        "bandwidth_gbps": (1.0 / fit["beta_ns_per_byte"]
                           if fit.get("beta_ns_per_byte") else None),
        "raw": {str(size): {"count": len(grouped[size]),
                            "p50_us": _percentile(grouped[size], 50),
                            "min_us": min(grouped[size]),
                            "max_us": max(grouped[size])}
                for size in sizes},
    })

def _variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.25 * max(1e-9, (values[0] if values else 1.0) ** 2)
    mean = sum(values) / len(values)
    return sum((value - mean) ** 2 for value in values) / (len(values) - 1)

def _holdout_mape(points: Sequence[tuple[float, float]]) -> float | None:
    sizes = sorted({point[0] for point in points})
    if len(sizes) < 3:
        return None
    errors = []
    for size in sizes:
        train = [point for point in points if point[0] != size]
        if len({point[0] for point in train}) < 2:
            continue
        fit = _weighted_fit(train, [1.0] * len(train))
        teste = [point[1] for point in points if point[0] == size]
        predicted = fit["alpha_us"] + fit["beta_ns_per_byte"] * size / 1000.0
        if predicted > 0:
            errors.append(abs(sum(teste) / len(teste) - predicted) / predicted * 100.0)
    return round(sum(errors) / len(errors), 6) if errors else None

def _percentile(values: Sequence[float], pct: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * pct / 100.0
    low, high = int(math.floor(position)), int(math.ceil(position))
    if low == high:
        return ordered[low]
    return ordered[low] * (high - position) + ordered[high] * (position - low)

def _sample_qualified(record: Mapping[str, Any], tier: Mapping[str, Any]) -> tuple[bool, str]:
    if _terminal_evidence(record):
        return False, "terminal_failure"
    if record.get("_rank_invalid") is not None:
        return False, "rank_invalid"
    if record.get("_group_size_invalid") is not None:
        return False, "group_size_invalid"
    if record.get("_group_ranks_invalid") is not None:
        return False, "group_ranks_invalid"
    if record.get("validated") is not True:
        return False, ("validated_false" if record.get("validated") is False
                       else "validated_absent")
    ranks = sorted(int(item) for item in tier.get("ranks") or ())
    rank = record.get("rank")
    if rank is None:
        return False, "rank_absent"
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 0:
        return False, "rank_invalid"
    if not ranks or rank not in ranks:
        return False, "out_of_group_rank"
    size = record.get("group_size")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        return False, "group_size_invalid"
    if size != len(ranks):
        return False, "group_size_incompatible"
    protocol = str(record.get("protocol") or "")
    tier_protocol = str(tier.get("protocol") or "")
    if tier_protocol and protocol and protocol != tier_protocol:
        return False, "protocol_incompatible"
    collective = record.get("collective")
    if collective is not None and str(collective) != str(record.get("op")):
        return False, "collective_incompatible"
    group_ranks = record.get("group_ranks")
    if group_ranks is None:
        return False, "group_ranks_absent"
    if (isinstance(group_ranks, (str, bytes))
            or any(isinstance(item, bool) or not isinstance(item, int) or item < 0
                   for item in group_ranks)
            or len(set(group_ranks)) != len(group_ranks)):
        return False, "group_ranks_invalid"
    if rank not in group_ranks:
        return False, "rank_not_in_group_ranks"
    if sorted(group_ranks) != ranks:
        return False, "group_ranks_incompatible"
    return True, ""

def _topology_verified(plan: Mapping[str, Any]) -> bool:
    label = str(plan.get("topology_label") or "unverified_rank_group")
    source = str(plan.get("topology_source") or "")
    return bool(plan.get("physical_verification") is True
                and label not in {"unverified_rank_group"}
                and source not in {"unverified_rank_group", "rank_count_assumption"})

def fit_calibrated_fabric_profile(plan: Mapping[str, Any], samples: Any, *,
                                  abort_record: Mapping[str, Any] | None = None
                                  ) -> dict[str, Any]:
    """Fit per-condition, per-regime fabric models without pooling."""
    plan, abort_record = bounded_sequence([plan, abort_record], "fabric fit inputs")
    for field in ("world_size", "ranks_per_node", "nodes", "dies_per_package"):
        if plan.get(field) is not None:
            bounded_count(plan[field], field, 0, 4096)
    for tier in bounded_sequence(plan.get("tiers") or (), "tiers", 3):
        for rank in bounded_sequence(tier.get("ranks") or (), "ranks", 4096):
            bounded_count(rank, "topology rank", 0, 4095)
    if isinstance(samples, (list, tuple)):
        bounded_sequence(samples, "samples", 100_000)
    records = parse_fabric_probe_samples(samples)  # Markers never authorize skipping validation.
    # Terminal evidence is classified before the measurement/control split, so
    # an already-parsed record can never smuggle a failure into the fit merely
    # because it also carries valid numeric fields.
    normalized_records: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, Mapping):
            continue
        item = dict(record)
        if item.get("_control_record") is not True and _terminal_evidence(item):
            item["_control_record"] = True
        normalized_records.append(item)
    records = normalized_records
    measurements = [record for record in records
                    if record.get("_control_record") is not True]
    controls = [record for record in records
                if record.get("_control_record") is True]
    planned = {str(tier["tier"]): tier for tier in plan.get("tiers") or ()
               if tier.get("available", True)}
    grouped: dict[tuple[str, str, int, str, str], list[dict[str, Any]]] = {}
    unidentified: dict[str, int] = {}
    rejected: list[dict[str, Any]] = []
    unqualified: list[dict[str, Any]] = []
    incomplete: list[dict[str, Any]] = []
    failed_keys: set[tuple[Any, Any, Any]] = set()
    for record in measurements:
        if not (_terminal_evidence(record)
                or record.get("validated") is False):
            continue
        key = (record.get("tier"), record.get("op"), record.get("group_size"))
        if key in failed_keys:
            continue
        failed_keys.add(key)
        expected = record.get("group_ranks")
        if not isinstance(expected, (list, tuple)) or not expected:
            expected = (planned.get(record.get("tier")) or {}).get("ranks") or ()
        expected_ranks = {int(item) for item in expected
                          if isinstance(item, int) and not isinstance(item, bool)}
        valid_ranks = {item.get("rank") for item in measurements
                       if item.get("tier") == record.get("tier")
                       and item.get("op") == record.get("op")
                       and item.get("group_size") == record.get("group_size")
                       and not _terminal_evidence(item)
                       and item.get("validated") is True}
        if expected_ranks and not expected_ranks <= valid_ranks:
            incomplete.append({"tier": record.get("tier"),
                               "op": record.get("op"),
                               "rank": record.get("rank"),
                               "reason": "incomplete_rank_set"})
    for control in controls:
        kind = control.get("kind") or ""
        status = control.get("status") or ""
        kind = kind if isinstance(kind, str) else bounded_summary(kind)
        status = status if isinstance(status, str) else bounded_summary(status)
        if _terminal_evidence(control) or control.get("validated") is False:
            incomplete.append({
                "tier": "run", "op": "run", "rank": diagnostic_value(control.get("rank")),
                "reason": f"control_failure:{kind or status or 'unknown'}"})
    run_blocked = bool(incomplete)
    blocked = {key: diagnostic_value(value) for key, value in abort_record.items()} if isinstance(abort_record, Mapping) else None
    if blocked is not None:
        marker = blocked.get("kind")
        status = blocked.get("status") or blocked.get("reason")
        if marker == "abort" or (isinstance(status, str) and status in _RUN_FAILURE_STATUS) \
                or status == "wall_budget_exceeded":
            run_blocked = True
            incomplete.append({"tier": "run", "op": "run",
                               "rank": blocked.get("rank"),
                               "reason": "incomplete_rank_set"})
    rejected.extend(incomplete)
    for record in measurements:
        tier = planned.get(record["tier"])
        if tier is None or record["op"] not in OPS:
            key = record["tier"] if tier is None else record["op"]
            unidentified[key] = unidentified.get(key, 0) + 1
            continue
        qualified, reason = _sample_qualified(record, tier)
        if not qualified and reason not in _EVIDENCE_REASONS:
            rejected.append({"tier": record["tier"], "op": record["op"],
                             "rank": record["rank"], "reason": reason})
            continue
        if not qualified:
            deficiency = {"tier": record["tier"], "op": record["op"],
                          "rank": record["rank"], "reason": reason,
                          "used_for_diagnostic_fit": True}
            unqualified.append(deficiency)
            rejected.append(deficiency)
        regime = "loaded" if str(record.get("regime")) == "loaded" else "isolated"
        grouped.setdefault((record["tier"], record["op"], record["group_size"],
                            record["protocol"], regime), []).append(record)
    tiers: dict[str, Any] = {}
    for (tier, op, group_size, protocol, regime), items in sorted(grouped.items()):
        entry = tiers.setdefault(tier, {"tier": tier, "operations": {},
                                        "sample_count": 0, "status": "measured"})
        entry["sample_count"] += len(items)
        fit = _fit_points([(item["bytes"], item["latency_us"]) for item in items])
        operation = entry["operations"].setdefault(op, {"conditions": [],
                                                        "regimes": {}})
        condition = {
            "group_size": group_size, "protocol": protocol,
            "regime": regime, "regimes": [regime], **fit,
        }
        operation["conditions"].append(condition)
        operation["regimes"][regime] = {
            **condition,
            "qualified": bool(
                fit["fit_quality"] not in {"single_size", "empty", "insufficient"}
                and fit["size_count"] >= 2
                and not fit["monotonicity_violation"]),
        }
    for tier, entry in tiers.items():
        for op, block in entry["operations"].items():
            block["conditions"].sort(key=lambda item: (-item["size_count"],
                                                       -item["sample_count"],
                                                       item["regime"]))
            isolated = block["regimes"].get("isolated")
            primary = isolated or block["conditions"][0]
            block.update({key: primary[key] for key in
                          ("alpha_us", "beta_ns_per_byte", "fit_quality",
                           "r2_weighted", "segments", "breakpoint_bytes",
                           "se_alpha_us", "se_beta_ns_per_byte",
                           "monotonicity_violation", "holdout_mape_pct",
                           "sample_count", "size_count", "regime")})
            block["congestion_factor"], block["congestion_reason"], block[
                "congestion_evidence"] = _congestion(grouped, tier, op)
            block["qualified"] = bool(
                all(condition.get("qualified") for condition in
                    block["regimes"].values())
                and block["fit_quality"] not in {"single_size", "empty",
                                                 "insufficient"}
                and not block["monotonicity_violation"])
    valid_ops = [op for block in tiers.values()
                 for op in block["operations"].values()]
    missing = sorted(set(planned) - set(tiers))
    all_qualified = bool(valid_ops) and all(op.get("qualified") for op in valid_ops)
    topology_verified = _topology_verified(plan)
    status = ("calibrated" if not missing and not unidentified and not rejected
              and not unqualified and all_qualified and topology_verified
              and not run_blocked else "partial")
    return _published_profile({
        "schema": PROFILE_SCHEMA, "status": status,
        "world_size": int(plan.get("world_size") or 0),
        "ranks_per_node": int(plan.get("ranks_per_node") or 0),
        "topology": plan.get("topology"),
        "topology_label": plan.get("topology_label", "unverified_rank_group"),
        "conditions": {
            "world_size": plan.get("world_size"),
            "ranks_per_node": plan.get("ranks_per_node"),
            "clocks": sorted({str(item.get("clock_mhz")) for item in measurements
                              if item.get("clock_mhz") is not None}),
            "protocols": sorted({item["protocol"] for item in measurements}),
            "firmware": plan.get("firmware"), "software": plan.get("software"),
        },
        "tiers": tiers, "missing_tiers": missing,
        "unidentified_tiers": dict(sorted(unidentified.items())),
        "rejected_samples": rejected, "unqualified_samples": unqualified,
        "run_evidence_blocked": run_blocked, "unqualified_sample_count": len(unqualified),
        "sample_count": len(measurements), "control_record_count": len(controls),
        "qualified_sample_count": max(
            0, len(measurements) - len([item for item in rejected
                                        if item.get("tier") != "run"])),
        "source": "live_hccl_micro_sweep",
        "topology_verified": topology_verified,
        "usable_for_link_override": bool(status == "calibrated" and all_qualified
                                         and not rejected and not unqualified
                                         and topology_verified),
        "limitations": [
            "A calibrated fit is only valid for the recorded topology, clocks, "
            "firmware and protocol conditions.",
            "Missing tiers, unidentified operations, rejected samples, samples "
            "without affirmative validation/rank/group_ranks evidence and "
            "non-monotone curves are not fabricated into a calibration.",
            "Isolated and loaded regimes are fitted separately. A diagnostic fit "
            "may include unqualified samples but can never be used as an override.",
        ],
    })

def _congestion(grouped: Mapping[tuple[str, str, int, str, str],
                               list[dict[str, Any]]],
                tier: str, op: str) -> tuple[float | None, str, dict[str, Any]]:
    isolated, loaded = [], []
    for (item_tier, item_op, _, _, regime), items in grouped.items():
        if item_tier != tier or item_op != op:
            continue
        (loaded if regime == "loaded" else isolated).append(
            _fit_points([(item["bytes"], item["latency_us"]) for item in items]))
        for item in items:
            (loaded if regime == "loaded" else isolated).append(item)
    fits = [item for item in isolated if "fit_quality" in item]
    fitted_loaded = [item for item in loaded if "fit_quality" in item]
    if not fits or not fitted_loaded:
        return None, "isolated and loaded regime fits are both required", {}
    iso, loa = fits[0], fitted_loaded[0]
    if (iso.get("beta_ns_per_byte") is None
            or loa.get("beta_ns_per_byte") is None):
        return None, "both regime fits need a slope", {}
    sizes = sorted({int(item["bytes"]) for item in isolated
                    if isinstance(item, Mapping) and "bytes" in item}
                   & {int(item["bytes"]) for item in loaded
                      if isinstance(item, Mapping) and "bytes" in item})
    if not sizes:
        return None, "no common message size across regimes", {}
    size = sizes[len(sizes) // 2]
    predicted_i = iso["alpha_us"] + iso["beta_ns_per_byte"] * size / 1000.0
    predicted_l = loa["alpha_us"] + loa["beta_ns_per_byte"] * size / 1000.0
    if predicted_i <= 0:
        return None, "isolated prediction is non-positive", {}
    factor = predicted_l / predicted_i
    if not all(math.isfinite(value) and value > 0 for value in (predicted_i, predicted_l, factor)):
        raise ProfilerUsageError("fabric congestion predictions must be finite and positive")
    return (factor, f"loaded/isolated fit ratio at {size} bytes",
            {"bytes": size, "isolated": iso, "loaded": loa})

__all__ = ["OPS", "PROFILE_SCHEMA", "REGIMES", "fit_calibrated_fabric_profile", "parse_fabric_probe_samples"]
