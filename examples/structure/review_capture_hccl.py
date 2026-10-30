"""[Role] Independently verify full-capture and retained-Body HCCL ledgers.
[Invariants] Population/geometry and integer endpoints match accepted artifacts;
  raw capture inventory includes duplicates while Body collective rows deduplicate
  only exact signatures. No pipeline sum is interpreted as communication service.
[Timeouts & Locks] One source JSON at a time; no raw capture scans or costs.
[Side-Effect Policy] Saved evidence reads and compact review/summary writes only.
"""
from collections import Counter, defaultdict
from decimal import Decimal
from math import ceil, isclose
from pathlib import Path
import argparse
import json
import resource
import sys

from replay_body_operator_families import identity, read, write


def stats(hist,scale=1):
    pairs=sorted((Decimal(str(v)),n) for v,n in hist);count=sum(n for _,n in pairs)
    if not count:return None
    def value_at(position):
        seen=0
        for value,n in pairs:
            if seen+n>position:return value
            seen+=n
        raise AssertionError('histogram_population')
    return {'count':count,'mean':float(sum(v*n for v,n in pairs)/count/scale),
        'p50':float((value_at((count-1)//2)+value_at(count//2))/2/scale),
        'p90':float(value_at(ceil(count*.9)-1)/scale),'min':float(pairs[0][0]/scale),'max':float(pairs[-1][0]/scale)}


def same_stats(actual,expected):
    if expected is None:assert actual is None;return
    assert actual['count']==expected['count']
    for key in ('mean','p50','p90','min','max'):
        assert isclose(actual[key],expected[key],rel_tol=1e-12,abs_tol=1e-9),(key,actual[key],expected[key])


def review_group(group):
    checks=0;hist=group['duration_ns_counter'];count=sum(n for _,n in hist)
    same_stats(group['observed_us'],stats(hist,1000));checks+=1
    assert group['raw_pmu']['event_count']==count;checks+=1
    for name,item in group['raw_pmu']['fields'].items():
        pairs=item['numeric_value_counter'];numeric=sum(n for _,n in pairs)
        assert numeric==item['numeric_count']
        assert numeric+item['missing_or_na_count']+item['invalid_numeric_count']==count
        assert sum(n for v,n in pairs if Decimal(v)==0)==item['zero_count']
        same_stats(item['statistics'],stats(pairs));checks+=4
    if 'layer_counts' in group:
        assert sum(group['layer_counts'].values())==sum(group['forward_counts'].values())==count
        checks+=1
    return checks


def key(geo):
    return tuple(geo[x] for x in ('query_rows','sequences_per_replica','tokens_per_sequence'))


def main(directory):
    manifest=read(directory/'inputs.json');by_id={c['case_id']:c for c in manifest['cases']}
    reports=[];checks=0;failures=[];capture_families=Counter();body_families=Counter();aliases=Counter()
    for case_id,entry in by_id.items():
        path=directory/f'{case_id}-capture-hccl.json'
        if not path.exists():failures.append({'case_id':case_id,'reason':'missing_completed_artifact'});continue
        value=read(path);body=read(value['body_acceptance_identity']['path'])
        assert identity(value['body_acceptance_identity']['path'])==value['body_acceptance_identity']
        assert value['source_identity']['sha256']==entry['source']['sha256'];checks+=2
        old={f['forward_id']:f for f in body['forwards']};seen=set();case_capture=Counter();case_body=Counter()
        for group in value['capture_inventory']:
            checks+=review_group(group)
            assert not group['can_add_to_other_categories'];checks+=1
            case_capture[group['native_operator_type']]+=group['observed_us']['count']
        assert sum(g['forward_count'] for g in value['body_geometry_groups'])==len(old)==value['body_count'];checks+=1
        assert len(value['body_geometry_groups'])==entry['geometry_count']==value['geometry_count'];checks+=1
        groups=[]
        for geometry in value['body_geometry_groups']:
            assert set(geometry['forward_ids'])=={fid for fid,f in old.items() if key(f['geometry'])==key(geometry['geometry'])};checks+=1
            assert len(geometry['per_forward'])==len(geometry['forward_ids'])==geometry['forward_count'];checks+=1
            counts=Counter()
            for group in geometry['groups']:
                checks+=review_group(group);counts[group['event_category']]+=group['observed_us']['count']
                case_body[group['native_operator_type']]+=group['observed_us']['count']
                assert set(group['forward_counts'])<=set(geometry['forward_ids']);checks+=1
                assert not group['communication_bandwidth_calibration_allowed'];checks+=1
            assert sum(counts.values())+geometry['counts']['exact_duplicate_summary_rows']==geometry['counts']['raw_rows_starting_inside_body'];checks+=1
            for category,n in counts.items():assert geometry['counts'][category]==n;checks+=1
            for forward in geometry['per_forward']:
                fid=forward['forward_id'];assert fid not in seen;seen.add(fid)
                assert (forward['start_ns'],forward['end_ns'])==(old[fid]['start_ns'],old[fid]['end_ns']);checks+=2
                assert forward['body_span_ns']==forward['end_ns']-forward['start_ns'];checks+=1
                for category,union in forward['category_union_ns'].items():
                    assert 0<=union<=forward['category_activity_ns'][category];checks+=1
            groups.append({'geometry':geometry['geometry'],'forward_count':geometry['forward_count'],
                'counts':geometry['counts'],'family_counts':dict(Counter({kind:sum(g['observed_us']['count'] for g in geometry['groups'] if g['native_operator_type']==kind)
                    for kind in {g['native_operator_type'] for g in geometry['groups']}}))})
        assert seen==set(old);checks+=1
        for kind,n in case_body.items():assert n<=case_capture[kind];checks+=1
        assert not value['controller_alias_overlay']['body_spans_changed'];checks+=1
        assert value['execution']['maximum_resident_set_size_bytes']<=512*1024**2;checks+=1
        aliases.update(value['controller_alias_overlay']['counts']);capture_families.update(case_capture);body_families.update(case_body)
        reports.append({'case_id':case_id,'artifact_identity':identity(path),'source_identity':value['source_identity'],
            'body_acceptance_identity':value['body_acceptance_identity'],'hardware_sku':value['hardware_sku'],
            'tp':value['tp'],'dp':value['dp'],'ep':value['ep'],'body_count':value['body_count'],'geometry_count':value['geometry_count'],
            'capture_parsed_event_count':value['capture_parsed_event_count'],'capture_family_counts':dict(case_capture),
            'body_family_counts':dict(case_body),'geometry_groups':groups,'controller_alias_overlay':value['controller_alias_overlay'],
            'prior_nine_primary_population_validation':value['prior_nine_primary_population_validation'],'execution':value['execution']})
    summary={'schema_version':'mindie-capture-and-body-hccl-summary/1','status':'failed' if failures else 'completed',
        'input_manifest_identity':identity(directory/'inputs.json'),'expected_sources':len(by_id),'completed_sources':len(reports),
        'unique_source_sha_count':len({r['source_identity']['sha256'] for r in reports}),
        'accepted_body_count':sum(r['body_count'] for r in reports),'geometry_count':sum(r['geometry_count'] for r in reports),
        'capture_parsed_event_count':sum(r['capture_parsed_event_count'] for r in reports),
        'capture_family_counts':dict(capture_families),'body_family_counts':dict(body_families),
        'controller_alias_counts':dict(aliases),'cases':reports,
        'execution':{'raw_scans':sum(r['execution']['raw_scans'] for r in reports),'predictions':0,
            'sum_source_elapsed_seconds':sum(r['execution']['elapsed_seconds'] for r in reports),
            'maximum_worker_rss_bytes':max((r['execution']['maximum_resident_set_size_bytes'] for r in reports),default=0)},
        'independent_review':{'checks':checks,'failures':failures,'raw_scans':0,'cost_predictions':0,
            'maximum_resident_set_size_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)},
        'limits':['Capture counts include raw summary duplicates and all phases; Body counts use exact summary deduplication.',
            'Controller/native fused communication populations are separate, not added into HCOM elapsed.',
            'Existing accepted Body endpoints and every geometry remain unchanged; controller aliases only expose a parser coverage gap.',
            'Task timing proximity does not establish subordinate tasks, peer waiting causes, actual algorithms or measured wire bytes.']}
    write(directory/'capture-body-hccl-summary.json',summary)
    print({k:summary[k] for k in ('status','completed_sources','accepted_body_count','geometry_count','capture_parsed_event_count')},'checks',checks,'failures',len(failures))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path)
    args=parser.parse_args();main(args.directory)
