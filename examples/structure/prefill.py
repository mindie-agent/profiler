"""Reusable Prefill Body extraction and client TTFT accounting.

[Role] Reuse Sim layer plans and profiler boundary/interval primitives for Prefill.
[Invariants] Ordered full topology, tensor geometry and a vocabulary head are
  required. MTP/head/client TTFT are separate; no client-derived span scaling.
[Timeouts & Locks] One chronological source, <=25k active rows, no model weights.
[Side-Effect Policy] Reads retained CSV/client JSON; writes compact observations.
"""
from collections import Counter
from hashlib import sha256
import json
import math
from math import prod
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

from mindie_profiler.decode_segmentation import (
    _Row, _norm, _norm_start, _head, _body_end, _scope, _activation,
    _MATRICES, _fused_ffn,
)
from mindie_profiler.normalized import kernel_rows


def identity(path):
    path=Path(path).resolve(); h=sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return {'path':str(path),'sha256':h.hexdigest(),'size_bytes':path.stat().st_size}


def anchor(row):
    if not row.inputs: return None
    shape=row.inputs[0]
    if row.kind in {'ChunkFwdH','ChunkGatedDeltaRuleFwd'}:
        return 'gdn'
    if row.kind=='ChunkKdaFwd': return 'kda'
    if row.kind=='SparseAttnSharedkv' and shape and shape[0]>16: return 'mla'
    if row.kind=='FusedInferAttentionScore':
        q=shape[2] if len(shape)==4 else shape[0] if len(shape)==3 else None
        return 'gqa' if q is not None and q>16 else None
    return None


def align(rows, config, ordinal):
    hidden=config['hidden_size']; plans=config['layer_plans']
    anchors=[(i,anchor(r)) for i,r in enumerate(rows) if anchor(r)]
    actual=[kind for _,kind in anchors]
    expected=[p['attention'] for p in plans]
    if actual!=expected:
        return None,{'reason':'ordered_prefill_layer_plan_mismatch','anchor_count':len(actual),
                     'expected_layers':len(expected),'head_locator':rows[-1].event.locator}
    norms=[i for i,r in enumerate(rows) if _norm(r,hidden)]
    starts=[]; inputs=[]; prev=-1
    for index,_ in anchors:
        choices=[i for i in norms if prev<i<index]
        if not choices:return None,{'reason':'input_norm_missing','layer':len(starts)}
        inputs.append(choices[-1]);starts.append(_norm_start(rows,choices[-1],hidden));prev=index
    queries={prod(rows[i].inputs[0][:-1]) for i in inputs}
    if len(queries)!=1 or next(iter(queries))<=16:
        return None,{'reason':'inconsistent_large_query','queries':sorted(queries)}
    query=next(iter(queries))
    finals=[i for i in norms if i>anchors[-1][0]]
    if len(finals)<2:return None,{'reason':'ffn_and_final_norm_missing'}
    final=_norm_start(rows,finals[-1],hidden)
    end=_body_end(rows,final,anchors[-1][0],plans[-1],query,hidden)
    if end is None:return None,{'reason':'final_mhc_output_missing'}
    successor=rows[end if end<final else finals[-1]]
    layers=[]
    for layer,(start,stop,(attention,_),plan) in enumerate(zip(starts,[*starts[1:],end],anchors,plans)):
        ffn=[i for i in norms if attention<i<stop]
        if not ffn:return None,{'reason':'ffn_input_missing','layer':layer}
        remaining=rows[ffn[0]+1:stop]
        acts=[i for i,r in enumerate(remaining) if _activation(r)]
        if not acts:return None,{'reason':'ffn_activation_missing','layer':layer}
        a=acts[0]; fused=remaining[a]
        returned=(_fused_ffn(fused) and fused.outputs[0][-1]==hidden) or any(
            r.outputs and r.outputs[0] and r.outputs[0][-1]==hidden
            and (r.kind in _MATRICES or r.kind.startswith('GroupedMatmul')
                 or any(k in r.kind for k in ('Unpermute','FinalizeRouting','DistributeCombine')))
            for r in remaining[a+1:])
        if not returned:return None,{'reason':'ffn_hidden_return_missing','layer':layer}
        nxt=rows[starts[layer+1]] if layer+1<len(plans) else successor
        layers.append(_scope(rows[start:stop], 'moe_layer' if plan['ffn']=='moe' else 'dense_layer',
                             f'prefill:{ordinal}/layer:{layer}',layer=layer,plan=plan,successor=nxt))
    body=_scope(rows[starts[0]:end],'target_body',f'prefill:{ordinal}',successor=successor)
    compact_layers=[{key:value for key,value in layer.items() if key in (
        'layer_id','attention','start_ns','end_ns','span_ms','device_activity_union_ms',
        'internal_uncovered_gap_ms','event_count','excluded_tail_wait_events','excluded_tail_wait_activity_ms')}
        | {'first_csv_line':layer['evidence']['first_locator'].get('csv_line'),
           'last_csv_line':layer['evidence']['last_locator'].get('csv_line')} for layer in layers]
    return {'forward_id':f'prefill:{ordinal}','phase':'prefill','query_rows':query,
            'basis':'structure_guided_complete_prefill_topology_and_vocab_head',
            'body':body,'layers':compact_layers,'head':_scope(rows[-1:],'lm_head',f'head:{ordinal}'),
            'matched_layer_count':len(layers),'body_includes_mtp':False},None


