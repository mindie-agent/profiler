"""Conditional source-role references for descriptor-free native attention.

[Role] Retain whole-body-aligned native calls by declared physical program group.
[Invariants] A source anchor is not a tensor contract or Host binding. Different
  physical groups are never averaged together. Existing program costs are not
  additional body work; peer waiting and elapsed kernel time do not fit rates.
[Timeouts & Locks] Bounded layer/program metadata and integer duration histograms.
[Side-Effect Policy] Pure local metadata/costing; no capture reads or devices.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


class SourceRoleReferences:
    def __init__(self, manifest, config):
        self.anchors = {(item['op_type'], item['name']): item
                        for item in config.get('source_attention_anchors', ())}
        self.by_layer = defaultdict(list)
        replicas = manifest['execution'].get('replicas', [0])
        self.replica = min(replicas)
        for target in manifest['nodes']:
            if (target['replica'] == self.replica and target['family'] == 'attention'
                    and target.get('event_matchable') is not False):
                self.by_layer[target.get('layer')].append(target)
        self.groups = {}

    def add(self, event, layer, block):
        declaration = self.anchors.get((event.op_type, event.name))
        if not declaration or block != 'attention' or declaration['attention'] != layer['attention']:
            return None
        targets = sorted(self.by_layer.get(layer['layer_id'], ()), key=lambda item: item['node_id'])
        signature = [(target['physical_signature'], target['physical_work']) for target in targets]
        key = canonical((event.op_type, event.name, declaration, signature))
        group = self.groups.setdefault(key, {
            'group_id': 'sha256:' + sha256(key.encode()).hexdigest(),
            'native_operator_type': event.op_type, 'native_name': event.name,
            'declared_role': 'attention_core', 'attention_kind': layer['attention'],
            'source_anchor_declaration': declaration, 'representative_replica': self.replica,
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
        return 'attention_core'

    def finish(self, duration_stats):
        result = []
        for group in self.groups.values():
            histogram = group['_durations']
            result.append({key: value for key, value in group.items() if not key.startswith('_')} | {
                'layer_ids': sorted(group['_layers']), 'duration_ns_counter': sorted(histogram.items()),
                'observed_us': duration_stats(histogram, 1000),
                'observed_activity_sum_ns': sum(value * count for value, count in histogram.items()),
                'status': 'source_reference', 'evidence_strength': 'source_reference',
                'basis': 'explicit_source_anchor_and_complete_whole_body_layer_topology',
                'tensor_contract': None, 'occurrence_binding_implied': False,
                'additional_budget_allowed': False,
            })
        return sorted(result, key=lambda group: group['group_id'])


def predict_source_role_references(case, manifest, actual):
    """Price each independent declared program set; never fabricate native ABI."""
    from mindie_sim.prediction.graph_analysis import graph_costs
    from mindie_sim.prediction.operator_analysis import target_graphs, operator_costs
    from mindie_sim.prediction.program import RecipeBook

    groups = actual.get('source_role_references', ())
    if not groups:
        return []
    execution = manifest['execution']
    geometry = {key: execution[key] for key in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    book = RecipeBook.from_mapping(case.runtime.kernels)
    graphs = target_graphs(case, **geometry)
    by_id = {f'rank:{replica}/{op.op_id}': op
             for replica, ops in graphs.items() for op in book.expand(ops)}
    targets = {target['node_id']: target for target in manifest['nodes']}
    result = []
    for group in groups:
        identifiers = group['representative_target_ids']
        row = dict(group)
        if not identifiers:
            row.update(prediction_status='unresolved', reason='declared_attention_program_set_unavailable')
            result.append(row)
            continue
        selected = [targets[key] for key in identifiers]
        if ([target['physical_signature'] for target in selected] != group['physical_program_signatures']
                or [target['physical_work'] for target in selected] != group['physical_work_per_program']):
            raise ValueError('source_role_reference_physical_declaration_changed')
        ops = tuple(by_id[key] for key in identifiers)
        replica = group['representative_replica']
        if len(ops) == 1 and ops[0].source_boundary != 'call':
            cost = operator_costs(case, ops, recipes=book, replica=replica)
            if cost['operator_occurrences'] != 1:
                raise ValueError('source_role_reference_expands_to_multiple_programs')
            duration = cost['operators'][0]['duration_ms']
            boundary = 'single_declared_attention_program_reference'
            programs = [{'op_id': cost['operators'][0]['operator']['op_id'],
                         'program': cost['operators'][0]['program']}]
        else:
            local = {op.op_id for op in ops}
            external = {dep: 0 for op in ops for dep in op.deps if dep not in local}
            cost = graph_costs(case, {replica: ops}, recipes=book, external_inputs=external,
                               include_submission=False, isolated=False, trace_limit=0)
            duration = cost['duration_ms']
            boundary = 'unfused_declared_attention_program_set_reference'
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
