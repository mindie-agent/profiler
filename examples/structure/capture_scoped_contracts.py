"""Source and tensor contracts for one explicitly selected native MoE window.

[Role] Classify retained native rows, validate the A3 AllToAll TP-slice and
  A5 eager local-expert chains, and compare the returned Sim graph.
[Invariants] A mapped allocation row is not valid work. Native observed GMM
  rows, generated expected local-valid rows and dispatch capacity remain three
  separate quantities. Group-list values, native binary identity, peer windows
  and exact routed counts stay unobserved. Missing or mixed evidence fails; it
  is never replaced by a guessed shape or a model-specific multiplier.
[Timeouts & Locks] Bounded arithmetic over one descriptor set per selected
  forward; no I/O, locks, waits or device work.
[Side-Effect Policy] Pure functions over caller-owned mappings and rows. No
  capture, prediction or global state is mutated.
"""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from math import ceil
from mindie_profiler.body_matrix_contracts import observed_matrix_contract
from mindie_profiler.body_moe_contracts import moe_fusion_contract
from mindie_profiler.native_tensor_abi import (
    native_tensor_contract, native_tensor_diagnostic)
ALLTOALL_KIND = "vllm_ascend_alltoall_tp_slice"
LOCAL_EXPERT_RECIPE = "local_expert_reduce"
GATE_KINDS = frozenset({"GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2"})
# Sim names balanced-routing grouped operators with a `balanced_` prefix. The
# semantic grouped role and every physical dimension are otherwise unchanged;
# map only those exact generated identities, never an open-ended prefix match.
GROUPED_SEMANTIC_RECIPES = {
    "grouped_gate_up": "grouped_gate_up",
    "balanced_grouped_gate_up": "grouped_gate_up",
    "grouped_down": "grouped_down",
    "balanced_grouped_down": "grouped_down",
}
MAX_VARIANTS = 6
MAX_ORDER_ROWS = 8192
UNOBSERVED = (
    "group_list_type",
    "group_list_values",
    "routed_token_counts",
    "peer_window",
    "native_binary_equivalence",
    "fused_implementation_timing",
    "exact_tensor_values",
    "dispatch_destination_ids",
    "histogram_dtype_at_native_boundary",
)
_REVISION = "175ef4d49c2072f9233619636f0309f4f88b4e2c"
_DISPATCHER = {
    "path": "vllm_ascend/ops/fused_moe/token_dispatcher.py",
    "sha256": "6126304014959e8c52d87284ccac078f7622a6d72c7a7fc8be25929dfe644cfb",
}
_SCOPE = "independent_source_semantics; not_capture_binary_identity"
ALLTOALL_SOURCE = {
    "repository": "vllm-ascend",
    "revision": _REVISION,
    "prepare_finalize": {
        "path": "vllm_ascend/ops/fused_moe/prepare_finalize.py",
        "sha256": "88560c839172f5b433753c796d17a5d41278204f33b2e9ca9d4b2af9ccbe16d8",
        "symbol": "PrepareAndFinalizeWithAll2All",
        "prepare_lines": (158, 180),
        "finalize_lines": (210, 225),
    },
    "token_dispatcher": {
        **_DISPATCHER,
        "class": "TokenDispatcherWithAll2AllV",
        "dispatch_lines": (497, 579),
        "combine_lines": (581, 600),
    },
    "semantics": (
        "prepare slices full router rows to the local TP view; dispatch permutes "
        "local rows by top-k, gathers local expert counts, exchanges FP32 row "
        "scales and INT8 payload separately, then exchanges the BF16 return; "
        "finalize all-gathers per-rank slices and trims to original rows."
    ),
    "scope": _SCOPE,
}
LOCAL_EXPERT_SOURCE = {
    "repository": "vllm-ascend",
    "revision": _REVISION,
    "token_dispatcher": {
        **_DISPATCHER,
        "class": "TokenDispatcherWithAllGather",
        "dispatch_lines": (367, 449),
        "combine_lines": (451, 462),
    },
    "semantics": (
        "dp1/no-sequence-parallel input stays replicated; init routing allocates "
        "q*top_k buffer rows and filters the local expert bank. The unfused "
        "SwiGlu scans that full allocation. Grouped up/down execute the declared "
        "or expected local-valid assignment counts, not every allocated buffer "
        "row. Unpermute restores q rows and one final TP reduction follows."
    ),
    "scope": _SCOPE,
}
ALLTOALL_TRANSPORT = {
    "kind": "separate_quantized_payload",
    "dispatch_dtype": "int8",
    "payload_dtype": "int8",
    "scale_dtype": "fp32",
    "scale_granularity": "row",
    "histogram_dtype": "int32",
}
COMM_ROLES = frozenset({
    "alltoall", "allgather", "histogram_allgather", "allreduce",
})
_SIMPLE_ROLES = {
    "MoeGatingTopK": "topk",
    "GroupedMatmul": "grouped",
    "MoeTokenPermute": "permute",
    "MoeTokenUnpermute": "unpermute",
    "SwiGlu": "swiglu",
    "TensorMove": "tensor_move",
    "DynamicQuant": "dispatch_quant",
    "allgatherAicpuKernel": "histogram_allgather",
}

