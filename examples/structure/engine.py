"""Join retained device boundaries and independently scoped serving measurements.

[Role] Join target cycles/client denominators and execute the formal serving API.
[Invariants] A cycle between complete target bodies is not a Host step marker;
  interval unions never double count. Missing stages/counters remain unknown.
  Configured acceptance and tensor padding never substitute for emitted tokens.
[Timeouts & Locks] One prediction child, explicit timeout and 512 MiB RSS cap.
[Side-Effect Policy] Local metadata and CPU simulation only; no raw CSV/device work.
"""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
from mindie_profiler.process_memory import peak_rss_bytes

import subprocess


def read(path):
    path=Path(path)
    if path.stat().st_size>50*1024**2:raise ValueError('metadata_requires_streaming:'+str(path))
    return json.loads(path.read_text())


def identity(path):
    path=Path(path).resolve();h=sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return {'path':str(path),'sha256':h.hexdigest(),'size_bytes':path.stat().st_size}


def verify(pin):
    current=identity(pin['path'])
    if current['sha256']!=pin['sha256']:raise ValueError('retained_metadata_changed:'+pin['path'])
    return current


def stats(values):
    ordered=sorted(values);n=len(ordered)
    if not n:return {'count':0,'mean':None,'p50':None,'p90':None,'min':None,'max':None}
    def quantile(q):
        x=(n-1)*q;i=int(x);return ordered[i]+(ordered[min(i+1,n-1)]-ordered[i])*(x-i)
    return {'count':n,'mean':sum(ordered)/n,'p50':quantile(.5),'p90':quantile(.9),'min':ordered[0],'max':ordered[-1]}


def union_ns(intervals):
    end=None;total=0
    for lo,hi in sorted(intervals):
        if hi<lo:raise ValueError('negative_interval')
        if end is None or lo>end:total+=hi-lo
        else:total+=max(0,hi-end)
        end=hi if end is None else max(end,hi)
    return total


def geometry_key(g):
    return tuple(g.get(k) for k in ('query_rows','tokens_per_sequence','sequences_per_replica'))


def cycles(extraction):
    by_device=defaultdict(list)
    for f in extraction['forwards']:by_device[(f.get('rank_id'),f.get('device_id'))].append(f)
    auxiliaries=extraction.get('auxiliary_occurrences',[]);output=[];invalid=[]
    for (rank,device),forwards in by_device.items():
        ordered=sorted(forwards,key=lambda f:f['start_ns'])
        for current,nxt in zip(ordered,ordered[1:]):
            lo,hi=current['start_ns'],nxt['start_ns']
            if current['end_ns']>hi:
                invalid.append({'forward_id':current['forward_id'],'reason':'body_overlaps_next_target'});continue
            known=[(lo,current['end_ns'])];head=[]
            if current.get('head_start_ns') is not None:
                if current['head_end_ns']>hi:
                    invalid.append({'forward_id':current['forward_id'],'reason':'head_overlaps_next_target'});continue
                head=[(current['head_start_ns'],current['head_end_ns'])];known+=head
            aux=[a for a in auxiliaries if a.get('rank_id')==rank and a.get('device_id')==device
                 and a['start_ns']>=lo and a['end_ns']<=hi]
            known.extend((a['start_ns'],a['end_ns']) for a in aux)
            # Short subgraph spans contain their own internal gaps. This union
            # is an accounting of known scopes, not a PMU device-busy estimate.
            accounted=union_ns(known);span=hi-lo
            output.append({'forward_id':current['forward_id'],'rank_id':rank,'device_id':device,
                'start_ns':lo,'next_target_start_ns':hi,'geometry':current['geometry'],
                'same_geometry_next_target':geometry_key(current['geometry'])==geometry_key(nxt['geometry']),
                'target_cycle_span_ms':span/1e6,'body_span_ms':(current['end_ns']-lo)/1e6,
                'target_body_to_head_end_ms':((current['head_end_ns']-lo)/1e6 if head else None),
                'known_scope_union_ms':accounted/1e6,'unclassified_outer_or_between_scope_ms':(span-accounted)/1e6,
                'short_auxiliary_count':len(aux),'short_auxiliary_scope_union_ms':union_ns([(a['start_ns'],a['end_ns']) for a in aux])/1e6,
                'auxiliary_anchor_count_histogram':dict(Counter(a['anchor_count'] for a in aux)),
                'auxiliary_identity_status':'retained_short_subgraphs_not_proven_MTP',
                'host_gap_attribution_established':False})
    return output,invalid


