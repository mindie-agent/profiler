"""BIND1 consumer: the profiler indexes the sim's actual-invocation identity.

These are the exact node dictionaries emitted by ``mindie_sim.structure`` for
an I-r64 QuantBatchMatmulV3 boundary; the profiler must join them without
claiming tensor or occurrence evidence.
"""
from mindie_profiler.structure_subgraphs import StructureTargets


def _qbmm_node(call_id="c" * 64):
    return {
        "node_id": "rank:0/s0.l0.q_a",
        "replica": 0,
        "stage": 0,
        "layer": 0,
        "block": "attention",
        "role": "q_a",
        "structure": {"kind": "attention_projection"},
        "family": "gemm",
        "recipe": "q_a",
        "contract": None,
        "implementation": {
            "native_kinds": ["QuantBatchMatmulV3", "QuantBatchMatmulV4"],
            "selection": "compatible_semantic_boundary; runtime_selection_not_implied",
        },
        "_native_call": {
            "schema": "mindie-sim/native-call-binding/1",
            "call_id": call_id,
            "op_id": "s0.l0.q_a",
            "family": "gemm",
            "recipe": "q_a",
            "source_boundary": "kernel",
            "api": {"namespace": "cann_kernel", "entry": "QuantBatchMatmulV3",
                    "aclnn_symbol": None, "candidates": []},
            "source": {"path": "quant_batch_matmul_v3/arch35/quant_batch_matmul_v3.cpp",
                       "sha256": "13daf996890d70e7b1dc9275ab3a464043860e67d6df730e28742393c023ec88"},
            "typed": {"dtype": "int8", "layout": "int8_per_channel",
                      "shapes": {"local": [64, 2048, 6144]}},
            "kernels": [{"name": "QuantBatchMatmulV3", "role": "cube",
                         "evidence": "source_declared"}],
            "evidence": {"entry": "source_declared", "aclnn_symbol": "unresolved",
                         "source": "source_declared", "kernels": "source_declared",
                         "core": "not_declared"},
            "unresolved": ["aclnn_symbol_unresolved", "execution_core_not_declared"],
        },
    }


def test_sim_call_identity_is_indexed_and_described_without_new_claims():
    node = _qbmm_node()
    record = {**node.pop("_native_call"), "node_id": node["node_id"]}
    index = StructureTargets({node["node_id"]: node}, (), [record])
    assert index.native_calls[record["call_id"]] == [node["node_id"]]
    assert index.native_call_entries["QuantBatchMatmulV3"] == [node["node_id"]]
    assert index.native_call_kernels["QuantBatchMatmulV3"] == [node["node_id"]]
    described = index.describe_implementation("QuantBatchMatmulV3", (node["node_id"],))
    assert described["native_call"]["call_id"] == record["call_id"]
    assert described["native_call"]["entry"] == "QuantBatchMatmulV3"
    assert described["native_call"]["kernels"] == ["QuantBatchMatmulV3"]
    assert described["tensor_match_implied"] is False
    assert described["occurrence_binding_implied"] is False


def test_nodes_without_bind1_keep_the_previous_behaviour():
    node = _qbmm_node()
    node.pop("_native_call")
    index = StructureTargets({node["node_id"]: node}, ())
    assert dict(index.native_calls) == {}
    described = index.describe_implementation("QuantBatchMatmulV3", (node["node_id"],))
    assert described["native_call"] is None


# ---------------------------------------------------------------------------
# Ordinary mapper control.
#
# mla-decode-control has no preserved hardware measurement.  The events below
# are prepare-only controls with declared tensor descriptors: they exercise
# the ordinary StructureMapper path and are never reported as measured
# hardware observations.
# ---------------------------------------------------------------------------
import json

import pytest

from mindie_profiler.accounting import account_window
from mindie_profiler.events import Event, Observation, QueryStats, SourceRef, Window
from mindie_profiler.structure_mapping import StructureMapper


def _mla_structure():
    structure = pytest.importorskip("mindie_sim.structure")
    operators = pytest.importorskip("mindie_sim.prediction.operators.mla_decode")
    program = pytest.importorskip("mindie_sim.prediction.program")
    op = operators.make_op({
        "implementation": operators.IMPLEMENTATION, "contexts": [16],
        "heads": 4, "key_heads": 1, "latent_dim": 256, "rope_dim": 32,
        "page_size": 16, "num_kv_splits": 2, "dtype": "bf16",
        "cache_dtype": "bf16", "is_mla": True, "is_hip": False})
    mapping = {"lowerings": {"mla_decode": "vllm_triton_mla_decode_tuple"}}
    expanded = program.RecipeBook.from_mapping(mapping).expand((op,))
    return structure.export_op_structure(
        {0: expanded, 1: expanded}, model={}, execution={"phase": "decode"},
        kernels=mapping)


