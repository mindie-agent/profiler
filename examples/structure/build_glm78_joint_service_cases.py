"""Bind complete local-native observations to an explicit shared service queue.

[Role] Prepare GLM78 SFA and grouped up/down joint-service replay inputs.
[Invariants] Complete identical ABI/Block/physical domains pool integer timing
  histograms. No Body residual enters a parameter; network rules are unchanged.
[Timeouts & Locks] Three bounded metadata exports only; no cost, locks or raw scan.
[Side-Effect Policy] Write independent declarations and provenance; no Sim edits.
"""
from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

from build_qwen_a3_service_cases import identity, physical_ops, read, write
from build_a3_observed_service_cases import _physical_match


HERE = Path(__file__).resolve().parent
BASE = HERE / 'acceptance-20261030-service-qwen-a3/decode-forward-glm78-caller-complete-service-cases.json'
NATIVE = HERE / 'acceptance-20261030-service-qwen-a3/glm78-native'
GROUPED = HERE.parents[1] / 'data/observations/sources/arch22-physical-services/grouped-source-constraints.json'
JOINT = HERE.parents[1] / 'data/observations/sources/arch22-physical-services/native-joint-service-inputs.json'
OUT = HERE / 'acceptance-20261030-glm78-joint-service'
TYPES = {'KvQuantSparseFlashAttention': 78, 'GroupedMatmulSwigluQuantV2': 75, 'GroupedMatmul': 75}
EXECUTION = {'kind': 'joint_native', 'resource': 'joint_native_a3', 'reference_rate': 1e9}


