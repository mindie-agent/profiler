"""Fit joint collective service curves from retained A3 device-event timings.

[Role] Supply positive-domain observable service parameters, without pure-link claims.
[Invariants] Preserve every run/rank; fit only >=3 payloads in one protocol/domain.
  Signed intercepts and residuals are reported unchanged; no Body values are inputs.
[Timeouts & Locks] Bounded saved JSON only, no subprocess or locks.
[Side-Effect Policy] Write a separate fit artifact; original observations are immutable.
"""
from collections import defaultdict
import json
from math import sqrt
from pathlib import Path
import resource
import time

from export_arch22_network_observations import OUT, pin, read


def fit_points(points, statistic):
    x = [p['payload_bytes'] for p in points]
    y = [p['elapsed_us'][statistic] for p in points]
    if len(set(x)) < 3:
        raise ValueError('three_distinct_payloads_required')
    mx, my = sum(x) / len(x), sum(y) / len(y)
    slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx)**2 for a in x)
    intercept = my - slope * mx
    residuals = [{'payload_bytes': a, 'observed_us': b, 'predicted_us': intercept + slope * a,
                  'residual_us': intercept + slope * a - b,
                  'relative_residual': (intercept + slope * a) / b - 1}
                 for a, b in zip(x, y)]
    return {'statistic': statistic, 'joint_fixed_us': intercept, 'us_per_byte': slope,
        'effective_payload_bandwidth_gb_s': .001 / slope if slope > 0 else None,
        'intercept_is_signed_unclamped': True,
        'positive_service_over_observed_domain': min(r['predicted_us'] for r in residuals) > 0,
        'rmse_us': sqrt(sum(r['residual_us']**2 for r in residuals) / len(residuals)),
        'max_abs_relative_residual': max(abs(r['relative_residual']) for r in residuals),
        'residuals': residuals}


def fit_run(run, rank_protocols):
    groups = defaultdict(list)
    for row in run['unprofiled_payload_curve']:
        groups[(row['rank'], row['collective'])].append(row)
    results, excluded = [], []
    for (rank, collective), rows in sorted(groups.items()):
        if len({p['payload_bytes'] for p in rows}) < 3:
            excluded.append({'rank': rank, 'collective': collective,
                             'reason': 'fewer_than_three_distinct_payloads', 'point_count': len(rows)})
            continue
        rows.sort(key=lambda p: p['payload_bytes'])
        results.append({'run_id': run['run_id'], 'rank': rank, 'collective': collective,
            'dtype': rank_protocols[rank]['dtype'], 'dtype_basis': 'retained_parent.ranks[rank].protocol.dtype',
            'world_size': run['topology']['world_size'], 'topology': run['topology'],
            'parent_identity': run['parent_identity'], 'point_count': len(rows),
            'sample_count': sum(p['sample_count'] for p in rows),
            'payload_domain_bytes': {'min': rows[0]['payload_bytes'], 'max': rows[-1]['payload_bytes']},
            'point_protocols': [{'payload_bytes': p['payload_bytes'],
                                 'repetitions_per_batch': p['repetitions_per_batch']} for p in rows],
            'mean_fit': fit_points(rows, 'mean'), 'p50_fit': fit_points(rows, 'p50'),
            'model': 'elapsed_us = joint_fixed_us + payload_bytes * us_per_byte',
            'weighting': 'equal weight per observed payload point; no best-run or best-rank selection',
            'evaluation_relation': 'in_sample', 'cross_rank_or_topology_extrapolation_supported': False,
            'mechanism_identification': 'joint collective response; intercept is not uniquely notify or switch-hop RTT',
            'scope': 'unprofiled device-event batch elapsed divided by repetitions',
            'applicability': 'Same run protocol, rank, world size, dtype and captured topology; inspect residuals within the payload domain.'})
    return results, excluded


def main():
    started = time.perf_counter()
    source = OUT / 'retained-a3-network-observations.json'
    observed = read(source)
    curves, excluded = [], []
    for run in observed['runs']:
        parent = read(run['parent_identity']['path'])
        if pin(run['parent_identity']['path']) != run['parent_identity']:
            raise ValueError('retained_parent_changed')
        protocols = {r['rank']: r['protocol'] for r in parent['ranks']}
        selected, omitted = fit_run(run, protocols)
        curves.extend(selected)
        excluded.extend({'run_id': run['run_id'], **row} for row in omitted)
    report = {'schema_version': 'mindie-joint-network-service-curves/1',
        'producer_identity': pin(__file__), 'observation_identity': pin(source),
        'curves': curves, 'excluded_controls': excluded,
        'identifiability': {'effective_joint_service_fitted': True, 'pure_link_rate_identified': False,
            'per_switch_hop_identified': False, 'notify_unit_latency_identified': False,
            'extrapolation_to_world_size_8_or_16': False},
        'execution': {'elapsed_seconds': time.perf_counter() - started,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'raw_capture_reads': 0, 'new_cost_predictions': 0, 'new_device_collections': 0}}
    output = OUT / 'retained-a3-joint-service-curves.json'
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'curves': len(curves), 'points': sum(c['point_count'] for c in curves),
                      'excluded_single_payload_controls': len(excluded), **report['execution']}))


if __name__ == '__main__':
    main()
