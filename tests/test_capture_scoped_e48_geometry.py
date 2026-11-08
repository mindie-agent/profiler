"""Focused generated-row geometry tests for A5 balanced local-expert binding.

[Role] Prove the generated grouped rows are bound to the declared routing
  ledger, including the E48 balanced remainder, not to a rank-global average.
[Invariants] Cases use the maintained Sim target graph. Positive controls are
  exact row counts; the negative copies a balanced graph into the old global
  geometry and must still be rejected.
[Side-Effect Policy] Pure in-memory declarations; no capture or cache writes.
"""
from copy import deepcopy
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
STRUCT = ROOT / "examples" / "structure"
sys.path.insert(0, str(STRUCT))

from capture_scoped_contracts import (  # noqa: E402
    LayerEvidence, generated_mismatches, validate_a5)
from capture_scoped_geometry import local_expert_rows  # noqa: E402


def sim_recipe_available():
    try:
        from mindie_sim.prediction.feedforward import MOE_RECIPES
    except Exception:
        return False
    return "local_expert_reduce" in MOE_RECIPES


pytestmark = pytest.mark.skipif(
    not sim_recipe_available(),
    reason="local_expert_reduce is not registered in this interpreter")


BASE = json.loads(
    (ROOT / "tests" / "fixtures" / "scoped_structure" / "a5_case.json").read_text())


def _case(experts, top_k, routing):
    raw = deepcopy(BASE)
    raw["model"].update(num_experts=experts, top_k=top_k)
    raw["runtime"].update(ep=4, moe_recipe="local_expert_reduce")
    if routing is not None:
        raw["runtime"]["routing"] = deepcopy(routing)
    return raw


def _ops(experts, top_k, tokens, routing):
    from mindie_sim import target_operators

    return target_operators(_case(experts, top_k, routing), phase="prefill",
                            tokens=tokens, context=0, sequences=1)


def _grouped_rows(ops):
    gate = next(op for op in ops
                if op.recipe == "balanced_grouped_gate_up" and op.layer == 0)
    down = next(op for op in ops
                if op.recipe == "balanced_grouped_down" and op.layer == 0)
    return gate.local_shape[0], down.local_shape[0]


def _mismatches(ops, experts, top_k, tokens, routing):
    return generated_mismatches(
        "local_expert_reduce", ops,
        window=SimpleNamespace(query_rows=tokens, layers=tuple(range(8))),
        tp=4, ep=4, hidden=2048, experts=experts, top_k=top_k,
        intermediate=768, material=None, routing=routing)


BALANCED = {"policy": "balanced"}


@pytest.mark.parametrize("experts,top_k,tokens,expected", [
    (16, 4, 4096, 4096), (16, 8, 4096, 8192),
    (32, 4, 4096, 4096), (32, 8, 4096, 8192),
    (48, 4, 4096, 4104), (48, 8, 4096, 8196),
    (64, 4, 4096, 4096), (64, 8, 4096, 8192),
    (16, 4, 8192, 8192), (16, 8, 8192, 16384),
    (32, 4, 8192, 8192), (32, 8, 8192, 16384),
    (48, 4, 8192, 8196), (48, 8, 8192, 16392),
    (64, 4, 8192, 8192), (64, 8, 8192, 16384),
])
def test_balanced_generated_rows_match_declared_ledger(
        experts, top_k, tokens, expected):
    assert local_expert_rows(tokens, top_k, experts, 4, BALANCED) == expected
    ops = _ops(experts, top_k, tokens, BALANCED)
    assert _grouped_rows(ops) == (expected, expected)
    assert _mismatches(ops, experts, top_k, tokens, BALANCED) == []


@pytest.mark.parametrize("top_k,tokens,balanced,probability", [
    (4, 4096, 4104, 4096),
    (8, 4096, 8196, 8192),
    (4, 8192, 8196, 8192),
    (8, 8192, 16392, 16384),
])
def test_e48_balanced_remainder_is_not_global_average(
        top_k, tokens, balanced, probability):
    assert local_expert_rows(tokens, top_k, 48, 4, BALANCED) == balanced
    assert local_expert_rows(tokens, top_k, 48, 4) == probability
    ops = _ops(48, top_k, tokens, BALANCED)
    assert _grouped_rows(ops) == (balanced, balanced)
    assert _mismatches(ops, 48, top_k, tokens, BALANCED) == []
    # A balanced ledger is not interchangeable with the global-average path.
    assert _mismatches(ops, 48, top_k, tokens, None)


