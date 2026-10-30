"""Real retained clients/scopes distinguish token TPOT, cycles and short graphs."""
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from engine import cycles, request_summary, request_metric_basis, union_ns, request_workload

FIXTURE=ROOT/'tests/fixtures/engine_boundaries/retained_requests_and_scopes.json'


def source(key):
    return json.loads(FIXTURE.read_text())['sources'][key]


def test_actual_qwen_cycles_and_counter_population_are_distinct():
    captured=source('qwen36-a5-tp2-c12')
    windows,invalid=cycles(captured['extraction'])
    assert not invalid
    assert len(captured['extraction']['forwards'])==55
    assert len(windows)==54  # final target has no observed successor
    assert len(captured['extraction']['auxiliary_occurrences'])==165
    assert {w['short_auxiliary_count'] for w in windows}=={3}
    for w in windows:
        assert w['known_scope_union_ms']+w['unclassified_outer_or_between_scope_ms']==pytest.approx(w['target_cycle_span_ms'])
        assert w['known_scope_union_ms']>=w['body_span_ms']
        assert w['auxiliary_identity_status']=='retained_short_subgraphs_not_proven_MTP'
    counters=captured['engine_window']
    assert counters['d_drafts']/len(captured['requests'])==55
    assert counters['d_generation_tokens']/counters['d_drafts']==pytest.approx(2.8954545454545455)
    # These are different windows: preserving both is required, not making the
    # service counter span numerically equal to target-start intervals.
    assert counters['metrics_interval_s']!=counters['profiler_window_s']


def test_livepre_reported_chunk_cadence_is_not_token_tpot():
    captured=source('glm53flash-a3-tp16-c4-livepre')
    result=request_summary(captured['requests'])
    assert result['actual_completion_tokens']==768
    assert result['reported_request_metric_denominators']=={'text_chunk':8}
    assert result['recomputed_per_request_tpot_ms']['p50']==pytest.approx(14.696906210462515)
    assert captured['reported_tpot']['p50']==pytest.approx(39.28998031806435)
    assert all(request_metric_basis(r)=='text_chunk' for r in captured['requests'])


def test_missing_v41_head_is_unknown_and_overlap_is_unioned_once():
    captured=source('a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64')['extraction']
    windows,invalid=cycles(captured)
    assert not invalid and len(windows)==1
    assert windows[0]['target_body_to_head_end_ms'] is None
    body=captured['forwards'][0];interval=(body['start_ns'],body['end_ns'])
    assert union_ns([interval,interval,(interval[0]+1,interval[1]-1)])==interval[1]-interval[0]


def test_formal_serving_workload_keeps_actual_arrivals_and_token_denominators():
    captured=source('qwen36-a5-tp2-c12')
    workload,origin=request_workload(captured['requests'])
    assert not workload['synthetic']
    assert len(workload['requests'])==12
    assert sum(r['output_tokens'] for r in workload['requests'])==6144
    for actual,mapped in zip(captured['requests'],workload['requests']):
        assert mapped['arrival_ms']==(actual['t_start_epoch']-origin)*1000
        assert (mapped['prompt_tokens'],mapped['output_tokens'])==(actual['prompt_tokens'],actual['completion_tokens'])
        assert mapped['prefix_tokens']==0  # explicit cold condition, not inferred from a mean hit ratio


CLIENT_FIXTURES = ROOT/'tests/fixtures/engine_boundaries/client_only'


def client_case(name, *, scope='client_only'):
    """Only the source identity is needed for an observation-only engine case."""
    from engine import identity

    path = CLIENT_FIXTURES/name
    entry = {
        'id': 'engine:'+path.stem, 'case_id': path.stem, 'phase': 'decode',
        'source': {**identity(path), 'kind': 'client_json'},
        'engine': {'scope': scope, 'observation_only': True},
    }
    return entry, json.loads(path.read_text())


def test_real_client_aggregate_preserves_ttft_and_distinct_event_token_denominators():
    from engine import run_case

    entry, captured = client_case('s1_c6_p4096.json')
    result = run_case(entry, CLIENT_FIXTURES)
    evidence = result['observed']['serving_evidence']
    metrics = evidence['metrics']
    assert metrics['ttft_ms']['mean'] == captured['ttft_ms_mean']
    assert metrics['ttft_ms']['mean'] != captured['server_ttft_ms_mean']
    assert metrics['itl_ms']['mean'] == pytest.approx(
        captured['decode_s_sum']*1000/captured['decode_events_sum'])
    assert metrics['tpot_ms']['mean'] == pytest.approx(
        captured['decode_s_sum']*1000/captured['token_gaps_sum'])
    assert metrics['itl_ms']['mean'] != metrics['tpot_ms']['mean']
    assert evidence['retained_counters']['decode_events_sum'] == 363
    assert evidence['retained_counters']['token_gaps_sum'] == 1524
    assert evidence['completion_tokens'] == 1536
    assert evidence['raw_request_records_available'] is False
    # A server acceptance aggregate cannot manufacture a per-device Step.
    assert evidence['retained_counters']['alpha_from_server'] == captured['alpha_from_server']
    assert 'acceptance_bridge' not in evidence  # no declared proposal-count input
    assert result['observed']['observed_target_forwards'] is None
    assert result['observed']['cycle_count'] is None
    assert result['observed']['cycle_geometry_groups'] == []
    assert result['observed']['outer_stage_measurements'] == []
    assert result['prediction'] is None
    assert result['comparison']['status'] == 'observed_only'
    assert result['comparison']['passed'] is None
    assert result['execution']['prediction_executions'] == 0


