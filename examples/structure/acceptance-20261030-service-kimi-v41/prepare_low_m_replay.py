"""Prepare a current-runtime low-M arm with the known routing gap explicit.

[Role] Reuse source-specific retained service responses without refitting.
[Invariants] Low-M source routing is not claimed closed. Original populations and
  parameters remain unchanged; no high-M response is extrapolated into this arm.
[Timeouts & Locks] Small local metadata; no cost, raw capture reads or locks.
[Side-Effect Policy] Write a new eight-case arm while retaining the prior attempt.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNTIME = '3b72ea2d8f23ec102292b33aa57dada54cd4da45'

def identity(path):
    path=Path(path).resolve()
    return {'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest(),'size_bytes':path.stat().st_size}


def prepare():
    manifest=json.loads((HERE/'decode-forward-low-m-route-pending-cases.json').read_text())
    oracle_path=Path('/Users/maoxx241/code/sim-rewrite-20261027/data/verification/a5-bf16-grouped-regimes-20261030.json')
    oracle=json.loads(oracle_path.read_text())['source_mask_cursor_oracle']
    by_batch={r['valid_tokens']:r for r in oracle['rows']}
    output=HERE/'cases-low-m-3b72ea2d';output.mkdir(exist_ok=True)
    for row in manifest['cases']:
        old=Path(row['sim_case_path']);case=json.loads(old.read_text())
        source_evidence=case['runtime']['metadata']['calibration_evidence']
        batch=int(row['case_id'].split('_c')[1].split('_')[0])
        if batch not in (1,2,4,8):raise ValueError('not_low_m_population')
        limitation={'status':'known_declared_work_gap','source_contract_closed':False,
            'declared_rank0_expert_rows':[4,4],
            'source_compatible_rank0_expert_rows':by_batch[batch]['rank_expert_rows'][0],
            'source_oracle_identity':identity(oracle_path),'source_revision':oracle['revision'],
            'oracle_basis':oracle['basis'],
            'captured_group_list_values_observed':False,
            'interpretation':'This arm evaluates current generic declared work plus same-source observed call service. It does not establish the source masked-routing contract; the source-policy correction remains separate.'}
        source_evidence['known_routing_work_gap']=limitation
        source_evidence['parameter_domain']='This source and its exact physical shape; no c16/c32 grouped response is imported.'
        case['runtime']['metadata']['known_routing_work_gap']=limitation
        target=output/old.name;target.write_text(json.dumps(case,indent=2)+'\n')
        row.update(sim_case_path=str(target),model_declaration=identity(target),
            prior_source_case_identity=identity(old),variant_id='observable-service-low-m-known-route-gap-3b72ea2d',
            calibration_evidence=deepcopy(source_evidence))
        row.setdefault('scenario_evidence',{})['known_routing_work_gap']=limitation
        row.setdefault('replay_input_pins',{})['case']=identity(target)
    manifest.update(variant_id='observable-service-low-m-known-route-gap-3b72ea2d',
        runtime_plan={'source_commit':RUNTIME},
        comparison_scope='in_sample_observed_service_under_current_declared_work_with_explicit_routing_gap',
        not_new_live_collection=True,parameter_refits=0)
    path=HERE/'decode-forward-low-m-3b72ea2d-cases.json'
    path.write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(path),'cases':len(manifest['cases']),'parameter_refits':0}))


if __name__=='__main__':prepare()
