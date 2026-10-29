"""Actual retained ABI/topology examples for complete-body operator reporting."""
from collections import Counter
from dataclasses import replace
import importlib
import json
from pathlib import Path
from statistics import median

import pytest

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/decode_forward'


@pytest.fixture
def replay(monkeypatch):
    pytest.importorskip('mindie_sim.structure')
    monkeypatch.syspath_prepend(str(ROOT/'examples/structure'))
    return importlib.import_module('replay_body_operator_families')


def test_real_duplicate_hcom_summary_is_not_a_second_call(replay):
    rows=list(replay.kernel_rows(FIXTURE/'qwen36_a5_hcom_layer.csv'))
    events=[row.event for row in rows]
    retained,duplicates=replay.deduplicate_communication(events)
    assert duplicates
    assert all(event.task_id in {'','N/A','None'} or event.stream_id in {'','N/A','None'} for event in duplicates)
    for duplicate in duplicates:
        assert any(event.start_ns==duplicate.start_ns and event.end_ns==duplicate.end_ns
                   and event.op_type==duplicate.op_type for event in retained)
    assert replay.deduplicate_communication(retained)==(retained,[])
    # Unknown summary-only evidence remains visible, rather than being deleted.
    assert replay.deduplicate_communication(duplicates)==(duplicates,[])


def test_active_conv_projection_preserves_history_but_omits_pool_capacity(replay):
    from mindie_profiler.tensor_contracts import observed_contract
    row=next(row for row in replay.kernel_rows(FIXTURE/'qwen38_a5_hccl_launch_layer.csv') if row.kind=='CausalConv1d')
    before=observed_contract(row)
    active=replay.active_causal_contract(row)
    assert active and active[5][0]==row.input_shapes[3][-2:]
    pool=row.input_shapes[3]
    capacity=replace(row,input_shapes=(*row.input_shapes[:3],(pool[0]+100,*pool[1:]),*row.input_shapes[4:]))
    assert replay.active_causal_contract(capacity)==active
    assert observed_contract(row)==before
    history=replace(row,input_shapes=(*row.input_shapes[:3],(pool[0],pool[1]+1,pool[2]),*row.input_shapes[4:]))
    assert replay.active_causal_contract(history)!=active


def test_pooled_quantile_uses_call_multiplicity_not_median_of_layer_medians(replay):
    rows=list(replay.kernel_rows(FIXTURE/'qwen38_a5_hccl_launch_layer.csv'))
    durations=[row.event.duration_ns for row in rows if row.event.duration_ns>0]
    histogram=Counter(durations)
    actual=replay.duration_stats(histogram,1000)
    assert actual['count']==len(durations)
    assert actual['p50']==median(durations)/1000
    assert actual['mean']==pytest.approx(sum(durations)/len(durations)/1000)


def test_qwen_repeated_qkv_tensor_contract_is_refined_by_whole_layer_topology(replay):
    import mindie_sim
    from mindie_profiler.events import Observation,QueryStats,SourceRef,Window
    from mindie_profiler.tensor_contracts import observed_contract
    case=Path(mindie_sim.__file__).resolve().parents[1]/'examples/cases/high-concurrency-20261030/source-gdn/qwen36-a5-tp8-c4.json'
    if not case.exists():
        pytest.skip('case declarations require companion Sim source checkout')
    manifest=replay.export_structure(replay.read(case),phase='decode',tokens=4,sequences=4,context=4104,scope='body')
    mapper=replay.RoleMapper(manifest,mapping_limit=0,phase='decode')
    events=list(replay.kernel_rows(FIXTURE/'qwen36_a5_hcom_layer.csv',rank_id='rank_0'))
    row=next(row for row in events if row.kind=='QuantBatchMatmulV3' and row.input_shapes[0]==(16,5120))
    contract=observed_contract(row)
    candidates=mapper.contracts[replay._freeze(contract)]
    assert {'linear_qkvz','qkv'}<={replay.declared_role(mapper.targets[key]) for key in candidates}
    source=SourceRef('rank_0',0,'csv',str(FIXTURE/'qwen36_a3_verify.csv'),'fixture',None,0,'fixture','fixture')
    observation=Observation('rank_0',0,Window(row.event.start_ns,row.event.end_ns),None,[],source,QueryStats('rank_0','fixture'))
    mapper.layer,mapper.block=0,'attention'
    result=mapper.match(row.event,observation)
    assert {replay.declared_role(mapper.targets[key]) for key in result[2]}=={'linear_qkvz'}
    assert result[0] in {'candidate','ambiguous'}
    assert result[-1]['occurrence_binding_implied'] is False
