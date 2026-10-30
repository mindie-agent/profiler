"""[Role] Project selected Body results onto explicit high-concurrency priorities.
[Invariants] Join exact case/source identities; selection never depends on error.
  Inventory predictions are not inputs. Body accuracy, execution, native-contract
  closure and calibration provenance are independent report dimensions.
[Timeouts & Locks] Stream finite local JSON; no subprocesses, locks or costs.
[Side-Effect Policy] Pure build/render API; CLI reads receipts and writes reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
from statistics import median

import ijson


def precision_summary(errors):
    """Count tighter goals on the same completed populations, without new fits."""
    values = sorted(abs(error) for error in errors if error is not None)
    return {
        'population_count': len(values),
        'weighting': 'one selected completed source/geometry population; no Forward weighting',
        'absolute_relative_error_mean': sum(values) / len(values) if values else None,
        'absolute_relative_error_median': median(values) if values else None,
        'absolute_relative_error_max': values[-1] if values else None,
        'within_relative_error': {str(percent): sum(value <= percent / 100 for value in values)
                                  for percent in (5, 8, 10, 15)},
    }


def _key(row):
    return row['case_id'], row['source_identity']['sha256']


def _index(rows):
    result = {}
    for row in rows:
        key = _key(row)
        if key in result:
            raise ValueError('multiple_selected_results_for_exact_case_source:' + key[0])
        result[key] = row
    return result


def _execution(row):
    if row is None:
        return 'NOT_AVAILABLE'
    comparison = row.get('comparison') or {}
    if row.get('error') or row.get('prediction_failure') or row.get('display_status') == 'prediction_failed':
        return 'EXEC_FAILED'
    if comparison.get('status') == 'compared':
        return 'COMPLETED'
    if comparison.get('status') == 'failed' or row.get('status') == 'failed':
        return 'EXEC_FAILED'
    return 'NOT_SCORED'


def _calibration(row):
    row = row or {}
    evidence = row.get('calibration_evidence') or {}
    if not isinstance(evidence, dict):
        evidence = {'declared_metadata': evidence}
    origin = row.get('calibration_origin') or evidence.get('origin') or 'not_declared'
    relation = evidence.get('evaluation_relation') or evidence.get('evaluation_role')
    # Early observable-service receipts used the origin field for this explicit
    # evaluation label. Preserve those receipts instead of inferring from rates.
    if relation is None and origin in {'in_sample', 'heldout'}:
        relation = origin
    return {
        'origin': origin,
        'evaluation_relation': relation or 'not_declared',
        'evidence': evidence,
        'metadata_identity': row.get('calibration_metadata_identity'),
        'observed_parameter_does_not_change_contract_admission': True,
        'held_out_status_is_not_inferred_from_error_or_parameter_names': True,
    }


def _tpot(scenario):
    tpot = scenario.get('tpot') or {}
    client = tpot.get('profiled_run_client_ms') or {}
    return {
        'client_profiled_ms': {
            'mean': client.get('mean'), 'p50': client.get('p50', client.get('median')),
            'p90': client.get('p90'), 'count': client.get('n'),
        },
        'unprofiled_sweep_ms': tpot.get('unprofiled_sweep_ms'),
        'engine_window_estimate_ms': tpot.get('profiled_engine_window_estimate_ms'),
        'explicit_scenario_target_tags': scenario.get('target_tags', []),
        'directory_target_label': scenario.get('capture_directory_target_label'),
        'benchmark_summary_identity': scenario.get('benchmark_summary_identity'),
        'scope': 'client token cadence / declared target; never Body Forward duration',
    }


def build_focus(current_body_rows, focus_spec, latest_attempts=()):
    """Keep the caller's selected result, including when its latest attempt failed."""
    current, latest = _index(current_body_rows), _index(latest_attempts)
    sources = []
    for focus in focus_spec['cases']:
        key = _key(focus)
        selected = current.get(key)
        attempted = latest.get(key)
        comparison = (selected or {}).get('comparison') or {}
        execution = _execution(selected)
        observed = comparison.get('observed_ms') or {}
        predicted = comparison.get('predicted_ms') if execution == 'COMPLETED' else None
        delta = predicted - observed['mean'] if predicted is not None and observed.get('mean') is not None else None
        margin = max(abs(delta) - .15 * observed['mean'], 0) if delta is not None else None
        accuracy = ('PASS' if comparison.get('passed') is True else 'FAIL') if execution == 'COMPLETED' else None
        sources.append({
            'source_case_id': focus['source_case_id'], 'case_id': key[0],
            'source_identity': (selected or focus)['source_identity'],
            'priority_six': bool(focus.get('priority_six')),
            'source_arm_families': focus.get('source_arm_families', []),
            'geometry': (selected or {}).get('geometry'),
            'declared_runtime': (selected or {}).get('declared_runtime'),
            'selected_execution_status': execution,
            'body_accuracy_status': accuracy,
            'selected_result_badge': ('Body ' + accuracy) if accuracy else execution,
            'observed_body_ms': observed,
            'observed_forward_count': comparison.get('observed_forward_count'),
            'predicted_body_ms': predicted,
            'relative_error': comparison.get('relative_error') if execution == 'COMPLETED' else None,
            'signed_body_delta_ms': delta,
            'absolute_ms_outside_15pct_band': margin,
            'selected_receipt': (selected or {}).get('receipt'),
            'selected_runtime_identity': (selected or {}).get('runtime_identity'),
            'selected_case_identity': (selected or {}).get('case_identity') or (selected or {}).get('model_structure_identity'),
            'selected_variant_id': (selected or {}).get('variant_id'),
            'latest_execution_status': _execution(attempted),
            'latest_receipt': (attempted or {}).get('receipt'),
            'latest_runtime_identity': (attempted or {}).get('runtime_identity'),
            'latest_error': (attempted or {}).get('error') or (attempted or {}).get('prediction_failure'),
            'selected_is_latest_attempt': attempted is not None and selected is not None and attempted.get('receipt') == selected.get('receipt'),
            'calibration': _calibration(selected),
            'comparison_basis': comparison.get('comparison_basis'),
            'comparison_assumptions': comparison.get('assumptions', []),
            'contract_boundary': {
                'native_strict_closure': 'not_established_by_body_result',
                'body_pass_implies_native_contract_closure': False,
                'conditional_reference_is_strict': False,
                'parameter_origin_is_not_a_contract_admission_gate': True,
            },
            'tpot': _tpot(focus.get('scenario') or {}),
        })
    if len({_key(row) for row in sources}) != len(sources):
        raise ValueError('focus_spec_repeats_exact_source_case_population')
    unique = {row['source_identity']['sha256'] for row in sources}
    return {
        'schema_version': 'mindie-high-concurrency-focus/1',
        'selection_basis': 'explicit focus identities joined to current caller-selected results; never best error',
        'summary': {
            'distinct_source_count': len(unique), 'selected_population_count': len(sources),
            'observed_forward_count': sum(row['observed_forward_count'] or 0 for row in sources),
            'accepted_source_arm_count': sum(bool(row['source_arm_families']) for row in sources),
            'priority_a5_count': sum(row['priority_six'] for row in sources),
            'body_pass_count': sum(row['body_accuracy_status'] == 'PASS' for row in sources),
            'body_fail_count': sum(row['body_accuracy_status'] == 'FAIL' for row in sources),
            'latest_execution_failed_count': sum(row['latest_execution_status'] == 'EXEC_FAILED' for row in sources),
            'body_precision': precision_summary(row['relative_error'] for row in sources),
        },
        'sources': sources,
        'accepted_source_arms': [row['case_id'] for row in sources if row['source_arm_families']],
        'priority_a5': [row['case_id'] for row in sources if row['priority_six']],
        'limitations': [
            'Accepted source arm means selected modelling declaration, not Body accuracy PASS.',
            'Selected completed results and latest execution attempts are separate.',
            'Native strict contracts and conditional references require their own operator scoreboard.',
            'Calibration and held-out status are not_declared unless explicitly recorded.',
            'The overlapping sections do not add sources or observed Forward populations.',
        ],
    }


