"""Retained native kernels validate caller selection and valid/capacity rows.

[Role] Exercise eight local boundaries on the entire held-out 192K context.
[Invariants] Native means set responses; Body timings do not. Missing source
  conditions, ALLGATHER callers and explicit conflicts retain the full input.
[Timeouts & Locks] Local target graphs and packaged captures; no waits.
[Side-Effect Policy] Runtime homes are isolated by the repository conftest.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import graph_costs, target_operators
from mindie_sim.prediction.structure import parse_case

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from a5_q35_unfused_native_observations import PROFILE_PATH, apply_a5_q35_unfused_native_observations
from a5_mtp_native_observations import apply_a5_mtp_native_observations


def retained():
    path = ROOT / "tests/fixtures/native_observations/a5_qwen35_unfused_q4_b7.json"
    return json.loads(path.read_text())


def options():
    return {"phase": "decode", "tokens": 4, "context": 196608, "sequences": 7}


def test_held_context_native_means_execute_on_valid_rows_and_physical_capacity():
    fixture = retained()
    raw = fixture["raw_case"]
    original = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "applied" and len(provenance["matched_domains"]) == 8
    assert all(row["occurrences"] == 40 for row in provenance["matched_domains"])
    assert raw == original and not provenance["observations_modified"]
    old_rules = raw["runtime"]["kernels"]["service_regimes"]
    retained_rules = [rule for rule in old_rules if rule["id"] not in provenance["replaced_rule_ids"]]
    assert result["runtime"]["kernels"]["service_regimes"][:len(retained_rules)] == retained_rules
    profile = json.loads(PROFILE_PATH.read_text())
    held = {row["recipe"]: row for row in profile["validation"]
            if row["id"] == fixture["source_case_id"] and row["active_query_rows"] == 28}
    assert len(held) == 8
    seen = set()
    for op in target_operators(result, **options()):
        if op.recipe not in held or op.recipe in seen:
            continue
        if op.recipe == "dynamic_quantize" and "mc2_unfused_storage" not in dict(op.metadata):
            continue
        seen.add(op.recipe)
        actual = held[op.recipe]
        isolated = graph_costs(result, (op,), isolated=False,
                               external_inputs={dependency: 0 for dependency in op.deps})
        prediction = isolated["duration_ms"] * 1000
        assert prediction == pytest.approx(actual["predicted_native_mean_us"])
        assert abs(prediction / actual["mean_us"] - 1) < 0.03
        assert fixture["source_case_id"] not in actual["training_source_ids"]
        metadata = dict(op.metadata)
        assert metadata["graph_active_query_rows"] == 28
        assert metadata["graph_physical_query_rows"] == 32
        if op.recipe in {"balanced_grouped_gate_up", "balanced_grouped_down"}:
            assert op.local_shape[0] == 56 and op.padded_shape[0] == 256
            assert sum(metadata["matrix_group_rows"]) == 56
        if op.recipe in {"grouped_swiglu", "dynamic_quantize"}:
            assert op.local_shape == (56, 512) and op.padded_shape == (256, 512)
    assert seen == held.keys()
    again, provenance = apply_a5_q35_unfused_native_observations(result, **options())
    assert provenance["status"] == "applied" and result == again


def test_independent_queue_keeps_existing_attention_and_recurrence_responses():
    raw, _ = apply_a5_mtp_native_observations(retained()["raw_case"], **options())
    old = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "applied" and raw == old
    assert len(provenance["added_queue_guard_rule_ids"]) == 2
    previous = {rule["id"]: rule for rule in old["runtime"]["kernels"]["service_regimes"]}
    for rule in result["runtime"]["kernels"]["service_regimes"]:
        if rule["id"] not in provenance["added_queue_guard_rule_ids"]:
            continue
        assert rule["response"] == previous[rule["id"]]["response"]
        for op in target_operators(result, **options()):
            if op.recipe == rule["match"]["recipe"]:
                cost = graph_costs(result, (op,), isolated=False,
                                   external_inputs={dependency: 0 for dependency in op.deps})
                original = graph_costs(old, (op,), isolated=False,
                                       external_inputs={dependency: 0 for dependency in op.deps})
                assert cost["duration_ms"] == pytest.approx(original["duration_ms"])
                break


@pytest.mark.parametrize("condition", (
    "q1", "allgather_q64", "missing_literal", "fusion_enabled", "force_eplb_disabled",
    "explicit_caller", "explicit_mask", "explicit_router", "rates", "capacity", "model_geometry",
    "routing", "moe_recipe", "sequence_parallel",
))
def test_unobserved_or_conflicting_callers_preserve_the_complete_input(condition):
    raw, geometry = retained()["raw_case"], options()
    runtime, model = raw["runtime"], raw["model"]
    kernels = runtime["kernels"]
    if condition == "q1":
        geometry.update(tokens=1, sequences=28)
    elif condition == "allgather_q64":
        geometry["sequences"] = 16
    elif condition == "missing_literal":
        runtime["metadata"].pop("captured_additional_config")
    elif condition == "fusion_enabled":
        runtime["metadata"]["captured_additional_config"]["ascend_fusion_config"]["fusion_ops_gmmswigluquant"] = True
    elif condition == "force_eplb_disabled":
        runtime["metadata"]["captured_additional_config"]["enable_force_eplb"] = False
    elif condition == "explicit_caller":
        kernels["lowerings"]["grouped_int8_caller"] = {"implementation": "int32_unselected", "options": {}}
    elif condition == "explicit_mask":
        kernels["force_eplb_source"] = {"kind": "vllm_ascend_mc2_tp", "global_bs": 32}
    elif condition == "explicit_router":
        model["layer_overrides"] = {"0": {"router_dtype": "bf16"}}
    elif condition == "rates":
        raw["machine"]["device"].setdefault("rates", {})["hbm"] = 1e6
    elif condition == "capacity":
        runtime["graph_capture_keys"] = runtime["graph_buckets"] = [64]
    elif condition == "routing":
        runtime["routing"] = {"policy": "expected"}
    elif condition == "moe_recipe":
        runtime["moe_recipe"] = "mc2"
    elif condition == "sequence_parallel":
        kernels["sequence_parallel"] = True
    else:
        model["layer_overrides"] = {"0": {"num_experts": 128}}
    original = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **geometry)
    assert provenance["status"] == "not_applicable"
    assert raw == result == original


@pytest.mark.parametrize("match", ({"recipe": "dynamic_quantize", "phase": "decode"}, {"phase": "decode"}))
def test_broad_existing_response_is_not_deleted_for_other_native_calls(match):
    raw = retained()["raw_case"]
    raw["runtime"]["kernels"]["service_regimes"].append({
        "id": "all-existing-operators", "match": match, "response": {"fixed_us": 1},
    })
    original = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["reason"] == "existing_response_spans_observed_and_other_native_boundaries"
    assert result == raw == original


def test_old_response_with_missing_coordinate_remains_unchanged():
    raw = retained()["raw_case"]
    old = {"id": "external-unavailable-coordinate", "match": {"recipe": "router"},
           "coordinates": {"x": {"path": "metadata.external_axis"}},
           "domain": {"x": {"max": 1}}, "response": {"fixed_us": 1}}
    raw["runtime"]["kernels"]["service_regimes"].append(deepcopy(old))
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "applied"
    assert old in result["runtime"]["kernels"]["service_regimes"]


@pytest.mark.parametrize("override", (
    {"device": {"rates": {"native_call_service": 2e9}}, "devices": [{}, {}, {}, {}]},
    {"dies": [{"rates": {"native_call_service": 2e9}}] * 4},
    {"device": {"work_units": {"native_call_service": "cycles"}}},
    {"devices": [{}, {}, {"resource_units": {"native_call_service": 2}}, {}]},
))
def test_normalized_per_die_queue_conflicts_are_preserved(override):
    raw = retained()["raw_case"]
    for name, value in override.items():
        if name == "device":
            raw["machine"].setdefault(name, {}).update(deepcopy(value))
        else:
            raw["machine"][name] = deepcopy(value)
    original = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["reason"] == "native_queue_declaration_conflict"
    assert result == raw == original


@pytest.mark.parametrize("condition", ("scale_bytes", "bf16_scale", "role_scale", "situ"))
def test_valid_existing_expert_abi_outside_native_caller_keeps_ordinary_prediction(condition):
    raw = retained()["raw_case"]
    quant = parse_case(raw).model.quant.to_dict()
    if condition == "scale_bytes":
        quant["scale_bytes"] = 2
    elif condition == "bf16_scale":
        quant.update(scale_format="bf16", scale_bytes=2)
    elif condition == "role_scale":
        quant.setdefault("category_overrides", {})["routed_expert"] = {
            "scale_format": "bf16", "scale_bytes": 2}
    else:
        raw["model"]["layer_overrides"] = {"0": {"ffn_activation": "situ"}}
    raw["model"]["quant"] = quant
    original = deepcopy(raw)
    ordinary = target_operators(raw, **options())
    assert len(ordinary) == 2470
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "not_applicable"
    assert provenance["reason"] == (
        "expert_activation_outside_observed_native_abi" if condition == "situ"
        else "expert_weight_scale_outside_observed_native_abi")
    assert result == raw == original
    assert target_operators(result, **options()) == ordinary


def test_declared_activation_format_does_not_override_mc2_produced_int8_abi():
    raw = retained()["raw_case"]
    raw["model"]["quant"] = parse_case(raw).model.quant.to_dict()
    raw["model"]["quant"].update(activation_format="bf16", activation_scale_format="bf16")
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "applied"
    gate = next(op for op in target_operators(result, **options()) if op.recipe == "balanced_grouped_gate_up")
    assert dict(gate.metadata)["activation_format"] == "int8"
    assert dict(gate.metadata)["activation_scale_format"] == "fp32"


def test_omitted_quantizer_preserves_valid_ordinary_caller():
    raw = retained()["raw_case"]
    raw["runtime"]["lowering_passes"] = []
    original = deepcopy(raw)
    ordinary = target_operators(raw, **options())
    assert len(ordinary) == 2410
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["reason"] == "required_activation_quantizer_not_selected"
    assert provenance["status"] == "not_applicable"
    assert result == raw == original
    assert target_operators(result, **options()) == ordinary


@pytest.mark.parametrize("selected", ("quantize", "native_fusion"))
def test_selected_native_implementation_keeps_its_original_valid_graph(selected):
    raw = retained()["raw_case"]
    lowerings = raw["runtime"]["kernels"]["lowerings"]
    if selected == "quantize":
        lowerings["quantize"] = {"implementation": "mindie_sd_quant_four_over_six_a5",
                                 "options": {"soc_family": "Ascend950"}}
    else:
        lowerings["native_fusion"] = {"cases": [{"domain": {"phases": ["decode"]},
            "binding": {"implementation": "declared_native_fusion",
                        "options": {"roles": ["grouped_gate_up_activation_quant"]}}}],
            "otherwise": "analytical"}
    original = deepcopy(raw)
    ordinary = target_operators(raw, **options())
    assert len(ordinary) == (2470 if selected == "quantize" else 2390)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "not_applicable"
    assert provenance["native_caller_domain_error"].startswith("mc2_unfused_")
    assert result == raw == original
    assert target_operators(result, **options()) == ordinary


def test_unselected_fusion_policy_does_not_block_native_decode_caller():
    raw = retained()["raw_case"]
    raw["runtime"]["kernels"]["lowerings"]["native_fusion"] = {
        "cases": [{"domain": {"phases": ["prefill"]},
                   "binding": {"implementation": "declared_native_fusion",
                               "options": {"roles": ["grouped_gate_up_activation_quant"]}}}],
        "otherwise": "analytical"}
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **options())
    assert provenance["status"] == "applied"
    assert result != raw
