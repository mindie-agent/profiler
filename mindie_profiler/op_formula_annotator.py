"""Profiler-row formula annotation, lossless diagnostics, CLI and lean MCP tools.

[Role]
  Bind a parsed ``kernel_details`` row (or an explicit formula request) to the
  ``mindie_sim.op_formulas`` engine through the ABI bridge, then report the
  certified floor, structural reference, SoL floor percentage and an explicit
  diagnostic status.  Aggregate every supplied row before choosing examples, and
  expose the same computation through a CLI subcommand plus two bounded MCP tools.

[Invariants]
  * A row is never annotated with invented shapes: unknown ABI and unsupported
    operators stay ``status="unmodeled"`` / ``"invalid_abi"`` with a stable code.
  * ``measured_us`` is reported as observed; a sub-floor measurement sets
    ``bound_violation_warning=True`` and lists root-cause candidates, never a
    silent clamp.
  * Aggregation covers 100% of supplied rows before sampling; ``status`` is
    ``violations_detected`` whenever ``violation_count > 0``.
  * Protocol identifiers (schema/status/family/canonical_op/root causes) are
    never truncated; raw display names are normalized before sampling.
  * MCP receipts are bounded by ``upper_bound_tokens`` (complete envelope,
    receipt included) to at most 250 tokens.
  * The annotator is read-only with respect to profiler sources.

[Timeouts & Locks]
  Pure arithmetic plus explicit-path, size-bounded CSV/JSON reads.  No device,
  HCCL or subprocess work.

[Side-Effect Policy]
  Reads only caller-provided paths; writes only an explicit ``--output``.
  MCP calls perform no filesystem writes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any, Mapping, Sequence

from mindie_sim.op_formulas import (
    FormulaError, FormulaValidationError, canonical_name, evaluate_with_diagnostics,
    supported_operators,
)
from mindie_sim.op_formulas.primitives import (
    strict_bool, strict_finite_float, strict_tol,
)

from .events import ProfilerError, ProfilerUsageError
from .op_abi_bridge import AbiError, infer_request

ANNOTATION_SCHEMA = "mindie-profile-formula-annotations/1"
MCP_SCHEMA = "mindie-op-formula-mcp/1"
MAX_ROWS = 100_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_MCP_ROWS = 20_000
_PROFILE_KEYS = ("rows", "ops", "kernels", "events", "records")
_ROOT_CAUSES = ("cross_op_l2_hit", "unfiltered_padding_shape_bound",
                "async_overlap_shadowed", "wrong_sku_spec")


def _strip(value: Any) -> str:
    return str(value).strip().strip('"').strip("'")


def _row_mapping(row: Any) -> Mapping[str, Any]:
    if isinstance(row, Mapping):
        return row
    as_dict = getattr(row, "as_dict", None)
    if callable(as_dict):
        candidate = as_dict()
        if isinstance(candidate, Mapping):
            return candidate
    values = getattr(row, "__dict__", None)
    if isinstance(values, Mapping):
        return values
    raise TypeError("profiler row must be a mapping or expose as_dict()")


def _norm_row(row: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in _row_mapping(row).items():
        name = re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")
        out[name] = _strip(value) if isinstance(value, str) else value
    if "type" not in out and "op_type" in out:
        out["type"] = out["op_type"]
    return out


def display_name(raw: Any) -> tuple[str, str]:
    """Return ``(safe_canonical, safe_preview)`` without path text."""
    text = str(raw or "unknown").strip()
    if "/" in text or "\\" in text:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        return "path_hidden", f"path_hidden#{digest}"
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]", "", text)
    if not cleaned:
        return "unknown", "unknown"
    if len(cleaned) <= 24:
        return cleaned, cleaned
    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:8]
    return cleaned, f"{cleaned[:11]}#{digest}"


def _safe_reason(exc: BaseException, limit: int = 120) -> str:
    """Stable printable-ASCII reason with path-like tokens removed."""
    text = re.sub(r"\S*[/\\]\S*", "<path>", str(exc))
    text = "".join(char if 32 <= ord(char) < 127 else "?" for char in text)
    return text[:limit]


def _error_code(exc: BaseException, fallback: str = "validation_error") -> str:
    code = getattr(exc, "code", None)
    text = str(code or fallback).strip().lower()
    text = re.sub(r"[^a-z0-9_]+", "_", text).strip("_")
    return text[:40] or fallback


def _measured_from_row(normalized: Mapping[str, Any]) -> float | None:
    for key in ("duration_us", "measured_us", "observed_us", "duration_(us)", "duration"):
        if normalized.get(key) in (None, ""):
            continue
        value = normalized[key]
        if isinstance(value, bool):
            raise FormulaValidationError("measured duration must be numeric, not bool")
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise FormulaValidationError(
                "measured duration is not a finite number") from exc
        return strict_finite_float(number, "measured_us", minimum=0.0)
    return None


def _row_flags(normalized: Mapping[str, Any]) -> dict[str, Any]:
    raw = normalized.get("flags")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            raw = None
    return dict(raw) if isinstance(raw, Mapping) else {}


def _invalid_record(code: str, reason: str, measured: float | None,
                    preview: str = "unknown", canonical: str | None = None,
                    status: str = "invalid_input") -> dict[str, Any]:
    return {"status": status, "operator": canonical or "unknown",
            "canonical_op": canonical, "raw_op_preview": preview,
            "code": code, "measured_us": measured,
            "reason": _safe_reason(Exception(reason))}


def annotate_row(row: Mapping[str, Any], *, sku: str = "Ascend950DT_9581",
                 launch_mode: str | None = None,
                 steady_l2_warm: bool | None = None,
                 tol: float = 0.02, measured_us: float | None = None,
                 include_card: bool = False) -> dict[str, Any]:
    """Annotate one profiled row; return a modeled, invalid or unmodeled record."""
    try:
        normalized = _norm_row(row)
    except TypeError:
        return _invalid_record("unmodeled_row", "row is not a mapping",
                               measured_us, status="unmodeled")
    if measured_us is None:
        try:
            measured = _measured_from_row(normalized)
        except FormulaValidationError:
            return _invalid_record("validation_error",
                                   "measured duration is invalid", None)
    else:
        try:
            measured = strict_finite_float(measured_us, "measured_us", minimum=0.0)
        except FormulaValidationError:
            return _invalid_record("validation_error",
                                   "measured duration is invalid", None)
    try:
        mode = launch_mode or str(normalized.get("launch_mode") or "aclgraph")
        if mode not in {"superkernel_subtask", "aclgraph", "eager",
                        "python_eager"}:
            return _invalid_record("invalid_launch_mode", "unknown launch mode",
                                   measured)
        if steady_l2_warm is None:
            if normalized.get("steady_l2_warm") in (None, ""):
                warm = True
            else:
                warm = strict_bool(normalized.get("steady_l2_warm"),
                                   "steady_l2_warm")
        else:
            warm = strict_bool(steady_l2_warm, "steady_l2_warm")
    except FormulaValidationError:
        return _invalid_record("validation_error", "invalid boolean flag",
                               measured)
    raw_operator = str(normalized.get("type") or normalized.get("name")
                       or normalized.get("operator") or "unknown")
    _, preview = display_name(normalized.get("operator") or normalized.get("name")
                              or raw_operator)
    canonical_raw = canonical_name(str(normalized.get("operator")
                                       or normalized.get("name") or raw_operator))
    canonical_label = (canonical_raw
                       if canonical_raw in set(supported_operators())
                       else None)
    try:
        operator, params, flags = infer_request(normalized)
        flags = {**_row_flags(normalized), **dict(flags or {})}
        evaluation, diagnostic = evaluate_with_diagnostics(
            operator, params, sku=sku, launch_mode=mode,
            steady_l2_warm=warm, measured_us=measured, tol=tol, flags=flags)
    except AbiError as exc:
        status = ("unmodeled" if exc.code in {
            "unclassified_kernel", "unsupported_formula_family",
            "missing_input_shapes"} else "invalid_abi")
        return _invalid_record(_error_code(exc, "invalid_abi"),
                               exc.detail or exc.code, measured, preview,
                               canonical_label, status)
    except FormulaValidationError as exc:
        return _invalid_record(_error_code(exc, "validation_error"),
                               str(exc), measured, preview, canonical_label,
                               "invalid_abi")
    except (FormulaError, ValueError, TypeError, OverflowError) as exc:
        return _invalid_record(_error_code(exc, "formula_error"),
                               str(exc), measured, preview, canonical_label,
                               "unmodeled")
    record = _metric_row(evaluation, diagnostic, include_card)
    record["status"] = diagnostic.get("status", "clean")
    record["canonical_op"] = canonical_name(operator) or operator
    record["raw_op_preview"] = preview
    return record


def _metric_row(evaluation: Any, diagnostic: Mapping[str, Any],
                include_card: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "operator": evaluation.operator,
        "family": evaluation.family,
        "variant": evaluation.variant,
        "sku": evaluation.sku,
        "launch_mode": evaluation.launch_mode,
        "t_floor_us": round(evaluation.t_floor_us, 6),
        "t_ref_us": round(evaluation.t_ref_us, 6),
        "measured_us": diagnostic.get("measured_us"),
        "sol_floor_pct": (None if diagnostic.get("sol_floor_pct") is None
                          else round(float(diagnostic["sol_floor_pct"]), 4)),
        "ref_ratio": (None if diagnostic.get("ref_ratio") is None
                      else round(float(diagnostic["ref_ratio"]), 4)),
        "bottleneck_pipe": evaluation.bottleneck_pipe,
        "structural_gap_us": (None if diagnostic.get("structural_gap_us") is None
                              else round(float(diagnostic["structural_gap_us"]), 6)),
        "impl_headroom_us": (None if diagnostic.get("impl_headroom_us") is None
                             else round(float(diagnostic["impl_headroom_us"]), 6)),
        "bound_violation_warning": bool(diagnostic.get("bound_violation_warning")),
        "root_cause_candidates": list(diagnostic.get("root_cause_candidates") or []),
    }
    if include_card:
        payload["formula_card"] = evaluation.formula_card.as_dict()
        payload["derating"] = evaluation.derating.as_dict()
        payload["latency"] = evaluation.latency.as_dict()
    return payload


def annotate_profile_formulas(rows: Sequence[Mapping[str, Any]], *,
                              sku: str = "Ascend950DT_9581",
                              launch_mode: str = "aclgraph",
                              steady_l2_warm: bool = True,
                              tol: float = 0.02,
                              include_card: bool = False) -> dict[str, Any]:
    """Annotate and aggregate every row before any example is selected."""
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise FormulaValidationError("rows must be a sequence of mappings")
    warm = strict_bool(steady_l2_warm, "steady_l2_warm")
    tolerance = strict_tol(tol)
    if launch_mode not in {"superkernel_subtask", "aclgraph", "eager",
                           "python_eager"}:
        raise FormulaValidationError("unknown launch_mode")
    records = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            records.append({"status": "invalid_input", "operator": "unknown",
                            "canonical_op": None, "measured_us": None,
                            "code": "validation_error",
                            "reason": f"row {index} is not a mapping"})
            continue
        records.append(annotate_row(row, sku=sku, launch_mode=launch_mode,
                                    steady_l2_warm=warm, tol=tolerance,
                                    include_card=include_card))
    return aggregate_records(records)


def aggregate_records(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate a complete annotation list (no pre-slicing anywhere)."""
    total = len(records)
    invalid = [item for item in records
               if item.get("status") == "invalid_input"]
    invalid_abi = [item for item in records
                   if item.get("status") == "invalid_abi"]
    unmodeled = [item for item in records if item.get("status") == "unmodeled"]
    modeled = [item for item in records
               if item.get("status") not in {"unmodeled", "invalid_input",
                                             "invalid_abi"}]
    violations = [item for item in modeled if item.get("bound_violation_warning")]
    ratios = [float(item["ref_ratio"]) for item in modeled
              if item.get("ref_ratio") not in (None,)]
    sols = [float(item["sol_floor_pct"]) for item in modeled
            if item.get("sol_floor_pct") is not None]
    floors = []
    for item in modeled:
        measured = item.get("measured_us")
        floor = item.get("t_floor_us")
        if measured and floor:
            floors.append(float(measured) / float(floor))
    causes = sorted({str(code) for item in violations
                     for code in (item.get("root_cause_candidates") or [])})
    error_codes = set(causes)
    for item in invalid:
        error_codes.add(str(item.get("code") or "validation_error"))
    for item in invalid_abi:
        error_codes.add(str(item.get("code") or "invalid_abi"))
    for item in unmodeled:
        error_codes.add(str(item.get("code") or "unmodeled_op"))
    # Stable precedence: violations dominate mixed invalidity.
    if violations:
        status = "violations_detected"
    elif invalid or invalid_abi:
        status = "invalid_input"
    elif modeled == [] and unmodeled:
        status = "unmodeled"
    else:
        status = "clean"
    return {
        "schema": ANNOTATION_SCHEMA,
        "status": status,
        "count": total,
        "total_rows": total,
        "modeled": len(modeled),
        "modeled_rows": len(modeled),
        "unmodeled": len(unmodeled),
        "unmodeled_rows": len(unmodeled),
        "invalid": len(invalid) + len(invalid_abi),
        "invalid_rows": len(invalid) + len(invalid_abi),
        "violations": len(violations),
        "violation_count": len(violations),
        "worst_ratio": round(min(floors), 4) if floors else None,
        "max_sol_floor_pct": round(max(sols), 4) if sols else None,
        "median_ref_ratio": round(statistics.median(ratios), 4) if ratios else None,
        "root_cause_codes": causes,
        "error_codes": sorted(error_codes),
        "rows": list(records),
    }


