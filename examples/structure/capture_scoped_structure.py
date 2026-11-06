"""Phase/geometry-scoped native caller projection for one explicit capture.

[Role] Expose the stable prepared-capture API: resolve one requested geometry
  from compact retained evidence and bind only the A3 AllToAll TP-slice or A5
  eager local-expert caller that the selected native window proves.
[Invariants] Only declared boundaries and physical geometry select a window;
  elapsed durations never do. Native observed rows, dispatch allocation and
  generated expected local-valid rows stay separate. Missing, mixed, malformed
  or conflicting evidence remains unbound; explicit declarations are preserved.
  Failed scans, parser errors and TimeoutError propagate.
[Timeouts & Locks] One prepared evidence scan per capture; apply is bounded
  in-memory contract lookup plus one target graph. No locks or device work.
[Side-Effect Policy] Read-only; returns a copied input and provenance. Source
  paths, hashes and counts never enter the physical predictor input.
"""
from __future__ import annotations

from copy import deepcopy
import json

from capture_scoped_contracts import (
    ALLTOALL_KIND,
    LOCAL_EXPERT_RECIPE,
    UNOBSERVED,
)
from capture_scoped_evidence import (
    MAX_ACTIVE_WINDOWS,
    MAX_SCAN_ROWS,
    SCAN_TIMEOUT_S,
    complete_transport,
    prepare_evidence,
    transport_conflicts,
)


SCHEMA = "mindie-profiler-scoped-native-structure/1"


class PreparedScopedCapture:
    """One capture's compact per-geometry evidence, reusable per geometry."""

    def __init__(self, *, capture_path, observation_identity, source_before,
                 source_after, declared_source, contracts, topology, scan,
                 context_offset, global_error=None):
        self.capture_path = capture_path
        self.observation_identity = observation_identity
        self.source_before = source_before
        self.source_after = source_after
        self.declared_source = declared_source
        self.contracts = contracts
        self.topology = topology
        self.scan = scan
        self.context_offset = context_offset
        self.global_error = global_error

    def geometries(self):
        return [
            {"phase": key[0], "tokens": key[1], "sequences": key[2],
             "context": key[3], "query_rows": key[4],
             "status": value.get("status", "unbound"),
             "reason": value.get("reason"),
             "window_count": value.get("window_count", 0)}
            for key, value in sorted(self.contracts.items())
        ]

    def apply(self, raw, *, phase, tokens, context, sequences=1,
              replace_recipe=False, archive_template=False):
        geometry = {"phase": phase, "tokens": tokens, "context": context,
                    "sequences": sequences}
        provenance = _provenance(
            self.source_before or {}, self.observation_identity, geometry,
            "not_provided", "prepared_capture_not_applied")
        provenance["scan"] = dict(self.scan)
        provenance["source_after_scan"] = deepcopy(self.source_after)
        provenance["context_offset"] = self.context_offset
        if self.global_error is not None:
            provenance.update(self.global_error)
            return deepcopy(raw), provenance
        parsed, error = _probe(raw)
        if parsed is None:
            provenance.update(status="unsupported", **error)
            return deepcopy(raw), provenance
        topology_error = _topology_matches(self.topology, parsed)
        if topology_error is not None:
            provenance.update(status="unbound", reason=topology_error)
            return deepcopy(raw), provenance
        key = (phase, tokens, sequences, context, tokens * sequences)
        contract = self.contracts.get(key)
        provenance["selection"] = {
            "window_count": (contract or {}).get("window_count", 0),
            "witnesses": list((contract or {}).get("witnesses", [])),
            "first_conflict": deepcopy((contract or {}).get("first_conflict")),
            "geometries": self.geometries(),
        }
        if contract is None:
            provenance.update(status="unbound",
                              reason="requested_geometry_not_in_prepared_capture")
            return deepcopy(raw), provenance
        if contract.get("status") != "ok":
            provenance.update(status="unbound",
                              reason=contract.get("reason",
                                                  "prepared_window_unbound"),
                              first_conflict=deepcopy(contract.get("first_conflict")))
            return deepcopy(raw), provenance
        analysis = deepcopy(contract["analysis"])
        analysis["window_count"] = contract.get("window_count", 0)
        analysis["witnesses"] = list(contract.get("witnesses", []))
        provenance["analysis"] = analysis
        provenance["topology"] = deepcopy(self.topology)
        family = analysis["family"]
        action = _apply_caller(
            deepcopy(raw), analysis, family, replace_recipe, archive_template)
        provenance["caller"] = deepcopy(action)
        provenance["declaration"] = deepcopy(analysis["declaration"])
        if action["conflicts"]:
            provenance.update(status="conflict",
                              reason="explicit_caller_conflict",
                              preserved_conflicts=action["conflicts"])
            return deepcopy(raw), provenance
        candidate = _candidate(raw, analysis, family)
        sim = _sim_validate(
            candidate, family=family, window=contract["primary_window"],
            tp=self.topology["tp"], ep=self.topology["ep"],
            hidden=self.topology["hidden_size"],
            experts=self.topology["num_experts"],
            top_k=self.topology["top_k"],
            intermediate=self.topology["moe_intermediate_size"],
            material=analysis["declaration"].get(
                "moe_token_partition", {}).get("gather_output_materialization"),
            phase=phase, tokens=tokens, context=context, sequences=sequences)
        provenance["sim"] = sim
        if not sim["supported"]:
            provenance.update(status="unbound", reason=sim["reason"])
            return deepcopy(raw), provenance
        provenance.update(status="applied", reason="scoped_caller_applied",
                          applied_fields=action["fields"])
        return candidate, provenance


