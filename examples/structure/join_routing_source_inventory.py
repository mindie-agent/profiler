"""Join retained routing PMU with the explicit source-operation inventory.

[Role] Extend the scalar/DMA ledger only with newly exported source counts.
[Invariants] Sort macros are not VBitSort/merge ISA counts. Three same-domain
  populations cannot identify independent correlated primitive prices.
[Timeouts & Locks] Bounded retained JSON and pure source arithmetic; no locks.
[Side-Effect Policy] Writes scalar-dma-routing-* only; no raw, costs or rates.
"""
from fractions import Fraction
from math import ceil
from pathlib import Path
import argparse
import json
import subprocess
import sys

from collect_scalar_dma_pmu import identity, read

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'data/observations/sources/arch3510-physical-services'


def matrix_rank(rows):
    """Exact rank for integer source-count coordinates, without a fit."""
    matrix=[[Fraction(value) for value in row] for row in rows]
    rank=0
    for col in range(len(matrix[0])):
        pivot=next((i for i in range(rank,len(matrix)) if matrix[i][col]),None)
        if pivot is None:continue
        matrix[rank],matrix[pivot]=matrix[pivot],matrix[rank]
        factor=matrix[rank][col];matrix[rank]=[v/factor for v in matrix[rank]]
        for i in range(len(matrix)):
            if i!=rank:
                factor=matrix[i][col]
                matrix[i]=[v-factor*p for v,p in zip(matrix[i],matrix[rank])]
        rank+=1
        if rank==len(matrix):break
    return rank


