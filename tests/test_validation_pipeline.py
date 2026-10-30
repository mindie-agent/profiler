"""Retained current results exercise canonical projection and model ownership."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from pipeline import archive_report, decode_populations, execute, identity, project, retained_cards
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


def test_retained_native_population_registration_changes_operator_inputs_only(tmp_path):
    sample = samples()[0]
    pointer = archive_report(sample['result'], tmp_path)
    runtime = {'package_sha256': 'retained-runtime', 'version': '0.8.0'}
    updated = deepcopy(sample['row'])
    # The evidence pointer can be registered without changing the already
    # verified Body declaration; it must invalidate an operator comparison.
    updated['operator_population_evidence'] = [pointer]
    for scope in ('body', 'operators'):
        card = project(sample['row'], sample['result'], pointer, scope=scope)
        previous = {'scope': scope, 'runtime': runtime, 'cases': [card]}
        if scope == 'body':
            assert retained_cards(previous, [updated], set(), runtime, scope) == [card]
        else:
            with pytest.raises(ValueError, match='changed_case_requires_replay'):
                retained_cards(previous, [updated], set(), runtime, scope)


def test_real_glm128k_primary_pass_does_not_cover_other_five_populations():
    rows = json.loads((ROOT / 'tests/fixtures/pipeline/glm128k_populations.json').read_text())['rows']
    original = deepcopy(rows)
    limited = decode_populations(rows, require_all=False)
    assert limited['comparison']['passed'] is True
    full = decode_populations(rows, require_all=True)
    assert full['comparison']['primary_population_passed'] is True
    assert full['status'] == full['comparison']['status'] == 'compared'
    assert full['source_all_populations_passed'] is None
    assert full['comparison']['passed'] is True
    assert full['population_coverage']['observed_calls'] == 98
    assert full['population_coverage']['covered_calls'] == 68
    assert {p['geometry']['sequences_per_replica']: p['forward_count']
            for p in full['geometry_comparisons']} == {1: 68, 4: 13, 3: 1, 2: 3, 8: 12, 7: 1}
    assert full['comparison']['observed_ms']['p50'] == rows[0]['comparison']['observed_ms']['p50']
    assert full['population_coverage']['complete'] is False
    assert full['population_coverage']['scoring_scope'] == 'primary_population'
    assert full['population_coverage']['all_population_evaluation_requested'] is True
    assert limited['population_coverage']['all_population_evaluation_requested'] is False
    assert full['population_coverage']['primary_population_basis'] == 'largest_complete_forward_count'
    assert full['population_coverage']['primary_population_host_steady_state_confirmed'] is False
    assert rows == original


def test_failed_minority_population_remains_visible_without_vetoing_headline():
    rows = json.loads((ROOT / 'tests/fixtures/pipeline/glm128k_populations.json').read_text())['rows']
    # Replay outcome perturbation: no captured durations or geometry change.
    rows[-1]['comparison'].update(status='failed', passed=None, reasons=['body_prediction_timeout'])
    full = decode_populations(rows, require_all=True)
    assert full['status'] == full['comparison']['status'] == 'compared'
    assert full['comparison']['passed'] is True
    assert full['source_all_populations_passed'] is None
    assert full['geometry_comparisons'][-1]['comparison']['reasons'] == ['body_prediction_timeout']
    assert full['geometry_comparisons'][-1]['comparison']['status'] == 'failed'


def test_real_complete_glm_buckets_preserve_failures_and_never_select_by_accuracy():
    samples = json.loads((ROOT / 'tests/fixtures/pipeline/decode_card_projection.json').read_text())['samples']
    populations = samples[1]['full_result_projection']['geometry_comparisons']
    rows = [{'geometry': p['geometry'], 'comparison': p['comparison'],
             'status': p['comparison']['status'], 'per_layer_comparison': p['per_layer']}
            for p in populations]
    original = deepcopy(rows)
    full = decode_populations(list(reversed(rows)), require_all=True)
    assert full['comparison']['observed_forward_count'] == 68
    assert full['comparison']['passed'] is full['comparison']['primary_population_passed'] is True
    assert full['source_all_populations_passed'] is False
    assert full['population_coverage']['complete'] is True
    assert full['population_coverage']['covered_calls'] == full['population_coverage']['observed_calls'] == 98
    assert [p['comparison']['passed'] for p in full['geometry_comparisons']] == [True, False, False, True, True, True]
    # A selection control using the other unchanged real buckets must choose
    # the largest 13-call FAIL, rather than a smaller bucket that passes.
    other = decode_populations(rows[1:], require_all=True)
    assert other['comparison']['observed_forward_count'] == 13
    assert other['comparison']['passed'] is False
    assert other['comparison'] == {**rows[1]['comparison'], 'primary_population_passed': False}
    assert rows == original
    # A failed primary prediction is not replaced by any passing minority.
    failed = deepcopy(rows)
    failed[0]['comparison'].update(status='failed', passed=None, reasons=['body_prediction_timeout'])
    failed_primary = decode_populations(failed, require_all=True)
    assert failed_primary['status'] == failed_primary['comparison']['status'] == 'failed'
    assert failed_primary['comparison']['passed'] is None
    assert failed_primary['comparison']['observed_forward_count'] == 68
    assert failed_primary['comparison']['reasons'] == ['body_prediction_timeout']


def test_operator_reuse_checks_declared_body_pin_before_equivalent_boundaries(tmp_path):
    from pipeline import operator_case
    extraction = tmp_path / 'mixed-body.json'
    extraction.write_bytes((ROOT / 'tests/fixtures/pipeline/mixed_decode_populations.json').read_bytes())
    prior = json.loads(extraction.read_text())
    row = {'id': 'decode:v4flash-a3-tp8-c4', 'case_id': 'v4flash-a3-tp8-c4',
           'source': prior['source_identity'], 'extraction_path': str(extraction),
           'extraction_identity': identity(extraction), 'sim_case_path': 'retained-model.json'}
    # The topology remains byte-for-byte equivalent after JSON decoding, but
    # the consumed artifact is no longer the one declared in the registry.
    extraction.write_bytes(extraction.read_bytes() + b'\n')
    with pytest.raises(ValueError, match='operator_body_extraction_changed_from_registry'):
        operator_case(row, tmp_path, tmp_path / 'operators', 90)


@pytest.mark.parametrize('all_populations', [False, True])
def test_operator_entry_preserves_real_mixed_population_selection(tmp_path, monkeypatch, all_populations):
    import operators
    from pipeline import operator_case
    extraction = ROOT / 'tests/fixtures/pipeline/mixed_decode_populations.json'
    prior = json.loads(extraction.read_text())
    row = {'id': 'decode:v4flash-a3-tp8-c4', 'case_id': 'v4flash-a3-tp8-c4',
           'source': prior['source_identity'], 'extraction_path': str(extraction),
           'extraction_identity': identity(extraction),
           'sim_case_path': 'retained-model.json', 'geometry': {'context_tokens': 4096}}
    if all_populations:
        row['geometry_limit'] = None
    class ExtractionBoundary(Exception):
        pass
    def verify_entry(entry, case_paths, output, *, geometry_limit, context_tokens):
        assert identity(entry['report_path'])['sha256'] == entry['report_sha256']
        assert entry['source_identity'] == prior['source_identity']
        assert context_tokens == 4096
        assert geometry_limit is (None if all_populations else 1)
        # The real retained minority has four complete calls. The entry must
        # forward the caller's selection policy before any scan or prediction.
        counts = sorted((g['body_forward_span_ms']['count'] for g in prior['geometry_groups']), reverse=True)
        assert counts == [104, 4]
        assert sum(counts if geometry_limit is None else counts[:geometry_limit]) == (108 if all_populations else 104)
        raise ExtractionBoundary
    monkeypatch.setattr(operators, 'extract_case', verify_entry)
    with pytest.raises(ExtractionBoundary):
        operator_case(row, tmp_path, tmp_path / 'operators', 90)
