"""Apply complete normalization, quantization and native HCPost responses.

[Role] Extend all nine GLM sources using existing source-declared physical groups.
[Invariants] Same-shape quant populations are pooled only as an explicit joint
  response. Native HCPost replaces its former semantic node once. No Body fit.
[Timeouts & Locks] One bounded declaration and saved cohort set; no locks.
[Side-Effect Policy] Writes an independent arm, no capture reads or prediction.
"""
from copy import deepcopy
import json

from build_service_cases import HERE, ROOT, pin, read, write, summarize
from build_matrix_slice_pass import plain, scalar_match, make_rule

DEST = HERE / 'norm-quant-post-pass'
PLANS = [
    ('RmsNorm', ['norm1'], 'attention', 45),
    ('RmsNorm', ['norm2'], 'ffn', 45),
    ('DynamicMxQuant', ['gate_up.quantize', 'shared.gate_up.quantize'], 'ffn', 45),
    ('DynamicMxQuant', ['down.quantize'], 'ffn', 3),
    ('DynamicMxQuant', ['shared.down.quantize'], 'ffn', 42),
    ('HcPost', ['attention.hc_post_group'], 'attention', 45),
    ('HcPost', ['ffn.hc_post_group'], 'ffn', 45),
]


def prepare():
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.prediction.operator_analysis import target_graphs
    from mindie_sim.structure_contracts import predicted_contract
    from mindie_sim.structure_subgraphs import subgraph_contract
    from mindie_sim.prediction.family_hc_arch35 import POST_PROFILE, SOURCE

    old_manifest = HERE / 'matrix-slice-pass/decode-forward-service-cases.json'
    manifest = read(old_manifest)
    canonical = ROOT / 'examples/structure/acceptance-20261030-glm-source-complete-operators/body-operator-family-scoreboard.json'
    old = {r['source_case_id']: r for r in read(canonical)['cases']}
    primary = {r['case_id']: r for r in read(HERE / 'observed-populations.json')['cases']}
    rows, populations = [], []
    for original in manifest['cases']:
        row = deepcopy(original); cid = row['case_id']; previous = pin(row['sim_case_path'])
        case = read(previous['path']); prior_rules = deepcopy(case['runtime']['kernels']['service_regimes'])
        opts = case['runtime']['kernels']['lowerings']['native_fusion']['options']
        assert 'hc_post' not in opts['roles']
        opts['roles'].append('hc_post'); opts['traffic_profile']['hc_post'] = POST_PROFILE
        parsed = parse_case(case); g = primary[cid]['geometry']
        ops = target_graphs(parsed, phase='decode', tokens=g['tokens_per_sequence'],
            context=g['context_tokens'], sequences=g['sequences_per_replica'], scope='body')[0]
        contracts = []
        for op in ops:
            meta = dict(op.metadata)
            if meta.get('fusion_role') == 'hc_post':
                contract = subgraph_contract({'role': 'hc_post', 'tensor_view': meta['fusion_tensor_view']})
            else:
                contract = predicted_contract(op.to_dict())
            contracts.append((op, plain(contract)))
        assert len([o for o in ops if dict(o.metadata).get('fusion_role') == 'hc_post']) == 90
        assert not any(o.recipe == 'hc_post_mix' for o in ops)
        ap, mp = old[cid]['actual_identity'], old[cid]['mapping_identity']
        assert pin(ap['path']) == ap and pin(mp['path']) == mp
        actual, mapping = read(ap['path']), read(mp['path'])
        cohorts = [c for w in mapping['windows'] for c in w['cohorts']]
        groups = []
        for native, roles, block, count in PLANS:
            families = [f for f in actual['families'] if f['native_operator_type'] == native and f['declared_role'] in roles]
            stats = summarize(families)
            matched = [c for c in cohorts if c['native_operator_type'] == native and
                set(mapping['conditional_role_by_cohort_id'].get(c['cohort_id'], [])) & set(roles)]
            assert stats['count'] == count * actual['forward_count']
            assert sum(c['complete_event_count'] for c in matched) == stats['count']
            assert sum(c['complete_activity_sum_ns'] for c in matched) == sum(ns*n for ns,n in stats['duration_ns_counter'])
            unique = {json.dumps(c['contract']) for c in matched}; assert len(unique) == 1
            contract = json.loads(unique.pop())
            selected = [o for o,c in contracts if c == contract and dict(o.metadata).get('structure_block') == block]
            assert len(selected) == count, (cid, native, roles, len(selected), count)
            assert len({(o.recipe,o.dtype,o.local_shape) for o in selected}) == 1
            match = scalar_match(selected[0], parsed.machine.sku)
            match['metadata.structure_block'] = block
            if native == 'HcPost':
                match.update({'metadata.fusion_role': 'hc_post',
                    'metadata.fusion_boundary.traffic_profile': POST_PROFILE,
                    'metadata.fusion_tensor_view.hidden': 4096,
                    'metadata.fusion_tensor_view.hc': 4,
                    'metadata.fusion_tensor_view.coefficient_dtype': 'fp32'})
            elif native == 'DynamicMxQuant':
                match.update({'metadata.output_format': 'fp8_e4m3',
                    'metadata.activation_scale_format': 'fp8_e8m0',
                    'metadata.activation_group_size': 32})
            rid = native.lower() + '-' + roles[0].replace('.', '-') + '-complete-native'
            caution = ('Identical source physical shape/dtype and full normalized contract: dense/shared gate-up populations pooled as a count-weighted joint response, not independently identified per-role parameters.'
                       if len(roles) > 1 else 'Complete normalized tensor contract and independently declared block; no Host occurrence, captured binary identity or scalar-value proof.')
            provenance = {'native_operator_type': native, 'declared_roles': roles,
                'actual_identity': ap, 'mapping_identity': mp, 'body_count': actual['forward_count'],
                'normalized_contract': contract, 'boundary_caution': caution}
            case['runtime']['kernels']['service_regimes'].append(make_rule(rid, match, stats, provenance))
            groups.append({'rule_id': rid, 'calls_per_forward': count, 'observed': stats, **provenance,
                'family_indices': [i for i,f in enumerate(actual['families']) if f in families],
                'retained_cohort_ids': [c['cohort_id'] for c in matched],
                'fresh_declared_instances': len(selected), 'physical_block': block,
                'source_profile': POST_PROFILE if native == 'HcPost' else None})
        calibration = {**row['calibration_evidence'], 'evaluation_relation': 'in_sample',
            'regime_count': len(prior_rules)+len(groups), 'source_hc_post_profile': POST_PROFILE}
        case['runtime']['metadata'].update(calibration_origin='observed', calibration_evidence=calibration)
        path = DEST / 'cases' / f'{cid}-norm-quant-post-service.json'; write(path, case)
        row.update(sim_case_path=str(path), model_declaration=pin(path), calibration_evidence=calibration,
            variant_id='observed-norm-quant-post-672a595f', prior_source_case_identity=previous)
        row['replay_input_pins']['case'] = pin(path); rows.append(row)
        populations.append({'case_id': cid, 'case_identity': pin(path), 'prior_case_identity': previous,
            'source_identity': row['source'], 'geometry': g, 'forward_count': actual['forward_count'],
            'prior_rules_unchanged': case['runtime']['kernels']['service_regimes'][:-7] == prior_rules,
            'prior_rule_count': len(prior_rules), 'groups': groups, 'hc_post_source': SOURCE,
            'former_semantic_post_instances_removed': 90, 'native_post_instances_added': 90})
        print(cid, 'seven independent groups;270 native calls/F', flush=True)
    manifest.update(cases=rows, variant_id='observed-norm-quant-post-672a595f')
    write(DEST / 'decode-forward-service-cases.json', manifest)
    write(DEST / 'observed-populations.json', {'schema_version': 'mindie-native-service-populations/1',
        'generator_identity': pin(__file__), 'prior_manifest_identity': pin(old_manifest),
        'cases': populations, 'raw_scans': 0, 'new_costs': 0})


if __name__ == '__main__':
    prepare()
