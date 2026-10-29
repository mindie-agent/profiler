"""Native fusion contracts retain real A3/A5 slots and reject partial exports."""
from dataclasses import replace
from pathlib import Path

import pytest

from mindie_profiler.body_fused_contracts import (
    KIMI_NORM_GATE,
    NORM_GATE,
    QKV_NORM_ROPE,
    fused_contract_diagnostic,
    fused_contract_scope,
    observed_fused_contract,
)
from mindie_profiler.normalized import kernel_rows, row_from_event


FIXTURES = Path(__file__).parent / "fixtures/body_fused"


def captured_rows(label):
    return list(kernel_rows(FIXTURES / f"{label}.csv"))


@pytest.mark.parametrize("label,rows", [
    ("a3_qwen35", 65536),
    ("a3_qwen36", 98304),
    ("a5_qwen38", 786432),
])
def test_norm_gate_native_slots_include_gate_weight_and_fp32_statistics(label, rows):
    row = next(r for r in captured_rows(label) if r.kind == NORM_GATE and r.input_shapes)
    x = ((rows, 128), "bf16", "ND")
    assert observed_fused_contract(row) == (
        "native_tensor_abi", NORM_GATE,
        (x, ((128,), "bf16", "ND"), x),
        (x, ((rows,), "fp32", "ND")),
    )
    shifted = row_from_event(replace(
        row.event, start_ns=row.event.start_ns + 100, end_ns=row.event.end_ns + 200))
    assert observed_fused_contract(shifted) == observed_fused_contract(row)
    diagnostic = fused_contract_diagnostic(row)
    assert {"eps", "norm_before_gate", "is_rms_norm"} <= set(diagnostic["unobserved_fields"])
    assert "scalar_flags_and_tensor_values_not_observed" in fused_contract_scope(row)["comparison_scope"]


@pytest.mark.parametrize("label", ["a3_qwen35", "a3_qwen36", "a5_qwen38"])
def test_qkv_fusion_single_output_is_incomplete_not_an_inferred_q_or_gate(label):
    row = next(r for r in captured_rows(label) if r.kind == QKV_NORM_ROPE and r.input_shapes)
    assert len(row.input_shapes) == 4 and len(row.output_shapes) == 1
    assert observed_fused_contract(row) is None
    diagnostic = fused_contract_diagnostic(row)
    assert diagnostic["category"] == "capture_metadata_missing"
    assert diagnostic["reason"] == "incomplete_native_tensor_slots"
    assert diagnostic["observed_output_slots"] == 1
    assert diagnostic["required_output_slots"] == 4
    assert len(diagnostic["captured_descriptor"][3]) == 1
    assert "output_slot_identity" in diagnostic["unobserved_fields"]
    scope = fused_contract_scope(row)
    assert scope["observed_output_slots"] == 1 and scope["required_output_slots"] == 4
    assert "no_contract_equality" in scope["comparison_scope"]


@pytest.mark.parametrize("label,width", [("a3_qwen35", 2048), ("a3_qwen36", 5120)])
def test_gemma_and_optional_bias_preserve_distinct_native_abi(label, width):
    rows = {row.kind: row for row in captured_rows(label)
            if row.input_shapes and row.kind in {"GemmaRmsNorm", "AddRmsNormBias"}}
    x, weight = ((8192, width), "bf16", "ND"), ((width,), "bf16", "ND")
    stats = ((8192, 1), "fp32", "ND")
    assert observed_fused_contract(rows["GemmaRmsNorm"]) == (
        "native_tensor_abi", "GemmaRmsNorm", (x, weight), (x, stats))
    assert observed_fused_contract(rows["AddRmsNormBias"]) == (
        "native_tensor_abi", "AddRmsNormBias",
        (x, x, weight, ((), None, None)), (x, stats, x))


@pytest.mark.parametrize("label,rows", [("a3_glm53_prefill", 4096), ("a3_glm53_decode", 1)])
def test_glm_affine_beta_is_preserved_as_a_real_native_input(label, rows):
    path = FIXTURES.parent / "fusion_contracts" / f"{label}.csv"
    row = next(row for row in kernel_rows(path) if row.kind == "AddRmsNormBias")
    x, affine = ((rows, 6144), "bf16", "ND"), ((6144,), "bf16", "ND")
    assert observed_fused_contract(row) == (
        "native_tensor_abi", "AddRmsNormBias", (x, x, affine, affine),
        (x, ((rows, 1), "fp32", "ND"), x))
    invalid = row_from_event(replace(row.event, input_shapes=f"{rows},6144;{rows},6144;6144;3072"))
    assert observed_fused_contract(invalid) is None


