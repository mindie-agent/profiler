"""[Role] Audit retained operator populations against typed controller evidence.
[Invariants] No native/strict budget is removed by a name alone; compare complete
  retained histograms to the same-source, same-geometry HCCL controller ledger.
[Timeouts & Locks] Sequential bounded saved JSON only; no locks or raw parsing.
[Side-Effect Policy] Write independent exclusion evidence; never rewrite costs.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def read(path):
    path=Path(path)
    if path.stat().st_size>50*1024**2:raise ValueError('bounded JSON limit')
    return json.loads(path.read_text())


def identity(path):
    path=Path(path);blob=path.read_bytes()
    return {'path':str(path.resolve()),'size_bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}


def geometry(value):
    return tuple(value.get(k)for k in ('tokens_per_sequence','sequences_per_replica','query_rows'))


def histogram(group):
    return Counter(dict(group['duration_ns_counter']))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--capture-summary',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();inputs=read(a.inputs);summary=read(a.capture_summary)
    sources={case['source_identity']['sha256']:case for case in summary['cases']}
    audited=[];failures=[];checks=0;seen={};source_receipts=[]
    def check(ok,label):
        nonlocal checks
        checks+=1
        if not ok:failures.append(label)
    for report_path in inputs['operators']:
        report=read(report_path);report_pin=identity(report_path);source_receipts.append(report_pin)
        for case in report['cases']:
            if 'actual_identity' not in case:continue
            pin=case['actual_identity'];source_sha=case['source_identity']['sha256']
            if source_sha not in sources:continue
            aliases=[family for family in case['families']if family['native_operator_type'].replace('_','').casefold()
                     in {'allreduceaicpukernel','allgatheraicpukernel','reducescatteraicpukernel','hccllaunchaicpukernel'}]
            if not aliases:continue
            actual=read(pin['path']);check(identity(pin['path'])['sha256']==pin['sha256'],'actual SHA')
            evidence_pin=sources[source_sha]['artifact_identity'];evidence=read(evidence_pin['path'])
            check(identity(evidence_pin['path'])['sha256']==evidence_pin['sha256'],'HCCL evidence SHA')
            bins=[b for b in evidence['body_geometry_groups']if geometry(b['geometry'])==geometry(actual['geometry'])]
            if len(bins)!=1:
                failures.append('unique geometry missing:'+case['case_id']);continue
            bin=bins[0]
            check(bin['forward_count']==actual['forward_count'],'same forward population')
            for family in aliases:
                native=family['native_operator_type'];key=(pin['sha256'],native)
                check(family['scored_event_count']==0 and not family['cohorts'],'controller was not a strict cohort')
                check(not family.get('conditional_source_role_references') and not family.get('conditional_program_reference'),
                      'controller was not a conditional resource program')
                full=[f for f in actual['families']if f['native_operator_type']==native]
                oldhist=Counter()
                for f in full:oldhist.update(histogram(f))
                groups=[g for g in bin['groups']if g['native_operator_type']==native]
                observed=Counter()
                for g in groups:
                    check(g['event_category']=='unlinked_aicpu_wrapper','typed controller category')
                    check(g['accelerator_core'].replace('_','').casefold()=='aicpu','raw core AI_CPU')
                    observed.update(histogram(g))
                check(bool(groups)and observed==oldhist,'complete family histogram matches same-source typed controller')
                occurrence={'operator_receipt_identity':report_pin,'report_case_id':case['case_id'],
                    'family_index':case['families'].index(family),'family_key':[native,family['declared_role']],
                    'event_count':family['observed_us']['count'],'strict_event_count':family['scored_event_count']}
                if key in seen:
                    audited[seen[key]]['matched_operator_occurrences'].append(occurrence)
                    continue
                seen[key]=len(audited)
                audited.append({'source_identity':case['source_identity'],'source_case_id':case.get('source_case_id'),
                    'geometry':actual['geometry'],'forward_count':actual['forward_count'],
                    'actual_identity':pin,'controller_ledger_identity':evidence_pin,
                    'native_operator_type':native,'observed_event_count':sum(oldhist.values()),
                    'observed_activity_sum_ns':sum(ns*n for ns,n in oldhist.items()),
                    'strict_event_count':0,'reference_event_count':0,'legacy_declared_role':family['declared_role'],
                    'full_histogram_matches_typed_controller_evidence':True,
                    'treatment':'separate controller overlay; exclude from unmodeled physical-service residual',
                    'original_cost_report_unchanged':True,'matched_operator_occurrences':[occurrence]})
    result={'schema_version':'mindie-controller-operator-population-review/1',
        'status':'passed'if not failures else'failed','input_identity':identity(a.inputs),
        'capture_summary_identity':identity(a.capture_summary),'operator_receipts':source_receipts,
        'checks':checks,'failures':failures,'populations':audited,'strict_events_to_remove':0,
        'reference_events_to_remove':0,'raw_capture_reads':0,'new_predictions':0,
        'limits':['Historical actual generations may describe the same source geometry; do not add their populations.',
                  'This evidence reclassifies only complete histograms proven typed AI_CPU by the raw-derived ledger.',
                  'Unlinked controllers are not measured transport work and do not imply peer-wait causality.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'checks':checks,'failures':failures,'populations':len(audited)}))
    raise SystemExit(bool(failures))


if __name__=='__main__':main()
