"""[Role] Reconcile real body communication by layer kind and physical program.
[Invariants] Complete topology alignment conditions roles; HCOM elapsed includes
  peer waits. Incompatible physical programs remain separate and never score
  tensor cohorts. Existing operator-family replay artifacts are immutable inputs.
[Timeouts & Locks] One active forward; serial scans and local program prediction.
[Side-Effect Policy] Read retained local captures; write separate communication
  reports. No remote access, device execution or bandwidth fitting.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from pathlib import Path
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards, _Row, _anchor, _norm
from mindie_profiler.normalized import kernel_rows, shapes, row_from_event
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.tensor_contracts import observed_contract
from mindie_sim.cohort_comparison import _predict
from mindie_sim.prediction.operator_analysis import target_graphs
from mindie_sim.prediction.program import RecipeBook
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from replay_body_operator_families import (BASE, read, write, digest, identity,
    runtime_identity, duration_stats, deduplicate_communication, declared_role)


GAP_TYPES={"AddRmsNormDynamicQuant","AddRmsNormDynamicMxQuant","DynamicQuantV2",
    "split_qkv_rmsnorm_mrope_kernel","_layer_norm_fwd_1pass_kernel_npu",
    "l2norm_fwd_kernel2","AddRmsNorm"}


def communication_regions(result, segment, config, include_types=()):
    """Only native collectives inside a complete body; retain real task durations."""
    layers=[row for row in result['stages'] if row['layer_id'] is not None]
    starts=[row['start_ns'] for row in layers]
    ffn_starts={}
    for layer in layers:
        rows=[_Row(event,shapes(event.input_shapes),shapes(event.output_shapes))
              for event in segment if layer['start_ns']<=event.start_ns<layer['evidence']['successor_boundary_start_ns']]
        anchor=next(row.event.start_ns for row in rows if _anchor(row,config))
        ffn_starts[layer['layer_id']]=next(row.event.start_ns for row in rows
             if row.event.start_ns>anchor and _norm(row,config['hidden_size']))
    body=[event for event in segment if (event.op_type.startswith('hcom_') or event.op_type in include_types)
          and result['start_ns']<=event.start_ns<event.end_ns<=result['end_ns']]
    body,duplicates=deduplicate_communication(body)
    selected=[]
    for event in body:
        layer=layers[bisect_right(starts,event.start_ns)-1]
        block='attention' if event.start_ns<ffn_starts[layer['layer_id']] else 'ffn'
        selected.append((event,layer,block))
    return selected,len(duplicates)


def declared_programs(manifest):
    result={}
    for node in manifest['nodes']:
        if node['family']=='allreduce' and node.get('layer') is not None:
            result.setdefault((node['layer'],node.get('block')),[]).append(node)
    return result


class CommunicationConsumer:
    def __init__(self,manifest,expected,config):
        self.manifest,self.expected,self.config=manifest,expected,config
        self.programs=declared_programs(manifest)
        self.groups={};self.gaps={};self.forward_ids=[];self.duplicate_count=0;self.unresolved=Counter()

    def __call__(self,result,segment):
        expected=self.expected[result['forward_id']]
        if any(result[key]!=expected[key] for key in ('start_ns','end_ns','head_start_ns','head_end_ns','query_rows','device_id')):
            raise ValueError('retained_body_boundary_changed')
        self.forward_ids.append(result['forward_id'])
        rows,duplicates=communication_regions(result,segment,self.config,GAP_TYPES)
        self.duplicate_count+=duplicates
        for event,layer,block in rows:
            if event.op_type in GAP_TYPES:
                self.add_gap(event,layer,block)
                continue
            targets=self.programs.get((layer['layer_id'],block),[])
            if len(targets)!=1 or not event.op_type.startswith('hcom_allReduce'):
                self.unresolved['collective_role_not_unique']+=1
                continue
            target=targets[0]
            key=(event.op_type,layer['attention'],block,target['physical_signature'])
            group=self.groups.setdefault(key,{'native_operator_type':event.op_type,
                'attention_kind':layer['attention'],'block':block,
                'physical_signature':target['physical_signature'],
                'physical_work':target['physical_work'],'representative_target':target,
                'declared_roles':set(),'layer_ids':set(),'layer_call_counts':Counter(),'durations':Counter(),
                'layer0_durations':Counter(),'steady_durations':Counter(),'examples':[]})
            group['declared_roles'].add(declared_role(target));group['layer_ids'].add(layer['layer_id'])
            group['layer_call_counts'][layer['layer_id']]+=1
            group['durations'][event.duration_ns]+=1
            group['layer0_durations' if layer['layer_id']==0 else 'steady_durations'][event.duration_ns]+=1
            if len(group['examples'])<2:
                group['examples'].append({'event_id':event.event_id,'locator':event.locator,
                    'forward_id':result['forward_id'],'layer_id':layer['layer_id'],
                    'start_ns':event.start_ns,'end_ns':event.end_ns,'target_id':target['node_id']})

    def add_gap(self,event,layer,block):
        row=row_from_event(event);native=native_tensor_contract(row);shared=observed_contract(row)
        raw={'input_shapes':event.input_shapes,'input_dtypes':event.input_dtypes,
             'input_formats':event.input_formats,'output_shapes':event.output_shapes,
             'output_dtypes':event.output_dtypes,'output_formats':event.output_formats}
        key=(event.op_type,layer['attention'],block,repr(native),repr(raw))
        group=self.gaps.setdefault(key,{'native_operator_type':event.op_type,
            'attention_kind':layer['attention'],'block':block,'native_tensor_contract':native,
            'shared_observed_contract':shared,'raw_tensor_descriptors':raw,'durations':Counter(),
            'layer_ids':set(),'examples':[],
            'tensor_evidence':'complete_native_abi' if native is not None else 'missing_or_incomplete_native_abi'})
        group['durations'][event.duration_ns]+=1;group['layer_ids'].add(layer['layer_id'])
        if not group['examples']:
            group['declared_region_nodes']=[{key:node.get(key) for key in ('node_id','op_id','family','contract','physical_signature')}
                for node in self.manifest['nodes'] if node.get('layer')==layer['layer_id'] and node.get('block')==block]
        if len(group['examples'])<2:
            group['examples'].append({'event_id':event.event_id,'locator':event.locator,
                'layer_id':layer['layer_id'],'start_ns':event.start_ns,'end_ns':event.end_ns})

    def gap_rows(self):
        return [{**{key:value for key,value in row.items() if key not in {'durations','layer_ids'}},
                 'layer_ids':sorted(row['layer_ids']),'duration_ns_counter':sorted(row['durations'].items()),
                 'observed_us':duration_stats(row['durations'],1000),
                 'basis':'whole_body_topology_conditioned_region; contract_gaps_are_not_occurrence_bindings'}
                for row in self.gaps.values()]

    def finish(self):
        if set(self.forward_ids)!=set(self.expected):raise ValueError('body_population_changed')
        groups=[]
        for group in self.groups.values():
            row={key:value for key,value in group.items() if not key.endswith('durations')}
            row['declared_roles']=sorted(group['declared_roles']);row['layer_ids']=sorted(group['layer_ids'])
            row['layer_call_counts']=dict(sorted(group['layer_call_counts'].items()))
            row['observed_us']=duration_stats(group['durations'],1000)
            row['duration_ns_counter']=sorted(group['durations'].items())
            row['layer_groups']={key:{'observed_us':duration_stats(group[field],1000),
                  'duration_ns_counter':sorted(group[field].items())}
                for key,field in [('layer0','layer0_durations'),('steady_layers','steady_durations')]}
            row.update(status='reference_pending',evidence_strength='conditional_whole_body_layer_kind_and_collective_role',
                occurrence_binding_implied=False,communication_bandwidth_calibration_allowed=False,
                observed_boundary='native_device_collective_elapsed_including_peer_wait')
            groups.append(row)
        return groups


def extract_case(actual_path,output):
    before=runtime_identity();started=time.perf_counter()
    actual=read(actual_path);prior=read(actual['body_acceptance_identity']['path'])
    if identity(actual['body_acceptance_identity']['path'])!=actual['body_acceptance_identity']:
        raise ValueError('prior_body_report_changed')
    prefix=actual_path.with_name(actual_path.name.removesuffix('.actual.json'))
    case_path=prefix.with_suffix('.case.json');case=parse_case(read(case_path))
    geometry=actual['geometry'];context=actual['conditional_context_tokens']
    manifest=export_structure(case,phase='decode',tokens=geometry['tokens_per_sequence'],
            sequences=geometry['sequences_per_replica'],context=context,scope='body')
    config=case.model.to_dict();config.update(tp=case.runtime.parallel.tp)
    consumer=CommunicationConsumer(manifest,{row['forward_id']:row for row in prior['forwards']},config)
    source=Path(actual['source_identity']['path']);stat=(source.stat().st_size,source.stat().st_mtime_ns)
    if digest(source)!=actual['source_identity']['sha256']:raise ValueError('source_changed')
    scanned=auto_segment_decode_forwards(kernel_rows(source,rank_id='rank_0',rank_index=0,max_rows=1_000_000,timeout_s=180),
            config,on_forward=consumer,max_detailed_forwards=0,max_samples_per_layer=0)
    if stat!=(source.stat().st_size,source.stat().st_mtime_ns):raise ValueError('source_changed_during_scan')
    if before!=runtime_identity():raise ValueError('runtime_changed_during_scan')
    result={'schema_version':'mindie-body-communication-buckets/1','case_id':actual['case_id'],
        'actual_family_identity':identity(actual_path),'body_acceptance_identity':actual['body_acceptance_identity'],
        'source_identity':actual['source_identity'],'case_identity':identity(case_path),
        'graph_id':manifest['graph_id'],'declared_execution':manifest['execution'],'geometry':geometry,
        'forward_count':len(consumer.forward_ids),'groups':consumer.finish(),'contract_gap_families':consumer.gap_rows(),
        'unresolved_event_counts':dict(consumer.unresolved),'duplicate_summary_count':consumer.duplicate_count,
        'scan_counts':scanned['scan_counts'],'runtime_source_identity':before,'runtime_sources_unchanged':True,
        'script_identity':identity(__file__),'elapsed_seconds':round(time.perf_counter()-started,3),'raw_capture_scans':1,'source_hash_reads':1}
    # Re-segmentation must reproduce the historical measured HCOM multiset exactly.
    for block,role in [('attention','attention_output_communication'),('ffn','ffn_down_communication')]:
        old=Counter({int(v):int(n) for row in actual['families'] if row['declared_role']==role
                     for v,n in row['duration_ns_counter']})
        new=Counter()
        for group in result['groups']:
            if group['block']==block:new.update(dict(group['duration_ns_counter']))
            if any(count!=result['forward_count'] for count in group['layer_call_counts'].values()):
                raise ValueError('collective_multiplicity_changed')
        if old!=new:raise ValueError('historical_collective_population_changed')
    result['historical_collective_population_unchanged']=True
    path=output/f"body-communication-{actual['case_id']}.actual.json";write(path,result)
    return path


def gap_references(actual,case,manifest,by_id,book):
    """Missing capture ABI can expose existing model work, without inventing binds."""
    results=[]
    for group in actual['contract_gap_families']:
        kind=group['native_operator_type'];layers=set(group['layer_ids'])
        nodes=[node for node in manifest['nodes'] if node.get('layer') in layers and node.get('block')==group['block']]
        source_roles={'l2norm_fwd_kernel2':{'decode_q_l2norm','decode_k_l2norm'},
                      '_layer_norm_fwd_1pass_kernel_npu':{'linear_output_norm_gate'}}
        target_kind='node';basis='conditional_source_role_existing_model_program'
        if kind in source_roles:
            selected=[node for node in nodes if declared_role(node) in source_roles[kind]]
        elif kind=='split_qkv_rmsnorm_mrope_kernel':
            selected=[node for node in manifest.get('subgraphs',[]) if node.get('layer') in layers and node.get('family')=='qkv_preprocess']
            target_kind='subgraph';basis='conditional_source_subgraph_existing_model_program'
        else:
            from mindie_profiler.structure_mapping import _freeze
            contracts={_freeze(value) for value in (group['native_tensor_contract'],group['shared_observed_contract']) if value is not None}
            selected=[node for node in nodes if node.get('contract') is not None and _freeze(node['contract']) in contracts and node.get('event_matchable') is not False]
            basis='tensor_contract_existing_model_program_reference'
        row={**group,'model_program_already_costed':bool(selected),'model_region_declared':bool(nodes),'additional_budget_allowed':False,
             'scored_cohort_count':0,'evidence_strength':basis,
             'observed_activity_ms_per_forward':sum(int(v)*int(n) for v,n in group['duration_ns_counter'])/actual['forward_count']/1e6}
        if not selected:
            row.update(status='boundary_unresolved',reason='native_fusion_or_complete_abi_boundary_not_declared',
                       predicted_service_ms_per_forward=None,predicted_reference_us=None)
            results.append(row);continue
        by_signature={}
        for target in selected:by_signature.setdefault(target['physical_signature'],[]).append(target)
        programs=[]
        for signature,targets in by_signature.items():
            prediction=_predict(case,targets[0],target_kind,by_id,book)
            programs.append({'physical_signature':signature,'target_count':len(targets),
                'target_ids':[target.get('node_id',target.get('subgraph_id')) for target in targets],
                'prediction':prediction})
        expected=len(selected)*actual['forward_count']
        row.update(declared_programs=programs,declared_expected_calls=expected,
                   multiplicity_matches=expected==group['observed_us']['count'])
        if expected!=group['observed_us']['count']:
            row.update(status='multiplicity_unresolved',predicted_service_ms_per_forward=None,predicted_reference_us=None)
        else:
            per_forward=sum(program['target_count']*program['prediction']['per_call_ms'] for program in programs)
            predicted_us=per_forward*actual['forward_count']/expected*1000
            row.update(status='reference_only',predicted_service_ms_per_forward=per_forward,
                predicted_reference_us=predicted_us,
                signed_activity_residual_ms_per_forward=per_forward-row['observed_activity_ms_per_forward'],
                aggregation_basis='declared_role_set_multiplicity; individual_call_identity_not_asserted',
                prediction_boundaries=sorted({program['prediction']['boundary'] for program in programs}))
        results.append(row)
    return results


def predict_case(path):
    actual=read(path);case=parse_case(read(actual['case_identity']['path']))
    geometry={key:actual['declared_execution'][key] for key in ('phase','tokens','context','sequences','scope')}
    manifest=export_structure(case,**geometry)
    if manifest['graph_id']!=actual['graph_id']:raise ValueError('communication_declaration_changed')
    book=RecipeBook.from_mapping(case.runtime.kernels)
    by_id={f'rank:{replica}/{op.op_id}':op for replica,ops in target_graphs(case,**geometry).items() for op in book.expand(ops)}
    rows=[]
    for group in actual['groups']:
        prediction=_predict(case,group['representative_target'],'node',by_id,book)
        predicted_us=prediction['per_call_ms']*1000;observed_us=group['observed_us']['mean']
        rows.append({**group,'status':'reference_only','prediction':prediction,
            'predicted_us':predicted_us,'per_call_diff_us':predicted_us-observed_us,
            'relative_error':predicted_us/observed_us-1,
            'reference_within_tolerance':abs(predicted_us-observed_us)<=(15 if observed_us<=50 else observed_us*.15),
            'scored_cohort_count':0,'model_program_already_costed':True,'additional_budget_allowed':False,
            'observed_activity_ms_per_forward':sum(int(v)*int(n) for v,n in group['duration_ns_counter'])/actual['forward_count']/1e6,
            'predicted_service_ms_per_forward':prediction['per_call_ms']*group['observed_us']['count']/actual['forward_count']})
    return {'case_id':actual['case_id'],'actual_identity':identity(path),'source_identity':actual['source_identity'],
            'forward_count':actual['forward_count'],'groups':rows,
            'source_role_gap_references':gap_references(actual,case,manifest,by_id,book),
            'unresolved_event_counts':actual['unresolved_event_counts']}


def render(report):
    lines=['# Complete Body Communication by Layer Kind and Physical Program','',
        'The buckets use complete model topology alignment. GDN and GQA collective programs stay separate. '
        'These are conditional references; native elapsed includes peer wait and cannot calibrate link bandwidth. '
        'They do not change the prior 12-arm operator scoreboard or enter its scored denominator.','',
        '| Case | Layer kind / block / declared role | Calls | Real mean us | Real P50 us | Sim reference us | Diff us | Reference tolerance |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for case in report['cases']:
        for row in sorted(case['groups'],key=lambda r:(r['block'],r['attention_kind'],r['physical_signature'])):
            label=f"{row['attention_kind']} / {row['block']} / {' + '.join(row['declared_roles'])}"
            lines.append(f"| {case['case_id']} | {label} | {row['observed_us']['count']} | {row['observed_us']['mean']:.3f} | "
                f"{row['observed_us']['p50']:.3f} | {row['predicted_us']:.3f} | {row['per_call_diff_us']:.3f} | "
                f"{'within' if row['reference_within_tolerance'] else 'outside'} (unscored) |")
    lines+=['','## Existing model programs behind capture ABI gaps','',
        'Per-forward values are kernel-activity sums, not body wall time. These programs already exist in Sim; '
        'their reference costs must not be added again. Unfused-subgraph references do not claim an atomic fused-kernel latency.','',
        '| Case | Native family / layer kind / block | Calls | Real mean / P50 us | Reference us | Real activity ms/forward | Sim service ms/forward | Status / boundary |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |']
    fmt=lambda value:'—' if value is None else f'{value:.3f}'
    for case in report['cases']:
        for row in case['source_role_gap_references']:
            label=f"{row['native_operator_type']} / {row['attention_kind']} / {row['block']}"
            lines.append(f"| {case['case_id']} | {label} | {row['observed_us']['count']} | {row['observed_us']['mean']:.3f} / {row['observed_us']['p50']:.3f} | "
                f"{fmt(row.get('predicted_reference_us'))} | {row['observed_activity_ms_per_forward']:.3f} | {fmt(row.get('predicted_service_ms_per_forward'))} | "
                f"{row['status']} / {' + '.join(row.get('prediction_boundaries',[]))} |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--directory',type=Path,default=BASE)
    parser.add_argument('--extract',action='store_true');parser.add_argument('--predict',action='store_true')
    parser.add_argument('--case-id',action='append');args=parser.parse_args()
    if not(args.extract or args.predict):parser.error('select --extract and/or --predict')
    if args.extract:
        for path in sorted(args.directory.glob('body-operator-*-source-gdn.actual.json')):
            if args.case_id and read(path)['case_id'] not in args.case_id:continue
            result=extract_case(path,args.directory);print(result,flush=True)
    if args.predict:
        before=runtime_identity();started=time.perf_counter();cases=[]
        for path in sorted(args.directory.glob('body-communication-*.actual.json')):
            if args.case_id and read(path)['case_id'] not in args.case_id:continue
            cases.append(predict_case(path))
        if before!=runtime_identity():raise ValueError('runtime_changed_during_prediction')
        report={'schema_version':'mindie-body-communication-references/1','status':'completed','cases':cases,
            'runtime_source_identity':before,'runtime_sources_unchanged':True,'script_identity':identity(__file__),
            'elapsed_seconds':round(time.perf_counter()-started,3),'raw_capture_reads':0,
            'scored_cohort_count':0,'historical_operator_scoreboard_identity':identity(args.directory/'body-operator-family-scoreboard.json')}
        write(args.directory/'body-communication-references.json',report)
        (args.directory/'body-communication-references.md').write_text(render(report))


if __name__=='__main__':main()
