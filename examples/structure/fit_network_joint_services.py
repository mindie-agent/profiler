"""Fit joint collective services within retained physical declaration domains.

[Role] Produce usable fixed-plus-payload service parameters from observations.
[Invariants] No Body residual, Sim prediction or invented payload is fitted.
  Declared payload/route remain conditions; joint terms are not pure link or
  switch-hop components. Two payloads define only their bounded secant.
[Timeouts & Locks] Small retained JSON only, no workers or locks.
[Side-Effect Policy] Write a new parameter sidecar, never mutate baseline/Sim.
"""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'data/observations/sources/arch3510-physical-services'
INPUT = DIRECTORY / 'network-observable-service-baseline.json'


def fit(points):
    """Give each distinct payload one vote after pooling its whole populations."""
    buckets = defaultdict(list)
    for index, row in points:
        buckets[row['declared_collective_program']['payload_bytes']].append((index, row))
    samples = []
    for payload, rows in sorted(buckets.items()):
        count = sum(row['event_count'] for _, row in rows)
        observed = sum(row['observed_service_us']['mean'] * row['event_count']
                       for _, row in rows) / count
        samples.append({'declared_payload_bytes': payload, 'observed_mean_us': observed,
            'event_count': count, 'point_indices': [i for i, _ in rows],
            'source_sha256': sorted({r['source_identity']['sha256'] for _, r in rows}),
            'retained_group_mean_min_us': min(r['observed_service_us']['mean'] for _, r in rows),
            'retained_group_mean_max_us': max(r['observed_service_us']['mean'] for _, r in rows)})
    if len(samples) < 2:
        return {'status': 'single_payload_observation', 'samples': samples,
                'parameters': None, 'extrapolation_allowed': False}
    n = len(samples)
    x = [s['declared_payload_bytes'] for s in samples]
    y = [s['observed_mean_us'] for s in samples]
    mx, my = sum(x)/n, sum(y)/n
    slope = sum((a-mx)*(b-my) for a,b in zip(x,y))/sum((a-mx)**2 for a in x)
    intercept = my - slope * mx
    residuals = []
    for index, row in points:
        value = intercept + slope * row['declared_collective_program']['payload_bytes']
        mean = row['observed_service_us']['mean']
        residuals.append({'point_index': index, 'predicted_joint_us': value,
            'observed_mean_us': mean, 'signed_per_call_residual_us': value - mean,
            'relative_error': value/mean-1})
    for sample in samples:
        prediction = intercept + slope * sample['declared_payload_bytes']
        sample.update(predicted_joint_us=prediction,
            signed_per_call_residual_us=prediction-sample['observed_mean_us'])
    return {'status': 'bounded_two_point_secant' if n == 2 else 'joint_linear_fit',
        'fit_method': 'OLS over distinct payload pooled means; each payload equally weighted',
        'evaluation_relation': 'in_sample', 'samples': samples,
        'parameters': {'joint_fixed_us': intercept, 'joint_us_per_declared_byte': slope,
            'effective_bytes_per_us': 1/slope if slope > 0 else None,
            'effective_GB_per_s_decimal': .001/slope if slope > 0 else None,
            'fixed_term_is_independent_rtt': False, 'slope_is_pure_link_bandwidth': False},
        'positive_service_parameterization': intercept >= 0 and slope > 0,
        'domain': {'declared_payload_bytes': {'min': min(x), 'max': max(x)},
            'discrete_observed_payload_bytes': x},
        'extrapolation_allowed': False, 'original_group_residuals': residuals,
        'max_abs_payload_mean_residual_us': max(abs(s['signed_per_call_residual_us']) for s in samples),
        'max_abs_original_group_residual_us': max(abs(r['signed_per_call_residual_us']) for r in residuals),
        'interpretation': 'Joint same-boundary service includes peer/control effects. Within-payload group variation remains visible; it is not eliminated by the linear fit.'}