def signature(row):
    return (row.kind, row.input_shapes, row.output_shapes, row.input_dtypes,
            row.output_dtypes, row.input_formats, row.output_formats)

def classify(row):
    name, kind = row.name or "", row.kind or ""
    for prefix, role in (("MoeDistributeDispatch", "dispatch"),
                         ("MoeDistributeCombine", "combine")):
        if kind.startswith(prefix):
            return role
    for prefix, role in (("hcom_alltoallv", "alltoall"),
                         ("hcom_allGather", "allgather"),
                         ("hcom_allReduce", "allreduce")):
        if name.startswith(prefix):
            return role
    if kind in GATE_KINDS:
        return "gate"
    if kind in _SIMPLE_ROLES:
        return _SIMPLE_ROLES[kind]
    if kind.startswith("MoeInitRoutingV3"):
        return "init_routing"
    if kind.startswith("MoeFinalizeRoutingV2"):
        return "finalize"
    if kind.startswith("MatMulV3"):
        return "matmul_v3"
    return "other_moe" if kind.startswith("Moe") else None

def projection(row, role):
    native = native_tensor_contract(row)
    if native is None:
        return native_tensor_diagnostic(row)
    if role == "gate":
        contract, issue = moe_fusion_contract(native)
        return contract if contract is not None else issue
    contract = observed_matrix_contract(row)
    return contract if contract is not None else native_tensor_diagnostic(row)

def shape2(value):
    return (isinstance(value, tuple) and len(value) == 2
            and all(type(item) is int and item > 0 for item in value))

def matches(sig, inputs, outputs, input_dtypes=None, output_dtypes=None,
            input_formats=None, output_formats=None):
    return (
        sig[1] == inputs
        and sig[2] == outputs
        and (input_dtypes is None or sig[3] == input_dtypes)
        and (output_dtypes is None or sig[4] == output_dtypes)
        and (input_formats is None or sig[5] == input_formats)
        and (output_formats is None or sig[6] == output_formats)
    )

@dataclass(frozen=True)

class LayerEvidence:
    roles: Counter
    variants: dict
    overflow: frozenset
    order: tuple

def new_layer_evidence():
    return {"roles": Counter(), "variants": {}, "overflow": set(), "order": []}

def add_evidence(layer, role, sig, projection_value, start_ns, line):
    layer["roles"][role] += 1
    bucket = layer["variants"].setdefault(role, {})
    if sig not in bucket:
        if len(bucket) < MAX_VARIANTS:
            bucket[sig] = projection_value
        else:
            layer["overflow"].add(role)
    if len(layer["order"]) < MAX_ORDER_ROWS:
        layer["order"].append((start_ns, line or 0, role, sig))

def frozen_layer(layer):
    return LayerEvidence(layer["roles"], layer["variants"],
                         frozenset(layer["overflow"]), tuple(layer["order"]))

def _single(layer, role):
    variants = list(layer.variants.get(role, {}))
    return variants[0] if len(variants) == 1 else None

def _contract(layer, role):
    sig = _single(layer, role)
    value = layer.variants.get(role, {}).get(sig) if sig is not None else None
    return value if isinstance(value, tuple) else None

def _fail(reason, **extra):
    return {"ok": False, "reason": reason, **extra}

def _ordered(layer):
    return sorted(layer.order, key=lambda item: (item[0], item[1]))

def _positions(layer, roles):
    ordered = _ordered(layer)
    return ordered, {role: [i for i, item in enumerate(ordered)
                            if item[2] == role] for role in roles}

