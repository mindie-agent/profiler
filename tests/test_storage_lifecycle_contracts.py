"""Tier-0/1 retention, cache-boundedness, and temp-workspace lifecycle.

[Role]
  Guard the storage lifecycle contract: a timed-out shim compile never leaks a
  partial object, the shim cache stays bounded, the repro CAS/diff roots are
  pruned without touching active state, trace sidecar rebuilds clean up their
  private database, and probe runs leave no temporary directory behind.
  Deterministic thread interleavings and fault injection cover symlink/reparse
  escapes, registration-vs-eviction TOCTOU, and atomic trace publication.

[Invariants]
  * Tests read only their own fresh roots; the pytest reaper owns cleanup.
  * No live NPU, network, or host ``$HOME`` access.

[Timeouts & Locks]
  Bounded filesystem work; events order threads instead of sleeps.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` and registered ``/tmp`` short roots.
"""

from __future__ import annotations

from dataclasses import replace
import errno
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import uuid

import pytest

from mindie_profiler import (
    cann_abi,
    repro_retention,
    repro_storage,
    sources_trace,
    storage_locks,
)
from mindie_profiler.events import ProfilerSchemaError
from mindie_profiler.fabric_probe import build_fabric_probe_plan
from mindie_sim import diff_trace

import nr_s6_round4_probe as probe
import temp_workspaces as temp_workspaces_module
from temp_workspaces import (
    live_temp_workspaces,
    make_temp_workspace,
    release_temp_workspace,
)


def _shim_install() -> cann_abi.Cann9Installation:
    return cann_abi.Cann9Installation(
        cann_root=Path("/opt/fake-cann"),
        arch_dir=Path("/opt/fake-cann/aarch64-linux"),
        arch="aarch64",
        version="9.0.0",
        major_version=9,
        minor_version=0,
        innerversion="fake",
        acl_include_dir=Path("/opt/fake-cann/aarch64-linux/include"),
        mspti_include_dir=Path("/opt/fake-cann/tools/mspti/include"),
        libascendcl_so=Path("/opt/fake-cann/aarch64-linux/lib64/libascendcl.so"),
        libmsprofiler_so=Path("/opt/fake-cann/aarch64-linux/lib64/libmsprofiler.so"),
        libmspti_so=Path("/opt/fake-cann/tools/mspti/lib64/libmspti.so"),
        msprof_bin=Path("/opt/fake-cann/tools/profiler/bin/msprof"),
    )


def _fake_compiler(monkeypatch, *, timeout: bool) -> None:
    def run(cmd, **kwargs):
        Path(cmd[cmd.index("-o") + 1]).write_bytes(b"\x7fELF fake shim")
        if timeout:
            raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1.0))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("mindie_profiler._host_exec.which_native", lambda _name: "/usr/bin/gcc")
    monkeypatch.setattr(subprocess, "run", run)


def test_shim_timeout_removes_unpublished_temporary(tmp_path, monkeypatch):
    cache = tmp_path / "shim"
    cache.mkdir()
    _fake_compiler(monkeypatch, timeout=True)
    with pytest.raises(TimeoutError, match="timeout_s"):
        cann_abi.ensure_capture_shim_binary(_shim_install(), cache_root=cache, timeout_s=0.5)
    assert not list(cache.glob("*.tmp.*"))
    assert not list(cache.glob(".*.tmp.*"))
    assert not list(cache.glob("libmindie_cann9_capture_*.so"))


def test_shim_cache_is_bounded_and_sweeps_stale_temporaries(tmp_path, monkeypatch):
    cache = tmp_path / "shim"
    cache.mkdir()
    now = time.time()
    superseded = []
    for index in range(cann_abi.SHIM_CACHE_MAX_ENTRIES + 3):
        so_path = cache / f"libmindie_cann9_capture_fast_9.0.{index}_aarch64-linux_{index:020x}.so"
        so_path.write_bytes(b"stale shim")
        stamp = now - (60 - index) * 60
        os.utime(so_path, (stamp, stamp))
        (cache / f".{so_path.name}.lock").write_bytes(b"")
        superseded.append(so_path)
    stale = cache / ".libmindie_cann9_capture_deep_9.0.0_aarch64-linux_old.so.tmp.1234"
    stale.write_bytes(b"partial")
    old = now - cann_abi.SHIM_TMP_STALE_S - 60
    os.utime(stale, (old, old))
    inflight = cache / ".libmindie_cann9_capture_deep_9.0.0_aarch64-linux_new.so.tmp.9999"
    inflight.write_bytes(b"in progress")

    _fake_compiler(monkeypatch, timeout=False)
    published = cann_abi.ensure_capture_shim_binary(_shim_install(), cache_root=cache)

    survivors = sorted(cache.glob("libmindie_cann9_capture_*.so"))
    assert published.is_file() and published.stat().st_size > 0
    assert len(survivors) == cann_abi.SHIM_CACHE_MAX_ENTRIES == 8
    assert published in survivors
    assert superseded[0] not in survivors
    assert superseded[-1] in survivors
    # Lock identity is never split: both the stable build lock and legacy
    # per-variant lock files survive eviction untouched.
    assert (cache / cann_abi._BUILD_LOCK_NAME).is_file()
    assert all((cache / f".{victim.name}.lock").exists() for victim in superseded)
    assert not stale.exists()
    assert inflight.exists()


def _age(path: Path, days: float) -> None:
    stamp = time.time() - days * 86400.0
    os.utime(path, (stamp, stamp))


def _cas_slot(root: Path, name: str, days: float) -> Path:
    entry = root / name
    entry.mkdir(parents=True)
    (entry / "repro.py").write_text(f"# {name}\n", encoding="utf-8")
    (entry / "manifest.json").write_text("{}\n", encoding="utf-8")
    _age(entry / "repro.py", days)
    _age(entry / "manifest.json", days)
    return entry


def _diff_slot(root: Path, name: str, days: float) -> Path:
    entry = root / "diff" / name
    entry.mkdir(parents=True)
    (entry / "diff.json").write_text("{}\n", encoding="utf-8")
    _age(entry / "diff.json", days)
    return entry


_REUSE_TRACE = {"total_ms": 2, "ops": [{"name": "R14", "duration_ms": 2}]}


