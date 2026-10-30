"""[Role] Audit packed-prolog populations against the formal profiler contract.
[Invariants] Both complete query-norm branches retain their native ABI and one
  inclusive local service; no cache capacity is converted into active work.
[Timeouts & Locks] Bounded local metadata and streaming receipt; no costs/locks.
[Side-Effect Policy] Write a parameter review only, preserving all case inputs.
"""
from collections import Counter
import json
import math
from pathlib import Path
import resource

import ijson

from build_glm78_native_service_cases import descriptor
from mindie_profiler.tensor_contracts import observed_contract
from review_glm78_tail_service import digest, read

BASE = Path(__file__).resolve().parent / 'acceptance-20261030-a3-tail-service-refinement/glm78-prolog'


def main():
    checks = 0; failures = []; results = []
    def check(value, reason):
        nonlocal checks
        checks += 1
        if not value: failures.append(reason)
    proof = read(BASE / 'prolog-service-populations.json')
    check(digest(proof['contract_parser_identity']['path']) == proof['contract_parser_identity']['sha256'], 'Formal packed parser pin')
    cases = {r['case_id']: r for r in proof['cases']}
    path = BASE / 'decode-forward-prolog-service-replay.json'
    with path.open('rb') as stream:
        for row in ijson.items(stream, 'cases.item', use_float=True):
            if row['comparison']['status'] != 'compared': continue
            item = cases[row['source_case_id']]; label = row['case_id']
            for key in ('prior_case_identity', 'case_identity'):
                check(digest(item[key]['path']) == item[key]['sha256'], label + ' ' + key)
            old = read(item['prior_case_identity']['path'])['runtime']['kernels']['service_regimes']
            new = read(item['case_identity']['path'])['runtime']['kernels']['service_regimes']
            check(new[:len(old)] == old and len(new) == len(old) + 2, label + ' old rules unchanged')
            check(row['model_structure_identity']['sha256'] == item['case_identity']['sha256'], label + ' executed case')
            declared = {r['id']: r for r in new}
            executed = {r['id']: r for r in row['prediction']['parameters']['service_regimes']}
            all_parts = set(); hits = 0
            for evidence in item['added_rules']:
                rid = evidence['rule_id']; prefix = label + ' ' + rid
                pin = evidence['native_identity']; check(digest(pin['path']) == pin['sha256'], prefix + ' complete native pin')
                native = read(pin['path'])
                check(native['source_identity']['sha256'] == row['source_identity']['sha256'], prefix + ' own source')
                expected = [i for i, p in enumerate(native['partitions']) if p['native_operator_type'] == 'MlaPrologV3'
                            and bool(p['native_abi'][3][5][0]) == evidence['query_norm_output']]
                check(expected == evidence['partition_indices'], prefix + ' entire output-presence domain')
                all_parts.update(expected); counter = Counter()
                for i in expected:
                    part = native['partitions'][i]
                    counter.update({int(ns): int(n) for ns, n in part['duration_ns_counter']})
                    contract = observed_contract(descriptor(part['native_abi']))
                    check(json.loads(json.dumps(contract)) == evidence['active_contract'], prefix + ' formal active contract')
                n = sum(counter.values()); mean = sum(ns * count for ns, count in counter.items()) / n / 1000
                check(sorted(counter.items()) == [tuple(x) for x in evidence['complete_population']['duration_ns_counter']], prefix + ' full histogram')
                check(n == native['forward_count'] * evidence['expected_rule_hits'], prefix + ' native multiplicity')
                rule = declared[rid]; actual = executed[rid]
                check(math.isclose(rule['response']['fixed_us'], mean, rel_tol=1e-13), prefix + ' complete native mean')
                for field in ('match', 'response', 'execution', 'provenance'):
                    check(actual[field] == rule[field], prefix + ' actual ' + field)
                check(actual['queries'] == {'joint_native_service': evidence['expected_rule_hits']}, prefix + ' inclusive execution once')
                check(not evidence['body_residual_used'] and not evidence['strict_tensor_admission_changed'], prefix + ' no residual fit or admission change')
                hits += evidence['expected_rule_hits']
            check(hits == 78 and len(all_parts) == 2, label + ' full 57 + 21 prolog population')
            results.append({'case_id': label, 'body_relative_error': row['comparison']['relative_error'], 'body_passed': row['comparison']['passed']})
    check(len(results) == len(cases), 'All three primary populations')
    result = {'status': 'failed' if failures else 'passed', 'checks': checks, 'failures': failures,
              'report_sha256': digest(path), 'cases': results,
              'execution': {'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            'new_cost_predictions': 0, 'raw_scans': 0}}
    (BASE / 'parameter-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'checks', 'failures', 'execution')}))
    return int(bool(failures))


if __name__ == '__main__':
    raise SystemExit(main())