def request_summary(requests,seconds=False):
    usable=[r for r in requests if r.get('ok') and isinstance(r.get('completion_tokens'),(int,float))]
    tokens=sum(r['completion_tokens'] for r in usable)
    tpots=[]
    for r in usable:
        completion=r['completion_tokens']
        if seconds:
            elapsed,first=r.get('e2e_s'),r.get('ttft_s');factor=1000
        else:
            elapsed,first=r.get('e2e_ms'),r.get('ttft_ms');factor=1
        if elapsed is not None and first is not None and completion>1:tpots.append((elapsed-first)*factor/(completion-1))
    return {'successful_requests':len(usable),'actual_completion_tokens':tokens,
            'recomputed_per_request_tpot_ms':stats(tpots),
            'denominator':'actual completion_tokens - 1 per successful request; E2E minus TTFT',
            'text_chunk_count_not_substituted_for_tokens':True,
            'reported_request_metric_denominators':dict(Counter(request_metric_basis(r,seconds) for r in usable))}


def request_metric_basis(row,seconds=False):
    """Check the producer's denominator against retained request counters."""
    value=row.get('tpot_tok_ms',row.get('tpot_ms'))
    if value is None:return 'not_reported_per_request'
    factor=1000 if seconds else 1
    elapsed=row.get('e2e_s' if seconds else 'e2e_ms')
    first=row.get('ttft_s' if seconds else 'ttft_ms')
    decode=row.get('decode_ms',(elapsed-first)*factor if elapsed is not None and first is not None else None)
    if decode is None:return 'insufficient_request_timing'
    candidates=[]
    for name,count in (('completion_token',row.get('completion_tokens')),('text_chunk',row.get('n_text_chunks'))):
        if count and count>1 and abs(value-decode/(count-1))<=max(0.001,abs(value)*1e-5):candidates.append(name)
    return '+'.join(candidates) if candidates else 'not_reproduced_from_retained_denominators'


def retained_requests(summary_path,summary):
    """Only documented local sidecars from this benchmark directory are used."""
    if summary.get('per_request'):return summary['per_request'],identity(summary_path),False
    root=Path(summary_path).parent
    for name,field,seconds in (('profile_evidence.json','requests',True),('client_cell.json','per_request',False)):
        candidate=root/name
        if candidate.exists():
            payload=read(candidate)
            if payload.get(field):return payload[field],identity(candidate),seconds
    return [],None,False


