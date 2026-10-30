"""Independently check retained grouped populations and source-count join.

[Role] Verify integer/decimal populations and provenance without raw or costs.
[Invariants] Partial PMU means never impersonate complete native populations.
[Timeouts & Locks] One source JSON at a time; no subprocesses or locks.
[Side-Effect Policy] Writes only the grouped evidence review receipt.
"""
from collections import Counter
from decimal import Decimal
from math import ceil, isclose
from pathlib import Path
import json
import resource
import sys

from collect_scalar_dma_pmu import identity, read

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/observations/sources'


def summarize(counter):
    pairs=sorted((Decimal(value),count) for value,count in counter)
    n=sum(count for _,count in pairs)
    if not n:return None
    def rank(index):
        seen=0
        for value,count in pairs:
            seen+=count
            if seen>index:return value
        raise AssertionError('rank outside real population')
    return {'count':n,'mean':float(sum(v*c for v,c in pairs)/n),
            'p50':float((rank((n-1)//2)+rank(n//2))/2),
            'p90':float(rank(ceil(n*.9)-1)),'min':float(pairs[0][0]),'max':float(pairs[-1][0])}


def main():
    receipt_path=DATA/'arch3510-physical-services/grouped-extraction-receipt.json'
    receipt=read(receipt_path); checks=0; failures=[]; sources=[]
    summaries={arch:read(DATA/f'{arch}-physical-services/grouped-source-constraints.json') for arch in ('arch22','arch3510')}
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    for source in receipt['cases']:
        pin=source['output_identity']; check(identity(pin['path'])==pin,source['case_id']+'/artifact')
        raw=read(pin['path']); prior=read(raw['prior_identity']['path']); totals={}
        joined=[r for r in summaries[raw['architecture']]['records'] if r['case_id']==raw['case_id']]
        check(len(joined)==len(raw['partitions']),raw['case_id']+'/all partitions joined')
        for index,g in enumerate(raw['partitions']):
            label=raw['case_id']+'/'+str(index); count=sum(n for _,n in g['duration_ns_counter'])
            check(all(isinstance(ns,int) and isinstance(n,int) and n>0 for ns,n in g['duration_ns_counter']),label+'/integer ns')
            check(sum(g['layer_counts'].values())==sum(g['forward_counts'].values())==count,label+'/layer forward conservation')
            check(len(g['forward_counts'])==raw['forward_count'],label+'/complete bodies')
            check(count==g['raw_pmu']['event_count'],label+'/PMU population')
            totals.setdefault(g['native_operator_type'],Counter()).update(dict(g['duration_ns_counter']))
            for name,f in g['raw_pmu']['fields'].items():
                fl=label+'/'+name; counts=f['numeric_value_counter']; stats=summarize(counts)
                check(sum(n for _,n in counts)==f['numeric_count'],fl+'/numeric denominator')
                check(f['numeric_count']+f['invalid_numeric_count']+f['missing_or_na_count']==count,fl+'/missing denominator')
                check(sum(n for value,n in counts if Decimal(value)==0)==f['zero_count'],fl+'/measured zero')
                check(stats==f['statistics'],fl+'/exact Decimal statistics')
            row=next(r for r in joined if r['partition_index']==index)
            for field in ('native_abi','native_operator_type','role','attention_kind','layer_counts','block_num','mix_block_num'):
                check(row[field]==g[field],label+'/joined '+field)
            check(row['partition_identity']==pin,label+'/partition provenance')
            check(row['source_identity']==raw['source_identity'] and row['body_identity']==raw['body_identity'],label+'/source body provenance')
            duration=summarize(g['duration_ns_counter'])
            check(row['observed']['count']==count,label+'/call count')
            for field in ('mean','p50','p90','min','max'):
                check(isclose(row['observed'][field+'_us'],duration[field]/1000,abs_tol=1e-10),label+'/native '+field)
            check(row['calls_per_forward']==count/raw['forward_count'],label+'/calls per forward')
            check(row['native_coordinates']['observed_valid_rows'] is None,label+'/no capacity-as-valid')
            for name,f in row['pmu']['fields'].items():
                check(f=={k:v for k,v in g['raw_pmu']['fields'][name].items() if k!='numeric_value_counter'},label+'/PMU projection '+name)
                expected=f['statistics']['mean'] if f['numeric_count']==count else None
                check(row['pmu']['complete_numeric_mean_us'][name]==expected,label+'/complete PMU '+name)
            c=row.get('conditional_source_counts')
            if c:
                rows=c['declared_expert_rows']; check(sum(rows)==c['declared_valid_rows'],label+'/declared route conservation')
                check(c['declared_valid_rows']==c['query_rows']*c['top_k']//c['ep'],label+'/declaration geometry')
                expected=sum(ceil(2*m/c['base_m'])*ceil(row['native_coordinates']['matrix_n']/c['base_n']) for m in rows if m)
                check(c['matrix_output_tile_count']==expected==sum(c['matrix_tiles_per_aic_owner'].values()),label+'/source tile arithmetic')
                check(c['compiled_dma_descriptor_count'] is None and c['not_an_observed_route_or_dispatch'],label+'/count boundary')
        for native,hist in totals.items():
            old=Counter()
            for family in prior['families']:
                if family['native_operator_type']==native:old.update(dict(family['duration_ns_counter']))
            check(hist==old,raw['case_id']+'/'+native+'/full retained histogram')
        check(raw['complete_native_histograms_match_prior'],raw['case_id']+'/collection validation')
        sources.append({'case_id':raw['case_id'],'forwards':raw['forward_count'],'partitions':len(raw['partitions']),
                        'calls':sum(sum(v.values()) for v in totals.values()),'identity':pin})
    out={'schema_version':'mindie-grouped-micro-independent-review/1','status':'failed' if failures else 'passed',
         'checks':checks,'failures':failures,'sources':sources,'primary_forwards':sum(r['forwards'] for r in sources),
         'summary_identities':{arch:identity(DATA/f'{arch}-physical-services/grouped-source-constraints.json') for arch in summaries},
         'extraction_receipt_identity':identity(receipt_path),'reviewer_identity':identity(__file__),
         'raw_scans':0,'new_costs':0,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
         'scope':'Saved full native integer/Decimal histograms and PMU denominators; declared source arithmetic, not proof of captured tile dispatch.'}
    (DATA/'arch3510-physical-services/grouped-source-independent-review.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','checks','failures','primary_forwards','peak_rss_bytes')}))
    return bool(failures)


if __name__=='__main__':raise SystemExit(main())
