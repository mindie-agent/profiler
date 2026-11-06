"""Retained q4 native boundaries preserve logical and graph tensor geometry.

[Role] Exercise native curves at entire contexts withheld from assignment.
[Invariants] Full native kernels are counted once; padding adds no requests.
  Every other operator response and the retained input mapping are preserved.
[Timeouts & Locks] Local operator graphs only; no remote operations or waits.
[Side-Effect Policy] Test runtime homes are isolated by conftest.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("mindie_sim")
from mindie_sim import graph_costs, target_operators

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from a5_mtp_native_observations import PROFILE_PATH, apply_a5_mtp_native_observations


def retained(name):
    return json.loads((ROOT / "tests" / "fixtures" / "native_observations" / f"{name}.json").read_text())


@pytest.mark.parametrize("name", ("a5_qwen36_tp8_q4_b32", "a5_qwen35_tp4_q4_b7"))
def test_reserved_native_context_executes_both_complete_boundaries(name):
    fixture = retained(name)
    raw, g = fixture["raw_case"], fixture["geometry"]
    original = deepcopy(raw)
    options = {"phase": "decode", "tokens": 4, "context": g["context"],
               "sequences": g["active_sequences"]}
    imported, provenance = apply_a5_mtp_native_observations(raw, **options)
    assert provenance["status"] == "applied"
    assert raw == original and not provenance["observations_modified"]
    assert len(provenance["matched_domains"]) == 2
    previous = raw["runtime"]["kernels"]["service_regimes"]
    unchanged = [row for row in previous if row["id"] not in provenance["replaced_rule_ids"]]
    assert imported["runtime"]["kernels"]["service_regimes"][:len(unchanged)] == unchanged
    profile = json.loads(PROFILE_PATH.read_text())
    held = {row["recipe"]: row for row in profile["validation"]
            if row["id"] == fixture["source_case_id"] and row["geometry"] == g}
    assert len(held) == 2 and all(row["held_context"] for row in held.values())
    seen = set()
    for op in target_operators(imported, **options):
        if op.recipe not in held or op.recipe in seen:
            continue
        seen.add(op.recipe)
        native = held[op.recipe]
        graph = graph_costs(imported, (op,), isolated=False,
                            external_inputs={dependency: 0 for dependency in op.deps})
        assert graph["duration_ms"] * 1000 == pytest.approx(native["predicted_us"])
        assert abs(graph["duration_ms"] * 1000 / native["observed_us"] - 1) < 0.01
        metadata = dict(op.metadata)
        assert metadata["graph_active_query_rows"] == g["active_query_rows"]
        assert metadata["graph_physical_query_rows"] == g["physical_query_rows"]
        if op.recipe == "ascend_recurrent_gdn_fp32_state":
            assert op.local_shape[0] == g["active_query_rows"]
            assert op.padded_shape[0] == g["physical_query_rows"]
            assert tuple(metadata["sequence_tokens"]) == (4,) * g["active_sequences"]
            assert tuple(metadata["physical_sequence_tokens"]) == (
                (4,) * g["active_sequences"] + (0,) * (g["physical_sequences"] - g["active_sequences"]))
    assert seen == held.keys()
    again, _ = apply_a5_mtp_native_observations(imported, **options)
    assert again == imported


@pytest.mark.parametrize("condition", ("q1", "padded_capacity", "context", "rates", "recurrence_implementation"))
def test_unmeasured_condition_leaves_the_complete_original_input(condition):
    fixture = retained("a5_qwen35_tp4_q4_b7")
    raw = fixture["raw_case"]
    options = {"phase": "decode", "tokens": 4, "context": 196608, "sequences": 7}
    if condition == "q1":
        options.update(tokens=1, sequences=28)
    elif condition == "padded_capacity":
        raw["runtime"]["graph_capture_keys"] = [64]
        raw["runtime"]["graph_buckets"] = [64]
    elif condition == "context":
        options["context"] = 400000
    elif condition == "rates":
        raw["machine"]["device"].setdefault("rates", {})["hbm"] = 1e6
    else:
        raw["runtime"]["kernels"]["lowerings"]["gdn_decode"]["options"]["recurrent_implementation"] = "analytical"
    original = deepcopy(raw)
    result, provenance = apply_a5_mtp_native_observations(raw, **options)
    assert provenance["status"] == "not_applicable"
    assert result == raw == original
