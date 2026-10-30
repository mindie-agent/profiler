"""Independently compare physical-service exports with retained source ledgers.

[Role] Audit PMU availability and conditional-network populations without cost.
[Invariants] Recorded zero differs from missing; source-only payload/template
  assumptions never become measured facts or separately identified wait prices.
[Timeouts & Locks] Bounded JSON receipts; no raw event scan or locks.
[Side-Effect Policy] Write one local review JSON.
"""
import json,hashlib,math,resource
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/observations/sources/arch3510-physical-services'
def rd(p):return json.loads(Path(p).read_text())
def pin(p):
 p=Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
check=0;fail=[]
def ck(ok,label):
 global check;check+=1
 if not ok:fail.append(label)
b=rd(D/'mc2-observable-pmu-baseline.json');by_source={}
for r in b['groups']:by_source.setdefault(r['retained_ledger_identity']['path'],[]).append(r)
counts=Counter()
for p,rows in by_source.items():
 path=Path(p);path=path if path.is_absolute() else ROOT/path;a=rd(path);ck(pin(path)['sha256']==rows[0]['retained_ledger_identity']['sha256'],p+':pin')
 for r in rows:
  _,gi,_,pi=r['retained_group_path'].split('/');geo=a['body_geometry_groups'][int(gi)];g=geo['groups'][int(pi)]
  ck(a['source_identity']==r['source_identity'],p+':source');ck(a['body_acceptance_identity']==r['body_acceptance_identity'],p+':bodypin');ck(r['geometry']==geo['geometry'] and r['forward_count']==geo['forward_count'],p+':geo');ck(r['native_operator_type']==g['native_operator_type'],p+':native');ck(r['observed_us']==g['observed_us'],p+':stats');ck(r['launch_dimensions']==g['raw_pmu']['dimensions'],p+':owners');ck(r['identifiability']['syncall_latency'] is None and r['identifiability']['scalar_spin_wait_time'] is None,p+':unknowncomponents')
  for k,met in r['pmu'].items():
   if k not in g['raw_pmu']['fields']:ck(met['availability']=='column_not_exported' and met['statistics'] is None,p+':absent:'+k)
   else:
    x=g['raw_pmu']['fields'][k]
    for field in ('column_present','numeric_count','missing_or_na_count','zero_count','statistics'):ck(met[field]==x[field],p+':field:'+k+field)
    ck(met['numeric_count']+met['missing_or_na_count']+met['invalid_numeric_count']==r['event_count'],p+':denom:'+k)
  counts[a['hardware_sku']+'|'+g['native_operator_type']]+=r['event_count']
 del a
ck(dict(counts)==b['summary']['native_event_counts'],'mc2-native-denominator')
n=rd(D/'network-observable-service-baseline.json');cache={};seen=set()
for r in n['points']:
 p=r['retained_receipt_identity']['path']
 if p not in cache:ck(pin(p)['sha256']==r['retained_receipt_identity']['sha256'],p+':pin');cache[p]=rd(p)
 case=next(c for c in cache[p]['cases'] if c['case_id']==r['case_id']);g=next(g for g in case['groups'] if g['retained_group_id']==r['retained_group_id']);ck(r['source_identity']==case['source_identity'] and r['body_acceptance_identity']==case['body_acceptance_identity'],p+':chain');ck(r['observed_service_us']==g['observed_us'],p+':realstats');ck(r['declared_collective_program']==g['source_correspondence']['selection'],p+':program');ck(r['measured_payload_bytes'] is None and r['measured_algorithm'] is None and not r['template_selection_confirmed'],p+':conditional');payload=r['declared_collective_program']['payload_bytes'];ck(math.isclose(r['declared_payload_bytes_per_observed_us'],payload/g['observed_us']['mean'],rel_tol=1e-12),p+':effective');ck(r['independent_control_rtt_us'] is None and r['independent_switch_hop_latency_us'] is None and not r['effective_service_ratio_is_pure_link_bandwidth'],p+':nocausalrate');key=(r['source_identity']['sha256'],r['retained_group_id']);ck(key not in seen,p+':dedup');seen.add(key)
ck(sum(r['event_count'] for r in n['points'])==n['coverage']['observed_collective_calls'],'network-denom')
output={'schema_version':'mindie-physical-service-export-review/1','status':'passed' if not fail else 'failed','checks':check,'failures':fail,'mc2_identity':pin(D/'mc2-observable-pmu-baseline.json'),'network_identity':pin(D/'network-observable-service-baseline.json'),'raw_reads':0,'new_predictions':0,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(D/'mc2-network-export-review.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:output[k] for k in ('status','checks','failures','peak_rss_bytes')}))
