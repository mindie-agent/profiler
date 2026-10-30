"""Extract native operator families strictly inside complete Decode bodies.

[Role] Reuse whole-body segmentation, Sim structure and profiler tensor cohorts.
[Invariants] Conditional topology narrows roles, never becomes Host occurrence
  evidence. Complete integer-ns body windows exclude heads/drafts. Real HCOM is
  retained once; its elapsed duration may contain peer wait, not link service.
[Timeouts & Locks] One bounded active forward; serial source scans; bounded JSON.
[Side-Effect Policy] Local retained captures only; no device, remote or weights.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import re
import subprocess
import sys
import time
from mindie_profiler.process_memory import peak_rss_bytes

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards, _norm, _norm_start, _anchor, _Row, is_aicpu_controller
from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.normalized import kernel_rows, shapes, row_from_event
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import StructureMapper, _freeze
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from references import SourceRoleReferences

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / '.mindie-local/operator-results'
MAX_JSON = 32 * 1024**2


def read(path):
    path = Path(path)
    if path.stat().st_size > MAX_JSON:
        raise ValueError(f'metadata_exceeds_32_mib:{path}')
    return json.loads(path.read_text())


def digest(path):
    value = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def identity(path):
    path = Path(path)
    return {'path': str(path), 'sha256': digest(path), 'size_bytes': path.stat().st_size}


def runtime_identity():
    import mindie_sim
    sim=Path(mindie_sim.__file__).resolve().parent
    paths=[*sorted(sim.rglob('*.py')), *sorted((sim/'backends/profiles').glob('*.json')),
           *sorted((ROOT/'mindie_profiler').glob('*.py')),Path(__file__).resolve(),
           Path(__file__).with_name('references.py')]
    return {str(path):digest(path) for path in paths}


def write(path, value):
    encoded = json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n'
    if len(encoded.encode()) > MAX_JSON:
        raise ValueError(f'output_exceeds_32_mib:{path}')
    Path(path).write_text(encoded)


def duration_stats(histogram, scale=1e6):
    count = sum(histogram.values())
    if not count:
        return dict(count=0, mean=None, p50=None, p90=None, min=None, max=None)
    positions = [(count-1)//2, count//2, ceil(count*.9)-1]
    samples, seen = [], 0
    for position in positions:
        seen = 0
        for value, multiplicity in sorted(histogram.items()):
            if seen <= position < seen + multiplicity:
                samples.append(value)
                break
            seen += multiplicity
    return dict(count=count, mean=sum(value*n for value,n in histogram.items())/count/scale,
                p50=(samples[0]+samples[1])/2/scale, p90=samples[2]/scale,
                min=min(histogram)/scale, max=max(histogram)/scale)


def declared_role(target):
    name = target.get('op_id') or target.get('subgraph_id', '').split('/', 1)[-1]
    return re.sub(r'^s\d+\.l\d+\.', '', name.removeprefix('subgraph:'))


def role_block(target):
    role = declared_role(target)
    if role == 'norm1' or role.startswith('norm1.'):
        return 'attention'
    if role == 'norm2' or role.startswith('norm2.'):
        return 'ffn'
    return target.get('block')


def active_causal_contract(row):
    """Project a declared active conv ABI without weakening the shared full ABI."""
    native = native_tensor_contract(row)
    if native is None or row.kind != 'CausalConv1d' or len(native[2]) != 12 or len(native[3]) != 1:
        return None
    inputs, outputs = native[2:]
    x, weight, bias, pool, y = inputs[0], inputs[1], inputs[2], inputs[3], outputs[0]
    if (len(x[0]) != 2 or len(weight[0]) != 2 or len(pool[0]) != 3 or y[0] != x[0]
            or not x[0][-1] == weight[0][-1] == pool[0][-1]
            or len({item[1] for item in (x,weight,pool,y)}) != 1
            or x[1] not in {'bf16','fp16'} or any(item[2] != 'ND' for item in (x,weight,pool,y))
            or (bias[0] and (bias[0] != (x[0][-1],) or bias[1:] != x[1:]))):
        return None
    return ('causal_conv1d_active','CausalConv1d',x,weight,bias,(pool[0][-2:],pool[1],pool[2]),y)


def deduplicate_communication(events):
    concrete = {(event.device_id, event.op_type, event.start_ns, event.end_ns)
                for event in events if event.op_type.startswith('hcom_')
                and event.task_id not in {'', 'N/A', 'None'}
                and event.stream_id not in {'', 'N/A', 'None'}}
    retained, duplicates = [], []
    for event in events:
        key = (event.device_id, event.op_type, event.start_ns, event.end_ns)
        summary = event.task_id in {'', 'N/A', 'None'} or event.stream_id in {'', 'N/A', 'None'}
        if event.op_type.startswith('hcom_') and summary and key in concrete:
            duplicates.append(event)
        else:
            retained.append(event)
    return retained, duplicates


class RoleMapper(StructureMapper):
    """Refine tensor candidates with a complete, conditional topology alignment."""
    layer = None
    block = None

    def match(self, event, observation):
        result = self._match(event, observation, self._check_source(observation))
        status, ids, candidates, basis, evidence, contract, refinement = result
        active = active_causal_contract(row_from_event(event)) if event.op_type == 'CausalConv1d' else None
        if active is not None and _freeze(active) in self.contracts:
            contract = active
            candidates = self._rank_candidates(self.contracts[_freeze(active)],observation.rank_id)
        local = [key for key in candidates if self.targets[key].get('layer') == self.layer
                 and (role_block(self.targets[key]) in {None, self.block})]
        roles = {declared_role(self.targets[key]) for key in local}
        selected = [key for key in candidates if declared_role(self.targets[key]) in roles]
        if candidates and not selected:
            return 'unmapped', [], [], 'topology_role_conflict', None, contract, None
        if selected:
            candidates = selected
            status = 'candidate' if len(candidates) == 1 else 'ambiguous'
            basis = 'tensor_contract_only' if len(candidates) == 1 else 'repeated_tensor_contract'
            refinement = {'basis': 'whole_body_topology_conditioned_role',
                          'declared_roles': sorted(roles), 'block': self.block,
                          'occurrence_binding_implied': False}
            if active is not None and contract == active:
                refinement['contract_projection'] = 'active_x_weight_bias_history_output; excludes_pool_capacity_and_scalar_index_values'
        return status, [], candidates, basis, evidence, contract, refinement


class BodyConsumer:
    def __init__(self, manifest, observation, expected, model_config):
        self.mapper = RoleMapper(manifest, mapping_limit=0, max_events=1_000_000, phase='decode')
        self.accumulator = CohortAccumulator(manifest['graph_id'], self.mapper.target_index,
                                            observation, execution=manifest['execution'])
        self.observation, self.expected, self.config = observation, expected, model_config
        self.counts, self.statuses, self.reasons = Counter(), Counter(), Counter()
        self.families, self.pooled = {}, defaultdict(Counter)
        self.forward_ids, self.examples = [], []
        self.source_roles = SourceRoleReferences(manifest, model_config)

    def __call__(self, result, segment):
        expected = self.expected[result['forward_id']]
        if any(result[key] != expected[key] for key in ('start_ns', 'end_ns', 'head_start_ns', 'head_end_ns', 'query_rows', 'device_id')):
            raise ValueError('complete_body_boundary_changed')
        self.forward_ids.append(result['forward_id'])
        layers = [stage for stage in result['stages'] if stage['layer_id'] is not None]
        for layer in layers:
            if layer['layer_id'] != 0:
                duration = layer['end_ns']-layer['start_ns']
                self.pooled['all'][duration] += 1
                self.pooled[layer['attention']][duration] += 1
        starts = [layer['start_ns'] for layer in layers]
        ffns = {}
        for layer in layers:
            boundary = layer['evidence']['successor_boundary_start_ns']
            candidates = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes))
                          for event in segment if layer['start_ns'] <= event.start_ns < boundary]
            anchor = next(row.event.start_ns for row in candidates if _anchor(row, self.config))
            norm_index=next(index for index,row in enumerate(candidates)
                            if row.event.start_ns>anchor and _norm(row,self.config['hidden_size']))
            ffns[layer['layer_id']]=candidates[_norm_start(candidates,norm_index,self.config['hidden_size'])].event.start_ns
        selected = []
        for event in segment:
            if not result['start_ns'] <= event.start_ns < result['end_ns']:
                self.counts['outside_body_events'] += 1
                continue
            if is_aicpu_controller(event):
                self.counts['scheduler_wrapper_events'] += 1
            elif event.end_ns > result['end_ns']:
                self.counts['crossing_body_endpoint_events'] += 1
            else:
                selected.append(event)
        selected, duplicate = deduplicate_communication(selected)
        self.counts['duplicate_communication_summary_events'] += len(duplicate)
        for event in selected:
            layer = layers[bisect_right(starts, event.start_ns)-1]
            self.mapper.layer = layer['layer_id']
            self.mapper.block = 'attention' if event.start_ns < ffns[layer['layer_id']] else 'ffn'
            status, ids, candidates, basis, evidence, contract, refinement = self.mapper.match(event, self.observation)
            roles = tuple(sorted({declared_role(self.mapper.targets[key]) for key in candidates}))
            role = '|'.join(roles) or 'unresolved'
            source_role = self.source_roles.add(event, layer, self.mapper.block) if not roles else None
            if source_role:
                role = source_role
            if event.op_type.startswith('hcom_'):
                role = 'attention_output_communication' if self.mapper.block == 'attention' else 'ffn_down_communication'
            reason = self.accumulator.add(event, (event.start_ns, event.end_ns), status=status,
                    ids=ids, candidates=candidates, basis=basis, contract=contract, refinement=refinement)
            self.counts['selected_body_events'] += 1
            self.statuses[status] += 1
            self.reasons[reason or 'cohort_eligible'] += 1
            key = event.op_type, role
            family = self.families.setdefault(key, {'durations': Counter(), 'cohort_reasons': Counter(),
                'layer_groups': defaultdict(Counter), 'structure_groups':defaultdict(Counter),
                'target_ids': set(), 'role_basis': 'whole_body_topology_and_tensor_contract' if roles else
                'topology_region_only; tensor_contract_unresolved', 'examples': []})
            family['durations'][event.duration_ns] += 1
            family['layer_groups']['layer0' if layer['layer_id']==0 else 'steady_layers'][event.duration_ns] += 1
            family['structure_groups'][(layer['attention'],self.mapper.block)][event.duration_ns]+=1
            family['cohort_reasons'][reason or 'cohort_eligible'] += 1
            family['target_ids'].update(candidates)
            if len(family['examples']) < 2:
                family['examples'].append({'event_id': event.event_id, 'locator': event.locator,
                    'layer_id': layer['layer_id'], 'attention': layer['attention'], 'block': self.mapper.block,
                    'contract': contract, 'start_ns': event.start_ns, 'end_ns': event.end_ns})

    def finish(self, manifest):
        if set(self.forward_ids) != set(self.expected):
            raise ValueError('body_population_differs_from_retained_acceptance')
        cohorts = self.accumulator.finish()
        role_ids = {row['cohort_id']: sorted({declared_role(self.mapper.targets[key]) for key in row['target_ids']}) for row in cohorts}
        window = {'rank_id': self.observation.rank_id, 'step': None,
                  'source_identity': self.observation.source.content_identity(),
                  'window': {'start_ns': self.observation.window.start_ns, 'end_ns': self.observation.window.end_ns,
                             'label': 'union_of_verified_complete_decode_body_windows'},
                  'cohorts': cohorts, 'cohort_excluded_event_counts': dict(self.accumulator.excluded)}
        mapping = {'schema_version': 'mindie-profile-structure-mapping/1', 'graph_id': manifest['graph_id'],
            'declared_execution': manifest['execution'], 'structure_source': manifest.get('source'),
            'observed_phase': 'decode', 'event_window_count': self.counts['selected_body_events'],
            'status_counts': dict(self.statuses), 'windows': [window],
            'cohort_event_window_count': sum(row['event_count'] for row in cohorts),
            'cohort_status': 'aggregated', 'conditional_role_by_cohort_id': role_ids}
        families = [{'native_operator_type': kind, 'declared_role': role,
                     'duration_ns_counter': sorted(value['durations'].items()),
                     'observed_us': duration_stats(value['durations'], 1000),
                     'cohort_reasons': dict(value['cohort_reasons']),
                     'candidate_target_ids': sorted(value['target_ids']),
                     'role_basis': value['role_basis'], 'examples': value['examples']}
                    for (kind, role), value in sorted(self.families.items())]
        for family in families:
            groups=self.families[family['native_operator_type'],family['declared_role']]['layer_groups']
            family['structure_groups']=[{'attention_kind':key[0],'block':key[1],
                'observed_us':duration_stats(histogram,1000),'duration_ns_counter':sorted(histogram.items())}
                for key,histogram in self.families[family['native_operator_type'],family['declared_role']]['structure_groups'].items()]
            family['layer_groups']={key:{'observed_us':duration_stats(histogram,1000),
                                        'duration_ns_counter':sorted(histogram.items())}
                                    for key,histogram in groups.items()}
        pooled = [{'attention_kind': None if kind == 'all' else kind,
                   'layer_ids': [plan['index'] for plan in self.config['layer_plans']
                                 if plan['index'] != 0 and (kind == 'all' or plan['attention'] == kind)],
                   'stats': duration_stats(histogram), 'duration_ns_counter': sorted(histogram.items())}
                  for kind, histogram in self.pooled.items()]
        return mapping, families, pooled


def geometry_key(geometry):
    return tuple(geometry.get(key) for key in ('tokens_per_sequence','sequences_per_replica','query_rows'))


def rebind_retained_mapping(mapping, structure):
    """Revalidate complete retained cohorts against the current declaration.

    Observations and their conditional layer/role evidence are immutable. A new
    implementation may change physical work, but cannot change the native
    contract, candidate population or inclusive boundary under the old samples.
    Unmapped family examples are deliberately outside this operation.
    """
    from types import SimpleNamespace
    from mindie_profiler.structure_subgraphs import StructureTargets
    from mindie_sim.structure_index import index_digest

    if structure.get('schema_version') != 'mindie-model-structure-index/1':
        raise ValueError('retained_rebinding_requires_complete_structure_index')
    if index_digest(structure) != structure.get('index_id'):
        raise ValueError('structure_index_identity_mismatch')
    execution = structure['execution']
    for key in ('phase', 'tokens', 'context', 'sequences', 'scope', 'replica_axis', 'replicas'):
        if mapping['declared_execution'].get(key) != execution.get(key):
            raise ValueError('retained_execution_geometry_changed:' + key)
    targets = StructureTargets({row['node_id']: row for row in structure['nodes']},
                               structure.get('subgraphs', ()))
    contracts = defaultdict(set)
    for key, target in targets.all.items():
        if target.get('contract') is not None and target.get('event_matchable', True):
            contracts[_freeze(target['contract']), declared_role(target)].add(key)
    windows, roles, receipts = [], {}, []
    for window in mapping['windows']:
        observation = SimpleNamespace(rank_id=window['rank_id'],
                                      source=SimpleNamespace(rank_id=window['rank_id']))
        accumulator = CohortAccumulator(structure['graph_id'], targets, observation,
                                        execution=execution)
        retained, excluded = [], []
        for old in window['cohorts']:
            ids = set(old['target_ids'])
            old_roles = set(mapping['conditional_role_by_cohort_id'][old['cohort_id']])
            refinements = old.get('candidate_refinements', ())
            reason = None
            if (not old.get('contract') or not old_roles or not refinements
                    or sum(item['event_count'] for item in refinements) != old['event_count']
                    or any(item.get('basis') != 'whole_body_topology_conditioned_role'
                           or set(item.get('declared_roles', ())) != old_roles for item in refinements)):
                reason = 'retained_complete_contract_or_topology_evidence_missing'
            elif not ids <= targets.all.keys():
                reason = 'retained_target_missing'
            elif any(targets.all[key].get('event_matchable') is False for key in ids):
                reason = 'retained_target_now_internal_to_native_fusion'
            else:
                candidates = set().union(*(contracts[_freeze(old['contract']), role] for role in old_roles))
                replicas = old['placement']['replica_candidates']
                candidates = {key for key in candidates if targets.all[key].get('replica') in replicas
                              and targets.all[key].get('stage') == old['stage']
                              and targets.all[key].get('phase') == old['phase']}
                if candidates != ids:
                    reason = 'retained_contract_role_candidate_set_changed'
                elif any((match := re.search(r'(?:^|[/:])s\d+\.l(\d+)\.', key)) is None
                         or targets.all[key].get('layer') != int(match[1]) for key in ids):
                    reason = 'retained_layer_identity_changed'
                elif any(role_block(targets.all[key]) not in {None, item['block']}
                         for key in ids for item in refinements):
                    reason = 'retained_role_block_changed'
            declaration = None
            if reason is None:
                declaration, reason = accumulator._cohort(ids)
            if reason is None:
                for key in ('target_kind', 'declared_candidate_instance_count', 'declared_instance_count',
                            'declared_layer_count', 'contract_scope', 'structural_classification'):
                    if _freeze(declaration.get(key)) != _freeze(old.get(key)):
                        reason = 'retained_boundary_or_population_changed:' + key
                        break
                if _freeze((old.get('resource_boundary') or {}).get('native')) != _freeze(
                        (declaration.get('resource_boundary') or {}).get('native')):
                    reason = 'retained_native_fusion_boundary_changed'
            receipt = {'retained_cohort_id': old['cohort_id'],
                       'native_operator_type': old['native_operator_type'],
                       'event_count': old['event_count'], 'reason': reason,
                       'status': 'excluded' if reason else 'rebound'}
            if reason:
                excluded.append({**old, 'rebind_exclusion_reason': reason})
            else:
                key = (old['native_operator_type'], old['device_id'], tuple(sorted(ids)))
                encoded = json.dumps((structure['graph_id'], window['rank_id'], key),
                                     sort_keys=True, separators=(',', ':'), allow_nan=False)
                cohort_id = 'sha256:' + sha256(encoded.encode()).hexdigest()
                retained.append({**old, **declaration, 'cohort_id': cohort_id,
                                 'retained_cohort_id': old['cohort_id']})
                roles[cohort_id] = sorted(old_roles)
                receipt.update(cohort_id=cohort_id,
                               physical_work_changed=_freeze(old['physical_work_per_instance']) !=
                                                     _freeze(declaration['physical_work_per_instance']))
            receipts.append(receipt)
        windows.append({**window, 'cohorts': retained, 'retained_excluded_cohorts': excluded})
    return {**mapping, 'graph_id': structure['graph_id'], 'declared_execution': execution,
            'windows': windows, 'conditional_role_by_cohort_id': roles,
            'cohort_event_window_count': sum(row['event_count'] for window in windows for row in window['cohorts']),
            'retained_population_rebinding': {
                'original_graph_id': mapping['graph_id'], 'current_index_id': structure['index_id'],
                'raw_capture_reads': 0, 'observation_values_changed': False,
                'unknown_families_promoted_from_examples': False, 'cohorts': receipts}}


def prepare_retained_case(entry, case_path, actual_path, prefix, *, retained_body_path=None):
    """Prepare current costing inputs from a pinned complete native population.

    The caller selects a retained actual/mapping pair, rather than looking for a
    result with a favourable error. Original artifacts remain immutable. Source
    references whose declared work changed require separate full-ABI reselection;
    their retained histograms stay visible as exclusions.
    """
    from mindie_sim.structure_index import export_structure_index

    actual_path, case_path, prefix = map(Path, (actual_path, case_path, prefix))
    mapping_path = actual_path.with_name(actual_path.name.removesuffix('.actual.json') + '.mapping.json')
    if prefix.with_suffix('.actual.json').resolve() == actual_path.resolve():
        raise ValueError('retained_operator_inputs_must_not_be_overwritten')
    runtime_before = runtime_identity()
    pins = {'actual': identity(actual_path), 'mapping': identity(mapping_path),
            'current_case': identity(case_path)}
    actual, mapping, case_json = read(actual_path), read(mapping_path), read(case_path)
    if actual['source_identity']['sha256'] != entry['source_identity']['sha256']:
        raise ValueError('retained_operator_source_changed')
    if any(window['source_identity']['sha256'] != actual['source_identity']['sha256']
           for window in mapping['windows']):
        raise ValueError('retained_operator_mapping_source_changed')
    prior_path = Path(entry['report_path'])
    if digest(prior_path) != entry['report_sha256']:
        raise ValueError('retained_operator_body_acceptance_changed')
    prior = read(prior_path)
    if prior['source_identity']['sha256'] != actual['source_identity']['sha256']:
        raise ValueError('retained_operator_body_source_changed')
    pins['current_body_acceptance'] = identity(prior_path)
    equivalence = None
    if actual['body_acceptance_identity']['sha256'] != entry['report_sha256']:
        if (retained_body_path is None
                or digest(retained_body_path) != actual['body_acceptance_identity']['sha256']):
            raise ValueError('retained_operator_body_acceptance_changed')
        previous = read(retained_body_path)
        fields = ('model_declaration', 'segmentation_options', 'forwards', 'geometry_groups', 'per_layer_ms')
        if (previous['source_identity']['sha256'] != prior['source_identity']['sha256']
                or any(previous.get(key) != prior.get(key) for key in fields)):
            raise ValueError('retained_operator_body_population_or_layer_boundary_changed')
        pins['retained_body_acceptance'] = identity(retained_body_path)
        equivalence = {'basis': 'exact_retained_body_and_layer_population_equality',
                       'compared_fields': list(fields), 'forward_count': len(prior['forwards'])}
    expected = [row for row in prior['forwards']
                if geometry_key(row['geometry']) == geometry_key(actual['geometry'])]
    if len(expected) != actual['forward_count']:
        raise ValueError('retained_operator_geometry_population_changed')
    execution = mapping['declared_execution']
    geometry = {key: execution[key] for key in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    if ((geometry['tokens'], geometry['sequences'], geometry['tokens'] * geometry['sequences'])
            != geometry_key(actual['geometry'])
            or geometry['context'] != actual['conditional_context_tokens']):
        raise ValueError('retained_operator_execution_geometry_mismatch')
    index = export_structure_index(case_json, **geometry)
    rebound = rebind_retained_mapping(mapping, index)
    targets = {row['node_id']: row for row in index['nodes']}
    kept, excluded = [], []
    for group in actual.get('source_role_references', ()):
        ids = group['representative_target_ids']
        selected = [targets[key] for key in ids if key in targets]
        if len(selected) != len(ids):
            reason = 'retained_source_program_missing'
        elif ([row['physical_signature'] for row in selected] != group['physical_program_signatures']
              or [row['physical_work'] for row in selected] != group['physical_work_per_program']):
            reason = 'retained_source_program_changed_requires_full_native_reselection'
        else:
            # A representative alone does not verify that all retained layers
            # still share the same program. Keep whole-group reuse conservative.
            reason = None if mapping['graph_id'] == index['graph_id'] else 'retained_source_group_requires_all_layer_revalidation'
        if reason:
            excluded.append({**group, 'rebind_exclusion_reason': reason})
        else:
            kept.append(group)
    del index, targets
    if runtime_identity() != runtime_before or any(identity(pin['path']) != pin for pin in pins.values()):
        raise ValueError('retained_operator_inputs_changed_during_rebinding')
    provenance = {'inputs': pins, 'runtime_source_identity': runtime_before,
                  'raw_capture_reads': 0, 'new_cost_calls': 0,
                  'population_basis': 'same_pinned_complete_body_geometry_population',
                  'body_acceptance_equivalence': equivalence}
    rebound['retained_population_rebinding'].update(provenance)
    current_actual = {**actual, 'source_role_references': kept,
                      'retained_excluded_source_role_references': excluded,
                      'retained_population_reuse': provenance}
    write(prefix.with_suffix('.case.json'), case_json)
    write(prefix.with_suffix('.actual.json'), current_actual)
    write(prefix.with_suffix('.mapping.json'), rebound)
    return current_actual, rebound


def segmentation_config(model_config, prior):
    """Keep the source boundary declaration used to accept the retained bodies."""
    config = dict(model_config)
    declaration = prior.get('model_declaration', {})
    for key in ('source_attention_anchors', 'source_decode_query', 'forward_closure', 'sequence_parallel'):
        if key in declaration:
            config[key] = declaration[key]
    config.update(prior.get('segmentation_options', {}))
    return config


def extract_case(entry, case_paths, output, *, context_tokens=None, geometry_limit=None):
    started=time.perf_counter(); runtime_before=runtime_identity()
    prior=read(entry['report_path'])
    if digest(entry['report_path'])!=entry['report_sha256']:raise ValueError('body_acceptance_identity_changed')
    source_identity=entry['source_identity']; path=Path(source_identity['path'])
    before=(path.stat().st_size,path.stat().st_mtime_ns)
    if digest(path)!=source_identity['sha256']:raise ValueError('capture_sha256_changed')
    if prior['source_identity']['sha256'] != source_identity['sha256']:
        raise ValueError('body_acceptance_source_identity_changed')
    schema_version = source_identity.get('schema_version') or prior['source_identity']['schema_version']
    source=SourceRef('rank_0',0,'csv',str(path),path.name,source_identity['sha256'],before[0],
                    schema_version,'retained_full_capture',mtime_ns=before[1])
    geometries={};expected_by_geometry=defaultdict(dict)
    for forward in prior['forwards']:
        key=geometry_key(forward['geometry'])
        if any(value is None for value in key):raise ValueError('complete_forward_execution_geometry_unresolved')
        geometries[key]=forward['geometry'];expected_by_geometry[key][forward['forward_id']]=forward
    if geometry_limit is not None:
        selected = sorted(geometries, key=lambda key: (-len(expected_by_geometry[key]), key))[:geometry_limit]
        geometries = {key: geometries[key] for key in selected}
    variants=[]
    for case_path in case_paths:
        case_json=read(case_path);case=parse_case(case_json)
        context=(context_tokens if context_tokens is not None
                 else case_json['workload']['requests'][0]['prompt_tokens'])
        config=segmentation_config({**case.model.to_dict(), 'tp':case.runtime.parallel.tp}, prior)
        for key,geometry in geometries.items():
            manifest=export_structure(case,phase='decode',tokens=geometry['tokens_per_sequence'],
                                  sequences=geometry['sequences_per_replica'],context=context,scope='body')
            expected=expected_by_geometry[key];forwards=list(expected.values())
            observation=Observation('rank_0',0,Window(forwards[0]['start_ns'],forwards[-1]['end_ns']),
                            None,[],source,QueryStats('rank_0','complete_decode_bodies'))
            consumer=BodyConsumer(manifest,observation,expected,config)
            variants.append((case_path,case_json,identity(case_path),manifest,consumer,context,config,key,geometry))
    config=variants[0][6]
    if any(item[6]!=config for item in variants):raise ValueError('variant_model_topology_differs')
    def consume(result,events):
        key=geometry_key(result['geometry'])
        for item in variants:
            if item[7]==key:item[4](result,events)
    actual=auto_segment_decode_forwards(kernel_rows(path,rank_id='rank_0',rank_index=0,max_rows=5_000_000,timeout_s=180),
              config,source=source,on_forward=consume,max_detailed_forwards=0,max_samples_per_layer=0)
    if before!=(path.stat().st_size,path.stat().st_mtime_ns):raise ValueError('capture_changed_during_scan')
    if runtime_identity()!=runtime_before or any(identity(item[0])!=item[2] for item in variants):
        raise ValueError('runtime_or_declaration_changed_during_scan')
    pooled_records={}
    for index,(case_path,case_json,declaration_identity,manifest,consumer,context,config,key,geometry) in enumerate(variants):
        variant=case_path.parent.name
        case_id=entry['case_id']+(f'-q{key[0]}-b{key[1]}' if len(geometries)>1 else '')
        mapping,families,pooled=consumer.finish(manifest)
        prefix=output/('body-operator-'+case_id+'-'+variant)
        write(prefix.with_suffix('.case.json'),case_json);write(prefix.with_suffix('.mapping.json'),mapping)
        result={'schema_version':'mindie-body-operator-actual/1','case_id':case_id,'source_case_id':entry['case_id'],'variant':variant,
                'source_identity':source_identity,'body_acceptance_identity':identity(entry['report_path']),
                'case_identity':declaration_identity,'geometry':geometry,'conditional_context_tokens':context,
                'context_basis':'explicit_representative_context' if context_tokens is not None else 'case_request_prompt_tokens',
                'geometry_selection':'largest_complete_forward_populations' if geometry_limit is not None else 'all_complete_populations',
                'unselected_source_forward_count':len(prior['forwards'])-sum(len(expected_by_geometry[key]) for key in geometries),
                'forward_count':len(consumer.forward_ids),'source_forward_count':len(prior['forwards']),
                'geometry_group_count':len(geometries),'counts':dict(consumer.counts),
                'scan_counts':actual['scan_counts'],'families':families,'steady_layer_groups':pooled,
                'source_role_references':consumer.source_roles.finish(duration_stats),
                'population_basis':'complete_verified_body_windows; no_heads_or_auxiliary_forwards',
                'steady_population_basis':'pooled_layer_calls_excluding_layer0',
                'raw_capture_scans':int(index==0),'shared_source_scan':entry['case_id'],
                'source_hash_reads':int(index==0),'elapsed_seconds':round(time.perf_counter()-started,3),
                'runtime_source_identity':runtime_before,'runtime_sources_unchanged':True,
                'maximum_resident_set_size_bytes':peak_rss_bytes()}
        write(prefix.with_suffix('.actual.json'),result)
        if key not in pooled_records:
            pooled_records[key]={'case_id':case_id,'source_case_id':entry['case_id'],'source_identity':source_identity,
                'extraction_identity':identity(prefix.with_suffix('.actual.json')),'geometry':geometry,
                'forward_count':result['forward_count'],'groups':pooled}
    return list(pooled_records.values())



from mindie_sim.cohort_comparison import _predict
from mindie_sim.prediction.operator_analysis import target_graphs
from mindie_sim.prediction.program import RecipeBook
from mindie_sim.prediction.body_defaults import effective_body_declaration
from references import predict_source_role_references, communication_calibration_evidence

def _reference_manifest(case, geometry, actual):
    """Retain reference targets while Sim hashes the complete declared cohort.

    Target discovery uses the existing expanded frontend, without serializing
    every layer's native program metadata. The selected-target API independently
    validates every DP peer and retains the original full structure identity.
    """
    from mindie_sim.structure_selection import select_structure_targets

    effective, _ = effective_body_declaration(
        case, geometry['phase'], tokens=geometry['tokens'], scope=geometry['scope'])
    book = RecipeBook.from_mapping(effective.runtime.kernels)
    graphs = target_graphs(effective, **geometry)
    wanted = {key for group in (actual or {}).get('source_role_references', ())
              for key in group['representative_target_ids']}
    for replica, ops in graphs.items():
        wanted.update(f'rank:{replica}/{op.op_id}' for op in book.expand(ops)
                      if op.family == 'allreduce'
                      or op.family in {'gdn_gating', 'attention'} and op.layer >= 0)
    del graphs, ops, book, effective
    selected = select_structure_targets(case, wanted, **geometry)
    missing = wanted - selected['targets'].keys()
    if missing:
        raise ValueError('source_reference_targets_missing_from_structure:' + ','.join(sorted(missing)))
    return {'graph_id': selected['graph_id'], 'execution': selected['execution'],
            'nodes': list(selected['targets'].values())}


def program_references(case_path, mapping, actual=None):
    case=parse_case(read(case_path)); execution=mapping['declared_execution']
    geometry={key:execution[key] for key in ('phase','tokens','context','sequences','scope')}
    manifest=_reference_manifest(case,geometry,actual)
    if manifest['graph_id']!=mapping['graph_id']:
        raise ValueError('communication_reference_structure_changed')
    case,_=effective_body_declaration(case,geometry['phase'],tokens=geometry['tokens'],scope=geometry['scope'])
    book=RecipeBook.from_mapping(case.runtime.kernels)
    graphs=target_graphs(case,**geometry)
    needed={target['node_id'] for target in manifest['nodes']}
    by_id={f'rank:{replica}/{op.op_id}':op for replica,ops in graphs.items() for op in book.expand(ops)
           if f'rank:{replica}/{op.op_id}' in needed}
    del graphs
    results={}
    for block,role in [('attention','attention_output_communication'),('ffn','ffn_down_communication')]:
        selected=[node for node in manifest['nodes'] if node['family']=='allreduce' and node.get('block')==block]
        signatures={node['physical_signature'] for node in selected}
        if not selected or len(signatures)!=1:
            results[role]={'status':'unresolved','reason':'communication_program_not_homogeneous'}
            continue
        prediction=_predict(case,selected[0],'node',by_id,book)
        results[role]={'status':'reference_only','reason':'native_collective_contract_and_captured_program_boundary_unverified',
                      'per_call_ms':prediction['per_call_ms'],'representative_target_id':selected[0]['node_id'],
                      'target_count':len(selected),'boundary':prediction['boundary'],
                      'evidence_strength':'conditional_topology_region_to_declared_collective',
                      **communication_calibration_evidence()}
    for native,family in [('fused_gdn_gating_kernel','gdn_gating'),('FusedInferAttentionScore','attention')]:
        selected=[node for node in manifest['nodes'] if node['family']==family and node.get('layer',-1)>=0]
        signatures={node['physical_signature'] for node in selected}
        if not selected or len(signatures)!=1:
            results[native]={'status':'unresolved','reason':'source_role_program_not_homogeneous'}
            continue
        target=selected[0]
        if native=='fused_gdn_gating_kernel' and target['operator'].get('metadata',{}).get('caller_implementation')!='vllm_ascend_gdn_decode':
            results[native]={'status':'unresolved','reason':'source_gdn_caller_not_declared'}
            continue
        prediction=_predict(case,target,'node',by_id,book)
        results[native]={'status':'reference_only','reason':'native_tensor_contract_incomplete_or_not_declared',
            'per_call_ms':prediction['per_call_ms'],'representative_target_id':target['node_id'],
            'target_count':len(selected),'boundary':prediction['boundary'],
            'evidence_strength':'conditional_source_role_program; not_a_tensor_contract_cohort',
            'single_device_program':prediction['single_device_program'],
            'observed_duration_used_for_selection':False}
    # The source-reference pass builds its own graph. Keeping this full-model
    # graph alive doubles DP-expanded working state without changing any cost.
    del by_id, book
    results['_source_role_groups'] = predict_source_role_references(case, manifest, actual or {})
    return results


def family_rows(actual,mapping,comparison,references):
    roles=mapping['conditional_role_by_cohort_id']
    grouped={}
    for window in comparison['windows']:
        for row in window['cohorts']:
            role='|'.join(roles[row['cohort_id']])
            grouped.setdefault((row['native_operator_type'],role),[]).append(row)
    results=[]
    for family in actual['families']:
        selected=grouped.get((family['native_operator_type'],family['declared_role']),[])
        compared=[row for row in selected if row['status']=='compared']
        reference=(references.get(family['declared_role']) if family['native_operator_type'].startswith('hcom_')
                   else references.get(family['native_operator_type']) if not compared else None)
        if family['native_operator_type'].startswith('hcom_') and not family['native_operator_type'].startswith('hcom_allReduce'):
            reference={'status':'unresolved','reason':'native_collective_algorithm_not_declared'}
        n=sum(row['observed']['event_count'] for row in compared)
        predicted=sum(row['prediction']['per_call_ms']*1000*row['observed']['event_count'] for row in compared)/n if n else None
        observed=sum(row['observed']['complete_activity_sum_ns'] for row in compared)/n/1000 if n else None
        row={**family,'cohort_count':len(selected),'scored_event_count':n,
             'unscored_event_count':family['observed_us']['count']-n,
             'cohort_status_counts':dict(Counter(item['status'] for item in selected)),
             'predicted_us':predicted,'scored_observed_mean_us':observed,
             'per_call_diff_us':predicted-observed if n else None,
             'relative_error':predicted/observed-1 if n and observed else None,
             'passed_cohort_count':sum(item['accuracy_pass'] is True for item in compared),
             'compared_cohort_count':len(compared),'cohorts':selected,
             'evidence_strength':'tensor_contract_and_conditional_whole_body_role' if selected else 'unmodeled',
             'status':'compared' if compared else 'reference_only' if selected else 'unresolved'}
        if reference:
            row['conditional_program_reference']=reference
            row['status']=reference['status']
            row['evidence_strength']=reference.get('evidence_strength','unresolved')
            row['predicted_reference_us']=reference.get('per_call_ms',0)*1000 if 'per_call_ms' in reference else None
            if row['predicted_reference_us'] is not None:
                diff=row['predicted_reference_us']-family['observed_us']['mean']
                row['reference_per_call_diff_us']=diff
                row['reference_relative_error']=diff/family['observed_us']['mean']
                row['reference_within_tolerance']=(abs(diff)<=15 if family['observed_us']['mean']<=50
                                                    else abs(row['reference_relative_error'])<=.15)
        source_groups = [group for group in references.get('_source_role_groups', ())
                         if group['native_operator_type'] == family['native_operator_type']
                         and group['declared_role'] == family['declared_role']]
        if source_groups:
            if sum(group['observed_us']['count'] for group in source_groups) != family['observed_us']['count']:
                raise ValueError('source_role_reference_population_differs')
            row['conditional_source_role_references'] = source_groups
            row['evidence_strength'] = 'source_reference'
            row['status'] = 'reference_only'
        results.append(row)
    return results
