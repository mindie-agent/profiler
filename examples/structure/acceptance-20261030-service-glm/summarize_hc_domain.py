"""Join the two completed parts of one nine-capture HC source domain.

[Role] Provide a compact index and honest pass-transition table for the main board.
[Invariants] No best-error selection, duplicated source, raw read or new prediction.
[Timeouts & Locks] Bounded saved receipts, no locks.
[Side-Effect Policy] Writes third-pass-all-nine.json and Markdown only.
"""
from build_service_cases import HERE, ORDER, read, write, pin


def main():
    reports = [HERE / folder / 'decode-forward-service-replay.json'
               for folder in ('third-pass', 'third-pass-remaining-six')]
    prior_reports = [HERE / folder for folder in
                     ('decode-forward-service-replay.json', 'second-pass/decode-forward-service-replay.json')]
    prior = {r['source_case_id']: r for p in prior_reports for r in read(p)['cases'] if r['status'] == 'compared'}
    rows = []
    all_geometry = 0
    all_forwards = 0
    for path in reports:
        report = read(path)
        assert report['status'] == 'completed' and report['runtime_generation']['unchanged']
        identity = pin(path)
        all_geometry += len(report['cases'])
        all_forwards += sum(r['observed']['body_forward_span_ms']['count'] for r in report['cases'])
        for r in report['cases']:
            if r['status'] != 'compared':
                continue
            cid = r['source_case_id']; old = prior[cid]
            assert old['source_identity'] == r['source_identity'] and old['observed'] == r['observed']
            hits = r['prediction']['parameters']['service_regimes']
            assert len(hits) == 11 and not r['prediction']['parameters']['regime_selection']['unmatched']
            rows.append({'case_id': cid, 'source_identity': r['source_identity'],
                         'replay_identity': identity, 'replay_case_id': r['case_id'],
                         'case_identity': r['prediction_execution']['case_identity'],
                         'runtime_identity': r['runtime_identity'], 'geometry': r['geometry'],
                         'forward_count': r['observed']['body_forward_span_ms']['count'], 'comparison': r['comparison'],
                         'previous_comparison': old['comparison'],
                         'previous_passed': old['comparison']['passed'],
                         'current_passed': r['comparison']['passed'],
                         'service_rule_hits': [{'id': h['id'], 'queries': h['queries']} for h in hits],
                         'execution': r['prediction_execution']['execution']})
    assert len(rows) == len(set(r['case_id'] for r in rows)) == 9
    rows.sort(key=lambda r: ORDER.index(r['case_id']))
    summary = {'source_count': 9, 'selected_forward_count': sum(r['forward_count'] for r in rows),
               'all_observed_geometry_count': all_geometry, 'all_observed_forward_count': all_forwards,
               'passed_before': sum(r['previous_passed'] for r in rows),
               'passed_current': sum(r['current_passed'] for r in rows),
               'exited_pass': [r['case_id'] for r in rows if r['previous_passed'] and not r['current_passed']],
               'new_predictions': 9, 'raw_scans': 0,
               'elapsed_seconds': sum(r['execution']['elapsed_seconds'] for r in rows),
               'peak_rss_bytes': max(r['execution']['peak_rss_bytes'] for r in rows)}
    value = {'schema_version': 'mindie-service-domain-comparison/1', 'status': 'completed',
             'selection_policy': 'All nine premix-absent BF16 HC4 sources in M4..256; never choose by error.',
             'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
             'scope_caution': 'Complete native service means do not establish every native tensor ABI. Runtime changed from 2f to 3b72; differences are not isolated HC causal effects.',
             'summary': summary, 'cases': rows, 'replay_identities': [pin(p) for p in reports],
             'generator_identity': pin(__file__)}
    write(HERE / 'third-pass-all-nine.json', value)
    lines = ['# GLM uniform HC source domain: all nine captures', '',
             'All eligible captures use the same eleven-mechanism source configuration. Responses remain each capture’s observed native Mean. The three earlier executions were retained; only the other six were newly run. No selection depends on whether a previous result passed.', '',
             '| Source | F | Real Mean ms | Previous Sim ms | Current Sim ms | Current error | Previous → current |',
             '|---|---:|---:|---:|---:|---:|---|']
    for r in rows:
        c = r['comparison']; old = r['previous_comparison']
        lines.append(f"| {r['case_id']} | {r['forward_count']} | {c['observed_ms']['mean']:.6f} | {old['predicted_ms']:.6f} | {c['predicted_ms']:.6f} | {100*c['relative_error']:+.3f}% | {'PASS' if r['previous_passed'] else 'FAIL'} → {'PASS' if r['current_passed'] else 'FAIL'} |")
    lines += ['', f"Uniform current result: {summary['passed_current']}/9 PASS, previously {summary['passed_before']}/9. Selected population: {summary['selected_forward_count']} Forward; all retained geometries: {all_geometry} / {all_forwards} Forward. Deferred geometries are not added to the scored population.", '',
              'All 99 rule/source combinations hit. MoeInitRoutingV3 (42/F) and pooled convolution-state copy (68/F) were already represented and are not charged twice. The normalized HC contract supports the premix-absent branch; the provider removes six standalone phases and adds one whole-native boundary per HC call. No obsolete decomposition is restored to recover a pass.', '',
              'Remaining Slice (mixed 224/F) and sparse-attention metadata (11/F) require independent physical role boundaries. Their unscored elapsed time is not a zero-cost assumption or an additive Body deficit.', '',
              f"Nine total fresh predictions across the two retained reports; {summary['elapsed_seconds']:.3f}s, maximum RSS {summary['peak_rss_bytes']/2**20:.2f}MiB. No new raw parsing or device collection. Runtime: 3b72ea2d. In-sample service calibration; strict ABI coverage stays separate."]
    (HERE / 'third-pass-all-nine.md').write_text('\n'.join(lines) + '\n')
    print(summary)


if __name__ == '__main__':
    main()
