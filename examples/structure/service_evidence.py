"""Retain executed observable-service evidence in compact operator reports.

[Role] Project Engine service evidence and freeze physical response functions.
[Invariants] Execution evidence never changes tensor admission or predictions.
  Serviced work is an Engine counter only when supplied by the cost result;
  response parameters and analytical reference work are labeled separately.
  Response fitting admits complete native observations from training sources
  only. Precision/source/boundary domains remain fixed; no Body residual fit.
[Timeouts & Locks] Bounded parameter metadata, no subprocesses or locks.
[Side-Effect Policy] Pure projection; no measurements, simulation or writes.
"""
from hashlib import sha256
from collections import Counter, defaultdict
from copy import deepcopy
from itertools import combinations
import json
import math
from pathlib import Path


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             allow_nan=False).encode()).hexdigest()


def service_execution_evidence(parameters, *, serviced=None):
    """Keep actual rule queries and their case-reconstructable declaration hash."""
    records = []
    for record in parameters.get("service_regimes", ()):
        declaration = {key: value for key, value in record.items()
                       if key not in {"model_id", "queries", "response_us_min", "response_us_max"}}
        provenance = record.get("provenance", {})
        records.append({
            "id": record["id"], "declaration_sha256": _digest(declaration),
            "provenance_sha256": _digest(provenance),
            "match": record.get("match", {}), "execution": record.get("execution"),
            "response": record.get("response"), "queries": dict(record.get("queries", {})),
            "response_us_min": record.get("response_us_min"),
            "response_us_max": record.get("response_us_max"),
            "calibration_origin": provenance.get("calibration_origin", "not_declared"),
            "evaluation_relation": provenance.get("evaluation_relation", "not_declared"),
            "body_residual_used": provenance.get("body_residual_used"),
        })
    return {
        "schema_version": "mindie-operator-service-execution/1",
        "basis": "executed_Sim_Engine_cost_parameters",
        "strict_admission_changed": False,
        "operator_occurrences": parameters.get("operator_occurrences"),
        "work_basis": parameters.get("work_basis"),
        "regime_selection": parameters.get("regime_selection"),
        "rules": records,
        "joint_native_services": parameters.get("joint_native_services", []),
        "serviced_resources": None if serviced is None else dict(serviced),
        "serviced_resources_basis": "not_retained" if serviced is None else "Engine_serviced_work_counter",
        "analytical_reference_work_executes_alongside_joint_service": False,
    }


def freeze_service_specification(training_sources, evaluation_sources, domains, *,
                                 evaluation_relation, minimum_training_sources=3):
    """Freeze source membership and physical function classes without reading timing.

    A domain has a fixed ``match``, a typed native ``boundary``, and named Sim
    ``coordinates`` (path/reduce/scale). Only declared coordinates vary; this
    function never drops differing precision, source, layout or rank selectors.
    Local M/N/K or their product can therefore vary across TP, while a collective
    keeps its own rank/topology/algorithm domain. Population multiplicity is not
    a latency coordinate: layers/calls are used only when reporting activity.
    """
    train, evaluation = sorted(set(training_sources)), sorted(set(evaluation_sources))
    if not train or set(train) & set(evaluation):
        raise ValueError('training_and_evaluation_sources_must_be_disjoint')
    prepared = deepcopy(list(domains))
    if len({d['id'] for d in prepared}) != len(prepared):
        raise ValueError('duplicate_service_domain')
    for domain in prepared:
        boundary = domain['boundary']
        for key in ('native_operator_type', 'source_implementation', 'precision',
                    'layout', 'execution_boundary'):
            if not boundary.get(key):
                raise ValueError('native_domain_missing:' + key)
        if not domain['match'].get('hardware') or not domain['coordinates']:
            raise ValueError('physical_hardware_and_coordinates_required')
        if len(domain['coordinates']) > 4:
            raise ValueError('physical_function_has_more_than_four_coordinates')
        forbidden = {'op_id', 'node_id', 'case_id', 'model_name', 'model_id', 'layer_id'}
        if forbidden & set(domain['match']):
            raise ValueError('service_domain_requires_physical_not_case_identity')
        for coordinate in domain['coordinates'].values():
            if coordinate['path'].split('.')[0] in forbidden | {'body', 'observed', 'timing'}:
                raise ValueError('service_coordinate_must_be_physical')
    result = {'schema_version': 'mindie-service-specification/1',
              'training_sources': train, 'evaluation_sources': evaluation,
              'evaluation_relation': evaluation_relation, 'domains': prepared,
              'minimum_training_sources': minimum_training_sources,
              'function_class': 'nonnegative_affine_physical_coordinates',
              'fit_objective': 'equal_source_weight_complete_native_call_mean',
              'heldout_timing_used_to_select_function': False,
              'body_residual_used': False}
    return {**result, 'sha256': _digest(result)}


