"""Rebind intact native cohorts when only their declared execution boundary changes.

[Role] Preserve complete observed tensor groups across source fusion selection.
[Invariants] Candidate IDs, normalized contract, scope, placement and full semantic
  membership stay identical. A one-kernel fusion must own exactly those members.
  Timing is copied unchanged and never selects a new candidate or physical work.
[Timeouts & Locks] Bounded manifest/retained metadata, no cost or raw capture reads.
[Side-Effect Policy] New mapping/proof only; no mutation of old observations.
"""
import argparse
from hashlib import sha256
from pathlib import Path

from reprice_body_operator_families import (
    _observation, canonical, fresh_structure, rebind_mapping,
)
from replay_body_operator_families import RoleMapper, read, write
from mindie_profiler.structure_cohorts import CohortAccumulator
from mindie_profiler.structure_mapping import _freeze
from mindie_sim.cohort_comparison import _check_cohort


def rebind_complete_fusions(mapping, manifest, source):
    rebound, plan = rebind_mapping(mapping, manifest, source)
    mapper = RoleMapper(manifest, mapping_limit=0, phase=manifest['execution']['phase'])
    resources = {r['node_id']: r for r in manifest['resource_operators']}
    targets = mapper.target_index.all
    proofs = []
    allowed = {r['old_cohort_id'] for r in plan['excluded']
               if r['reason'] == 'aggregate_resource_boundary_changed'}
    for old_window, window in zip(mapping['windows'], rebound['windows']):
        observation = _observation(old_window, source)
        accumulator = CohortAccumulator(manifest['graph_id'], mapper.target_index, observation,
                                        execution=manifest['execution'])
        for old in old_window['cohorts']:
            # HcPost has a complete retained input/output tensor population.
            # HcPre's optional coefficients and routed GMM active rows need
            # separate evidence; their old reference status is not promoted.
            if (old['cohort_id'] not in allowed or old['target_kind'] != 'subgraph'
                    or old['native_operator_type'] != 'HcPost'
                    or old['contract'][0] != 'hyper_connection_active'):
                continue
            roles = mapping['conditional_role_by_cohort_id'][old['cohort_id']]
            fresh, reason = accumulator._cohort(old['target_ids'])
            if reason or fresh['target_kind'] != 'subgraph':
                continue
            invariant_fields = ('contract','contract_scope','target_kind','placement','replica','stage',
                                'phase','structural_classification','declared_instance_count')
            if any(canonical(old.get(k)) != canonical(fresh.get(k)) for k in invariant_fields):
                continue
            local_proofs = []
            for target_id in old['target_ids']:
                target = targets[target_id]
                boundary = target.get('resource_boundary') or {}
                ids = boundary.get('operator_ids', [])
                if (target.get('coverage', {}).get('kind') != 'complete_subgraph'
                        or boundary.get('kind') != 'selected_native_fusion'
                        or boundary.get('native', {}).get('native_kind') != old['native_operator_type']
                        or boundary.get('submitted_kernels') != 1 or len(ids) != 1):
                    break
                resource = resources[ids[0]]
                semantic = resource['operator']['metadata'].get('fusion_semantic_ids', [])
                members = [x.split('/', 1)[1] for x in target['node_ids']]
                if sorted(semantic) != sorted(members) or _freeze(target['contract']) != _freeze(old['contract']):
                    break
                local_proofs.append({'target_id':target_id,'resource_id':ids[0],
                    'semantic_members':target['node_ids'], 'physical_signature':resource['physical_signature']})
            if len(local_proofs) != len(old['target_ids']):
                continue
            key = (old['native_operator_type'], old['device_id'], tuple(sorted(old['target_ids'])))
            cohort_id = 'sha256:' + sha256(canonical((manifest['graph_id'], observation.rank_id, key)).encode()).hexdigest()
            row = {**old, **fresh, 'cohort_id':cohort_id}
            _check_cohort(row, old_window, manifest, targets)
            window['cohorts'].append(row)
            rebound['conditional_role_by_cohort_id'][cohort_id] = roles
            excluded_key = 'rebind:aggregate_resource_boundary_changed'
            window['cohort_excluded_event_counts'][excluded_key] -= old['event_count']
            if not window['cohort_excluded_event_counts'][excluded_key]:
                del window['cohort_excluded_event_counts'][excluded_key]
            proofs.append({'old_cohort_id':old['cohort_id'],'cohort_id':cohort_id,
                'native_operator_type':old['native_operator_type'],'event_count':old['event_count'],
                'contract':old['contract'],'contract_scope':old['contract_scope'],
                'candidate_set_unchanged':True,'observed_timing_unchanged':True,
                'complete_single_native_resource_proofs':local_proofs})
    restored = {p['old_cohort_id'] for p in proofs}
    rebound['cohort_event_window_count'] = sum(c['event_count'] for w in rebound['windows'] for c in w['cohorts'])
    rebound['resource_rebind_evidence'] = {'basis':'complete_tensor_contract_and_exact_semantic_fusion_members',
        'source_graph_id':mapping['graph_id'],'proofs':proofs,
        'remaining_exclusions':[r for r in plan['excluded'] if r['old_cohort_id'] not in restored],
        'raw_capture_reads':0,'capture_binary_identity_implied':False}
    return rebound


def main():
    p=argparse.ArgumentParser();p.add_argument('--mapping',type=Path,required=True)
    p.add_argument('--actual',type=Path,required=True);p.add_argument('--case',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    mapping=read(a.mapping);actual=read(a.actual)
    result=rebind_complete_fusions(mapping,fresh_structure(a.case,mapping),actual['source_identity'])
    a.output.parent.mkdir(parents=True,exist_ok=True);write(a.output,result)

if __name__=='__main__':main()
