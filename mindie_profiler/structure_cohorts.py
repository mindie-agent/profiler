"""Measured multiplicities for physically identical declared candidate sets.

[Role] Reconcile repeated operators/subgraphs without inventing layer instances.
[Invariants] Cohorts require one tensor contract, physical signature and device
  placement. Timing never chooses a candidate. Conflicting evidence, overlapping
  target boundaries and unknown multi-launch stages cannot form a cohort.
  Window counts are not step counts, and activity sums are not elapsed time.
[Timeouts & Locks] Bounded by the mapper's event budget; no I/O or locks.
[Side-Effect Policy] Window-local counters and measured intervals only.
"""
from collections import Counter
from hashlib import sha256
import json

from .accounting import merge_intervals


_BASES = {
    "tensor_contract_only", "repeated_tensor_contract", "host_scope_has_multiple_nodes",
    "module_scope_has_multiple_nodes", "explicit_evidence", "host_connection_and_tensor",
    "synchronized_module_and_tensor",
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _median(counts):
    total = sum(counts.values())
    positions = ((total - 1) // 2, total // 2)
    selected, seen = [], 0
    for value, count in sorted(counts.items()):
        selected.extend(value for position in positions if seen <= position < seen + count)
        seen += count
        if len(selected) == 2:
            return sum(selected) / 2
    return None


class CohortAccumulator:
    def __init__(self, graph_id, targets, observation):
        self.graph_id, self.targets, self.observation = graph_id, targets, observation
        self.groups = {}
        self.eligibility = {}
        self.excluded = Counter()

    def _cohort(self, ids):
        key = tuple(sorted(ids))
        if key in self.eligibility:
            return self.eligibility[key]
        rows = [self.targets.all[item] for item in key]
        reason = None
        if any(not row.get("physical_signature") or not row.get("physical_work") for row in rows):
            reason = "physical_work_not_declared"
        elif (len({row["physical_signature"] for row in rows}) != 1
              or len({_canonical(row["physical_work"]) for row in rows}) != 1):
            reason = "candidate_physical_work_differs"
        elif len({_canonical(row.get("contract")) for row in rows}) != 1:
            reason = "candidate_contracts_differ"
        elif len({(row.get("replica"), row.get("stage"), row.get("phase")) for row in rows}) != 1:
            reason = "candidate_placement_differs"
        elif len({item in self.targets.subgraphs for item in key}) != 1:
            reason = "candidate_boundaries_differ"
        elif any(row.get("coverage", {}).get("kind", "complete_subgraph")
                 not in {"complete_subgraph", "complete_semantic_subgraph"} for row in rows):
            reason = "incomplete_native_boundary"
        else:
            seen = set()
            for item in key:
                members = set(self.targets.members(item))
                if seen & members:
                    reason = "candidate_boundaries_overlap"
                    break
                seen.update(members)
        result = (None, reason)
        if reason is None:
            first = rows[0]
            layers = {(row.get("replica"), row.get("stage"), layer)
                      for row in rows for layer in row.get("layer_ids", [row.get("layer")])
                      if layer is not None and layer >= 0}
            result = ({
                "graph_id": self.graph_id, "target_ids": list(key),
                "target_kind": "subgraph" if key[0] in self.targets.subgraphs else "node",
                "declared_instance_count": len(key), "declared_layer_count": len(layers),
                "physical_signature": first["physical_signature"],
                "physical_work_per_instance": first["physical_work"],
                "resource_boundary": first.get("resource_boundary"),
                "contract": first["contract"], "contract_scope": first.get("contract_scope"),
                "replica": first.get("replica"), "stage": first.get("stage"),
                "phase": first.get("phase"),
                "structural_classification": self.targets.classify(key),
            }, None)
        self.eligibility[key] = result
        return result

    def add(self, event, interval, *, status, ids, candidates, basis, contract):
        if not candidates or contract is None:
            self.excluded["no_tensor_candidates"] += 1
            return "no_tensor_candidates"
        if basis not in _BASES:
            self.excluded["conflicting_or_incomplete_occurrence_evidence"] += 1
            return "conflicting_or_incomplete_occurrence_evidence"
        if status == "bound" and (len(ids) != 1 or not set(ids) <= set(candidates)):
            self.excluded["explicit_fusion_not_one_declared_target"] += 1
            return "explicit_fusion_not_one_declared_target"
        declaration, reason = self._cohort(candidates)
        if reason:
            self.excluded[reason] += 1
            return reason
        key = (event.op_type, event.device_id, tuple(declaration["target_ids"]))
        if key not in self.groups:
            identity = _canonical((self.graph_id, self.observation.rank_id, key))
            self.groups[key] = {
                "schema_version": "mindie-profile-cohort/1",
                "cohort_id": "sha256:" + sha256(identity.encode()).hexdigest(),
                **declaration, "native_operator_type": event.op_type,
                "rank_id": self.observation.rank_id, "device_id": event.device_id,
                "event_count": 0, "complete_event_count": 0, "clipped_event_count": 0,
                "activity_sum_ns": 0, "complete_activity_sum_ns": 0,
                "status_counts": Counter(), "_durations": Counter(), "_intervals": [],
                "occurrence_binding_implied": False,
            }
        group = self.groups[key]
        group["event_count"] += 1
        group["status_counts"][status] += 1
        group["activity_sum_ns"] += interval[1] - interval[0]
        group["_intervals"].append(interval)
        if event.complete_in(self.observation.window.start_ns, self.observation.window.end_ns):
            duration = event.end_ns - event.start_ns
            group["complete_event_count"] += 1
            group["complete_activity_sum_ns"] += duration
            group["_durations"][duration] += 1
        else:
            group["clipped_event_count"] += 1

    def finish(self):
        records = []
        for group in self.groups.values():
            durations = group.pop("_durations")
            intervals = group.pop("_intervals")
            count = group["complete_event_count"]
            group["status_counts"] = dict(group["status_counts"])
            group["busy_union_ns"] = sum(end - start for start, end in merge_intervals(intervals))
            group["duration_ns"] = {
                "mean": group["complete_activity_sum_ns"] / count if count else None,
                "p50": _median(durations), "min": min(durations) if durations else None,
                "max": max(durations) if durations else None,
                "basis": "complete_events_only",
            }
            group["multiplicity"] = {
                "observed_calls": group["event_count"],
                "declared_instances": group["declared_instance_count"],
                "calls_per_declared_instance": group["event_count"] / group["declared_instance_count"],
                "steps_in_window": None,
                "basis": "window_counts_not_layer_binding; step_label_is_not_completeness_evidence",
            }
            group["attribution"] = "candidate_set_aggregate; no_per_layer_allocation"
            records.append(group)
        return records
