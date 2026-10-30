"""Audit Qwen35 source-authored service replay against retained observations.

[Role] Verify immutable populations, physical service selection and numeric bills.
[Invariants] No Body residual sets parameters; reference activity is nonadditive.
[Timeouts & Locks] One bounded saved report at a time; no subprocess or locks.
[Side-Effect Policy] Write a local review and readable operator bill; no raw/cost.
"""
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import resource

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / 'acceptance-20261030-qwen35-source-complete'


def read(path):
    return json.loads(Path(path).read_text())


def key(group):
    return json.dumps([group['native_operator_type'], group['declared_role'],
                       group['layer_ids'], group.get('native_abi'),
                       group.get('retained_group_id', group.get('partition_index'))], sort_keys=True)


def main():
    checks, failures = 0, []
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok: failures.append(label)
    def close(a, b, label):
        check(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-9), label)
    report_path = HERE / 'decode-forward-service-replay.json'
    report = read(report_path)
    inputs = {r['case_id']: r for r in read(HERE/'decode-forward-service-cases.json')['cases']}
    body = {r['source_case_id']: r for r in report['cases'] if r['comparison']['status'] == 'compared'}
    selections = []
    for cid, row in body.items():
        source = inputs[cid]; path = Path(source['sim_case_path']); case = read(path)
        check(sha256(path.read_bytes()).hexdigest() == source['model_declaration']['sha256'], cid+':case_pin')
        for field in ('path','sha256','size_bytes'):
            check(row['source_identity'][field] == source['source'][field], cid+':source:'+field)
        check(row['calibration_evidence']['evaluation_relation'] == 'in_sample', cid+':in_sample')
        check(not row['prediction_execution']['reused_prediction'], cid+':new_worker')
        check(row['prediction_execution']['execution']['peak_rss_bytes'] <= 512*1024**2, cid+':RSS')
        rules = {r['id']: r for r in case['runtime']['kernels']['service_regimes']}
        selected = {r['id']: r for r in row['prediction']['parameters']['service_regimes']}
        expected_unselected = {rid for rid in rules if 'mxa8w4' in rid}
        if '-c4-' in cid: expected_unselected.add('a5-arch35-dsq-full-load-normal-smallrows-effective-service-v1')
        check(set(rules)-set(selected) == expected_unselected, cid+':known_domains_outside')
        for rid, item in selected.items():
            original = rules[rid]
            for field in ('match','coordinates','domain','response','provenance'):
                check(item[field] == original[field], cid+':unchanged_'+field+':'+rid)
            expected = 80 if 'allreduce' in rid else 40
            check(item['queries'] == {'observable_response': expected}, cid+':inclusive_once:'+rid)
            check(not any('op_id' in k or 'model_name' in k for k in item['match']), cid+':physical_selector')
        selections.append({'case_id':cid, 'rule_hits':{k:v['queries'] for k,v in selected.items()},
            'unselected_rules':sorted(expected_unselected),
            'c4_dsq_domain_note':'Rows below 512 and group rows below 8 are outside this declared large-row rule.' if '-c4-' in cid else None})
    bills = []
    for relative in ('native-references/qwen35-native-reference-scoreboard.json',
                     'hccl-references/source-caller-reference-scoreboard.json'):
        current = read(HERE/relative); previous = {c['case_id']:c for c in read(PRIOR/relative)['cases']}
        for case in current['cases']:
            cid = case['case_id']; old = previous[cid]; observed = body[cid]['comparison']['observed_ms']
            check(case['forward_count'] == observed['count'], cid+':forward_count')
            check(case['source_identity'] == old['source_identity'], cid+':native_source')
            check(case['geometry'] == old['geometry'], cid+':native_geometry')
            check(case['execution']['raw_capture_reads'] == 0, cid+':raw_zero')
            check(case['execution']['maximum_resident_set_size_bytes'] <= 512*1024**2, cid+':native_RSS')
            oldgroups = {key(g):g for g in old['groups']}
            check(set(oldgroups) == {key(g) for g in case['groups']}, cid+':all_groups_preserved')
            for group in case['groups']:
                orig = oldgroups[key(group)]
                for field in ('duration_ns_counter','observed_us','observed_activity_sum_ns'):
                    check(group[field] == orig[field], cid+':native_'+field)
                check(group['prediction_status']=='reference_only' and not group['additional_budget_allowed'], cid+':nonadditive_reference')
                count = sum(n for _,n in group['duration_ns_counter'])
                activity = sum(ns*n for ns,n in group['duration_ns_counter'])
                close(activity/count/1000, group['observed_us']['mean'], cid+':native_mean')
                close(count/case['forward_count'], group['calls_per_forward'], cid+':calls_per_forward')
                close(activity/1e6/case['forward_count'], group['observed_activity_ms_per_forward'], cid+':activity')
                close(group['predicted_reference_us']*count/case['forward_count']/1000,
                      group['predicted_service_ms_per_forward'], cid+':service')
                bills.append({k:group[k] for k in ('native_operator_type','declared_role','layer_ids','observed_us',
                    'calls_per_forward','predicted_reference_us','observed_activity_ms_per_forward',
                    'predicted_service_ms_per_forward','reference_activity_error_ms_per_forward')} | {'case_id':cid})
    result={'status':'failed' if failures else 'passed','checks':checks,'failures':failures,
        'report_identity':{'path':str(report_path),'sha256':sha256(report_path.read_bytes()).hexdigest()},
        'rule_selections':selections,'operator_bills':bills,'raw_reads':0,'new_predictions':0,
        'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':'Retained population/mean arithmetic and unchanged case rule provenance; no independent rate/service re-solve.',
        'review_correction':'First 674-check audit used full source dict equality and omitted retained_group_id in the HCCL join, producing 30 false mismatches. This audit checks the shared path/SHA/size fields and exact retained group identity; input costs and histograms were not changed.'}
    (HERE/'service-and-operator-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','checks','failures','peak_rss_bytes')}))
    if failures: raise SystemExit(1)


if __name__ == '__main__':
    main()
