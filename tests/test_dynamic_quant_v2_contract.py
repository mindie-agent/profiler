"""Retain the materialized offset of the actual three-output quantization ABI."""
from dataclasses import replace
from pathlib import Path

from mindie_profiler.normalized import kernel_rows, row_from_event
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_diagnostic, observed_contract_scope


def test_actual_dynamic_quant_v2_preserves_scale_and_offset_outputs():
    fixture = Path(__file__).parent / "fixtures/graph_execution/op_summary.csv"
    row = next(row for row in kernel_rows(fixture) if row.kind == "DynamicQuantV2")
    contract = observed_contract(row)
    assert contract == (
        "dynamic_quant_v2_active", "DynamicQuantV2", ((4, 5120), "bf16", "ND"),
        ((4, 5120), "int8", "ND"), ((4,), "fp32", "ND"), ((4,), "fp32", "ND"))
    assert observed_contract_diagnostic(row)["category"] == "tensor_contract_available"
    assert "materialized_offset_slot" in observed_contract_scope(row)["compared"]
    # Algorithm probe: dropping the real third output cannot silently make
    # this capture alias the older DynamicQuant interface.
    lost_offset = row_from_event(replace(row.event, output_shapes='"4,5120;4"',
                                         output_dtypes="INT8;FLOAT", output_formats="ND;ND"))
    assert observed_contract(lost_offset) is None
    assert observed_contract_diagnostic(lost_offset)["reason"] == "unsupported_native_tensor_slots"
