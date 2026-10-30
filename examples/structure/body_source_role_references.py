"""Conditional source-role references for incomplete native body contracts.

[Role] Retain whole-body-aligned native calls by declared physical program group.
[Invariants] A source anchor is not a tensor contract or Host binding. Different
  physical groups are never averaged together. Existing program costs are not
  additional body work. Observed elapsed service may calibrate the same boundary;
  unseparated peer wait does not identify a pure transport rate.
[Timeouts & Locks] Bounded layer/program metadata and integer duration histograms.
[Side-Effect Policy] Pure local metadata/costing; no capture reads or devices.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import math

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import row_from_event
from mindie_profiler.tensor_contracts import observed_contract


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def communication_calibration_evidence():
    """Separate observable service calibration from pure-link identification.

    This metadata never changes cohort admission, candidate selection or cost.
    The old bandwidth field refers only to a link rate with wait removed.
    """
    return {
        'communication_bandwidth_calibration_allowed': False,
        'communication_bandwidth_calibration_scope': 'pure_link_rate_from_elapsed_without_peer_wait_separation',
        'pure_link_rate_identifiable': False,
        'observed_service_calibration': {
            'allowed': True,
            'boundary': 'same_observed_collective_or_native_program_service',
            'parameter_scopes': ['per_call', 'per_group', 'payload_or_low_M_regime'],
            'peer_wait_separation_established': False,
            'strict_admission_effect': 'none; tensor_work_and_boundary_evidence_remain_required',
            'evaluation_reporting': 'same_fit_capture_is_in_sample; holdout_requires_separate_evidence',
        },
    }


def reference_signature(target):
    """Collective occurrence labels do not change an already bound traffic ledger."""
    if target['family'] not in {'alltoall', 'alltoallv'}:
        return target['physical_signature']
    operator = deepcopy(target['operator'])
    for key in ('op_id', 'deps', 'layer', 'stage', 'requests', 'notes'):
        operator.pop(key, None)
    for key in ('collective_id', 'reverse_of_collective', 'graph_segment'):
        operator['metadata'].pop(key, None)
    return {'collective_program': operator, 'physical_work': target['physical_work']}


def routed_ffn_reference(native, local):
    """The retained MC2 call owns routed experts; shared/router/residual stay external."""
    if (len(native[2]), len(native[3])) != (8, 2):
        return None
    x, up, down, ids, scale1, scale2, weights, mask = native[2]
    y, counts = native[3]
    if len(x[0]) != 2 or len(up[0]) != 3 or len(down[0]) != 3 or len(ids[0]) != 2:
        return None
    capacity, hidden = x[0]
    experts, weight_hidden, gate_width = up[0]
    topk = ids[0][1]
    if (min(capacity, hidden, experts, gate_width, topk) <= 0 or gate_width % 2
            or x[1:] != ('bf16', 'ND') or y != x
            or weight_hidden != hidden or up[1:] != ('int8', 'FRACTAL_NZ')
            or down != ((experts, gate_width // 2, hidden), 'int8', 'FRACTAL_NZ')
            or ids != ((capacity, topk), 'int32', 'ND')
            or scale1 != ((experts * gate_width,), 'int64', 'ND')
            or scale2 != ((experts * hidden,), 'int64', 'ND')
            or weights != ((capacity, topk), 'fp32', 'ND')
            or mask != ((capacity,), 'bool', 'ND') or counts != ((experts,), 'int32', 'ND')):
        return None
    names = {'pack', 'dispatch', 'expert_up.quantize', 'expert_up', 'expert_act',
             'expert_down.quantize', 'expert_down', 'combine', 'unpack'}
    targets = {target['op_id'].split('.', 2)[-1]: target for target in local
               if target.get('block') == 'ffn' and target['op_id'].split('.', 2)[-1] in names}
    if set(targets) != names:
        return None
    upper, lower = targets['expert_up'].get('contract'), targets['expert_down'].get('contract')
    if (not upper or not lower or upper[0] != 'grouped_matrix' or lower[0] != 'grouped_matrix'
            or (upper[1][0], upper[1][2], upper[1][3]) != (experts, gate_width, hidden)
            or (lower[1][0], lower[1][2], lower[1][3]) != (experts, hidden, gate_width // 2)
            or tuple(upper[2:5]) != ('int8', 'int8', 'bf16')
            or tuple(lower[2:5]) != ('int8', 'int8', 'bf16')
            or targets['pack']['operator']['metadata'].get('top_k') != topk):
        return None
    return ('routed_ffn_native', list(targets.values()), {
        'kind': 'validated_dispatch_ffn_combine_tensor_roles',
        'source_evidence': 'tests/fixtures/native_body_contracts/v41_a3_dispatch_ffn_combine.provenance.json'}, {
        'boundary_relation': 'whole_routed_ffn_decomposed_program_reference',
        'observed_native_tensor_contract': native,
        'observed_buffer_row_capacity': capacity, 'observed_active_token_rows': None,
        'observed_valid_routed_rows': None, 'observed_active_mask_values': None,
        'declared_pack_input_rows': targets['pack']['operator']['semantic_shape'][0],
        'declared_valid_routed_rows': upper[1][1],
        'native_fusion_cost_established': False,
        'excluded_semantic_roles': ['router', 'topk', 'route_normalize', 'shared.*', 'join', 'hc_*', 'norm*'],
        **communication_calibration_evidence(),
        'limitations': ['Native fused MC2 routing, quantization, matrix scheduling and launch elimination are not modeled by this decomposed reference.',
                       'Storage capacity and active-mask/group-count values do not establish active or routed rows.',
                       'The complete declared DP cohort supplies peer context; its rank costs are not added into a single-card elapsed time.']})


class SourceRoleReferences:
    def __init__(self, manifest, config):
        self.anchors = {(item['op_type'], item['name']): item
                        for item in config.get('source_attention_anchors', ())}
        self.by_layer = defaultdict(list)
        self.subgraphs = defaultdict(list)
        replicas = manifest['execution'].get('replicas', [0])
        self.replica = min(replicas)
        for target in manifest['nodes']:
            if target['replica'] == self.replica and target.get('event_matchable') is not False:
                self.by_layer[target.get('layer')].append(target)
        for target in manifest.get('subgraphs', ()):
            if target['replica'] == self.replica:
                self.subgraphs[target.get('layer')].append(target)
        self.groups = {}

    def _select(self, event, layer, block):
        local = self.by_layer.get(layer['layer_id'], ())
        declaration = self.anchors.get((event.op_type, event.name))
        if declaration and block == 'attention' and declaration['attention'] == layer['attention']:
            return ('attention_core', [target for target in local if target['family'] == 'attention'],
                    declaration, {'boundary_relation': 'source_symbol_to_declared_attention_program'})
        row = row_from_event(event)
        native = native_tensor_contract(row)
        if native is None:
            return None
        inputs, outputs = native[2:]
        if event.op_type == 'DispatchFFNCombine' and block == 'ffn':
            return routed_ffn_reference(native, local)
        if event.op_type == 'GroupedMatmul' and block == 'ffn':
            contract = observed_contract(row)
            if not contract or contract[0] != 'grouped_matrix':
                return None
            e, capacity, n, k = contract[1]
            candidates = []
            for target in local:
                expected = target.get('contract')
                if (target.get('block') == 'ffn' and expected and expected[0] == 'grouped_matrix'
                        and tuple(expected[1][::2]) == (e, n)
                        and expected[1][3] == k and tuple(expected[2:5]) == contract[2:5]
                        and tuple(expected[5][1:]) == contract[5][1:] and expected[6] == contract[6]):
                    candidates.append(target)
            if len(candidates) != 1:
                return None
            target = candidates[0]
            role = target['op_id'].rsplit('.', 1)[-1]
            if role not in {'expert_up', 'expert_down'}:
                return None
            source = next((group.get('source') for group in self.subgraphs[layer['layer_id']]
                           if target['node_id'] in group['node_ids'] and group.get('source')), None)
            return (role, candidates, {'kind': 'validated_native_expert_weight_axes', 'source': source}, {
                'boundary_relation': 'capacity_vs_valid_rows_conditional',
                'observed_buffer_row_capacity': capacity,
                'declared_valid_routed_rows': target['contract'][1][1],
                'observed_valid_routed_rows': None, 'observed_group_list_values': None,
                'validated_geometry': {'expert_banks': e, 'output_width': n, 'input_width': k,
                                       'operand_output_dtypes': contract[2:5]},
                'observed_native_tensor_contract': native,
                'prediction_coverage': target.get('contract_scope'),
                'limitations': ['Buffer capacity does not prove valid routed FLOPs or active expert counts.',
                                'Native MXFP4 service/conversion coverage follows the declared program.']})
        if event.op_type in {'HcPre', 'HcPost'}:
            role = 'hc_pre' if event.op_type == 'HcPre' else 'hc_post'
            groups = [group for group in self.subgraphs[layer['layer_id']]
                      if group.get('role') == role and group.get('block') == block]
            if len(groups) != 1:
                return None
            group = groups[0]
            expected = group.get('contract')
            if not expected or expected[0] != 'hyper_connection_active':
                return None
            if role == 'hc_pre':
                if len(inputs) != 5 or len(outputs) != 4 or len(inputs[0][0]) not in {3, 4}:
                    return None
                leading, (hc, width) = inputs[0][0][:-2], inputs[0][0][-2:]
                tokens = math.prod(leading)
                active_inputs = (((tokens, hc, width), *inputs[0][1:]), *inputs[1:4])
                active_outputs = (((tokens, width), *outputs[0][1:]),
                                  ((tokens, hc), *outputs[1][1:]),
                                  ((tokens, hc, hc), *outputs[2][1:]))
                if (canonical(active_inputs) != canonical(expected[2])
                        or canonical(active_outputs) != canonical(expected[3])
                        or tuple(item[0] for item in outputs[:3]) !=
                           ((*leading, width), (*leading, hc), (*leading, hc, hc))
                        or inputs[4] != ((*leading, hc), 'fp32', 'ND')
                        or outputs[3] != inputs[4]):
                    return None
                relation = 'partial_base_program_reference_premix_branch_unresolved'
            else:
                if canonical(observed_contract(row)) != canonical(expected):
                    return None
                relation = 'source_role_hyper_connection_post'
            targets = [target for target in local if target['node_id'] in group['node_ids']]
            if len(targets) != len(group['node_ids']):
                return None
            return (f'{block}.{role}', targets, group.get('source'), {
                'boundary_relation': relation, 'observed_native_tensor_contract': native,
                'limitations': ['The supplied pre-mix branch is not proven equivalent to the full declared base subgraph.']
                              if role == 'hc_pre' else []})
        if event.op_type in {'MoeDistributeDispatchV3', 'MoeDistributeCombineV3'} and block == 'ffn':
            dispatch = event.op_type == 'MoeDistributeDispatchV3'
            if (len(inputs), len(outputs)) != ((8, 7) if dispatch else (19, 1)):
                return None
            x, ids = inputs[1:3]
            y = outputs[0]
            if (len(x[0]) != 2 or len(ids[0]) != 2 or len(y[0]) != 2
                    or ids[1:] != ('int32', 'ND') or x[2] != 'ND' or y[2] != 'ND'
                    or x[0][1] != y[0][1] or (x if dispatch else y)[0][0] != ids[0][0]):
                return None
            recipes = {'route_pack', 'expert_dispatch'} if dispatch else {'expert_combine', 'route_unpack'}
            targets = [target for target in local if target.get('block') == 'ffn'
                       and target['operator']['recipe'] in recipes]
            if {target['operator']['recipe'] for target in targets} != recipes:
                return None
            pack = next((target for target in local if target['operator']['recipe'] == 'route_pack'), None)
            metadata = pack['operator']['metadata'] if pack else {}
            if metadata.get('top_k') != ids[0][1]:
                return None
            if dispatch and x[1] != y[1]:
                quant = [target for target in local if target['op_id'].endswith('.expert_up.quantize')]
                if len(quant) != 1:
                    return None
                qcontract = quant[0].get('contract')
                if not qcontract or qcontract[0] != 'DynamicMxQuant' or (qcontract[2], qcontract[3]) != (x[1], y[1]):
                    return None
                targets += quant
            elif not dispatch and x[1] != y[1]:
                return None
            return ('expert_dispatch_native' if dispatch else 'expert_combine_native', targets,
                {'kind': 'native_mc2_v3_tensor_roles',
                 'protocol_evidence': 'examples/structure/acceptance-20261030-priority-operators/kimi-native-expert-protocol-evidence.json',
                 'protocol_evidence_sha256': '4c9a86879343cecfc589eb1f1523a02a2c0a94f757545b7a056c45a4864d8582'}, {
                    'boundary_relation': 'pack_transport_output_quant_reference' if dispatch else 'transport_unpack_weighted_combine_reference',
                    'observed_native_tensor_contract': native,
                    'observed_buffer_row_capacity': y[0][0] if dispatch else x[0][0],
                    'observed_valid_routed_rows': None,
                    'limitations': ['Native atomic implementation and active peer/routing counts remain unproven.',
                                    'Declared generic transport may differ from native destination-window protocol.',
                                    'Elapsed native communication may include peer wait; same-boundary service may be calibrated but a pure link rate is not identified.'],
                    **communication_calibration_evidence()})
        return None

    def add(self, event, layer, block):
        selected = self._select(event, layer, block)
        if selected is None:
            return None
        role, targets, declaration, relation = selected
        targets = sorted(targets, key=lambda item: item['node_id'])
        signature = [(reference_signature(target), target['physical_work']) for target in targets]
        key = canonical((event.op_type, event.name, role, declaration, relation, signature))
        group = self.groups.setdefault(key, {
            'group_id': 'sha256:' + sha256(key.encode()).hexdigest(),
            'native_operator_type': event.op_type, 'native_name': event.name,
            'declared_role': role, 'attention_kind': layer['attention'], 'block': block,
            'source_anchor_declaration': declaration, 'representative_replica': self.replica,
            'source_correspondence': relation,
            'representative_target_ids': [target['node_id'] for target in targets],
            'physical_program_signatures': [target['physical_signature'] for target in targets],
            'physical_work_per_program': [target['physical_work'] for target in targets],
            '_durations': Counter(), '_layers': set(), 'examples': [],
        })
        group['_durations'][event.duration_ns] += 1
        group['_layers'].add(layer['layer_id'])
        if len(group['examples']) < 2:
            group['examples'].append({'event_id': event.event_id, 'locator': event.locator,
                'layer_id': layer['layer_id'], 'start_ns': event.start_ns, 'end_ns': event.end_ns})
        return role

    def finish(self, duration_stats):
        result = []
        for group in self.groups.values():
            histogram = group['_durations']
            result.append({key: value for key, value in group.items() if not key.startswith('_')} | {
                'layer_ids': sorted(group['_layers']), 'duration_ns_counter': sorted(histogram.items()),
                'observed_us': duration_stats(histogram, 1000),
                'observed_activity_sum_ns': sum(value * count for value, count in histogram.items()),
                'status': 'source_reference', 'evidence_strength': 'source_reference',
                'basis': 'source_semantics_and_complete_whole_body_layer_topology',
                'tensor_contract': None, 'occurrence_binding_implied': False,
                'additional_budget_allowed': False,
            })
        return sorted(result, key=lambda group: group['group_id'])


def _reference_graphs(graphs, book, groups):
    """Keep selected expanded programs on every peer after full graph validation.

    Complete graph construction resolves dispatch/combine traffic first. The
    reference boundary then treats outside predecessors as ready, so unrelated
    model layers need not remain live while these programs are priced.
    """
    local_ids = {key.split('/', 1)[1] for group in groups
                 for key in group['representative_target_ids']}
    return {replica: tuple(op for op in book.expand(ops) if op.op_id in local_ids)
            for replica, ops in graphs.items()}


def predict_source_role_references(case, manifest, actual):
    """Price each independent declared program set; never fabricate native ABI."""
    from mindie_sim.prediction.graph_analysis import graph_costs
    from mindie_sim.prediction.operator_analysis import target_graphs, operator_costs
    from mindie_sim.prediction.program import RecipeBook
    from mindie_sim.prediction.body_defaults import effective_body_declaration

    groups = actual.get('source_role_references', ())
    if not groups:
        return []
    execution = manifest['execution']
    geometry = {key: execution[key] for key in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    case, _ = effective_body_declaration(case, geometry['phase'], tokens=geometry['tokens'], scope=geometry['scope'])
    book = RecipeBook.from_mapping(case.runtime.kernels)
    graphs = _reference_graphs(target_graphs(case, **geometry), book, groups)
    by_id = {f'rank:{replica}/{op.op_id}': op
             for replica, ops in graphs.items() for op in ops}
    targets = {target['node_id']: target for target in manifest['nodes']}
    result = []
    for group in groups:
        identifiers = group['representative_target_ids']
        row = dict(group)
        if not identifiers:
            row.update(prediction_status='unresolved', reason='declared_source_program_set_unavailable')
            result.append(row)
            continue
        selected = [targets[key] for key in identifiers]
        if ([target['physical_signature'] for target in selected] != group['physical_program_signatures']
                or [target['physical_work'] for target in selected] != group['physical_work_per_program']):
            raise ValueError('source_role_reference_physical_declaration_changed')
        identifier_set = set(identifiers)
        ops = tuple(op for key, op in by_id.items() if key in identifier_set)
        if len(ops) != len(identifier_set):
            raise ValueError('source_role_reference_targets_missing_from_fresh_graph')
        replica = group['representative_replica']
        if len(ops) == 1 and ops[0].source_boundary != 'call':
            cost = operator_costs(case, ops, recipes=book, replica=replica)
            if cost['operator_occurrences'] != 1:
                raise ValueError('source_role_reference_expands_to_multiple_programs')
            duration = cost['operators'][0]['duration_ms']
            boundary = 'single_declared_program_reference'
            programs = [{'op_id': cost['operators'][0]['operator']['op_id'],
                         'program': cost['operators'][0]['program']}]
        else:
            local = {op.op_id for op in ops}
            joint = case.runtime.parallel.ep_spans_dp and any(
                dict(op.metadata).get('group_axis') == 'ep' for op in ops)
            selected_graphs = ({rank: tuple(op for op in values if op.op_id in local)
                                for rank, values in graphs.items()} if joint else {replica: ops})
            # target_graphs has already validated/transposed the full dispatch
            # ledger. Keep that concrete traffic while cutting the predecessor
            # out of a combine-only cost boundary; do not execute dispatch twice.
            selected_graphs = {rank: tuple(replace(op, metadata=tuple(
                (key, value) for key, value in op.metadata if key != 'reverse_of_collective'))
                if 'reverse_of_collective' in dict(op.metadata)
                and dict(op.metadata)['reverse_of_collective'] not in local
                and 'peer_traffic' in dict(op.metadata) else op for op in values)
                for rank, values in selected_graphs.items()}
            external = {dep: 0 for values in selected_graphs.values() for op in values
                        for dep in op.deps if dep not in local}
            cost = graph_costs(case, selected_graphs, recipes=book, external_inputs=external,
                               include_submission=False, isolated=False, trace_limit=0)
            duration = cost['duration_ms']
            boundary = ('complete_collective_cohort_program_set_reference' if joint
                        else 'unfused_declared_program_set_reference')
            programs = [{'op_id': op.op_id, 'family': op.family, 'recipe': op.recipe} for op in ops]
        measured = group['observed_us']['mean']
        difference = duration * 1000 - measured
        row.update(prediction_status='reference_only', boundary=boundary,
            declared_programs=programs, predicted_reference_us=duration * 1000,
            per_call_reference_diff_us=difference,
            reference_tolerance_us=15 if measured <= 50 else measured * .15,
            reference_within_tolerance=abs(difference) <= (15 if measured <= 50 else measured * .15),
            observed_activity_ms_per_forward=group['observed_activity_sum_ns']/1e6/actual['forward_count'],
            predicted_service_ms_per_forward=duration*group['observed_us']['count']/actual['forward_count'],
            conditions=['Existing case-declared programs; these costs are already part of model work.',
                'Representative DP replica is conditional; the capture does not establish symmetric peer activity.',
                'Native scalar arguments, cache contents, tiling and tensor ABI remain unobserved.',
                'Unfused program sets are references and do not establish an atomic native kernel implementation.'])
        result.append(row)
    return result
