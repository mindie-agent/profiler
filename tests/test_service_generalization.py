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


def test_client_only_native_generalization_keeps_gap_without_fabricated_scores(tmp_path):
    from engine import identity
    from pipeline import run

    path = ROOT/'tests/fixtures/engine_boundaries/client_only/kimi-tp8-sweep-c2-p4k.json'
    captured = json.loads(path.read_text())
    entry = {'id': 'kimi-tp8-native-coverage', 'status': 'planned',
        'reason': 'device_capture_missing',
        'coverage': {'client_runs': 1, 'client_requests': len(captured['requests']),
            'successful_requests': captured['summary']['n_ok'], 'decode_device_captures': 0,
            'native_populations': None, 'body_accuracy_available': False},
        'limits': ['Client TPOT does not substitute for native latency.']}
    registry = {'schema_version': 'mindie-cases/1',
        'cases': [{'source': identity(path)}], 'generalization': [entry]}
    source = tmp_path/'cases.json'
    source.write_text(json.dumps(registry))
    output = tmp_path/'generalization.json'
    report = run(source, output=output, archive_root=tmp_path/'archive', scope='generalization')
    card = report['cases'][0]
    assert card['coverage'] == entry['coverage']
    assert card['comparison'] == {'status': 'planned'}
    assert card['fitted_domains'] is None
    assert card['population_coverage'] is None
    assert report['summary']['completed'] == 0
    assert report['summary']['planned'] == 1
    assert report['new_Sim_predictions'] == 0
    # The rendered card keeps the missing denominator rather than 0/0 accuracy.
    assert '| — / — / — |' in output.with_suffix('.md').read_text()
    assert 'device_capture_missing' in output.with_suffix('.md').read_text()


def test_real_kda_abi_guards_do_not_become_constant_fit_columns():
    from types import SimpleNamespace
    from mindie_sim.prediction.service_regimes import RegimePolicy

    retained = json.loads((ROOT/'tests/fixtures/retrospective_heldout/glm-kda-guard-populations.json').read_text())
    points = retained['points']
    train, evaluation = points[:-1], points[-1:]
    domain = deepcopy(retained['domain'])
    original_spec = freeze_service_specification(
        [p['source_sha256'] for p in train], [p['source_sha256'] for p in evaluation],
        [domain], evaluation_relation='retrospective_source_exclusion')
    baseline = fit_service_domains(original_spec, train)
    domain['guard_coordinates'] = {
        'query_min': {'path': 'metadata.sequence_tokens', 'reduce': 'min'},
        'query_max': {'path': 'metadata.sequence_tokens', 'reduce': 'max'}}
    domain['guard_bounds'] = {name: {'min': 4, 'max': 4} for name in domain['guard_coordinates']}
    domain['match'].update({'dtype': 'bf16', 'layout': 'TND',
        'metadata.kda_recurrent_params.gate_dtype': 'bf16',
        'metadata.kda_recurrent_params.use_beta_sigmoid': True})
    spec = freeze_service_specification(original_spec['training_sources'], original_spec['evaluation_sources'],
        [domain], evaluation_relation=original_spec['evaluation_relation'])
    guarded = fit_service_domains(spec, train)
    assert guarded['models'][0]['status'] == 'fitted'
    assert guarded['models'][0]['coefficients'] == baseline['models'][0]['coefficients']
    assert evaluate_service_domains(guarded, evaluation)['rows'][0]['predicted_us'] == pytest.approx(
        predict_service_domains(baseline, evaluation[0])['predicted_us'])
    excluded = deepcopy(train[0])
    excluded['axes']['metadata']['sequence_tokens'] = [1] * len(excluded['axes']['metadata']['sequence_tokens'])
    del excluded['observation']  # ABI exclusion occurs before accessing timing.
    checked = fit_service_domains(spec, [excluded, *train[1:]])
    assert checked['rejected_training_populations'][0]['reason'] == 'physical_guard_differs'
    mismatches = []
    for mutation in ('q1', 'mixed_q5', 'dtype', 'sigmoid'):
        point = deepcopy(evaluation[0])
        if mutation == 'q1': point['axes']['metadata']['sequence_tokens'] = [1] * len(point['axes']['metadata']['sequence_tokens'])
        elif mutation == 'mixed_q5': point['axes']['metadata']['sequence_tokens'][0] = 5
        elif mutation == 'dtype': point['axes']['dtype'] = 'fp16'
        else: point['axes']['metadata']['kda_recurrent_params']['use_beta_sigmoid'] = False
        assert predict_service_domains(guarded, point)['status'] == 'unresolved'
        assert evaluate_service_domains(guarded, [point])['summary']['predicted'] == 0
        mismatches.append(point)
    exported = service_regimes(guarded, [*evaluation, *mismatches])
    assert exported['excluded_ambiguous_domains'] == []
    rule, = exported['rules']
    assert rule['domain']['query_min'] == rule['domain']['query_max'] == {'min': 4, 'max': 4}
    assert [term['coordinate'] for term in rule['response']['terms']] == ['batch']
    policy = RegimePolicy([rule])
    # Exercise the installed Engine selector with real retained physical axes;
    # no operator program, simulation or synthetic latency is executed.
    for point in [*evaluation, *mismatches]:
        axes = point['axes']
        context = SimpleNamespace(service_boundary='device_kernel',
            op=SimpleNamespace(**{k: axes[k] for k in ('recipe','family','phase','local_shape',
                'semantic_shape','padded_shape','launch_shape','metadata')}),
            service_identity={'hardware': {'key': axes['hardware']}, 'dtype': axes['dtype'], 'layout': axes['layout']},
            native_work={}, resource_units={}, core_count=48)
        result = policy.resolve(context, lambda *args, **kwargs: None)
        if point is evaluation[0]:
            assert result.duration_ms * 1000 == pytest.approx(predict_service_domains(guarded, point)['predicted_us'])
        else:
            assert result is None


