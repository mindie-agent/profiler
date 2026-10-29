"""Retained Kimi MX branches preserve scale slots, packed axes and routing limits."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import (
    observed_contract, observed_contract_diagnostic, observed_contract_scope,
)


FIXTURE = Path(__file__).parent / "fixtures/fusion_contracts/kimi_matrix_branches.csv"


def rows(kind):
    return [row for row in kernel_rows(FIXTURE) if row.kind == kind]


def test_grouped_situ_native_abi_proves_channels_but_not_expert_histogram():
    captured = rows("GroupedMatmulSituQuant")
    assert [row.input_shapes[0][0] for row in captured] == [2875, 3286]
    expected = (
        "grouped_mlp_parameters_active", "GroupedMatmulSituQuant",
        (28, 3584, 3072), ("fp8_e4m3", "mxfp4", "fp8_e4m3"),
    )
    assert all(observed_contract(row) == expected for row in captured)
    assert native_tensor_contract(captured[0]) != native_tensor_contract(captured[1])
    assert observed_contract(replace(captured[0], duration_ns=1)) == expected
    scope = observed_contract_scope(captured[0])
    assert {"routed_token_count", "expert_group_sizes_and_indices", "beta", "linear_beta"} <= \
        set(scope["not_compared"])
    assert "expert_down_projection" in scope["excluded_semantic_work"]


@pytest.mark.parametrize("slot,shape", [
    (1, (2875, 56, 1)),
    (2, (28, 1792, 6144)),
    (3, (28, 56, 6144, 2)),
    (4, (29,)),
])
def test_grouped_situ_rejects_wrong_scale_packing_weight_axes_and_bank(slot, shape):
    row = rows("GroupedMatmulSituQuant")[0]
    shapes = list(row.input_shapes)
    shapes[slot] = shape
    changed = replace(row, input_shapes=tuple(shapes))
    assert observed_contract(changed) is None
    assert observed_contract_diagnostic(changed)["reason"] == \
        "unsupported_grouped_situ_parameter_geometry"


def test_grouped_situ_missing_slots_and_other_implementations_do_not_become_matches():
    row = rows("GroupedMatmulSituQuant")[0]
    missing = replace(row, output_shapes=None, event=replace(row.event, output_shapes="N/A"))
    assert observed_contract(missing) is None
    assert observed_contract_diagnostic(missing)["category"] == "capture_metadata_missing"
    assert observed_contract(replace(row, kind="GroupedMatmulSwigluQuant")) is None
    assert observed_contract(replace(
        row, input_formats=(*row.input_formats[:2], "FRACTAL_NZ", *row.input_formats[3:]))) is None
    assert observed_contract(replace(
        row, output_shapes=(row.output_shapes[0], (2875, 48, 1)))) is None


def test_grouped_mxfp4_down_uses_antiquant_scale_as_microscale_not_affine_bias():
    captured = [row for row in rows("GroupedMatmul") if row.input_dtypes[1] == "DT_FLOAT4_E2M1"]
    assert [row.input_shapes[0][0] for row in captured] == [2875, 3286]
    for row in captured:
        m = row.input_shapes[0][0]
        assert observed_contract(row) == (
            "grouped_matrix", (28, m, 3584, 3072), "fp8_e4m3", "mxfp4", "bf16",
            (m, 48, 2), "fp8_e8m0")
        swapped = replace(row, input_shapes=(
            *row.input_shapes[:3], row.input_shapes[5], row.input_shapes[4], (),
            *row.input_shapes[6:]))
        assert observed_contract(swapped) is None
        wrong_axes = replace(row, input_shapes=(
            row.input_shapes[0], (28, 224, 96, 16, 32), *row.input_shapes[2:]))
        assert observed_contract(wrong_axes) is None
        offset = replace(row, input_shapes=(*row.input_shapes[:6], (28, 3584),
                                           *row.input_shapes[7:]))
        assert observed_contract(offset) is None
        assert observed_contract_diagnostic(offset)["reason"] == \
            "grouped_matrix_antiquant_boundary_not_declared"


def test_single_bank_grouped_linear_keeps_its_native_bank_identity():
    row = rows("GroupedMatmul")[0]
    assert observed_contract(row) == (
        "grouped_matrix", (1, 8192, 4608, 7168), "fp8_e4m3", "fp8_e4m3", "bf16",
        (8192, 112, 2), "fp8_e8m0")
    assert "group_list_values" in observed_contract_scope(row)["not_compared"]
