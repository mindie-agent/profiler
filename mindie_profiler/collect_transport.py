"""Receipt reconciliation identities for online profile-window control.

[Role]
  Keep the transport-result reconciliation schema and the one shared
  ``unknown external effect`` projector used by ``collect``.

[Invariants]
  * A sent request whose acknowledgement was lost is always ``unknown`` and
    always carries a reconciliation identity; it is never retried blindly.
  * Message text is recorded verbatim; no outcome is inferred from it.

[Timeouts & Locks]
  Pure in-memory mapping updates; no I/O, locks or clocks.

[Side-Effect Policy]
  Mutates only the caller-owned result mapping.
"""
from __future__ import annotations

from typing import Any

RECONCILE_SCHEMA = "mindie-profile-reconcile/1"


def reconcile_identity(
    *, request_id: str, action: str, endpoint: str, execution_id: str,
    started_at: str,
) -> dict[str, Any]:
    """Describe the exact control request an operator must reconcile."""
    return {
        "schema_version": RECONCILE_SCHEMA,
        "request_id": request_id,
        "action": action,
        "endpoint": endpoint,
        "execution_id": execution_id,
        "started_at": started_at,
        "instruction": "inspect trace/output evidence before any further control request",
    }


def mark_unknown(
    result: dict[str, Any], *, code: str, message: str,
    request_id: str, action: str, endpoint: str, execution_id: str,
    started_at: str,
) -> None:
    """Record a sent request whose external effect was not acknowledged."""
    result.update({
        "status": "unknown", "sent": True, "external_effect": "unknown",
        "error": {"code": code, "message": message},
        "reconcile": reconcile_identity(
            request_id=request_id, action=action, endpoint=endpoint,
            execution_id=execution_id, started_at=started_at,
        ),
    })
