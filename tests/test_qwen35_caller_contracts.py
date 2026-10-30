"""Real packed INT8 caller ABI, typed scale edges and copy-region regressions."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def evidence():
    sim=pytest.importorskip('mindie_sim')
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    sys.path.insert(0,str(ROOT/'examples/structure'))
    helper=importlib.import_module('qwen35_caller_contracts')
    part=json.loads((ROOT/'tests/fixtures/structure/qwen35-tp4-int8-caller.json').read_text())
    case_path=Path(sim.__file__).resolve().parents[1]/'examples/cases/high-concurrency-20261030/qwen35-mc2-tp-source-complete-conditional/qwen35-35b-a5-tp4-c128-mc2-tp-source-complete.json'
    if not case_path.exists():pytest.skip('companion source case unavailable')
    manifest=export_structure(parse_case(json.loads(case_path.read_text())),phase='decode',tokens=4,sequences=128,context=4096,scope='body')
    return helper,part,manifest


def test_packed_INT8_up_INT32_and_down_scale_preserve_capacity(evidence):
    h,part,_=evidence
    groups=[p for p in part['partitions'] if p['native_operator_type']=='GroupedMatmul']
    up,down=[h.grouped_contract(g['native_abi']) for g in groups]
    assert up==('grouped_matrix',(64,4096,1024,2048),'int8','int8','int32',(),'')
    assert down==('grouped_matrix',(64,4096,2048,512),'int8','int8','bf16',(4096,),'fp32')
    changed=deepcopy(groups[1]['native_abi']);changed[2][8][1]='bf16'
    assert h.grouped_contract(changed) is None
    changed=deepcopy(groups[0]['native_abi']);changed[3][0][1]='bf16'
    assert h.grouped_contract(changed) is None


def test_full_typed_chain_requires_received_and_activation_owned_scales(evidence):
    h,_,manifest=evidence
    audit=h.audit_typed_chain(manifest)
    assert audit['layer_count']==40
    assert all(r['router_shared_rows']==512 and r['topk_source_rows']==128 and
               r['declared_valid_routed_rows']==1024 and r['FFN_materialization_calls']==4 for r in audit['layers'])
    changed=deepcopy(manifest)
    node=next(n for n in changed['nodes'] if n['op_id']=='s0.l3.expert_down')
    node['operator']['metadata']['activation_scale_producer']='s0.l3.dispatch'
    with pytest.raises(ValueError,match='down_requires_activation_owned'):
        h.audit_typed_chain(changed)


def test_native_scale_and_dispatch_outputs_are_complete_not_shape_hints(evidence):
    h,part,manifest=evidence
    local=[n for n in manifest['nodes'] if n.get('layer')==0]
    for kind in ('DequantSwigluQuant','MoeDistributeDispatchV3'):
        p=next(p for p in part['partitions'] if p['native_operator_type']==kind)
        role,_,correspondence=h.select(h.freeze(p['native_abi']),p,local)
        assert role in ('expert_act','dispatch')
        assert correspondence['observed_buffer_row_capacity']==4096
        assert correspondence['declared_valid_routed_rows']==1024
        assert correspondence['observed_valid_routed_rows'] is None
        changed=deepcopy(p['native_abi']);changed[3][-1][1]='bf16'
        with pytest.raises(ValueError):h.select(h.freeze(changed),p,local)


def test_FFN_copies_do_not_consume_attention_layout_moves(evidence):
    h,part,manifest=evidence
    local=[n for n in manifest['nodes'] if n.get('layer')==0]
    copies=[p for p in part['partitions'] if p['native_operator_type']=='TensorMove']
    for p in copies:
        if p['topology_region']!='ffn':
            with pytest.raises(ValueError,match='attention_layout_copy_not_reclassified'):
                h.select(h.freeze(p['native_abi']),p,local)
        else:
            role,nodes,_=h.select(h.freeze(p['native_abi']),p,local)
            assert role=='post_gather_materialization' and len(nodes)==1
            assert nodes[0]['contract']==p['native_abi']
    assert len([p for p in copies if p['topology_region']=='ffn'])==4


def test_topk_third_output_stays_partial_boundary(evidence):
    h,part,manifest=evidence
    p=next(p for p in part['partitions'] if p['native_operator_type']=='MoeGatingTopK')
    _,nodes,evidence=h.select(h.freeze(p['native_abi']),p,[n for n in manifest['nodes'] if n.get('layer')==0])
    assert evidence['partial_work_boundary'] and evidence['observed_third_output_modeled'] is False
    assert nodes[0]['contract'] is None


def test_complete_FFN_materialization_cohort_keeps_attention_copies_unscored(evidence):
    _,_,manifest=evidence
    from reprice_kimi_matrix_partitions import matrix_mapping
    base=ROOT/'examples/structure/acceptance-20261030-qwen35-source-complete'
    part=json.loads((base/'tensor-move-contracts/qwen35-35b-a5-tp4-c128-graph-native-partitions.json').read_text())
    old=ROOT/'examples/structure/acceptance-20261030-qwen-source-native-operators/retained-six-actual/body-operator-qwen35-35b-a5-tp4-c128-graph-qwen-source-gdn-native.mapping.json'
    cohorts,_,families,decisions=matrix_mapping(part,json.loads(old.read_text()),manifest,'TensorMove')
    assert len(cohorts)==1 and cohorts[0]['event_count']==76*160
    assert cohorts[0]['declared_instance_count']==40*4
    assert sum(d['event_count'] for d in decisions if not d['eligible'])==76*60
    assert sum(f['observed_us']['count'] for f in families)==76*220
