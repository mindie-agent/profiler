"""Reporting, diagnosis and CLI projection for the zero-shot piecewise lane.

[Role] Turn a frozen ``Prediction`` and a measured ``MeasuredCell`` into L1-L4
  comparisons, physical diagnoses, aggregations and the baseline markdown/JSON
  projection.
[Invariants] Every function reads measured fields only after the prediction is
  frozen; no measured latency enters prediction.  Types are imported lazily from
  the validator so this module stays importable both as a package and a script.
[Timeouts & Locks] Pure bounded arithmetic over supplied records.
[Side-Effect Policy] Read-only; the CLI writes only stdout or the caller's
  trace-cache path.
"""
from __future__ import annotations

import argparse, json, math
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from statistics import mean, median
from typing import Any, Mapping, Sequence


_SYNCED = False


def _sync() -> None:
    """Bring validator globals/classes into this module on first use.

    The validator imports this module at its end; a lazy one-time sync keeps
    both import orders (package, script, test) valid without a cycle while the
    moved functions keep their original, readable bodies.
    """
    global _SYNCED
    if _SYNCED:
        return
    z = _z()
    target = globals()
    for name in dir(z):
        if name.startswith('__') or name in target:
            continue
        target[name] = getattr(z, name)
    _SYNCED = True


def _synced(fn):
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        _sync()
        return fn(*args, **kwargs)

    return wrapper



def _z():
    """Lazy validator module, avoiding an import cycle at module load."""
    try:
        from . import zero_shot_piecewise_validation as module
    except ImportError:
        import zero_shot_piecewise_validation as module
    return module


@_synced
def _row_chargeable(row: Any) -> bool:
    """Eligible for standalone owner comparison; unresolved ABI is not consumed."""
    occurrence = getattr(row, 'native_occurrence', None) or {}
    membership = str(occurrence.get('membership') or '')
    if membership.startswith('consumed_by_') or membership == 'phase_attribution':
        return False
    owner = occurrence.get('timing_owner')
    return not (occurrence.get('charge') == 'none' and owner and owner != getattr(row, 'name', None))


@_synced
def _l2_driver(rows: Sequence[OperatorRow], family: str, mechanisms: Sequence[str], measured: Mapping[str, float]) -> OperatorRow | None:
    """Choose the actual semantic owner; fall back to measured participant."""
    participants = [row for row in rows if row.mechanism in mechanisms and _row_chargeable(row)]
    if not participants: return None
    named = [row for row in participants if row.mechanism == family]
    return max(named or participants, key=lambda row: (measured.get(row.mechanism, 0.0), row.total_ms))


@_synced
def _row_for(rows: Sequence[OperatorRow], mechanism: str) -> OperatorRow | None: return max((row for row in rows if row.mechanism == mechanism and _row_chargeable(row)), key=lambda row: row.total_ms, default=None)
@_synced
def _component_errors(cell: MeasuredCell, prediction: Prediction, family: str) -> dict[str, float]:
    if cell.trace is None: return {}
    s, l = (max(1, cell.decode_steps), max(1, prediction.layers))
    by_c = cell.trace.by_class or {k: sum((us for n, us in cell.trace.by_name.items() if classify_kernel(n, allow_unresolved=True) == k)) for k in MECHANISMS}
    meas = {m: by_c.get(m, 0.0) / 1000.0 / s / l for m in MECHANISMS}
    if family == 'attention': keys: tuple[str, ...] = ('attention', 'rope', 'kv_cache', 'indexer', 'gdn_linear_attn', 'kda_linear_attn')
    elif family == 'moe':
        has_ep_coll = cell.spec.tp <= 1 or any(prediction.per_layer.get(k, 0.0) > 0 for k in ('gdn_linear_attn', 'kda_linear_attn'))
        keys = ('activation',) if meas['moe_grouped'] <= 0.0 and prediction.per_layer.get('moe_grouped', 0.0) <= 0.0 else ('moe_grouped', 'moe_router', 'activation', 'collective') if has_ep_coll else ('moe_grouped', 'moe_router', 'activation')
    else: keys = (family,) if family in {'norm_residual', 'hyperconnection'} else ()
    return {k: prediction.per_layer.get(k, 0.0) - meas[k] for k in keys if prediction.per_layer.get(k, 0.0) > 0 or meas[k] > 0}