def extract_events(events, config, *, max_active_events=25000):
    """Align a chronological Event/shape stream; no I/O or cost computation."""
    active=[]; forwards=[]; anomalies=[]; counts=Counter(); previous=None
    for normalized in events:
        event=normalized.event
        if event.duration_ns<=0:continue
        if previous is not None and event.start_ns<previous:
            raise ValueError('source_not_chronological')
        previous=event.start_ns
        row=_Row(event,normalized.input_shapes,normalized.output_shapes)
        active.append(row);counts['positive_events']+=1
        if len(active)>max_active_events:raise ValueError('unclosed_prefill_segment_exceeds_bound')
        if not _head(row,config):continue
        result,error=align(active,config,len(forwards))
        if result:
            forwards.append(result);counts['selected_body_events']+=result['body']['event_count']
        else:
            counts[error['reason']]+=1
            if len(anomalies)<20:anomalies.append(error)
        active=[]
    counts['trailing_events']=len(active)
    return {'schema_version':'mindie-prefill-body-observation/1',
            'status':'measured' if forwards else 'unresolved','forwards':forwards,
            'scan_counts':dict(counts),'anomaly_examples':anomalies,
            'body_span_sum_ms':sum(f['body']['span_ms'] for f in forwards) if forwards else None,
            'body_activity_union_sum_ms':sum(f['body']['device_activity_union_ms'] for f in forwards) if forwards else None,
            'matched_query_rows':sum(f['query_rows'] for f in forwards),
            'boundary':'first body input norm/HCPre through final target FFN output; excludes final norm, logits, MTP and inter-chunk scheduling',
            'limitations':['Topology alignment is conditional, not Host occurrence evidence.',
                           'Summed body chunk spans are not client TTFT; overlap/gaps remain separate.',
                           'No scaled client timing substitutes for device timing.']}


def extract_file(path, config, *, max_rows=5_000_000, timeout_s=180, max_active_events=25000):
    result=extract_events(kernel_rows(path,max_rows=max_rows,timeout_s=timeout_s),config,
                          max_active_events=max_active_events)
    result['source_identity']=identity(path)
    return result


def request_population(value):
    """Use retained request records/counters, not concurrency or TTFT sample count."""
    requests=value.get('per_request')
    if isinstance(requests,list) and requests:
        ok=sum(r.get('ok') is True for r in requests)
        total=len(requests);basis='retained_per_request_records'
    elif isinstance(value.get('n_ok'),int) and isinstance(value.get('n_failed'),int):
        ok=value['n_ok'];total=ok+value['n_failed'];basis='retained_n_ok_plus_n_failed'
    elif isinstance(value.get('n_requests'),int) and isinstance(value.get('n_errors'),int):
        total=value['n_requests'];ok=total-value['n_errors'];basis='retained_n_requests_minus_n_errors'
    else:
        return {'status':'unknown','request_count':None,'successful_requests':None,
                'basis':'request_population_not_exported'}
    return {'status':'single_request' if total==1 and ok==1 else 'multiple_or_failed_requests',
            'request_count':total,'successful_requests':ok,'basis':basis}


def _flat_stats(value, prefix):
    # The producer filters missing timings before aggregation. Request counts
    # alone do not prove the metric's valid-timing denominator.
    if value.get(prefix+'_mean') is None:return None
    return {**{key:value.get(prefix+'_'+key) for key in ('mean','p50','p90','min','max')},
            'count':None,'population_basis':'producer aggregate; valid timing count not exported'}


