"""Real retained fusion ABIs and exclusions that prevent false subgraph matches."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_fusion_contracts import (
    observed_fusion_contract, fusion_contract_diagnostic, fusion_contract_scope,
)
from mindie_profiler.native_tensor_abi import native_tensor_contract
from mindie_profiler.normalized import kernel_rows


FIXTURES = Path(__file__).parent / "fixtures/fusion_contracts"


def rows(capture, kind):
    return [row for row in kernel_rows(FIXTURES / f"{capture}.csv") if row.kind == kind]


@pytest.mark.parametrize("capture,tokens,topk", [
    ("a3_v4f", 4096, 512), ("a3_v4pro", 1024, 1024),
])
def test_quant_indexer_retains_scales_native_identity_and_selection_output(capture, tokens, topk):
    row = rows(capture, "VllmAscendQuantLightningIndexerV2")[0]
    contract = observed_fusion_contract(row)
    assert contract == (
        "quant_lightning_indexer_active", row.kind,
        (((tokens, 64, 128), "int8", "ND"), ((tokens, 64), "fp16", "ND"),
         ((tokens, 64), "fp16", "ND")),
        (((1, 128), "int8", "ND"), ((1,), "fp16", "ND")),
        ((tokens, 1, topk), "int32", "ND"),
    )
    assert observed_fusion_contract(replace(row, kind="LightningIndexer")) is None
    wrong = replace(row, input_shapes=(*row.input_shapes[:3], (tokens, 32),
                                       *row.input_shapes[4:]))
    assert observed_fusion_contract(wrong) is None
    assert fusion_contract_diagnostic(wrong)["reason"] == "unsupported_quant_indexer_active_geometry"
    candidate = replace(row, input_shapes=(*row.input_shapes[:13], (tokens, 1, topk)),
                        input_dtypes=(*row.input_dtypes[:13], "INT32"),
                        input_formats=(*row.input_formats[:13], "ND"))
    assert observed_fusion_contract(candidate) is None
    assert fusion_contract_diagnostic(candidate)["reason"] == "candidate_indexer_boundary_unsupported"


@pytest.mark.parametrize("capture,tokens,hidden", [
    ("a3_v4f", 4096, 4096), ("a3_v4pro", 1024, 7168),
])
def test_hyper_connection_preserves_pre_and_post_distinct_boundaries(capture, tokens, hidden):
    pre = rows(capture, "HcPre")[0]
    post = rows(capture, "HcPost")[0]
    pre_contract = observed_fusion_contract(pre)
    assert pre_contract == (
        "hyper_connection_active", "HcPre",
        (((tokens, 4, hidden), "bf16", "ND"), ((24, 4 * hidden), "fp32", "ND"),
         ((3,), "fp32", "ND"), ((24,), "fp32", "ND")),
        (((tokens, hidden), "bf16", "ND"), ((tokens, 4), "fp32", "ND"),
         ((tokens, 4, 4), "fp32", "ND")),
    )
    post_contract = observed_fusion_contract(post)
    assert post_contract[1] == "HcPost"
    assert post_contract[2][1] == pre_contract[2][0]
    assert post_contract[3] == (pre_contract[2][0],)
    wrong = replace(post, input_shapes=((2, tokens // 2, hidden), *post.input_shapes[1:]))
    assert observed_fusion_contract(wrong) is None
    assert fusion_contract_diagnostic(wrong)["reason"] == "inconsistent_hyper_connection_geometry"
    premix = replace(pre, input_shapes=(*pre.input_shapes[:4], (tokens, 24)),
                     input_dtypes=(*pre.input_dtypes[:4], "FLOAT"),
                     input_formats=(*pre.input_formats[:4], "ND"))
    assert observed_fusion_contract(premix) is None
    assert fusion_contract_diagnostic(premix)["reason"] == "precomputed_hyper_connection_mix"


def test_compressor_projection_keeps_ratio_width_precision_but_not_reserved_rows():
    captures = rows("a3_v4f", "Compressor")
    contracts = [observed_fusion_contract(row) for row in captures]
    assert all(contract is not None for contract in contracts)
    assert {(contract[3][2][0], contract[-1][0]) for contract in contracts} == {
        ((4, 1024), (512,)), ((4, 256), (128,)), ((128, 512), (512,)),
    }
    row = captures[0]
    assert contracts[0][3][-1] == ((512,), "fp32", "ND")
    resized = replace(
        row, duration_ns=row.duration_ns * 100,
        input_shapes=(*row.input_shapes[:6], (2000, 64), (2000, 64), *row.input_shapes[8:]),
        output_shapes=((2000, 512), row.output_shapes[1]))
    assert native_tensor_contract(resized) != native_tensor_contract(row)
    assert observed_fusion_contract(resized) == contracts[0]
    assert "reserved_output_rows" in fusion_contract_scope(row)["not_compared"]
    bad = replace(row, input_shapes=(*row.input_shapes[:4], (4, 512), *row.input_shapes[5:]))
    assert observed_fusion_contract(bad) is None
    assert fusion_contract_diagnostic(bad)["reason"] == "inconsistent_compressor_active_geometry"


@pytest.mark.parametrize("kind,reason", [
    ("ChunkKdaFwd", "stage_dispatch_unobserved"),
    ("AttnResFwd", "active_view_or_stride_unobserved"),
])
def test_backing_allocations_and_multilaunch_stages_do_not_claim_whole_subgraph(kind, reason):
    row = rows("a5_kimi_k3", kind)[0]
    assert native_tensor_contract(row) is not None
    assert observed_fusion_contract(row) is None
    assert fusion_contract_diagnostic(row)["reason"] == reason
    assert fusion_contract_scope(row)["compared"] == []


def test_recurrent_kda_compares_real_gate_parameters_without_reshaping_qkv_backing():
    row = rows("a5_kimi_k3", "RecurrentKda")[0]
    contract = observed_fusion_contract(row)
    assert contract == (
        "recurrent_kda_parameters_active", "RecurrentKda",
        (((1, 1, 12, 128), "bf16", "ND"), ((1, 1, 12), "fp32", "ND"),
         ((12,), "fp32", "ND"), ((1536,), "fp32", "ND")),
        (("bf16", "ND"),) * 3, ("fp32", "ND"), ("bf16", "ND"),
    )
    resized = replace(row, input_shapes=((9216,), (9216,), (9216,), *row.input_shapes[3:]))
    assert observed_fusion_contract(resized) == contract
    assert native_tensor_contract(resized) != native_tensor_contract(row)
    assert "query_key_value_active_shapes" in fusion_contract_scope(row)["not_compared"]
    wrong = replace(row, input_shapes=(*row.input_shapes[:8], (24,), row.input_shapes[9]))
    assert observed_fusion_contract(wrong) is None
    assert fusion_contract_diagnostic(wrong)["reason"] == "unsupported_recurrent_parameter_geometry"


@pytest.mark.parametrize("kind", ["HcPre", "HcPost", "Compressor",
                                 "VllmAscendQuantLightningIndexerV2"])
def test_missing_capture_fields_remain_missing_and_scope_is_safe(kind):
    row = rows("a3_v4f", kind)[0]
    missing = replace(row, input_shapes=None)
    assert observed_fusion_contract(missing) is None
    assert fusion_contract_diagnostic(missing)["category"] == "capture_metadata_missing"
    assert fusion_contract_scope(missing)["occurrence_identity"] is False
    wrong_format = replace(row, input_formats=("NCL", *row.input_formats[1:]))
    assert observed_fusion_contract(wrong_format) is None
    truncated = replace(row, input_shapes=row.input_shapes[:2],
                        input_dtypes=row.input_dtypes[:2], input_formats=row.input_formats[:2])
    assert observed_fusion_contract(truncated) is None
    assert fusion_contract_diagnostic(truncated)["reason"] == "unsupported_native_tensor_slots"


@pytest.mark.parametrize("capture,kind,geometry,precision", [
    ("a3_v4f", "GroupedMatmulSwigluQuant", (32, 4096, 2048), ("int8", "int8", "int8")),
    ("a3_qwen35", "GroupedMatmulSwigluQuant", (256, 2048, 128), ("int8", "int8", "int8")),
    ("a3_glm53_prefill", "GroupedMatmulSwigluQuantV2", (256, 6144, 256), ("int8", "int4", "int8")),
    ("a3_v4pro", "GroupedMatmulSwigluQuantV2", (24, 7168, 3072), ("int8", "int4", "int8")),
])
def test_grouped_ffn_parameters_do_not_turn_actual_routing_into_declared_load(
    capture, kind, geometry, precision,
):
    row = rows(capture, kind)[0]
    contract = observed_fusion_contract(row)
    assert contract == ("grouped_mlp_parameters_active", kind, geometry, precision)
    # The same expert parameters can receive a different actual routing load.
    input_shapes = list(row.input_shapes)
    input_shapes[0] = (100, geometry[1])
    input_shapes[3 if kind == "GroupedMatmulSwigluQuant" else 1] = (100,)
    changed = replace(row, input_shapes=tuple(input_shapes),
                      output_shapes=((100, geometry[2]), (100,)))
    assert observed_fusion_contract(changed) == contract
    assert native_tensor_contract(changed) != native_tensor_contract(row)
    assert "routed_token_count" in fusion_contract_scope(row)["not_compared"]
    broken = replace(row, output_shapes=((row.output_shapes[0][0], geometry[2] // 2),
                                        row.output_shapes[1]))
    assert observed_fusion_contract(broken) is None
    missing = replace(row, input_shapes=((), *row.input_shapes[1:]))
    assert fusion_contract_diagnostic(missing)["missing_fields"] == ["input[0].shape"]


def test_dequant_swiglu_and_norm_mx_keep_auxiliary_precision_and_optional_branches():
    row = rows("a3_glm53_prefill", "DequantSwigluQuant")[0]
    assert observed_fusion_contract(row) == (
        "dequant_swiglu_quant_active", "DequantSwigluQuant",
        ((4096, 512), "int32", "ND"), ((512,), "fp32", "ND"),
        ((4096,), "fp32", "ND"), ((4096, 256), "int8", "ND"),
        ((4096,), "fp32", "ND"),
    )
    bias = replace(row, input_shapes=(*row.input_shapes[:3], (512,), *row.input_shapes[4:]),
                   input_dtypes=(*row.input_dtypes[:3], "FLOAT", *row.input_dtypes[4:]),
                   input_formats=(*row.input_formats[:3], "ND", *row.input_formats[4:]))
    assert observed_fusion_contract(bias) is None
    assert fusion_contract_diagnostic(bias)["reason"] == "dequant_swiglu_optional_boundary_unsupported"
    norm = rows("a5_kimi_k3", "RmsNormDynamicMxQuant")[0]
    assert observed_fusion_contract(norm) == (
        "rmsnorm_mxquant_active", "RmsNormDynamicMxQuant",
        ((1024, 3584), "bf16", "ND"), ((3584,), "bf16", "ND"),
        ((1024, 3584), "fp8_e4m3", "ND"), ((1024, 56, 2), "fp8_e8m0", "NCL"),
    )
    changed_scale = replace(norm, output_formats=("ND", "ND", norm.output_formats[2]))
    assert observed_fusion_contract(changed_scale) is None


@pytest.mark.parametrize("capture,tokens", [("a3_glm53_prefill", 4096), ("a3_glm53_decode", 1)])
def test_int8_dynamic_quant_does_not_alias_mx_or_drop_the_affine_norm_input(capture, tokens):
    row = rows(capture, "DynamicQuant")[0]
    assert observed_fusion_contract(row) == (
        "dynamic_quant_active", "DynamicQuant", ((tokens, 6144), "bf16", "ND"),
        ((tokens, 6144), "int8", "ND"), ((tokens,), "fp32", "ND"),
    )
    mx = replace(row, output_dtypes=("DT_FLOAT8_E4M3FN", "DT_FLOAT8_E8M0"))
    assert observed_fusion_contract(mx) is None
    norm = rows(capture, "AddRmsNormDynamicQuant")[0]
    contract = observed_fusion_contract(norm)
    assert contract == (
        "add_rmsnorm_dynamic_quant_active", norm.kind,
        (((tokens, 6144), "bf16", "ND"), ((tokens, 6144), "bf16", "ND"),
         ((6144,), "bf16", "ND"), ((6144,), "bf16", "ND")),
        (((tokens, 6144), "int8", "ND"), ((tokens, 6144), "bf16", "ND"),
         ((tokens,), "fp32", "ND")),
    )
    no_affine = replace(norm, input_shapes=norm.input_shapes[:3], input_dtypes=norm.input_dtypes[:3],
                        input_formats=norm.input_formats[:3])
    assert observed_fusion_contract(no_affine) != contract
    assert observed_fusion_contract(no_affine)[2][-1] == ((), None, None)
    other_mask = replace(norm, output_shapes=(norm.output_shapes[0], (tokens, 6144),
                                             *norm.output_shapes[2:]))
    assert observed_fusion_contract(other_mask) is None


def test_rmsnorm_cast_preserves_both_actual_output_precisions():
    row = rows("a3_v4f", "RmsNormCast")[0]
    assert observed_fusion_contract(row) == native_tensor_contract(row)
    missing_output = replace(row, output_shapes=(row.output_shapes[0], ()))
    assert observed_fusion_contract(missing_output) is None
    assert fusion_contract_diagnostic(missing_output)["missing_fields"] == ["output[1].shape"]
    wrong = replace(row, output_dtypes=(row.output_dtypes[0], row.output_dtypes[0]))
    assert observed_fusion_contract(wrong) is None
