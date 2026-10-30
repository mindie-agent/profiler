"""Real retained Kimi populations calibrate one response per physical boundary."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / 'examples/structure'
DIRECTORY = ROOT / 'acceptance-20261030-service-kimi-v41'


def test_distinct_retained_kda_buckets_are_not_deduplicated_by_representative_node():
    case_id = 'a5_kimi_tp8_e16_bf16_c32_p4k'
    case = json.loads((DIRECTORY/'cases-complete-population'/f'{case_id}.json').read_text())
    native = json.loads((ROOT/'acceptance-20261030-kimi-native-references-5ec8843a/kimi-native-reference-scoreboard.json').read_text())
    source = next(row for row in native['cases'] if row['case_id'] == case_id)
    groups = [g for g in source['groups'] if g['native_operator_type'] == 'RecurrentKda']
    rule, = [r for r in case['runtime']['kernels']['service_regimes']
             if r['provenance']['native_operator_types'] == ['RecurrentKda']]
    assert len(groups) == len(rule['provenance']['retained_observations']) == 23
    count = sum(g['observed_us']['count'] for g in groups)
    activity = sum(sum(duration*n for duration, n in g['duration_ns_counter']) for g in groups)
    assert count == source['forward_count'] * 69
    assert rule['provenance']['measurement_population'] == count
    assert rule['response']['fixed_us'] == pytest.approx(activity / count / 1000)
    assert rule['provenance']['expected_invocations_full_dp_cohort'] == 69


def test_real_mc2_response_owns_native_group_not_each_internal_phase():
    case_id = 'a5_kimi_tp8_e16_bf16_c32_p4k'
    case = json.loads((DIRECTORY/'cases-complete-population'/f'{case_id}.json').read_text())
    native = json.loads((ROOT/'acceptance-20261030-kimi-native-references-5ec8843a/kimi-native-reference-scoreboard.json').read_text())
    source = next(row for row in native['cases'] if row['case_id'] == case_id)
    for kind in ('MoeDistributeDispatchV3', 'MoeDistributeCombineV3'):
        group, = [g for g in source['groups'] if g['native_operator_type'] == kind]
        rule, = [r for r in case['runtime']['kernels']['service_regimes'] if r['match'].get('kernel') == kind]
        assert len(group['program_buckets'][0]['representative_target_ids']) > 1
        assert rule['provenance']['expected_invocations_full_dp_cohort'] == 92
        assert rule['provenance']['measurement_population'] == source['forward_count'] * 92
        assert rule['response']['fixed_us'] == pytest.approx(group['observed_us']['mean'])
        assert rule['provenance']['evaluation_relation'] == 'in_sample'
        assert rule['provenance']['fit_source_identity']['sha256'] == source['source_identity']['sha256']