def _diff_payload(trace: dict) -> bytes:
    """Byte-identical payload for ``mindie_sim.diff_trace._persist_diff``."""

    payload = diff_trace.attribute_diff(trace, trace)
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def test_prune_repro_storage_bounds_age_and_count_while_protecting_active(
        tmp_path, monkeypatch):
    root = make_temp_workspace("mpr15-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    staged = repro_storage.stage_artifacts(
        "#!/usr/bin/env python3\nprint('active')\n",
        {"schema": "mindie-op-repro/1"},
        output_dir=tmp_path / "mirror",
    )
    assert staged["status"] == "delivered"
    _age(Path(staged["short_artifact_path"]), 40.0)
    _age(Path(staged["short_manifest_path"]), 40.0)

    stale = [_cas_slot(root, f"{index:012x}", days)
             for index, days in enumerate((30.0, 20.0, 10.0, 3.0, 1.0))]
    pinned = _cas_slot(root, "bbbbbbbbbbbb", 40.0)
    repro_storage._remember_inodes(pinned / "repro.py", pinned / "manifest.json")
    foreign = _cas_slot(root, "cccccccccccc", 40.0)
    (foreign / "payload.bin").write_bytes(b"not ours")

    diff_expired = _diff_slot(root, "expired", 20.0)
    diff_excess = _diff_slot(root, "excess", 5.0)
    diff_recent = _diff_slot(root, "recent", 1.0)
    diff_locked = _diff_slot(root, "locked", 30.0)
    (root / "diff" / ".locked.lock").write_bytes(b"")

    removed = repro_retention.prune_repro_storage(root, max_entries=2, max_age_days=14)

    assert removed == 4
    assert not stale[0].exists() and not stale[1].exists() and not stale[2].exists()
    assert stale[3].exists() and stale[4].exists()
    assert pinned.exists() and (pinned / "repro.py").exists()
    assert Path(staged["short_artifact_path"]).is_file()
    assert foreign.exists() and (foreign / "payload.bin").is_file()
    assert not diff_expired.exists()
    assert diff_excess.exists() and diff_recent.exists() and diff_locked.exists()
    protected_inodes = repro_storage._protected_inodes()
    assert repro_storage._inode_of(staged["short_artifact_path"]) in protected_inodes
    assert repro_storage._inode_of(pinned / "repro.py") in protected_inodes


