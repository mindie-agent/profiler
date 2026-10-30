"""Select the source-described D656 prolog/cache/attention boundary for GLM78.

[Role] Mount the explicit packed INT8/BF16/FP32 layout on retained whole calls.
[Invariants] All 78 layers and observed geometry remain; no empirical SFA or
  prolog response is added. Existing grouped/AR responses remain byte-equivalent.
[Timeouts & Locks] Bounded existing JSON and metadata-only graph expansion.
[Side-Effect Policy] Write independent declarations; no cost, CSV or device work.
"""
from collections import Counter
from copy import deepcopy
import argparse

from build_qwen_a3_service_cases import OUT, identity, physical_ops, read, write


def build(captured_grid=False):
    from mindie_sim.prediction.mla_prolog_packed import LAYOUT, PROFILE
    previous = OUT/'decode-forward-glm78-grouped-service-cases.json'
    manifest = read(previous); rows, receipts = [], []
    for old in manifest['cases']:
        row = deepcopy(old); case = read(old['sim_case_path']); cid = old['case_id']
        native_path = OUT/'glm78-native'/f'{cid}-native-partitions.json'
        native = read(native_path)
        if native['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_source_differs')
        rules = deepcopy(case['runtime']['kernels']['service_regimes'])
        geo = row['replay_input_pins']['primary_geometry']
        if captured_grid:
            case['runtime']['graph_capture_keys'] = [geo['query_rows']]
        kernels = case['runtime']['kernels']; lower = kernels['lowerings']
        lower['mla_prolog'] = {'implementation':'vllm_ascend_mla_prolog_v3',
                              'options':{'cache_layout':LAYOUT,'cache_group_size':128}}
        fusion = lower['native_fusion']['options']
        fusion['roles'] = [*fusion['roles'], 'mla_prolog']
        fusion['traffic_profile'] = {'mla_prolog': PROFILE}
        kernels['programs']['indexed_attention'] = {
            'kind':'indexed_attention_packed_int8','scratch_policy':'offchip','operand_modes':True}
        _, ops = physical_ops(case, geo)
        prologs = [dict(o.metadata) for o in ops if dict(o.metadata).get('fusion_role') == 'mla_prolog']
        attention = [dict(o.metadata) for o in ops if dict(o.metadata).get('program_kind') == 'indexed_attention']
        if len(prologs) != 78 or len(attention) != 78:
            raise ValueError('whole_layer_native_call_population_differs')
        if Counter(m['fusion_tensor_view']['query_norm_output'] for m in prologs) != {False:57,True:21}:
            raise ValueError('query_output_variant_population_differs')
        for m in prologs:
            view = m['fusion_tensor_view']
            if view['packed_cache']['row_bytes'] != 656:
                raise ValueError('packed_prolog_geometry_differs')
            if m['fusion_boundary']['submitted_kernels'] != 1:
                raise ValueError('prolog_not_one_native_call')
        for m in attention:
            shape = m['indexed_attention_geometry']
            if shape['rope'] != 64 or tuple(shape['sequences']) != ((geo['tokens_per_sequence'],geo['context_tokens']),)*geo['sequences_per_replica']:
                raise ValueError('sparse_attention_must_be_full_batch_rope64')
        count = Counter()
        for group in native['partitions']:
            count[group['native_operator_type']] += group['observed_us']['count']
            if group['native_operator_type'] != 'KvQuantSparseFlashAttention': continue
            inputs, outputs = group['native_abi'][2:4]
            if inputs[0][0] != [geo['query_rows'],4,576] or inputs[0][1] != 'bf16':
                raise ValueError('captured_query_ABI_differs')
            if inputs[1][0][-1] != 656 or inputs[1][1] != 'int8' or inputs[2] != inputs[1]:
                raise ValueError('captured_packed_KV_ABI_differs')
            if inputs[6][0] != [geo['sequences_per_replica'],1024] or outputs[0][0] != [geo['query_rows'],4,512]:
                raise ValueError('captured_full_batch_or_output_differs')
        for native_type in ('MlaPrologV3','KvQuantSparseFlashAttention'):
            if count[native_type] != 78*native['forward_count']:
                raise ValueError('captured_native_multiplicity_differs')
        if kernels['service_regimes'] != rules: raise ValueError('existing_observed_responses_changed')
        declared_tokens = sorted({m['fusion_tensor_view']['tokens'] for m in prologs})
        prolog_shape_equal = declared_tokens == [geo['query_rows']]
        conditions = {'packed_layout':'512 INT8 latent + 64 BF16 rotary + four FP32 scales = 656 bytes',
            'cache_offsets':{'latent':0,'rope':512,'scales':640},
            'full_batch_attention_calls_per_forward':78,'full_prolog_calls_per_forward':78,
            'prolog_output_variants':{'ordinary':57,'quant_query_with_scale':21},
            'captured_binary_dispatch_identity':'not_established',
            'active_context_lengths':'unchanged explicit context4096 condition, not inferred from capacity',
            'new_empirical_prolog_or_attention_response':False,
            'captured_prolog_tokens':geo['query_rows'], 'declared_prolog_tokens':declared_tokens,
            'prolog_active_contract_equal':prolog_shape_equal,
            'prolog_geometry_limitation':None if prolog_shape_equal else
                'Retained graph-mode declaration pads M12 to16. This source arm preserves that work discrepancy and does not claim the captured prolog ABI is closed.',
            'source_program':'explicit analytic packed prolog plus source-described packed attention pipeline',
            'native_identity':identity(native_path)}
        if captured_grid:
            conditions.update(capture_grid_basis='Complete retained native prolog/query M, not measured elapsed.',
                graph_capture_keys=[geo['query_rows']],
                separate_ffn_concat_gap='Captured FFN Concat pads M12 to16 before TP/SP on c2; correcting global graph grid does not add that missing explicit caller node.')
        case['runtime']['metadata']['packed_D656_source_condition'] = conditions
        evidence = case['runtime']['metadata']['calibration_evidence']
        evidence['unsupported_native_domains'] = [] if prolog_shape_equal else ['prolog_declared_token_padding_differs_from_capture']
        evidence['packed_source_condition'] = conditions
        stem = 'glm78-captured-grid' if captured_grid else 'glm78-packed-source'
        path = OUT/(stem+'-cases')/f'{cid}-packed-D656-source.json';write(path,case)
        row.update(sim_case_path=str(path),model_declaration=identity(path),
            baseline_grouped_case_identity=identity(old['sim_case_path']),
            variant_id='glm78-packed-D656-captured-grid-672a595f' if captured_grid else
                'glm78-packed-D656-source-a961c114', calibration_evidence=evidence)
        row['replay_input_pins']['case'] = identity(path)
        row.setdefault('scenario_evidence', {})['source_recipe_conditions'] = conditions
        rows.append(row);receipts.append({'case_id':cid,'case_identity':identity(path),
            'conditions':conditions,'preserved_service_rule_count':len(rules),
            'program_recipe_counts':dict(Counter(o.recipe for o in ops)),
            'source_native_calls_per_forward':{k:v/native['forward_count'] for k,v in count.items()},
            'whole_model_layers':78,'observed_forward_count':native['forward_count']})
    write(OUT/('decode-forward-'+stem+'-cases.json'), {
        'schema_version':manifest['schema_version'],'cases':rows,'not_new_live_collection':True,
        'baseline_identity':identity(previous),'variant_id':rows[0]['variant_id']})
    write(OUT/(stem+'-preflight.json'), {'cases':receipts,'raw_reads':0,'new_predictions':0})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captured-grid',action='store_true')
    build(parser.parse_args().captured_grid)
