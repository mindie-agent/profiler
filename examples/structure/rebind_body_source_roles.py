"""Rebind complete retained native-ABI partitions to fresh source-role programs.

[Role] Reuse MC2 native ABI histograms without rereading raw profiling events.
[Invariants] The original source-role key includes the complete native ABI in
  source_correspondence. Re-select all saved layers through the existing source
  selector; never split an aggregate or substitute signatures without validation.
  Buffer capacity remains distinct from unknown valid rows and mask/count values.
[Timeouts & Locks] Bounded manifest/group metadata only; no I/O, cost or locks.
[Side-Effect Policy] Return new declarations while preserving all measured fields.
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

from body_source_role_references import canonical, reference_signature, routed_ffn_reference


def freeze(value):
    return tuple(freeze(item) for item in value) if isinstance(value, (list, tuple)) else value


def rebind_frozen_native_groups(actual, manifest):
    """Return (actual_with_groups, records); unsupported groups stay unchanged.

    Only DispatchFFNCombine groups are eligible. Their original aggregation key
    includes the full eight-input/two-output ABI and correspondence, in addition
    to the old physical program. The saved histogram therefore belongs to this
    ABI across every saved layer, rather than only the two example occurrences.
    Downstream physical validation still excludes any unchanged ineligible group.
    """
    layers = defaultdict(list)
    for target in manifest['nodes']:
        if target.get('event_matchable') is not False:
            layers[target['replica'], target.get('layer')].append(target)
    groups, records = [], []
    for group in actual.get('source_role_references', ()):
        if group['native_operator_type'] != 'DispatchFFNCombine':
            groups.append(group)
            continue
        record = {'old_group_id': group['group_id'], 'native_operator_type': group['native_operator_type'],
                  'declared_role': group['declared_role'], 'event_count': group['observed_us']['count'],
                  'layer_ids': group['layer_ids'], 'raw_capture_reads': 0,
                  'observed_histogram_partition': 'unchanged',
                  'evidence_strength': 'conditional_source_role_reference'}
        relation = group.get('source_correspondence', {})
        native = freeze(relation.get('observed_native_tensor_contract'))
        reason = None
        if (not native or len(native) != 4 or native[:2] != ('native_tensor_abi', 'DispatchFFNCombine')
                or group['declared_role'] != 'routed_ffn_native' or group['block'] != 'ffn'
                or not group['layer_ids']):
            reason = 'complete_native_abi_or_whole_routed_boundary_not_retained'
        selected, first_key = None, None
        if reason is None:
            for layer_id in group['layer_ids']:
                candidate = routed_ffn_reference(native, layers[group['representative_replica'], layer_id])
                if candidate is None:
                    reason = 'native_abi_no_longer_matches_declared_routed_roles'
                    break
                role, targets, declaration, correspondence = candidate
                targets = sorted(targets, key=lambda target: target['node_id'])
                signature = [(reference_signature(target), target['physical_work']) for target in targets]
                key = canonical((group['native_operator_type'], group['native_name'], role,
                                 declaration, correspondence, signature))
                if first_key is not None and key != first_key:
                    reason = 'fresh_physical_program_heterogeneous_cannot_split_retained_histogram'
                    break
                if selected is None:
                    selected = role, targets, declaration, correspondence
                    first_key = key
        if reason is not None:
            groups.append(group)
            records.append({**record, 'status': 'not_rebound', 'reason': reason})
            continue
        role, targets, declaration, correspondence = selected
        group_id = 'sha256:' + sha256(first_key.encode()).hexdigest()
        rebound = {**group, 'group_id': group_id, 'declared_role': role,
            'source_anchor_declaration': declaration, 'source_correspondence': correspondence,
            'representative_target_ids': [target['node_id'] for target in targets],
            'physical_program_signatures': [target['physical_signature'] for target in targets],
            'physical_work_per_program': [target['physical_work'] for target in targets],
            'frozen_native_rebind': {
                'basis': 'complete_retained_native_abi_revalidated_by_source_selector_for_every_saved_layer',
                'original_observation_group_id': group['group_id'],
                'native_abi_sha256': sha256(canonical(native).encode()).hexdigest(),
                'new_graph_id': manifest['graph_id'], 'validated_layer_ids': group['layer_ids'],
                'original_grouping_included_complete_native_abi': True,
                'observation_histogram_unchanged': True, 'raw_capture_reads': 0,
                'strict_tensor_cohort_implied': False, 'new_physical_work_from_manifest': True}}
        groups.append(rebound)
        records.append({**record, 'status': 'rebound', 'group_id': group_id,
                        'new_graph_id': manifest['graph_id'],
                        'declared_routed_program_count': len(targets),
                        'observed_buffer_row_capacity': correspondence['observed_buffer_row_capacity'],
                        'observed_valid_routed_rows': None,
                        'declared_valid_routed_rows': correspondence['declared_valid_routed_rows']})
    return {**actual, 'source_role_references': groups}, records