def serving_evidence(scenario,summary):
    root=Path(scenario['benchmark_summary']['path']).parent
    current_pin=identity(scenario['benchmark_summary']['path'])
    current_tpot=(summary.get('tpot_client_ms') or summary.get('tpot_tok_ms') or summary.get('tpot_ms')
        or ({'p50':summary['profile_cell']['tpot_true_p50_ms']} if 'profile_cell' in summary else None))
    result={'benchmark_summary_identity':current_pin,
        'benchmark_summary_prior_identity':scenario['benchmark_summary'],
        'benchmark_metadata_generation':('same' if current_pin['sha256']==scenario['benchmark_summary']['sha256'] else 'changed_since_body_manifest; current bounded metadata read explicitly recorded'),
        'profiled_client_tpot':current_tpot,
        'historical_profiled_client_tpot':scenario.get('tpot',{}).get('profiled_run_client_ms'),
        'unprofiled_sweep_tpot_ms':scenario.get('tpot',{}).get('unprofiled_sweep_ms'),
        'profile_window':summary.get('profile_window'),'client_concurrency':scenario.get('client',{}).get('concurrency'),
        'profiled_vs_unprofiled_kept_separate':True,'client_metric_scope':'complete benchmark requests, not only retained device-window calls'}
    for key in ('output_throughput_tok_s','output_throughput_tok_s_steady','total_output_tokens','n_ok','wall_s',
                'step_time_engine_ms','step_time_client_ms','step_ms','tokens_per_chunk'):
        if key in summary:result[key]=summary[key]
    requests,request_pin,seconds=retained_requests(scenario['benchmark_summary']['path'],summary)
    if scenario.get('request_records'):
        request_pin=scenario['request_records'];payload=read(request_pin['path'])
        key=scenario.get('request_array_key') or ('requests' if 'requests' in payload else 'per_request')
        requests=payload[key];seconds=bool(requests and 'e2e_s' in requests[0])
    if requests:
        result['profiled_request_population']=request_summary(requests,seconds=seconds)
        result['request_records_identity']=request_pin
        result['reported_tpot_interpretation']=result['profiled_request_population']['reported_request_metric_denominators']
    evidence_path=root/'profile_evidence.json'
    if evidence_path.exists():
        evidence=read(evidence_path);result['profile_evidence_identity']=identity(evidence_path)
        result['profiled_full_run_metrics']=evidence.get('summary')
        result['counter_delta']= {k:v for k,v in evidence.get('delta',{}).items()
            if k=='vllm:generation_tokens_total' or k.startswith('vllm:spec_decode')}
        result['counter_scope']='retained benchmark metric-delta window; not equated to device cycle window'
    engine=summary.get('engine_window')
    if engine:
        concurrency=result['client_concurrency'];drafts=engine.get('d_drafts');generation=engine.get('d_generation_tokens')
        steps=drafts/concurrency if drafts is not None and concurrency else None
        result['engine_window_counters']={**engine,'recomputed_steps_from_per_request_drafts':steps,
            'observed_emitted_tokens_per_request_draft':generation/drafts if drafts and generation is not None else None,
            'recomputed_step_service_ms':engine['metrics_interval_s']*1000/steps if steps and engine.get('metrics_interval_s') else None,
            'rate_basis':'actual counter deltas; configured 0.8 acceptance unused'}
    result['step_trace']=scenario.get('step_trace') or {'per_step_boundaries_available':False,'basis':'not_retained_in_manifest'}
    return result



def resolved(path,base):
    path=Path(path)
    return path.resolve() if path.is_absolute() else (base/path).resolve()


def pin_path(value,base,*,verify_hash=True):
    if isinstance(value,str):return identity(resolved(value,base))
    path=resolved(value['path'],base);current=identity(path)
    if verify_hash and value.get('sha256') and current['sha256']!=value['sha256']:
        raise ValueError('metadata_changed:'+str(path))
    return current


