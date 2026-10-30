"""Bind the complete Q397 matrix/GDN domains after shared BF16 correction.

[Role] Use full captured ABI plus accepted layer topology for source-role rules.
[Invariants] A same-shaped native bucket is admitted only when every retained
  layer has a unique compatible operator and the full physical population agrees.
[Timeouts & Locks] Bounded metadata graphs only; no raw scan or prediction.
[Side-Effect Policy] New arms preserve the preceding GQA/GMM/HCOM results.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen_a3_service_cases import physical_ops, read, write, identity
from build_qwen35_complete_service_cases import _physical_match
from build_qwen35_highconc_service import match_ids, REVISION
from build_qwen397_highconc_service import pooled
from build_glm78_native_service_cases import descriptor, freeze
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure_contracts import predicted_contract

ROOT = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement'
OUT = ROOT / 'qwen397-a3-matrix-gdn'


def build():
    manifest = read(ROOT / 'qwen397-a3/decode-forward-cases.json'); evidence = []
    for row in manifest['cases']:
        prior = identity(row['sim_case_path']); raw = read(prior['path'])
        geometry = row['replay_input_pins']['primary_geometry']
        path = ROOT / 'qwen397-a3/native-partitions' / (row['case_id'] + '-native-partitions.json')
        native = read(path); F = native['forward_count']
        case, before = physical_ops(raw, geometry)
        # Resolve the original public catalog first; the stored explicit quant
        # fields preserve every other operand category and its source metadata.
        quant = case.model.quant.to_dict()
        quant.setdefault('category_overrides', {})['shared_expert'] = {'weight_format': 'bf16', 'activation_format': 'bf16'}
        raw['model']['quant'] = quant
        case, ops = physical_ops(raw, geometry); by_layer = defaultdict(list)
        for op in ops:
            by_layer[op.layer].append(op)
        buckets, excluded = {}, []
        for index, part in enumerate(native['partitions']):
            if part['native_operator_type'] not in ('MatMulV2', 'RecurrentGatedDeltaRule'):
                continue
            observed = observed_contract(descriptor(part['native_abi']))
            selected = []
            for layer, count in part['layer_counts'].items():
                matches = [op for op in by_layer[int(layer)]
                           if predicted_contract(op.to_dict(include_work=False)) == observed]
                if len(matches) != 1 or count != F:
                    selected = []; break
                selected.extend(matches)
            if not selected:
                excluded.append({'partition_index': index, 'native_operator_type': part['native_operator_type'],
                    'native_abi': part['native_abi'], 'layer_counts': part['layer_counts'],
                    'observed_us': part['observed_us'], 'reason': 'fresh_physical_contract_not_unique_in_all_retained_layers'})
                continue
            match = _physical_match(case, selected[0])
            if any(_physical_match(case, op) != match for op in selected):
                raise ValueError('retained_native_histogram_covers_heterogeneous_programs')
            key = json.dumps([part['native_operator_type'], match], sort_keys=True)
            bucket = buckets.setdefault(key, {'match': match, 'parts': [], 'indices': [], 'targets': []})
            bucket['parts'].append(part); bucket['indices'].append(index); bucket['targets'].extend(selected)
        additions = []
        for bucket in buckets.values():
            parts = bucket['parts']; population = pooled(parts); targets = bucket['targets']
            ids = {op.op_id for op in targets}
            if len(ids) != len(targets) or population['count'] != F * len(ids):
                raise ValueError('native_occurrences_not_one_per_declared_role')
            kind = parts[0]['native_operator_type']; selector = bucket['match']
            rule = {'id': 'q397-complete-' + sha256(json.dumps(selector, sort_keys=True).encode()).hexdigest()[:16],
                'match': selector, 'response': {'fixed_us': population['mean_us']},
                'execution': {'kind': 'joint_native', 'native_kernel': kind, 'resource': 'joint_native_a3', 'reference_rate': 1e9},
                'provenance': {'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'source_identity': row['source'], 'native_partition_identity': identity(path),
                    'native_operator_type': kind, 'native_partition_indices': bucket['indices'],
                    'native_abi': parts[0]['native_abi'], 'active_contract': predicted_contract(targets[0].to_dict(include_work=False)),
                    'observed_population': population, 'expected_rule_hits': len(ids), 'forward_count': F,
                    'body_residual_used': False, 'strict_contract_admission_changed': False,
                    'basis': 'complete_retained_ABI_then_unique_active_contract_in_every_accepted_layer'}}
            if match_ids(rule, case, ops) != ids:
                raise ValueError('incomplete_physical_selector_population')
            for old in raw['runtime']['kernels']['service_regimes']:
                if match_ids(old, case, ops) & ids:
                    raise ValueError('native_service_overlap:' + old['id'])
            raw['runtime']['kernels']['service_regimes'].append(rule); additions.append(rule)
        cal = {'evaluation_relation': 'in_sample', 'baseline_case_identity': prior,
               'prior_evidence_reference': {'case_identity': prior, 'json_pointer': '/runtime/metadata/calibration_evidence'},
               'native_partition_identity': identity(path), 'body_residual_used': False,
               'precision_correction': 'shared_expert BF16 operands observed; GQA output mismatch remains excluded'}
        raw['runtime']['metadata'].update(calibration_origin='observed', calibration_evidence=cal)
        target = OUT / 'cases' / (row['case_id'] + '-matrix-gdn.json'); write(target, raw)
        row.update(sim_case_path=str(target), model_declaration=identity(target), calibration_origin='observed',
                   calibration_evidence=cal, variant_id='q397-matrix-gdn-' + REVISION[:8])
        row['replay_input_pins']['case'] = identity(target)
        evidence.append({'case_id': row['case_id'], 'case_identity': identity(target), 'baseline_case_identity': prior,
            'native_partition_identity': identity(path), 'source_identity': row['source'], 'geometry': geometry,
            'forward_count': F, 'new_rules': additions, 'exclusions': excluded,
            'removed_shared_quantizers': [o.op_id for o in before if o.op_id not in {x.op_id for x in ops}]})
    manifest.update(variant_id='q397-matrix-gdn-' + REVISION[:8], runtime_source_commit=REVISION)
    write(OUT / 'decode-forward-cases.json', manifest)
    write(OUT / 'observed-populations.json', {'cases': evidence, 'producer_identity': identity(__file__),
                                           'new_raw_scans': 0, 'new_cost_predictions': 0})
    print(json.dumps([{'case_id': e['case_id'], 'new_rules': len(e['new_rules']),
        'new_calls_per_forward': sum(r['provenance']['expected_rule_hits'] for r in e['new_rules']),
        'excluded_calls_per_forward': sum(x['observed_us']['count'] for x in e['exclusions']) / e['forward_count']} for e in evidence]))


if __name__ == '__main__':
    build()
