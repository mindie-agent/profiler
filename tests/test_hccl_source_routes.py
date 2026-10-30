"""Source arithmetic and real exported HCCL evidence guard template inference."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))
from audit_hccl_source_routes import (
    audited_allreduce_mesh_branch, classify_group, collective_bytes, mesh_die_type,
    annotate_ledger, registration_arguments, selector_route,
)


def source_catalog():
    return json.loads((ROOT/'examples/structure/acceptance-20261030-hccl-source/hccl-source-template-audit.json').read_text())['registrations']


def test_collective_size_is_not_the_same_buffer_extent_for_all_operations():
    ar=collective_bytes('ALLREDUCE',65536,2,8)
    ag=collective_bytes('ALLGATHER',65536,2,8)
    rs=collective_bytes('REDUCE_SCATTER',65536,2,8)
    assert ar['selector_data_bytes']==ag['selector_data_bytes']==rs['selector_data_bytes']==131072
    assert ar['input_bytes_per_rank']==ar['output_bytes_per_rank']==131072
    assert ag['output_bytes_per_rank']==rs['input_bytes_per_rank']==1048576
    assert ag['aiv_size_guard_bytes']==rs['aiv_size_guard_bytes']==1048576
    assert collective_bytes('ALLTOALLV',65536,2,8)['selector_data_bytes'] is None


def test_legacy_threshold_edges_do_not_override_cost_model_route():
    assert selector_route(level0_topology='MESH_1D',device_is_960=False)=='cost_model'
    assert selector_route(level0_topology='CLOS',device_is_960=False)=='legacy_heuristic'
    assert selector_route(level0_topology='CLOS',device_is_960=None)=='unknown'
    assert audited_allreduce_mesh_branch('AIV',131071,8).endswith('OneShot')
    assert audited_allreduce_mesh_branch('AIV',131072,8).endswith('TwoShot')
    assert audited_allreduce_mesh_branch('AIV',131072,16).endswith('OneShot')
    assert audited_allreduce_mesh_branch('AICPU',8*1024**2,8).endswith('OneShot')
    assert audited_allreduce_mesh_branch('AICPU',8*1024**2+1,8).endswith('TwoShot')
    assert audited_allreduce_mesh_branch('AICPU',8*1024**2,2,two_level=True).endswith('Concur')
    assert audited_allreduce_mesh_branch('AIV',1024,8,reduce_op='prod') is None


def test_two_die_is_rank_graph_property_not_device_brand():
    assert mesh_die_type('MESH_1D',None,16) is None
    assert mesh_die_type('MESH_1D',[8,7],16)=='TWO_DIE_REGULAR'
    assert mesh_die_type('MESH_1D',[9,6],16)=='TWO_DIE_NOT_REGULAR'
    assert mesh_die_type('MESH_1D',[0,7],8)=='SINGLE_DIE'
    assert mesh_die_type('MESH_1D_CLOS',[8,7],16)=='NOT_MESH'


def test_real_aiv_task_does_not_bind_one_shot_using_preceding_tensor_bytes():
    path=ROOT/'examples/structure/acceptance-20261030-a5-tp-hccl/qwen36-a5-tp2-c1-hccl-ledger.json'
    captured=json.loads(path.read_text())
    group=next(g for g in captured['groups'] if g['implementation_name']=='AivKernel')
    row=classify_group(group,source_catalog())
    assert row['observed_engine']['collective_device_engine']=='AIV'
    assert row['measured_payload_bytes'] is None
    assert row['conditional_preceding_tensor_byte_counter']
    assert set(row['candidate_algorithm_names'])=={'AivAllReduceSoleMeshOneShot','AivAllReduceSoleMeshTwoShot'}
    assert row['template_selection_confirmed'] is False
    assert row['observed_template'] is None


def test_variable_gather_and_fused_program_do_not_inherit_fixed_gather_template():
    samples=json.loads((ROOT/'tests/fixtures/hccl/source-route-signatures.json').read_text())['signatures']
    variable=classify_group(samples['variable_gather']['group'],source_catalog())
    assert variable['collective_operation']=='ALLGATHER_V'
    assert all('GatherV' in name for name in variable['candidate_algorithm_names'])
    fused=classify_group(samples['fused_program']['group'],source_catalog())
    assert fused['candidate_algorithm_names']==[]
    assert fused['observed_engine']['collective_device_engine'] is None
    alias=classify_group(samples['controller_alias']['group'],source_catalog())
    assert alias['collective_operation']=='REDUCE_SCATTER'
    assert alias['observed_engine']['controller_engine']=='AICPU'
    assert alias['observed_engine']['collective_device_engine'] is None


def test_annotating_old_real_ledger_preserves_body_population_without_capture_claim():
    path=ROOT/'examples/structure/acceptance-20261030-a5-tp-hccl/qwen36-a5-tp2-c1-hccl-ledger.json'
    retained=json.loads(path.read_text());row=annotate_ledger(retained,path,source_catalog())
    assert row['capture_inventory']==[]
    assert row['forward_count']==retained['forward_count']
    assert row['body_geometry_groups'][0]['geometry']==retained['geometry']
    assert len(row['body_geometry_groups'][0]['groups'])==len(retained['groups'])
    assert [g['observed_us'] for g in row['body_geometry_groups'][0]['groups']]==[g['observed_us'] for g in retained['groups']]


def test_real_multilevel_registration_keeps_duplicate_stages_and_ignores_inline_comments():
    sample=json.loads((ROOT/'tests/fixtures/hccl/source-route-signatures.json').read_text())['multi_template_registration']
    three,two=registration_arguments(sample['text'])
    assert three['topology_match_class']=='TopoMatchThreeLevel'
    assert two['topology_match_class']=='TopoMatchTwoLevel'
    assert three['template_class'] is two['template_class'] is None
    stages=three['template_classes_in_registration_order']
    assert len(stages)==6
    assert stages[1]==stages[2]=='InsTempScatterNHR'
    assert stages[3]==stages[4]=='InsTempAllGatherNHR'
    assert two['template_classes_in_registration_order']==stages
    assert three['end_line']<two['line']