def observed_case(entry,base):
    """Consume the canonical case, not a prior prediction or ranking report."""
    if entry['source'].get('kind') == 'client_json':
        return client_observation(entry, base)
    engine=entry['engine'];extraction_pin=pin_path(entry.get('extraction_identity') or entry['extraction_path'],base)
    extraction=read(extraction_pin['path'])
    if extraction['source_identity']['sha256']!=entry['source']['sha256']:
        raise ValueError('source_and_extraction_differ:'+entry['case_id'])
    summary_pin=pin_path(engine['benchmark_summary'],base);summary=read(summary_pin['path'])
    observed_cycles,invalid=cycles(extraction);by_geometry=defaultdict(list)
    for c in observed_cycles:by_geometry[geometry_key(c['geometry'])].append(c)
    groups=[]
    for items in by_geometry.values():
        groups.append({'geometry':items[0]['geometry'],'cycle_count':len(items),
            **{field:stats([c[field] for c in items if c[field] is not None]) for field in (
                'target_cycle_span_ms','body_span_ms','target_body_to_head_end_ms','known_scope_union_ms',
                'unclassified_outer_or_between_scope_ms','short_auxiliary_scope_union_ms')},
            'same_geometry_next_count':sum(c['same_geometry_next_target'] for c in items),
            'short_auxiliary_count_histogram':dict(Counter(c['short_auxiliary_count'] for c in items)),
            'samples':items[:3]})
    scenario={'benchmark_summary':summary_pin,'client':{'concurrency':engine.get('client_concurrency',summary.get('concurrency'))},
              'tpot':engine.get('tpot',{}),'step_trace':engine.get('step_trace'),
              'request_records':pin_path(engine['request_records'],base) if engine.get('request_records') else None,
              'request_array_key':engine.get('request_array_key')}
    evidence=serving_evidence(scenario,summary)
    bounds=evidence.get('profile_window') or {};start=bounds.get('start_profile_epoch',bounds.get('started_at'));end=bounds.get('stop_profile_epoch',bounds.get('stopped_at'))
    evidence['retained_body_clock_containment']={'profile_start_epoch':start,'profile_end_epoch':end,
        'all_selected_bodies_inside':all(start*1e9<=f['start_ns']<=f['end_ns']<=end*1e9 for f in extraction['forwards']) if start is not None and end is not None else None,
        'cross_machine_clock_offset_calibrated':False}
    return {'id':entry.get('id',entry['case_id']),'case_id':entry['case_id'],'source_identity':entry['source'],
        'extraction_identity':extraction_pin,'primary_geometry':entry['geometry'],
        'observed_target_forwards':len(extraction['forwards']),
        'cycle_count':len(observed_cycles),'invalid_cycles':invalid,'cycle_geometry_groups':groups,
        'cycle_boundary':'consecutive target-body starts on the same rank/device; final open cycle excluded',
        'outer_stage_measurements':[{k:v for k,v in s.items() if k not in {'samples','per_stream_activity_ms'}}
             for s in extraction['stage_span_ms'] if s.get('kind') not in {'body','layer'}],
        'outer_stage_population':'all complete target forwards in this extraction; not added to overlapping Body intervals',
        'serving_evidence':evidence,'bridge_kind':'observed boundaries; missing remainder is not attributed to Host',
        'prediction':None,'client_delivery_prediction_claimed':False}


