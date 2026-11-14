"""Cross-platform subprocess, WSL2 native binary lookup, and UTF-8 pipe helpers.

[Role]
  Provide zero-dependency host helpers for Windows ``CREATE_NO_WINDOW`` / ``CP936``
  child-pipe UTF-8 discipline, ``git -C`` extended-path normalization, Windows
  process-tree termination, and WSL2 native Linux binary discovery that never
  resolves Windows PE / DrvFS binaries appended on ``$PATH``.

[Invariants]
  * ``which_native`` preserves explicit relative/absolute paths (never stripping
    ``./`` into a bare command name) and preserves ``..`` until symlink resolution
    before checking ``/proc/self/mountinfo``.
  * ``utf8_python_env`` explicitly sets ``PYTHONUTF8=1`` and
    ``PYTHONIOENCODING=utf-8`` so inherited ``CP936`` settings cannot override it.
  * ``except TimeoutError: raise`` precedes every ``except OSError:`` boundary,
    including Windows ``PATHEXT`` candidate probes.

[Timeouts & Locks]
  Pure bounded file-header / mountinfo reads and bounded ``taskkill`` execution;
  no locks or persistent background processes.

[Side-Effect Policy]
  Read-only filesystem probes except ``kill_windows_process_tree``, which
  terminates only the caller-owned PID tree; never mutates global ``os.environ``.
"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from typing import Mapping

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
_IS_WINDOWS_OVERRIDE: bool | None = None
_MOUNTINFO_PATH = "/proc/self/mountinfo"
_WIN_SCRIPT_EXTS = (".exe", ".cmd", ".bat", ".com", ".ps1")
_WIN_DEFAULT_PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC"
_WIN_RESERVED_STEMS = frozenset(
    {
        "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
        *(f"COM{idx}" for idx in range(1, 10)),
        *(f"LPT{idx}" for idx in range(1, 10)),
        "COM\xb9", "COM\xb2", "COM\xb3", "LPT\xb9", "LPT\xb2", "LPT\xb3",
    }
)


def _is_windows() -> bool:
    return (os.name == "nt") if _IS_WINDOWS_OVERRIDE is None else _IS_WINDOWS_OVERRIDE


def _is_windows_fs() -> bool:
    return (sys.platform == "win32") if _IS_WINDOWS_OVERRIDE is None else _IS_WINDOWS_OVERRIDE


def no_window_kwargs() -> dict[str, int]:
    if not _is_windows():
        return {}
    return {"creationflags": CREATE_NO_WINDOW}


def utf8_python_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _valid_win32_components(parts: list[str]) -> bool:
    for part in parts:
        if not part or part in {".", ".."} or part.endswith((".", " ")) or ":" in part:
            return False
        stem = part.split(".", 1)[0].rstrip(" ").upper()
        if stem in _WIN_RESERVED_STEMS:
            return False
    return True


def normalize_git_repo_arg(path: str | os.PathLike[str]) -> str:
    raw = os.fspath(path)
    if not _is_windows() or not raw.startswith("\\\\?\\") or "/" in raw:
        return raw
    if raw[:8].casefold() == "\\\\?\\unc\\":
        rest = raw[8:]
        body = rest[:-1] if rest.endswith("\\") else rest
        if not body or body.endswith("\\"):
            return raw
        parts = body.split("\\")
        unc = "\\" + raw[7:]
        if len(parts) >= 2 and len(unc) < 248 and _valid_win32_components(parts):
            return unc
        return raw
    if len(raw) >= 7 and raw[4].isascii() and raw[4].isalpha() and raw[5] == ":" and raw[6] == "\\":
        candidate = raw[4:]
        tail = candidate[3:]
        body = tail[:-1] if tail.endswith("\\") else tail
        if tail and not body:
            return raw
        parts = body.split("\\") if body else []
        if len(candidate) < 248 and _valid_win32_components(parts):
            return candidate
    return raw


def _decode_mountinfo_field(field: str) -> str:
    for oct_seq, ch in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        field = field.replace(oct_seq, ch)
    return field


def _join_uncollapsed(base: str, leaf: str) -> str:
    if base == "/":
        return f"/{leaf}"
    return f"{base.rstrip('/')}/{leaf}"


def _strict_realpath(raw_text: str) -> str:
    probe = raw_text if raw_text.startswith("/") else _join_uncollapsed(os.getcwd(), raw_text)
    suffix: list[str] = []
    hops = 0
    while True:
        try:
            resolved = os.path.realpath(probe, strict=True)
            return os.path.normpath(os.path.join(resolved, *reversed(suffix))) if suffix else resolved
        except TimeoutError:
            raise
        except (FileNotFoundError, NotADirectoryError):
            try:
                if hops < 40 and stat.S_ISLNK(os.lstat(probe).st_mode):
                    hops += 1
                    target = os.readlink(probe)
                    parent_dir = os.path.dirname(probe) or "/"
                    expanded = target if target.startswith("/") else _join_uncollapsed(parent_dir, target)
                    probe = "/".join([expanded.rstrip("/"), *reversed(suffix)]) if suffix else expanded
                    suffix.clear()
                    continue
            except TimeoutError:
                raise
            except OSError:
                pass
            trimmed = probe.rstrip("/")
            if not trimmed:
                return os.path.normpath(os.path.join("/", *reversed(suffix))) if suffix else "/"
            parent, name = os.path.split(trimmed)
            if not name or parent == probe:
                return probe
            suffix.append(name)
            probe = parent or "/"
        except OSError:
            return probe


def is_wsl_drvfs(value: str | os.PathLike[str]) -> bool:
    if _is_windows_fs():
        return False
    try:
        resolved = _strict_realpath(os.fspath(value))
        with open(_MOUNTINFO_PATH, "r", encoding="utf-8", errors="replace") as handle:
            lines = handle.read().splitlines()
    except TimeoutError:
        raise
    except OSError:
        return False
    best_mp = ""
    best_fstype = ""
    best_opts = ""
    for line in lines:
        parts = line.split(" - ", 1)
        if len(parts) != 2:
            continue
        lhs = parts[0].split()
        rhs = parts[1].split()
        if len(lhs) < 5 or len(rhs) < 3:
            continue
        mp = _decode_mountinfo_field(lhs[4])
        if resolved == mp or resolved.startswith(mp.rstrip("/") + "/") or mp == "/":
            if len(mp) >= len(best_mp):
                best_mp = mp
                best_fstype = rhs[0]
                best_opts = rhs[2]
    if not best_mp:
        return False
    return best_fstype in {"drvfs", "9p"} and ("aname=drvfs" in best_opts or best_fstype == "drvfs")


def is_pe_executable(value: str | os.PathLike[str]) -> bool:
    try:
        with open(os.fspath(value), "rb") as handle:
            dos = handle.read(64)
            if len(dos) < 64 or dos[:2] != b"MZ":
                return False
            pe_offset = int.from_bytes(dos[0x3C:0x40], "little", signed=False)
            handle.seek(pe_offset)
            return handle.read(4) == b"PE\x00\x00"
    except TimeoutError:
        raise
    except OSError:
        return False


def _is_regular_file(cand: str, *, require_exec: bool = False) -> bool:
    try:
        st = os.stat(cand)
        if not stat.S_ISREG(st.st_mode):
            return False
        return os.access(cand, os.X_OK) if require_exec else True
    except TimeoutError:
        raise
    except OSError:
        return False


def _which_windows(command: str, *, path: str | None = None) -> str | None:
    if not command:
        return None
    pathext_raw = os.environ.get("PATHEXT") or _WIN_DEFAULT_PATHEXT
    pathext: list[str] = []
    for raw_ext in pathext_raw.split(";"):
        if not raw_ext:
            continue
        norm_ext = raw_ext if raw_ext.startswith(".") else f".{raw_ext}"
        for variant in (norm_ext.lower(), norm_ext):
            if variant not in pathext:
                pathext.append(variant)
    has_known_ext = any(command.lower().endswith(ext.lower()) for ext in pathext)
    if "\\" in command or "/" in command or (len(command) >= 2 and command[1] == ":"):
        direct_candidates = [command] if has_known_ext else [command, *(command + ext for ext in pathext)]
        for cand in direct_candidates:
            if _is_regular_file(cand):
                return cand if ("\\" in cand or "/" in cand) else os.path.abspath(cand)
        return None
    search_path = os.environ.get("PATH", None) if path is None else path
    if search_path is None:
        search_path = os.defpath
    if not search_path:
        return None
    sep = ";" if ";" in search_path else os.pathsep
    names = [command] if has_known_ext else [command + ext for ext in pathext]
    for raw_entry in search_path.split(sep):
        entry = raw_entry.strip().strip('"')
        if not entry:
            continue
        join_sep = "\\" if ("\\" in entry or (len(entry) >= 2 and entry[1] == ":")) else os.sep
        prefix = entry if entry in {"\\", "/"} else entry.rstrip("/\\")
        for name in names:
            cand = f"{prefix}{name}" if prefix in {"\\", "/"} else f"{prefix}{join_sep}{name}"
            if _is_regular_file(cand):
                return cand
    return None


def which_native(command: str, *, path: str | None = None) -> str | None:
    if not command:
        return None
    if _is_windows_fs():
        return _which_windows(command, path=path)
    if "/" in command:
        if _is_regular_file(command, require_exec=True) and not is_pe_executable(command) and not is_wsl_drvfs(command):
            return command
        return None
    search_path = os.environ.get("PATH", None) if path is None else path
    if search_path is None:
        search_path = os.defpath
    if not search_path:
        return None
    _, ext = os.path.splitext(command)
    if ext.lower() in _WIN_SCRIPT_EXTS:
        return None
    for entry in search_path.split(os.pathsep):
        if not entry:
            continue
        if entry == ".":
            cand = _join_uncollapsed(os.getcwd(), command)
        elif entry.startswith("/"):
            cand = _join_uncollapsed(entry, command)
        else:
            cand = _join_uncollapsed(_join_uncollapsed(os.getcwd(), entry), command)
        if not _is_regular_file(cand, require_exec=True):
            continue
        if is_wsl_drvfs(cand) or is_pe_executable(cand):
            continue
        return cand
    return None


def kill_windows_process_tree(pid: int, *, timeout_s: float) -> subprocess.CompletedProcess[str]:
    sys_root = (os.environ.get("SystemRoot") or r"C:\Windows").rstrip("/\\")
    tk_exe = f"{sys_root}\\System32\\taskkill.exe"
    tk_cmd = tk_exe if _is_regular_file(tk_exe) else "taskkill"
    return subprocess.run(
        [tk_cmd, "/T", "/F", "/PID", str(pid)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=max(0.1, float(timeout_s)),
        check=False,
        **no_window_kwargs(),
    )