def prepare_scoped_capture(capture_path, observation, *, raw, context_offset=0,
                           max_rows=MAX_SCAN_ROWS, timeout_s=SCAN_TIMEOUT_S,
                           max_active_windows=MAX_ACTIVE_WINDOWS):
    """Prepare one capture once; see capture_scoped_evidence for bounds."""
    data = prepare_evidence(
        capture_path, observation, raw=raw, context_offset=context_offset,
        max_rows=max_rows, timeout_s=timeout_s,
        max_active_windows=max_active_windows)
    return PreparedScopedCapture(
        capture_path=capture_path,
        observation_identity=data.get("observation_identity"),
        source_before=data.get("source_before"),
        source_after=data.get("source_after"),
        declared_source=data.get("declared_source"),
        contracts=data.get("contracts", {}),
        topology=data.get("topology", {}),
        scan=data.get("scan", {"scanned_rows": 0, "windows": 0}),
        context_offset=context_offset,
        global_error=data.get("global_error"))


def apply_scoped_structure(raw, *, capture_path, observation, phase, tokens,
                           context, sequences=1, replace_recipe=False,
                           archive_template=False, context_offset=0,
                           max_rows=MAX_SCAN_ROWS, timeout_s=SCAN_TIMEOUT_S):
    """Convenience adapter: prepare one capture, then apply one geometry."""
    prepared = prepare_scoped_capture(
        capture_path, observation, raw=raw, context_offset=context_offset,
        max_rows=max_rows, timeout_s=timeout_s)
    return prepared.apply(
        raw, phase=phase, tokens=tokens, context=context, sequences=sequences,
        replace_recipe=replace_recipe, archive_template=archive_template)


def _probe(raw):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.schema.common import ModelingError

    probe = deepcopy(raw)
    runtime = probe.get("runtime")
    if isinstance(runtime, dict):
        runtime.pop("moe_recipe", None)
        kernels = runtime.get("kernels")
        if isinstance(kernels, dict):
            kernels.pop("moe_token_partition", None)
            kernels.pop("moe_transport", None)
    try:
        return parse_case(probe), None
    except ModelingError as error:
        return None, {"reason": "case_parse_error", "detail": str(error)}


def _topology(parsed):
    parallel, model = parsed.runtime.parallel, parsed.model
    return {"tp": parallel.tp, "dp": parallel.dp, "ep": parallel.ep,
            "etp": parallel.etp, "pp": parallel.pp, "cp": parallel.cp,
            "pcp": parallel.pcp, "layers": model.layers,
            "hidden_size": model.hidden_size,
            "num_experts": model.num_experts, "top_k": model.top_k,
            "moe_intermediate_size": model.moe_intermediate_size,
            "routing": deepcopy(getattr(parsed.runtime, "routing", {}))}


def _topology_matches(stored, parsed):
    if not stored:
        return "prepared_topology_unavailable"
    return (None if _topology(parsed) == stored
            else "prepared_topology_differs_from_requested_input")


def _apply_caller(result, analysis, family, replace_recipe, archive_template):
    return (_apply_a3(result, analysis["declaration"])
            if family == "alltoall_tp_slice"
            else _apply_a5(result, analysis["declaration"], replace_recipe,
                           archive_template))


