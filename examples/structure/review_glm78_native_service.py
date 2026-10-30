"""Reconcile GLM78 observable responses with complete retained native histograms.

[Role] Independently check same-source parameters, multiplicity and population.
[Invariants] No Body error is used to construct or validate a fitted parameter.
[Timeouts & Locks] Small saved JSON only; no raw reads, cost calls or locks.
[Side-Effect Policy] Write an audit receipt; leave model and report unchanged.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource

OUT=Path(__file__).resolve().parent/'acceptance-20261030-service-qwen-a3'
def read(path):return json.loads(Path(path).read_text())
def main(caller_complete=False):
    stem="glm78-caller-complete-service" if caller_complete else "glm78-native-service"
    checks=0;failures=[]
    def check(value,label):
        nonlocal checks
        checks+=1
        if not value:failures.append(label)
    manifest=read(OUT/f'decode-forward-{stem}-cases.json')
    evidence={c['case_id']:c for c in read(OUT/f'{stem}-populations.json')['cases']}
    report_path=OUT/f'decode-forward-{stem}-replay.json';report=read(report_path)
    rows={r['source_case_id']:r for r in report['cases'] if r['comparison']['status']=='compared'}
    for declaration in manifest['cases']:
        cid=declaration['case_id'];row=rows[cid];ev=evidence[cid]
        native_path=Path(ev['native_identity']['path']);native=read(native_path)
        check(sha256(native_path.read_bytes()).hexdigest()==ev['native_identity']['sha256'],cid+':native_pin')
        check(native['source_identity']['sha256']==row['source_identity']['sha256']==declaration['source']['sha256'],cid+':source')
        check(native['forward_count']==row['comparison']['observed_ms']['count'],cid+':population')
        raw=read(declaration['sim_case_path']);rules=raw['runtime']['kernels']['service_regimes'];rule_map={r['id']:r for r in rules}
        old=read(declaration['baseline_service_case_identity']['path'])
        model=dict(raw['model'])
        if caller_complete:
            overrides=model.pop('layer_overrides')
            check(set(overrides)=={str(i) for i in range(3,78)},cid+':router_layer_population')
            check(all(v=={'router_dtype':'bf16','router_output_dtype':'fp32'}for v in overrides.values()),cid+':observed_router_precision')
            check(raw['runtime']['kernels']['fusion_domains']=={'norm_quant':{'consumers':[{'recipe':'dense_gate_up'}]}},cid+':dense_only_norm_quant')
            source=raw['runtime']['metadata']['caller_source_case_identity']
            check(sha256(Path(source['path']).read_bytes()).hexdigest()==source['sha256'],cid+':parent_source_case_pin')
            check(raw['runtime']['kernels']['moe_token_partition']==read(source['path'])['runtime']['kernels']['moe_token_partition'],cid+':parent_caller_choice')
        check(model==old['model'] and raw['machine']==old['machine'],cid+':same_other_model_hardware')
        check(raw['runtime']['graph_capture_keys']==[native['geometry']['query_rows']],cid+':correct_captured_grid')
        check(raw['runtime']['kernels']['lowerings']['shared_expert']=='ascend_shared_gate_up_int32',cid+':source_INT32_chain')
        hits={r['id']:r['queries']['observable_response'] for r in row['prediction']['parameters']['service_regimes']}
        check(set(hits)==set(rule_map),cid+':all_rules_hit')
        old_rules={r['id']:r for r in old['runtime']['kernels']['service_regimes']}
        for group in ev['rebound_prior_rules']:
            rid=group['id'];r=rule_map[rid]
            check(r['response']==old_rules[rid]['response'],cid+':unchanged_prior_response:'+rid)
            check(r['provenance']['previous_physical_match']==old_rules[rid]['match'],cid+':retained_old_axis:'+rid)
            check(hits[rid]==group['expected_hits'],cid+':prior_hits:'+rid)
        assigned=set()
        for group in [*ev['complete_contract_rules'],*ev.get('caller_rules',[])]:
            rid=group['rule_id'];r=rule_map[rid];counter=Counter()
            for index in group['partition_indices']:
                check(index not in assigned,cid+':disjoint_native_partition:'+str(index));assigned.add(index)
                p=native['partitions'][index]
                check(p['native_operator_type']==group['native_operator_type'],cid+':native_kind')
                counter.update(dict(p['duration_ns_counter']))
            n=sum(counter.values());mean=sum(ns*c for ns,c in counter.items())/n/1000
            check(n==group['observed_us']['count'],cid+':complete_count:'+rid)
            check(abs(mean-r['response']['fixed_us'])<1e-12,cid+':mean_not_body_fit:'+rid)
            check(n==group['expected_rule_hits']*native['forward_count'],cid+':multiplicity:'+rid)
            check(hits[rid]==group['expected_rule_hits'],cid+':physical_hits:'+rid)
            if 'target_ids'in group:check(len(group['target_ids'])==group['expected_rule_hits'],cid+':target_multiplicity:'+rid)
            check(group['body_residual_used'] is False,cid+':no_residual:'+rid)
            check(not any(k in ('op_id','model','layer','name') for k in r['match']),cid+':physical_axes:'+rid)
        check(not row['prediction_execution']['reused_prediction'],cid+':new_execution')
        check(row['prediction_execution']['execution']['peak_rss_bytes']<=512*1024**2,cid+':bounded_worker')
    result={'status':'passed' if not failures else 'failed','checks':checks,'failures':failures,
        'report_identity':{'path':str(report_path),'sha256':sha256(report_path.read_bytes()).hexdigest()},
        'raw_reads':0,'cost_predictions':0,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'scope':'Saved complete native histograms, exact rule provenance/hits and unchanged prior means. Body arithmetic is separately reviewed; no fresh cost.'}
    (OUT/f'{stem}-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result));return bool(failures)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caller-complete',action='store_true')
    raise SystemExit(main(parser.parse_args().caller_complete))
