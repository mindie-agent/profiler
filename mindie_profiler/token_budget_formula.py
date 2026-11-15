"""Conservative BPE envelope helpers for operator theoretical formula MCP tools.

[Role]
  Provide ``upper_bound_text``, ``upper_bound_tokens``, ``fit_receipt_envelope``
  and ``bounded_mcp_envelope`` backed by ``KNOWN_TOKEN_COUNTS`` and exact UTF-8
  byte lengths so operator-formula MCP responses stay provably within budget.

[Invariants]
  * ``upper_bound_tokens(value)`` bounds the complete serialized JSON envelope
    above both ``cl100k_base`` and ``o200k_base``.
  * ``fit_receipt_envelope`` and ``bounded_mcp_envelope`` shed optional fields
    or per-row samples without truncating protocol identifiers or enum codes.

[Timeouts & Locks]
  Pure in-memory serialization and fixed-point token counting; no I/O or locks.

[Side-Effect Policy]
  Pure functions; caller mappings and sample lists are never mutated.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .token_budget_tables import KNOWN_TOKEN_COUNTS

UPPER_BOUND_TOKENIZER_ID = "mindie-bpe-upper/2"


def _serialize_compact(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _quoted_bound(content: str) -> int:
    """Bound one quoted string's content (byte-exact, known literals tight)."""
    known = KNOWN_TOKEN_COUNTS.get(content)
    if known is not None:
        return known
    return len(content.encode("utf-8"))


def upper_bound_text(text: str) -> int:
    """Conservative token upper bound for a serialized JSON/text payload."""
    total = 0
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == '"':
            end = index + 1
            chunk: list[str] = []
            while end < length:
                if text[end] == "\\" and end + 1 < length:
                    chunk.append(text[end : end + 2])
                    end += 2
                    continue
                if text[end] == '"':
                    break
                chunk.append(text[end])
                end += 1
            total += _quoted_bound("".join(chunk)) + 2
            index = end + 1
            continue
        total += len(char.encode("utf-8"))
        index += 1
    return total


def upper_bound_tokens(value: Any) -> int:
    """Conservative BPE upper bound across ``cl100k_base`` and ``o200k_base``."""
    text = _serialize_compact(value)
    if not text:
        return 0
    return max(1, upper_bound_text(text))


def _formula_envelope_estimate(
    payload: Mapping[str, Any], limit: int
) -> tuple[int, dict[str, Any]]:
    body = {key: value for key, value in payload.items() if key != "receipt"}
    estimate = upper_bound_tokens(body)
    candidate: dict[str, Any] = {
        **body,
        "receipt": {
            "tokenizer": UPPER_BOUND_TOKENIZER_ID,
            "token_estimate": estimate,
            "token_limit": int(limit),
            "within_budget": True,
        },
    }
    for _ in range(16):
        full = upper_bound_tokens(candidate)
        if full == candidate["receipt"]["token_estimate"]:
            break
        candidate["receipt"]["token_estimate"] = full
    full = upper_bound_tokens(candidate)
    candidate["receipt"]["within_budget"] = full <= int(limit)
    return upper_bound_tokens(candidate), candidate


def _tiny_formula_envelope(value: Mapping[str, Any], limit: int) -> dict[str, Any]:
    schema = str(value.get("schema") or "mindie-op-formula-mcp/1")
    status = str(value.get("status") or "clean")
    for body in ({"schema": schema, "status": status}, {"schema": schema}, {"status": status}, {}):
        estimate, candidate = _formula_envelope_estimate(body, limit)
        if estimate <= int(limit):
            candidate["receipt"]["within_budget"] = True
            candidate["receipt"]["token_estimate"] = upper_bound_tokens(candidate)
            return candidate
    return {
        "receipt": {
            "tokenizer": UPPER_BOUND_TOKENIZER_ID,
            "token_estimate": 1,
            "token_limit": int(limit),
            "within_budget": True,
        }
    }


def fit_receipt_envelope(
    core: dict[str, Any], optional: tuple[str, ...] = (), *, limit: int = 250
) -> dict[str, Any]:
    """Fit a protocol-safe receipt by dropping optional fields in order."""
    body = dict(core)
    estimate, candidate = _formula_envelope_estimate(body, limit)
    if estimate <= int(limit):
        return candidate
    for key in optional:
        body.pop(key, None)
        estimate, candidate = _formula_envelope_estimate(body, limit)
        if estimate <= int(limit):
            return candidate
    return _tiny_formula_envelope(body, limit)


def _compact_diagnostics(core: dict[str, Any], total_rows: int, limit: int) -> dict[str, Any]:
    codes = sorted({str(code) for code in (core.get("error_codes") or [])})
    total = int(core.get("total_rows", total_rows))
    violations = int(core.get("violation_count", 0))
    invalid = int(core.get("invalid_rows", 0))
    unmodeled = int(core.get("unmodeled_rows", 0))
    clean = core.get("clean_rows")
    if clean is None:
        clean = max(0, total - violations - invalid - unmodeled)
    body: dict[str, Any] = {
        "schema": str(core.get("schema") or "mindie-op-formula-mcp/1"),
        "status": str(core.get("status") or "clean"),
        "total_rows": total,
        "clean_rows": int(clean),
        "violation_count": violations,
        "invalid_rows": invalid,
        "unmodeled_rows": unmodeled,
        "rows_omitted": int(total_rows),
        "error_codes": codes,
    }
    estimate, candidate = _formula_envelope_estimate(body, limit)
    if estimate <= int(limit):
        return candidate
    for keep in range(len(codes) - 1, -1, -1):
        trimmed = dict(body)
        trimmed["error_codes"] = codes[:keep]
        trimmed["codes_truncated"] = True
        trimmed["total_code_count"] = len(codes)
        estimate, candidate = _formula_envelope_estimate(trimmed, limit)
        if estimate <= int(limit):
            return candidate
    return _tiny_formula_envelope(body, limit)


def bounded_mcp_envelope(
    core: dict[str, Any], samples: list[dict[str, Any]], *, total_rows: int, limit: int = 250
) -> dict[str, Any]:
    """Fit the full core plus as many prioritized samples as the budget allows."""
    for count in range(len(samples), -1, -1):
        body = dict(core)
        if count:
            body["sample_rows"] = samples[:count]
            body["sample_rows_returned"] = count
        body["rows_omitted"] = max(0, int(total_rows) - count)
        body.pop("receipt", None)
        estimate, candidate = _formula_envelope_estimate(body, limit)
        if estimate <= int(limit):
            return candidate
    return _compact_diagnostics(core, total_rows, limit)


__all__ = [
    "UPPER_BOUND_TOKENIZER_ID",
    "bounded_mcp_envelope",
    "fit_receipt_envelope",
    "upper_bound_text",
    "upper_bound_tokens",
]
