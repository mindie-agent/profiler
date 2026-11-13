"""Tier 0/1/2 tests for CANN 9.x native steady-state profiling capture.

[Role]
  Validate the CANN >= 9.0 ABI gate, /dev/shm control plane, Principle-10
  timeout arithmetic, Level-3 transient contamination audit, CLI contract, and
  live Ascend 950DT (CANN 9.2.1) Gear-1/Gear-2/Attach hardware execution.

[Invariants]
  * Isolates HOME, MINDIE_CONFIG_HOME, MINDIE_DATA_HOME, MINDIE_DIAGNOSTICS_ROOT,
    and MINDIE_CAPTURE_SHM_DIR in every test (Principle 16).
  * Live NPU tests check ``npu-smi info`` first and never disturb foreign PIDs
    (Guardrail P6.3).

[Timeouts & Locks]
  Tier 0 < 5s, Tier 1 < 15s, Tier 2 live NPU < 60s bounded SSH/process runs.

[Side-Effect Policy]
  All local artifacts stay under pytest ``tmp_path``; remote live tests use
  trap-cleaned ``/tmp/mindie-cann9-cap-*`` directories.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import tarfile
import io
import pytest

from mindie_profiler import (
    CAPTURE_SCHEMA,
    ProfilerUsageError,
    __main__ as cli_root,
    mark_capture_step,
)
from mindie_profiler.cann_abi import (
    build_cann_runtime_env,
    discover_cann9,
    parse_cann_install_info,
    parse_cann_version_tuple,
)
from mindie_profiler.native_capture import (
    _aggregate_gear1_worker_payload,
    _export_and_analyze_gear2,
    _validate_timeout_budgets,
    audit_worker_steady_state,
    capture_profile,
)
from mindie_profiler.native_capture_shm import (
    GEAR_FAST_MSPTI,
    MODE_COORDINATED,
    PHASE_ARMED,
    PHASE_START_NOW,
    WORKER_DONE,
    WORKER_GATE_READY,
    CaptureShmSession,
    PipeTailDrainer,
    resolve_shm_backing_path,
)


_REAL_SSH_HOME = str(Path.home())


def _ssh_client_env() -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = _REAL_SSH_HOME
    return env


@pytest.fixture(autouse=True)
def _isolated_mindie_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "isolated_home"
    cfg = tmp_path / "isolated_config"
    data = tmp_path / "isolated_data"
    diag = tmp_path / "isolated_diag"
    shm = tmp_path / "isolated_shm"
    for p in (home, cfg, data, diag, shm):
        p.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("MINDIE_CONFIG_HOME", str(cfg))
    monkeypatch.setenv("MINDIE_DATA_HOME", str(data))
    monkeypatch.setenv("MINDIE_DIAGNOSTICS_ROOT", str(diag))
    monkeypatch.setenv("MINDIE_CAPTURE_SHM_DIR", str(shm))


def _create_synthetic_cann_tree(
    root: Path,
    *,
    version: str = "9.2.1",
    arch: str = "aarch64",
    include_injection: bool = True,
    include_shape_macro: bool = True,
) -> Path:
    arch_dir = root / f"{arch}-linux"
    (arch_dir / "include" / "acl").mkdir(parents=True, exist_ok=True)
    (arch_dir / "lib64").mkdir(parents=True, exist_ok=True)
    (arch_dir / "bin").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "mspti" / "include").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "mspti" / "lib64").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "profiler" / "bin").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "profiler" / "lib64").mkdir(parents=True, exist_ok=True)

    (arch_dir / "ascend_toolkit_install.info").write_text(
        f"package_name=cann-toolkit\nversion={version}\n"
        f"innerversion=V100R001C12SPC002B201\narch={arch}\n",
        encoding="utf-8",
    )
    acl_rt_body = (
        "aclError aclrtApiInjectionSetFunc(const char* name, aclrtApiFunc func);\n"
        if include_injection
        else "/* missing injection */\n"
    )
    acl_prof_body = (
        "#define ACL_PROF_AICORE_SHAPE 0x800000000ULL\n"
        if include_shape_macro
        else "/* missing shape */\n"
    )
    (arch_dir / "include" / "acl" / "acl_rt.h").write_text(acl_rt_body, encoding="utf-8")
    (arch_dir / "include" / "acl" / "acl_prof.h").write_text(acl_prof_body, encoding="utf-8")
    (root / "tools" / "mspti" / "include" / "mspti.h").write_text("/* mspti */\n", encoding="utf-8")
    for lib_rel in (
        arch_dir / "lib64" / "libascendcl.so",
        arch_dir / "lib64" / "libmsprofiler.so",
        root / "tools" / "mspti" / "lib64" / "libmspti.so",
        root / "tools" / "profiler" / "bin" / "msprof",
    ):
        lib_rel.write_bytes(b"\x7fELF-stub")
    return root


def test_cann9_version_gate_rejects_8x_and_accepts_9x(tmp_path: Path) -> None:
    with pytest.raises(ProfilerUsageError, match=">= 9.0"):
        parse_cann_version_tuple("8.2.RC1")
    with pytest.raises(ProfilerUsageError, match=">= 9.0"):
        parse_cann_version_tuple("8.0.0")
    assert parse_cann_version_tuple("9.2.1") == (9, 2, "1")

    cann8_dir = _create_synthetic_cann_tree(tmp_path / "cann8", version="8.2.0")
    with pytest.raises(ProfilerUsageError, match=">= 9.0"):
        discover_cann9(cann8_dir, host_machine="aarch64")

    no_hook_dir = _create_synthetic_cann_tree(
        tmp_path / "cann9_no_hook", version="9.0.0", include_injection=False
    )
    with pytest.raises(ProfilerUsageError, match="aclrtApiInjectionSetFunc"):
        discover_cann9(no_hook_dir, host_machine="aarch64")

    cann9_dir = _create_synthetic_cann_tree(tmp_path / "cann-9.2.1", version="9.2.1")
    install = discover_cann9(cann9_dir, host_machine="aarch64")
    assert install.major_version == 9
    assert install.minor_version == 2
    assert install.version == "9.2.1"

    info = parse_cann_install_info("version=9.2.1\ninnerversion=V100\n")
    assert info["version"] == "9.2.1"
    env = build_cann_runtime_env(install, base_env={"LD_LIBRARY_PATH": "/custom/lib"})
    ld_parts = env["LD_LIBRARY_PATH"].split(os.pathsep)
    assert str(install.cann_root / "tools" / "profiler" / "lib64") in ld_parts
    assert ld_parts[-1] == "/custom/lib"


def test_timeout_arithmetic_enforces_principle_10() -> None:
    resolved = _validate_timeout_budgets(
        warmup_timeout_s=30.0,
        capture_timeout_s=20.0,
        export_timeout_s=40.0,
        cleanup_grace_s=10.0,
        outer_timeout_s=None,
    )
    assert resolved == 100.0

    with pytest.raises(ProfilerUsageError, match="Principle 10"):
        _validate_timeout_budgets(
            warmup_timeout_s=30.0,
            capture_timeout_s=20.0,
            export_timeout_s=40.0,
            cleanup_grace_s=10.0,
            outer_timeout_s=95.0,
        )


def test_l3_steady_audit_detects_rampup_and_graph_contamination() -> None:
    # Clean 5 steps, each 2000 us (2,000,000 ns) -> sum_ns = 10_000_000, sum_sq_us = 5 * 4_000_000 = 20_000_000
    clean_worker = {
        "captured_steps": 5,
        "graph_captures_in_window": 0,
        "allocs_in_window": 0,
        "mspti_records_dropped": 0,
        "window_capture_sum_step_ns": 10_000_000,
        "window_capture_sum_sq_us": 20_000_000,
    }
    clean_audit = audit_worker_steady_state(
        clean_worker,
        target_capture_steps=5,
        max_cv_ppm=100_000,
        require_zero_alloc_steps=True,
    )
    assert clean_audit["transient_contaminated"] is False
    assert clean_audit["complete_window"] is True
    assert clean_audit["captured_step_cv_ppm"] == 0
    assert clean_audit["audit_flags"] == []

    # Ramp-up spike inside capture window: [10000 us, 2000 us, 2000 us, 2000 us, 2000 us]
    # sum = 18_000_000 ns, sum_sq_us = 100_000_000 + 4 * 4_000_000 = 116_000_000
    spiky_worker = {
        "captured_steps": 5,
        "graph_captures_in_window": 1,
        "allocs_in_window": 2,
        "mspti_records_dropped": 0,
        "window_capture_sum_step_ns": 18_000_000,
        "window_capture_sum_sq_us": 116_000_000,
    }
    spiky_audit = audit_worker_steady_state(
        spiky_worker,
        target_capture_steps=5,
        max_cv_ppm=100_000,
        require_zero_alloc_steps=True,
    )
    assert spiky_audit["transient_contaminated"] is True
    flags = " ".join(spiky_audit["audit_flags"])
    assert "graph_capture_during_window:1" in flags
    assert "hbm_malloc_churn_during_window:2" in flags
    assert "captured_step_cv_spike:" in flags


def test_gear1_payload_aggregation_classifies_blocks_without_double_counting_comm() -> None:
    raw = {
        "observed_event_span_ns": 10_000_000,
        "device_busy_union_ns": 8_500_000,
        "exposed_comm_ns": 1_500_000,
        "device_uncovered_ns": 1_500_000,
        "interval_count": 30,
        "interval_overflow": False,
        "operators": [
            {
                "kind": "kernel",
                "op_type": "KERNEL_MIX_AIV",
                "name": "FlashAttentionScore",
                "comm_name": "",
                "count": 10,
                "total_ns": 4_000_000,
                "min_ns": 390_000,
                "max_ns": 410_000,
                "bw_gbps_mean": 0.0,
            },
            {
                "kind": "kernel",
                "op_type": "KERNEL_AICORE",
                "name": "GroupedMatmulV4",
                "comm_name": "",
                "count": 10,
                "total_ns": 3_000_000,
                "min_ns": 295_000,
                "max_ns": 305_000,
                "bw_gbps_mean": 0.0,
            },
            {
                "kind": "hccl",
                "op_type": "HCCL",
                "name": "hcom_allReduce__901",
                "comm_name": "tp_group",
                "count": 10,
                "total_ns": 2_000_000,
                "min_ns": 190_000,
                "max_ns": 210_000,
                "bw_gbps_mean": 142.5,
            },
            {
                "kind": "comm",
                "op_type": "MESH",
                "name": "hcom_allReduce__logical",
                "comm_name": "tp_group",
                "count": 10,
                "total_ns": 2_050_000,
                "min_ns": 200_000,
                "max_ns": 215_000,
                "bw_gbps_mean": 0.0,
            },
        ],
    }
    agg = _aggregate_gear1_worker_payload(raw, top_n=8)
    # Activity sum counts physical kernel + hccl (4 + 3 + 2 = 9 ms), NOT logical comm wrapper
    assert agg["device_activity_sum_ms"] == 9.0
    assert agg["device_busy_union_ms"] == 8.5
    assert agg["exposed_comm_ms"] == 1.5
    assert agg["underfeed_bubble_ratio"] == 0.15
    assert agg["block_activity_ms"]["Attention"] == 4.0
    assert agg["block_activity_ms"]["MoE"] == 3.0
    assert agg["block_activity_ms"]["Comm"] == 2.0


def test_shm_control_plane_roundtrip_and_cli_contract(tmp_path: Path) -> None:
    assert mark_capture_step() is False

    shm_path = resolve_shm_backing_path("unit_sess_01", shm_dir=tmp_path)
    out_dir = tmp_path / "cap_out"
    out_dir.mkdir()
    with CaptureShmSession(shm_path, create=True, unlink_on_close=False) as writer:
        gen = writer.configure_run(
            session_id="unit_sess_01",
            output_dir=out_dir,
            gear=GEAR_FAST_MSPTI,
            control_mode=MODE_COORDINATED,
            desired_phase=PHASE_ARMED,
            min_warmup_steps=3,
            steady_window_steps=4,
            target_capture_steps=6,
            max_cv_ppm=120_000,
        )
        assert gen == 1
        # Simulate one NPU worker claiming slot 0
        slot0 = writer.view.slots[0]
        slot0.pid = 4242
        slot0.logical_device_id = 0
        slot0.physical_device_id = 3
        slot0.acked_generation = 1
        slot0.worker_state = WORKER_GATE_READY
        slot0.total_steps = 7
        slot0.claimed = 2

        with CaptureShmSession(shm_path, create=False, unlink_on_close=False) as reader:
            snap = reader.snapshot_workers(generation=1)
            assert len(snap) == 1
            assert reader.snapshot_workers(generation=2) == []
            assert snap[0]["pid"] == 4242
            assert snap[0]["physical_device_id"] == 3
            assert snap[0]["worker_state"] == "gate_ready"
            reader.set_phase(PHASE_START_NOW)
            assert writer.view.header.desired_phase == PHASE_START_NOW

        slot0.worker_state = WORKER_DONE
        slot0.captured_steps = 6
        slot0.summary_written = 1
        del slot0

    shm_path.unlink(missing_ok=True)
    with pytest.raises(SystemExit) as excinfo:
        cli_root.main(["capture", "--help"])
    assert excinfo.value.code == 0
    assert cli_root.main(["capture"]) == 2


def test_pipe_drainer_incomplete_window_and_shared_export_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys
    import time

    # 1. PipeTailDrainer drains multi-MiB child stdout/stderr without blocking pipes
    chatty = subprocess.Popen(
        [
            sys.executable,
            "-c",
            "import sys; chunk = 'X' * 65536 + '\\n';\n"
            "for _ in range(48): sys.stdout.write(chunk); sys.stderr.write(chunk)\n"
            "sys.stderr.write('TAIL_MARKER_OK\\n')",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    drainer = PipeTailDrainer(chatty.stdout, chatty.stderr, max_bytes=2048)
    assert chatty.wait(timeout=5.0) == 0
    out_tail, err_tail = drainer.finish(timeout_s=1.0)
    assert len(out_tail) <= 2048
    assert "TAIL_MARKER_OK" in err_tail

    # 2. Shared export deadline stops immediately without a 5s floor when budget expires
    cann_dir = _create_synthetic_cann_tree(tmp_path / "cann_exp", version="9.2.1")
    install = discover_cann9(cann_dir, host_machine="aarch64")
    w_dirs: list[Path] = []
    for idx in range(3):
        wd = tmp_path / "gen_1" / f"rank_{idx}"
        (wd / f"PROF_{idx}").mkdir(parents=True)
        w_dirs.append(wd)
    if os.name == "nt":
        slow_msprof = tmp_path / "slow_msprof.cmd"
        slow_msprof.write_text(f'@"{sys.executable}" -c "import time; time.sleep(0.4)"\r\n', encoding="utf-8")
    else:
        slow_msprof = tmp_path / "slow_msprof.py"
        slow_msprof.write_text("#!/usr/bin/env python3\nimport time\ntime.sleep(0.4)\n", encoding="utf-8")
        slow_msprof.chmod(0o755)
    install_slow = type(install)(**(install.__dict__ if hasattr(install, "__dict__") else {f: getattr(install, f) for f in install.__dataclass_fields__} | {"msprof_bin": slow_msprof}))
    t0 = time.monotonic()
    _, c7_rep, exp_errs = _export_and_analyze_gear2(
        install_slow,
        w_dirs,
        gen_out_dir=tmp_path / "gen_1",
        export_deadline=t0 + 0.15,
        export_timeout_s=0.15,
        top_n=5,
    )
    elapsed = time.monotonic() - t0
    assert c7_rep is None
    assert elapsed < 1.5
    assert any("msprof_export_timeout_exceeded" in e for e in exp_errs)

    # 3. Incomplete capture window (< target_capture_steps) fails capture_profile honestly
    stub_so = tmp_path / "stub_shim.so"
    stub_so.write_bytes(b"\x7fELF")
    monkeypatch.setattr("mindie_profiler.native_capture.discover_cann9", lambda _r=None: install)
    monkeypatch.setattr(
        "mindie_profiler.native_capture.ensure_capture_shim_binary",
        lambda *_a, **_kw: stub_so,
    )
    shm_p = resolve_shm_backing_path("short_win_sess", shm_dir=tmp_path)
    with CaptureShmSession(shm_p, create=True, unlink_on_close=False) as s:
        s.configure_run(
            session_id="short_win_sess",
            output_dir=tmp_path / "out_short",
            gear=GEAR_FAST_MSPTI,
            control_mode=MODE_COORDINATED,
            desired_phase=PHASE_ARMED,
            min_warmup_steps=1,
            steady_window_steps=1,
            target_capture_steps=6,
            max_cv_ppm=100_000,
            bump_generation=False,
        )
        # Pre-populate a worker that acknowledges gen 1 and exits early with only 2/6 steps
        w_json = tmp_path / "out_short" / "gen_1" / "worker.json"
        w_json.parent.mkdir(parents=True, exist_ok=True)
        w_json.write_text(json.dumps({"operators": []}), encoding="utf-8")
        sl = s.view.slots[0]
        sl.pid = 9999
        sl.acked_generation = 1
        sl.captured_steps = 2
        sl.summary_written = 1
        sl.worker_state = WORKER_DONE
        sl.artifact_path = str(w_json).encode("utf-8")
        sl.claimed = 2
        del sl

    rep = capture_profile(
        attach_session_id="short_win_sess",
        shm_dir=tmp_path,
        output_dir=tmp_path / "out_short",
        gear="fast",
        target_capture_steps=6,
        warmup_timeout_s=1.0,
        capture_timeout_s=1.0,
        cleanup_grace_s=0.2,
    )
    assert rep["status"] == "failed"
    assert any("incomplete_capture_window:slot_0:2/6" in n for n in rep["notes"])
    shm_p.unlink(missing_ok=True)


def _probe_live_cann9_host() -> str | None:
    host = os.environ.get("MINDIE_LIVE_CANN9_HOST", "177.25.23.1")
    try:
        with socket.create_connection((host, 22), timeout=2.0):
            pass
    except OSError:
        return None
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=4", f"root@{host}", "test -d /usr/local/Ascend/cann-9.2.1 && echo OK"],
        env=_ssh_client_env(),
        capture_output=True,
        text=True,
        timeout=8.0,
        check=False,
    )
    if proc.returncode == 0 and "OK" in (proc.stdout or ""):
        return host
    return None


def _pack_profiler_tar() -> bytes:
    repo_root = Path(__file__).resolve().parents[1]
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        tf.add(
            repo_root / "mindie_profiler",
            arcname="mindie_profiler",
            filter=lambda ti: None if "__pycache__" in ti.name else ti,
        )
    return buf.getvalue()


@pytest.mark.live_npu
def test_live_cann921_npugraph_gear1_and_gear2() -> None:
    host = _probe_live_cann9_host()
    if host is None:
        pytest.skip("live CANN 9.2.1 host (177.25.23.1) is unreachable on current network")

    payload_bytes = _pack_profiler_tar()
    remote_script = r"""set -euo pipefail
