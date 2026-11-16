"""Process-wide registry for temporary test workspaces.

[Role]
  Create short-root and probe workspaces that are always reclaimed, including
  when an assertion, timeout, or interrupt skips a test's own ``finally``.

[Invariants]
  * Every path is absolute once registered; release is idempotent.
  * Cleanup removes only registered roots and never follows a symlink out of
    one; ``atexit`` drains the registry for non-pytest callers as well.
  * A released root is never re-registered by cleanup itself.

[Timeouts & Locks]
  One process-local ``RLock`` around the registry; no timers or sleeps.

[Side-Effect Policy]
  Writes only directories created under the caller-selected base.
"""

from __future__ import annotations

import atexit
import os
from pathlib import Path
import shutil
import tempfile
import threading

_LOCK = threading.RLock()
_LIVE: set[str] = set()


def register_temp_workspace(path: str | os.PathLike[str]) -> Path:
    """Track ``path`` so fixture and ``atexit`` cleanup both remove it."""

    absolute = os.path.abspath(os.fspath(path))
    with _LOCK:
        _LIVE.add(absolute)
    return Path(absolute)


def make_temp_workspace(
    prefix: str,
    *,
    base: str | os.PathLike[str] | None = None,
) -> Path:
    """Create and register a fresh temporary directory."""

    return register_temp_workspace(tempfile.mkdtemp(prefix=prefix, dir=base))


def release_temp_workspace(path: str | os.PathLike[str]) -> None:
    """Forget and remove one workspace; missing paths are already released."""

    absolute = os.path.abspath(os.fspath(path))
    with _LOCK:
        _LIVE.discard(absolute)
    shutil.rmtree(absolute, ignore_errors=True)


def release_all_temp_workspaces() -> int:
    """Remove every registered workspace and return the reclaimed count."""

    with _LOCK:
        paths = sorted(_LIVE, key=len, reverse=True)
        _LIVE.clear()
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)
    return len(paths)


def live_temp_workspaces() -> tuple[str, ...]:
    with _LOCK:
        return tuple(sorted(_LIVE))


atexit.register(release_all_temp_workspaces)
