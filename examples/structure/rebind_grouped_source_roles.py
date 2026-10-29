"""Revalidate retained GroupedMatmul ABI populations against fresh FFN programs.

[Role] Restore conditional expert-up/down references from complete ABI buckets.
[Invariants] Shared native tensor parsing validates every slot. Expert/weight axes
  and the already aligned FFN role select programs; capacity M never becomes valid
  routing counts. A changed per-layer program cannot split one saved histogram.
[Timeouts & Locks] Bounded group/layer descriptors; no cost, raw scans or locks.
[Side-Effect Policy] Return new reference declarations; preserve measured facts.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from types import SimpleNamespace

from mindie_profiler.body_matrix_contracts import observed_matrix_contract
from mindie_profiler.native_tensor_abi import native_tensor_contract
from body_source_role_references import canonical, reference_signature
from rebind_body_source_roles import freeze


def retained_descriptor_row(native):
    """Adapt saved descriptors to the shared parser without inventing an Event."""
    if not native or len(native) != 4 or native[:2] != ('native_tensor_abi', 'GroupedMatmul'):
        return None
    fields = {'kind': native[1]}
    for direction, slots in zip(('input', 'output'), native[2:]):
        fields[direction+'_shapes'] = tuple(slot[0] for slot in slots)
        fields[direction+'_dtypes'] = tuple(slot[1] if slot[1] is not None else 'DT_UNDEFINED' for slot in slots)
        fields[direction+'_formats'] = tuple(slot[2] if slot[2] is not None else 'NULL' for slot in slots)
    row = SimpleNamespace(**fields)
    return row if native_tensor_contract(row) == native else None


def select_grouped_reference(native, local, subgraphs, role):
    row = retained_descriptor_row(native)
    contract = observed_matrix_contract(row) if row is not None else None
    if contract is None or contract[0] != 'grouped_matrix' or role not in {'expert_up', 'expert_down'}:
        return None
    experts, capacity, n, k = contract[1]
    selected = []
    for target in local:
        expected = target.get('contract')
        if (target.get('block') == 'ffn' and expected and expected[0] == 'grouped_matrix'
                and tuple(expected[1][::2]) == (experts, n) and expected[1][3] == k
                and tuple(expected[2:5]) == contract[2:5]
                and tuple(expected[5][1:]) == contract[5][1:] and expected[6] == contract[6]):
            selected.append(target)
    if len(selected) != 1 or selected[0]['op_id'].rsplit('.', 1)[-1] != role:
        return None
    target = selected[0]
    source = next((subgraph.get('source') for subgraph in subgraphs
                   if target['node_id'] in subgraph['node_ids'] and subgraph.get('source')), None)
    return target, {'kind': 'validated_native_expert_weight_axes', 'source': source}, {
        'boundary_relation': 'capacity_vs_valid_rows_conditional',
        'observed_buffer_row_capacity': capacity,
        'declared_valid_routed_rows': target['contract'][1][1],
        'observed_valid_routed_rows': None, 'observed_group_list_values': None,
        'validated_geometry': {'expert_banks': experts, 'output_width': n, 'input_width': k,
                               'operand_output_dtypes': contract[2:5]},
        'observed_native_tensor_contract': native,
        'prediction_coverage': target.get('contract_scope'),
        'limitations': ['Buffer capacity does not prove valid routed FLOPs or active expert counts.',
                        'Native MXFP4 service/conversion coverage follows the declared program.']}


def rebind_frozen_grouped_groups(actual, manifest):
    """Return new groups and audit records, without changing non-GroupedMatmul groups."""
    layers, subgraphs = defaultdict(list), defaultdict(list)
    for target in manifest['nodes']:
        if target.get('event_matchable') is not False:
            layers[target['replica'], target.get('layer')].append(target)
    for target in manifest.get('subgraphs', ()):
        subgraphs[target['replica'], target.get('layer')].append(target)
    groups, records = [], []
    for group in actual.get('source_role_references', ()):
        if group['native_operator_type'] != 'GroupedMatmul':
            groups.append(group)
            continue
        record = {'old_group_id': group['group_id'], 'native_operator_type': 'GroupedMatmul',
                  'declared_role': group['declared_role'], 'event_count': group['observed_us']['count'],
                  'layer_ids': group['layer_ids'], 'raw_capture_reads': 0,
                  'observed_histogram_partition': 'unchanged',
                  'evidence_strength': 'conditional_source_role_reference'}
        native = freeze(group.get('source_correspondence', {}).get('observed_native_tensor_contract'))
        reason, representative, first_key = None, None, None
        if not group['layer_ids'] or group['block'] != 'ffn':
            reason = 'complete_ffn_layer_population_not_retained'
        else:
            for layer in group['layer_ids']:
                index = group['representative_replica'], layer
                selection = select_grouped_reference(native, layers[index], subgraphs[index], group['declared_role'])
                if selection is None:
                    reason = 'native_grouped_abi_no_longer_matches_unique_expert_role'
                    break
                target, declaration, correspondence = selection
                key = canonical(('GroupedMatmul', group['native_name'], group['declared_role'],
                                 declaration, correspondence,
                                 [(reference_signature(target), target['physical_work'])]))
                if first_key is not None and key != first_key:
                    reason = 'fresh_physical_program_heterogeneous_cannot_split_retained_histogram'
                    break
                if representative is None:
                    representative, first_key = selection, key
        if reason is not None:
            groups.append(group)
            records.append({**record, 'status': 'not_rebound', 'reason': reason})
            continue
        target, declaration, correspondence = representative
        group_id = 'sha256:' + sha256(first_key.encode()).hexdigest()
        groups.append({**group, 'group_id': group_id, 'source_anchor_declaration': declaration,
            'source_correspondence': correspondence, 'representative_target_ids': [target['node_id']],
            'physical_program_signatures': [target['physical_signature']],
            'physical_work_per_program': [target['physical_work']],
            'frozen_native_rebind': {
                'basis': 'complete_retained_grouped_abi_revalidated_against_every_aligned_layer_expert_role',
                'original_observation_group_id': group['group_id'],
                'native_abi_sha256': sha256(canonical(native).encode()).hexdigest(),
                'new_graph_id': manifest['graph_id'], 'validated_layer_ids': group['layer_ids'],
                'original_grouping_included_complete_native_abi': True,
                'observation_histogram_unchanged': True, 'raw_capture_reads': 0,
                'strict_tensor_cohort_implied': False, 'new_physical_work_from_manifest': True}})
        records.append({**record, 'status': 'rebound', 'group_id': group_id,
                        'new_graph_id': manifest['graph_id'], 'declared_program_count': 1,
                        'observed_buffer_row_capacity': correspondence['observed_buffer_row_capacity'],
                        'observed_valid_routed_rows': None,
                        'declared_valid_routed_rows': correspondence['declared_valid_routed_rows']})
    return {**actual, 'source_role_references': groups}, records
