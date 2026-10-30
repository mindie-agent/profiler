"""Check complete-cohort service parameters against immutable native histograms.

[Role] Reconcile retained active contracts and executed service hits.
[Invariants] No simulation or raw read; each source histogram remains complete,
  original case physics stays unchanged, and rule predicates contain no IDs.
[Timeouts & Locks] One small source at a time; no subprocess or locks.
[Side-Effect Policy] Writes a producer review, independently of the case builder.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource
from statistics import median


def review():
    root = Path(__file__).resolve().parent / 'acceptance-20261030-service-qwen-a3'
    report_path = root / 'decode-forward-qwen-cohort-service-replay.json'
    report = json.loads(report_path.read_text())
    manifest = json.loads((root / 'decode-forward-qwen-cohort-service-cases.json').read_text())
    inputs = {row['case_id']: row for row in manifest['cases']}
    checks, failures, populations = 0, [], []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def load(pin):
        path = Path(pin['path'])
        raw = path.read_bytes()
        check(sha256(raw).hexdigest() == pin['sha256'], str(path) + ':sha')
        return json.loads(raw)

    for result in report['cases']:
        row = inputs[result['source_case_id']]
        case = load(row['model_declaration'])
        baseline = load(row['baseline_service_case_identity'])
        rules = case['runtime']['kernels'].pop('service_regimes')
        before = baseline['runtime']['kernels'].pop('service_regimes')
        case['runtime']['metadata'].pop('calibration_evidence')
        baseline['runtime']['metadata'].pop('calibration_evidence')
        check(case == baseline, row['case_id'] + ':nonparameter_case_unchanged')
        check(rules[:len(before)] == before, row['case_id'] + ':existing_rules_unchanged')
        parameters = result['prediction']['parameters']
        hits = {entry['id']: entry for entry in parameters['service_regimes']}
        check(parameters['regime_selection']['unmatched'] == [], row['case_id'] + ':none_unmatched')
        check(len(rules) == 18 and len(hits) == 18, row['case_id'] + ':eighteen_rules')
        actual = mapping = None
        for rule in rules[len(before):]:
            p = rule['provenance']
            if actual is None:
                actual, mapping = load(p['actual_identity']), load(p['mapping_identity'])
            cohort = next(co for w in mapping['windows'] for co in w['cohorts']
                          if co['cohort_id'] == p['retained_cohort_id'])
            check(all(w['source_identity']['sha256'] == row['source']['sha256']
                      for w in mapping['windows']), rule['id'] + ':mapping_source')
            check(actual['source_identity']['sha256'] == row['source']['sha256'], rule['id'] + ':actual_source')
            family = next(f for f in actual['families']
                          if f['native_operator_type'] == cohort['native_operator_type']
                          and set(f['candidate_target_ids']) == set(cohort['target_ids']))
            histogram = Counter(dict(family['duration_ns_counter']))
            count = sum(histogram.values())
            activity_ns = sum(ns * n for ns, n in histogram.items())
            check(count == cohort['event_count'], rule['id'] + ':complete_count')
            check(activity_ns == cohort['activity_sum_ns'], rule['id'] + ':complete_activity')
            check(count == actual['forward_count'] * len(cohort['target_ids']), rule['id'] + ':multiplicity')
            check(p['contract'] == cohort['contract'] and p['contract_scope'] == cohort['contract_scope'],
                  rule['id'] + ':contract_boundary_preserved')
            check(abs(rule['response']['fixed_us'] - activity_ns / count / 1000) < 1e-10,
                  rule['id'] + ':native_mean_parameter')
            samples = [ns for ns, n in histogram.items() for _ in range(n)]
            check(abs(median(samples) / 1000 - p['observed_us']['p50']) < 1e-10,
                  rule['id'] + ':native_p50')
            expected = count / actual['forward_count']
            check(hits[rule['id']]['queries'] == {'observable_response': expected}, rule['id'] + ':executed_once')
            check(not any(k.startswith(('op_id', 'model', 'metadata.layer')) for k in rule['match']),
                  rule['id'] + ':physical_selector')
            check(p['evaluation_relation'] == 'in_sample' and p['body_residual_used'] is False,
                  rule['id'] + ':observable_origin')
            populations.append({'case_id': row['case_id'], 'rule_id': rule['id'], 'observed_calls': count,
                                'matched_calls_per_forward': expected, 'missed_calls_per_forward': 0})
        for rule in rules[:len(before)]:
            p = rule['provenance']
            expected = p.get('expected_rule_hits', p.get('expected_calls_per_forward'))
            check(hits[rule['id']]['queries'] == {'observable_response': expected}, rule['id'] + ':prior_hits')
        check(result['prediction_execution']['reused_prediction'] is False, row['case_id'] + ':fresh_prediction')
        check(result['prediction_execution']['execution']['peak_rss_bytes'] <= 512 * 1024**2,
              row['case_id'] + ':bounded_worker')
    output = {'schema_version': 'mindie-observed-service-review/1', 'status': 'failed' if failures else 'passed',
              'report_sha256': sha256(report_path.read_bytes()).hexdigest(), 'checks': checks,
              'failures': failures, 'matched_new_rules': populations, 'raw_capture_reads': 0, 'new_predictions': 0,
              'review_scope': 'Producer mathematical check independent of generator; standard Body audit is separate.',
              'maximum_resident_set_size_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (root / 'qwen-cohort-service-review.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k != 'matched_new_rules'}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(review())
