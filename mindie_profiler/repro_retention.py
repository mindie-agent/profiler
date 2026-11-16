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
    while both locks are held, then unlinks only pre-validated regular leaves;
    a ``.trash-*`` sibling that is itself a symlink or reparse point is never
    traversed.
  * Writers publish a private ``.write-<slot>-*`` marker holding an exclusive
    OS lock for the whole delivery; a marker is swept only when it is stale and
    its lock is provably free.  A written or reused slot also holds a shared
    ``.pin-<slot>.lock`` lease through registration and leaves its PID behind;
    a slot with a held lock or a live PID lease is never evicted.
  * Leftover ``.trash-*`` siblings with a known payload shape are swept.

[Timeouts & Locks]
  The shared process-local ownership lock plus a non-blocking ``flock``/
  ``msvcrt`` lock on ``<root>/.retention.lock`` guard every eviction.  Writers
  hold that OS lock only while creating their locked write marker and pin, so
  no lock spans a read, a leaf write, or a directory walk; contention skips
  eviction.  Marker age alone never proves a writer dead.

[Side-Effect Policy]
  Removes only expired/excess slots and their private trash siblings inside the
  selected short root.  Network, caller output paths, and the index leaf are
  never mutated.
"""

from __future__ import annotations

import atexit
from collections.abc import Iterator
import contextlib
import os
from pathlib import Path
import stat
import threading
import time
import uuid

from .repro_atomic_io import unlink_quiet
from .storage_locks import (
    close_lock_fd,
    exclusive_lock,
    open_lock_file,
    process_exited,
    try_lock_fd,
    unlock_fd,
)

PRUNE_MAX_ENTRIES = 64
PRUNE_MAX_AGE_DAYS = 14.0
_SECONDS_PER_DAY = 86400.0
_CAS_LEAVES = ("repro.py", "manifest.json")
_DIFF_DIRECTORY = "diff"
_DIFF_LEAVES = ("diff.json",)
_SLOT_LEAVES = _CAS_LEAVES + _DIFF_LEAVES
_RETENTION_LOCK_NAME = ".retention.lock"
_TRASH_PREFIX = ".trash-"
_WRITE_MARKER_INFIX = ".write-"
_PIN_MARKER_PREFIX = ".pin-"
_LOCK_SUFFIX = ".lock"
_STALE_WRITE_MARKER_S = 3600.0
_REPARSE_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_PINS: dict[tuple[str, str], int] = {}
_PIN_LOCK = threading.Lock()


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
    prefixes = (f"{_WRITE_MARKER_INFIX}{entry.name}-",
                f".{entry.name}{_WRITE_MARKER_INFIX}")
    return any(child.name.startswith(prefixes) for child in children)


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


def _pin_path(entry: Path) -> Path:
    return entry.with_name(f"{_PIN_MARKER_PREFIX}{entry.name}{_LOCK_SUFFIX}")


def _pin_key(entry: Path) -> tuple[str, str]:
    try:
        base = str(entry.parent.resolve())
    except TimeoutError:
        raise
    except (OSError, RuntimeError):
        base = os.path.abspath(entry.parent)
    return base, entry.name


def _close_lock(fd: int) -> None:
    try:
        unlock_fd(fd)
    finally:
        close_lock_fd(fd)


def _hold_pin(entry: Path) -> None:
    """Cache one shared OS lease so eviction skips a live slot."""

    key = _pin_key(entry)
    with _PIN_LOCK:
        if key in _PINS:
            return
        while len(_PINS) >= PRUNE_MAX_ENTRIES:
            _close_lock(_PINS.pop(next(iter(_PINS))))
        fd = open_lock_file(_pin_path(entry), append=True)
        if fd is None:
            return
        if not try_lock_fd(fd, exclusive=False):
            close_lock_fd(fd)
            return
        _PINS[key] = fd


def _drop_pin(entry: Path) -> None:
    with _PIN_LOCK:
        fd = _PINS.pop(_pin_key(entry), None)
    if fd is not None:
        _close_lock(fd)


def _lease_pids(fd: int) -> list[int]:
    try:
        size = os.fstat(fd).st_size
        os.lseek(fd, 0, os.SEEK_SET)
        limit = min(size, int(_STALE_WRITE_MARKER_S))
        data = os.read(fd, limit) if limit else b""
    except TimeoutError:
        raise
    except OSError:
        return []
    pids = []
    for part in data.replace(b"\0", b" ").split():
        if part.isdigit():
            try:
                pids.append(int(part))
            except ValueError:
                continue
    return pids


def _rewrite_lease(fd: int, pids: list[int]) -> None:
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        if pids:
            os.write(fd, "".join(f"{pid}\n" for pid in pids).encode("ascii"))
    except TimeoutError:
        raise
    except OSError:
        pass


def _append_lease(entry: Path) -> None:
    fd = open_lock_file(_pin_path(entry), append=True)
    if fd is None:
        return
    try:
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
    except TimeoutError:
        raise
    except OSError:
        pass
    finally:
        close_lock_fd(fd)


def _seal_pin(entry: Path) -> None:
    """Hand a held shared OS lock off to a PID lease, then release the lock."""

    key = _pin_key(entry)
    with _PIN_LOCK:
        fd = _PINS.pop(key, None)
    if fd is None:
        _append_lease(entry)
        return
    try:
        os.write(fd, f"{os.getpid()}\n".encode("ascii"))
    except TimeoutError:
        raise
    except OSError:
        pass
    finally:
        _close_lock(fd)


def _release_pins() -> None:
    with _PIN_LOCK:
        fds = list(_PINS.values())
        _PINS.clear()
    for fd in fds:
        _close_lock(fd)


def _slot_pinned(entry: Path) -> bool:
    """True when a live process holds the OS pin or its PID lease."""

    path = _pin_path(entry)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    except TimeoutError:
        raise
    except OSError:
        return True
    if not stat.S_ISREG(info.st_mode) or _is_symlink_or_reparse(info, path):
        return True
    fd = open_lock_file(path, create=False)
    if fd is None:
        return True
    free = False
    try:
        free = try_lock_fd(fd, exclusive=True)
        if not free:
            return True
        live = [pid for pid in dict.fromkeys(_lease_pids(fd))
                if process_exited(pid) is not True]
        _rewrite_lease(fd, live)
        if live:
            return True
        if os.name != "nt":
            unlink_quiet(path)
    finally:
        if free:
            unlock_fd(fd)
        close_lock_fd(fd)
    if free and os.name == "nt":
        unlink_quiet(path)
    return False


def _refresh_slot(entry: Path) -> None:
    """Touch regular leaves and the slot directory so reuse restarts the age."""

    for name in _SLOT_LEAVES:
        path = entry / name
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            continue
        except TimeoutError:
            raise
        except OSError:
            continue
        if not stat.S_ISREG(info.st_mode) or _is_symlink_or_reparse(info, path):
            continue
        try:
            os.utime(path, None, follow_symlinks=False)
        except TimeoutError:
            raise
        except (NotImplementedError, OSError, ValueError):
            continue
    try:
        info = os.lstat(entry)
    except TimeoutError:
        raise
    except OSError:
        return
    if stat.S_ISDIR(info.st_mode) and not _is_symlink_or_reparse(info, entry):
        try:
            os.utime(entry, None, follow_symlinks=False)
        except TimeoutError:
            raise
        except (NotImplementedError, OSError, ValueError):
            pass


def _create_marker(marker: Path) -> int | None:
    fd = open_lock_file(marker)
    if fd is not None and try_lock_fd(fd, exclusive=True):
        return fd
    if fd is not None:
        close_lock_fd(fd)
    return None


def _drop_marker(marker: Path, fd: int | None) -> None:
    if fd is None:
        return
    try:
        if os.name != "nt":
            unlink_quiet(marker)
            return
    finally:
        _close_lock(fd)
    unlink_quiet(marker)


def _unlink_dead_marker(marker: Path) -> None:
    """Unlink only when the marker lock is free, never while a writer holds it."""

    fd = open_lock_file(marker, create=False)
    if fd is None:
        return
    locked = try_lock_fd(fd, exclusive=True)
    try:
        if locked and os.name != "nt":
            unlink_quiet(marker)
    finally:
        if locked:
            unlock_fd(fd)
        close_lock_fd(fd)
    if locked and os.name == "nt":
        unlink_quiet(marker)


def _remove_trash(trash: Path, leaves: tuple[str, ...],
                  expected: dict[Path, tuple[int, int]] | None = None) -> int:
    """Unlink only re-validated regular leaves, then the empty trash directory."""

    try:
        info = os.lstat(trash)
    except TimeoutError:
        raise
    except OSError:
        return 0
    if not stat.S_ISDIR(info.st_mode) or _is_symlink_or_reparse(info, trash):
        return 0
    receipts = _validated_leaves(trash, leaves)
    if receipts is None:
        return 0
    if expected is not None and set(receipts.values()) != set(expected.values()):
        return 0
    try:
        current = os.lstat(trash)
    except TimeoutError:
        raise
    except OSError:
        return 0
    if ((current.st_dev, current.st_ino) != (info.st_dev, info.st_ino)
            or not stat.S_ISDIR(current.st_mode)
            or _is_symlink_or_reparse(current, trash)):
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
    removed = 0
    for child in children:
        try:
            info = os.lstat(child)
        except TimeoutError:
            raise
        except OSError:
            continue
        if not stat.S_ISDIR(info.st_mode) or _is_symlink_or_reparse(info, child):
            continue
        removed += _remove_trash(child, leaves)
    return removed


def _evict_entry(base: Path, entry: Path, leaves: tuple[str, ...]) -> int:
    """Re-check live state and atomically detach one slot before unlinking it."""

    with repro_storage._LOCK:
        with exclusive_lock(base / _RETENTION_LOCK_NAME, blocking=False) as locked:
            if not locked or _entry_locked(entry) or _slot_pinned(entry):
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


def _sweep_write_markers(base: Path, children: list[Path], now: float) -> None:
    """Drop markers left by a killed writer so its slot can become eligible."""

    try:
        with exclusive_lock(base / _RETENTION_LOCK_NAME, blocking=False) as locked:
            if not locked:
                return
            for child in children:
                if not child.name.startswith(".") or _WRITE_MARKER_INFIX not in child.name:
                    continue
                try:
                    info = os.lstat(child)
                except TimeoutError:
                    raise
                except OSError:
                    continue
                if not stat.S_ISREG(info.st_mode) or _is_symlink_or_reparse(info, child):
                    continue
                if now - info.st_mtime > _STALE_WRITE_MARKER_S:
                    _unlink_dead_marker(child)
    except TimeoutError:
        raise
    except OSError:
        return


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
    _sweep_write_markers(base, children, now)
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
    """Hold an OS-locked marker and a shared slot lease across one delivery.

    The marker is created and locked under the cross-process retention lock,
    which eviction holds for its whole re-check/rename section.  The retention
    lock is released before the caller writes leaves, so readers and concurrent
    writers never block; the held marker lock proves the writer is alive even
    when its mtime is older than the stale-marker threshold.  A shared OS pin is
    also acquired before the retention lock is released; on success it is handed
    off to a PID lease that covers the later in-process registration step, and
    leaves are re-touched so a written or reused slot restarts its age.
    """

    base = entry.parent
    try:
        base.mkdir(parents=True, exist_ok=True)
    except TimeoutError:
        raise
    except OSError:
        pass
    marker = base / (f"{_WRITE_MARKER_INFIX}{entry.name}-{os.getpid()}-"
                     f"{uuid.uuid4().hex}{_LOCK_SUFFIX}")
    handle = None
    safe = _safe_directory(base)
    if safe:
        with exclusive_lock(base / _RETENTION_LOCK_NAME, blocking=True):
            handle = _create_marker(marker)
            _hold_pin(entry)
    completed = False
    try:
        yield
        completed = True
    finally:
        try:
            if safe:
                _refresh_slot(entry)
        finally:
            if safe:
                if completed:
                    _seal_pin(entry)
                else:
                    _drop_pin(entry)
                    _slot_pinned(entry)  # Remove a pin leaf that never got a lease.
            _drop_marker(marker, handle)


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


atexit.register(_release_pins)

__all__ = ["PRUNE_MAX_AGE_DAYS", "PRUNE_MAX_ENTRIES", "opportunistic_prune",
           "prune_repro_storage", "retention_write_guard"]

# Deliberately last: ``repro_storage`` re-exports ``prune_repro_storage``, and
# binding the module object here (never its attributes) makes both import
# orders safe without a duplicate storage state machine.
from . import repro_storage  # noqa: E402  (see comment above)
