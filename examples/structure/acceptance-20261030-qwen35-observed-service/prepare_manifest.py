"""Attach source-authored Qwen35 service cases to unchanged observed populations.

[Role] Validate retained native ABI populations and mount explicit Sim cases.
[Invariants] Never fit parameters, copy cases, change measured boundaries, or
  infer evaluation independence from a parameter name. Preserve controller fixes.
[Timeouts & Locks] Bounded saved JSON only; no workers, raw CSV reads or locks.
[Side-Effect Policy] Write a small preflight and, when supplied, replay manifest.
"""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parent
ROOT = EXAMPLES.parents[1]
BASE = EXAMPLES / 'acceptance-20261030-qwen35-mc2-tp-bf71bd7d/decode-forward-qwen35-mc2-tp-cases.json'
PARTITIONS = EXAMPLES / 'acceptance-20261030-qwen35-source-complete/native-partitions/native-partition-receipt.json'


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata_requires_streaming:' + str(path))
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'size_bytes': path.stat().st_size,
            'sha256': sha256(path.read_bytes()).hexdigest()}


def pinned(raw):
    path = Path(raw['path'])
    if not path.is_absolute():
        path = ROOT / path
    if identity(path)['sha256'] != raw['sha256']:
        raise ValueError('retained_pin_changed:' + str(path))
    return read(path)


def geometry(value):
    return tuple(value.get(k) for k in ('query_rows', 'sequences_per_replica', 'tokens_per_sequence'))


def frame_keys(observed, wanted):
    # Controller aliases change retained completion, not the norm/head occurrence.
    return [(r['start_ns'], r['head_start_ns'], r['head_end_ns'], r['device_id'])
            for r in observed['forwards'] if geometry(r['geometry']) == wanted]


