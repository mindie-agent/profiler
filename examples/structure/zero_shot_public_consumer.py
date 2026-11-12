"""Public compact-event consumer for the ordinary zero-shot forecast.

[Role] Turn one public ``graph_costs``/``body_forward`` compact profile into the
  published L1/L2/L3 rows and the canonical serving L4 boundaries.
[Invariants] One selected replica's own ready/complete/elapsed callbacks are
  used once; no private sum is added on top. Classification comes from the
  declared public family/recipe/fusion role, never a nearest private name.
[Side-Effect Policy] Pure arithmetic over an existing public result; the only
  external work is a canonical ``mindie_sim.prediction.api.predict`` call.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence


def _operator_row(*args: Any, **kwargs: Any) -> Any:
    try: from .zero_shot_piecewise_validation import OperatorRow
    except ImportError: from zero_shot_piecewise_validation import OperatorRow
    return OperatorRow(*args, **kwargs)


def _typed_metadata(value: Any) -> dict[str, Any]:
    """Normalise frozen ``Software.metadata`` pairs or an ordinary mapping."""
    if isinstance(value, Mapping):
        return dict(value)
    try:
        return {str(key): item for key, item in (value or ())}
    except (TypeError, ValueError):
        return {}


def public_supply_key(case: Any) -> str:
    """Stable identity of the resolved physical public intake.

    The typed Case carries its model/parallel/request/workload geometry, the
    actual hardware/topology, and the C7 ``Software.metadata`` as frozen pairs.
    Hash all relevant coordinates, not just a resource count, so a MAC-only and
    a MAC+MTE1 intake cannot collide and a changed request/model/topology cannot
    reuse a stale public graph/serving entry.
    """
    if case is None:
        return ""
    runtime = getattr(case, "runtime", None)
    metadata = _typed_metadata(getattr(runtime, "metadata", ()))
    kernels = _typed_metadata(getattr(runtime, "kernels", {}))
    supply = _typed_metadata(metadata.get("profiler_measured_supply"))
    regimes = kernels.get("service_regimes")
    model = getattr(case, "model", None)
    workload = getattr(case, "workload", None)
    machine = getattr(case, "machine", None)
    parallel = getattr(runtime, "parallel", None)
    requests = tuple(
        (str(getattr(req, "request_id", getattr(req, "id", ""))),
         int(getattr(req, "prompt_tokens", 0) or 0),
         int(getattr(req, "output_tokens", 0) or 0))
        for req in (getattr(workload, "requests", ()) or ()))
    links = tuple(str(item) for item in (getattr(machine, "links", ()) or ()))
    model_fields = {
        key: getattr(model, key, None) for key in
        ("name", "layers", "hidden_size", "num_heads", "head_dim",
         "intermediate_size", "num_experts", "top_k", "attention", "ffn",
         "moe_intermediate_size", "num_shared_experts", "body_layers")
    } if model is not None else {}
    payload = {
        "hardware": {key: getattr(machine, key, None) for key in
                     ("hardware_key", "sku", "arch_family")} if machine is not None else {},
        "model": model_fields,
        "layer_plans": tuple(str(item) for item in (getattr(model, "layer_plans", ()) or ())),
        "runtime_parallel": str(parallel) if parallel is not None else "",
        "requests": requests,
        "topology": links,
        "supply": supply,
        "service_regimes": regimes,
    }
    try:
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    except (TypeError, ValueError):
        return ""


def _resolved_public_case(spec: Any, *, case: Any = None) -> Any:
    if case is not None:
        return case
    try: from .zero_shot_piecewise_validation import _public_case
    except ImportError: from zero_shot_piecewise_validation import _public_case
    return _public_case(spec)


def _policy_sequences(spec: Any) -> tuple[int, ...]:
    dp = max(1, int(spec.dp or 1)); count = max(1, int(spec.concurrency or 1))
    out = [0] * dp
    for index in range(count): out[index % dp] += 1
    return tuple(out)


def _public_graph_projection(case: Any, *, phase: str, tokens: int, context: int,
                             sequences: Sequence[int], selected_replica: int,
                             scope: str = 'model') -> dict[str, Any]:
    """Read one public target_graphs/body_forward → graph_costs compact result.

    Every declared operator occurrence of the selected replica is retained; the
    compact profile already carries the same ready/complete/elapsed boundary.
    No private estimator is assembled around this result.
    """
    if str(scope) == 'body':
        from mindie_sim.prediction.body import body_forward
        result = body_forward(case, phase=phase, tokens=int(tokens), context=int(context),
                              sequences=list(sequences), compact=True)
    else:
        from mindie_sim.prediction.operator_analysis import target_graphs
        from mindie_sim.prediction.graph_analysis import graph_costs
        graphs = target_graphs(case, phase=phase, tokens=int(tokens), context=int(context),
                               sequences=list(sequences), scope='model')
        result = graph_costs(case, graphs, isolated=False, compact=True,
                             trace_limit=0, external_inputs={'analysis_input': 0})
    profile = dict(result.get('profile') or {})
    by_operator = profile.get('by_operator') or {}
    selected = str(selected_replica)
    operators = {}
    for key, stats in by_operator.items():
        replicas = stats.get('replicas') or {}
        item = replicas.get(selected) or replicas.get(int(selected_replica))
        if item is None:
            continue
        raw_op = str(stats.get('op_id') or '')
        operators[key] = {
            'status': 'present', 'identity': key, 'op_id': raw_op,
            'family': item.get('family'), 'stage': stats.get('stage'),
            'replica': int(selected_replica), 'layer': item.get('layer'),
            'phase': item.get('phase'), 'stream': item.get('stream'),
            'recipe': item.get('recipe'), 'program': item.get('program'),
            'source_boundary': item.get('source_boundary'),
            'ready_ms': item.get('ready_ms'), 'complete_ms': item.get('complete_ms'),
            'elapsed_ms': item.get('elapsed_ms'),
            'operator_events': int(item.get('operator_events') or 0),
            'native_call': item.get('native_call'),
            'native_kind': item.get('native_kind') or ((item.get('matrix_wrapper') or {}).get('native_kind')
                                                       if isinstance(item.get('matrix_wrapper'), Mapping) else None),
            'matrix_wrapper': dict(item['matrix_wrapper']) if isinstance(item.get('matrix_wrapper'), Mapping) else None,
            'fusion_role': item.get('fusion_role'),
            'fusion_group_key': item.get('fusion_group_key'),
            'native_implementation': item.get('native_implementation'),
            'physical_source_program': item.get('physical_source_program'),
            'native_local_ready_ms': item.get('native_local_ready_ms'),
            'local_ready_ms': item.get('local_ready_ms'),
            'rendezvous_wait_ms': item.get('rendezvous_wait_ms'),
            'rendezvous_events': item.get('rendezvous_events'),
            **{key: item[key] for key in ('grouping_kind', 'grouping_scope', 'routed_expert',
                                         'source_caller', 'source_caller_lines', 'source_caller_sha256',
                                         'source_image_sha256', 'source_basis')
               if item.get(key) is not None},
        }
    steps = profile.get('steps_by_replica') or {}
    step = steps.get(selected) or steps.get(int(selected_replica))
    native = dict(profile.get('native_bridge') or {})
    return {'schema': 'f17j-public-graph-consumer/1', 'scope': str(scope),
            'duration_ms': result.get('duration_ms') or result.get('body_forward_ms'),
            'input_ready_ms': result.get('input_ready_ms'),
            'complete_ms': result.get('complete_ms'),
            'selected_replica': int(selected_replica),
            'operator_events': int(profile.get('operator_events') or sum(
                int(item.get('operator_events') or 0) for item in operators.values())),
            'by_family': {str(name): dict(value) for name, value in (profile.get('by_family') or {}).items()},
            'operators': operators, 'step': step, 'native_bridge': native,
            'steps_source': 'profile.steps_by_replica' if step is not None else None,
            'public_result': 'mindie_sim.graph_costs compact profile'}


_PUBLIC_CACHE: dict[Any, Any] = {}
# Authoritative public op.family -> ordinary physical mechanism.  This is the
# simulator's declared family vocabulary, not a model/case-name table and not a
# nearest private-row label.
_PUBLIC_FAMILY_MECHANISM = {
    'gemm': 'gemm', 'prepared_mx32_aic_matrix': 'gemm', 'steady_matmul': 'gemm',
    'logits': 'gemm', 'down_projection': 'gemm', 'gate_up_projection': 'gemm',
    'mx_matrix': 'gemm', 'grouped_gemm': 'moe_grouped', 'swiglu': 'activation',
    'collective': 'collective', 'transport': 'collective', 'mc2_protocol': 'collective',
    'allgather': 'collective', 'reduce_scatter': 'collective', 'allreduce': 'collective',
    'recurrent_scan': 'gdn_kda',
    'mc2_transport': 'collective', 'alltoallv': 'collective',
    'mla': 'attention', 'attention': 'attention', 'indexer': 'indexer',
    'rmsnorm': 'norm_residual', 'layernorm': 'norm_residual',
    'cast': 'elementwise_quant', 'quantize': 'elementwise_quant',
    'elementwise': 'elementwise_quant', 'copy': 'elementwise_quant',
    'rotary': 'rope', 'cache_store': 'kv_cache', 'kv_access': 'kv_cache',
    'compression': 'kv_cache', 'hyper_connection': 'hyperconnection',
    'hc_post': 'hyperconnection', 'engram_gate': 'gemm', 'engram_apply': 'activation',
}
_PUBLIC_ATTENTION = {'attention', 'indexer', 'kv_cache', 'rope', 'gdn_kda'}
_PUBLIC_MOE = {'moe_grouped', 'moe_router', 'activation'}


def _public_leaf(identity: str) -> str:
    leaf = str(identity).split(':', 1)[-1]
    return re.sub(r'^s\d+\.l\d+\.', '', leaf)


def _public_native_kind(item: Mapping[str, Any]) -> str:
    implementation = item.get('native_implementation')
    if isinstance(implementation, Mapping) and implementation.get('native_kind'):
        return str(implementation.get('native_kind'))
    if isinstance(implementation, str): return implementation
    wrapper = item.get('matrix_wrapper')
    if isinstance(wrapper, Mapping) and wrapper.get('native_kind'):
        return str(wrapper.get('native_kind'))
    return str(item.get('native_kind') or '')


def _public_mechanism(item: Mapping[str, Any], leaf: str,
                      index: Mapping[str, Any]) -> tuple[str, str, str, Any | None]:
    """Resolve one public lowered op from its declared source semantics."""
    family = str(item.get('family') or '').lower()
    role = str(item.get('fusion_role') or '').lower()
    native = _public_native_kind(item).lower()
    program = str(item.get('physical_source_program') or '').lower()
    text = f'{role} {native} {program}'
    if family == 'native_fusion':
        if any(token in text for token in ('hc_pre', 'hcpost', 'hc_post', 'hcpre')):
            mechanism = 'hyperconnection'
        elif 'grouped_gate_up_situ_quant' in text or 'groupedmatmul' in text:
            mechanism = 'moe_grouped'
        else:
            mechanism = 'unclassified'
    elif (family == 'projection' and 'groupedmatmul' in native
          and (str(item.get('recipe') or '') == 'latent_projection'
               or 'latent' in str(item.get('grouping_scope') or '').lower())):
        # GMMK3A: one-group non-routed latent MoE projection is physically a
        # grouped GEMM.  Keep the non-routed source role, never F3/expert.
        mechanism = 'moe_grouped'
    elif family == 'router':
        # F1 router_gemm is a GEMM (feedforward.py gemm_op), not MoE top-k.
        mechanism = 'gemm' if 'router' in str(item.get('recipe') or '') or 'steadymatmul' in str(item.get('program') or '').lower() else 'moe_router'
    elif family == 'topk':
        # MLA/indexer top-k is the frozen indexer; router_topk remains MoE routing.
        topk_text = f"{item.get('recipe')} {leaf} {item.get('op_id')} {item.get('program')}".lower()
        mechanism = 'indexer' if 'index' in topk_text else 'moe_router'
    elif family == 'elementwise' and str(item.get('recipe') or '') == 'expert_add':
        # Source feedforward.py join: two selected BF16 tensors are combined by
        # the caller's ForeachAddList path, which the frozen _CLASS_RULES price
        # as norm_residual.  Other elementwise recipes (e.g. R64 muls_add) stay
        # distinct and are not guessed into this bucket.
        mechanism = 'norm_residual'
    else:
        mechanism = _PUBLIC_FAMILY_MECHANISM.get(family, 'unclassified')
    if mechanism == 'collective' and family not in {'mc2_protocol', 'mc2_transport', 'alltoallv'}:
        subgraph = ''
    elif mechanism in _PUBLIC_ATTENTION: subgraph = 'attention'
    elif mechanism in _PUBLIC_MOE: subgraph = 'moe'
    elif mechanism == 'norm_residual': subgraph = 'norm_residual'
    elif mechanism == 'hyperconnection': subgraph = 'hyperconnection'
    elif mechanism == 'collective' and family in {'mc2_protocol', 'mc2_transport', 'alltoallv'}: subgraph = 'moe'
    else: subgraph = ''
    kind = {'grouped_gemm': 'F3', 'router': 'F1', 'topk': 'F1', 'swiglu': 'F4',
            'rmsnorm': 'N0', 'layernorm': 'N0', 'native_fusion': 'R0',
            'mc2_protocol': 'F2', 'mc2_transport': 'F2'}.get(family, '')
    if family == 'native_fusion' and mechanism == 'moe_grouped': kind = 'F3'
    owner = index.get(leaf.replace('.', '_'))
    return mechanism, subgraph, kind, owner


def _subgraph_charge(family: str, mechanism: str, kind: str) -> bool:
    """The one enrolled L2 membership rule shared by public and private rows.

    ``measured_subgraph_us`` prices attention as attention/rope/kv/index/gdn and
    MoE as grouped/router/activation (+ EP collective); GEMM, quantize and other
    vector work stay in L1 only.  Norm/hyper subgraphs own only their class.
    """
    if not family: return False
    if family == 'attention': return mechanism in _PUBLIC_ATTENTION
    if family == 'moe': return mechanism in _PUBLIC_MOE or (mechanism == 'collective' and kind not in {'F0', 'F4'})
    if family in {'norm_residual', 'hyperconnection'}: return mechanism == family
    return False


def _public_consume(projection: Mapping[str, Any], base_rows: Sequence[Any], *,
                    layers: int, basis: str) -> dict[str, Any] | None:
    """Publish public compact operator events as the ordinary forecast rows.

    The selected replica's own ready/complete/elapsed callback boundaries are
    used once.  The completed step parent comes from ``steps_by_replica``; no
    private per-layer sum is added on top of these events.  Only an exact source
    owner row may lend typed native metadata; classification is never taken from
    a nearest private name.
    """
    operators = projection.get('operators') or {}
    if not operators or layers <= 0: return None
    index = {row.name.replace('.', '_'): row for row in base_rows}
    rows = []; per_layer = defaultdict(float); subgraphs = defaultdict(float)
    for identity, item in operators.items():
        elapsed = float(item.get('elapsed_ms') or 0.0)
        events = int(item.get('operator_events') or 0)
        if not (math.isfinite(elapsed) and elapsed > 0.0 and events > 0): continue
        leaf = _public_leaf(identity)
        mechanism, subgraph, kind, owner = _public_mechanism(item, leaf, index)
        duration = elapsed / events
        native_call = item.get('native_call')
        if native_call is None and owner is not None and owner.mechanism == mechanism and owner.subgraph == subgraph:
            native_call = owner.native_call
        family = str(item.get('family') or '')
        semantic_role = ('nonrouted_latent_moe_one_group' if family == 'projection' and mechanism == 'moe_grouped'
                         else 'routed_expert_gate_up' if family == 'native_fusion' and mechanism == 'moe_grouped'
                         else str(item.get('fusion_role') or ''))
        occurrence = {'identity': identity, 'op_id': str(item.get('op_id') or ''),
                      'family': item.get('family'), 'stage': item.get('stage'), 'replica': item.get('replica'),
                      'layer': item.get('layer'), 'phase': item.get('phase'), 'stream': item.get('stream'),
                      'recipe': item.get('recipe'), 'program': item.get('program'),
                      'source_boundary': item.get('source_boundary'),
                      'operator_events': events, 'ready_ms': item.get('ready_ms'),
                      'complete_ms': item.get('complete_ms'), 'elapsed_ms': elapsed,
                      'per_occurrence_ms': duration, 'basis': basis,
                      'charge': 'public_event', 'timing_owner': leaf,
                      'membership': 'public_lowered_event',
                      'native': str(item.get('family') or '') == 'mc2_transport',
                      'split_phase': str(item.get('family') or '') in {'mc2_protocol', 'alltoallv'},
                      'classification': mechanism, 'source_role': semantic_role,
                      'routed_expert': semantic_role == 'routed_expert_gate_up',
                      'native_projection_kind': _public_native_kind(item) if family == 'projection' else '',
                      'source_basis': str(item.get('source_basis') or '')}
        for key in ('native_local_ready_ms', 'local_ready_ms', 'rendezvous_wait_ms', 'rendezvous_events',
                    'native_kind', 'fusion_role', 'fusion_group_key', 'native_implementation',
                    'physical_source_program', 'matrix_wrapper'):
            if item.get(key) is not None: occurrence[key] = item[key]
        if owner is not None and owner.mechanism == mechanism and owner.subgraph == subgraph:
            occurrence['source_owner'] = owner.name
        row = _operator_row(leaf, kind, mechanism, subgraph, duration, events, (),
                          str(item.get('recipe') or item.get('program') or item.get('family') or 'public'),
                          f'public:{identity};{basis}', int(item.get('stage') or 0), None,
                          native_call=native_call, native_occurrence=occurrence,
                          phase=str(item.get('phase') or ''))
        rows.append(row); per_layer[mechanism] += row.total_ms / layers
        if subgraph and _subgraph_charge(subgraph, mechanism, kind): subgraphs[subgraph] += row.total_ms / layers
    if not rows: return None
    step = dict(projection.get('step') or {})
    start = float(step.get('start_ms') or 0.0)
    device_end = float(step.get('device_end_ms') or projection.get('duration_ms') or 0.0)
    end = float(step.get('end_ms') or device_end)
    return {'rows': tuple(rows), 'per_layer': dict(per_layer), 'subgraphs': dict(subgraphs),
            'body_ms': max(0.0, device_end - start), 'step_ms': max(0.0, end - start),
            'operator_events': sum(row.count for row in rows), 'basis': basis}

def _selected_moe_comm(spec: Any, features: Any, *, top_k: int, experts: int, ep: int) -> str:
    """PCOM27S canonical effective MC2 selector on the normalized feature record."""
    from mindie_sim.prediction.moe_comm_selection import MoeCommConfig, local_tokens
    try: from .zero_shot_piecewise_validation import _geometry, _raw_case
    except ImportError: from zero_shot_piecewise_validation import _geometry, _raw_case
    kernels = ((_raw_case(spec).get('runtime') or {}).get('kernels') or {})
    if kernels.get('native_moe_protocol'): return 'mc2'
    config = MoeCommConfig.from_features(features, ep=max(1, ep), top_k=max(1, top_k), experts=max(1, experts))
    return '' if config is None else config.select(local_tokens(_geometry(spec, spec.phase)))


def _public_request_placement(spec: Any, group: Mapping[str, Any] | None) -> tuple[tuple[int, ...], str]:
    """Declared source vector when complete, otherwise the model's declared policy."""
    expected = int((group or {}).get('expected_membership') or max(1, spec.dp))
    active = (group or {}).get('active_counts')
    if isinstance(active, Sequence) and not isinstance(active, (str, bytes)) and len(active) == expected:
        return tuple(int(v) for v in active), 'observed_active_vector'
    exact = [item for item in (group or {}).get('source_conditions') or ()
             if len(item.get('sequences') or ()) == expected]
    if len(exact) == 1:
        return tuple(int(v) for v in exact[0]['sequences']), f"source_declared_condition:{exact[0].get('name')}"
    return tuple(_policy_sequences(spec)), 'expected_index_mod_dp'


