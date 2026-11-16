"""Tier-0/1 retention, cache-boundedness, and temp-workspace lifecycle.

[Role]
  Guard the storage lifecycle contract: a timed-out shim compile never leaks a
  partial object, the shim cache stays bounded, the repro CAS/diff roots are
  pruned without touching active state, trace sidecar rebuilds clean up their
  private database, and probe runs leave no temporary directory behind.

[Invariants]
  * Tests read only their own fresh roots; the pytest reaper owns cleanup.
  * No live NPU, network, or host ``$HOME`` access.

[Timeouts & Locks]
  Bounded filesystem work; no sleeps or timing races.

[Side-Effect Policy]
  Writes only pytest ``tmp_path`` and registered ``/tmp`` short roots.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace

import pytest

from mindie_profiler import cann_abi, repro_retention, repro_storage, sources_trace
from mindie_profiler.events import ProfilerSchemaError
from mindie_profiler.fabric_probe import build_fabric_probe_plan

import nr_s6_round4_probe as probe
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
    assert not (cache / f".{superseded[0].name}.lock").exists()
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
