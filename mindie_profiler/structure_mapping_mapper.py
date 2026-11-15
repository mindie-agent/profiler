"""Deterministic mapping from mindie-model-structure/1 graphs to measured events (structure_mapping_mapper).

[Role]
  Internal cohesive submodule of ``mindie_profiler`` supporting deterministic mapping from mindie-model-structure/1 graphs to measured events.
[Invariants]
  Preserves deterministic schemas, explicit Missing/None semantics, and zero hidden state.
[Timeouts & Locks]
  Inherits caller query/scan budgets; acquires no module-level locks.
[Side-Effect Policy]
  Pure in-memory transforms or bounded read-only source access unless explicitly invoked to write output.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from .events import ProfilerUsageError
from .structure_subgraphs import StructureTargets
from .structure_cohorts import CohortAccumulator

from .structure_mapping_helpers import (
    SCHEMA, _event_key, _event_raw_identity, _event_signature, _freeze,
    _native_call_signature_match, _shared_kv_candidates, _task_key, _union_ns,
    _verify_graph_id, read_metadata,
)

class StructureMapper:
    def __init__(self, structure, *, bindings=None, correlations=None,
                 mapping_limit=200, max_events=100_000, phase=None, module_evidence=None):
        self.structure = read_metadata(structure, "mindie-model-structure/1")
        self.graph_id = _verify_graph_id(self.structure)
        self.phase = phase
        declared_phase = self.structure.get("execution", {}).get("phase")
        if phase is not None and declared_phase != str(phase).strip().lower():
            raise ProfilerUsageError(
                f"scene phase {phase!r} does not match structure phase {declared_phase!r}")
        self.nodes = {}
        for node in self.structure.get("nodes", ()):
            node_id = node.get("node_id")
            if not node_id or node_id in self.nodes:
                raise ProfilerUsageError(f"structure node_id missing or duplicated: {node_id}")
            self.nodes[node_id] = node
        if not self.nodes:
            raise ProfilerUsageError("structure has no nodes")
        self.target_index = StructureTargets(
            self.nodes, self.structure.get("subgraphs", ()),
            self.structure.get("native_calls"))
        self.targets = self.target_index.all
        self.subgraphs = self.target_index.subgraphs
        self.contracts = defaultdict(list)
        for target_id, target in self.targets.items():
            if target.get("contract") is not None and target.get("event_matchable", True):
                self.contracts[_freeze(target["contract"])].append(target_id)
        if mapping_limit < 0 or max_events <= 0:
            raise ProfilerUsageError("mapping_limit must be nonnegative and max_mapping_events positive")
        self.mapping_limit = mapping_limit
        self.max_events = max_events
        self.examined = 0
        self.sample = []
        self.statuses = Counter()
        self.reasons = Counter()
        self.diagnostic_counts = Counter()
        self.diagnostics = {}
        self.implementation_correspondences = {}
        self.hccl_occurrences = {}
        self.hccl_presentation_counts = Counter()
        self.explicit = {}
        self.host_scopes = defaultdict(set)
        self.module_scopes = {}
        self.module_evidence = module_evidence
        self.rank_replicas = {}
        self.rank_stages = {}
        self.used_bindings = set()
        self.correlations = defaultdict(list)
        self.sources = {}
        if bindings is not None:
            self._load_bindings(read_metadata(bindings, "mindie-profile-bindings/1"))
        for value in correlations or ():
            self._load_correlation(read_metadata(value, "mindie-profiler-correlation/1"))
        if module_evidence is not None and not self.module_scopes:
            raise ProfilerUsageError("module traces require bindings.module_scopes")

    def _node_ids(self, row):
        ids = row.get("node_ids")
        if not isinstance(ids, list) or not ids or len(set(ids)) != len(ids):
            raise ProfilerUsageError("binding node_ids must be a nonempty unique list")
        if any(node not in self.nodes for node in ids):
            raise ProfilerUsageError(f"binding references unknown structure node: {ids}")
        return ids

    def _load_bindings(self, value):
        if value.get("graph_id") != self.graph_id:
            raise ProfilerUsageError("binding graph_id does not match structure")
        self.rank_replicas = {str(k): str(v) for k, v in value.get("rank_replicas", {}).items()}
        self.rank_stages = {str(k): str(v) for k, v in value.get("rank_stages", {}).items()}
        for rank in self.rank_replicas.keys() | self.rank_stages.keys():
            if not self._rank_candidates(self.nodes, rank):
                raise ProfilerUsageError(f"rank binding has no structure nodes: {rank}")
        for row in value.get("events", ()):
            event_id = row.get("event_id")
            subgraph_ids = row.get("subgraph_ids")
            if subgraph_ids is not None:
                if (row.get("node_ids") or not isinstance(subgraph_ids, list)
                        or len(subgraph_ids) != 1 or subgraph_ids[0] not in self.subgraphs):
                    raise ProfilerUsageError(
                        "explicit subgraph binding requires exactly one declared subgraph")
                ids = subgraph_ids
            else:
                ids = self._node_ids(row)
            if any(not self.targets[key].get("event_matchable", True) for key in ids):
                raise ProfilerUsageError(
                    "binding references an internal node of a selected native fusion")
            if not event_id or event_id in self.explicit:
                raise ProfilerUsageError("explicit bindings require unique event_id")
            if not isinstance(row.get("evidence"), dict) or not row["evidence"].get("source"):
                raise ProfilerUsageError("explicit event binding requires evidence.source")
            relation = row.get("relation", "direct")
            if relation not in {"direct", "fusion"}:
                raise ProfilerUsageError(f"unknown binding relation: {relation}")
            if len(ids) > 1 and relation != "fusion":
                raise ProfilerUsageError("multiple semantic nodes require relation=fusion")
            owners = {(self.targets[key].get("replica"), self.targets[key].get("stage"))
                      for key in ids}
            if len(owners) > 1:
                raise ProfilerUsageError("one device event cannot bind across replicas or pipeline stages")
            self.explicit[event_id] = {**row, "_target_ids": ids}
        for row in value.get("host_scopes", ()):
            if not row.get("name"):
                raise ProfilerUsageError("host scope requires an exact frame name")
            self.host_scopes[row["name"]].update(self.target_index.scope(row))
        for row in value.get("module_scopes", ()):
            module_id = row.get("module_id")
            if not isinstance(module_id, str) or module_id in self.module_scopes:
                raise ProfilerUsageError("module scopes require unique string module_id")
            self.module_scopes[module_id] = self.target_index.scope(row)

    def _load_correlation(self, value):
        identity = value.get("source_identity")
        if not identity:
            raise ProfilerUsageError("correlation lacks source_identity; regenerate it with correlate")
        rank = str(value["rank_id"])
        source_key = (rank, str(Path(identity["path"]).resolve()))
        previous = self.sources.get(source_key)
        if previous is not None and previous != identity:
            raise ProfilerUsageError("correlations describe different versions of the same source")
        self.sources[source_key] = identity
        for call in value.get("correlated_calls", ()):
            self.correlations[_task_key(rank, call["device_task"])].append((source_key, call))

    def _check_source(self, observation):
        key = (observation.rank_id, str(Path(observation.source.path).resolve()))
        identity = self.sources.get(key)
        if identity is not None and (
            identity.get("size_bytes") != observation.source.size_bytes
            or identity.get("mtime_ns") != observation.source.mtime_ns
        ):
            raise ProfilerUsageError("correlation source changed; regenerate correlation before mapping")
        return key

    def _rank_candidates(self, candidates, rank):
        # Physical capture ranks and sim DP replicas have different namespaces.
        # Their placement (including PP stages) must be supplied, never guessed.
        replica, stage = self.rank_replicas.get(rank), self.rank_stages.get(rank)
        return [
            key for key in candidates
            if (replica is None or str(self.targets[key].get("replica")) == replica)
            and (stage is None or str(self.targets[key].get("stage")) == stage)
        ]

    def _implementation_correspondence(self, kind, rank, event=None):
        signature = _event_signature(event) if event is not None else None
        raw = _event_raw_identity(event) if event is not None else None
        key = (kind, rank, _freeze(signature) if signature is not None else None,
               raw)
        if key in self.implementation_correspondences:
            return self.implementation_correspondences[key]
        targets = []
        basis = "declared_native_implementation"
        signature_match = None
        if raw is not None:
            targets = self._rank_candidates(
                self.target_index.native_call_observed.get(raw, ()), rank)
            if targets:
                basis = "observed_hccl_alias_same_call"
                signature_match = True
        if not targets:
            targets = self._rank_candidates(
                self.target_index.native_implementations.get(kind, ()), rank)
        if not targets:
            # BIND1 native-call names (wrapper entry and declared child launch)
            # resolve through the normal mapper only when the event descriptor
            # agrees with the declared typed signature.  A name alone is never
            # enough to make a correspondence.
            candidates = self._rank_candidates(
                [*self.target_index.native_call_entries.get(kind, ()),
                 *self.target_index.native_call_kernels.get(kind, ())], rank)
            if event is not None:
                targets = [
                    node for node in candidates
                    if _native_call_signature_match(
                        self.target_index.native_bindings[node], event) is True
                ]
                signature_match = bool(targets)
            else:
                targets = candidates
            basis = "declared_native_call_signature" if event is not None else (
                "declared_native_call_no_event")
        if targets:
            description = self.target_index.describe_implementation(kind, targets)
            description.update(
                basis=basis,
                rank=rank,
                observed_signature=(
                    {"shapes": [list(shape) for shape in signature[0]],
                     "dtypes": list(signature[1])} if signature is not None else None),
                raw_identity=(
                    {"rank_id": raw[0], "global_task_id": raw[1],
                     "stream_id": raw[2], "task_id": raw[3],
                     "connection_id": raw[4], "device_id": raw[5],
                     "start_ns": raw[6], "end_ns": raw[7]}
                    if raw is not None else None),
                signature_match=signature_match,
                # Raw task identity is occurrence evidence for this signed HCCL
                # packet; tensor-only correspondence remains non-occurrence and
                # prepare-only, never a measured hardware proof.
                observed_proof=(basis == "observed_hccl_alias_same_call"),
                prepare_only_control=(basis != "observed_hccl_alias_same_call"),
                occurrence_binding_implied=(basis == "observed_hccl_alias_same_call"),
            )
            call = description.get("native_call") or {}
            if call.get("call_id"):
                description["call_ids"] = [call["call_id"]]
        else:
            description = None
        self.implementation_correspondences[key] = description
        return description

    def _host_candidates(self, event, source_key):
        scopes = []
        evidence = []
        for candidate_source, call in self.correlations.get(_event_key(event), ()):
            if (candidate_source != source_key or call.get("ambiguous_global_task_id")
                    or call.get("global_task_id_unique") is not True):
                continue
            basis = call.get("association_basis", {})
            unique = call.get("association_unique", {})
            connected = unique.get("pytorch") is True and (
                (basis.get("cann") is None and basis.get("pytorch") == "connection_ids")
                or (basis.get("cann") == "connection_ids" and unique.get("cann") is True
                    and basis.get("pytorch") in {"connection_ids", "same_global_tid_containment"})
            )
            if not connected:
                continue
            # Exact Host names are supplied by the caller; no model-specific
            # layer-number regex or device-time containment invents a scope.
            matched = [
                (frame, self.host_scopes[frame["name"]])
                for frame in call.get("host_stack", ())
                if frame.get("name") in self.host_scopes
            ]
            for frame, nodes in matched:
                scopes.append(set(nodes))
                evidence.append({"frame": frame, "association_basis": basis,
                                 "device_task": call["device_task"]})
        if not scopes:
            return None, []
        return scopes, evidence

    def _match(self, event, observation, source_key):
        from .normalized import row_from_event
        from .tensor_contracts import observed_contract

        row = row_from_event(event, source=observation.source.path)
        contract = observed_contract(row)
        key = _freeze(contract) if contract is not None else None
        candidates = self._rank_candidates(self.contracts.get(key, ()), observation.rank_id)
        candidates, refinement = _shared_kv_candidates(row, contract, candidates, self.targets)
        explicit = self.explicit.get(event.event_id)
        if (refinement and explicit and explicit.get("relation", "direct") == "direct"
                and not set(explicit["_target_ids"]) <= set(candidates)):
            raise ProfilerUsageError(f"explicit binding index descriptor mismatch for {event.event_id}")
        result = self._match_evidence(event, observation, source_key, contract, candidates)
        if (refinement and not candidates and result[0] == "unmapped" and result[3] not in {
                "module_tensor_contract_mismatch", "host_tensor_contract_mismatch",
                "module_has_no_declared_scope",
        }):
            result = (*result[:3], "declared_index_descriptor_mismatch", result[4], contract)
        return (*result, refinement)

    def _match_evidence(self, event, observation, source_key, contract, candidates):
        key = _freeze(contract) if contract is not None else None
        explicit = self.explicit.get(event.event_id)
        if explicit is not None:
            ids = explicit["_target_ids"]
            allowed = self._rank_candidates(ids, observation.rank_id)
            if len(allowed) != len(ids):
                raise ProfilerUsageError(f"explicit binding rank mismatch for {event.event_id}")
            if ids[0] in self.subgraphs:
                expected = self.subgraphs[ids[0]].get("contract")
                if expected is None or contract is None or _freeze(expected) != key:
                    raise ProfilerUsageError(
                        f"explicit subgraph binding tensor contract mismatch for {event.event_id}")
            elif explicit.get("relation", "direct") == "direct":
                expected = self.nodes[ids[0]].get("contract")
                if expected is not None and contract is not None and _freeze(expected) != key:
                    raise ProfilerUsageError(f"explicit binding tensor contract mismatch for {event.event_id}")
            self.used_bindings.add(event.event_id)
            return "bound", ids, candidates, "explicit_evidence", explicit["evidence"], contract
        scoped, evidence = self._host_candidates(event, source_key)
        module_basis = None
        if self.module_evidence is not None:
            module_basis, module_record = self.module_evidence.lookup(event, observation)
            if module_basis not in {None, "contained"}:
                return "ambiguous", [], candidates, module_basis, module_record, contract
            if module_basis == "contained":
                module_nodes = self.module_scopes.get(module_record["module_id"], set())
                scoped = [*(scoped or []), module_nodes]
                evidence = [*evidence, module_record]
        if scoped is not None:
            matches_by_scope = [set(candidates) & scope for scope in scoped]
            matches = sorted(set.intersection(*matches_by_scope))
            combined = sorted(set.union(*matches_by_scope))
            # Nested declared scopes narrow by intersection. A contradictory
            # ancestor or another report must never be discarded as a mismatch.
            if len(matches) == 1:
                basis = ("synchronized_module_and_tensor" if module_basis == "contained"
                         else "host_connection_and_tensor")
                return "bound", matches, matches, basis, evidence, contract
            if combined:
                reason = "host_scope_has_multiple_nodes" if matches else "conflicting_host_scopes"
                if module_basis == "contained":
                    reason = "module_scope_has_multiple_nodes" if matches else "conflicting_evidence_scopes"
                return "ambiguous", [], matches or combined, reason, evidence, contract
            if module_basis == "contained":
                reason = ("module_tensor_contract_mismatch"
                          if module_nodes else "module_has_no_declared_scope")
                return "unmapped", [], candidates, reason, evidence, contract
            return "unmapped", [], candidates, "host_tensor_contract_mismatch", evidence, contract
        if len(candidates) == 1:
            return "candidate", [], candidates, "tensor_contract_only", None, contract
        if candidates:
            return "ambiguous", [], candidates, "repeated_tensor_contract", None, contract
        diagnostic = self._diagnostic(event, observation, contract, candidates)
        reason = diagnostic["reason"]
        return "unmapped", [], [], reason, None, contract

    def _diagnostic(self, event, observation, contract, candidates):
        if candidates:
            return {"category": "occurrence_evidence_missing",
                    "reason": ("tensor_contract_only" if len(candidates) == 1
                               else "repeated_tensor_contract"),
                    "detail": "Tensor matches need independent evidence of the module occurrence."}
        if contract is None:
            from .normalized import row_from_event
            from .tensor_contracts import observed_contract_diagnostic

            return observed_contract_diagnostic(row_from_event(event))
        key = (_freeze(contract), observation.rank_id)
        if key not in self.diagnostics:
            from .structure_diagnostics import mismatch_diagnostic

            declared = [other for other, nodes in self.contracts.items()
                        if self._rank_candidates(nodes, observation.rank_id)]
            self.diagnostics[key] = mismatch_diagnostic(key[0], declared)
        return self.diagnostics[key]

    def map_window(self, observation, *, events=None):
        """Map a bounded window, optionally streaming its normalized events.

        Callers supplying a stream retain source/window identity in observation;
        the same occurrence budget, matching and interval accounting apply.
        With module evidence, streamed windows must cover full event spans so
        that evidence outside a clipped window cannot have been discarded.
        """
        source_key = self._check_source(observation)
        counts = Counter()
        reasons = Counter()
        diagnostic_counts = Counter()
        operators = {}
        intervals = defaultdict(list)
        nodes = {}
        subgraphs = {}
        covered_nodes = set()
        layers = {}
        blocks = {}
        structural_groups = {}
        cohorts = CohortAccumulator(
            self.graph_id, self.target_index, observation,
            execution=self.structure.get("execution"))
        window_sample = []
        for event in observation.events if events is None else events:
            interval = event.clipped(observation.window.start_ns, observation.window.end_ns)
            if interval is None:
                continue
            if (events is not None and self.module_evidence is not None
                    and not event.complete_in(observation.window.start_ns, observation.window.end_ns)):
                raise ProfilerUsageError(
                    "streamed module mapping requires full event bounds in the window; "
                    "retain selected events before loading module evidence for clipped windows")
            self.examined += 1
            if self.examined > self.max_events:
                raise ProfilerUsageError(
                    f"structure mapping exceeds {self.max_events} event-window occurrences; "
                    "select fewer ranks/windows or raise --max-mapping-events"
                )
            status, ids, candidates, basis, evidence, contract, refinement = self._match(
                event, observation, source_key)
            cohort_reason = cohorts.add(
                event, interval, status=status, ids=ids, candidates=candidates,
                basis=basis, contract=contract, refinement=refinement)
            counts[status] += 1
            self.statuses[status] += 1
            reasons[basis] += 1
            self.reasons[basis] += 1
            diagnostic = None if status == "bound" else self._diagnostic(
                event, observation, contract, candidates)
            if basis == "declared_index_descriptor_mismatch":
                diagnostic = {
                    "category": "declared_structure_mismatch", "reason": basis,
                    "detail": ("The captured compressed-index interface disagrees with all "
                               "otherwise compatible declared attention candidates."),
                }
            if status != "bound" and basis in {
                "overlapping_module_invocations", "event_crosses_module_boundary",
                "module_step_mismatch", "conflicting_host_scopes", "conflicting_evidence_scopes",
                "module_tensor_contract_mismatch", "host_tensor_contract_mismatch",
                "module_has_no_declared_scope", "module_scope_has_multiple_nodes",
                "host_scope_has_multiple_nodes",
            }:
                diagnostic = {
                    "category": "occurrence_evidence_conflict", "reason": basis,
                    "detail": ("Inspect the supplied scope declaration and occurrence evidence; "
                               "existing conflicting evidence cannot be replaced by a tensor guess."),
                }
            if diagnostic is not None:
                diagnostic_counts[diagnostic["category"]] += 1
                self.diagnostic_counts[diagnostic["category"]] += 1
            raw_identity = _event_raw_identity(event)
            correspondence = self._implementation_correspondence(
                event.op_type, observation.rank_id, event=event)
            native_identity = None
            if (correspondence is not None
                    and correspondence.get("basis") == "observed_hccl_alias_same_call"):
                native_identity = "observed_raw_identity"
            elif (raw_identity is None
                    and (event.op_type in self.target_index.native_call_alias_names
                         or event.name in self.target_index.native_call_alias_names)):
                native_identity = "unresolved_alias_without_relational_keys"
            native_occurrence = None
            if (correspondence is not None
                    and correspondence.get("basis") == "observed_hccl_alias_same_call"):
                raw = raw_identity
                call = correspondence.get("native_call") or {}
                presentation_id = f"{event.event_id}:{event.op_type}"
                primary = self.hccl_occurrences.setdefault(raw, presentation_id)
                presentation = self.hccl_presentation_counts[raw] + 1
                self.hccl_presentation_counts[raw] = presentation
                native_occurrence = {
                    "call_id": call.get("call_id"),
                    "raw_identity": dict(correspondence.get("raw_identity") or {}),
                    "charge": "call",
                    "call_owner": (call.get("timing_owner") or {}).get("op_id"),
                    "primary_presentation": primary,
                    "alias_of": None if presentation_id == primary else primary,
                    "presentation_id": presentation_id,
                    "presentation_index": presentation,
                    "occurrence_key": list(raw) if raw is not None else None,
                }
            operator = operators.setdefault(event.op_type, {
                "operator_type": event.op_type, "event_count": 0,
                "activity_sum_ns": 0, "complete_activity_sum_ns": 0,
                "complete_event_count": 0, "clipped_event_count": 0,
                "cohort_event_count": 0, "cohort_excluded_event_counts": Counter(),
                "contract_available_events": 0,
                "implementation_correspondence": correspondence,
                "status_counts": Counter(), "reason_counts": Counter(),
                "diagnostic_counts": Counter(),
            })
            operator["event_count"] += 1
            operator["activity_sum_ns"] += interval[1] - interval[0]
            complete = event.complete_in(observation.window.start_ns, observation.window.end_ns)
            operator["complete_event_count" if complete else "clipped_event_count"] += 1
            if complete:
                operator["complete_activity_sum_ns"] += event.duration_ns
            if cohort_reason is None:
                operator["cohort_event_count"] += 1
            else:
                operator["cohort_excluded_event_counts"][cohort_reason] += 1
            operator["contract_available_events"] += int(contract is not None)
            operator["status_counts"][status] += 1
            operator["reason_counts"][basis] += 1
            if diagnostic is not None:
                operator["diagnostic_counts"][diagnostic["category"]] += 1
            intervals["observed"].append(interval)
            intervals[status].append(interval)
            node_ids, subgraph_ids = self.target_index.split(ids)
            covered_nodes.update(member for target in ids for member in self.target_index.members(target))
            candidate_nodes, candidate_subgraphs = self.target_index.split(candidates)
            classification = self.target_index.classify(ids if status == "bound" else candidates)
            if status == "bound":
                classification = {**classification, "basis": "declared_structure_of_bound_targets"}
            common = classification["common"]
            if common:
                group = structural_groups.setdefault(_freeze(common), {
                    **common, "event_count": 0, "status_counts": Counter(),
                    "_intervals": [], "activity_sum_ns": 0,
                    "basis": "declared_target_structure; see_status_counts",
                    "occurrence_binding_implied": False,
                })
                group["event_count"] += 1
                group["status_counts"][status] += 1
                group["_intervals"].append(interval)
                group["activity_sum_ns"] += interval[1] - interval[0]
            for node_id in node_ids:
                node = self.nodes[node_id]
                record = nodes.setdefault(node_id, {
                    "node_id": node_id, "op_id": node.get("op_id"),
                    "replica": node.get("replica"), "stage": node.get("stage"),
                    "layer": node.get("layer"), "block": node.get("block"),
                    "family": node.get("family"), "event_count": 0,
                    "boundary": node.get("boundary"), "lineage": node.get("lineage"),
                    "contract_scope": node.get("contract_scope"),
                    "shared_event_count": 0, "_intervals": [], "activity_sum_ns": 0,
                })
                record["event_count"] += 1
                record["shared_event_count"] += int(len(ids) > 1)
                record["_intervals"].append(interval)
                record["activity_sum_ns"] += interval[1] - interval[0]
            for subgraph_id in subgraph_ids:
                target = self.subgraphs[subgraph_id]
                record = subgraphs.setdefault(subgraph_id, {
                    key: target.get(key) for key in (
                        "subgraph_id", "node_ids", "replica", "stage", "layer", "block",
                        "role", "family", "boundary", "lineage", "contract_scope", "structure",
                        "layer_ids", "owner_scopes", "coverage",
                    )
                })
                record["event_count"] = record.get("event_count", 0) + 1
                record.setdefault("_intervals", []).append(interval)
                record["activity_sum_ns"] = record.get("activity_sum_ns", 0) + interval[1] - interval[0]
                record["member_timing"] = "not_separately_measured"
            # A fusion is inclusive at each semantic node, but occurs once
            # at each enclosing layer and once in the observed window.
            for target, fields in (
                (layers, ("replica", "stage", "layer")),
                (blocks, ("replica", "stage", "layer", "block")),
            ):
                scopes = self.target_index.enclosing_scopes(ids, fields)
                for scope in scopes:
                    record = target.setdefault(scope, {
                        **dict(zip(fields, scope)), "event_count": 0,
                        "_intervals": [], "activity_sum_ns": 0,
                    })
                    record["event_count"] += 1
                    record["_intervals"].append(interval)
                    record["activity_sum_ns"] += interval[1] - interval[0]
            if len(self.sample) < self.mapping_limit:
                from .normalized import row_from_event
                from .native_tensor_abi import native_tensor_contract
                from .tensor_contracts import NATIVE_BODY_TYPES, observed_contract_scope

                normalized = row_from_event(event)
                retain_native = (event.op_type in NATIVE_BODY_TYPES
                                 and (contract is None or contract[0] != "native_tensor_abi"))
                row = {
                    "event_id": event.event_id, "rank_id": observation.rank_id,
                    "step": observation.window.step, "window": observation.window.label,
                    "kernel_name": event.name, "operator_type": event.op_type,
                    "start_ns": event.start_ns, "end_ns": event.end_ns,
                    "clipped_start_ns": interval[0], "clipped_end_ns": interval[1],
                    "source": observation.source.path, "locator": event.locator,
                    "status": status, "node_ids": node_ids, "subgraph_ids": subgraph_ids,
                    "covered_node_ids": sorted({
                        member for target in ids for member in self.target_index.members(target)
                    }),
                    "candidate_node_ids": candidate_nodes[:64],
                    "candidate_subgraph_ids": candidate_subgraphs[:64],
                    "candidate_count": len(candidates), "basis": basis, "evidence": evidence,
                    "candidate_refinement": refinement,
                    "implementation_correspondence": correspondence,
                    "native_call_identity": native_identity,
                    "native_call_occurrence": native_occurrence,
                    "structural_classification": classification,
                    "observed_contract": contract,
                    "observed_contract_scope": observed_contract_scope(normalized),
                    "observed_native_tensor_abi": (
                        native_tensor_contract(normalized) if retain_native else None),
                    "diagnostic": diagnostic,
                }
                self.sample.append(row)
                window_sample.append(row)
        hccl_groups = defaultdict(list)
        for row in window_sample:
            occurrence = row.get("native_call_occurrence")
            if occurrence and occurrence.get("occurrence_key") is not None:
                hccl_groups[tuple(occurrence["occurrence_key"])].append(row)
        native_calls = []
        for key, rows in hccl_groups.items():
            presentations = [row["native_call_occurrence"]["presentation_id"]
                             for row in rows]
            for row in rows:
                row["native_call_occurrence"].update(
                    presentations=presentations,
                    presentation_count=len(presentations))
            occurrence = rows[0]["native_call_occurrence"]
            starts = [row["clipped_start_ns"] for row in rows]
            ends = [row["clipped_end_ns"] for row in rows]
            native_calls.append({
                "call_id": occurrence.get("call_id"),
                "rank_id": key[0],
                "raw_identity": occurrence.get("raw_identity"),
                "charge": "call",
                "call_owner": occurrence.get("call_owner"),
                "presentation_count": len(presentations),
                "presentations": presentations,
                "representative_event_id": rows[0]["event_id"],
                "activity_ns": max(ends) - min(starts),
                "accounting_basis": "one_call_alias_union_not_sum_of_presentations",
            })
        for record in [*nodes.values(), *subgraphs.values(), *layers.values(), *blocks.values(),
                       *structural_groups.values()]:
            record["busy_union_ns"] = _union_ns(record.pop("_intervals"))
            record["attribution"] = "inclusive_nonadditive"
        total = sum(counts.values())
        observed_ns = _union_ns(intervals["observed"]) if total else None
        bound_ns = _union_ns(intervals["bound"]) if total else None
        return {
            "rank_id": observation.rank_id, "step": observation.window.step,
            "source_identity": observation.source.content_identity(),
            "window": {"start_ns": observation.window.start_ns, "end_ns": observation.window.end_ns,
                       "label": observation.window.label},
            "event_count": total, "status_counts": dict(counts), "reason_counts": dict(reasons),
            "diagnostic_counts": dict(diagnostic_counts),
            "bound_event_fraction": counts["bound"] / total if total else None,
            "observed_busy_union_ns": observed_ns,
            "bound_busy_union_ns": bound_ns,
            "bound_busy_fraction": bound_ns / observed_ns if observed_ns else None,
            "rank_scope": {
                "replica": self.rank_replicas.get(observation.rank_id),
                "stage": self.rank_stages.get(observation.rank_id),
                "basis": "caller_declared" if observation.rank_id in self.rank_replicas
                         or observation.rank_id in self.rank_stages else "unspecified",
            },
            "nodes": list(nodes.values()), "layers": list(layers.values()),
            "blocks": list(blocks.values()),
            "subgraphs": list(subgraphs.values()),
            "covered_node_ids": sorted(covered_nodes),
            "cohorts": cohorts.finish(),
            "cohort_excluded_event_counts": dict(cohorts.excluded),
            "structural_groups": [
                {**record, "status_counts": dict(record["status_counts"])}
                for record in structural_groups.values()
            ],
            "operators": [
                {key: dict(value) if isinstance(value, Counter) else value
                 for key, value in operator.items()}
                for _, operator in sorted(operators.items())
            ],
            "unobserved_node_ids": sorted(
                set(self._rank_candidates(self.nodes, observation.rank_id)) - covered_nodes),
            "unobserved_subgraph_ids": sorted(
                set(self._rank_candidates(self.subgraphs, observation.rank_id)) - set(subgraphs)),
            "native_calls": native_calls, "native_call_count": len(native_calls),
        }

    def finish(self, windows):
        unused = sorted(set(self.explicit) - self.used_bindings)
        native_calls = [call for window in windows
                        for call in window.get("native_calls", ())]
        native_identity_counts = Counter(
            row.get("native_call_identity") for row in self.sample
            if row.get("native_call_identity") is not None)
        cohort_count = sum(
            group["event_count"] for window in windows for group in window["cohorts"])
        return {
            "schema_version": SCHEMA, "graph_id": self.graph_id,
            "structure_source": self.structure.get("source"),
            "declared_execution": self.structure.get("execution"),
            "observed_phase": self.phase,
            "status": ("mapped" if self.examined and self.statuses["bound"] == self.examined
                       else "partial" if self.statuses["bound"] else "unresolved"),
            "event_window_count": self.examined,
            "status_counts": dict(self.statuses), "reason_counts": dict(self.reasons), "windows": windows,
            "diagnostic_counts": dict(self.diagnostic_counts),
            "cohort_event_window_count": cohort_count,
            "cohort_status": "aggregated" if cohort_count else "unavailable",
            "cohort_event_fraction": cohort_count / self.examined if self.examined else None,
            "module_evidence": self.module_evidence.summaries if self.module_evidence else [],
            "event_mappings": self.sample, "retained_event_mappings": len(self.sample),
            "event_mappings_truncated": self.examined > len(self.sample),
            "native_calls": native_calls, "native_call_count": len(native_calls),
            "native_call_identity_counts": dict(native_identity_counts),
            "unused_explicit_event_ids": unused,
            "semantics": {
                "structure": "declared; absence of a measured event does not prove nonexecution",
                "candidate": "tensor contract match; not a verified layer assignment",
                "bound": ("explicit occurrence evidence, Host connection plus tensor contract, "
                          "or hash-verified synchronized module containment plus tensor contract"),
                "timing": "measured clipped intervals only; no predicted costs or duration-based matching",
                "aggregation": "independent windows; node/layer/block unions are inclusive and not additive",
                "subgraphs": ("declared semantic members share one measured boundary; "
                              "member timings are not separately measured"),
                "implementation_correspondence": (
                    "native types index independently declared implementation boundaries; "
                    "this alone does not establish tensor compatibility or an occurrence"),
                "structural_classification": ("properties shared by all compatible declared targets; "
                                              "does not establish a layer or invocation"),
                "cohorts": ("identical declared contract and physical work on one placement; "
                            "measured multiplicity and complete-event duration statistics without "
                            "per-layer allocation; window counts do not establish step counts"),
                "candidate_refinement": (
                    "source-defined optional tensor interfaces can narrow candidates; "
                    "missing or unsupported descriptors do not select a bucket, and "
                    "compression ratio, context and occurrence are not inferred"),
                "rank": "physical rank is not a DP replica; only explicit placement filters candidates",
            },
        }
