"""Consume witnessed MoE route geometry with an existing sim recipe.

Row identity and collective names come from one kernel. A duration, a top-k
value alone, a case id, and a path do not select the algorithm. The gate
projection, the gating input, and the grouped expert rows are separate
tensor edges. Query rows on the producer frames only associate a population
with a forward. A partial exchange keeps the token partition, selects
alltoall, and removes the native fullmesh protocol. When that source also
shows three alltoallv and two allgather per layer on an int8 row-scale
model, the existing operator-graph transport is declared so the scale
dispatch and the histogram gather are part of the graph. Widths stay the
layer latent times the dtype. A replicated allreduce selects
local_expert_reduce for a floating expert and for W8A8 whose shared expert
is the activation float or the same int8. The W8A8 witness prices the
grouped matmul at the full eager allocation. A source that does not show
the projection edge is recorded and left unchanged.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping

from fleet_archive_producer_reader import _MATRIX_ROW_CAP, _shape_slots

_FLOAT_EXPERT_FORMATS = {"bf16": "bf16", "bfloat16": "bf16", "fp16": "fp16", "float16": "fp16"}
_W8A8_FORMATS = {"int8": "int8", "w8a8": "int8"}
_CONTRACT = "mindie-sim/replicated-allreduce-packed-grouped-rows/1"
_DROPPED_KEYS = ("moe_token_partition", "native_moe_protocol", "moe_transport")
_ROW_SCALE_TRANSPORT = {
    "kind": "separate_quantized_payload",
    "payload_dtype": "int8",
    "scale_dtype": "fp32",
    "scale_granularity": "row",
    "histogram_dtype": "int64",
}
_FULL_EAGER_GROUPED = "full_eager_allocation"


def _rank2(slot: Any) -> tuple[int, int] | None:
    if isinstance(slot, tuple) and len(slot) == 2 and all(type(item) is int for item in slot):
        return slot
    return None


def _leading(slots: list | None) -> int | None:
    if not slots:
        return None
    shape = _rank2(slots[0])
    return shape[0] if shape is not None else None


def _collective(name: str) -> str | None:
    """Count the named collective record. A type-only AivKernel alias is the same launch."""
    text = str(name or "").lower()
    if "alltoallv" in text:
        return "alltoallv"
    if "allgather" in text:
        return "allgather"
    if "allreduce" in text or "all_reduce" in text:
        return "allreduce"
    return None


def _family(name: str, op_type: str) -> str:
    text = f"{name} {op_type}".lower()
    if "moegatingtopk" in text:
        return "gating"
    if "moeinitroutingv2" in text:
        return "init_v2"
    if "moeinitroutingv3" in text:
        return "init_v3"
    if "moefinalize" in text or "unpermute" in text:
        return "finalize"
    if "moetokenpermute" in text:
        return "permute"
    if "groupedmatmul" in text:
        return "grouped"
    return ""


def _segment_meta(name: str, op_type: str) -> bool:
    text = f"{name} {op_type}".lower()
    return any(token in text for token in ("cast", "tensormove", "hccllaunch", "aivkernel"))


def _blank_layer(device: str, gating_rows: int, experts: int | None, topk: int | None,
                 projection_rows: int | None, prelude_allreduce: int) -> dict[str, Any]:
    return {
        "device": device, "gating_rows": gating_rows, "experts": experts, "topk": topk,
        "projection_rows": projection_rows, "projection_absent": projection_rows is None,
        "topk_conflict": topk is None, "permute_topk": None, "grouped": set(), "expand": set(),
        "tiles": set(), "events": [], "init_v2": 0, "init_v3": 0,
        "prelude_allreduce": prelude_allreduce,
    }


def _projection_edge(name: str, op_type: str, inputs: list | None, outputs: list | None) -> tuple[int, int] | None:
    """Token-preserving matmul. The returned pair is input/output rows and output width."""
    text = f"{name} {op_type}".lower()
    if "matmul" not in text or "grouped" in text:
        return None
    entered = _rank2(inputs[0]) if inputs else None
    left = _rank2(outputs[0]) if outputs else None
    if entered is None or left is None or entered[0] != left[0] or entered[0] <= 1:
        return None
    return entered[0], left[1]


def _epilogue_matmul(name: str, op_type: str, inputs: list | None) -> bool:
    """A leading row of 1 is the post-body logits matmul, not an expert projection."""
    text = f"{name} {op_type}".lower()
    if "matmul" not in text or "grouped" in text:
        return False
    entered = _rank2(inputs[0]) if inputs else None
    return entered is not None and entered[0] == 1


def _immediate_allreduce(events: list[tuple[str, str | None]]) -> int:
    """The allreduce touching the next projection. An earlier collective is another region."""
    for kind, value in reversed(events):
        if kind in {"meta", "compute"}:
            continue
        if kind == "collective" and value == "allreduce":
            return 1
        return 0
    return 0


def _split_epilogue(events: list[tuple[str, str | None]]) -> tuple[list[tuple[str, str | None]], list[tuple[str, str | None]]]:
    for index, (kind, _value) in enumerate(events):
        if kind == "epilogue":
            return events[:index], events[index:]
    return events, []


def _note_gap(name: str, op_type: str, inputs: list | None, outputs: list | None,
              pending: tuple[int, int] | None) -> tuple[list[tuple[str, str | None]], tuple[int, int] | None]:
    """Keep the gate matmul that still reaches the next gating. Logits close the body."""
    if _epilogue_matmul(name, op_type, inputs):
        return [("epilogue", None)], None
    event = _event(name, op_type)
    projection = _projection_edge(name, op_type, inputs, outputs)
    if projection is not None:
        return [event], projection
    if event[0] == "compute":
        return [event], None
    return [event], pending


def _observe_layer(layer: dict[str, Any], family: str, inputs: list | None, outputs: list | None) -> None:
    if family == "permute" and inputs and len(inputs) >= 2:
        second = _rank2(inputs[1])
        if second is not None:
            if layer["permute_topk"] not in (None, second[1]):
                layer["topk_conflict"] = True
            layer["permute_topk"] = second[1]
    elif family == "init_v2":
        layer["init_v2"] += 1
        rows = _leading(outputs)
        if rows is not None:
            layer["expand"].add(rows)
    elif family == "init_v3":
        layer["init_v3"] += 1
        rows = _leading(outputs)
        if rows is not None:
            layer["expand"].add(rows)
        for slot in outputs or []:
            if isinstance(slot, tuple) and len(slot) == 1 and type(slot[0]) is int and slot[0] != rows:
                layer["tiles"].add(slot[0])
    elif family == "grouped":
        rows = _leading(inputs)
        if rows is None:
            rows = _leading(outputs)
        if rows is not None:
            layer["grouped"].add(rows)


def _singleton(values: set[int]) -> int | None:
    if len(values) == 1:
        return next(iter(values))
    return None


def _event(name: str, op_type: str) -> tuple[str, str | None]:
    family = _family(name, op_type)
    if family in {"init_v2", "init_v3", "permute", "finalize"}:
        return "routing", family
    if family == "grouped":
        return "grouped", None
    collective = _collective(name)
    if collective is not None:
        return "collective", collective
    if _segment_meta(name, op_type):
        return "meta", None
    return "compute", None


def _route_counts(events: list[tuple[str, str | None]]) -> dict[str, int]:
    """Exchange collectives stay with the routing ops. Later math is another collective."""
    last = max((index for index, (kind, _value) in enumerate(events) if kind in {"routing", "grouped"}), default=-1)
    end = last + 1
    if last >= 0:
        while end < len(events) and events[end][0] in {"collective", "meta"}:
            end += 1
    counts = {"alltoallv": 0, "allgather": 0, "allreduce": 0}
    for index, (kind, value) in enumerate(events):
        if kind != "collective" or value not in counts:
            continue
        if value != "allreduce" and last >= 0 and index < end:
            counts[value] += 1
        elif value == "allreduce":
            counts["allreduce"] += 1
    return counts


def _finish_layer(layer: dict[str, Any]) -> dict[str, Any]:
    grouped = _singleton(layer["grouped"])
    expand = _singleton(layer["expand"])
    tile = _singleton(layer["tiles"])
    topk = layer["topk"]
    if layer["permute_topk"] is not None and topk is not None and layer["permute_topk"] != topk:
        layer["topk_conflict"] = True
    conflict = []
    if layer["topk_conflict"] or topk is None:
        conflict.append("topk_sources_disagree")
    if len(layer["grouped"]) != 1:
        conflict.append("grouped_rows_disagree")
    if len(layer["expand"]) > 1:
        conflict.append("expand_rows_disagree")
    if expand is not None and grouped is not None and expand != grouped:
        conflict.append("expand_disagrees_with_grouped_rows")
    if len(layer["tiles"]) > 1:
        conflict.append("expert_tile_disagrees")
    if layer["projection_absent"]:
        conflict.append("projection_edge_absent")
    counts = _route_counts(layer["events"])
    return {
        "device": layer["device"], "gating_rows": layer["gating_rows"], "experts": layer["experts"],
        "topk": topk, "projection_rows": layer["projection_rows"],
        "grouped_rows": grouped, "expand_rows": expand, "expert_tile": tile,
        "layers": 1, "alltoallv": counts["alltoallv"], "allgather": counts["allgather"],
        "allreduce": counts["allreduce"] + int(layer["prelude_allreduce"]),
        "init_v2": layer["init_v2"], "init_v3": layer["init_v3"],
        "conflict": conflict,
    }


def _same_population(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    keys = ("device", "gating_rows", "topk", "projection_rows", "grouped_rows", "expand_rows", "expert_tile")
    return all(left.get(key) == right.get(key) for key in keys) and not left["conflict"] and not right["conflict"]


def _merge(left: dict[str, Any], right: Mapping[str, Any]) -> None:
    left["layers"] += int(right["layers"])
    for key in ("alltoallv", "allgather", "allreduce", "init_v2", "init_v3"):
        left[key] += int(right[key])


def witness_route_geometry(source: Path, *, row_cap: int = _MATRIX_ROW_CAP) -> dict[str, Any]:
    """Read route operators and collectives. Timestamps are not read."""
    witness: dict[str, Any] = {
        "opened": False, "rows_seen": 0, "capped": False, "reason": None,
        "populations": [], "orphan_collectives": 0, "expert_chain_without_route": False,
    }
    if not isinstance(source, Path) or not source.is_file() or source.name.endswith(".gz"):
        witness["reason"] = "source_not_read"
        return witness
    layers: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    prefix_events: list[tuple[str, str | None]] = []
    pending: tuple[int, int] | None = None
    saw_grouped = False
    saw_swiglu = False
    try:
        with source.open(newline="", encoding="utf-8", errors="replace") as handle:
            reader = csv.DictReader(handle)
            names = reader.fieldnames or []
            if "Name" not in names or "Input Shapes" not in names or "Output Shapes" not in names:
                witness["reason"] = "shape_columns_absent"
                return witness
            witness["opened"] = True
            for index, row in enumerate(reader):
                if index >= row_cap:
                    witness["capped"] = True
                    break
                witness["rows_seen"] = index + 1
                name = row.get("Name") or ""
                op_type = row.get("Type") or ""
                family = _family(name, op_type)
                collective = _collective(name)
                inputs = _shape_slots(row.get("Input Shapes") or "", True)
                outputs = _shape_slots(row.get("Output Shapes") or "", True)
                if family == "grouped":
                    saw_grouped = True
                if "swiglu" in f"{name} {op_type}".lower():
                    saw_swiglu = True
                if family == "gating":
                    carry = 0
                    if current is not None:
                        head, tail = _split_epilogue(current["events"])
                        current["events"] = head
                        carry = _immediate_allreduce(tail)
                        layers.append(_finish_layer(current))
                    else:
                        carry = _immediate_allreduce(prefix_events)
                    shape = _rank2(inputs[0]) if inputs else None
                    experts = shape[1] if shape is not None else None
                    rows = shape[0] if shape is not None else None
                    topk_values = []
                    for slot in outputs or []:
                        parsed = _rank2(slot)
                        if parsed is not None and parsed[1] != experts:
                            topk_values.append(parsed[1])
                    topk = topk_values[0] if topk_values and all(item == topk_values[0] for item in topk_values) else None
                    projection = pending[0] if pending is not None and experts is not None and pending[1] == experts else None
                    pending = None
                    current = _blank_layer(
                        str(row.get("Device_id") or ""), rows if rows is not None else -1, experts, topk,
                        projection, carry,
                    )
                    if rows is None:
                        current["topk_conflict"] = True
                    continue
                noted = _note_gap(name, op_type, inputs, outputs, pending)
                if current is None:
                    if collective is not None:
                        witness["orphan_collectives"] += 1
                    prefix_events.extend(noted[0])
                    pending = noted[1]
                    continue
                current["events"].extend(noted[0])
                pending = noted[1]
                if family:
                    _observe_layer(current, family, inputs, outputs)
    except OSError:
        witness["opened"] = False
        witness["reason"] = "source_not_read"
        return witness
    if current is not None:
        head, _tail = _split_epilogue(current["events"])
        current["events"] = head
        layers.append(_finish_layer(current))
    populations: list[dict[str, Any]] = []
    for layer in layers:
        if populations and _same_population(populations[-1], layer):
            _merge(populations[-1], layer)
            continue
        populations.append(dict(layer))
    witness["populations"] = populations
    witness["expert_chain_without_route"] = bool(saw_grouped and saw_swiglu and not populations and not witness["orphan_collectives"])
    return witness


def _match_frames(population: Mapping[str, Any], frames: list[Mapping[str, Any]], tp: int | None) -> dict[str, Any]:
    gating = population.get("gating_rows")
    relations = []
    forward_ids = []
    queries = []
    for frame in frames:
        query = frame.get("query_rows")
        if not isinstance(query, int) or not isinstance(gating, int) or gating < 0:
            continue
        device = str(frame.get("device_id") or "")
        if device and population.get("device") and device != population["device"]:
            continue
        if gating == query:
            relation = "gating_equals_query"
        elif isinstance(tp, int) and tp > 1 and gating * tp == query:
            relation = "gating_times_tp"
        else:
            continue
        relations.append(relation)
        queries.append(query)
        forward_ids.append(frame.get("forward_id"))
    unique = set(relations)
    return {
        "query_relation": relations[0] if len(unique) == 1 else None,
        "query_rows": queries[0] if len(set(queries)) == 1 else None,
        "query_rows_seen": sorted(set(queries)),
        "forward_ids": forward_ids,
        "query_conflict": len(unique) > 1,
    }


def _classify(population: Mapping[str, Any], association: Mapping[str, Any]) -> tuple[str | None, str | None]:
    if population.get("conflict") == ["projection_edge_absent"]:
        return None, "projection_edge_absent"
    if population.get("conflict"):
        return None, "row_sources_disagree:" + ",".join(population["conflict"])
    if association.get("query_conflict"):
        return None, "query_relation_disagrees"
    gating = population.get("gating_rows")
    topk = population.get("topk")
    grouped = population.get("grouped_rows")
    projection = population.get("projection_rows")
    if not isinstance(gating, int) or gating < 0 or not isinstance(topk, int) or not isinstance(grouped, int):
        return None, "row_sources_incomplete"
    if not isinstance(projection, int):
        return None, "projection_edge_absent"
    expanded = grouped == gating * topk
    unexpanded = grouped == gating
    exchange = population["alltoallv"] > 0 and population["allgather"] > 0
    replicated = population["alltoallv"] == 0 and population["allgather"] == 0 and population["allreduce"] > 0
    quiet = population["alltoallv"] == 0 and population["allgather"] == 0 and population["allreduce"] == 0
    relation = association.get("query_relation")
    query = association.get("query_rows")
    if exchange and expanded:
        if relation == "gating_times_tp":
            if projection == query:
                return "expert_alltoallv", None
            return None, "projection_disagrees_with_partial_route"
        if relation == "gating_equals_query":
            return None, "alltoallv_with_replicated_token_rows"
        return None, "query_rows_unassociated"
    if replicated and expanded:
        if relation == "gating_equals_query":
            if projection == gating == query:
                return "replicated_allreduce", None
            return None, "projection_disagrees_with_replicated_route"
        return None, "query_rows_unassociated" if relation is None else "replicated_collectives_without_replicated_query"
    if quiet and unexpanded:
        return "local_no_route", None
    if quiet and expanded:
        return None, "expand_without_collectives"
    if population["alltoallv"] or population["allgather"] or population["allreduce"]:
        return None, "row_identity_unmatched"
    return None, "row_identity_unmatched"


def _expert_formats(model: Mapping[str, Any] | None) -> tuple[str, str]:
    """Mirror local_expert_reduce's routed and shared format read."""
    if not isinstance(model, Mapping):
        return "", ""
    quant = model.get("quant") if isinstance(model.get("quant"), Mapping) else None
    if quant is None:
        name = str(model.get("quantization") or "none").strip().lower()
        if name in {"", "none"}:
            native = str(model.get("activation_dtype") or "bf16").strip().lower()
            return native, native
        if "int8" in name or "w8a8" in name or name.startswith("w8"):
            return "int8", "int8"
        return name, name
    native = str(quant.get("native_format") or "bf16").strip().lower()
    expert = str(quant.get("expert_weight_format") or quant.get("weight_format") or native).strip().lower()
    weight = str(quant.get("weight_format") or native).strip().lower()
    overrides = quant.get("category_overrides") if isinstance(quant.get("category_overrides"), Mapping) else {}
    routed = overrides.get("routed_expert") if isinstance(overrides.get("routed_expert"), Mapping) else {}
    shared = overrides.get("shared_expert") if isinstance(overrides.get("shared_expert"), Mapping) else {}
    if routed.get("weight_format"):
        expert = str(routed["weight_format"]).strip().lower()
    shared_format = str(shared.get("weight_format") or weight).strip().lower() if shared else weight
    return expert, shared_format


