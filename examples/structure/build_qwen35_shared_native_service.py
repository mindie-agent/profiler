"""Separate same-shaped router and shared FFN calls using retained topology.

[Role] Correct the independent shared-expert precision and bind complete roles.
[Invariants] Native FFN ordinal is conditioned on the already accepted layer
  topology; router and shared gate-up never share one doubled timing population.
[Timeouts & Locks] Three finite metadata graphs; no raw scan or prediction.
[Side-Effect Policy] Write new cases/evidence without modifying previous arms.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen_a3_service_cases import physical_ops, read, write, identity
from build_qwen35_complete_service_cases import _physical_match
from build_qwen35_highconc_service import match_ids, REVISION
from build_qwen397_highconc_service import pooled

ROOT = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement'
OUT = ROOT / 'qwen35-a5-shared-native'


def build():
    manifest = read(ROOT / 'qwen35-a5/decode-forward-cases.json'); evidence = []
    for row in manifest['cases']:
        prior = identity(row['sim_case_path']); raw = read(prior['path'])
        geometry = row['replay_input_pins']['primary_geometry']; M = geometry['query_rows']
        native_path = OUT / 'native-partitions' / (row['case_id'] + '-native-partitions.json')
        native = read(native_path); F = native['forward_count']
        if native['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_source_changed')
        before, oldops = physical_ops(raw, geometry)
        raw['model']['quant']['category_overrides']['shared_expert'] = {
            'weight_format': 'bf16', 'activation_format': 'bf16'}
        case, ops = physical_ops(raw, geometry)
        removed = [o.op_id for o in oldops if o.op_id not in {x.op_id for x in ops}]
        if len(removed) != 80 or not all('.shared.' in i and i.endswith('.quantize') for i in removed):
            raise ValueError('shared_precision_changed_unexpected_work')
        additions = []
        for ordinal, recipe, n, k in [(1, 'router', 256, 2048), (2, 'dense_gate_up', 256, 2048),
                                      (3, 'dense_down', 2048, 128)]:
            parts = [p for p in native['partitions'] if p['native_operator_type'] == 'MatMulV3'
                     and p['topology_region'] == 'ffn' and p['native_type_ordinal_in_region'] == ordinal]
            expected_abi = ['native_tensor_abi', 'MatMulV3',
                [[[M, k], 'bf16', 'ND'], [[n, k], 'bf16', 'ND']], [[[M, n], 'bf16', 'ND']]]
            if not parts or any(p['native_abi'] != expected_abi for p in parts):
                raise ValueError('native_shared_role_ABI_mismatch')
            population = pooled(parts); selected = [o for o in ops if o.recipe == recipe]
            if len(selected) != 40 or population['count'] != 40 * F:
                raise ValueError('native_role_not_40_per_forward')
            for part in parts:
                if any(count != F for count in part['layer_counts'].values()):
                    raise ValueError('native_role_missing_in_accepted_layer')
            if any(tuple(o.local_shape) != (M, n, k) or o.dtype != 'bf16'
                   or dict(o.metadata)['weight_dtype'] != 'bf16' for o in selected):
                raise ValueError('fresh_shared_physical_geometry_mismatch')
            selector = _physical_match(case, selected[0])
            rule = {'id': 'q35-bf16-shared-' + sha256(json.dumps(selector, sort_keys=True).encode()).hexdigest()[:16],
                'match': selector, 'response': {'fixed_us': population['mean_us']}, 'provenance': {
                    'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'source_identity': row['source'], 'native_partition_identity': identity(native_path),
                    'native_operator_type': 'MatMulV3', 'native_abi': expected_abi,
                    'topology_region': 'ffn', 'native_type_ordinal_in_region': ordinal,
                    'declared_role': recipe, 'observed_population': population,
                    'forward_count': F, 'expected_rule_hits': 40, 'body_residual_used': False,
                    'small_M_values_copied': False, 'strict_contract_admission_changed': False,
                    'mapping_basis': 'full_ABI_and_complete_layer_topology_then_distinct_FFN_source_order'}}
            selected_ids = {o.op_id for o in selected}
            if match_ids(rule, case, ops) != selected_ids:
                raise ValueError('physical_role_selector_not_unique')
            for old in raw['runtime']['kernels']['service_regimes']:
                if selected_ids & match_ids(old, case, ops):
                    raise ValueError('existing_native_response_overlap:' + old['id'])
            raw['runtime']['kernels']['service_regimes'].append(rule); additions.append(rule)
        cal = {'evaluation_relation': 'in_sample', 'baseline_case_identity': prior,
               'prior_evidence_reference': {'case_identity': prior, 'json_pointer': '/runtime/metadata/calibration_evidence'},
               'native_partition_identity': identity(native_path), 'body_residual_used': False,
               'precision_correction': 'shared_expert BF16 operands/output; routed INT8 experts unchanged'}
        raw['runtime']['metadata'].update(calibration_origin='observed', calibration_evidence=cal)
        path = OUT / 'cases' / (row['case_id'] + '-shared-bf16.json'); write(path, raw)
        row.update(sim_case_path=str(path), model_declaration=identity(path), calibration_origin='observed',
                   calibration_evidence=cal, variant_id='q35-shared-native-' + REVISION[:8])
        row['replay_input_pins']['case'] = identity(path)
        evidence.append({'case_id': row['case_id'], 'source_identity': row['source'], 'forward_count': F,
            'geometry': geometry, 'case_identity': identity(path), 'baseline_case_identity': prior,
            'native_partition_identity': identity(native_path), 'new_rules': additions,
            'removed_shared_quantizers': removed, 'source_semantic_role_order': [
                'router -> MoeGatingTopK', 'shared gate_up -> SwiGlu -> shared down -> shared gate']})
    manifest.update(runtime_source_commit=REVISION, variant_id='q35-shared-native-' + REVISION[:8])
    write(OUT / 'decode-forward-cases.json', manifest)
    write(OUT / 'observed-populations.json', {'cases': evidence, 'producer_identity': identity(__file__),
                                           'new_raw_scans': 0, 'new_cost_predictions': 0})
    print(json.dumps([{'case_id': r['case_id'], 'new_rules': len(r['new_rules'])} for r in evidence]))


if __name__ == '__main__':
    build()
