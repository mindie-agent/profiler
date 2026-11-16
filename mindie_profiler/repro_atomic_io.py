"""Unfollowed, inode-checked atomic file primitives for artifact stores.

[Role]
  Own unfollowed writes/rollback with protected inodes and slot subtrees.
[Invariants]
  * Inspect parents/leaves; open only exclusive/no-follow 0600 temporaries.
  * Detach and verify publication inodes; install by exclusive link or replace.
  * Check final regular-file identity and SHA-256 through unfollowed reads.
  * Park rollback leaves; restore foreign entries exclusively or retain recovery.
[Timeouts & Locks]
  Commit registration and final-leaf cleanup share a process-local RLock.
  No lock spans publication or verification; private recovery names are owned.
[Side-Effect Policy]
  Writes the destination and unpredictable temporary/recovery siblings only.
  Never follows symlinks or truncates pre-existing inodes.
"""
from __future__ import annotations
import contextlib
import errno
import hashlib
import io
import os
import stat
import sys
import threading
from pathlib import Path
from typing import Any, Iterable
_TMP_SUFFIX = ".tmp"
_COPY_CHUNK = 1 << 20
_OWNERSHIP_LOCK = threading.RLock()
_COMMITTED_INODES: set[tuple[int, int]] = set()
_IS_WIN = os.name == "nt"
_WIN_BIN = os.O_BINARY if _IS_WIN else 0
_READ_FLAGS = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | _WIN_BIN
def _link_nofollow(src: Any, dst: Any) -> None:
    os.link(src, dst) if _IS_WIN else os.link(src, dst, follow_symlinks=False)
def _retention_read_hook(path: Path) -> None:
    from . import repro_retention
    repro_retention.note_atomic_read(path)
def read_regular_bytes(path: Any) -> bytes | None:
    try:
        target = Path(str(path))
        before = os.lstat(target)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            return None
        handle = os.open(target, _READ_FLAGS)
    except TimeoutError: raise
    except OSError: return None
    stream, expected_fd_inode = None, None
    def close(primary):
        if stream is None:
            _close_owned_fd(handle, active_exc=primary, expected=expected_fd_inode)
        else:
            _close_stream(stream, handle, expected_fd_inode, primary)
    try:
        with _cleanup_scope(close):
            opened = os.fstat(handle)
            expected_fd_inode = (opened.st_dev, opened.st_ino)
            if not stat.S_ISREG(opened.st_mode) or expected_fd_inode != (before.st_dev, before.st_ino):
                return None
            if not _IS_WIN:
                os.set_blocking(handle, True)
            stream = os.fdopen(handle, "rb", closefd=False)
            handle = _borrow_stream_fd(stream, handle, expected_fd_inode)
            data = stream.read()
            _retention_read_hook(target)
            return data
    except TimeoutError: raise
    except OSError: return None
def inode_of(path: Any) -> tuple[int, int] | None:
    info = lstat_or_none(path)
    return (info.st_dev, info.st_ino) if info is not None and stat.S_ISREG(info.st_mode) else None
def unlink_quiet(path: Any) -> None:
    try:
        os.unlink(path)
    except TimeoutError: raise
    except OSError:
        return
def _cleanup_call(action, primary=None):
    with contextlib.suppress(Exception) if primary is not None else contextlib.nullcontext():
        return action()
@contextlib.contextmanager
def _cleanup_scope(cleanup):
    """Pass only this body's escaping exception, never a caller's handled one."""
    completed = False
    try:
        yield
        completed = True
    finally:
        cleanup(None if completed else sys.exc_info()[1])
def _retry_cleanup(action, absent_errno: int, *, active_exc) -> bool:
    """Retry finite OS faults; preserve the body exception or first cleanup fault."""
    first_error = None
    for _ in range(4):
        completed, error = False, None
        with contextlib.suppress(BaseException):
            try:
                action()
                completed = True
            finally:
                error = None if completed else sys.exc_info()[1]
        if error is None or (isinstance(error, OSError) and error.errno == absent_errno):
            break
        first_error = first_error or error
        if not isinstance(error, OSError):
            break
    if active_exc is None and first_error is not None:
        raise first_error
    return first_error is None
def _recover_fd_inode(fd):
    """Recover an opened-FD receipt, including rejected non-regular files."""
    for _ in range(4):
        with contextlib.suppress(BaseException):
            info = os.fstat(fd)
            return (info.st_dev, info.st_ino)
    return None