@_synced
def _phase_body(prediction: Prediction, phase: str) -> float: return (prediction.decode_body_ms if phase == 'decode' else prediction.prefill_body_ms) or prediction.body_ms
@_synced
def _step_series(cell: MeasuredCell) -> tuple[float, ...]:
    if cell.spec.phase == 'decode' and cell.trace_quality == 'mixed_prefill': return () if cell.step_trace_ms == 0.0 else _decode_segments(cell.trace)
    if cell.spec.phase != 'decode': return (cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else ()
    segments = tuple((us / 1000.0 for us in getattr(cell.trace, 'step_us', ()) or () if us > 0))
    return () if not segments else _decode_segments(cell.trace) or ((cell.step_trace_ms,) if cell.step_trace_ms and cell.step_trace_ms > 0 else segments)
@_synced
def _latency_comparison(level: str, target: str, predicted_ms: float, measured_ms: float, cell: MeasuredCell, operator: str, guard: str, pipe: str, formula: str, segment: int, uncancelled_ms: float=0.0, per_step: Sequence[float]=()) -> Comparison:
    z = _z(); Comparison = z.Comparison
    series = tuple((float(v) for v in per_step if v > 0)) or ((measured_ms,) if measured_ms > 0 else ())
    details = tuple(((idx, val, predicted_ms, math.nan if not (math.isfinite(predicted_ms) and math.isfinite(val)) else (predicted_ms - val) / val if val > 0 else math.inf if predicted_ms > 0 else 0.0) for idx, val in enumerate(series)))
    return Comparison(level, target, 'service' if level == 'L4' else 'model', predicted_ms, mean(series) if series else measured_ms, operator, guard, pipe, formula, segment, uncancelled_ms, cell.spec.cell_id, details)
@_synced
def compare_cell(cell: MeasuredCell, prediction: Prediction) -> list[Comparison]:
    z = _z(); Comparison, KernelTrace = z.Comparison, z.KernelTrace
    measured_subgraph_us = z.measured_subgraph_us
    _row_for, _step_series = z._row_for, z._step_series
    if cell.trace is None or getattr(cell.trace, 'incomplete', False) or prediction.layers <= 0: return []
    steps, layers = (max(1, cell.decode_steps), max(1, prediction.layers)); comparisons: list[Comparison] = []; components: dict[str, float] = {}
    has_segs = bool(_decode_segments(cell.trace)) and cell.step_trace_ms != 0.0
    trace_usable = cell.trace_quality != 'dp_barrier_skew' and (cell.trace_quality in {'ok', 'warmup_contaminated_ttft', 'rank_step_alignment_unresolved'} or cell.spec.phase == 'prefill' or has_segs)
    attn_tot = cell.trace.by_class.get('attention', 0.0) + cell.trace.by_class.get('gdn_linear_attn', 0.0) + cell.trace.by_class.get('kda_linear_attn', 0.0)
    idle_dp = cell.spec.dp > cell.spec.concurrency and attn_tot <= 0.0
    t_segs = tuple((seg for seg in getattr(cell.trace, 'segments', ()) or () if seg[0] > 100.0 and seg[1])); use_segs = len(t_segs) >= 2
    meas_map = {m: cell.trace.by_class.get(m, 0.0) / 1000.0 / steps / layers for m in MECHANISMS}
    l1_mechs = (('collective',) if idle_dp and (not cell.trace.counts) else () if idle_dp else MECHANISMS) if trace_usable else ()
    for mechanism in l1_mechs:
        measured, predicted = (meas_map[mechanism], float(prediction.per_layer.get(mechanism, 0.0)))
        if measured <= 0 and (not math.isfinite(predicted) or predicted <= 0) and math.isfinite(predicted): continue
        row = _row_for(prediction.rows, mechanism); components[mechanism] = predicted - measured; s_vals = [seg[1].get(mechanism, 0.0) / 1000.0 / layers for seg in t_segs] if use_segs else []
        details = tuple(((idx, v, predicted, (predicted - v) / v) for idx, v in enumerate(s_vals) if v > 0)) if any((v > 0 for v in s_vals)) else (((0, measured, predicted, (predicted - measured) / measured),) if measured > 0 else ())
        comparisons.append(Comparison('L1', mechanism, mechanism, predicted, measured, row.name if row else f'missing:{mechanism}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, 0.0, cell.spec.cell_id, details))
    uncancelled = max(0.0, sum((abs(v) for v in components.values())) - abs(sum(components.values())))
    for family in SUBGRAPHS if trace_usable and (not idle_dp) else ():
        measured = measured_subgraph_us(cell.trace, family) / 1000.0 / steps / layers; predicted = float(prediction.subgraphs.get(family, 0.0))
        if measured <= 0 and (not math.isfinite(predicted) or predicted <= 0) and math.isfinite(predicted): continue
        errors = _component_errors(cell, prediction, family); unc_l2 = max(0.0, sum((abs(v) for v in errors.values())) - abs(sum(errors.values())))
        row = _l2_driver(prediction.rows, family, tuple(errors), meas_map)
        s_vals = [measured_subgraph_us(KernelTrace(seg[0], seg[1], seg[2], seg[3]), family) / 1000.0 / layers for seg in t_segs] if use_segs else []
        details = tuple(((idx, v, predicted, (predicted - v) / v) for idx, v in enumerate(s_vals) if v > 0)) if any((v > 0 for v in s_vals)) else (((0, measured, predicted, (predicted - measured) / measured),) if measured > 0 else ())
        comparisons.append(Comparison('L2', family, family, predicted, measured, row.name if row else f'missing:{family}', row.guard_text if row else 'unmodeled', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, unc_l2, cell.spec.cell_id, details))
    unsegmented_pf = cell.trace_quality == 'mixed_prefill' and (not has_segs) or cell.trace_quality in {'dp_barrier_skew'} or idle_dp; series = () if unsegmented_pf else _step_series(cell)
    step_ms = 0.0 if unsegmented_pf else mean(series) if series else cell.step_trace_ms or 0.0; unc_step = uncancelled * layers
    target = f'{cell.spec.phase}_step_trace'
    if step_ms > 0:
        eligible = [item for item in prediction.rows if _row_chargeable(item)]
        row = max(eligible, key=lambda item: item.total_ms) if eligible else None
        comparisons.append(_latency_comparison('L3', target, _phase_body(prediction, cell.spec.phase), step_ms, cell, row.name if row else f'missing:{target}', row.guard_text if row else '', row.dominant_pipe if row else '', row.formula if row else '', row.segment if row else -1, unc_step, series))
    else:
        comparisons.append(Comparison('L3', target, 'model', 0.0, 0.0, 'missing:trace', 'uncovered', '', '', -1, 0.0, cell.spec.cell_id))
    if cell.spec.phase != 'prefill':
        if cell.tpot_ms and (cell.tpot_ms > 0) and (cell.trace_quality not in {'warmup_contaminated_tpot', 'dp_barrier_skew'}):
            _l4_step = prediction.step_ms if prediction.step_ms is not None and math.isfinite(prediction.step_ms) and prediction.step_ms > 0 else (prediction.body_ms if math.isfinite(prediction.body_ms) and prediction.body_ms > 0 else _phase_body(prediction, 'decode'))
            _l4_basis = prediction.public_basis if prediction.step_ms is not None else 'body + framework span'
            comparisons.append(_latency_comparison('L4', 'decode_step_tpot', _l4_step, cell.tpot_ms, cell, 'service_framework', 'no_discrete_guard', 'host', _l4_basis, -1, unc_step))
        elif cell.tpot_ms and cell.tpot_ms > 0:
            comparisons.append(Comparison('L4', 'decode_step_tpot', 'service', 0.0, 0.0, 'missing:tpot', 'uncovered', '', '', -1, 0.0, cell.spec.cell_id))
    elif cell.ttft_ms and cell.ttft_ms > 0 and (prediction.ttft_ms is not None) and (cell.trace_quality not in {'warmup_contaminated_ttft', 'dp_barrier_skew'}) and (not unsegmented_pf):
        comparisons.append(_latency_comparison('L4', 'prefill_step_ttft', prediction.ttft_ms, cell.ttft_ms, cell, 'prefill_body', 'no_discrete_guard', 'host', 'prefill body + queue/launch', -1, unc_step))
    elif cell.ttft_ms and cell.ttft_ms > 0:
        comparisons.append(Comparison('L4', 'prefill_step_ttft', 'service', 0.0, 0.0, 'missing:ttft', 'uncovered', '', '', -1, 0.0, cell.spec.cell_id))
    declared_partial = set(prediction.partial_targets or ())
    predicted_conditional = set() if prediction.formal_point else {
        'L1:collective', 'L2:moe', 'L3:prefill_step_trace', 'L3:decode_step_trace',
        'L4:decode_step_tpot', 'L4:prefill_step_ttft'}
    declared_partial |= predicted_conditional

    def _partial(item: Comparison) -> bool:
        key = f'{item.level}:{item.target}'
        if key in declared_partial: return True
        if item.level in {'L3', 'L4'} and any(value.startswith(item.level + ':') for value in declared_partial): return True
        return bool(item.conditional)

    return [replace(item, conditional=_partial(item)) for item in comparisons]
@_synced
def _fused_evidence(cell: MeasuredCell, target: str) -> bool:
    if cell.trace is None: return False
    candidates = [(us, name) for name, us in cell.trace.by_name.items() if classify_kernel(name, allow_unresolved=True) in _TARGET_CLASSES.get(target, {target})]
    return bool(candidates) and _has(max(candidates)[1], _FUSED_TARGETS.get(target, ()))
@_synced
def diagnose(comparison: Comparison, cell: MeasuredCell, prediction: Prediction) -> Diagnosis | None:
    z = _z(); Diagnosis = z.Diagnosis
    _row_for, _step_series = z._row_for, z._step_series
    if comparison.measured_ms <= 0:
        if comparison.predicted_ms <= 0: return None
        return Diagnosis(comparison.level, comparison.target, comparison.mechanism, math.inf, math.inf, 'confirmed_structural_gap', comparison.operator, comparison.segment, comparison.dominant_pipe, comparison.guard, comparison.formula, f'remove or justify {comparison.operator}: the declared family is absent from this measured implementation', f'measured class absent; predicted {comparison.predicted_ms:.6f}ms')
    max_step = max((abs(d[3]) for d in comparison.step_details), default=comparison.unsigned_error); unc_ratio = comparison.uncancelled_ms / max(comparison.measured_ms, 1e-12)
    if math.isfinite(comparison.unsigned_error) and math.isfinite(max_step) and (max(comparison.unsigned_error, max_step) <= ERROR_THRESHOLD) and (unc_ratio <= ERROR_THRESHOLD): return None
    mechanism = comparison.mechanism; row = _row_for(prediction.rows, mechanism); guard, pipe = (comparison.guard, comparison.dominant_pipe); notes = set(cell.spec.notes) | set(prediction.notes)
    if not math.isfinite(comparison.predicted_ms) or comparison.predicted_ms <= 0: physical, fix = ('confirmed_structural_gap', f'add the missing {mechanism} family/operator to subgraphs and compile {comparison.target} with declared geometry')
    elif comparison.level in {'L3', 'L4'}: physical, fix = ('confirmed_structural_gap', f'reconcile {comparison.target} boundary: body arithmetic is declared, while service launch/scheduler/queue spans are not')
    elif comparison.target == 'norm_residual' and comparison.predicted_ms < 0.1 * comparison.measured_ms: physical, fix = ('confirmed_structural_gap', f'add the fixed kernel-launch span to {comparison.operator}; the declared norm/residual arithmetic is below one launch quantum')
    elif unc_ratio > ERROR_THRESHOLD: physical, fix = ('fusion_boundary', f'repair {comparison.target} composition: component errors cancel; separate the fused boundary before summing serial costs')
    elif mechanism == 'collective' or comparison.target == 'collective': physical, fix = ('collective_skew', f'correct {comparison.operator} link stage: replace mean bandwidth with slowest-rank skew plus launch latency')
    elif _fused_evidence(cell, comparison.target): physical, fix = ('fusion_boundary', f'correct {comparison.operator} fusion boundary: merge or split the declared internal materialisation at the measured fused kernel')
    elif any((k in {'M_TILES', 'TOKEN_TILES', 'SPLITS', 'TILES'} for k, _ in (row.regime if row else ()))): physical, fix = ('tiling_wave_step', f'correct {comparison.operator} guard {guard}: use ceil(tiles/cores) waves and the real tail-row wave instead of a smooth tile mean')
    elif pipe in {'mte2', 'mte1', 'mte3', 'hbm', 'link'}: physical, fix = ('mte2_granule_amplification', f'correct {comparison.operator} stage {comparison.segment} {pipe} bytes: align every transfer to the physical granule and count descriptor round-up')
    elif 'structural_proxy' in notes or 'no_structural_case' in notes: physical, fix = ('confirmed_structural_gap', f'replace the structural proxy for {comparison.target} with the served model declaration; do not fit measured latency')
    else: physical, fix = ('confirmed_structural_gap', f'extend {comparison.operator} segment {comparison.segment} with the declared physical boundary term that the measurement exposes')
    suffix = ' [structural proxy]' if 'structural_proxy' in notes else ''
    ev = f"measured={comparison.measured_ms:.6f}ms predicted={comparison.predicted_ms:.6f}ms signed={comparison.signed_error:+.2%} guard={guard or 'none'} pipe={pipe or 'none'}"
    return Diagnosis(comparison.level, comparison.target, mechanism, comparison.signed_error, max(comparison.unsigned_error, max_step), physical, comparison.operator, comparison.segment, pipe, guard, comparison.formula, fix + suffix, ev)
@_synced
def diagnose_cell(comparisons: Sequence[Comparison], cell: MeasuredCell, prediction: Prediction) -> list[Diagnosis]:
    z = _z(); Diagnosis = z.Diagnosis
    found = [item for item in (diagnose(c, cell, prediction) for c in comparisons) if item is not None]
    for c in comparisons:
        if c.level == 'L2' and c.measured_ms > 0 and (c.uncancelled_ms / c.measured_ms > ERROR_THRESHOLD) and (not any((it.level == 'L2' and it.target == c.target for it in found))): found.append(Diagnosis('L2', c.target, c.mechanism, c.signed_error, c.unsigned_error, 'fusion_boundary', c.operator, c.segment, c.dominant_pipe, c.guard, c.formula, f'repair {c.target} composition: component errors cancel; separate the fused boundary before summing serial costs', f'uncancelled_l1={c.uncancelled_ms:.6f}ms measured={c.measured_ms:.6f}ms'))
    return found
@_synced
def _quantile(values: Sequence[float], fraction: float) -> float: ordered = sorted(values); return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)] if ordered else 0.0
@_synced
def aggregate(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[Comparison]] = defaultdict(list)
    for comparison in comparisons: groups[comparison.level, comparison.target].append(comparison)
    result = []
    for (level, target), items in sorted(groups.items()):
        valid = [item for item in items if item.measured_ms > 0]; unsigned = [item.unsigned_error for item in valid]; step_signed: list[float] = []; step_unsigned: list[float] = []; resolved_unsigned: list[float] = []
        uncancelled: list[float] = []; conditional_steps = 0; conditional_cells = 0
        for item in valid:
            details = item.step_details or ((0, item.measured_ms, item.predicted_ms, item.signed_error),); step_signed.extend((d[3] for d in details)); step_unsigned.extend((abs(d[3]) for d in details))
            if item.conditional:
                conditional_steps += len(details); conditional_cells += 1
            else:
                resolved_unsigned.extend((abs(d[3]) for d in details))
            unc_add = item.uncancelled_ms / item.measured_ms if item.measured_ms > 0 else 0.0; uncancelled.extend((abs(d[3]) + unc_add for d in details))
        if not any((v > 0 for v in uncancelled)): uncancelled = list(step_unsigned)
        pass_rate = (sum((math.isfinite(v) and v <= ERROR_THRESHOLD for v in resolved_unsigned)) / len(resolved_unsigned) if resolved_unsigned else 0.0)
        above_10 = sum((not (math.isfinite(v) and v <= ERROR_THRESHOLD) for v in step_unsigned)); s_max = math.inf if any((not math.isfinite(v) for v in step_unsigned)) else max(step_unsigned) if step_unsigned else 0.0
        conditional_above = sum((not (math.isfinite(abs(v)) and abs(v) <= ERROR_THRESHOLD) for item in valid if item.conditional for v in (tuple(d[3] for d in item.step_details) or (item.signed_error,))))
        result.append({'level': level, 'target': target, 'unit': 'ms/step', 'samples': len(step_unsigned), 'resolved_samples': len(resolved_unsigned), 'conditional_samples': conditional_steps, 'conditional_cells': conditional_cells, 'cells': len(valid), 'resolved_cells': len(valid) - conditional_cells, 'unmatched': len(items) - len(valid), 'measured_ms_mean': mean((item.measured_ms for item in valid)) if valid else 0.0, 'predicted_ms_mean': mean((item.predicted_ms for item in valid)) if valid else 0.0, 'signed_error_mean': mean((item.signed_error for item in valid)) if valid else 0.0, 'unsigned_error_median': median(unsigned) if unsigned else 0.0, 'unsigned_error_p90': _quantile(unsigned, 0.9), 'above_10pct': above_10, 'conditional_above_10pct': conditional_above, 'step_err_p50': median(step_unsigned) if step_unsigned else 0.0, 'step_err_p90': _quantile(step_unsigned, 0.9), 'step_err_max': s_max, 'signed_p50': median(step_signed) if step_signed else 0.0, 'uncancelled_p50': median(uncancelled) if uncancelled else 0.0, 'pass_rate_10pct': pass_rate, 'within_10pct_rate': pass_rate, 'conditional': conditional_cells > 0})
    return result
@_synced
def _step_rows(comparisons: Sequence[Comparison]) -> list[dict[str, Any]]:
    return [{'cell': item.cell_id, 'level': item.level, 'target': item.target, 'step': detail[0], 'measured_ms': detail[1], 'predicted_ms': detail[2], 'signed_error': detail[3]} for item in comparisons for detail in item.step_details]
@_synced
def _category_label(level: str, target: str) -> str:
    z = _z()
    return z._SUBGRAPH_LABELS.get(target, target) if level == 'L2' else z._MECH_LABELS.get(target, target) if level == 'L1' else z._STEP_LABELS.get(target, target)
@_synced
def cell_to_dict(cell: MeasuredCell) -> dict[str, Any]:
    s, t = (cell.spec, cell.trace); mc = str(s.model_case.relative_to(ROOT)) if s.model_case and s.model_case.is_relative_to(ROOT) else s.model_case.name if s.model_case else ''
    return {'cell_id': s.cell_id, 'dataset': s.dataset, 'phase': s.phase, 'model_case': mc, 'model_label': s.model_label, 'prompt_tokens': s.prompt_tokens, 'concurrency': s.concurrency, 'max_tokens': s.max_tokens, 'tp': s.tp, 'dp': s.dp, 'ep': s.ep, 'pp': s.pp, 'graph_buckets': list(s.graph_buckets), 'graph_bucket': s.graph_bucket, 'notes': list(s.notes), 'sequences_per_replica': s.sequences_per_replica, 'tokens_per_sequence': s.tokens_per_sequence, 'synthetic_layers': s.synthetic_layers, 'synthetic_experts': s.synthetic_experts, 'synthetic_topk': s.synthetic_topk, 'source_config': None if s.source_config is None else str(s.source_config), 'source_config_sha256': s.source_config_sha256, 'source_deploy_sha256': s.source_deploy_sha256, 'source_file_sha256': s.source_file_sha256, 'source_origin': s.source_origin, 'source_weight_dir': None if s.source_weight_dir is None else str(s.source_weight_dir), 'source_case_dir': None if s.source_case_dir is None else str(s.source_case_dir), 'source_header_archive': None if s.source_header_archive is None else str(s.source_header_archive), 'require_source': s.require_source, 'source_reject_reason': s.source_reject_reason, 'source_binding': _plain_source_value(s.source_binding or {}), 'ttft_ms': cell.ttft_ms, 'tpot_ms': cell.tpot_ms, 'step_trace_ms': cell.step_trace_ms, 'decode_steps': cell.decode_steps, 'success': cell.success, 'failure': cell.failure, 'trace_quality': cell.trace_quality, 'request_tokens': int(getattr(cell, 'request_tokens', 0)), 'source_conflict': str(getattr(cell, 'source_conflict', '')), 'source_measured': str(getattr(cell, 'source_measured', '')), 'trace': None if t is None else {'duration_us': t.duration_us, 'by_class': dict(t.by_class), 'by_name': dict(t.by_name), 'counts': dict(t.counts), 'step_us': list(t.step_us), 'segments': [[seg[0], dict(seg[1]), dict(seg[2]), dict(seg[3])] for seg in getattr(t, 'segments', ()) or ()], 'union_duration_us': t.union_duration_us, 'forward_span_us': t.forward_span_us, 'incomplete': t.incomplete, 'incomplete_reason': t.incomplete_reason}}
@_synced
def cell_from_dict(raw: Mapping[str, Any]) -> MeasuredCell:
    z = _z(); CellSpec, MeasuredCell, KernelTrace = z.CellSpec, z.MeasuredCell, z.KernelTrace
    s = raw.get('spec') if isinstance(raw.get('spec'), Mapping) else raw; t = raw.get('trace') if isinstance(raw.get('trace'), Mapping) else raw if 'by_class' in raw else None
    mc_s = str(s.get('model_case') or ''); mc = (ROOT / mc_s if (ROOT / mc_s).exists() else CASES_DIR / Path(mc_s).name if (CASES_DIR / Path(mc_s).name).exists() else Path(mc_s)) if mc_s else None
    if mc is None or not mc.exists(): mc, _, _ = resolve_model(str(s.get('model_label') or s.get('cell_id') or ''))
    cid, ml = (str(s.get('cell_id') or ''), str(s.get('model_label') or 'unresolved')); notes = tuple(dict.fromkeys(str(x) for x in s.get('notes') or ())); nra = s.get('norm_runtime_abi') or s.get('norm_runtime'); notes = notes + (f'norm_runtime_abi:{json.dumps(nra, sort_keys=True)}',) if isinstance(nra, Mapping) else notes; iwf = s.get('indexer_weight_formats'); notes = notes + (f'indexer_weight_formats:{json.dumps(iwf, sort_keys=True)}',) if isinstance(iwf, Mapping) else notes
    spec = CellSpec(cid, str(s.get('dataset') or 'bench'), str(s.get('phase') or 'decode'), mc, ml, int(s.get('prompt_tokens') or 1), int(s.get('concurrency') or 1), int(s.get('max_tokens') or 1), int(s.get('tp') or 1), int(s.get('dp') or 1), int(s.get('ep') or 1), int(s.get('pp') or 1), tuple((int(x) for x in s.get('graph_buckets') or ())), int(s.get('graph_bucket') or 0), notes, int(s.get('sequences_per_replica') or 0), int(s.get('tokens_per_sequence') or 0), int(s.get('synthetic_layers') or 0), int(s.get('synthetic_experts') or 0), int(s.get('synthetic_topk') or 0), (Path(str(s.get('source_config') or s.get('model_config_path'))) if (s.get('source_config') or s.get('model_config_path')) else None), str(s.get('source_config_sha256') or s.get('model_config_sha256') or ''), str(s.get('source_deploy_sha256') or ''), (Path(s['source_weight_dir']) if s.get('source_weight_dir') else None), (Path(s['source_case_dir']) if s.get('source_case_dir') else None), (Path(s['source_header_archive']) if s.get('source_header_archive') else None), bool(s.get('require_source')), str(s.get('source_reject_reason') or ''), str(s.get('source_file_sha256') or ''), str(s.get('source_origin') or ''))
    spec = resolve_and_apply_source(spec)
    bind_raw = ({**s, 'source_config_sha256': '', 'model_config_sha256': ''}
                if spec.source_reject_reason == 'source_config_sha256_mismatch' else s)
    if isinstance(s.get('source_binding'), Mapping): spec = replace(spec, source_binding=_freeze_source_value(s['source_binding']))
    if spec.model_case is not None and spec.model_case.exists():
        spec = replace(spec, source_binding=_source_binding(spec))
    if (corrected := glm51_source_case(model_label=spec.model_label, model_case=spec.model_case)) is not None and corrected != spec.model_case: spec = replace(spec, model_case=corrected)
    tr = None if t is None else KernelTrace(float(t.get('duration_us') or 0.0), dict(t.get('by_class') or {}), dict(t.get('by_name') or {}), {k: int(v) for k, v in (t.get('counts') or {}).items()}, tuple((float(x) for x in t.get('step_us') or ())), tuple(((float(g[0]), dict(g[1] or {}), dict(g[2] or {}), {k: int(v) for k, v in (g[3] or {}).items()}) for g in t.get('segments') or ())), float(t.get('union_duration_us') or 0.0), float(t.get('forward_span_us') or 0.0), bool(t.get('incomplete', False)), str(t.get('incomplete_reason') or ''))
    steps = int(raw.get('decode_steps') or 1); st_ms = None if raw.get('step_trace_ms') is None else float(raw['step_trace_ms'])
    if tr is not None and tr.union_duration_us >= sum(tr.by_class.values()) > 0 and tr.duration_us > 1.25 * tr.union_duration_us: st_ms = tr.union_duration_us / 1000.0 / max(1, steps)
    if str(s.get('dataset') or '') == 'out':
        alias = _header_alias(s); spec = replace(spec, source_header_archive=alias) if alias else spec
        spec = _bind_original_deployment(spec, bind_raw)
        if spec.source_config is not None:
            resolved = resolve_source_file(spec)
            spec = apply_source_resolution(spec, resolved)
            if spec.source_deploy_sha256 and not resolved.error:
                spec = replace(spec, source_origin='deployment', source_file_sha256=resolved.actual_sha256)
    return MeasuredCell(spec, (), tr, None if raw.get('ttft_ms') is None else float(raw['ttft_ms']), None if raw.get('tpot_ms') is None else float(raw['tpot_ms']), st_ms, steps, bool(raw.get('success', True)), str(raw.get('failure') or ''), str(raw.get('trace_quality') or 'ok'), int(raw.get('request_tokens') or 0), str(raw.get('source_conflict') or ''), str(raw.get('source_measured') or ''))
@_synced
def load_benchmark_jsonl(path: Path, *, roots: Sequence[Path] | None=None) -> list[MeasuredCell]:
    try: from .zero_shot_actual_entry import apply_original_observations as recover, DEFAULT_ROOTS
    except ImportError: from zero_shot_actual_entry import apply_original_observations as recover, DEFAULT_ROOTS
    return recover([cell_from_dict(json.loads(line)) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()], roots=roots or DEFAULT_ROOTS)
@lru_cache(maxsize=1)
def _static_source_is_blind() -> bool:
    import inspect; text = Path(_z().__file__).read_text(encoding='utf-8'); banned = ('_EP_' + 'S', '_qwen_l1_' + 'scale', '_k3_' + 'l1', '_ep1_l1_' + 'scale', '_U' + 'G', '_V' + 'G')
    return not any((name in text for name in banned)) and all((tok not in inspect.getsource(predict_cell) for tok in ('MeasuredCell', '.trace', 'by_name', 'by_class', 'ttft_ms', 'tpot_ms')))
@_synced
def _source_is_blind() -> bool:
    return _static_source_is_blind()
@lru_cache(maxsize=1)
def _static_no_empirical_curve_fit() -> bool:
    import ast, inspect, mindie_sim.prediction.piecewise as _pw; banned = ('_harm' + '1', '_harm' + '2', 'harm' + 'onic', 'is_' + 'glm', 'is_' + 'dsv41', 'is_' + 'qwen', 'is_' + 'k3', 'is_' + 'v41', '_glm' + '_', '_dsv41' + '_', '_qwen' + '_', '_k3' + '_')
    trig = {'cos', 'sin', 'acos', 'asin', 'atan', 'atan2'}; svars = {'q_len', 'prompt_tokens', 'kv_len', 'seq_len', 'context', 'tokens', 'concurrency', 'layers', 'head_dim', 'dk'}; glits = {45, 74, 75, 512, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072}
    for p in (Path(_z().__file__), *sorted(Path(_pw.__file__).resolve().parent.rglob('*.py'))):
        for n in ast.walk(ast.parse(p.read_text(encoding='utf-8'))):
            if isinstance(n, ast.ImportFrom) and any((a.name in trig for a in n.names)): return False
            if isinstance(n, ast.Call) and ((isinstance(n.func, ast.Attribute) and n.func.attr in trig) or (isinstance(n.func, ast.Name) and n.func.id in trig)): return False
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and isinstance(n.right, ast.Constant) and (n.right.value == 17): return False
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Name, ast.arg)) and any((b in (getattr(n, 'name', '') or getattr(n, 'id', '') or getattr(n, 'arg', '')).lower() for b in banned)): return False
            if isinstance(n, ast.Compare) and p == Path(_z().__file__) and any((({s.id for s in [*ast.walk(l), *ast.walk(r)] if isinstance(s, ast.Name)} & svars) and ({int(s.value) for s in [*ast.walk(l), *ast.walk(r)] if isinstance(s, ast.Constant) and isinstance(s.value, int) and (not isinstance(s.value, bool))} & glits)) for l, r in zip([n.left, *n.comparators], n.comparators)): return False
    if 'theta.tiles' in inspect.getsource(predict_cell) or inspect.getsource(predict_cell).count('model_label') > 2 or any(('model_label' in inspect.getsource(fn) for fn in (_raw_case, _structure_fingerprint, _model_for_instantiation, _ep_ranks, _service_ttft_overhead_ms, _component_errors))): return False
    return True