def _quant_rejection(model: Mapping[str, Any] | None) -> str | None:
    """Reject expert formats local_expert_reduce still cannot execute.

    W8A8 routed int8 with a floating activation is legal when the shared
    expert is that activation or the same int8. Shared int8 beside a floating
    routed expert, mixed floats, and other quantized formats stay refused.
    """
    activation = _FLOAT_EXPERT_FORMATS.get(str((model or {}).get("activation_dtype") or "bf16").strip().lower())
    if activation is None:
        return f"local_expert_reduce_requires_floating_activation_dtype:{(model or {}).get('activation_dtype')}"
    routed, shared = _expert_formats(model)
    routed_f = _FLOAT_EXPERT_FORMATS.get(routed)
    shared_f = _FLOAT_EXPERT_FORMATS.get(shared)
    routed_q = _W8A8_FORMATS.get(routed)
    shared_q = _W8A8_FORMATS.get(shared)
    if routed_f is not None and shared_f is not None:
        if routed_f != activation:
            return f"local_expert_reduce_rejects_mixed_expert_format:routed_expert:{routed_f}!={activation}"
        if shared_f != activation:
            return f"local_expert_reduce_rejects_mixed_expert_format:shared_expert:{shared_f}!={activation}"
        return None
    if routed_q == "int8" and (shared_f == activation or shared_q == "int8"):
        return None
    if routed_f is None:
        return f"local_expert_reduce_rejects_quantized_expert_format:routed_expert:{routed or 'absent'}"
    return f"local_expert_reduce_rejects_quantized_expert_format:shared_expert:{shared or 'absent'}"


