"""CANN 9.x framework-agnostic steady-state NPU profiling collector.

[Role]
  Orchestrate Gear-1 (MSPTI in-memory kernel/HCCL/comm summary, zero ``msprof``)
  and Gear-2 (sniper ``aclprofStart``/``aclprofStop`` + bounded ``msprof`` export
  + C7 ``analyze_profile``) captures in both Launch Mode and Attach Mode over
  the ``/dev/shm`` multi-worker control plane.

[Invariants]
  * Enforces ``outer_timeout_s >= warmup_timeout_s + capture_timeout_s +
    export_timeout_s + cleanup_grace_s`` (Principle 10).
  * Distinguishes ``completed`` and ``failed`` honestly; incomplete capture
    windows fail the run, while ``transient_contaminated`` is audited
    post-capture from measured window invariants (L3 gate).
  * Never imports ``torch_npu`` or creates NPU device contexts in the controller.

[Timeouts & Locks]
  Bounded polling loop (10 ms cadence) over ``CaptureShmSession`` with background
  pipe draining; subprocess calls always re-raise ``TimeoutError`` before ``OSError``.

[Side-Effect Policy]
  Writes per-generation outputs under ``output_dir/gen_<N>`` and optional
  ``output`` JSON via atomic ``os.replace``.  Cleans up launch ``/dev/shm`` files.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

from .cann_abi import Cann9Installation, build_cann_runtime_env, discover_cann9, ensure_capture_shim_binary
from .classify import EVENT_BLOCKS, classify_event
from .events import ProfilerError, ProfilerUsageError
from .native_capture_shm import (
    AICORE_METRICS_MAP, DEFAULT_GEAR2_PROF_MASK, GEAR_DEEP_ACLPROF, GEAR_FAST_MSPTI,
    MODE_AUTONOMOUS, MODE_COORDINATED, PHASE_ARMED, PHASE_STANDBY, PHASE_START_NOW, PHASE_STOP_NOW,
    WORKER_CAPTURING, WORKER_DONE, WORKER_ERROR, WORKER_GATE_READY,
    CaptureShmSession, PipeTailDrainer, audit_worker_steady_state, resolve_shm_backing_path, validate_session_id,
)
from .report import write_report
from .segment import discover_rank_sources

CAPTURE_SCHEMA = "mindie-native-capture/1"
_FATAL_NOTE_PREFIXES = (
    "warmup_timeout", "capture_timeout", "process_drain_timeout", "worker_error",
    "incomplete_capture_window", "incomplete_worker_count", "msprof", "analyze_profile",
    "gear2_", "mspti_operator_table_overflow", "mspti_interval_overflow",
    "mspti_records_dropped:", "worker_slot_exhausted:",
    "empty_mspti_capture_window", "worker_json", "target_command_nonzero", "no_npu_workers",
)


def _ns_to_ms(value: int | float | None) -> float | None:
    return None if value is None else round(float(value) / 1_000_000.0, 6)


def _ns_to_us(value: int | float | None) -> float | None:
    return None if value is None else round(float(value) / 1_000.0, 4)


def _resolve_gear(gear: str) -> int:
    folded = (gear or "").strip().lower()
    if folded in {"fast", "gear1", "mspti"}:
        return GEAR_FAST_MSPTI
    if folded in {"deep", "gear2", "aclprof"}:
        return GEAR_DEEP_ACLPROF
    raise ProfilerUsageError(
        f"unsupported capture gear {gear!r}; choose 'fast' (MSPTI) or 'deep' (aclprof)"
    )


def _resolve_aicore_metrics(metrics: str) -> int:
    key = (metrics or "pipe_utilization").strip().lower()
    if key not in AICORE_METRICS_MAP:
        choices = ", ".join(sorted(AICORE_METRICS_MAP))
        raise ProfilerUsageError(
            f"unsupported aicore_metrics {metrics!r}; choose from {choices}"
        )
    return AICORE_METRICS_MAP[key]


def _validate_timeout_budgets(
    *,
    warmup_timeout_s: float,
    capture_timeout_s: float,
    export_timeout_s: float,
    cleanup_grace_s: float,
    outer_timeout_s: float | None,
) -> float:
    for name, val in (
        ("warmup_timeout_s", warmup_timeout_s),
        ("capture_timeout_s", capture_timeout_s),
        ("export_timeout_s", export_timeout_s),
        ("cleanup_grace_s", cleanup_grace_s),
    ):
        if val < 0:
            raise ProfilerUsageError(f"{name} must be >= 0, got {val}")
    required_outer = (
        warmup_timeout_s + capture_timeout_s + export_timeout_s + cleanup_grace_s
    )
    if required_outer <= 0:
        raise ProfilerUsageError("total capture timeout budget must be > 0")
    if outer_timeout_s is None:
        return required_outer
    if outer_timeout_s < required_outer:
        raise ProfilerUsageError(
            f"outer_timeout_s ({outer_timeout_s}s) violates Principle 10: must be >= "
            f"warmup_timeout_s ({warmup_timeout_s}s) + capture_timeout_s ({capture_timeout_s}s) "
            f"+ export_timeout_s ({export_timeout_s}s) + cleanup_grace_s ({cleanup_grace_s}s) "
            f"= {required_outer}s"
        )
    return outer_timeout_s


def build_preload_env(
    install: Cann9Installation,
    shim_so: Path,
    shm_path: Path,
    *,
    gear_code: int,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build runtime environment with CANN 9.x paths and absolute preload libraries."""

    env = build_cann_runtime_env(install, base_env=base_env)
    abs_shim = str(Path(shim_so).expanduser().resolve())
    abs_shm = str(Path(shm_path).expanduser().resolve())
    abs_acl = str(Path(install.libascendcl_so).expanduser().resolve())
    preload_items: list[str] = []
    if gear_code == GEAR_FAST_MSPTI:
        abs_mspti = str(Path(install.libmspti_so).expanduser().resolve())
        preload_items.append(abs_mspti)
        env["MINDIE_CAPTURE_LIBMSPTI"] = abs_mspti
    preload_items.append(abs_shim)
    existing_preload = (env.get("LD_PRELOAD") or "").strip()
    if existing_preload:
        for item in existing_preload.split(":"):
            if item and item not in preload_items:
                preload_items.append(item)
    env["LD_PRELOAD"] = ":".join(preload_items)
    env["MINDIE_CAPTURE_SHM_PATH"] = abs_shm
    env["MINDIE_CAPTURE_LIBASCENDCL"] = abs_acl
    return env


