"""Independently reconcile a frozen retrospective native-service split.

[Role] Check training-only coefficients, validation arithmetic and replay use.
[Invariants] No refit or model selection from held-out errors; Body is a
  counterfactual, not a claim of historically blind whole-model validation.
[Timeouts & Locks] Small retained JSON only; no subprocess, raw scan or cost.
[Side-Effect Policy] Writes one compact review and a readable result table.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('streaming required')
    return json.loads(path.read_text())


def review(directory):
    d = Path(directory)
    policy = read(d/'split-policy.json'); trained = read(d/'training-models.json')
    evaluation = read(d/'operator-heldout-evaluation.json')
    checks, failures = 0, []
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok: failures.append(label)
    def close(a,b,label):
        check(math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-8),label)
    train_shas = {x['source_identity']['sha256'] for x in policy['training']}
    test_shas = {x['source_identity']['sha256'] for x in policy['heldout']}
    check(not train_shas & test_shas, 'disjoint source hashes')
    models = {m['rule']['id']:m for m in trained['models']}
    for mid,m in models.items():
        a=m['coefficients']['fixed_us']; b=m['coefficients']['us_per_axis_unit']
        rows=m['training_rows']; x=[r['coordinate'] for r in rows]; y=[r['observed_mean_us'] for r in rows]
        check({r['source_identity']['sha256'] for r in rows}==train_shas,mid+': training population')
        check(a>=0 and b>=0 and len(set(x))>1,mid+': nonnegative rank2')
        # Independent constrained optimum certificate: gradient is zero for
        # positive parameters and nonnegative at an active lower bound.
        residual=[a+b*u-v for u,v in zip(x,y)]
        for parameter,g in ((a,sum(residual)),(b,sum(u*r for u,r in zip(x,residual)))):
            tolerance=1e-8*max(1,sum(abs(u*v) for u,v in zip(x,y)))
            check(abs(g)<=tolerance if parameter>0 else g>=-tolerance,mid+': KKT')
        close(sum(v*v for v in residual),m['coefficients']['training_sse_us2'],mid+': SSE')
    for r in evaluation['rows']:
        m=models[r['rule_id']]; c=m['coefficients']
        pred=c['fixed_us']+c['us_per_axis_unit']*r['coordinate']
        close(pred,r['predicted_response_us'],'response arithmetic')
        close(pred-r['observed_mean_us'],r['per_call_difference_us'],'difference arithmetic')
        check(r['source_identity']['sha256'] in test_shas,'heldout provenance')
        check(r['count']==r['forward_count']*r['native_calls_per_forward'],'native population')
        expected=abs(pred-r['observed_mean_us']) <= (15 if r['observed_mean_us']<=50 else .15*r['observed_mean_us'])
        check(expected==r['passed'],'tiered accuracy')
    manifest=read(d/'decode-forward-heldout-cases.json')
    for row in manifest['cases']:
        case=read(row['sim_case_path']); rules=case['runtime']['kernels']['service_regimes']
        check({r['id'] for r in rules}==set(models),'only train-derived rules')
        for rule in rules:
            check(rule['response']==models[rule['id']]['rule']['response'],'same learned response across validation')
            check({s['sha256'] for s in rule['provenance']['training_source_identities']}==train_shas,'case training sources')
    report=read(d/'decode-forward-heldout-replay.json')
    body=[]
    for row in report['cases']:
        if row['comparison']['status']!='compared': continue
        selected=row['prediction']['parameters'].get('service_regimes',{})
        body.append({'case_id':row['case_id'],'comparison':row['comparison'],
                     'service_regime_selection':[{k:s[k] for k in ('id','queries','response_us_min','response_us_max') if k in s} for s in selected]})
        check(bool(selected),'selection accounting retained')
        expected={x['rule_id']:x for x in evaluation['rows'] if x['case_id']==row['source_case_id']}
        check({s['id'] for s in selected}==set(expected),'all learned domains selected')
        for s in selected:
            e=expected[s['id']]
            check(sum(s['queries'].values())==e['native_calls_per_forward'],'whole native application count')
            close(s['response_us_min'],e['predicted_response_us'],'minimum applied response')
            close(s['response_us_max'],e['predicted_response_us'],'maximum applied response')
    result={'schema_version':'mindie-retrospective-heldout-review/1','status':'failed' if failures else 'passed',
        'checks':checks,'failures':failures,'training_sources':len(train_shas),'heldout_sources':len(test_shas),
        'operator_groups':len(evaluation['rows']),'operator_passed':sum(r['passed'] for r in evaluation['rows']),
        'body':body,'scope':'Training exclusion, coefficient optimality certificate, complete native population and response arithmetic. No claim of whole-model historical blindness.',
        'report_sha256':sha256((d/'decode-forward-heldout-replay.json').read_bytes()).hexdigest(),
        'new_raw_scans':0,'new_cost_predictions':0}
    (d/'parameter-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='body'}))
    return bool(failures)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path)
    raise SystemExit(review(p.parse_args().directory))
