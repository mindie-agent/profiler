"""Review retained joint-native execution against independent full populations.

[Role] Verify two complete local five-domain service replays without new costs.
[Invariants] Observed means identify whole calls, not hardware pipeline prices;
  analytical reference work is not executed alongside the selected joint queue.
[Timeouts & Locks] Bounded retained JSON only; no subprocesses or locks.
[Side-Effect Policy] Write one independent review; no source or runtime edits.
"""
from collections import Counter
from copy import deepcopy
from math import isclose
from pathlib import Path
import json

from collect_scalar_dma_pmu import identity, read


ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'examples/structure/acceptance-20261030-livepre-native/joint-service'
EXPECTED = {'HcPre': 90, 'HcPost': 90, 'GroupedMatmul': 42,
            'GroupedMatmulSwigluQuant': 42, 'KvQuantSparseFlashAttentionVllm': 11}
QUEUE = 'observed_a3_local_native'


def member(value, pointer):
    for key in pointer.split('/'):
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def scheduler_native(group):
    if group.get('fusion_role'):
        return {'hc_pre': 'HcPre', 'hc_post': 'HcPost',
                'grouped_gate_up_activation_quant': 'GroupedMatmulSwigluQuant'}[group['fusion_role']]
    return {'grouped_down': 'GroupedMatmul',
            'latent_attention_batch': 'KvQuantSparseFlashAttentionVllm'}[group['recipe']]