@_synced
def _no_empirical_curve_fit(predictions: Sequence[Prediction]=()) -> bool:
    if not _static_no_empirical_curve_fit():
        return False
    return all((p.layers > 0 and bool(p.rows) and all((isinstance(v, (int, float)) and math.isfinite(v) and (v >= 0.0) for v in (*p.per_layer.values(), *p.subgraphs.values(), p.body_ms, p.decode_body_ms, p.prefill_body_ms))) and (abs(sum(p.per_layer.values()) * p.layers - sum((r.total_ms for r in p.rows))) <= 1e-05) and ('_pd_' in p.cell_id or p.public_events > 0 or abs(p.body_ms - (p.prefill_body_ms if p.decode_body_ms == 0.0 else p.decode_body_ms)) <= 1e-06) for p in predictions))
@_synced
def acceptance(result: Mapping[str, Any], *, require_all_21: bool=False) -> dict[str, Any]:
    z = _z(); _REQUIRED_BENCH, ERROR_THRESHOLD = z._REQUIRED_BENCH, z.ERROR_THRESHOLD
    levels = {(row['level'], row['target']): row for row in result['levels']}; failures = ['incomplete_coverage'] if result['coverage']['failed'] or result['skipped'] else []
    if not result.get('measurement_blind'): failures.append('measurement_not_blind')
    if not bool(result.get('no_empirical_curve_fit', False)): failures.append('empirical_curve_fit_detected')
    if not (wanted := (_REQUIRED_BENCH if require_all_21 else tuple(levels))): failures.append('no_levels')
    for key in wanted:
        row = levels.get(key)
        if row is None or row['samples'] <= 0 or row['unmatched']: failures.append(f'missing:{key[0]}:{key[1]}'); continue
        if row.get('conditional_samples', 0) or row.get('conditional', False): failures.append(f'conditional:{key[0]}:{key[1]}')
        if any((not math.isfinite(float(row.get(k, math.nan))) or float(row[k]) > ERROR_THRESHOLD for k in ('step_err_p50', 'step_err_max', 'uncancelled_p50'))) or row['above_10pct']: failures.append(f'threshold:{key[0]}:{key[1]}')
    return {'pass': not failures, 'failures': failures}
