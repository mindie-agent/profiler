"""Retained A5 FP8/MXFP4 grouped bank ABI, not fabricated per-expert rows."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ROOT/'examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1-v41-dp8'


@pytest.fixture(scope='module')
def grouped_evidence():
    pytest.importorskip('mindie_sim.structure')
    sys.path.insert(0, str(ROOT/'examples/structure'))
    reprice = importlib.import_module('reprice_body_operator_families')
    helper = importlib.import_module('rebind_grouped_source_roles')
    actual = reprice.read(PREFIX.with_suffix('.actual.json'))
    manifest = reprice.fresh_structure(PREFIX.with_suffix('.case.json'),
                                       reprice.read(PREFIX.with_suffix('.mapping.json')))
    return helper, actual, manifest


def test_full_retained_abi_preserves_up_down_populations_and_unknown_rows(grouped_evidence):
    helper, actual, manifest = grouped_evidence
    rebound, records = helper.rebind_frozen_grouped_groups(actual, manifest)
    assert len(records) == 2 and all(row['status']=='rebound' for row in records)
    original = {row['declared_role']:row for row in actual['source_role_references'] if row['native_operator_type']=='GroupedMatmul'}
    targets = {node['node_id']:node for node in manifest['nodes']}
    for group in rebound['source_role_references']:
        if group['native_operator_type'] != 'GroupedMatmul':
            continue
        before = original[group['declared_role']]
        assert group['duration_ns_counter'] == before['duration_ns_counter']
        assert group['observed_us']['count'] == 6080 and group['layer_ids'] == list(range(40))
        relation = group['source_correspondence']
        assert relation['observed_buffer_row_capacity'] == 48
        assert relation['observed_valid_routed_rows'] is None and relation['observed_group_list_values'] is None
        assert relation['observed_native_tensor_contract'] == helper.freeze(before['source_correspondence']['observed_native_tensor_contract'])
        assert group['physical_work_per_program'] == [targets[key]['physical_work'] for key in group['representative_target_ids']]
        assert not group['occurrence_binding_implied'] and not group['additional_budget_allowed']


def test_native_scale_layout_is_required_for_frozen_grouped_rebind(grouped_evidence):
    helper, actual, manifest = grouped_evidence
    group = deepcopy(next(row for row in actual['source_role_references'] if row['declared_role']=='expert_up'))
    group['source_correspondence']['observed_native_tensor_contract'][2][5][2] = 'ND'
    _, records = helper.rebind_frozen_grouped_groups({**actual,'source_role_references':[group]},manifest)
    assert records[0]['status'] == 'not_rebound'
    assert records[0]['reason'] == 'native_grouped_abi_no_longer_matches_unique_expert_role'


def test_one_layer_new_program_cannot_split_retained_full_histogram(grouped_evidence):
    helper, actual, manifest = grouped_evidence
    group = next(row for row in actual['source_role_references'] if row['declared_role']=='expert_up')
    nodes = list(manifest['nodes'])
    index = next(i for i,node in enumerate(nodes) if node['node_id']=='rank:0/s0.l19.expert_up')
    target = nodes[index]
    nodes[index] = {**target,'physical_signature':'different_program',
                   'physical_work':{**target['physical_work'],'hbm_bytes':target['physical_work']['hbm_bytes']*2}}
    rebound, records = helper.rebind_frozen_grouped_groups({**actual,'source_role_references':[group]}, {**manifest,'nodes':nodes})
    assert records[0]['reason'] == 'fresh_physical_program_heterogeneous_cannot_split_retained_histogram'
    assert rebound['source_role_references'][0] is group
