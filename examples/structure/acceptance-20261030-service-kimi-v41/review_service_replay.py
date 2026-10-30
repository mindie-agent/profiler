"""Independently check calibration observations, invocation counts and body math.

[Role] Audit retained-data service cases without source scans or new predictions.
[Invariants] Calibration is explicitly in-sample; observed service never becomes
  a body residual or a recovered link rate. Every selected rule fires once per
  declared physical invocation, including one entry/exit group for native MC2.
[Timeouts & Locks] Bounded JSON reports; no workers, raw reads or locks.
[Side-Effect Policy] Write one requested review JSON.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / 'examples/structure'


def read(path):
    path=Path(path)
    if path.stat().st_size>50*1024**2:raise ValueError('bounded_review_requires_streaming:'+str(path))
    return json.loads(path.read_text())


def digest(path):
    result=sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def review(report_path, manifest_path):
    report=read(report_path);manifest=read(manifest_path)
    inputs={r['case_id']:r for r in manifest['cases']}
    checks=0;failures=[];cases=[];receipts={}
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    def same(a,b):return abs(a-b)<=1e-9*max(1,abs(a),abs(b))
    for row in report['cases']:
        cid=row.get('source_case_id',row['case_id']);decl=inputs[cid]
        if row['comparison']['status']!='compared':
            check('prediction_deferred_by_population_priority' in row['comparison']['reasons'],cid+':unexpected_incomplete')
            continue
        case=read(decl['sim_case_path']);rules=case['runtime']['kernels']['service_regimes']
        check(digest(decl['sim_case_path'])==row['model_structure_identity']['sha256'],cid+':case_identity')
        check(digest(decl['extraction_path'])==row['extraction_identity']['sha256'],cid+':extraction_identity')
        check(row['source_identity']['sha256']==decl['source']['sha256'],cid+':source_identity')
        observed=read(decl['extraction_path'])
        matches=[g for g in observed['geometry_groups'] if all(g['geometry'].get(k)==row['geometry'].get(k)
                 for k in ['query_rows','tokens_per_sequence','sequences_per_replica'])]
        check(len(matches)==1,cid+':geometry_unique')
        if matches:check(matches[0]['body_forward_span_ms']==row['comparison']['observed_ms'],cid+':body_unchanged')
        check(row['calibration_origin']=='retained_operator_service_in_sample',cid+':origin')
        check(row['calibration_evidence']['evaluation_relation']=='in_sample',cid+':evaluation')
        parameters=row['prediction']['parameters']
        actual={r['id']:r for r in parameters.get('service_regimes',[])}
        check(parameters['regime_selection']['unmatched']==[],cid+':unmatched')
        hit_count=0
        cache={}
        def load_origin(raw):
            path=Path(raw['path']);path=path if path.is_absolute() else ROOT/path
            if str(path) not in cache:
                actual_sha=digest(path)
                check(actual_sha==raw.get('sha256',actual_sha),cid+':retained_receipt_sha')
                cache[str(path)]=read(path);receipts[str(path)]=actual_sha
            return cache[str(path)]
        def original_stats(sample):
            origin=sample['origin']
            if 'cohort_id' in origin:
                retained=load_origin(origin['receipt'])
                cohort=next(c for w in retained['windows'] for c in w['cohorts'] if c['cohort_id']==origin['cohort_id'])
                return {'count':cohort['complete_event_count'],'mean':cohort['duration_ns']['mean']/1000,
                        'p50':cohort['duration_ns'].get('p50',0)/1000}
            if 'native_reference_case' in origin:
                name=('acceptance-20261030-kimi-native-references-5ec8843a/kimi-native-reference-scoreboard.json'
                      if 'kimi' in cid else 'acceptance-20261030-v41-composed-native-5ec8843a/v41-complete-reference-scoreboard.json')
                retained=load_origin({'path':str(EXAMPLES/name)})
                source=next(c for c in retained['cases'] if c['case_id']==origin['native_reference_case'])
                check(source['source_identity']['sha256']==decl['source']['sha256'],cid+':native_source')
                return next(g['observed_us'] for g in source['groups'] if g['group_id']==origin['group_id'])
            retained=load_origin(origin['canonical'])['cases'][0]
            source=next(f for f in retained['families'] if f['native_operator_type']==sample['native_operator_type']
                        and f['declared_role']==sample['declared_role'])
            if 'family' in origin:return source['observed_us']
            return next(g['observed_us'] for g in source['conditional_source_role_references']
                        if g.get('group_id')==origin.get('group_id'))
        for rule in rules:
            label=cid+':'+rule['id'];provenance=rule['provenance']
            samples=provenance['retained_observations'];n=sum(s['observed_us']['count'] for s in samples)
            for sample in samples:check(original_stats(sample)==sample['observed_us'],label+':original_observation')
            total=sum(s['observed_us']['mean']*s['observed_us']['count'] for s in samples)
            check(n==provenance['measurement_population'],label+':sample_count')
            check(same(total/n,rule['response']['fixed_us']),label+':mean_from_observations')
            check(provenance['prediction_values_used'] is False and provenance['whole_body_residual_used'] is False,label+':observation_only')
            check(provenance['fit_source_identity']['sha256']==decl['source']['sha256'],label+':fit_source')
            check(provenance['evaluation_source_identity']['sha256']==decl['source']['sha256'],label+':in_sample_source')
            check(not any(k in rule['match'] for k in ['op_id','layer','case_id','model']),label+':physical_selector')
            check(all(v['min']==v['max'] for v in rule['domain'].values()),label+':exact_declared_shape_domain')
            check(len({s['sample_key'] for s in samples})==len(samples),label+':no_duplicate_observation_group')
            measured=actual.get(rule['id'])
            check(measured is not None,label+':query_record')
            if measured:
                hits=measured['queries'].get('observable_response',0);hit_count+=hits
                check(hits==provenance['expected_invocations_full_dp_cohort'],label+':one_response_per_native_boundary')
                check(measured['response_us_min']==measured['response_us_max']==rule['response']['fixed_us'],label+':response_unchanged')
        compare=row['comparison'];pred=row['prediction']['body_forward_span_ms'];real=compare['observed_ms']['mean']
        check(same(compare['relative_error'],pred/real-1),cid+':relative_error')
        check(compare['passed']==(abs(pred/real-1)<=.15),cid+':pass_threshold')
        execution=row['prediction_execution'].get('execution',{})
        peak=execution.get('peak_rss_bytes',0)
        check(peak<=512*1024**2,cid+':worker_memory')
        cases.append({'case_id':cid,'observed_forwards':compare['observed_forward_count'],
            'observed_mean_ms':real,'predicted_ms':pred,'relative_error':compare['relative_error'],
            'passed':compare['passed'],'rule_count':len(rules),'matched_invocations':hit_count,
            'peak_worker_rss_bytes':peak,'prediction_elapsed_seconds':execution.get('elapsed_seconds')})
    return {'schema_version':'mindie-observed-service-replay-independent-review/1',
        'report_identity':{'path':str(Path(report_path).resolve()),'sha256':digest(report_path)},
        'manifest_identity':{'path':str(Path(manifest_path).resolve()),'sha256':digest(manifest_path)},
        'checks':checks,'failures':failures,'status':'passed' if not failures else 'failed',
        'cases':cases,'observation_receipts':receipts,'raw_event_reads':0,'new_predictions':0,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--report',required=True);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    value=review(a.report,a.manifest);Path(a.output).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k] for k in ['status','checks','failures','peak_rss_bytes']}))
    raise SystemExit(bool(value['failures']))
