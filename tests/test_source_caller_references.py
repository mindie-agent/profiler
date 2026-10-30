"""Real retained populations exercise source-caller reference boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from source_caller_references import prepare_callers, prepare_hccl


def read(path):
    return json.loads((ROOT/path).read_text())


def glm_inputs():
    actual=read('examples/structure/acceptance-20261030-glm-operators-09811dad/body-operator-a5_glm53flash_tp8_c64_p4k-glm-flash-ws9.actual.json')
    manifest=read('tests/fixtures/source_callers/glm64-programs.json')['manifest']
    return actual,manifest


def qwen_inputs():
    ledger=read('examples/structure/acceptance-20261030-a5-tp-hccl/qwen36-a5-tp2-c1-hccl-ledger.json')
    manifest=read('tests/fixtures/source_callers/qwen36-c1-programs.json')['manifest']
    return ledger,manifest


def test_real_copy_pair_keeps_complete_pool_without_direction_or_tensor_invention():
    actual,manifest=glm_inputs();refs,failures,costs,compact=prepare_callers(actual,manifest)
    assert not failures
    copy=next(r for r in refs if r['native_operator_type']=='_copy_conv_state_kernel')
    prior=next(f for f in actual['families'] if f['native_operator_type']=='_copy_conv_state_kernel')
    assert copy['duration_ns_counter']==prior['duration_ns_counter']
    assert copy['observed_us']['count']==31*34*2
    assert [c['weight'] for c in copy['cost_components']]==[.5,.5]
    assert copy['native_abi'] is None and not copy['strict_accuracy_implied']
    used={c['program_set_key'] for c in copy['cost_components']}
    selected={key for c in costs if c['program_set_key'] in used for key in c['representative_target_ids']}
    nodes=[n for n in compact['nodes'] if n['node_id'] in selected]
    assert {n['operator']['metadata']['direction'] for n in nodes}=={'gather','scatter'}
    assert all(n['family']=='conv_state_copy' for n in nodes)
    captured=read('tests/fixtures/source_callers/glm64-retained-rows.json')['rows']
    copy_rows=[r for r in captured if r['raw']['Type']=='_copy_conv_state_kernel']
    assert all(r['raw']['Input Shapes']==r['raw']['Output Shapes']=='N/A' for r in copy_rows)


def test_copy_population_or_physical_work_drift_cannot_be_hidden_by_pooled_mean():
    actual,manifest=glm_inputs()
    copy=next(f for f in actual['families'] if f['native_operator_type']=='_copy_conv_state_kernel')
    copy['structure_groups'][0]['observed_us']['count']-=1
    refs,failures,_,_=prepare_callers(actual,manifest)
    assert not any(r['native_operator_type']=='_copy_conv_state_kernel' for r in refs)
    assert failures[0]['reason']=='retained_calls_do_not_match_declared_caller_multiplicity'
    actual,manifest=glm_inputs();next(n for n in manifest['nodes'] if n['layer']==1 and n['family']=='conv_state_copy')['physical_work']['hbm_bytes']+=1
    refs,failures,_,_=prepare_callers(actual,manifest)
    assert not any(r['native_operator_type']=='_copy_conv_state_kernel' for r in refs)
    assert failures[0]['reason']=='heterogeneous_layer_work_saved_histogram_not_splittable'


def test_routing_reference_uses_all_native_calls_not_two_examples_as_full_abi():
    actual,manifest=glm_inputs();refs,_,_,_=prepare_callers(actual,manifest)
    routing=[r for r in refs if r['native_operator_type']=='MoeInitRoutingV3']
    assert sum(r['observed_us']['count'] for r in routing)==1302
    assert sorted(len(r['layer_ids']) for r in routing)==[11,31]
    assert all(r['native_abi'] is None and not r['source_correspondence']['native_abi_population_verified'] for r in routing)
    rows=read('tests/fixtures/source_callers/glm64-retained-rows.json')['rows']
    native=next(r['raw'] for r in rows if r['raw']['Type']=='MoeInitRoutingV3')
    assert native['Output Shapes']=='"2048,4096;2048;288;2048,128"'
    assert native['Input Shapes']=='"256,4096;256,8"'


def test_real_hccl_population_prices_whole_collective_and_keeps_layer0():
    ledger,manifest=qwen_inputs();refs,failures,costs,_=prepare_hccl(ledger,manifest)
    assert not failures and len(refs)==6
    assert sum(r['observed_us']['count'] for r in refs)==85*128
    assert any(r['layer_ids']==[0] for r in refs)
    assert all(len(c['representative_target_ids'])==5 for c in costs)
    assert all(r['native_abi'] is None and not r['source_correspondence']['template_selection_confirmed'] for r in refs)
    assert not any('HcclLaunch' in r['native_operator_type'] for r in refs)
    assert all(r['source_correspondence']['measured_payload_bytes'] is None for r in refs)


def test_hccl_observed_aiv_cannot_be_priced_as_aicpu_or_heterogeneous_payload():
    ledger,manifest=qwen_inputs()
    for n in manifest['nodes']:
        n['operator']['metadata']['hccl_selection']['expansion']='AICPU_TS'
    refs,failures,_,_=prepare_hccl(ledger,manifest)
    assert not refs
    assert all(f['reason']=='explicit_source_engine_conflicts_with_observed_AIV' for f in failures)
    ledger,manifest=qwen_inputs()
    next(n for n in manifest['nodes'] if n['layer']==2 and n['family']=='hccl_local')['physical_work']['hbm_bytes']+=1
    refs,failures,_,_=prepare_hccl(ledger,manifest)
    assert failures and all(f['reason']=='heterogeneous_collective_work_saved_histogram_not_splittable' for f in failures)
    assert sum(r['observed_us']['count'] for r in refs)+sum(f['event_count'] for f in failures)==85*128


def test_complete_native_routing_abi_preserves_every_output_before_cohort_match():
    from compare_routing_cohorts import routing_contract
    source=read('examples/structure/acceptance-20261030-source-callers-40e4300e/routing-native/a5_glm53flash_tp8_c64_p4k-native-partitions.json')
    _,manifest=glm_inputs();contracts={json.dumps(n['contract']) for n in manifest['nodes'] if n['family']=='moe_init_routing'}
    for part in source['partitions']:
        contract=routing_contract(part['native_abi'])
        assert json.dumps(contract) in contracts
        wrong=deepcopy(part['native_abi']);wrong[3][3][0][1]//=2
        assert routing_contract(wrong) is None
        wrong=deepcopy(part['native_abi']);wrong[3][2][1]='int32'
        assert routing_contract(wrong) is None
        assert part['observed_us']['count']==sum(part['layer_counts'].values())