def test_stage_artifacts_prunes_expired_slots_opportunistically(tmp_path, monkeypatch):
    root = make_temp_workspace("mpr15o-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    expired = _cas_slot(root, "dddddddddddd", 40.0)
    script = "#!/usr/bin/env python3\nprint('fresh')\n"
    result = repro_storage.stage_artifacts(
        script,
        {"schema": "mindie-op-repro/1", "script_sha256": repro_storage.artifact_id(script)},
        output_dir=tmp_path / "mirror",
    )
    assert result["status"] == "delivered"
    assert not expired.exists()
    assert Path(result["short_artifact_path"]).is_file()
    assert repro_storage.resolve_repro_artifact(result["artifact_id"])["resolved"] is True


def test_failed_index_build_removes_private_database_and_sidecars(tmp_path):
    trace = tmp_path / "trace_view.json"
    trace.write_text('[{"name": "kernel_0", "ts": 0},', encoding="utf-8")
    with pytest.raises(ProfilerSchemaError):
        sources_trace.build_trace_index(trace)
    index = sources_trace.index_path_for(trace)
    assert not index.exists()
    assert not Path(f"{index}-wal").exists()
    assert not Path(f"{index}-shm").exists()
    assert not list(tmp_path.glob(f".{index.name}.tmp.*"))
    assert not list(tmp_path.glob(".*.tmp.*"))


def test_open_index_closes_connection_when_a_pragma_fails(tmp_path, monkeypatch):
    database = tmp_path / "sidecar.sqlite3"
    broker = SimpleNamespace(closed=False)

    def broken_execute(*args, **kwargs):
        raise sqlite3.OperationalError("pragma failed")

    broker.execute = broken_execute
    broker.close = lambda: broker.__setattr__("closed", True)
    monkeypatch.setattr(sources_trace.sqlite3, "connect", lambda *args, **kwargs: broker)
    with pytest.raises(sqlite3.OperationalError, match="pragma failed"):
        sources_trace._open_index(database)
    assert broker.closed is True


def test_index_wal_is_bounded_and_checkpointed_on_close(tmp_path):
    database = tmp_path / "sidecar.sqlite3"
    con = sources_trace._open_index(database)
    try:
        assert con.execute("PRAGMA journal_size_limit").fetchone()[0] == (
            sources_trace.WAL_JOURNAL_SIZE_LIMIT)
        con.execute("CREATE TABLE payload(value BLOB)")
        con.execute("INSERT INTO payload VALUES (?)", (b"x" * 200_000,))
        con.commit()
    finally:
        sources_trace._close_index(con)
    wal = Path(f"{database}-wal")
    assert not wal.exists() or wal.stat().st_size <= sources_trace.WAL_JOURNAL_SIZE_LIMIT


def test_successful_index_build_leaves_a_bounded_wal_and_valid_sidecar(tmp_path):
    trace = tmp_path / "trace_view.json"
    trace.write_text(
        '[{"name": "a", "ts": 0, "dur": 1}, {"name": "b", "ts": 2, "dur": 1}]',
        encoding="utf-8",
    )
    facts = sources_trace.build_trace_index(trace)
    index = Path(facts["index_path"])
    assert facts["rebuilt"] is True and facts["event_count"] == 2
    assert index.is_file()
    wal = Path(f"{index}-wal")
    assert not wal.exists() or wal.stat().st_size <= sources_trace.WAL_JOURNAL_SIZE_LIMIT
    assert sources_trace.index_is_valid(index, trace) is True
    rebuilt = sources_trace.build_trace_index(trace, force=True)
    assert rebuilt["rebuilt"] is True
    index_wal = Path(f"{rebuilt['index_path']}-wal")
    assert not index_wal.exists() or index_wal.stat().st_size <= sources_trace.WAL_JOURNAL_SIZE_LIMIT


def _probe_plan():
    return build_fabric_probe_plan(
        world_size=2, ranks_per_node=2, sizes=[4096], ops=["all_reduce"],
        iterations=1, warmup=0, duration_s=60.0,
        topology={"tiers": [{"tier": "intra_node_hccs", "ranks": [0, 1],
                             "protocol": "HCCS"}]})


def _private_tempdir(tmp_path, monkeypatch) -> Path:
    """Point the effective ``TMPDIR`` at a test-private directory."""

    private = tmp_path / "tmpdir"
    private.mkdir()
    monkeypatch.setenv("TMPDIR", str(private))
    monkeypatch.setattr(tempfile, "tempdir", str(private))
    return private


def test_run_ranks_reclaims_its_workspace_without_touching_other_temp_entries(
        tmp_path, monkeypatch):
    private = _private_tempdir(tmp_path, monkeypatch)
    world, results, workspace = probe.run_ranks(_probe_plan())
    try:
        assert world.errors == {}
        assert sorted(results) == [0, 1]
        assert Path(workspace).is_dir()
        assert Path(workspace).parent == private
        assert workspace in live_temp_workspaces()
    finally:
        release_temp_workspace(workspace)
    assert not Path(workspace).exists()
    assert list(private.iterdir()) == []


def test_run_ranks_releases_the_workspace_when_thread_startup_fails(
        tmp_path, monkeypatch):
    private = _private_tempdir(tmp_path, monkeypatch)
    created = []
    original_make = probe.make_temp_workspace

    def tracking_make(prefix, **kwargs):
        path = original_make(prefix, **kwargs)
        created.append(Path(path))
        return path

    def broken_thread(*_args, **_kwargs):
        raise RuntimeError("thread startup failed")

    monkeypatch.setattr(probe, "make_temp_workspace", tracking_make)
    monkeypatch.setattr(probe.threading, "Thread", broken_thread)
    with pytest.raises(RuntimeError, match="thread startup failed"):
        probe.run_ranks(_probe_plan())
    assert created and not created[0].exists()
    assert str(created[0]) not in live_temp_workspaces()
    assert list(private.iterdir()) == []


# ------------------------------------------------ symlink / reparse confinement
def _link_directory_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except (NotImplementedError, OSError):
        pytest.skip("directory symlinks are unavailable")


def _link_file_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("file symlinks are unavailable")


def test_prune_refuses_symlinked_root_and_diff_targets(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    external_cas = _cas_slot(external, "aaaaaaaaaaaa", 40.0)
    external_diff = external / "old_diff"
    external_diff.mkdir()
    (external_diff / "diff.json").write_text("{}\n", encoding="utf-8")
    _age(external_diff / "diff.json", 40.0)

    root = tmp_path / "root"
    root.mkdir()
    _link_directory_or_skip(root / "diff", external)

    # A symlinked root must not launder a real ``diff`` directory underneath it.
    real_root = tmp_path / "real_root"
    real_root.mkdir()
    nested_diff = real_root / "diff" / "old_nested"
    nested_diff.mkdir(parents=True)
    (nested_diff / "diff.json").write_text("{}\n", encoding="utf-8")
    _age(nested_diff / "diff.json", 40.0)
    link_root = tmp_path / "root_link"
    _link_directory_or_skip(link_root, real_root)

    assert repro_retention.prune_repro_storage(link_root, max_entries=0, max_age_days=0) == 0
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 0
    assert (external_cas / "repro.py").is_file()
    assert (external_cas / "manifest.json").is_file()
    assert (external_diff / "diff.json").is_file()
    assert (nested_diff / "diff.json").is_file()
    assert (root / "diff").is_symlink()


@pytest.mark.parametrize("attribute", ["st_reparse_tag", "st_file_attributes"])
def test_prune_skips_windows_reparse_entries_without_isjunction(tmp_path, monkeypatch, attribute):
    root = tmp_path / "cas"
    root.mkdir()
    junction = _cas_slot(root, "dddddddddddd", 40.0)
    real_lstat = os.lstat

    def fake_lstat(target, *args, **kwargs):
        if args or kwargs:
            return real_lstat(target, *args, **kwargs)
        info = real_lstat(target)
        if Path(target) != junction:
            return info
        values = {
            "st_mode": stat.S_IFDIR,
            "st_dev": info.st_dev,
            "st_ino": info.st_ino,
            "st_mtime": info.st_mtime,
            "st_size": info.st_size,
        }
        if attribute == "st_reparse_tag":
            values["st_reparse_tag"] = 0xA0000003
        else:
            values["st_file_attributes"] = 0x400
        return SimpleNamespace(**values)

    monkeypatch.delattr(os.path, "isjunction", raising=False)
    monkeypatch.setattr(repro_retention.os, "lstat", fake_lstat)

    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 0
    assert (junction / "repro.py").is_file()
    assert (junction / "manifest.json").is_file()


def test_prune_partial_symlink_leaf_keeps_regular_sibling(tmp_path):
    root = tmp_path / "cas"
    root.mkdir()
    entry = root / "eeeeeeeeeeee"
    entry.mkdir()
    (entry / "repro.py").write_text("# regular leaf\n", encoding="utf-8")
    _age(entry / "repro.py", 40.0)
    external = tmp_path / "external-manifest.json"
    external.write_text("{}\n", encoding="utf-8")
    _link_file_or_skip(entry / "manifest.json", external)

    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 0
    assert (entry / "repro.py").is_file()
    assert (entry / "manifest.json").is_symlink()
    assert external.is_file()


@pytest.mark.parametrize("kind", ["cas", "diff"])
@pytest.mark.parametrize("mode", ["symlink", "reparse"])
def test_prune_never_traverses_symlinked_or_reparse_trash(tmp_path, monkeypatch, kind, mode):
    root = tmp_path / "root"
    root.mkdir()
    base = root if kind == "cas" else root / "diff"
    base.mkdir(exist_ok=True)
    leaves = repro_retention._CAS_LEAVES if kind == "cas" else repro_retention._DIFF_LEAVES
    external = tmp_path / f"external-{kind}"
    external.mkdir()
    for name in leaves:
        (external / name).write_text("{}\n", encoding="utf-8")
    trash = base / ".trash-evil"
    if mode == "symlink":
        _link_directory_or_skip(trash, external)
    else:
        trash.mkdir()
        for name in leaves:
            (trash / name).write_text("{}\n", encoding="utf-8")
        real_lstat = os.lstat

        def fake_lstat(target, *args, **kwargs):
            if args or kwargs:
                return real_lstat(target, *args, **kwargs)
            info = real_lstat(target)
            if Path(target) != trash:
                return info
            return SimpleNamespace(
                st_mode=stat.S_IFDIR,
                st_dev=info.st_dev,
                st_ino=info.st_ino,
                st_mtime=info.st_mtime,
                st_size=info.st_size,
                st_file_attributes=0x400,
            )

        monkeypatch.delattr(os.path, "isjunction", raising=False)
        monkeypatch.setattr(repro_retention.os, "lstat", fake_lstat)

    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 0
    assert all((external / name).is_file() for name in leaves)
    assert repro_retention._remove_trash(trash, leaves) == 0
    assert all((external / name).is_file() for name in leaves)
    if mode == "symlink":
        assert trash.is_symlink()
    else:
        assert all((trash / name).is_file() for name in leaves)


def test_prune_rechecks_slot_registered_after_snapshot(tmp_path, monkeypatch):
    root = tmp_path / "cas"
    root.mkdir()
    entry = _cas_slot(root, "ffffffffffff", 40.0)
    scanned = threading.Event()
    registration_visible = threading.Event()
    allow_remember = threading.Event()
    original_age = repro_retention._entry_age_seconds
    original_remember = repro_storage._remember_inodes

    def hooked_age(candidate, leaves, now):
        if candidate == entry and not scanned.is_set():
            scanned.set()
            assert registration_visible.wait(5.0)
        return original_age(candidate, leaves, now)

    def held_remember(*paths):
        registration_visible.set()
        assert allow_remember.wait(5.0)
        return original_remember(*paths)

    monkeypatch.setattr(repro_retention, "_entry_age_seconds", hooked_age)
    monkeypatch.setattr(repro_storage, "_remember_inodes", held_remember)
    outcome: dict[str, object] = {}

    def prune():
        outcome["removed"] = repro_retention.prune_repro_storage(
            root, max_entries=repro_retention.PRUNE_MAX_ENTRIES, max_age_days=1)

    def register():
        assert scanned.wait(5.0)
        outcome["indexed"] = repro_storage._register({
            "artifact_id": "sha256:" + "f" * 64,
            "artifact_path": str(entry / "repro.py"),
            "manifest_path": str(entry / "manifest.json"),
            "script_sha256": "sha256:" + "f" * 64,
        })

    pruner = threading.Thread(target=prune)
    registrar = threading.Thread(target=register)
    pruner.start()
    registrar.start()
    assert registration_visible.wait(5.0)
    pruner.join(5.0)
    allow_remember.set()
    registrar.join(5.0)

    assert not pruner.is_alive() and not registrar.is_alive()
    assert outcome["removed"] == 0
    assert outcome["indexed"] is True
    assert (entry / "repro.py").is_file()
    assert (entry / "manifest.json").is_file()
    assert repro_storage._inode_of(entry / "repro.py") in repro_storage._PROTECTED_INODES
    assert not list(root.glob(".trash-*"))


_RETENTION_LOCK_HOLDER = """
import sys
from pathlib import Path

from mindie_profiler.storage_locks import exclusive_lock

with exclusive_lock(Path(sys.argv[1]) / ".retention.lock", blocking=True):
    print("held", flush=True)
    sys.stdin.readline()
"""


def test_prune_skips_when_another_process_holds_retention_lock(tmp_path):
    root = tmp_path / "cas"
    root.mkdir()
    entry = _cas_slot(root, "121212121212", 40.0)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH", "")])
    process = subprocess.Popen(
        [sys.executable, "-c", _RETENTION_LOCK_HOLDER, str(root)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "held"
        assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 0
        assert (entry / "repro.py").is_file()
        assert (entry / "manifest.json").is_file()
    finally:
        assert process.stdin is not None
        process.stdin.write("\n")
        process.stdin.flush()
        process.stdin.close()
        assert process.wait(timeout=10) == 0

    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=0) == 1
    assert not entry.exists()


def test_backdated_write_marker_survives_a_live_guard_and_blocks_eviction(tmp_path):
    root = make_temp_workspace("mpr15g-", base="/tmp")
    entry = _cas_slot(root, "343434343434", 40.0)
    with repro_retention.retention_write_guard(entry):
        markers = [child for child in root.iterdir() if child.name.startswith(".write-")]
        assert len(markers) == 1
        stamp = time.time() - 7200.0
        os.utime(markers[0], (stamp, stamp))
        assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0
        assert markers[0].is_file()
        assert (entry / "repro.py").is_file() and (entry / "manifest.json").is_file()
    assert not [child for child in root.iterdir() if child.name.startswith(".write-")]
    assert time.time() - (entry / "repro.py").stat().st_mtime < 60.0
    # The successful guard left a PID lease for this live process, so the slot
    # stays protected until the owner is gone.
    leases = list(root.glob(".pin-*.lock"))
    assert len(leases) == 1
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0
    leases[0].unlink()
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 1
    assert not entry.exists()


_SLOT_REUSE_CHILD = r"""
import os
import sys
from pathlib import Path

from mindie_profiler import repro_storage

root = Path(os.environ["MINDIE_REPRO_SHORT_ROOT"])
kind = sys.argv[1]
if kind == "cas":
    script = "#!/usr/bin/env python3\nprint('reused')\n"
    result = repro_storage.stage_artifacts(script, {"schema": "mindie-op-repro/1"})
    assert result["status"] == "delivered", result
else:
    from mindie_sim.diff_trace import call_mcp_tool
    trace = {"total_ms": 2, "ops": [{"name": "R14", "duration_ms": 2}]}
    result = call_mcp_tool({"predicted": trace, "captured": trace})
    assert result["persisted"] is True, result
    entry = Path(result["artifact_path"]).parent
print("ready", flush=True)
sys.stdin.readline()
"""


def test_lease_reader_sees_a_live_tail_past_the_legacy_window(tmp_path, monkeypatch):
    entry = tmp_path / "slot"
    entry.mkdir()
    (entry / "diff.json").write_text("{}\n", encoding="utf-8")
    pin = entry.with_name(".pin-slot.lock")
    dead = b"".join(f"{900000 + index}\n".encode("ascii") for index in range(700))
    pin.write_bytes(dead + f"{os.getpid()}\n".encode("ascii"))
    assert pin.stat().st_size > 3600
    monkeypatch.setattr(repro_retention, "process_exited",
                        lambda pid: pid != os.getpid())

    assert repro_retention._slot_pinned(entry) is True
    assert pin.read_bytes() == f"{os.getpid()}\n".encode("ascii")


def test_unreadable_lease_is_conservatively_pinned(tmp_path, monkeypatch):
    entry = tmp_path / "slot"
    entry.mkdir()
    (entry / "diff.json").write_text("{}\n", encoding="utf-8")
    pin = entry.with_name(".pin-slot.lock")
    pin.write_bytes(f"{os.getpid()}\n".encode("ascii"))
    monkeypatch.setattr(repro_retention, "_lease_pids", lambda _fd: None)

    assert repro_retention._slot_pinned(entry) is True
    assert pin.is_file() and pin.read_bytes() == f"{os.getpid()}\n".encode("ascii")


def test_refresh_slot_touches_leaves_without_follow_symlinks_support(tmp_path, monkeypatch):
    entry = tmp_path / "slot"
    entry.mkdir()
    leaf = entry / "diff.json"
    leaf.write_text("{}\n", encoding="utf-8")
    old = time.time() - 40 * 86400.0
    os.utime(leaf, (old, old))
    monkeypatch.setattr(repro_retention.os, "supports_follow_symlinks", frozenset())

    repro_retention._refresh_slot(entry)

    assert time.time() - leaf.stat().st_mtime < 60.0


@pytest.mark.parametrize("code,exited", [(errno.EINVAL, True), (errno.EACCES, False)])
def test_windows_process_exit_uses_mapped_errno_without_winapi_constant(
        monkeypatch, code, exited):
    fake = SimpleNamespace(PROCESS_QUERY_LIMITED_INFORMATION=object())

    def deny(*_args):
        raise OSError(code, "mapped Win32 error")

    fake.OpenProcess = deny
    monkeypatch.setitem(sys.modules, "_winapi", fake)
    assert storage_locks._windows_process_exited(4242) is exited


def test_prune_reclaims_recycled_protected_inode_after_its_path_is_gone(tmp_path):
    root = tmp_path / "cas"
    root.mkdir()
    entry = _cas_slot(root, "dddddddddddd", 40.0)
    inode = repro_storage._inode_of(entry / "repro.py")
    stale = tmp_path / "gone" / "repro.py"
    with repro_storage._LOCK:
        repro_storage._PROTECTED_INODES.add(inode)
        repro_storage._PROTECTED_PATHS[inode] = {stale}
    try:
        assert repro_retention.prune_repro_storage(
            root, max_entries=0, max_age_days=0) == 1
        assert not entry.exists()
        assert inode not in repro_storage._PROTECTED_INODES
        assert inode not in repro_storage._PROTECTED_PATHS
    finally:
        repro_storage._PROTECTED_INODES.discard(inode)
        repro_storage._PROTECTED_PATHS.pop(inode, None)


def test_write_guard_drops_marker_when_seal_pin_times_out(tmp_path, monkeypatch):
    entry = tmp_path / "slot"
    entry.mkdir()
    (entry / "diff.json").write_text("{}\n", encoding="utf-8")
    sentinel = TimeoutError("seal pin timeout")
    pin_fds: list[int] = []
    marker_fds: list[int] = []
    original_hold = repro_retention._hold_pin
    original_create = repro_retention._create_marker
    original_write = os.write

    def recording_hold(target):
        original_hold(target)
        fd = repro_retention._PINS.get(repro_retention._pin_key(target))
        if fd is not None:
            pin_fds.append(fd)

    def recording_create(marker):
        fd = original_create(marker)
        if fd is not None:
            marker_fds.append(fd)
        return fd

    def failing_write(fd, data):
        if fd in pin_fds:
            raise sentinel
        return original_write(fd, data)

    monkeypatch.setattr(repro_retention, "_hold_pin", recording_hold)
    monkeypatch.setattr(repro_retention, "_create_marker", recording_create)
    monkeypatch.setattr(repro_retention.os, "write", failing_write)

    with pytest.raises(TimeoutError) as caught:
        with repro_retention.retention_write_guard(entry):
            pass

    assert caught.value is sentinel
    assert len(pin_fds) == 1 and len(marker_fds) == 1
    for fd in (*pin_fds, *marker_fds):
        with pytest.raises(OSError):
            os.fstat(fd)
    assert not list(tmp_path.glob(".write-*"))
    assert repro_retention._slot_pinned(entry) is False
    assert not list(tmp_path.glob(".pin-*.lock"))
    assert not repro_retention._PINS


@pytest.mark.parametrize("kind", ["cas", "diff"])
def test_live_child_slot_pin_survives_prune_until_the_child_exits(tmp_path, kind):
    root = make_temp_workspace("mpr15p-", base="/tmp")
    if kind == "cas":
        script = "#!/usr/bin/env python3\nprint('reused')\n"
        manifest = {"schema": "mindie-op-repro/1"}
        script_bytes, manifest_bytes = repro_storage._encode_pair(script, manifest)
        entry = root / repro_storage.artifact_id(script).split(":")[1][:12]
        entry.mkdir()
        (entry / "repro.py").write_bytes(script_bytes)
        (entry / "manifest.json").write_bytes(manifest_bytes)
        leaves = ("repro.py", "manifest.json")
    else:
        data = _diff_payload(_REUSE_TRACE)
        entry = root / "diff" / hashlib.sha256(data).hexdigest()[:12]
        entry.mkdir(parents=True)
        (entry / "diff.json").write_bytes(data)
        leaves = ("diff.json",)
    for name in leaves:
        _age(entry / name, 40.0)
    env = dict(os.environ)
    env["MINDIE_REPRO_SHORT_ROOT"] = str(root)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(Path(__file__).resolve().parents[1]), env.get("PYTHONPATH", "")])
    process = subprocess.Popen(
        [sys.executable, "-c", _SLOT_REUSE_CHILD, kind],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert process.stdout is not None
        assert process.stdout.readline().strip() == "ready"
        assert time.time() - (entry / leaves[0]).stat().st_mtime < 60.0
        assert list(entry.parent.glob(".pin-*.lock"))
        assert repro_retention.prune_repro_storage(
            root, max_entries=0, max_age_days=14) == 0
        assert all((entry / name).is_file() for name in leaves)
    finally:
        if process.poll() is None:
            if process.stdin is not None:
                process.stdin.write("\n")
                process.stdin.flush()
                process.stdin.close()
            try:
                assert process.wait(timeout=10) == 0
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
                raise
    assert process.stderr is not None and process.stderr.read() == ""
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 1
    assert not entry.exists()


# ------------------------------------------------------- concurrent build gates
def test_cann_abi_threaded_builds_keep_stable_lock_and_unique_temps(tmp_path, monkeypatch):
    cache = tmp_path / "shim"
    cache.mkdir()
    legacy_locks = []
    now = time.time()
    for index in range(cann_abi.SHIM_CACHE_MAX_ENTRIES + 2):
        so_path = cache / f"libmindie_cann9_capture_fast_9.0.{index}_aarch64-linux_{index:020x}.so"
        so_path.write_bytes(b"old shim")
        stamp = now - (60 - index) * 60
        os.utime(so_path, (stamp, stamp))
        lock_path = cache / f".{so_path.name}.lock"
        lock_path.write_bytes(b"")
        legacy_locks.append(lock_path)

    created: list[Path] = []
    records_lock = threading.Lock()

    def run(cmd, **kwargs):
        target = Path(cmd[cmd.index("-o") + 1])
        with records_lock:
            created.append(target)
        target.write_bytes(b"\x7fELF threaded shim")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("mindie_profiler._host_exec.which_native", lambda _name: "/usr/bin/gcc")
    monkeypatch.setattr(subprocess, "run", run)
    installs = [_shim_install(), replace(_shim_install(), version="9.0.1")]
    published, errors = [], []

    def build(install):
        try:
            published.append(cann_abi.ensure_capture_shim_binary(install, cache_root=cache))
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=build, args=(install,)) for install in installs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(15.0)

    assert not errors
    assert len(published) == 2 and all(path.is_file() for path in published)
    assert len({str(path) for path in created}) == 2
    assert not list(cache.glob(".*.tmp.*"))
    assert (cache / cann_abi._BUILD_LOCK_NAME).is_file()
    assert all(lock_path.is_file() for lock_path in legacy_locks)


def test_trace_index_threaded_rebuilds_use_unique_temporary_databases(tmp_path, monkeypatch):
    trace = tmp_path / "trace_view.json"
    trace.write_text('[{"name": "a", "ts": 0, "dur": 1}]', encoding="utf-8")
    builds: list[Path] = []
    original_build_path = sources_trace._build_path

    def recorded_build_path(index):
        path = original_build_path(index)
        builds.append(path)
        return path

    monkeypatch.setattr(sources_trace, "_build_path", recorded_build_path)
    results, errors = [], []

    def rebuild():
        try:
            results.append(sources_trace.build_trace_index(trace, force=True))
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=rebuild) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(15.0)

    index = sources_trace.index_path_for(trace)
    assert not errors and len(results) == 2
    assert len(builds) == 2 and len(set(builds)) == 2
    assert sources_trace.index_is_valid(index, trace) is True
    assert not list(tmp_path.glob(f".{index.name}.tmp.*"))