def _close_owned_fd(fd: int, *, active_exc, expected=None) -> None:
    expected, entered = expected or _recover_fd_inode(fd), False
    def close():
        nonlocal entered
        if (expected is None and not entered) or (expected is not None and _recover_fd_inode(fd) == expected):
            entered = True  # Without a receipt, a syscall may be entered only once.
            os.close(fd)
    _retry_cleanup(close, errno.EBADF, active_exc=active_exc)
def _stream_raw(stream):
    return getattr(getattr(stream, "buffer", stream), "raw", getattr(stream, "buffer", stream))
def _borrow_stream_fd(stream, fd, expected):
    """Move an owning raw to a fresh borrowed FD; never reclaim its old number."""
    raw = _stream_raw(stream)
    if raw.closed or not raw.closefd:
        return fd
    mode, name, transferred = raw.mode, raw.name, False
    try:
        spare = os.dup(fd)
        with _cleanup_scope(lambda exc: _close_owned_fd(spare, expected=expected, active_exc=exc) if exc else None):
            io.FileIO.__init__(raw, spare, mode, closefd=False)
            transferred = True
            raw.name = name
        return spare
    finally:
        if not transferred:
            io.FileIO.close(raw)  # No callbacks ran; retire the original owner on dup failure.
def _close_stream(stream, fd, expected, primary):
    fd = _borrow_stream_fd(stream, fd, expected)
    raw = _stream_raw(stream)
    def close():
        if not stream.closed:
            if expected is not None and _recover_fd_inode(fd) == expected:
                stream.close()
            else:
                io.FileIO.close(raw)  # Non-owning: neither flush nor close a reused FD.
                raise OSError("stream descriptor ownership changed")
    with _cleanup_scope(lambda exc: _close_owned_fd(fd, expected=expected, active_exc=primary or exc)):
        try:
            return _retry_cleanup(close, errno.EBADF, active_exc=primary) and stream.closed
        finally:
            if stream.closed and expected is not None and _recover_fd_inode(fd) == expected:
                _cleanup_call(lambda: io.FileIO(fd, closefd=True).close(), primary or sys.exc_info()[1])
            io.FileIO.close(raw)  # Retire all wrappers before the owner releases fd.
def _unlink_owned_path(path, expected_inode=None, *, protected=(), active_exc=None, private=False):
    """Detach before checking/deleting; never unlink a shared final pathname."""
    if expected_inode is None:
        return
    path = Path(path)
    parked = None
    def owned(info):
        inode = (info.st_dev, info.st_ino)
        return (stat.S_ISREG(info.st_mode) and inode == expected_inode
                and inode not in protected and (private or inode not in _COMMITTED_INODES))
    def remove():
        nonlocal parked
        if private:
            if owned(os.lstat(path)):
                os.unlink(path)
            return
        if parked is None:
            parked = path.with_name(f".{path.name}.{os.urandom(16).hex()}.rollback")
        try:
            info = os.lstat(parked)  # Also recover a rename that raised after success.
        except FileNotFoundError:
            if not owned(os.lstat(path)):
                return
            os.rename(path, parked)
            info = os.lstat(parked)
        if not owned(info):
            try:
                _link_nofollow(parked, path)
            except FileExistsError:
                current = os.lstat(path)
                if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                    return  # Keep the foreign recovery leaf; never overwrite another writer.
        os.unlink(parked)
    with contextlib.nullcontext() if private else _OWNERSHIP_LOCK:
        _retry_cleanup(remove, errno.ENOENT, active_exc=active_exc)
def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def stat_or_none(path: Any) -> os.stat_result | None:
    """Checked stat: ordinary OS errors are None; timeouts retain identity."""
    try: return os.stat(path)
    except TimeoutError: raise
    except (OSError, ValueError): return None
def lstat_or_none(path: Any) -> os.stat_result | None:
    try: return os.lstat(path)
    except TimeoutError: raise
    except (OSError, ValueError): return None
def path_exists(path: Any) -> bool:
    return stat_or_none(path) is not None
def path_lexists(path: Any) -> bool:
    return lstat_or_none(path) is not None
def path_is_dir(path: Any) -> bool:
    info = stat_or_none(path)
    return info is not None and stat.S_ISDIR(info.st_mode)
def path_is_file(path: Any) -> bool:
    info = stat_or_none(path)
    return info is not None and stat.S_ISREG(info.st_mode)
def path_is_symlink(path: Any) -> bool:
    info = lstat_or_none(path)
    return info is not None and stat.S_ISLNK(info.st_mode)
