"""Real A5 HCOM duplicates, PMU availability and layer-zero boundary evidence."""
import importlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/hccl'


@pytest.fixture
def ledger(monkeypatch):
    pytest.importorskip('mindie_sim')
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    return importlib.import_module('collect_a5_tp_hccl')


@pytest.mark.parametrize('batch,blocks,first_ns,second_ns,tensor_bytes', [
    (12,3,1278720,39713,491520), (96,63,2232822,127073,3932160)])
def test_actual_tp2_long_collective_is_after_gdn_output_not_embedding(ledger,batch,blocks,first_ns,second_ns,tensor_bytes):
    path = FIXTURE / f'qwen36_tp2_c{batch}_layer0.csv'
    rows = list(ledger.raw_stream(path,ledger.probe_csv(path)))
    events = [event for event,_ in rows]
    comm = [e for e in events if ledger.relevant(e)]
    retained,duplicates = ledger.deduplicate_communication(comm)
    assert len(duplicates) == 2
    assert [e.duration_ns for e in retained] == [first_ns,second_ns]
    first = retained[0]
    recurrent = next(e for e in events if e.op_type == 'RecurrentGatedDeltaRule')
    output = next(e for e in events if e.op_type == 'MatMulV3' and e.start_ns > recurrent.end_ns)
    ffn_norm = next(e for e in events if e.op_type == 'AddRmsNormDynamicQuant')
    assert events[0].op_type == 'Add' and events[1].op_type == 'RmsNorm'
    assert recurrent.end_ns <= output.start_ns < output.end_ns <= first.start_ns < first.end_ns <= ffn_norm.start_ns
    witness = ledger.tensor_witness(events,first,events[0].start_ns,5120)
    assert witness['tensor_bytes'] == tensor_bytes
    assert witness['measured_communication_payload'] is False
    pmu = ledger.NativePmu(ledger.probe_csv(path).header)
    for event,raw in rows:
        if event in retained:
            pmu.add(raw,event,forward_id=0,layer_id=0)
    result = pmu.result()
    assert dict(result['fields']['Block Num']['numeric_value_counter']) == {str(blocks):2}
    assert result['fields']['aiv_vec_time(us)']['zero_count'] == 2
    assert result['fields']['aiv_mte2_time(us)']['numeric_count'] == 2
    assert result['fields']['aic_mac_time(us)']['zero_count'] == 2


def test_actual_glm_envelopes_and_launches_are_not_temporal_parent_child_matches(ledger):
    path = FIXTURE / 'glm_flash_tp8_c16_hccl.csv'
    rows = list(ledger.raw_stream(path,ledger.probe_csv(path)))
    events = [event for event,_ in rows]
    retained,duplicates = ledger.deduplicate_communication(events)
    assert not duplicates
    assert [ledger.category(e) for e in retained].count('collective_envelope_only') == 2
    assert [ledger.category(e) for e in retained].count('unlinked_aicpu_wrapper') == 3
    pmu = ledger.NativePmu(ledger.probe_csv(path).header)
    for event,raw in rows:
        pmu.add(raw,event,forward_id=0,layer_id=0)
    fields = pmu.result()['fields']
    assert fields['aiv_mte2_time(us)']['missing_or_na_count'] == 5
    assert fields['aiv_mte2_time(us)']['zero_count'] == 0