@_synced
def run_validation(*, roots: Sequence[Path] | None=None, include_historical: bool=True, max_cells: int=0, benchmark_jsonl: Path | None=None, trace_cache: Path | None=None) -> dict[str, Any]:
    z = _z(); roots = tuple(z.WORKSTREAM_ROOTS if roots is None else roots)
    load_historical_inventory, discover_workstream, attach_trace = z.load_historical_inventory, z.discover_workstream, z.attach_trace
    predict_cell, classify_kernel, _native_forecast = z.predict_cell, z.classify_kernel, z._native_forecast
    _source_is_blind, _no_empirical_curve_fit = z._source_is_blind, z._no_empirical_curve_fit
    _COMPILED_MODELS, _COMPILED_HARDWARE = z._COMPILED_MODELS, z._COMPILED_HARDWARE
    _COMPILED_DRAFT, _COMPILED_SELECTOR = z._COMPILED_DRAFT, z._COMPILED_SELECTOR
    _SOURCE_GROUP_CACHE, _PUBLIC_CONSUMED_CACHE = z._SOURCE_GROUP_CACHE, z._PUBLIC_CONSUMED_CACHE
    _PUBLIC_CACHE, _AGG_CACHE = z._PUBLIC_CACHE, z._AGG_CACHE
    from mindie_profiler.structural_inference import infer_trace_structure; inventory = load_historical_inventory() if include_historical else []; initial_modules = frozenset(sys.modules)
    cells = sorted(load_benchmark_jsonl(benchmark_jsonl) if benchmark_jsonl is not None else [cell for root in roots for cell in discover_workstream(Path(root))], key=lambda cell: (cell.spec.dataset, cell.spec.cell_id))
    cells = cells[:max_cells] if max_cells > 0 else cells; predictions: dict[Any, Prediction] = {}; comparisons: list[Comparison] = []; diagnosis: list[Diagnosis] = []; skipped: Counter[str] = Counter()
    unresolved: dict[str, list[Any]] = defaultdict(lambda: [0, 0.0, 0]); decisions: dict[str, Any] = {}; evaluated = with_trace = with_model = failed = mixed_pf = 0
    for cell in cells:
        if cell.spec.model_case is not None: with_model += 1
        if not cell.success: failed += 1; skipped[cell.failure or 'unsuccessful_cell'] += 1; continue
        key = cell.spec.prediction_key()
        if key not in predictions: predictions[key] = predict_cell(cell.spec)
        pred = predictions[key]
        cell = attach_trace(cell, cache_dir=trace_cache)
        if cell.trace is not None: with_trace += 1
        if cell.trace_quality == 'mixed_prefill': mixed_pf += 1
        if cell.trace is None: skipped['no_kernel_trace'] += 1; continue
        for k, us in cell.trace.by_name.items():
            if classify_kernel(k, allow_unresolved=True) == 'unresolved': u = unresolved[k]; u[0] += int(cell.trace.counts.get(k, 1)); u[1] += float(us); u[2] += 1
        if len(decisions) < 64 and ('unresolved' in cell.trace.by_class or any((x in k.lower() for k in cell.trace.by_name for x in ('megamoe', '_minimax_qknorm', 'dflash', 'dspark')))):
            items = infer_trace_structure([{'name': k, 'dur_us': us} for k, us in cell.trace.by_name.items()], explicit_steps=cell.decode_steps, hint_layers=pred.layers, model_hint=cell.spec.model_label).agent_decision_items
            for item in items: decisions.setdefault(f'{item.inferred_role}:{item.operator_name}', {k: getattr(item, k) for k in item.__slots__})
        if pred.layers <= 0: failed += 1; skipped[pred.notes[0] if pred.notes else 'prediction_failed'] += 1; continue
        if cell.trace_quality == 'dp_barrier_skew': failed += 1; skipped[cell.trace_quality] += 1; continue
        cell_comparisons = compare_cell(cell, pred)
        if not cell_comparisons: failed += 1; skipped[cell.trace_quality if cell.trace_quality != 'ok' else 'no_comparisons'] += 1; continue
        evaluated += 1; comparisons.extend(cell_comparisons); diagnosis.extend(diagnose_cell(cell_comparisons, cell, pred))
    coverage = {'cells': len(cells), 'evaluated': evaluated, 'with_kernel_trace': with_trace, 'with_model': with_model, 'failed': failed, 'trace_mixed_prefill': mixed_pf, 'step_samples': sum((len(item.step_details) for item in comparisons)), 'conditional_step_samples': sum((len(item.step_details) for item in comparisons if item.conditional)), 'conditional_targets': sorted({f'{item.level}:{item.target}' for item in comparisons if item.conditional}), 'unresolved_kernels': len(unresolved), 'agent_decisions': len(decisions)}; _COMPILED_MODELS.clear(); _COMPILED_HARDWARE.clear(); _COMPILED_DRAFT.clear(); _COMPILED_SELECTOR.clear(); _SOURCE_GROUP_CACHE.clear(); _PUBLIC_CONSUMED_CACHE.clear(); _PUBLIC_CACHE.clear(); _AGG_CACHE.clear()
    return {'schema': 'mindie-profiler-zero-shot-piecewise-validation/1', 'coverage': coverage, 'skipped': dict(skipped), 'roots': [str(benchmark_jsonl)] if benchmark_jsonl is not None else [str(path) for path in roots], 'historical': {'inventoried': len(inventory), 'existing': sum((1 for item in inventory if item.get('exists'))), 'by_kind': dict(Counter((item['kind'] for item in inventory)))}, 'levels': aggregate(comparisons), 'step_errors': _step_rows(comparisons), 'diagnoses': [item.__dict__ for item in diagnosis], 'diagnosis_counts': dict(Counter((item.physical_mechanism for item in diagnosis))), 'unresolved_kernels': {k: {'calls': v[0], 'total_us': round(v[1], 3), 'cells': v[2]} for k, v in sorted(unresolved.items(), key=lambda x: -x[1][1])}, 'agent_decisions': list(decisions.values()), 'routing_statuses': dict(Counter(str(item.routing_status or 'unresolved') for item in predictions.values())), 'measurement_blind': _source_is_blind(), 'no_empirical_curve_fit': _no_empirical_curve_fit(tuple(predictions.values())), 'forbidden_lookup_imported': any((name.startswith('mindie_sim.prediction.service_regimes') and name not in initial_modules for name in sys.modules)), 'native_forecast': _native_forecast(tuple(predictions.values()))}
