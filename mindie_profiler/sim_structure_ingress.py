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
from pathlib import Path
from typing import Any, Mapping, Sequence

from .events import ProfilerUsageError
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
    from mindie_sim.cohort_comparison import compare_cohorts

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
    try:
        from mindie_sim.observed_contracts.vocabulary import (
            build_unmodeled_onboarding_hint,
        )
    except ImportError:
        return []
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


def _case_hardware_peaks(
    case_doc: Mapping[str, Any] | None, *,
    replica: int | None = None, stage: int | None = None,
) -> dict[str, Any] | None:
    """Look up peak rates at the target placement, never always stage 0.

    A missing dimension (replica or pipeline stage) is scored only when every
    applicable placement exposes identical peaks; otherwise the efficiency
    value stays unavailable rather than borrowing another stage's hardware.
    """
    if case_doc is None:
        return None
    try:
        from mindie_sim.prediction.efficiency import extract_hardware_peaks
        from mindie_sim.prediction.structure import parse_case

        parallel = parse_case(case_doc).runtime.parallel
        total_replicas = max(1, int(parallel.dp or 1))
        total_stages = max(1, int(parallel.pp or 1))
        if replica is not None and (int(replica) < 0 or int(replica) >= total_replicas):
            return None
        if stage is not None and (int(stage) < 0 or int(stage) >= total_stages):
            return None
        replicas = [int(replica)] if replica is not None else list(range(total_replicas))
        stages = [int(stage)] if stage is not None else list(range(total_stages))
        payloads = [
            _peak_payload(extract_hardware_peaks(
                case_doc, stage=item_stage, replica=item_replica))
            for item_replica in replicas for item_stage in stages
        ]
        if not payloads:
            return None
        signature = json.dumps(payloads[0], sort_keys=True)
        if any(json.dumps(item, sort_keys=True) != signature
               for item in payloads[1:]):
            return None
        # Device records are not report data; only the declared SI rates are.
        return payloads[0]
    except TimeoutError:
        raise
    except Exception:
        # A case that cannot expose stage peaks leaves MBU/MFU unavailable
        # rather than substituting a baseline profile.
        return None


def _cohort_measurement(cohort: Mapping[str, Any]) -> tuple[float, int] | None:
    """Return a complete-event cohort's measurable (duration_ns, invocations)."""
    duration_ns = cohort.get("busy_union_ns")
    invocations = cohort.get("complete_event_count")
    if not (isinstance(duration_ns, (int, float)) and duration_ns > 0
            and type(invocations) is int and invocations > 0):
        return None
    if (cohort.get("clipped_event_count")
            and cohort.get("busy_union_basis") != "complete_events_only"):
        # Legacy mapping: a mixed clipped cohort has no complete-event union,
        # so scoring it would depress MFU/MBU.
        return None
    return float(duration_ns), invocations


def _declared_work_signature(declared: Mapping[str, Any]) -> str:
    """Hash declared work fields that drive efficiency math, not identity."""
    from mindie_sim.subgraph_math import SubgraphMathSummary

    fields = {
        key: value for key, value in declared.items()
        if key in SubgraphMathSummary.__dataclass_fields__ and key != "subgraph_id"
    }
    return json.dumps(fields, sort_keys=True)


def _evaluate_cohort(
    declared: Mapping[str, Any], cohort: Mapping[str, Any],
    peaks: Mapping[str, Any], window_index: int,
    *, candidates: Sequence[str] | None = None,
) -> dict[str, Any]:
    from mindie_sim.subgraph_math import (
        SubgraphMathSummary, evaluate_subgraph_efficiency,
    )

    duration_ns = cohort.get("busy_union_ns")
    invocations = cohort.get("complete_event_count")
    fields = {key: value for key, value in declared.items()
              if key in SubgraphMathSummary.__dataclass_fields__}
    metrics = evaluate_subgraph_efficiency(
        SubgraphMathSummary(**fields), duration_s=float(duration_ns) / 1000000000,
        hardware_peaks=peaks, observed_hbm_bytes=None, invocations=invocations)
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
    context: int | None = None, bindings: Any = None,
    correlations: Any = None, module_traces: Any = None,
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
            context=context, declared=declared)
        if not regenerate(graph_schema or SIM_GRAPH_SCHEMA):
            return
    elif isinstance(document, Mapping) and CASE_REQUIRED_KEYS <= set(document):
        case_doc = dict(document)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context)
        if not regenerate("mindie-sim.case/1"):
            return
    elif sim_case is not None and document is None:
        case_doc = _case_document(sim_case)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context)
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
