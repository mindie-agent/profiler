"""Inspect bounded retained DP representatives without changing runtime models.

[Role] Reuse complete-body topology to compare same-capture DP execution shapes.
[Invariants] Absolute-time overlap is conditional alignment, not a shared step
  identity. Padded shapes and boolean-mask descriptors never prove valid rows.
[Timeouts & Locks] At most 30k streamed events/rank, 60 s/source; no locks.
[Side-Effect Policy] Read local gzip sources; write compact evidence only.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards
from mindie_profiler.normalized import kernel_rows, shapes
from mindie_sim.prediction.structure import parse_case

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'examples/structure/acceptance-20261030-v41-final6'
OPERATORS = ROOT / 'examples/structure/acceptance-20261030-v41-final6-operators-e8'


def read(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024**2:
        raise ValueError(f'bounded_metadata_exceeded:{path}')
    return json.loads(path.read_text())


def identity(path):
    path = Path(path)
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size}


def event_evidence(event):
    return {'op_type': event.op_type, 'name': event.name, 'start_ns': event.start_ns,
            'end_ns': event.end_ns, 'locator': event.locator,
            'inputs': shapes(event.input_shapes), 'outputs': shapes(event.output_shapes),
            'input_dtypes': event.input_dtypes, 'output_dtypes': event.output_dtypes,
            'input_formats': event.input_formats, 'output_formats': event.output_formats}


def forward_evidence(result, events):
    layers = [stage for stage in result['stages'] if stage['layer_id'] is not None]
    starts = [stage['start_ns'] for stage in layers]
    selected = [event for event in events if result['start_ns'] <= event.start_ns < result['end_ns']]
    native = [event for event in selected if event.op_type == 'DispatchFFNCombine']
    # Every layer has its own fusion; retain all 40 small descriptors so counts
    # and hidden/MC2 populations can be independently checked without rereading.
    components = []
    for event in native:
        layer = layers[bisect_right(starts, event.start_ns) - 1]
        inputs, outputs = shapes(event.input_shapes), shapes(event.output_shapes)
        components.append({'layer_id': layer['layer_id'], 'start_ns': event.start_ns,
                           'end_ns': event.end_ns, 'locator': event.locator,
                           'x_shape': inputs[0] if inputs else None,
                           'route_ids_shape': inputs[3] if inputs and len(inputs) > 3 else None,
                           'active_mask_shape': inputs[7] if inputs and len(inputs) > 7 else None,
                           'local_expert_counts_shape': outputs[1] if outputs and len(outputs) > 1 else None,
                           'active_mask_values': None, 'routed_counts_values': None})
    body = next(stage for stage in result['stages'] if stage['kind'] == 'target_body')
    examples = []
    for layer in layers:
        if layer['layer_id'] not in {0, 19, 39}:
            continue
        candidates = [event for event in selected if layer['start_ns'] <= event.start_ns < layer['end_ns']]
        for kind in ('HcPre', 'SparseFlashMla', 'DispatchFFNCombine'):
            match = next((event for event in candidates if event.op_type == kind), None)
            if match is not None:
                examples.append({'layer_id': layer['layer_id'], **event_evidence(match)})
    return {key: result[key] for key in ('forward_id', 'start_ns', 'end_ns', 'geometry',
            'body_forward_span_ms', 'device_id', 'rank_id', 'confidence')} | {
        'body_endpoint_evidence': body['evidence'], 'matched_layer_count': len(layers),
        'native_mc2_count': len(native), 'native_mc2': components,
        'representative_rows': examples}


def run(output):
    core_files = sorted((ROOT / 'mindie_profiler').glob('*.py'))
    before = {str(path): identity(path)['sha256'] for path in core_files}
    cases = {row['case_id']: row for row in read(BASE / 'decode-forward-auto-cases.json')['cases']}
    report = {'schema_version': 'mindie-bounded-dp-cohort-evidence/1',
              'not_new_live_collection': True, 'core_files_sha256': before,
              'algorithm_identity': identity(__file__), 'captures': [],
              'limitations': [
                  'Topology and absolute-time overlap conditionally align complete target forwards; no shared step ID is retained.',
                  'CSV timestamps have no retained cross-device clock synchronization receipt.',
                  'Block-table/hidden/mask extents describe execution buffers; active mask, routed histograms and valid token values are absent.',
                  'Four TP0 representatives do not establish behavior of the other twelve TP ranks.',
                  'Native MC2 elapsed includes peer synchronization; it is not a link-bandwidth observation.']}
    started = time.perf_counter()
    for concurrency in (4, 64):
        key = f'a3_v41_w8a8_tp4_dp4_ep16_dspark7_c{concurrency}'
        item = cases[key]
        prior_path = BASE / f'auto-forward-{key}.json'
        prior = read(prior_path)
        reference = prior['forwards'][:5]
        stop_ns = reference[-1]['end_ns'] + 5_000_000
        case_path = OPERATORS / f'body-operator-{key}-v41-new6.case.json'
        parsed = parse_case(read(case_path))
        config = parsed.model.to_dict()
        config.update(tp=parsed.runtime.parallel.tp)
        config.update(prior['segmentation_options'])
        capture_root = Path(item['scenario_evidence']['capture_directory'])
        capture_manifest = read(capture_root / 'manifest.json')
        rank_metadata = {row['rank']: row for row in capture_manifest['ranks']}
        capture = {'case_id': key, 'client_concurrency': concurrency,
                   'manifest_identity': identity(capture_root / 'manifest.json'),
                   'case_identity': identity(case_path), 'prior_body_identity': identity(prior_path),
                   'bounded_reference_body_count': len(reference),
                   'scan_end_ns': stop_ns, 'ranks': [], 'aligned_windows': []}
        for dp in range(4):
            rank = f'dp{dp}_tp0'
            source = capture_root / 'ranks' / rank / 'kernel_details.csv.gz'
            step_path = source.with_name('step_trace_time.csv')
            with step_path.open(newline='') as stream:
                steps = list(csv.DictReader(stream))
            forwards, scan = [], {'decoded_rows': 0, 'first_start_ns': None, 'last_start_ns': None,
                                  'stopped_at_absolute_time_bound': False, 'full_capture_scanned': False}
            begin = time.perf_counter()

            def bounded_events():
                for row in kernel_rows(source, rank_id=rank, max_rows=30_000, timeout_s=60):
                    scan['decoded_rows'] += 1
                    scan['first_start_ns'] = scan['first_start_ns'] or row.event.start_ns
                    scan['last_start_ns'] = row.event.start_ns
                    if row.event.start_ns > stop_ns:
                        scan['stopped_at_absolute_time_bound'] = True
                        break
                    yield row.event

            def consume(result, events):
                forwards.append(forward_evidence(result, events))

            extraction = auto_segment_decode_forwards(bounded_events(), config, on_forward=consume,
                max_events=30_000, max_forward_events=10_000, max_detailed_forwards=0, max_samples_per_layer=0)
            capture['ranks'].append({'rank_id': rank, 'dp_replica_from_retained_path': dp,
                'tp_shard_from_retained_path': 0, 'raw_origin': rank_metadata[rank]['src'],
                'source_identity': identity(source), 'step_identity': identity(step_path),
                'step_rows': steps, 'scan': scan, 'elapsed_s': time.perf_counter() - begin,
                'forward_count': len(forwards), 'forwards': forwards,
                'anomaly_counts': extraction.get('anomaly_counts'),
                'scan_counts': extraction['scan_counts']})
        for ref in capture['ranks'][0]['forwards']:
            members = []
            for rank in capture['ranks']:
                overlapping = [forward for forward in rank['forwards']
                    if min(ref['end_ns'], forward['end_ns']) > max(ref['start_ns'], forward['start_ns'])]
                candidate = overlapping[0] if len(overlapping) == 1 else None
                members.append({'rank_id': rank['rank_id'], 'overlap_candidate_count': len(overlapping),
                    'forward_id': candidate['forward_id'] if candidate else None,
                    'start_offset_from_dp0_us': (candidate['start_ns'] - ref['start_ns']) / 1000 if candidate else None,
                    'end_offset_from_dp0_us': (candidate['end_ns'] - ref['end_ns']) / 1000 if candidate else None,
                    'geometry': candidate['geometry'] if candidate else None,
                    'body_forward_span_ms': candidate['body_forward_span_ms'] if candidate else None,
                    'mc2_capacity_rows': sorted({row['x_shape'][0] for row in candidate['native_mc2']}) if candidate else None})
            complete = all(member['overlap_candidate_count'] == 1 for member in members)
            capture['aligned_windows'].append({'dp0_forward_id': ref['forward_id'],
                'basis': 'unique_absolute_timestamp_overlap_of_complete_40_layer_forwards',
                'alignment_status': 'conditional_unique' if complete else 'unresolved',
                'shared_step_id_observed': False, 'members': members,
                'execution_geometry_uniform': len({json.dumps(member['geometry'],sort_keys=True) for member in members}) == 1 if complete else None,
                'idle_dp_status': 'unresolved_active_mask_values_not_captured'})
        report['captures'].append(capture)
        print(json.dumps({'case': key, 'rank_forward_counts': [rank['forward_count'] for rank in capture['ranks']],
                          'decoded_rows': [rank['scan']['decoded_rows'] for rank in capture['ranks']]}), flush=True)
    after = {str(path): identity(path)['sha256'] for path in core_files}
    if before != after:
        raise RuntimeError('profiler_runtime_changed_during_bounded_scan')
    report['elapsed_s'] = time.perf_counter() - started
    report['max_rss_bytes'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report['core_identity_unchanged'] = True
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
