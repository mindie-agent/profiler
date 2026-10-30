"""Generate observed physical-service regimes from retained operator populations.

[Role] Reuse source-bound Sim programs and retained per-call observations.
[Invariants] Parameters use observed activity/count only, never prediction or
  whole-forward residuals. A fused group receives one inclusive response. Shape,
  dtype and implementation selectors carry no layer, case or operation IDs.
[Timeouts & Locks] Serial bounded metadata; no raw event scans, devices or locks.
[Side-Effect Policy] Write independent cases, manifests and provenance locally.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
ROOT = EXAMPLES.parents[1]
sys.path.insert(0, str(EXAMPLES))
from mindie_profiler.sources_db import sha256_file
from mindie_sim.structure import export_structure
from mindie_sim.prediction.structure import parse_case

INPUTS = {
    'kimi': ('acceptance-20261030-kimi-source-complete-operators/full-matrix-canonical/body-operator-family-scoreboard.json',
             'acceptance-20261030-kimi-native-references-5ec8843a/kimi-native-reference-scoreboard.json'),
    'v41': ('acceptance-20261030-v41-composed-operators-40e4300e/body-operator-family-scoreboard.json',
            'acceptance-20261030-v41-composed-native-5ec8843a/v41-complete-reference-scoreboard.json'),
}
PRIORITY = ['a5_kimi_tp8_e16_bf16_c32_p4k', 'a5_kimi_tp8_e16_bf16_c32_p16k',
            'a5_v41_fp8_tp1_dp8_ep8_tpot30ms_c64', 'a5_v41_fp8_tp1_dp8_ep8_c128_p2k']


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata_too_large:' + str(path))
    return json.loads(path.read_text())


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256_file(path), 'size_bytes': path.stat().st_size}


def pinned(raw):
    path = resolve(raw['path'])
    if sha256_file(path) != raw['sha256']:
        raise ValueError('retained_identity_changed:' + str(path))
    return read(path)


def key(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def physical_match(node, hardware, compute_dtype):
    op = node['operator']; meta = op.get('metadata', {})
    group = meta.get('device_kernel_group')
    match = {'hardware': hardware, 'recipe': op['recipe'], 'family': op['family'],
             'dtype': op.get('dtype') or compute_dtype}
    if group:
        match['kernel'] = group['kernel']
    elif meta.get('kernel') or meta.get('kernel_name'):
        match['kernel'] = meta.get('kernel', meta.get('kernel_name'))
    for path in ('implementation', 'native_kind', 'compute_format', 'activation_format',
                 'weight_format', 'output_format', 'matrix_groups'):
        value = meta.get(path)
        if isinstance(value, (str, int, float, bool)):
            match['metadata.' + path] = value
    # A compression ratio is a physical domain, unlike a layer index.
    if 'mqsmla_geometry' in meta:
        match['metadata.mqsmla_geometry.ratio'] = meta['mqsmla_geometry']['ratio']
        match['metadata.mqsmla_geometry.topk'] = meta['mqsmla_geometry']['topk']
    if 'fusion_boundary' in meta:
        match['metadata.fusion_boundary.native.native_kind'] = meta['fusion_boundary']['native']['native_kind']
    shape = op.get('local_shape', [])
    coordinates = {f'd{i}': {'path': f'local_shape.{i}'} for i in range(len(shape))}
    domain = {f'd{i}': {'min': size, 'max': size} for i, size in enumerate(shape)}
    return match, coordinates, domain


def generate(row, family, index, native_case, *, case_directory='cases-complete-population'):
    started = time.monotonic()
    old_case = resolve(row['sim_case_path']); case = read(old_case)
    parsed = parse_case(case)
    observed = read(resolve(row['extraction_path']))
    main = max(observed['geometry_groups'], key=lambda g: g['body_forward_span_ms']['count'])
    geometry = main['geometry']; forwards = main['body_forward_span_ms']['count']
    source_hash = row['source']['sha256']
    if observed['source_identity']['sha256'] != source_hash or index['source_identity']['sha256'] != source_hash:
        raise ValueError('body_operator_source_mismatch')
    if index['forward_count'] != forwards or native_case['forward_count'] != forwards:
        raise ValueError('body_operator_population_mismatch')
    manifest = export_structure(case, phase='decode', tokens=geometry['tokens_per_sequence'],
        sequences=geometry['sequences_per_replica'], context=row['geometry']['context_tokens'],
        scope='body', replicas=[0])
    nodes = {n['node_id']: n for n in manifest['nodes'] + manifest['resource_operators']}
    subgraphs = {g['subgraph_id']: g for g in manifest['subgraphs']}
    detail = pinned(index['case_detail_identity'])['cases'][0]
    mapping = pinned(index['mapping_identity'])
    comparison = pinned(index['comparison_identity'])
    eligible = {c['cohort_id'] for w in comparison['windows'] for c in w['cohorts'] if c['status'] == 'compared'}
    rules, omissions = {}, []

    def add(target_ids, stats, origin, *, native, role, source_boundary, correspondence=None):
        selected = []
        for target_id in target_ids:
            if target_id in subgraphs:
                target_ids2 = (subgraphs[target_id].get('resource_boundary') or {}).get('operator_ids', [])
                selected.extend(nodes[i] for i in target_ids2 if i in nodes)
            elif target_id in nodes:
                selected.append(nodes[target_id])
        if not selected:
            omissions.append({'native': native, 'role': role, 'reason': 'fresh_target_missing', 'origin': origin})
            return
        group_ids = {n['operator'].get('metadata', {}).get('device_kernel_group', {}).get('id') for n in selected}
        if len(selected) > 1 and len(group_ids) == 1 and None not in group_ids:
            selected = [n for n in selected if n['operator']['metadata']['device_kernel_group'].get('entry')]
        elif len(selected) > 1 and source_boundary != 'cohort':
            omissions.append({'native': native, 'role': role, 'reason': 'no_single_native_boundary_for_unfused_program_set', 'origin': origin})
            return
        seen = set()
        for node in selected:
            if node.get('event_matchable') is False:
                continue
            match, coords, domain = physical_match(node, parsed.machine.hardware_key or parsed.machine.sku,
                                                    parsed.model.compute_dtype)
            signature = key([match, coords, domain])
            if signature in seen:
                continue
            seen.add(signature)
            record = rules.setdefault(signature, {'match': match, 'coordinates': coords, 'domain': domain,
                'samples': [], 'count': 0, 'observed_sum_us': 0., 'native_types': set(), 'target_ids': set(),
                'strict_cohort': source_boundary == 'cohort'})
            if source_boundary != 'cohort' and record['strict_cohort']:
                continue
            # The same retained population can be present in native and cohort
            # receipts. Calibration counts it once for this physical selector.
            sample_key = key([native, role, origin])
            if any(x['sample_key'] == sample_key for x in record['samples']):
                continue
            record['count'] += stats['count']; record['observed_sum_us'] += stats['mean'] * stats['count']
            record['native_types'].add(native); record['target_ids'].add(node['node_id'])
            record['samples'].append({'sample_key': sample_key, 'origin': origin, 'native_operator_type': native,
                'declared_role': role, 'observed_us': stats, 'boundary': source_boundary,
                'source_correspondence': correspondence})

    # Strict cohorts already retain the complete observation and candidate set.
    # No previous prediction or residual is consulted to choose parameters.
    for window in mapping['windows']:
        for cohort in window['cohorts']:
            if cohort['cohort_id'] not in eligible:
                continue
            targets = cohort['target_ids']
            add(targets, {'count': cohort['complete_event_count'], 'mean': cohort['duration_ns']['mean']/1000,
                'p50': cohort['duration_ns'].get('p50', 0)/1000},
                {'receipt': index['mapping_identity'], 'cohort_id': cohort['cohort_id']},
                native=cohort['native_operator_type'], role='|'.join(mapping['conditional_role_by_cohort_id'][cohort['cohort_id']]),
                source_boundary='cohort')
    # Independent complete native observations include conditional work (e.g.
    # unknown valid rows). Fitting a service response does not repair that ABI gap.
    native_roles = set()
    for group in native_case['groups']:
        native_roles.add((group['native_operator_type'], group.get('declared_role')))
        buckets = group.get('program_buckets', [group])
        for bucket in buckets:
            targets = bucket.get('representative_target_ids', [])
            # One observation group spanning several physical programs does not
            # provide separate timing per program; keep this limitation visible.
            add(targets, group['observed_us'], {'group_id': group.get('group_id'), 'native_reference_case': native_case['case_id']},
                native=group['native_operator_type'], role=group.get('declared_role'), source_boundary='retained_native_group',
                correspondence=group.get('source_correspondence'))
    for f in detail['families']:
        if f['native_operator_type'] == 'GroupedMatmul':
            if (f['native_operator_type'], f['declared_role']) in native_roles:
                continue
            for group in f.get('conditional_source_role_references', []):
                targets = group.get('representative_target_ids', [])
                add(targets, group['observed_us'], {'group_id': group.get('group_id'), 'canonical': index['case_detail_identity']},
                    native=f['native_operator_type'], role=f['declared_role'], source_boundary='retained_native_group',
                    correspondence=group.get('source_correspondence'))
        if f['native_operator_type'].startswith('hcom_'):
            kind = ('allgather' if 'allGather' in f['native_operator_type'] else
                    'reduce_scatter' if 'reduceScatter' in f['native_operator_type'] else
                    'allreduce' if 'allReduce' in f['native_operator_type'] else None)
            block = 'attention' if f['declared_role'].startswith('attention') else 'ffn'
            targets = [n['node_id'] for n in nodes.values() if n['family'] == kind and n.get('block') == block]
            if targets and len(targets) * forwards == f['observed_us']['count']:
                add(targets, f['observed_us'], {'canonical': index['case_detail_identity'], 'family': [f['native_operator_type'], f['declared_role']]},
                    native=f['native_operator_type'], role=f['declared_role'], source_boundary='cohort',
                    correspondence={'basis': 'whole_body_collective_count_and_structural_block',
                        'measured_algorithm': None, 'peer_wait_separated': False,
                        'pure_link_rate_identifiable': False})
            else:
                omissions.append({'native': f['native_operator_type'], 'role': f['declared_role'],
                    'reason': 'collective_population_or_structural_role_unresolved',
                    'observed_calls': f['observed_us']['count'], 'declared_candidates': len(targets)})
    declarations = []
    expected = Counter()
    for node in nodes.values():
        meta = node['operator'].get('metadata', {})
        group = meta.get('device_kernel_group')
        if node.get('event_matchable') is False or (group and not group.get('entry')):
            continue
        expected[key(physical_match(node, parsed.machine.hardware_key or parsed.machine.sku,
                                    parsed.model.compute_dtype))] += 1
    for signature, entry in rules.items():
        declarations.append({'id': 'retained-service-' + sha256(signature.encode()).hexdigest()[:16],
            **{k: entry[k] for k in ['match', 'coordinates', 'domain']},
            'response': {'fixed_us': entry['observed_sum_us']/entry['count']},
            'provenance': {'basis': 'observed_operator_service_mean', 'evaluation_relation': 'in_sample',
                'fit_source_identity': row['source'], 'evaluation_source_identity': row['source'],
                'measurement_population': entry['count'], 'native_operator_types': sorted(entry['native_types']),
                'retained_observations': entry['samples'], 'whole_body_residual_used': False,
                'prediction_values_used': False, 'scope': 'inclusive_native_or_declared_kernel_service',
                'expected_invocations_per_representative_replica': expected[signature],
                'expected_invocations_full_dp_cohort': expected[signature] * parsed.runtime.parallel.dp,
                'outside_exact_shape_domain': 'analytical', 'historically_examined': True}})
    case['runtime'].setdefault('kernels', {})['service_regimes'] = declarations
    evidence = {'evaluation_relation': 'in_sample', 'fit_source_identity': row['source'],
        'evaluation_source_identity': row['source'], 'source_manifest_case_id': row['case_id'],
        'retained_operator_receipt': index['case_detail_identity'], 'parameter_source': 'per_call_observations_only',
        'body_residual_used': False, 'contract_gaps_remain': omissions, 'generalization_claim': False}
    case['runtime'].setdefault('metadata', {}).update(calibration_origin='retained_operator_service_in_sample', calibration_evidence=evidence)
    out = HERE/case_directory/f"{row['case_id']}.json"; out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(case, indent=2) + '\n')
    replay = {**deepcopy(row), 'variant_id': 'observable-service-2f48346b', 'sim_case_path': str(out),
        'model_declaration': identity(out), 'calibration_origin': 'retained_operator_service_in_sample',
        'calibration_evidence': evidence, 'original_case_identity': identity(old_case)}
    summary = {'case_id': row['case_id'], 'case_identity': identity(out), 'original_case_identity': identity(old_case),
        'source_identity': row['source'], 'extraction_identity': identity(resolve(row['extraction_path'])),
        'forward_count': forwards, 'geometry': geometry, 'rule_count': len(declarations),
        'rule_native_counts': dict(Counter(t for r in rules.values() for t in r['native_types'])),
        'rules': [{'id': r['id'], 'response': r['response'], 'match': r['match'], 'domain': r['domain']} for r in declarations],
        'omissions': omissions, 'elapsed_seconds': time.monotonic()-started,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'raw_event_reads': 0, 'predictions_run': 0, 'full_peer_graph_binding_preserved': True,
        'serialized_replica_projection': [0]}
    (out.parent/f"{row['case_id']}-generation.json").write_text(json.dumps(summary, indent=2)+'\n')
    return replay, summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case-id', action='append')
    parser.add_argument('--exclude-priority', action='store_true')
    parser.add_argument('--suffix', default='complete')
    parser.add_argument('--case-directory', default='cases-complete-population');args=parser.parse_args()
    all_rows=[];summaries=[]
    for family in ('kimi','v41'):
        source_manifest=EXAMPLES/f'acceptance-20261030-runtime40e4300e/decode-forward-{family}-controller-cases.json'
        source=read(source_manifest)
        operator=read(EXAMPLES/INPUTS[family][0]);native=read(EXAMPLES/INPUTS[family][1])
        by_id={c['source_case_id']:c for c in operator['cases']};native_by_id={c['case_id']:c for c in native['cases']}
        rows=sorted(source['cases'],key=lambda r:(PRIORITY.index(r['case_id']) if r['case_id'] in PRIORITY else 99,r['case_id']))
        for row in rows:
            if args.case_id and row['case_id'] not in args.case_id:continue
            if args.exclude_priority and row['case_id'] in PRIORITY:continue
            replay,summary=generate(row,family,by_id[row['case_id']],native_by_id[row['case_id']],case_directory=args.case_directory)
            all_rows.append(replay);summaries.append(summary)
            print(json.dumps({'case_id':row['case_id'],'rules':summary['rule_count'],'rss_mib':summary['peak_rss_bytes']/1024**2}),flush=True)
    all_rows.sort(key=lambda r:PRIORITY.index(r['case_id']) if r['case_id'] in PRIORITY else 99)
    manifests=[(args.suffix,all_rows)]
    if args.suffix == 'all' and not args.exclude_priority:manifests.append(('priority',[r for r in all_rows if r['case_id'] in PRIORITY]))
    for name,rows in manifests:
        (HERE/f'decode-forward-{name}-cases.json').write_text(json.dumps({'schema_version':'mindie-decode-forward-replay/1',
            'variant_id':'observable-service-2f48346b','cases':rows},indent=2)+'\n')
    (HERE/f'generation-{args.suffix}-summary.json').write_text(json.dumps({'schema_version':'mindie-observed-service-case-generation/1',
        'cases':summaries,'raw_event_reads':0,'predictions_run':0,'generator_identity':identity(__file__)},indent=2)+'\n')


if __name__=='__main__':main()
