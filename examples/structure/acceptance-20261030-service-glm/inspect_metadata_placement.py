"""Join retained AI_CPU metadata examples to independent Body/layer windows.

[Role] Distinguish native device-task placement from Python setup-call placement.
[Invariants] Full histograms establish population, six saved examples establish
  local order only. Same-stream succession does not imply an additive Body budget.
[Timeouts & Locks] Small retained JSON reads; no raw scan, locks or prediction.
[Side-Effect Policy] Writes one compact placement-evidence sidecar.
"""
from build_service_cases import HERE, ROOT, pin, read, write


def main():
    cases = []
    for cid in ['glm53flash-a5-tp8-c1', 'a5_glm53flash_tp8_c4_p8k', 'a5_glm53flash_tp8_c8_p4k']:
        path = ROOT / f'data/observations/sources/arch3510-physical-services/scalar-dma-{cid}.json'
        pmu = read(path); actual = read(pmu['actual_identity']['path']); body = read(pmu['body_identity']['path'])
        part = next(g for g in pmu['partitions'] if g['native_operator_type'] == 'SparseFlashMlaMetadata')
        families = {name: next(f for f in actual['families'] if f['native_operator_type'] == name)
                    for name in ('SparseFlashMlaMetadata', 'SparseFlashMla', '_glm5_next_lightning_indexer_score_kernel')}
        assert part['duration_ns_counter'] == families['SparseFlashMlaMetadata']['duration_ns_counter']
        examples = []
        for event in part['raw_pmu']['examples']:
            forward = next(f for f in body['forwards'] if f['forward_id'] == event['forward_id'])
            layer = next(s for s in forward['stages'] if s['layer_id'] is not None and
                         s['start_ns'] <= event['start_ns'] < event['end_ns'] <= s['end_ns'])
            following = next(e for e in families['SparseFlashMla']['examples'] if e['layer_id'] == layer['layer_id'])
            score = next(e for e in families['_glm5_next_lightning_indexer_score_kernel']['examples'] if e['layer_id'] == layer['layer_id'])
            assert following['locator']['stream_id'] == event['locator']['stream_id']
            assert score['end_ns'] < event['start_ns'] < event['end_ns'] < following['start_ns']
            assert layer['attention'] == 'mla'
            examples.append({
                'metadata': {k:event[k] for k in ('event_id','locator','start_ns','end_ns','duration_ns','forward_id')},
                'accelerator_core': event['raw_fields']['Accelerator Core'], 'block_num': event['raw_fields']['Block Num'],
                'layer_id': layer['layer_id'], 'attention': layer['attention'],
                'body_start_ns': forward['start_ns'], 'body_end_ns': forward['end_ns'],
                'layer_start_ns': layer['start_ns'], 'layer_end_ns': layer['end_ns'],
                'start_after_body_us': (event['start_ns']-forward['start_ns'])/1000,
                'preceding_index_score': score, 'following_sparse_attention': following,
                'csv_line_distance': following['locator']['csv_line']-event['locator']['csv_line'],
                'metadata_end_to_attention_start_ns': following['start_ns']-event['end_ns'],
                'same_stream': True, 'metadata_attention_overlap_ns': 0,
            })
        cases.append({'case_id':cid,'source_identity':pmu['source_identity'],'pmu_identity':pin(path),
            'actual_identity':pmu['actual_identity'],'body_identity':pmu['body_identity'],
            'forward_count':pmu['forward_count'],'metadata_call_count':sum(n for _,n in part['duration_ns_counter']),
            'metadata_calls_per_body':11,'complete_histogram_matches_retained_actual':True,'examples':examples})
    value = {'schema_version':'mindie-glm-metadata-placement-evidence/1', 'cases':cases,
        'extractor_identity':pin(__file__), 'raw_reads':0, 'cost_calls':0,
        'conclusions':[
            'The full retained metadata population was collected inside accepted Body windows. Six exact retained examples occur in MLA layers 3 and 7 after that layer index-score call and before its SparseFlashMla on the same stream.',
            'These observed device executions are not all before Forward. Python before-forward setup alone does not establish native device task placement.',
            'Five examples are adjacent CSV rows; one has an intervening row not retained in this sidecar. All six have positive 621..740ns metadata-end to attention-start gaps and zero mutual overlap.',
            'Examples do not recover every occurrence dependency or all other-stream overlap. 11/F is a population count, not proof that 11*Mean is an additive Body delay. Source caller/readiness dependencies are still required.'],
        'scope':'Three full native histograms plus six existing integer-ns event examples; no new raw scan or invented complete per-occurrence timeline.',
        'inspection_correction':'An initial local adjacency assertion assumed every following attention row was consecutive. c8 layer3 has CSV distance2; final sidecar records actual row distance without inventing the intervening event.'}
    write(HERE/'metadata-placement-evidence.json',value)
    print([(r['case_id'], [(e['layer_id'],e['metadata']['locator']['csv_line'],e['start_after_body_us'],e['metadata_end_to_attention_start_ns']) for e in r['examples']]) for r in cases])


if __name__ == '__main__':
    main()