def _public_selected_replica(group: Mapping[str, Any] | None) -> tuple[int, str]:
    # Forecast uses the source-declared representative rank.  Observed rank
    # folders belong to post-forecast attribution/comparison only.
    return int((group or {}).get('selected_rank') or 0), 'source_declared_rank_representative'


def _serving_case(spec: Any, *, case: Any = None) -> Any:
    """Same resolved source case with the original request population."""
    from mindie_sim.schema.model import RequestSpec, WorkloadSpec
    case = _resolved_public_case(spec, case=case)
    prompt = max(1, int(spec.prompt_tokens)); output = max(1, int(spec.max_tokens)); count = max(1, int(spec.concurrency))
    requests = tuple(RequestSpec(f'original-r{i}', 0.0, prompt, output) for i in range(count))
    return replace(case, workload=WorkloadSpec(requests, synthetic=False))


def _serving_projection(spec: Any, cache_key: Any, *, runner: Any = None,
                        case: Any = None) -> dict[str, Any]:
    """Canonical serving projection from the ordinary public API.

    The default is the real ``mindie_sim.prediction.api.predict`` burst on the
    same resolved source case and original request population.  ``runner`` is a
    focused test seam only; it must return the same public predict shape.
    """
    intake = public_supply_key(case)
    key = (cache_key, 'serving', spec.phase, spec.prompt_tokens, spec.concurrency, spec.max_tokens, intake)
    if key in _PUBLIC_CACHE: return dict(_PUBLIC_CACHE[key])
    record = {'status': 'not_started', 'ttft_ms': None, 'tpot_ms': None, 'boundary': '',
              'residual': '', 'served': None, 'total': None,
              'execution_status': '', 'request_statuses': {}}
    try:
        if runner is not None:
            result = runner(_serving_case(spec, case=case))
        else:
            from mindie_sim.prediction.api import predict
            result = predict(_serving_case(spec, case=case), scope='serving', trace_limit=0, event_limit=0)
        status = str(result.get('status') or 'unknown')
        rows = result.get('requests') or ()
        served = sum(1 for row in rows if isinstance(row, Mapping) and row.get('status') == 'served')
        request_statuses = {}
        for row in rows:
            key_status = str(row.get('status') or 'unknown') if isinstance(row, Mapping) else 'unknown'
            request_statuses[key_status] = request_statuses.get(key_status, 0) + 1
        record.update(status=status, served=served, total=len(rows),
                      execution_status=str(result.get('execution_status') or ''),
                      request_statuses=request_statuses)
        boundaries = result.get('metric_boundaries') or {}
        boundary_name = next((name for name in ('client_delivery', 'host_result_ready', 'device_token_commit')
                              if name in boundaries), '')
        residual = '' if boundary_name == 'client_delivery' else ('residual_delivery_unavailable' if boundary_name else '')
        metrics = boundaries.get(boundary_name) or {}
        ttft = (metrics.get('ttft_ms') or {}).get('mean'); tpot = (metrics.get('tpot_ms') or {}).get('mean')
        if status != 'modeled' or served != len(rows) or not rows:
            record['basis'] = f'serving_status_not_modeled:{status}:{served}/{len(rows)}'
            return dict(record)
        if not (isinstance(ttft, (int, float)) and math.isfinite(float(ttft))): ttft = None
        if not (isinstance(tpot, (int, float)) and math.isfinite(float(tpot))): tpot = None
        record.update(ttft_ms=None if ttft is None else float(ttft),
                      tpot_ms=None if tpot is None else float(tpot),
                      boundary=boundary_name, residual=residual,
                      basis=f'serving:{boundary_name}' + (f';{residual}' if residual else ''))
        if record['ttft_ms'] is not None or record['tpot_ms'] is not None:
            if len(_PUBLIC_CACHE) >= 8: _PUBLIC_CACHE.pop(next(iter(_PUBLIC_CACHE)))
            _PUBLIC_CACHE[key] = dict(record)
    except TimeoutError:
        raise
    except Exception as error:
        record['basis'] = f'serving_unavailable:{type(error).__name__}:{error}'
    return dict(record)