def _router(layer, query_rows, hidden, experts):
    """Return the unique router-shaped signature and its ABI issue, if any."""
    candidates = [
        sig for sig in layer.variants.get("matmul_v3", {})
        if sig[1] and len(sig[1]) == 2
        and sig[1][0] == (query_rows, hidden)
        and sig[1][1] == (experts, hidden)
        and sig[2] and sig[2][0] == (query_rows, experts)
    ]
    if len(candidates) != 1:
        return None, "router_variant_ambiguous"
    signature = candidates[0]
    occurrences = sum(1 for item in layer.order
                      if item[2] == "matmul_v3" and item[3] == signature)
    if occurrences != 1:
        return None, "router_variant_duplicate"
    if not (
            len(signature[3]) == 2
            and signature[3][0] == signature[3][1]
            and signature[3][0] in {"DT_BF16", "bf16", "FLOAT", "fp32"}
            and signature[4] == ("FLOAT",)
            and signature[5] == ("ND", "ND")
            and signature[6] == ("ND",)):
        return None, "router_abi_incompatible"
    return signature, None


def _unpermutes(layer, valid_rows, local_rows, dispatch_rows, hidden, top_k):
    values = list(layer.variants.get("unpermute", {}))
    combine = next((item for item in values
                    if matches(item,
                               ((valid_rows, hidden), (valid_rows,), ()),
                               ((valid_rows, hidden),),
                               ("DT_BF16", "INT32", "DT_UNDEFINED"),
                               ("DT_BF16",),
                               ("ND", "ND", "NULL"),
                               ("ND",))), None)
    reconstruct = next((item for item in values
                        if matches(item,
                                   ((dispatch_rows, hidden), (dispatch_rows,),
                                    (local_rows, top_k)),
                                   ((local_rows, hidden),),
                                   ("DT_BF16", "INT32", "DT_BF16"),
                                   ("DT_BF16",),
                                   ("ND", "ND", "ND"),
                                   ("ND",))), None)
    return values, combine, reconstruct

def _expected_local_valid(query_rows, top_k, ep):
    return int(ceil(query_rows * top_k / ep))

