"""Actual retained Body rows exercise focus selection and separate evidence axes."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def real_focus(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    helper = importlib.import_module('high_concurrency_scoreboard')
    captured = json.loads((ROOT / 'tests/fixtures/source_callers/high-concurrency-focus.json').read_text())
    return helper, captured


def by_source(view, source_id):
    return next(row for row in view['sources'] if row['source_case_id'] == source_id)


def test_retained_service_receipts_keep_explicit_in_sample_labels(real_focus):
    helper, data = real_focus
    board = importlib.import_module('priority_decode_scoreboard')
    receipts = [
        ROOT / 'examples/structure/acceptance-20261030-service-glm/decode-forward-service-replay.json',
        ROOT / 'examples/structure/acceptance-20261030-service-qwen-a3/decode-forward-qwen-service-replay.json']
    current = {(row['case_id'], row['source_identity']['sha256']): row for row in data['current']}
    for path in receipts:
        receipt, identity = board._read(path)
        for row in board.body_rows(receipt, identity):
            key = (row['case_id'], row['source_identity']['sha256'])
            if key in current: current[key] = row
    view = helper.build_focus(current.values(), data['focus_spec'], current.values())
    for name in ('qwen36-a5-tp2-c96', 'a5_glm53flash_tp8_c64_p4k'):
        row = by_source(view, name)
        assert row['body_accuracy_status'] == 'PASS'
        assert row['calibration']['evaluation_relation'] == 'in_sample'
    assert view['summary']['distinct_source_count'] == 13
    assert view['summary']['observed_forward_count'] == 877


def test_real_body_accuracy_and_overlapping_sections_preserve_one_population(real_focus):
    helper, data = real_focus
    view = helper.build_focus(data['current'], data['focus_spec'], data['current'])
    assert view['summary']['distinct_source_count'] == 13
    assert view['summary']['observed_forward_count'] == 877
    assert len(view['accepted_source_arms']) == 8 and len(view['priority_a5']) == 6
    qwen = by_source(view, 'qwen36-a5-tp2-c96')
    assert qwen['body_accuracy_status'] == 'FAIL'
    assert qwen['relative_error'] == pytest.approx(-0.1551407053756646)
    assert qwen['absolute_ms_outside_15pct_band'] == pytest.approx(0.328251336709774)
    v4 = by_source(view, 'v4flash-a3-tp8-c4')
    assert v4['body_accuracy_status'] == 'PASS'
    assert not v4['contract_boundary']['body_pass_implies_native_contract_closure']
    assert qwen['tpot']['client_profiled_ms']['p50'] == pytest.approx(31.824432297650745)
    assert qwen['observed_body_ms']['p50'] == pytest.approx(63.561524)
    precision = view['summary']['body_precision']
    errors = sorted(abs(row['comparison']['predicted_ms'] / row['comparison']['observed_ms']['mean'] - 1)
                    for row in data['current'])
    assert precision['population_count'] == 13
    assert precision['within_relative_error'] == {
        str(limit): sum(error <= limit / 100 for error in errors) for limit in (5, 8, 10, 15)}
    assert precision['absolute_relative_error_mean'] == pytest.approx(sum(errors) / 13)
    assert precision['absolute_relative_error_median'] == pytest.approx(errors[6])
    assert precision['within_relative_error']['15'] == view['summary']['body_pass_count']


def test_caller_selected_new_arm_replaces_old_without_using_focus_predictions(real_focus):
    helper, data = real_focus
    old = data['qwen96_previous']
    old_rows = [old if row['case_id'] == old['case_id'] else row for row in data['current']]
    spec = deepcopy(data['focus_spec'])
    # The retained prior real result is deliberately present in inventory metadata;
    # it must never override the selected current result supplied to the API.
    next(row for row in spec['cases'] if row['case_id'] == old['case_id'])['body'] = old
    before = helper.build_focus(old_rows, spec)
    after = helper.build_focus(data['current'], spec)
    a = by_source(before, 'qwen36-a5-tp2-c96'); b = by_source(after, 'qwen36-a5-tp2-c96')
    assert a['predicted_body_ms'] != b['predicted_body_ms']
    assert b['predicted_body_ms'] == pytest.approx(53.94710891329023)
    assert a['observed_body_ms'] == b['observed_body_ms']
    assert before['summary']['observed_forward_count'] == after['summary']['observed_forward_count']


def test_actual_timeout_is_distinct_from_retained_completed_prediction(real_focus):
    helper, data = real_focus
    # Replay the real retained timeout as the latest-attempt input to exercise
    # the display rule; this does not relabel its historical execution time.
    latest = [data['qwen96_timeout'] if r['case_id'] == data['qwen96_timeout']['case_id'] else r for r in data['current']]
    view = helper.build_focus(data['current'], data['focus_spec'], latest)
    qwen = by_source(view, 'qwen36-a5-tp2-c96')
    assert qwen['selected_execution_status'] == 'COMPLETED'
    assert qwen['latest_execution_status'] == 'EXEC_FAILED'
    assert not qwen['selected_is_latest_attempt']
    assert qwen['latest_error']['reason'] == 'body_prediction_timeout'
    assert qwen['predicted_body_ms'] == pytest.approx(53.94710891329023)
    assert 'EXEC_FAILED' in '\n'.join(helper.render_focus(view))


def test_explicit_observed_calibration_does_not_downgrade_body_or_contract_status(real_focus):
    helper, data = real_focus
    rows = deepcopy(data['current'])
    v4 = next(row for row in rows if row['case_id'].startswith('v4flash-a3-tp8-c4:'))
    # Metadata declaration only: exercise admission independence without claiming
    # that this historical V4 prediction actually used a fitted parameter.
    v4['calibration_origin'] = 'observed'
    v4['calibration_evidence'] = {'evaluation_relation': 'in_sample',
        'fit_source_identity': v4['source_identity'], 'evaluation_source_identity': v4['source_identity']}
    view = helper.build_focus(rows, data['focus_spec'])
    result = by_source(view, 'v4flash-a3-tp8-c4')
    assert result['body_accuracy_status'] == 'PASS'
    assert result['calibration']['origin'] == 'observed'
    assert result['calibration']['evaluation_relation'] == 'in_sample'
    assert by_source(view, 'qwen36-a5-tp2-c96')['calibration']['origin'] == 'not_declared'


def test_same_case_label_on_two_real_sources_keeps_both_rendered_populations(real_focus):
    helper, data = real_focus
    selected = [deepcopy(row) for row in data['current']
                if row['case_id'].startswith(('qwen36-a5-tp2-c12:', 'qwen36-a5-tp2-c96:'))]
    focus = {'cases': [deepcopy(row) for row in data['focus_spec']['cases']
                      if row['source_case_id'] in {'qwen36-a5-tp2-c12', 'qwen36-a5-tp2-c96'}]}
    # A caller may reuse its display label across different retained captures.
    # Source identities and every measured value stay from the two real rows.
    for row in selected + focus['cases']:
        row['case_id'] = 'shared-display-label'
    view = helper.build_focus(selected, focus, selected)
    assert view['summary']['distinct_source_count'] == 2
    lines = '\n'.join(helper.render_focus(view))
    assert 'qwen36-a5-tp2-c12 /' in lines
    assert 'qwen36-a5-tp2-c96 /' in lines
    assert '-22.19%' in lines and '-15.51%' in lines
