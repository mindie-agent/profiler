"""Bounded MCP wrappers for ACLGraph diagnostics and resource checks.

[Role]
Expose `diagnose_region`, SQ/CQ capture-budget checks, SuperKernel eligibility,
and launch floors as deterministic compact MCP tools that keep `mode`, `code`,
`cause`, and `grade` intact while staying <= 250 UTF-8 bytes / 250 BPE tokens.
[Invariants]
Required identity/evidence keys are never truncated. Optional recommendations
are dropped only when the exact envelope would exceed the budget. Every wrapper
is fail-closed on invalid modes, non-finite counts, and unknown tools.
[Timeouts & Locks]
Pure in-memory calls; no locks, waits, I/O, or subprocesses.
[Side-Effect Policy]
Read-only; no files, streams, or graph captures are created.
"""

from __future__ import annotations

from typing import Any, Mapping

from .aclgraph_multistream import (
    ACLGraphModelError, ParallelRegion, check_capture_budget,
    check_superkernel_eligibility, diagnose_region, effective_launch_floor_us,
)


def _ok(payload: dict[str, Any], required: tuple[str, ...]) -> dict[str, Any]:
    from mindie_sim.opflow.token_budget import bounded_envelope

    payload.setdefault("ok", 1)
    return bounded_envelope(payload, required=required)


def _err(code: str, message: str = "") -> dict[str, Any]:
    from mindie_sim.opflow.token_budget import bounded_error

    return bounded_error(code, message)


def aclgraph_diagnose(region: Mapping[str, Any]) -> dict[str, Any]:
    try:
        parsed = ParallelRegion.from_mapping(region)
        result = diagnose_region(parsed)
    except (ACLGraphModelError, KeyError, TypeError, ValueError) as exc:
        return _err("EREGION", str(exc))
    return _ok(
        {
            "code": result.code, "ov": round(result.overlap_pct, 2),
            "net": round(result.net_speedup_us, 2), "wall": round(result.wall_us, 2),
            "cause": result.cause,
            "grade": result.evidence_grade,
            "rec": list(result.recommendations[:2]),
            "sec": list(result.secondary[:2]),
        },
        ("ok", "code", "cause", "grade", "ov", "net", "wall"),
    )


def aclgraph_sq_budget(captured_batch_sizes: int = 1, subgraphs_per_step: int = 1,
                       active_streams_per_graph: int = 1,
                       capacity: int | None = None,
                       mode: str = "piecewise") -> dict[str, Any]:
    from .profiler_configs import DEFAULT_ACLGRAPH_LAUNCH_CONFIG
    if capacity is None:
        capacity = DEFAULT_ACLGRAPH_LAUNCH_CONFIG.sq_cq_stream_capacity
    try:
        budget = check_capture_budget(captured_batch_sizes, subgraphs_per_step,
                                      active_streams_per_graph, capacity=capacity, mode=mode)
    except (ACLGraphModelError, ValueError) as exc:
        return _err("EARGS", str(exc))
    return _ok(
        {"need": budget.required, "cap": budget.capacity, "fits": int(budget.fits),
         "err": budget.error_code, "rec": budget.recommendation},
        ("ok", "need", "cap", "fits", "err"),
    )


def aclgraph_superkernel(static_decode: bool = True, capturable_ops: bool = True,
                         dynamic_tiling_host_sync: bool = False) -> dict[str, Any]:
    try:
        result = check_superkernel_eligibility(
            static_decode=static_decode, capturable_ops=capturable_ops,
            dynamic_tiling_host_sync=dynamic_tiling_host_sync,
        )
    except ACLGraphModelError as exc:
        return _err("EARGS", str(exc))
    return _ok(
        {"eligible": int(result.eligible), "static": int(result.static_decode),
         "dcci": int(result.dcci_after_kernel_end), "reason": result.reason},
        ("ok", "eligible", "static", "dcci"),
    )


def aclgraph_launch_floor(mode: str = "full", superkernel: bool = False) -> dict[str, Any]:
    if not isinstance(superkernel, bool):
        return _err("EARGS", "superkernel must be bool")
    if not isinstance(mode, str):
        return _err("EMODE", "mode must be a string")
    try:
        floor = effective_launch_floor_us(mode, superkernel=superkernel)
    except ACLGraphModelError as exc:
        return _err("EMODE", str(exc))
    return _ok({"mode": mode.lower(), "us": floor, "sk": int(superkernel)},
               ("ok", "mode", "us", "sk"))


TOOL_SPECS: tuple[dict[str, Any], ...] = (
    {
        "name": "aclgraph_diagnose",
        "description": "Diagnose multi-stream ACLGraph overlap loss (codes A1-A5) within <=250 B.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "region": {"type": "object", "description": "ParallelRegion stream/event mapping."},
            },
            "required": ["region"],
            "additionalProperties": False,
        },
    },
    {
        "name": "aclgraph_sq_budget",
        "description": "Check Ascend 207008 SQ/CQ stream-queue capture budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "captured_batch_sizes": {"type": "integer", "minimum": 1, "description": "Captured batch buckets."},
                "subgraphs_per_step": {"type": "integer", "minimum": 1, "description": "Subgraphs per step."},
                "active_streams_per_graph": {"type": "integer", "minimum": 1, "description": "Active streams per graph."},
                "capacity": {"type": "integer", "minimum": 1, "description": "SQ/CQ stream capacity."},
                "mode": {"type": "string", "description": "Graph mode (piecewise/full/eager)."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "aclgraph_superkernel",
        "description": "Check SuperKernel device-loop fusion eligibility.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "static_decode": {"type": "boolean", "description": "Static decode shape flag."},
                "capturable_ops": {"type": "boolean", "description": "All ops capturable without AI-CPU sync."},
                "dynamic_tiling_host_sync": {"type": "boolean", "description": "Host-sync dynamic tiling flag."},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "aclgraph_launch_floor",
        "description": "Return per-kernel ACLGraph or eager Host launch floor (us).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "description": "Launch mode (full/piecewise/eager)."},
                "superkernel": {"type": "boolean", "description": "SuperKernel device-loop flag."},
            },
            "additionalProperties": False,
        },
    },
)

MCP_TOOL_SPECS = TOOL_SPECS

_TOOLS = {
    "aclgraph_diagnose": aclgraph_diagnose, "aclgraph_sq_budget": aclgraph_sq_budget,
    "aclgraph_superkernel": aclgraph_superkernel, "aclgraph_launch_floor": aclgraph_launch_floor,
}


def call_tool(name: str, arguments: Mapping[str, Any] | None = None) -> dict[str, Any]:
    function = _TOOLS.get(str(name))
    if function is None:
        return _err("ETOOL", str(name))
    if arguments is not None and not isinstance(arguments, Mapping):
        return _err("EARGS", "arguments must be an object")
    try:
        return function(**(dict(arguments or {})))
    except TypeError as exc:
        return _err("EARGS", str(exc))
    except TimeoutError:
        raise
    except Exception as exc:  # defensive MCP boundary
        return _err("EINTERNAL", type(exc).__name__)


__all__ = [
    "MCP_TOOL_SPECS", "TOOL_SPECS", "aclgraph_diagnose", "aclgraph_launch_floor",
    "aclgraph_sq_budget", "aclgraph_superkernel", "call_tool",
]