def client_observation(entry, base):
    """Retain literal client/PD metrics without manufacturing device boundaries."""
    pin = pin_path(entry['source'], base)
    payload = read(pin['path'])
    config = payload.get('config', {})
    metrics = {}
    for name in ('ttft_ms', 'itl_ms', 'steady_itl_ms', 'tpot_ms', 'prefill_ms', 'decode_ttft_ms', 'e2e_ms'):
        values = {stat: payload[name + '_' + stat] for stat in ('mean', 'p50', 'p90', 'max')
                  if name + '_' + stat in payload}
        if not values and isinstance(payload.get(name),dict):values=payload[name]
        if values: metrics[name] = values
    if 'itl_ms' not in metrics and isinstance(payload.get('itl_ms_all_tokens'),dict):
        metrics['itl_ms']=payload['itl_ms_all_tokens']
    records=payload.get('per_request') or payload.get('requests') or []
    request_stats=request_summary(records,seconds=bool(records and 'e2e_s' in records[0])) if records else None
    n_errors=payload.get('n_errors',payload.get('n_failed'))
    producer_status=payload.get('status')
    if producer_status is None and n_errors is not None:
        producer_status='failed' if n_errors else 'completed'
    errors=payload.get('errors')
    if errors is None:
        errors=[{key:record[key] for key in ('slot','status','error') if key in record}
                for record in records if record.get('ok') is False]
    evidence = {
        'benchmark_summary_identity': pin, 'producer_status': producer_status,
        'producer_status_basis':'literal status or retained failure count',
        'client_concurrency': config.get('concurrency',payload.get('concurrency')),
        'request_configuration': config or {k:payload[k] for k in ('input_len','output_len','concurrency','num_prompts') if k in payload},
        'n_requests': payload.get('n_requests',len(records) if records else None), 'n_errors': n_errors,
        'errors': errors, 'metrics': metrics,
        'metric_source_fields':{'itl_ms':'itl_ms_all_tokens' if 'itl_ms_all_tokens' in payload
                                and 'itl_ms' not in payload else 'itl_ms'},
        'metric_boundaries': {'ttft_ms': 'client request to first streamed response',
            'itl_ms': 'streamed event cadence; not assumed one token per event',
            'tpot_ms': 'literal producer TPOT; denominator audited against retained requests when available',
            'prefill_ms': 'prefiller HTTP request; not device Prefill Body',
            'decode_ttft_ms': 'decoder HTTP first response; separate PD endpoint',
            'e2e_ms': 'whole client request'},
        'reported_aggregate_tpot_ms': metrics.get('tpot_ms'),
        'raw_request_records_available': bool(records),
        'request_population':request_stats,
        'output_tok_s': payload.get('output_tok_s',payload.get('output_throughput_tok_s')),
        'completion_tokens': payload.get('completion_tokens',payload.get('total_output_tokens')),
        'wall_s': payload.get('wall_s'),
        'retained_counters': {k: v for k, v in payload.items() if k in {
            'decode_s_sum', 'decode_events_sum', 'token_gaps_sum', 'prefix_cache_queries_delta',
            'prefix_cache_hits_delta', 'measured_hit_rate', 'target_hit_rate', 'planned_cached_tokens',
            'warm_uncached_prompt_tokens', 'alpha_from_server', 'alpha_from_decode_server',
            'tokens_per_step_from_server', 'tokens_per_step_pooled', 'prefill_hit_rate',
            'prefill_prompt_tokens_delta', 'decode_generation_tokens_delta'}},
    }
    alpha = payload.get('alpha_from_server', payload.get('alpha_from_decode_server'))
    proposals = entry['engine'].get('draft_proposals')
    cadence = metrics.get('steady_itl_ms', {}).get('mean')
    real_tpot = metrics.get('tpot_ms', {}).get('mean')
    if alpha is not None and proposals is not None and cadence is not None and real_tpot:
        expected = cadence / (1 + proposals * alpha)
        evidence['acceptance_bridge'] = {'scope': 'measured event cadence and measured server acceptance; not Sim',
            'draft_proposals': proposals, 'observed_acceptance': alpha,
            'expected_tokens_per_step': 1 + proposals * alpha,
            'cadence_based_tpot_ms': expected, 'observed_tpot_ms': real_tpot,
            'relative_difference': expected / real_tpot - 1}
    return {'id': entry['id'], 'case_id': entry['case_id'], 'source_identity': pin,
        'observed_target_forwards': None, 'cycle_count': None, 'cycle_geometry_groups': [],
        'outer_stage_measurements': [], 'serving_evidence': evidence,
        'bridge_kind': 'client metrics only; device Body/Outer/MTP/Host intervals unavailable',
        'client_delivery_prediction_claimed': False}


def request_workload(records):
    successful=[r for r in records if r.get('ok')]
    starts=[r.get('t_start_epoch',r.get('t_start')) for r in successful]
    if not starts or any(x is None for x in starts):raise ValueError('actual_request_arrivals_missing')
    origin=min(starts);requests=[]
    for i,(r,start) in enumerate(zip(successful,starts)):
        usage=r.get('usage') or {};prompt=r.get('prompt_tokens',usage.get('prompt_tokens'));output=r.get('completion_tokens',usage.get('completion_tokens'))
        if not isinstance(prompt,int) or not isinstance(output,int) or min(prompt,output)<=0:
            raise ValueError('actual_request_token_count_missing')
        requests.append({'id':f'observed-{i}','arrival_ms':(start-origin)*1000,
                         'prompt_tokens':prompt,'output_tokens':output,'prefix_tokens':0})
    return {'requests':requests,'synthetic':False},origin


