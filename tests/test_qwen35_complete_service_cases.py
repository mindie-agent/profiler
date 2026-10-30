"""Complete Q35 retained populations define service responses without Body fits."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from build_qwen35_complete_service_cases import population, pinned, read

OUT = ROOT / 'examples/structure/acceptance-20261030-qwen35-complete-observed-service'


@pytest.mark.parametrize('concurrency', [4, 64, 128])
def test_complete_matrix_gdn_histograms_keep_multiplicity_and_other_rules(concurrency):
    evidence = read(OUT / 'complete-service-populations.json')
    row = next(r for r in evidence['cases'] if r['case_id'] == f'qwen35-35b-a5-tp4-c{concurrency}-graph')
    case = pinned(row['case_identity'])
    rules = {r['id']: r for r in case['runtime']['kernels']['service_regimes']}
    for addition in row['new_rules']:
        if addition['native_operator_type'] not in {'MatMulV3', 'RecurrentGatedDeltaRule'}:
            continue
        actual = pinned(addition['actual_identity'])
        mapping = pinned(addition['mapping_identity'])
        cohort, = [c for w in mapping['windows'] for c in w['cohorts'] if c['cohort_id'] == addition['cohort_id']]
        families = [f for f in actual['families'] if f['native_operator_type'] == addition['native_operator_type']
                    and set(f['candidate_target_ids']) == set(cohort['target_ids'])]
        observed = json.loads(json.dumps(population(families)))
        assert observed == addition['observed_population']
        assert observed['count'] == addition['forward_count'] * len(cohort['target_ids'])
        assert rules[addition['rule_id']]['response']['fixed_us'] == pytest.approx(observed['mean_us'])
    excluded, = row['unresolved_population_domains']
    assert excluded['observed_population']['count'] == 2 * excluded['declared_target_count'] * row['forward_count']
    assert not excluded['calibration_rule_added']
    assert set(row['retained_rule_ids']) <= rules.keys()
    assert not (set(row['removed_other_model_rule_ids']) & rules.keys())


def test_small_rows_dsq_preserves_typed_chain_and_capacity_not_valid_rows():
    evidence = read(OUT / 'complete-service-populations.json')
    row = next(r for r in evidence['cases'] if r['case_id'] == 'qwen35-35b-a5-tp4-c4-graph')
    addition, = [r for r in row['new_rules'] if r['native_operator_type'] == 'DequantSwigluQuant']
    dsq = pinned(addition['dsq_partition_identity'])
    grouped = pinned(addition['grouped_partition_identity'])
    dsq_parts = [p for p in dsq['partitions'] if p['native_operator_type'] == 'DequantSwigluQuant']
    assert addition['observed_population'] == json.loads(json.dumps(population(dsq_parts)))
    assert addition['observed_population']['count'] == 40 * row['forward_count']
    abi = addition['native_abi']
    assert addition['capacity_rows'] == 128
    assert addition['declared_active_shape'][0] == 32
    assert not addition['actual_group_list_values_observed']
    for part in grouped['partitions']:
        if part['role'] == 'expert_up':
            assert part['native_abi'][3][0] == abi[2][0]
        else:
            assert part['native_abi'][2][0] == abi[3][0]
            assert part['native_abi'][2][8] == abi[3][1]
    assert not addition['whole_body_residual_used']
    assert addition['evaluation_relation'] == 'in_sample'


def test_c4_extension_replaces_grouped_response_instead_of_adding_two_floors():
    evidence = read(OUT / 'c4-extended-populations.json')
    case = pinned(evidence['case_identity'])
    rules = {r['id']: r for r in case['runtime']['kernels']['service_regimes']}
    assert not (set(evidence['replaced_rule_ids']) & rules.keys())
    for rule in evidence['new_rules']:
        proof = rule['provenance']
        assert proof['observed_population']['count'] == proof['expected_rule_hits'] * evidence['forward_count']
        assert rule['response']['fixed_us'] == pytest.approx(proof['observed_population']['mean_us'])
        assert not proof['body_residual_used']
        if proof['native_operator_type'] == 'GroupedMatmul':
            assert proof['declared_active_rows'] == 32
            assert proof['captured_capacity_rows'] == 128
            assert sum(rule['match']['metadata.matrix_group_rows']) == 32
            assert not proof['actual_group_list_values_observed']


def test_attention_uses_one_batch_response_without_upgrading_two_ABI_examples():
    evidence = read(OUT / 'c4-batched-attention-population.json')
    rule = evidence['new_rule']; proof = rule['provenance']
    actual = pinned(proof['actual_identity'])
    family, = [f for f in actual['families'] if f['native_operator_type'] == 'FusedInferAttentionScore']
    observed = population([family])
    assert observed['count'] == 840 == 10 * evidence['forward_count']
    assert rule['response']['fixed_us'] == pytest.approx(observed['mean_us'])
    assert proof['expected_rule_hits'] == len(proof['declared_layer_ids']) == 10
    assert len(proof['retained_contract_examples']) == 2
    assert not proof['all_event_native_ABIs_retained']
    assert not proof['strict_admission_changed']
    assert not proof['physical_implementation_identified']
    assert not proof['body_residual_used']


def test_gdn_helpers_preserve_qk_pooled_population_and_single_native_boundaries():
    evidence = read(OUT / 'c4-gdn-helpers-population.json')
    unique = {}
    for rule in evidence['new_rules']:
        proof = rule['provenance']; actual = pinned(proof['actual_identity'])
        family, = [f for f in actual['families'] if f['native_operator_type'] == proof['native_operator_type']]
        observed = population([family])
        assert rule['response']['fixed_us'] == pytest.approx(observed['mean_us'])
        assert observed['count'] == proof['pooled_native_target_count'] * evidence['forward_count']
        assert proof['expected_rule_hits'] == 30
        assert not proof['all_event_native_ABIs_retained']
        assert not proof['strict_admission_changed']
        assert not proof['body_residual_used']
        unique[proof['native_operator_type']] = observed['count']
    assert sum(unique.values()) == 120 * evidence['forward_count']
    qk = [r for r in evidence['new_rules'] if r['provenance']['native_operator_type'] == 'l2norm_fwd_kernel2']
    assert len(qk) == 2
    assert all(not r['provenance']['per_role_timing_separately_observed'] for r in qk)
    assert sum(r['provenance']['expected_rule_hits'] for r in qk) == 60
