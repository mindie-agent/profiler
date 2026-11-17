"""Strict ACLGraph input records.

[Role]
Validate stream intervals and legacy or explicit multi-node parallel regions.
[Invariants]
Unknown keys, non-boolean flags and malformed graph evidence fail closed.
[Timeouts & Locks]
Bounded in-memory validation; no waits or locks.
[Side-Effect Policy]
No filesystem, stream or device changes.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

MIB = 1024**2
_HCCL_TOKENS = ("allreduce", "allgather", "reducescatter", "alltoall", "hccl", "dispatch", "combine")

class ACLGraphModelError(ValueError):
    """Invalid graph-mode or stream declaration."""


class GraphMode(str, Enum):
    NONE = "none"
    PIECEWISE = "piecewise"
    FULL = "full"
    FULL_DECODE_ONLY = "full_decode_only"
    FULL_AND_PIECEWISE = "full_and_piecewise"


class HcclExpansion(str, Enum):
    AIV = "AIV"
    CCU_SCHED = "CCU_SCHED"
    AICPU = "AICPU"


def _int(name: str, value: object, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ACLGraphModelError(f"{name} must be an integer, got {value!r}")
    number = float(value)
    if not math.isfinite(number) or number != int(number) or int(number) < minimum:
        raise ACLGraphModelError(f"{name} must be an integer >= {minimum}, got {value!r}")
    return int(number)


def _num(name: str, value: object, *, minimum: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ACLGraphModelError(f"{name} must be a finite number, got {value!r}")
    number = float(value)
    if not math.isfinite(number) or number < minimum:
        raise ACLGraphModelError(f"{name} must be finite and >= {minimum}, got {value!r}")
    return number


@dataclass(frozen=True, slots=True)
class StreamInterval:
    op: str
    stream_id: int
    start_us: float
    end_us: float
    aic_blocks: int = 0
    aiv_blocks: int = 0
    io_bytes: int = 0
    hccl_expansion_mode: str = "AIV"
    waits_on_capture_root: bool = True
    joined_at_exit: bool = True
    aliases_buffer: bool = False
    events_ordered: bool = True
    is_hccl: bool = False

    read_bytes: int | None = None
    write_bytes: int | None = None
    unique_bytes: int | None = None

    def __post_init__(self) -> None:
        for name in ("read_bytes", "write_bytes", "unique_bytes"):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, _int(name, getattr(self, name)))
        if (self.read_bytes is None) != (self.write_bytes is None):
            raise ACLGraphModelError("read/write service counters must be supplied together")
        if not isinstance(self.op, str):
            raise ACLGraphModelError("op must be a string")
        object.__setattr__(self, "stream_id", _int("stream_id", self.stream_id))
        object.__setattr__(self, "start_us", _num("start_us", self.start_us))
        object.__setattr__(self, "end_us", _num("end_us", self.end_us))
        if self.end_us < self.start_us:
            raise ACLGraphModelError("invalid stream interval")
        for name in ("aic_blocks", "aiv_blocks", "io_bytes"):
            object.__setattr__(self, name, _int(name, getattr(self, name)))
        mode = (self.hccl_expansion_mode.value if isinstance(self.hccl_expansion_mode, HcclExpansion)
                else str(self.hccl_expansion_mode).upper())
        if mode not in {item.value for item in HcclExpansion}:
            raise ACLGraphModelError(f"unknown HCCL expansion mode: {self.hccl_expansion_mode!r}")
        object.__setattr__(self, "hccl_expansion_mode", mode)
        for name in ("waits_on_capture_root", "joined_at_exit", "aliases_buffer",
                     "events_ordered", "is_hccl"):
            if not isinstance(getattr(self, name), bool):
                raise ACLGraphModelError(f"{name} must be bool")
        if not self.is_hccl and any(token in self.op.lower() for token in _HCCL_TOKENS):
            object.__setattr__(self, "is_hccl", True)

    @property
    def duration_us(self) -> float:
        return self.end_us - self.start_us

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StreamInterval":
        known = {field.name for field in cls.__dataclass_fields__.values()}
        unknown = set(payload) - known
        if unknown:
            raise ACLGraphModelError(f"unknown stream fields: {sorted(unknown)}")
        try:
            return cls(**dict(payload))
        except (TypeError, ValueError) as exc:
            raise ACLGraphModelError(f"invalid stream interval: {exc}") from exc


@dataclass(frozen=True, slots=True)
class ParallelRegion:
    name: str
    branch_a: StreamInterval | None = None
    branch_b: StreamInterval | None = None
    graph_backend: str = "aclgraph"
    graph_mode: str = "full"
    piece_boundary_between: bool = False
    event_pairs: int = 1
    l2_size_bytes: int = 128 * MIB
    aic_cores: int = 32
    aiv_cores: int = 64
    rw_contention_alpha: float = 0.30
    memory_bw_gbps: float = 6400.0
    hbm_bw_gbps: float = 1600.0
    event_causality_observed: bool = False
    capture_root_stream_id: int | None = None
    nodes: tuple = ()
    intervals: tuple = ()
    events: tuple = ()
    records: tuple = ()
    waits: tuple = ()
    dependencies: tuple = ()
    dag: Any = field(default=None, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ACLGraphModelError("region name is required")
        for name in ("nodes", "intervals", "events", "records", "waits", "dependencies"):
            if not isinstance(getattr(self, name), (tuple, list)):
                raise ACLGraphModelError(f"{name} must be a list or tuple")
        explicit = bool(self.nodes or self.intervals)
        if explicit and (self.branch_a is not None or self.branch_b is not None):
            raise ACLGraphModelError("use nodes/intervals or a legacy branch pair, not both")
        if not explicit:
            for name in ("branch_a", "branch_b"):
                if not isinstance(getattr(self, name), StreamInterval):
                    raise ACLGraphModelError(f"{name} must be a StreamInterval")
        object.__setattr__(self, "graph_backend", str(self.graph_backend).lower())
        mode = self.graph_mode.value if isinstance(self.graph_mode, GraphMode) else str(self.graph_mode)
        object.__setattr__(self, "graph_mode", mode.lower())
        if self.graph_backend not in ("aclgraph", "torchair_ge"):
            raise ACLGraphModelError("graph_backend must be aclgraph or torchair_ge")
        if self.graph_mode not in {item.value for item in GraphMode}:
            raise ACLGraphModelError(f"unknown graph mode: {self.graph_mode!r}")
        object.__setattr__(self, "event_pairs", _int("event_pairs", self.event_pairs))
        for name in ("event_causality_observed", "piece_boundary_between"):
            if not isinstance(getattr(self, name), bool):
                raise ACLGraphModelError(f"{name} must be bool")
        if self.capture_root_stream_id is not None:
            object.__setattr__(self, "capture_root_stream_id",
                               _int("capture_root_stream_id", self.capture_root_stream_id))
        object.__setattr__(self, "l2_size_bytes", _int("l2_size_bytes", self.l2_size_bytes, minimum=1))
        object.__setattr__(self, "aic_cores", _int("aic_cores", self.aic_cores, minimum=1))
        object.__setattr__(self, "aiv_cores", _int("aiv_cores", self.aiv_cores, minimum=1))
        object.__setattr__(self, "rw_contention_alpha", _num("rw_contention_alpha", self.rw_contention_alpha))
        if self.rw_contention_alpha > 1.0:
            raise ACLGraphModelError("rw_contention_alpha must be <= 1")
        object.__setattr__(self, "memory_bw_gbps", _num("memory_bw_gbps", self.memory_bw_gbps, minimum=1e-9))
        object.__setattr__(self, "hbm_bw_gbps", _num("hbm_bw_gbps", self.hbm_bw_gbps, minimum=1e-9))
        from .aclgraph_dag import reconstruct_dag
        object.__setattr__(self, "dag", reconstruct_dag(self))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ParallelRegion":
        if not isinstance(payload, Mapping):
            raise ACLGraphModelError("parallel region must be a mapping")
        known = {name for name, info in cls.__dataclass_fields__.items() if info.init}
        hardware_keys = {"hardware", "sku"} & set(payload)
        if set(payload) - known - hardware_keys:
            raise ACLGraphModelError(f"unknown region fields: {sorted(set(payload) - known - hardware_keys)}")
        try:
            values = {key: value for key, value in payload.items() if key not in hardware_keys}
            hardware = payload.get("hardware") or payload.get("sku")
            if hardware:
                from .hardware_presets import resolve_chip_topology

                topology = resolve_chip_topology(str(hardware))
                values.setdefault("aic_cores", topology.aic_cores)
                values.setdefault("aiv_cores", topology.aiv_cores)
                values.setdefault("l2_size_bytes", topology.l2_bytes_per_die)
                values.setdefault("hbm_bw_gbps", topology.hbm_gbps)
            for key in ("branch_a", "branch_b"):
                if key in values:
                    values[key] = StreamInterval.from_mapping(values[key])
            return cls(**values)
        except (KeyError, TypeError, ValueError) as exc:
            raise ACLGraphModelError(f"invalid parallel region: {exc}") from exc