@_synced
def render_markdown(result: Mapping[str, Any]) -> str:
    z = _z(); _DIAGNOSIS_LABELS = z._DIAGNOSIS_LABELS
    coverage, counts = (result['coverage'], result['diagnosis_counts']); details = list(result.get('step_errors') or ())
    lines = ['# Zero-shot piecewise validation baseline — Per-Step Latency Error (单步耗时误差)', '', 'Prediction path: `mindie_sim.prediction.subgraphs` + `mindie_sim.prediction.piecewise`; empirical `service_regimes` are not imported. Measured values are read only after each prediction is frozen.', '', 'Focus: **per-step latency** (`ms/step`), not cross-case means. `signed_p50` exposes systematic bias; `uncancelled_p50` exposes positive/negative cancellation among physical components. 验收重点为每个 Step 的单步耗时误差与正负抵消，跨 Case 均值仅保留兼容字段。', '', f"- cells: {coverage['cells']} (evaluated {coverage['evaluated']}, kernel trace {coverage['with_kernel_trace']}, model {coverage['with_model']}, mixed prefill {coverage['trace_mixed_prefill']})", f"- routing statuses: {result.get('routing_statuses') or {}}", f"- per-step samples: {coverage.get('step_samples', 0)} (conditional {coverage.get('conditional_step_samples', 0)})", f"- skipped: {result['skipped'] or 'none'}", f"- historical inventory: {result['historical']['inventoried']} ({result['historical']['existing']} existing)", f"- forbidden lookup imported: {result['forbidden_lookup_imported']}", f"- native forecast bound/unresolved: {((result.get('native_forecast') or {}).get('overall') or {}).get('totals', {}).get('bound_occurrences', 0)}/{((result.get('native_forecast') or {}).get('overall') or {}).get('totals', {}).get('unresolved_occurrences', 0)}", '', '## Coverage by level / 分级覆盖（Per-Step Latency Error / 单步耗时误差）', '', '| level | target (EN / 中文) | step samples | cond samples | cells | unmatched | measured ms | predicted ms | step_err_p50 | step_err_p90 | step_err_max | signed_p50 | uncancelled_p50 | <=10% pass | legacy unsigned med | legacy >10% |', '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in result['levels']: lines.append(f"| {row['level']} | {_category_label(row['level'], row['target'])} | {row['samples']} | {row.get('conditional_samples', 0)} | {row.get('cells', row['samples'])} | {row['unmatched']} | {row['measured_ms_mean']:.6f} | {row['predicted_ms_mean']:.6f} | {row.get('step_err_p50', 0.0):.2%} | {row.get('step_err_p90', 0.0):.2%} | {row.get('step_err_max', 0.0):.2%} | {row.get('signed_p50', 0.0):+.2%} | {row.get('uncancelled_p50', 0.0):.2%} | {row.get('pass_rate_10pct', 0.0):.1%} | {row['unsigned_error_median']:.2%} | {row['above_10pct']} |")
    lines.extend(['', '## Physical diagnoses / 物理诊断类别', '', '| diagnosis category (EN / 中文) | raw key | count |', '|---|---|---:|', *[f'| {_DIAGNOSIS_LABELS.get(name, name)} | `{name}` | {counts.get(name, 0)} |' for name in sorted(set(_DIAGNOSIS_LABELS) | set(counts))]])
    by_key: dict[tuple[str, str], list[float]] = defaultdict(list)
    for detail in details: by_key[detail['cell'], detail['target']].append(detail['signed_error'])
    flips = {k for k, vals in by_key.items() if any((v < 0 for v in vals)) and any((v > 0 for v in vals))}
    worst = sorted(details, key=lambda item: -math.inf if not math.isfinite(item['signed_error']) else -abs(item['signed_error']))[:20]
    lines.extend(['', '## Worst per-step errors (top 20) / 最差单步误差', '', '`±cancel` = the same cell/target has both positive and negative Step errors, so a mean hides the miss; use `step_err_p90` / `step_err_max`. `±cancel` 表示同一 cell/target 的不同 Step 同时出现正负误差，均值会抵消，应看 P90 与最大误差。', '', '| cell | level | target (EN / 中文) | step | measured ms | predicted ms | signed error | ±cancel |', '|---|---|---|---:|---:|---:|---:|:---:|'])
    for item in worst: lines.append(f"| {item['cell']} | {item['level']} | {_category_label(item['level'], item['target'])} | {item['step']} | {item['measured_ms']:.6f} | {item['predicted_ms']:.6f} | {item['signed_error']:+.2%} | {('yes' if (item['cell'], item['target']) in flips else 'no')} |")
    lines.extend(['', '## Repair targets (top 15) / 修复目标', '', '| level | target (EN / 中文) | diagnosis (EN / 中文) | operator | segment | pipe | guard | required fix |', '|---|---|---|---|---:|---|---|---|'])
    for item in result['diagnoses'][:15]: lines.append(f"| {item['level']} | {_category_label(item['level'], item['target'])} | {_DIAGNOSIS_LABELS.get(item['physical_mechanism'], item['physical_mechanism'])} | {item['operator']} | {item['segment']} | {item['dominant_pipe']} | {item['guard']} | {item['required_fix']} |")
    return '\n'.join(lines + [''])
@_synced
def main(argv: Sequence[str] | None=None) -> int:
    z = _z(); WORKSTREAM_ROOTS = z.WORKSTREAM_ROOTS; discover_all_profiling_roots = z.discover_all_profiling_roots
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0]); parser.add_argument('--root', action='append', type=Path, default=None); parser.add_argument('--all-roots', action='store_true'); parser.add_argument('--max-cells', type=int, default=0); parser.add_argument('--no-historical', action='store_true'); parser.add_argument('--json', action='store_true'); parser.add_argument('--benchmark-jsonl', type=Path, default=None); parser.add_argument('--trace-cache', type=Path, default=None); args = parser.parse_args(argv)
    roots = discover_all_profiling_roots() if args.all_roots else tuple(args.root) if args.root else WORKSTREAM_ROOTS; result = run_validation(roots=roots, include_historical=not args.no_historical, max_cells=args.max_cells, benchmark_jsonl=args.benchmark_jsonl, trace_cache=args.trace_cache); print(json.dumps(result, indent=2, sort_keys=True) if args.json else render_markdown(result)); return 0 if acceptance(result, require_all_21=args.benchmark_jsonl is not None)['pass'] else 1


