"""Complete retained V4.1 MX32/HC populations against shared source programs."""
from copy import deepcopy
from collections import Counter
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
    helper = importlib.import_module("v41_mx32_hc_references")
    sim_root = Path(sim.__file__).resolve().parents[1]
    case_path = sim_root / "examples/cases/high-concurrency-20261030/v41-mc2-mx32-conditional/a5_v41_fp8_tp1_dp8_ep8_c32_p2k-mx32-fullmesh-source.json"
    if not case_path.exists():
        pytest.skip("companion Sim MX32 source declaration unavailable")
    raw = json.loads(case_path.read_text())
    raw["runtime"]["kernels"]["lowerings"]["native_fusion"]["options"]["traffic_profile"] = {
        "hc_pre": helper.PRE_PROFILE, "hc_post": "hc_post_arch35_bf16_175ef4d4"}
    prepared_path = sim_root / "examples/cases/high-concurrency-20261030/v41-mx32-conditional/a5_v41_fp8_tp1_dp8_ep8_c128_p2k-prepared-mx32-source.json"
    prepared = json.loads(prepared_path.read_text())
    raw["runtime"]["kernels"]["lowerings"]["mx_matrix"] = prepared["runtime"]["kernels"]["lowerings"]["mx_matrix"]
    actual = json.loads((ROOT / "examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-a5_v41_fp8_tp1_dp8_ep8_c32_p2k-matrix-extension.actual.json").read_text())
    case = parse_case(raw)
    execution = {"phase": "decode", "tokens": 1, "sequences": 4,
                 "context": actual["conditional_context_tokens"], "scope": "body"}
    # Full target construction validates the declared eight-peer traffic. The
    # metadata selector fixture needs one replica's forty layers, not eight
    # duplicate serialized manifests; this never evaluates a reduced cost case.
    manifest = export_structure(case, **execution, replicas=(0,))
    return helper, actual, manifest


def test_complete_mx32_protocol_and_partial_hc_branch_preserve_all_forty_layers(evidence):
    helper, actual, manifest = evidence
    refs, unresolved, _ = helper.prepare_references(actual, manifest)
    assert not unresolved
    assert len(refs) == 4 and sum(g["observed_us"]["count"] for g in refs) == 16800
    old = {g["group_id"]: g for g in actual["source_role_references"]}
    for group in refs:
        original = old[group["retained_group_id"]]
        assert group["duration_ns_counter"] == original["duration_ns_counter"]
        assert group["observed_us"] == original["observed_us"]
        assert group["layer_ids"] == list(range(40))
        assert not group["strict_accuracy_implied"] and not group["additional_budget_allowed"]
    dispatch = next(g for g in refs if g["native_operator_type"] == "MoeDistributeDispatchV3")
    assert len(dispatch["representative_target_ids"]) == 16
    relation = dispatch["source_correspondence"]
    assert relation["observed_buffer_row_capacity"] == 192
    assert relation["observed_valid_routed_rows"] is None
    assert {p["received_assignments"] for p in relation["declared_source_phases"]} == {24}
    for group in refs:
        if group["native_operator_type"] == "HcPre":
            assert len(group["representative_target_ids"]) == 1
            assert group["source_correspondence"]["unmodeled_native_tensor_slots"] == {"inputs": [4], "outputs": [3]}


def test_bf16_dispatch_cannot_be_relabelled_as_captured_mx32(evidence):
    helper, actual, manifest = evidence
    changed = deepcopy(actual)
    group = next(g for g in changed["source_role_references"] if g["native_operator_type"] == "MoeDistributeDispatchV3")
    group["source_correspondence"]["observed_native_tensor_contract"][3][0][1] = "bf16"
    refs, unresolved, _ = helper.prepare_references(changed, manifest)
    assert len(unresolved) == 1 and unresolved[0]["reason"] == "v41_mx32_dispatch_full_abi"
    assert unresolved[0]["event_count"] == 4200
    assert sum(g["observed_us"]["count"] for g in refs) == 12600


def test_one_changed_source_layer_does_not_split_the_retained_native_histogram(evidence):
    helper, actual, manifest = evidence
    nodes = list(manifest["nodes"])
    index = next(i for i, n in enumerate(nodes) if n["layer"] == 19 and
        n["operator"]["metadata"].get("native_kind") == "MoeDistributeDispatchV3")
    node = nodes[index]
    nodes[index] = {**node, "physical_work": {**node["physical_work"], "hbm_bytes": node["physical_work"]["hbm_bytes"] + 256}}
    refs, unresolved, _ = helper.prepare_references(actual, {**manifest, "nodes": nodes})
    assert len(unresolved) == 1
    assert unresolved[0]["reason"] == "v41_fresh_source_work_differs_across_saved_layers"
    assert unresolved[0]["event_count"] == 4200
    assert sum(g["observed_us"]["count"] for g in refs) == 12600


def test_old_hc_program_is_not_claimed_as_new_arch35_source(evidence):
    helper, actual, manifest = evidence
    groups = []
    for group in manifest["subgraphs"]:
        if group["role"] == "hc_pre":
            group = {**group, "resource_boundary": {**group["resource_boundary"],
                "traffic_profile": "hc_pre_m_k_split_175ef4d4"}}
        groups.append(group)
    refs, unresolved, _ = helper.prepare_references(actual, {**manifest, "subgraphs": groups})
    assert len(unresolved) == 2
    assert {r["reason"] for r in unresolved} == {"v41_hc_pre_arch35_resource_not_selected"}
    assert sum(r["event_count"] for r in unresolved) == 8400
    assert sum(g["observed_us"]["count"] for g in refs) == 8400


