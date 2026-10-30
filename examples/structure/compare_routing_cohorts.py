"""Exact MX routing ABI normalization into existing cohort comparison.

[Role] Bridge retained full native ABI to Sim's active routing contract.
[Invariants] Every descriptor is checked; tensor values/dispatch are not claimed.
  Complete histogram/whole-layer evidence selects candidates, never measured time.
[Timeouts & Locks] One bounded source per invocation; no raw scans or locks.
[Side-Effect Policy] New scoped mapping and comparison files, no canonical overwrite.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import time

from rebind_body_source_roles import freeze
from replay_body_operator_families import read,write,identity


def routing_contract(native):
    native=freeze(native)
    if len(native)!=4 or native[:2]!=('native_tensor_abi','MoeInitRoutingV3'):
        return None
    inputs,outputs=native[2:]
    if len(inputs)!=2 or len(outputs)!=4:
        return None
    x,ids=inputs
    if len(x[0])!=2 or len(ids[0])!=2:
        return None
    tokens,width=x[0];itokens,topk=ids[0];rows=tokens*topk
    if tokens<1 or width<1 or topk<1 or itokens!=tokens or width%32:
        return None
    if x[1:]!=('bf16','ND') or ids[1:]!=('int32','ND'):
        return None
    if (outputs[0]!=((rows,width),'fp8_e4m3','ND') or outputs[1]!=((rows,),'int32','ND')
            or len(outputs[2][0])!=1 or outputs[2][0][0]<1 or outputs[2][1:]!=('int64','ND')
            or outputs[3]!=((rows,width//32),'fp8_e8m0','ND')):
        return None
    return ('moe_init_routing_mxfp8_active','MoeInitRoutingV3',inputs,outputs)


def mapping(partitions,previous,manifest):
    from reprice_kimi_matrix_partitions import matrix_mapping
    retained=deepcopy(partitions)
    for part in retained['partitions']:
        part['contract']=routing_contract(part['native_abi'])
    cohorts,roles,families,decisions=matrix_mapping(retained,previous,manifest,'MoeInitRoutingV3')
    result={'schema_version':'mindie-profile-structure-mapping/1','graph_id':manifest['graph_id'],
        'declared_execution':manifest['execution'],'observed_phase':'decode',
        'windows':[{**previous['windows'][0],'cohorts':cohorts}],
        'scope':'supplemental_single_native_family; must not replace complete canonical family receipt',
        'partition_decisions':decisions,'cohort_roles':roles,'families':families}
    return result


def main():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    from mindie_sim.cohort_comparison import compare_cohorts
    from compare_source_caller_references import runtime_identity,verify
    from compare_glm_native_partitions import peak_rss
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--partition',type=Path,required=True)
    p.add_argument('--previous-mapping',type=Path,required=True);p.add_argument('--case',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--runtime-source-commit',required=True)
    a=p.parse_args();a.output_dir.mkdir(exist_ok=True,parents=True);before=runtime_identity();own=identity(Path(__file__).resolve())
    start=time.perf_counter();part=read(a.partition);actual=read(part['actual_identity']['path']);verify(part['actual_identity'])
    for k in ('source_identity','geometry','forward_count','body_acceptance_identity'):
        if part[k]!=actual[k]:raise ValueError('partition_population_differs:'+k)
    case=parse_case(read(a.case));manifest=export_structure(case,phase='decode',tokens=part['geometry']['tokens_per_sequence'],
        sequences=part['geometry']['sequences_per_replica'],context=actual['conditional_context_tokens'],scope='body')
    result=mapping(part,read(a.previous_mapping),manifest)
    compared=compare_cohorts(case,result)
    if runtime_identity()!=before or identity(Path(__file__).resolve())!=own:
        raise ValueError('routing_runtime_changed')
    rss=peak_rss()
    if rss>512*1024**2:raise MemoryError('routing_cohort_exceeds_512MiB')
    name=part['source_case_id'];write(a.output_dir/(name+'-routing-mapping.json'),result)
    write(a.output_dir/(name+'-routing-comparison.json'),compared)
    write(a.output_dir/(name+'-routing-receipt.json'),{
        'schema_version':'mindie-routing-cohort-replay/1','case_id':name,
        'partition_identity':identity(a.partition),'previous_mapping_identity':identity(a.previous_mapping),
        'case_identity':identity(a.case),'actual_identity':part['actual_identity'],'source_identity':part['source_identity'],
        'body_acceptance_identity':part['body_acceptance_identity'],'geometry':part['geometry'],
        'forward_count':part['forward_count'],'native_event_count':part['native_event_count'],
        'mapping_identity':identity(a.output_dir/(name+'-routing-mapping.json')),
        'comparison_identity':identity(a.output_dir/(name+'-routing-comparison.json')),
        'runtime_source_commit':a.runtime_source_commit,'runtime_source_identity':before,'normalizer_identity':own,
        'scoped_supplement_only':True,'canonical_family_receipt_replacement_allowed':False,
        'contract_scope':'Complete BF16/INT32 inputs and four MXFP8/INT32/INT64/E8M0 outputs; no expert-ID values, sort flags, source/binary or layer occurrence proof.',
        'execution':{'raw_capture_reads':0,'old_prediction_reused':False,'elapsed_seconds':time.perf_counter()-start,
                     'maximum_resident_set_size_bytes':rss}})
    print(name,len(result['windows'][0]['cohorts']),compared['status_counts'])

if __name__=='__main__':main()