@_synced
def _fused_mechanism(kind: str, members: Sequence[Any]) -> str:
    """Map an active composite from its selected semantic members.

    A1 is the attention macro: its selected native fusion owns attention
    timing.  Every other family borrows the first selected member's physical
    mechanism, so this is source/assembly evidence rather than a name table.
    """
    if kind in {'A1', 'mla_attention', 'dsa_attention'}: return 'attention'
    for member in members:
        try: return operator_mechanism(member, kind)
        except ValueError: continue
    raise ValueError('unclassified_fused_members:' + kind)

@_synced
def _native_bound(call: Any) -> bool:
    """True only for a real source/entry binding, not a truthy null descriptor."""
    if not isinstance(call, Mapping): return False
    source, api = call.get('source'), call.get('api')
    return bool(isinstance(source, Mapping) and isinstance(api, Mapping)
                and source.get('sha256') and api.get('entry'))


@_synced
def _publish_rows(serial: Any, kind: str, count: int) -> tuple[list[tuple[Any, bool, str]], list[tuple[Any, bool, str]]]:
    """Return charged physical rows and uncharged member-attribution rows.
    Uses the actual selected SerialResult; no model/family symbol table.
    """
    _ops_of = _z()._ops_of
    results = tuple(getattr(serial, 'fusion_results', ()) or ())
    consumed = {member.name: result for result in results for member in result.semantic}
    charged, attribution = [], []
    for cost in _ops_of(serial):
        owner = consumed.get(cost.name)
        if owner is None:
            charged.append((cost, True, cost.name))
    for cost in getattr(serial, 'unfused_costs', ()) or ():
        owner = consumed.get(cost.name)
        if owner is not None:
            attribution.append((cost, False, owner.fused.name))
    return charged, attribution


