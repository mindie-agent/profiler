"""Price saved complete-body cohorts and preserve unmodeled native coverage.

[Role] Reuse Sim cohort and program costing for body-only operator scoreboards.
[Invariants] No observed duration selects a recipe. Accuracy decisions precede
  aggregation; missing/fused-partial boundaries do not become zero predictions.
  Incomplete collective evidence stays a reference. Its observed elapsed service
  may calibrate the same boundary without claiming a pure link rate.
[Timeouts & Locks] Serial physical programs, each with a bounded process budget.
[Side-Effect Policy] Local metadata/prediction only; no raw captures or devices.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import sys
import time

from replay_body_operator_families import BASE, read, write, identity, runtime_identity
from replay_fusion_cohorts import _compare_programs
from mindie_sim.cohort_accuracy import accuracy_fields, accuracy_policy
from mindie_sim.cohort_comparison import _predict
from mindie_sim.prediction.operator_analysis import target_graphs
from mindie_sim.prediction.program import RecipeBook
from mindie_sim.prediction.structure import parse_case
from mindie_sim.structure import export_structure
from mindie_sim.prediction.body_defaults import effective_body_declaration
from body_source_role_references import (predict_source_role_references,
                                         communication_calibration_evidence)


def prediction_runtime_identity():
    excluded={'decode_segmentation.py','forward_spans.py','graph_execution.py'}
    result={path:value for path,value in runtime_identity().items() if Path(path).name not in excluded}
    for name in (Path(__file__).name, 'operator_service_evidence.py', 'replay_fusion_cohorts.py'):
        own=identity(Path(__file__).with_name(name).resolve());result[own['path']]=own['sha256']
    return result


def program_references(case_path, mapping, actual=None):
    case=parse_case(read(case_path)); execution=mapping['declared_execution']
    geometry={key:execution[key] for key in ('phase','tokens','context','sequences','scope')}
    manifest=export_structure(case,**geometry)
    if manifest['graph_id']!=mapping['graph_id']:
        raise ValueError('communication_reference_structure_changed')
    case,_=effective_body_declaration(case,geometry['phase'],tokens=geometry['tokens'],scope=geometry['scope'])
    book=RecipeBook.from_mapping(case.runtime.kernels)
    graphs=target_graphs(case,**geometry)
    by_id={f'rank:{replica}/{op.op_id}':op for replica,ops in graphs.items() for op in book.expand(ops)}
    results={}
    for block,role in [('attention','attention_output_communication'),('ffn','ffn_down_communication')]:
        selected=[node for node in manifest['nodes'] if node['family']=='allreduce' and node.get('block')==block]
        signatures={node['physical_signature'] for node in selected}
        if not selected or len(signatures)!=1:
            results[role]={'status':'unresolved','reason':'communication_program_not_homogeneous'}
            continue
        prediction=_predict(case,selected[0],'node',by_id,book)
        results[role]={'status':'reference_only','reason':'native_collective_contract_and_captured_program_boundary_unverified',
                      'per_call_ms':prediction['per_call_ms'],'representative_target_id':selected[0]['node_id'],
                      'target_count':len(selected),'boundary':prediction['boundary'],
                      'evidence_strength':'conditional_topology_region_to_declared_collective',
                      **communication_calibration_evidence()}
    for native,family in [('fused_gdn_gating_kernel','gdn_gating'),('FusedInferAttentionScore','attention')]:
        selected=[node for node in manifest['nodes'] if node['family']==family and node.get('layer',-1)>=0]
        signatures={node['physical_signature'] for node in selected}
        if not selected or len(signatures)!=1:
            results[native]={'status':'unresolved','reason':'source_role_program_not_homogeneous'}
            continue
        target=selected[0]
        if native=='fused_gdn_gating_kernel' and target['operator'].get('metadata',{}).get('caller_implementation')!='vllm_ascend_gdn_decode':
            results[native]={'status':'unresolved','reason':'source_gdn_caller_not_declared'}
            continue
        prediction=_predict(case,target,'node',by_id,book)
        results[native]={'status':'reference_only','reason':'native_tensor_contract_incomplete_or_not_declared',
            'per_call_ms':prediction['per_call_ms'],'representative_target_id':target['node_id'],
            'target_count':len(selected),'boundary':prediction['boundary'],
            'evidence_strength':'conditional_source_role_program; not_a_tensor_contract_cohort',
            'single_device_program':prediction['single_device_program'],
            'observed_duration_used_for_selection':False}
    # The source-reference pass builds its own graph. Keeping this full-model
    # graph alive doubles DP-expanded working state without changing any cost.
    del graphs, by_id, book
    results['_source_role_groups'] = predict_source_role_references(case, manifest, actual or {})
    return results


def family_rows(actual,mapping,comparison,references):
    roles=mapping['conditional_role_by_cohort_id']
    grouped={}
    for window in comparison['windows']:
        for row in window['cohorts']:
            role='|'.join(roles[row['cohort_id']])
            grouped.setdefault((row['native_operator_type'],role),[]).append(row)
    results=[]
    for family in actual['families']:
        selected=grouped.get((family['native_operator_type'],family['declared_role']),[])
        compared=[row for row in selected if row['status']=='compared']
        reference=(references.get(family['declared_role']) if family['native_operator_type'].startswith('hcom_')
                   else references.get(family['native_operator_type']) if not compared else None)
        if family['native_operator_type'].startswith('hcom_') and not family['native_operator_type'].startswith('hcom_allReduce'):
            reference={'status':'unresolved','reason':'native_collective_algorithm_not_declared'}
        n=sum(row['observed']['event_count'] for row in compared)
        predicted=sum(row['prediction']['per_call_ms']*1000*row['observed']['event_count'] for row in compared)/n if n else None
        observed=sum(row['observed']['complete_activity_sum_ns'] for row in compared)/n/1000 if n else None
        row={**family,'cohort_count':len(selected),'scored_event_count':n,
             'unscored_event_count':family['observed_us']['count']-n,
             'cohort_status_counts':dict(Counter(item['status'] for item in selected)),
             'predicted_us':predicted,'scored_observed_mean_us':observed,
             'per_call_diff_us':predicted-observed if n else None,
             'relative_error':predicted/observed-1 if n and observed else None,
             'passed_cohort_count':sum(item['accuracy_pass'] is True for item in compared),
             'compared_cohort_count':len(compared),'cohorts':selected,
             'evidence_strength':'tensor_contract_and_conditional_whole_body_role' if selected else 'unmodeled',
             'status':'compared' if compared else 'reference_only' if selected else 'unresolved'}
        if reference:
            row['conditional_program_reference']=reference
            row['status']=reference['status']
            row['evidence_strength']=reference.get('evidence_strength','unresolved')
            row['predicted_reference_us']=reference.get('per_call_ms',0)*1000 if 'per_call_ms' in reference else None
            if row['predicted_reference_us'] is not None:
                diff=row['predicted_reference_us']-family['observed_us']['mean']
                row['reference_per_call_diff_us']=diff
                row['reference_relative_error']=diff/family['observed_us']['mean']
                row['reference_within_tolerance']=(abs(diff)<=15 if family['observed_us']['mean']<=50
                                                    else abs(row['reference_relative_error'])<=.15)
        source_groups = [group for group in references.get('_source_role_groups', ())
                         if group['native_operator_type'] == family['native_operator_type']
                         and group['declared_role'] == family['declared_role']]
        if source_groups:
            if sum(group['observed_us']['count'] for group in source_groups) != family['observed_us']['count']:
                raise ValueError('source_role_reference_population_differs')
            row['conditional_source_role_references'] = source_groups
            row['evidence_strength'] = 'source_reference'
            row['status'] = 'reference_only'
        results.append(row)
    return results


def render(report):
    populations={}
    for case in report['cases']:
        key=(case['source_identity']['sha256'],json.dumps(case['geometry'],sort_keys=True))
        populations[key]=case['forward_count']
    forwards=sum(populations.values());sources=len({key[0] for key in populations})
    lines=['# Complete Decode Body Operator Families','',
           f'Only complete events inside the {forwards} accepted target-body windows from {sources} sources enter this report. '
           'Heads, auxiliary forwards and typed scheduler wrappers are excluded. Exact HCOM summary duplicates are removed.',
           'Mean/P50 are pooled native-call statistics. Sim roles are conditioned on the complete declared topology; no Host layer binding is asserted.',
           'Declaration arms may reuse captures. Calls summed across arms are not independent observations.',
           'Accuracy is decided per tensor/physical-work cohort: >50 us uses 15% relative error; <=50 us uses 15 us absolute error. '
           'Collective references retain unseparated peer wait. Their same-boundary service may be calibrated; this does not identify pure link bandwidth or complete missing native contracts.','',
           '| Case | <=50 us passed / compared | >50 us passed / compared | All passed / compared | Scored / body calls | Prediction failed |',
           '| --- | ---: | ---: | ---: | ---: | ---: |']
    for case in report['cases']:
        c=case['comparison_status_counts'];tiers={tier:[0,0] for tier in ('absolute_15us','relative_15pct')}
        for family in case['families']:
            for cohort in family['cohorts']:
                if cohort['status']=='compared':
                    tiers[cohort['accuracy_tier']][0]+=int(cohort['accuracy_pass']);tiers[cohort['accuracy_tier']][1]+=1
        small,large=tiers.values()
        scored=sum(row['scored_event_count'] for row in case['families'])
        population=sum(row['observed_us']['count'] for row in case['families'])
        lines.append(f"| {case['case_id']} | {small[0]} / {small[1]} | {large[0]} / {large[1]} | "
                     f"{case['passed_cohorts']} / {c.get('compared',0)} | {scored} / {population} | {c.get('prediction_failed',0)} |")
    for case in report['cases']:
        lines += ['', '## '+case['case_id'],'',
          '| Native family / declared role | Calls | Scored / unscored | Real mean us | Real P50 us | Sim us | Diff us | Tolerance | Passed / compared | Evidence / status |',
          '| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- |']
        for row in sorted(case['families'],key=lambda r:-r['observed_us']['mean']*r['observed_us']['count']):
            fmt=lambda v:'—' if v is None else f'{v:.3f}'
            prediction=row['predicted_us'] if row['predicted_us'] is not None else row.get('predicted_reference_us')
            tolerance='15 us' if row['observed_us']['mean']<=50 else '15%'
            if row['status']!='compared':tolerance+=' (unscored reference)' if prediction is not None else ' (unmodeled)'
            lines.append(f"| {row['native_operator_type']} / {row['declared_role'].replace('|',' + ')} | {row['observed_us']['count']} | "
                         f"{row['scored_event_count']} / {row['unscored_event_count']} | {fmt(row['observed_us']['mean'])} | "
                         f"{fmt(row['observed_us']['p50'])} | {fmt(prediction)} | {fmt(row['per_call_diff_us'] if row['per_call_diff_us'] is not None else row.get('reference_per_call_diff_us'))} | "
                         f"{tolerance} | {row['passed_cohort_count']} / {row['compared_cohort_count']} | {row['evidence_strength']} / {row['status']} |")
        source_groups = [group for row in case['families']
                         for group in row.get('conditional_source_role_references', ())]
        if source_groups:
            lines += ['', '### Conditional source-role program references', '',
                'Each row retains one homogeneous declared physical program set. These references lack complete observed-to-declared tensor equality and do not enter the strict cohort denominator. Their existing costs must not be added to the body again.', '',
                '| Native role / layer subset | Calls | Real mean / P50 us | Sim reference us | Real activity ms/forward | Predicted service ms/forward | Boundary |',
                '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
            for group in source_groups:
                layers=', '.join(map(str, group['layer_ids']))
                lines.append(f"| {group['native_operator_type']} / {group['declared_role']} / layers {layers} | {group['observed_us']['count']} | "
                    f"{group['observed_us']['mean']:.3f} / {group['observed_us']['p50']:.3f} | "
                    f"{fmt(group.get('predicted_reference_us'))} | {fmt(group.get('observed_activity_ms_per_forward'))} | "
                    f"{fmt(group.get('predicted_service_ms_per_forward'))} | {group['source_correspondence']['boundary_relation']} |")
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output-dir',type=Path,default=BASE)
    parser.add_argument('--case-id',action='append')
    parser.add_argument('--variant',action='append')
    parser.add_argument('--compare-timeout',type=float,default=120)
    args=parser.parse_args();before=prediction_runtime_identity();started=time.perf_counter();cases=[]
    prior_path=args.output_dir/'body-operator-family-scoreboard.json'
    previous=read(prior_path) if prior_path.exists() else None
    previous_identity=identity(prior_path) if previous else None
    previous_by_comparison={row['comparison_identity']['path']:row for row in previous['cases']} if previous else {}
    for actual_path in sorted(args.output_dir.glob('body-operator-*.actual.json')):
        actual=read(actual_path)
        if args.case_id and actual['case_id'] not in args.case_id:continue
        if args.variant and actual['variant'] not in args.variant:continue
        prefix=actual_path.with_name(actual_path.name.removesuffix('.actual.json'))
        mapping=read(prefix.with_suffix('.mapping.json'))
        comparison_path=prefix.with_suffix('.comparison.json')
        prior=previous_by_comparison.get(str(comparison_path))
        reusable=prior and identity(comparison_path)==prior['comparison_identity'] and identity(prefix.with_suffix('.case.json'))==prior['case_identity'] and identity(prefix.with_suffix('.mapping.json'))==prior['mapping_identity']
        if reusable:
            for path,value in previous['runtime_source_identity'].items():
                if '/mindie_sim/' in path and before.get(path)!=value:raise ValueError('cached_prediction_sim_runtime_changed')
            comparison=read(comparison_path)
        else:
            comparison=_compare_programs(args,prefix,mapping)
        references=program_references(prefix.with_suffix('.case.json'),mapping,actual)
        families=family_rows(actual,mapping,comparison,references)
        cases.append({'case_id':actual['case_id']+' / '+actual['variant'],'source_case_id':actual.get('source_case_id',actual['case_id']),
                      'variant':actual['variant'],'actual_identity':identity(actual_path),
                      'mapping_identity':identity(prefix.with_suffix('.mapping.json')),
                      'case_identity':identity(prefix.with_suffix('.case.json')),
                      'comparison_identity':identity(prefix.with_suffix('.comparison.json')),
                      'source_identity':actual['source_identity'],'forward_count':actual['forward_count'],
                      'geometry':actual['geometry'],'comparison_status_counts':comparison['status_counts'],
                      'passed_cohorts':sum(row['passed_cohort_count'] for row in families),'families':families})
        cases[-1]['strict_prediction_reused_from']=previous_identity if reusable else None
    after=prediction_runtime_identity()
    if before!=after:raise ValueError('prediction_runtime_changed')
    result={'schema_version':'mindie-body-operator-comparison/1',
            'status':'partial' if any(c['comparison_status_counts'].get('prediction_failed') for c in cases) else 'completed',
            'cases':cases,'accuracy_policy':accuracy_policy(),'runtime_source_identity':before,
            'coverage_status':'partial' if any(row['unscored_event_count'] for case in cases for row in case['families']) else 'complete',
            'runtime_sources_unchanged':True,'raw_capture_reads':0,'elapsed_seconds':round(time.perf_counter()-started,3)}
    write(args.output_dir/'body-operator-family-scoreboard.json',result)
    (args.output_dir/'body-operator-family-scoreboard.md').write_text(render(result))


if __name__=='__main__':main()
