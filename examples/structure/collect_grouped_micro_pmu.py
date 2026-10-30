"""Collect grouped-kernel PMU populations within accepted model bodies.

[Role] Preserve native ABI, topology role, BlockNum and complete PMU denominators.
[Invariants] Body endpoints and complete native histograms must equal retained
  evidence. Qwen up/down require a verified layer and GMM/DSQ/GMM call chain.
  Missing tensor descriptors and routing values are never manufactured.
[Timeouts & Locks] One active body, 180s CSV budget; serial sources; <=512 MiB.
[Side-Effect Policy] Existing local files only, no prediction or device calls.
"""
from bisect import bisect_right
from collections import Counter
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from collect_scalar_dma_pmu import identity, read, geometry
from mindie_profiler.decode_segmentation import _align, _anchor, _model, _norm, _norm_start, _Row
from mindie_profiler.native_tensor_abi import native_tensor_contract, native_contract_issue
from mindie_profiler.normalized import row_from_event, shapes
from mindie_profiler.sources_csv import probe_csv
from targeted_native_pmu import NativePmu, scan_rows

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/observations/sources'
INPUTS = DATA / 'arch3510-physical-services/grouped-inputs.json'
TARGETS = {'GroupedMatmul', 'GroupedMatmulSwigluQuantV2'}


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def prepare():
    # Metadata parsing happens once before collection. Workers use the serialized
    # existing Sim plans, so they do not import or hold a changing cost runtime.
    from mindie_sim.prediction.structure import parse_case
    entries = []
    for arch, labels in [('arch22', ('30_c2', '50_c2', '88_c8')), ('arch3510', (4, 64, 128))]:
        for label in labels:
            if arch == 'arch22':
                cid = f'a3_glm53_w4a8_tp16_tpot{label}'
                prior_path = ROOT / f'examples/structure/acceptance-20261030-service-qwen-a3/glm78-native/{cid}-native-partitions.json'
                prior = read(prior_path); case_path = Path(prior['case_identity']['path'])
                body_pin = prior['body_acceptance_identity']
            else:
                cid = f'qwen35-35b-a5-tp4-c{label}-graph'
                prior_path = ROOT / f'examples/structure/acceptance-20261030-qwen-source-native-operators/retained-six-actual/body-operator-{cid}-qwen-source-gdn-native.actual.json'
                prior = read(prior_path); case_path = prior_path.with_name(prior_path.name.replace('.actual.json', '.case.json'))
                body_pin = prior['body_acceptance_identity']
            raw = read(case_path); case = parse_case(raw); body = read(body_pin['path'])
            config = {**case.model.to_dict(), 'tp': case.runtime.parallel.tp, **body.get('segmentation_options', {})}
            declared = body['model_declaration']
            if any(config[k] != declared[k] for k in ('layers', 'hidden_size', 'vocab_size', 'tp')):
                raise ValueError('retained_model_declaration_differs')
            entries.append({'case_id': cid, 'architecture': arch, 'hardware': case.machine.sku,
                'prior_identity': identity(prior_path), 'case_identity': identity(case_path),
                'retained_case_identity': prior['case_identity'], 'source_identity': prior['source_identity'],
                'body_identity': body_pin, 'model_config': config, 'geometry': prior['geometry'],
                'forward_count': prior['forward_count'],
                'output': str(DATA / f'{arch}-physical-services/grouped-{cid}.json')})
    write(INPUTS, {'schema_version': 'mindie-grouped-micro-inputs/1', 'cases': entries,
                   'purpose': 'Existing Sim layer plans serialized for retained-window verification; no resource or cost graph.'})


def layer_roles(rows, config, layers):
    """Use verified whole-layer regions plus native producer/consumer sequence."""
    assignments = {}
    for layer in layers:
        if layer['kind'] != 'moe_layer':
            continue
        local = [r for r in rows if layer['start_ns'] <= r.event.start_ns < layer['evidence']['successor_boundary_start_ns']]
        anchor = next(r for r in local if _anchor(r, config))
        norm = next(i for i, r in enumerate(local) if r.event.start_ns > anchor.event.start_ns and _norm(r, config['hidden_size']))
        boundary = local[_norm_start(local, norm, config['hidden_size'])].event.start_ns
        chain = [r for r in local if r.event.start_ns >= boundary and r.kind in TARGETS | {'DequantSwigluQuant'}]
        if any(r.kind == 'GroupedMatmulSwigluQuantV2' for r in chain):
            # A3's routed activation is inside the named fused native call;
            # a separate shared-expert DSQ is outside this grouped chain.
            chain = [r for r in chain if r.kind in TARGETS]
        kinds = [r.kind for r in chain]
        if kinds == ['GroupedMatmul', 'DequantSwigluQuant', 'GroupedMatmul']:
            pairs = [(chain[0], 'expert_up'), (chain[2], 'expert_down')]
            basis = 'verified_moe_layer_GMM_DequantSwigluQuant_GMM_source_call_chain'
        elif kinds == ['GroupedMatmulSwigluQuantV2', 'GroupedMatmul']:
            pairs = [(chain[0], 'expert_up_activation_quant'), (chain[1], 'expert_down')]
            basis = 'verified_moe_layer_fused_up_then_grouped_down_source_call_chain'
        else:
            raise ValueError(f'grouped_layer_call_chain_differs:{layer["layer_id"]}:{kinds}')
        locators = [r.event.locator for r in chain]
        for row, role in pairs:
            assignments[row.event.locator['csv_line']] = (layer, role, basis, locators)
    return assignments


