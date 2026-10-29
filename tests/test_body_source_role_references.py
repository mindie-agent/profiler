"""Descriptor-free V4.1 attention retains heterogeneous source-program groups."""
from collections import Counter
from dataclasses import replace
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/decode_forward'


@pytest.fixture(scope='module')
def captured_reference_groups():
    sim = pytest.importorskip('mindie_sim')
    from mindie_sim.structure import export_structure
    from mindie_sim.prediction.structure import parse_case
    from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.tensor_contracts import observed_contract
    import sys
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    helper = importlib.import_module('body_source_role_references')
    replay = importlib.import_module('replay_body_operator_families')
    path = Path(sim.__file__).resolve().parents[1] / 'examples/cases/high-concurrency-20261030/v41-dp8/a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1.json'
    if not path.exists():
        pytest.skip('source-bound V4.1 case requires companion Sim source checkout')
    case = parse_case(json.loads(path.read_text()))
    config = json.loads((FIXTURE / 'v41_dp8_model_config.json').read_text())
    manifest = export_structure(case, phase='decode', tokens=1, sequences=1, context=2048, scope='body')
    collector = helper.SourceRoleReferences(manifest, config)
    rows = list(kernel_rows(FIXTURE / 'v41_dp8_first_body.csv'))
    native = [row for row in rows if row.kind == 'MqsmlaKernel___call__']
    assert all(observed_contract(row) is None for row in native)
    callbacks = []
    def consume(forward, events):
        layers = [stage for stage in forward['stages'] if stage['layer_id'] is not None]
        for event in events:
            if event.op_type == 'MqsmlaKernel___call__':
                layer = next(stage for stage in layers if stage['start_ns'] <= event.start_ns < stage['end_ns'])
                assert collector.add(event, layer, 'attention') == 'attention_core'
                callbacks.append((event, layer))
    observed = auto_segment_decode_forwards(rows, config, on_forward=consume,
                max_detailed_forwards=0, max_samples_per_layer=0)
    assert observed['body_forward_span_ms']['count'] == 1
    return helper, replay, case, manifest, config, collector.finish(replay.duration_stats), callbacks


def test_real_na_attention_has_three_physical_subsets_without_tensor_or_layer_binding(captured_reference_groups):
    helper, replay, case, manifest, config, groups, callbacks = captured_reference_groups
    assert sorted(len(group['layer_ids']) for group in groups) == [2, 18, 20]
    assert sum(group['observed_us']['count'] for group in groups) == len(callbacks) == 40
    histogram = Counter()
    for group in groups:
        histogram.update(dict(group['duration_ns_counter']))
        assert group['tensor_contract'] is None
        assert not group['occurrence_binding_implied']
        assert not group['additional_budget_allowed']
        assert len(group['representative_target_ids']) == 1
    assert histogram == Counter(event.duration_ns for event, _ in callbacks)
    absent = helper.SourceRoleReferences(manifest, {**config, 'source_attention_anchors': []})
    event, layer = callbacks[0]
    assert absent.add(event, layer, 'attention') is None
    explicit = helper.SourceRoleReferences(manifest, config)
    assert explicit.add(event, layer, 'ffn') is None
    assert explicit.add(replace(event, name='different_source_symbol'), layer, 'attention') is None


def test_reference_cost_is_per_physical_group_and_does_not_use_measured_duration(captured_reference_groups):
    helper, replay, case, manifest, config, groups, callbacks = captured_reference_groups
    actual = {'forward_count': 1, 'source_role_references': groups}
    references = helper.predict_source_role_references(case, manifest, actual)
    changed = [dict(group, observed_us={**group['observed_us'], 'mean': 1}) for group in groups]
    second = helper.predict_source_role_references(case, manifest,
        {'forward_count': 1, 'source_role_references': changed})
    assert [row['predicted_reference_us'] for row in references] == [row['predicted_reference_us'] for row in second]
    assert all(row['prediction_status'] == 'reference_only' and 'accuracy_pass' not in row for row in references)
    assert len({row['physical_program_signatures'][0] for row in references}) == 3
    assert all(row['predicted_reference_us'] > 0 for row in references)
