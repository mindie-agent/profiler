"""[Role] Independently reconcile A3 retained service populations and execution.
[Invariants] Complete native histograms set parameters, not Body differences;
  pooled physical variants retain their shared timing population explicitly.
[Timeouts & Locks] Bounded local artifacts, streaming replay, no costs or locks.
[Side-Effect Policy] Write one independent review; never mutate declarations.
"""
from collections import Counter, defaultdict
import argparse
import json
import math
from pathlib import Path
import resource

import ijson

from review_glm78_tail_service import digest, read


BASE = Path(__file__).resolve().parent / 'acceptance-20261030-a3-tail-service-refinement/retained-cohorts'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, default=BASE)
    parser.add_argument('--proof', default='retained-cohort-service-populations.json')
    parser.add_argument('--report', default='decode-forward-retained-cohort-replay.json')
    args = parser.parse_args(); base = args.directory
    checks = 0; failures = []; results = []
    def check(value, reason):
        nonlocal checks
        checks += 1
        if not value: failures.append(reason)
    def pinned(identity):
        check(digest(identity['path']) == identity['sha256'], 'Pinned ' + identity['path'])
        return read(identity['path'])

    proof = read(base / args.proof)
    cases = {r['case_id']: r for r in proof['cases'] if r.get('prediction_requested', True)}
    path = base / args.report
    with path.open('rb') as stream:
        for row in ijson.items(stream, 'cases.item', use_float=True):
            if row['comparison']['status'] != 'compared': continue
            item = cases[row['source_case_id']]; label = row['case_id']
            prior = item.get('baseline_case_identity') or item['prior_case_identity']
            old, new = pinned(prior), pinned(item['case_identity'])
            old_rules = old['runtime'].get('kernels', {}).get('service_regimes', [])
            new_rules = new['runtime']['kernels']['service_regimes']
            check(new_rules[:len(old_rules)] == old_rules, label + ' all prior declarations unchanged')
            check(len(new_rules) == len(old_rules) + len(item['new_rules']), label + ' exact additions')
            check(row['model_structure_identity']['sha256'] == item['case_identity']['sha256'], label + ' consumed case')
            source = item.get('source_identity') or item['new_rules'][0]['source_identity']
            check(row['source_identity']['sha256'] == source['sha256'], label + ' measured source')
            check(row['comparison']['observed_forward_count'] == item['forward_count'], label + ' Forward population')
            actual = {r['id']: r for r in row['prediction']['parameters'].get('service_regimes', [])}
            declared = {r['id']: r for r in new_rules}; groups = defaultdict(list)
            for evidence in item['new_rules']:
                rid = evidence['rule_id']; prefix = label + ' ' + rid
                rule = declared[rid]; executed = actual[rid]
                if 'actual_identity' in evidence:
                    observation = pinned(evidence['actual_identity'])
                    mapping = pinned(evidence['mapping_identity'])
                    ids = evidence['cohort_ids'] if 'cohort_ids' in evidence else [evidence['cohort_id']]
                    cohorts = [c for w in mapping['windows'] for c in w['cohorts'] if c['cohort_id'] in ids]
                    check(len(cohorts) == len(ids), prefix + ' complete constituent cohorts')
                    parts = []; targets = set()
                    for cohort in cohorts:
                        check(not targets.intersection(cohort['target_ids']), prefix + ' disjoint target populations')
                        targets.update(cohort['target_ids'])
                        selected = [f for f in observation['families']
                                    if f['native_operator_type'] == evidence['native_operator_type']
                                    and set(f['candidate_target_ids']) == set(cohort['target_ids'])]
                        check(len(selected) == 1, prefix + ' unique complete mapped family')
                        parts.extend(selected)
                        check(cohort['contract'] == evidence['active_contract'], prefix + ' retained active contract')
                else:
                    observation = pinned(evidence['observation_identity'])
                    population, = [g for g in observation['body_geometry_groups']
                        if all(g['geometry'][k] == row['geometry'][k]
                               for k in ('query_rows', 'tokens_per_sequence', 'sequences_per_replica'))]
                    parts = [g for g in population['groups']
                             if g['native_operator_type'] == evidence['native_operator_type']
                             and g['event_category'] in ('collective_envelope_only', 'collective_device_task')]
                    check(population['forward_count'] == item['forward_count'], prefix + ' HCCL Forward population')
                    check(not evidence['pure_link_rate_identified'], prefix + ' collective elapsed is not bandwidth')
                check(observation['source_identity']['sha256'] == source['sha256'], prefix + ' own source mean')
                counter = Counter()
                for part in parts:
                    counter.update({int(ns): int(count) for ns, count in part['duration_ns_counter']})
                n = sum(counter.values()); total = sum(ns * count for ns, count in counter.items())
                stats = evidence['complete_population']
                check(sorted(counter.items()) == [tuple(pair) for pair in stats['duration_ns_counter']], prefix + ' complete histogram')
                check(n == item['forward_count'] * evidence['pooled_native_invocations'], prefix + ' complete native calls')
                check(math.isclose(rule['response']['fixed_us'], total / n / 1000, rel_tol=1e-13), prefix + ' exact per-call mean')
                for field in ('match', 'response', 'provenance'):
                    check(executed[field] == rule[field], prefix + ' actual ' + field)
                check(executed['queries'] == {'observable_response': evidence['expected_rule_hits']}, prefix + ' actual occurrence count')
                check(not evidence['body_residual_used'] and not evidence['old_predicted_cost_used'], prefix + ' no residual fitting')
                key = (evidence['native_operator_type'], tuple(evidence.get('cohort_ids', [])),
                       evidence.get('cohort_id'), digest_json(stats))
                groups[key].append(evidence)
            for key, rules in groups.items():
                check(sum(r['expected_rule_hits'] for r in rules) == rules[0]['pooled_native_invocations'], label + ' pooled calls counted once ' + key[0])
            if 'old_noncommunication_work' in item:
                check(item['old_noncommunication_work'] == item['new_noncommunication_work'], label + ' noncommunication work conserved')
                check(sum(item['old_reductions'].values()) == 231 and sum(item['new_reductions'].values()) == 156,
                      label + ' source caller reduction populations')
                check(sum(r['expected_rule_hits'] for r in item['new_rules']) == 156, label + ' captured collectives used once')
            results.append({'case_id': label, 'new_rules': len(item['new_rules']),
                            'body_relative_error': row['comparison']['relative_error'],
                            'body_passed': row['comparison']['passed']})
    check(len(results) == len(cases), 'All primary populations reviewed')
    report = {'status': 'failed' if failures else 'passed', 'checks': checks, 'failures': failures,
              'report_sha256': digest(path), 'proof_sha256': digest(base / args.proof),
              'cases': results, 'execution': {'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'new_cost_predictions': 0, 'raw_scans': 0}}
    (base / 'parameter-independent-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'checks', 'failures', 'execution')}))
    return int(bool(failures))


def digest_json(value):
    from hashlib import sha256
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


if __name__ == '__main__':
    raise SystemExit(main())
