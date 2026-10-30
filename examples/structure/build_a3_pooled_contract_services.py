"""Pool disjoint same-contract cohorts before applying a physical service rule.

[Role] Recover complete quant/norm populations whose physical axes are equal.
[Invariants] Candidate target sets and observed histograms remain disjoint;
  pooling never multiplies a partial mean or splits by unobserved role timings.
[Timeouts & Locks] One source metadata graph and retained table at a time.
[Side-Effect Policy] Independent declarations and receipts only; no raw or costs.
"""
from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_glm78_joint_service_cases import pooled
from build_glm78_native_service_cases import freeze
from build_a3_tail_cohort_service_cases import append_population, pinned
from mindie_sim.structure_contracts import predicted_contract


HERE=Path(__file__).resolve().parent
BASE=HERE/'acceptance-20261030-a3-tail-service-refinement/retained-cohorts'
OUT=HERE/'acceptance-20261030-a3-tail-service-refinement/pooled-contracts'


def build():
    manifest=read(BASE/'decode-forward-retained-cohort-cases.json')
    prior_proof={r['case_id']:r for r in read(BASE/'retained-cohort-service-populations.json')['cases']}
    rows=[];proofs=[]
    for before in manifest['cases']:
        cid=before['case_id'];evidence=prior_proof[cid]
        excluded=[r for r in evidence['unassigned_populations'] if r['reason']=='physical_selector_has_other_population']
        if not excluded:continue
        mapping_pin=excluded[0]['mapping_identity'];actual_pin=excluded[0]['actual_identity']
        mapping=pinned(mapping_pin);actual=pinned(actual_pin);F=actual['forward_count']
        if actual['source_identity']['sha256']!=before['source']['sha256']:raise ValueError('source_changed')
        raw=read(before['sim_case_path']);prior=deepcopy(raw['runtime']['kernels']['service_regimes'])
        geo=before['replay_input_pins']['primary_geometry'];case,ops=physical_ops(raw,geo);by_id={o.op_id:o for o in ops}
        cohorts=defaultdict(list)
        for window in mapping['windows']:
            if window['source_identity']['sha256']!=before['source']['sha256']:raise ValueError('mapping_source_changed')
            for cohort in window['cohorts']:
                if cohort['native_operator_type'] not in {r['native_operator_type']for r in excluded}:continue
                cohorts[(cohort['native_operator_type'],freeze(cohort['contract']))].append(cohort)
        added=[];unassigned=[]
        for (native,contract),members in cohorts.items():
            if len(members)<2:continue
            target_ids=set();families=[];target_overlap=False
            for cohort in members:
                ids=set(cohort['target_ids'])
                if target_ids&ids:target_overlap=True;break
                target_ids.update(ids)
                groups=[g for g in actual['families']if g['native_operator_type']==native and set(g['candidate_target_ids'])==ids]
                if len(groups)!=1 or sum(n for _,n in groups[0]['duration_ns_counter'])!=cohort['complete_event_count']:
                    raise ValueError('complete_disjoint_cohort_histogram_missing')
                families.extend(groups)
            if target_overlap:
                unassigned.append({'native_operator_type':native,'reason':'cohort_candidate_sets_overlap'});continue
            selected=[by_id[t.split('/',1)[1]]for t in sorted(target_ids)if t.split('/',1)[1]in by_id]
            if len(selected)!=len(target_ids) or any(freeze(predicted_contract(o.to_dict(include_work=False)))!=contract for o in selected):
                unassigned.append({'native_operator_type':native,'reason':'fresh_active_contract_changed'});continue
            append_population(raw,case,ops,selected,pooled(families),before['source'],F,
                {'native_operator_type':native,'actual_identity':actual_pin,'mapping_identity':mapping_pin,
                 'cohort_ids':[c['cohort_id']for c in members],'active_contract':contract,
                 'constituent_event_counts':[c['complete_event_count']for c in members],
                 'disjoint_target_ids':[c['target_ids']for c in members],
                 'observed_partition_basis':'Disjoint retained cohort target populations with identical active contract.',
                 'individual_role_timing_used':False},added,unassigned)
        if not added:
            proofs.append({'case_id':cid,'new_rules':[],'unassigned':unassigned,'prediction_requested':False});continue
        if raw['runtime']['kernels']['service_regimes'][:len(prior)]!=prior:raise ValueError('prior_rules_changed')
        target=OUT/'cases'/f'{cid}-pooled-contract-service.json';write(target,raw)
        row=deepcopy(before);row.update(sim_case_path=str(target),model_declaration=identity(target),variant_id='a3-pooled-active-contract-service')
        row['replay_input_pins']['case']=identity(target)
        row['calibration_evidence']['disjoint_contract_pools']=[{'rule_id':r['rule_id'],
            'native_operator_type':r['native_operator_type'],'expected_rule_hits':r['expected_rule_hits']}for r in added]
        rows.append(row);proofs.append({'case_id':cid,'prior_case_identity':identity(before['sim_case_path']),
            'case_identity':identity(target),'forward_count':F,'prior_rules_unchanged':True,
            'new_rules':added,'unassigned':unassigned,'prediction_requested':True})
        print(json.dumps({'case_id':cid,'new_rules':[(r['native_operator_type'],r['expected_rule_hits'],r['complete_population']['mean_us'])for r in added]}),flush=True)
    write(OUT/'decode-forward-pooled-contract-cases.json',{'schema_version':manifest['schema_version'],
        'cases':rows,'variant_id':'a3-pooled-active-contract-service','baseline_identity':identity(BASE/'decode-forward-retained-cohort-cases.json'),
        'not_new_live_collection':True})
    write(OUT/'pooled-contract-populations.json',{'cases':proofs,'producer_identity':identity(__file__),'raw_reads':0,'new_predictions':0})


if __name__=='__main__':build()
