"""Contracts from real A2 module captures and A5 mixed-phase kernel exports."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.events import Window
from mindie_profiler.normalized import kernel_rows, row_from_event
from mindie_profiler.sources_db import DbSource, probe_db
from mindie_profiler.tensor_contracts import observed_contract, observed_contract_diagnostic


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("capture,kind", [
    ("a5_qwen38", "DynamicMxQuant"),
    ("a5_kimi_k3", "DynamicMxQuant"),
    ("a5_qwen38", "AddRmsNormDynamicMxQuant"),
])
def test_real_mx_quant_requires_consistent_primary_output_and_scale_layout(capture, kind):
    row = next(row for row in kernel_rows(FIXTURES / "fusion_contracts" / f"{capture}.csv")
               if row.kind == kind)
    actual = observed_contract(row)
    assert actual is not None
    assert actual[1] == row.input_shapes[0]
    assert observed_contract(replace(row, duration_ns=row.duration_ns * 100)) == actual
    assert observed_contract(replace(
        row, output_shapes=((1,), *row.output_shapes[1:]))) is None
    assert observed_contract(replace(
        row, output_formats=("FRACTAL_NZ", *row.output_formats[1:]))) is None
    scale_index = 2 if kind == "AddRmsNormDynamicMxQuant" else 1
    formats = list(row.output_formats)
    formats[scale_index] = "ND" if formats[scale_index] == "NCL" else "NCL"
    assert observed_contract(replace(row, output_formats=tuple(formats))) is None
    scale_shapes = list(row.output_shapes)
    scale_shapes[scale_index] = (row.input_shapes[0][0], 1, 2)
    assert observed_contract(replace(row, output_shapes=tuple(scale_shapes))) is None
    missing = replace(row, output_formats=row.output_formats[:-1])
    assert observed_contract(missing) is None
    assert observed_contract_diagnostic(missing)["category"] == "capture_metadata_missing"


def test_real_add_norm_mx_preserves_residual_gamma_and_typed_empty_auxiliary_slot():
    row = next(row for row in kernel_rows(FIXTURES / "fusion_contracts/a5_qwen38.csv")
               if row.kind == "AddRmsNormDynamicMxQuant")
    actual = observed_contract(row)
    assert actual is not None and row.output_shapes[-1] == ()
    assert row.output_dtypes[-1] == "FLOAT" and row.output_formats[-1] == "ND"
    for changed in (
        replace(row, input_shapes=(row.input_shapes[0], (1, 5120), row.input_shapes[2])),
        replace(row, input_shapes=(*row.input_shapes[:2], (1,))),
        replace(row, input_dtypes=(*row.input_dtypes[:2], "FLOAT")),
        replace(row, output_shapes=(row.output_shapes[0], (1,), *row.output_shapes[2:])),
        replace(row, output_shapes=(*row.output_shapes[:3], (16384,))),
    ):
        assert observed_contract(changed) is None


def a5_rows():
    return {
        row.kind: row for row in kernel_rows(
            FIXTURES / "structure_contracts/a5_tensor_contracts.csv")
    }


def test_tiny_mlp_db_preserves_bias_and_relu_contracts_for_two_invocations():
    source = DbSource(probe_db(FIXTURES / "structure_module/capture.db"))
    events, stats = source.iter_window(Window(1792446524431924369, 1792446525730030111))
    rows = [row_from_event(event) for event in events]
    assert stats.rows_read == 6
    assert [row.event.locator["task_global_id"] for row in rows] == [58, 61, 63, 64, 65, 67]
    assert [observed_contract(row) for row in rows] == [
        ("matrix_bias", (8, 512, 256), "fp32", "fp32", "fp32", (512,), "fp32"),
        ("relu", (8, 512), "fp32"),
        ("matrix_bias", (8, 256, 512), "fp32", "fp32", "fp32", (256,), "fp32"),
    ] * 2
    assert len({row.event_id for row in rows}) == 6


def test_a5_swiglu_alias_uses_recorded_geometry_and_slice_keeps_rank():
    rows = a5_rows()
    assert observed_contract(rows["SwiGlu"]) == ("swiglu", (16384, 17408), "bf16")
    contract = observed_contract(rows["Slice"])
    assert contract == (
        "slice_copy", (16384, 128, 128), (16384, 48, 128), "bf16", "bf16")
    assert contract != (
        "slice_copy", (16384, 16384), (16384, 6144), "bf16", "bf16")
    assert rows["Slice"].input_shapes[1:] == ((3,), (3,))


def test_real_absent_tensors_are_distinct_from_unsupported_present_tensors():
    rows = a5_rows()
    missing = rows["fused_gdn_gating_kernel"]
    assert missing.event.input_shapes == missing.event.output_shapes == "N/A"
    assert observed_contract(missing) is None
    diagnostic = observed_contract_diagnostic(missing)
    assert diagnostic["category"] == "capture_metadata_missing"
    assert diagnostic["reason"] == "missing_tensor_metadata"
    assert set(diagnostic["missing_fields"]) >= {"input_shapes", "output_shapes"}
    unsupported = rows["Fill"]
    assert unsupported.input_shapes == ((1,), ())
    assert observed_contract(unsupported) is None
    diagnostic = observed_contract_diagnostic(unsupported)
    assert diagnostic["category"] == "contract_support_gap"
    assert diagnostic["reason"] == "unsupported_operator_contract"


def test_descriptor_loss_unparsed_shapes_and_unsupported_layout_stay_distinct():
    event = a5_rows()["SwiGlu"].event
    absent = row_from_event(replace(event, output_dtypes=""))
    assert observed_contract(absent) is None
    diagnostic = observed_contract_diagnostic(absent)
    assert diagnostic["category"] == "capture_metadata_missing"
    assert diagnostic["missing_fields"] == ["output_dtypes"]
    malformed = row_from_event(replace(event, input_shapes="tokens,34816"))
    assert observed_contract(malformed) is None
    diagnostic = observed_contract_diagnostic(malformed)
    assert diagnostic["category"] == "parser_contract_gap"
    assert diagnostic["fields"] == ["input_shapes"]
    unsupported = row_from_event(replace(event, input_formats="FRACTAL_NZ"))
    assert observed_contract(unsupported) is None
    diagnostic = observed_contract_diagnostic(unsupported)
    assert diagnostic["category"] == "contract_support_gap"
    assert diagnostic["reason"] == "unsupported_tensor_contract"
