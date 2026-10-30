"""Qwen3.5 TP-sliced MC2 and typed grouped caller correspondence.

[Role] Revalidate complete retained native buckets against the Sim frontend.
[Invariants] Buffer capacity never supplies valid routed rows. Exact layer
  multiplicity is retained; INT32 accumulators and their scale producers remain
  separate boundaries. No latency selects a role or program.
[Timeouts & Locks] Bounded metadata only; no subprocesses, captures or locks.
[Side-Effect Policy] Return fresh plans/audits without changing Sim declarations.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256

from body_source_role_references import canonical
from rebind_body_source_roles import freeze


def named(nodes, role):
    values=[n for n in nodes if n['op_id'].split('.',2)[-1]==role]
    if len(values)!=1:raise ValueError('caller_role_not_unique:'+role)
    return values[0]


def grouped_contract(native):
    """Validate the retained packed INT8 8/9-slot branches, including outputs."""
    native=freeze(native)
    if not native or native[:2]!=('native_tensor_abi','GroupedMatmul'):return None
    ins,outs=native[2:]
    if len(ins) not in (8,9) or len(outs)!=1:return None
    x,w,bias,scale,offset,anti,anti_offset,counts=ins[:8];y=outs[0]
    if len(x[0])!=2 or len(y[0])!=2 or len(w[0])!=5:return None
    rows,k=x[0];yrows,n=y[0];experts=w[0][0]
    if (rows!=yrows or min(rows,k,n,experts)<1 or n%32 or k%16
            or x[1:]!=('int8','ND') or w!=((experts,n//32,k//16,16,32),'int8','FRACTAL_NZ')
            or y[2]!='ND' or counts!=((experts,),'int64','ND')
            or bias!=((),'int32','ND') or offset!=((),'fp32','ND')
            or anti!=((),'fp16','ND') or anti_offset!=((),'fp16','ND')):return None
    if len(ins)==8:
        if scale not in (((),'UINT64','ND'),((),'uint64','ND')) or y[1]!='int32':return None
        return ('grouped_matrix',(experts,rows,n,k),'int8','int8','int32',(),'')
    xs=ins[8]
    if scale!=((experts,n),'bf16','ND') or xs!=((rows,),'fp32','ND') or y[1]!='bf16':return None
    return ('grouped_matrix',(experts,rows,n,k),'int8','int8','bf16',(rows,),'fp32')


def audit_typed_chain(manifest):
    """Check every real layer's typed producer/consumer edges, not one example."""
    replica=min(manifest['execution']['replicas']);layers=defaultdict(list)
    for n in manifest['nodes']:
        if n['replica']==replica and n.get('layer') is not None:layers[n['layer']].append(n)
    full=manifest['execution']['tokens']*manifest['execution']['sequences'];rows=[]
    for layer,local in sorted(layers.items()):
        by={n['op_id']:n for n in local};router=named(local,'router');topk=named(local,'topk')
        dispatch=named(local,'dispatch');up=named(local,'expert_up');act=named(local,'expert_act');down=named(local,'expert_down')
        rm,tm,dm,um,am,lm=[n['operator']['metadata'] for n in (router,topk,dispatch,up,act,down)]
        local_tokens=topk['operator']['local_shape'][0];valid=up['operator']['local_shape'][0]
        if router['operator']['local_shape'][0]!=full or local_tokens*4!=full:
            raise ValueError('router_full_rows_topk_TP4_rows_differ')
        for name in ('shared.gate_up','shared.down'):
            if named(local,name)['operator']['local_shape'][0]!=full:raise ValueError('shared_full_rows_differ')
        if (dm.get('output_format')!='int8' or dm.get('activation_payload_shape')!=[valid,up['operator']['local_shape'][2]]
                or dm.get('activation_scale_shape')!=[valid] or dm.get('activation_scale_format')!='fp32'
                or dm.get('activation_scale_bytes')!=valid*4 or 'activation_scales' not in dispatch['operator']['returns']):
            raise ValueError('dispatch_receiver_payload_scale_contract')
        if (um.get('activation_payload_producer')!=dispatch['op_id'] or um.get('activation_scale_producer')!=dispatch['op_id']
                or up['operator']['deps']!=[dispatch['op_id']] or um.get('output_format')!='int32'):
            raise ValueError('INT32_up_requires_received_payload_and_scale')
        if (am.get('input_row_scale_producer')!=dispatch['op_id'] or act['operator']['deps']!=[up['op_id'],dispatch['op_id']]
                or am.get('input_format')!='int32' or am.get('output_format')!='int8'
                or am.get('activation_scale_shape')!=[valid] or am.get('activation_scale_format')!='fp32'
                or 'activation_scales' not in act['operator']['returns']):
            raise ValueError('dequant_activation_producer_contract')
        if (lm.get('activation_payload_producer')!=act['op_id'] or lm.get('activation_scale_producer')!=act['op_id']
                or down['operator']['deps']!=[act['op_id']] or lm.get('output_format')!='bf16'):
            raise ValueError('down_requires_activation_owned_payload_and_scale')
        duplicate=[n['op_id'] for n in local if n['op_id'].split('.',2)[-1] in {'expert_up.quantize','expert_down.quantize'}
                   or n['recipe']=='expert_scale_dispatch']
        if duplicate:raise ValueError('duplicate_expert_quantization_or_scale_transport')
        copies=[n for n in local if '.mc2_gather_copy' in n['op_id']]
        collectives=Counter(n['operator']['metadata']['hccl_selection']['collective'] for n in local
            if n['recipe']=='hccl_entry')
        if collectives!={'allreduce':2,'allgather':1}:raise ValueError('TP_caller_collective_population')
        rows.append({'layer':layer,'attention_kind':router['structure']['attention_kind'],
            'router_shared_rows':full,'topk_source_rows':local_tokens,'declared_valid_routed_rows':valid,
            'dispatch_payload_producer':dispatch['op_id'],'INT32_producer':up['op_id'],
            'down_scale_producer':act['op_id'],'down_consumer':down['op_id'],
            'scale_shape':[valid],'scale_dtype':'fp32','independent_expert_scale_or_quant_nodes':duplicate,
            'collective_calls':dict(collectives),'FFN_materialization_calls':len(copies)})
    return {'layer_count':len(rows),'layers':rows,'observed_valid_routed_rows':None,
        'interpretation':'Declared typed chain validated on every layer; tensor pointer aliases and group counts are not observed.'}


