"""Retained router ABIs preserve score/weight precision and hash-table mode."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_router_contracts import (
    observed_router_contract, router_contract_diagnostic, router_contract_scope,
)
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import observed_contract


FIXTURES = Path(__file__).parent / "fixtures/fusion_contracts"


def rows(capture, kind):
    return [row for row in kernel_rows(FIXTURES / f"{capture}.csv") if row.kind == kind]


@pytest.mark.parametrize("capture,kind,dtype,experts,topk", [
    ("a3_glm53_prefill", "MoeGatingTopK", "fp32", 256, 8),
    ("a3_qwen35", "MoeGatingTopK", "bf16", 256, 8),
    ("a5_kimi_k3", "MoeGatingTopK", "fp32", 896, 16),
    ("a3_v4f", "MoeGatingTopKHash", "fp32", 256, 6),
    ("a3_v4pro", "MoeGatingTopKHash", "fp32", 384, 6),
])
def test_real_router_geometry_and_precision(capture, kind, dtype, experts, topk):
    actual = rows(capture, kind)
    assert actual
    for row in actual:
        contract = observed_router_contract(row)
        assert contract is not None
        count = row.input_shapes[0][0]
        base = (
            ((count, experts), dtype, "ND"), ((count, topk), dtype, "ND"),
            ((count, topk), "int32", "ND"))
        expected = (
            (*base, ((experts,), dtype, "ND"), ((), None, None))
            if kind == "MoeGatingTopKHash" and contract[2] == "score_topk"
            else base)
        assert contract[3:] == expected
        assert observed_contract(row) == contract
        assert observed_contract(replace(row, duration_ns=row.duration_ns * 100)) == contract
        assert not router_contract_scope(row)["occurrence_identity"]


def test_hash_table_and_score_topk_branches_cannot_alias():
    actual = rows("a3_v4f", "MoeGatingTopKHash")
    contracts = [observed_contract(row) for row in actual]
    assert {contract[2] for contract in contracts} == {"hash_table", "score_topk"}
    row = next(row for row in actual if row.input_shapes[2])
    with_vision_bias = replace(
        row, input_shapes=(*row.input_shapes[:4], (256,)),
        input_dtypes=(*row.input_dtypes[:4], "FLOAT"),
        input_formats=(*row.input_formats[:4], "ND"))
    vision_contract = observed_contract(with_vision_bias)
    assert vision_contract is not None
    assert vision_contract[-2:] == (((), None, None), ((256,), "fp32", "ND"))
    bad_vision_bias = replace(
        row, input_shapes=(*row.input_shapes[:4], (128,)),
        input_dtypes=(*row.input_dtypes[:4], "FLOAT"),
        input_formats=(*row.input_formats[:4], "ND"))
    assert observed_contract(bad_vision_bias) is None
    assert router_contract_diagnostic(bad_vision_bias)["reason"] == "unsupported_router_active_geometry"
    extra_slot = replace(
        row, input_shapes=(*row.input_shapes[:4], (256,), (256,)),
        input_dtypes=(*row.input_dtypes[:4], "FLOAT", "FLOAT"),
        input_formats=(*row.input_formats[:4], "ND", "ND"))
    assert observed_contract(extra_slot) is None
    assert router_contract_diagnostic(extra_slot)["reason"] == "unsupported_router_native_slots"


def test_missing_metadata_and_invalid_score_or_output_geometry_are_not_candidates():
    row = rows("a3_glm53_prefill", "MoeGatingTopK")[0]
    broken = [
        replace(row, input_shapes=None),
        replace(row, input_formats=("FRACTAL_NZ", *row.input_formats[1:])),
        replace(row, output_shapes=((row.input_shapes[0][0], 257), *row.output_shapes[1:])),
        replace(row, output_dtypes=("BF16", *row.output_dtypes[1:])),
        replace(row, input_dtypes=("UNKNOWN_DTYPE", *row.input_dtypes[1:])),
    ]
    for changed in broken:
        assert observed_contract(changed) is None
        assert router_contract_diagnostic(changed)["reason"]
