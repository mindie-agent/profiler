"""Retained A3/A5 matrix descriptors and perturbations of their native ABI."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_matrix_contracts import (
    observed_matrix_contract, matrix_contract_diagnostic, matrix_contract_scope,
)
from mindie_profiler.normalized import kernel_rows


FIXTURES = Path(__file__).parent / "fixtures/fusion_contracts"


def rows(capture, kind):
    return [row for row in kernel_rows(FIXTURES / f"{capture}.csv") if row.kind == kind]


@pytest.mark.parametrize("capture,m,n,k", [
    ("a3_glm53_prefill", 4096, 4096, 2048),
    ("a3_glm53_decode", 1, 4096, 2048),
    ("a3_qwen35", 8192, 2560, 2048),
    ("a3_qwen36", 8192, 4096, 5120),
    ("a3_v4f", 4096, 1024, 4096),
    ("a3_v4pro", 1024, 1536, 7168),
])
def test_int8_v3_checks_both_scale_descriptors_and_nz_axes(capture, m, n, k):
    row = rows(capture, "QuantBatchMatmulV3")[0]
    expected = "matrix", (m, n, k), "int8", "int8", "bf16", (m,), "fp32"
    assert observed_matrix_contract(row) == expected
    swapped = replace(row, input_shapes=(row.input_shapes[0],
                                         (k // 16, n // 32, 16, 32),
                                         *row.input_shapes[2:]))
    if swapped.input_shapes != row.input_shapes:
        assert observed_matrix_contract(swapped) is None
    wrong_scale = replace(row, input_shapes=(*row.input_shapes[:2], (n + 1,), (m,)))
    assert observed_matrix_contract(wrong_scale) is None
    assert matrix_contract_diagnostic(wrong_scale)["reason"] == "unsupported_quant_matrix_scale_or_precision"
    assert observed_matrix_contract(replace(row, input_formats=("NCL", *row.input_formats[1:]))) is None


@pytest.mark.parametrize("capture", ["a5_kimi_k3", "a5_qwen38"])
def test_mxfp8_v3_keeps_paired_e8_scales(capture):
    row = rows(capture, "QuantBatchMatmulV3")[0]
    m, k = row.input_shapes[0]
    n = row.output_shapes[0][1]
    assert observed_matrix_contract(row) == (
        "matrix", (m, n, k), "fp8_e4m3", "fp8_e4m3", "bf16",
        (m, (k + 63) // 64, 2), "fp8_e8m0")
    bad = replace(row, input_shapes=(*row.input_shapes[:2],
                                     row.input_shapes[2][:-1] + (1,), row.input_shapes[3]))
    assert observed_matrix_contract(bad) is None
    assert observed_matrix_contract(replace(row, kind="QuantBatchMatmulV4")) is None


def test_mxfp4_v4_preserves_transposed_weight_and_scale_order():
    captured = rows("a5_kimi_k3", "QuantBatchMatmulV4")
    assert len(captured) == 2
    for row in captured:
        m, k = row.input_shapes[0]
        n = row.output_shapes[0][1]
        expected = ("matrix", (m, n, k), "fp8_e4m3", "mxfp4", "bf16",
                    (m, (k + 63) // 64, 2), "fp8_e8m0")
        assert observed_matrix_contract(row) == expected
        assert observed_matrix_contract(replace(row, duration_ns=1)) == expected
        swapped = replace(row, input_shapes=(*row.input_shapes[:2],
                                             row.input_shapes[3], row.input_shapes[2], ()))
        assert observed_matrix_contract(swapped) is None
        axes = replace(row, input_shapes=(row.input_shapes[0],
                                          (n // 32, k // 16, 16, 32),
                                          *row.input_shapes[2:]))
        assert observed_matrix_contract(axes) is None
        bias = replace(row, input_shapes=(*row.input_shapes[:4], (n,)))
        assert observed_matrix_contract(bias) is None
        assert matrix_contract_diagnostic(bias)["reason"] == "quant_matrix_bias_boundary_not_declared"
        assert "ten-slot" in matrix_contract_scope(row)["conditions"]


@pytest.mark.parametrize("capture,experts,weight", [
    ("a3_glm53_prefill", 256, "int4"), ("a3_glm53_decode", 256, "int4"),
    ("a3_qwen35", 256, "int8"), ("a3_v4f", 32, "int8"),
    ("a3_v4pro", 24, "int4"), ("a5_kimi_k3", 1, "fp8_e4m3"),
])
def test_grouped_matrix_never_flattens_expert_bank(capture, experts, weight):
    row = rows(capture, "GroupedMatmul")[0]
    contract = observed_matrix_contract(row)
    m, k = row.input_shapes[0]
    n = row.output_shapes[0][1]
    assert contract[:2] == ("grouped_matrix", (experts, m, n, k))
    assert contract[3] == weight
    assert "per_expert_row_counts" in matrix_contract_scope(row)["not_compared"]
    wrong_bank = replace(row, input_shapes=(*row.input_shapes[:7], (experts + 1,),
                                           *row.input_shapes[8:]))
    assert observed_matrix_contract(wrong_bank) is None
    offset = replace(row, input_shapes=(*row.input_shapes[:4], (experts, n),
                                       *row.input_shapes[5:]))
    assert observed_matrix_contract(offset) is None
    assert observed_matrix_contract(replace(row, kind="QuantBatchMatmulV3")) is None


def test_bf16_grouped_branch_is_distinct_from_quantized_same_geometry():
    row = rows("a3_qwen35", "GroupedMatmul")[1]
    assert observed_matrix_contract(row) == (
        "grouped_matrix", (256, 65536, 256, 2048), "bf16", "bf16", "bf16", (), "")
    materialized = replace(row, input_shapes=(*row.input_shapes[:3], (256, 256),
                                            *row.input_shapes[4:]))
    assert observed_matrix_contract(materialized) is None


@pytest.mark.parametrize("kind", ["QuantBatchMatmulV3", "QuantBatchMatmulV4", "GroupedMatmul"])
def test_missing_matrix_metadata_and_unknown_precision_remain_visible(kind):
    row = rows("a5_kimi_k3", kind)[0]
    missing = replace(row, input_shapes=None)
    assert observed_matrix_contract(missing) is None
    assert matrix_contract_diagnostic(missing)["category"] == "capture_metadata_missing"
    assert matrix_contract_scope(missing)["occurrence_identity"] is False
    unknown = replace(row, input_dtypes=("UNRECOGNIZED_FP8", *row.input_dtypes[1:]))
    assert observed_matrix_contract(unknown) is None
    incomplete = replace(row, input_formats=row.input_formats[:-1])
    assert observed_matrix_contract(incomplete) is None
    assert matrix_contract_diagnostic(incomplete)["reason"] == "incomplete_native_tensor_slots"
