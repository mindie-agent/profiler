"""Bidirectional ``mindie-sim`` structure/Case ingress for ``analyze``.

[Role]
  Accept a ``mindie-model-structure/1`` mapping directly, or turn a five-key
  ``mindie-sim`` Case (and optionally a ``mindie-sim.graph/1`` summary) into a
  declared structure via ``mindie_sim.structure.export_structure`` before
  running ``StructureMapper``; then attach ``compare_cohorts``, a descriptive
  graph-summary comparison, and the shared ``mindie_sim.subgraph_math``
  efficiency evaluation. Also builds the single-owner onboarding hint for every
  unmapped captured operator.
[Invariants]
  * A Case requires only ``{"machine","model","runtime"}``; ``workload`` and
    ``slo`` are optional and validation is delegated to ``parse_case``.
  * Execution geometry is never invented from service requests: phase, tokens,
    sequences and context come from the supplied graph/mapping execution record
    or explicit caller flags, else a usage error names each missing flag.
  * ``draft_prepare`` is carried from the supplied graph/geometry through
    structure regeneration and cohort comparison so MTP prefill compares the
    same ``draft_prefill.*`` graph it measured.
  * A ``mindie-model-structure/1`` mapping always passes straight to
    ``StructureMapper`` with its own ``declared_execution`` preserved.
  * ``mindie-sim.graph/1`` without a Case (or without ``mindie_sim``) raises an
    exact copy-pasteable command; it never crashes in the mapper.
[Timeouts & Locks]
  One bounded (<= 50 MiB) JSON read per document; ``mindie_sim`` calls are pure
  in-memory metadata work with no device or NPU context.
[Side-Effect Policy]
  Read-only document access; the caller owns report writing.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from .events import ProfilerUsageError
from .hardware_presets import efficiency_tolerances, resolve_hardware_peaks
from .sim_draft_geometry import (
    CASE_REQUIRED_KEYS,
    MODEL_STRUCTURE_SCHEMA,
    SIM_GRAPH_SCHEMA,
    UNSUPPORTED_DRAFT_PREPARE_CODES,
    _DraftPrepareUnsupported,
    _export_structure,
    _graph_declared,
    _mapping_source_path,
    _unsupported_draft_report,
    resolve_case_geometry,
)

MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
#: Backwards-compatible public name; only the three core Case keys are required.
CASE_KEYS = CASE_REQUIRED_KEYS


def _load_document(value: Any, label: str) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    path = Path(str(value)).expanduser()
    try:
        if path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise ProfilerUsageError(f"{label} exceeds the 50 MiB metadata budget: {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    except ProfilerUsageError:
        raise
    except TimeoutError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProfilerUsageError(f"cannot read {label} {path}: {exc}") from exc


def _case_document(value: Any, label: str = "mindie-sim Case") -> dict[str, Any]:
    doc = _load_document(value, label)
    if not isinstance(doc, dict) or not CASE_REQUIRED_KEYS <= set(doc):
        raise ProfilerUsageError(
            f"expected mindie-sim Case with machine/model/runtime in {label}")
    return doc


def _measured_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    accounting = report.get("accounting")
    holder = accounting if isinstance(accounting, Mapping) else report
    step = holder.get("step_accounting") if isinstance(holder, Mapping) else None
    step = step if isinstance(step, Mapping) else {}
    return {
        "measured_step_ms": step.get("observed_event_span_ms_p50"),
        "measured_device_busy_union_ms": step.get("device_busy_union_ms_p50"),
        "measured_device_activity_sum_ms": step.get("device_activity_sum_ms_p50"),
        "measured_exposed_comm_ms": step.get("exposed_comm_ms_p50"),
        "measured_steps": list(step.get("steady_steps") or ()),
    }


def _graph_summary_comparison(
    graph: Mapping[str, Any], report: Mapping[str, Any],
) -> dict[str, Any]:
    bounds = graph.get("bounds") if isinstance(graph.get("bounds"), Mapping) else {}
    predicted = graph.get("duration_ms", graph.get("complete_ms"))
    bound = bounds.get("combined_ms") if isinstance(bounds, Mapping) else None
    measured = _measured_summary(report)
    measured_step = measured["measured_step_ms"]
    ratio = (
        float(predicted) / float(measured_step)
        if isinstance(predicted, (int, float)) and isinstance(measured_step, (int, float))
        and measured_step > 0 else None
    )
    return {
        "status": "compared" if predicted is not None else "unavailable",
        "schema": SIM_GRAPH_SCHEMA,
        "graph_predicted_ms": predicted,
        "graph_resource_bound_ms": bound,
        **measured,
        "predicted_over_measured": ratio,
        "basis": "declared graph total vs measured selected-step wall median; descriptive only",
        "claim_scope": "declared_model_structure_not_optimization_savings",
    }


def _compare_cohorts(
    case_doc: Mapping[str, Any], mapping: Mapping[str, Any], *,
    draft_prepare: bool = False,
) -> dict[str, Any]:
    try:
        from mindie_sim.cohort_accuracy import compare_cohorts
    except ImportError:
        return {
            "status": "unavailable",
            "reason": "mindie_sim_not_installed",
            "draft_prepare": bool(draft_prepare),
            "claim_scope": "standalone_profiler_without_sim",
        }

    payload = dict(mapping)
    if draft_prepare:
        execution = dict(payload.get("declared_execution") or {})
        execution["draft_prepare"] = True
        payload["declared_execution"] = execution
    try:
        return compare_cohorts(dict(case_doc), payload)
    except TimeoutError:
        raise
    except Exception as exc:
        raise ProfilerUsageError(f"sim cohort comparison failed: {exc}") from exc


#: ``native_tensor_contract`` tuple: family, operator type, inputs, outputs.
NATIVE_ABI_SLOT_COUNT = 2 + 2
#: Onboarding hints are deterministic and bounded per report.
MAX_ONBOARDING_HINTS = 2 ** (2 + 2) + 2 + 2


def _abi_summary(native_abi: Any) -> dict[str, Any] | None:
    """Describe captured ABI ranks/dtypes without claiming a declared contract."""
    if isinstance(native_abi, Mapping):
        shapes = native_abi.get("input_shapes"), native_abi.get("output_shapes")
        dtypes = native_abi.get("input_dtypes"), native_abi.get("output_dtypes")
    elif (isinstance(native_abi, (list, tuple))
          and len(native_abi) >= NATIVE_ABI_SLOT_COUNT):
        _family, _kind, input_slots, output_slots = native_abi[:NATIVE_ABI_SLOT_COUNT]
        shapes = ([slot[0] if isinstance(slot, (list, tuple)) else ()
                   for slot in input_slots],
                  [slot[0] if isinstance(slot, (list, tuple)) else ()
                   for slot in output_slots])
        dtypes = ([slot[1] if isinstance(slot, (list, tuple)) else None
                   for slot in input_slots],
                  [slot[1] if isinstance(slot, (list, tuple)) else None
                   for slot in output_slots])
    else:
        return None
    ranks = [[len(shape) for shape in group if isinstance(shape, (list, tuple))]
             for group in shapes]
    flat_dtypes = [dtype for group in dtypes for dtype in group if dtype]
    if not ranks[0] and not ranks[1]:
        return None
    return {
        "input_ranks": ranks[0],
        "output_ranks": ranks[1],
        "dtypes": sorted({str(dtype) for dtype in flat_dtypes}),
    }


def onboarding_hints_from_sample(
    sample: Sequence[Mapping[str, Any]], *, limit: int | None = None,
) -> list[dict[str, Any]]:
    """Build deterministic single-owner hints for unmapped captured operators."""
    from .observed_contracts.vocabulary import build_unmodeled_onboarding_hint
    hints: dict[tuple[str, str], dict[str, Any]] = {}
    cap = MAX_ONBOARDING_HINTS if limit is None else limit
    for row in sample or ():
        if row.get("status") == "bound":
            continue
        op_type = str(row.get("operator_type") or "")
        kernel = str(row.get("kernel_name") or "")
        key = (op_type, kernel)
        if key in hints or (not op_type and not kernel):
            continue
        hints[key] = build_unmodeled_onboarding_hint(
            observed_kernel_name=kernel or None,
            observed_op_type=op_type or None,
            observed_abi_summary=_abi_summary(row.get("native_abi")),
        )
        if len(hints) >= cap:
            break
    return [hints[key] for key in sorted(hints)]


def _cohorts_by_target(
    mapping: Mapping[str, Any],
) -> dict[str, list[tuple[int, Mapping[str, Any]]]]:
    """Preserve every window/cohort entry for a declared target.

    No ``setdefault`` truncation: a target observed in several independent
    windows keeps every cohort so the caller can evaluate each window rather
    than silently reporting only the first one.
    """
    index: dict[str, list[tuple[int, Mapping[str, Any]]]] = {}
    for window_index, window in enumerate(mapping.get("windows") or ()):
        if not isinstance(window, Mapping):
            continue
        for cohort in window.get("cohorts") or ():
            if not isinstance(cohort, Mapping):
                continue
            for target in cohort.get("target_ids") or ():
                index.setdefault(str(target), []).append((window_index, cohort))
    return index


def _peak_payload(peaks: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "compute_peaks": dict(peaks.get("compute_peaks") or {}),
        "vector_peak_ops_per_s": peaks.get("vector_peak_ops_per_s"),
        "hbm_peak_bytes_per_s": peaks.get("hbm_peak_bytes_per_s"),
    }


_DTYPE_FAMILY_ALIASES: Mapping[str, str] = {
    "fp8_e4m3": "fp8",
    "fp8_e5m2": "fp8",
    "fp4_e2m1": "fp4",
    "mxfp4": "fp4",
    "int8_w8a8": "int8",
}
_WORK_SIGNATURE_KEYS: tuple[str, ...] = (
    "subgraph_kind", "semantic_family", "phase", "layer_multiplicity",
    "parameterization", "algebraic_cube_flops", "algebraic_cube_flops_by_dtype",
    "algebraic_vector_ops", "minimal_boundary_hbm_bytes", "realized_hbm_bytes",
    "parallel_comm_bytes", "parallel_comm_by_domain", "boundary_breakdown_bytes",
    "fusion_hbm_overhead_bytes", "fusion_byte_efficiency", "unavailable_reasons",
)


_NON_COMPUTE_RATE_KEYS = frozenset({"hbm", "vector", "ub", "l2", "l1", "sram", "link"})


def _peaks_from_device(device: Mapping[str, Any]) -> dict[str, Any] | None:
    rates = device.get("rates") if isinstance(device.get("rates"), Mapping) else {}
    hbm = rates.get("hbm")
    if not (isinstance(hbm, (int, float)) and not isinstance(hbm, bool) and hbm > 0):
        return None
    raw_peaks = device.get("compute_peaks")
    if isinstance(raw_peaks, Mapping):
        compute_peaks = {
            str(k): float(v) for k, v in raw_peaks.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
        }
    else:
        compute_peaks = {
            str(k): float(v) for k, v in rates.items()
            if str(k) not in _NON_COMPUTE_RATE_KEYS
            and isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0
        }
    return {
        "compute_peaks": compute_peaks,
        "vector_peak_ops_per_s": float(rates.get("vector") or 0.0) or None,
        "hbm_peak_bytes_per_s": float(hbm),
    }


def _peaks_from_machine(machine: Mapping[str, Any]) -> dict[str, Any] | None:
    device = machine.get("device") if isinstance(machine.get("device"), Mapping) else None
    if isinstance(device, Mapping):
        peaks = _peaks_from_device(device)
        if peaks is not None:
            return peaks
    sku = machine.get("sku") or machine.get("hardware_key") or machine.get("name")
    if isinstance(sku, str) and sku.strip():
        try:
            return resolve_hardware_peaks(sku.strip())
        except ProfilerUsageError:
            return None
    return None


def _parallel_dims(case_doc: Mapping[str, Any]) -> tuple[int, int, int, int, int]:
    runtime = case_doc.get("runtime") if isinstance(case_doc.get("runtime"), Mapping) else {}
    parallel = runtime.get("parallel") if isinstance(runtime.get("parallel"), Mapping) else runtime
    def _pos(key: str) -> int:
        val = parallel.get(key)
        return int(val) if isinstance(val, int) and not isinstance(val, bool) and val > 0 else 1
    return _pos("tp"), _pos("cp"), _pos("pcp"), _pos("pp"), _pos("dp")


def _uniform_peaks(payloads: Sequence[dict[str, Any] | None]) -> dict[str, Any] | None:
    if not payloads or any(p is None for p in payloads):
        return None
    sig = json.dumps(payloads[0], sort_keys=True)
    return None if any(json.dumps(p, sort_keys=True) != sig for p in payloads[1:]) else payloads[0]


def _case_hardware_peaks(
    case_doc: Mapping[str, Any] | None, *,
    replica: int | None = None, stage: int | None = None,
) -> dict[str, Any] | None:
    """Resolve SI hardware peaks from a Case mapping or packaged presets."""
    if case_doc is None or not isinstance(case_doc, Mapping):
        return None
    machine = case_doc.get("machine")
    if not isinstance(machine, Mapping):
        return None
    tp, cp, pcp, pp, dp = _parallel_dims(case_doc)
    if replica is not None and (replica < 0 or replica >= dp):
        return None
    if stage is not None and (stage < 0 or stage >= pp):
        return None
    stages_cfg = machine.get("stages")
    if isinstance(stages_cfg, Sequence) and not isinstance(stages_cfg, (str, bytes)) and stages_cfg:
        indices = [int(stage)] if stage is not None else list(range(len(stages_cfg)))
        if any(idx < 0 or idx >= len(stages_cfg) for idx in indices):
            return None
        payloads = [
            _peaks_from_machine(stages_cfg[idx]) if isinstance(stages_cfg[idx], Mapping) else None
            for idx in indices
        ]
        return _uniform_peaks(payloads)
    devices_cfg = machine.get("devices") or machine.get("dies")
    if isinstance(devices_cfg, Sequence) and not isinstance(devices_cfg, (str, bytes)) and devices_cfg:
        stage_ranks = tp * cp * pcp
        replica_ranks = stage_ranks * pp
        reps = [int(replica)] if replica is not None else list(range(dp))
        stgs = [int(stage)] if stage is not None else list(range(pp))
        indices = [
            r * replica_ranks + s * stage_ranks + offset
            for r in reps for s in stgs for offset in range(stage_ranks)
        ]
        if any(idx < 0 or idx >= len(devices_cfg) for idx in indices):
            return None
        payloads = [
            _peaks_from_device(devices_cfg[idx]) if isinstance(devices_cfg[idx], Mapping) else None
            for idx in indices
        ]
        return _uniform_peaks(payloads)
    return _peaks_from_machine(machine)


def _cohort_measurement(cohort: Mapping[str, Any]) -> tuple[float, int] | None:
    """Return a complete-event cohort's measurable (duration_ns, invocations)."""
    duration_ns = cohort.get("busy_union_ns")
    invocations = cohort.get("complete_event_count")
    if not (isinstance(duration_ns, (int, float)) and duration_ns > 0
            and type(invocations) is int and invocations > 0):
        return None
    if (cohort.get("clipped_event_count")
            and cohort.get("busy_union_basis") != "complete_events_only"):
        return None
    return float(duration_ns), invocations