def prepare_standby_session(
    session_id: str,
    *,
    output_dir: str | os.PathLike[str],
    gear: str = "fast",
    cann_root: str | os.PathLike[str] | None = None,
    shm_dir: str | os.PathLike[str] | None = None,
    cache_root: str | os.PathLike[str] | None = None,
) -> dict[str, object]:
    """Create a persistent STANDBY /dev/shm session for long-lived servers."""

    clean_id = validate_session_id(session_id)
    gear_code = _resolve_gear(gear)
    install = discover_cann9(cann_root)
    shim_so = ensure_capture_shim_binary(install, gear=gear, cache_root=cache_root)
    out_path = Path(output_dir).expanduser().resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    shm_path = resolve_shm_backing_path(clean_id, shm_dir=shm_dir)

    with CaptureShmSession(shm_path, create=True, unlink_on_close=False, exclusive_controller=True) as sess:
        sess.configure_run(
            session_id=clean_id, output_dir=out_path, gear=gear_code,
            control_mode=MODE_COORDINATED, desired_phase=PHASE_STANDBY,
            min_warmup_steps=5, steady_window_steps=5, target_capture_steps=10,
            max_cv_ppm=150_000, libmsprofiler_path=str(install.libmsprofiler_so), bump_generation=False,
        )
    preload_env = build_preload_env(install, shim_so, shm_path, gear_code=gear_code)
    inject_keys = (
        "LD_PRELOAD", "MINDIE_CAPTURE_SHM_PATH", "MINDIE_CAPTURE_LIBASCENDCL",
        "MINDIE_CAPTURE_LIBMSPTI", "LD_LIBRARY_PATH", "PATH", "PYTHONPATH",
        "ASCEND_HOME_PATH", "ASCEND_TOOLKIT_HOME", "ASCEND_AICPU_PATH", "ASCEND_OPP_PATH", "TOOLCHAIN_HOME",
    )
    return {
        "schema_version": CAPTURE_SCHEMA,
        "status": "standby_ready",
        "session_id": clean_id,
        "gear": "fast" if gear_code == GEAR_FAST_MSPTI else "deep",
        "shm_path": str(shm_path),
        "shim_so": str(shim_so),
        "output_dir": str(out_path),
        "cann": install.as_dict(),
        "inject_env": {k: preload_env[k] for k in inject_keys if k in preload_env},
    }


