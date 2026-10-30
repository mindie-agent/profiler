"""Offline real-capture acceptance of the sim-to-profiler structure contract.

The graph and event bindings below are controlled declarations. They do not
claim that the captured A5 program ran this two-layer model or a fused RmsNorm.
"""
from copy import deepcopy
import csv
from hashlib import sha256
import json
from pathlib import Path

import pytest
from tests.sim_fixtures import case_path

from mindie_profiler.analyze import analyze_profile


@pytest.fixture(scope="module")
def real_capture():
    structure = pytest.importorskip("mindie_sim.structure")
    fixture_dir = case_path('operator-kernels.csv').parent
    capture = fixture_dir / "operator-kernels.csv"
    provenance = json.loads((fixture_dir / "operator-kernels.provenance.json").read_text())
    assert sha256(capture.read_bytes()).hexdigest() == provenance["fixture_sha256"]
    return structure, capture, provenance


@pytest.fixture(scope="module")
def manifest(real_capture):
    structure, _, _ = real_capture
    # The ordinary Case schema requires machine fields; export never evaluates
    # these declared rates or claims that they describe the capture hardware.
    case = {
        "machine": {
            "name": "structure-only-declaration", "architecture": "cuda", "num_devices": 1,
            "device": {
                "memory_bytes": 64 * 1024 ** 3,
                "compute_peaks": {"bf16": 1e9, "fp32": 1e9},
                "rates": {"memory": 1e9, "vector": 1e9}, "compute_units": 4,
            },
            "links": [{"name": "fabric", "capacity_bytes_per_ms": 1000,
                       "members": [0], "semantics": "shared"}],
        },
        "model": {
            "name": "declared-contract-geometry", "layers": 2, "hidden_size": 5120,
            "num_heads": 40, "num_kv_heads": 8, "head_dim": 128,
            "intermediate_size": 13824, "vocab_size": 128,
        },
        "workload": {"requests": [{"id": "r", "prompt_tokens": 16384, "output_tokens": 1}]},
        "runtime": {"dp": 1, "tp": 1, "pp": 1, "ep": 1, "max_num_batched_tokens": 16384},
    }
    return structure.export_structure(
        case, phase="prefill", tokens=16384, scope="body",
        source={"kind": "controlled_contract_declaration", "not_capture_model_identity": True},
    )


def analyze(capture, manifest, *, bindings=None, mapping_limit=200):
    return analyze_profile(
        capture, source="csv", full_range=True, structure=manifest,
        structure_bindings=bindings, mapping_limit=mapping_limit,
    )["structure_mapping"]


def norm_event(mapping):
    return next(row for row in mapping["event_mappings"] if row["kernel_name"] == "RmsNorm")


def explicit_binding(manifest, event, node_ids, relation="direct"):
    return {
        "schema_version": "mindie-profile-bindings/1", "graph_id": manifest["graph_id"],
        "rank_replicas": {event["rank_id"]: 0},
        "events": [{
            "event_id": event["event_id"], "node_ids": node_ids, "relation": relation,
            "evidence": {"source": "test-declared association; not hardware module evidence"},
        }],
    }


def test_real_capture_retains_repeated_layers_and_missing_observations(real_capture, manifest):
    _, capture, provenance = real_capture
    mapping = analyze(capture, manifest)
    event = norm_event(mapping)
    assert event["status"] == "ambiguous"
    assert set(event["candidate_node_ids"]) == {
        "rank:0/s0.l0.norm1", "rank:0/s0.l0.norm2",
        "rank:0/s0.l1.norm1", "rank:0/s0.l1.norm2",
    }
    assert event["node_ids"] == []
    assert event["observed_contract"] == ("rmsnorm", (16384, 5120), "bf16", True)
    assert event["end_ns"] - event["start_ns"] == 108_051
    assert event["source"] == str(capture)
    assert event["locator"]["csv_line"] == 2
    assert provenance["source_lines"][event["locator"]["row_index"]] == 45
    assert mapping["windows"][0]["bound_busy_union_ns"] == 0
    assert mapping["windows"][0]["nodes"] == []
    assert mapping["windows"][0]["unobserved_node_ids"]
    missing = [row for row in mapping["event_mappings"]
               if row["kernel_name"] == "fused_gdn_gating_kernel"
               and row["observed_contract"] is None]
    assert missing
    assert all(row["status"] == "unmapped" and not row["node_ids"] for row in missing)


