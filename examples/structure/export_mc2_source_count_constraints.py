"""Join retained MC2 PMU populations to source-operation inventories.

[Role] Export four source-bound physical domains for subsequent joint fitting.
[Invariants] Source calls are not compiled ISA. Per-owner counts stay separate
  from all-owner totals; PMU owner reduction is unknown. Missing waits, DMA
  descriptors and transaction counts remain unknown, not zero observations.
[Timeouts & Locks] Four bounded metadata graphs; no Engine, raw scan or locks.
[Side-Effect Policy] Write an independent JSON/Markdown observation matrix.
"""
from collections import Counter, defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
FIXED = Path('/tmp/mindie-sim-cohort-wave6-20261029')
OUT = ROOT / 'data/observations/sources/arch3510-physical-services'
BASELINE = OUT / 'mc2-observable-pmu-baseline.json'
RUNTIME = 'c2b21f2023d096392ec7a4b7406df88d8611849a'
CASE_ROOT = FIXED / 'examples/cases/high-concurrency-20261030'
DOMAINS = (
    ('a5_kimi_tp8_e16_bf16_c1_p4k', ROOT / 'examples/structure/acceptance-20261030-service-kimi-v41/cases-source-routing-84d80b40/a5_kimi_tp8_e16_bf16_c1_p4k.json', 4104),
    ('a5_kimi_tp8_e16_bf16_c32_p4k', CASE_ROOT / 'kimi-source-complete/a5_kimi_tp8_e16_bf16_c32_p4k_source_complete.json', 4104),
    ('a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1', CASE_ROOT / 'v41-composed-arch35-conditional/a5_v41_fp8_tp1_dp8_ep8_tpot5ms_c1-composed-arch35-source.json', 2048),
    ('a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64', CASE_ROOT / 'v41-composed-arch35-conditional/a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64-composed-arch35-source.json', 2048),
)


def read(path):
    path = Path(path)
    if path.stat().st_size > 50*1024**2:
        raise ValueError('bounded_metadata_required')
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(), 'size_bytes': path.stat().st_size}


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return sha256(stable(value).encode()).hexdigest()


def source_identities():
    paths = ('prediction/mc2_phase.py', 'prediction/mc2_instructions.py',
             'prediction/operators/mc2_fullmesh.py', 'prediction/instructions.py',
             'prediction/mc2_graph.py', 'prediction/source_force_eplb.py')
    return [identity(FIXED / 'mindie_sim' / path) for path in paths]


def matrix_rank(values):
    """Numerical rank of the retained design, with column-scale normalization."""
    if not values:
        return 0
    scales = [max(abs(row[i]) for row in values) or 1 for i in range(len(values[0]))]
    a = [[float(x)/scales[i] for i, x in enumerate(row)] for row in values]
    rank = 0
    for col in range(len(scales)):
        pivot = max(range(rank, len(a)), key=lambda r: abs(a[r][col]), default=None)
        if pivot is None or abs(a[pivot][col]) < 1e-10:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        div = a[rank][col]; a[rank] = [x/div for x in a[rank]]
        for row in range(len(a)):
            if row != rank:
                mul = a[row][col]
                a[row] = [x-mul*y for x, y in zip(a[row], a[rank])]
        rank += 1
        if rank == len(a):
            break
    return rank


def histogram(group):
    return Counter({int(t): int(n) for t, n in group['duration_ns_counter']})


def primitive_counts(phases):
    totals, owner_totals = Counter(), defaultdict(Counter)
    for phase in phases:
        for owner, steps in phase['primitive_services']['owners'].items():
            for entry in steps.values():
                totals.update(entry['counts']); owner_totals[int(owner)].update(entry['counts'])
    return totals, owner_totals


