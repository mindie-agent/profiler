"""Real contract cohorts admit fitted rates without inventing observed work."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def fitted_copy():
    sim=pytest.importorskip('mindie_sim')
    sys.path.insert(0,str(ROOT/'examples/structure'))
    from mindie_sim.cohort_comparison import compare_cohorts
    from mindie_sim.structure import export_structure
    from reprice_body_operator_families import rebind_mapping
    base=ROOT/'examples/structure/acceptance-20261030-qwen35-source-complete/canonical-with-tensor-move'
    old=json.loads(next(base.glob('*c128*.mapping.json')).read_text())
    old['windows'][0]['cohorts']=[c for c in old['windows'][0]['cohorts'] if c['native_operator_type']=='TensorMove']
    observed=old['windows'][0]['cohorts'][0]
    case_path=Path(sim.__file__).resolve().parents[1]/'examples/cases/high-concurrency-20261030/qwen35-mc2-tp-source-complete-conditional/qwen35-35b-a5-tp4-c128-mc2-tp-source-complete.json'
    if not case_path.exists():pytest.skip('companion Qwen35 source case unavailable')
    case=json.loads(case_path.read_text())
    geometry={k:old['declared_execution'][k] for k in ('phase','tokens','context','sequences','scope')}
    source=old['windows'][0]['source_identity']
    baseline=json.loads(next(base.glob('*c128*.comparison.json')).read_text())
    baseline['windows'][0]['cohorts']=[c for c in baseline['windows'][0]['cohorts'] if c['native_operator_type']=='TensorMove']
    # This deliberately uses this very population's mean. It is an in-sample
    # effective service rate for this payload/M regime, not a hardware peak or
    # an out-of-sample accuracy claim. Work and tensor descriptors stay fixed.
    effective_rate=observed['physical_work_per_instance']['mte3_bytes']/(observed['duration_ns']['mean']/1e9)
    calibrated=deepcopy(case)
    calibrated['machine']['device'].setdefault('rates',{})['mte3']=effective_rate
    fitted_manifest=export_structure(calibrated,**geometry)
    fitted_mapping,_=rebind_mapping(old,fitted_manifest,source)
    result=compare_cohorts(calibrated,fitted_mapping)
    return {'observed':observed,'fitted_mapping':fitted_mapping,
        'manifest':fitted_manifest,'baseline':baseline,'result':result,
        'effective_rate_bytes_per_second':effective_rate,
        'calibration_evidence':{'evaluation_relation':'in_sample','fit_source_identity':source,
            'evaluation_source_identity':source,'regime':{'native_operator_type':'TensorMove',
                'shape':[128,2048],'dtype':'bf16','read_bytes':524288,'write_bytes':524288},
            'scope':'effective_copy_service; not_peak_MTE3_bandwidth','generalization_claim':False}}


def test_observed_regime_rate_keeps_public_comparison_strict(fitted_copy):
    x=fitted_copy;row=x['result']['windows'][0]['cohorts'][0]
    baseline=x['baseline']['windows'][0]['cohorts'][0]
    assert row['status']==baseline['status']=='compared'
    assert row['accuracy_pass'] is True
    assert row['prediction']['per_call_ms']==pytest.approx(x['observed']['duration_ns']['mean']/1e6)
    assert row['prediction']['per_call_ms']!=baseline['prediction']['per_call_ms']
    assert row['contract']==baseline['contract']
    assert row['prediction']['physical_work_per_instance']==baseline['prediction']['physical_work_per_instance']
    assert row['observed']==baseline['observed']
    assert row['observed']['event_count']==12160
    assert x['calibration_evidence']['fit_source_identity']==x['calibration_evidence']['evaluation_source_identity']


def test_fitted_rate_does_not_complete_a_partial_native_boundary(fitted_copy):
    from mindie_sim.cohort_comparison import _comparison
    x=fitted_copy;cohort=deepcopy(x['fitted_mapping']['windows'][0]['cohorts'][0])
    cohort['contract_scope']={'prediction_coverage':{'kind':'partial_program',
        'reason':'observed_output_not_in_declared_resource_boundary'}}
    status,reason,_=_comparison(cohort,x['result']['windows'][0]['cohorts'][0]['prediction'])
    assert status=='reference_only' and reason=='observed_output_not_in_declared_resource_boundary'


def test_calibrated_resources_do_not_turn_routing_capacity_into_active_rows(fitted_copy):
    from reprice_kimi_matrix_partitions import matrix_mapping
    helper=importlib.import_module('qwen35_caller_contracts')
    part_path=ROOT/'examples/structure/acceptance-20261030-qwen35-source-complete/native-partitions/qwen35-35b-a5-tp4-c128-graph-native-partitions.json'
    partitions=json.loads(part_path.read_text())
    for group in partitions['partitions']:
        if group['native_operator_type']=='GroupedMatmul':group['contract']=helper.grouped_contract(group['native_abi'])
    cohorts,_,families,decisions=matrix_mapping(partitions,fitted_copy['fitted_mapping'],fitted_copy['manifest'],'GroupedMatmul')
    assert not cohorts
    assert sum(f['observed_us']['count'] for f in families)==6080
    assert all(not d['eligible'] for d in decisions)
