"""[Role] Build an actual HCCL ledger within already accepted Decode bodies.
[Invariants] Integer windows and whole-layer topology are reused, not re-inferred
  from communication names. Identical HCOM summary/device rows count once;
  unlinked AICPU/device tasks remain separate. Payload and algorithm stay unknown
  unless observed; a model tensor-size hypothesis is not wire traffic evidence.
[Timeouts & Locks] One retained body buffer; 180 s / 5M rows per local source.
[Side-Effect Policy] Local read-only capture/declaration access and new reports;
  no prediction, bandwidth fitting, NPU, remote calls, or source mutation.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import csv
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.accounting import union_length
from mindie_profiler.decode_segmentation import _align, _anchor, _model, _norm, _norm_start, _Row
from mindie_profiler.events import QueryStats
from mindie_profiler.normalized import shapes
from mindie_profiler.sources_csv import decode_csv_row, probe_csv, _open_csv_text
from mindie_sim.prediction.operator_analysis import target_graphs
from mindie_sim.prediction.structure import parse_case
from replay_body_operator_families import deduplicate_communication, duration_stats, identity, read, write
from targeted_native_pmu import NativePmu

MISSING = {'', 'N/A', 'NA', 'NONE', 'NULL', 'NAN'}


def geometry_key(value):
    return tuple(value[k] for k in ('tokens_per_sequence', 'sequences_per_replica', 'query_rows'))


def relevant(event):
    text = (event.name + event.op_type).lower()
    return event.op_type.startswith('hcom_') or event.core in {'COMMUNICATION', 'SDMA', 'DPU'} or any(
        word in text for word in ('sdma', 'notify', 'ccu', 'dpu', 'moedistributedispatch',
                                   'moedistributecombine', 'dispatchffncombine')) or (
        'aicpu' in event.core.lower().replace('_', '') and
        any(word in text for word in ('hccl', 'hcom', 'reduce', 'gather', 'alltoall')))


def category(event):
    if event.op_type.startswith('hcom_'):
        concrete = event.task_id.upper() not in MISSING and event.stream_id.upper() not in MISSING
        return 'collective_device_task' if concrete else 'collective_envelope_only'
    if 'aicpu' in event.core.lower().replace('_', ''):
        return 'unlinked_aicpu_wrapper'
    if any(word in event.op_type.lower() for word in ('moedistributedispatch', 'moedistributecombine', 'dispatchffncombine')):
        return 'native_fused_communication_program'
    return 'unlinked_device_communication_task'


def raw_stream(path, schema):
    stats = QueryStats('rank_0', 'retained_body_hccl', budget=5_000_000)
    deadline = time.perf_counter() + 180
    with _open_csv_text(path) as stream:
        reader = csv.reader(stream)
        if tuple(next(reader)) != schema.header:
            raise ValueError('capture_header_changed')
        for index, values in enumerate(reader):
            if index >= 5_000_000 or index % 1024 == 0 and time.perf_counter() > deadline:
                raise TimeoutError('hccl_scan_budget_exceeded')
            event = decode_csv_row(values, index, schema, rank_id='rank_0', rank_index=0,
                                   stats=stats, strict=True)
            if event is None:
                continue
            raw = dict(zip(schema.header, values)) if relevant(event) else None
            yield event, {key: value.strip() for key, value in raw.items()} if raw else None


def source_pins():
    import mindie_profiler.decode_segmentation as segmentation
    import mindie_profiler.sources_csv as parser
    import mindie_profiler.native_tensor_abi as tensor
    import mindie_sim
    paths = [Path(__file__), Path(segmentation.__file__), Path(parser.__file__), Path(tensor.__file__),
             Path(__file__).with_name('targeted_native_pmu.py'),
             Path(__file__).with_name('replay_body_operator_families.py')]
    # Graph and model declarations are read without cost evaluation; pin their source.
    paths += list(Path(mindie_sim.__file__).resolve().parent.rglob('*.py'))
    return {str(path.resolve()): identity(path)['sha256'] for path in paths}


def declared_collectives(case, geometry, context):
    graphs = target_graphs(case, phase='decode', tokens=geometry['tokens_per_sequence'],
                          sequences=geometry['sequences_per_replica'], context=context, scope='body')
    replica = min(graphs)
    result = defaultdict(list)
    for op in graphs[replica]:
        if op.family not in {'allreduce', 'allgather', 'reduce_scatter', 'reducescatter'}:
            continue
        meta = dict(op.metadata)
        if op.layer is None:
            continue
        result[op.layer, meta.get('structure_block')].append({
            'op_id': op.op_id, 'family': op.family, 'recipe': op.recipe,
            'declared_link_bytes': op.link_bytes, 'link_scope': op.link_scope,
            'semantic_shape': list(op.semantic_shape), 'metadata': meta,
            'dependency_ids': list(op.deps), 'representative_dp_replica': replica,
            'basis': 'Sim declaration; not measured payload or observed HCCL algorithm'})
    return result


def tensor_witness(events, event, start, hidden):
    """Nearest completed hidden-width producer is evidence of a tensor, not a link."""
    dtypes = {'DT_BF16': 2, 'BF16': 2, 'DT_FLOAT16': 2, 'FLOAT16': 2,
              'DT_FLOAT': 4, 'FLOAT': 4, 'DT_INT8': 1, 'INT8': 1}
    for candidate in reversed(events):
        if candidate.start_ns < start or candidate.end_ns > event.start_ns or relevant(candidate):
            continue
        output = shapes(candidate.output_shapes)
        if not output or len(output[0]) != 2 or output[0][1] != hidden:
            continue
        dtype = candidate.output_dtypes.split(';')[0].strip().upper()
        if dtype not in dtypes:
            continue
        return {'locator': candidate.locator, 'op_type': candidate.op_type,
            'output_shape': output[0], 'output_dtype': dtype,
            'tensor_bytes': output[0][0] * output[0][1] * dtypes[dtype],
            'basis': 'observed preceding tensor; communication input association unproven',
            'measured_communication_payload': False}
    return None


def new_group(event, layer, block, header):
    return {'native_operator_type': event.op_type, 'implementation_name': event.name if category(event) != 'collective_envelope_only' else 'hcom_summary',
        'event_category': category(event), 'accelerator_core': event.core,
        'attention_kind': layer['attention'], 'block': block,
        'layer_population': 'layer0' if layer['layer_id'] == 0 else 'steady_layers',
        'durations': Counter(), 'layer_counts': Counter(), 'forward_counts': Counter(),
        'task_ids': Counter(), 'stream_ids': Counter(), 'tensor_status': Counter(),
        'pmu': NativePmu(header), 'source_programs': {}, 'preceding_tensor_bytes': Counter(),
        'preceding_tensor_examples': [], 'crossing_body_end_count': 0}


class HcclLedger:
    def __init__(self, actual, body, case, schema):
        self.actual, self.body, self.case, self.schema = actual, body, case, schema
        self.config = _model({**case.model.to_dict(), 'tp': case.runtime.parallel.tp,
                              **body.get('segmentation_options', {})})
        self.expected = [f for f in body['forwards'] if geometry_key(f['geometry']) == geometry_key(actual['geometry'])]
        if len(self.expected) != actual['forward_count']:
            raise ValueError('accepted_geometry_population_changed')
        self.declarations = declared_collectives(case, actual['geometry'], actual['conditional_context_tokens'])
        self.groups, self.counts, self.totals = {}, Counter(), defaultdict(Counter)
        self.summary_pairs, self.per_forward = [], []

    @classmethod
    def retained_windows(cls, config, schema, expected):
        """Use pre-exported Sim topology only; no physical-resource graph or cost."""
        self = cls.__new__(cls)
        self.actual, self.body, self.case = None, None, None
        self.schema, self.config, self.expected = schema, _model(config), expected
        self.declarations = {}
        self.groups, self.counts, self.totals = {}, Counter(), defaultdict(Counter)
        self.summary_pairs, self.per_forward = [], []
        return self

    def close(self, window, rows, raw):
        aligned, failure = _align(rows, self.config, window['forward_id'])
        if failure or any(aligned[k] != window[k] for k in
                ('start_ns', 'end_ns', 'head_start_ns', 'head_end_ns', 'query_rows', 'device_id')):
            raise ValueError(f'accepted_body_topology_changed:{window["forward_id"]}:{failure}')
        events = [row.event for row in rows]
        self.consume(window, aligned, events, raw)

    def consume(self, window, aligned, events, raw):
        rows = [_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)) for event in events]
        layers = [stage for stage in aligned['stages'] if stage['layer_id'] is not None]
        starts = [layer['start_ns'] for layer in layers]
        ffns = {}
        for layer in layers:
            local = [row for row in rows if layer['start_ns'] <= row.event.start_ns < layer['evidence']['successor_boundary_start_ns']]
            anchor = next(row.event.start_ns for row in local if _anchor(row, self.config))
            norm = next(i for i, row in enumerate(local) if row.event.start_ns > anchor and _norm(row, self.config['hidden_size']))
            ffns[layer['layer_id']] = local[_norm_start(local, norm, self.config['hidden_size'])].event.start_ns
        selected = [e for e in events if relevant(e) and window['start_ns'] <= e.start_ns < window['end_ns']]
        self.counts['raw_rows_starting_inside_body'] += len(selected)
        retained, duplicates = deduplicate_communication(selected)
        self.counts['exact_duplicate_summary_rows'] += len(duplicates)
        if len(self.summary_pairs) < 3:
            for duplicate in duplicates[:3-len(self.summary_pairs)]:
                partner = next(e for e in retained if (e.device_id,e.op_type,e.start_ns,e.end_ns) == (duplicate.device_id,duplicate.op_type,duplicate.start_ns,duplicate.end_ns))
                self.summary_pairs.append({'summary': {'locator': duplicate.locator, 'raw': raw[duplicate.locator['csv_line']]},
                    'concrete': {'locator': partner.locator, 'raw': raw[partner.locator['csv_line']]},
                    'basis': 'same device/type/start/end; no approximate temporal association'})
        intervals = defaultdict(list)
        for event in retained:
            layer = layers[bisect_right(starts, event.start_ns)-1]
            block = 'attention' if event.start_ns < ffns[layer['layer_id']] else 'ffn'
            event_category = category(event)
            implementation = event.name if event_category != 'collective_envelope_only' else 'hcom_summary'
            key = event.op_type, implementation, event_category, layer['attention'], block, layer['layer_id'] == 0
            if key not in self.groups:
                self.groups[key] = new_group(event, layer, block, self.schema.header)
            group = self.groups[key]
            group['durations'][event.duration_ns] += 1
            group['layer_counts'][layer['layer_id']] += 1
            group['forward_counts'][window['forward_id']] += 1
            group['task_ids'][event.task_id] += 1
            group['stream_ids'][event.stream_id] += 1
            group['tensor_status']['complete_descriptors' if shapes(event.input_shapes) and shapes(event.output_shapes) else 'missing_descriptors'] += 1
            group['pmu'].add(raw[event.locator['csv_line']], event, forward_id=window['forward_id'], layer_id=layer['layer_id'])
            group['crossing_body_end_count'] += event.end_ns > window['end_ns']
            intervals[event_category].append((event.start_ns, min(event.end_ns, window['end_ns'])))
            self.counts[event_category] += 1
            if event.op_type.startswith('hcom_') and event.end_ns <= window['end_ns']:
                self.totals[event.op_type][event.duration_ns] += 1
            if event.op_type.startswith('hcom_'):
                family = 'allreduce' if 'allReduce' in event.op_type else 'allgather' if 'allGather' in event.op_type else 'reduce_scatter' if 'reduceScatter' in event.op_type else None
                for op in self.declarations.get((layer['layer_id'], block), []):
                    if op['family'] == family:
                        # Retain one declaration per semantic role; do not sum DP copies.
                        role = op['op_id'].split('.', 2)[-1]
                        group['source_programs'].setdefault(role, op)
                witness = tensor_witness(events, event, layer['start_ns'] if block == 'attention' else ffns[layer['layer_id']], self.config['hidden_size'])
                if witness:
                    group['preceding_tensor_bytes'][witness['tensor_bytes']] += 1
                    if len(group['preceding_tensor_examples']) < 2:
                        group['preceding_tensor_examples'].append(witness)
        self.per_forward.append({'forward_id': window['forward_id'], 'start_ns': window['start_ns'], 'end_ns': window['end_ns'],
            'body_span_ns': window['end_ns']-window['start_ns'],
            'category_union_ns': {key: union_length(value) for key,value in intervals.items()},
            'category_activity_ns': {key: sum(b-a for a,b in value) for key,value in intervals.items()},
            'category_unions_are_not_additive': True})

    def finish(self):
        saved = defaultdict(Counter)
        for family in self.actual['families'] if self.actual is not None else []:
            if family['native_operator_type'].startswith('hcom_'):
                saved[family['native_operator_type']].update({int(ns):n for ns,n in family['duration_ns_counter']})
        if self.actual is not None and dict(saved) != dict(self.totals):
            raise ValueError('collective_histograms_differ_from_prior_complete_family_population')
        groups = []
        for group in self.groups.values():
            hist = group['durations']
            row = {k:v for k,v in group.items() if k not in {'durations','task_ids','stream_ids','pmu','source_programs','preceding_tensor_bytes'}}
            row.update(duration_ns_counter=sorted(hist.items()), observed_us=duration_stats(hist, 1000),
                calls_per_forward=sum(hist.values())/len(self.expected),
                activity_ms_per_forward=sum(ns*n for ns,n in hist.items())/1e6/len(self.expected),
                task_identity={'distinct_task_ids':len(group['task_ids']), 'missing_task_id_events':sum(n for v,n in group['task_ids'].items() if v.upper() in MISSING),
                    'repeated_task_id_count':sum(n>1 for v,n in group['task_ids'].items() if v.upper() not in MISSING),
                    'task_id_is_not_occurrence_identity':True}, stream_id_counter=sorted(group['stream_ids'].items()),
                raw_pmu=group['pmu'].result(), source_declared_programs=list(group['source_programs'].values()),
                preceding_tensor_byte_counter=sorted(group['preceding_tensor_bytes'].items()),
                measured_payload_bytes=None, observed_hccl_algorithm=None, parent_child_task_association=None,
                payload_evidence='communication tensor descriptors and explicit byte column unavailable; preceding tensor and Sim work are conditional only',
                communication_bandwidth_calibration_allowed=False, prior_rank_wait_cause_proven=False)
            groups.append(row)
        return sorted(groups, key=lambda row:-row['activity_ms_per_forward'])


def extract(actual_path, output):
    started = time.perf_counter(); pins = source_pins()
    actual = read(actual_path); actual_pin = identity(actual_path)
    body_pin = actual['body_acceptance_identity']
    if identity(body_pin['path']) != body_pin:
        raise ValueError('accepted_body_identity_changed')
    body = read(body_pin['path'])
    case_path = actual_path.with_name(actual_path.name.replace('.actual.json','.case.json'))
    case_pin = identity(case_path); case = parse_case(read(case_path))
    source = actual['source_identity']; path = Path(source['path']); source_pin = identity(path)
    if any(source_pin[k] != source[k] for k in ('path','sha256','size_bytes')):
        raise ValueError('source_identity_changed')
    stat = path.stat(); schema = probe_csv(path)
    ledger = HcclLedger(actual, body, case, schema)
    cursor, buffer, raw_buffer, scanned, previous = 0, [], {}, 0, None
    for event, raw in raw_stream(path, schema):
        scanned += 1
        if previous is not None and event.start_ns < previous:
            raise ValueError('chronological_source_required')
        previous = event.start_ns
        while cursor < len(ledger.expected) and event.start_ns > ledger.expected[cursor]['head_start_ns']:
            ledger.close(ledger.expected[cursor], buffer, raw_buffer)
            cursor += 1; buffer = []; raw_buffer = {}
        if cursor == len(ledger.expected):
            break
        window = ledger.expected[cursor]
        if window['start_ns'] <= event.start_ns <= window['head_start_ns']:
            buffer.append(_Row(event, shapes(event.input_shapes), shapes(event.output_shapes)))
            if raw is not None:
                raw_buffer[event.locator['csv_line']] = raw
            if len(buffer) > 100_000:
                raise MemoryError('retained_body_buffer_exceeds_100k_events')
    if cursor < len(ledger.expected):
        ledger.close(ledger.expected[cursor], buffer, raw_buffer); cursor += 1
    if cursor != len(ledger.expected):
        raise ValueError('accepted_body_population_not_fully_read')
    groups = ledger.finish()
    if source_pins() != pins or identity(case_path) != case_pin or identity(actual_path) != actual_pin:
        raise ValueError('local_source_or_declaration_changed')
    if (path.stat().st_size,path.stat().st_mtime_ns) != (stat.st_size,stat.st_mtime_ns):
        raise ValueError('capture_changed_during_scan')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    if rss > 512*1024**2:
        raise MemoryError('hccl_ledger_exceeds_512MiB')
    inventory = [{'path':str(p),'size_bytes':p.stat().st_size} for p in sorted(path.parent.rglob('*')) if p.is_file()]
    result = {'schema_version':'mindie-retained-body-hccl-ledger/1', 'case_id':actual['source_case_id'],
        'actual_identity':actual_pin,'body_acceptance_identity':body_pin,'source_identity':source,
        'case_identity':case_pin,'runtime_source_identity':pins,'geometry':actual['geometry'],
        'tp':case.runtime.parallel.tp,'hidden_size':case.model.hidden_size,'layers':case.model.layers,
        'forward_count':len(ledger.expected),'source_forward_count':actual.get('source_forward_count',len(body['forwards'])),
        'capture_inventory':inventory,'header':list(schema.header),'task_type_source':'Accelerator Core alias; no independent Task Type CSV column',
        'counts':dict(ledger.counts),'collective_histograms_match_prior_actual':True,
        'groups':groups,'summary_duplicate_examples':ledger.summary_pairs,'per_forward':ledger.per_forward,
        'collective_summary_device_exact_duplicate_rule':'same device/type/start/end and one missing task/stream row',
        'unlinked_aicpu_and_device_rows_not_added_to_collective_elapsed':True,
        'execution':{'raw_scans':1,'source_hash_reads':1,'parsed_rows':scanned,
            'scan_end':'after last selected Body vocabulary head; source remainder not parsed',
            'elapsed_seconds':time.perf_counter()-started,'maximum_resident_set_size_bytes':rss}}
    target = output / f'{actual["source_case_id"]}-hccl-ledger.json';write(target,result)
    print({'case':result['case_id'],'forwards':result['forward_count'],'counts':result['counts'],
           'seconds':round(result['execution']['elapsed_seconds'],3),'rss_mib':round(rss/1024**2,2)},flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actual',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    extract(args.actual,args.output_dir)


if __name__ == '__main__':
    main()