def source_program(phases, die):
    from mindie_sim.prediction.mc2_phase import build, contract
    from mindie_sim.prediction.mechanism import Geometry
    from mindie_sim.prediction.operators.mc2_fullmesh import SOURCE
    from mindie_sim.prediction.mc2_instructions import SOURCE_RANGES

    resource_units = {name: die.units(name) for name, _ in die.rates}
    geometry = Geometry(die.compute_units, resource_units)
    rows = []
    for op in sorted(phases, key=lambda o: dict(o.metadata)['mc2_phase']['phase']):
        raw = dict(op.metadata)['mc2_phase']; plan = build(op, geometry)
        meta = plan.metadata
        rows.append({'phase': raw['phase'], 'source_geometry': raw,
                     'active_owner_domain': meta['active_owner_domain'], 'owner_basis': meta['owner_basis'],
                     'owner_approximation': meta['owner_approximation'],
                     'primitive_services': meta['primitive_services'],
                     'source_service_details': meta['source_service_details'],
                     'row_layout': meta['row_layout'], 'count_basis': meta['count_basis']})
    raw = dict(phases[0].metadata)['mc2_phase']
    ledger = contract(raw, die.units('vector'))
    layout = asdict(ledger.layout)
    exact_details = {p.name: dict(p.details) for p in ledger.phases}
    totals, owner_totals = primitive_counts(rows)
    return {'kind': raw['kind'], 'geometry': {k: raw[k] for k in (
                'width', 'dtype', 'source_tokens', 'top_k', 'source_assignments', 'received_assignments', 'experts', 'ep')},
            'precision': {'input_dtype': layout['input_dtype'], 'payload_dtype': layout['payload_dtype'], 'quant_mode': layout['quant_mode']},
            'wire_layout': layout, 'source_identity': SOURCE, 'source_ranges': SOURCE_RANGES[raw['kind']],
            'phase_count': len(rows), 'phases': rows,
            'source_primitive_counts_all_owners': dict(totals),
            'source_primitive_counts_by_owner': {str(k): dict(v) for k, v in sorted(owner_totals.items())},
            'source_primitive_counts_max_single_owner': {k: max(v.get(k, 0) for v in owner_totals.values()) for k in totals},
            'source_operation_details': exact_details,
            'source_wire_blocks_per_token': layout['blocks'],
            'source_sent_framed_blocks': raw['source_assignments'] * layout['blocks'],
            'source_received_flag_bytes': raw['received_assignments'] * ledger.layout.flag_bytes,
            'unidentified_counts': {'native_mte2_descriptor_count': None, 'native_mte3_descriptor_count': None,
                'compiled_memory_transactions': None, 'notify_wait_calls': None,
                'cross_core_sync_calls': None, 'failed_flag_poll_iterations': None,
                'hardware_memory_cacheline_amplification': None},
            'unidentified_count_basis': 'selected source scalar/pipe operations exported; other operations not enumerated by this planner',
            'compiled_binary_identity_established': False}


def captured_abi(case_id, baseline_group, native_parts):
    if native_parts is None:
        return {'native_abi': None, 'native_abi_sha256': None,
                'basis': 'retained_MC2_ledger_has_no_complete_native_tensor_descriptor; source_conditional_geometry_only'}
    parts = [p for p in native_parts['partitions'] if p['native_operator_type'] == baseline_group['native_operator_type']
             and p['attention_kind'] == baseline_group['attention_kind']
             and p['layer_counts'] == baseline_group['layer_counts']]
    part, = parts
    if part['observed_us']['count'] != baseline_group['event_count'] or part['observed_us'] != baseline_group['observed_us']:
        raise ValueError('native_partition_population_differs')
    return {'native_abi': part['native_abi'], 'native_abi_sha256': digest(part['native_abi']),
            'basis': 'complete_retained_native_partition_exact_population',
            'native_partition_identity': identity(ROOT / f'examples/structure/acceptance-20261030-kimi-paged-fia-pmu/{case_id}-native-partitions.json')}


def complete_pmu_mean(row, name):
    """A subset of numeric calls cannot stand in for the whole population."""
    field = row['pmu'].get(name, {})
    stats = field.get('statistics')
    return stats['mean'] if stats and field.get('numeric_count') == row['event_count'] else None