IDLE_NPUS=($(npu-smi info | grep "No running processes found in NPU" | sed -E "s/.*NPU ([0-9]+).*/\1/" || true))
if [ "${#IDLE_NPUS[@]}" -lt 1 ]; then
  echo "SKIP_NO_IDLE_NPU"
  exit 0
fi
NPU0="${IDLE_NPUS[0]}"

RDIR=$(mktemp -d /tmp/mindie-cann9-cap-XXXXXX)
trap "rm -rf $RDIR" EXIT
tar -xzf - -C "$RDIR"

export HOME="$RDIR/home"
export MINDIE_CONFIG_HOME="$RDIR/cfg"
export MINDIE_DATA_HOME="$RDIR/data"
export MINDIE_DIAGNOSTICS_ROOT="$RDIR/diag"
mkdir -p "$HOME" "$MINDIE_CONFIG_HOME" "$MINDIE_DATA_HOME" "$MINDIE_DIAGNOSTICS_ROOT"

PY=/root/miniconda3/envs/mc2_test/bin/python
export PYTHONPATH="$RDIR:${PYTHONPATH:-}"

cat > "$RDIR/workload_graph.py" << 'PYEOF'
import time
import torch
import torch_npu

x = torch.randn(4096, 4096, device="npu:0", dtype=torch.float16)
w = torch.randn(4096, 4096, device="npu:0", dtype=torch.float16)
for _ in range(2):
    z = torch.matmul(x, w)
