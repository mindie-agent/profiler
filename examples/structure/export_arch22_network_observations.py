"""Export retained A3 network timing and phase evidence without device work.

[Role] Preserve observed topology, event-timed payload curves and task phases.
[Invariants] Warm unprofiled timings and instrumented traces are separate.
  Phase durations overlap and notify wait is not a pure link or switch RTT.
[Timeouts & Locks] One small existing trace/ledger at a time, no locks.
[Side-Effect Policy] Read local historical assets; write compact observations.
"""
from collections import Counter
from decimal import Decimal
from hashlib import sha256
import json
from math import ceil
from pathlib import Path
import resource
from statistics import mean, median
import time


REPO = Path(__file__).resolve().parents[2]
CAPTURES = Path('/Volumes/data/mindie-sim-data/a3/2026-10-20/accuracy-round-20261021/comm')
OUT = REPO / 'data/observations/sources/arch22-physical-services/network'
RUNS = ('a3-comm-r2-sio-c1', 'a3-comm-r2-sio-c2',
        'a3-comm-r2-hccssw-c1', 'a3-comm-r4-pkg2pkg3-c1')
PHASES = {'NOTIFY_WAIT_SQE', 'NOTIFY_RECORD_SQE', 'SDMA_SQE', 'WRITE_VALUE_SQE',
          'NOTIFY_WAIT', 'NOTIFY_RECORD', 'EVENT_WAIT', 'EVENT_RECORD'}
HCCL_LEDGERS = REPO / 'examples/structure/acceptance-20261030-hccl-66'


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('bounded_network_artifact_required')
    return json.loads(path.read_text())


def stats(values):
    values = sorted(values)
    return {'count': len(values), 'mean': mean(values), 'p50': median(values),
            'p90': values[ceil(.9 * len(values)) - 1], 'min': values[0], 'max': values[-1]}


def union(intervals):
    end, total = None, 0
    for start, stop in sorted(intervals):
        total += max(0, stop - max(start, end if end is not None else start))
        end = max(stop, end if end is not None else stop)
    return total


def topology(parent):
    recorded = parent['metadata_before']['npu_smi_topo']
    if recorded['exit_code'] != 0:
        raise ValueError('captured_topology_command_failed')
    lines = [line.split() for line in recorded['stdout'].splitlines()]
    headers = next(line for line in lines if line and line[0] == 'Phy-ID0')
    matrix = {line[0]: dict(zip(headers, line[1:])) for line in lines
              if len(line) == len(headers) + 1 and line[0].startswith('Phy-ID')}
    devices = parent['devices']
    pairs = [{'source_phy_id': a, 'destination_phy_id': b, 'link_label': matrix[f'Phy-ID{a}'][f'Phy-ID{b}']}
             for a in devices for b in devices if a != b]
    return {'devices': devices, 'world_size': parent['world_size'], 'observed_pairs': pairs,
            'basis': 'captured_successful_npu_smi_topology', 'forwarding_hop_count': None,
            'topology_levels_of_selected_collective': None,
            'note': 'SIO/HCCS_SW labels identify paths, not the internal switch topology or collective phase route.'}


def curve_rows(parent):
    rows = []
    for condition in parent['conditions']:
        if condition['collective'] == 'overlap':
            continue  # Separate simultaneous-communicator workload, not one call.
        for rank, measured in condition['ranks'].items():
            if measured['status'] != 'completed':
                raise ValueError('retained_curve_condition_failed')
            samples = measured['samples']
            durations = [s['per_op_ms'] * 1000 for s in samples]
            repetitions = condition['repetitions_per_batch']
            if any(abs(s['batch_ms'] / repetitions - s['per_op_ms']) > 1e-10 for s in samples):
                raise ValueError('retained_event_batch_arithmetic_differs')
            rows.append({'case_id': condition['case_id'], 'rank': int(rank),
                         'collective': condition['collective'], 'payload_bytes': condition['payload_bytes'],
                         'repetitions_per_batch': repetitions, 'elapsed_us': stats(durations),
                         'sample_count': len(samples), 'scope': 'unprofiled_device_event_batch_divided_by_repetitions',
                         'pure_link_bandwidth_identified': False, 'raw_sample_source': 'parent.conditions[].ranks[].samples'})
    return rows


