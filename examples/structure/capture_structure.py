"""Summarize retained native caller structure for replay binding and reconciliation.

[Role] Project a caller-selected kernel_details.csv into bounded native ABI
  evidence and compare it with the corrected Sim graph.
[Invariants] Native descriptors do not prove group lists, peer windows, binary
  identity or fused timing. Source paths/hashes and event counts stay outside
  raw predictive inputs. Missing/mixed/unsupported evidence never binds MC2.
[Timeouts & Locks] One bounded streaming scan; no locks, subprocesses or devices.
[Side-Effect Policy] Read-only CSV access; returns provenance and mutates only
  the explicitly requested copied runtime caller/rules.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from mindie_profiler.body_matrix_contracts import (
    matrix_contract_diagnostic, matrix_contract_scope, observed_matrix_contract)
from mindie_profiler.body_moe_contracts import moe_fusion_contract, moe_fusion_scope
from mindie_profiler.native_tensor_abi import native_tensor_contract, native_tensor_diagnostic
from mindie_profiler.normalized import kernel_rows

from capture_ffn_guard import ROUTED_RECIPES, guard_legacy_ffn_rules


SCHEMA = "mindie-profiler-native-structure/1"
MAX_SCAN_ROWS = 1_000_000
SCAN_TIMEOUT_S = 30.0
MAX_SIGNATURE_VARIANTS = 4
MC2_KIND = "vllm_ascend_mc2_tp_slice"
MC2_PADDING = "right_to_tp"
DISPATCH_KIND = "MoeDistributeDispatchV2"
COMBINE_KIND = "MoeDistributeCombineV2"
GATE_KINDS = frozenset({"GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"})
DOWN_KIND = "GroupedMatmul"
PAD_KIND = "PadV3"
ALLGATHER_PREFIX = "hcom_allGather"
UNOBSERVED = (
    "group_list_type",
    "group_list_values",
    "routed_token_counts",
    "peer_window",
    "native_binary_equivalence",
    "fused_implementation_timing",
    "first_allreduce_wait_cause",
)


def capture_csv_path(capture_path):
    """Resolve only the conventional kernel_details.csv(.gz) source."""
    source = Path(capture_path)
    if source.name in {"kernel_details.csv", "kernel_details.csv.gz"}:
        return source
    parent = source if source.is_dir() else source.parent
    plain = parent / "kernel_details.csv"
    if plain.is_file() or not parent.is_dir():
        return plain
    compressed = parent / "kernel_details.csv.gz"
    return compressed if compressed.is_file() else plain


def _file_sha256(path):
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _signature(row):
    return (row.kind, row.core, row.state, row.blocks, row.input_shapes,
            row.output_shapes, row.input_dtypes, row.output_dtypes,
            row.input_formats, row.output_formats)


def _classify(kind):
    if kind == DISPATCH_KIND:
        return "dispatch"
    if kind == COMBINE_KIND:
        return "combine"
    if kind in GATE_KINDS:
        return "gate"
    if kind == DOWN_KIND:
        return "down"
    if kind == PAD_KIND:
        return "pad"
    if kind.startswith(ALLGATHER_PREFIX):
        return "allgather"
    if (kind.startswith("MoeDistributeDispatch")
            or kind.startswith("MoeDistributeCombine")
            or kind.startswith(("MoeInitRouting", "MoeFinalizeRouting",
                                "MoeTokenPermute", "MoeTokenUnpermute"))
            or kind in {"MoeDistributeAllToAll", "MoeAllToAll",
                        "DispatchFFNCombine"}):
        return "other_caller"
    return None


def _summary(row, classification):
    native = native_tensor_contract(row)
    summary = {
        "kind": row.kind,
        "line": row.line,
        "count": 1,
        "input_shapes": row.input_shapes,
        "output_shapes": row.output_shapes,
        "input_dtypes": row.input_dtypes,
        "output_dtypes": row.output_dtypes,
        "input_formats": row.input_formats,
        "output_formats": row.output_formats,
        "native_contract_sha256": None,
        "native_slots": None,
        "contract_issue": None,
    }
    if native is None:
        summary["contract_issue"] = native_tensor_diagnostic(row)
        return summary
    summary["native_contract_sha256"] = sha256(repr(native).encode("utf-8")).hexdigest()[:16]
    summary["native_slots"] = (len(native[2]), len(native[3]))
    if classification == "gate":
        projection, issue = moe_fusion_contract(native)
        summary["projection"] = projection
        summary["contract_issue"] = issue
        summary["scope"] = moe_fusion_scope(row.kind) if projection else None
    elif classification == "down":
        projection = observed_matrix_contract(row)
        summary["projection"] = projection
        summary["contract_issue"] = None if projection else matrix_contract_diagnostic(row)
        summary["scope"] = matrix_contract_scope(row) if projection else None
    return summary


DISPATCH_INPUT_DTYPES = ("DT_BF16", "INT32", "DT_UNDEFINED", "BOOL",
                          "DT_UNDEFINED", "DT_UNDEFINED", "DT_UNDEFINED")
DISPATCH_OUTPUT_DTYPES = ("INT8", "FLOAT", "INT32", "INT64", "INT32", "INT32", "FLOAT")
DISPATCH_INPUT_FORMATS = ("ND", "ND", "NULL", "ND", "NULL", "NULL", "NULL")
COMBINE_INPUT_DTYPES = ("DT_BF16", "INT32", "INT32", "INT32", "FLOAT", "INT32",
                        "BOOL", "DT_UNDEFINED", "DT_UNDEFINED", "DT_UNDEFINED",
                        "FLOAT", "DT_UNDEFINED", "DT_UNDEFINED", "DT_UNDEFINED",
                        "DT_UNDEFINED", "DT_UNDEFINED", "DT_UNDEFINED",
                        "DT_UNDEFINED")
COMBINE_OUTPUT_DTYPES = ("DT_BF16",)
COMBINE_INPUT_FORMATS = ("ND", "ND", "ND", "ND", "ND", "ND", "ND", "NULL",
                         "NULL", "NULL", "ND", "NULL", "NULL", "NULL", "NULL",
                         "NULL", "NULL", "NULL")


CSV_DTYPES = {"bf16": "DT_BF16", "fp16": "DT_FLOAT16", "fp32": "FLOAT",
              "int8": "INT8", "int32": "INT32", "int64": "INT64"}


def _csv_dtype(dtype):
    return CSV_DTYPES.get(str(dtype), str(dtype))


def _shape2(shape):
    return (isinstance(shape, tuple) and len(shape) == 2
            and all(type(value) is int and value > 0 for value in shape))


def _pad_contract(pad, tp, *, hidden_size, num_experts, activation_dtype,
                  router_dtype):
    shapes_in = pad["input_shapes"]
    shapes_out = pad["output_shapes"]
    if (not shapes_in or not shapes_out or len(shapes_in) != 3
            or len(shapes_out) != 1 or not _shape2(shapes_in[0])
            or not _shape2(shapes_out[0])):
        return None, "prepare_pad_descriptor_incomplete"
    control = shapes_in[1]
    if (not isinstance(control, tuple) or len(control) != 1
            or type(control[0]) is not int or control[0] < 1
            or shapes_in[2] != ()):
        return None, "prepare_pad_control_shape_unsupported"
    if (pad["input_dtypes"][1] != "INT32"
            or pad["input_dtypes"][2] != pad["input_dtypes"][0]
            or pad["output_dtypes"] != (pad["input_dtypes"][0],)
            or tuple(pad["input_formats"]) != ("ND", "ND", "ND")
            or tuple(pad["output_formats"]) != ("ND",)):
        return None, "prepare_pad_dtype_or_layout_unsupported"
    rows, width = shapes_in[0]
    output_rows, output_width = shapes_out[0]
    if output_width != width:
        return None, "prepare_pad_output_width_disagrees"
    expected = ((rows + tp - 1) // tp) * tp
    if output_rows != expected:
        return None, "prepare_pad_rows_disagree_with_ceil_tp"
    if width == hidden_size:
        expected_dtype = _csv_dtype(activation_dtype)
    elif width == num_experts:
        expected_dtype = _csv_dtype(router_dtype)
    else:
        return None, "prepare_pad_width_disagrees_with_model"
    if pad["input_dtypes"][0] != expected_dtype:
        return None, "prepare_pad_dtype_role_disagrees"
    return {"input_rows": rows, "source_local_rows": (rows + tp - 1) // tp,
            "output_rows": output_rows, "width": width,
            "line": pad["line"]}, None


def _dispatch_contract(dispatch, combine, *, hidden_size, num_experts, top_k,
                       source_local_rows, banks):
    din, dout = dispatch["input_shapes"], dispatch["output_shapes"]
    cin, cout = combine["input_shapes"], combine["output_shapes"]
    if (dispatch["input_dtypes"] != DISPATCH_INPUT_DTYPES
            or dispatch["output_dtypes"] != DISPATCH_OUTPUT_DTYPES
            or tuple(dispatch["input_formats"]) != DISPATCH_INPUT_FORMATS
            or tuple(dispatch["output_formats"]) != ("ND",) * 7):
        return None, "dispatch_native_dtype_or_layout_unsupported"
    if (combine["input_dtypes"] != COMBINE_INPUT_DTYPES
            or combine["output_dtypes"] != COMBINE_OUTPUT_DTYPES
            or tuple(combine["input_formats"]) != COMBINE_INPUT_FORMATS
            or tuple(combine["output_formats"]) != ("ND",)):
        return None, "combine_native_dtype_or_layout_unsupported"
    if (len(din) != 7 or len(dout) != 7 or len(cin) != 18 or len(cout) != 1):
        return None, "dispatch_combine_slot_count_unsupported"
    if not (_shape2(din[0]) and _shape2(dout[0]) and _shape2(cin[0])
            and _shape2(cout[0])):
        return None, "dispatch_combine_boundary_shape_unsupported"
    if (din[0] != (source_local_rows, hidden_size)
            or din[1] != (source_local_rows, top_k)
            or dout[0] != (dout[0][0], hidden_size)
            or dout[1] != (dout[0][0],)
            or dout[3] != (banks,)
            or dout[4] != (num_experts,)
            or dout[5] != (1,)
            or dout[6] != (dout[0][0],)):
        return None, "dispatch_boundary_geometry_unsupported"
    if (cout[0] != (source_local_rows, hidden_size)
            or cin[0] != (dout[0][0], hidden_size)
            or cin[1] != (source_local_rows, top_k)
            or cin[3] != (num_experts,)
            or cin[4] != (source_local_rows, top_k)
            or cin[10] != (dout[0][0],)):
        return None, "combine_boundary_geometry_unsupported"
    if dout[0][0] < source_local_rows:
        return None, "dispatch_capacity_smaller_than_source_rows"
    return {
        "source_local_rows": source_local_rows,
        "hidden_size": hidden_size,
        "capacity_rows": dout[0][0],
        "bank_axis": dout[3][0],
        "expert_axis": dout[4][0],
        "combine_output_rows": cout[0][0],
    }, None


def _assess(evidence, *, tp, hidden_size, num_experts, top_k,
            activation_dtype=None, router_dtype=None):
    counts = evidence["counts"]
    signatures = evidence["signatures"]
    if evidence.get("other_caller_kinds"):
        return "mixed_unsupported", "unrecognized_moe_or_eager_caller_observed"
    if type(tp) is not int or tp < 1:
        return "unsupported", "tensor_parallel_axis_unavailable"
    if hidden_size is None or num_experts is None or top_k is None:
        return "unsupported", "model_topology_geometry_unavailable"
    for classification in ("dispatch", "combine", "gate", "down"):
        found = signatures.get(classification, [])
        if not found:
            return "unresolved", classification + "_not_observed"
        if len(found) > 1 or evidence["signature_truncated"]:
            return "mixed_unsupported", "mixed_" + classification + "_signatures"
        if found[0].get("contract_issue"):
            return "unsupported", classification + "_native_contract_unsupported"
    if len({counts.get(name) for name in ("dispatch", "combine", "gate", "down")}) != 1:
        return "unresolved", "dispatch_combine_grouped_multiplicity_mismatch"
    gate = signatures["gate"][0]
    down = signatures["down"][0]
    if not gate.get("projection") or not down.get("projection"):
        return "unsupported", "grouped_projection_unavailable"
    gate_tag, gate_kind, (gate_banks, gate_k, gate_n), gate_dtypes = gate["projection"]
    down_tag, (down_banks, down_m, down_n, down_k), *down_dtypes = down["projection"]
    if gate_tag != "grouped_mlp_parameters_active" or down_tag != "grouped_matrix":
        return "unsupported", "grouped_projection_kind_unsupported"
    if gate_banks != down_banks:
        return "unsupported", "grouped_expert_bank_count_disagrees"
    if gate_k != down_n or gate_n != down_k:
        return "unsupported", "grouped_channel_geometry_disagrees"
    if not activation_dtype or not router_dtype:
        return "unsupported", "prepare_pad_dtype_roles_unavailable"
    pads = signatures.get("pad", [])
    if not pads:
        return "unresolved", "prepare_pad_not_observed"
    if len(pads) != 2:
        return "unsupported", "prepare_pad_signature_count_unsupported"
    if any(pad.get("contract_issue") for pad in pads):
        return "unsupported", "prepare_pad_native_contract_unsupported"
    pad_contracts = [
        _pad_contract(pad, tp, hidden_size=hidden_size, num_experts=num_experts,
                      activation_dtype=activation_dtype, router_dtype=router_dtype)
        for pad in pads]
    if any(contract is None for contract, _ in pad_contracts):
        issue = next(issue for contract, issue in pad_contracts if contract is None)
        return "unsupported", issue
    prepared = [contract for contract, _ in pad_contracts]
    widths = {item["width"] for item in prepared}
    if widths != {hidden_size, num_experts}:
        return "unsupported", "prepare_pad_widths_disagree_with_model"
    if len({(item["input_rows"], item["output_rows"],
             item["source_local_rows"]) for item in prepared}) != 1:
        return "mixed_unsupported", "mixed_prepare_pad_rows"
    source_local_rows = prepared[0]["source_local_rows"]
    if down_m != 0 and gate["input_shapes"][0][0] < source_local_rows:
        return "unsupported", "grouped_allocation_smaller_than_source_rows"
    boundary, issue = _dispatch_contract(
        signatures["dispatch"][0], signatures["combine"][0],
        hidden_size=hidden_size, num_experts=num_experts, top_k=top_k,
        source_local_rows=source_local_rows, banks=gate_banks)
    if boundary is None:
        return "unsupported", issue
    if boundary["bank_axis"] != gate_banks:
        return "unsupported", "dispatch_bank_axis_disagrees_with_grouped_banks"
    if boundary["expert_axis"] != num_experts:
        return "unsupported", "dispatch_expert_axis_disagrees_with_model"
    if boundary["combine_output_rows"] != source_local_rows:
        return "unsupported", "combine_output_rows_disagree_with_source_local_rows"
    capacity = boundary["capacity_rows"]
    if (gate["input_shapes"][0] != (capacity, hidden_size)
            or gate["output_shapes"][0] != (capacity, gate_n)
            or down["input_shapes"][0] != (capacity, down_k)
            or down["output_shapes"][0] != (capacity, hidden_size)):
        return "unsupported", "capacity_buffer_rows_or_channels_disagree"
    combine = signatures["combine"][0]
    if (gate["input_dtypes"][0] != "INT8" or gate["input_formats"][0] != "ND"
            or gate["output_dtypes"][0] != "INT8" or gate["output_formats"][0] != "ND"
            or down["input_dtypes"][0] != "INT8" or down["input_formats"][0] != "ND"
            or down["output_dtypes"][0] != combine["input_dtypes"][0]
            or down["output_formats"][0] != combine["input_formats"][0]):
        return "unsupported", "capacity_buffer_dtype_or_layout_disagree"
    evidence["capacity_buffer"] = {
        "rows": capacity, "hidden": hidden_size, "width": gate_n,
        "role": "allocation_not_valid_work",
    }
    evidence["prepare"] = {
        "input_rows": prepared[0]["input_rows"],
        "source_local_rows": source_local_rows,
        "output_rows": prepared[0]["output_rows"],
        "x_width": hidden_size,
        "logits_width": num_experts,
        "signatures": 2,
        "line": prepared[0]["line"],
    }
    evidence["grouped"] = {
        "gate": {
            "kind": gate["kind"], "line": gate["line"], "banks": gate_banks,
            "hidden": gate_k, "width": gate_n, "dtypes": gate_dtypes,
            "count": gate["count"],
        },
        "down": {
            "kind": down["kind"], "line": down["line"], "banks": down_banks,
            "hidden": down_n, "width": down_k, "dtypes": down_dtypes,
            "count": down["count"],
        },
        "allocation_rows": gate["input_shapes"][0][0],
        "row_axis_role": "allocation_not_valid_work",
        "valid_routed_rows": "unobserved",
    }
    evidence["dispatch"] = {
        "kind": signatures["dispatch"][0]["kind"],
        "line": signatures["dispatch"][0]["line"],
        "count": counts["dispatch"],
        "input_shapes": signatures["dispatch"][0]["input_shapes"],
        "output_shapes": signatures["dispatch"][0]["output_shapes"],
        "contract": boundary,
    }
    evidence["combine"] = {
        "kind": signatures["combine"][0]["kind"],
        "line": signatures["combine"][0]["line"],
        "count": counts["combine"],
        "input_shapes": signatures["combine"][0]["input_shapes"],
        "output_shapes": signatures["combine"][0]["output_shapes"],
    }
    return "consistent", "mc2_dispatch_combine_and_grouped_geometry_observed"


def collect_structural_evidence(csv_path, *, tp, hidden_size=None, num_experts=None,
                                top_k=None, activation_dtype=None, router_dtype=None):
    """Stream one CSV into bounded native-caller evidence; never all events."""
    path = Path(csv_path)
    evidence = {
        "schema_version": SCHEMA,
        "status": "not_provided",
        "reason": "capture_csv_not_present",
        "source": {"path": str(path), "sha256": None,
                   "size_bytes": path.stat().st_size if path.is_file() else None},
        "scanned_rows": 0,
        "counts": {},
        "signatures": {},
        "signature_truncated": False,
        "other_caller_kinds": [],
        "allgather": {"count": 0, "first_line": None,
                      "moe_attributed_count": None, "attribution": "unresolved"},
    }
    if not path.is_file():
        return evidence
    evidence["source"]["sha256"] = _file_sha256(path)
    buckets = {}
    counts = {}
    other_caller_kinds = set()
    scanned = 0
    for row in kernel_rows(path, max_rows=MAX_SCAN_ROWS,
                           timeout_s=SCAN_TIMEOUT_S,
                           include_zero_duration=True):
        scanned += 1
        classification = _classify(row.kind)
        if classification is None:
            continue
        counts[classification] = counts.get(classification, 0) + 1
        if classification == "allgather":
            if evidence["allgather"]["first_line"] is None:
                evidence["allgather"]["first_line"] = row.line
            continue
        if classification == "other_caller":
            if len(other_caller_kinds) < MAX_SIGNATURE_VARIANTS:
                other_caller_kinds.add(row.kind)
            continue
        bucket = buckets.setdefault(classification, {})
        signature = _signature(row)
        if signature in bucket:
            bucket[signature]["count"] += 1
        elif len(bucket) < MAX_SIGNATURE_VARIANTS:
            bucket[signature] = _summary(row, classification)
        else:
            evidence["signature_truncated"] = True
    evidence["scanned_rows"] = scanned
    evidence["counts"] = counts
    evidence["signatures"] = {name: list(bucket.values())
                              for name, bucket in buckets.items()}
    evidence["other_caller_kinds"] = sorted(other_caller_kinds)
    evidence["allgather"] = {
        "count": counts.get("allgather", 0),
        "first_line": evidence["allgather"]["first_line"],
        "moe_attributed_count": None,
        "attribution": "unresolved",
    }
    status, reason = _assess(
        evidence, tp=tp, hidden_size=hidden_size, num_experts=num_experts,
        top_k=top_k, activation_dtype=activation_dtype, router_dtype=router_dtype)
    evidence.update(status=status, reason=reason)
    return evidence


def _generated_descriptors(case, *, tokens):
    from mindie_sim import target_operators
    from mindie_sim.schema.common import ModelingError

    try:
        ops = target_operators(case, phase="decode", tokens=max(1, int(tokens)),
                               context=0, sequences=1)
    except ModelingError as error:
        return None, {"reason": "generated_descriptor_unavailable",
                      "detail": str(error)}
    roles, pads, graph_rows, finalize_rows, partition = {}, set(), set(), set(), None
    for op in ops:
        if op.layer != 0:
            continue
        metadata = dict(op.metadata)
        if op.recipe in ROUTED_RECIPES:
            role = "gate_up" if op.recipe.endswith("grouped_gate_up") else "down"
            local = tuple(op.local_shape)
            padded = tuple(op.padded_shape)
            if role == "gate_up":
                shape = {"banks": metadata.get("matrix_weight_bank_groups"),
                         "hidden": local[2], "width": local[1] // 2,
                         "local_shape": local, "padded_shape": padded}
            else:
                shape = {"banks": metadata.get("matrix_weight_bank_groups"),
                         "hidden": local[1], "width": local[2],
                         "local_shape": local, "padded_shape": padded}
            roles.setdefault(role, shape)
        if op.recipe in {"tensor_concat", "tensor_pad"}:
            pads.add(int(op.local_shape[0]))
            if metadata.get("moe_token_partition"):
                partition = metadata["moe_token_partition"]
        if op.recipe == "route_pack" and metadata.get("moe_token_partition"):
            partition = metadata["moe_token_partition"]
        if op.recipe == "route_unpack":
            finalize_rows.add(int(op.local_shape[0]))
        if "graph_physical_query_rows" in metadata:
            graph_rows.add(metadata["graph_physical_query_rows"])
    if "gate_up" not in roles or "down" not in roles:
        return None, {"reason": "generated_grouped_recipe_missing"}
    if roles["gate_up"]["banks"] is None or roles["down"]["banks"] is None:
        return None, {"reason": "generated_expert_bank_missing"}
    return {
        "roles": roles,
        "prepare_allocation_rows": sorted(pads),
        "graph_physical_rows": sorted(graph_rows),
        "finalize_rows": sorted(finalize_rows),
        "partition": deepcopy(partition),
    }, None


def _compare(evidence, generated):
    if generated is None:
        return {"matched_descriptor_fields": [],
                "mismatches": [{"field": "generated_descriptors", "reason": "unavailable"}]}
    observed_gate = evidence["grouped"]["gate"]
    observed_down = evidence["grouped"]["down"]
    generated_gate = generated["roles"]["gate_up"]
    generated_down = generated["roles"]["down"]
    checks = [
        ("expert_bank_count", observed_gate["banks"], generated_gate["banks"]),
        ("gate_hidden_channels", observed_gate["hidden"], generated_gate["hidden"]),
        ("gate_expert_width", observed_gate["width"], generated_gate["width"]),
        ("down_expert_bank_count", observed_down["banks"], generated_down["banks"]),
        ("down_hidden_channels", observed_down["hidden"], generated_down["hidden"]),
        ("down_expert_width", observed_down["width"], generated_down["width"]),
        ("prepare_input_rows", evidence["prepare"]["input_rows"],
         (generated["partition"] or {}).get("full_rows")),
        ("prepare_source_local_rows", evidence["prepare"]["source_local_rows"],
         (generated["partition"] or {}).get("local_rows")),
        ("prepare_allocation_rows", evidence["prepare"]["output_rows"],
         (generated["partition"] or {}).get("allocated_rows")),
        ("generated_padding", "right_to_tp", (generated["partition"] or {}).get("padding")),
        ("padding_implementation", "pad_v3",
         (generated["partition"] or {}).get("padding_implementation", "concat")),
        ("finalize_rows", evidence["combine"]["output_shapes"][0][0],
         generated["finalize_rows"][0] if generated["finalize_rows"] else None),
    ]
    matched, mismatches = [], []
    for field, observed, produced in checks:
        if observed == produced and observed is not None:
            matched.append(field)
        else:
            mismatches.append({"field": field, "observed": observed, "generated": produced})
    return {
        "matched_descriptor_fields": matched,
        "mismatches": mismatches,
        "gmm_row_axis_role": "allocation_not_valid_work",
        "valid_routed_rows": "unobserved",
    }




def _comparison(evidence, generated, basis):
    if evidence["status"] != "consistent":
        comparison = {
            "matched_descriptor_fields": [],
            "mismatches": [{"field": "evidence", "reason": evidence["reason"]}],
            "gmm_row_axis_role": "allocation_not_valid_work",
            "valid_routed_rows": "unobserved",
        }
    else:
        comparison = _compare(evidence, generated)
    comparison["basis"] = basis
    comparison["observed_allocation_rows"] = (
        evidence.get("grouped") or {}).get("allocation_rows")
    comparison["allocation_role"] = "allocation_not_valid_work"
    comparison["allocation_not_compared"] = True
    comparison["valid_routed_rows"] = "unobserved"
    return comparison


def apply_captured_structure(result, *, before_case, capture_path, command_sha256,
                             bind_caller=True):
    """Bind only evidence-supported MC2 caller structure; reconciliation only."""
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.schema.common import ModelingError

    try:
        parsed = parse_case(result)
    except ModelingError as error:
        return {
            "schema_version": SCHEMA, "status": "unsupported",
            "reason": "case_parse_error", "detail": str(error),
            "source": {"path": str(capture_csv_path(capture_path)), "sha256": None},
            "unobserved": list(UNOBSERVED), "semantic_equivalence": False,
            "exact_native_kernel_match": False, "timing_values_used": False,
        }
    runtime = result.get("runtime") if isinstance(result.get("runtime"), dict) else {}
    model = parsed.model
    router_dtype = next((plan.router_dtype for plan in model.layer_plans
                         if getattr(plan, "router_dtype", "")), "")
    evidence = collect_structural_evidence(
        capture_csv_path(capture_path), tp=parsed.runtime.parallel.tp,
        hidden_size=model.hidden_size, num_experts=model.num_experts,
        top_k=model.top_k, activation_dtype=model.activation_dtype,
        router_dtype=router_dtype)
    if evidence["status"] == "not_provided":
        return {
            "schema_version": SCHEMA, "status": "not_provided",
            "reason": "structural_evidence_not_provided",
            "source": evidence["source"], "unobserved": list(UNOBSERVED),
            "semantic_equivalence": False, "exact_native_kernel_match": False,
            "timing_values_used": False,
        }
    kernels = runtime.get("kernels") if isinstance(runtime.get("kernels"), dict) else {}
    existing = kernels.get("moe_token_partition")
    caller_conflict = None
    if existing is not None:
        if not isinstance(existing, dict):
            caller_conflict = "explicit_caller_not_mapping"
        elif existing.get("kind") != MC2_KIND:
            caller_conflict = "explicit_caller_not_mc2"
        elif existing.get("padding") not in (None, MC2_PADDING):
            caller_conflict = "explicit_mc2_padding_incompatible"
        elif existing.get("padding_implementation") not in (None, "pad_v3"):
            caller_conflict = "explicit_padding_implementation_disagrees_with_pad_v3"

    tokens = (evidence.get("prepare") or {}).get("input_rows") or 1
    if existing is None:
        completion = {"kind": MC2_KIND, "padding": MC2_PADDING,
                      "padding_implementation": "pad_v3"}
        completion_action = "bind"
    elif not isinstance(existing, dict):
        completion = None
        completion_action = "conflict"
    elif existing.get("kind") != MC2_KIND:
        completion = deepcopy(existing)
        completion_action = "conflict"
    elif existing.get("padding") not in (None, MC2_PADDING):
        completion = deepcopy(existing)
        completion_action = "conflict"
    elif existing.get("padding_implementation") not in (None, "pad_v3"):
        completion = deepcopy(existing)
        completion_action = "conflict"
    else:
        completion = deepcopy(existing)
        scopes = completion.get("layer_scopes")
        body_selected = (scopes is None
                         or (isinstance(scopes, (list, tuple)) and "body" in scopes))
        if body_selected and (completion.get("padding") is None
                              or completion.get("padding_implementation") is None):
            completion["padding"] = MC2_PADDING
            completion["padding_implementation"] = "pad_v3"
            completion_action = "complete_padding"
        else:
            completion_action = "preserve"

    completion_case = deepcopy(result)
    if completion is not None:
        completion_case.setdefault("runtime", {}).setdefault("kernels", {})[
            "moe_token_partition"] = deepcopy(completion)
    completion_generated, completion_issue = _generated_descriptors(
        completion_case, tokens=tokens)
    completion_comparison = _comparison(
        evidence, completion_generated,
        "hypothetical_mc2_completion_not_necessarily_selected")
    completion_ok = (evidence["status"] == "consistent"
                     and completion is not None
                     and completion_generated is not None
                     and not completion_comparison["mismatches"]
                     and completion_action != "conflict")

    applied_fields = []
    action = "not_bound"
    if completion_action == "conflict":
        action = "conflict"
    elif completion_ok:
        if completion_action == "bind":
            if bind_caller:
                runtime["kernels"] = kernels
                kernels["moe_token_partition"] = deepcopy(completion)
                applied_fields.append("runtime.kernels.moe_token_partition")
                action = "bound"
        elif completion_action == "complete_padding":
            if bind_caller:
                for field in ("padding", "padding_implementation"):
                    if existing.get(field) != completion[field]:
                        existing[field] = completion[field]
                        applied_fields.append("runtime.kernels.moe_token_partition." + field)
                action = "completed_padding"
        else:
            action = "preserved_existing"
    elif evidence["status"] != "consistent":
        action = "preserved_existing" if existing is not None else "not_bound"
    else:
        action = "conflict" if existing is not None else "not_bound"

    actual_generated, actual_issue = _generated_descriptors(result, tokens=tokens)
    actual_comparison = _comparison(evidence, actual_generated, "actual_returned_graph")
    actual_caller = (result.get("runtime", {}).get("kernels", {})
                     .get("moe_token_partition"))
    actual_selected = (isinstance(actual_caller, dict)
                       and actual_caller.get("kind") == MC2_KIND
                       and actual_generated is not None
                       and not actual_comparison["mismatches"])
    if evidence["status"] != "consistent":
        status, reason = evidence["status"], evidence["reason"]
    elif caller_conflict:
        status, reason = "conflict", caller_conflict
    elif actual_selected:
        status, reason = ("consistent",
                          "source_mc2_caller_and_actual_returned_geometry_agree")
    elif existing is not None:
        status, reason = "conflict", "explicit_caller_actual_graph_mismatch"
    elif not bind_caller:
        status, reason = "unresolved", "caller_binding_not_requested"
    elif actual_generated is None:
        status, reason = "unsupported", "actual_generated_descriptor_unavailable"
    else:
        status, reason = "unsupported", "actual_generated_geometry_mismatch"
    caller = {
        "action": action,
        "field": "runtime.kernels.moe_token_partition",
        "returned": deepcopy(actual_caller),
        "applied_fields": applied_fields,
    }

    prepare = evidence.get("prepare") or {}
    grouped = evidence.get("grouped") or {}
    dispatch = evidence.get("dispatch") or {}
    combine = evidence.get("combine") or {}
    actual_partition = ((actual_generated or {}).get("partition") or {})
    rows = {
        "observed_full_graph": prepare.get("input_rows"),
        "observed_source_local": prepare.get("source_local_rows"),
        "observed_prepare_allocated": prepare.get("output_rows"),
        "observed_dispatch_capacity": (dispatch.get("contract") or {}).get("capacity_rows"),
        "observed_finalize": ((combine.get("output_shapes") or [[None]])[0][0]),
        "generated_full": actual_partition.get("full_rows"),
        "generated_local": actual_partition.get("local_rows"),
        "generated_allocated": actual_partition.get("allocated_rows"),
        "generated_finalize": (actual_generated or {}).get("finalize_rows") or [],
        "gmm_allocation_rows": grouped.get("allocation_rows"),
        "gmm_row_axis_role": "allocation_not_valid_work",
        "valid_routed_rows": "unobserved",
    }
    unmatched = [
        {"kind": "hcom_allGather_", "count": evidence["allgather"]["count"],
         "boundary": "whole_window_events", "moe_attribution": "unresolved"},
        {"kind": "GroupedMatmulSwigluQuant",
         "boundary": "fused_native_boundary_not_decomposed_into_generic_grouped_gate_up_and_swiglu"},
        {"kind": "GroupedMatmul",
         "boundary": "native_grouped_down_not_equivalent_to_analytical_grouped_down"},
        {"kind": "MoeDistributeDispatchV2",
         "boundary": "native_framing_not_reconstructed_by_analytical_alltoall"},
        {"kind": "MoeDistributeCombineV2",
         "boundary": "native_framing_not_reconstructed_by_analytical_alltoall"},
        {"kind": "PadV3",
         "boundary": "prepare_allocation_rows_are_not_graph_rows"},
        {"kind": "GroupedMatmul",
         "boundary": "native_row_axis_is_allocation_not_valid_routed_work"},
    ]
    return {
        "schema_version": SCHEMA,
        "status": status,
        "reason": reason,
        "source": evidence["source"],
        "evidence": {
            "scanned_rows": evidence["scanned_rows"],
            "counts": evidence["counts"],
            "signatures": evidence["signatures"],
            "allgather": evidence["allgather"],
            "other_caller_kinds": evidence.get("other_caller_kinds", []),
            "prepare": evidence.get("prepare"),
            "grouped": evidence.get("grouped"),
            "capacity_buffer": evidence.get("capacity_buffer"),
            "dispatch": evidence.get("dispatch"),
            "combine": evidence.get("combine"),
        },
        "candidate": {
            "basis": "hypothetical_mc2_completion_not_necessarily_selected",
            "declaration": deepcopy(completion),
            "generated": completion_generated,
            "issue": completion_issue,
            "comparison": completion_comparison,
            "selected": actual_selected,
        },
        "generated": actual_generated,
        "generated_issue": actual_issue,
        "comparison": actual_comparison,
        "rows": rows,
        "caller": caller,
        "unmatched_native_boundaries": unmatched,
        "unobserved": list(UNOBSERVED),
        "routed_counts": "unobserved",
        "claim": "descriptor_agreement_only_not_native_equivalence",
        "semantic_equivalence": False,
        "exact_native_kernel_match": False,
        "timing_values_used": False,
    }


def guard_actual_ffn_rules(result, *, before_case, evidence, command_sha256,
                           tokens=None):
    """Guard legacy FFN rules using the actual returned graph, not a candidate."""
    if tokens is None:
        prepare = (evidence or {}).get("prepare") or {}
        tokens = prepare.get("input_rows") or 1
    before_generated, before_issue = _generated_descriptors(before_case, tokens=tokens)
    after_generated, after_issue = _generated_descriptors(result, tokens=tokens)
    if before_generated is None or after_generated is None:
        return {"status": "not_evaluated",
                "reason": "actual_generated_descriptor_unavailable",
                "before_issue": before_issue, "after_issue": after_issue,
                "removed_ids": [], "removed_count": 0,
                "timing_values_modified": False}
    return guard_legacy_ffn_rules(
        result, before_generated=before_generated, after_generated=after_generated,
        evidence=evidence or {}, command_sha256=command_sha256)
