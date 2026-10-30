"""Reconcile normalization, quantization and HCPost observed service additions.

[Role] Verify full retained native histograms, fresh selection and actual hit counts.
[Invariants] Homogeneous shape pooling is explicit; prior rule bytes and values
  remain exact. No Body difference becomes a response parameter.
[Timeouts & Locks] Saved bounded JSON; no capture, subprocess or lock.
[Side-Effect Policy] Writes this arm's compact review and README only.
"""
from build_service_cases import HERE, pin, read, write, summarize

DEST = HERE / 'norm-quant-post-pass'


def main():
    path = DEST / 'decode-forward-service-replay.json'; report = read(path)
    population = read(DEST / 'observed-populations.json')
    old_report = read(HERE / 'matrix-slice-pass/decode-forward-service-replay.json')
    old = {r['source_case_id']: r for r in old_report['cases'] if r['status'] == 'compared'}
    rows = {r['source_case_id']: r for r in report['cases'] if r['status'] == 'compared'}
    checks, failures, results = 0, [], []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    check(len(rows) == 9 and report['status'] == 'completed', 'all nine complete')
    check(report['runtime_generation']['unchanged'], 'same runtime throughout')
    check(report['runtime_generation']['start'] == old_report['runtime_generation']['start'], 'unchanged previous runtime')
    for p in population['cases']:
        cid = p['case_id']; current = rows[cid]; previous_row = old[cid]
        case = read(p['case_identity']['path']); previous = read(p['prior_case_identity']['path'])
        for key in ('case_identity', 'prior_case_identity'):
            check(pin(p[key]['path']) == p[key], cid + '/' + key)
        rules = case['runtime']['kernels']['service_regimes']; prior = previous['runtime']['kernels']['service_regimes']
        check(rules[:-7] == prior and len(rules) == len(prior)+7, cid + '/all prior responses exact')
        check(current['observed'] == previous_row['observed'], cid + '/all observed statistics unchanged')
        check(current['geometry'] == previous_row['geometry'], cid + '/same geometry')
        check(current['source_identity'] == previous_row['source_identity'], cid + '/same source')
        check(current['calibration_origin'] == 'observed' and current['calibration_evidence']['evaluation_relation'] == 'in_sample', cid + '/measured in-sample parameter')
        for key in ('model', 'machine', 'workload'):
            check(case[key] == previous[key], cid + '/unchanged ' + key)
        options = case['runtime']['kernels']['lowerings']['native_fusion']['options']
        check(options['roles'].count('hc_post') == 1, cid + '/HCPost selected once')
        check(options['traffic_profile']['hc_post'] == 'hc_post_arch35_bf16_175ef4d4', cid + '/source profile')
        parameters = current['prediction']['parameters']
        hits = {r['id']:r for r in parameters['service_regimes']}
        check(not parameters['regime_selection']['unmatched'], cid + '/all rules applied')
        check(len(hits) == len(rules), cid + '/rule total')
        previous_hits = {r['id']:r for r in previous_row['prediction']['parameters']['service_regimes']}
        for rid, previous_hit in previous_hits.items():
            for field in ('queries', 'response_us_min', 'response_us_max'):
                check(hits[rid][field] == previous_hit[field], cid + '/prior applied response ' + rid + '/' + field)
        family_indices = set(); expected_added_calls = 0
        for g in p['groups']:
            ap, mp = g['actual_identity'], g['mapping_identity']; rid = g['rule_id']
            check(pin(ap['path']) == ap and pin(mp['path']) == mp, cid + '/' + rid + '/source pins')
            actual, mapping = read(ap['path']), read(mp['path'])
            fs = [actual['families'][i] for i in g['family_indices']]
            check(not (family_indices & set(g['family_indices'])), cid + '/' + rid + '/disjoint family populations')
            family_indices.update(g['family_indices'])
            check(all(f['native_operator_type'] == g['native_operator_type'] and f['declared_role'] in g['declared_roles'] for f in fs), cid + '/' + rid + '/native and roles')
            stats = summarize(fs); check(stats == g['observed'], cid + '/' + rid + '/complete histogram')
            check(stats['count'] == p['forward_count'] * g['calls_per_forward'], cid + '/' + rid + '/native multiplicity')
            ids = set(g['retained_cohort_ids'])
            cohorts = [c for w in mapping['windows'] for c in w['cohorts'] if c['cohort_id'] in ids]
            check(len(cohorts) == len(ids), cid + '/' + rid + '/all retained cohorts')
            check(all(c['contract'] == g['normalized_contract'] for c in cohorts), cid + '/' + rid + '/same physical contract')
            check(sum(c['complete_event_count'] for c in cohorts) == stats['count'], cid + '/' + rid + '/cohort count')
            check(sum(c['complete_activity_sum_ns'] for c in cohorts) == sum(ns*n for ns,n in stats['duration_ns_counter']), cid + '/' + rid + '/cohort activity')
            rule = next(r for r in rules if r['id'] == rid)
            check(rule['response'] == {'fixed_us': stats['mean_us']}, cid + '/' + rid + '/measured response')
            check(rule['provenance']['body_residual_used'] is False, cid + '/' + rid + '/no Body fit')
            check(hits[rid]['queries'] == {'observable_response': g['calls_per_forward']}, cid + '/' + rid + '/applied once per native')
            check(hits[rid]['response_us_min'] == hits[rid]['response_us_max'] == stats['mean_us'], cid + '/' + rid + '/exact response value')
            check(not set(rule['match']) & {'op_id','layer','model'}, cid + '/' + rid + '/physical selector')
            expected_added_calls += g['calls_per_forward']
        check(expected_added_calls == 270, cid + '/complete added native calls')
        comp = current['comparison']; error = comp['predicted_ms']/comp['observed_ms']['mean']-1
        check(abs(error-comp['relative_error']) < 1e-12, cid + '/Body error arithmetic')
        check(comp['passed'] == (abs(error) <= .15), cid + '/unrounded tolerance')
        results.append({'case_id':cid,'forward_count':p['forward_count'], 'body':comp,
            'prior_predicted_ms':previous_row['comparison']['predicted_ms'], 'regime_count':len(rules),
            'added_native_calls_per_forward':270, 'runtime_identity':current['runtime_identity']})
    write(DEST / 'service-regime-review.json', {'schema_version':'mindie-norm-quant-post-service-review/1',
        'status':'failed' if failures else 'passed','checks':checks,'failures':failures,
        'report_identity':pin(path),'population_identity':pin(DEST / 'observed-populations.json'),
        'reviewer_identity':pin(__file__),'cases':results,'raw_scans':0,'new_costs':0})
    lines=['# GLM complete normalization, quantization and HCPost service','',
        'All nine sources retain their prior matrix/Slice and eleven original responses. The same seven additions apply throughout: attention and FFN RMSNorm (45+45 calls/F), quantization at three physical shapes (45+3+42), and attention/FFN native HCPost (45+45). HCPost uses the existing arch35 BF16 whole-call provider; the former 90 semantic nodes are replaced once.', '',
        'Dense and shared gate-up quantization share one exact physical shape/contract. Their complete 3+42 call populations are pooled by event count into one explicit joint response; this is not an independently identified per-role latency. Other blocks/shapes remain separate. All parameters are observed, in-sample and derived from full histograms, never Body error.', '',
        '| Source | F | Real Mean / P50 / P90 ms | Previous Sim ms | New Sim ms | Error | Body | Rules |',
        '|---|---:|---:|---:|---:|---:|---|---:|']
    for r in results:
        c=r['body'];o=c['observed_ms']
        lines.append(f"| {r['case_id']} | {r['forward_count']} | {o['mean']:.6f} / {o['p50']:.6f} / {o['p90']:.6f} | {r['prior_predicted_ms']:.6f} | {c['predicted_ms']:.6f} | {c['relative_error']*100:+.2f}% | {'PASS' if c['passed'] else 'FAIL'} | {r['regime_count']} |")
    lines += ['',f"{sum(r['body']['passed'] for r in results)}/9 Body PASS; {checks} retained-population/application checks, {len(failures)} failures. All nine were reevaluated regardless of earlier result. No raw scan or device work.", '',
        'Remaining metadata, unidentified native matrix/elementwise and unpartitioned Slice populations are not assigned synthetic prices. Native activity sums and scheduled intervals are not additive Body causal budgets. Body PASS does not mean all native ABI contracts are closed.', '',
        'Reproduce with fixed 672a595f: ../build_norm_quant_post_pass.py, replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90, ../review_norm_quant_post_pass.py and review_decode_predictions.py.']
    (DEST/'README.md').write_text('\n'.join(lines)+'\n')
    print({'checks':checks,'failures':failures,'passed':sum(r['body']['passed'] for r in results)})
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
