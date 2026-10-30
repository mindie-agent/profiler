"""Pre-register, fit and evaluate retrospective concurrency-held-out services.

[Role] Fit physical response functions from training sources only, then prepare
  counterfactual Body inputs with all earlier point responses removed.
[Invariants] Split and function class precede held-out timing reads. No model
  choice from validation error. Historical source/hardware tuning is not blind.
[Timeouts & Locks] Bounded retained JSON and finite metadata graphs, no raw/cost.
[Side-Effect Policy] New evidence/cases only; existing scoreboard is unchanged.
"""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen_a3_service_cases import physical_ops, read, write, identity
from mindie_sim.prediction.service_regimes import axis_equal, lookup, MISSING

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'acceptance-20261030-heldout-generalization'
BASE = ROOT / 'acceptance-20261030-service-glm/metadata-pass/decode-forward-service-cases.json'
REV = '21c30821d87a757bace8cf6b2fffea2536db643e'
TRAIN = ['glm53flash-a5-tp8-c1', 'a5_glm53flash_tp8_c8_p4k', 'a5_glm53flash_tp8_c32_p4k']
EXCLUDED = ['SparseFlashMla', '_glm5_next_lightning_indexer_score_kernel', 'SparseFlashMlaMetadata']


def affine_nonnegative(points):
    """Exact two-parameter nonnegative least squares, equal weight per source."""
    xs, ys = zip(*points); n = len(xs); sx, sy = sum(xs), sum(ys)
    sxx = sum(x*x for x in xs); sxy = sum(x*y for x,y in points)
    determinant = n*sxx-sx*sx
    if determinant <= 0:
        raise ValueError('rank_deficient_fixed_plus_axis_design')
    candidates = [(max(0.0, sy/n), 0.0), (0.0, max(0.0, sxy/sxx)), (0.0, 0.0)]
    a, b = (sy*sxx-sx*sxy)/determinant, (n*sxy-sx*sy)/determinant
    if a >= 0 and b >= 0:
        candidates.append((a,b))
    fixed, slope = min(candidates, key=lambda v: sum((v[0]+v[1]*x-y)**2 for x,y in points))
    return {'fixed_us': fixed, 'us_per_axis_unit': slope, 'design_rank': 2,
            'training_sse_us2': sum((fixed+slope*x-y)**2 for x,y in points)}


def axes(case, op):
    value = {**op.to_dict(include_work=False), 'hardware': case.machine.hardware_key or case.machine.sku,
             'dtype': op.dtype or case.model.compute_dtype}
    value['kernel'] = dict(op.metadata).get('device_kernel_group', {}).get('kernel')
    return value


def targets(rule, case, ops):
    return [o for o in ops if (not dict(o.metadata).get('device_kernel_group') or
                dict(o.metadata)['device_kernel_group'].get('entry'))
            and all(axis_equal(lookup(axes(case,o), k), v) for k,v in rule['match'].items())]


def register():
    manifest = read(BASE)
    rows = manifest['cases']
    train = [r for r in rows if r['case_id'] in TRAIN]
    heldout = [r for r in rows if r['case_id'] not in TRAIN]
    train_shas = {r['source']['sha256'] for r in train}
    heldout_shas = {r['source']['sha256'] for r in heldout}
    if len(train) != 3 or train_shas & heldout_shas:
        raise ValueError('source_split_not_disjoint')
    result = {'schema_version': 'mindie-retrospective-heldout-policy/1',
        'evaluation_design': 'retrospective_leave_concurrency_out', 'baseline_manifest_identity': identity(BASE),
        'training': [{'case_id': r['case_id'], 'source_identity': r['source'],
                      'case_identity': identity(r['sim_case_path']), 'geometry': r['replay_input_pins']['primary_geometry']} for r in train],
        'heldout': [{'case_id': r['case_id'], 'source_identity': r['source'],
                    'case_identity': identity(r['sim_case_path']), 'geometry': r['replay_input_pins']['primary_geometry']} for r in heldout],
        'function_class': 'nonnegative fixed_us + nonnegative slope * one source physical coordinate',
        'fit_objective': 'unweighted least squares over complete native mean per training source',
        'domain_admission': 'only domains with complete native populations in all three training sources; others remain analytic',
        'function_selection': 'fixed before reading heldout native responses; no threshold/function/model search',
        'coordinate_policy': {'hcom_allReduce_AicpuKernel': 'metadata.hccl_selection.payload_bytes',
                              'HcPre': 'metadata.fusion_tensor_view.tokens', 'HcPost': 'metadata.fusion_tensor_view.tokens',
                              'otherwise': 'local_shape.0'},
        'excluded_native_domains': {n: 'training contexts do not independently identify context-dependent work' for n in EXCLUDED},
        'domain_policy': 'same hardware/recipe/dtype/layout/constant physical axes; scalar coordinate >= 0; extrapolation separately labelled',
        'all_previous_point_response_rules_removed': True,
        'body_claim': 'counterfactual Body replay with train-only response rules; not independently held-out full model',
        'historical_leakage_limit': 'Retained measurements were previously inspected and source/hardware programs may have been developed with them; operator fit exclusion is retrospective, not prospective blindness.',
        'prospective_inventory': {str(p): [c.name for c in p.iterdir()] for p in (
            Path('/Volumes/data/mindie-sim-data/a3/heldout_engine_20261030'),
            Path('/Volumes/data/mindie-sim-data/a5/heldout_engine_20261030'))},
        'runtime_source_commit': REV, 'producer_identity': identity(__file__)}
    write(OUT / 'split-policy.json', result)
    print(json.dumps({'training': len(train), 'heldout': len(heldout), 'policy': identity(OUT / 'split-policy.json')}))