# ------------------------------------------------------------ trace fault gates
def _zombie_trace_build(index: Path, token: str) -> Path:
    candidate = index.parent / f".{index.name}.tmp.4242.{token}"
    candidate.write_bytes(b"stale trace build")
    old = time.time() - 7 * 3600
    os.utime(candidate, (old, old))
    return candidate


def test_stale_trace_build_with_fresh_wal_or_held_lock_is_not_swept(tmp_path):
    trace = tmp_path / "trace_view.json"
    trace.write_text("[]", encoding="utf-8")
    index = sources_trace.index_path_for(trace)
    fresh_wal = _zombie_trace_build(index, uuid.uuid4().hex)
    wal = Path(f"{fresh_wal}-wal")
    wal.write_bytes(b"fresh write")
    held = _zombie_trace_build(index, uuid.uuid4().hex)
    held_lock = Path(f"{held}.lock")
    started, release = threading.Event(), threading.Event()

    def holder():
        with storage_locks.exclusive_lock(held_lock, blocking=True):
            started.set()
            release.wait(5.0)

    thread = threading.Thread(target=holder)
    thread.start()
    assert started.wait(5.0)
    try:
        sources_trace.build_trace_index(trace, force=True)
    finally:
        release.set()
        thread.join(5.0)

    assert fresh_wal.exists()
    assert wal.exists()
    assert held.exists()
    assert held_lock.exists()

    sources_trace.build_trace_index(trace, force=True)
    assert not held.exists()
    assert not held_lock.exists()
    assert fresh_wal.exists()  # Its fresh WAL still proves recent activity.


