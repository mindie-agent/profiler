"""Relate complete V4.1 native ABI buckets to existing semantic programs.

[Role] Account for output projection, partial RoPE and packed cache insertion.
[Invariants] Whole-layer topology disambiguates equal Q/output RoPE descriptors.
  A combined Q/KV program cannot be duplicated into two kernel costs. Reserved
  compressed rows and slot arrays never prove valid writes. No extra Body budget.
[Timeouts & Locks] Finite retained metadata; no raw reads, workers or locks.
[Side-Effect Policy] Pure selections and compact reference manifests only.
"""
from collections import Counter, defaultdict
from hashlib import sha256
from math import prod

from body_source_role_references import canonical, reference_signature
from rebind_body_source_roles import freeze
from replay_body_operator_families import duration_stats


SOURCE = {
    'repository':'cann-recipes-infer',
    'path':'models/deepseek_v4/models/modeling_deepseek.py',
    'symbols':['update_win_kv','o_a_proj'],
    'lines':[[1415,1435],[1532,1572]],
    'scope':'independent source semantics; capture binary identity unproven',
}
ROPE_SOURCE = {
    'repository':'vllm-ascend',
    'path':'vllm_ascend/attention/dsa_v41.py',
    'lines':[[283,305],[430,452],[596,611]],
    'indexer_path':'vllm_ascend/models/deepseek_v41/indexer.py',
    'indexer_lines':[[93,105],[133,143]],
    'scope':'independent source semantics; capture binary identity unproven',
}


def _slot(value, shape, dtype, layout='ND'):
    return value == (tuple(shape),dtype,layout)


