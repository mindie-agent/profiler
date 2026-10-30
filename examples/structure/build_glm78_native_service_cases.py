"""Assign complete retained native populations to the corrected GLM78 graph.

[Role] Rebind prior whole-call means and exact active tensor-contract populations.
[Invariants] Never fit Body residuals, split a histogram by predicted timing, or
  use capacity as routed rows. Unsupported contracts remain a visible inventory.
[Timeouts & Locks] Per-source bounded JSON and metadata-only graph expansion.
[Side-Effect Policy] Independent declarations and receipts; no raw/cost/device.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import json
from types import SimpleNamespace

from build_qwen_a3_service_cases import OUT, identity, physical_ops, read, write
from build_a3_observed_service_cases import pooled, _physical_match
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure_contracts import predicted_contract


def freeze(value):
    return tuple(freeze(v) for v in value) if isinstance(value, (list, tuple)) else value


def descriptor(native):
    native=freeze(native)
    if not native:return None
    fields={'kind':native[1]}
    for direction,slots in zip(('input','output'),native[2:]):
        fields[direction+'_shapes']=tuple(s[0] for s in slots)
        fields[direction+'_dtypes']=tuple(s[1] if s[1] is not None else 'DT_UNDEFINED' for s in slots)
        fields[direction+'_formats']=tuple(s[2] if s[2] is not None else 'NULL' for s in slots)
    row=SimpleNamespace(**fields)
    if native_tensor_contract(row)!=native:raise ValueError('saved_native_ABI_not_preserved')
    return row


def build(router_bf16=False, caller_complete=False):
    router_bf16 = router_bf16 or caller_complete
    stem="glm78-caller-complete-service" if caller_complete else "glm78-router-native-service" if router_bf16 else "glm78-native-service"
    previous=OUT/'decode-forward-glm78-captured-grid-cases.json'
    original=read(previous); rows=[]; receipts=[]
    for before in original['cases']:
        if not caller_complete and before['replay_input_pins']['primary_geometry']['query_rows']!=12:continue
        row=deepcopy(before);cid=row['case_id'];raw=read(row['sim_case_path']);geo=row['replay_input_pins']['primary_geometry']
        native_path=OUT/'glm78-native'/f'{cid}-native-partitions.json';native=read(native_path)
        if native['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('native_source_changed')
        # Existing lowering carries INT32 accumulator output into one DSQ call;
        # the retained full native descriptors below must validate both boundaries.
        raw['runtime']['kernels']['lowerings']['shared_expert']='ascend_shared_gate_up_int32'
        if router_bf16:
            routers=[g for g in native['partitions'] if g['native_operator_type']=='MatMulV3'
                     and g['topology_region']=='ffn']
            if len(routers)!=1 or routers[0]['observed_us']['count']!=75*native['forward_count']:
                raise ValueError('router_complete_population_not_unique')
            abi=routers[0]['native_abi']
            if abi[2][:2]!=[[[geo['query_rows'],6144],'bf16','ND'],[[256,6144],'bf16','ND']] or abi[3]!=[[[geo['query_rows'],256],'fp32','ND']]:
                raise ValueError('router_native_precision_shape_differs')
            layers=sorted(int(layer) for layer in routers[0]['layer_counts'])
            if layers!=list(range(3,78)):raise ValueError('router_layer_population_differs')
            overrides=raw['model'].setdefault('layer_overrides',{})
            for layer in layers:
                overrides.setdefault(str(layer),{}).update(router_dtype='bf16',router_output_dtype='fp32')
        if caller_complete:
            from build_qwen_a3_service_cases import FIXED
            source_path=FIXED/'examples/cases/high-concurrency-20261030/glm78-capture-rows'/f'{cid}.json'
            source_case=read(source_path)
            if source_case['runtime']['graph_capture_keys']!=raw['runtime']['graph_capture_keys']:
                raise ValueError('source_capture_grid_differs')
            raw['runtime']['kernels']['moe_token_partition']=deepcopy(source_case['runtime']['kernels']['moe_token_partition'])
            raw['runtime']['lowering_passes']=['activation_quantization','norm_quant','residual_norm']
            raw['runtime']['kernels']['fusion_domains']={'norm_quant':{'consumers':[{'recipe':'dense_gate_up'}]}}
            for family in ('add_rmsnorm','add_rmsnorm_quant'):
                raw['runtime']['kernels']['lowerings'][family]={'implementation':'vllm_ascend_native_norm','options':{'has_bias':True}}
            raw['runtime']['metadata']['caller_source_case_identity']=identity(source_path)
        case,ops=physical_ops(raw,geo)
        prior=deepcopy(raw['runtime']['kernels']['service_regimes']); rebound=[]
        for rule in prior:
            selected=[o for o in ops if o.recipe==rule['match']['recipe'] and o.family==rule['match']['family']]
            matches=[_physical_match(case,o) for o in selected]
            expected=rule['provenance']['expected_rule_hits']
            if len(selected)!=expected or any(m!=matches[0] for m in matches):
                raise ValueError('retained_whole_call_population_changed:'+rule['id'])
            physical=matches[0]
            for k,v in rule['match'].items():
                if k.startswith('metadata.'):
                    actual=dict(selected[0].metadata)
                    for part in k.split('.')[1:]:actual=actual[part]
                    if actual!=v:raise ValueError('retained_native_program_axes_changed')
                    physical[k]=v
            rule['provenance']['previous_physical_match']=deepcopy(rule['match'])
            rule['provenance']['rebind_basis']='same retained whole-call population; source-corrected M12 graph geometry'
            rule['match']=physical;rebound.append({'id':rule['id'],'expected_hits':expected,'new_match':physical})
        raw['runtime']['kernels']['service_regimes']=prior
        by_contract=defaultdict(list)
        for op in ops:
            contract=predicted_contract(op.to_dict(include_work=False))
            if contract is not None:by_contract[freeze(contract)].append(op)
        observed=defaultdict(list);excluded=[]
        for i,group in enumerate(native['partitions']):
            r=descriptor(group['native_abi'])
            contract=observed_contract(r) if r is not None else None
            if contract is None:continue
            observed[(group['native_operator_type'],freeze(contract))].append((i,group))
        assigned=[]
        for (kind,contract),members in observed.items():
            groups=[g for _,g in members];stats=pooled(groups);selected=by_contract.get(contract,[])
            expected=stats['count']/native['forward_count']
            if not selected or len(selected)!=expected:
                excluded.append({'native_operator_type':kind,'contract':contract,'observed_calls_per_forward':expected,
                    'declared_calls':len(selected),'observed_us':{k:v for k,v in stats.items() if k!='duration_ns_counter'},
                    'reason':'no_exact_declared_contract' if not selected else 'declared_population_differs'})
                continue
            matches=[_physical_match(case,o) for o in selected]
            if any(m!=matches[0] for m in matches):
                excluded.append({'native_operator_type':kind,'contract':contract,'observed_calls_per_forward':expected,
                    'declared_calls':len(selected),'reason':'physical_domains_differ_without_observed_partition'})
                continue
            if {o.op_id for o in ops if _physical_match(case,o)==matches[0]}!={o.op_id for o in selected}:
                raise ValueError('physical_selector_admits_other_contracts')
            rid=f"complete-{kind.lower()}-{len(assigned)}"
            evidence={'calibration_origin':'observed','evaluation_relation':'in_sample','native_identity':identity(native_path),
                'source_identity':native['source_identity'],'native_operator_type':kind,'partition_indices':[i for i,_ in members],
                'contract':contract,'observed_us':{k:v for k,v in stats.items() if k!='duration_ns_counter'},
                'forward_count':native['forward_count'],'expected_rule_hits':len(selected),
                'target_ids':[o.op_id for o in selected],'response_boundary':'one_complete_active_contract_kernel_call',
                'parameter_statistic':'full_native_population_arithmetic_mean_us','body_residual_used':False,
                'strict_admission_changed':False,'occurrence_binding_implied':False}
            raw['runtime']['kernels']['service_regimes'].append({'id':rid,'match':matches[0],
                'response':{'fixed_us':stats['mean_us']},'provenance':evidence})
            assigned.append({'rule_id':rid,'match':matches[0],**evidence})
        caller_rules=[]
        if caller_complete:
            # Only the two source-declared materialized concat calls and final
            # TP collective are assigned. Generic pack/transport is not MC2.
            for kind,selected in [('ConcatD',[o for o in ops if o.recipe=='tensor_concat']),
                                  ('hcom_allGather_',[o for o in ops if o.recipe=='ring_allgather'])]:
                buckets=defaultdict(list)
                for op in selected:buckets[json.dumps(_physical_match(case,op),sort_keys=True)].append(op)
                for key,targets in buckets.items():
                    meta=dict(targets[0].metadata)
                    if kind=='ConcatD':
                        expected_abi=('native_tensor_abi',kind,tuple((tuple(sh),targets[0].dtype,'ND') for sh in meta['input_shapes']),
                                      ((tuple(meta['output_shape']),targets[0].dtype,'ND'),))
                        measured=[(i,g) for i,g in enumerate(native['partitions']) if freeze(g['native_abi'])==expected_abi]
                    else:
                        measured=[(i,g) for i,g in enumerate(native['partitions']) if g['native_operator_type']==kind]
                        if meta.get('collective_role')!='mc2_finalize_token_reconstruction':
                            raise ValueError('allgather_not_source_finalize_boundary')
                    stats=pooled([g for _,g in measured])
                    if len(targets)!=75 or stats['count']!=75*native['forward_count']:
                        raise ValueError('caller_complete_population_differs:'+kind)
                    rid='source-caller-'+kind.lower()+'-'+str(len(caller_rules))
                    proof={'calibration_origin':'observed','evaluation_relation':'in_sample','native_identity':identity(native_path),
                        'source_identity':native['source_identity'],'native_operator_type':kind,'partition_indices':[i for i,_ in measured],
                        'forward_count':native['forward_count'],'expected_rule_hits':75,
                        'observed_us':{k:v for k,v in stats.items() if k!='duration_ns_counter'},
                        'response_boundary':'one_complete_source_caller_kernel','body_residual_used':False,
                        'source_caller':meta['moe_token_partition'],'strict_admission_changed':False,
                        'full_abi_equal':kind=='ConcatD', 'source_payload_is_derived_not_tensor_observed':kind!='ConcatD'}
                    raw['runtime']['kernels']['service_regimes'].append({'id':rid,'match':json.loads(key),
                        'response':{'fixed_us':stats['mean_us']},'provenance':proof})
                    caller_rules.append({'rule_id':rid,'match':json.loads(key),**proof})
            graph_counts={recipe:sum(o.recipe==recipe for o in ops) for recipe in
                ('add_rmsnorm','add_rmsnorm_quantize','route_pack','route_unpack','dynamic_quantize','ring_allgather','tensor_concat')}
            if graph_counts['add_rmsnorm']!=152 or graph_counts['add_rmsnorm_quantize']!=3 or graph_counts['ring_allgather']!=75:
                raise ValueError('source_norm_or_caller_population_differs')
        if not any(g['native_operator_type']=='DequantSwigluQuant' for g in assigned):
            raise ValueError('shared_INT32_DSQ_source_chain_not_verified')
        meta=raw['runtime']['metadata'];meta['calibration_origin']='observed'
        if router_bf16:
            meta['router_precision_source']={'native_identity':identity(native_path),'native_operator_type':'MatMulV3',
                'captured_operand_dtype':'bf16','captured_output_dtype':'fp32','calls_per_forward':75,
                'layer_indices':layers,'source_basis':'complete retained FFN router contract population','body_timing_used':False}
        meta['calibration_evidence'].update(evaluation_relation='in_sample',native_identity=identity(native_path),
            assignment_basis='complete same-source native histograms plus fresh active contract equality',
            source_lowering='ascend_shared_gate_up_int32: INT32 accumulator plus native DSQ',
            unresolved_caller_gaps=[*(['FFN/router M12-to16 Concat and native AllGather75 lack corresponding declared caller nodes'] if not caller_complete else ['Native MC2 boundary remains decomposed pack/transport/quant; no complete MC2 response is assigned']),
                *(['router observed BF16 operands/FP32 output differs from current FP32 router declaration'] if not router_bf16 else []),
                'buffer capacities do not establish dynamic expert valid rows'])
        if caller_complete:
            conditions=meta['packed_D656_source_condition']
            conditions['separate_ffn_concat_gap']='Source caller right_to_tp pads hidden/logits locally and trims after TP AllGather; all materialized Concat and gather invocations are declared.'
            conditions['norm_quant_domain']={'consumers':[{'recipe':'dense_gate_up'}]}
            conditions['router_operand_dtype']='bf16'
            conditions['router_output_dtype']='fp32'
            conditions['mc2_remaining_boundary']='Generic pack/transport/quant remains decomposed; no whole native MC2 service assigned.'
            meta['calibration_evidence']['packed_source_condition']=conditions
            row.setdefault('scenario_evidence',{})['source_recipe_conditions']=deepcopy(conditions)
        path=OUT/(stem+'-cases')/f'{cid}-native-service.json';write(path,raw)
        row.update(sim_case_path=str(path),model_declaration=identity(path),baseline_service_case_identity=identity(before['sim_case_path']),
            variant_id=stem+('-c2b21f20' if caller_complete else '-672a595f'),calibration_origin='observed',calibration_evidence=meta['calibration_evidence'])
        row['replay_input_pins']['case']=identity(path);rows.append(row)
        receipts.append({'case_id':cid,'native_identity':identity(native_path),'forward_count':native['forward_count'],
            'rebound_prior_rules':rebound,'complete_contract_rules':assigned,'unassigned_contracts':excluded,
            'caller_rules':caller_rules,'source_graph_counts':graph_counts if caller_complete else None})
        print(cid,'rules',len(raw['runtime']['kernels']['service_regimes']),'new',len(assigned),flush=True)
    write(OUT/(stem+'-populations.json'),{'cases':receipts,'raw_reads':0,'cost_predictions':0})
    write(OUT/('decode-forward-'+stem+'-cases.json'),{'schema_version':original['schema_version'],
        'cases':rows,'baseline_identity':identity(previous),'not_new_live_collection':True})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--router-bf16',action='store_true')
    parser.add_argument('--caller-complete',action='store_true')
    args=parser.parse_args()
    build(args.router_bf16,args.caller_complete)
