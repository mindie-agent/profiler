"""Bounded MCP receipts for op-formula evaluation and batch annotation.

[Role]
  Build the two protocol envelopes (``evaluate_op_formula`` and
  ``annotate_profile_formulas``) with a complete-envelope receipt whose
  ``token_estimate`` equals ``upper_bound_tokens(final)``.  Counts and stable
  diagnostic codes survive every size fallback.

[Invariants]
  * ``receipt.token_estimate`` is the fixed point of the complete envelope and
    ``within_budget`` is true only when it is <= 250 tokens.
  * Aggregate counts and deduplicated sorted codes are never dropped; per-row
    samples are optional and are removed first under pressure.
  * A caller-supplied path or raw display name is never echoed verbatim.

[Timeouts & Locks]
  Pure in-memory serialization/measurement; no I/O.

[Side-Effect Policy]
  No filesystem or global-state mutation.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from mindie_sim.op_formulas import (
    FormulaError, FormulaValidationError, canonical_name,
    evaluate_with_diagnostics, supported_operators,
)
from mindie_sim.op_formulas.primitives import (
    strict_bool, strict_finite_float, strict_int, strict_tol,
)

from .events import ProfilerError
from .op_formula_annotator import (
    MAX_MCP_ROWS, MCP_SCHEMA, _error_code, annotate_profile_formulas,
)
from .op_mcp_tool_specs import MCP_TOOL_SPECS
from .token_budget import (
    bounded_mcp_envelope, fit_receipt_envelope, upper_bound_tokens,
)

_EVAL_KEYS = frozenset(MCP_TOOL_SPECS[0]["inputSchema"]["properties"])
_ANNOTATE_KEYS = frozenset(MCP_TOOL_SPECS[1]["inputSchema"]["properties"])
_ALGO_TOPOLOGIES = frozenset({"ring", "hd", "tree", "halving_doubling", "halvingdoubling", "mesh", "auto"})
_TRANSPORT_TOPOLOGIES = frozenset({"ub", "hccs", "roce"})


def _parse_collective_defaults(args: Mapping[str, Any]) -> tuple[dict[str, Any], int | None]:
    extra: dict[str, Any] = {}
    topology = args.get("topology")
    if topology is not None:
        if not isinstance(topology, str) or not topology.strip():
            raise FormulaValidationError("invalid_topology")
        norm = topology.strip().lower().replace("-", "_")
        if norm in _ALGO_TOPOLOGIES:
            extra["algorithm"] = norm
        elif norm in _TRANSPORT_TOPOLOGIES:
            extra["transport"] = norm
        else:
            raise FormulaValidationError("invalid_topology")
    ranks_raw = args.get("ranks")
    ranks = strict_int(ranks_raw, "ranks", minimum=1) if ranks_raw is not None else None
    return extra, ranks


def _sample_row(item: Mapping[str, Any]) -> dict[str, Any]:
    canonical = item.get("canonical_op")
    if canonical not in set(supported_operators()):
        canonical = None
    sample = {
        "canonical_op": canonical,
        "status": item.get("status"),
        "t_floor_us": (None if item.get("t_floor_us") is None
                       else round(float(item["t_floor_us"]), 3)),
        "measured_us": item.get("measured_us"),
    }
    if item.get("code"):
        sample["code"] = _error_code(Exception(str(item["code"])))
    return sample


def _priority(records: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    def key(item: Mapping[str, Any]) -> tuple[int, float]:
        measured = item.get("measured_us")
        floor = item.get("t_floor_us")
        ratio = (float(measured) / float(floor)
                 if measured and floor else float("inf"))
        return (0 if item.get("bound_violation_warning") else 1, ratio)
    return sorted(records, key=key)


def _request_error(error_code: str) -> dict[str, Any]:
    return {"schema": MCP_SCHEMA, "status": "invalid_request",
            "error_code": _error_code(Exception(error_code))}


def _evaluate_receipt(args: Mapping[str, Any]) -> dict[str, Any]:
    if set(args) - _EVAL_KEYS:
        return _request_error("unexpected_argument")
    operator = args.get("operator")
    if not isinstance(operator, str) or not operator.strip():
        return _request_error("operator_required")
    params = args.get("params")
    if params is None:
        params = {}
    if not isinstance(params, Mapping):
        return _request_error("params_not_an_object")
    raw_measured = args.get("measured_us")
    raw_observed = args.get("observed_us")
    measured: float | None = None
    try:
        m_val = (strict_finite_float(raw_measured, "measured_us", minimum=0.0)
                 if raw_measured is not None else None)
        o_val = (strict_finite_float(raw_observed, "observed_us", minimum=0.0)
                 if raw_observed is not None else None)
    except FormulaValidationError:
        return _request_error("measured_us_invalid")
    if m_val is not None and o_val is not None and m_val != o_val:
        return _request_error("conflicting_measured_us")
    measured = m_val if m_val is not None else o_val
    try:
        tol = strict_tol(args.get("tol", 0.02))
        warm = strict_bool(args.get("steady_l2_warm", False), "steady_l2_warm")
        mode = str(args.get("launch_mode") or "eager")
        coll_extra, ranks = _parse_collective_defaults(args)
    except FormulaValidationError:
        return _request_error("invalid_request")
    merged_params = dict(params)
    for k, v in coll_extra.items():
        merged_params.setdefault(k, v)
    if ranks is not None:
        merged_params.setdefault("world_size", ranks)
        merged_params.setdefault("ep", ranks)
    try:
        evaluation, diagnostic = evaluate_with_diagnostics(
            operator, merged_params,
            sku=str(args.get("sku") or "Ascend950DT_9581"),
            launch_mode=mode,
            steady_l2_warm=warm,
            measured_us=measured, tol=tol)
    except FormulaValidationError as exc:
        return {"schema": MCP_SCHEMA, "status": "invalid_abi",
                "error_code": _error_code(exc)}
    except FormulaError as exc:
        canonical = canonical_name(operator)
        payload = {"schema": MCP_SCHEMA,
                   "status": "unmodeled",
                   "error_code": _error_code(exc, "unsupported_operator")}
        if canonical in set(supported_operators()):
            payload["canonical_op"] = canonical
        return payload
    except (ValueError, TypeError, OverflowError):
        return _request_error("invalid_request")
    canonical = canonical_name(operator)
    payload = {
        "schema": MCP_SCHEMA,
        "status": diagnostic.get("status", "clean"),
        "t_floor_us": round(evaluation.t_floor_us, 4),
        "t_ref_us": round(evaluation.t_ref_us, 4),
        "bottleneck_pipe": evaluation.bottleneck_pipe,
        "alg_flops": card_value(evaluation.formula_card.alg_flops),
        "cube_flops_tiled": card_value(evaluation.formula_card.cube_flops_tiled),
        "compulsory_gm_bytes": evaluation.formula_card.compulsory_gm_bytes,
        "granule_gm_bytes": evaluation.formula_card.granule_gm_bytes,
        "alg_flops_expr": evaluation.formula_card.alg_flops_expr,
        "measured_us": diagnostic.get("measured_us"),
        "sol_floor_pct": (None if diagnostic.get("sol_floor_pct") is None
                          else round(float(diagnostic["sol_floor_pct"]), 3)),
        "ref_ratio": (None if diagnostic.get("ref_ratio") is None
                      else round(float(diagnostic["ref_ratio"]), 3)),
        "bound_violation_warning": bool(diagnostic.get("bound_violation_warning")),
        "root_cause_candidates": list(diagnostic.get("root_cause_candidates") or []),
    }
    if canonical in set(supported_operators()):
        payload["canonical_op"] = canonical
    return payload


def card_value(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _annotate_receipt(args: Mapping[str, Any]) -> dict[str, Any]:
    if set(args) - _ANNOTATE_KEYS:
        return _request_error("unexpected_argument")
    rows = args.get("rows")
    if not isinstance(rows, list) or not rows:
        return _request_error("rows_required")
    if len(rows) > MAX_MCP_ROWS:
        return _request_error("rows_exceed_limit")
    bad = [index for index, row in enumerate(rows) if not isinstance(row, Mapping)]
    if bad:
        return _request_error("row_not_an_object")
    try:
        tol = strict_tol(args.get("tol", 0.02))
        warm = strict_bool(args.get("steady_l2_warm", True), "steady_l2_warm")
        coll_extra, ranks = _parse_collective_defaults(args)
        eff_rows: Sequence[Mapping[str, Any]] = rows
        if coll_extra or ranks is not None:
            adapted: list[dict[str, Any]] = []
            for row in rows:
                item = dict(row)
                for k, v in coll_extra.items():
                    item.setdefault(k, v)
                if ranks is not None:
                    item.setdefault("world_size", ranks)
                    item.setdefault("ep", ranks)
                if isinstance(item.get("params"), Mapping):
                    p_copy = dict(item["params"])
                    for k, v in coll_extra.items():
                        p_copy.setdefault(k, v)
                    if ranks is not None:
                        p_copy.setdefault("world_size", ranks)
                        p_copy.setdefault("ep", ranks)
                    item["params"] = p_copy
                adapted.append(item)
            eff_rows = adapted
        report = annotate_profile_formulas(
            eff_rows, sku=str(args.get("sku") or "Ascend950DT_9581"),
            launch_mode=str(args.get("launch_mode") or "aclgraph"),
            steady_l2_warm=warm, tol=tol)
    except FormulaValidationError as exc:
        return {"schema": MCP_SCHEMA, "status": "invalid_request",
                "error_code": _error_code(exc)}
    except (ProfilerError, ValueError, TypeError, OverflowError):
        return _request_error("invalid_request")
    prioritized = _priority(report["rows"])
    samples = [_sample_row(item) for item in prioritized]
    core = {
        "schema": MCP_SCHEMA,
        "status": report["status"],
        "total_rows": report["total_rows"],
        "modeled_rows": report["modeled_rows"],
        "unmodeled_rows": report["unmodeled_rows"],
        "invalid_rows": report["invalid_rows"],
        "violation_count": report["violation_count"],
        "worst_ratio": report["worst_ratio"],
        "root_cause_codes": report["root_cause_codes"],
        "error_codes": report["error_codes"],
    }
    return bounded_mcp_envelope(core, samples, total_rows=report["total_rows"],
                                limit=250)


def call_mcp_tool(name: str, arguments: Any = None) -> dict[str, Any]:
    """Dispatch one bounded MCP receipt (upper-bound <= 250 tokens)."""
    try:
        args = dict(arguments) if isinstance(arguments, Mapping) else {}
    except (TypeError, ValueError):
        payload = _request_error("arguments_not_an_object")
    else:
        try:
            if name == "evaluate_op_formula":
                payload = _evaluate_receipt(args)
            elif name == "annotate_profile_formulas":
                payload = _annotate_receipt(args)
            else:
                payload = _request_error("unknown_tool")
        except (FormulaError, ProfilerError, ValueError, TypeError,
                OverflowError, KeyError) as exc:
            payload = _request_error(_error_code(exc))
    receipt = payload.get("receipt")
    valid = (isinstance(receipt, dict)
             and receipt.get("within_budget") is True
             and receipt.get("token_estimate") == upper_bound_tokens(payload))
    if valid:
        return payload
    return fit_receipt_envelope(
        payload,
        optional=("alg_flops_expr", "cube_flops_tiled", "granule_gm_bytes",
                  "compulsory_gm_bytes", "alg_flops",
                  "root_cause_candidates", "bound_violation_warning"),
        limit=250)