def collect(entry):
    started = time.perf_counter(); pins = {p: identity(ROOT / p) for p in (
        'examples/structure/collect_grouped_micro_pmu.py', 'examples/structure/targeted_native_pmu.py',
        'mindie_profiler/decode_segmentation.py')}
    prior = read(entry['prior_identity']['path']); body = read(entry['body_identity']['path'])
    for key in ('prior_identity', 'body_identity'):
        if identity(entry[key]['path']) != entry[key]: raise ValueError(key+'_changed')
    source = entry['source_identity']; path = Path(source['path']); source_pin = identity(path); stat = path.stat()
    if any(source_pin[k] != source[k] for k in ('path', 'sha256', 'size_bytes')): raise ValueError('capture_identity_changed')
    config = _model(entry['model_config'])
    expected = [w for w in body['forwards'] if geometry(w['geometry']) == geometry(entry['geometry'])]
    if len(expected) != entry['forward_count']: raise ValueError('retained_forward_count_changed')
    schema = probe_csv(path); groups = {}; totals = {k: Counter() for k in TARGETS}; old_abi = Counter(); new_abi = Counter()
    buffer = []; raw_buffer = {}; cursor = 0; counts = Counter()

    def close(window):
        aligned, failure = _align(buffer, config, cursor)
        if failure or any(aligned[k] != window[k] for k in ('start_ns', 'end_ns', 'head_start_ns', 'head_end_ns', 'query_rows', 'device_id')):
            raise ValueError(f'retained_body_endpoint_changed:{window["forward_id"]}:{failure}')
        layers = [s for s in aligned['stages'] if s['layer_id'] is not None]
        roles = layer_roles(buffer, config, layers); ordinal = Counter()
        for row in buffer:
            event = row.event
            if row.kind not in TARGETS or not window['start_ns'] <= event.start_ns < window['end_ns'] or event.end_ns > window['end_ns']:
                continue
            layer, role, basis, chain = roles[event.locator['csv_line']]
            raw = raw_buffer[event.locator['csv_line']]; kernel = row_from_event(event)
            abi = native_tensor_contract(kernel); ordinal_key = (layer['layer_id'], row.kind); ordinal[ordinal_key] += 1
            abi_key = json.dumps([row.kind, abi, layer['attention'], 'ffn', ordinal[ordinal_key]], sort_keys=True)
            new_abi[(abi_key, event.duration_ns)] += 1
            fields = {k: raw.get(k) for k in ('Input Shapes', 'Input Data Types', 'Input Formats', 'Output Shapes', 'Output Data Types', 'Output Formats')}
            key = json.dumps([row.kind, abi, fields, layer['attention'], role, raw.get('Accelerator Core'), raw.get('Block Num'), raw.get('Mix Block Num')], sort_keys=True)
            if key not in groups:
                if len(groups) >= 2048: raise MemoryError('grouped_partition_budget_exceeded')
                groups[key] = {'native_operator_type': row.kind, 'native_abi': abi,
                    'native_abi_issue': native_contract_issue(kernel), 'raw_tensor_fields': fields,
                    'attention_kind': layer['attention'], 'role': role, 'role_basis': basis,
                    'accelerator_core': raw.get('Accelerator Core'), 'block_num': raw.get('Block Num'), 'mix_block_num': raw.get('Mix Block Num'),
                    'duration_ns_counter': Counter(), 'layer_counts': Counter(), 'forward_counts': Counter(),
                    'raw_pmu': NativePmu(schema.header), 'source_chain_examples': []}
            g = groups[key]; g['duration_ns_counter'][event.duration_ns] += 1
            g['layer_counts'][layer['layer_id']] += 1; g['forward_counts'][window['forward_id']] += 1
            g['raw_pmu'].add(raw, event, forward_id=window['forward_id'], layer_id=layer['layer_id'])
            if len(g['source_chain_examples']) < 2: g['source_chain_examples'].append(chain)
            totals[row.kind][event.duration_ns] += 1

    last = None
    for kernel, raw in scan_rows(path, schema, TARGETS):
        e = kernel.event; counts['parsed_rows'] += 1
        if last is not None and e.start_ns < last: raise ValueError('nonchronological_capture')
        last = e.start_ns
        while cursor < len(expected) and e.start_ns > expected[cursor]['head_start_ns']:
            close(expected[cursor]); buffer.clear(); raw_buffer.clear(); cursor += 1
        if cursor == len(expected): break
        if expected[cursor]['start_ns'] <= e.start_ns <= expected[cursor]['head_start_ns']:
            buffer.append(_Row(e, shapes(e.input_shapes), shapes(e.output_shapes)))
            if raw is not None: raw_buffer[e.locator['csv_line']] = raw
            if len(buffer) > 100_000: raise MemoryError('active_body_limit_exceeded')
    if cursor < len(expected): close(expected[cursor]); cursor += 1
    if cursor != len(expected): raise ValueError('retained_bodies_not_all_read')
    wanted = {k: Counter() for k in TARGETS}
    for family in prior['families']:
        if family['native_operator_type'] in wanted: wanted[family['native_operator_type']].update(dict(family['duration_ns_counter']))
    if wanted != totals: raise ValueError('full_native_histogram_changed')
    if entry['architecture'] == 'arch22':
        for g in prior['partitions']:
            if g['native_operator_type'] not in TARGETS: continue
            key = json.dumps([g['native_operator_type'], g['native_abi'], g['attention_kind'], g['topology_region'], g['native_type_ordinal_in_region']], sort_keys=True)
            old_abi.update({(key, ns): n for ns, n in g['duration_ns_counter']})
        if old_abi != new_abi: raise ValueError('retained_A3_ABI_partition_histogram_changed')
    parts = []
    for g in groups.values():
        parts.append({**g, 'duration_ns_counter': sorted(g['duration_ns_counter'].items()),
            'layer_counts': dict(g['layer_counts']), 'forward_counts': dict(g['forward_counts']), 'raw_pmu': g['raw_pmu'].result()})
    if any(identity(ROOT / p) != pin for p, pin in pins.items()): raise ValueError('extractor_changed')
    if (path.stat().st_size, path.stat().st_mtime_ns) != (stat.st_size, stat.st_mtime_ns): raise ValueError('capture_changed')
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    if peak > 512*1024**2: raise MemoryError('grouped_extraction_exceeds_512MiB')
    result = {'schema_version': 'mindie-grouped-micro-pmu/1', 'case_id': entry['case_id'], 'architecture': entry['architecture'],
        'hardware': entry['hardware'], 'source_identity': source_pin, 'prior_identity': entry['prior_identity'],
        'body_identity': entry['body_identity'], 'case_identity': entry['case_identity'], 'inputs_identity': identity(INPUTS),
        'geometry': entry['geometry'], 'forward_count': len(expected), 'partitions': parts,
        'complete_native_histograms_match_prior': True, 'A3_complete_ABI_partition_histograms_match_prior': entry['architecture'] == 'arch22',
        'native_counts': {k: sum(v.values()) for k,v in totals.items()}, 'runtime_sources': pins,
        'execution': {'source_passes': 1, 'predictions': 0, 'elapsed_seconds': time.perf_counter()-started, 'peak_rss_bytes': peak, **counts},
        'limitations': ['Source call-chain role is conditional on independently verified complete layer topology, not Host identity.',
            'Native N/A ABI remains absent; buffer capacity is not active routed rows.', 'PMU pipes overlap; no exclusive latency partition or descriptor unit price is implied.']}
    write(entry['output'], result)
    print(json.dumps({'case_id': entry['case_id'], 'forwards': len(expected), 'partitions': len(parts), 'native_counts': result['native_counts'], 'execution': result['execution']}), flush=True)


