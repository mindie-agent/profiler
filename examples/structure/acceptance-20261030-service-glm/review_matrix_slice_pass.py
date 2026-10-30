"""Check complete native populations and applied matrix/Slice service responses.

[Role] Reconcile stored histograms, contract cohorts, fresh inputs and rule hits.
[Invariants] No time fitted from Body error; no copied response between shapes.
  First eleven rules are unchanged, unresolved Slice populations remain unpriced.
[Timeouts & Locks] Finite retained JSON only; no locks or subprocesses.
[Side-Effect Policy] Writes this arm's review/README; no raw scan or prediction.
"""
from collections import Counter
from copy import deepcopy

from build_service_cases import HERE, pin, read, write, summarize

DEST = HERE / 'matrix-slice-pass'


def main():
    report_path = DEST / 'decode-forward-service-replay.json'
    report = read(report_path)
    populations = read(DEST / 'observed-populations.json')
    current = {r['source_case_id']: r for r in report['cases'] if r['status'] == 'compared'}
    earlier = {r['case_id']: r for r in read(HERE / 'third-pass-all-nine.json')['cases']}
    checks, failures, results = 0, [], []

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(label)

    check(len(current) == 9 and report['status'] == 'completed', 'nine completed predictions')
    check(report['runtime_generation']['unchanged'], 'runtime unchanged')
    for entry in populations['cases']:
        cid = entry['case_id']; row = current[cid]
        case, previous = read(entry['case_identity']['path']), read(entry['prior_case_identity']['path'])
        for key in ('case_identity', 'prior_case_identity'):
            check(pin(entry[key]['path']) == entry[key], cid + '/' + key)
        rules = case['runtime']['kernels']['service_regimes']
        check(rules[:11] == previous['runtime']['kernels']['service_regimes'], cid + '/prior eleven exact')
        check(len(rules) == 11 + len(entry['groups']), cid + '/new regime total')
        for key in ('model', 'machine', 'workload'):
            check(case[key] == previous[key], cid + '/unchanged ' + key)
        check(row['comparison']['observed_ms'] == earlier[cid]['comparison']['observed_ms'], cid + '/same observed population')
        check(all(row['source_identity'][k] == entry['source_identity'][k]
                  for k in ('path', 'sha256', 'size_bytes')), cid + '/same source')
        parameters = row['prediction']['parameters']
        hits = {r['id']: r for r in parameters['service_regimes']}
        check(not parameters['regime_selection']['unmatched'], cid + '/no unmatched regime')
        check(len(hits) == len(rules), cid + '/every regime applied')
        fresh_by_id = {r['id']: r for r in rules}
        for group in entry['groups']:
            rid = group['rule_id']; rule = fresh_by_id[rid]
            if 'actual_identity' in group:
                ap, mp = group['actual_identity'], group['mapping_identity']
                check(pin(ap['path']) == ap and pin(mp['path']) == mp, cid + '/' + rid + '/pins')
                actual, mapping = read(ap['path']), read(mp['path'])
                selected = [actual['families'][i] for i in group['family_indices']]
                check(all(f['native_operator_type'] == group['native_operator_type'] and
                          f['declared_role'] == group['declared_role'] for f in selected), cid + '/' + rid + '/family roles')
                stats = summarize(selected)
                ids = set(group['retained_cohort_ids'])
                cohorts = [c for w in mapping['windows'] for c in w['cohorts'] if c['cohort_id'] in ids]
                check(len(cohorts) == len(ids), cid + '/' + rid + '/cohort existence')
                check(sum(c['complete_event_count'] for c in cohorts) == stats['count'], cid + '/' + rid + '/cohort count')
                check(sum(c['complete_activity_sum_ns'] for c in cohorts) ==
                      sum(ns*n for ns,n in stats['duration_ns_counter']), cid + '/' + rid + '/cohort activity')
                check(all(c['contract'] == group['normalized_contract'] for c in cohorts), cid + '/' + rid + '/contracts')
            else:
                p = group['partition_identity']; check(pin(p['path']) == p, cid + '/' + rid + '/partition pin')
                doc = read(p['path']); parts = [doc['partitions'][i] for i in group['partition_indices']]
                check(doc['source_identity']['sha256'] == entry['source_identity']['sha256'], cid + '/' + rid + '/source')
                check(doc['forward_count'] == entry['forward_count'], cid + '/' + rid + '/body population')
                check(all(p['native_abi'] == group['native_abi'] and p['native_operator_type'] == 'Slice' for p in parts), cid + '/' + rid + '/full Slice ABI')
                stats = summarize(parts)
                check(group['calls_per_forward'] == 34, cid + '/' + rid + '/copy multiplicity')
                check(group['normalized_contract'][2] == group['native_abi'][3][0][0], cid + '/' + rid + '/actual output view')
                check(group['normalized_contract'][1] == group['native_abi'][2][0][0], cid + '/' + rid + '/actual input view')
            check(stats == group['observed'], cid + '/' + rid + '/complete integer histogram stats')
            check(stats['count'] == entry['forward_count'] * group['calls_per_forward'], cid + '/' + rid + '/calls per Forward')
            check(rule['response'] == {'fixed_us': stats['mean_us']}, cid + '/' + rid + '/observed mean only')
            check(rule['provenance']['body_residual_used'] is False, cid + '/' + rid + '/no Body fit')
            check(hits[rid]['queries'] == {'observable_response': group['calls_per_forward']}, cid + '/' + rid + '/exact actual application count')
            check(hits[rid]['response_us_min'] == hits[rid]['response_us_max'] == stats['mean_us'], cid + '/' + rid + '/response exact')
            check(not any(k in {'op_id', 'layer', 'model'} for k in rule['match']), cid + '/' + rid + '/physical selector')
        # Old rules remain source-pinned complete populations, and all are still
        # applied at the same native multiplicity despite the two new copy nodes.
        for rule in rules[:11]:
            prov = rule['provenance']; native = prov['native_operator_type']
            actual = read(prov['actual_identity']['path'])
            families = [f for f in actual['families'] if f['native_operator_type'] == native]
            if native == 'MatMulV3': families = [f for f in families if f['declared_role'] == 'linear_qkvbfg_a']
            if native == 'GroupedMatmul': families = [f for f in families if f['declared_role'] == 'expert_down']
            stats = summarize(families)
            check(stats['mean_us'] == rule['response']['fixed_us'], cid + '/prior population ' + rule['id'])
            check(hits[rule['id']]['queries']['observable_response'] * entry['forward_count'] == stats['count'], cid + '/prior multiplicity ' + rule['id'])
        copies = entry['source_materializations']
        check(len(copies) == 2 and all(c['fresh_declared_instances'] == 34 for c in copies), cid + '/two independent source copies')
        for missing in [c for c in copies if c['status'] != 'observed_response']:
            check(not any(g['declared_role'] == missing['recipe'] for g in entry['groups']), cid + '/no unobserved copy response')
        comp = row['comparison']; expected = comp['predicted_ms'] / comp['observed_ms']['mean'] - 1
        check(abs(comp['relative_error'] - expected) < 1e-12, cid + '/Body arithmetic')
        check(comp['passed'] == (abs(expected) <= .15), cid + '/unrounded tolerance')
        results.append({'case_id': cid, 'forward_count': entry['forward_count'], 'body': comp,
            'previous_predicted_ms': earlier[cid]['comparison']['predicted_ms'],
            'regime_count': len(rules), 'new_matrix_calls_per_forward': 199,
            'new_slice_observed_calls_per_forward': sum(c.get('calls_per_forward', 0) for c in copies),
            'runtime_identity': row['runtime_identity'], 'prediction_execution': row['prediction_execution']})
    value = {'schema_version': 'mindie-matrix-slice-service-review/1',
        'status': 'failed' if failures else 'passed', 'checks': checks, 'failures': failures,
        'report_identity': pin(report_path), 'population_identity': pin(DEST / 'observed-populations.json'),
        'reviewer_identity': pin(__file__), 'cases': results, 'raw_scans': 0, 'new_costs': 0,
        'review_corrections': ['Initial source-dictionary equality compared replay schema/mtime metadata with a compact path/size/SHA identity. Final review checks the three shared immutable source fields; no observation, rule, cost or source identity changed.']}
    write(DEST / 'service-regime-review.json', value)
    lines = ['# GLM complete matrix and packed KDA copy service', '',
        'Nine previously unified HC sources are all evaluated. Each adds nine complete matrix cohorts (199 calls/Forward) with shape-specific native Mean, while keeping the prior eleven responses unchanged. Two common tensor materializations are enabled for all nine: convolution input and KDA beta, each 34 calls/Forward. Only the three sources with full retained Slice ABI/histograms receive their own observed copy responses; the other six retain physical copy cost without borrowed parameters.', '',
        '| Source | F | Real Mean/P50/P90 ms | Previous Sim ms | New Sim ms | Error | Body | Rules | Observed new Slice calls/F |',
        '|---|---:|---:|---:|---:|---:|---|---:|---:|']
    for r in results:
        c=r['body'];o=c['observed_ms']
        lines.append(f"| {r['case_id']} | {r['forward_count']} | {o['mean']:.6f}/{o['p50']:.6f}/{o['p90']:.6f} | {r['previous_predicted_ms']:.6f} | {c['predicted_ms']:.6f} | {c['relative_error']*100:+.2f}% | {'PASS' if c['passed'] else 'FAIL'} | {r['regime_count']} | {r['new_slice_observed_calls_per_forward']} |")
    lines += ['', f"{sum(r['body']['passed'] for r in results)}/9 Body PASS. {checks} retained-population and application-count checks, {len(failures)} failures. The runtime changed to 672a595f, so the Body delta is not an isolated matrix/copy causal allocation.", '',
        'All parameters are explicitly observed and in-sample. Matrix geometry normalization does not establish captured tiling or Host occurrence. Slice start-offset scalars are not exported; source-packed layout and actual output geometry support the conditional correspondence. NCL beta input remains in provenance. No whole mixed Slice population, Body residual, metadata CPU latency, or already-covered copy/routing response is used to fill a gap.', '',
        'SparseFlashMlaMetadata remains a typed AI_CPU dependency requiring its own source node. Unresolved MatMul/quant matrix subpopulations remain unchanged. No new raw scan, device call, or measured parameter extrapolation.', '',
        'Reproduce: run ../build_matrix_slice_pass.py with fixed 672a595f on PYTHONPATH, replay decode-forward-service-cases.json with replay_decode_forwards.py --geometry-limit 1 --prediction-timeout 90, then run ../review_matrix_slice_pass.py and review_decode_predictions.py.']
    (DEST / 'README.md').write_text('\n'.join(lines)+'\n')
    print({'checks':checks, 'failures':failures, 'passed':sum(r['body']['passed'] for r in results)})
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