def _absolute(path: Any) -> Path:
    return Path(os.path.abspath(str(path)))
def _inside(path: Path, roots: Iterable[Path]) -> bool:
    ancestors = {path, *path.parents}
    return not ancestors.isdisjoint(roots) if isinstance(roots, (set, frozenset)) else any(r in ancestors for r in roots)
def _resolved_loose(path: Path) -> Path | None:
    try: return path.resolve(strict=False)
    except TimeoutError: raise
    except (OSError, RuntimeError): return None
def _forbidden_parent(parent: Path, forbidden: set[Path], allow_slot: Path | None) -> bool:
    if not forbidden:
        return False
    resolved = _resolved_loose(parent)
    allowed = {allow_slot, _resolved_loose(allow_slot) if allow_slot is not None else None} - {None}
    if parent in allowed or (resolved is not None and resolved in allowed):
        return False
    return _inside(parent, forbidden) or (resolved is not None and _inside(resolved, forbidden))
def _anchor_for(parent: Path) -> tuple[Path, tuple[str, ...]] | None:
    root = Path(parent.anchor or os.sep)
    if (info := stat_or_none(root)) is None or not stat.S_ISDIR(info.st_mode):
        return None
    if not _IS_WIN:
        temp = Path(os.sep + "tmp")
        if (temp == parent or temp in parent.parents) and (ti := stat_or_none(temp)) is not None and stat.S_ISDIR(ti.st_mode):
            return temp, parent.relative_to(temp).parts
    return root, (parent.parts[1:] if parent.anchor else parent.parts)
def _walk_parent(parent: Path, forbidden: set[Path], allow_slot: Path | None, create: bool = True) -> bool:
    """Validate every component before creating any missing directory."""
    anchor = _anchor_for(parent)
    if anchor is None:
        return False
    current, parts = anchor
    for part in parts:
        current = current / part
        if _forbidden_parent(current, forbidden, allow_slot):
            return False
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if not create:
                continue
            try:
                os.mkdir(current, 0o700)
                info = os.lstat(current)
            except TimeoutError: raise
            except OSError:
                return False
        except TimeoutError: raise
        except OSError:
            return False
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return False
        if _forbidden_parent(current, forbidden, allow_slot):
            return False
    return True
def validate_directory(path: Any, *, forbidden: Iterable[Any] = (), allow_slot: Any = None) -> bool:
    return _walk_parent(_absolute(path), {_absolute(item) for item in forbidden},
                        _absolute(allow_slot) if allow_slot is not None else None, create=False)
def ensure_directory(path: Any, *, forbidden: Iterable[Any] = (), allow_slot: Any = None) -> bool:
    return _walk_parent(_absolute(path), {_absolute(item) for item in forbidden},
                        _absolute(allow_slot) if allow_slot is not None else None, create=True)
def _leaf_safe(target: Path, protected: set[tuple[int, int]]) -> bool:
    try:
        info = os.lstat(target)
    except FileNotFoundError:
        return True
    except TimeoutError: raise
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) not in protected
def _inspect_predictable_temps(parent: Path, leaf: str) -> bool:
    candidates = [parent / (leaf + _TMP_SUFFIX)]
    try:
        candidates.extend(parent.glob("." + leaf + ".*" + _TMP_SUFFIX))
    except TimeoutError: raise
    except OSError:
        pass
    for candidate in candidates:
        info = lstat_or_none(candidate)
        if info is not None and stat.S_ISDIR(info.st_mode):
            return False
    return True
def _open_temporary(parent: Path, leaf: str) -> tuple[int, Path] | None:
    temporary = parent / f".{leaf}.{os.getpid()}.{os.urandom(16).hex()}{_TMP_SUFFIX}"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | (_WIN_BIN if _IS_WIN else getattr(os, "O_NOFOLLOW", 0))
    try:
        handle = os.open(temporary, flags, 0o600)
    except TimeoutError: raise
    except OSError: return None
    return handle, temporary
def _write_all(handle: int, data: bytes) -> bool:
    view = memoryview(data)
    while view:
        written = os.write(handle, view)
        if written <= 0:
            return False
        view = view[written:]
    os.fsync(handle)
    return True
