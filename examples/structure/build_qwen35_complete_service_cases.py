"""Extend Q35 observable service domains using complete retained populations.

[Role] Rebind MatMul/GDN cohorts and the small-row DSQ native boundary.
[Invariants] Only observed integer histograms set responses. Body residuals and
  old predicted times never set parameters. INT32→DSQ→INT8+row-scale evidence
  retains allocation capacity separately from declared active expert rows.
[Timeouts & Locks] Three bounded metadata graphs; no raw scans or model costs.
[Side-Effect Policy] Write independent cases and manifests; preserve old arms.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import resource

from build_qwen_a3_service_cases import physical_ops
from build_a3_observed_service_cases import _physical_match
from mindie_sim.structure_contracts import predicted_contract

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'examples/structure'
OUT = EXAMPLES / 'acceptance-20261030-qwen35-complete-observed-service'
PREVIOUS = EXAMPLES / 'acceptance-20261030-qwen35-observed-service'
CANONICAL = EXAMPLES / 'acceptance-20261030-qwen35-source-complete/canonical-with-tensor-move'
OBS = ROOT / 'data/observations/sources/arch3510-physical-services'
RUNTIME = '672a595fb1e102208d9fc904fad0ec9180fa437a'


def read(path):
    path = Path(path)
    if path.stat().st_size > 50 * 1024**2:
        raise ValueError('bounded_metadata_required')
    return json.loads(path.read_text())


def resolve(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def identity(path):
    path = resolve(path)
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def pinned(pin):
    path = resolve(pin['path'])
    if identity(path)['sha256'] != pin['sha256']:
        raise ValueError('retained_metadata_changed:' + str(path))
    return read(path)


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def population(groups):
    counter = Counter()
    for group in groups:
        counter.update({int(ns): int(n) for ns, n in group['duration_ns_counter']})
    count = sum(counter.values())
    total = sum(ns*n for ns, n in counter.items())
    return {'count': count, 'activity_sum_ns': total, 'mean_us': total/count/1000,
            'duration_ns_counter': sorted(counter.items())}


def build():
    manifest = read(PREVIOUS / 'decode-forward-service-cases.json')
    canonical = {r['source_case_id']: r for r in read(CANONICAL / 'body-operator-family-scoreboard.json')['cases']}
    rows, evidence = [], []
    (OUT / 'cases').mkdir(parents=True, exist_ok=True)
    for source in sorted(manifest['cases'], key=lambda r: r['case_id']):
        row = deepcopy(source); cid = row['case_id']; prior_path = resolve(row['sim_case_path'])
        raw = pinned(row['model_declaration'])
        geometry = row['replay_input_pins']['primary_geometry']
        case, ops = physical_ops(raw, geometry)
        by_id = {op.op_id: op for op in ops}
        previous_rules = deepcopy(raw['runtime']['kernels']['service_regimes'])
        removed = [r for r in previous_rules if 'mxa8w4-nznk' in r['id']]
        if len(removed) != 2 or any(dict(op.metadata).get('weight_format') == 'mxfp4' for op in ops):
            raise ValueError('unrelated_mxfp4_domain_not_proven_empty')
        raw['runtime']['kernels']['service_regimes'] = [r for r in previous_rules if r not in removed]
        index = canonical[cid]; actual = pinned(index['actual_identity']); mapping = pinned(index['mapping_identity'])
        if actual['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('actual_source_differs')
        F = actual['forward_count']
        additions, exclusions = [], []
        for window in mapping['windows']:
            for cohort in window['cohorts']:
                native = cohort['native_operator_type']
                if native not in {'MatMulV3', 'RecurrentGatedDeltaRule'}:
                    continue
                targets = [by_id[t.split('/', 1)[1]] for t in cohort['target_ids']]
                if any(json.loads(json.dumps(predicted_contract(op.to_dict(include_work=False)))) != cohort['contract'] for op in targets):
                    raise ValueError('fresh_active_contract_changed:' + native)
                families = [f for f in actual['families'] if f['native_operator_type'] == native
                            and set(f['candidate_target_ids']) == set(cohort['target_ids'])]
                if len(families) != 1:
                    raise ValueError('complete_cohort_population_not_unique')
                observed = population(families)
                if observed['count'] != cohort['complete_event_count']:
                    raise ValueError('cohort_histogram_differs')
                if observed['count'] != len(targets)*F:
                    exclusions.append({'cohort_id': cohort['cohort_id'], 'native_operator_type': native,
                        'contract': cohort['contract'], 'observed_population': observed,
                        'declared_target_count': len(targets), 'forward_count': F,
                        'reason': 'retained_population_has_more_calls_than_fresh_matching_targets',
                        'calibration_rule_added': False})
                    continue
                domains = defaultdict(list)
                for op in targets:
                    domains[stable(_physical_match(case, op))].append(op)
                for domain, selected in domains.items():
                    match = json.loads(domain)
                    matching = [o for o in ops if _physical_match(case, o) == match]
                    if {o.op_id for o in matching} != {o.op_id for o in selected}:
                        raise ValueError('physical_selector_population_differs')
                    rid = 'q35-complete-' + sha256(domain.encode()).hexdigest()[:16]
                    provenance = {'evaluation_relation': 'in_sample',
                        'source_identity': row['source'], 'actual_identity': index['actual_identity'],
                        'mapping_identity': index['mapping_identity'], 'cohort_id': cohort['cohort_id'],
                        'native_operator_type': native, 'observed_population': observed,
                        'contract': cohort['contract'], 'contract_scope': cohort['contract_scope'],
                        'forward_count': F, 'expected_rule_hits': len(selected),
                        'pooled_native_cohort_target_count': len(targets),
                        'declared_role_timing_separately_observed': len(domains) == 1,
                        'parameter_basis': 'complete_native_contract_cohort_arithmetic_mean_us',
                        'whole_body_residual_used': False, 'old_prediction_values_used': False,
                        'active_contracts_revalidated': True, 'strict_admission_changed': False}
                    raw['runtime']['kernels']['service_regimes'].append({
                        'id': rid, 'match': match, 'response': {'fixed_us': observed['mean_us']},
                        'provenance': provenance})
                    additions.append({'rule_id': rid, 'match': match, **provenance})
        dsq_path = OBS / f'scalar-dma-{cid}.json'
        gmm_path = OBS / f'grouped-{cid}.json'
        dsq = read(dsq_path); gmm = read(gmm_path)
        if any(value['source_identity']['sha256'] != row['source']['sha256'] or value['forward_count'] != F
               for value in (dsq, gmm)):
            raise ValueError('retained_native_source_or_population_differs')
        dsq_parts = [p for p in dsq['partitions'] if p['native_operator_type'] == 'DequantSwigluQuant']
        abi_keys = {stable(p['native_abi']) for p in dsq_parts}
        if len(abi_keys) != 1:
            raise ValueError('multiple_DSQ_ABIs_need_distinct_domains')
        abi = json.loads(next(iter(abi_keys)))
        up = [p for p in gmm['partitions'] if p['role'] == 'expert_up']
        down = [p for p in gmm['partitions'] if p['role'] == 'expert_down']
        if not up or not down:
            raise ValueError('typed_expert_roles_missing')
        if any(p['native_abi'][3][0] != abi[2][0] for p in up):
            raise ValueError('INT32_producer_contract_differs')
        if any(p['native_abi'][2][0] != abi[3][0] or p['native_abi'][2][8] != abi[3][1] for p in down):
            raise ValueError('DSQ_INT8_row_scale_consumer_contract_differs')
        dsq_observed = population(dsq_parts)
        if dsq_observed['count'] != F*40:
            raise ValueError('DSQ_full_layer_population_differs')
        typed_chain = {'dsq_partition_identity': identity(dsq_path),
            'grouped_partition_identity': identity(gmm_path), 'native_abi': abi,
            'input_dtype': 'int32', 'output_dtype': 'int8', 'row_scale_dtype': 'fp32',
            'up_output_to_DSQ_input_shape_dtype_equal': True,
            'DSQ_output_to_down_input_and_row_scale_shape_dtype_equal': True,
            'captured_tensor_address_aliasing_established': False,
            'capacity_rows': abi[2][0][0][0],
            'observed_population': dsq_observed}
        # The existing parent's DSQ response only covers 8..16 rows per expert.
        # Add the c4 native boundary's own complete observed response, not a
        # widened copy of that other physical domain.
        if cid == 'qwen35-35b-a5-tp4-c4-graph':
            selected = [o for o in ops if o.recipe == 'grouped_int32_dequant_swiglu']
            if len(selected) != 40:
                raise ValueError('DSQ_declared_layer_population_differs')
            match = _physical_match(case, selected[0])
            if any(_physical_match(case, o) != match for o in selected):
                raise ValueError('DSQ_heterogeneous_domain')
            if {o.op_id for o in ops if _physical_match(case, o) == match} != {o.op_id for o in selected}:
                raise ValueError('DSQ_selector_population_differs')
            match['metadata.program_execution.grouped_dequant_schedule.kind'] = 'arch35_full_load'
            provenance = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
                'native_operator_type': 'DequantSwigluQuant', 'forward_count': F,
                'expected_rule_hits': 40, **typed_chain,
                'declared_active_shape': list(selected[0].local_shape),
                'declared_active_expert_rows': dict(selected[0].metadata).get('matrix_group_rows'),
                'actual_group_list_values_observed': False,
                'response_boundary': 'one_complete_source_DSQ_call',
                'whole_body_residual_used': False, 'old_prediction_values_used': False,
                'strict_admission_changed': False}
            rid = 'q35-smallrows-DSQ-complete-native-response'
            raw['runtime']['kernels']['service_regimes'].append({
                'id': rid, 'match': match, 'response': {'fixed_us': dsq_observed['mean_us']},
                'provenance': provenance})
            additions.append({'rule_id': rid, 'match': match, **provenance})
        calibration = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
            'baseline_parameters_retained': True,
            'new_parameters_basis': 'complete_cohort_and_native_observed_means',
            'body_residual_used': False, 'generalization_claim': False,
            'prior_calibration_evidence': raw['runtime'].get('metadata', {}).get('calibration_evidence'),
            'typed_expert_chain': typed_chain,
            'unused_other_model_rule_ids_removed': [r['id'] for r in removed]}
        raw['runtime'].setdefault('metadata', {}).update(calibration_origin='observed', calibration_evidence=calibration)
        target = OUT / 'cases' / f'{cid}-complete-service.json'
        target.write_text(json.dumps(raw, indent=2) + '\n')
        row.update(sim_case_path=str(target), model_declaration=identity(target),
            variant_id='qwen35-complete-native-service-672a595f',
            calibration_origin='observed', calibration_evidence=calibration,
            baseline_service_case_identity=identity(prior_path))
        row['replay_input_pins']['case'] = identity(target)
        rows.append(row)
        evidence.append({'case_id': cid, 'source_identity': row['source'], 'forward_count': F,
            'geometry': geometry, 'case_identity': identity(target),
            'new_rules': additions, 'unresolved_population_domains': exclusions, 'retained_rule_ids': [r['id'] for r in previous_rules if r not in removed],
            'removed_other_model_rule_ids': [r['id'] for r in removed],
            'typed_expert_chain': typed_chain,
            'raw_capture_reads': 0, 'new_predictions': 0})
        print(json.dumps({'case_id': cid, 'new_rules': len(additions),
            'forward_count': F, 'dsq_mean_us': dsq_observed['mean_us'],
            'rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
    (OUT / 'decode-forward-complete-service-cases.json').write_text(json.dumps({
        'schema_version': manifest['schema_version'], 'variant_id': 'qwen35-complete-native-service-672a595f',
        'cases': rows, 'runtime_source_commit': RUNTIME, 'not_new_live_collection': True,
        'baseline_reference': identity(PREVIOUS / 'decode-forward-service-replay.json')}, indent=2)+'\n')
    (OUT / 'complete-service-populations.json').write_text(json.dumps({
        'schema_version': 'mindie-qwen35-complete-observed-services/1', 'cases': evidence,
        'producer_identity': identity(__file__), 'runtime_source_commit': RUNTIME,
        'raw_capture_reads': 0, 'new_predictions': 0}, indent=2)+'\n')


def extend_c4():
    """Add the remaining complete cohort populations and source-typed GMM calls."""
    manifest = read(OUT / 'decode-forward-complete-service-cases.json')
    row = deepcopy(next(r for r in manifest['cases'] if r['case_id'] == 'qwen35-35b-a5-tp4-c4-graph'))
    base = deepcopy(row)
    raw = pinned(row['model_declaration'])
    case, ops = physical_ops(raw, row['replay_input_pins']['primary_geometry'])
    by_id = {o.op_id: o for o in ops}
    index = next(r for r in read(CANONICAL / 'body-operator-family-scoreboard.json')['cases']
                 if r['source_case_id'] == row['case_id'])
    actual, mapping = pinned(index['actual_identity']), pinned(index['mapping_identity'])
    F, additions = actual['forward_count'], []
    types = {'Slice', 'CausalConv1d', 'SwiGlu', 'QuantBatchMatmulV3', 'ScatterPaKvCache'}
    for cohort in [c for w in mapping['windows'] for c in w['cohorts'] if c['native_operator_type'] in types]:
        targets = [by_id[t.split('/', 1)[1]] for t in cohort['target_ids']]
        if any(json.loads(json.dumps(predicted_contract(o.to_dict(include_work=False)))) != cohort['contract'] for o in targets):
            raise ValueError('extended_active_contract_changed')
        family, = [f for f in actual['families'] if f['native_operator_type'] == cohort['native_operator_type']
                   and set(f['candidate_target_ids']) == set(cohort['target_ids'])]
        observed = population([family])
        if observed['count'] != len(targets)*F or observed['count'] != cohort['complete_event_count']:
            raise ValueError('extended_cohort_population_differs')
        match = _physical_match(case, targets[0])
        if any(_physical_match(case, o) != match for o in targets):
            raise ValueError('extended_cohort_physical_domain_differs')
        if {o.op_id for o in ops if _physical_match(case, o) == match} != {o.op_id for o in targets}:
            raise ValueError('extended_selector_not_exact')
        proof = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
                 'actual_identity': index['actual_identity'], 'mapping_identity': index['mapping_identity'],
                 'native_operator_type': cohort['native_operator_type'], 'cohort_id': cohort['cohort_id'],
                 'contract': cohort['contract'], 'observed_population': observed, 'forward_count': F,
                 'expected_rule_hits': len(targets), 'complete_native_call_boundary': True,
                 'body_residual_used': False, 'active_contract_revalidated': True}
        rule = {'id': 'q35-complete-' + sha256(stable(match).encode()).hexdigest()[:16],
                'match': match, 'response': {'fixed_us': observed['mean_us']}, 'provenance': proof}
        raw['runtime']['kernels']['service_regimes'].append(rule)
        additions.append(rule)
    grouped_path = OBS / f"grouped-{row['case_id']}.json"
    grouped = read(grouped_path)
    if grouped['source_identity']['sha256'] != row['source']['sha256'] or grouped['forward_count'] != F:
        raise ValueError('extended_GMM_source_differs')
    replaced = [r for r in raw['runtime']['kernels']['service_regimes'] if r['id'].startswith('a5-int8-grouped-')]
    if len(replaced) != 2:
        raise ValueError('expected_two_prior_GMM_domains')
    raw['runtime']['kernels']['service_regimes'] = [r for r in raw['runtime']['kernels']['service_regimes'] if r not in replaced]
    for role, recipe in [('expert_up', 'balanced_grouped_gate_up'), ('expert_down', 'balanced_grouped_down')]:
        parts = [g for g in grouped['partitions'] if g['role'] == role]
        observed = population(parts)
        targets = [o for o in ops if o.recipe == recipe]
        if len(targets) != 40 or observed['count'] != F*40 or len({stable(p['native_abi']) for p in parts}) != 1:
            raise ValueError('complete_GMM_population_or_ABI_differs')
        match = _physical_match(case, targets[0])
        if any(_physical_match(case, o) != match or dict(o.metadata)['matrix_group_rows'] != dict(targets[0].metadata)['matrix_group_rows'] for o in targets):
            raise ValueError('GMM_physical_population_differs')
        match['metadata.matrix_group_rows'] = list(dict(targets[0].metadata)['matrix_group_rows'])
        proof = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
                 'native_partition_identity': identity(grouped_path), 'native_operator_type': 'GroupedMatmul',
                 'declared_role': role, 'native_abi': parts[0]['native_abi'], 'observed_population': observed,
                 'forward_count': F, 'expected_rule_hits': len(targets),
                 'response_boundary': 'one_complete_source_typed_grouped_call',
                 'body_residual_used': False, 'actual_group_list_values_observed': False,
                 'declared_active_rows': targets[0].local_shape[0],
                 'captured_capacity_rows': parts[0]['native_abi'][2][0][0][0],
                 'strict_admission_changed': False}
        rule = {'id': 'q35-c4-complete-source-' + role, 'match': match,
                'response': {'fixed_us': observed['mean_us']}, 'provenance': proof}
        raw['runtime']['kernels']['service_regimes'].append(rule)
        additions.append(rule)
    target = OUT / 'cases' / (row['case_id'] + '-extended-service.json')
    raw['runtime']['metadata']['calibration_evidence']['additional_complete_populations'] = [r['id'] for r in additions]
    target.write_text(json.dumps(raw, indent=2) + '\n')
    row.update(sim_case_path=str(target), model_declaration=identity(target),
               variant_id='qwen35-c4-extended-native-service-672a595f',
               calibration_evidence=raw['runtime']['metadata']['calibration_evidence'])
    row['replay_input_pins']['case'] = identity(target)
    manifest.update(cases=[row], variant_id=row['variant_id'], baseline_reference=identity(OUT / 'decode-forward-complete-service-replay.json'))
    (OUT / 'decode-forward-c4-extended-cases.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / 'c4-extended-populations.json').write_text(json.dumps({
        'schema_version': 'mindie-qwen35-complete-observed-services/1', 'source_identity': row['source'],
        'forward_count': F, 'base_case_identity': base['model_declaration'], 'case_identity': identity(target),
        'new_rules': additions, 'replaced_rule_ids': [r['id'] for r in replaced],
        'raw_capture_reads': 0, 'new_predictions': 0}, indent=2) + '\n')
    print(json.dumps({'case_id': row['case_id'], 'additional_complete_rules': len(additions), 'forward_count': F}))


def extend_c4_attention():
    """Calibrate the complete observed batch boundary without claiming full ABI."""
    manifest = read(OUT / 'decode-forward-c4-extended-cases.json')
    row = deepcopy(manifest['cases'][0]); raw = pinned(row['model_declaration'])
    previous_case = row['model_declaration']
    case, ops = physical_ops(raw, row['replay_input_pins']['primary_geometry'])
    index = next(r for r in read(CANONICAL / 'body-operator-family-scoreboard.json')['cases'] if r['source_case_id'] == row['case_id'])
    actual = pinned(index['actual_identity'])
    family, = [f for f in actual['families'] if f['native_operator_type'] == 'FusedInferAttentionScore']
    group, = family['structure_groups']
    targets = [o for o in ops if o.recipe == 'flash_attention_decode']
    F = actual['forward_count']; observed = population([family])
    if group['attention_kind'] != 'gqa' or group['block'] != 'attention' or observed != population([group]):
        raise ValueError('attention_topology_population_differs')
    if len(targets) != 10 or observed['count'] != F * len(targets):
        raise ValueError('attention_is_not_one_batch_call_per_declared_GQA_layer')
    geometry = row['replay_input_pins']['primary_geometry']
    M, B, Q = geometry['query_rows'], geometry['sequences_per_replica'], geometry['tokens_per_sequence']
    for target in targets:
        gqa = dict(target.metadata)['gqa_decode']
        if gqa['requests'] != ((Q, geometry['context_tokens']),) * B:
            raise ValueError('attention_batch_request_domain_differs')
        if target.local_shape[0] != M or target.local_shape[2:] != (4, 256):
            raise ValueError('attention_query_geometry_differs')
    for example in family['examples']:
        contract = example['contract']
        if contract[0] != 'attention_paged_active_qkv' or contract[2] != [[M, 4, 256], 'bf16', 'ND'] or contract[4] != contract[2] or contract[5] != B:
            raise ValueError('retained_attention_examples_conflict_with_declared_query')
    match = _physical_match(case, targets[0])
    match['metadata.gqa_decode.requests'] = [[Q, geometry['context_tokens']]] * B
    if any(_physical_match(case, o) != _physical_match(case, targets[0]) for o in targets):
        raise ValueError('attention_batch_domains_not_homogeneous')
    proof = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
             'actual_identity': index['actual_identity'], 'forward_count': F,
             'native_operator_type': 'FusedInferAttentionScore', 'observed_population': observed,
             'expected_rule_hits': len(targets), 'declared_layer_ids': [o.layer for o in targets],
             'declared_execution_geometry': geometry, 'retained_contract_examples': family['examples'],
             'evidence_strength': 'complete_topology_population_with_bounded_normalized_contract_examples',
             'all_event_native_ABIs_retained': False, 'strict_admission_changed': False,
             'context_basis': 'source_declared_prompt; KV valid-length tensor values not retained',
             'response_boundary': 'one_complete_observed_batch_FIA_call_per_GQA_layer',
             'physical_implementation_identified': False,
             'body_residual_used': False, 'old_prediction_values_used': False}
    rule = {'id': 'q35-c4-batched-GQA-observed-complete-service', 'match': match,
            'response': {'fixed_us': observed['mean_us']}, 'provenance': proof}
    raw['runtime']['kernels']['service_regimes'].append(rule)
    raw['runtime']['metadata']['calibration_evidence']['attention_service_evidence'] = proof
    target = OUT / 'cases' / (row['case_id'] + '-batched-attention-service.json')
    target.write_text(json.dumps(raw, indent=2) + '\n')
    row.update(sim_case_path=str(target), model_declaration=identity(target),
               variant_id='qwen35-c4-batched-attention-service-672a595f',
               calibration_evidence=raw['runtime']['metadata']['calibration_evidence'])
    row['replay_input_pins']['case'] = identity(target)
    manifest.update(cases=[row], variant_id=row['variant_id'], baseline_reference=identity(OUT / 'decode-forward-c4-extended-replay.json'))
    (OUT / 'decode-forward-c4-batched-attention-cases.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / 'c4-batched-attention-population.json').write_text(json.dumps({
        'schema_version': 'mindie-qwen35-complete-observed-services/1', 'source_identity': row['source'],
        'forward_count': F, 'base_case_identity': previous_case, 'case_identity': identity(target),
        'new_rule': rule, 'raw_capture_reads': 0, 'new_predictions': 0}, indent=2) + '\n')
    print(json.dumps({'case_id': row['case_id'], 'FIA_complete_calls': observed['count'], 'batch_programs_per_forward': len(targets)}))


def extend_c4_gdn_helpers():
    """Use whole observed GDN helper calls; no fabricated native descriptors."""
    manifest = read(OUT / 'decode-forward-c4-batched-attention-cases.json')
    row = deepcopy(manifest['cases'][0]); raw = pinned(row['model_declaration'])
    previous_case = row['model_declaration']
    case, ops = physical_ops(raw, row['replay_input_pins']['primary_geometry'])
    index = next(r for r in read(CANONICAL / 'body-operator-family-scoreboard.json')['cases'] if r['source_case_id'] == row['case_id'])
    actual = pinned(index['actual_identity']); F = actual['forward_count']
    correspondence = {
        'fused_gdn_gating_kernel': ('ascend_gdn_decode_gating',),
        'l2norm_fwd_kernel2': ('decode_q_l2norm', 'decode_k_l2norm'),
        '_layer_norm_fwd_1pass_kernel_npu': ('linear_output_norm_gate',),
    }
    additions = []
    for native, recipes in correspondence.items():
        family, = [f for f in actual['families'] if f['native_operator_type'] == native]
        group, = family['structure_groups']; observed = population([family])
        if group['attention_kind'] != 'gdn' or group['block'] != 'attention' or observed != population([group]):
            raise ValueError('helper_population_not_exclusively_GDN_attention')
        all_targets = [o for o in ops if o.recipe in recipes]
        if len(all_targets) != 30 * len(recipes) or observed['count'] != len(all_targets) * F:
            raise ValueError('helper_call_boundary_multiplicity_differs')
        for recipe in recipes:
            targets = [o for o in all_targets if o.recipe == recipe]
            match = _physical_match(case, targets[0])
            match['metadata.caller_implementation'] = 'vllm_ascend_gdn_decode'
            if any(_physical_match(case, o) != _physical_match(case, targets[0]) or dict(o.metadata).get('caller_implementation') != 'vllm_ascend_gdn_decode' for o in targets):
                raise ValueError('helper_source_domain_differs')
            proof = {'evaluation_relation': 'in_sample', 'source_identity': row['source'],
                     'actual_identity': index['actual_identity'], 'native_operator_type': native,
                     'declared_recipe': recipe, 'declared_source_metadata': dict(targets[0].metadata),
                     'declared_contract': predicted_contract(targets[0].to_dict(include_work=False)),
                     'observed_population': observed, 'forward_count': F,
                     'expected_rule_hits': len(targets), 'pooled_native_target_count': len(all_targets),
                     'per_role_timing_separately_observed': len(recipes) == 1,
                     'evidence_strength': 'complete_topology_population_with_source_semantic_boundary',
                     'all_event_native_ABIs_retained': False, 'strict_admission_changed': False,
                     'response_boundary': 'one_complete_source_GDN_helper_call',
                     'compiled_binary_identity_established': False, 'body_residual_used': False,
                     'old_prediction_values_used': False}
            rule = {'id': 'q35-c4-source-helper-' + recipe, 'match': match,
                    'response': {'fixed_us': observed['mean_us']}, 'provenance': proof}
            raw['runtime']['kernels']['service_regimes'].append(rule); additions.append(rule)
    raw['runtime']['metadata']['calibration_evidence']['source_helper_service_rules'] = [r['id'] for r in additions]
    target = OUT / 'cases' / (row['case_id'] + '-gdn-helpers-service.json')
    target.write_text(json.dumps(raw, indent=2) + '\n')
    row.update(sim_case_path=str(target), model_declaration=identity(target),
               variant_id='qwen35-c4-complete-GDN-helper-service-672a595f',
               calibration_evidence=raw['runtime']['metadata']['calibration_evidence'])
    row['replay_input_pins']['case'] = identity(target)
    manifest.update(cases=[row], variant_id=row['variant_id'], baseline_reference=identity(OUT / 'decode-forward-c4-batched-attention-replay.json'))
    (OUT / 'decode-forward-c4-gdn-helpers-cases.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (OUT / 'c4-gdn-helpers-population.json').write_text(json.dumps({
        'schema_version': 'mindie-qwen35-complete-observed-services/1', 'source_identity': row['source'],
        'forward_count': F, 'base_case_identity': previous_case, 'case_identity': identity(target),
        'new_rules': additions, 'raw_capture_reads': 0, 'new_predictions': 0}, indent=2) + '\n')
    print(json.dumps({'case_id': row['case_id'], 'source_GDN_helpers': len(additions), 'unique_native_calls': F*120}))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--extend-c4', action='store_true')
    parser.add_argument('--extend-c4-attention', action='store_true')
    parser.add_argument('--extend-c4-gdn-helpers', action='store_true')
    args = parser.parse_args()
    if args.extend_c4_gdn_helpers:
        extend_c4_gdn_helpers()
    elif args.extend_c4_attention:
        extend_c4_attention()
    elif args.extend_c4:
        extend_c4()
    else:
        build()
