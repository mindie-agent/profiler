"""Source-conditioned Kimi native ABI references from existing Sim subgraphs.

[Role] Join retained complete ABI/topology buckets to declared Kimi body programs.
[Invariants] No native names imply a layer. Each observed layer/region is retained;
  capacity is never active work, and heterogeneous layer programs use the captured
  multiplicities without inventing per-layer measured latency distributions.
[Timeouts & Locks] Finite metadata-only selectors; no I/O, subprocesses or locks.
[Side-Effect Policy] Return conditional reference plans; never mutate Sim declarations.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from math import prod

from glm_native_references import _slot, _subgraph, freeze
from body_source_role_references import reference_signature
from reprice_body_operator_families import canonical
from kimi_paged_mla_references import paged_mla_reference


def role(target):
    return target['op_id'].split('.', 2)[-1] if target['op_id'].startswith('s') else target['op_id']


def one(local, name):
    selected = [node for node in local if role(node) == name]
    if len(selected) != 1:
        raise ValueError('declared_program_missing_or_ambiguous:' + name)
    return selected[0]


def _attn_res(native, local, groups, execution, partition):
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (6, 3) or len(ins[2][0]) != 1:
        raise ValueError('attn_res_native_six_input_three_output_abi')
    hidden = ins[2][0][0]
    if (len(outs[0][0]) != 1 or outs[0][0][0] % hidden
            or any(not _slot(ins[i], (hidden,), 'bf16') for i in (2, 3, 5))):
        raise ValueError('attn_res_hidden_and_normalization_parameter_abi')
    active = outs[0][0][0]; rows = active // hidden
    if (not all(_slot(outs[i], (active,), 'bf16') for i in (0, 2))
            or len(ins[0][0]) != 1 or len(ins[4][0]) != 1
            or ins[0][1:] != ('bf16', 'ND') or ins[4][1:] != ('bf16', 'ND')
            or min(ins[0][0][0], ins[4][0][0]) < active
            or outs[1] != ins[0] or len(ins[1][0]) != 1
            or ins[1][1:] != ('bf16', 'NCL') or ins[1][0][0] % active):
        raise ValueError('attn_res_flat_storage_and_active_output_abi')
    ordinal = partition['native_type_ordinal_in_region']
    region = partition['topology_region']
    name = ('final.attn_res_fwd' if region == 'ffn' and ordinal == 2 else
            'ffn.attn_res_fwd' if region == 'ffn' and ordinal == 1 else
            'attention.attn_res_fwd' if region == 'before_attention_anchor' and ordinal == 1 else None)
    if name is None: raise ValueError('attn_res_topology_ordinal_not_declared')
    target = one(local, name)
    view = target['operator']['metadata'].get('attn_res_view', {})
    if ((view.get('tokens_local'), view.get('hidden'), view.get('bank_capacity')) !=
            (rows, hidden, ins[1][0][0] // active)):
        raise ValueError('attn_res_source_local_rows_or_bank_capacity_differs')
    return name, [target], target['operator']['metadata'].get('attn_res_source'), {
        'boundary_relation': 'whole_source_AttnResFwd_point_with_topology_declared_flags',
        'observed_output_active_rows': rows, 'observed_bank_capacity': ins[1][0][0] // active,
        'observed_prefix_backing_elements': ins[0][0][0], 'declared_view': view,
        'observed_valid_blocks': None, 'observed_scalar_flags': None,
        'limitations': ['Source flags/valid bank rows are declared, not captured scalar values.',
            'Initial prefix backing extent is retained as storage capacity; output rows bound the conditional active view.',
            'Per-layer calls are known from complete topology; group P50 is not split into per-layer observations.',
            'Captured binary identity and tensor address aliasing are not established.']}


def _convolution(native, local, groups, execution, partition):
    ins, outs = native[2:]
    if (len(ins), len(outs)) != (12, 1): raise ValueError('causal_conv_native_abi')
    x, weight, bias, state = ins[:4]
    if (len(x[0]) != 2 or len(weight[0]) != 2 or len(state[0]) != 3
            or x[0][1] != weight[0][1] or state[0][1:] != (weight[0][0]-1, x[0][1])
            or not _slot(x, x[0], 'bf16') or not _slot(weight, weight[0], 'bf16')
            or not _slot(state, state[0], 'bf16') or outs[0] != x or bias[0]):
        raise ValueError('causal_conv_active_x_weight_history_abi')
    target = one(local, 'short_convolution')
    if prod(target['operator']['local_shape']) != prod(x[0]):
        raise ValueError('causal_conv_declared_active_elements_differ')
    return 'short_convolution', [target], {'basis':'existing_sim_kda_short_convolution'}, {
        'boundary_relation':'declared_short_convolution_program_reference',
        'observed_active_shape':x[0], 'observed_kernel_width':weight[0][0],
        'observed_state_pool_capacity':state[0][0], 'observed_state_index_values':None,
        'limitations':['State pool capacity does not determine active sequences.',
            'Activation/bias flags and caller tensor index values remain unobserved.',
            'The selected declared recipe is recorded; a generic elementwise recipe is not native-source calibration.']}


def _kda(native, local, groups, execution, partition):
    ins, outs = native[2:]
    if (len(ins),len(outs)) != (10,3): raise ValueError('kimi_kda_requires_no_accepted_array_10_input_abi')
    gate,beta,state,prefix,slots,alog,bias=ins[3:]
    if len(gate[0]) != 4: raise ValueError('kda_gate_rank')
    outer,rows,heads,dim=gate[0];batch,q=execution['sequences'],execution['tokens']
    if (outer != 1 or rows != batch*q or dim != 128 or not _slot(gate,(1,rows,heads,dim),'bf16')
            or not _slot(beta,(1,rows,heads),'fp32') or not _slot(prefix,(batch+1,),'int32')
            or not _slot(slots,(batch,),'int32') or not _slot(alog,(heads,),'fp32')
            or not _slot(bias,(heads*dim,),'fp32') or len(state[0])!=1 or state[1:]!=('fp32','ND')
            or outs[1:]!=(state,state) or not _slot(outs[0],(rows*heads*dim,),'bf16')
            or any(len(x[0])!=1 or x[0][0]<rows*heads*dim or x[1:]!=('bf16','ND') for x in ins[:3])):
        raise ValueError('kimi_kda_gate_state_parameter_abi')
    semantic,targets=_subgraph('kda_recurrent',groups,local)
    scans=[t for t in targets if t['family']=='recurrent_scan']
    if scans:
        native_batch = len(scans)==1 and scans[0]['operator']['metadata'].get('kda_recurrent_params')
        if native_batch:
            params=scans[0]['operator']['metadata']['kda_recurrent_params']
            if (tuple(scans[0]['operator']['local_shape'])!=(rows,heads,dim,dim)
                    or params['lengths']!=[q]*batch or params['has_accepted_tokens']
                    or (params['heads'],params['dk'],params['dv'],params['dtype'],params['gate_dtype'],params['beta_dtype'])
                    !=(heads,dim,dim,'bf16','bf16','fp32')):
                raise ValueError('kimi_kda_source_batch_parameters')
        elif len(scans)!=batch or any(tuple(t['operator']['local_shape'])!=(q,heads,dim,dim) for t in scans):
            raise ValueError('kimi_kda_declared_batch_scan_geometry')
    else:
        shapes=[tuple(t['operator']['local_shape']) for t in targets]
        if not any(heads in shape and dim in shape for shape in shapes):
            raise ValueError('kimi_kda_source_program_geometry_unavailable')
    return semantic['role'],targets,semantic.get('source'),{
        'boundary_relation':'complete_kda_semantic_program_set_no_accepted_array_reference',
        'observed_query_rows':rows,'observed_heads':heads,'observed_head_dim':dim,
        'observed_accepted_array_present':False,'observed_state_pool_backing':state[0][0],
        'observed_state_index_values':None,'observed_qkv_strides':None,
        'limitations':['QKV/state backing sizes do not establish active view strides or selected checkpoint state.',
            'The 10-input no-accepted-array branch is distinct from the GLM 11-input accepted-token branch.',
            'All batch sequence programs are included; the reference is not one sequence substituted for a batch.']}


def _prolog(native, local, groups, execution, partition):
    ins,outs=native[2:]
    if (len(ins),len(outs))!=(21,7):raise ValueError('kimi_mla_prolog_native_21_7_abi')
    x,qa,qb,uk,kva,qn,kn=ins[:7]
    if len(x[0])!=2 or len(uk[0])!=3:raise ValueError('kimi_mla_prolog_rank')
    rows,hidden=x[0];heads,nope,latent=uk[0];rope=64;rank=qa[0][1]
    if (not _slot(x,(rows,hidden),'bf16') or not _slot(qa,(hidden,rank),'bf16','FRACTAL_NZ')
            or not _slot(qb,(rank,heads*(nope+rope)),'bf16','FRACTAL_NZ')
            or not _slot(uk,(heads,nope,latent),'bf16') or not _slot(kva,(hidden,latent+rope),'bf16','FRACTAL_NZ')
            or not _slot(qn,(rank,),'bf16') or not _slot(kn,(latent,),'bf16')
            or not _slot(outs[0],(rows,heads,latent),'bf16') or not _slot(outs[1],(rows,heads,rope),'bf16')
            or outs[2:4] != ins[9:11] or ins[9][0][1:]!=(128,1,latent) or ins[10][0][1:]!=(128,1,rope)):
        raise ValueError('kimi_mla_prolog_bf16_padded_heads_abi')
    names=('q_a','kv_a','q_norm','q_b','kv_norm','rotary','kv_store','q_absorb')
    targets=[one(local,name) for name in names]
    by_name={role(t):t for t in targets}
    for name,shape in [('q_a',(rows,rank,hidden)),('kv_a',(rows,latent+rope,hidden)),('q_b',(rows,heads*(nope+rope),rank))]:
        contract=freeze(by_name[name].get('contract'))
        if not contract or contract[:2]!=('matrix',shape) or contract[2:5]!=('bf16','bf16','bf16'):
            raise ValueError('kimi_mla_prolog_declared_projection_differs:'+name)
    return 'mla_prolog',targets,{'basis':'existing_sim_MLA_projection_norm_rope_cache_absorb_nodes'}, {
        'boundary_relation':'unfused_MLA_prolog_semantic_program_set_reference',
        'observed_physical_heads':heads,'observed_query_rows':rows,'observed_q_lora_rank':rank,
        'observed_kv_lora_rank':latent,'observed_rope_dim':rope,'native_fusion_resource_program_selected':False,
        'limitations':['Physical16 prolog heads are not substituted for logical12 output heads.',
            'Declared projection/norm/rope/cache/absorb work is a decomposed reference with internal HBM and launch overhead.',
            'Subsequent explicit query Slice/Pad, attention core, V expansion, output gate and output projection are excluded.',
            'Cache addresses, scalar flags and exact captured binary are not established.']}


SELECTORS={'AttnResFwd':_attn_res,'CausalConv1d':_convolution,'RecurrentKda':_kda,
           'MlaPrologV3':_prolog,'FusedInferAttentionScore':paged_mla_reference}


def program_signature(target):
    if target['operator']['metadata'].get('native_kind') in {'MoeDistributeDispatchV3','MoeDistributeCombineV3'}:
        operator=deepcopy(target['operator'])
        for key in ('op_id','deps','layer','stage','requests','notes'):
            operator.pop(key,None)
        # Keep phase stream separation while removing the enclosing occurrence.
        # The actual graph passed to the cost engine retains its full stream IDs.
        if operator.get('stream','').startswith('s'):
            operator['stream']=operator['stream'].split('.',2)[-1]
        metadata=operator['metadata']
        for key in ('collective_id','reverse_of_collective','graph_segment'):
            metadata.pop(key,None)
        if 'device_kernel_group' in metadata:
            metadata['device_kernel_group'].pop('id',None)
        return {'native_mc2_source_phase':operator}
    if target['family'] != 'attn_res_prefix':
        return reference_signature(target)
    operator=target['operator']
    # family_attnres builds resource phases from the explicit view. Bank tensor
    # identities express graph dependencies, not a different isolated program.
    return {'family':target['family'],'recipe':operator['recipe'],
        'shape':operator['local_shape'],'dtype':operator['dtype'],
        'view':operator['metadata']['attn_res_view'],
        'source':operator['metadata']['attn_res_source']}


def prepare_references(partitions,manifest):
    """Allow heterogeneous source programs only with exact retained layer counts."""
    replica=min(manifest['execution']['replicas']);local=defaultdict(list);subgraphs=defaultdict(list)
    for node in manifest['nodes']:
        if node['replica']==replica:local[node.get('layer')].append(node)
    for group in manifest['subgraphs']:
        if group['replica']==replica:subgraphs[group.get('layer')].append(group)
    references,failures,programs=[],[],{}
    for index,part in enumerate(partitions['partitions']):
        native=freeze(part['native_abi']);kind=part['native_operator_type'];buckets={}
        try:
            for layer,count in sorted((int(k),v) for k,v in part['layer_counts'].items()):
                name,targets,source,correspondence=SELECTORS[kind](native,local[layer],subgraphs[layer],manifest['execution'],part)
                signature=canonical([(program_signature(t),t['physical_work']) for t in targets]);key=sha256(signature.encode()).hexdigest()
                program={'program_set_key':key,'declared_role':name,'representative_replica':replica,
                    'representative_target_ids':[t['node_id'] for t in targets],
                    'physical_program_signatures':[t['physical_signature'] for t in targets],
                    'physical_work_per_program':[t['physical_work'] for t in targets],
                    'source_anchor_declaration':source,'source_correspondence':correspondence,
                    'nodes':targets}
                programs.setdefault(key,program)
                bucket=buckets.setdefault(key,{'program_set_key':key,'layer_ids':[],'event_count':0})
                bucket['layer_ids'].append(layer);bucket['event_count']+=count
            if sum(b['event_count'] for b in buckets.values())!=part['observed_us']['count']:
                raise ValueError('native_layer_multiplicity_does_not_cover_histogram')
        except ValueError as error:
            failures.append({'partition_index':index,'native_operator_type':kind,'event_count':part['observed_us']['count'],
                             'status':'unresolved','reason':str(error)})
            continue
        references.append({'group_id':'sha256:'+sha256(canonical((partitions['source_identity']['sha256'],index,native)).encode()).hexdigest(),
            'partition_index':index,'native_operator_type':kind,'declared_role':name,'native_abi':native,
            'layer_ids':sorted(map(int,part['layer_counts'])),'program_buckets':list(buckets.values()),
            'observed_us':part['observed_us'],'duration_ns_counter':part['duration_ns_counter'],
            'observed_activity_sum_ns':sum(ns*n for ns,n in part['duration_ns_counter']),
            'strict_accuracy_implied':False,'occurrence_binding_implied':False,'additional_budget_allowed':False,
            'layer_histograms_inferred':False,'original_partition_histogram_unchanged':True})
    used={b['program_set_key'] for r in references for b in r['program_buckets']}
    return references,failures,{key:value for key,value in programs.items() if key in used}


def prepare_mc2_references(actual,manifest):
    """Revalidate the retained complete dispatch/combine ABI on every saved layer."""
    replica=min(manifest['execution']['replicas']);by_layer=defaultdict(list)
    for node in manifest['nodes']:
        if node['replica']==replica:by_layer[node.get('layer')].append(node)
    refs,failures,programs=[],[],{}
    for old in actual.get('source_role_references',()):
        kind=old['native_operator_type']
        if kind not in {'MoeDistributeDispatchV3','MoeDistributeCombineV3'}:continue
        native=freeze(old['source_correspondence']['observed_native_tensor_contract'])
        ins,outs=native[2:];dispatch=kind=='MoeDistributeDispatchV3';signature=None;program=None
        try:
            if native[:2]!=('native_tensor_abi',kind) or (len(ins),len(outs))!=((8,7) if dispatch else (19,1)):
                raise ValueError('mc2_complete_native_v3_abi_required')
            x,ids=ins[1:3];y=outs[0];source=x if dispatch else y
            if (len(x[0])!=2 or len(y[0])!=2 or len(ids[0])!=2 or x[0][1]!=y[0][1]
                    or ids[1:]!=('int32','ND') or source[0][0]!=ids[0][0]
                    or x[1:]!=('bf16','ND') or y[1:]!=('bf16','ND')):
                raise ValueError('mc2_unquantized_native_shape_dtype')
            for layer in old['layer_ids']:
                targets=[n for n in by_layer[layer] if n['operator']['metadata'].get('native_kind')==kind]
                if not targets:raise ValueError('mc2_source_phase_program_not_selected')
                params=[n['operator']['metadata'].get('mc2_phase') for n in targets if n['family']=='mc2_protocol']
                if not params or any((p['source_tokens'],p['top_k'],p['width'],p['dtype'])!=
                    (ids[0][0],ids[0][1],source[0][1],'bf16') for p in params):
                    raise ValueError('mc2_source_tokens_topk_width_dtype_differ')
                current=canonical([(program_signature(n),n['physical_work']) for n in targets])
                if signature is not None and signature!=current:
                    raise ValueError('mc2_saved_bucket_fresh_source_phases_heterogeneous')
                if program is None:
                    signature=current;key=sha256(current.encode()).hexdigest()
                    program={'program_set_key':key,'declared_role':old['declared_role'],
                        'representative_replica':replica,'representative_target_ids':[n['node_id'] for n in targets],
                        'physical_program_signatures':[n['physical_signature'] for n in targets],
                        'physical_work_per_program':[n['physical_work'] for n in targets],
                        'source_anchor_declaration':targets[0]['operator']['metadata'].get('source'),
                        'source_correspondence':{'boundary_relation':'complete_native_mc2_source_phase_program_reference',
                            'observed_native_tensor_contract':native,'observed_source_tokens':ids[0][0],
                            'observed_top_k':ids[0][1],'observed_buffer_row_capacity':(y if dispatch else x)[0][0],
                            'observed_valid_routed_rows':None,'observed_active_peer_counts':None,
                            'limitations':['Active routed rows, expert counts and peer readiness are not captured.',
                                'Elapsed MC2 may include peer wait; service reference is not bandwidth calibration.',
                                'Full source protocol phases are selected; captured binary equivalence remains unproven.']},
                        'nodes':targets}
            if program is None:raise ValueError('mc2_saved_layers_missing')
        except ValueError as error:
            failures.append({'native_operator_type':kind,'event_count':old['observed_us']['count'],
                             'status':'unresolved','reason':str(error)})
            continue
        programs[key]=program
        refs.append({'group_id':'sha256:'+sha256(canonical((actual['source_identity']['sha256'],old['group_id'],native)).encode()).hexdigest(),
            'partition_index':old['group_id'],'native_operator_type':kind,'declared_role':old['declared_role'],
            'native_abi':native,'layer_ids':old['layer_ids'],
            'program_buckets':[{'program_set_key':key,'layer_ids':old['layer_ids'],'event_count':old['observed_us']['count']}],
            'observed_us':old['observed_us'],'duration_ns_counter':old['duration_ns_counter'],
            'observed_activity_sum_ns':old['observed_activity_sum_ns'],
            'strict_accuracy_implied':False,'occurrence_binding_implied':False,'additional_budget_allowed':False,
            'layer_histograms_inferred':False,'original_partition_histogram_unchanged':True,
            'retained_observation_group_id':old['group_id']})
    return refs,failures,programs