def signature(nodes):
    """Normalize occurrence references while preserving all executable metadata."""
    ids={n['op_id']:f'node:{i}' for i,n in enumerate(nodes)}
    def normalize(value):
        if isinstance(value,dict):return {k:normalize(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)):return [normalize(v) for v in value]
        if isinstance(value,str):
            if value in ids:return ids[value]
            if value.startswith('s') and len(value.split('.',2))==3:
                stage,layer,tail=value.split('.',2)
                if stage[1:].isdigit() and layer.startswith('l') and layer[1:].isdigit():return 'occurrence.'+tail
        return value
    result=[]
    for n in nodes:
        op=deepcopy(n['operator'])
        for k in ('op_id','layer','stage','notes','requests'):op.pop(k,None)
        # External dependencies control readiness, while an isolated reference
        # prices only this boundary. Internal edges and all peer requests remain.
        op['deps']=[ids[d] for d in op['deps'] if d in ids]
        for k in ('structure_subgraphs','structure_subgraph_entries','structure_subgraph_memberships','fused_origin_scopes'):
            op['metadata'].pop(k,None)
        result.append({'operator':normalize(op),'physical_work':n['physical_work']})
    return canonical(result)


def select(native,part,local):
    kind=part['native_operator_type'];ins,outs=native[2:]
    if part['topology_region']!='ffn':raise ValueError('outside_selected_FFN_caller; attention_layout_copy_not_reclassified')
    capacity=None
    if kind=='GroupedMatmul':
        contract=grouped_contract(native)
        if contract is None:raise ValueError('unsupported_complete_packed_INT8_GMM_ABI')
        role='expert_up' if contract[4]=='int32' else 'expert_down';node=named(local,role)
        expected=freeze(node['contract']);e,m,n,k=contract[1]
        if (expected[0]!='grouped_matrix' or (expected[1][0],expected[1][2],expected[1][3])!=(e,n,k)
                or expected[2:5]!=contract[2:5] or expected[6]!=contract[6]
                or expected[1][1]>m):raise ValueError('GMM_expert_weight_precision_or_capacity_differs')
        if part['native_type_ordinal_in_region']!=({'expert_up':1,'expert_down':2}[role]):raise ValueError('GMM_topology_order_conflicts_with_weight_axes')
        nodes=[node];capacity=m
    elif kind=='DequantSwigluQuant':
        role='expert_act';node=named(local,role);expected=deepcopy(node['contract']);capacity=ins[0][0][0]
        # Only row capacity differs. All seven inputs, scales and both outputs
        # must otherwise match the source-owned native contract exactly.
        valid=expected[2][0][0][0]
        if capacity<valid:raise ValueError('DSQ_capacity_smaller_than_declared_rows')
        for direction,slot in ((2,0),(2,2),(3,0),(3,1)):expected[direction][slot][0][0]=capacity
        if freeze(expected)!=native:raise ValueError('DSQ_complete_scale_and_output_ABI_differs')
        nodes=[node]
    elif kind=='MoeDistributeDispatchV3':
        role='dispatch';last=named(local,role);meta=last['operator']['metadata'];params=meta['mc2_phase']
        b,h,topk=params['source_tokens'],params['width'],params['top_k']
        experts,ep=params['experts'],params['ep']
        if len(ins)!=8 or len(outs)!=7:raise ValueError('Dispatch_8input_7output_ABI')
        capacity=outs[0][0][0]
        if (ins[0]!=((4100,),'int32','ND') or ins[1]!=((b,h),'bf16','ND') or ins[2]!=((b,topk),'int32','ND') or ins[4]!=((b,),'bool','ND')
                or any(ins[i]!=((),None,None) for i in (3,5,6,7)) or outs[0]!=((capacity,h),'int8','ND')
                or outs[1]!=((capacity,),'fp32','ND') or outs[6]!=((capacity,),'fp32','ND')
                or outs[2]!=((capacity*128,),'int32','ND')
                or outs[3]!=((experts//ep,),'int64','ND')
                or outs[4]!=((experts,),'int32','ND') or outs[5]!=((1,),'int32','ND')
                or capacity<meta['activation_payload_shape'][0]):raise ValueError('Dispatch_local_rows_received_quantization_ABI')
        nodes=[n for n in local if n['operator']['metadata'].get('native_kind')==kind]
    elif kind=='MoeGatingTopK':
        role='topk';node=named(local,role);shape=node['operator']['local_shape'];b,e=shape[:2]
        views=[v['tensor_view'] for v in node['operator']['metadata'].get('structure_subgraphs',[]) if v.get('role')=='router_selection']
        if len(views)!=1:raise ValueError('TopK_source_selection_boundary_missing')
        k=views[0]['topk']
        if native!=('native_tensor_abi',kind,(((b,e),'bf16','ND'),),(((b,k),'bf16','ND'),((b,k),'int32','ND'),((b,e),'fp32','ND'))):
            raise ValueError('TopK_local_rows_full_native_output_ABI')
        nodes=[node]
    elif kind=='TensorMove':
        role='post_gather_materialization';nodes=[n for n in local if '.mc2_gather_copy' in n['op_id']]
        if len(nodes)!=4:raise ValueError('four_explicit_post_gather_copies_required')
        shape=tuple(nodes[0]['operator']['local_shape'])
        if native!=('native_tensor_abi',kind,((shape,'bf16','ND'),),((shape,'bf16','ND'),)):
            raise ValueError('post_gather_complete_copy_ABI')
        if any((n['physical_signature'],n['physical_work'])!=(nodes[0]['physical_signature'],nodes[0]['physical_work']) for n in nodes):raise ValueError('copy_programs_not_homogeneous')
        nodes=[nodes[0]]  # Any identical physical instance; no ordinal→TP rank claim.
    else:raise ValueError('native_type_outside_Qwen35_caller')
    if not nodes:raise ValueError('empty_native_program')
    return role,nodes,{'boundary_relation':('source_topk_two_output_program_with_unmodeled_observed_third_output'
            if kind=='MoeGatingTopK' else 'complete_source_caller_reference'),
        'observed_third_output_modeled':False if kind=='MoeGatingTopK' else None,
        'partial_work_boundary':kind=='MoeGatingTopK',
        'observed_native_tensor_contract':native,'observed_buffer_row_capacity':capacity,
        'observed_valid_routed_rows':None,'observed_group_list_values':None,
        'declared_valid_routed_rows':named(local,'expert_up')['operator']['local_shape'][0] if capacity else None,
        'limitations':['Captured allocation capacity is not valid routed rows or active expert counts.',
            'Binary/template selection, scalar flags, peer readiness and pointer aliases are not proven.',
            'The complete native histogram remains whole; no latency assigns a role or a layer.',
            'Physical service residuals are not additive Body wall-clock contributions.'] +
            (['Source TopK models weights and ids only; observed full FP32 third output is not included, so this is a partial-work boundary.'] if kind=='MoeGatingTopK' else [])}


def prepare(partitions,manifest):
    replica=min(manifest['execution']['replicas']);layers=defaultdict(list)
    for n in manifest['nodes']:
        if n['replica']==replica:layers[n.get('layer')].append(n)
    refs,unresolved,programs=[],[],{}
    for index,part in enumerate(partitions['partitions']):
        buckets={};native=freeze(part['native_abi'])
        try:
            if native is None:raise ValueError('native_ABI_missing')
            for layer,count in sorted((int(l),n) for l,n in part['layer_counts'].items()):
                role,nodes,correspondence=select(native,part,layers[layer]);key=sha256(signature(nodes).encode()).hexdigest()
                programs.setdefault(key,{'program_set_key':key,'representative_replica':replica,
                    'declared_role':role,'representative_target_ids':[n['node_id'] for n in nodes],
                    'physical_program_signatures':[n['physical_signature'] for n in nodes],
                    'physical_work_per_program':[n['physical_work'] for n in nodes],
                    'source_correspondence':correspondence,'nodes':nodes})
                bucket=buckets.setdefault(key,{'program_set_key':key,'layer_ids':[],'event_count':0})
                bucket['layer_ids'].append(layer);bucket['event_count']+=count
        except ValueError as error:
            unresolved.append({'partition_index':index,'native_operator_type':part['native_operator_type'],
                'event_count':part['observed_us']['count'],'reason':str(error)});continue
        refs.append({'group_id':'qwen35:'+str(index),'partition_index':index,
            'native_operator_type':part['native_operator_type'],'native_abi':native,'declared_role':role,
            'layer_ids':sorted(map(int,part['layer_counts'])),'program_buckets':list(buckets.values()),
            'duration_ns_counter':part['duration_ns_counter'],'observed_us':part['observed_us'],
            'observed_activity_sum_ns':sum(ns*n for ns,n in part['duration_ns_counter']),
            'strict_accuracy_implied':False,'occurrence_binding_implied':False,'additional_budget_allowed':False})
    used={b['program_set_key'] for g in refs for b in g['program_buckets']}
    return refs,unresolved,{k:v for k,v in programs.items() if k in used}
