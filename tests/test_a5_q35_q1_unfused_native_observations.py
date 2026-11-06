"""Validate physical q1 MoE domains on entire retained 64K captures.

[Role] Check native services and Body results using held-out source evidence.
[Invariants] Only 4K native samples assign parameters. Context never selects a
  local MoE service, and an unobserved physical domain preserves the full input.
[Timeouts & Locks] Local golden captures and finite target graphs; no waits.
[Side-Effect Policy] Runtime homes are isolated by the repository conftest.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import graph_costs, predict, target_operators

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from a5_native_observations import apply_a5_native_observations
from a5_q35_unfused_native_observations import Q1_PROFILE_PATH, apply_a5_q35_unfused_native_observations


FIXTURE_PATH = ROOT / "tests/fixtures/native_observations/a5_q35_q1_unfused_heldout.json"


def fixtures():
    return json.loads(FIXTURE_PATH.read_text())["cases"]


def declared(fixture):
    return apply_a5_native_observations(fixture["raw_case"], **fixture["geometry"])[0]


@pytest.mark.parametrize("index", range(6))
def test_entire_held_context_native_boundaries_and_body(index):
    fixture = fixtures()[index]
    profile = json.loads(Q1_PROFILE_PATH.read_text())
    held = [row for row in profile["native_validation"]
            if row["id"] == fixture["source_case_id"]]
    expected = next(row for row in profile["body_validation"]
                    if row["id"] == fixture["source_case_id"])
    estimates, observations, counts = [], [], []
    for population in fixture["populations"]:
        source_geometry = population["geometry"]
        geometry = {"phase": "decode", "tokens": source_geometry["tokens_per_sequence"],
                    "context": source_geometry["context_tokens"],
                    "sequences": source_geometry["sequences_per_replica"]}
        raw = apply_a5_native_observations(fixture["raw_case"], **geometry)[0]
        original = deepcopy(raw)
        result, provenance = apply_a5_q35_unfused_native_observations(raw, **geometry)
        assert raw == original
        population_native = {row["recipe"]: row for row in held
                             if row["active_query_rows"] == geometry["sequences"]}
        supported = population_native["balanced_grouped_gate_up"]["response_validation_supported"]
        expected_part = next(row for row in expected["populations"] if row["geometry"] == geometry)
        if supported:
            assert provenance["status"] == "applied"
            assert len(provenance["matched_domains"]) == 8
            assert all(row["occurrences"] == 8 for row in provenance["matched_domains"])
            seen = set()
            for op in target_operators(result, **geometry):
                if op.recipe not in population_native or op.recipe in seen:
                    continue
                if op.recipe == "dynamic_quantize" and "mc2_unfused_storage" not in dict(op.metadata):
                    continue
                seen.add(op.recipe)
                row = population_native[op.recipe]
                measured = graph_costs(result, (op,), isolated=False,
                                       external_inputs={dependency: 0 for dependency in op.deps})
                predicted_us = measured["duration_ms"] * 1000
                assert predicted_us == pytest.approx(row["predicted_mean_us"])
                assert abs(predicted_us / row["mean_us"] - 1) < 0.1
            assert len(seen) == 8
            again, _ = apply_a5_q35_unfused_native_observations(result, **geometry)
            assert again == result
        else:
            # Retain every undeclared active caller population in the whole capture.
            assert provenance["status"] == "not_applicable"
            assert provenance["reason"] == "source_geometry_outside_observed_native_profile"
            assert result == raw
            for recipe in ("balanced_grouped_gate_up", "balanced_grouped_down"):
                assert population_native[recipe]["predicted_mean_us"] is None
        prediction = predict(result, scope="body", event_limit=0, **geometry)
        body = prediction["complete_ms"] - min(
            row["ready_ms"] for row in prediction["timeline"] if row["family"] != "barrier")
        assert body == pytest.approx(expected_part["predicted_ms"])
        if not supported:
            assert body == pytest.approx(expected_part["baseline_ms"])
        assert abs(body / population["observed_ms"] - 1) < 0.1
        estimates.append(body)
        observations.append(population["observed_ms"])
        counts.append(population["forward_count"])
    weighted_body = sum(value * count for value, count in zip(estimates, counts)) / sum(counts)
    weighted_observed = sum(value * count for value, count in zip(observations, counts)) / sum(counts)
    assert weighted_body == pytest.approx(expected["predicted_body_ms"])
    assert weighted_observed == pytest.approx(expected["observed_body_ms"])
    assert abs(weighted_body / weighted_observed - 1) < 0.1


def test_parameters_recompute_from_only_complete_training_native_calls():
    profile = json.loads(Q1_PROFILE_PATH.read_text())
    held_ids = {row["id"] for row in profile["source_captures"] if row["role"] == "validation"}
    for parameter in profile["parameter_groups"]:
        observations = [row for row in profile["native_observations"]
                        if row["role"] == "parameter_assignment" and row["abi"] == parameter["abi"]]
        count = sum(row["sample_count"] for row in observations)
        total = sum(row["sum_ns"] for row in observations)
        assert count == parameter["sample_count"] and total == parameter["sum_ns"]
        assert total / count / 1000 == pytest.approx(parameter["mean_us"])
        assert not held_ids.intersection(parameter["training_ids"])
        assert all(row["sample_count"] == row["forward_count"] * 8 for row in observations)


@pytest.mark.parametrize("condition", ("experts", "topk", "sequences", "layers", "graph_capacity", "literal_caller"))
def test_unobserved_q1_domain_preserves_the_complete_original(condition):
    fixture = fixtures()[0]
    raw, geometry = fixture["raw_case"], dict(fixture["geometry"])
    if condition == "experts":
        raw["model"]["num_experts"] = 16
    elif condition == "topk":
        raw["model"]["top_k"] = 8
    elif condition == "sequences":
        geometry["sequences"] = 2
    elif condition == "layers":
        raw["model"]["layers"] = 4
    elif condition == "graph_capacity":
        raw["runtime"]["graph_capture_keys"] = raw["runtime"]["graph_buckets"] = [8]
    else:
        raw["runtime"]["metadata"]["captured_additional_config"]["enable_force_eplb"] = False
    original = deepcopy(raw)
    result, provenance = apply_a5_q35_unfused_native_observations(raw, **geometry)
    assert provenance["status"] == "not_applicable"
    assert result == raw == original


def test_context_is_not_a_selector_for_local_native_work():
    fixture = fixtures()[0]
    raw, geometry = declared(fixture), fixture["geometry"]
    reference, expected = apply_a5_q35_unfused_native_observations(raw, **geometry)
    actual, provenance = apply_a5_q35_unfused_native_observations(raw, **{**geometry, "context": 32768})
    assert provenance["status"] == "applied"
    assert provenance["matched_domains"] == expected["matched_domains"]
    assert actual == reference
