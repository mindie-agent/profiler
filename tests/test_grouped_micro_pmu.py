"""Real A3/A5 native branches and PMU populations without capture I/O."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'examples/structure'))
from summarize_grouped_micro_services import complete_pmu, histogram_stats, native_coordinates, source_branch


def fixture(name):
    data = json.loads((ROOT/'tests/fixtures/grouped_micro/retained_populations.json').read_text())
    return data[name]['partition']


def test_int32_up_does_not_inherit_bf16_down_source_schedule():
    part = fixture('a5up'); axes = native_coordinates(part)
    assert (axes['matrix_n'],axes['matrix_k'],axes['stored_expert_banks']) == (1024,2048,64)
    assert axes['input_buffer_capacity_rows'] == 128
    assert axes['observed_valid_rows'] is None
    assert axes['observed_active_experts'] is None
    assert source_branch(part,'arch3510')['source_formula'] is None
    down = fixture('a5down')
    assert source_branch(down,'arch3510')['native_scale_dtype'] == 'bf16'
    assert native_coordinates(down)['matrix_k'] == 512


def test_a3_fused_swiglu_output_is_half_matrix_n_and_capacity_is_unproven():
    part = fixture('a3up'); axes = native_coordinates(part)
    assert axes['matrix_n'] == 4096 and part['native_abi'][3][0][0][1] == 2048
    assert axes['weight_dtype'] == 'DT_INT4'
    assert axes['input_buffer_capacity_rows'] == 128
    assert axes['capacity_equals_valid_rows'] is False
    assert axes['observed_expert_rows'] is None


def test_full_integer_call_histogram_keeps_native_mean_and_median():
    part = fixture('a5down'); stats = histogram_stats(part['duration_ns_counter'])
    pmu = part['raw_pmu']['fields']['Duration(us)']['statistics']
    assert stats['count'] == 2520
    assert stats['mean_us'] == pytest.approx(pmu['mean'])
    assert stats['p50_us'] == pytest.approx(pmu['p50'])
    assert stats['p90_us'] == pytest.approx(pmu['p90'])


def test_numeric_zero_and_missing_pmu_stay_distinct():
    up = complete_pmu(fixture('a5up')); missing = complete_pmu(fixture('a3_missing'))
    assert up['complete_numeric_mean_us']['aiv_scalar_time(us)'] == 0
    assert up['fields']['aiv_scalar_time(us)']['zero_count'] == 2520
    assert missing['complete_numeric_mean_us']['aiv_scalar_time(us)'] is None
    assert missing['fields']['aiv_scalar_time(us)']['numeric_count'] == 3298
    assert missing['fields']['aiv_scalar_time(us)']['missing_or_na_count'] == 2
    assert missing['aiv_signed_diagnostics']['signed_aiv_minus_pipe_sum_us'] is None


def test_incomplete_numeric_subset_is_not_a_full_call_mean():
    part = deepcopy(fixture('a5down'))
    part['raw_pmu']['fields']['aiv_scalar_time(us)']['numeric_count'] -= 1
    result = complete_pmu(part)
    assert result['complete_numeric_mean_us']['aiv_scalar_time(us)'] is None
    assert result['aiv_signed_diagnostics']['signed_aiv_minus_pipe_sum_us'] is None
    assert result['isolated_descriptor_or_scalar_price_ns'] is None
