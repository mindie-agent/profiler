"""Cross-platform subprocess, WSL2 native binary lookup, and UTF-8 pipe helpers.

[Role]
  Provide zero-dependency host helpers for Windows ``CREATE_NO_WINDOW`` / ``CP936``
  child-pipe UTF-8 discipline, ``git -C`` extended-path normalization, and WSL2
  native Linux binary discovery that never resolves Windows PE / DrvFS binaries
  appended on ``$PATH``.

[Invariants]
  * ``which_native`` resolves symlinks before checking ``/proc/self/mountinfo``
    and returns ``None`` when only Windows ``.exe`` / PE / DrvFS candidates exist.
  * ``utf8_python_env`` sets ``PYTHONUTF8=1`` and ``PYTHONIOENCODING=utf-8`` so
    child Python interpreters emit UTF-8 on ``CP936`` Windows pipes.
  * ``except TimeoutError: raise`` precedes every ``except OSError:`` boundary.

[Timeouts & Locks]
  Pure bounded file-header / mountinfo reads; no locks or background processes.

[Side-Effect Policy]
  Read-only filesystem probes only; never mutates global ``os.environ``.
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Mapping

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
_IS_WINDOWS = os.name == "nt"
_MOUNTINFO_PATH = "/proc/self/mountinfo"
_WIN_SCRIPT_EXTS = (".exe", ".cmd", ".bat", ".com", ".ps1")


def no_window_kwargs() -> dict[str, int]:
    if not _IS_WINDOWS:
        return {}
    return {"creationflags": CREATE_NO_WINDOW}


def utf8_python_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if base is None else base)
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def normalize_git_repo_arg(path: str | os.PathLike[str]) -> str:
    raw = os.fspath(path)
    if _IS_WINDOWS and not raw.endswith((".", " ")):
        if raw[:8].casefold() == "\\\\?\\unc\\" and len(raw) > 8 and raw[8] not in ("\\", "/"):
            unc = "\\" + raw[7:]
            if len(unc) < 260:
                return unc
        elif (
            raw.startswith("\\\\?\\")
            and len(raw) >= 7
            and raw[4].isascii()
            and raw[4].isalpha()
            and raw[5] == ":"
            and raw[6] in ("\\", "/")
            and len(raw) - 4 < 260
        ):
            return raw[4:]
    return raw


def _decode_mountinfo_field(field: str) -> str:
    for oct_seq, ch in (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\")):
        field = field.replace(oct_seq, ch)
    return field


def _strict_realpath(raw_text: str) -> str:
    probe = raw_text if os.path.isabs(raw_text) else os.path.join(os.getcwd(), raw_text)
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
                    probe = target if os.path.isabs(target) else os.path.join(os.path.dirname(probe), target)
                    continue
            except TimeoutError:
                raise
            except OSError:
                pass
            parent, name = os.path.split(probe.rstrip("/"))
            if not name or parent == probe:
                return os.path.abspath(raw_text)
            suffix.append(name)
            probe = parent
        except OSError:
            return os.path.abspath(raw_text)


def is_wsl_drvfs(value: str | os.PathLike[str]) -> bool:
    if _IS_WINDOWS:
        return False
    try:
        resolved = _strict_realpath(os.fspath(value))
        lines = Path(_MOUNTINFO_PATH).read_text(encoding="utf-8", errors="replace").splitlines()
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
        with Path(value).open("rb") as handle:
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


def _is_exec_regular_file(cand: Path) -> bool:
    try:
        st = cand.stat()
        return stat.S_ISREG(st.st_mode) and os.access(cand, os.X_OK)
    except TimeoutError:
        raise
    except OSError:
        return False


def which_native(command: str, *, path: str | None = None) -> str | None:
    if _IS_WINDOWS:
        return shutil.which(command, path=path)
    if os.path.sep in command:
        cand = Path(command)
        if _is_exec_regular_file(cand) and not is_pe_executable(cand) and not is_wsl_drvfs(cand):
            return str(cand)
        return None
    search_path = os.environ.get("PATH", None) if path is None else path
    if search_path is None:
        search_path = os.defpath
    if not search_path:
        return None
    for entry in search_path.split(os.pathsep):
        if not entry:
            continue
        cand = Path(os.path.abspath(entry)) / command
        if cand.suffix.lower() in _WIN_SCRIPT_EXTS:
            continue
        if not _is_exec_regular_file(cand):
            continue
        if is_wsl_drvfs(cand) or is_pe_executable(cand):
            continue
        return str(cand)
    return None