def test_kimi_situ_mx_preserves_both_phases_and_excludes_unrecorded_activation_parameters():
    path = FIXTURES.parent / "fusion_contracts/a5_kimi_k3.csv"
    rows = [row for row in kernel_rows(path) if row.kind == "SituMxQuant"]
    assert {row.input_shapes[0][0] for row in rows} == {1, 8192}
    for row in rows:
        tokens = row.input_shapes[0][0]
        assert observed_fused_contract(row) == (
            "situ_mxquant_active", "SituMxQuant",
            ((tokens, 1536), "bf16", "ND"), ((tokens, 768), "fp8_e4m3", "ND"),
            ((tokens, 12, 2), "fp8_e8m0", "ND"))
        scope = fused_contract_scope(row)
        assert {"beta", "linear_beta", "activate_left"} <= set(scope["unobserved_fields"])
        altered = row_from_event(replace(
            row.event, output_shapes=f"{tokens},768;{tokens},24,2"))
        assert observed_fused_contract(altered) is None

@pytest.mark.parametrize("label", ["a3_qwen35", "a3_qwen36", "a5_qwen38"])
def test_absent_fused_rows_never_inherit_tensors_from_other_invocations(label):
    rows = [r for r in captured_rows(label) if not r.input_shapes]
    assert {r.kind for r in rows} == {NORM_GATE, QKV_NORM_ROPE}
    for row in rows:
        assert row.event.input_shapes == row.event.output_shapes == "N/A"
        assert observed_fused_contract(row) is None
        assert fused_contract_diagnostic(row)["category"] == "capture_metadata_missing"


def test_norm_gate_rejects_incompatible_statistics_descriptor():
    row = next(r for r in captured_rows("a5_qwen38") if r.kind == NORM_GATE and r.input_shapes)
    altered = row_from_event(replace(row.event, output_dtypes="DT_BF16;DT_BF16"))
    assert observed_fused_contract(altered) is None
    assert fused_contract_diagnostic(altered)["reason"] == "unsupported_tensor_contract"


def test_kimi_norm_gate_compares_wrapper_rows_without_inventing_auxiliary_outputs():
    row = captured_rows("kimi_a5_norm_gate")[0]
    assert row.kind == KIMI_NORM_GATE
    assert row.input_shapes == ((1, 8192, 12, 128), (8192, 12, 128), (128,))
    assert row.output_shapes == ((1, 8192, 12, 128),)
    assert observed_fused_contract(row) == (
        "gated_norm_active_rows", KIMI_NORM_GATE,
        ((98304, 128), "bf16", "ND"), ((128,), "bf16", "ND"))
    shifted = row_from_event(replace(
        row.event, start_ns=row.event.start_ns + 100, end_ns=row.event.end_ns + 500))
    assert observed_fused_contract(shifted) == observed_fused_contract(row)
    scope = fused_contract_scope(row)
    assert "no_full_native_abi_equality" in scope["comparison_scope"]
    assert {"eps", "gate_activation", "is_rms_norm", "rstd", "bias", "residual"} <= set(
        scope["unobserved_fields"])


def test_kimi_norm_gate_absent_decode_metadata_stays_missing():
    row = captured_rows("kimi_a5_norm_gate")[1]
    assert row.event.input_shapes == row.event.output_shapes == "N/A"
    assert observed_fused_contract(row) is None
    assert fused_contract_diagnostic(row)["category"] == "capture_metadata_missing"


def test_kimi_norm_gate_requires_matching_gate_width_and_primary_output():
    row = captured_rows("kimi_a5_norm_gate")[0]
    wrong_gate = row_from_event(replace(
        row.event, input_shapes='"1,8192,12,128;8192,24,64;128"'))
    wrong_output = row_from_event(replace(
        row.event, output_shapes='"8192,12,128"'))
    for altered in (wrong_gate, wrong_output):
        assert observed_fused_contract(altered) is None
        assert fused_contract_diagnostic(altered)["category"] == "contract_support_gap"
