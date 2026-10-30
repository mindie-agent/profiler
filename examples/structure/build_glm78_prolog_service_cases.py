"""Bind both complete packed D656 prolog output contracts to native service.

[Role] Add 57 ordinary and 21 query-normalizing prolog calls per Forward.
[Invariants] Existing source fusion and native ABI agree; the optional INT8
  query-normalization output separates populations without using layer names.
[Timeouts & Locks] Bounded retained JSON and metadata graph per source; no waits.
[Side-Effect Policy] Own declarations/proof only; no raw, device or Sim mutation.
"""
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from build_glm78_joint_service_cases import EXECUTION, pooled
from build_glm78_native_service_cases import descriptor, freeze
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure_subgraphs import subgraph_contract


HERE=Path(__file__).resolve().parent
BASE=HERE/'acceptance-20261030-a3-tail-service-refinement/glm78-indexer-routing/decode-forward-glm78-tail-cases.json'
NATIVE=HERE/'acceptance-20261030-service-qwen-a3/glm78-native'
OUT=HERE/'acceptance-20261030-a3-tail-service-refinement/glm78-prolog'


def build():
    manifest=read(BASE);output=deepcopy(manifest);output['cases']=[];proofs=[]
    for row in manifest['cases']:
        raw=read(row['sim_case_path']);prior=deepcopy(raw['runtime']['kernels']['service_regimes'])
        geo=row['replay_input_pins']['primary_geometry'];case,ops=physical_ops(raw,geo)
        path=NATIVE/f"{row['case_id']}-native-partitions.json";native=read(path)
        if native['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('source_changed')
        actual=defaultdict(list);declared=defaultdict(list)
        for i,g in enumerate(native['partitions']):
            if g['native_operator_type']!='MlaPrologV3':continue
            contract=observed_contract(descriptor(g['native_abi']))
            if contract is None:raise ValueError('packed_prolog_contract_not_supported')
            actual[freeze(contract)].append((i,g))
        for op in ops:
            meta=dict(op.metadata)
            if meta.get('fusion_role')!='mla_prolog':continue
            contract=subgraph_contract({'role':'mla_prolog','tensor_view':meta['fusion_tensor_view']})
            if op.link_bytes or meta.get('device_kernel_group'):raise ValueError('prolog_not_local_native')
            declared[freeze(contract)].append(op)
        if actual.keys()!=declared.keys() or len(actual)!=2:raise ValueError('prolog_output_contract_sets_differ')
        added=[]
        for contract,groups in actual.items():
            selected=declared[contract];stats=pooled([g for _,g in groups]);F=native['forward_count']
            qnorm=bool(dict(selected[0].metadata)['fusion_tensor_view']['query_norm_output'])
            expected=21 if qnorm else 57
            if len(selected)!=expected or stats['count']!=expected*F:raise ValueError('prolog_population_differs')
            matches=[]
            for op in selected:
                view=dict(op.metadata)['fusion_tensor_view'];match=_physical_match(case,op)
                match['metadata.fusion_role']='mla_prolog'
                for key,value in view.items():
                    if isinstance(value,(str,int,float,bool)) or value is None:
                        match['metadata.fusion_tensor_view.'+key]=value
                for key in ('row_bytes','group_size','layout','latent_dtype','rope_dtype','scale_dtype'):
                    match['metadata.fusion_tensor_view.packed_cache.'+key]=view['packed_cache'][key]
                matches.append(match)
            if any(m!=matches[0]for m in matches):raise ValueError('prolog_physical_domains_differ')
            rid='packed-prolog-querynorm-'+str(qnorm).lower()+'-joint'
            evidence={'calibration_origin':'observed','evaluation_relation':'in_sample',
                'native_operator_type':'MlaPrologV3','native_identity':identity(path),
                'source_identity':native['source_identity'],'partition_indices':[i for i,_ in groups],
                'full_native_abis':[g['native_abi']for _,g in groups],'active_contract':contract,
                'complete_population':stats,'forward_count':F,'expected_rule_hits':expected,
                'query_norm_output':qnorm,'declared_target_ids':[o.op_id for o in selected],
                'response_boundary':'one_complete_local_MlaPrologV3_call_including_optional_output',
                'body_residual_used':False,'strict_tensor_admission_changed':False,
                'native_scalar_values_observed':False,'pointer_aliasing_observed':False}
            raw['runtime']['kernels']['service_regimes'].append({'id':rid,'match':matches[0],
                'response':{'fixed_us':stats['mean_us']},
                'execution':{**EXECUTION,'native_kernel':'MlaPrologV3'},'provenance':evidence})
            added.append({'rule_id':rid,'match':matches[0],**evidence})
        if raw['runtime']['kernels']['service_regimes'][:len(prior)]!=prior:raise ValueError('prior_rules_changed')
        target=OUT/'cases'/f"{row['case_id']}-prolog-joint.json";write(target,raw)
        new=deepcopy(row);new.update(sim_case_path=str(target),model_declaration=identity(target),variant_id='glm78-packed-prolog-joint')
        new['replay_input_pins']['case']=identity(target)
        new['calibration_evidence']['packed_prolog_services']=[{k:r[k] for k in ('rule_id','query_norm_output','expected_rule_hits')}for r in added]
        output['cases'].append(new)
        proofs.append({'case_id':row['case_id'],'prior_case_identity':identity(row['sim_case_path']),
            'case_identity':identity(target),'prior_rules_unchanged':True,'added_rules':added})
        print(json.dumps({'case_id':row['case_id'],'prolog_domains':[(r['query_norm_output'],r['complete_population']['mean_us'],r['expected_rule_hits'])for r in added]}),flush=True)
    output['baseline_identity']=identity(BASE);output['variant_id']='glm78-packed-prolog-joint'
    write(OUT/'decode-forward-prolog-service-cases.json',output)
    write(OUT/'prolog-service-populations.json',{'cases':proofs,'producer_identity':identity(__file__),
        'contract_parser_identity':identity(HERE.parents[1]/'mindie_profiler/body_subgraph_contracts.py'),
        'raw_reads':0,'cost_predictions':0})


if __name__=='__main__':build()
