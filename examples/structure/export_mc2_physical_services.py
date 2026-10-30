"""Export inspectable MC2 pipeline observations from retained 66-source ledgers.

[Role] Build A3/A5 scalar, DMA and wait baselines without rereading captures.
[Invariants] Exported PMU columns keep their units, missingness and scope. Task
  wait is not scalar spin; marginal busy times cannot identify barrier latency.
[Timeouts & Locks] One bounded source ledger at a time; no locks or workers.
[Side-Effect Policy] Write local observation tables, never hardware or Sim rates.
"""
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parents[2]
LEDGERS = ROOT / 'examples/structure/acceptance-20261030-hccl-66'
OUT = ROOT / 'data/observations/sources/arch3510-physical-services'
FIELDS = ('Duration(us)', 'Wait Time(us)', 'aicore_time(us)', 'aic_total_cycles',
          'aic_scalar_time(us)', 'aic_scalar_wait_time(us)', 'aic_mac_time(us)',
          'aic_mte1_time(us)', 'aic_mte2_time(us)', 'aic_mte3_time(us)',
          'aic_fixpipe_time(us)', 'aiv_time(us)', 'aiv_total_cycles',
          'aiv_scalar_time(us)', 'aiv_scalar_wait_time(us)', 'aiv_vec_time(us)',
          'aiv_mte2_time(us)', 'aiv_mte3_time(us)')


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('ledger_requires_streaming:' + str(path))
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def extract():
    started = time.monotonic()
    summary_path = LEDGERS / 'capture-body-hccl-summary.json'
    summary = read(summary_path)
    rows, sources, counts, availability = [], [], Counter(), Counter()
    checks = 0
    for entry in summary['cases']:
        pin = entry['artifact_identity']
        path = Path(pin['path'])
        path = path if path.is_absolute() else ROOT / path
        if identity(path)['sha256'] != pin['sha256']:
            raise ValueError('ledger_pin_changed:' + str(path))
        data = read(path)
        source_rows = 0
        for gi, geometry in enumerate(data['body_geometry_groups']):
            for pi, group in enumerate(geometry['groups']):
                if group['event_category'] != 'native_fused_communication_program':
                    continue
                hist = group['duration_ns_counter']
                event_count = sum(count for _, count in hist)
                activity = sum(ns * count for ns, count in hist)
                if event_count != group['observed_us']['count']:
                    raise ValueError('native_histogram_count_changed')
                checks += 1
                raw = group['raw_pmu']
                metrics = {}
                for name in FIELDS:
                    value = raw['fields'].get(name)
                    if value is None:
                        metrics[name] = {'column_present': False, 'numeric_count': 0,
                            'missing_or_na_count': event_count, 'statistics': None,
                            'availability': 'column_not_exported'}
                        availability[name + ':not_exported'] += event_count
                        continue
                    metric = {k: v for k, v in value.items() if k != 'numeric_value_counter'}
                    counter = value.get('numeric_value_counter', [])
                    numeric_n = sum(n for _, n in counter)
                    if numeric_n != value['numeric_count']:
                        raise ValueError('pmu_histogram_count_changed:' + name)
                    if numeric_n:
                        mean = sum(Decimal(v) * n for v, n in counter) / numeric_n
                        if abs(float(mean) - value['statistics']['mean']) > 1e-8 * max(1, abs(float(mean))):
                            raise ValueError('pmu_histogram_mean_changed:' + name)
                    checks += 1
                    metric['availability'] = 'numeric_observed' if numeric_n else 'not_numeric_or_na'
                    metric['unit'] = 'microseconds' if name.endswith('(us)') else 'cycles'
                    metrics[name] = metric
                    availability[name + ':numeric_observed'] += numeric_n
                    availability[name + ':missing_or_na'] += value['missing_or_na_count']
                    availability[name + ':invalid_numeric'] += value['invalid_numeric_count']
                rows.append({'case_id': data['case_id'],
                    'source_identity': data['source_identity'],
                    'retained_ledger_identity': pin,
                    'body_acceptance_identity': data['body_acceptance_identity'],
                    'retained_group_path': f'body_geometry_groups/{gi}/groups/{pi}',
                    'hardware_sku': data['hardware_sku'],
                    'placement': {k: data[k] for k in ('tp', 'dp', 'ep')},
                    'geometry': geometry['geometry'], 'forward_count': geometry['forward_count'],
                    'native_operator_type': group['native_operator_type'],
                    'implementation_name': group['implementation_name'],
                    'accelerator_core': group['accelerator_core'],
                    'attention_kind': group['attention_kind'], 'block': group['block'],
                    'layer_population': group['layer_population'],
                    'layer_counts': group['layer_counts'],
                    'event_count': event_count, 'observed_us': group['observed_us'],
                    'observed_activity_ms_per_forward': activity / geometry['forward_count'] / 1e6,
                    'calls_per_forward': event_count / geometry['forward_count'],
                    'pmu': metrics, 'launch_dimensions': raw['dimensions'],
                    'task_identity': group['task_identity'],
                    'longest_retained_examples': raw.get('longest_calls', [])[:3],
                    'measured_payload_bytes': group['measured_payload_bytes'],
                    'source_declared_programs': group['source_declared_programs'],
                    'identifiability': {
                        'per_owner_instruction_counts_joined': False,
                        'independent_scalar_issue_rate': None,
                        'independent_scalar_memory_rate': None,
                        'scalar_spin_wait_time': None,
                        'syncall_latency': None,
                        'network_wait_cause_proven': False,
                        'elapsed_minus_pipeline_max_is_syncall': False}})
                source_rows += 1
                counts[data['hardware_sku'] + '|' + group['native_operator_type']] += event_count
        if source_rows:
            sources.append({'case_id': data['case_id'], 'source_sha256': data['source_identity']['sha256'],
                            'groups': source_rows, 'retained_ledger_identity': pin})
        del data
    output = {'schema_version': 'mindie-mc2-observable-pmu-baseline/1',
        'source_receipt_identity': identity(summary_path), 'sources': sources, 'groups': rows,
        'summary': {'retained_capture_sources_examined': len(summary['cases']),
            'native_communication_sources': len(sources), 'groups': len(rows),
            'native_event_counts': dict(sorted(counts.items())),
            'pmu_availability_event_counts': dict(sorted(availability.items())),
            'histogram_math_checks': checks},
        'interpretation': [
            'Whole native Dispatch/Combine and fused DispatchFFNCombine boundaries are distinct; do not pool their timings.',
            'PMU counters retain exporter aggregation. Block Num is a launch dimension, not a measured active-owner count.',
            'Wait Time(us) is task wait metadata, not a measured scalar spin, SyncAll or network component.',
            'Separate marginal PMU histograms do not recover per-event overlap/correlation; no elapsed-minus-max attribution is made.',
            'Missing scalar-wait columns remain missing; recorded numeric zero is preserved as zero.',
            'Same-boundary service calibration is allowed. Independent instruction-unit prices need source-count/owner joins and identifiable variation.',
            'These are complete accepted-body populations from a retained extraction generation; controller overlays do not reclassify native MC2 tasks.'],
        'execution': {'raw_event_reads': 0, 'new_predictions': 0,
            'elapsed_seconds': time.monotonic() - started,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'mc2-observable-pmu-baseline.json').write_text(json.dumps(output, indent=2) + '\n')
    return output


if __name__ == '__main__':
    result = extract()
    print(json.dumps({'summary': result['summary'], 'execution': result['execution']}))
