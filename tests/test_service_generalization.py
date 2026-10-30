"""Real source-excluded native populations exercise frozen physical functions."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from service_evidence import (
    evaluate_service_domains, fit_service_domains, freeze_service_specification,
    predict_service_domains, service_regimes,
    run_generalization,
)


@pytest.fixture
def retained():
    return json.loads((ROOT / 'tests/fixtures/retrospective_heldout/physical-domains.json').read_text())


def fit(retained):
    spec = freeze_service_specification(
        [p['source_sha256'] for p in retained['training_points']],
        [p['source_sha256'] for p in retained['evaluation_points']],
        retained['domains'], evaluation_relation='retrospective_leave_source_out')
    return spec, fit_service_domains(spec, retained['training_points'])


def test_retained_native_affine_fit_and_heldout_arithmetic(retained):
    _, model = fit(retained)
    for domain in model['models']:
        expected = retained['expected'][domain['domain']['id']]
        coefficients = domain['coefficients']
        assert coefficients['fixed_us'] == pytest.approx(expected['fixed_us'])
        assert coefficients['terms']['physical_axis'] == pytest.approx(expected['us_per_axis_unit'])
        assert coefficients['training_weighted_sse_us2'] == pytest.approx(expected['training_sse_us2'])
    result = evaluate_service_domains(model, retained['evaluation_points'])
    assert result['summary']['predicted'] == 4
    for actual, saved in zip(result['rows'], retained['evaluation_points']):
        assert actual['predicted_us'] == pytest.approx(saved['expected_predicted_us'])
        assert actual['observed']['count'] == saved['observation']['count']
        diff = actual['predicted_us'] - saved['observation']['mean_us']
        assert actual['activity_difference_ms_per_forward'] == pytest.approx(
            diff * saved['observation']['calls_per_forward'] / 1000)
        assert actual['passed'] == (abs(diff) <= 15 if saved['observation']['mean_us'] <= 50
                                   else abs(diff / saved['observation']['mean_us']) <= .15)
    assert not result['activity_differences_are_additive_body_wall_time']


def test_excluded_capture_timing_is_not_read_or_fit(retained):
    spec, clean = fit(retained)
    # Supplying the excluded source without even an observation is intentional:
    # the training loop must decide source membership before accessing timing.
    excluded = [{'source_sha256': p['source_sha256']} for p in retained['evaluation_points']]
    mixed = fit_service_domains(spec, [*retained['training_points'], *excluded])
    assert mixed['models'] == clean['models']
    assert mixed['excluded_timing_values_read'] == 0
    assert sum(mixed['excluded_source_populations'].values()) == 4


def test_physical_transfer_preserves_source_rank_precision_and_call_boundary(retained):
    _, model = fit(retained)
    target = deepcopy(retained['evaluation_points'][0])
    valid = predict_service_domains(model, target)
    assert valid['status'] == 'predicted'
    assert valid['extrapolated_coordinates'] == ['physical_axis']
    target['axes']['metadata.hccl_selection.ranks'] = 16
    assert predict_service_domains(model, target)['status'] == 'unresolved'
    target = deepcopy(retained['evaluation_points'][3])
    target['boundary']['precision'] = {'dtype': 'bf16'}
    assert predict_service_domains(model, target)['status'] == 'unresolved'
    target = deepcopy(retained['evaluation_points'][1])
    target['boundary']['execution_boundary'] = 'subkernel_only'
    assert predict_service_domains(model, target)['status'] == 'unresolved'
    output = service_regimes(model, retained['evaluation_points'])
    assert len(output['rules']) == 4
    for rule in output['rules']:
        domain = next(d for d in retained['domains'] if rule['id'] == 'frozen-' + d['id'])
        assert rule['match'] == domain['match']
        assert rule['coordinates'] == domain['coordinates']
        assert rule['provenance']['heldout_observed_values_used_in_fit'] is False
        assert 'fixed_us' in rule['response'] and len(rule['response']['terms']) == 1


def test_missing_training_population_and_ambiguous_boundaries_remain_unresolved(retained):
    spec, _ = fit(retained)
    first = retained['training_points'][0]
    incomplete = [p for p in retained['training_points'] if p is not first]
    model = fit_service_domains(spec, incomplete)
    target = retained['evaluation_points'][0]
    assert predict_service_domains(model, target)['status'] == 'unresolved'
    assert service_regimes(model, [target])['new_prediction_required'] is False
    # Two semantic names cannot price one and the same physical native call.
    duplicate = deepcopy(retained['domains'][0]); duplicate['id'] += '-second-label'
    spec = freeze_service_specification(spec['training_sources'], spec['evaluation_sources'],
        [retained['domains'][0], duplicate], evaluation_relation='retrospective_leave_source_out')
    points = [p for p in retained['training_points'] if p['domain_id'] == retained['domains'][0]['id']]
    aliases = [{**p, 'domain_id': duplicate['id']} for p in points]
    model = fit_service_domains(spec, [*points, *aliases])
    assert predict_service_domains(model, target)['reason'] == 'overlapping_frozen_domains'


def test_equivalent_physical_element_coordinate_and_complete_target_admission(retained):
    original = deepcopy(retained)
    domain_id = '-copy-conv-state-kernel-observed'
    data = deepcopy(retained)
    data['domains'] = [d for d in data['domains'] if d['id'] == domain_id]
    data['domains'][0]['coordinates']['physical_axis'] = {'path': 'local_shape', 'reduce': 'product'}
    for key in ('training_points', 'evaluation_points'):
        data[key] = [p for p in data[key] if p['domain_id'] == domain_id]
        for point in data[key]:
            axes = point['axes']
            axes['local_shape'] = [axes[f'local_shape.{i}'] for i in range(3)]
    _, per_row = fit(original)
    _, per_element = fit(data)
    predicted = predict_service_domains(per_element, data['evaluation_points'][0])
    row_prediction = predict_service_domains(per_row, original['evaluation_points'][1])
    assert predicted['predicted_us'] == pytest.approx(row_prediction['predicted_us'])
    # The source inventory also contains a differently bounded operation which
    # the same coarse recipe selector would hit. Export must not price it by
    # silently treating the first matched example as the entire population.
    other = deepcopy(data['evaluation_points'][0])
    other['boundary']['execution_boundary'] = 'subkernel_only'
    output = service_regimes(per_element, [*data['evaluation_points'], other])
    assert output['rules'] == []
    assert output['excluded_ambiguous_domains'] == [domain_id]


def test_canonical_registry_runs_source_excluded_native_validation(retained, tmp_path):
    spec, model = fit(retained)
    pins = []
    for key in ('training_points', 'evaluation_points'):
        path = tmp_path / (key + '.json')
        path.write_text(json.dumps({'points': retained[key]}))
        pins.append({'path': path.name, 'sha256': sha256(path.read_bytes()).hexdigest()})
    registry = {'cases': [{'source': {'sha256': value}} for value in
        spec['training_sources'] + spec['evaluation_sources']], 'generalization': [{
            'id': 'retained-real-native-populations', 'specification': spec,
            'training_observations': pins[0], 'evaluation_observations': pins[1]}]}
    result = run_generalization(registry, tmp_path)
    experiment = result['experiments'][0]
    assert experiment['frozen_model_sha256'] == model['sha256']
    assert experiment['evaluation'] == evaluate_service_domains(model, retained['evaluation_points'])
    assert result['summary']['predicted'] == 4
    assert result['new_Sim_predictions'] == 0