def test_e48_global_average_geometry_is_rejected():
    ops = _ops(48, 4, 4096, BALANCED)
    rejected = [
        replace(op, local_shape=(4096,) + tuple(op.local_shape[1:]))
        if op.recipe in {"balanced_grouped_gate_up", "balanced_grouped_down"}
        and op.layer == 0 else op
        for op in ops
    ]
    fields = {item["field"]
              for item in _mismatches(rejected, 48, 4, 4096, BALANCED)}
    assert fields == {"gate_expected_rows_or_width",
                      "down_expected_rows_or_width"}


def _a5_layer(experts, top_k, query_rows, hidden=2048, intermediate=768):
    allocation = query_rows * top_k
    bank = experts // 4

    def sig(kind, inputs, outputs, input_dtypes, output_dtypes,
            input_formats, output_formats):
        return (kind, inputs, outputs, input_dtypes, output_dtypes,
                input_formats, output_formats)

    router = sig("MatMulV3", ((query_rows, hidden), (experts, hidden)),
                 ((query_rows, experts),), ("DT_BF16", "DT_BF16"),
                 ("FLOAT",), ("ND", "ND"), ("ND",))
    topk = sig("MoeGatingTopK", ((query_rows, experts),),
               ((query_rows, top_k), (query_rows, top_k),
                (query_rows, experts)), ("FLOAT",),
               ("FLOAT", "INT32", "FLOAT"), ("ND",),
               ("ND", "ND", "ND"))
    init = sig("MoeInitRoutingV3",
               ((query_rows, hidden), (query_rows, top_k)),
               ((allocation, hidden), (allocation,), (bank,), (allocation,)),
               ("DT_BF16", "INT32"),
               ("DT_BF16", "INT32", "INT64", "FLOAT"),
               ("ND", "ND"), ("ND", "ND", "ND", "ND"))
    up_sig, down_sig = ("GroupedMatmul", "up"), ("GroupedMatmul", "down")
    up_value = ("grouped_matrix", (bank, allocation, 2 * intermediate, hidden),
                "bf16", "bf16", "bf16", (), "")
    down_value = ("grouped_matrix", (bank, allocation, hidden, intermediate),
                  "bf16", "bf16", "bf16", (), "")
    swiglu = sig("SwiGlu", ((allocation, 2 * intermediate),),
                 ((allocation, intermediate),), ("DT_BF16",), ("DT_BF16",),
                 ("ND",), ("ND",))
    final = sig("MoeFinalizeRoutingV2",
                ((allocation, hidden), (allocation,), (query_rows, top_k)),
                ((query_rows, hidden),), ("DT_BF16", "INT32", "DT_BF16"),
                ("DT_BF16",), ("ND", "ND", "ND"), ("ND",))
    allreduce = ("hcom_allReduce",)
    roles = Counter({"topk": 1, "init_routing": 1, "grouped": 2,
                     "swiglu": 1, "finalize": 1, "matmul_v3": 1,
                     "allreduce": 1})
    variants = {
        "matmul_v3": {router: None}, "topk": {topk: None},
        "init_routing": {init: None},
        "grouped": {up_sig: up_value, down_sig: down_value},
        "swiglu": {swiglu: None}, "finalize": {final: None},
        "allreduce": {allreduce: None},
    }
    ordered = (("matmul_v3", router), ("topk", topk),
               ("init_routing", init), ("grouped", up_sig),
               ("swiglu", swiglu), ("grouped", down_sig),
               ("finalize", final), ("allreduce", allreduce))
    order = tuple((index, index + 1, role, item)
                  for index, (role, item) in enumerate(ordered))
    return LayerEvidence(roles, variants, frozenset(), order)


def test_a5_analysis_reports_declared_local_rows_and_uniform_reference():
    window = SimpleNamespace(
        query_rows=4096, layers=(SimpleNamespace(layer_id=0),))
    result = validate_a5(
        window, [_a5_layer(48, 4, 4096)], tp=4, ep=4, hidden=2048,
        experts=48, top_k=4, intermediate=768, routing_policy=BALANCED)
    assert result["ok"] is True
    allocation = result["allocation"]
    assert allocation["expected_local_valid_rows"] == 4104
    assert allocation["uniform_rank_average_rows"] == 4096
    assert allocation["routing_basis"] == (
        "declared_balanced_integer_ledger; not_native_force_eplb")
    probability = validate_a5(
        window, [_a5_layer(48, 4, 4096)], tp=4, ep=4, hidden=2048,
        experts=48, top_k=4, intermediate=768, routing_policy={})
    assert probability["allocation"]["expected_local_valid_rows"] == 4096
    assert probability["allocation"]["routing_basis"] == (
        "declared_probability_moments_or_default; not_native_force_eplb")
