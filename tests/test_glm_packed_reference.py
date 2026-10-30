"""Retained A3 GLM full-ABI buckets never become the rope64 source contract."""
from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def packed_evidence():
    pytest.importorskip("mindie_sim.structure")
    from mindie_sim.structure import export_structure
    import sys
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "examples/structure"))
    helper = importlib.import_module("glm_native_references")
    selectors = importlib.import_module("glm_source_mechanism_references").SELECTORS
    path = root / "examples/structure/acceptance-20261030-glm-source-mechanisms/a3_glm53flash_tp16_aclgraph_c32-native-partitions.json"
    partition = json.loads(path.read_text())
    raw = json.loads(Path(partition["case_identity"]["path"]).read_text())
    raw["runtime"]["kernels"]["programs"]["indexed_attention"] = {
        "kind": "indexed_attention_packed_int8", "scratch_policy": "offchip"}
    manifest = export_structure(raw, phase="decode", tokens=6, sequences=32, context=4096, scope="body")
    return helper, selectors, partition, manifest


def test_complete_packed528_bucket_covers_every_sequence_without_promoting_values(packed_evidence):
    helper, selectors, partition, manifest = packed_evidence
    groups, failures, _ = helper.prepare_references(partition, manifest, selectors=selectors)
    assert not failures
    group, = groups
    assert group["observed_us"]["count"] == 539
    assert len(group["layer_ids"]) == 11
    assert group["duration_ns_counter"] == partition["partitions"][0]["duration_ns_counter"]
    correspondence = group["source_correspondence"]
    assert correspondence["declared_sequence_count"] == 32
    assert correspondence["observed_cache_row_bytes"] == 528
    assert correspondence["observed_index_values"] is None
    assert correspondence["observed_key_value_address_alias"] is None
    assert not group["strict_accuracy_implied"]


def test_672_byte_rope64_layout_cannot_be_bound_as_captured_528_bucket(packed_evidence):
    helper, selectors, partition, manifest = packed_evidence
    changed = deepcopy(partition)
    for slot in (1, 2):
        changed["partitions"][0]["native_abi"][2][slot][0][-1] = 672
    groups, failures, _ = helper.prepare_references(changed, manifest, selectors=selectors)
    assert not groups
    assert failures[0]["event_count"] == 539
    assert failures[0]["reason"] == "packed_sparse_int8_528_rope0_abi"


def test_missing_declared_sequence_cannot_take_full_native_batch_histogram(packed_evidence):
    helper, selectors, partition, manifest = packed_evidence
    nodes = deepcopy(manifest["nodes"])
    target = next(n for n in nodes if n["layer"] == 3 and
                  n["operator"]["metadata"].get("program_kind") == "indexed_attention")
    target["operator"]["metadata"]["indexed_attention_geometry"]["sequences"].pop()
    groups, failures, _ = helper.prepare_references(partition, {**manifest, "nodes": nodes}, selectors=selectors)
    assert not groups
    assert failures[0]["event_count"] == 539
    assert failures[0]["reason"] == "packed_sparse_declared_batch_coverage"