def _aggregate_gear1_worker_payload(
    raw_worker: Mapping[str, object],
    *,
    top_n: int,
) -> dict[str, object]:
    operators = list(raw_worker.get("operators") or [])
    block_ns: dict[str, int] = {block: 0 for block in EVENT_BLOCKS}
    total_activity_ns = 0
    enriched_ops: list[dict[str, object]] = []

    for op in operators:
        if not isinstance(op, Mapping):
            continue
        kind = str(op.get("kind") or "kernel")
        op_type = str(op.get("op_type") or "")
        name = str(op.get("name") or "unknown")
        count = int(op.get("count") or 0)
        total_ns = int(op.get("total_ns") or 0)
        min_ns = int(op.get("min_ns") or 0)
        max_ns = int(op.get("max_ns") or 0)
        cls = classify_event(
            name=name, op_type=op_type if kind != "kernel" else "",
            task_type=op_type if kind == "kernel" else "",
            table="COMMUNICATION_OP" if kind in {"hccl", "comm"} else "",
        )
        if kind in {"kernel", "hccl"}:
            block_ns[cls.block] = block_ns.get(cls.block, 0) + total_ns
            total_activity_ns += total_ns
        enriched_ops.append({
            "kind": kind, "kernel_name": name, "op_type": op_type,
            "comm_name": op.get("comm_name") or None, "semantic_block": cls.block,
            "execution_engine": cls.execution_engine, "call_count": count,
            "total_ms": _ns_to_ms(total_ns),
            "mean_us": _ns_to_us(total_ns / count) if count > 0 else None,
            "min_us": _ns_to_us(min_ns) if count > 0 else None,
            "max_us": _ns_to_us(max_ns) if count > 0 else None,
            "bw_gbps_mean": round(float(op.get("bw_gbps_mean") or 0.0), 4) if kind == "hccl" else None,
            "_total_ns": total_ns,
        })

    enriched_ops.sort(key=lambda item: (int(item["_total_ns"]), str(item["kernel_name"])), reverse=True)
    hotspots: list[dict[str, object]] = []
    for item in enriched_ops[: max(1, top_n)]:
        row = {k: v for k, v in item.items() if k != "_total_ns"}
        row["share_of_activity_pct"] = (
            round(100.0 * float(item["_total_ns"]) / float(total_activity_ns), 4)
            if total_activity_ns > 0 and item["kind"] in {"kernel", "hccl"}
            else None
        )
        hotspots.append(row)

    interval_count = int(raw_worker.get("interval_count") or 0)
    interval_overflow = bool(raw_worker.get("interval_overflow"))
    op_overflow = bool(raw_worker.get("operator_table_overflow"))
    op_dropped = int(raw_worker.get("operator_records_dropped") or 0)
    empty_window = interval_count == 0 and total_activity_ns == 0
    limitations: list[dict[str, str]] = []
    if empty_window:
        limitations.append({"code": "empty_window", "detail": "No MSPTI kernel or HCCL activities were recorded in the captured window."})
    if op_overflow:
        limitations.append({"code": "operator_table_overflow", "detail": f"MSPTI operator table exceeded 4096 distinct keys ({op_dropped} records omitted)."})
    if interval_overflow:
        limitations.append({"code": "interval_overflow", "detail": "MSPTI interval ring exceeded capacity; union timing is incomplete."})

    span_ns = int(raw_worker.get("observed_event_span_ns") or 0)
    busy_ns = int(raw_worker.get("device_busy_union_ns") or 0)
    uncovered_ns = int(raw_worker.get("device_uncovered_ns") or 0)
    exposed_comm_ns = int(raw_worker.get("exposed_comm_ns") or 0)

    return {
        "observed_event_span_ms": None if empty_window else _ns_to_ms(span_ns),
        "device_busy_union_ms": None if empty_window else _ns_to_ms(busy_ns),
        "device_activity_sum_ms": None if empty_window else _ns_to_ms(total_activity_ns),
        "exposed_comm_ms": None if empty_window else _ns_to_ms(exposed_comm_ns),
        "device_uncovered_ms": None if empty_window else _ns_to_ms(uncovered_ns),
        "underfeed_bubble_ratio": (
            round(float(uncovered_ns) / float(span_ns), 6) if (not empty_window and span_ns > 0) else None
        ),
        "interval_count": interval_count,
        "interval_overflow": interval_overflow,
        "operator_table_overflow": op_overflow,
        "operator_records_dropped": op_dropped,
        "distinct_operator_count": len(enriched_ops),
        "limitations": limitations,
        "block_activity_ms": {
            block: (None if empty_window else _ns_to_ms(ns_val)) for block, ns_val in block_ns.items()
        },
        "block_share_pct": {
            block: (
                None if empty_window else (round(100.0 * float(ns_val) / float(total_activity_ns), 4) if total_activity_ns > 0 else 0.0)
            )
            for block, ns_val in block_ns.items()
        },
        "hotspots": hotspots,
    }


