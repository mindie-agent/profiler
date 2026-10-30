"""Real capture-scope inventories preserve controller aliases and duplicate rows."""
import importlib
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def collector(monkeypatch):
    pytest.importorskip('mindie_sim')
    monkeypatch.syspath_prepend(str(ROOT/'examples/structure'))
    return importlib.import_module('collect_capture_hccl')


def inventory(collector,path):
    schema=collector.probe_csv(path);result=collector.Inventory(schema.header)
    for event,raw in collector.raw_stream(path,schema):result.add(event,raw)
    return result.finish()


def test_capture_inventory_keeps_summary_rows_separate_from_concrete_aiv(collector):
    groups=inventory(collector,ROOT/'tests/fixtures/hccl/qwen36_tp2_c12_layer0.csv')
    assert sum(g['observed_us']['count'] for g in groups)==4
    by={g['event_category']:g for g in groups}
    assert by['collective_device_task']['observed_us']['count']==2
    assert by['collective_envelope_only']['observed_us']['count']==2
    assert by['collective_device_task']['raw_pmu']['fields']['aiv_mte2_time(us)']['numeric_count']==2
    assert by['collective_envelope_only']['raw_pmu']['fields']['aiv_mte2_time(us)']['missing_or_na_count']==2
    assert all(not g['can_add_to_other_categories'] for g in groups)


def test_actual_a3_underscore_controller_and_native_mc2_remain_separate(collector):
    groups=inventory(collector,ROOT/'tests/fixtures/decode_forward/a3_kimi4_first_decode.csv')
    by={g['native_operator_type']:g for g in groups}
    alias=by['reduce_scatterAicpuKernel'];envelope=by['hcom_reduceScatter_']
    assert alias['observed_us']['count']==envelope['observed_us']['count']==8
    assert alias['event_category']=='unlinked_aicpu_wrapper'
    assert envelope['event_category']=='collective_envelope_only'
    assert by['MoeDistributeDispatchV2']['event_category']=='native_fused_communication_program'
    assert by['MoeDistributeDispatchV2']['observed_us']['count']==3
    assert alias['raw_pmu']['fields']['Block Num']['zero_count']==8
    assert alias['raw_pmu']['fields']['aiv_mte2_time(us)']['missing_or_na_count']==8


def test_staged_real_csv_does_not_claim_its_enclosing_directory_is_a_capture(collector):
    source=ROOT/'tests/fixtures/hccl/qwen36_tp2_c12_layer0.csv'
    result=collector.adjacent_inventory(source)
    assert result['files']==[{'path':str(source),'size_bytes':source.stat().st_size}]
    assert result['separate_associated_artifact_ledger']=='associated-artifacts.json'
