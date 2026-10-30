"""Retained MC2 populations test owner accounting and descriptive constraints."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from export_mc2_source_count_constraints import primitive_counts, response_constraints


@pytest.fixture(scope='module')
def retained():
    path = ROOT / 'data/observations/sources/arch3510-physical-services/mc2-source-count-constraints.json'
    return json.loads(path.read_text())


def test_all_owner_inventories_do_not_replace_busiest_owner(retained):
    for program in retained['source_programs'].values():
        totals, owners = primitive_counts(program['phases'])
        assert dict(totals) == program['source_primitive_counts_all_owners']
        assert {str(k): dict(v) for k, v in owners.items()} == program['source_primitive_counts_by_owner']
        assert {k: max(v.get(k, 0) for v in owners.values()) for k in totals} == program['source_primitive_counts_max_single_owner']
    combine = [p for p in retained['source_programs'].values()
               if p['geometry']['width'] == 3584 and p['kind'] == 'combine']
    combine.sort(key=lambda p: p['geometry']['source_tokens'])
    assert [p['source_primitive_counts_all_owners']['scalar_ub_access'] for p in combine] == [26, 188]
    assert [p['source_primitive_counts_max_single_owner']['scalar_ub_access'] for p in combine] == [26, 26]


def test_compatible_designs_keep_confounded_global_rank_out_of_prices(retained):
    domains = response_constraints(retained['rows'], retained['source_programs'], retained['design_matrix']['rows'])
    assert len(domains) == 8
    assert all(d['point_count'] == 2 and d['design_rank'] == 2 and d['parameter_count'] == 8 for d in domains)
    assert sum(p['event_count'] for d in domains for p in d['points']) == 37480
    assert all(not d['independent_primitive_prices_identifiable'] for d in domains)
    observed = [d for d in domains if d['domain']['width'] == 3584
                and d['domain']['native_operator_type'] == 'MoeDistributeCombineV3'
                and d['domain']['attention_kind'] == 'kda'][0]
    contrast, = observed['contrasts']
    assert contrast['scalar_ub_all_owners_ratio'] == pytest.approx(188/26)
    assert contrast['scalar_ub_max_owner_ratio'] == 1
    assert contrast['observed']['aiv_scalar_time(us)']['signed_diff_us'] < 0
    assert contrast['observed']['aiv_scalar_time(us)']['direction_vs_source_ub_total'] == 'opposite_direction'


def test_incomplete_pmu_cannot_supply_a_whole_population_response(retained):
    rows = deepcopy(retained['rows'])
    row = rows[0]
    row['pmu']['aiv_scalar_time(us)']['numeric_count'] -= 1
    domains = response_constraints(rows, retained['source_programs'], retained['design_matrix']['rows'])
    point, = [p for d in domains for p in d['points'] if p['row_id'] == row['row_id']]
    assert point['observed_mean_us']['aiv_scalar_time(us)'] is None
    contrast, = [c for d in domains for c in d['contrasts'] if c['low_row_id'] == row['row_id']]
    assert contrast['observed']['aiv_scalar_time(us)']['signed_diff_us'] is None
    assert contrast['observed']['aiv_scalar_time(us)']['high_over_low'] is None


def test_joined_histograms_retain_layer_zero_and_exact_native_population(retained):
    assert sum(r['event_count'] for r in retained['rows']) == 37480
    for row in retained['rows']:
        assert sum(n for _, n in row['duration_ns_counter']) == row['event_count']
        assert sum(t*n for t, n in row['duration_ns_counter']) / row['event_count'] / 1000 == pytest.approx(row['observed_us']['mean'])
        assert sum(row['layer_counts'].values()) == row['event_count']
        assert all(n == row['forward_count'] for n in row['layer_counts'].values())
    v41 = [r for r in retained['rows'] if r['case_id'].endswith('tpot5ms_c1')
           and r['native_operator_type'] == 'MoeDistributeDispatchV3']
    assert len({r['source_program_id'] for r in v41}) == 1
    assert {r['layer_population'] for r in v41} == {'layer0', 'steady_layers'}
    assert max(r['pmu']['aiv_mte2_time(us)']['statistics']['mean'] for r in v41) > 10*min(
        r['pmu']['aiv_mte2_time(us)']['statistics']['mean'] for r in v41)
