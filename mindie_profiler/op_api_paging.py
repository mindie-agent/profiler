"""Lossless, bounded MCP pagination over one full ABI catalog entry.

[Role]
  Convert the complete catalog entry resolved by an MCP ``span`` continuation
  into deterministic pages.  Each page carries the exact catalog artifact,
  the current and next page numbers, a compact list of ``[path, value]``
  fragments, and the normal bounded receipt.

[Invariants]
  * Pages are produced from a deterministic depth-first flattening.  A
    container fragment is emitted only when it fits whole; otherwise its
    children are emitted, so every path occurs once except segmented strings.
  * Following ``next_page`` from zero and merging every page reconstructs the
    catalog entry exactly, including ordered parameters and slot specs.
  * A page always carries the exact artifact reference, its page number, and
    both ``next`` and ``next_page`` aliases for the exact next cursor; the
    caller never has to reconstruct one.
  * A page is passed through ``bounded_envelope``; an information-losing
    truncation raises ``ProfilerUsageError`` instead of returning a partial
    page.
  * The whole page (receipt included) is measured by ``estimate_tokens(page)``
    and never exceeds 250; ``receipt.token_estimate`` is its measured body.
  * Cached pages are keyed by operator, byte span and catalog digest; the
    direct resolver is never narrowed.

[Timeouts & Locks]
  Pure in-memory work.  The cache is a process-local dictionary; a duplicate
  concurrent build is harmless.

[Side-Effect Policy]
  No file, network or subprocess I/O.
"""

from __future__ import annotations

import copy
from typing import Any, Iterator

from .events import ProfilerUsageError
from .repro_values import bounded_mapping
from .token_budget import (
    TOKENIZER_ID, bounded_envelope, estimate_tokens,
)

CARD_SCHEMA = "mindie-op-abi-card/2"
PAGE_LIMIT = 250
_UNIT_LIMIT = 64
_STRING_BYTES = 44
_MAX_ITEMS = 8
_PAGE_CACHE: dict[tuple[str, tuple[int, int], str], tuple[dict[str, Any], ...]] = {}


def _segments(value: str, limit: int = _STRING_BYTES) -> Iterator[str]:
    start = size = 0
    for index, character in enumerate(value):
        width = len(character.encode("utf-8"))
        if size and size + width > limit:
            yield value[start:index]
            start, size = index, 0
        size += width
    yield value[start:]


def _units(value: Any, path: tuple[Any, ...] = ()) -> Iterator[list[Any]]:
    """Flatten a JSON value into path-addressed fragments small enough to pack."""
    if isinstance(value, dict):
        if not value or estimate_tokens(value) <= _UNIT_LIMIT:
            yield [list(path), value]
            return
        for key, item in value.items():
            yield from _units(item, path + (key,))
        return
    if isinstance(value, list):
        if not value or estimate_tokens(value) <= _UNIT_LIMIT:
            yield [list(path), value]
            return
        for index, item in enumerate(value):
            yield from _units(item, path + (index,))
        return
    if isinstance(value, str) and estimate_tokens(value) > _UNIT_LIMIT:
        offset = 0
        for part in _segments(value):
            yield [list(path), part, offset]
            offset += len(part)
        return
    yield [list(path), value]


def _payload(api: str, artifact: dict[str, Any], page: int, next_page: int | None,
             items: list[list[Any]], first: bool) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": CARD_SCHEMA, "artifact": dict(artifact),
        "page": int(page), "cursor": next_page, "next": next_page,
        "next_page": next_page, "items": items,
    }
    if first:
        payload["api"] = api
    return payload


def _fits(payload: dict[str, Any]) -> bool:
    probe = dict(payload)
    estimate = estimate_tokens(probe)
    probe["receipt"] = {"tokenizer": TOKENIZER_ID,
                        "token_estimate": estimate, "within_budget": True}
    full = estimate_tokens(probe)
    for _ in range(8):
        probe["receipt"]["token_estimate"] = estimate
        full = estimate_tokens(probe)
        probe["receipt"]["within_budget"] = full <= PAGE_LIMIT
        if full <= PAGE_LIMIT:
            return True
    return False


def _pack(api: str, artifact: dict[str, Any],
          entry: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    units = list(_units(entry))
    pages: list[dict[str, Any]] = []
    index = 0
    while index < len(units) or not pages:
        items: list[list[Any]] = []
        while index < len(units) and len(items) < _MAX_ITEMS:
            candidate = items + [units[index]]
            body = _payload(api, artifact, len(pages), len(pages) + 1,
                            candidate, not pages)
            if items and not _fits(body):
                break
            items, index = candidate, index + 1
        next_page = None if index >= len(units) else len(pages) + 1
        body = _payload(api, artifact, len(pages), next_page, items, not pages)
        if not _fits(body):
            raise ProfilerUsageError(
                "catalog entry cannot be paged within the 250-token limit")
        bounded = bounded_envelope(body, limit=PAGE_LIMIT)
        if (bounded.get("items") != items
                or bounded.get("page") != len(pages)
                or bounded.get("next_page") != next_page
                or "receipt" not in bounded):
            raise ProfilerUsageError(
                "catalog page lost information under the 250-token limit")
        pages.append(bounded)
        if index >= len(units):
            break
    return tuple(pages)


def span_page(api: str, artifact: dict[str, Any], entry: dict[str, Any],
              page: Any = 0) -> dict[str, Any]:
    """Return one lossless bounded page of the complete catalog entry."""
    artifact = bounded_mapping(artifact, "catalog artifact")
    entry = bounded_mapping(entry, "catalog entry")
    if isinstance(page, bool):
        raise ProfilerUsageError("invalid catalog page")
    try:
        number = int(page)
    except (TypeError, ValueError):
        raise ProfilerUsageError("invalid catalog page") from None
    if number < 0:
        raise ProfilerUsageError("invalid catalog page")
    try:
        span = (int(artifact["span"][0]), int(artifact["span"][1]))
        digest = str(artifact["catalog_sha256_16"])
    except (KeyError, IndexError, TypeError, ValueError):
        raise ProfilerUsageError("invalid catalog artifact reference") from None
    key = (str(api), span, digest)
    pages = _PAGE_CACHE.get(key)
    if pages is None:
        pages = _pack(str(api), artifact, entry)
        if len(_PAGE_CACHE) >= 64:
            _PAGE_CACHE.clear()
        _PAGE_CACHE[key] = pages
    if number >= len(pages):
        raise ProfilerUsageError(
            f"catalog page {number} out of range 0..{len(pages) - 1}")
    return copy.deepcopy(pages[number])


__all__ = ["PAGE_LIMIT", "span_page"]