def _verified(value):
    if value['sha256'] != _digest({k: v for k, v in value.items() if k != 'sha256'}):
        raise ValueError('frozen_service_identity_changed')


def _lookup(axes, path):
    if path in axes:
        return axes[path]
    value = axes
    for component in path.split('.'):
        if isinstance(value, dict):
            value = value[component]
        else:
            value = value[int(component)]
    return value


def _coordinate(axes, declaration):
    value = _lookup(axes, declaration['path'])
    reduction = declaration.get('reduce')
    if reduction:
        functions = {'sum': sum, 'product': math.prod, 'min': min, 'max': max,
                     'len': len, 'positive_count': lambda seq: sum(x > 0 for x in seq)}
        value = functions[reduction](value)
    value = float(value) * declaration.get('scale', 1)
    if not math.isfinite(value) or value < 0:
        raise ValueError('physical_coordinate_not_finite_nonnegative')
    return value


def _admit(domain, point):
    if point['boundary'] != domain['boundary']:
        return None, 'native_precision_source_or_execution_boundary_differs'
    try:
        if any(_digest(_lookup(point['axes'], path)) != _digest(value)
               for path, value in domain['match'].items()):
            return None, 'physical_domain_differs'
        return {name: _coordinate(point['axes'], declaration)
                for name, declaration in domain['coordinates'].items()}, None
    except (KeyError, IndexError):
        return None, 'physical_axis_not_available'


def _matches(domain, target):
    try:
        return all(_digest(_lookup(target['axes'], path)) == _digest(value)
                   for path, value in domain['match'].items())
    except (KeyError, IndexError):
        return False


def _population(point):
    observation = point['observation']
    if (observation['basis'] != 'complete_native_call_population'
            or observation['count'] <= 0
            or observation['count'] != observation['forward_count'] * observation['calls_per_forward']):
        raise ValueError('service_fit_requires_complete_native_population')
    mean = float(observation['mean_us'])
    if not math.isfinite(mean) or mean <= 0:
        raise ValueError('native_mean_must_be_positive')
    if not point['evidence_identity']['sha256']:
        raise ValueError('native_observation_evidence_required')
    return observation


def _linear_solve(matrix, values):
    """Small scaled normal equations; singular active sets are not identifiable."""
    rows = [list(row) + [value] for row, value in zip(matrix, values)]
    for index in range(len(rows)):
        pivot = max(range(index, len(rows)), key=lambda j: abs(rows[j][index]))
        if abs(rows[pivot][index]) <= 1e-12:
            return None
        rows[index], rows[pivot] = rows[pivot], rows[index]
        factor = rows[index][index]
        rows[index] = [v / factor for v in rows[index]]
        for j in range(len(rows)):
            if j != index:
                factor = rows[j][index]
                rows[j] = [v - factor * x for v, x in zip(rows[j], rows[index])]
    return [row[-1] for row in rows]


def _fit_nonnegative(rows, names):
    scales = [max(r['coordinates'][name] for r in rows) or 1.0 for name in names]
    design = [[1.0, *(r['coordinates'][name] / scale for name, scale in zip(names, scales))]
              for r in rows]
    per_source = Counter(r['source_sha256'] for r in rows)
    weights = [1 / per_source[r['source_sha256']] for r in rows]
    values = [r['mean_us'] for r in rows]
    size = len(names) + 1
    gram = [[sum(w * x[i] * x[j] for w, x in zip(weights, design))
             for j in range(size)] for i in range(size)]
    rhs = [sum(w * x[i] * y for w, x, y in zip(weights, design, values)) for i in range(size)]
    if _linear_solve(gram, rhs) is None:
        return None
    candidates = [[0.0] * size]
    for count in range(1, size + 1):
        for indices in combinations(range(size), count):
            beta = _linear_solve([[gram[i][j] for j in indices] for i in indices],
                                 [rhs[i] for i in indices])
            if beta is not None and all(v >= -1e-10 for v in beta):
                candidate = [0.0] * size
                for index, value in zip(indices, beta):
                    candidate[index] = max(0.0, value)
                candidates.append(candidate)
    def loss(beta):
        return sum(w * (sum(b * v for b, v in zip(beta, x)) - y) ** 2
                   for w, x, y in zip(weights, design, values))
    best = min(candidates, key=loss)
    return {'fixed_us': best[0],
            'terms': {name: best[i + 1] / scales[i] for i, name in enumerate(names)},
            'training_weighted_sse_us2': loss(best), 'design_rank': size}


