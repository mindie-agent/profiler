"""Collect complete SFA PMU populations inside immutable GLM78 Body windows.

[Role] Join full native ABI/timing populations to exporter pipeline counters.
[Invariants] No new Body segment or geometry is admitted. Pipeline busy times
  overlap; signed sum/max-minus-elapsed diagnostics are not wall-time costs.
[Timeouts & Locks] One serial CSV stream/source, 180 s, 5M rows, <=512 MiB RSS.
[Side-Effect Policy] Local read-only profiling; write evidence, no Sim/device.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.sources_csv import probe_csv
from mindie_profiler.sources_db import sha256_file
from targeted_native_pmu import NativePmu, numeric_stats, scan_rows


ROOT = Path(__file__).resolve().parent
RETAINED = ROOT / 'acceptance-20261030-service-qwen-a3/glm78-native'
OUT = ROOT.parents[1] / 'data/observations/sources/arch22-physical-services/sparse-attention'
NATIVE = 'KvQuantSparseFlashAttention'
PIPELINES = {
    'aic': ('aic_mac_time(us)', 'aic_scalar_time(us)', 'aic_mte1_time(us)',
            'aic_mte2_time(us)', 'aic_fixpipe_time(us)'),
    'aiv': ('aiv_vec_time(us)', 'aiv_scalar_time(us)', 'aiv_mte2_time(us)', 'aiv_mte3_time(us)'),
    'core_envelopes': ('aicore_time(us)', 'aiv_time(us)'),
}


def read(path):
    return json.loads(Path(path).read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def decimal_value(value):
    try:
        result = Decimal(value)
        return result if result.is_finite() else None
    except (TypeError, InvalidOperation):
        return None


def paired_diagnostics(raw, duration_ns):
    """Keep per-call pairing; subtracting independently pooled means loses it."""
    elapsed = Decimal(duration_ns) / 1000
    result = {}
    for name, fields in PIPELINES.items():
        values = [decimal_value(raw.get(field)) for field in fields]
        result[name] = None if any(value is None for value in values) else {
            'sum_minus_elapsed_us': sum(values) - elapsed,
            'max_minus_elapsed_us': max(values) - elapsed,
        }
    return result


def memory_observability(header):
    """I-cache misses are not evidence of tensor-data L2 hits or HBM bytes."""
    candidates = [name for name in header if any(word in name.lower()
                  for word in ('hbm', 'ddr', 'l2', 'byte', 'bandwidth', 'memory'))]
    return {'data_memory_columns': candidates,
            'hbm_ddr_bytes': None, 'data_l2_bytes': None, 'data_l2_hit_rate': None,
            'status': 'requires_column_semantics_review' if candidates else 'not_exported',
            'instruction_cache_columns': [name for name in header if 'icache' in name.lower()],
            'interpretation': 'Instruction-cache miss rates and MTE pipeline times do not identify tensor-data L2 hits or HBM/DDR byte traffic.'}


def extract(path):
    started = time.perf_counter()
    pin = identity(path); retained = read(path)
    native = [group for group in retained['partitions'] if group['native_operator_type'] == NATIVE]
    expected = Counter()
    for group in native: expected.update(dict(group['duration_ns_counter']))
    if not native: raise ValueError('retained_sfa_population_missing')
    body_pin = retained['body_acceptance_identity']
    if identity(body_pin['path']) != body_pin: raise ValueError('body_identity_changed')
    body = read(body_pin['path']); geometry = retained['geometry']
    keys = ('query_rows', 'tokens_per_sequence', 'sequences_per_replica')
    windows = [row for row in body['forwards'] if all(row['geometry'][key] == geometry[key] for key in keys)]
    if len(windows) != retained['forward_count']: raise ValueError('forward_population_changed')
    source = retained['source_identity']; source_path = Path(source['path'])
    source_stat = source_path.stat()
    if identity(source_path)['sha256'] != source['sha256']: raise ValueError('source_identity_changed')
    schema = probe_csv(source_path); pmu = NativePmu(schema.header)
    by_abi = {}
    for group in native:
        key = json.dumps(group['native_abi'], sort_keys=True)
        target = by_abi.setdefault(key, {'expected_histogram': Counter(), 'histogram': Counter(),
                                        'expected_forward_counts': Counter(), 'forward_counts': Counter(),
                                        'native_abi': group['native_abi']})
        target['expected_histogram'].update(dict(group['duration_ns_counter']))
        target['expected_forward_counts'].update(group['forward_counts'])
    pairs = {name: {kind: Counter() for kind in ('sum_minus_elapsed_us', 'max_minus_elapsed_us')}
             for name in PIPELINES}
    complete = Counter(); histogram = Counter(); cursor = 0; scanned = 0; previous = None
    for row, raw in scan_rows(source_path, schema, {NATIVE}):
        event = row.event; scanned += 1
        if previous is not None and event.start_ns < previous: raise ValueError('nonchronological_capture')
        previous = event.start_ns
        while cursor < len(windows) and event.start_ns >= windows[cursor]['end_ns']: cursor += 1
        if cursor == len(windows): break
        window = windows[cursor]
        if event.op_type != NATIVE or event.start_ns < window['start_ns']: continue
        if event.end_ns > window['end_ns']: raise ValueError('sfa_crosses_retained_body_endpoint')
        key = json.dumps(native_tensor_contract(row), sort_keys=True)
        if key not in by_abi: raise ValueError('sfa_native_abi_changed')
        target = by_abi[key]; target['histogram'][event.duration_ns] += 1
        target['forward_counts'][window['forward_id']] += 1; histogram[event.duration_ns] += 1
        pmu.add(raw, event, forward_id=window['forward_id'], layer_id=None)
        for name, values in paired_diagnostics(raw, event.duration_ns).items():
            if values is None: continue
            complete[name] += 1
            for kind, value in values.items(): pairs[name][kind][str(value)] += 1
    if histogram != expected: raise ValueError('whole_native_duration_histogram_changed')
    for group in by_abi.values():
        if group['histogram'] != group['expected_histogram'] or group['forward_counts'] != group['expected_forward_counts']:
            raise ValueError('native_abi_forward_population_changed')
    if (source_stat.st_size, source_stat.st_mtime_ns) != (source_path.stat().st_size, source_path.stat().st_mtime_ns):
        raise ValueError('source_changed_during_scan')
    if identity(path) != pin or identity(body_pin['path']) != body_pin: raise ValueError('retained_evidence_changed')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if rss > 512 * 1024**2: raise MemoryError(f'sfa_pmu_exceeds_512_mib:{rss}')
    count = sum(histogram.values())
    result = {'schema_version': 'mindie-sfa-native-pmu/1', 'case_id': retained['case_id'],
        'source_identity': source, 'retained_native_identity': pin, 'body_acceptance_identity': body_pin,
        'collector_identity': identity(__file__), 'pmu_helper_identity': identity(ROOT / 'targeted_native_pmu.py'),
        'geometry': geometry, 'forward_count': len(windows), 'native_operator_type': NATIVE,
        'event_count': count, 'calls_per_forward': count / len(windows),
        'complete_native_histogram_unchanged': True, 'native_abi_and_forward_counts_unchanged': True,
        'retained_body_endpoints_unchanged': True, 'duration_ns_counter': sorted(histogram.items()),
        'observed_us': numeric_stats(Counter({str(Decimal(ns) / 1000): n for ns, n in histogram.items()})),
        'native_abi_groups': [{'native_abi': group['native_abi'], 'event_count': sum(group['histogram'].values()),
            'duration_ns_counter': sorted(group['histogram'].items()), 'forward_counts': dict(group['forward_counts'])}
            for group in by_abi.values()],
        'raw_pmu': pmu.result(), 'data_memory_observability': memory_observability(schema.header),
        'paired_pipeline_diagnostics': {name: {'field_names': list(PIPELINES[name]),
            'complete_pair_count': complete[name], 'incomplete_pair_count': count - complete[name],
            **{kind: {'statistics': numeric_stats(values),
                      'numeric_value_counter': sorted(values.items(), key=lambda item: Decimal(item[0]))}
               for kind, values in diagnostics.items()}} for name, diagnostics in pairs.items()},
        'interpretation': ['Pipeline busy intervals overlap and are not additive elapsed service.',
            'Signed sum-minus-elapsed and max-minus-elapsed are paired observations, not inferred cache hits or exclusive pipe costs.',
            'No HBM bandwidth or L2 hit-rate value is inferred from elapsed-minus-PMU.',
            'Layer IDs are not re-bound by kernel name in this pass; existing complete ABI/timing/Forward populations are validated.'],
        'execution': {'raw_targeted_scans': 1, 'source_hash_reads': 1, 'parsed_rows': scanned,
            'elapsed_seconds': time.perf_counter() - started, 'maximum_resident_set_size_bytes': rss,
            'new_predictions': 0, 'remote_or_device_actions': 0}}
    output = OUT / f"{retained['case_id']}-sfa-pmu.json"; write(output, result)
    print(json.dumps({'case_id': result['case_id'], 'event_count': count, 'forward_count': len(windows),
                      'output': str(output), 'execution': result['execution']}), flush=True)
    return result


def render(rows):
    lines = ['# A3 GLM78 complete SFA pipeline observations', '',
        'The three populations reuse retained Body windows and full native ABI/timing histograms. No new device run or prediction was executed.', '',
        '| Case | Forwards | Calls | Mean / P50 us | AIC sum−elapsed / max−elapsed us | AIV sum−elapsed / max−elapsed us |',
        '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        pair = row['paired_pipeline_diagnostics']
        def value(name, kind): return pair[name][kind]['statistics']['mean']
        lines.append(f"| {row['case_id']} | {row['forward_count']} | {row['event_count']} | {row['observed_us']['mean']:.3f} / {row['observed_us']['p50']:.3f} | {value('aic','sum_minus_elapsed_us'):.3f} / {value('aic','max_minus_elapsed_us'):.3f} | {value('aiv','sum_minus_elapsed_us'):.3f} / {value('aiv','max_minus_elapsed_us'):.3f} |")
    lines += ['', 'All sums and maxima are paired per call before aggregation. Pipeline times overlap; neither sum nor maximum is automatically a wall-time model. Raw numeric/missing/zero denominators and full histograms are retained in JSON.', '',
        'These CSV headers export instruction-cache miss rates and MTE time, but no HBM/DDR byte counts, tensor-data L2 byte counts, or data-L2 hit rate. Consequently these observations do not identify a scratch-cache hit rate or validate moving the declared off-chip scratch traffic into L2.', '']
    (OUT / 'README.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--case-id'); args = parser.parse_args()
    paths = sorted(RETAINED.glob(f"{args.case_id or '*'}-native-partitions.json"))
    if not paths: raise ValueError('no_retained_sources')
    rows = [extract(path) for path in paths]; render(rows)
