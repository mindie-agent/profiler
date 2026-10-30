"""Real FP8 native buckets use the selected fused resource, never missing members."""
from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def evidence():
    sim = pytest.importorskip("mindie_sim")
    from mindie_sim.prediction.structure import parse_case
    from mindie_sim.structure import export_structure
    sys.path.insert(0, str(ROOT / "examples/structure"))
    helper = importlib.import_module("glm_native_references")
    case_path = Path(sim.__file__).resolve().parents[1] / "examples/cases/high-concurrency-20261030/glm-source-complete/a5_glm53flash_tp8_c32_p4k.json"
    case = parse_case(json.loads(case_path.read_text()))
    path = ROOT / "examples/structure/acceptance-20261030-glm-native-partitions/a5_glm53flash_tp8_c32_p4k-native-partitions.json"
    partitions = json.loads(path.read_text())
    partitions["partitions"] = [g for g in partitions["partitions"]
        if g["native_operator_type"] == "GroupedMatmulSwigluQuantV2"]
    manifest = export_structure(case, phase="decode", tokens=4, sequences=32, context=4104, scope="body")
    return helper, case, partitions, manifest


def test_complete_native_up_buckets_select_one_fused_resource_per_layer(evidence):
    helper, case, partitions, manifest = evidence
    refs, unresolved, compact = helper.prepare_references(partitions, manifest)
    assert not unresolved
    assert sum(r["observed_us"]["count"] for r in refs) == 31 * 42
    assert sum(len(r["layer_ids"]) for r in refs) == 42
    for ref in refs:
        assert ref["duration_ns_counter"] == partitions["partitions"][ref["partition_index"]]["duration_ns_counter"]
        assert len(ref["representative_target_ids"]) == 1
        assert ref["source_correspondence"]["native_fusion_resource_program_selected"]
        assert ref["source_correspondence"]["observed_valid_routed_rows"] is None
        assert ref["strict_accuracy_implied"] is False
    assert all(n["recipe"] == "ascend_mxfp8_grouped_swiglu_quant" for n in compact["nodes"])
    from body_source_role_references import predict_source_role_references
    priced = predict_source_role_references(case, compact, {
        "source_role_references": [refs[0]], "forward_count": partitions["forward_count"]})
    assert priced[0]["predicted_reference_us"] > 0
    assert priced[0]["boundary"] == "single_declared_program_reference"
    assert len(priced[0]["declared_programs"]) == 1


def test_replaced_semantic_members_fail_before_empty_graph_cost(evidence):
    helper, case, partitions, manifest = evidence
    refs, _, _ = helper.prepare_references(partitions, manifest)
    ref = deepcopy(refs[0])
    ids = ref["source_correspondence"]["semantic_member_ids"]
    targets = [n for n in manifest["nodes"] if n["node_id"] in ids]
    ref["representative_target_ids"] = [n["node_id"] for n in targets]
    ref["physical_program_signatures"] = [n["physical_signature"] for n in targets]
    ref["physical_work_per_program"] = [n["physical_work"] for n in targets]
    from body_source_role_references import predict_source_role_references
    with pytest.raises(ValueError, match="source_role_reference_targets_missing_from_fresh_graph"):
        predict_source_role_references(case, manifest, {
            "source_role_references": [ref], "forward_count": partitions["forward_count"]})


def test_one_layer_resource_change_cannot_reuse_whole_native_histogram(evidence):
    helper, _, partitions, original = evidence
    manifest = deepcopy(original)
    resource = next(n for n in manifest["resource_operators"] if n["layer"] == 19)
    resource["physical_work"]["hbm_bytes"] *= 2
    refs, unresolved, _ = helper.prepare_references(partitions, manifest)
    assert len(unresolved) == 1
    assert unresolved[0]["reason"] == "heterogeneous_fresh_layer_programs_cannot_split_saved_histogram"
    assert sum(r["observed_us"]["count"] for r in refs) + unresolved[0]["event_count"] == 1302
