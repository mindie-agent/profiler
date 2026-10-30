"""Complete retained GLM FP8, accepted-state and sparse-batch ABI boundaries."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def evidence():
    pytest.importorskip("mindie_sim.structure")
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    sys.path.insert(0, str(ROOT / "examples/structure"))
    helper = importlib.import_module("glm_native_references")
    partition = json.loads((ROOT / "examples/structure/acceptance-20261030-glm-native-partitions/a5_glm53flash_tp8_c64_p4k-native-partitions.json").read_text())
    case = parse_case(json.loads(Path(partition["case_identity"]["path"]).read_text()))
    manifest = export_structure(case, phase="decode", tokens=4, sequences=64, context=4104, scope="body")
    return helper, partition, manifest


def test_complete_native_populations_keep_full_batch_and_conditional_values(evidence):
    helper, partition, manifest = evidence
    groups, failures, _ = helper.prepare_references(partition, manifest)
    assert not failures
    assert sum(g["observed_us"]["count"] for g in groups) == 2697
    for row in groups:
        original = partition["partitions"][row["partition_index"]]
        assert row["duration_ns_counter"] == original["duration_ns_counter"]
        assert row["strict_accuracy_implied"] is False
        assert row["layer_ids"] == sorted(map(int, original["layer_counts"]))
    sparse = next(g for g in groups if g["native_operator_type"] == "SparseFlashMla")
    assert len(sparse["representative_target_ids"]) == 64
    assert sparse["source_correspondence"]["observed_sparse_index_capacity"] == 2051
    assert sparse["source_correspondence"]["declared_topk"] == 2048
    assert sparse["source_correspondence"]["observed_topk_length_values"] is None
    recurrent = next(g for g in groups if g["native_operator_type"] == "RecurrentKda")
    assert len(recurrent["representative_target_ids"]) == 66
    assert recurrent["source_correspondence"]["observed_accepted_tokens_descriptor"] == ((64,), "int32", "ND")
    assert recurrent["source_correspondence"]["native_source_adapter_status"] == "accepted_token_state_slot_branch_not_supported"
    mx = next(g for g in groups if g["native_operator_type"] == "GroupedMatmulSwigluQuantV2")
    assert mx["source_correspondence"]["observed_valid_routed_rows"] is None
    assert mx["source_correspondence"]["declared_valid_routed_rows"] == 2048


def test_changed_one_layer_cannot_reuse_whole_saved_fusion_histogram(evidence):
    helper, partition, manifest = evidence
    nodes = list(manifest["nodes"])
    index = next(i for i, n in enumerate(nodes) if n["node_id"] == "rank:0/s0.l19.expert_up")
    target = nodes[index]
    nodes[index] = {**target, "physical_work": {**target["physical_work"], "hbm_bytes": target["physical_work"]["hbm_bytes"] * 2}}
    groups, failures, _ = helper.prepare_references(partition, {**manifest, "nodes": nodes})
    assert len(failures) == 1
    assert failures[0]["event_count"] == 341
    assert failures[0]["reason"] == "heterogeneous_fresh_layer_programs_cannot_split_saved_histogram"
    assert sum(g["observed_us"]["count"] for g in groups) == 2697 - 341


def test_fp8_scale_layout_is_not_reinterpreted_as_w4a8(evidence):
    helper, partition, manifest = evidence
    changed = deepcopy(partition)
    group = next(g for g in changed["partitions"] if g["native_operator_type"] == "GroupedMatmulSwigluQuantV2")
    group["native_abi"][2][4][2] = "ND"
    _, failures, _ = helper.prepare_references(changed, manifest)
    assert len(failures) == 1 and failures[0]["reason"] == "mx_swiglu_fp8_packed_parameter_abi"


def test_explicit_rope0_pipeline_preserves_complete_bf16_batch_population(evidence):
    helper, partition, _ = evidence
    from mindie_sim.structure import export_structure
    raw = json.loads(Path(partition["case_identity"]["path"]).read_text())
    raw["runtime"]["kernels"].setdefault("programs", {})["indexed_attention"] = {
        "kind": "indexed_attention_pipeline", "scratch_policy": "offchip",
        "operand_modes": False, "rope0_analytic": True}
    manifest = export_structure(raw, phase="decode", tokens=4, sequences=64, context=4104, scope="body")
    groups, failures, _ = helper.prepare_references(partition, manifest)
    assert not failures
    group = next(g for g in groups if g["native_operator_type"] == "SparseFlashMla")
    assert group["observed_us"]["count"] == 341
    assert len(group["representative_target_ids"]) == 1
    assert group["source_correspondence"]["declared_sequence_count"] == 64
    original = partition["partitions"][group["partition_index"]]
    assert group["duration_ns_counter"] == original["duration_ns_counter"]
