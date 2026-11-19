"""Static standalone HCCL probe template with real tier groups and a deadline.

[Role]
  Hold the emitted ``torch.distributed`` sweep: ``LOCAL_RANK``-first bind with a
  fail-closed physical-die allowlist, one ``new_group`` per tier, matched
  pairwise send/recv, unequal AllToAllV splits, preallocated buffers,
  device-event timing behind a ``2.5 ms`` stream blocker and bounded cleanup.

[Invariants]
  * Only declared pair participants call send/recv.
  * AllToAllV splits are integers with ``recv_r[s] = send_s[r]``.
  * Buffered samples are disqualified when the final MIN gate, the destroy or
    the wall gate fails; no collective barrier runs in failure cleanup.
  * ``torch.npu.device_count()`` is never consulted before the bind.

[Timeouts & Locks]
  Finite process-group timeout and bounded monotonic deadline; cleanup is
  guarded by a daemon timer plus POSIX ``signal.alarm``.

[Side-Effect Policy]
  No I/O or hardware access at import time.
"""

from __future__ import annotations
PROBE_TEMPLATE = r'''#!/usr/bin/env python3
"""[Role] Standalone HCCL sweep. [Invariants] Validated groups and bounded counts. [Timeouts & Locks] Monotonic deadline and guarded cleanup. [Side-Effect Policy] Explicit output and abort paths only."""
from __future__ import annotations
import argparse
import contextlib
import datetime
import errno
import hashlib
import io
import json
import os
import signal
import stat
import sys
import threading
import time
PLAN = __PLAN__
ABORT_FILE = None
_RUN_ID = str(PLAN.get("run_id") or "fabric-probe")
_HELDOUT_SIZES = (1 << 15, 1 << 19, 1 << 23, 1 << 27)
_PEER_ABORTED = threading.Event()
_ABORT_STATE = {"lock": threading.Lock(), "groups": [], "stop": None, "thread": None}
_GROUP_KWARG_SUPPORT = {}
__SPLIT_HELPERS__
__IO_HELPERS__
class ProfilerUsageError(ValueError):
    """Invalid standalone resource request."""
__COUNT_HELPER__
def _abort_file_present(path):
    if not path: return False
    try:
        os.lstat(path)
    except TimeoutError: raise
    except OSError:
        return False
    return True
def _abort_signaled(_dist=None):
    if _PEER_ABORTED.is_set(): return True
    return _abort_file_present(ABORT_FILE)
def _cleanup_call(fn, active_exc=None):
    """Secondary cleanup must not replace an explicitly active primary."""
    if active_exc is not None:
        with contextlib.suppress(Exception):
            return fn()
        return None
    return fn()
def _remove_abort_temporary(path, expected):
    if expected is None: return
    first, parked = None, None
    def owned(info):
        return stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == expected
    for _ in range(4):
        completed = False
        with contextlib.suppress(OSError):
            try:
                try:
                    if parked is None:
                        parked = path + "." + os.urandom(16).hex() + ".rollback"
                    try:
                        info = os.lstat(parked)
                    except FileNotFoundError:
                        if not owned(os.lstat(path)): return
                        os.rename(path, parked); info = os.lstat(parked)
                    if not owned(info):
                        try:
                            os.link(parked, path) if os.name == "nt" else os.link(parked, path, follow_symlinks=False)
                        except FileExistsError:
                            current = os.lstat(path)
                            if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino): return
                    os.unlink(parked)
                except FileNotFoundError: completed = True
            finally: first = first if completed or first is not None else sys.exc_info()[1]
        if completed: break
    if first is not None: raise first
def _write_abort_record(record, primary_exc=None):
    if not ABORT_FILE: return
    def write():
        temporary = ABORT_FILE + f".{os.getpid()}.{os.urandom(16).hex()}.tmp"
        inode = publish = None
        committed_write, temp_owned = False, True
        try:
            try:
                fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0), 0o600)
                handle = None
                try:
                    handle = open(fd, "w", closefd=False, encoding="utf-8", newline="\n", opener=os.open)
                    _stream_raw(handle).name = temporary
                    info = os.fstat(fd)
                    inode = (info.st_dev, info.st_ino)
                    if not stat.S_ISREG(info.st_mode):
                        raise OSError("abort temporary is not regular")
                    fd = _borrow_stream_fd(handle, fd, inode)
                    payload = json.dumps(record, sort_keys=True) + "\n"
                    if handle.write(payload) != len(payload):
                        raise OSError("short abort write")
                    handle.flush(); os.fsync(fd)
                finally:
                    active = sys.exc_info()[1]
                    if inode is None: inode = _recover_fd_inode(fd)  # Recover before close, never from a pathname.
                    clean_close = _cleanup_call(lambda: _close_stream(handle, fd, inode, active) if handle is not None else _close_owned_fd(fd, expected=inode, active_exc=active), active)
                committed_write = bool(clean_close and handle.closed)
                if not committed_write:
                    return
                publish = ABORT_FILE + f".{os.getpid()}.{os.urandom(16).hex()}.publish"
                os.rename(temporary, publish); temp_owned = False
                info = os.lstat(publish)
                if not stat.S_ISREG(info.st_mode) or (info.st_dev, info.st_ino) != inode:
                    foreign_publish, publish = publish, None
                    try:
                        os.link(foreign_publish, temporary) if os.name == "nt" else os.link(foreign_publish, temporary, follow_symlinks=False)
                    except FileExistsError:
                        return  # Both foreign occupants remain; no destination overwrite.
                    os.unlink(foreign_publish); return
                os.replace(publish, ABORT_FILE)
            finally:
                active = sys.exc_info()[1]
                try:
                    if publish is not None: _cleanup_call(lambda: _remove_abort_temporary(publish, inode), active)
                finally:
                    if temp_owned: _cleanup_call(lambda: _remove_abort_temporary(temporary, inode), active or sys.exc_info()[1])
        except TimeoutError: raise
        except Exception: _cleanup_call(write, primary_exc if primary_exc is not None else sys.exc_info()[1])
def _disqualify(records, status, reason):
    for record in records:
        record["validated"] = False; record["disqualified_reason"] = reason
        record["status"] = status
    return records
def _signal_abort(_dist, rank, step, error):
    _write_abort_record({"kind": "abort", "rank": int(rank), "step": str(step), "error": str(error)[:800]})
def _signal_deadline(rank, step):
    _write_abort_record({"kind": "status", "status": "deadline_exceeded", "reason": "deadline_exceeded", "rank": int(rank), "step": str(step)})
    _PEER_ABORTED.set()
def _register_group(group):
    with _ABORT_STATE["lock"]:
        if group is not None: _ABORT_STATE["groups"].append(group)
        if not ABORT_FILE or _ABORT_STATE["thread"] is not None:
            return
        stop = threading.Event()
        thread = _AbortWatcher(stop, ABORT_FILE)
        _ABORT_STATE.update({"stop": stop, "thread": thread})
        thread.start()
class _AbortWatcher(threading.Thread):
    """Wake a peer blocked in a collective when --abort-file appears."""
    def __init__(self, stop, abort_file):
        super().__init__(name="mindie-abort-watch", daemon=True)
        self._stop_event = stop
        self._abort_file = abort_file
    def run(self):
        aborted = set()
        while not self._stop_event.wait(0.005):
            if not _abort_file_present(self._abort_file): continue
            _PEER_ABORTED.set()
            with _ABORT_STATE["lock"]:
                groups = list(_ABORT_STATE["groups"])
            for group in groups:
                if group is None or id(group) in aborted:
                    continue
                aborted.add(id(group))
                for attribute in ("abort", "_abort", "_shutdown"):
                    method = getattr(group, attribute, None)
                    if not callable(method):
                        continue
                    try:
                        method()
                    except TimeoutError: raise
                    except Exception:
                                        break
            # A communicator registered after the first observed abort must be
            # aborted too; stop is owned by the finally block.
def _stop_abort_watcher():
    with _ABORT_STATE["lock"]:
        stop = _ABORT_STATE.get("stop")
        thread = _ABORT_STATE.get("thread")
    if stop is not None: stop.set()
    if thread is not None and thread is not threading.current_thread(): thread.join(0.2)
def _clock_mhz():
    try:
        import torch_npu
        return float(torch_npu.npu_get_clock_rate()) / 1e6
    except TimeoutError: raise
    except Exception:
        return None
def _check_physical_die(ordinal, allowed):
    """Post-bind visible->physical mapping; the allowlist is fail-closed."""
    if not allowed: return {"physical_id": None, "allowed": None}
    try:
        from vllm_ascend.platform import NPUPlatform
        physical = int(NPUPlatform.visible_device_id_to_physical_device_id(ordinal))
    except TimeoutError: raise
    except Exception:
        physical = None
    if physical is None or physical not in [int(item) for item in allowed]:
        raise ProfilerUsageError("physical die %r is not in the allowed physical ids" % (physical,))
    return {"physical_id": physical, "allowed": True}
def _new_timer(torch):
    """Preallocated event pair plus a private stream for the blocker."""
    timer = {"torch": torch, "mode": "host_fallback", "start": None, "end": None, "stream": None,
             "blocker_done": None, "blocker_stream": None, "unit": None, "unit_ms": None,
             "repeats": 0, "calibrated": False}
    npu = getattr(torch, "npu", None)
    factory = getattr(npu, "Event", None)
    if not callable(factory):
        return timer
    try:
        streams = getattr(npu, "Stream", None)
        timer.update({"mode": "device_event", "start": factory(enable_timing=True), "end": factory(enable_timing=True),
                      "stream": npu.current_stream(),
                      "blocker_done": factory(enable_timing=True),
                      "blocker_stream": (streams() if callable(streams)
                                         else npu.current_stream())})
    except TimeoutError: raise
    except Exception:
        return {"torch": torch, "mode": "host_fallback", "start": None, "end": None, "stream": None,
                "blocker_done": None, "blocker_stream": None, "unit": None, "unit_ms": None, "repeats": 0, "calibrated": False}
    return timer
def _stream_context(torch, stream):
    """Enter a private stream context when the backend exposes one."""
    factory = getattr(getattr(torch, "npu", None), "stream", None)
    if callable(factory) and stream is not None:
        try:
            return factory(stream)
        except TimeoutError: raise
        except Exception:
            return contextlib.nullcontext()
    return contextlib.nullcontext()
def _calibrate_blocker(torch, timer):
    """Size ~2.5 ms of queued work with a measured single-unit device time."""
    if timer["mode"] != "device_event": return timer
    buffer = torch.zeros(262144, dtype=torch.float32, device="npu")
    def unit(): torch.add(buffer, buffer, out=buffer)
    stream = timer["blocker_stream"]
    with _stream_context(torch, stream):
        timer["start"].record(stream); unit(); timer["end"].record(stream)
    timer["end"].synchronize()
    unit_ms = float(timer["start"].elapsed_time(timer["end"]))
    if unit_ms <= 0: return timer
    target = float(PLAN.get("timing", {}).get("blocker_target_ms") or 2.5)
    timer.update({"unit": unit, "unit_ms": unit_ms, "repeats": max(1, min(4096, int(round(target / unit_ms))))})
    timer["calibrated"] = unit_ms * timer["repeats"] >= 0.95 * target
    return timer
def _blocker_receipt(timer):
    estimated = (0.0 if timer["mode"] != "device_event" or not timer["repeats"]
                 else float(timer["unit_ms"] or 0.0) * float(timer["repeats"]))
    return {"mode": timer["mode"], "unit_ms": timer["unit_ms"], "repeats": timer["repeats"], "estimated_ms": estimated,
            "calibrated": bool(timer["calibrated"]), "target_ms": PLAN.get("timing", {}).get("blocker_target_ms")}
def _begin(timer, saturated):
    """Open a timed window after an optional cross-stream blocker dependency."""
    host_begin = time.perf_counter_ns()
    blocker_ran = bool(saturated and timer["mode"] == "device_event" and timer.get("calibrated") and timer["repeats"])
    timer["_blocker_ran"] = blocker_ran
    if blocker_ran:
        with _stream_context(timer.get("torch"), timer["blocker_stream"]):
            for _ in range(int(timer["repeats"])):
                timer["unit"]()
        timer["blocker_done"].record(timer["blocker_stream"])
        waiter = getattr(timer["stream"], "wait_event", None)
        if callable(waiter): waiter(timer["blocker_done"])
    timed = timer["mode"] == "device_event"
    if timed:
        timer["start"].record(timer["stream"])
    return host_begin, timed
def _finish(timer, host_begin, timed, saturated, blocker_ms=None):
    """Close the window on device events; host enqueue must fit the blocker."""
    if not timed:
        return {"duration_us": (time.perf_counter_ns() - host_begin) / 1000.0, "enqueue_us": None, "timing_mode": "host_fallback",
                "qualified": None}
    timer["end"].record(timer["stream"])
    enqueue_us = (time.perf_counter_ns() - host_begin) / 1000.0
    timer["end"].synchronize()
    duration_us = float(timer["start"].elapsed_time(timer["end"])) * 1000.0
    blocker_us = float(blocker_ms or 0.0) * 1000.0
    ran = bool(timer.get("_blocker_ran"))
    qualified = bool(ran and blocker_us > 0 and enqueue_us <= blocker_us) if saturated else None
    return {"duration_us": duration_us, "enqueue_us": enqueue_us, "timing_mode": ("stream_saturated" if saturated else "eager"),
            "qualified": qualified}
def _wait_work(work):
    waiter = getattr(work, "wait", None)
    if not callable(waiter): return False
    waiter(); return True
def _report(stream, path, kind, item, size, **extra):
    record = {"kind": kind, "tier": item["tier"], "op": item["op"], "bytes": size}
    record.update(extra)
    _write(stream, record, path)
def _write(stream, record, path):
    line = json.dumps(record, sort_keys=True) + "\n"
    if not path:
        stream.write(line); return
    handle = open(path, "a", encoding="utf-8", newline="\n")
    try: handle.write(line)
    finally: _cleanup_call(handle.close, sys.exc_info()[1])
def _supports_group(method, name, kwarg="group"):
    """Check send/recv or group-creation kwarg support once via code-object metadata."""
    if name in _GROUP_KWARG_SUPPORT:
        return _GROUP_KWARG_SUPPORT[name]
    target = getattr(method, "__func__", method)
    code = getattr(target, "__code__", None)
    if code is None:
        supported = True
    else:
        span = int(code.co_argcount) + int(getattr(code, "co_kwonlyargcount", 0))
        has_varkw = bool(int(code.co_flags) & 8)
        supported = kwarg in code.co_varnames[:span] or (has_varkw and kwarg == "group")
    _GROUP_KWARG_SUPPORT[name] = supported
    return supported
def _tier_groups(dist, rank, deadline):
    # The default WORLD communicator is always active for send/recv unless a
    # group is supplied; register it so the watcher can abort every
    # communicator that could be blocking, not just the tier group.
    _register_group(getattr(getattr(dist, "group", None), "WORLD", None))
    groups = {}
    for tier in PLAN["tiers"]:
        ranks = sorted(int(item) for item in tier["ranks"])
        group = None
        if tier.get("available", True):
            if time.monotonic() >= deadline:
                _signal_deadline(rank, "group_create")
                groups[tier["tier"]] = (None, rank in ranks, ranks)
                continue
            try:
                group = (dist.new_group(ranks, timeout=datetime.timedelta(seconds=max(1.0, deadline - time.monotonic())))
                         if _supports_group(dist.new_group, "new_group_timeout", "timeout")
                         else dist.new_group(ranks))
            except TimeoutError: raise
            except Exception:
                group = None
            _register_group(group)
        groups[tier["tier"]] = (group, rank in ranks, ranks)
    return groups
def _buffers(torch, nbytes, group_size, op, rank):
    bounded_count(nbytes, "buffer bytes", 4096, 268_435_456)
    bounded_count(group_size, "group_size", 1, 4096)
    bounded_count(nbytes * (group_size if op in {"all_gather", "reduce_scatter", "all_to_all"} else 1), "group buffer bytes", 1, 1 << 32)
    count = max(1, int(nbytes) // 4)
    if op == "all_to_all" and count % int(group_size) != 0:
        raise ProfilerUsageError("all_to_all payload elements must divide group_size")
    first = count  # total per-rank send payload for every collective
    second = {"all_gather": count * group_size, "reduce_scatter": count * group_size, "all_to_all": count, "all_to_all_v": count}.get(op)
    zero = lambda size: torch.zeros(size, dtype=torch.float32, device="npu")
    buffers = (zero(first), None if second is None else zero(second))
    if op in {"all_gather", "reduce_scatter"}:
        buffers[0].fill_(float(rank + 1))
    return buffers
def _call_once(torch, dist, op, buf, second, group, pair, rank, tag, ranks=(), style=None):
    if op == "send_recv":
        if pair is None or rank not in pair:
            return False
        sender = rank == pair[0]
        method = dist.send if sender else dist.recv
        extra = {"group": group} if _supports_group(method, "send_recv") else {}
        if sender:
            dist.send(buf, dst=pair[1], tag=tag, **extra)
        else:
            dist.recv(buf, src=pair[0], tag=tag, **extra)
        return True
    if op == "all_reduce":
        dist.all_reduce(buf, group=group)
    elif op == "all_gather":
        dist.all_gather_into_tensor(second, buf, group=group)
    elif op == "reduce_scatter":
        dist.reduce_scatter_tensor(buf, second, group=group)
    elif op == "all_to_all":
        dist.all_to_all_single(buf, second, group=group)
    elif op == "all_to_all_v":
        member_index = ranks.index(rank) if rank in ranks else rank
        send, recv = _all_to_all_v_counts(member_index, len(ranks), buf.numel(), style or "uniform")
        work = dist.all_to_all_single(second, buf, output_split_sizes=recv, input_split_sizes=send, group=group,
                                      async_op=True)
        _wait_work(work)
    else:
        raise RuntimeError("unsupported probe op " + str(op))
    return True
def _group_decision(torch, dist, group, member, value):
    """Reduce one continue flag across the group; every member joins."""
    if not member: return 1
    tensor = torch.tensor([int(value)], dtype=torch.int32, device="npu")
    dist.all_reduce(tensor, op=dist.ReduceOp.MIN, group=group)
    return int(tensor.item())
def _world_decision(torch, dist, value):
    """Agree a group-creation/abort flag across the whole world."""
    return _group_decision(torch, dist, None, True, value)
def _continue_decision(torch, dist, group, member, local_ok, deadline, faulted=False):
    """Shared continue flag: local status AND the shared deadline."""
    if not member: return 1
    value = int(bool(local_ok) and not faulted and time.monotonic() < deadline and not _abort_signaled(dist))
    return _group_decision(torch, dist, group, member, value)
def _bounded_destroy(dist, allowance_s):
    """Destroy with a wall-clock bound; never claim an unbounded cleanup."""
    limit = max(0.05, float(allowance_s or 0.05))
    def _watchdog(): os._exit(124)
    timer = threading.Timer(limit, _watchdog)
    timer.daemon = True
    timer.start()
    previous, completed = None, False
    def _timeout(_signum, _frame): raise TimeoutError("destroy_process_group exceeded cleanup allowance")
    try:
        if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
            previous = signal.signal(signal.SIGALRM, _timeout)
            # setitimer is the sub-second form of signal.alarm.
            signal.setitimer(signal.ITIMER_REAL, limit)
        dist.destroy_process_group()
        completed = True; return True
    except TimeoutError: raise
    except Exception:
        completed = True
        return False
    finally:
        active_exc = None if completed else sys.exc_info()[1]
        def reset_signal():
            if previous is not None:
                signal.setitimer(signal.ITIMER_REAL, 0); signal.signal(signal.SIGALRM, previous)
        try: _cleanup_call(timer.cancel, active_exc)
        finally: _cleanup_call(reset_signal, active_exc or sys.exc_info()[1])
def main(argv=None):
    global ABORT_FILE, _RUN_ID
    parser = argparse.ArgumentParser(description="Bounded HCCL tier sweep under shared rank deadlines.")
    parser.add_argument("--output", "-o", help="per-rank JSONL prefix (<prefix>.rank<N>.jsonl)")
    parser.add_argument("--abort-file", help="shared sentinel for cross-rank aborts")
    parser.add_argument("--run-id", help="explicit run identity shared by every rank")
    parser.add_argument("--max-bytes", type=int, default=256 * 1024 * 1024, help="maximum buffer size (default: 256 MiB)")
    args = parser.parse_args(argv)
    try: bounded_count(args.max_bytes, "max_bytes", 4096, 268_435_456)
    except ProfilerUsageError as exc: parser.error(str(exc))
    ABORT_FILE = args.abort_file or os.environ.get("MINDIE_FABRIC_PROBE_ABORT_FILE")
    explicit_run_id = args.run_id or os.environ.get("MINDIE_PROBE_RUN_ID") or (PLAN.get("run_id") if PLAN.get("explicit_run_id") else None)
    _RUN_ID = str(explicit_run_id or (PLAN.get("plan_id") or "fabric-probe") + "-" + os.urandom(8).hex())
    started = time.monotonic()
    try:
        import torch
        import torch_npu  # noqa: F401
        import torch.distributed as dist
    except TimeoutError: raise
    except Exception as exc:
        print(json.dumps({"status": "torch_npu_unavailable", "error": str(exc)}))
        return 3
    try:
        rank = int(os.environ.get("RANK", "0"))
        world = int(os.environ.get("WORLD_SIZE", "1"))
        # LOCAL_RANK is authoritative; device_count() is never probed first.
        per_node = max(1, int(PLAN.get("ranks_per_node") or 1))
        local_rank = int(os.environ.get("LOCAL_RANK", str(rank % per_node)))
        bounded_count(world, "WORLD_SIZE", 1, 4096)
        bounded_count(rank, "RANK", 0, world - 1)
        bounded_count(local_rank, "LOCAL_RANK", 0, 4095)
        visible = os.environ.get("ASCEND_RT_VISIBLE_DEVICES")
        allowed_phy = [int(value) for value in (PLAN.get("allowed_phy_ids") or ())]
        sparse_unmasked = (not visible) and local_rank in allowed_phy
        if local_rank >= per_node and not sparse_unmasked:
            raise ProfilerUsageError("LOCAL_RANK exceeds the plan's ranks_per_node")
    except ValueError as exc:
        parser.error(str(exc))
    except ProfilerUsageError as exc:
        parser.error(str(exc))
    torch.npu.set_device(local_rank)
    try:
        die = _check_physical_die(local_rank, PLAN.get("allowed_phy_ids"))
    except ProfilerUsageError as exc:
        print(json.dumps({"status": "physical_die_rejected", "rank": rank, "error": str(exc)[:400]}))
        return 4
    timer = _calibrate_blocker(torch, _new_timer(torch))
    blocker_ms = _blocker_receipt(timer)["estimated_ms"]
    remaining = max(0.01, float(PLAN["budget_s"]) - (time.monotonic() - started))
    max_wall = float(PLAN.get("deadline", {}).get("max_wall_s") or PLAN["budget_s"])
    init_timeout_s = max(1e-6, min(remaining, max_wall))
    init_timeout_s = min(init_timeout_s, max_wall) if max_wall > 0 else init_timeout_s
    try:
        dist.init_process_group(backend="hccl", rank=rank, world_size=world, timeout=datetime.timedelta(seconds=init_timeout_s))
        if not explicit_run_id and world > 1 and callable(getattr(dist, "all_reduce", None)) and hasattr(torch, "tensor") and hasattr(getattr(dist, "ReduceOp", None), "MAX"):
            seed_tok = torch.tensor([int.from_bytes(os.urandom(3), "big") + 1 if rank == 0 else 0], dtype=torch.int32, device="npu")
            dist.all_reduce(seed_tok, op=dist.ReduceOp.MAX)
            _RUN_ID = "%s-%06x" % (PLAN.get("plan_id") or "fabric-probe", int(seed_tok.item()))
    except TimeoutError: raise
    except Exception as exc:
        print(json.dumps({"status": "init_failed", "rank": rank, "error": str(exc)}))
        return 3
    output_path = args.output
    if output_path:
        output_path = f"{output_path}.rank{rank}.jsonl"
        handle = open(output_path, "w", encoding="utf-8", newline="\n")
        try:
            handle.write(json.dumps({"schema": "mindie-fabric-probe-samples/3", "rank": rank, "world_size": world, "local_rank": local_rank, "physical_die": die,
                                     "timer": _blocker_receipt(timer),
                                     "deadline": PLAN.get("deadline")}) + "\n")
        finally:
            _cleanup_call(handle.close, sys.exc_info()[1])
    deadline = started + float(PLAN["deadline"]["measurement_budget_s"])
    wall_deadline = started + max(0.001, float(PLAN["budget_s"]))
    groups = _tier_groups(dist, rank, deadline)
    local_ok = 1
    for tier in PLAN.get("tiers") or ():
        if not tier.get("available", True):
            continue
        group, member, _ranks = groups[tier["tier"]]
        if member and group is None:
            local_ok = 0
    world_ok = _world_decision(torch, dist, local_ok)
    if not world_ok:
        _write(sys.stdout, {"kind": "group_failed", "rank": rank, "reason": "one or more tier process groups failed to initialize"}, output_path)
        _bounded_destroy(dist, float(PLAN.get("deadline", {}).get("cleanup_allowance_s")
                        or PLAN.get("cleanup_allowance_s") or 0.1))
        _stop_abort_watcher()
        return 2
    emitted = 0
    run_ok = True
    group_faulted = False
    final_failure = None
    buffered = []
    cleanup_allowance = float(PLAN.get("deadline", {}).get("cleanup_allowance_s")
                              or PLAN.get("cleanup_allowance_s") or 0.1)
    body_completed = False
    destroyed, cleanup_failed = True, False
    try:
        for item in PLAN.get("admitted") or ():
            tier = next((entry for entry in PLAN["tiers"] if entry["tier"] == item["tier"]), None)
            if tier is None:
                continue
            group, member, ranks = groups[item["tier"]]
            if not member:
                continue
            pair, pair_index = None, None
            for index, candidate in enumerate(tier.get("pairs") or ()):
                if rank in candidate:
                    pair, pair_index = candidate, index
                    break
            size = int(item["bytes"])
            if size > args.max_bytes:
                continue
            local_ok = 1
            alive = _continue_decision(torch, dist, group, member, local_ok, deadline)
            if not alive:
                expired = time.monotonic() >= deadline
                _write(sys.stdout, {"kind": "unmeasured", "tier": item["tier"], "op": item["op"], "bytes": size, "reason": "deadline" if expired else "step_failed", "status": ("deadline_exceeded" if expired else "step_failed")}, output_path)
                run_ok = False
                continue
            tag = 1000 + int(pair_index or 0)
            try:
                buf, second = _buffers(torch, size, len(ranks), item["op"], rank)
            except TimeoutError: raise
            except Exception as exc:
                local_ok = 0
                buf, second = None, None
                _write(sys.stdout, {"kind": "failed", "tier": item["tier"], "op": item["op"], "bytes": size, "rank": rank, "stage": "allocation", "error": str(exc)}, output_path)
            # Every fallible local preparation happens before this gate.
            if local_ok:
                try:
                    torch.npu.synchronize()
                except TimeoutError: raise
                except Exception as exc:
                    local_ok = 0
                    _signal_abort(dist, rank, "validation_pre_sync", exc)
                    _write(sys.stdout, {"kind": "failed", "tier": item["tier"], "op": item["op"], "bytes": size, "rank": rank, "stage": "pre_sync", "error": str(exc)}, output_path)
            validated = _continue_decision(torch, dist, group, member, local_ok, deadline)
            if not validated:
                expired = time.monotonic() >= deadline
                _write(sys.stdout, {"kind": "unmeasured", "tier": item["tier"], "op": item["op"], "bytes": size, "reason": "deadline" if expired else "step_failed", "status": ("deadline_exceeded" if expired else "step_failed")}, output_path)
                run_ok = False
                continue
            # The validation data collective is admitted by all ranks together.
            try:
                _call_once(torch, dist, item["op"], buf, second, group, pair, rank, tag, ranks, (item.get("split_styles") or ["uniform"])[0])
            except TimeoutError: raise
            except Exception as exc:
                group_faulted = True
                run_ok = False
                peer_aborted = type(exc).__name__ == "PeerAbortedError"
                if not peer_aborted:
                    _signal_abort(dist, rank, "validation_data_collective", exc)
                _write(sys.stdout, {"kind": "failed", "tier": item["tier"], "op": item["op"], "bytes": size, "rank": rank, "stage": "data_collective", "status": ("peer_aborted" if peer_aborted else "collective_failed"), "error": str(exc)}, output_path)
                break
            local_valid = 0
            try:
                torch.npu.synchronize()
                local_valid = 1
                if item["op"] not in {"send_recv", "all_to_all"}:
                    local_valid = int(bool(torch.isfinite(buf).all().item()))
            except TimeoutError: raise
            except Exception as exc:
                _signal_abort(dist, rank, "validation_post_sync", exc)
                _write(sys.stdout, {"kind": "failed", "tier": item["tier"], "op": item["op"], "bytes": size, "rank": rank, "stage": "post_sync", "error": str(exc)}, output_path)
            if not _continue_decision(torch, dist, group, member, int(local_valid), deadline, group_faulted):
                _write(sys.stdout, {"kind": "unmeasured", "tier": item["tier"], "op": item["op"], "bytes": size, "reason": "step_failed"}, output_path)
                run_ok = False
                continue
            validated = True
            warmup_count = max(0, int(item.get("warmup", PLAN.get("warmup", 0))))
            count = max(0, int(item.get("iterations", 0)))
            aborted, abort_reason = False, "deadline"
            modes = item.get("timing_modes") or ["eager"]
            split_styles = item.get("split_styles") or ["uniform"]
            pair_rounds = item.get("pair_rounds") or []
            round_cursor = 0
            timed_index = [0]
            for mode in modes:
                saturated = (mode == "stream_saturated" and timer["mode"] == "device_event")
                for style in split_styles:
                    for phase, steps in (("warmup", warmup_count), ("timed", count)):
                        for iter_index in range(steps):
                            local_ok = 1
                            try:
                                torch.npu.synchronize()
                            except TimeoutError: raise
                            except Exception as exc:
                                local_ok = 0
                                _signal_abort(dist, rank, phase + "_pre_sync", exc)
                                _report(sys.stdout, output_path, "failed", item, size, rank=rank, stage=phase + "_pre_sync", error=str(exc))
                            gate = _continue_decision(torch, dist, group, member, local_ok, deadline, group_faulted)
                            if not gate:
                                expired = time.monotonic() >= deadline
                                aborted = True
                                abort_reason = "deadline" if expired else "step_failed"
                                run_ok = False
                                _report(sys.stdout, output_path, "unmeasured", item, size, reason=abort_reason, status=("deadline_exceeded" if expired else "step_failed"))
                                break
                            # Coordination time excluded: start timing after pre-step MIN gate returns 1.
                            round_index = (round_cursor % len(pair_rounds)
                                           if pair_rounds and item["op"] == "send_recv" else None)
                            concurrent_pairs = (len(pair_rounds[round_index]) if round_index is not None
                                                else 1 if item["op"] == "send_recv" else None)
                            active_rails = 1 if item["op"] == "send_recv" else None
                            if round_index is not None:
                                pair, tag = _round_pair(pair_rounds, round_cursor, rank)
                            host_begin, timed = _begin(timer, saturated)
                            try:
                                finished = _call_once(torch, dist, item["op"], buf, second, group, pair, rank, tag, ranks, style)
                            except TimeoutError: raise
                            except Exception as exc:
                                group_faulted = True
                                aborted, abort_reason = True, "step_failed"
                                run_ok = False
                                peer_aborted = type(exc).__name__ == "PeerAbortedError"
                                if not peer_aborted:
                                    _signal_abort(dist, rank, phase + "_data_collective", exc)
                                _report(sys.stdout, output_path, "failed", item, size, rank=rank, stage=phase + "_data_collective", status=("peer_aborted" if peer_aborted else "collective_failed"), error=str(exc))
                                break
                            latency_us = 0.0
                            local_ok = 1
                            try:
                                # The event window closes before the post-step device sync.
                                sample = _finish(timer, host_begin, timed, saturated, blocker_ms)
                                latency_us = sample["duration_us"]
                                torch.npu.synchronize()
                                if item["op"] in {"all_gather", "reduce_scatter"}:
                                    output_buffer = second if item["op"] == "all_gather" else buf
                                    local_ok = int(bool(torch.isfinite(output_buffer).all().item()))
                                elif item["op"] not in {"send_recv", "all_to_all", "all_to_all_v"}:
                                    local_ok = int(bool(torch.isfinite(buf).all().item()))
                            except TimeoutError: raise
                            except Exception as exc:
                                local_ok = 0
                                _signal_abort(dist, rank, phase + "_post_sync", exc)
                                _report(sys.stdout, output_path, "failed", item, size, rank=rank, stage=phase + "_post_sync", error=str(exc))
                            gate = _continue_decision(torch, dist, group, member, local_ok, deadline, group_faulted)
                            if not gate:
                                expired = (time.monotonic() >= deadline or _abort_signaled(dist))
                                aborted = True
                                abort_reason = "deadline" if expired else "step_failed"
                                run_ok = False
                                _write(sys.stdout, {"kind": "unmeasured", "tier": item["tier"], "op": item["op"], "bytes": size, "reason": abort_reason, "status": ("deadline_exceeded" if expired else "step_failed")}, output_path)
                                break
                            round_cursor += 1
                            if phase != "timed" or not finished:
                                if phase == "timed":
                                    _continue_decision(torch, dist, group, member, 1, wall_deadline, group_faulted)
                                continue
                            device = sample["timing_mode"] != "host_fallback"
                            direction = ("send" if item["op"] == "send_recv" and pair and rank == pair[0] else "recv" if item["op"] == "send_recv" and pair else "collective")
                            repeat_index = round_index * count + iter_index if round_index is not None else timed_index[0]
                            record = {"schema": "mindie-fabric-probe-sample/3", "tier": item["tier"], "op": item["op"], "bytes": size, "latency_us": latency_us, "rank": rank, "world_size": world,
                                "group_size": len(ranks), "group_ranks": list(ranks), "protocol": tier.get("protocol"), "link": tier.get("link"),
                                "regime": item.get("regime", "isolated"), "direction": direction, "validated": bool(validated), "clock_mhz": _clock_mhz(),
                                "iterations": count, "warmup": warmup_count, "fixed_iteration_count": True,
                                "monotonic_s": time.monotonic() - started, "timing_mode": sample["timing_mode"], "enqueue_us": sample["enqueue_us"],
                                "device_completion_us": (sample["duration_us"] if device else None), "saturated_qualified": sample["qualified"],
                                "repeat_index": repeat_index, "split_style": (style if item["op"] == "all_to_all_v" else None),
                                "pair": ([int(pair[0]), int(pair[1])] if item["op"] == "send_recv" and pair else None),
                                "active_rails": active_rails, "concurrent_pairs": concurrent_pairs, "round_index": round_index,
                                "input_bytes": (size * len(ranks) if item["op"] == "reduce_scatter" else size),
                                "output_bytes": (size * len(ranks) if item["op"] == "all_gather" else size),
                                "route": item.get("route"), "hops": item.get("hops"), "rails": item.get("rails"),
                                "blocker": _blocker_receipt(timer)}
                            if item["op"] == "all_to_all_v":
                                member_index = ranks.index(rank) if rank in ranks else rank
                                record["send_counts"], record["recv_counts"] = _all_to_all_v_counts( member_index, len(ranks), max(1, size // 4), style)
                            record.update({"sample_id": _sample_id(item["tier"], item["op"], size, rank, timed_index[0], style, sample["timing_mode"]),
                                "run_id": _RUN_ID, "split": ("heldout" if size in _HELDOUT_SIZES else "train"),
                                "source": ("capture://fabric-probe/%s/%s/r%s.%s" % (item["tier"], item["op"], rank, timed_index[0])),
                                "duration_ms": (sample["duration_us"] / 1000.0 if device else None), "work_bytes": size,
                                "qualified": bool(device and (sample["timing_mode"] != "stream_saturated" or sample["qualified"] is True)),
                                "identity": _sample_identity(item, size, rank, sample["timing_mode"])})
                            timed_index[0] += 1
                            # Telemetry can take time: requalify the wall budget only
                            # through the shared MIN tensor, never a local branch.
                            wall_ok = _continue_decision(torch, dist, group, member, 1, wall_deadline, group_faulted)
                            if not wall_ok:
                                record.update({"validated": False, "status": "deadline_exceeded", "reason": "wall_budget_exceeded"})
                                run_ok = False
                            emitted += 1
                            buffered.append(record)
                            if not wall_ok:
                                aborted, abort_reason = True, "deadline"
                                break
                        if aborted:
                            break
                    if aborted:
                        break
                if aborted:
                    break
            if aborted:
                _report(sys.stdout, output_path, "unmeasured", item, size, reason=abort_reason, status=("deadline_exceeded" if abort_reason == "deadline" else "step_failed"))
                break
        if not group_faulted and emitted:
            final_ok = _continue_decision(torch, dist, group, member, 1, wall_deadline, group_faulted)
            if not final_ok:
                expired = (time.monotonic() >= wall_deadline or _abort_signaled(dist))
                final_failure = ("deadline_exceeded" if expired else "step_failed")
                if expired:
                    _signal_deadline(rank, "final_wall_gate")
                run_ok = False
                _write(sys.stdout, {"kind": "unmeasured", "reason": "deadline" if expired else "step_failed", "status": ("deadline_exceeded" if expired else "step_failed")}, output_path)
            elif time.monotonic() >= wall_deadline:
                final_failure = "deadline_exceeded"
                _signal_deadline(rank, "final_wall_return")
                run_ok = False
            elif _abort_signaled(dist):
                final_failure = "peer_aborted"
                run_ok = False
        body_completed = True
    finally:
        active_exc = None if body_completed else sys.exc_info()[1]
        if active_exc is not None:
            _cleanup_call(lambda: _signal_abort(dist, rank, "exception", active_exc), active_exc)
        def finish():
            nonlocal destroyed, cleanup_failed, run_ok, final_failure
            if not group_faulted:
                destroyed = bool(_bounded_destroy(dist, cleanup_allowance))
                if not destroyed:
                    cleanup_failed = True
                    run_ok = False
                    final_failure = final_failure or "cleanup_failed"
                    _signal_abort(dist, rank, "cleanup_destroy", "destroy_process_group failed")
                    _disqualify(buffered, "cleanup_failed", "cleanup_failed")
                    try:
                        _write(sys.stdout, {"kind": "cleanup_failed", "rank": rank, "cleanup_failed": True, "status": "cleanup_failed"}, output_path)
                    except TimeoutError: raise
                    except Exception:
                        pass
            # No collective remains after destroy: qualify the real completion
            # time again so a late final MIN return cannot certify samples.
            if final_failure is None and not group_faulted and emitted:
                if time.monotonic() >= wall_deadline:
                    final_failure = "deadline_exceeded"
                    _signal_deadline(rank, "post_destroy")
                elif _abort_signaled(dist):
                    final_failure = "peer_aborted"
            if final_failure is not None:
                run_ok = False
                _disqualify(buffered, final_failure, final_failure)
            elif group_faulted:
                _disqualify(buffered, "step_failed", "group_faulted")
        try:
            _cleanup_call(finish, active_exc)
        finally:
            _cleanup_call(_stop_abort_watcher, active_exc or sys.exc_info()[1])
    if final_failure is not None:
        _write(sys.stdout, {"kind": "status", "status": final_failure, "reason": final_failure, "rank": rank}, output_path)
    for record in buffered:
        _write(sys.stdout, record, output_path)
    return 0 if (emitted and run_ok and not group_faulted and destroyed and not cleanup_failed and final_failure is None) else 2
if __name__ == "__main__":
    raise SystemExit(main())
'''