def fit():
    policy = read(OUT / 'split-policy.json'); domains = {}
    for source in policy['training']:
        if identity(source['case_identity']['path']) != source['case_identity']:
            raise ValueError('training_case_changed')
        raw = read(source['case_identity']['path']); case, ops = physical_ops(raw, source['geometry'])
        for original in raw['runtime']['kernels']['service_regimes']:
            p = original['provenance']; native = p['native_operator_type']
            if native in EXCLUDED:
                continue
            selected = targets(original, case, ops)
            count = p.get('count'); F = p.get('body_count')
            if not selected or count != F * len(selected):
                raise ValueError('training_native_boundary_count_differs:' + original['id'])
            coordinate = policy['coordinate_policy'].get(native, 'local_shape.0')
            values = [lookup(axes(case,o), coordinate) for o in selected]
            if values[0] is MISSING or any(v != values[0] for v in values):
                raise ValueError('training_domain_has_heterogeneous_coordinate:' + original['id'])
            value = original['response']['fixed_us']
            if value != p['mean_us']:
                raise ValueError('training_value_not_complete_native_mean')
            domains.setdefault(original['id'], []).append({'case_id': source['case_id'],
                'source_identity': source['source_identity'], 'case_identity': source['case_identity'],
                'native_operator_type': native, 'coordinate_path': coordinate, 'coordinate': values[0],
                'observed_mean_us': value, 'observed_p50_us': p['p50_us'], 'native_count': count,
                'forward_count': F, 'native_calls_per_forward': len(selected), 'match': original['match'],
                'original_provenance': p, 'execution': original.get('execution')})
    models, exclusions = [], []
    for rule_id, rows in domains.items():
        if len(rows) != len(TRAIN) or {r['case_id'] for r in rows} != set(TRAIN):
            exclusions.append({'original_rule_id': rule_id, 'reason': 'complete_training_sources_missing',
                               'available_training_sources': [r['case_id'] for r in rows]})
            continue
        if len({r['coordinate_path'] for r in rows}) != 1:
            raise ValueError('coordinate_semantics_changed')
        common = {k: v for k,v in rows[0]['match'].items() if all(k in r['match'] and axis_equal(r['match'][k],v) for r in rows)}
        coefficients = affine_nonnegative([(r['coordinate'], r['observed_mean_us']) for r in rows])
        match = deepcopy(common)
        rule = {'id': 'loco-' + rule_id, 'match': match,
                'coordinates': {'physical_work_axis': {'path': rows[0]['coordinate_path']}},
                'domain': {'physical_work_axis': {'min': 0}},
                'response': {'fixed_us': coefficients['fixed_us'], 'terms': [{'coordinate': 'physical_work_axis', 'us_per_unit': coefficients['us_per_axis_unit']}]},
                'provenance': {'calibration_origin': 'observed', 'evaluation_relation': 'retrospective_leave_concurrency_out',
                    'training_source_identities': [r['source_identity'] for r in rows],
                    'split_policy_identity': identity(OUT / 'split-policy.json'),
                    'native_operator_type': rows[0]['native_operator_type'],
                    'body_residual_used': False, 'heldout_observed_values_used_in_fit': False,
                    'historical_source_model_blindness_claimed': False}}
        if rows[0]['execution'] is not None:
            if any(r['execution'] != rows[0]['execution'] for r in rows):
                raise ValueError('training_execution_domain_differs')
            rule['execution'] = rows[0]['execution']
        models.append({'original_rule_id': rule_id, 'rule': rule, 'training_rows': rows,
                       'coefficients': coefficients, 'coordinate_range': [min(r['coordinate'] for r in rows),max(r['coordinate'] for r in rows)],
                       'variable_match_fields_removed': sorted(set(rows[0]['match']) - set(match))})
    write(OUT / 'training-models.json', {'schema_version': 'mindie-heldout-service-models/1',
        'split_policy_identity': identity(OUT / 'split-policy.json'), 'models': models, 'exclusions': exclusions,
        'heldout_value_reads_during_fit': 0, 'new_raw_scans': 0, 'new_cost_predictions': 0})
    print(json.dumps({'models': len(models), 'training_model_identity': identity(OUT / 'training-models.json')}))