def fit_service_domains(specification, points):
    """Fit training-only complete observations; excluded timing is never accessed.

    ``points`` may be streamed. The compact active state is native population
    means/physical coordinates, not kernel rows or historical prediction traces.
    A source contributes equal total weight even if it has several populations.
    """
    _verified(specification)
    domains = {d['id']: d for d in specification['domains']}
    train = set(specification['training_sources'])
    rows, rejected, skipped, seen = defaultdict(list), [], Counter(), set()
    for point in points:
        source = point['source_sha256']
        if source not in train:
            skipped[source] += 1
            continue
        domain_id = point['domain_id']
        key = source, domain_id, point['population_id']
        if key in seen:
            raise ValueError('duplicate_training_native_population')
        seen.add(key)
        if domain_id not in domains:
            rejected.append({'source_sha256': source, 'domain_id': domain_id, 'reason': 'domain_not_registered'})
            continue
        coordinates, reason = _admit(domains[domain_id], point)
        if reason:
            rejected.append({'source_sha256': source, 'domain_id': domain_id, 'reason': reason})
            continue
        observed = _population(point)
        rows[domain_id].append({'source_sha256': source, 'population_id': point['population_id'],
            'coordinates': coordinates, 'mean_us': observed['mean_us'],
            'p50_us': observed.get('p50_us'), 'count': observed['count'],
            'forward_count': observed['forward_count'], 'calls_per_forward': observed['calls_per_forward'],
            'evidence_identity': point['evidence_identity'], 'input_sha256': _digest(point)})
    models = []
    for domain_id, domain in domains.items():
        selected = rows[domain_id]
        sources = sorted({r['source_sha256'] for r in selected})
        reason = None
        if len(sources) < specification['minimum_training_sources']:
            reason = 'insufficient_independent_training_sources'
        elif len({tuple(r['coordinates'].values()) for r in selected}) < len(domain['coordinates']) + 2:
            reason = 'insufficient_independent_physical_points'
        coefficients = None if reason else _fit_nonnegative(selected, list(domain['coordinates']))
        if not reason and coefficients is None:
            reason = 'physical_coordinates_not_independently_identified'
        models.append({'domain': domain, 'status': 'unresolved' if reason else 'fitted',
            'reason': reason, 'coefficients': coefficients, 'training_sources': sources,
            'training_coordinate_ranges': {name: [min(r['coordinates'][name] for r in selected),
                max(r['coordinates'][name] for r in selected)] for name in domain['coordinates']} if selected else {},
            'training_populations': selected})
    result = {'schema_version': 'mindie-frozen-service-models/1', 'specification': specification,
              'models': models, 'rejected_training_populations': rejected,
              'excluded_source_populations': dict(skipped),
              'excluded_timing_values_read': 0, 'body_residual_used': False}
    return {**result, 'sha256': _digest(result)}


def predict_service_domains(frozen, target):
    """Predict per-call service from physical axes; no target timing is consulted."""
    _verified(frozen)
    candidates = []
    for model in frozen['models']:
        if model['status'] != 'fitted':
            continue
        values, reason = _admit(model['domain'], target)
        if reason:
            continue
        coefficients = model['coefficients']
        candidates.append({'status': 'predicted', 'domain_id': model['domain']['id'],
            'predicted_us': coefficients['fixed_us'] + sum(coefficients['terms'][k] * x for k, x in values.items()),
            'coordinates': values, 'extrapolated_coordinates': [k for k, x in values.items()
                if not model['training_coordinate_ranges'][k][0] <= x <= model['training_coordinate_ranges'][k][1]],
            'frozen_model_sha256': frozen['sha256']})
    if len(candidates) != 1:
        return {'status': 'unresolved', 'reason': 'no_eligible_frozen_domain' if not candidates else
                'overlapping_frozen_domains', 'matching_domain_ids': [c['domain_id'] for c in candidates],
                'predicted_us': None, 'frozen_model_sha256': frozen['sha256']}
    return candidates[0]


