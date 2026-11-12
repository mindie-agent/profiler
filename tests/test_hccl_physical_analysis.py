"""Product-path regression on the real COMRUN5A AIV HCCL packet.

The caller supplies only the genuine two-rank output directory and the shared
native plan; `analyze_profile` must discover rank_0/rank_1, join both raw DB
presentations through the real CANN TASK/COMMUNICATION_OP keys, and report one
deduplicated call per rank.  CSV-only input has no relational keys and must
stay explicitly unresolved.  No hardware is touched.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest

PACKET = Path("/tmp/mindie-7337-20261111-1457/COMRUN5A/remote-return/run/out")
EVIDENCE = Path("/Volumes/data/code/mindie-release-20261014/sim/examples/"
                "source-families/hccl-comrun5a-allgather.json")

pytestmark = pytest.mark.skipif(
    not PACKET.is_dir() or not EVIDENCE.is_file(),
    reason="real COMRUN5A profile bundle is not present in this checkout")


def _structure():
    analysis = pytest.importorskip("mindie_sim.prediction.operator_analysis")
    del analysis
    schema = pytest.importorskip("mindie_sim.schema.operators")
    hccl_graph = pytest.importorskip("mindie_sim.prediction.hccl_graph")
    structure_module = pytest.importorskip("mindie_sim.structure")
    import json

    evidence = json.loads(EVIDENCE.read_text())
    op = schema.OpSpec(
        "s0.l0.tp_all_gather", "allgather", "decode", 0, 0, (),
        (5120,), (5120,), (5120,), (5120,), link_bytes=10240,
        dtype="bf16", metadata=(("group_axis", "tp"),
                                ("collective", "allgather"),
                                ("hccl_observed_call", evidence["call"])))
    lowered = hccl_graph.lower((op,), SimpleNamespace(kernels={}), "bf16")[0]
    return structure_module.export_op_structure(
        {0: (lowered,), 1: (lowered,)}, model={},
        execution={"phase": "decode"}), evidence


def _bindings(structure):
    return {"schema_version": "mindie-profile-bindings/1",
            "graph_id": structure["graph_id"],
            "rank_replicas": {"rank_0": "0", "rank_1": "1"}}


def test_whole_directory_discovery_uses_real_rank_names():
    segment = pytest.importorskip("mindie_profiler.segment")
    sources = segment.discover_rank_sources(PACKET, source="auto")
    assert [(source.rank_id, source.rank_index) for source in sources] == [
        ("rank_0", 0), ("rank_1", 1)]
    assert {source.kind for source in sources} == {"db"}


def test_public_analyze_profile_links_two_ranks_and_dedups_the_call():
    analyze = pytest.importorskip("mindie_profiler.analyze")
    structure, evidence = _structure()
    # The shared plan alone carries rank_0/rank_1 aliases; no bindings needed.
    report = analyze.analyze_profile(
        PACKET, source="auto", structure=structure,
        full_range=True, hash_sources=False, mapping_limit=50)
    mapping = report["structure_mapping"]
    assert mapping["native_call_count"] == 2
    assert mapping["native_call_identity_counts"] == {"observed_raw_identity": 4}
    calls = {(call["rank_id"], call["call_id"]) for call in mapping["native_calls"]}
    assert len(calls) == 2
    assert len({call["call_id"] for call in mapping["native_calls"]}) == 1
    assert {call["call_owner"] for call in mapping["native_calls"]} == {
        "s0.l0.tp_all_gather"}
    # Two raw presentations per rank, but one call and one activity range.
    assert {call["presentation_count"] for call in mapping["native_calls"]} == {2}
    assert {call["charge"] for call in mapping["native_calls"]} == {"call"}
    activities = {call["rank_id"]: call["activity_ns"] for call in mapping["native_calls"]}
    assert activities == {"rank_0": 56348811, "rank_1": 13445}
    # Raw rows are preserved; only their call accounting is deduplicated.
    assert mapping["status_counts"] == {"unmapped": 4}
    assert {
        (row["rank_id"], row["kernel_name"]) for row in mapping["event_mappings"]
    } == {("rank_0", "AivKernel"), ("rank_0", "hcom_allGather__612_0_1"),
          ("rank_1", "AivKernel"), ("rank_1", "hcom_allGather__612_0_1")}
    for row in mapping["event_mappings"]:
        assert row["native_call_identity"] == "observed_raw_identity"
        assert row["native_call_occurrence"]["charge"] == "call"


def test_csv_only_is_honest_unresolved_without_relational_keys():
    analyze = pytest.importorskip("mindie_profiler.analyze")
    structure, _ = _structure()
    report = analyze.analyze_profile(
        PACKET, source="csv", structure=structure,
        structure_bindings=_bindings(structure), full_range=True,
        hash_sources=False, mapping_limit=50)
    mapping = report["structure_mapping"]
    assert mapping["native_call_count"] == 0
    assert mapping["native_call_identity_counts"] == {
        "unresolved_alias_without_relational_keys": 4}
    assert all(row["implementation_correspondence"] is None
               for row in mapping["event_mappings"])
    assert mapping["status_counts"] == {"unmapped": 4}


def test_db_compute_and_comm_share_the_real_relational_keys():
    analyze = pytest.importorskip("mindie_profiler.analyze")
    structure, _ = _structure()
    report = analyze.analyze_profile(
        PACKET, source="db", structure=structure,
        structure_bindings=_bindings(structure), full_range=True,
        hash_sources=False, mapping_limit=50)
    rows = report["structure_mapping"]["event_mappings"]
    by_rank = {}
    for row in rows:
        by_rank.setdefault(row["rank_id"], {})[row["kernel_name"]] = row["locator"]
    for rank in ("rank_0", "rank_1"):
        compute = by_rank[rank]["AivKernel"]
        comm = by_rank[rank]["hcom_allGather__612_0_1"]
        assert compute["connection_id"] == comm["connection_id"] == "2"
        assert str(compute["task_global_id"]) == str(comm["global_task_id"]) == "5"
        assert compute["stream_id"] == comm["stream_id"] == "26"
        assert compute["task_id"] == comm["task_id"] == "17"
        assert compute["device_id"] == comm["device_id"]
        assert comm["algorithm"] == "AlgType::NHR"
        assert comm["count"] == 5120