def _declared_work_signature(declared: Mapping[str, Any]) -> str:
    """Hash declared work fields that drive efficiency math, not identity."""
    fields = {key: value for key, value in declared.items() if key in _WORK_SIGNATURE_KEYS}
    return json.dumps(fields, sort_keys=True)


def _evaluate_efficiency_local(
    declared: Mapping[str, Any], *, duration_s: float,
    hardware_peaks: Mapping[str, Any], invocations: int,
) -> dict[str, Any]:
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration_s_must_be_positive_finite")
    if type(invocations) is not int or invocations <= 0:
        raise ValueError("complete_invocation_count_required")

    def total(value: Any) -> float | None:
        return None if value is None else float(value) * invocations

    def ratio(work: float | None, peak: Any) -> float | None:
        if work is None:
            return None
        if not math.isfinite(work) or work < 0:
            raise ValueError("invalid_work")
        if peak is None or not math.isfinite(float(peak)) or float(peak) <= 0:
            return None
        return work / (duration_s * float(peak))

    cube: float | None = None
    by_dtype = declared.get("algebraic_cube_flops_by_dtype")
    if isinstance(by_dtype, Mapping):
        peaks_by_dtype = hardware_peaks.get("compute_peaks") or {}
        cube_flops = declared.get("algebraic_cube_flops")
        if not by_dtype:
            if cube_flops == 0.0:
                cube = 0.0
        else:
            by_dtype_sum = sum(float(work) for work in by_dtype.values())
            rel_tol, abs_tol = efficiency_tolerances()
            if by_dtype_sum > 0.0 and (
                cube_flops is None
                or math.isclose(
                    by_dtype_sum, float(cube_flops),
                    rel_tol=rel_tol, abs_tol=abs_tol,
                )
            ):
                terms = [
                    ratio(
                        total(work),
                        peaks_by_dtype.get(str(dt))
                        or peaks_by_dtype.get(_DTYPE_FAMILY_ALIASES.get(str(dt), "")),
                    )
                    for dt, work in by_dtype.items()
                ]
                if terms and all(term is not None for term in terms):
                    cube = sum(t for t in terms if t is not None)

    boundary = total(declared.get("minimal_boundary_hbm_bytes"))
    realized = total(declared.get("realized_hbm_bytes"))
    headroom = None if boundary is None or realized is None else realized - boundary
    return {
        "algebraic_cube_mfu": cube,
        "algebraic_vector_mfu": ratio(
            total(declared.get("algebraic_vector_ops")),
            hardware_peaks.get("vector_peak_ops_per_s"),
        ),
        "minimal_boundary_mbu": ratio(boundary, hardware_peaks.get("hbm_peak_bytes_per_s")),
        "realized_mbu": ratio(realized, hardware_peaks.get("hbm_peak_bytes_per_s")),
        "fusion_headroom_bytes": headroom,
        "byte_accounting_consistent": None if headroom is None else headroom >= 0,
    }


