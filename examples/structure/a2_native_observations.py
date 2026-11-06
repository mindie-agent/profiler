"""Source-scoped A2 native operator responses for retained-capture replay.

[Role] Bind explicit tensor/quantization contracts and native kernel services.
[Invariants] No model names, case IDs or Body durations select a response.
  Unmatched shapes retain the caller's base declaration. Binary identity is
  provenance, not an execution admission condition. Input mappings are copied.
[Timeouts & Locks] One bounded local JSON profile, cached after the first read.
[Side-Effect Policy] Reads the packaged profile; no capture, device or network I/O.
"""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path


PROFILE_PATH = Path(__file__).with_name('profiles') / 'a2_native_20261031.json'
DECODE_PROFILE_PATH = PROFILE_PATH.with_name('a2_decode_native_20261031.json')


@lru_cache(maxsize=2)
def _profile(phase):
    data = (DECODE_PROFILE_PATH if phase == 'decode' else PROFILE_PATH).read_bytes()
    return json.loads(data), sha256(data).hexdigest()


def _source_domain(case, profile):
    contract = profile['source_contract']
    hardware = case.machine.hardware_key or case.machine.sku
    if hardware != contract['hardware']:
        return 'hardware_outside_source_domain'
    if any(getattr(case.runtime.parallel, key) != value
           for key, value in contract['parallel'].items()):
        return 'parallelism_outside_source_domain'
    if any(getattr(case.model, key) != value for key, value in contract['model'].items()):
        return 'model_geometry_outside_source_domain'
    if not case.model.layer_plans or any(
            any(getattr(plan, key) != value for key, value in contract['layer'].items())
            for plan in case.model.layer_plans):
        return 'layer_geometry_outside_source_domain'
    if any(getattr(case.model.quant, key) != value for key, value in contract['quant'].items()):
        return 'quantization_outside_source_domain'
    if any(getattr(case.runtime, key) != value for key, value in contract['runtime'].items()):
        return 'runtime_outside_source_domain'
    return None


def _explicit_quant_conflict(raw, profile):
    quant = raw.get('model', {}).get('quant') or {}
    if any(key in quant and quant[key] != value for key, value in profile['quant_fields'].items()):
        return True
    overrides = dict(quant.get('category_overrides', {}))
    for category, expected in profile['quant_category_overrides'].items():
        parents = ['.'.join(category.split('.')[:i + 1]) for i in range(len(category.split('.')))]
        if category == 'mla_absorb':
            parents.insert(0, 'mla')
        declared = {}
        for name in parents:
            declared.update(dict(overrides.get(name, {})))
        if any(key in declared and declared[key] != value for key, value in expected.items()):
            return True
    return False


def _native_domain_matches(raw, rules, geometry):
    """Check the complete replacement before discarding an existing response."""
    from mindie_sim import target_operators
    from mindie_sim.prediction.body_defaults import consume_target_declaration
    from mindie_sim.prediction.cost import CostModel
    from mindie_sim.prediction.execution import Execution
    from mindie_sim.prediction.operator_analysis import _replay_scope
    from mindie_sim.prediction.program import RecipeBook
    from mindie_sim.prediction.service_regimes import RegimePolicy
    from mindie_sim.prediction.structure import parse_case

    operators = target_operators(raw, **geometry)
    case = consume_target_declaration(parse_case(raw), operators)
    execution = Execution(case, CostModel(case), recipes=RecipeBook.from_mapping(case.runtime.kernels))
    policy = RegimePolicy(rules)
    expected = {rule['match']['recipe'] for rule in rules}
    seen = set()
    scope = _replay_scope(operators, None)
    for op in operators:
        if op.recipe not in expected:
            continue
        seen.add(op.recipe)
        prepared, recipe = execution.prepare(op, 0)
        context = execution._context(prepared, 0, scope, recipe=recipe)
        if policy.resolve(context, lambda *args, **kwargs: None) is None:
            return False
    return seen == expected


