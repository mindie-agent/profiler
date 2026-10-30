"""Real hidden-output forwards and retained pre-activity extraction schema."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
from mindie_profiler.normalized import kernel_rows

ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / 'tests/fixtures/decode_forward'


def test_two_real_terminal_norm_forwards_pair_without_a_vocabulary_head(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    compare = importlib.import_module('replay_controller_aliases').compare
    config = json.loads((FIXTURE / 'a3_v41_dspark7_model_config.json').read_text())
    actual = auto_segment_decode_forwards(kernel_rows(FIXTURE / 'a3_v41_dspark7_two_forwards.csv'), config)
    assert len(actual['forwards']) == 2
    assert all(row['head_start_ns'] is None for row in actual['forwards'])
    result = compare(actual, actual)
    assert result['accepted_population_unchanged']
    assert result['previous_body_count'] == result['current_body_count'] == 2
    assert result['body_endpoint_changed_count'] == 0
    assert result['changed_forwards'] == []


def test_historical_missing_activity_is_unavailable_not_zero_or_unchanged(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    compare = importlib.import_module('replay_controller_aliases').compare
    config = json.loads((FIXTURE / 'a3_kimi4_c32_model_config.json').read_text())
    actual = auto_segment_decode_forwards(kernel_rows(FIXTURE / 'a3_kimi4_c32_first_full_body.csv'), config)
    # The preserved GLM dc4k generation predates these activity fields. Apply
    # that documented metadata projection to unchanged real captured timings.
    legacy = deepcopy(actual)
    for field in ('body_activity_ms', 'body_internal_gap_ms'):
        legacy.pop(field)
        for row in legacy['forwards']:
            row.pop(field)
    result = compare(legacy, actual)
    assert result['accepted_population_unchanged']
    assert result['previous_body_activity_ms'] is None
    assert result['body_activity_previous_missing_count'] == 1
    assert result['body_activity_changed_count'] == 0
    assert result['body_endpoint_changed_count'] == 0
    assert result['changed_forwards'][0]['before']['body_activity_ms'] is None
    assert result['changed_forwards'][0]['after']['body_activity_ms'] == 6.519291
