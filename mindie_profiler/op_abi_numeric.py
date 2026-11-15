"""Strict numeric scalar and list decoders shared by ABI padding rules.

[Role]
  Convert captured descriptor values into finite numbers, non-negative integer
  tokens and bounded numeric sequences without truthiness or string coercion.

[Invariants]
  * Bools, empty strings, NaN, infinities and non-numeric spellings decode to
    ``None``.
  * Integer tokens reject negative, fractional and non-finite values.
  * Sequence decoding enforces ``bounded_sequence`` before element conversion.

[Timeouts & Locks]
  Pure in-memory conversion; no I/O or locks.

[Side-Effect Policy]
  No mutation of caller values.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from .repro_values import bounded_sequence


def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value) if isinstance(value, (int, float)) else float(str(value).strip())
        return number if math.isfinite(number) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _strict_tokens(value: Any) -> int | None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, bytes)):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, float):
        return (
            int(value)
            if value == value
            and value not in (float("inf"), float("-inf"))
            and value.is_integer()
            and value >= 0
            else None
        )
    return None


def numeric_list(value: Any) -> list[float] | None:
    if value is None or isinstance(value, (str, bytes)):
        return None
    if isinstance(value, Sequence):
        numbers = [_num(item) for item in bounded_sequence(value, "numeric array")]
        return None if any(item is None for item in numbers) else numbers
    number = _num(value)
    return None if number is None else [number]


__all__ = ["_num", "_strict_tokens", "numeric_list"]