def evaluate_service_domains(frozen, points):
    """Evaluate a frozen native-response model; activity differences are not wall attribution."""
    _verified(frozen)
    evaluation = set(frozen['specification']['evaluation_sources'])
    rows, seen = [], set()
    for point in points:
        if point['source_sha256'] not in evaluation:
            raise ValueError('evaluation_source_not_in_frozen_holdout_split')
        key = point['source_sha256'], point['domain_id'], point['population_id']
        if key in seen:
            raise ValueError('duplicate_evaluation_native_population')
        seen.add(key)
        prediction = predict_service_domains(frozen, point)
        observed = _population(point)
        row = {'source_sha256': point['source_sha256'], 'population_id': point['population_id'],
               'requested_domain_id': point['domain_id'],
               'native_operator_type': point['boundary']['native_operator_type'],
               **prediction, 'observed': observed, 'evidence_identity': point['evidence_identity'],
               'passed': None, 'evaluation_relation': frozen['specification']['evaluation_relation']}
        if prediction['status'] == 'predicted':
            difference = prediction['predicted_us'] - observed['mean_us']
            row.update(per_call_difference_us=difference, relative_error=difference / observed['mean_us'],
                tier='micro_15us' if observed['mean_us'] <= 50 else 'heavy_15pct',
                passed=abs(difference) <= 15 if observed['mean_us'] <= 50 else abs(difference / observed['mean_us']) <= .15,
                activity_difference_ms_per_forward=difference * observed['calls_per_forward'] / 1000)
        rows.append(row)
    return {'schema_version': 'mindie-service-generalization/1', 'frozen_model_sha256': frozen['sha256'],
            'rows': rows, 'summary': {'populations': len(rows),
                'predicted': sum(r['status'] == 'predicted' for r in rows),
                'passed': sum(r['passed'] is True for r in rows)},
            'activity_differences_are_additive_body_wall_time': False,
            'heldout_timing_used_to_refit': False}


def _runtime_coordinates(domain, targets):
    """Translate normalized work quantities into Engine resource-role axes.

    OpSpec/primitive inventories name FLOPs and bytes; RegimePolicy receives
    CostModel's native work (cube/hbm). The amounts and fitted coefficients stay
    unchanged. Additional resource work would break this equivalence.
    """
    aliases = {'work.flops': ('work.cube', 'cube'),
               'work.hbm_bytes': ('work.hbm', 'hbm')}
    coordinates = deepcopy(domain['coordinates'])
    projection = {}
    for coordinate in coordinates.values():
        source = coordinate['path']
        if source not in aliases:
            continue
        destination, role = aliases[source]
        for target in targets:
            if _matches(domain, target):
                extra = target['axes'].get('work', {}).get('resource_work', {})
                if extra.get(role, 0):
                    raise ValueError('normalized_work_differs_from_engine_resource:' + role)
        coordinate['path'] = destination
        projection[source] = destination
    return coordinates, projection


