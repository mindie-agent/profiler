"""[Role] Independently audit body-operator identities, histograms and score counts.
[Invariants] Unscored references never enter passes; pooled quantiles use call counts.
[Timeouts & Locks] No subprocesses or locks; bounded saved reports, no raw scans.
[Side-Effect Policy] Writes only the requested independent review JSON.
"""
from pathlib import Path
from hashlib import sha256
from collections import Counter,defaultdict
import argparse,json,math
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--directory',type=Path,default=Path(__file__).parent/'acceptance-20261030-high-concurrency')
parser.add_argument('--skip-pooled',action='store_true',help='Audit operator families only; omit the separately versioned pooled-layer sidecar')
args=parser.parse_args();BASE=args.directory
def read(p):
 p=Path(p);assert p.stat().st_size<32*1024**2;return json.loads(p.read_text())
def digest(p):return sha256(Path(p).read_bytes()).hexdigest()
checks=0;failures=[]
def check(ok,label):
 global checks;checks+=1
 if not ok:failures.append(label)
def eq(a,b,label):check(a==b,label)
def near(a,b,label):check(math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-10),label)
def verify_identity(record,label):
 p=Path(record['path']);eq(digest(p),record['sha256'],label+':sha');eq(p.stat().st_size,record['size_bytes'],label+':size')
