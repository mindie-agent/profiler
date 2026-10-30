"""Execute retained native service domains through existing Sim program costs.

[Role] Refresh complete source-conditioned native references without raw scans.
[Invariants] All declared calls, complete observed histograms and whole native
  program boundaries are preserved. Calibration does not upgrade ABI evidence;
  each reported prediction comes from Engine execution, never a copied mean.
[Timeouts & Locks] Serial bounded source workers; each source <=512 MiB/180s.
[Side-Effect Policy] New local reference reports only; no case or runtime edits.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import argparse
import gc
import json
from pathlib import Path
import subprocess
import sys
import time

from build_qwen_a3_service_cases import physical_ops
from body_source_role_references import canonical, predict_source_role_references
from compare_body_operator_families import prediction_runtime_identity
from compare_glm_native_partitions import peak_rss
from replay_body_operator_families import read, write, identity, duration_stats

HERE = Path(__file__).resolve().parent
GLM78 = HERE / 'acceptance-20261030-service-qwen-a3/glm78-native'


def verify(pin):
    current = identity(pin['path'])
    if current['sha256'] != pin['sha256']:
        raise ValueError('retained_input_changed:' + pin['path'])


def member(value, pointer):
    for key in pointer.split('/'):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def observed_population(kind, case_id, rule):
    provenance = rule['provenance']
    if kind == 'glm78':
        path = GLM78 / (case_id + '-native-partitions.json')
        retained = read(path)
        native = rule.get('execution', {}).get('native_kernel') or provenance['native_operator_type']
        selected = [g for g in retained['partitions'] if g['native_operator_type'] == native]
        if not selected or any(g['native_abi'] != selected[0]['native_abi'] for g in selected):
            raise ValueError('native_service_requires_one_retained_ABI_domain')
        histogram, layers = Counter(), Counter()
        for group in selected:
            histogram.update(dict(group['duration_ns_counter']))
            layers.update({int(k): v for k, v in group['layer_counts'].items()})
        return dict(native=native, histogram=histogram, layer_ids=sorted(layers),
            native_abi=selected[0]['native_abi'], forward_count=retained['forward_count'],
            source_identity=retained['source_identity'], retained_identity=identity(path),
            body_acceptance_identity=retained['body_acceptance_identity'],
            observed_contract=None, evidence_strength='full_native_abi',
            original_case_identity=retained['case_identity'])
    verify(provenance['input_identity'])
    inputs = read(provenance['input_identity']['path'])
    candidate, = [c for c in inputs['candidates'] if c['candidate_id'] == provenance['candidate_id']]
    source, = candidate['source_populations']
    if source['case_id'] != case_id:
        raise ValueError('native_service_source_case_mismatch')
    verify(source['timing_identity'])
    retained = read(source['timing_identity']['path'])
    histogram = Counter()
    for pointer in source['timing_members']:
        histogram.update(dict(member(retained, pointer)))
    if histogram != Counter(dict(candidate['duration_ns_counter'])):
        raise ValueError('native_service_complete_histogram_changed')
    domain = candidate['applicability_domain']
    return dict(native=domain['native_operator_type'], histogram=histogram,
        layer_ids=None, native_abi=domain.get('native_abi'),
        observed_contract=None, evidence_strength='source_symbol_retained_group',
        forward_count=source['forward_count'], source_identity=source['source_identity'],
        retained_identity=source['timing_identity'], body_acceptance_identity=source['body_acceptance_identity'],
        original_case_identity=source['declared_case_identity'],
        source_symbol_domain=domain, example_ABI_is_not_full_population_ABI=True)


def selected_programs(rule, parsed, ops):
    from mindie_sim.prediction.service_regimes import axis_equal, lookup
    selected = []
    for op in ops:
        metadata = dict(op.metadata)
        axes = {**op.to_dict(include_work=False),
                'hardware': parsed.machine.hardware_key or parsed.machine.sku,
                'dtype': op.dtype or parsed.model.compute_dtype,
                'kernel': metadata.get('device_kernel_group', {}).get('kernel',
                           metadata.get('kernel', metadata.get('kernel_name', op.recipe)))}
        if all(axis_equal(lookup(axes, key), value) for key, value in rule['match'].items()):
            group = metadata.get('device_kernel_group')
            members = [o for o in ops if dict(o.metadata).get('device_kernel_group', {}).get('id') == group['id']] if group else [op]
            if group and (not group['entry'] or sum(dict(o.metadata)['device_kernel_group']['exit'] for o in members) != 1):
                raise ValueError('native_group_requires_unique_entry_exit')
            selected.append((op, members))
    return selected


def worker(row, kind, runtime_commit):
    from mindie_sim.structure import export_structure
    started = time.perf_counter()
    before = prediction_runtime_identity()
    pin = identity(row['sim_case_path'])
    if pin['sha256'] != row['model_declaration']['sha256']:
        raise ValueError('body_case_identity_changed')
    raw = read(pin['path']); geometry = row['replay_input_pins']['primary_geometry']
    parsed, ops = physical_ops(raw, geometry)
    manifest = export_structure(parsed, phase='decode', tokens=geometry['tokens_per_sequence'],
        context=geometry['context_tokens'], sequences=geometry['sequences_per_replica'], scope='body')
    nodes = {n['op_id']: n for n in [*manifest['nodes'], *manifest.get('resource_operators', [])] if n['replica'] == 0}
    rules = [r for r in raw['runtime']['kernels'].get('service_regimes', [])
             if r.get('execution', {}).get('kind') == 'joint_native'
             or r.get('provenance', {}).get('native_operator_type') in {'MoeDistributeDispatchV2', 'MoeDistributeCombineV2'}]
    groups, cost_inputs, compact_nodes = [], {}, {}
    population = None
    for rule in rules:
        observed = observed_population(kind, row['case_id'], rule)
        population = observed
        histogram = observed['histogram']; count = sum(histogram.values()); forwards = observed['forward_count']
        selected = selected_programs(rule, parsed, ops)
        if len(selected) * forwards != count:
            raise ValueError('native_service_declared_observed_multiplicity_differs:' + rule['id'])
        if observed['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_service_capture_differs')
        layers = sorted({op.layer for op, _ in selected})
        if observed['layer_ids'] is not None and layers != observed['layer_ids']:
            raise ValueError('native_service_layer_population_differs')
        components = Counter()
        signatures = []
        for op, members in selected:
            targets = [nodes[o.op_id] for o in members]
            # Every distinct declared physical program is priced; multiplicity
            # supplies weights within the intact observed native population.
            physical = [(t['physical_signature'], t['physical_work']) for t in targets]
            key = sha256(canonical(physical).encode()).hexdigest()
            components[key] += 1
            signatures.extend(t['physical_signature'] for t in targets)
            if key not in cost_inputs:
                cost_inputs[key] = {'program_set_key': key, 'representative_replica': 0,
                    'representative_target_ids': [t['node_id'] for t in targets],
                    'physical_program_signatures': [t['physical_signature'] for t in targets],
                    'physical_work_per_program': [t['physical_work'] for t in targets],
                    'observed_us': duration_stats(histogram, 1000),
                    'observed_activity_sum_ns': sum(ns*n for ns, n in histogram.items())}
                compact_nodes.update((t['node_id'], t) for t in targets)
        role = rule.get('match', {}).get('metadata.fusion_role') or rule['match']['recipe']
        groups.append({'group_id': rule['id'], 'retained_group_id': rule['id'],
            'native_operator_type': observed['native'], 'declared_role': role,
            'native_abi': observed['native_abi'], 'observed_contract': observed['observed_contract'],
            'evidence_strength': observed['evidence_strength'], 'layer_ids': layers,
            'observed_us': duration_stats(histogram, 1000), 'duration_ns_counter': sorted(histogram.items()),
            'observed_activity_sum_ns': sum(ns*n for ns, n in histogram.items()),
            'cost_components': [{'program_set_key': k, 'declared_occurrences': n,
                                 'per_native_call_weight': n / len(selected)} for k, n in components.items()],
            'physical_program_signatures': sorted(set(signatures)),
            'observed_population_identity': observed['retained_identity'],
            'source_correspondence': {'boundary_relation': 'complete_declared_native_service_boundary',
                'retained_observation_scope': observed['evidence_strength'],
                'complete_native_calls': count, 'declared_calls_per_forward': len(selected),
                'source_symbol_domain': observed.get('source_symbol_domain'),
                'example_ABI_is_not_full_population_ABI': observed.get('example_ABI_is_not_full_population_ABI', False)},
            'conditions': ['Existing logical source work, context and unobserved scalar values stay declared conditions.',
                'Whole-call calibration is explicitly in-sample and does not promote a reference to strict.',
                'Activity residuals do not add to Body wall time.'],
            'strict_accuracy_implied': False, 'strict_accuracy_pass': None,
            'occurrence_binding_implied': False, 'additional_budget_allowed': False,
            'calibration_origin': 'observed', 'evaluation_relation': 'in_sample'})
    if population is None:
        raise ValueError('no_retained_native_service_rules')
    compact = {k: manifest[k] for k in ('graph_id', 'execution')}
    compact['nodes'] = list(compact_nodes.values())
    del manifest, nodes, ops
    gc.collect()
    costs = predict_source_role_references(parsed, compact, {
        'source_role_references': list(cost_inputs.values()), 'forward_count': population['forward_count']})
    by_key = {x['program_set_key']: x for x in costs}
    for group in groups:
        duration = sum(by_key[c['program_set_key']]['predicted_reference_us'] * c['per_native_call_weight']
                       for c in group['cost_components'])
        count = group['observed_us']['count']; forwards = population['forward_count']
        executions = []
        for component in group['cost_components']:
            cost = by_key[component['program_set_key']]
            ev = cost['executed_service_response']
            matching = [r for r in ev['rules'] if r['id'] == group['group_id']]
            if len(matching) != 1 or sum(matching[0]['queries'].values()) != 1:
                raise ValueError('native_service_not_executed_exactly_once:' + group['group_id'])
            executions.append({**component, 'declared_programs': cost['declared_programs'],
                'predicted_program_set_us': cost['predicted_reference_us'], 'executed_service_response': ev})
        group.update(prediction_status='reference_only', accuracy_status='reference_only',
            reference_boundary='one_complete_native_program_or_device_kernel_group',
            predicted_reference_us=duration, declared_programs=executions,
            calls_per_forward=count/forwards,
            observed_activity_ms_per_forward=group['observed_activity_sum_ns']/1e6/forwards,
            predicted_service_ms_per_forward=duration*count/1000/forwards,
            reference_activity_error_ms_per_forward=(duration-group['observed_us']['mean'])*count/1000/forwards,
            per_call_reference_diff_us=duration-group['observed_us']['mean'])
    if prediction_runtime_identity() != before or identity(pin['path']) != pin:
        raise ValueError('native_service_runtime_or_case_changed')
    rss = peak_rss()
    if rss > 512*1024**2:
        raise MemoryError('native_service_reference_exceeds_512MiB')
    return {'schema_version':'mindie-native-body-reference/1', 'status':'completed',
        'case_id':row['case_id'], 'source_identity':population['source_identity'],
        'case_identity':pin, 'actual_identity':population['retained_identity'],
        'partition_identity':population['retained_identity'],
        'body_acceptance_identity':population['body_acceptance_identity'],
        'geometry':geometry, 'conditional_context_tokens':geometry['context_tokens'],
        'forward_count':population['forward_count'], 'groups':groups, 'unresolved':[], 'strict_compared':0,
        'native_event_count':sum(g['observed_us']['count'] for g in groups),
        'referenced_event_count':sum(g['observed_us']['count'] for g in groups),
        'runtime_source_commit':runtime_commit, 'runtime_source_identity':before,
        'runtime_sources_unchanged':True, 'execution':{'new_program_sets':len(cost_inputs),
            'raw_capture_reads':0,'old_prediction_reused':False,'elapsed_seconds':time.perf_counter()-started,
            'maximum_resident_set_size_bytes':rss}, 'producer_identity':identity(__file__)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--kind',choices=('glm78','livepre'),required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--runtime-source-commit',required=True)
    p.add_argument('--worker-case');args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    manifest=read(args.manifest)
    if args.worker_case:
        row,=[x for x in manifest['cases'] if x['case_id']==args.worker_case]
        result=worker(row,args.kind,args.runtime_source_commit)
        write(args.output_dir/(args.worker_case+'.json'),result);return
    cases=[];attempts=[];started=time.perf_counter()
    for row in manifest['cases']:
        cmd=[sys.executable,str(Path(__file__).resolve()),'--manifest',str(args.manifest.resolve()),
             '--kind',args.kind,'--output-dir',str(args.output_dir.resolve()),
             '--runtime-source-commit',args.runtime_source_commit,'--worker-case',row['case_id']]
        with (args.output_dir/(row['case_id']+'.log')).open('w') as log:
            child=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=180)
        attempts.append({'case_id':row['case_id'],'command':cmd,'returncode':child.returncode,'timeout_seconds':180})
        write(args.output_dir/'execution.json',{'attempts':attempts,'input_identity':identity(args.manifest)})
        if child.returncode:raise SystemExit('native service worker failed; see log')
        cases.append(read(args.output_dir/(row['case_id']+'.json')))
        print(json.dumps({'case_id':row['case_id'],'groups':len(cases[-1]['groups']),'completed':len(cases)}),flush=True)
    result={'schema_version':'mindie-native-body-reference-batch/1','status':'completed','cases':cases,
        'runtime_source_commit':args.runtime_source_commit,'runtime_source_identity':cases[0]['runtime_source_identity'],
        'strict_compared':0,'input_identity':identity(args.manifest),'raw_capture_reads':0,
        'elapsed_seconds':time.perf_counter()-started}
    write(args.output_dir/'native-service-reference-scoreboard.json',result)


if __name__=='__main__':main()
