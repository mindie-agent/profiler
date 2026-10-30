"""Reprice the complete Qwen3.5 TP4 INT32 caller evidence without raw scans.

[Role] Join retained native partitions to fresh typed Sim caller programs.
[Invariants] Routed capacities remain capacities; histograms and whole-layer
  counts are immutable. Source service references never enter strict accuracy.
[Timeouts & Locks] Sequential source workers, 180 s each; <=512 MiB; no locks.
[Side-Effect Policy] Read local pinned artifacts and write a separate cost arm.
"""
import argparse
from collections import Counter
import gc
from pathlib import Path
import subprocess
import sys
import time

from body_source_role_references import predict_source_role_references
from compare_body_operator_families import prediction_runtime_identity
from compare_kimi_native_partitions import peak_rss, render, verify_pin
from kimi_native_references import prepare_mc2_references
from qwen35_caller_contracts import audit_typed_chain, prepare
from replay_body_operator_families import identity, read, write


def runtime_identity():
    result = prediction_runtime_identity()
    for name in ('qwen35_caller_contracts.py', 'replay_qwen35_caller_contracts.py', 'kimi_native_references.py'):
        p = Path(__file__).with_name(name).resolve()
        result[str(p)] = identity(p)['sha256']
    return result


def worker(row, commit, strict_tensor_move=False):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    started = time.perf_counter(); before = runtime_identity()
    part_pin, case_pin = row['partition_identity'], row['case_identity']
    for pin in (part_pin, case_pin): verify_pin(pin)
    part = read(part_pin['path']); verify_pin(part['actual_identity'])
    actual = read(part['actual_identity']['path']); verify_pin(actual['body_acceptance_identity'])
    for k in ('source_identity', 'geometry', 'forward_count', 'body_acceptance_identity'):
        if actual[k] != part[k]: raise ValueError('partition_actual_population_differs:' + k)
    for kind in {p['native_operator_type'] for p in part['partitions']}:
        new = Counter(); old = Counter()
        for p in part['partitions']:
            if p['native_operator_type'] == kind: new.update(dict(p['duration_ns_counter']))
        for p in actual['families']:
            if p['native_operator_type'] == kind: old.update(dict(p['duration_ns_counter']))
        if new != old: raise ValueError('native_full_histogram_differs:' + kind)
    case = parse_case(read(case_pin['path'])); geo = part['geometry']
    manifest = export_structure(case, phase='decode', tokens=geo['tokens_per_sequence'],
        sequences=geo['sequences_per_replica'], context=actual['conditional_context_tokens'], scope='body')
    audit = audit_typed_chain(manifest)
    refs, failures, programs = prepare(part, manifest)
    combine, combine_failures, combine_programs = prepare_mc2_references(actual, manifest)
    refs.extend(combine); failures.extend(combine_failures); programs.update(combine_programs)
    # An independently verified strict supplement may own the FFN copy buckets.
    # Its exact partition indices, not a name-only filter, define this exclusion.
    superseded = []
    if strict_tensor_move:
        proof = row['strict_partition_proof']; verify_pin(proof)
        selected = read(proof['path'])
        if selected['partition_identity'] != part_pin: raise ValueError('strict_partition_proof_source_differs')
        indices = set(selected['strict_partition_indices'])
        superseded = [r for r in refs if r.get('partition_index') in indices]
        refs = [r for r in refs if r.get('partition_index') not in indices]
        failures = [r for r in failures if r.get('partition_index') not in indices]
    used = {b['program_set_key'] for g in refs for b in g['program_buckets']}
    programs = {k: v for k, v in programs.items() if k in used}
    context = {}; selected_nodes = {}
    for group in refs:
        for bucket in group['program_buckets']: context.setdefault(bucket['program_set_key'], group)
    pricing = []
    for key, program in programs.items():
        group = context[key]
        selected_nodes.update({n['node_id']: n for n in program['nodes']})
        pricing.append({k: v for k, v in program.items() if k != 'nodes'} | {
            'observed_us': group['observed_us'], 'observed_activity_sum_ns': group['observed_activity_sum_ns']})
    compact = {k: manifest[k] for k in ('schema_version', 'graph_id', 'execution')}
    compact['nodes'] = list(selected_nodes.values())
    combine_count = sum(g['observed_us']['count'] for g in combine) + sum(g['event_count'] for g in combine_failures)
    del manifest, actual, selected_nodes
    gc.collect()
    costs = {g['program_set_key']: g for g in predict_source_role_references(case, compact,
        {'source_role_references': pricing, 'forward_count': part['forward_count']})}
    results = []
    for group in refs:
        count = group['observed_us']['count']; forwards = part['forward_count']; buckets = []
        for bucket in group['program_buckets']:
            key = bucket['program_set_key']; cost = costs[key]
            if cost['prediction_status'] != 'reference_only': raise ValueError('source_reference_prediction_failed:' + key)
            buckets.append({**bucket, **{k: v for k, v in programs[key].items() if k not in ('nodes','program_set_key')},
                'predicted_reference_us': cost['predicted_reference_us'], 'declared_programs': cost['declared_programs'],
                'reference_boundary': cost['boundary']})
        if sum(b['event_count'] for b in buckets) != count: raise ValueError('native_call_multiplicity_differs')
        predicted = sum(b['event_count'] * b['predicted_reference_us'] for b in buckets) / count
        observed_ms = group['observed_activity_sum_ns'] / 1e6 / forwards
        limits = sorted({v for b in buckets for v in b['source_correspondence']['limitations']})
        results.append({**group, 'program_buckets': buckets, 'prediction_status': 'reference_only',
            'reference_boundary': buckets[0]['source_correspondence']['boundary_relation'],
            'physical_program_signatures': [b['physical_program_signatures'] for b in buckets],
            'source_correspondence': {'observed_native_tensor_contract': group['native_abi'],
                'boundary_relation': buckets[0]['source_correspondence']['boundary_relation'],
                'program_weight_basis': 'exact_captured_layer_counts', 'limitations': limits,
                'partial_work_boundary': any(b['source_correspondence'].get('partial_work_boundary',False) for b in buckets)},
            'predicted_reference_us': predicted, 'calls_per_forward': count/forwards,
            'observed_activity_ms_per_forward': observed_ms,
            'predicted_service_ms_per_forward': predicted*count/1000/forwards,
            'reference_activity_error_ms_per_forward': predicted*count/1000/forwards-observed_ms,
            'per_call_reference_diff_us': predicted-group['observed_us']['mean'],
            'accuracy_status': 'reference_only', 'strict_accuracy_pass': None,
            'conditions': limits})
    for pin in (part_pin, case_pin, part['actual_identity'], part['body_acceptance_identity']): verify_pin(pin)
    if runtime_identity() != before: raise ValueError('runtime_changed')
    rss = peak_rss()
    if rss > 512*1024**2: raise MemoryError('qwen35_reference_exceeds_512_MiB')
    return {'schema_version': 'mindie-native-body-reference/1', 'case_id': part['source_case_id'],
        'status': 'partial' if failures else 'completed', 'partition_identity': part_pin,
        'actual_identity': part['actual_identity'], 'case_identity': case_pin,
        'original_case_identity': part['case_identity'], 'source_identity': part['source_identity'],
        'body_acceptance_identity': part['body_acceptance_identity'], 'geometry': geo,
        'forward_count': part['forward_count'], 'conditional_context_tokens': compact['execution']['context'],
        'native_event_count': part['native_event_count']+combine_count,
        'referenced_event_count': sum(g['observed_us']['count'] for g in results),
        'typed_caller_audit': audit, 'groups': results, 'unresolved': failures,
        'strict_superseded_partitions': superseded, 'strict_compared': 0,
        'fresh_graph_id': compact['graph_id'], 'runtime_source_commit': commit,
        'runtime_source_identity': before, 'runtime_sources_unchanged': True,
        'execution': {'new_program_sets': len(programs), 'raw_capture_reads': 0, 'old_prediction_reused': False,
            'elapsed_seconds': time.perf_counter()-started, 'maximum_resident_set_size_bytes': rss}}