def _candidate(raw, analysis, family):
    candidate = deepcopy(raw)
    runtime = candidate.setdefault("runtime", {})
    kernels = runtime.setdefault("kernels", {})
    if family == "alltoall_tp_slice":
        partition = analysis["declaration"]["moe_token_partition"]
        transport = analysis["declaration"]["moe_transport"]
        existing_partition = kernels.get("moe_token_partition")
        if isinstance(existing_partition, dict):
            existing_partition.update(deepcopy(partition))
        else:
            kernels["moe_token_partition"] = deepcopy(partition)
        existing_transport = kernels.get("moe_transport")
        if isinstance(existing_transport, dict):
            kernels["moe_transport"] = complete_transport(existing_transport)
        else:
            kernels["moe_transport"] = deepcopy(transport)
    else:
        runtime["moe_recipe"] = LOCAL_EXPERT_RECIPE
    return candidate


def _sim_validate(candidate, *, family, window, tp, ep, hidden, experts, top_k,
                  intermediate, material, phase, tokens, context, sequences):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.schema.common import ModelingError
    from mindie_sim import target_operators
    from capture_scoped_contracts import generated_mismatches

    try:
        parse_case(candidate)
    except ModelingError as error:
        detail = str(error)
        if (family == "local_expert_reduce"
                and "moe_requires_registered_recipe" in detail):
            return {"supported": False,
                    "reason": "sim_local_expert_reduce_recipe_unavailable",
                    "detail": detail}
        return {"supported": False, "reason": "sim_declaration_rejected",
                "detail": detail}
    try:
        ops = target_operators(candidate, phase=phase, tokens=tokens,
                               context=context, sequences=sequences)
    except ModelingError as error:
        return {"supported": False, "reason": "sim_generated_graph_unavailable",
                "detail": str(error)}
    mismatches = generated_mismatches(
        family, ops, window=window, tp=tp, ep=ep, hidden=hidden,
        experts=experts, top_k=top_k, intermediate=intermediate,
        material=material,
        routing=(candidate.get("runtime") or {}).get("routing"))
    return {"supported": not mismatches,
            "reason": ("generated_graph_matched" if not mismatches
                       else "generated_graph_mismatch"),
            "mismatches": mismatches,
            "generated": _generated_summary(ops)}


def _generated_summary(ops):
    selected = {"grouped_gate_up", "grouped_down", "grouped_swiglu",
                "route_pack", "route_unpack", "moe_output_reduce",
                "expert_scale_dispatch", "expert_quantized_dispatch",
                "expert_combine", "tensor_copy", "ring_allgather",
                "moe_expert_count_histogram"}
    layers = {}
    for op in ops:
        if op.layer is None or op.recipe not in selected:
            continue
        layers.setdefault(op.layer, []).append({
            "recipe": op.recipe, "local_shape": tuple(op.local_shape),
            "metadata": {key: value for key, value in dict(op.metadata).items()
                         if key in {"moe_token_partition", "histogram_dtype",
                                    "payload_dtype", "scale_dtype",
                                    "traffic_model", "gathered_slice",
                                    "matrix_weight_bank_groups"}},
        })
    return [{"layer": layer, "facts": facts}
            for layer, facts in sorted(layers.items())]


def _conflict(field, value, reason):
    return {"field": field, "value": deepcopy(value), "reason": reason}


def _result(action, fields=(), conflicts=(), preserved=()):
    return {"action": action, "fields": list(fields),
            "conflicts": list(conflicts), "preserved": list(preserved)}


