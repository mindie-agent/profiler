"""Bounded window parsing, one-pass collection and compact contract aggregation.

[Role] Turn retained forward/layer spans into a bounded set of active scanner
  windows, stream one capture once, release each window's evidence after
  validation, and retain one compact contract per requested geometry.
[Invariants] Scanner state is allocated only for currently active windows.
  Repeated windows at one geometry must agree on caller family, declaration,
  transport and all deterministic layer contracts; the first conflict makes
  that geometry permanently unbound. Historical window IDs are reduced to an
  exact count plus bounded witnesses. Native row counts contribute only
  min/max summaries, never copied trace history.
[Timeouts & Locks] One bounded CSV pass and one bounded observation read; CSV,
  parser and TimeoutError failures propagate. No locks, subprocesses or devices.
[Side-Effect Policy] Read-only capture access. Returns compact mappings and
  provenance; source paths and hashes never enter the physical input.
"""
from __future__ import annotations

from bisect import bisect_right
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from mindie_profiler.normalized import kernel_rows

from capture_scoped_contracts import (
    ALLTOALL_TRANSPORT,
    COMM_ROLES,
    add_evidence,
    classify,
    frozen_layer,
    new_layer_evidence,
    projection,
    signature,
    validate_a3,
    validate_a5,
)


MAX_SCAN_ROWS = 2_000_000
SCAN_TIMEOUT_S = 30.0
MAX_LAYERS = 256
MAX_ACTIVE_WINDOWS = 16
MAX_OBSERVATION_BYTES = 32 * 1024 * 1024
MAX_GEOMETRY_CONTRACTS = 4096
MAX_WITNESSES = 4
OBSERVATION_SCHEMAS = frozenset({
    "mindie-prefill-body-observation/1",
    "mindie-scoped-structure-window/1",
})
TRANSPORT_FIELDS = frozenset({
    "kind", "dispatch_dtype", "payload_dtype", "scale_dtype",
    "scale_granularity", "histogram_dtype",
})
TRANSPORT_OPTION_FIELDS = frozenset({
    "layer_scopes", "mode", "deepep_overlap_ratio", "eplb_peak_to_avg",
    "ep_ratio", "ranks_per_node", "scale_group", "scale_Group",
})


@dataclass(frozen=True)
class _Span:
    layer_id: int
    start_ns: int
    end_ns: int
    first: int | None = None
    last: int | None = None


@dataclass(frozen=True)
class _Window:
    forward_id: str
    phase: str | None
    query_rows: int
    tokens: int
    sequences: int
    context: int | None
    start_ns: int
    end_ns: int
    first: int | None
    last: int | None
    layers: tuple[_Span, ...]


class _WindowEvidence:
    __slots__ = ("window", "layers", "unscoped", "line_mismatch", "overflow",
                 "comm_seen")

    def __init__(self, window):
        self.window = window
        self.layers = [new_layer_evidence() for _ in window.layers]
        self.unscoped = 0
        self.line_mismatch = 0
        self.overflow = False
        self.comm_seen = set()


def _positive(value):
    return value if type(value) is int and value > 0 else None


def _integer(value):
    return value if type(value) is int else None


def _file_identity(path):
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(path), "sha256": digest.hexdigest(),
            "size_bytes": Path(path).stat().st_size}


def _source_conflict(identity, declared):
    if not isinstance(declared, dict):
        return None
    if declared.get("sha256") and declared["sha256"] != identity["sha256"]:
        return {"status": "unsupported", "reason": "capture_source_hash_mismatch",
                "observed": identity["sha256"], "declared": declared["sha256"]}
    size = declared.get("size_bytes")
    if type(size) is int and size != identity["size_bytes"]:
        return {"status": "unsupported", "reason": "capture_source_size_mismatch"}
    return None