def service_regimes(frozen, targets):
    """Export applicable Sim rules after fresh physical/native boundary admission.

    ``targets`` is the complete fresh native/program inventory of the target
    case, not a few matched examples. A broad matcher that also selects a
    different native boundary or ambiguous domain is not exported.
    Replace old per-capture point rules with these rules when constructing a
    transfer case. Empty output means no new prediction arm; it is not zero cost.
    Runtime execution still records actual hits/misses through the public
    ``service_execution_evidence`` projection above.
    """
    targets = list(targets)
    assignments = []
    for target in targets:
        if target['source_sha256'] not in frozen['specification']['evaluation_sources']:
            raise ValueError('transfer_target_not_in_frozen_holdout_split')
        assignments.append(predict_service_domains(frozen, target))
    selected = {r['domain_id'] for r in assignments if r['status'] == 'predicted'}
    blocked = {model['domain']['id'] for model in frozen['models']
        if model['domain']['id'] in selected
        and any(_matches(model['domain'], target) and
                (assignment['status'] != 'predicted' or assignment['domain_id'] != model['domain']['id'])
                for target, assignment in zip(targets, assignments))}
    for assignment in assignments:
        if assignment.get('domain_id') in blocked:
            assignment.update(status='unresolved', reason='matcher_broadens_fresh_native_boundary', predicted_us=None)
    selected -= blocked
    rules = []
    for model in frozen['models']:
        domain = model['domain']
        if domain['id'] not in selected:
            continue
        coefficients = model['coefficients']
        coordinates, projection = _runtime_coordinates(domain, targets)
        rule = {'id': 'frozen-' + domain['id'], 'match': deepcopy(domain['match']),
                'coordinates': coordinates,
                'domain': {name: {'min': 0} for name in domain['coordinates']},
                'response': {'fixed_us': coefficients['fixed_us'], 'terms': [
                    {'coordinate': name, 'us_per_unit': value} for name, value in coefficients['terms'].items()]},
                'provenance': {'calibration_origin': 'observed',
                    'evaluation_relation': frozen['specification']['evaluation_relation'],
                    'training_source_sha256': model['training_sources'],
                    'frozen_model_sha256': frozen['sha256'], 'specification_sha256': frozen['specification']['sha256'],
                    'native_boundary': deepcopy(domain['boundary']), 'body_residual_used': False,
                    'heldout_observed_values_used_in_fit': False}}
        if projection:
            rule['provenance']['coordinate_projection'] = projection
        if domain.get('execution') is not None:
            rule['execution'] = deepcopy(domain['execution'])
        rules.append(rule)
    return {'rules': rules, 'assignments': assignments, 'excluded_ambiguous_domains': sorted(blocked),
            'status': 'ready' if rules else 'no_eligible_frozen_domains',
            'new_prediction_required': bool(rules)}


def _read_observation_pin(pin, base):
    path = Path(pin['path'])
    if not path.is_absolute():
        path = Path(base) / path
    if path.stat().st_size > 50_000_000:
        raise ValueError('service_population_metadata_requires_streaming')
    data = path.read_bytes()
    if sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('service_population_evidence_changed')
    return json.loads(data)


def run_concurrency_exclusion(entry, base):
    """Leave a whole concurrency group out, including every retained context.

    Each source belongs to exactly one group and is evaluated once. Function
    classes and native domains are supplied before fitting; fold membership
    cannot depend on the observed error. This is retrospective validation.
    """
    groups = entry['source_groups']
    membership = {}
    for group in groups:
        for source in group['source_sha256']:
            if source in membership:
                raise ValueError('source_occurs_in_multiple_concurrency_groups')
            membership[source] = group['concurrency']
    pins = {pin['source_sha256']: pin for pin in entry['observations']}
    if len(pins) != len(entry['observations']) or set(pins) != set(membership):
        raise ValueError('concurrency_population_pins_do_not_match_split')
    if len({g['concurrency'] for g in groups}) != len(groups):
        raise ValueError('same_concurrency_must_be_one_exclusion_group')

    def read_sources(sources):
        for source in sorted(sources):
            bundle = _read_observation_pin(pins[source], base)
            if (bundle['source_sha256'] != source
                    or bundle['concurrency'] != membership[source]
                    or any(p['source_sha256'] != source for p in bundle['points'])):
                raise ValueError('concurrency_observation_source_or_group_mismatch')
            yield from bundle['points']

    folds, rows = [], []
    for group in groups:
        evaluation = set(group['source_sha256'])
        specification = freeze_service_specification(
            set(membership) - evaluation, evaluation, entry['domains'],
            evaluation_relation='retrospective_leave_concurrency_out',
            minimum_training_sources=entry.get('minimum_training_sources', 3))
        model = fit_service_domains(specification, read_sources(specification['training_sources']))
        result = evaluate_service_domains(model, read_sources(evaluation))
        for row in result['rows']:
            row['heldout_concurrency'] = group['concurrency']
        rows.extend(result['rows'])
        folds.append({'heldout_concurrency': group['concurrency'], 'model': model,
                      'evaluation_summary': result['summary'],
                      'training_frozen_before_evaluation_read': True})
    native_summary = defaultdict(Counter)
    for row in rows:
        counts = native_summary[row['native_operator_type']]
        counts['populations'] += 1
        counts['predicted'] += row['status'] == 'predicted'
        counts['passed'] += row['passed'] is True
        counts['observed_calls'] += row['observed']['count']
    return {'id': entry['id'], 'status': 'completed',
        'scope': 'native_per_call_response_function_only',
        'evaluation_relation': 'retrospective_leave_concurrency_out',
        'source_groups': groups, 'observations': entry['observations'], 'folds': folds,
        'population_coverage': entry.get('population_coverage', []),
        'fitted_domains': sum(m['status'] == 'fitted' for f in folds for m in f['model']['models']),
        'evaluation': {'rows': rows, 'summary': {'populations': len(rows),
            'predicted': sum(r['status'] == 'predicted' for r in rows),
            'passed': sum(r['passed'] is True for r in rows)},
            'by_native_family': {key: dict(value) for key, value in sorted(native_summary.items())},
            'activity_differences_are_additive_body_wall_time': False,
            'heldout_timing_used_to_refit': False},
        'limits': entry.get('limits', []), 'training_frozen_before_evaluation_read': True}


