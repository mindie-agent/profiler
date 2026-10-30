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
