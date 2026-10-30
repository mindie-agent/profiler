"""Bind retained GLM78 grouped native means to one fused up and one down call.

[Role] Reuse explicit A8W4 MSD fusion and retained local ABI populations.
[Invariants] No per-sequence sparse/prolog floor; unsupported INT8 D656 remains
  visible. Native capacity never becomes a fabricated valid-route histogram.
[Timeouts & Locks] Bounded JSON and metadata graphs only; no locks.
[Side-Effect Policy] Independent case declarations; no simulation or raw scan.
"""
from copy import deepcopy

from build_qwen_a3_service_cases import ROOT, OUT, read, write, identity, physical_ops
from build_a3_observed_service_cases import pooled, _physical_match


def build():
    manifest=read(OUT/'decode-forward-a3-service-cases.json')
    rows=[];coverage=[]
    for original in manifest['cases']:
        if not original['case_id'].startswith('a3_glm53_w4a8_tp16'):continue
        row=deepcopy(original);cid=row['case_id'];old=row['sim_case_path'];raw=read(old)
        native_path=OUT/'glm78-native'/f'{cid}-native-partitions.json';native=read(native_path)
        if native['source_identity']['sha256']!=row['source']['sha256']:
            raise ValueError('native_source_mismatch')
        kernels=raw['runtime']['kernels'];kernels.setdefault('lowerings',{})['native_fusion']={
            'implementation':'declared_native_fusion','options':{
                'roles':['grouped_gate_up_activation_quant'],
                'program_profiles':{'grouped_gate_up_activation_quant':'ascend_w4a8_msd'}}}
        case,ops=physical_ops(raw,row['replay_input_pins']['primary_geometry'])
        records=[]
        for kind,recipe in [('GroupedMatmulSwigluQuantV2','ascend_w4a8_msd'),
                            ('GroupedMatmul','balanced_grouped_down')]:
            groups=[g for g in native['partitions'] if g['native_operator_type']==kind]
            stats=pooled(groups);programs=[o for o in ops if o.recipe==recipe]
            expected=stats['count']/native['forward_count']
            if expected!=75 or len(programs)!=75:raise ValueError('native_grouped_population_differs')
            abis={str(g['native_abi'])for g in groups}
            if len(abis)!=1:raise ValueError('native_grouped_ABI_not_homogeneous')
            abi=groups[0]['native_abi'];inputs,outputs=abi[2:4]
            width=6144 if kind=='GroupedMatmulSwigluQuantV2' else 2048
            outwidth=2048 if kind=='GroupedMatmulSwigluQuantV2' else 6144
            if (inputs[0][0][-1]!=width or inputs[0][1]!='int8'
                    or outputs[0][0][-1]!=outwidth or inputs[2 if kind=='GroupedMatmulSwigluQuantV2' else 7][0]!=[16]):
                raise ValueError('native_grouped_width_or_expert_bank_mismatch')
            matches=[_physical_match(case,op)for op in programs]
            if any(match!=matches[0]for match in matches):raise ValueError('declared_grouped_work_heterogeneous')
            view=dict(programs[0].metadata)
            if recipe=='ascend_w4a8_msd':
                tensor=view['fusion_tensor_view']
                for k,v in {'input_width':6144,'intermediate_width':2048,'local_experts':16,
                            'input_dtype':'int8','weight_dtype':'int4','output_dtype':'int8'}.items():
                    if tensor[k]!=v:raise ValueError('declared_fusion_ABI_mismatch:'+k)
                    matches[0]['metadata.fusion_tensor_view.'+k]=v
            else:
                if view['weight_dtype']!='int4' or view['matrix_weight_bank_groups']!=16:
                    raise ValueError('declared_down_expert_bank_mismatch')
                matches[0]['metadata.matrix_weight_bank_groups']=16
            rid=kind.lower()+'-complete-native-response'
            provenance={'calibration_origin':'observed','evaluation_relation':'in_sample',
                'native_identity':identity(native_path),'native_operator_type':kind,
                'observed':{k:v for k,v in stats.items()if k!='duration_ns_counter'},
                'forward_count':native['forward_count'],'expected_rule_hits':75,
                'native_abi':abi,'declared_physical_shape':list(programs[0].local_shape),
                'observed_buffer_capacity_rows':inputs[0][0][0], 'observed_valid_routed_rows':None,
                'routing_basis':'retained_symmetric_integer_declaration; values not observed',
                'response_boundary':'one_fused_up_call' if recipe=='ascend_w4a8_msd' else 'one_grouped_down_call',
                'body_residual_used':False,'strict_tensor_admission_changed':False}
            kernels['service_regimes'].append({'id':rid,'match':matches[0],
                'response':{'fixed_us':stats['mean_us']},'provenance':provenance})
            records.append({'rule_id':rid,**provenance})
        meta=raw['runtime']['metadata'];meta['calibration_origin']='observed'
        meta['calibration_evidence'].update(evaluation_relation='in_sample',
            additional_native_identity=identity(native_path),explicit_resource_fusion='ascend_w4a8_msd',
            unsupported_native_domains=['MlaPrologV3 INT8 cache D656','KvQuantSparseFlashAttention D656 rope64 batch'])
        target=OUT/'glm78-grouped-cases'/f'{cid}-grouped-service.json';write(target,raw)
        row.update(sim_case_path=str(target),model_declaration=identity(target),
            baseline_service_case_identity=identity(old),variant_id='glm78-grouped-observable-service-3b72ea2d',
            calibration_origin='observed',calibration_evidence=meta['calibration_evidence'])
        row['replay_input_pins']['case']=identity(target);rows.append(row);coverage.append({'case_id':cid,'rules':records})
    write(OUT/'glm78-grouped-service-populations.json',{'cases':coverage})
    write(OUT/'decode-forward-glm78-grouped-service-cases.json',{'schema_version':manifest['schema_version'],
        'variant_id':'glm78-grouped-observable-service-3b72ea2d','cases':rows,'not_new_live_collection':True})


if __name__=='__main__':
    build()