def client_measurement(path, *, profiled=None):
    """Retain only the client's literal first-token metric; E2E is separate."""
    path=Path(path)
    if not path.exists():return {'status':'missing_same_run_client_artifact','identity':None,'ttft_ms':None}
    if path.stat().st_size>50_000_000:
        raise ValueError('client_metadata_requires_streaming:'+str(path))
    value=json.loads(path.read_text());cfg=value.get('config') or {}
    ttft=value.get('ttft_ms') or _flat_stats(value,'ttft_ms')
    return {'identity':identity(path),'status':'measured' if ttft else 'ttft_not_exported',
            'source_status':value.get('status'),
            'ttft_ms':ttft,'e2e_ms':value.get('e2e_ms') or _flat_stats(value,'e2e_ms'),
            'decode_ttft_ms':_flat_stats(value,'decode_ttft_ms'),
            'prefill_http_ms':_flat_stats(value,'prefill_ms'),
            'metric_boundary':'literal client aggregates; HTTP prefill/Decode TTFT/E2E are separate from device Body',
            'request_population':request_population(value),
            'input_len':value.get('input_len',value.get('prompt_tokens',cfg.get('prompt_tokens'))),
            'output_len':value.get('output_len',cfg.get('output_tokens')),
            'concurrency':value.get('concurrency',cfg.get('concurrency')),'n_ok':value.get('n_ok'),
            'n_failed':value.get('n_failed'),'profiled_client':profiled,
            'e2e_substituted_for_ttft':False}


def associate_request(observed, *, prompt_tokens, client, prefix_evidence=None):
    """Keep exact query workload and independently evidenced request identity apart."""
    complete=observed['matched_query_rows']==prompt_tokens
    population=client.get('request_population') or request_population(client)
    status=population['status'];single=status=='single_request'
    comparable=complete and status!='multiple_or_failed_requests'
    if not complete:
        association='capture_query_rows_do_not_match_client_no_timing_based_subset_selection'
    elif single:
        association='single_request_exact_prompt_query_sum'
    elif comparable:
        association='exact_query_workload_request_identity_unverified'
    else:
        association='multiple_or_failed_client_requests_without_chunk_membership'
    return {**observed,'declared_prompt_tokens':prompt_tokens,'client':client,
        'prompt_query_coverage_complete':complete,'request_population':population,
        'request_identity_status':status,'body_workload_comparable':comparable,
        'comparison_body_sum_ms':observed['body_span_sum_ms'] if comparable else None,
        'request_prefill_body_sum_ms':observed['body_span_sum_ms'] if complete and single else None,
        'client_to_body_association':association,
        'prefix_cache':{'evidence_identity':prefix_evidence,'observed_hit_ratio':None,
            'policy':'source declaration only; query coverage does not manufacture a cache-hit counter'}}


def validate(observed, config):
    """Check saved integer spans and full layer populations without another raw pass."""
    failures=[]; checks=0
    def check(value,label):
        nonlocal checks
        checks+=1
        if not value:failures.append(label)
    def same(a,b,label):check(math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9),label)
    expected=[p['attention'] for p in config['layer_plans']]
    for forward in observed['forwards']:
        body=forward['body']
        same(body['span_ms'],(body['end_ns']-body['start_ns'])/1e6,'integer body span')
        same(body['span_ms'],body['device_activity_union_ms']+body['internal_uncovered_gap_ms'],'interval union accounting')
        check([l['attention'] for l in forward['layers']]==expected,'complete ordered layer plan')
        check(not forward['body_includes_mtp'],'MTP excluded')
        check(body['end_ns']<=forward['head']['start_ns'],'body before vocabulary head')
        for layer in forward['layers']:
            same(layer['span_ms'],(layer['end_ns']-layer['start_ns'])/1e6,'integer layer span')
            check(body['start_ns']<=layer['start_ns']<=layer['end_ns']<=body['end_ns'],'layer inside body')
    if observed['forwards']:
        same(sum(f['body']['span_ms'] for f in observed['forwards']),observed['body_span_sum_ms'],'all body spans')
    return {'status':'failed' if failures else 'passed','checks':checks,'failures':failures}


def runtime_identity():
    # Use the same Python + JSON package identity as the unified pipeline.
    from decode import _sim_identity
    return _sim_identity()


def _single_stat(value):
    return {'count':0 if value is None else 1,'mean':value,'p50':value,'p90':value,
            'min':value,'max':value}


