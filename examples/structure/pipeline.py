"""[Role] One source-pinned entry point for current model and engine validation.
[Invariants] Every score uses one immutable Sim package and a pinned case;
  no historical cost selection, timing-fitted window selection or silent failures.
[Timeouts & Locks] Bounded source and prediction workers, streaming capture
  readers. Individual full results are archived before the next case is retained.
[Side-Effect Policy] Read local metadata/captures and write current results only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import time

from decode import _sim_identity, replay_manifest


def archive_report(report, root):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.scoreboard-', suffix='.json', dir=root)
    temporary = Path(name)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(report, stream, separators=(',', ':'), allow_nan=False)
            stream.write('\n')
        sha = identity(temporary)['sha256']
        target = root / (sha + '.json')
        if target.exists():
            if identity(target)['sha256'] != sha:
                raise ValueError('archive content does not match its SHA256 name')
            temporary.unlink()
        else:
            os.replace(temporary, target)
        return {'path': str(target.resolve()), 'sha256': sha,
                'size_bytes': target.stat().st_size, 'format': 'full_scoreboard_json'}
    finally:
        temporary.unlink(missing_ok=True)
def operator_case(row, base, directory, timeout):
    from types import SimpleNamespace
    from operators import extract_case
    from cohorts import _compare_programs
    from operators import family_rows, program_references
    extraction = Path(row['extraction_path'])
    if not extraction.is_absolute(): extraction = base / extraction
    case = Path(row['sim_case_path'])
    if not case.is_absolute(): case = base / case
    directory = directory / row['id'].replace(':', '-')
    directory.mkdir(parents=True, exist_ok=True)
    entry = {'case_id': row['case_id'], 'source_identity': row['source'],
             'report_path': str(extraction), 'report_sha256': identity(extraction)['sha256']}
    populations = extract_case(entry, [case], directory, geometry_limit=1,
                               context_tokens=row.get('geometry', {}).get('context_tokens'))
    result = []
    for population in populations:
        actual_path = Path(population['extraction_identity']['path'])
        prefix = actual_path.with_name(actual_path.name.removesuffix('.actual.json'))
        actual = read(actual_path); mapping = read(prefix.with_suffix('.mapping.json'))
        comparison = _compare_programs(SimpleNamespace(compare_timeout=timeout), prefix, mapping)
        references = program_references(prefix.with_suffix('.case.json'), mapping, actual)
        result.append({'geometry': actual['geometry'], 'forward_count': actual['forward_count'],
                       'families': family_rows(actual, mapping, comparison, references),
                       'comparison_status_counts': comparison['status_counts']})
    cohorts = [c for p in result for f in p['families'] for c in f.get('cohorts', [])]
    scored = [c for c in cohorts if c['status'] == 'compared']
    tiers = {}
    for cohort in scored:
        observed = cohort['observed']
        mean_us = observed['complete_activity_sum_ns'] / observed['event_count'] / 1000
        tier = 'micro_absolute_15us' if mean_us <= 50 else 'heavy_relative_15pct'
        bucket = tiers.setdefault(tier, {'compared': 0, 'passed': 0, 'events': 0})
        bucket['compared'] += 1
        bucket['passed'] += cohort.get('accuracy_pass') is True
        bucket['events'] += observed['event_count']
    return {'status': 'completed', 'populations': result,
            'comparison': {'status': 'operator_compared', 'compared': len(scored),
                           'passed_cohorts': sum(c.get('accuracy_pass') is True for c in scored),
                           'tiers': tiers}}


def read(path):
    path = Path(path)
    if path.stat().st_size > 50_000_000:
        raise ValueError('metadata_requires_streaming:' + str(path))
    return json.loads(path.read_text())


def identity(path):
    path = Path(path); value = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return {'path': str(path.resolve()), 'sha256': value.hexdigest(), 'size_bytes': path.stat().st_size}


def project(row, result, evidence):
    comparison = result.get('comparison') or {}
    observed = result.get('observed') or {}
    layers = result.get('per_layer_comparison') or {}
    card = {'id': row['id'], 'case_id': row['case_id'], 'phase': row['phase'],
            'entry_sha256': entry_hash(row),
            'source': row['source'], 'model_case': row.get('model_case', row.get('sim_case_path')),
            'geometry': result.get('geometry', row.get('geometry')),
            'status': result.get('status', comparison.get('status', 'failed')),
            'comparison': comparison, 'error': result.get('error'),
            'body_activity_ms': observed.get('body_activity_ms'),
            'body_internal_gap_ms': observed.get('body_internal_gap_ms'),
            'stage_span_ms': observed.get('stage_span_ms'),
            'per_layer': {k: v for k, v in layers.items() if k != 'layers'},
            'calibration': row.get('calibration', {}), 'evidence': evidence}
    if row['phase'] == 'prefill':
        card['client'] = result.get('client')
        card['ttft_prediction_ms'] = result.get('ttft_prediction_ms')
        card['prefix_cache'] = observed.get('prefix_cache')
        card['query_coverage_complete'] = observed.get('prompt_query_coverage_complete')
        card['body_activity_union_sum_ms'] = observed.get('body_activity_union_sum_ms')
        card['request_identity_status'] = observed.get('request_identity_status')
        card['request_population'] = observed.get('request_population')
    if 'serving_input' in result or 'serving_evidence' in observed:
        card['engine'] = observed
        prediction = result.get('prediction') or {}
        card['serving_prediction'] = {k: v for k, v in prediction.items() if k != 'error'}
    return card


def entry_hash(row):
    """Pin the full declaration, including source selection and engine settings."""
    return sha256(json.dumps(row, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def retained_cards(previous, rows, selected_ids, generation, scope):
    """Incremental updates retain only unchanged inputs from the same runtime."""
    runtime = previous.get('runtime', {})
    if (previous['scope'] != scope or runtime.get('package_sha256') != generation['package_sha256']
            or runtime.get('version') != generation['version']):
        raise ValueError('incremental_update_requires_same_sim_and_scope')
    current = {r['id']: r for r in rows}
    cards = []
    for card in previous['cases']:
        if card['id'] in selected_ids or card['id'] not in current:
            continue
        if card.get('entry_sha256') != entry_hash(current[card['id']]):
            raise ValueError('changed_case_requires_replay:' + card['id'])
        evidence = card['evidence']
        if identity(evidence['path'])['sha256'] != evidence['sha256']:
            raise ValueError('retained_evidence_changed:' + card['id'])
        cards.append(card)
    return cards


def render(report):
    def number(value): return '—' if value is None else f'{value:.3f}'
    lines = ['# Current profiling validation', '',
             'One canonical case registry and one recorded Sim package. '
             + ('Frozen native service functions are evaluated separately from Sim Body prediction. ' if report.get('scope') == 'generalization' else
                ('Selected costs are freshly replayed; unchanged cases retain verified evidence from this same Sim package. '
                 if report.get('retained_unchanged_sources') else 'All costs are fresh in this run. '))
             +
             'Calibration and held-out labels remain distinct; device Body latency is not client TPOT.', '']
    if report.get('scope', 'body') == 'body':
        lines += ['| Case | Phase | Calls | Real mean / P50 / P90 ms | Sim ms | Error | Status |',
                  '|---|---|---:|---:|---:|---:|---|']
    for row in report['cases'] if report.get('scope', 'body') == 'body' else []:
        c = row['comparison']; real = c.get('observed_ms') or {}; error = c.get('relative_error')
        status = ('PASS' if c.get('passed') else 'FAIL') if c.get('status') == 'compared' else row['status']
        lines.append(f"| {row['case_id']} | {row['phase']} | {c.get('observed_forward_count', real.get('count', '—'))} | "
                     + ' / '.join(number(real.get(k)) for k in ('mean', 'p50', 'p90'))
                     + f" | {number(c.get('predicted_ms'))} | {'—' if error is None else f'{error:+.2%}'} | {status} |")
    if report.get('scope') == 'engine':
        from engine import geometry_key
        lines += ['', '| Case | Complete target cycles | Cycle mean / P50 ms | Client token TPOT P50 ms | Serving status |',
                  '|---|---:|---:|---:|---|']
        for row in report['cases']:
            observed = row.get('engine') or {}
            groups = observed.get('cycle_geometry_groups', [])
            primary = observed.get('primary_geometry')
            group = next((g for g in groups if primary and geometry_key(g['geometry']) == geometry_key(primary)), {})
            cycle = group.get('target_cycle_span_ms') or {}
            serving = observed.get('serving_evidence', {})
            client = (serving.get('profiled_request_population', {}).get('recomputed_per_request_tpot_ms')
                      or serving.get('reported_aggregate_tpot_ms') or {})
            prediction = row.get('serving_prediction') or {}
            lines.append(f"| {row['case_id']} | {cycle.get('count', '—')} | {number(cycle.get('mean'))} / {number(cycle.get('p50'))} | {number(client.get('p50'))} | {prediction.get('reason', row['status'])} |")
        lines += ['', 'Device target cycles, completion-token TPOT and client delivery have different boundaries. '
                  'Uncovered cycle intervals are not assigned to Host scheduling without evidence.']
        failures = [r for r in report['cases'] if r.get('error')]
        if failures:
            lines += ['', '| Case | Prediction / source failure |', '|---|---|']
            for row in failures:
                error = row['error']
                detail = error.get('detail') or error.get('message') or error.get('reason') if isinstance(error, dict) else error
                text = str(detail).strip().splitlines()[-1] if detail else str(error)
                lines.append('| ' + row['case_id'] + ' | ' + text.replace('|', '\\|')[-500:] + ' |')
        client_only = [r for r in report['cases'] if (r.get('engine') or {}).get('serving_evidence', {}).get('metrics')]
        if client_only:
            lines += ['', '| Case | Client TTFT mean ms | Prefiller HTTP mean ms | Decoder TTFT mean ms | Token TPOT mean ms | Output tok/s |',
                      '|---|---:|---:|---:|---:|---:|']
            for row in client_only:
                serving = row['engine']['serving_evidence']; metrics = serving['metrics']
                values = [number(metrics.get(k, {}).get('mean')) for k in ('ttft_ms', 'prefill_ms', 'decode_ttft_ms', 'tpot_ms')]
                lines.append('| ' + row['case_id'] + ' | ' + ' | '.join(values) + ' | ' + number(serving.get('output_tok_s')) + ' |')
            lines += ['', 'Client-only and PD rows have no measured device Body. Prefiller HTTP, decoder first response and end-to-end request durations remain separate.']
        bridges = [(r['case_id'], (r.get('engine') or {}).get('serving_evidence', {}).get('acceptance_bridge')) for r in report['cases']]
        if any(b for _, b in bridges):
            lines += ['', '| Case | Measured acceptance | Tokens / step | Cadence-based TPOT ms | Measured token TPOT ms | Difference |',
                      '|---|---:|---:|---:|---:|---:|']
            for name, bridge in bridges:
                if bridge:
                    values = [number(bridge[k]) for k in ('observed_acceptance', 'expected_tokens_per_step', 'cadence_based_tpot_ms', 'observed_tpot_ms')]
                    lines.append('| ' + name + ' | ' + ' | '.join(values) + f" | {bridge['relative_difference']:+.2%} |")
            lines += ['', 'This acceptance bridge uses measured cadence and measured server acceptance. It is not a Sim prediction or a device Body estimate.']
    if any(r.get('client') for r in report['cases']):
        lines += ['', '| Case | Client TTFT ms | Predicted TTFT ms | Query coverage complete |',
                  '|---|---:|---:|---|']
        for row in report['cases']:
            if not row.get('client'): continue
            ttft = row['client'].get('ttft_ms')
            if isinstance(ttft, dict): ttft = ttft.get('mean')
            lines.append(f"| {row['case_id']} | {number(ttft)} | {number(row.get('ttft_prediction_ms'))} | {row.get('query_coverage_complete')} |")
        lines += ['', 'Prefill Body sums complete device chunk spans. Client TTFT includes other stages and is not substituted for Body.']
    if report.get('scope') == 'operators':
        lines += ['', '| Case | Tier | Passed / compared cohorts | Scored events |', '|---|---|---:|---:|']
        for row in report['cases']:
            for tier, stats in row['comparison'].get('tiers', {}).items():
                lines.append(f"| {row['case_id']} | {tier} | {stats['passed']} / {stats['compared']} | {stats['events']} |")
    if report.get('scope') == 'generalization':
        lines += ['', '| Experiment | Relation | Fitted domains | Passed / predicted populations |',
                  '|---|---|---:|---:|']
        for row in report['cases']:
            result = row['comparison']
            lines.append(f"| {row['case_id']} | {row.get('evaluation_relation', 'planned')} | {row.get('fitted_domains', '—')} | {result.get('passed_populations', 0)} / {result.get('predicted_populations', 0)} |")
        lines += ['', 'Retrospective source holdout is not new blind validation. Native activity differences are not additive Body wall-time errors.']
    lines += ['', 'Summary: ' + json.dumps(report['summary'], sort_keys=True), '',
              'Full per-layer, operator and prediction details retain their individual SHA256 evidence pointers. '
              'Missing evidence and failed predictions remain visible and never count as a pass.', '']
    return '\n'.join(lines)


def publish(report, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    for target, content in ((path, json.dumps(report, separators=(',', ':'), allow_nan=False) + '\n'),
                            (path.with_suffix('.md'), render(report))):
        if target.suffix == '.json' and len(content.encode()) >= 5_000_000:
            raise ValueError('current_scoreboard_exceeds_5mb')
        fd, name = tempfile.mkstemp(prefix='.' + target.name, dir=target.parent)
        try:
            with os.fdopen(fd, 'w') as stream: stream.write(content)
            os.replace(name, target)
        finally:
            Path(name).unlink(missing_ok=True)


def summarize(cards, requested_sources):
    counts = Counter(r['comparison'].get('status', r['status']) for r in cards)
    result = {'sources': len(cards), 'requested_sources': requested_sources,
              'status_counts': dict(counts), 'compared': counts['compared'],
              'passed': sum(r['comparison'].get('passed') is True for r in cards)}
    tiers = {}
    for card in cards:
        for tier, observed in card['comparison'].get('tiers', {}).items():
            total = tiers.setdefault(tier, {'compared': 0, 'passed': 0, 'events': 0})
            for field in total: total[field] += observed[field]
    if tiers: result['operator_tiers'] = tiers
    return result


def execute(row, base, scope, archive_root, timeout, generation):
    try:
        case_path = None
        observation_only = (scope == 'engine' and row.get('engine', {}).get('observation_only')) or (
            scope == 'body' and row['phase'] == 'prefill' and row['source'].get('kind') == 'client_json')
        if not observation_only:
            declaration = row['model_case']
            case_path = Path(declaration['path'])
            if not case_path.is_absolute(): case_path = base / case_path
            consumed_path = Path(row['sim_case_path'])
            if not consumed_path.is_absolute(): consumed_path = base / consumed_path
            if case_path.resolve() != consumed_path.resolve():
                raise ValueError('model_declaration_path_differs_from_consumer')
            before = identity(case_path)
            if any(before[k] != declaration[k] for k in ('sha256', 'size_bytes')):
                raise ValueError('model_declaration_changed_from_registry')
        if scope == 'operators':
            result = operator_case(row, base, Path(archive_root) / 'operators', timeout)
        elif scope == 'engine':
            from engine import run_case
            result = run_case(row, base, prediction_timeout_s=timeout)
        elif row['phase'] == 'prefill':
            from prefill import run_case
            result = run_case(row, base, prediction_timeout_s=timeout)
        else:
            decoded = replay_manifest({'schema_version': 'mindie-decode-forward-replay/1', 'cases': [row]},
                base=base, prediction_timeout_s=timeout, geometry_limit=1)
            result = next((r for r in decoded['cases'] if r['comparison']['status'] != 'unresolved'), decoded['cases'][0])
            result['other_geometry_populations'] = [r for r in decoded['cases'] if r is not result]
        if _sim_identity() != generation: raise ValueError('sim_package_changed_during_run')
        if case_path and identity(case_path) != before: raise ValueError('model_declaration_changed_during_run')
    except (OSError, ValueError, RuntimeError) as error:
        result = {'status': 'failed', 'comparison': {'status': 'failed', 'passed': False},
                  'error': {'type': type(error).__name__, 'message': str(error)}}
    return result


def execute_rows(rows, base, scope, archive_root, timeout, generation, workers):
    if workers < 1:
        raise ValueError('worker_count_must_be_positive')
    if workers == 1:
        for row in rows:
            yield row, execute(row, base, scope, archive_root, timeout, generation)
        return
    from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
    import psutil
    capacity = min(os.cpu_count() or 1, int(psutil.virtual_memory().available // (512 * 1024**2)))
    if workers > capacity:
        raise ValueError('workers_exceed_observed_cpu_or_512MiB_memory_budget')
    iterator = iter(rows)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = {}
        def fill():
            while len(pending) < workers:
                row = next(iterator, None)
                if row is None: break
                pending[pool.submit(execute, row, base, scope, archive_root, timeout, generation)] = row
        fill()
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                row = pending.pop(future)
                yield row, future.result()
            fill()


def run(manifest_path, *, output, archive_root, phase=None, scope='body', case_ids=(), timeout=90, workers=1, update=False):
    manifest_path = Path(manifest_path); manifest = read(manifest_path)
    if manifest['schema_version'] != 'mindie-cases/1': raise ValueError('unknown_case_registry')
    if scope == 'generalization':
        from service_evidence import run_generalization
        result = run_generalization(manifest, manifest_path.parent)
        cards = []
        for experiment in result['experiments']:
            summary = (experiment.get('evaluation') or {}).get('summary', {})
            cards.append({'id': experiment['id'], 'case_id': experiment['id'], 'phase': 'native_service',
                'status': experiment['status'], 'evaluation_relation': experiment.get('evaluation_relation'),
                'fitted_domains': experiment.get('fitted_domains'),
                'frozen_model_sha256': experiment.get('frozen_model_sha256'),
                'limits': experiment.get('limits', []), 'reason': experiment.get('reason'),
                'comparison': {'status': 'generalization_compared' if experiment['status'] == 'completed' else experiment['status'],
                    'predicted_populations': summary.get('predicted', 0),
                    'passed_populations': summary.get('passed', 0)},
                'evidence': archive_report(experiment, archive_root)})
        report = {'schema_version': 'mindie-current-validation/1', 'registry': identity(manifest_path),
            'scope': scope, 'status': result['status'], 'cases': cards, 'summary': result['summary'],
            'new_Sim_predictions': 0, 'new_blind_or_zero_shot_claimed': False}
        publish(report, output)
        return report
    eligible = [r for r in manifest['cases'] if (phase is None or r['phase'] == phase)
            and (not r.get('supported_scopes') or scope in r['supported_scopes'])
            and (scope != 'engine' or r.get('engine'))]
    rows = [r for r in eligible if not case_ids or r['id'] in case_ids or r['case_id'] in case_ids]
    if not rows or len({r['id'] for r in eligible}) != len(eligible): raise ValueError('empty_or_duplicate_case_selection')
    generation = _sim_identity(); started = time.monotonic(); cards = []
    if update:
        previous = read(output)
        if not case_ids:
            prior = {r['id']: r for r in previous['cases']}
            rows = [r for r in rows if prior.get(r['id'], {}).get('entry_sha256') != entry_hash(r)]
        cards = retained_cards(previous, eligible, {r['id'] for r in rows}, generation, scope)
    retained_count = len(cards)
    report = {'schema_version': 'mindie-current-validation/1', 'registry': identity(manifest_path),
              'runtime': generation, 'workers': workers, 'scope': scope, 'cases': cards, 'status': 'running', 'summary': {},
              'replayed_sources': len(rows), 'retained_unchanged_sources': retained_count}
    report['summary'] = summarize(cards, len(rows) + retained_count)
    for row, result in execute_rows(rows, manifest_path.parent, scope, archive_root, timeout, generation, workers):
        if identity(manifest_path) != report['registry']: raise ValueError('case_registry_changed_during_run')
        evidence = archive_report(result, archive_root)
        cards.append(project(row, result, evidence))
        report['summary'] = summarize(cards, len(rows) + retained_count)
        report['elapsed_seconds'] = time.monotonic() - started
        publish(report, output)
        print(json.dumps({'id': row['id'], 'status': cards[-1]['status'], **report['summary']}), flush=True)
    report['status'] = 'completed' if not report['summary']['status_counts'].get('failed') else 'failed'
    order = {r['id']: i for i, r in enumerate(eligible)}
    cards.sort(key=lambda r: order[r['id']])
    publish(report, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=Path(__file__).with_name('cases.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive-root', type=Path, required=True)
    parser.add_argument('--phase', choices=('decode', 'prefill'))
    parser.add_argument('--scope', choices=('body', 'operators', 'engine', 'generalization'), default='body')
    parser.add_argument('--case-id', action='append', default=[])
    parser.add_argument('--prediction-timeout', type=float, default=90)
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--update', action='store_true', help='Replay selected cases while retaining unchanged cases from this exact Sim package')
    args = parser.parse_args()
    result = run(args.cases, output=args.output, archive_root=args.archive_root, phase=args.phase,
                 scope=args.scope, case_ids=args.case_id, timeout=args.prediction_timeout, workers=args.workers, update=args.update)
    return int(result['status'] == 'failed')


if __name__ == '__main__': raise SystemExit(main())
