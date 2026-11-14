"""Regression tests for Windows CP936/CREATE_NO_WINDOW, WSL2 native lookup, and TimeoutError honesty."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from mindie_profiler import _host_exec, kernel_inventory, tensor_cast_provider, vllm_online_evidence


def test_normalize_git_repo_arg_strips_extended_prefix_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_host_exec, "_IS_WINDOWS", True)
    assert _host_exec.normalize_git_repo_arg(r"\\?\C:\Users\张三\repo") == r"C:\Users\张三\repo"
    assert _host_exec.normalize_git_repo_arg(r"\\?\UNC\server\share\repo") == r"\\server\share\repo"
    vol = r"\\?\Volume{01234567-89ab-cdef-0123-456789abcdef}\repo"
    assert _host_exec.normalize_git_repo_arg(vol) == vol
    trailing = r"\\?\C:\Users\张三\repo."
    assert _host_exec.normalize_git_repo_arg(trailing) == trailing


def test_host_exec_symlink_dotdot_large_pe_and_path_edge_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name == "nt":
        pytest.skip("POSIX/WSL2 symlink/mountinfo and PATH edge-case test")
    ext4_dir = tmp_path / "ext4" / "sub"
    drv_dir = tmp_path / "mnt_c"
    ext4_dir.mkdir(parents=True)
    drv_dir.mkdir()

    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        f"30 1 8:1 / {tmp_path} rw,relatime - ext4 /dev/sdb rw\n"
        f"40 30 0:35 / {drv_dir.resolve()} rw,noatime - 9p drvfs rw,aname=drvfs\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(_host_exec, "_MOUNTINFO_PATH", str(mountinfo))
    link = ext4_dir / "escape"
    link.symlink_to(drv_dir / "nested")
    assert _host_exec.is_wsl_drvfs(f"{link}/../tool") is True

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
    for folder in (cwd_dir, def_dir):
        tool = folder / "git"
        tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        tool.chmod(0o755)
    monkeypatch.chdir(cwd_dir)
    monkeypatch.setattr(_host_exec.os, "defpath", str(def_dir))
    monkeypatch.setenv("PATH", "")
    assert _host_exec.which_native("git") is None
    assert _host_exec.which_native("git", path=".") == str(cwd_dir / "git")
    monkeypatch.delenv("PATH", raising=False)
    assert _host_exec.which_native("git") == str(def_dir / "git")


def test_which_native_skips_pe_and_drvfs_and_preserves_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if os.name == "nt":
        pytest.skip("POSIX/WSL2 native binary discovery test")
    win_dir = tmp_path / "mnt_c_bin"
    lin_dir = tmp_path / "usr_bin"
    win_dir.mkdir()
    lin_dir.mkdir()

    pe_git = win_dir / "git"
    pe_bytes = bytearray(128)
    pe_bytes[0:2] = b"MZ"
    pe_bytes[0x3C:0x40] = (64).to_bytes(4, "little")
    pe_bytes[64:68] = b"PE\x00\x00"
    pe_git.write_bytes(bytes(pe_bytes))
    pe_git.chmod(0o755)

    elf_git = lin_dir / "git"
    elf_git.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    elf_git.chmod(0o755)

    resolved = _host_exec.which_native("git", path=f"{win_dir}:{lin_dir}")
    assert resolved == str(elf_git)
    assert _host_exec.which_native("git", path=str(win_dir)) is None

    with mock.patch.object(Path, "stat", side_effect=TimeoutError("stat deadline")):
        with pytest.raises(TimeoutError, match="stat deadline"):
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


def test_terminate_process_group_works_on_current_platform() -> None:
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **({"creationflags": _host_exec.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}),
    )
    try:
        receipt = vllm_online_evidence.terminate_process_group(proc, grace_s=2.0, kill_timeout_s=3.0)
        assert receipt["term_sent"] is True
        assert proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3.0)
        if proc.stdout:
            proc.stdout.close()
        if proc.stderr:
            proc.stderr.close()


def test_kernel_inventory_propagates_timeout_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    archive = tmp_path / "sample.tar"
    archive.write_bytes(b"")
    monkeypatch.setattr(kernel_inventory, "discover", lambda roots: [archive])
    monkeypatch.setattr(kernel_inventory, "source_streams", mock.Mock(side_effect=TimeoutError("inventory deadline")))
    with pytest.raises(TimeoutError, match="inventory deadline"):
        kernel_inventory.build_inventory({"roots": [str(archive)]}, tmp_path / "out", timeout_s=1.0)