torch.npu.synchronize()

g = torch.npu.NPUGraph()
with torch.npu.graph(g):
    y = torch.matmul(x, w)
    y = torch.nn.functional.silu(y)
torch.npu.synchronize()

for step in range(16):
    if step == 0:
        time.sleep(0.030)  # Cold step-0 jitter that SteadyStateGate must skip
    g.replay()
    torch.npu.synchronize()
PYEOF

ASCEND_RT_VISIBLE_DEVICES="$NPU0" "$PY" -m mindie_profiler capture \
  --gear fast \
  --cann-root /usr/local/Ascend/cann-9.2.1 \
  --min-warmup-steps 3 \
  --steady-window-steps 3 \
  --steps 5 \
  --max-cv-pct 25.0 \
  --warmup-timeout-s 30 \
  --capture-timeout-s 20 \
  --output-dir "$RDIR/out_fast" \
  --output "$RDIR/fast.json" \
  -- "$PY" "$RDIR/workload_graph.py" || true

ASCEND_RT_VISIBLE_DEVICES="$NPU0" "$PY" -m mindie_profiler capture \
  --gear deep \
  --cann-root /usr/local/Ascend/cann-9.2.1 \
  --min-warmup-steps 3 \
  --steady-window-steps 3 \
  --steps 5 \
  --max-cv-pct 25.0 \
  --warmup-timeout-s 30 \
  --capture-timeout-s 20 \
  --export-timeout-s 45 \
  --output-dir "$RDIR/out_deep" \
  --output "$RDIR/deep.json" \
  -- "$PY" "$RDIR/workload_graph.py" || true