def _evaluate_cohort(
    declared: Mapping[str, Any], cohort: Mapping[str, Any],
    peaks: Mapping[str, Any], window_index: int,
    *, candidates: Sequence[str] | None = None,
) -> dict[str, Any]:
    duration_ns = cohort.get("busy_union_ns")
    invocations = cohort.get("complete_event_count")
    metrics = _evaluate_efficiency_local(
        declared,
        duration_s=float(duration_ns) / 1000000000,
        hardware_peaks=peaks,
        invocations=int(invocations),
    )
    record = {
        "window_index": window_index,
        "cohort_id": cohort.get("cohort_id"),
        "target_ids": list(cohort.get("target_ids") or ()),
        "duration_ns": float(duration_ns),
        "invocations": invocations,
        "metrics": metrics,
        "basis": "complete cohort busy_union_ns / 1e9 with invocation multiplicity",
    }
    if candidates is not None:
        record.update(
            candidates=[str(item) for item in candidates],
            occurrence_binding="candidate_cohort_only",
        )
    return record


def _cohort_complete_binding(cohort: Mapping[str, Any]) -> tuple[int, bool]:
    complete = cohort.get("complete_status_counts")
    if isinstance(complete, Mapping):
        bound = int(complete.get("bound", 0) or 0)
        unbound = sum(int(v or 0) for k, v in complete.items() if k != "bound")
        if bound or unbound:
            return (bound if not unbound else 0), bool(unbound)
        raw = cohort.get("status_counts")
        raw_unbound = isinstance(raw, Mapping) and any(
            int(v or 0) for k, v in raw.items() if k != "bound")
        return 0, bool(raw_unbound)
    status_counts = cohort.get("status_counts") or {}
    if not isinstance(status_counts, Mapping):
        return 0, False
    bound = int(status_counts.get("bound", 0) or 0)
    unbound = sum(int(v or 0) for k, v in status_counts.items() if k != "bound")
    return (bound if not unbound else 0), bool(unbound)