def _apply_a3(result, declaration):
    runtime = result.setdefault("runtime", {})
    kernels = runtime.setdefault("kernels", {})
    partition = declaration["moe_token_partition"]
    transport = declaration["moe_transport"]
    conflicts, preserved, fields = [], [], []
    if runtime.get("moe_recipe") not in (None, "alltoall"):
        conflicts.append(_conflict("runtime.moe_recipe",
                                   runtime.get("moe_recipe"),
                                   "explicit_incompatible_moe_recipe"))
    existing_partition = kernels.get("moe_token_partition")
    if existing_partition is not None:
        if (not isinstance(existing_partition, dict)
                or existing_partition.get("kind") != ALLTOALL_KIND):
            conflicts.append(_conflict("runtime.kernels.moe_token_partition",
                                       existing_partition,
                                       "explicit_caller_not_scoped_alltoall"))
        else:
            if set(existing_partition) - {
                    "kind", "padding", "gather_output_materialization",
                    "layer_scopes"}:
                conflicts.append(_conflict(
                    "runtime.kernels.moe_token_partition", existing_partition,
                    "explicit_caller_has_unexpected_fields"))
            scopes = existing_partition.get("layer_scopes")
            if (scopes is not None
                    and (not isinstance(scopes, (list, tuple))
                         or "body" not in scopes)):
                conflicts.append(_conflict(
                    "runtime.kernels.moe_token_partition.layer_scopes",
                    scopes, "explicit_caller_scope_excludes_body"))
            if ("padding" in existing_partition
                    and existing_partition["padding"] != "none"):
                conflicts.append(_conflict(
                    "runtime.kernels.moe_token_partition.padding",
                    existing_partition["padding"],
                    "explicit_alltoall_padding_incompatible"))
            if ("gather_output_materialization" in existing_partition
                    and existing_partition["gather_output_materialization"]
                    != partition["gather_output_materialization"]):
                conflicts.append(_conflict(
                    "runtime.kernels.moe_token_partition.gather_output_materialization",
                    existing_partition["gather_output_materialization"],
                    "explicit_gather_materialization_incompatible"))
    existing_transport = kernels.get("moe_transport")
    conflicts.extend(transport_conflicts(existing_transport))
    if conflicts:
        return _result("conflict", [], conflicts, preserved)
    if existing_partition is None:
        kernels["moe_token_partition"] = deepcopy(partition)
        fields.append("runtime.kernels.moe_token_partition")
        action = "bound"
    else:
        completed = []
        for field in ("padding", "gather_output_materialization"):
            if field not in existing_partition:
                existing_partition[field] = partition[field]
                completed.append(
                    "runtime.kernels.moe_token_partition." + field)
        fields.extend(completed)
        preserved.append({"field": "runtime.kernels.moe_token_partition",
                          "value": deepcopy(existing_partition),
                          "status": "preserved_explicit"})
        action = "completed" if completed else "preserved"
    if existing_transport is None:
        kernels["moe_transport"] = deepcopy(transport)
        fields.append("runtime.kernels.moe_transport")
    else:
        completed = complete_transport(existing_transport)
        if completed != existing_transport:
            kernels["moe_transport"] = completed
            fields.append("runtime.kernels.moe_transport")
            action = "completed"
        preserved.append({"field": "runtime.kernels.moe_transport",
                          "value": deepcopy(completed),
                          "status": "preserved_explicit"})
    return _result(action, fields, conflicts, preserved)


def _apply_a5(result, declaration, replace_recipe, archive_template):
    runtime = result.setdefault("runtime", {})
    kernels = runtime.setdefault("kernels", {})
    conflicts, preserved, fields = [], [], []
    recipe = runtime.get("moe_recipe")
    if recipe is None:
        runtime["moe_recipe"] = LOCAL_EXPERT_RECIPE
        fields.append("runtime.moe_recipe")
        action = "bound"
    elif recipe == LOCAL_EXPERT_RECIPE:
        action = "preserved"
    elif (replace_recipe and archive_template
          and recipe in {"alltoall", "tp_join_reduce"}):
        preserved.append({"field": "runtime.moe_recipe",
                          "value": deepcopy(recipe),
                          "status": "replaced_inherited_template_recipe",
                          "basis": "archive_template_adaptation"})
        runtime["moe_recipe"] = LOCAL_EXPERT_RECIPE
        fields.append("runtime.moe_recipe")
        action = "replaced"
    elif replace_recipe and not archive_template:
        conflicts.append(_conflict(
            "runtime.moe_recipe", recipe,
            "recipe_replacement_requires_archive_template"))
        action = "conflict"
    else:
        conflicts.append(_conflict("runtime.moe_recipe", recipe,
                                   "explicit_incompatible_moe_recipe"))
        action = "conflict"
    for field, reason in (
            ("moe_token_partition",
             "explicit_token_partition_conflicts_with_local_expert"),
            ("moe_transport",
             "explicit_transport_conflicts_with_local_expert"),
            ("native_moe_protocol",
             "explicit_native_protocol_conflicts_with_local_expert")):
        if field in kernels:
            conflicts.append(_conflict("runtime.kernels." + field,
                                       kernels[field], reason))
    return _result("conflict" if conflicts else action,
                   [] if conflicts else fields, conflicts, preserved)


def _provenance(source, observation, geometry, status, reason):
    return {"schema_version": SCHEMA, "status": status, "reason": reason,
            "geometry": deepcopy(geometry), "source": deepcopy(source),
            "observation": deepcopy(observation),
            "timing_values_used": False, "observations_modified": False,
            "semantic_equivalence": False,
            "exact_native_kernel_match": False,
            "source_paths_in_predictor_input": False,
            "unobserved": list(UNOBSERVED)}
