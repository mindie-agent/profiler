"""Real CSV branches use the core mapper without manufacturing occurrence evidence."""
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

from mindie_profiler.analyze import analyze_profile

FIXTURES = Path(__file__).parent / 'fixtures'


def replay(capture, case_name):
    structure = pytest.importorskip('mindie_sim.structure')
    path = case_path(f'{case_name}.json')
    original = path.read_bytes()
    case = json.loads(original)
    case['runtime'].setdefault('kernels', {})['lowerings'] = {'mla_prolog': 'vllm_ascend_mla_prolog_v3'}
    manifest = structure.export_structure(case, phase='decode', tokens=1, context=4096, scope='model')
    report = analyze_profile(FIXTURES / capture, source='csv', full_range=True,
                             structure=manifest)['structure_mapping']
    assert path.read_bytes() == original
    assert report['windows'][0]['bound_busy_union_ns'] == 0
    assert report['windows'][0]['layers'] == []
    assert sum(report['status_counts'].values()) == len(report['event_mappings'])
    return report


def test_glm_decode_keeps_both_real_prolog_output_branches():
    report = replay('attention_cache_contracts/a3_glm53_decode.csv', 'glm53-a3-w4a8')
    assert len(report['event_mappings']) == 3
    prologs = [row for row in report['event_mappings'] if row['operator_type'] == 'MlaPrologV3']
    assert len(prologs) == 2
    assert {row['candidate_count'] for row in prologs} == {21, 57}
    assert all(row['status'] == 'ambiguous' for row in prologs)
    assert all(row['observed_native_tensor_abi'][1] == 'MlaPrologV3' for row in prologs)
    assert prologs[0]['observed_contract'] != prologs[1]['observed_contract']
    assert not (set(prologs[0]['candidate_subgraph_ids']) & set(prologs[1]['candidate_subgraph_ids']))
    assert all(not row['occurrence_binding_implied'] for row in report['windows'][0]['cohorts'])


def test_kimi_mixed_capture_does_not_invent_fp8_attention_from_expert_precision():
    report = replay('body_attention/kimi_a5_full_model.csv', 'kimi-k3-a5')
    assert len(report['event_mappings']) == 8
    examples = {row['operator_type']: row for row in report['event_mappings']}
    prolog = examples['MlaPrologV3']
    assert prolog['status'] == 'unmapped' and prolog['candidate_count'] == 0
    assert prolog['diagnostic']['category'] == 'declared_structure_mismatch'
    assert prolog['observed_contract'][2] == ((1, 7168), 'fp8_e4m3', 'ND')
    assert prolog['observed_native_tensor_abi'][2][0][0] == (1, 1, 7168)
    assert all(examples[kind]['status'] == 'unmapped' for kind in (
        'layer_norm_gated_fwd_kernel', 'ScatterPaKvCache', 'FusedInferAttentionScore'))
