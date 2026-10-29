"""Real HCOM scope/dedup evidence and incompatible declared program buckets."""
import importlib
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def communication(monkeypatch):
    pytest.importorskip('mindie_sim.structure')
    monkeypatch.syspath_prepend(str(ROOT/'examples/structure'))
    return importlib.import_module('replay_body_communication')


def test_real_layer_hcom_preserves_peer_wait_excludes_embedding_and_wrapper(communication):
    events=[row.event for row in communication.kernel_rows(ROOT/'tests/fixtures/decode_forward/qwen36_a5_hcom_layer.csv')]
    norm=next(i for i,event in enumerate(events) if event.op_type=='RmsNorm')
    successor=next(i for i,event in enumerate(events) if event.op_type=='AddRmsNorm')
    layer={'layer_id':0,'attention':'gdn','start_ns':events[norm-1].start_ns,
           'evidence':{'successor_boundary_start_ns':events[successor-1].start_ns}}
    end=max(event.end_ns for event in events[norm-1:successor-1])
    result={'start_ns':layer['start_ns'],'end_ns':end,'stages':[layer]}
    rows,duplicates=communication.communication_regions(result,events,{'hidden_size':5120,'layer_plans':[{'index':0,'attention':'gdn'}]})
    assert duplicates==2
    assert [(event.duration_ns,block) for event,_,block in rows]==[(6_284_378,'attention'),(23_489,'ffn')]
    assert all(event.task_id not in {'','N/A','None'} for event,_,_ in rows)


def test_gdn_and_gqa_collectives_retain_distinct_programs_despite_equal_link_bytes(communication):
    import mindie_sim
    case=Path(mindie_sim.__file__).resolve().parents[1]/'examples/cases/high-concurrency-20261030/source-gdn/qwen36-a5-tp8-c4.json'
    if not case.exists():pytest.skip('companion Sim source declarations required')
    manifest=communication.export_structure(communication.read(case),phase='decode',tokens=4,sequences=4,context=4104,scope='body')
    programs=communication.declared_programs(manifest)
    gdn,gqa=programs[0,'attention'],programs[3,'attention']
    assert len(gdn)==len(gqa)==1
    assert gdn[0]['physical_work']['link_bytes']==gqa[0]['physical_work']['link_bytes']
    assert gdn[0]['physical_signature']!=gqa[0]['physical_signature']
    assert communication.declared_role(gdn[0])=='linear_reduce'
    assert communication.declared_role(gqa[0])=='tp_attn'
