"""Join retained grouped PMU populations to source schedule coordinates.

[Role] Export usable whole-call responses and bounded source-count constraints.
[Invariants] Storage M is not valid M; tile submissions are not DMA descriptors.
  PMU pipes overlap and exporter aggregation is not presumed to be per owner.
[Timeouts & Locks] One retained JSON at a time, no capture reads, costs or locks.
[Side-Effect Policy] Writes grouped-* evidence only; changes no hardware rates.
"""
from collections import Counter
from pathlib import Path
import argparse
import json
from math import ceil
import sys

from collect_scalar_dma_pmu import identity, read
from summarize_scalar_dma_services import signed_diagnostics

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/observations/sources'
RECEIPT = DATA / 'arch3510-physical-services/grouped-extraction-receipt.json'


def histogram_stats(histogram):
    counts = Counter(dict(histogram)); total = sum(counts.values())
    if not total:
        raise ValueError('empty_grouped_population')
    ordered = sorted(counts.items())

    def at(position):
        cumulative = 0
        for duration, count in ordered:
            cumulative += count
            if position < cumulative:
                return duration
        raise ValueError('histogram_population_mismatch')

    def quantile(fraction):
        position = (total-1)*fraction; low = int(position)
        return (at(low)+(at(min(low+1,total-1))-at(low))*(position-low))/1000

    return {'count': total, 'mean_us': sum(ns*n for ns,n in ordered)/total/1000,
            'p50_us': quantile(.5), 'p90_us': at(ceil(total*.9)-1)/1000,
            'min_us': ordered[0][0]/1000, 'max_us': ordered[-1][0]/1000}


def native_coordinates(partition):
    """Logical axes from full ABI, leaving unexported route contents unknown."""
    abi = partition['native_abi']; inputs, outputs = abi[2:]
    x, y = inputs[0], outputs[0]
    group_lists = [t for t in inputs if t[1] == 'int64' and len(t[0]) == 1]
    if len(group_lists) != 1 or len(x[0]) != 2 or len(y[0]) != 2:
        raise ValueError('grouped_native_axes_not_unique')
    fused = partition['native_operator_type'] == 'GroupedMatmulSwigluQuantV2'
    weight = inputs[3] if fused else inputs[1]
    return {'input_buffer_capacity_rows': x[0][0], 'output_buffer_capacity_rows': y[0][0],
            'matrix_n': y[0][1]*(2 if fused else 1), 'matrix_k': x[0][1],
            'stored_expert_banks': group_lists[0][0][0],
            'activation_dtype': x[1], 'weight_dtype': weight[1], 'output_dtype': y[1],
            'group_list_descriptor': group_lists[0], 'observed_valid_rows': None,
            'observed_active_experts': None, 'observed_expert_rows': None,
            'capacity_equals_valid_rows': False}


def source_branch(partition, architecture):
    coordinates = native_coordinates(partition)
    if architecture == 'arch22':
        return {'candidate': 'A8W4_MSD_double_row', 'observed_dispatch_confirmed': False,
                'source_formula': 'sum_e ceil(2*valid_rows[e]/base_m)*ceil(N/base_n)',
                'tile_constants': {'up': [128,256,256], 'down_short': [64,512], 'down_tall': [128,256]},
                'host_down_predicate': 'floor(valid_M/stored_expert_banks) < 32',
                'counter_scope': 'whole native invocation; per-owner tile counts separately retained',
                'compiled_dma_descriptor_count': None}
    if coordinates['output_dtype'] == 'int32':
        return {'candidate': 'arch35_INT32_output_without_dequant_epilogue',
                'observed_dispatch_confirmed': False,
                'source_formula': None,
                'excluded_candidate': 'BF16_GMM_DEQUANT_VECTOR_GQmmMixRegbaseKernel',
                'reason': 'Pinned AnalyzeInputs returns before scale/dequant mode when output is INT32.',
                'compiled_dma_descriptor_count': None}
    return {'candidate': 'V310_GMM_QUANT_MIX_GMM_DEQUANT_VECTOR_no_transpose',
            'observed_dispatch_confirmed': False,
            'source_formula': 'sum_e ceil(valid_rows[e]/base_m)*ceil(N/base_n), then source last-group tail split',
            'owner_order': 'four-row window; rotation persists across nonempty experts',
            'native_scale_dtype': partition['native_abi'][2][3][1],
            'adapter_count_boundary': 'Geometric schedule only; FP32 adapter scale-byte offsets do not describe this BF16 scale tensor.',
            'unobserved_selection': ['base_m','base_n','base_k','group_list_type','group_list_values','transpose_attributes','tiling_key'],
            'compiled_dma_descriptor_count': None}


