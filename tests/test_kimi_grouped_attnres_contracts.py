"""Real backing allocations cannot stand in for native execution arguments."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import (
    observed_contract, observed_contract_diagnostic, observed_contract_scope,
)


FIXTURES = Path(__file__).parent / "fixtures"


def captured(kind):
    return [row for row in kernel_rows(FIXTURES / "kimi_grouped_attnres/a5_kimi_k3.csv")
            if row.kind == kind]


@pytest.mark.parametrize("capture,k", [
    ("a3_glm53_prefill", 6144), ("a3_v4f", 4096),
])
def test_shared_gate_up_int32_capture_remains_a_separate_accumulator_boundary(capture, k):
    row = next(kernel_rows(FIXTURES / f"mixed_step_body/{capture}.csv"))
    expected = ("matrix", (4096, 512, k), "int8", "int8", "int32", (), "")
    assert row.kind == "QuantBatchMatmulV3"
    assert observed_contract(row) == expected
    assert observed_contract(replace(row, duration_ns=1)) == expected
    scope = observed_contract_scope(row)
    assert scope["output_boundary"] == "integer_accumulator"
    assert "activation_scale_shape_dtype" not in scope["compared"]
    assert "weight_scale_shape_dtype_layout" in scope["validated_observed"]
    assert "subsequent_dequantization" in scope["not_compared"]
    # The same three slots with floating output do not establish a missing
    # token-scale epilogue; the real following activation is a separate event.
    floating = replace(row, output_dtypes=("DT_BF16",))
    assert observed_contract(floating) is None
    assert observed_contract_diagnostic(floating)["reason"] == \
        "unsupported_quant_matrix_accumulator_boundary"
    missing_scale = replace(row, input_shapes=(*row.input_shapes[:2], ()))
    assert observed_contract(missing_scale) is None


def test_single_bank_mx_shapes_remain_grouped_without_group_list_value_evidence():
    rows = [row for row in captured("GroupedMatmul") if row.input_shapes[7] == (1,)]
    assert {row.input_shapes[0][0] for row in rows} == {1, 1024, 8192}
    for row in rows:
        m, k = row.input_shapes[0]
        n = row.output_shapes[0][1]
        contract = observed_contract(row)
        assert contract == (
            "grouped_matrix", (1, m, n, k), "fp8_e4m3", "fp8_e4m3", "bf16",
            (m, (k + 63) // 64, 2), "fp8_e8m0")
        assert contract[0] != "matrix"
        scope = observed_contract_scope(row)
        assert scope["row_count_basis"] == "recorded_tensor_extent"
        assert "group_list_values" in scope["required_runtime_evidence"]
        assert scope["single_bank_condition"]


def test_routed_down_retains_allocated_rows_and_bank_instead_of_assumed_effective_rows():
    rows = [row for row in captured("GroupedMatmul") if row.input_shapes[7] == (28,)]
    assert 512 in {row.input_shapes[0][0] for row in rows}
    contracts = []
    for row in rows:
        m = row.input_shapes[0][0]
        contract = observed_contract(row)
        assert contract == (
            "grouped_matrix", (28, m, 3584, 3072), "fp8_e4m3", "mxfp4", "bf16",
            (m, 48, 2), "fp8_e8m0")
        assert observed_contract(replace(row, duration_ns=1)) == contract
        contracts.append(contract)
    assert len(set(contracts)) == len(rows)


def test_attnres_six_slot_capture_does_not_claim_mixture_only_or_capacity_depth():
    rows = captured("AttnResFwd")
    assert len(rows) == 4
    assert {row.output_shapes[0][0] for row in rows} == {7168, 7340032}
    for row in rows:
        native = native_tensor_contract(row)
        assert len(native[2]) == 6 and len(native[3]) == 3
        assert observed_contract(row) is None
        diagnostic = observed_contract_diagnostic(row)
        assert diagnostic["recorded_slot_counts"] == {"inputs": 6, "outputs": 3}
        assert {"valid_blocks", "block_residual_strides", "fuse_add", "mix",
                "output_norm_enabled", "invocation_implementation_and_tiling"} <= \
            set(diagnostic["required_runtime_evidence"])
        evidence = diagnostic["source_interface_evidence"]
        assert evidence["recorded_slot_count_matches"]
        assert evidence["identity_basis"] == "retained_capture_image_source"
        assert not evidence["event_binary_or_dispatch_proven"]
        assert observed_contract_scope(row)["compared"] == []
        assert observed_contract(replace(row, duration_ns=1)) is None


@pytest.mark.parametrize("kind", ["AttnResFwd", "GroupedMatmul"])
def test_missing_native_slots_cannot_be_replaced_by_a_runtime_evidence_diagnostic(kind):
    row = captured(kind)[0]
    missing = replace(row, output_shapes=None, event=replace(row.event, output_shapes="N/A"))
    assert observed_contract(missing) is None
    assert observed_contract_diagnostic(missing)["category"] == "capture_metadata_missing"
    incomplete = replace(row, input_dtypes=row.input_dtypes[:-1])
    assert observed_contract(incomplete) is None
    assert observed_contract_diagnostic(incomplete)["reason"] == "incomplete_native_tensor_slots"
