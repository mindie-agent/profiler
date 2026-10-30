"""Annotate retained HCCL observations with pinned, conditional source routes.

[Role] Separate observed engine execution from source template possibilities.
[Invariants] No latency/name-based algorithm choice. Public source revision is
  not captured binary identity; preceding tensor bytes are never communication
  payload. Engine/registration evidence does not bypass topology or op checks.
[Timeouts & Locks] Sequential bounded metadata and source files; no locks.
[Side-Effect Policy] Read local source/evidence; write independent audit reports.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

REVISION='c2d6790464654ccf58aca39448de4b65fdc7b184'
SOURCE=Path('/Volumes/data-tmp/tmp/sim-hccl-source-20261030')


def identity(path):
    path=Path(path);h=sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):h.update(block)
    return {'path':str(path.resolve()),'sha256':h.hexdigest(),'size_bytes':path.stat().st_size}


def read(path):
    if Path(path).stat().st_size>32*1024**2:raise ValueError('metadata_exceeds_32MiB')
    return json.loads(Path(path).read_text())


def source_ref(root,path,line,end=None):
    return {**identity(root/path),'line':line,'end_line':end or line,'revision':REVISION}


def selector_route(*,level0_topology=None,device_is_960=None):
    """op_common.cc:184; unknown topology is not inferred from product branding."""
    if level0_topology=='MESH_1D' or device_is_960 is True:return 'cost_model'
    if level0_topology is not None and device_is_960 is False:return 'legacy_heuristic'
    return 'unknown'


def collective_bytes(operation,count,dtype_bytes,rank_size):
    """DataDes.count means sendCount for AG and recvCount for RS."""
    local=count*dtype_bytes
    if operation=='ALLREDUCE': inp,out,meaning=local,local,'full_rank_input_count'
    elif operation=='ALLGATHER':inp,out,meaning=local,local*rank_size,'per_rank_send_count'
    elif operation=='REDUCE_SCATTER':inp,out,meaning=local*rank_size,local,'per_rank_receive_count'
    else:return {'selector_data_bytes':None,'reason':'collective_count_semantics_not_audited_here'}
    return {'selector_data_bytes':local,'input_bytes_per_rank':inp,'output_bytes_per_rank':out,
            'aiv_size_guard_bytes':local if operation=='ALLREDUCE' else local*rank_size,
            'count_semantics':meaning,'rank_size':rank_size}


def audited_allreduce_mesh_branch(engine,data_bytes,rank_size,*,dtype='bf16',reduce_op='sum',two_level=False):
    """Evaluate the legacy helper only, never the cost-table entry selection."""
    if engine=='AIV':
        if dtype in {'uint64','fp64'} or reduce_op=='prod':return None
        threshold=128*1024 if rank_size<=8 else 512*1024
        return 'AivAllReduceSoleMeshOneShot' if data_bytes<threshold else 'AivAllReduceSoleMeshTwoShot'
    if engine!='AICPU':return None
    if dtype in {'int64','uint64','fp64'} or reduce_op=='prod':
        return 'AicpuAllReduceSoleMeshOneShot' if data_bytes<=8*1024**2 else 'AicpuAllReduceSoleMeshTwoShot'
    if two_level and rank_size==2 and data_bytes>=8*1024**2:return 'AicpuAllReduceSoleMeshConcur'
    if data_bytes<=8*1024**2:return 'AicpuAllReduceSoleMeshOneShot'
    # Exact source expression is 8/rank/rank, not (8/rank)^2.
    if data_bytes*(8.0/rank_size/rank_size)>32*1024**2:
        return 'AicpuAllReduceSoleMeshConcur' if two_level and data_bytes>4*1024**3 else 'AicpuAllReduceSoleMeshChunkTwoShot'
    return 'AicpuAllReduceSoleMeshTwoShot'


def mesh_die_type(level0_topology,endpoint_die_link_counts,rank_count):
    if level0_topology!='MESH_1D':return 'NOT_MESH'
    if rank_count<=2:return 'SINGLE_DIE'
    if endpoint_die_link_counts is None:return None
    a,b=endpoint_die_link_counts
    if not a or not b:return 'SINGLE_DIE'
    return 'TWO_DIE_REGULAR' if abs(a-b)==1 else 'TWO_DIE_NOT_REGULAR'


def registration_arguments(text):
    """Parse the real single-/multi-template macros without losing stage order."""
    pattern=re.compile(r'\b(REGISTER_EXEC(?:UTOR)?_[A-Z0-9_]+)\s*\(\s*HcclCMDType::HCCL_CMD_(\w+)\s*,\s*([^;]*?)\)\s*;',re.M)
    # Inline stage comments contain commas; preserve offsets/lines while
    # removing comment contents before splitting registration arguments.
    code=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/',lambda m:re.sub(r'[^\n]',' ',m.group()),text)
    for match in pattern.finditer(code):
        macro,op,args=match.groups();fields=[part.strip() for part in args.split(',')]
        if not all(re.fullmatch(r'\w+',field) for field in fields):
            raise ValueError('registration_argument_not_an_identifier')
        name,executor,*tail=fields
        if macro=='REGISTER_EXECUTOR_IMPL':topomatch=None;templates=[]
        elif macro=='REGISTER_EXECUTOR_IMPL_NO_TOPOMATCH':topomatch=None;templates=tail
        elif macro in {'REGISTER_EXEC_V2','REGISTER_EXEC_V2_MULTI','REGISTER_EXECUTOR_BY_TWO_TEMPS',
                       'REGISTER_EXECUTOR_BY_FOUR_TEMPS','REGISTER_EXECUTOR_BY_TOPO'}:
            topomatch,*templates=tail
        else:raise ValueError('unhandled_registration_macro:'+macro)
        engine=next((value for prefix,value in [('Aiv','AIV'),('Aicpu','AICPU'),('CcuMS','CCU_MS'),
            ('CcuSched','CCU_SCHED'),('Dpu','DPU')] if name.startswith(prefix)),None)
        yield {'operation':op,'algorithm_name':name,'executor_class':executor,
            'registration_kind':macro,'topology_match_class':topomatch,
            'template_class':templates[0] if len(templates)==1 else None,
            'template_classes_in_registration_order':templates,'registered_engine_domain':engine,
            'line':text.count('\n',0,match.start())+1,'end_line':text.count('\n',0,match.end())+1}


def registrations(root):
    """Extract registration facts, not guesses from an observed kernel name."""
    result=[]
    for path in sorted((root/'src/ops').glob('*/algorithm/executor/*.cc')):
        for declaration in registration_arguments(path.read_text()):
            line=declaration.pop('line');end=declaration.pop('end_line')
            result.append(declaration|{'source':source_ref(root,str(path.relative_to(root)),line,end),
                'eligibility':'registration_only; topology/op/build/cost/override conditions still apply'})
    return result


def operation_kind(native):
    """Keep variable-count collectives distinct after exporter spelling changes."""
    name=native.lower().replace('_','')
    name=name.removeprefix('hcom').removesuffix('aicpukernel')
    return {'allreduce':'ALLREDUCE','allgather':'ALLGATHER','allgatherv':'ALLGATHER_V',
        'reducescatter':'REDUCE_SCATTER','reducescatterv':'REDUCE_SCATTER_V',
        'alltoall':'ALLTOALL','alltoallv':'ALLTOALLV','alltoallvc':'ALLTOALLVC',
        'reduce':'REDUCE','broadcast':'BROADCAST','scatter':'SCATTER',
        'barrier':'BARRIER','batchsendrecv':'BATCH_SEND_RECV'}.get(name)


def execution_evidence(group):
    name=group['implementation_name'];core=group['accelerator_core'];category=group['event_category']
    controller=core=='AI_CPU' or category=='unlinked_aicpu_wrapper'
    fused=category=='native_fused_communication_program'
    unit=None;engine=None
    if controller:unit='AICPU'
    elif name=='AivKernel' or core=='AI_VECTOR_CORE':unit='AIV'
    elif core in {'CCU_MS','CCU_SCHED','CCU','DPU','SDMA','NOTIFY'}:unit=core
    elif name=='CcuKernel':unit='CCU'
    elif name=='DpuKernel':unit='DPU'
    elif core=='MIX_AIV':unit='MIX_AIV'
    if category=='collective_device_task' and unit in {'AIV','CCU_MS','CCU_SCHED','CCU','DPU'}:
        engine=unit
    return {'collective_device_engine':engine,'controller_engine':'AICPU' if controller else None,
        'observed_execution_unit':unit,'exported_core':core,
        'ccu_mode':'not_distinguished' if unit=='CCU' else unit if unit in {'CCU_MS','CCU_SCHED'} else None,
        'basis':'typed fused program; not a standalone HCCL selection' if fused else
                'exported device task implementation/core' if engine else
                'typed controller only; child transport engine not established' if controller else
                'typed non-collective device unit; no collective parent established' if unit else
                'collective envelope lacks linked device engine'}


def classify_group(group,catalog):
    native=group['native_operator_type'];name=group['implementation_name'];category=group['event_category']
    fused=category=='native_fused_communication_program'
    op=None if fused else operation_kind(native)
    observed=execution_evidence(group);engine=observed['collective_device_engine']
    domains={'CCU_MS','CCU_SCHED'} if engine=='CCU' else {engine} if engine else None
    candidates=[c for c in catalog if c['operation']==op and
        (domains is None or c['registered_engine_domain'] in domains)]
    missing=['captured_library_build_identity','communicator_rank_size_and_members','selected_algorithm_log',
        'effective_op_expansion_mode','HCCL_ALGO_and_tuner_or_plugin','rank_graph_level_shapes_and_links',
        'topLevelUboe_and_level2UbRtp','measured_count_dtype_reduce_op','CCL_buffer_size',
        'determinism_and_symmetric_memory_flags']
    return {'native_operator_type':native,'implementation_name':name,'event_category':category,
        'accelerator_core':group['accelerator_core'],'attention_kind':group.get('attention_kind'),
        'block':group.get('block'),'layer_population':group.get('layer_population'),
        'observed_us':group['observed_us'],'calls_per_forward':group.get('calls_per_forward'),
        'observed_engine':observed,'collective_operation':op,
        'source_domain':'fused_native_communication; separate from HCCL executor selector' if fused else
            'HCCL_collective' if op else 'unlinked_communication; no standalone collective operation established',
        'selector_route':'unknown','observed_template':None,'template_selection_confirmed':False,
        'candidate_scope':'pinned public-source registration domain; not runtime-compatible shortlist',
        'candidate_algorithm_names':sorted({c['algorithm_name'] for c in candidates}),
        'candidate_template_classes':sorted({template for c in candidates for template in c['template_classes_in_registration_order']}),
        'measured_payload_bytes':group.get('measured_payload_bytes'),
        'conditional_preceding_tensor_byte_counter':group.get('preceding_tensor_byte_counter'),
        'conditional_source_programs':group.get('source_declared_programs'),
        'missing_selection_evidence':missing,'bandwidth_calibration_allowed':False,
        'controller_elapsed_additive_to_collective':False}


def annotate_ledger(retained,path,catalog):
    """One compact source, preserving capture and each accepted Body population."""
    result={'case_id':retained['case_id'],'ledger_identity':identity(path),
        'source_identity':retained['source_identity'],'body_acceptance_identity':retained['body_acceptance_identity'],
        'case_identity':retained['case_identity'],'tp_declaration':retained['tp'],
        'hardware_sku':retained.get('hardware_sku'),'dp_declaration':retained.get('dp'),
        'ep_declaration':retained.get('ep')}
    if retained['schema_version']=='mindie-capture-and-body-hccl-ledger/1':
        result['capture_inventory']=[classify_group(g,catalog)|{
            'scope':g['scope'],'input_json_pointer':f'/capture_inventory/{i}',
            'includes_duplicate_summary_rows':g['includes_duplicate_summary_rows'],
            'can_add_to_other_categories':False} for i,g in enumerate(retained['capture_inventory'])]
        geometries=retained['body_geometry_groups']
        result['controller_alias_overlay']=retained['controller_alias_overlay']
        result['forward_count']=retained['body_count']
    elif retained['schema_version']=='mindie-retained-body-hccl-ledger/1':
        # Original nine ledgers cover only one selected accepted geometry.
        result['capture_inventory']=[];geometries=[retained]
        result['controller_alias_overlay']=None;result['forward_count']=retained['forward_count']
    else:raise ValueError('unsupported_hccl_ledger_schema')
    result['body_geometry_groups']=[{'geometry':geometry['geometry'],
        'forward_count':geometry['forward_count'],'groups':[classify_group(g,catalog)|{
            'scope':'accepted_body_geometry','input_json_pointer':
            f'/body_geometry_groups/{gi}/groups/{i}' if 'body_geometry_groups' in retained else f'/groups/{i}'}
            for i,g in enumerate(geometry['groups'])]} for gi,geometry in enumerate(geometries)]
    if sum(g['forward_count'] for g in result['body_geometry_groups'])!=result['forward_count']:
        raise ValueError('body_geometry_population_not_partitioned')
    return result


def associated_evidence(case,associated):
    source=case['source_identity'];rows=[row for row in associated['sources'] if row['source_identity']['sha256']==source['sha256']]
    if len(rows)!=1 or rows[0]['source_identity']['size_bytes']!=source['size_bytes']:
        raise ValueError('associated_artifact_source_identity_not_unique')
    result={'inventory':rows[0],'status':'artifact_inventory_only; no runtime template asserted'}
    expanded=associated.get('bounded_same_capture_expansion')
    if expanded and expanded['retained_csv_member_identity']['sha256']==source['sha256']:
        trace=expanded['trace_inventory']
        result.update({'archive_identity':expanded['archive_identity'],
            'retained_csv_member_identity':expanded['retained_csv_member_identity'],
            'trace_inventory':trace,
            'status':'existing_trace_but_no_device_correlation' if not trace['device_task_connection_fields_present'] and
                      not trace['flow_events_present'] else 'explicit_trace_fields_require_occurrence_link_validation'})
    return result


def build(root,ledgers,output,associated_artifacts=None):
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,text=True,check=True,timeout=5).stdout.strip()
    if commit!=REVISION:raise ValueError('public_source_revision_changed')
    catalog=registrations(root)
    selected={
        'entry_route':('src/ops/op_common/op_common.cc',159,211),
        'expansion_mode':('src/ops/op_common/op_common.cc',3668,3708),
        'cost_selection':('src/ops/op_common/selector/selector_engine.cc',240,299),
        'engine_priority':('src/ops/op_common/selector/selector_engine.cc',69,89),
        'mesh_die_derivation':('src/ops/op_common/topo_info/topo_host.cc',1179,1243),
        'top_uboe_derivation':('src/ops/op_common/topo_info/topo_host.cc',670,706),
        'ar_aiv_heuristic':('src/ops/all_reduce/selector/all_reduce_auto_selector.cc',604,699),
        'ar_aicpu_heuristic':('src/ops/all_reduce/selector/all_reduce_auto_selector.cc',530,601),
        'ar_aicpu_multilevel':('src/ops/all_reduce/selector/all_reduce_auto_selector.cc',415,484),
        'ag_aicpu_heuristic':('src/ops/all_gather/selector/all_gather_auto_selector.cc',303,410),
        'ag_aiv_heuristic':('src/ops/all_gather/selector/all_gather_auto_selector.cc',412,472),
        'rs_aicpu_heuristic':('src/ops/reduce_scatter/selector/reduce_scatter_auto_selector.cc',473,534),
        'rs_aiv_heuristic':('src/ops/reduce_scatter/selector/reduce_scatter_auto_selector.cc',536,615),
        'ar_count':('src/ops/all_reduce/all_reduce.cc',164,186),
        'ag_count':('src/ops/all_gather/all_gather.cc',158,190),
        'rs_count':('src/ops/reduce_scatter/reduce_scatter.cc',154,179),
        'ar_attrs':('src/ops/all_reduce/algorithm/executor/ins_v2_all_reduce_sole_executor.cc',371,483),
        'two_shot_phases':('src/ops/all_reduce/algorithm/template/aicpu/ins_temp_all_reduce_mesh_1D_two_shot.cc',155,173),
        'cost_formula':('src/ops/op_common/selector/cost_table.cc',366,410),
        'aicpu_oneshot_coefficients':('src/ops/all_reduce/algorithm/template/aicpu/ins_temp_all_reduce_mesh_1D_one_shot.cc',23,57),
        'aiv_oneshot_coefficients':('src/ops/all_reduce/algorithm/template/aiv/aiv_temp_all_reduce_mesh_1D_oneshot.cc',25,75),
        'aiv_twoshot_coefficients':('src/ops/all_reduce/algorithm/template/aiv/aiv_temp_all_reduce_mesh_1D_twoshot.cc',26,80),
        'common_thresholds':('src/ops/op_common/selector/auto_selector_base.h',23,32)}
    facts={k:source_ref(root,*v) for k,v in selected.items()}
    associated=read(associated_artifacts) if associated_artifacts else None
    cases=[];sources=set()
    for path in ledgers:
        retained=read(path)
        source=retained['source_identity']['sha256']
        if source in sources:raise ValueError('same_source_added_twice; select one retained generation')
        sources.add(source);case=annotate_ledger(retained,path,catalog)
        if associated:case['associated_artifact_evidence']=associated_evidence(case,associated)
        cases.append(case)
        del retained
    body_groups=[g for case in cases for geometry in case['body_geometry_groups'] for g in geometry['groups']]
    inventory=[g for case in cases for g in case['capture_inventory']]
    def counts(groups):
        return {'groups':len(groups),'categories':dict(Counter(g['event_category'] for g in groups)),
            'observed_device_engine_counts':dict(Counter(g['observed_engine']['collective_device_engine'] or 'not_established' for g in groups)),
            'observed_execution_unit_counts':dict(Counter(g['observed_engine']['observed_execution_unit'] or 'not_established' for g in groups))}
    report={'schema_version':'mindie-hccl-source-template-audit/1','public_source_revision':REVISION,
        'source_root':str(root),'captured_binary_equivalence_established':False,
        'associated_artifacts_identity':identity(associated_artifacts) if associated_artifacts else None,
        'source_facts':facts,'registrations':catalog,'cases':cases,
        'selection_findings':[
            {'claim':'MESH_1D or device960 uses cost-table selection; all other known shapes/non960 use ExecuteSelector.',
             'source_fact':'entry_route','heuristic_thresholds_are_universal':False},
            {'claim':'AIV AllReduce legacy helper: MESH_1D and ranks<=8 uses strict dataSize<128KiB OneShot; otherwise TwoShot. Ranks>8 uses <512KiB.',
             'source_fact':'ar_aiv_heuristic','source_entry_route_must_be_established':True},
            {'claim':'AICPU AllReduce single-level mesh legacy helper uses <=8MiB OneShot, after special dtype/PROD and two-rank detour conditions. Generic large selection uses ratio=8/rank/rank, not (8/rank)^2.',
             'source_fact':'ar_aicpu_heuristic','source_entry_route_must_be_established':True},
            {'claim':'TWO_DIE_REGULAR requires MESH_1D, more than two ranks, both endpoint-die link counts nonzero and counts differing by one. Product generation alone is insufficient.',
             'source_fact':'mesh_die_derivation'},
            {'claim':'A5+ with supported HcclConfigGetInfo obtains expansion mode from communicator config; older/no-config paths use environment overrides.',
             'source_fact':'expansion_mode'},
            {'claim':'AllReduce count is full per-rank data; AllGather count is per-rank send; ReduceScatter count is per-rank receive. Variable collectives need their count vectors.',
             'source_facts':['ar_count','ag_count','rs_count']},
            {'claim':'Cost-table evaluation groups transfer/reduce/copy and launch terms, then selects minimum cost after eligibility/priorities/config/tuner. It is not a fixed message-size switch.',
             'source_facts':['cost_formula','cost_selection']}],
        'summary':{'sources':len(cases),'body_geometries':sum(len(c['body_geometry_groups']) for c in cases),
            'body_forward_count':sum(c['forward_count'] for c in cases),
            'registered_algorithms':len(catalog),'confirmed_templates':0,
            'registration_macro_counts':dict(Counter(c['registration_kind'] for c in catalog)),
            'body':counts(body_groups),'capture':counts(inventory),
            'capture_inventory_available_sources':sum(bool(case['capture_inventory']) for case in cases),
            'signature_presence_in_completed_capture_inventory':{unit:{
                'source_count':sum(any(g['observed_engine']['observed_execution_unit']==unit for g in case['capture_inventory']) for case in cases),
                'status':'present' if any(g['observed_engine']['observed_execution_unit']==unit for g in inventory) else
                    'unknown_due_to_capture_filter_scope' if unit=='DPU' else
                    'not_observed_in_available_inventory' if inventory else 'inventory_unavailable',
                'collector_filter_coverage_note':'No standalone DPU name/core branch in retained collector; hcom/COMMUNICATION matches only.' if unit=='DPU' else
                    'CCU/Notify name tokens and hcom/COMMUNICATION are retained; this is not an unrestricted execution-unit census.' if unit in {'CCU_MS','CCU_SCHED','CCU','NOTIFY'} else
                    'Interpret only within the retained communication-name/core filter; not all profiler execution units.',
                'absence_means':'no matching exported signature in this inventory, not proof the mechanism was unused'}
                for unit in ['AIV','AICPU','CCU_MS','CCU_SCHED','CCU','DPU','SDMA','NOTIFY','MIX_AIV']},
            'capture_and_body_counts_are_not_additive':True},
        'schema_contract':{'known': 'exported engine/controller, native op, complete elapsed histogram and Body identity',
            'conditional':'Sim payload/work, preceding tensors, topology/selector scenarios',
            'unproven':'captured binary, actual rank graph, runtime algo/template and payload scalar arguments',
            'population':'one retained source; phase-unclassified capture inventory and each accepted Body geometry are separate and not additive'}}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,separators=(',',':'),allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--source-root',type=Path,default=SOURCE)
    parser.add_argument('--ledger',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--associated-artifacts',type=Path)
    args=parser.parse_args();build(args.source_root,args.ledger,args.output,args.associated_artifacts)


if __name__=='__main__':main()
