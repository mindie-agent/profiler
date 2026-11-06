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

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from a5_capture_policy import import_a5_capture_policy

FIXTURES = ROOT / "tests" / "fixtures" / "native_observations"


def test_retained_literal_policy_restores_q12_and_excludes_q64_graph_capture(tmp_path):
    from mindie_sim import target_operators

    raw = json.loads((FIXTURES / "a5_qwen35_tp4_q4_b7.json").read_text())["raw_case"]
    original = deepcopy(raw)
    before = (FIXTURES / "a5_qwen35_mtp_cmd.sh").read_bytes()
    command = tmp_path / "cmd.sh"
    command.write_bytes(before)
    # A caller supplies the selected retained command rather than a model-name lookup.
    imported, provenance = import_a5_capture_policy(raw, capture_path=command)
    assert provenance["status"] == "applied"
    assert imported["runtime"]["graph_capture_keys"] == [1, 2, 4, 8, 12, 16, 24, 32]
    assert imported["runtime"]["kernels"] == original["runtime"]["kernels"]
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
    result, provenance = import_a5_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["status"] == "not_provided"
    capture.parent.mkdir()
    (capture.parent / "cmd.sh").write_text("vllm serve retained-model --dtype bfloat16\n")
    result, provenance = import_a5_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["status"] == "not_provided"
    (capture.parent / "cmd.sh").write_text(
        "vllm serve retained-model --compilation-config='{}'\n")
    result, provenance = import_a5_capture_policy(raw, capture_path=capture)
    assert result == raw and provenance["reason"] == "graph_policy_fields_not_declared"


@pytest.mark.parametrize("value", ("$UNRESOLVED_CAPTURE_CONFIG", "$(touch should-not-run)"))
def test_dynamic_shell_values_are_not_executed_or_treated_as_literal_config(tmp_path, value):
    command = tmp_path / "cmd.sh"
    command.write_text(f"vllm serve retained-model --compilation-config '{value}'\n")
    with pytest.raises(ValueError, match="requires_literal_json"):
        import_a5_capture_policy({}, capture_path=command)
    assert not (tmp_path / "should-not-run").exists()


def test_multiple_compilation_declarations_require_resolution(tmp_path):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --compilation-config '{}' --compilation-config '{}'\n")
    with pytest.raises(ValueError, match="ambiguous_multiple_declarations"):
        import_a5_capture_policy({}, capture_path=command)


def test_unrepresented_mixed_capture_mode_is_reported_without_changing_input(tmp_path):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --compilation-config "
                       "'{\"cudagraph_mode\":\"FULL_AND_PIECEWISE\",\"cudagraph_capture_sizes\":[4,8]}'\n")
    raw = {"runtime": {"graph_mode": "none"}}
    result, provenance = import_a5_capture_policy(raw, capture_path=command)
    assert result == raw and provenance["status"] == "unsupported"
