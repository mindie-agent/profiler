"""[Role] Inspect retained communication/trace/DB availability beside the 66 captures.
[Invariants] File presence differs from usable task linkage. The one proven Kimi
  archive is streamed; Python parent IDs are never promoted to NPU task IDs.
[Timeouts & Locks] Metadata walks and one <=120 s / 1M-event trace stream.
[Side-Effect Policy] Local reads and compact evidence only; no extraction,
  remote fetch, device workload, prediction, or Body mutation.
"""
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import argparse
import csv
import gzip
import io
import json
import re
import resource
import sys
import tarfile
import time

ARCHIVE=Path('/Volumes/data/mindie-sim-data/a5/2026-10-23/kimi-k3-longctx/k3lc-os1.tgz')
MEMBER='raw/prof-export/op_summary_20261023053244.csv'


def identity(path):
    value=sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):value.update(block)
    return {'path':str(path.resolve()),'size_bytes':path.stat().st_size,'sha256':value.hexdigest()}


def capture_root(path):
    parts=path.parts
    if 'mindie-sim-data' in parts:
        offset=parts.index('mindie-sim-data')+2
        return Path(*parts[:offset+2 if re.fullmatch(r'\d{4}-\d{2}-\d{2}',parts[offset]) else offset+1])
    if path.name=='mindie-body-profiling-kimi-op-summary.csv':return ARCHIVE.parent
    return path.parent


def scan_root(root):
    files=[];directory_tags=[]
    for p in root.rglob('*'):
        rel=str(p.relative_to(root));name=p.name.lower()
        if p.is_dir():
            if name=='framework' or name.startswith('prof_'):directory_tags.append(rel)
            continue
        categories=[]
        if name.endswith(('.db','.sqlite','.sqlite3')):categories.append('database')
        if 'trace' in name and name.endswith(('.json','.json.gz','.csv')):
            categories.append('step_trace_export' if 'step_trace' in name else 'timeline_trace')
        if any(x in name for x in ('communication','hccl','task_time','task_trace')):categories.append('communication_or_task_export')
        if name.endswith(('.tgz','.tar','.tar.gz','.zip','.tar.zst')):categories.append('archive_unexpanded')
        if any(x=='FRAMEWORK' or x.startswith('PROF_') for x in p.relative_to(root).parts):categories.append('framework_or_raw_profiler')
        if categories:
            files.append({'path':str(p),'relative_path':rel,'size_bytes':p.stat().st_size,'categories':categories})
        if len(files)>10000:raise ValueError('metadata_inventory_exceeds_10000_relevant_files')
    return {'root':str(root),'files':files,'framework_or_prof_directories':directory_tags,
        'scope':'recursive filesystem metadata only; no large trace or database whole-read'}


