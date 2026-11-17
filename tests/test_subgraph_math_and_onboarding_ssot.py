"""SSOT shims, live identity resolution and shared subgraph math in the profiler.

[Role]
  Prove that the profiler owns no shadow catalog or contract copy, that model
  resolution comes from ``mindie_sim`` with separate provenance, that unmodeled
  operators produce the single-onboarding-point hint, and that exported
  subgraph math is evaluated by the shared ``mindie_sim.subgraph_math``.

[Invariants]
  * Contract modules forward the exact simulator objects; no local rule copy.
  * Unknown checkpoints raise; aliases resolve to live catalog keys.
  * Boundary/algebraic metrics stay ``None`` when the explicit ledger is absent.
  * Hints name ``mindie-sim`` as the only onboarding owner.

[Timeouts & Locks]
  Two-layer in-memory exports only; no device, waits or locks.

[Side-Effect Policy]
  Read-only in-memory construction; no filesystem writes.
"""
from __future__ import annotations

import pytest

from mindie_sim.compose import compose_case
from mindie_sim.structure import export_structure


def _structure():
    case = compose_case(
        "deepseek-v3.2", "a3", tp=8, prompt_tokens=64, output_tokens=4, layers=2)
    structure = export_structure(
        case, phase="prefill", tokens=64, context=0, sequences=1, scope="body")
    return case, structure


def test_contract_modules_are_lazy_forwarding_shims():
    import mindie_sim.observed_contracts.attention_contracts as attention
    import mindie_sim.observed_contracts.tensor_contracts as tensor
    import mindie_sim.observed_contracts.vocabulary as vocabulary
    from mindie_profiler import (
        body_attention_contracts, structure_diagnostics, tensor_contracts,
    )

    assert body_attention_contracts.ATTENTION_CACHE_TYPES is (
        attention.ATTENTION_CACHE_TYPES)
    assert body_attention_contracts.MQSMLA_KINDS == attention.MQSMLA_KINDS
    assert tensor_contracts.observed_contract is tensor.observed_contract
    assert structure_diagnostics.FIELDS is vocabulary.FIELDS
    # The five previously drifted families are present in the shared vocabulary.
    assert {
        "attention_paged_active_qkv", "attention_paged_mla_qk_rope",
        "situ_mxquant_active", "dynamic_quant_v2_active", "causal_conv1d_active",
    } <= set(structure_diagnostics.FIELDS)


def test_catalog_and_hardware_own_no_shadow_tables():
    from mindie_profiler import sim_bridge_catalog as catalog

    for name in ("_GEOMETRY", "_GENERIC", "_MAX_POS", "_SKUS", "_HARDWARE",
                 "_MODEL_PATTERNS", "_fallback_model"):
        assert not hasattr(catalog, name), name
    from mindie_profiler import hardware_presets

    assert not hasattr(hardware_presets, "_STATIC")
    assert "_STATIC" not in hardware_presets.__dict__
    # Live profile keys, not an import-time mirror.
    assert "Ascend950DT_9582" in catalog.supported_hardware_skus()


def test_model_resolution_alias_and_provenance_are_separate():
    from mindie_profiler.sim_bridge_catalog import resolve_sim_model_key

    assert resolve_sim_model_key("qwen3-30b") == "qwen3-30b-a3b"
    assert resolve_sim_model_key("qwen3.8-2.4t") == "qwen3.8-2.4t-a95b"
    assert resolve_sim_model_key("deepseek-v4-flash") == "deepseek-v4-flash-0731"
    assert resolve_sim_model_key("synth-qwen3-30b-l8-e16-k2") == "qwen3-30b-a3b"
    with pytest.raises(Exception, match="unsupported or unrecognized model"):
        resolve_sim_model_key("Qwen3-8B")


def test_unmodeled_operator_hint_names_the_single_owner():
    from mindie_profiler.sim_structure_ingress import onboarding_hints_from_sample

    sample = [{
        "status": "unmatched_observed",
        "operator_type": "CustomFlashDecoderV4",
        "kernel_name": "aclnnCustomFlashDecoderV4",
        "native_abi": ("native_tensor_abi", "CustomFlashDecoderV4",
                       [((3, 4, 4, 2), "bf16", "ND")], [((3,), "bf16", "ND")]),
    }, {
        "status": "bound", "operator_type": "MatMul", "kernel_name": "aclnnMatMul",
    }]
    hints = onboarding_hints_from_sample(sample)
    assert len(hints) == 1
    hint = hints[0]
    assert hint["schema"] == "mindie-unmodeled-structure-hint/1"
    assert hint["ssot_owner_repo"] == "mindie-sim"
    assert hint["inferred_subgraph_candidate"] == "attention"
    assert "mindie_sim/subgraph_math.py" in hint["onboarding_targets"]
    assert "Do NOT add local operator/subgraph contract rules" in hint["agent_directive"]
    assert hint["observed_abi_summary"]["input_ranks"] == [4]


def test_exported_subgraph_math_is_evaluated_by_the_shared_function():
    from mindie_profiler.sim_structure_ingress import subgraph_efficiency_summary

    case, structure = _structure()
    group = next(group for group in structure["subgraphs"]
                 if group.get("math_summary"))
    mapping = {"windows": [{"cohorts": [{
        "target_ids": [group["subgraph_id"]],
        "busy_union_ns": 2_000_000.0,
        "complete_event_count": 2,
    }]}]}
    summary = subgraph_efficiency_summary(structure, mapping, case_doc=case)
    assert summary["schema"] == "mindie-profiler-subgraph-efficiency/1"
    assert summary["status"] == "evaluated"
    record = next(row for row in summary["records"]
                  if row["subgraph_id"] == group["subgraph_id"])
    assert record["status"] == "evaluated"
    assert record["invocations"] == 2
    assert record["metrics"]["realized_mbu"] is not None
    # No explicit boundary access ledger exists yet: never an invented zero.
    assert record["metrics"]["minimal_boundary_mbu"] is None
    assert record["metrics"]["algebraic_cube_mfu"] is None
    assert record["metrics"]["fusion_headroom_bytes"] is None


def test_mapping_reports_onboarding_hints_without_observations():
    from mindie_profiler.structure_mapping import map_structure

    _case, structure = _structure()
    mapping = map_structure([], structure)
    assert mapping["unmodeled_structure_onboarding_hints"] == []
    assert mapping["status"] == "unresolved"
