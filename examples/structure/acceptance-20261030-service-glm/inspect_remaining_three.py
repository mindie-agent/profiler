"""Read-only native/declared-boundary diagnostics for the remaining three cases.

[Role] Relate retained native activity to current saved scheduled operator groups.
[Invariants] Ready-to-complete includes waiting, is not isolated service and is not
  an additive Body budget. Missing atomic boundaries do not imply zero Sim work.
[Timeouts & Locks] Saved bounded JSON only; no locks, subprocess, capture or cost.
[Side-Effect Policy] Writes diagnostic JSON/Markdown in this acceptance directory.
"""
from pathlib import Path

from build_service_cases import HERE, read, pin, write, summarize


def main():
    replay_path=HERE/'second-pass/decode-forward-service-replay.json'
    replay=read(replay_path)
    evidence={c['case_id']:c for c in read(HERE/'observed-populations.json')['cases']}
    cases=[]
    for row in replay['cases']:
        if row['status']!='compared' or row['comparison']['passed']:
            continue
        cid=row['source_case_id'];ap=evidence[cid]['groups'][0]['actual_identity'];actual=read(ap['path'])
        F=actual['forward_count'];scheduled=row['prediction']['scheduled_operator_summary']['groups']
        plans=[('HcPre',None,{'hc_values_fp32','hc_projection','hc_inverse_rms','hc_normalize_scale_bias_gate','hc_sinkhorn','hc_pre_mix'}),
               ('MatMulV3','linear_qkvbfg_a',{'linear_qkvbfg_a'}),('Slice',None,set()),
               ('SparseFlashMlaMetadata',None,set())]
        groups=[]
        for native,role,recipes in plans:
            fs=[f for f in actual['families'] if f['native_operator_type']==native and (role is None or f['declared_role']==role)]
            observed=summarize(fs);count=observed['count'];observed.pop('duration_ns_counter')
            measured_activity=observed['mean_us']*count/F/1000
            refs=[{'group_index':i,**g} for i,g in enumerate(scheduled) if g['recipe'] in recipes and g['replica']==0]
            status=('decomposed_subgraph_without_atomic_native_boundary' if native=='HcPre' else
                    'one_declared_role_with_equal_call_count' if role else 'no_independent_recipe_correspondence_retained')
            if role: assert len(refs)==1 and refs[0]['scheduled_elapsed_ms']['count']==count/F
            groups.append({'native_operator_type':native,'declared_role':role,'observed':observed,
                'calls_per_forward':count/F,'measured_activity_ms_per_forward':measured_activity,
                'retained_native_population':{'identity':ap,'family_indices':[i for i,f in enumerate(actual['families']) if f in fs]},
                'boundary_status':status,'scheduled_reference_groups':refs,
                'scheduled_reference_boundary':'node ready-to-complete including contention/peer/resource waiting',
                'scheduled_minus_native_activity_ms_per_forward':refs[0]['sum_elapsed_ms']-measured_activity if role else None,
                'isolated_native_service_prediction_us':None,'additive_body_error_implied':False,
                'missing_work_implied':False})
        cases.append({'case_id':cid,'source_identity':actual['source_identity'],'forward_count':F,
                      'geometry':row['geometry'],'runtime_identity':row['runtime_identity'],
                      'body_comparison':row['comparison'],'groups':groups})
    value={'schema_version':'mindie-native-boundary-gap-diagnostics/1','replay_identity':pin(replay_path),
           'cases':cases,'execution':{'raw_scans':0,'new_costs':0},
           'recommendations':[
               'HcPre needs a whole-native source group and resource accounting review before attaching its observed completion floor. Do not assign the full native mean to each decomposed phase.',
               'linear_qkvbfg_a has a unique declared role and equal native call count; validate the retained complete tensor contract before extending its service regime.',
               'Slice has 224 retained calls/Forward but no independent resource recipe correspondence. Recover its shape/role partitions before distinguishing materialization from a zero-work view.',
               'SparseFlashMlaMetadata has 11 native calls/Forward and no independent saved source node. Its metadata work must not be silently folded into the already calibrated SparseFlashMla call.']}
    write(HERE/'remaining-three-diagnostics.json',value)
    lines=['# Remaining three GLM cases: boundary and service evidence','',
           'No new cost or capture read. References below are current scheduled node intervals including waiting, not isolated kernel service. Component intervals and native activities are not additive Body-error allocations.','',
           '| Source | Native / role | Calls/F | Native Mean / P50 us | Native ms/F | Current reference |',
           '|---|---|---:|---:|---:|---|']
    for c in cases:
        for g in c['groups']:
            s=g['observed'];ref=g['boundary_status']
            if g['declared_role']:
                z=g['scheduled_reference_groups'][0];ref=f"scheduled {z['scheduled_elapsed_ms']['mean']*1000:.3f}us/call; {z['sum_elapsed_ms']:.6f}ms/F"
            elif g['native_operator_type']=='HcPre':
                z=next(x for x in g['scheduled_reference_groups'] if x['recipe']=='hc_projection')
                ref=f"6 stages × 90 calls; projection alone scheduled {z['sum_elapsed_ms']:.6f}ms/F (not an atomic native comparison)"
            lines.append(f"| {c['case_id']} | {g['native_operator_type']} / {g['declared_role'] or 'whole retained population'} | {g['calls_per_forward']:.0f} | {s['mean_us']:.3f} / {s['p50_us']:.3f} | {g['measured_activity_ms_per_forward']:.6f} | {ref} |")
    lines+=['','No extra regime is added by this diagnostic. Native ABI gaps and missing atomic boundaries remain visible; the listed recipes may already account for physical work.']
    (HERE/'remaining-three-diagnostics.md').write_text('\n'.join(lines)+'\n')
    print('cases',len(cases),'native groups',sum(len(c['groups']) for c in cases))


if __name__=='__main__':
    main()