def test_prepared_output_and_expert_populations_remain_separate_complete_groups(evidence):
    helper, actual, manifest = evidence
    path = ROOT / "examples/structure/acceptance-20261030-v41-native-partitions/a5_v41_fp8_tp1_dp8_ep8_c32_p2k-native-partitions.json"
    partitions = json.loads(path.read_text())
    refs, unresolved, compact = helper.prepare_affected_references(actual, partitions, manifest)
    assert not unresolved
    assert len(refs) == 10 and sum(g["observed_us"]["count"] for g in refs) == 33600
    grouped = [g for g in refs if g["native_operator_type"] == "GroupedMatmul"]
    assert {g["declared_role"] for g in grouped} == {"expert_up", "expert_down"}
    for group in grouped:
        old = next(g for g in actual["source_role_references"] if g["group_id"] == group["retained_group_id"])
        assert group["duration_ns_counter"] == old["duration_ns_counter"]
        assert group["source_correspondence"]["observed_valid_routed_rows"] is None
    output = next(g for g in refs if g["native_operator_type"] == "TransposeQuantBatchMatMul")
    assert output["declared_role"] == "grouped_output_a"
    assert output["source_correspondence"]["selected_output_boundary"] == "aic_fixpipe_bf16_to_gm"
    assert output["source_correspondence"]["prepared_mx32_source_selected"]
    original_hist = Counter()
    for index in output["partition_indices"]:
        original_hist.update(dict(partitions["partitions"][index]["duration_ns_counter"]))
    assert dict(output["duration_ns_counter"]) == original_hist
    target = next(n for n in compact["nodes"] if n["node_id"] == output["representative_target_ids"][0])
    assert target["operator"]["metadata"]["fixpipe_bytes"] > 0
    assert target["physical_work"]["mte3_bytes"] == 0


def test_mqsmla_ratio_populations_do_not_claim_a_missing_native_abi(evidence):
    helper, actual, manifest = evidence
    refs, failures, _ = helper.prepare_attention_symbols(actual, manifest)
    assert not failures and len(refs) == 3
    assert sum(g["observed_us"]["count"] for g in refs) == 4200
    assert sorted(g["source_correspondence"]["declared_mqsmla_geometry"]["ratio"] for g in refs) == [0, 1, 2]
    for group in refs:
        old = next(g for g in actual["source_role_references"] if g["group_id"] == group["retained_group_id"])
        assert group["duration_ns_counter"] == old["duration_ns_counter"]
        assert group["layer_ids"] == old["layer_ids"]
        assert group["source_correspondence"]["observed_native_tensor_contract"] is None
        assert not group["source_correspondence"]["complete_native_abi_available"]
        assert not group["strict_accuracy_implied"]


def test_normalized_cohorts_keep_full_histogram_and_dp_condition_without_strict_upgrade(evidence):
    _, actual, manifest = evidence
    helper = importlib.import_module("compare_v41_composed_cohorts")
    path = ROOT / "examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-a5_v41_fp8_tp1_dp8_ep8_c32_p2k-matrix-extension.mapping.json"
    mapping = json.loads(path.read_text())
    groups, failures, _ = helper.prepare_references(actual, mapping, manifest)
    assert not failures and len(groups) == 4
    assert sum(g["observed_us"]["count"] for g in groups) == 16800
    for group in groups:
        family = next(f for f in actual["families"] if f["declared_role"] == group["declared_role"])
        assert group["duration_ns_counter"] == family["duration_ns_counter"]
        assert group["layer_ids"] == list(range(40))
        assert group["source_correspondence"]["declared_cohort_replicas"] == list(range(8))
        assert group["native_abi"] is None and group["observed_contract"]
        assert not group["strict_accuracy_implied"] and not group["additional_budget_allowed"]


def test_partial_matrix_cohort_cannot_borrow_whole_family_latency_distribution(evidence):
    _, actual, manifest = evidence
    helper = importlib.import_module("compare_v41_composed_cohorts")
    path = ROOT / "examples/structure/acceptance-20261030-v41-operators-09811dad/body-operator-a5_v41_fp8_tp1_dp8_ep8_c32_p2k-matrix-extension.mapping.json"
    mapping = json.loads(path.read_text())
    old = next(g for w in mapping["windows"] for g in w["cohorts"]
        if mapping["conditional_role_by_cohort_id"][g["cohort_id"]] == ["q_b"])
    old["event_count"] -= 1
    groups, failures, _ = helper.prepare_references(actual, mapping, manifest)
    assert len(failures) == 1 and failures[0]["declared_role"] == "q_b"
    assert failures[0]["reason"] == "whole_family_histogram_is_not_exact_complete_cohort"
    assert sum(g["observed_us"]["count"] for g in groups) == 12600


def test_join_retains_disjoint_histograms_and_counts_source_forwards_once():
    helper = importlib.import_module("join_v41_composed_references")
    directory = ROOT / "examples/structure/acceptance-20261030-v41-composed-native-5ec8843a"
    first = directory / "v41-composed-native-reference-scoreboard.json"
    second = directory / "normalized-cohorts/v41-normalized-reference-scoreboard.json"
    result = helper.join(first, second)
    assert sum(case["forward_count"] for case in result["cases"]) == 830
    assert sum(len(case["groups"]) for case in result["cases"]) == 98
    assert sum(case["referenced_event_count"] for case in result["cases"]) == 398400
    assert result["strict_compared"] == result["new_predictions_in_join"] == 0
    originals = [json.loads(path.read_text()) for path in (first, second)]
    for case in result["cases"]:
        expected = {
            group["group_id"]: group["duration_ns_counter"]
            for report in originals for source in report["cases"]
            if source["case_id"] == case["case_id"] for group in source["groups"]
        }
        assert len(expected) == 14
        assert {g["group_id"]: g["duration_ns_counter"] for g in case["groups"]} == expected
