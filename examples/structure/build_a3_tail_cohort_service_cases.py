"""Reuse complete captured A3 call populations on fresh physical declarations.

[Role] Prepare seven A3 tail cases with typed HCCL and exact cohort responses.
[Invariants] Means come from complete integer histograms, never Body residuals.
  New contracts must match fresh nodes; existing responses remain unchanged.
[Timeouts & Locks] One retained file/source and metadata graph at a time; no cost.
[Side-Effect Policy] Write owned declarations/evidence; no raw or Sim mutations.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import ijson

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from build_glm78_joint_service_cases import pooled
from build_glm78_native_service_cases import freeze
from mindie_sim.structure_contracts import predicted_contract


HERE = Path(__file__).resolve().parent
OUT = HERE / 'acceptance-20261030-a3-tail-service-refinement/retained-cohorts'
BOARD = HERE / 'acceptance-20261030-priority/priority-three-level-scoreboard.json'
INPUTS = HERE / 'acceptance-20261030-priority/priority-scoreboard-inputs.json'
WANTED = {'a3_kimi4_tp8_w4a8_c32', 'a3_kimi4_tp8_w4a8_c64',
          'a3_glm53_dc4k_b1', 'a3_glm53_dc4k_b2', 'a3_glm53_dc16k_b1',
          'glm53flash-a3-tp16-c2', 'v4flash-a3-tp8-c4'}


def pinned(pin):
    if identity(pin['path'])['sha256'] != pin['sha256']:
        raise ValueError('retained_input_changed:' + pin['path'])
    return read(pin['path'])


def selected_inputs():
    selected = {}
    with BOARD.open('rb') as stream:
        for row in ijson.items(stream, 'current_body_comparisons.item'):
            cid = row['case_id'].split(':')[0]
            if cid in WANTED and row['comparison']['status'] == 'compared':
                previous = selected.get(cid)
                if previous is None or row['comparison']['observed_forward_count'] > previous['comparison']['observed_forward_count']:
                    selected[cid] = row
    if set(selected) != WANTED:
        raise ValueError('current_source_population_missing')
    result = {}
    for cid, current in selected.items():
        report = pinned(current['receipt']); manifest = pinned(report['manifest_identity'])
        rows = [r for r in manifest['cases'] if r['case_id'] == cid and r['source']['sha256'] == current['source_identity']['sha256']]
        if len(rows) != 1: raise ValueError('current_source_manifest_not_unique')
        result[cid] = (rows[0], current['receipt'])
    operators = {}
    for path in read(INPUTS)['operators']:
        with open(path, 'rb') as stream:
            for row in ijson.items(stream, 'cases.item'):
                cid = row.get('source_case_id')
                if cid in WANTED and all(k in row for k in ('actual_identity','mapping_identity')):
                    operators[cid] = {k:{'path':row[k]['path'],'sha256':row[k]['sha256']}
                                      for k in ('actual_identity','mapping_identity')}
    operators['v4flash-a3-tp8-c4'] = {key:identity(HERE / 'acceptance-20261030-a3-borderline/v4-actual' /
        ('body-operator-v4flash-a3-tp8-c4-new17.' + suffix + '.json'))
        for key,suffix in (('actual_identity','actual'),('mapping_identity','mapping'))}
    return result, operators


def matches(case, op, match):
    physical = _physical_match(case, op); meta = dict(op.metadata)
    for key, value in match.items():
        if key in physical:
            actual = physical[key]
        elif key.startswith('metadata.'):
            actual = meta
            for part in key.split('.')[1:]:
                actual = actual.get(part) if isinstance(actual, dict) else None
        elif key == 'kernel':
            actual = meta.get('device_kernel_group', {}).get('kernel')
        else:
            return False
        if freeze(actual) != freeze(value): return False
    return True


def append_population(raw, case, ops, selected, stats, source, F, evidence, additions, exclusions):
    if stats['count'] != len(selected)*F or not selected:
        exclusions.append({**evidence, 'reason':'native_population_differs_from_declared_invocations',
            'observed_count':stats['count'],'declared_invocations':len(selected),'forward_count':F})
        return
    if any(any(matches(case, op, r['match']) for r in raw['runtime']['kernels']['service_regimes']) for op in selected):
        exclusions.append({**evidence,'reason':'existing_response_preserved','observed_count':stats['count']})
        return
    domains = defaultdict(list)
    for op in selected: domains[json.dumps(_physical_match(case,op),sort_keys=True)].append(op)
    for key, targets in domains.items():
        match = json.loads(key)
        if {o.op_id for o in ops if matches(case,o,match)} != {o.op_id for o in targets}:
            exclusions.append({**evidence,'reason':'physical_selector_has_other_population','match':match})
            return
    for key, targets in domains.items():
        rid = 'a3-retained-call-' + sha256(key.encode()).hexdigest()[:16]
        provenance = {**evidence,'calibration_origin':'observed','evaluation_relation':'in_sample',
            'source_identity':source,'complete_population':stats,'forward_count':F,
            'expected_rule_hits':len(targets),'pooled_native_invocations':len(selected),
            'separate_domain_timing_observed':len(domains)==1,
            'pooling_basis':'Whole retained native population; same mean per call across declared physical variants.',
            'body_residual_used':False,'old_predicted_cost_used':False,'strict_admission_changed':False,
            'response_boundary':'one_complete_declared_kernel_call_inclusive_floor'}
        rule = {'id':rid,'match':json.loads(key),'response':{'fixed_us':stats['mean_us']},'provenance':provenance}
        raw['runtime']['kernels']['service_regimes'].append(rule)
        additions.append({'rule_id':rid,'match':rule['match'],**provenance})


def build():
    inputs, operators = selected_inputs(); rows=[]; ledger=[]
    for cid, (before, baseline_report) in sorted(inputs.items()):
        row=deepcopy(before);raw=pinned(row['model_declaration']);geo=row['replay_input_pins']['primary_geometry']
        case,ops=physical_ops(raw,geo);by_id={o.op_id:o for o in ops}
        rules=raw['runtime'].setdefault('kernels',{}).setdefault('service_regimes',[]);prior=deepcopy(rules)
        capture_path=HERE/'acceptance-20261030-hccl-66'/f'{cid}-capture-hccl.json';capture=read(capture_path)
        if capture['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('HCCL_source_mismatch')
        group=next(g for g in capture['body_geometry_groups'] if all(g['geometry'][k]==geo[k]
            for k in ('query_rows','tokens_per_sequence','sequences_per_replica')))
        F=group['forward_count'];additions=[];exclusions=[]
        for native,family in [('hcom_allReduce_','allreduce'),('hcom_allGather_','allgather'),('hcom_reduceScatter_','reduce_scatter')]:
            measured=[g for g in group['groups'] if g['native_operator_type']==native and
                g['event_category'] in ('collective_envelope_only','collective_device_task')]
            if not measured:continue
            append_population(raw,case,ops,[o for o in ops if o.family==family],pooled(measured),row['source'],F,
                {'native_operator_type':native,'observation_identity':identity(capture_path),
                 'timing_scope':'Typed native collective elapsed including protocol and peer wait; not isolated link service.',
                 'observed_topology':{'tp':capture['tp'],'ep':capture['ep'],'hardware_sku':capture['hardware_sku']},
                 'pure_link_rate_identified':False,'rank2_or4_curve_extrapolated':False},additions,exclusions)
        if cid in operators:
            index=operators[cid];actual=pinned(index['actual_identity']);mapping=pinned(index['mapping_identity'])
            if actual['source_identity']['sha256']!=row['source']['sha256'] or actual['forward_count']!=F:
                raise ValueError('cohort_source_or_population_mismatch')
            for window in mapping['windows']:
                if window['source_identity']['sha256']!=row['source']['sha256']:raise ValueError('mapping_source_mismatch')
                for cohort in window['cohorts']:
                    target_ids=[t.split('/',1)[1] for t in cohort['target_ids']]
                    evidence={'native_operator_type':cohort['native_operator_type'],
                        'actual_identity':index['actual_identity'],'mapping_identity':index['mapping_identity'],
                        'cohort_id':cohort['cohort_id'],'active_contract':cohort['contract']}
                    targets=[by_id[t] for t in target_ids if t in by_id]
                    if len(targets)!=len(target_ids) or any(freeze(predicted_contract(o.to_dict(include_work=False)))!=freeze(cohort['contract']) for o in targets):
                        exclusions.append({**evidence,'reason':'fresh_declared_active_contract_changed'});continue
                    families=[g for g in actual['families'] if g['native_operator_type']==cohort['native_operator_type'] and
                        set(g['candidate_target_ids'])==set(cohort['target_ids'])]
                    if len(families)!=1:
                        exclusions.append({**evidence,'reason':'complete_native_cohort_population_not_unique'});continue
                    stats=pooled(families)
                    if stats['count']!=cohort['complete_event_count']:raise ValueError('cohort_histogram_population_changed')
                    append_population(raw,case,ops,targets,stats,row['source'],F,evidence,additions,exclusions)
        else:
            exclusions.append({'reason':'no_retained_body_operator_actual','source_case_id':cid})
        if rules[:len(prior)]!=prior:raise ValueError('old_service_rule_changed')
        target=OUT/'cases'/f'{cid}-retained-call-service.json';write(target,raw)
        calibration={'evaluation_relation':'in_sample','source_identity':row['source'],
            'body_residual_used':False,'parameter_assignment':'complete_retained_native_histogram_mean',
            'baseline_receipt':baseline_report,'new_service_rule_count':len(additions)}
        row.update(sim_case_path=str(target),model_declaration=identity(target),variant_id='a3-retained-cohort-service-21c30821',
            calibration_origin='observed',calibration_evidence=calibration)
        row['replay_input_pins']['case']=identity(target);rows.append(row)
        ledger.append({'case_id':cid,'geometry':geo,'forward_count':F,'baseline_case_identity':before['model_declaration'],
            'source_identity':row['source'],'case_identity':identity(target),'prior_rule_count':len(prior),
            'prior_rules_unchanged':True,'new_rules':additions,'unassigned_populations':exclusions})
        print(json.dumps({'case_id':cid,'forward_count':F,'rules_added':len(additions),'unassigned':len(exclusions)}),flush=True)
    write(OUT/'decode-forward-retained-cohort-cases.json',{'schema_version':'mindie-decode-forward-replay/1',
        'cases':rows,'variant_id':'a3-retained-cohort-service-21c30821','not_new_live_collection':True})
    write(OUT/'retained-cohort-service-populations.json',{'cases':ledger,'producer_identity':identity(__file__),
        'source_main_identity':identity(BOARD),'operator_inputs_identity':identity(INPUTS),'raw_reads':0,'cost_predictions':0})


if __name__=='__main__':build()
