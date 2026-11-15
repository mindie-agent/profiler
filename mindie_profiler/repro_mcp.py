"""Bounded MCP receipt for single-op reproducer generation and resolution.

[Role]
  Validate the ``repro_op`` tool arguments, stage one generated reproducer under
  the bounded short root, expose exact retrievable paths plus the ``sha256:``
  handle, and resolve an existing handle on request.

[Invariants]
  * A receipt is emitted only after the script and manifest are both readable.
  * ``artifact_path``/``manifest_path`` are never truncated; long or omitted
    caller directories fall back to short-root paths.
  * ``resolve_artifact_id`` returns the same staged files without regenerating.
  * Resolution re-hashes the script and manifest; a mismatch or an
    unrepresentable path is a blocked delivery, never a trusted echo.
  * Unrepresentable paths use the single transition helper: both path keys are
    absent and ``artifact_path_omitted=True`` survives the final MCP wrapper.
  * A refused/malformed index write is reported as
    ``delivery_failed``/``index_persistence_failed`` with
    ``index_persisted=False``; it is never presented as an ordinary ready run.
  * The complete envelope stays within 250 estimated tokens.

[Timeouts & Locks]
  Pure in-memory generation plus synchronous short-root file writes; no device
  or subprocess work.

[Side-Effect Policy]
  Writes only artifact files under the short root or a short caller directory.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .events import ProfilerUsageError
from .repro_storage import file_artifact_id, resolve_repro_artifact
from .repro_values import diagnostic_value, bounded_mapping, binding_issues

REPRO_SCHEMA = "mindie-single-op-repro/2"
_ARTIFACT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")

MCP_TOOL_SPECS = (
    {
        "name": "repro_op",
        "description": "Synthesize or resolve a standalone single-operator NPU reproducer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "occurrence": {"type": "object", "description": "Captured operator row or bound ABI occurrence."},
                "resolve_artifact_id": {"type": "string", "description": "Existing sha256:<64-hex> artifact handle."},
                "output_dir": {"type": "string", "description": "Optional artifact store root directory."},
                "cann_version": {"type": "string", "description": "Optional CANN release for ABI binding."},
                "seed": {"type": "integer", "minimum": 0, "description": "Deterministic input RNG seed (default: 0)."},
                "warmup": {"type": "integer", "minimum": 0, "description": "Untimed warmup launches (default: 10)."},
                "iters": {"type": "integer", "minimum": 1, "description": "Timed launches per pass (default: 50)."},
            },
            "required": [], "additionalProperties": False,
        },
    },
)

_ALLOWED_REPRO_ARGS = frozenset(MCP_TOOL_SPECS[0]["inputSchema"]["properties"])


def _issue_summary(issue: Any) -> dict[str, Any]:
    """Bounded issue projection; long caller names/slots are shed whole."""
    from .token_budget import sanitize_code
    fallback = "invalid_occurrence_issue"
    issue = diagnostic_value(issue)
    if not isinstance(issue, dict):
        return {"code": sanitize_code(issue, fallback)}
    out: dict[str, Any] = {"code": sanitize_code(
        issue.get("code"), fallback)}
    for key in ("name", "slot"):
        value = issue.get(key)
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            if isinstance(value, str) and len(value) > 64:
                continue
            out[key] = value
        if len(out) >= 3:
            break
    return out


class _BoundedReceipt(dict):
    """Direct-call view: the redundant manifest digest aliases the identity.

    The canonical ``artifact_id`` is the only 64-byte digest serialized, so a
    bounded receipt does not pay twice for the same value.  Direct Python
    callers still receive ``repro_sha256`` when they index the receipt.
    """

    def __getitem__(self, key: Any) -> Any:
        if key == "repro_sha256" and dict.__contains__(self, "artifact_id"):
            return dict.__getitem__(self, "artifact_id")
        return dict.__getitem__(self, key)

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


def _alias_identity(envelope: dict[str, Any]) -> dict[str, Any]:
    return _BoundedReceipt(envelope)


def call_mcp_tool(name: str, arguments: Any = None) -> dict[str, Any]:
    from .op_api_registry import BINDING_SCHEMA, bind_captured_occurrence
    from .repro_op import generate_single_op_reproducer
    from .repro_values import _INT_RANGES, bounded_count, validate_container_depth
    from .token_budget import _TOKEN_LIMIT, bounded_envelope
    if name != "repro_op":
        raise ProfilerUsageError(f"unknown profiler tool: {name!r}")
    try:
        args = bounded_mapping(arguments, "repro_op arguments") if arguments is not None else {}
    except ProfilerUsageError as exc:
        return bounded_envelope({"schema": REPRO_SCHEMA, "status": "blocked",
                                 "reason": str(exc)}, limit=250, list_limit=8)
    unknown_keys = sorted(set(args) - _ALLOWED_REPRO_ARGS)
    if unknown_keys:
        return bounded_envelope({"schema": REPRO_SCHEMA, "status": "blocked",
                                 "reason": f"unexpected repro_op arguments: {unknown_keys}"},
                                limit=_TOKEN_LIMIT)
    if "resolve_artifact_id" in args:
        identifier = args.get("resolve_artifact_id")
        if (not isinstance(identifier, str)
                or _ARTIFACT_ID.fullmatch(identifier) is None):
            return bounded_envelope({
                "schema": REPRO_SCHEMA, "status": "invalid_request",
                "resolved": False, "retrievable": False,
                "artifact_id": None,
                "error": "invalid_artifact_id"}, limit=250, list_limit=8)
        resolved = resolve_repro_artifact(identifier)
        lean = {key: resolved[key] for key in (
            "schema", "artifact_id", "resolved", "retrievable",
            "artifact_path", "manifest_path", "error") if key in resolved}
        envelope = bounded_envelope(lean, limit=250, list_limit=8)
        if resolved.get("resolved") and (
                envelope.get("artifact_path_omitted")
                or envelope.get("status") == "delivery_blocked"
                or "artifact_path" not in envelope
                or "manifest_path" not in envelope):
            from .token_budget import omit_unrepresentable_paths
            blocked = omit_unrepresentable_paths({
                "schema": REPRO_SCHEMA, "status": "delivery_blocked",
                "resolved": False, "retrievable": False,
                "artifact_id": identifier,
                "artifact_path": resolved.get("artifact_path"),
                "manifest_path": resolved.get("manifest_path"),
                "error": "artifact_paths_not_representable"})
            return bounded_envelope(blocked, limit=250, list_limit=8)
        return _alias_identity(envelope)
    occurrence = args.get("occurrence")
    if not isinstance(occurrence, dict):
        return bounded_envelope({"schema": REPRO_SCHEMA, "status": "blocked",
                                 "reason": "repro_op requires an 'occurrence' object"},
                                limit=250, list_limit=8)
    warmup = args.get("warmup", 10)
    iters = args.get("iters", 50)
    seed = args.get("seed", 0)
    cann_version = args.get("cann_version")
    requested_dir = args.get("output_dir")
    prefer_short = not requested_dir or len(str(requested_dir)) > 48
    try:
        seed_val = bounded_count(seed, "seed", 0, _INT_RANGES["int64"][1])
        if cann_version is not None:
            if not isinstance(cann_version, str) or not cann_version.strip():
                raise ProfilerUsageError("cann_version must be a non-empty string")
            cann_version = cann_version.strip()
        if occurrence.get("schema") != BINDING_SCHEMA:
            validate_container_depth(occurrence)
            eff_version = cann_version or (
                str(occurrence.get("cann_version") or occurrence.get("cann_release") or "").strip() or None
            )
            occurrence = bind_captured_occurrence(occurrence, cann_version=eff_version)
        binding_issues(occurrence)
        result = generate_single_op_reproducer(
            occurrence,
            output_dir=(None if prefer_short else requested_dir),
            warmup=warmup, iters=iters, seed=seed_val,
            cann_version=cann_version, stage=True)
    except ProfilerUsageError as exc:
        issues = occurrence.get("issues")
        issues = issues if isinstance(issues, (list, tuple)) else []
        payload = {
            "schema": REPRO_SCHEMA, "status": "blocked",
            "reason": str(exc)[:900], "issue_count": len(issues),
            "issues": [_issue_summary(item) for item in issues[:8]],
        }
        if len(issues) > 8:
            payload["issues_truncated_count"] = len(issues) - 8
        return bounded_envelope(payload, limit=250, list_limit=8)
    storage = result.get("storage") or {}
    if storage.get("index_persisted") is False:
        return bounded_envelope({
            "schema": REPRO_SCHEMA,
            "status": result.get("status") or "delivery_failed",
            "error": "index_persistence_failed",
            "artifact_id": result["sha256"], "index_persisted": False,
            "index_warning": (storage.get("index_warning")
                              or "index_persistence_failed"),
            "retrievable": False}, limit=250, list_limit=8)
    if storage.get("status") in {"delivery_blocked", "delivery_failed"}:
        blocked = {
            "schema": REPRO_SCHEMA, "status": storage["status"],
            "reason": "artifact storage refused an unsafe destination",
            "error": storage.get("error") or "artifact_delivery_blocked",
            "artifact_id": result["sha256"],
            "artifact": {"sha256": result["sha256"], "retrievable": False},
        }
        if storage.get("protected_artifact_target"):
            blocked["protected_artifact_target"] = True
        return bounded_envelope(blocked, limit=250, list_limit=8)
    artifact_path = (storage.get("short_artifact_path")
                     if prefer_short else result.get("output_path"))
    manifest_path = (storage.get("short_manifest_path")
                     if prefer_short else result.get("manifest_path"))
    artifact_path = artifact_path or result.get("output_path")
    manifest_path = manifest_path or result.get("manifest_path")
    resolved = resolve_repro_artifact(result["sha256"])
    retrievable = (bool(storage.get("retrievable"))
                   and bool(resolved.get("retrievable")))
    if not retrievable and artifact_path and manifest_path:
        try:
            actual = file_artifact_id(artifact_path)
            loaded = json.loads(
                Path(str(manifest_path)).read_text(encoding="utf-8"))
            retrievable = bool(
                actual == result["sha256"] and isinstance(loaded, dict)
                and loaded.get("repro_sha256") == result["sha256"]
                and loaded.get("script_sha256",
                               result["sha256"]) == result["sha256"])
        except TimeoutError:
            raise
        except (OSError, TypeError, ValueError, UnicodeError):
            retrievable = False
    if not retrievable:
        return bounded_envelope({
            "schema": REPRO_SCHEMA, "status": "delivery_blocked",
            "reason": "artifact path and short-root staging are not retrievable",
            "artifact_id": result["sha256"],
            "artifact": {"sha256": result["sha256"], "retrievable": False},
        }, limit=250, list_limit=8)
    payload = {
        "schema": REPRO_SCHEMA, "status": result["status"],
        "artifact_id": result["sha256"],
        "artifact_path": artifact_path,
        "manifest_path": manifest_path,
        "artifact": {"retrievable": True, "inline_script_omitted": True},
    }
    envelope = bounded_envelope(payload, limit=250, list_limit=8)
    if (envelope.get("artifact_path_omitted")
            or "artifact_path" not in envelope
            or "manifest_path" not in envelope):
        from .token_budget import omit_unrepresentable_paths
        blocked = omit_unrepresentable_paths({
            "schema": REPRO_SCHEMA, "status": "delivery_blocked",
            "reason": "receipt identity cannot be represented within 250 tokens",
            "error": "artifact_paths_not_representable",
            "artifact_id": result["sha256"], "retrievable": False,
            "artifact_path": artifact_path, "manifest_path": manifest_path,
            "artifact": {"sha256": result["sha256"], "retrievable": False}})
        return bounded_envelope(blocked, limit=250, list_limit=8)
    if (envelope.get("status") != result["status"]
            or envelope.get("artifact_id") != result["sha256"]):
        return bounded_envelope({
            "schema": REPRO_SCHEMA, "status": "delivery_blocked",
            "reason": "receipt identity cannot be represented within 250 tokens",
            "error": "artifact_identity_truncated",
            "artifact_id": result["sha256"], "retrievable": False,
            "artifact_path": artifact_path, "manifest_path": manifest_path,
            "artifact": {"sha256": result["sha256"], "retrievable": False},
        }, limit=250, list_limit=8)
    return _alias_identity(envelope)


__all__ = ["MCP_TOOL_SPECS", "call_mcp_tool"]
