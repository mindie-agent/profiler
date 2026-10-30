"""[Role] Independently audit the saved V4.1 70+28 conditional-reference join.
[Invariants] Retained full histograms and source populations are authoritative;
  reference-only rows never enter strict accuracy denominators. No raw/cost run.
[Timeouts & Locks] Sequential JSON metadata <50 MiB each; no locks/subprocesses.
[Side-Effect Policy] Write one independent review receipt without changing inputs.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time


class Review:
    def __init__(self):
        self.checks = 0
        self.failures = []
        self.pins = {}

    def check(self, okay, label):
        self.checks += 1
        if not okay:
            self.failures.append(label)

    def equal(self, left, right, label):
        self.check(left == right, label)

    def close(self, left, right, label):
        self.check(isinstance(left, (int, float)) and math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-9), label)

    def pin(self, pin):
        path = Path(pin['path'])
        key = str(path.resolve())
        if key not in self.pins:
            size = path.stat().st_size
            h = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    h.update(chunk)
            self.pins[key] = (size, h.hexdigest())
        size, digest = self.pins[key]
        self.equal(size, pin['size_bytes'], key + ':size')
        self.equal(digest, pin['sha256'], key + ':sha256')
        return path


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata exceeds bounded JSON read: ' + str(path))
    return json.loads(path.read_text())


def identity(path):
    path = Path(path)
    return {'path': str(path.resolve()), 'size_bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def histogram(group):
    return Counter({int(ns): int(n) for ns, n in group['duration_ns_counter']})


def quantile(hist, probability):
    count = sum(hist.values())
    # Retained producer contract: median averages central samples; P90 is nearest-rank.
    index = ((9 * count + 9) // 10 - 1) if probability == .9 else (count - 1) * probability
    lo, hi = math.floor(index), math.ceil(index)
    a = b = None
    running = 0
    for ns, n in sorted(hist.items()):
        if a is None and running + n > lo:
            a = ns
        if running + n > hi:
            b = ns
            break
        running += n
    return (a + (b - a) * (index - lo)) / 1000


def check_stats(r, group, tag):
    hist = histogram(group)
    r.equal(len(hist), len(group['duration_ns_counter']), tag + ':unique durations')
    for ns, count in hist.items():
        r.check(ns > 0 and count > 0, tag + ':positive integer duration/count')
    n, total = sum(hist.values()), sum(ns * count for ns, count in hist.items())
    observed = group['observed_us']
    r.equal(observed['count'], n, tag + ':count')
    r.equal(group['observed_activity_sum_ns'], total, tag + ':integer activity')
    for key, value in {'mean': total / n / 1000, 'min': min(hist) / 1000,
                       'max': max(hist) / 1000, 'p50': quantile(hist, .5),
                       'p90': quantile(hist, .9)}.items():
        r.close(observed[key], value, tag + ':' + key)
    return hist


def review(path):
    start = time.perf_counter()
    r = Review()
    data = read(path)
    r.equal(data['schema_version'], 'mindie-native-body-reference-batch/1', 'schema')
    r.equal(data['status'], 'completed', 'join completed')
    r.equal(data['strict_compared'], 0, 'strict denominator')
    r.equal(data['raw_capture_reads'], 0, 'join raw reads')
    r.equal(data['new_predictions_in_join'], 0, 'join cost executions')
    sources = [read(r.pin(pin)) for pin in data['input_reference_receipts']]
    r.equal(len(sources), 2, 'two disjoint source receipts')
    expected_runtime = {}
    for source in sources:
        r.equal(source['status'], 'completed', 'antecedent completed')
        r.equal(source['runtime_source_commit'], data['runtime_source_commit'], 'runtime commit')
        r.equal(source['strict_compared'], 0, 'antecedent strict denominator')
        for name, digest in source['runtime_source_identity'].items():
            if name in expected_runtime:
                r.equal(expected_runtime[name], digest, 'common runtime source bytes:' + name)
            expected_runtime[name] = digest
    r.equal(data['runtime_source_identity'], expected_runtime, 'joined runtime identity union')
    by_arm = [{c['case_id']: c for c in source['cases']} for source in sources]
    r.equal(set(by_arm[0]), set(by_arm[1]), 'same seven sources')
    r.equal(len(data['cases']), 7, 'source count')
    r.equal(len({c['source_identity']['sha256'] for c in data['cases']}), 7, 'unique raw source hashes')
    totals = Counter()
    rows = []
    for case in data['cases']:
        name = case['case_id']; arm = [x[name] for x in by_arm]
        actual = read(r.pin(case['actual_identity']))
        partitions = read(r.pin(case['partition_identity']))
        selected_case = read(r.pin(case['case_identity']))
        r.pin(case['original_case_identity'])
        for source in arm:
            for field in ('source_identity', 'actual_identity', 'case_identity', 'geometry',
                          'conditional_context_tokens', 'forward_count'):
                r.equal(case[field], source[field], name + ':unchanged ' + field)
            r.equal(source['status'], 'completed', name + ':source completed')
            r.equal(source['unresolved'], [], name + ':no hidden unresolved')
            r.equal(source['strict_compared'], 0, name + ':source reference-only')
            r.check(source['runtime_sources_unchanged'] is True, name + ':pinned runtime')
            r.check(source['execution']['maximum_resident_set_size_bytes'] <= 512 * 1024**2, name + ':memory budget')
            r.check(source['execution']['elapsed_seconds'] <= 180, name + ':worker timeout budget')
            r.check(source['execution']['old_prediction_reused'] is False, name + ':fresh prediction')
            for key, value in source['runtime_source_identity'].items():
                r.equal(expected_runtime[key], value, name + ':cost-source generation')
        r.pin(arm[1]['mapping_identity'])
        r.pin(arm[1]['native_reference_identity'])
        mapping = read(arm[1]['mapping_identity']['path'])
        for field in ('source_identity', 'geometry', 'forward_count', 'conditional_context_tokens'):
            r.equal(case[field], actual[field], name + ':actual ' + field)
            r.equal(case[field], partitions[field], name + ':partitions ' + field)
        if actual.get('body_acceptance_identity'):
            r.pin(actual['body_acceptance_identity'])
        execution = case['serialized_structure_execution']
        r.equal(execution['cohort_replicas'], list(range(8)), name + ':full declared DP cohort')
        r.equal(execution['replicas'], [0], name + ':serialization projection')
        r.equal(execution['scope'], 'body', name + ':body scope')
        r.equal(execution['phase'], 'decode', name + ':decode phase')
        r.equal(case['conditional_context_tokens'], 2048, name + ':explicit source context')
        r.equal(case['geometry']['tokens_per_sequence'], 1, name + ':decode query')
        # The join adds only these two pointers; all observed/work/cost fields stay exact.
        for i, original in enumerate(arm[0]['groups'] + arm[1]['groups']):
            final = case['groups'][i]
            r.equal({k: v for k, v in final.items() if k not in ('cost_receipt_identity', 'cost_receipt_case_id')}, original, name + ':original group preserved')
            r.equal(final['cost_receipt_identity'], data['input_reference_receipts'][int(i >= len(arm[0]['groups']))], name + ':exact cost source')
        r.equal(len(case['groups']), 14, name + ':fourteen groups')
        r.equal(len(arm[0]['groups']), 10, name + ':native/source-symbol groups')
        r.equal(len(arm[1]['groups']), 4, name + ':complete normalized groups')
        oldrefs = {g['group_id']: g for g in actual['source_role_references']}
        oldcohorts = {g['cohort_id']: g for w in mapping['windows'] for g in w['cohorts']}
        seen = set(); native_count = normalized_count = 0
        role_layers = defaultdict(set)
        for index, group in enumerate(case['groups']):
            tag = name + ':' + group['declared_role'] + ':' + str(index)
            hist = check_stats(r, group, tag)
            key = (group['native_operator_type'], group['declared_role'], tuple(group['layer_ids']))
            r.check(key not in seen, tag + ':no repeated population')
            seen.add(key)
            role_layers[group['declared_role']].update(group['layer_ids'])
            count = sum(hist.values()); f = case['forward_count']
            r.equal(count, f * len(group['layer_ids']), tag + ':one invocation per declared layer and accepted Forward')
            r.equal(len(set(group['layer_ids'])), len(group['layer_ids']), tag + ':unique layer IDs')
            r.check(set(group['layer_ids']) <= set(range(40)), tag + ':valid forty-layer indices')
            for field in ('strict_accuracy_implied', 'additional_budget_allowed', 'occurrence_binding_implied'):
                r.check(group[field] is False, tag + ':' + field)
            r.equal(group['strict_accuracy_pass'], None, tag + ':no strict pass')
            r.equal(group['accuracy_status'], 'reference_only', tag + ':reference status')
            predicted = group['predicted_reference_us']
            r.check(math.isfinite(predicted) and predicted > 0, tag + ':positive finite prediction')
            for field, value in {
                'calls_per_forward': count / f,
                'observed_activity_ms_per_forward': group['observed_activity_sum_ns'] / 1e6 / f,
                'predicted_service_ms_per_forward': predicted * count / f / 1000,
                'reference_activity_error_ms_per_forward': predicted * count / f / 1000 - group['observed_activity_sum_ns'] / 1e6 / f,
                'per_call_reference_diff_us': predicted - group['observed_us']['mean'],
            }.items(): r.close(group[field], value, tag + ':' + field)
            r.check(bool(group['physical_program_signatures']), tag + ':physical signatures retained')
            r.equal(len(group['physical_program_signatures']), len(group['physical_work_per_program']), tag + ':work/signature arity')
            for work in group['physical_work_per_program']:
                r.check(bool(work), tag + ':physical work retained')
                for value in work.values():
                    if isinstance(value, (int, float)):
                        r.check(math.isfinite(value) and value >= 0, tag + ':finite nonnegative work')
            if index < 10:
                native_count += count
                if 'retained_group_id' in group:
                    old = oldrefs[group['retained_group_id']]
                    r.equal(hist, histogram(old), tag + ':full retained histogram')
                    r.equal(group['layer_ids'], old['layer_ids'], tag + ':retained layer set')
                    r.equal(group.get('native_abi'), old['source_correspondence'].get('observed_native_tensor_contract'), tag + ':full ABI or explicit absence')
                else:
                    combined = Counter(); layers = set(); forwards = Counter()
                    for pindex in group['partition_indices']:
                        part = partitions['partitions'][pindex]
                        combined.update(histogram(part)); layers.update(map(int, part['layer_counts']))
                        forwards.update({k: int(v) for k, v in part['forward_counts'].items()})
                        r.equal(part['native_abi'], group['native_abi'], tag + ':every retained partition ABI')
                    r.equal(hist, combined, tag + ':all native partitions exactly retained')
                    r.equal(set(group['layer_ids']), layers, tag + ':partition layer set')
                    r.equal(len(forwards), f, tag + ':partition accepted Forward population')
                corr = group['source_correspondence']
                if group['declared_role'] in ('expert_up', 'expert_down', 'expert_dispatch_native', 'expert_combine_native'):
                    r.equal(corr.get('observed_valid_routed_rows'), None, tag + ':capacity is not observed valid rows')
                if group['native_operator_type'] == 'HcPre':
                    r.equal(corr['unmodeled_native_tensor_slots'], {'inputs': [4], 'outputs': [3]}, tag + ':extra premix remains partial')
                    r.check(corr['native_extra_branch_equivalence_established'] is False, tag + ':no unsupported HCPre equivalence')
            else:
                normalized_count += count
                old = oldcohorts[group['retained_cohort_id']]
                family = [x for x in actual['families'] if x['declared_role'] == group['declared_role']]
                r.equal(len(family), 1, tag + ':single complete retained family')
                r.equal(hist, histogram(family[0]), tag + ':complete family histogram')
                r.equal(group['observed_contract'], old['contract'], tag + ':retained active contract')
                r.equal(count, old['complete_event_count'], tag + ':complete cohort count')
                r.equal(old['event_count'], count, tag + ':whole cohort population')
                r.equal(old['clipped_event_count'], 0, tag + ':no clipping')
                r.equal(group['observed_activity_sum_ns'], old['complete_activity_sum_ns'], tag + ':whole cohort activity')
                ids = defaultdict(set)
                for node in old['target_ids']:
                    rank, local = node.split('/', 1); ids[int(rank.removeprefix('rank:'))].add(local)
                r.equal(set(ids), set(range(8)), tag + ':retained eight DP candidates')
                for rank in ids: r.equal(ids[rank], ids[0], tag + ':same DP topology candidates')
                r.equal(len(ids[0]), 40, tag + ':forty retained layer candidates')
                corr = group['source_correspondence']
                r.equal(group['native_abi'], None, tag + ':normalized is not full native ABI')
                r.check(corr['complete_native_abi_available'] is False, tag + ':explicit evidence strength')
                r.equal(corr['fresh_layer_contracts_validated'], 40, tag + ':fresh validation scope')
        for role, layers in role_layers.items(): r.equal(layers, set(range(40)), name + ':complete layer union:' + role)
        r.equal(native_count, 320 * case['forward_count'], name + ':native calls/F')
        r.equal(normalized_count, 160 * case['forward_count'], name + ':normalized calls/F')
        r.equal(case['referenced_event_count'], native_count + normalized_count, name + ':joined referenced calls')
        r.equal(case['native_event_count'], native_count + normalized_count, name + ':joined population')
        totals.update(sources=1, forwards=case['forward_count'], groups=len(case['groups']), native_calls=native_count, normalized_calls=normalized_count)
        rows.append({'case_id': name, 'forward_count': case['forward_count'], 'native_calls': native_count, 'normalized_calls': normalized_count, 'reference_groups': len(case['groups']), 'strict_compared': 0})
        del actual, partitions, selected_case, mapping
    r.equal(dict(totals), {'sources': 7, 'forwards': 830, 'groups': 98, 'native_calls': 265600, 'normalized_calls': 132800}, 'complete unique population')
    failed_path = Path(path).parent / 'strict-focused-c32/body-operator-family-scoreboard.json'
    failed = read(failed_path)
    r.equal(failed['status'], 'partial', 'earlier strict attempt remains partial')
    for attempt in failed['cases']:
        r.equal(attempt['passed_cohorts'], 0, 'failed strict attempt contributes no passes')
        r.equal(attempt['comparison_status_counts'], {'prediction_failed': 2}, 'two real failed programs preserved')
        comparison = read(r.pin(attempt['comparison_identity']))
        for program in comparison['program_receipts']:
            r.equal(program['status'], 'failed', 'failed worker status preserved')
            r.check('comparison_worker_exceeds_512_mib' in program['stderr'], 'actual memory budget failure retained')
    r.check(all('strict-focused-c32' not in p['path'] for p in data['input_reference_receipts']), 'failed strict attempt excluded from references')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != 'darwin': rss *= 1024
    return {'schema_version': 'mindie-v41-independent-reference-review/1', 'status': 'passed' if not r.failures else 'failed',
            'report_identity': identity(path), 'reviewer_identity': identity(__file__), 'checks': r.checks, 'failures': r.failures,
            'population': dict(totals), 'strict_compared': 0, 'raw_capture_reads': 0, 'new_predictions': 0,
            'quantile_definition': {'p50': 'mean_of_two_central_order_statistics', 'p90': 'nearest_rank_ceil_0.9N'},
            'metadata_files_hashed': len(r.pins), 'cases': rows, 'elapsed_seconds': time.perf_counter() - start,
            'maximum_resident_set_size_bytes': rss,
            'scope': ['Full saved histogram moments/quantiles and original 70+28 groups unchanged.',
                      'Retained actual/partition/mapping/case/body receipts and identical runtime generation.',
                      'All forty-layer and declared eight-DP candidate populations; physical work/signatures retained.',
                      'Per-Forward reference arithmetic and successful execution budgets; earlier failed attempt preserved.'],
            'limits': ['No raw CSV scan, Sim export, new prediction or independent rate/service-trace reconstruction.',
                       'Fresh forty-layer physical-work validation is inspected in the producer and saved evidence; no fresh graph is re-exported.',
                       'declared_programs may name a memoized physically equivalent representative, not the group semantic occurrence.',
                       'HCPre extra [B,4] branch remains partial; native route values/peer readiness and captured binary are unobserved.',
                       'Normalized references do not create a full native ABI or strict accuracy pass; source-symbol MQSMLA remains conditional.',
                       'Activity/service residuals are nonadditive with respect to Body wall-clock error.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path); p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); result = review(a.report)
    a.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'checks', 'failures', 'population', 'maximum_resident_set_size_bytes')}))
    raise SystemExit(bool(result['failures']))


if __name__ == '__main__': main()