def _verified_inode(path: Path, expected: tuple[int, int], digest: str) -> bool:
    try:
        if inode_of(path) != expected:
            return False
        handle = os.open(path, _READ_FLAGS)
        receipt = None
        with _cleanup_scope(lambda exc: _close_owned_fd(handle, active_exc=exc, expected=receipt)):
            opened = os.fstat(handle)
            receipt = (opened.st_dev, opened.st_ino)
            if not stat.S_ISREG(opened.st_mode) or receipt != expected:
                return False
            hasher = hashlib.sha256()
            while True:
                chunk = os.read(handle, _COPY_CHUNK)
                if not chunk:
                    break
                hasher.update(chunk)
            return hasher.hexdigest() == digest
    except TimeoutError: raise
    except OSError: return False
def safe_write_bytes(target: Any, data: bytes, *, protected: Iterable[tuple[int, int]] = (),
                     forbidden: Iterable[Any] = (), allow_slot: Any = None, exclusive: bool = False,
                     installed_out: list[tuple[int, int]] | None = None, refresh_protected=None) -> bool:
    """Install and verify a fresh inode; report ownership only on success."""
    destination, parent = _absolute(target), _absolute(target).parent
    from . import repro_retention
    with repro_retention.atomic_write_guard(destination):
        protected_set = {(int(dev), int(ino)) for dev, ino in protected}
        forbidden_set = {_absolute(path) for path in forbidden}
        allowance = _absolute(allow_slot) if allow_slot is not None else None
        if (not _walk_parent(parent, forbidden_set, allowance) or _forbidden_parent(parent, forbidden_set, allowance)
                or not _leaf_safe(destination, protected_set) or not _inspect_predictable_temps(parent, destination.name)):
            return False
        opened = _open_temporary(parent, destination.name)
        if opened is None:
            return False
        handle, temporary = opened
        installed_inode = temp_inode = publication = None
        temp_present, verified = True, False
        def close_writer(primary):
            nonlocal temp_inode
            if temp_inode is None:
                temp_inode = _recover_fd_inode(handle)
            _close_owned_fd(handle, active_exc=primary, expected=temp_inode)
        def rollback(primary_exc):
            if temp_present:
                with _cleanup_scope(lambda exc: _unlink_owned_path(
                        temporary, temp_inode, active_exc=primary_exc or exc, private=True)):
                    if publication is not None:
                        _unlink_owned_path(publication, temp_inode, active_exc=primary_exc, private=True)
            if installed_inode is not None and not verified:
                _unlink_owned_path(destination, installed_inode, protected=protected_set, active_exc=primary_exc)
        with _cleanup_scope(rollback):
            try:
                with _cleanup_scope(close_writer):
                    temp_info = os.fstat(handle)
                    temp_inode = (temp_info.st_dev, temp_info.st_ino)
                    if not stat.S_ISREG(temp_info.st_mode):
                        raise OSError("temporary is not a regular file")
                    if temp_info.st_nlink == 1:  # O_CREAT|O_EXCL sole link: purge recycled ext4 inodes.
                        with _OWNERSHIP_LOCK:
                            _COMMITTED_INODES.discard(temp_inode)
                        protected_set.discard(temp_inode)
                    if not _write_all(handle, data):
                        raise OSError("short write")
                expected, digest = temp_inode, sha256_digest(data)
                if not _verified_inode(temporary, expected, digest):
                    return False
                if refresh_protected is not None:
                    protected_set.update(refresh_protected())
                    protected_set.discard(expected)
                if not _leaf_safe(destination, protected_set) or _forbidden_parent(parent, forbidden_set, allowance):
                    return False
                # Keep the leaf prefix/suffix used by retained temporary fault selectors.
                publication = parent / f".{destination.name}.{os.urandom(16).hex()}.publish.tmp"
                os.rename(temporary, publication)
                if inode_of(publication) != expected:
                    try:
                        _link_nofollow(publication, temporary)
                    except FileExistsError:
                        return False  # Preserve both foreign occupants.
                    os.unlink(publication)
                    return False
                installed_inode = expected
                if exclusive:
                    os.link(publication, destination)
                    _unlink_owned_path(publication, expected, private=True)
                else:
                    os.replace(publication, destination)
                temp_present = False
                verified = _verified_inode(destination, expected, digest)
                if not verified:
                    return False
            except TimeoutError: raise
            except OSError: return False
        if installed_out is not None:
            installed_out.append(expected)
        return True
__all__ = ["ensure_directory", "inode_of", "lstat_or_none", "path_exists", "path_is_dir", "path_is_file",
           "path_is_symlink", "path_lexists", "read_regular_bytes", "safe_write_bytes", "sha256_digest",
           "stat_or_none", "unlink_quiet", "validate_directory"]
