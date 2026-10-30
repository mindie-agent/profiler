"""Price complete Kimi ABI buckets against explicit source-declared programs.

[Role] Reuse accepted Body topology and native histograms for conditional costs.
[Invariants] Exact native counts weight heterogeneous source programs; no measured
  layer histogram is invented, references do not enter strict or Body budgets.
[Timeouts & Locks] Sequential source workers, 180 s each; <=512 MiB; no locks.
[Side-Effect Policy] Read retained evidence/cases and write a separate local arm.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gc
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from body_source_role_references import predict_source_role_references
from compare_body_operator_families import prediction_runtime_identity
from kimi_native_references import prepare_references, prepare_mc2_references
from replay_body_operator_families import identity, read, write


def runtime_identity():
    value = prediction_runtime_identity()
    for name in ('kimi_native_references.py', 'compare_kimi_native_partitions.py',
                 'glm_native_references.py', 'reprice_body_operator_families.py'):
        path = Path(__file__).with_name(name).resolve()
        value[str(path)] = identity(path)['sha256']
    return value


def peak_rss():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == 'darwin' else value * 1024


def verify_pin(pin):
    actual = identity(pin['path'])
    if any(actual[k] != pin[k] for k in ('sha256', 'size_bytes')):
        raise ValueError('retained_input_changed:' + pin['path'])


def worker(partition_path, case_path, runtime_commit):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure

    started = time.perf_counter(); before = runtime_identity()
    part_pin, case_pin = identity(partition_path), identity(case_path)
    part = read(partition_path); verify_pin(part['actual_identity'])
    actual = read(part['actual_identity']['path'])
    verify_pin(actual['body_acceptance_identity'])
    for key in ('source_identity', 'geometry', 'forward_count', 'body_acceptance_identity'):
        if actual[key] != part[key]:
            raise ValueError('partition_actual_identity_differs:' + key)
    for kind in {p['native_operator_type'] for p in part['partitions']}:
        histogram = Counter()
        for p in part['partitions']:
            if p['native_operator_type'] == kind:
                histogram.update(dict(p['duration_ns_counter']))
        old_histogram = Counter()
        for family in actual['families']:
            if family['native_operator_type'] == kind:
                old_histogram.update(dict(family['duration_ns_counter']))
        if histogram != old_histogram:
            raise ValueError('native_partition_not_complete:' + kind)
    case = parse_case(read(case_path)); geo = part['geometry']
    manifest = export_structure(case, phase='decode', tokens=geo['tokens_per_sequence'],
        sequences=geo['sequences_per_replica'], context=actual['conditional_context_tokens'], scope='body')
    refs, unresolved, programs = prepare_references(part, manifest)
    mc2, mc2_unresolved, mc2_programs = prepare_mc2_references(actual, manifest)
    refs.extend(mc2); unresolved.extend(mc2_unresolved); programs.update(mc2_programs)
    selected = {n['node_id']: n for p in programs.values() for n in p['nodes']}
    compact = {k: manifest[k] for k in ('schema_version', 'graph_id', 'execution')}
    compact['nodes'] = list(selected.values())
    # Pricing uses the original whole bucket only as observed context. Its
    # duration is never attributed to a sub-bucket or used to select a program.
    representative_context = {}
    for group in refs:
        for bucket in group['program_buckets']:
            representative_context.setdefault(bucket['program_set_key'], group)
    pricing = []
    for key, program in programs.items():
        group = representative_context[key]
        pricing.append({k: v for k, v in program.items() if k != 'nodes'} | {
            'observed_us': group['observed_us'],
            'observed_activity_sum_ns': group['observed_activity_sum_ns'],
            'observed_context_is_full_native_partition': True})
    source_pin = part['source_identity']; body_pin = part['body_acceptance_identity']
    mc2_event_count = sum(r['observed_us']['count'] for r in actual.get('source_role_references', [])
        if r['native_operator_type'] in {'MoeDistributeDispatchV3', 'MoeDistributeCombineV3'})
    del manifest, actual, selected
    gc.collect()
    priced = predict_source_role_references(case, compact, {
        'source_role_references': pricing, 'forward_count': part['forward_count']})
    costs = {row['program_set_key']: row for row in priced}
    results = []
    for group in refs:
        count = group['observed_us']['count']; forwards = part['forward_count']
        buckets = []
        for bucket in group['program_buckets']:
            key = bucket['program_set_key']; cost = costs[key]; program = programs[key]
            if cost['prediction_status'] != 'reference_only':
                raise ValueError('source_program_prediction_unavailable:' + key)
            buckets.append({**bucket, 'predicted_reference_us': cost['predicted_reference_us'],
                'declared_programs': cost['declared_programs'], 'reference_boundary': cost['boundary'],
                **{k: v for k, v in program.items() if k not in ('nodes', 'program_set_key')}})
        if sum(b['event_count'] for b in buckets) != count:
            raise ValueError('program_multiplicity_does_not_cover_native_histogram')
        mean = sum(b['event_count'] * b['predicted_reference_us'] for b in buckets) / count
        observed = group['observed_activity_sum_ns'] / 1e6 / forwards
        predicted = mean * count / 1000 / forwards
        limitations = sorted({text for b in buckets for text in b['source_correspondence']['limitations']})
        relation = (buckets[0]['source_correspondence']['boundary_relation'] if len(buckets) == 1
            else 'captured_layer_multiplicity_weighted_source_program_reference')
        correspondence = {'boundary_relation': relation,
            'observed_native_tensor_contract': group['native_abi'],
            'program_weight_basis': 'exact_captured_layer_counts',
            'measured_per_program_histograms_available': False,
            'limitations': limitations}
        results.append({**group, 'program_buckets': buckets,
            'source_correspondence': correspondence,
            'reference_boundary': relation,
            'physical_program_signatures': [b['physical_program_signatures'] for b in buckets],
            'physical_signature_population': 'ordered_program_buckets_with_captured_call_weights',
            'prediction_status': 'reference_only', 'predicted_reference_us': mean,
            'predicted_reference_mean_basis': 'captured_layer_count_weighted_source_program_service',
            'calls_per_forward': count / forwards,
            'observed_activity_ms_per_forward': observed,
            'predicted_service_ms_per_forward': predicted,
            'reference_activity_error_ms_per_forward': predicted - observed,
            'per_call_reference_diff_us': mean - group['observed_us']['mean'],
            'accuracy_status': 'reference_only', 'strict_accuracy_pass': None,
            'conditions': ['Existing case-declared work is not an additional Body budget.',
                'Native elapsed activity and source service are not additive Body wall contributions.',
                'Exact captured native histograms remain whole; per-layer latency is not imputed.', *limitations]})
    for pin in (part_pin, case_pin, part['actual_identity'], body_pin): verify_pin(pin)
    if runtime_identity() != before: raise ValueError('reference_runtime_changed')
    rss = peak_rss()
    if rss > 512 * 1024**2: raise MemoryError('kimi_native_reference_exceeds_512_mib')
    return {'schema_version': 'mindie-native-body-reference/1',
        'status': 'partial' if unresolved else 'completed', 'case_id': part['source_case_id'],
        'partition_identity': part_pin, 'actual_identity': part['actual_identity'],
        'case_identity': case_pin, 'original_case_identity': part['case_identity'],
        'source_identity': source_pin, 'body_acceptance_identity': body_pin,
        'geometry': geo, 'forward_count': part['forward_count'],
        'conditional_context_tokens': compact['execution']['context'],
        'native_event_count': part['native_event_count'] + mc2_event_count,
        'referenced_event_count': sum(g['observed_us']['count'] for g in results),
        'declaration_variant': 'explicit_source_mechanism_logical96_physical16',
        'original_case_identity_is_historical': True, 'fresh_graph_id': compact['graph_id'],
        'groups': results, 'unresolved': unresolved, 'strict_compared': 0,
        'runtime_source_commit': runtime_commit, 'runtime_source_identity': before,
        'runtime_sources_unchanged': True, 'execution': {'new_program_sets': len(programs),
            'raw_capture_reads': 0, 'old_prediction_reused': False,
            'elapsed_seconds': time.perf_counter() - started, 'maximum_resident_set_size_bytes': rss}}


def render(report):
    lines = ['# Kimi complete native Body references', '',
        f"Runtime `{report['runtime_source_commit']}`; all rows are conditional references, outside strict accuracy.",
        'Exact native histograms are retained. Heterogeneous AttnRes source flags use captured layer call counts; no per-layer measured P50 is invented.', '',
        '| Case / native | Calls/F | Real Mean / P50 us | Sim mean reference us | Real activity / Sim service / residual ms/F |',
        '| --- | ---: | ---: | ---: | ---: |']
    for case in report['cases']:
        if case['status'] == 'failed':
            lines.append(f"| {case['case_id']} | — | — | — | failed: {case['reason']} |")
            continue
        totals = {}
        for group in case['groups']:
            item = totals.setdefault(group['native_operator_type'], [0, 0., 0.])
            item[0] += group['observed_us']['count']
            item[1] += group['observed_activity_ms_per_forward']
            item[2] += group['predicted_service_ms_per_forward']
        for kind, (count, observed, predicted) in totals.items():
            # Family P50 is not the mean of partition P50s; merge integer bins.
            from review_repriced_body_operators import statistics
            histogram = Counter()
            for g in case['groups']:
                if g['native_operator_type'] == kind: histogram.update(dict(g['duration_ns_counter']))
            stats = statistics(sorted(histogram.items())); calls = count / case['forward_count']
            lines.append(f"| {case['case_id']} / {kind} | {calls:.3f} | {stats['mean']:.6f} / {stats['p50']:.6f} | "
                f"{predicted * 1000 / calls:.6f} | {observed:.6f} / {predicted:.6f} / {predicted-observed:+.6f} |")
        for row in case['unresolved']:
            lines.append(f"| {case['case_id']} / {row['native_operator_type']} | — | — | — | {row['reason']} |")
    lines += ['', 'Source service residuals cannot be added to explain Body wall time. Full ABI, source/case/runtime identity, exact histograms and program multiplicities are retained in JSON.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--partition-dir', type=Path)
    parser.add_argument('--partition', type=Path)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--runtime-source-commit', required=True)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.worker:
        result = worker(args.partition, args.case, args.runtime_source_commit)
        write(args.output_dir / (result['case_id'] + '-references.json'), result)
        return
    manifest_pin = identity(args.manifest); entries = read(args.manifest)['cases']
    before = runtime_identity(); started = time.perf_counter(); cases = []
    for entry in entries:
        case_id = entry['case_id']; part = args.partition_dir / (case_id + '-native-partitions.json')
        command = [sys.executable, str(Path(__file__).resolve()), '--worker', '--partition', str(part.resolve()),
            '--case', entry['sim_case_path'], '--output-dir', str(args.output_dir.resolve()),
            '--runtime-source-commit', args.runtime_source_commit]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            if result.returncode: raise RuntimeError(result.stderr[-4000:])
            case = read(args.output_dir / (case_id + '-references.json'))
        except (subprocess.TimeoutExpired, RuntimeError) as error:
            case = {'case_id': case_id, 'partition_path': str(part), 'status': 'failed', 'reason': str(error)}
        cases.append(case); print(json.dumps({'case': case_id, 'status': case['status']}), flush=True)
    if before != runtime_identity(): raise ValueError('batch_runtime_changed')
    verify_pin(manifest_pin)
    report = {'schema_version': 'mindie-native-body-reference-batch/1',
        'status': 'completed' if all(c['status'] == 'completed' for c in cases) else 'partial',
        'runtime_source_commit': args.runtime_source_commit, 'runtime_source_identity': before,
        'source_manifest_identity': manifest_pin, 'cases': cases,
        'elapsed_seconds': time.perf_counter() - started, 'raw_capture_reads': 0, 'strict_compared': 0}
    write(args.output_dir / 'kimi-native-reference-scoreboard.json', report)
    (args.output_dir / 'kimi-native-reference-scoreboard.md').write_text(render(report))
    if any(c['status'] == 'failed' for c in cases): raise SystemExit(1)


if __name__ == '__main__': main()
