"""Peer-reduction harness for the Round-3 fabric-probe regressions.

[Role]
  Execute the emitted probe script sequentially for one simulated rank while a
  peer stub supplies the other rank's decision input and the exact shared MIN is
  recorded.  This makes allocation failure, deadline and warmup behavior
  observable without launching HCCL or threads.

[Invariants]
  * A decision tensor is reduced with the peer value at the same decision index;
    the resulting log is the shared decision sequence for that rank.
  * Data collectives are counted separately and never contribute a decision.
  * Allocation can fail or advance the monotonic clock exactly at the allocation
    boundary, which is the Round-3 counterexample boundary.
  * Environment rank reads in the emitted script are replaced only for this
    in-process harness.

[Timeouts & Locks]
  No real process group, thread or device is created; every call is synchronous.

[Side-Effect Policy]
  No I/O; module injection is restored before returning.
"""

from __future__ import annotations

import contextlib
import io
import sys
import types

from mindie_profiler.fabric_probe import (
    build_fabric_probe_plan, emit_fabric_probe_script,
)

# -------------------------------------------------------- probe peer harness
class _Clock:
    def __init__(self, now=1000.0):
        self.now = float(now)

    def monotonic(self):
        return self.now

    def perf_counter_ns(self):
        return int(self.now * 1e9)


class _Tensor:
    def __init__(self, shape=(), dtype=None, device=None, decision=False,
                 item=1):
        self.shape = tuple(shape)
        self.dtype = dtype
        self.device = device
        self._decision = decision
        self._item = item

    def numel(self):
        total = 1
        for dim in self.shape:
            total *= dim
        return total

    def item(self):
        return self._item

    def zero_(self):
        return self

    def fill_(self, *_args):
        return self

    def copy_(self, _other):
        return self

    def clone(self):
        return _Tensor(self.shape, self.dtype, self.device)

    def sum(self):
        return _Tensor((), self.dtype, self.device)

    def reshape(self, shape):
        return _Tensor(shape, self.dtype, self.device)

    def all(self):
        return self


class _Event:
    def record(self):
        return None

    def synchronize(self):
        return None

    def elapsed_time(self, _other):
        return 10.0


class _PeerDist:
    """Sequential peer stub: records the shared MIN decision after each rank."""

    class ReduceOp:
        MIN = "min"

    def __init__(self, rank, peer):
        self.rank = rank
        self.peer = dict(peer)
        self.decisions = 0
        self.log = []
        self.data = 0
        self.timeout = None

    def init_process_group(self, **kwargs):
        self.timeout = kwargs.get("timeout")

    def new_group(self, ranks):
        return ("group", tuple(ranks))

    def destroy_process_group(self):
        return None

    def all_reduce(self, tensor, group=None, op=None):
        if getattr(tensor, "_decision", False):
            local = int(tensor._item)
            peer = int(self.peer.get(self.decisions, 1))
            combined = min(local, peer)
            tensor._item = combined
            self.log.append(combined)
            self.decisions += 1
        else:
            self.data += 1

    def all_gather_into_tensor(self, *_args, **_kwargs):
        self.data += 1

    def reduce_scatter_tensor(self, *_args, **_kwargs):
        self.data += 1

    def all_to_all_single(self, *_args, **_kwargs):
        self.data += 1

    def send(self, *_args, **_kwargs):
        return None

    def recv(self, *_args, **_kwargs):
        return None


def _probe_run(plan, rank, peer, *, advance_alloc=0.0, fail_alloc=False):
    script = emit_fabric_probe_script(plan)["script"]
    script = script.replace('os.environ.get("RANK", "0")', str(rank))
    script = script.replace('os.environ.get("WORLD_SIZE", "1")', "2")
    script = script.replace(
        'os.environ.get("LOCAL_RANK", str(rank % max(1, torch.npu.device_count())))',
        "0")
    clock = _Clock()

    def zeros(*args, **kwargs):
        if fail_alloc:
            raise RuntimeError("simulated allocation failure")
        if advance_alloc:
            clock.now += float(advance_alloc)
        shape = args[0] if len(args) == 1 and isinstance(args[0], (tuple, list)) \
            else args
        return _Tensor(shape, kwargs.get("dtype"), kwargs.get("device"))

    torch = types.ModuleType("torch")
    torch.__path__ = []
    for name in ("int8", "int32", "int64", "uint8", "bfloat16", "float16",
                 "float32", "bool", "float8_e4m3fn", "float8_e5m2"):
        setattr(torch, name, name)
    torch.zeros = zeros
    torch.tensor = lambda values, dtype=None, device=None: _Tensor(
        (len(values),), dtype, device, decision=True, item=values[0])
    torch.empty_strided = lambda shape, strides, dtype=None, device=None: _Tensor(
        shape, dtype, device)
    torch.isfinite = lambda _tensor: _Tensor((), None, None, item=True)
    torch.npu = types.SimpleNamespace(
        synchronize=lambda: None, device_count=lambda: 2,
        set_device=lambda _rank: None, memory_allocated=lambda: 0,
        Event=lambda enable_timing=False: _Event())
    npu = types.ModuleType("torch_npu")
    npu.__path__ = []
    npu.npu_get_clock_rate = lambda: 1.8e9
    distributed = types.ModuleType("torch.distributed")
    dist = _PeerDist(rank, peer)
    for name in ("init_process_group", "new_group", "destroy_process_group",
                 "all_reduce", "all_gather_into_tensor", "reduce_scatter_tensor",
                 "all_to_all_single", "send", "recv"):
        setattr(distributed, name, getattr(dist, name))
    distributed.ReduceOp = _PeerDist.ReduceOp
    torch.distributed = distributed
    namespace = {"__name__": "round3_probe"}
    old = {name: sys.modules.get(name) for name in ("torch", "torch_npu",
                                                    "torch.distributed")}
    sys.modules["torch"] = torch
    sys.modules["torch_npu"] = npu
    sys.modules["torch.distributed"] = distributed
    try:
        exec(compile(script, "<probe>", "exec"), namespace)
        namespace["time"] = clock
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = namespace["main"]([])
    finally:
        for name, value in old.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return code, dist, buffer.getvalue()


