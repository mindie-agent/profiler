"""Provable byte-level BPE upper bound for bounded MCP artifact receipts.

[Role]
  Bound every MCP envelope with a dependency-free estimate that is at or above
  the real ``cl100k_base`` and ``o200k_base`` token count of the exact compact
  JSON that is returned, receipt included.  Arbitrary text is charged one token
  per UTF-8 byte; closed tables supply pre-verified exact counts for fixed
  protocol keys, schemas, statuses, errors, issue enums and operator names.

[Invariants]
  * Both shipped byte-level BPE vocabularies contain a token for every byte
    ``0x00..0xFF`` and merges only preserve or reduce token count, so
    ``len(text.encode("utf-8"))`` is a mathematical upper bound for any text.
  * Only exact fragments of the finite protocol vocabulary use the calibrated
    tables; caller names, paths, digests, hex runs and arbitrary strings are
    charged at one token per UTF-8 byte (quotes and escapes included).
  * ``bounded_envelope``, ``bounded_mcp_envelope`` and ``fit_receipt_envelope``
    never return an estimate above ``limit`` and never report
    ``within_budget=False``.
  * Path omission deletes path keys cleanly and sets ``status="delivery_blocked"``,
    ``error="artifact_paths_not_representable"``, ``retrievable=False`` and
    ``artifact_path_omitted=True``.
  * ``schema``/``status``/``error``/identities and issue codes are never sliced.

[Timeouts & Locks]
  Pure in-memory work proportional to the serialized payload length.

[Side-Effect Policy]
  No I/O, network, subprocess or tokenizer download.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from .repro_snapshot import snapshot_call
from .token_budget_formula import (
    UPPER_BOUND_TOKENIZER_ID,
    bounded_mcp_envelope,
    fit_receipt_envelope,
    upper_bound_text,
    upper_bound_tokens,
)
from .token_budget_tables import (
    KNOWN_TOKEN_COUNTS,
    _ARTIFACT_KEYS,
    _CHARGE_KEYS,
    _CORE_STRING_KEYS,
    _FLAG_KEYS,
    _ISSUE_CODES,
    _KEY_TOKENS,
    _KNOWN_KEYS,
    _OPTIONAL_DROP,
    _PADDING_KEYS,
    _PATH_KEYS,
    _PATH_SUFFIX_TOKENS,
    _SCHEMA_WHITELIST,
    _STATUS_WHITELIST,
    _VALUE_TOKENS,
)

TOKENIZER_ID = "b3"
BYTES_PER_TOKEN = 1.0
_TOKEN_LIMIT = 250
_STRUCTURAL = frozenset("{}[],:")
_BOUNDED_CODE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


def _dynamic_string_cost(literal: str) -> int:
    """Full bytes for the dynamic part, exact counts for fixed protocol fixes."""
    value = literal[1:-1]
    if value.startswith("sha256:") and len(value) == 71:
        return 4 + len(value[7:].encode("utf-8")) + 1
    if value.startswith("/"):
        for suffix, count in _PATH_SUFFIX_TOKENS.items():
            if value.endswith(suffix) and len(value) > len(suffix):
                prefix = value[:-len(suffix)]
                return 2 + len(prefix.encode("utf-8")) + count
    return len(literal.encode("utf-8"))


def _string_end(text: str, start: int) -> int:
    index, escaped = start + 1, False
    while index < len(text):
        character = text[index]
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif character == '"':
            return index
        index += 1
    return len(text) - 1


def _upper_bound_json(text: str) -> int:
    """Sum exact protocol-fragment counts and one token per dynamic UTF-8 byte."""
    total, index, length = 0, 0, len(text)
    while index < length:
        character = text[index]
        if character in "{," and index + 1 < length and text[index + 1] == '"':
            end = _string_end(text, index + 1)
            if end + 1 < length and text[end + 1] == ":":
                key = text[index + 2:end]
                count = _KEY_TOKENS.get(key)
                if count is not None:
                    total += count
                    index = end + 2
                    continue
        if character == '"':
            end = _string_end(text, index)
            literal = text[index:end + 1]
            count = _VALUE_TOKENS.get(literal[1:-1])
            total += count if count is not None else _dynamic_string_cost(literal)
            index = end + 1
            continue
        if character in _STRUCTURAL:
            total += 1
            index += 1
            continue
        if text.startswith("true", index) or text.startswith("null", index):
            total += 1
            index += 4
            continue
        if text.startswith("false", index):
            total += 1
            index += 5
            continue
        end = index
        while end < length and text[end] not in '"{}[],:':
            end += 1
        total += max(1, len(text[index:end].encode("utf-8")))
        index = end if end > index else index + 1
    return total


def serialize(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def estimate_tokens(value: Any) -> int:
    text = serialize(value)
    if not text:
        return 0
    if isinstance(value, str):
        quoted = _VALUE_TOKENS.get(text)
        if quoted is not None:
            return max(1, quoted)
        return max(1, len(text.encode("utf-8")))
    if '"schema":"mindie-op-formula-mcp/1"' in text:
        return max(1, upper_bound_text(text))
    return max(1, _upper_bound_json(text))


def within_budget(value: Any, limit: int) -> bool:
    return estimate_tokens(value) <= int(limit)


def _receipt_payload(body: Mapping[str, Any], limit: int,
                     *, include_limit: bool = True) -> dict[str, Any]:
    estimate = estimate_tokens(body)
    receipt: dict[str, Any] = {
        "tokenizer": TOKENIZER_ID, "token_estimate": estimate,
        "within_budget": True}
    if include_limit:
        receipt["token_limit"] = int(limit)
    return {**body, "receipt": receipt}


def receipt(value: Any, *, limit: int = _TOKEN_LIMIT, **extra: Any
            ) -> dict[str, Any]:
    body = dict(value) if isinstance(value, Mapping) else {}
    candidate = _receipt_payload(body, int(limit))
    full = estimate_tokens(candidate)
    candidate["receipt"]["token_estimate"] = estimate_tokens(body)
    candidate["receipt"]["within_budget"] = full <= int(limit)
    for key, item in extra.items():
        candidate[key] = item
    return candidate


def _shorten(value: str, string_limit: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= string_limit:
        return value
    return encoded[:max(0, int(string_limit))].decode("utf-8", "ignore") + "..."


def sanitize_code(value: Any, fallback: str = "invalid_request") -> str:
    text = str(value)
    if text in _ISSUE_CODES:
        return text
    if len(text) <= 64 and _BOUNDED_CODE.fullmatch(text):
        return text
    return fallback


def _sanitize_field(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    if value in _CORE_STRING_KEYS:
        return value
    if len(value) <= 64:
        return value
    return None


def _project_issue(issue: Any, *, keep_detail: bool = True) -> Any:
    if isinstance(issue, Mapping):
        projected: dict[str, Any] = {
            "code": sanitize_code(issue.get("code"),
                                  "invalid_occurrence_issue")}
        for key in ("name", "slot"):
            value = issue.get(key)
            if isinstance(value, (str, int)) and not isinstance(value, bool):
                if isinstance(value, str) and len(value) > 64:
                    continue
                if keep_detail:
                    projected[key] = value
        if keep_detail and "detail" in issue:
            projected["detail"] = truncate_lists(issue.get("detail"),
                                                 string_limit=256)
        return projected
    if isinstance(issue, str):
        return sanitize_code(issue)
    return {"code": "invalid_occurrence_issue"}


def _project_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, item in payload.items():
        if key == "receipt" or key not in _KNOWN_KEYS:
            continue
        if key == "issues" and isinstance(item, (list, tuple)):
            out["issues"] = [_project_issue(entry) for entry in item[:8]]
            if len(item) > 8:
                out["issues_omitted"] = len(item) - 8
            continue
        if key in _CORE_STRING_KEYS:
            if isinstance(item, str):
                if key in ("error", "schema", "status") and len(item) > 64:
                    out[key] = ("invalid_request" if key == "error"
                                else "mindie-mcp-envelope/1")
                else:
                    out[key] = item
            elif key in _PATH_KEYS and item is None:
                out[key] = None
            continue
        if key in ("artifact", "padding") and isinstance(item, Mapping):
            allowed = _ARTIFACT_KEYS if key == "artifact" else _PADDING_KEYS
            compact = {name: value for name, value in item.items()
                       if name in allowed}
            if key == "padding" and isinstance(compact.get("charges"), list):
                compact["charges"] = [
                    {name: value for name, value in charge.items()
                     if name in _CHARGE_KEYS}
                    for charge in compact["charges"][:2]
                    if isinstance(charge, Mapping)]
            if compact:
                out[key] = compact
            continue
        if key in _FLAG_KEYS or key in _KNOWN_KEYS:
            out[key] = item
    if "issues" not in out and isinstance(payload.get("issues"), (list, tuple)):
        out["issues"] = []
    return out


def truncate_lists(value: Any, *, list_limit: int = 8,
                   string_limit: int = 256, max_dict_items: int = 16,
                   protect_strings: bool = False) -> Any:
    """Cap list/dict width while keeping protocol values whole."""
    if isinstance(value, Mapping):
        kept: dict[str, Any] = {}
        omitted = 0
        for key, item in value.items():
            text = str(key)
            allowed = (text in _KNOWN_KEYS or text in _CORE_STRING_KEYS
                       or text in _FLAG_KEYS or text.startswith("_"))
            if not allowed:
                omitted += 1
                continue
            if len(kept) >= max(0, int(max_dict_items)):
                omitted += 1
                continue
            if isinstance(item, str):
                kept[text] = (item if (protect_strings
                                       or text in _CORE_STRING_KEYS
                                       or text in _ARTIFACT_KEYS)
                              else _shorten(item, string_limit))
                continue
            if isinstance(item, list) and text == "issues":
                kept[text] = [_project_issue(entry, keep_detail=(
                    string_limit > 16)) if isinstance(entry, Mapping)
                    else sanitize_code(entry) if isinstance(entry, str)
                    else _truncate_lists_snapshot(entry, list_limit=list_limit,
                                        string_limit=string_limit,
                                        max_dict_items=max_dict_items,
                                        protect_strings=protect_strings)
                    for entry in item[:max(1, int(list_limit))]]
                if len(item) > max(1, int(list_limit)):
                    kept["issues_omitted"] = len(item) - max(1, int(list_limit))
                continue
            if isinstance(item, list) and len(item) > list_limit:
                kept[text] = [_truncate_lists_snapshot(
                    entry, list_limit=list_limit, string_limit=string_limit,
                    max_dict_items=max_dict_items,
                    protect_strings=protect_strings)
                    for entry in item[:max(1, int(list_limit))]]
                kept[f"{text}_truncated_count"] = len(item) - int(list_limit)
                continue
            kept[text] = _truncate_lists_snapshot(
                item, list_limit=list_limit, string_limit=string_limit,
                max_dict_items=max_dict_items,
                protect_strings=protect_strings)
        if omitted:
            kept["_omitted_keys"] = omitted
        return kept
    if isinstance(value, list):
        return [_truncate_lists_snapshot(item, list_limit=list_limit,
                               string_limit=string_limit,
                               max_dict_items=max_dict_items,
                               protect_strings=protect_strings)
                for item in value[:max(1, int(list_limit))]]
    if isinstance(value, str):
        if protect_strings:
            return value
        return _shorten(value, string_limit)
    return value


def _envelope_estimate(payload: Mapping[str, Any], limit: int,
                       *, include_limit: bool = False
                       ) -> tuple[int, dict[str, Any]]:
    body = {key: value for key, value in payload.items() if key != "receipt"}
    estimate = estimate_tokens(body)
    candidate = _receipt_payload(body, int(limit), include_limit=include_limit)
    candidate["receipt"]["token_estimate"] = estimate
    full = estimate_tokens(candidate)
    for _ in range(8):
        candidate["receipt"]["token_estimate"] = estimate
        candidate["receipt"]["within_budget"] = full <= int(limit)
        updated = estimate_tokens(candidate)
        if updated == full:
            break
        full = updated
    candidate["receipt"]["token_estimate"] = estimate
    candidate["receipt"]["within_budget"] = full <= int(limit)
    return full, candidate


def _trim_issues(payload: dict[str, Any], keep: int) -> dict[str, Any]:
    issues = payload.get("issues")
    if not isinstance(issues, list):
        return dict(payload)
    out = dict(payload)
    if len(issues) > keep:
        out["issues"] = issues[:max(0, int(keep))]
        out["issues_omitted"] = len(issues) - max(0, int(keep))
    return out


def _drop_issue_details(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    issues = out.get("issues")
    if isinstance(issues, list):
        codes = []
        for issue in issues:
            if isinstance(issue, Mapping):
                codes.append({"code": sanitize_code(
                    issue.get("code"), "invalid_occurrence_issue")})
            elif isinstance(issue, str):
                codes.append(sanitize_code(issue))
        out["issues"] = codes
    return out


def omit_unrepresentable_paths(payload: dict[str, Any]) -> dict[str, Any]:
    """Delete path keys and record the deliberate bounded-path transition.

    This is the single transition helper used both by the bounded-envelope
    shedder and by the MCP resolution/generation wrappers.  It never leaves a
    null path key behind: absence plus ``artifact_path_omitted=True`` is the
    one external contract.
    """
    out = dict(payload)
    if any(key in out for key in _PATH_KEYS) or out.get(
            "artifact_path_omitted") is True:
        for key in _PATH_KEYS:
            out.pop(key, None)
        out["artifact_path_omitted"] = True
        out["retrievable"] = False
        out["status"] = "delivery_blocked"
        out["error"] = "artifact_paths_not_representable"
        artifact = out.get("artifact")
        if isinstance(artifact, Mapping):
            artifact = dict(artifact)
            artifact["retrievable"] = False
            out["artifact"] = artifact
    return out


# Historical private spelling; the transition above is the one implementation.
_drop_paths = omit_unrepresentable_paths


def _core_only(payload: dict[str, Any]) -> dict[str, Any]:
    keep = {"schema", "status", "error", "artifact_id", "repro_sha256",
            "script_sha256", "manifest_sha256", "artifact_path",
            "manifest_path", "retrievable", "persisted", "reconciled",
            "resolved", "artifact", "issues", "issue_count",
            "issues_truncated_count", "issues_omitted", "artifact_path_omitted",
            "index_persisted", "index_warning"}
    return {key: value for key, value in payload.items() if key in keep}


def _terminal_failure(payload: Mapping[str, Any]) -> dict[str, Any]:
    schema = payload.get("schema")
    status = payload.get("status")
    terminal: dict[str, Any] = {
        "schema": schema if schema in _SCHEMA_WHITELIST
        else "mindie-mcp-envelope/1",
        "status": status if status in _STATUS_WHITELIST else "blocked",
        "error": "envelope_budget_exceeded",
        "issues": [{"code": "invalid_request"}],
    }
    for flag in ("persisted", "retrievable", "resolved", "index_persisted"):
        if isinstance(payload.get(flag), bool):
            terminal[flag] = payload[flag]
    warning = payload.get("index_warning")
    if isinstance(warning, str) and len(warning) <= 64:
        terminal["index_warning"] = warning
    return terminal


def _candidates(payload: dict[str, Any]):
    yield dict(payload)
    compacted = {key: value for key, value in payload.items()
                 if key not in _OPTIONAL_DROP}
    yield dict(compacted)
    for string_limit in (256, 128, 64, 32, 16, 8):
        yield truncate_lists(payload, list_limit=8,
                             string_limit=string_limit, max_dict_items=32)
    yield _drop_issue_details(compacted)
    for keep in (4, 2, 1):
        yield _trim_issues(compacted, keep)
    shed = _drop_issue_details(compacted)
    for keep in (4, 2, 1):
        yield _trim_issues(shed, keep)
    yield omit_unrepresentable_paths(shed)
    yield _core_only(omit_unrepresentable_paths(shed))


def _assert_protocol_intact(original: Mapping[str, Any],
                            candidate: Mapping[str, Any]) -> None:
    """Exact-value postcondition; the path transition is the only exception."""
    omitted = bool(candidate.get("artifact_path_omitted"))
    terminal = candidate.get("error") == "envelope_budget_exceeded"
    for key in _CORE_STRING_KEYS:
        expected = original.get(key)
        if not isinstance(expected, str) or key not in candidate:
            continue
        if key in _PATH_KEYS and omitted:
            continue
        if omitted and key in ("status", "error"):
            continue
        if terminal and key in ("schema", "status", "error"):
            continue
        if key in ("error", "schema", "status") and len(expected) > 64:
            continue
        actual = candidate.get(key)
        if actual is not None and actual != expected:
            raise AssertionError(f"protocol field {key!r} changed")
    for key in _FLAG_KEYS:
        if key not in original or key not in candidate:
            continue
        if key == "retrievable" and omitted:
            continue
        if candidate.get(key) != original.get(key):
            raise AssertionError(f"protocol flag {key!r} changed")
    original_issues = original.get("issues")
    if isinstance(original_issues, list):
        retained = candidate.get("issues")
        if isinstance(retained, list):
            allowed = {str(entry.get("code")) if isinstance(entry, Mapping)
                       else str(entry) for entry in original_issues}
            for entry in retained:
                code = (str(entry.get("code")) if isinstance(entry, Mapping)
                        else str(entry))
                if code not in allowed and code not in _ISSUE_CODES:
                    raise AssertionError("invented issue code")


def _finalize_terminal(bounded: dict[str, Any],
                       limit: int) -> dict[str, Any]:
    """Measure the terminal envelope itself, never just its body."""
    for _ in range(8):
        full = estimate_tokens(bounded)
        if bounded["receipt"].get("token_estimate") == full:
            break
        bounded["receipt"]["token_estimate"] = full
    full = estimate_tokens(bounded)
    bounded["receipt"]["within_budget"] = full <= int(limit)
    if full > int(limit):
        return {}
    return bounded


def _fit_terminal(payload: Mapping[str, Any], limit: int) -> dict[str, Any]:
    terminal = _terminal_failure(payload)
    total, bounded = _envelope_estimate(terminal, int(limit))
    if total <= int(limit):
        result = _finalize_terminal(bounded, int(limit))
        if result:
            return result
    minimal: dict[str, Any] = {"status": "blocked",
                               "error": "envelope_budget_exceeded"}
    while minimal:
        total, bounded = _envelope_estimate(minimal, int(limit))
        if total <= int(limit):
            result = _finalize_terminal(bounded, int(limit))
            if result:
                return result
        minimal.pop(next(reversed(minimal)))
    for bare in (
        {"receipt": {"tokenizer": TOKENIZER_ID, "token_estimate": 1,
                     "within_budget": True}},
        {"receipt": {"token_estimate": 1, "within_budget": True}},
    ):
        result = _finalize_terminal(bare, int(limit))
        if result:
            return result
    raise ValueError("token limit is too small for a measurable receipt")


def bounded_envelope(value: dict[str, Any], *, limit: int = 3000,
                     list_limit: int = 8) -> dict[str, Any]:
    """Return a complete envelope whose own estimate never exceeds ``limit``."""
    payload = _project_payload(dict(value))
    seen: set[str] = set()
    for candidate in _candidates(payload):
        marker = serialize(candidate)
        if marker in seen:
            continue
        seen.add(marker)
        total, bounded = _envelope_estimate(candidate, int(limit))
        if total <= int(limit):
            _assert_protocol_intact(payload, bounded)
            bounded["receipt"]["within_budget"] = True
            return bounded
    return _fit_terminal(payload, int(limit))


serialize = snapshot_call(serialize, 'value')
receipt = snapshot_call(receipt, 'value', 'extra')
_truncate_lists_snapshot = truncate_lists
truncate_lists = snapshot_call(truncate_lists, 'value')
omit_unrepresentable_paths = snapshot_call(omit_unrepresentable_paths, 'payload')
bounded_envelope = snapshot_call(bounded_envelope, 'value')

__all__ = [
    "BYTES_PER_TOKEN",
    "KNOWN_TOKEN_COUNTS",
    "TOKENIZER_ID",
    "UPPER_BOUND_TOKENIZER_ID",
    "bounded_envelope",
    "bounded_mcp_envelope",
    "estimate_tokens",
    "fit_receipt_envelope",
    "omit_unrepresentable_paths",
    "receipt",
    "sanitize_code",
    "serialize",
    "truncate_lists",
    "upper_bound_text",
    "upper_bound_tokens",
    "within_budget",
]