def prepare(overrides=None, runtime_commit=None):
    manifest = read(BASE)
    partitions = {r['case_id']: r for r in read(PARTITIONS)['cases']}
    rows, evidence = [], []
    for original in manifest['cases']:
        cid = original['case_id']
        extraction = read(original['extraction_path'])
        native = pinned(partitions[cid]['artifact_identity'])
        old_extraction = pinned(native['body_acceptance_identity'])
        source_sha = original['source']['sha256']
        if not all(x['source_identity']['sha256'] == source_sha for x in
                   (extraction, native, old_extraction)):
            raise ValueError('source_population_mismatch:' + cid)
        selected = max(extraction['geometry_groups'], key=lambda x: x['body_forward_span_ms']['count'])
        selected_geometry = geometry(selected['geometry'])
        if selected_geometry != geometry(native['geometry']):
            raise ValueError('native_geometry_mismatch:' + cid)
        if selected['body_forward_span_ms']['count'] != native['forward_count']:
            raise ValueError('native_forward_population_mismatch:' + cid)
        if frame_keys(extraction, selected_geometry) != frame_keys(old_extraction, selected_geometry):
            raise ValueError('controller_refresh_changed_native_occurrences:' + cid)
        totals = Counter()
        abi_groups = []
        for part in native['partitions']:
            n = sum(count for _, count in part['duration_ns_counter'])
            if n != part['observed_us']['count']:
                raise ValueError('native_histogram_population:' + cid)
            totals[part['native_operator_type']] += n
            abi_groups.append({'native_operator_type': part['native_operator_type'],
                'native_abi_sha256': sha256(json.dumps(part['native_abi'], sort_keys=True,
                    separators=(',', ':')).encode()).hexdigest(),
                'declared_roles': part['declared_roles'], 'event_count': n,
                'input_dtypes': [slot[1] for slot in part['native_abi'][2]],
                'output_dtypes': [slot[1] for slot in part['native_abi'][3]]})
        if dict(totals) != {k: v for k, v in native['native_family_counts'].items() if v}:
            raise ValueError('native_family_population:' + cid)
        entry = {'case_id': cid, 'source_identity': original['source'],
            'controller_corrected_extraction_identity': identity(original['extraction_path']),
            'retained_native_partition_identity': partitions[cid]['artifact_identity'],
            'original_native_body_identity': native['body_acceptance_identity'],
            'same_norm_and_head_occurrences': True,
            'source_forward_count': len(extraction['forwards']),
            'main_forward_count': native['forward_count'], 'geometry': selected['geometry'],
            'conditional_context_tokens': original['geometry']['context_tokens'],
            'native_family_counts': dict(totals), 'native_abi_groups': abi_groups,
            'parameter_fit_performed_here': False}
        if overrides:
            override = overrides[cid]
            case_path = Path(override['path'])
            case = read(case_path)
            if override.get('sha256') and identity(case_path)['sha256'] != override['sha256']:
                raise ValueError('new_case_pin_changed:' + cid)
            rules = case['runtime'].get('kernels', {}).get('service_regimes', [])
            if not rules:
                raise ValueError('source_service_rules_missing:' + cid)
            from mindie_sim.prediction.structure import parse_case
            declared = parse_case(case)
            if declared.runtime.parallel.tp != 4 or declared.runtime.parallel.ep != 4:
                raise ValueError('source_placement_changed:' + cid)
            row = deepcopy(original)
            row.update(sim_case_path=str(case_path.resolve()), model_declaration=identity(case_path),
                       variant_id='qwen35-source-observed-service-' + runtime_commit[:8])
            row['prior_source_case_identity'] = original['model_declaration']
            row['replay_input_pins']['case'] = row['model_declaration']
            row['runtime_refresh'] = {
                'prior_input_manifest': identity(BASE),
                'prior_case_identity': original['model_declaration'],
                'case_bytes_changed': row['model_declaration']['sha256'] != original['model_declaration']['sha256'],
                'explicit_case_override': True, 'retained_extraction_bytes_unchanged': True}
            row['baseline_reference'] = identity(BASE.with_name('decode-forward-qwen35-mc2-tp-replay.json'))
            # Only an explicit provider evaluation label is carried. No label is
            # manufactured from whether a rule happens to mention this source.
            if override.get('calibration_evidence') is not None:
                row['calibration_evidence'] = override['calibration_evidence']
                row['calibration_origin'] = 'source_declared_operator_service'
            entry['source_case_identity'] = row['model_declaration']
            entry['service_rule_count'] = len(rules)
            rows.append(row)
        evidence.append(entry)
    preflight = {'schema_version': 'mindie-qwen35-observed-service-inputs/1',
        'status': 'ready_for_declared_runtime' if overrides else 'awaiting_source_authored_cases',
        'prior_manifest_identity': identity(BASE), 'native_receipt_identity': identity(PARTITIONS),
        'cases': evidence, 'raw_event_reads': 0, 'new_predictions': 0,
        'parameter_fits': 0, 'main_forwards': sum(x['main_forward_count'] for x in evidence),
        'all_source_forwards': sum(x['source_forward_count'] for x in evidence)}
    if rows:
        manifest['cases'] = rows
        manifest['variant_id'] = rows[0]['variant_id']
        manifest['runtime_plan'] = {'source_commit': runtime_commit}
        manifest['baseline_reference'] = identity(BASE)
        manifest.pop('declaration_source_commits', None)
        manifest['case_source_policy'] = 'Source-authored cases are read unchanged; no parameter fit here.'
        (HERE / 'decode-forward-service-cases.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (HERE / 'input-preflight.json').write_text(json.dumps(preflight, indent=2) + '\n')
    return preflight


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-overrides')
    parser.add_argument('--runtime-commit')
    args = parser.parse_args()
    if bool(args.case_overrides) != bool(args.runtime_commit):
        parser.error('--case-overrides and --runtime-commit must be supplied together')
    result = prepare(read(args.case_overrides) if args.case_overrides else None, args.runtime_commit)
    print(json.dumps({k: result[k] for k in ('status', 'main_forwards', 'all_source_forwards')}))