def load_rows(path: str | Path) -> list[dict[str, Any]]:
    """Load a bounded kernel CSV or a strict JSON profile container."""
    source = Path(path)
    try:
        size = source.stat().st_size
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"cannot read rows: {exc}") from exc
    if size > MAX_FILE_BYTES:
        raise ProfilerUsageError(f"row file exceeds {MAX_FILE_BYTES} bytes")
    if source.suffix.lower() == ".csv":
        try:
            csv.field_size_limit(min(2**31 - 1, MAX_FILE_BYTES))
        except OverflowError:  # pragma: no cover - platform dependent
            csv.field_size_limit(131072)
        try:
            with source.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fieldnames = list(reader.fieldnames or [])
                if not fieldnames:
                    raise ProfilerUsageError("CSV has no header row")
                lowered = {name.strip().lower() for name in fieldnames
                           if name is not None}
                if not any(name in lowered for name in
                           ("name", "type", "op_type", "operator")):
                    raise ProfilerUsageError(
                        "CSV is missing an operator name column")
                if not any(name in lowered for name in
                           ("duration_us", "duration_(us)", "duration(us)",
                            "measured_us")):
                    raise ProfilerUsageError(
                        "CSV is missing a duration column")
                rows = []
                for raw in reader:
                    if None in raw:
                        raise ProfilerUsageError(
                            "CSV row has more fields than the header declares")
                    rows.append(dict(raw))
        except csv.Error as exc:
            raise ProfilerUsageError(f"invalid CSV: {exc}") from exc
    else:
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except TimeoutError:
            raise
        except (OSError, json.JSONDecodeError) as exc:
            raise ProfilerUsageError(f"invalid JSON rows: {exc}") from exc
        if isinstance(payload, Mapping):
            key = next((name for name in _PROFILE_KEYS if name in payload), None)
            if key is None:
                raise ProfilerUsageError(
                    f"JSON object must contain one of {list(_PROFILE_KEYS)}")
            payload = payload[key]
        if not isinstance(payload, list):
            raise ProfilerUsageError("JSON rows must be a list or a profile object")
        rows = []
        for index, item in enumerate(payload):
            if not isinstance(item, Mapping):
                raise ProfilerUsageError(
                    f"JSON row {index} is {type(item).__name__}, not an object")
            rows.append(dict(item))
    if len(rows) > MAX_ROWS:
        raise ProfilerUsageError(f"row file exceeds {MAX_ROWS} rows")
    return rows


