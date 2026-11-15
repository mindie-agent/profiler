"""Sequence-length and group-list validation plus metadata synthesis.

[Role]
  Validate cumulative/per-sequence offsets and group-list encodings exactly, and
  synthesize deterministic offsets/group lists for the reproducer.

[Invariants]
  * Negative, fractional, non-monotone, missing-leading-zero and out-of-extent
    metadata is reported as an explicit violation, never clamped.
  * Sparse-pair indices are unique/increasing and in range.
  * Synthesized counts sum exactly to the requested total.

[Timeouts & Locks]
  Pure in-memory arithmetic; no I/O.

[Side-Effect Policy]
  No mutation of caller values.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from .op_abi_numeric import _num, numeric_list


def validate_sequence_lengths(values: Any, *, encoding: str | None,
                              extent: int | None = None,
                              leading_zero: bool = False,
                              per_sequence: bool = False,
                              label: str = "sequence") -> dict[str, Any]:
    """Validate a cumulative-offset or per-sequence length vector exactly.

    Negative entries, fractional entries, a missing leading zero, decreasing
    cumulative offsets and values beyond the physical tensor extent are hard
    violations.  ``per_sequence`` treats ``extent`` as the sequence-axis bound
    for every item (BSH/BSND/BNSD), never as a cumulative token bound.  Nothing
    is clamped or rounded into validity.
    """
    raw = numeric_list(values)
    violations: list[dict[str, Any]] = []
    if raw is None:
        return {"valid": False, "values": None, "total": 0,
                "violations": [{"code": f"{label}_not_numeric",
                                "detail": repr(values)}]}
    if any(not float(value).is_integer() for value in raw):
        violations.append({"code": f"{label}_fractional",
                           "detail": str(list(raw)[:8])})
    numbers = [int(value) for value in raw]
    if any(value < 0 for value in numbers):
        violations.append({"code": f"{label}_negative",
                           "detail": str(numbers[:8])})
    mode = str(encoding or "cumsum")
    if mode == "lengths":
        total = sum(max(0, value) for value in numbers)
    else:
        if leading_zero and numbers and numbers[0] != 0:
            violations.append({"code": f"{label}_missing_leading_zero",
                               "detail": str(numbers[:8])})
        if any(right < left for left, right in zip(numbers, numbers[1:])):
            violations.append({"code": f"{label}_not_monotone",
                               "detail": str(numbers[:8])})
        body = numbers[1:] if leading_zero and numbers and numbers[0] == 0 else numbers
        total = body[-1] if body else 0
        if extent is not None and any(value > extent for value in numbers):
            violations.append({"code": f"{label}_exceeds_extent",
                               "detail": f"{numbers} > {extent}"})
    if mode == "lengths" and extent is not None:
        if per_sequence:
            if any(value > extent for value in numbers):
                violations.append({"code": f"{label}_exceeds_per_sequence_extent",
                                   "detail": f"{numbers} > {extent}"})
        elif total > extent:
            violations.append({"code": f"{label}_exceeds_extent",
                               "detail": f"{total} > {extent}"})
    return {"valid": not violations, "values": numbers, "total": max(0, total),
            "encoding": mode, "extent": extent, "per_sequence": bool(per_sequence),
            "violations": violations}


def validate_group_list(values: Sequence[float], group_type: str | int, capacity: int,
                        num_groups: int | None = None) -> dict[str, Any]:
    """Validate one group_list against its declared encoding."""
    raw = list(values)
    kind = str(group_type)
    violations: list[dict[str, Any]] = []
    fractional: list[Any] = []
    numbers: list[int] = []
    for value in raw:
        number = _num(value)
        if number is None or isinstance(value, bool) or not float(number).is_integer():
            fractional.append(value)
        else:
            numbers.append(int(number))
    if fractional:
        violations.append({"code": "group_list_fractional",
                           "detail": f"non-integral entries {fractional[:8]}"})
    routed = 0
    if any(value < 0 for value in numbers):
        violations.append({"code": "group_list_negative",
                           "detail": f"negative entry in {numbers}"})
    if kind in {"0", "cumsum"}:
        if any(right < left for left, right in zip(numbers, numbers[1:])):
            violations.append({"code": "group_list_not_monotone",
                               "detail": f"cumsum {numbers} decreases"})
        if numbers and numbers[-1] > capacity:
            violations.append({"code": "group_list_out_of_bounds",
                               "detail": f"tail {numbers[-1]} > capacity {capacity}"})
        routed = numbers[-1] if numbers else 0
        encoding = "cumsum"
    elif kind in {"1", "counts", "count"}:
        total = sum(numbers)
        if numbers and total > capacity:
            violations.append({"code": "group_list_out_of_bounds",
                               "detail": f"counts sum {total} > capacity {capacity}"})
        routed = total
        encoding = "counts"
    elif kind in {"2", "sparse_pairs", "pairs"}:
        if len(numbers) % 2:
            violations.append({"code": "group_list_pairs_odd",
                               "detail": f"sparse pair vector has {len(numbers)} entries"})
        indices = numbers[0::2]
        sizes = numbers[1::2]
        if any(right <= left for left, right in zip(indices, indices[1:])):
            violations.append({"code": "group_list_pairs_not_increasing",
                               "detail": f"sparse indices {indices} are not unique/increasing"})
        if num_groups is not None and any(index >= num_groups for index in indices):
            violations.append({"code": "group_list_pairs_index_out_of_range",
                               "detail": f"indices {indices} >= groups {num_groups}"})
        routed = sum(sizes)
        if routed > capacity:
            violations.append({"code": "group_list_out_of_bounds",
                               "detail": f"paired sizes sum {routed} > capacity {capacity}"})
        encoding = "sparse_pairs"
    else:
        violations.append({"code": "group_list_type_unknown", "detail": str(group_type)})
        encoding = "unknown"
    return {"encoding": encoding, "routed_tokens": max(0, routed),
            "values": numbers, "valid": not violations, "violations": violations}


def synthesize_offsets(counts: Sequence[int], *, cumulative: bool,
                       leading_zero: bool = True) -> list[int]:
    """Emit per-batch lengths or a cumulative offset vector."""
    clean = [max(0, int(value)) for value in counts]
    if not cumulative:
        return clean
    out, running = [], 0
    if leading_zero:
        out.append(0)
    for value in clean:
        running += value
        out.append(running)
    return out


def synthesize_group_list(total: int, groups: int, group_type: str | int = "0") -> list[int]:
    """Split ``total`` rows across an integral number of groups."""
    try:
        number = float(groups)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"group count must be a positive integer, got {groups!r}")
    if isinstance(groups, bool) or not number.is_integer() or number < 1:
        raise ValueError(f"group count must be a positive integer, got {groups!r}")
    total, groups = max(0, int(total)), int(number)
    base, extra = divmod(total, groups)
    counts = [base + (1 if index < extra else 0) for index in range(groups)]
    kind = str(group_type)
    if kind in {"1", "counts", "count"}:
        return counts
    if kind in {"2", "sparse_pairs", "pairs"}:
        out, running = [], 0
        for index, count in enumerate(counts):
            out.extend([index, count])
        return out
    out, running = [], 0
    for count in counts:
        running += count
        out.append(running)
    return out


__all__ = ["synthesize_group_list", "synthesize_offsets", "validate_group_list", "validate_sequence_lengths"]
