"""Literal deployment flags correct offline replay topology without timing evidence.

[Role] Exercise the retained command parser and the DP1/EP=TP MoE correction.
[Invariants] Only actual physical topology changes; graph rows, service rules and
  explicit caller/native declarations keep their source meaning.
[Timeouts & Locks] Small local command files and pure target lowering only.
[Side-Effect Policy] All command variants and runtime homes live in tmp_path.
"""
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "structure"))
from capture_policy import _native_protocol_conflicts, import_capture_policy
from mindie_profiler.events import ProfilerSchemaError

FIXTURES = ROOT / "tests" / "fixtures" / "native_observations"
E32 = FIXTURES / "a3_qwen35_e32_ep8_source.json"
E32_COMMAND = FIXTURES / "a3_qwen35_e32_ep8_cmd.sh"
E32_STRUCTURAL = FIXTURES / "a3_qwen35_e32_ep8_structural.csv"
E32_STRUCTURAL_SIDECAR = FIXTURES / "a3_qwen35_e32_ep8_structural.json"
DSV4F = FIXTURES / "a3_dsv4f_mc2_padding.json"
DSV4F_COMMAND = FIXTURES / "a3_dsv4f_mc2_cmd.sh"
DSV4F_STRUCTURAL = FIXTURES / "a3_dsv4f_mc2_structural.csv"
DSV4F_STRUCTURAL_SIDECAR = FIXTURES / "a3_dsv4f_mc2_structural.json"
DSV4F_Q4_COMMAND = FIXTURES / "a3_dsv4f_mc2_q4_cmd.sh"
DSV4F_Q4_STRUCTURAL = FIXTURES / "a3_dsv4f_mc2_q4_structural.csv"
DSV4F_Q4_STRUCTURAL_SIDECAR = FIXTURES / "a3_dsv4f_mc2_q4_structural.json"


def _command(tmp_path, source, structural=None):
    target = tmp_path / "cmd.sh"
    target.write_bytes(source.read_bytes())
    if structural is not None:
        (tmp_path / "kernel_details.csv").write_bytes(structural.read_bytes())
    return target


def _layer0(ops, recipe):
    matches = [op for op in ops if op.layer == 0 and op.recipe == recipe]
    assert len(matches) == 1, recipe
    return matches[0]


def test_retained_e32_command_restores_ep8_local4_width512_and_keeps_graph_rows(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND)
    command_bytes = command.read_bytes()
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original and command.read_bytes() == command_bytes
    assert fixture["source_capture"]["sha256"] == (
        "bdd6a2022358f29c60b586da3f17ab0c677df0fed10734219e40d091cf0933e1")
    assert fixture["source_command"]["sha256"] == (
        "dda2cdc32a526c279b66b84b069024be6fe5a515cf126ba3f78722d19afc21a0")
    assert fixture["source_command"]["size_bytes"] == 741
    assert {row["csv_line"] for row in fixture["source_rows"]} == {80, 82, 84, 86, 87, 88, 89}
    assert provenance["command_sha256"] == fixture["source_command"]["sha256"]
    assert provenance["provided_fields"] == ["cudagraph_capture_sizes", "cudagraph_mode"]
    assert provenance["missing_fields"] == []
    deployment = provenance["deployment"]
    assert deployment["status"] == "applied"
    assert deployment["declared"] == {"tensor_parallel_size": 8,
                                      "data_parallel_size": 1,
                                      "expert_parallel": True}
    assert deployment["missing"] == []
    assert deployment["derived"] == {
        "ep": 8,
        "basis": "declared_dp1_tp_gt1_enabled_expert_parallel_and_moe_model_imply_ep_equals_tp",
        "source": "retained_capture_command",
    }
    assert deployment["before"] == {"tp": 8, "dp": 1, "ep": 1, "pp": 1,
                                    "moe_recipe": "tp_join_reduce"}
    assert deployment["after"] == {"tp": 8, "dp": 1, "ep": 8, "pp": 1,
                                   "moe_recipe": "alltoall"}
    assert deployment["changed_fields"] == ["runtime.ep", "runtime.moe_recipe"]
    assert deployment["timing_values_used"] is False

    runtime = imported["runtime"]
    assert (runtime["tp"], runtime["dp"], runtime["ep"]) == (8, 1, 8)
    assert runtime["moe_recipe"] == "alltoall"
    assert runtime["graph_capture_keys"] == fixture["expected"]["after"]["graph_capture_keys"]
    assert runtime["kernels"]["service_regimes"] == (
        original["runtime"]["kernels"]["service_regimes"][:1])
    assert "moe_token_partition" not in runtime["kernels"]
    assert "native_moe_protocol" not in runtime["kernels"]
    assert "moe_transport" not in runtime["kernels"]
    assert provenance["native_structure"]["status"] == "not_provided"
    assert provenance["native_structure"]["reason"] == "structural_evidence_not_provided"
    assert provenance["status"] == "partially_provided"
    guard = provenance["legacy_ffn_guard"]
    assert guard["status"] == "applied"
    assert guard["removed_count"] == 6
    assert guard["kept_count"] == 1
    assert guard["source"]["command_sha256"] == fixture["source_command"]["sha256"]
    assert "kernels" in provenance["changed_fields"]
    assert str(command) not in json.dumps(imported)
    assert fixture["source_capture"]["sha256"] not in json.dumps(imported)
    source_gate = next(row for row in fixture["source_rows"] if row["csv_line"] == 87)
    source_down = next(row for row in fixture["source_rows"] if row["csv_line"] == 88)
    assert "4,32,128,16,32" in source_gate["Input Shapes"]
    assert "4,512,2048" in source_down["Input Shapes"]
    assert source_gate["Output Shapes"] == '"16,512;16"'
    assert source_down["Output Shapes"] == '"16,2048"'

    inherited_ops = target_operators(original, **fixture["geometry"])
    inherited_gate = _layer0(inherited_ops, "balanced_grouped_gate_up")
    inherited_down = _layer0(inherited_ops, "balanced_grouped_down")
    assert dict(inherited_gate.metadata)["matrix_weight_bank_groups"] == 32
    assert inherited_gate.local_shape[1] == 2 * 64
    assert inherited_down.local_shape[2] == 64

    ops = target_operators(imported, **fixture["geometry"])
    gate = _layer0(ops, "balanced_grouped_gate_up")
    down = _layer0(ops, "balanced_grouped_down")
    assert gate.local_shape == tuple(fixture["expected"]["grouped_gate_up_shape"])
    assert down.local_shape == tuple(fixture["expected"]["grouped_down_shape"])
    assert gate.local_shape[1] == 2 * 512
    assert down.local_shape[2] == 512
    assert dict(gate.metadata)["matrix_weight_bank_groups"] == 4
    assert dict(down.metadata)["matrix_weight_bank_groups"] == 4
    assert _layer0(ops, "expert_dispatch").local_shape == (2, 2048)
    assert _layer0(ops, "expert_combine").local_shape == (2, 2048)
    assert dict(_layer0(ops, "route_pack").metadata).get("moe_token_partition") is None

    for sequences, physical in ((1, 1), (4, 4)):
        ops = target_operators(imported, phase="decode", tokens=1, context=262144,
                               sequences=sequences)
        grouped = _layer0(ops, "balanced_grouped_gate_up")
        metadata = dict(grouped.metadata)
        assert metadata["graph_physical_query_rows"] == physical
        assert metadata["graph_active_query_rows"] == physical
        assert grouped.local_shape[0] == 1

    repeated, repeated_provenance = import_capture_policy(imported, capture_path=command)
    assert repeated == imported
    assert repeated_provenance["deployment"]["status"] == "unchanged"
    assert repeated_provenance["deployment"]["changed_fields"] == []
    from_original, _ = import_capture_policy(original, capture_path=command)
    assert from_original == imported