def call_mcp_tool(name: str, arguments: Any = None) -> dict[str, Any]:
    """Dispatch one bounded MCP receipt (upper-bound <= 250 tokens)."""
    from .op_formula_mcp import call_mcp_tool as _call_mcp_tool

    return _call_mcp_tool(name, arguments)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler op-formula",
        description="Evaluate analytical Roofline floor/reference bounds for one operator or annotate captured kernel rows.",
    )
    parser.add_argument("--operator", default=None, help="canonical or Ascend operator name for single-op evaluation")
    parser.add_argument("--params", default="{}", help="inline JSON parameter object for --operator")
    parser.add_argument("--params-file", default=None, help="path to JSON parameter object file (<= 64 MiB)")
    parser.add_argument("--sku", default="Ascend950DT_9581", help="target Ascend hardware SKU identifier (default: Ascend950DT_9581)")
    parser.add_argument("--launch-mode", default="eager",
                        choices=("superkernel_subtask", "aclgraph", "eager",
                                 "python_eager"),
                        help="kernel dispatch regime used for launch-floor accounting (default: eager)")
    parser.add_argument("--steady-l2-warm", dest="steady_l2_warm",
                        action="store_true", default=True,
                        help="assume steady-state L2 residency where supported (default)")
    parser.add_argument("--cold", dest="steady_l2_warm", action="store_false",
                        help="disable L2 warm-residency credit and charge cold HBM traffic")
    parser.add_argument("--measured-us", type=float, default=None, help="optional observed kernel duration in us for bound-violation diagnosis")
    parser.add_argument("--rows", default=None, help="kernel CSV or JSON row list for batch profile annotation")
    parser.add_argument("--tol", type=float, default=0.02, help="relative tolerance below theoretical floor before flagging violation (default: 0.02)")
    parser.add_argument("--full", action="store_true", help="include full formula card")
    parser.add_argument("--output", default=None, help="write JSON evaluation or annotation output to path")
    args = parser.parse_args(argv)
    try:
        tol = strict_tol(args.tol)
        measured = (None if args.measured_us is None else
                    strict_finite_float(args.measured_us, "measured_us",
                                        minimum=0.0))
        if args.rows:
            rows = load_rows(args.rows)
            payload = annotate_profile_formulas(
                rows, sku=args.sku, launch_mode=args.launch_mode,
                steady_l2_warm=args.steady_l2_warm, tol=tol,
                include_card=args.full)
        else:
            if not args.operator:
                raise ProfilerUsageError("--operator or --rows is required")
            try:
                if args.params_file:
                    params_path = Path(args.params_file)
                    if params_path.stat().st_size > MAX_FILE_BYTES:
                        raise ProfilerUsageError("params file exceeds 64 MiB")
                    params = json.loads(params_path.read_text(encoding="utf-8"))
                else:
                    params = json.loads(args.params)
            except TimeoutError:
                raise
            except (OSError, json.JSONDecodeError) as exc:
                raise ProfilerUsageError(f"invalid --params JSON: {exc}") from exc
            if not isinstance(params, dict):
                raise ProfilerUsageError("--params must decode to a JSON object")
            evaluation, diagnostic = evaluate_with_diagnostics(
                args.operator, params, sku=args.sku,
                launch_mode=args.launch_mode,
                steady_l2_warm=args.steady_l2_warm,
                measured_us=measured, tol=tol)
            payload = evaluation.as_dict()
            payload["diagnostic"] = diagnostic
    except (FormulaError, ProfilerError, ValueError, TypeError,
            OverflowError) as exc:
        print(f"mindie_profiler op-formula: {exc}")
        return 2
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2,
                      allow_nan=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


def __getattr__(name: str) -> Any:
    if name == "MCP_TOOL_SPECS":
        from .op_mcp_tool_specs import MCP_TOOL_SPECS
        return MCP_TOOL_SPECS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ANNOTATION_SCHEMA", "MCP_SCHEMA", "MCP_TOOL_SPECS",
    "aggregate_records", "annotate_profile_formulas", "annotate_row",
    "call_mcp_tool", "display_name", "evaluate_op_formula", "infer_request",
    "load_rows", "main",
]


def evaluate_op_formula(operator: str, params: Mapping[str, Any] | None = None,
                        *, sku: str = "Ascend950DT_9581",
                        launch_mode: str = "eager",
                        steady_l2_warm: bool = False,
                        measured_us: float | None = None):
    """Deterministic Python alias used by the MCP tool and external callers."""
    from mindie_sim.op_formulas import evaluate_operator
    return evaluate_operator(operator, params, sku=sku,
                             launch_mode=launch_mode,
                             steady_l2_warm=steady_l2_warm,
                             measured_us=measured_us)
