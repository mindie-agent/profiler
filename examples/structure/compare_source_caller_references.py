"""Replay retained caller/HCCL populations against explicit source programs.

[Role] Independent reference entry point reusing shared Sim frontend and pricing.
[Invariants] No raw capture scan, timing fit, fabricated ABI or strict upgrade.
  Source, case and program identities are pinned; failed populations stay visible.
[Timeouts & Locks] Sequential bounded child per source, 180s, RSS <=512 MiB.
[Side-Effect Policy] Reads local retained artifacts and writes separate reports.
"""
from __future__ import annotations
import argparse
import gc
from pathlib import Path
import subprocess
import sys
import time

from body_source_role_references import predict_source_role_references
from compare_body_operator_families import prediction_runtime_identity
from compare_glm_native_partitions import peak_rss
from replay_body_operator_families import identity, read, write
from source_caller_references import prepare_callers, prepare_hccl


def runtime_identity():
    result = prediction_runtime_identity()
    for name in ('source_caller_references.py','compare_source_caller_references.py'):
        p = Path(__file__).with_name(name).resolve(); result[str(p)] = identity(p)['sha256']
    return result


def verify(pin):
    now = identity(pin['path'])
    if any(now[k] != pin[k] for k in ('sha256','size_bytes')):
        raise ValueError('retained_input_changed:' + pin['path'])


def worker(row, runtime_commit):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    started = time.perf_counter(); before = runtime_identity()
    for key in ('retained_identity','case_identity'):
        verify(row[key])
    retained = read(row['retained_identity']['path'])
    original_case_pin = retained['case_identity']; verify(original_case_pin)
    if retained.get('body_acceptance_identity'):
        verify(retained['body_acceptance_identity'])
    selected_raw = read(row['case_identity']['path'])
    original_raw = read(original_case_pin['path'])
    case = parse_case(selected_raw); original = parse_case(original_raw)
    if (case.model.to_dict() != original.model.to_dict() or case.machine != original.machine
            or case.runtime.parallel != original.runtime.parallel):
        raise ValueError('caller_arm_changes_model_hardware_parallel')
    geo = retained['geometry']
    context = row['conditional_context_tokens']
    original_kernels = original.runtime.kernels
    del original, original_raw, selected_raw
    manifest = export_structure(case,phase='decode',tokens=geo['tokens_per_sequence'],
        sequences=geo['sequences_per_replica'],context=context,scope='body')
    prepare = prepare_hccl if row['retained_kind']=='hccl_ledger' else prepare_callers
    refs, failures, cost_inputs, compact = prepare(retained,manifest)
    del manifest; gc.collect()
    predictions = predict_source_role_references(case,compact,{
        'source_role_references':cost_inputs,'forward_count':retained['forward_count']})
    costs = {p['program_set_key']:p for p in predictions}; groups=[]
    for r in refs:
        duration = sum(costs[c['program_set_key']]['predicted_reference_us']*c['weight'] for c in r['cost_components'])
        measured = r['observed_us']['mean'];count=r['observed_us']['count'];f=retained['forward_count']
        groups.append({**r,'prediction_status':'reference_only','predicted_reference_us':duration,
            'reference_boundary':'complete_explicit_source_program_composition',
            'physical_program_signatures':[s for component in r['cost_components'] for cg in cost_inputs if cg['program_set_key']==component['program_set_key'] for s in cg['physical_program_signatures']],
            'declared_programs':[{'program_set_key':c['program_set_key'],'per_native_call_weight':c['weight'],
                'programs':costs[c['program_set_key']]['declared_programs'],
                'predicted_program_set_us':costs[c['program_set_key']]['predicted_reference_us']} for c in r['cost_components']],
            'calls_per_forward':count/f,'observed_activity_ms_per_forward':r['observed_activity_sum_ns']/1e6/f,
            'predicted_service_ms_per_forward':duration*count/1000/f,
            'reference_activity_error_ms_per_forward':(duration-measured)*count/1000/f,
            'per_call_reference_diff_us':duration-measured})
    for key in ('retained_identity','case_identity'):
        verify(row[key])
    if runtime_identity()!=before:raise ValueError('runtime_changed_during_reference')
    rss=peak_rss()
    if rss>512*1024**2:raise MemoryError('source_caller_reference_exceeds_512_MiB')
    return {'schema_version':'mindie-native-body-reference/1','status':'partial' if failures else 'completed',
        'case_id':row['case_id'],'variant':'explicit_source_caller_reference',
        'source_identity':retained['source_identity'],'actual_identity':row['retained_identity'],
        'partition_identity':row['retained_identity'],'retained_identity':row['retained_identity'],'body_acceptance_identity':retained.get('body_acceptance_identity'),
        'case_identity':row['case_identity'],'original_case_identity':original_case_pin,
        'declaration_changes':{'runtime.kernels':{'original':original_kernels,'selected':case.runtime.kernels}},
        'geometry':geo,'conditional_context_tokens':context,'forward_count':retained['forward_count'],
        'source_forward_count':retained.get('source_forward_count',retained['forward_count']),
        'native_event_count':sum(g['observed_us']['count'] for g in groups)+sum(g['event_count'] for g in failures),
        'referenced_event_count':sum(g['observed_us']['count'] for g in groups),
        'groups':groups,'unresolved':failures,'strict_compared':0,
        'runtime_source_commit':runtime_commit,'runtime_source_identity':before,'runtime_sources_unchanged':True,
        'execution':{'new_program_sets':len(cost_inputs),'raw_capture_reads':0,'old_prediction_reused':False,
            'elapsed_seconds':time.perf_counter()-started,'maximum_resident_set_size_bytes':rss}}