def main():
    p = argparse.ArgumentParser(); p.add_argument('--prepare', action='store_true'); p.add_argument('--case-id'); p.add_argument('--batch', action='store_true'); a = p.parse_args()
    if a.prepare: prepare(); return
    entries = read(INPUTS)['cases']
    if a.case_id: collect(next(e for e in entries if e['case_id'] == a.case_id)); return
    if not a.batch: p.error('select --prepare, --case-id or --batch')
    results = []
    for entry in entries:
        result = subprocess.run([sys.executable, __file__, '--case-id', entry['case_id']], text=True, capture_output=True, timeout=190, cwd=ROOT)
        log = Path(entry['output']).with_suffix('.run.log'); log.write_text(result.stdout+result.stderr)
        if result.returncode: raise RuntimeError('grouped_extraction_failed:see '+str(log))
        saved = read(entry['output']); results.append({'case_id': entry['case_id'], 'output_identity': identity(entry['output']), 'execution': saved['execution']})
        print(result.stdout, end='', flush=True)
    write(DATA / 'arch3510-physical-services/grouped-extraction-receipt.json', {'schema_version': 'mindie-grouped-micro-batch/1',
        'status': 'completed', 'inputs_identity': identity(INPUTS), 'cases': results, 'raw_source_passes': len(results), 'new_cost_calls': 0})


if __name__ == '__main__': main()
