"""Retained GLM full-ABI populations stay conditional under accepted-state programs."""
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
    from mindie_sim.structure import export_structure
    sys.path.insert(0, str(ROOT / "examples/structure"))
    native = importlib.import_module("glm_native_references")
    selected = importlib.import_module("glm_kda_accepted_references")
    path = ROOT / "examples/structure/acceptance-20261030-glm-native-partitions/a5_glm53flash_tp8_c32_p4k-native-partitions.json"
    partition = json.loads(path.read_text())
    partition["partitions"] = [g for g in partition["partitions"] if g["native_operator_type"] == "RecurrentKda"]
    raw = json.loads(Path(partition["case_identity"]["path"]).read_text())
    raw["runtime"]["kernels"]["lowerings"] = {"kda": {
        "implementation": "vllm_ascend_recurrent_kda_arch35", "options": {
            "safe_gate": True, "use_beta_sigmoid": True, "state_selection": {
                "kind": "symbolic_valid_selection", "index_layout": "speculative", "index_row_stride": 4,
                "validity": {"prefix": True, "state_indices": True,
                             "accepted_tokens": True, "independent_sequences": True}}}}}
    manifest = export_structure(raw, phase="decode", tokens=4, sequences=32, context=4104, scope="body")
    return native, selected, partition, manifest


def test_full_accepted_bucket_selects_all_queries_and_preserves_unknown_flags(evidence):
    native, selected, partition, manifest = evidence
    refs, unresolved, _ = native.prepare_references(partition, manifest, selectors=selected.SELECTORS)
    assert not unresolved
    ref, = refs
    assert ref["observed_us"]["count"] == 1054
    assert ref["duration_ns_counter"] == partition["partitions"][0]["duration_ns_counter"]
    assert len(ref["layer_ids"]) == 34
    assert len(ref["representative_target_ids"]) == 1
    correspondence = ref["source_correspondence"]
    assert correspondence["declared_total_query_work"] == 128
    assert correspondence["state_selection"]["acceptance_changes_query_work"] is False
    assert correspondence["observed_accepted_token_values"] is None
    assert correspondence["declared_kernel_flags"]["use_beta_sigmoid"] is True
    assert correspondence["observed_kernel_flags"] is None
    assert ref["strict_accuracy_implied"] is ref["additional_budget_allowed"] is False


def test_partial_query_execution_cannot_reuse_complete_observed_bucket(evidence):
    native, selected, partition, original = evidence
    manifest = deepcopy(original)
    target = next(n for n in manifest["nodes"] if n["node_id"] == "rank:0/s0.l0.recurrent_scan0")
    target["operator"]["metadata"]["kda_recurrent_params"]["lengths"][0] = 1
    refs, unresolved, _ = native.prepare_references(partition, manifest, selectors=selected.SELECTORS)
    assert not refs
    assert unresolved[0]["event_count"] == 1054
    assert unresolved[0]["reason"] == "accepted_kda_declared_source_geometry_or_precision"


def test_fp32_external_beta_branch_is_not_reinterpreted_as_in_kernel_bf16(evidence):
    native, selected, original, manifest = evidence
    partition = deepcopy(original)
    partition["partitions"][0]["native_abi"][2][4][1] = "fp32"
    refs, unresolved, _ = native.prepare_references(partition, manifest, selectors=selected.SELECTORS)
    assert not refs
    assert unresolved[0]["reason"] == "kda_gate_state_metadata_abi"