def _observation(value):
    if isinstance(value, (str, Path)):
        path = Path(value)
        if path.stat().st_size > MAX_OBSERVATION_BYTES:
            raise ValueError("scoped_observation_exceeds_bounded_read")
        data = path.read_bytes()
        document = json.loads(data)
        identity = {"path": str(path), "sha256": sha256(data).hexdigest(),
                    "size_bytes": len(data)}
    elif isinstance(value, dict):
        document, identity = value, None
    else:
        raise ValueError("scoped_observation_requires_mapping_or_path")
    observed = (document.get("observed")
                if isinstance(document.get("observed"), dict) else document)
    if (not isinstance(observed, dict)
            or not isinstance(observed.get("forwards"), list)):
        raise ValueError("scoped_observation_requires_forwards")
    schema = observed.get("schema_version") or document.get("schema_version")
    if schema not in OBSERVATION_SCHEMAS:
        raise ValueError("scoped_observation_schema_unsupported")
    source = observed.get("source_identity") or document.get("source_identity")
    return observed, identity, source if isinstance(source, dict) else None


def _lines(value):
    if not isinstance(value, dict):
        return None, None
    first = _positive(value.get("first_csv_line"))
    last = _positive(value.get("last_csv_line"))
    evidence = value.get("evidence") if isinstance(value.get("evidence"), dict) else {}
    if first is None:
        first = _positive((evidence.get("first_locator") or {}).get("csv_line"))
    if last is None:
        last = _positive((evidence.get("last_locator") or {}).get("csv_line"))
    return first, last


def _layers(value):
    layers = value.get("layers")
    if not isinstance(layers, list) or not layers or len(layers) > MAX_LAYERS:
        raise ValueError("scoped_forward_layers_malformed")
    result, seen = [], set()
    for item in layers:
        if not isinstance(item, dict):
            raise ValueError("scoped_layer_requires_object")
        layer_id = _integer(item.get("layer_id"))
        start = _positive(item.get("start_ns"))
        end = _positive(item.get("end_ns"))
        first, last = _lines(item)
        if (layer_id is None or layer_id < 0 or start is None or end is None
                or end <= start):
            raise ValueError("scoped_layer_span_malformed")
        if layer_id in seen:
            raise ValueError("scoped_layer_id_duplicate")
        if first is not None and last is not None and last < first:
            raise ValueError("scoped_layer_line_range_malformed")
        seen.add(layer_id)
        result.append(_Span(layer_id, start, end, first, last))
    result.sort(key=lambda span: (span.start_ns, span.layer_id))
    if any(cur.start_ns < prev.end_ns for prev, cur in zip(result, result[1:])):
        raise ValueError("scoped_layer_spans_overlap")
    return tuple(result)


def _parse_forwards(observed, *, context_offset=0):
    forwards, cursor = [], 0
    for index, item in enumerate(observed["forwards"]):
        if not isinstance(item, dict):
            raise ValueError("scoped_forward_requires_object")
        forward_id = item.get("forward_id") or "forward:" + str(index)
        phase = item.get("phase")
        rows = _positive(item.get("query_rows"))
        sequences = _positive(item.get("sequences", 1))
        if rows is None or sequences is None:
            raise ValueError("scoped_forward_geometry_malformed")
        tokens = item.get("tokens_per_sequence")
        if tokens is None:
            if rows % sequences:
                raise ValueError("scoped_forward_token_partition_malformed")
            tokens = rows // sequences
        tokens = _positive(tokens)
        if tokens is None or tokens * sequences != rows:
            raise ValueError("scoped_forward_token_partition_malformed")
        context = item.get("context", item.get("context_tokens"))
        if context is None:
            context = (context_offset + cursor) if phase == "prefill" else None
        elif _integer(context) is None or context < 0:
            raise ValueError("scoped_forward_context_malformed")
        if phase == "prefill":
            cursor = (context - context_offset + rows
                      if context >= context_offset else cursor + rows)
        body = item.get("body") if isinstance(item.get("body"), dict) else item
        start = _positive(body.get("start_ns"))
        end = _positive(body.get("end_ns"))
        first, last = _lines(body)
        spans = _layers(item)
        if start is None or end is None or end <= start:
            start = min(span.start_ns for span in spans)
            end = max(span.end_ns for span in spans)
        if any(not start <= span.start_ns <= span.end_ns <= end
               for span in spans):
            raise ValueError("scoped_layer_outside_forward")
        forwards.append(_Window(
            forward_id, phase, rows, tokens, sequences, context, start, end,
            first, last, spans))
    return forwards