def test_kimi_whole_concurrency_exclusion_preserves_real_mc2_discontinuity(tmp_path):
    retained = json.loads((ROOT / 'tests/fixtures/retrospective_heldout/kimi-concurrency.json').read_text())
    pins = []
    for bundle in retained['observations']:
        path = tmp_path / (bundle['source_sha256'] + '.json')
        path.write_text(json.dumps(bundle))
        pins.append({'source_sha256': bundle['source_sha256'], 'path': str(path),
                     'sha256': sha256(path.read_bytes()).hexdigest()})
    entry = {'id': 'kimi-a5-retrospective-concurrency-exclusion',
             'domains': retained['domains'], 'source_groups': retained['source_groups'],
             'observations': pins}
    registry = {'cases': [{'source': {'sha256': p['source_sha256']}} for p in pins],
                'generalization': [entry]}
    result = run_generalization(registry, tmp_path)['experiments'][0]
    assert len(result['folds']) == 6
    assert len(result['evaluation']['rows']) == 12
    for fold in result['folds']:
        spec = fold['model']['specification']
        expected = next(g['source_sha256'] for g in retained['source_groups']
                        if g['concurrency'] == fold['heldout_concurrency'])
        assert set(spec['evaluation_sources']) == set(expected)
        assert len(expected) == 2  # p4k and p16k leave training together.
        assert not set(expected) & set(spec['training_sources'])
    fold = next(f for f in result['folds'] if f['heldout_concurrency'] == 2)
    evaluated = [r for r in result['evaluation']['rows'] if r['heldout_concurrency'] == 2]
    assert [r['predicted_us'] for r in evaluated] == pytest.approx([14.512982165622185] * 2)
    assert all(r['passed'] is False and r['observed']['mean_us'] > 34 for r in evaluated)
    # The highest concurrency has only two distinct input-row sizes left in
    # training. This API retains the unresolved domain instead of inventing a fit.
    assert all(r['status'] == 'unresolved' for r in result['evaluation']['rows']
               if r['heldout_concurrency'] == 32)
    for pin in pins:
        if pin['source_sha256'] not in fold['model']['specification']['evaluation_sources']:
            continue
        path = Path(pin['path']); bundle = json.loads(path.read_text())
        for point in bundle['points']:
            point['observation']['mean_us'] *= 10
        path.write_text(json.dumps(bundle)); pin['sha256'] = sha256(path.read_bytes()).hexdigest()
    changed = run_generalization(registry, tmp_path)['experiments'][0]
    changed_fold = next(f for f in changed['folds'] if f['heldout_concurrency'] == 2)
    assert changed_fold['model']['sha256'] == fold['model']['sha256']
