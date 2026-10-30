"""Verify saved scalar/DMA histograms and population identities without new scans.

[Role] Recompute complete PMU numeric denominators and native count conservation.
[Invariants] Source files are not reread; historical execution/tool identities persist.
[Timeouts & Locks] One bounded evidence file at a time, no locks or subprocesses.
[Side-Effect Policy] Writes a compact review receipt only.
"""
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path
import resource
import sys

from collect_scalar_dma_pmu import identity, read
from targeted_native_pmu import numeric_stats

DEST = Path(__file__).resolve().parents[2] / 'data/observations/sources/arch3510-physical-services'


def main():
    receipt_path = DEST / 'scalar-dma-extraction-receipt.json'
    receipt = read(receipt_path)
    checks = 0; failures = []; cases = []

    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            failures.append(label)

    for entry in receipt['cases']:
        pin = entry['output_identity']
        check(identity(pin['path']) == pin, entry['case_id'] + ' output identity')
        data = read(pin['path'])
        actual = read(data['actual_identity']['path'])
        check(identity(data['actual_identity']['path']) == data['actual_identity'], entry['case_id'] + ' actual identity')
        check(identity(data['body_identity']['path']) == data['body_identity'], entry['case_id'] + ' accepted body identity')
        check(data['source_identity']['sha256'] == actual['source_identity']['sha256'], entry['case_id'] + ' source pin')
        check(data['forward_count'] == actual['forward_count'] == entry['forward_count'], entry['case_id'] + ' selected Forward denominator')
        check(data['geometry'] == actual['geometry'], entry['case_id'] + ' exact observed geometry')
        check(data['extractor_identity'] == entry['executed_extractor_identity'], entry['case_id'] + ' actual extractor generation')
        totals = {native: Counter() for native in data['native_counts']}
        for i, group in enumerate(data['partitions']):
            prefix = f"{entry['case_id']} partition {i}"
            pmu = group['raw_pmu']; count = pmu['event_count']
            hist = Counter(dict(group['duration_ns_counter']))
            check(sum(hist.values()) == count == sum(group['forward_counts'].values()), prefix + ' count conservation')
            totals[group['native_operator_type']].update(hist)
            for name, field in pmu['fields'].items():
                numeric = Counter(dict(field['numeric_value_counter']))
                check(sum(numeric.values()) == field['numeric_count'], prefix + '/' + name + ' numeric count')
                check(field['numeric_count'] + field['invalid_numeric_count'] + field['missing_or_na_count'] == count,
                      prefix + '/' + name + ' complete denominator')
                check(sum(n for value, n in numeric.items() if Decimal(value) == 0) == field['zero_count'], prefix + '/' + name + ' measured zeros')
                check(numeric_stats(numeric) == field['statistics'], prefix + '/' + name + ' independent Decimal statistics')
            duration = {int(Decimal(value)*1000): n for value, n in pmu['fields']['Duration(us)']['numeric_value_counter']}
            check(Counter(duration) == hist, prefix + ' duration integer-ns equality')
            for name, values in pmu['dimensions'].items():
                check(sum(n for _, n in values) == count, prefix + '/' + name + ' dimension population')
            for chain in group['chain_examples']:
                check(chain['gather']['stream_id'] == chain['convolution']['stream_id'] == chain['scatter']['stream_id'], prefix + ' same-stream copy chain')
                check(chain['gather']['device_id'] == chain['convolution']['device_id'] == chain['scatter']['device_id'], prefix + ' same-device copy chain')
                check(chain['gather']['csv_line'] < chain['convolution']['csv_line'] < chain['scatter']['csv_line'], prefix + ' ordered copy-conv-copy locators')
        expected = {k: Counter() for k in totals}
        for family in actual['families']:
            if family['native_operator_type'] in expected:
                expected[family['native_operator_type']].update(dict(family['duration_ns_counter']))
        for native in totals:
            check(totals[native] == expected[native], entry['case_id'] + '/' + native + ' entire retained histogram')
            check(sum(totals[native].values()) == data['native_counts'][native], entry['case_id'] + '/' + native + ' full count')
        check(data['execution']['peak_rss_bytes'] <= 512*1024**2, entry['case_id'] + ' memory budget')
        cases.append({'case_id': entry['case_id'], 'forwards': data['forward_count'],
                      'partitions': len(data['partitions']), 'native_events': sum(data['native_counts'].values())})
    constraints = read(DEST / 'scalar-dma-physical-constraints.json')
    check(constraints['extraction_receipt_identity'] == identity(receipt_path), 'summary receipt identity')
    check(not constraints['parameter_changes'] and not constraints['body_residual_used'], 'no runtime calibration side effect')
    check(len(constraints['joint_response_fits']) == 6, 'six independent direction/pipe composite regressions')
    for fit in constraints['joint_response_fits']:
        points = [(p['source_programs_per_declared_owner'], p['pmu'][fit['field']]['mean'])
                  for p in constraints['directional_copy_points'] if p['direction'] == fit['direction']]
        # The normal equations independently check the serialized slope/intercept.
        residuals = [(x, y-fit['intercept_us']-fit['slope_us_per_coordinate']*x) for x, y in points]
        check(abs(sum(y for _, y in residuals)) < 1e-10, 'regression zero residual sum')
        check(abs(sum(x*y for x, y in residuals)) < 1e-8, 'regression zero weighted residual sum')
        check(fit['feature_rank_without_intercept'] == 1 and not fit['separate_scalar_load_descriptor_and_byte_prices_identifiable'], 'collinear features remain joint')
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(peak if sys.platform == 'darwin' else peak*1024)
    result = {'schema_version': 'mindie-scalar-dma-evidence-review/1', 'status': 'failed' if failures else 'passed',
              'checks': checks, 'failures': failures, 'cases': cases,
              'receipt_identity': identity(receipt_path),
              'summary_identity': identity(DEST / 'scalar-dma-physical-constraints.json'),
              'reviewer_identity': identity(__file__), 'execution': {'raw_scans': 0, 'cost_calls': 0, 'peak_rss_bytes': peak}}
    (DEST / 'scalar-dma-evidence-review.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'checks': checks, 'failures': failures, 'peak_rss_bytes': peak}))
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
