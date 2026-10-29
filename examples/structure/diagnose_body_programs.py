"""[Role] Inspect isolated program budgets for selected declared body layers.
[Invariants] Service sums are not body wall time; full DP participants are retained
  for joint collectives. Unpriced physical signatures remain explicit. Observed
  durations never select a program or alter hardware rates.
[Timeouts & Locks] One declared graph, a bounded set of layers, no runtime locks.
[Side-Effect Policy] Local source/case reads and one diagnostic JSON; no captures,
  device initialization, installation or remote execution.
"""
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
import argparse,json,subprocess,time
import mindie_sim
from mindie_sim.prediction.structure import parse_case
from mindie_sim.prediction.operator_analysis import target_graphs,operator_costs,physical_id
from mindie_sim.prediction.program import RecipeBook


def identity(path):
    path=Path(path);return {'path':str(path.resolve()),'sha256':sha256(path.read_bytes()).hexdigest(),'size_bytes':path.stat().st_size}


def runtime_identity():
    root=Path(mindie_sim.__file__).resolve().parent
    return {str(path):identity(path)['sha256'] for path in [*root.rglob('*.py'),*(root/'backends/profiles').glob('*.json')]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--layers',type=int,nargs='+',required=True);parser.add_argument('--tokens',type=int,default=1)
    parser.add_argument('--sequences',type=int,default=1);parser.add_argument('--context',type=int,default=32768)
    args=parser.parse_args();started=time.perf_counter();before=runtime_identity()
    case=parse_case(json.loads(args.case.read_text()));book=RecipeBook.from_mapping(case.runtime.kernels)
    graphs=target_graphs(case,phase='decode',tokens=args.tokens,sequences=args.sequences,context=args.context,scope='body')
    expanded={replica:tuple(op for op in book.expand(ops) if op.family!='barrier') for replica,ops in graphs.items()}
    replica=min(expanded)
    all_occurrences=Counter(physical_id(op) for op in expanded[replica]);all_identifiers=defaultdict(list)
    for op in expanded[replica]:all_identifiers[physical_id(op)].append(op.op_id)
    layers=[];priced={}
    for layer_id in args.layers:
        selected={replica:tuple(op for op in ops if op.layer==layer_id) for replica,ops in expanded.items()}
        result=operator_costs(case,selected,recipes=book)
        rows=[]
        for row in result['operators']:
            if row['replica']!=replica:continue
            ids=[op.op_id for op in selected[replica] if physical_id(op)==row['physical_id']]
            row={**row,'represented_operator_ids':ids}
            rows.append(row)
            old=priced.get(row['physical_id'])
            if old is not None and abs(old['duration_ms']-row['duration_ms'])>1e-10:
                raise ValueError('equivalent_physical_program_cost_changed')
            priced[row['physical_id']]=row
        layers.append({'layer_id':layer_id,'attention_kind':case.model.layer_plans[layer_id].attention,
            'ffn_kind':case.model.layer_plans[layer_id].ffn,'replica':replica,
            'isolated_program_sum_ms':sum(row['total_ms'] for row in rows),'operators':rows,
            'boundary':'sum_of_isolated_device_programs; not_layer_wall_clock',
            'joint_collective_scope':result.get('cross_dp_transport_isolation')})
        print(json.dumps({'layer_id':layer_id,'programs':len(rows),'service_sum_ms':layers[-1]['isolated_program_sum_ms']}),flush=True)
    coverage=[]
    for key,row in priced.items():
        coverage.append({'physical_id':key,'family':row['operator']['family'],'program':row['program'],
            'representative_operator_id':row['operator']['op_id'],'declared_operator_ids':all_identifiers[key],
            'declared_occurrences_per_forward':all_occurrences[key],'per_program_service_ms':row['duration_ms'],
            'covered_service_ms_per_forward':row['duration_ms']*all_occurrences[key],
            'serviced':row['serviced'],'communication':row.get('communication')})
    if before!=runtime_identity():raise ValueError('runtime_changed_during_diagnostic')
    root=Path(mindie_sim.__file__).resolve().parent.parent
    commit=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],text=True,capture_output=True,timeout=5,check=True).stdout.strip()
    output={'schema_version':'mindie-body-isolated-program-diagnostic/1','status':'completed',
        'case_identity':identity(args.case),'sim_git_commit':commit,'sim_module_path':str(Path(mindie_sim.__file__).resolve()),
        'runtime_source_identity':before,'runtime_sources_unchanged':True,'script_identity':identity(__file__),
        'geometry':{'phase':'decode','tokens_per_sequence':args.tokens,'sequences_per_replica':args.sequences,'context_tokens':args.context},
        'participating_replicas':list(expanded),'reported_replica':replica,'layers':layers,
        'covered_physical_programs':coverage,'covered_declared_occurrences':sum(all_occurrences[key] for key in priced),
        'total_declared_occurrences':sum(all_occurrences.values()),'raw_capture_reads':0,
        'elapsed_seconds':round(time.perf_counter()-started,3),'additional_budget_allowed':False,
        'limitations':['Isolated service sums do not reproduce body wall time or cross-program contention.',
            'A DP4 symmetric B1 declaration does not establish that all four replicas were active in the client-concurrency-one capture.',
            'Only signatures actually priced on the selected layers are extended to identical declared occurrences; remaining programs are unpriced.']}
    encoded=json.dumps(output,separators=(',',':'),allow_nan=False)+'\n'
    if len(encoded.encode())>32*1024**2:raise ValueError('diagnostic_output_exceeds_budget')
    args.output.write_text(encoded)


if __name__=='__main__':main()
