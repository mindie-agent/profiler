"""Descriptor-free V4.1 attention retains heterogeneous source-program groups."""
from collections import Counter
from dataclasses import replace
import importlib
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

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
    helper = importlib.import_module('references')
    replay = importlib.import_module('operators')
    path = case_path('a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1.json')
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


@pytest.fixture(scope='module')
def captured_native_component_groups(captured_reference_groups):
    helper, replay, case, manifest, config, _, _ = captured_reference_groups
    from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
    from mindie_profiler.normalized import kernel_rows
    from mindie_profiler.events import SourceRef, Observation, QueryStats, Window
    rows = list(kernel_rows(FIXTURE / 'v41_dp8_first_body.csv'))
    forwards = []
    auto_segment_decode_forwards(rows, config, on_forward=lambda forward, events: forwards.append((forward, events)))
    assert len(forwards) == 1
    forward, events = forwards[0]
    source = SourceRef('rank_0', 0, 'csv', str(FIXTURE / 'v41_dp8_first_body.csv'),
                       'retained_fixture', None, 0, 'fixture', 'fixture')
    observation = Observation('rank_0', 0, Window(forward['start_ns'], forward['end_ns']),
                              None, [], source, QueryStats('rank_0', 'fixture'))
    consumer = replay.BodyConsumer(manifest, observation, {forward['forward_id']: forward}, config)
    consumer(forward, events)
    mapping, families, _ = consumer.finish(manifest)
    groups = consumer.source_roles.finish(replay.duration_stats)
    return helper, case, manifest, mapping, families, groups


def test_real_native_component_references_keep_capacity_and_program_boundaries(captured_native_component_groups):
    helper, case, manifest, mapping, families, groups = captured_native_component_groups
    by_role = {}
    for group in groups:
        by_role.setdefault(group['declared_role'], []).append(group)
    for role, calls in [('expert_up', 40), ('expert_down', 40), ('attention.hc_pre', 40),
                        ('ffn.hc_pre', 40), ('expert_dispatch_native', 40), ('expert_combine_native', 40)]:
        assert sum(group['observed_us']['count'] for group in by_role[role]) == calls
    up, down = by_role['expert_up'][0], by_role['expert_down'][0]
    for group in (up, down):
        relation = group['source_correspondence']
        assert relation['observed_buffer_row_capacity'] == 48
        assert relation['declared_valid_routed_rows'] == 6
        assert relation['observed_valid_routed_rows'] is None
        assert relation['boundary_relation'] == 'capacity_vs_valid_rows_conditional'
    assert up['representative_target_ids'] != down['representative_target_ids']
    dispatch = by_role['expert_dispatch_native'][0]['representative_target_ids']
    combine = by_role['expert_combine_native'][0]['representative_target_ids']
    assert {name.rsplit('/', 1)[-1].split('.', 2)[-1] for name in dispatch} == {
        'pack', 'dispatch', 'expert_up.quantize'}
    assert {name.rsplit('/', 1)[-1].split('.', 2)[-1] for name in combine} == {'combine', 'unpack'}
    assert not set(dispatch) & set(combine)
    assert all(group['source_correspondence']['boundary_relation'].startswith('partial_base_program_')
               for role in ('attention.hc_pre', 'ffn.hc_pre') for group in by_role[role])
    # HcPost already has a full tensor cohort; references must not double count it.
    assert not any(group['native_operator_type'] == 'HcPost' for group in groups)
    assert sum(row['observed_us']['count'] for row in families if row['native_operator_type'] == 'HcPost') == 80


def test_native_multi_program_cost_uses_complete_dp_collective(captured_native_component_groups):
    helper, case, manifest, mapping, families, groups = captured_native_component_groups
    roles = {'expert_dispatch_native', 'expert_combine_native', 'attention.hc_pre', 'expert_up'}
    selected = []
    for group in groups:
        if group['declared_role'] in roles:
            selected.append(group)
            roles.remove(group['declared_role'])
    references = helper.predict_source_role_references(case, manifest,
        {'forward_count': 1, 'source_role_references': selected})
    assert len(references) == 4 and all(row['predicted_reference_us'] > 0 for row in references)
    assert all('accuracy_pass' not in row and not row['additional_budget_allowed'] for row in references)
    assert all(row['boundary'] == 'complete_collective_cohort_program_set_reference'
               for row in references if row['declared_role'].startswith('expert_') and 'native' in row['declared_role'])


def test_compact_reference_graph_preserves_full_graph_cost_and_all_dp_peers(
        captured_native_component_groups, monkeypatch):
    helper, case, manifest, mapping, families, groups = captured_native_component_groups
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.prediction.program import RecipeBook
    roles = {'expert_dispatch_native', 'expert_combine_native', 'attention.hc_pre', 'expert_up'}
    selected = []
    for group in groups:
        if group['declared_role'] in roles:
            selected.append(group)
            roles.remove(group['declared_role'])
    actual = {'forward_count': 1, 'source_role_references': selected}
    execution = manifest['execution']
    geometry = {key: execution[key] for key in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    book = RecipeBook.from_mapping(case.runtime.kernels)
    full = target_graphs(case, **geometry)
    compact = helper._reference_graphs(full, book, selected)
    ids = {key.split('/', 1)[1] for group in selected for key in group['representative_target_ids']}
    assert compact.keys() == full.keys() and len(compact) == 8
    for replica in full:
        expected = tuple(op for op in book.expand(full[replica]) if op.op_id in ids)
        assert compact[replica] == expected
        assert len(compact[replica]) < len(full[replica]) // 10
    optimized = helper.predict_source_role_references(case, manifest, actual)
    # The control keeps every real expanded layer, as before the memory change.
    # It uses the same source graphs and cost engine, with no fabricated payloads.
    monkeypatch.setattr(helper, '_reference_graphs', lambda graphs, book, groups: {
        replica: book.expand(ops) for replica, ops in graphs.items()})
    control = helper.predict_source_role_references(case, manifest, actual)
    assert optimized == control


def test_partial_hcpre_does_not_discard_observed_output_leading_axes(captured_reference_groups):
    helper, replay, case, manifest, config, _, _ = captured_reference_groups
    from mindie_profiler.normalized import kernel_rows
    row = next(row for row in kernel_rows(FIXTURE / 'v41_dp8_first_body.csv') if row.kind == 'HcPre')
    layer = {'layer_id': 0, 'attention': 'mla'}
    collector = helper.SourceRoleReferences(manifest, config)
    assert collector.add(row.event, layer, 'attention') == 'attention.hc_pre'
    changed = row.event.output_shapes.replace('1,5120', '2,5120', 1)
    assert changed != row.event.output_shapes
    assert collector.add(replace(row.event, output_shapes=changed), layer, 'attention') is None
