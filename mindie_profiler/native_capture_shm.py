"""Shared-memory control plane, pipe drainer, and step marker for CANN 9.x capture.

[Role]
  Mirror the C ``MindieCaptureShm`` binary layout via ``ctypes``, manage
  ``/dev/shm`` (or fallback tmpfs) lifecycle for launch and attach sessions,
  drain child ``stdout``/``stderr`` pipes in bounded $O(1)$ memory, audit L3
  steady-state window invariants, and expose ``mark_capture_step()``.

[Invariants]
  * ``sizeof(MindieCaptureHeader) == 1024``, ``sizeof(MindieWorkerSlot) == 1024``,
    and ``sizeof(MindieCaptureShm) == 33792`` on every 64-bit host.
  * ``mark_capture_step()`` never imports ``torch_npu`` or opens NPU contexts;
    when no preload shim is active in the process, it is a cached no-op.

[Timeouts & Locks]
  Memory-mapped reads/writes are non-blocking; session teardown closes ``mmap``
  before unlinking backing files.

[Side-Effect Policy]
  Creates or opens only the explicit ``mindie_cap_<session_id>.shm`` file.
"""

from __future__ import annotations

from collections.abc import Mapping
import ctypes
import gc
import math
import mmap
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from typing import BinaryIO, Callable

from .events import ProfilerError, ProfilerUsageError

MINDIE_CAPTURE_MAGIC = 0x4D494E4449454339
MINDIE_CAPTURE_ABI_VERSION = 3
MINDIE_MAX_WORKERS = 32
MINDIE_MAX_WINDOW_STEPS = 64

GEAR_FAST_MSPTI = 1
GEAR_DEEP_ACLPROF = 2

MODE_AUTONOMOUS = 0
MODE_COORDINATED = 1

PHASE_STANDBY = 0
PHASE_ARMED = 1
PHASE_START_NOW = 2
PHASE_STOP_NOW = 3
PHASE_SHUTDOWN = 4

WORKER_IDLE = 0
WORKER_WARMUP = 1
WORKER_GATE_READY = 2
WORKER_CAPTURING = 3
WORKER_DONE = 4
WORKER_ERROR = 5

WORKER_STATE_NAMES = {
    WORKER_IDLE: "idle",
    WORKER_WARMUP: "warmup",
    WORKER_GATE_READY: "gate_ready",
    WORKER_CAPTURING: "capturing",
    WORKER_DONE: "done",
    WORKER_ERROR: "error",
}

# Verified against CANN 9.2.1 <acl/acl_prof.h>
ACL_PROF_ACL_API = 0x0001
ACL_PROF_TASK_TIME = 0x0002
ACL_PROF_AICORE_METRICS = 0x0004
ACL_PROF_AICPU = 0x0008
ACL_PROF_L2CACHE = 0x0010
ACL_PROF_HCCL_TRACE = 0x0020
ACL_PROF_MSPROFTX = 0x0080
ACL_PROF_RUNTIME_API = 0x0100
ACL_PROF_TASK_MEMORY = 0x1000
ACL_PROF_OP_ATTR = 0x4000
ACL_PROF_AICORE_SHAPE = 0x800000000

DEFAULT_GEAR2_PROF_MASK = (
    ACL_PROF_ACL_API
    | ACL_PROF_TASK_TIME
    | ACL_PROF_AICORE_METRICS
    | ACL_PROF_AICPU
    | ACL_PROF_HCCL_TRACE
    | ACL_PROF_MSPROFTX
    | ACL_PROF_RUNTIME_API
    | ACL_PROF_OP_ATTR
    | ACL_PROF_AICORE_SHAPE
)

AICORE_METRICS_MAP = {
    "arithmetic_utilization": 0,
    "pipe_utilization": 1,
    "memory_bandwidth": 2,
    "l0b_and_width": 3,
    "resource_conflict_ratio": 4,
    "memory_ub": 5,
    "l2_cache": 6,
    "pipe_execute_utilization": 7,
    "memory_access": 8,
}

_SAFE_SESSION_RE = re.compile(r"^[A-Za-z0-9._-]{1,56}$")


