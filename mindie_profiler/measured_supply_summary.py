"""Bounded condition-median aggregation for measured matrix-pipe supply.

[Role]
  Incrementally aggregate complete 2D matrix PMU observations by condition key
  with hard condition and sample caps, then select one certified R64
  saturated/underfilled condition pair without retaining unbounded event lists.

[Invariants]
  * When ``physical_owners`` is undeclared (``None``), ``MatrixSupplyAccumulator``
    is an ``O(1)`` no-op and retains zero per-event dicts.
  * Retention is strictly bounded by ``MAX_SUPPLY_CONDITIONS`` (``256``) and
    ``MAX_SAMPLES_PER_CONDITION`` (``512``); overflow is disclosed via explicit
    limitation codes.
  * Clipped window events are counted and excluded from condition medians.

[Timeouts & Locks]
  Pure in-memory median arithmetic over bounded numeric arrays; no I/O or locks.

[Side-Effect Policy]
  Mutates only caller-owned ``MatrixSupplyAccumulator`` instances and returns
  fresh summary dicts.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Iterable, Mapping, Sequence

from .events import Event, Observation
from .measured_supply import (
    MAX_SAMPLES_PER_CONDITION,
    MAX_SUPPLY_CONDITIONS,
    MEASURED_SUPPLY_SCHEMA,
    MEASURED_SUPPLY_SCOPE,
    SATURATION_THRESHOLD,
    _canonical,
    _positive_int,
    build_dual_load_service,
    measured_supply_event_record,
)


def _finite_number(value: Any) -> float | None:
    if (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    ):
        return float(value)
    return None


class _ConditionBucket:
    __slots__ = (
        "head",
        "total_count",
        "all_complete",
        "durations",
        "mac_ratios",
        "cube_utils",
        "logical_flops",
        "issued_flops",
        "pipe_times",
        "pipe_ratios",
        "source_paths",
        "event_ids",
        "row_indices",
    )

    def __init__(self, head: dict[str, Any], max_samples: int) -> None:
        self.head = head
        self.total_count = 0
        self.all_complete = True
        self.durations: list[float] = []
        self.mac_ratios: list[float] = []
        self.cube_utils: list[float] = []
        self.logical_flops: list[float] = []
        self.issued_flops: list[float] = []
        self.pipe_times: dict[str, list[float]] = {}
        self.pipe_ratios: dict[str, list[float]] = {}
        self.source_paths: set[str] = set()
        self.event_ids: list[str] = []
        self.row_indices: list[Any] = []
        self.add(head, max_samples=max_samples)

    def add(self, row: Mapping[str, Any], *, max_samples: int) -> bool:
        self.total_count += 1
        self.all_complete = self.all_complete and bool(row.get("complete_in_window"))
        prov = row.get("provenance") or {}
        src = prov.get("source")
        if src and len(self.source_paths) < 4:
            self.source_paths.add(str(src))
        eid = prov.get("event_id")
        if eid and len(self.event_ids) < 8:
            self.event_ids.append(str(eid))
        ridx = prov.get("row_index")
        if ridx is not None and len(self.row_indices) < 8:
            self.row_indices.append(ridx)
        if len(self.mac_ratios) >= max_samples and self.total_count > max_samples:
            return True
        if (val := _finite_number(row.get("duration_ns"))) is not None and len(
            self.durations
        ) < max_samples:
            self.durations.append(val)
        if (val := _finite_number(row.get("mac_ratio"))) is not None and len(
            self.mac_ratios
        ) < max_samples:
            self.mac_ratios.append(val)
        if (val := _finite_number(row.get("cube_utilization_pct"))) is not None and len(
            self.cube_utils
        ) < max_samples:
            self.cube_utils.append(val)
        if (val := _finite_number(row.get("logical_flops"))) is not None and len(
            self.logical_flops
        ) < max_samples:
            self.logical_flops.append(val)
        if (val := _finite_number(row.get("issued_flops"))) is not None and len(
            self.issued_flops
        ) < max_samples:
            self.issued_flops.append(val)
        for key, raw_val in (row.get("pipe_times_ns") or {}).items():
            if (val := _finite_number(raw_val)) is not None:
                series = self.pipe_times.setdefault(str(key), [])
                if len(series) < max_samples:
                    series.append(val)
        for key, raw_val in (row.get("pipe_ratios") or {}).items():
            if (val := _finite_number(raw_val)) is not None:
                series = self.pipe_ratios.setdefault(str(key), [])
                if len(series) < max_samples:
                    series.append(val)
        return False

    def summary(self, physical_owners: int, saturation_threshold: float) -> dict[str, Any]:
        first = dict(self.head)
        times = {k: statistics.median(v) for k, v in sorted(self.pipe_times.items()) if v}
        ratios = {k: statistics.median(v) for k, v in sorted(self.pipe_ratios.items()) if v}
        mac_time = times.get("aic_mac_time")
        mac_ratio = statistics.median(self.mac_ratios) if self.mac_ratios else None
        logical = statistics.median(self.logical_flops) if self.logical_flops else None
        issued = statistics.median(self.issued_flops) if self.issued_flops else None
        duration = statistics.median(self.durations) if self.durations else None
        active_owners = int(first["active_owners"])
        rate = (
            (issued / (mac_time * 1e-9))
            if issued is not None and mac_time and mac_time > 0
            else None
        )
        per_owner = rate / active_owners if rate is not None else None
        limiting = max(ratios.items(), key=lambda item: (item[1], item[0]))[0] if ratios else None
        missing = [
            reason
            for reason in (first.get("missing") or ())
            if reason != "physical_owners_not_declared"
        ]
        prov = first.get("provenance") or {}
        issue = first.get("issue")
        return {
            **first,
            "m": int(first["m"]),
            "n": int(first["n"]),
            "k": int(first["k"]),
            "issue": issue,
            "issue_rule": issue,
            "active_owners": active_owners,
            "physical_owners": int(physical_owners),
            "event_count": self.total_count,
            "logical_flops": int(logical) if logical is not None else None,
            "issued_flops": int(issued) if issued is not None else None,
            "flops": int(issued) if issued is not None else None,
            "duration_ns": duration,
            "mac_ratio": mac_ratio,
            "cube_utilization_pct": (
                statistics.median(self.cube_utils) if self.cube_utils else None
            ),
            "pipe_times_ns": times,
            "pipe_ratios": ratios,
            "limited_by": limiting,
            "rate_flops_per_s": rate,
            "per_owner_rate_flops_per_s": per_owner,
            "effective_rate_flops_per_s": (
                issued / (duration * 1e-9) if issued and duration else None
            ),
            "saturated": bool(
                active_owners == physical_owners
                and mac_ratio is not None
                and mac_ratio >= saturation_threshold
            ),
            "complete_in_window": self.all_complete,
            "counter_status": "present" if not missing else "unknown",
            "missing": missing,
            "provenance": {
                "source": prov.get("source"),
                "source_sha256": prov.get("source_sha256"),
                "source_schema": prov.get("source_schema"),
                "event_id": prov.get("event_id"),
                "row_index": prov.get("row_index"),
                "observation_id": prov.get("observation_id"),
                "native_call": first.get("native_call"),
                "native_type": first.get("native_type"),
                "device_id": first.get("device_id"),
                "rank_id": first.get("rank_id"),
                "rank_index": first.get("rank_index"),
                "condition": {
                    "m": int(first["m"]),
                    "n": int(first["n"]),
                    "k": int(first["k"]),
                    "active_owners": active_owners,
                },
                "event_count": self.total_count,
                "sampled_count": min(self.total_count, len(self.mac_ratios)),
                "median_basis": "per_condition_median_repeats",
                "source_paths": sorted(self.source_paths)[:4],
                "event_ids": list(self.event_ids),
                "row_indices": list(self.row_indices),
                "physical_owners_basis": "declared_aic_count",
                "issue_rule": issue,
                "elapsed_duration_used_as_rate": False,
            },
        }


class MatrixSupplyAccumulator:
    """Bounded O(unique conditions) incremental aggregator for matrix PMU supply."""

    def __init__(
        self,
        *,
        physical_owners: int | None = None,
        source_identity: Mapping[str, Any] | None = None,
        saturation_threshold: float = SATURATION_THRESHOLD,
        max_conditions: int = MAX_SUPPLY_CONDITIONS,
        max_samples_per_condition: int = MAX_SAMPLES_PER_CONDITION,
    ) -> None:
        self.physical_owners = _positive_int(physical_owners)
        self.source_identity = dict(source_identity) if source_identity else None
        self.saturation_threshold = saturation_threshold
        self.max_conditions = max(1, int(max_conditions))
        self.max_samples_per_condition = max(1, int(max_samples_per_condition))
        self.conditions: dict[tuple[Any, ...], _ConditionBucket] = {}
        self.clipped = 0
        self.dropped_conditions = 0
        self.capped_samples = 0

    def add_record(self, candidate: Mapping[str, Any]) -> None:
        if self.physical_owners is None:
            return
        if candidate.get("status") != "measured":
            return
        if not candidate.get("complete_in_window"):
            self.clipped += 1
            return
        prov = candidate.get("provenance") or {}
        key = (
            candidate.get("native_call"),
            candidate.get("native_type"),
            candidate.get("dtype"),
            candidate.get("output_dtype"),
            candidate.get("n"),
            candidate.get("k"),
            candidate.get("device_id"),
            candidate.get("rank_id"),
            prov.get("source"),
            prov.get("source_sha256"),
            int(candidate["m"]),
            int(candidate["active_owners"]),
            _canonical(candidate.get("issue")),
        )
        bucket = self.conditions.get(key)
        if bucket is None:
            if len(self.conditions) >= self.max_conditions:
                self.dropped_conditions += 1
                return
            self.conditions[key] = _ConditionBucket(dict(candidate), self.max_samples_per_condition)
            return
        if bucket.add(candidate, max_samples=self.max_samples_per_condition):
            self.capped_samples += 1

    def add_event(self, observation: Observation, event: Event) -> None:
        if self.physical_owners is None:
            return
        self.add_record(
            measured_supply_event_record(
                observation,
                event,
                self.source_identity,
                physical_owners=self.physical_owners,
            )
        )


def summarize_measured_supply(
    candidates: MatrixSupplyAccumulator | Iterable[Mapping[str, Any]],
    *,
    physical_owners: int | None = None,
    source_identity: Mapping[str, Any] | None = None,
    resource_services: Sequence[Mapping[str, Any]] | None = None,
    extra_limitations: Sequence[Mapping[str, Any]] | None = None,
    saturation_threshold: float = SATURATION_THRESHOLD,
    max_groups: int = 16,
) -> dict[str, Any]:
    """Select one saturated/underfilled condition pair from bounded condition medians."""
    limitations: list[dict[str, Any]] = [dict(item) for item in (extra_limitations or ())]
    resolved_owners = _positive_int(
        candidates.physical_owners
        if isinstance(candidates, MatrixSupplyAccumulator) and physical_owners is None
        else physical_owners
    )
    resolved_source = (
        candidates.source_identity
        if isinstance(candidates, MatrixSupplyAccumulator) and source_identity is None
        else (dict(source_identity) if source_identity else None)
    )
    if resolved_owners is None:
        limitations.insert(
            0,
            {
                "code": "measured_supply_physical_owners_not_declared",
                "detail": (
                    "declare the physical AIC count (for example --aic-count 32); "
                    "the maximum sampled Block Num is not capacity evidence"
                ),
                "severity": "high",
            },
        )
        return {
            "schema_version": MEASURED_SUPPLY_SCHEMA,
            "status": "not_available",
            "selection": "most_samples_per_condition_median",
            "scope": MEASURED_SUPPLY_SCOPE,
            "not_end_to_end_kernel_latency": True,
            "pair": None,
            "source_identity": resolved_source,
            "resource_services": list(resource_services or ()),
            "candidates": [],
            "candidate_conditions": 0,
            "limitations": limitations,
        }

    if isinstance(candidates, MatrixSupplyAccumulator):
        acc = candidates
    else:
        acc = MatrixSupplyAccumulator(
            physical_owners=resolved_owners,
            source_identity=resolved_source,
            saturation_threshold=saturation_threshold,
        )
        for raw in candidates:
            acc.add_record(raw)

    summaries = [
        bucket.summary(resolved_owners, saturation_threshold)
        for bucket in acc.conditions.values()
    ]
    identities: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in summaries:
        prov = row.get("provenance") or {}
        key = (
            row.get("native_call"),
            row.get("native_type"),
            row.get("dtype"),
            row.get("output_dtype"),
            row.get("n"),
            row.get("k"),
            row.get("device_id"),
            row.get("rank_id"),
            prov.get("source"),
            prov.get("source_sha256"),
            _canonical(row.get("issue")),
        )
        identities.setdefault(key, []).append(row)

    pairs: list[tuple[int, int, dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    certified = 0
    for rows in identities.values():
        if rows[0].get("issue") is None:
            continue
        certified += 1
        raw_fulls = [row for row in rows if row["saturated"] and row["active_owners"] == resolved_owners]
        raw_tails = [row for row in rows if not row["saturated"] and row["active_owners"] < resolved_owners]
        if not raw_fulls or not raw_tails:
            limitations.append(
                {
                    "code": (
                        "measured_supply_no_saturated_condition"
                        if not raw_fulls
                        else "measured_supply_no_underfilled_condition"
                    ),
                    "detail": (
                        "identity has no complete full-grid saturated / lower-owner "
                        "underfilled condition pair"
                    ),
                    "severity": "medium",
                }
            )
            continue
        candidate_pairs = sorted(
            (
                (
                    cand_full["event_count"] + cand_tail["event_count"],
                    int(cand_full["issued_flops"] or 0),
                    -int(cand_tail["issued_flops"] or 0),
                    cand_full,
                    cand_tail,
                )
                for cand_full in raw_fulls
                for cand_tail in raw_tails
            ),
            key=lambda item: (item[0], item[1], item[2]),
            reverse=True,
        )
        best_pair: tuple[int, int, dict[str, Any], dict[str, Any], dict[str, Any]] | None = None
        last_exc: ValueError | None = None
        for total_events, full_flops, _neg_tail_flops, cand_full, cand_tail in candidate_pairs:
            try:
                pair_doc = build_dual_load_service(
                    cand_full,
                    cand_tail,
                    physical_owners=resolved_owners,
                    saturation_threshold=saturation_threshold,
                )
            except ValueError as exc:
                if last_exc is None:
                    last_exc = exc
                continue
            best_pair = (total_events, full_flops, pair_doc, cand_full, cand_tail)
            break
        if best_pair is None:
            limitations.append(
                {
                    "code": "measured_supply_pair_invalid",
                    "detail": str(last_exc or "no valid dual-load pair"),
                    "severity": "medium",
                }
            )
            continue
        pairs.append(best_pair)

    pair = None
    selected: tuple[dict[str, Any], ...] = ()
    if pairs:
        chosen = max(pairs, key=lambda item: (item[0], item[1]))
        pair, selected = chosen[2], (chosen[3], chosen[4])
    elif certified == 0:
        limitations.insert(
            0,
            {
                "code": "measured_supply_no_certified_issue_rule",
                "detail": "no condition carries the certified R64 QBMM issued-work rule",
                "severity": "medium",
            },
        )
    if not summaries:
        limitations.insert(
            0,
            {
                "code": "measured_supply_no_matrix_pmu_events",
                "detail": "no complete 2D matrix event with issued shape, owners and raw MAC counters",
                "severity": "medium",
            },
        )
    if acc.clipped:
        limitations.append(
            {
                "code": "measured_supply_clipped_events_excluded",
                "detail": f"{acc.clipped} matrix PMU events were clipped and not used",
                "severity": "medium",
            }
        )
    if acc.dropped_conditions:
        limitations.append(
            {
                "code": "measured_supply_condition_cap_reached",
                "detail": (
                    f"{acc.dropped_conditions} matrix PMU events exceeded the "
                    f"{acc.max_conditions}-condition cap"
                ),
                "severity": "medium",
            }
        )
    if acc.capped_samples:
        limitations.append(
            {
                "code": "measured_supply_condition_samples_capped",
                "detail": (
                    f"{acc.capped_samples} repeat matrix PMU samples exceeded the "
                    f"{acc.max_samples_per_condition}-sample per-condition cap"
                ),
                "severity": "low",
            }
        )
    selected_keys = {
        (
            r.get("native_call"),
            r.get("n"),
            r.get("k"),
            r.get("m"),
            r.get("active_owners"),
            r.get("device_id"),
            r.get("rank_id"),
        )
        for r in selected
    }
    summaries.sort(
        key=lambda row: (
            0
            if (
                row.get("native_call"),
                row.get("n"),
                row.get("k"),
                row.get("m"),
                row.get("active_owners"),
                row.get("device_id"),
                row.get("rank_id"),
            )
            in selected_keys
            else 1,
            str(row.get("native_call")),
            row["n"],
            row["k"],
            row["m"],
            row["active_owners"],
        )
    )
    return {
        "schema_version": MEASURED_SUPPLY_SCHEMA,
        "status": "measured_pair" if pair else "not_available",
        "selection": "most_samples_certified_identity_pair",
        "physical_owners": resolved_owners,
        "physical_owners_basis": "declared_aic_count",
        "scope": MEASURED_SUPPLY_SCOPE,
        "not_end_to_end_kernel_latency": True,
        "certified_identities": certified,
        "pair": pair,
        "source_identity": resolved_source,
        "resource_services": list(resource_services or ()),
        "candidates": summaries[:max_groups],
        "candidate_conditions": len(summaries),
        "limitations": limitations,
    }


__all__ = ["MatrixSupplyAccumulator", "summarize_measured_supply"]
