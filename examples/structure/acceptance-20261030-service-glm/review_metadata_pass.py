"""Review typed metadata populations, dependency paths and inclusive responses.

[Role] Audit saved evidence and actual service-regime applications without costs.
[Invariants] Native response is once per build, no price on publish or SFA;
  placement conditions and missing full ABI stay explicit after Body PASS.
[Timeouts & Locks] Bounded retained JSON only; no subprocess, source scan or locks.
[Side-Effect Policy] Writes only this arm's review and concise README.
"""
from build_service_cases import HERE, pin, read, write, summarize

DEST=HERE/'metadata-pass'


def main():
    rp=DEST/'decode-forward-service-replay.json';report=read(rp)
    pops=read(DEST/'observed-populations.json');old_report=read(HERE/'norm-quant-post-pass/decode-forward-service-replay.json')
    old={r['source_case_id']:r for r in old_report['cases'] if r['status']=='compared'}
    current={r['source_case_id']:r for r in report['cases'] if r['status']=='compared'}
    checks,failures,results=0,[],[]

    def check(condition,label):
        nonlocal checks
        checks+=1
        if not condition:failures.append(label)

    check(report['status']=='completed' and len(current)==9,'nine completed results')
    check(report['runtime_generation']['unchanged'],'one unchanged runtime')
    for p in pops['cases']:
        cid=p['case_id'];row=current[cid];before=old[cid]
        case=read(p['case_identity']['path']);previous=read(p['prior_case_identity']['path'])
        for key in ('case_identity','prior_case_identity'):
            check(pin(p[key]['path'])==p[key],cid+'/'+key)
        prior=previous['runtime']['kernels']['service_regimes'];rules=case['runtime']['kernels']['service_regimes']
        check(rules[:-1]==prior and len(rules)==len(prior)+1,cid+'/all prior rules exact')
        for key in ('model','machine','workload'):check(case[key]==previous[key],cid+'/unchanged '+key)
        for key in ('source_identity','observed','geometry'):check(row[key]==before[key],cid+'/unchanged '+key)
        options=case['runtime']['kernels']['lowerings']['sparse_mla_metadata']['options']
        check(options['schedule']=='layer_ordered',cid+'/layer ordered source schedule')
        check(len(options['layer_groups'])==11 and all(len(g)==1 for g in options['layer_groups']),cid+'/11 explicit singleton groups')
        check(len(p['fresh_dependency_paths'])==11,cid+'/complete fresh dependency paths')
        for path in p['fresh_dependency_paths']:
            group=[path['layer_id']]
            check(group in options['layer_groups'],cid+'/source layer group')
            check(path['metadata_call']['view']['layer_group']==group,cid+'/fresh group')
            check(path['metadata_call']['deps']==[path['index_selection']['op_id']],cid+'/selection to metadata')
            check(path['publication']['deps']==[path['metadata_call']['op_id']],cid+'/metadata to publication')
            check(path['publication']['op_id'] in path['attention']['deps'],cid+'/publication to attention')
            check(path['metadata_call']['view']['schedule']=='layer_ordered',cid+'/no preforward hoist')
        ap=p['actual_identity'];check(pin(ap['path'])==ap,cid+'/retained actual identity')
        actual=read(ap['path']);families=[actual['families'][i] for i in p['family_indices']]
        check(all(f['native_operator_type']=='SparseFlashMlaMetadata' for f in families),cid+'/typed family')
        stats=summarize(families)
        check(stats==p['observed'],cid+'/full native histogram')
        check(stats['count']==11*p['forward_count'],cid+'/native calls per body')
        rid=p['rule_id'];rule=rules[-1]
        check(rule['id']==rid and rule['response']=={'fixed_us':stats['mean_us']},cid+'/own native response')
        check(rule['match']['metadata.execution_domain']=='AI_CPU',cid+'/CPU execution domain')
        check(rule['provenance']['body_residual_used'] is False,cid+'/no Body fit')
        check(rule['provenance']['native_abi_admission']=='unchanged_missing_full_ABI',cid+'/no fabricated ABI')
        check(rule['provenance']['evaluation_relation']=='in_sample',cid+'/in sample')
        check(pin(p['placement_evidence_identity']['path'])==p['placement_evidence_identity'],cid+'/placement evidence pin')
        params=row['prediction']['parameters'];hits={r['id']:r for r in params['service_regimes']}
        check(not params['regime_selection']['unmatched'] and len(hits)==len(rules),cid+'/all source rules matched')
        check(hits[rid]['queries']=={'observable_response':11},cid+'/11 inclusive builds only')
        check(hits[rid]['response_us_min']==hits[rid]['response_us_max']==stats['mean_us'],cid+'/applied native mean')
        prior_hits={r['id']:r for r in before['prediction']['parameters']['service_regimes']}
        for prior_id,prior_hit in prior_hits.items():
            for field in ('queries','response_us_min','response_us_max'):
                check(hits[prior_id][field]==prior_hit[field],cid+'/old rule unchanged '+prior_id+'/'+field)
        comp=row['comparison'];error=comp['predicted_ms']/comp['observed_ms']['mean']-1
        check(abs(error-comp['relative_error'])<1e-12,cid+'/Body arithmetic')
        check(comp['passed']==(abs(error)<=.15),cid+'/unrounded pass')
        results.append({'case_id':cid,'forward_count':p['forward_count'],'body':comp,
            'prior_predicted_ms':before['comparison']['predicted_ms'],'metadata_mean_us':stats['mean_us'],
            'metadata_p50_us':stats['p50_us'],'metadata_calls_per_forward':11,
            'measured_metadata_activity_ms_per_forward':11*stats['mean_us']/1000,
            'regime_count':len(rules),'runtime_identity':row['runtime_identity']})
    write(DEST/'service-regime-review.json',{'schema_version':'mindie-metadata-service-review/1',
        'status':'failed' if failures else 'passed','checks':checks,'failures':failures,
        'report_identity':pin(rp),'population_identity':pin(DEST/'observed-populations.json'),
        'reviewer_identity':pin(__file__),'cases':results,'raw_scans':0,'new_costs':0})
    lines=['# GLM layer-ordered AI_CPU metadata response','',
        'The explicit source caller creates 11 singleton MLA metadata groups. Each follows its layer index selection and feeds a separate 1024-word publication before the layer attention. The metadata build alone receives that source’s complete native-call Mean; neither publication nor attention receives a duplicate parameter. No before-forward hoisting is selected.', '',
        'All nine sources retain their previous responses. Parameters are observed and in-sample. Six retained low-source integer-ns examples show MLA layers 3/7 after index-score and before SparseFlashMla on the same stream; they do not identify every capture dependency, binary, or complete native ABI. Thus singleton caller placement is an explicit source condition, not a new strict tensor binding. Native activity is not assumed additive to Body time.', '',
        '| Source | F | Real Mean/P50/P90 ms | Previous Sim ms | New Sim ms | Error | Body | Metadata Mean/P50 us |',
        '|---|---:|---:|---:|---:|---:|---|---:|']
    for r in results:
        c=r['body'];o=c['observed_ms']
        lines.append(f"| {r['case_id']} | {r['forward_count']} | {o['mean']:.6f}/{o['p50']:.6f}/{o['p90']:.6f} | {r['prior_predicted_ms']:.6f} | {c['predicted_ms']:.6f} | {c['relative_error']*100:+.2f}% | {'PASS' if c['passed'] else 'FAIL'} | {r['metadata_mean_us']:.6f}/{r['metadata_p50_us']:.6f} |")
    lines+=['',f"{sum(r['body']['passed'] for r in results)}/9 Body PASS; {checks} population/dependency/application checks and {len(failures)} failures. The standard independent Body review is separate. No raw read or device collection. Runtime changed from 672a to 13862d5e; the numerical delta is not an isolated additive metadata estimate.", '',
        'Reproduce: ../inspect_metadata_placement.py, ../build_metadata_pass.py with fixed 13862d5e on PYTHONPATH; replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90; ../review_metadata_pass.py and review_decode_predictions.py.']
    (DEST/'README.md').write_text('\n'.join(lines)+'\n')
    print({'checks':checks,'failures':failures,'passed':sum(r['body']['passed'] for r in results)})
    return bool(failures)


if __name__=='__main__':
    raise SystemExit(main())