def evaluate_and_build():
    policy = read(OUT / 'split-policy.json'); trained = read(OUT / 'training-models.json')
    model_pin = identity(OUT / 'training-models.json'); models = trained['models']
    manifest = read(BASE); results = []; removed = []
    heldout_ids = {r['case_id'] for r in policy['heldout']}
    for row in manifest['cases']:
        if row['case_id'] not in heldout_ids:
            continue
        prior = identity(row['sim_case_path']); raw = read(prior['path']); geo = row['replay_input_pins']['primary_geometry']
        case, ops = physical_ops(raw, geo); old = {r['id']:r for r in raw['runtime']['kernels']['service_regimes']}
        newrules = []
        for model in models:
            rule = deepcopy(model['rule']); original = old[model['original_rule_id']]
            expected = targets(original, case, ops); fresh = targets(rule, case, ops)
            if {o.op_id for o in expected} != {o.op_id for o in fresh}:
                raise ValueError('learned_match_broadens_source_native_boundary:' + rule['id'])
            values = [lookup(axes(case,o), model['training_rows'][0]['coordinate_path']) for o in fresh]
            if not values or any(v != values[0] for v in values):
                raise ValueError('heldout_native_axis_not_homogeneous')
            prov = original['provenance']; count = prov['count']; F = prov['body_count']
            if count != F * len(fresh):
                raise ValueError('heldout_whole_native_multiplicity_differs')
            x = values[0]; observed = prov['mean_us']; coef = model['coefficients']
            predicted = coef['fixed_us'] + coef['us_per_axis_unit'] * x
            error = predicted - observed
            passed = abs(error) <= 15 if observed <= 50 else abs(error/observed) <= .15
            results.append({'case_id': row['case_id'], 'source_identity': row['source'], 'case_identity': prior,
                'training_model_identity': model_pin, 'rule_id': rule['id'],
                'native_operator_type': prov['native_operator_type'], 'coordinate': x,
                'training_coordinate_range': model['coordinate_range'],
                'extrapolation': not model['coordinate_range'][0] <= x <= model['coordinate_range'][1],
                'observed_mean_us': observed, 'observed_p50_us': prov['p50_us'],
                'predicted_response_us': predicted, 'per_call_difference_us': error,
                'relative_error': error/observed, 'passed': passed,
                'tier': 'micro_15us' if observed <= 50 else 'heavy_15pct',
                'count': count, 'forward_count': F, 'native_calls_per_forward': len(fresh),
                'complete_native_provenance': prov,
                'accuracy_scope': 'train-source-excluded native response function, not actual Engine service or full-model blindness'})
            rule['provenance']['training_model_identity'] = model_pin
            newrules.append(rule)
        removed.append({'case_id': row['case_id'], 'prior_case_identity': prior, 'removed_rule_ids': sorted(old),
                        'replacement_rules': [r['id'] for r in newrules], 'heldout_point_rules_retained': 0})
        raw['runtime']['kernels']['service_regimes'] = newrules
        cal = {'evaluation_relation': 'retrospective_leave_concurrency_out', 'training_model_identity': model_pin,
               'split_policy_identity': identity(OUT / 'split-policy.json'), 'all_prior_point_responses_removed': True,
               'scope': 'operator-only heldout; Body counterfactual with historically developed source/hardware inputs',
               'baseline_case_identity': prior, 'body_residual_used': False}
        raw['runtime'].setdefault('metadata', {}).update(calibration_origin='observed', calibration_evidence=cal)
        path = OUT / 'cases' / (row['case_id'] + '-loco.json'); write(path, raw)
        row.update(sim_case_path=str(path), model_declaration=identity(path), calibration_origin='observed',
                   calibration_evidence=cal, variant_id='glm-a5-retrospective-loco-' + REV[:8])
        row['replay_input_pins']['case'] = identity(path)
    manifest['cases'] = [r for r in manifest['cases'] if r['case_id'] in heldout_ids]
    manifest.update(runtime_source_commit=REV, variant_id='glm-a5-retrospective-loco-' + REV[:8])
    write(OUT / 'decode-forward-heldout-cases.json', manifest)
    write(OUT / 'operator-heldout-evaluation.json', {'schema_version': 'mindie-operator-heldout-evaluation/1',
        'training_model_identity': model_pin, 'split_policy_identity': identity(OUT / 'split-policy.json'),
        'rows': results, 'point_response_removal': removed, 'summary': {'groups': len(results),
        'passed': sum(r['passed'] for r in results), 'sources': len(heldout_ids)},
        'new_raw_scans': 0, 'new_cost_predictions': 0})
    print(json.dumps({'heldout_sources': len(heldout_ids), 'groups': len(results), 'passed': sum(r['passed'] for r in results)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('stage', choices=['register', 'fit', 'evaluate'])
    {'register': register, 'fit': fit, 'evaluate': evaluate_and_build}[parser.parse_args().stage]()
