"""Regression tests for Windows CP936/CREATE_NO_WINDOW, WSL2 native lookup, and TimeoutError honesty."""
from __future__ import annotations

import io
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from unittest import mock

import pytest

from mindie_profiler import _host_exec, kernel_inventory, native_capture_shm, tensor_cast_provider, vllm_online_evidence


def test_normalize_git_repo_arg_strips_only_safe_extended_prefixes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_host_exec, "_IS_WINDOWS_OVERRIDE", True)
    assert _host_exec.normalize_git_repo_arg(r"\\?\C:\Users\张三\repo") == r"C:\Users\张三\repo"
    assert _host_exec.normalize_git_repo_arg(r"\\?\UNC\server\share\repo") == r"\\server\share\repo"
    for unsafe in (
        r"\\?\Volume{01234567-89ab-cdef-0123-456789abcdef}\repo",
        r"\\?\C:\Users\张三\repo.",
        r"\\?\C:\trusted.\repo",
        r"\\?\C:\trusted \repo",
        r"\\?\C:\dir\NUL\repo",
        r"\\?\C:\dir\..\repo",
        r"\\?\C:\dir/sub\repo",
    ):
        assert _host_exec.normalize_git_repo_arg(unsafe) == unsafe


def test_utf8_python_env_overrides_inherited_cp936() -> None:
    env = _host_exec.utf8_python_env({"PYTHONIOENCODING": "cp936", "PYTHONUTF8": "0"})
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    child_env = _host_exec.utf8_python_env({**os.environ, "PYTHONIOENCODING": "cp936", "PYTHONUTF8": "0"})
    proc = subprocess.run(
        [sys.executable, "-c", "import sys; sys.stdout.write('昇腾算子分析\\n')"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10.0,
        check=True,
        env=child_env,
        **_host_exec.no_window_kwargs(),
    )
    assert proc.stdout.strip() == "昇腾算子分析"


def test_host_exec_explicit_relpath_symlink_dotdot_and_pe_edge_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name == "nt":
        pytest.skip("POSIX/WSL2 symlink/mountinfo and PATH edge-case test")
    ext4_root = tmp_path / "ext4"
    ext4_sub = ext4_root / "sub"
    decoy_bin = ext4_root / "bin"
    drv_dir = tmp_path / "mnt_c"
    ext4_sub.mkdir(parents=True)
    decoy_bin.mkdir()
    drv_dir.mkdir()

    decoy_git = decoy_bin / "git"
    decoy_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    decoy_git.chmod(0o755)

    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        f"30 1 8:1 / {tmp_path} rw,relatime - ext4 /dev/sdb rw\n"
        f"40 30 0:35 / {drv_dir.resolve()} rw,noatime - 9p drvfs rw,aname=drvfs\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_host_exec, "_MOUNTINFO_PATH", str(mountinfo))
    link = ext4_sub / "escape"
    link.symlink_to(drv_dir / "nested")
    assert _host_exec.is_wsl_drvfs(f"{link}/../tool") is True
    # Must NOT collapse escape/.. lexically to ext4_root/bin where decoy_git lives:
    assert _host_exec.which_native("git", path=f"{ext4_sub}/escape/../bin") is None

    large_pe = tmp_path / "large_pe"
    buf = bytearray(0x1400)
    buf[0:2] = b"MZ"
    buf[0x3C:0x40] = (0x1200).to_bytes(4, "little")
    buf[0x1200:0x1204] = b"PE\x00\x00"
    large_pe.write_bytes(bytes(buf))
    assert _host_exec.is_pe_executable(large_pe) is True

    cwd_dir = tmp_path / "cwd"
    def_dir = tmp_path / "defbin"
    cwd_dir.mkdir()
    def_dir.mkdir()
    for folder, name in ((cwd_dir, "git"), (cwd_dir, "gcc"), (def_dir, "git")):
        tool = folder / name
        tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)
    monkeypatch.chdir(cwd_dir)
    assert _host_exec.which_native("./gcc") == "./gcc"
    monkeypatch.setattr(_host_exec.os, "defpath", str(def_dir))
    monkeypatch.setenv("PATH", "")
    assert _host_exec.which_native("git") is None
    assert _host_exec.which_native("git", path=".") == str(cwd_dir / "git")
    monkeypatch.delenv("PATH", raising=False)
    assert _host_exec.which_native("git") == str(def_dir / "git")


def test_which_native_skips_pe_and_preserves_timeout_on_posix_and_windows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    win_dir = tmp_path / "win_bin"
    win_dir.mkdir()
    git_exe = win_dir / "git.exe"
    git_exe.write_bytes(b"MZ" + b"\x00" * 62)

    monkeypatch.setattr(_host_exec, "_IS_WINDOWS_OVERRIDE", True)
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    resolved_win = _host_exec.which_native("git", path=f'"{win_dir}"')
    assert resolved_win is not None and resolved_win.lower().endswith("git.exe")
    with mock.patch("mindie_profiler._host_exec.os.stat", side_effect=TimeoutError("win stat deadline")):
        with pytest.raises(TimeoutError, match="win stat deadline"):
            _host_exec.which_native("git", path=str(win_dir))

    monkeypatch.setattr(_host_exec, "_IS_WINDOWS_OVERRIDE", None)
    if os.name == "nt":
        return

    pe_dir = tmp_path / "mnt_c_bin"
    lin_dir = tmp_path / "usr_bin"
    pe_dir.mkdir()
    lin_dir.mkdir()
    pe_git = pe_dir / "git"
    pe_bytes = bytearray(128)
    pe_bytes[0:2] = b"MZ"
    pe_bytes[0x3C:0x40] = (64).to_bytes(4, "little")
    pe_bytes[64:68] = b"PE\x00\x00"
    pe_git.write_bytes(bytes(pe_bytes))
    pe_git.chmod(0o755)
    elf_git = lin_dir / "git"
    elf_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    elf_git.chmod(0o755)

    assert _host_exec.which_native("git", path=f"{pe_dir}:{lin_dir}") == str(elf_git)
    assert _host_exec.which_native("git", path=str(pe_dir)) is None
    with mock.patch("mindie_profiler._host_exec.os.stat", side_effect=TimeoutError("posix stat deadline")):
        with pytest.raises(TimeoutError, match="posix stat deadline"):
            _host_exec.which_native("git", path=str(lin_dir))


