"""Audit the second arm against the immutable first arm and retained native histograms.

[Role] Check native counts, response provenance and first-arm preservation.
[Invariants] No prediction or raw scan; an in-sample Body pass does not prove ABI.
[Timeouts & Locks] Finite saved receipts, no locks or subprocesses.
[Side-Effect Policy] Writes only second-pass review/README.
"""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json

from build_service_cases import HERE, read, pin, write, summarize

SECOND=HERE/'second-pass'


def main():
    checks=0;failures=[]
    def check(test,message):
        nonlocal checks
        checks+=1
        if not test:failures.append(message)
    first=read(HERE/'decode-forward-service-replay.json')
    report=read(SECOND/'decode-forward-service-replay.json')
    pop=read(SECOND/'observed-populations.json')
    first_results={r['source_case_id']:r for r in first['cases'] if r['status']=='compared'}
    results={r['source_case_id']:r for r in report['cases'] if r['status']=='compared'}
    check(report['status']=='completed' and len(results)==6,'six completed primary results')
    check(report['runtime_generation']==first['runtime_generation'],'same fixed runtime generation')
    summaries=[]
    correction=read(SECOND/'selector-correction.json')
    previous_rules={r['case_id']:r for r in correction['cases']}
    initial=read(SECOND/'initial-selector-attempt-replay.json')
    initial_manifest_pin=pin(SECOND/'initial-selector-attempt-manifest.json')
    check(initial_manifest_pin['sha256']==initial['manifest_identity']['sha256'],'initial manifest retained under explicit attempt filename')
    for c in pop['cases']:
        cid=c['case_id'];before=read(c['first_arm_case_identity']['path']);case=read(c['case_identity']['path'])
        check(pin(c['case_identity']['path'])==c['case_identity'],cid+' new case identity')
        check(pin(c['first_arm_case_identity']['path'])==c['first_arm_case_identity'],cid+' first case identity')
        original=before['runtime']['kernels']['service_regimes'];rules=case['runtime']['kernels']['service_regimes']
        restored=deepcopy(case)
        restored['runtime']['kernels']['service_regimes']=[previous_rules[cid]['initial_rule']
            if r['id']=='groupedmatmul-observed-second' else r for r in rules]
        restored_hash=sha256((json.dumps(restored,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        check(restored_hash==previous_rules[cid]['initial_case_identity']['sha256'],cid+' initial input reproducible from retained exact selector rule')
        check(rules[:6]==original,cid+' first six rules unchanged')
        check(len(rules)==9 and len({r['id'] for r in rules})==9,cid+' three distinct added rules')
        for key in ('model','machine','workload'):
            check(case[key]==before[key],cid+' unchanged '+key)
        check({k:v for k,v in case['runtime']['kernels'].items() if k!='service_regimes'}==
              {k:v for k,v in before['runtime']['kernels'].items() if k!='service_regimes'},cid+' unchanged physical program selection')
        row=results[cid];old=first_results[cid]
        check(row['source_identity']==old['source_identity'],cid+' unchanged source')
        check(row['observed']==old['observed'],cid+' unchanged full observed population')
        check(row['geometry']==old['geometry'],cid+' unchanged geometry')
        check(row['calibration_evidence']['evaluation_role']=='in_sample',cid+' in_sample evidence')
        check(row['calibration_evidence']['evaluation_relation']=='in_sample',cid+' normalized relation metadata')
        params=row['prediction']['parameters'];hits={g['id']:g for g in params['service_regimes']}
        check(not params['regime_selection']['unmatched'],cid+' all regimes selected')
        first_hits={g['id']:g for g in old['prediction']['parameters']['service_regimes']}
        for rid,h in first_hits.items():
            check(hits[rid]['queries']==h['queries'],cid+' unchanged original native hits '+rid)
        new_groups=[]
        for group in c['groups']:
            ap=group['actual_identity'];check(pin(ap['path'])==ap,cid+' retained actual pin')
            actual=read(ap['path']);families=[actual['families'][i] for i in group['family_indices']]
            stats=summarize(families)
            check(stats==group['observed'],cid+' retained full native population '+group['native_operator_type'])
            check(stats['count']==c['forward_count']*group['calls_per_forward'],cid+' native multiplicity')
            rid=group['rule_id'];rule=next(r for r in rules if r['id']==rid)
            check(rule['response']=={'fixed_us':stats['mean_us']},cid+' native mean response')
            check(rule['provenance']['body_residual_used'] is False,cid+' no Body residual input')
            check(hits[rid]['queries']=={'observable_response':group['calls_per_forward']},cid+' once per native boundary '+rid)
            check(abs(hits[rid]['response_us_min']-stats['mean_us'])<1e-10 and
                  abs(hits[rid]['response_us_max']-stats['mean_us'])<1e-10,cid+' response exactly observed mean')
            check(all(not isinstance(v,list) for v in rule['match'].values()),cid+' scalar dotted shape axes')
            new_groups.append({'native_operator_type':group['native_operator_type'],'calls_per_forward':group['calls_per_forward'],
                               'count':stats['count'],'mean_us':stats['mean_us'],'p50_us':stats['p50_us'],
                               'hits':hits[rid]['queries']['observable_response']})
        obs=row['comparison']['observed_ms'];sim=row['comparison']['predicted_ms'];err=(sim/obs['mean']-1)*100
        check(row['comparison']['passed']==(abs(err)<=15),cid+' Body tolerance')
        summaries.append({'case_id':cid,'forward_count':c['forward_count'],'real_ms':obs,
                          'first_arm_sim_ms':old['comparison']['predicted_ms'],'second_arm_sim_ms':sim,
                          'relative_error_pct':err,'passed':row['comparison']['passed'],'added_groups':new_groups})
    result={'schema_version':'mindie-observed-service-replay-review/1','status':'passed' if not failures else 'failed',
            'checks':checks,'failures':failures,'cases':summaries,'first_replay_identity':pin(HERE/'decode-forward-service-replay.json'),
            'replay_identity':pin(SECOND/'decode-forward-service-replay.json'),'population_identity':pin(SECOND/'observed-populations.json'),
            'reviewer_identity':pin(__file__),'execution':{'raw_scans':0,'new_costs':0}}
    result['selector_attempt_history']={'correction_identity':pin(SECOND/'selector-correction.json'),
        'initial_replay_identity':pin(SECOND/'initial-selector-attempt-replay.json'),
        'initial_fresh_predictions':sum(r.get('prediction_execution',{}).get('reused_prediction') is False for r in initial['cases']),
        'final_fresh_predictions':sum(r.get('prediction_execution',{}).get('reused_prediction') is False for r in report['cases']),
        'service_coefficients_changed':False,'reason':'Use active matrix_groups separately from full matrix_weight_bank_groups; preserve complete integer rows domain.'}
    write(SECOND/'service-regime-review.json',result)
    lines=['# GLM second observed-service arm','',
           'This separate arm adds complete-population service means for expert-down GroupedMatmul, whole-batch SparseFlashMla and the standalone index-score kernel. The original six rules and physical program selections are byte-for-byte unchanged. All results are in-sample; no Body residual determines the three new parameters.','',
           '| Case | F | Real Mean / P50 / P90 ms | First Sim ms | Second Sim ms | Error | Body result |',
           '|---|---:|---:|---:|---:|---:|---|']
    for r in summaries:
        o=r['real_ms'];lines.append(f"| {r['case_id']} | {r['forward_count']} | {o['mean']:.6f} / {o['p50']:.6f} / {o['p90']:.6f} | {r['first_arm_sim_ms']:.6f} | {r['second_arm_sim_ms']:.6f} | {r['relative_error_pct']:+.2f}% | {'PASS' if r['passed'] else 'FAIL'} |")
    lines += ['', 'The added native boundaries receive 42, 11 and 11 responses per Forward. Index-score HBM-work coordinates distinguish context lengths even when the displayed input shape is equal; index_topk and projections remain separate. B=1 indexed attention uses its existing single-sequence source boundary, while B>1 uses the declared complete-batch boundary. No sequence subset is substituted for a full native call.', '',
              'Forced-balanced grouped work, sparse-index/active-context values and captured binary identity remain source conditions. Service calibration changes no strict ABI admission. Each response remains an inclusive lower bound on completion under the preserved physical schedule, not extra delay summed over phases.', '',
              f'Saved-native/first-arm/hit verification: {checks} checks / {len(failures)} failures. Independent Body arithmetic review is recorded in body-independent-review.json. No capture was parsed or newly collected.', '',
              'The initial six executions are retained in initial-selector-attempt-replay.json. Four small-M sources missed the GMM rule because matrix_groups was incorrectly equated with the 288 stored weight banks. The corrected physical selector uses the actual active group count plus a separate weight-bank guard. All six revised inputs were freshly predicted (12 total second-arm executions across two attempts); response means never changed. selector-correction.json preserves each exact earlier rule and case hash, independently reconstructible from the final inputs.', '',
              'Reproduce with the fixed 2f48346b runtime on PYTHONPATH: run ../build_second_pass.py; replay this manifest through ../../replay_decode_forwards.py with --geometry-limit 1 --prediction-timeout 90; then run ../review_second_pass.py.']
    (SECOND/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'checks':checks,'failures':failures,'passed':sum(r['passed'] for r in summaries),'sources':len(summaries)}))
    return bool(failures)


if __name__=='__main__':
    raise SystemExit(main())