"$PY" - << 'PYEOF' "$RDIR/fast.json" "$RDIR/deep.json"
import json, sys
fast = json.load(open(sys.argv[1]))
deep = json.load(open(sys.argv[2]))
if fast["status"] != "completed" or deep["status"] != "completed":
    print("DIAG_GEAR12:" + json.dumps({"fast": fast, "deep": deep}))
    sys.exit(1)
print("RESULTS_GEAR12:" + json.dumps({
    "fast_status": fast["status"],
    "fast_contaminated": fast["transient_contaminated"],
    "fast_steps": fast["workers"][0]["captured_steps"],
    "fast_records": fast["workers"][0]["mspti_records_captured"],
    "fast_graph_in_win": fast["workers"][0]["graph_captures_in_window"],
    "fast_hotspots": [h["kernel_name"] for h in fast["workers"][0]["fast_summary"]["hotspots"][:3]],
    "deep_status": deep["status"],
    "deep_contaminated": deep["transient_contaminated"],
    "deep_steps": deep["workers"][0]["captured_steps"],
    "deep_c7_schema": (deep.get("c7_summary") or {}).get("schema_version"),
    "deep_c7_hotspots": [
        {"kernel_name": h["kernel_name"], "call_count": h["call_count"], "input_shapes": h.get("input_shapes")}
        for h in (deep.get("c7_summary") or {}).get("top_hotspot_kernels", [])[:3]
    ],
}))
PYEOF
"""
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", f"root@{host}", remote_script],
        env=_ssh_client_env(),
        input=payload_bytes,
        capture_output=True,
        timeout=85.0,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if "SKIP_NO_IDLE_NPU" in stdout:
        pytest.skip("all NPUs on live host are currently busy with foreign processes")
    assert proc.returncode == 0, f"remote Gear 1/2 test failed (rc={proc.returncode}):\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"

    marker = "RESULTS_GEAR12:"
    line = next((ln for ln in stdout.splitlines() if ln.startswith(marker)), None)
    assert line is not None, f"missing {marker} in stdout:\n{stdout}"
    res = json.loads(line[len(marker):])

    assert res["fast_status"] == "completed"
    assert res["fast_contaminated"] is False
    assert res["fast_steps"] == 5
    assert res["fast_records"] >= 10
    assert res["fast_graph_in_win"] == 0
    assert any("matmul" in k.lower() for k in res["fast_hotspots"])

    assert res["deep_status"] == "completed"
    assert res["deep_contaminated"] is False
    assert res["deep_steps"] == 5
    assert res["deep_c7_schema"] == "mindie-profile-summary/1"
    matmul_rows = [h for h in res["deep_c7_hotspots"] if "matmul" in h["kernel_name"].lower()]
    assert matmul_rows and matmul_rows[0]["call_count"] == 5
    assert "4096" in str(matmul_rows[0].get("input_shapes") or "")
    assert CAPTURE_SCHEMA == "mindie-native-capture/1"


@pytest.mark.live_npu
def test_live_cann921_standby_attach_multi_worker() -> None:
    host = _probe_live_cann9_host()
    if host is None:
        pytest.skip("live CANN 9.2.1 host (177.25.23.1) is unreachable on current network")

    payload_bytes = _pack_profiler_tar()
    remote_script = r"""set -euo pipefail