def _serving_l4(spec: Any, cache_key: Any, *, runner: Any = None,
                case: Any = None) -> dict[str, Any]:
    """L4 serving scalar without exposing measured field names to the predictor."""
    record = _serving_projection(spec, cache_key, runner=runner, case=case)
    return {'body_ms': record.get('tpot_ms'), 'service_ms': record.get('ttft_ms'),
            'basis': record.get('basis') or 'serving_unavailable', 'status': record.get('status'),
            'served': record.get('served'), 'total': record.get('total'),
            'boundary': record.get('boundary'), 'residual': record.get('residual')}


def _moe_comparison_subgraphs(rows: Sequence[Any], subgraphs: Mapping[str, Any], layers: int,
                              kda_layers: Sequence[int] = ()) -> dict[str, float]:
    """Original enrolled L2-MoE view from once-charged public rows.

    Mirrors the frozen measured routine without touching canonical rows/DAG:
    no grouped -> activation if positive, else only source-declared MoE comm;
    grouped -> exact RecurrentKDA/ChunkKDA means all L1.collective, while a real
    AllReduce non-KDA topology uses only source-declared MoE comm.  Pure TP
    AllGather/ReduceScatter is never promoted without that frozen condition.
    """
    layer_count = max(1, int(layers))
    grouped = sum(float(getattr(row, 'total_ms', 0.0)) for row in rows
                  if getattr(row, 'mechanism', '') == 'moe_grouped') / layer_count
    router = sum(float(getattr(row, 'total_ms', 0.0)) for row in rows
                 if getattr(row, 'mechanism', '') == 'moe_router') / layer_count
    activation = sum(float(getattr(row, 'total_ms', 0.0)) for row in rows
                     if getattr(row, 'mechanism', '') == 'activation') / layer_count
    collectives = [row for row in rows if getattr(row, 'mechanism', '') == 'collective']
    def _occ(row: Any) -> Mapping[str, Any]:
        return getattr(row, 'native_occurrence', None) or {}
    def _text(row: Any) -> str:
        occ = _occ(row)
        return f"{occ.get('family')} {occ.get('recipe')} {occ.get('source_role')} {occ.get('program')}".lower()
    def _moe_comm(row: Any) -> bool:
        family = str(_occ(row).get('family') or '').lower()
        if family in {'mc2_protocol', 'mc2_transport', 'alltoallv'}: return True
        text = _text(row)
        return ('moe' in text or 'dispatch' in text or 'combine' in text
                or 'alltoall' in text or 'unpack' in text)
    kda_layer_set = {int(layer) for layer in kda_layers or ()}
    def _recurrent_kda(row: Any) -> bool:
        layer = _occ(row).get('layer')
        try: layer = int(layer)
        except (TypeError, ValueError): return False
        if not kda_layer_set or layer not in kda_layer_set: return False
        text = _text(row)
        if 'recurrentkda' in text or 'chunkkda' in text: return True
        family = str(_occ(row).get('family') or '').lower()
        recipe = str(_occ(row).get('recipe') or '').lower()
        return family == 'recurrent_scan' and recipe.startswith('recurrent_scan')
    moe_comm = sum(float(getattr(row, 'total_ms', 0.0)) for row in collectives if _moe_comm(row)) / layer_count
    all_collective = sum(float(getattr(row, 'total_ms', 0.0)) for row in collectives) / layer_count
    has_kda = any(_recurrent_kda(row) for row in rows)
    has_allreduce = any('allreduce' in _text(row) for row in collectives)
    result = {str(key): float(value) for key, value in (subgraphs or {}).items()}
    if grouped <= 0.0:
        result['moe'] = activation if activation > 0.0 else moe_comm
    else:
        result['moe'] = grouped + router + activation + (all_collective if (has_kda or not has_allreduce) else moe_comm)
    return result


