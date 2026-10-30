"""Export retained collective service curves with explicit payload conditions.

[Role] Separate measured collective service from source-declared network inputs.
[Invariants] No measured algorithm, switch hop RTT or link rate is invented from
  kernel names or end-to-end time. Native MC2 and HCCL are separate populations.
[Timeouts & Locks] Bounded saved JSON only, one receipt at a time; no workers.
[Side-Effect Policy] Write observational tables; never change Sim or collect data.
"""
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'examples/structure'
OUT = ROOT / 'data/observations/sources/arch3510-physical-services'
INPUTS = (
    'acceptance-20261030-source-callers-40e4300e/source-caller-reference-scoreboard.json',
    'acceptance-20261030-qwen35-source-complete/hccl-references/source-caller-reference-scoreboard.json',
    'acceptance-20261030-hccl-aicpu-ts-reference/source-caller-reference-scoreboard.json',
)


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata_requires_streaming:' + str(path))
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def export():
    started = time.monotonic()
    inventory = read(EXAMPLES / 'acceptance-20261030-hccl-66/capture-body-hccl-summary.json')
    hardware = {r['source_identity']['sha256']: r['hardware_sku'] for r in inventory['cases']}
    points, sources, seen = [], [], set()
    for relative in INPUTS:
        path = EXAMPLES / relative
        receipt = read(path)
        pin = identity(path)
        sources.append(pin)
        for case in receipt['cases']:
            for group in case['groups']:
                if not group['native_operator_type'].lower().startswith('hcom_'):
                    continue
                corr = group['source_correspondence']
                selection = corr['selection']
                hist = group['duration_ns_counter']
                n = sum(c for _, c in hist)
                total = sum(ns * c for ns, c in hist)
                if n != group['observed_us']['count'] or total != group['observed_activity_sum_ns']:
                    raise ValueError('saved_collective_histogram_changed')
                key = (case['source_identity']['sha256'], group['native_operator_type'],
                       group['retained_group_id'], json.dumps(case['geometry'], sort_keys=True))
                if key in seen:
                    raise ValueError('duplicate_collective_observation_population')
                seen.add(key)
                sku = hardware[case['source_identity']['sha256']]
                payload = selection['payload_bytes']
                points.append({'case_id': case['case_id'], 'source_identity': case['source_identity'],
                    'body_acceptance_identity': case['body_acceptance_identity'],
                    'retained_receipt_identity': pin, 'retained_group_id': group['retained_group_id'],
                    'hardware_sku': sku, 'geometry': case['geometry'],
                    'forward_count': case['forward_count'],
                    'native_operator_type': group['native_operator_type'],
                    'declared_role': group['declared_role'], 'layer_ids': group['layer_ids'],
                    'event_count': n, 'calls_per_forward': n / case['forward_count'],
                    'observed_service_us': group['observed_us'],
                    'observed_event_category': corr['observed_event_category'],
                    'observed_implementation_name': corr['observed_implementation_name'],
                    'observed_device_engine': corr['observed_device_engine'],
                    'declared_collective_program': selection,
                    'measured_payload_bytes': corr['measured_payload_bytes'],
                    'measured_algorithm': corr['observed_hccl_algorithm'],
                    'template_selection_confirmed': corr['template_selection_confirmed'],
                    'declared_fabric_family': 'UB_MESH' if sku.startswith('Ascend950') and selection['topology'] == 'MESH_1D' else None,
                    'fabric_basis': 'source_compatible_topology_declaration_not_measured_switch_path',
                    'declared_payload_bytes_per_observed_us': payload / group['observed_us']['mean'],
                    'effective_service_ratio_is_pure_link_bandwidth': False,
                    'independent_control_rtt_us': None, 'independent_switch_hop_latency_us': None,
                    'incast_rx_queue_time_us': None, 'conditions': group['conditions']})
        del receipt
    curves = defaultdict(list)
    for i, point in enumerate(points):
        s = point['declared_collective_program']
        key = (point['hardware_sku'], point['observed_device_engine'], s['collective'],
               s['template'], s['ranks'], s['dtype_bytes'], s['topology'])
        curves[key].append(i)
    result = {'schema_version': 'mindie-conditional-network-service-baseline/1',
        'source_receipts': sources, 'points': points,
        'curve_groups': [{'identity': dict(zip(('hardware_sku', 'observed_engine', 'collective',
            'declared_template', 'declared_ranks', 'declared_dtype_bytes', 'declared_topology'), key)),
            'point_indices': indexes,
            'declared_payload_bytes': sorted({points[i]['declared_collective_program']['payload_bytes'] for i in indexes}),
            'curve_fit_performed': False} for key, indexes in sorted(curves.items(), key=lambda x: str(x[0]))],
        'coverage': {'source_count': len({p['source_identity']['sha256'] for p in points}),
            'groups': len(points), 'observed_collective_calls': sum(p['event_count'] for p in points),
            'groups_4k_through_64k': sum(4096 <= p['declared_collective_program']['payload_bytes'] <= 65536 for p in points),
            'groups_over_64k': sum(p['declared_collective_program']['payload_bytes'] > 65536 for p in points),
            'exact_4k_payload_observed': any(p['measured_payload_bytes'] == 4096 for p in points),
            'ub_clos_measured_path_available': False,
            'all_point_payloads_are_source_conditions': all(p['measured_payload_bytes'] is None for p in points)},
        'incast_evidence': {
            'same_shape_kimi_c2_combine_counterexample': identity(EXAMPLES / 'acceptance-20261030-kimi-paged-fia-pmu/mc2-pmu-summary.json'),
            'multi_rank_v41_timing_evidence': identity(EXAMPLES / 'acceptance-20261030-v41-final6-operators-e8/dp-cohort-bounded-evidence.json')
                if (EXAMPLES / 'acceptance-20261030-v41-final6-operators-e8/dp-cohort-bounded-evidence.json').exists() else None,
            'rx_packet_arrival_times_measured': False, 'peer_payload_matrix_measured': False,
            'causal_incast_delay_identified': False,
            'interpretation': 'Same-ABI timing and multi-rank phase skew constrain candidate models; neither uniquely identifies switch ingress contention.'},
        'interpretation': [
            'Each point retains one complete collective observation population; AIV tasks and envelope-only populations are not added together.',
            'Template, rank graph, payload and fabric are explicit source conditions. Captured native task name alone does not confirm them.',
            'The payload/service ratio is an observable effective-service quantity under the declared payload, not a pure link measurement.',
            'RTT cannot uniquely decompose into switch-hop, controller issue, notify polling and peer-ready components without independent observables.',
            'No UB_CLOS curve or exact 4KB point is fabricated. Existing observations cover the listed discrete payloads; empty intervals remain uncovered.',
            'MC2 PMU baselines are exported separately and are not summed into HCCL service curves.'],
        'execution': {'raw_event_reads': 0, 'new_predictions': 0,
            'elapsed_seconds': time.monotonic() - started,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'network-observable-service-baseline.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'coverage': result['coverage'], 'execution': result['execution']}))


if __name__ == '__main__':
    export()