def _export_and_analyze_gear2(
    install: Cann9Installation,
    worker_dirs: Sequence[Path],
    *,
    gen_out_dir: Path,
    export_deadline: float,
    export_timeout_s: float,
    top_n: int,
) -> tuple[list[dict[str, object]], dict[str, object] | None, list[str]]:
    env = build_cann_runtime_env(install)
    prof_dirs: list[Path] = []
    export_receipts: list[dict[str, object]] = []
    errors: list[str] = []
    for idx, wdir in enumerate(worker_dirs):
        w_profs = sorted(wdir.glob("PROF_*")) if wdir.is_dir() else []
        if not w_profs:
            errors.append(f"msprof_missing_prof_dir_for_worker:{idx}:{wdir}")
        prof_dirs.extend(w_profs)
    if errors or not prof_dirs:
        return export_receipts, None, errors or ["msprof_no_prof_dirs_produced_by_aclprof"]

    popen_kwargs: dict[str, object] = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    for prof_dir in prof_dirs:
        remaining = export_deadline - time.monotonic()
        if remaining <= 0:
            errors.append(f"msprof_export_timeout_exceeded:{export_timeout_s}s")
            break
        cmd = [str(install.msprof_bin), "--export=on", f"--output={prof_dir}"]
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd, env=env, capture_output=True, text=True,
                timeout=remaining, check=False, **popen_kwargs,
            )
        except subprocess.TimeoutExpired:
            errors.append(f"msprof_export_timeout_exceeded:{export_timeout_s}s on {prof_dir}")
            break
        except TimeoutError:
            raise
        except OSError as exc:
            errors.append(f"msprof invocation failed on {prof_dir}: {exc}")
            continue
        elapsed_ms = round((time.monotonic() - t0) * 1000.0, 2)
        export_receipts.append({"prof_dir": str(prof_dir), "returncode": proc.returncode, "elapsed_ms": elapsed_ms})
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip()[-400:]
            errors.append(f"msprof --export=on failed (rc={proc.returncode}) on {prof_dir}: {tail}")

    c7_report: dict[str, object] | None = None
    if not errors:
        for prof_dir in prof_dirs:
            try:
                if not discover_rank_sources(prof_dir):
                    errors.append(f"msprof_missing_exported_source:{prof_dir}")
            except ProfilerError as exc:
                errors.append(f"msprof_missing_exported_source:{prof_dir}:{exc}")
    if not errors:
        rem_analyze = export_deadline - time.monotonic()
        if rem_analyze <= 0:
            errors.append(f"gear2_analyze_timeout_exceeded:{export_timeout_s}s")
            return export_receipts, None, errors
        per_rank_timeout = max(0.05, rem_analyze / max(1, len(prof_dirs)))
        analyze_root = prof_dirs[0] if len(prof_dirs) == 1 else gen_out_dir
        c7_tmp = gen_out_dir / f".c7_analyze_{uuid.uuid4().hex[:8]}.json"
        pkg_root = str(Path(__file__).resolve().parents[1])
        py_path = f"{pkg_root}{os.pathsep}{os.environ['PYTHONPATH']}" if os.environ.get("PYTHONPATH") else pkg_root
        analyze_cmd = [
            sys.executable, "-m", "mindie_profiler", "analyze", "--root", str(analyze_root),
            "--full-range", "--top", str(top_n), "--query-timeout-s", f"{per_rank_timeout:.4f}",
            "--csv-timeout-s", f"{per_rank_timeout:.4f}", "--output", str(c7_tmp),
        ]
        try:
            proc_an = subprocess.run(
                analyze_cmd, env={**os.environ, "PYTHONPATH": py_path},
                capture_output=True, text=True, timeout=rem_analyze, check=False, **popen_kwargs,
            )
            if proc_an.returncode != 0:
                tail = (proc_an.stderr or proc_an.stdout or "").strip()[-300:]
                errors.append(f"analyze_profile failed on exported Gear-2 root: {tail}")
            else:
                c7_report = json.loads(c7_tmp.read_text(encoding="utf-8"))
                lims = c7_report.get("limitations") if isinstance(c7_report, Mapping) else None
                timed_out_lim = isinstance(lims, list) and any(
                    isinstance(it, Mapping) and str(it.get("code") or "") in {"query_timeout", "csv_timeout"}
                    for it in lims
                )
                if timed_out_lim or time.monotonic() > export_deadline:
                    errors.append(f"gear2_analyze_timeout_exceeded:{export_timeout_s}s")
                empty_scopes = [
                    str(it.get("scope") or "global") for it in (lims or [])
                    if isinstance(it, Mapping) and str(it.get("code") or "") in {"empty_window", "empty_source"}
                ]
                prov_sources = ((c7_report.get("source_identity") or {}).get("sources") or []) if isinstance(c7_report, Mapping) else []
                if empty_scopes or not (c7_report.get("top_hotspot_kernels") if isinstance(c7_report, Mapping) else None):
                    errors.append(f"gear2_empty_capture_window:{','.join(empty_scopes) or analyze_root}")
                if len(prov_sources) < len(worker_dirs):
                    errors.append(f"gear2_missing_worker_rank_in_c7:{len(prov_sources)}/{len(worker_dirs)}")
        except subprocess.TimeoutExpired:
            errors.append(f"gear2_analyze_timeout_exceeded:{export_timeout_s}s")
        except TimeoutError:
            raise
        except (OSError, ValueError) as exc:
            errors.append(f"analyze_profile failed on exported Gear-2 root: {exc}")
        finally:
            c7_tmp.unlink(missing_ok=True)
    return export_receipts, c7_report, errors