def render_qwen35(report):
    return render(report).replace('Kimi complete','Qwen3.5 typed caller').replace(
        'Heterogeneous AttnRes source flags use captured layer call counts; no per-layer measured P50 is invented.',
        'Captured layer counts weight fresh source programs; no per-layer measured P50 is invented. TopK is a partial-work boundary: its observed third FP32 output is not modeled.')


def complete_saved_schema(path):
    """Add required boundary metadata to saved costs without re-executing them."""
    before = identity(path); report = read(path)
    producer = identity(Path(__file__))
    for case in report['cases']:
        for group in case['groups']:
            group['reference_boundary'] = group['source_correspondence']['boundary_relation']
        detail = path.parent/(case['case_id']+'-references.json')
        saved = read(detail)
        for group in saved['groups']:
            group['reference_boundary'] = group['source_correspondence']['boundary_relation']
        if saved != case: raise ValueError('saved_reference_case_differs_before_metadata_completion')
        write(detail, saved)
    report['metadata_completion'] = {
        'pre_completion_content_sha256': before['sha256'], 'producer_identity': producer,
        'changed_fields': ['groups[].reference_boundary', 'markdown_boundary_description'],
        'numeric_costs_and_histograms_unchanged': True, 'cost_executions': 0, 'raw_capture_reads': 0,
        'executed_cost_runtime_source_identity_preserved': True}
    write(path, report); path.with_suffix('.md').write_text(render_qwen35(report))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--runtime-source-commit',required=True);p.add_argument('--worker-index',type=int)
    p.add_argument('--strict-tensor-move',action='store_true');p.add_argument('--timeout',type=float,default=180)
    a=p.parse_args(); a.output_dir.mkdir(parents=True,exist_ok=True); rows=read(a.inputs)['cases']
    if a.worker_index is not None:
        row=rows[a.worker_index];r=worker(row,a.runtime_source_commit,a.strict_tensor_move)
        write(a.output_dir/(r['case_id']+'-references.json'),r);return
    before=runtime_identity(); pin=identity(a.inputs); cases=[];start=time.perf_counter()
    for i,row in enumerate(rows):
        command=[sys.executable,str(Path(__file__).resolve()),'--inputs',str(a.inputs.resolve()),
            '--output-dir',str(a.output_dir.resolve()),'--runtime-source-commit',a.runtime_source_commit,'--worker-index',str(i)]
        if a.strict_tensor_move:command.append('--strict-tensor-move')
        try:
            r=subprocess.run(command,capture_output=True,text=True,timeout=a.timeout)
            (a.output_dir/(row['case_id']+'.run.log')).write_text(r.stdout+r.stderr)
            if r.returncode:raise RuntimeError(r.stderr[-4000:])
            case=read(a.output_dir/(row['case_id']+'-references.json'))
        except (subprocess.TimeoutExpired,RuntimeError) as error:
            case={'case_id':row['case_id'],'status':'failed','reason':str(error)}
        cases.append(case);print(row['case_id'],case['status'],flush=True)
    verify_pin(pin)
    if runtime_identity()!=before:raise ValueError('batch_runtime_changed')
    result={'schema_version':'mindie-native-body-reference-batch/1','input_identity':pin,
        'runtime_source_commit':a.runtime_source_commit,'runtime_source_identity':before,'cases':cases,
        'elapsed_seconds':time.perf_counter()-start,'raw_capture_reads':0,'strict_compared':0}
    write(a.output_dir/'qwen35-native-reference-scoreboard.json',result)
    (a.output_dir/'qwen35-native-reference-scoreboard.md').write_text(render_qwen35(result))
    if any(c['status']=='failed' for c in cases):raise SystemExit(1)


if __name__=='__main__':main()