def count_features(assignments,active,experts):
    # These coordinates are only the source-level counts used for the rank
    # audit. Hardware opcodes/cache transactions remain unobserved.
    return {'intercept':1,'concat_blocks32':ceil(assignments/32),
            'sort_blocks32':ceil(assignments/32),'extract_blocks32':ceil(assignments/32),
            'count_gm_load32_all_owners':4*assignments-2*active,
            'inverse_gm_load32_all_owners':assignments,
            'inverse_gm_store32_all_owners':assignments,
            'atomic_copy_calls_all_owners':active,
            'atomic_payload_int32_all_owners':experts*active,
            'owner0_ub_getvalue':experts,'owner0_scalar_add':experts,
            'owner0_ub_setvalue':1,'owner0_pipe_v_barrier':1}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sim-source',type=Path,required=True)
    args=parser.parse_args();sys.path.insert(0,str(args.sim_source))
    from mindie_sim.prediction.moe_init_instructions import source_operations,diagnostics
    from mindie_sim.prediction.moe_init_mxfp8 import SOURCE
    modules=('mindie_sim/prediction/moe_init_instructions.py','mindie_sim/prediction/moe_init_mxfp8.py',
             'mindie_sim/prediction/instructions.py')
    pins={p:identity(args.sim_source/p) for p in modules}
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=args.sim_source,text=True,
                          capture_output=True,check=True,timeout=5).stdout.strip()
    prior_path=DEST/'scalar-dma-physical-constraints.json';prior=read(prior_path)
    records=[]
    for old in prior['records']:
        if old['native_operator_type']!='MoeInitRoutingV3':continue
        artifact=read(old['partition_identity']['path'])
        if identity(old['partition_identity']['path'])!=old['partition_identity']:
            raise ValueError('retained_routing_partition_changed')
        part=artifact['partitions'][old['partition_index']]
        abi=part['native_abi'];tokens,width=abi[2][0][0];topk=abi[2][1][0][1]
        experts=abi[3][2][0][0];assignments=tokens*topk;units=int(part['block_num'])
        if abi[2][0][1:]!=['bf16','ND'] or abi[3][0][1]!='fp8_e4m3' or width!=4096 or experts!=288:
            raise ValueError('routing_joint_domain_changed')
        per_owner=ceil(assignments/units);active=ceil(assignments/per_owner)
        sort,count,inverse=source_operations(assignments,per_owner,active,experts)
        exported=diagnostics(sort,count,inverse,experts=experts,declared_roles=())
        if old['source_instruction_counts']['count_simt_int32_loads_all_active_owners']!=sum(x.counts['source_simt_gm_load32'] for x in count):
            raise ValueError('old_and_new_source_count_disagree')
        features=count_features(assignments,active,experts)
        n=part['raw_pmu']['event_count']
        records.append({'case_id':old['source_case_id'],'source_identity':old['source_identity'],
            'partition_identity':old['partition_identity'],'partition_index':old['partition_index'],
            'native_abi':abi,'hardware':old['hardware'],'block_num':units,
            'forward_count':old['forward_count'],'calls':n,'calls_per_forward':n/old['forward_count'],
            'native_mean_p50_us':{k:part['raw_pmu']['fields']['Duration(us)']['statistics'][k] for k in ('mean','p50')},
            'pmu_fields':old['pmu'],'signed_boundary_diagnostics':old['diagnostics'],
            'conditional_source_geometry':{'tokens':tokens,'width':width,'topk':topk,'experts':experts,
                'assignments':assignments,'per_owner_rows':per_owner,'active_owners':active,
                'source_branch':'onecore_sort_GATHER_count_mode_full_range_useGatherCopy',
                'capture_binary_or_scalar_args_verified':False},
            'source_operation_export':exported,'count_features':features,
            'source_sort_api_macros_per_call':{'Concat':1,'Sort<float,true>':1,'Extract':1},
            'compiled_sort_opcodes_per_call':{'VBitSort32':None,'VMrgSort4V2':None},
            'source_atomic_boundary':{'DataCopyPad_calls':active,'INT32_payload_elements':experts*active,
                'shared_target_arrays':1,'atomic_cache_RMW_transactions':None},
            'owner0_scalar_boundary':{'GetValue_INT32':experts,'SetValue_INT32':1,'source_adds':experts,
                'PIPE_V_source_barriers':1,'loop_branch_address_ISA_counts':None},
            'not_a_per_core_observed_pmu':True,'response_use':'whole-call same-domain in-sample joint response; no opcode-level rate'} )
    records.sort(key=lambda r:r['conditional_source_geometry']['assignments'])
    names=list(records[0]['count_features']);matrix=[[r['count_features'][name] for name in names] for r in records]
    rank=matrix_rank(matrix)
    if any(identity(args.sim_source/p)!=pin for p,pin in pins.items()):raise ValueError('source_inventory_changed')
    output={'schema_version':'mindie-routing-source-operation-pmu-join/1','status':'completed',
        'source_commit':commit,'source_modules':pins,'source_provenance':SOURCE,
        'prior_scalar_dma_identity':identity(prior_path),'producer_identity':identity(__file__),
        'delta_from_prior': ['explicit whole-sort macro boundary and unobserved VBitSort/merge ISA counts',
            'per-owner SIMT count/inverse loads and stores','atomic-copy versus cache-RMW distinction',
            'owner0 SetValue and PIPE_V source barrier','same-domain exact feature rank'],
        'unchanged_prior_evidence':{'copy_joint_fits':len(prior['joint_response_fits']),
                                    'copy_fit_identity':identity(prior_path)},
        'records':records,'design':{'sample_count':len(records),'feature_names':names,'feature_matrix':matrix,
            'exact_rank':rank,'nullity':len(names)-rank,'remaining_fit_degrees_of_freedom':len(records)-rank,
            'basis':['1','assignments','active_owners'],
            'dependencies':['concat=sort=extract=assignments/32 in these three aligned domains',
                'count_loads=4*assignments-2*active_owners','inverse_loads=inverse_stores=assignments',
                'atomic_payload=288*active_owners','GetValue=ScalarAdd=288*intercept','SetValue=PIPE_V=intercept'],
            'interpretation':'Rank is geometric identifiability only, not an additive latency model. Three-point saturation leaves no validation degree of freedom; PMU owner aggregation and stage overlap remain unobserved.'},
        'usable_constraints':{'whole_native_response':'Three fully populated Mean/P50 points, each physical ABI and Block domain retained',
            'macro_scalar_simt_prices':'Only joint response constraints; no independent positive opcode prices inferred',
            'bounds':'Without an additive stage and owner mapping, a native elapsed or pipe-time ratio is not an upper/lower bound on one opcode latency',
            'needed_contrasts':['vary expert count E at fixed assignments,width,Block and source branch',
                'vary active owner split at fixed assignments and retain owner-specific PMU',
                'record compiled sort expansion or a standalone sort macro at multiple sizes',
                'retain SIMT warp/cache/atomic transactions and compare constant bytes with changed descriptor counts']},
        'new_raw_scans':0,'new_costs':0,'parameter_changes':[],'body_residual_used':False}
    path=DEST/'scalar-dma-routing-source-join.json';path.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    lines=['# Routing source-operation / PMU join','',
        'This increment reuses the existing six-source scalar/DMA ledger; only its three same-domain GLM MoeInitRoutingV3 populations need the new source-operation export. Copy fits and DSQ observations remain unchanged. No raw scan, prediction, or rate change occurs.','',
        '| Source | Calls/F | Assignments / active owners | Native Mean/P50 us | Vector / Scalar / MTE2 / MTE3 busy us |',
        '|---|---:|---:|---:|---:|']
    for r in records:
        g=r['conditional_source_geometry'];p=r['signed_boundary_diagnostics']['complete_numeric_mean_us'];o=r['native_mean_p50_us']
        values='/'.join(f"{p[k]:.3f}" for k in ('aiv_vec_time(us)','aiv_scalar_time(us)','aiv_mte2_time(us)','aiv_mte3_time(us)'))
        lines.append(f"| {r['case_id']} | {r['calls_per_forward']:.0f} | {g['assignments']} / {g['active_owners']} | {o['mean']:.3f}/{o['p50']:.3f} | {values} |")
    lines+=['',f'The 13 source-count features have exact rank {rank} on three independent capture domains. Sort/Concat/Extract blocks co-vary with assignments; owner-zero E288 loops are constant; atomic payload co-varies with active owners. A saturated three-point fit would have zero validation degrees of freedom. Repeated calls improve each measured mean but add no independent physical design point.', '',
        'VBitSort32 and VMrgSort4V2 are registered resource names; the actual source export deliberately retains one whole Sort macro and leaves SDK/compiled opcode expansion unknown. Logical SIMT INT32 accesses are not warp instructions or DCache misses. SetAtomicAdd plus a DataCopyPad payload is not a measured number of RMW transactions. Do not divide aggregate PMU fields by all-owner counts.', '',
        'The usable result is the complete per-domain native response plus source-count joint constraints. Separate rates need orthogonal E/assignment/owner/bytes contrasts and compiled/owner-specific observations. Signed differences between overlapping pipes remain diagnostics, not automatically synchronization or unmodeled latency.']
    path.with_suffix('.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'records':len(records),'calls':sum(r['calls'] for r in records),'features':len(names),'rank':rank,'source_commit':commit}))


if __name__=='__main__':main()