def captured_speculative_policy(summary, recipe):
    """Map declared policy or retained prefix counters; never infer from TPOT."""
    spec=recipe.get('speculative_config') or recipe.get('speculative')
    if spec:
        width=spec['num_speculative_tokens'];rates=spec.get('synthetic_acceptance_rates')
        if rates is None or len(rates)!=width:raise ValueError('explicit_draft_acceptance_policy_missing')
        return {'draft_len':width,'acceptance':rates,'acceptance_mode':'marginal',
            'label':'captured configured synthetic policy; not actual acceptance trace'}, {
            'basis':'captured configured synthetic distribution','evaluation_relation':'configured',
            'actual_acceptance_trace_available':False}
    reported=summary.get('summary') or {}
    width=reported.get('spec_k')
    if not width:return None,{'basis':'unchanged source case declaration',
        'evaluation_relation':'not_declared','actual_acceptance_trace_available':False}
    delta=summary.get('delta') or {}
    draft_tokens=delta.get('vllm:spec_decode_num_draft_tokens_total')
    accepted=delta.get('vllm:spec_decode_num_accepted_tokens_total')
    counts=[delta.get(f'spec_pos:{i}') for i in range(width)]
    if (draft_tokens is None or accepted is None or any(v is None for v in counts)):
        raise ValueError('captured_speculative_acceptance_counters_missing')
    # The producer retains tokens and prefix-position counts, not draft-round
    # events. Dividing by explicitly declared fixed k is a stated input condition.
    rounds=draft_tokens/width
    if rounds<=0 or sum(counts)!=accepted or any(v<0 or v>rounds for v in counts):
        raise ValueError('captured_speculative_acceptance_counters_inconsistent')
    rates=[v/rounds for v in counts]
    if any(a<b for a,b in zip(rates,rates[1:])):
        raise ValueError('captured_prefix_acceptance_counts_not_monotone')
    return {'draft_len':width,'acceptance':rates,'acceptance_mode':'marginal',
        'label':'observed prefix marginals conditional on fixed proposal width; not request trace'}, {
        'basis':'retained per-position accepted counts / (draft tokens / declared fixed proposal width)',
        'evaluation_relation':'in_sample','declared_proposal_tokens':width,
        'draft_tokens':draft_tokens,'accepted_tokens':accepted,'accepted_per_position':counts,
        'derived_draft_rounds':rounds,'fixed_proposal_width_assumption':True,
        'counter_window':'retained server metric delta; distinct from complete client-request population',
        'actual_acceptance_trace_available':False,'observed_gaps_used_as_parameters':False}


