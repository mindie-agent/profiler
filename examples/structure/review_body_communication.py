"""[Role] Independently check communication buckets and existing-program references.
[Invariants] Exact measured multisets remain unchanged; references never add cost.
[Timeouts & Locks] No process, network or locks; bounded saved JSON only.
[Side-Effect Policy] Write one review result, no raw scans or predictions.
"""
from collections import Counter
from hashlib import sha256
import json
from math import ceil,isclose
from pathlib import Path
import argparse

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory',type=Path,default=Path(__file__).parent/'acceptance-20261030-high-concurrency')
base=parser.parse_args().directory
checks=0;failures=[]
def read(path):
    path=Path(path)
    if path.stat().st_size>32*1024**2:raise ValueError('report_too_large')
    return json.loads(path.read_text())
def check(actual,expected,label):
    global checks
    checks+=1
    equal=isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-10) if isinstance(actual,float) and isinstance(expected,(int,float)) else actual==expected
    if not equal:failures.append(label)
def verify(record):
    path=Path(record['path']);check(sha256(path.read_bytes()).hexdigest(),record['sha256'],str(path)+':sha')
def histogram(row):return Counter({int(v):int(n) for v,n in row['duration_ns_counter']})
def stats(row,label):
    pairs=histogram(row);values=sorted(v for v,n in pairs.items() for _ in range(n));n=len(values)
    expected={'count':n,'mean':sum(values)/n/1000,'min':values[0]/1000,'max':values[-1]/1000,
        'p50':(values[(n-1)//2]+values[n//2])/2000,'p90':values[ceil(.9*n)-1]/1000}
    for key,value in expected.items():check(row['observed_us'][key],value,label+':'+key)
path=base/'body-communication-references.json';report=read(path)
forward_count=call_count=reference_count=0
verify(report['historical_operator_scoreboard_identity'])
for case in report['cases']:
    verify(case['actual_identity']);actual=read(case['actual_identity']['path']);verify(actual['actual_family_identity'])
    prior=read(actual['actual_family_identity']['path']);f=case['forward_count'];forward_count+=f
    for block,role in [('attention','attention_output_communication'),('ffn','ffn_down_communication')]:
        observed=Counter();old=Counter()
        for group in case['groups']:
            if group['block']==block:observed.update(histogram(group))
        for group in prior['families']:
            if group['declared_role']==role:old.update(histogram(group))
        check(observed,old,case['case_id']+':'+block+':historical_duration_multiset')
    for group in case['groups']:
        label=case['case_id']+':'+group['attention_kind']+':'+group['block'];stats(group,label)
        check(group['observed_us']['count'],(48 if group['attention_kind']=='gdn' else 16)*f,label+':layer_multiplicity')
        check(group['scored_cohort_count'],0,label+':unscored');check(group['additional_budget_allowed'],False,label+':no_double_count')
        check(group['observed_activity_ms_per_forward'],sum(v*n for v,n in histogram(group).items())/f/1e6,label+':activity_per_forward')
        check(group['predicted_service_ms_per_forward'],group['predicted_us']*group['observed_us']['count']/f/1000,label+':service_per_forward')
        for count in group['layer_call_counts'].values():check(count,f,label+':per_layer_count')
        call_count+=group['observed_us']['count']
    for native in {row['native_operator_type'] for row in actual['contract_gap_families']}:
        now=Counter();old=Counter()
        for row in actual['contract_gap_families']:
            if row['native_operator_type']==native:now.update(histogram(row))
        for row in prior['families']:
            if row['native_operator_type']==native:old.update(histogram(row))
        check(now,old,case['case_id']+':'+native+':gap_population')
    for row in case['source_role_gap_references']:
        label=case['case_id']+':'+row['native_operator_type'];stats(row,label)
        check(row['scored_cohort_count'],0,label+':unscored');check(row['additional_budget_allowed'],False,label+':no_double_count')
        if row['status']=='reference_only':
            reference_count+=1
            programs=row['declared_programs'];calls=sum(p['target_count'] for p in programs)*f
            service=sum(p['target_count']*p['prediction']['per_call_ms'] for p in programs)
            check(calls,row['observed_us']['count'],label+':multiplicity')
            check(service,row['predicted_service_ms_per_forward'],label+':service')
            check(service*f/calls*1000,row['predicted_reference_us'],label+':reference_us')
result={'schema_version':'mindie-body-communication-review/1','status':'passed' if not failures else 'failed',
    'checks':checks,'failures':failures,'source_count':len(report['cases']),'forward_count':forward_count,
    'retained_collective_calls':call_count,'source_role_reference_count':reference_count,'scored_cohort_count':0,
    'report_sha256':sha256(path.read_bytes()).hexdigest(),'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
    'raw_capture_reads':0,'prediction_executions':0}
(base/'body-communication-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2));raise SystemExit(bool(failures))
