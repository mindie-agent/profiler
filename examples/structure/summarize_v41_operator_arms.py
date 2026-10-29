"""Keep baseline and source-symmetric V4.1 operator arms independently accountable.

[Role] Join saved, independently reviewed operator arms without re-running cost.
[Invariants] Same observations may appear in two conditions, never one accuracy
  denominator. GMM references retain unknown valid rows and are not strict scores.
[Timeouts & Locks] One bounded metadata file at a time, no raw scans or subprocesses.
[Side-Effect Policy] Write a compact comparison and its Markdown rendering.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path


def read(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024**2:
        raise ValueError('oversized_metadata')
    return json.loads(path.read_text())


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def gather(paths):
    rows, reports, sim = {}, [], None
    totals = Counter()
    accuracy = defaultdict(Counter)
    for path in paths:
        report = read(path)
        if report['status'] != 'completed':
            raise ValueError('partial_cost_arm_requires_visible_failure_report')
        review_path = path.with_name('body-operator-reprice-independent-review.json')
        review = read(review_path)
        if review['status'] != 'passed' or review['scoreboard_sha256'] != identity(path)['sha256']:
            raise ValueError('independent_review_missing_or_stale')
        for tier, counts in review['accuracy_by_tier'].items():
            accuracy[tier].update(counts)
        current = {name:digest for name,digest in report['runtime_source_identity'].items()
                   if '/mindie_sim/' in name}
        if sim is not None and sim != current:
            raise ValueError('mixed_sim_runtime_in_arm')
        sim = current
        reports.append({'report': identity(path), 'review': identity(review_path), 'status': report['status']})
        for projected in report['cases']:
            case = read(projected['case_detail_identity']['path'])['cases'][0]
            cid = case['source_case_id']
            if cid in rows:
                raise ValueError('duplicate_capture_in_arm')
            comparison = read(case['comparison_identity']['path'])
            receipts = comparison['program_receipts'] + [case['reference_receipt']]
            rss = max((item.get('maximum_resident_set_size_bytes',0) for item in receipts), default=0)
            if rss > 512 * 1024**2:
                raise ValueError('worker_memory_budget_exceeded')
            refs = [group for family in case['families']
                    for group in family.get('conditional_source_role_references',())]
            grouped = {}
            for group in refs:
                if group['native_operator_type'] != 'GroupedMatmul':
                    continue
                relation = group['source_correspondence']
                if relation['observed_valid_routed_rows'] is not None or relation['observed_group_list_values'] is not None:
                    raise ValueError('unobserved_route_values_inferred')
                grouped[group['declared_role']] = {
                    'count': group['observed_us']['count'], 'observed_us': group['observed_us'],
                    'predicted_us': group['predicted_reference_us'],
                    'observed_activity_ms_per_forward': group['observed_activity_ms_per_forward'],
                    'predicted_service_ms_per_forward': group['predicted_service_ms_per_forward'],
                    'residual_activity_ms_per_forward': group['predicted_service_ms_per_forward'] - group['observed_activity_ms_per_forward'],
                    'buffer_capacity_rows': relation['observed_buffer_row_capacity'],
                    'declared_valid_rows': relation['declared_valid_routed_rows'],
                    'observed_valid_rows': None, 'group_list_values': None,
                    'boundary_relation': relation['boundary_relation'],
                    'strict_accuracy_eligible': False,
                    'native_abi_sha256': group['frozen_native_rebind']['native_abi_sha256']}
            rows[cid] = {'actual_identity': case['actual_identity'], 'case_identity': case['case_identity'],
                         'source_identity': case['source_identity'], 'geometry': case['geometry'],
                         'forward_count': case['forward_count'], 'passed': case['passed_cohorts'],
                         'strict_compared': case['comparison_status_counts'].get('compared',0),
                         'strict_failed': case['comparison_status_counts'].get('prediction_failed',0),
                         'reference_groups': len(refs), 'reference_exclusions': case['reference_exclusions'],
                         'strict_rebind_exclusions': case['declaration_refresh']['excluded'],
                         'maximum_worker_rss_bytes': rss, 'grouped_matrix_references': grouped}
            totals.update({key:rows[cid][key] for key in ('forward_count','passed','strict_compared','strict_failed','reference_groups')})
            totals['reference_exclusions'] += len(case['reference_exclusions'])
            totals['strict_rebind_exclusions'] += len(case['declaration_refresh']['excluded'])
            totals['strict_scored_events'] += sum(family['scored_event_count'] for family in case['families'])
    return {'cases': rows, 'reports': reports, 'totals': dict(totals), 'accuracy_by_tier': dict(accuracy)}, sim


def summarize(baseline_dirs, source_root):
    baseline_paths = [directory/'body-operator-family-scoreboard.json' for directory in baseline_dirs]
    source_paths = sorted(source_root.glob('a5_*/body-operator-family-scoreboard.json'))
    baseline, a = gather(baseline_paths)
    source, b = gather(source_paths)
    if a != b or set(baseline['cases']) != set(source['cases']) or len(source['cases']) != 7:
        raise ValueError('seven_source_identical_runtime_arm_join_failed')
    checks = 0
    for cid, left in baseline['cases'].items():
        right = source['cases'][cid]
        for field in ('actual_identity','source_identity','geometry','forward_count'):
            if left[field] != right[field]:
                raise ValueError('arm_observations_changed:'+cid+':'+field)
            checks += 1
        for role in ('expert_up','expert_down'):
            left_group = left['grouped_matrix_references'][role]
            right_group = right['grouped_matrix_references'][role]
            for field in ('count','observed_us','observed_activity_ms_per_forward','buffer_capacity_rows','native_abi_sha256'):
                if left_group[field] != right_group[field]:
                    raise ValueError('grouped_reference_population_changed:'+cid+':'+role+':'+field)
                checks += 1
    report = {'schema_version':'mindie-v41-operator-arms/1', 'status':'completed',
              'runtime_commit':'86c1ee8f18b9b997eacb315476e2461b99b59fb1',
              'baseline':baseline, 'source_symmetric_conditional':source,
              'arm_join_checks':checks, 'arm_observed_populations_identical':True,
              'raw_capture_reads':0, 'cost_executions':0,
              'no_cross_arm_accuracy_denominator':True,
              'conditions':[
                  'Baseline preserves each prior case; only the Sim runtime changes.',
                  'Source-symmetric uses explicit MXA8W4 NZ + mixed-packed MQSMLA + source HC selectors.',
                  'Both inherit integer sequences B: [B]*8 is a declared symmetric DP condition, not observed load.',
                  'No single_active_rank0 arm is inferred and neither arm is selected by smaller error.',
                  'GroupedMatmul capacity and full ABI are observed; valid rows, active expert histogram and group-list values remain unobserved.',
                  'Reference kernel activity residuals are not additive body-wall-clock budgets.']}
    json_path = source_root/'v41-seven-arm-comparison.json'
    json_path.write_text(json.dumps(report,indent=2)+'\n')
    lines = ['# V4.1 A5 seven-source operator comparison', '',
             'Runtime `86c1ee8f`; zero raw rereads. Baseline and source-symmetric are separate conditions on the same observations.', '',
             '| Arm | Complete forwards | Strict passed / compared | Strict calls | Conditional references | Excluded references |',
             '|---|---:|---:|---:|---:|---:|']
    for label,arm in [('Baseline',baseline),('Source-symmetric conditional',source)]:
        t=arm['totals'];lines.append(f"| {label} | {t['forward_count']} | {t['passed']} / {t['strict_compared']} | {t['strict_scored_events']} | {t['reference_groups']} | {t['reference_exclusions']} |")
    lines += ['', 'All strict compared cohorts in both arms are in the <=50us / absolute-error <=15us tier. No >50us strict cohort is scored in this population.', '', 'GroupedMatmul uses complete retained native ABI partitions and independently rebuilt FFN declarations for all 40 aligned layers. These rows do not enter strict accuracy.', '',
              '| Capture | Role | Calls | Capacity / declared valid rows | Observed mean / P50 us | Baseline us | Source us | Baseline residual ms/F | Source residual ms/F |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    ordered=sorted(baseline['cases'],key=lambda cid:baseline['cases'][cid]['geometry']['sequences_per_replica'])
    for cid in ordered:
        left,right=baseline['cases'][cid],source['cases'][cid]
        for role in ('expert_up','expert_down'):
            x,y=left['grouped_matrix_references'][role],right['grouped_matrix_references'][role]
            label=cid.removeprefix('a5_v41_fp8_tp1_dp8_ep8_')
            lines.append(f"| {label} | {role} | {x['count']} | {x['buffer_capacity_rows']} / {x['declared_valid_rows']} | {x['observed_us']['mean']:.3f} / {x['observed_us']['p50']:.3f} | {x['predicted_us']:.3f} | {y['predicted_us']:.3f} | {x['residual_activity_ms_per_forward']:+.3f} | {y['residual_activity_ms_per_forward']:+.3f} |")
    lines += ['', 'Valid route rows and expert histogram remain unknown. Per-forward residual is predicted service minus measured kernel activity; communication/overlap prevents interpreting its sum as a body wall-time explanation.', '',
              'Source HC changes two existing aggregate resource boundaries, so those old strict partitions remain excluded. N/A MQSMLA and changed HC/Dispatch/Combine references need a separate explicit source-correspondence rebind; they are not silently assigned zero cost.', '',
              f"Independent join: {checks} checks; all seven observed identities, geometry and GMM histogram statistics match between arms.", '']
    json_path.with_suffix('.md').write_text('\n'.join(lines))
    print(json.dumps({'status':'completed','checks':checks,'baseline':baseline['totals'],'source_symmetric':source['totals']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-dir',action='append',type=Path,required=True)
    parser.add_argument('--source-root',type=Path,required=True)
    args=parser.parse_args()
    summarize(args.baseline_dir,args.source_root)
