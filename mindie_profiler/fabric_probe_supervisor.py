"""Standalone HCCL probe script emission and multi-rank process supervision.

[Role]
  Emit syntax-validated standalone ``torch.distributed`` probe scripts from
  validated ``mindie-fabric-probe-plan/3`` plans and supervise multi-rank probe
  child processes with bounded abort propagation and emergency child reaping.

[Invariants]
  * One failed peer or non-empty abort file terminates every remaining rank
    process within ``cleanup_slice``.
  * ``TimeoutError`` is never swallowed; ``finally`` reaps surviving children
    on both POSIX and Windows.

[Timeouts & Locks]
  Bounded monotonic ``wall_budget_s`` plus Bounded emergency reap window; no
  host locks.

[Side-Effect Policy]
  Writes only ``output_path`` when requested; terminates/reaps only ``procs``.
"""

from __future__ import annotations

import contextlib
import inspect
import json
import math
import os
from pathlib import Path
import pprint
import signal
import time
from typing import Any, Callable

from . import repro_atomic_io as atomic_io
from .events import ProfilerUsageError
from .fabric_probe_samples import SPLIT_HELPERS
from .fabric_probe_script_template import PROBE_TEMPLATE
from .repro_atomic_io import path_exists
from .repro_values import bounded_count, bounded_sequence

_PRESETS_PATH = Path(__file__).parent / "knowledge" / "fabric_probe_presets.json"
_DEFAULTS = json.loads(_PRESETS_PATH.read_text(encoding="utf-8"))["defaults"]

_DEFAULT_DURATION_S = float(_DEFAULTS["default_duration_s"])
_MAX_WORLD = int(_DEFAULTS["max_world_size"])
_ROUND_S = int(_DEFAULTS["round_s_digits"])
_PPRINT_W = int(_DEFAULTS["pprint_width"])
_NT_EMERG_S = float(_DEFAULTS["nt_emergency_s"])
_POSIX_EMERG_S = float(_DEFAULTS["posix_emergency_s"])
_NT_WAIT_MS = int(_DEFAULTS["nt_wait_ms"])
_REAP_SLEEP_S = float(_DEFAULTS["reap_sleep_s"])
_MIN_BUDGET_S = float(_DEFAULTS["min_budget_s"])
_DEFAULT_POLL_S = float(_DEFAULTS["default_poll_s"])
_MAX_POLL_S = float(_DEFAULTS["max_poll_s"])
_CLEAN_SLICE_MAX_S = float(_DEFAULTS["cleanup_slice_max_s"])
_CLEAN_SLICE_FRAC = float(_DEFAULTS["cleanup_slice_fraction"])
_HARD_GRACE_S = float(_DEFAULTS["hard_end_grace_s"])
_SETTLE_GRACE_S = float(_DEFAULTS["settle_grace_s"])
_SETTLE_POLL_S = float(_DEFAULTS["settle_poll_s"])
_WAIT_MAX_S = float(_DEFAULTS["wait_max_s"])
_EXIT_ERR = int(_DEFAULTS["exit_error"])


