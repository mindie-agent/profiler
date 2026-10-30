"""Complete HcPost timing stays strict through a validated native resource boundary."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples/structure'))


def test_real_hcpost_contract_and_members_rebind_without_timing_or_partial_promotion():
    pytest.importorskip('mindie_sim')
    from rebind_complete_fusion_cohorts import rebind_complete_fusions
    from reprice_body_operator_families import fresh_structure
    inputs=json.loads((ROOT/'examples/structure/acceptance-20261030-operator-service-refresh/inputs.json').read_text())
    row=next(r for r in inputs['cases'] if r['case_id'].endswith('c4-livepre'))
    mapping=json.loads(Path(row['mapping_identity']['path']).read_text())
    fresh=fresh_structure(row['selected_case_identity']['path'],mapping)
    output=rebind_complete_fusions(mapping,fresh,row['source_identity'])
    proofs=output['resource_rebind_evidence']['proofs']
    assert len(proofs)==2 and sum(p['event_count'] for p in proofs)==4140
    assert all(p['native_operator_type']=='HcPost' and len(p['complete_single_native_resource_proofs'])==45 for p in proofs)
    original={c['cohort_id']:c for w in mapping['windows'] for c in w['cohorts']}
    current={c['cohort_id']:c for w in output['windows'] for c in w['cohorts']}
    for proof in proofs:
        old,new=original[proof['old_cohort_id']],current[proof['cohort_id']]
        for key in ('event_count','duration_ns','complete_activity_sum_ns','contract','target_ids'):
            assert new[key]==old[key]
    assert {r['native_operator_type'] for r in output['resource_rebind_evidence']['remaining_exclusions']}=={'HcPre','GroupedMatmulSwigluQuant'}
    # The positive proof is complete; mutate the same declaration for the
    # negative case instead of retaining a second full 45-layer manifest.
    invalid=fresh
    target=proofs[0]['complete_single_native_resource_proofs'][0]['resource_id']
    next(r for r in invalid['resource_operators'] if r['node_id']==target)['operator']['metadata']['fusion_semantic_ids']=[]
    invalid['graph_id']='sha256:'+sha256(json.dumps({k:v for k,v in invalid.items() if k not in {'graph_id','source'}},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    rejected=rebind_complete_fusions(mapping,invalid,row['source_identity'])
    assert len(rejected['resource_rebind_evidence']['proofs'])==1


def test_same_graph_new_engine_cost_receipt_is_reviewed_as_unchanged_population(tmp_path):
    from review_repriced_body_operators import review
    source=ROOT/'examples/structure/acceptance-20261030-operator-service-refresh/complete-hcpost/glm53flash-a3-tp16-c4-livepre/body-operator-family-scoreboard.json'
    (tmp_path/source.name).write_bytes(source.read_bytes())
    review(tmp_path)
    result=json.loads((tmp_path/'body-operator-reprice-independent-review.json').read_text())
    assert result['status']=='passed' and result['counts']['strict_events']==23506
    assert result['counts']['compared']==21
