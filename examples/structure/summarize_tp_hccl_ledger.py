"""[Role] Independently reconcile retained HCCL histograms and build B-scaling tables.
[Invariants] Recompute numeric moments from full counters; never add controller
  or unlinked subtasks to collective elapsed. Tensor bytes are not wire bytes.
[Timeouts & Locks] Bounded per-source JSON; no locks or child predictions.
[Side-Effect Policy] Read saved evidence only; write compact JSON/Markdown.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal
from math import ceil, isclose
from pathlib import Path

from replay_body_operator_families import identity, read, write, duration_stats


def merge(groups, field='duration_ns_counter'):
    total = Counter()
    for group in groups:
        total.update({int(value):count for value,count in group[field]})
    return total


def pmu_hist(groups, field):
    result = Counter()
    for group in groups:
        item = group['raw_pmu']['fields'].get(field)
        if item:
            result.update({Decimal(v):n for v,n in item['numeric_value_counter']})
    return result


def validate(data, checks):
    actual = read(data['actual_identity']['path'])
    assert identity(data['actual_identity']['path']) == data['actual_identity']
    assert identity(data['body_acceptance_identity']['path']) == data['body_acceptance_identity']
    checks.append('actual_and_body_sha')
    grouped = Counter()
    for group in data['groups']:
        hist = {int(v):n for v,n in group['duration_ns_counter']}
        count = sum(hist.values()); values = duration_stats(hist,1000)
        assert values == group['observed_us']
        assert count == sum(group['layer_counts'].values()) == sum(group['forward_counts'].values())
        assert isclose(sum(v*n for v,n in hist.items())/1e6/data['forward_count'],group['activity_ms_per_forward'])
        grouped[group['event_category']] += count
        for name,pmu in group['raw_pmu']['fields'].items():
            assert pmu['present_count'] == count
            assert pmu['numeric_count'] + pmu['missing_or_na_count'] + pmu['invalid_numeric_count'] == count
            nums = {Decimal(value):n for value,n in pmu['numeric_value_counter']}
            assert sum(nums.values()) == pmu['numeric_count']
            assert nums.get(Decimal(0),0) == pmu['zero_count']
            if nums:
                assert isclose(float(sum(v*n for v,n in nums.items())/sum(nums.values())),pmu['statistics']['mean'])
            else:
                assert pmu['statistics'] is None
            checks.append('pmu_population_'+name)
        assert group['measured_payload_bytes'] is None and group['observed_hccl_algorithm'] is None
        assert not group['communication_bandwidth_calibration_allowed']
        checks += ['duration_moments','layer_forward_population','unknown_payload_and_algorithm']
    assert sum(grouped.values())+data['counts']['exact_duplicate_summary_rows'] == data['counts']['raw_rows_starting_inside_body']
    for key,count in grouped.items():
        assert data['counts'][key] == count
    for kind in {g['native_operator_type'] for g in data['groups'] if g['native_operator_type'].startswith('hcom_')}:
        old = merge([g for g in actual['families'] if g['native_operator_type']==kind])
        new = merge([g for g in data['groups'] if g['native_operator_type']==kind])
        assert old == new
        checks.append('prior_collective_full_histogram_'+kind)
    assert len(data['per_forward']) == data['forward_count']
    assert data['execution']['maximum_resident_set_size_bytes'] <= 512*1024**2
    checks += ['row_partition_conservation','bounded_memory','all_forward_population']


def summarize(directory):
    cases,checks = [],[]
    for path in sorted(directory.glob('*-hccl-ledger.json')):
        data=read(path);validate(data,checks)
        collectives=[g for g in data['groups'] if g['native_operator_type'].startswith('hcom_')]
        families=[]
        for kind in sorted({g['native_operator_type'] for g in collectives}):
            groups=[g for g in collectives if g['native_operator_type']==kind]
            hist=merge(groups);steady=[g for g in groups if g['layer_population']=='steady_layers']
            first=[g for g in groups if g['layer_population']=='layer0' and g['block']=='attention']
            blocks=pmu_hist(groups,'Block Num')
            row={'native_operator_type':kind,'calls':sum(hist.values()),'calls_per_forward':sum(hist.values())/data['forward_count'],
                'observed_us':duration_stats(hist,1000),'steady_observed_us':duration_stats(merge(steady),1000),
                'layer0_attention_observed_us':duration_stats(merge(first),1000),
                'activity_ms_per_forward':sum(v*n for v,n in hist.items())/1e6/data['forward_count'],
                'observed_block_num_counter':[[str(v),n] for v,n in sorted(blocks.items())],
                'device_task_calls':sum(g['observed_us']['count'] for g in groups if g['event_category']=='collective_device_task'),
                'envelope_only_calls':sum(g['observed_us']['count'] for g in groups if g['event_category']=='collective_envelope_only'),
                'preceding_hidden_tensor_bytes':sorted({v for g in groups for v,n in g['preceding_tensor_byte_counter']}),
                'payload_basis':'preceding native tensor shape/dtype candidate only; data dependency and HCCL buffer association not proven',
                'direct_payload_bytes':None,'confirmed_algorithm':None,
                'steady_pmu_us':{name:duration_stats(pmu_hist(steady,name),1) for name in
                    ['aiv_time(us)','aiv_scalar_time(us)','aiv_mte2_time(us)','aiv_mte3_time(us)','Wait Time(us)']}}
            # Decimal keys/numbers from PMU must remain exact until final JSON projection.
            row['steady_pmu_us']={k:{field:float(v) if isinstance(v,Decimal) else v for field,v in values.items()}
                                  for k,values in row['steady_pmu_us'].items()}
            families.append(row)
        cases.append({'case_id':data['case_id'],'artifact_identity':identity(path),'source_identity':data['source_identity'],
            'body_acceptance_identity':data['body_acceptance_identity'],'geometry':data['geometry'],'tp':data['tp'],
            'layers':data['layers'],'forward_count':data['forward_count'],'source_forward_count':data['source_forward_count'],
            'unselected_geometry_forward_count':data['source_forward_count']-data['forward_count'],
            'counts':data['counts'],'families':families,'execution':data['execution']})
    report={'schema_version':'mindie-body-hccl-population-summary/1','status':'completed','sources':len(cases),
        'selected_complete_body_count':sum(c['forward_count'] for c in cases),'source_complete_body_count':sum(c['source_forward_count'] for c in cases),
        'unique_collective_calls':sum(f['calls'] for c in cases for f in c['families']),
        'exact_duplicate_summary_rows':sum(c['counts']['exact_duplicate_summary_rows'] for c in cases),
        'separate_unlinked_aicpu_calls':sum(c['counts'].get('unlinked_aicpu_wrapper',0) for c in cases),
        'raw_scans':sum(c['execution']['raw_scans'] for c in cases),'predictions':0,
        'elapsed_seconds':sum(c['execution']['elapsed_seconds'] for c in cases),
        'maximum_resident_set_size_bytes':max(c['execution']['maximum_resident_set_size_bytes'] for c in cases),
        'cases':cases,'validation':{'checks':len(checks),'failures':0,'raw_re_reads':0,'method':'full retained histograms, layer/forward populations, PMU missing/zero conservation and source identities'},
        'limitations':['Only selected accepted execution geometry per capture; unselected Body counts remain explicit.',
            'HCOM envelopes and exact concrete task duplicates are reconciled; temporal proximity never assigns parent/child tasks.',
            'AICPU group layer/block is where the timestamp lands, not an assertion of semantic ownership.',
            'No direct payload, HCCL algorithm, peer-rank arrival or parent/child connection is exported by these CSVs.',
            'Exporter Wait Time and overlapping AIV pipeline fields do not identify peer wait or wire service.',
            'Source recipe names are declarations, not evidence that the observed runtime chose ring/mesh/CCU.']}
    write(directory/'hccl-population-summary.json',report)
    lines=['# A5 TP HCCL retained-Body evidence','',
        f"{len(cases)} local captures; {report['selected_complete_body_count']} selected complete Bodies; {report['unique_collective_calls']:,} unique collective rows; {report['exact_duplicate_summary_rows']:,} exact duplicate summaries removed. {report['separate_unlinked_aicpu_calls']:,} AICPU rows are separate, never added to collective elapsed.",'',
        '| Capture | TP / execution B / q | F | Type | Calls/F | Mean / P50 µs | Steady Mean / P50 µs | L0 attention Mean / P50 µs | Activity ms/F | BlockNum | Preceding tensor bytes (conditional) |',
        '|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|']
    def pair(stats):
        return '—' if not stats['count'] else f"{stats['mean']:.3f} / {stats['p50']:.3f}"
    for case in cases:
        for family in case['families']:
            geo=case['geometry'];block=','.join(v for v,n in family['observed_block_num_counter'])
            lines.append(f"| {case['case_id']} | {case['tp']} / {geo['sequences_per_replica']} / {geo['tokens_per_sequence']} | {case['forward_count']} | {family['native_operator_type']} | {family['calls_per_forward']:.0f} | {pair(family['observed_us'])} | {pair(family['steady_observed_us'])} | {pair(family['layer0_attention_observed_us'])} | {family['activity_ms_per_forward']:.4f} | {block} | {family['preceding_hidden_tensor_bytes']} |")
    lines += ['', 'The byte column describes an actual preceding hidden tensor, not a measured HCCL payload. No bandwidth is inferred. `B` is shape-derived execution batch, not active client count. The payload association remains conditional. A model `ring_allreduce` recipe does not prove that HCCL selected ring.','',
        'Qwen36 TP2 c12/c96 layer0 starts with parameter Add and input RmsNorm; the long collective follows RecurrentGatedDeltaRule and output MatMul and precedes FFN normalization. It is inside the target body, not embedding tail. Exact source rows are preserved in `tests/fixtures/hccl/`.', '',
        'The nine local capture roots contain kernel/op-statistic/step CSVs but no communication table, profiler DB, or other-rank file. Metadata only points to remote profiler directories; this pass does not fetch them.', '',
        '| Capture | Collective type | Steady AIV mean µs | Scalar mean µs | MTE2 mean µs | MTE3 mean µs |', '|---|---|---:|---:|---:|---:|']
    for case in cases:
        for family in case['families']:
            values=[]
            for name in ['aiv_time(us)','aiv_scalar_time(us)','aiv_mte2_time(us)','aiv_mte3_time(us)']:
                v=family['steady_pmu_us'][name]['mean'];values.append('N/A' if v is None else f'{v:.3f}')
            lines.append(f"| {case['case_id']} | {family['native_operator_type']} | {' | '.join(values)} |")
    lines += ['', 'PMU pipelines can overlap; these columns are not additive. Missing counters remain N/A; observed zero remains zero. `Wait Time(us)` is retained in JSON without interpreting it as network/peer wait.', '',
        f"Validation: {len(checks):,} checks, zero failures; one retained-window CSV pass per source; no new collection or prediction. Peak worker {report['maximum_resident_set_size_bytes']/1024**2:.2f} MiB. Full source identities, raw PMU counters, per-layer/per-forward counts, bounded longest-call locators and duplicate pairs remain in each ledger."]
    (directory/'hccl-population-summary.md').write_text('\n'.join(lines)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    args=parser.parse_args();report=summarize(args.directory)
    print({key:report[key] for key in ('sources','selected_complete_body_count','unique_collective_calls','maximum_resident_set_size_bytes','validation')})
