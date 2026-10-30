"""[Role] Declare complete local native services for two retained A3 captures.
[Invariants] Native means, not Body residuals, set parameters. All five source
  roles use the same rule: one complete native call occupies one declared queue.
  Logical FLOPs/traffic remain analytical reference, not measured HBM service.
[Timeouts & Locks] Two finite metadata graphs; no raw scans, Engine or locks.
[Side-Effect Policy] Write separate cases, population links and a replay manifest.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from mindie_sim.prediction.service_regimes import axis_equal, lookup

INPUT = HERE.parents[2] / 'data/observations/sources/arch22-physical-services/native-joint-service-inputs.json'
QUEUE = 'observed_a3_local_native'


def role(op):
    meta = dict(op.metadata)
    if meta.get('fusion_role'):
        return meta['fusion_role']
    return {'grouped_down': 'expert_down',
            'latent_attention_batch': 'indexed_attention_batch'}.get(op.recipe)


def matched_ids(rule, ops, parsed):
    selected = set()
    for op in ops:
        axes = {**op.to_dict(include_work=False),
                'hardware': parsed.machine.hardware_key or parsed.machine.sku,
                'dtype': op.dtype or parsed.model.compute_dtype}
        if all(axis_equal(lookup(axes, key), value) for key, value in rule['match'].items()):
            selected.add(op.op_id)
    return selected


def build(revision):
    inputs = read(INPUT)
    before = read(HERE / 'decode-forward-native-cases.json')
    result = deepcopy(before)
    variant = 'livepre-complete-native-joint-' + revision[:8]
    result['variant_id'] = variant
    result['runtime_plan']['source_commit'] = revision
    population_rows = []
    for row in result['cases']:
        original = Path(row['sim_case_path'])
        raw = read(original)
        parsed, ops = physical_ops(raw, row['replay_input_pins']['primary_geometry'])
        candidates = [c for c in inputs['candidates']
                      if any(p['case_id'] == row['case_id'] for p in c['source_populations'])]
        if len(candidates) != 5:
            raise ValueError('five_complete_native_role_populations_required')
        additions = []
        joint_ids = set()
        for c in candidates:
            domain = c['applicability_domain']
            source, = c['source_populations']
            if source['source_identity']['sha256'] != row['source']['sha256']:
                raise ValueError('retained_native_source_changed')
            if source['declared_case_identity']['sha256'] != identity(original)['sha256']:
                raise ValueError('native_source_declaration_changed')
            geometry = row['replay_input_pins']['primary_geometry']
            if any(domain[left] != geometry[right] for left, right in (
                    ('execution_query_rows', 'query_rows'), ('execution_batch', 'sequences_per_replica'),
                    ('query_tokens_per_sequence', 'tokens_per_sequence'))):
                raise ValueError('observed_joint_domain_geometry_differs')
            selected = [op for op in ops if role(op) == domain['source_role']]
            expected = source['calls_per_forward']
            if len(selected) != expected:
                raise ValueError('native_role_multiplicity_differs:' + domain['source_role'])
            joint_ids.update(op.op_id for op in selected)
            matches = []
            for op in selected:
                match = _physical_match(parsed, op)
                meta = dict(op.metadata)
                for key in ('fusion_role', 'fusion_program_profile', 'fusion_source_profile',
                            'indexed_attention_geometry', 'expected_active_experts', 'expected_rows'):
                    if key in meta:
                        match['metadata.' + key] = meta[key]
                matches.append(match)
            if any(match != matches[0] for match in matches):
                raise ValueError('source_domain_not_homogeneous:' + domain['source_role'])
            statistics = c['observed_native_elapsed_us']
            if statistics['count'] != expected * source['forward_count']:
                raise ValueError('complete_population_multiplicity_differs')
            additions.append({
                'id': 'joint-' + domain['source_role'], 'match': matches[0],
                'response': {'fixed_us': c['parameter_value_us']},
                'execution': {'kind': 'joint_native', 'native_kernel': domain['native_operator_type'],
                              'resource': QUEUE, 'reference_rate': 1e9},
                'provenance': {
                    'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'input_identity': identity(INPUT), 'candidate_id': c['candidate_id'],
                    'source_identity': source['source_identity'],
                    'timing_identity': source['timing_identity'], 'timing_members': source['timing_members'],
                    'observed_native_elapsed_us': statistics,
                    'applicability_domain': domain, 'expected_rule_hits': expected,
                    'forward_count': source['forward_count'], 'body_residual_used': False,
                    'strict_admission_changed': False,
                    'service_semantics': 'one_complete_local_native_call; analytical_work_retained_as_reference',
                    'queue_scope': 'one_declared_device_queue_shared_by_the_five_local_native_domains',
                    'physical_HBM_or_ISA_rate_identified': False}})
        kept, replaced = [], []
        for previous in raw['runtime']['kernels'].get('service_regimes', []):
            prior_ids = matched_ids(previous, ops, parsed)
            if prior_ids & joint_ids:
                if prior_ids - joint_ids or previous.get('coordinates') or previous.get('domain'):
                    raise ValueError('prior_response_requires_explicit_partial_domain_replacement')
                replaced.append(previous)
            else:
                kept.append(previous)
        raw['runtime']['kernels']['service_regimes'] = kept + additions
        device = raw['machine'].setdefault('device', {})
        for field, value in [('rates', 1e9), ('work_units', 'busy_ns'), ('resource_units', 1)]:
            device.setdefault(field, {})[QUEUE] = value
        evidence = {'evaluation_relation': 'in_sample', 'input_identity': identity(INPUT),
                    'body_residual_used': False, 'joint_native_domains': [c['candidate_id'] for c in candidates],
                    'replaced_same_native_completion_floors': replaced,
                    'scope': 'complete native service; not isolated hardware pipeline prices'}
        raw['runtime'].setdefault('metadata', {}).update(calibration_origin='observed', calibration_evidence=evidence)
        path = HERE / 'joint-service/cases' / (row['case_id'] + '.json')
        write(path, raw)
        row.update(sim_case_path=str(path), model_declaration=identity(path), variant_id=variant,
                   calibration_origin='observed', calibration_evidence=evidence)
        row['replay_input_pins']['case'] = identity(path)
        row['runtime_refresh']['scope'] = 'five_complete_local_native_joint_services; existing_collective_floor_unchanged'
        population_rows.append({'case_id': row['case_id'], 'rules': additions,
                                'replaced_same_native_completion_floors': replaced,
                                'original_case_identity': identity(original), 'case_identity': identity(path)})
    write(HERE / 'joint-service/observed-populations.json',
          {'cases': population_rows, 'input_identity': identity(INPUT), 'raw_scans': 0, 'cost_predictions': 0})
    write(HERE / 'joint-service/decode-forward-cases.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime-source-commit', required=True)
    build(parser.parse_args().runtime_source_commit)
