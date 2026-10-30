"""[Role] Inventory full captures and reconcile every accepted Body HCCL population.
[Invariants] Capture signatures have no phase label. Body groups reuse exact
  accepted endpoints and all observed geometries. Controller aliases are an
  overlay, never a Body subtraction or invented task-to-collective connection.
[Timeouts & Locks] One source stream/active forward, 180 s / 5M rows; <=512 MiB.
[Side-Effect Policy] Local reads and new evidence only; no simulation, collection,
  remote access, runtime mutation, or prediction-rate fitting.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards, _TAIL_NAMES
from mindie_profiler.sources_csv import probe_csv
from collect_a5_tp_hccl import HcclLedger, category, geometry_key, raw_stream, relevant
from targeted_native_pmu import NativePmu
from replay_body_operator_families import duration_stats, identity, read, write


def implementation(event):
    return 'hcom_summary' if category(event) == 'collective_envelope_only' else event.name


def collector_identity():
    import mindie_profiler
    paths = sorted(Path(mindie_profiler.__file__).resolve().parent.glob('*.py'))
    paths += [Path(__file__).resolve(),Path(__file__).with_name('collect_a5_tp_hccl.py'),
              Path(__file__).with_name('targeted_native_pmu.py'),
              Path(__file__).with_name('replay_body_operator_families.py')]
    return {str(path.resolve()):identity(path)['sha256'] for path in paths}


class Inventory:
    def __init__(self, header):
        self.header, self.groups = header, {}
        self.rows, self.positive_rows = 0, 0

    def add(self, event, raw):
        self.rows += 1;self.positive_rows += event.duration_ns>0
        if raw is None:
            return
        key = event.op_type,implementation(event),event.core,event.task_type,category(event)
        if key not in self.groups:
            self.groups[key]={'native_operator_type':event.op_type,'implementation_name':implementation(event),
                'accelerator_core':event.core,'parser_task_type':event.task_type,'event_category':category(event),
                'durations':Counter(),'tasks':Counter(),'pmu':NativePmu(self.header),
                'tensor_descriptors':Counter(),'explicit_link_fields':defaultdict(Counter)}
        group=self.groups[key];group['durations'][event.duration_ns]+=1;group['tasks'][event.task_id]+=1
        group['pmu'].add(raw,event,forward_id=None,layer_id=None)
        descriptors=tuple(raw.get(k) for k in ('Input Shapes','Input Data Types','Input Formats','Output Shapes','Output Data Types','Output Formats'))
        group['tensor_descriptors'][descriptors]+=1
        for name,value in raw.items():
            if any(token in name.lower() for token in ('byte','payload','link','connection','parent','algorithm','transport','remote rank','local rank','channel')):
                group['explicit_link_fields'][name][value]+=1

    def finish(self):
        result=[]
        for group in self.groups.values():
            hist=group['durations'];tasks=group['tasks']
            result.append({key:value for key,value in group.items() if key not in
                {'durations','tasks','pmu','tensor_descriptors','explicit_link_fields'}} | {
                'scope':'complete_capture; phase_unclassified','duration_ns_counter':sorted(hist.items()),
                'observed_us':duration_stats(hist,1000),'raw_pmu':group['pmu'].result(),
                'distinct_task_ids':len(tasks),'task_ids_repeat':any(n>1 for task,n in tasks.items() if task not in ('','N/A','None')),
                'native_tensor_descriptor_counter':[[list(tensors),n] for tensors,n in group['tensor_descriptors'].items()],
                'explicit_link_field_counters':{k:sorted(v.items(),key=lambda item:str(item[0])) for k,v in group['explicit_link_fields'].items()},
                'includes_duplicate_summary_rows':group['event_category']=='collective_envelope_only',
                'can_add_to_other_categories':False})
        return sorted(result,key=lambda g:-g['observed_us']['count'])


def adjacent_inventory(path):
    root=path.parent
    if 'mindie-sim-data' not in path.parts:
        return {'searched_root':str(root),'files':[{'path':str(path),'size_bytes':path.stat().st_size}],
            'scope':'staged CSV only; enclosing temporary directory is not a capture root',
            'separate_associated_artifact_ledger':'associated-artifacts.json',
            'other_rank_files_are_inventory_only':True,'no_remote_originals_fetched':True}
    if root.parent.name=='ranks':root=root.parent.parent
    files=[]
    for child in root.rglob('*'):
        if not child.is_file():continue
        name=child.name.lower()
        if any(word in name for word in ('communication','hccl','task_time','step_trace','kernel_details','op_summary','.db','.tar','.zip')):
            files.append({'path':str(child),'size_bytes':child.stat().st_size})
            if len(files)>1024:raise ValueError('associated_capture_artifact_inventory_exceeds_1024')
    return {'searched_root':str(root),'files':files,'other_rank_files_are_inventory_only':True,
        'no_remote_originals_fetched':True}


def extract(entry, input_pin, output):
    started=time.perf_counter();pins=collector_identity()
    body_pin=entry['body_identity'];body=read(body_pin['path'])
    if identity(body_pin['path'])!=body_pin:raise ValueError('accepted_body_changed')
    path=Path(entry['source']['path']);source_pin=identity(path)
    if any(source_pin[k]!=entry['source'][k] for k in ('sha256','size_bytes')):
        raise ValueError('capture_source_changed')
    stat=path.stat();schema=probe_csv(path);inventory=Inventory(schema.header)
    expected={f['forward_id']:f for f in body['forwards']};seen=set();bins={};raw_counts=Counter()
    by_geometry=defaultdict(list)
    for forward in body['forwards']:by_geometry[geometry_key(forward['geometry'])].append(forward)
    for key,forwards in by_geometry.items():
        bins[key]=HcclLedger.retained_windows(entry['model_config'],schema,forwards)
    aliases=Counter();alias_examples=[];extra_aligned=[]
    def consume(aligned,events):
        fid=aligned['forward_id']
        if fid not in expected:
            extra_aligned.append(fid);return
        old=expected[fid]
        if fid in seen or any(aligned[k]!=old[k] for k in
            ('start_ns','end_ns','head_start_ns','head_end_ns','query_rows','device_id','geometry')):
            raise ValueError('retained_body_boundary_or_geometry_changed:'+str(fid))
        seen.add(fid)
        raw={event.locator['csv_line']:event.pmu_provenance['hccl_raw_fields']
             for event in events if 'hccl_raw_fields' in event.pmu_provenance}
        bins[geometry_key(old['geometry'])].consume(old,aligned,events,raw)
        for event in events:
            if not old['start_ns']<=event.start_ns<old['end_ns'] or category(event)!='unlinked_aicpu_wrapper':continue
            normalized=event.op_type.replace('_','').lower()
            supported={name.replace('_','').lower() for name in _TAIL_NAMES}
            if normalized in supported and event.op_type not in _TAIL_NAMES:
                aliases[event.op_type]+=1
                if len(alias_examples)<5:
                    alias_examples.append({'op_type':event.op_type,'locator':event.locator,'forward_id':fid,
                        'start_ns':event.start_ns,'end_ns':event.end_ns,'body_end_ns':old['end_ns'],
                        'typed_core':event.core,'same_normalized_supported_name':True,
                        'body_endpoint_modified':False,'parent_child_relation_proven':False})
    def stream():
        for event,raw in raw_stream(path,schema):
            inventory.add(event,raw)
            if raw is not None:
                # This metadata lives exactly as long as the shared front-end's
                # active segment. No external full-capture event dictionary.
                event.pmu_provenance['hccl_raw_fields']=raw
            yield event
    replay=auto_segment_decode_forwards(stream(),entry['model_config'],on_forward=consume,
        max_detailed_forwards=0,max_samples_per_layer=0,max_forwards=max(1024,len(expected)+16))
    if seen!=set(expected):raise ValueError('accepted_body_population_not_reproduced')
    geometries=[]
    for key,ledger in bins.items():
        geometries.append({'geometry':ledger.expected[0]['geometry'],'forward_count':len(ledger.expected),
            'forward_ids':[f['forward_id'] for f in ledger.expected],'groups':ledger.finish(),
            'counts':dict(ledger.counts),'per_forward':ledger.per_forward,
            'summary_duplicate_examples':ledger.summary_pairs})
    prior9=Path(__file__).parent/'acceptance-20261030-a5-tp-hccl'/f'{entry["case_id"]}-hccl-ledger.json'
    prior_check=None
    if prior9.exists():
        old=read(prior9);new=next(g for g in geometries if geometry_key(g['geometry'])==geometry_key(old['geometry']))
        def histograms(groups):
            values=defaultdict(Counter)
            for g in groups:
                if g['native_operator_type'].startswith('hcom_'):
                    values[g['native_operator_type']].update({int(v):n for v,n in g['duration_ns_counter']})
            return dict(values)
        if histograms(old['groups'])!=histograms(new['groups']) or old['forward_count']!=new['forward_count']:
            raise ValueError('old_nine_primary_collective_population_changed')
        prior_check={'identity':identity(prior9),'primary_body_count':old['forward_count'],
                     'all_primary_collective_duration_histograms_unchanged':True,
                     'reason_for_additional_scan':'Full capture inventory and previously unselected accepted geometries were outside earlier scope.'}
    if collector_identity()!=pins or identity(body_pin['path'])!=body_pin:
        raise ValueError('collector_or_accepted_body_changed_during_scan')
    if (path.stat().st_size,path.stat().st_mtime_ns)!=(stat.st_size,stat.st_mtime_ns):
        raise ValueError('source_changed_during_scan')
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    if rss>512*1024**2:raise MemoryError('capture_ledger_exceeds_512MiB')
    result={'schema_version':'mindie-capture-and-body-hccl-ledger/1','status':'completed','case_id':entry['case_id'],
        'input_manifest_identity':input_pin,'source_identity':entry['source'],'body_acceptance_identity':body_pin,
        'case_identity':entry['case_identity'],'model_topology_exported_from_existing_sim':True,
        'hardware_sku':entry['hardware_sku'],'tp':entry['tp'],'dp':entry['dp'],'ep':entry['ep'],
        'runtime_source_identity':pins,'header':list(schema.header),'associated_artifacts':adjacent_inventory(path),
        'capture_inventory':inventory.finish(),'capture_parsed_event_count':inventory.rows,
        'body_count':len(expected),'geometry_count':len(geometries),'body_geometry_groups':geometries,
        'controller_alias_overlay':{'counts':dict(aliases),'examples':alias_examples,'body_spans_changed':False,
            'normalization_only_not_transport_association':True},
        'prior_nine_primary_population_validation':prior_check,'extra_current_alignment_forward_ids':extra_aligned,
        'accepted_endpoints_geometry_population_unchanged':True,
        'execution':{'raw_scans':1,'source_hash_reads':1,'scan_scope':'entire CSV to EOF',
            'elapsed_seconds':time.perf_counter()-started,'maximum_resident_set_size_bytes':rss,'predictions':0},
        'interpretation':['Capture signatures are phase-unclassified; Body geometry groups reuse existing measured windows.',
            'Only exact duplicate HCOM summary/device rows are deduplicated inside Body; capture inventory preserves original rows.',
            'AICPU, SDMA, Notify, CCU and fused network programs remain separate without explicit relationship evidence.',
            'No source template/algorithm, payload bytes, peer waiting cause or bandwidth is inferred from elapsed time.']}
    target=output/f'{entry["case_id"]}-capture-hccl.json';write(target,result)
    print(json.dumps({'case':entry['case_id'],'bodies':len(expected),'geometries':len(geometries),
        'capture_signatures':len(inventory.groups),'rows':inventory.rows,'seconds':round(result['execution']['elapsed_seconds'],3),
        'rss_mib':round(rss/1024**2,2),'controller_aliases':dict(aliases)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--case-id',required=True);parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();data=read(args.inputs);entry=next(c for c in data['cases'] if c['case_id']==args.case_id)
    args.output_dir.mkdir(parents=True,exist_ok=True);extract(entry,identity(args.inputs),args.output_dir)
