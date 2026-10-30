"""Summarize joint scalar/DMA constraints from complete retained PMU populations.

[Role] Separate useful effective responses from unidentifiable instruction prices.
[Invariants] Pipe times overlap; signed differences are diagnostics, not barriers.
  Source instruction counts never become observed compiler dispatch or route data.
[Timeouts & Locks] One compact evidence JSON at a time, no raw reads or locks.
[Side-Effect Policy] Writes scalar-dma-* summary and source-linked constraints only.
"""
from pathlib import Path
import json

from collect_scalar_dma_pmu import identity, read

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/observations/sources/arch3510-physical-services'
SIM = Path('/Users/maoxx241/code/sim-rewrite-20261027')
PIPES = ('aiv_vec_time(us)', 'aiv_scalar_time(us)', 'aiv_mte2_time(us)', 'aiv_mte3_time(us)')


def signed_diagnostics(pmu):
    """Keep absent and partial populations out of arithmetic across PMU fields."""
    n = pmu['event_count']
    fields = pmu['fields']
    def mean(name):
        value = fields.get(name)
        return (value['statistics']['mean'] if value and value['numeric_count'] == n else None)
    means = {name: mean(name) for name in ('Duration(us)', 'aiv_time(us)', *PIPES)}
    valid = all(means[k] is not None for k in PIPES)
    total = means['aiv_time(us)']
    return {'complete_numeric_mean_us': means,
            'signed_aiv_minus_pipe_sum_us': total - sum(means[k] for k in PIPES) if valid and total is not None else None,
            'signed_aiv_minus_max_pipe_us': total - max(means[k] for k in PIPES) if valid and total is not None else None,
            'signed_duration_minus_aiv_us': means['Duration(us)'] - total if total is not None and means['Duration(us)'] is not None else None,
            'interpretation': 'Signed boundary diagnostics only; neither remainder is classified as synchronization or launch.'}


def line_fit(points):
    """An effective conditional slope; independent physical components stay separate."""
    n = len(points)
    xmean = sum(x for x, _ in points) / n
    ymean = sum(y for _, y in points) / n
    variance = sum((x - xmean)**2 for x, _ in points)
    slope = sum((x - xmean)*(y - ymean) for x, y in points) / variance
    intercept = ymean - slope*xmean
    error = sum((y - (intercept+slope*x))**2 for x, y in points)
    spread = sum((y-ymean)**2 for _, y in points)
    return {'intercept_us': intercept, 'slope_us_per_coordinate': slope,
            'r_squared': 1-error/spread if spread else None, 'point_count': n,
            'prediction_usage': 'conditional composite response only; not an independent primitive price'}


