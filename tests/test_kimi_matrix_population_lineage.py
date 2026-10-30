"""Whole captured MatMul population survives a saved topology role refresh."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    pytest.importorskip('mindie_sim.cohort_comparison')
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    helper = importlib.import_module('reprice_kimi_matrix_partitions')
    compact = json.loads((ROOT / 'examples/structure/acceptance-20261030-kimi-source-operators/body-operator-family-scoreboard.json').read_text())
    row = next(c for c in compact['cases'] if c['source_case_id'] == 'a5_kimi_tp8_e16_bf16_c32_p4k')
    actual = json.loads(Path(row['actual_identity']['path']).read_text())
    partitions = json.loads((ROOT / 'examples/structure/acceptance-20261030-matrix-fix/a5_kimi_tp8_e16_bf16_c32_p4k-matrix-partitions.json').read_text())
    return helper, row, actual, partitions


def test_saved_role_refresh_can_reuse_full_native_population():
    helper, row, actual, partitions = inputs()
    proof = helper.retained_population_origin(actual, partitions, row['actual_identity'])
    assert proof['basis'] == 'explicit_original_actual_identity_with_unchanged_body_geometry_and_native_histogram'
    assert proof['original_actual_identity'] == actual['original_actual_identity']
    assert proof['previous_actual_identity'] == row['actual_identity']


def test_changed_geometry_or_removed_call_cannot_follow_old_population_pin():
    helper, row, actual, partitions = inputs()
    changed = deepcopy(actual)
    changed['geometry']['sequences_per_replica'] += 1
    with pytest.raises(ValueError, match='matrix_original_population_differs:geometry'):
        helper.retained_population_origin(changed, partitions, row['actual_identity'])
    changed = deepcopy(actual)
    family = next(f for f in changed['families'] if f['native_operator_type'] == 'MatMulV3')
    family['duration_ns_counter'][0][1] += 1
    with pytest.raises(ValueError, match='matrix_role_refresh_changed_native_histogram'):
        helper.retained_population_origin(changed, partitions, row['actual_identity'])


def test_full_paged_abi_without_length_values_is_retained_but_not_strict():
    helper, row, actual, _ = inputs()
    from mindie_sim.structure import export_structure
    part = json.loads((ROOT / 'examples/structure/acceptance-20261030-kimi-paged-fia-pmu/a5_kimi_tp8_e16_bf16_c32_p4k-native-partitions.json').read_text())
    case = json.loads(Path(part['case_identity']['path']).read_text())
    # This is the retained nominal host arm. Neither nominal nor corrected
    # host contexts establish the unobserved per-call length-array values.
    declared_context = case['runtime']['kernels']['lowerings']['paged_mla_attention']['options']['dispatch']['contexts'][0]
    manifest = export_structure(case, phase='decode', tokens=1, sequences=32,
        context=declared_context, scope='body')
    previous = json.loads(Path(row['mapping_identity']['path']).read_text())
    cohorts, _, families, decisions = helper.matrix_mapping(part, previous, manifest, 'FusedInferAttentionScore')
    assert not cohorts
    assert sum(f['observed_us']['count'] for f in families) == 1104
    assert len(decisions) == 1
    assert decisions[0]['reason'] == 'paged_attention_sequence_values_unavailable_for_strict_physical_work'
    assert dict(families[0]['duration_ns_counter']) == dict(next(g['duration_ns_counter'] for g in part['partitions']
        if g['native_operator_type'] == 'FusedInferAttentionScore'))