@_synced
def _aggregate(unique: Mapping[str, Any], counts: Mapping[str, int], geometry: Any, state: Any, skipped: list[str], include_draft: bool=False, features: Any=None, supply: Any=None, publish_fused: bool=False, build_rows: bool=True) -> tuple[list[OperatorRow], float, dict[str, float], dict[str, float]]:
    from mindie_sim.prediction.piecewise import attribute_rope; from mindie_sim.prediction.piecewise.composition import contention_envelope, evaluate_serial_split
    from mindie_sim.catalog.context_parallel import dsa_cp_rank_geometry, project_dsa_cp_geometry
    dsa_local = dsa_local_padded = None
    if (features is not None and getattr(features, 'cp_plan', 'none') == 'dsa_cp'
            and int(getattr(features, 'tp', 1) or 1) > 1
            and getattr(geometry, 'phase_name', '') == 'prefill'):
        dsa_local = dsa_cp_rank_geometry(geometry, int(features.tp))
        dsa_local_padded = dsa_local
    dsa_skip = (('dsa_cp_output_all_gather',) if (
        features is not None and getattr(features, 'cp_plan', 'none') == 'dsa_cp'
        and getattr(geometry, 'phase_name', '') != 'prefill') else ())
    skip_set = tuple(dict.fromkeys((*skipped, *dsa_skip)))
    rows, body, per_layer, subgraphs, by_kind = ([], 0.0, defaultdict(float), defaultdict(float), defaultdict(list)); fused_parent_ms = defaultdict(float)
    for fingerprint, compiled in unique.items():
        count, kind = (counts[fingerprint], compiled.instance.kind)
        if kind in {'V0', 'mm_encoder_projector'} and getattr(geometry, 'media_tokens', 0) == 0 or (kind in {'D0', 'spec_decode'} and (not include_draft)): continue
        g_use = geometry; fusions = tuple((c.name for c in compiled.instance.template.fusions))
        has_aux = kind in {'A2', 'swa_attention', 'csa_attention', 'csa2_attention', 'hca_attention'} and getattr(features, 'multistream_window_compressed', False) or (kind in {'gdn_linear_attn', 'kda_linear_attn'} and getattr(features, 'multistream_kda_proj', False))
        if kind in {'O0', 'lm_head_sampler'}:
            selected = _selected_geometry(geometry)
            scope = str(getattr(features, 'final_norm_scope', 'all') or 'all')
            from mindie_sim.prediction.piecewise.model_pipeline import (
                physical_selected_geometry, producing_selected_geometry)
            physical = physical_selected_geometry(geometry)
            has_physical_row = any(
                operator.name == 'hidden_select'
                and str(operator.operator.theta.find('row_binding', '')) == 'selected'
                and str(operator.operator.theta.find('source_runner_class', ''))
                == 'NPUModelRunner'
                for operator in compiled.operators)
            def _o0_geometry(operator: Any) -> Any:
                if operator.name == 'hidden_select':
                    if (scope == 'all' and has_physical_row
                            and physical is not None):
                        produced = producing_selected_geometry(geometry, physical)
                        if produced is not None:
                            return produced
                    return selected or geometry
                if (scope == 'all' and has_physical_row
                        and operator.name in {'lm_head', 'logits_gather', 'sampling'}
                        and physical is not None):
                    return physical
                if operator.name == 'final_norm' and scope == 'selected':
                    return selected or geometry
                if operator.name == 'final_norm':
                    return geometry
                return selected or geometry
            o0_skip = (('hidden_select',)
                       if scope == 'all' and physical is None and has_physical_row
                       else ())
            serial = evaluate_serial_split(
                compiled, geometry, state, geometry_for=_o0_geometry,
                fusion=fusions, skip=o0_skip)
        else:
            if dsa_local is not None:
                def _dsa_geometry(operator: Any, kind: str = kind) -> Any:
                    projected = project_dsa_cp_geometry(
                        kind, str(operator.name), str(operator.family),
                        geometry, geometry, dsa_local, dsa_local_padded)
                    return projected[0] if projected is not None else g_use
                serial = evaluate_serial_split(compiled, geometry, state, geometry_for=_dsa_geometry,
                                               fusion=fusions, skip=skip_set)
            elif skip_set or fusions or has_aux:
                serial = evaluate_serial_split(compiled, g_use, state, fusion=fusions, skip=skip_set)
            else:
                serial = compiled.evaluate(g_use, state)
        by_kind[kind].append((compiled, serial, count)); body += count * float(serial.total_ms)
        if not build_rows: continue
        if publish_fused and fusions:
            charged, attribution = _publish_rows(serial, kind, count)
            parent_names = {r.fused.name for r in getattr(serial, 'fusion_results', ())}
            for cost, charge, owner in charged:
                is_parent = cost.name in parent_names
                member_costs = next((tuple(r.semantic) for r in getattr(serial, 'fusion_results', ()) if r.fused.name == cost.name), ())
                members = tuple(m.name for m in member_costs)
                mechanism = _fused_mechanism(kind, list(member_costs)) if is_parent else operator_mechanism(cost, kind)
                membership = 'selected_fused_owner' if is_parent else 'separate'
                occurrence = ({**cost.native_occurrence} if getattr(cost, 'native_occurrence', None) else {})
                occurrence.update({'repeat': count, 'charge': 'call', 'timing_owner': cost.name,
                                   'membership': membership, 'members': list(members),
                                   'binding': 'source_declared_selected' if _native_bound(getattr(cost, 'native_call', None)) else 'unbound'})
                row = OperatorRow(cost.name, kind, mechanism, subgraph_family(kind), float(cost.duration_ms), count,
                                  cost.regime or (), cost.dominant_pipe, cost.formula, int(cost.segment_index), cost,
                                  native_call=getattr(cost, 'native_call', None), native_occurrence=occurrence,
                                  phase=str(occurrence.get('phase', '')))
                rows.append(row); per_layer[mechanism] += row.total_ms
                if membership == 'selected_fused_owner':
                    if subgraph_family(kind): subgraphs[subgraph_family(kind)] += row.total_ms; fused_parent_ms[subgraph_family(kind)] += row.total_ms
                elif _subgraph_charge(subgraph_family(kind), mechanism, kind): subgraphs[subgraph_family(kind)] += row.total_ms
            for cost, _, owner in attribution:
                member_mechanism = operator_mechanism(cost, kind)
                occurrence = ({**cost.native_occurrence} if getattr(cost, 'native_occurrence', None) else {})
                occurrence.update({'repeat': count, 'charge': 'none', 'timing_owner': owner,
                                   'membership': 'consumed_by_selected_fusion', 'members': [],
                                   'uncharged_ms': float(cost.duration_ms)})
                rows.append(OperatorRow(cost.name, kind, member_mechanism, subgraph_family(kind), 0.0,
                                        count, cost.regime or (), cost.dominant_pipe, cost.formula,
                                        int(cost.segment_index), cost, native_call=getattr(cost, 'native_call', None),
                                        native_occurrence=occurrence, phase=str(occurrence.get('phase', ''))))
        else:
            ops = (getattr(serial, 'unfused_costs', None) or _ops_of(compiled.evaluate(g_use, state))) if fusions or has_aux else _ops_of(serial)
            for cost in ops:
                # A zero-work state row is not a charged operator; publishing it
                # with an empty dominant pipe would fake a physical boundary.
                if float(cost.duration_ms) <= 0 and cost.name != "prepare":
                    continue
                mechanism, family = attribute_rope(kind, operator_mechanism(cost, kind), subgraph_family(kind))
                row = OperatorRow(cost.name, kind, mechanism, family, float(cost.duration_ms), count, cost.regime or (), cost.dominant_pipe, cost.formula, int(cost.segment_index), cost, native_call=getattr(cost, 'native_call', None), native_occurrence=({**cost.native_occurrence, 'repeat': count} if getattr(cost, 'native_occurrence', None) else None), phase=str((getattr(cost, 'native_occurrence', None) or {}).get('phase', ''))); rows.append(row)
                per_layer[mechanism] += row.total_ms
                if _subgraph_charge(family, mechanism, kind): subgraphs[family] += row.total_ms
    if features is not None and per_layer:
        moe_k = ('activation',) if per_layer.get('moe_grouped', 0.0) <= 0.0 else ('moe_grouped', 'moe_router', 'activation', 'collective') if getattr(features, 'tp', 1) <= 1 or any(per_layer.get(k, 0.0) > 0 for k in ('gdn_linear_attn', 'kda_linear_attn')) else ('moe_grouped', 'moe_router', 'activation')
        subgraphs['moe'] = sum((per_layer.get(k, 0.0) for k in moe_k)) + fused_parent_ms.get('moe', 0.0)
    if features is not None and supply is not None:
        f3, f4, f2 = by_kind['F3'] + by_kind['routed_experts'], by_kind['F4'] + by_kind['shared_experts'], by_kind['F2'] + by_kind['moe_token_dispatcher']
        if getattr(features, 'multistream_shared_expert', False) and f3 and f4:
            sh = [e for comp, e, _ in f4 if str(dict(comp.instance.metadata).get('role', '')) != 'join']
            dp_l = [e for comp, e, _ in f2 if 'combine' not in str(dict(comp.instance.metadata).get('role', ''))]
            cb_l = [e for comp, e, _ in f2 if 'combine' in str(dict(comp.instance.metadata).get('role', ''))]
            s_st, s_ms = (_stages_of([op for e in sh for op in _ops_of(e)], supply), sum((float(e.total_ms) for e in sh)))
            for _, e3, c3 in f3:
                rt = dp_l + [e3] + cb_l; r_st, r_ms = (_stages_of([op for e in rt for op in _ops_of(e)], supply), sum((float(e.total_ms) for e in rt)))
                if sh: body += c3 * (float(contention_envelope({}, supply, chains={'routed': r_st, 'shared': s_st}).makespan_ms) - (r_ms + s_ms))
        a1 = by_kind['A1'] + by_kind['mla_attention'] + by_kind['dsa_attention']
        idx_evs = [members[0][1] for members in (by_kind['I0'] + by_kind['indexer_prolog'], by_kind['I1'] + by_kind['lightning_indexer']) if members]
        if getattr(features, 'multistream_attention_indexer', False) and a1 and idx_evs:
            pro_names = {'q_down', 'q_norm', 'q_up', 'q_direct', 'kv_down', 'kv_norm', 'rotary', 'kv_store', 'fused:mla_prolog'}; (_, ea, _), ca = (a1[0], sum((c for _, _, c in a1)))
            pro = [op for op in _ops_of(ea) if op.name in pro_names]
            if pro and idx_evs:
                a_ms, i_ms = (sum((float(op.duration_ms) for op in pro)), sum((float(e.total_ms) for e in idx_evs)))
                body += ca * (float(contention_envelope({}, supply, chains={'attention': _stages_of(pro, supply), 'indexer': _stages_of([op for e in idx_evs for op in _ops_of(e)], supply)}).makespan_ms) - (a_ms + i_ms))
    return (rows, body, dict(per_layer), dict(subgraphs))
