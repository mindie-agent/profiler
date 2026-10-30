"""Apply the retained TP-only join-before-reduce caller to old GLM78 sources.

[Role] Declare the source-selected shared/routed join and complete HCCL service.
[Invariants] Source control flow chooses the caller; event counts only validate
  its population. Noncommunication work and all observations stay unchanged.
[Timeouts & Locks] Three metadata-only graph pairs; no raw, cost or locks.
[Side-Effect Policy] New cases and evidence only; no Sim or baseline mutation.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import FIXED, identity, physical_ops, read, write
from build_glm78_joint_service_cases import pooled
from build_a3_tail_cohort_service_cases import append_population


HERE=Path(__file__).resolve().parent
BASE=HERE/'acceptance-20261030-a3-tail-service-refinement/retained-cohorts/decode-forward-retained-cohort-cases.json'
OUT=HERE/'acceptance-20261030-a3-tail-service-refinement/glm78-tp-join'
WANTED={'a3_glm53_dc4k_b1','a3_glm53_dc4k_b2','a3_glm53_dc16k_b1'}
SOURCE_COMMIT='8fd0bc4885cb52e58791aaa8efacc571b9bd115d'


def noncommunication(ops):
    return {key:sum(getattr(op,key) for op in ops if op.family not in
        {'allreduce','allgather','reduce_scatter','alltoall','collective'})
        for key in ('flops','vector_ops','hbm_bytes','mte2_bytes','mte3_bytes')}


def build():
    manifest=read(BASE);output=deepcopy(manifest);output['cases']=[];proofs=[]
    source_doc=identity(FIXED/'docs/operators/moe-output-reduction.md')
    for row in manifest['cases']:
        if row['case_id'] not in WANTED:continue
        raw=read(row['sim_case_path']);geo=row['replay_input_pins']['primary_geometry']
        before,old=physical_ops(raw,geo)
        p=before.runtime.parallel
        if (p.tp,p.ep,p.dp,p.cp,p.pcp)!=(8,1,1,1,1):raise ValueError('tp_only_source_caller_not_applicable')
        raw['runtime']['moe_recipe']='tp_join_reduce'
        condition={'upstream_repository':'vllm-project/vllm-ascend','source_commit':SOURCE_COMMIT,
            'source_locations':['vllm_ascend/ops/fused_moe/fused_moe.py:203-244,304-312,343-356',
                'vllm_ascend/ops/register_custom_ops.py:123-156'],
            'source_document_identity':source_doc,'declared_branch':'non_SP_ALLGATHER_TP_sharded_shared',
            'installed_binary_correspondence_proven':False,
            'selection_basis':'Source shared/routed token-wise join followed by one TP reduction; not observed event-count fitting.',
            'not_applicable_to_cross_EP_or_routed_nonlinear_output_transform':True}
        raw.setdefault('metadata',{})['tp_join_caller_condition']=condition
        case,ops=physical_ops(raw,geo)
        old_work,new_work=noncommunication(old),noncommunication(ops)
        if old_work!=new_work:raise ValueError('noncommunication_work_changed')
        old_counts=Counter(o.recipe for o in old if o.family=='allreduce')
        new_counts=Counter(o.recipe for o in ops if o.family=='allreduce')
        selected=[o for o in ops if o.family=='allreduce']
        ledger_path=HERE/'acceptance-20261030-hccl-66'/f"{row['case_id']}-capture-hccl.json";capture=read(ledger_path)
        if capture['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('source_changed')
        population=next(g for g in capture['body_geometry_groups'] if all(g['geometry'][k]==geo[k]
            for k in ('query_rows','tokens_per_sequence','sequences_per_replica')))
        groups=[g for g in population['groups']if g['native_operator_type']=='hcom_allReduce_' and
            g['event_category'] in ('collective_envelope_only','collective_device_task')]
        stats=pooled(groups);F=population['forward_count'];added=[];excluded=[]
        append_population(raw,case,ops,selected,stats,row['source'],F,
            {'native_operator_type':'hcom_allReduce_','observation_identity':identity(ledger_path),
             'source_caller_condition':condition,'pure_link_rate_identified':False,
             'timing_scope':'Complete typed native collective elapsed including protocol/peer wait; not pure link time.'},added,excluded)
        if excluded or sum(x['expected_rule_hits']for x in added)!=156:raise ValueError('source_join_native_population_not_complete')
        target=OUT/'cases'/f"{row['case_id']}-tp-join-observed-service.json";write(target,raw)
        new=deepcopy(row);new.update(sim_case_path=str(target),model_declaration=identity(target),
            variant_id='glm78-tp-join-observed-service',calibration_origin='observed')
        new['replay_input_pins']['case']=identity(target)
        new['scenario_evidence']['tp_join_caller_condition']=condition
        new['calibration_evidence']={'evaluation_relation':'in_sample','body_residual_used':False,
            'source_identity':row['source'],'native_calls_per_forward':156,
            'separate_physical_variant_timings_observed':False,'parameter_basis':'complete_source_native_mean'}
        output['cases'].append(new)
        proofs.append({'case_id':row['case_id'],'baseline_case_identity':identity(row['sim_case_path']),
            'case_identity':identity(target),'source_condition':condition,'old_reductions':dict(old_counts),
            'new_reductions':dict(new_counts),'old_noncommunication_work':old_work,
            'new_noncommunication_work':new_work,'forward_count':F,'new_rules':added})
        print(json.dumps({'case_id':row['case_id'],'old_reductions':dict(old_counts),
            'new_reductions':dict(new_counts),'native_mean_us':stats['mean_us'],'rules':len(added)}),flush=True)
    output['variant_id']='glm78-tp-join-observed-service';output['baseline_identity']=identity(BASE)
    write(OUT/'decode-forward-tp-join-cases.json',output)
    write(OUT/'tp-join-source-proof.json',{'cases':proofs,'producer_identity':identity(__file__),
        'raw_reads':0,'new_predictions':0})


if __name__=='__main__':build()
