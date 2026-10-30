"""Reconcile native partitions and executed Q35/Q397 service responses.

[Role] Independently audit complete native populations and saved response queries.
[Invariants] Integer histograms and topology multiplicity, not timing similarity,
  establish the parameter population. AICPU wrappers never enter HCOM service.
[Timeouts & Locks] Bounded retained JSON only; no runtime imports or locks.
[Side-Effect Policy] Write one local review; no raw scan or prediction.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from math import isclose
from pathlib import Path


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('oversized_metadata')
    return json.loads(path.read_text())


def review(directory):
    report_path = directory / 'decode-forward-replay.compact.json'
    if not report_path.exists():
        report_path = directory / 'decode-forward-replay.json'
    report = read(report_path)
    evidence = read(directory / 'observed-populations.json')
    rows = {x['source_case_id']: x for x in report['cases'] if x['comparison']['status'] == 'compared'}
    checks, failures, records = 0, [], []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def pinned(pin):
        path = Path(pin['path']); data = read(path)
        check(sha256(path.read_bytes()).hexdigest() == pin['sha256'], 'identity:' + str(path))
        return data

    for item in evidence['cases']:
        name = item['case_id']; row = rows[name]; F = item['forward_count']
        native = pinned(item['native_partition_identity']); case = pinned(item['case_identity'])
        old = pinned(item['baseline_case_identity']); recorded = {r['id']: r for r in row['prediction']['parameters']['service_regimes']}
        check(native['retained_endpoints_exactly_equal'], name + ':accepted_endpoints')
        check(native['source_identity']['sha256'] == item['source_identity']['sha256'] == row['source_identity']['sha256'], name + ':same_source')
        check(native['forward_count'] == F == row['comparison']['observed_ms']['count'], name + ':same_forwards')
        check(row['model_structure_identity']['sha256'] == item['case_identity']['sha256'], name + ':executed_case')
        check(sum(sum(c for _, c in p['duration_ns_counter']) for p in native['partitions']) == native['native_event_count'], name + ':full_native_population')
        for family in native['families']:
            pooled = Counter()
            for part in native['partitions']:
                if part['native_operator_type'] == family['native_operator_type']:
                    pooled.update(dict(part['duration_ns_counter']))
            check(sorted(pooled.items()) == [tuple(x) for x in family['duration_ns_counter']], name + ':full_family_hist')
        newrules = item.get('new_rules', item.get('rules', []))
        for rule in newrules:
            prov = rule['provenance']; label = name + ':' + rule['id']
            parts = [p for p in native['partitions'] if p['native_operator_type'] == prov['native_operator_type']]
            if 'native_type_ordinal_in_region' in prov:
                parts = [p for p in parts if p['topology_region'] == prov['topology_region'] and
                         p['native_type_ordinal_in_region'] == prov['native_type_ordinal_in_region']]
            hist = Counter(); layer_counts = Counter()
            for part in parts:
                hist.update(dict(part['duration_ns_counter'])); layer_counts.update(part['layer_counts'])
                check(part['native_abi'] == prov['native_abi'], label + ':full_ABI')
                check(sum(part['forward_counts'].values()) == sum(part['layer_counts'].values()) == sum(c for _, c in part['duration_ns_counter']), label + ':partition_counts')
            pop = prov['observed_population']; count = sum(hist.values()); total = sum(ns * c for ns, c in hist.items())
            check(sorted(hist.items()) == [tuple(x) for x in pop['duration_ns_counter']], label + ':full_original_hist')
            check(count == pop['count'] == prov['expected_rule_hits'] * F, label + ':multiplicity')
            check(total == pop['activity_sum_ns'], label + ':integer_duration')
            check(isclose(total / count / 1000, rule['response']['fixed_us'], rel_tol=1e-14), label + ':mean_us')
            check(not prov['body_residual_used'], label + ':no_body_fit')
            actual = recorded[rule['id']]; query = 'joint_native_service' if 'execution' in rule else 'observable_response'
            check(actual['queries'] == {query: prov['expected_rule_hits']}, label + ':one_native_response')
            check(actual['match'] == rule['match'] and actual['response'] == rule['response'], label + ':executed_parameters')
            check(actual['response_us_min'] == actual['response_us_max'] == rule['response']['fixed_us'], label + ':executed_value')
            if 'execution' in rule:
                check(actual['execution'] == rule['execution'], label + ':joint_execution')
                resource = rule['execution']['resource']; device = case['machine']['device']
                check(device['rates'][resource] == 1e9 and device['work_units'][resource] == 'busy_ns' and device['resource_units'][resource] == 1, label + ':joint_units')
            else:
                check('allreduceAicpuKernel' != prov['native_operator_type'], label + ':no_controller_service')
        if 'removed_shared_quantizers' in item:
            old_rules = old['runtime']['kernels']['service_regimes']; rules = case['runtime']['kernels']['service_regimes']
            check(rules[:len(old_rules)] == old_rules, name + ':prior_rules_unchanged')
            check(len(item['removed_shared_quantizers']) == 80, name + ':only_shared_conversions_removed')
            changed = case['model']['quant']['category_overrides']['shared_expert']
            check(changed == {'weight_format': 'bf16', 'activation_format': 'bf16'}, name + ':observed_shared_dtype')
            check([r['provenance']['native_type_ordinal_in_region'] for r in newrules] == [1, 2, 3], name + ':router_up_down_disjoint')
        else:
            ledger = read(directory.parent.parent / 'acceptance-20261030-hccl-66' / (name + '-capture-hccl.json'))
            bucket = next(g for g in ledger['body_geometry_groups'] if all(g['geometry'][k] == item['geometry'][k] for k in ['query_rows','tokens_per_sequence','sequences_per_replica']))
            hh = Counter()
            for g in bucket['groups']:
                if g['native_operator_type'] == 'hcom_allReduce_' and g['event_category'] in ['collective_envelope_only','collective_device_task']:
                    hh.update(dict(g['duration_ns_counter']))
            ar = next(r for r in newrules if r['provenance']['native_operator_type'] == 'hcom_allReduce_')
            check(sorted(hh.items()) == [tuple(x) for x in ar['provenance']['observed_population']['duration_ns_counter']], name + ':typed_HCOM_ledger_not_wrapper')
        comp = row['comparison']; records.append({'case_id': name, 'forward_count': F,
            'real_ms': comp['observed_ms']['mean'], 'predicted_ms': comp['predicted_ms'],
            'relative_error': comp['relative_error'], 'passed_15pct': comp['passed'],
            'passed_8pct': abs(comp['relative_error']) <= .08, 'new_rule_count': len(newrules)})
    result = {'schema_version': 'mindie-native-service-parameter-review/1', 'status': 'failed' if failures else 'passed',
        'checks': checks, 'failures': failures, 'cases': records,
        'report_identity': {'path': str(report_path.resolve()), 'sha256': sha256(report_path.read_bytes()).hexdigest()},
        'new_raw_scans': 0, 'new_cost_predictions': 0,
        'scope': 'Complete retained full ABI/histogram/population, executed query units/counts/value, controller exclusion and source precision changes; no claim to inspect unretained Engine trace.'}
    (directory / 'parameter-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--directory', type=Path, required=True)
    review(parser.parse_args().directory)
