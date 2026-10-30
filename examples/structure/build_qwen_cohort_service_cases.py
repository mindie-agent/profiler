"""Bind complete retained Qwen cohorts to current physical service domains.

[Role] Add observed matrix/copy/activation means without reading raw captures.
[Invariants] Every retained target must still have the same active contract;
  each complete histogram is assigned once. No Body residual or per-layer rule.
[Timeouts & Locks] Metadata-only graph construction; bounded per-source JSON.
[Side-Effect Policy] Write a new observable arm, preserving preceding receipts.
"""
from copy import deepcopy
import json

from build_qwen_a3_service_cases import ROOT, OUT, read, write, identity, physical_ops
from build_a3_observed_service_cases import _physical_match
from mindie_sim.structure_contracts import predicted_contract


def build():
    previous = read(OUT / 'decode-forward-qwen-gating-service-cases.json')
    result, evidence = [], []
    for original in previous['cases']:
        row = deepcopy(original)
        cid, old_case = row['case_id'], row['sim_case_path']
        raw = read(old_case)
        base = ROOT / 'acceptance-20261030-qwen-source-native-operators'
        mapping_path = base / 'runtime30dcea1e' / f'body-operator-{cid}-source-gdn-native-runtime30dcea1e.mapping.json'
        actual_path = base / 'retained-six-actual' / f'body-operator-{cid}-qwen-source-gdn-native.actual.json'
        mapping, actual = read(mapping_path), read(actual_path)
        case, ops = physical_ops(raw, row['replay_input_pins']['primary_geometry'])
        by_id = {op.op_id: op for op in ops}
        groups = []
        if actual['source_identity']['sha256'] != row['source']['sha256']:
            raise ValueError('actual_source_mismatch')
        for window in mapping['windows']:
            if window['source_identity']['sha256'] != row['source']['sha256']:
                raise ValueError('mapping_source_mismatch')
            for cohort in window['cohorts']:
                if cohort['native_operator_type'] in ('CausalConv1d', 'RecurrentGatedDeltaRule'):
                    continue  # Already calibrated using their whole source kernels.
                targets = cohort['target_ids']
                declared = [by_id[target.split('/', 1)[1]] for target in targets]
                contracts = [json.loads(json.dumps(predicted_contract(op.to_dict(include_work=False))))
                             for op in declared]
                if any(contract != cohort['contract'] for contract in contracts):
                    raise ValueError('fresh_declared_contract_changed')
                matches = [_physical_match(case, op) for op in declared]
                if not matches or any(match != matches[0] for match in matches):
                    raise ValueError('heterogeneous_physical_service_domain')
                matching = [op for op in ops if _physical_match(case, op) == matches[0]]
                if {op.op_id for op in matching} != {op.op_id for op in declared}:
                    raise ValueError('physical_rule_population_differs')
                families = [family for family in actual['families']
                            if family['native_operator_type'] == cohort['native_operator_type']
                            and set(family['candidate_target_ids']) == set(targets)]
                if len(families) != 1:
                    raise ValueError('complete_family_population_not_unique')
                family = families[0]
                hist = family['duration_ns_counter']
                count = sum(n for _, n in hist)
                activity_ns = sum(ns * n for ns, n in hist)
                if (count != cohort['event_count'] or activity_ns != cohort['activity_sum_ns']
                        or count != len(declared) * actual['forward_count']):
                    raise ValueError('complete_histogram_or_multiplicity_differs')
                mean_us = activity_ns / count / 1000
                rid = f"{declared[0].recipe}-complete-cohort-response"
                provenance = {
                    'calibration_origin': 'observed', 'evaluation_relation': 'in_sample',
                    'actual_identity': identity(actual_path), 'mapping_identity': identity(mapping_path),
                    'retained_cohort_id': cohort['cohort_id'], 'native_operator_type': cohort['native_operator_type'],
                    'source_identity': actual['source_identity'], 'contract': cohort['contract'],
                    'contract_scope': cohort['contract_scope'], 'observed_us': family['observed_us'],
                    'forward_count': actual['forward_count'], 'expected_rule_hits': len(declared),
                    'response_boundary': 'one_complete_declared_kernel_call',
                    'parameter_statistic': 'whole_population_arithmetic_mean_us',
                    'fresh_candidate_contracts_equal': True, 'body_residual_used': False,
                    'occurrence_binding_implied': False, 'strict_contract_admission_changed': False,
                }
                raw['runtime']['kernels']['service_regimes'].append({
                    'id': rid, 'match': matches[0], 'response': {'fixed_us': mean_us},
                    'provenance': provenance,
                })
                groups.append({'rule_id': rid, 'match': matches[0], **provenance})
        if len(groups) != 11:
            raise ValueError('retained_complete_cohort_population_changed')
        metadata = raw['runtime']['metadata']
        metadata['calibration_origin'] = 'observed'
        metadata['calibration_evidence'].update(
            evaluation_relation='in_sample', complete_cohort_mapping=identity(mapping_path),
            complete_cohort_actual=identity(actual_path), physical_rule_admission='fresh_active_contract_equality',
        )
        target = OUT / 'cohort-cases' / f'{cid}-cohort-observable-service.json'
        write(target, raw)
        row.update(sim_case_path=str(target), model_declaration=identity(target),
                   baseline_service_case_identity=identity(old_case), calibration_origin='observed',
                   calibration_evidence=metadata['calibration_evidence'],
                   variant_id='observable-complete-cohort-service-3b72ea2d')
        row['replay_input_pins']['case'] = identity(target)
        result.append(row)
        evidence.append({'case_id': cid, 'groups': groups,
                         'unassigned': 'Mixed Add/Slice and unresolved fused norms remain unassigned; no Body residual allocation.'})
    write(OUT / 'qwen-cohort-service-populations.json', {'cases': evidence, 'raw_capture_reads': 0})
    write(OUT / 'decode-forward-qwen-cohort-service-cases.json', {
        'schema_version': previous['schema_version'], 'variant_id': 'observable-complete-cohort-service-3b72ea2d',
        'cases': result, 'not_new_live_collection': True,
        'baseline_reference': identity(OUT / 'decode-forward-qwen-gating-service-replay.json'),
    })


if __name__ == '__main__':
    build()
