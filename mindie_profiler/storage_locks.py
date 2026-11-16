"""Advisory cross-process locks for bounded storage caches.

[Role]
  Serialize storage mutations (cache eviction, reproducer retention, trace
  sidecar publication) across threads in one process and across processes that
  share the same cache directory.

[Invariants]
  * POSIX locks use ``fcntl.flock``; Windows locks use ``msvcrt.locking`` on
    the first byte of the lock file.
  * A per-path process-local ``threading.RLock`` always precedes the OS lock,
    so two threads can never race on one file-descriptor lock.
  * A nested acquisition by the same thread is re-entrant and never re-locks
    the OS file; callers may compose guarded helpers safely.
  * Lock files are 0-byte leaves that are created on demand and never removed
    while a holder depends on their inode identity.
  * Every filesystem failure is best effort: a non-blocking caller receives
    ``False`` instead of an exception, while a blocking caller degrades to the
    process-local lock when the platform cannot provide an advisory lock.

[Timeouts & Locks]
  Non-blocking acquisition is a single attempt.  Blocking acquisition waits on
  the OS primitive; an OS crash releases the advisory lock automatically.

[Side-Effect Policy]
  Creates the requested 0-byte lock file; never writes payload bytes and never
  deletes a lock path.
"""

from __future__ import annotations

from collections.abc import Iterator
import contextlib
import errno
import os
from pathlib import Path
import stat
import threading

_REGISTRY_LOCK = threading.Lock()
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_HELD = threading.local()
_LOCK_FILE_MODE = stat.S_IRUSR | stat.S_IWUSR


def _thread_lock(key: str) -> threading.RLock:
    with _REGISTRY_LOCK:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


def _os_lock(fd: int, *, blocking: bool) -> None:
    if os.name == "nt":
        import msvcrt

        while True:
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                msvcrt.locking(fd, msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
                return
            except TimeoutError:
                raise
            except OSError as exc:
                # ``LK_LOCK`` gives up after roughly ten seconds; a long
                # compile must not silently split the directory lock.
                if not blocking or exc.errno not in (errno.EACCES, errno.EDEADLK):
                    raise
                continue
    import fcntl

    flags = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
    fcntl.flock(fd, flags)


def _os_unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fd, fcntl.LOCK_UN)


@contextlib.contextmanager
def exclusive_lock(path: str | os.PathLike[str], *, blocking: bool = True) -> Iterator[bool]:
    """Yield ``True`` when the path lock is held, ``False`` on contention.

    The process-local lock is always released, so a failed non-blocking attempt
    leaves no residue for the next caller.
    """

    key = os.path.abspath(os.fspath(path))
    depths = getattr(_HELD, "depths", None)
    if depths is None:
        depths = {}
        _HELD.depths = depths
    if depths.get(key):
        depths[key] += 1
        try:
            yield True
        finally:
            depths[key] -= 1
        return
    guard = _thread_lock(key)
    if not guard.acquire(blocking=blocking):
        yield False
        return
    fd = None
    locked = False
    try:
        try:
            fd = os.open(key, os.O_CREAT | os.O_RDWR, _LOCK_FILE_MODE)
        except TimeoutError:
            raise
        except OSError:
            fd = None
        if fd is None:
            # Advisory locks may be unsupported (some network filesystems).
            # A blocking caller still owns the process-local lock.
            locked = blocking
        else:
            try:
                _os_lock(fd, blocking=blocking)
                locked = True
            except TimeoutError:
                raise
            except OSError:
                locked = blocking
        depths[key] = 1
        try:
            yield locked
        finally:
            if fd is not None:
                if locked:
                    try:
                        _os_unlock(fd)
                    except TimeoutError:
                        raise
                    except OSError:
                        pass
                try:
                    os.close(fd)
                except TimeoutError:
                    raise
                except OSError:
                    pass
    finally:
        depths.pop(key, None)
        guard.release()


__all__ = ["exclusive_lock"]
