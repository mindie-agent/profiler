"""Complete real cohorts retain actual Engine execution of calibrated service."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim", reason="companion Sim acceptance tools require the optional runtime")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples/structure'))
from operator_service_evidence import service_execution_evidence
from replay_fusion_cohorts import _compact_comparison


def test_public_complete_tensor_cohort_executes_joint_service_once():
    sim = pytest.importorskip('mindie_sim')
    from mindie_sim.cohort_comparison import compare_cohorts
    from mindie_sim.structure import export_structure
    from reprice_body_operator_families import rebind_mapping

    retained = ROOT / 'examples/structure/acceptance-20261030-qwen35-source-complete/canonical-with-tensor-move'
    mapping = json.loads(next(retained.glob('*c128*.mapping.json')).read_text())
    cohort = next(c for c in mapping['windows'][0]['cohorts'] if c['native_operator_type'] == 'TensorMove')
    mapping['windows'][0]['cohorts'] = [cohort]
    case_path = Path(sim.__file__).resolve().parents[1] / 'examples/cases/high-concurrency-20261030/qwen35-mc2-tp-source-complete-conditional/qwen35-35b-a5-tp4-c128-mc2-tp-source-complete.json'
    if not case_path.exists():
        pytest.skip('companion real Qwen35 case unavailable')
    case = json.loads(case_path.read_text())
    geometry = {k: mapping['declared_execution'][k] for k in ('phase', 'tokens', 'context', 'sequences', 'scope')}
    manifest = export_structure(case, **geometry)
    target = next(n for n in manifest['nodes'] if n['node_id'] == cohort['target_ids'][0])
    operator = target['operator']
    match = {'recipe': operator['recipe'], 'phase': 'decode', 'dtype': operator['dtype'],
             **{f'local_shape.{i}': n for i, n in enumerate(operator['local_shape'])}}
    mean_us = cohort['duration_ns']['mean'] / 1000
    case['runtime']['kernels']['service_regimes'] = [{
        'id': 'retained-complete-copy', 'match': match, 'response': {'fixed_us': mean_us},
        'execution': {'kind': 'joint_native', 'resource': 'observed_copy',
                      'reference_rate': 1e9, 'native_kernel': 'TensorMove'},
        'provenance': {'evaluation_relation': 'in_sample', 'calibration_origin': 'observed',
                       'body_residual_used': False, 'source_identity': mapping['windows'][0]['source_identity']},
    }]
    device = case['machine'].setdefault('device', {})
    for field, value in [('rates', 1e9), ('work_units', 'busy_ns'), ('resource_units', 1)]:
        device.setdefault(field, {})['observed_copy'] = value
    fresh = export_structure(case, **geometry)
    rebound, _ = rebind_mapping(mapping, fresh, mapping['windows'][0]['source_identity'])
    result = compare_cohorts(case, rebound)
    original = result['windows'][0]['cohorts'][0]
    row = _compact_comparison(result)['windows'][0]['cohorts'][0]
    evidence = row['prediction']['executed_service_response']
    assert row['status'] == 'compared' and row['accuracy_pass'] is True
    assert row['observed']['event_count'] == cohort['event_count'] == 12160
    assert row['prediction']['per_call_ms'] == pytest.approx(mean_us / 1000)
    assert evidence['rules'][0]['queries'] == {'joint_native_service': 1}
    assert evidence['rules'][0]['evaluation_relation'] == 'in_sample'
    assert evidence['serviced_resources'] == original['prediction']['serviced']
    assert len(evidence['serviced_resources']) == 1
    resource_name, serviced_work = next(iter(evidence['serviced_resources'].items()))
    assert 'observed_copy' in resource_name
    assert serviced_work == pytest.approx(mean_us * 1000)
    assert evidence['joint_native_services'][0]['invocations'] == 1
    assert evidence['joint_native_services'][0]['analytical_reference_work']


def test_retained_joint_response_projection_keeps_unknown_counters_unknown():
    path = ROOT / 'tests/fixtures/scoreboard/glm-joint-execution.json'
    report = json.loads(path.read_text())
    original = report['parameters']
    evidence = service_execution_evidence(deepcopy(original))
    assert evidence['serviced_resources'] is None
    assert evidence['serviced_resources_basis'] == 'not_retained'
    assert evidence['joint_native_services'] == original['joint_native_services']
    assert {s['native_kernel']: s['invocations'] for s in evidence['joint_native_services']} == {
        'KvQuantSparseFlashAttention': 78, 'GroupedMatmulSwigluQuantV2': 75, 'GroupedMatmul': 75}
    assert all('duration_ns_counter' not in json.dumps(rule) for rule in evidence['rules'])
    assert len(evidence['rules']) == len(original['service_regimes'])
