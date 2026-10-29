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
import resource
import subprocess
import sys
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards, _norm, _norm_start, _anchor, _Row, _TAIL_NAMES
from mindie_profiler.events import Observation, QueryStats, SourceRef, Window
from mindie_profiler.normalized import kernel_rows, shapes, row_from_event
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import StructureMapper, _freeze
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from body_source_role_references import SourceRoleReferences

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'examples/structure/acceptance-20261030-high-concurrency'
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
           Path(__file__).with_name('body_source_role_references.py')]
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
            typed = any('aicpu' in item.lower().replace('_', '') for item in (event.core, event.task_type))
            if typed and event.op_type in _TAIL_NAMES:
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


def extract_case(entry, case_paths, output, *, context_tokens=None, geometry_limit=None):
    started=time.perf_counter(); runtime_before=runtime_identity()
    prior=read(entry['report_path'])
    if digest(entry['report_path'])!=entry['report_sha256']:raise ValueError('body_acceptance_identity_changed')
    source_identity=entry['source_identity']; path=Path(source_identity['path'])
    before=(path.stat().st_size,path.stat().st_mtime_ns)
    if digest(path)!=source_identity['sha256']:raise ValueError('capture_sha256_changed')
    source=SourceRef('rank_0',0,'csv',str(path),path.name,source_identity['sha256'],before[0],
                    source_identity['schema_version'],'retained_full_capture',mtime_ns=before[1])
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
        config=case.model.to_dict();config.update(tp=case.runtime.parallel.tp)
        config.update(prior.get('segmentation_options', {}))
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
                'maximum_resident_set_size_bytes':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))}
        write(prefix.with_suffix('.actual.json'),result)
        if key not in pooled_records:
            pooled_records[key]={'case_id':case_id,'source_case_id':entry['case_id'],'source_identity':source_identity,
                'extraction_identity':identity(prefix.with_suffix('.actual.json')),'geometry':geometry,
                'forward_count':result['forward_count'],'groups':pooled}
    return list(pooled_records.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--case-id',action='append')
    parser.add_argument('--case-dir',type=Path,action='append')
    parser.add_argument('--receipt',type=Path,default=BASE/'decode-forward-auto-acceptance.json')
    parser.add_argument('--output-dir',type=Path,default=BASE)
    parser.add_argument('--context-tokens',type=int,help='Explicit representative context; does not alter measured q/batch')
    parser.add_argument('--geometry-limit',type=int,help='Select the largest N measured populations; preserve total source denominator')
    args = parser.parse_args()
    receipt = read(args.receipt)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    records=[]
    for entry in receipt['cases']:
        if args.case_id and entry['case_id'] not in args.case_id:
            continue
        name=Path(entry['model_structure_identity']['path']).name
        case_paths=[directory/name for directory in args.case_dir] if args.case_dir else [Path(entry['model_structure_identity']['path'])]
        extracted=extract_case(entry,case_paths,args.output_dir,context_tokens=args.context_tokens,
                               geometry_limit=args.geometry_limit);records.extend(extracted)
        print(json.dumps({'case_id':entry['case_id'],'status':'extracted','forward_count':sum(record['forward_count'] for record in extracted),'geometry_groups':len(extracted)}),flush=True)
    write(args.output_dir/'steady-layer-pooled.json',{'schema_version':'mindie-steady-layer-pooled/1',
          'cases':records,'population_basis':'pooled_layer_calls_excluding_layer0',
          'interpretation':'Complete Transformer layer device spans include FFN and real communication; not isolated attention kernels.',
          'source_receipt_identity':identity(args.receipt)})


if __name__ == '__main__':
    main()
