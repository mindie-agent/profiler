"""Actual FIA/MC2 raw PMU fields keep zeros, NA and long scalar activity distinct."""
import importlib
from dataclasses import replace
from pathlib import Path
import sys

from mindie_profiler.normalized import kernel_rows
from mindie_profiler.sources_csv import probe_csv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
pmu = importlib.import_module('targeted_native_pmu')


def test_raw_counter_stream_reuses_exact_decoder_and_retains_missing_zero():
    path = ROOT / 'tests/fixtures/native_body_contracts/kimi_a5_fia_mc2_pmu.csv'
    schema = probe_csv(path)
    kinds = {'MoeDistributeDispatchV3', 'MoeDistributeCombineV3', 'FusedInferAttentionScore'}
    rows = list(pmu.scan_rows(path, schema, kinds))
    regular = list(kernel_rows(path, rank_id='rank_0', rank_index=0))
    assert [(r.event.identity(), r.duration_ns) for r, _ in rows] == [
        (r.event.identity(), r.duration_ns) for r in regular]
    combine, raw = next((r, raw) for r, raw in rows if r.kind == 'MoeDistributeCombineV3')
    group = pmu.NativePmu(schema.header)
    group.add(raw, combine.event, forward_id='bounded_fixture', layer_id=1)
    result = group.result()
    assert result['fields']['aiv_scalar_time(us)']['statistics']['mean'] == 16.853
    assert result['fields']['Duration(us)']['statistics']['mean'] == 32.140
    zero = [r for r in result['fields'].values() if r['zero_count']]
    assert zero and all(r['statistics']['count'] == 1 and r['statistics']['mean'] == 0 for r in zero)
    # An exporter NA for the same real zero must change availability, not add
    # another zero to the numerical population.
    zero_name = next(name for name, field in result['fields'].items() if field['zero_count'])
    group.add({**raw, zero_name: 'N/A'}, combine.event, forward_id='missing_export', layer_id=1)
    field = group.result()['fields'][zero_name]
    assert field['missing_or_na_count'] == 1 and field['zero_count'] == 1
    assert field['statistics']['count'] == 1
    assert result['longest_calls'][0]['locator'] == combine.event.locator


def test_repeated_task_ids_remain_distinct_events_and_full_tail_is_retained():
    path = ROOT / 'tests/fixtures/native_body_contracts/kimi_a5_fia_mc2_pmu.csv'
    schema = probe_csv(path); group = pmu.NativePmu(schema.header)
    rows = list(pmu.scan_rows(path, schema, {'MoeDistributeDispatchV3', 'MoeDistributeCombineV3'}))
    for row, raw in rows:
        if raw is not None:
            raw = {**raw, 'Task ID': 'replayed-task-id'}
            event = replace(row.event, task_id='replayed-task-id',
                locator={**row.event.locator, 'task_id': 'replayed-task-id'})
            group.add(raw, event, forward_id='bounded_fixture', layer_id=1)
    result = group.result()
    assert result['event_count'] == 2
    assert len({e['event_id'] for e in result['longest_calls']}) == 2
    assert result['fields']['Duration(us)']['statistics']['max'] == 32.140
    assert result['fields']['Duration(us)']['statistics']['count'] == 2
