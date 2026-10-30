"""[Role] Build four mechanism ledgers from a fixed current scoreboard.
[Invariants] Actual populations are unique; partial costs never cover missing
  calls. Strict and reference overlap is explicit. Activity is not Body time.
[Timeouts & Locks] Stream Git/large receipts; one retained actual at a time,
  no raw profiling or cost evaluation, no locks; Git waits bounded to 30s.
[Side-Effect Policy] Write a separate JSON/Markdown ledger only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

import ijson

ROOT = Path(__file__).resolve().parents[2]
SCOREBOARD = 'examples/structure/acceptance-20261030-priority/priority-three-level-scoreboard.json'
CLUSTERS = {
    'A': 'MC2 dispatch / combine',
    'B': 'conv_state_copy / MoeInitRoutingV3',
    'C': 'small-M grouped matmul / DequantSwigluQuant',
    'D': 'HCCL data-plane / collective envelopes',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def population(row):
    g = row.get('geometry') or {}
    return (row['source_identity']['sha256'], g.get('query_rows'),
            g.get('tokens_per_sequence'), g.get('sequences_per_replica'))


def classify(native):
    if native.startswith(('MoeDistributeDispatch', 'MoeDistributeCombine')) or native == 'DispatchFFNCombine':
        return 'A'
    if native in {'_copy_conv_state_kernel', 'MoeInitRoutingV3'}:
        return 'B'
    if native.startswith(('GroupedMatmul', 'DequantSwigluQuant')):
        return 'C'
    if native.startswith('hcom_'):
        return 'D'
    return None


def identity(path):
    p = Path(path); digest = hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(p.resolve()), 'sha256': digest.hexdigest(), 'size_bytes': p.stat().st_size}


def read(path):
    p = Path(path)
    if p.stat().st_size > 50 * 1024**2:
        raise ValueError('metadata_read_exceeds_50_MiB:' + str(p))
    return json.loads(p.read_text())


class HashReader(io.RawIOBase):
    def __init__(self, stream):
        self.stream, self.digest = stream, hashlib.sha256()
        self.size = 0

    def readable(self):
        return True

    def readinto(self, target):
        data = self.stream.read(len(target))
        target[:len(data)] = data
        self.digest.update(data); self.size += len(data)
        return len(data)


def fixed_sections(commit):
    names = {'current_body_comparisons', 'current_operator_families',
             'current_operator_cohorts', 'current_source_role_references'}
    result = {key: [] for key in names}
    command = ['git', 'show', commit + ':' + SCOREBOARD]
    with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        source = HashReader(proc.stdout); active = None; builder = None
        for prefix, event, value in ijson.parse(source, use_float=True):
            if active is not None:
                builder.event(event, value)
                if prefix == active and event == 'end_map':
                    row = builder.value
                    if active.startswith('current_body_comparisons'):
                        row.pop('per_layer', None)
                    result[active.split('.')[0]].append(row)
                    active = builder = None
            elif event == 'start_map' and prefix.endswith('.item') and prefix.split('.')[0] in names:
                active = prefix; builder = ijson.ObjectBuilder(); builder.event(event, value)
        if proc.wait(timeout=30):
            raise RuntimeError('git_scoreboard_read_failed:' + proc.stderr.read(2000).decode())
    full_commit = subprocess.check_output(['git', 'rev-parse', commit], cwd=ROOT, timeout=5).decode().strip()
    return result, {'git_commit': full_commit, 'repository': str(ROOT), 'path': SCOREBOARD,
                    'sha256': source.digest.hexdigest(), 'size_bytes': source.size}


def choose_cases(rows):
    complete = [r for r in rows if r['comparison']['status'] == 'compared']
    selected = []
    for r in complete:
        cid = r['case_id']; a5 = '/a5/' in r['source_identity']['path']
        group = None
        if a5 and cid.startswith('a5_kimi_tp8_e16_bf16_'):
            group = 'A5 Kimi BF16 (12)'
        elif a5 and cid.startswith('a5_v41_'):
            group = 'A5 V4.1 (7)'
        elif a5 and 'glm53flash' in cid and not r['comparison']['passed']:
            group = 'A5 GLM Flash failed (9)'
        elif cid.startswith('qwen35-35b-a5-tp4-'):
            group = 'A5 Qwen3.5 TP4 (3)'
        elif cid.startswith('qwen36-a5-tp2-'):
            group = 'A5 Qwen3.6 TP2 (3)'
        if group:
            selected.append({**r, 'selection_group': group})
    failed_a3 = [r for r in complete if '/a3/' in r['source_identity']['path'] and not r['comparison']['passed']]
    def margin(r):
        c = r['comparison']
        return abs(c['predicted_ms'] - c['observed_ms']['mean']) - .15 * c['observed_ms']['mean']
    def relative_margin(r):
        return abs(r['comparison']['relative_error']) - .15
    ranked = sorted(failed_a3, key=lambda r: (relative_margin(r), r['case_id']))
    required = ('v4flash-a3-tp8-c4:', 'a3_kimi4_tp8_w4a8_c32:')
    boundary = [next(r for r in ranked if r['case_id'].startswith(prefix)) for prefix in required]
    boundary += [r for r in ranked if r not in boundary][:2]
    for rank, r in enumerate(boundary, 1):
        selected.append({**r, 'selection_group': 'A3 nearest failed boundary (4)',
                         'boundary_selection_rank': rank, 'absolute_ms_to_15pct_boundary': margin(r)})
    if Counter(r['selection_group'] for r in selected) != {
            'A5 Kimi BF16 (12)': 12, 'A5 V4.1 (7)': 7, 'A5 GLM Flash failed (9)': 9,
            'A5 Qwen3.5 TP4 (3)': 3, 'A5 Qwen3.6 TP2 (3)': 3, 'A3 nearest failed boundary (4)': 4}:
        raise ValueError('requested_fixed_baseline_population_differs')
    return selected, [{'case_id': r['case_id'], 'absolute_ms_to_15pct_boundary': margin(r),
                      'relative_margin_above_15pct': relative_margin(r)} for r in ranked]


def histogram(value):
    return Counter({int(ns): int(n) for ns, n in value})


def stats(hist):
    count = sum(hist.values()); elapsed = sum(ns * n for ns, n in hist.items())
    if not count:
        return None
    ordered = sorted(hist.items())
    def at(index):
        total = 0
        for ns, n in ordered:
            total += n
            if total > index:
                return ns
        raise AssertionError('histogram_quantile_index')
    return {'count': count, 'mean': elapsed / count / 1000,
            'p50': (at((count - 1) // 2) + at(count // 2)) / 2000,
            'activity_sum_ns': elapsed}


def check_stats(hist, observed):
    got = stats(hist)
    if got is None or got['count'] != observed['count'] or abs(got['mean'] - observed['mean']) > 1e-7:
        raise ValueError('retained_full_histogram_does_not_match_current_population')


def family_key(row):
    return row['receipt']['sha256'], row['case_id'], row['native_operator_type'], row['declared_role']


def compact_pin(pin):
    return {k: pin[k] for k in ('path', 'sha256', 'size_bytes') if k in pin}


def source_role_partition(raw, actual, actual_pin):
    """Resolve saved observation IDs in their actual-file namespace."""
    retained_id = raw.get('retained_observation_group_id') or raw.get('retained_group_id')
    members = ([retained_id] if retained_id else raw.get('partition_indices', [raw.get('partition_index')]))
    groups = {g['group_id']: g for g in actual['source_role_references']}
    pooled, layers = Counter(), set()
    for member in members:
        saved = groups[member]
        if saved['native_operator_type'] != raw['native_operator_type']:
            raise ValueError('source_role_partition_native_differs')
        pooled.update(histogram(saved['duration_ns_counter']))
        layers.update(saved['layer_ids'])
    if pooled != histogram(raw['duration_ns_counter']) or layers != set(raw['layer_ids']):
        raise ValueError('source_role_partition_population_differs')
    return {'partition_identity': compact_pin(actual_pin), 'partition_kind': 'source_role_group',
            'partition_members': members}


def linked_case_data(sections, chosen):
    selected_pops = {population(row) for row in chosen}
    families = [r for r in sections['current_operator_families']
                if population(r) in selected_pops and classify(r['native_operator_type'])]
    references = [r for r in sections['current_source_role_references']
                  if population(r) in selected_pops and classify(r['native_operator_type'])]
    wanted = defaultdict(set); pins = {}
    for row in [*families, *references]:
        path = row['receipt']['path']; wanted[path].add(row['case_id']); pins[path] = row['receipt']
    histograms, matched, reference_data = {}, {}, {}
    actual_reads = 0
    for path, case_ids in wanted.items():
        if identity(path)['sha256'] != pins[path]['sha256']:
            raise ValueError('fixed_linked_receipt_changed:' + path)
        with Path(path).open('rb') as stream:
            for case in ijson.items(stream, 'cases.item', use_float=True):
                if case['case_id'] not in case_ids:
                    continue
                local_f = [r for r in families if r['receipt']['path'] == path and r['case_id'] == case['case_id']]
                local_r = [r for r in references if r['receipt']['path'] == path and r['case_id'] == case['case_id']]
                actual = None
                if local_f or any(r.get('reference_origin') != 'external_native_partition' for r in local_r):
                    actual_pin = case.get('actual_identity')
                    if actual_pin:
                        if identity(actual_pin['path'])['sha256'] != actual_pin['sha256']:
                            raise ValueError('fixed_actual_changed')
                        actual = read(actual_pin['path']); actual_reads += 1
                for row in local_f:
                    key = family_key(row)
                    raw_f = next(f for f in case['families'] if (f['native_operator_type'], f['declared_role']) == key[2:])
                    raw_a = raw_f if 'duration_ns_counter' in raw_f else next((f for f in actual['families']
                        if (f['native_operator_type'], f['declared_role']) == key[2:]), None) if actual else None
                    if raw_a is None:
                        raise ValueError('current_native_family_histogram_missing:' + str(key))
                    h = histogram(raw_a['duration_ns_counter']); check_stats(h, row['observed_us'])
                    histograms[key] = (h, compact_pin(case.get('actual_identity') or row['receipt']))
                    for co in raw_f.get('cohorts', []):
                        matched[(key, co['cohort_id'])] = co
                for index, row in enumerate(local_r):
                    entry = {'row': row, 'histogram': None, 'raw': None, 'histogram_basis': None,
                             'partition_identity': case.get('partition_identity') or case.get('actual_identity'),
                             'partition_kind': None, 'partition_members': []}
                    if row.get('reference_origin') == 'external_native_partition':
                        raw = next(g for g in case['groups'] if g['group_id'] == row['group_id'])
                        entry.update(raw=raw, histogram=histogram(raw['duration_ns_counter']),
                                     histogram_basis='complete_retained_native_group')
                        members = raw.get('partition_indices', [raw.get('partition_index')])
                        retained_id = raw.get('retained_observation_group_id') or raw.get('retained_group_id')
                        if (isinstance(retained_id, str) and retained_id.startswith('sha256:')) or any(
                                isinstance(m, str) and m.startswith('sha256:') for m in members):
                            if actual is None:
                                actual_pin = case['actual_identity']
                                if identity(actual_pin['path'])['sha256'] != actual_pin['sha256']:
                                    raise ValueError('fixed_actual_changed')
                                actual = read(actual_pin['path']); actual_reads += 1
                            entry.update(source_role_partition(raw, actual, case['actual_identity']))
                        elif raw.get('partition_indices') is not None or raw.get('partition_index') is not None:
                            entry.update(partition_kind='native_partition_indices',
                                partition_members=raw.get('partition_indices', [raw.get('partition_index')]))
                        elif raw.get('retained_group_id') is not None:
                            entry.update(partition_kind='retained_group', partition_members=[raw['retained_group_id']])
                        elif raw.get('retained_cohort_id') is not None:
                            entry.update(partition_kind='retained_cohort', partition_members=[raw['retained_cohort_id']])
                    else:
                        candidates = [g for f in case.get('families', []) for g in f.get('conditional_source_role_references', [])
                                      if g['native_operator_type'] == row['native_operator_type']
                                      and g['declared_role'] in row['declared_roles']
                                      and g.get('layer_ids') == row.get('layer_ids')]
                        candidates = [g for g in candidates if g['observed_us'] == row['observed_us']]
                        if len(candidates) == 1:
                            raw = candidates[0]; entry['raw'] = raw
                            old_id = raw.get('frozen_native_rebind', {}).get('original_observation_group_id')
                            saved = [g for g in (actual or {}).get('source_role_references', [])
                                     if g['group_id'] in {raw['group_id'], old_id}]
                            if len(saved) == 1 and 'duration_ns_counter' in saved[0]:
                                entry.update(histogram=histogram(saved[0]['duration_ns_counter']),
                                             histogram_basis='original_retained_source_role_group',
                                             partition_kind='source_role_group', partition_members=[saved[0]['group_id']])
                            elif actual:
                                fs = [f for f in actual['families'] if f['native_operator_type'] == row['native_operator_type']
                                      and f['declared_role'] in row['declared_roles']
                                      and f['observed_us']['count'] == row['observed_us']['count']]
                                if len(fs) == 1:
                                    entry.update(histogram=histogram(fs[0]['duration_ns_counter']),
                                                 histogram_basis='complete_same_role_family_population',
                                                 partition_kind='complete_family',
                                                 partition_members=[(fs[0]['native_operator_type'], fs[0]['declared_role'])])
                    if entry['histogram'] is not None:
                        check_stats(entry['histogram'], row['observed_us'])
                    reference_data[id(row)] = entry
                del actual
    return families, references, histograms, matched, reference_data, actual_reads


def measured_hccl_supplements(chosen, families, histograms):
    """Use retained complete Body HCCL histograms where main has no operators.

    This adds measured populations only; neither a missing canonical family
    nor a communication-program name establishes a Sim program or its service.
    """
    present = {population(row) for row in families}
    directory = ROOT / 'examples/structure/acceptance-20261030-hccl-66'
    inputs = read(directory / 'inputs.json')
    by_source = {row['source']['sha256']: row for row in inputs['cases']}
    map_path = ROOT / 'examples/structure/acceptance-20261030-controller-alias/extraction-generation-map.json'
    generation = {row['case_id']: row for row in read(map_path)['cases']}
    supplements = []
    for body in chosen:
        if population(body) in present:
            continue
        source = by_source[body['source_identity']['sha256']]
        path = directory / (source['case_id'] + '-capture-hccl.json')
        ledger = read(path); pin = identity(path)
        if ledger['source_identity']['sha256'] != body['source_identity']['sha256']:
            raise ValueError('supplement_hccl_source_differs')
        geometry = next(g for g in ledger['body_geometry_groups'] if
                        tuple(g['geometry'].get(k) for k in ('query_rows', 'tokens_per_sequence', 'sequences_per_replica')) == population(body)[1:])
        if geometry['forward_count'] != body['comparison']['observed_forward_count']:
            raise ValueError('supplement_hccl_body_population_differs')
        reuse = generation[source['case_id']]
        if not reuse['body_operator_population_reusable'] or reuse['previous_extraction_identity']['sha256'] != ledger['body_acceptance_identity']['sha256']:
            raise ValueError('retained_hccl_population_not_proven_reusable_after_controller_correction')
        added = []
        for index, group in enumerate(geometry['groups']):
            if group['event_category'] not in {'collective_device_task', 'collective_envelope_only', 'native_fused_communication_program'}:
                continue
            if classify(group['native_operator_type']) not in {'A', 'D'}:
                continue
            row = {'case_id': body['case_id'], 'receipt': pin, 'source_identity': body['source_identity'],
                'geometry': body['geometry'], 'forward_count': geometry['forward_count'],
                'native_operator_type': group['native_operator_type'],
                'declared_role': f"retained:{group['block']}:{group['attention_kind']}:group{index}",
                'observed_us': group['observed_us'],
                'runtime_identity': {'recorded_sim_file_map_sha256': None, 'basis': 'measured_supplement_has_no_Sim_cost'},
                'measurement_origin': 'retained_complete_body_hccl_population; not a canonical operator prediction'}
            h = histogram(group['duration_ns_counter']); check_stats(h, row['observed_us'])
            histograms[family_key(row)] = (h, pin)
            families.append(row); added.append({'native': row['native_operator_type'], 'group_index': index,
                                               'event_count': row['observed_us']['count']})
        supplements.append({'case_id': body['case_id'], 'ledger_identity': pin,
            'controller_corrected_generation_map_identity': identity(map_path),
            'current_extraction_identity': reuse['extraction_identity'],
            'canonical_operator_population_available': False, 'added_measured_groups': added,
            'unavailable_mechanism_families_not_zero': ['B', 'C'],
            'forward_count': geometry['forward_count'], 'new_raw_reads': 0, 'new_costs': 0})
    return supplements


def reference_entry(entry, forwards):
    row = entry['row']; raw = entry['raw'] or {}; hist = entry['histogram']
    count = row['observed_us']['count']; predicted = row.get('predicted_reference_us')
    value = {'kind': 'conditional_reference', 'native_operator_type': row['native_operator_type'],
        'roles': row['declared_roles'], 'layer_ids': row.get('layer_ids'),
        'observed_us': row['observed_us'], 'calls_per_forward': count / forwards,
        'predicted_us': predicted, 'observed_activity_ms_per_forward': row['observed_activity_ms_per_forward'],
        'predicted_activity_ms_per_forward': row.get('predicted_service_ms_per_forward'),
        'signed_activity_residual_ms_per_forward': row.get('reference_residual_ms_per_forward'),
        'receipt': row['receipt'], 'runtime_identity': row['runtime_identity'],
        'group_id': raw.get('group_id'), 'physical_program_signatures': row.get('physical_program_signatures'),
        'observation_identity_domain': row.get('observation_identity_domain', 'embedded_source_role'),
        'source_correspondence': row.get('source_correspondence'), 'conditions': row.get('conditions'),
        'boundary': row.get('boundary'), 'strict_accuracy_implied': False,
        'additional_budget_allowed': False, 'histogram_basis': entry['histogram_basis'],
        'population_partition_identity': entry['partition_identity'],
        'population_partition_kind': entry['partition_kind'],
        'population_partition_members': entry['partition_members'],
        'duration_ns_counter': sorted(hist.items()) if hist is not None else None}
    if predicted is not None and abs(predicted * count / forwards / 1000 - value['predicted_activity_ms_per_forward']) > 1e-7:
        raise ValueError('reference_forward_denominator_mismatch')
    return value


def references_disjoint(left, right):
    a, b = set(left.get('layer_ids') or []), set(right.get('layer_ids') or [])
    if a and b and a.isdisjoint(b):
        return True
    lp, rp = left.get('population_partition_identity') or {}, right.get('population_partition_identity') or {}
    kind = left.get('population_partition_kind')
    lm = {canonical(x) for x in left.get('population_partition_members', [])}
    rm = {canonical(x) for x in right.get('population_partition_members', [])}
    return bool(lp.get('sha256') and lp['sha256'] == rp.get('sha256')
        and kind and kind == right.get('population_partition_kind') and lm and rm and lm.isdisjoint(rm))


def cost_coverage(observed, strict, references, normalized):
    """A complete native population owns the denominator, never a program sum.

    Strict portions have no retained per-event histogram in these old receipts.
    Therefore a partial strict/reference overlap cannot be subtracted exactly;
    it is shown separately and never added to primary covered calls or budget.
    """
    total = sum(observed.values()); strict_count = sum(r['observed_us']['count'] for r in strict)
    if strict_count > total:
        raise ValueError('strict_population_exceeds_native_population')
    primary = list(strict); exclusions = []; used = Counter(); seen = set()
    if strict_count:
        for r in [*references, *normalized]:
            r['coverage_disposition'] = ('overlaps_complete_strict_population' if strict_count == total
                else 'partial_strict_overlap_not_resolved_from_retained_histograms')
            exclusions.append(r['coverage_disposition'])
        return primary, {'strict_calls': strict_count, 'additional_reference_calls': 0,
                         'uncovered_calls': total - strict_count, 'reference_overlap_exclusions': exclusions}
    # Current source groups precede shape-only reference cohorts. Sorting never
    # inspects prediction error and exact duplicate histograms cannot add calls.
    strength = {'full_native_abi': 0, 'normalized_contract': 1, 'source_symbol_retained_group': 2,
                'embedded_source_role': 3}
    for r in sorted(references, key=lambda x: (strength.get(x['observation_identity_domain'], 4),
                                               x['receipt']['sha256'], x.get('group_id') or '')):
        h = histogram(r['duration_ns_counter']) if r['duration_ns_counter'] is not None else None
        key = (tuple(r['roles']), tuple(r.get('layer_ids') or []), canonical(r['duration_ns_counter']))
        if h is None:
            r['coverage_disposition'] = 'full_histogram_unavailable_kept_as_separate_reference'
        elif key in seen:
            r['coverage_disposition'] = 'duplicate_same_role_layer_histogram'
        elif any(not references_disjoint(r, selected) for selected in primary):
            r['coverage_disposition'] = 'cross_partition_occurrence_overlap_unproven_not_added'
        elif any(n > observed[ns] - used[ns] for ns, n in h.items()):
            r['coverage_disposition'] = 'overlap_with_selected_reference_population_not_added'
        else:
            r['coverage_disposition'] = 'primary_disjoint_retained_histogram'
            used.update(h); primary.append(r); seen.add(key)
            continue
        exclusions.append(r['coverage_disposition'])
    has_source = bool(primary)
    complete_normalized = not has_source and sum(x['observed_us']['count'] for x in normalized) == total
    for r in normalized:
        if has_source:
            r['coverage_disposition'] = 'alternative_shape_reference_not_added_to_source_reference'
        elif complete_normalized:
            r['coverage_disposition'] = 'complete_shape_reference_population'
            primary.append(r)
        else:
            r['coverage_disposition'] = 'partial_shape_reference_kept_separate'
        exclusions.append(r['coverage_disposition'])
    covered = sum(r['observed_us']['count'] for r in primary)
    return primary, {'strict_calls': 0, 'additional_reference_calls': covered,
                     'uncovered_calls': total - covered, 'reference_overlap_exclusions': exclusions}


def build(commit):
    started = time.perf_counter(); sections, baseline = fixed_sections(commit)
    chosen, boundary_ranking = choose_cases(sections['current_body_comparisons'])
    families, refs, histograms, matched, reference_data, actual_reads = linked_case_data(sections, chosen)
    measured_supplements = measured_hccl_supplements(chosen, families, histograms)
    missing_canonical = {row['case_id'] for row in measured_supplements}
    cases = []; hist_checks = 0
    for body in chosen:
        pop = population(body); forwards = body['comparison']['observed_forward_count']
        local_f = [r for r in families if population(r) == pop]
        local_c = [r for r in sections['current_operator_cohorts'] if population(r) == pop and classify(r['native_operator_type'])]
        local_r = [r for r in refs if population(r) == pop]
        native_types = sorted({r['native_operator_type'] for r in [*local_f, *local_r]})
        mechanisms = []
        for native in native_types:
            fs = [r for r in local_f if r['native_operator_type'] == native]
            observed = Counter(); role_populations = []
            for f in fs:
                if f['forward_count'] != forwards:
                    raise ValueError('operator_forward_population_differs_from_body')
                h, pin = histograms[family_key(f)]; observed.update(h); hist_checks += 1
                role_populations.append({'role': f['declared_role'], 'observed_us': f['observed_us'],
                    'actual_identity': pin, 'receipt': f['receipt'], 'runtime_identity': f['runtime_identity'],
                    'duration_ns_counter': sorted(h.items()), 'controller_overlay': f.get('controller_overlay'),
                    'measurement_origin': f.get('measurement_origin', 'current_canonical_operator_family')})
            if not observed:
                # A separately retained reference cannot fabricate the missing
                # complete native-family denominator in the canonical actual.
                mechanisms.append({'cluster': classify(native), 'native_operator_type': native,
                    'status': 'canonical_native_population_missing', 'observed_us': None,
                    'references': [reference_entry(reference_data[id(r)], forwards) for r in local_r if r['native_operator_type'] == native]})
                continue
            strict, normalized = [], []
            for row in local_c:
                if row['native_operator_type'] != native:
                    continue
                original = matched[(family_key(row), row['cohort_id'])]
                obs = original['observed']; count = obs['complete_event_count']
                item = {'kind': 'strict_cohort' if row['status'] == 'compared' else 'normalized_reference_cohort',
                    'cohort_id': row['cohort_id'], 'role': row['declared_role'], 'status': row['status'],
                    'observed_us': {'count': count, 'mean': row['observed_us'],
                                    'p50': obs['duration_ns']['p50'] / 1000},
                    'calls_per_forward': count / forwards, 'predicted_us': row['predicted_us'],
                    'observed_activity_ms_per_forward': obs['complete_activity_sum_ns'] / forwards / 1e6,
                    'predicted_activity_ms_per_forward': row['predicted_activity_ms_per_forward'],
                    'signed_activity_residual_ms_per_forward': row['signed_activity_residual_ms_per_forward'],
                    'receipt': row['receipt'], 'runtime_identity': row['runtime_identity'],
                    'contract': original.get('contract'), 'physical_signature': row['physical_signature'],
                    'accuracy_pass': row['accuracy_pass'], 'duration_ns_counter': None,
                    'histogram_basis': 'persisted_cohort_mean_p50_activity_only; complete family histogram retained separately'}
                (strict if row['status'] == 'compared' else normalized).append(item)
            reference_rows = [reference_entry(reference_data[id(r)], forwards) for r in local_r if r['native_operator_type'] == native]
            primary, coverage = cost_coverage(observed, strict, reference_rows, normalized)
            all_stats = stats(observed); covered = sum(r['observed_us']['count'] for r in primary)
            measured_covered = sum(r['observed_activity_ms_per_forward'] for r in primary) if primary else None
            predicted = sum(r['predicted_activity_ms_per_forward'] for r in primary) if primary else None
            mechanisms.append({'cluster': classify(native), 'native_operator_type': native,
                'status': 'complete_cost_coverage' if covered == all_stats['count'] else 'partial_cost_coverage' if covered else 'measured_cost_unavailable',
                'observed_us': all_stats, 'calls_per_forward': all_stats['count'] / forwards,
                'observed_activity_ms_per_forward': all_stats['activity_sum_ns'] / forwards / 1e6,
                'duration_ns_counter': sorted(observed.items()), 'roles': role_populations,
                'coverage': coverage, 'primary_cost_components': primary,
                'references': reference_rows, 'normalized_reference_alternatives': normalized,
                'covered_observed_activity_ms_per_forward': measured_covered,
                'predicted_covered_activity_ms_per_forward': predicted,
                'covered_signed_activity_residual_ms_per_forward': predicted - measured_covered if predicted is not None else None,
                'full_family_predicted_activity_ms_per_forward': predicted if covered == all_stats['count'] else None,
                'missing_cost_reason': 'No cost for this exact retained source/geometry/native population in the fixed current strict or reference selections.' if not primary else None,
                'small_m_valid_rows_basis': 'Execution query rows are known; expert bank capacity is not proven valid routing work.' if classify(native) == 'C' else None,
                'nonadditive_activity_not_body_causal_budget': True})
        clusters = []
        for key, title in CLUSTERS.items():
            rows = [m for m in mechanisms if m['cluster'] == key]
            populated = [m for m in rows if m.get('observed_us')]
            unknown = not populated and body['case_id'] in missing_canonical
            has_cost = any(m['covered_signed_activity_residual_ms_per_forward'] is not None for m in populated)
            strict_calls = sum(m['coverage']['strict_calls'] for m in populated)
            reference_calls = sum(m['coverage']['additional_reference_calls'] for m in populated)
            uncovered_calls = None if unknown else sum(m['coverage']['uncovered_calls'] for m in populated)
            clusters.append({'cluster': key, 'title': title,
                'status': 'present' if populated else 'canonical_operator_population_unavailable' if body['case_id'] in missing_canonical else 'not_present_in_canonical_actual',
                'native_types': [m['native_operator_type'] for m in rows],
                'observed_calls': None if unknown else sum(m['observed_us']['count'] for m in populated),
                'strict_calls': strict_calls, 'additional_reference_calls': reference_calls,
                'uncovered_calls': uncovered_calls,
                'strict_calls_per_forward': strict_calls / forwards,
                'additional_reference_calls_per_forward': reference_calls / forwards,
                'uncovered_calls_per_forward': uncovered_calls / forwards if uncovered_calls is not None else None,
                'observed_activity_ms_per_forward': sum(m['observed_activity_ms_per_forward'] for m in populated) if populated else None,
                'covered_observed_activity_ms_per_forward': sum(m['covered_observed_activity_ms_per_forward'] for m in populated
                    if m['covered_observed_activity_ms_per_forward'] is not None) if has_cost else None,
                'covered_predicted_activity_ms_per_forward': sum(m['predicted_covered_activity_ms_per_forward'] for m in populated
                    if m['predicted_covered_activity_ms_per_forward'] is not None) if has_cost else None,
                'covered_signed_activity_residual_ms_per_forward': sum(m['covered_signed_activity_residual_ms_per_forward'] for m in populated
                    if m['covered_signed_activity_residual_ms_per_forward'] is not None) if has_cost else None,
                'interpretation': 'Sum of distinct measured native activities inside this cluster only; may overlap in time or physical source programs. Do not sum clusters or attribute this to Body elapsed.'})
        cases.append({'case_id': body['case_id'], 'selection_group': body['selection_group'],
            'source_identity': body['source_identity'], 'geometry': body['geometry'], 'forward_count': forwards,
            'body_comparison': body['comparison'], 'body_runtime_identity': body['runtime_identity'], 'body_receipt': body['receipt'],
            'absolute_ms_to_15pct_boundary': abs(body['comparison']['per_forward_diff_ms']) - .15 * body['comparison']['observed_ms']['mean'],
            'boundary_selection_rank': body.get('boundary_selection_rank'), 'clusters': clusters, 'mechanisms': mechanisms})
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)
    if rss > 512 * 1024**2:
        raise MemoryError('residual_ledger_exceeds_512_MiB')
    return {'schema_version': 'mindie-residual-mechanism-ledger/1', 'baseline_identity': baseline,
        'source_count': len(cases), 'forward_count': sum(c['forward_count'] for c in cases),
        'selection_groups': dict(Counter(c['selection_group'] for c in cases)),
        'a3_boundary_selection': {'basis': 'Mandatory historical focuses V4Flash c4 and Kimi4 c32; two other failed A3 sources chosen by smallest abs(relative_error)-0.15. Absolute milliseconds are reported separately and do not establish relative near-pass.',
                                  'ranking': boundary_ranking,
                                  'mandatory': ['v4flash-a3-tp8-c4', 'a3_kimi4_tp8_w4a8_c32'], 'additional_from_ranking': 2},
        'cases': cases, 'incremental_arms': [],
        'measured_only_supplements': measured_supplements,
        'coverage_policy': ['Canonical actual families own complete measured populations.',
            'Strict complete-event cohorts take precedence; partial strict/reference overlap is kept separate and never counted twice.',
            'With no strict calls, full retained reference histograms are selected in fixed evidence-domain/receipt order without using error; overlap is not added.',
            'Reference disjointness requires nonoverlapping aligned layers or distinct members of the same retained population partition. Histogram capacity alone never proves occurrence separation.',
            'Normalized reference cohorts are alternatives when source references already cover calls.',
            'Unknown predictions are null, never zero. Full-family prediction is null for partial coverage.',
            'Histograms and real P50 are retained; predicted means do not create predicted latency distributions.',
            'Small-M labels do not assert expert group-list or valid routing rows from storage capacity.',
            'HCOM elapsed is not link service; typed controller overlays are outside mechanism D.',
            'All residuals are nonadditive kernel activities. Neither clusters nor source service differences explain Body wall-clock causally.'],
        'execution': {'raw_capture_reads': 0, 'new_cost_evaluations': 0, 'retained_actual_reads': actual_reads,
                      'full_histogram_checks': hist_checks, 'elapsed_seconds': time.perf_counter() - started,
                      'maximum_resident_set_size_bytes': rss}}


def number(value, digits=3):
    return '—' if value is None else f'{value:.{digits}f}'


def compact_summary(report):
    lines = ['## Model-group mechanism ranges', '',
        'Ranges describe separate case populations. Covered Real/Sim/residual use the same covered calls within each case; rows with no cost do not enter those ranges. Inactive clusters are omitted here and retained in JSON.', '',
        '| Model group / cluster | Measured / cost-covered cases | All Real ms/F range | Covered Real / Sim ms/F ranges | Covered residual ms/F range | Strict / reference / uncovered calls |',
        '|---|---:|---:|---:|---:|---:|']
    def span(rows, field):
        values = [r[field] for r in rows if r[field] is not None]
        return f'{min(values):.3f}–{max(values):.3f}' if values else '—'
    for group in report['selection_groups']:
        cases = [c for c in report['cases'] if c['selection_group'] == group]
        for key in CLUSTERS:
            all_rows = [r for c in cases for r in c['clusters'] if r['cluster'] == key]
            rows = [r for r in all_rows if r['status'] == 'present']
            if not rows:
                continue
            cost_count = sum(r['covered_predicted_activity_ms_per_forward'] is not None for r in rows)
            coverage = ' / '.join(str(sum(r[k] for r in rows)) for k in ('strict_calls', 'additional_reference_calls', 'uncovered_calls'))
            lines.append(f"| {group} / {key} | {len(rows)} / {cost_count} of {len(cases)} | {span(rows, 'observed_activity_ms_per_forward')} | {span(rows, 'covered_observed_activity_ms_per_forward')} / {span(rows, 'covered_predicted_activity_ms_per_forward')} | {span(rows, 'covered_signed_activity_residual_ms_per_forward')} | {coverage} |")
    return lines


def render(report):
    lines = ['# Residual mechanism ledger — fixed 9f10558 baseline', '',
        f"{report['source_count']} distinct captures / {report['forward_count']} selected complete Body forwards. No raw re-scan or new prediction.", '',
        'Four clusters retain complete native-family measurements and individual strict/reference provenance. **The millisecond columns are nonadditive activity residuals, not a causal Body budget. Do not sum clusters.** Missing costs are shown as `—`; partial references never extrapolate to an entire native family.', '',
        'A3 includes the requested V4Flash c4 and Kimi4 c32, then the two remaining failed sources closest to the ±15% relative band. Absolute milliseconds are shown separately; small four-layer absolute gaps do not imply relative accuracy. The full eligible ranking is retained in JSON.', '']
    lines += compact_summary(report)
    lines += ['', '## Per-case clusters', '',
        '| Case | Body Real / Sim ms | ms to 15% band | Cluster | All observed ms/F | Covered Real / Sim ms/F | Strict / reference / uncovered calls (per F) | Covered activity residual ms/F |',
        '|---|---:|---:|---|---:|---:|---:|---:|']
    for case in report['cases']:
        body = case['body_comparison']
        for cl in case['clusters']:
            if cl['status'] == 'not_present_in_canonical_actual':
                continue
            coverage = f"{cl['strict_calls']} / {cl['additional_reference_calls']} / {cl['uncovered_calls'] if cl['uncovered_calls'] is not None else '—'}"
            per_forward = ' / '.join(number(cl[k], 2) for k in ('strict_calls_per_forward', 'additional_reference_calls_per_forward', 'uncovered_calls_per_forward'))
            lines.append(f"| {case['case_id']} | {body['observed_ms']['mean']:.3f} / {body['predicted_ms']:.3f} | {case['absolute_ms_to_15pct_boundary']:.3f} | {cl['cluster']} | {number(cl['observed_activity_ms_per_forward'])} | {number(cl['covered_observed_activity_ms_per_forward'])} / {number(cl['covered_predicted_activity_ms_per_forward'])} | {coverage} ({per_forward}) | {number(cl['covered_signed_activity_residual_ms_per_forward'])} |")
    for case in report['cases']:
        lines += ['', '## ' + case['case_id'], '',
            '| Cluster / native | Calls/F | Real Mean / P50 us | Strict/reference covered calls | Covered Sim ms/F | Covered residual ms/F | Coverage |',
            '|---|---:|---:|---:|---:|---:|---|']
        for row in case['mechanisms']:
            if not row.get('observed_us'):
                lines.append(f"| {row['cluster']} / {row['native_operator_type']} | — | — | — | — | — | canonical actual missing |"); continue
            obs = row['observed_us']; cov = row['coverage']
            lines.append(f"| {row['cluster']} / {row['native_operator_type']} | {row['calls_per_forward']:.2f} | {obs['mean']:.3f} / {obs['p50']:.3f} | {cov['strict_calls']} / {cov['additional_reference_calls']} | {number(row['predicted_covered_activity_ms_per_forward'])} | {number(row['covered_signed_activity_residual_ms_per_forward'])} | {row['status']} |");
        lines += ['', 'Component costs (each retains its own measured population and runtime):', '',
            '| Native / role | Calls/F | Real Mean / P50 us | Sim us/call | Runtime file-map | Evidence |',
            '|---|---:|---:|---:|---|---|']
        for row in case['mechanisms']:
            for component in row.get('primary_cost_components', []):
                runtime = component['runtime_identity'].get('recorded_sim_file_map_sha256') or 'unknown'
                role = component.get('role') or ','.join(component.get('roles', []))
                obs = component['observed_us']
                lines.append(f"| {row['native_operator_type']} / {role} | {component['calls_per_forward']:.2f} | {obs['mean']:.3f} / {obs['p50']:.3f} | {number(component['predicted_us'])} | `{runtime[:12]}` | {component['kind']} |")
    lines += ['', 'Full integer duration histograms, excluded overlapping alternatives, source/case/receipt hashes, physical program references and conditions remain in JSON. Current Body and operator families may originate from different runtime generations; the ledger does not relabel them.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', default='9f105588a72d8cba10e74f19c828e142fe968eca')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(); result = build(args.commit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'residual-mechanism-ledger.json').write_text(json.dumps(result, separators=(',', ':'), ensure_ascii=False) + '\n')
    (args.output_dir / 'residual-mechanism-ledger.md').write_text(render(result))
    print(json.dumps({'sources': result['source_count'], 'forwards': result['forward_count'], 'execution': result['execution']}))


if __name__ == '__main__':
    main()
