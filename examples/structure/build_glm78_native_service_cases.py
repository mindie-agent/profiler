"""Assign complete retained native populations to the corrected GLM78 graph.

[Role] Rebind prior whole-call means and exact active tensor-contract populations.
[Invariants] Never fit Body residuals, split a histogram by predicted timing, or
  use capacity as routed rows. Unsupported contracts remain a visible inventory.
[Timeouts & Locks] Per-source bounded JSON and metadata-only graph expansion.
[Side-Effect Policy] Independent declarations and receipts; no raw/cost/device.
"""
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


def build():
    previous=OUT/'decode-forward-glm78-captured-grid-cases.json'
    original=read(previous); rows=[]; receipts=[]
    for before in original['cases']:
        if before['replay_input_pins']['primary_geometry']['query_rows']!=12:continue
        row=deepcopy(before);cid=row['case_id'];raw=read(row['sim_case_path']);geo=row['replay_input_pins']['primary_geometry']
        native_path=OUT/'glm78-native'/f'{cid}-native-partitions.json';native=read(native_path)
        if native['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('native_source_changed')
        # Existing lowering carries INT32 accumulator output into one DSQ call;
        # the retained full native descriptors below must validate both boundaries.
        raw['runtime']['kernels']['lowerings']['shared_expert']='ascend_shared_gate_up_int32'
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
        if not any(g['native_operator_type']=='DequantSwigluQuant' for g in assigned):
            raise ValueError('shared_INT32_DSQ_source_chain_not_verified')
        meta=raw['runtime']['metadata'];meta['calibration_origin']='observed'
        meta['calibration_evidence'].update(evaluation_relation='in_sample',native_identity=identity(native_path),
            assignment_basis='complete same-source native histograms plus fresh active contract equality',
            source_lowering='ascend_shared_gate_up_int32: INT32 accumulator plus native DSQ',
            unresolved_caller_gaps=['FFN/router M12-to16 Concat and native AllGather75 lack corresponding declared caller nodes',
                'router observed BF16 operands/FP32 output differs from current FP32 router declaration',
                'buffer capacities do not establish dynamic expert valid rows'])
        path=OUT/'glm78-native-service-cases'/f'{cid}-native-service.json';write(path,raw)
        row.update(sim_case_path=str(path),model_declaration=identity(path),baseline_service_case_identity=identity(before['sim_case_path']),
            variant_id='glm78-M12-complete-native-service-672a595f',calibration_origin='observed',calibration_evidence=meta['calibration_evidence'])
        row['replay_input_pins']['case']=identity(path);rows.append(row)
        receipts.append({'case_id':cid,'native_identity':identity(native_path),'forward_count':native['forward_count'],
            'rebound_prior_rules':rebound,'complete_contract_rules':assigned,'unassigned_contracts':excluded})
        print(cid,'rules',len(raw['runtime']['kernels']['service_regimes']),'new',len(assigned),flush=True)
    write(OUT/'glm78-native-service-populations.json',{'cases':receipts,'raw_reads':0,'cost_predictions':0})
    write(OUT/'decode-forward-glm78-native-service-cases.json',{'schema_version':original['schema_version'],
        'cases':rows,'baseline_identity':identity(previous),'not_new_live_collection':True})


if __name__=='__main__':build()
