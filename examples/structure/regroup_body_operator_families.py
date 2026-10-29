"""[Role] Canonicalize saved native fusion cohorts using exact duration histograms.
[Invariants] Only equal contract/work/placement groups merge; timestamps are not
  recreated. Merged busy union remains unknown. Original artifacts stay intact.
[Timeouts & Locks] Local bounded saved JSON, no raw reads or process execution.
[Side-Effect Policy] Write a separate canonical variant, retaining source hashes.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import argparse,json,re,shutil
from replay_body_operator_families import read,write,identity,export_structure,RoleMapper,duration_stats
from mindie_profiler.structure_cohorts import CohortAccumulator,_canonical


def role(value):return '|'.join(re.sub(r'^s\d+\.l\d+\.','',part.removeprefix('subgraph:')) for part in value.split('|'))


def regroup(path):
    actual=read(path);prefix=path.with_name(path.name.removesuffix('.actual.json'))
    mapping=read(prefix.with_suffix('.mapping.json'));case=read(prefix.with_suffix('.case.json'))
    execution=mapping['declared_execution'];manifest=export_structure(case,**{k:execution[k]for k in ('phase','tokens','context','sequences','scope')})
    if manifest['graph_id']!=mapping['graph_id']:raise ValueError('declaration_changed')
    mapper=RoleMapper(manifest,mapping_limit=0,phase='decode')
    prior_roles=mapping['conditional_role_by_cohort_id']
    families={(row['native_operator_type'],row['declared_role']):row for row in actual['families']}
    cohort_family_counts=Counter((row['native_operator_type'],'|'.join(prior_roles[row['cohort_id']]))
                                for window in mapping['windows'] for row in window['cohorts'])
    new_roles={};merged_count=0
    for window in mapping['windows']:
        observation=SimpleNamespace(rank_id=window['rank_id'],source=SimpleNamespace(rank_id=window['rank_id']))
        accumulator=CohortAccumulator(manifest['graph_id'],mapper.target_index,observation,execution=execution)
        grouped=defaultdict(list)
        for row in window['cohorts']:
            key=(row['native_operator_type'],tuple(role(v) for v in prior_roles[row['cohort_id']]),row['physical_signature'],
                 row['device_id'],_canonical(row['contract']),_canonical(row.get('contract_scope')),row['replica'],row['stage'])
            grouped[key].append(row)
        rows=[]
        for key,old in grouped.items():
            if len(old)==1:
                row=old[0];new_roles[row['cohort_id']]=list(key[1]);rows.append(row);continue
            selected_ids=sorted({identifier for row in old for identifier in row['target_ids']})
            declaration,reason=accumulator._cohort(selected_ids)
            if reason:raise ValueError(reason)
            histogram=Counter()
            for row in old:
                family_key=(row['native_operator_type'],'|'.join(prior_roles[row['cohort_id']]))
                if cohort_family_counts[family_key]!=1 or row['clipped_event_count']:
                    raise ValueError('saved_histogram_not_unique_complete_cohort_population')
                histogram.update(dict(families[family_key]['duration_ns_counter']))
            count=sum(histogram.values());activity=sum(v*n for v,n in histogram.items())
            if count!=sum(row['event_count'] for row in old) or activity!=sum(row['complete_activity_sum_ns'] for row in old):
                raise ValueError('histogram_population_mismatch')
            cohort_id='sha256:'+sha256(_canonical((manifest['graph_id'],window['rank_id'],(key[0],key[3],tuple(selected_ids)))).encode()).hexdigest()
            status=Counter()
            for row in old:status.update(row['status_counts'])
            stats=duration_stats(histogram,1)
            row={**old[0],**declaration,'cohort_id':cohort_id,'event_count':count,'complete_event_count':count,
                 'activity_sum_ns':activity,'complete_activity_sum_ns':activity,'status_counts':dict(status),
                 'busy_union_ns':None,'busy_union_basis':'unavailable_from_saved_duration_histograms',
                 'duration_ns':{k:stats[k]for k in ('mean','p50','min','max')},
                 'candidate_refinements':[{'basis':'whole_body_topology_conditioned_role','declared_roles':list(key[1]),
                     'occurrence_binding_implied':False,'event_count':count}],
                 'multiplicity':{**old[0]['multiplicity'],'observed_calls':count,
                     'declared_instances':declaration['declared_instance_count'],
                     'declared_candidate_instances':declaration['declared_candidate_instance_count'],
                     'calls_per_declared_instance':count/declaration['declared_instance_count']},
                 'regrouped_from_cohort_ids':[r['cohort_id']for r in old]}
            row['duration_ns']['basis']='complete_events_only'
            new_roles[cohort_id]=list(key[1]);rows.append(row);merged_count+=len(old)-1
        window['cohorts']=rows
    mapping['conditional_role_by_cohort_id']=new_roles
    regrouped={}
    for old in actual['families']:
        key=(old['native_operator_type'],role(old['declared_role']))
        row=regrouped.setdefault(key,{**old,'declared_role':key[1],'_hist':Counter(),'_reasons':Counter(),'_targets':set(),'_layers':defaultdict(Counter)})
        row['_hist'].update(dict(old['duration_ns_counter']));row['_reasons'].update(old['cohort_reasons']);row['_targets'].update(old['candidate_target_ids'])
        for name,group in old['layer_groups'].items():row['_layers'][name].update(dict(group['duration_ns_counter']))
    result=[]
    for row in regrouped.values():
        hist=row.pop('_hist');row['duration_ns_counter']=sorted(hist.items());row['observed_us']=duration_stats(hist,1000)
        row['cohort_reasons']=dict(row.pop('_reasons'));row['candidate_target_ids']=sorted(row.pop('_targets'))
        row['layer_groups']={name:{'duration_ns_counter':sorted(hist.items()),'observed_us':duration_stats(hist,1000)}for name,hist in row.pop('_layers').items()}
        result.append(row)
    provenance={'actual_identity':identity(path),'mapping_identity':identity(prefix.with_suffix('.mapping.json')),
        'raw_capture_reads':0,'prediction_executions':0,'merged_cohort_count':merged_count,
        'busy_union_policy':'unknown_for_merged_groups; duration_histograms_preserve_mean_p50_and_activity_exactly',
        'script_identity':identity(__file__)}
    actual.update(variant=actual['variant']+'-canonical',families=result,regrouping=provenance)
    mapping['regrouping']=provenance
    destination=prefix.with_name(prefix.name+'-canonical')
    write(destination.with_suffix('.actual.json'),actual);write(destination.with_suffix('.mapping.json'),mapping)
    write(destination.with_suffix('.case.json'),case)
    return destination,len(mapping['windows'][0]['cohorts'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('actual',type=Path);args=parser.parse_args()
    print(regroup(args.actual))


if __name__=='__main__':main()