def test_real_one_token_prefill_retains_null_tpot_without_fake_decode_or_body():
    from engine import run_case

    entry, captured = client_case('s5_prefill_p2048_c1.json')
    result = run_case(entry, CLIENT_FIXTURES)
    evidence = result['observed']['serving_evidence']
    assert evidence['n_requests'] == 2
    assert evidence['request_configuration']['output_tokens'] == 1
    assert evidence['completion_tokens'] == 2
    assert evidence['metrics']['ttft_ms']['p50'] == captured['ttft_ms_p50']
    assert evidence['metrics']['tpot_ms']['mean'] is None
    assert evidence['metrics']['itl_ms']['mean'] is None
    assert evidence['retained_counters']['token_gaps_sum'] == 0
    assert result['observed']['observed_target_forwards'] is None
    assert result['prediction'] is None
    assert result['execution'] == {'raw_capture_reads': 0, 'prediction_executions': 0}


def test_real_pd_http_prefill_and_decoder_metrics_do_not_become_device_scopes():
    from engine import run_case

    entry, captured = client_case('pd_pipeline_c4_p4096.json', scope='disaggregated_pd')
    result = run_case(entry, CLIENT_FIXTURES)
    observation = result['observed']
    evidence = observation['serving_evidence']
    assert evidence['metrics']['prefill_ms']['mean'] == captured['prefill_ms_mean']
    assert evidence['metrics']['decode_ttft_ms']['mean'] == captured['decode_ttft_ms_mean']
    assert evidence['metrics']['e2e_ms']['mean'] == captured['e2e_ms_mean']
    assert evidence['metric_boundaries']['prefill_ms'] == 'prefiller HTTP request; not device Prefill Body'
    assert evidence['completion_tokens'] == evidence['retained_counters']['decode_generation_tokens_delta'] == 512
    assert observation['outer_stage_measurements'] == []
    assert observation['observed_target_forwards'] is None
    assert observation['cycle_count'] is None
    assert observation['client_delivery_prediction_claimed'] is False
    assert result['prediction'] is None
    assert result['comparison']['passed'] is None


def test_real_failed_pd_producer_keeps_partial_metrics_and_failures():
    from engine import run_case

    entry, captured = client_case('pd_pipeline_c24_p4096.json', scope='disaggregated_pd')
    result = run_case(entry, CLIENT_FIXTURES)
    evidence = result['observed']['serving_evidence']
    assert result['status'] == 'failed'
    assert result['comparison']['status'] == 'failed'
    assert result['comparison']['reason'] == 'producer_failed'
    assert result['error'] == captured['errors']
    assert evidence['n_requests'] == 24
    assert evidence['n_errors'] == 3
    assert len(evidence['errors']) == 3
    assert evidence['completion_tokens'] == captured['completion_tokens'] == 2688
    assert evidence['metrics']['tpot_ms']['mean'] == captured['tpot_ms_mean']
    assert evidence['metrics']['prefill_ms']['mean'] == captured['prefill_ms_mean']
    assert result['prediction'] is None
    assert result['comparison']['passed'] is None
    assert result['execution']['prediction_executions'] == 0


@pytest.mark.parametrize('name', [
    's1_c6_p4096.json', 'pd_pipeline_c4_p4096.json',
    'pd_pipeline_c24_p4096.json',
])
def test_compact_pipeline_keeps_real_client_metrics_and_failed_partial_population(name):
    from engine import run_case
    from pipeline import project

    entry, captured = client_case(name)
    result = run_case(entry, CLIENT_FIXTURES)
    card = project(entry, result, entry['source'])
    assert card['engine']['serving_evidence'] == result['observed']['serving_evidence']
    assert card['engine']['serving_evidence']['completion_tokens'] == captured['completion_tokens']
    assert card['engine']['serving_evidence']['n_errors'] == captured['n_errors']
    assert card['engine']['observed_target_forwards'] is None
    assert card['body_activity_ms'] is None
    assert card['geometry'] is None
    assert not card['serving_prediction']
    assert card['comparison']['passed'] is None
    if captured['status'] == 'failed':
        assert card['status'] == 'failed'
        assert card['error'] == captured['errors']
        assert len(card['error']) == 3
        assert card['engine']['serving_evidence']['metrics']['tpot_ms']['mean'] == captured['tpot_ms_mean']