def _control_event(name, *, shapes="1,4,288", dtypes="DT_BF16",
                   rank="rank_0", rank_index=0, task="1"):
    return Event(
        rank_id=rank, rank_index=rank_index, name=name, op_type=name,
        task_type="MIX_AIC", core="MIX_AIC", stream_id="1", task_id=task,
        device_id="0", start_ns=0, end_ns=100, source_kind="db",
        table="COMPUTE_TASK_INFO", input_shapes=shapes, input_dtypes=dtypes,
        input_formats="ND", output_shapes=shapes, output_dtypes=dtypes,
        output_formats="ND", locator={"source": "/prepare-only", "task_rowid": 1})


def _control_observation(events, *, rank="rank_0", rank_index=0):
    window = Window(0, 100, step=3)
    source = SourceRef(
        rank_id=rank, rank_index=rank_index, kind="db", path="/prepare-only",
        basename="prepare-only", sha256=None, size_bytes=1,
        schema_version="declared", schema_variant="prepare_only", mtime_ns=1)
    return Observation(rank, rank_index, window, account_window(events, window),
                       events, source, QueryStats(rank, "3"))


def _ordinary_correspondences(structure, events, *, rank="rank_0",
                              rank_index=0, rank_replicas=None):
    bindings = None
    if rank_replicas:
        bindings = {"schema_version": "mindie-profile-bindings/1",
                    "graph_id": structure["graph_id"],
                    "rank_replicas": rank_replicas}
    mapper = StructureMapper(structure, bindings=bindings)
    mapper.map_window(_control_observation(events, rank=rank, rank_index=rank_index))
    return [row.get("implementation_correspondence") for row in mapper.sample]


def test_ordinary_mapper_resolves_wrapper_and_both_launches_by_signature():
    structure = _mla_structure()
    names = ("decode_attention_fwd_grouped", "_fwd_grouped_kernel_stage1",
             "_fwd_kernel_stage2")
    correspondences = _ordinary_correspondences(
        structure, [_control_event(name, task=str(index))
                    for index, name in enumerate(names)],
        rank_replicas={"rank_0": "0"})
    assert len(correspondences) == 3
    call_ids = set()
    for name, correspondence in zip(names, correspondences):
        assert correspondence is not None, name
        assert correspondence["basis"] == "declared_native_call_signature"
        assert correspondence["rank"] == "rank_0"
        assert correspondence["signature_match"] is True
        call = correspondence["native_call"]
        assert call["entry"] == "decode_attention_fwd_grouped"
        assert call["kernels"] == ["_fwd_grouped_kernel_stage1",
                                   "_fwd_kernel_stage2"]
        assert call["declared_target_count"] == 2
        assert correspondence["occurrence_binding_implied"] is False
        assert correspondence["tensor_match_implied"] is False
        assert correspondence["observed_proof"] is False
        assert correspondence["prepare_only_control"] is True
        call_ids.add(call["call_id"])
    assert len(call_ids) == 1


def test_ordinary_mapper_ranks_one_call_and_rejects_signature_mismatch():
    structure = _mla_structure()
    rank1 = _ordinary_correspondences(
        structure, [_control_event("_fwd_kernel_stage2", rank="rank_1",
                                   rank_index=1)],
        rank="rank_1", rank_index=1,
        rank_replicas={"rank_1": "1"})[0]
    assert rank1["rank"] == "rank_1"
    assert rank1["declared_node_ids"] == [
        "rank:1/mla_decode/stage1_grouped_decode",
        "rank:1/mla_decode/stage2_split_merge"]
    assert rank1["signature_match"] is True
    # Different dtype or shape is a different invocation, not an alias.
    for event in (_control_event("decode_attention_fwd_grouped",
                                 dtypes="DT_FLOAT", task="8"),
                  _control_event("decode_attention_fwd_grouped",
                                 shapes="1,4,289", task="9"),
                  _control_event("decode_attention_fwd_grouped",
                                 shapes="777,1,4,288", task="10"),
                  _control_event("decode_attention_fwd_grouped",
                                 shapes="1,4,288;9,11",
                                 dtypes="DT_FLOAT;DT_BF16", task="11")):
        assert _ordinary_correspondences(structure, [event])[0] is None