def _row_scale_int8(model: Mapping[str, Any] | None) -> bool:
    """This model's int8 row-scale identity. A block or MX scale is not it."""
    if not isinstance(model, Mapping):
        return False
    activation = str(model.get("activation_dtype") or "").strip().lower()
    if activation not in {"bf16", "bfloat16"}:
        return False
    routed, _shared = _expert_formats(model)
    if routed not in _W8A8_FORMATS:
        return False
    name = str(model.get("quantization") or "").strip().lower()
    if any(token in name for token in ("mx", "fp8", "fp4")):
        return False
    quant = model.get("quant") if isinstance(model.get("quant"), Mapping) else {}
    scale = str(quant.get("activation_scale_format") or quant.get("scale_format") or "fp32").strip().lower()
    if scale not in {"", "fp32", "float32"}:
        return False
    group = quant.get("activation_group_size")
    if isinstance(group, bool) or (isinstance(group, int) and group not in (0,)):
        return False
    return True


def _scale_dispatch_witnessed(classified: list) -> bool:
    """Three alltoallv and two allgather on every population, counted per layer."""
    if not classified:
        return False
    for population, _association, _algorithm, _reason in classified:
        layers = population.get("layers")
        if not isinstance(layers, int) or layers < 1:
            return False
        if population.get("alltoallv") != 3 * layers or population.get("allgather") != 2 * layers:
            return False
    return True


