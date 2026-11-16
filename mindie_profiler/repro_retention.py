"""Bounded retention for the reproducer short root (CAS and diff slots).

[Role]
  Evict expired or excess ``<sha>/repro.py`` + ``manifest.json`` pairs and
  ``diff/<id>/diff.json`` slots from the content-addressed short root so a
  long-lived ``/tmp/mprof`` never grows without bound.

[Invariants]
  * At most ``max_entries`` slots per kind survive; entries older than
    ``max_age_days`` are evicted regardless of count.
  * Active state is never touched: inodes in the process commit registry
    (``repro_storage._PROTECTED_INODES``, the committed component of
    ``_protected_inodes()``), registered/active slots, lock-marked entries,
    symbolic links, and directories holding an unexpected payload stay.
  * Eviction unlinks only known regular leaves and then an empty directory;
    every filesystem ``OSError`` is best effort and never fails a delivery.

[Timeouts & Locks]
  Registry/slot snapshots are taken under the shared process-local ownership
  lock; commit-registry membership is re-checked under that lock immediately
  before each unlink.  No lock spans a read or a directory walk.

[Side-Effect Policy]
  Removes only expired/excess slots inside the selected short root.  Network,
  caller output paths, and the index leaf are never mutated.
"""

from __future__ import annotations

import os
from pathlib import Path
import stat
import time

PRUNE_MAX_ENTRIES = 64
PRUNE_MAX_AGE_DAYS = 14.0
_SECONDS_PER_DAY = 86400.0
_CAS_LEAVES = ("repro.py", "manifest.json")
_DIFF_DIRECTORY = "diff"
_DIFF_LEAVES = ("diff.json",)


def _entry_age_seconds(entry: Path, leaves: tuple[str, ...], now: float) -> float | None:
    newest = None
    for name in leaves:
        try:
            info = os.lstat(entry / name)
        except FileNotFoundError:
            continue
        except TimeoutError:
            raise
        except OSError:
            continue
        if stat.S_ISREG(info.st_mode):
            newest = info.st_mtime if newest is None else max(newest, info.st_mtime)
    if newest is None:
        try:
            newest = os.lstat(entry).st_mtime
        except TimeoutError:
            raise
        except OSError:
            return None
    return max(0.0, now - newest)


def _entry_inodes(entry: Path, leaves: tuple[str, ...]) -> set[tuple[int, int]]:
    return {inode for inode in (repro_storage._inode_of(entry / name) for name in leaves) if inode}


def _entry_locked(entry: Path) -> bool:
    markers = (entry / ".lock", entry.with_name(f".{entry.name}.lock"))
    return any(repro_storage.path_lexists(marker) for marker in markers)


def _remove_pruned_entry(entry: Path, leaves: tuple[str, ...]) -> int:
    """Unlink only known regular leaves, then the now-empty directory."""

    try:
        names = {child.name for child in entry.iterdir()}
    except TimeoutError:
        raise
    except OSError:
        return 0
    if not names or not names <= set(leaves):
        return 0
    for name in leaves:
        if name not in names:
            continue
        path = entry / name
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            continue
        except TimeoutError:
            raise
        except OSError:
            return 0
        if not stat.S_ISREG(info.st_mode):
            return 0
        try:
            path.unlink()
        except TimeoutError:
            raise
        except OSError:
            return 0
    try:
        entry.rmdir()
    except TimeoutError:
        raise
    except OSError:
        return 0
    return 1


def _prune_kind(base: Path, leaves: tuple[str, ...], *, limit: int, max_age_s: float,
                slots: set[Path], registered: set[Path], now: float) -> int:
    try:
        children = list(base.iterdir())
    except TimeoutError:
        raise
    except OSError:
        return 0
    candidates: list[tuple[float, Path]] = []
    for entry in children:
        if entry.name in {repro_storage._INDEX_NAME, _DIFF_DIRECTORY} or _entry_locked(entry):
            continue
        try:
            info = os.lstat(entry)
        except TimeoutError:
            raise
        except OSError:
            continue
        if not stat.S_ISDIR(info.st_mode):
            continue
        resolved = repro_storage._resolved(entry)
        if resolved is None or resolved in slots or resolved in registered \
                or repro_storage._in_registered_subtree(resolved, slots):
            continue
        age = _entry_age_seconds(entry, leaves, now)
        if age is not None:
            candidates.append((age, entry))
    candidates.sort(key=lambda item: item[0])  # Newest first; age only grows.
    removed = 0
    for index, (age, entry) in enumerate(candidates):
        if age <= max_age_s and index < limit:
            continue
        with repro_storage._LOCK:
            if _entry_inodes(entry, leaves) & repro_storage._PROTECTED_INODES:
                continue
        removed += _remove_pruned_entry(entry, leaves)
    return removed


def prune_repro_storage(root: str | Path | None = None, *, max_entries: int = PRUNE_MAX_ENTRIES,
                        max_age_days: float = PRUNE_MAX_AGE_DAYS) -> int:
    """Evict expired/excess CAS and diff slots; return the removed slot count."""

    base = Path(root).expanduser() if root is not None else repro_storage.short_root()
    limit, now = max(0, int(max_entries)), time.time()
    max_age_s = max(0.0, float(max_age_days)) * _SECONDS_PER_DAY
    with repro_storage._LOCK:
        slots = set(repro_storage._SLOTS)
        registered = {Path(str(entry.get(key))).parent
                      for entry in repro_storage._REGISTRY.values()
                      for key in ("artifact_path", "manifest_path") if entry.get(key)}
    removed = _prune_kind(base, _CAS_LEAVES, limit=limit, max_age_s=max_age_s,
                          slots=slots, registered=registered, now=now)
    removed += _prune_kind(base / _DIFF_DIRECTORY, _DIFF_LEAVES, limit=limit, max_age_s=max_age_s,
                           slots=slots, registered=registered, now=now)
    return removed


def opportunistic_prune() -> None:
    """Write-path retention hook; a filesystem ``OSError`` never fails the write."""

    try:
        prune_repro_storage()
    except TimeoutError:
        raise
    except OSError:
        pass


__all__ = ["PRUNE_MAX_AGE_DAYS", "PRUNE_MAX_ENTRIES", "opportunistic_prune", "prune_repro_storage"]

# Deliberately last: ``repro_storage`` re-exports ``prune_repro_storage``, and
# binding the module object here (never its attributes) makes both import
# orders safe without a duplicate storage state machine.
from . import repro_storage  # noqa: E402  (see comment above)
