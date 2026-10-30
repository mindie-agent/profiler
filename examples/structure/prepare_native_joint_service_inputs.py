"""Prepare measured native joint-response inputs independently of a pricing API.

[Role] Preserve full native populations and physical source domains for import.
[Invariants] A mean is inclusive native elapsed, not an additive resource price.
  ABI examples never establish a full-population ABI; capacity is not valid M.
[Timeouts & Locks] Retained JSON only, one source at a time; no locks or waits.
[Side-Effect Policy] Writes neutral inputs; no raw scan, cost or Sim mutation.
"""
from collections import Counter
from hashlib import sha256
from pathlib import Path
import json

from collect_scalar_dma_pmu import identity,read
from summarize_grouped_micro_services import histogram_stats

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/observations/sources/arch22-physical-services'
DEST=DATA/'native-joint-service-inputs.json'
SFA=DATA/'sparse-attention'
LIVE=ROOT/'examples/structure/acceptance-20261030-livepre-native'


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))


def pooled_population(rows):
    """Pool only equal physical/evidence domains; call weights come from histograms."""
    domain=rows[0]['applicability_domain']
    if any(row['applicability_domain']!=domain for row in rows):
        raise ValueError('cannot_pool_different_native_domains')
    hist=Counter()
    for row in rows:hist.update(dict(row['duration_ns_counter']))
    return {'candidate_id':'sha256:'+sha256(canonical(domain).encode()).hexdigest(),
            'applicability_domain':domain,'duration_ns_counter':sorted(hist.items()),
            'observed_native_elapsed_us':histogram_stats(sorted(hist.items())),
            'source_populations':rows,
            'calibration_origin':'observed','evaluation_relation':'in_sample',
            'recommended_neutral_parameter':'whole_native_inclusive_mean_us',
            'parameter_unit':'us/native_call',
            'parameter_value_us':histogram_stats(sorted(hist.items()))['mean_us'],
            'alternative_descriptive_p50_us':histogram_stats(sorted(hist.items()))['p50_us'],
            'body_residual_used':False,'native_response_multiplicity':'one response per whole native call',
            'api_binding':None,
            'integration_constraint':'Preserve source dependencies and occupancy; do not add this native elapsed once per internal phase or on top of an inclusive analytic total.'}


def pmu_projection(pmu):
    return {'event_count':pmu['event_count'],
            'fields':{k:{field:v for field,v in f.items() if field!='numeric_value_counter'}
                      for k,f in pmu['fields'].items() if k.endswith('_time(us)')},
            'interpretation':'Every field retains its own numeric/missing population. Do not subtract a numeric-subset mean from the full timing mean; pipes overlap.'}


def sfa_population(path):
    saved=read(path);retained=read(saved['retained_native_identity']['path'])
    if identity(saved['retained_native_identity']['path'])!=saved['retained_native_identity']:
        raise ValueError('SFA_retained_native_identity_changed')
    block=saved['raw_pmu']['dimensions']['Block Num'];mix=saved['raw_pmu']['dimensions']['Mix Block Num']
    if len(saved['native_abi_groups'])!=1 or len(block)!=1 or len(mix)!=1:
        raise ValueError('SFA_domain_requires_partitioning')
    abi=saved['native_abi_groups'][0]['native_abi'];n=saved['event_count']
    if block[0][1]!=n or mix[0][1]!=n:raise ValueError('SFA_launch_population_changed')
    case_path=retained['case_identity']['path'];case=read(case_path)
    domain={'hardware':case['machine']['sku'],'native_operator_type':saved['native_operator_type'],
            'observed_block_num':int(block[0][0]),'observed_mix_block_num':int(mix[0][0]),
            'native_abi':abi,'evidence_scope':'complete_native_ABI_and_duration_population',
            'source_program_domain':'sparse_MLA_INT8_cache_packed_D656_query_D576_output_D512',
            'execution_query_rows':saved['geometry']['query_rows'],
            'execution_batch':saved['geometry']['sequences_per_replica'],
            'query_tokens_per_sequence':saved['geometry']['tokens_per_sequence'],
            'context_condition':{'declared_context_tokens':saved['geometry']['context_tokens'],
                                 'active_lengths_values_observed':False}}
    return {'case_id':saved['case_id'],'source_identity':saved['source_identity'],
            'timing_identity':identity(path),'timing_member':'duration_ns_counter',
            'body_acceptance_identity':saved['body_acceptance_identity'],
            'declared_case_identity':identity(case_path),'applicability_domain':domain,
            'forward_count':saved['forward_count'],'calls_per_forward':saved['calls_per_forward'],
            'duration_ns_counter':saved['duration_ns_counter'],'observed_native_elapsed_us':histogram_stats(saved['duration_ns_counter']),
            'pmu':pmu_projection(saved['raw_pmu']),
            'remaining_conditions':['Native scalar attributes/actual index and sequence-length values are not exported.',
                                    'Complete descriptor ABI does not identify captured source binary or individual phase costs.']}


