"""Rebind retained low-M services to the explicit source force-EPLB graph.

[Role] Replace generic padded assignment work with the source integer ledger.
[Invariants] Timing parameters come from the original complete observations;
  no cost or body residual is read. Source-scenario closure does not establish
  captured group-list values or the deployed binary identity.
[Timeouts & Locks] Eight bounded metadata graphs, serial; no devices or locks.
[Side-Effect Policy] Write new cases and replay manifest; preserve prior arms.
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

from build_service_cases import (EXAMPLES, HERE, INPUTS, generate, identity,
                                 key, read, resolve)
from mindie_sim import target_graphs
from mindie_sim.prediction.source_force_eplb import SOURCE, ledger

FIXED = Path('/tmp/mindie-sim-cohort-wave6-20261029')
RUNTIME = '84d80b40dca5a462ff32b971152c2f2e81abfc4b'
VARIANT = 'observable-service-source-force-eplb-84d80b40'


def main():
    previous = read(HERE / 'decode-forward-low-m-3b72ea2d-cases.json')
    operator = read(EXAMPLES / INPUTS['kimi'][0])
    native = read(EXAMPLES / INPUTS['kimi'][1])
    by_id = {r['source_case_id']: r for r in operator['cases']}
    native_by_id = {r['case_id']: r for r in native['cases']}
    rows, evidence = [], []
    source_dir = HERE / 'source-routing-inputs-84d80b40'
    source_dir.mkdir(exist_ok=True)
    for prior_row in previous['cases']:
        row = deepcopy(prior_row)
        name = row['case_id']
        batch = int(name.split('_c')[1].split('_')[0])
        source_path = FIXED / ('examples/cases/high-concurrency-20261030/'
                              f'kimi-source-complete/{name}_source_complete.json')
        raw = read(source_path)
        raw['runtime']['kernels']['force_eplb_source'] = {
            'kind': 'vllm_ascend_sp_mc2', 'global_bs': 0}
        raw['runtime']['kernels'].pop('service_regimes', None)
        route = ledger(16, 8, 8, max(1, (batch + 7) // 8), batch).to_dict()
        scenario = {
            'status': 'source_scenario_integer_work_matched',
            'prior_declared_rank0_expert_rows': [4, 4],
            'source_rank0_expert_rows': list(route['local_expert_rows']),
            'source_policy': raw['runtime']['kernels']['force_eplb_source'],
            'source': SOURCE, 'routing_ledger': route,
            'source_scenario_work_closed': True,
            'captured_group_list_values_observed': False,
            'captured_binary_identity_established': False,
            'scope': 'declared physical rank-zero compute with complete peer transport',
            'interpretation': 'The previous generic padded-row discrepancy is removed for the explicit source scenario. Captured routing values and peer completion remain unobserved.'}
        raw['runtime'].setdefault('metadata', {})['source_routing_work_evidence'] = scenario
        raw['runtime']['metadata'].pop('known_routing_work_gap', None)
        input_path = source_dir / (name + '.json')
        input_path.write_text(json.dumps(raw, indent=2) + '\n')
        row['sim_case_path'] = str(input_path)
        row['scenario_evidence'].pop('known_routing_work_gap', None)
        row['scenario_evidence']['source_routing_work_evidence'] = scenario
        row.pop('calibration_evidence', None)
        row['source_author_case_identity'] = identity(source_path)
        row['prior_service_case_identity'] = identity(resolve(prior_row['sim_case_path']))
        row['runtime_refresh'] = {'source_commit': RUNTIME,
            'prior_runtime_commit': '3b72ea2d8f23ec102292b33aa57dada54cd4da45',
            'reason': 'explicit source force-EPLB integer work and physical service rebinding'}
        rebuilt, summary = generate(row, 'kimi', by_id[name], native_by_id[name],
                                   case_directory='cases-source-routing-84d80b40')
        final_path = resolve(rebuilt['sim_case_path'])
        final = read(final_path)
        final['runtime']['metadata']['calibration_evidence']['source_routing_work_evidence'] = scenario
        final_path.write_text(json.dumps(final, indent=2) + '\n')
        rebuilt.update(variant_id=VARIANT, model_declaration=identity(final_path),
                       calibration_evidence=final['runtime']['metadata']['calibration_evidence'])
        rebuilt['replay_input_pins']['case'] = identity(final_path)
        graphs = target_graphs(final, scope='body', phase='decode', tokens=1,
            context=row['geometry']['context_tokens'], sequences=batch, apply_body_defaults=True)
        grouped = [op for graph in graphs.values() for op in graph if op.family == 'grouped_gemm']
        if len(grouped) != 184:
            raise ValueError(('incomplete_grouped_layers', name, len(grouped)))
        expected_rows = tuple(route['local_expert_rows'])
        if any(tuple(dict(op.metadata)['matrix_group_rows']) != expected_rows for op in grouped):
            raise ValueError(('source_group_rows_differ', name))
        traffic = [op for graph in graphs.values() for op in graph
                   if dict(op.metadata).get('traffic_model') == 'source_masked_integer_assignments']
        if len(traffic) != 184:
            raise ValueError(('incomplete_peer_transport', name, len(traffic)))
        old_rules = read(resolve(prior_row['sim_case_path']))['runtime']['kernels']['service_regimes']
        new_rules = final['runtime']['kernels']['service_regimes']
        population = lambda rules: Counter((key(r['provenance']['native_operator_types']),
            r['provenance']['measurement_population'], r['response']['fixed_us']) for r in rules)
        if population(old_rules) != population(new_rules):
            raise ValueError(('observed_parameter_population_changed', name))
        summary.update(case_identity=identity(final_path),
            source_author_case_identity=identity(source_path),
            original_source_policy_evidence=scenario,
            validated_full_layer_grouped_count=len(grouped),
            validated_full_layer_peer_transport_count=len(traffic),
            observed_parameter_population_unchanged=True,
            historical_generic_work_arm=identity(resolve(prior_row['sim_case_path'])))
        (final_path.parent / (name + '-generation.json')).write_text(json.dumps(summary, indent=2) + '\n')
        rows.append(rebuilt); evidence.append(summary)
        print(json.dumps({'case_id': name, 'rank0_expert_rows': expected_rows,
            'full_grouped_nodes': len(grouped), 'peer_transport_nodes': len(traffic),
            'rules': len(new_rules), 'observed_parameters_unchanged': True}), flush=True)
        del graphs, grouped, traffic
    output = HERE / 'decode-forward-source-routing-84d80b40-cases.json'
    output.write_text(json.dumps({'schema_version': 'mindie-decode-forward-replay/1',
        'variant_id': VARIANT, 'cases': rows, 'runtime_plan': {'source_commit': RUNTIME},
        'parameter_refits': 0, 'not_new_live_collection': True,
        'comparison_scope': 'in_sample_service_on_explicit_source_force_eplb_work'}, indent=2) + '\n')
    (HERE / 'source-routing-84d80b40-generation.json').write_text(json.dumps({
        'schema_version': 'mindie-source-routing-service-rebinding/1',
        'generator_identity': identity(__file__), 'runtime_source_commit': RUNTIME,
        'source_policy_identity': identity(FIXED / 'mindie_sim/prediction/source_force_eplb.py'),
        'cases': evidence, 'parameter_refits': 0, 'raw_event_reads': 0,
        'predictions_run': 0}, indent=2) + '\n')


if __name__ == '__main__':
    main()
