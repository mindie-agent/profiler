"""Saved complete HCOM populations exercise residual coverage, not timing fits."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SAVED = ROOT / 'examples/structure/acceptance-20261030-hccl-aicpu-ts-reference'


def real_reduce_scatter(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    module = importlib.import_module('residual_mechanism_ledger')
    case = json.loads((SAVED / 'source-caller-reference-scoreboard.json').read_text())['cases'][0]
    groups = [g for g in case['groups'] if g['native_operator_type'] == 'hcom_reduceScatter_']
    observed = module.Counter()
    refs = []
    for group in groups:
        observed.update(module.histogram(group['duration_ns_counter']))
        refs.append({'observed_us': group['observed_us'], 'roles': [group['declared_role']],
            'layer_ids': group['layer_ids'], 'duration_ns_counter': group['duration_ns_counter'],
            'observation_identity_domain': 'source_symbol_retained_group',
            'population_partition_identity': case['partition_identity'],
            'population_partition_kind': 'retained_group',
            'population_partition_members': [group['retained_group_id']],
            'receipt': {'sha256': 'same-retained-reference'}, 'group_id': group['group_id']})
    return module, observed, refs


def test_complete_reference_histograms_and_exact_duplicate_are_not_double_counted(monkeypatch):
    module, observed, refs = real_reduce_scatter(monkeypatch)
    duplicate = deepcopy(refs[0]); duplicate['group_id'] = 'another-receipt-same-population'
    primary, coverage = module.cost_coverage(observed, [], [*refs, duplicate], [])
    assert sum(r['observed_us']['count'] for r in primary) == 1760
    assert coverage['additional_reference_calls'] == 1760 and coverage['uncovered_calls'] == 0
    assert 'duplicate_same_role_layer_histogram' in coverage['reference_overlap_exclusions']


def test_partial_strict_population_keeps_overlapping_real_references_outside_coverage(monkeypatch):
    module, observed, refs = real_reduce_scatter(monkeypatch)
    # Controlled classifier projection of one real, independently retained group.
    # It tests coverage only; it does not upgrade the saved conditional capture.
    strict_part = {'observed_us': refs[0]['observed_us']}
    primary, coverage = module.cost_coverage(observed, [strict_part], refs, [])
    assert primary == [strict_part]
    assert coverage['additional_reference_calls'] == 0
    assert coverage['uncovered_calls'] == 1760 - strict_part['observed_us']['count']
    assert set(coverage['reference_overlap_exclusions']) == {'partial_strict_overlap_not_resolved_from_retained_histograms'}


def test_histogram_capacity_alone_does_not_prove_cross_receipt_event_disjointness(monkeypatch):
    module, observed, refs = real_reduce_scatter(monkeypatch)
    repeated_layers = [r for r in refs if r['layer_ids'] == [1, 2]]
    assert len(repeated_layers) == 2
    repeated_layers[1]['population_partition_identity'] = {'sha256': 'different-retained-population'}
    primary, coverage = module.cost_coverage(observed, [], repeated_layers, [])
    assert len(primary) == 1
    assert 'cross_partition_occurrence_overlap_unproven_not_added' in coverage['reference_overlap_exclusions']


def test_complete_multi_component_alternative_does_not_stop_after_its_first_group(monkeypatch):
    module, observed, refs = real_reduce_scatter(monkeypatch)
    # These are six real disjoint retained populations; the fallback must retain
    # the entire complete set even when its event-level histogram is unavailable.
    primary, coverage = module.cost_coverage(observed, [], [], refs)
    assert len(primary) == 6
    assert coverage['additional_reference_calls'] == 1760
    assert coverage['uncovered_calls'] == 0


def test_fixed_body_boundary_selection_uses_requested_cases_and_relative_gap(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    module = importlib.import_module('residual_mechanism_ledger')
    fixture = json.loads((ROOT / 'tests/fixtures/source_callers/residual-body-selection-9f10558.json').read_text())
    cases, ranked = module.choose_cases(fixture['rows'])
    a3 = [c['case_id'].split(':')[0] for c in cases if c['selection_group'].startswith('A3')]
    assert a3 == ['v4flash-a3-tp8-c4', 'a3_kimi4_tp8_w4a8_c32',
                  'a3_glm53_w4a8_tp16_tpot88_c8', 'a3_kimi4_tp8_w4a8_c1']
    assert ranked[0]['case_id'].startswith('v4flash-a3-tp8-c4:')


@pytest.mark.parametrize(('fixture_name', 'calls'), [
    ('residual-kimi-mc2-partition.json', 4232), ('residual-v41-grouped-partition.json', 2920),
])
def test_real_native_group_resolves_actual_namespace_and_validates_full_population(monkeypatch, fixture_name, calls):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    module = importlib.import_module('residual_mechanism_ledger')
    fixture = json.loads((ROOT / 'tests/fixtures/source_callers' / fixture_name).read_text())
    raw, actual = fixture['raw'], fixture['actual']
    result = module.source_role_partition(raw, actual, fixture['actual_identity'])
    assert result['partition_identity'] == fixture['actual_identity']
    assert result['partition_identity']['sha256'] != fixture['partition_identity']['sha256']
    assert result['partition_kind'] == 'source_role_group'
    assert result['partition_members'] == [raw.get('retained_observation_group_id') or raw['retained_group_id']]
    assert sum(n for _, n in raw['duration_ns_counter']) == calls
    changed = deepcopy(actual)
    changed['source_role_references'][0]['duration_ns_counter'][0][1] += 1
    with pytest.raises(ValueError, match='source_role_partition_population_differs'):
        module.source_role_partition(raw, changed, fixture['actual_identity'])