def test_tensor_cast_run_git_executes_resolved_native_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tensor_cast_provider, "which_native", lambda cmd: "/usr/bin/git")
    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="a" * 40 + "\n", stderr="")

    monkeypatch.setattr(tensor_cast_provider.subprocess, "run", fake_run)
    commit = tensor_cast_provider.read_source_commit(tmp_path)
    assert commit == "a" * 40
    assert isinstance(captured["cmd"], list) and captured["cmd"][0] == "/usr/bin/git"
    assert captured["kwargs"]["encoding"] == "utf-8"


def _pid_alive(pid: int) -> bool:
    if os.name == "nt":
        res = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5.0,
            check=False,
            **_host_exec.no_window_kwargs(),
        )
        return f'"{pid}"' in res.stdout
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def test_terminate_process_group_reaps_parent_and_child() -> None:
    code = (
        "import subprocess, sys, time\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
        "print(child.pid, flush=True)\n"
        "time.sleep(30)\n"
    )
    proc = subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        **({"creationflags": _host_exec.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}),
    )
    child_pid: int | None = None
    try:
        assert proc.stdout is not None
        line = proc.stdout.readline().strip()
        child_pid = int(line)
        receipt = vllm_online_evidence.terminate_process_group(proc, grace_s=3.0, kill_timeout_s=3.0)
        assert receipt["term_sent"] is True
        assert proc.poll() is not None
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline and _pid_alive(child_pid):
            time.sleep(0.05)
        assert not _pid_alive(child_pid)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3.0)
        if child_pid is not None and _pid_alive(child_pid):
            try:
                os.kill(child_pid, 9)
            except OSError:
                pass
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()


def test_capture_shm_controller_lock_cleanup_on_unlock_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    shm_file = tmp_path / "cap_test.shm"
    session = native_capture_shm.CaptureShmSession(
        shm_file, create=True, unlink_on_close=True, exclusive_controller=True
    )
    lock_key = session._ctl_lock_key
    assert lock_key in native_capture_shm._ACTIVE_CONTROLLERS
    closed_fds: list[int] = []
    real_close = os.close

    def tracking_close(fd: int) -> None:
        closed_fds.append(fd)
        real_close(fd)

    monkeypatch.setattr(native_capture_shm.os, "close", tracking_close)
    if os.name == "nt":
        import msvcrt

        monkeypatch.setattr(msvcrt, "locking", mock.Mock(side_effect=TimeoutError("unlock timeout")))
    else:
        import fcntl

        monkeypatch.setattr(fcntl, "flock", mock.Mock(side_effect=TimeoutError("unlock timeout")))
    with pytest.raises(TimeoutError, match="unlock timeout"):
        session.close()
    assert len(closed_fds) >= 2
    assert lock_key not in native_capture_shm._ACTIVE_CONTROLLERS


def test_kernel_inventory_invalidates_archive_before_propagating_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = tmp_path / "sample.tar"
    archive.write_bytes(b"v1")
    csv_header = "Device_id,Name,Type,Start Time(us),Duration(us),Stream Id,Task Id,Context Id\n"
    row_a = csv_header + "0,MatMulV2,MatMul,10.0,5.0,1,1,1\n"
    row_b = csv_header + "0,Add,Vector,20.0,3.0,1,2,1\n"
    monkeypatch.setattr(kernel_inventory, "discover", lambda roots: [archive])
    monkeypatch.setattr(
        kernel_inventory,
        "source_streams",
        lambda p: [("a.csv", io.StringIO(row_a)), ("b.csv", io.StringIO(row_b))],
    )
    out_dir = tmp_path / "out"
    kernel_inventory.build_inventory({"roots": [str(archive)]}, out_dir, timeout_s=5.0)

    archive.write_bytes(b"v2-longer")

    def interrupted_streams(_p: Path):
        yield ("a.csv", io.StringIO(csv_header + "0,MatMulV2,MatMul,10.0,9.0,1,1,1\n"))
        raise TimeoutError("inventory deadline")

    monkeypatch.setattr(kernel_inventory, "source_streams", interrupted_streams)
    with pytest.raises(TimeoutError, match="inventory deadline"):
        kernel_inventory.build_inventory({"roots": [str(archive)]}, out_dir, timeout_s=5.0)

    with sqlite3.connect(out_dir / "kernels.sqlite") as conn:
        statuses = dict(conn.execute("SELECT member, status FROM sources").fetchall())
        cost_rows = conn.execute("SELECT COUNT(*) FROM costs").fetchone()[0]
    assert statuses == {"a.csv": "failed", "b.csv": "failed"}
    assert cost_rows == 0
