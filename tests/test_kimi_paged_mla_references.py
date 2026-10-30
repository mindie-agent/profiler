"""Complete native FIA evidence stays conditional despite exact source geometry."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module', params=[(1, '4k'), (32, '4k'), (1, '16k'), (32, '16k')])
def complete_fia(request):
    sim = pytest.importorskip('mindie_sim')
    from mindie_sim.structure import export_structure
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    helper = importlib.import_module('kimi_native_references')
    join = importlib.import_module('compare_kimi_native_partitions')
    batch, context_label = request.param
    case_id = f'a5_kimi_tp8_e16_bf16_c{batch}_p{context_label}'
    parent = ROOT / 'examples/structure'
    base_path = parent / 'acceptance-20261030-kimi-logical96-operators/native-partitions' / (case_id + '-native-partitions.json')
    additional_path = parent / 'acceptance-20261030-kimi-paged-fia-pmu' / (case_id + '-native-partitions.json')
    base = json.loads(base_path.read_text()); actual = json.loads(Path(base['actual_identity']['path']).read_text())
    combined, proof = join.additional_partitions(base, actual, additional_path)
    case_path = Path(sim.__file__).resolve().parents[1] / 'examples/cases/high-concurrency-20261030/kimi-source-complete' / (case_id + '_source_complete.json')
    if not case_path.exists(): pytest.skip('Companion source-complete case unavailable')
    manifest = export_structure(json.loads(case_path.read_text()), phase='decode', tokens=1,
        sequences=batch, context=actual['conditional_context_tokens'], scope='body')
    combined['partitions'] = [p for p in combined['partitions'] if p['native_operator_type'] == 'FusedInferAttentionScore']
    return helper, combined, manifest, proof, base, additional_path


def test_full_fia_native_population_prices_source_program_without_strict_claim(complete_fia):
    helper, part, manifest, proof, _, _ = complete_fia
    groups, failures, programs = helper.prepare_references(part, manifest)
    assert not failures and len(groups) == 1 and len(programs) == 1
    group = groups[0]
    assert group['duration_ns_counter'] == part['partitions'][0]['duration_ns_counter']
    assert group['observed_us']['count'] == part['forward_count'] * 24
    assert len(group['layer_ids']) == 24
    assert not group['strict_accuracy_implied'] and not group['additional_budget_allowed']
    program = next(iter(programs.values())); correspondence = program['source_correspondence']
    assert correspondence['observed_output_layout'] == 'NBSD'
    assert correspondence['observed_context_values'] is None
    assert not correspondence['strict_physical_work_proven']
    assert correspondence['declared_contexts'] == [manifest['execution']['context']] * part['geometry']['sequences_per_replica']
    assert program['physical_work_per_program'][0]['flops'] > 0
    assert program['nodes'][0]['physical_work_basis'] == 'prepared_source_plan'
    assert proof['original_actual_identity']


def test_transposed_output_or_wrong_declared_context_cannot_match(complete_fia):
    helper, part, manifest, _, _, _ = complete_fia
    changed = deepcopy(part)
    changed['partitions'][0]['native_abi'][3][0][0] = changed['partitions'][0]['native_abi'][2][0][0]
    groups, failures, _ = helper.prepare_references(changed, manifest)
    assert not groups and failures[0]['reason'] == 'kimi_paged_mla_active_bns_query_nbs_output_abi'
    changed = deepcopy(manifest)
    changed['execution']['context'] -= 8
    groups, failures, _ = helper.prepare_references(part, changed)
    assert not groups and failures[0]['reason'] == 'kimi_paged_mla_source_dispatch_geometry_differs'


def test_additional_pass_joins_only_fia_and_does_not_duplicate_mc2(complete_fia):
    _, _, _, _, base, additional_path = complete_fia
    join = importlib.import_module('compare_kimi_native_partitions')
    actual = json.loads(Path(base['actual_identity']['path']).read_text())
    combined, _ = join.additional_partitions(base, actual, additional_path)
    types = {p['native_operator_type'] for p in combined['partitions']}
    assert types == {'RecurrentKda', 'CausalConv1d', 'AttnResFwd', 'MlaPrologV3', 'FusedInferAttentionScore'}
    assert combined['native_event_count'] == base['native_event_count'] + base['forward_count'] * 24