def prepare_serving(entry,base,case_path):
    original=pin_path(entry.get('model_case') or entry['sim_case_path'],base)
    case=read(original['path']);engine=entry['engine'];summary_pin=pin_path(engine['benchmark_summary'],base)
    summary=read(summary_pin['path']);records,request_pin,seconds=retained_requests(summary_pin['path'],summary)
    # An explicit canonical request file takes precedence over discovered same-run sidecars.
    if engine.get('request_records'):
        request_pin=pin_path(engine['request_records'],base);payload=read(request_pin['path'])
        key=engine.get('request_array_key') or ('requests' if 'requests' in payload else 'per_request')
        records=payload[key]
    workload,origin=request_workload(records);case['workload']=workload
    recipe=summary.get('recipe') or summary.get('extra',{}).get('recipe') or {}
    copied={k:recipe[k] for k in ('max_model_len','max_num_seqs','max_num_batched_tokens','gpu_memory_utilization','enable_chunked_prefill') if k in recipe}
    case['runtime'].update(copied);metadata=case['runtime'].setdefault('metadata',{})
    spec,acceptance_evidence=captured_speculative_policy(summary,recipe)
    if spec:
        metadata['draft_mode']='mtp';metadata['speculative']=spec
    prefix=engine.get('prefix_tokens');prefix_basis=engine.get('prefix_basis')
    if prefix is None:
        protocol=summary.get('prefix_cache_protocol')
        if protocol and protocol.get('warmup_cell') and protocol.get('max_cacheable_tokens') is not None:
            prefix=int(protocol['max_cacheable_tokens']);prefix_basis='declared warmed complete blocks; actual per-request residency unavailable'
        else:
            prefix=0;prefix_basis='explicit cold residency condition; not inferred from hit-rate mean'
            if recipe.get('enable_prefix_caching') is False or metadata.get('prefix_cache',{}).get('enabled') is False:
                prefix_basis='cache disabled by retained deployment declaration'
    for request in workload['requests']:
        if not isinstance(prefix,int) or not 0<=prefix<=request['prompt_tokens']:raise ValueError('prefix_residency_invalid')
        request['prefix_tokens']=prefix
    proof={'base_case_identity':original,'benchmark_summary_identity':summary_pin,'request_records_identity':request_pin,
        'arrival_epoch_origin':origin,'requests':len(workload['requests']),
        'actual_completion_tokens':sum(r['output_tokens'] for r in workload['requests']),
        'runtime_fields_from_retained_recipe':copied,'prefix_tokens':prefix,'prefix_residency_basis':prefix_basis,
        'acceptance_basis':acceptance_evidence['basis'],'acceptance_evidence':acceptance_evidence,
        'actual_acceptance_trace_available':False,'observed_gaps_used_as_parameters':False,
        'client_delivery_modeled':False,'scope':'full successful client-request workload; device token commit endpoint'}
    metadata['serving_workload_evidence']=proof
    case_path.parent.mkdir(parents=True,exist_ok=True);case_path.write_text(json.dumps(case,indent=2)+'\n')
    return {'case_identity':identity(case_path),'workload_evidence':proof}


def sim_identity():
    from decode import _sim_identity
    return _sim_identity()


def serving_worker(case_path,output):
    from mindie_sim import predict
    before=sim_identity();started=time.perf_counter();pin=identity(case_path)
    result=predict(read(case_path),scope='serving',trace_limit=3,event_limit=0)
    after=sim_identity();rss=peak_rss_bytes()
    if before!=after or identity(case_path)!=pin:raise ValueError('prediction_inputs_changed')
    if rss>512*1024**2:raise MemoryError('serving_prediction_exceeds_512MiB')
    receipt={'status':'completed','case_identity':pin,'runtime_identity':{**before,'sources_unchanged':True},
        'prediction':result,'execution':{'elapsed_seconds':time.perf_counter()-started,'peak_rss_bytes':rss,
        'raw_capture_reads':0,'formal_entry':'predict(scope=serving, trace_limit=3, event_limit=0)'}}
    output.write_text(json.dumps(receipt,indent=2)+'\n')


def bounded_serving(prepared,output,timeout):
    import psutil
    before=sim_identity();start=time.perf_counter();peak=0
    stderr=output.with_suffix('.stderr.log');stdout=output.with_suffix('.stdout.log')
    command=[sys.executable,__file__,'--worker-case',prepared['case_identity']['path'],'--worker-output',str(output)]
    reason=None
    with stdout.open('w') as out,stderr.open('w') as err:
        process=subprocess.Popen(command,stdout=out,stderr=err)
        while process.poll() is None:
            try:
                peak=max(peak,psutil.Process(process.pid).memory_info().rss)
            except psutil.NoSuchProcess:
                break
            if peak>512*1024**2:reason='serving_prediction_memory_limit'
            elif time.perf_counter()-start>timeout:reason='serving_prediction_timeout'
            if reason:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
                break
            time.sleep(.25)
        code=process.wait(timeout=3)
    after=sim_identity()
    if before!=after:reason='sim_runtime_changed'
    if code or reason:
        return {'status':'failed','reason':reason or 'serving_prediction_failed','returncode':code,
            'elapsed_seconds':time.perf_counter()-start,'peak_sampled_rss_bytes':peak,
            'runtime_identity':{**before,'sources_unchanged':before==after},
            'stderr_identity':identity(stderr),'error':stderr.read_text()[-3000:]}
    receipt=read(output);prediction=receipt['prediction']
    return {'status':'completed','full_prediction_identity':identity(output),
        'runtime_identity':receipt['runtime_identity'],'execution':receipt['execution'],
        'metric_boundary':prediction['metric_boundary'],'metrics':prediction['metrics'],
        'simulation_status':prediction['status'],'simulation_execution_status':prediction['execution_status'],
        'serving_execution':prediction['execution'],'assumptions':prediction['assumptions'],
        'trace_count':len(prediction['traces']),'client_delivery_comparison_status':'different_endpoint; device-token-only prediction'}


