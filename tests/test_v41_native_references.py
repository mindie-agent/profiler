"""Real complete-body V4.1 ABI populations and source-role accounting."""
from collections import Counter
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
PARTITIONS=ROOT/'examples/structure/acceptance-20261030-v41-native-partitions'


@pytest.fixture(scope='module')
def evidence():
    structure=pytest.importorskip('mindie_sim.structure')
    from mindie_sim.prediction.structure import parse_case
    sys.path.insert(0,str(ROOT/'examples/structure'))
    helper=importlib.import_module('v41_native_references')
    data=json.loads((PARTITIONS/'a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1-native-partitions.json').read_text())
    case=parse_case(json.loads(Path(data['case_identity']['path']).read_text()))
    manifest=structure.export_structure(case,phase='decode',tokens=1,sequences=1,context=2048,scope='body')
    return helper,data,manifest


def test_all_saved_native_histograms_and_complete_layer_memberships_are_preserved():
    total=Counter();forwards=0
    for path in PARTITIONS.glob('*-native-partitions.json'):
        data=json.loads(path.read_text());actual=json.loads(Path(data['actual_identity']['path']).read_text())
        observed={kind:Counter() for kind in data['selected_native_types']}
        for group in data['partitions']:
            observed[group['native_operator_type']].update(dict(group['duration_ns_counter']))
            assert sum(group['layer_counts'].values())==sum(group['forward_counts'].values())==group['observed_us']['count']
        for kind,hist in observed.items():
            expected=Counter()
            for family in actual['families']:
                if family['native_operator_type']==kind:expected.update(dict(family['duration_ns_counter']))
            assert hist==expected
            total[kind]+=sum(hist.values())
        forwards+=data['forward_count']
    assert forwards==830
    assert total=={'TransposeQuantBatchMatMul':33200,'InplacePartialRotaryMul':112880,'KvCompressEpilogV2':36520}


def test_output_matrix_and_cache_reference_do_not_duplicate_atomic_rotary(evidence):
    helper,data,manifest=evidence
    refs,unresolved,compact=helper.prepare_references(data,manifest)
    output=[row for row in refs if row['declared_role']=='grouped_output_a']
    assert len(output)==1 and output[0]['layer_ids']==list(range(40))
    assert output[0]['observed_us']['count']==6080
    assert output[0]['source_correspondence']['input_quantization_is_separate_native_call']
    reasons=Counter(row['reason'] for row in unresolved)
    if any(node['op_id'].endswith('.rotary') for node in manifest['nodes']):
        assert all(row['declared_role'] not in {'q_rotary','kv_rotary'} for row in refs)
        assert reasons['combined_q_kv_program_cannot_be_split_or_reused:q_rotary']==40
        assert reasons['combined_q_kv_program_cannot_be_split_or_reused:kv_rotary']==40
    if not any(node['op_id'].endswith('.output_inverse_rotary') for node in manifest['nodes']):
        assert all(row['declared_role']!='output_inverse_rotary' for row in refs)
        assert reasons['declared_semantic_program_missing:output_inverse_rotary']==40
    assert sum(row['observed_us']['count'] for row in refs)+sum(row['event_count'] for row in unresolved)==33440
    assert all(row['additional_budget_allowed'] is False and row['reference_only'] for row in refs)
    for row in refs:
        if row['declared_role'].endswith('store'):
            assert row['source_correspondence']['observed_valid_write_rows'] is None
            assert not row['source_correspondence']['cache_capacity_is_active_context']


def test_full_native_scale_format_and_whole_layer_region_are_required(evidence):
    helper,data,manifest=evidence
    source=next(row for row in data['partitions'] if row['native_operator_type']=='TransposeQuantBatchMatMul')
    changed=deepcopy(source);changed['native_abi'][2][2][2]='ND'
    with pytest.raises(ValueError,match='transpose_quant_native_mx_abi'):
        helper.classify(changed,manifest['execution'])
    rotary=deepcopy(next(row for row in data['partitions'] if row['native_operator_type']=='InplacePartialRotaryMul' and row['topology_region']=='after_attention_anchor'))
    assert helper.classify(rotary,manifest['execution'])[0]=='output_inverse_rotary'
    rotary['topology_region']='before_attention_anchor'
    assert helper.classify(rotary,manifest['execution'])[0]=='q_rotary'


@pytest.fixture(scope='module')
def source_rotary_evidence(evidence):
    helper,data,_=evidence
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    raw=json.loads(Path(data['case_identity']['path']).read_text())
    raw['runtime']['kernels'].setdefault('lowerings',{})['v41_rotary']='v41_partial_rotary'
    manifest=export_structure(parse_case(raw),phase='decode',tokens=1,sequences=1,context=2048,scope='body')
    return helper,data,manifest


def test_source_rotary_accounts_for_three_distinct_real_calls_without_aggregate_reuse(source_rotary_evidence):
    helper,data,manifest=source_rotary_evidence
    refs,unresolved,_=helper.prepare_references(data,manifest)
    assert not unresolved
    assert sum(row['observed_us']['count'] for row in refs)==data['native_event_count']==33440
    selected=[r for r in refs if r['declared_role'] in {'q_rotary','kv_rotary','output_inverse_rotary'}]
    assert {r['declared_role'] for r in selected}=={'q_rotary','kv_rotary','output_inverse_rotary'}
    assert sum(r['observed_us']['count'] for r in selected)==152*120
    assert len({node for r in selected for node in r['representative_target_ids']})==3
    for r in selected:
        relation=r['source_correspondence'];view=relation['declared_native_tensor_view']
        assert relation['native_source_program_selected']
        assert view['inverse']==(r['declared_role']=='output_inverse_rotary')
        assert relation['declared_partial_rotary_work']['untouched_nope_elements']>0
        assert r['reference_only'] and not r['additional_budget_allowed']


def test_real_inverse_call_rejects_forward_coefficients_or_wrong_partial_slice(source_rotary_evidence):
    helper,data,manifest=source_rotary_evidence
    group=next(g for g in data['partitions'] if g['native_operator_type']=='InplacePartialRotaryMul'
               and g['topology_region']=='after_attention_anchor')
    layer=int(next(iter(group['layer_counts'])))
    local=[n for n in manifest['nodes'] if n['replica']==0 and n['layer']==layer]
    target=next(n for n in local if n['op_id'].endswith('.output_inverse_rotary'))
    for field,bad in [('inverse',False),('partial_slice',[0,64]),('coefficient_dtype','bf16')]:
        changed=deepcopy(target);changed['operator']['metadata']['native_tensor_view'][field]=bad
        with pytest.raises(ValueError,match='declared_partial_rotary_native_view_differs'):
            helper.select(group,[changed],manifest['execution'])
