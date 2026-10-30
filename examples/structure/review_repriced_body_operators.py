"""Audit saved zero-raw body-operator repricing, including partial references.

[Role] Independently verify preserved observations, population partitions and math.
[Invariants] References and failed predictions never enter strict accuracy. Fresh
  declarations may change physical work, never retained measured histograms.
[Timeouts & Locks] Bounded JSON, one case at a time; no prediction/raw CSV/locks.
[Side-Effect Policy] Write an independent review beside the requested scoreboard.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import ceil, isclose
from pathlib import Path


def read(path):
    path = Path(path)
    if path.stat().st_size >= 32 * 1024**2:
        raise ValueError(f'oversized_metadata:{path}')
    return json.loads(path.read_text())


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def statistics(histogram):
    pairs = sorted((int(value), int(n)) for value, n in histogram)
    count = sum(n for _, n in pairs)

    def at(position):
        seen = 0
        for value, n in pairs:
            if seen <= position < seen + n:
                return value
            seen += n
        raise ValueError('histogram_position_outside_population')

    return {'count': count, 'mean': sum(value*n for value,n in pairs)/count/1000,
            'p50': (at((count-1)//2)+at(count//2))/2000, 'p90': at(ceil(count*.9)-1)/1000,
            'min': pairs[0][0]/1000, 'max': pairs[-1][0]/1000}


def review(directory):
    directory = Path(directory)
    report_path = directory / 'body-operator-family-scoreboard.json'
    report = read(report_path)
    checks, failures, cases = 0, [], []
    accuracy, totals = defaultdict(Counter), Counter()

    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            failures.append(label)

    def near(left, right, label):
        check(isclose(left, right, rel_tol=1e-10, abs_tol=1e-10), label)

    def identity(record, label):
        path = Path(record['path'])
        check(path.stat().st_size == record['size_bytes'], label+':size')
        check(digest(path) == record['sha256'], label+':sha256')

    def observed_stats(row, label):
        values = statistics(row['duration_ns_counter'])
        for key, value in values.items():
            near(row['observed_us'][key], value, label+':histogram_'+key)

    check(report['raw_capture_reads'] == 0, 'no_raw_reads')
    strict_source = None
    if report.get('successful_strict_predictions_reused'):
        identity(report['strict_prediction_source_report'], 'strict_source_report')
        strict_source = read(report['strict_prediction_source_report']['path'])
        check(report['new_strict_program_count'] == 0, 'reference_retry_does_not_repeat_strict')
        sim_files = lambda value: {path:sha for path,sha in value.items() if '/mindie_sim/' in path}
        check(sim_files(report['runtime_source_identity']) == sim_files(strict_source['runtime_source_identity']),
              'reference_retry_same_exact_sim_runtime_as_strict')
    else:
        check(not report['old_prediction_reused'], 'no_old_cost')
    check(report['runtime_sources_unchanged'], 'runtime_stable_during_run')
    for projected in report['cases']:
        identity(projected['case_detail_identity'], 'case_detail')
        case = read(projected['case_detail_identity']['path'])['cases'][0]
        cid = case['case_id']
        if strict_source is not None:
            original_case = next(row for row in strict_source['cases']
                                 if row['actual_identity'] == case['actual_identity'])
            for key in ('comparison_identity','actual_identity','mapping_identity','case_identity'):
                check(original_case[key] == case[key], cid+':strict_retry_preserved_'+key)
        for field in ('actual_identity','case_identity','mapping_identity','comparison_identity'):
            identity(case[field], cid+':'+field)
            check(case[field] == projected[field], cid+':projection_'+field)
        actual = read(case['actual_identity']['path'])
        identity(actual['body_acceptance_identity'], cid+':original_body')
        old_mapping = read(case['declaration_refresh']['old_mapping_identity']['path'])
        mapping = read(case['mapping_identity']['path'])
        comparison = read(case['comparison_identity']['path'])
        old_cohorts = {row['cohort_id']: row for window in old_mapping['windows'] for row in window['cohorts']}
        new_cohorts = {row['cohort_id']: row for window in mapping['windows'] for row in window['cohorts']}
        change = case['declaration_refresh']
        check(not change['old_prediction_reused'] and change['raw_capture_reads'] == 0, cid+':fresh_cost')
        check(mapping['declared_execution'] == change['declared_execution'], cid+':execution')
        check(mapping['graph_id'] == change['fresh_graph_id'], cid+':fresh_graph')
        check(case['geometry'] == actual['geometry'], cid+':geometry')
        check(case['source_identity'] == actual['source_identity'], cid+':source')
        check(case['forward_count'] == actual['forward_count'], cid+':forward_population')
        for record in change['rebound']:
            before, after = old_cohorts[record['old_cohort_id']], new_cohorts[record['cohort_id']]
            for field in ('event_count','complete_activity_sum_ns','duration_ns','busy_union_ns',
                          'status_counts','contract','target_ids','native_operator_type'):
                check(before[field] == after[field], cid+':preserved_'+field)
        if change['mode'] == 'identical_declaration_new_cost':
            check(old_cohorts == new_cohorts and not change['excluded'], cid+':identical_declaration_population')
        else:
            check(len(change['rebound'])+len(change['excluded']) == len(old_cohorts), cid+':rebind_partition')
        original_families = {(row['native_operator_type'],row['declared_role']):row for row in actual['families']}
        source_groups = {group['group_id']:group for group in actual.get('source_role_references',())}
        raw_count, strict_events, strict_cohorts, passed, refs, excluded_refs = 0,0,0,0,0,0
        for family in case['families']:
            label = cid+':'+family['native_operator_type']+':'+family['declared_role']
            original = original_families[family['native_operator_type'],family['declared_role']]
            check(family['duration_ns_counter'] == original['duration_ns_counter'], label+':exact_histogram_preserved')
            observed_stats(family,label)
            n = family['observed_us']['count']; raw_count += n
            selected = [row for row in family['cohorts'] if row['status']=='compared']
            scored = sum(row['observed']['event_count'] for row in selected)
            check(scored == family['scored_event_count'],label+':strict_event_count')
            check(scored+family['unscored_event_count'] == n,label+':strict_population_partition')
            strict_events += scored; strict_cohorts += len(selected)
            family_pass = 0
            for cohort in family['cohorts']:
                if cohort['status'] != 'compared':
                    check(cohort.get('accuracy_pass') is None,label+':failure_not_scored')
                    continue
                measured = cohort['observed']['duration_ns']['mean']/1000
                predicted = cohort['prediction']['per_call_ms']*1000
                tier = 'absolute_15us' if measured <= 50 else 'relative_15pct'
                success = abs(predicted-measured) <= (15 if measured <= 50 else measured*.15)
                check(cohort['accuracy_tier'] == tier,label+':tier')
                check(cohort['accuracy_pass'] == success,label+':tolerance')
                family_pass += success; accuracy[tier]['compared'] += 1; accuracy[tier]['passed'] += success
            check(family_pass == family['passed_cohort_count'],label+':pass_count'); passed += family_pass
            groups = family.get('conditional_source_role_references',())
            dropped = family.get('current_source_reference_exclusions',())
            for group in groups:
                refs += 1
                original_group_id = group.get('frozen_native_rebind',{}).get('original_observation_group_id',group['group_id'])
                before = source_groups[original_group_id]
                check(group['duration_ns_counter'] == before['duration_ns_counter'],label+':reference_observations')
                rebind = group.get('frozen_native_rebind')
                if rebind:
                    native = before['source_correspondence']['observed_native_tensor_contract']
                    native_bytes = json.dumps(native,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
                    check(group['source_correspondence']['observed_native_tensor_contract']==native,label+':complete_native_abi_preserved')
                    check(rebind['native_abi_sha256']==sha256(native_bytes).hexdigest(),label+':native_abi_hash')
                    check(rebind['validated_layer_ids']==before['layer_ids'],label+':all_old_layers_revalidated')
                    check(rebind['new_graph_id']==mapping['graph_id'],label+':reference_fresh_graph')
                    check(not rebind['strict_tensor_cohort_implied'],label+':reference_not_strict')
                    check(group['source_correspondence']['observed_valid_routed_rows'] is None
                          and group['source_correspondence'].get('observed_active_mask_values') is None
                          and group['source_correspondence'].get('observed_group_list_values') is None,
                          label+':mask_group_list_and_valid_rows_still_unknown')
                observed_stats(group,label+':reference')
                activity = sum(value*n for value,n in group['duration_ns_counter'])
                near(group['observed_activity_ms_per_forward'],activity/1e6/case['forward_count'],label+':reference_activity')
                near(group['predicted_service_ms_per_forward'],group['predicted_reference_us']*group['observed_us']['count']/1000/case['forward_count'],label+':reference_prediction')
                check(not group['additional_budget_allowed'] and not group['occurrence_binding_implied'],label+':conditional_reference')
                check('accuracy_pass' not in group,label+':reference_outside_accuracy')
            coverage = family.get('source_reference_coverage')
            if coverage:
                reference_count = sum(group['observed_us']['count'] for group in groups)
                excluded_count = sum(group.get('event_count',0) for group in dropped)
                excluded_refs += len(dropped)
                check(coverage['measured_event_count']==n and coverage['strict_scored_event_count']==scored,label+':coverage_population')
                check(coverage['reference_event_count']==reference_count and coverage['excluded_reference_event_count']==excluded_count,label+':reference_partition')
                check(scored+reference_count+excluded_count+coverage['unclassified_event_count']==n,label+':whole_family_partition')
                check(not coverage['reference_events_enter_strict_denominator'],label+':references_unscored')
        check(raw_count == actual['counts']['selected_body_events'],cid+':all_family_population')
        check(passed==case['passed_cohorts']==projected['passed_cohorts'],cid+':global_pass')
        status = Counter(row['status'] for window in comparison['windows'] for row in window['cohorts'])
        check(dict(status)==case['comparison_status_counts'],cid+':comparison_status')
        check(not comparison['old_prediction_reused'] and comparison['raw_capture_reads']==0,cid+':new_prediction_receipt')
        check(all(receipt['status']=='completed' or receipt.get('reason') for receipt in comparison['program_receipts']),cid+':failures_visible')
        if case['reference_receipt']['status']=='failed':
            check(bool(case['reference_exclusions']),cid+':reference_failure_visible')
        summary = {'case_id':cid,'passed':passed,'compared':strict_cohorts,'strict_events':strict_events,
                   'retained_reference_groups':refs,'excluded_reference_groups':excluded_refs,
                   'reference_worker_status':case['reference_receipt']['status'],
                   'strict_rebind_exclusions':len(change['excluded']), 'forward_count':case['forward_count']}
        cases.append(summary)
        totals.update({key:value for key,value in summary.items() if isinstance(value,int)})
    check(report['status']==('partial' if any(case['reference_worker_status']=='failed' for case in cases)
          or any(row['comparison_status_counts'].get('prediction_failed') for row in report['cases']) else 'completed'),'global_completion_honest')
    result = {'schema_version':'mindie-repriced-body-operator-review/1','status':'passed' if not failures else 'failed',
              'checks':checks,'failures':failures,'scoreboard_sha256':digest(report_path),
              'script_sha256':digest(__file__),'source_count':len(cases),'counts':dict(totals),
              'accuracy_by_tier':dict(accuracy),'cases':cases,'raw_capture_reads':0,'prediction_executions':0,
              'method':'stdlib identities/histograms, old-to-new observed partition equality and independent tier math'}
    (directory/'body-operator-reprice-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='cases'}))
    if failures:
        raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    review(parser.parse_args().directory)
