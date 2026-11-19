"""Case geometry resolution and draft-prepare regeneration for ``sim_structure_ingress``.

[Role]
  Validate ``mindie-sim`` Case execution geometry, propagate ``draft_prepare``
  through ``mindie_sim.structure.export_structure``, and produce explicit
  ``unsupported_geometry`` records only for genuine missing-draft declarations
  or legacy ``mindie-sim`` installations.

[Invariants]
  * Phase, tokens, sequences and context come from the supplied graph/mapping
    declaration or explicit caller flags; they are never guessed from requests.
  * Narrow ``UNSUPPORTED_DRAFT_PREPARE_CODES`` match only missing draft-mode or
    scope/legacy-API conditions, never masking modeling bugs inside draft ops.

[Timeouts & Locks]
  In-memory validation and one pure ``mindie_sim`` structure export; no locks.

[Side-Effect Policy]
  Pure dictionary construction; mutates only the caller-supplied ``report``
  mapping inside ``_unsupported_draft_report``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .events import ProfilerUsageError

MODEL_STRUCTURE_SCHEMA = "mindie-model-structure/1"
SIM_GRAPH_SCHEMA = "mindie-sim.graph/1"
CASE_REQUIRED_KEYS = frozenset({"machine", "model", "runtime"})

UNSUPPORTED_DRAFT_PREPARE_CODES: tuple[str, ...] = (
    "draft_preparation_requires_prefill_model_scope",
    "draft_preparation_requires_declared_runtime_draft_mode",
    "catalog_draft_missing",
    "catalog_draft_mode_unavailable",
    "catalog_draft_mode_missing",
    "structure_phase_mismatch",
    "structure_draft_prepare_requires_prefill",
)


class _DraftPrepareUnsupported(ProfilerUsageError):
    """``draft_prepare`` geometry cannot be regenerated for this Case/sim."""


def resolve_case_geometry(
    doc: Any,
    *,
    phase: str | None = None,
    tokens: int | None = None,
    sequences: int | None = None,
    context: int | None = None,
    declared: Mapping[str, Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Validate a Case and resolve explicit/declared execution geometry."""
    from mindie_sim.prediction.structure import parse_case

    if not isinstance(doc, dict) or not CASE_REQUIRED_KEYS <= doc.keys():
        raise ProfilerUsageError("expected mindie-sim Case with machine/model/runtime")
    case = parse_case(doc)
    declared_map = dict(declared or {})
    values = {
        "phase": phase,
        "tokens": tokens,
        "sequences": sequences,
        "context": context,
    }
    values = {
        key: value if value is not None else declared_map.get(key)
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
    draft_prepare = declared_map.get("draft_prepare", False)
    if not isinstance(draft_prepare, bool):
        raise ProfilerUsageError("draft_prepare must be a boolean")
    return case, {
        **values,
        "scope": declared_map.get("scope", "model"),
        "draft_prepare": draft_prepare,
    }


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
    if isinstance(graph.get("draft_prepare"), bool):
        declared["draft_prepare"] = graph["draft_prepare"]
    execution = graph.get("execution")
    if isinstance(execution, Mapping):
        for key in ("phase", "tokens", "sequences", "context", "scope", "draft_prepare"):
            if execution.get(key) is not None:
                declared[key] = execution[key]
    return declared


def _export_structure(
    case_doc: Mapping[str, Any], geometry: Mapping[str, Any],
) -> dict[str, Any]:
    from mindie_sim.structure import export_structure

    kwargs = dict(
        phase=str(geometry["phase"]),
        tokens=int(geometry["tokens"]),
        context=int(geometry["context"]),
        sequences=int(geometry["sequences"]),
        scope=str(geometry.get("scope") or "model"),
        source={"kind": "mindie_profiler_case_ingress", "schema": MODEL_STRUCTURE_SCHEMA},
    )
    if geometry.get("draft_prepare"):
        try:
            return export_structure(case_doc, draft_prepare=True, **kwargs)
        except TypeError as exc:
            if "draft_prepare" not in str(exc):
                raise
            raise _DraftPrepareUnsupported(
                "installed mindie-sim cannot regenerate draft_prepare structure; "
                "supply a draft-aware mindie-model-structure/1 document"
            ) from exc
        except ValueError as exc:
            message = str(exc)
            if not any(code in message for code in UNSUPPORTED_DRAFT_PREPARE_CODES):
                raise
            raise _DraftPrepareUnsupported(
                f"installed mindie-sim cannot export draft_prepare geometry: {exc}"
            ) from exc
    return export_structure(case_doc, **kwargs)


def _unsupported_draft_report(
    report: dict[str, Any],
    schema: str,
    geometry: Mapping[str, Any],
    exc: ProfilerUsageError,
    graph: Mapping[str, Any] | None = None,
) -> None:
    """Record that draft-aware regeneration cannot be honoured honestly."""
    reason = str(exc)
    report["structure_ingress"] = {
        "source_schema": schema,
        "generated_structure": False,
        "geometry": dict(geometry),
        "draft_prepare": True,
        "declared_execution_preserved": False,
        "status": "unsupported_geometry",
        "reason": reason,
    }
    report["subgraph_efficiency_summary"] = {
        "schema": "mindie-profiler-subgraph-efficiency/1",
        "status": "unsupported_geometry",
        "reason": reason,
        "subgraph_count": 0,
        "evaluated_count": 0,
        "evaluation_count": 0,
        "cohort_evaluations": [],
        "records": [],
    }
    report["sim_cohort_comparison"] = {
        "status": "unsupported_geometry",
        "reason": reason,
        "draft_prepare": True,
        "claim_scope": "no_structure_comparison",
    }
    if graph is not None:
        report["sim_graph_summary_comparison"] = {
            "schema": SIM_GRAPH_SCHEMA,
            "status": "unsupported_geometry",
            "reason": reason,
            "graph_predicted_ms": graph.get("duration_ms", graph.get("complete_ms")),
            "claim_scope": "no_structure_comparison",
        }


__all__ = [
    "CASE_REQUIRED_KEYS",
    "MODEL_STRUCTURE_SCHEMA",
    "SIM_GRAPH_SCHEMA",
    "UNSUPPORTED_DRAFT_PREPARE_CODES",
    "_DraftPrepareUnsupported",
    "_export_structure",
    "_graph_declared",
    "_mapping_source_path",
    "_unsupported_draft_report",
    "resolve_case_geometry",
]