def _public_tokens_context(spec: Any) -> tuple[int, int]:
    if spec.phase == 'prefill':
        prompt = max(1, spec.prompt_tokens)
        return prompt, prompt
    return max(1, spec.tokens_per_sequence or 1), max(0, spec.prompt_tokens)


def _native_source_status(spec: Any, group: Mapping[str, Any] | None,
                          projection: Mapping[str, Any] | None,
                          *, basis: str = '', selected_replica: int | None = None,
                          error: str = '') -> dict[str, Any]:
    """Source/native provenance plus the public consumer that owns the numbers."""
    if group is None and projection is None and not error: return {}
    expected = int((group or {}).get('expected_membership') or 0)
    observed = [int(item.get('ep')) for item in (group or {}).get('observed') or ()]
    if projection is None:
        return {'schema': 'f17j-source-consumer-status/1', 'cell_id': spec.cell_id,
                'expected_membership': expected, 'observed_membership': len(observed),
                'selected_rank': None if group is None else group.get('selected_rank'),
                'selected_replica': selected_replica,
                'active_ownership': 'observed' if (group or {}).get('active_counts') else 'expected_or_unknown',
                'missing': tuple((group or {}).get('unknown') or ()) + ((error,) if error else ()),
                'public_status': 'unavailable', 'basis': 'base_compiled_forecast'}
    step = dict(projection.get('step') or {})
    return {'schema': 'f17j-source-consumer-status/1', 'cell_id': spec.cell_id,
            'expected_membership': expected, 'observed_membership': len(observed),
            'selected_rank': None if group is None else group.get('selected_rank'),
            'selected_replica': projection.get('selected_replica', selected_replica),
            'active_ownership': 'observed' if (group or {}).get('active_counts') else 'expected_or_unknown',
            'missing': tuple((group or {}).get('unknown') or ()) + ((error,) if error else ()),
            'public_status': 'modeled', 'public_basis': basis,
            'public_operator_events': projection.get('operator_events'),
            'public_scope': projection.get('scope'),
            'public_duration_ms': projection.get('duration_ms'),
            'public_step_ms': (float(step.get('device_end_ms', 0.0)) - float(step.get('start_ms', 0.0))
                               if step else None),
            'native_bridge': dict(projection.get('native_bridge') or {}),
            'basis': 'published L1-L3 from public graph_costs; L4 canonical serving or base_statistical_unverified'}
