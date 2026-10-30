"""Conditional source caller programs against complete retained populations.

[Role] Connect conv-state copy, MX routing and explicit HCCL source programs.
[Invariants] Retained symbols/regions are not native tensor ABI or Host binds.
  Complete histograms stay intact; heterogeneous saved populations are rejected.
  Copy direction remains unresolved; equal gather/scatter multiplicity is explicit.
[Timeouts & Locks] Pure bounded metadata; no cost workers, files or locks.
[Side-Effect Policy] Returns new reference rows without changing declarations.
"""
from collections import defaultdict
from hashlib import sha256

from body_source_role_references import canonical

COPY = 'triton_noncontiguous_conv_state_copy'
ROUTE = 'ascend_moe_init_routing_v3_mxfp8'
COLLECTIVES = {'hcom_allReduce_': 'allreduce', 'hcom_allReduce_AicpuKernel': 'allreduce',
               'hcom_allGather_': 'allgather', 'hcom_reduceScatter_': 'reduce_scatter'}


def program_identity(nodes):
    """Remove location only; preserve the complete source program and work."""
    result = []
    ids = {n['op_id']: i for i, n in enumerate(nodes)}
    for node in nodes:
        op = node['operator']; m = op['metadata']
        result.append({'recipe': node['recipe'], 'family': node['family'],
            'dtype': op['dtype'], 'shape': op['local_shape'], 'work': node['physical_work'],
            'internal_dependencies': [ids[d] for d in op['deps'] if d in ids],
            'program_execution': m.get('program_execution'),
            'direction': m.get('direction'), 'state_slots': m.get('state_slots'),
            'state_dtype': m.get('state_dtype'), 'state_strides': m.get('state_strides'),
            'moe_init_config': m.get('moe_init_config'),
            'hccl_selection': m.get('hccl_selection'),
            'hccl_phase': m.get('hccl_phase'),
            'peer_traffic': m.get('peer_traffic')})
    return canonical(result)


def _cost_group(nodes, replica):
    signature = program_identity(nodes)
    return {'program_set_key': sha256(signature.encode()).hexdigest(),
        'representative_replica': replica,
        'representative_target_ids': [n['node_id'] for n in nodes],
        'physical_program_signatures': [n['physical_signature'] for n in nodes],
        'physical_work_per_program': [n['physical_work'] for n in nodes],
        'observed_us': {'count': 1, 'mean': 0}, 'observed_activity_sum_ns': 0}


def _reference(group, key, layers, components, conditions, *, role, correspondence):
    histogram = group['duration_ns_counter']
    if sum(n for _, n in histogram) != group['observed_us']['count']:
        raise ValueError('retained_histogram_count_differs')
    return {'group_id': key, 'retained_group_id': key,
        'native_operator_type': group['native_operator_type'], 'native_abi': None,
        'observed_contract': None, 'evidence_strength': 'source_symbol_retained_group',
        'declared_role': role, 'layer_ids': layers,
        'observed_us': group['observed_us'], 'duration_ns_counter': histogram,
        'observed_activity_sum_ns': sum(ns*n for ns, n in histogram),
        'cost_components': components, 'source_correspondence': correspondence,
        'conditions': conditions, 'strict_accuracy_implied': False,
        'strict_accuracy_pass': None, 'accuracy_status': 'reference_only',
        'occurrence_binding_implied': False, 'additional_budget_allowed': False}


def prepare_callers(actual, manifest):
    replica = min(manifest['execution']['replicas']); by_layer = defaultdict(list)
    for n in manifest['nodes']:
        if n['replica'] == replica and n.get('layer') is not None:
            by_layer[n['layer']].append(n)
    refs, failures, costs, selected = [], [], {}, {}
    for fi, family in enumerate(actual['families']):
        kind = family['native_operator_type']
        if kind not in {'_copy_conv_state_kernel', 'MoeInitRoutingV3'}:
            continue
        for gi, g in enumerate(family['structure_groups']):
            retained = {**g, 'native_operator_type': kind}
            recipe = COPY if kind == '_copy_conv_state_kernel' else ROUTE
            regions = {}
            for layer, nodes in by_layer.items():
                candidates = [n for n in nodes if n['recipe'] == recipe
                              and n['block'] == g['block']
                              and n['structure']['attention_kind'] == g['attention_kind']]
                if candidates:
                    regions[layer] = candidates
            count_per_layer = 2 if recipe == COPY else 1
            try:
                if not regions or any(len(ns) != count_per_layer for ns in regions.values()):
                    raise ValueError('declared_caller_population_missing')
                ordered = {}
                for layer, ns in regions.items():
                    if recipe == COPY:
                        directions = {n['operator']['metadata']['direction']: n for n in ns}
                        if set(directions) != {'gather', 'scatter'}:
                            raise ValueError('copy_pair_boundary_incomplete')
                        ns = [directions['gather'], directions['scatter']]
                    ordered[layer] = ns
                first = next(iter(ordered.values()))
                if any([program_identity([n]) for n in ns] != [program_identity([n]) for n in first]
                       for ns in ordered.values()):
                    raise ValueError('heterogeneous_layer_work_saved_histogram_not_splittable')
                if g['observed_us']['count'] != actual['forward_count']*len(ordered)*count_per_layer:
                    raise ValueError('retained_calls_do_not_match_declared_caller_multiplicity')
                components = []
                for n in first:
                    c = _cost_group([n], replica); costs[c['program_set_key']] = c
                    selected[n['node_id']] = n
                    components.append({'program_set_key': c['program_set_key'], 'weight': 1/count_per_layer})
                key = f'families/{fi}/structure_groups/{gi}'
                conditions = ['Source symbol plus whole-Body topology and multiplicity only; native tensor ABI is not retained for this complete population.',
                    'Declared active requests, valid indices and runtime source version remain conditions; no captured binary identity is established.',
                    'Activity residual is not additive Body wall-clock error.']
                if recipe == COPY:
                    conditions += ['Both gather/scatter histograms are pooled; no per-event direction is inferred.',
                        'The per-call reference is (gather service + scatter service)/2; zero-fill and convolution are excluded.']
                else:
                    conditions += ['All tokens*topk assignments are explicitly declared valid and local (EP1); captured index/count values are unobserved.']
                refs.append(_reference(retained, key, sorted(ordered), components, conditions,
                    role='conv_state_copy_gather_scatter_cohort' if recipe == COPY else 'local_routing_mxfp8',
                    correspondence={'boundary_relation': 'source_caller_multiplicity_reference',
                        'program_profile': recipe, 'calls_per_declared_layer': count_per_layer,
                        'native_abi_population_verified': False,
                        'source': first[0]['operator']['metadata'].get('source'), 'limitations': conditions}))
            except ValueError as error:
                failures.append({'native_operator_type': kind, 'retained_group_id': f'families/{fi}/structure_groups/{gi}',
                    'event_count': g['observed_us']['count'], 'reason': str(error)})
    return refs, failures, list(costs.values()), {'execution': manifest['execution'],
        'graph_id': manifest['graph_id'], 'nodes': list(selected.values())}


