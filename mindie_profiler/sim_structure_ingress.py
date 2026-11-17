"""Bidirectional ``mindie-sim`` structure/Case ingress for ``analyze``.

[Role]
  Accept a ``mindie-model-structure/1`` mapping directly, or turn a five-key
  ``mindie-sim`` Case (and optionally a ``mindie-sim.graph/1`` summary) into a
  declared structure via ``mindie_sim.structure.export_structure`` before
  running ``StructureMapper``; then attach ``compare_cohorts`` and a descriptive
  graph-summary comparison.
[Invariants]
  * A Case is exactly ``{"machine","model","workload","runtime","slo"}``;
    top-level ``hardware``/``parallel`` are rejected by ``parse_case``.
  * Execution geometry is never invented from service requests: phase, tokens,
    sequences and context come from the supplied graph/mapping execution record
    or explicit caller flags, else a usage error names each missing flag.
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

MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
MODEL_STRUCTURE_SCHEMA = "mindie-model-structure/1"
SIM_GRAPH_SCHEMA = "mindie-sim.graph/1"
CASE_KEYS = frozenset({"machine", "model", "workload", "runtime", "slo"})


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
    if not isinstance(doc, dict) or not CASE_KEYS <= set(doc):
        raise ProfilerUsageError(
            f"expected mindie-sim Case with machine/model/workload/runtime/slo in {label}")
    return doc


def resolve_case_geometry(
    doc: Any, *, phase: str | None = None, tokens: int | None = None,
    sequences: int | None = None, context: int | None = None,
    declared: Mapping[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Validate a five-key Case and resolve explicit/declared execution geometry."""
    from mindie_sim.prediction.structure import parse_case

    if not isinstance(doc, dict) or not {"machine", "model", "workload"} <= doc.keys():
        raise ProfilerUsageError("expected mindie-sim Case with machine/model/workload")
    case = parse_case(doc)
    declared = dict(declared or {})
    values = {
        "phase": phase,
        "tokens": tokens,
        "sequences": sequences,
        "context": context,
    }
    values = {
        key: value if value is not None else declared.get(key)
        for key, value in values.items()
    }
    missing = [key for key, value in values.items() if value is None]
    if missing:
        raise ProfilerUsageError(
            "structure execution geometry is missing: "
            + ", ".join("--" + key for key in missing)
        )
    values["phase"] = str(values["phase"]).strip().lower()
    if values["phase"] not in {"prefill", "decode"}:
        raise ProfilerUsageError("--phase must be prefill or decode")
    for key in ("tokens", "sequences", "context"):
        minimum = 0 if key == "context" else 1
        if type(values[key]) is not int or values[key] < minimum:
            raise ProfilerUsageError(f"invalid --{key}")
    return case, {**values, "scope": declared.get("scope", "model")}


def _mapping_source_path(graph: Mapping[str, Any]) -> Path | None:
    source = graph.get("source")
    if isinstance(source, Mapping) and isinstance(source.get("path"), str):
        return Path(source["path"]).expanduser()
    return None


def _graph_declared(graph: Mapping[str, Any]) -> dict[str, Any]:
    declared = {
        "tokens": graph.get("tokens_per_sequence"),
        "sequences": graph.get("sequences_per_replica"),
        "scope": graph.get("graph_scope") or "model",
    }
    execution = graph.get("execution")
    if isinstance(execution, Mapping):
        for key in ("phase", "tokens", "sequences", "context", "scope"):
            if execution.get(key) is not None:
                declared[key] = execution[key]
    return declared


def _export_structure(
    case_doc: Mapping[str, Any], geometry: Mapping[str, Any],
) -> dict[str, Any]:
    from mindie_sim.structure import export_structure

    return export_structure(
        case_doc,
        phase=str(geometry["phase"]),
        tokens=int(geometry["tokens"]),
        context=int(geometry["context"]),
        sequences=int(geometry["sequences"]),
        scope=str(geometry.get("scope") or "model"),
        source={"kind": "mindie_profiler_case_ingress", "schema": MODEL_STRUCTURE_SCHEMA},
    )


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


def _compare_cohorts(case_doc: Mapping[str, Any], mapping: Mapping[str, Any]) -> dict[str, Any]:
    from mindie_sim.cohort_comparison import compare_cohorts

    try:
        return compare_cohorts(dict(case_doc), dict(mapping))
    except TimeoutError:
        raise
    except Exception as exc:
        raise ProfilerUsageError(f"sim cohort comparison failed: {exc}") from exc


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
        mapping_document = _export_structure(case_doc, geometry)
    elif isinstance(document, Mapping) and CASE_KEYS <= set(document):
        case_doc = dict(document)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context)
        mapping_document = _export_structure(case_doc, geometry)
    elif sim_case is not None and document is None:
        case_doc = _case_document(sim_case)
        _case, geometry = resolve_case_geometry(
            case_doc, phase=phase, tokens=tokens, sequences=sequences,
            context=context)
        mapping_document = _export_structure(case_doc, geometry)
    if mapping_document is None:
        raise ProfilerUsageError("a structure document or --sim-case is required")
    from .structure_mapping import map_structure

    mapping = map_structure(
        observations, mapping_document, bindings=bindings,
        correlations=correlations, mapping_limit=mapping_limit,
        module_traces=module_traces, max_events=max_events, phase=phase)
    report["structure_mapping"] = mapping
    report["structure_ingress"] = {
        "source_schema": schema or graph_schema or "mindie-sim.case/1",
        "generated_structure": bool(geometry is not None),
        "geometry": None if geometry is None else dict(geometry),
        "declared_execution_preserved": mapping.get("declared_execution") is not None,
    }
    if case_doc is not None:
        report["sim_cohort_comparison"] = _compare_cohorts(case_doc, mapping)
    if graph_document is not None:
        report["sim_graph_summary_comparison"] = _graph_summary_comparison(
            graph_document, report)


__all__ = [
    "MODEL_STRUCTURE_SCHEMA", "SIM_GRAPH_SCHEMA", "apply_structure_ingress",
    "resolve_case_geometry",
]