def review():
    report = read(DIR / 'decode-forward-replay.json')
    populations = read(DIR / 'observed-populations.json')
    inputs = read(populations['input_identity']['path'])
    manifest = read(DIR / 'decode-forward-cases.json')
    checks, failures, summaries = 0, [], []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    def pin(value, label):
        actual = identity(value['path'])
        check(all(actual[key] == expected for key, expected in value.items()), label)

    check(report['status'] == 'completed', 'completed replay')
    check(report['runtime_generation']['start'] == report['runtime_generation']['end'], 'runtime unchanged')
    check(report['runtime_provenance']['source_commit'] == 'f6e68d5e326ccbc6aade4f62fffbd816b23da500', 'runtime source')
    pin(populations['input_identity'], 'neutral input identity')
    pin(report['manifest_identity'], 'replay manifest')
    selected = [r for r in report['cases'] if r.get('prediction')]
    check(len(selected) == 2, 'two cost results')
    candidate_map = {r['candidate_id']: r for r in inputs['candidates']}
    source_counts, old_rule_ids = {}, {}
    for row in selected:
        name = row['source_case_id']
        declaration = next(r for r in populations['cases'] if r['case_id'] == name)
        manifest_row = next(r for r in manifest['cases'] if r['case_id'] == name)
        for field in ('case_identity', 'original_case_identity'):
            pin(declaration[field], name + '/' + field)
        current = read(declaration['case_identity']['path'])
        original = read(declaration['original_case_identity']['path'])
        old = original['runtime']['kernels'].get('service_regimes', [])
        removed = declaration['replaced_same_native_completion_floors']
        additions = declaration['rules']
        retained = [r for r in old if r not in removed]
        check(all(r in old for r in removed), name + '/removed rules originate in old case')
        check(current['runtime']['kernels']['service_regimes'] == retained + additions, name + '/only explicit same-native replacement')
        normalized = deepcopy(current)
        normalized['runtime']['kernels']['service_regimes'] = old
        if 'service_regimes' not in original['runtime']['kernels']:
            normalized['runtime']['kernels'].pop('service_regimes')
        normalized['runtime']['metadata'] = deepcopy(original['runtime']['metadata'])
        for field in ('rates', 'work_units', 'resource_units'):
            normalized['machine']['device'][field].pop(QUEUE)
            if field not in original['machine'].get('device', {}):
                normalized['machine']['device'].pop(field)
        if 'device' not in original['machine']:
            check(not normalized['machine']['device'], name + '/only introduced device queue fields')
            normalized['machine'].pop('device')
        check(normalized == original, name + '/all other case values inherited')
        old_rule_ids[name] = [r['id'] for r in removed]
        check(len(removed) == (1 if '-c4-' in name else 0), name + '/old down floor multiplicity')
        device = current['machine']['device']
        check(device['rates'][QUEUE] == 1e9, name + '/busy ns rate')
        check(device['work_units'][QUEUE] == 'busy_ns' and device['resource_units'][QUEUE] == 1, name + '/one declared queue')
        params = row['prediction']['parameters']
        check(params['work_basis'] == 'logical_and_analytical_reference; joint_native_queues_replace_selected_service', name + '/analytical work label')
        check(params['operator_occurrences']['joint_native_service'] == sum(EXPECTED.values()) == 275, name + '/joint occurrences')
        check(not params['regime_selection']['unmatched'], name + '/all declared regimes matched')
        check(not set(old_rule_ids[name]) & {r['id'] for r in params['service_regimes']}, name + '/old floor not executed')
        services = {r['native_kernel']: r for r in params['joint_native_services']}
        check(set(services) == set(EXPECTED), name + '/five native services')
        schedule = {scheduler_native(r): r for r in row['prediction']['scheduled_operator_summary']['groups']
                    if r['program'] == 'JointNativeService'}
        check(set(schedule) == set(EXPECTED), name + '/five saved joint scheduling groups')
        native_rows = []
        for rule in additions:
            native = rule['execution']['native_kernel']
            count = EXPECTED[native]
            provenance = rule['provenance']
            candidate = candidate_map[provenance['candidate_id']]
            population, = candidate['source_populations']
            source_counts[population['source_identity']['sha256']] = population['forward_count']
            pin(population['timing_identity'], name + '/' + native + '/retained timing pin')
            actual = read(population['timing_identity']['path'])
            hist = Counter()
            for pointer in population['timing_members']:
                hist.update(dict(member(actual, pointer)))
            check(hist == Counter(dict(candidate['duration_ns_counter'])), name + '/' + native + '/complete original histogram')
            n = sum(hist.values())
            mean = sum(ns * copies for ns, copies in hist.items()) / n / 1000
            check(n == count * population['forward_count'], name + '/' + native + '/all native occurrences')
            check(isclose(mean, rule['response']['fixed_us'], abs_tol=1e-10), name + '/' + native + '/observed mean response')
            check(provenance['source_identity'] == row['source_identity'], name + '/' + native + '/same capture')
            check(population['forward_count'] == row['comparison']['observed_forward_count'], name + '/' + native + '/same selected body population')
            check(provenance['body_residual_used'] is False and provenance['evaluation_relation'] == 'in_sample', name + '/' + native + '/calibration boundary')
            runtime_rule, = [r for r in params['service_regimes'] if r['id'] == rule['id']]
            check(runtime_rule['queries'] == {'joint_native_service': count}, name + '/' + native + '/exact joint hits')
            check(all(runtime_rule[key] == rule[key] for key in rule), name + '/' + native + '/same executed rule')
            check(runtime_rule['response_us_min'] == runtime_rule['response_us_max'] == mean, name + '/' + native + '/one inclusive response')
            service = services[native]
            check(service['invocations'] == count and service['resource'] == QUEUE, name + '/' + native + '/one queue invocation per native')
            check(service['execution_basis'] == 'declared_joint_native_service_queue', name + '/' + native + '/execution basis')
            check(service['analytical_reference_work'] and QUEUE not in service['analytical_reference_work'], name + '/' + native + '/reference separate from busy ns')
            group = schedule[native]
            check(group['scheduled_elapsed_ms']['count'] == count, name + '/' + native + '/saved scheduled occurrence population')
            for field in ('mean', 'min', 'max'):
                check(isclose(group['scheduled_elapsed_ms'][field], mean / 1000, rel_tol=1e-9, abs_tol=1e-10), name + '/' + native + '/scheduled ' + field)
            check(isclose(group['sum_elapsed_ms'], count * mean / 1000, rel_tol=1e-9, abs_tol=1e-10), name + '/' + native + '/scheduled sum')
            native_rows.append({'native_operator_type': native, 'calls_per_forward': count,
                                'complete_population_count': n, 'observed_mean_us': mean,
                                'recorded_scheduled_elapsed_ms': group['scheduled_elapsed_ms'],
                                'declared_joint_busy_ns_per_forward': count * mean * 1000,
                                'busy_ns_basis': 'derived_from_executed_response_and_exact_hits; raw_engine_counter_not_retained',
                                'analytical_reference_work': service['analytical_reference_work']})
        execution = row['prediction_execution']
        check(execution['status'] == 'completed' and not execution['reused_prediction'], name + '/fresh completed cost')
        check(execution['case_identity']['sha256'] == declaration['case_identity']['sha256'], name + '/worker case pin')
        check(execution['runtime_identity']['package_sha256'] == report['runtime_generation']['start']['package_sha256'], name + '/worker same runtime')
        check(execution['execution']['peak_rss_bytes'] <= 512 * 1024 ** 2, name + '/memory limit')
        check(manifest_row['source']['sha256'] == row['source_identity']['sha256'], name + '/manifest source')
        comp = row['comparison']
        check(isclose(comp['relative_error'], comp['predicted_ms'] / comp['observed_ms']['mean'] - 1, abs_tol=1e-12), name + '/body error arithmetic')
        summaries.append({'case_id': name, 'forward_count': comp['observed_forward_count'],
                          'native_domains': native_rows, 'replaced_floor_ids': old_rule_ids[name],
                          'body_comparison': comp})
    check(sum(source_counts.values()) == 83, 'primary forward denominator')
    check(sum(r['observed']['body_forward_span_ms']['count'] for r in report['cases']) == 181, 'all accepted forwards')
    check(len(report['cases']) == 17 and sum(r.get('prediction') is None for r in report['cases']) == 15, 'all geometries and deferred outcomes')
    return {'schema_version': 'mindie-joint-native-service-independent-review/1',
            'status': 'failed' if failures else 'passed', 'checks': checks, 'failures': failures,
            'report_identity': identity(DIR / 'decode-forward-replay.json'),
            'input_identity': populations['input_identity'], 'reviewer_identity': identity(__file__),
            'cases': summaries, 'new_raw_scans': 0, 'new_cost_predictions': 0,
            'review_corrections': ['Reviewer now preserves genuinely absent original device/service_regimes fields when checking inheritance, and accepts the manifest identity schema without optional size_bytes. No production inputs or results changed.'],
            'scope': 'Whole native response, exact hits, inherited inputs, saved scheduling intervals and separated analytical reference work.',
            'limitations': ['Engine serviced busy_ns counters are not present in the compact replay; derived queue work is labeled and is not an independently retained counter.',
                            'Livepre ABI remains complete-duration/source-role conditional; Body PASS is in-sample and does not promote strict native contracts or isolated resource prices.']}


if __name__ == '__main__':
    result = review()
    (DIR / 'service-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'checks', 'failures')}))
    raise SystemExit(bool(result['failures']))