class MindieCaptureHeader(ctypes.Structure):
    _fields_ = [
        ("magic", ctypes.c_uint64),
        ("abi_version", ctypes.c_uint32),
        ("gear", ctypes.c_uint32),
        ("control_mode", ctypes.c_uint32),
        ("desired_phase", ctypes.c_uint32),
        ("generation", ctypes.c_uint64),
        ("min_warmup_steps", ctypes.c_uint32),
        ("steady_window_steps", ctypes.c_uint32),
        ("target_capture_steps", ctypes.c_uint32),
        ("max_cv_ppm", ctypes.c_uint32),
        ("replays_per_step", ctypes.c_uint32),
        ("require_zero_alloc_steps", ctypes.c_uint32),
        ("min_step_interval_ns", ctypes.c_uint64),
        ("aclprof_data_type_mask", ctypes.c_uint64),
        ("aclprof_aicore_metrics", ctypes.c_uint32),
        ("active_worker_slots", ctypes.c_uint32),
        ("controller_arm_mono_ns", ctypes.c_uint64),
        ("controller_start_mono_ns", ctypes.c_uint64),
        ("controller_stop_mono_ns", ctypes.c_uint64),
        ("session_id", ctypes.c_char * 64),
        ("output_dir", ctypes.c_char * 512),
        ("libmsprofiler_path", ctypes.c_char * 256),
        ("slot_overflow_count", ctypes.c_uint32),
        ("reserved", ctypes.c_uint8 * 84),
    ]


class MindieWorkerSlot(ctypes.Structure):
    _fields_ = [
        ("claimed", ctypes.c_uint32),
        ("pid", ctypes.c_int32),
        ("logical_device_id", ctypes.c_int32),
        ("physical_device_id", ctypes.c_int32),
        ("worker_state", ctypes.c_uint32),
        ("active_graph_captures", ctypes.c_uint32),
        ("acked_generation", ctypes.c_uint64),
        ("total_steps", ctypes.c_uint64),
        ("graph_replays_total", ctypes.c_uint64),
        ("graph_captures_total", ctypes.c_uint64),
        ("alloc_calls_total", ctypes.c_uint64),
        ("last_alloc_step", ctypes.c_uint64),
        ("last_step_ns", ctypes.c_uint64),
        ("last_step_duration_ns", ctypes.c_uint64),
        ("window_mean_ns", ctypes.c_uint64),
        ("window_cv_ppm", ctypes.c_uint64),
        ("capture_start_mono_ns", ctypes.c_uint64),
        ("capture_end_mono_ns", ctypes.c_uint64),
        ("capture_start_step", ctypes.c_uint64),
        ("captured_steps", ctypes.c_uint64),
        ("graph_captures_in_window", ctypes.c_uint64),
        ("allocs_in_window", ctypes.c_uint64),
        ("window_capture_min_step_ns", ctypes.c_uint64),
        ("window_capture_max_step_ns", ctypes.c_uint64),
        ("window_capture_sum_step_ns", ctypes.c_uint64),
        ("window_capture_sum_sq_us", ctypes.c_uint64),
        ("mspti_records_captured", ctypes.c_uint64),
        ("mspti_records_dropped", ctypes.c_uint64),
        ("last_error_code", ctypes.c_int32),
        ("summary_written", ctypes.c_uint32),
        ("error_msg", ctypes.c_char * 128),
        ("artifact_path", ctypes.c_char * 688),
    ]


class MindieCaptureShm(ctypes.Structure):
    _fields_ = [
        ("header", MindieCaptureHeader),
        ("slots", MindieWorkerSlot * MINDIE_MAX_WORKERS),
    ]


if ctypes.sizeof(MindieCaptureHeader) != 1024:
    raise AssertionError(f"MindieCaptureHeader size mismatch: {ctypes.sizeof(MindieCaptureHeader)}")
if ctypes.sizeof(MindieWorkerSlot) != 1024:
    raise AssertionError(f"MindieWorkerSlot size mismatch: {ctypes.sizeof(MindieWorkerSlot)}")
if ctypes.sizeof(MindieCaptureShm) != 33792:
    raise AssertionError(f"MindieCaptureShm size mismatch: {ctypes.sizeof(MindieCaptureShm)}")