def trace_rows(path):
    events = read(path)
    processes = {e['pid']: e['args']['name'] for e in events if e.get('name') == 'process_name'}
    hardware = [e for e in events if e.get('ph') == 'X' and processes.get(e['pid']) == 'Ascend Hardware']
    envelopes = [e for e in events if e.get('ph') == 'X' and processes.get(e['pid']) == 'Communication'
                 and e['name'].startswith('hcom_allReduce_')]
    ns = lambda value: int(Decimal(str(value)) * 1000)
    tasks = [(ns(e['ts']), ns(e['ts']) + ns(e['dur']), e) for e in hardware]
    rows = []
    for envelope in sorted(envelopes, key=lambda e: Decimal(str(e['ts']))):
        start, stop = ns(envelope['ts']), ns(envelope['ts']) + ns(envelope['dur'])
        selected = [(s, t, e) for s, t, e in tasks if start <= s and t <= stop and e['name'] in PHASES]
        crossing = [(s, t, e) for s, t, e in tasks if e['name'] in PHASES and s < stop and t > start
                    and not (start <= s and t <= stop)]
        signatures, phase_summaries = [], []
        for stream in sorted({e['tid'] for _, _, e in selected}):
            ordered = sorted(((s, t, e) for s, t, e in selected if e['tid'] == stream), key=lambda x: x[0])
            signatures.append({'stream_id': stream, 'ordered_phase_types': [e['name'] for _, _, e in ordered]})
        for phase in sorted({e['name'] for _, _, e in selected}):
            values = [(s, t) for s, t, e in selected if e['name'] == phase]
            phase_summaries.append({'phase_type': phase, 'count': len(values),
                'reported_zero_duration_count': sum(s == t for s, t in values),
                'duration_us': stats([(t - s) / 1000 for s, t in values]),
                'activity_sum_us': sum(t - s for s, t in values) / 1000,
                'interval_union_us': union(values) / 1000, 'additive_across_phases': False})
        args = envelope['args']
        if args['data_type'] != 'BFP16':
            raise ValueError('unsupported_trace_payload_dtype')
        rows.append({'name': envelope['name'], 'start_ns': start, 'end_ns': stop,
            'elapsed_us': (stop - start) / 1000, 'payload_bytes': args['count'] * 2,
            'payload_basis': 'trace_hccl_count_times_reported_BFP16_width',
            'observed_algorithm_signature': args['alg_type'], 'connection_id': args.get('connection_id'),
            'phase_summaries': phase_summaries, 'stream_signatures': signatures,
            'crossing_phase_count': len(crossing),
            'contained_phase_union_us': union([(s, t) for s, t, _ in selected]) / 1000,
            'association_basis': 'same_trace_device_temporal_containment; no fabricated_task_parent_id',
            'scope': 'profiled_collective; separate from unprofiled calibration curve',
            'pure_notify_rtt_or_switch_latency_identified': False})
    return {'trace_identity': pin(path), 'envelopes': rows,
            'reported_zero_duration_is_not_zero_instruction_cost': True,
            'observed_hardware_event_count': len(hardware), 'profiled_collective_count': len(rows)}


def model_envelope_rows(ledger):
    """Keep measured whole-call services without turning adjacent tensors into payloads."""
    rows = []
    for geometry_index, geometry in enumerate(ledger['body_geometry_groups']):
        for group_index, group in enumerate(geometry['groups']):
            if group['event_category'] != 'collective_envelope_only':
                continue
            histogram = group['duration_ns_counter']
            count = sum(n for _, n in histogram)
            activity_ns = sum(duration * n for duration, n in histogram)
            if count != group['observed_us']['count']:
                raise ValueError('whole_model_histogram_population_differs')
            forward_count = geometry['forward_count']
            if abs(count / forward_count - group['calls_per_forward']) > 1e-10:
                raise ValueError('whole_model_calls_per_forward_differs')
            if abs(activity_ns / forward_count / 1e6 - group['activity_ms_per_forward']) > 1e-8:
                raise ValueError('whole_model_activity_per_forward_differs')
            rows.append({'geometry': geometry['geometry'], 'forward_count': forward_count,
                'native_operator_type': group['native_operator_type'],
                'implementation_name': group['implementation_name'],
                'accelerator_core': group['accelerator_core'], 'attention_kind': group['attention_kind'],
                'block': group['block'], 'layer_population': group['layer_population'],
                'layer_counts': group['layer_counts'], 'elapsed_us': group['observed_us'],
                'calls_per_forward': group['calls_per_forward'],
                'activity_ms_per_forward': group['activity_ms_per_forward'],
                'histogram_locator': f'body_geometry_groups[{geometry_index}].groups[{group_index}].duration_ns_counter',
                'measured_payload_bytes': group['measured_payload_bytes'],
                'observed_hccl_algorithm': group['observed_hccl_algorithm'],
                'parent_child_task_association': group['parent_child_task_association'],
                'preceding_tensor_byte_counter': group['preceding_tensor_byte_counter'],
                'preceding_tensor_is_measured_collective_payload': False,
                'whole_call_service_is_observed': True, 'per_phase_service_identified': False,
                'pure_link_bandwidth_identified': False,
                'scope': 'retained_source_geometry_complete_collective_envelope_population',
                'activity_is_not_additive_body_latency': True})
    return rows