def render(report):
    lines=['# Source caller and explicit HCCL conditional references','',
        'All rows remain source-symbol conditional references. Native tensor ABI, valid routing values and captured HCCL template are not invented.',
        'Copy gather/scatter remain pooled; zero-fill/convolution are outside their cost. Controllers never add to HCOM elapsed.','',
        '| Source / native / role | Calls/F | Real Mean / P50 us | Sim us/call | Signed activity residual ms/F |',
        '| --- | ---: | ---: | ---: | ---: |']
    for case in report['cases']:
        if case['status']=='failed':
            lines.append(f"| {case['case_id']} | failed | {case['reason']} | — | — |");continue
        for g in case['groups']:
            lines.append(f"| {case['case_id']} / {g['native_operator_type']} / {g['declared_role']} | {g['calls_per_forward']:.2f} | {g['observed_us']['mean']:.6f} / {g['observed_us']['p50']:.6f} | {g['predicted_reference_us']:.6f} | {g['reference_activity_error_ms_per_forward']:+.6f} |")
        for g in case['unresolved']:
            lines.append(f"| {case['case_id']} / {g['native_operator_type']} | {g['event_count']} calls unresolved | {g['reason']} | — | — |")
    lines+=['','Residuals compare event activity to source service. They must not be summed into Body wall time.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--runtime-source-commit',required=True)
    p.add_argument('--worker-index',type=int);p.add_argument('--timeout',type=float,default=180)
    args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    rows=read(args.inputs)['cases']
    if args.worker_index is not None:
        row=rows[args.worker_index];result=worker(row,args.runtime_source_commit)
        write(args.output_dir/(row['case_id']+'-references.json'),result);return
    pin=identity(args.inputs);before=runtime_identity();start=time.perf_counter();cases=[]
    for i,row in enumerate(rows):
        command=[sys.executable,str(Path(__file__).resolve()),'--inputs',str(args.inputs.resolve()),
            '--output-dir',str(args.output_dir.resolve()),'--runtime-source-commit',args.runtime_source_commit,'--worker-index',str(i)]
        try:
            attempt=subprocess.run(command,capture_output=True,text=True,timeout=args.timeout)
            (args.output_dir/(row['case_id']+'.run.log')).write_text(attempt.stdout+attempt.stderr)
            if attempt.returncode:
                case={'case_id':row['case_id'],'status':'failed','reason':attempt.stderr[-3000:]}
            else:case=read(args.output_dir/(row['case_id']+'-references.json'))
        except subprocess.TimeoutExpired as error:
            case={'case_id':row['case_id'],'status':'failed','reason':str(error)}
        cases.append(case);print(row['case_id'],case['status'],flush=True)
    if identity(args.inputs)!=pin or before!=runtime_identity():raise ValueError('batch_inputs_or_runtime_changed')
    result={'schema_version':'mindie-native-body-reference-batch/1','runtime_source_commit':args.runtime_source_commit,
        'input_identity':pin,'cases':cases,'strict_compared':0,'runtime_source_identity':before,
        'execution':{'elapsed_seconds':time.perf_counter()-start,'raw_capture_reads':0,'old_prediction_reused':False,
            'maximum_resident_set_size_bytes':max([peak_rss()]+[c.get('execution',{}).get('maximum_resident_set_size_bytes',0) for c in cases])}}
    write(args.output_dir/'source-caller-reference-scoreboard.json',result)
    (args.output_dir/'source-caller-reference-scoreboard.md').write_text(render(result))

if __name__=='__main__':main()