class PipeTailDrainer:
    """Drain child ``stdout``/``stderr`` continuously while retaining only a bounded tail."""

    def __init__(
        self,
        stdout_pipe: BinaryIO | None,
        stderr_pipe: BinaryIO | None,
        *,
        max_bytes: int = 8192,
    ) -> None:
        self._max_bytes = max(512, int(max_bytes))
        self._stdout_buf = bytearray()
        self._stderr_buf = bytearray()
        self._threads: list[threading.Thread] = []
        for pipe, target_buf in (
            (stdout_pipe, self._stdout_buf),
            (stderr_pipe, self._stderr_buf),
        ):
            if pipe is not None:
                th = threading.Thread(
                    target=self._drain_loop,
                    args=(pipe, target_buf),
                    daemon=True,
                )
                th.start()
                self._threads.append(th)

    def _drain_loop(self, pipe: BinaryIO, buf: bytearray) -> None:
        cap = self._max_bytes
        try:
            while True:
                chunk = pipe.read(4096)
                if not chunk:
                    break
                if len(chunk) >= cap:
                    buf[:] = chunk[-cap:]
                else:
                    buf.extend(chunk)
                    if len(buf) > cap * 2:
                        del buf[:-cap]
        except TimeoutError:
            raise
        except OSError:
            pass
        finally:
            try:
                pipe.close()
            except TimeoutError:
                raise
            except OSError:
                pass

    def finish(self, *, timeout_s: float = 1.0) -> tuple[str, str]:
        deadline = time.monotonic() + max(0.05, float(timeout_s))
        for th in self._threads:
            rem = max(0.01, deadline - time.monotonic())
            th.join(timeout=rem)
        cap = self._max_bytes
        out_str = bytes(self._stdout_buf[-cap:]).decode("utf-8", errors="replace")
        err_str = bytes(self._stderr_buf[-cap:]).decode("utf-8", errors="replace")
        return out_str, err_str


def audit_worker_steady_state(
    worker: Mapping[str, object],
    *,
    target_capture_steps: int,
    max_cv_ppm: int,
    require_zero_alloc_steps: bool,
) -> dict[str, object]:
    """Level-3 post-capture steady-state contamination audit."""

    reasons: list[str] = []
    captured_steps = int(worker.get("captured_steps") or 0)
    graph_in_win = int(worker.get("graph_captures_in_window") or 0)
    allocs_in_win = int(worker.get("allocs_in_window") or 0)
    dropped = int(worker.get("mspti_records_dropped") or 0)

    if captured_steps < target_capture_steps:
        reasons.append(f"incomplete_capture_steps:{captured_steps}<{target_capture_steps}")
    if graph_in_win > 0:
        reasons.append(f"graph_capture_during_window:{graph_in_win}")
    if require_zero_alloc_steps and allocs_in_win > 0:
        reasons.append(f"hbm_malloc_churn_during_window:{allocs_in_win}")
    if dropped > 0:
        reasons.append(f"mspti_records_dropped:{dropped}")

    captured_cv_ppm: int | None = None
    sum_ns = int(worker.get("window_capture_sum_step_ns") or 0)
    sum_sq_us = int(worker.get("window_capture_sum_sq_us") or 0)
    if captured_steps >= 2 and sum_ns > 0:
        mean_us = (sum_ns / 1000.0) / captured_steps
        if mean_us > 0:
            mean_sq = sum_sq_us / float(captured_steps)
            variance = max(0.0, mean_sq - (mean_us * mean_us))
            captured_cv_ppm = int(round((math.sqrt(variance) / mean_us) * 1_000_000.0))
            if max_cv_ppm > 0 and captured_cv_ppm > int(max_cv_ppm * 1.5):
                reasons.append(
                    f"captured_step_cv_spike:{captured_cv_ppm}>{int(max_cv_ppm * 1.5)}"
                )

    contaminated = any(
        r.startswith(
            (
                "graph_capture_during_window:",
                "hbm_malloc_churn_during_window:",
                "captured_step_cv_spike:",
            )
        )
        for r in reasons
    )
    return {
        "transient_contaminated": contaminated,
        "complete_window": captured_steps >= target_capture_steps,
        "captured_step_mean_ms": (
            round((sum_ns / 1_000_000.0) / captured_steps, 6)
            if captured_steps > 0 and sum_ns > 0
            else None
        ),
        "captured_step_cv_ppm": captured_cv_ppm,
        "audit_flags": reasons,
    }


def validate_session_id(session_id: str) -> str:
    if not _SAFE_SESSION_RE.match(session_id or ""):
        raise ProfilerUsageError(
            f"invalid capture session_id {session_id!r}; use 1..56 [A-Za-z0-9._-] chars"
        )
    return session_id