def run_generalization(registry, base):
    """Canonical pipeline API: fit, freeze, then read held-out native responses.

    ``registry.generalization`` declares experiments with ``specification`` and
    immutable ``training_observations`` / ``evaluation_observations`` pins. Each
    evidence file contains compact complete-population ``points``. This reports
    native response-function validation, not fresh Sim kernel or Body accuracy.
    The pipeline owns publication/archive and any subsequent fresh Body replay.
    """
    sources = {row['source']['sha256'] for row in registry['cases']}
    experiments = []
    for entry in registry.get('generalization', []):
        if entry.get('status') == 'planned':
            experiments.append({'id': entry['id'], 'status': 'planned', 'reason': entry['reason'],
                **{key: entry[key] for key in ('coverage', 'evaluation_relation', 'limits') if key in entry}})
            continue
        if 'source_groups' in entry:
            if not {s for g in entry['source_groups'] for s in g['source_sha256']} <= sources:
                raise ValueError('generalization_source_missing_from_canonical_registry')
            experiments.append(run_concurrency_exclusion(entry, base))
            continue
        specification = entry['specification']
        if not set(specification['training_sources'] + specification['evaluation_sources']) <= sources:
            raise ValueError('generalization_source_missing_from_canonical_registry')
        training = _read_observation_pin(entry['training_observations'], base)
        model = fit_service_domains(specification, training['points'])
        # Freeze before opening the evaluation artifact. No function, coordinate
        # or domain selection below depends on its response values.
        frozen_identity = model['sha256']
        evaluation = _read_observation_pin(entry['evaluation_observations'], base)
        result = evaluate_service_domains(model, evaluation['points'])
        experiments.append({'id': entry['id'], 'status': 'completed',
            'scope': 'native_per_call_response_function_only',
            'evaluation_relation': specification['evaluation_relation'],
            'specification_sha256': specification['sha256'],
            'training_observations': entry['training_observations'],
            'evaluation_observations': entry['evaluation_observations'],
            'frozen_model_sha256': frozen_identity, 'model': model, 'evaluation': result,
            'serving_mode_groups': entry.get('serving_mode_groups', []),
            'fitted_domains': sum(m['status'] == 'fitted' for m in model['models']),
            'limits': entry.get('limits', []), 'training_frozen_before_evaluation_read': True})
    compared = [e for e in experiments if e['status'] == 'completed']
    return {'schema_version': 'mindie-service-generalization-run/1', 'status': 'completed',
        'experiments': experiments, 'summary': {'experiments': len(experiments),
            'completed': len(compared), 'planned': len(experiments) - len(compared),
            'populations': sum(e['evaluation']['summary']['populations'] for e in compared),
            'predicted': sum(e['evaluation']['summary']['predicted'] for e in compared),
            'passed': sum(e['evaluation']['summary']['passed'] for e in compared)},
        'new_raw_scans': 0, 'new_Sim_predictions': 0,
        'body_residual_used': False, 'strict_native_admission_changed': False,
        'new_blind_or_zero_shot_claimed': False}