def _parallel_rejection(runtime: Mapping[str, Any], model: Mapping[str, Any] | None) -> str | None:
    kernels = runtime.get("kernels") if isinstance(runtime.get("kernels"), Mapping) else {}
    if "sequence_parallel" in kernels:
        return "local_expert_reduce_rejects_sequence_parallel_declaration"
    tp, dp, ep = runtime.get("tp"), runtime.get("dp"), runtime.get("ep")
    if dp != 1:
        return f"local_expert_reduce_requires_dp1:{dp}"
    if not isinstance(ep, int) or not isinstance(tp, int) or ep < 2 or ep != tp:
        return f"local_expert_reduce_requires_ep_equals_tp:{ep}!={tp}"
    for key, minimum in (("etp", 1), ("cp", 1)):
        value = runtime.get(key, 1)
        if value != 1:
            return f"local_expert_reduce_requires_{key}1:{value}"
    for key in ("pp", "pcp"):
        value = runtime.get(key, 1)
        if not isinstance(value, int) or value < 1:
            return f"local_expert_reduce_requires_{key}:{value}"
    experts = None if not isinstance(model, Mapping) else model.get("num_experts")
    if isinstance(experts, int) and experts % ep:
        return f"local_expert_reduce_requires_divisible_expert_banks:{experts}%{ep}"
    return None


