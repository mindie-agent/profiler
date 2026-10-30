"""Extend two requested Qwen TP2 regimes with complete saved gating populations.

[Role] Assign retained gating and normalization means to existing source calls.
[Invariants] Whole populations, one response/call, no Body residual or layer IDs.
  Missing copy ABI/populations stay missing; no mixture is allocated by guess.
[Timeouts & Locks] Bounded JSON and metadata graphs; no locks or device work.
[Side-Effect Policy] Independent second-arm cases/manifest; first replay immutable.
"""
from copy import deepcopy

from build_qwen_a3_service_cases import ROOT, OUT, read, write, identity, physical_ops
from build_a3_observed_service_cases import pooled, _physical_match


def build():
    first=read(OUT/'decode-forward-qwen-service-cases.json')
    rows={r['case_id']:r for r in first['cases']}
    out,evidence=[],[]
    for batch in (12,1):
        cid=f'qwen36-a5-tp2-c{batch}';row=deepcopy(rows[cid]);old=row['sim_case_path'];raw=read(old)
        actual_path=ROOT/'acceptance-20261030-qwen-source-native-operators/retained-six-actual'/f'body-operator-{cid}-qwen-source-gdn-native.actual.json'
        actual=read(actual_path)
        if actual['source_identity']['sha256']!=row['source']['sha256']:
            raise ValueError('gating_source_identity_mismatch')
        case,ops=physical_ops(raw,row['replay_input_pins']['primary_geometry'])
        populations=[]
        for native,recipes in [
            ('fused_gdn_gating_kernel',{'ascend_gdn_decode_gating'}),
            ('l2norm_fwd_kernel2',{'decode_q_l2norm','decode_k_l2norm'}),
            ('_layer_norm_fwd_1pass_kernel_npu',{'linear_output_norm_gate'})]:
            groups=[f for f in actual['families'] if f['native_operator_type']==native]
            stats=pooled(groups);selected=[o for o in ops if o.recipe in recipes]
            if len(selected)!=stats['count']/actual['forward_count']:
                raise ValueError('complete_gating_population_differs:'+native)
            for recipe in sorted(recipes):
                programs=[o for o in selected if o.recipe==recipe]
                matches=[_physical_match(case,o) for o in programs]
                if any(match!=matches[0] for match in matches):
                    raise ValueError('gating_physical_domains_differ')
                rid=recipe+'-observed-complete'
                provenance={'calibration_origin':'observed','evaluation_relation':'in_sample',
                    'source_identity':actual['source_identity'],'actual_identity':identity(actual_path),
                    'native_operator_type':native,'observed':stats,'forward_count':actual['forward_count'],
                    'expected_rule_hits':len(programs),'pooled_q_k_assignment':len(recipes)>1,
                    'response_boundary':'one_existing_declared_source_call',
                    'contract_admission_changed':False,'full_native_abi_established':False,
                    'basis':'Complete topology-aligned native population, declared source physical shape.',
                    'body_residual_used':False}
                raw['runtime']['kernels']['service_regimes'].append({'id':rid,'match':matches[0],
                    'response':{'fixed_us':stats['mean_us']},'provenance':provenance})
                populations.append({'rule_id':rid,**provenance})
        calibration=raw['runtime']['metadata']['calibration_evidence']
        calibration.update(evaluation_relation='in_sample',additional_actual_identity=identity(actual_path),
                           parameter_assignment='complete_native_arithmetic_means')
        raw['runtime']['metadata']['calibration_origin']='observed'
        target=OUT/'gating-cases'/f'{cid}-gating-observable-service.json';write(target,raw)
        row.update(sim_case_path=str(target),model_declaration=identity(target),
                   baseline_service_case_identity=identity(old),calibration_origin='observed',
                   calibration_evidence=calibration,variant_id='observable-gating-service-2f48346b')
        row['replay_input_pins']['case']=identity(target);out.append(row)
        evidence.append({'case_id':cid,'groups':populations,
            'copy_status':'No _copy_conv_state_kernel native family in either complete source population; Slice is mixed and is not allocated to convolution input by guessing.'})
    write(OUT/'qwen-gating-service-populations.json',{'cases':evidence,'raw_capture_reads':0})
    write(OUT/'decode-forward-qwen-gating-service-cases.json',{
        'schema_version':first['schema_version'],'variant_id':'observable-gating-service-2f48346b',
        'cases':out,'not_new_live_collection':True,'baseline_reference':identity(OUT/'decode-forward-qwen-service-replay.json')})


if __name__=='__main__':
    build()
