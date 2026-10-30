"""Retained current results exercise canonical projection and model ownership."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from pipeline import archive_report, execute, identity, project, retained_cards
from engine import geometry_key, observed_case

FIXTURE = ROOT / 'tests/fixtures/prefill/pipeline_projection.json'


def samples():
    return json.loads(FIXTURE.read_text())['cases']


def test_real_prefill_archive_keeps_layer_detail_and_ttft_out_of_body(tmp_path):
    sample = samples()[0]
    full = sample['result']
    pointer = archive_report(full, tmp_path)
    restored = json.loads(Path(pointer['path']).read_text())
    card = project(sample['row'], restored, pointer)
    assert identity(pointer['path'])['sha256'] == pointer['sha256']
    assert card['comparison'] == full['comparison']
    assert card['comparison']['passed'] is True
    assert card['comparison']['observed_ms']['mean'] == 436.567509
    assert card['client']['ttft_ms'] == full['client']['ttft_ms']
    assert card['client']['ttft_ms']['mean'] != card['comparison']['observed_ms']['mean']
    assert card['ttft_prediction_ms'] is None
    assert card['prefix_cache']['observed_hit_ratio'] is None
    assert 'layers' not in card['per_layer']
    assert restored['per_layer_comparison']['layers'] == full['per_layer_comparison']['layers']
    assert card['evidence'] == pointer


def test_real_v4pro_missing_ttft_does_not_use_e2e_or_body(tmp_path):
    sample = samples()[1]
    pointer = archive_report(sample['result'], tmp_path)
    card = project(sample['row'], sample['result'], pointer)
    assert card['comparison']['observed_ms']['mean'] == 2586.2334069999997
    assert card['client']['e2e_ms']['mean'] == 2732.478460064158
    assert card['client']['ttft_ms'] is None
    assert card['ttft_prediction_ms'] is None
    assert card['client']['e2e_substituted_for_ttft'] is False
    assert card['query_coverage_complete'] is True


def test_real_engine_timeout_preserves_cycles_without_promoting_body_to_tpot(tmp_path):
    sample = samples()[2]
    pointer = archive_report(sample['result'], tmp_path)
    card = project(sample['row'], sample['result'], pointer)
    assert card['status'] == 'failed'
    assert card['comparison'] == {}
    assert card['serving_prediction']['reason'] == 'serving_prediction_timeout'
    assert card['engine']['observed_target_forwards'] == 55
    assert card['engine']['cycle_count'] == 54
    assert card['engine']['client_delivery_prediction_claimed'] is False
    groups = card['engine']['cycle_geometry_groups']
    primary = next(g for g in groups if geometry_key(g['geometry']) == geometry_key(card['engine']['primary_geometry']))
    tpot = card['engine']['serving_evidence']['profiled_request_population']['recomputed_per_request_tpot_ms']
    assert primary['target_cycle_span_ms']['p50'] != tpot['p50']
    assert primary['body_span_ms']['p50'] < primary['target_cycle_span_ms']['p50']


def model_row(tmp_path):
    sample = samples()[0]
    path = tmp_path / 'actual-case.json'
    path.write_text(json.dumps(sample['model_json']) + '\n')
    row = deepcopy(sample['row'])
    row['model_case'] = identity(path)
    row['sim_case_path'] = str(path)
    return row, path


def test_verified_declaration_cannot_point_to_a_different_consumed_model(tmp_path):
    row, path = model_row(tmp_path)
    other = tmp_path / 'other-retained-case.json'
    other.write_text(json.dumps(samples()[1]['model_json']) + '\n')
    row['sim_case_path'] = str(other)
    result = execute(row, tmp_path, 'body', tmp_path / 'archive', 1, {})
    assert result['status'] == 'failed'
    assert result['error']['message'] == 'model_declaration_path_differs_from_consumer'
    assert result['comparison']['passed'] is False


def test_model_bytes_changed_after_registry_pin_fail_before_prediction(tmp_path):
    row, path = model_row(tmp_path)
    path.write_text(path.read_text() + '\n')
    result = execute(row, tmp_path, 'body', tmp_path / 'archive', 1, {})
    assert result['status'] == 'failed'
    assert result['error']['message'] == 'model_declaration_changed_from_registry'
    assert result['comparison']['passed'] is False


def test_retained_engine_boundaries_cannot_be_relabelled_as_another_capture(tmp_path):
    captured=json.loads((ROOT/'tests/fixtures/engine_boundaries/retained_requests_and_scopes.json').read_text())
    actual=captured['sources']['qwen36-a5-tp2-c12']
    path=tmp_path/'retained-boundaries.json'
    path.write_text(json.dumps({**actual['extraction'],'source_identity':actual['source_identity']})+'\n')
    row=deepcopy(samples()[2]['row'])
    row['extraction_identity']=identity(path)
    row['engine']={}
    row['source']=samples()[1]['row']['source']
    with pytest.raises(ValueError,match='source_and_extraction_differ:'):
        observed_case(row,tmp_path)


def test_incremental_replay_preserves_same_runtime_evidence_not_historical_best(tmp_path):
    sample = samples()[0]
    pointer = archive_report(sample['result'], tmp_path)
    card = project(sample['row'], sample['result'], pointer)
    runtime = {'package_sha256': 'retained-runtime', 'version': '0.8.0'}
    previous = {'scope': 'body', 'runtime': runtime, 'cases': [card]}
    assert retained_cards(previous, [sample['row']], set(), runtime, 'body') == [card]
    # Selected cases are removed before execution even when the old cost passed.
    assert retained_cards(previous, [sample['row']], {card['id']}, runtime, 'body') == []
    changed = deepcopy(sample['row'])
    changed['model_case']['sha256'] = 'changed-cost-declaration'
    with pytest.raises(ValueError, match='changed_case_requires_replay'):
        retained_cards(previous, [changed], set(), runtime, 'body')
    with pytest.raises(ValueError, match='incremental_update_requires_same_sim'):
        retained_cards(previous, [sample['row']], set(), {**runtime, 'package_sha256': 'new-runtime'}, 'body')


def test_client_evidence_registration_does_not_invalidate_body_cost(tmp_path):
    sample = samples()[0]
    pointer = archive_report(sample['result'], tmp_path)
    runtime = {'package_sha256': 'retained-runtime', 'version': '0.8.0'}
    updated = deepcopy(sample['row'])
    updated['engine'] = {'benchmark_summary': {'path': 'new-client-capture.json', 'sha256': 'new-client-pin'}}
    for scope in ('body', 'operators', 'engine'):
        card = project(sample['row'], sample['result'], pointer, scope=scope)
        previous = {'scope': scope, 'runtime': runtime, 'cases': [card]}
        if scope == 'engine':
            with pytest.raises(ValueError, match='changed_case_requires_replay'):
                retained_cards(previous, [updated], set(), runtime, scope)
        else:
            assert retained_cards(previous, [updated], set(), runtime, scope) == [card]
            changed = deepcopy(updated)
            changed['model_case']['sha256'] = 'different-physical-model'
            with pytest.raises(ValueError, match='changed_case_requires_replay'):
                retained_cards(previous, [changed], set(), runtime, scope)
