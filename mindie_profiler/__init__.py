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

import importlib
from typing import Any

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

__version__ = "0.5.14"

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "ADVISOR_SCHEMA": (".advisor_rules", "ADVISOR_SCHEMA"),
    "FUSION_PATTERN_RULES": (".advisor_rules", "FUSION_PATTERN_RULES"),
    "FusionPatternRule": (".advisor_rules", "FusionPatternRule"),
    "evaluate_advisor_rules": (".advisor_rules", "evaluate_advisor_rules"),
    "scan_aicpu_fallbacks": (".advisor_rules", "scan_aicpu_fallbacks"),
    "scan_alignment_and_mte_contention": (".advisor_rules", "scan_alignment_and_mte_contention"),
    "scan_fusible_operator_sequences": (".advisor_rules", "scan_fusible_operator_sequences"),
    "scan_host_sync_and_gc_freezes": (".advisor_rules", "scan_host_sync_and_gc_freezes"),
    "analyze": (".analyze", "analyze_profile"),
    "analyze_profile": (".analyze", "analyze_profile"),
    "read_collective_readiness": (".collective_readiness", "read_collective_readiness"),
    "correlate_profile": (".correlate", "correlate_profile"),
    "attribute_cluster_stragglers_and_links": (".cross_rank", "attribute_cluster_stragglers_and_links"),
    "cross_rank_stats": (".cross_rank", "cross_rank_stats"),
    "evaluate_ep_load_balance": (".cross_rank", "evaluate_ep_load_balance"),
    "inventory_profile": (".inventory", "inventory_profile"),
    "MEMORY_FORENSICS_SCHEMA": (".memory_forensics", "MEMORY_FORENSICS_SCHEMA"),
    "analyze_memory_inefficiencies": (".memory_forensics", "analyze_memory_inefficiencies"),
    "detect_step_monotonic_leaks": (".memory_forensics", "detect_step_monotonic_leaks"),
    "run_memory_forensics": (".memory_forensics", "run_memory_forensics"),
    "CAPTURE_SCHEMA": (".native_capture", "CAPTURE_SCHEMA"),
    "capture_profile": (".native_capture", "capture_profile"),
    "prepare_standby_session": (".native_capture", "prepare_standby_session"),
    "mark_capture_step": (".native_capture_shm", "mark_capture_step"),
    "call_tool": (".aclgraph_mcp", "call_tool"),
    "ACLGraphModelError": (".aclgraph_multistream", "ACLGraphModelError"),
    "ACLGraphWrapperModel": (".aclgraph_multistream", "ACLGraphWrapperModel"),
    "BreakableACLGraphWrapperModel": (".aclgraph_multistream", "BreakableACLGraphWrapperModel"),
    "CAPTURE_ERROR_CODE": (".aclgraph_multistream", "CAPTURE_ERROR_CODE"),
    "DIAGNOSTIC_CODES": (".aclgraph_multistream", "DIAGNOSTIC_CODES"),
    "Diagnostic": (".aclgraph_multistream", "Diagnostic"),
    "GraphMode": (".aclgraph_multistream", "GraphMode"),
    "HcclExpansion": (".aclgraph_multistream", "HcclExpansion"),
    "OLD_HDK_CAPTURE_MARKER": (".aclgraph_multistream", "OLD_HDK_CAPTURE_MARKER"),
    "ParallelRegion": (".aclgraph_multistream", "ParallelRegion"),
    "SQBudget": (".aclgraph_multistream", "SQBudget"),
    "STREAM_RESOURCE_MARKERS": (".aclgraph_multistream", "STREAM_RESOURCE_MARKERS"),
    "StreamInterval": (".aclgraph_multistream", "StreamInterval"),
    "StreamResourceExhausted": (".aclgraph_multistream", "StreamResourceExhausted"),
    "SuperKernelEligibility": (".aclgraph_multistream", "SuperKernelEligibility"),
    "UpdatableGraphModel": (".aclgraph_multistream", "UpdatableGraphModel"),
    "check_capture_budget": (".aclgraph_multistream", "check_capture_budget"),
    "check_superkernel_eligibility": (".aclgraph_multistream", "check_superkernel_eligibility"),
    "classify_capture_error": (".aclgraph_multistream", "classify_capture_error"),
    "diagnose_aclgraph_multistream": (".aclgraph_multistream", "diagnose_aclgraph_multistream"),
    "diagnose_region": (".aclgraph_multistream", "diagnose_region"),
    "effective_launch_floor_us": (".aclgraph_multistream", "effective_launch_floor_us"),
    "build_fabric_probe_plan": (".fabric_probe", "build_fabric_probe_plan"),
    "fit_calibrated_fabric_profile": (".fabric_probe", "fit_calibrated_fabric_profile"),
    "bind_captured_occurrence": (".op_api_registry", "bind_captured_occurrence"),
    "inspect_op_abi": (".op_api_registry", "inspect_op_abi"),
    "ACLGraphLaunchConfig": (".profiler_configs", "ACLGraphLaunchConfig"),
    "AdvisorConfig": (".profiler_configs", "AdvisorConfig"),
    "CorrelationConfig": (".profiler_configs", "CorrelationConfig"),
    "FusionRuleConfig": (".profiler_configs", "FusionRuleConfig"),
    "MemoryForensicsConfig": (".profiler_configs", "MemoryForensicsConfig"),
    "SimBridgeBottleneckPolicy": (".profiler_configs", "SimBridgeBottleneckPolicy"),
    "StructuralInferenceConfig": (".profiler_configs", "StructuralInferenceConfig"),
    "generate_single_op_reproducer": (".repro_op", "generate_single_op_reproducer"),
    "export_sim_case": (".sim_bridge", "export_sim_case"),
    "CANONICAL_L1_FAMILIES": (".structural_inference", "CANONICAL_L1_FAMILIES"),
    "STRUCTURAL_INFERENCE_SCHEMA": (".structural_inference", "STRUCTURAL_INFERENCE_SCHEMA"),
    "AgentDecisionItem": (".structural_inference", "AgentDecisionItem"),
    "BodyTopologyInference": (".structural_inference", "BodyTopologyInference"),
    "FrameworkEnvelopeInference": (".structural_inference", "FrameworkEnvelopeInference"),
    "FusedCompositeInference": (".structural_inference", "FusedCompositeInference"),
    "OperatorObservation": (".structural_inference", "OperatorObservation"),
    "SpeculativeModuleInference": (".structural_inference", "SpeculativeModuleInference"),
    "StructuralInferenceReport": (".structural_inference", "StructuralInferenceReport"),
    "classify_canonical_l1_family": (".structural_inference", "classify_canonical_l1_family"),
    "infer_trace_structure": (".structural_inference", "infer_trace_structure"),
    "discover_rank_sources": (".segment", "discover_rank_sources"),
    "find_csv_candidates": (".segment", "find_csv_candidates"),
    "find_db_candidates": (".segment", "find_db_candidates"),
    "find_trace_candidates": (".segment", "find_trace_candidates"),
    "load_steps_file": (".segment", "load_steps_file"),
    "parse_step_windows": (".segment", "parse_step_windows"),
    "parse_windows": (".segment", "parse_windows"),
    "resolve_ranks": (".segment", "resolve_ranks"),
    "build_trace_index": (".sources_trace", "build_trace_index"),
    "iter_trace_events": (".sources_trace", "iter_trace_events"),
    "run_sql": (".sql", "run_sql"),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_EXPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        value = getattr(importlib.import_module(mod_name, __name__), attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

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
    "ACLGraphLaunchConfig",
    "ACLGraphModelError",
    "ACLGraphWrapperModel",
    "AdvisorConfig",
    "BreakableACLGraphWrapperModel",
    "CAPTURE_ERROR_CODE",
    "CorrelationConfig",
    "DIAGNOSTIC_CODES",
    "Diagnostic",
    "FusionRuleConfig",
    "GraphMode",
    "HcclExpansion",
    "MemoryForensicsConfig",
    "OLD_HDK_CAPTURE_MARKER",
    "ParallelRegion",
    "SQBudget",
    "STREAM_RESOURCE_MARKERS",
    "SimBridgeBottleneckPolicy",
    "StreamInterval",
    "StreamResourceExhausted",
    "StructuralInferenceConfig",
    "SuperKernelEligibility",
    "UpdatableGraphModel",
    "bind_captured_occurrence",
    "build_fabric_probe_plan",
    "call_tool",
    "check_capture_budget",
    "check_superkernel_eligibility",
    "classify_capture_error",
    "diagnose_aclgraph_multistream",
    "diagnose_region",
    "effective_launch_floor_us",
    "fit_calibrated_fabric_profile",
    "generate_single_op_reproducer",
    "inspect_op_abi",
    "__version__",
]
