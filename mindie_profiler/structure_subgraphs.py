"""Declared composite boundaries and their common structural classification.

[Role] Project sim subgraphs into match targets without duplicating model logic.
[Invariants] A composite consumes its entire declared member set. A scope that
  contains only one member cannot identify the whole fusion. Common structure
  across candidates does not prove an individual layer or invocation.
[Timeouts & Locks] Bounded by the supplied structure and distinct candidate sets.
[Side-Effect Policy] Pure metadata processing; no model imports or device I/O.
"""
from __future__ import annotations

from collections import defaultdict

from .events import ProfilerUsageError


class StructureTargets:
    def __init__(self, nodes, subgraphs):
        self.nodes = nodes
        self.subgraphs = {}
        for record in subgraphs:
            key = record.get("subgraph_id")
            members = record.get("node_ids", ())
            if not key or key in nodes or key in self.subgraphs:
                raise ProfilerUsageError(f"structure subgraph_id missing or duplicated: {key}")
            if not members or len(set(members)) != len(members) or any(
                member not in nodes for member in members
            ):
                raise ProfilerUsageError(f"subgraph has invalid semantic members: {key}")
            for field in ("replica", "stage", "phase"):
                if any(nodes[member].get(field) != record.get(field) for member in members):
                    raise ProfilerUsageError(f"subgraph crosses declared {field}: {key}")
            if record.get("layer") is not None and any(
                nodes[member].get("layer") != record["layer"] for member in members
            ):
                raise ProfilerUsageError(f"subgraph has inconsistent declared layer: {key}")
            self.subgraphs[key] = record
        self.all = {**nodes, **self.subgraphs}
        self.native_implementations = defaultdict(list)
        for key, target in self.all.items():
            implementation = target.get("implementation") or {}
            kinds = set(implementation.get("native_kinds", ()))
            if implementation.get("native_kind"):
                kinds.add(implementation["native_kind"])
            for kind in sorted(kinds):
                self.native_implementations[kind].append(key)
        self._classification = {}

    def describe_implementation(self, kind, targets):
        """Describe a declared native boundary without claiming a tensor match."""
        node_ids, subgraph_ids = self.split(targets)
        return {
            "basis": "declared_native_implementation",
            "native_operator_type": kind,
            "declared_target_count": len(targets),
            "declared_node_ids": node_ids[:64],
            "declared_subgraph_ids": subgraph_ids[:64],
            "targets_with_contract": sum(
                self.all[key].get("contract") is not None for key in targets),
            "event_matchable_targets": sum(
                self.all[key].get("event_matchable", True) for key in targets),
            "coverage_kinds": sorted({
                self.all[key].get("coverage", {}).get(
                    "kind", "declared_node_boundary" if key in self.nodes else "complete_subgraph")
                for key in targets
            }),
            "common": self.classify(targets)["common"],
            "tensor_match_implied": False,
            "occurrence_binding_implied": False,
        }

    def members(self, key):
        return self.subgraphs[key]["node_ids"] if key in self.subgraphs else [key]

    def enclosing_scopes(self, keys, fields):
        """Keep both sides of a cross-block fusion without duplicating an event."""
        scopes = set()
        for key in keys:
            for member in self.members(key):
                node = self.nodes[member]
                meta = node.get("operator", {}).get("metadata", {})
                semantic = {**meta.get("semantic_metadata", {}), **meta}
                owners = [node, *semantic.get("fused_origin_scopes", ())]
                for owner in owners:
                    scope = {**owner, "replica": node.get("replica")}
                    if (scope.get("layer") is not None and scope["layer"] >= 0
                            and scope.get(fields[-1]) is not None):
                        scopes.add(tuple(scope.get(field) for field in fields))
        return scopes

    def scope(self, row):
        """Expand a declared evidence scope, preserving full fusion containment."""
        node_ids = row.get("node_ids", ())
        subgraph_ids = row.get("subgraph_ids", ())
        if not node_ids and not subgraph_ids:
            raise ProfilerUsageError("evidence scope requires node_ids or subgraph_ids")
        if any(key not in self.nodes for key in node_ids) or any(
            key not in self.subgraphs for key in subgraph_ids
        ):
            raise ProfilerUsageError("evidence scope references an unknown node or subgraph")
        members = set(node_ids)
        for key in subgraph_ids:
            members.update(self.members(key))
        return members | {
            key for key, record in self.subgraphs.items()
            if set(record["node_ids"]) <= members
        }

    def split(self, keys):
        return (
            [key for key in keys if key in self.nodes],
            [key for key in keys if key in self.subgraphs],
        )

    def classify(self, candidates):
        """Keep only properties shared by every compatible declared target."""
        key = tuple(candidates)
        if key not in self._classification:
            targets = [self.all[item] for item in candidates]
            common = {}
            for field in ("block", "role"):
                values = {target.get(field) for target in targets}
                if len(values) == 1 and None not in values:
                    common[field] = next(iter(values))
            structure = dict(targets[0].get("structure", {})) if targets else {}
            structure = {
                field: value for field, value in structure.items()
                if value is not None and all(
                    target.get("structure", {}).get(field) == value for target in targets
                )
            }
            if structure:
                common["structure"] = structure
            self._classification[key] = {
                "basis": "common_to_all_declared_tensor_candidates",
                "common": common,
                "occurrence_binding_implied": False,
            }
        return self._classification[key]
