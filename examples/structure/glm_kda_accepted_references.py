"""Conditional source programs for GLM's retained accepted-state KDA ABI.

[Role] Match full native buckets to explicitly selected Sim recurrent programs.
[Invariants] Symbolic acceptance selects the initial state, never reduces query
  work. BF16 beta does not prove an in-kernel sigmoid or private caller identity.
  Native histograms remain whole; references never enter strict accuracy.
[Timeouts & Locks] Bounded declaration checks, no locks or subprocesses.
[Side-Effect Policy] Pure selector; no capture access, costs, or Sim mutation.
"""
from glm_native_references import _subgraph, kda_native_geometry


def accepted_recurrent(native, local, groups, execution):
    geometry = kda_native_geometry(native, execution)
    batch, q, heads, width = (geometry[name] for name in
                              ("batch", "query", "heads", "width"))
    semantic, targets = _subgraph("kda_recurrent", groups, local)
    if len(targets) != 1 or targets[0]["family"] != "recurrent_scan":
        raise ValueError("accepted_kda_requires_one_complete_batch_source_program")
    target = targets[0]
    metadata = target["operator"]["metadata"]
    params = metadata.get("kda_recurrent_params", {})
    implementation = metadata.get("implementation")
    if (implementation not in {"vllm_ascend_recurrent_kda_arch22",
                                "vllm_ascend_recurrent_kda_arch35"}
            or semantic["implementation"]["selection"] != implementation
            or tuple(params.get("lengths", ())) != (q,) * batch
            or (params.get("heads"), params.get("key_heads"), params.get("dk"), params.get("dv"))
               != (heads, heads, width, width)
            or (params.get("dtype"), params.get("gate_dtype"), params.get("beta_dtype"),
                params.get("state_dtype"), params.get("metadata_dtype"))
               != ("bf16", "bf16", "bf16", "fp32", "int32")
            or not params.get("has_accepted_tokens") or not params.get("has_state_indices")
            or not params.get("has_initial_state") or not params.get("state_v_first")):
        raise ValueError("accepted_kda_declared_source_geometry_or_precision")
    raw = params.get("state_selection", {})
    resolved = metadata.get("state_selection", {})
    validity = {"prefix", "state_indices", "accepted_tokens", "independent_sequences"}
    if (raw.get("kind") != "symbolic_valid_selection"
            or raw.get("index_layout") != "speculative" or raw.get("index_row_stride") != q
            or set(raw.get("validity", {})) != validity
            or any(raw["validity"][name] is not True for name in validity)
            or any(name in raw for name in ("prefix", "state_indices", "accepted_tokens", "state_capacity"))
            or resolved.get("acceptance_changes_query_work") is not False
            or resolved.get("capture_value_identity") != "not_established"
            or resolved.get("initial_state") != "indices[b,accepted[b]-1]"
            or resolved.get("checkpoint_state") != "indices[b,t] for every current query t"):
        raise ValueError("accepted_kda_requires_explicit_symbolic_initial_state_only")
    flags = {name: params.get(name) for name in
             ("use_qk_l2norm", "use_gate_in_kernel", "use_beta_sigmoid", "safe_gate", "allow_neg_eigval")}
    return "kda_recurrent", targets, semantic.get("source"), {
        "boundary_relation": "whole_batch_symbolic_accepted_state_source_reference",
        "selected_implementation": implementation,
        "observed_gate_geometry": [geometry["rows"], heads, width],
        "declared_sequence_count": batch, "declared_queries_per_sequence": q,
        "declared_total_query_work": batch * q,
        "observed_accepted_tokens_descriptor": geometry["accepted_descriptor"],
        "observed_accepted_token_values": None, "observed_state_indices_values": None,
        "observed_prefix_values": None, "observed_qkv_active_strides": None,
        "observed_state_output_address_alias": None,
        "state_selection": resolved, "declared_kernel_flags": flags,
        "observed_kernel_flags": None, "private_caller_sigmoid_placement": "not_established",
        "native_source_adapter_status": "explicit_conditional_accepted_state_program",
        "limitations": [
            "Symbolic valid selection is a caller assumption about the initial checkpoint; all current queries execute and write checkpoints.",
            "Accepted counts, state indices, prefix values, independent state pools and flat active views are not captured.",
            "BF16 beta establishes storage precision only; the declared in-kernel sigmoid is not proven by dtype.",
            "A private caller with an external FP32 sigmoid is a different boundary and is not represented by this native-only reference.",
            "The selected public source does not prove private binary dispatch; strict capture matching remains disabled."]}


SELECTORS = {"RecurrentKda": accepted_recurrent}