def main():
    receipt_path = DEST / 'scalar-dma-extraction-receipt.json'
    receipt = read(receipt_path)
    copy_path = SIM / 'data/verification/conv-state-memory-service-audit-20261030.json'
    count_path = SIM / 'data/verification/moe-init-source-control-audit-20261030.json'
    dsq_path = SIM / 'data/verification/grouped-dequant-arch35-20261030.json'
    pmu_boundary_path = ROOT / 'examples/structure/acceptance-20261029/situ-mx-pmu-boundary.md'
    counts = read(count_path)
    dsq = read(dsq_path)
    records, gaps = [], []
    for source in receipt['cases']:
        if identity(source['output_identity']['path']) != source['output_identity']:
            raise ValueError('retained_pmu_partition_identity_changed')
        evidence = read(source['output_identity']['path'])
        for index, group in enumerate(evidence['partitions']):
            native = group['native_operator_type']
            pmu = group['raw_pmu']
            record = {'source_case_id': source['case_id'], 'source_identity': evidence['source_identity'],
                      'partition_identity': source['output_identity'], 'partition_index': index,
                      'native_operator_type': native, 'native_abi': group['native_abi'],
                      'hardware': group['hardware'], 'accelerator_core': group['accelerator_core'],
                      'block_num': group['block_num'], 'copy_direction': group['copy_direction'],
                      'conditional_state_shapes': group['conditional_state_shapes'],
                      'forward_count': evidence['forward_count'], 'calls': pmu['event_count'],
                      'calls_per_forward': pmu['event_count']/evidence['forward_count'],
                      'pmu': {k: {field: value for field, value in v.items() if field != 'numeric_value_counter'}
                              for k, v in pmu['fields'].items() if k.endswith('_time(us)') or k in ('Duration(us)', 'Wait Time(us)')},
                      'scalar_wait_column_present': any('scalar_wait' in k for k in evidence['header']),
                      'diagnostics': signed_diagnostics(pmu),
                      'isolated_instruction_price_identified': False}
            if native == 'MoeInitRoutingV3':
                abi = group['native_abi']; assignments = abi[2][1][0][0] * abi[2][1][0][1]
                experts = abi[3][2][0][0]
                active = min(64, assignments)
                record['source_instruction_counts'] = {
                    'evidence_identity': identity(count_path), 'source_revision': counts['source_revision'],
                    'source_hashes': counts['source_hashes'], 'count_mode': 1,
                    'assumptions': ['valid topk assignments', 'full local expert range', 'single-core sort domain', 'captured compiler/route values not established'],
                    'sort_blocks32': (assignments+31)//32, 'assignments': assignments,
                    'count_simt_int32_loads_all_active_owners': 4*assignments-2*active,
                    'atomic_add_count_payload_bytes_all_active_owners': 4*experts*active,
                    'owner0_serial_ub_getvalue_calls': experts,
                    'owner0_serial_scalar_adds': experts,
                    'sort_opcode_instruction_count': None,
                    'scope': 'source logical operations; per-owner counts explicitly distinguished from sums'}
            elif native == 'DequantSwigluQuant':
                abi = group['native_abi']; banks = abi[2][-1][0][0]; blocks = int(group['block_num'])
                record['source_instruction_counts'] = {
                    'evidence_identity': identity(dsq_path), 'source': dsq['source'],
                    'scalar_group_index_getvalue_calls_all_blocks': blocks*banks,
                    'scalar_group_index_getvalue_calls_per_block': banks,
                    'launched_blocks': blocks, 'input_buffer_capacity_rows': abi[2][0][0][0],
                    'observed_valid_group_rows': None,
                    'scope': 'arch35 source-conditional full-load group scan; no inference that capacity equals valid rows'}
            if native in {'Slice', 'SparseFlashMlaMetadata'}:
                gaps.append(record)
            else:
                records.append(record)
    copy = read(copy_path)
    copy_points = []
    for row in copy['rows']:
        for direction, values in row['directions'].items():
            n = row['geometry']['programs_per_owner']
            copy_points.append({'batch': row['batch'], 'direction': direction, 'source_identity': row['source'],
                                'source_population_identity': identity(copy_path), 'calls': values['calls'],
                                'state_shape': row['state_shape'], 'block_counts': values['block_counts'],
                                'source_programs_per_declared_owner': n,
                                'source_metadata_loads_per_declared_owner': 3*n,
                                'source_payload_load_store_pairs_per_declared_owner': n,
                                'source_logical_payload_bytes_per_declared_owner': 512*n,
                                'pmu': values['pmu'], 'per_source_program_effective_busy_us': values['busy_us_per_declared_owner_program'],
                                'capture_binary_and_grid_assignment_confirmed': False})
    fits = []
    for direction in ('gather', 'scatter'):
        selected = [p for p in copy_points if p['direction'] == direction]
        for field in ('aiv_scalar_time(us)', 'aiv_mte2_time(us)', 'aiv_mte3_time(us)'):
            fit = line_fit([(p['source_programs_per_declared_owner'], p['pmu'][field]['mean']) for p in selected])
            fits.append({'direction': direction, 'field': field, 'coordinate': 'source_programs_per_declared_owner', **fit,
                         'collinear_features': {'programs': 1, 'metadata_loads': 3, 'payload_bytes': 512},
                         'feature_rank_without_intercept': 1, 'separate_scalar_load_descriptor_and_byte_prices_identifiable': False})
    for row in counts['controls']:
        assert row['count_SIMT_int32_loads'] == 4*row['assignments']-2*row['active_count_owners']
        assert row['owner0_total_UB_GetValue_count'] == row['experts']
    constraints = [
        {'mechanism': 'copy scalar and DMA', 'usable_result': 'Direction-specific joint busy-time response vs source programs/owner',
         'independent_prices': None, 'why': 'Programs, three scalar metadata loads and fixed 512B payload are collinear. Compiled descriptor count, grid assignment and exporter owner aggregation remain separate conditions.',
         'needed_contrast': 'Hold bytes constant while changing descriptors, then hold descriptors constant while changing bytes; retain exact compiled instruction counts and PMU aggregation metadata.'},
        {'mechanism': 'DSQ GetValue', 'usable_result': 'Complete INT32/BF16 native ABI and scalar busy at three capacity domains, with a source scan of 64 group descriptors per launched block',
         'independent_prices': None, 'why': 'The group scan count stays 64 while valid work, tile control and scalar address work vary. A scalar-time/GetValue quotient includes these other operations.',
         'needed_contrast': 'Vary stored group count at fixed valid rows, layouts, tile schedule and BlockNum; retain actual group-list values and generated scalar instructions.'},
        {'mechanism': 'routing sort/SIMT/owner-zero accumulation', 'usable_result': 'Full mean/P50 PMU populations with conditional sort-block, SIMT-read and owner-zero E288 counts',
         'independent_prices': None, 'why': 'Owner-zero GetValue remains E288 and sort/SIMT/quantization coexist in one kernel. Scalar wait is not exported; sort blocks are not compiled sort instruction counts.',
         'needed_contrast': 'Hold assignments/width constant while varying E, and separately vary assignments with the same sort branch; retain route values, SIMT atomic/cache events and owner-specific counters.'}]
    result = {'schema_version': 'mindie-scalar-dma-physical-constraints/1', 'status': 'completed',
              'extraction_receipt_identity': identity(receipt_path),
              'pmu_semantics_evidence': identity(pmu_boundary_path),
              'pmu_scope': 'CSV exporter units retained. The inspected Ascend950 syscnt interval path differs from generic block-average paths; capture exporter binary and raw syscnt are not established.',
              'records': records, 'materialization_and_metadata_populations': gaps,
              'directional_copy_points': copy_points, 'joint_response_fits': fits,
              'identifiability_constraints': constraints,
              'parameter_changes': [], 'body_residual_used': False, 'new_costs': 0, 'new_raw_scans': 0,
              'producer_identity': identity(__file__)}
    output = DEST / 'scalar-dma-physical-constraints.json'
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    lines = ['# Scalar / DMA / routing physical evidence', '',
             'Six saved-capture passes preserve full native ABI, BlockNum, PMU numeric/missing populations and complete integer duration histograms inside already accepted Body windows. Every selected family exactly matches its previous retained population. The separately retained B16/32/64 directional copy audit is reused without another capture pass.', '',
             'No hardware rate or Body prediction changes here. Pipeline times overlap; signed sum/max differences are not classified as barriers or launch. Exporter owner aggregation and compiled dispatch remain distinct from source counts.', '',
             '| Source | Native / direction | Calls/F | Block | Duration Mean/P50 us | Scalar busy us | MTE2 busy us | MTE3 busy us |',
             '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in records:
        def value(field, key='mean'):
            item = r['pmu'].get(field, {}).get('statistics')
            return f"{item[key]:.3f}" if item else 'not exported'
        lines.append(f"| {r['source_case_id']} | {r['native_operator_type']} / {r['copy_direction'] or 'whole native'} | {r['calls_per_forward']:.0f} | {r['block_num']} | {value('Duration(us)')} / {value('Duration(us)', 'p50')} | {value('aiv_scalar_time(us)')} | {value('aiv_mte2_time(us)')} | {value('aiv_mte3_time(us)')} |")
    lines += ['', '| Copy direction | Pipe | Effective slope ns/source-program | Intercept us | R² |', '|---|---|---:|---:|---:|']
    for fit in fits:
        lines.append(f"| {fit['direction']} | {fit['field']} | {fit['slope_us_per_coordinate']*1000:.3f} | {fit['intercept_us']:.3f} | {fit['r_squared']:.4f} |")
    lines += ['', 'These six slopes are usable composite responses under the stated source schedule. Each point changes program count, metadata loads and bytes together: feature rank is one, so this dataset cannot split their independent prices. Negative intercepts or signed PMU remainders are retained, not clipped into a positive synchronization cost.', '',
              'DSQ uses a conditional 64 group-index GetValue scan per block across all three domains; changing capacity changes other scalar work without changing this count. Routing keeps the owner-zero E288 serial load/add chain while sort/SIMT/gather/quantization work changes. Neither population identifies an isolated GetValue, sort opcode or atomic RMW latency.', '',
              'All three GLM SparseFlashMlaMetadata populations are typed AI_CPU / Block0 with missing AIV/AIC counters. They stay model-body dependencies and are not represented as Vector service or discarded as tail control. Full Slice populations now have independent ABI buckets; offsets/index values remain unobserved.', '',
              'Source hashes, complete counter populations, signed diagnostics, conditional counts and concrete missing contrasts are retained in scalar-dma-physical-constraints.json.']
    (DEST / 'scalar-dma-physical-constraints.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'native_records': len(records), 'slice_metadata_records': len(gaps), 'joint_fits': len(fits)}))


if __name__ == '__main__':
    main()
