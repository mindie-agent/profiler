"""Retained Kimi BF16 native ABI and heterogeneous topology correspondence."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def evidence():
    sim = pytest.importorskip('mindie_sim')
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    helper = importlib.import_module('kimi_native_references')
    path = ROOT / 'examples/structure/acceptance-20261030-kimi-logical96-operators/native-partitions/a5_kimi_tp8_e16_bf16_c32_p4k-native-partitions.json'
    part = json.loads(path.read_text())
    actual = json.loads(Path(part['actual_identity']['path']).read_text())
    case_path = Path(sim.__file__).resolve().parents[1] / 'examples/cases/high-concurrency-20261030/kimi-source/a5_kimi_tp8_e16_bf16_c32_p4k_source.json'
    if not case_path.exists(): pytest.skip('companion Sim source case is unavailable')
    case = parse_case(json.loads(case_path.read_text()))
    manifest = export_structure(case, phase='decode', tokens=1, sequences=32, context=4096, scope='body')
    return helper, part, actual, manifest


def test_all_native_calls_keep_whole_histogram_and_layer_weighted_programs(evidence):
    helper, part, actual, manifest = evidence
    groups, failures, programs = helper.prepare_references(part, manifest)
    mc2, mc2_failures, mc2_programs = helper.prepare_mc2_references(actual, manifest)
    assert not failures and not mc2_failures
    assert sum(g['observed_us']['count'] for g in groups) == part['native_event_count'] == 16054
    assert sum(g['observed_us']['count'] for g in mc2) == 8464
    assert len(programs) == 28 and len(mc2_programs) == 2
    for g in groups:
        old = part['partitions'][g['partition_index']]
        assert g['duration_ns_counter'] == old['duration_ns_counter']
        assert g['observed_us'] == old['observed_us']
        assert sum(b['event_count'] for b in g['program_buckets']) == g['observed_us']['count']
        assert not g['layer_histograms_inferred'] and not g['strict_accuracy_implied']
    hetero = [g for g in groups if len(g['program_buckets']) > 1]
    assert hetero and all(g['native_operator_type'] == 'AttnResFwd' for g in hetero)
    for program in mc2_programs.values():
        assert len(program['nodes']) > 2
        assert program['source_correspondence']['observed_valid_routed_rows'] is None
        assert any(n['family'] == 'alltoall' for n in program['nodes'])


def test_kda_accepted_state_branch_and_active_view_are_not_interchanged(evidence):
    helper, part, _, manifest = evidence
    changed = deepcopy(part)
    changed['partitions'] = [next(g for g in changed['partitions'] if g['native_operator_type'] == 'RecurrentKda')]
    changed['partitions'][0]['native_abi'][2].append([[32], 'int32', 'ND'])
    groups, failures, _ = helper.prepare_references(changed, manifest)
    assert not groups
    assert failures[0]['reason'] == 'kimi_kda_requires_no_accepted_array_10_input_abi'


def test_mla_prolog_uses_physical_padded_heads_not_logical_output_heads(evidence):
    helper, part, _, manifest = evidence
    groups, failures, programs = helper.prepare_references(part, manifest)
    prolog = next(g for g in groups if g['native_operator_type'] == 'MlaPrologV3')
    program = programs[prolog['program_buckets'][0]['program_set_key']]
    assert program['source_correspondence']['observed_physical_heads'] == 16
    assert {helper.role(n) for n in program['nodes']} == {
        'q_a', 'kv_a', 'q_norm', 'q_b', 'kv_norm', 'rotary', 'kv_store', 'q_absorb'}
    changed = deepcopy(part)
    changed['partitions'] = [next(g for g in changed['partitions'] if g['native_operator_type'] == 'MlaPrologV3')]
    changed['partitions'][0]['native_abi'][3][0][0][1] = 12
    assert helper.prepare_references(changed, manifest)[1][0]['reason'] == 'kimi_mla_prolog_bf16_padded_heads_abi'


def test_mc2_phase_stream_separation_is_part_of_program_identity(evidence):
    helper, _, _, manifest = evidence
    a = next(n for n in manifest['nodes'] if n['op_id'] == 's0.l1.mc2_dispatch.count_compute')
    b = next(n for n in manifest['nodes'] if n['op_id'] == 's0.l2.mc2_dispatch.count_compute')
    assert helper.program_signature(a) == helper.program_signature(b)
    changed = deepcopy(b)
    changed['operator']['stream'] = 's0.l2.mc2_dispatch.payload_net'
    assert helper.program_signature(a) != helper.program_signature(changed)
