"""Extend the same retained native domains across the Q35 A5 batch neighborhood.

[Role] Bind complete per-source populations to existing physical source roles.
[Invariants] No small-M parameter copying, Body residual fitting or extra native
  launches. Full cohort evidence and source-only helper correspondence stay distinct.
[Timeouts & Locks] Three finite metadata graphs; no raw capture or cost calls.
[Side-Effect Policy] Write independent cases and provenance, preserving old arms.
"""
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from build_qwen35_complete_service_cases import (
    read, pinned, identity, population, stable, physical_ops, _physical_match,
    predicted_contract, CANONICAL, OBS, OUT as BASE)
from mindie_sim.prediction.service_regimes import axis_equal, lookup

OUT = Path(__file__).resolve().parent / 'acceptance-20261030-highconc-service-refinement'
REVISION = '21c30821d87a757bace8cf6b2fffea2536db643e'


def match_ids(rule, case, ops):
    return {op.op_id for op in ops if all(axis_equal(lookup({
        **op.to_dict(include_work=False), 'hardware': case.machine.hardware_key or case.machine.sku,
        'dtype': op.dtype or case.model.compute_dtype}, key), value)
        for key, value in rule['match'].items())}


def build():
    manifest = read(BASE / 'decode-forward-complete-service-cases.json')
    control = read(BASE / 'decode-forward-c4-gdn-helpers-cases.json')['cases'][0]
    manifest['cases'] = [control if r['case_id'] == control['case_id'] else r for r in manifest['cases']]
    indices = {r['source_case_id']: r for r in read(CANONICAL / 'body-operator-family-scoreboard.json')['cases']}
    evidence = []
    for row in manifest['cases']:
        name = row['case_id']; prior = row['model_declaration']; raw = pinned(prior)
        geometry = row['replay_input_pins']['primary_geometry']; case, ops = physical_ops(raw, geometry)
        by_id = {o.op_id: o for o in ops}; index = indices[name]
        actual, mapping = pinned(index['actual_identity']), pinned(index['mapping_identity'])
        forwards = actual['forward_count']; additions, replaced, exclusions = [], [], []
        if actual['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_source_changed')
        if name != control['case_id']:
            def add(native, targets, observed, proof, *, extra=None, replace_ids=()):
                if observed['count'] != proof.get('pooled_target_count', len(targets)) * forwards:
                    raise ValueError('whole_native_population_mismatch:' + native)
                selector = _physical_match(case, targets[0]); selector.update(extra or {})
                rule = {'id': 'q35-highconc-' + sha256(stable(selector).encode()).hexdigest()[:16],
                        'match': selector, 'response': {'fixed_us': observed['mean_us']},
                        'provenance': {'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                            'source_identity': row['source'], 'native_operator_type': native,
                            'actual_identity': index['actual_identity'], 'forward_count': forwards,
                            'expected_rule_hits': len(targets), 'observed_population': observed,
                            'body_residual_used': False, 'small_M_value_copied': False,
                            'strict_admission_changed': False, **proof}}
                selected = match_ids(rule, case, ops)
                if selected != {o.op_id for o in targets}:
                    raise ValueError('physical_selector_population_mismatch:' + native)
                old = raw['runtime']['kernels']['service_regimes']
                for previous in list(old):
                    overlap = selected & match_ids(previous, case, ops)
                    if overlap:
                        if previous['id'] not in replace_ids or match_ids(previous, case, ops) != selected:
                            raise ValueError('unexpected_existing_response_overlap:' + previous['id'])
                        old.remove(previous); replaced.append(previous)
                old.append(rule); additions.append(rule)

            for cohort in (c for w in mapping['windows'] for c in w['cohorts']):
                if cohort['native_operator_type'] not in {'Slice', 'CausalConv1d', 'SwiGlu', 'QuantBatchMatmulV3', 'ScatterPaKvCache'}:
                    continue
                targets = [by_id[t.split('/', 1)[1]] for t in cohort['target_ids']]
                if any(json.loads(json.dumps(predicted_contract(o.to_dict(include_work=False)))) != cohort['contract'] for o in targets):
                    raise ValueError('fresh_cohort_contract_changed')
                family, = [f for f in actual['families'] if f['native_operator_type'] == cohort['native_operator_type']
                           and set(f['candidate_target_ids']) == set(cohort['target_ids'])]
                observed = population([family])
                if observed['count'] != len(targets) * forwards:
                    exclusions.append({'native_operator_type': cohort['native_operator_type'],
                                       'cohort_id': cohort['cohort_id'], 'count': observed['count'],
                                       'declared_calls': len(targets) * forwards,
                                       'reason': 'native_occurrences_do_not_match_declared_calls'})
                    continue
                add(cohort['native_operator_type'], targets, observed,
                    {'evidence_strength': 'complete_active_tensor_cohort', 'contract': cohort['contract'],
                     'cohort_id': cohort['cohort_id'], 'mapping_identity': index['mapping_identity']})

            grouped_path = OBS / f'grouped-{name}.json'; grouped = read(grouped_path)
            if grouped['source_identity']['sha256'] != row['source']['sha256'] or grouped['forward_count'] != forwards:
                raise ValueError('grouped_native_population_changed')
            old_gmm = [r['id'] for r in raw['runtime']['kernels']['service_regimes'] if r['id'].startswith('a5-int8-grouped-')]
            for role, recipe in [('expert_up', 'balanced_grouped_gate_up'), ('expert_down', 'balanced_grouped_down')]:
                parts = [p for p in grouped['partitions'] if p['role'] == role]
                if len({stable(p['native_abi']) for p in parts}) != 1:
                    raise ValueError('grouped_ABI_domain_differs')
                targets = [o for o in ops if o.recipe == recipe]
                rows = list(dict(targets[0].metadata)['matrix_group_rows'])
                add('GroupedMatmul', targets, population(parts),
                    {'evidence_strength': 'complete_native_ABI_with_source_role_and_conditional_routed_counts',
                     'declared_role': role, 'native_partition_identity': identity(grouped_path),
                     'native_abi': parts[0]['native_abi'], 'actual_group_list_values_observed': False,
                     'captured_capacity_rows': parts[0]['native_abi'][2][0][0][0]},
                    extra={'metadata.matrix_group_rows': rows}, replace_ids=old_gmm)

            helper_recipes = {'fused_gdn_gating_kernel': ('ascend_gdn_decode_gating',),
                              'l2norm_fwd_kernel2': ('decode_q_l2norm', 'decode_k_l2norm'),
                              '_layer_norm_fwd_1pass_kernel_npu': ('linear_output_norm_gate',)}
            for native, recipes in helper_recipes.items():
                family, = [f for f in actual['families'] if f['native_operator_type'] == native]
                group, = family['structure_groups']; measured = population([family])
                if group['attention_kind'] != 'gdn' or group['block'] != 'attention' or population([group]) != measured:
                    raise ValueError('helper_not_complete_GDN_attention_population')
                total_targets = [o for o in ops if o.recipe in recipes]
                if measured['count'] != len(total_targets) * forwards:
                    raise ValueError('helper_whole_call_count_changed')
                for recipe in recipes:
                    targets = [o for o in total_targets if o.recipe == recipe]
                    # Pool the identical native Q/K calls once; each declared
                    # helper receives the pooled per-call mean, not their sum.
                    add(native, targets, measured,
                        {'evidence_strength': 'complete_topology_population_and_source_semantic_boundary',
                         'pooled_native_population': measured, 'pooled_target_count': len(total_targets),
                         'per_role_timing_separately_observed': len(recipes) == 1,
                         'all_event_native_ABIs_retained': False, 'declared_recipe': recipe},
                        extra={'metadata.caller_implementation': 'vllm_ascend_gdn_decode'})

            family, = [f for f in actual['families'] if f['native_operator_type'] == 'FusedInferAttentionScore']
            group, = family['structure_groups']; targets = [o for o in ops if o.recipe == 'flash_attention_decode']
            if group['attention_kind'] != 'gqa' or group['block'] != 'attention' or population([family]) != population([group]):
                raise ValueError('FIA_not_complete_GQA_population')
            requests = [[geometry['tokens_per_sequence'], geometry['context_tokens']]] * geometry['sequences_per_replica']
            if any(json.loads(json.dumps(dict(o.metadata)['gqa_decode']['requests'])) != requests for o in targets):
                raise ValueError('FIA_batch_geometry_changed')
            for example in family['examples']:
                contract = example['contract']
                if contract[0] != 'attention_paged_active_qkv' or contract[2] != [[geometry['query_rows'], 4, 256], 'bf16', 'ND'] or contract[5] != geometry['sequences_per_replica']:
                    raise ValueError('FIA_contract_example_conflicts_with_source')
            add('FusedInferAttentionScore', targets, population([family]),
                {'evidence_strength': 'complete_topology_population_with_retained_contract_examples',
                 'all_event_native_ABIs_retained': False, 'retained_contract_examples': family['examples'],
                 'context_basis': 'declared_prompt_not_observed_valid_KV'},
                extra={'metadata.gqa_decode.requests': requests})

        calibration = {'evaluation_relation': 'in_sample', 'body_residual_used': False,
                       'scope': 'same_source_native_domains_across_declared_batch_neighborhood',
                       'prior_evidence_reference': {'case_identity': prior,
                           'json_pointer': '/runtime/metadata/calibration_evidence'},
                       'new_rule_ids': [r['id'] for r in additions],
                       'unchanged_control': name == control['case_id']}
        raw['runtime']['metadata'].update(calibration_origin='observed', calibration_evidence=calibration)
        path = OUT / 'qwen35-a5/cases' / (name + '.json'); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw, indent=2) + '\n')
        row.update(sim_case_path=str(path), model_declaration=identity(path),
                   variant_id='qwen35-highconc-native-domains-' + REVISION[:8],
                   calibration_origin='observed', calibration_evidence=calibration)
        row['replay_input_pins']['case'] = identity(path)
        evidence.append({'case_id': name, 'baseline_case_identity': prior, 'case_identity': identity(path),
                         'source_identity': row['source'], 'forward_count': forwards, 'geometry': geometry,
                         'new_rules': additions, 'replaced_rules': replaced, 'exclusions': exclusions,
                         'unchanged_control': name == control['case_id']})
    manifest.update(variant_id='qwen35-highconc-native-domains-' + REVISION[:8], runtime_source_commit=REVISION)
    manifest['runtime_plan'] = {'source_commit': REVISION}
    destination = OUT / 'qwen35-a5'
    (destination / 'decode-forward-cases.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (destination / 'observed-populations.json').write_text(json.dumps({'cases': evidence,
        'producer_identity': identity(__file__), 'new_raw_scans': 0, 'new_cost_predictions': 0}, indent=2) + '\n')
    print(json.dumps([{'case_id': r['case_id'], 'new_rules': len(r['new_rules']), 'replaced': len(r['replaced_rules'])} for r in evidence]))


if __name__ == '__main__':
    build()
