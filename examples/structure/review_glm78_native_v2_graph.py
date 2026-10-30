"""Audit GLM78 native V2 boundaries against retained complete tensor evidence.

[Role] Independently verify all declared MoE layers, typed links and TP scopes.
[Invariants] Native capacity is not valid work. Controlled comparison removes
  only native_moe_protocol; source compatibility is not binary equivalence.
[Timeouts & Locks] Bounded metadata graphs and retained JSON only; no locks.
[Side-Effect Policy] Write a compact review; no Engine, raw CSV, device or cost.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json, resource, sys, time
from pathlib import Path
ROOT=Path('/Users/maoxx241/code/profiler'); FIXED=Path('/tmp/mindie-sim-cohort-wave6-20261029')
sys.path.insert(0,str(ROOT/'examples/structure'))
from build_qwen_a3_service_cases import physical_ops,read,identity
from check_glm78_native_v2 import check_retained_v2
start=time.monotonic(); checks=0; failures=[]; rows=[]
def check(c,n):
 global checks
 checks+=1
 if not c: failures.append(n)
def normalized_operation(op):
 value=asdict(op)
 # The MLA fusion stores the entire recipe book. Ignore only the one
 # deliberately switched flag in this controlled metadata comparison.
 metadata=dict(value['metadata'])
 if 'fusion_recipe_configuration' in metadata:
  configuration=dict(metadata['fusion_recipe_configuration'])
  configuration.pop('native_moe_protocol',None)
  metadata['fusion_recipe_configuration']=configuration
 value['metadata']=metadata
 return value
for suffix,B in [('30_c2',2),('50_c2',2),('88_c8',8)]:
 cp=FIXED/f'examples/cases/high-concurrency-20261030/glm78-capture-rows/a3_glm53_w4a8_tp16_tpot{suffix}.json'
 rp=ROOT/f'examples/structure/acceptance-20261030-service-qwen-a3/glm78-native/a3_glm53_w4a8_tp16_tpot{suffix}-native-partitions.json'
 raw=read(cp); retained=read(rp); checked=check_retained_v2(retained,tp=16,ep=16,hidden=6144,experts=256)
 geometry={'query_rows':6*B,'tokens_per_sequence':6,'sequences_per_replica':B,'context_tokens':4096}
 case,ops=physical_ops(raw,geometry); old=deepcopy(raw); old['runtime']['kernels'].pop('native_moe_protocol')
 _,before=physical_ops(old,geometry); by={o.op_id:o for o in ops}; oldby={o.op_id:o for o in before}
 g=checked['source_caller_geometry']; M=g['global_query_rows']; local=g['tp_local_rows']; cap=g['expert_buffer_capacity_rows']; padded=g['right_padded_rows']; H=6144
 check(len(by)==len(ops),suffix+':unique_ids')
 external={d for o in ops for d in o.deps if d not in by}; oldexternal={d for o in before for d in o.deps if d not in oldby}
 check(external==oldexternal,suffix+':external_dependencies_exact')
 # Computing transitive ancestry for the old direct edges preserves every original external dependency.
 def reaches(node,wanted):
  stack=list(by[node].deps); seen=set()
  while stack:
   d=stack.pop()
   if d==wanted:return True
   if d not in seen:
    seen.add(d)
    if d in by:stack.extend(by[d].deps)
  return False
 removed=set(oldby)-set(by); expected_removed={f's0.l{i}.expert_up.quantize' for i in checked['layer_ids']}
 check(removed==expected_removed,suffix+':only_routed_input_quant_removed')
 for oldop in before:
  if oldop.op_id not in by:continue
  for dep in oldop.deps:
   if dep in removed:
    for p in oldby[dep].deps:check(reaches(oldop.op_id,p),suffix+':removed_quant_dependency:'+oldop.op_id)
   else:check(reaches(oldop.op_id,dep),suffix+':old_edge_reachable:'+oldop.op_id+'<-'+dep)
 indegree={k:sum(d in by for d in v.deps) for k,v in by.items()}; outgoing=defaultdict(list)
 for o in ops:
  for d in o.deps:outgoing[d].append(o.op_id)
 ready=[k for k,n in indegree.items() if not n]; visited=0
 while ready:
  k=ready.pop();visited+=1
  for dest in outgoing[k]:
   indegree[dest]-=1
   if not indegree[dest]:ready.append(dest)
 check(visited==len(by),suffix+':DAG')
 transport_changed=set(); groupcounts=Counter(); workrows=set(); validrows=set(); capacityrows=set(); semids=[]
 for layer in checked['layer_ids']:
  p=f's0.l{layer}'; get=lambda s:by[p+s]; meta=lambda s:dict(get(s).metadata)
  di=get('.dispatch'); co=get('.combine'); up=get('.expert_up'); down=get('.expert_down'); quant=get('.expert_down.quantize')
  dm=meta('.dispatch'); cm=meta('.combine'); um=meta('.expert_up'); wm=meta('.expert_down'); qm=meta('.expert_down.quantize'); caller=dm['mc2_v2_caller']
  work=caller['received_assignments'];workrows.add(work);validrows.add(caller['valid_source_tokens']);capacityrows.add(caller['native_output_capacity_rows'])
  for kind,expectedmembers,entry,exit in [('dispatch',4,'.pack','.dispatch'),('combine',3,'.combine','.unpack')]:
   gid=p+'.mc2_v2_'+kind; members=[o for o in ops if dict(o.metadata).get('device_kernel_group',{}).get('id')==gid]
   groupcounts[kind]+=1;check(len(members)==expectedmembers,f'{suffix}:{gid}:members')
   check([o.op_id for o in members if dict(o.metadata)['device_kernel_group']['entry']]==[p+entry],f'{suffix}:{gid}:one_entry')
   check([o.op_id for o in members if dict(o.metadata)['device_kernel_group']['exit']]==[p+exit],f'{suffix}:{gid}:one_exit')
   check(all(dict(o.metadata)['native_kind']=='MoeDistribute'+kind.title()+'V2' for o in members),f'{suffix}:{gid}:kind')
   transport_changed.update(o.op_id for o in members)
  check(get('.pack').recipe==get('.unpack').recipe=='arch22_v2_caller_local',f'{suffix}:{p}:old_pack_unpack_recipe_gone')
  check(up.deps==(di.op_id,),f'{suffix}:{p}:direct_quantized_transport')
  check(um['activation_payload_producer']==um['activation_scale_producer']==di.op_id,f'{suffix}:{p}:typed_dispatch_producer')
  check((um['activation_format'],um['activation_scale_format'])==('int8','fp32'),f'{suffix}:{p}:payload_scale_dtypes')
  check(tuple(um['activation_scale_shape'])==(work,) and um['activation_scale_bytes']==work*4,f'{suffix}:{p}:valid_scale_work')
  abi=checked['native_contracts']['dispatch'][3]
  check([ [list(t['shape']),t['dtype'],t['layout']] for t in dm['native_abi_outputs'] ]==abi,f'{suffix}:{p}:all_seven_native_outputs')
  check(list(um['native_input_capacity_shape'])==abi[0][0] and list(um['native_input_scale_capacity_shape'])==abi[1][0],f'{suffix}:{p}:capacity_boundary')
  check(work<cap and up.local_shape[0]==down.local_shape[0]==quant.local_shape[0]==work,f'{suffix}:{p}:capacity_not_work')
  check(quant.deps==(get('.expert_act').op_id,) and down.deps==(quant.op_id,),f'{suffix}:{p}:up_activation_quant_down_dependency')
  check(qm['output_format']=='int8' and qm['activation_scale_format']=='fp32' and wm['activation_scale_format']=='fp32',f'{suffix}:{p}:up_subgraph_scale_to_down')
  check(qm['activation_scale_shape']==wm['activation_scale_shape'] and qm['activation_scale_bytes']==wm['activation_scale_bytes']==work*4,f'{suffix}:{p}:up_down_row_scale_work')
  check(wm['output_format']=='bf16' and list(wm['native_output_capacity_shape'])==checked['native_contracts']['combine'][2][0][0],f'{suffix}:{p}:down_bf16_to_combine')
  check(set(co.deps)=={down.op_id,di.op_id,p+'.route_normalize'},f'{suffix}:{p}:weighted_combine_external_inputs')
  check(cm['assist_info_producer']==cm['ep_counts_producer']==cm['expand_scales_buffer_producer']==di.op_id,f'{suffix}:{p}:combine_dispatch_aux')
  check(cm['router_weight_producers']==(p+'.route_normalize',),f'{suffix}:{p}:router_weight_producer')
  check(cm['expand_scales_value_semantics']=='optional; distinct_from_dynamic_scales',f'{suffix}:{p}:distinct_expand_scale')
  check(get('.mc2_input_view').local_shape==(local,H),f'{suffix}:{p}:local_hidden_rows')
  check(get('.mc2_logits_view').local_shape==(local,256),f'{suffix}:{p}:local_router_rows')
  if padded>M:
   check(get('.mc2_input_pad').local_shape==(padded,H) and get('.mc2_logits_pad').local_shape==(padded,256),f'{suffix}:{p}:pad_shapes')
   check(meta('.mc2_input_pad')['input_shapes']==((M,H),(padded-M,H)),f'{suffix}:{p}:pad_inputs')
  else:check(p+'.mc2_input_pad' not in by and p+'.mc2_logits_pad' not in by,f'{suffix}:{p}:no_unneeded_pad')
  gather=get('.mc2_tp_gather');trim=get('.mc2_output_trim') if padded>M else gather;gm=dict(gather.metadata)
  check(gather.deps==(p+'.unpack',) and (padded==M or trim.deps==(gather.op_id,)),f'{suffix}:{p}:finalize_dependencies')
  check(gather.local_shape==(padded,H) and trim.local_shape==(M,H),f'{suffix}:{p}:gather_unpad_shapes')
  check(gm['input_shape']==(local,H) and gm['output_shape']==(padded,H),f'{suffix}:{p}:gather_payload')
  check(gm['collective_role']=='mc2_finalize_token_reconstruction',f'{suffix}:{p}:gather_role')
  check(set(get('.join').deps)=={trim.op_id,p+'.shared.tp'},f'{suffix}:{p}:complete_shared_routed_join')
  for s in ('.shared.gate_up.quantize','.shared.down.quantize'):
   check(asdict(get(s))==asdict(oldby[p+s]),f'{suffix}:{p}:shared_quant_preserved:{s}')
  transport_changed.update([p+'.expert_up',p+'.expert_act',p+'.expert_down'])
 # Any original node outside the intended native boundary/typed consumer has exactly unchanged operation metadata and deps.
 for op in before:
  if op.op_id not in removed|transport_changed:check(normalized_operation(op)==normalized_operation(by[op.op_id]),suffix+':unrelated_node_unchanged:'+op.op_id)
 rows.append({'case_identity':identity(cp),'retained_identity':identity(rp),'source_identity':retained['source_identity'],'body_acceptance_identity':retained['body_acceptance_identity'],'geometry':geometry,'forward_count':retained['forward_count'],'layer_count':len(checked['layer_ids']),'typed_links':checked['typed_links'],'graph_node_count':len(ops),'baseline_node_count':len(before),'removed_input_quantizers':len(removed),'native_groups':dict(groupcounts),'source_local_rows':local,'declared_valid_source_rows':sorted(validrows),'declared_received_assignments':sorted(workrows),'native_capacity_rows':sorted(capacityrows),'external_dependency_ids':sorted(external),'scope_limits':['Source skeleton has separate expert-up / SwiGLU / down-input quantization nodes representing one native fused subgraph; selecting its resource fusion is a separate source-program case choice.','Observed capacity does not establish actual group_list values or valid expert rows.','Public source compatibility does not establish captured binary revision.','Router remains the skeleton FP32 declaration; this audit does not replace the separate BF16 router source overlay.']})
report={'schema_version':'mindie-glm78-native-v2-graph-review/1','runtime_commit':'f6e68d5e326ccbc6aade4f62fffbd816b23da500','runtime_source_identity':identity(FIXED/'mindie_sim/prediction/mc2_arch22.py'),'checker_identity':identity(__file__),'checks':checks,'failures':failures,'cases':rows,'raw_scans':0,'cost_executions':0,'elapsed_s':time.monotonic()-start,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
out=ROOT/'examples/structure/acceptance-20261030-glm78-native-v2-review';out.mkdir(exist_ok=True)
(out/'native-v2-graph-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':checks,'failures':failures[:12],'failure_count':len(failures),'elapsed_s':report['elapsed_s'],'rss':report['peak_rss_bytes'],'cases':[{k:r[k] for k in ('layer_count','graph_node_count','declared_received_assignments','native_capacity_rows')} for r in rows]}))
