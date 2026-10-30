"""Declare Q397 native GQA/GMM and TP16 service domains from full populations.

[Role] Reuse retained Body-native ABI histograms with source physical boundaries.
[Invariants] No Body residual or case-id selectors. A fused up/activation/quant
  call receives one response. Buffer capacity never establishes expert counts.
[Timeouts & Locks] Two bounded metadata graphs; no raw scan or cost calls.
[Side-Effect Policy] Write new conditional in-sample cases, manifest and evidence.
"""
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen_a3_service_cases import physical_ops, identity, read, write
from build_qwen35_complete_service_cases import _physical_match
from build_qwen35_highconc_service import match_ids, REVISION

OUT = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement/qwen397-a3'


def pooled(parts):
    hist = Counter()
    for part in parts:
        hist.update(dict(part['duration_ns_counter']))
    n = sum(hist.values()); total = sum(ns * c for ns, c in hist.items())
    return {'count': n, 'activity_sum_ns': total, 'mean_us': total / n / 1000,
            'duration_ns_counter': sorted(hist.items())}


def build():
    manifest = read(OUT / 'retained-native-cases.json'); evidence = []
    for row in manifest['cases']:
        prior = identity(row['sim_case_path']); raw = read(prior['path'])
        geo = row['replay_input_pins']['primary_geometry']; M = geo['query_rows']
        native_path = OUT / 'native-partitions' / (row['case_id'] + '-native-partitions.json')
        observed = read(native_path); F = observed['forward_count']
        if observed['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_source_changed')
        kernels = raw['runtime'].setdefault('kernels', {})
        if kernels.get('service_regimes'):
            raise ValueError('baseline_service_rules_require_explicit_merge')
        kernels.setdefault('lowerings', {})['native_fusion'] = {'implementation': 'declared_native_fusion',
            'options': {'roles': ['grouped_gate_up_activation_quant'], 'traffic_profile': {
                'grouped_gate_up_activation_quant': 'grouped_swiglu_quant_int8_split_workspace_ae923905'}}}
        kernels['hccl'] = {'allreduce': {'expansion': 'AICPU_TS', 'template': 'mesh_twoshot', 'axes': ['tp']}}
        raw['machine'].setdefault('device', {}).setdefault('rates', {})['joint_native_a3'] = 1e9
        raw['machine']['device'].setdefault('work_units', {})['joint_native_a3'] = 'busy_ns'
        raw['machine']['device'].setdefault('resource_units', {})['joint_native_a3'] = 1
        case, ops = physical_ops(raw, geo)
        if case.runtime.parallel.tp != 16 or case.runtime.parallel.ep != 1:
            raise ValueError('unexpected_source_parallel_domain')
        rules = []
        for native, recipe, calls, joint in [
            ('GroupedMatmulSwigluQuant', 'declared_native_fusion', 60, True),
            ('GroupedMatmul', 'grouped_down', 60, True),
            ('FusedInferAttentionScore', 'flash_attention_decode', 15, True),
            ('hcom_allReduce_', 'hccl_entry', 120, False)]:
            parts = [p for p in observed['partitions'] if p['native_operator_type'] == native]
            pop = pooled(parts); selected = [o for o in ops if o.recipe == recipe]
            if len(selected) != calls or pop['count'] != calls * F:
                raise ValueError('source_native_multiplicity_changed:' + native)
            abis = {json.dumps(p['native_abi'], sort_keys=True) for p in parts}
            if len(abis) != 1:
                raise ValueError('native_ABI_requires_separate_domains')
            abi = parts[0]['native_abi']
            if native == 'GroupedMatmulSwigluQuant':
                inputs, outputs = abi[2:]
                if (inputs[0] != [[M * 10, 4096], 'int8', 'ND'] or
                    inputs[1] != [[512, 4, 256, 16, 32], 'int8', 'FRACTAL_NZ'] or
                    inputs[2] != [[512, 128], 'fp32', 'ND'] or
                    outputs != [[[M * 10, 64], 'int8', 'ND'], [[M * 10], 'fp32', 'ND']]):
                    raise ValueError('grouped_up_ABI_mismatch')
                for op in selected:
                    view = dict(op.metadata)['fusion_tensor_view']
                    if any(view[k] != v for k, v in {'input_width': 4096, 'intermediate_width': 64,
                            'local_experts': 512, 'input_dtype': 'int8', 'weight_dtype': 'int8',
                            'output_dtype': 'int8', 'input_scale_dtype': 'fp32', 'output_scale_dtype': 'fp32'}.items()):
                        raise ValueError('fused_source_view_mismatch')
            elif native == 'GroupedMatmul':
                if abi[2][0] != [[M * 10, 64], 'int8', 'ND'] or abi[2][1] != [[512, 64, 4096], 'int8', 'FRACTAL_NZ'] or abi[3] != [[[M * 10, 4096], 'bf16', 'ND']]:
                    raise ValueError('grouped_down_ABI_mismatch')
                if any(tuple(o.local_shape) != (M * 10, 4096, 64) or o.dtype != 'int8' for o in selected):
                    raise ValueError('grouped_down_source_mismatch')
            elif native == 'FusedInferAttentionScore':
                if abi[2][0] != [[M, 2, 256], 'bf16', 'ND'] or abi[2][6][0][0] != geo['sequences_per_replica']:
                    raise ValueError('FIA_query_blocktable_mismatch')
            selector = _physical_match(case, selected[0])
            if native == 'GroupedMatmulSwigluQuant':
                selector['metadata.fusion_role'] = 'grouped_gate_up_activation_quant'
                selector['metadata.fusion_tensor_view.local_experts'] = 512
            if native == 'hcom_allReduce_':
                # All 120 actual calls are retained once. Source-derived payload
                # and template are conditions, not observed launch arguments.
                selector = {'hardware': case.machine.hardware_key or case.machine.sku, 'phase': 'decode',
                    'recipe': 'hccl_entry', 'metadata.hccl_selection.collective': 'allreduce',
                    'metadata.hccl_selection.expansion': 'AICPU_TS',
                    'metadata.hccl_selection.template': 'mesh_twoshot',
                    'metadata.hccl_selection.ranks': 16,
                    'metadata.hccl_selection.payload_bytes': M * 4096 * 2}
            rule = {'id': 'q397-native-' + sha256(json.dumps(selector, sort_keys=True).encode()).hexdigest()[:16],
                'match': selector, 'response': {'fixed_us': pop['mean_us']}, 'provenance': {
                    'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'source_identity': row['source'], 'native_partition_identity': identity(native_path),
                    'native_operator_type': native, 'native_abi': abi, 'observed_population': pop,
                    'expected_rule_hits': calls, 'forward_count': F, 'body_residual_used': False,
                    'boundary': 'inclusive_whole_native_call', 'group_list_values_observed': False,
                    'source_expert_distribution': 'unchanged_probability_moments',
                    'actual_hccl_template_observed': False, 'actual_hccl_payload_observed': False,
                    'contract_admission_changed': False}}
            if joint:
                rule['execution'] = {'kind': 'joint_native', 'native_kernel': native,
                                     'resource': 'joint_native_a3', 'reference_rate': 1e9}
            if match_ids(rule, case, ops) != {o.op_id for o in selected}:
                raise ValueError('physical_selector_not_exact:' + native)
            rules.append(rule)
        kernels['service_regimes'] = rules
        calibration = {'evaluation_relation': 'in_sample', 'baseline_case_identity': prior,
            'native_population_identity': identity(native_path), 'body_residual_used': False,
            'full_capture_native_ABI': True, 'source_routing_and_transport_conditions_remain': True}
        raw['runtime'].setdefault('metadata', {}).update(calibration_origin='observed', calibration_evidence=calibration)
        path = OUT / 'cases' / (row['case_id'] + '-native-service.json'); write(path, raw)
        row.update(sim_case_path=str(path), model_declaration=identity(path), calibration_origin='observed',
                   calibration_evidence=calibration, variant_id='q397-highconc-native-' + REVISION[:8])
        row['replay_input_pins']['case'] = identity(path)
        evidence.append({'case_id': row['case_id'], 'source_identity': row['source'], 'geometry': geo,
            'case_identity': identity(path), 'baseline_case_identity': prior, 'forward_count': F,
            'native_partition_identity': identity(native_path), 'rules': rules})
    manifest.update(runtime_source_commit=REVISION, variant_id='q397-highconc-native-' + REVISION[:8])
    write(OUT / 'decode-forward-cases.json', manifest)
    write(OUT / 'observed-populations.json', {'cases': evidence, 'new_raw_scans': 0, 'new_cost_predictions': 0,
                                           'producer_identity': identity(__file__)})
    print(json.dumps([{'case_id': x['case_id'], 'rules': len(x['rules'])} for x in evidence]))


if __name__ == '__main__':
    build()
