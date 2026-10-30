"""Add complete matrix cohorts and source-backed packed KDA materializations.

[Role] Bind retained native populations to fresh physical service coordinates.
[Invariants] Prior eleven responses persist. Matrix histograms equal complete
  cohorts; Slice means require full ABI populations, never a mixed-family mean.
  Copy materializations use common tensor lowering and occur once per KDA layer.
[Timeouts & Locks] One small declaration graph and saved population at a time.
[Side-Effect Policy] Local preparation only; no capture reads or cost execution.
"""
from copy import deepcopy
import json

from build_service_cases import HERE, ROOT, ORDER, pin, read, write, summarize

DEST = HERE / 'matrix-slice-pass'
PLANS = [
    ('MatMulV3', 'linear_output', 34), ('MatMulV3', 'index_q', 11),
    ('MatMulV3', 'router', 42), ('QuantBatchMatmulV3', 'gate_up', 3),
    ('QuantBatchMatmulV3', 'down', 3), ('QuantBatchMatmulV3', 'shared.gate_up', 42),
    ('QuantBatchMatmulV3', 'shared.down', 42),
    ('TransposeBatchMatMul', 'q_absorb', 11), ('TransposeBatchMatMul', 'v_expand', 11),
]


def plain(value):
    return json.loads(json.dumps(value))


def scalar_match(op, hardware):
    return {'hardware': hardware, 'recipe': op.recipe, 'dtype': op.dtype,
            **{f'local_shape.{i}': value for i, value in enumerate(op.local_shape)}}


def make_rule(rule_id, match, stats, provenance):
    return {'id': rule_id, 'match': match, 'response': {'fixed_us': stats['mean_us']},
            'provenance': {'basis': 'complete_retained_native_population_mean',
                'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                'count': stats['count'], 'mean_us': stats['mean_us'], 'p50_us': stats['p50_us'],
                'body_residual_used': False, 'response_boundary': 'inclusive_native_call_once',
                **provenance}}


