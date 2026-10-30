"""Verify neutral native parameters against retained full integer populations.

[Role] Check provenance, weighted means/medians and exclusive domain pooling.
[Invariants] Whole native timings cannot create full ABI, route or PMU evidence.
[Timeouts & Locks] One retained local JSON at a time; no subprocesses or locks.
[Side-Effect Policy] Writes this input ledger's review only; no raw or costs.
"""
from collections import Counter
from math import isclose
from pathlib import Path
import json

from collect_scalar_dma_pmu import identity,read

ROOT=Path(__file__).resolve().parents[2]
PATH=ROOT/'data/observations/sources/arch22-physical-services/native-joint-service-inputs.json'


def navigate(value,path):
    for part in path.split('/'):
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value


def main():
    data=read(PATH);checks=0;failures=[];populations={};calls=0
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    for candidate in data['candidates']:
        aggregate=Counter();domain=candidate['applicability_domain'];seen=set()
        for row in candidate['source_populations']:
            label=row['case_id']+'/'+domain['native_operator_type'];pin=row['timing_identity']
            check(identity(pin['path'])==pin,label+'/timing pin')
            source=read(pin['path']);hist=Counter()
            for member in row.get('timing_members',[row.get('timing_member')]):
                hist.update(dict(navigate(source,member)))
            check(hist==Counter(dict(row['duration_ns_counter'])),label+'/complete retained histogram')
            check(row['source_identity']==source['source_identity'],label+'/capture identity')
            check(row['applicability_domain']==domain,label+'/equal domain')
            check(row['source_identity']['sha256'] not in seen,label+'/no duplicate source in domain')
            seen.add(row['source_identity']['sha256']);n=sum(hist.values());calls+=n
            check(n==row['calls_per_forward']*row['forward_count'],label+'/call multiplicity')
            check(row['forward_count']==source['forward_count'],label+'/primary forward count')
            populations[row['source_identity']['sha256']]=row['forward_count'];aggregate+=hist
            if row.get('pmu'):
                check(row['pmu']['event_count']==n,label+'/PMU full event count')
                for name,field in row['pmu']['fields'].items():
                    check(field=={k:v for k,v in source['raw_pmu']['fields'][name].items() if k!='numeric_value_counter'},label+'/PMU denominator '+name)
                check(domain['native_abi']==source['native_abi_groups'][0]['native_abi'],label+'/full ABI identity')
                check(source['raw_pmu']['dimensions']['Block Num']==[[str(domain['observed_block_num']),n]],label+'/all Block observations')
            else:
                check(domain['native_abi'] is None and domain['observed_block_num'] is None,label+'/no example promotion')
                check(row['example_ABI_is_not_full_population_ABI'],label+'/explicit evidence strength')
                subs=Counter()
                for group in row['complete_attention_subpopulations']:subs.update(dict(group['duration_ns_counter']))
                check(subs==hist,label+'/layer-kind subdivision conservation')
        check(aggregate==Counter(dict(candidate['duration_ns_counter'])),candidate['candidate_id']+'/pooled full hist')
        values=[ns for ns,n in sorted(aggregate.items()) for _ in range(n)]
        mean=sum(values)/len(values)/1000;median=(values[(len(values)-1)//2]+values[len(values)//2])/2000
        check(isclose(candidate['parameter_value_us'],mean,abs_tol=1e-10),candidate['candidate_id']+'/weighted mean')
        check(isclose(candidate['alternative_descriptive_p50_us'],median,abs_tol=1e-10),candidate['candidate_id']+'/pooled median')
        check(candidate['observed_native_elapsed_us']['count']==len(values),candidate['candidate_id']+'/pooled count')
        check(candidate['body_residual_used'] is False and candidate['api_binding'] is None,candidate['candidate_id']+'/no residual or invented API')
    check(len(populations)==data['source_count']==5,'unique sources')
    check(sum(populations.values())==data['primary_forwards']==220,'unique forwards')
    check(calls==data['native_calls']==33511,'complete calls')
    result={'schema_version':'mindie-native-joint-service-input-review/1','status':'failed' if failures else 'passed',
            'checks':checks,'failures':failures,'report_identity':identity(PATH),'reviewer_identity':identity(__file__),
            'source_count':len(populations),'primary_forwards':sum(populations.values()),'native_calls':calls,
            'new_raw_scans':0,'new_costs':0}
    PATH.with_name('native-joint-service-input-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return bool(failures)


if __name__=='__main__':raise SystemExit(main())