@_synced
def _dual_moe(rows: Sequence[OperatorRow], supply: Any, layers: int) -> float | None:
    from mindie_sim.prediction.piecewise.composition import contention_envelope, operator_segment; branches: dict[str, list[Any]] = {'routed': [], 'shared': []}
    for row in rows:
        target = 'routed' if row.kind in {'F3', 'routed_experts'} else 'shared' if row.kind in {'F4', 'shared_experts'} else ''
        if target and _row_chargeable(row) and row.cost is not None:
            for _ in range(max(1, row.count // max(1, layers))): branches[target].append(operator_segment(row.cost, supply))
    return float(contention_envelope({}, supply, chains=branches).makespan_ms) if branches['routed'] and branches['shared'] else None


@_synced
def _source_native_group(spec: CellSpec) -> dict[str, Any] | None:
    """Structural source group plan from the retained campaign, no timings.

    The campaign status owns membership; only profiled rank folders are marked
    observed.  Active logical counts are used only when an explicit source
    condition has exactly the declared membership; otherwise they stay unknown.
    """
    root = Path(spec.source_case_dir) if spec.source_case_dir is not None else None
    status = root / 'status.json' if root is not None else None
    if root is None or not root.is_dir() or status is None or not status.is_file():
        return None
    try:
        payload = status.read_bytes(); meta = json.loads(payload)
    except (OSError, ValueError, TypeError):
        return None
    cell_dir = root / spec.cell_id.removeprefix(root.name + '_') if spec.cell_id.startswith(root.name + '_') else root
    if not cell_dir.is_dir(): cell_dir = root
    op_csvs = sorted(cell_dir.rglob('op_statistic.csv'))
    signature = tuple((str(path), path.stat().st_size, path.stat().st_mtime_ns)
                      for op_csv in op_csvs for path in (op_csv, op_csv.parent / 'kernel_details.csv.gz') if path.exists())
    cache_key = (str(root), spec.cell_id, hashlib.sha256(payload).hexdigest(), signature)
    if cache_key in _SOURCE_GROUP_CACHE: return _SOURCE_GROUP_CACHE[cache_key]
    declared = meta.get('spec') if isinstance(meta.get('spec'), Mapping) else {}
    dp = int(declared.get('dp') or spec.dp or 1); tp = int(declared.get('tp') or spec.tp or 1)
    ep = int(declared.get('ep') or spec.ep or dp * tp or 1)
    expected = max(1, ep)
    observed = []
    for op_csv in op_csvs:
        match = re.search(r'(dp\d+_pp0_tp\d+_dcp\d+_ep\d+_rank\d+)', str(op_csv))
        if match is None: continue
        tag = match.group(1); pm = re.search(r'dp(\d+)_pp0_tp(\d+)_dcp(\d+)_ep(\d+)_rank(\d+)', tag)
        if pm is None: continue
        try:
            first = op_csv.read_text(encoding='utf-8', errors='replace').splitlines()[1].split(',')
            device = int(first[0])
        except (OSError, ValueError, IndexError, TypeError):
            device = None
        item = {'folder': str(op_csv.parent.relative_to(root)), 'host': op_csv.parent.parent.name,
                'tag': tag, 'dp': int(pm.group(1)), 'tp': int(pm.group(2)),
                'ep': int(pm.group(4)), 'logical_rank': int(pm.group(5)), 'device_id': device}
        kernel_csv = op_csv.parent / 'kernel_details.csv.gz'
        mc2 = {}
        if kernel_csv.is_file():
            try:
                import gzip as _gzip
                with _gzip.open(kernel_csv, 'rt', encoding='utf-8', errors='replace') as handle:
                    reader = csv.DictReader(handle)
                    for row in reader:
                        name = str(row.get('Name') or '')
                        if 'MoeDistributeDispatchV3' not in name and 'MoeDistributeCombineV3' not in name:
                            continue
                        key = 'dispatch' if 'Dispatch' in name else 'combine'
                        if key in mc2: continue
                        iraw = str(row.get('Input Shapes') or '').replace('"', '')
                        oraw = str(row.get('Output Shapes') or '').replace('"', '')
                        ivals = [part for part in iraw.split(';') if re.fullmatch(r'\d+,\d+', part)]
                        ovals = [part for part in oraw.split(';') if re.fullmatch(r'\d+,\d+', part)]
                        mc2[key] = {'input_shapes': iraw, 'output_shapes': oraw,
                                    'input_rows': int(ivals[0].split(',')[0]) if ivals else None,
                                    'input_width': int(ivals[0].split(',')[1]) if ivals else None,
                                    'capacity': int(ovals[0].split(',')[0]) if ovals else None,
                                    'block_num': int(row.get('Block Num') or 0) if str(row.get('Block Num') or '').isdigit() else None}
                        if {'dispatch', 'combine'} <= set(mc2): break
            except (OSError, ValueError, TypeError, csv.Error):
                mc2 = {}
        if mc2: item['mc2'] = mc2
        observed.append(item)
    raw = _raw_case(spec)
    runtime = raw.get('runtime') if isinstance(raw, Mapping) else None
    raw_meta = runtime.get('metadata') if isinstance(runtime, Mapping) else None
    selected = 0
    raw_sel = str((raw_meta or {}).get('selected_rank') or '')
    sm = re.search(r'rank(\d+)', raw_sel)
    if sm is not None: selected = int(sm.group(1))
    scenario = (raw_meta or {}).get('source_scenario') if isinstance(raw_meta, Mapping) else None
    conditions = scenario.get('conditions') if isinstance(scenario, Mapping) else None
    active = None; options = []
    if isinstance(conditions, Mapping):
        for key, value in conditions.items():
            if not isinstance(value, Mapping): continue
            counts = value.get('sequences')
            if isinstance(counts, Sequence) and not isinstance(counts, (str, bytes)):
                counts = tuple(int(c) for c in counts)
                options.append({'name': str(key), 'sequences': counts})
                if len(counts) == expected:
                    active = counts
                    break
    unknown = []
    if active is None: unknown.append('active_logical_counts')
    if len(observed) < expected: unknown.append('unobserved_physical_ranks')
    if any(not 0 <= item['ep'] < expected for item in observed): unknown.append('observed_ep_membership_mismatch')
    result = {'source_case_dir': str(root), 'status_sha256': __import__('hashlib').sha256(payload).hexdigest(),
              'declared': {'dp': dp, 'tp': tp, 'ep': ep, 'nodes': list(declared.get('nodes') or ()),
                           'dp_local': declared.get('dp_local')},
              'expected_membership': expected, 'observed': observed,
              'selected_rank': selected, 'active_counts': active, 'source_conditions': options,
              'unknown': tuple(unknown), 'basis': 'source_status_membership + profiled_rank_folders'}
    if len(_SOURCE_GROUP_CACHE) >= 16: _SOURCE_GROUP_CACHE.clear()
    _SOURCE_GROUP_CACHE[cache_key] = result
    return result

