"""Caller-supplied evidence roots for the structure examples.

[Role] Resolve capture/workstream evidence roots from the caller's environment
  so no developer-local path is compiled into the repository.
[Invariants] An unenrolled root resolves to a deterministic absent absolute
  path; this module never guesses a machine layout and never creates a root.
[Timeouts & Locks] Pure environment lookup; no I/O and no locks.
[Side-Effect Policy] Read-only environment access.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Environment variables enrolling the local capture tree and workstream tree.
CAPTURE_ROOT_ENV = "MINDIE_SIM_DATA_ROOT"
WORKSTREAM_ROOT_ENV = "MINDIE_WORKSTREAM_ROOT"
#: Deterministic absent roots used when the caller has not enrolled a tree.
ABSENT_CAPTURE_ROOT = "/nonexistent/mindie-sim-data"
ABSENT_WORKSTREAM_ROOT = "/nonexistent/mindie-agent-workstreams"
#: ``parents[2]`` from ``examples/structure/`` is the repository root.
REPO_ROOT_PARENTS = 2
#: Offset from a matched URI prefix to the first relative-path character.
NEXT_CHAR_OFFSET = 1


def capture_root() -> Path:
    """Local root of the ``capture://mindie-sim-data`` evidence tree."""
    return Path(os.environ.get(CAPTURE_ROOT_ENV) or ABSENT_CAPTURE_ROOT)


def workstream_root() -> Path:
    """Local root of the ``repository://mindie-agent/.workstreams`` tree."""
    return Path(os.environ.get(WORKSTREAM_ROOT_ENV) or ABSENT_WORKSTREAM_ROOT)


def localize_evidence(value, *, capture_base=None):
    """Resolve stored ``capture://`` / ``repository://`` URIs in memory."""
    if isinstance(value, dict):
        return {
            key: localize_evidence(item, capture_base=capture_base)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            localize_evidence(item, capture_base=capture_base)
            for item in value
        ]
    if isinstance(value, tuple):
        return tuple(
            localize_evidence(item, capture_base=capture_base)
            for item in value
        )
    if not isinstance(value, str) or not value.startswith(
        ("capture:", "repository:")
    ):
        return value

    roots = (
        (
            "capture", "mindie-sim-data",
            Path(capture_base) if capture_base is not None else capture_root(),
        ),
        ("repository", "mindie-agent/.workstreams", workstream_root()),
        (
            "repository", "mindie-agent/profiler",
            Path(__file__).resolve().parents[REPO_ROOT_PARENTS],
        ),
    )
    for scheme, authority, root in roots:
        for separator in ("://", ":/"):
            prefix = scheme + separator + authority
            if value == prefix:
                return str(root.resolve())
            if value.startswith(prefix + "/"):
                return str((root / value[len(prefix) + NEXT_CHAR_OFFSET:]).resolve())
    return value
