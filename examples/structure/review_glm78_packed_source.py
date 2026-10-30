"""Review preserved GLM78 service rules and the explicitly changed D656 boundary.

[Role] Reconcile new source declarations with prior cases and retained native populations.
[Invariants] No cost/raw reads; M12/M16 remains a contract discrepancy, not an exact match.
[Timeouts & Locks] Bounded saved JSON only; no subprocess or locks.
[Side-Effect Policy] Write an input/provenance review without changing predictions.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent/'acceptance-20261030-service-qwen-a3'
def read(p): return json.loads(Path(p).read_text())
def main(captured_grid=False):
    stem="glm78-captured-grid" if captured_grid else "glm78-packed-source"
    checks,failures=0,[]
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    old={r['case_id']:r for r in read(ROOT/'decode-forward-glm78-grouped-service-cases.json')['cases']}
    cases={r['case_id']:r for r in read(ROOT/f'decode-forward-{stem}-cases.json')['cases']}
    pre={r['case_id']:r for r in read(ROOT/f'{stem}-preflight.json')['cases']}
    path=ROOT/f'decode-forward-{stem}-replay.json';report=read(path)
    for row in report['cases']:
        if row['comparison']['status']!='compared':continue
        cid=row['source_case_id'];decl=cases[cid];before=read(old[cid]['sim_case_path']);after=read(decl['sim_case_path'])
        native=read(ROOT/'glm78-native'/f'{cid}-native-partitions.json')
        check(sha256(Path(decl['sim_case_path']).read_bytes()).hexdigest()==decl['model_declaration']['sha256'],cid+':case_sha')
        for field in ('model','machine','workload'):check(before[field]==after[field],cid+':preserved_'+field)
        for field in ('tp','dp','ep','pp','graph_mode','routing'):
            check(before['runtime'].get(field)==after['runtime'].get(field),cid+':preserved_'+field)
        rules=after['runtime']['kernels']['service_regimes']
        check(rules==before['runtime']['kernels']['service_regimes'],cid+':same_observed_responses')
        selected={r['id']:r['queries'] for r in row['prediction']['parameters'].get('service_regimes', [])}
        expected_rules=set() if captured_grid and native['geometry']['query_rows']==12 else {r['id'] for r in rules}
        check(set(selected)==expected_rules,cid+':actual_rule_hit_population')
        for rid,q in selected.items():check(q=={'observable_response':78 if 'allreduce' in rid else 75},cid+':inclusive:'+rid)
        check(pre[cid]['whole_model_layers']==78,cid+':whole_layers')
        cond=pre[cid]['conditions'];check(cond['new_empirical_prolog_or_attention_response'] is False,cid+':no_extra_floor')
        check(cond==decl['scenario_evidence']['source_recipe_conditions'],cid+':conditions_visible')
        expected=native['geometry']['query_rows']
        check(cond['captured_prolog_tokens']==expected,cid+':actual_M')
        check(cond['declared_prolog_tokens']==[expected if captured_grid else 48 if expected==48 else 16],cid+':declared_M')
        check(cond['prolog_active_contract_equal']==(captured_grid or expected==48),cid+':gap_not_hidden')
        check(pre[cid]['program_recipe_counts']['declared_native_fusion']==78,cid+':one_prolog_per_layer')
        check(pre[cid]['program_recipe_counts']['latent_attention_batch']==78,cid+':one_full_batch_SFA_per_layer')
        check(pre[cid]['source_native_calls_per_forward']['MlaPrologV3']==78,cid+':native_prolog_population')
        check(pre[cid]['source_native_calls_per_forward']['KvQuantSparseFlashAttention']==78,cid+':native_SFA_population')
        check(native['forward_count']==row['comparison']['observed_ms']['count'],cid+':same_forward_count')
        check(native['source_identity']['sha256']==row['source_identity']['sha256'],cid+':source')
        check(not row['prediction_execution']['reused_prediction'],cid+':fresh_cost')
        check(row['prediction_execution']['execution']['peak_rss_bytes']<=512*1024**2,cid+':memory')
    result={'status':'failed' if failures else 'passed','checks':checks,'failures':failures,
        'report_identity':{'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest()},
        'raw_reads':0,'cost_predictions':0,
        'scope':'Independent preserved-input/rule/population checks. Standard review separately checks all Body/layer numeric arithmetic.'}
    (ROOT/f'{stem}-independent-review.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    if failures:raise SystemExit(1)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captured-grid',action='store_true')
    main(parser.parse_args().captured_grid)