def _locate(starts, spans, value):
    index = bisect_right(starts, value) - 1
    if index < 0:
        return None
    span = spans[index]
    return index if span.start_ns <= value <= span.end_ns else None


def _locate_line(line, starts, spans):
    index = bisect_right(starts, line) - 1
    if index < 0:
        return None
    span = spans[index]
    return index if span.first <= line <= span.last else None


def _family(layers):
    roles = set()
    for layer in layers:
        roles.update(layer.roles)
    if {"dispatch", "combine"} & roles:
        return "mc2"
    a3 = {"topk", "permute", "init_routing", "gate", "grouped",
          "unpermute", "alltoall", "allgather"} <= roles
    a5 = {"topk", "init_routing", "grouped", "swiglu", "finalize"} <= roles
    if a3 and a5:
        return "mixed"
    return "alltoall" if a3 else "local_expert" if a5 else "unknown"


def _contract_for_window(evidence, topology):
    if evidence.line_mismatch:
        return {"ok": False, "reason": "line_and_timestamp_boundaries_disagree",
                "row_count": evidence.line_mismatch}
    if evidence.overflow:
        return {"ok": False, "reason": "descriptor_variant_limit_exceeded"}
    if evidence.unscoped:
        return {"ok": False, "reason": "relevant_row_outside_layer_span"}
    window = evidence.window
    if len(window.layers) != topology["layers"]:
        return {"ok": False, "reason": "observed_layer_count_disagrees_with_model",
                "observed": len(window.layers), "model": topology["layers"]}
    if [span.layer_id for span in window.layers] != list(range(topology["layers"])):
        return {"ok": False, "reason": "observed_layer_ids_disagree_with_model"}
    layers = [frozen_layer(item) for item in evidence.layers]
    family = _family(layers)
    if family == "mc2":
        return {"ok": False, "reason": "existing_mc2_path_outside_scoped_adapter"}
    if family == "mixed":
        return {"ok": False, "reason": "mixed_scoped_native_callers"}
    if family == "alltoall":
        result = validate_a3(
            window, layers, tp=topology["tp"], ep=topology["ep"],
            hidden=topology["hidden_size"], experts=topology["num_experts"],
            top_k=topology["top_k"],
            intermediate=topology["moe_intermediate_size"])
    elif family == "local_expert":
        result = validate_a5(
            window, layers, tp=topology["tp"], ep=topology["ep"],
            hidden=topology["hidden_size"], experts=topology["num_experts"],
            top_k=topology["top_k"],
            intermediate=topology["moe_intermediate_size"],
            routing_policy=topology.get("routing"))
    else:
        return {"ok": False, "reason": "no_supported_scoped_caller"}
    if result.get("ok"):
        result["forward_id"] = window.forward_id
    return result


def _layer_signature(layer):
    return {key: value for key, value in layer.items()
            if key not in {"first_line", "native_gmm_rows",
                           "auxiliary_histogram_gathers"}}


def _contract_signature(analysis):
    return {
        "family": analysis["family"],
        "declaration": analysis["declaration"],
        "transport": analysis.get("transport"),
        "layers": [_layer_signature(layer) for layer in analysis["layers"]],
    }


def _merge_analysis(base, extra):
    if _contract_signature(base) != _contract_signature(extra):
        return None
    merged = deepcopy(base)
    if merged["family"] == "alltoall_tp_slice":
        merged["allocation"]["native_gmm_rows_min"] = min(
            merged["allocation"].get("native_gmm_rows_min",
                                     extra["allocation"]["native_gmm_rows_min"]),
            extra["allocation"]["native_gmm_rows_min"])
        merged["allocation"]["native_gmm_rows_max"] = max(
            merged["allocation"].get("native_gmm_rows_max",
                                     extra["allocation"]["native_gmm_rows_max"]),
            extra["allocation"]["native_gmm_rows_max"])
    return merged


