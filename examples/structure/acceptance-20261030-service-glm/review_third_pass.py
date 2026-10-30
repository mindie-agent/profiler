"""Review the existing HC source fusion and complete native response populations.

[Role] Check saved source selections, normalized contracts and actual rule hits.
[Invariants] No raw scan, cost call or Body-residual parameter; prior rules persist.
[Timeouts & Locks] Finite saved receipts, no subprocesses or locks.
[Side-Effect Policy] Writes only third-pass review and concise README.
"""
from copy import deepcopy
import json

from build_service_cases import HERE, read, pin, write, summarize


def main():
    dest = HERE / 'third-pass'
    report = read(dest / 'decode-forward-service-replay.json')
    old_report = read(HERE / 'second-pass/decode-forward-service-replay.json')
    old_rows = {r['source_case_id']: r for r in old_report['cases'] if r['status'] == 'compared'}
    rows = {r['source_case_id']: r for r in report['cases'] if r['status'] == 'compared'}
    populations = read(dest / 'observed-populations.json')
    checks = 0
    failures = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    check(report['status'] == 'completed' and len(rows) == 3, 'three completed source populations')
    check(report['runtime_generation']['unchanged'], 'fixed runtime unchanged')
    check(report['runtime_generation']['start']['package_sha256'] ==
          '57520ed725bfe6358585bd404f4cefa1f7702c00aabbc9294fecfb44a2f21db8', '3b72 runtime package')
    results = []
    for population in populations['cases']:
        cid = population['case_id']
        case = read(population['case_identity']['path'])
        before = read(population['prior_case_identity']['path'])
        for key in ('case_identity', 'prior_case_identity'):
            check(pin(population[key]['path']) == population[key], cid + ' ' + key)
        rules = case['runtime']['kernels']['service_regimes']
        prior_rules = before['runtime']['kernels']['service_regimes']
        check(len(rules) == 11 and rules[:9] == prior_rules, cid + ' unchanged prior nine rules')
        after_kernels = deepcopy(case['runtime']['kernels'])
        after_kernels['service_regimes'] = prior_rules
        options = after_kernels['lowerings']['native_fusion']['options']
        check(options['roles'].count('hc_pre') == 1, cid + ' HC role selected once')
        options['roles'].remove('hc_pre')
        check(options['traffic_profile'].pop('hc_pre') == 'hc_pre_arch35_mk_175ef4d4', cid + ' source HC provider')
        if not options['traffic_profile']:
            del options['traffic_profile']
        check(after_kernels == before['runtime']['kernels'], cid + ' only HC physical selection added')
        for key in ('model', 'machine', 'workload'):
            check(case[key] == before[key], cid + ' unchanged ' + key)
        row = rows[cid]
        old = old_rows[cid]
        for key in ('source_identity', 'observed', 'geometry'):
            check(row[key] == old[key], cid + ' unchanged ' + key)
        check(row['calibration_origin'] == 'observed', cid + ' observed calibration')
        check(row['calibration_evidence']['evaluation_relation'] == 'in_sample', cid + ' in-sample relation')
        check(row['prediction_execution']['reused_prediction'] is False, cid + ' fresh execution')
        params = row['prediction']['parameters']
        hits = {r['id']: r for r in params['service_regimes']}
        check(not params['regime_selection']['unmatched'] and len(hits) == 11, cid + ' all eleven rules selected')
        for previous in old['prediction']['parameters']['service_regimes']:
            current = hits[previous['id']]
            for key in ('queries', 'response_us_min', 'response_us_max'):
                check(current[key] == previous[key], cid + ' preserved native response ' + previous['id'] + '/' + key)
        added = []
        for group in population['groups']:
            ap = group['actual_identity']
            mp = group['mapping_identity']
            check(pin(ap['path']) == ap and pin(mp['path']) == mp, cid + ' retained actual/mapping identities')
            actual = read(ap['path'])
            families = [actual['families'][i] for i in group['family_indices']]
            stats = summarize(families)
            check(stats == group['observed'], cid + ' complete native histogram')
            check(stats['count'] == population['forward_count'] * group['calls_per_forward'], cid + ' native multiplicity')
            mapping = read(mp['path'])
            cohort_ids = set(group['retained_cohort_ids'])
            cohorts = [c for window in mapping['windows'] for c in window['cohorts'] if c['cohort_id'] in cohort_ids]
            check(len(cohorts) == len(cohort_ids), cid + ' exact normalized cohort membership')
            check(sum(c['complete_event_count'] for c in cohorts) == stats['count'], cid + ' cohort count conservation')
            check(sum(c['complete_activity_sum_ns'] for c in cohorts) ==
                  sum(ns * count for ns, count in stats['duration_ns_counter']), cid + ' cohort activity conservation')
            for cohort in cohorts:
                check(cohort['contract'] == group['normalized_contract'], cid + ' full normalized contract')
                check(cohort['native_operator_type'] == group['native_operator_type'], cid + ' native type')
            rid = group['rule_id']
            rule = next(r for r in rules if r['id'] == rid)
            check(rule['response'] == {'fixed_us': stats['mean_us']}, cid + ' response is native mean')
            check(rule['provenance']['body_residual_used'] is False, cid + ' no Body residual')
            check(hits[rid]['queries'] == {'observable_response': group['calls_per_forward']}, cid + ' one inclusive response per native call')
            check(hits[rid]['response_us_min'] == hits[rid]['response_us_max'] == stats['mean_us'], cid + ' exact response applied')
            check(all(not isinstance(v, list) for v in rule['match'].values()), cid + ' physical scalar selectors')
            added.append({k: group[k] for k in ('native_operator_type', 'declared_role', 'calls_per_forward', 'normalized_contract')}
                         | {'count': stats['count'], 'mean_us': stats['mean_us'], 'p50_us': stats['p50_us']})
        scheduled = row['prediction']['scheduled_operator_summary']['groups']
        removed = {'hc_values_fp32', 'hc_projection', 'hc_inverse_rms', 'hc_normalize_scale_bias_gate', 'hc_sinkhorn', 'hc_pre_mix'}
        check(not any(g['recipe'] in removed for g in scheduled), cid + ' no former standalone HC phase scheduled')
        check(sum(g['scheduled_elapsed_ms']['count'] for g in scheduled if g['recipe'] == 'linear_qkvbfg_a') == 34,
              cid + ' 34 QKV scheduled occurrences')
        comparison = row['comparison']
        error = comparison['predicted_ms'] / comparison['observed_ms']['mean'] - 1
        check(abs(error - comparison['relative_error']) < 1e-12, cid + ' Body error arithmetic')
        check(comparison['passed'] == (abs(error) <= .15), cid + ' unrounded tolerance')
        results.append({'case_id': cid, 'forward_count': population['forward_count'],
                        'real_ms': comparison['observed_ms'], 'prior_sim_ms': old['comparison']['predicted_ms'],
                        'predicted_ms': comparison['predicted_ms'], 'relative_error_pct': error * 100,
                        'passed': comparison['passed'], 'new_native_groups': added})
    review = {'schema_version': 'mindie-observed-service-replay-review/1', 'status': 'failed' if failures else 'passed',
              'checks': checks, 'failures': failures, 'cases': results,
              'replay_identity': pin(dest / 'decode-forward-service-replay.json'),
              'population_identity': pin(dest / 'observed-populations.json'), 'reviewer_identity': pin(__file__),
              'runtime_comparison_caution': 'Previous arm used 2f48346b; this arm uses 3b72ea2d. Its delta is not an isolated HC experiment.',
              'review_corrections': ['The first selection comparison retained an empty traffic_profile dictionary after removing the added HC key. Normalizing this added-empty container restores the exact original selector; no case, prediction or observed value changed.'],
              'execution': {'raw_scans': 0, 'new_costs': 0}}
    write(dest / 'service-regime-review.json', review)
    lines = ['# GLM HC atomic source arm', '',
             'The existing arch35 HCPre provider replaces 540 standalone semantic phases with 90 native occurrences per Forward. The complete retained normalized contract covers the premix-absent branch; it does not establish capture binary identity or optional output storage aliases. Each atomic call receives its observed whole-call Mean once. The 34 QKV projection calls receive their independently observed Mean. Previous nine parameters remain unchanged.', '',
             '| Source | F | Real Mean / P50 / P90 ms | Previous Sim ms | Current Sim ms | Error | Body result |',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in results:
        o = r['real_ms']
        lines.append(f"| {r['case_id']} | {r['forward_count']} | {o['mean']:.6f} / {o['p50']:.6f} / {o['p90']:.6f} | {r['prior_sim_ms']:.6f} | {r['predicted_ms']:.6f} | {r['relative_error_pct']:+.2f}% | {'PASS' if r['passed'] else 'FAIL'} |")
    lines += ['', 'All three remain outside the 15% Body tolerance. Source-consistent fusion reduces prediction rather than adding arbitrary delay; the old decomposition is not restored to improve error. The prior runtime was 2f48346b and this runtime is 3b72ea2d, so the difference is not attributed solely to HC.', '',
              'All eleven regimes hit exactly their declared native multiplicities. These are explicit in-sample measured service parameters, not a held-out validation and not a claim that every native ABI is closed. Scheduled family intervals include contention and are not additive Body budgets.', '',
              'Slice (224 calls/F) and SparseFlashMlaMetadata (11 calls/F) remain separate unresolved physical-boundary work. No observed time is attached to an unproven view/copy/metadata mapping.', '',
              f'Retained-population/rule review: {checks} checks, {len(failures)} failures. Body arithmetic and unchanged source/geometry checks are in body-independent-review.json. Three fresh predictions, no raw parsing or device collection; the shared replay validates source file identities.', '',
              'Reproduce: run ../build_third_pass.py with fixed 3b72ea2d on PYTHONPATH, then replay decode-forward-service-cases.json via ../../replay_decode_forwards.py with --geometry-limit 1 --prediction-timeout 90, and run ../review_third_pass.py.']
    (dest / 'README.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'checks': checks, 'failures': failures, 'passed': sum(r['passed'] for r in results)}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
