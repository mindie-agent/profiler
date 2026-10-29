"""Compare pre-cache and cached MXFP4 builders on the same declared V4.1 work.

[Role] Independently check that immutable panel caching changes no physical cost.
[Invariants] Only the builder is replaced; source case, graph, hardware and Engine
  remain identical. This is a cache equivalence check, not a measured timing fit.
[Timeouts & Locks] One bounded representative up/down pair; git read timeout 10s.
[Side-Effect Policy] Read code and metadata; write one compact validation report.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource
import subprocess
import sys
import time
import types

from mindie_sim import operator_costs, target_graphs
from mindie_sim.prediction import mxfp4_grouped
from mindie_sim.prediction.mechanism import PlannedRecipe
from mindie_sim.prediction.program import RecipeBook
from mindie_sim.prediction.structure import parse_case
from mindie_sim.prediction.cost import CostModel
from mindie_sim.prediction.execution import Execution


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def identity(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha256(path.read_bytes()).hexdigest(),
            'size_bytes': path.stat().st_size}


def traced_execution(raw, op, builder):
    case = parse_case(raw)
    book = RecipeBook(families={'grouped_gemm': PlannedRecipe(builder)})
    execution = Execution(case, CostModel(case), recipes=book, trace_limit=30000)
    op, recipe = execution.prepare(op, 0)
    context = execution._context(op, 0, dict(op.metadata).get('graph_replay_scope', 'none'), recipe=recipe)
    engine = execution.engine
    ready = engine.submit('input_ready', release=7)
    done = execution.lower_program(context, recipe).start(engine, 'operator', ready)
    engine.advance(until=(done,))
    return {'completion_ms': done.time, 'serviced': dict(engine.serviced),
            'completed_tasks': engine.completed_count, 'trace': list(engine.trace),
            'live_tasks': engine.summary()['live_tasks'], 'remaining_buffers': dict(engine.allocated)}


def review(source_root, case_path, output):
    started = time.monotonic()
    previous = 'd1cd8436'
    file = 'mindie_sim/prediction/mxfp4_grouped.py'
    source = subprocess.run(['git', 'show', previous+':'+file], cwd=source_root,
                            capture_output=True, check=True, timeout=10).stdout
    module = types.ModuleType('mindie_sim.prediction._uncached_mxfp4_audit')
    module.__package__ = 'mindie_sim.prediction'
    sys.modules[module.__name__] = module
    exec(compile(source, previous+':'+file, 'exec'), module.__dict__)
    case_identity = identity(case_path)
    raw = json.loads(Path(case_path).read_text())
    graphs = target_graphs(raw, phase='decode', tokens=1, context=2048, sequences=1,
                           scope='body', resource_fusion=False)
    ops = tuple(op for op in graphs[0] if op.layer == 0 and op.family == 'grouped_gemm')
    del graphs
    if len(ops) != 2:
        raise ValueError('expected_independently_declared_layer0_expert_up_down')
    records = []
    for op in ops:
        old = operator_costs(raw, (op,), recipes=RecipeBook(families={
            'grouped_gemm': PlannedRecipe(module.build)}), input_ready_ms=7)['operators'][0]
        new = operator_costs(raw, (op,), recipes=RecipeBook(families={
            'grouped_gemm': PlannedRecipe(mxfp4_grouped.build)}), input_ready_ms=7)['operators'][0]
        repeated = operator_costs(raw, (op,), recipes=RecipeBook(families={
            'grouped_gemm': PlannedRecipe(mxfp4_grouped.build)}), input_ready_ms=7)['operators'][0]
        equal = old == new == repeated
        old_trace = traced_execution(raw, op, module.build)
        new_trace = traced_execution(raw, op, mxfp4_grouped.build)
        trace_equal = old_trace == new_trace
        records.append({'op_id': op.op_id, 'local_shape': op.local_shape,
                        'declared_group_rows': dict(op.metadata)['matrix_group_rows'],
                        'before_duration_ms': old['duration_ms'], 'after_duration_ms': new['duration_ms'],
                        'entire_operator_result_equal': equal,
                        'engine_execution_equal': trace_equal,
                        'engine_before_sha256': sha256(canonical(old_trace).encode()).hexdigest(),
                        'engine_after_sha256': sha256(canonical(new_trace).encode()).hexdigest(),
                        'completed_tasks': new_trace['completed_tasks'],
                        'retained_trace_events': len(new_trace['trace']),
                        'trace_capacity': 30000,
                        'before_result_sha256': sha256(canonical(old).encode()).hexdigest(),
                        'after_result_sha256': sha256(canonical(new).encode()).hexdigest(),
                        'reused_cache_result_sha256': sha256(canonical(repeated).encode()).hexdigest(),
                        'service_equal': old['serviced'] == new['serviced'] == repeated['serviced'],
                        'live_tasks': new['live_tasks'], 'remaining_buffers': new['remaining_buffers']})
    before = subprocess.run(['git', 'rev-parse', previous], cwd=source_root,
                            capture_output=True, check=True, text=True, timeout=10).stdout.strip()
    current = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=source_root,
                             capture_output=True, check=True, text=True, timeout=10).stdout.strip()
    maxrss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # resource.getrusage returns bytes on this host; retain raw units with platform evidence.
    report = {'schema_version': 'mindie-mxfp4-cache-equivalence/1',
              'status': 'passed' if all(row['entire_operator_result_equal'] and row['engine_execution_equal'] for row in records) else 'failed',
              'review_script_identity': identity(__file__),
              'before_builder_commit': before, 'after_commit': current,
              'before_builder_sha256': sha256(source).hexdigest(),
              'after_builder_identity': identity(Path(source_root)/file), 'case_identity': case_identity,
              'scope': 'same V4.1 source-symmetric q1/B1 layer0 expert up/down; builder-only A/B',
              'observed_timing_used': False, 'new_capture_reads': 0,
              'checks': ['entire public operator result including physical service, work and duration',
                         'repeat cached invocation preserves result and leaves no live tasks or buffers',
                         'independent Engine task count, retained trace, physical service and completion equality'],
              'records': records, 'elapsed_seconds': time.monotonic()-started,
              'maximum_resident_set_size_raw': maxrss, 'resource_api_platform': sys.platform}
    Path(output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','elapsed_seconds','maximum_resident_set_size_raw')}))
    if report['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--case', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    review(args.source_root, args.case, args.output)