def _merge_into(aggregate, contract, window):
    aggregate["window_count"] += 1
    if len(aggregate["witnesses"]) < MAX_WITNESSES:
        aggregate["witnesses"].append(window.forward_id)
    if aggregate["status"] != "ok":
        return
    if not contract.get("ok"):
        aggregate["status"] = "unbound"
        aggregate["reason"] = contract.get("reason", "unbound")
        aggregate["first_conflict"] = {
            "reason": aggregate["reason"],
            "forward_ids": list(aggregate["witnesses"]),
            "layer": contract.get("layer"),
            "role": contract.get("role"),
        }
        aggregate["analysis"] = None
        return
    if aggregate["analysis"] is None:
        aggregate["analysis"] = contract
        aggregate["primary_window"] = window
        return
    merged = _merge_analysis(aggregate["analysis"], contract)
    if merged is None:
        aggregate["status"] = "unbound"
        aggregate["reason"] = "repeated_window_contract_conflict"
        aggregate["first_conflict"] = {
            "reason": aggregate["reason"],
            "forward_ids": list(aggregate["witnesses"]),
            "field": "family/declaration/transport/layer-contract",
        }
        aggregate["analysis"] = None
        return
    aggregate["analysis"] = merged


def prepare_evidence(capture_path, observation, *, raw, context_offset=0,
                     max_rows=MAX_SCAN_ROWS, timeout_s=SCAN_TIMEOUT_S,
                     max_active_windows=MAX_ACTIVE_WINDOWS):
    """Stream one capture into compact per-geometry contracts."""
    capture = Path(capture_path)
    absent = {"path": str(capture), "sha256": None, "size_bytes": None}
    if not capture.is_file():
        return {"source_before": absent, "global_error": {
            "status": "not_provided", "reason": "capture_csv_not_present"}}
    try:
        observed, observation_identity, declared = _observation(observation)
    except FileNotFoundError:
        return {"source_before": absent, "global_error": {
            "status": "not_provided", "reason": "scoped_observation_not_present"}}
    except (ValueError, json.JSONDecodeError) as error:
        return {"source_before": absent, "global_error": {
            "status": "unsupported", "reason": "scoped_observation_malformed",
            "detail": str(error)}}
    source_before = _file_identity(capture)
    conflict = _source_conflict(source_before, declared)
    if conflict is not None:
        return {"source_before": source_before,
                "observation_identity": observation_identity,
                "declared_source": declared, "global_error": conflict}
    parsed, topology_error = _probe(raw)
    if parsed is None:
        return {"source_before": source_before,
                "observation_identity": observation_identity,
                "declared_source": declared,
                "global_error": {"status": "unsupported", **topology_error}}
    topology = _topology(parsed)
    topology_error = _topology_supported(topology)
    if topology_error is not None:
        return {"source_before": source_before,
                "observation_identity": observation_identity,
                "declared_source": declared, "topology": topology,
                "global_error": {"status": "unbound", "reason": topology_error}}
    try:
        windows = _parse_forwards(observed, context_offset=context_offset)
    except ValueError as error:
        return {"source_before": source_before,
                "observation_identity": observation_identity,
                "declared_source": declared, "topology": topology,
                "global_error": {"status": "unsupported",
                                 "reason": "scoped_window_malformed",
                                 "detail": str(error)}}
    if not windows:
        return {"source_before": source_before,
                "observation_identity": observation_identity,
                "declared_source": declared, "topology": topology,
                "global_error": {"status": "unbound",
                                 "reason": "scoped_observation_has_no_forward"}}
    contracts, scan = _scan_prepared(
        capture, windows, topology, max_rows=max_rows, timeout_s=timeout_s,
        max_active_windows=max_active_windows)
    source_after = _file_identity(capture)
    if (source_after["sha256"] != source_before["sha256"]
            or source_after["size_bytes"] != source_before["size_bytes"]):
        raise ValueError("capture_source_changed_during_scan")
    return {"source_before": source_before, "source_after": source_after,
            "observation_identity": observation_identity,
            "declared_source": declared, "topology": topology,
            "contracts": contracts, "scan": scan,
            "context_offset": context_offset}


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


