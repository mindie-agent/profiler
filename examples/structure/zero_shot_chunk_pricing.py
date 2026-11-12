"""Bounded chunk pricing through the canonical zero-shot model.

``predict_chunk`` prices one prefill chunk.  ``predict_chunk_batch`` prices one
admitted rank step as a single compiled WorkloadGeometry of per-request
records.  Neither function builds a prefix model or subtracts two whole-request
runs, and the batch total is not a sum or multiple of scalar chunk prices.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping, Sequence

import zero_shot_piecewise_validation as z


def _pp_chunk(spec: z.CellSpec, q_len: int, layers: int, hidden: int, rpn: int,
              links: Any, supply: Any, act_dtype: str):
    from dataclasses import replace as _replace
    from mindie_sim.prediction.piecewise.composition import p2p_transfer_cost
    from mindie_sim.schema.common import dtype_bytes
    rows = []
    total = 0.0
    cuts = max(0, min(spec.pp, layers) - 1)
    for stage in range(cuts):
        src = stage * max(1, spec.tp * spec.dp)
        dst = src + max(1, spec.tp * spec.dp)
        same_node = src // max(1, rpn) == dst // max(1, rpn)
        key = "link_hccs" if same_node else "link_roce"
        rate = supply.effective(key) if key in dict(supply.rates) else supply.effective("link")
        routed = _replace(supply, rates=tuple(sorted({**dict(supply.rates), "link": rate}.items())))
        latency = next((float(getattr(link, "latency_us", 0.0) or 0.0) / 1000.0
                        for link in links
                        if (("roce" if not same_node else "ub")
                            in f"{getattr(link, 'name', '')} {getattr(link, 'channel', '')}".lower())), 0.0)
        cost = p2p_transfer_cost(stage, q_len, hidden, dtype_bytes(act_dtype), routed)
        duration = float(cost.duration_ms) + latency
        total += duration
        rows.append(z.OperatorRow(
            f"pp_transfer:s{stage}->{dst}:chunk", "PP", "collective", "moe",
            duration, 1, cost.regime or (), cost.dominant_pipe,
            f"{cost.formula};{key};startup_ms={latency}", int(cost.segment_index), None))
    return total, tuple(rows)


def predict_chunk(spec: z.CellSpec, q_len: int, kv_end: int,
                  sequences: int = 1) -> z.Prediction:
    """Price one prefill chunk with q_len new tokens and absolute KV end.

    kv_end must be explicit.  The context is kv_end - q_len; the function never
    infers kv_end from q_len.  sequences must be exactly 1 for this interface.
    """
    q_len, kv_end, sequences = int(q_len), int(kv_end), int(sequences)
    if sequences != 1:
        raise ValueError(f"chunk_sequences_must_be_one:{sequences}")
    if q_len <= 0:
        raise ValueError(f"chunk_query_tokens_invalid:{q_len}")
    if kv_end <= 0 or kv_end < q_len:
        raise ValueError(f"chunk_kv_end_impossible:q={q_len}:kv_end={kv_end}")
    if spec.phase != "prefill":
        raise ValueError(f"chunk_phase_must_be_prefill:{spec.phase}")
    key = (spec.dataset, z._structure_fingerprint(spec))
    if key not in z._COMPILED_MODELS:
        z.predict_cell(spec)
    if key not in z._COMPILED_MODELS:
        raise ValueError("chunk_model_not_compiled")
    (layers, _notes, supply, unique, counts, state, features, hidden,
     rpn, links, act_dtype) = z._COMPILED_MODELS[key]
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry, ep_batch
    context = kv_end - q_len
    cohort = ep_batch(1, spec.dp, max(z._ep_ranks(spec), spec.dp))
    geometry = WorkloadGeometry(
        (RequestGeometry(q_len, context, phase="prefill", replica=0),),
        phase="prefill", cohort_batch=cohort, local_batch=1)
    cache_key = (key, "chunk", q_len, kv_end)
    if cache_key not in z._AGG_CACHE:
        if len(z._AGG_CACHE) >= 128:
            z._AGG_CACHE.clear()
        rows, body, per_layer, subgraphs = z._aggregate(
            unique, counts, geometry, state, [], features=features, supply=supply)
        dual = z._dual_moe(rows, supply, layers)
        rows = tuple(replace(row, cost=None) for row in rows)
        z._AGG_CACHE[cache_key] = (rows, body, per_layer, subgraphs, dual)
    rows, body, per_layer, subgraphs, dual = z._AGG_CACHE[cache_key]
    rows = tuple(rows)
    if spec.pp > 1:
        moved, pp_rows = _pp_chunk(spec, q_len, layers, hidden, rpn, links, supply, act_dtype)
        body += moved
        per_layer = dict(per_layer)
        per_layer["collective"] = per_layer.get("collective", 0.0) + moved
        rows += pp_rows
    pl = {k: v / layers for k, v in per_layer.items()}
    sg = {k: v / layers for k, v in subgraphs.items()}
    service = body + z._service_ttft_overhead_ms(spec, layers)
    notes = ("chunk_pricing:explicit_kv_end", f"chunk_q:{q_len}", f"chunk_kv_end:{kv_end}")
    return z.Prediction(spec.cell_id, spec.model_label, layers, pl, sg, body,
                        service, None, rows, notes, 0.0, body)


def _compiled(spec: z.CellSpec):
    key = (spec.dataset, z._structure_fingerprint(spec))
    if key not in z._COMPILED_MODELS:
        z.predict_cell(spec)
    if key not in z._COMPILED_MODELS:
        raise ValueError("chunk_model_not_compiled")
    return key, z._COMPILED_MODELS[key]


_BATCH_PHASES = {"prefill", "decode", "draft", "draft_prefill", "verify"}


def _declared_int(item: Mapping[str, Any], key: str, index: int) -> int | None:
    if key not in item or item[key] is None:
        return None
    value = item[key]
    if isinstance(value, bool):
        raise ValueError(f"chunk_batch_{key}_invalid:{index}")
    return int(value)


def _query_ranges(item: Mapping[str, Any], q_len: int, index: int) -> tuple[tuple[int, int], ...]:
    raw = item.get("query_ranges", ())
    if raw in (None, (), []):
        return ()
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise ValueError(f"chunk_batch_query_ranges_invalid:{index}")
    ranges = []
    for pair in raw:
        if isinstance(pair, (str, bytes)) or not isinstance(pair, Sequence) or len(pair) != 2:
            raise ValueError(f"chunk_batch_query_ranges_invalid:{index}")
        start, end = pair
        if isinstance(start, bool) or isinstance(end, bool):
            raise ValueError(f"chunk_batch_query_ranges_invalid:{index}")
        ranges.append((int(start), int(end)))
    if any(start < 0 or start > end or end > q_len for start, end in ranges):
        raise ValueError(f"chunk_batch_query_ranges_invalid:{index}:{q_len}")
    return tuple(ranges)


def _batch_records(requests: Sequence[Mapping[str, Any]], sequences: int) -> tuple[dict[str, Any], ...]:
    """One admitted step. ``sequences`` is per record, not a multiplier.

    A missing ``rank`` is a local lane whose physical rank was not declared.
    It is not an observation that the step ran on rank 0.
    """
    if sequences != 1:
        raise ValueError(f"chunk_batch_sequences_must_be_one:{sequences}")
    if isinstance(requests, (str, bytes)) or not isinstance(requests, Sequence) or not requests:
        raise ValueError("chunk_batch_requests_invalid")
    records = []
    ordinals: list[int] = []
    for index, item in enumerate(requests):
        if not isinstance(item, Mapping):
            raise ValueError(f"chunk_batch_request_invalid:{index}")
        seq = item.get("seq", 1)
        if isinstance(seq, bool) or int(seq) != 1:
            raise ValueError(f"chunk_batch_seq_must_be_one:{seq}")
        q_len, kv_end = item.get("q_len"), item.get("kv_end")
        if isinstance(q_len, bool) or isinstance(kv_end, bool):
            raise ValueError(f"chunk_batch_token_invalid:{index}")
        q_len, kv_end = int(q_len), int(kv_end)
        if q_len <= 0:
            raise ValueError(f"chunk_query_tokens_invalid:{q_len}")
        if kv_end <= 0 or kv_end < q_len:
            raise ValueError(f"chunk_kv_end_impossible:q={q_len}:kv_end={kv_end}")
        phase = str(item.get("phase") or "prefill")
        if phase not in _BATCH_PHASES:
            raise ValueError(f"chunk_batch_phase_invalid:{phase}")
        supplied = "rank" in item or "replica" in item
        rank = _declared_int(item, "rank", index) if "rank" in item else None
        if rank is None and "replica" in item:
            rank = _declared_int(item, "replica", index)
        if supplied and rank is None:
            raise ValueError(f"chunk_batch_rank_invalid:{index}")
        draft_len = _declared_int(item, "draft_len", index)
        if draft_len is None:
            draft_len = 1
        if draft_len < 0:
            raise ValueError(f"chunk_batch_draft_len_invalid:{index}")
        physical = _declared_int(item, "physical_tokens", index)
        if physical is not None and physical < 0:
            raise ValueError(f"chunk_batch_physical_tokens_invalid:{index}")
        ordinal = item.get("ordinal")
        if ordinal is not None:
            if isinstance(ordinal, bool):
                raise ValueError(f"chunk_batch_ordinal_invalid:{index}")
            ordinal = int(ordinal)
            if ordinal in ordinals:
                raise ValueError(f"chunk_batch_ordinal_repeated:{ordinal}")
            ordinals.append(ordinal)
        records.append({
            "ordinal": ordinal, "q_len": q_len, "prior_kv": kv_end - q_len,
            "kv_end": kv_end, "phase": phase, "rank": rank,
            "rank_role": "declared" if supplied else "local_lane_unspecified",
            "draft_len": draft_len, "query_ranges": _query_ranges(item, q_len, index),
            "physical_tokens": physical, "index": index,
        })
    roles = {item["rank_role"] for item in records}
    if len(roles) > 1:
        raise ValueError("chunk_batch_rank_partial")
    declared = [item["rank"] for item in records if item["rank_role"] == "declared"]
    if len(set(declared)) > 1:
        raise ValueError(f"chunk_batch_rank_not_single_lane:{sorted(set(declared))}")
    physical_flags = [item["physical_tokens"] is not None for item in records]
    if any(physical_flags) and not all(physical_flags):
        raise ValueError("chunk_batch_physical_tokens_partial")
    return tuple(records)


def predict_chunk_batch(spec: z.CellSpec, requests: Sequence[Mapping[str, Any]],
                        *, sequences: int = 1) -> dict[str, Any]:
    """Price one admitted batch from its real per-request query, prior KV, phase and rank.

    ``requests`` uses the P14/H3 BatchRequest keys ``ordinal, q_len, kv_end, phase, seq``.
    Optional ``rank`` is a declared lane.  When every item omits it, the step is
    one local lane whose physical rank is unspecified; the result rank is null,
    not observed rank 0.  Optional ``draft_len``, ``query_ranges`` and
    ``physical_tokens`` are kept on the compiled geometry.  ``sequences`` must
    be 1.  ``total_ms`` is the compiled joint body.
    """
    records = _batch_records(requests, int(sequences))
    key, (layers, _notes, supply, unique, counts, state, features, hidden,
          rpn, links, act_dtype) = _compiled(spec)
    from mindie_sim.prediction.piecewise import RequestGeometry, WorkloadGeometry
    geometry_requests = tuple(
        RequestGeometry(
            item["q_len"], item["prior_kv"], phase=item["phase"],
            query_ranges=item["query_ranges"],
            replica=0 if item["rank"] is None else item["rank"],
            draft_len=item["draft_len"])
        for item in records)
    phases = {item.phase for item in geometry_requests}
    phase = next(iter(phases)) if len(phases) == 1 else ""
    declared_physical = records[0]["physical_tokens"] is not None
    physical_tokens = sum(item["physical_tokens"] for item in records) if declared_physical else 0
    geometry = WorkloadGeometry(
        geometry_requests, phase=phase, cohort_batch=len(geometry_requests),
        local_batch=len(geometry_requests), physical_tokens=physical_tokens)
    query_tokens = sum(item.q_len for item in geometry_requests)
    if geometry.tokens != query_tokens:
        raise RuntimeError(f"chunk_batch_token_conservation:{geometry.tokens}!={query_tokens}")
    if declared_physical and geometry.physical_tokens != physical_tokens:
        raise RuntimeError(
            f"chunk_batch_physical_token_conservation:{geometry.physical_tokens}!={physical_tokens}")
    cache_token = tuple(
        (item["ordinal"], item["q_len"], item["prior_kv"], item["phase"], item["rank"],
         item["rank_role"], item["draft_len"], item["query_ranges"], item["physical_tokens"])
        for item in records)
    cache_key = (key, "chunk_batch", cache_token)
    if cache_key not in z._AGG_CACHE:
        if len(z._AGG_CACHE) >= 128:
            z._AGG_CACHE.clear()
        rows, body, per_layer, subgraphs = z._aggregate(
            unique, counts, geometry, state, [], features=features, supply=supply)
        rows = tuple(replace(row, cost=None) for row in rows)
        per_layer = dict(per_layer)
        pp_ms = 0.0
        if spec.pp > 1:
            pp_ms, pp_rows = _pp_chunk(
                spec, query_tokens, layers, hidden, rpn, links, supply, act_dtype)
            body += pp_ms
            per_layer["collective"] = per_layer.get("collective", 0.0) + pp_ms
            rows += pp_rows
        z._AGG_CACHE[cache_key] = (rows, body, per_layer, subgraphs, pp_ms)
    rows, body, per_layer, subgraphs, pp_ms = z._AGG_CACHE[cache_key]
    rows = tuple(rows)
    per_layer = dict(per_layer)
    weights = [item.pairs(causal=True) for item in geometry_requests]
    if sum(weights) <= 0:
        weights = [item.q_len for item in geometry_requests]
    weight_sum = float(sum(weights))
    per_request: dict[Any, float] = {}
    running = 0.0
    for index, (record, weight) in enumerate(zip(records, weights)):
        label = record["ordinal"] if record["ordinal"] is not None else f"background:{record['index']}"
        part = body - running if index == len(records) - 1 else body * weight / weight_sum
        running += part
        per_request[label] = part
    collective = float(per_layer.get("collective", 0.0))
    return {
        "total_ms": body,
        "per_request_ms": per_request,
        "rows": [{"name": row.name, "kind": row.kind, "mechanism": row.mechanism,
                  "subgraph": row.subgraph, "duration_ms": row.duration_ms, "count": row.count,
                  "total_ms": row.total_ms, "dominant_pipe": row.dominant_pipe, "formula": row.formula}
                 for row in rows],
        "scope": "single admitted batch",
        "tokens": query_tokens,
        "causal_pairs": geometry.pairs(causal=True),
        "s_sum": geometry.s_sum,
        "activated_layers": layers,
        "pp_ms": pp_ms,
        "collective_ms": collective,
        "request_count": len(records),
        "rank_role": records[0]["rank_role"],
        "physical_tokens": geometry.physical_tokens,
        "requests": [{
            "ordinal": record["ordinal"], "q_len": record["q_len"],
            "prior_kv": record["prior_kv"], "kv_end": record["kv_end"],
            "phase": record["phase"], "rank": record["rank"],
            "rank_role": record["rank_role"], "draft_len": record["draft_len"],
            "query_ranges": [list(pair) for pair in record["query_ranges"]],
            "physical_tokens": record["physical_tokens"],
        } for record in records],
        "per_layer": per_layer,
        "notes": ("chunk_batch:joint_workload_geometry",
                  "per_request_ms_attributes_joint_body_by_causal_pairs",
                  f"activated_layers:{layers}", f"query_tokens:{query_tokens}",
                  f"rank_role:{records[0]['rank_role']}",
                  "omitted_rank_is_local_lane_unspecified"),
    }