IDLE_NPUS=($(npu-smi info | grep "No running processes found in NPU" | sed -E "s/.*NPU ([0-9]+).*/\1/" || true))
if [ "${#IDLE_NPUS[@]}" -lt 1 ]; then
  echo "SKIP_NO_IDLE_NPU"
  exit 0
fi
NPU0="${IDLE_NPUS[0]}"
NPU1="${IDLE_NPUS[1]:-$NPU0}"

RDIR=$(mktemp -d /tmp/mindie-cann9-att-XXXXXX)
SESS_ID="live_attach_$$"
trap 'kill ${W1:-} ${W2:-} 2>/dev/null || true; rm -rf "$RDIR" "/dev/shm/mindie_cap_${SESS_ID}.shm"' EXIT
tar -xzf - -C "$RDIR"

export HOME="$RDIR/home"
export MINDIE_CONFIG_HOME="$RDIR/cfg"
export MINDIE_DATA_HOME="$RDIR/data"
export MINDIE_DIAGNOSTICS_ROOT="$RDIR/diag"
mkdir -p "$HOME" "$MINDIE_CONFIG_HOME" "$MINDIE_DATA_HOME" "$MINDIE_DIAGNOSTICS_ROOT"

PY=/root/miniconda3/envs/mc2_test/bin/python
export PYTHONPATH="$RDIR:${PYTHONPATH:-}"