def livepre_populations(concurrency):
    cid=f'glm53flash-a3-tp16-c{concurrency}-livepre'
    partition_path=ROOT/f'examples/structure/acceptance-20261030-glm-source-accepted-26/additional-native-partitions/{cid}-native-partitions.json'
    original=read(partition_path);actual_path=Path(original['actual_identity']['path'])
    if not actual_path.is_absolute():actual_path=ROOT/actual_path
    if identity(actual_path)['sha256']!=original['actual_identity']['sha256']:
        raise ValueError('livepre_actual_identity_changed')
    actual=read(actual_path);case_path=LIVE/f'cases/{cid}-native.json';case=read(case_path)
    roles={'GroupedMatmul':'expert_down','GroupedMatmulSwigluQuant':'grouped_gate_up_activation_quant',
           'KvQuantSparseFlashAttentionVllm':'indexed_attention_batch','HcPre':'hc_pre','HcPost':'hc_post'}
    rows=[]
    for native in roles:
        members=[(i,f) for i,f in enumerate(actual['families']) if f['native_operator_type']==native]
        if not members:raise ValueError('livepre_native_family_not_found')
        hist=Counter()
        for _,family in members:hist.update(dict(family['duration_ns_counter']))
        f={'duration_ns_counter':sorted(hist.items()),
           'examples':[x for _,family in members for x in family['examples']],
           'structure_groups':[x for _,family in members for x in family.get('structure_groups',[])]}
        references=[]
        for example in f['examples']:
            contract=example.get('contract')
            if contract not in [r['contract'] for r in references]:
                references.append({'contract':contract,'event_id':example['event_id'],'locator':example['locator']})
        role=roles[native];lowering=case['runtime']['kernels']['lowerings']['native_fusion']['options']['traffic_profile']
        program=(lowering[role] if native in {'HcPre','HcPost'}
                 else lowering['grouped_gate_up_activation_quant'] if native=='GroupedMatmulSwigluQuant'
                 else 'INT8_grouped_down_BF16_per_token_scale' if native=='GroupedMatmul'
                 else 'INT8_packed_D528_sparse_MLA_query_D512_output_D512')
        domain={'hardware':case['machine']['sku'],'native_operator_type':native,
                'observed_block_num':None,'observed_mix_block_num':None,'native_abi':None,
                'evidence_scope':'complete_duration_population_with_source_role_conditions',
                'source_program_domain':program,'source_role':role,
                'execution_query_rows':actual['geometry']['query_rows'],
                'execution_batch':actual['geometry']['sequences_per_replica'],
                'query_tokens_per_sequence':actual['geometry']['tokens_per_sequence'],
                'source_dtype_condition': 'BF16 residual/hidden and FP32 mixing parameters' if native in {'HcPre','HcPost'}
                    else 'INT8 x INT8 grouped / INT8 activation output' if native=='GroupedMatmulSwigluQuant'
                    else 'INT8 x INT8 grouped / BF16 output' if native=='GroupedMatmul' else 'BF16 query/output, INT8 cache D528',
                'source_logical_axes': {'hidden_width':4096,'residual_streams':4} if native in {'HcPre','HcPost'}
                    else {'local_expert_banks':18,'hidden_width':4096,'expert_intermediate_width':2048}
                    if native!='KvQuantSparseFlashAttentionVllm' else {'query_heads':4,'query_head_dim':512,'output_head_dim':512},
                'routing_values_observed':False,'buffer_capacity_is_valid_rows':False}
        count=sum(n for _,n in f['duration_ns_counter']);expected=90 if native in {'HcPre','HcPost'} else 11 if 'SparseFlash' in native else 42
        if count!=actual['forward_count']*expected:raise ValueError('livepre_native_population_incomplete')
        subs=[];merged=Counter()
        for s in f.get('structure_groups',[]):
            merged.update(dict(s['duration_ns_counter']))
            subs.append({'attention_kind':s['attention_kind'],'block':s['block'],
                         'duration_ns_counter':s['duration_ns_counter'],
                         'observed_native_elapsed_us':histogram_stats(s['duration_ns_counter'])})
        if subs and merged!=Counter(dict(f['duration_ns_counter'])):raise ValueError('livepre_subpopulation_not_conserved')
        rows.append({'case_id':cid,'source_identity':actual['source_identity'],
            'timing_identity':identity(actual_path),'timing_members':[f'families/{index}/duration_ns_counter' for index,_ in members],
            'body_acceptance_identity':actual['body_acceptance_identity'],'declared_case_identity':identity(case_path),
            'source_case_condition':{'native_fusion':case['runtime']['kernels']['lowerings']['native_fusion'],
                                     'tp':case['runtime']['tp'],'ep':case['runtime']['ep']},
            'applicability_domain':domain,'forward_count':actual['forward_count'],'calls_per_forward':expected,
            'duration_ns_counter':f['duration_ns_counter'],'observed_native_elapsed_us':histogram_stats(f['duration_ns_counter']),
            'complete_attention_subpopulations':subs,'complete_native_member_populations':[
                {'family_index':index,'declared_role':family['declared_role'],
                 'observed_native_elapsed_us':histogram_stats(family['duration_ns_counter'])} for index,family in members],
            'representative_contract_examples':references,
            'example_ABI_is_not_full_population_ABI':True,'pmu':None,
            'remaining_conditions':['Complete native timing is usable for this declared caller domain without independently identifying cache/descriptor costs.',
                'Full-population ABI and Block/MixBlock are not preserved in this actual; examples are not promoted.',
                'Expert route counts are unobserved; buffer shape does not establish valid M.',
                'The retained KDA/MLA subdivisions are diagnostics; no timing-based per-layer binding is inferred.']})
    if len(rows)!=5:raise ValueError('livepre_five_native_families_not_found')
    return rows


