"""Conditional source paged-MLA reference from a complete retained native ABI.

[Role] Match Kimi FIA tensor views and whole-layer scope to Sim's native program.
[Invariants] NBS output differs from BNS query; table capacity never supplies KV
  lengths. A declared CPU dispatch can price service but cannot prove strict work.
[Timeouts & Locks] Bounded in-memory metadata validation; no locks or subprocesses.
[Side-Effect Policy] Return a reference plan; no raw reads or declaration mutations.
"""
from glm_native_references import _slot, freeze


def paged_mla_reference(native, local, groups, execution, partition):
    ins, outs = native[2:]
    if native[:2] != ('native_tensor_abi', 'FusedInferAttentionScore') or (len(ins), len(outs)) != (31, 2):
        raise ValueError('kimi_paged_mla_requires_complete_31_2_abi')
    if len(ins[0][0]) != 4 or len(ins[1][0]) != 4:
        raise ValueError('kimi_paged_mla_query_cache_rank')
    batch, heads, query, latent = ins[0][0]
    pool, kv_heads, page, cache_latent = ins[1][0]
    if (query != 1 or latent != 512 or cache_latent != latent or kv_heads != 1
            or batch != execution['sequences'] or execution['tokens'] != 1
            or page < 1 or 128 % page or pool < 1
            or not _slot(ins[0], (batch, heads, 1, latent), 'bf16')
            or not _slot(ins[1], (pool, 1, page, latent), 'bf16') or ins[2] != ins[1]
            or not _slot(ins[6], (batch,), 'int64')
            or len(ins[14][0]) != 2 or ins[14][0][0] != batch or ins[14][1:] != ('int32', 'ND')
            or not _slot(ins[24], (batch, heads, 1, 64), 'bf16')
            or not _slot(ins[25], (pool, 1, page, 64), 'bf16')
            or not _slot(outs[0], (heads, batch, 1, latent), 'bf16')
            or not _slot(outs[1], (), 'fp32')
            or any(ins[i] != ((), None, None) for i in range(31) if i not in {0, 1, 2, 6, 14, 24, 25})):
        raise ValueError('kimi_paged_mla_active_bns_query_nbs_output_abi')
    active = ('attention_paged_mla_qk_rope', 'FusedInferAttentionScore',
        (ins[0], ins[24]), (((1, page, latent), 'bf16', 'ND'),
        ((1, page, latent), 'bf16', 'ND'), ((1, page, 64), 'bf16', 'ND')), outs[0], batch)
    if freeze(partition['contract']) != active:
        raise ValueError('kimi_paged_mla_retained_active_contract_differs')
    targets = [n for n in local if freeze(n.get('contract')) == active
        and n['operator']['metadata'].get('implementation_binding', {}).get('implementation')
        == 'ascend_paged_mla_decode_arch35']
    if len(targets) != 1:
        raise ValueError('kimi_paged_mla_source_kernel_missing_or_ambiguous')
    target = targets[0]; geometry = target['operator']['metadata']['paged_mla_geometry']
    dispatch = geometry.get('dispatch', {})
    if (target['boundary'] != 'kernel' or target['physical_work_basis'] != 'prepared_source_plan'
            or geometry['contexts'] != [execution['context']] * batch
            or dispatch.get('contexts') != geometry['contexts'] or dispatch.get('heads') != heads
            or not dispatch.get('aic_owner_segments') or 'aiv_merge_segments' not in dispatch):
        raise ValueError('kimi_paged_mla_source_dispatch_geometry_differs')
    return 'mla_attention_core', targets, dispatch['source'], {
        'boundary_relation': 'complete_native_FIA_conditional_source_paged_MLA_program',
        'observed_query_layout': 'BNSD', 'observed_output_layout': 'NBSD',
        'observed_batch': batch, 'observed_physical_heads': heads,
        'observed_page_size': page, 'observed_block_table_capacity': ins[14][0][1],
        'observed_cache_pool_capacity': pool, 'observed_context_values': None,
        'observed_block_table_values': None, 'declared_contexts': geometry['contexts'],
        'declared_dispatch': dispatch, 'strict_physical_work_proven': False,
        'limitations': [
            'The captured length-array descriptor does not contain per-call KV length values.',
            'The block table and cache pool describe capacity, not active context lengths.',
            'Initial prompt contexts and SplitCore/FD owner ranges are source-declared conditions; KV growth is unobserved.',
            'Captured binary and host dispatch identity remain unverified.',
            'Full source program service is a conditional reference outside strict accuracy; it is not an additional Body budget.']}
