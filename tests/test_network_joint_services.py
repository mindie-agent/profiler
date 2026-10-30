"""Retained A5 collectives yield bounded joint services, not invented link rates."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('network_joint', ROOT / 'examples/structure/fit_network_joint_services.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def source_points(collective, template, ranks):
    baseline = json.loads((ROOT / 'data/observations/sources/arch3510-physical-services/network-observable-service-baseline.json').read_text())
    return [(i, p) for i, p in enumerate(baseline['points'])
            if p['declared_collective_program']['collective'] == collective
            and p['declared_collective_program']['template'] == template
            and p['declared_collective_program']['ranks'] == ranks]


def test_three_actual_payloads_preserve_population_and_nonzero_group_residuals():
    points = source_points('allgather', 'mesh', 4)
    result = MODULE.fit(points)
    assert result['status'] == 'joint_linear_fit'
    assert result['parameters']['joint_fixed_us'] == pytest.approx(11.324448, abs=1e-6)
    assert result['parameters']['effective_GB_per_s_decimal'] == pytest.approx(26.026929, abs=1e-6)
    assert sum(s['event_count'] for s in result['samples']) == sum(p['event_count'] for _, p in points)
    assert result['domain']['discrete_observed_payload_bytes'] == [16384, 262144, 524288]
    assert result['max_abs_payload_mean_residual_us'] > 2
    assert len(result['original_group_residuals']) == len(points)
    assert result['parameters']['fixed_term_is_independent_rtt'] is False


def test_two_actual_payloads_are_only_a_secant_with_original_group_variation():
    points = source_points('allreduce', 'mesh_oneshot', 2)
    result = MODULE.fit(points)
    assert result['status'] == 'bounded_two_point_secant'
    assert result['max_abs_payload_mean_residual_us'] < 1e-12
    assert result['max_abs_original_group_residual_us'] > 200
    assert result['extrapolation_allowed'] is False
    assert result['parameters']['slope_is_pure_link_bandwidth'] is False
    assert result['domain']['discrete_observed_payload_bytes'] == [40960, 491520]