def main():
    populations=[sfa_population(SFA/f'a3_glm53_w4a8_tp16_tpot{x}-sfa-pmu.json') for x in ('30_c2','50_c2','88_c8')]
    for c in (4,16):populations.extend(livepre_populations(c))
    groups={}
    for row in populations:groups.setdefault(canonical(row['applicability_domain']),[]).append(row)
    candidates=[pooled_population(rows) for rows in groups.values()]
    result={'schema_version':'mindie-observed-native-joint-service-inputs/1','status':'completed',
            'producer_identity':identity(__file__),'candidates':candidates,
            'source_count':len({r['source_identity']['sha256'] for r in populations}),
            'primary_forwards':sum({r['source_identity']['sha256']:r['forward_count'] for r in populations}.values()),
            'native_calls':sum(r['observed_native_elapsed_us']['count'] for r in populations),
            'selection_policy':'Exact native/physical-source/evidence domain; case IDs are provenance, never cost selectors.',
            'pooling_policy':'Only fully equal applicability domains; pooled integer histograms retain every source comparison.',
            'api_schema_assumed':False,'new_raw_scans':0,'new_costs':0,'body_residual_used':False,'parameter_changes':[]}
    DEST.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Native joint-service observed parameter inputs','',
        'These neutral inputs carry measured inclusive native-call responses for a future API. They do not install a floor or replacement and do not invent its interface. Case IDs are provenance only. Each response applies once to the complete source-native boundary, preserving dependencies and occupancy; it must not be repeated for internal phases or added to an already inclusive analytic total.','',
        '| Physical domain / native | Sources | F | Calls | Mean/P50 us | Evidence |',
        '|---|---|---:|---:|---:|---|']
    for c in candidates:
        d=c['applicability_domain'];s=c['observed_native_elapsed_us'];p=c['source_populations']
        lines.append(f"| {d['native_operator_type']} qrows={d['execution_query_rows']} B={d['execution_batch']} | {', '.join(r['case_id'] for r in p)} | {sum(r['forward_count'] for r in p)} | {s['count']} | {s['mean_us']:.6f}/{s['p50_us']:.6f} | {d['evidence_scope']} |")
    lines+=['', 'GLM78 c2 sources have identical full ABI, Block20/Mix40 and declared context domain, so their complete timing histograms are pooled; each original source and its PMU denominator remain separate. The c8 domain is separate. PMU numeric populations are 3432/3430/3809 while timing populations are 3432/3432/3822.', '',
        'Livepre c4/c16 HCPre/HCPost/up/down/SFA provide complete 90/90/42/42/11-call-per-Forward histograms, with source-role and dtype conditions. HC attention/FFN populations share their declared source program and are pooled with each original 45-call population retained. Examples do not prove full-population ABI or Block configuration, so these fields remain absent. This limits strict binding, but does not erase their valid whole-native duration response. No active route count is inferred from capacity. KDA/MLA subgroup histograms remain inspectable.', '',
        'All proposed values are observed, in-sample, in microseconds per native call. No Body residual, pass status, or model/case name determines any value or domain. No raw scan or simulation was run.']
    DEST.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:result[k] for k in ('source_count','primary_forwards','native_calls')}|{'candidate_count':len(candidates)}))


if __name__=='__main__':main()