def _price_chunk(case_path, tokens, context, timeout_s):
    """Use the shared generic Body adapter in one bounded subprocess."""
    adapter=Path(__file__).with_name('body.py');before=identity(adapter)
    with tempfile.TemporaryDirectory(prefix='mindie-prefill-') as directory:
        output=Path(directory)/'body.json'
        command=[sys.executable,str(adapter),'--case',str(case_path),'--tokens',str(tokens),
                 '--context',str(context),'--sequences','1','--phase','prefill','--output',str(output)]
        try:
            process=subprocess.run(command,capture_output=True,text=True,timeout=timeout_s)
        except subprocess.TimeoutExpired:
            return {'status':'failed','reason':'prefill_prediction_timeout','timeout_s':timeout_s}
        if process.returncode:
            return {'status':'failed','reason':'prefill_prediction_failed',
                    'returncode':process.returncode,'stderr':process.stderr[-2000:]}
        result=json.loads(output.read_text())
    if before!=identity(adapter):return {'status':'failed','reason':'body_adapter_changed'}
    if result['execution']['peak_rss_bytes']>512*1024**2:
        return {'status':'failed','reason':'prediction_memory_budget_exceeded','execution':result['execution']}
    prediction=result['prediction']
    if prediction['status']!='modeled' or not prediction['timeline_complete']:
        return {'status':'failed','reason':'prefill_body_timeline_incomplete'}
    return {'status':'completed','execution':result['execution'],'adapter_identity':before,
            'prediction':{key:prediction[key] for key in ('body_forward_span_ms','per_layer_ms',
                'geometry','boundary_details','operator_occurrences','timeline_complete')}}