@pytest.mark.skipif(os.name == "nt", reason="legacy PID liveness is uncertain on Windows")
def test_stale_legacy_tokenless_trace_build_is_swept_only_after_its_pid_exits(tmp_path):
    trace = tmp_path / "trace_view.json"
    trace.write_text("[]", encoding="utf-8")
    index = sources_trace.index_path_for(trace)
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait(timeout=10)
    dead_build = tmp_path / f".{index.name}.tmp.{dead.pid}"
    live_build = tmp_path / f".{index.name}.tmp.{os.getpid()}"
    old = time.time() - 7 * 3600
    for candidate in (dead_build, live_build):
        candidate.write_bytes(b"legacy stale trace build")
        os.utime(candidate, (old, old))
    sources_trace.build_trace_index(trace, force=True)
    assert not dead_build.exists()
    assert live_build.is_file()


@pytest.mark.parametrize("crash_after_replace", [False, True])
def test_trace_publish_interruption_never_pairs_new_database_with_old_wal(
        tmp_path, monkeypatch, crash_after_replace):
    trace = tmp_path / "trace_view.json"
    trace.write_text('[{"name": "a", "ts": 0, "dur": 1}]', encoding="utf-8")
    index = sources_trace.index_path_for(trace)
    con = sqlite3.connect(index)
    con.execute("CREATE TABLE legacy(value)")
    con.execute("INSERT INTO legacy VALUES ('old')")
    con.commit()
    con.close()
    stale_wal = Path(f"{index}-wal")
    stale_wal.write_bytes(b"stale old wal from the previous database")
    real_replace = os.replace

    def interrupted_replace(src, dst, *args, **kwargs):
        if Path(dst) == index and ".tmp." in Path(src).name:
            if crash_after_replace:
                real_replace(src, dst, *args, **kwargs)
            raise KeyboardInterrupt("simulated crash during trace publish")
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(sources_trace.os, "replace", interrupted_replace)
    with pytest.raises(KeyboardInterrupt):
        sources_trace.build_trace_index(trace, force=True)

    assert not stale_wal.exists()
    assert not (index.exists() and stale_wal.exists())
    assert index.exists() is crash_after_replace

    monkeypatch.setattr(sources_trace.os, "replace", real_replace)
    facts = sources_trace.build_trace_index(trace, force=True)
    assert facts["rebuilt"] is True
    assert sources_trace.index_is_valid(index, trace) is True
    assert not Path(f"{index}-wal").exists()
    assert not Path(f"{index}-shm").exists()


