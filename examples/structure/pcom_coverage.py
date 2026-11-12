"""Out-of-band coverage for a declared partial MoE transport route.

[Role] Report which prediction targets are not formal independent points.
  This never filters or rewrites `compare_cell`/`aggregate` canonical samples.
[Invariants] A partial route is published as its affected targets; ordinary
  and exact-route predictions carry no partial targets.
[Timeouts & Locks] Pure local arithmetic.
[Side-Effect Policy] Returns a new dict; no I/O.
"""
from __future__ import annotations

from typing import Any, Sequence


def conditional_entries(comparisons: Sequence[Any]) -> tuple[Any, ...]:
    """Only the three dependent rows carry the out-of-band conditional flag."""
    return tuple(item for item in comparisons if getattr(item, "conditional", False))


def coverage(predictions: Sequence[Any]) -> dict[str, Any]:
    """Count formal cells and list unresolved targets without dropping rows."""
    partial = [item for item in predictions if getattr(item, "partial_targets", ())]
    return {
        "cells": len(predictions),
        "formal_cells": len(predictions) - len(partial),
        "partial_cells": len(partial),
        "unresolved_targets": tuple(sorted({target for item in partial
                                            for target in item.partial_targets})),
    }