def quantiles(hist,scale):
 pairs=sorted((int(v),int(n)) for v,n in hist);n=sum(c for _,c in pairs)
 def at(position):
  seen=0
  for v,c in pairs:
   if seen+c>position:return v
   seen+=c
 return {'count':n,'mean':sum(v*c for v,c in pairs)/n/scale,'p50':(at((n-1)//2)+at(n//2))/2/scale,'p90':at(math.ceil(.9*n)-1)/scale,'min':pairs[0][0]/scale,'max':pairs[-1][0]/scale}
def verify_stats(actual,hist,scale,label):
 for k,v in quantiles(hist,scale).items():near(actual[k],v,label+':'+k)
report_path=BASE/'body-operator-family-scoreboard.json';report=read(report_path)
counts=Counter();accuracy=defaultdict(Counter);source_cases={};case_results=[]
for case in report['cases']:
 label=case['case_id'];families=case['families']
 for field in ('actual_identity','case_identity','mapping_identity','comparison_identity'):verify_identity(case[field],label+':'+field)
 actual=read(case['actual_identity']['path']);mapping=read(case['mapping_identity']['path']);comp=read(case['comparison_identity']['path'])
 verify_identity(actual['body_acceptance_identity'],label+':body_acceptance')
 retained=read(actual['body_acceptance_identity']['path'])
 attention_layers=Counter(row['samples'][0]['attention'] for row in retained['per_layer_ms'] if row.get('samples'))
 matching_forwards=[forward for forward in retained['forwards'] if all(forward['geometry'].get(key)==actual['geometry'].get(key) for key in ('query_rows','tokens_per_sequence','sequences_per_replica'))]
 eq(case['forward_count'],len(matching_forwards),label+':retained_complete_bodies_in_geometry')
 source_cases.setdefault(actual['case_id'],actual)
 other=source_cases[actual['case_id']]
 eq(actual['source_identity'],other['source_identity'],label+':same_source_two_arms')
 eq(actual['counts'],other['counts'],label+':same_measured_population_two_arms')
 eq(sum(f['observed_us']['count'] for f in families),actual['counts']['selected_body_events'],label+':all_body_event_denominator')
 cohort_rows=[r for w in comp['windows'] for r in w['cohorts']]
 eq(dict(Counter(r['status'] for r in cohort_rows)),case['comparison_status_counts'],label+':comparison_status_count')
 total_pass=0;scored=0
 for family in families:
  familylabel=label+':'+family['native_operator_type']+':'+family['declared_role']
  verify_stats(family['observed_us'],family['duration_ns_counter'],1000,familylabel)
  selected=[r for r in family['cohorts'] if r['status']=='compared'];n=sum(r['observed']['event_count'] for r in selected)
  eq(n,family['scored_event_count'],familylabel+':scored_count')
  eq(n+family['unscored_event_count'],family['observed_us']['count'],familylabel+':coverage')
  count_pass=0
  for row in family['cohorts']:
   score=row['status']=='compared'
   if score:
    measured=row['observed']['duration_ns']['mean']/1000;predicted=row['prediction']['per_call_ms']*1000
    passed=abs(predicted-measured)<=(15 if measured<=50 else measured*.15)
    eq(passed,row['accuracy_pass'],familylabel+':independent_tolerance')
    eq(row['accuracy_tier'],'absolute_15us' if measured<=50 else 'relative_15pct',familylabel+':threshold')
    count_pass+=passed;scored+=1
    tier=accuracy[row['accuracy_tier']];tier['compared']+=1;tier['passed']+=passed
   else:eq(row['accuracy_pass'],None,familylabel+':unscored_not_pass')
  eq(count_pass,family['passed_cohort_count'],familylabel+':family_pass_count');total_pass+=count_pass
  if n:
   predicted=sum(r['prediction']['per_call_ms']*1000*r['observed']['event_count'] for r in selected)/n
   observed=sum(r['observed']['complete_activity_sum_ns'] for r in selected)/n/1000
   near(family['predicted_us'],predicted,familylabel+':weighted_prediction')
   near(family['scored_observed_mean_us'],observed,familylabel+':weighted_observation')
   near(family['per_call_diff_us'],predicted-observed,familylabel+':signed_diff')
  if family['status']=='reference_only':eq(family['compared_cohort_count'],0,familylabel+':reference_excluded')
  references=family.get('conditional_source_role_references', [])
  if references:
   eq(sum(group['observed_us']['count'] for group in references),family['observed_us']['count'],familylabel+':source_reference_population')
   pooled_hist=Counter()
   for group in references:
    glabel=familylabel+':'+group['group_id']
    verify_stats(group['observed_us'],group['duration_ns_counter'],1000,glabel)
    histogram=Counter({int(value):int(n) for value,n in group['duration_ns_counter']});pooled_hist.update(histogram)
    activity=sum(value*n for value,n in histogram.items())
    eq(group['observed_activity_sum_ns'],activity,glabel+':source_reference_activity_ns')
    near(group['observed_activity_ms_per_forward'],activity/1e6/case['forward_count'],glabel+':source_reference_activity_per_forward')
    near(group['predicted_service_ms_per_forward'],group['predicted_reference_us']/1000*sum(histogram.values())/case['forward_count'],glabel+':source_reference_service_per_forward')
    near(group['per_call_reference_diff_us'],group['predicted_reference_us']-group['observed_us']['mean'],glabel+':source_reference_difference')
    eq(group['additional_budget_allowed'],False,glabel+':source_reference_no_extra_work')
    eq(group['occurrence_binding_implied'],False,glabel+':source_reference_not_host_binding')
    check('accuracy_pass' not in group,glabel+':source_reference_no_strict_accuracy')
    relation=group['source_correspondence']
    if relation['boundary_relation']=='capacity_vs_valid_rows_conditional':
     eq(relation['observed_valid_routed_rows'],None,glabel+':capacity_does_not_prove_routed_rows')
    if 'communication_bandwidth_calibration_allowed' in relation:
     eq(relation['communication_bandwidth_calibration_allowed'],False,glabel+':native_peer_wait_not_bandwidth')
   eq(pooled_hist,Counter({int(value):int(n) for value,n in family['duration_ns_counter']}),familylabel+':source_reference_exact_histogram_partition')
  if family['native_operator_type'].startswith('hcom_'):
   reference=family['conditional_program_reference']
   if reference['status']=='reference_only':eq(reference['communication_bandwidth_calibration_allowed'],False,familylabel+':no_peer_wait_bandwidth_fit')
   else:
    check(reference['reason'] in {'communication_program_not_homogeneous','native_collective_algorithm_not_declared'},familylabel+':heterogeneous_communication_not_averaged')
    eq(family.get('predicted_reference_us'),None,familylabel+':missing_uniform_reference_not_zero')
   if family['native_operator_type'].startswith('hcom_allReduce') and len(retained['per_layer_ms'])==64:
    eq(family['observed_us']['count'],64*case['forward_count'],familylabel+':once_per_layer_physical_communication')
  if family['native_operator_type'] in {'RecurrentGatedDeltaRule','CausalConv1d','fused_gdn_gating_kernel'}:
   expected_layers=attention_layers['gdn']+(attention_layers['kda'] if family['native_operator_type']=='CausalConv1d' else 0)
   eq(family['observed_us']['count'],expected_layers*case['forward_count'],familylabel+':declared_recurrent_layers')
  if family['native_operator_type']=='FusedInferAttentionScore':eq(family['observed_us']['count'],(attention_layers['gqa']+attention_layers['mla'])*case['forward_count'],familylabel+':declared_attention_layers')
 eq(sum(actual['counts'].values()),sum(row['closed_segment_event_count'] for row in matching_forwards),label+':complete_segment_selection_partition')
 check(0<=actual['counts']['duplicate_communication_summary_events']<=sum(row['observed_us']['count'] for row in families if row['native_operator_type'].startswith('hcom_')),label+':duplicate_summaries_bounded_by_retained_real_hcom_calls')
 eq(total_pass,case['passed_cohorts'],label+':case_pass_count')
 counts.update(case['comparison_status_counts']);case_results.append({'case_id':label,'passed':total_pass,'compared':scored})
pooled={'cases':[]} if args.skip_pooled else read(BASE/'steady-layer-pooled.json')
for case in pooled['cases']:
 verify_identity(case['extraction_identity'],case['case_id']+':pooled_source')
 actual=read(case['extraction_identity']['path']);prior=read(actual['body_acceptance_identity']['path'])
 prior_layers={row['layer_id']:row['stats'] for row in prior['per_layer_ms']}
 for group in case['groups']:
  label=case['case_id']+':pooled:'+str(group['attention_kind'])
  verify_stats(group['stats'],group['duration_ns_counter'],1e6,label)
  eq(group['stats']['count'],len(group['layer_ids'])*case['forward_count'],label+':population')
  eq(len(group['layer_ids']),63 if group['attention_kind'] is None else 47 if group['attention_kind']=='gdn' else 16,label+':layer_count')
  check(0 not in group['layer_ids'],label+':exclude_layer0')
  layers=[prior_layers[layer_id] for layer_id in group['layer_ids']]
  count=sum(layer['count'] for layer in layers)
  eq(group['stats']['count'],count,label+':prior_extraction_count')
  near(group['stats']['mean'],sum(layer['mean']*layer['count'] for layer in layers)/count,label+':prior_extraction_weighted_mean')
  near(group['stats']['min'],min(layer['min'] for layer in layers),label+':prior_extraction_min')
  near(group['stats']['max'],max(layer['max'] for layer in layers),label+':prior_extraction_max')
result={'schema_version':'mindie-body-operator-independent-review/1','status':'passed' if not failures else 'failed',
 'checks':checks,'failures':failures,'scoreboard_sha256':digest(report_path),'steady_layer_pooled_sha256':None if args.skip_pooled else digest(BASE/'steady-layer-pooled.json'),
 'source_count':len(source_cases),'forward_count':sum(a['forward_count'] for a in source_cases.values()),
 'comparison_status_counts':dict(counts),'accuracy_by_tier':dict(accuracy),'cases':case_results,
 'method':'independent stdlib histogram/count/identity arithmetic; no profiler or Sim import',
 'raw_capture_reads':0,'prediction_executions':0,'script_sha256':digest(__file__)}
(BASE/'body-operator-family-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='cases'},indent=2));raise SystemExit(bool(failures))