def prepare():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.structure_contracts import predicted_contract

    sources = [HERE / name / 'decode-forward-service-cases.json'
               for name in ('third-pass', 'third-pass-remaining-six')]
    manifests = [read(p) for p in sources]
    entries = {r['case_id']: r for m in manifests for r in m['cases']}
    first_pop = {r['case_id']: r for r in read(HERE / 'observed-populations.json')['cases']}
    canonical = ROOT / 'examples/structure/acceptance-20261030-glm-source-complete-operators/body-operator-family-scoreboard.json'
    old_operators = {r['source_case_id']: r for r in read(canonical)['cases']}
    out, evidence = [], []
    for cid in ORDER:
        row = deepcopy(entries[cid]); previous = pin(row['sim_case_path']); case = read(previous['path'])
        prior_rules = deepcopy(case['runtime']['kernels']['service_regimes'])
        assert len(prior_rules) == 11
        case['runtime'].setdefault('tensor_layouts', {}).update(
            short_convolution={'input': 'contiguous'}, kda_recurrent={'beta': 'contiguous'})
        g = first_pop[cid]['geometry']; actual_pin = old_operators[cid]['actual_identity']
        mapping_pin = old_operators[cid]['mapping_identity']
        actual, mapping = read(actual_pin['path']), read(mapping_pin['path'])
        assert pin(actual_pin['path']) == actual_pin and pin(mapping_pin['path']) == mapping_pin
        assert actual['source_identity']['sha256'] == row['source']['sha256']
        cohorts = [c for w in mapping['windows'] for c in w['cohorts']]
        parsed = parse_case(case)
        ops = target_graphs(parsed, phase='decode', tokens=g['tokens_per_sequence'],
            context=g['context_tokens'], sequences=g['sequences_per_replica'], scope='body')[0]
        contracts = [(op, plain(predicted_contract(op.to_dict()))) for op in ops]
        groups, added = [], []
        for native, role, count in PLANS:
            families = [f for f in actual['families'] if f['native_operator_type'] == native and f['declared_role'] == role]
            stats = summarize(families)
            selected = [c for c in cohorts if c['native_operator_type'] == native and
                        role in mapping['conditional_role_by_cohort_id'].get(c['cohort_id'], [])]
            assert stats['count'] == count * actual['forward_count']
            assert sum(c['complete_event_count'] for c in selected) == stats['count']
            assert sum(c['complete_activity_sum_ns'] for c in selected) == sum(ns*n for ns,n in stats['duration_ns_counter'])
            unique_contracts = {json.dumps(c['contract']) for c in selected}
            assert len(unique_contracts) == 1
            contract = json.loads(unique_contracts.pop())
            fresh = [op for op, current in contracts if current == contract]
            assert len(fresh) == count, (cid, role, 'fresh count', len(fresh), count)
            assert len({(o.recipe, o.dtype, o.local_shape) for o in fresh}) == 1
            match = scalar_match(fresh[0], parsed.machine.sku)
            rid = 'matrix-' + role.replace('.', '-') + '-complete-native'
            provenance = {'native_operator_type': native, 'declared_role': role,
                'actual_identity': actual_pin, 'mapping_identity': mapping_pin,
                'body_count': actual['forward_count'], 'normalized_contract': contract,
                'boundary_caution': 'Complete normalized geometry and whole-layer role; no Host occurrence or captured binary proof.'}
            added.append(make_rule(rid, match, stats, provenance))
            groups.append({'rule_id': rid, 'calls_per_forward': count, 'observed': stats,
                **provenance, 'family_indices': [i for i,f in enumerate(actual['families']) if f in families],
                'retained_cohort_ids': [c['cohort_id'] for c in selected],
                'fresh_declared_instances': len(fresh), 'fresh_recipes': sorted({o.recipe for o in fresh})})
        pmu_path = ROOT / f'data/observations/sources/arch3510-physical-services/scalar-dma-{cid}.json'
        slice_evidence = []
        pmu = read(pmu_path) if pmu_path.exists() else None
        if pmu:
            assert pmu['source_identity']['sha256'] == row['source']['sha256']
            assert pmu['forward_count'] == actual['forward_count']
        M = g['query_rows']
        for recipe, width, layout in [('convolution_input_contiguous', 3072, 'ND'), ('kda_beta_contiguous', 8, 'NCL')]:
            fresh = [o for o in ops if o.recipe == recipe]
            assert len(fresh) == 34
            contract = ['slice_copy', [M, 3336], [M, width], 'bf16', 'bf16']
            assert all(plain(predicted_contract(o.to_dict())) == contract for o in fresh)
            entry = {'recipe': recipe, 'fresh_declared_instances': 34, 'normalized_contract': contract,
                     'status': 'source_materialization_without_separate_observed_population'}
            if pmu:
                abi = ['native_tensor_abi', 'Slice', [[[M,3336], 'bf16', layout], [[2], 'int64', 'ND'], [[2], 'int64', 'ND']],
                       [[[M,width], 'bf16', 'ND']]]
                indices = [i for i,p in enumerate(pmu['partitions']) if p['native_abi'] == abi]
                assert len(indices) == 1
                part = pmu['partitions'][indices[0]]; stats = summarize([part])
                assert stats['count'] == 34 * actual['forward_count']
                match = scalar_match(fresh[0], parsed.machine.sku)
                match.update({'metadata.native_kind': 'Slice', 'metadata.source_layout.strides.0': 3336,
                              'metadata.source_layout.offset': 0 if width == 3072 else 3072})
                rid = recipe + '-complete-native'
                provenance = {'native_operator_type': 'Slice', 'declared_role': recipe,
                    'partition_identity': pin(pmu_path), 'partition_indices': indices,
                    'native_abi': abi, 'normalized_contract': contract, 'body_count': actual['forward_count'],
                    'boundary_caution': 'Input/output storage geometry plus declared contiguous consumer; native scalar offsets not exported. NCL beta input label remains observed and is not silently rewritten to ND.'}
                added.append(make_rule(rid, match, stats, provenance))
                group = {'rule_id': rid, 'observed': stats, 'calls_per_forward': 34, **provenance,
                         'fresh_declared_instances': 34}
                groups.append(group); entry.update(status='observed_response', **group)
            slice_evidence.append(entry)
        case['runtime']['kernels']['service_regimes'].extend(added)
        calibration = {**row['calibration_evidence'], 'evaluation_relation': 'in_sample',
            'regime_count': len(prior_rules)+len(added), 'matrix_population_complete': True,
            'new_slice_responses': sum(e['status'] == 'observed_response' for e in slice_evidence)}
        case['runtime']['metadata'].update(calibration_origin='observed', calibration_evidence=calibration)
        path = DEST / 'cases' / f'{cid}-matrix-slice-service.json'; write(path, case)
        row.update(sim_case_path=str(path), model_declaration=pin(path), calibration_evidence=calibration,
                   variant_id='observed-matrix-slice-672a595f', prior_source_case_identity=previous)
        row['replay_input_pins']['case'] = pin(path)
        out.append(row)
        evidence.append({'case_id': cid, 'case_identity': pin(path), 'prior_case_identity': previous,
            'source_identity': row['source'], 'geometry': g, 'forward_count': actual['forward_count'],
            'prior_eleven_rules_unchanged': case['runtime']['kernels']['service_regimes'][:11] == prior_rules,
            'groups': groups, 'source_materializations': slice_evidence})
        print(cid, 'new rules', len(added), 'slice observed', calibration['new_slice_responses'], flush=True)
    manifest = deepcopy(manifests[0]); manifest.update(cases=out, variant_id='observed-matrix-slice-672a595f')
    write(DEST / 'decode-forward-service-cases.json', manifest)
    write(DEST / 'observed-populations.json', {'schema_version': 'mindie-native-service-populations/1',
        'generator_identity': pin(__file__), 'prior_manifest_identities': [pin(p) for p in sources],
        'cases': evidence, 'raw_scans': 0, 'new_costs': 0})


if __name__ == '__main__':
    prepare()