"$PY" -m mindie_profiler capture \
  --prepare-session "$SESS_ID" \
  --gear fast \
  --cann-root /usr/local/Ascend/cann-9.2.1 \
  --output-dir "$RDIR/out_attach" \
  --output "$RDIR/standby.json"

cat > "$RDIR/standing_worker.py" << 'PYEOF'
import time
import torch
import torch_npu
from mindie_profiler import mark_capture_step

x = torch.randn(2048, 2048, device="npu:0", dtype=torch.float16)
w = torch.randn(2048, 2048, device="npu:0", dtype=torch.float16)
deadline = time.monotonic() + 55.0
while time.monotonic() < deadline:
    y = torch.matmul(x, w)
    torch.npu.synchronize()
    mark_capture_step()
    time.sleep(0.015)
PYEOF

eval "$("$PY" -c 'import json, shlex, sys; d=json.load(open(sys.argv[1]))["inject_env"]; print("\n".join(f"export {k}={shlex.quote(v)}" for k,v in d.items()))' "$RDIR/standby.json")"
ASCEND_RT_VISIBLE_DEVICES="$NPU0" "$PY" "$RDIR/standing_worker.py" >/dev/null 2>&1 &
W1=$!
ASCEND_RT_VISIBLE_DEVICES="$NPU1" "$PY" "$RDIR/standing_worker.py" >/dev/null 2>&1 &
W2=$!
unset LD_PRELOAD MINDIE_CAPTURE_SHM_PATH MINDIE_CAPTURE_LIBASCENDCL MINDIE_CAPTURE_LIBMSPTI

