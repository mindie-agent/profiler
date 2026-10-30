"""Real PMU controls: overlapping pipes, missing counters and exact numeric scope."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from summarize_scalar_dma_services import signed_diagnostics
from targeted_native_pmu import NativePmu


def fixture():
    return json.loads((ROOT / 'tests/fixtures/scalar_dma/real_pmu_populations.json').read_text())


def test_dsq_overlapping_busy_fields_keep_signed_diagnostic():
    result = signed_diagnostics(fixture()['dsq_complete_population'])
    assert result['complete_numeric_mean_us']['aiv_time(us)'] == pytest.approx(56.287055921052634)
    assert result['signed_aiv_minus_pipe_sum_us'] == pytest.approx(-26.17686875)
    assert result['signed_aiv_minus_max_pipe_us'] == pytest.approx(28.38984605263158)


def test_aicpu_metadata_absent_pmu_does_not_become_zero_service():
    result = signed_diagnostics(fixture()['metadata_complete_population'])
    assert result['complete_numeric_mean_us']['Duration(us)'] == pytest.approx(34.98046293706294)
    assert result['complete_numeric_mean_us']['aiv_scalar_time(us)'] is None
    assert result['signed_aiv_minus_pipe_sum_us'] is None
    assert result['signed_duration_minus_aiv_us'] is None


def test_partial_numeric_population_cannot_be_subtracted_from_full_call_mean():
    population = deepcopy(fixture()['dsq_complete_population'])
    population['fields']['aiv_mte2_time(us)']['numeric_count'] -= 1
    result = signed_diagnostics(population)
    assert result['complete_numeric_mean_us']['aiv_mte2_time(us)'] is None
    assert result['signed_aiv_minus_pipe_sum_us'] is None
    assert result['signed_aiv_minus_max_pipe_us'] is None


def test_real_csv_na_and_numeric_zero_have_distinct_counter_populations():
    examples = fixture()['raw_real_examples']
    for label, example in examples.items():
        raw = example['raw_fields']
        collector = NativePmu(raw)
        event = SimpleNamespace(**{k: example[k] for k in
            ('locator', 'event_id', 'start_ns', 'end_ns', 'duration_ns')})
        collector.add(raw, event, forward_id=example['forward_id'], layer_id=None)
        fields = collector.result()['fields']
        if label == 'metadata':
            assert fields['aiv_time(us)']['missing_or_na_count'] == 1
            assert fields['aiv_time(us)']['numeric_count'] == 0
            assert fields['aiv_time(us)']['statistics'] is None
        else:
            assert fields['aic_scalar_time(us)']['numeric_count'] == 1
            assert fields['aic_scalar_time(us)']['zero_count'] == 1
            assert fields['aic_scalar_time(us)']['missing_or_na_count'] == 0