def default_shm_dir() -> Path:
    override = (os.environ.get("MINDIE_CAPTURE_SHM_DIR") or "").strip()
    if override:
        path = Path(override).expanduser().resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path
    dev_shm = Path("/dev/shm")
    if dev_shm.is_dir() and os.access(dev_shm, os.W_OK):
        return dev_shm.resolve()
    data_home = (os.environ.get("MINDIE_DATA_HOME") or "").strip()
    if data_home:
        fallback = Path(data_home).expanduser() / "profiler" / "shm"
    else:
        fallback = Path(tempfile.gettempdir()) / "mindie_profiler_shm"
    fallback = fallback.resolve()
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def resolve_shm_backing_path(
    session_id: str,
    *,
    shm_dir: str | os.PathLike[str] | None = None,
) -> Path:
    clean_id = validate_session_id(session_id)
    base = (Path(shm_dir).expanduser() if shm_dir is not None else default_shm_dir()).resolve()
    base.mkdir(parents=True, exist_ok=True)
    return (base / f"mindie_cap_{clean_id}.shm").resolve()


def _encode_c_field(value: str, max_bytes: int, field_name: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) >= max_bytes:
        raise ProfilerUsageError(
            f"{field_name} exceeds {max_bytes - 1} UTF-8 bytes: {value!r}"
        )
    return raw


_CONTROLLER_GUARD = threading.Lock()
_ACTIVE_CONTROLLERS: set[str] = set()


