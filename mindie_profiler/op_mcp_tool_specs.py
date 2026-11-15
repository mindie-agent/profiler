"""MCP tool metadata for the operator-formula annotator.

[Role]
  Single source of truth for the two MCP tool descriptors exposed by
  ``mindie_profiler.op_formula_annotator``.

[Invariants]
  * The descriptors are immutable module constants describing exactly the
    accepted request fields; no path or free-form diagnostic text is added.
  * Every property is JSON-serializable and every tool has an explicit
    ``additionalProperties=False`` contract.

[Timeouts & Locks]
  Pure literal data; no I/O.

[Side-Effect Policy]
  No mutation; callers receive the shared constant by reference.
"""

from __future__ import annotations

from .op_formula_annotator import MAX_MCP_ROWS

MCP_TOOL_SPECS = (
    {
        "name": "evaluate_op_formula",
        "description": "Compute physical floor and Roofline bounds for an Ascend operator.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operator": {"type": "string", "description": "Operator key or kernel name."},
                "params": {"type": "object", "description": "Shape, dtype, and collective map."},
                "sku": {"type": "string", "description": "Ascend SKU id."},
                "launch_mode": {"type": "string", "description": "Dispatch mode (eager/aclgraph)."},
                "steady_l2_warm": {"type": "boolean", "description": "Warm L2 residency flag."},
                "measured_us": {"type": "number", "minimum": 0, "description": "Observed latency (us)."},
                "observed_us": {"type": "number", "minimum": 0, "description": "Alias for measured_us."},
                "tol": {"type": "number", "minimum": 0, "description": "Floor violation tolerance."},
                "topology": {"type": "string", "description": "Collective algorithm or transport."},
                "ranks": {"type": "integer", "minimum": 1, "description": "Collective rank count."},
            },
            "required": ["operator"],
            "additionalProperties": False,
        },
    },
    {
        "name": "annotate_profile_formulas",
        "description": "Annotate kernel rows with Roofline bounds and physical floor checks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rows": {"type": "array", "maxItems": MAX_MCP_ROWS, "items": {"type": "object"}, "description": "Captured kernel rows."},
                "sku": {"type": "string", "description": "Ascend SKU id."},
                "launch_mode": {"type": "string", "description": "Dispatch mode (eager/aclgraph)."},
                "steady_l2_warm": {"type": "boolean", "description": "Warm L2 residency flag."},
                "tol": {"type": "number", "minimum": 0, "description": "Floor violation tolerance."},
                "topology": {"type": "string", "description": "Default collective topology."},
                "ranks": {"type": "integer", "minimum": 1, "description": "Default collective rank count."},
            },
            "required": ["rows"],
            "additionalProperties": False,
        },
    },
)


__all__ = ["MCP_TOOL_SPECS"]