@pytest.mark.parametrize("relation", ["direct", "fusion"])
def test_explicit_occurrence_counts_once_with_shared_node_attribution(
    real_capture, manifest, relation,
):
    _, capture, _ = real_capture
    baseline = analyze(capture, manifest)
    event = norm_event(baseline)
    ids = ["rank:0/s0.l0.norm1"]
    if relation == "fusion":
        ids.append("rank:0/s0.l0.norm2")
    bindings = explicit_binding(manifest, event, ids, relation)
    mapped = analyze(capture, manifest, bindings=bindings)
    bound = norm_event(mapped)
    assert bound["basis"] == "explicit_evidence"
    assert bound["evidence"] == bindings["events"][0]["evidence"]
    assert bound["node_ids"] == ids
    assert mapped["status_counts"]["bound"] == 1
    assert mapped["status_counts"]["unmapped"] == baseline["status_counts"]["unmapped"]
    window = mapped["windows"][0]
    assert window["bound_busy_union_ns"] == 108_051
    assert window["layers"][0]["busy_union_ns"] == 108_051
    assert window["layers"][0]["event_count"] == 1
    assert {row["node_id"] for row in window["nodes"]} == set(ids)
    for node in window["nodes"]:
        assert node["busy_union_ns"] == node["activity_sum_ns"] == 108_051
        assert node["shared_event_count"] == int(relation == "fusion")
    hidden = analyze(capture, manifest, bindings=bindings, mapping_limit=0)
    assert hidden["event_mappings"] == []
    assert hidden["event_mappings_truncated"] is True
    assert hidden["windows"] == mapped["windows"]
    assert hidden["status_counts"] == mapped["status_counts"]


def test_duration_control_changes_measurement_without_changing_candidates(
    real_capture, manifest, tmp_path,
):
    _, capture, provenance = real_capture
    original_manifest = deepcopy(manifest)
    baseline = analyze(capture, manifest)
    with capture.open(newline="") as source:
        reader = csv.DictReader(source)
        fields, rows = reader.fieldnames, list(reader)
    rows[0]["Duration(us)"] = "216.102"
    altered = tmp_path / "duration-control.csv"
    with altered.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    changed = analyze(altered, manifest)
    assert manifest == original_manifest
    assert [
        (row["locator"]["row_index"], row["status"], row["candidate_node_ids"])
        for row in changed["event_mappings"]
    ] == [
        (row["locator"]["row_index"], row["status"], row["candidate_node_ids"])
        for row in baseline["event_mappings"]
    ]
    first, second = norm_event(baseline), norm_event(changed)
    assert second["event_id"] != first["event_id"]
    assert second["end_ns"] - second["start_ns"] == 2 * (first["end_ns"] - first["start_ns"])
    bound = analyze(
        altered, manifest,
        bindings=explicit_binding(manifest, second, ["rank:0/s0.l0.norm1"]),
    )
    assert bound["windows"][0]["bound_busy_union_ns"] == 216_102
    assert sha256(capture.read_bytes()).hexdigest() == provenance["fixture_sha256"]


def test_real_db_replay_binds_only_selected_occurrences_to_one_node(manifest):
    fixture_dir = Path(__file__).resolve().parent / "fixtures/profiler_core/real_glm45"
    capture = fixture_dir / "rank_0/ASCEND_PROFILER_OUTPUT/ascend_pytorch_profiler_0.db"
    provenance = json.loads((fixture_dir / "slice_provenance.json").read_text())
    assert sha256(capture.read_bytes()).hexdigest() == provenance["slice"]["db_sha256"]
    baseline = analyze_profile(
        capture, source="db", full_range=True, structure=manifest, mapping_limit=2000,
    )["structure_mapping"]
    occurrences = [
        row for row in baseline["event_mappings"]
        if row["locator"].get("task_global_id") == 1132
    ]
    assert len(occurrences) == 26
    assert len({row["event_id"] for row in occurrences}) == 26
    assert all(row["observed_contract"] is None and row["status"] == "unmapped"
               for row in occurrences)
    selected = occurrences[:2]
    assert selected[0]["end_ns"] < selected[1]["start_ns"]
    # Missing DB tensors remain unknown. These explicit test declarations only
    # exercise occurrence identity and many-event accounting, not layer proof.
    bindings = explicit_binding(manifest, selected[0], ["rank:0/s0.l0.norm1"])
    bindings["events"].extend(
        explicit_binding(manifest, row, ["rank:0/s0.l0.norm1"])["events"][0]
        for row in selected[1:]
    )
    mapped = analyze_profile(
        capture, source="db", full_range=True, structure=manifest,
        structure_bindings=bindings, mapping_limit=2000,
    )["structure_mapping"]
    bound = [row for row in mapped["event_mappings"] if row["status"] == "bound"]
    assert {row["event_id"] for row in bound} == {row["event_id"] for row in selected}
    assert all(row["basis"] == "explicit_evidence" and row["observed_contract"] is None
               for row in bound)
    expected = sum(row["end_ns"] - row["start_ns"] for row in selected)
    window = mapped["windows"][0]
    assert window["bound_busy_union_ns"] == expected
    assert window["nodes"][0]["busy_union_ns"] == expected
    assert window["nodes"][0]["event_count"] == 2
    assert mapped["status_counts"]["unmapped"] == baseline["event_window_count"] - 2