def run_case(row, base:Path, *, prediction_timeout_s=90):
    """Shared pipeline entry: measure a catalog case, then price each complete chunk.

    Geometry comes from the source body and declared request, never TTFT. No
    learned parameters are fit or modified. The unique capture with extra query
    chunks stays unscored at request scope; it is not trimmed by elapsed time.
    """
    if row['source'].get('kind')=='client_json':
        # A retained client benchmark is valid TTFT evidence without a device
        # capture. Its request count does not identify Body calls or chunks.
        source=Path(row['source']['path'])
        if not source.is_absolute():source=Path(base)/source
        source_pin=identity(source)
        if any(source_pin[key]!=row['source'][key] for key in ('sha256','size_bytes')):
            raise ValueError('client_source_identity_changed')
        client=client_measurement(source,profiled=False)
        if client['identity']!=source_pin:
            raise ValueError('client_source_changed_during_read')
        return {'case_id':row['case_id'],'catalog_id':row['id'],'phase':'prefill',
            'status':'observed_only','source_identity':source_pin,'client':client,
            'runtime_identity':runtime_identity(),'model_case_consumed':False,
            'ttft_prediction_ms':None,'body_and_ttft_scopes_separate':True,
            'comparison':{'status':'observed_only','observed_ms':_single_stat(None),
                'predicted_ms':None,'relative_error':None,'passed':None,
                'scope':'literal client TTFT only; device Body unavailable'},
            'observed':{'status':'client_only','device_body_available':False,
                'request_population':client['request_population'],
                'request_identity_status':'no_device_chunk_association',
                'body_span_sum_ms':None,'body_activity_union_sum_ms':None},
            'execution':{'new_predictions':0,'new_device_captures':0,'fit_performed':False}}
    from mindie_sim.prediction.structure import parse_case
    started=time.monotonic();spec=row['prefill'];path=Path(row['sim_case_path'])
    if not path.is_absolute():path=Path(base)/path
    generation=runtime_identity();model_pin=identity(path)
    result={'case_id':row['case_id'],'catalog_id':row['id'],'phase':'prefill',
            'runtime_identity':generation,'model_case_identity':model_pin,
            'source_identity':row['source'],'calibration_origin':'not_declared',
            'ttft_prediction_ms':None,'body_and_ttft_scopes_separate':True}
    if model_pin['sha256']!=row['model_case']['sha256']:
        return {**result,'status':'failed','reason':'model_case_identity_changed'}
    raw=json.loads(path.read_text());case=parse_case(raw)
    if case.runtime.parallel.tp!=spec['tp']:
        return {**result,'status':'failed','reason':'source_declared_tp_mismatch'}
    cfg=json.loads(json.dumps(case.model.to_dict()));cfg['tp']=spec['tp']
    observed=extract_file(row['source']['path'],cfg)
    if observed['source_identity']['sha256']!=row['source']['sha256']:
        return {**result,'status':'failed','reason':'source_identity_changed'}
    client=client_measurement(spec['client'],profiled=True)
    if spec.get('client_identity') and client['identity']!=spec['client_identity']:
        return {**result,'status':'failed','reason':'client_identity_changed'}
    prefix=identity(spec['prefix_evidence']) if spec.get('prefix_evidence') else None
    if spec.get('prefix_evidence_identity') and prefix!=spec['prefix_evidence_identity']:
        return {**result,'status':'failed','reason':'prefix_declaration_identity_changed'}
    observed=associate_request(observed,prompt_tokens=spec['prompt'],client=client,
        prefix_evidence=prefix)
    result.update(observed=observed,validation=validate(observed,cfg),client=client)
    if not observed['forwards'] or result['validation']['status']=='failed':
        return {**result,'status':'failed','reason':'complete_prefill_body_not_validated'}
    if not observed['body_workload_comparable']:
        return {**result,'status':'unresolved','reason':'client_request_chunk_membership_not_unique',
                'comparison':{'status':'unresolved','observed_ms':_single_stat(None),
                    'predicted_ms':None,'relative_error':None,'passed':None}}
    chunks=[];context=0
    for index,forward in enumerate(observed['forwards']):
        priced=_price_chunk(path,forward['query_rows'],context,prediction_timeout_s)
        chunks.append({'chunk_index':index,'tokens':forward['query_rows'],'context':context,
                       'observed_ms':forward['body']['span_ms'],**priced})
        context+=forward['query_rows']
        if priced['status']!='completed':break
    result['chunks']=chunks
    result['execution']={'elapsed_s':time.monotonic()-started,'prediction_timeout_s':prediction_timeout_s,
                         'new_device_captures':0,'fit_performed':False}
    if runtime_identity()!=generation or identity(path)!=model_pin:
        return {**result,'status':'failed','reason':'prediction_input_generation_changed'}
    if len(chunks)!=len(observed['forwards']) or any(c['status']!='completed' for c in chunks):
        return {**result,'status':'failed','reason':'prefill_chunk_prediction_failed',
                'comparison':{'status':'failed','observed_ms':_single_stat(observed['comparison_body_sum_ms']),
                    'predicted_ms':None,'relative_error':None,'passed':None}}
    predicted=sum(c['prediction']['body_forward_span_ms'] for c in chunks)
    real=observed['comparison_body_sum_ms'];error=predicted/real-1
    result.update(status='completed',comparison={'status':'compared','observed_ms':_single_stat(real),
        'predicted_ms':predicted,'relative_error':error,'per_workload_diff_ms':predicted-real,
        'per_request_diff_ms':predicted-real if observed['request_identity_status']=='single_request' else None,
        'request_identity_status':observed['request_identity_status'],
        'passed':abs(error)<=.15,'threshold':.15,
        'observed_population_basis':('one verified request, sum of its complete target-body chunk spans'
            if observed['request_identity_status']=='single_request' else
            'one capture query workload; client request identity unverified'),
        'scope':'sum of target-body chunk spans; excludes scheduling between chunks, MTP and client overhead',
        'assumptions':['Source rank represents balanced declared TP/EP cohort conditionally.',
                       'Context grows by captured query rows under the source prefix policy.',
                       'Device first-event and model input-ready endpoints may differ.']})
    comparisons=[]
    for measured,priced in zip(observed['forwards'],chunks):
        nodes={r['layer_id']:r for r in priced['prediction']['per_layer_ms'] if r['replica']==0}
        for layer in measured['layers']:
            model=nodes.get(layer['layer_id'])
            if model is None:
                raise ValueError('predicted_prefill_layer_missing')
            span=model['end_ms']-model['start_ms']
            difference=span/layer['span_ms']-1
            comparisons.append({'chunk_index':priced['chunk_index'],'status':'compared',
                'layer_id':layer['layer_id'],'observed_ms':_single_stat(layer['span_ms']),'predicted_ms':span,
                'relative_error':difference,'passed':abs(difference)<=.15,'representative_replica':0})
    result['per_layer_comparison']={'layers':comparisons,
        'observed_population_basis':'one layer occurrence in each explicit chunk; contexts are not pooled',
        'summary':{'compared_layers':len(comparisons),'passed_layers':sum(r['passed'] for r in comparisons)}}
    return result
