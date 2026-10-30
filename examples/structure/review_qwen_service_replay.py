"""Audit retained populations and executed observable-service rule counts.

[Role] Independently check the Qwen service replay's measured parameters.
[Invariants] No Body error selects a parameter; full native histograms determine
  means. Runtime hits must equal the complete per-Forward source population.
[Timeouts & Locks] Small retained JSON only; no subprocess or locks.
[Side-Effect Policy] Write one review JSON; no raw capture read or simulation.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource


def review(directory):
    checks, failures, hits = 0, [], []
    def check(value, label):
        nonlocal checks
        checks += 1
        if not value:
            failures.append(label)
    def read(path):
        return json.loads(Path(path).read_text())
    def validate(pin):
        path = Path(pin['path'])
        check(sha256(path.read_bytes()).hexdigest() == pin['sha256'], str(path))
        return read(path)
    report_path = directory / 'decode-forward-qwen-service-replay.json'
    report = read(report_path)
    manifest = read(directory / 'decode-forward-qwen-service-cases.json')
    rows = {r['case_id']: r for r in manifest['cases']}
    for result in report['cases']:
        row = rows[result['source_case_id']]
        case = validate(row['model_declaration'])
        base = validate(row['baseline_case_identity'])
        unchanged = json.loads(json.dumps(case))
        unchanged['runtime']['kernels'].pop('service_regimes')
        for key in ('calibration_origin', 'calibration_evidence'):
            unchanged['runtime']['metadata'].pop(key)
        check(unchanged == base, row['case_id'] + ':only_observed_rules_added')
        parameters = result['prediction']['parameters']
        records = {r['id']: r for r in parameters['service_regimes']}
        check(parameters['regime_selection']['unmatched'] == [], row['case_id'] + ':none_unmatched')
        for rule in case['runtime']['kernels']['service_regimes']:
            p = rule['provenance']
            evidence = validate(p['evidence_identity'])
            source = next(c for c in evidence['cases'] if c['case_id'] == row['case_id'])
            expected = next(o for o in source['operators'] if o['native_operator_type'] == p['native_operator_type'])
            check(p['source_identity'] == source['source_identity'], rule['id'] + ':source')
            check(p['source_identity']['sha256'] == row['source']['sha256'], rule['id'] + ':body_source')
            check(p['observed'] == expected['observed'], rule['id'] + ':complete_statistics')
            check(rule['response']['fixed_us'] == p['observed']['mean_us'], rule['id'] + ':mean_parameter')
            check(p['calibration_origin'] == 'in_sample' and p['body_residual_used'] is False,
                  rule['id'] + ':provenance')
            check(not any(k.startswith(('metadata.layer', 'metadata.structure_block', 'op_id', 'model'))
                          for k in rule['match']), rule['id'] + ':physical_axes')
            if p['native_operator_type'] != 'hcom_allReduce_':
                actual = validate(p['actual_identity'])
                hist = Counter()
                for family in actual['families']:
                    if family['native_operator_type'] == p['native_operator_type']:
                        hist.update(dict(family['duration_ns_counter']))
                check(sum(hist.values()) == p['observed']['count'], rule['id'] + ':native_hist_count')
                mean = sum(int(k)*v for k,v in hist.items()) / sum(hist.values()) / 1000
                check(abs(mean-p['observed']['mean_us']) < 1e-9, rule['id'] + ':native_hist_mean')
            n = p['observed']['count'] / p['forward_count']
            check(records[rule['id']]['queries'] == {'observable_response': n}, rule['id'] + ':inclusive_hits')
            check(p['forward_count'] == result['comparison']['observed_forward_count'], rule['id'] + ':body_population')
            hits.append({'case_id': row['case_id'], 'rule_id': rule['id'], 'matched_calls_per_forward': n,
                         'missed_calls_per_forward': 0, 'observed_call_count': p['observed']['count']})
        check(result['prediction_execution']['reused_prediction'] is False, row['case_id'] + ':fresh_worker')
        check(result['prediction_execution']['execution']['peak_rss_bytes'] <= 512*1024**2,
              row['case_id'] + ':bounded_worker')
    output = {'schema_version': 'mindie-observed-service-review/1', 'status': 'failed' if failures else 'passed',
              'report_sha256': sha256(report_path.read_bytes()).hexdigest(), 'checks': checks,
              'failures': failures, 'matched_rules': hits, 'raw_capture_reads': 0, 'new_predictions': 0,
              'maximum_resident_set_size_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (directory / 'qwen-service-independent-review.json').write_text(json.dumps(output, indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k != 'matched_rules'}))
    return bool(failures)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    raise SystemExit(review(parser.parse_args().directory))