def build():
    baseline = json.loads(INPUT.read_text())
    domains = defaultdict(list)
    for index, point in enumerate(baseline['points']):
        selection = {k:v for k,v in point['declared_collective_program'].items()
                     if k != 'payload_bytes'}
        domain = {'hardware_sku': point['hardware_sku'],
            'observed_engine': point['observed_device_engine'],
            'observed_implementation': point['observed_implementation_name'],
            'observed_event_category': point['observed_event_category'],
            'native_operator_type': point['native_operator_type'],
            'declared_program_without_payload': selection}
        domains[json.dumps(domain, sort_keys=True)].append((index, point))
    results = [{'physical_domain': json.loads(domain), **fit(points)}
               for domain, points in sorted(domains.items())]
    output = {'schema_version': 'mindie-joint-collective-service-regimes/1',
        'source_identity': {'path': str(INPUT), 'sha256': sha256(INPUT.read_bytes()).hexdigest()},
        'producer_identity': {'path': str(Path(__file__).resolve()),
            'sha256': sha256(Path(__file__).read_bytes()).hexdigest()},
        'regimes': results,
        'coverage': {'source_count': baseline['coverage']['source_count'],
            'observation_groups': len(baseline['points']),
            'observation_calls': sum(p['event_count'] for p in baseline['points']),
            'joint_fits': sum(r['status']=='joint_linear_fit' for r in results),
            'bounded_secants': sum(r['status']=='bounded_two_point_secant' for r in results),
            'single_payload_domains': sum(r['status']=='single_payload_observation' for r in results)},
        'limitations': ['Payload and source template are conditional declarations, not measured wire bytes or a confirmed runtime route.',
            'Source/role/step peer readiness can vary with payload; the fitted terms are joint observable service parameters, not isolated causal mechanisms.',
            'Two-payload secants have no independent shape validation and cannot extrapolate. Three-point fits retain all residuals and are still in-sample.',
            'No exact 4 KiB or UB_CLOS curve is invented, and no coefficient is written into Sim automatically.'],
        'execution': {'raw_event_reads': 0, 'new_predictions': 0,
            'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}}
    path = DIRECTORY / 'network-joint-service-regimes.json'
    path.write_text(json.dumps(output, indent=2) + '\n')
    lines = ['# Joint collective service parameters', '',
        'These bounded parameters use the [retained network populations](network-observable-service-baseline.json). '
        'They can parameterize the same observable collective boundary. Payload, topology and template remain explicit source conditions; '
        'the intercept is a joint fixed service and the slope is a joint effective service rate.', '',
        '| Physical domain | Payload bytes | Fixed µs | Effective GB/s | Maximum payload-mean residual µs | Status |',
        '|---|---|---:|---:|---:|---|']
    for r in results:
        d = r['physical_domain']; s = d['declared_program_without_payload']; p = r['parameters']
        label = f"{d['hardware_sku']} {s['expansion']} {s['collective']} {s['template']} R{s['ranks']}"
        payloads = ', '.join(str(x['declared_payload_bytes']) for x in r['samples'])
        fmt = lambda v: '—' if v is None else f'{v:.6f}'
        lines.append(f"| {label} | {payloads} | {fmt(p['joint_fixed_us']) if p else '—'} | "
            f"{fmt(p['effective_GB_per_s_decimal']) if p else '—'} | "
            f"{fmt(r.get('max_abs_payload_mean_residual_us'))} | {r['status']} |")
    lines.extend(['', 'Distinct payload means are pooled using complete event counts, then weighted equally in OLS. '
        'The JSON retains every original group residual and within-payload range. In particular, first/steady or role-specific peer readiness '
        'may differ substantially at the same payload; these differences are not attributed solely to network throughput.', '',
        'All fits are in-sample and bounded to their stated payload domains. The two-point secant is an exact interpolation only, '
        'with no independent third-point validation or extrapolation. Negative intercepts/slopes, if present, remain visible rather than clipped.', '',
        'Reproduce: `python3 examples/structure/fit_network_joint_services.py`. No raw scan, device collection or Sim cost is run.'])
    (DIRECTORY / 'network-joint-service-regimes.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({'coverage': output['coverage'], 'execution': output['execution']}))


if __name__ == '__main__':
    build()
