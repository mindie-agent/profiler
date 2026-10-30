"""Retain complete native/PMU populations inside previously accepted Body windows.

[Role] Supply scalar, DMA and routing evidence without re-segmenting model bodies.
[Invariants] Native ABI, BlockNum and exporter PMU columns remain separate axes.
  Missing counters are not zero. Copy direction uses an explicit same-stream
  copy/conv/copy chain; it never fabricates a tensor ABI for the copy itself.
[Timeouts & Locks] One streaming pass per source, 180s/5M rows, <=512MiB.
[Side-Effect Policy] Reads saved local captures; writes requested compact evidence.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.native_tensor_abi import native_tensor_contract, native_contract_issue
from mindie_profiler.sources_csv import probe_csv
from targeted_native_pmu import NativePmu, scan_rows

COPY = '_copy_conv_state_kernel'
KINDS = {COPY, 'CausalConv1d', 'MoeInitRoutingV3', 'DequantSwigluQuant',
         'Slice', 'SparseFlashMlaMetadata'}
CHAIN_MATERIALIZATIONS = {'Slice', 'ViewCopy'}


def identity(path):
    path = Path(path).resolve()
    digest = sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size}


def read(path):
    path = Path(path)
    if path.stat().st_size > 50_000_000:
        raise ValueError('metadata_exceeds_bounded_json_budget')
    return json.loads(path.read_text())


def geometry(value):
    return tuple(value[k] for k in ('tokens_per_sequence', 'sequences_per_replica', 'query_rows'))


def collect(actual_path, output, *, native_types=KINDS, hardware_case=None):
    started = time.perf_counter()
    tool_pin = identity(__file__)
    helper_pin = identity(Path(__file__).with_name('targeted_native_pmu.py'))
    actual_pin = identity(actual_path)
    actual = read(actual_path)
    body_pin = actual['body_acceptance_identity']
    if identity(body_pin['path']) != body_pin:
        raise ValueError('accepted_body_identity_changed')
    body = read(body_pin['path'])
    windows = sorted((w for w in body['forwards'] if geometry(w['geometry']) == geometry(actual['geometry'])),
                     key=lambda w: w['start_ns'])
    if len(windows) != actual['forward_count']:
        raise ValueError('accepted_body_population_changed')
    for left, right in zip(windows, windows[1:]):
        if left['end_ns'] > right['start_ns']:
            raise ValueError('accepted_body_windows_overlap')
    source = actual['source_identity']
    path = Path(source['path'])
    source_pin = identity(path)
    if any(source_pin[k] != source[k] for k in ('path', 'sha256', 'size_bytes')):
        raise ValueError('capture_identity_changed')
    before_stat = path.stat()
    case_pin = actual['case_identity']
    if hardware_case is None and identity(case_pin['path']) != case_pin:
        raise ValueError('retained_case_identity_changed')
    hardware_pin = identity(hardware_case or case_pin['path'])
    hardware = read(hardware_pin['path'])['machine']['sku']
    schema = probe_csv(path)
    starts = [w['start_ns'] for w in windows]
    groups, pending, scans = {}, {}, Counter()
    native_types = set(native_types)
    totals = {kind: Counter() for kind in native_types}

    def add(kernel, raw, window, *, direction=None, state=None, chain=None):
        event = kernel.event
        abi = native_tensor_contract(kernel)
        native_fields = {name: raw.get(name) for name in
                         ('Input Shapes', 'Input Data Types', 'Input Formats',
                          'Output Shapes', 'Output Data Types', 'Output Formats')}
        key = json.dumps([event.op_type, abi, native_fields, raw.get('Accelerator Core'),
                          raw.get('Block Num'), raw.get('Mix Block Num'), direction, state], sort_keys=True)
        if key not in groups:
            if len(groups) >= 2048:
                raise MemoryError('scalar_dma_partition_budget_exceeded')
            groups[key] = {'native_operator_type': event.op_type, 'native_abi': abi,
                           'native_abi_issue': native_contract_issue(kernel), 'raw_tensor_fields': native_fields,
                           'hardware': hardware, 'accelerator_core': raw.get('Accelerator Core'),
                           'block_num': raw.get('Block Num'), 'mix_block_num': raw.get('Mix Block Num'),
                           'copy_direction': direction, 'conditional_state_shapes': state,
                           'direction_basis': 'same_stream_copy_conv_copy' if direction else None,
                           'duration_ns_counter': Counter(), 'forward_counts': Counter(),
                           'raw_pmu': NativePmu(schema.header), 'chain_examples': []}
        group = groups[key]
        group['duration_ns_counter'][event.duration_ns] += 1
        group['forward_counts'][window['forward_id']] += 1
        group['raw_pmu'].add(raw, event, forward_id=window['forward_id'], layer_id=None)
        if chain and len(group['chain_examples']) < 2:
            group['chain_examples'].append(chain)
        totals[event.op_type][event.duration_ns] += 1

    def flush():
        for saved in pending.values():
            add(*saved['copy'])
        pending.clear()

    previous_window = None
    for kernel, raw in scan_rows(path, schema, native_types):
        event = kernel.event
        scans['decoded_rows'] += 1
        if event.start_ns >= windows[-1]['end_ns']:
            break
        at = bisect_right(starts, event.start_ns) - 1
        if at < 0:
            continue
        window = windows[at]
        if event.start_ns >= window['end_ns'] or event.end_ns > window['end_ns']:
            continue
        if event.device_id is not None and str(event.device_id) != str(window['device_id']):
            continue
        if previous_window != at:
            flush()
            previous_window = at
        scans['selected_body_events'] += 1
        stream = (event.device_id, event.stream_id)
        saved = pending.get(stream)
        if event.op_type == COPY and COPY in native_types:
            if saved and saved.get('conv'):
                chain = {'gather': saved['copy'][0].event.locator,
                         'convolution': saved['conv'].event.locator, 'scatter': event.locator}
                state = [list(s) for s in saved['conv'].input_shapes if len(s) == 3]
                add(*saved['copy'], direction='gather', state=state, chain=chain)
                add(kernel, raw, window, direction='scatter', state=state, chain=chain)
                del pending[stream]
                scans['paired_convolutions'] += 1
            else:
                if saved:
                    add(*saved['copy'])
                pending[stream] = {'copy': (kernel, raw, window)}
            continue
        if event.op_type == 'CausalConv1d' and saved:
            saved['conv'] = kernel
        elif event.op_type not in CHAIN_MATERIALIZATIONS and saved:
            add(*saved['copy'])
            del pending[stream]
        if event.op_type in native_types:
            add(kernel, raw, window)
    flush()
    expected = {kind: Counter() for kind in native_types}
    for family in actual['families']:
        kind = family['native_operator_type']
        if kind in expected:
            expected[kind].update(dict(family['duration_ns_counter']))
    if expected != totals:
        mismatches = {k: (sum(expected[k].values()), sum(totals[k].values()))
                      for k in native_types if expected[k] != totals[k]}
        raise ValueError(f'full_native_population_drift:{mismatches}')
    partitions = []
    for group in groups.values():
        group['duration_ns_counter'] = sorted(group['duration_ns_counter'].items())
        group['forward_counts'] = dict(group['forward_counts'])
        group['raw_pmu'] = group['raw_pmu'].result()
        group['group_id'] = 'sha256:' + sha256(json.dumps({k: v for k, v in group.items()
            if k not in ('raw_pmu', 'duration_ns_counter', 'forward_counts', 'chain_examples')}, sort_keys=True).encode()).hexdigest()
        partitions.append(group)
    if (path.stat().st_size, path.stat().st_mtime_ns) != (before_stat.st_size, before_stat.st_mtime_ns):
        raise ValueError('capture_changed_during_scan')
    if identity(__file__) != tool_pin or identity(Path(__file__).with_name('targeted_native_pmu.py')) != helper_pin:
        raise ValueError('extractor_changed_during_scan')
    # getrusage's unit conversion does not control workload placement.
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss = int(rss if sys.platform == 'darwin' else rss * 1024)
    if rss > 512 * 1024**2:
        raise MemoryError('scalar_dma_extraction_exceeds_512MiB')
    result = {'schema_version': 'mindie-scalar-dma-native-pmu/1', 'source_case_id': actual['source_case_id'],
              'source_identity': source_pin, 'actual_identity': actual_pin, 'body_identity': body_pin,
              'case_identity': case_pin, 'hardware_declaration_identity': hardware_pin,
              'hardware': hardware, 'geometry': actual['geometry'],
              'forward_count': len(windows), 'complete_native_histograms_match_actual': True,
              'native_counts': {k: sum(v.values()) for k, v in sorted(totals.items())},
              'header': list(schema.header), 'partitions': partitions,
              'extractor_identity': tool_pin, 'pmu_helper_identity': helper_pin,
              'execution': {'elapsed_seconds': time.perf_counter()-started, 'peak_rss_bytes': rss,
                            'source_passes': 1, 'prediction_calls': 0, 'scanned': dict(scans)},
              'scope': 'Previously accepted primary-geometry Body windows; source is streamed only through the final retained window.',
              'limitations': ['PMU pipelines overlap; sum and maximum differences are signed diagnostics, not synchronization measurements.',
                             'Copy direction has a same-stream source-caller relation, not a fabricated native ABI.',
                             'Instruction counts and per-owner/compiler execution are separate source declarations.']}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'source': result['source_case_id'], 'forwards': len(windows),
                      'native_counts': result['native_counts'], 'partitions': len(partitions), 'execution': result['execution']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--actual', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hardware-case', type=Path)
    args = parser.parse_args()
    collect(args.actual, args.output, hardware_case=args.hardware_case)
