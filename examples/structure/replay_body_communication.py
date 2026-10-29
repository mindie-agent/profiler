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
from mindie_profiler.normalized import kernel_rows, shapes
from mindie_sim.cohort_comparison import _predict
from mindie_sim.prediction.operator_analysis import target_graphs
from mindie_sim.prediction.program import RecipeBook
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from replay_body_operator_families import (BASE, read, write, digest, identity,
    runtime_identity, duration_stats, deduplicate_communication, declared_role)


def communication_regions(result, segment, config):
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
    body=[event for event in segment if event.op_type.startswith('hcom_')
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
        self.groups={};self.forward_ids=[];self.duplicate_count=0;self.unresolved=Counter()

    def __call__(self,result,segment):
        expected=self.expected[result['forward_id']]
        if any(result[key]!=expected[key] for key in ('start_ns','end_ns','head_start_ns','head_end_ns','query_rows','device_id')):
            raise ValueError('retained_body_boundary_changed')
        self.forward_ids.append(result['forward_id'])
        rows,duplicates=communication_regions(result,segment,self.config)
        self.duplicate_count+=duplicates
        for event,layer,block in rows:
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
                'declared_roles':set(),'layer_ids':set(),'durations':Counter(),
                'layer0_durations':Counter(),'steady_durations':Counter(),'examples':[]})
            group['declared_roles'].add(declared_role(target));group['layer_ids'].add(layer['layer_id'])
            group['durations'][event.duration_ns]+=1
            group['layer0_durations' if layer['layer_id']==0 else 'steady_durations'][event.duration_ns]+=1
            if len(group['examples'])<2:
                group['examples'].append({'event_id':event.event_id,'locator':event.locator,
                    'forward_id':result['forward_id'],'layer_id':layer['layer_id'],
                    'start_ns':event.start_ns,'end_ns':event.end_ns,'target_id':target['node_id']})

    def finish(self):
        if set(self.forward_ids)!=set(self.expected):raise ValueError('body_population_changed')
        groups=[]
        for group in self.groups.values():
            row={key:value for key,value in group.items() if not key.endswith('durations')}
            row['declared_roles']=sorted(group['declared_roles']);row['layer_ids']=sorted(group['layer_ids'])
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
        'forward_count':len(consumer.forward_ids),'groups':consumer.finish(),
        'unresolved_event_counts':dict(consumer.unresolved),'duplicate_summary_count':consumer.duplicate_count,
        'scan_counts':scanned['scan_counts'],'runtime_source_identity':before,'runtime_sources_unchanged':True,
        'script_identity':identity(__file__),'elapsed_seconds':round(time.perf_counter()-started,3),'raw_capture_scans':1}
    path=output/f"body-communication-{actual['case_id']}.actual.json";write(path,result)
    return path


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
            'scored_cohort_count':0})
    return {'case_id':actual['case_id'],'actual_identity':identity(path),'source_identity':actual['source_identity'],
            'forward_count':actual['forward_count'],'groups':rows,'unresolved_event_counts':actual['unresolved_event_counts']}


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
