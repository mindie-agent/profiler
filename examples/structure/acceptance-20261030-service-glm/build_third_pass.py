"""Reuse the existing arch35 HC atomic source boundary and observed QKV service.

[Role] Replace omitted HC fusion through the public source selector, then calibrate
  each whole HCPre/QKV call from its complete retained normalized-contract population.
[Invariants] No new Sim code or Body residual fitting; prior nine rules unchanged.
[Timeouts & Locks] One small source graph and retained mapping at a time, no locks.
[Side-Effect Policy] Writes third-pass/ cases and evidence; no raw/device/cost I/O.
"""
from copy import deepcopy
import json
from pathlib import Path

from build_service_cases import HERE, ROOT, read, write, pin, summarize

THIRD=HERE/'third-pass'
ORDER=['a5_glm53flash_tp8_c8_p4k','a5_glm53flash_tp8_c4_p8k','glm53flash-a5-tp8-c1']


def main(*, manifest_path=None, output_dir=None, case_ids=None):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.structure_contracts import matrix_contract
    from mindie_sim.prediction.family_hc_arch35 import SOURCE, PRE_PROFILE
    destination=Path(output_dir or THIRD)
    manifest=read(manifest_path or HERE/'second-pass/decode-forward-service-cases.json');inputs={r['case_id']:r for r in manifest['cases']}
    allpop={r['case_id']:r for r in read(HERE/'observed-populations.json')['cases']}
    canon=read(ROOT/'examples/structure/acceptance-20261030-glm-source-complete-operators/body-operator-family-scoreboard.json')
    prior={r['source_case_id']:r for r in canon['cases']};rows=[];evidence=[]
    for cid in (case_ids or ORDER):
        row=deepcopy(inputs[cid]);old_path=Path(row['sim_case_path']);case=read(old_path);old=deepcopy(case)
        actual_pin=allpop[cid]['groups'][0]['actual_identity'];actual=read(actual_pin['path']);g=allpop[cid]['geometry'];M=g['query_rows']
        mapping_pin=prior[cid]['mapping_identity'];mapping=read(mapping_pin['path']);cohorts=[c for w in mapping['windows'] for c in w['cohorts']]
        assert pin(mapping_pin['path'])==mapping_pin
        options=case['runtime']['kernels']['lowerings']['native_fusion']['options']
        options['roles'].append('hc_pre');options.setdefault('traffic_profile',{})['hc_pre']=PRE_PROFILE
        parsed=parse_case(case);ops=target_graphs(parsed,phase='decode',tokens=g['tokens_per_sequence'],
              context=g['context_tokens'],sequences=g['sequences_per_replica'],scope='body')[0]
        hc=[o for o in ops if dict(o.metadata).get('fusion_role')=='hc_pre']
        qkv=[o for o in ops if o.recipe=='linear_qkvbfg_a']
        assert len(hc)==90 and len(qkv)==34
        assert not any(o.recipe in {'hc_values_fp32','hc_projection','hc_inverse_rms','hc_normalize_scale_bias_gate','hc_sinkhorn','hc_pre_mix'} for o in ops)
        groups=[]
        for native,role,selected,count in [('HcPre',None,hc,90),('MatMulV3','linear_qkvbfg_a',qkv,34)]:
            fs=[f for f in actual['families'] if f['native_operator_type']==native and (role is None or f['declared_role']==role)]
            stats=summarize(fs);assert stats['count']==count*actual['forward_count']
            matched=[c for c in cohorts if c['native_operator_type']==native and
                     (role is None or role in mapping['conditional_role_by_cohort_id'].get(c['cohort_id'],[]))]
            assert sum(c['complete_event_count'] for c in matched)==stats['count']
            assert sum(c['complete_activity_sum_ns'] for c in matched)==sum(k*n for k,n in stats['duration_ns_counter'])
            contracts={json.dumps(c['contract']) for c in matched};assert len(contracts)==1
            contract=json.loads(next(iter(contracts)))
            representative=selected[0]
            if native=='HcPre':
                expected=['hyper_connection_active','HcPre',[[[M,4,4096],'bf16','ND'],[[24,16384],'fp32','ND'],[[3],'fp32','ND'],[[24],'fp32','ND']],
                          [[[M,4096],'bf16','ND'],[[M,4],'fp32','ND'],[[M,4,4],'fp32','ND']]]
                assert contract==expected
                assert all(dict(o.metadata)['fusion_boundary']['traffic_profile']==PRE_PROFILE for o in selected)
                match={'hardware':parsed.machine.sku,'recipe':representative.recipe,'dtype':'bf16',
                       'metadata.fusion_role':'hc_pre','metadata.fusion_boundary.traffic_profile':PRE_PROFILE,
                       'metadata.fusion_tensor_view.tokens':M,'metadata.fusion_tensor_view.hidden':4096,
                       'metadata.fusion_tensor_view.hc':4,'metadata.fusion_tensor_view.parameter_dtype':'fp32'}
                caution='Complete normalized premix-absent contract population; optional output storage aliases, capture binary and runtime scalar values remain unestablished. Existing arch35 provider replaces all six phases once.'
            else:
                assert all(json.loads(json.dumps(matrix_contract(o.to_dict())))==contract for o in selected)
                match={'hardware':parsed.machine.sku,'recipe':representative.recipe,'dtype':representative.dtype,
                       **{f'local_shape.{i}':v for i,v in enumerate(representative.local_shape)}}
                caution='Complete native matrix normalized contract matches each source role; placement/occurrence is topology-conditioned, not Host stack evidence.'
            rid=native.lower()+'-'+(role or 'hc-pre')+'-observed-third'
            rule={'id':rid,'match':match,'response':{'fixed_us':stats['mean_us']},
                  'provenance':{'basis':'complete_normalized_contract_native_mean','calibration_origin':'observed',
                     'evaluation_relation':'in_sample','actual_identity':actual_pin,'mapping_identity':mapping_pin,
                     'native_operator_type':native,'count':stats['count'],'body_count':actual['forward_count'],
                     'mean_us':stats['mean_us'],'p50_us':stats['p50_us'],'contract':contract,
                     'body_residual_used':False,'response_boundary':'inclusive_native_call_once','boundary_caution':caution}}
            case['runtime']['kernels']['service_regimes'].append(rule)
            groups.append({'rule_id':rid,'native_operator_type':native,'declared_role':role,'actual_identity':actual_pin,
                           'mapping_identity':mapping_pin,'normalized_contract':contract,
                           'retained_cohort_ids':[c['cohort_id'] for c in matched],
                           'family_indices':[i for i,f in enumerate(actual['families']) if f in fs],
                           'observed':stats,'calls_per_forward':count,'declared_native_occurrences':len(selected),
                           'boundary_caution':caution})
        calibration={**row['calibration_evidence'],'evaluation_relation':'in_sample','regime_count':11,
                     'source_boundary_added':PRE_PROFILE,'normalized_contract_populations_verified':True}
        case['runtime']['metadata']['calibration_evidence']=calibration
        path=destination/'cases'/f'{cid}-hc-atomic-service.json';write(path,case)
        row.update(sim_case_path=str(path),model_declaration=pin(path),calibration_evidence=calibration,
                   variant_id='observed-service-hc-atomic-3b72ea2d')
        row['replay_input_pins']['case']=pin(path);row['prior_source_case_identity']=pin(old_path)
        rows.append(row);evidence.append({'case_id':cid,'case_identity':pin(path),'prior_case_identity':pin(old_path),
           'source_identity':actual['source_identity'],'geometry':g,'forward_count':actual['forward_count'],
           'hc_source':SOURCE,'groups':groups,'former_hc_semantic_phases_removed':540,
           'native_hc_instances_added':90,'prior_nine_rules_unchanged':case['runtime']['kernels']['service_regimes'][:9]==old['runtime']['kernels']['service_regimes']})
        print(cid,'verified90HC34QKV',flush=True)
    manifest.update(cases=rows,variant_id='observed-service-hc-atomic-3b72ea2d')
    write(destination/'decode-forward-service-cases.json',manifest)
    write(destination/'observed-populations.json',{'schema_version':'mindie-native-service-populations/1','cases':evidence,
        'generator_identity':pin(__file__),'raw_scans':0,'new_costs':0})


if __name__=='__main__':
    main()
