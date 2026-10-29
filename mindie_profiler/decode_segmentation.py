"""Align complete device operator sequences to declared target-body topology.

[Role] Automatically segment Decode-like forwards using existing Sim layer plans.
[Invariants] Alignment is an explicitly labelled structural inference, not Host
  occurrence evidence. It requires the entire ordered layer plan and a vocabulary
  head closure; repeated kernel names alone never determine a layer. Device
  timestamps remain measured. Body spans exclude final norm/head/sampling and
  between-forward gaps, retain internal communication, and expose AICPU tails.
[Timeouts & Locks] One bounded chronological scan, one active segment per device;
  bounded result samples. No I/O, locks, model weights or device initialization.
[Side-Effect Policy] Pure local analysis. Does not change source events or Sim.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, is_dataclass
from math import prod

from .accounting import union_length
from .events import ProfilerUsageError
from .forward_spans import _statistics
from .normalized import shapes

_MATRICES = {"MatMul", "MatMulV2", "MatMulV3", "QuantBatchMatmulV3",
             "QuantBatchMatmulV4", "TransposeBatchMatMul", "BatchMatMulV2"}
_NORMS = {"RmsNorm", "GemmaRmsNorm", "AddRmsNorm", "AddRmsNormBias",
          "AddRmsNormDynamicQuant", "AddRmsNormDynamicMxQuant", "RmsNormQuant",
          "RmsNormDynamicQuant", "RmsNormDynamicMxQuant"}
_ACTIVATIONS = {"SwiGlu", "SwiGLU", "DequantSwigluQuant", "SwigluQuant",
                "GroupedMatmulSwigluQuant", "GroupedMatmulSwigluQuantV2",
                "GroupedMatmulSwigluQuantWeightNz", "MoeInitRoutingV3",
                "MoeTokenPermute", "MoeTokenPermuteWithRoutingMap",
                "GroupedMatmulSituQuant", "Sigmoid", "Tanh"}
_ANCHORS = {"RecurrentGatedDeltaRule": "gdn", "FusedInferAttentionScore": "gqa",
            "SparseFlashAttention": "mla", "SparseAttnSharedkv": "mla",
            "RecurrentKda": "kda", "RecurrentKdaFwd": "kda",
            "FusedRecurrentKda": "kda", "RecurrentGatedDeltaRuleV2": "gdn"}
_PREFILL_ANCHORS = {"ChunkGatedDeltaRuleFwd", "ChunkKdaFwd", "ChunkFwdH"}
_TAIL_NAMES = {"allreduceAicpuKernel", "allgatherAicpuKernel", "reducescatterAicpuKernel",
               "HcclLaunchAicpuKernel"}


@dataclass(slots=True)
class _Row:
    event: object
    inputs: tuple | None
    outputs: tuple | None

    @property
    def kind(self):
        return self.event.op_type


def _model(value):
    config = asdict(value) if is_dataclass(value) else dict(value)
    plans = config.get("layer_plans", ())
    plans = [asdict(plan) if is_dataclass(plan) else dict(plan) for plan in plans]
    plans = [plan for plan in plans if not plan.get("mtp", False)]
    if not plans:
        raise ProfilerUsageError("automatic forward segmentation requires existing Sim layer_plans")
    layers = int(config.get("body_layers") or config.get("layers") or len(plans))
    if len(plans) != layers:
        raise ProfilerUsageError("declared body layer count differs from existing layer_plans")
    config["layer_plans"] = plans
    config["tp"] = int(config.get("tp", 1))
    return config


def _norm(row, hidden):
    if row.kind == "AttnResFwd":
        # Kimi's attention-residual boundary replaces the ordinary hidden norm;
        # slots 2/3 are the declared hidden-width vectors, not a batch dimension.
        return (row.inputs is not None and len(row.inputs) == 6
                and row.inputs[2] == row.inputs[3] == (hidden,))
    return (row.kind in _NORMS and row.inputs and len(row.inputs[0]) >= 2
            and row.inputs[0][-1] == hidden)


def _head(row, config):
    if row.kind not in _MATRICES or not row.inputs or not row.outputs:
        return False
    x, y = row.inputs[0], row.outputs[0]
    vocab, tp = config["vocab_size"], config["tp"]
    # Explicit TP-sharded vocabulary ABI; arbitrary large matrices are not heads.
    widths = {vocab}
    if vocab % tp == 0:
        widths.add(vocab // tp)
    return len(x) == len(y) == 2 and x[-1] == config["hidden_size"] and y[-1] in widths


def _anchor(row, config):
    kind = _ANCHORS.get(row.kind)
    if kind is None or not row.inputs or not row.inputs[0]:
        return None
    # An FIA is GQA or MLA according to the independent model plan; the complete
    # sequence still has to match. Its name alone does not choose a layer.
    plan_kinds = {plan["attention"] for plan in config["layer_plans"]}
    if kind == "gqa" and "gqa" not in plan_kinds and "mla" in plan_kinds:
        kind = "mla"
    return kind


def _query_geometry(anchors, query_rows):
    batches = set()
    for row in anchors:
        inputs = row.inputs
        slot = None
        if row.kind == "FusedInferAttentionScore" and len(inputs) in {7, 31}:
            slot = inputs[6 if len(inputs) == 7 else 14]
        elif row.kind == "SparseFlashAttention" and len(inputs) == 9:
            slot = inputs[4]
        elif row.kind == "SparseAttnSharedkv" and len(inputs) == 14:
            slot = inputs[5]
        if slot and len(slot) == 2 and slot[0] > 0:
            batches.add(slot[0])
    batch = next(iter(batches)) if len(batches) == 1 else None
    q = query_rows // batch if batch and query_rows % batch == 0 else None
    return {"query_rows": query_rows, "sequences_per_replica": batch,
            "tokens_per_sequence": q, "context_tokens": None,
            "batch_basis": "captured_paged_attention_block_table_rows" if batch else None,
            "context_basis": "not_observed_from_cache_capacity"}


def _parameter_only(row, hidden):
    return row.kind == "Add" and row.inputs and row.inputs[0] == (hidden,)


def _norm_start(rows, index, hidden):
    # Gemma's 1 + gamma preparation is actual work of the following norm.
    return index - 1 if index and _parameter_only(rows[index - 1], hidden) else index


def _scope(rows, kind, identity, *, layer=None, plan=None, successor=None):
    def scheduler(row):
        typed = any("aicpu" in value.lower().replace("_", "")
                    for value in (row.event.core, row.event.task_type))
        return typed and row.kind in _TAIL_NAMES

    ordinary = [row for row in rows if not scheduler(row)]
    if not ordinary:
        return None
    first = min(row.event.start_ns for row in ordinary)
    last = max(row.event.end_ns for row in ordinary)
    tails = [row for row in rows if scheduler(row) and successor is not None
             and row.event.end_ns > successor.event.start_ns]
    retained_scheduler = [row for row in rows if scheduler(row) and row not in tails]
    if retained_scheduler:
        first = min(first, min(row.event.start_ns for row in retained_scheduler))
        last = max(last, max(row.event.end_ns for row in retained_scheduler))
    retained = ordinary + retained_scheduler
    first_endpoint = min(retained, key=lambda row: row.event.start_ns)
    last_endpoint = max(retained, key=lambda row: row.event.end_ns)
    last_started = max(retained, key=lambda row: row.event.start_ns)
    # A scheduler task must actually cross the successor's input boundary before
    # its suffix can be removed. AICPU completions inside the layer remain real
    # measured work; HCCL device task completions are never shortened.
    excluded = sum(max(0, row.event.end_ns - max(last, row.event.start_ns)) for row in tails)
    intervals = [(row.event.start_ns, row.event.end_ns) for row in ordinary]
    activity_ns = union_length(intervals)
    per_stream = defaultdict(list)
    for row in ordinary:
        per_stream[row.event.stream_id].append((row.event.start_ns, row.event.end_ns))
    return {"scope_id": identity, "kind": kind, "layer_id": layer,
            "rank_id": ordinary[0].event.rank_id, "device_id": ordinary[0].event.device_id,
            "replica": None, "stage": None, "status": "measured",
            "start_ns": first, "end_ns": last, "span_ms": (last - first) / 1e6,
            "device_activity_union_ms": activity_ns / 1e6,
            "internal_uncovered_gap_ms": (last - first - activity_ns) / 1e6,
            "activity_basis": "same_device_non_scheduler_interval_union_including_real_hcom",
            "activity_excluded_scheduler_event_count": len(rows) - len(ordinary),
            "per_stream_activity_ms": [{"stream_id": stream, "activity_union_ms": union_length(values) / 1e6}
                                       for stream, values in per_stream.items()],
            "event_count": len(rows), "attention": plan.get("attention") if plan else None,
            "span_start_basis": "first_retained_device_event_start",
            "span_end_basis": "last_retained_device_event_end",
            "excluded_tail_wait_activity_ms": excluded / 1e6,
            "excluded_tail_wait_events": len(tails),
            "aicpu_tail_policy": "clip_scheduler_tail_at_same_scope_real_device_completion",
            "evidence": {"basis": "structure_guided_topology_alignment",
                         "first_locator": first_endpoint.event.locator,
                         "last_locator": last_endpoint.event.locator,
                         "last_started_locator": last_started.event.locator,
                         "successor_boundary_start_ns": successor.event.start_ns if successor else None,
                         "successor_locator": successor.event.locator if successor else None}}


def _align(rows, config, ordinal):
    hidden, plans = config["hidden_size"], config["layer_plans"]
    anchors = [(index, _anchor(row, config)) for index, row in enumerate(rows)
               if _anchor(row, config) is not None]
    expected = [plan["attention"] for plan in plans]
    actual = [kind for _, kind in anchors]
    if any(row.kind in _PREFILL_ANCHORS for row in rows):
        return None, {"reason": "prefill_or_mixed_phase_sequence", "head_locator": rows[-1].event.locator}
    if len(actual) < len(expected):
        auxiliary = None
        if anchors:
            preceding = [index for index, row in enumerate(rows[:anchors[0][0]]) if _norm(row, hidden)]
            if preceding:
                start = _norm_start(rows, preceding[-1], hidden)
                auxiliary = _scope(rows[start:], "mtp_candidate", "auxiliary_candidate")
                auxiliary.update(query_rows=rows[-1].inputs[0][0], anchor_count=len(actual),
                                 identity_status="short_closed_subgraph_not_proven_mtp",
                                 mtp_declared=bool(config.get("auxiliary")),
                                 head_start_ns=rows[-1].event.start_ns,
                                 head_end_ns=rows[-1].event.end_ns)
        return None, {"reason": "auxiliary_or_partial_layer_sequence", "anchor_count": len(actual),
                      "expected_layers": len(expected), "head_locator": rows[-1].event.locator,
                      "auxiliary_candidate": auxiliary}
    if actual != expected:
        return None, {"reason": "ordered_layer_topology_mismatch", "anchor_count": len(actual),
                      "expected_layers": len(expected), "head_locator": rows[-1].event.locator}
    norm_indices = [index for index, row in enumerate(rows) if _norm(row, hidden)]
    starts, input_norms, previous_anchor = [], [], -1
    for anchor_index, _ in anchors:
        preceding = [index for index in norm_indices if previous_anchor < index < anchor_index]
        if not preceding:
            return None, {"reason": "layer_input_boundary_unresolved", "layer": len(starts)}
        input_norms.append(preceding[-1])
        starts.append(_norm_start(rows, preceding[-1], hidden))
        previous_anchor = anchor_index
    final_norms = [index for index in norm_indices if index > anchors[-1][0]]
    if len(final_norms) < 2:
        return None, {"reason": "final_norm_and_ffn_boundary_unresolved"}
    final_norm = _norm_start(rows, final_norms[-1], hidden)
    query_sizes = {prod(rows[index].inputs[0][:-1]) for index in input_norms
                   if rows[index].kind != "AttnResFwd"}
    if not query_sizes:
        # Flat AttnRes buffers also contain history/padding. Head query rows,
        # cross-checked with BSND KDA query slots, supply the token geometry.
        query_sizes.add(rows[-1].inputs[0][0])
        query_sizes.update(prod(rows[index].inputs[3][:2]) for index, _ in anchors
                           if rows[index].kind == "RecurrentKda"
                           and len(rows[index].inputs) > 3 and len(rows[index].inputs[3]) == 4)
    if len(query_sizes) != 1:
        return None, {"reason": "layer_query_geometry_changes", "query_rows": sorted(query_sizes)}
    query_rows = next(iter(query_sizes))
    geometry = _query_geometry([rows[index] for index, _ in anchors], query_rows)
    # Recurrent GDN/KDA anchors distinguish this path from chunk prefill; short
    # paged attention requires the declared decode query bound as another check.
    recurrent = any(kind in {"gdn", "kda"} for _, kind in anchors)
    if (not recurrent and (geometry["tokens_per_sequence"] is None
                           or geometry["tokens_per_sequence"] > config.get("max_decode_query", 16))):
        return None, {"reason": "decode_query_geometry_unresolved", "geometry": geometry}
    layers = []
    for layer, (start, end, (anchor_index, _), plan) in enumerate(zip(
            starts, [*starts[1:], final_norm], anchors, plans)):
        ffn_norms = [index for index in norm_indices if anchor_index < index < end]
        if not ffn_norms:
            return None, {"reason": "ffn_input_boundary_unresolved", "layer": layer}
        # Only activation/down-projection work after the FFN input boundary
        # qualifies. Attention output gates must not masquerade as an MLP.
        after_attention = rows[ffn_norms[0] + 1:end]
        activation_indices = [index for index, row in enumerate(after_attention)
                              if row.kind in _ACTIVATIONS or "Swiglu" in row.kind
                              or "SwiGlu" in row.kind]
        if not activation_indices:
            return None, {"reason": "ffn_completion_unverified", "layer": layer}
        following = after_attention[activation_indices[0] + 1:]
        returned_hidden = any(row.outputs and row.outputs[0] and row.outputs[0][-1] == hidden
                              and (row.kind in _MATRICES or row.kind.startswith("GroupedMatmul")
                                   or any(token in row.kind for token in ("Unpermute", "FinalizeRouting", "DistributeCombine")))
                              for row in following)
        if not returned_hidden:
            return None, {"reason": "ffn_output_hidden_contract_missing", "layer": layer}
        chunk = rows[start:end]
        layers.append(_scope(chunk, "moe_layer" if plan["ffn"] == "moe" else "dense_layer",
                             f"layer:{plan['index']}", layer=plan["index"], plan=plan,
                             successor=rows[input_norms[layer + 1] if layer + 1 < len(plans) else final_norms[-1]]))
    body = _scope(rows[starts[0]:final_norm], "target_body", "body",
                  successor=rows[final_norms[-1]])
    final = _scope(rows[final_norm:-1], "final_norm", "final_norm", successor=rows[-1])
    head = _scope(rows[-1:], "lm_head", "lm_head")
    embeddings = [row for row in rows[:starts[0]] if row.kind in {"Gather", "GatherV2", "Embedding", "IndexSelect"}
                  and row.inputs and row.outputs and len(row.outputs[0]) == 2
                  and row.outputs[0][-1] == hidden and any(
                      len(shape) == 2 and shape[-1] == hidden
                      and shape[0] in {config["vocab_size"], config["vocab_size"] // config["tp"]}
                      for shape in row.inputs)]
    embedding = _scope(embeddings, "embedding", "embedding") if embeddings else None
    stages = [embedding, body, *layers, final, head]
    return {
        "forward_id": f"auto:{ordinal}", "phase": "decode", "status": "measured",
        "basis": "structure_guided_topology_alignment",
        "body_forward_span_ms": body["span_ms"], "geometry": geometry,
        "body_activity_ms": body["device_activity_union_ms"],
        "body_internal_gap_ms": body["internal_uncovered_gap_ms"],
        "per_stream_activity_ms": body["per_stream_activity_ms"],
        "start_ns": body["start_ns"], "end_ns": body["end_ns"],
        "rank_id": body["rank_id"], "device_id": body["device_id"],
        "head_start_ns": head["start_ns"], "head_end_ns": head["end_ns"],
        "query_rows": query_rows, "stages": [item for item in stages if item is not None],
        "confidence": {"level": "conditional_structural_alignment",
                       "matched_layers": len(layers), "declared_layers": len(plans),
                       "ordered_attention_plan_matches": True,
                       "hidden_norm_boundaries_match": True, "ffn_path_present_each_layer": True,
                       "vocabulary_head_contract_matches": True,
                       "server_phase_marker_observed": False,
                       "phase_basis": "recurrent_attention" if recurrent else "short_paged_query",
                       "individual_layer_identity_is_inferred": True},
    }, None


def auto_segment_decode_forwards(events, model_config, *, source=None, max_events=5_000_000,
                                 max_forward_events=100_000, max_forwards=1024,
                                 max_anomalies=200, max_detailed_forwards=3,
                                 max_samples_per_layer=3, max_closed_segments=16_384,
                                 on_forward=None):
    """Align chronological Events against existing Sim ModelSpec/layer_plans.

    ``model_config`` is ModelSpec or its serialized dictionary, plus explicit
    ``tp`` for sharded vocabulary heads. No caller-created boundary JSON is
    required. Device streams share one active segment per (rank,device), closed
    by an independently declared vocabulary projection; shorter auxiliary/MTP
    segments cannot be promoted into a complete body. Unknown or corrupted
    sequences remain anomalies. The result measures conditional device spans,
    and does not assert Host-labelled forward or server-phase identity.
    ``on_forward(result, events)`` consumes each complete aligned segment before
    details are bounded; consumers must not mutate either argument or retain
    unbounded event history. The event tuple includes separate prefix/head work,
    so consumers select the measured body boundaries explicitly.
    """
    config = _model(model_config)
    active, previous = defaultdict(list), {}
    forwards, auxiliaries, auxiliary_values, anomalies, counts = [], [], [], [], Counter()
    auxiliary_occurrences = []
    reasons = Counter()
    per_layer, stages = {}, {}
    geometry_groups = {}

    def accumulate_stages(result):
        geometry = result["geometry"]
        geometry_key = (result["rank_id"], result["device_id"], geometry["query_rows"],
                        geometry["sequences_per_replica"], geometry["tokens_per_sequence"])
        geometry_group = geometry_groups.setdefault(geometry_key, {
            "geometry": geometry, "rank_id": result["rank_id"], "device_id": result["device_id"],
            "forward_ids": [], "values": [], "activity": [], "gaps": [],
            "streams": defaultdict(list), "layers": {}, "stages": {}})
        geometry_group["forward_ids"].append(result["forward_id"])
        geometry_group["values"].append(result["body_forward_span_ms"])
        geometry_group["activity"].append(result["body_activity_ms"])
        geometry_group["gaps"].append(result["body_internal_gap_ms"])
        for stream in result["per_stream_activity_ms"]:
            geometry_group["streams"][stream["stream_id"]].append(stream["activity_union_ms"])
        for stage in result["stages"]:
            if stage["kind"] == "target_body":
                continue
            key = (stage["kind"], stage["layer_id"], stage["rank_id"], stage["device_id"])
            values = per_layer if stage["layer_id"] is not None else stages
            group = values.setdefault(key, scope_values())
            append_scope(group, stage)
            if len(group["samples"]) < max_samples_per_layer:
                group["samples"].append({"forward_id": result["forward_id"], **stage})
            collection = geometry_group["layers" if stage["layer_id"] is not None else "stages"]
            append_scope(collection.setdefault(key, scope_values()), stage)

    def scope_values():
        return {"values": [], "activity": [], "gaps": [], "streams": defaultdict(list), "samples": []}

    def append_scope(group, stage):
        group["values"].append(stage["span_ms"])
        group["activity"].append(stage["device_activity_union_ms"])
        group["gaps"].append(stage["internal_uncovered_gap_ms"])
        for stream in stage["per_stream_activity_ms"]:
            group["streams"][stream["stream_id"]].append(stream["activity_union_ms"])

    def anomaly(value):
        reasons[value["reason"]] += 1
        if len(anomalies) < max_anomalies:
            anomalies.append(value)

    for index, item in enumerate(events, 1):
        if index > max_events:
            raise ProfilerUsageError(f"automatic forward scan exceeds {max_events} events")
        event = getattr(item, "event", item)
        counts["scanned_events"] += 1
        if event.duration_ns <= 0:
            continue
        counts["positive_events"] += 1
        key = (event.rank_id, event.device_id)
        if event.start_ns < previous.get(key, event.start_ns):
            raise ProfilerUsageError("automatic forward segmentation requires chronological device events")
        previous[key] = event.start_ns
        row = _Row(event, shapes(event.input_shapes), shapes(event.output_shapes))
        active[key].append(row)
        if sum(map(len, active.values())) > max_forward_events:
            raise ProfilerUsageError(f"active forward events exceed {max_forward_events}; no trustworthy head closure")
        if not _head(row, config):
            continue
        counts["vocabulary_head_occurrences"] += 1
        if counts["vocabulary_head_occurrences"] > max_closed_segments:
            raise ProfilerUsageError(f"closed forward segments exceed {max_closed_segments}")
        result, failure = _align(active[key], config, len(forwards))
        if result:
            result["closed_segment_event_count"] = len(active[key])
            counts["complete_body_segment_events"] += len(active[key])
            if on_forward is not None:
                on_forward(result, tuple(row.event for row in active[key]))
            accumulate_stages(result)
            result["stage_count"] = len(result["stages"])
            result["stage_details_retained"] = len(forwards) < max_detailed_forwards
            if not result["stage_details_retained"]:
                result["stages"] = []
            forwards.append(result)
            if len(forwards) > max_forwards:
                raise ProfilerUsageError(f"forward samples exceed {max_forwards}")
        else:
            auxiliary = failure.pop("auxiliary_candidate", None)
            if auxiliary:
                auxiliary_values.append(auxiliary["span_ms"])
                auxiliary_occurrences.append({name: auxiliary[name] for name in (
                    "start_ns", "end_ns", "head_start_ns", "head_end_ns", "device_id",
                    "rank_id", "span_ms", "query_rows", "anchor_count", "identity_status")})
                if len(auxiliaries) < max_anomalies:
                    auxiliaries.append({"candidate_id": f"auxiliary:{len(auxiliary_values) - 1}", **auxiliary})
                counts["auxiliary_candidate_segment_events"] += len(active[key])
            else:
                counts["rejected_segment_events"] += len(active[key])
            anomaly({**failure, "event_count": len(active[key]), "rank_id": key[0], "device_id": key[1]})
        active[key].clear()
    for key, rows in active.items():
        if rows:
            counts["trailing_segment_events"] += len(rows)
            anomaly({"reason": "trailing_segment_without_vocabulary_head", "event_count": len(rows),
                     "rank_id": key[0], "device_id": key[1]})
    def groups(values):
        return [{"kind": key[0], "layer_id": key[1], "rank_id": key[2], "device_id": key[3],
                 "replica": None, "stage": None, "stats": _statistics(group["values"]),
                 "activity_ms_stats": _statistics(group["activity"]),
                 "internal_gap_ms_stats": _statistics(group["gaps"]),
                 "per_stream_activity_ms": stream_stats(group["streams"]),
                 "sample_count": len(group["samples"]), "total_count": len(group["values"]),
                 "samples": group["samples"]} for key, group in values.items()]

    def stream_stats(streams):
        return [{"stream_id": stream, "stats": _statistics(values),
                 "additive_across_streams": False} for stream, values in streams.items()]

    geometries = [forward["geometry"] for forward in forwards]
    geometry = geometries[0] if geometries and all(value == geometries[0] for value in geometries) else None
    return {
        "schema_version": "mindie-forward-spans/1", "metric_boundary": "target_body_device_graph",
        "basis": "structure_guided_topology_alignment", "phase": "decode",
        "status": "measured" if forwards else "unresolved",
        "span_start_basis": "first_retained_device_event_start",
        "span_end_basis": "last_retained_device_event_end",
        "source_identity": source.content_identity() if source is not None else None,
        "geometry": geometry, "query_rows": geometry["query_rows"] if geometry else None,
        "model_declaration": {key: config.get(key) for key in ("name", "layers", "hidden_size", "vocab_size", "tp")},
        "body_forward_span_ms": _statistics([row["body_forward_span_ms"] for row in forwards]),
        "body_activity_ms": _statistics([row["body_activity_ms"] for row in forwards]),
        "body_internal_gap_ms": _statistics([row["body_internal_gap_ms"] for row in forwards]),
        "forwards": forwards, "per_layer_ms": groups(per_layer), "stage_span_ms": groups(stages),
        "auxiliary_forward_span_ms": _statistics(auxiliary_values),
        "auxiliary_candidates": auxiliaries,
        "auxiliary_occurrences": auxiliary_occurrences,
        "geometry_groups": [{"geometry": group["geometry"], "rank_id": group["rank_id"],
                             "device_id": group["device_id"], "forward_ids": group["forward_ids"],
                             "representative_forwards": [],
                             "body_forward_span_ms": _statistics(group["values"]),
                             "body_activity_ms": _statistics(group["activity"]),
                             "body_internal_gap_ms": _statistics(group["gaps"]),
                             "per_stream_activity_ms": stream_stats(group["streams"]),
                             "per_layer_ms": groups(group["layers"]),
                             "stage_span_ms": groups(group["stages"])}
                            for group in geometry_groups.values()],
        "scan_counts": dict(counts), "anomaly_counts": dict(reasons), "anomalies": anomalies,
        "limitations": ["Layer identity is inferred from complete declared topology, not observed Host scopes.",
                        "Decode phase uses recurrent/short-paged-query evidence; no server-phase marker is asserted.",
                        "AICPU scheduler suffixes beyond real device completion are excluded conditionally.",
                        "Internal device communication and gaps remain; stage spans are not additive.",
                        "Activity is the same-device union excluding typed AICPU scheduling wrappers; real HCOM is retained.",
                        "Internal uncovered gaps are not attributed to Host; per-stream activity cannot be summed across streams.",
                        "Cache tensor capacity does not reveal active context or prefix-cache hit rate."],
    }
