"""Bind retained AI_CPU native response to explicit layer-ordered metadata calls.

[Role] Reuse the source caller's metadata/build/publication/attention dependency.
[Invariants] Singleton groups are explicit; native Mean applies to build once,
  not publication or attention. No additive Body-delay claim or residual fit.
[Timeouts & Locks] One fresh bounded source graph and retained actual per case.
[Side-Effect Policy] Preparation artifacts only; no capture read or prediction.
"""
from copy import deepcopy

from build_service_cases import HERE, ROOT, pin, read, write, summarize
from build_matrix_slice_pass import make_rule

DEST = HERE / 'metadata-pass'
COMMIT = '13862d5e35fe0dea7ef6e8a9105fb2cbb9b34ba1'


def prepare():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.prediction.sparse_mla_metadata import IMPLEMENTATION, NATIVE, SOURCE

    prior_manifest = HERE / 'norm-quant-post-pass/decode-forward-service-cases.json'
    manifest = read(prior_manifest)
    prior_pop = {p['case_id']:p for p in read(HERE / 'observed-populations.json')['cases']}
    placement = pin(HERE/'metadata-placement-evidence.json')
    rows, evidence = [], []
    for original in manifest['cases']:
        row=deepcopy(original);cid=row['case_id'];previous=pin(row['sim_case_path']);case=read(previous['path'])
        prior_rules=deepcopy(case['runtime']['kernels']['service_regimes'])
        declaration=parse_case(case)
        groups=[[p.index] for p in declaration.model.layer_plans if p.attention=='mla']
        assert len(groups)==11
        case['runtime']['kernels']['lowerings']['sparse_mla_metadata']={
            'implementation':IMPLEMENTATION,'options':{'layer_groups':groups,'schedule':'layer_ordered'}}
        g=prior_pop[cid]['geometry'];parsed=parse_case(case)
        ops=target_graphs(parsed,phase='decode',tokens=g['tokens_per_sequence'],context=g['context_tokens'],
            sequences=g['sequences_per_replica'],scope='body')[0]
        calls=[o for o in ops if o.recipe==IMPLEMENTATION];by_id={o.op_id:o for o in ops}
        assert len(calls)==11
        paths=[]
        for op in calls:
            meta=dict(op.metadata);view=meta['metadata_call']
            assert meta['execution_domain']=='AI_CPU' and meta['invocation_class']=='aicpu'
            assert meta['metadata_schedule']=='layer_ordered' and view['layer_group']==(op.layer,)
            assert op.flops==op.vector_ops==0 and op.source_boundary=='kernel'
            assert view['batch']==g['sequences_per_replica'] and view['rows']==g['query_rows']
            assert len(op.deps)==1
            selection=by_id[op.deps[0]]
            assert selection.layer==op.layer and selection.family=='topk'
            publication=next(p for p in ops if p.recipe=='sparse_mla_metadata_publish' and p.deps==(op.op_id,))
            consumers=[p for p in ops if p.family=='attention' and publication.op_id in p.deps]
            assert len(consumers)==1 and consumers[0].layer==op.layer
            paths.append({'layer_id':op.layer,'index_selection':{'op_id':selection.op_id,'recipe':selection.recipe},
                'metadata_call':{'op_id':op.op_id,'recipe':op.recipe,'local_shape':op.local_shape,'deps':op.deps,'view':view},
                'publication':{'op_id':publication.op_id,'recipe':publication.recipe,'deps':publication.deps},
                'attention':{'op_id':consumers[0].op_id,'recipe':consumers[0].recipe,'deps':consumers[0].deps}})
        ap=prior_pop[cid]['groups'][0]['actual_identity'];actual=read(ap['path'])
        assert pin(ap['path'])==ap
        fs=[f for f in actual['families'] if f['native_operator_type']==NATIVE];stats=summarize(fs)
        assert stats['count']==11*actual['forward_count']
        view=dict(calls[0].metadata)['metadata_call']
        fields=('batch','rows','heads','head_dim','topk','max_query','max_context')
        assert all(all(dict(o.metadata)['metadata_call'][k]==view[k] for k in fields) for o in calls)
        rid='sparse-flash-mla-metadata-layer-ordered-observed'
        match={'hardware':parsed.machine.sku,'recipe':IMPLEMENTATION,'dtype':'int32',
            'metadata.execution_domain':'AI_CPU','metadata.metadata_schedule':'layer_ordered',
            **{f'metadata.metadata_call.{k}':view[k] for k in fields}}
        caution='Complete native family population, no complete captured tensor ABI. Six retained low-source examples establish MLA3/7 in-Body same-stream ordering, not all-rank/all-occurrence dependence. Eleven singleton source groups are explicit conditional caller placement. Native response is applied only to metadata build; publication and SFA retain separate dependencies/work.'
        provenance={'native_operator_type':NATIVE,'actual_identity':ap,'source_identity':actual['source_identity'],
            'body_count':actual['forward_count'],'placement_evidence_identity':placement,
            'native_abi_admission':'unchanged_missing_full_ABI','source_caller':SOURCE,
            'schedule':'layer_ordered','layer_group_count':11,'boundary_caution':caution}
        case['runtime']['kernels']['service_regimes'].append(make_rule(rid,match,stats,provenance))
        calibration={**row['calibration_evidence'],'evaluation_relation':'in_sample','regime_count':len(prior_rules)+1,
            'metadata_schedule':'layer_ordered','metadata_placement_evidence_identity':placement}
        case['runtime']['metadata'].update(calibration_origin='observed',calibration_evidence=calibration)
        path=DEST/'cases'/f'{cid}-metadata-layer-service.json';write(path,case)
        row.update(sim_case_path=str(path),model_declaration=pin(path),calibration_evidence=calibration,
            variant_id='observed-metadata-layer-13862d5e',prior_source_case_identity=previous)
        row['replay_input_pins']['case']=pin(path);rows.append(row)
        evidence.append({'case_id':cid,'case_identity':pin(path),'prior_case_identity':previous,
            'source_identity':row['source'],'geometry':g,'forward_count':actual['forward_count'],
            'rule_id':rid,'observed':stats,**provenance,
            'family_indices':[i for i,f in enumerate(actual['families']) if f in fs],
            'prior_rules_unchanged':case['runtime']['kernels']['service_regimes'][:-1]==prior_rules,
            'fresh_dependency_paths':paths,'whole_body_serial_sum_implied':False})
        print(cid,'11 typed calls, complete population',stats['count'],'mean_us',stats['mean_us'],flush=True)
    manifest.update(cases=rows,variant_id='observed-metadata-layer-13862d5e')
    write(DEST/'decode-forward-service-cases.json',manifest)
    write(DEST/'observed-populations.json',{'schema_version':'mindie-metadata-service-populations/1',
        'cases':evidence,'generator_identity':pin(__file__),'prior_manifest_identity':pin(prior_manifest),
        'source_commit':COMMIT,'raw_scans':0,'new_costs':0})


if __name__=='__main__':
    prepare()