def response_constraints(rows, programs, design):
    """Form controlled descriptive domains, preserving token/peer confounding."""
    domain_rows = defaultdict(list)
    feature_by_program = {row['source_program_id']: row['features'] for row in design}
    for row in rows:
        p = programs[row['source_program_id']]; g = p['geometry']
        domain = {'native_operator_type': row['native_operator_type'],
            'width': g['width'], 'experts': g['experts'], 'ep': g['ep'], 'top_k': g['top_k'],
            'precision': p['precision'], 'source_identity': p['source_identity'],
            'placement': row['placement'], 'attention_kind': row['attention_kind'],
            'layer_population': row['layer_population'],
            'observed_launch_domain': {name: sorted(str(v) for v, _ in row['launch_dimensions'][name])
                for name in ('Accelerator Core', 'Block Num', 'Mix Block Num', 'Device_id')}}
        domain_rows[stable(domain)].append(row)
    result = []
    for key, members in sorted(domain_rows.items()):
        members.sort(key=lambda r: programs[r['source_program_id']]['geometry']['source_tokens'])
        points = []
        for row in members:
            p = programs[row['source_program_id']]
            points.append({'row_id': row['row_id'], 'case_id': row['case_id'],
                'source_program_id': row['source_program_id'], 'source_identity': row['source_identity'],
                'geometry': row['geometry'], 'source_geometry': p['geometry'],
                'native_abi_sha256': row['native_abi_sha256'],
                'event_count': row['event_count'], 'forward_count': row['forward_count'],
                'source_primitive_counts_all_owners': p['source_primitive_counts_all_owners'],
                'source_primitive_counts_max_single_owner': p['source_primitive_counts_max_single_owner'],
                'wire_blocks_sent': p['source_sent_framed_blocks'],
                'observed_mean_us': {'elapsed': row['observed_us']['mean'], **{
                    name: complete_pmu_mean(row, name) for name in
                    ('aiv_scalar_time(us)', 'aiv_mte2_time(us)', 'aiv_mte3_time(us)')}}})
        features = [feature_by_program[p['source_program_id']] for p in points]
        contrasts = []
        for low, high in zip(points, points[1:]):
            count0 = low['source_primitive_counts_all_owners']['scalar_ub_access']
            count1 = high['source_primitive_counts_all_owners']['scalar_ub_access']
            metrics = {}
            for name, v0 in low['observed_mean_us'].items():
                v1 = high['observed_mean_us'][name]
                delta = None if v0 is None or v1 is None else v1-v0
                concordance = None if delta is None else (
                    'unchanged_response' if delta == 0 else
                    'source_count_unchanged' if count1 == count0 else
                    'same_direction' if delta*(count1-count0) > 0 else 'opposite_direction')
                metrics[name] = {'low_us': v0, 'high_us': v1, 'signed_diff_us': delta,
                    'high_over_low': v1/v0 if v0 and v1 is not None else None,
                    'direction_vs_source_ub_total': concordance}
            contrasts.append({'low_row_id': low['row_id'], 'high_row_id': high['row_id'],
                'scalar_ub_all_owners_ratio': count1/count0,
                'scalar_ub_max_owner_ratio': high['source_primitive_counts_max_single_owner']['scalar_ub_access'] /
                    low['source_primitive_counts_max_single_owner']['scalar_ub_access'],
                'wire_blocks_ratio': high['wire_blocks_sent']/low['wire_blocks_sent'], 'observed': metrics})
        result.append({'domain_id': digest(json.loads(key)), 'domain': json.loads(key), 'points': points,
            'point_count': len(points), 'design_rank': matrix_rank(features), 'parameter_count': len(features[0]),
            'contrasts': contrasts, 'independent_primitive_prices_identifiable': False,
            'joint_response_use': 'two exact observed domains; descriptive response constraints, no extrapolation',
            'changing_or_uncontrolled_axes': ['source tokens, assignments and active peer pattern change together',
                'captured per-owner PMU reducer and exact compiled source are unrecorded',
                'peer arrival, polling retries and hidden transaction amplification are unmeasured']})
    return result


