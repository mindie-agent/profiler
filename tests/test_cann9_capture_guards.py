"""Tier 0/1 regression guards for CANN 9.x capture safety and inventory discovery.

[Role]
  Verify exclusive controller locking, MSPTI dropped-record and slot-exhaustion
  honesty, per-worker Gear-2 PROF_* verification, process-group orphan cleanup,
  nonzero exit reporting under --terminate-after-capture, and inventory_profile
  discovery of CANN 9.x mindstudio_profiler_output trees.

[Invariants]
  * Isolates HOME, MINDIE_CONFIG_HOME, MINDIE_DATA_HOME, MINDIE_DIAGNOSTICS_ROOT,
    and MINDIE_CAPTURE_SHM_DIR in every test (Principle 16).
  * Releases ctypes buffer views inside ``with CaptureShmSession`` blocks so
    Windows ``mmap`` file handles close cleanly before ``unlink()``.

[Timeouts & Locks]
  Bounded Tier 0/1 local tests (< 10s total).

[Side-Effect Policy]
  Writes only under pytest ``tmp_path``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest

from mindie_profiler import ProfilerUsageError, inventory_profile
from mindie_profiler.cann_abi import default_shim_cache_dir, discover_cann9, shim_source_path
from mindie_profiler.native_capture import (
    _export_and_analyze_gear2,
    _pgid_alive,
    _terminate_process_group,
    build_preload_env,
    capture_profile,
)
from mindie_profiler.native_capture_shm import (
    GEAR_DEEP_ACLPROF,
    GEAR_FAST_MSPTI,
    MODE_AUTONOMOUS,
    MODE_COORDINATED,
    PHASE_ARMED,
    PHASE_STANDBY,
    WORKER_DONE,
    CaptureShmSession,
    resolve_shm_backing_path,
)
from test_cann9_native_capture import _create_synthetic_cann_tree


@pytest.fixture(autouse=True)
def _isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "HOME",
        "MINDIE_CONFIG_HOME",
        "MINDIE_DATA_HOME",
        "MINDIE_DIAGNOSTICS_ROOT",
        "MINDIE_CAPTURE_SHM_DIR",
    ):
        d = tmp_path / key.lower()
        d.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(key, str(d))


def test_overlapping_controller_rejected_and_dropped_or_overflow_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cann_dir = _create_synthetic_cann_tree(tmp_path / "cann9", version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    stub_so = tmp_path / "stub_shim.so"
    stub_so.write_bytes(b"\x7fELF")
    monkeypatch.setattr("mindie_profiler.native_capture.discover_cann9", lambda _r=None: install)
    monkeypatch.setattr(
        "mindie_profiler.native_capture.ensure_capture_shim_binary",
        lambda *_a, **_kw: stub_so,
    )

    shm_path = resolve_shm_backing_path("overlap_sess", shm_dir=tmp_path)
    with CaptureShmSession(
        shm_path, create=True, unlink_on_close=False, exclusive_controller=True
    ) as active_ctl:
        active_ctl.configure_run(
            session_id="overlap_sess",
            output_dir=tmp_path / "out_overlap",
            gear=GEAR_FAST_MSPTI,
            control_mode=MODE_COORDINATED,
            desired_phase=PHASE_STANDBY,
            min_warmup_steps=1,
            steady_window_steps=1,
            target_capture_steps=2,
            max_cv_ppm=100_000,
            bump_generation=False,
        )
        with pytest.raises(ProfilerUsageError, match="already has an active controller"):
            CaptureShmSession(
                shm_path, create=False, unlink_on_close=False, exclusive_controller=True
            )

    # Now populate worker with mspti_records_dropped > 0 and complete window -> must FAIL!
    w_json = tmp_path / "out_drop" / "gen_1" / "worker.json"
    w_json.parent.mkdir(parents=True, exist_ok=True)
    w_json.write_text(
        json.dumps(
            {
                "interval_count": 2,
                "observed_event_span_ns": 20_000,
                "device_busy_union_ns": 15_000,
                "device_uncovered_ns": 5_000,
                "exposed_comm_ns": 0,
                "operators": [
                    {
                        "kind": "kernel",
                        "op_type": "MatMul",
                        "name": "MatMulV2",
                        "count": 2,
                        "total_ns": 15_000,
                        "min_ns": 7_000,
                        "max_ns": 8_000,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with CaptureShmSession(shm_path, create=False, unlink_on_close=False) as writer:
        sl = writer.view.slots[0]
        sl.pid = 7777
        sl.acked_generation = 1
        sl.captured_steps = 2
        sl.mspti_records_captured = 2
        sl.mspti_records_dropped = 5
        sl.summary_written = 1
        sl.worker_state = WORKER_DONE
        sl.artifact_path = str(w_json).encode("utf-8")
        sl.claimed = 2
        del sl

    rep = capture_profile(
        attach_session_id="overlap_sess",
        shm_dir=tmp_path,
        output_dir=tmp_path / "out_drop",
        gear="fast",
        target_capture_steps=2,
        warmup_timeout_s=1.0,
        capture_timeout_s=1.0,
        cleanup_grace_s=0.2,
    )
    assert rep["status"] == "failed"
    assert any("mspti_records_dropped:slot_0:5" in n for n in rep["notes"])
    shm_path.unlink(missing_ok=True)
    shm_path.with_name(f".{shm_path.name}.ctl.lock").unlink(missing_ok=True)


def test_gear2_requires_every_worker_prof_dir_and_exported_source(tmp_path: Path) -> None:
    cann_dir = _create_synthetic_cann_tree(tmp_path / "cann_g2", version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    if os.name == "nt":
        noop_msprof = tmp_path / "noop_msprof.cmd"
        noop_msprof.write_text("@exit /b 0\r\n", encoding="utf-8")
    else:
        noop_msprof = tmp_path / "noop_msprof.sh"
        noop_msprof.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        noop_msprof.chmod(0o755)
    install_noop = type(install)(
        **({f: getattr(install, f) for f in install.__dataclass_fields__} | {"msprof_bin": noop_msprof})
    )

    # Worker 0 has PROF_0, Worker 1 is missing PROF_* -> must fail before export!
    w0 = tmp_path / "gen_1" / "rank_0_device_0"
    w1 = tmp_path / "gen_1" / "rank_1_device_1"
    (w0 / "PROF_0").mkdir(parents=True)
    w1.mkdir(parents=True)
    _, c7_rep, errs = _export_and_analyze_gear2(
        install_noop,
        [w0, w1],
        gen_out_dir=tmp_path / "gen_1",
        export_deadline=time.monotonic() + 5.0,
        export_timeout_s=5.0,
        top_n=5,
    )
    assert c7_rep is None
    assert any("msprof_missing_prof_dir_for_worker:1:" in e for e in errs)

    # Both workers have PROF_*, but msprof exited 0 without producing CSV/DB for PROF_1 -> must fail!
    (w0 / "PROF_0" / "mindstudio_profiler_output").mkdir(parents=True)
    (w0 / "PROF_0" / "mindstudio_profiler_output" / "op_summary_2026.csv").write_text(
        "Op Name,Op Type,Task Type,Task Start Time(us),Task Duration(us)\n"
        "MatMul_0,MatMul,AI_CORE,100.0,20.0\n",
        encoding="utf-8",
    )
    (w1 / "PROF_1").mkdir(parents=True)
    _, c7_rep2, errs2 = _export_and_analyze_gear2(
        install_noop,
        [w0, w1],
        gen_out_dir=tmp_path / "gen_1",
        export_deadline=time.monotonic() + 5.0,
        export_timeout_s=5.0,
        top_n=5,
    )
    assert c7_rep2 is None
    assert any("msprof_missing_exported_source:" in e for e in errs2)


def test_inventory_discovers_mindstudio_csv_and_process_group_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 1. inventory_profile discovers CANN 9.x mindstudio_profiler_output & infers rank_index from parent
    prof_dir = tmp_path / "gen_1" / "rank_3_device_3_pid123_gen1" / "PROF_0001" / "mindstudio_profiler_output"
    prof_dir.mkdir(parents=True)
    csv_file = prof_dir / "op_summary_20260101.csv"
    csv_file.write_text(
        "Op Name,Op Type,Task Type,Task Start Time(us),Task Duration(us)\n"
        "FlashAttentionScore,FlashAttentionScore,AI_CORE,10.0,5.0\n",
        encoding="utf-8",
    )
    inv = inventory_profile(tmp_path / "gen_1")
    assert inv["rank_count"] == 1
    assert inv["ranks"][0]["rank_id"] == "rank_3"
    assert inv["ranks"][0]["rank_index"] == 3
    assert str(csv_file.resolve()) in inv["ranks"][0]["csv_candidates"]

    # 2. --terminate-after-capture still reports independent nonzero crash when child died on its own
    cann_dir = _create_synthetic_cann_tree(tmp_path / "cann_term", version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    stub_so = tmp_path / "stub.so"
    stub_so.write_bytes(b"\x7fELF")
    monkeypatch.setattr("mindie_profiler.native_capture.discover_cann9", lambda _r=None: install)
    monkeypatch.setattr(
        "mindie_profiler.native_capture.ensure_capture_shim_binary",
        lambda *_a, **_kw: stub_so,
    )
    rep_crash = capture_profile(
        command=[sys.executable, "-c", "import sys; sys.exit(7)"],
        output_dir=tmp_path / "out_crash",
        gear="fast",
        terminate_after_capture=True,
        warmup_timeout_s=2.0,
        capture_timeout_s=1.0,
        cleanup_grace_s=0.2,
    )
    assert rep_crash["status"] == "failed"
    assert rep_crash["process_exit_code"] == 7
    assert "target_command_nonzero_exit:7" in rep_crash["notes"]

    # 3. On POSIX, _terminate_process_group reaps surviving background child even after leader exits
    if os.name != "nt":
        pid_file = tmp_path / "bg_child.pid"
        leader = subprocess.Popen(
            [
                sys.executable,
                "-c",
                f"import os, subprocess, sys, time\n"
                f"p = subprocess.Popen([sys.executable, '-c', 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)'])\n"
                f"open({str(pid_file)!r}, 'w').write(str(p.pid))\n",
            ],
            start_new_session=True,
        )
        pgid = leader.pid
        assert leader.wait(timeout=3.0) == 0
        deadline = time.monotonic() + 2.0
        while not pid_file.is_file() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert _pgid_alive(pgid) is True
        signaled_live_leader = _terminate_process_group(leader, pgid, grace_s=0.1)
        assert signaled_live_leader is False
        assert _pgid_alive(pgid) is False


def test_preload_env_resolves_relative_paths_and_gear2_rejects_empty_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cann_dir = _create_synthetic_cann_tree(Path("rel_cann9"), version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    rel_shim = Path("rel_shim.so")
    rel_shim.write_bytes(b"\x7fELF")
    rel_shm = resolve_shm_backing_path("rel_sess", shm_dir=".")
    assert rel_shm.is_absolute()
    assert default_shim_cache_dir({"MINDIE_DATA_HOME": "."}).is_absolute()

    env = build_preload_env(install, rel_shim, Path("rel_local.shm"), gear_code=GEAR_FAST_MSPTI, base_env={})
    assert env["LD_PRELOAD"] == f"{install.libmspti_so.resolve()}:{rel_shim.resolve()}"
    for key in ("MINDIE_CAPTURE_SHM_PATH", "MINDIE_CAPTURE_LIBASCENDCL", "MINDIE_CAPTURE_LIBMSPTI"):
        assert Path(env[key]).is_absolute(), f"non-absolute {key}: {env[key]}"

    # Gear-2 empty CSV export (single-worker, multi-worker partial empty, and graph-wait task_time) must fail!
    if os.name == "nt":
        noop_msprof = tmp_path / "noop_msprof2.cmd"
        noop_msprof.write_text("@exit /b 0\r\n", encoding="utf-8")
    else:
        noop_msprof = tmp_path / "noop_msprof2.sh"
        noop_msprof.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        noop_msprof.chmod(0o755)
    install_noop = type(install)(
        **({f: getattr(install, f) for f in install.__dataclass_fields__} | {"msprof_bin": noop_msprof})
    )
    hdr_only = "Op Name,Op Type,Task Type,Task Start Time(us),Task Duration(us)\n"
    w_empty = tmp_path / "g2_empty" / "rank_0_device_0"
    (w_empty / "PROF_0" / "mindstudio_profiler_output").mkdir(parents=True)
    (w_empty / "PROF_0" / "mindstudio_profiler_output" / "op_summary_1.csv").write_text(hdr_only, encoding="utf-8")
    _, _, errs_single = _export_and_analyze_gear2(
        install_noop, [w_empty], gen_out_dir=tmp_path / "g2_empty",
        export_deadline=time.monotonic() + 5.0, export_timeout_s=5.0, top_n=5,
    )
    assert any(e.startswith("gear2_empty_capture_window:") for e in errs_single)

    # task_time export with only MODEL_EXECUTE / MODEL_WAIT_COMPLETE envelope markers must not fabricate N/A kernels
    w_graph_markers = tmp_path / "g2_markers" / "rank_0_device_0"
    (w_graph_markers / "PROF_0" / "mindstudio_profiler_output").mkdir(parents=True)
    fixture_task_time = Path(__file__).resolve().parent / "fixtures" / "graph_execution" / "task_time.csv"
    (w_graph_markers / "PROF_0" / "mindstudio_profiler_output" / "task_time_1.csv").write_bytes(
        fixture_task_time.read_bytes()
    )
    _, _, errs_markers = _export_and_analyze_gear2(
        install_noop, [w_graph_markers], gen_out_dir=tmp_path / "g2_markers",
        export_deadline=time.monotonic() + 5.0, export_timeout_s=5.0, top_n=5,
    )
    assert any(e.startswith("gear2_empty_capture_window:") for e in errs_markers)

    # Large Gear-2 CSV export must be bounded end-to-end by export_deadline (not overrun in synchronous accounting)
    w_big = tmp_path / "g2_big" / "rank_0_device_0"
    (w_big / "PROF_0" / "mindstudio_profiler_output").mkdir(parents=True)
    big_rows = "".join(f"MatMul_{i % 64},MatMul,AI_CORE,{i * 30.0},20.0\n" for i in range(40_000))
    (w_big / "PROF_0" / "mindstudio_profiler_output" / "op_summary_1.csv").write_text(
        hdr_only + big_rows, encoding="utf-8"
    )
    t_big = time.monotonic()
    _, _, errs_big = _export_and_analyze_gear2(
        install_noop, [w_big], gen_out_dir=tmp_path / "g2_big",
        export_deadline=t_big + 0.25, export_timeout_s=0.25, top_n=5,
    )
    elapsed_big = time.monotonic() - t_big
    assert elapsed_big < 0.75, f"Gear-2 analyze overshot 0.25s deadline: {elapsed_big:.3f}s"
    assert any("timeout_exceeded" in e for e in errs_big), errs_big

    w_ok = tmp_path / "g2_pair" / "rank_0_device_0"
    w_bad = tmp_path / "g2_pair" / "rank_1_device_1"
    (w_ok / "PROF_0" / "mindstudio_profiler_output").mkdir(parents=True)
    (w_bad / "PROF_1" / "mindstudio_profiler_output").mkdir(parents=True)
    (w_ok / "PROF_0" / "mindstudio_profiler_output" / "op_summary_0.csv").write_text(
        hdr_only + "MatMul_0,MatMul,AI_CORE,100.0,25.0\n", encoding="utf-8"
    )
    (w_bad / "PROF_1" / "mindstudio_profiler_output" / "op_summary_1.csv").write_text(hdr_only, encoding="utf-8")
    _, _, errs_pair = _export_and_analyze_gear2(
        install_noop, [w_ok, w_bad], gen_out_dir=tmp_path / "g2_pair",
        export_deadline=time.monotonic() + 5.0, export_timeout_s=5.0, top_n=5,
    )
    assert any("gear2_empty_capture_window:rank_1" in e for e in errs_pair)


@pytest.mark.skipif(os.name == "nt", reason="POSIX SIGTERM-ignoring process group budget test")
def test_outer_deadline_reserves_cleanup_grace_against_sigterm_ignoring_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cann_dir = _create_synthetic_cann_tree(tmp_path / "cann_budget", version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    stub_so = tmp_path / "stub_budget.so"
    stub_so.write_bytes(b"\x7fELF")
    monkeypatch.setattr("mindie_profiler.native_capture.discover_cann9", lambda _r=None: install)
    monkeypatch.setattr("mindie_profiler.native_capture.ensure_capture_shim_binary", lambda *_a, **_kw: stub_so)

    # Child marks worker DONE in /dev/shm immediately, then ignores SIGTERM and sleeps 30s.
    child_code = (
        "import json, os, pathlib, signal, time\n"
        "from mindie_profiler.native_capture_shm import CaptureShmSession, WORKER_DONE\n"
        "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
        "shm = pathlib.Path(os.environ['MINDIE_CAPTURE_SHM_PATH'])\n"
        "with CaptureShmSession(shm, create=False, unlink_on_close=False) as s:\n"
        "    out_dir = pathlib.Path(bytes(s.view.header.output_dir).split(b'\\x00', 1)[0].decode())\n"
        "    wj = out_dir / 'w0.json'\n"
        "    wj.write_text(json.dumps({'interval_count': 1, 'observed_event_span_ns': 1000, "
        "'device_busy_union_ns': 900, 'device_uncovered_ns': 100, 'exposed_comm_ns': 0, "
        "'operators': [{'kind': 'kernel', 'op_type': 'MatMul', 'name': 'MM', 'count': 1, "
        "'total_ns': 900, 'min_ns': 900, 'max_ns': 900}]}))\n"
        "    sl = s.view.slots[0]\n"
        "    sl.pid = os.getpid(); sl.logical_device_id = 0; sl.physical_device_id = 0\n"
        "    sl.acked_generation = s.view.header.generation; sl.captured_steps = 2\n"
        "    sl.mspti_records_captured = 1; sl.summary_written = 1\n"
        "    sl.artifact_path = str(wj).encode(); sl.worker_state = WORKER_DONE; sl.claimed = 2\n"
        "    del sl\n"
        "time.sleep(30)\n"
    )
    repo_root = str(Path(__file__).resolve().parents[1])
    t0 = time.monotonic()
    rep = capture_profile(
        command=[sys.executable, "-c", child_code],
        output_dir=tmp_path / "out_budget",
        gear="fast",
        target_capture_steps=2,
        warmup_timeout_s=0.35,
        capture_timeout_s=0.35,
        cleanup_grace_s=0.30,
        outer_timeout_s=1.0,
        extra_env={"PYTHONPATH": repo_root},
    )
    elapsed = time.monotonic() - t0
    assert elapsed < 1.12, f"capture_profile overshot 1.0s outer budget: {elapsed:.3f}s"
    assert "process_drain_timeout_terminated" in rep["notes"]
    assert rep["status"] == "failed"


@pytest.mark.skipif(os.name == "nt", reason="POSIX C shim harness test")
def test_compiled_shim_standby_zero_sync_stream_match_eager_dev_and_lazy_slot(tmp_path: Path) -> None:
    import shutil

    cc = shutil.which("cc") or shutil.which("gcc")
    if cc is None:
        pytest.skip("no C compiler available")

    inc = tmp_path / "inc"
    (inc / "acl").mkdir(parents=True)
    (inc / "acl" / "acl_rt.h").write_text(
        "#ifndef MOCK_ACL_RT_H\n#define MOCK_ACL_RT_H\n#include <stddef.h>\n#include <stdint.h>\n"
        "typedef int aclError;\ntypedef void *aclrtStream;\ntypedef void *aclrtApiFunc;\n"
        "typedef void *aclmdlRI;\ntypedef int aclmdlRICaptureMode;\ntypedef int aclrtMemMallocPolicy;\n"
        "aclError aclrtApiInjectionGetFunc(const char *n, aclrtApiFunc *o, aclrtApiFunc *c);\n"
        "aclError aclrtApiInjectionSetFunc(const char *n, aclrtApiFunc f);\n#endif\n",
        encoding="utf-8",
    )
    (inc / "acl" / "acl_prof.h").write_text(
        "#ifndef MOCK_ACL_PROF_H\n#define MOCK_ACL_PROF_H\n#include <stddef.h>\n#include <stdint.h>\n"
        "typedef struct aclprofConfig aclprofConfig;\ntypedef int aclprofAicoreMetrics;\n"
        "typedef void aclprofAicoreEvents;\n"
        "#define ACL_PROF_ACL_API 1ULL\n#define ACL_PROF_TASK_TIME 2ULL\n"
        "#define ACL_PROF_AICORE_METRICS 4ULL\n#define ACL_PROF_AICPU 8ULL\n"
        "#define ACL_PROF_HCCL_TRACE 16ULL\n#define ACL_PROF_MSPROFTX 32ULL\n"
        "#define ACL_PROF_RUNTIME_API 64ULL\n#define ACL_PROF_OP_ATTR 128ULL\n"
        "#define ACL_PROF_AICORE_SHAPE 256ULL\n#endif\n",
        encoding="utf-8",
    )
    (inc / "mspti.h").write_text(
        "#ifndef MOCK_MSPTI_H\n#define MOCK_MSPTI_H\n#include <stddef.h>\n#include <stdint.h>\n"
        "typedef int msptiResult;\n#define MSPTI_SUCCESS 0\ntypedef void *msptiSubscriberHandle;\n"
        "typedef int msptiCallbackDomain;\ntypedef int msptiCallbackId;\ntypedef void msptiCallbackData;\n"
        "typedef void (*msptiCallbackFunc)(void *, msptiCallbackDomain, msptiCallbackId, const msptiCallbackData *);\n"
        "typedef void (*msptiBuffersCallbackRequestFunc)(uint8_t **, size_t *, size_t *);\n"
        "typedef void (*msptiBuffersCallbackCompleteFunc)(uint8_t *, size_t, size_t);\n"
        "typedef enum { MSPTI_ACTIVITY_KIND_KERNEL = 1, MSPTI_ACTIVITY_KIND_HCCL = 2, "
        "MSPTI_ACTIVITY_KIND_COMMUNICATION = 3 } msptiActivityKind;\n"
        "typedef struct { msptiActivityKind kind; } msptiActivity;\n"
        "typedef struct { msptiActivityKind kind; uint64_t start; uint64_t end; struct { uint32_t streamId; } ds; "
        "const char *type; const char *name; } msptiActivityKernel;\n"
        "typedef struct { msptiActivityKind kind; uint64_t start; uint64_t end; struct { uint32_t streamId; } ds; "
        "double bandWidth; const char *name; const char *commName; } msptiActivityHccl;\n"
        "typedef struct { msptiActivityKind kind; uint64_t start; uint64_t end; struct { uint32_t streamId; } ds; "
        "uint64_t count; const char *algType; const char *name; const char *commName; } msptiActivityCommunication;\n"
        "#endif\n",
        encoding="utf-8",
    )

    shim_c = shim_source_path()
    harness_c = tmp_path / "harness.c"
    harness_c.write_text(
        '#include <assert.h>\n#include <stdio.h>\n#include <string.h>\n#include <sys/mman.h>\n#include <sys/wait.h>\n#include <unistd.h>\n'
        '#include "acl/acl_rt.h"\n'
        '#include "_cann9_capture_mspti.h"\n'
        "extern void mindie_capture_mark_step(void);\n"
        "static int g_cur_dev = -1, g_sync_stream_calls = 0, g_sync_dev_calls = 0, g_ri_begin_rc = 0, g_subs = 0;\n"
        "static size_t g_mock_drops = 0;\n"
        "static aclError base_set_dev(int32_t d) { g_cur_dev = d; return 0; }\n"
        "static aclError base_get_dev(int32_t *d) { if (g_cur_dev < 0) return 1; *d = g_cur_dev; return 0; }\n"
        "static aclError base_sync_stream(aclrtStream s) { (void)s; g_sync_stream_calls++; return 0; }\n"
        "static aclError base_sync_dev(void) { g_sync_dev_calls++; return 0; }\n"
        "static aclError base_ri_begin(aclrtStream s, aclmdlRICaptureMode m) { (void)s; (void)m; return g_ri_begin_rc; }\n"
        "static aclError base_ri_async(aclmdlRI r, aclrtStream s) { (void)r; (void)s; return 0; }\n"
        '__attribute__((visibility("default"))) msptiResult msptiSubscribe(msptiSubscriberHandle *s, msptiCallbackFunc cb, void *ud) {\n'
        "  (void)cb; (void)ud; if (g_subs > 0) return 2; g_subs++; *s = (void *)0x1; return 0;\n}\n"
        '__attribute__((visibility("default"))) msptiResult msptiActivityRegisterCallbacks(msptiBuffersCallbackRequestFunc r, msptiBuffersCallbackCompleteFunc c) { (void)r; (void)c; return 0; }\n'
        '__attribute__((visibility("default"))) msptiResult msptiActivityEnable(msptiActivityKind k) { (void)k; return 0; }\n'
        '__attribute__((visibility("default"))) msptiResult msptiActivityGetNextRecord(uint8_t *b, size_t s, msptiActivity **r) { (void)b; (void)s; *r = NULL; return 1; }\n'
        '__attribute__((visibility("default"))) msptiResult msptiActivityFlushAll(uint32_t f) { (void)f; return 0; }\n'
        '__attribute__((visibility("default"))) msptiResult msptiActivityGetNumDroppedRecords(void *c, uint32_t s, size_t *n) { (void)c; (void)s; *n = g_mock_drops; g_mock_drops = 0; return 0; }\n'
        '__attribute__((visibility("default"))) msptiResult msptiGetTimestamp(uint64_t *t) { *t = 1000ULL; return 0; }\n'
        "typedef struct { const char *name; aclrtApiFunc orig; aclrtApiFunc cur; } HookSlot;\n"
        "static HookSlot g_tbl[] = {\n"
        '  {"aclrtSetDevice", (aclrtApiFunc)base_set_dev, NULL},\n'
        '  {"aclrtGetDevice", (aclrtApiFunc)base_get_dev, NULL},\n'
        '  {"aclrtSynchronizeStream", (aclrtApiFunc)base_sync_stream, NULL},\n'
        '  {"aclrtSynchronizeDevice", (aclrtApiFunc)base_sync_dev, NULL},\n'
        '  {"aclmdlRICaptureBegin", (aclrtApiFunc)base_ri_begin, NULL},\n'
        '  {"aclmdlRIExecuteAsync", (aclrtApiFunc)base_ri_async, NULL},\n'
        "  {NULL, NULL, NULL}\n};\n"
        '__attribute__((visibility("default"))) aclError aclrtApiInjectionGetFunc(const char *n, aclrtApiFunc *o, aclrtApiFunc *c) {\n'
        "  for (int i = 0; g_tbl[i].name; ++i) if (strcmp(g_tbl[i].name, n) == 0) { *o = g_tbl[i].orig; *c = g_tbl[i].cur; return 0; }\n"
        "  return 1;\n}\n"
        '__attribute__((visibility("default"))) aclError aclrtApiInjectionSetFunc(const char *n, aclrtApiFunc f) {\n'
        "  for (int i = 0; g_tbl[i].name; ++i) if (strcmp(g_tbl[i].name, n) == 0) { g_tbl[i].cur = f; return 0; }\n"
        "  return 1;\n}\n"
        '__attribute__((visibility("default"))) aclError aclrtGetDevice(int32_t *d) { return base_get_dev(d); }\n'
        '__attribute__((visibility("default"))) aclError aclrtSynchronizeDevice(void) { return base_sync_dev(); }\n'
        "static aclrtApiFunc fn(const char *n) {\n"
        "  for (int i = 0; g_tbl[i].name; ++i) if (strcmp(g_tbl[i].name, n) == 0) return g_tbl[i].cur ? g_tbl[i].cur : g_tbl[i].orig;\n"
        "  return NULL;\n}\n"
        "int main(int argc, char **argv) {\n"
        "  assert(argc >= 2);\n"
        "  int fd = open(getenv(\"MINDIE_CAPTURE_SHM_PATH\"), O_RDWR);\n"
        "  MindieCaptureShm *shm = (MindieCaptureShm *)mmap(NULL, sizeof(MindieCaptureShm), PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);\n"
        "  aclError (*set_dev)(int32_t) = (aclError (*)(int32_t))fn(\"aclrtSetDevice\");\n"
        "  aclError (*ri_begin)(aclrtStream, aclmdlRICaptureMode) = (aclError (*)(aclrtStream, aclmdlRICaptureMode))fn(\"aclmdlRICaptureBegin\");\n"
        "  aclError (*ri_async)(aclmdlRI, aclrtStream) = (aclError (*)(aclmdlRI, aclrtStream))fn(\"aclmdlRIExecuteAsync\");\n"
        "  aclError (*sync_s)(aclrtStream) = (aclError (*)(aclrtStream))fn(\"aclrtSynchronizeStream\");\n"
        "  aclError (*sync_d)(void) = (aclError (*)(void))fn(\"aclrtSynchronizeDevice\");\n"
        "  if (strcmp(argv[1], \"cpu_only\") == 0) {\n"
        "    for (int i = 0; i < 6; ++i) mindie_capture_mark_step();\n"
        "    assert(shm->header.active_worker_slots == 0U && shm->slots[0].claimed == 0U);\n"
        "    set_dev(0); mindie_capture_mark_step();\n"
        "    assert(shm->header.active_worker_slots == 1U && shm->slots[0].logical_device_id == 0);\n"
        "  } else if (strcmp(argv[1], \"replay_streams\") == 0) {\n"
        "    aclrtStream sA = (aclrtStream)(uintptr_t)0x1001, sB = (aclrtStream)(uintptr_t)0x2002;\n"
        "    set_dev(0);\n"
        "    for (int i = 0; i < 6; ++i) ri_async((aclmdlRI)1, sA);\n"
        "    assert(g_sync_stream_calls == 0 && g_sync_dev_calls == 0);\n"
        "    shm->header.desired_phase = PHASE_ARMED; shm->header.generation = 1;\n"
        "    ri_async((aclmdlRI)1, sA);\n"
        "    sync_s(sB); assert(shm->slots[0].total_steps == 0ULL);\n"
        "    sync_s(sA); assert(shm->slots[0].total_steps == 1ULL);\n"
        "    shm->slots[0].worker_state = WORKER_DONE;\n"
        "    int sync_done0 = g_sync_stream_calls + g_sync_dev_calls;\n"
        "    for (int i = 0; i < 6; ++i) ri_async((aclmdlRI)1, sA);\n"
        "    assert((g_sync_stream_calls + g_sync_dev_calls) == sync_done0);\n"
        "  } else if (strcmp(argv[1], \"eager_dev\") == 0) {\n"
        "    set_dev(0);\n"
        "    for (int i = 0; i < 5; ++i) { usleep(1000); sync_d(); }\n"
        "    assert(shm->slots[0].total_steps >= 4ULL && shm->slots[0].worker_state == 2U);\n"
        "  } else if (strcmp(argv[1], \"fork_drops_rollback_gen\") == 0) {\n"
        "    assert(g_subs == 0);\n"
        "    pid_t pid = fork(); assert(pid >= 0);\n"
        "    if (pid == 0) {\n"
        "      assert(g_subs == 0);\n"
        "      set_dev(0); assert(g_subs == 1);\n"
        "      g_ri_begin_rc = 55;\n"
        "      assert(ri_begin((aclrtStream)1, 0) == 55);\n"
        "      assert(shm->slots[0].active_graph_captures == 0U && shm->slots[0].graph_captures_total == 0ULL);\n"
        "      g_mock_drops = 7;\n"
        "      for (int i = 0; i < 6; ++i) { usleep(500); mindie_capture_mark_step(); }\n"
        "      assert(shm->slots[0].worker_state == 2U);\n"
        "      shm->header.desired_phase = PHASE_START_NOW;\n"
        "      mindie_capture_mark_step(); assert(shm->slots[0].worker_state == 3U);\n"
        "      g_mock_drops = 7;\n"
        "      usleep(500); mindie_capture_mark_step(); usleep(500); mindie_capture_mark_step();\n"
        "      assert(shm->slots[0].worker_state == WORKER_DONE && shm->slots[0].mspti_records_dropped == 7ULL);\n"
        "      shm->header.min_warmup_steps = 4; shm->header.steady_window_steps = 2;\n"
        "      shm->header.desired_phase = PHASE_ARMED; shm->header.generation = 2;\n"
        "      for (int i = 0; i < 4; ++i) { usleep(500); mindie_capture_mark_step(); }\n"
        "      assert(shm->slots[0].worker_state == 1U);\n"
        "      for (int i = 0; i < 3; ++i) { usleep(500); mindie_capture_mark_step(); }\n"
        "      assert(shm->slots[0].worker_state == 2U);\n"
        "      _exit(0);\n"
        "    }\n"
        "    int st = 0; assert(waitpid(pid, &st, 0) == pid && WIFEXITED(st) && WEXITSTATUS(st) == 0);\n"
        "  }\n"
        "  return 0;\n}\n",
        encoding="utf-8",
    )
    bin_path = tmp_path / "shim_harness"
    extra_ld = ["-rdynamic"] if sys.platform.startswith("linux") else []
    comp = subprocess.run(
        [cc, "-O2", "-std=gnu11", f"-I{shim_c.parent}", f"-I{inc}", str(harness_c), str(shim_c), "-o", str(bin_path), *extra_ld, "-ldl", "-lpthread", "-lm"],
        capture_output=True, text=True, timeout=20.0, check=False,
    )
    assert comp.returncode == 0, f"failed to compile shim harness:\n{comp.stderr}"

    for mode, init_phase, gear in (
        ("cpu_only", PHASE_ARMED, GEAR_DEEP_ACLPROF),
        ("replay_streams", PHASE_STANDBY, GEAR_DEEP_ACLPROF),
        ("eager_dev", PHASE_ARMED, GEAR_DEEP_ACLPROF),
        ("fork_drops_rollback_gen", PHASE_ARMED, GEAR_FAST_MSPTI),
    ):
        out_m = tmp_path / f"out_{mode}"
        out_m.mkdir(parents=True, exist_ok=True)
        shm_p = resolve_shm_backing_path(f"h_{mode}", shm_dir=tmp_path)
        with CaptureShmSession(shm_p, create=True, unlink_on_close=True) as sess:
            sess.configure_run(
                session_id=f"h_{mode}", output_dir=out_m, gear=gear,
                control_mode=MODE_COORDINATED, desired_phase=init_phase,
                min_warmup_steps=1, steady_window_steps=2, target_capture_steps=2,
                max_cv_ppm=900_000, min_step_interval_ns=100, bump_generation=(init_phase != PHASE_STANDBY),
            )
            run = subprocess.run(
                [str(bin_path), mode],
                env={**os.environ, "MINDIE_CAPTURE_SHM_PATH": str(shm_p)},
                capture_output=True, text=True, timeout=10.0, check=False,
            )
            assert run.returncode == 0, f"shim_harness {mode} failed (rc={run.returncode}):\n{run.stderr}"