def test_retained_e32_structural_evidence_binds_mc2_and_guards_legacy_ffn(tmp_path):
    from hashlib import sha256
    from mindie_sim import target_operators

    fixture = json.loads(E32.read_text())
    sidecar = json.loads(E32_STRUCTURAL_SIDECAR.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    command_bytes = command.read_bytes()
    csv_bytes = (tmp_path / "kernel_details.csv").read_bytes()
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original and command.read_bytes() == command_bytes
    assert (tmp_path / "kernel_details.csv").read_bytes() == csv_bytes
    assert sidecar["source"]["sha256"] == fixture["source_capture"]["sha256"]
    assert {row["source_line"] for row in sidecar["rows"]} == {80, 82, 84, 86, 87, 88, 89, 90}
    assert provenance["command_sha256"] == fixture["source_command"]["sha256"]
    deployment = provenance["deployment"]
    assert deployment["status"] == "applied"
    assert deployment["derived"]["ep"] == 8
    assert deployment["before"]["ep"] == 1
    assert deployment["after"]["ep"] == 8
    assert deployment["after"]["moe_recipe"] == "alltoall"

    structure = provenance["native_structure"]
    assert structure["status"] == "consistent"
    assert structure["source"]["sha256"] == sha256(csv_bytes).hexdigest()
    assert structure["evidence"]["grouped"]["gate"]["banks"] == 4
    assert structure["evidence"]["grouped"]["gate"]["hidden"] == 2048
    assert structure["evidence"]["grouped"]["gate"]["width"] == 512
    assert structure["evidence"]["grouped"]["allocation_rows"] == 16
    assert structure["evidence"]["grouped"]["row_axis_role"] == "allocation_not_valid_work"
    assert structure["evidence"]["grouped"]["valid_routed_rows"] == "unobserved"
    prepare = structure["evidence"]["prepare"]
    assert prepare["input_rows"] == 1
    assert prepare["source_local_rows"] == 1
    assert prepare["output_rows"] == 8
    assert prepare["x_width"] == 2048
    assert prepare["logits_width"] == 32
    assert prepare["signatures"] == 2
    assert structure["evidence"]["dispatch"]["input_shapes"][0] == (1, 2048)
    assert structure["evidence"]["dispatch"]["contract"] == {
        "source_local_rows": 1, "hidden_size": 2048, "capacity_rows": 16,
        "bank_axis": 4, "expert_axis": 32, "combine_output_rows": 1,
    }
    assert structure["evidence"]["combine"]["output_shapes"][0] == (1, 2048)
    for pad in structure["evidence"]["signatures"]["pad"]:
        assert pad["input_dtypes"][1] == "INT32"
        assert pad["input_dtypes"][2] == pad["input_dtypes"][0]
        assert pad["output_dtypes"] == (pad["input_dtypes"][0],)
        assert tuple(pad["input_formats"]) == ("ND", "ND", "ND")
        assert tuple(pad["output_formats"]) == ("ND",)
    assert structure["evidence"]["allgather"]["count"] == 1
    assert structure["evidence"]["allgather"]["moe_attributed_count"] is None
    assert structure["evidence"]["allgather"]["attribution"] == "unresolved"
    assert structure["caller"]["action"] == "bound"
    assert structure["candidate"]["basis"] == (
        "hypothetical_mc2_completion_not_necessarily_selected")
    assert structure["comparison"]["basis"] == "actual_returned_graph"
    assert structure["candidate"]["selected"] is True
    assert structure["candidate"]["generated"]["roles"]["gate_up"]["banks"] == 4
    assert structure["generated"]["roles"]["gate_up"]["banks"] == 4
    assert structure["comparison"]["mismatches"] == []
    assert structure["comparison"]["gmm_row_axis_role"] == "allocation_not_valid_work"
    assert structure["comparison"]["observed_allocation_rows"] == 16
    assert structure["comparison"]["allocation_not_compared"] is True
    assert structure["comparison"]["valid_routed_rows"] == "unobserved"
    assert "prepare_source_local_rows" in structure["comparison"]["matched_descriptor_fields"]
    assert structure["topology"]["declared"] == {
        "tensor_parallel_size": 8, "data_parallel_size": 1, "expert_parallel": True}
    assert structure["topology"]["after"]["ep"] == 8
    assert structure["rows"] == {
        "observed_full_graph": 1,
        "observed_source_local": 1,
        "observed_prepare_allocated": 8,
        "observed_dispatch_capacity": 16,
        "observed_finalize": 1,
        "generated_full": 1,
        "generated_local": 1,
        "generated_allocated": 8,
        "generated_finalize": [1],
        "gmm_allocation_rows": 16,
        "gmm_row_axis_role": "allocation_not_valid_work",
        "valid_routed_rows": "unobserved",
    }
    assert structure["semantic_equivalence"] is False
    assert structure["exact_native_kernel_match"] is False
    assert {item["kind"] for item in structure["unmatched_native_boundaries"]} >= {
        "hcom_allGather_", "GroupedMatmulSwigluQuant", "GroupedMatmul",
        "MoeDistributeDispatchV2", "MoeDistributeCombineV2", "PadV3"}
    assert "group_list_values" in structure["unobserved"]
    assert "peer_window" in structure["unobserved"]
    assert "native_binary_equivalence" in structure["unobserved"]
    assert "fused_implementation_timing" in structure["unobserved"]
    assert "first_allreduce_wait_cause" in structure["unobserved"]

    guard = provenance["legacy_ffn_guard"]
    assert guard["status"] == "applied"
    assert set(guard["removed_ids"]) == {
        "a3-native-expert-down-2048-low", "a3-native-expert-down-2048-mid",
        "a3-native-expert-down-2048-high", "a3-native-expert-up-2048-low",
        "a3-native-expert-up-2048-mid", "a3-native-expert-up-2048-high",
    }
    assert guard["timing_values_modified"] is False
    assert guard["kept_count"] == 1
    assert guard["old_descriptors"]["gate_up"]["banks"] == 32
    assert guard["old_descriptors"]["gate_up"]["width"] == 64
    assert guard["new_descriptors"]["gate_up"]["banks"] == 4
    assert guard["new_descriptors"]["gate_up"]["width"] == 512
    assert guard["changed_axes"]["gate_up"] == ["banks", "width"]
    assert imported["runtime"]["kernels"]["service_regimes"] == (
        original["runtime"]["kernels"]["service_regimes"][:1])
    assert imported["runtime"]["kernels"]["service_regimes"][0]["id"] == (
        "a3-native-rmsnorm-2048")
    assert imported["runtime"]["kernels"]["moe_token_partition"] == {
        "kind": "vllm_ascend_mc2_tp_slice", "padding": "right_to_tp"}
    assert "native_moe_protocol" not in imported["runtime"]["kernels"]
    assert "kernels" in provenance["changed_fields"]
    assert str(tmp_path / "kernel_details.csv") not in json.dumps(imported)
    assert structure["source"]["sha256"] not in json.dumps(imported)

    ops = [op for op in target_operators(imported, **fixture["geometry"]) if op.layer == 0]
    by_recipe = {}
    for op in ops:
        by_recipe.setdefault(op.recipe, []).append(op)
    gate = by_recipe["balanced_grouped_gate_up"][0]
    down = by_recipe["balanced_grouped_down"][0]
    assert gate.local_shape == (1, 1024, 2048)
    assert down.local_shape == (1, 2048, 512)
    assert dict(gate.metadata)["matrix_weight_bank_groups"] == 4
    assert dict(gate.metadata)["graph_physical_query_rows"] == 1
    assert gate.padded_shape[0] == 16
    assert len(by_recipe["tensor_concat"]) == 2
    assert {op.local_shape[0] for op in by_recipe["tensor_concat"]} == {8}
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["full_rows"] == partition["valid_rows"] == 1
    assert partition["local_rows"] == 1
    assert partition["allocated_rows"] == 8
    assert partition["padding"] == "right_to_tp"
    assert by_recipe["route_unpack"][0].local_shape[0] == 1

    repeated, repeated_provenance = import_capture_policy(imported, capture_path=command)
    assert repeated == imported
    assert repeated_provenance["deployment"]["status"] == "unchanged"
    assert repeated_provenance["native_structure"]["status"] == "not_evaluated"
    assert repeated_provenance["native_structure"]["reason"] == "automatic_scope_not_met"


def test_draft_only_caller_is_not_treated_as_consistent_actual_graph(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    declared = {"kind": "vllm_ascend_mc2_tp_slice", "layer_scopes": ["draft"]}
    raw["runtime"]["kernels"]["moe_token_partition"] = deepcopy(declared)
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    returned = imported["runtime"]["kernels"]["moe_token_partition"]
    assert returned == declared
    assert "padding" not in returned
    structure = provenance["native_structure"]
    assert structure["status"] == "conflict"
    assert structure["reason"] == "explicit_caller_actual_graph_mismatch"
    assert structure["caller"]["action"] == "conflict"
    assert structure["caller"]["returned"] == declared
    assert structure["candidate"]["selected"] is False
    assert structure["candidate"]["comparison"]["mismatches"]
    assert structure["generated"]["partition"] is None
    assert structure["comparison"]["basis"] == "actual_returned_graph"
    assert structure["comparison"]["mismatches"]
    assert structure["rows"]["generated_full"] is None
    assert provenance["status"] == "conflict"


def test_body_layer_scope_caller_completes_padding_and_matches_actual_graph(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    declared = {"kind": "vllm_ascend_mc2_tp_slice", "layer_scopes": ["body"]}
    raw["runtime"]["kernels"]["moe_token_partition"] = deepcopy(declared)
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "consistent"
    assert structure["caller"]["action"] in {"preserved_existing", "completed_padding"}
    assert structure["candidate"]["selected"] is True
    returned = imported["runtime"]["kernels"]["moe_token_partition"]
    assert returned == {
        "kind": "vllm_ascend_mc2_tp_slice", "padding": "right_to_tp",
        "layer_scopes": ["body"]}
    assert structure["generated"]["partition"]["allocated_rows"] == 8
    ops = [op for op in target_operators(
        imported, phase="decode", tokens=1, context=262144, sequences=1)
        if op.layer == 0]
    by_recipe = {}
    for op in ops:
        by_recipe.setdefault(op.recipe, []).append(op)
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["allocated_rows"] == 8
    assert partition["padding"] == "right_to_tp"


def test_nested_parallel_representation_binds_identically_to_flat(tmp_path):
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim import target_operators

    fixture = json.loads(E32.read_text())
    flat_raw = deepcopy(fixture["raw"])
    nested_raw = deepcopy(flat_raw)
    runtime = nested_raw["runtime"]
    runtime["parallel"] = {name: runtime.pop(name) for name in ("tp", "dp", "ep", "pp")}

    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    flat, flat_provenance = import_capture_policy(flat_raw, capture_path=command)
    nested, nested_provenance = import_capture_policy(nested_raw, capture_path=command)

    assert flat_provenance["deployment"]["status"] == "applied"
    assert nested_provenance["deployment"]["status"] == "applied"
    assert flat_provenance["native_structure"]["status"] == "consistent"
    assert nested_provenance["native_structure"]["status"] == "consistent"
    assert nested_provenance["native_structure"]["caller"]["action"] == "bound"
    assert nested_provenance["legacy_ffn_guard"]["removed_count"] == 6

    flat_case = parse_case(flat)
    nested_case = parse_case(nested)
    assert (nested_case.runtime.parallel.tp, nested_case.runtime.parallel.dp,
            nested_case.runtime.parallel.ep) == (8, 1, 8)
    assert (flat_case.runtime.parallel.tp, flat_case.runtime.parallel.dp,
            flat_case.runtime.parallel.ep) == (8, 1, 8)
    assert nested_case.model.hidden_size == flat_case.model.hidden_size == 2048
    assert nested_case.model.num_experts == flat_case.model.num_experts == 32

    def physical(case):
        ops = [op for op in target_operators(
            case, phase="decode", tokens=1, context=262144, sequences=1)
            if op.layer == 0]
        by_recipe = {}
        for op in ops:
            by_recipe.setdefault(op.recipe, []).append(op)
        partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
        return ({
            "gate": by_recipe["balanced_grouped_gate_up"][0].local_shape,
            "down": by_recipe["balanced_grouped_down"][0].local_shape,
            "tensor_concat": [op.local_shape for op in by_recipe["tensor_concat"]],
            "route_pack": (partition["full_rows"], partition["local_rows"],
                           partition["allocated_rows"], partition["padding"]),
            "route_unpack": by_recipe["route_unpack"][0].local_shape,
        })

    assert physical(nested) == physical(flat)
    assert nested_provenance["native_structure"]["rows"] == (
        flat_provenance["native_structure"]["rows"])


def test_already_ep8_dsv4f_keeps_topology_and_local_mc2_alignment(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(DSV4F.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, DSV4F_COMMAND)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    deployment = provenance["deployment"]
    assert deployment["status"] == "unchanged"
    assert deployment["changed_fields"] == []
    assert deployment["before"] == deployment["after"]
    runtime = imported["runtime"]
    assert (runtime["tp"], runtime["dp"], runtime["ep"]) == (8, 1, 8)
    assert "moe_recipe" not in runtime
    caller = runtime["kernels"]["moe_token_partition"]
    assert caller["kind"] == "vllm_ascend_mc2_tp_slice"
    assert caller["padding"] == "right_to_tp"

    capture = fixture["captures"][0]
    rows = capture["geometry"]["sequences"]
    ops = [op for op in target_operators(imported, **capture["geometry"]) if op.layer == 0]
    by_recipe = {}
    for op in ops:
        by_recipe.setdefault(op.recipe, []).append(op)
    assert by_recipe["router"][0].local_shape[0] == rows
    assert by_recipe["dense_gate_up"][0].local_shape[0] == rows
    assert len(by_recipe["tensor_concat"]) == 2
    assert {dict(op.metadata)["graph_physical_query_rows"] for op in ops} == {rows}
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["full_rows"] == partition["valid_rows"] == rows
    assert partition["allocated_rows"] == 8 and partition["local_rows"] == 1
    assert partition["padding"] == "right_to_tp"

    repeated, _ = import_capture_policy(imported, capture_path=command)
    assert repeated == imported


@pytest.mark.parametrize("flags, reason, missing", [
    ("--tensor-parallel-size 8 --data-parallel-size 1",
     "expert_parallel_not_declared", ["expert_parallel"]),
    ("--data-parallel-size 1 --enable-expert-parallel",
     "tensor_parallel_size_missing", ["tensor_parallel_size"]),
    ("--tensor-parallel-size 8 --enable-expert-parallel",
     "data_parallel_size_missing", ["data_parallel_size"]),
    ("--tensor-parallel-size 8 --data-parallel-size 2 --enable-expert-parallel",
     "data_parallel_size_not_one", []),
    ("--tensor-parallel-size 1 --data-parallel-size 1 --enable-expert-parallel",
     "tensor_parallel_size_not_greater_than_one", []),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --no-enable-expert-parallel",
     "expert_parallel_disabled", []),
])
def test_missing_or_unsupported_topology_is_explicit_and_never_mutates(
        tmp_path, flags, reason, missing):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model " + flags + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert imported == original
    deployment = provenance["deployment"]
    assert deployment["status"] == "unsupported"
    assert deployment["reason"] == reason
    assert deployment["missing"] == missing
    assert deployment["derived"] == {}
    assert deployment["before"] == deployment["after"]
    assert deployment["changed_fields"] == []
    assert deployment["remaining_limits"]
    assert provenance["status"] == "unsupported"


def test_unsupported_topology_keeps_graph_outcome_and_reports_deployment_unsupported(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = tmp_path / "cmd.sh"
    command.write_text(
        "vllm serve retained-model "
        "--compilation-config '{\"cudagraph_mode\":\"FULL_DECODE_ONLY\","
        "\"cudagraph_capture_sizes\":[1,2,4]}' "
        "--tensor-parallel-size 8 --data-parallel-size 1 --no-enable-expert-parallel\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    assert provenance["graph_status"] == "applied"
    assert provenance["status"] == "applied"
    assert provenance["deployment"]["status"] == "unsupported"
    assert provenance["deployment"]["reason"] == "expert_parallel_disabled"
    assert imported["runtime"]["graph_capture_keys"] == [1, 2, 4]
    assert imported["runtime"]["ep"] == 1


def test_default_import_completes_body_scoped_dsv4_padding(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(DSV4F.read_text())
    raw = deepcopy(fixture["raw"])
    declared = {"kind": "vllm_ascend_mc2_tp_slice", "layer_scopes": ["body"]}
    raw["runtime"]["kernels"]["moe_token_partition"] = deepcopy(declared)
    command = _command(tmp_path, DSV4F_COMMAND)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert provenance["deployment"]["status"] == "unchanged"
    assert provenance["native_structure"]["status"] == "not_evaluated"
    assert provenance["native_structure"]["reason"] == "automatic_scope_not_met"
    returned = imported["runtime"]["kernels"]["moe_token_partition"]
    assert returned == {
        "kind": "vllm_ascend_mc2_tp_slice", "layer_scopes": ["body"],
        "padding": "right_to_tp",
    }
    ops = target_operators(imported, phase="decode", tokens=1, context=4096,
                           sequences=1)
    assert len(ops) == 505
    by_recipe = {}
    for op in ops:
        if op.layer == 0:
            by_recipe.setdefault(op.recipe, []).append(op)
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["allocated_rows"] == 8
    assert partition["padding"] == "right_to_tp"
    assert {op.local_shape[0] for op in by_recipe["tensor_concat"]} == {8}


def test_malformed_layer_scope_is_not_padded_as_body(tmp_path):
    from mindie_sim import target_operators
    from mindie_sim.schema.common import ModelingError

    fixture = json.loads(DSV4F.read_text())
    raw = deepcopy(fixture["raw"])
    declared = {"kind": "vllm_ascend_mc2_tp_slice", "layer_scopes": ["bogus"]}
    raw["runtime"]["kernels"]["moe_token_partition"] = deepcopy(declared)
    command = _command(tmp_path, DSV4F_COMMAND)
    imported, _ = import_capture_policy(raw, capture_path=command)

    returned = imported["runtime"]["kernels"]["moe_token_partition"]
    assert returned == declared
    assert "padding" not in returned
    with pytest.raises(ModelingError, match="layer_scopes_require_body_or_draft"):
        target_operators(imported, phase="decode", tokens=1, context=4096,
                         sequences=1)


def test_already_ep8_dsv4f_explicit_reconciliation_preserves_existing_caller(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(DSV4F.read_text())
    sidecar = json.loads(DSV4F_STRUCTURAL_SIDECAR.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, DSV4F_COMMAND, DSV4F_STRUCTURAL)
    imported, provenance = import_capture_policy(
        raw, capture_path=command, reconcile_structure=True)

    assert raw == original
    assert sidecar["source"]["sha256"] == fixture["captures"][0]["source_csv"]["sha256"]
    assert provenance["deployment"]["status"] == "unchanged"
    structure = provenance["native_structure"]
    assert structure["status"] == "consistent"
    assert structure["evidence"]["grouped"]["gate"]["banks"] == 2
    assert structure["evidence"]["grouped"]["gate"]["hidden"] == 4096
    assert structure["evidence"]["grouped"]["gate"]["width"] == 2048
    assert structure["comparison"]["mismatches"] == []
    assert structure["caller"]["action"] == "preserved_existing"
    assert structure["caller"]["applied_fields"] == []
    assert provenance["legacy_ffn_guard"]["status"] == "unchanged"
    assert provenance["legacy_ffn_guard"]["reason"] == "matrix_physical_boundary_unchanged"
    assert imported["runtime"]["kernels"]["moe_token_partition"] == {
        "kind": "vllm_ascend_mc2_tp_slice", "padding": "right_to_tp"}

    capture = fixture["captures"][0]
    ops = [op for op in target_operators(imported, **capture["geometry"]) if op.layer == 0]
    by_recipe = {}
    for op in ops:
        by_recipe.setdefault(op.recipe, []).append(op)
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["allocated_rows"] == 8
    assert partition["local_rows"] == 1
    assert partition["padding"] == "right_to_tp"
    assert by_recipe["route_unpack"][0].local_shape[0] == 1

    repeated, repeated_provenance = import_capture_policy(
        imported, capture_path=command, reconcile_structure=True)
    assert repeated == imported
    assert repeated_provenance["native_structure"]["caller"]["action"] == "preserved_existing"


def test_dsv4_q4_structural_evidence_pads_four_to_eight(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(DSV4F.read_text())
    sidecar = json.loads(DSV4F_Q4_STRUCTURAL_SIDECAR.read_text())
    raw = fixture["raw"]
    command = _command(tmp_path, DSV4F_Q4_COMMAND, DSV4F_Q4_STRUCTURAL)
    imported, provenance = import_capture_policy(
        raw, capture_path=command, reconcile_structure=True)

    assert sidecar["source"]["sha256"] == (
        "98e10982e0e3fa7228da6c0fe7563eaf6f5d72901634a9ad38f3cde65c95f6b3")
    assert sidecar["source_command"]["sha256"] == (
        "1fd86caa273b9661c642288edd49ce73ac856a764ead39928d709effb3bf7565")
    assert provenance["deployment"]["status"] == "unchanged"
    structure = provenance["native_structure"]
    assert structure["status"] == "consistent"
    prepare = structure["evidence"]["prepare"]
    assert prepare["input_rows"] == 4
    assert prepare["source_local_rows"] == 1
    assert prepare["output_rows"] == 8
    assert prepare["output_rows"] != prepare["input_rows"] * 8  # ceil(4/8)*8, not 4*8
    assert prepare["x_width"] == 4096
    assert prepare["logits_width"] == 16
    assert structure["evidence"]["dispatch"]["contract"] == {
        "source_local_rows": 1, "hidden_size": 4096, "capacity_rows": 16,
        "bank_axis": 2, "expert_axis": 16, "combine_output_rows": 1,
    }
    assert structure["comparison"]["mismatches"] == []
    assert "prepare_input_rows" in structure["comparison"]["matched_descriptor_fields"]
    assert "prepare_source_local_rows" in structure["comparison"]["matched_descriptor_fields"]
    assert "prepare_allocation_rows" in structure["comparison"]["matched_descriptor_fields"]
    assert structure["comparison"]["observed_allocation_rows"] == 16
    assert structure["comparison"]["allocation_not_compared"] is True
    assert structure["rows"] == {
        "observed_full_graph": 4,
        "observed_source_local": 1,
        "observed_prepare_allocated": 8,
        "observed_dispatch_capacity": 16,
        "observed_finalize": 1,
        "generated_full": 4,
        "generated_local": 1,
        "generated_allocated": 8,
        "generated_finalize": [1],
        "gmm_allocation_rows": 16,
        "gmm_row_axis_role": "allocation_not_valid_work",
        "valid_routed_rows": "unobserved",
    }
    assert structure["candidate"]["selected"] is True
    assert structure["generated"]["roles"]["gate_up"]["banks"] == 2
    assert structure["generated"]["roles"]["gate_up"]["width"] == 2048
    assert structure["caller"]["action"] == "preserved_existing"
    assert provenance["legacy_ffn_guard"]["status"] == "unchanged"

    ops = [op for op in target_operators(
        imported, phase="decode", tokens=1, context=4096, sequences=4)
        if op.layer == 0]
    by_recipe = {}
    for op in ops:
        by_recipe.setdefault(op.recipe, []).append(op)
    partition = dict(by_recipe["route_pack"][0].metadata)["moe_token_partition"]
    assert partition["full_rows"] == 4
    assert partition["local_rows"] == 1
    assert partition["allocated_rows"] == 8
    assert partition["padding"] == "right_to_tp"
    assert {op.local_shape[0] for op in by_recipe["tensor_concat"]} == {8}
    assert {dict(op.metadata)["graph_physical_query_rows"]
            for op in ops} == {4}


def test_explicit_alltoall_caller_conflicts_with_mc2_structural_evidence(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    caller = {"kind": "vllm_ascend_alltoall_tp_slice"}
    raw["runtime"]["kernels"]["moe_token_partition"] = deepcopy(caller)
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    assert imported["runtime"]["kernels"]["moe_token_partition"] == caller
    assert (imported["runtime"]["tp"], imported["runtime"]["dp"],
            imported["runtime"]["ep"]) == (8, 1, 8)
    structure = provenance["native_structure"]
    assert structure["status"] == "conflict"
    assert structure["reason"] == "explicit_caller_not_mc2"
    assert structure["caller"]["action"] == "conflict"
    assert structure["candidate"]["selected"] is False
    assert structure["generated"] is None
    assert structure["generated_issue"]["reason"] == "generated_descriptor_unavailable"
    assert provenance["legacy_ffn_guard"]["status"] == "not_evaluated"
    assert provenance["status"] == "conflict"


def test_gzip_structural_source_is_used_when_plain_csv_is_absent(tmp_path):
    import gzip

    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    command = _command(tmp_path, E32_COMMAND)
    with gzip.open(tmp_path / "kernel_details.csv.gz", "wb") as handle:
        handle.write(E32_STRUCTURAL.read_bytes())
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "consistent"
    assert structure["source"]["path"].endswith("kernel_details.csv.gz")
    assert imported["runtime"]["kernels"]["moe_token_partition"] == {
        "kind": "vllm_ascend_mc2_tp_slice", "padding": "right_to_tp"}


def test_single_matching_axis_is_not_a_complete_ffn_domain_guard(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    rules = raw["runtime"]["kernels"]["service_regimes"]
    template = next(rule for rule in rules
                    if rule.get("match", {}).get("recipe") == "balanced_grouped_gate_up")
    partial = deepcopy(template)
    partial["id"] = "partial-bank-only-guard"
    partial["match"]["metadata.matrix_weight_bank_groups"] = 4
    complete = deepcopy(template)
    complete["id"] = "complete-bank-and-width-guard"
    complete["match"]["metadata.matrix_weight_bank_groups"] = 4
    complete["match"]["local_shape.1"] = 1024
    raw["runtime"]["kernels"]["service_regimes"] = [partial, complete]
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    guard = provenance["legacy_ffn_guard"]
    assert guard["status"] == "applied"
    assert guard["removed_ids"] == ["partial-bank-only-guard"]
    assert imported["runtime"]["kernels"]["service_regimes"] == [complete]


def _modified_structural_csv(tmp_path, transform):
    lines = E32_STRUCTURAL.read_text().splitlines()
    altered = transform(lines)
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text("\n".join(altered) + "\n")
    return command


def test_down_output_fp16_does_not_match_bf16_combine_consumer(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    rows = list(csv.reader(E32_STRUCTURAL.read_text().splitlines()))
    header = rows[0]
    type_index = header.index("Type")
    output_dtype_index = header.index("Output Data Types")
    changed = []
    for row in rows[1:]:
        if row[type_index] == "GroupedMatmul":
            row[output_dtype_index] = "DT_FLOAT16"
        changed.append(row)
    command = _command(tmp_path, E32_COMMAND)
    with (tmp_path / "kernel_details.csv").open("w", newline="") as handle:
        csv.writer(handle).writerows([header, *changed])
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unsupported"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_pad_output_width_negative_control_does_not_bind(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]

    def widen_x_pad(lines):
        result = []
        for line in lines:
            if '"1,2048;4;"' in line and '"8,2048"' in line:
                line = line.replace('"8,2048"', '"8,2049"')
            result.append(line)
        return result

    command = _modified_structural_csv(tmp_path, widen_x_pad)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unsupported"
    assert structure["reason"] == "prepare_pad_output_width_disagrees"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_pad_dtype_role_negative_control_does_not_bind(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]

    def recast_x_pad(lines):
        result = []
        for line in lines:
            if '"1,2048;4;"' in line and "DT_BF16;INT32;DT_BF16" in line:
                line = line.replace("DT_BF16", "FLOAT")
            result.append(line)
        return result

    command = _modified_structural_csv(tmp_path, recast_x_pad)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unsupported"
    assert structure["reason"] == "prepare_pad_dtype_role_disagrees"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_capacity_buffer_rows_negative_control_does_not_bind(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]

    def shrink_down_capacity(lines):
        result = []
        for line in lines:
            if ",GroupedMatmul," in line and '"16,512;4,512,2048;' in line:
                line = line.replace(
                    '"16,512;4,512,2048;;4,2048;;;;4;16"',
                    '"15,512;4,512,2048;;4,2048;;;;4;15"', 1)
                line = line.replace('"16,2048"', '"15,2048"', 1)
            result.append(line)
        return result

    command = _modified_structural_csv(tmp_path, shrink_down_capacity)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unsupported"
    assert structure["reason"] == "capacity_buffer_rows_or_channels_disagree"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_structural_scan_propagates_timeout_and_requests_zero_duration_rows(
        tmp_path, monkeypatch):
    import capture_structure

    captured = {}

    def timeout_scan(*args, **kwargs):
        captured.update(kwargs)
        raise TimeoutError("structural scan deadline")

    monkeypatch.setattr(capture_structure, "kernel_rows", timeout_scan)
    with pytest.raises(TimeoutError):
        capture_structure.collect_structural_evidence(
            E32_STRUCTURAL, tp=8, hidden_size=2048, num_experts=32, top_k=2)
    assert captured["include_zero_duration"] is True


def test_structural_timeout_propagates_through_common_import(tmp_path, monkeypatch):
    import capture_structure

    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)

    def timeout_scan(*args, **kwargs):
        raise TimeoutError("structural scan deadline")

    monkeypatch.setattr(capture_structure, "kernel_rows", timeout_scan)
    with pytest.raises(TimeoutError):
        import_capture_policy(raw, capture_path=command)
    assert raw == original


def test_structural_scan_requests_zero_duration_rows(tmp_path, monkeypatch):
    import capture_structure

    captured = {}

    def empty_scan(*args, **kwargs):
        captured.update(kwargs)
        return iter(())

    monkeypatch.setattr(capture_structure, "kernel_rows", empty_scan)
    evidence = capture_structure.collect_structural_evidence(
        E32_STRUCTURAL, tp=8, hidden_size=2048, num_experts=32, top_k=2)
    assert captured["include_zero_duration"] is True
    assert evidence["status"] == "unresolved"


def test_malformed_structural_csv_propagates_through_import(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text(
        "Name,Type,Duration(us)\nvllm serve only\n")
    with pytest.raises(ProfilerSchemaError):
        import_capture_policy(raw, capture_path=command)
    assert raw == original


def test_unrelated_pad_signature_does_not_establish_prepare(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    e32_lines = E32_STRUCTURAL.read_text().splitlines()
    dsv4_lines = DSV4F_STRUCTURAL.read_text().splitlines()
    dsv4_pad = next(line for line in dsv4_lines[1:]
                    if ",PadV3," in line and '"1,4096;4;"' in line)
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text(
        "\n".join([e32_lines[0], *e32_lines[1:], dsv4_pad]) + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unsupported"
    assert structure["reason"] == "prepare_pad_signature_count_unsupported"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_structural_evidence_without_dispatch_combine_does_not_bind_mc2(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    source_lines = E32_STRUCTURAL.read_text().splitlines()
    kept = [source_lines[0]] + [line for line in source_lines[1:]
                                if ",MoeDistributeDispatchV2," not in line
                                and ",MoeDistributeCombineV2," not in line]
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text("\n".join(kept) + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "unresolved"
    assert structure["reason"] == "dispatch_not_observed"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_unrecognized_eager_caller_type_blocks_mc2_binding(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    lines = E32_STRUCTURAL.read_text().splitlines()
    allgather = lines[-1]
    eager = allgather.replace(",hcom_allGather_,", ",MoeInitRouting,")
    assert ",MoeInitRouting," in eager
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text(
        "\n".join([*lines, eager]) + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "mixed_unsupported"
    assert structure["reason"] == "unrecognized_moe_or_eager_caller_observed"
    assert "MoeInitRouting" in structure["evidence"]["other_caller_kinds"]
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


@pytest.mark.parametrize("source_path, line_number, kind", (
    (Path("tests/fixtures/fusion_contracts/a3_qwen35.csv"), 50, "MoeInitRoutingV3"),
    (Path("tests/fixtures/fusion_contracts/a3_v4pro.csv"), 68, "MoeTokenPermute"),
))
def test_versioned_routing_and_permutation_rows_block_mc2(
        tmp_path, source_path, line_number, kind):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    source = ROOT / source_path
    lines = E32_STRUCTURAL.read_text().splitlines()
    with source.open(newline="") as handle:
        header = next(csv.reader(handle))
    assert header == next(csv.reader([lines[0]]))
    extra = source.read_text().splitlines()[line_number - 1]
    assert next(csv.DictReader([lines[0], extra]))["Type"] == kind
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text(
        "\n".join([*lines, extra]) + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "mixed_unsupported"
    assert structure["reason"] == "unrecognized_moe_or_eager_caller_observed"
    assert kind in structure["evidence"]["other_caller_kinds"]
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_mixed_grouped_signatures_do_not_bind_mc2(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    e32_lines = E32_STRUCTURAL.read_text().splitlines()
    dsv4_lines = DSV4F_STRUCTURAL.read_text().splitlines()
    dsv4_gate = next(line for line in dsv4_lines[1:]
                     if ",GroupedMatmulSwigluQuant," in line)
    command = _command(tmp_path, E32_COMMAND)
    (tmp_path / "kernel_details.csv").write_text(
        "\n".join([e32_lines[0], *e32_lines[1:], dsv4_gate]) + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    structure = provenance["native_structure"]
    assert structure["status"] == "mixed_unsupported"
    assert structure["reason"] == "mixed_gate_signatures"
    assert provenance["status"] == "partially_provided"
    assert "moe_token_partition" not in imported["runtime"]["kernels"]


def test_non_moe_model_is_not_changed_by_an_expert_parallel_command(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    raw["model"]["ffn"] = "dense"
    original = deepcopy(raw)
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model --tensor-parallel-size 8 "
                       "--data-parallel-size 1 --enable-expert-parallel\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert imported == original
    deployment = provenance["deployment"]
    assert deployment["status"] == "unsupported"
    assert deployment["reason"] == "moe_model_required"
    assert deployment["derived"] == {}
    assert imported["runtime"]["ep"] == 1
    assert imported["runtime"]["moe_recipe"] == "tp_join_reduce"


@pytest.mark.parametrize("flags, error", [
    ("--tensor-parallel-size 8 --tensor-parallel-size=8 --data-parallel-size 1 "
     "--enable-expert-parallel",
     "capture_tensor_parallel_size_ambiguous_multiple_declarations"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --data-parallel-size 1 "
     "--enable-expert-parallel",
     "capture_data_parallel_size_ambiguous_multiple_declarations"),
    ("--tensor-parallel-size $TP --data-parallel-size 1 --enable-expert-parallel",
     "capture_tensor_parallel_size_requires_literal_integer"),
    ("--tensor-parallel-size 8 --data-parallel-size $(DP) --enable-expert-parallel",
     "capture_data_parallel_size_requires_literal_integer"),
    ("--tensor-parallel-size 8.0 --data-parallel-size 1 --enable-expert-parallel",
     "capture_tensor_parallel_size_requires_literal_integer"),
    ("--tensor-parallel-size --data-parallel-size 1 --enable-expert-parallel",
     "capture_tensor_parallel_size_requires_literal_integer"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel=$EP",
     "capture_enable_expert_parallel_rejects_explicit_value"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel=false",
     "capture_enable_expert_parallel_rejects_explicit_value"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel=true",
     "capture_enable_expert_parallel_rejects_explicit_value"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel 1",
     "capture_enable_expert_parallel_rejects_explicit_value"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --no-enable-expert-parallel=0",
     "capture_enable_expert_parallel_rejects_explicit_value"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel "
     "--enable-expert-parallel",
     "capture_enable_expert_parallel_ambiguous_multiple_declarations"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --enable-expert-parallel "
     "--no-enable-expert-parallel",
     "capture_enable_expert_parallel_ambiguous_multiple_declarations"),
    ("--tensor-parallel-size 8 --data-parallel-size 1 --no-enable-expert-parallel "
     "--enable-expert-parallel",
     "capture_enable_expert_parallel_ambiguous_multiple_declarations"),
])
def test_repeated_dynamic_or_nonliteral_flag_values_are_rejected(tmp_path, flags, error):
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model " + flags + "\n")
    raw = {"runtime": {"tp": 8, "dp": 1, "ep": 1}}
    original = deepcopy(raw)
    with pytest.raises(ValueError, match=error):
        import_capture_policy(raw, capture_path=command)
    assert raw == original


def test_explicit_incompatible_caller_and_native_declarations_are_preserved(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    raw["runtime"]["moe_recipe"] = "mc2"
    raw["runtime"]["kernels"]["moe_token_partition"] = {"kind": "eager_allgather"}
    native = {"kind": "arch35_fullmesh", "max_inflight_per_rank": 4}
    raw["runtime"]["kernels"]["native_moe_protocol"] = deepcopy(native)
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    runtime = imported["runtime"]
    assert (runtime["tp"], runtime["dp"], runtime["ep"]) == (8, 1, 1)
    assert runtime["moe_recipe"] == "mc2"
    assert runtime["kernels"]["moe_token_partition"] == {"kind": "eager_allgather"}
    assert runtime["kernels"]["native_moe_protocol"] == native
    assert runtime["graph_capture_keys"] == fixture["expected"]["after"]["graph_capture_keys"]
    deployment = provenance["deployment"]
    assert deployment["status"] == "conflict"
    assert deployment["reason"] == "explicit_incompatible_declaration"
    assert deployment["derived"]["ep"] == 8
    assert deployment["before"] == deployment["after"]
    assert deployment["changed_fields"] == []
    conflicts = {item["field"]: item["reason"]
                 for item in deployment["preserved_conflicts"]}
    assert conflicts == {
        "runtime.moe_recipe": "explicit_incompatible_moe_recipe",
        "runtime.kernels.moe_token_partition.kind": "explicit_incompatible_caller",
    }
    preserved = {item["field"]: item["status"]
                 for item in deployment["preserved_explicit"]}
    assert preserved == {"runtime.kernels.native_moe_protocol": "preserved_unresolved"}
    assert provenance["status"] == "conflict"
    assert provenance["graph_status"] == "applied"
    assert provenance["reason"] == "explicit_incompatible_declaration"


def test_unknown_native_protocol_declaration_is_a_conflict_before_mutation(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    native = {"kind": "unknown_caller", "max_inflight_per_rank": 4}
    raw["runtime"]["kernels"]["native_moe_protocol"] = deepcopy(native)
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    assert imported["runtime"]["ep"] == 1
    assert imported["runtime"]["kernels"]["native_moe_protocol"] == native
    deployment = provenance["deployment"]
    assert deployment["status"] == "conflict"
    conflict, = deployment["preserved_conflicts"]
    assert conflict["field"] == "runtime.kernels.native_moe_protocol"
    assert conflict["reason"] == "explicit_incompatible_native_protocol"
    assert "native_moe_protocol_requires" in conflict["detail"]
    assert provenance["status"] == "conflict"


@pytest.mark.parametrize("native", [
    {"kind": "arch35_fullmesh", "max_inflight_per_rank": 4},
    {"kind": "arch22_v2_caller", "max_inflight_per_rank": 4,
     "dispatch_quant": "per_token_int8"},
    {"kind": "arch35_fullmesh", "max_inflight_per_rank": 4, "extra": 1},
    {"kind": "arch35_fullmesh", "max_inflight_per_rank": 4, "global_bs": 0},
    {"kind": "arch22_v2_caller", "max_inflight_per_rank": 4,
     "dispatch_quant": "none"},
    {"kind": "arch22_v2_caller", "max_inflight_per_rank": 4,
     "dispatch_quant": "per_token_int8", "global_bs": -1},
    {"kind": "arch35_fullmesh"},
    {"kind": "unknown_caller", "max_inflight_per_rank": 4},
])
def test_native_protocol_conflicts_reuse_the_real_sim_selector(native):
    from mindie_sim.prediction.mc2_graph import select
    from mindie_sim.schema.common import ModelingError

    original = deepcopy(native)
    try:
        select({"native_moe_protocol": native})
        selected = True
    except ModelingError:
        selected = False
    conflicts = _native_protocol_conflicts(native)
    assert native == original
    assert bool(conflicts) is (not selected)
    if conflicts:
        assert conflicts[0]["field"] == "runtime.kernels.native_moe_protocol"
        assert conflicts[0]["value"] == native
        assert conflicts[0]["reason"] == "explicit_incompatible_native_protocol"
        assert conflicts[0]["detail"]


def test_native_protocol_without_peer_window_is_a_conflict_before_mutation(tmp_path):
    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    native = {"kind": "arch35_fullmesh"}
    raw["runtime"]["kernels"]["native_moe_protocol"] = deepcopy(native)
    original = deepcopy(raw)
    command = _command(tmp_path, E32_COMMAND)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    assert imported["runtime"]["ep"] == 1
    assert imported["runtime"]["kernels"]["native_moe_protocol"] == native
    deployment = provenance["deployment"]
    assert deployment["status"] == "conflict"
    conflict, = deployment["preserved_conflicts"]
    assert conflict["field"] == "runtime.kernels.native_moe_protocol"
    assert conflict["reason"] == "explicit_incompatible_native_protocol"
    assert "native_moe_protocol_requires" in conflict["detail"]
    assert provenance["status"] == "conflict"


def test_compatible_existing_mc2_caller_remains_usable(tmp_path):
    from mindie_sim import target_operators

    fixture = json.loads(E32.read_text())
    raw = deepcopy(fixture["raw"])
    raw["runtime"]["kernels"]["moe_token_partition"] = {
        "kind": "vllm_ascend_mc2_tp_slice"}
    command = _command(tmp_path, E32_COMMAND, E32_STRUCTURAL)
    imported, provenance = import_capture_policy(raw, capture_path=command)

    deployment = provenance["deployment"]
    assert deployment["status"] == "applied"
    assert "preserved_conflicts" not in deployment
    assert provenance["native_structure"]["status"] == "consistent"
    assert provenance["native_structure"]["caller"]["action"] == "preserved_existing"
    preserved, = deployment["preserved_explicit"]
    assert preserved["field"] == "runtime.kernels.moe_token_partition"
    runtime = imported["runtime"]
    assert (runtime["tp"], runtime["dp"], runtime["ep"]) == (8, 1, 8)
    assert runtime["moe_recipe"] == "alltoall"
    assert runtime["kernels"]["moe_token_partition"]["kind"] == "vllm_ascend_mc2_tp_slice"
    assert runtime["kernels"]["moe_token_partition"]["padding"] == "right_to_tp"

    ops = [op for op in target_operators(imported, **fixture["geometry"]) if op.layer == 0]
    partition = dict(_layer0(ops, "route_pack").metadata)["moe_token_partition"]
    assert partition["allocated_rows"] == 8
    assert partition["local_rows"] == 1


@pytest.mark.parametrize("flags", [
    "--tensor-parallel-size=8 --data-parallel-size 1 --enable-expert-parallel",
    "--tensor-parallel-size 8 --data-parallel-size=1 --enable-expert-parallel",
])
def test_long_numeric_flag_value_forms_are_both_literal(tmp_path, flags):
    fixture = json.loads(E32.read_text())
    raw = fixture["raw"]
    original = deepcopy(raw)
    command = tmp_path / "cmd.sh"
    command.write_text("vllm serve retained-model " + flags + "\n")
    imported, provenance = import_capture_policy(raw, capture_path=command)

    assert raw == original
    assert provenance["deployment"]["status"] == "applied"
    assert (imported["runtime"]["tp"], imported["runtime"]["dp"],
            imported["runtime"]["ep"]) == (8, 1, 8)
    assert imported["runtime"]["moe_recipe"] == "alltoall"