def run_case(row, base: Path, *, prediction_timeout_s=90):
    """Public engine adapter for pipeline.py; all failures retain their boundary."""
    import tempfile
    base=Path(base).resolve()
    if not row.get('engine'):
        return {'case_id':row['case_id'],'status':'unresolved','observed':None,'comparison':None,
                'error':{'reason':'engine_request_metadata_not_declared'}}
    observed=observed_case(row,base)
    engine=row['engine']
    if engine.get('observation_only'):
        producer = observed['serving_evidence'].get('producer_status')
        failed = producer not in (None, 'completed')
        return {'case_id': row['case_id'], 'id': row['id'], 'observed': observed,
            'status': 'failed' if failed else 'completed', 'prediction': None,
            'comparison': {'status': 'failed' if failed else 'observed_only', 'passed': None,
                'reason': 'producer_failed' if failed else 'full_serving_prediction_not_requested_for_client_only_source'},
            'error': observed['serving_evidence'].get('errors') if failed else None,
            'execution': {'raw_capture_reads': 0, 'prediction_executions': 0}}
    configured=engine.get('artifact_dir')
    artifact_dir=resolved(configured,base) if configured else Path(tempfile.gettempdir())/'mindie-profiler-engine'/row['case_id']
    artifact_dir.mkdir(parents=True,exist_ok=True)
    prepared=prepare_serving(row,base,artifact_dir/'serving-case.json')
    run_key=sha256((prepared['case_identity']['sha256']+sim_identity()['package_sha256']).encode()).hexdigest()[:16]
    prediction=bounded_serving(prepared,artifact_dir/('serving-result-'+run_key+'.json'),prediction_timeout_s)
    result={'case_id':row['case_id'],'id':row.get('id',row['case_id']),
            'status':prediction['status'],'observed':observed,'serving_input':prepared,
            'prediction':prediction,'comparison':None,'error':None,
            'execution':{'raw_capture_reads':0,'prediction_executions':1}}
    if prediction['status']!='completed':
        result['error']={'reason':prediction['reason'],'detail':prediction.get('error')}
        return result
    if prediction['simulation_status']!='modeled' or prediction['simulation_execution_status']!='completed':
        result['status']='failed'
        result['error']={'reason':'serving_workload_infeasible','simulation_status':prediction['simulation_status'],
                         'execution_status':prediction['simulation_execution_status']}
        return result
    real=observed['serving_evidence'].get('profiled_request_population',{}).get('recomputed_per_request_tpot_ms',{})
    predicted=prediction['metrics']['tpot_ms']
    actual=real.get('p50');estimated=predicted.get('p50')
    result['comparison']={'status':'conditional_endpoint_comparison','prediction_boundary':'device_token_commit',
        'observation_boundary':'client_token_arrival','observed_token_tpot_ms':real,
        'predicted_device_token_tpot_ms':predicted,
        'p50_relative_difference':estimated/actual-1 if actual and estimated is not None else None,
        'same_endpoint_accuracy_established':False,'passed':None,
        'unmodeled_endpoint_components':['host_result_ready','client_delivery'],
        'observed_gaps_inserted_into_prediction':False}
    return result


def _worker_main():
    p=argparse.ArgumentParser(description='Internal serving worker; use pipeline.py --scope engine.')
    p.add_argument('--worker-case',type=Path,required=True);p.add_argument('--worker-output',type=Path,required=True)
    args=p.parse_args();serving_worker(args.worker_case,args.worker_output)

if __name__=='__main__':_worker_main()
