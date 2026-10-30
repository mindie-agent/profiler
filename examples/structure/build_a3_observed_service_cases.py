"""Declare A3 per-call responses from retained complete native populations.

[Role] Add observable service floors to existing physical model declarations.
[Invariants] No residual fitting or per-layer selection. A pooled native mean
  is assigned once per matching declared invocation, with explicit scope limits.
[Timeouts & Locks] One metadata graph at a time; bounded retained JSON, no locks.
[Side-Effect Policy] Independent cases/manifests only; no raw scan/device/cost.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import ROOT, OUT, read, write, identity, physical_ops


ORDER = ['a3_kimi4_tp8_w4a8_c32', 'a3_kimi4_tp8_w4a8_c16',
         'a3_kimi4_tp8_w4a8_c4', 'a3_kimi4_tp8_w4a8_c1',
         'a3_glm53_w4a8_tp16_tpot88_c8', 'a3_glm53_w4a8_tp16_tpot30_c2',
         'a3_glm53_w4a8_tp16_tpot50_c2', 'glm53flash-a3-tp16-c4-livepre']


def pooled(groups):
    counter = Counter()
    for group in groups:
        counter.update({int(k): n for k,n in group['duration_ns_counter']})
    n = sum(counter.values())
    def quantile(p):
        rank=(n-1)*p; lo=int(rank);hi=min(lo+1,n-1); vals=[]
        for at in (lo,hi):
            running=0
            for value,count in sorted(counter.items()):
                running += count
                if running>at:
                    vals.append(value);break
        return (vals[0]+(vals[1]-vals[0])*(rank-lo))/1000
    return {'count': n, 'mean_us': sum(k*v for k,v in counter.items())/n/1000,
            'p50_us': quantile(.5), 'duration_ns_counter': sorted(counter.items())}


def _physical_match(case, op):
    match={'hardware':case.machine.hardware_key or case.machine.sku,
           'recipe':op.recipe, 'family':op.family, 'phase':op.phase,
           'dtype':op.dtype or case.model.compute_dtype}
    match.update({f'local_shape.{i}':value for i,value in enumerate(op.local_shape)})
    meta=dict(op.metadata)
    for key in ('weight_dtype','state_dtype','heads','dk','dv','group_axis','kernel_width'):
        if key in meta:
            match['metadata.'+key]=meta[key]
    return match


def build():
    basenames=['decode-forward-remaining-controller-cases.json','decode-forward-glm-controller-cases.json']
    rows={r['case_id']:r for name in basenames
          for r in read(ROOT/'acceptance-20261030-runtime40e4300e'/name)['cases']}
    operators={r['source_case_id']:r for r in read(ROOT/'acceptance-20261030-kimi-source-operators/body-operator-family-scoreboard.json')['cases']}
    flash=read(ROOT/'acceptance-20261030-glm-source-complete-operators/body-operator-family-scoreboard.json')
    operators.update({r['source_case_id']:r for r in flash['cases']})
    out, evidence=[] ,[]
    for cid in ORDER:
        row=deepcopy(rows[cid]); old=Path(row['sim_case_path']);raw=read(old)
        geo=row['replay_input_pins']['primary_geometry'];case,ops=physical_ops(raw,geo)
        ledger_path=ROOT/'acceptance-20261030-hccl-66'/f'{cid}-capture-hccl.json'
        ledger=read(ledger_path)
        capture=next(g for g in ledger['body_geometry_groups'] if all(g['geometry'][k]==geo[k]
                     for k in ('query_rows','sequences_per_replica','tokens_per_sequence')))
        F=capture['forward_count']
        if ledger['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('source_identity_mismatch')
        actual=read(operators[cid]['actual_identity']['path']) if cid in operators else None
        if actual and (actual['forward_count']!=F or actual['source_identity']['sha256']!=row['source']['sha256']):
            raise ValueError('actual_population_mismatch')
        plans=[]
        # Communication rows are typed retained native envelopes, never AICPU
        # launch wrappers or duplicate summary events. All layers remain pooled.
        for native,family in [('hcom_allReduce_','allreduce'),('hcom_allGather_','allgather'),
                              ('hcom_reduceScatter_','reduce_scatter')]:
            measured=[g for g in capture['groups'] if g['native_operator_type']==native
                      and g['event_category'] in ('collective_envelope_only','collective_device_task')]
            if measured:
                plans.append((native,measured,[o for o in ops if o.family==family],identity(ledger_path),
                    'Source-declared collective physical boundary; pooled complete native elapsed includes protocol and peer wait.'))
        if actual:
            for native,role,recipes in [
                ('CausalConv1d',None,{'short_convolution'}),
                ('RecurrentKda',None,{'vllm_ascend_recurrent_kda_arch22'}),
                ('GroupedMatmul','expert_up',{'balanced_grouped_gate_up','grouped_gate_up'}),
                ('GroupedMatmul','expert_down',{'balanced_grouped_down','grouped_down'})]:
                measured=[g for g in actual['families'] if g['native_operator_type']==native
                          and (role is None or g['declared_role']==role)]
                if measured:
                    plans.append((native+(':'+role if role else ''),measured,
                        [o for o in ops if o.recipe in recipes],operators[cid]['actual_identity'],
                        'Complete native family/role population; source physical domain retained. Dynamic routed row values are not identified by buffer capacity.'))
        rules,coverage=[],[]
        for native,groups,selected,pin,boundary in plans:
            stats=pooled(groups);expected=stats['count']/F
            if not selected or len(selected)!=expected:
                coverage.append({'native_operator_type':native,'status':'not_parameterized',
                    'reason':'declared_single_call_population_differs','observed_calls_per_forward':expected,
                    'declared_invocations':len(selected),'observed':stats,'identity':pin})
                continue
            axes={}
            for op in selected:
                match=_physical_match(case,op);key=json.dumps(match,sort_keys=True)
                axes.setdefault(key,{'match':match,'count':0})['count']+=1
            # Pooling remains explicit where a complete population spans several
            # physical recipe variants; it does not claim variant-specific timing.
            for i,axis in enumerate(axes.values()):
                rid=native.lower().replace(':','-')+f'-observed-{i}'
                rules.append({'id':rid,'match':axis['match'],'response':{'fixed_us':stats['mean_us']},
                    'provenance':{'calibration_origin':'observed','evaluation_role':'in_sample',
                    'source_identity':row['source'],'observation_identity':pin,
                    'native_operator_type':native,'complete_population':stats,'forward_count':F,
                    'expected_rule_hits':axis['count'],'population_partition_count':len(axes),
                    'pooled_assignment':len(axes)>1,'body_residual_used':False,
                    'response_boundary':'one_declared_whole_call','scope_limitations':boundary}})
                coverage.append({'rule_id':rid,'status':'declared','native_operator_type':native,
                    'observed_calls_per_forward':expected,'expected_rule_hits':axis['count'],
                    'pooled_assignment':len(axes)>1,'observed':stats,'identity':pin})
        if not rules:
            raise ValueError('no_observable_call_domain:'+cid)
        raw['runtime'].setdefault('kernels',{})['service_regimes']=rules
        calibration={'evaluation_role':'in_sample','source_identity':row['source'],
                     'body_residual_used':False,'parameter_assignment':'complete_native_arithmetic_means',
                     'scope':'whole call completion floor; larger analytic work remains',
                     'contract_admission_changed':False}
        raw['runtime'].setdefault('metadata',{}).update(calibration_origin='observed',calibration_evidence=calibration)
        target=OUT/'a3-cases'/f'{cid}-observable-service.json';write(target,raw)
        row.update(sim_case_path=str(target),model_declaration=identity(target),
                   baseline_case_identity=identity(old),variant_id='a3-observable-service-2f48346b',
                   calibration_origin='observed',calibration_evidence=calibration)
        row['replay_input_pins']['case']=identity(target)
        out.append(row);evidence.append({'case_id':cid,'geometry':geo,'forward_count':F,
            'source_identity':row['source'],'baseline_case_identity':identity(old),'groups':coverage,
            'not_parameterized':['MC2 native envelope does not equal generic transport-only program',
                                 'native calls without a complete retained single-call correspondence']})
        print(cid,'rules',len(rules),'F',F,flush=True)
    write(OUT/'a3-service-populations.json',{'schema_version':'mindie-observed-service-populations/1',
          'cases':evidence,'raw_capture_scans':0,'new_predictions':0})
    write(OUT/'decode-forward-a3-service-cases.json',{'schema_version':'mindie-decode-forward-replay/1',
          'variant_id':'a3-observable-service-2f48346b','cases':out,'not_new_live_collection':True})


if __name__=='__main__':
    build()
