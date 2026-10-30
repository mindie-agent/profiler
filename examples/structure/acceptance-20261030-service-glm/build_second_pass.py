"""Add measured down-projection, MLA and index-score service to a separate arm.

[Role] Extend the completed first arm with three independently retained native calls.
[Invariants] First-arm inputs/coefficients remain unchanged; no Body residual fit.
  Exact source geometry and inclusive one-call boundaries constrain each response.
[Timeouts & Locks] Bounded saved populations and one graph; no locks or capture reads.
[Side-Effect Policy] Writes second-pass/ only; no Sim source changes or predictions.
"""
from copy import deepcopy
from pathlib import Path

from build_service_cases import HERE, read, pin, write, summarize

SECOND=HERE/'second-pass'
ORDER=['a5_glm53flash_tp8_c16_p4k','a5_glm53flash_tp8_c16_p8k',
       'a5_glm53flash_tp8_c8_p4k','a5_glm53flash_tp8_c4_p8k',
       'glm53flash-a5-tp8-c3','glm53flash-a5-tp8-c1']


def main():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    manifest_path=HERE/'decode-forward-service-cases.json'
    manifest=read(manifest_path)
    entries={r['case_id']:r for r in manifest['cases']}
    populations={r['case_id']:r for r in read(HERE/'observed-populations.json')['cases']}
    result=[];evidence=[]
    for cid in ORDER:
        row=deepcopy(entries[cid]);first_path=Path(row['sim_case_path']);case=read(first_path)
        pop=populations[cid];actual_pin=pop['groups'][0]['actual_identity'];actual=read(actual_pin['path'])
        assert pin(actual_pin['path'])==actual_pin
        g=pop['geometry'];M=g['query_rows'];B=g['sequences_per_replica'];q=g['tokens_per_sequence']
        parsed=parse_case(case)
        ops=target_graphs(parsed,phase='decode',tokens=q,context=g['context_tokens'],sequences=B,scope='body')[0]
        choices=[('GroupedMatmul','balanced_grouped_down',42,'expert_down'),
                 ('SparseFlashMla','latent_attention_batch',11,None),
                 ('_glm5_next_lightning_indexer_score_kernel','index_scores',11,None)]
        additions=[];new_rules=[]
        for native,recipe,count,role in choices:
            targets=([o for o in ops if o.family=='attention' and
                      dict(o.metadata).get('program_kind')=='indexed_attention']
                     if native=='SparseFlashMla' else [o for o in ops if o.recipe==recipe])
            assert len(targets)==count, (cid,native,len(targets))
            assert len({o.recipe for o in targets})==1
            recipe=targets[0].recipe
            fs=[f for f in actual['families'] if f['native_operator_type']==native and (role is None or f['declared_role']==role)]
            stats=summarize(fs);assert stats['count']==count*actual['forward_count']
            representative=targets[0]
            assert all((o.local_shape,o.dtype,o.hbm_bytes)==(representative.local_shape,representative.dtype,representative.hbm_bytes) for o in targets)
            match={'hardware':parsed.machine.sku,'recipe':recipe,'dtype':representative.dtype}
            match.update({f'local_shape.{i}':v for i,v in enumerate(representative.local_shape)})
            coordinates={'hbm_bytes':{'path':'work.hbm'}}
            # The unexpanded index-score program contains all sequence/context
            # dependent traffic. This prevents a q-matched rule extending to a
            # different context length whose displayed local shape is identical.
            domain={'hbm_bytes':{'min':representative.hbm_bytes,'max':representative.hbm_bytes}}
            if native=='GroupedMatmul':
                match.update({'metadata.matrix_groups':dict(representative.metadata)['matrix_groups'],
                              'metadata.matrix_weight_bank_groups':288,'metadata.input_format':'fp8_e4m3',
                              'metadata.weight_format':'fp8_e4m3','metadata.output_format':'bf16'})
                # The source grouped recipe prepares additional physical traffic;
                # constrain its full integer bank work rather than analytic HBM.
                coordinates={'routed_rows':{'path':'local_shape.0'},'banks':{'path':'metadata.matrix_group_rows','reduce':'len'}}
                domain={'routed_rows':{'min':M*8,'max':M*8},'banks':{'min':288,'max':288}}
            elif native=='SparseFlashMla':
                match.update({'metadata.indexed_attention_geometry.topk':2048,
                              'metadata.indexed_attention_geometry.query_dtype':'bf16',
                              'metadata.indexed_attention_geometry.cache_dtype':'bf16'})
                if B==1:
                    coordinates={'query':{'path':'metadata.indexed_attention_geometry.query'},
                                 'context':{'path':'metadata.indexed_attention_geometry.context'}}
                    domain={'query':{'min':q,'max':q},'context':{'min':g['context_tokens'],'max':g['context_tokens']}}
                else:
                    coordinates={'batch':{'path':'metadata.attention_tensor_view.batch_count'}}
                    domain={'batch':{'min':B,'max':B}}
            rid=native.lower().replace('_','-')+'-observed-second'
            caution=('Source declared valid integer expert rows; native storage capacity does not establish group-list values.' if native=='GroupedMatmul' else
                     'Whole-batch indexed attention boundary; active KV, sparse-index values and captured native implementation are not established.' if native=='SparseFlashMla' else
                     'Source-symbol score kernel matches standalone index_scores; index_topk and projections remain separate; complete native ABI unavailable.')
            rule={'id':rid,'match':match,'coordinates':coordinates,'domain':domain,
                  'response':{'fixed_us':stats['mean_us']},
                  'provenance':{'basis':'retained_complete_native_population_mean',
                     'calibration_origin':'observed','evaluation_role':'in_sample','native_operator_type':native,
                     'actual_identity':actual_pin,'source_sha256':actual['source_identity']['sha256'],
                     'count':stats['count'],'body_count':actual['forward_count'],
                     'mean_us':stats['mean_us'],'p50_us':stats['p50_us'],'physical_domain':g,
                     'body_residual_used':False,'response_boundary':'inclusive_native_call_once',
                     'contract_and_source_uncertainties_retained':True,'boundary_caution':caution}}
            new_rules.append(rule)
            additions.append({'native_operator_type':native,'declared_role':role,'recipe':recipe,'rule_id':rid,
                'actual_identity':actual_pin,'source_identity':actual['source_identity'],
                'observed':stats,'calls_per_forward':count,'declared_occurrences':count,
                'family_indices':[i for i,f in enumerate(actual['families']) if f in fs],
                'representative_physical_operator':{k:v for k,v in representative.to_dict().items() if k not in ('op_id','layer','requests','deps')},
                'boundary_caution':caution})
        rules=case['runtime']['kernels']['service_regimes']; assert len(rules)==6
        rules.extend(new_rules)
        calibration=deepcopy(row['calibration_evidence']);calibration.update(regime_count=9,
           first_arm_case_identity=pin(first_path),new_native_service_families=[x[0] for x in choices])
        case['runtime']['metadata']['calibration_evidence']=calibration
        path=SECOND/'cases'/f'{cid}-service-regimes-extended.json';write(path,case)
        row.update(sim_case_path=str(path),calibration_evidence={**calibration,'evaluation_relation':'in_sample'},
                   variant_id='observed-service-extended-2f48346b')
        row['model_declaration']=pin(path);row['replay_input_pins']['case']=pin(path)
        row['prior_source_case_identity']=pin(first_path)
        result.append(row)
        evidence.append({'case_id':cid,'case_identity':pin(path),'first_arm_case_identity':pin(first_path),
                         'geometry':g,'source_identity':row['source'],'forward_count':actual['forward_count'],
                         'groups':additions})
        print(cid,'three additions',[(r['native_operator_type'],r['observed']['mean_us']) for r in additions],flush=True)
    write(SECOND/'observed-populations.json',{'schema_version':'mindie-native-service-populations/1',
          'cases':evidence,'first_arm_population_identity':pin(HERE/'observed-populations.json'),
          'generator_identity':pin(__file__),'raw_scans':0,'new_costs':0})
    manifest.update(cases=result,variant_id='observed-service-extended-2f48346b',
                    first_arm_manifest_identity=pin(manifest_path))
    write(SECOND/'decode-forward-service-cases.json',manifest)


if __name__=='__main__':
    main()