def _num(value, digits=3):
    return '—' if value is None else f'{value:.{digits}f}'


def _runtime(value):
    value = value or {}
    return value.get('package_sha256') or value.get('recorded_sim_file_map_sha256') or 'not_declared'


def _receipt(value):
    return '—' if not value else f"[{value['sha256'][:12]}]({value['path']})"


def render_focus(view):
    summary = view['summary']
    lines = ['## 已接受的 source arms', '',
        f"{summary['distinct_source_count']} 个独立来源 / {summary['observed_forward_count']} 次选中 Body Forward。两个表格有交集，分母只计一次。接受建模声明不代表精度达标。", '',
        'Body 误差目标（同一分母）：' + '；'.join(
            f"≤{percent}%：{count}/{summary['body_precision']['population_count']}"
            for percent, count in summary['body_precision']['within_relative_error'].items()) + '。原 15% 验收标准不变。', '',
        '| Case / source family | 当前保留结果 | 最近执行 | Body error | calibration / evaluation | 契约边界 | 当前 runtime / receipt |',
        '|---|---|---|---:|---|---|---|']
    for row in view['sources']:
        if not row['source_arm_families']:
            continue
        calibration = row['calibration']
        lines.append(f"| {row['source_case_id']} / {', '.join(row['source_arm_families'])} | {row['selected_result_badge']} | {row['latest_execution_status']} | {_num(None if row['relative_error'] is None else 100*row['relative_error'], 2)}% | {calibration['origin']} / {calibration['evaluation_relation']} | Body 不证明 native strict 闭合 | `{_runtime(row['selected_runtime_identity'])[:12]}` / {_receipt(row['selected_receipt'])} |")
    lines += ['', '## 六个 A5 高并发重点', '',
        '| Case | Real Mean / P50 / P90 ms | Sim ms / error | Delta / 到 15% 带 ms | 客户端 TPOT Mean / P50 / P90 ms | 场景目标 / 文件名标签 | 最近执行 runtime / receipt |',
        '|---|---:|---:|---:|---|---|---|']
    for row in view['sources']:
        if not row['priority_six']:
            continue
        observed = row['observed_body_ms']; tpot = row['tpot']; client = tpot['client_profiled_ms']
        target = ', '.join(str(item['value']) for item in tpot['explicit_scenario_target_tags']) or '未声明'
        label = (tpot['directory_target_label'] or {}).get('tag') or '无'
        lines.append(f"| {row['source_case_id']} ({row['selected_result_badge']}; latest {row['latest_execution_status']}) | {' / '.join(_num(observed.get(k)) for k in ('mean','p50','p90'))} | {_num(row['predicted_body_ms'])} / {_num(None if row['relative_error'] is None else 100*row['relative_error'], 2)}% | {_num(row['signed_body_delta_ms'])} / {_num(row['absolute_ms_outside_15pct_band'])} | {' / '.join(_num(client[k]) for k in ('mean','p50','p90'))} | {target} / {label}（仅标签） | `{_runtime(row['latest_runtime_identity'])[:12]}` / {_receipt(row['latest_receipt'])} |")
    lines += ['', 'Delta = Sim − Real；“到 15% 带”是统计验收超额，不是待补物理服务预算。客户端 TPOT、场景目标和 Body Forward 是不同指标。最新执行失败时，旧的成功结果可以保留，但不能冒称最新执行已完成。', '']
    return lines


