"""Actual A3 Kimi controller aliases, with A5 AIV/HCOM negative controls."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from mindie_profiler.decode_segmentation import (
    _Row, _scope, auto_segment_decode_forwards, is_aicpu_controller,
)
from mindie_profiler.normalized import kernel_rows, shapes

FIXTURE = Path(__file__).parent / 'fixtures'


def kimi():
    base = FIXTURE / 'decode_forward'
    events = [row.event for row in kernel_rows(base / 'a3_kimi4_c32_first_full_body.csv')]
    config = json.loads((base / 'a3_kimi4_c32_model_config.json').read_text())
    return events, config


def test_real_kimi_c32_alias_excludes_controller_activity_without_discarding_body_work():
    events, config = kimi()
    report = auto_segment_decode_forwards(events, config)
    assert report['body_forward_span_ms']['count'] == 1
    assert report['body_forward_span_ms']['mean'] == pytest.approx(6.646987)
    assert report['body_activity_ms']['mean'] == pytest.approx(6.519291)
    assert report['body_internal_gap_ms']['mean'] == pytest.approx(.127696)
    assert [layer['activity_ms_stats']['mean'] for layer in report['per_layer_ms']] == pytest.approx(
        [.760245, 1.882162, 1.762105, 2.114779])
    # The eight underscore aliases previously added 32,739ns to this union.
    alias = [event for event in events if event.op_type == 'reduce_scatterAicpuKernel']
    assert len(alias) == 8 and all(is_aicpu_controller(event) for event in alias)
    hcom = [event for event in events if event.op_type.startswith('hcom_')]
    assert hcom and not any(is_aicpu_controller(event) for event in hcom)


def test_real_controller_alias_obeys_successor_evidence_and_exporter_case():
    events, config = kimi()
    report = auto_segment_decode_forwards(events, config)
    layer = next(scope for scope in report['forwards'][0]['stages'] if scope['layer_id'] == 0)
    boundary = layer['evidence']['successor_boundary_start_ns']
    selected = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes))
                for event in events if layer['start_ns'] <= event.start_ns < boundary]
    successor_event = next(event for event in events if event.start_ns == boundary)
    successor = _Row(successor_event, shapes(successor_event.input_shapes), shapes(successor_event.output_shapes))
    tail = next(row for row in selected if row.kind == 'allgatherAicpuKernel'
                and row.event.end_ns > boundary)
    actual = _scope(selected, 'dense_layer', 'captured', successor=successor)
    # No successor evidence means the actual completion is still retained in span.
    no_boundary = _scope(selected, 'dense_layer', 'retained')
    assert no_boundary['end_ns'] >= tail.event.end_ns > actual['end_ns']
    changed = _Row(replace(tail.event, op_type='ALL_GATHER_AICPU_KERNEL'), tail.inputs, tail.outputs)
    equivalent = _scope([changed if row is tail else row for row in selected], 'dense_layer', 'alias', successor=successor)
    assert equivalent['end_ns'] == actual['end_ns']
    assert equivalent['device_activity_union_ms'] == actual['device_activity_union_ms']
    # A recorded device/data-plane type must not be discarded just for its name.
    assert not is_aicpu_controller(replace(tail.event, core='COMMUNICATION', task_type='COMMUNICATION'))


def test_real_aiv_and_hcom_aicpu_suffix_are_not_scheduler_aliases():
    aiv = [row.event for row in kernel_rows(FIXTURE / 'hccl/qwen36_tp2_c12_layer0.csv')]
    glm = [row.event for row in kernel_rows(FIXTURE / 'hccl/glm_flash_tp8_c16_hccl.csv')]
    concrete = [event for event in aiv if event.name == 'AivKernel']
    envelope = [event for event in glm if event.op_type == 'hcom_allReduce_AicpuKernel']
    assert concrete and envelope
    for event in [*concrete, *envelope]:
        assert not is_aicpu_controller(event)
        row = _Row(event, shapes(event.input_shapes), shapes(event.output_shapes))
        result = _scope([row], 'dense_layer', 'actual_data_plane')
        assert result['device_activity_union_ms'] == event.duration_ns / 1e6
        assert result['end_ns'] == event.end_ns
