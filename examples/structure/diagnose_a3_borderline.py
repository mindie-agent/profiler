"""Audit near-threshold A3 bodies without treating activity as wall-time causality.

[Role] Join whole-body receipts, complete family histograms and declared references.
[Invariants] Reference populations cover complete native calls; capacity is not
  valid work. Signed residual is Sim service minus measured activity, never a
  correction to the existing Body span. All layers and batch programs survive.
[Timeouts & Locks] One source at a time; bounded saved metadata; no locks.
[Side-Effect Policy] Local evidence/Sim reads and independent output only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import time

from body_source_role_references import predict_source_role_references, reference_signature
from compare_body_operator_families import prediction_runtime_identity
from kimi_native_references import _convolution, _kda, freeze
from replay_body_operator_families import duration_stats, identity, read, write


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def select_fia_batch(native, local, execution):
    """Keep the complete declared batch, with physical head mismatch explicit."""
    ins, outs = native[2:]
    batch, query = execution['sequences'], execution['tokens']
    if native[:2] != ('native_tensor_abi', 'FusedInferAttentionScore') or (len(ins), len(outs)) != (7, 2):
        raise ValueError('A3_FIA_requires_complete_7_input_2_output_ABI')
    q, key, value, lengths, table, rope_q, rope_cache = ins
    if (q[0] != (batch, 16, query, 512) or q[1:] != ('bf16', 'ND')
            or outs[0] != ((16, batch, query, 512), 'bf16', 'ND')
            or lengths != ((batch,), 'int64', 'ND') or table[0][0] != batch
            or table[1:] != ('int32', 'ND') or key != value
            or key[0][1:] != (1, 128, 512) or key[1:] != ('bf16', 'ND')
            or rope_q != ((batch, 16, query, 64), 'bf16', 'ND')
            or rope_cache != ((key[0][0], 1, 128, 64), 'bf16', 'ND')):
        raise ValueError('A3_FIA_query_cache_rope_table_or_NBS_output_differs')
    targets = [n for n in local if n['family'] == 'attention']
    if len(targets) != batch or len({n['node_id'] for n in targets}) != batch:
        raise ValueError('FIA_reference_must_cover_every_declared_sequence_once')
    shapes = {tuple(n['operator']['local_shape']) for n in targets}
    if len(shapes) != 1 or next(iter(shapes))[0] != query or next(iter(shapes))[-2:] != (576, 512):
        raise ValueError('FIA_declared_latent_program_geometry_differs')
    shape = next(iter(shapes))
    return 'latent_attention_complete_batch', targets, {'basis': 'existing_complete_MLA_batch_semantic_programs'}, {
        'boundary_relation': 'unfused_complete_batch_semantic_reference_not_native_kernel',
        'observed_physical_heads': 16, 'declared_logical_heads': shape[2],
        'declared_sequence_program_count': batch, 'declared_context_extent': shape[1],
        'observed_sequence_length_values': None, 'observed_cache_capacity_blocks': key[0][0],
        'observed_block_table_capacity': table[0][1],
        'limitations': ['All declared sequence programs are selected together and costed once.',
            'Native physical 16 heads differ from declared logical heads; padding work is not invented.',
            'Unfused sequence programs do not prove the fused native batch implementation.',
            'Sequence-length values and binary/tiling identity are absent; cache capacity is not context.',
            'This reference replaces the incomplete one-sequence reference, not any Body prediction.']}


def price_kimi(partition_path, case_path, output):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    before = prediction_runtime_identity(); started = time.perf_counter()
    pins = {'partition_identity': identity(partition_path), 'case_identity': identity(case_path)}
    part = read(partition_path); actual = read(part['actual_identity']['path'])
    if identity(part['actual_identity']['path']) != part['actual_identity']:
        raise ValueError('retained_actual_identity_changed')
    for key in ('source_identity', 'body_acceptance_identity', 'geometry', 'forward_count'):
        if part[key] != actual[key]: raise ValueError('retained_population_differs:' + key)
    case = parse_case(read(case_path)); geo = part['geometry']
    manifest = export_structure(case, phase='decode', tokens=geo['tokens_per_sequence'],
        sequences=geo['sequences_per_replica'], context=actual['conditional_context_tokens'], scope='body')
    layers, subgraphs = defaultdict(list), defaultdict(list)
    for n in manifest['nodes']:
        if n['replica'] == 0: layers[n.get('layer')].append(n)
    for n in manifest['subgraphs']:
        if n['replica'] == 0: subgraphs[n.get('layer')].append(n)
    groups = []
    for p in part['partitions']:
        kind = p['native_operator_type']
        if kind not in {'RecurrentKda', 'CausalConv1d', 'FusedInferAttentionScore'}: continue
        native = freeze(p['native_abi']); key = None; representative = None
        for layer in sorted(map(int, p['layer_counts'])):
            chosen = (select_fia_batch(native, layers[layer], manifest['execution']) if kind == 'FusedInferAttentionScore'
                else {'RecurrentKda': _kda, 'CausalConv1d': _convolution}[kind](native,
                    layers[layer], subgraphs[layer], manifest['execution'], p))
            name, targets, declaration, correspondence = chosen
            current = canonical([(reference_signature(t), t['physical_work']) for t in targets])
            if key is not None and current != key: raise ValueError('native_partition_programs_heterogeneous')
            key = current; representative = chosen
        name, targets, declaration, correspondence = representative
        groups.append({'group_id': 'sha256:' + sha256(canonical((kind, native, key)).encode()).hexdigest(),
            'native_operator_type': kind, 'native_name': kind, 'declared_role': name,
            'representative_replica': 0, 'representative_target_ids': [t['node_id'] for t in targets],
            'physical_program_signatures': [t['physical_signature'] for t in targets],
            'physical_work_per_program': [t['physical_work'] for t in targets],
            'source_anchor_declaration': declaration,
            'source_correspondence': {**correspondence, 'observed_native_tensor_contract': native},
            'layer_ids': sorted(map(int, p['layer_counts'])),
            'observed_us': p['observed_us'], 'duration_ns_counter': p['duration_ns_counter'],
            'observed_activity_sum_ns': sum(ns*n for ns,n in p['duration_ns_counter'])})
    result = predict_source_role_references(case, manifest,
        {'source_role_references': groups, 'forward_count': part['forward_count']})
    if len(result) != len(groups) or any(g['prediction_status'] != 'reference_only' for g in result):
        raise ValueError('complete_native_reference_prediction_missing')
    if prediction_runtime_identity() != before: raise ValueError('runtime_changed')
    for pin in pins.values():
        if identity(pin['path']) != pin: raise ValueError('input_changed')
    write(output, {'schema_version': 'mindie-a3-borderline-native-references/1', **pins,
        'source_identity': part['source_identity'], 'body_acceptance_identity': part['body_acceptance_identity'],
        'geometry': geo, 'forward_count': part['forward_count'], 'groups': result,
        'runtime_source_identity': before, 'runtime_sources_unchanged': True,
        'elapsed_seconds': time.perf_counter()-started, 'raw_capture_reads': 0,
        'old_one_sequence_FIA_reference_superseded': True})


def priced_row(kind, role, count, mean, p50, predicted_us, forwards, strength, evidence, **extra):
    return {'native_operator_type': kind, 'declared_role': role, 'event_count': count,
        'calls_per_forward': count/forwards, 'real_mean_us': mean, 'real_p50_us': p50,
        'sim_mean_us': predicted_us, 'observed_activity_ms_per_forward': mean*count/1000/forwards,
        'predicted_service_ms_per_forward': predicted_us*count/1000/forwards,
        'signed_activity_residual_ms_per_forward': (predicted_us-mean)*count/1000/forwards,
        'evidence_strength': strength, 'strict_accuracy_implied': strength == 'strict_cohort',
        'evidence': evidence, **extra}


def family_ledger(case, extra_references=(), confirmed_controller_types=()):
    """Coverage and errors use exactly the population priced, never whole-family fill."""
    forwards=case['forward_count']; priced=[]; unpriced=[]; overlays=[]; superseded=[]
    overrides=defaultdict(list)
    for ref in extra_references: overrides[ref['native_operator_type']].append(ref)
    for family in case['families']:
        kind,role=family['native_operator_type'],family['declared_role']
        stats=duration_stats(dict(family['duration_ns_counter']),1000)
        if stats != family['observed_us']: raise ValueError('retained_family_statistics_differ')
        if kind in confirmed_controller_types:
            overlays.append({'native_operator_type':kind,'declared_role':role,'observed_us':stats,
                'calls_per_forward':stats['count']/forwards,
                'activity_ms_per_forward':stats['mean']*stats['count']/1000/forwards,
                'basis':'all retained calls independently verified AI_CPU/Block0/Mix0 in PMU partitions',
                'additive_to_device_service':False,'body_span_modified':False})
            continue
        matched_count=0; matched_activity_ns=0
        for cohort in family['cohorts']:
            if cohort['status'] not in {'compared','reference_only'} or not cohort.get('prediction'): continue
            obs=cohort['observed']; n=obs['event_count']; mean=obs['complete_activity_sum_ns']/n/1000
            strength='strict_cohort' if cohort['status']=='compared' else 'conditional_declared_subgraph'
            priced.append(priced_row(kind,role,n,mean,obs['duration_ns']['p50']/1000,
                cohort['prediction']['per_call_ms']*1000,forwards,strength,
                {'cohort_id':cohort['cohort_id'],'boundary':cohort['prediction']['boundary'],
                 'contract_scope':cohort.get('contract_scope'),'accuracy_pass':cohort.get('accuracy_pass')}))
            matched_count+=n;matched_activity_ns+=obs['complete_activity_sum_ns']
        refs=overrides.get(kind) or family.get('conditional_source_role_references',())
        if refs and matched_count: raise ValueError('references_overlap_scored_family_population')
        for ref in refs:
            obs=ref['observed_us'];n=obs['count'];pred=ref.get('predicted_reference_us')
            if pred is None: continue
            priced.append(priced_row(kind,ref.get('declared_role',role),n,obs['mean'],obs['p50'],pred,
                forwards,'conditional_source_reference',
                {'group_id':ref['group_id'],'boundary':ref['source_correspondence']['boundary_relation'],
                 'source_correspondence':ref['source_correspondence']}))
            matched_count+=n;matched_activity_ns+=ref['observed_activity_sum_ns']
        generic=family.get('conditional_program_reference')
        if kind in overrides and generic:
            superseded.append({'native_operator_type':kind,'declared_role':role,'prior_reference':generic,
                'reason':'single_sequence_program_does_not_cover_captured_native_batch',
                'replacement':'complete_declared_batch_program_set_conditional_reference'})
        if not matched_count and generic and generic.get('status')=='reference_only' and 'per_call_ms' in generic:
            priced.append(priced_row(kind,role,stats['count'],stats['mean'],stats['p50'],
                generic['per_call_ms']*1000,forwards,'conditional_collective_reference',generic))
            matched_count=stats['count'];matched_activity_ns=sum(ns*n for ns,n in family['duration_ns_counter'])
        remaining=stats['count']-matched_count
        activity=sum(ns*n for ns,n in family['duration_ns_counter'])-matched_activity_ns
        if remaining<0 or activity<0: raise ValueError('priced_population_exceeds_measured_family')
        if remaining:
            unpriced.append({'native_operator_type':kind,'declared_role':role,'event_count':remaining,
                'calls_per_forward':remaining/forwards,'unpriced_activity_ms_per_forward':activity/1e6/forwards,
                'whole_family_real_mean_us':stats['mean'],'whole_family_real_p50_us':stats['p50'],
                'unpriced_mean_us':activity/remaining/1000,'unpriced_p50_us':stats['p50'] if remaining==stats['count'] else None,
                'sim_mean_us':None,'signed_activity_residual_ms_per_forward':None,
                'reasons':family['cohort_reasons'],'current_rebind_exclusions':family.get('current_rebind_exclusions',[])})
    return {'priced_rows':priced,
        'top3_underestimates':sorted((p for p in priced if p['signed_activity_residual_ms_per_forward']<0),
                                  key=lambda p:p['signed_activity_residual_ms_per_forward'])[:3],
        'top3_overestimates':sorted((p for p in priced if p['signed_activity_residual_ms_per_forward']>0),
                                 key=lambda p:-p['signed_activity_residual_ms_per_forward'])[:3],
        'unpriced_families':sorted(unpriced,key=lambda p:-p['unpriced_activity_ms_per_forward']),
        'controller_overlays':overlays,'superseded_references':superseded}


def build_ledger(body_path, root, output):
    body=read(body_path); results=[]
    for source_id,arm in [('v4flash-a3-tp8-c4','v4'),('a3_kimi4_tp8_w4a8_c32','kimi')]:
        b=next(c for c in body['cases'] if c['source_case_id']==source_id and c['status']=='compared')
        score_path=root/(arm+'-30d')/'body-operator-family-scoreboard.json'
        compact=read(score_path);detail=compact['cases'][0]['case_detail_identity']
        if identity(detail['path']) != detail: raise ValueError('case_detail_identity_changed')
        case=read(detail['path'])['cases'][0];actual=read(case['actual_identity']['path'])
        if case['source_identity']!=b['source_identity'] or actual['body_acceptance_identity']['sha256']!=b['extraction_identity']['sha256']:
            raise ValueError('body_family_source_or_accepted_window_identity_differs')
        if case['case_identity']['sha256']!=b['model_structure_identity']['sha256']:
            raise ValueError('body_family_declaration_identity_differs')
        for key in ('tokens_per_sequence','sequences_per_replica','query_rows'):
            if case['geometry'][key]!=b['geometry'][key]:raise ValueError('body_family_geometry_differs')
        stats=b['observed']['body_forward_span_ms'];n=stats['count']
        if n!=case['forward_count']:raise ValueError('body_family_population_differs')
        native_path=root/'kimi-complete-native-references.json';refs=[];controllers=[]
        if arm=='kimi':
            native=read(native_path)
            if any(native[k]!=actual[k] for k in ('source_identity','body_acceptance_identity','geometry','forward_count')):
                raise ValueError('native_reference_population_differs')
            refs=native['groups']
            partition=read(native['partition_identity']['path'])
            if identity(native['partition_identity']['path'])!=native['partition_identity']:
                raise ValueError('native_partition_identity_changed')
            wrapper_hist=Counter();cores=Counter();blocks=Counter();mix=Counter()
            for p in partition['partitions']:
                if p['native_operator_type']!='reduce_scatterAicpuKernel':continue
                wrapper_hist.update(dict(p['duration_ns_counter']))
                dims=p['raw_pmu']['dimensions'];cores.update(dict(dims['Accelerator Core']))
                blocks.update(dict(dims['Block Num']));mix.update(dict(dims['Mix Block Num']))
            original=next(f for f in case['families'] if f['native_operator_type']=='reduce_scatterAicpuKernel')
            n_wrappers=sum(wrapper_hist.values())
            if (wrapper_hist!=Counter(dict(original['duration_ns_counter'])) or cores!={'AI_CPU':n_wrappers}
                    or blocks!={'0':n_wrappers} or mix!={'0':n_wrappers}):
                raise ValueError('controller_overlay_complete_typed_population_not_verified')
            controllers=['reduce_scatterAicpuKernel']
        ledger=family_ledger(case,refs,controllers);pred=b['comparison']['predicted_ms'] if 'predicted_ms' in b['comparison'] else b['prediction']['body_forward_span_ms']
        if isinstance(pred,dict):pred=pred['mean']
        mean=stats['mean']
        results.append({'source_case_id':source_id,'source_identity':case['source_identity'],
            'case_identity':case['case_identity'],'extraction_identity':b['extraction_identity'],
            'family_scoreboard_identity':identity(score_path),'family_detail_identity':detail,
            'native_reference_identity':identity(native_path) if arm=='kimi' else None,
            'runtime_identity':b['runtime_identity'],'operator_runtime_commit':compact['runtime_source_commit'],
            'geometry':case['geometry'],'forward_count':n,'source_forward_count':case['source_forward_count'],
            'selected_body_event_count':sum(f['observed_us']['count'] for f in case['families']),
            'body':{'real_ms':stats,'sim_ms':pred,'relative_error':pred/mean-1,
                'signed_difference_ms':pred-mean,'lower_15_percent_limit_ms':.85*mean,
                'remaining_to_lower_limit_ms':max(0,.85*mean-pred),
                'device_activity_union_ms':b['observed']['body_activity_ms'],
                'internal_uncovered_gap_ms':b['observed']['body_internal_gap_ms'],
                'span_modified':False},'layers':b['per_layer_comparison']['layers'],**ledger})
    result={'schema_version':'mindie-a3-borderline-gap-ledger/1','body_receipt_identity':identity(body_path),
        'cases':results,'interpretation':[
            'Signed activity residual is Sim service minus measured native elapsed activity per complete forward.',
            'These rows are not additive causal contributions to Body wall-time error.',
            'Unknown cost remains null; unpriced activity is not a predicted error.',
            'Gaps remain measured internal uncovered intervals, not automatically Host scheduling.',
            'Transformer layer kind labels describe its FFN; attention remains a separate layer block.',
            'Reference heads, cache lengths, expert routing and peer readiness remain explicit conditions.']}
    write(output,result); output.with_suffix('.md').write_text(render_ledger(result))


def render_ledger(report):
    lines=['# A3 near-threshold Body and family ledger','',
        'Fixed Sim `30dcea1e`. Residual sign is Sim − Real. Native activity/service differences are not additive Body wall-clock causes.','']
    for case in report['cases']:
        body=case['body'];real=body['real_ms'];lines += [f"## {case['source_case_id']}",'',
            f"Selected {case['forward_count']} / {case['source_forward_count']} complete forwards; {len(case['layers'])} layers. "
            f"Body Real Mean/P50 {real['mean']:.6f}/{real['p50']:.6f} ms, Sim {body['sim_ms']:.6f} ms "
            f"({body['relative_error']:+.2%}). The lower 15% bound is {body['lower_15_percent_limit_ms']:.6f} ms; "
            f"shortfall {body['remaining_to_lower_limit_ms']:.6f} ms.",
            f"Measured activity union {body['device_activity_union_ms']['mean']:.6f} ms, internal uncovered gap "
            f"{body['internal_uncovered_gap_ms']['mean']:.6f} ms. Both original measurements are retained.",'',
            '| Same-direction Top3 / role | Evidence | Calls/F | Real Mean / P50 us | Sim us | Sim−Real ms/F |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
        for row in case['top3_underestimates']:
            lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['evidence_strength']} | {row['calls_per_forward']:.3f} | {row['real_mean_us']:.6f} / {row['real_p50_us']:.6f} | {row['sim_mean_us']:.6f} | {row['signed_activity_residual_ms_per_forward']:+.6f} |")
        lines += ['', 'Largest opposite-direction rows:']
        for row in case['top3_overestimates']:
            lines.append(f"- {row['native_operator_type']} / {row['declared_role']}: {row['signed_activity_residual_ms_per_forward']:+.6f} ms/F ({row['evidence_strength']}).")
        lines += ['', '| Unpriced family / role | Calls/F | Real Mean / P50 us | Unpriced activity ms/F |',
            '| --- | ---: | ---: | ---: |']
        for row in case['unpriced_families'][:12]:
            lines.append(f"| {row['native_operator_type']} / {row['declared_role']} | {row['calls_per_forward']:.3f} | {row['whole_family_real_mean_us']:.6f} / {row['whole_family_real_p50_us']:.6f} | {row['unpriced_activity_ms_per_forward']:.6f} |")
        if case['controller_overlays']:
            lines += ['', 'The 1,760 `reduce_scatterAicpuKernel` records are confirmed AI_CPU / Block0 / Mix0. Their 1.375535 ms/F elapsed overlay is isolated from service residuals. The existing alias filter recognizes `reducescatterAicpuKernel`, so this underscore variant needs a separate boundary regression; no Body time is subtracted here.']
        if case['superseded_references']:
            lines += ['', 'The old FIA 5 us reference selected one of 32 sequences. This ledger replaces that reference with all 32 declared programs costed together (160 us), not with a manually multiplied budget. It remains conditional: native physical 16 heads differ from declared logical 12, context scalar values are missing, and 32 unfused programs differ from one native batch call.']
        lines += ['', 'All priced rows, original histograms via source references, per-layer means, exact source/case/runtime identities and remaining unpriced families are retained in JSON.','']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--partition', type=Path)
    parser.add_argument('--case', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--body-receipt', type=Path)
    parser.add_argument('--ledger-root', type=Path)
    args = parser.parse_args()
    if args.body_receipt:build_ledger(args.body_receipt,args.ledger_root,args.output)
    else:price_kimi(args.partition, args.case, args.output)


if __name__ == '__main__':
    main()