def test_ordinary_mapper_resolves_real_a3_hc_pre_call_by_signature():
    from hashlib import sha256
    body = pytest.importorskip("mindie_sim.prediction.body")
    raw = json.load(open(
        "/Volumes/data/code/mindie-release-20261014/sim/examples/cases/"
        "longctx-decode-20261030/glm53flash-a3-native-keypool.json"))
    result = body.body_forward(raw, phase="decode", tokens=1, context=2048,
                               sequences=1)
    row = next(row for row in result["timeline"]
               if row["op_id"].endswith(".attention.hc_pre.native")
               and "native_call" in row)
    node_id = "rank:0/" + row["op_id"]
    structure = {
        "schema_version": "mindie-model-structure/1",
        "source": {"kind": "prepare_only_body_row"},
        "execution": {"phase": "decode"},
        "nodes": [{
            "node_id": node_id, "op_id": row["op_id"], "replica": 0,
            "stage": row.get("stage"), "layer": row.get("layer"),
            "block": row.get("block"), "family": row["family"],
            "recipe": row["recipe"], "contract": None, "implementation": {},
            "operator": {"metadata": {}}, "boundary": "kernel",
        }],
        "subgraphs": [],
        "native_calls": [{**row["native_call"], "node_id": node_id}],
    }
    payload = {key: value for key, value in structure.items()
               if key not in {"graph_id", "source", "native_calls",
                              "native_call_coverage"}}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                           allow_nan=False)
    structure["graph_id"] = "sha256:" + sha256(canonical.encode()).hexdigest()
    event = _control_event("aclnnHcPre", shapes="6;4096;4;24", task="1")
    correspondence = _ordinary_correspondences(
        structure, [event], rank_replicas={"rank_0": "0"})[0]
    assert correspondence is not None
    assert correspondence["basis"] == "declared_native_call_signature"
    call = correspondence["native_call"]
    assert call["entry"] == "aclnnHcPre"
    assert call["kernels"] == ["HcPre"]
    assert correspondence["signature_match"] is True
    assert correspondence["tensor_match_implied"] is False


def _comrun5a_structure():
    from dataclasses import replace as _replace
    from types import SimpleNamespace

    schema = pytest.importorskip("mindie_sim.schema.operators")
    hccl_graph = pytest.importorskip("mindie_sim.prediction.hccl_graph")
    structure_module = pytest.importorskip("mindie_sim.structure")
    evidence = json.load(open(
        "/Volumes/data/code/mindie-release-20261014/sim/examples/"
        "source-families/hccl-comrun5a-allgather.json"))
    op = schema.OpSpec(
        "s0.l0.tp_all_gather", "allgather", "decode", 0, 0, (),
        (5120,), (5120,), (5120,), (5120,), link_bytes=10240,
        dtype="bf16", metadata=(("group_axis", "tp"),
                                ("collective", "allgather"),
                                ("hccl_observed_call", evidence["call"])))
    lowered = hccl_graph.lower((op,), SimpleNamespace(kernels={}), "bf16")[0]
    structure = structure_module.export_op_structure(
        {0: (lowered,), 1: (lowered,)}, model={},
        execution={"phase": "decode"})
    return structure, evidence


def _comrun5a_event(name, rank, rank_index, device, start_ns, end_ns):
    return Event(
        rank_id=rank, rank_index=rank_index, name=name, op_type=name,
        task_type="AI_CORE" if name == "AivKernel" else "COMMUNICATION",
        core="MIX_AIC" if name == "AivKernel" else "COMMUNICATION",
        stream_id="26", task_id="17", device_id=str(device),
        start_ns=start_ns, end_ns=end_ns, source_kind="db",
        table="COMPUTE_TASK_INFO",
        locator={"global_task_id": 5, "connection_id": 2,
                 "source": "/COMRUN5A/raw-target.json"})