def whole_model_envelopes():
    sources = []
    for path in sorted(HCCL_LEDGERS.glob('*a3*capture-hccl.json')):
        ledger = read(path)
        if ledger['hardware_sku'] != 'Ascend910_9362' or ledger['tp'] not in (8, 16):
            continue
        sources.append({'case_id': ledger['case_id'], 'ledger_identity': pin(path),
            'source_identity': ledger['source_identity'], 'body_acceptance_identity': ledger['body_acceptance_identity'],
            'case_identity': ledger['case_identity'], 'hardware_sku': ledger['hardware_sku'],
            'declared_parallelism': {k: ledger[k] for k in ('tp', 'dp', 'ep')},
            'body_count': ledger['body_count'], 'geometry_count': ledger['geometry_count'],
            'topology_matrix_or_collective_phase_route_observed': False,
            'topology_note': 'TP is the retained case declaration; it does not identify card/die placement or per-task links.',
            'envelope_services': model_envelope_rows(ledger)})
        del ledger
    return sources


def build():
    started = time.perf_counter()
    runs = []
    for name in RUNS:
        folder = CAPTURES / name
        path = folder / f'{name}.parent.json'
        parent = read(path)
        if parent['status'] != 'completed':
            raise ValueError('historical_network_run_not_completed')
        traces = sorted(folder.rglob('msprof_*.json'))
        runs.append({'run_id': name, 'parent_identity': pin(path), 'topology': topology(parent),
            'protocol': parent['protocol'], 'source_worker_sha256': parent['source_sha256'],
            'unprofiled_payload_curve': curve_rows(parent), 'profiled_phase_evidence': [trace_rows(p) for p in traces]})
    models = whole_model_envelopes()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if peak > 512 * 1024**2:
        raise MemoryError('network_evidence_exceeds_512MiB')
    output = {'schema_version': 'mindie-arch22-network-observations/1', 'producer_identity': pin(__file__),
        'runs': runs, 'whole_model_envelope_sources': models,
        'coverage': {'world_sizes_observed_in_phase_traces': [2, 4],
            'world_sizes_8_16_phase_assignment': 'not_established_by_these_traces',
            'whole_model_declared_tp_values': sorted({s['declared_parallelism']['tp'] for s in models}),
            'whole_model_source_count': len(models),
            'whole_model_geometry_count': sum(s['geometry_count'] for s in models),
            'whole_model_body_count': sum(s['body_count'] for s in models),
            'whole_model_collective_event_count': sum(g['elapsed_us']['count'] for s in models for g in s['envelope_services'])},
        'identifiability': {'joint_collective_service_observed': True, 'physical_link_path_labels_observed': True,
            'per_switch_hop_delay_identified': False, 'notify_instruction_unit_price_identified': False,
            'SIO_HCCS_phase_route_identified': False,
            'reason': 'No per-task link routing or exclusive wait-cause evidence. Profiled timing and unprofiled queued batches have different boundaries.'},
        'execution': {'existing_local_parent_json_reads': len(runs),
            'existing_local_trace_json_reads': sum(len(r['profiled_phase_evidence']) for r in runs),
            'retained_whole_model_ledger_sources': len(models),
            'whole_model_csv_reads': 0,
            'new_device_collections': 0, 'new_cost_predictions': 0,
            'elapsed_seconds': time.perf_counter() - started, 'peak_rss_bytes': peak}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'retained-a3-network-observations.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({'runs': len(runs), 'curve_points': sum(len(r['unprofiled_payload_curve']) for r in runs),
        'profiled_envelopes': sum(p['profiled_collective_count'] for r in runs for p in r['profiled_phase_evidence']),
        **output['execution']}))


if __name__ == '__main__':
    build()