def _projected_hardware_peaks(
    structure: Mapping[str, Any], mapping: Mapping[str, Any],
    peaks_at: Any,
) -> dict[str, Any] | None:
    execution = structure.get("execution")
    if not isinstance(execution, Mapping):
        execution = mapping.get("declared_execution")
    projection = execution.get("replica_projection") if isinstance(execution, Mapping) else None
    selected = projection.get("selected") if isinstance(projection, Mapping) else None
    if (isinstance(selected, Sequence) and not isinstance(selected, (str, bytes))
            and selected):
        if any(not isinstance(r, int) or isinstance(r, bool) for r in selected):
            return None
        replicas = [int(r) for r in selected]
        if replicas:
            payloads = [peaks_at(rep, None) for rep in replicas]
            if any(item is None for item in payloads):
                return None
            sig = json.dumps(payloads[0], sort_keys=True)
            return None if any(json.dumps(p, sort_keys=True) != sig for p in payloads[1:]) else payloads[0]
    return peaks_at(None, None)


def subgraph_efficiency_summary(
    structure: Mapping[str, Any], mapping: Mapping[str, Any], *,
    case_doc: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate exported subgraph math with the shared ``mindie_sim`` function."""
    groups = [group for group in structure.get("subgraphs") or ()
              if isinstance(group, Mapping)]
    cohorts = _cohorts_by_target(mapping)
    peak_cache: dict[tuple[int | None, int | None], dict[str, Any] | None] = {}

    def peaks_at(rep: int | None, st: int | None) -> dict[str, Any] | None:
        key = (rep, st)
        if key not in peak_cache:
            peak_cache[key] = _case_hardware_peaks(
                case_doc, replica=rep, stage=st)
        return peak_cache[key]

    records: list[dict[str, Any]] = []
    evaluated = 0
    evaluations_total = 0
    group_index = {str(group.get("subgraph_id")): group for group in groups}
    cohort_evaluations: list[dict[str, Any]] = []
    homogeneous_targets: set[str] = set()
    scored_cohorts: set[tuple[int, int]] = set()
    for window_index, window in enumerate(mapping.get("windows") or ()):
        if not isinstance(window, Mapping):
            continue
        for cohort in window.get("cohorts") or ():
            if not isinstance(cohort, Mapping):
                continue
            targets = [str(item) for item in cohort.get("target_ids") or ()]
            if not targets:
                continue
            bound, explicit_unbound = _cohort_complete_binding(cohort)
            if bound or (len(targets) == 1 and not explicit_unbound):
                continue  # unambiguous occurrence attribution is per target
            marker = (window_index, id(cohort))
            if marker in scored_cohorts:
                continue
            scored_cohorts.add(marker)
            members = [group_index.get(target) for target in targets]
            if any(member is None for member in members):
                continue
            declared_rows = [member.get("math_summary") for member in members]
            if any(not isinstance(row, Mapping) for row in declared_rows):
                continue
            if len({_declared_work_signature(row)
                    for row in declared_rows}) != 1:
                continue  # declared work is not homogeneous
            if _cohort_measurement(cohort) is None:
                continue
            payloads: list[dict[str, Any] | None] = []
            for member in members:
                replica = cohort.get("replica")
                if replica is None:
                    replica = member.get("replica")
                stage = cohort.get("stage")
                if stage is None:
                    stage = member.get("stage")
                payloads.append(peaks_at(replica, stage))
            if any(payload is None for payload in payloads):
                continue
            signature = json.dumps(payloads[0], sort_keys=True)
            if any(json.dumps(payload, sort_keys=True) != signature
                   for payload in payloads[1:]):
                continue  # stage hardware peaks are not homogeneous
            # One physical program priced once per window; the candidate tuple
            # records the unbound occurrence alternatives without claiming one.
            cohort_evaluations.append(_evaluate_cohort(
                declared_rows[0], cohort, payloads[0], window_index,
                candidates=targets))
            homogeneous_targets.update(targets)
    for group in groups:
        declared = group.get("math_summary")
        entries = cohorts.get(str(group.get("subgraph_id"))) or []
        candidates = sorted({
            str(target) for _window, cohort in entries
            for target in cohort.get("target_ids") or ()})
        record: dict[str, Any] = {
            "subgraph_id": group.get("subgraph_id"),
            "role": group.get("role"),
            "semantic_family": (declared or {}).get("semantic_family")
            if isinstance(declared, Mapping) else None,
            "phase": group.get("phase"),
            "declared": declared,
            "candidates": candidates,
            "evaluations": [],
        }
        if not isinstance(declared, Mapping):
            records.append({**record, "status": "unavailable",
                            "reason": "structure_export_without_subgraph_math"})
            continue
        ambiguous = False
        evaluations: list[dict[str, Any]] = []
        for window_index, cohort in entries:
            targets = [str(item) for item in cohort.get("target_ids") or ()]
            bound, explicit_unbound = _cohort_complete_binding(cohort)
            if (len(targets) > 1 or explicit_unbound) and not bound:
                ambiguous = True
                continue
            if _cohort_measurement(cohort) is None:
                continue
            replica = cohort.get("replica")
            if replica is None:
                replica = group.get("replica")
            stage = cohort.get("stage")
            if stage is None:
                stage = group.get("stage")
            peaks = peaks_at(replica, stage)
            if peaks is None:
                continue
            evaluations.append(_evaluate_cohort(
                declared, cohort, peaks, window_index))
        record["evaluations"] = evaluations
        if evaluations:
            evaluated += 1
            evaluations_total += len(evaluations)
            record.update(status="evaluated", evaluated_count=len(evaluations))
            if len(evaluations) == 1:
                record.update({
                    key: evaluations[0][key] for key in (
                        "window_index", "cohort_id", "duration_ns",
                        "invocations", "metrics", "basis")
                })
            else:
                # Independent windows are preserved per window; no first-window
                # duration is promoted to the whole target.
                record.update(
                    duration_ns=None, metrics=None,
                    invocations=sum(item["invocations"] for item in evaluations),
                    basis="per-window complete cohort busy_union_ns; see evaluations")
        elif ambiguous:
            scored = str(group.get("subgraph_id")) in homogeneous_targets
            record.update(
                status="declared_only",
                reason=("occurrence_unbound_scored_once_at_cohort_level"
                        if scored else "ambiguous_candidate_set_unbound"))
        else:
            record.update(status="declared_only",
                          reason="measured_cohort_unavailable")
        records.append(record)
    evaluated_total = evaluated + len(cohort_evaluations)
    return {
        "schema": "mindie-profiler-subgraph-efficiency/1",
        "status": ("evaluated" if evaluated_total else
                   "structure_only" if groups else "unavailable"),
        "basis": "shared mindie_sim.subgraph_math.evaluate_subgraph_efficiency",
        "hardware_peaks": _projected_hardware_peaks(structure, mapping, peaks_at),
        "subgraph_count": len(records),
        "evaluated_count": evaluated_total,
        "evaluation_count": evaluations_total + len(cohort_evaluations),
        "cohort_evaluation_count": len(cohort_evaluations),
        "cohort_evaluations": cohort_evaluations,
        "records": records,
    }


def apply_structure_ingress(
    report: dict[str, Any], observations: Sequence[Any], *,
    structure: Any = None, sim_case: Any = None, phase: str | None = None,
    tokens: int | None = None, sequences: int | None = None,
    context: int | None = None, media_tokens_per_sequence: int | None = None,
    bindings: Any = None, correlations: Any = None, module_traces: Any = None,
    mapping_limit: int = 200, max_events: int = 100_000,
) -> None:
    """Map structure (native or sim-generated) and attach closed-loop cohorts."""
    if structure is None and sim_case is None:
        return
    document = _load_document(structure, "structure document") if structure is not None else None
    schema = document.get("schema_version") if isinstance(document, Mapping) else None
    graph_schema = document.get("schema") if isinstance(document, Mapping) else None
    case_doc: dict[str, Any] | None = None
    geometry: dict[str, Any] | None = None
    graph_document: dict[str, Any] | None = None
    mapping_document = document
    if schema == MODEL_STRUCTURE_SCHEMA:
        if sim_case is not None:
            case_doc = _case_document(sim_case)
    elif graph_schema == SIM_GRAPH_SCHEMA:
        graph_document = dict(document)  # type: ignore[arg-type]
        if sim_case is None:
            embedded = _mapping_source_path(graph_document)
            if embedded is not None and embedded.is_file():
                sim_case = embedded
    def regenerate(source_schema: str) -> bool:
        """Regenerate the declared graph, reporting unsupported draft geometry."""
        nonlocal mapping_document
        try:
            mapping_document = _export_structure(case_doc, geometry)  # type: ignore[arg-type]
        except _DraftPrepareUnsupported as exc:
            _unsupported_draft_report(
                report, source_schema, geometry, exc, graph_document)  # type: ignore[arg-type]
            return False
        return True

    if graph_document is not None:
        if sim_case is None:
            raise ProfilerUsageError(
                "received mindie-sim.graph/1 (cost summary without tensor-contract "
                "occurrences); pass --sim-case <case.json> alongside --structure, or "
                "export topology via: mindie-sim structure <case.json> --phase decode "
                "--tokens 1 --sequences 8 --context 4096 --output structure.json")
        case_doc = _case_document(sim_case)
        declared = _graph_declared(graph_document)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context, media_tokens_per_sequence=media_tokens_per_sequence,
            declared=declared)
        if not regenerate(graph_schema or SIM_GRAPH_SCHEMA):
            return
    elif isinstance(document, Mapping) and CASE_REQUIRED_KEYS <= set(document):
        case_doc = dict(document)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context, media_tokens_per_sequence=media_tokens_per_sequence)
        if not regenerate("mindie-sim.case/1"):
            return
    elif sim_case is not None and document is None:
        case_doc = _case_document(sim_case)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context, media_tokens_per_sequence=media_tokens_per_sequence)
        if not regenerate("mindie-sim.case/1"):
            return
    if mapping_document is None:
        raise ProfilerUsageError("a structure document or --sim-case is required")
    from .structure_mapping import map_structure

    mapping = map_structure(
        observations, mapping_document, bindings=bindings,
        correlations=correlations, mapping_limit=mapping_limit,
        module_traces=module_traces, max_events=max_events, phase=phase)
    report["structure_mapping"] = mapping
    declared_execution = mapping.get("declared_execution")
    draft_prepare = bool(
        (geometry and geometry.get("draft_prepare"))
        or (isinstance(declared_execution, Mapping)
            and declared_execution.get("draft_prepare")))
    report["structure_ingress"] = {
        "source_schema": schema or graph_schema or "mindie-sim.case/1",
        "generated_structure": bool(geometry is not None),
        "geometry": None if geometry is None else dict(geometry),
        "draft_prepare": draft_prepare,
        "declared_execution_preserved": mapping.get("declared_execution") is not None,
    }
    report["subgraph_efficiency_summary"] = subgraph_efficiency_summary(
        mapping_document, mapping, case_doc=case_doc)
    if case_doc is not None:
        # ``compare_cohorts`` regenerates draft-aware geometry from the declared
        # execution, so draft-prepare windows compare like target-only ones.
        report["sim_cohort_comparison"] = _compare_cohorts(
            case_doc, mapping, draft_prepare=draft_prepare)
    if graph_document is not None:
        report["sim_graph_summary_comparison"] = _graph_summary_comparison(
            graph_document, report)


__all__ = [
    "MODEL_STRUCTURE_SCHEMA", "SIM_GRAPH_SCHEMA", "apply_structure_ingress",
    "onboarding_hints_from_sample", "resolve_case_geometry",
    "subgraph_efficiency_summary",
]
