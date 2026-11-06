"""A2 native services bind physical contracts without changing caller inputs."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

STRUCT = Path(__file__).resolve().parents[1] / 'examples' / 'structure'
sys.path.insert(0, str(STRUCT))
from a2_native_observations import apply_a2_native_observations


def source_case():
    # The retained capture's normalized geometry, without its model/case labels.
    return {
        'machine': {'backend': 'ascend', 'sku': 'Ascend910B4', 'num_devices': 4, 'ranks_per_node': 4},
        'model': {'name': 'arbitrary-label', 'layers': 3, 'hidden_size': 7168,
            'num_heads': 128, 'num_kv_heads': 1, 'head_dim': 192,
            'intermediate_size': 18432, 'vocab_size': 129280,
            'attention': 'mla', 'ffn': 'dense', 'activation_dtype': 'bf16',
            'quantization': 'w8a8_dynamic', 'mla': {
                'q_lora_rank': 1536, 'kv_lora_rank': 512, 'qk_nope_head_dim': 128,
                'qk_rope_head_dim': 64, 'v_head_dim': 128, 'index_topk': 2048,
                'index_n_heads': 64, 'index_head_dim': 128}},
        'workload': {'num_requests': 1, 'prompt_tokens': 8192, 'output_tokens': 1},
        'runtime': {'tp': 4, 'dp': 1, 'ep': 1, 'pp': 1, 'max_num_seqs': 32,
            'max_num_batched_tokens': 8192, 'graph_mode': 'auto', 'kernels': {
                'service_regimes': [
                    {'id': 'a2-dsv32prune-prefill-dsa-4k',
                     'match': {'phase': 'prefill', 'recipe': 'latent_attention0'},
                     'response': {'fixed_us': 20700}}]}}}


def apply(raw, **geometry):
    return apply_a2_native_observations(raw, **{
        'phase': 'prefill', 'tokens': 8192, 'context': 8192, 'sequences': 1, **geometry})


def test_profile_replaces_only_its_old_boundary_and_is_idempotent_without_mutation():
    raw = source_case()
    original = deepcopy(raw)
    selected, provenance = apply(raw)
    assert raw == original
    assert provenance['status'] == 'applied'
    assert provenance['capture_binary_identity'] == 'unknown'
    rules = selected['runtime']['kernels']['service_regimes']
    assert len(rules) == 14
    assert all(r['id'] != 'a2-dsv32prune-prefill-dsa-4k' for r in rules)
    quant = selected['model']['quant']
    assert quant['index_dtype'] == 'bf16'
    assert quant['category_overrides']['mla_absorb'] == {'weight_format': 'bf16', 'activation_format': 'bf16'}
    assert quant['category_overrides']['dense_mlp']['int8_weight_metadata'] == 'scale_only'
    repeated, again = apply(selected)
    assert repeated == selected and again['status'] == 'applied'
    renamed = deepcopy(raw)
    renamed['name'] = 'different-case'
    renamed['model']['name'] = 'different-model'
    renamed_result, renamed_provenance = apply(renamed)
    assert renamed_result['runtime'] == selected['runtime']
    assert renamed_provenance == provenance


@pytest.mark.parametrize('geometry', [
    {'phase': 'decode', 'tokens': 1}, {'tokens': 4096, 'context': 1},
    {'tokens': 8192, 'context': 122881}, {'sequences': 2}, {'tokens': 2048}])
def test_outside_geometry_does_not_change_base_prediction_declarations(geometry):
    raw = source_case()
    result, provenance = apply(raw, **geometry)
    assert result == raw
    assert provenance['status'] == 'not_applicable'
    result['model']['name'] = 'returned-copy'
    assert raw['model']['name'] == 'arbitrary-label'


@pytest.mark.parametrize('category,fields', [
    ('indexer_fp8', {'activation_format': 'int8'}),
    ('mla', {'weight_format': 'int8'}),
    ('dense_mlp', {'scale_format': 'fp32'}),
    ('dense_mlp', {'int8_weight_metadata': 'scale_offset'})])
def test_explicit_caller_quantization_is_not_overwritten(category, fields):
    raw = source_case()
    raw['model']['quant'] = {'name': 'explicit', 'weight_format': 'int8', 'activation_format': 'int8',
                             'category_overrides': {category: fields}}
    result, provenance = apply(raw)
    assert result == raw
    assert provenance['reason'] == 'explicit_quantization_contract_conflict'


def test_explicit_index_cache_and_native_fusion_bindings_are_preserved():
    raw = source_case()
    raw['model']['quant'] = {'name': 'explicit-cache', 'index_dtype': 'int8'}
    assert apply(raw)[1]['reason'] == 'explicit_quantization_contract_conflict'
    raw = source_case()
    raw['runtime']['kernels']['lowerings'] = {'native_fusion': {
        'implementation': 'declared_native_fusion', 'options': {'roles': []}}}
    result, provenance = apply(raw)
    assert result == raw and provenance['reason'] == 'native_fusion_roles_conflict'


def test_native_services_execute_and_partition_collision_stays_outside_rule_domain():
    from mindie_sim import operator_costs, target_operators
    from mindie_sim.prediction.body_defaults import consume_target_declaration
    from mindie_sim.prediction.structure import parse_case

    selected, _ = apply(source_case(), context=0)
    operators = target_operators(selected, phase='prefill', tokens=8192, context=0)
    parsed = consume_target_declaration(parse_case(selected), operators)
    relevant = tuple(o for o in operators if o.layer == 0 and (
        o.recipe in {'index_q', 'q_absorb', 'v_expand', 'dense_gate_up', 'dense_down', 'latent_attention0'}
        or dict(o.metadata).get('fusion_role') == 'lightning_indexer'))
    rows = operator_costs(parsed, relevant)['operators']
    assert len(rows) == 7
    assert all(row['program'] == 'JointNativeService' for row in rows)
    rules = {r['id']: r for r in selected['runtime']['kernels']['service_regimes']}
    down = next(row for row in rows if row['operator']['recipe'] == 'dense_down')
    assert down['duration_ms'] == pytest.approx(rules['a2-native-gemm-dense_down-q8192']['response']['fixed_us'] / 1000)
    assert down['operator']['metadata']['matrix_epilogue']['column_scale_bytes'] == 7168 * 2
    assert down['analytical_reference_work']['hbm'] > 0

    # Deliberately reuse the selected raw case at an aggregate-work collision;
    # the rule itself, independent of the wrapper, must reject this partition.
    other = target_operators(selected, phase='prefill', tokens=4096, context=2048, sequences=2)
    fused = next(o for o in other if dict(o.metadata).get('fusion_role') == 'lightning_indexer')
    same_work = next(o for o in relevant if dict(o.metadata).get('fusion_role') == 'lightning_indexer')
    assert fused.flops == same_work.flops
    row = operator_costs(parsed, (fused,))['operators'][0]
    assert row['program'] != 'JointNativeService'


def test_profile_keeps_heldout_evidence_out_of_training_responses():
    selected, provenance = apply(source_case())
    training = {s['sha256'] for s in provenance['training_sources']}
    heldout = {s['sha256'] for s in provenance['validation_sources']}
    assert training.isdisjoint(heldout)
    for rule in selected['runtime']['kernels']['service_regimes']:
        events = rule['provenance']['training_events']
        assert events
        assert {event['source_sha256'] for event in events} <= training


@pytest.mark.parametrize('machine', [
    {'device': {'rates': {'native_call_service': 2e9}}, 'devices': [{}, {}, {}, {}]},
    {'dies': [{'rates': {'native_call_service': 2e9}}] * 4},
    {'rates': {'native_call_service': 2e9}},
    {'device': {'work_units': {'native_call_service': 'cycles'}}},
    {'devices': [{}, {}, {'resource_units': {'native_call_service': 2}}, {}]},
])
def test_inherited_or_per_rank_queue_conflicts_preserve_entire_caller(machine):
    raw = source_case()
    raw['machine'].update(machine)
    before = deepcopy(raw)
    selected, provenance = apply(raw)
    assert raw == before and selected == before
    assert provenance['reason'] == 'native_queue_declaration_conflict'


@pytest.mark.parametrize('supply', [
    {'rates': {'hbm': 4e11}}, {'compute_peaks': {'bf16': 1e14}},
    {'service_modes': {'mte1_l0a': {'rate': 4e12}}},
])
def test_physical_supply_miss_preserves_old_response_and_quant_contract(supply):
    raw = source_case()
    raw['machine']['device'] = supply
    before = deepcopy(raw)
    selected, provenance = apply(raw)
    assert raw == before and selected == before
    assert provenance['reason'] == 'native_physical_domain_mismatch'


def decode_source_case():
    raw = source_case()
    raw['runtime'].update(graph_buckets=[1], graph_capture_keys=[1], kv_block_size=128)
    raw['runtime']['kernels']['service_regimes'].append({
        'id': 'a2-dsv32prune-decode-ar', 'match': {'recipe': 'ring_allreduce', 'phase': 'decode'},
        'response': {'fixed_us': 298}})
    return raw


@pytest.mark.parametrize('context', [4096, 32768])
def test_decode_binds_own_native_boundaries_and_preserves_collective_work(context):
    from mindie_sim import operator_costs, target_operators
    from mindie_sim.prediction.body_defaults import consume_target_declaration
    from mindie_sim.prediction.structure import parse_case

    raw = decode_source_case()
    selected, provenance = apply(raw, phase='decode', tokens=1, context=context)
    assert provenance['status'] == 'applied' and provenance['rule_count'] == 10
    rules = selected['runtime']['kernels']['service_regimes']
    assert all(r['id'] != 'a2-dsv32prune-decode-ar' for r in rules)
    # Prefill declarations retain their own phase even during decode selection.
    assert any(r['id'] == 'a2-dsv32prune-prefill-dsa-4k' for r in rules)
    assert not any(r['match'].get('recipe') == 'q_absorb' for r in rules)
    ops = target_operators(selected, phase='decode', tokens=1, context=context)
    parsed = consume_target_declaration(parse_case(selected), ops)
    native = tuple(o for o in ops if o.layer == 0 and o.recipe in {
        'declared_native_fusion', 'latent_attention0', 'index_q', 'v_expand', 'dense_gate_up', 'dense_down'})
    priced = operator_costs(parsed, native, replay_scope='full')['operators']
    assert len(priced) == 6 and all(row['program'] == 'JointNativeService' for row in priced)
    comm = next(o for o in ops if o.layer == 0 and o.recipe == 'ring_allreduce')
    row = operator_costs(parsed, (comm,), replay_scope='full')['operators'][0]
    rule = next(r for r in rules if r['match'].get('recipe') == 'ring_allreduce')
    assert 'execution' not in rule
    assert row['program'] != 'JointNativeService'
    assert comm.link_bytes > 0
    assert row['duration_ms'] == pytest.approx(rule['response']['fixed_us'] / 1000)
    training = {s['sha256'] for s in provenance['training_sources']}
    heldout = {s['sha256'] for s in provenance['validation_sources']}
    assert training.isdisjoint(heldout)
    assert {e['source_sha256'] for r in rules if r['id'].startswith('a2-decode-native-')
            for e in r['provenance']['training_events']} <= training


@pytest.mark.parametrize('change', ['graph', 'transport', 'batch', 'context'])
def test_decode_profile_miss_keeps_existing_inputs_and_responses(change):
    raw = decode_source_case()
    geometry = dict(phase='decode', tokens=1, context=4096)
    if change == 'graph':
        raw['runtime']['graph_capture_keys'] = []
        raw['runtime']['graph_buckets'] = []
    elif change == 'transport':
        raw['machine']['links'] = [{'name': 'changed', 'channel': 'd2d_intra_node',
            'members': [0, 1, 2, 3], 'capacity_bytes_per_ms': 1e8, 'latency_us': 2.5}]
    elif change == 'batch':
        geometry['sequences'] = 2
    else:
        geometry['context'] = 4097
    selected, provenance = apply(raw, **geometry)
    assert selected == raw and provenance['status'] == 'not_applicable'


@pytest.mark.parametrize('phase', ['prefill', 'decode'])
@pytest.mark.parametrize('owners', [
    {'compute_units': 12}, {'resource_units': {'mte2_aiv': 24}},
    {'resource_units': {'vector': 24}},
])
def test_owner_geometry_miss_is_atomic_before_import_and_invalidates_imported_service(phase, owners):
    from mindie_sim import operator_costs, target_operators
    from mindie_sim.prediction.body_defaults import consume_target_declaration
    from mindie_sim.prediction.structure import parse_case

    geometry = (dict(phase='decode', tokens=1, context=4096, sequences=1)
                if phase == 'decode' else dict(phase='prefill', tokens=8192, context=8192, sequences=1))
    raw = decode_source_case() if phase == 'decode' else source_case()
    changed = deepcopy(raw)
    changed['machine']['device'] = owners
    before = deepcopy(changed)
    missed, provenance = apply(changed, **geometry)
    assert missed == changed == before
    assert provenance['reason'] == 'native_physical_domain_mismatch'

    selected, provenance = apply(raw, **geometry)
    assert provenance['status'] == 'applied'
    ops = target_operators(selected, **geometry)
    native = next(o for o in ops if dict(o.metadata).get('fusion_role') == 'lightning_indexer')
    # Change ownership after importing the response. The engine must reject the
    # same retained rule even though aggregate bandwidth and FLOP rates match.
    for key, value in owners.items():
        if isinstance(value, dict):
            selected['machine']['device'].setdefault(key, {}).update(value)
        else:
            selected['machine']['device'][key] = value
    parsed = consume_target_declaration(parse_case(selected), ops)
    row = operator_costs(parsed, (native,), replay_scope='full' if phase == 'decode' else 'none')['operators'][0]
    assert row['program'] != 'JointNativeService'