def complete_pmu(partition):
    pmu = partition['raw_pmu']; n = pmu['event_count']
    fields = {k: {f:v for f,v in value.items() if f != 'numeric_value_counter'}
              for k,value in pmu['fields'].items() if k.endswith('_time(us)') or k in ('Duration(us)','Wait Time(us)')}
    means = {k: (v['statistics']['mean'] if v['numeric_count'] == n else None)
             for k,v in fields.items()}
    # A3/A5 exporter values stay at their original aggregate scope. Do not
    # divide them by BlockNum or pair them with all-owner instruction sums.
    aic = {k:means.get(k) for k in ('aicore_time(us)','aic_mac_time(us)','aic_mte1_time(us)',
                                  'aic_mte2_time(us)','aic_fixpipe_time(us)','aic_scalar_time(us)')}
    return {'fields': fields, 'complete_numeric_mean_us': means,
            'aiv_signed_diagnostics': signed_diagnostics(pmu), 'aic_original_scope_mean_us': aic,
            'owner_aggregation': 'capture exporter not identified; raw units retained',
            'isolated_descriptor_or_scalar_price_ns': None}


def conditional_a3_schedule(entry, partition, gate_schedule, down_schedule):
    """Reuse Sim's source arithmetic under the saved balanced-routing declaration."""
    c = native_coordinates(partition); raw = read(entry['case_identity']['path'])
    runtime = raw['runtime']; topk = entry['model_config']['top_k']
    numerator = entry['geometry']['query_rows']*topk
    ep = runtime['ep']
    if numerator % ep or runtime['routing']['policy'] != 'balanced':
        raise ValueError('conditional_balanced_source_domain_changed')
    m = numerator//ep; banks = c['stored_expert_banks']
    rows = tuple(m//banks+(i<m % banks) for i in range(banks))
    owners = int(partition['block_num']); aivs = int(partition['mix_block_num'])
    function = gate_schedule if partition['role'] == 'expert_up_activation_quant' else down_schedule
    schedule = function(m,c['matrix_n'],c['matrix_k'],rows,aic_owners=owners,aiv_owners=aivs)
    return {'basis': 'retained balanced Sim routing declaration, not captured group-list values',
            'case_identity': entry['case_identity'], 'query_rows': entry['geometry']['query_rows'],
            'top_k': topk, 'ep': ep, 'declared_valid_rows': m, 'declared_expert_rows': rows,
            'active_experts': schedule.active_experts, 'stored_expert_banks': banks,
            'base_m': schedule.base_m, 'base_n': schedule.base_n,
            'matrix_output_tile_count': schedule.tile_count,
            'matrix_tiles_per_aic_owner': {r.owner:r.tiles for r in schedule.matrix},
            'all_bank_source_scan_count': schedule.expert_scan_count,
            'source_matrix_set_tensor_a_submissions': schedule.tile_count,
            'source_matrix_set_tensor_b_submissions': schedule.tile_count,
            'compiled_dma_descriptor_count': None,
            'not_an_observed_route_or_dispatch': True,
            'no_latency_divided_by_conditional_tile_count': True}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--sim-source',type=Path,required=True)
    args = parser.parse_args(); sys.path.insert(0,str(args.sim_source))
    from mindie_sim.prediction.w4a8_schedule import gate_schedule,down_schedule
    from mindie_sim.prediction.w4a8 import SOURCE
    from mindie_sim.prediction.operators.quant_grouped_schedule import SOURCE_REVISION,_SOURCE_FILES,SOURCE_ROOT
    module_paths = ['mindie_sim/prediction/w4a8_schedule.py','mindie_sim/prediction/w4a8.py',
                    'mindie_sim/prediction/operators/quant_grouped_schedule.py']
    modules = {p:identity(args.sim_source/p) for p in module_paths}
    inputs_path = DATA/'arch3510-physical-services/grouped-inputs.json'
    inputs = {x['case_id']:x for x in read(inputs_path)['cases']}; receipt = read(RECEIPT)
    records = {'arch22':[],'arch3510':[]}
    for source in receipt['cases']:
        pin = source['output_identity']; evidence = read(pin['path'])
        if identity(pin['path']) != pin: raise ValueError('grouped_retained_partition_changed')
        entry = inputs[evidence['case_id']]
        for index,part in enumerate(evidence['partitions']):
            stats = histogram_stats(part['duration_ns_counter'])
            if stats['count'] != part['raw_pmu']['event_count']: raise ValueError('pmu_population_differs')
            record = {'case_id':evidence['case_id'],'architecture':evidence['architecture'],
                'hardware':evidence['hardware'],'source_identity':evidence['source_identity'],
                'partition_identity':pin,'partition_index':index,'body_identity':evidence['body_identity'],
                'geometry':evidence['geometry'],'forward_count':evidence['forward_count'],
                'native_operator_type':part['native_operator_type'],'role':part['role'],
                'attention_kind':part['attention_kind'],'native_abi':part['native_abi'],
                'accelerator_core':part['accelerator_core'],'block_num':part['block_num'],
                'mix_block_num':part['mix_block_num'],'layer_counts':part['layer_counts'],
                'observed':stats,'calls_per_forward':stats['count']/evidence['forward_count'],
                'native_coordinates':native_coordinates(part),'source_branch':source_branch(part,evidence['architecture']),
                'pmu':complete_pmu(part),'usable_response': 'whole native call joint response in this complete ABI/Block/attention domain',
                'generalization': 'in_sample; no arbitrary valid-row, tile or owner extrapolation',
                'body_residual_used':False,'parameter_changes':[]}
            if evidence['architecture'] == 'arch22':
                record['conditional_source_counts'] = conditional_a3_schedule(entry,part,gate_schedule,down_schedule)
                record['source_provenance'] = SOURCE
            else:
                record['source_provenance'] = {'revision':SOURCE_REVISION,'files':_SOURCE_FILES,
                    'INT32_host_branch':{'path':str(Path(SOURCE_ROOT)/_SOURCE_FILES[-1]['path']),
                                         'sha256':_SOURCE_FILES[-1]['sha256'],'lines':'884-921'},
                    'BF16_dispatch':{'path':str(Path(SOURCE_ROOT)/_SOURCE_FILES[0]['path']),
                                      'sha256':_SOURCE_FILES[0]['sha256'],'lines':'336-348'}}
            records[evidence['architecture']].append(record)
    if any(identity(args.sim_source/p)!=pin for p,pin in modules.items()):
        raise ValueError('source_schedule_changed')
    for arch,rows in records.items():
        result = {'schema_version':'mindie-grouped-source-pmu-constraints/1','status':'completed',
            'extraction_receipt_identity':identity(RECEIPT),'source_modules':modules,
            'producer_identity':identity(__file__),'records':rows,
            'identifiability': {
                'usable': 'Complete observed whole-call and individual PMU-field responses; source-conditional tile coordinates where independently declared.',
                'unidentified': ['actual group-list values/active experts','captured host tiling/binary',
                    'MatmulImpl internal DMA descriptor count','exporter owner aggregation','independent descriptor/scalar/byte/sync rates'],
                'next_contrast': 'At fixed N/K/dtype/Block, retain route counts and host tiling; vary active groups at fixed total valid M, then vary tile boundaries at fixed bytes. Keep native inclusive and owner PMU scopes separate.',
                'no_pipe_subtraction_as_exclusive_latency':True},
            'new_raw_scans':0,'new_costs':0,'body_residual_used':False}
        dest = DATA/f'{arch}-physical-services/grouped-source-constraints.json'
        dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        lines = ['# Grouped source / PMU joint constraints','',
            'Each row retains its complete native ABI, integer call histogram, layer population and original Block/PMU scope. Capacity is not valid routed M. These are usable whole-call responses, not inferred descriptor prices. No new capture scan or prediction occurs in this join.','',
            '| Source | Role / attention | Capacity | Calls/F | Mean/P50 us | AIC MTE2 us | AIV scalar us | AIV MTE2 us |',
            '|---|---|---:|---:|---:|---:|---:|---:|']
        for r in rows:
            means=r['pmu']['complete_numeric_mean_us']
            def val(k):
                field=r['pmu']['fields'].get(k)
                if not field or not field['numeric_count']:return 'no numeric values'
                suffix=(f" ({field['numeric_count']}/{r['observed']['count']} numeric)"
                        if means.get(k) is None else '')
                return f"{field['statistics']['mean']:.3f}"+suffix
            o=r['observed'];lines.append(f"| {r['case_id']} | {r['role']} / {r['attention_kind']} | {r['native_coordinates']['input_buffer_capacity_rows']} | {r['calls_per_forward']:.0f} | {o['mean_us']:.3f}/{o['p50_us']:.3f} | {val('aic_mte2_time(us)')} | {val('aiv_scalar_time(us)')} | {val('aiv_mte2_time(us)')} |")
        lines += ['', 'A numeric-subset PMU mean is explicitly marked with its own denominator and is excluded from arithmetic against complete-call means. A3 count examples reuse the source schedule under the saved balanced-routing assumption, not observed group-list values. Source SetTensor submissions are not compiled DMA descriptors. A5 INT32 up is separate from the mixed BF16 dequant branch; the latter supports a geometric schedule only after actual routing and host tile selection are known. Neither BlockNum nor an all-owner count may divide an exporter aggregate into a per-core price. Signed PMU differences remain diagnostics.']
        dest.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'records':{k:len(v) for k,v in records.items()},'raw_scans':0,'costs':0}))


if __name__ == '__main__': main()
