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


def capture_root() -> Path:
    """Local root of the ``capture://mindie-sim-data`` evidence tree."""
    return Path(os.environ.get(CAPTURE_ROOT_ENV) or ABSENT_CAPTURE_ROOT)


def workstream_root() -> Path:
    """Local root of the ``repository://mindie-agent/.workstreams`` tree."""
    return Path(os.environ.get(WORKSTREAM_ROOT_ENV) or ABSENT_WORKSTREAM_ROOT)