def _public_population(population: Mapping[str, Any], association: Mapping[str, Any], algorithm: str | None,
                       reason: str | None) -> dict[str, Any]:
    return {
        "device": population.get("device"), "gating_rows": population.get("gating_rows"),
        "projection_rows": population.get("projection_rows"),
        "topk": population.get("topk"), "grouped_rows": population.get("grouped_rows"),
        "expand_rows": population.get("expand_rows"), "expert_tile": population.get("expert_tile"),
        "layers": population.get("layers"), "alltoallv": population.get("alltoallv"),
        "allgather": population.get("allgather"), "allreduce": population.get("allreduce"),
        "init_routing_v2": population.get("init_v2"), "init_routing_v3": population.get("init_v3"),
        "query_rows": association.get("query_rows"), "query_relation": association.get("query_relation"),
        "forward_ids": list(association.get("forward_ids") or []),
        "algorithm": algorithm, "reason": reason,
    }


def _ep_divided(population: Mapping[str, Any], association: Mapping[str, Any], ep: Any) -> int | None:
    query = association.get("query_rows")
    topk = population.get("topk")
    grouped = population.get("grouped_rows")
    if not isinstance(query, int) or not isinstance(topk, int) or not isinstance(ep, int) or ep < 1:
        return None
    if query * topk % ep:
        return None
    divided = query * topk // ep
    if divided == grouped:
        return None
    return divided


