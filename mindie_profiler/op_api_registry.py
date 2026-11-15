"""Source-pinned operator ABI catalog access, exact lookup and bounded cards.

[Role]
  Index ``op_api_catalog.json`` once by byte span, resolve operator names by
  exact name/alias only (never by prefix), gate on an explicit CANN release and
  optional ABI identity, bind captured slots, and expose a bounded
  ``inspect_op_abi`` receipt plus the CLI.

[Invariants]
  * No prefix or fuzzy name matching exists.  ``aclnnMatmulBogusV999`` and
    ``aclnnFlashAttentionVarLenScoreV999`` are uncatalogued; they return
    ``unknown_abi`` with every raw descriptor preserved.
  * A missing or unverified CANN release returns ``unknown_abi``; the binding is
    never stamped with the entry's last declared release.
  * The catalog text is scanned once per (mtime, size); a lookup parses only its
    own byte span.  Full validation runs in ``load_catalog`` for CLI/summary.
  * Every MCP result is a bounded, content-addressed receipt (<= 250 pinned
    tokens).  Name inspection embeds only the compact reference; a ``span``
    continuation is returned as lossless bounded pages with an exact
    ``next_page`` cursor, while the direct Python resolver and
    ``inspect_op_abi`` remain unstripped and lossless.

[Timeouts & Locks]
  One bounded file read per catalog mtime/size plus a cached span index.  No
  waits, subprocesses or hardware access.

[Side-Effect Policy]
  Read-only except for the optional ``--output`` file written by ``main`` and
  content-addressed artifacts written by the MCP reproducer path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re
from typing import Any
from collections.abc import Mapping

from .events import ProfilerUsageError
from .repro_values import bounded_mapping
from .op_abi_binding import (
    BINDING_SCHEMA, bind_resolved_occurrence, captured_version, operator_name,
)
from .op_api_paging import span_page
from .token_budget import TOKENIZER_ID, estimate_tokens

CATALOG_SCHEMA = "mindie-op-api-catalog/2"
CARD_SCHEMA = "mindie-op-abi-card/2"
CATALOG_FILENAME = "op_api_catalog.json"
CARD_TOKEN_LIMIT = 250
DIRECT_CARD_LIMIT = 20000
MCP_TOKEN_LIMIT = 250
PADDING_MODES = ("masked_varlen", "grouped_prefix", "full_padded_tensor")
SURFACES = ("aclnn_c_api", "torch_npu_op", "vllm_ascend_op", "hccl_collective")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _catalog_path() -> Path:
    return Path(__file__).resolve().with_name(CATALOG_FILENAME)


def _skip_string(text: str, index: int) -> int:
    index += 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
        elif text[index] == '"':
            return index + 1
        else:
            index += 1
    raise ProfilerUsageError("unterminated JSON string in operator catalog")


def _scan_index(text: str) -> tuple[dict[str, tuple[int, int]], dict[str, str]]:
    """Return operator byte spans and the alias map without parsing entries."""
    match = re.search(r'"operators"\s*:\s*\{', text)
    if not match:
        raise ProfilerUsageError("operator catalog has no operators object")
    index = match.end()
    spans: dict[str, tuple[int, int]] = {}
    while True:
        while index < len(text) and text[index] in " \n\r\t,":
            index += 1
        if index >= len(text):
            raise ProfilerUsageError("unterminated operators object")
        if text[index] == "}":
            break
        if text[index] != '"':
            raise ProfilerUsageError("malformed operator key")
        end = _skip_string(text, index)
        key = json.loads(text[index:end])
        index = end
        while index < len(text) and text[index] != ":":
            index += 1
        index += 1
        while index < len(text) and text[index] in " \n\r\t":
            index += 1
        start, depth = index, 0
        while index < len(text):
            if text[index] == '"':
                index = _skip_string(text, index)
                continue
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        spans[str(key)] = (start, index + 1)
        index += 1
    alias_match = re.search(r'"aliases"\s*:\s*\{', text)
    aliases: dict[str, str] = {}
    if alias_match:
        cursor = alias_match.end()
        while True:
            while cursor < len(text) and text[cursor] in " \n\r\t,":
                cursor += 1
            if cursor >= len(text) or text[cursor] == "}":
                break
            key_end = _skip_string(text, cursor)
            alias = json.loads(text[cursor:key_end])
            cursor = key_end
            while text[cursor] != ":":
                cursor += 1
            cursor += 1
            while text[cursor] in " \n\r\t":
                cursor += 1
            value_end = _skip_string(text, cursor)
            aliases[str(alias)] = json.loads(text[cursor:value_end])
            cursor = value_end
    return spans, aliases


@lru_cache(maxsize=8)
def _catalog_index(path_str: str, mtime_ns: int, size: int) -> dict[str, Any]:
    path = Path(path_str)
    try:
        text = path.read_text(encoding="utf-8")
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"cannot read operator catalog {path}: {exc}") from exc
    try:
        spans, aliases = _scan_index(text)
    except json.JSONDecodeError as exc:
        raise ProfilerUsageError(f"invalid operator catalog {path}: {exc}") from exc
    return {"path": str(path.resolve()), "text": text, "spans": spans,
            "aliases": aliases, "sha256": "sha256:" + hashlib.sha256(
                text.encode("utf-8")).hexdigest(), "size": len(text.encode("utf-8"))}


def _index(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path is not None else _catalog_path()
    try:
        stat = target.stat()
    except TimeoutError:
        raise
    except OSError as exc:
        raise ProfilerUsageError(f"operator catalog not found: {target}") from exc
    return _catalog_index(str(target.resolve()), stat.st_mtime_ns, stat.st_size)


def _entry(index: Mapping[str, Any], name: str) -> dict[str, Any]:
    span = index["spans"].get(name)
    if span is None:
        raise ProfilerUsageError(f"operator not catalogued: {name!r}")
    try:
        entry = json.loads(index["text"][span[0]:span[1]])
    except json.JSONDecodeError as exc:
        raise ProfilerUsageError(f"invalid entry {name!r}: {exc}") from exc
    if not isinstance(entry, dict):
        raise ProfilerUsageError(f"operator entry {name!r} is not an object")
    return entry


def _validate_entry(name: str, entry: Mapping[str, Any], versions: set[str]) -> None:
    padding = entry.get("padding_semantics")
    if not isinstance(padding, dict) or padding.get("mode") not in PADDING_MODES:
        raise ProfilerUsageError(f"{name}: invalid padding_semantics")
    slots = entry.get("c_abi_slots")
    if not isinstance(slots, dict) or not isinstance(slots.get("parameters"), list):
        raise ProfilerUsageError(f"{name}: missing c_abi_slots.parameters")
    if entry.get("surface") not in SURFACES:
        raise ProfilerUsageError(f"{name}: invalid surface")
    if not set(map(str, entry.get("cann_versions") or ())) <= versions:
        raise ProfilerUsageError(f"{name}: unknown CANN version tag")
    if not isinstance(entry.get("sources"), list) or not entry["sources"]:
        raise ProfilerUsageError(f"{name}: no pinned source")


def load_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Validate and return the complete catalog (CLI/summary only)."""
    index = _index(path)
    try:
        doc = json.loads(index["text"])
    except json.JSONDecodeError as exc:
        raise ProfilerUsageError(f"invalid operator catalog: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("schema") != CATALOG_SCHEMA:
        raise ProfilerUsageError(f"expected schema {CATALOG_SCHEMA}")
    versions = {str(item) for item in doc.get("cann_versions") or ()}
    operators = doc.get("operators")
    if not isinstance(operators, dict) or not versions:
        raise ProfilerUsageError("catalog needs cann_versions[] and operators{}")
    for name, entry in operators.items():
        _validate_entry(str(name), entry, versions)
    if len(operators) != len(index["spans"]):
        raise ProfilerUsageError("operator span index disagrees with parsed catalog")
    return doc


def operator_names(path: str | Path | None = None) -> tuple[str, ...]:
    return tuple(_index(path)["spans"])


def _resolve_name(index: Mapping[str, Any], raw: str) -> tuple[str | None, str, str | None]:
    spans = index["spans"]
    if raw in spans:
        return raw, "exact", None
    lowered = raw.lower()
    for name in spans:
        if name.lower() == lowered:
            return name, "exact_casefold", None
    alias = index["aliases"].get(lowered)
    if alias == "__ambiguous__":
        return None, "", "ambiguous_alias"
    if alias:
        return alias, "alias", None
    return None, "", "uncatalogued_name"


def catalog_operator(
    op_name: str,
    *,
    cann_version: str | None = None,
    abi_id: str | None = None,
    path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Resolve one name by exact name/alias and gate identity exactly."""
    raw = _text(op_name)
    if not raw:
        return None
    index = _index(path)
    canonical, match, reason = _resolve_name(index, raw)
    if canonical is None:
        return None
    entry = _entry(index, canonical)
    versions = [str(item) for item in entry.get("cann_versions") or ()]
    source_pinned = any(source.get("pinned") and source.get("sha256")
                        for source in entry.get("sources") or ())
    signature_status = str(entry["c_abi_slots"].get("signature_status") or
                           ("pinned" if source_pinned else "external_doc_unpinned"))
    version_ok = cann_version is not None and str(cann_version) in versions
    abi_ok = abi_id is None or str(abi_id) == entry.get("abi_id")
    release_basis = str(entry.get("release_basis") or
                        "declared_compatibility_tags_not_build_verified")
    verified_versions = {str(item) for item in
                         entry.get("release_verified_versions") or ()}
    capture_verified = bool((entry.get("flatten_adapter") or {}).get(
        "verified_against_capture"))
    version_qualified = bool(version_ok and (
        str(cann_version) in verified_versions or capture_verified))
    if cann_version is None:
        qualification_state = "version_not_requested"
    elif not version_ok:
        qualification_state = "release_not_declared"
    elif version_qualified:
        qualification_state = ("capture_verified" if capture_verified
                               else "schema_pinned")
    elif source_pinned:
        qualification_state = "schema_pinned_unverified"
    else:
        qualification_state = "release_unverified"
    return {
        "name": canonical, "entry": entry, "match": match,
        "requested_version": None if cann_version is None else str(cann_version),
        "versions": versions,
        "version_supported": version_ok,
        "version_qualified": version_qualified,
        "qualification_state": qualification_state,
        "release_basis": ("declared_not_build_verified" if "not_build_verified"
                          in release_basis else release_basis),
        "schema_pinned": bool(entry["c_abi_slots"].get("pinned")),
        "capture_verified": capture_verified,
        "signature_supported": bool(source_pinned and signature_status == "pinned"),
        "signature_status": signature_status,
        "abi_id": entry.get("abi_id"),
        "abi_id_supported": abi_ok,
        "unknown_reason": reason or (
            "missing_cann_version" if cann_version is None
            else "unverified_cann_version" if not version_ok
            else "abi_id_mismatch" if not abi_ok
            else None if source_pinned else "abi_signature_unpinned"),
    }


def bind_captured_occurrence(row: Any, *, cann_version: str | None = None,
                             catalog: Any = None,
                             path: str | Path | None = None) -> dict[str, Any]:
    """Bind one captured occurrence, preserving raw slots on every failure."""
    if isinstance(row, Mapping):
        row = bounded_mapping(row, "capture row")
    version = cann_version if cann_version is not None else captured_version(row)
    captured_abi = _text(getattr(row, "abi_id", None) if not isinstance(row, dict)
                         else row.get("abi_id")) or None
    target = path if path is not None else (catalog if isinstance(catalog, (str, Path))
                                            else None)
    match = catalog_operator(operator_name(row), cann_version=version,
                             abi_id=captured_abi, path=target)
    return bind_resolved_occurrence(row, match, cann_version=version)


def _compact_slots(slots: list[dict[str, Any]], limit: int = 24) -> str:
    rendered = [f"{slot['name']}:{slot['role']}{'?' if slot.get('optional') else ''}"
                for slot in slots[:limit]]
    if len(slots) > limit:
        rendered.append(f"+{len(slots) - limit}")
    return ",".join(rendered)


def _slot_names(slots: Any) -> list[str]:
    return [str(slot.get("name")) for slot in slots or ()
            if isinstance(slot, dict) and slot.get("name")]


def _slot_specs(slots: Any) -> list[dict[str, Any]]:
    fields = ("name", "c_name", "cat", "role", "optional", "mutable",
              "dtypes", "layouts", "undefined_means_null")
    return [{key: slot[key] for key in fields if key in slot}
            for slot in slots or () if isinstance(slot, dict)]


def _catalog_reference(index: Mapping[str, Any], name: str) -> dict[str, Any]:
    span = index["spans"][name]
    return {"kind": "catalog_span",
            "catalog_sha256_16": index["sha256"].removeprefix("sha256:")[:16],
            "span": list(span)}


def _full_card(match: Mapping[str, Any]) -> dict[str, Any]:
    """Complete direct-call ABI card; the compact MCP projection is separate."""
    entry = match["entry"]
    slots = entry["c_abi_slots"]
    specs = slots.get("slot_specs") or {}
    recipe = entry.get("repro_recipe") or {}
    repro_supported = bool(recipe.get("supported")
                           or recipe.get("repro_supported"))
    repro_status = str(recipe.get("status") or (
        "ready" if repro_supported else "blocked"))
    return {
        "api": match["name"], "abi_id": match["abi_id"],
        "c_abi_slots": slots, "slot_specs": specs,
        "surface": entry["surface"], "pipe": entry["pipe"],
        "signature": slots["kind"], "versions": match["versions"],
        "pinned": bool(slots.get("pinned")),
        "schema_pinned": bool(match["schema_pinned"]),
        "capture_verified": bool(match["capture_verified"]),
        "version_qualified": bool(match["version_qualified"]),
        "qualification": {
            "state": match["qualification_state"],
            "release_basis": match["release_basis"],
            "signature_status": match["signature_status"]},
        "qualification_state": match["qualification_state"],
        "release_basis": match["release_basis"],
        "padding": entry["padding_semantics"]["mode"],
        "inputs": _slot_specs(specs.get("inputs")),
        "input_slots": _slot_names(specs.get("inputs")),
        "input_summary": _compact_slots(specs.get("inputs") or []),
        "outputs": _slot_specs(specs.get("outputs")),
        "output_slots": _slot_names(specs.get("outputs")),
        "output_summary": _compact_slots(specs.get("outputs") or [], 12),
        "attrs": list(slots.get("attr_slots") or ()),
        "recipe": recipe,
        "repro_supported": repro_supported,
        "repro_status": repro_status,
        "complete": bool(match["schema_pinned"] and match["capture_verified"]
                         and match["version_qualified"] and repro_supported
                         and repro_status == "ready"),
        "padding_semantics": entry["padding_semantics"],
    }


def _receipted(payload: dict[str, Any], limit: int,
               optional: tuple[str, ...] = ()) -> dict[str, Any]:
    """Attach a receipt after assembling the complete envelope.

    ``optional`` keys are dropped in order until the whole serialized object
    (receipt included) fits, so the advertised estimate is measured on exactly
    the bytes that are returned.
    """
    body = bounded_mapping(payload, "receipt")
    pending = list(optional)
    while True:
        body.pop("receipt", None)
        estimate = estimate_tokens(body)
        candidate = {**body, "receipt": {
            "tokenizer": TOKENIZER_ID, "token_estimate": estimate,
            "token_limit": int(limit), "within_budget": True}}
        full = estimate_tokens(candidate)
        candidate["receipt"]["within_budget"] = full <= int(limit)
        if full <= int(limit) or not pending:
            return candidate
        body.pop(pending.pop(0), None)


def _span_name(index: Mapping[str, Any], span: Any) -> str:
    try:
        target = (int(span[0]), int(span[1]))
    except (TypeError, ValueError, IndexError, KeyError):
        raise ProfilerUsageError("invalid catalog span") from None
    for name, candidate in index["spans"].items():
        if tuple(candidate) == target:
            return name
    raise ProfilerUsageError("no operator occupies that catalog span")


def resolve_op_abi_catalog_span(
    span: Any = None, *, op: str | None = None,
    op_name: str | None = None, catalog_sha256_16: str | None = None,
    catalog_sha256: str | None = None, path: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve a compact MCP continuation to the full catalog constraints."""
    index = _index(path)
    digest = catalog_sha256 or catalog_sha256_16
    if digest is not None:
        full_digest = index["sha256"].removeprefix("sha256:")
        text = str(digest).removeprefix("sha256:")
        if full_digest[:len(text)] != text:
            raise ProfilerUsageError("catalog digest does not match the span")
    if span is None:
        raw = str(op or op_name or "")
        name, _, reason = _resolve_name(index, raw)
        if name is None:
            raise ProfilerUsageError(f"operator not catalogued: {raw!r} ({reason})")
        span = index["spans"][name]
    else:
        name = _span_name(index, span)
    entry = _entry(index, name)
    reference = _catalog_reference(index, name)
    return {"schema": CARD_SCHEMA, "api": name,
            "abi_id": entry.get("abi_id"), "artifact": reference,
            "span": reference["span"], "entry": entry,
            "constraints": entry.get("c_abi_slots"),
            "padding_semantics": entry.get("padding_semantics")}


def inspect_op_abi(op_name: str | None = None, *,
                   cann_version: str | None = None, span: Any = None,
                   catalog_sha256_16: str | None = None,
                   path: str | Path | None = None) -> dict[str, Any]:
    """Return the complete direct-call ABI card plus its catalog continuation."""
    if span is not None:
        resolved = resolve_op_abi_catalog_span(
            span, catalog_sha256_16=catalog_sha256_16, path=path)
        op_name = resolved["api"]
    match = catalog_operator(str(op_name or ""), cann_version=cann_version,
                             path=path)
    if match is None:
        raise ProfilerUsageError(f"operator not catalogued: {op_name!r}")
    if cann_version is not None and not match["version_supported"]:
        raise ProfilerUsageError(
            f"{match['name']} is not declared for CANN {cann_version}; "
            f"declared: {', '.join(match['versions']) or 'none'}")
    entry = match["entry"]
    index = _index(path)
    digests = [source.get("sha256") for source in entry.get("sources") or ()
               if source.get("sha256")]
    card = _full_card(match)
    payload = {
        "schema": CARD_SCHEMA, "card": card,
        "identity": {"match": match["match"],
                     "source_sha256": digests[:1],
                     "requested_version": cann_version,
                     "version_supported": match["version_supported"]},
        "artifact": _catalog_reference(index, match["name"]),
    }
    return _receipted(payload, DIRECT_CARD_LIMIT)


def catalog_entry(op_name: str, *, path: str | Path | None = None
                  ) -> dict[str, Any] | None:
    """Return one entry by exact name/alias without a version gate (metrics)."""
    index = _index(path)
    canonical, _, _ = _resolve_name(index, _text(op_name))
    return None if canonical is None else _entry(index, canonical)


def catalog_summary(path: str | Path | None = None) -> dict[str, Any]:
    doc = load_catalog(path)
    families: dict[str, int] = {}
    surfaces: dict[str, int] = {}
    modes: dict[str, int] = {}
    pinned = 0
    for entry in doc["operators"].values():
        families[entry["family"]] = families.get(entry["family"], 0) + 1
        surfaces[entry["surface"]] = surfaces.get(entry["surface"], 0) + 1
        mode = entry["padding_semantics"]["mode"]
        modes[mode] = modes.get(mode, 0) + 1
        pinned += int(bool(entry["c_abi_slots"].get("pinned")))
    return {"schema": doc["schema"], "cann_versions": doc["cann_versions"],
            "operator_count": len(doc["operators"]), "pinned_signatures": pinned,
            "families": families, "surfaces": surfaces, "padding_modes": modes}


MCP_TOOL_SPECS = (
    {
        "name": "inspect_op_abi",
        "description": "Inspect an Ascend operator C-ABI signature and slot contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "op_name": {"type": "string", "description": "Operator or kernel name."},
                "cann_version": {"type": "string", "description": "CANN release tag."},
                "span": {
                    "type": "array", "minItems": 2, "maxItems": 2,
                    "items": {"type": "integer"},
                    "description": "Slot range [start, end).",
                },
                "catalog_sha256_16": {"type": "string", "description": "16-hex catalog digest."},
                "page": {"type": "integer", "minimum": 0, "description": "Catalog page index."},
                "cursor": {"type": "integer", "minimum": 0, "description": "Pagination cursor."},
                "slot_offset": {"type": "integer", "minimum": 0, "description": "Starting slot index."},
            },
            "required": [], "additionalProperties": False,
        },
    },
)


