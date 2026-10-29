"""Real SharedKV descriptors narrow physical alternatives without layer claims.

Captured descriptors remain unchanged except explicitly identified timing,
missing-field and contradictory-declaration controls. No timing chooses a bucket.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from mindie_profiler.events import Observation, ProfilerUsageError, QueryStats, SourceRef, Window
from mindie_profiler.normalized import kernel_rows
from mindie_profiler.structure_mapping import map_structure
from test_structure_cohorts import seal
from test_structure_subgraphs import bindings


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module", params=["v4f", "v4pro"])
def declared(request):
    structure = pytest.importorskip("mindie_sim.structure")
    root = Path(structure.__file__).resolve().parents[1]
    filename = {"v4f": "v4f-a3-w8a8-tp8.json", "v4pro": "v4pro-a3-w4a8-tp16.json"}
    case = json.loads((root / "examples/cases" / filename[request.param]).read_text())
    tokens = 4096 if request.param == "v4f" else 1024
    return request.param, case, structure.export_structure(case, phase="prefill", tokens=tokens)


def captured(key):
    path = (FIXTURES / "attention_cache_contracts/a3_deepseek_v4f_compressed.csv"
            if key == "v4f" else FIXTURES / "fusion_contracts/a3_v4pro.csv")
    rows = [row for row in kernel_rows(path, rank_id="rank_0", rank_index=0)
            if row.kind == "SparseAttnSharedkv" and row.input_shapes[2]]
    return path, rows


def observation(path, events):
    stat = path.stat()
    return Observation(
        "rank_0", 0, Window(min(event.start_ns for event in events),
                            max(event.end_ns for event in events)),
        None, events, SourceRef(
            "rank_0", 0, "csv", str(path.resolve()), path.name, None, stat.st_size,
            "retained_capture", "kernel_details", mtime_ns=stat.st_mtime_ns),
        QueryStats("rank_0", "heterogeneous_source_fixture"),
    )


def test_real_index_presence_splits_physical_candidates_once_without_layer_binding(declared):
    key, _, structure = declared
    path, rows = captured(key)
    assert len(rows) == 2
    # Equal intervals are a control: the real tensor descriptors alone must
    # distinguish sparse-index and no-index compressed attention.
    events = [replace(row.event, start_ns=100, end_ns=300) for row in rows]
    report = map_structure([observation(path, events)], structure)
    window = report["windows"][0]
    groups = window["cohorts"]
    assert len(groups) == 2
    assert {group["declared_instance_count"] for group in groups} == (
        {20, 21} if key == "v4f" else {30, 31})
    assert len({group["physical_signature"] for group in groups}) == 2
    assert sum(group["event_count"] for group in groups) == window["event_count"] == 2
    assert sum(group["activity_sum_ns"] for group in groups) == 400
    assert window["observed_busy_union_ns"] == 200
    assert window["cohort_excluded_event_counts"] == {}
    assert report["status_counts"] == {"ambiguous": 2}
    assert window["nodes"] == window["layers"] == window["subgraphs"] == []
    assert set(groups[0]["target_ids"]).isdisjoint(groups[1]["target_ids"])
    for group in groups:
        assert not group["occurrence_binding_implied"]
        assert group["multiplicity"]["steps_in_window"] is None
        assert sum(item["event_count"] for item in group["candidate_refinements"]) == 1
    for mapped in report["event_mappings"]:
        refinement = mapped["candidate_refinement"]
        assert refinement["candidate_count_before"] == (41 if key == "v4f" else 61)
        assert refinement["candidate_count_after"] == mapped["candidate_count"]
        assert not refinement["occurrence_binding_implied"]
        assert mapped["node_ids"] == []


def test_real_topk_descriptor_rejects_alternative_with_same_active_contract(declared):
    key, _, structure = declared
    path, rows = captured(key)
    row = next(row for row in rows if row.input_shapes[4])
    changed = deepcopy(structure)
    targets = [node for node in changed["nodes"]
               if node["structure"].get("indexer") and node.get("contract")
               and node["contract"][:2] == ["sparse_attention_active", "SparseAttnSharedkv"]]
    wrong = targets[0]
    # Independently declared alternative top-k changes physical work while the
    # older active contract intentionally remains identical.
    wrong["operator"]["metadata"]["indexed_attention_geometry"]["topk"] = (
        1024 if row.input_shapes[4][2] == 512 else 512)
    wrong["physical_signature"] = "sha256:controlled-alternate-topk"
    wrong["physical_work"]["mte2_bytes"] += 1024
    report = map_structure([observation(path, [row.event])], seal(changed))
    group = report["windows"][0]["cohorts"][0]
    assert wrong["node_id"] not in group["target_ids"]
    assert group["declared_instance_count"] == len(targets) - 1
    assert group["event_count"] == 1
    assert group["candidate_refinements"][0]["observed_descriptor"][0][2] == (
        512 if key == "v4f" else 1024)


def test_typed_empty_index_is_unknown_and_does_not_select_nonindexed_bucket(declared):
    key, _, structure = declared
    path, rows = captured(key)
    row = next(row for row in rows if not row.input_shapes[4])
    dtypes = row.event.input_dtypes.split(";")
    formats = row.event.input_formats.split(";")
    dtypes[4], formats[4] = "INT32", "ND"
    unknown = replace(row.event, input_dtypes=";".join(dtypes),
                      input_formats=";".join(formats))
    report = map_structure([observation(path, [unknown])], structure)
    assert report["event_mappings"][0]["candidate_refinement"] is None
    assert report["event_mappings"][0]["candidate_count"] == (41 if key == "v4f" else 61)
    assert report["windows"][0]["cohorts"] == []
    assert report["windows"][0]["cohort_excluded_event_counts"] == {
        "candidate_physical_work_differs": 1}


def test_unknown_declared_index_interface_is_retained_instead_of_guessing_a_bucket(declared):
    key, _, structure = declared
    path, rows = captured(key)
    row = next(row for row in rows if row.input_shapes[4])
    changed = deepcopy(structure)
    unknown = next(node for node in changed["nodes"]
                   if node["structure"].get("compress_ratio") == 128
                   and node.get("contract")
                   and node["contract"][:2] == ["sparse_attention_active", "SparseAttnSharedkv"])
    unknown["structure"].pop("indexer")
    report = map_structure([observation(path, [row.event])], seal(changed))
    mapped = report["event_mappings"][0]
    assert unknown["node_id"] in mapped["candidate_node_ids"]
    assert mapped["candidate_refinement"]["unknown_declaration_candidates_retained"] == 1
    assert report["windows"][0]["cohorts"] == []
    assert report["windows"][0]["cohort_excluded_event_counts"] == {
        "candidate_physical_work_differs": 1}


def test_wrong_declared_topk_reports_descriptor_mismatch_without_reusing_other_branch(declared):
    key, _, structure = declared
    path, rows = captured(key)
    row = next(row for row in rows if row.input_shapes[4])
    changed = deepcopy(structure)
    for node in changed["nodes"]:
        geometry = node.get("operator", {}).get("metadata", {}).get("indexed_attention_geometry")
        if geometry:
            geometry["topk"] = 1024 if key == "v4f" else 512
    report = map_structure([observation(path, [row.event])], seal(changed))
    mapped = report["event_mappings"][0]
    assert mapped["candidate_count"] == 0
    assert mapped["basis"] == mapped["diagnostic"]["reason"] == "declared_index_descriptor_mismatch"
    assert report["windows"][0]["cohorts"] == []
    assert report["windows"][0]["operators"][0]["cohort_event_count"] == 0


def test_incompatible_explicit_layer_annotation_cannot_override_native_index_interface(declared):
    key, _, structure = declared
    path, rows = captured(key)
    row = next(row for row in rows if row.input_shapes[4])
    wrong = next(node for node in structure["nodes"]
                 if node["structure"].get("compress_ratio") == 128
                 and node.get("contract")
                 and node["contract"][:2] == ["sparse_attention_active", "SparseAttnSharedkv"])
    with pytest.raises(ProfilerUsageError, match="index descriptor mismatch"):
        map_structure(
            [observation(path, [row.event])], structure,
            bindings=bindings(structure, events=[{
                "event_id": row.event.event_id, "node_ids": [wrong["node_id"]],
                "evidence": {"source": "controlled contradictory occurrence annotation"},
            }]))


def test_compressor_precision_mismatch_remains_visible_despite_matching_ratio(declared):
    key, _, structure = declared
    path = FIXTURES / "fusion_contracts" / f"a3_{key}.csv"
    events = [row.event for row in kernel_rows(path, rank_id="rank_0", rank_index=0)
              if row.kind == "Compressor"]
    report = map_structure([observation(path, events)], structure)
    window = report["windows"][0]
    assert window["cohorts"] == []
    assert window["operators"][0]["cohort_excluded_event_counts"] == {
        "no_tensor_candidates": len(events)}
    assert all(row["diagnostic"]["category"] == "declared_structure_mismatch"
               for row in report["event_mappings"])
