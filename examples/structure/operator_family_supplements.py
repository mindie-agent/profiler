"""Native-family-complete supplements to an existing operator population.

[Role] Replace one native family's current rows without replacing its source.
[Invariants] Whole native histogram and accepted Body identity must agree exactly.
  An input cannot add a source population, invent calls or replace unrelated work.
[Timeouts & Locks] One bounded retained actual at a time; no processes/locks.
[Side-Effect Policy] Reads pinned local metadata; returns new scoreboard rows.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path


def histogram(case, native):
    total=Counter()
    for family in case['families']:
        if family['native_operator_type']==native:
            total.update({int(ns):int(n) for ns,n in family['duration_ns_counter']})
    return sorted(total.items())


def histogram_digest(value):
    return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()


def checked_actual(pin):
    path=Path(pin['path'])
    if not path.is_absolute():path=Path(__file__).resolve().parents[2]/path
    if path.stat().st_size>50*1024**2:raise ValueError('supplement_actual_exceeds_bounded_read')
    data=path.read_bytes()
    if hashlib.sha256(data).hexdigest()!=pin['sha256']:raise ValueError('supplement_actual_identity_changed')
    return json.loads(data)


def validate(case, base, *, baseline_actual):
    natives=case['native_operator_types']
    if not natives or len(natives)!=len(set(natives)):
        raise ValueError('supplement_native_family_scope_invalid')
    if {f['native_operator_type'] for f in case['families']}!=set(natives):
        raise ValueError('supplement_family_scope_differs')
    for field in ('source_identity','geometry','forward_count','body_acceptance_identity'):
        if case[field]!=baseline_actual[field]:raise ValueError('supplement_population_differs:'+field)
    if case['forward_count']!=base['forward_count']:
        raise ValueError('supplement_current_forward_denominator_differs')
    own_actual=checked_actual(case['actual_identity'])
    for field in ('source_identity','geometry','forward_count','body_acceptance_identity'):
        if own_actual[field]!=case[field]:raise ValueError('supplement_retained_actual_differs:'+field)
    for native in natives:
        saved=histogram(baseline_actual,native);fresh=histogram(case,native)
        if not saved or fresh!=saved or fresh!=histogram(own_actual,native):
            raise ValueError('supplement_must_cover_complete_native_histogram:'+native)
        proof=case['native_population_evidence'][native]
        if proof!={'event_count':sum(n for _,n in saved),'duration_ns_histogram_sha256':histogram_digest(saved)}:
            raise ValueError('supplement_native_population_proof_differs')
    return {n:case['native_population_evidence'][n] for n in natives}


def project_references(references, supplement, *, reference_identity, supplement_identity):
    """Retain historical costs while removing exactly superseded current calls."""
    import copy
    projected=copy.deepcopy(references)
    superseded=[]
    for case in projected['cases']:
        matches=[s for s in supplement['cases'] if all(s[k]==case[k] for k in
                 ('source_identity','geometry','forward_count','body_acceptance_identity'))]
        if not matches:continue
        if len(matches)!=1:raise ValueError('reference_supplement_population_not_unique')
        scoped=matches[0]
        for native in scoped['native_operator_types']:
            removed=[g for g in case['groups'] if g['native_operator_type']==native]
            if not removed:continue
            counts=Counter()
            for group in removed:counts.update(dict(group['duration_ns_counter']))
            retained=sorted((int(ns),int(n)) for ns,n in counts.items())
            if retained!=histogram(scoped,native):
                raise ValueError('reference_supplement_histogram_differs')
            superseded.append({'source_identity':case['source_identity'],'geometry':case['geometry'],
                'case_id':case['case_id'],'native_operator_type':native,
                'forward_count':case['forward_count'],'observed_event_count':sum(counts.values()),
                'group_ids':[g['group_id'] for g in removed],
                'status':'superseded_by_scoped_strict','supplement_case_id':scoped['case_id'],
                'supplement_identity':supplement_identity})
            case['groups']=[g for g in case['groups'] if g['native_operator_type']!=native]
        case['historical_native_event_count']=case['native_event_count']
        case['referenced_event_count']=sum(g['observed_us']['count'] for g in case['groups'])
        case['native_event_count']=case['referenced_event_count']+sum(g['event_count'] for g in case['unresolved'])
    projected.update({'historical_reference_identity':reference_identity,
        'superseding_operator_supplement_identity':supplement_identity,
        'superseded_reference_populations':superseded,
        'projection_policy':'Exact whole-native histogram moved to scoped strict; original reference receipt and costs remain historical.',
        'historical_execution':projected.pop('execution'),
        'execution':{'raw_capture_reads':0,'new_cost_evaluations':0,
                     'basis':'projection_of_already_completed_reference_costs'}})
    return projected


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Project current references after complete family strict supplements.')
    parser.add_argument('--references',type=Path,required=True)
    parser.add_argument('--supplement',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    def load(path):
        if path.stat().st_size>50*1024**2:raise ValueError('reference_projection_exceeds_bounded_read')
        payload=path.read_bytes()
        return json.loads(payload),{'path':str(path.resolve()),'size_bytes':len(payload),
            'sha256':hashlib.sha256(payload).hexdigest()}
    references,reference_pin=load(args.references);supplement,supplement_pin=load(args.supplement)
    result=project_references(references,supplement,reference_identity=reference_pin,supplement_identity=supplement_pin)
    result['projection_tool_identity']={
        'path':str(Path(__file__).resolve()),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