def apply_witnessed_route(runtime: dict, model: Any, source: Path, frames: list[Mapping[str, Any]] | None,
                          replaced: list[dict[str, Any]], diagnostics: list[str]) -> None:
    """Record the witnessed algorithm and select a sim recipe only where it accepts it."""
    if not isinstance(runtime, dict):
        return
    witness = witness_route_geometry(source)
    if not witness.get("opened"):
        return
    populations = list(witness.get("populations") or [])
    if witness.get("capped"):
        if populations or witness.get("orphan_collectives") or witness.get("expert_chain_without_route"):
            diagnostics.append("route_geometry_not_certified:witness_capped")
        return
    if not populations and not witness.get("orphan_collectives") and not witness.get("expert_chain_without_route"):
        return
    tp = runtime.get("tp") if isinstance(runtime.get("tp"), int) else None
    classified = []
    for population in populations:
        association = _match_frames(population, list(frames or []), tp)
        algorithm, reason = _classify(population, association)
        classified.append((population, association, algorithm, reason))
    algorithms = {item[2] for item in classified}
    reasons = [item[3] for item in classified if item[3]]
    if witness.get("orphan_collectives") and not populations:
        reasons.append("collectives_without_routing")
    if witness.get("expert_chain_without_route"):
        reasons.append("route_ops_absent")
    agreed = next(iter(algorithms)) if len(algorithms) == 1 else None
    if len(algorithms) > 1 or (populations and agreed is None):
        agreed = None
        if not reasons:
            reasons.append("populations_disagree")
    applied = None
    rejection = None
    if agreed == "expert_alltoallv":
        kernels = runtime.get("kernels")
        removed = {}
        if isinstance(kernels, dict) and "native_moe_protocol" in kernels:
            removed["native_moe_protocol"] = kernels.pop("native_moe_protocol")
        previous = runtime.get("moe_recipe")
        runtime["moe_recipe"] = "alltoall"
        transport_previous = None
        transport_declared = False
        if isinstance(kernels, dict) and _row_scale_int8(model) and _scale_dispatch_witnessed(classified):
            transport_previous = kernels.get("moe_transport")
            kernels["moe_transport"] = dict(_ROW_SCALE_TRANSPORT)
            transport_declared = True
            # The witnessed circuit is an unfused all-to-all: its local input is
            # direct TP rows, not the MC2 fused-token-slice annotation.  Keep the
            # token partition (and its reconstruction gather) but qualify it to
            # the all-to-all source, with no MC2 right-to-tp padding.
            partition = kernels.get("moe_token_partition")
            if isinstance(partition, dict) and partition.get("kind") == "vllm_ascend_mc2_tp_slice":
                partition = dict(partition)
                partition["kind"] = "vllm_ascend_alltoall_tp_slice"
                partition["padding"] = "none"
                kernels["moe_token_partition"] = partition
        if previous != "alltoall" or removed or transport_declared:
            record = {
                "moe_recipe": previous, "bound_moe_recipe": "alltoall",
                "removed_kernel_keys": removed, "reason": "witnessed_expert_alltoallv",
                "grouped_rows": sorted({item[0]["grouped_rows"] for item in classified}),
                "kept_kernel_keys": ["moe_token_partition"] if isinstance(kernels, dict) and "moe_token_partition" in kernels else [],
            }
            if transport_declared:
                record["moe_transport"] = transport_previous
                record["bound_moe_transport"] = dict(_ROW_SCALE_TRANSPORT)
                record["transport_width_basis"] = "layer_latent_times_dtype_bytes"
            replaced.append(record)
        applied = "alltoall"
        rows = ",".join(str(item) for item in sorted({item[0]["grouped_rows"] for item in classified}))
        diagnostics.append(f"route_geometry:expert_alltoallv:grouped_rows={rows}:native_fullmesh_removed")
        if transport_declared:
            diagnostics.append("route_geometry:expert_alltoallv:row_scale_dispatch:int8_fp32_bf16")
    elif agreed == "replicated_allreduce":
        rejection = _quant_rejection(model) or _parallel_rejection(runtime, model)
        rows = ",".join(str(item) for item in sorted({item[0]["grouped_rows"] for item in classified}))
        if rejection is None:
            kernels = runtime.get("kernels")
            removed = {}
            if isinstance(kernels, dict):
                for key in _DROPPED_KEYS:
                    if key in kernels:
                        removed[key] = kernels.pop(key)
            previous = runtime.get("moe_recipe")
            runtime["moe_recipe"] = "local_expert_reduce"
            grouped_m = "heaviest_contiguous_bank_not_packed_rows"
            if _quant_rejection(model) is None and _row_scale_int8(model):
                metadata = runtime.get("metadata") if isinstance(runtime.get("metadata"), dict) else {}
                metadata = dict(metadata)
                metadata["moe_grouped_gemm_rows"] = _FULL_EAGER_GROUPED
                runtime["metadata"] = metadata
                grouped_m = _FULL_EAGER_GROUPED
            replaced.append({
                "moe_recipe": previous, "bound_moe_recipe": "local_expert_reduce",
                "removed_kernel_keys": removed, "reason": "witnessed_replicated_allreduce",
                "grouped_rows": sorted({item[0]["grouped_rows"] for item in classified}),
                "grouped_gemm_m": grouped_m,
            })
            applied = "local_expert_reduce"
            diagnostics.append(f"route_geometry:replicated_allreduce:local_expert_reduce:grouped_rows={rows}")
            if grouped_m == _FULL_EAGER_GROUPED:
                diagnostics.append("route_geometry:grouped_gemm_m_is_full_eager_allocation")
            else:
                diagnostics.append("route_geometry:grouped_gemm_m_remains_heaviest_bank")
        else:
            diagnostics.append(f"route_geometry:replicated_allreduce_not_applied:{rejection}")
            diagnostics.append("route_geometry:grouped_gemm_m_remains_heaviest_bank")
    elif agreed == "local_no_route":
        ep = runtime.get("ep")
        if ep == 1:
            diagnostics.append("route_geometry:local_no_route:ep=1:recipe_unchanged")
        else:
            diagnostics.append(f"route_geometry:local_no_route_not_rewritten:declared_ep={ep}")
    elif reasons:
        diagnostics.append("route_geometry_not_certified:" + reasons[0])
    disproven = []
    for population, association, _algorithm, _reason in classified:
        divided = _ep_divided(population, association, runtime.get("ep"))
        if divided is not None and divided not in disproven:
            disproven.append(divided)
    public = {
        "algorithm": agreed, "applied_moe_recipe": applied, "rewritten": applied is not None,
        "reason": rejection or (reasons[0] if reasons else None),
        "populations": [
            _public_population(population, association, algorithm, reason)
            for population, association, algorithm, reason in classified
        ],
        "witness_rows_seen": int(witness.get("rows_seen") or 0),
        "witness_capped": False,
        "disproven_ep_divided_rows": sorted(disproven),
    }
    if agreed == "replicated_allreduce" and applied is None:
        public["sim_contract"] = _CONTRACT
        public["sim_grouped_gemm_m"] = "heaviest_contiguous_bank"
        public["sim_activation_rows_when_recipe_accepted"] = "tokens_times_topk"
    if isinstance(model, dict) and isinstance(model.get("metadata"), dict):
        model["metadata"]["route_geometry"] = public
