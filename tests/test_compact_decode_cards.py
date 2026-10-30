"""Actual multi-geometry Decode cards retain scores during bounded projection."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from pipeline import archive_report, compact_card, project, render, retained_cards


def samples():
    return json.loads((ROOT / 'tests/fixtures/pipeline/decode_card_projection.json').read_text())['samples']


def assert_population_scores(old, new):
    assert new['comparison'] == old['comparison']
    assert new['population_coverage'] == old['population_coverage']
    assert new['source_all_populations_passed'] == old['source_all_populations_passed']
    assert new['per_layer']['summary'] == old['per_layer']['summary']
    assert len(new['geometry_comparisons']) == len(old['geometry_comparisons'])
    for before, after in zip(old['geometry_comparisons'], new['geometry_comparisons']):
        assert after['geometry'] == before['geometry']
        assert after['forward_count'] == before['forward_count']
        for key, value in after['comparison'].items():
            assert value == before['comparison'][key]
        for field in ('attention_kind_distributions', 'ffn_kind_distributions'):
            for original, reduced in zip(before['per_layer'].get(field, []), after['per_layer'].get(field, [])):
                for metric in ('observed_ms', 'predicted_ms'):
                    for key in ('count', 'mean', 'p50', 'p90'):
                        assert reduced[metric][key] == original[metric][key]
                for key in ('mean', 'p50'):
                    assert reduced['relative_errors'][key] == pytest.approx(
                        original['predicted_ms'][key] / original['observed_ms'][key] - 1)


def test_actual_multibucket_projection_preserves_every_population_and_layer_scores():
    for sample in samples():
        original = deepcopy(sample['card'])
        reduced = compact_card(original)
        assert_population_scores(original, reduced)
        assert original == sample['card']
        assert compact_card(reduced) == reduced
        assert reduced['evidence'] == original['evidence']
        assert reduced['calibration'] == original['calibration']
        assert len(json.dumps(reduced)) < len(json.dumps(original)) * 0.8
        for before, after in zip(original['per_layer']['steady_layer_comparison']['excluded_layers'],
                                 reduced['per_layer']['steady_layer_comparison']['excluded_layers']):
            assert after['layer_id'] == before['layer_id']
            assert after['observed_ms']['p90'] == before['observed_ms']['p90']
            assert after['relative_error'] == before['relative_error']


def test_new_and_retained_actual_cards_use_identical_compaction(tmp_path):
    runtime = {'package_sha256': 'same-runtime-projection-test', 'version': '0.8.0'}
    for sample in samples():
        pointer = archive_report(sample['full_result_projection'], tmp_path)
        old = {**sample['card'], 'evidence': pointer}
        projected = project(sample['row'], sample['full_result_projection'], pointer, scope='body')
        retained = retained_cards({'scope': 'body', 'runtime': runtime, 'cases': [old]},
                                 [sample['row']], set(), runtime, 'body')[0]
        assert_population_scores(old, projected)
        assert projected['per_layer'] == retained['per_layer']
        assert projected['geometry_comparisons'] == retained['geometry_comparisons']
        assert projected['stage_span_ms'] == retained['stage_span_ms']
        assert json.loads(Path(pointer['path']).read_text()) == sample['full_result_projection']


def test_compact_render_keeps_failed_and_unscored_geometry_visible():
    cards = [compact_card(sample['card']) for sample in samples()]
    text = render({'scope': 'body', 'cases': cards, 'summary': {}})
    assert 'unresolved' in text
    assert 'FAIL' in text
    assert 'Mean / P50 error' in text
    assert 'median of per-layer call P50' in text
    for card in cards:
        for population in card['geometry_comparisons']:
            geometry = population['geometry']
            assert f"| {card['case_id']} | {geometry['sequences_per_replica']} | {geometry['tokens_per_sequence']} |" in text
