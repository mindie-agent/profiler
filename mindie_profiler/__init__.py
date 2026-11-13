"""MindIE profiler core: explicit-step Ascend DB/CSV accounting + C7 JSON.

[Role]
  Public package boundary for the compact profiler core.  Re-exports the
  analysis entry point, explicit window records, source-discovery helpers, and
  actionable error types.

[Invariants]
  * ``analyze_profile`` requires an explicit window or ``full_range=True``;
    no step is inferred from kernel rows.
  * The package exposes the C7 ``mindie-profile-summary/1`` dict as its
    cross-package interface; no external submodule is imported here.
  * Missing measurements are ``None``.

[Timeouts & Locks]
  Import-time only; bounded read budgets are owned by ``analyze`` and the
  source adapters.

[Side-Effect Policy]
  No I/O at import time and no network anywhere in this package.
"""

from __future__ import annotations

from .advisor_rules import (
    ADVISOR_SCHEMA,
    FUSION_PATTERN_RULES,
    FusionPatternRule,
    evaluate_advisor_rules,
    scan_aicpu_fallbacks,
    scan_alignment_and_mte_contention,
    scan_fusible_operator_sequences,
    scan_host_sync_and_gc_freezes,
)
from .analyze import analyze_profile
from .correlate import correlate_profile
from .cross_rank import (
    attribute_cluster_stragglers_and_links,
    cross_rank_stats,
    evaluate_ep_load_balance,
)
from .events import (
    PARSER_VERSION,
    REPORT_SCHEMA,
    Event,
    ProfilerError,
    ProfilerQueryError,
    ProfilerSchemaError,
    ProfilerUsageError,
    SourceRef,
    Window,
)
from .inventory import inventory_profile
from .memory_forensics import (
    MEMORY_FORENSICS_SCHEMA,
    analyze_memory_inefficiencies,
    detect_step_monotonic_leaks,
    run_memory_forensics,
)
from .native_capture import CAPTURE_SCHEMA, capture_profile, prepare_standby_session
from .native_capture_shm import mark_capture_step
from .sim_bridge import export_sim_case
from .structural_inference import (
    CANONICAL_L1_FAMILIES,
    STRUCTURAL_INFERENCE_SCHEMA,
    AgentDecisionItem,
    BodyTopologyInference,
    FrameworkEnvelopeInference,
    FusedCompositeInference,
    OperatorObservation,
    SpeculativeModuleInference,
    StructuralInferenceReport,
    classify_canonical_l1_family,
    infer_trace_structure,
)
from .segment import (
    discover_rank_sources,
    find_csv_candidates,
    find_db_candidates,
    find_trace_candidates,
    load_steps_file,
    parse_step_windows,
    parse_windows,
    resolve_ranks,
)
from .sources_trace import build_trace_index, iter_trace_events
from .sql import run_sql

__version__ = "0.5.11"
analyze = analyze_profile

__all__ = [
    "ADVISOR_SCHEMA",
    "CANONICAL_L1_FAMILIES",
    "CAPTURE_SCHEMA",
    "FUSION_PATTERN_RULES",
    "FusionPatternRule",
    "MEMORY_FORENSICS_SCHEMA",
    "PARSER_VERSION",
    "REPORT_SCHEMA",
    "STRUCTURAL_INFERENCE_SCHEMA",
    "AgentDecisionItem",
    "BodyTopologyInference",
    "Event",
    "FrameworkEnvelopeInference",
    "FusedCompositeInference",
    "OperatorObservation",
    "ProfilerError",
    "ProfilerQueryError",
    "ProfilerSchemaError",
    "ProfilerUsageError",
    "SourceRef",
    "SpeculativeModuleInference",
    "StructuralInferenceReport",
    "Window",
    "analyze",
    "analyze_memory_inefficiencies",
    "analyze_profile",
    "attribute_cluster_stragglers_and_links",
    "build_trace_index",
    "capture_profile",
    "classify_canonical_l1_family",
    "correlate_profile",
    "cross_rank_stats",
    "detect_step_monotonic_leaks",
    "discover_rank_sources",
    "evaluate_advisor_rules",
    "evaluate_ep_load_balance",
    "export_sim_case",
    "find_csv_candidates",
    "find_db_candidates",
    "find_trace_candidates",
    "infer_trace_structure",
    "inventory_profile",
    "iter_trace_events",
    "load_steps_file",
    "mark_capture_step",
    "parse_step_windows",
    "parse_windows",
    "prepare_standby_session",
    "resolve_ranks",
    "run_memory_forensics",
    "run_sql",
    "scan_aicpu_fallbacks",
    "scan_alignment_and_mte_contention",
    "scan_fusible_operator_sequences",
    "scan_host_sync_and_gc_freezes",
    "__version__",
]