def _comrun5a_mapper(structure, events, rank, rank_index):
    bindings = {"schema_version": "mindie-profile-bindings/1",
                "graph_id": structure["graph_id"],
                "rank_replicas": {"rank_0": "0", "rank_1": "1"}}
    mapper = StructureMapper(structure, bindings=bindings)
    window = Window(min(event.start_ns for event in events),
                    max(event.end_ns for event in events), step=3)
    source = SourceRef(
        rank_id=rank, rank_index=rank_index, kind="db",
        path="/COMRUN5A/raw-target.json", basename="raw-target.json",
        sha256="418a10dbceb3ae96510c2153121c130fced6d1098bcad719713b09fb95ec95d9",
        size_bytes=4468, schema_version="1", schema_variant="raw", mtime_ns=1)
    observation = Observation(
        rank, rank_index, window, account_window(events, window), events,
        source, QueryStats(rank, "3"))
    mapper.map_window(observation)
    return mapper


def test_comrun5a_ordinary_mapper_one_call_two_rank_local_aliases():
    structure, evidence = _comrun5a_structure()
    for rank, rank_index, device in (("rank_0", 0, 0), ("rank_1", 1, 1)):
        raw = evidence["observations"][rank]["raw_identity"]
        events = [
            _comrun5a_event("AivKernel", rank, rank_index, device,
                            raw["start_ns"], raw["end_ns"]),
            _comrun5a_event("hcom_allGather__612_0_1", rank, rank_index,
                            device, raw["start_ns"], raw["end_ns"]),
        ]
        mapper = _comrun5a_mapper(structure, events, rank, rank_index)
        assert len(mapper.sample) == 2
        rows = mapper.sample
        correspondences = [row["implementation_correspondence"] for row in rows]
        occurrences = [row["native_call_occurrence"] for row in rows]
        assert all(correspondence["basis"] == "observed_hccl_alias_same_call"
                   for correspondence in correspondences)
        assert all(correspondence["rank"] == rank
                   for correspondence in correspondences)
        assert all(correspondence["signature_match"] is True
                   for correspondence in correspondences)
        assert all(correspondence["tensor_match_implied"] is False
                   for correspondence in correspondences)
        assert all(correspondence["occurrence_binding_implied"] is True
                   for correspondence in correspondences)
        assert all(correspondence["observed_proof"] is True
                   for correspondence in correspondences)
        assert all(correspondence["prepare_only_control"] is False
                   for correspondence in correspondences)
        call_ids = {(correspondence["native_call"] or {})["call_id"]
                    for correspondence in correspondences}
        assert len(call_ids) == 1
        owners = {occurrence["call_owner"] for occurrence in occurrences}
        assert owners == {"s0.l0.tp_all_gather"}
        assert all(occurrence["charge"] == "call" for occurrence in occurrences)
        assert {occurrence["presentation_count"] for occurrence in occurrences} == {2}
        assert len({tuple(occurrence["presentations"]) for occurrence in occurrences}) == 1
        aliases = {occurrence["alias_of"] for occurrence in occurrences}
        assert None in aliases and len(aliases) == 2
        raw_identity = correspondences[0]["raw_identity"]
        assert raw_identity == {
            "rank_id": rank, "global_task_id": "5", "stream_id": "26",
            "task_id": "17", "connection_id": "2",
            "device_id": str(device), "start_ns": str(raw["start_ns"]),
            "end_ns": str(raw["end_ns"])}
        # Durations stay out of the call/occurrence linkage.
        encoded = json.dumps({"c": correspondences, "o": occurrences},
                             sort_keys=True)
        for forbidden in ("56.348811", "56.462669", "0.013445", "0.365121",
                          "duration"):
            assert forbidden not in encoded


def test_comrun5a_mapper_rejects_cross_rank_and_cross_range_reuse():
    structure, evidence = _comrun5a_structure()
    raw0 = evidence["observations"]["rank_0"]["raw_identity"]
    cases = (
        # rank1 reusing gtid5 with rank0's device
        ("rank_1", 1, 0, raw0["start_ns"], raw0["end_ns"]),
        # right rank/device but a different physical range
        ("rank_0", 0, 0, raw0["start_ns"] + 1, raw0["end_ns"] + 1),
        # unknown rank key
        ("rank_2", 2, 2, raw0["start_ns"], raw0["end_ns"]),
    )
    for rank, rank_index, device, start_ns, end_ns in cases:
        event = _comrun5a_event("AivKernel", rank, rank_index, device,
                                start_ns, end_ns)
        mapper = _comrun5a_mapper(structure, [event], rank, rank_index)
        assert mapper.sample[0]["implementation_correspondence"] is None
        assert mapper.sample[0].get("native_call_occurrence") is None
