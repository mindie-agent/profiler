"""Retain full native ABI populations in already accepted V4.1 Body windows.

[Role] Fill missing matrix, rotary and cache-store evidence with one local pass.
[Invariants] Complete shared-frontend alignment must reproduce every retained
  endpoint and the full prior family histogram. Names never determine layers.
  Full native descriptors and layer plans define buckets, not two examples.
[Timeouts & Locks] One active forward; 180 s bounded CSV scan, <=512 MiB RSS.
[Side-Effect Policy] Local reads and a separate evidence artifact only.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import resource
import sys
import time

from mindie_profiler.decode_segmentation import auto_segment_decode_forwards, _anchor, _Row
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows, row_from_event, shapes
from mindie_sim.prediction.structure import parse_case
from replay_body_operator_families import duration_stats, geometry_key, identity, read, runtime_identity, write

TYPES = ('TransposeQuantBatchMatMul', 'InplacePartialRotaryMul', 'KvCompressEpilogV2')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def plan_signature(plan):
    # Ownership/compression changes semantic work. The ordinal is retained as
    # membership, not part of homogeneous-work bucketing.
    return {key: value for key, value in plan.items() if key != 'index'}


class NativeConsumer:
    def __init__(self, actual, body, config):
        self.actual, self.config = actual, config
        key = geometry_key(actual['geometry'])
        self.expected = {row['forward_id']:row for row in body['forwards'] if geometry_key(row['geometry']) == key}
        if len(self.expected) != actual['forward_count']:
            raise ValueError('retained_geometry_population_changed')
        self.partitions = {}; self.totals = {kind:Counter() for kind in TYPES}; self.seen = set()

    def __call__(self, result, events):
        fid = result['forward_id']
        if fid not in self.expected:
            return
        expected = self.expected[fid]
        if any(result[key] != expected[key] for key in ('start_ns','end_ns','head_start_ns','head_end_ns','query_rows','device_id','geometry')):
            raise ValueError('retained_complete_body_boundary_changed:' + fid)
        if fid in self.seen:
            raise ValueError('duplicate_complete_forward')
        self.seen.add(fid)
        layers = [row for row in result['stages'] if row['layer_id'] is not None]
        starts = [row['start_ns'] for row in layers]
        anchors = {}
        # Device start order is used only within an already validated whole
        # layer topology, never to infer the number or identity of layers.
        for event in events:
            if not result['start_ns'] <= event.start_ns < result['end_ns']:
                continue
            index = bisect_right(starts,event.start_ns)-1
            row = _Row(event,shapes(event.input_shapes),shapes(event.output_shapes))
            if _anchor(row,self.config): anchors[layers[index]['layer_id']] = event.start_ns
        if len(anchors) != len(layers):
            raise ValueError('layer_anchor_population_changed')
        ordinals = Counter()
        for event in events:
            if event.op_type not in self.totals or not result['start_ns'] <= event.start_ns < result['end_ns'] or event.end_ns > result['end_ns']:
                continue
            layer = layers[bisect_right(starts,event.start_ns)-1]; lid = layer['layer_id']
            region = 'before_attention_anchor' if event.start_ns < anchors[lid] else 'after_attention_anchor'
            native = native_tensor_contract(row_from_event(event))
            ordinal_key = (lid,region,event.op_type,canonical(native))
            ordinals[ordinal_key] += 1
            plan = plan_signature(self.config['layer_plans'][lid])
            key = canonical((event.op_type,native,region,ordinals[ordinal_key],plan))
            group = self.partitions.setdefault(key, {
                'native_operator_type':event.op_type,'native_abi':native,'topology_region':region,
                'same_abi_ordinal_in_region':ordinals[ordinal_key], 'layer_plan':plan,
                'role_basis':'complete_native_abi_conditioned_on_verified_whole_layer_region',
                'duration_ns_counter':Counter(),'layer_counts':Counter(),'forward_counts':Counter(),'examples':[]})
            group['duration_ns_counter'][event.duration_ns] += 1
            group['layer_counts'][lid] += 1; group['forward_counts'][fid] += 1
            self.totals[event.op_type][event.duration_ns] += 1
            if len(group['examples']) < 2:
                group['examples'].append({'locator':event.locator,'forward_id':fid,'layer_id':lid,
                    'start_ns':event.start_ns,'end_ns':event.end_ns})

    def finish(self):
        if self.seen != set(self.expected): raise ValueError('retained_forward_population_not_reproduced')
        saved = {kind:Counter() for kind in TYPES}
        for family in self.actual['families']:
            if family['native_operator_type'] in saved:
                saved[family['native_operator_type']].update(dict(family['duration_ns_counter']))
        if saved != self.totals: raise ValueError('full_native_family_histogram_drift')
        groups = []
        for group in self.partitions.values():
            hist = group['duration_ns_counter']
            groups.append({**group,'duration_ns_counter':sorted(hist.items()),
                'layer_counts':dict(group['layer_counts']),'forward_counts':dict(group['forward_counts']),
                'observed_us':duration_stats(hist,1000),
                'observed_activity_ms_per_forward':sum(ns*n for ns,n in hist.items())/1e6/len(self.seen)})
        return sorted(groups,key=lambda g:-g['observed_activity_ms_per_forward'])


def extract(actual_path, case_path, output):
    started = time.perf_counter(); before = runtime_identity(); helper = identity(Path(__file__).resolve())
    actual = read(actual_path); actual_pin = identity(actual_path)
    body_pin = actual['body_acceptance_identity']
    if identity(body_pin['path']) != body_pin: raise ValueError('retained_body_artifact_changed')
    body = read(body_pin['path']); source = actual['source_identity']; path = Path(source['path'])
    source_now = identity(path)
    if any(source_now[k] != source[k] for k in ('path','sha256','size_bytes')): raise ValueError('source_changed')
    stat_before = path.stat(); case_pin = identity(case_path); case = parse_case(read(case_path))
    config = {**case.model.to_dict(),'tp':case.runtime.parallel.tp,**body.get('segmentation_options',{})}
    config['layer_plans'] = [asdict(p) if not isinstance(p,dict) else p for p in config['layer_plans']]
    consumer = NativeConsumer(actual,body,config)
    auto_segment_decode_forwards(kernel_rows(path,rank_id='rank_0',rank_index=0,max_rows=5_000_000,timeout_s=180),
        config,on_forward=consumer,max_detailed_forwards=0,max_samples_per_layer=0)
    groups = consumer.finish()
    if runtime_identity() != before or identity(case_path) != case_pin or identity(Path(__file__).resolve()) != helper:
        raise ValueError('runtime_or_case_changed')
    if (path.stat().st_size,path.stat().st_mtime_ns) != (stat_before.st_size,stat_before.st_mtime_ns): raise ValueError('capture_changed_during_scan')
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    if rss > 512*1024**2: raise MemoryError('native_partition_scan_exceeds_512_mib')
    result = {'schema_version':'mindie-body-native-partitions/1','source_case_id':actual['source_case_id'],
        'source_identity':source,'actual_identity':actual_pin,'body_acceptance_identity':body_pin,
        'case_identity':case_pin,'runtime_source_identity':before,'extractor_identity':helper,
        'geometry':actual['geometry'],'conditional_context_tokens':actual['conditional_context_tokens'],
        'forward_count':len(consumer.seen),'selected_native_types':TYPES,
        'native_event_count':sum(sum(v.values()) for v in consumer.totals.values()),
        'native_family_counts':{k:sum(v.values()) for k,v in consumer.totals.items()},
        'saved_native_family_histograms_exactly_equal':True,'all_body_endpoints_exactly_equal':True,
        'partitions':groups,'execution':{'raw_targeted_scans':1,'source_hash_reads':1,
            'elapsed_seconds':time.perf_counter()-started,'maximum_resident_set_size_bytes':rss},
        'interpretation':'All accepted body windows and full native populations are preserved. Native scalar/slot values remain unobserved; whole-layer alignment is conditional, not Host occurrence evidence.'}
    output.mkdir(parents=True,exist_ok=True)
    dest=output/(actual['source_case_id']+'-native-partitions.json');write(dest,result)
    print(json.dumps({'case':result['source_case_id'],'forwards':result['forward_count'],
        'events':result['native_family_counts'],'partitions':len(groups),'rss':rss,'elapsed_s':result['execution']['elapsed_seconds']}),flush=True)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--actual',type=Path,required=True);parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();extract(args.actual,args.case,args.output_dir)