def call_mcp_tool(name: str, arguments: Any = None) -> dict[str, Any]:
    from .token_budget import bounded_envelope
    if name == "repro_op":
        from .repro_op import call_mcp_tool as repro_tool
        return repro_tool(name, arguments)
    args = bounded_mapping(arguments) if arguments is not None else {}
    if name == "inspect_op_abi":
        continuation = args.get("span") or args.get("catalog_span")
        if continuation is not None:
            resolved = resolve_op_abi_catalog_span(
                continuation,
                catalog_sha256_16=args.get("catalog_sha256_16"))
            return span_page(
                resolved["api"], resolved["artifact"], resolved["entry"],
                args.get("page", args.get("cursor",
                                         args.get("slot_offset", 0))))
        name = str(args.get("op_name") or "")
        match = catalog_operator(name, cann_version=args.get("cann_version"))
        if match is None:
            raise ProfilerUsageError(f"operator not catalogued: {name!r}")
        index = _index()
        card = _full_card(match)
        envelope = {
            "schema": CARD_SCHEMA, "api": match["name"],
            "abi_id": match["abi_id"], "signature": card["signature"],
            "schema_pinned": card["schema_pinned"],
            "capture_verified": card["capture_verified"],
            "version_qualified": card["version_qualified"],
            "qualification_state": card["qualification_state"],
            "release_basis": match["release_basis"],
            "complete": card["complete"],
            "padding": card["padding"],
            "repro_supported": card["repro_supported"],
            "repro_status": card["repro_status"],
            "artifact": _catalog_reference(index, match["name"]),
        }
        bounded = bounded_envelope(envelope, limit=MCP_TOKEN_LIMIT)
        if estimate_tokens(bounded) > MCP_TOKEN_LIMIT - 4:
            envelope.pop("complete", None)
            bounded = bounded_envelope(envelope, limit=MCP_TOKEN_LIMIT)
        return bounded
    raise ProfilerUsageError(f"unknown profiler tool: {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mindie-profiler inspect-op",
        description="Inspect a pinned Ascend operator ABI card or summarize the ABI catalog.",
        allow_abbrev=False,
    )
    parser.add_argument("op_name", nargs="?", help="operator API or kernel name to inspect (omit with --list)")
    parser.add_argument("--version", default=None, help="CANN release version to check qualification against")
    parser.add_argument("--list", action="store_true", help="summarize catalogued operator families and padding modes")
    parser.add_argument("--output", "-o", default=None, help="write JSON card or summary to path instead of stdout")
    args = parser.parse_args(list(argv or ()))
    payload = (catalog_summary() if args.list or not args.op_name
               else inspect_op_abi(args.op_name, cann_version=args.version))
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0


__all__ = [
    "BINDING_SCHEMA", "CARD_SCHEMA", "CARD_TOKEN_LIMIT", "CATALOG_SCHEMA",
    "DIRECT_CARD_LIMIT", "MCP_TOKEN_LIMIT",
    "MCP_TOOL_SPECS", "bind_captured_occurrence", "call_mcp_tool",
    "catalog_entry", "catalog_operator", "catalog_summary", "inspect_op_abi",
    "load_catalog", "main", "operator_names",
    "resolve_op_abi_catalog_span",
]


if __name__ == "__main__":
    raise SystemExit(main())
