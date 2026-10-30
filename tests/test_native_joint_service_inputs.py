"""Complete real SFA populations pool by physical domain, not case labels."""
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from prepare_native_joint_service_inputs import pooled_population


def populations():
    return json.loads((ROOT/'tests/fixtures/grouped_micro/native_joint_sfa.json').read_text())['rows']


def test_two_same_abi_captures_pool_full_histograms_not_summary_medians():
    rows=populations();pooled=pooled_population(rows[:2]);observed=pooled['observed_native_elapsed_us']
    assert observed['count']==6864
    assert observed['mean_us']==pytest.approx(95.7641016899767)
    assert observed['p50_us']==95.082
    assert pooled['parameter_unit']=='us/native_call'
    assert pooled['api_binding'] is None
    assert len(pooled['source_populations'])==2
    assert sum(r['forward_count'] for r in pooled['source_populations'])==88


def test_actual_b8_query_and_blocktable_shape_cannot_pool_with_b2():
    rows=populations()
    assert rows[0]['applicability_domain']['native_abi']!=rows[2]['applicability_domain']['native_abi']
    with pytest.raises(ValueError,match='different_native_domains'):
        pooled_population([rows[0],rows[2]])