def kimi_trace(source_sha):
    started=time.perf_counter();deadline=started+120;pin=identity(ARCHIVE)
    members=[];exports={};trace=None;verified=None
    with tarfile.open(ARCHIVE,'r|gz') as archive:
        for member in archive:
            if not member.isfile():continue
            if len(members)>10000:raise ValueError('archive_member_budget')
            members.append({'name':member.name,'size_bytes':member.size})
            if member.name==MEMBER:
                value=sha256();stream=archive.extractfile(member)
                for chunk in iter(lambda:stream.read(1024**2),b''):value.update(chunk)
                verified={'member':member.name,'sha256':value.hexdigest(),'size_bytes':member.size}
                if verified['sha256']!=source_sha:raise ValueError('retained_csv_archive_member_sha_differs')
            elif 'communication_statistic' in member.name or member.name.endswith('step_trace_20261023053209.json'):
                if member.size>256*1024:raise ValueError('bounded_communication_export_too_large')
                text=archive.extractfile(member).read().decode()
                exports[member.name]={'size_bytes':member.size,'sha256':sha256(text.encode()).hexdigest(),
                    'rows':list(csv.DictReader(io.StringIO(text))) if member.name.endswith('.csv') else json.loads(text)}
            elif member.name.endswith('.pt.trace.json.gz'):
                import ijson
                categories=Counter();names=defaultdict(list);arg_keys=defaultdict(Counter)
                matching=Counter();examples=[];phases=Counter();n=0;ts_min=None;ts_max=None
                with gzip.GzipFile(fileobj=archive.extractfile(member)) as stream:
                    for event in ijson.items(stream,'traceEvents.item'):
                        n+=1
                        if n>1_000_000 or n%2048==0 and time.perf_counter()>deadline:raise TimeoutError('bounded_trace_inventory_budget')
                        category=str(event.get('cat'));ph=str(event.get('ph'));key=category+'|'+ph
                        categories[key]+=1;phases[ph]+=1;arg_keys[key].update(event.get('args',{}).keys())
                        name=str(event.get('name'))
                        if len(names[key])<3:names[key].append(name)
                        normalized=name.lower().replace('_','')
                        if any(x in normalized for x in ('hcom','hccl','allreduce','allgather','reducescatter','alltoall')):
                            matching[name]+=1
                            if len(examples)<8:examples.append({'trace_event_index':n-1,'event':event})
                        ts=event.get('ts')
                        if ts is not None:
                            ts_min=ts if ts_min is None else min(ts_min,ts)
                            ts_max=ts if ts_max is None else max(ts_max,ts)
                trace={'member':member.name,'compressed_member_size_bytes':member.size,'event_count':n,
                    'category_phase_counts':dict(categories),'phase_counts':dict(phases),
                    'arg_key_counts':{k:dict(v) for k,v in arg_keys.items()},'sample_names':dict(names),
                    'communication_name_counts':dict(matching),'communication_examples':examples,
                    'timestamp_min_us':str(ts_min),'timestamp_max_us':str(ts_max),
                    'device_task_connection_fields_present':False,'flow_events_present':any(ph in phases for ph in ('s','t','f')),
                    'association_result':'Python stack scopes only; no exported NPU task/stream/correlation or flow relation for linking HCOM CSV occurrences.',
                    'clock_domain_alignment_to_csv_proven':False}
    if verified is None or trace is None:raise ValueError('known_kimi_archive_evidence_missing')
    return {'archive_identity':pin,'retained_csv_member_identity':verified,'archive_members':members,
        'bounded_exports':exports,'trace_inventory':trace,'elapsed_seconds':time.perf_counter()-started,
        'large_members_written_to_disk':False,'raw_csv_parse_count':0,
        'prior_read_only_trace_probes':{'passes':2,'events_per_pass':425826,
            'purpose':['Initial named-HCOM lookup','Category/field availability check before retained expanded evidence']}}


def main(inputs,output):
    source=json.loads(inputs.read_text());roots={};rows=[]
    for case in source['cases']:
        root=capture_root(Path(case['source']['path']));rootkey=str(root)
        if rootkey not in roots:roots[rootkey]=scan_root(root)
        inventory=roots[rootkey];counts=Counter(tag for f in inventory['files'] for tag in f['categories'])
        rows.append({'case_id':case['case_id'],'source_identity':case['source'],'root':rootkey,
            'artifact_category_counts':dict(counts),
            'direct_timeline_trace_or_db_present':bool(counts['timeline_trace'] or counts['database']),
            'step_trace_export_present':bool(counts['step_trace_export']),
            'archive_members_examined':case['case_id']=='a5_kimi_k3_p32768_c1',
            'retained_rank_kernel_file_count':len(list(root.glob('ranks/*/kernel_details.csv*'))),
            'rank_file_count_includes_primary_tp0_when_present':True,
            'actual_task_relationship_status':'not_established_from_CSV; inspect listed trace/database/archive contents before concluding absence'})
    kimi=next(c for c in source['cases'] if c['case_id']=='a5_kimi_k3_p32768_c1')
    prior=json.loads(output.read_text()) if output.exists() else None
    expansion=prior.get('bounded_same_capture_expansion') if prior else None
    reuse=bool(expansion and expansion['archive_identity']==identity(ARCHIVE))
    result={'schema_version':'mindie-hccl-associated-artifacts/1','input_identity':identity(inputs),
        'source_count':len(rows),'unique_capture_roots':len(roots),'sources':rows,'root_inventories':list(roots.values()),
        'bounded_same_capture_expansion':expansion if reuse else kimi_trace(kimi['source']['sha256']),
        'unchanged_archive_expansion_reused':reuse,
        'raw_capture_csv_scans':0,'remote_fetches':0,'cost_predictions':0,
        'maximum_resident_set_size_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)}
    output.write_text(json.dumps(result,separators=(',',':'),default=str)+'\n')
    print({'sources':len(rows),'roots':len(roots),'timeline_trace_or_db_sources':sum(r['direct_timeline_trace_or_db_present'] for r in rows),
        'archive_trace_events':result['bounded_same_capture_expansion']['trace_inventory']['event_count'],
        'rss_mib':result['maximum_resident_set_size_bytes']/1024**2})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--inputs',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();main(args.inputs,args.output)
