"""Real A3 Kimi TP8 HCOM populations retain controllers outside service refs."""
import importlib
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
ACCEPTANCE = ROOT / 'examples/structure/acceptance-20261030-hccl-aicpu-ts-reference'


def inputs(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'examples/structure'))
    prepare = importlib.import_module('source_caller_references').prepare_hccl
    ledger = json.loads((ACCEPTANCE / 'a3_kimi4_tp8_w4a8_c32-retained-hccl.json').read_text())
    manifest = json.loads((ROOT / 'tests/fixtures/source_callers/kimi4-c32-aicpu-ts-programs.json').read_text())['manifest']
    return prepare, ledger, manifest


def test_real_a3_allgather_reduce_scatter_keep_full_hcom_histograms_and_controller_separation(monkeypatch):
    prepare, ledger, manifest = inputs(monkeypatch)
    refs, failures, costs, compact = prepare(ledger, manifest)
    assert len(refs) == 11 and len(costs) == 2
    assert sum(r['observed_us']['count'] for r in refs) == 3300
    assert failures == [{'native_operator_type': 'hcom_allGather_', 'retained_group_id': 'groups/14',
                         'event_count': 440, 'reason': 'collective_region_not_one_declared_call_per_layer_forward'}]
    for row in refs:
        saved = ledger['groups'][int(row['retained_group_id'].split('/')[1])]
        assert row['duration_ns_counter'] == saved['duration_ns_counter']
        assert row['observed_us'] == saved['observed_us']
        assert saved['accelerator_core'] == 'COMMUNICATION'
        assert saved['event_category'] == 'collective_envelope_only'
        assert row['source_correspondence']['observed_device_engine'] is None
        assert row['source_correspondence']['measured_payload_bytes'] is None
        assert not row['source_correspondence']['template_selection_confirmed']
    assert any(g['accelerator_core'] == 'AI_CPU' for g in ledger['groups'])
    assert not any(r['native_operator_type'].endswith('AicpuKernel') for r in refs)
    selected = {n['node_id']: n for n in compact['nodes']}
    for group in costs:
        nodes = [selected[key] for key in group['representative_target_ids']]
        assert {n['family'] for n in nodes} == {'hccl_boundary', 'hccl_local', 'alltoallv'}
        assert nodes[0]['recipe'] == 'hccl_entry' and nodes[-1]['recipe'] == 'hccl_exit'
        assert len([n for n in nodes if n['recipe'] == 'hccl_source_peer_exchange']) == 1


def test_hcom_envelope_cannot_upgrade_to_observed_aiv_template(monkeypatch):
    prepare, ledger, manifest = inputs(monkeypatch)
    for node in manifest['nodes']:
        node['operator']['metadata']['hccl_selection']['expansion'] = 'AIV'
    refs, failures, costs, _ = prepare(ledger, manifest)
    assert refs == costs == []
    assert sum(row['event_count'] for row in failures) == 3740
    assert sum(row['event_count'] for row in failures
               if row['reason'] == 'AIV_reference_requires_retained_AIV_device_task') == 3300
