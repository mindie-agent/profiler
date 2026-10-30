"""Independently reconcile complete native tail responses with executed costs.

[Role] Review the retained native population, case delta and fresh Engine queries.
[Invariants] Inclusive native means occur once; old rules and tensor identities
  remain unchanged. Accuracy failures are valid reviewed results.
[Timeouts & Locks] Bounded local JSON and streaming replay cases; no costs/locks.
[Side-Effect Policy] Read retained artifacts and write one parameter review.
"""
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import resource
import time

import ijson


ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'acceptance-20261030-a3-tail-service-refinement/glm78-indexer-routing'


def digest(path):
    result = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def read(path):
    path = Path(path)
    if path.stat().st_size > 50_000_000:
        raise ValueError('Use streaming for large retained artifacts: ' + str(path))
    return json.loads(path.read_text())


def main():
    started = time.monotonic(); failures = []; checks = 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(reason)

    proof = read(BASE / 'tail-native-input-proof.json')
    proofs = {row['case_id']: row for row in proof['cases']}
    report_path = BASE / 'decode-forward-glm78-tail-replay.json'
    results = []
    with report_path.open('rb') as stream:
        for row in ijson.items(stream, 'cases.item', use_float=True):
            if row['source_case_id'] not in proofs or row['comparison']['status'] != 'compared':
                continue
            item = proofs[row['source_case_id']]
            label = row['case_id']; seen = []
            for field in ('prior_case_identity', 'case_identity'):
                identity = item[field]
                check(digest(identity['path']) == identity['sha256'], label + ' ' + field)
            old = read(item['prior_case_identity']['path'])
            new = read(item['case_identity']['path'])
            old_rules = old['runtime']['kernels']['service_regimes']
            new_rules = new['runtime']['kernels']['service_regimes']
            check(new_rules[:len(old_rules)] == old_rules, label + ' prior rules byte-equivalent')
            check(len(new_rules) == len(old_rules) + len(item['added_rules']), label + ' only new native rules')
            check(row['model_structure_identity']['sha256'] == item['case_identity']['sha256'], label + ' consumed case')
            check(row['source_identity']['sha256'] == item['source_identity']['sha256'], label + ' source population')
            check(row['comparison']['observed_forward_count'] == item['forward_count'], label + ' complete forwards')
            actual_rules = {r['id']: r for r in row['prediction']['parameters']['service_regimes']}
            declared_rules = {r['id']: r for r in new_rules}
            for evidence in item['added_rules']:
                rid = evidence['rule_id']; prefix = label + ' ' + rid
                native_identity = evidence['native_identity']
                check(digest(native_identity['path']) == native_identity['sha256'], prefix + ' retained identity')
                native = read(native_identity['path'])
                partitions = [p for p in native['partitions']
                              if p['native_operator_type'] == evidence['native_operator_type']]
                selected = [native['partitions'][i] for i in evidence['partition_indices']]
                check(partitions == selected, prefix + ' complete native family, no timing selection')
                counter = Counter()
                for part in partitions:
                    counter.update({int(ns): int(count) for ns, count in part['duration_ns_counter']})
                total = sum(counter.values()); mean = sum(ns * count for ns, count in counter.items()) / total / 1000
                check(sorted(counter.items()) == [tuple(x) for x in evidence['complete_population']['duration_ns_counter']], prefix + ' full histogram')
                check(total == item['forward_count'] * evidence['expected_rule_hits'], prefix + ' call multiplicity')
                check([p['native_abi'] for p in partitions] == evidence['full_native_abis'], prefix + ' full ABI including auxiliary outputs')
                rule = declared_rules[rid]; actual = actual_rules[rid]
                check(math.isclose(rule['response']['fixed_us'], mean, rel_tol=1e-13), prefix + ' native mean parameter')
                for field in ('match', 'response', 'execution', 'provenance'):
                    check(actual[field] == rule[field], prefix + ' executed ' + field)
                check(actual['queries'] == {'joint_native_service': evidence['expected_rule_hits']}, prefix + ' one executed native per occurrence')
                check(actual['response_us_min'] == actual['response_us_max'] == rule['response']['fixed_us'], prefix + ' applied response')
                check(rule['execution']['kind'] == 'joint_native', prefix + ' whole local schedule replacement')
                check(not evidence['body_residual_used'] and not evidence['strict_tensor_admission_changed'], prefix + ' unchanged admission and no Body fit')
                check(evidence['evaluation_relation'] == 'in_sample', prefix + ' explicit calibration population')
                seen.append({'native': evidence['native_operator_type'], 'calls_per_forward': evidence['expected_rule_hits'], 'mean_us': mean})
            results.append({'case_id': label, 'native_services': seen,
                            'body_relative_error': row['comparison']['relative_error'],
                            'body_passed': row['comparison']['passed']})
    check(len(results) == len(proofs), 'All primary case populations reviewed')
    result = {'status': 'failed' if failures else 'passed', 'checks': checks, 'failures': failures,
              'report_sha256': digest(report_path), 'proof_sha256': digest(BASE / 'tail-native-input-proof.json'),
              'cases': results, 'execution': {'elapsed_seconds': time.monotonic() - started,
                  'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  'new_cost_predictions': 0, 'raw_scans': 0},
              'scope': 'Executed response/query evidence; compact receipt does not export Engine serviced counters.'}
    (BASE / 'tail-service-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'checks', 'failures', 'execution')}))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
