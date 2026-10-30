"""Build observable kernel-service declarations from retained profiling groups.

[Role] Reuse source-pinned whole-call populations to declare physical regimes.
[Invariants] No body residual enters a parameter; inclusive calls are counted
  once. Physical shapes/recipes select rules, never layer, model or operator IDs.
[Timeouts & Locks] Bounded local JSON; metadata graph construction only.
[Side-Effect Policy] Write independent cases/manifests; no raw scan or device.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FIXED = Path('/tmp/mindie-sim-cohort-wave6-20261029').resolve()
OUT = ROOT / 'acceptance-20261030-service-qwen-a3'
EVIDENCE = ROOT / 'acceptance-20261030-calibration-policy/glm-qwen-observed-service-inputs.json'
BASE = ROOT / 'acceptance-20261030-runtime40e4300e/decode-forward-qwen-hccl-controller-cases.json'


def read(path):
    return json.loads(Path(path).read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def physical_ops(raw, geometry):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.prediction.body_defaults import effective_body_declaration
    from mindie_sim.prediction.program import RecipeBook
    case = parse_case({k: v for k, v in raw.items() if k != 'name'})
    case, _ = effective_body_declaration(case, 'decode', tokens=geometry['tokens_per_sequence'], scope='body')
    graphs = target_graphs(case, phase='decode', tokens=geometry['tokens_per_sequence'],
                          context=geometry['context_tokens'], sequences=geometry['sequences_per_replica'], scope='body')
    ops = RecipeBook.from_mapping(case.runtime.kernels).expand(graphs[0])
    return case, ops


def qwen_rules(raw, geometry, evidence):
    case, ops = physical_ops(raw, geometry)
    native_to_recipe = {'CausalConv1d': 'ascend_causal_conv1d_update',
                        'RecurrentGatedDeltaRule': 'ascend_recurrent_gdn_fp32_state',
                        'hcom_allReduce_': 'hccl_entry'}
    rules, coverage = [], []
    for measured in evidence['operators']:
        native = measured['native_operator_type']
        recipe = native_to_recipe[native]
        selected = [op for op in ops if op.recipe == recipe]
        observed = measured['observed']
        expected = observed['count'] / evidence['body_count']
        if not selected or len(selected) != expected:
            raise ValueError(f'physical_population_differs:{native}:{len(selected)}:{expected}')
        match = {'hardware': case.machine.hardware_key or case.machine.sku,
                 'recipe': recipe, 'phase': 'decode'}
        physical = []
        for op in selected:
            meta = dict(op.metadata)
            if recipe == 'hccl_entry':
                selection = meta['hccl_selection']
                axes = {'kernel': meta['device_kernel_group']['kernel'],
                        **{f'metadata.hccl_selection.{k}': selection[k]
                           for k in ('ranks', 'payload_bytes', 'block_limit', 'collective', 'template')}}
            else:
                axes = {'dtype': op.dtype,
                        **{f'local_shape.{i}': n for i, n in enumerate(op.local_shape)}}
                keys = (('kernel_width', 'state_history_slots', 'cache_index_row_stride')
                        if native == 'CausalConv1d' else ('key_heads', 'heads', 'dk', 'dv', 'state_dtype'))
                axes.update({f'metadata.{k}': meta[k] for k in keys})
            physical.append(axes)
        if any(axes != physical[0] for axes in physical):
            raise ValueError(f'heterogeneous_population_requires_retained_partitions:{native}')
        match.update(physical[0])
        provenance = {'calibration_origin': 'in_sample', 'source_identity': evidence['source_identity'],
                      'actual_identity': evidence['actual_identity'], 'evidence_identity': identity(EVIDENCE),
                      'native_operator_type': native, 'observed': observed,
                      'parameter_statistic': 'whole_population_arithmetic_mean_us',
                      'forward_count': evidence['body_count'], 'expected_calls_per_forward': expected,
                      'response_boundary': 'inclusive_whole_native_call',
                      'body_residual_used': False, 'pure_link_bandwidth_identified': False,
                      'contract_admission_changed': False}
        rule_id = native.lower() + '-physical-' + str(geometry['query_rows'])
        rules.append({'id': rule_id, 'match': match,
                      'response': {'fixed_us': observed['mean_us']}, 'provenance': provenance})
        coverage.append({'rule_id': rule_id, 'native_operator_type': native,
                         'expected_calls_per_forward': expected, 'declared_physical_matches': len(selected),
                         'observed_count': observed['count'], 'mean_us': observed['mean_us'],
                         'p50_us': observed['p50_us']})
    return rules, coverage


def build_qwen():
    base, measurements = read(BASE), read(EVIDENCE)
    source_rows = {r['case_id']: r for r in base['cases']}
    observed = {r['case_id']: r for r in measurements['cases']}
    rows, coverage = [], []
    for concurrency in (96, 12, 1):
        source_id = f'qwen36-a5-tp2-c{concurrency}'
        row = deepcopy(source_rows[source_id])
        retained_case = Path(row['sim_case_path'])
        raw = read(retained_case)
        geo = row['replay_input_pins']['primary_geometry']
        if observed[source_id]['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('observed_service_source_mismatch')
        rules, populations = qwen_rules(raw, geo, observed[source_id])
        kernels = raw['runtime'].setdefault('kernels', {})
        if kernels.get('service_regimes'):
            raise ValueError('baseline_already_has_service_regimes')
        kernels['service_regimes'] = rules
        metadata = raw['runtime'].setdefault('metadata', {})
        metadata['calibration_origin'] = 'in_sample'
        metadata['calibration_evidence'] = {
            'source': identity(EVIDENCE), 'response_boundary': 'inclusive_whole_native_call',
            'parameter_statistic': 'whole_population_arithmetic_mean_us',
            'model_body_residual_used': False, 'contract_admission_changed': False,
            'limitations': ['completion lower bounds preserve larger analytic work costs',
                            'HCOM elapsed includes protocol/peer wait and is not pure-link identification']}
        target = OUT / 'cases' / f'{source_id}-observable-service.json'
        write(target, raw)
        row['sim_case_path'] = str(target)
        row['variant_id'] = 'observable-native-service-2f48346b'
        row['baseline_case_identity'] = identity(retained_case)
        row['model_declaration'] = identity(target)
        row['replay_input_pins']['case'] = identity(target)
        row['calibration_origin'] = 'in_sample'
        row['calibration_evidence'] = metadata['calibration_evidence']
        rows.append(row)
        coverage.append({'case_id': source_id, 'geometry': geo, 'rules': populations,
                         'not_parameterized': ['mixed TensorMove population has no sole-copy role partition',
                                               'other families retain the declared analytic/source programs']})
    manifest = {'schema_version': base['schema_version'], 'variant_id': 'observable-native-service-2f48346b',
                'baseline_reference': identity(BASE), 'not_new_live_collection': True,
                'parameter_policy': 'per-native complete-population mean; no Body fitting or per-layer identifiers',
                'runtime_source_commit': '2f48346b', 'cases': rows}
    write(OUT / 'decode-forward-qwen-service-cases.json', manifest)
    write(OUT / 'qwen-service-coverage.json', {'evidence_identity': identity(EVIDENCE), 'cases': coverage})
    return manifest


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps({'cases': len(build_qwen()['cases']), 'output': str(OUT)}))
