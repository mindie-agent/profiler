"""Bind retained indexer and routing calls to existing semantic fusion regions.

[Role] Prepare an independent A3 tail-service arm from the typed V2 baseline.
[Invariants] Complete native populations and fresh active contracts agree before
  one local joint response replaces each fused region. No Body residual is used.
[Timeouts & Locks] Three bounded metadata exports; no cost, raw reads or locks.
[Side-Effect Policy] Write owned cases/proof only; leave Sim and older arms intact.
"""
from copy import deepcopy
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match
from build_glm78_joint_service_cases import EXECUTION, pooled
from build_glm78_native_service_cases import descriptor, freeze
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.structure_subgraphs import subgraph_contract


HERE = Path(__file__).resolve().parent
BASE = HERE / 'acceptance-20261030-glm78-native-v2-service/decode-forward-glm78-native-v2-cases.json'
NATIVE = HERE / 'acceptance-20261030-service-qwen-a3/glm78-native'
OUT = HERE / 'acceptance-20261030-a3-tail-service-refinement/glm78-indexer-routing'
ROLES = {'LightningIndexer': ('lightning_indexer', 21),
         'MoeGatingTopK': ('router_selection', 75)}


def select_native_region(case, ops, groups, role, expected, forward_count):
    """Require the entire observed ABI bucket and declared region population."""
    contracts = {freeze(observed_contract(descriptor(group['native_abi']))) for group in groups}
    if None in contracts or len(contracts) != 1:
        raise ValueError('native_region_active_contract_not_unique')
    contract = next(iter(contracts))
    selected = []
    for op in ops:
        meta = dict(op.metadata)
        if meta.get('fusion_role') != role:
            continue
        actual = freeze(subgraph_contract({'role': role, 'tensor_view': meta['fusion_tensor_view']}))
        if actual != contract:
            raise ValueError('declared_native_region_contract_differs')
        if op.link_bytes or meta.get('device_kernel_group'):
            raise ValueError('joint_region_is_not_single_local_kernel')
        selected.append(op)
    stats = pooled(groups)
    if len(selected) != expected or stats['count'] != expected * forward_count:
        raise ValueError('native_region_population_differs')
    # Full native tensors remain in evidence. Matching uses physical axes and
    # active descriptor equality; names and layer IDs never select a response.
    matches = []
    for op in selected:
        match = _physical_match(case, op)
        match['metadata.fusion_role'] = role
        view = dict(op.metadata)['fusion_tensor_view']
        for key, value in view.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                match['metadata.fusion_tensor_view.' + key] = value
        matches.append(match)
    if any(match != matches[0] for match in matches):
        raise ValueError('heterogeneous_native_region_cannot_split_histogram')
    return stats, matches[0], selected, contract


def build():
    manifest = read(BASE); output = deepcopy(manifest); output['cases'] = []; proofs = []
    for row in manifest['cases']:
        raw = read(row['sim_case_path']); prior = deepcopy(raw['runtime']['kernels']['service_regimes'])
        geometry = row['replay_input_pins']['primary_geometry']
        native_path = NATIVE / f"{row['case_id']}-native-partitions.json"
        native = read(native_path)
        if native['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('native_source_identity_differs')
        options = raw['runtime']['kernels']['lowerings']['native_fusion']['options']
        for role, _ in ROLES.values():
            if role not in options['roles']: options['roles'].append(role)
        case, ops = physical_ops(raw, geometry); added = []
        for kind, (role, calls) in ROLES.items():
            indexed = [(i,g) for i,g in enumerate(native['partitions']) if g['native_operator_type'] == kind]
            groups = [g for _,g in indexed]
            stats, match, selected, contract = select_native_region(case, ops, groups, role, calls, native['forward_count'])
            rid = kind.lower() + '-complete-native-tail-joint'
            evidence = {'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                'native_operator_type': kind, 'native_identity': identity(native_path),
                'source_identity': native['source_identity'], 'partition_indices': [i for i,_ in indexed],
                'full_native_abis': [g['native_abi'] for g in groups], 'active_contract': contract,
                'complete_population': stats, 'forward_count': native['forward_count'],
                'expected_rule_hits': calls, 'declared_fusion_role': role,
                'source_target_ids': [op.op_id for op in selected],
                'response_boundary': 'single_local_native_whole_call_inclusive_once',
                'body_residual_used': False, 'strict_tensor_admission_changed': False,
                'occurrence_binding_implied': False,
                'auxiliary_output_boundary': ('Captured third FP32 score output remains in the full ABI; '
                    'active selection contract identifies the whole fused score/selection/normalization provider.'
                    if kind == 'MoeGatingTopK' else 'Captured optional second output is retained; sparse index output defines the active result.'),
                'unknowns': ['Scalar inputs, exact binary implementation and native internal tiling are not observed.']}
            raw['runtime']['kernels']['service_regimes'].append({'id': rid, 'match': match,
                'response': {'fixed_us': stats['mean_us']},
                'execution': {**EXECUTION, 'native_kernel': kind}, 'provenance': evidence})
            added.append({'rule_id': rid, 'match': match, **evidence})
        if raw['runtime']['kernels']['service_regimes'][:len(prior)] != prior:
            raise ValueError('prior_response_changed')
        target = OUT / 'cases' / f"{row['case_id']}-indexer-routing-joint.json"; write(target, raw)
        new = deepcopy(row); new.update(sim_case_path=str(target), model_declaration=identity(target),
            variant_id='glm78-v2-indexer-routing-joint')
        new['replay_input_pins']['case'] = identity(target)
        new['calibration_evidence']['tail_native_responses'] = [
            {k:r[k] for k in ('rule_id','native_operator_type','expected_rule_hits')} for r in added]
        output['cases'].append(new)
        proofs.append({'case_id':row['case_id'],'source_identity':native['source_identity'],
            'prior_case_identity':identity(row['sim_case_path']), 'case_identity':identity(target),
            'geometry':geometry,'forward_count':native['forward_count'],
            'prior_rules_unchanged':True,'prior_rule_count':len(prior),'added_rules':added})
    output['baseline_identity'] = identity(BASE); output['variant_id'] = 'glm78-v2-indexer-routing-joint'
    write(OUT / 'decode-forward-glm78-tail-cases.json', output)
    write(OUT / 'tail-native-input-proof.json', {'schema_version':'mindie-native-tail-service/1',
        'producer_identity':identity(__file__),'cases':proofs,'raw_reads':0,'new_cost_predictions':0})
    print(json.dumps([{'case_id':p['case_id'],'forward_count':p['forward_count'],
        'rules':[(r['native_operator_type'],r['expected_rule_hits'],r['complete_population']['mean_us'])
                 for r in p['added_rules']]} for p in proofs]))


if __name__ == '__main__': build()
