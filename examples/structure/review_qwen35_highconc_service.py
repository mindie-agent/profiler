"""Check saved complete native populations and executed source response queries.

[Role] Review Q35 high-concurrency parameters independently of the case builder.
[Invariants] Full integer histograms determine means; selected and deferred Body
  populations remain separate. Source responses do not promote strict contracts.
[Timeouts & Locks] Read bounded retained JSON only; no locks, raw scan or cost.
[Side-Effect Policy] Write a compact parameter review and human-readable summary.
"""
from collections import Counter
from hashlib import sha256
import json
from math import isclose
from pathlib import Path

BASE = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement/qwen35-a5'


def load(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('oversized_metadata')
    return json.loads(path.read_text())


def review():
    evidence = load(BASE / 'observed-populations.json')
    report = load(BASE / 'decode-forward-replay.compact.json')
    rows = {r['source_case_id']: r for r in report['cases'] if r['comparison']['status'] == 'compared'}
    checks, failures, summaries = 0, [], []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def pinned(pin):
        path = Path(pin['path'])
        check(sha256(path.read_bytes()).hexdigest() == pin['sha256'], 'identity:' + str(path))
        return load(path)

    for item in evidence['cases']:
        name = item['case_id']; row = rows[name]
        case = pinned(item['case_identity']); baseline = pinned(item['baseline_case_identity'])
        rules = {r['id']: r for r in case['runtime']['kernels']['service_regimes']}
        actual_rules = {r['id']: r for r in row['prediction']['parameters']['service_regimes']}
        check(row['model_structure_identity']['sha256'] == item['case_identity']['sha256'], name + ':executed_case')
        check(row['source_identity']['sha256'] == item['source_identity']['sha256'], name + ':source')
        check(row['comparison']['observed_ms']['count'] == item['forward_count'], name + ':full_selected_population')
        removed = {r['id'] for r in item['replaced_rules']}
        for old in baseline['runtime']['kernels']['service_regimes']:
            check(old['id'] in removed or rules.get(old['id']) == old, name + ':prior_rule_preserved')
        check(removed.isdisjoint(rules), name + ':old_grouped_response_removed')
        for rule in item['new_rules']:
            prov = rule['provenance']; pop = prov['observed_population']; hist = pop['duration_ns_counter']
            count = sum(c for _, c in hist); duration = sum(ns * c for ns, c in hist)
            label = name + ':' + rule['id']
            check(count == pop['count'], label + ':hist_count')
            check(duration == pop['activity_sum_ns'], label + ':hist_sum')
            check(isclose(duration / count / 1000, rule['response']['fixed_us'], rel_tol=1e-14), label + ':native_mean')
            check(count == prov.get('pooled_target_count', prov['expected_rule_hits']) * item['forward_count'], label + ':native_multiplicity')
            check(prov['source_identity'] == item['source_identity'], label + ':own_source_domain')
            check(not prov['body_residual_used'] and not prov['small_M_value_copied'], label + ':parameter_basis')
            executed = actual_rules[rule['id']]
            check(executed['match'] == rule['match'] and executed['response'] == rule['response'], label + ':executed_response')
            check(executed['queries'] == {'observable_response': prov['expected_rule_hits']}, label + ':exact_native_queries')
            check(executed['response_us_min'] == executed['response_us_max'] == rule['response']['fixed_us'], label + ':whole_call_value')
            if 'native_partition_identity' in prov:
                retained = pinned(prov['native_partition_identity'])
                matching = [p for p in retained['partitions'] if p['role'] == prov['declared_role']]
            else:
                retained = pinned(prov['actual_identity'])
                matching = [f for f in retained['families'] if f['native_operator_type'] == prov['native_operator_type']]
                matching = [f for f in matching if f['duration_ns_counter'] == hist]
            combined = Counter()
            for part in matching:
                combined.update(dict(part['duration_ns_counter']))
            check(sorted(combined.items()) == [tuple(x) for x in hist], label + ':original_full_histogram')
        comp = row['comparison']
        summaries.append({'case_id': name, 'forward_count': item['forward_count'], 'new_rules': len(item['new_rules']),
            'replaced_rules': len(item['replaced_rules']), 'real_ms': comp['observed_ms']['mean'],
            'predicted_ms': comp['predicted_ms'], 'relative_error': comp['relative_error'],
            'passed_15pct': comp['passed'], 'passed_8pct': abs(comp['relative_error']) <= .08,
            'unmatched_rules': row['prediction']['parameters']['regime_selection']['unmatched']})
    result = {'schema_version': 'mindie-observed-service-parameter-review/1', 'status': 'failed' if failures else 'passed',
        'checks': checks, 'failures': failures, 'new_raw_scans': 0, 'new_cost_predictions': 0, 'cases': summaries,
        'report_identity': {'path': str((BASE / 'decode-forward-replay.compact.json').resolve()),
                            'sha256': sha256((BASE / 'decode-forward-replay.compact.json').read_bytes()).hexdigest()},
        'scope': 'Retained full native histograms, own-source means, executed exact query counts and replacement/preservation of prior rules; no new graph export or Engine service trace verification.'}
    (BASE / 'parameter-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    review()