def _pgid_alive(pgid: int | None) -> bool:
    if pgid is None or os.name == "nt":
        return False
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False


def _terminate_process_group(
    proc: subprocess.Popen[bytes] | subprocess.Popen[str],
    pgid: int | None,
    *,
    grace_s: float,
    hard_deadline: float | None = None,
) -> bool:
    proc_was_alive = proc.poll() is None
    if not proc_was_alive and not _pgid_alive(pgid):
        return False
    now = time.monotonic()
    budget = max(0.02, float(grace_s))
    if hard_deadline is not None:
        budget = max(0.02, min(budget, hard_deadline - now))
    end_deadline = now + budget
    kill_reserve = min(0.15, budget * 0.35)
    term_deadline = now + max(0.01, budget - kill_reserve)
    try:
        if os.name != "nt" and pgid is not None:
            os.killpg(pgid, signal.SIGTERM)
        elif proc_was_alive:
            proc.terminate()
    except OSError:
        pass
    while time.monotonic() < term_deadline:
        if proc.poll() is not None and not _pgid_alive(pgid):
            return proc_was_alive
        time.sleep(0.005)
    if proc.poll() is None or _pgid_alive(pgid):
        try:
            if os.name != "nt" and pgid is not None:
                os.killpg(pgid, signal.SIGKILL)
            elif proc.poll() is None:
                proc.kill()
        except OSError:
            pass
        while time.monotonic() < end_deadline:
            if proc.poll() is not None and not _pgid_alive(pgid):
                break
            time.sleep(0.005)
    return proc_was_alive


