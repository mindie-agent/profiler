"""Immutable configuration and diagnostic policy schemas for MindIE Profiler.

[Role]
  Centralizes typed, validated configuration dataclasses for Host-Device
  correlation, Ascend Advisor rule thresholds, memory forensics, bottom-up
  structural inference, ACLGraph launch/overlap diagnostics, and simulator
  bridge bottleneck classification.

[Invariants]
  * Every count, byte, step, and microsecond integer field rejects ``bool``.
  * Every ratio, event rate, and fractional latency field requires a finite
    ``float`` and validates domain bounds at construction time.
  * Configuration defaults preserve deterministic diagnostic behavior; they
    represent explicit diagnostic policies rather than universal hardware laws.

[Timeouts & Locks]
  Pure in-memory validation at dataclass construction; no locks or I/O.

[Side-Effect Policy]
  Side-effect-free immutable value types.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_MAX_PERCENT = 1.0 * 100


def _req_int(name: str, value: int, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be int, got {type(value).__name__}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


def _req_float(
    name: str,
    value: float | int,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be float, got {type(value).__name__}")
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} must be finite, got {value!r}")
    if minimum is not None and out < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {out}")
    if maximum is not None and out > maximum:
        raise ValueError(f"{name} must be <= {maximum}, got {out}")
    return out


@dataclass(frozen=True, slots=True)
class CorrelationConfig:
    """Row budgets, SQL chunking, and deadline policy for Host-Device correlation."""

    max_rows: int = 5000
    max_name_rows: int = 5000
    max_task_occurrences: int = 2000
    sql_batch_ids: int = 500
    max_stack_depth: int = 8
    max_calls: int = 200
    query_timeout_us: int = 20_000_000
    min_query_timeout_us: int = 100_000
    progress_interval_opcodes: int = 20_000

    def __post_init__(self) -> None:
        for field_name in (
            "max_rows", "max_name_rows", "max_task_occurrences", "sql_batch_ids",
            "max_stack_depth", "max_calls", "query_timeout_us",
            "min_query_timeout_us", "progress_interval_opcodes",
        ):
            _req_int(field_name, getattr(self, field_name), minimum=1)
        if self.query_timeout_us < self.min_query_timeout_us:
            raise ValueError("query_timeout_us must be >= min_query_timeout_us")


@dataclass(frozen=True, slots=True)
class AdvisorConfig:
    """Thresholds and declared layout granules for Ascend Advisor diagnostics."""

    cast_storm_min_count: int = 4
    cast_storm_share_ratio: float = 0.15
    cast_high_severity_ratio: float = 0.25
    mte2_contention_ratio: float = 0.35
    gc_gap_us: int = 10_000
    gc_high_severity_us: int = 20_000
    sync_co_occurrence_ratio: float = 0.80
    max_inter_kernel_gap_us: int = 5_000
    acl_idle_busy_ratio: float = 0.01
    acl_idle_events_per_us: float = 0.0001
    ub_burst_bytes: int = 32
    hbm_burst_bytes: int = 512
    cube_fractal_tile: int = 16
    cube_inner_tile: int = 256
    fa_head_dim_multiple: int = 16

    def __post_init__(self) -> None:
        for field_name in (
            "cast_storm_min_count", "gc_gap_us", "gc_high_severity_us",
            "max_inter_kernel_gap_us", "ub_burst_bytes", "hbm_burst_bytes",
            "cube_fractal_tile", "cube_inner_tile", "fa_head_dim_multiple",
        ):
            _req_int(field_name, getattr(self, field_name), minimum=1)
        for ratio_name in (
            "cast_storm_share_ratio", "cast_high_severity_ratio",
            "mte2_contention_ratio", "sync_co_occurrence_ratio", "acl_idle_busy_ratio",
        ):
            _req_float(ratio_name, getattr(self, ratio_name), minimum=0.0, maximum=1.0)
        _req_float("acl_idle_events_per_us", self.acl_idle_events_per_us, minimum=0.0)
        if self.gc_high_severity_us < self.gc_gap_us:
            raise ValueError("gc_high_severity_us must be >= gc_gap_us")
        if self.cast_high_severity_ratio < self.cast_storm_share_ratio:
            raise ValueError("cast_high_severity_ratio must be >= cast_storm_share_ratio")


@dataclass(frozen=True, slots=True)
class FusionRuleConfig:
    """Non-causal candidate savings bounds for operator fusion pattern rules."""

    default_savings_ratio: float = 0.50
    min_savings_ratio: float = 0.40
    max_savings_ratio: float = 0.80

    def __post_init__(self) -> None:
        _req_float("default_savings_ratio", self.default_savings_ratio, minimum=0.0, maximum=1.0)
        _req_float("min_savings_ratio", self.min_savings_ratio, minimum=0.0, maximum=1.0)
        _req_float("max_savings_ratio", self.max_savings_ratio, minimum=0.0, maximum=1.0)
        if not (self.min_savings_ratio <= self.default_savings_ratio <= self.max_savings_ratio):
            raise ValueError(
                "savings ratios must satisfy min_savings_ratio <= default_savings_ratio <= max_savings_ratio"
            )


@dataclass(frozen=True, slots=True)
class MemoryForensicsConfig:
    """Temporal, fragmentation, and step-leak thresholds for memory forensics."""

    min_api_gap_count: int = 10
    idle_api_gap_count: int = 3000
    early_alloc_us: int = 2000
    late_free_us: int = 2000
    idle_gap_us: int = 10_000
    early_alloc_ratio: float = 0.30
    late_free_ratio: float = 0.30
    spike_ratio: float = 0.15
    high_fragmentation_ratio: float = 0.15
    moderate_fragmentation_ratio: float = 0.05
    min_post_warmup_steps: int = 3
    min_leak_bytes: int = 1_048_576
    positive_step_transition_ratio: float = 0.80

    def __post_init__(self) -> None:
        for field_name in (
            "min_api_gap_count", "idle_api_gap_count", "early_alloc_us",
            "late_free_us", "idle_gap_us", "min_post_warmup_steps", "min_leak_bytes",
        ):
            _req_int(field_name, getattr(self, field_name), minimum=1)
        for ratio_name in (
            "early_alloc_ratio", "late_free_ratio", "spike_ratio",
            "high_fragmentation_ratio", "moderate_fragmentation_ratio",
            "positive_step_transition_ratio",
        ):
            _req_float(ratio_name, getattr(self, ratio_name), minimum=0.0, maximum=1.0)
        if self.high_fragmentation_ratio < self.moderate_fragmentation_ratio:
            raise ValueError("high_fragmentation_ratio must be >= moderate_fragmentation_ratio")
        if self.idle_api_gap_count < self.min_api_gap_count:
            raise ValueError("idle_api_gap_count must be >= min_api_gap_count")


@dataclass(frozen=True, slots=True)
class StructuralInferenceConfig:
    """Candidate bounds and periodicity tolerances for trace structural inference."""

    max_candidate_steps: int = 512
    gap_median_multiple: float = 8.0
    min_positive_gaps: int = 3
    candidate_step_upper_bound: int = 255
    min_layer_candidates: int = 20
    max_layer_candidates: int = 120
    secondary_split_max_layers: int = 96
    call_count_tolerance: float = 0.51
    min_family_coverage_ratio: float = 0.25
    max_draft_fraction_ratio: float = 0.25
    unknown_moe_min_share_ratio: float = 0.05
    high_confidence_min_layers: int = 8

    def __post_init__(self) -> None:
        for field_name in (
            "max_candidate_steps", "min_positive_gaps", "candidate_step_upper_bound",
            "min_layer_candidates", "max_layer_candidates",
            "secondary_split_max_layers", "high_confidence_min_layers",
        ):
            _req_int(field_name, getattr(self, field_name), minimum=1)
        _req_float("gap_median_multiple", self.gap_median_multiple, minimum=1.0)
        _req_float("call_count_tolerance", self.call_count_tolerance, minimum=0.0)
        for ratio_name in (
            "min_family_coverage_ratio", "max_draft_fraction_ratio", "unknown_moe_min_share_ratio",
        ):
            _req_float(ratio_name, getattr(self, ratio_name), minimum=0.0, maximum=1.0)
        if self.max_layer_candidates < self.min_layer_candidates:
            raise ValueError("max_layer_candidates must be >= min_layer_candidates")
        if self.max_candidate_steps < self.candidate_step_upper_bound:
            raise ValueError("max_candidate_steps must be >= candidate_step_upper_bound")


@dataclass(frozen=True, slots=True)
class ACLGraphLaunchConfig:
    """Reference dispatch/replay service times and queue capacity for ACLGraph models."""

    superkernel_us: float = 0.32
    full_graph_us: float = 1.35
    piecewise_graph_us: float = 1.6
    eager_us: float = 5.0
    event_sync_us: float = 1.5
    overlap_serial_pct: float = 5.0
    sq_cq_stream_capacity: int = 2048
    max_dag_nodes: int = 10_000
    max_dag_edges: int = 100_000

    def __post_init__(self) -> None:
        for field_name in (
            "superkernel_us", "full_graph_us", "piecewise_graph_us",
            "eager_us", "event_sync_us",
        ):
            _req_float(field_name, getattr(self, field_name), minimum=0.0)
        _req_float("overlap_serial_pct", self.overlap_serial_pct, minimum=0.0, maximum=_MAX_PERCENT)
        for int_name in ("sq_cq_stream_capacity", "max_dag_nodes", "max_dag_edges"):
            _req_int(int_name, getattr(self, int_name), minimum=1)


@dataclass(frozen=True, slots=True)
class SimBridgeBottleneckPolicy:
    """Diagnostic share thresholds for non-causal observed bottleneck summaries."""

    comm_share_ratio: float = 0.35
    launch_share_ratio: float = 0.30
    memory_share_ratio: float = 0.85
    percent_scale_cutoff: float = 1.5
    max_top_operators: int = 10

    def __post_init__(self) -> None:
        for ratio_name in ("comm_share_ratio", "launch_share_ratio", "memory_share_ratio"):
            _req_float(ratio_name, getattr(self, ratio_name), minimum=0.0, maximum=1.0)
        _req_float("percent_scale_cutoff", self.percent_scale_cutoff, minimum=1.0)
        _req_int("max_top_operators", self.max_top_operators, minimum=1)


DEFAULT_CORRELATION_CONFIG = CorrelationConfig()
DEFAULT_ADVISOR_CONFIG = AdvisorConfig()
DEFAULT_FUSION_RULE_CONFIG = FusionRuleConfig()
DEFAULT_MEMORY_FORENSICS_CONFIG = MemoryForensicsConfig()
DEFAULT_STRUCTURAL_INFERENCE_CONFIG = StructuralInferenceConfig()
DEFAULT_ACLGRAPH_LAUNCH_CONFIG = ACLGraphLaunchConfig()
DEFAULT_SIM_BRIDGE_POLICY = SimBridgeBottleneckPolicy()

__all__ = [
    "ACLGraphLaunchConfig",
    "AdvisorConfig",
    "CorrelationConfig",
    "DEFAULT_ACLGRAPH_LAUNCH_CONFIG",
    "DEFAULT_ADVISOR_CONFIG",
    "DEFAULT_CORRELATION_CONFIG",
    "DEFAULT_FUSION_RULE_CONFIG",
    "DEFAULT_MEMORY_FORENSICS_CONFIG",
    "DEFAULT_SIM_BRIDGE_POLICY",
    "DEFAULT_STRUCTURAL_INFERENCE_CONFIG",
    "FusionRuleConfig",
    "MemoryForensicsConfig",
    "SimBridgeBottleneckPolicy",
    "StructuralInferenceConfig",
]
