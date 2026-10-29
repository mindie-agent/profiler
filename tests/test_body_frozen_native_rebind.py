"""Real full-ABI MC2 aggregate rebinding without raw captures or fake timings."""
from copy import deepcopy
import importlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ROOT / 'examples/structure/acceptance-20261030-v41-final6-operators-e8/body-operator-a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4-v41-new6'


@pytest.fixture(scope='module')
def retained_mc2():
    pytest.importorskip('mindie_sim.structure')
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    module = importlib.import_module('rebind_body_source_roles')
    reprice = importlib.import_module('reprice_body_operator_families')
    actual = reprice.read(PREFIX.with_suffix('.actual.json'))
    mapping = reprice.read(PREFIX.with_suffix('.mapping.json'))
    manifest = reprice.fresh_structure(PREFIX.with_suffix('.case.json'), mapping)
    return module, actual, manifest


def test_real_full_native_mc2_histogram_reselects_all_routed_programs(retained_mc2):
    module, actual, manifest = retained_mc2
    before = actual['source_role_references'][0]
    rebound, records = module.rebind_frozen_native_groups(actual, manifest)
    after = rebound['source_role_references'][0]
    assert records[0]['status'] == 'rebound'
    assert records[0]['declared_routed_program_count'] == 9
    assert after['layer_ids'] == list(range(40))
    for key in ('duration_ns_counter', 'observed_us', 'observed_activity_sum_ns', 'examples'):
        assert after[key] == before[key]
    assert after['observed_us']['count'] == 1920
    assert after['source_correspondence']['observed_buffer_row_capacity'] == 4
    assert after['source_correspondence']['observed_valid_routed_rows'] is None
    assert after['source_correspondence']['observed_active_mask_values'] is None
    expected = {target['node_id']:target for target in manifest['nodes']}
    assert after['physical_work_per_program'] == [expected[key]['physical_work'] for key in after['representative_target_ids']]
    roles = {key.split('.',2)[-1] for key in after['representative_target_ids']}
    assert roles == {'pack','dispatch','expert_up.quantize','expert_up','expert_act','expert_down.quantize','expert_down','combine','unpack'}
    assert not after['additional_budget_allowed'] and not after['occurrence_binding_implied']
    assert after['frozen_native_rebind']['original_observation_group_id'] == before['group_id']


def test_changed_layer_work_cannot_split_real_aggregate_histogram(retained_mc2):
    module, actual, manifest = retained_mc2
    nodes = list(manifest['nodes'])
    index = next(i for i,node in enumerate(nodes) if node['node_id']=='rank:0/s0.l19.expert_up')
    target = nodes[index]
    nodes[index] = {**target, 'physical_signature':'different_verified_program',
                   'physical_work':{**target['physical_work'], 'hbm_bytes':target['physical_work']['hbm_bytes']*2}}
    rebound, records = module.rebind_frozen_native_groups(actual, {**manifest,'nodes':nodes})
    assert records[0]['status'] == 'not_rebound'
    assert records[0]['reason'] == 'fresh_physical_program_heterogeneous_cannot_split_retained_histogram'
    assert rebound['source_role_references'][0] is actual['source_role_references'][0]


def test_real_mc2_requires_native_index_dtype_not_shape_alone(retained_mc2):
    module, actual, manifest = retained_mc2
    group = deepcopy(actual['source_role_references'][0])
    group['source_correspondence']['observed_native_tensor_contract'][2][3][1] = 'int64'
    _, records = module.rebind_frozen_native_groups({**actual,'source_role_references':[group]}, manifest)
    assert records[0]['status'] == 'not_rebound'
    assert records[0]['reason'] == 'native_abi_no_longer_matches_declared_routed_roles'