def test_temp_workspace_stays_registered_until_removal_is_confirmed(tmp_path, monkeypatch):
    path = temp_workspaces_module.make_temp_workspace("mpr15r-", base=tmp_path)
    real_rmtree = temp_workspaces_module.shutil.rmtree
    attempts: list[str] = []

    def flaky_rmtree(target, ignore_errors=False, **kwargs):
        attempts.append(str(target))
        if len(attempts) == 1:
            return  # Simulate transient Windows handle contention.
        return real_rmtree(target, ignore_errors=ignore_errors, **kwargs)

    monkeypatch.setattr(temp_workspaces_module.shutil, "rmtree", flaky_rmtree)
    temp_workspaces_module.release_temp_workspace(path)
    assert str(path) in temp_workspaces_module.live_temp_workspaces()

    released = temp_workspaces_module.release_all_temp_workspaces()
    assert released >= 1
    assert str(path) not in temp_workspaces_module.live_temp_workspaces()
    assert not path.exists()


def test_diff_reuse_rebuilds_when_slot_is_evicted_mid_read(monkeypatch):
    from mindie_sim.diff_trace import call_mcp_tool as diff_mcp

    root = make_temp_workspace("mpr15m-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    trace = {"total_ms": 2, "ops": [{"name": "MatMul", "duration_ms": 2}]}
    seeded = diff_mcp({"predicted": trace, "captured": trace})
    assert seeded["persisted"] is True
    artifact = Path(seeded["artifact_path"])
    assert artifact.is_file()
    for pin in (root / "diff").glob(".pin-*.lock"):
        pin.unlink()
    _age(artifact, 40.0)

    real_note = repro_retention.note_reused_slot
    evicted = []

    def evict_before_lease(leaf, expected_inode):
        if not evicted and leaf == artifact:
            evicted.append(repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14))
        return real_note(leaf, expected_inode)

    monkeypatch.setattr(repro_retention, "note_reused_slot", evict_before_lease)
    rebuilt = diff_mcp({"predicted": trace, "captured": trace})
    assert evicted == [1]
    assert rebuilt["persisted"] is True
    assert Path(rebuilt["artifact_path"]).is_file()
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0


