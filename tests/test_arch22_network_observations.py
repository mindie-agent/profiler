"""Original A3 SIO topology and overlapping HCCL task traces."""
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    'arch22_network', ROOT / 'examples/structure/export_arch22_network_observations.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE = Path(__file__).parent / 'fixtures/network'


def test_real_sio_phase_counts_preserve_overlap_and_reported_zero():
    result = MODULE.trace_rows(FIXTURE / 'a3-sio-phase-trace.json')
    assert result['profiled_collective_count'] == 1
    event = result['envelopes'][0]
    assert event['observed_algorithm_signature'] == 'RING-RING-NHR'
    assert event['payload_bytes'] == 4 * 1024**2
    assert event['elapsed_us'] == 969.34
    groups = {g['phase_type']: g for g in event['phase_summaries']}
    assert groups['SDMA_SQE']['count'] == 8
    assert groups['NOTIFY_RECORD_SQE']['reported_zero_duration_count'] == 4
    assert sum(g['activity_sum_us'] for g in groups.values()) > event['elapsed_us']
    assert event['contained_phase_union_us'] <= event['elapsed_us']
    assert event['pure_notify_rtt_or_switch_latency_identified'] is False


def test_real_topology_and_event_batch_have_distinct_observed_boundaries():
    parent = MODULE.read(FIXTURE / 'a3-sio-parent-excerpt.json')
    topo = MODULE.topology(parent)
    assert topo['devices'] == [4, 5]
    assert [p['link_label'] for p in topo['observed_pairs']] == ['SIO', 'SIO']
    assert topo['topology_levels_of_selected_collective'] is None
    curves = MODULE.curve_rows(parent)
    assert len(curves) == 2
    assert {c['rank'] for c in curves} == {0, 1}
    assert all(c['repetitions_per_batch'] == 32 and c['sample_count'] == 25 for c in curves)
    assert curves[0]['elapsed_us']['p50'] == 103.06437313556671
    assert all(c['pure_link_bandwidth_identified'] is False for c in curves)


def test_tp16_whole_call_population_does_not_invent_phase_or_payload():
    ledger = MODULE.read(FIXTURE / 'a3-tp16-whole-call-excerpt.json')
    row, = MODULE.model_envelope_rows(ledger)
    assert row['elapsed_us']['count'] == 3388
    assert row['forward_count'] == 44 and row['calls_per_forward'] == 77
    assert row['elapsed_us']['p50'] == 85.862
    assert row['preceding_tensor_byte_counter'] == [[147456, 3388]]
    assert row['measured_payload_bytes'] is None
    assert row['observed_hccl_algorithm'] is None
    assert row['parent_child_task_association'] is None
    assert row['whole_call_service_is_observed'] is True
    assert row['per_phase_service_identified'] is False


def test_real_payload_curve_reports_residuals_without_body_fit():
    sys.path.insert(0, str(ROOT / 'examples/structure'))
    from fit_arch22_network_services import fit_points
    curve = MODULE.read(FIXTURE / 'a3-sio-service-curve.json')['unprofiled_payload_curve']
    result = fit_points(curve, 'mean')
    assert abs(result['joint_fixed_us'] - 62.11304737358449) < 1e-9
    assert abs(result['effective_payload_bandwidth_gb_s'] - 115.13596390278964) < 1e-9
    assert len(result['residuals']) == 5
    assert result['rmse_us'] > 20
    assert abs(sum(row['residual_us'] for row in result['residuals'])) < 1e-9
    assert result['intercept_is_signed_unclamped'] is True
