"""Independently verify retained V4.1 native populations without raw rereads.

[Role] Audit complete histogram conservation, source pins and topology coverage.
[Invariants] Seven rank0 sources remain seven captures; all native counts include
  unreferenced work. Actual valid cache slots cannot be inferred from allocation.
[Timeouts & Locks] Bounded JSON metadata (<32 MiB each); no workers or locks.
[Side-Effect Policy] Read retained evidence and write one compact review.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import ceil, isclose
from pathlib import Path
import resource
import sys


def read(path):
    path=Path(path)
    if path.stat().st_size>32*1024**2:raise ValueError('bounded_metadata_required')
    return json.loads(path.read_text())


def pin(path):
    path=Path(path);return {'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest(),'size_bytes':path.stat().st_size}


def statistics(hist):
    count=sum(hist.values());positions=((count-1)//2,count//2,ceil(count*.9)-1)
    values={};current=0
    for duration,n in sorted(hist.items()):
        for position in positions:
            if current<=position<current+n:values[position]=duration
        current+=n
    return {'count':count,'mean':sum(k*v for k,v in hist.items())/count/1000,
            'p50':(values[positions[0]]+values[positions[1]])/2000,
            'p90':values[positions[2]]/1000,'min':min(hist)/1000,'max':max(hist)/1000}


def review(directory):
    checks=0;failures=[];cases=[];global_counts=Counter()
    def check(condition,reason):
        nonlocal checks
        checks+=1
        if not condition:failures.append(reason)
    for path in sorted(directory.glob('*-native-partitions.json')):
        data=read(path);actual_pin=data['actual_identity'];body_pin=data['body_acceptance_identity']
        check(pin(actual_pin['path'])==actual_pin,str(path)+':actual_identity')
        check(pin(body_pin['path'])==body_pin,str(path)+':body_identity')
        actual=read(actual_pin['path']);body=read(body_pin['path'])
        check(data['source_identity']==actual['source_identity'],str(path)+':source_identity')
        check(data['geometry']==actual['geometry'],str(path)+':geometry')
        geo=data['geometry'];fields=('tokens_per_sequence','sequences_per_replica','query_rows')
        selected={f['forward_id']:f for f in body['forwards'] if all(f['geometry'][k]==geo[k] for k in fields)}
        check(len(selected)==data['forward_count']==actual['forward_count'],str(path)+':forwards')
        check(data['all_body_endpoints_exactly_equal'] is True,str(path)+':endpoint_validation')
        histograms=defaultdict(Counter);layers=defaultdict(Counter)
        for index,group in enumerate(data['partitions']):
            hist=Counter(dict(group['duration_ns_counter']));count=sum(hist.values())
            prefix=f'{path.name}:{index}'
            check(all(isinstance(ns,int) and ns>0 and isinstance(n,int) and n>0 for ns,n in hist.items()),prefix+':integer_ns')
            computed=statistics(hist)
            for field,value in computed.items():check(isclose(value,group['observed_us'][field],rel_tol=1e-12,abs_tol=1e-12),prefix+':'+field)
            check(sum(group['layer_counts'].values())==sum(group['forward_counts'].values())==count,prefix+':membership')
            check(set(group['forward_counts'])==set(selected),prefix+':complete_selected_population')
            check(all(0<=int(layer)<40 for layer in group['layer_counts']),prefix+':declared_layer_membership')
            native=group['native_abi']
            check(native[:2]==['native_tensor_abi',group['native_operator_type']],prefix+':full_abi')
            check(len(native)==4 and all(len(slot)==3 for side in native[2:] for slot in side),prefix+':complete_slots')
            histograms[group['native_operator_type']].update(hist);layers[group['native_operator_type']].update(group['layer_counts'])
        family_rows=[]
        for kind,hist in histograms.items():
            old=Counter()
            for family in actual['families']:
                if family['native_operator_type']==kind:old.update(dict(family['duration_ns_counter']))
            check(hist==old,str(path)+':'+kind+':full_saved_histogram')
            count=sum(hist.values());global_counts[kind]+=count
            check(count==data['native_family_counts'][kind],str(path)+':'+kind+':reported_count')
            family_rows.append({'native_operator_type':kind,'observed_us':statistics(hist),
                'calls_per_forward':count/data['forward_count'],
                'observed_activity_ms_per_forward':sum(ns*n for ns,n in hist.items())/1e6/data['forward_count'],
                'layer_ids':sorted(map(int,layers[kind]))})
        check(sum(sum(h.values()) for h in histograms.values())==data['native_event_count'],str(path)+':all_counts')
        cases.append({'case_id':data['source_case_id'],'partition_identity':pin(path),
            'source_identity':data['source_identity'],'geometry':geo,'forward_count':data['forward_count'],
            'families':family_rows,'scan_execution':data['execution']})
    check(len(cases)==len({c['source_identity']['sha256'] for c in cases})==7,'seven_unique_sources')
    check(sum(c['forward_count'] for c in cases)==830,'830_existing_bodies')
    result={'schema_version':'mindie-v41-native-partition-review/1','status':'passed' if not failures else 'failed',
        'checks':checks,'failures':failures,'cases':cases,'source_count':len(cases),
        'forward_count':sum(c['forward_count'] for c in cases),'native_event_counts':dict(global_counts),
        'raw_capture_reads':0,'prediction_executions':0,'reviewer_identity':pin(Path(__file__).resolve()),
        'maximum_resident_set_size_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)}
    dest=directory/'native-partition-independent-review.json';dest.write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:result[k] for k in ('status','checks','source_count','forward_count','native_event_counts','maximum_resident_set_size_bytes')}))
    if failures:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);review(parser.parse_args().directory)