def _topology_supported(topology):
    if (topology["tp"] < 2 or topology["dp"] != 1
            or topology["ep"] != topology["tp"] or topology["etp"] != 1
            or topology["pp"] != 1 or topology["cp"] != 1
            or topology["pcp"] != 1):
        return "parallelism_outside_supported_scoped_domain"
    if (topology["num_experts"] % topology["ep"]
            or topology["num_experts"] < 2 or topology["top_k"] < 1
            or topology["moe_intermediate_size"] < 1 or topology["layers"] < 1):
        return "model_moe_topology_not_supported"
    return None


def _scan_prepared(capture, windows, topology, *, max_rows, timeout_s,
                   max_active_windows):
    ordered = sorted(range(len(windows)), key=lambda index: windows[index].start_ns)
    starts = [windows[index].start_ns for index in ordered]
    evidence, active, next_index = {}, [], 0
    scanned, last_start = 0, None
    peak_active = peak_live = live = 0
    contracts, finished = {}, set()

    def admit(index):
        nonlocal live, peak_live
        evidence[index] = _WindowEvidence(windows[index])
        live += 1
        peak_live = max(peak_live, live)

    def record(index, contract):
        key = (windows[index].phase, windows[index].tokens,
               windows[index].sequences, windows[index].context,
               windows[index].query_rows)
        aggregate = contracts.setdefault(key, {
            "status": "ok", "reason": None, "analysis": None,
            "window_count": 0, "witnesses": [], "first_conflict": None,
            "primary_window": None,
        })
        _merge_into(aggregate, contract, windows[index])
        if len(contracts) > MAX_GEOMETRY_CONTRACTS:
            raise ValueError("scoped_geometry_contract_limit_exceeded")

    def finish(index):
        nonlocal live
        item = evidence.pop(index)
        live -= 1
        finished.add(index)
        record(index, _contract_for_window(item, topology))

    for row in kernel_rows(capture, max_rows=max_rows, timeout_s=timeout_s,
                           include_zero_duration=True):
        scanned += 1
        if last_start is not None and row.start_ns < last_start:
            raise ValueError("capture_rows_not_time_ordered")
        last_start = row.start_ns
        keep = []
        for index in active:
            if windows[index].end_ns < row.start_ns:
                finish(index)
            else:
                keep.append(index)
        active = keep
        while next_index < len(ordered) and starts[next_index] <= row.start_ns:
            index = ordered[next_index]
            next_index += 1
            if windows[index].end_ns < row.start_ns:
                if live < max_active_windows:
                    admit(index)
                    finish(index)
                else:
                    finished.add(index)
                    record(index, {"ok": False,
                                   "reason": "window_expired_before_evidence"})
                continue
            if len(active) >= max_active_windows:
                raise ValueError("scoped_active_window_limit_exceeded")
            active.append(index)
            admit(index)
            peak_active = max(peak_active, len(active))
        role = classify(row)
        if role is None:
            continue
        for index in active:
            window = windows[index]
            if not window.start_ns <= row.start_ns <= window.end_ns:
                continue
            item = evidence[index]
            if (row.line is not None and window.first is not None
                    and window.last is not None
                    and not window.first <= row.line <= window.last):
                item.line_mismatch += 1
                continue
            if (row.line is not None
                    and all(span.first is not None and span.last is not None
                            for span in window.layers)):
                layer_starts = [span.first for span in window.layers]
                layer_index = _locate_line(row.line, layer_starts, window.layers)
            else:
                layer_starts = [span.start_ns for span in window.layers]
                layer_index = _locate(layer_starts, window.layers, row.start_ns)
            if role in COMM_ROLES:
                device = getattr(row.event, "device_id", None)
                key = (role, row.name, row.kind, row.start_ns, row.stream, device)
                if key in item.comm_seen:
                    continue
                item.comm_seen.add(key)
            if layer_index is None:
                item.unscoped += 1
                continue
            add_evidence(
                item.layers[layer_index], role, signature(row),
                projection(row, role) if role in {"gate", "grouped"} else None,
                row.start_ns, row.line)
    for index in list(active):
        if index not in finished:
            finish(index)
    active.clear()
    for index in ordered:
        if index in finished:
            continue
        if index not in evidence:
            admit(index)
        finish(index)
    for aggregate in contracts.values():
        if aggregate["status"] != "ok":
            aggregate.pop("analysis", None)
            aggregate.pop("primary_window", None)
    return contracts, {
        "scanned_rows": scanned, "windows": len(windows),
        "active_window_cap": max_active_windows,
        "peak_active_windows": peak_active,
        "peak_live_evidence": peak_live, "retained_evidence": 0,
        "geometry_contracts": len(contracts),
    }