"$PY" -m mindie_profiler capture \
  --attach "$SESS_ID" \
  --gear fast \
  --cann-root /usr/local/Ascend/cann-9.2.1 \
  --min-warmup-steps 3 \
  --steady-window-steps 3 \
  --steps 4 \
  --max-cv-pct 25.0 \
  --expected-workers 2 \
  --warmup-timeout-s 30 \
  --capture-timeout-s 15 \
  --output-dir "$RDIR/out_attach" \
  --output "$RDIR/attach.json" || true

"$PY" -m mindie_profiler capture \
  --attach "$SESS_ID" \
  --gear fast \
  --cann-root /usr/local/Ascend/cann-9.2.1 \
  --min-warmup-steps 2 \
  --steady-window-steps 2 \
  --steps 3 \
  --max-cv-pct 25.0 \
  --expected-workers 2 \
  --warmup-timeout-s 30 \
  --capture-timeout-s 15 \
  --output-dir "$RDIR/out_attach" \
  --output "$RDIR/attach_gen2.json" || true

kill "$W1" "$W2" 2>/dev/null || true
wait "$W1" "$W2" 2>/dev/null || true

"$PY" - << 'PYEOF' "$RDIR/attach.json" "$RDIR/attach_gen2.json"
import json, sys
attach = json.load(open(sys.argv[1]))
attach2 = json.load(open(sys.argv[2]))
if attach["status"] != "completed" or attach2["status"] != "completed":
    print("DIAG_ATTACH:" + json.dumps({"g1": attach, "g2": attach2}))
    sys.exit(1)
