"""[Role] Validate a controller-alias extraction generation and publish its join map.
[Invariants] Source/case populations remain distinct; missing historical activity
  is unavailable, not zero. Layer ends and actual operator population boundaries
  have separate reuse decisions. Every retry retains its original receipt.
[Timeouts & Locks] Bounded saved JSON one source at a time; no raw/cost/locks.
[Side-Effect Policy] Write summary, extraction map and README only.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys


def read(path):
    path=Path(path)
    if path.stat().st_size>50*1024**2:raise ValueError('bounded metadata read')
    return json.loads(path.read_text())


def identity(path):
    path=Path(path);blob=path.read_bytes()
    return {'path':str(path.resolve()),'size_bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt',type=Path,required=True);parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
    receipt=read(args.receipt);inputs=read(args.inputs);oldby={e['case_id']:e for e in inputs['cases']}
    checks=0;failures=[]
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    def pin(value):
        result=identity(value['path'])
        check(result['sha256']==value['sha256']and result['size_bytes']==value['size_bytes'],'immutable input:'+value['path'])
    check(receipt['status']=='completed','all source workers complete')
    check({r['case_id']for r in receipt['cases']}==set(oldby),'all66 source IDs')
    rows=[];mapping=[];totals=Counter();core_hashes=set()
    for row in receipt['cases']:
        check(row['status']=='completed',row['case_id']+':worker success')
        pin(row['comparison_identity']);d=read(row['comparison_identity']['path']);pin(d['new_extraction_identity']);pin(d['previous_extraction_identity'])
        old=read(d['previous_extraction_identity']['path']);new=read(d['new_extraction_identity']['path']);c=d['comparison'];e=oldby[row['case_id']]
        for key in ('path','sha256','size_bytes'):check(new['source_identity'][key]==e['source'][key],row['case_id']+':same source')
        check(d['runtime_sources_unchanged'],row['case_id']+':worker sources stable')
        core_hashes.update(digest for path,digest in d['runtime_source_identity'].items()if path.endswith('/decode_segmentation.py'))
        counts=c['same_stream_previous_policy']['counts'];changes=c['same_stream_previous_policy']['scope_changes']
        layer_starts=[x for x in changes if x['layer_id']is not None and 'start_ns'in x['changed_fields']]
        layer_ends=[x for x in changes if x['layer_id']is not None and 'end_ns'in x['changed_fields']]
        body_ends=[x for x in changes if x['kind']=='target_body'and 'end_ns'in x['changed_fields']]
        plans=[p for p in e['model_config']['layer_plans']if not p.get('mtp',False)]
        check(counts['layers_checked']==len(new['forwards'])*len(plans),row['case_id']+':every complete layer paired')
        check(counts.get('layer_endpoints_changed',0)==len(layer_starts)+len(layer_ends)-sum('end_ns'in x['changed_fields']for x in layer_starts),row['case_id']+':scope delta count')
        oldbyid={x['forward_id']:x for x in old['forwards']}
        check(len(old['forwards'])==c['previous_body_count']and len(new['forwards'])==c['current_body_count'],row['case_id']+':forward population')
        check(len(old['geometry_groups'])==c['previous_geometry_count']and len(new['geometry_groups'])==c['current_geometry_count'],row['case_id']+':geometry population')
        # Confirm actual retained-forward coordinates independently of the metadata matcher.
        same_population=len(old['forwards'])==len(new['forwards'])
        body_endpoint_changes=0;geometry_changes=0
        for f in new['forwards']:
            prior=oldbyid.get(f['forward_id'])
            if prior is None:same_population=False;continue
            check((f['head_start_ns'],f['head_end_ns'])==(prior['head_start_ns'],prior['head_end_ns']),row['case_id']+':same closure')
            body_endpoint_changes+=any(f[k]!=prior[k]for k in ('start_ns','end_ns'))
            geometry_changes+=f['geometry']!=prior['geometry']
            check(abs(f['body_forward_span_ms']-(f['end_ns']-f['start_ns'])/1e6)<1e-12,row['case_id']+':integer body span')
            check(abs(f['body_activity_ms']+f['body_internal_gap_ms']-f['body_forward_span_ms'])<1e-9,row['case_id']+':union plus gap')
        check(c['body_endpoint_changed_count']==body_endpoint_changes,row['case_id']+':saved endpoint delta')
        check(c['body_geometry_changed_count']==geometry_changes,row['case_id']+':saved geometry delta')
        reusable=same_population and not body_endpoint_changes and not geometry_changes and not layer_starts
        # FFN cut is chosen from the same raw norm and anchor indices. The
        # controller-only predicate is not used by those selectors.
        result={'case_id':row['case_id'],'source_identity':e['source'],
            'comparison_identity':row['comparison_identity'],'new_extraction_identity':d['new_extraction_identity'],
            'previous_extraction_identity':d['previous_extraction_identity'],
            'previous_body_count':len(old['forwards']),'current_body_count':len(new['forwards']),
            'previous_geometry_count':len(old['geometry_groups']),'current_geometry_count':len(new['geometry_groups']),
            'accepted_population_unchanged':same_population,'body_endpoint_changed_count':body_endpoint_changes,
            'body_geometry_changed_count':geometry_changes,'body_activity_changed_count':c['body_activity_changed_count'],
            'historical_activity_unavailable_count':c.get('body_activity_previous_missing_count',0),
            'layer_scope_count':counts['layers_checked'],'layer_start_changed_count':len(layer_starts),
            'layer_end_changed_count':len(layer_ends),'per_layer_span_changed':bool(layer_starts or layer_ends),
            'body_operator_population_reusable':reusable,
            'operator_reuse_basis':'same body endpoints/geometry/whole topology and raw layer starts; BodyConsumer FFN norm/anchor partition is independent of controller end',
            'scope_pair_evidence':{'paired_delta_count':len(changes),'complete_same_stream_pairing':True},
            'new_body_controller_alias_count':d['body_controller_accounting'].get('newly_recognized_controller_aliases',0),
            'body_hcom_rows_preserved':d['body_controller_accounting'].get('hcom_rows_preserved',0),
            'maximum_resident_set_size_bytes':d['maximum_resident_set_size_bytes'],
            'individual_runtime_source_identity_retained':True}
        check(result['maximum_resident_set_size_bytes']<=512*1024**2,row['case_id']+':memory budget')
        rows.append(result)
        mapping.append({'case_id':row['case_id'],'source':e['source'],
            'extraction_path':d['new_extraction_identity']['path'],'extraction_identity':d['new_extraction_identity'],
            'previous_extraction_identity':d['previous_extraction_identity'],
            'model_config_sha256':new['extraction_provenance']['model_config_sha256'],
            'model_configuration_reused_exactly':True,'comparison_identity':row['comparison_identity'],
            'body_operator_population_reusable':reusable,'per_layer_span_changed':result['per_layer_span_changed']})
        totals.update(sources=1,previous_bodies=len(old['forwards']),current_bodies=len(new['forwards']),
            previous_geometries=len(old['geometry_groups']),current_geometries=len(new['geometry_groups']),
            parsed_events=new['scan_counts']['scanned_events'],body_endpoints_changed=body_endpoint_changes,
            layer_starts_changed=len(layer_starts),layer_ends_changed=len(layer_ends),
            body_activity_changed=c['body_activity_changed_count'],
            historical_activity_unavailable=c.get('body_activity_previous_missing_count',0),
            paired_layers=counts['layers_checked'],body_new_controller_aliases=result['new_body_controller_alias_count'])
        del old,new,d
    check(len(core_hashes)==1,'single canonical controller core generation')
    check((totals['sources'],totals['current_bodies'],totals['current_geometries'])==(66,5250,222),'complete expected population')
    history=[]
    for path in (args.output_dir/'decode-forward-auto-acceptance.json',args.output_dir/'scope-paired/decode-forward-auto-acceptance.json',args.receipt):
        prior=read(path)
        attempts=prior.get('raw_capture_scan_attempts',sum(not x.get('reused_successful_extraction',False)for x in prior['cases']))
        history.append({'receipt_identity':identity(path),'status':prior['status'],'scan_attempts':attempts,
            'metadata_failed_cases':[x['case_id']for x in prior['cases']if x['status']=='failed']})
    result={'schema_version':'mindie-controller-alias-summary/1','status':'passed'if not failures else'failed',
        'checks':checks,'failures':failures,'core_sha256':next(iter(core_hashes)),'totals':dict(totals),
        'receipt_identity':identity(args.receipt),'input_manifest_identity':identity(args.inputs),
        'execution_history':history,'total_raw_scan_attempts':sum(x['scan_attempts']for x in history),
        'new_predictions':0,'cases':rows,
        'operator_population_review_identity':identity(args.output_dir/'operator-population-review.json'),
        'maximum_worker_resident_set_size_bytes':max(x['maximum_resident_set_size_bytes']for x in rows),
        'review_maximum_resident_set_size_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin'else 1024),
        'limits':['Original extractions and failed metadata attempts remain immutable.',
                  'Missing prior activity metrics are unavailable; newly provided metrics are not reported as measured deltas.',
                  'Layer span changes and strict/native event populations use separate reuse decisions.',
                  'Typed AICPU control overlays are separate from physical-service residuals; HCOM data-plane intervals remain.',
                  'Controller suffix removal still requires an actual successor boundary; internal communication is retained.']}
    output=args.output_dir/'controller-alias-summary.json';output.write_text(json.dumps(result,indent=2)+'\n')
    mapdoc={'schema_version':'mindie-forward-extraction-generation-map/1','status':result['status'],
        'summary_identity':identity(output),'input_manifest_identity':identity(args.inputs),
        'cases':mapping,'model_or_cost_inputs_changed':False,'new_predictions':0}
    (args.output_dir/'extraction-generation-map.json').write_text(json.dumps(mapdoc,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'checks':checks,'failures':failures,'totals':dict(totals),
        'raw_scan_attempts':result['total_raw_scan_attempts'],'maximum_worker_MiB':result['maximum_worker_resident_set_size_bytes']/1024**2}))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
