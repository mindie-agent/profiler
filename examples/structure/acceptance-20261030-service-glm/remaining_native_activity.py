"""Inventory observed native activity outside the six assigned service responses.

[Role] Prioritize retained measurements for a later explicit calibration iteration.
[Invariants] Unassigned service is not absent Sim cost. Activity is nonadditive
  against Body span; no Body residual is used as a native service parameter.
[Timeouts & Locks] One small actual receipt at a time; no subprocess or locks.
[Side-Effect Policy] Reads saved metadata only and writes this acceptance directory.
"""
import json
from pathlib import Path

from build_service_cases import pin, read, write

HERE=Path(__file__).resolve().parent


def main():
    evidence=read(HERE/'observed-populations.json')
    review=read(HERE/'service-regime-review.json')
    results={c['source_case_id']:c for c in review['cases']}
    cases=[]
    for c in evidence['cases']:
        scored=results[c['case_id']]
        if scored['body_passed']:
            continue
        actual_pin=c['groups'][0]['actual_identity'];actual=read(actual_pin['path'])
        assigned={g['native_operator_type'] for g in c['groups']}
        families=[]
        for index,f in enumerate(actual['families']):
            if f['native_operator_type'] in assigned:
                continue
            stats=f['observed_us']; count=stats['count']
            hist=f['duration_ns_counter'];total_ns=sum(int(k)*n for k,n in hist)
            assert sum(n for k,n in hist)==count
            families.append({'native_operator_type':f['native_operator_type'],
                'declared_role':f['declared_role'],'actual_family_index':index,
                'count':count,'calls_per_forward':count/c['forward_count'],
                'observed_us':stats,'activity_ms_per_forward':total_ns/c['forward_count']/1e6,
                'heavy_call':stats['mean']>50,'native_service_response_assigned':False,
                'sim_physical_program_absent':None,
                'complete_histogram_identity':{'actual_identity':actual_pin,'json_pointer':f'/families/{index}/duration_ns_counter'},
                'contract_status_counts':f.get('cohort_reasons',{})})
        families.sort(key=lambda x:x['activity_ms_per_forward'],reverse=True)
        cases.append({'case_id':c['case_id'],'source_identity':c['source_identity'],
                      'body_count':c['forward_count'],'geometry':c['geometry'],
                      'actual_identity':actual_pin,'families':families,
                      'heavy_families':[f for f in families if f['heavy_call']],
                      'top_activity_families':families[:5]})
    output={'schema_version':'mindie-unassigned-native-service-activity/1',
            'population_identity':pin(HERE/'observed-populations.json'),
            'completed_replay_identity':review['replay_identity'],'cases':cases,
            'interpretation':['These native families have not been assigned an observed-service rule in this arm.',
              'Existing analytical Sim costs are retained; unassigned is not a claim of missing modeling or zero prediction.',
              'Per-family activity is not an additive allocation of Body wall-clock error.',
              'All counts and histograms are retained observations; no extra service parameter is inferred from Body residual.'],
            'execution':{'raw_scans':0,'new_costs':0}}
    write(HERE/'remaining-native-activity.json',output)
    lines=['# Native activity outside the assigned service regimes','',
           'These measurements prioritize the next investigation. They do not establish missing Sim cost or an additive Body error budget. The current six service rules remain unchanged.','',
           '| Source | Native / role | Calls/F | Mean / P50 us | Activity ms/F | >50us/call |',
           '|---|---|---:|---:|---:|---|']
    for case in cases:
        for f in case['top_activity_families']:
            s=f['observed_us'];lines.append(f"| {case['case_id']} | {f['native_operator_type']} / {f['declared_role']} | {f['calls_per_forward']:.2f} | {s['mean']:.3f} / {s['p50']:.3f} | {f['activity_ms_per_forward']:.6f} | {f['heavy_call']} |")
    (HERE/'remaining-native-activity.md').write_text('\n'.join(lines)+'\n')
    print('sources',len(cases),'families',sum(len(c['families']) for c in cases))


if __name__=='__main__':
    main()
