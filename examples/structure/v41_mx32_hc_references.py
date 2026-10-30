"""Relate retained V4.1 MC2/HCPre buckets to explicitly selected source programs.

[Role] Validate complete native interfaces before selecting fresh resource work.
[Invariants] MX32 applies only to BF16-to-E4M3/E8M0 dispatch. Whole histograms
  cannot be split when saved layers have different work. HCPre's extra tensor
  remains an uncovered branch, and routed counts/peer waits remain unknown.
[Timeouts & Locks] Bounded per-source metadata; no workers, locks or raw reads.
[Side-Effect Policy] Pure selections; no case edits, cost execution or devices.
"""
from collections import defaultdict
from hashlib import sha256

from body_source_role_references import canonical
from kimi_native_references import program_signature
from rebind_body_source_roles import freeze

PRE_PROFILE = "hc_pre_arch35_mk_175ef4d4"


def _slot(value, shape, dtype):
    return value == (tuple(shape), dtype, "ND")


def _vector(value, dtype):
    return len(value[0]) == 1 and value[0][0] > 0 and value[1:] == (dtype, "ND")


def _mc2(native, local, execution):
    kind = native[1]
    dispatch = kind == "MoeDistributeDispatchV3"
    inputs, outputs = native[2:]
    if (len(inputs), len(outputs)) != ((8, 7) if dispatch else (19, 1)):
        raise ValueError("v41_mc2_native_arity")
    comm, x, ids = inputs[:3]
    y = outputs[0]
    if len(x[0]) != 2 or len(y[0]) != 2 or len(ids[0]) != 2:
        raise ValueError("v41_mc2_native_active_ranks")
    source_rows, topk = ids[0]
    capacity, width = (y if dispatch else x)[0]
    if (min(source_rows, topk, capacity, width) <= 0 or width % 256
            or source_rows != execution["tokens"] * execution["sequences"]
            or not _vector(comm, "int32") or not _slot(ids, (source_rows, topk), "int32")
            or x[0][1] != y[0][1]
            or not _slot(x if dispatch else y, (source_rows, width), "bf16")):
        raise ValueError("v41_mc2_native_source_rows_topk_dtype")
    empty = ((), None, None)
    if dispatch:
        if (not _slot(y, (capacity, width), "fp8_e4m3")
                or not _slot(outputs[1], (capacity, width // 32), "fp8_e8m0")
                or inputs[3] != empty or not _slot(inputs[4], (source_rows,), "bool")
                or inputs[5:] != (empty,) * 3
                or not _vector(outputs[2], "int32") or not _vector(outputs[3], "int64")
                or not _vector(outputs[4], "int32") or not _slot(outputs[5], (1,), "int32")
                or not _slot(outputs[6], (capacity,), "fp32")):
            raise ValueError("v41_mx32_dispatch_full_abi")
    elif (not _slot(x, (capacity, width), "bf16")
            or not _vector(inputs[3], "int32") or not _vector(inputs[4], "int32")
            or not _slot(inputs[5], (source_rows, topk), "fp32")
            or not _slot(inputs[6], (1,), "int32")
            or not _slot(inputs[7], (source_rows,), "bool")
            or inputs[8:11] != (empty,) * 3
            or not _slot(inputs[11], (capacity,), "fp32") or inputs[12:] != (empty,) * 7):
        raise ValueError("v41_float_combine_full_abi")
    targets = [n for n in local if n["operator"]["metadata"].get("native_kind") == kind]
    phases = [n["operator"]["metadata"]["mc2_phase"] for n in targets if n["family"] == "mc2_protocol"]
    if not phases:
        raise ValueError("v41_mc2_source_protocol_not_selected")
    for phase in phases:
        if ((phase["source_tokens"], phase["top_k"], phase["width"], phase["dtype"]) !=
                (source_rows, topk, width, "bf16")
                or phase["kind"] != ("dispatch" if dispatch else "combine")
                or phase["ep"] < 2
                or (dispatch and not 0 <= phase["received_assignments"] <= capacity)
                or (not dispatch and not 0 <= phase["source_assignments"] <= capacity)):
            raise ValueError("v41_mc2_declared_source_geometry")
        if dispatch and (phase.get("dispatch_quant") != "mx" or phase.get("payload_dtype") != "fp8_e4m3"
                or outputs[3][0] != (phase["experts"] // phase["ep"],)
                or outputs[4][0] != (phase["experts"],)):
            raise ValueError("v41_mc2_declared_mx32_or_expert_counts")
    return targets, {
        "boundary_relation": "MX32_dispatch_complete_source_protocol_reference" if dispatch else "float_combine_complete_source_protocol_reference",
        "observed_native_tensor_contract": native, "observed_source_rows": source_rows,
        "observed_top_k": topk, "observed_buffer_row_capacity": capacity,
        "observed_valid_routed_rows": None, "observed_group_count_values": None,
        "observed_peer_readiness": None, "observed_scale_values": None,
        "dispatch_payload_quantization": "MX32_E4M3_E8M0" if dispatch else "not_applicable_float_return",
        "declared_source_phases": phases,
        "communication_bandwidth_calibration_allowed": False,
        "limitations": ["The complete native ABI establishes storage representations, not dynamic routed rows, masks, group counts or peer readiness.",
            "Source phases execute the full declared DP peer cohort; its latencies are not added into one rank's elapsed time.",
            "Native communication elapsed may include synchronization/peer waits; service residuals cannot fit link bandwidth.",
            "Explicit fullmesh peer window and source binary correspondence remain conditional."]}


def _pre(native, role, groups, local, execution):
    inputs, outputs = native[2:]
    if (len(inputs), len(outputs)) != (5, 4) or len(inputs[0][0]) != 3:
        raise ValueError("v41_hc_pre_complete_native_abi")
    rows, hc, width = inputs[0][0]
    expected_inputs = (((rows, hc, width), "bf16", "ND"), ((24, hc * width), "fp32", "ND"),
        ((3,), "fp32", "ND"), ((24,), "fp32", "ND"), ((rows, hc), "fp32", "ND"))
    expected_outputs = (((rows, width), "bf16", "ND"), ((rows, hc), "fp32", "ND"),
        ((rows, hc, hc), "fp32", "ND"), ((rows, hc), "fp32", "ND"))
    if hc != 4 or rows != execution["tokens"] * execution["sequences"] or inputs != expected_inputs or outputs != expected_outputs:
        raise ValueError("v41_hc_pre_native_parameters")
    block = role.split(".", 1)[0]
    semantic = [g for g in groups if g["role"] == "hc_pre" and g["block"] == block]
    if len(semantic) != 1:
        raise ValueError("v41_hc_pre_subgraph_not_unique")
    group = semantic[0]
    if freeze(group["contract"]) != ("hyper_connection_active", "HcPre", inputs[:4], outputs[:3]):
        raise ValueError("v41_hc_pre_public_source_contract")
    boundary = group.get("resource_boundary", {})
    if boundary.get("kind") != "selected_native_fusion" or boundary.get("traffic_profile") != PRE_PROFILE:
        raise ValueError("v41_hc_pre_arch35_resource_not_selected")
    targets = [n for n in local if n["node_id"] in boundary["operator_ids"]]
    if len(targets) != 1:
        raise ValueError("v41_hc_pre_source_resource_missing")
    return targets, {"boundary_relation": "arch35_HCPre_public_three_output_source_partial_reference",
        "observed_native_tensor_contract": native, "declared_resource_boundary": boundary,
        "unmodeled_native_tensor_slots": {"inputs": [4], "outputs": [3]},
        "observed_extra_branch_values": None, "native_extra_branch_equivalence_established": False,
        "limitations": ["The native five-input/four-output ABI has an additional [B,4] input/output absent from the public three-output source.",
            "The source program is a partial conditional service reference, not a complete native equivalence or additional Body budget.",
            "Private source dispatch, scalar flags and tensor values remain unobserved."]}


def prepare_references(actual, manifest):
    replica = min(manifest["execution"]["replicas"])
    by_layer, subgraphs = defaultdict(list), defaultdict(list)
    for node in (*manifest["nodes"], *manifest.get("resource_operators", ())):
        if node["replica"] == replica:
            by_layer[node.get("layer")].append(node)
    for group in manifest["subgraphs"]:
        if group["replica"] == replica:
            subgraphs[group.get("layer")].append(group)
    refs, unresolved, selected = [], [], {}
    for old in actual.get("source_role_references", ()):
        kind = old["native_operator_type"]
        if kind not in {"MoeDistributeDispatchV3", "MoeDistributeCombineV3", "HcPre"}:
            continue
        native = freeze(old["source_correspondence"]["observed_native_tensor_contract"])
        first, signature = None, None
        try:
            if native[:2] != ("native_tensor_abi", kind):
                raise ValueError("v41_retained_native_type_differs")
            for layer in old["layer_ids"]:
                targets, relation = (_pre(native, old["declared_role"], subgraphs[layer], by_layer[layer], manifest["execution"])
                    if kind == "HcPre" else _mc2(native, by_layer[layer], manifest["execution"]))
                current = canonical([(program_signature(n), n["physical_work"]) for n in targets])
                if signature is not None and signature != current:
                    raise ValueError("v41_fresh_source_work_differs_across_saved_layers")
                if first is None:
                    first, signature = (targets, relation), current
            if first is None:
                raise ValueError("v41_saved_native_layers_missing")
        except ValueError as error:
            unresolved.append({"retained_group_id": old["group_id"], "native_operator_type": kind,
                "declared_role": old["declared_role"], "event_count": old["observed_us"]["count"],
                "status": "unresolved", "reason": str(error)})
            continue
        targets, relation = first
        selected.update((n["node_id"], n) for n in targets)
        refs.append({**{k: old[k] for k in ("native_operator_type", "declared_role", "layer_ids", "observed_us",
                "duration_ns_counter", "observed_activity_sum_ns")},
            "group_id": "sha256:" + sha256(canonical((old["group_id"], signature)).encode()).hexdigest(),
            "retained_group_id": old["group_id"], "native_abi": native,
            "program_set_key": sha256(signature.encode()).hexdigest(),
            "representative_replica": replica, "representative_target_ids": [n["node_id"] for n in targets],
            "physical_program_signatures": [n["physical_signature"] for n in targets],
            "physical_work_per_program": [n["physical_work"] for n in targets],
            "source_correspondence": relation, "strict_accuracy_implied": False,
            "additional_budget_allowed": False, "occurrence_binding_implied": False,
            "original_partition_histogram_unchanged": True})
    return refs, unresolved, {"execution": manifest["execution"], "graph_id": manifest["graph_id"],
                              "nodes": list(selected.values())}


def prepare_affected_references(actual, partitions, manifest):
    """Include complete expert and output-matrix populations in the new arm.

    Prepared MX32 selects q_b/wo_a/wo_b, not routed expert GEMMs. The expert
    programs are revalidated independently so their active-row uncertainty and
    original population cannot be replaced by the prepared-matrix declaration.
    q_b/wo_b and HCPost retain their existing normalized strict cohort path.
    """
    from rebind_grouped_source_roles import rebind_frozen_grouped_groups
    from v41_native_references import prepare_references as prepare_output_matrix

    refs, unresolved, compact = prepare_references(actual, manifest)
    selected = {n["node_id"]: n for n in compact["nodes"]}
    targets = {n["node_id"]: n for n in manifest["nodes"]}
    original = {g["group_id"]: g for g in actual["source_role_references"]
                if g["native_operator_type"] == "GroupedMatmul"}
    rebound, records = rebind_frozen_grouped_groups(
        {**actual, "source_role_references": list(original.values())}, manifest)
    by_id = {g["group_id"]: g for g in rebound["source_role_references"]}
    for record in records:
        if record["status"] != "rebound":
            unresolved.append({**record, "retained_group_id": record["old_group_id"],
                               "status": "unresolved"})
            continue
        group = by_id[record["group_id"]]
        nodes = [targets[key] for key in group["representative_target_ids"]]
        signature = canonical([(program_signature(n), n["physical_work"]) for n in nodes])
        selected.update((n["node_id"], n) for n in nodes)
        refs.append({**group, "retained_group_id": record["old_group_id"],
            "native_abi": group["source_correspondence"]["observed_native_tensor_contract"],
            "program_set_key": sha256(signature.encode()).hexdigest(),
            "strict_accuracy_implied": False, "original_partition_histogram_unchanged": True})

    output_groups = [(index, group) for index, group in enumerate(partitions["partitions"])
                     if group["native_operator_type"] == "TransposeQuantBatchMatMul"]
    output, failures, output_manifest = prepare_output_matrix(
        {**partitions, "partitions": [group for _, group in output_groups]}, manifest)
    unresolved.extend(failures)
    for group in output:
        nodes = [targets[key] for key in group["representative_target_ids"]]
        if (len(nodes) != 1 or nodes[0]["operator"]["metadata"].get("implementation_binding", {}).get("implementation")
                != "ascend_prepared_mx32_matrix"):
            unresolved.append({"native_operator_type": group["native_operator_type"],
                "declared_role": group["declared_role"], "event_count": group["observed_us"]["count"],
                "status": "unresolved", "reason": "prepared_mx32_output_matrix_not_selected"})
            continue
        group["partition_indices"] = [output_groups[i][0] for i in group["partition_indices"]]
        group["source_correspondence"].update(
            prepared_mx32_source_selected=True,
            selected_source_implementation=nodes[0]["operator"]["metadata"]["source"],
            selected_output_boundary=nodes[0]["operator"]["metadata"]["matrix_output_contract"],
            prepared_runtime_representation_is_capture_binary_proof=False)
        selected.update((n["node_id"], n) for n in nodes)
        refs.append(group)
    attention, failures, attention_manifest = prepare_attention_symbols(actual, manifest)
    refs.extend(attention)
    unresolved.extend(failures)
    selected.update((n["node_id"], n) for n in attention_manifest["nodes"])
    return refs, unresolved, {**compact, "nodes": list(selected.values())}


def prepare_attention_symbols(actual, manifest):
    """Keep source-symbol correspondence distinct from retained complete ABI.

    These original custom DSL calls have complete populations and independently
    aligned layer groups, but no retained tensor ABI. The same source file and
    fresh homogeneous layer programs support a conditional service reference.
    """
    replica = min(manifest["execution"]["replicas"])
    layers = defaultdict(list)
    for node in manifest["nodes"]:
        if node["replica"] == replica:
            layers[node.get("layer")].append(node)
    refs, failures, selected = [], [], {}
    for old in actual["source_role_references"]:
        if old["native_operator_type"] != "MqsmlaKernel___call__":
            continue
        source = old["source_anchor_declaration"]
        original_sha = source.get("evidence", {}).get("sha256")
        first, signature = None, None
        try:
            if not original_sha or source.get("name") != "mixed_quant_sparse_flash_mla" or source.get("attention") != "mla":
                raise ValueError("retained_mqsmla_source_anchor_incomplete")
            for layer in old["layer_ids"]:
                targets = [n for n in layers[layer] if n["family"] == "attention"]
                if len(targets) != 1:
                    raise ValueError("fresh_mqsmla_complete_batch_program_not_unique")
                target = targets[0]
                meta = target["operator"]["metadata"]
                binding = meta.get("implementation_binding", {})
                if (binding.get("implementation") != "cannbot_mixed_quant_sparse_flash_mla"
                        or binding.get("source", {}).get("kernel", {}).get("sha256") != original_sha
                        or meta.get("native_kind") != old["native_operator_type"]):
                    raise ValueError("fresh_mqsmla_source_identity_differs")
                current = canonical((program_signature(target), target["physical_work"]))
                if signature is not None and current != signature:
                    raise ValueError("mqsmla_ratio_programs_cannot_split_retained_histogram")
                if first is None:
                    first, signature = target, current
            if first is None:
                raise ValueError("retained_mqsmla_layer_population_empty")
        except ValueError as error:
            failures.append({"retained_group_id": old["group_id"], "native_operator_type": old["native_operator_type"],
                "declared_role": old["declared_role"], "event_count": old["observed_us"]["count"],
                "status": "unresolved", "reason": str(error)})
            continue
        selected[first["node_id"]] = first
        refs.append({**old, "retained_group_id": old["group_id"],
            "group_id": "sha256:" + sha256(canonical((old["group_id"], signature)).encode()).hexdigest(),
            "program_set_key": sha256(signature.encode()).hexdigest(), "representative_replica": replica,
            "representative_target_ids": [first["node_id"]],
            "physical_program_signatures": [first["physical_signature"]],
            "physical_work_per_program": [first["physical_work"]],
            "source_correspondence": {"boundary_relation": "retained_source_symbol_to_explicit_full_batch_mqsmla",
                "observed_native_tensor_contract": None, "complete_native_abi_available": False,
                "declared_mqsmla_geometry": first["operator"]["metadata"]["mqsmla_geometry"],
                "declared_source_binding": first["operator"]["metadata"]["implementation_binding"],
                "observed_sparse_index_values": None,
                "limitations": ["The complete saved ratio/layer population uses an independently established source-symbol anchor, not a full native tensor contract.",
                    "Source binary equivalence, scalar metadata and sparse index values remain unknown.",
                    "Each saved histogram is retained whole; different fresh layer work would reject the entire group."]},
            "strict_accuracy_implied": False, "original_partition_histogram_unchanged": True})
    return refs, failures, {"execution": manifest["execution"], "graph_id": manifest["graph_id"],
                            "nodes": list(selected.values())}