def apply_a2_native_observations(raw, *, phase, tokens, context, sequences):
    """Apply one declared physical profile; unknown domains stay analytical/base.

    The selected profile supplies the source caller's BF16 and scale-only
    inputs. Its response rules independently guard dtype, shape, sequence
    partition, implementation and physical rates inside the common engine.
    """
    profile, digest = _profile(phase)
    result = deepcopy(raw)
    provenance = {'profile_id': profile['id'], 'profile_sha256': digest,
                  'status': 'not_applicable', 'capture_binary_identity': 'unknown',
                  'calibration_boundary': 'individual_native_device_kernel',
                  'body_total_fitting': False}
    domains = profile['geometry_domains']
    matched = (phase == profile.get('phase', 'prefill') and type(tokens) is int and type(context) is int
               and type(sequences) is int and sequences == 1
               and any(tokens == d['query'] and d['context_min'] <= context <= d['context_max']
                       for d in domains))
    if not matched:
        return result, {**provenance, 'reason': 'geometry_outside_calibration_domain'}
    hardware = raw.get('machine', {}).get('hardware_key') or raw.get('machine', {}).get('sku')
    if hardware and hardware != profile['source_contract']['hardware']:
        return result, {**provenance, 'reason': 'hardware_outside_source_domain'}
    if _explicit_quant_conflict(raw, profile):
        return result, {**provenance, 'reason': 'explicit_quantization_contract_conflict'}

    from mindie_sim.prediction.structure import parse_case

    parsed = parse_case(raw)
    reason = _source_domain(parsed, profile)
    if reason:
        return result, {**provenance, 'reason': reason}
    service = profile['native_queue']
    # Inspect normalized inheritance, including device/devices/dies aliases,
    # before supplying an omitted queue. A per-rank declaration always wins.
    queue = service['resource']
    for device in parsed.machine.dies:
        for values, expected in ((dict(device.rates), service['rate']),
                                 (dict(device.resource_units), 1),
                                 (dict(device.work_units), 'busy_ns')):
            if queue in values and values[queue] != expected:
                return result, {**provenance, 'reason': 'native_queue_declaration_conflict'}
    kernels = result.setdefault('runtime', {}).setdefault('kernels', {})
    lowerings = kernels.setdefault('lowerings', {})
    fusion = lowerings.get('native_fusion')
    if fusion is not None and (not isinstance(fusion, dict)
                              or fusion.get('implementation') != 'declared_native_fusion'):
        return deepcopy(raw), {**provenance, 'reason': 'native_fusion_binding_conflict'}
    if fusion:
        options = fusion.get('options', {})
        if not isinstance(options, dict) or not options.get('roles'):
            return deepcopy(raw), {**provenance, 'reason': 'native_fusion_roles_conflict'}
        if options.get('program_profiles', {}).get('lightning_indexer'):
            return deepcopy(raw), {**provenance, 'reason': 'native_indexer_program_conflict'}

    quant = parsed.model.quant.to_dict()
    for category, fields in profile['quant_category_overrides'].items():
        quant.setdefault('category_overrides', {}).setdefault(category, {}).update(fields)
    quant.update(profile['quant_fields'])
    quant['source'] = {'kind': 'source_bound_native_operator_profile', 'profile': profile['id']}
    quant['notes'] = ['Explicit per-role native tensor inputs from retained A2 captures.']
    result['model']['quant'] = quant
    fusion = lowerings.setdefault('native_fusion', {'implementation': 'declared_native_fusion', 'options': {}})
    options = fusion.setdefault('options', {})
    options['roles'] = list(dict.fromkeys([*options.get('roles', []), 'lightning_indexer']))

    device = result['machine'].setdefault('device', {})
    for key, value in (('rates', service['rate']), ('resource_units', 1), ('work_units', 'busy_ns')):
        device.setdefault(key, {}).setdefault(queue, value)

    rules = profile['service_regimes']
    geometry = dict(phase=phase, tokens=tokens, context=context, sequences=sequences)
    if not _native_domain_matches(result, rules, geometry):
        return deepcopy(raw), {**provenance, 'reason': 'native_physical_domain_mismatch'}
    replaced = set(profile['replaced_regime_ids']) | {r['id'] for r in rules}
    kernels['service_regimes'] = [r for r in kernels.get('service_regimes', []) if r['id'] not in replaced]
    kernels['service_regimes'].extend(deepcopy(rules))
    provenance.update(status='applied', rule_count=len(rules),
                      training_sources=profile['training_sources'],
                      validation_sources=profile['validation_sources'],
                      limitations=profile['limitations'])
    return result, provenance