class CaptureShmSession:
    """Memory-mapped controller handle over ``MindieCaptureShm``."""

    def __init__(
        self,
        path: Path,
        *,
        create: bool,
        unlink_on_close: bool,
        exclusive_controller: bool = False,
    ) -> None:
        self.path = path
        self.unlink_on_close = unlink_on_close
        self._fd: int | None = None
        self._mmap: mmap.mmap | None = None
        self._view: MindieCaptureShm | None = None
        self._ctl_lock_key: str | None = None
        self._ctl_lock_path: Path | None = None
        self._ctl_lock_fd: int | None = None
        shm_size = ctypes.sizeof(MindieCaptureShm)

        if exclusive_controller:
            self._acquire_controller_lock(path)

        flags = (
            os.O_RDWR
            | (os.O_CREAT | os.O_EXCL if create else 0)
            | getattr(os, "O_BINARY", 0)
        )
        try:
            fd = os.open(str(path), flags, 0o600)
            if create:
                os.ftruncate(fd, shm_size)
            else:
                st = os.fstat(fd)
                if st.st_size < shm_size:
                    os.close(fd)
                    raise ProfilerUsageError(
                        f"capture shm {path} is truncated ({st.st_size} < {shm_size})"
                    )
            mm = mmap.mmap(fd, shm_size, access=mmap.ACCESS_WRITE)
        except TimeoutError:
            self._release_controller_lock(unlink=False)
            raise
        except ProfilerUsageError:
            self._release_controller_lock(unlink=False)
            raise
        except FileExistsError as exc:
            self._release_controller_lock(unlink=False)
            raise ProfilerUsageError(
                f"capture session already exists at {path}; attach with --attach or choose a distinct session_id"
            ) from exc
        except OSError as exc:
            self._release_controller_lock(unlink=False)
            raise ProfilerError(f"cannot open capture shm {path}: {exc}") from exc

        self._fd = fd
        self._mmap = mm
        self._view = MindieCaptureShm.from_buffer(mm)
        if create:
            self._view.header.magic = MINDIE_CAPTURE_MAGIC
            self._view.header.abi_version = MINDIE_CAPTURE_ABI_VERSION
        elif (
            self._view.header.magic != MINDIE_CAPTURE_MAGIC
            or self._view.header.abi_version != MINDIE_CAPTURE_ABI_VERSION
        ):
            self.close(unlink=False)
            raise ProfilerError(f"capture shm {path} has incompatible magic/ABI")

    def _acquire_controller_lock(self, path: Path) -> None:
        key = str(path.resolve())
        lock_path = path.with_name(f".{path.name}.ctl.lock")
        with _CONTROLLER_GUARD:
            if key in _ACTIVE_CONTROLLERS:
                raise ProfilerUsageError(
                    f"capture session {path.name} already has an active controller"
                )
            _ACTIVE_CONTROLLERS.add(key)
        self._ctl_lock_key = key
        self._ctl_lock_path = lock_path
        try:
            lfd = os.open(
                str(lock_path),
                os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0),
                0o600,
            )
            try:
                if os.name == "nt":
                    import msvcrt

                    if os.lseek(lfd, 0, os.SEEK_END) == 0:
                        os.write(lfd, b"\0")
                    os.lseek(lfd, 0, os.SEEK_SET)
                    msvcrt.locking(lfd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except TimeoutError:
                os.close(lfd)
                raise
            except OSError as exc:
                os.close(lfd)
                raise ProfilerUsageError(
                    f"capture session {path.name} already has an active controller"
                ) from exc
            self._ctl_lock_fd = lfd
        except BaseException:
            with _CONTROLLER_GUARD:
                _ACTIVE_CONTROLLERS.discard(key)
            self._ctl_lock_key = None
            raise

    def _release_controller_lock(self, *, unlink: bool) -> None:
        if self._ctl_lock_fd is not None:
            lfd = self._ctl_lock_fd
            self._ctl_lock_fd = None
            try:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(lfd, 0, os.SEEK_SET)
                    msvcrt.locking(lfd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(lfd, fcntl.LOCK_UN)
            except TimeoutError:
                raise
            except OSError:
                pass
            try:
                os.close(lfd)
            except TimeoutError:
                raise
            except OSError:
                pass
        if unlink and self._ctl_lock_path is not None:
            try:
                self._ctl_lock_path.unlink(missing_ok=True)
            except TimeoutError:
                raise
            except OSError:
                pass
        if self._ctl_lock_key is not None:
            with _CONTROLLER_GUARD:
                _ACTIVE_CONTROLLERS.discard(self._ctl_lock_key)
            self._ctl_lock_key = None

    @property
    def view(self) -> MindieCaptureShm:
        if self._view is None:
            raise ProfilerError("capture shm session is already closed")
        return self._view

    def configure_run(
        self,
        *,
        session_id: str,
        output_dir: Path,
        gear: int,
        control_mode: int,
        desired_phase: int,
        min_warmup_steps: int,
        steady_window_steps: int,
        target_capture_steps: int,
        max_cv_ppm: int,
        replays_per_step: int = 1,
        require_zero_alloc_steps: bool = True,
        min_step_interval_ns: int = 50_000,
        aclprof_data_type_mask: int = DEFAULT_GEAR2_PROF_MASK,
        aclprof_aicore_metrics: int = 1,
        libmsprofiler_path: str = "",
        bump_generation: bool = True,
    ) -> int:
        if steady_window_steps < 1 or steady_window_steps > MINDIE_MAX_WINDOW_STEPS:
            raise ProfilerUsageError(
                f"steady_window_steps must be in 1..{MINDIE_MAX_WINDOW_STEPS}, got {steady_window_steps}"
            )
        if target_capture_steps < 1:
            raise ProfilerUsageError(
                f"target_capture_steps must be >= 1, got {target_capture_steps}"
            )
        hdr = self.view.header
        hdr.gear = int(gear)
        hdr.control_mode = int(control_mode)
        hdr.min_warmup_steps = max(0, int(min_warmup_steps))
        hdr.steady_window_steps = int(steady_window_steps)
        hdr.target_capture_steps = int(target_capture_steps)
        hdr.max_cv_ppm = max(0, int(max_cv_ppm))
        hdr.replays_per_step = max(1, int(replays_per_step))
        hdr.require_zero_alloc_steps = 1 if require_zero_alloc_steps else 0
        hdr.min_step_interval_ns = max(0, int(min_step_interval_ns))
        hdr.aclprof_data_type_mask = int(aclprof_data_type_mask)
        hdr.aclprof_aicore_metrics = int(aclprof_aicore_metrics)
        hdr.session_id = _encode_c_field(session_id, 64, "session_id")
        hdr.output_dir = _encode_c_field(str(output_dir.resolve()), 512, "output_dir")
        hdr.libmsprofiler_path = _encode_c_field(
            libmsprofiler_path, 256, "libmsprofiler_path"
        )
        now_ns = time.monotonic_ns()
        hdr.controller_arm_mono_ns = now_ns
        if bump_generation:
            hdr.slot_overflow_count = 0
            hdr.generation = int(hdr.generation) + 1
        hdr.desired_phase = int(desired_phase)
        return int(hdr.generation)

    @property
    def slot_overflow_count(self) -> int:
        return int(self.view.header.slot_overflow_count)

    def set_phase(self, phase: int) -> None:
        hdr = self.view.header
        now_ns = time.monotonic_ns()
        if phase == PHASE_START_NOW:
            hdr.controller_start_mono_ns = now_ns
        elif phase in {PHASE_STOP_NOW, PHASE_SHUTDOWN}:
            hdr.controller_stop_mono_ns = now_ns
        hdr.desired_phase = int(phase)

    def snapshot_workers(
        self, *, generation: int | None = None
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for slot_idx in range(MINDIE_MAX_WORKERS):
            slot = self.view.slots[slot_idx]
            if slot.claimed != 2:
                continue
            acked_gen = int(slot.acked_generation)
            if generation is not None and acked_gen != int(generation):
                continue
            state_code = int(slot.worker_state)
            min_step = (
                None
                if slot.captured_steps == 0
                or slot.window_capture_min_step_ns == (1 << 64) - 1
                else int(slot.window_capture_min_step_ns)
            )
            max_step = (
                None if slot.captured_steps == 0 else int(slot.window_capture_max_step_ns)
            )
            rows.append(
                {
                    "slot_index": slot_idx,
                    "pid": int(slot.pid),
                    "logical_device_id": int(slot.logical_device_id),
                    "physical_device_id": int(slot.physical_device_id),
                    "acked_generation": acked_gen,
                    "worker_state_code": state_code,
                    "worker_state": WORKER_STATE_NAMES.get(state_code, f"unknown_{state_code}"),
                    "active_graph_captures": int(slot.active_graph_captures),
                    "total_steps": int(slot.total_steps),
                    "graph_replays_total": int(slot.graph_replays_total),
                    "graph_captures_total": int(slot.graph_captures_total),
                    "alloc_calls_total": int(slot.alloc_calls_total),
                    "last_alloc_step": int(slot.last_alloc_step),
                    "last_step_duration_ns": int(slot.last_step_duration_ns),
                    "window_mean_ns": int(slot.window_mean_ns),
                    "window_cv_ppm": int(slot.window_cv_ppm),
                    "capture_start_mono_ns": int(slot.capture_start_mono_ns),
                    "capture_end_mono_ns": int(slot.capture_end_mono_ns),
                    "capture_start_step": int(slot.capture_start_step),
                    "captured_steps": int(slot.captured_steps),
                    "graph_captures_in_window": int(slot.graph_captures_in_window),
                    "allocs_in_window": int(slot.allocs_in_window),
                    "window_capture_min_step_ns": min_step,
                    "window_capture_max_step_ns": max_step,
                    "window_capture_sum_step_ns": int(slot.window_capture_sum_step_ns),
                    "window_capture_sum_sq_us": int(slot.window_capture_sum_sq_us),
                    "mspti_records_captured": int(slot.mspti_records_captured),
                    "mspti_records_dropped": int(slot.mspti_records_dropped),
                    "last_error_code": int(slot.last_error_code),
                    "summary_written": bool(slot.summary_written),
                    "error_msg": slot.error_msg.decode("utf-8", errors="replace"),
                    "artifact_path": slot.artifact_path.decode("utf-8", errors="replace"),
                }
            )
        return rows

    def close(self, *, unlink: bool | None = None) -> None:
        should_unlink = self.unlink_on_close if unlink is None else unlink
        self._view = None
        if self._mmap is not None:
            try:
                self._mmap.close()
            except BufferError:
                gc.collect()
                try:
                    self._mmap.close()
                except BufferError:
                    pass
            self._mmap = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except TimeoutError:
                raise
            except OSError:
                pass
            self._fd = None
        if should_unlink:
            try:
                self.path.unlink(missing_ok=True)
            except TimeoutError:
                raise
            except OSError:
                pass
        self._release_controller_lock(unlink=should_unlink)

    def __enter__(self) -> CaptureShmSession:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()


_STEP_FN_RESOLVED = False
_STEP_FN: Callable[[], None] | None = None


def mark_capture_step() -> bool:
    """Signal an explicit step boundary to an active preload shim, if loaded."""

    global _STEP_FN_RESOLVED, _STEP_FN
    if not _STEP_FN_RESOLVED:
        _STEP_FN_RESOLVED = True
        if os.environ.get("MINDIE_CAPTURE_SHM_PATH"):
            try:
                proc_lib = ctypes.CDLL(None)
                fn = getattr(proc_lib, "mindie_capture_mark_step", None)
                if fn is not None:
                    fn.argtypes = []
                    fn.restype = None
                    _STEP_FN = fn
            except TimeoutError:
                raise
            except OSError:
                _STEP_FN = None
    if _STEP_FN is None:
        return False
    _STEP_FN()
    return True