def _finite_s(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ProfilerUsageError("seconds budget must be a finite number")
    return float(value)


def render_fabric_probe_script(
    plan: dict[str, Any],
    *,
    validator: Callable[[dict[str, Any]], dict[str, Any]],
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    validated = validator(plan)
    script = PROBE_TEMPLATE.replace(
        "__PLAN__", pprint.pformat(validated, sort_dicts=True, width=_PPRINT_W)
    )
    script = script.replace(
        "__IO_HELPERS__",
        "\n".join(
            inspect.getsource(getattr(atomic_io, name))
            for name in (
                "_cleanup_scope",
                "_retry_cleanup",
                "_recover_fd_inode",
                "_close_owned_fd",
                "_stream_raw",
                "_borrow_stream_fd",
                "_close_stream",
            )
        ),
    )
    script = script.replace("__SPLIT_HELPERS__", SPLIT_HELPERS)
    script = script.replace("__COUNT_HELPER__", inspect.getsource(bounded_count))
    try:
        compile(script, "<fabric_probe>", "exec")
    except SyntaxError as exc:
        raise ProfilerUsageError(
            f"fabric probe script failed syntax validation: {exc}"
        ) from exc
    if output_path is not None:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(script, encoding="utf-8", newline="\n")
    return {
        "schema": "mindie-fabric-probe-script/2",
        "status": "ok",
        "syntax_ok": True,
        "line_count": len(script.splitlines()),
        "output_path": None if output_path is None else str(Path(output_path)),
        "script": script,
    }


def _read_abort_record(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except TimeoutError:
        raise
    except (OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _process_reaped(proc: Any) -> bool:
    if proc.returncode is None:
        return False
    handle = getattr(proc, "_handle", None) if os.name == "nt" else None
    if isinstance(handle, int) and not isinstance(handle, bool):
        import _winapi

        return _winapi.WaitForSingleObject(int(handle), 0) == 0
    return True


def _emergency_reap_children(children: Any, hard_end: float) -> None:
    with contextlib.suppress(BaseException):
        emerg = _NT_EMERG_S if os.name == "nt" else _POSIX_EMERG_S
        end = max(hard_end, time.monotonic() + emerg)
        pending = list(children)
        while pending and time.monotonic() < end:
            survivors = []
            for proc in pending:
                with contextlib.suppress(BaseException):
                    proc.poll()
                if _process_reaped(proc):
                    continue
                if proc.returncode is None:
                    with contextlib.suppress(BaseException):
                        proc.kill()
                        proc.wait(timeout=0)
                    with contextlib.suppress(BaseException):
                        if proc.returncode is None and os.name == "nt":
                            import _winapi

                            _winapi.TerminateProcess(int(proc._handle), 1)
                        elif proc.returncode is None:
                            pid = getattr(proc, "pid", None)
                            if isinstance(pid, int) and pid > 0:
                                os.kill(pid, signal.SIGKILL)
                handle = getattr(proc, "_handle", None) if os.name == "nt" else None
                if isinstance(handle, int) and not isinstance(handle, bool):
                    import _winapi

                    if (
                        _winapi.WaitForSingleObject(int(handle), _NT_WAIT_MS) == 0
                        and proc.returncode is None
                    ):
                        proc.returncode = _winapi.GetExitCodeProcess(int(handle))
                if not _process_reaped(proc):
                    survivors.append(proc)
            pending = survivors
            if pending:
                time.sleep(max(0.0, min(_REAP_SLEEP_S, end - time.monotonic())))


def supervise_probe_processes(
    procs: Any,
    abort_file: str | Path | None = None,
    wall_budget_s: float = _DEFAULT_DURATION_S,
    poll_interval_s: float = _DEFAULT_POLL_S,
) -> dict[str, Any]:
    """One failed peer stops every remaining rank process."""
    processes = list(
        bounded_sequence(() if procs is None else procs, "processes", _MAX_WORLD)
    )
    if not processes:
        raise ProfilerUsageError("supervisor requires at least one process")
    budget = max(_MIN_BUDGET_S, _finite_s(wall_budget_s))
    poll = max(_MIN_BUDGET_S, min(_finite_s(poll_interval_s), _MAX_POLL_S))
    started = time.monotonic()
    deadline = started + budget
    cleanup_slice = min(_CLEAN_SLICE_MAX_S, _CLEAN_SLICE_FRAC * budget)
    terminate_at = max(started, deadline - cleanup_slice)
    kill_at = max(terminate_at, deadline - 0.5 * cleanup_slice)
    hard_end = deadline + _HARD_GRACE_S
    status = "completed"
    codes: dict[int, int] = {}
    terminated: list[int] = []
    reaped = False

    def poll_once() -> None:
        nonlocal status
        for idx, proc in enumerate(processes):
            code = proc.poll()
            if code is not None:
                codes.setdefault(idx, int(code))
                if code != 0 and status == "completed":
                    status = "peer_aborted"
        if status == "completed" and abort_file and path_exists(str(abort_file)):
            status = "peer_aborted"

    def sleep_bounded(seconds: float, end: float) -> None:
        remaining = min(float(seconds), end - time.monotonic())
        if remaining > 0:
            time.sleep(remaining)

    try:
        while True:
            poll_once()
            if status != "completed" or all(proc.poll() is not None for proc in processes):
                break
            if time.monotonic() >= terminate_at:
                break
            sleep_bounded(poll, terminate_at)
        poll_once()
        if status == "completed" and not all(proc.poll() is not None for proc in processes):
            status = "deadline_exceeded"
        if status == "peer_aborted":
            settle_end = min(kill_at, time.monotonic() + _SETTLE_GRACE_S)
            while time.monotonic() < settle_end:
                poll_once()
                if all(proc.poll() is not None for proc in processes):
                    break
                sleep_bounded(min(_SETTLE_POLL_S, poll), settle_end)
        for idx, proc in enumerate(processes):
            if proc.poll() is None:
                terminated.append(idx)
                try:
                    proc.terminate()
                except TimeoutError:
                    raise
                except OSError:
                    pass
        grace_end = min(kill_at, time.monotonic() + _SETTLE_GRACE_S)
        while time.monotonic() < grace_end:
            poll_once()
            if all(proc.poll() is not None for proc in processes):
                break
            sleep_bounded(min(_SETTLE_POLL_S, poll), grace_end)
        for proc in processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                except TimeoutError:
                    raise
                except OSError:
                    pass
        for proc in processes:
            while proc.poll() is None and time.monotonic() < hard_end:
                try:
                    proc.wait(
                        timeout=max(_MIN_BUDGET_S, min(_WAIT_MAX_S, hard_end - time.monotonic()))
                    )
                except TimeoutError:
                    raise
                except Exception:
                    pass
        reaped = all(proc.poll() is not None and _process_reaped(proc) for proc in processes)
        poll_once()
        for idx, proc in enumerate(processes):
            if idx not in codes and proc.returncode is not None:
                codes[idx] = int(proc.returncode)
        payload: dict[str, Any] = {
            "status": status,
            "exit_code": 0 if status == "completed" else _EXIT_ERR,
            "exit_codes": dict(sorted(codes.items())),
            "terminated_ranks": terminated,
            "elapsed_s": round(time.monotonic() - started, _ROUND_S),
        }
        record = _read_abort_record(abort_file)
        if record is not None:
            payload["abort_record"] = record
        return payload
    finally:
        if not reaped:
            _emergency_reap_children(processes, hard_end)


__all__ = ["render_fabric_probe_script", "supervise_probe_processes"]
