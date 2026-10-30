"""Run explicit retained-source operator refreshes with their current Body case.

[Role] Queue independent fresh Engine cohort costs from a saved input selection.
[Invariants] Input order/identity, complete family populations and failed attempts
  remain visible; no raw reads or old predictions, no error-based selection.
[Timeouts & Locks] Serial program workers use the existing 120s budget; the
  source budget sums retained cohort budgets plus 180s metadata/cleanup allowance.
[Side-Effect Policy] New local reports/logs only, no runtime/case mutations.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',type=Path,required=True)
    p.add_argument('--case-id',action='append',required=True);p.add_argument('--output-dir',type=Path,required=True)
    args=p.parse_args();inputs=json.loads(args.inputs.read_text()); attempts=[]
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for case_id in args.case_id:
        row,=[r for r in inputs['cases'] if r['case_id']==case_id]
        for key in ('actual_identity','mapping_identity','selected_case_identity'):
            pin=row[key]
            if sha256(Path(pin['path']).read_bytes()).hexdigest()!=pin['sha256']:
                raise ValueError('selected_input_changed:'+key+':'+case_id)
        mapping=json.loads(Path(row['mapping_identity']['path']).read_text())
        budget=120*sum(len(w['cohorts']) for w in mapping['windows'])+180
        out=args.output_dir/case_id;out.mkdir(exist_ok=True)
        cmd=[sys.executable,str(Path(__file__).with_name('reprice_body_operator_families.py')),
             '--actual',row['actual_identity']['path'],'--mapping',row['mapping_identity']['path'],
             '--case',row['selected_case_identity']['path'],'--output-dir',str(out),
             '--variant','executed-service-21c30821','--runtime-source-commit',inputs['runtime_source_commit'],
             '--skip-references']
        started=time.perf_counter()
        with (out/'execution.log').open('w') as log:
            try:
                result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=budget)
                status='completed' if result.returncode==0 else 'failed';code=result.returncode
            except subprocess.TimeoutExpired:
                status='timed_out';code=None
        attempts.append({'case_id':case_id,'command':cmd,'status':status,'returncode':code,
                         'source_timeout_seconds':budget,'elapsed_seconds':time.perf_counter()-started})
        (args.output_dir/('queue-'+args.case_id[0]+'.json')).write_text(json.dumps({
            'input_path':str(args.inputs),'input_sha256':sha256(args.inputs.read_bytes()).hexdigest(),
            'attempts':attempts,'raw_capture_reads':0},indent=2)+'\n')
        print(json.dumps(attempts[-1]),flush=True)
        if status!='completed':raise SystemExit('operator_refresh_failed; see retained log')

if __name__=='__main__':main()
