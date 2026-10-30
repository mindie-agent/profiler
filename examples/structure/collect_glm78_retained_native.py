"""Fill GLM78 native ABI evidence inside already accepted Forward windows.

[Role] One local streaming pass per source, preserving complete native histograms.
[Invariants] Stored Body endpoints and selected geometry are immutable. Re-aligned
  layer topology must match those endpoints; no new Forward is admitted.
[Timeouts & Locks] One bounded Body buffer, serial sources, 180s parser budget.
[Side-Effect Policy] Read existing local captures; write new evidence; no device.
"""
import argparse
from bisect import bisect_right
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource
import time

from mindie_profiler.decode_segmentation import _align, _anchor, _model, _norm, _norm_start, _Row
from mindie_profiler.normalized import kernel_rows, row_from_event, shapes
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.sources_db import sha256_file
from mindie_sim.prediction.structure import parse_case
from replay_body_operator_families import duration_stats
from build_qwen_a3_service_cases import ROOT, OUT, read, write, identity


def extract(row):
    started=time.perf_counter()
    body_pin=identity(row['extraction_path']);prior=read(body_pin['path'])
    source=row['source'];source_path=Path(source['path']);stat=source_path.stat()
    if sha256_file(source_path)!=source['sha256'] or prior['source_identity']['sha256']!=source['sha256']:
        raise ValueError('retained_source_identity_changed')
    case_pin=identity(row['sim_case_path']);case=parse_case(read(case_pin['path']))
    config=_model({**case.model.to_dict(),'tp':case.runtime.parallel.tp,**prior.get('segmentation_options',{})})
    geo=row['replay_input_pins']['primary_geometry'];keys=('query_rows','tokens_per_sequence','sequences_per_replica')
    expected=[f for f in prior['forwards'] if all(f['geometry'][k]==geo[k]for k in keys)]
    groups,counts,buffer={},Counter(),[];cursor=0
    def close(window,rows):
        aligned,failure=_align(rows,config,cursor)
        if failure or any(aligned[k]!=window[k] for k in
                          ('start_ns','end_ns','head_start_ns','head_end_ns','query_rows','device_id')):
            raise ValueError('retained_body_endpoint_changed:'+window['forward_id'])
        layers=[s for s in aligned['stages'] if s['layer_id'] is not None]
        starts=[l['start_ns'] for l in layers];boundaries={}
        for layer in layers:
            local=[r for r in rows if layer['start_ns']<=r.event.start_ns<layer['evidence']['successor_boundary_start_ns']]
            anchor=next(r for r in local if _anchor(r,config))
            norm=next(i for i,r in enumerate(local) if r.event.start_ns>anchor.event.start_ns and _norm(r,config['hidden_size']))
            boundaries[layer['layer_id']]=(anchor.event.start_ns,local[_norm_start(local,norm,config['hidden_size'])].event.start_ns)
        ordinal=Counter()
        for r in rows:
            e=r.event
            if not window['start_ns']<=e.start_ns<window['end_ns'] or e.end_ns>window['end_ns']:
                continue
            if e.duration_ns<=0:continue
            layer=layers[bisect_right(starts,e.start_ns)-1];anchor,ffn=boundaries[layer['layer_id']]
            region='ffn' if e.start_ns>=ffn else 'before_attention' if e.start_ns<anchor else 'attention_anchor' if e.start_ns==anchor else 'after_attention'
            ordinal_key=(layer['layer_id'],region,e.op_type);ordinal[ordinal_key]+=1
            abi=native_tensor_contract(row_from_event(e))
            key=json.dumps([e.op_type,abi,layer['attention'],region,ordinal[ordinal_key]],sort_keys=True)
            group=groups.setdefault(key,{'native_operator_type':e.op_type,'native_abi':abi,
                'attention_kind':layer['attention'],'topology_region':region,
                'native_type_ordinal_in_region':ordinal[ordinal_key],
                'duration_ns_counter':Counter(),'layer_counts':Counter(),'forward_counts':Counter(),'examples':[]})
            group['duration_ns_counter'][e.duration_ns]+=1
            group['layer_counts'][layer['layer_id']]+=1;group['forward_counts'][window['forward_id']]+=1
            if len(group['examples'])<2:
                group['examples'].append({'locator':e.locator,'forward_id':window['forward_id'],
                    'layer_id':layer['layer_id'],'start_ns':e.start_ns,'end_ns':e.end_ns})
            counts['selected_positive_events']+=1
    previous=None
    for kernel in kernel_rows(source_path,rank_id='rank_0',rank_index=0,max_rows=5_000_000,timeout_s=180):
        e=kernel.event;counts['parsed_kernel_rows']+=1
        if previous is not None and e.start_ns<previous:raise ValueError('nonchronological_capture')
        previous=e.start_ns
        while cursor<len(expected) and e.start_ns>expected[cursor]['head_start_ns']:
            close(expected[cursor],buffer);buffer=[];cursor+=1
        if cursor==len(expected):break
        if expected[cursor]['start_ns']<=e.start_ns<=expected[cursor]['head_start_ns']:
            buffer.append(_Row(e,shapes(e.input_shapes),shapes(e.output_shapes)))
            if len(buffer)>100_000:raise MemoryError('retained_body_buffer_exceeded')
    if cursor<len(expected):close(expected[cursor],buffer);cursor+=1
    if cursor!=len(expected):raise ValueError('not_all_retained_windows_read')
    partitions=[];families={}
    for g in groups.values():
        hist=g['duration_ns_counter'];families.setdefault(g['native_operator_type'],Counter()).update(hist)
        partitions.append({**g,'duration_ns_counter':sorted(hist.items()),'layer_counts':dict(g['layer_counts']),
            'forward_counts':dict(g['forward_counts']),'observed_us':duration_stats(hist,1000)})
    if (source_path.stat().st_size,source_path.stat().st_mtime_ns)!=(stat.st_size,stat.st_mtime_ns):
        raise ValueError('capture_changed')
    if identity(case_pin['path'])!=case_pin or identity(body_pin['path'])!=body_pin:
        raise ValueError('retained_declaration_changed')
    rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if rss>512*1024**2:raise MemoryError('retained_native_exceeds_512MiB')
    output={'schema_version':'mindie-body-native-partitions/1','case_id':row['case_id'],
        'source_identity':source,'body_acceptance_identity':body_pin,'case_identity':case_pin,
        'extractor_identity':identity(__file__),'geometry':geo,'forward_count':len(expected),
        'retained_endpoints_exactly_equal':True,'native_event_count':counts['selected_positive_events'],
        'native_family_counts':{k:sum(v.values())for k,v in families.items()},
        'families':[{'native_operator_type':k,'duration_ns_counter':sorted(v.items()),'observed_us':duration_stats(v,1000)}for k,v in families.items()],
        'partitions':sorted(partitions,key=lambda g:-sum(ns*n for ns,n in g['duration_ns_counter'])),
        'execution':{**counts,'raw_targeted_scans':1,'source_hash_reads':1,
                     'elapsed_seconds':time.perf_counter()-started,'maximum_resident_set_size_bytes':rss},
        'scope':'Complete native ABI and elapsed histograms inside selected retained Body windows. Native tasks may overlap; sums are activity, not additive Body wall time.'}
    target=OUT/'glm78-native'/f"{row['case_id']}-native-partitions.json";write(target,output)
    print(json.dumps({'case_id':row['case_id'],'forward_count':len(expected),'partitions':len(partitions),
                      'events':output['native_event_count'],'execution':output['execution']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case-id',required=True);a=p.parse_args()
    manifest=read(ROOT/'acceptance-20261030-runtime40e4300e/decode-forward-glm-controller-cases.json')
    extract(next(r for r in manifest['cases']if r['case_id']==a.case_id))