def capture_profile(
    *,
    command: Sequence[str] | None = None,
    attach_session_id: str | None = None,
    output_dir: str | os.PathLike[str] | None = None,
    output: str | os.PathLike[str] | None = None,
    gear: str = "fast",
    cann_root: str | os.PathLike[str] | None = None,
    shm_dir: str | os.PathLike[str] | None = None,
    cache_root: str | os.PathLike[str] | None = None,
    min_warmup_steps: int = 5,
    steady_window_steps: int = 5,
    target_capture_steps: int = 10,
    max_cv_pct: float = 15.0,
    replays_per_step: int = 1,
    require_zero_alloc_steps: bool = True,
    min_step_interval_us: float = 50.0,
    expected_workers: int = 1,
    coordinated: bool | None = None,
    aicore_metrics: str = "pipe_utilization",
    aclprof_mask: int = DEFAULT_GEAR2_PROF_MASK,
    terminate_after_capture: bool = False,
    warmup_timeout_s: float = 120.0,
    capture_timeout_s: float = 60.0,
    export_timeout_s: float = 90.0,
    cleanup_grace_s: float = 10.0,
    outer_timeout_s: float | None = None,
    top_n: int = 12,
    extra_env: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Execute a steady-state CANN 9.x NPU capture in launch or attach mode."""

    if bool(command) == bool(attach_session_id):
        raise ProfilerUsageError(
            "specify exactly one of 'command' (launch mode) or 'attach_session_id' (attach mode)"
        )
    if expected_workers < 1 or expected_workers > 32:
        raise ProfilerUsageError(
            f"expected_workers must be in 1..32, got {expected_workers}"
        )
    gear_code = _resolve_gear(gear)
    metrics_code = _resolve_aicore_metrics(aicore_metrics)
    effective_export_s = export_timeout_s if gear_code == GEAR_DEEP_ACLPROF else 0.0
    resolved_outer_s = _validate_timeout_budgets(
        warmup_timeout_s=warmup_timeout_s,
        capture_timeout_s=capture_timeout_s,
        export_timeout_s=effective_export_s,
        cleanup_grace_s=cleanup_grace_s,
        outer_timeout_s=outer_timeout_s,
    )

    install = discover_cann9(cann_root)
    shim_so = ensure_capture_shim_binary(install, gear=gear, cache_root=cache_root)
    is_attach = attach_session_id is not None
    session_id = (
        validate_session_id(attach_session_id)
        if attach_session_id is not None
        else f"cap_{uuid.uuid4().hex[:12]}"
    )
    out_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir is not None
        else Path.cwd() / "mindie_captures" / session_id
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    shm_path = resolve_shm_backing_path(session_id, shm_dir=shm_dir)
    use_coordinated = (
        (expected_workers > 1 or is_attach) if coordinated is None else bool(coordinated)
    )
    control_mode = MODE_COORDINATED if use_coordinated else MODE_AUTONOMOUS
    max_cv_ppm = max(0, int(round(max_cv_pct * 10_000.0)))

    t_begin = time.monotonic()
    outer_deadline = t_begin + resolved_outer_s
    proc: subprocess.Popen[bytes] | None = None
    pgid: int | None = None
    drainer: PipeTailDrainer | None = None
    process_exit_code: int | None = None
    process_stderr_tail = ""
    barrier_skew_ms: float | None = None
    controller_terminated_after_capture = False
    controller_notes: list[str] = []

    with CaptureShmSession(
        shm_path, create=not is_attach, unlink_on_close=not is_attach, exclusive_controller=True
    ) as sess:
        if is_attach and int(sess.view.header.gear) != gear_code:
            raise ProfilerUsageError(
                f"attached session {session_id!r} was initialized with gear="
                f"{sess.view.header.gear}, cannot switch to gear={gear!r} mid-process"
            )
        next_gen = int(sess.view.header.generation) + 1
        gen_out_dir = out_dir / f"gen_{next_gen}"
        gen_out_dir.mkdir(parents=True, exist_ok=True)
        generation = sess.configure_run(
            session_id=session_id, output_dir=gen_out_dir, gear=gear_code,
            control_mode=control_mode, desired_phase=PHASE_ARMED,
            min_warmup_steps=min_warmup_steps, steady_window_steps=steady_window_steps,
            target_capture_steps=target_capture_steps, max_cv_ppm=max_cv_ppm,
            replays_per_step=replays_per_step, require_zero_alloc_steps=require_zero_alloc_steps,
            min_step_interval_ns=int(round(min_step_interval_us * 1000.0)),
            aclprof_data_type_mask=aclprof_mask, aclprof_aicore_metrics=metrics_code,
            libmsprofiler_path=str(install.libmsprofiler_so), bump_generation=True,
        )

        if command is not None:
            merged_env = {**os.environ, **{str(k): str(v) for k, v in extra_env.items()}} if extra_env else None
            launch_env = build_preload_env(
                install, shim_so, shm_path, gear_code=gear_code, base_env=merged_env
            )
            popen_kwargs: dict[str, object] = (
                {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}
                if os.name == "nt"
                else {"start_new_session": True}
            )
            try:
                proc = subprocess.Popen(
                    list(command), env=launch_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **popen_kwargs
                )
                pgid = proc.pid if os.name != "nt" else None
                drainer = PipeTailDrainer(proc.stdout, proc.stderr)
            except TimeoutError:
                raise
            except OSError as exc:
                raise ProfilerError(f"failed to launch target command: {exc}") from exc

        non_export_deadline = outer_deadline - effective_export_s
        active_run_deadline = non_export_deadline - cleanup_grace_s
        warmup_deadline = min(active_run_deadline, t_begin + warmup_timeout_s)
        capture_deadline = min(active_run_deadline, warmup_deadline + capture_timeout_s)
        capture_started = False

        try:
            while True:
                now = time.monotonic()
                workers = sess.snapshot_workers(generation=generation)
                if proc is not None and proc.poll() is not None:
                    process_exit_code = proc.returncode
                    break

                if workers:
                    all_finished = len(workers) >= expected_workers and all(
                        w["worker_state_code"] in {WORKER_DONE, WORKER_ERROR}
                        and (w["summary_written"] or w["worker_state_code"] == WORKER_ERROR)
                        for w in workers
                    )
                    if all_finished:
                        if proc is not None and terminate_after_capture:
                            controller_terminated_after_capture = _terminate_process_group(
                                proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline
                            )
                            process_exit_code = proc.returncode
                        break

                    if not capture_started:
                        if control_mode == MODE_COORDINATED:
                            if any(w["worker_state_code"] == WORKER_ERROR for w in workers):
                                sess.set_phase(PHASE_STOP_NOW)
                                controller_notes.append("worker_error_aborted")
                                break
                            ready = [w for w in workers if w["worker_state_code"] == WORKER_GATE_READY]
                            if len(ready) >= expected_workers:
                                sess.set_phase(PHASE_START_NOW)
                                capture_started = True
                                capture_deadline = min(active_run_deadline, now + capture_timeout_s)
                        elif any(w["worker_state_code"] in {WORKER_CAPTURING, WORKER_DONE} for w in workers):
                            capture_started = True
                            capture_deadline = min(active_run_deadline, now + capture_timeout_s)

                if not capture_started and now >= warmup_deadline:
                    sess.set_phase(PHASE_STOP_NOW)
                    controller_notes.append(f"warmup_timeout_exceeded:{warmup_timeout_s}s")
                    if proc is not None:
                        _terminate_process_group(proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline)
                        process_exit_code = proc.returncode
                    break

                if capture_started and now >= capture_deadline:
                    sess.set_phase(PHASE_STOP_NOW)
                    controller_notes.append(f"capture_timeout_exceeded:{capture_timeout_s}s")
                    if proc is not None:
                        _terminate_process_group(proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline)
                        process_exit_code = proc.returncode
                    break

                time.sleep(0.01)

            if proc is not None and proc.poll() is None:
                remaining = active_run_deadline - time.monotonic()
                if remaining <= 0:
                    _terminate_process_group(proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline)
                    process_exit_code = proc.returncode
                    controller_notes.append("process_drain_timeout_terminated")
                else:
                    try:
                        proc.wait(timeout=remaining)
                        process_exit_code = proc.returncode
                    except subprocess.TimeoutExpired:
                        _terminate_process_group(proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline)
                        process_exit_code = proc.returncode
                        controller_notes.append("process_drain_timeout_terminated")
            elif proc is not None:
                process_exit_code = proc.returncode
        finally:
            if is_attach:
                sess.set_phase(PHASE_STOP_NOW)
                stop_wait_end = min(non_export_deadline, time.monotonic() + max(0.02, cleanup_grace_s))
                while time.monotonic() < stop_wait_end:
                    active_now = sess.snapshot_workers(generation=generation)
                    if not any(w["worker_state_code"] == WORKER_CAPTURING for w in active_now):
                        break
                    time.sleep(0.01)
                sess.set_phase(PHASE_STANDBY)
            elif proc is not None and (proc.poll() is None or _pgid_alive(pgid)):
                _terminate_process_group(proc, pgid, grace_s=cleanup_grace_s, hard_deadline=non_export_deadline)
            if drainer is not None:
                drain_t = max(0.02, min(max(0.05, cleanup_grace_s), non_export_deadline - time.monotonic()))
                _, stderr_tail = drainer.finish(timeout_s=drain_t)
                process_stderr_tail = stderr_tail.strip()[-800:]

        final_workers = sess.snapshot_workers(generation=generation)
        slot_overflow = sess.slot_overflow_count

    start_times = [int(w["capture_start_mono_ns"]) for w in final_workers if int(w["capture_start_mono_ns"]) > 0]
    if len(start_times) >= 2:
        barrier_skew_ms = _ns_to_ms(max(start_times) - min(start_times))

    worker_reports: list[dict[str, object]] = []
    gear2_dirs: list[Path] = []
    any_contaminated = False
    all_workers_ok = len(final_workers) >= expected_workers and slot_overflow == 0
    if slot_overflow > 0:
        controller_notes.append(f"worker_slot_exhausted:{slot_overflow}")
    if final_workers and len(final_workers) < expected_workers:
        controller_notes.append(
            f"incomplete_worker_count:{len(final_workers)}/{expected_workers}"
        )

    for w in final_workers:
        audit = audit_worker_steady_state(
            w,
            target_capture_steps=target_capture_steps,
            max_cv_ppm=max_cv_ppm,
            require_zero_alloc_steps=require_zero_alloc_steps,
        )
        any_contaminated = any_contaminated or bool(audit["transient_contaminated"])
        art_str = str(w.get("artifact_path") or "").strip()
        w_entry: dict[str, object] = {
            **w,
            "window_mean_ms": _ns_to_ms(int(w.get("window_mean_ns") or 0)),
            "steady_audit": audit,
        }
        if int(w["last_error_code"]) != 0 or int(w["worker_state_code"]) == WORKER_ERROR:
            all_workers_ok = False
        dropped_recs = int(w.get("mspti_records_dropped") or 0)
        if dropped_recs > 0:
            all_workers_ok = False
            controller_notes.append(f"mspti_records_dropped:slot_{w['slot_index']}:{dropped_recs}")
        if int(w["captured_steps"]) < int(target_capture_steps):
            all_workers_ok = False
            controller_notes.append(
                f"incomplete_capture_window:slot_{w['slot_index']}:"
                f"{w['captured_steps']}/{target_capture_steps}"
            )

        if gear_code == GEAR_FAST_MSPTI and art_str and Path(art_str).is_file():
            try:
                raw_json = json.loads(Path(art_str).read_text(encoding="utf-8"))
                fast_sum = _aggregate_gear1_worker_payload(raw_json, top_n=top_n)
                w_entry["fast_summary"] = fast_sum
                if fast_sum.get("observed_event_span_ms") is None:
                    all_workers_ok = False
                    controller_notes.append(f"empty_mspti_capture_window:slot_{w['slot_index']}")
                if fast_sum.get("operator_table_overflow"):
                    all_workers_ok = False
                    controller_notes.append(f"mspti_operator_table_overflow:slot_{w['slot_index']}")
                if fast_sum.get("interval_overflow"):
                    all_workers_ok = False
                    controller_notes.append(f"mspti_interval_overflow:slot_{w['slot_index']}")
            except (OSError, ValueError) as exc:
                all_workers_ok = False
                controller_notes.append(f"worker_json_read_error:{exc}")
        elif gear_code == GEAR_DEEP_ACLPROF and art_str:
            gear2_dirs.append(Path(art_str))
        else:
            all_workers_ok = False
        worker_reports.append(w_entry)

    export_receipts: list[dict[str, object]] = []
    c7_summary: dict[str, object] | None = None
    if gear_code == GEAR_DEEP_ACLPROF and gear2_dirs and all_workers_ok:
        export_deadline = min(outer_deadline, time.monotonic() + effective_export_s)
        export_receipts, c7_summary, export_errors = _export_and_analyze_gear2(
            install, gear2_dirs, gen_out_dir=gen_out_dir,
            export_deadline=export_deadline, export_timeout_s=effective_export_s, top_n=top_n,
        )
        if export_errors:
            all_workers_ok = False
            controller_notes.extend(export_errors)

    if command is not None and not controller_terminated_after_capture and process_exit_code not in {0, None}:
        all_workers_ok = False
        controller_notes.append(f"target_command_nonzero_exit:{process_exit_code}")
    if not final_workers:
        controller_notes.append("no_npu_workers_registered_in_shm")

    has_fatal_note = any(n.startswith(_FATAL_NOTE_PREFIXES) for n in controller_notes)
    status = "completed" if (all_workers_ok and not has_fatal_note) else "failed"

    report: dict[str, object] = {
        "schema_version": CAPTURE_SCHEMA, "status": status,
        "mode": "attach" if is_attach else "launch",
        "gear": "fast" if gear_code == GEAR_FAST_MSPTI else "deep",
        "session_id": session_id, "generation": generation,
        "output_dir": str(out_dir), "generation_output_dir": str(gen_out_dir),
        "elapsed_ms": round((time.monotonic() - t_begin) * 1000.0, 2),
        "cann": install.as_dict(), "shim_so": str(shim_so),
        "gate_policy": {
            "control_mode": "coordinated" if use_coordinated else "autonomous",
            "min_warmup_steps": min_warmup_steps, "steady_window_steps": steady_window_steps,
            "target_capture_steps": target_capture_steps, "max_cv_pct": max_cv_pct,
            "replays_per_step": replays_per_step, "require_zero_alloc_steps": require_zero_alloc_steps,
        },
        "transient_contaminated": any_contaminated, "worker_count": len(worker_reports),
        "multi_worker_barrier_skew_ms": barrier_skew_ms, "process_exit_code": process_exit_code,
        "process_stderr_tail": process_stderr_tail or None,
        "notes": controller_notes, "workers": worker_reports,
    }
    if gear_code == GEAR_DEEP_ACLPROF:
        report["gear2_exports"] = export_receipts
        report["c7_summary"] = c7_summary

    if output is not None:
        write_report(report, str(output))
    return report
