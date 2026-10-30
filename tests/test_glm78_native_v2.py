"""Real retained GLM78 V2 tensors protect typed source-caller boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'examples/structure'))
from check_glm78_native_v2 import check_retained_v2


@pytest.fixture(scope='module')
def native():
    root = ROOT/'examples/structure/acceptance-20261030-service-qwen-a3/glm78-native'
    return {suffix: json.loads((root/f'a3_glm53_w4a8_tp16_tpot{suffix}-native-partitions.json').read_text())
            for suffix in ('30_c2', '88_c8')}


def test_c2_right_pad_and_native_quantized_payload_chain(native):
    checked = check_retained_v2(native['30_c2'], tp=16, ep=16, hidden=6144, experts=256)
    g = checked['source_caller_geometry']
    assert (g['global_query_rows'], g['right_padded_rows'], g['tp_local_rows']) == (12, 16, 1)
    assert g['expert_buffer_capacity_rows'] == 128 and g['expert_valid_rows'] is None
    assert checked['calls_per_native_per_forward'] == 75
    assert len(checked['materialized_right_pad']) == 2
    links = {x['role']: x for x in checked['typed_links']}
    assert links['dynamic_activation_scale']['output_slot'] == 1
    assert links['expand_combine_scales']['output_slot'] == 6
    assert links['expand_combine_scales']['input_slot'] == 10
    assert links['fused_swiglu_dynamic_scale']['input_slot'] == 8


def test_c8_capacity_is_not_tp_local_work_or_gather_output(native):
    checked = check_retained_v2(native['88_c8'], tp=16, ep=16, hidden=6144, experts=256)
    g = checked['source_caller_geometry']
    assert (g['global_query_rows'], g['right_padded_rows'], g['tp_local_rows']) == (48, 48, 3)
    assert g['expert_buffer_capacity_rows'] == 384 and g['expert_valid_rows'] is None
    assert checked['materialized_right_pad'] == []
    assert checked['tp_finalization']['source_payload_bytes_per_rank'] == 3*6144*2
    assert checked['tp_finalization']['unpad_output_shape'] == [48, 6144]


def test_wrong_gmm_row_scale_dtype_cannot_satisfy_dispatch_contract(native):
    actual = deepcopy(native['30_c2'])
    up = next(p for p in actual['partitions'] if p['native_operator_type'] == 'GroupedMatmulSwigluQuantV2')
    up['native_abi'][2][1][1] = 'bf16'
    with pytest.raises(ValueError, match='dynamic_activation_scale_producer_consumer_contract_mismatch'):
        check_retained_v2(actual, tp=16, ep=16, hidden=6144, experts=256)


def test_combine_must_consume_distinct_expand_scale_slot(native):
    actual = deepcopy(native['88_c8'])
    combine = next(p for p in actual['partitions'] if p['native_operator_type'] == 'MoeDistributeCombineV2')
    combine['native_abi'][2][10] = [[], None, None]
    with pytest.raises(ValueError, match='expand_combine_scales_producer_consumer_contract_mismatch'):
        check_retained_v2(actual, tp=16, ep=16, hidden=6144, experts=256)
