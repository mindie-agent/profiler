"""Import retained literal graph and deployment conditions into replay declarations.

[Role] Read compilation/additional config and literal deployment topology from a
  caller-selected cmd.sh.
[Invariants] Command text is never executed; model names, paths and timings never
  select a capture policy. Missing, ambiguous, dynamic or unsupported topology
  remains explicit. A supported DP1 + TP>1 + enabled-EP MoE command derives
  EP=TP; only an inherited tp_join_reduce recipe is replaced by the existing
  alltoall graph recipe. Explicit caller/native declarations are preserved and
  reported rather than overwritten.
[Timeouts & Locks] One small local command file; no subprocesses or locks.
[Side-Effect Policy] Return copied input and source provenance; no file writes.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shlex


MC2_ALIGNMENT_SOURCE = {
    "repository": "vllm-ascend",
    "revision": "8c30e4f491f73cba737a1dacc522894e437cdf3d",
    "forward_context": {
        "repository_path": "vllm_ascend/ascend_forward_context.py", "lines": [216, 226],
        "sha256": "ab5110b44b2b951f0f55d09fcc90c316f6515bb8d085a5fdd0ac1b1b1dcd099e",
    },
    "prepare_finalize": {
        "repository_path": "vllm_ascend/ops/fused_moe/prepare_finalize.py", "lines": [291, 325],
        "sha256": "41dc995d6a8b2ec714733eb229803ad45e6ed0f09d40a531bd764ac794f2b902",
    },
    "formula": "ceil(max_tokens_across_dp / tp_world_size) * tp_world_size",
    "scope": "MC2 prepare padding and TP slicing; finalize trims to original rows",
    "capture_binary_identity": "unknown",
}


DEPLOYMENT_SCHEMA = "mindie-profiler-capture-deployment/1"
INHERITED_MOE_RECIPES = frozenset({"alltoall", "tp_join_reduce"})
MOE_PARTITION_KINDS = frozenset({"vllm_ascend_mc2_tp_slice",
                                 "vllm_ascend_alltoall_tp_slice"})
REMAINING_LIMITS = (
    "deployment flags correct only the DP1/TP>1/enabled-EP domain; other axes are not derived",
    "capture EP does not select MC2, fusion, native_moe_protocol, routing counts or max_inflight_per_rank",
    "legacy FFN service responses still match by recipe and row domain, not by corrected local-expert banks or intermediate width",
    "single-rank capture does not prove peer groups, group_list values, native binary identity or per-forward rates",
)


def _complete_mc2_alignment(runtime):
    caller = runtime.get("kernels", {}).get("moe_token_partition")
    if (not isinstance(caller, dict) or caller.get("kind") != "vllm_ascend_mc2_tp_slice"
            or "padding" in caller):
        return None
    scopes = caller.get("layer_scopes")
    if scopes is not None:
        # None selects every scope. A nonempty list/tuple of body/draft selects
        # only those scopes; malformed or draft-only declarations are excluded.
        if (not isinstance(scopes, (list, tuple)) or not scopes
                or any(scope not in {"body", "draft"} for scope in scopes)
                or "body" not in scopes):
            return None
    # MC2 pads after the full-row router, then slices across TP. Captured graph
    # keys govern attention/shared rows and must not absorb this local padding.
    caller["padding"] = "right_to_tp"
    return {"field": "runtime.kernels.moe_token_partition.padding",
            "value": "right_to_tp", "basis": "already_selected_mc2_caller_source_semantics",
            "source": deepcopy(MC2_ALIGNMENT_SOURCE)}


def _literal_config(tokens, option):
    values = []
    error_prefix = "capture_" + option.removeprefix("--").replace("-", "_")
    for index, token in enumerate(tokens):
        if token == option:
            if index + 1 >= len(tokens):
                raise ValueError(error_prefix + "_missing_value")
            values.append(tokens[index + 1])
        elif token.startswith(option + "="):
            values.append(token.split("=", 1)[1])
    if not values:
        return None
    if len(values) != 1:
        raise ValueError(error_prefix + "_ambiguous_multiple_declarations")
    try:
        config = json.loads(values[0])
    except json.JSONDecodeError as error:
        raise ValueError(error_prefix + "_requires_literal_json") from error
    if not isinstance(config, dict):
        raise ValueError(error_prefix + "_requires_object")
    return config


def _deployment_error(option, suffix):
    return "capture_" + option.removeprefix("--").replace("-", "_") + "_" + suffix


def _flag_values(tokens, option):
    """Collect exact and ``--option=value`` occurrences without shell expansion."""
    return [(index, token.split("=", 1)[1]) if token != option else (index, None)
            for index, token in enumerate(tokens)
            if token == option or token.startswith(option + "=")]


def _literal_positive_integer(tokens, option):
    occurrences = _flag_values(tokens, option)
    if not occurrences:
        return None
    if len(occurrences) != 1:
        raise ValueError(_deployment_error(option, "ambiguous_multiple_declarations"))
    index, inline = occurrences[0]
    if inline is None:
        if index + 1 >= len(tokens):
            raise ValueError(_deployment_error(option, "missing_value"))
        value = tokens[index + 1]
    else:
        value = inline
    if "$" in value or "`" in value:
        raise ValueError(_deployment_error(option, "requires_literal_integer"))
    if not value.isascii() or not value.isdigit():
        raise ValueError(_deployment_error(option, "requires_literal_integer"))
    number = int(value)
    if number < 1:
        raise ValueError(_deployment_error(option, "requires_positive_integer"))
    return number


def _literal_expert_parallel(tokens):
    positive = "--enable-expert-parallel"
    negative = "--no-enable-expert-parallel"
    declarations = []
    for index, token in enumerate(tokens):
        if token in (positive, negative):
            declarations.append((index, token == positive))
        elif token.startswith(positive + "=") or token.startswith(negative + "="):
            raise ValueError(_deployment_error(positive, "rejects_explicit_value"))
    if not declarations:
        return None
    if len(declarations) != 1:
        raise ValueError(_deployment_error(positive, "ambiguous_multiple_declarations"))
    index, value = declarations[0]
    if index + 1 < len(tokens) and tokens[index + 1] in {"true", "false", "1", "0"}:
        # The source CLI uses argparse.BooleanOptionalAction. Any following
        # boolean word would be a positional, not this flag's value.
        raise ValueError(_deployment_error(positive, "rejects_explicit_value"))
    return value


def _deployment_declaration(tokens):
    declared = {
        "tensor_parallel_size": _literal_positive_integer(tokens, "--tensor-parallel-size"),
        "data_parallel_size": _literal_positive_integer(tokens, "--data-parallel-size"),
        "expert_parallel": _literal_expert_parallel(tokens),
    }
    missing = sorted(name for name, value in declared.items() if value is None)
    return {"declared": declared, "missing": missing,
            "provided": sorted(name for name, value in declared.items() if value is not None)}


def _runtime_axis(runtime, name):
    parallel = runtime.get("parallel")
    if isinstance(parallel, dict) and name in parallel:
        return parallel[name]
    return runtime.get(name)


def _runtime_snapshot(runtime):
    return {"tp": _runtime_axis(runtime, "tp"), "dp": _runtime_axis(runtime, "dp"),
            "ep": _runtime_axis(runtime, "ep"), "pp": _runtime_axis(runtime, "pp"),
            "moe_recipe": runtime.get("moe_recipe")}


def _assign_axis(runtime, name, value):
    """Write one declared axis only when it differs from the replay template."""
    parallel = runtime.get("parallel")
    target = parallel if isinstance(parallel, dict) else runtime
    other = runtime if target is not runtime else parallel
    if _runtime_axis(runtime, name) == value:
        return None
    target[name] = value
    if isinstance(other, dict) and name in other:
        other[name] = value
    return "runtime." + ("parallel." if target is not runtime else "") + name


def _supported_topology(runtime, model, declared):
    """Return the derived DP1/EP=TP topology or an explicit refusal."""
    tp = declared["tensor_parallel_size"]
    dp = declared["data_parallel_size"]
    expert_parallel = declared["expert_parallel"]
    if tp is None:
        return None, "tensor_parallel_size_missing", None
    if dp is None:
        return None, "data_parallel_size_missing", None
    if expert_parallel is None:
        return None, "expert_parallel_not_declared", None
    if expert_parallel is False:
        return None, "expert_parallel_disabled", None
    if tp < 2:
        return None, "tensor_parallel_size_not_greater_than_one", None
    if dp != 1:
        return None, "data_parallel_size_not_one", None
    if not isinstance(model, dict) or not model or model.get("ffn") != "moe":
        return None, "moe_model_required", None
    experts = model.get("num_experts")
    if type(experts) is not int or experts < 2:
        return None, "moe_model_required", None
    if experts % tp:
        return None, "experts_not_divisible_by_derived_ep", None
    for name in ("pp", "cp", "dcp", "pcp"):
        value = _runtime_axis(runtime, name)
        if value is None:
            continue
        if type(value) is not int or value != 1:
            return None, "template_" + name + "_not_one", None
    # The retained command supplies the physical deployment; the simulator
    # schema validates every remaining axis before any field is written.
    try:
        from mindie_sim.schema.common import ModelingError
        from mindie_sim.schema.model import ModelSpec
        from mindie_sim.schema.parallel import ParallelSpec
        cp = _runtime_axis(runtime, "cp")
        if cp is None:
            cp = _runtime_axis(runtime, "dcp")
        spec = ModelSpec.from_mapping(model)
        ParallelSpec(dp=1, tp=tp, ep=tp, pp=_runtime_axis(runtime, "pp") or 1,
                     cp=cp or 1, pcp=_runtime_axis(runtime, "pcp") or 1).validate(spec)
    except ModelingError as error:
        return None, "unsupported_topology", str(error)
    return (tp, 1, tp), None, None


def _deployment_record(*, status, reason, declaration, before, after, changed_fields,
                       derived=None, conflicts=(), preserved=(), detail=None):
    record = {
        "schema_version": DEPLOYMENT_SCHEMA,
        "status": status,
        "reason": reason,
        "declared": deepcopy(declaration["declared"]),
        "derived": deepcopy(derived or {}),
        "missing": list(declaration["missing"]),
        "before": deepcopy(before),
        "after": deepcopy(after),
        "changed_fields": list(changed_fields),
        "timing_values_used": False,
    }
    if detail:
        record["detail"] = detail
    if conflicts:
        record["preserved_conflicts"] = list(conflicts)
    if preserved:
        record["preserved_explicit"] = list(preserved)
    if declaration["provided"]:
        record["remaining_limits"] = list(REMAINING_LIMITS)
    return record


def _native_protocol_conflicts(native):
    """Validate an explicit native mapping with the Sim selector, never a copy."""
    if not isinstance(native, dict):
        return [{"field": "runtime.kernels.native_moe_protocol",
                 "value": deepcopy(native),
                 "reason": "explicit_incompatible_native_protocol"}]
    from mindie_sim.prediction.mc2_graph import select
    from mindie_sim.schema.common import ModelingError
    try:
        select({"native_moe_protocol": native})
    except ModelingError as error:
        return [{"field": "runtime.kernels.native_moe_protocol",
                 "value": deepcopy(native),
                 "reason": "explicit_incompatible_native_protocol",
                 "detail": str(error)}]
    return []


def _declaration_state(runtime, ep):
    """Classify caller/native declarations before any topology field is written."""
    conflicts, preserved = [], []
    recipe = runtime.get("moe_recipe")
    switch_recipe = ep > 1 and recipe == "tp_join_reduce"
    if recipe is not None and recipe not in INHERITED_MOE_RECIPES:
        conflicts.append({"field": "runtime.moe_recipe", "value": deepcopy(recipe),
                          "reason": "explicit_incompatible_moe_recipe"})
    kernels = runtime.get("kernels")
    if not isinstance(kernels, dict):
        return conflicts, preserved, switch_recipe
    partition = kernels.get("moe_token_partition")
    if partition is not None:
        kind = partition.get("kind") if isinstance(partition, dict) else None
        if kind not in MOE_PARTITION_KINDS:
            conflicts.append({"field": "runtime.kernels.moe_token_partition.kind",
                              "value": deepcopy(kind),
                              "reason": "explicit_incompatible_caller"})
        else:
            preserved.append({"field": "runtime.kernels.moe_token_partition",
                              "value": deepcopy(kind),
                              "status": "preserved_explicit"})
    if "native_moe_protocol" in kernels:
        native = kernels["native_moe_protocol"]
        native_conflicts = _native_protocol_conflicts(native)
        if native_conflicts:
            conflicts.extend(native_conflicts)
        else:
            preserved.append({"field": "runtime.kernels.native_moe_protocol",
                              "value": deepcopy(native),
                              "status": "preserved_unresolved"})
    if "moe_transport" in kernels:
        preserved.append({"field": "runtime.kernels.moe_transport",
                          "value": deepcopy(kernels["moe_transport"]),
                          "status": "preserved_explicit"})
    return conflicts, preserved, switch_recipe


def _apply_deployment(result, declaration):
    """Apply only the supported literal deployment topology to the copied case."""
    runtime = result.get("runtime")
    provided = bool(declaration["provided"])
    if not isinstance(runtime, dict):
        before = {}
        reason = "deployment_flags_not_declared" if not provided else "runtime_not_declared"
        status = "not_provided" if not provided else "unsupported"
        return _deployment_record(status=status, reason=reason, declaration=declaration,
                                  before=before, after=before, changed_fields=[])
    before = _runtime_snapshot(runtime)
    if not provided:
        return _deployment_record(status="not_provided",
                                  reason="deployment_flags_not_declared",
                                  declaration=declaration, before=before, after=before,
                                  changed_fields=[])
    derived, reason, detail = _supported_topology(
        runtime, result.get("model"), declaration["declared"])
    if derived is None:
        return _deployment_record(status="unsupported", reason=reason, detail=detail,
                                  declaration=declaration, before=before, after=before,
                                  changed_fields=[])
    tp, dp, ep = derived
    derived_fields = {
        "ep": ep,
        "basis": "declared_dp1_tp_gt1_enabled_expert_parallel_and_moe_model_imply_ep_equals_tp",
        "source": "retained_capture_command",
    }
    conflicts, preserved, switch_recipe = _declaration_state(runtime, ep)
    if conflicts:
        # An explicit incompatible caller/native declaration is not a clean
        # deployment success. Preserve the physical replay input and let graph
        # import keep its independent outcome in the top-level provenance.
        return _deployment_record(
            status="conflict", reason="explicit_incompatible_declaration",
            declaration=declaration, derived=derived_fields,
            before=before, after=before, changed_fields=[],
            conflicts=conflicts, preserved=preserved)
    changed = []
    for name, value in (("tp", tp), ("dp", dp), ("ep", ep)):
        field = _assign_axis(runtime, name, value)
        if field:
            changed.append(field)
    if switch_recipe:
        runtime["moe_recipe"] = "alltoall"
        changed.append("runtime.moe_recipe")
    after = _runtime_snapshot(runtime)
    status = "applied" if changed else "unchanged"
    return _deployment_record(
        status=status,
        reason=("literal_captured_deployment_topology_imported" if changed
                else "declared_topology_already_matches"),
        declaration=declaration, derived=derived_fields,
        before=before, after=after, changed_fields=changed,
        conflicts=conflicts, preserved=preserved)


def _empty_declaration():
    return {"declared": {"tensor_parallel_size": None, "data_parallel_size": None,
                         "expert_parallel": None},
            "missing": ["data_parallel_size", "expert_parallel", "tensor_parallel_size"],
            "provided": []}


def _automatic_structure_scope(deployment):
    """The batch1a EP1/tp_join_reduce -> DP1/EP=TP/alltoall correction only."""
    if deployment.get("status") != "applied":
        return False
    before, after = deployment.get("before") or {}, deployment.get("after") or {}
    return (before.get("dp") == 1 and before.get("ep") == 1
            and before.get("moe_recipe") == "tp_join_reduce"
            and after.get("dp") == 1
            and after.get("ep") == after.get("tp")
            and type(after.get("ep")) is int and after["ep"] > 1
            and after.get("moe_recipe") == "alltoall")


def _not_evaluated_structure(reason):
    return {
        "schema_version": "mindie-profiler-native-structure/1",
        "status": "not_evaluated",
        "reason": reason,
        "semantic_equivalence": False,
        "exact_native_kernel_match": False,
        "timing_values_used": False,
    }


def import_capture_policy(raw: dict, *, capture_path: str | Path,
                          reconcile_structure: bool = False) -> tuple[dict, dict]:
    """Apply literal graph/deployment fields and retain caller conditions without guessing."""
    source = Path(capture_path)
    command = source if source.name == "cmd.sh" else (
        source / "cmd.sh" if source.is_dir() else source.parent / "cmd.sh")
    result = deepcopy(raw)
    provenance = {"schema_version": "mindie-profiler-capture-policy-import/1",
                  "status": "not_provided", "capture_path": str(source),
                  "command_path": str(command), "command_executed": False,
                  "timing_values_used": False, "provided_fields": [], "changed_fields": []}
    try:
        data = command.read_bytes()
    except FileNotFoundError:
        before = (_runtime_snapshot(raw["runtime"])
                  if isinstance(raw.get("runtime"), dict) else {})
        deployment = _deployment_record(
            status="not_provided", reason="capture_command_not_present",
            declaration=_empty_declaration(), before=before, after=before,
            changed_fields=[])
        return result, {**provenance, "reason": "capture_command_not_present",
                        "graph_status": "not_provided",
                        "graph_reason": "capture_command_not_present",
                        "deployment": deployment}
    provenance["command_sha256"] = sha256(data).hexdigest()
    tokens = shlex.split(data.decode("utf-8"), comments=True, posix=True)
    declaration = _deployment_declaration(tokens)
    config = _literal_config(tokens, "--compilation-config")
    additional = _literal_config(tokens, "--additional-config")
    deployment_provided = bool(declaration["provided"])
    if config is None and additional is None and not deployment_provided:
        deployment = _apply_deployment(result, declaration)
        return result, {**provenance, "reason": "compilation_config_not_declared",
                        "graph_status": "not_provided",
                        "graph_reason": "compilation_config_not_declared",
                        "deployment": deployment}
    fields = {name: config[name] for name in ("cudagraph_mode", "cudagraph_capture_sizes")
              if config is not None and name in config}
    if not fields and additional is None and not deployment_provided:
        deployment = _apply_deployment(result, declaration)
        return result, {**provenance, "reason": "graph_policy_fields_not_declared",
                        "graph_status": "not_provided",
                        "graph_reason": "graph_policy_fields_not_declared",
                        "deployment": deployment}

    graph_status = "not_provided"
    graph_reason = ("compilation_config_not_declared" if config is None and additional is None
                    else "graph_policy_fields_not_declared")
    graph_changed = []
    if fields or additional is not None:
        provenance["provided_fields"] = sorted(
            [*fields, *(["additional_config"] if additional is not None else [])])
        provenance["captured_fields"] = deepcopy(fields)
        if additional is not None:
            provenance["captured_fields"]["additional_config"] = deepcopy(additional)
        provenance["missing_fields"] = sorted(
            {"cudagraph_mode", "cudagraph_capture_sizes"} - fields.keys())
        mode = fields.get("cudagraph_mode")
        if mode is not None and mode not in {"NONE", "FULL_DECODE_ONLY"}:
            graph_status, graph_reason = "unsupported", "capture_mode_not_represented"
        else:
            sizes = fields.get("cudagraph_capture_sizes")
            if sizes is not None and (not isinstance(sizes, list) or
                    any(type(size) is not int or size <= 0 for size in sizes)
                    or len(set(sizes)) != len(sizes)):
                raise ValueError("capture_graph_sizes_require_unique_positive_integers")
            runtime = result.setdefault("runtime", {})
            before = deepcopy(runtime)
            if additional is not None:
                runtime.setdefault("metadata", {})["captured_additional_config"] = deepcopy(additional)
            if mode is not None:
                runtime["graph_mode"] = "none" if mode == "NONE" else "auto"
                runtime["graph_capture_mode"] = "none" if mode == "NONE" else "full"
                runtime.setdefault("metadata", {})["captured_execution_mode"] = mode
                if mode == "NONE":
                    runtime["graph_capture_keys"] = []
                    runtime["graph_buckets"] = []
                runtime["piecewise_capture_keys"] = []
            if sizes is not None:
                sizes = sorted(sizes)
                runtime.setdefault("metadata", {})["cudagraph_capture_sizes"] = sizes
                selected = runtime.get("graph_capture_mode", "full")
                if selected == "full":
                    runtime["graph_capture_keys"] = sizes
                    runtime["graph_buckets"] = sizes
                if selected == "piecewise":
                    runtime["piecewise_capture_keys"] = sizes
            if fields:
                alignment = _complete_mc2_alignment(runtime)
                if alignment is not None:
                    provenance["source_conditions"] = [alignment]
            graph_changed = sorted(
                key for key in runtime if before.get(key) != runtime[key])
            graph_status = ("applied" if not provenance["missing_fields"]
                            else "partially_provided")
            graph_reason = "literal_captured_compilation_fields_imported"

    deployment = _apply_deployment(result, declaration)
    provenance["deployment"] = deployment
    if deployment["status"] == "conflict":
        native_structure = _not_evaluated_structure("deployment_conflict")
        legacy_guard = {"status": "not_evaluated", "reason": "deployment_conflict",
                        "removed_ids": [], "removed_count": 0,
                        "timing_values_modified": False}
    elif (_automatic_structure_scope(deployment)
          or (reconcile_structure and deployment["status"] in {"applied", "unchanged"})):
        from capture_structure import apply_captured_structure, guard_actual_ffn_rules
        native_structure = apply_captured_structure(
            result, before_case=raw, capture_path=source,
            command_sha256=provenance.get("command_sha256"), bind_caller=True)
        guard_evidence = {
            "source": native_structure.get("source"),
            "prepare": (native_structure.get("evidence") or {}).get("prepare"),
        }
        legacy_guard = guard_actual_ffn_rules(
            result, before_case=raw, evidence=guard_evidence,
            command_sha256=provenance.get("command_sha256"))
    else:
        native_structure = _not_evaluated_structure("automatic_scope_not_met")
        legacy_guard = {"status": "not_evaluated", "reason": "automatic_scope_not_met",
                        "removed_ids": [], "removed_count": 0,
                        "timing_values_modified": False}
    if isinstance(native_structure, dict):
        native_structure["topology"] = {
            "declared": deepcopy(deployment.get("declared") or {}),
            "derived": deepcopy(deployment.get("derived") or {}),
            "before": deepcopy(deployment.get("before") or {}),
            "after": deepcopy(deployment.get("after") or {}),
        }
    provenance["native_structure"] = native_structure
    provenance["legacy_ffn_guard"] = legacy_guard
    top_changed = set(graph_changed)
    for field in deployment["changed_fields"]:
        parts = field.split(".")
        if len(parts) >= 2 and parts[0] == "runtime":
            top_changed.add(parts[1])
    if native_structure.get("caller", {}).get("applied_fields"):
        top_changed.add("kernels")
    if legacy_guard.get("status") == "applied":
        top_changed.add("kernels")
    provenance["changed_fields"] = sorted(top_changed)

    provenance["graph_status"] = graph_status
    provenance["graph_reason"] = graph_reason
    if native_structure.get("status") == "conflict":
        status, reason = "conflict", native_structure.get("reason")
    elif deployment["status"] == "conflict":
        status, reason = "conflict", deployment["reason"]
    elif graph_status == "unsupported":
        status, reason = "unsupported", graph_reason
    elif (native_structure.get("status") in {"not_provided", "unsupported",
                                              "mixed_unsupported", "unresolved"}
          and deployment["status"] in {"applied", "unchanged"}):
        status, reason = "partially_provided", "native_structure_" + native_structure["status"]
    elif graph_status in {"applied", "partially_provided"}:
        status = graph_status
        reason = ("literal_captured_compilation_and_deployment_fields_imported"
                  if deployment["status"] == "applied" else graph_reason)
    elif deployment["status"] == "applied":
        status, reason = "applied", deployment["reason"]
    elif deployment["status"] == "unchanged":
        status, reason = "unchanged", deployment["reason"]
    elif deployment["status"] == "unsupported":
        status, reason = "unsupported", deployment["reason"]
    else:
        status, reason = "not_provided", graph_reason
    provenance.update(status=status, reason=reason)
    return result, provenance