def classify(group, execution):
    """Identify the semantic role from full ABI and the verified local region."""
    native=freeze(group['native_abi']);kind=group['native_operator_type']
    if not native or native[:2] != ('native_tensor_abi',kind):
        raise ValueError('complete_native_abi_missing')
    ins,outs=native[2:];rows=execution['tokens']*execution['sequences']
    before=group['topology_region']=='before_attention_anchor'
    ordinal=group['same_abi_ordinal_in_region']
    if kind=='TransposeQuantBatchMatMul':
        if len(ins)!=4 or len(outs)!=1 or len(ins[0][0])!=3 or before:
            raise ValueError('transpose_quant_output_projection_boundary')
        m,heads,k=ins[0][0];n=outs[0][0][-1]
        if (m!=rows or k%64 or not _slot(ins[0],(m,heads,k),'fp8_e4m3')
                or not _slot(ins[1],(heads,k,n),'fp8_e4m3')
                or not _slot(ins[2],(m,heads,k//64,2),'fp8_e8m0','NCHW')
                or not _slot(ins[3],(heads,k//64,n,2),'fp8_e8m0','NCHW')
                or not _slot(outs[0],(m,heads,n),'bf16')):
            raise ValueError('transpose_quant_native_mx_abi')
        return 'grouped_output_a',{'native_view':{'rows':m,'heads':heads,'n':n,'k':k},
            'input_quantization_is_separate_native_call':True},SOURCE
    if kind=='InplacePartialRotaryMul':
        if len(ins)!=3 or len(outs)!=1 or len(ins[0][0])!=4:
            raise ValueError('rotary_native_slots')
        batch,s,heads,width=ins[0][0]
        if (batch*s!=rows or ins[0][1:]!=('bf16','ND') or outs[0]!=ins[0]
                or not _slot(ins[1],(batch,s,1,64),'fp32') or ins[2]!=ins[1]):
            raise ValueError('rotary_native_active_layout')
        if not before and (heads,width)==(64,512):role='output_inverse_rotary'
        elif before and (heads,width)==(64,512):role='q_rotary'
        elif before and (heads,width)==(1,512):role='kv_rotary' if ordinal==1 else 'compress_rotary' if ordinal==2 else None
        elif before and (heads,width)==(32,128):role='index_query_rotary'
        elif before and (heads,width)==(1,128):role='index_rotary'
        else:role=None
        if role is None:raise ValueError('rotary_source_role_not_unique')
        return role,{'observed_tensor_rows':rows,'observed_heads':heads,'observed_width':width,
            'observed_rotary_width':64,'cos_sin_values_observed':False,
            'rotation_direction_basis':'source call and whole-layer pre/post attention boundary',
            'observed_valid_compressed_rows':None if role in {'compress_rotary','index_rotary'} else rows},ROPE_SOURCE
    if kind=='KvCompressEpilogV2':
        if len(ins)!=3 or len(outs)!=1 or len(ins[0][0])!=4 or not before:
            raise ValueError('cache_epilog_native_slots')
        cache,x,slots=ins
        if (cache[0][2]!=1 or cache[2]!='ND' or outs[0]!=cache
                or not _slot(x,(rows,512),'bf16') or not _slot(slots,(rows,),'int64')):
            raise ValueError('cache_epilog_active_x_and_slot_abi')
        if cache[0][-1]==544 and cache[1]=='fp8_e4m3':role='kv_store'
        elif cache[0][-1]==320 and cache[1]=='UINT8':role='compressed_store'
        else:raise ValueError('cache_epilog_packed_region_not_declared')
        return role,{'observed_input_row_capacity':rows,'observed_slot_mapping_values':None,
            'observed_valid_write_rows':None,'observed_cache_capacity':cache[0],
            'observed_packed_row_bytes':cache[0][-1],
            'cache_capacity_is_active_context':False},SOURCE
    raise ValueError('native_family_not_supported')


def select(group, local, execution):
    role,details,source=classify(group,execution)
    matches=[node for node in local if node['op_id'].split('.',2)[-1]==role]
    if len(matches)!=1:
        reason='combined_q_kv_program_cannot_be_split_or_reused' if role in {'q_rotary','kv_rotary'} else 'declared_semantic_program_missing'
        raise ValueError(reason+':'+role)
    node=matches[0];op=node['operator'];meta=op.get('metadata',{});source_selected=False
    if role=='grouped_output_a':
        view=meta.get('native_tensor_view',{});seen=details['native_view']
        if any(view.get(key)!=seen[field] for key,field in (('rows','rows'),('batch','heads'),('n','n'),('k','k'))):
            raise ValueError('declared_grouped_output_view_differs')
        if (meta.get('input_format'),meta.get('weight_dtype'),meta.get('output_format')) != ('fp8_e4m3','fp8_e4m3','bf16'):
            raise ValueError('declared_grouped_output_precision_differs')
    elif role.endswith('store'):
        fmt=meta.get('cache_representation',{})
        if fmt.get('row_bytes')!=details['observed_packed_row_bytes']:
            raise ValueError('declared_packed_cache_row_bytes_differ')
        details['declared_write_rows']=op['local_shape'][0]
    else:
        shape=op['local_shape'];details['declared_active_shape']=shape
        if role not in {'compress_rotary','index_rotary'} and prod(shape)!=details['observed_tensor_rows']*details['observed_heads']*details['observed_width']:
            raise ValueError('declared_rotary_active_shape_differs')
        if role in {'compress_rotary','index_rotary'}:
            details['declared_valid_compressed_rows']=shape[0]
        if role in {'q_rotary','kv_rotary','output_inverse_rotary'}:
            view=meta.get('native_tensor_view',{})
            implementation=meta.get('native_implementation',{})
            if implementation.get('selection')=='v41_partial_rotary':
                ins,outs=freeze(group['native_abi'])[2:]
                width=details['observed_rotary_width'];head_width=details['observed_width']
                inverse=role=='output_inverse_rotary'
                if (view.get('kind')!='inplace_partial_rotary'
                        or view.get('native_kind')!='InplacePartialRotaryMul'
                        or freeze(view.get('shape'))!=ins[0][0]
                        or freeze(view.get('coefficient_shape'))!=ins[1][0]
                        or (view.get('dtype'),view.get('coefficient_dtype'),view.get('layout'))
                            !=(ins[0][1],ins[1][1],ins[0][2])
                        or freeze(view.get('partial_slice'))!=(head_width-width,head_width)
                        or view.get('inverse') is not inverse
                        or view.get('sine_sign')!=('caller_negated' if inverse else 'caller_forward')
                        or view.get('rotary_mode')!='interleave' or outs[0]!=ins[0]):
                    raise ValueError('declared_partial_rotary_native_view_differs')
                source_selected=True
                details['declared_native_tensor_view']=view
                details['declared_partial_rotary_work']=meta['partial_rotary_work']
                source=meta['native_source']
    details.update(boundary_relation='source_role_conditional_existing_semantic_program',
        native_source_program_selected=source_selected,
        limitations=['Native scalar values, slot masks and binary/source identity are not retained.',
            'This prices existing declared work; it is not additional Body budget or strict accuracy.',
            'Compressed output allocation is not proof of a valid compressed write.'])
    return role,[node],source,details


def prepare_references(partitions,manifest):
    """Validate every aligned layer, then pool only identical physical programs."""
    replica=min(manifest['execution']['replicas']);layers=defaultdict(list)
    for node in manifest['nodes']:
        if node['replica']==replica:layers[node.get('layer')].append(node)
    references={};failures=[];selected={}
    for index,group in enumerate(partitions['partitions']):
        try:
            first=None;signature=None
            for lid in sorted(map(int,group['layer_counts'])):
                current=select(group,layers[lid],manifest['execution'])
                role,targets,source,relation=current
                physical=canonical([(reference_signature(t),t['physical_work']) for t in targets])
                if signature is not None and signature!=physical:
                    raise ValueError('heterogeneous_programs_cannot_split_retained_histogram')
                if first is None:first,signature=current,physical
            role,targets,source,relation=first
        except ValueError as error:
            failures.append({'partition_index':index,'native_operator_type':group['native_operator_type'],
                'event_count':group['observed_us']['count'],'observed_us':group['observed_us'],
                'duration_ns_counter':group['duration_ns_counter'],'native_abi':group['native_abi'],
                'layer_ids':sorted(map(int,group['layer_counts'])),'topology_region':group['topology_region'],
                'reason':str(error),'status':'unresolved'})
            continue
        selected.update((t['node_id'],t) for t in targets)
        # Native allocations stay in ABI buckets. Pooling is allowed only after
        # each saved layer has independently selected identical physical work.
        key=canonical((group['native_abi'],role,signature,relation))
        row=references.setdefault(key,{'native_operator_type':group['native_operator_type'],
            'declared_role':role,'native_abi':group['native_abi'],'layer_ids':set(),
            'representative_replica':replica,'representative_target_ids':[t['node_id'] for t in targets],
            'physical_program_signatures':[t['physical_signature'] for t in targets],
            'physical_work_per_program':[t['physical_work'] for t in targets],
            'program_set_key':sha256(signature.encode()).hexdigest(),
            'source_anchor_declaration':source,'source_correspondence':relation,
            'histogram':Counter(),'partition_indices':[], 'reference_only':True,
            'occurrence_binding_implied':False,'strict_accuracy_implied':False,'additional_budget_allowed':False})
        row['layer_ids'].update(map(int,group['layer_counts']));row['histogram'].update(dict(group['duration_ns_counter']))
        row['partition_indices'].append(index)
    results=[]
    for key,row in references.items():
        hist=row.pop('histogram');row.update(group_id='sha256:'+sha256(key.encode()).hexdigest(),
            layer_ids=sorted(row['layer_ids']),duration_ns_counter=sorted(hist.items()),
            observed_us=duration_stats(hist,1000),observed_activity_sum_ns=sum(ns*n for ns,n in hist.items()),
            original_partition_histogram_unchanged=True)
        results.append(row)
    return results,failures,{'execution':manifest['execution'],'graph_id':manifest['graph_id'],'nodes':list(selected.values())}