def _identity(path):
    path = Path(path); digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path.resolve()), 'sha256': digest.hexdigest(), 'size_bytes': path.stat().st_size}


def read_current_rows(path):
    """One streaming pass; discard per-layer detail before retaining a row."""
    keys = {'current_body_comparisons', 'latest_body_attempts'}
    result = {key: [] for key in keys}; active = builder = None
    with Path(path).open('rb') as stream:
        for prefix, event, value in ijson.parse(stream, use_float=True):
            if active is not None:
                builder.event(event, value)
                if prefix == active and event == 'end_map':
                    row = builder.value; row.pop('per_layer', None); row.pop('per_layer_reference', None)
                    result[active.split('.')[0]].append(row); active = builder = None
            elif event == 'start_map' and prefix.endswith('.item') and prefix.split('.')[0] in keys:
                active = prefix; builder = ijson.ObjectBuilder(); builder.event(event, value)
    return result


def enrich_receipt_metadata(rows, focus_spec):
    """Only explicit case metadata can establish calibration/held-out labels."""
    wanted = {_key(row) for row in focus_spec['cases']}
    grouped = {}
    for row in rows:
        if _key(row) in wanted and row.get('receipt'):
            grouped.setdefault(row['receipt']['path'], []).append(row)
    for path, targets in grouped.items():
        receipt_pin = _identity(path)
        if any(row['receipt']['sha256'] != receipt_pin['sha256'] for row in targets):
            raise ValueError('selected_body_receipt_identity_changed:' + path)
        by_key = {_key(row): row for row in targets}
        with Path(path).open('rb') as stream:
            for case in ijson.items(stream, 'cases.item', use_float=True):
                row = by_key.get(_key(case))
                if row is None:
                    continue
                if case['comparison'] != row['comparison']:
                    raise ValueError('selected_body_result_differs_from_receipt:' + case['case_id'])
                row['case_identity'] = case.get('model_structure_identity')
                for owner in (case, case.get('scenario_evidence') or {}):
                    for field in ('calibration_origin', 'calibration_evidence'):
                        if field in owner and field not in row:
                            row[field] = owner[field]
                            row['calibration_metadata_identity'] = {'receipt': receipt_pin, 'case_id': case['case_id'], 'field': field}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scoreboard', required=True, type=Path)
    parser.add_argument('--focus-spec', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path, help='Output JSON; Markdown uses the same stem.')
    args = parser.parse_args()
    scoreboard_pin, focus_pin = _identity(args.scoreboard), _identity(args.focus_spec)
    with args.focus_spec.open('rb') as stream:
        spec = next(ijson.items(stream, '', use_float=True))
    data = read_current_rows(args.scoreboard)
    enrich_receipt_metadata(data['current_body_comparisons'], spec)
    enrich_receipt_metadata(data['latest_body_attempts'], spec)
    view = build_focus(data['current_body_comparisons'], spec, data['latest_body_attempts'])
    if scoreboard_pin != _identity(args.scoreboard) or focus_pin != _identity(args.focus_spec):
        raise ValueError('focus_inputs_changed_during_projection')
    view['inputs'] = {'scoreboard': scoreboard_pin, 'focus_spec': focus_pin}
    view['execution'] = {'new_costs': 0, 'raw_scans': 0,
                         'maximum_resident_set_size_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(view, ensure_ascii=False, indent=2) + '\n')
    args.output.with_suffix('.md').write_text('\n'.join(render_focus(view)))
    print(json.dumps({'output': _identity(args.output), 'summary': view['summary'], 'execution': view['execution']}))


if __name__ == '__main__':
    main()
