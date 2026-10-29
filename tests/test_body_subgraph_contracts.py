"""Real MLA/index-selection fused rows, including A3/A5 capture gaps."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.tensor_contracts import (
    observed_contract, observed_contract_diagnostic, observed_contract_scope,
)


FIXTURES = Path(__file__).parent / "fixtures"


def capture(name):
    return list(kernel_rows(FIXTURES / "attention_cache_contracts" / (name + ".csv")))


@pytest.mark.parametrize("name,index,tokens", [
    ("a3_glm53", 1, 4096), ("a3_glm53_decode", 1, 1),
])
def test_lightning_indexer_keeps_selection_geometry_separate_from_projections(name, index, tokens):
    row = capture(name)[index]
    contract = observed_contract(row)
    assert contract == (
        "lightning_indexer_active", "LightningIndexer",
        (((tokens, 32, 128), "bf16", "ND"), ((tokens, 32), "bf16", "ND")),
        ((1, 128), "bf16", "ND"), ((tokens, 1, 2048), "int32", "ND"),
    )
    assert "query_projection" in observed_contract_scope(row)["excluded_semantic_work"]
    assert observed_contract(replace(row, duration_ns=row.duration_ns * 100)) == contract
    other_topk = replace(row, output_shapes=((tokens, 1, 1024), *row.output_shapes[1:]))
    assert observed_contract(other_topk) != contract
    wrong_weights = replace(row, input_shapes=(*row.input_shapes[:2], (tokens, 16),
                                               *row.input_shapes[3:]))
    assert observed_contract(wrong_weights) is None
    assert observed_contract_diagnostic(wrong_weights)["reason"] == "unsupported_indexer_active_geometry"
    assert observed_contract(replace(row, kind="VllmAscendQuantLightningIndexerV2")) is None


@pytest.mark.parametrize("name,index,tokens,present", [
    ("a3_glm53", 0, 4096, True),
    ("a3_glm53_prolog_no_index", 0, 4096, False),
    ("a3_glm53_decode", 0, 1, True),
    ("a3_glm53_decode", 2, 1, False),
])
def test_glm_mla_prolog_preserves_parameter_dtypes_and_optional_query_norm(
    name, index, tokens, present,
):
    row = capture(name)[index]
    assert observed_contract(row) == (
        "mla_prolog_active", "MlaPrologV3", ((tokens, 6144), "int8", "ND"),
        (((6144, 2048), "int8"), ((2048, 2048), "int8"),
         ((8, 192, 512), "bf16"), ((6144, 576), "int8"),
         ((2048,), "bf16"), ((512,), "bf16")),
        (((1, 512), "bf16", "ND"), ((1, 64), "bf16", "ND")),
        (((tokens, 8, 512), "bf16", "ND"), ((tokens, 8, 64), "bf16", "ND"),
         ((tokens, 2048), "int8", "ND") if present else ((), None, None)),
    )
    quant = replace(row, input_dtypes=(*row.input_dtypes[:1], "DT_FLOAT8_E4M3FN",
                                      *row.input_dtypes[2:]))
    assert observed_contract(quant) != observed_contract(row)
    wrong_parameter = replace(
        row, input_shapes=(*row.input_shapes[:3], (8, 128, 512), *row.input_shapes[4:]))
    assert observed_contract(wrong_parameter) is None
    assert observed_contract_diagnostic(wrong_parameter)["reason"] == "inconsistent_mla_active_parameters"


def test_kimi_mla_uses_source_defined_leading_axes_without_guessing_missing_rope():
    row = next(r for r in kernel_rows(FIXTURES / "body_attention/kimi_a5_full_model.csv")
               if r.kind == "MlaPrologV3")
    contract = observed_contract(row)
    assert contract == (
        "mla_prolog_active", "MlaPrologV3", ((1, 7168), "fp8_e4m3", "ND"),
        (((7168, 1536), "fp8_e4m3"), ((1536, 2304), "fp8_e4m3"),
         ((12, 128, 512), "bf16"), ((7168, 576), "fp8_e4m3"),
         ((1536,), "bf16"), ((512,), "bf16")),
        (((1, 512), "bf16", "ND"), ((1, 64), "bf16", "ND")),
        (((1, 12, 512), "bf16", "ND"), ((1, 12, 64), "bf16", "ND"), ((), None, None)),
    )
    scope = observed_contract_scope(row)
    assert scope["excluded_capture_missing_fields"] == ["input[7].shape", "input[8].shape"]
    assert {"rope_input_tensors", "quantization_scale_tensors",
            "quantization_scalar_modes", "leading_token_axis_grouping"} <= set(scope["not_compared"])
    assert native_tensor_contract(row)[2][0][0] == (1, 1, 7168)
    assert native_tensor_contract(row)[3][0][0] == (1, 1, 12, 512)
    incomplete = replace(row, input_shapes=((), *row.input_shapes[1:]))
    assert observed_contract(incomplete) is None
    assert observed_contract_diagnostic(incomplete)["missing_fields"] == ["input[0].shape"]


def test_mla_does_not_merge_inconsistent_leading_axes_or_invent_partial_query_norm():
    row = capture("a3_glm53")[0]
    inconsistent = replace(
        row, input_shapes=((1, 4096, 6144), *row.input_shapes[1:]),
        output_shapes=((2, 2048, 8, 512), (2, 2048, 8, 64), *row.output_shapes[2:]))
    assert observed_contract(inconsistent) is None
    assert observed_contract_diagnostic(inconsistent)["reason"] == "inconsistent_mla_active_parameters"
    missing_query = replace(row, output_shapes=(*row.output_shapes[:5], (), row.output_shapes[6]))
    assert observed_contract(missing_query) is None
    assert observed_contract_diagnostic(missing_query)["missing_fields"] == ["output[5].shape"]
    missing_dtype = replace(row, input_dtypes=("DT_UNDEFINED", *row.input_dtypes[1:]))
    assert observed_contract(missing_dtype) is None
    assert observed_contract_diagnostic(missing_dtype)["missing_fields"] == ["input[0].dtype"]
    missing_layout = replace(row, input_formats=(*row.input_formats[:3], "NULL",
                                               *row.input_formats[4:]))
    assert observed_contract(missing_layout) is None
    absent_shapes = replace(
        row, input_shapes=None, output_shapes=None,
        event=replace(row.event, input_shapes="N/A", output_shapes="N/A"))
    assert observed_contract(absent_shapes) is None
    assert observed_contract_diagnostic(absent_shapes)["reason"] == "missing_tensor_metadata"
    assert observed_contract_scope(absent_shapes)["excluded_capture_missing_fields"] == [
        "input[7].shape", "input[8].shape"]
    truncated = replace(row, input_shapes=row.input_shapes[:3],
                        input_dtypes=row.input_dtypes[:3], input_formats=row.input_formats[:3])
    assert observed_contract(truncated) is None
    assert observed_contract_diagnostic(truncated)["reason"] == "unsupported_native_tensor_slots"
    assert observed_contract_scope(truncated)["kind"] == "active_mla_prolog_descriptors"


def test_mla_active_projection_changes_neither_for_capacity_nor_duration():
    row = capture("a3_glm53")[0]
    cache, rope = (900, 64, 1, 512), (900, 64, 1, 64)
    changed = replace(
        row, duration_ns=row.duration_ns * 10,
        input_shapes=(*row.input_shapes[:9], cache, rope, *row.input_shapes[11:]),
        output_shapes=(*row.output_shapes[:2], cache, rope, *row.output_shapes[4:]))
    assert native_tensor_contract(changed) != native_tensor_contract(row)
    assert observed_contract(changed) == observed_contract(row)
    assert observed_contract_scope(row)["timing_scope"] == "inclusive_fused_subgraph; no_member_time_split"
