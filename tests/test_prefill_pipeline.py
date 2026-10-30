"""Captured complete Qwen topology and missing V4Pro TTFT prevent scope inflation."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from prefill import align, anchor, client_measurement, associate_request, validate, request_population, identity, run_case, _anchor_groups, extract_events
from mindie_profiler.decode_segmentation import _Row
from mindie_profiler.events import Event
from mindie_profiler.normalized import shapes, row_from_event


def fixture():
    value=json.loads((ROOT/'tests/fixtures/prefill/qwen36-prefill-first-head.json').read_text())
    rows=[_Row(Event(**r['event']),tuple(tuple(s) for s in r['inputs']) if r['inputs'] is not None else None,
               tuple(tuple(s) for s in r['outputs']) if r['outputs'] is not None else None) for r in value['rows']]
    return value,rows


def kimi_fixture(name='kimi-prefill-first-head.json'):
    value=json.loads((ROOT/'tests/fixtures/prefill'/name).read_text())
    rows=[]
    for retained in value['rows']:
        event=Event(**value['event_defaults'],
                    **dict(zip(value['event_fields'],retained[:-1])),locator=retained[-1])
        rows.append(_Row(event,shapes(event.input_shapes),shapes(event.output_shapes)))
    return value,rows


def test_real_kimi_93_layers_keep_all_chunk_stages_and_crosscheck_global_query():
    value,rows=kimi_fixture();result,error=align(rows,value['model_config'],0)
    assert error is None
    assert result['matched_layer_count']==93 and result['query_rows']==8192
    assert {key:result['body'][key] for key in value['expected_body']}==value['expected_body']
    kda=[g for g in result['attention_stage_groups'] if g['native_type']=='ChunkKdaFwd']
    assert len(kda)==69 and sum(g['physical_events'] for g in kda)==276
    assert all(g['physical_events']==4 for g in kda)
    assert [l['attention'] for l in result['layers']]==[p['attention'] for p in value['model_config']['layer_plans']]
    assert rows[-1].inputs[0][0]==1  # Sampled head does not reduce the 8192-token Body.
    assert result['body']['event_count']==7024
    assert result['body']['end_ns']<result['head']['start_ns']


def test_kda_stages_with_different_dtype_cannot_merge_on_shape_alone():
    value,rows=kimi_fixture()
    physical=next(r for r in rows if r.kind=='ChunkKdaFwd')
    physical.event.input_dtypes=physical.event.input_dtypes.replace('DT_BF16','FLOAT',1)
    result,error=align(rows,value['model_config'],0)
    assert result is None and error['reason']=='ordered_prefill_layer_plan_mismatch'
    assert error['anchor_count']==94


def test_kimi_fia_query_must_agree_with_kda_even_when_layer_plan_matches():
    value,rows=kimi_fixture()
    index=next(i for i,r in enumerate(rows) if r.kind=='FusedInferAttentionScore')
    original=rows[index]
    changed=((4096,*original.inputs[0][1:]),*original.inputs[1:])
    rows[index]=_Row(original.event,changed,original.outputs)
    result,error=align(rows,value['model_config'],0)
    assert result is None and error['reason']=='inconsistent_large_query'
    assert error['queries']==[4096,8192]


def test_real_mla_prefix_and_current_attention_require_explicit_merge_contract():
    value,rows=kimi_fixture('kimi-mla-prefix-merge.json')
    groups=_anchor_groups(rows,value['model_config'])
    assert len(groups)==1 and groups[0]['physical_events']==2
    assert rows[groups[0]['merge_event']].kind=='AttentionUpdate'
    without_merge=[row for row in rows if row.kind!='AttentionUpdate']
    assert len(_anchor_groups(without_merge,value['model_config']))==2
    changed=deepcopy(rows)
    second=[r for r in changed if r.kind=='FusedInferAttentionScore'][1]
    second.event.output_dtypes='FLOAT;FLOAT'
    assert len(_anchor_groups(changed,value['model_config']))==2


def test_unclosed_no_attention_prefix_is_counted_without_unbounded_retention():
    value,rows=kimi_fixture()
    # Actual initial device events, before the first attention anchor. A bounded
    # incomplete fragment must not erase already completed observations or grow.
    fragment=rows[:44]
    result=extract_events((row_from_event(r.event) for r in fragment),value['model_config'],max_active_events=20)
    assert result['status']=='unresolved' and result['forwards']==[]
    assert result['scan_counts']['positive_events']==44
    assert result['scan_counts']['unclosed_non_prefill_events']==44
    assert result['scan_counts']['unclosed_non_prefill_segments']==1
    assert result['scan_counts']['trailing_events']==0


def test_real_64_layer_prefill_excludes_final_norm_logits_and_keeps_internal_communication():
    value,rows=fixture();result,error=align(rows,value['model_config'],0)
    assert error is None
    assert len(result['layers'])==64 and result['query_rows']==4096
    assert result['body']['span_ms']==value['expected_body']['span_ms']==156.479256
    assert {k:result['body'][k] for k in value['expected_body']}==value['expected_body']
    assert result['body']['end_ns']<result['head']['start_ns']
    assert not result['body_includes_mtp']


def test_missing_real_attention_layer_cannot_become_a_complete_body():
    value,rows=fixture();removed=next(i for i,r in enumerate(rows) if anchor(r))
    result,error=align(rows[:removed]+rows[removed+1:],value['model_config'],0)
    assert result is None and error['reason']=='ordered_prefill_layer_plan_mismatch'
    assert error['anchor_count']==63


def test_real_client_e2e_without_first_token_timestamp_is_not_ttft():
    path=ROOT/'tests/fixtures/prefill/v4pro-client-no-ttft.json'
    result=client_measurement(path)
    assert result['ttft_ms'] is None
    assert result['status']=='ttft_not_exported'
    assert result['e2e_ms']['mean']==2732.478460064158
    assert not result['e2e_substituted_for_ttft']


def test_excess_observed_query_rows_cannot_be_trimmed_to_a_client_wall_time():
    value,rows=fixture();forward,error=align(rows,value['model_config'],0)
    assert error is None
    observed={'forwards':[forward], 'matched_query_rows':4096,
              'body_span_sum_ms':forward['body']['span_ms']}
    result=associate_request(observed,prompt_tokens=2048,client={'ttft_ms':{'mean':80.0}})
    assert result['request_prefill_body_sum_ms'] is None
    assert result['body_span_sum_ms']==156.479256
    assert validate(result,value['model_config'])['status']=='passed'


def test_missing_client_population_keeps_query_workload_conditional():
    value,rows=fixture();forward,error=align(rows,value['model_config'],0)
    assert error is None
    observed={'forwards':[forward],'matched_query_rows':4096,
              'body_span_sum_ms':forward['body']['span_ms']}
    result=associate_request(observed,prompt_tokens=4096,client={})
    assert result['body_workload_comparable'] is True
    assert result['comparison_body_sum_ms']==156.479256
    assert result['request_prefill_body_sum_ms'] is None
    assert result['request_identity_status']=='unknown'


def test_real_multiple_request_records_cannot_establish_chunk_membership():
    captured=json.loads((ROOT/'tests/fixtures/engine_boundaries/retained_requests_and_scopes.json').read_text())
    requests=captured['sources']['qwen36-a5-tp2-c12']['requests']
    population=request_population({'per_request':requests})
    assert population['request_count']==12
    assert population['successful_requests']==12
    value,rows=fixture();forward,error=align(rows,value['model_config'],0)
    assert error is None
    observed={'forwards':[forward],'matched_query_rows':4096,
              'body_span_sum_ms':forward['body']['span_ms']}
    result=associate_request(observed,prompt_tokens=4096,
                             client={'request_population':population})
    assert result['prompt_query_coverage_complete'] is True
    assert result['body_workload_comparable'] is False
    assert result['comparison_body_sum_ms'] is None
    assert result['request_prefill_body_sum_ms'] is None


def test_heldout_prefill_client_summary_has_no_device_or_profile_scope():
    result=client_measurement(ROOT/'tests/fixtures/prefill/heldout-glm-prefill-client.json')
    assert result['request_population']['request_count']==2
    assert result['request_population']['successful_requests']==2
    assert result['concurrency']==1
    assert result['input_len']==2048 and result['output_len']==1
    assert result['ttft_ms']['mean']>0
    assert result['ttft_ms']['count'] is None
    assert result['profiled_client'] is None
    assert result['e2e_ms'] is None


def test_disaggregated_http_prefill_and_decode_ttft_are_not_device_body():
    result=client_measurement(ROOT/'tests/fixtures/prefill/heldout-v41-pd-client.json')
    assert result['ttft_ms'] is None
    assert result['prefill_http_ms']['mean']>0
    assert result['decode_ttft_ms']['mean']>0
    assert result['e2e_ms']['mean']>result['prefill_http_ms']['mean']
    assert result['request_population']['request_count']==4
    assert result['profiled_client'] is None


def test_pure_prefill_client_is_publishable_without_device_or_model(tmp_path):
    source=ROOT/'tests/fixtures/prefill/heldout-glm-prefill-client.json'
    row={'id':'prefill:a3_glm53flash_heldout_s5_prefill_p2048_c1',
         'case_id':'a3_glm53flash_heldout_s5_prefill_p2048_c1','phase':'prefill',
         'source':{**identity(source),'kind':'client_json'}}
    result=run_case(row,tmp_path)
    literal=json.loads(source.read_text())
    assert result['status']==result['comparison']['status']=='observed_only'
    assert result['client']['ttft_ms']['mean']==literal['ttft_ms_mean']
    assert result['client']['ttft_ms']['p50']==literal['ttft_ms_p50']
    assert result['client']['request_population']['request_count']==2
    assert result['client']['profiled_client'] is False
    assert result['comparison']['observed_ms']['mean'] is None
    assert result['comparison']['predicted_ms'] is None
    assert result['comparison']['passed'] is None
    assert result['observed']['device_body_available'] is False
    assert result['execution']['new_predictions']==0
    assert result['model_case_consumed'] is False