def prepare_hccl(ledger, manifest):
    replica = min(manifest['execution']['replicas']); source_groups = defaultdict(list)
    for n in manifest['nodes']:
        m = n['operator']['metadata']
        if n['replica'] == replica and m.get('hccl_source_group'):
            source_groups[(n['layer'], n['block'], m['hccl_source_group'])].append(n)
    refs, failures, costs, selected = [], [], {}, {}
    for i, g in enumerate(ledger['groups']):
        family = COLLECTIVES.get(g['native_operator_type'])
        if not family or g['event_category'] not in {'collective_device_task','collective_envelope_only'}:
            continue
        try:
            per_layer = {}
            for layer_text, count in g['layer_counts'].items():
                layer = int(layer_text)
                calls = [ns for (l, block, _), ns in source_groups.items()
                         if l == layer and block == g['block']
                         and ns[0]['operator']['metadata']['hccl_selection']['collective'] == family]
                if len(calls) != 1 or count != ledger['forward_count']:
                    raise ValueError('collective_region_not_one_declared_call_per_layer_forward')
                per_layer[layer] = calls[0]
            if not per_layer:
                raise ValueError('collective_layer_evidence_missing')
            first = next(iter(per_layer.values())); signature = program_identity(first)
            if any(program_identity(ns) != signature for ns in per_layer.values()):
                raise ValueError('heterogeneous_collective_work_saved_histogram_not_splittable')
            selection = first[0]['operator']['metadata']['hccl_selection']
            if g['implementation_name'] == 'AivKernel' and selection['expansion'] != 'AIV':
                raise ValueError('explicit_source_engine_conflicts_with_observed_AIV')
            if selection['expansion'] == 'AIV' and g['implementation_name'] != 'AivKernel':
                raise ValueError('AIV_reference_requires_retained_AIV_device_task')
            c = _cost_group(first, replica); costs[c['program_set_key']] = c
            selected.update((n['node_id'],n) for n in first)
            conditions = ['Explicit source template, rank graph, dtype and local payload are declaration conditions, not captured HCCL arguments.',
                'All local phases and peer exchanges of one source collective are priced together, once.',
                'Unlinked AICPU controllers and exact duplicate summary rows are not added to this measured population.',
                'Elapsed can contain protocol/peer waiting; the service residual is not additive Body wall-clock error.']
            refs.append(_reference(g, f'groups/{i}', sorted(per_layer),
                [{'program_set_key': c['program_set_key'], 'weight': 1}], conditions,
                role=family+'_explicit_source_collective', correspondence={
                    'boundary_relation': 'complete_explicit_collective_program_set_reference',
                    'selection': selection, 'observed_event_category': g['event_category'],
                    'observed_implementation_name': g['implementation_name'],
                    'observed_device_engine': 'AIV' if g['implementation_name']=='AivKernel' else None,
                    'measured_payload_bytes': g.get('measured_payload_bytes'),
                    'observed_hccl_algorithm': g.get('observed_hccl_algorithm'),
                    'template_selection_confirmed': False, 'limitations': conditions}))
        except ValueError as error:
            failures.append({'native_operator_type':g['native_operator_type'], 'retained_group_id':f'groups/{i}',
                             'event_count':g['observed_us']['count'], 'reason':str(error)})
    return refs, failures, list(costs.values()), {'execution':manifest['execution'],
        'graph_id':manifest['graph_id'], 'nodes':list(selected.values())}
