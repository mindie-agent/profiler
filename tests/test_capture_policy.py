"""Retained command declarations correct graph replay and padding boundaries.

[Role] Import actual recorded capture keys through a non-executing parser.
[Invariants] Source bytes, non-graph declarations and missing facts survive.
[Timeouts & Locks] Small local command files and pure target lowering only.
[Side-Effect Policy] All command variants and runtime homes live in tmp_path.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from capture_policy import import_capture_policy

FIXTURES = ROOT / "tests" / "fixtures" / "native_observations"


def test_retained_literal_policy_restores_q12_and_excludes_q64_graph_capture(tmp_path):
    from mindie_sim import target_operators

    raw = json.loads((FIXTURES / "a5_qwen35_tp4_q4_b7.json").read_text())["raw_case"]
    original = deepcopy(raw)
    before = (FIXTURES / "a5_qwen35_mtp_cmd.sh").read_bytes()
    command = tmp_path / "cmd.sh"
    command.write_bytes(before)
    # A caller supplies the selected retained command rather than a model-name lookup.
    imported, provenance = import_capture_policy(raw, capture_path=command)
    assert provenance["status"] == "applied"
    assert imported["runtime"]["graph_capture_keys"] == [1, 2, 4, 8, 12, 16, 24, 32]
    assert imported["runtime"]["kernels"] == original["runtime"]["kernels"]
    assert imported["runtime"]["metadata"]["captured_additional_config"] == {
        "ascend_fusion_config": {"fusion_ops_gmmswigluquant": False}, "enable_force_eplb": True}
    assert imported["model"] == original["model"] and raw == original
    assert command.read_bytes() == before
    for sequences, physical, scope in ((3, 12, "full"), (7, 32, "full"), (16, 64, "none")):
        ops = target_operators(imported, phase="decode", tokens=4, context=196608, sequences=sequences)
        recurrence = next(op for op in ops if op.recipe == "ascend_recurrent_gdn_fp32_state")
        assert recurrence.local_shape[0] == 4 * sequences
        assert recurrence.padded_shape[0] == physical
        assert dict(recurrence.metadata)["graph_replay_scope"] == scope


def test_missing_capture_fields_are_unprovided_and_do_not_guess_policy(tmp_path):
    raw = {"runtime": {"graph_mode": "none", "graph_capture_keys": [4, 8],
                       "kernels": {"moe_token_partition": {"kind": "vllm_ascend_mc2_tp_slice"}}}}
    capture = tmp_path / "capture" / "kernel_details.csv"
    result, provenance = import_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["status"] == "not_provided"
    capture.parent.mkdir()
    (capture.parent / "cmd.sh").write_text("vllm serve retained-model --dtype bfloat16\n")
    result, provenance = import_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["status"] == "not_provided"
    (capture.parent / "cmd.sh").write_text(
        "vllm serve retained-model --compilation-config='{}'\n")
    result, provenance = import_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["reason"] == "graph_policy_fields_not_declared"


@pytest.mark.parametrize("value", ("$UNRESOLVED_CAPTURE_CONFIG", "$(touch should-not-run)"))
def test_dynamic_shell_values_are_not_executed_or_treated_as_literal_config(tmp_path, value):
    command = tmp_path / "cmd.sh"
    command.write_text(f"vllm serve retained-model --compilation-config '{value}'\n")
    with pytest.raises(ValueError, match="requires_literal_json"):
        import_capture_policy({}, capture_path=command)
    assert not (tmp_path / "should-not-run").exists()


def test_multiple_compilation_declarations_require_resolution(tmp_path):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --compilation-config '{}' --compilation-config '{}'\n")
    with pytest.raises(ValueError, match="ambiguous_multiple_declarations"):
        import_capture_policy({}, capture_path=command)


def test_unrepresented_mixed_capture_mode_is_reported_without_changing_input(tmp_path):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --compilation-config "
                       "'{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\",\"cudagraph_capture_sizes\":[4,8]}'\n")
    raw = {"runtime": {"graph_mode": "none"}}
    result, provenance = import_capture_policy(raw, capture_path=command)
    assert result == raw and provenance["status"] == "unsupported"


def test_retained_a3_capture_path_corrects_physical_rows_through_common_adapter(tmp_path, monkeypatch):
    from mindie_sim import target_operators
    import wave5_generalization_eval as wave5

    fixture = json.loads((FIXTURES / "a3_qwen35_tp8_q1_b1.json").read_text())
    command = tmp_path / "cmd.sh"
    command.write_bytes((FIXTURES / "a3_qwen35_cmd.sh").read_bytes())
    capture = tmp_path / "kernel_details.csv"
    module = ModuleType("eval_a3_wave5")
    module._unadapted_parse_capture_traits = lambda path: fixture["traits"]
    raw = fixture["raw"]
    segmentation = {"source": "retained_capture"}
    module._unadapted_resolve_template = lambda traits: ("retained", raw, segmentation, False)
    module._capture_policy_imports = {}
    monkeypatch.setitem(sys.modules, "eval_a3_wave5", module)
    traits = wave5._capture_traits("a3", capture)
    resolved = wave5._resolve_capture_template("a3", traits)
    assert resolved[0] == "retained" and resolved[2:] == (segmentation, False)
    assert traits["capture_path"] == str(capture)
    assert module._capture_policy_imports[str(capture)]["command_sha256"] == fixture["source_command"]["sha256"]
    assert raw == fixture["raw"]
    # CSV rows 69/73 have a single physical input row for both native kernels.
    assert {row["csv_line"] for row in fixture["native_row_evidence"]} == {69, 73}
    for declared, physical in ((raw, 4), (resolved[1], 1)):
        ops = target_operators(declared, phase="decode", tokens=1, context=4096, sequences=1)
        convolution = next(op for op in ops if op.recipe == "ascend_causal_conv1d_update")
        assert convolution.local_shape[0] == 1
        assert convolution.padded_shape[0] == physical
        assert dict(convolution.metadata)["graph_physical_query_rows"] == physical


def test_literal_caller_conditions_do_not_invent_missing_graph_fields(tmp_path):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --additional-config "
                       "'{\"enable_force_eplb\":false}'\n")
    raw = {"runtime": {"graph_mode": "none", "graph_capture_keys": [4, 8],
                       "kernels": {"moe_token_partition": {"kind": "vllm_ascend_mc2_tp_slice"}}}}
    result, provenance = import_capture_policy(raw, capture_path=command)
    assert result["runtime"]["graph_mode"] == "none"
    assert result["runtime"]["graph_capture_keys"] == [4, 8]
    assert result["runtime"]["metadata"]["captured_additional_config"] == {"enable_force_eplb": False}
    assert provenance["status"] == "partially_provided"
    assert provenance["provided_fields"] == ["additional_config"]
    assert provenance["missing_fields"] == ["cudagraph_capture_sizes", "cudagraph_mode"]
    assert result["runtime"]["kernels"] == raw["runtime"]["kernels"]
    assert "source_conditions" not in provenance


@pytest.mark.parametrize("capture_index", [0, 1], ids=["q1", "q4"])
def test_retained_a3_mc2_alignment_is_local_to_prepare(tmp_path, capture_index):
    from mindie_sim import target_operators

    fixture = json.loads((FIXTURES / "a3_dsv4f_mc2_padding.json").read_text())
    capture = fixture["captures"][capture_index]
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = tmp_path / "cmd.sh"
    command.write_bytes((FIXTURES / "a3_dsv4f_mc2_cmd.sh").read_bytes())
    result, provenance = import_capture_policy(raw, capture_path=command)
    assert raw == original
    assert result["model"] == original["model"]
    assert result["runtime"]["graph_capture_keys"] == [1, 2, 4, 8, 16, 32]
    assert result["runtime"]["kernels"]["moe_token_partition"]["padding"] == "right_to_tp"
    assert provenance["command_sha256"] == fixture["captures"][0]["source_command"]["sha256"]
    condition, = provenance["source_conditions"]
    assert condition["source"]["revision"] == fixture["source_revision"]
    assert condition["source"]["capture_binary_identity"] == "unknown"
    assert set(provenance["captured_fields"]) == {"cudagraph_mode", "cudagraph_capture_sizes"}

    def shapes(row, key):
        return tuple(tuple(int(n) for n in item.split(",")) if item else ()
                     for item in row[key].strip('"').split(";"))

    # Retained PadV3 and the source-selected generic materialization have the
    # same row boundary; this does not assert binary/kernel equivalence.
    evidence = capture["native_row_evidence"]
    native_router = next(row for row in evidence if row["Type"] == "MatMulV2")
    native_shared = next(row for row in evidence if row["Type"] == "QuantBatchMatmulV3")
    native_dispatch = next(row for row in evidence if row["Type"] == "MoeDistributeDispatchV2")
    native_pads = [row for row in evidence if row["Type"] == "PadV3"]
    ops = [op for op in target_operators(result, **capture["geometry"]) if op.layer == 0]
    by_recipe = {op.recipe: op for op in ops}
    rows = capture["geometry"]["sequences"]
    assert shapes(native_router, "Input Shapes")[0][0] == rows
    assert by_recipe["router"].local_shape[0] == rows
    assert by_recipe["dense_gate_up"].local_shape[0] == shapes(native_shared, "Input Shapes")[0][0] == rows
    assert {dict(op.metadata)["graph_physical_query_rows"] for op in ops} == {rows}
    pads = [op for op in ops if op.recipe == "tensor_concat"]
    assert len(pads) == len(native_pads) == 2
    for op, native in zip(pads, native_pads):
        assert dict(op.metadata)["input_shapes"][0] == shapes(native, "Input Shapes")[0]
        assert op.local_shape == shapes(native, "Output Shapes")[0]
        assert op.local_shape[0] == fixture["expected"]["moe_allocated_rows"]
    partition = dict(by_recipe["route_pack"].metadata)["moe_token_partition"]
    assert partition["full_rows"] == partition["valid_rows"] == rows
    assert partition["allocated_rows"] == 8
    assert partition["local_rows"] == shapes(native_dispatch, "Input Shapes")[0][0] == 1
    assert partition["valid_rows_per_rank"] == (1,) * rows + (0,) * (8 - rows)


@pytest.mark.parametrize("caller", [
    None,
    {"kind": "vllm_ascend_alltoall_tp_slice"},
    {"kind": "vllm_ascend_mc2_tp_slice", "padding": "none"},
    {"kind": "vllm_ascend_mc2_tp_slice", "padding": "right_to_tp"},
])
def test_captured_graph_fields_preserve_explicit_or_other_caller_alignment(tmp_path, caller):
    command = tmp_path / "cmd.sh"
    command.write_bytes((FIXTURES / "a3_dsv4f_mc2_cmd.sh").read_bytes())
    kernels = {"moe_token_partition": caller} if caller is not None else {}
    raw = {"runtime": {"kernels": kernels}}
    result, provenance = import_capture_policy(raw, capture_path=command)
    assert result["runtime"]["kernels"] == kernels
    assert "source_conditions" not in provenance
