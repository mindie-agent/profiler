"""Declare the A3 V2 typed caller and complete native-group responses.

[Role] Add V2 caller/transport as a separate arm after local joint calibration.
[Invariants] Quantized dispatch feeds routed GMM directly; no second pack or
  activation quantizer. Complete MC2 elapsed floors belong to one whole group.
[Timeouts & Locks] Three bounded metadata exports; no raw reads, cost or locks.
[Side-Effect Policy] Write independent cases and proof; never modify Sim/source.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from build_glm78_joint_service_cases import pooled, verify_grouped_match
from check_glm78_native_v2 import check_retained_v2


HERE = Path(__file__).resolve().parent
BASE = HERE / 'acceptance-20261030-glm78-joint-service/decode-forward-glm78-joint-service-cases.json'
NATIVE = HERE / 'acceptance-20261030-service-qwen-a3/glm78-native'
OUT = HERE / 'acceptance-20261030-glm78-native-v2-service'


def build():
    manifest = read(BASE); output = deepcopy(manifest); output['cases'] = []; proofs = []
    for row in manifest['cases']:
        original = read(row['sim_case_path']); raw = deepcopy(original)
        geometry = row['replay_input_pins']['primary_geometry']; case, old_ops = physical_ops(raw, geometry)
        native_path = NATIVE / f"{row['case_id']}-native-partitions.json"; retained = read(native_path)
        proof = check_retained_v2(retained, tp=case.runtime.parallel.tp, ep=case.runtime.parallel.ep,
                                  hidden=case.model.hidden_size, experts=case.model.num_experts)
        ep = case.runtime.parallel.ep
        raw['runtime']['kernels']['native_moe_protocol'] = {
            'kind': 'arch22_v2_caller', 'dispatch_quant': 'per_token_int8', 'max_inflight_per_rank': ep}
        assumption = {'kind': 'explicit_logical_transport_concurrency', 'max_inflight_per_rank': ep,
            'basis': 'fully_concurrent_EP_peer_window_for_logical_payload_lower_bound',
            'observed_window': False, 'captured_inner_tiling': None,
            'scope': 'Does not identify fullmesh/basic/hierarchy selection or captured native peer concurrency.'}
        raw.setdefault('metadata', {})['native_v2_caller_assumption'] = assumption
        case, ops = physical_ops(raw, geometry)
        old_ids = {op.op_id for op in old_ops}; ids = {op.op_id for op in ops}
        old_external = {dep for op in old_ops for dep in op.deps if dep not in old_ids}
        if {dep for op in ops for dep in op.deps if dep not in ids} - old_external:
            raise ValueError('native_v2_dangling_dependency')
        if any(op.family in {'route_pack', 'route_unpack'} for op in ops):
            raise ValueError('native_v2_kept_separate_pack_or_unpack')
        before = Counter(op.family for op in old_ops); after = Counter(op.family for op in ops)
        if before['quantize'] - after['quantize'] != 75: raise ValueError('routed_quantizer_not_removed_exactly_once')
        if after['dequant_swiglu_quant'] != before['dequant_swiglu_quant']:
            raise ValueError('native_v2_removed_shared_ffn_quantizer')
        # The local-native joint rules retain the same physical inputs and do
        # not absorb the transport phases or change their inclusive means.
        for rule in raw['runtime']['kernels']['service_regimes']:
            if rule.get('execution', {}).get('native_kernel') in {'GroupedMatmul','GroupedMatmulSwigluQuantV2'}:
                verify_grouped_match(case, ops, rule['match'], 75)
        capacity = proof['source_caller_geometry']['expert_buffer_capacity_rows']
        width = case.model.hidden_size; groups = {}; entries = {}
        for op in ops:
            meta = dict(op.metadata); group = meta.get('device_kernel_group')
            if not group: continue
            groups.setdefault(group['id'], []).append(op)
            if group['entry']: entries.setdefault(group['kernel'], []).append(op)
        added = []
        for kind, entry_ops in sorted(entries.items()):
            if kind not in ('MoeDistributeDispatchV2','MoeDistributeCombineV2') or len(entry_ops) != 75:
                raise ValueError('unexpected_native_v2_population')
            parts = [part for part in retained['partitions'] if part['native_operator_type'] == kind]
            observed = pooled(parts)
            if observed['count'] != 75 * retained['forward_count']: raise ValueError('native_v2_population_incomplete')
            matches = []
            for entry in entry_ops:
                meta = dict(entry.metadata); members = groups[meta['device_kernel_group']['id']]
                exits = [op for op in members if dict(op.metadata)['device_kernel_group']['exit']]
                if len(exits) != 1: raise ValueError('native_v2_exit_not_unique')
                contract = meta['mc2_v2_caller']
                if contract['native_output_capacity_rows'] != capacity or contract['source_tokens'] != proof['source_caller_geometry']['tp_local_rows']:
                    raise ValueError('native_v2_capacity_or_tp_local_shape_differs')
                if kind == 'MoeDistributeDispatchV2':
                    declared = meta['native_abi_outputs']; observed_outputs = parts[0]['native_abi'][3]
                    if len(declared) != len(observed_outputs): raise ValueError('native_dispatch_output_slots_differ')
                    for tensor, actual in zip(declared, observed_outputs):
                        if [list(tensor['shape']),tensor['dtype'],tensor['layout']] != actual:
                            raise ValueError('native_dispatch_typed_output_differs')
                else:
                    if tuple(dict(exits[0].metadata)['output_shape']) != (contract['source_tokens'],width):
                        raise ValueError('native_combine_final_shape_differs')
                match = _physical_match(case, entry)
                match.update(kernel=kind)
                match['metadata.device_kernel_group.entry'] = True
                for key in ('kind','source_tokens','valid_source_tokens','top_k','width','experts','ep',
                            'received_assignments','native_output_capacity_rows','dispatch_quant'):
                    match['metadata.mc2_v2_caller.' + key] = contract[key]
                matches.append(match)
            if any(match != matches[0] for match in matches): raise ValueError('heterogeneous_native_v2_physical_domain')
            rule = {'id': kind.lower() + '-complete-group-response', 'match': matches[0],
                'response': {'fixed_us': observed['mean_us']},
                'provenance': {'calibration_origin':'observed','evaluation_relation':'in_sample',
                    'native_operator_type':kind,'native_identity':identity(native_path),
                    'source_identity':retained['source_identity'],'complete_population':observed,
                    'forward_count':retained['forward_count'],'expected_rule_hits':75,
                    'response_boundary':'one_complete_native_device_kernel_group_including_transport',
                    'body_residual_used':False,'observed_pointer_identity':False,
                    'actual_expert_valid_rows':None,'buffer_capacity_is_not_valid_rows':True,
                    'transport_assumption':assumption}}
            raw['runtime']['kernels']['service_regimes'].append(rule)
            added.append({'rule_id':rule['id'],'native_operator_type':kind,'expected_rule_hits':75,
                          'parameter_us':observed['mean_us'],'complete_call_count':observed['count']})
        if set(entries) != {'MoeDistributeDispatchV2','MoeDistributeCombineV2'}: raise ValueError('missing_native_v2_boundary')
        target = OUT / 'cases' / f"{row['case_id']}-native-v2.json"; write(target,raw)
        new = deepcopy(row); new.update(sim_case_path=str(target), model_declaration=identity(target),
            variant_id='glm78-native-v2-caller-joint-local-service')
        new['replay_input_pins']['case'] = identity(target)
        new['calibration_evidence']['native_v2_responses'] = added
        new.setdefault('scenario_evidence', {})['native_v2_transport_assumption'] = assumption
        output['cases'].append(new)
        proofs.append({'case_id':row['case_id'],'retained_native_identity':identity(native_path),
            'baseline_case_identity':identity(row['sim_case_path']),'case_identity':identity(target),
            'typed_native_proof':proof,'source_condition':assumption,'response_rules':added,
            'fresh_graph':{'native_dispatch_groups':75,'native_combine_groups':75,
                'separate_route_pack_count':0,'separate_route_unpack_count':0,
                'routed_quantizers_removed':before['quantize']-after['quantize'],
                'shared_dequant_swiglu_quant_count':after['dequant_swiglu_quant'],
                'tp_finalization_allgather_count':after['allgather'],
                'dependencies_resolve_to_preserved_external_inputs':True}})
    output['baseline_identity'] = identity(BASE); output['variant_id'] = 'glm78-native-v2-caller-joint-local-service'
    write(OUT / 'decode-forward-glm78-native-v2-cases.json', output)
    write(OUT / 'native-v2-input-proof.json', {'cases':proofs,'raw_reads':0,'new_predictions':0,
        'producer_identity':identity(__file__),'typed_checker_identity':identity(HERE/'check_glm78_native_v2.py')})
    print(json.dumps([{'case_id':r['case_id'],'responses':r['response_rules'],'fresh_graph':r['fresh_graph']}for r in proofs]))


if __name__ == '__main__': build()
