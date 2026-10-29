"""Join completed conditional V4.1 body predictions to seven retained captures.

[Role] Reuse the parent simulation ledger, its explicit retries and measured bodies.
[Invariants] Fourteen workload conditions remain seven captures; no nearest-error
  selection. A cohort-ready prediction and rank0 device envelope are conditional
  counterparts. Timeout attempts and per-run package identities remain visible.
[Timeouts & Locks] Bounded metadata files only; no prediction, raw CSV or locks.
[Side-Effect Policy] Write one independently validated comparison JSON/Markdown.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path


def read(path):
    path = Path(path)
    if path.stat().st_size >= 32 * 1024**2:
        raise ValueError('oversized_metadata')
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest(),
            'size_bytes':path.stat().st_size}


def run(original_path, retry_path, operator_arms, output):
    original, retry, arms = read(original_path), read(retry_path), read(operator_arms)
    checks = 0
    def check(value, message):
        nonlocal checks
        checks += 1
        if not value:
            raise ValueError(message)
    def verify(record):
        now = identity(record['path'])
        check(now['sha256'] == record['sha256'], 'evidence_hash_changed:'+record['path'])
        if 'size_bytes' in record:
            check(now['size_bytes'] == record['size_bytes'], 'evidence_size_changed')
    check(retry['baseline']['sha256'] == identity(original_path)['sha256'], 'retry_baseline_hash')
    check(len(original['rows']) == 14 and len(retry['rows']) == 3, 'expected_14_conditions_3_retries')
    check(Counter(row['status'] for row in original['rows']) == {'completed':11,'timeout':3}, 'original_outcomes')
    keyed = {(row['input']['sha256'],row['condition']):row for row in original['rows']}
    check(len(keyed) == 14, 'unique_original_input_condition')
    retry_keyed = {(row['input']['sha256'],row['condition']):row for row in retry['rows']}
    check(len(retry_keyed) == 3, 'unique_retry_input_condition')
    for key,new in retry_keyed.items():
        old = keyed[key]
        check(old['status'] == 'timeout' and new['status'] == 'completed', 'retry_only_failed_condition')
        check(old['input'] == new['input'] and old['geometry'] == new['geometry'], 'retry_actual_input_geometry_equal')
        check(new['same_input'] and new['same_geometry'], 'producer_retry_join_flags')
        check(new['baseline_package'] == old['package_start'], 'retry_previous_package')
        check(new['budget_seconds'] == old['budget_seconds'] == 60, 'same_60_second_budget')
    for row in original['rows'] + retry['rows']:
        verify(row['input'])
        check(row['package_start'] == row['package_end'], 'runtime_package_changed_during_worker')
        check(row['full_model_layers'] == row['executed_layers'] == 40, 'full_40_layer_scope')
        check(row['case_patch'] == {} and not row['diagnostic'], 'no_reduced_or_patched_case')
        check(row['budget_seconds'] == 60 and row['memory']['peak_rss_bytes'] <= 512*1024**2, 'worker_resource_budget')
        if row['status'] == 'completed':
            check(row['worker_exit_code'] == 0 and row['duration_ms'] > 0 and row['wall_seconds'] <= 60, 'completed_worker_valid')
            for engine in row['engines']:
                check(engine['live_tasks'] == engine['live_programs'] == 0 and not any(engine['live_allocated'].values()), 'completed_engine_drained')
        else:
            check(row['status'] == 'timeout' and row['duration_ms'] is None and row['worker_exit_code'] != 0, 'timeout_not_a_prediction')
    observations = {}
    for cid,case in arms['baseline']['cases'].items():
        verify(case['actual_identity'])
        actual = read(case['actual_identity']['path'])
        verify(actual['body_acceptance_identity'])
        body_path = Path(actual['body_acceptance_identity']['path'])
        body = read(body_path)
        manifest_path = body_path.with_name('decode-forward-auto-cases.json')
        manifest = read(manifest_path)
        declarations = [c for c in manifest['cases'] if c['case_id'] == cid]
        check(len(declarations) == 1, 'one_capture_manifest_declaration')
        declaration = declarations[0]
        check(declaration['source']['sha256'] == actual['source_identity']['sha256'] == body['source_identity']['sha256'], 'same_retained_raw_source')
        rank = declaration['scenario_evidence']['selected_rank']
        check(rank == 'dp0_pp0_tp0_dcp0_ep0_rank0', 'selected_capture_is_rank0')
        groups = [g for g in body['geometry_groups'] if all(g['geometry'][k] == case['geometry'][k]
                  for k in ('query_rows','tokens_per_sequence','sequences_per_replica'))]
        check(len(groups) == 1, 'one_matching_observed_execution_geometry')
        group = groups[0]
        check(group['body_forward_span_ms']['count'] == case['forward_count'], 'same_complete_forward_population')
        check(len(group['per_layer_ms']) == 40 and {r['layer_id'] for r in group['per_layer_ms']} == set(range(40)), 'all_40_measured_layers')
        for layer in group['per_layer_ms']:
            check(layer['stats']['count'] == case['forward_count'], 'layer_complete_forward_count')
        observations[cid] = {'actual_identity':case['actual_identity'],
            'body_identity':actual['body_acceptance_identity'],'capture_manifest_identity':identity(manifest_path),
            'source_identity':actual['source_identity'],'selected_rank':rank,
            'rank_id_in_csv':group['rank_id'],'device_id':group['device_id'],
            'geometry':group['geometry'],'full_model_layers':40,
            'body_forward_span_ms':group['body_forward_span_ms'],
            'metric_boundary':body['metric_boundary'],'span_start_basis':body['span_start_basis'],
            'span_end_basis':body['span_end_basis'],
            'geometry_basis':'shape-derived execution geometry; not active-valid-token or peer-load proof'}
    check(len(observations) == 7, 'seven_unique_captures')
    rows = []
    for cid,observation in observations.items():
        source_case_identity = arms['source_symmetric_conditional']['cases'][cid]['case_identity']
        verify(source_case_identity)
        raw = read(source_case_identity['path'])
        declared_conditions = raw['runtime']['metadata']['source_scenario']['conditions']
        if isinstance(declared_conditions,list):
            declared_conditions = {c.get('name',c.get('condition')):c for c in declared_conditions}
        b = observation['geometry']['sequences_per_replica']
        for condition,sequences in [('single_active_rank0',[b]+[0]*7),('symmetric_declared',[b]*8)]:
            key=(source_case_identity['sha256'],condition)
            old=keyed[key];selected=retry_keyed.get(key,old)
            geometry={'phase':'decode','tokens':1,'sequences':sequences,'context':2048,'scope':'body'}
            check(selected['geometry']==geometry, 'prediction_geometry_matches_capture_execution_and_condition')
            check(declared_conditions[condition]['sequences']==sequences, 'condition_matches_source_case_metadata')
            result_geometry=selected['result_geometry']
            check(result_geometry['tokens_per_sequence']==1 and result_geometry['context_tokens']==2048
                  and result_geometry['sequences_per_replica']==sequences, 'public_prediction_result_geometry')
            real=observation['body_forward_span_ms']
            def attempt(item):
                return {k:item[k] for k in ('status','error','runtime_revision','runtime_root','package_start','package_end',
                    'input','condition','geometry','budget_seconds','wall_seconds','cpu_seconds','memory','duration_ms','worker_exit_code')}
            attempts=[attempt(old)] + ([attempt(selected)] if key in retry_keyed else [])
            rows.append({'source_case_id':cid,'condition':condition,'observation':observation,
                'prediction':{'duration_ms':selected['duration_ms'],'executed_layers':selected['executed_layers'],
                    'result_geometry':result_geometry,'modeling_status':selected['modeling_status'],
                    'model_coverage':selected['model_coverage'],'unmodeled_features':selected['unmodeled_features'],
                    'runtime_revision':selected['runtime_revision'],'package':selected['package_start'],
                    'family_activity':selected['family_activity'],
                    'family_activity_boundary':selected['activity_boundary'],
                    'family_activity_additive_body_budget':False},
                'input_identity':source_case_identity,'attempt_history':attempts,
                'comparison':{'status':'conditional_reference','predicted_minus_observed_mean_ms':selected['duration_ms']-real['mean'],
                    'relative_difference_vs_mean':selected['duration_ms']/real['mean']-1,
                    'relative_difference_vs_p50':selected['duration_ms']/real['p50']-1,
                    'strict_accuracy_eligible':False,'selected_by_error':False,
                    'boundary_relation':'Sim complete declared EP/DP-cohort readiness vs retained rank0 first/last-device envelope',
                    'context_relation':'2048 source scenario; active KV length not observed per forward'}})
    check(len(rows)==14 and len({r['source_case_id'] for r in rows})==7,'conditions_are_not_captures')
    report={'schema_version':'mindie-v41-body-source-condition-comparison/1','status':'completed',
        'original_prediction_ledger':identity(original_path),'retry_prediction_ledger':identity(retry_path),
        'operator_arm_index':identity(operator_arms),'producer_identity':identity(__file__),
        'runtime_change_for_retries':retry['runtime_change'],'checks':checks,'source_count':7,'condition_count':14,
        'unique_observed_forward_count':sum(o['body_forward_span_ms']['count'] for o in observations.values()),
        'original_attempt_outcomes':dict(Counter(r['status'] for r in original['rows'])),
        'retry_attempt_outcomes':dict(Counter(r['status'] for r in retry['rows'])),
        'final_condition_outcomes':{'completed':14},'raw_capture_reads':0,'new_predictions':0,
        'baseline_66_case_selection_changed':False,'cross_condition_accuracy_denominator':False,
        'maximum_worker_rss_bytes':max(r['memory']['peak_rss_bytes'] for r in original['rows']+retry['rows']),
        'rows':rows}
    output.write_text(json.dumps(report,indent=2)+'\n')
    lines=['# V4.1 source-body conditions against seven retained captures','',
           f"Seven captures / {report['unique_observed_forward_count']} measured complete forwards; fourteen explicit peer-load conditions. This is an additional conditional comparison, not a replacement for the 66-case baseline. Neither condition is selected by smaller error.",'',
           '| Capture | Execution B | Forwards | Real mean / P50 / P90 ms | Single rank0-active ms | Difference vs mean | Symmetric [B]×8 ms | Difference vs mean |',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for cid in sorted(observations,key=lambda x:observations[x]['geometry']['sequences_per_replica']):
        a,b=[next(r for r in rows if r['source_case_id']==cid and r['condition']==condition)
             for condition in ('single_active_rank0','symmetric_declared')]
        o=observations[cid];s=o['body_forward_span_ms']
        lines.append(f"| {cid.removeprefix('a5_v41_fp8_tp1_dp8_ep8_')} | {o['geometry']['sequences_per_replica']} | {s['count']} | {s['mean']:.3f} / {s['p50']:.3f} / {s['p90']:.3f} | {a['prediction']['duration_ms']:.3f} | {a['comparison']['relative_difference_vs_mean']:+.1%} | {b['prediction']['duration_ms']:.3f} | {b['comparison']['relative_difference_vs_mean']:+.1%} |")
    lines += ['', 'All predictions execute the full declared 40-layer body. The original ledger has 11 successes and three 60-second timeouts; the three explicit c226 retries complete with exactly the same input SHA and geometry under the same 60-second budget. Both attempts remain in the JSON. Each package_start equals package_end; every worker stays below 512 MiB.', '',
              'Real values are the retained rank0 device-event envelopes. Sim duration is completion of the declared cohort from input readiness; endpoint and peer-load equivalence are not observed. Shape-derived B is execution geometry, not proof of valid active requests on every DP rank. Source programs, route-mask/group-list values and per-forward active KV length remain conditional.', '',
              'Family activity is retained only as a nonadditive diagnostic across all declared participants; it includes contention and is not a decomposition of rank0 wall time.', '',
              f"Validation: {checks} checks, zero raw reads and zero new predictions. Unique observed population is counted once; no 14-capture or combined-accuracy claim.",'']
    output.with_suffix('.md').write_text('\n'.join(lines))
    print(json.dumps({k:report[k] for k in ('status','checks','source_count','condition_count','unique_observed_forward_count','maximum_worker_rss_bytes')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--original',type=Path,required=True)
    parser.add_argument('--retries',type=Path,required=True)
    parser.add_argument('--operator-arms',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    run(a.original,a.retries,a.operator_arms,a.output)
