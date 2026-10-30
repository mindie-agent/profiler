"""Map complete GLM native ABI buckets to existing declared semantic programs.

[Role] Validate active parameters before creating conditional program references.
[Invariants] Every aligned layer must select the same physical program set.
  Buffer extents never prove routing, accepted-token values or sparse lengths.
  Full native histograms remain intact; these references are never strict binds.
[Timeouts & Locks] Bounded per-source layer metadata; no workers or locks.
[Side-Effect Policy] Pure mappings; no raw capture reads or Sim cost execution.
"""
from collections import defaultdict
from hashlib import sha256

from body_source_role_references import canonical, reference_signature
from rebind_body_source_roles import freeze


def _slot(slot, shape, dtype, layout="ND"):
    return slot == (tuple(shape), dtype, layout)


def _subgraph(role, groups, local):
    matches = [g for g in groups if g["role"] == role]
    if len(matches) != 1:
        raise ValueError("semantic_subgraph_not_unique:" + role)
    group = matches[0]
    ids = set(group["node_ids"])
    targets = [node for node in local if node["node_id"] in ids]
    if len(targets) != len(ids):
        raise ValueError("semantic_subgraph_members_missing")
    return group, targets


def _mx_swiglu(native, local, groups, execution):
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (6, 2):
        raise ValueError("mx_swiglu_native_slot_count")
    x, xs, route, weight, ws, assist = ins
    y, ys = outs
    if len(x[0]) != 2 or len(y[0]) != 2 or len(route[0]) != 1:
        raise ValueError("mx_swiglu_rank")
    capacity, hidden = x[0]; out_rows, width = y[0]; experts = route[0][0]
    if (min(capacity, hidden, width, experts) <= 0 or capacity != out_rows
            or hidden % 64 or width % 64 or (2 * width) % 32
            or not _slot(x, (capacity, hidden), "fp8_e4m3")
            or not _slot(y, (capacity, width), "fp8_e4m3")
            or not _slot(xs, (capacity, hidden // 64, 2), "fp8_e8m0", "NCL")
            or not _slot(ys, (capacity, width // 64, 2), "fp8_e8m0")
            or not _slot(route, (experts,), "int64")
            or not _slot(weight, (experts, 2 * width // 32, hidden // 16, 16, 32), "fp8_e4m3", "FRACTAL_NZ")
            or not _slot(ws, (experts, hidden // 64, 2 * width, 2), "fp8_e8m0", "NCHW")
            or assist != ((), "fp32", "ND")):
        raise ValueError("mx_swiglu_fp8_packed_parameter_abi")
    semantic, targets = _subgraph("grouped_gate_up_activation_quant", groups, local)
    by_role = {t["op_id"].split(".", 2)[-1]: t for t in targets}
    if set(by_role) != {"expert_up", "expert_act", "expert_down.quantize"}:
        raise ValueError("mx_swiglu_declared_boundary")
    upper = freeze(by_role["expert_up"]["contract"])
    if (not upper or upper[0] != "grouped_matrix"
            or (upper[1][0], upper[1][2], upper[1][3]) != (experts, 2 * width, hidden)
            or upper[2:5] != ("fp8_e4m3", "fp8_e4m3", "bf16")
            or upper[5][1:] != (hidden // 64, 2) or upper[6] != "fp8_e8m0"):
        raise ValueError("mx_swiglu_declared_expert_geometry")
    rows = upper[1][1]
    if (freeze(by_role["expert_act"]["contract"]) != ("swiglu", (rows, width), "bf16")
            or freeze(by_role["expert_down.quantize"]["contract"]) !=
               ("DynamicMxQuant", (rows, width), "bf16", "fp8_e4m3", (rows, width // 64, 2), "fp8_e8m0")):
        raise ValueError("mx_swiglu_declared_epilogue_geometry")
    return semantic["role"], targets, semantic.get("source"), {
        "boundary_relation": "FP8_MX_expert_gate_up_activation_quant_decomposed_reference",
        "observed_buffer_row_capacity": capacity, "observed_valid_routed_rows": None,
        "observed_group_list_values": None, "declared_valid_routed_rows": rows,
        "validated_expert_bank_channels": [experts, hidden, width],
        "native_fusion_resource_program_selected": False,
        "limitations": ["Current native fusion traffic profiles cover INT8/INT4, not this FP8 MX ABI.",
            "The unfused reference retains intermediate memory and launches; no fused accuracy is implied.",
            "Expert group-list values and active routing distribution are not retained."]}


def kda_native_geometry(native, execution):
    """Validate the retained eleven-slot ABI without selecting an implementation."""
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (11, 3):
        raise ValueError("kda_native_slot_count")
    gate, beta, state, prefix, slots, alog, bias, accepted = ins[3:]
    batch, q = execution["sequences"], execution["tokens"]
    if len(gate[0]) != 4:
        raise ValueError("kda_gate_rank")
    _, rows, heads, width = gate[0]
    if (rows != batch * q or width != 128
            or not _slot(gate, (1, rows, heads, width), "bf16")
            or not _slot(beta, (1, rows, heads), "bf16")
            or not _slot(prefix, (batch + 1,), "int32")
            or not _slot(slots, (batch, q), "int32")
            or not _slot(accepted, (batch,), "int32")
            or not _slot(alog, (heads,), "fp32")
            or not _slot(bias, (heads * width,), "fp32")
            or any(len(x[0]) != 1 or x[1:] != ("bf16", "ND")
                   or x[0][0] < rows * heads * width for x in ins[:3])
            or len(state[0]) != 1 or state[1:] != ("fp32", "ND")
            or state[0][0] < batch * heads * width * width
            or not _slot(outs[0], (rows * heads * width,), "bf16")
            or outs[1:] != (state, state)):
        raise ValueError("kda_gate_state_metadata_abi")
    return {"batch": batch, "query": q, "rows": rows, "heads": heads,
            "width": width, "accepted_descriptor": accepted}


def _kda(native, local, groups, execution):
    geometry = kda_native_geometry(native, execution)
    batch, q, rows, heads, width = (geometry[name] for name in
                                  ("batch", "query", "rows", "heads", "width"))
    accepted = geometry["accepted_descriptor"]
    semantic, targets = _subgraph("kda_recurrent", groups, local)
    scans = [t for t in targets if t["family"] == "recurrent_scan"]
    if (len(scans) != batch or any(tuple(t["operator"]["local_shape"]) != (q, heads, width, width)
                                  for t in scans)
            or {t["family"] for t in targets} != {"recurrent_scan", "elementwise"}):
        # The exact source adapter rejects accepted-token state slots; this
        # comparison intentionally uses the declared complete generic subgraph.
        raise ValueError("kda_declared_generic_sequence_geometry")
    return semantic["role"], targets, semantic.get("source"), {
        "boundary_relation": "whole_batch_generic_gating_and_recurrent_reference",
        "observed_gate_geometry": [rows, heads, width], "declared_sequence_count": batch,
        "observed_accepted_tokens_descriptor": accepted, "observed_accepted_token_values": None,
        "observed_state_indices_values": None, "observed_qkv_active_strides": None,
        "native_source_adapter_status": "accepted_token_state_slot_branch_not_supported",
        "limitations": ["The native accepted-token tensor is present; do not bind the no-accepted-array arch35 source program.",
            "Flat QKV/state backing extent does not establish active views or checkpoint slot values.",
            "The reference prices the existing generic normalization/gating and all sequence scans, including their launches."]}


def _sparse_mla(native, local, groups, execution):
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (18, 2):
        raise ValueError("sparse_mla_native_slot_count")
    x, cache, indices, table = ins[0], ins[1], ins[3], ins[5]
    batch, q = execution["sequences"], execution["tokens"]
    if len(x[0]) != 3 or len(cache[0]) != 4 or len(table[0]) != 2 or len(indices[0]) != 3:
        raise ValueError("sparse_mla_rank")
    rows, heads, width = x[0]
    if (rows != batch * q or not _slot(x, (rows, heads, width), "bf16") or outs[0] != x
            or cache[0][1:] != (128, 1, width) or cache[1:] != ("bf16", "ND")
            or not _slot(indices, (rows, 1, indices[0][2]), "int32")
            or not _slot(table, (batch, table[0][1]), "int32")
            or not _slot(ins[7], (batch + 1,), "int32")
            or not _slot(ins[11], (batch,), "int32")
            or not _slot(ins[14], (rows, 1), "int32")
            or not _slot(ins[16], (heads,), "fp32")
            or not _slot(ins[17], (1024,), "int32")
            or any(ins[i] != ((), None, None) for i in (2, 4, 6, 8, 9, 10, 12, 13, 15))
            or outs[1] != ((), "fp32", "ND")):
        raise ValueError("sparse_mla_uncompressed_paged_native_abi")
    targets = [t for t in local if t["family"] == "attention"
               and t["operator"]["metadata"].get("program_kind") == "indexed_attention"]
    if not targets:
        raise ValueError("sparse_mla_declared_batch_programs")
    declared = [t["operator"]["metadata"]["indexed_attention_geometry"] for t in targets]
    if any((v["heads"], v["latent"], v["rope"], v["query_dtype"], v["cache_dtype"])
           != (heads, width, 0, "bf16", "bf16") for v in declared):
        raise ValueError("sparse_mla_declared_head_channel_precision")
    sequences = [tuple(item) for v in declared for item in v.get(
        "sequences", [(v.get("query"), v.get("context"))])]
    if sequences != [(q, execution["context"])]*batch:
        raise ValueError("sparse_mla_declared_batch_programs")
    topks = {v["topk"] for v in declared}
    if len(topks) != 1 or indices[0][2] < next(iter(topks)):
        raise ValueError("sparse_mla_index_capacity_smaller_than_declared_topk")
    return "indexed_attention_batch", targets, {"kind": "existing_declared_indexed_attention_programs"}, {
        "boundary_relation": "whole_batch_indexed_attention_reference",
        "observed_sparse_index_capacity": indices[0][2], "declared_topk": next(iter(topks)),
        "observed_topk_length_values": None, "observed_sequence_length_values": None,
        "observed_metadata_values": None, "observed_cache_capacity_is_active_context": False,
        "declared_sequence_count": batch, "declared_sequence_program_count": len(targets),
        "limitations": ["All sequence programs are priced jointly; one sequence is never substituted for one native batch call.",
            "Native sparse index capacity includes slots whose valid count is supplied by an unobserved tensor.",
            "Mask/window scalars, metadata task split, sinks values and active KV lengths are not retained.",
            "Declared indexed attention is a reference, not proof of the captured SparseFlashMla native implementation."]}


SELECTORS = {"GroupedMatmulSwigluQuantV2": _mx_swiglu, "RecurrentKda": _kda, "SparseFlashMla": _sparse_mla}


def prepare_references(partitions, manifest, *, selectors=None):
    """Return homogeneous complete buckets and a small cost manifest."""
    selectors = SELECTORS if selectors is None else selectors
    replica = min(manifest["execution"]["replicas"])
    by_layer, subgraphs = defaultdict(list), defaultdict(list)
    for node in manifest["nodes"]:
        if node["replica"] == replica:
            by_layer[node.get("layer")].append(node)
    for group in manifest["subgraphs"]:
        if group["replica"] == replica:
            subgraphs[group.get("layer")].append(group)
    references, failures, selected_nodes = [], [], {}
    for index, group in enumerate(partitions["partitions"]):
        native = freeze(group["native_abi"]); kind = group["native_operator_type"]
        layers = sorted(map(int, group["layer_counts"]))
        first, signature, problem = None, None, None
        try:
            if native[:2] != ("native_tensor_abi", kind) or not layers:
                raise ValueError("retained_native_identity_or_layers_missing")
            for layer in layers:
                selection = selectors[kind](native, by_layer[layer], subgraphs[layer], manifest["execution"])
                role, targets, source, correspondence = selection
                physical = canonical([(reference_signature(t), t["physical_work"]) for t in targets])
                if signature is not None and signature != physical:
                    raise ValueError("heterogeneous_fresh_layer_programs_cannot_split_saved_histogram")
                if first is None:
                    first, signature = selection, physical
        except ValueError as error:
            problem = str(error)
        if problem:
            failures.append({"partition_index": index, "native_operator_type": kind,
                "event_count": group["observed_us"]["count"], "status": "unresolved", "reason": problem})
            continue
        role, targets, source, correspondence = first
        selected_nodes.update((t["node_id"], t) for t in targets)
        references.append({"group_id": "sha256:" + sha256(canonical((index, native, signature)).encode()).hexdigest(),
            "partition_index": index, "native_operator_type": kind, "declared_role": role,
            "native_abi": native, "layer_ids": layers, "representative_replica": replica,
            "representative_target_ids": [t["node_id"] for t in targets],
            "physical_program_signatures": [t["physical_signature"] for t in targets],
            "physical_work_per_program": [t["physical_work"] for t in targets],
            "program_set_key": sha256(signature.encode()).hexdigest(),
            "source_anchor_declaration": source, "source_correspondence": correspondence,
            "observed_us": group["observed_us"], "duration_ns_counter": group["duration_ns_counter"],
            "observed_activity_sum_ns": sum(ns * n for ns, n in group["duration_ns_counter"]),
            "original_partition_histogram_unchanged": True, "occurrence_binding_implied": False,
            "strict_accuracy_implied": False, "additional_budget_allowed": False})
    return references, failures, {"execution": manifest["execution"],
        "graph_id": manifest["graph_id"], "nodes": list(selected_nodes.values())}
