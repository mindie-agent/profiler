"""ACLGraph capture/replay resource model and A1-A5 multi-stream diagnostics.

[Role]
Model vLLM-Ascend ACLGraphWrapper/BreakableACLGraphWrapper/UpdatableGraph,
PIECEWISE vs FULL modes, SuperKernel dcci, the SQ/CQ capture budget (207008),
and evidence-graded A1-A5 diagnosis of intended parallel regions.
[Invariants]
A1 requires identical stream IDs. A2 requires binding event delay and observed
causality to confirm a premature event; otherwise evidence stays bounded. A3 only
claims HCCL AIV expansion when at least one branch is an HCCL op and re-solves
shared AIV contention. A4 uses a bandwidth service model, not an arbitrary
overlap*alpha penalty. A5 needs an explicit capture root plus unjoined or
aliased-buffer evidence. Draft-EAGLE is `is_draft_model and use_eagle`.
[Timeouts & Locks]
Pure arithmetic; no device APIs, locks, sleeps, or I/O.
[Side-Effect Policy]
Read-only model; no capture, replay, or filesystem effect.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from .aclgraph_schema import (ACLGraphModelError, GraphMode, HcclExpansion,
                              StreamInterval, ParallelRegion, _int, _num)
from .profiler_configs import (ACLGraphLaunchConfig, DEFAULT_ACLGRAPH_LAUNCH_CONFIG,
                               DEFAULT_MEMORY_FORENSICS_CONFIG)

MIB = DEFAULT_MEMORY_FORENSICS_CONFIG.min_leak_bytes
SQ_CQ_DEFAULT_CAPACITY = DEFAULT_ACLGRAPH_LAUNCH_CONFIG.sq_cq_stream_capacity
EVENT_OVERHEAD_US = DEFAULT_ACLGRAPH_LAUNCH_CONFIG.event_sync_us
DCCI_AFTER_KERNEL_END = ".*"
CAPTURE_ERROR_CODE = "207008"
STREAM_RESOURCE_MARKERS = ("insufficient_stream_resources", "stream resources are insufficient")
OLD_HDK_CAPTURE_MARKER = "alloc sq cq fail"
_HCCL_TOKENS = ("allreduce", "allgather", "reducescatter", "alltoall", "hccl", "dispatch", "combine")


def classify_capture_error(text: str) -> str:
    """Distinguish 207008 stream exhaustion from legacy HDK SQ/CQ allocation."""
    lowered = str(text).lower()
    if CAPTURE_ERROR_CODE in str(text) or any(marker in lowered for marker in STREAM_RESOURCE_MARKERS):
        return "stream_resource_207008"
    if OLD_HDK_CAPTURE_MARKER in lowered:
        return "old_hdk_alloc_sq_cq"
    return "unknown"


class StreamResourceExhausted(RuntimeError):
    error_code = "207008"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    name: str
    overlap_pct: float
    span_us: float
    wall_us: float
    net_speedup_us: float
    cause: str
    evidence: str
    recommendations: tuple[str, ...] = ()
    secondary: tuple[str, ...] = ()
    evidence_grade: str = "observed"
    details: Mapping[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.code == "OK"

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code, "name": self.name, "overlap": round(self.overlap_pct, 4),
            "span": round(self.span_us, 4), "wall": round(self.wall_us, 4),
            "net": round(self.net_speedup_us, 4), "cause": self.cause,
            "grade": self.evidence_grade, "rec": list(self.recommendations),
        }


def _overlap_us(a: StreamInterval, b: StreamInterval) -> float:
    return max(0.0, min(a.end_us, b.end_us) - max(a.start_us, b.start_us))


def _overlap_pct(a: StreamInterval, b: StreamInterval) -> float:
    overlap = _overlap_us(a, b)
    smaller = min(a.duration_us, b.duration_us)
    return 100.0 * overlap / smaller if smaller > 0 else 0.0


def _dangling(interval: StreamInterval, root: int | None) -> bool:
    # ABI: ACLGraph capture records tasks for replay; cross-stream dependencies and capture boundaries must survive partitioning or fusion.
    if interval.stream_id != root and (not interval.waits_on_capture_root or not interval.joined_at_exit):
        return True
    return interval.aliases_buffer and not interval.events_ordered


def diagnose_region(
    region: ParallelRegion | Mapping[str, Any],
    *,
    config: ACLGraphLaunchConfig = DEFAULT_ACLGRAPH_LAUNCH_CONFIG,
) -> Diagnostic:
    """Classify one intended parallel region into A1..A5 or OK."""
    if not isinstance(region, ParallelRegion):
        region = ParallelRegion.from_mapping(region)
    dag = region.dag
    intervals = [node.interval for node in dag.nodes]
    streams = {x.stream_id for x in intervals}
    overlap, pct, span = dag.overlap_us, dag.overlap_pct, dag.critical_path_us
    # Only observed DAG wall time and overlap are reported here.  A modeled
    # memory service would add an unobserved duration to the measured span.
    wall = dag.event_wall_us
    net = dag.serial_us - wall
    details = {**dag.details(), "net_wall_us": wall}
    # ABI: ACLGraph capture records tasks for replay; cross-stream dependencies and capture boundaries must survive partitioning or fusion.
    if dag.capture_hazards:
        return Diagnostic(
            "A5", "CAPTURE_DANGLING_STREAM_OR_POOL_HAZARD", pct, span, wall, net,
            "capture_stream_not_waiting_or_not_joined_or_buffer_alias",
            "explicit capture-root/dependency/pool-lifetime evidence",
            ("wait on the capture root at entry", "join_after_forward() before capture exit",
             "record_stream()/event ordering for aliased buffers"),
            (), "observed", details,
        )
    if len(streams) == 1:
        return Diagnostic(
            "A1", "SAME_STREAM_COLLAPSE", pct, span, wall, net,
            "missing_npu_stream_switch_or_default_stream_fallback",
            "both branches carry the same observed stream_id",
            ("wrap the secondary branch in npu_stream_switch", "verify Stream ID in kernel_details"),
            (), "confirmed", details,
        )
    if pct <= config.overlap_serial_pct:
        binding_event = (len(dag.event_delays_us) > 0 if dag.explicit else dag.event_cost_us > 0)
        # ABI: ACLGraph capture records tasks for replay; cross-stream dependencies and capture boundaries must survive partitioning or fusion.
        if region.piece_boundary_between and region.graph_mode in ("piecewise", "full_and_piecewise"):
            cause = "piecewise_aclgraph_split_barrier"
            rec = ("use FULL/FULL_DECODE_ONLY for uniform decode", "move the split outside the region")
            grade = "observed"
        elif dag.event_count > 0 and binding_event and region.event_causality_observed:
            cause = "premature_event_record_wait"
            rec = ("stage EventRecord after the producer milestone", "use RoutedMoEMilestones")
            grade = "confirmed"
        elif dag.event_count > 0 and binding_event:
            cause = "premature_event_record_wait"
            rec = ("collect EventRecord/EventWait timestamps before confirming the cause",)
            grade = "supported_hypothesis"
        else:
            cause = "insufficient_trace_evidence_for_event_attribution"
            rec = ("capture EventRecord/EventWait and producer/consumer timestamps",)
            grade = "observed"
        evidence = ("ACLGraph capture order is explicit; no GE Notify_Wait reorder inference"
                    if region.graph_backend == "aclgraph" else "legacy TorchAir/GE may reorder Notify_Wait")
        return Diagnostic("A2", "PREMATURE_EVENT_OR_PIECEWISE_JOIN", pct, span, wall, net,
                          cause, evidence, rec, (), grade, details)
    from .aclgraph_dag import peak_resources
    aic_sum, aiv_sum = peak_resources(dag)
    if aic_sum > region.aic_cores or aiv_sum > region.aiv_cores:
        hccl = [item for item in intervals if item.is_hccl and (item.io_bytes or item.read_bytes or item.write_bytes)]
        harmful = [item for item in hccl if item.hccl_expansion_mode == HcclExpansion.AIV.value]
        if harmful and aiv_sum > region.aiv_cores:
            return Diagnostic(
                "A3", "CORE_ENGINE_OVERSUBSCRIPTION", pct, span, wall, net,
                "hccl_aiv_expansion_steals_vector_cores",
                f"observed HCCL AIV expansion; aiv_sum={aiv_sum}/{region.aiv_cores}",
                ("set HCCL_OP_EXPANSION_MODE=CCU_SCHED on A5", "limit stream core num"),
                (), "supported_hypothesis",
                {**details, "aic_sum": aic_sum, "aiv_sum": aiv_sum},
            )
        return Diagnostic(
            "A3", "CORE_ENGINE_OVERSUBSCRIPTION", pct, span, wall, net,
            "cube_cube_or_aiv_aiv_wave_serialization",
            f"observed aic_sum={aic_sum}/{region.aic_cores} aiv_sum={aiv_sum}/{region.aiv_cores}",
            ("rebalance branch block dims", "serialize the weaker branch"),
            (), "observed", {**details, "aic_sum": aic_sum, "aiv_sum": aiv_sum},
        )
    if net <= 0.0:
        return Diagnostic(
            "A4", "MEMORY_CONTENTION_OR_SYNC_EROSION", pct, span, wall, net,
            "observed_overlap_eroded_by_stream_and_event_overhead",
            f"events={region.event_pairs} stream_to_stream={span:.4f}us",
            ("merge event pairs", "split the dominant branch"),
            (), "supported_hypothesis", details,
        )
    return Diagnostic("OK", "TRUE_OVERLAP", pct, span, wall, net, "overlap_holds",
                      "distinct streams, sufficient cores, non-negative net speedup",
                      (), (), "observed", details)


@dataclass(frozen=True, slots=True)
class SQBudget:
    captured_batch_sizes: int
    subgraphs_per_step: int
    active_streams_per_graph: int
    capacity: int = SQ_CQ_DEFAULT_CAPACITY
    mode: str = "piecewise"

    def __post_init__(self) -> None:
        for name in ("captured_batch_sizes", "subgraphs_per_step", "active_streams_per_graph"):
            object.__setattr__(self, name, _int(name, getattr(self, name)))
        object.__setattr__(self, "capacity", _int("capacity", self.capacity, minimum=1))
        object.__setattr__(self, "mode", str(self.mode).lower())
        if self.mode not in {item.value for item in GraphMode}:
            raise ACLGraphModelError(f"unknown graph mode: {self.mode!r}")

    @property
    def required(self) -> int:
        return self.captured_batch_sizes * self.subgraphs_per_step * self.active_streams_per_graph

    @property
    def fits(self) -> bool:
        return self.required <= self.capacity

    @property
    def error_code(self) -> str:
        return "" if self.fits else StreamResourceExhausted.error_code

    @property
    def recommendation(self) -> str:
        if self.fits:
            return "within_sq_cq_budget"
        if self.mode in ("piecewise", "full_and_piecewise"):
            return "prefer_full_or_full_decode_only"
        return "reduce_cudagraph_capture_sizes"

    def raise_if_exhausted(self) -> None:
        if not self.fits:
            raise StreamResourceExhausted(
                f"predicted ACLGraph capture failure 207008: need {self.required} "
                f"SQ/CQ entries, capacity {self.capacity}")


def check_capture_budget(captured_batch_sizes: int, subgraphs_per_step: int,
                         active_streams_per_graph: int, *, capacity: int = SQ_CQ_DEFAULT_CAPACITY,
                         mode: str = "piecewise") -> SQBudget:
    return SQBudget(captured_batch_sizes, subgraphs_per_step, active_streams_per_graph,
                    capacity, mode)


@dataclass(frozen=True, slots=True)
class SuperKernelEligibility:
    eligible: bool
    static_decode: bool
    capturable_ops: bool
    dynamic_tiling_host_sync: bool
    dcci_after_kernel_end: bool = True
    reason: str = ""

    def __post_init__(self) -> None:
        for name in ("eligible", "static_decode", "capturable_ops",
                     "dynamic_tiling_host_sync", "dcci_after_kernel_end"):
            if not isinstance(getattr(self, name), bool):
                raise ACLGraphModelError(f"{name} must be bool")

    @property
    def optimize_options(self) -> Mapping[str, list[str]]:
        return {"dcci_after_kernel_end": [DCCI_AFTER_KERNEL_END]} if self.eligible else {}


def check_superkernel_eligibility(static_decode: bool, capturable_ops: bool = True,
                                  dynamic_tiling_host_sync: bool = False) -> SuperKernelEligibility:
    for name, value in (("static_decode", static_decode), ("capturable_ops", capturable_ops),
                        ("dynamic_tiling_host_sync", dynamic_tiling_host_sync)):
        if not isinstance(value, bool):
            raise ACLGraphModelError(f"{name} must be bool")
    if not static_decode:
        reason = "dynamic prefill is not a static decode shape"
    elif not capturable_ops:
        reason = "non-capturable op in scope"
    elif dynamic_tiling_host_sync:
        reason = "dynamic tiling host sync is forbidden inside replay"
    else:
        reason = "static decode + capturable ops; dcci_after_kernel_end applies"
    return SuperKernelEligibility(static_decode and capturable_ops and not dynamic_tiling_host_sync,
                                  static_decode, capturable_ops, dynamic_tiling_host_sync, True, reason)


def effective_launch_floor_us(
    mode: str,
    *,
    superkernel: bool = False,
    config: ACLGraphLaunchConfig = DEFAULT_ACLGRAPH_LAUNCH_CONFIG,
) -> float:
    key = str(mode).strip().lower()
    if not isinstance(superkernel, bool):
        raise ACLGraphModelError("superkernel must be bool")
    aliases = {"aclgraph_full": "full", "aclgraph_piecewise": "piecewise", "aclgraph_superkernel": "superkernel"}
    key = aliases.get(key, key)
    mode_table = {
        "superkernel": config.superkernel_us,
        "full": config.full_graph_us,
        "full_decode_only": config.full_graph_us,
        "piecewise": config.piecewise_graph_us,
        "full_and_piecewise": config.piecewise_graph_us,
        "none": config.eager_us,
    }
    if key != "superkernel" and key not in {item.value for item in GraphMode}:
        raise ACLGraphModelError(f"unknown graph mode: {mode!r}")
    if superkernel:
        if key not in ("full", "full_decode_only", "superkernel"):
            raise ACLGraphModelError(f"superkernel requires a full-graph mode, got {mode!r}")
        return config.superkernel_us
    return mode_table.get(key, config.full_graph_us)


@dataclass(frozen=True, slots=True)
class ACLGraphWrapperModel:
    runtime_mode: str = "full"
    captured_batch_sizes: int = 1
    subgraphs_per_step: int = 1
    active_streams_per_graph: int = 1
    enable_enpu: bool = False
    use_eagle: bool = False
    enable_super_kernel: bool = False
    static_decode: bool = True
    capturable_ops: bool = True
    dynamic_tiling_host_sync: bool = False
    sq_capacity: int = SQ_CQ_DEFAULT_CAPACITY
    is_draft_model: bool = False

    def __post_init__(self) -> None:
        aliases = {"aclgraph_full": "full", "aclgraph_piecewise": "piecewise",
                   "aclgraph_superkernel": "superkernel", "none": "none"}
        runtime = self.runtime_mode.value if isinstance(self.runtime_mode, GraphMode) else str(self.runtime_mode)
        object.__setattr__(self, "runtime_mode", aliases.get(runtime.lower(), runtime.lower()))
        if self.runtime_mode not in {item.value for item in GraphMode}:
            raise ACLGraphModelError(f"unknown runtime mode: {self.runtime_mode!r}")
        for name in ("enable_enpu", "use_eagle", "is_draft_model", "enable_super_kernel",
                     "static_decode", "capturable_ops", "dynamic_tiling_host_sync"):
            if not isinstance(getattr(self, name), bool):
                raise ACLGraphModelError(f"{name} must be bool")
        for name in ("captured_batch_sizes", "subgraphs_per_step",
                     "active_streams_per_graph", "sq_capacity"):
            object.__setattr__(self, name, _int(name, getattr(self, name), minimum=1))

    @property
    def is_draft_eagle(self) -> bool:
        return self.is_draft_model and self.use_eagle

    @property
    def budget(self) -> SQBudget:
        return check_capture_budget(self.captured_batch_sizes, self.subgraphs_per_step,
                                    self.active_streams_per_graph, capacity=self.sq_capacity,
                                    mode=self.runtime_mode)

    @property
    def capture_budget(self) -> SQBudget:
        return self.budget

    @property
    def replay_sync_required(self) -> bool:
        return (self.runtime_mode in ("full", "full_decode_only")
                and not self.enable_enpu and not self.is_draft_eagle)

    @property
    def superkernel(self) -> SuperKernelEligibility:
        return check_superkernel_eligibility(static_decode=self.static_decode,
                                             capturable_ops=self.capturable_ops,
                                             dynamic_tiling_host_sync=self.dynamic_tiling_host_sync)

    @property
    def launch_floor_us(self) -> float:
        return effective_launch_floor_us(
            self.runtime_mode, superkernel=self.enable_super_kernel and self.superkernel.eligible)


@dataclass(frozen=True, slots=True)
class BreakableACLGraphWrapperModel:
    pieces: int = 1
    piece_break_us: float = 1.5
    force_join_at_boundary: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "pieces", _int("pieces", self.pieces, minimum=1))
        object.__setattr__(self, "piece_break_us", _num("piece_break_us", self.piece_break_us))
        if not isinstance(self.force_join_at_boundary, bool):
            raise ACLGraphModelError("force_join_at_boundary must be bool")

    @property
    def piece_join_overhead_us(self) -> float:
        return self.join_overhead_us

    @property
    def join_overhead_us(self) -> float:
        if not self.force_join_at_boundary:
            return 0.0
        return (self.pieces - 1) * self.piece_break_us


@dataclass(frozen=True, slots=True)
class UpdatableGraphModel:
    update_stream: bool = True
    enable_enpu: bool = False
    use_eagle: bool = False
    is_draft_model: bool = False

    def __post_init__(self) -> None:
        for name in ("update_stream", "enable_enpu", "use_eagle", "is_draft_model"):
            if not isinstance(getattr(self, name), bool):
                raise ACLGraphModelError(f"{name} must be bool")

    @property
    def is_draft_eagle(self) -> bool:
        return self.is_draft_model and self.use_eagle

    @property
    def sync_before_replay(self) -> bool:
        return not self.enable_enpu and not self.is_draft_eagle

    @property
    def needs_sync(self) -> bool:
        return self.sync_before_replay

    @property
    def update_before_replay(self) -> bool:
        return self.enable_enpu

    def replay_order(self) -> tuple[str, ...]:
        return ("update", "replay") if self.enable_enpu else ("replay", "update")


DIAGNOSTIC_CODES = {
    "A1": "SAME_STREAM_COLLAPSE", "A2": "PREMATURE_EVENT_OR_PIECEWISE_JOIN",
    "A3": "CORE_ENGINE_OVERSUBSCRIPTION", "A4": "MEMORY_CONTENTION_OR_SYNC_EROSION",
    "A5": "CAPTURE_DANGLING_STREAM_OR_POOL_HAZARD",
}


def diagnose_aclgraph_multistream(regions: Any) -> tuple[Diagnostic, ...]:
    if isinstance(regions, ParallelRegion):
        items = [regions]
    elif isinstance(regions, Mapping) and "regions" in regions:
        if set(regions) != {"regions"}:
            raise ACLGraphModelError("unknown region collection fields")
        items = list(regions["regions"])
    elif isinstance(regions, Mapping):
        items = [regions]
    else:
        items = list(regions)
    parsed = [item if isinstance(item, ParallelRegion) else ParallelRegion.from_mapping(item)
              for item in items]
    return tuple(diagnose_region(region) for region in parsed)


__all__ = [
    "ACLGraphModelError", "ACLGraphWrapperModel", "BreakableACLGraphWrapperModel",
    "CAPTURE_ERROR_CODE", "DCCI_AFTER_KERNEL_END", "DIAGNOSTIC_CODES", "Diagnostic",
    "EVENT_OVERHEAD_US", "GraphMode", "HcclExpansion", "OLD_HDK_CAPTURE_MARKER",
    "ParallelRegion", "SQBudget", "SQ_CQ_DEFAULT_CAPACITY", "STREAM_RESOURCE_MARKERS",
    "StreamInterval", "StreamResourceExhausted", "SuperKernelEligibility",
    "UpdatableGraphModel", "check_capture_budget", "check_superkernel_eligibility",
    "classify_capture_error", "diagnose_aclgraph_multistream", "diagnose_region",
    "effective_launch_floor_us",
]
