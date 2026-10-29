"""Retained A3/A5 normalization and batch-matrix boundaries."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_layout_contracts import (
    observed_layout_contract, layout_contract_diagnostic, layout_contract_scope,
)
from mindie_profiler.normalized import kernel_rows


FIXTURES = Path(__file__).parent / "fixtures/fusion_contracts"


def row(capture, kind):
    return next(value for value in kernel_rows(FIXTURES / f"{capture}.csv")
                if value.kind == kind)


@pytest.mark.parametrize("capture,tokens", [
    ("a3_glm53_prefill", 4096), ("a3_glm53_decode", 1),
])
def test_layernorm_preserves_fp32_affine_and_primary_output(capture, tokens):
    actual = row(capture, "LayerNormV3")
    x, affine = ((tokens, 128), "fp32", "ND"), ((128,), "fp32", "ND")
    assert observed_layout_contract(actual) == (
        "layernorm_active", "LayerNormV3", x, affine, affine, x)
    wrong = replace(actual, input_shapes=(actual.input_shapes[0], (64,), (128,)))
    assert observed_layout_contract(wrong) is None
    assert layout_contract_diagnostic(wrong)["reason"] == "unsupported_layernorm_geometry"
    assert "auxiliary_mean_rstd_values_and_stores" in layout_contract_scope(actual)["not_compared"]


@pytest.mark.parametrize("capture,geometry", [
    ("a3_glm53_prefill", (8, 4096, 256, 512)),
    ("a3_glm53_decode", (8, 1, 256, 512)),
    ("a3_v4f", (1, 4096, 1024, 4096)),
    ("a3_v4pro", (1, 1024, 1024, 4096)),
    ("a5_kimi_k3", (12, 1, 128, 512)),
])
def test_transposed_batch_contract_keeps_heads_rows_and_parameter_axes(capture, geometry):
    actual = row(capture, "TransposeBatchMatMul")
    assert observed_layout_contract(actual) == (
        "transpose_batchmatmul_active", "TransposeBatchMatMul", geometry,
        "bf16", "bf16", "bf16")
    batch, tokens, n, k = geometry
    wrong = replace(actual, output_shapes=((tokens, batch, n + 1),))
    assert observed_layout_contract(wrong) is None
    # Flattening a batch into M loses the per-head weight mapping.
    flattened = replace(actual, input_shapes=((batch * tokens, k), actual.input_shapes[1]))
    assert observed_layout_contract(flattened) is None
    assert layout_contract_scope(actual)["observed_input_shapes"] == actual.input_shapes
    assert observed_layout_contract(replace(actual, duration_ns=actual.duration_ns * 7)) == \
        observed_layout_contract(actual)
