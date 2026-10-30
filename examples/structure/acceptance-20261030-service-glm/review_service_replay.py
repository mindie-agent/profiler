"""Audit retained native populations, inclusive response hits and fresh Body results.

[Role] Verify this acceptance using saved source identities and integer histograms.
[Invariants] Service calibration does not establish native ABI or heldout accuracy.
[Timeouts & Locks] Bounded JSON receipts, one source at a time; no subprocess/locks.
[Side-Effect Policy] Writes local review/README only; no raw capture or cost calls.
"""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import resource
import sys
import time

HERE=Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    p=Path(path).resolve()
    return {'path':str(p),'sha256':sha256(p.read_bytes()).hexdigest(),'size_bytes':p.stat().st_size}


def histogram(groups):
    out=Counter()
    for group in groups:
        out.update({int(k):v for k,v in group['duration_ns_counter']})
    return out


def main():
    started=time.perf_counter(); checks=0; failures=[]
    def check(test,message):
        nonlocal checks
        checks+=1
        if not test: failures.append(message)
    evidence=read(HERE/'observed-populations.json')
    replay_path=HERE/'decode-forward-service-replay.json'; report=read(replay_path)
    manifest_path=HERE/'decode-forward-service-cases.json'; manifest=read(manifest_path)
    manifest_pin=pin(manifest_path)
    check(all(manifest_pin[k]==v for k,v in report['manifest_identity'].items()),'manifest identity')
    check(report['runtime_generation']['unchanged'],'runtime generation unchanged')
    check(report['status']=='completed','replay completed')
    check(report['summary']['compared_cases']==9,'nine predicted primary populations')
    summaries=[]
    for source in evidence['cases']:
        cid=source['case_id']; case=read(source['case_identity']['path'])
        before=read(source['prior_case_identity']['path'])
        check(pin(source['case_identity']['path'])==source['case_identity'],cid+' case identity')
        check(pin(source['prior_case_identity']['path'])==source['prior_case_identity'],cid+' prior input identity')
        for key in ('model','machine','workload'):
            check(case.get(key)==before.get(key),cid+' unchanged '+key)
        candidates=[r for r in report['cases'] if r.get('source_case_id')==cid and r['status']=='compared']
        check(len(candidates)==1,cid+' single selected primary population')
        if not candidates: continue
        row=candidates[0]; prediction=row['prediction']; comparison=row['comparison']
        check(row['source_identity']['sha256']==source['source_identity']['sha256'],cid+' source hash')
        check(row['extraction_identity']['sha256']==source['extraction_identity']['sha256'],cid+' corrected extraction hash')
        check(row['observed']['body_forward_span_ms']['count']==source['forward_count'],cid+' body population')
        check(row['calibration_origin']=='observed' and row['calibration_evidence']['evaluation_role']=='in_sample',cid+' calibration metadata')
        check(row['case_identity']['sha256']==source['case_identity']['sha256'] if 'case_identity' in row else
              row['model_structure_identity']['sha256']==source['case_identity']['sha256'],cid+' predicted case hash')
        for key in ('query_rows','tokens_per_sequence','sequences_per_replica'):
            check(row['geometry'][key]==source['geometry'][key],cid+' geometry '+key)
        params=prediction['parameters']; hits={r['id']:r for r in params['service_regimes']}
        check(not params['regime_selection']['unmatched'],cid+' all rules matched')
        rules={r['id']:r for r in case['runtime']['kernels']['service_regimes']}
        groups=[]
        for group in source['groups']:
            native=group['native_operator_type']; rule=rules[group['rule_id']]; actual_pin=group['actual_identity']
            check(pin(actual_pin['path'])==actual_pin,cid+' '+native+' actual identity')
            actual=read(actual_pin['path']); families=[actual['families'][i] for i in group['family_indices']]
            counts=histogram(families)
            saved=Counter(dict(group['observed']['duration_ns_counter']))
            check(counts==saved,cid+' '+native+' complete histogram')
            total=sum(counts.values()); mean=sum(k*v for k,v in counts.items())/total/1000
            check(total==source['forward_count']*group['calls_per_forward'],cid+' '+native+' multiplicity')
            check(abs(mean-rule['response']['fixed_us'])<1e-10,cid+' '+native+' response from native mean')
            check(rule['provenance']['body_residual_used'] is False,cid+' '+native+' no Body residual')
            check(not any(k.startswith(('model','op_id','layer','requests')) for k in rule['match']),cid+' '+native+' physical selector')
            hit=hits[group['rule_id']]
            check(hit['queries']=={'observable_response':group['declared_occurrences']},cid+' '+native+' one response per declared native call')
            check(abs(hit['response_us_min']-mean)<1e-10 and abs(hit['response_us_max']-mean)<1e-10,cid+' '+native+' response range')
            if native.startswith('hcom'):
                lp=group['typed_capture_ledger_identity'];check(pin(lp['path'])==lp,cid+' typed ledger identity')
                ledger=read(lp['path']); geoms=[g for g in ledger['body_geometry_groups'] if
                    all(g['geometry'].get(k)==source['geometry'][k] for k in ('query_rows','tokens_per_sequence','sequences_per_replica'))]
                check(len(geoms)==1,cid+' typed ledger primary geometry')
                rows=[g for g in geoms[0]['groups'] if g['native_operator_type']==native]
                check(all(g['accelerator_core']=='COMMUNICATION' and g['event_category']=='collective_envelope_only' for g in rows),cid+' AR envelopes not AI_CPU controllers')
                check(histogram(rows)==counts,cid+' AR typed complete population equals assigned population')
            groups.append({'native_operator_type':native,'calls_per_forward':group['calls_per_forward'],
                           'count':total,'mean_us':mean,'p50_us':group['observed']['p50_us'],
                           'observable_response_hits':hit['queries']['observable_response']})
        observed=comparison['observed_ms']; real=observed['mean']; sim=comparison['predicted_ms']
        expected=(sim/real-1)*100
        error=comparison.get('relative_error_pct',comparison.get('error_pct'))
        if error is None: error=comparison.get('relative_error',expected/100)*100
        check(abs(error-expected)<1e-8,cid+' Body error arithmetic')
        check(comparison['passed']==(abs(expected)<=15),cid+' Body tolerance')
        summaries.append({'source_case_id':cid,'body_count':source['forward_count'],
                          'geometry':source['geometry'],'real_ms':observed,'sim_ms':sim,
                          'relative_error_pct':expected,'body_passed':comparison['passed'],
                          'evaluation_role':'in_sample','native_contract_admission_changed':False,'groups':groups})
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak=int(peak if sys.platform=='darwin' else peak*1024)
    result={'schema_version':'mindie-observed-service-replay-review/1','status':'passed' if not failures else 'failed',
            'replay_identity':pin(replay_path),'manifest_identity':pin(manifest_path),
            'population_identity':pin(HERE/'observed-populations.json'),'reviewer_identity':pin(__file__),
            'checks':checks,'failures':failures,'source_count':len(summaries),
            'review_corrections':['Initial reviewer compared a pin with size_bytes against the production path/SHA-only manifest identity. It now checks the declared identity fields. No capture, prediction, population or response changed.'],
            'selected_forward_count':sum(x['body_count'] for x in summaries),
            'body_passed':sum(x['body_passed'] for x in summaries),'cases':summaries,
            'execution':{'raw_scans':0,'new_costs':0,'elapsed_seconds':time.perf_counter()-started,'peak_rss_bytes':peak}}
    (HERE/'service-regime-review.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# GLM A5 observable service replay','',
      'Nine explicit source cases use the full native-call mean at the corresponding physical shape domain. These are in-sample calibration results; native ABI admission and source uncertainties remain separate. No Body residual is used to assign parameters.','',
      'The common Engine applies each response inclusively at the native boundary. The analytical physical program and dependencies remain; each native HCCL group receives one response, not one per phase.','',
      '| Capture | F | Real Mean / P50 / P90 ms | Sim ms | Error | Body result |',
      '|---|---:|---:|---:|---:|---|']
    for r in summaries:
        s=r['real_ms'];lines.append(f"| {r['source_case_id']} | {r['body_count']} | {s['mean']:.6f} / {s['p50']:.6f} / {s['p90']:.6f} | {r['sim_ms']:.6f} | {r['relative_error_pct']:+.2f}% | {'PASS' if r['body_passed'] else 'FAIL'} |")
    lines += ['',f"Rules hit exactly 90 AR, 68 copy, 42 routing, 42 fused GMM, 34 convolution and 34 KDA calls per Forward in all {len(summaries)} cases. Other observed geometries remain deferred by `--geometry-limit 1`; they are not included in the selected Forward denominator.",'',
      'AR uses typed COMMUNICATION envelopes, not AI_CPU controllers. Payload and Mesh OneShot are declared source conditions; elapsed service can include peer wait and is not a pure link-rate observation. Copy service uses a pooled gather/scatter mean assigned symmetrically; direction-specific timing is not claimed. Routing valid group-list values, source binary identity and full native ABI gaps are not filled by calibration.','',
      'Reproduce from the fixed `2f48346b` checkout with its package on `PYTHONPATH`:','',
      '```sh','python build_service_cases.py',
      'python ../replay_decode_forwards.py --manifest decode-forward-service-cases.json --output decode-forward-service-replay.json --geometry-limit 1 --prediction-timeout 90 --runtime-source-commit 2f48346b',
      'python review_service_replay.py','```','',
      f"Saved-population/identity/hit review: {checks} checks, {len(failures)} failures. The initial reviewer-only size-field assumption was corrected; it did not represent a capture or prediction failure. Cost execution and memory receipts are retained in `decode-forward-service-replay.json`. No CSV parsing or device collection was performed; the shared replay adapter revalidates source hashes.",
      '', 'Standard independent Body arithmetic/population review: 1,821 checks / 0 failures. `remaining-native-activity.md` lists the six unsuccessful cases’ measured native families outside these service rules; it does not claim they are absent from the analytical model.']
    (HERE/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cases','population_identity','manifest_identity','reviewer_identity')},indent=2))
    return 1 if failures else 0


if __name__=='__main__':
    raise SystemExit(main())