def test_diff_reuse_short_lease_write_forces_rebuild_and_rolls_back_partial_pid(monkeypatch):
    from mindie_sim.diff_trace import call_mcp_tool as diff_mcp

    root = make_temp_workspace("mpr15s-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    trace = {"total_ms": 2, "ops": [{"name": "Softmax", "duration_ms": 2}]}
    seeded = diff_mcp({"predicted": trace, "captured": trace})
    artifact = Path(seeded["artifact_path"])
    pin = next((root / "diff").glob(".pin-*.lock"))
    pin.unlink()
    _age(artifact, 40.0)

    real_write = repro_retention.os.write
    calls = []
    short_fds: set[int] = set()

    def truncated_once(fd, data):
        payload = bytes(data)
        if not calls and payload == f"{os.getpid()}\n".encode("ascii"):
            short_fds.add(fd)
            calls.append(len(payload))
            return real_write(fd, payload[:1])
        if fd in short_fds and len(calls) == 1:
            calls.append(len(payload))
            return 0
        return real_write(fd, data)

    monkeypatch.setattr(repro_retention.os, "write", truncated_once)
    failed = diff_mcp({"predicted": trace, "captured": trace})
    assert len(calls) == 2
    assert failed["persisted"] is False
    assert not pin.exists()
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 1
    assert not artifact.exists()

    rebuilt = diff_mcp({"predicted": trace, "captured": trace})
    assert rebuilt["persisted"] is True
    assert Path(rebuilt["artifact_path"]).is_file()
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0


def test_diff_new_write_short_seal_pin_reports_delivery_failed_without_false_persisted(monkeypatch):
    from mindie_sim.diff_trace import call_mcp_tool as diff_mcp

    root = make_temp_workspace("mpr15p-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    trace = {"total_ms": 3, "ops": [{"name": "LayerNorm", "duration_ms": 3}]}

    real_write = repro_retention.os.write
    calls = []
    short_fds: set[int] = set()

    def short_on_seal(fd, data):
        payload = bytes(data)
        if not calls and payload == f"{os.getpid()}\n".encode("ascii"):
            short_fds.add(fd)
            calls.append(len(payload))
            return real_write(fd, payload[:2])
        if fd in short_fds and len(calls) == 1:
            calls.append(len(payload))
            return 0
        return real_write(fd, data)

    real_drop = repro_retention._drop_marker
    pruned_during_drop = []

    def drop_then_prune(marker, fd):
        real_drop(marker, fd)
        pruned_during_drop.append(repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14))

    monkeypatch.setattr(repro_retention.os, "write", short_on_seal)
    monkeypatch.setattr(repro_retention, "_drop_marker", drop_then_prune)
    failed = diff_mcp({"predicted": trace, "captured": trace})
    assert len(calls) == 2
    assert failed["persisted"] is False
    assert failed["retrievable"] is False
    assert failed["status"] == "delivery_failed"
    assert not list((root / "diff").glob(".pin-*.lock"))
    assert not repro_retention._PINS

    monkeypatch.setattr(repro_retention.os, "write", real_write)
    monkeypatch.setattr(repro_retention, "_drop_marker", real_drop)
    rebuilt = diff_mcp({"predicted": trace, "captured": trace})
    assert rebuilt["persisted"] is True
    assert Path(rebuilt["artifact_path"]).is_file()
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0


def test_diff_failed_seal_pin_preserves_concurrent_reader_lease_and_artifact(monkeypatch):
    from mindie_sim.diff_trace import call_mcp_tool as diff_mcp

    root = make_temp_workspace("mpr15c-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    trace = {"total_ms": 5, "ops": [{"name": "RMSNorm", "duration_ms": 5}]}

    real_write = repro_retention.os.write
    real_seal_pin = repro_retention._seal_pin
    reader_pid = os.getpid() + 100000
    monkeypatch.setattr(repro_retention, "process_exited", lambda pid: pid not in {os.getpid(), reader_pid})
    short_fds: set[int] = set()
    calls: list[int] = []

    def reader_then_writer_fails(entry):
        pin = repro_retention._pin_path(entry)
        with pin.open("ab") as handle:
            handle.write(f"{reader_pid}\n".encode("ascii"))
        return real_seal_pin(entry)

    def short_writer_pid(fd, data):
        payload = bytes(data)
        if not calls and payload == f"{os.getpid()}\n".encode("ascii"):
            short_fds.add(fd)
            calls.append(len(payload))
            return real_write(fd, payload[:1])
        if fd in short_fds and len(calls) == 1:
            calls.append(len(payload))
            return 0
        return real_write(fd, data)

    monkeypatch.setattr(repro_retention, "_seal_pin", reader_then_writer_fails)
    monkeypatch.setattr(repro_retention.os, "write", short_writer_pid)
    failed = diff_mcp({"predicted": trace, "captured": trace})
    assert failed["persisted"] is False
    assert failed["status"] == "delivery_failed"
    pins = list((root / "diff").glob(".pin-*.lock"))
    assert len(pins) == 1
    assert pins[0].read_bytes().lstrip(b"\x00") == f"{reader_pid}\n".encode("ascii")
    assert len(list((root / "diff").glob("*/diff.json"))) == 1
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0


def test_post_publish_verification_failure_preserves_concurrent_reader_lease(monkeypatch):
    from mindie_profiler import repro_atomic_io as checked_io
    from mindie_sim.diff_trace import call_mcp_tool as diff_mcp

    root = make_temp_workspace("mpr15v-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    trace = {"total_ms": 6, "ops": [{"name": "Rotary", "duration_ms": 6}]}
    reader_pid = os.getpid() + 100001
    monkeypatch.setattr(repro_retention, "process_exited", lambda pid: pid not in {os.getpid(), reader_pid})

    real_verify = checked_io._verified_inode
    calls = []

    def fail_final_verify_after_reader(path, expected, digest):
        calls.append(Path(path).name)
        if Path(path).name == "diff.json" and len(calls) == 2:
            pin = repro_retention._pin_path(Path(path).parent)
            with pin.open("ab") as handle:
                handle.write(f"{reader_pid}\n".encode("ascii"))
            raise OSError(errno.EIO, "transient read error after publish")
        return real_verify(path, expected, digest)

    monkeypatch.setattr(checked_io, "_verified_inode", fail_final_verify_after_reader)
    failed = diff_mcp({"predicted": trace, "captured": trace})
    assert failed["persisted"] is False
    assert failed["status"] == "delivery_failed"
    assert len(list((root / "diff").glob("*/diff.json"))) == 1
    assert repro_retention.prune_repro_storage(root, max_entries=0, max_age_days=14) == 0


def test_rewrite_lease_short_write_never_erases_live_reader_pid(tmp_path, monkeypatch):
    entry = tmp_path / "slot"
    entry.mkdir()
    (entry / "diff.json").write_text("{}\n", encoding="utf-8")
    pin = entry.with_name(".pin-slot.lock")
    live_pid = os.getpid() + 100002
    dead_pid = os.getpid() + 100003
    pin.write_bytes(f"{dead_pid}\n{live_pid}\n".encode("ascii"))
    monkeypatch.setattr(repro_retention, "process_exited", lambda pid: pid == dead_pid)

    real_write = repro_retention.os.write
    step = [0]

    def fail_compaction_write(fd, data):
        step[0] += 1
        if step[0] == 1:
            return real_write(fd, bytes(data)[:2])
        return 0

    monkeypatch.setattr(repro_retention.os, "write", fail_compaction_write)
    assert repro_retention._slot_pinned(entry) is True
    monkeypatch.setattr(repro_retention.os, "write", real_write)
    assert repro_retention._slot_pinned(entry) is True
    assert pin.read_bytes() == f"{live_pid}\n".encode("ascii")


def test_rollback_unleased_skips_deletion_when_os_lock_fails(tmp_path, monkeypatch):
    from mindie_profiler import storage_locks

    diff_dir = tmp_path / "diff"
    slot = diff_dir / "0123456789ab"
    slot.mkdir(parents=True)
    leaf = slot / "diff.json"
    leaf.write_text("{}\n", encoding="utf-8")
    pin = diff_dir / ".pin-0123456789ab.lock"
    pin.write_bytes(f"{os.getpid()}\n".encode("ascii"))

    real_open = storage_locks.os.open
    lock_target = os.path.abspath(diff_dir / ".retention.lock")

    def deny_retention_lock(path, flags, *args, **kwargs):
        if kwargs.get("dir_fd") is None and os.path.abspath(path) == lock_target:
            raise PermissionError(errno.EACCES, "os lock unavailable")
        return real_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(storage_locks.os, "open", deny_retention_lock)
    deleted = []
    repro_retention.rollback_unleased(leaf, lambda: deleted.append(True))
    assert deleted == []
    assert leaf.is_file()
    assert not repro_retention._PINS


@pytest.mark.parametrize("fail_call", [1, 2])
@pytest.mark.parametrize("fail_kind", ["open", "lock"])
def test_cas_stage_artifacts_fails_without_registering_when_retention_lock_fails(
        monkeypatch, fail_call, fail_kind):
    from mindie_profiler import storage_locks

    root = make_temp_workspace("mpr15l-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    lock_target = os.path.abspath(root / ".retention.lock")
    script = f"#!/usr/bin/env python3\n# single-op reproducer generated by mindie-profiler\nprint({fail_call!r}, {fail_kind!r})\n"
    identifier = repro_storage.artifact_id(script)

    real_open = storage_locks.os.open
    real_lock = storage_locks._os_lock
    seen = [0]

    def hooked_open(path, flags, *args, **kwargs):
        if kwargs.get("dir_fd") is None and os.path.abspath(path) == lock_target:
            seen[0] += 1
            if fail_kind == "open" and seen[0] == fail_call:
                raise PermissionError(errno.EACCES, "retention lock open failed")
            fd = real_open(path, flags, *args, **kwargs)
            seen.append(fd)
            return fd
        return real_open(path, flags, *args, **kwargs)

    def hooked_lock(fd, *args, **kwargs):
        if fail_kind == "lock" and fd in seen[1:] and seen[0] == fail_call:
            raise OSError(errno.ENOLCK, "retention os lock failed")
        return real_lock(fd, *args, **kwargs)

    monkeypatch.setattr(storage_locks.os, "open", hooked_open)
    monkeypatch.setattr(storage_locks, "_os_lock", hooked_lock)
    failed = repro_storage.stage_artifacts(script, {"schema": "mindie-op-repro/1", "script_sha256": identifier})
    assert failed["status"] == "delivery_failed"
    assert failed["retrievable"] is False
    assert identifier not in repro_storage._REGISTRY
    assert not repro_retention._PINS


def test_cas_failed_seal_pin_preserves_slot_for_concurrent_same_process_reuser(monkeypatch, tmp_path):
    root = make_temp_workspace("mpr15s-", base="/tmp")
    monkeypatch.setenv("MINDIE_REPRO_SHORT_ROOT", str(root))
    script = "#!/usr/bin/env python3\n# single-op reproducer generated by mindie-profiler\nprint('concurrent_reuse')\n"
    identifier = repro_storage.artifact_id(script)
    manifest = {"schema": "mindie-op-repro/1", "script_sha256": identifier}
    directory = root / identifier.split(":", 1)[1][:12]

    ready = threading.Event()
    reused = threading.Event()
    writer_done = threading.Event()
    result_a: dict[str, object] = {}
    real_verify = repro_storage._verify_pair_bytes
    real_write = repro_retention.os.write
    first_b = [True]

    def hooked_verify(*args):
        ok = real_verify(*args)
        if Path(args[0]) == directory / "repro.py":
            if threading.current_thread().name == "writer_A":
                assert ok
                ready.set()
                assert reused.wait(5.0)
            elif first_b[0]:
                first_b[0] = False
                assert ok
                reused.set()
                assert writer_done.wait(5.0)
        return ok

    def fail_writer_a_seal(fd, data):
        if threading.current_thread().name == "writer_A" and bytes(data) == f"{os.getpid()}\n".encode("ascii"):
            return 0
        return real_write(fd, data)

    monkeypatch.setattr(repro_storage, "_verify_pair_bytes", hooked_verify)
    monkeypatch.setattr(repro_retention.os, "write", fail_writer_a_seal)

    def run_a():
        try:
            result_a["result"] = repro_storage._write_pair_immutable(directory, script, manifest, identifier)
        finally:
            writer_done.set()

    thread_a = threading.Thread(target=run_a, name="writer_A")
    thread_a.start()
    assert ready.wait(5.0)
    result_b = repro_storage.stage_artifacts(script, manifest, output_dir=tmp_path / "caller")
    thread_a.join(5.0)
    assert not thread_a.is_alive()
    assert result_a["result"] == (None, "artifact_persistence_failed")
    assert result_b["status"] == "delivered" and result_b["retrievable"] is True
    assert (directory / "repro.py").is_file() and (directory / "manifest.json").is_file()
    resolved = repro_storage.resolve_repro_artifact(identifier)
    assert resolved["retrievable"] is True
    assert not repro_retention._PINS


