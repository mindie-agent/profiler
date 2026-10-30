"""Real A3 fused routed-FFN ABI retains one conditional, nonduplicated boundary."""
from collections import Counter
from dataclasses import replace
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/native_body_contracts/v41_a3_dispatch_ffn_combine.csv'


@pytest.fixture(scope='module')
def mc2_reference():
    sim = pytest.importorskip('mindie_sim')
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    from mindie_profiler.normalized import kernel_rows
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    helper = importlib.import_module('references')
    replay = importlib.import_module('operators')
    path = Path(sim.__file__).resolve().parents[1] / 'examples/cases/high-concurrency-20261030/v41-new6/a3_v41_w8a8_tp4_dp4_ep16_dspark7_c4.json'
    if not path.exists():
        pytest.skip('requires the source-bound A3 V4.1 declaration')
    case = parse_case(json.loads(path.read_text()))
    assert case.runtime.parallel.tp == case.runtime.parallel.dp == 4
    assert case.model.quant.expert_weight_format == 'int8'
    manifest = export_structure(case, phase='decode', tokens=8, sequences=1, context=2048, scope='body')
    row = next(kernel_rows(FIXTURE))
    collector = helper.SourceRoleReferences(manifest, case.model.to_dict())
    assert collector.add(row.event, {'layer_id': 0, 'attention': 'mla'}, 'ffn') == 'routed_ffn_native'
    groups = collector.finish(replay.duration_stats)
    return helper, case, manifest, row, groups


def test_fused_mc2_reference_owns_only_routed_ffn_and_preserves_capacity(mc2_reference):
    helper, case, manifest, row, groups = mc2_reference
    assert len(groups) == 1
    group = groups[0]
    names = {name.split('/', 1)[1].split('.', 2)[-1] for name in group['representative_target_ids']}
    assert names == {'pack', 'dispatch', 'expert_up.quantize', 'expert_up', 'expert_act',
                     'expert_down.quantize', 'expert_down', 'combine', 'unpack'}
    relation = group['source_correspondence']
    assert relation['observed_buffer_row_capacity'] == 64
    assert relation['observed_active_token_rows'] is None
    assert relation['declared_valid_routed_rows'] == 12
    assert not relation['native_fusion_cost_established']
    assert not group['additional_budget_allowed']
    assert dict(group['duration_ns_counter']) == Counter({row.duration_ns: 1})
    changed = row.event.input_dtypes.replace('DT_INT32', 'DT_INT64', 1)
    if changed == row.event.input_dtypes:
        changed = row.event.input_dtypes.replace('INT32', 'INT64', 1)
    assert changed != row.event.input_dtypes
    collector = helper.SourceRoleReferences(manifest, case.model.to_dict())
    assert collector.add(replace(row.event, input_dtypes=changed), {'layer_id': 0, 'attention': 'mla'}, 'ffn') is None
    assert collector.add(row.event, {'layer_id': 0, 'attention': 'mla'}, 'attention') is None


def test_native_mc2_prices_one_complete_collective_graph_not_summed_dp_costs(mc2_reference):
    helper, case, manifest, row, groups = mc2_reference
    result = helper.predict_source_role_references(case, manifest,
        {'forward_count': 1, 'source_role_references': groups})
    assert len(result) == 1
    reference = result[0]
    assert reference['predicted_reference_us'] > 0
    assert reference['boundary'] == 'complete_collective_cohort_program_set_reference'
    assert reference['prediction_status'] == 'reference_only'
    assert 'accuracy_pass' not in reference
    assert len(reference['declared_programs']) == 9
    assert reference['observed_activity_ms_per_forward'] == row.duration_ns / 1e6
