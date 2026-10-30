"""Extract GLM78 native V2 caller constraints from retained complete ABI.

[Role] Independent typed producer/consumer and TP materialization checks.
[Invariants] ABI compatibility is not pointer identity. Buffer capacity does
  not establish valid expert rows; distinct FP32 scale roles remain distinct.
[Timeouts & Locks] In-memory retained metadata only; no Sim, raw scan or costs.
[Side-Effect Policy] Return constraints for a fresh graph reviewer; no writes.
"""
from math import ceil


def require(condition, message):
    if not condition:
        raise ValueError(message)


def one(parts, kind):
    values = [p for p in parts if p['native_operator_type'] == kind]
    require(len(values) == 1, f'expected_one_complete_{kind}_ABI_domain')
    return values[0]


def tensors(part):
    abi = part['native_abi']
    require(abi[:2] == ['native_tensor_abi', part['native_operator_type']], 'native_ABI_kind_differs')
    return abi[2], abi[3]


def check_retained_v2(retained, *, tp, ep, hidden, experts):
    """Return exact contracts and source-caller obligations, without pricing.

    The slot names follow the retained CANN V2 interface: dynamic_scales is
    dispatch output 1; expand_scales is output 6 and Combine input 10. Both
    are FP32 row tensors, but they have different mathematical roles.
    """
    parts = retained['partitions']; forwards = retained['forward_count']
    dispatch = one(parts, 'MoeDistributeDispatchV2')
    combine = one(parts, 'MoeDistributeCombineV2')
    up = one(parts, 'GroupedMatmulSwigluQuantV2')
    down = one(parts, 'GroupedMatmul')
    gather = one(parts, 'hcom_allGather_')
    selected = {'dispatch': dispatch, 'combine': combine, 'expert_up': up,
                'expert_down': down, 'tp_finalize_allgather': gather}
    layers = dispatch['layer_counts']
    for name, part in selected.items():
        require(part['layer_counts'] == layers, f'{name}_layer_population_differs')
        require(all(n == forwards for n in part['layer_counts'].values()), f'{name}_not_once_per_layer_forward')
        require(part['observed_us']['count'] == sum(layers.values()), f'{name}_full_population_differs')
        require(sum(n for _, n in part['duration_ns_counter']) == part['observed_us']['count'], f'{name}_histogram_incomplete')
    di, do = tensors(dispatch); ci, co = tensors(combine)
    ui, uo = tensors(up); wi, wo = tensors(down)
    require((len(di), len(do), len(ci), len(co)) == (7, 7, 18, 1), 'native_V2_slot_schema_differs')
    require(len(ui) == 6 and len(uo) == 2 and len(wi) == 9 and len(wo) == 1, 'W4A8_GMM_slot_schema_differs')
    M = retained['geometry']['query_rows']; padded = ceil(M/tp)*tp; local = padded//tp
    capacity = do[0][0][0]; topk = di[1][0][1]
    require(di[0] == [[local, hidden], 'bf16', 'ND'], 'dispatch_local_hidden_input_differs')
    require(di[1] == [[local, topk], 'int32', 'ND'] and di[3] == [[local], 'bool', 'ND'], 'dispatch_router_or_active_mask_differs')
    require(do[0] == [[capacity, hidden], 'int8', 'ND'], 'dispatch_quantized_payload_differs')
    require(do[1] == [[capacity], 'fp32', 'ND'], 'dispatch_dynamic_row_scale_differs')
    require(do[6] == [[capacity], 'fp32', 'ND'], 'dispatch_combine_weight_scale_differs')
    require(do[2] == [[capacity*128], 'int32', 'ND'], 'dispatch_assist_capacity_differs')
    require(experts % ep == 0 and do[3] == [[experts//ep], 'int64', 'ND'], 'declared_expert_bank_count_differs')
    require(co[0] == [[local, hidden], 'bf16', 'ND'], 'combine_local_output_differs')
    links = []

    def link(producer, slot_out, out, consumer, slot_in, inp, role):
        require(out == inp, f'{role}_producer_consumer_contract_mismatch')
        links.append({'producer': producer, 'output_slot': slot_out, 'consumer': consumer,
                      'input_slot': slot_in, 'role': role, 'tensor_contract': out,
                      'basis': 'complete_native_tensor_contract_compatibility_and_V2_interface_role',
                      'observed_pointer_identity': False})

    link('dispatch', 0, do[0], 'expert_up', 0, ui[0], 'quantized_expert_payload')
    link('dispatch', 1, do[1], 'expert_up', 1, ui[1], 'dynamic_activation_scale')
    link('dispatch', 3, do[3], 'expert_up', 2, ui[2], 'expert_token_counts')
    link('dispatch', 3, do[3], 'expert_down', 7, wi[7], 'expert_token_counts')
    link('expert_up', 0, uo[0], 'expert_down', 0, wi[0], 'fused_swiglu_quantized_payload')
    link('expert_up', 1, uo[1], 'expert_down', 8, wi[8], 'fused_swiglu_dynamic_scale')
    link('expert_down', 0, wo[0], 'combine', 0, ci[0], 'bf16_expert_output')
    for outslot, inslot, role in [(2, 2, 'assist_info_for_combine'), (4, 3, 'ep_receive_send_counts'),
                                 (5, 5, 'tp_receive_send_counts'), (6, 10, 'expand_combine_scales')]:
        link('dispatch', outslot, do[outslot], 'combine', inslot, ci[inslot], role)
    require(di[1] == ci[1] and di[3] == ci[6], 'combine_router_or_active_mask_differs')
    require(ci[4] == [[local, topk], 'fp32', 'ND'], 'combine_router_weight_differs')
    concat = []
    if padded > M:
        for dtype, width, role in [('bf16', hidden, 'hidden'), ('fp32', experts, 'router_logits')]:
            expected = ['native_tensor_abi', 'ConcatD', [[[M, width], dtype, 'ND'],
                        [[padded-M, width], dtype, 'ND']], [[[padded, width], dtype, 'ND']]]
            found = [p for p in parts if p['native_operator_type'] == 'ConcatD' and p['native_abi'] == expected]
            require(len(found) == 1 and found[0]['layer_counts'] == layers, f'{role}_right_pad_Concat_not_complete')
            concat.append({'role': role, 'native_abi': expected, 'calls_per_forward': len(layers)})
    return {'case_id': retained['case_id'], 'source_identity': retained['source_identity'],
        'body_acceptance_identity': retained['body_acceptance_identity'], 'geometry': retained['geometry'],
        'forward_count': forwards, 'layer_ids': sorted(map(int, layers)), 'calls_per_native_per_forward': len(layers),
        'source_caller_geometry': {'global_query_rows': M, 'tp': tp, 'ep': ep, 'experts': experts, 'right_padded_rows': padded,
            'tp_local_rows': local, 'hidden': hidden, 'topk': topk, 'expert_buffer_capacity_rows': capacity,
            'expert_valid_rows': None, 'buffer_capacity_is_not_valid_rows': True},
        'native_contracts': {k: v['native_abi'] for k, v in selected.items() if k != 'tp_finalize_allgather'},
        'typed_links': links, 'materialized_right_pad': concat,
        'tp_finalization': {'observed_native_calls_per_forward': len(layers),
            'source_payload_bytes_per_rank': local*hidden*2, 'gathered_shape': [padded, hidden],
            'unpad_output_shape': [M, hidden], 'payload_basis': 'source_caller_BF16_contract; not_observed_HCOM_descriptor'},
        'fresh_graph_obligations': [
            'One complete native DispatchV2 and CombineV2 boundary per declared MoE layer.',
            'Dispatch INT8 plus FP32 dynamic scale feeds GMM directly; no second routed activation quantizer.',
            'Keep expand_scales distinct from dynamic_scales despite equal dtype and shape.',
            'Native route replaces route_pack/route_unpack; preserve topk, active-mask, group-count and weighted-combine dependencies.',
            'Preserve shared FFN DynamicQuant/DSQ; do not remove every same-named quantizer globally.',
            'Keep source right-pad and TP local slicing, then AllGather and final unpad.',
            'Every original external dependency must reach a surviving consumer; no dangling IDs or disconnected completion join.'],
        'unproven': ['ABI cannot observe tensor values, per-expert valid counts or pointer-level producer identity.',
                    'Public V2 interface/source compatibility does not establish the captured binary revision.']}
