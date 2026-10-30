"""Real contract cohorts admit fitted rates without inventing observed work."""
from copy import deepcopy
import json

import pytest

from tests.retained_tensor_cohort import FIXTURE, mapping_for_case, retained_case


@pytest.fixture(scope='module')
def fitted_copy():
    pytest.importorskip('mindie_sim')
    from mindie_sim.cohort_comparison import compare_cohorts

    observed = json.loads(FIXTURE.read_text())['cohort']
    case = retained_case()
    _, baseline_mapping = mapping_for_case(case)
    baseline = compare_cohorts(case, baseline_mapping)
    # This exact population's mean calibrates effective service, not a peak
    # bandwidth or independent validation. Tensor and physical work stay fixed.
    effective_rate = observed['physical_work_per_instance']['mte3_bytes'] / (observed['duration_ns']['mean'] / 1e9)
    calibrated = deepcopy(case)
    calibrated['machine']['device'].setdefault('rates', {})['mte3'] = effective_rate
    _, mapping = mapping_for_case(calibrated)
    return observed, baseline, mapping, compare_cohorts(calibrated, mapping)


def test_observed_regime_rate_keeps_public_comparison_strict(fitted_copy):
    observed, baseline, mapping, result = fitted_copy
    row = result['windows'][0]['cohorts'][0]
    before = baseline['windows'][0]['cohorts'][0]
    assert row['status'] == before['status'] == 'compared'
    assert row['accuracy_pass'] is True
    assert row['prediction']['per_call_ms'] == pytest.approx(observed['duration_ns']['mean'] / 1e6)
    assert row['prediction']['per_call_ms'] != before['prediction']['per_call_ms']
    assert row['contract'] == before['contract']
    assert row['prediction']['physical_work_per_instance'] == before['prediction']['physical_work_per_instance']
    assert row['observed'] == before['observed']
    assert row['observed']['event_count'] == 12160


def test_fitted_rate_does_not_complete_a_partial_native_boundary(fitted_copy):
    from mindie_sim.cohort_comparison import _comparison

    observed, baseline, mapping, result = fitted_copy
    cohort = deepcopy(mapping['windows'][0]['cohorts'][0])
    cohort['contract_scope'] = {'prediction_coverage': {'kind': 'partial_program',
        'reason': 'observed_output_not_in_declared_resource_boundary'}}
    status, reason, _ = _comparison(cohort, result['windows'][0]['cohorts'][0]['prediction'])
    assert status == 'reference_only' and reason == 'observed_output_not_in_declared_resource_boundary'