def main():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.body_defaults import effective_body_declaration
    from mindie_sim.prediction.operator_analysis import target_graphs

    start = time.monotonic(); before = source_identities(); baseline = read(BASELINE)
    programs, joined, source_rows = {}, [], []
    for cid, case_path, context in DOMAINS:
        tick = time.monotonic(); measured = [r for r in baseline['groups'] if r['case_id'] == cid]
        if len(measured) != 4:
            raise ValueError('expected_four_retained_MC2_population_groups')
        raw_case = read(case_path); parsed = parse_case({k:v for k,v in raw_case.items() if k != 'name'})
        geometry = measured[0]['geometry']; q = geometry['tokens_per_sequence']; B = geometry['sequences_per_replica']
        parsed, _ = effective_body_declaration(parsed, 'decode', tokens=q, scope='body')
        sequences = [B] * parsed.runtime.parallel.dp if parsed.runtime.parallel.dp > 1 else B
        graphs = target_graphs(parsed, phase='decode', tokens=q, sequences=sequences, context=context, scope='body')
        all_replica_counts = {str(replica): len(ops) for replica, ops in graphs.items()}
        phases_by = defaultdict(list)
        peer_source = defaultdict(list)
        for op in graphs[0]:
            meta = dict(op.metadata)
            if meta.get('mc2_phase'):
                phases_by[(op.layer, meta['mc2_phase']['kind'])].append(op)
            if meta.get('peer_traffic') and op.layer == min(o.layer for o in graphs[0] if dict(o.metadata).get('mc2_phase')):
                peer_source['declared_rank0_peer_channels'].append({'op_id': op.op_id, 'metadata': meta})
        memo = {}; layer_program = {}
        for key, phases in phases_by.items():
            signature = digest([dict(o.metadata)['mc2_phase'] for o in sorted(phases, key=lambda o: dict(o.metadata)['mc2_phase']['phase'])])
            if signature not in memo:
                program = source_program(phases, parsed.machine.dies[0]); pid = digest(program)
                memo[signature] = pid; programs[pid] = program
            layer_program[key] = memo[signature]
        native_path = ROOT / f'examples/structure/acceptance-20261030-kimi-paged-fia-pmu/{cid}-native-partitions.json'
        native_parts = read(native_path) if native_path.exists() else None
        if native_parts is not None and native_parts['source_identity']['sha256'] != measured[0]['source_identity']['sha256']:
            raise ValueError('native_source_identity_differs')
        ledger_pin = measured[0]['retained_ledger_identity']; ledger_path = ROOT / ledger_pin['path']
        if identity(ledger_path)['sha256'] != ledger_pin['sha256']:
            raise ValueError('retained_ledger_changed')
        ledger = read(ledger_path)
        for observed in measured:
            kind = 'dispatch' if observed['native_operator_type'] == 'MoeDistributeDispatchV3' else 'combine'
            layers = [int(layer) for layer in observed['layer_counts']]
            ids = {layer_program[(layer, kind)] for layer in layers}
            if len(ids) != 1 or any(n != observed['forward_count'] for n in observed['layer_counts'].values()):
                raise ValueError('measured_group_not_homogeneous_declared_layer_program')
            pid = ids.pop(); value = ledger
            for item in observed['retained_group_path'].split('/'):
                value = value[int(item)] if isinstance(value, list) else value[item]
            h = histogram(value)
            if sum(h.values()) != observed['event_count'] or sum(t*n for t,n in h.items())/sum(h.values())/1000 != observed['observed_us']['mean']:
                raise ValueError('retained_hccl_histogram_differs')
            abi = captured_abi(cid, observed, native_parts)
            if native_parts is not None:
                native_part, = [p for p in native_parts['partitions'] if p['native_operator_type'] == observed['native_operator_type'] and p['layer_counts'] == observed['layer_counts']]
                if histogram(native_part) != h:
                    raise ValueError('full_native_histogram_differs')
            joined.append({'row_id': digest([cid, observed['retained_group_path'], pid]),
                'case_id': cid, 'source_identity': observed['source_identity'], 'case_identity': identity(case_path),
                'body_acceptance_identity': observed['body_acceptance_identity'],
                'retained_ledger_identity': ledger_pin, 'retained_group_path': observed['retained_group_path'],
                'geometry': geometry, 'source_context_tokens': context, 'placement': observed['placement'],
                'observed_rank_device': observed['launch_dimensions'].get('Device_id'), 'modeled_rank_replica': 0,
                'source_program_id': pid, 'forward_count': observed['forward_count'], 'layer_ids': layers,
                'layer_counts': observed['layer_counts'], 'attention_kind': observed['attention_kind'],
                'layer_population': observed['layer_population'], 'native_operator_type': observed['native_operator_type'],
                'event_count': observed['event_count'], 'observed_us': observed['observed_us'],
                'duration_ns_counter': sorted(h.items()), 'launch_dimensions': observed['launch_dimensions'],
                'pmu': observed['pmu'], **abi,
                'measurement_owner_reduction': 'not_recorded_by_export; PMU values are not sum over all modeled owners',
                'source_total_divided_by_PMU_as_instruction_rate': False,
                'independent_parameter_prices_identifiable': False})
        source_rows.append({'case_id': cid, 'case_identity': identity(case_path), 'source_identity': measured[0]['source_identity'],
            'observed_forward_count': measured[0]['forward_count'], 'all_declared_replica_graph_counts': all_replica_counts,
            'representative_rank': 0, 'source_force_eplb': raw_case['runtime']['kernels'].get('force_eplb_source'),
            'peer_scope': 'all_declared_peer_graphs_built; only_rank0_has_captured_PMU', **peer_source,
            'unique_program_count': len(memo), 'elapsed_seconds': time.monotonic()-tick})
        print(json.dumps({'case_id': cid, 'programs': len(memo), 'rows': len(measured), 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
        del graphs, phases_by, ledger, native_parts
    features = ['intercept', 'source_tokens', 'source_assignments', 'received_assignments',
                'scalar_ub_access_all_owners', 'scalar_alu_issue_all_owners', 'pipe_barrier_all_owners', 'wire_blocks_sent']
    design = []
    for pid, p in programs.items():
        c = p['source_primitive_counts_all_owners']; g = p['geometry']
        design.append({'source_program_id': pid, 'kind': p['kind'], 'features': [1, g['source_tokens'], g['source_assignments'], g['received_assignments'],
            c.get('scalar_ub_access', 0), c.get('scalar_alu_issue', 0), c.get('pipe_barrier', 0), p['source_sent_framed_blocks']]})
    after = source_identities()
    if before != after:
        raise ValueError('source_metadata_changed_during_join')
    report = {'schema_version': 'mindie-mc2-source-count-constraints/1', 'runtime_source_commit': RUNTIME,
        'source_module_identities': before, 'source_modules_unchanged': True, 'baseline_identity': identity(BASELINE),
        'source_cases': source_rows, 'source_programs': programs, 'rows': joined,
        'design_matrix': {'feature_names': features, 'rows': design, 'numerical_rank': matrix_rank([r['features'] for r in design]),
            'parameter_count': len(features), 'row_count': len(design), 'rank_method': 'column-normalized Gaussian elimination tolerance 1e-10',
            'not_a_causal_identification_claim': True},
        'compatible_response_domains': response_constraints(joined, programs, design),
        'summary': {'source_count': len(source_rows), 'program_count': len(programs), 'joined_population_count': len(joined),
            'events': sum(r['event_count'] for r in joined), 'forward_count': sum(r['observed_forward_count'] for r in source_rows)},
        'interpretation': ['Each row preserves one native/ABI/Block/Mix/topology population; do not pool models or transport domains.',
            'Source calls are conditional source-program work, not established compiled ISA; native binary match is not established.',
            'Source totals and maximum per-owner counts are separate. Unknown exported PMU owner reduction forbids calling their ratio a scalar instruction price.',
            'Successful flag polling is enumerated; absent scalar-wait counters, failed polls, Notify/Wait, SyncAll and transaction amplification remain unknown.',
            'Task Wait Time is not scalar spin wait; elapsed minus maximum pipeline busy is not SyncAll latency.',
            'Packet/frame blocks are source protocol units, not measured network packets or hardware DMA descriptors.',
            'Joint response models may use observable population means within the same explicit domain; training/holdout is reported independently of admission.'],
        'execution': {'elapsed_seconds': time.monotonic()-start, 'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'raw_capture_reads': 0, 'new_cost_predictions': 0, 'engine_executions': 0}}
    path = OUT / 'mc2-source-count-constraints.json'; path.write_text(json.dumps(report, indent=2)+'\n')
    render(report, path.with_suffix('.md'))


def render(report, path):
    lines = ['# MC2 source counts and retained PMU constraints', '',
        f"Four domains, {report['summary']['joined_population_count']} native populations, {report['summary']['events']:,} calls. No raw scans or Engine predictions.", '',
        '| Case / population | Native | Calls | Scalar mean us | MTE2 mean us | MTE3 mean us | Source UB calls total / max owner |',
        '|---|---|---:|---:|---:|---:|---:|']
    for row in report['rows']:
        p = report['source_programs'][row['source_program_id']]
        def metric(name):
            stats = row['pmu'].get(name, {}).get('statistics')
            return f"{stats['mean']:.4f}" if stats else 'unavailable'
        lines.append(f"| {row['case_id']} / {row['attention_kind']} / {row['layer_population']} | {p['kind']} | {row['event_count']} | {metric('aiv_scalar_time(us)')} | {metric('aiv_mte2_time(us)')} | {metric('aiv_mte3_time(us)')} | {p['source_primitive_counts_all_owners'].get('scalar_ub_access',0):g} / {p['source_primitive_counts_max_single_owner'].get('scalar_ub_access',0):g} |")
    lines += ['', *['- '+x for x in report['interpretation']], '',
        f"The retained design has {report['design_matrix']['row_count']} distinct source programs, {report['design_matrix']['parameter_count']} columns and numerical rank {report['design_matrix']['numerical_rank']}. Algebraic rank does not establish independent prices because source families, precision, payload and owner schedules are confounded.",
        '', f"Runtime `{report['runtime_source_commit']}`; JSON keeps complete histograms, native descriptors where retained, layer counts, per-owner inventories, source ranges and exact input identities."]
    lines += ['', '## Within-domain observed responses', '',
        'Each domain has only two token/peer configurations (rank 2 for 8 candidate columns). The figures below are descriptive constraints, not isolated scalar or link prices. Native ABI changes remain attached to each point.', '',
        '| Width / native / population | UB total ratio | UB max-owner ratio | Scalar high/low | MTE2 high/low | MTE3 high/low |',
        '|---|---:|---:|---:|---:|---:|']
    for group in report['compatible_response_domains']:
        domain = group['domain']
        for c in group['contrasts']:
            ratios = [c['observed'][name]['high_over_low'] for name in
                      ('aiv_scalar_time(us)', 'aiv_mte2_time(us)', 'aiv_mte3_time(us)')]
            values = ['unavailable' if v is None else f'{v:.4f}' for v in ratios]
            lines.append(f"| {domain['width']} / {domain['native_operator_type']} / {domain['attention_kind']} / {domain['layer_population']} | {c['scalar_ub_all_owners_ratio']:.4f} | {c['scalar_ub_max_owner_ratio']:.4f} | {' | '.join(values)} |")
    lines += ['', 'Source UB totals rise in all eight comparisons while the maximum single-owner UB count stays fixed. Kimi Combine and V4.1 Dispatch scalar time falls in the larger-token population. These observations rule out treating all-owner UB calls divided by exported scalar busy time as one independently measured scalar rate. V4.1 Layer0 and steady populations retain the same source program but markedly different observed responses; they remain separate.',
        '', 'The copied source-operation details preserve historical field names such as `scalar_source_id_reads_unpriced` verbatim. Those names are provenance, not a statement that the current runtime does not charge the operation: the current `primitive_services` owner inventory is exported separately, and this report executes no cost model.',
        '', 'Qwen35 response parameters are outside this four-domain matrix. Their complete-population and typed-chain check remains recorded in `examples/structure/acceptance-20261030-qwen35-complete-observed-service/complete-service-cross-review.json` (421 checks, zero failures); FIA/GDN source-symbol applicability remains explicit and strict cohort counts were not changed.']
    path.write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    main()
