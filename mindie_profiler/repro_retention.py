"""Bounded retention for the reproducer short root (CAS and diff slots).

[Role]
  Evict expired or excess ``<sha>/repro.py`` + ``manifest.json`` pairs and
  ``diff/<id>/diff.json`` slots from the content-addressed short root so a
  long-lived ``/tmp/mprof`` never grows without bound.

[Invariants]
  * At most ``max_entries`` slots per kind survive; entries older than
    ``max_age_days`` are evicted regardless of count.
  * A symlinked or reparse-point ``<root>``/``<root>/diff`` is refused; such
    candidates and leaves are never traversed or deleted.
  * Every leaf is validated as a regular, non-reparse file before anything is
    unlinked; an unexpected payload keeps the whole slot.
  * Active state is never touched: commit-registry inodes, registered/active
    slots, lock-marked or write-marked entries, and unexpected payloads stay.
  * Eviction atomically renames the slot to a private ``.trash-*`` sibling
    while both locks are held, then unlinks only pre-validated regular leaves.
  * Writers publish a private ``.<slot>.write-*`` marker under the
    cross-process lock for the whole leaf write; stale markers are swept.
  * Leftover ``.trash-*`` siblings with a known payload shape are swept.

[Timeouts & Locks]
  The shared process-local ownership lock plus a non-blocking ``flock``/
  ``msvcrt`` lock on ``<root>/.retention.lock`` guard every eviction.  Writers
  hold that OS lock only while creating their write marker, so no lock spans a
  read, a leaf write, or a directory walk; contention skips eviction.

[Side-Effect Policy]
  Removes only expired/excess slots and their private trash siblings inside the
  selected short root.  Network, caller output paths, and the index leaf are
  never mutated.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import os
from pathlib import Path
import stat
import time
import uuid

from .storage_locks import exclusive_lock

PRUNE_MAX_ENTRIES = 64
PRUNE_MAX_AGE_DAYS = 14.0
_SECONDS_PER_DAY = 86400.0
_CAS_LEAVES = ("repro.py", "manifest.json")
_DIFF_DIRECTORY = "diff"
_DIFF_LEAVES = ("diff.json",)
_RETENTION_LOCK_NAME = ".retention.lock"
_TRASH_PREFIX = ".trash-"
_WRITE_MARKER_INFIX = ".write-"
_STALE_WRITE_MARKER_S = 3600.0
_REPARSE_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_symlink_or_reparse(info: os.stat_result, path: Path | None = None) -> bool:
    """Detect POSIX symlinks and Windows reparse points/junctions."""

    if stat.S_ISLNK(info.st_mode):
        return True
    if bool(getattr(info, "st_reparse_tag", 0)):
        return True
    if int(getattr(info, "st_file_attributes", 0) or 0) & _REPARSE_ATTRIBUTE:
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is None or path is None:
        return False
    try:
        return bool(isjunction(path))
    except TimeoutError:
        raise
    except (OSError, ValueError):
        return False


def _safe_directory(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except TimeoutError:
        raise
    except OSError:
        return False
    return stat.S_ISDIR(info.st_mode) and not _is_symlink_or_reparse(info, path)


def _live_registered() -> set[Path]:
    return {Path(str(entry.get(key))).parent
            for entry in repro_storage._REGISTRY.values()
            for key in ("artifact_path", "manifest_path") if entry.get(key)}


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


def _entry_locked(entry: Path) -> bool:
    markers = (entry / ".lock", entry.with_name(f".{entry.name}.lock"))
    if any(repro_storage.path_lexists(marker) for marker in markers):
        return True
    try:
        children = list(entry.parent.iterdir())
    except TimeoutError:
        raise
    except OSError:
        return True
    prefix = f".{entry.name}{_WRITE_MARKER_INFIX}"
    return any(child.name.startswith(prefix) for child in children)


def _validated_leaves(entry: Path, leaves: tuple[str, ...]
                      ) -> dict[Path, tuple[int, int]] | None:
    """Return leaf inode receipts only for a closed set of regular files."""

    try:
        names = {child.name for child in entry.iterdir()}
    except TimeoutError:
        raise
    except OSError:
        return None
    if not names or not names <= set(leaves):
        return None
    receipts: dict[Path, tuple[int, int]] = {}
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
            return None
        if not stat.S_ISREG(info.st_mode) or _is_symlink_or_reparse(info, path):
            return None
        receipts[path] = (info.st_dev, info.st_ino)
    return receipts or None


def _remove_trash(trash: Path, leaves: tuple[str, ...],
                  expected: dict[Path, tuple[int, int]] | None = None) -> int:
    """Unlink only re-validated regular leaves, then the empty trash directory."""

    receipts = _validated_leaves(trash, leaves)
    if receipts is None:
        return 0
    if expected is not None and set(receipts.values()) != set(expected.values()):
        return 0
    for path in receipts:
        try:
            path.unlink()
        except TimeoutError:
            raise
        except OSError:
            return 0
    try:
        trash.rmdir()
    except TimeoutError:
        raise
    except OSError:
        return 0
    return 1


def _sweep_trash(base: Path, leaves: tuple[str, ...]) -> int:
    try:
        children = list(base.glob(f"{_TRASH_PREFIX}*"))
    except TimeoutError:
        raise
    except OSError:
        return 0
    return sum(_remove_trash(child, leaves) for child in children)


def _evict_entry(base: Path, entry: Path, leaves: tuple[str, ...]) -> int:
    """Re-check live state and atomically detach one slot before unlinking it."""

    with repro_storage._LOCK:
        with exclusive_lock(base / _RETENTION_LOCK_NAME, blocking=False) as locked:
            if not locked or _entry_locked(entry):
                return 0
            resolved = repro_storage._resolved(entry)
            if resolved is None:
                return 0
            slots = set(repro_storage._SLOTS)
            if (resolved in slots or resolved in _live_registered()
                    or repro_storage._in_registered_subtree(resolved, slots)):
                return 0
            receipts = _validated_leaves(entry, leaves)
            if receipts is None:
                return 0
            if set(receipts.values()) & repro_storage._PROTECTED_INODES:
                return 0
            trash = base / f"{_TRASH_PREFIX}{entry.name}-{uuid.uuid4().hex[:8]}"
            try:
                os.replace(entry, trash)
            except TimeoutError:
                raise
            except OSError:
                return 0
    return _remove_trash(trash, leaves, receipts)


def _sweep_write_markers(children: list[Path], now: float) -> None:
    """Drop markers left by a killed writer so its slot can become eligible."""

    for child in children:
        if _WRITE_MARKER_INFIX not in child.name:
            continue
        try:
            if now - os.lstat(child).st_mtime <= _STALE_WRITE_MARKER_S:
                continue
            child.unlink()
        except TimeoutError:
            raise
        except OSError:
            continue


def _prune_kind(base: Path, leaves: tuple[str, ...], *, limit: int, max_age_s: float,
                slots: set[Path], registered: set[Path], now: float) -> int:
    if not _safe_directory(base):
        return 0
    try:
        children = list(base.iterdir())
    except TimeoutError:
        raise
    except OSError:
        return 0
    _sweep_write_markers(children, now)
    candidates: list[tuple[float, Path]] = []
    for entry in children:
        if entry.name in {repro_storage._INDEX_NAME, _DIFF_DIRECTORY} \
                or entry.name.startswith(_TRASH_PREFIX) or _entry_locked(entry):
            continue
        try:
            info = os.lstat(entry)
        except TimeoutError:
            raise
        except OSError:
            continue
        if not stat.S_ISDIR(info.st_mode) or _is_symlink_or_reparse(info, entry):
            continue
        resolved = repro_storage._resolved(entry)
        if resolved is None or resolved in slots or resolved in registered \
                or repro_storage._in_registered_subtree(resolved, slots):
            continue
        if _validated_leaves(entry, leaves) is None:
            continue
        age = _entry_age_seconds(entry, leaves, now)
        if age is not None:
            candidates.append((age, entry))
    candidates.sort(key=lambda item: item[0])  # Newest first; age only grows.
    removed = _sweep_trash(base, leaves)
    for index, (age, entry) in enumerate(candidates):
        if age <= max_age_s and index < limit:
            continue
        removed += _evict_entry(base, entry, leaves)
    return removed


@contextlib.contextmanager
def retention_write_guard(entry: Path) -> Iterator[None]:
    """Publish a per-write marker so eviction skips an in-flight slot.

    The marker is created under the cross-process retention lock, which eviction
    holds for its whole re-check/rename section.  The lock is released before
    the caller writes leaves, so readers and concurrent writers never block on
    it; the marker alone keeps the slot ineligible until ``_remember_inodes``
    has protected the committed inodes.
    """

    base = entry.parent
    try:
        base.mkdir(parents=True, exist_ok=True)
    except TimeoutError:
        raise
    except OSError:
        pass
    marker = entry.with_name(
        f".{entry.name}{_WRITE_MARKER_INFIX}{os.getpid()}-{uuid.uuid4().hex[:8]}")
    if not _safe_directory(base):
        yield
        return
    with exclusive_lock(base / _RETENTION_LOCK_NAME, blocking=True):
        try:
            handle = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                             stat.S_IRUSR | stat.S_IWUSR)
        except TimeoutError:
            raise
        except OSError:
            handle = None
        if handle is not None:
            try:
                os.close(handle)
            except TimeoutError:
                raise
            except OSError:
                pass
    try:
        yield
    finally:
        try:
            marker.unlink(missing_ok=True)
        except TimeoutError:
            raise
        except OSError:
            pass


def prune_repro_storage(root: str | Path | None = None, *, max_entries: int = PRUNE_MAX_ENTRIES,
                        max_age_days: float = PRUNE_MAX_AGE_DAYS) -> int:
    """Evict expired/excess CAS and diff slots; return the removed slot count."""

    base = Path(root).expanduser() if root is not None else repro_storage.short_root()
    if not _safe_directory(base):
        return 0
    limit, now = max(0, int(max_entries)), time.time()
    max_age_s = max(0.0, float(max_age_days)) * _SECONDS_PER_DAY
    with repro_storage._LOCK:
        slots = set(repro_storage._SLOTS)
        registered = _live_registered()
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


__all__ = ["PRUNE_MAX_AGE_DAYS", "PRUNE_MAX_ENTRIES", "opportunistic_prune",
           "prune_repro_storage", "retention_write_guard"]

# Deliberately last: ``repro_storage`` re-exports ``prune_repro_storage``, and
# binding the module object here (never its attributes) makes both import
# orders safe without a duplicate storage state machine.
from . import repro_storage  # noqa: E402  (see comment above)
