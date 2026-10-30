"""Bind complete low-row GLM78 native contracts to source-shaped kernel calls.

[Role] Add same-source native services after the TP join-before-reduce repair.
[Invariants] All response values come from complete retained integer histograms;
  exact active contracts and call multiplicity gate each physical assignment.
[Timeouts & Locks] One metadata graph and retained source table at a time.
[Side-Effect Policy] New cases/proof only; no raw scans, costs or Sim source edits.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from build_glm78_joint_service_cases import EXECUTION, pooled
from build_glm78_native_service_cases import descriptor, freeze
from build_a3_tail_cohort_service_cases import matches
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure_contracts import predicted_contract
from mindie_sim.structure_subgraphs import subgraph_contract


HERE=Path(__file__).resolve().parent
BASE=HERE/'acceptance-20261030-a3-tail-service-refinement'
OUT=BASE/'glm78-low-native-service'
JOINT={'MlaPrologV3','LightningIndexer','MoeGatingTopK','SparseFlashAttention',
       'GroupedMatmul','GroupedMatmulSwigluQuantV2'}


def physical_match(case,op):
    result=_physical_match(case,op);meta=dict(op.metadata)
    if meta.get('fusion_role'):
        result['metadata.fusion_role']=meta['fusion_role']
        for key,value in meta['fusion_tensor_view'].items():
            if isinstance(value,(str,int,float,bool))or value is None:
                result['metadata.fusion_tensor_view.'+key]=value
    return result


def build():
    manifest=read(BASE/'glm78-tp-join/decode-forward-tp-join-cases.json');rows=[];proofs=[]
    for before in manifest['cases']:
        cid=before['case_id'];raw=read(before['sim_case_path']);geo=before['replay_input_pins']['primary_geometry']
        native_path=BASE/'glm78-low-native'/f'{cid}-native-partitions.json';native=read(native_path);F=native['forward_count']
        if native['source_identity']['sha256']!=before['source']['sha256']:raise ValueError('source_changed')
        router=[g for g in native['partitions']if g['native_operator_type']=='MatMulV3'and g['topology_region']=='ffn']
        expected_router=['native_tensor_abi','MatMulV3',[[[geo['query_rows'],6144],'bf16','ND'],
            [[256,6144],'bf16','ND']],[[[geo['query_rows'],256],'fp32','ND']]]
        if len(router)!=1 or router[0]['native_abi']!=expected_router or router[0]['observed_us']['count']!=75*F:
            raise ValueError('router_operand_population_not_verified')
        k=raw['runtime']['kernels'];prior=deepcopy(k['service_regimes'])
        k['lowerings']={'mla_prolog':{'implementation':'vllm_ascend_mla_prolog_v3'},
            'native_fusion':{'implementation':'declared_native_fusion','options':{'roles':
                ['mla_prolog','lightning_indexer','router_selection','grouped_gate_up_activation_quant']}},
            'shared_expert':'ascend_shared_gate_up_int32',
            'add_rmsnorm':{'implementation':'vllm_ascend_native_norm','options':{'has_bias':True}},
            'add_rmsnorm_quant':{'implementation':'vllm_ascend_native_norm','options':{'has_bias':True}}}
        k['fusion_domains']={'norm_quant':{'consumers':[{'recipe':'dense_gate_up'}]}}
        k['programs']={'indexed_attention':{'kind':'indexed_attention_pipeline','scratch_policy':'offchip'}}
        raw['runtime']['lowering_passes']=['activation_quantization','norm_quant','residual_norm']
        overrides=raw['model'].setdefault('layer_overrides',{})
        for layer in router[0]['layer_counts']:
            overrides.setdefault(str(layer),{}).update(router_dtype='bf16',router_output_dtype='fp32')
        case,ops=physical_ops(raw,geo);declared=defaultdict(list);observed=defaultdict(list)
        for op in ops:
            meta=dict(op.metadata)
            contract=subgraph_contract({'role':meta['fusion_role'],'tensor_view':meta['fusion_tensor_view']})if meta.get('fusion_role')else predicted_contract(op.to_dict(include_work=False))
            if contract is not None:declared[freeze(contract)].append(op)
        for i,g in enumerate(native['partitions']):
            if g['native_abi'] is None:continue
            contract=observed_contract(descriptor(g['native_abi']))
            if contract is not None:observed[(g['native_operator_type'],freeze(contract))].append((i,g))
        added=[];excluded=[]
        for (kind,contract),parts in observed.items():
            selected=declared.get(contract,[]);stats=pooled([g for _,g in parts])
            if not selected or stats['count']!=len(selected)*F:
                excluded.append({'native_operator_type':kind,'active_contract':contract,'observed_calls':stats['count'],
                    'observed_calls_per_forward':stats['count']/F,'declared_invocations':len(selected),'reason':'complete_contract_population_differs'});continue
            if any(any(matches(case,o,r['match'])for r in k['service_regimes'])for o in selected):
                excluded.append({'native_operator_type':kind,'reason':'prior_response_preserved'});continue
            domains=defaultdict(list)
            for op in selected:domains[json.dumps(physical_match(case,op),sort_keys=True)].append(op)
            if any({o.op_id for o in ops if matches(case,o,json.loads(key))}!={o.op_id for o in members}for key,members in domains.items()):
                excluded.append({'native_operator_type':kind,'active_contract':contract,'reason':'physical_selector_other_population'});continue
            for key,targets in domains.items():
                rid='low-native-'+kind.lower()+'-'+sha256(key.encode()).hexdigest()[:12]
                proof={'calibration_origin':'observed','evaluation_relation':'in_sample','native_identity':identity(native_path),
                    'source_identity':native['source_identity'],'native_operator_type':kind,'active_contract':contract,
                    'partition_indices':[i for i,_ in parts],'full_native_abis':[g['native_abi']for _,g in parts],
                    'complete_population':stats,'forward_count':F,'expected_rule_hits':len(targets),
                    'whole_contract_calls_per_forward':len(selected),'physical_variant_timings_observed':len(domains)==1,
                    'body_residual_used':False,'strict_admission_changed':False,
                    'dynamic_group_list_values_observed':False,'pointer_identity_observed':False,
                    'declared_target_ids':[o.op_id for o in targets]}
                rule={'id':rid,'match':json.loads(key),'response':{'fixed_us':stats['mean_us']},'provenance':proof}
                if kind in JOINT:
                    if any(o.link_bytes or dict(o.metadata).get('device_kernel_group')for o in targets):raise ValueError('joint_not_single_local_native')
                    rule['execution']={**EXECUTION,'native_kernel':kind}
                    proof['response_boundary']='one_complete_local_native_joint_service'
                else:proof['response_boundary']='one_complete_active_contract_native_inclusive_floor'
                k['service_regimes'].append(rule);added.append({'rule_id':rid,'match':rule['match'],**proof})
        required={'MlaPrologV3','LightningIndexer','MoeGatingTopK','GroupedMatmul','GroupedMatmulSwigluQuantV2','SparseFlashAttention','DequantSwigluQuant'}
        if not required<={r['native_operator_type']for r in added}:raise ValueError('required_complete_native_boundary_missing')
        device=raw['machine'].setdefault('device',{})
        for field,value in [('rates',1e9),('work_units','busy_ns'),('resource_units',1)]:device.setdefault(field,{})['joint_native_a3']=value
        if k['service_regimes'][:len(prior)]!=prior:raise ValueError('prior_HCCL_service_changed')
        target=OUT/'cases'/f'{cid}-complete-native-service.json';write(target,raw)
        row=deepcopy(before);row.update(sim_case_path=str(target),model_declaration=identity(target),variant_id='glm78-low-complete-native-service')
        row['replay_input_pins']['case']=identity(target)
        row['calibration_evidence']['complete_native_rules']=[{'rule_id':r['rule_id'],'native_operator_type':r['native_operator_type'],
            'expected_rule_hits':r['expected_rule_hits']}for r in added]
        rows.append(row);proofs.append({'case_id':cid,'case_identity':identity(target),'native_identity':identity(native_path),
            'prior_case_identity':identity(before['sim_case_path']),'forward_count':F,'prior_rules_unchanged':True,
            'new_rules':added,'unassigned_populations':excluded,'router_typed_source_abi':expected_router,
            'source_boundary_conditions':['Shared INT32 accumulator feeds native DSQ once.',
                'Existing source prolog preserves BF16 UK/UV and BF16 separate KV/rope caches.',
                'Indexed analytic batch declaration joins only query rows; full observed SFA contract is compared before a whole-call response.',
                'Grouped active rows equal captured tensor rows; dynamic group-list values and installed binary identity remain unknown.']})
        print(json.dumps({'case_id':cid,'rules':len(added),'unassigned':len(excluded),'joint':[(r['native_operator_type'],r['expected_rule_hits'])for r in added if r['native_operator_type']in JOINT]}),flush=True)
    write(OUT/'decode-forward-low-native-cases.json',{'schema_version':manifest['schema_version'],'cases':rows,
        'variant_id':'glm78-low-complete-native-service','not_new_live_collection':True})
    write(OUT/'low-native-service-populations.json',{'cases':proofs,'producer_identity':identity(__file__),'raw_reads':0,'cost_predictions':0})


if __name__=='__main__':build()