print("RESULTS_ATTACH:" + json.dumps({
    "attach_status": attach["status"],
    "attach_workers": attach["worker_count"],
    "attach_skew_ms": attach["multi_worker_barrier_skew_ms"],
    "attach_steps": [w["captured_steps"] for w in attach["workers"]],
    "attach2_gen": attach2["generation"],
    "attach2_steps": [w["captured_steps"] for w in attach2["workers"]],
    "attach_records": [w["mspti_records_captured"] for w in attach["workers"]],
    "attach_w0_hotspots": [h["kernel_name"] for h in attach["workers"][0]["fast_summary"]["hotspots"][:2]],
    "attach_w1_hotspots": [h["kernel_name"] for h in attach["workers"][1]["fast_summary"]["hotspots"][:2]],
}))
PYEOF
"""
    proc = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", f"root@{host}", remote_script],
        env=_ssh_client_env(),
        input=payload_bytes,
        capture_output=True,
        timeout=60.0,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    if "SKIP_NO_IDLE_NPU" in stdout:
        pytest.skip("all NPUs on live host are currently busy with foreign processes")
    assert proc.returncode == 0, f"remote Attach test failed (rc={proc.returncode}):\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"

    marker = "RESULTS_ATTACH:"
    line = next((ln for ln in stdout.splitlines() if ln.startswith(marker)), None)
    assert line is not None, f"missing {marker} in stdout:\n{stdout}"
    res = json.loads(line[len(marker):])
    assert res["attach_status"] == "completed"
    assert res["attach_workers"] == 2
    assert res["attach_steps"] == [4, 4]
    assert res["attach2_gen"] == 2
    assert res["attach2_steps"] == [3, 3]
    assert all(r >= 4 for r in res["attach_records"]), res
    assert any("matmul" in k.lower() for k in res["attach_w0_hotspots"])
    assert any("matmul" in k.lower() for k in res["attach_w1_hotspots"])
    assert res["attach_skew_ms"] is not None and res["attach_skew_ms"] < 50.0


def test_session_exclusivity_empty_window_and_overflow_limitations(tmp_path: Path) -> None:
    shm_p = tmp_path / "mindie_cap_dup"
    with CaptureShmSession(shm_p, create=True, unlink_on_close=False):
        with pytest.raises(ProfilerUsageError, match="already exists"):
            CaptureShmSession(shm_p, create=True, unlink_on_close=False)
    shm_p.unlink(missing_ok=True)

    empty_sum = _aggregate_gear1_worker_payload({"interval_count": 0, "operators": []}, top_n=5)
    assert empty_sum["observed_event_span_ms"] is None
    assert empty_sum["device_busy_union_ms"] is None
    assert empty_sum["exposed_comm_ms"] is None
    assert empty_sum["block_activity_ms"]["Attention"] is None
    assert [it["code"] for it in empty_sum["limitations"]] == ["empty_window"]

    ovf_sum = _aggregate_gear1_worker_payload(
        {
            "interval_count": 2,
            "interval_overflow": True,
            "operator_table_overflow": True,
            "operator_records_dropped": 17,
            "observed_event_span_ns": 20_000,
            "device_busy_union_ns": 15_000,
            "device_uncovered_ns": 5_000,
            "exposed_comm_ns": 0,
            "operators": [{"kind": "kernel", "op_type": "MatMul", "name": "MatMulV2", "count": 2, "total_ns": 15_000, "min_ns": 7_000, "max_ns": 8_000}],
        },
        top_n=5,
    )
    assert ovf_sum["operator_table_overflow"] is True
    assert ovf_sum["operator_records_dropped"] == 17
    assert {it["code"] for it in ovf_sum["limitations"]} == {"operator_table_overflow", "interval_overflow"}