def pooled(groups):
    histogram = Counter()
    for group in groups: histogram.update(dict(group['duration_ns_counter']))
    count = sum(histogram.values()); ordered = sorted(histogram.items())
    def at(position):
        cumulative = 0
        for ns, n in ordered:
            cumulative += n
            if cumulative > position: return ns
        raise ValueError('empty_native_population')
    return {'duration_ns_counter': ordered, 'count': count,
        'mean_us': float(sum(Decimal(ns) * n for ns, n in ordered) / count / 1000),
        'p50_us': (at((count - 1)//2) + at(count//2))/2000}


def sfa_match(case, ops, abi, geometry):
    inputs, outputs = abi[2:]; m = geometry['query_rows']; batch = geometry['sequences_per_replica']
    if (len(inputs) != 9 or len(outputs) != 1 or inputs[0] != [[m,4,576], 'bf16','ND']
        or inputs[1] != inputs[2] or inputs[1][0][-2:] != [1,656] or inputs[1][1:] != ['int8','ND']
        or inputs[3] != [[m,1,2048], 'int32','ND'] or inputs[4][0] or inputs[5][0]
        or inputs[6][0][0] != batch or inputs[6][1] != 'int32'
        or inputs[7] != [[batch], 'int32','ND'] or inputs[8] != inputs[7]
        or outputs[0] != [[m,4,512], 'bf16','ND']):
        raise ValueError('packed_d656_full_sfa_abi_changed')
    selected = [op for op in ops if op.recipe == 'latent_attention_batch']
    if len(selected) != 78: raise ValueError('sfa_not_one_batch_call_per_layer')
    matches = []
    for op in selected:
        meta = dict(op.metadata); view = meta['attention_tensor_view']; dimensions = meta['indexed_attention_geometry']
        if (tuple(view['query_shape']) != (m,4,512) or tuple(view['query_rope_shape']) != (m,4,64)
            or tuple(view['output_shape']) != (m,4,512) or view['batch_count'] != batch
            or len(dimensions['sequences']) != batch or dimensions['cache_dtype'] != 'int8'
            or dimensions['topk'] != 2048 or dimensions['latent'] != 512 or dimensions['rope'] != 64):
            raise ValueError('source_sfa_batch_geometry_changed')
        match = _physical_match(case, op)
        match.update({f'metadata.indexed_attention_geometry.{key}': dimensions[key]
                      for key in ('topk','heads','latent','rope','cp','query_dtype','cache_dtype')})
        matches.append(match)
    if any(match != matches[0] for match in matches): raise ValueError('sfa_layer_physical_domains_differ')
    return matches[0]


def verify_grouped_match(case, ops, match, expected):
    selected = [op for op in ops if op.recipe == match['recipe'] and op.family == match['family']]
    if len(selected) != expected: raise ValueError('grouped_native_multiplicity_changed')
    for op in selected:
        physical = _physical_match(case, op)
        for key, wanted in match.items():
            if key.startswith('metadata.'):
                actual = dict(op.metadata)
                for part in key.split('.')[1:]: actual = actual[part]
            else:
                actual = physical.get(key)
            if actual != wanted: raise ValueError('grouped_native_physical_domain_changed:' + key)
        if dict(op.metadata).get('device_kernel_group') or op.link_bytes:
            raise ValueError('grouped_joint_reference_is_not_single_local_call')


def build():
    manifest = read(BASE); sources = []; pools = defaultdict(list)
    grouped = read(GROUPED)['records']; neutral = read(JOINT)['candidates']
    for row in manifest['cases']:
        raw = read(row['sim_case_path']); geometry = row['replay_input_pins']['primary_geometry']
        native_path = NATIVE / f"{row['case_id']}-native-partitions.json"; native = read(native_path)
        if native['source_identity']['sha256'] != row['source']['sha256']: raise ValueError('source_mismatch')
        case, ops = physical_ops(raw, geometry); records = []
        for kind, calls in TYPES.items():
            groups = [group for group in native['partitions'] if group['native_operator_type'] == kind]
            if not groups or any(group['native_abi'] != groups[0]['native_abi'] for group in groups):
                raise ValueError('native_family_has_multiple_abis')
            observed = pooled(groups)
            if observed['count'] != calls * native['forward_count']: raise ValueError('native_population_incomplete')
            if kind == 'KvQuantSparseFlashAttention':
                configured = raw['runtime']['kernels']['programs']['indexed_attention']
                if configured['kind'] != 'indexed_attention_packed_int8': raise ValueError('wrong_sfa_program')
                candidates = [x for x in neutral if x['applicability_domain'].get('native_abi') == groups[0]['native_abi']]
                if len(candidates) != 1: raise ValueError('no_unique_neutral_sfa_domain')
                match = sfa_match(case, ops, groups[0]['native_abi'], geometry)
                block = candidates[0]['applicability_domain']['observed_block_num']
                mix = candidates[0]['applicability_domain']['observed_mix_block_num']
                original = None
            else:
                originals = [rule for rule in raw['runtime']['kernels']['service_regimes']
                             if rule.get('provenance', {}).get('native_operator_type') == kind]
                if len(originals) != 1: raise ValueError('native_grouped_rule_not_unique')
                original = originals[0]; match = original['match']
                verify_grouped_match(case, ops, match, calls)
                evidence = [x for x in grouped if x['case_id'] == row['case_id'] and x['native_operator_type'] == kind]
                if len(evidence) != 1 or evidence[0]['native_abi'] != groups[0]['native_abi']:
                    raise ValueError('grouped_complete_pmu_abi_domain_changed')
                block, mix = int(evidence[0]['block_num']), int(evidence[0]['mix_block_num'])
                if abs(original['response']['fixed_us'] - observed['mean_us']) > 1e-9:
                    raise ValueError('prior_mean_not_complete_native_population')
            domain = {'native_operator_type': kind, 'native_abi': groups[0]['native_abi'],
                'physical_match': match, 'block_num': block, 'mix_block_num': mix}
            key = json.dumps(domain, sort_keys=True)
            record = {'case_id': row['case_id'], 'domain': domain, 'observed': observed,
                'native_identity': identity(native_path), 'source_identity': native['source_identity'],
                'forward_count': native['forward_count'], 'expected_rule_hits': calls,
                'prior_rule_id': None if original is None else original['id']}
            records.append(record); pools[key].append(record)
        sources.append((row, raw, records))
    output = deepcopy(manifest); output['cases'] = []; ledger = []
    for row, raw, records in sources:
        rules = raw['runtime']['kernels']['service_regimes']; updated = []
        for record in records:
            domain = record['domain']; kind = domain['native_operator_type']; members = pools[json.dumps(domain, sort_keys=True)]
            stats = pooled([member['observed'] for member in members])
            rule = {'id': kind.lower() + '-pooled-joint-native', 'match': domain['physical_match'],
                'response': {'fixed_us': stats['mean_us']}, 'execution': {**EXECUTION, 'native_kernel': kind},
                'provenance': {'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'native_operator_type': kind, 'expected_rule_hits': record['expected_rule_hits'],
                    'native_abi': domain['native_abi'], 'observed_block_num': domain['block_num'],
                    'observed_mix_block_num': domain['mix_block_num'], 'complete_population': stats,
                    'retained_source_populations': [{k:v for k,v in member.items() if k not in ('domain','observed')} for member in members],
                    'pooling_basis': 'Identical full native ABI, Block/Mix and declared physical match; integer whole-call histogram pooled before mean/P50.',
                    'response_boundary': 'single_local_native_whole_call_inclusive_once',
                    'body_residual_used': False, 'strict_tensor_admission_changed': False,
                    'unknowns': ['Captured scalar/index/group-list contents and binary identity are not established.',
                                 'Joint busy_ns resource does not identify separate physical byte/cycle rates.']}}
            if record['prior_rule_id'] is not None:
                rules[:] = [item for item in rules if item['id'] != record['prior_rule_id']]
            rules.append(rule); updated.append({'rule_id': rule['id'], 'native_operator_type': kind,
                'rule_hits': record['expected_rule_hits'], 'parameter_us': stats['mean_us'],
                'source_member_count': len(members), 'pooled_call_count': stats['count']})
        device = raw['machine'].setdefault('device', {})
        for field, value in (('rates', 1e9), ('work_units', 'busy_ns'), ('resource_units', 1)):
            device.setdefault(field, {})['joint_native_a3'] = value
        raw.setdefault('metadata', {})['joint_service_baseline'] = identity(row['sim_case_path'])
        target = OUT / 'cases' / f"{row['case_id']}-joint-native.json"; write(target, raw)
        new = deepcopy(row); new.update(sim_case_path=str(target), model_declaration=identity(target),
            variant_id='glm78-local-native-joint-service')
        new['replay_input_pins']['case'] = identity(target)
        new['calibration_origin'] = 'observed'
        new['calibration_evidence'] = {'evaluation_relation': 'in_sample', 'body_residual_used': False,
            'joint_service_boundaries': updated, 'baseline_identity': identity(row['sim_case_path'])}
        output['cases'].append(new); ledger.append({'case_id': row['case_id'], 'rules': updated,
            'local_native_calls_per_forward': sum(x['rule_hits'] for x in updated),
            'communication_and_multiphase_rules_unchanged': True})
    output['baseline_identity'] = identity(BASE)
    output['variant_id'] = 'glm78-local-native-joint-service'
    write(OUT / 'decode-forward-glm78-joint-service-cases.json', output)
    write(OUT / 'joint-service-populations.json', {'cases': ledger, 'producer_identity': identity(__file__),
        'neutral_sfa_identity': identity(JOINT), 'grouped_domain_identity': identity(GROUPED),
        'raw_reads': 0, 'cost_predictions': 0, 'status': 'prepared'})
    print(json.dumps(ledger), flush=True)


if __name__ == '__main__': build()