def transport_conflicts(existing):
    """Return concrete conflicts for an explicit transport declaration."""
    if existing is None:
        return []
    if not isinstance(existing, dict):
        return [{"field": "runtime.kernels.moe_transport", "value": existing,
                 "reason": "explicit_transport_not_mapping"}]
    unknown = set(existing) - TRANSPORT_FIELDS - TRANSPORT_OPTION_FIELDS
    if unknown:
        return [{"field": "runtime.kernels.moe_transport", "value": existing,
                 "reason": "explicit_transport_has_unexpected_fields"}]
    conflicts = []
    for field, value in ALLTOALL_TRANSPORT.items():
        if field in existing and existing[field] != value:
            conflicts.append({
                "field": "runtime.kernels.moe_transport." + field,
                "value": existing[field],
                "reason": "explicit_transport_incompatible"})
    if existing.get("mode", "alltoall") != "alltoall":
        conflicts.append({
            "field": "runtime.kernels.moe_transport.mode",
            "value": existing.get("mode"),
            "reason": "scoped_transport_requires_alltoall_mode"})
    if existing.get("deepep_overlap_ratio", 0.0) != 0.0:
        conflicts.append({
            "field": "runtime.kernels.moe_transport.deepep_overlap_ratio",
            "value": existing.get("deepep_overlap_ratio"),
            "reason": "scoped_transport_requires_deepep_disabled"})
    if existing.get("eplb_peak_to_avg", 1.0) != 1.0:
        conflicts.append({
            "field": "runtime.kernels.moe_transport.eplb_peak_to_avg",
            "value": existing.get("eplb_peak_to_avg"),
            "reason": "scoped_transport_requires_unity_eplb"})
    if existing.get("scale_group", existing.get("scale_Group", 0)) != 0:
        conflicts.append({
            "field": "runtime.kernels.moe_transport.scale_group",
            "value": existing.get("scale_group", existing.get("scale_Group")),
            "reason": "scoped_transport_requires_row_scale_group_zero"})
    scopes = existing.get("layer_scopes")
    if scopes is not None and (not isinstance(scopes, (list, tuple))
                               or "body" not in scopes):
        conflicts.append({
            "field": "runtime.kernels.moe_transport.layer_scopes",
            "value": scopes,
            "reason": "explicit_transport_scope_excludes_body"})
    return conflicts


def complete_transport(existing):
    result = dict(ALLTOALL_TRANSPORT)
    if isinstance(existing, dict):
        for field in TRANSPORT_FIELDS:
            if field in existing:
                result[field] = existing[field]
        for field in TRANSPORT_OPTION_FIELDS:
            if field in existing:
                result[field] = existing[field]
    return result
