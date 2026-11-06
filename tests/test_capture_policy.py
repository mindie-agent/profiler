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
    raw = {"runtime": {"graph_mode": "none", "graph_capture_keys": [4, 8]}}
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
    raw = {"runtime": {"graph_mode": "none", "graph_capture_keys": [4, 8]}}
    result, provenance = import_capture_policy(raw, capture_path=command)
    assert result["runtime"]["graph_mode"] == "none"
    assert result["runtime"]["graph_capture_keys"] == [4, 8]
    assert result["runtime"]["metadata"]["captured_additional_config"] == {"enable_force_eplb": False}
    assert provenance["status"] == "partially_provided"
    assert provenance["provided_fields"] == ["additional_config"]
    assert provenance["missing_fields"] == ["cudagraph_capture_sizes", "cudagraph_mode"]
