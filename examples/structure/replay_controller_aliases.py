"""[Role] Re-extract all accepted captures after typed controller alias repair.
[Invariants] Reuse pinned Sim model plans, never old endpoints as new truth;
  retain old generations and report every endpoint/population/statistics change.
  Communication data-plane envelopes are not removed by an AICPU suffix.
[Timeouts & Locks] One sequential source worker, 180 s parser / 190 s worker;
  <=512 MiB, <=5M rows, bounded active forward and retained examples. No locks.
[Side-Effect Policy] Read local sources and write a new extraction generation;
  no Sim cost, device initialization, remote access or old-report mutation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from mindie_profiler.decode_segmentation import (
    _TAIL_NAMES, auto_segment_decode_forwards, is_aicpu_controller,
)
from mindie_profiler.normalized import kernel_rows


MAX_JSON = 32 * 1024**2


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('bounded_json_metadata_limit:' + str(path))
    return json.loads(path.read_text())


def write(path, value):
    encoded = json.dumps(value, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n'
    if len(encoded.encode()) > MAX_JSON:
        raise ValueError('bounded_output_limit:' + str(path))
    Path(path).write_text(encoded)


def identity(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            digest.update(chunk)
    return {'path': str(path.resolve()), 'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size}


def same_pin(pin):
    current = identity(pin['path'])
    return all(current[key] == pin[key] for key in ('sha256', 'size_bytes'))


def runtime_identity():
    import mindie_profiler
    paths = sorted(Path(mindie_profiler.__file__).resolve().parent.glob('*.py'))
    paths.extend((Path(__file__), Path(__file__).with_name('replay_body_operator_families.py')))
    return {str(path.resolve()): identity(path)['sha256'] for path in paths}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def scope_key(value):
    return tuple(value.get(key) for key in ('kind', 'layer_id', 'rank_id', 'device_id'))


def scope_statistics(values):
    return {scope_key(row): {key: row[key] for key in
            ('stats', 'activity_ms_stats', 'internal_gap_ms_stats') if key in row} for row in values}


def changed_stats(before, after):
    result = []
    for key in sorted(set(before) | set(after), key=str):
        old, new = before.get(key), after.get(key)
        if old != new:
            result.append({'scope': list(key), 'before': old, 'after': new,
                           'changed_fields': sorted(k for k in set(old or {}) | set(new or {})
                                                    if (old or {}).get(k) != (new or {}).get(k))})
    return result


def compare(previous, current):
    # Head occurrence identity stays independent of a changed body boundary.
    def forward_key(row):
        return tuple(row.get(k) for k in ('rank_id', 'device_id', 'head_start_ns', 'head_end_ns'))
    old = {forward_key(row): row for row in previous['forwards']}
    new = {forward_key(row): row for row in current['forwards']}
    if len(old) != len(previous['forwards']) or len(new) != len(current['forwards']):
        raise ValueError('duplicate_head_occurrence')
    common = old.keys() & new.keys()
    changed = []
    for key in sorted(common, key=str):
        left, right = old[key], new[key]
        fields = [k for k in ('forward_id', 'start_ns', 'end_ns', 'geometry', 'query_rows',
                  'body_forward_span_ms', 'body_activity_ms', 'body_internal_gap_ms') if left[k] != right[k]]
        if fields:
            changed.append({'forward_id': left['forward_id'], 'head_occurrence': list(key),
                            'changed_fields': fields, 'before': {k: left[k] for k in fields},
                            'after': {k: right[k] for k in fields}})
    oldgeo = {canonical(g['geometry']): g for g in previous['geometry_groups']}
    newgeo = {canonical(g['geometry']): g for g in current['geometry_groups']}
    geometries = []
    for key in sorted(set(oldgeo) | set(newgeo)):
        left, right = oldgeo.get(key), newgeo.get(key)
        changes = {}
        for field in ('body_forward_span_ms', 'body_activity_ms', 'body_internal_gap_ms'):
            before, after = (left or {}).get(field), (right or {}).get(field)
            if before != after:
                changes[field] = {'before': before, 'after': after}
        layers = changed_stats(scope_statistics((left or {}).get('per_layer_ms', [])),
                               scope_statistics((right or {}).get('per_layer_ms', [])))
        stages = changed_stats(scope_statistics((left or {}).get('stage_span_ms', [])),
                               scope_statistics((right or {}).get('stage_span_ms', [])))
        geometries.append({'geometry': json.loads(key),
            'previous_forward_count': (left or {}).get('body_forward_span_ms', {}).get('count', 0),
            'current_forward_count': (right or {}).get('body_forward_span_ms', {}).get('count', 0),
            'changes': changes, 'layer_statistics_changes': layers, 'stage_statistics_changes': stages})
    return {'previous_body_count': len(old), 'current_body_count': len(new),
        'previous_geometry_count': len(oldgeo), 'current_geometry_count': len(newgeo),
        'accepted_population_unchanged': old.keys() == new.keys(),
        'added_head_occurrences': [list(k) for k in new.keys() - old.keys()],
        'removed_head_occurrences': [list(k) for k in old.keys() - new.keys()],
        'body_endpoint_changed_count': sum(bool({'start_ns', 'end_ns'} & set(r['changed_fields'])) for r in changed),
        'body_activity_changed_count': sum('body_activity_ms' in r['changed_fields'] for r in changed),
        'body_geometry_changed_count': sum('geometry' in r['changed_fields'] for r in changed),
        'changed_forwards': changed, 'geometry_groups': geometries,
        'layer_statistics_changes': changed_stats(scope_statistics(previous['per_layer_ms']),
                                                 scope_statistics(current['per_layer_ms'])),
        'stage_statistics_changes': changed_stats(scope_statistics(previous['stage_span_ms']),
                                                 scope_statistics(current['stage_span_ms'])),
        'previous_body_forward_span_ms': previous['body_forward_span_ms'],
        'current_body_forward_span_ms': current['body_forward_span_ms'],
        'previous_body_activity_ms': previous['body_activity_ms'],
        'current_body_activity_ms': current['body_activity_ms']}


def worker(entry, input_pin, output):
    started = time.perf_counter(); before = runtime_identity()
    if not same_pin(entry['body_identity']): raise ValueError('accepted_extraction_changed')
    old = read(entry['body_identity']['path']); source = Path(entry['source']['path'])
    source_pin = identity(source)
    if any(source_pin[k] != entry['source'][k] for k in ('sha256', 'size_bytes')):
        raise ValueError('raw_source_changed')
    original_stat = source.stat()
    count, body_counts = Counter(), Counter(); alias_examples = []
    rank = old['forwards'][0]['rank_id'] if old['forwards'] else ''
    def stream():
        for row in kernel_rows(source, rank_id=rank, rank_index=None,
                               max_rows=5_000_000, timeout_s=180):
            event = row.event
            count['parsed_positive_events'] += 1
            controller = is_aicpu_controller(event)
            if controller:
                count['typed_controllers'] += 1
                count['controller_type:' + event.op_type] += 1
                if event.op_type not in _TAIL_NAMES:
                    count['newly_recognized_controller_aliases'] += 1
                    if len(alias_examples) < 8:
                        alias_examples.append({'op_type': event.op_type, 'core': event.core,
                            'task_type': event.task_type, 'locator': event.locator,
                            'start_ns': event.start_ns, 'end_ns': event.end_ns})
            if event.op_type.startswith('hcom_'):
                count['hcom_rows_preserved'] += 1
                if controller: raise ValueError('hcom_data_plane_classified_as_controller')
            yield event
    def consume(result, events):
        for event in events:
            if result['start_ns'] <= event.start_ns < result['end_ns']:
                if is_aicpu_controller(event):
                    body_counts['typed_controllers'] += 1
                    body_counts['controller_type:' + event.op_type] += 1
                    if event.op_type not in _TAIL_NAMES:
                        body_counts['newly_recognized_controller_aliases'] += 1
                elif event.op_type.startswith('hcom_'):
                    body_counts['hcom_rows_preserved'] += 1
    current = auto_segment_decode_forwards(stream(), entry['model_config'], on_forward=consume,
        max_forwards=max(1024, len(old['forwards']) + 16))
    partition = current['scan_counts']
    if partition['positive_events'] != sum(partition.get(k, 0) for k in (
            'complete_body_segment_events', 'auxiliary_candidate_segment_events',
            'rejected_segment_events', 'trailing_segment_events')):
        raise ValueError('positive_event_partition_not_conserved')
    stat = source.stat()
    if (stat.st_size, stat.st_mtime_ns) != (original_stat.st_size, original_stat.st_mtime_ns):
        raise ValueError('raw_source_changed_during_scan')
    if runtime_identity() != before or not same_pin(entry['body_identity']):
        raise ValueError('runtime_or_previous_extraction_changed_during_scan')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    if rss > 512 * 1024**2: raise MemoryError('alias_replay_exceeds_512_mib')
    current.update(case_id=entry['case_id'], source_identity=old['source_identity'],
        model_structure_identity=entry['case_identity'], positive_event_partition_verified=True,
        extraction_runtime={'source_identities': before, 'unchanged': True},
        extraction_provenance={'input_manifest_identity': input_pin,
            'previous_extraction_identity': entry['body_identity'],
            'source_identity_verified': source_pin,
            'model_config_sha256': hashlib.sha256(canonical(entry['model_config']).encode()).hexdigest(),
            'model_configuration_reused_exactly': True,
            'policy_change': 'typed_supported_AICPU_names_case_and_underscore_canonicalization',
            'source_hash_reads': 1, 'raw_capture_scans': 1, 'new_predictions': 0},
        elapsed_seconds=time.perf_counter() - started, maximum_resident_set_size_bytes=rss)
    comparison = compare(old, current)
    path = output / ('auto-forward-' + entry['case_id'] + '.json')
    write(path, current)
    result = {'schema_version': 'mindie-controller-alias-source-comparison/1', 'status': 'completed',
        'case_id': entry['case_id'], 'source_identity': entry['source'],
        'previous_extraction_identity': entry['body_identity'], 'new_extraction_identity': identity(path),
        'input_manifest_identity': input_pin, 'runtime_source_identity': before,
        'runtime_sources_unchanged': True, 'comparison': comparison,
        'capture_controller_accounting': dict(count), 'body_controller_accounting': dict(body_counts),
        'new_alias_examples': alias_examples, 'elapsed_seconds': time.perf_counter() - started,
        'maximum_resident_set_size_bytes': rss, 'raw_capture_scans': 1, 'new_predictions': 0}
    target = output / (entry['case_id'] + '-comparison.json'); write(target, result)
    return result, identity(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--worker-case'); parser.add_argument('--cases', nargs='*')
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = read(args.input); pin = identity(args.input)
    entries = manifest['cases']
    if args.worker_case:
        worker(next(e for e in entries if e['case_id'] == args.worker_case), pin, args.output_dir)
        return
    if args.cases: entries = [e for e in entries if e['case_id'] in args.cases]
    # The requested defect's representative is first, without changing its data.
    entries.sort(key=lambda e: (e['case_id'] != 'a3_kimi4_tp8_w4a8_c32', e['case_id']))
    before = runtime_identity(); started = time.perf_counter(); receipts = []
    for entry in entries:
        command = [sys.executable, str(Path(__file__).resolve()), '--input', str(args.input.resolve()),
                   '--output-dir', str(args.output_dir.resolve()), '--worker-case', entry['case_id']]
        begin = time.perf_counter()
        try:
            child = subprocess.run(command, capture_output=True, text=True, timeout=190)
            if child.returncode:
                row = {'case_id': entry['case_id'], 'status': 'failed', 'returncode': child.returncode,
                       'stderr': child.stderr[-6000:], 'elapsed_seconds': time.perf_counter() - begin}
            else:
                path = args.output_dir / (entry['case_id'] + '-comparison.json'); result = read(path)
                row = {'case_id': entry['case_id'], 'status': 'completed', 'comparison_identity': identity(path),
                    'new_extraction_identity': result['new_extraction_identity'],
                    'elapsed_seconds': result['elapsed_seconds'],
                    'maximum_resident_set_size_bytes': result['maximum_resident_set_size_bytes'],
                    'summary': {key: result['comparison'][key] for key in (
                        'previous_body_count', 'current_body_count', 'previous_geometry_count',
                        'current_geometry_count', 'accepted_population_unchanged',
                        'body_endpoint_changed_count', 'body_activity_changed_count', 'body_geometry_changed_count')},
                    'new_body_alias_count': result['body_controller_accounting'].get('newly_recognized_controller_aliases', 0)}
        except subprocess.TimeoutExpired as error:
            row = {'case_id': entry['case_id'], 'status': 'failed', 'reason': 'worker_timeout',
                   'timeout_seconds': error.timeout, 'elapsed_seconds': time.perf_counter() - begin}
        receipts.append(row)
        write(args.output_dir / 'decode-forward-auto-acceptance.json', {
            'schema_version': 'mindie-controller-alias-replay/1', 'status': 'running',
            'input_manifest_identity': pin, 'runtime_source_identity': before, 'cases': receipts})
        print(json.dumps(row), flush=True)
    stable = runtime_identity() == before
    complete = len(receipts) == len(entries) and all(row['status'] == 'completed' for row in receipts)
    write(args.output_dir / 'decode-forward-auto-acceptance.json', {
        'schema_version': 'mindie-controller-alias-replay/1',
        'status': 'completed' if complete and stable else 'failed',
        'input_manifest_identity': pin, 'runtime_source_identity': before,
        'runtime_sources_unchanged': stable, 'cases': receipts,
        'raw_capture_scan_attempts': len(receipts), 'new_predictions': 0,
        'elapsed_seconds': time.perf_counter() - started,
        'scope': 'all current source captures; original model_config and old accepted generation preserved'})
    raise SystemExit(not (complete and stable))


if __name__ == '__main__': main()