def validate_a3(window, evidence_layers, *, tp, ep, hidden, experts, top_k,
                intermediate):
    """Validate every repeated A3 layer and return a compact caller contract."""
    layers = []
    materials = set()
    for index, layer in enumerate(evidence_layers):
        lid = window.layers[index].layer_id
        if layer.overflow:
            return _fail("descriptor_variant_limit_exceeded", layer=lid)
        counts = layer.roles
        for role, count in (("topk", 1), ("permute", 1), ("alltoall", 3),
                            ("allgather", 2), ("init_routing", 1),
                            ("gate", 1), ("grouped", 1), ("unpermute", 2)):
            if counts.get(role, 0) != count:
                return _fail("layer_role_count_mismatch", layer=lid, role=role,
                             expected=count, observed=counts.get(role, 0))
        for forbidden in ("dispatch", "combine", "finalize", "other_moe"):
            if counts.get(forbidden):
                return _fail("mixed_scoped_native_callers", layer=lid,
                             role=forbidden)
        query_rows = window.query_rows
        if query_rows % tp:
            return _fail("alltoall_requires_divisible_full_rows",
                         query_rows=query_rows, tp=tp)
        local_rows = query_rows // tp
        dispatch_rows = local_rows * top_k
        expected_valid = _expected_local_valid(query_rows, top_k, ep)
        router, router_issue = _router(layer, query_rows, hidden, experts)
        if router is None:
            return _fail(router_issue, layer=lid)
        topk = _single(layer, "topk")
        permute = _single(layer, "permute")
        quants = [
            sig for sig in layer.variants.get("dispatch_quant", {})
            if matches(sig, ((dispatch_rows, hidden),),
                       ((dispatch_rows, hidden), (dispatch_rows,)),
                       input_dtypes=("DT_BF16",),
                       output_dtypes=("INT8", "FLOAT"),
                       input_formats=("ND",),
                       output_formats=("ND", "ND"))
        ]
        if len(quants) != 1:
            return _fail("dispatch_quant_not_unique", layer=lid,
                         observed=len(quants))
        quant = quants[0]
        routing = _single(layer, "init_routing")
        gate = _contract(layer, "gate")
        grouped = _contract(layer, "grouped")
        if None in (topk, permute, quant, routing) or gate is None or grouped is None:
            return _fail("layer_descriptor_variant_not_unique", layer=lid)
        if not matches(topk, ((local_rows, experts), ()),
                       ((local_rows, top_k), (local_rows, top_k),
                        (local_rows, experts)),
                       input_dtypes=("FLOAT", "DT_UNDEFINED"),
                       output_dtypes=("FLOAT", "INT32", "FLOAT"),
                       input_formats=("ND", "NULL"),
                       output_formats=("ND", "ND", "ND")):
            return _fail("topk_local_rows_or_geometry_disagree", layer=lid)
        if not matches(permute, ((local_rows, hidden), (local_rows, top_k)),
                       ((dispatch_rows, hidden), (dispatch_rows,)),
                       input_dtypes=("DT_BF16", "INT32"),
                       output_dtypes=("DT_BF16", "INT32"),
                       input_formats=("ND", "ND"),
                       output_formats=("ND", "ND")):
            return _fail("permute_local_rows_or_capacity_disagree", layer=lid)
        valid = routing[1][0][0] if (
            routing[1] and len(routing[1]) == 3
            and isinstance(routing[1][0], tuple) and len(routing[1][0]) == 2) else None
        if (valid is None
                or not matches(routing,
                               ((valid, hidden), (valid, 1), (valid,)),
                               ((valid, hidden), (valid,),
                                (experts // ep,), (valid,)),
                               input_dtypes=("INT8", "INT32", "FLOAT"),
                               output_dtypes=("INT8", "INT32", "INT64", "FLOAT"),
                               input_formats=("ND", "ND", "ND"),
                               output_formats=("ND", "ND", "ND", "ND"))):
            return _fail("init_routing_geometry_or_bank_disagree", layer=lid)
        gate_sig = _single(layer, "gate")
        if (len(gate_sig[1]) != 5 or gate_sig[1][0] != (valid, hidden)
                or gate_sig[2] != ((valid, intermediate), (valid,))
                or gate_sig[3] != ("INT8", "INT8", "FLOAT", "FLOAT", "INT64")
                or gate_sig[4] != ("INT8", "FLOAT")
                or gate_sig[5] != ("ND", "FRACTAL_NZ", "ND", "ND", "ND")):
            return _fail("gate_input_output_row_or_dtype_disagree", layer=lid)
        if (gate[0] != "grouped_mlp_parameters_active"
                or gate[1] not in GATE_KINDS
                or gate[2] != (experts // ep, hidden, intermediate)
                or gate[3] != ("int8", "int8", "int8")):
            return _fail("gate_expert_bank_or_channel_geometry_disagree", layer=lid)
        if (grouped[0] != "grouped_matrix"
                or grouped[1] != (experts // ep, valid, hidden, intermediate)
                or grouped[2] != "int8" or grouped[3] != "int8"
                or grouped[4] != "bf16"):
            return _fail("grouped_down_rows_geometry_or_bank_disagree", layer=lid)
        values, combine, reconstruct = _unpermutes(
            layer, valid, local_rows, dispatch_rows, hidden, top_k)
        if combine is None or reconstruct is None or len(values) != 2:
            return _fail("finalize_unpermute_chain_disagree", layer=lid)
        ordered, positions = _positions(
            layer, ("topk", "permute", "dispatch_quant", "alltoall",
                    "allgather", "init_routing", "gate", "grouped"))
        router_pos = next((i for i, item in enumerate(ordered)
                           if item[2] == "matmul_v3" and item[3] == router), None)
        permute_pos = positions["permute"][0]
        quant_after = [i for i in positions["dispatch_quant"] if i > permute_pos]
        combine_pos = next((i for i, item in enumerate(ordered)
                            if item[2] == "unpermute" and item[3] == combine), None)
        reconstruct_pos = next((i for i, item in enumerate(ordered)
                                if item[2] == "unpermute"
                                and item[3] == reconstruct), None)
        copies = [i for i, item in enumerate(ordered)
                  if item[2] == "tensor_move"
                  and item[3][1] == ((local_rows, hidden),)
                  and item[3][2] == ((local_rows, hidden),)]
        after_reconstruct = [i for i, item in enumerate(ordered)
                             if i > reconstruct_pos and item[2] == "allgather"] \
            if reconstruct_pos is not None else []
        if (None in (router_pos, combine_pos, reconstruct_pos)
                or len(quant_after) != 1
                or positions["topk"][0] < router_pos
                or positions["topk"][0] > permute_pos
                or quant_after[0] > positions["alltoall"][0]
                or positions["allgather"][0] > permute_pos
                or positions["init_routing"][0] > positions["gate"][0]
                or positions["gate"][0] > positions["grouped"][0]
                or positions["grouped"][0] > combine_pos
                or combine_pos > positions["alltoall"][2]
                or positions["alltoall"][2] > reconstruct_pos
                or len(after_reconstruct) != 1
                or any(i < after_reconstruct[0] for i in copies)
                or len(copies) not in (0, tp)):
            return _fail("layer_chain_order_mismatch", layer=lid)
        materials.add("per_rank_copy" if copies else "view")
        layers.append({
            "layer_id": lid,
            "first_line": ordered[0][1],
            "full_rows": query_rows,
            "local_rows": local_rows,
            "partition_allocation_rows": local_rows * tp,
            "dispatch_allocation_rows": dispatch_rows,
            "native_gmm_rows": valid,
            "expected_local_valid_rows": expected_valid,
            "expert_banks": gate[2][0],
            "hidden": gate[2][1],
            "width": gate[2][2],
            "histogram_allgathers": 1,
            "auxiliary_histogram_gathers": counts.get("histogram_allgather", 0),
            "scale_exchanges": 1,
            "payload_exchanges": 1,
            "return_exchanges": 1,
            "finalize_gathers": 1,
            "gather_copies": len(copies),
        })
    if not layers:
        return _fail("selected_layer_chain_empty")
    if len(materials) != 1:
        return _fail("mixed_gather_materialization",
                     materials=sorted(materials))
    if len({item["expert_banks"] for item in layers}) != 1:
        return _fail("mixed_grouped_geometry")
    if len({item["hidden"] for item in layers}) != 1:
        return _fail("mixed_grouped_geometry")
    if len({item["width"] for item in layers}) != 1:
        return _fail("mixed_grouped_geometry")
    material = materials.pop()
    partition = {
        "kind": ALLTOALL_KIND,
        "padding": "none",
        "gather_output_materialization": material,
    }
    transport = dict(ALLTOALL_TRANSPORT)
    native_rows = [item["native_gmm_rows"] for item in layers]
    return {
        "ok": True,
        "family": "alltoall_tp_slice",
        "caller": {
            "moe_token_partition": dict(partition),
            "moe_transport": dict(transport),
        },
        "declaration": {
            "moe_token_partition": dict(partition),
            "moe_transport": dict(transport),
        },
        "source": {"alltoall": dict(ALLTOALL_SOURCE)},
        "allocation": {
            "full_rows": query_rows,
            "local_rows": local_rows,
            "partition_allocation_rows": local_rows * tp,
            "dispatch_allocation_rows": layers[0]["dispatch_allocation_rows"],
            "native_gmm_rows_min": min(native_rows),
            "native_gmm_rows_max": max(native_rows),
            "expected_local_valid_rows": layers[0]["expected_local_valid_rows"],
            "gmm_row_axis_role": "native_observed_rows_and_generated_expected_rows_are_separate",
            "gmm_rows_compared_to_generated": False,
            "valid_routed_rows": "observed_native_total_not_group_list",
        },
        "transport": {
            "kind": transport["kind"],
            "payload_dtype": transport["payload_dtype"],
            "scale_dtype": transport["scale_dtype"],
            "histogram_dtype": transport["histogram_dtype"],
            "histogram_dtype_basis": "source_declared_and_sim_transport",
            "histogram_dtype_at_native_boundary": "unobserved",
            "histogram_allgathers_per_layer": 1,
            "scale_exchanges_per_layer": 1,
            "payload_exchanges_per_layer": 1,
            "return_exchanges_per_layer": 1,
            "finalize_gathers_per_layer": 1,
            "peer_window": "unobserved",
            "native_protocol": "unobserved",
        },
        "layers": layers,
    }

def validate_a5(window, evidence_layers, *, tp, ep, hidden, experts, top_k,
                intermediate):
    """Validate every repeated A5 eager layer without inventing valid rows."""
    layers = []
    for index, layer in enumerate(evidence_layers):
        lid = window.layers[index].layer_id
        if layer.overflow:
            return _fail("descriptor_variant_limit_exceeded", layer=lid)
        counts = layer.roles
        for role, count in (("topk", 1), ("init_routing", 1), ("grouped", 2),
                            ("swiglu", 1), ("finalize", 1)):
            if counts.get(role, 0) != count:
                return _fail("layer_role_count_mismatch", layer=lid, role=role,
                             expected=count, observed=counts.get(role, 0))
        for forbidden in ("dispatch", "combine", "alltoall", "permute",
                          "unpermute", "gate", "other_moe"):
            if counts.get(forbidden):
                return _fail("mixed_scoped_native_callers", layer=lid,
                             role=forbidden)
        query_rows = window.query_rows
        allocation = query_rows * top_k
        expected_valid = _expected_local_valid(query_rows, top_k, ep)
        router, router_issue = _router(layer, query_rows, hidden, experts)
        if router is None:
            return _fail(router_issue, layer=lid)
        topk = _single(layer, "topk")
        routing = _single(layer, "init_routing")
        swiglu = _single(layer, "swiglu")
        finalize = _single(layer, "finalize")
        if None in (topk, routing, swiglu, finalize):
            return _fail("layer_descriptor_variant_not_unique", layer=lid)
        if not matches(topk, ((query_rows, experts),),
                       ((query_rows, top_k), (query_rows, top_k),
                        (query_rows, experts)),
                       input_dtypes=("FLOAT",),
                       output_dtypes=("FLOAT", "INT32", "FLOAT"),
                       input_formats=("ND",),
                       output_formats=("ND", "ND", "ND")):
            return _fail("topk_router_rows_disagree", layer=lid)
        if not matches(routing, ((query_rows, hidden), (query_rows, top_k)),
                       ((allocation, hidden), (allocation,),
                        (experts // ep,), (allocation,)),
                       input_dtypes=("DT_BF16", "INT32"),
                       output_dtypes=("DT_BF16", "INT32", "INT64", "FLOAT"),
                       input_formats=("ND", "ND"),
                       output_formats=("ND", "ND", "ND", "ND")):
            return _fail("eager_init_routing_allocation_or_bank_disagree",
                         layer=lid)
        grouped = list(layer.variants.get("grouped", {}).items())
        up_signature = next((sig for sig, value in grouped
                             if isinstance(value, tuple)
                             and value[0] == "grouped_matrix"
                             and value[1] == (experts // ep, allocation,
                                              2 * intermediate, hidden)
                             and value[2:] == ("bf16", "bf16", "bf16", (), "")),
                            None)
        down_signature = next((sig for sig, value in grouped
                               if isinstance(value, tuple)
                               and value[0] == "grouped_matrix"
                               and value[1] == (experts // ep, allocation,
                                                hidden, intermediate)
                               and value[2:] == ("bf16", "bf16", "bf16", (), "")),
                              None)
        if up_signature is None or down_signature is None:
            return _fail("eager_grouped_projection_geometry_disagree",
                         layer=lid)
        if not matches(swiglu, ((allocation, 2 * intermediate),),
                       ((allocation, intermediate),),
                       input_dtypes=("DT_BF16",),
                       output_dtypes=("DT_BF16",),
                       input_formats=("ND",),
                       output_formats=("ND",)):
            return _fail("swiglu_allocation_or_intermediate_disagree",
                         layer=lid)
        if not matches(finalize, ((allocation, hidden), (allocation,),
                                  (query_rows, top_k)),
                       ((query_rows, hidden),),
                       input_dtypes=("DT_BF16", "INT32", "DT_BF16"),
                       output_dtypes=("DT_BF16",),
                       input_formats=("ND", "ND", "ND"),
                       output_formats=("ND",)):
            return _fail("finalize_rows_or_weights_disagree", layer=lid)
        ordered, positions = _positions(
            layer, ("init_routing", "grouped", "swiglu", "finalize",
                    "allreduce"))
        init_pos = positions["init_routing"][0]
        up_pos = next((i for i, item in enumerate(ordered)
                       if item[2] == "grouped" and item[3] == up_signature), None)
        down_pos = next((i for i, item in enumerate(ordered)
                         if item[2] == "grouped" and item[3] == down_signature),
                        None)
        swiglu_pos = positions["swiglu"][0]
        finalize_pos = positions["finalize"][0]
        final_reduce = [i for i in positions["allreduce"] if i > finalize_pos]
        if (None in (up_pos, down_pos)
                or not init_pos < up_pos < swiglu_pos < down_pos < finalize_pos
                or not final_reduce):
            return _fail("layer_chain_order_mismatch", layer=lid)
        layers.append({
            "layer_id": lid,
            "first_line": ordered[0][1],
            "query_rows": query_rows,
            "allocation_rows": allocation,
            "expected_local_valid_rows": expected_valid,
            "native_gmm_rows": allocation,
            "expert_banks": experts // ep,
            "hidden": hidden,
            "intermediate": intermediate,
            "final_reductions_after_finalize": len(final_reduce),
            "valid_routed_rows": "unobserved",
            "gmm_row_axis_role": "allocated_capacity_including_unselected_slots",
        })
    if not layers:
        return _fail("selected_layer_chain_empty")
    return {
        "ok": True,
        "family": "local_expert_reduce",
        "caller": {"moe_recipe": LOCAL_EXPERT_RECIPE},
        "declaration": {"moe_recipe": LOCAL_EXPERT_RECIPE},
        "source": {"local_expert": dict(LOCAL_EXPERT_SOURCE)},
        "allocation": {
            "query_rows": query_rows,
            "init_routing_allocation_rows": query_rows * top_k,
            "native_gmm_rows": query_rows * top_k,
            "expected_local_valid_rows": _expected_local_valid(
                query_rows, top_k, ep),
            "gmm_row_axis_role": "allocated_capacity_including_unselected_slots",
            "gmm_rows_compared_to_generated": False,
            "valid_routed_rows": "unobserved",
            "swiglu_rows": "full_allocation",
        },
        "layers": layers,
    }

def _op_summary(ops):
    layers = {}
    for op in ops:
        if op.layer is None:
            continue
        item = layers.setdefault(op.layer, {
            "recipes": Counter(),
            "metadata": [],
            "grouped": [],
            "partition": None,
            "copies": 0,
        })
        metadata = dict(op.metadata)
        item["recipes"][op.recipe] += 1
        item["metadata"].append((op.recipe, metadata, tuple(op.local_shape)))
        if "moe_token_partition" in metadata:
            item["partition"] = metadata["moe_token_partition"]
        if "gathered_slice" in metadata:
            item["copies"] += 1
        grouped_role = GROUPED_SEMANTIC_RECIPES.get(op.recipe)
        if grouped_role is not None:
            item["grouped"].append({
                "recipe": grouped_role,
                "banks": metadata.get("matrix_weight_bank_groups"),
                "shape": tuple(op.local_shape),
                "dtype": op.dtype,
                "metadata": {key: metadata.get(key) for key in (
                    "expected_rows", "allocated_routing_rows")},
            })
    return layers

def _comm_items(summary, recipe):
    return [entry for entry in summary["metadata"] if entry[0] == recipe]

def generated_mismatches(family, ops, *, window, tp, ep, hidden, experts,
                         top_k, intermediate, material):
    if ops is None:
        return [{"field": "generated_graph", "reason": "unavailable"}]
    layers = _op_summary(ops)
    if len(layers) != len(window.layers):
        return [{"field": "generated_layers", "observed": len(layers),
                 "expected": len(window.layers)}]
    bad = []
    expected_copies = tp if material == "per_rank_copy" else 0
    for layer_id in range(len(window.layers)):
        item = layers.get(layer_id)
        if item is None:
            bad.append({"field": "generated_layer", "layer": layer_id,
                        "reason": "missing"})
            continue
        if family == "alltoall_tp_slice":
            partition = item["partition"]
            if not isinstance(partition, dict):
                bad.append({"field": "moe_token_partition",
                            "layer": layer_id, "reason": "missing"})
            else:
                for field, value in (
                        ("kind", ALLTOALL_KIND),
                        ("padding", "none"),
                        ("gather_output_materialization", material),
                        ("full_rows", window.query_rows),
                        ("local_rows", window.query_rows // tp),
                        ("tp", tp),
                        ("allocated_rows", (window.query_rows // tp) * tp)):
                    if partition.get(field) != value:
                        bad.append({"field": "moe_token_partition." + field, "layer": layer_id, "observed": partition.get(field), "generated": value})
            recipes = item["recipes"]
            hist = _comm_items(item, "moe_expert_count_histogram")
            if len(hist) != 1:
                bad.append({"field": "histogram", "layer": layer_id, "observed": len(hist)})
            elif hist[0][1].get("histogram_dtype") != "int32":
                bad.append({"field": "histogram_dtype", "layer": layer_id, "observed": hist[0][1].get("histogram_dtype")})
            hist_gather = [entry for entry in item["metadata"] if entry[0] == "ring_allgather" and entry[1].get("traffic_model") == "local_expert_count_allgather"]
            if len(hist_gather) != 1:
                bad.append({"field": "histogram_gather", "layer": layer_id, "observed": len(hist_gather)})
            scale = _comm_items(item, "expert_scale_dispatch")
            if len(scale) != 1:
                bad.append({"field": "scale_exchange", "layer": layer_id,
                            "observed": len(scale)})
            elif scale[0][1].get("payload_dtype") != "fp32":
                bad.append({"field": "scale_payload_dtype", "layer": layer_id,
                            "observed": scale[0][1].get("payload_dtype")})
            payload = _comm_items(item, "expert_quantized_dispatch")
            return_exchange = _comm_items(item, "expert_combine")
            if len(payload) != 1:
                bad.append({"field": "payload_exchange", "layer": layer_id,
                            "observed": len(payload)})
            elif payload[0][1].get("payload_dtype") != "int8":
                bad.append({"field": "payload_dtype", "layer": layer_id,
                            "observed": payload[0][1].get("payload_dtype")})
            if len(return_exchange) != 1:
                bad.append({"field": "return_exchange", "layer": layer_id,
                            "observed": len(return_exchange)})
            gather_after = [entry for entry in item["metadata"] if entry[0] == "ring_allgather" and entry[1].get("traffic_model") != "local_expert_count_allgather"]
            if len(gather_after) != 1:
                bad.append({"field": "finalize_gather", "layer": layer_id, "observed": len(gather_after)})
            if item["copies"] != expected_copies:
                bad.append({"field": "gather_copies", "layer": layer_id,
                            "observed": item["copies"],
                            "expected": expected_copies})
            expected_valid = _expected_local_valid(window.query_rows, top_k, ep)
            gate = next((entry for entry in item["grouped"]
                         if entry["recipe"] == "grouped_gate_up"), None)
            down = next((entry for entry in item["grouped"]
                         if entry["recipe"] == "grouped_down"), None)
            if gate is None or down is None:
                bad.append({"field": "grouped_roles", "layer": layer_id})
            else:
                if gate["banks"] != experts // ep or down["banks"] != experts // ep:
                    bad.append({"field": "grouped_banks", "layer": layer_id})
                if (gate["shape"][:2] != (expected_valid, 2 * intermediate)
                        or gate["shape"][2] != hidden):
                    bad.append({"field": "gate_expected_rows_or_width",
                                "layer": layer_id,
                                "observed": gate["shape"]})
                if (down["shape"][:2] != (expected_valid, hidden)
                        or down["shape"][2] != intermediate):
                    bad.append({"field": "down_expected_rows_or_width",
                                "layer": layer_id,
                                "observed": down["shape"]})
            dispatch = (window.query_rows // tp) * top_k
            if payload and payload[0][2][:2] != (dispatch, hidden):
                bad.append({"field": "payload_allocation_shape",
                            "layer": layer_id,
                            "observed": payload[0][2][:2]})
        else:
            if item["partition"] is not None:
                bad.append({"field": "moe_token_partition",
                            "layer": layer_id, "reason": "unexpected"})
            recipes = item["recipes"]
            for recipe in ("expert_dispatch", "expert_combine", "expert_scale_dispatch", "expert_quantized_dispatch"):
                if recipes.get(recipe):
                    bad.append({"field": "transport_recipe", "layer": layer_id, "observed": recipe})
            route_pack = _comm_items(item, "route_pack")
            if len(route_pack) != 1 or route_pack[0][2][:2] != (
                    window.query_rows, top_k):
                bad.append({"field": "route_pack", "layer": layer_id})
            expected_valid = _expected_local_valid(window.query_rows, top_k, ep)
            allocation = window.query_rows * top_k
            gate = next((entry for entry in item["grouped"]
                         if entry["recipe"] == "grouped_gate_up"), None)
            down = next((entry for entry in item["grouped"]
                         if entry["recipe"] == "grouped_down"), None)
            swiglu = _comm_items(item, "grouped_swiglu")
            if gate is None or down is None:
                bad.append({"field": "grouped_roles", "layer": layer_id})
            else:
                if gate["banks"] != experts // ep or down["banks"] != experts // ep:
                    bad.append({"field": "grouped_banks", "layer": layer_id})
                if (gate["shape"][:2] != (expected_valid, 2 * intermediate)
                        or gate["shape"][2] != hidden):
                    bad.append({"field": "gate_expected_rows_or_width",
                                "layer": layer_id,
                                "observed": gate["shape"]})
                if (down["shape"][:2] != (expected_valid, hidden)
                        or down["shape"][2] != intermediate):
                    bad.append({"field": "down_expected_rows_or_width",
                                "layer": layer_id,
                                "observed": down["shape"]})
            if len(swiglu) != 1 or swiglu[0][2][:2] != (
                    allocation, intermediate):
                bad.append({"field": "swiglu_full_allocation",
                            "layer": layer_id})
            elif (swiglu[0][1].get("allocated_routing_rows") != allocation
                  or swiglu[0][1].get("activation_rows") != allocation):
                bad.append({"field": "swiglu_capacity_rows",
                            "layer": layer_id})
            route_unpack = _comm_items(item, "route_unpack")
            if len(route_unpack) != 1:
                bad.append({"field": "route_unpack", "layer": layer_id,
                            "observed": len(route_unpack)})
            unpack_pos = next((pos for pos, entry in enumerate(item["metadata"])
                               if entry[0] == "route_unpack"), None)
            reduce_positions = [pos for pos, entry in enumerate(item["metadata"])
                                if entry[0] in {"moe_output_reduce", "ring_allreduce"}
                                or "allreduce" in entry[0]]
            if unpack_pos is None or not any(pos > unpack_pos
                                             for pos in reduce_positions):
                bad.append({"field": "final_reduction", "layer": layer_id})
    return bad
